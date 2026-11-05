"""Shared annual biomass-schedule adapter for empirical and proxy reporting."""

from __future__ import annotations

from calendar import monthrange
from datetime import date, timedelta
from math import erf, sqrt

from Greenhub.application.contracts import BiomassSchedule
from Greenhub.application.dynamic_complete_scenario import (
    DynamicCompleteScenario,
    build_biomass_schedule,
)
from Greenhub.time_grid import TimeGridStep, generate_time_grid


def build_empirical_biomass_schedule(config: BiomassSchedule) -> dict[str, object]:
    """Apply the dynamic dashboard's supply and monthly-cap policy to an empirical run."""

    scenario = DynamicCompleteScenario(
        annual_available_biomass_tonnes=config.annual_available_biomass_tonnes,
        annual_processed_biomass_tonnes=config.annual_processed_biomass_tonnes,
        collection_refinery_fraction=config.collection_refinery_fraction,
        feed_basis=config.feed_basis,
        feed_kg_per_hr=config.feed_kg_per_hr,
        season_start=config.season_start,
        season_end=config.season_end,
        peak_date=config.peak_date,
        spread_days=config.spread_days,
        active_months=config.active_months,
    )
    schedule = build_biomass_schedule(scenario)
    schedule["policy_id"] = "shared_normal_supply_monthly_cap_v1"
    schedule["source_status"] = "operating_scenario"
    schedule["feedstock_source_id"] = config.source_id
    schedule["feedstock_location"] = config.location
    potential = None
    if config.accessible_area_ha is not None and config.harvest_yield_tonnes_per_ha is not None:
        potential = config.accessible_area_ha * config.harvest_yield_tonnes_per_ha * config.collection_efficiency
    schedule["availability_basis"] = {
        "accessible_area_ha": config.accessible_area_ha,
        "harvest_yield_tonnes_per_ha": config.harvest_yield_tonnes_per_ha,
        "collection_efficiency": config.collection_efficiency,
        "calculated_collectable_biomass_tonnes": potential,
        "annual_available_biomass_tonnes_input": config.annual_available_biomass_tonnes,
        "status": "user_input_potential" if potential is not None else "annual_availability_input_only",
        "warning": "Calculated potential is reported for comparison; it does not replace annual_available_biomass_tonnes.",
    }
    schedule["warning"] = (
        "Seasonality is a normal-distribution-like operating assumption, not measured biomass availability."
    )
    return schedule


def extend_grid_for_processing_delay(
    grid: tuple[TimeGridStep, ...], config: BiomassSchedule, time_step: str,
    processing_delay_days: int,
) -> tuple[TimeGridStep, ...]:
    """Keep the full delayed processing tail inside the simulation horizon."""
    if not grid or processing_delay_days <= 0:
        return grid
    delayed_end = date.fromisoformat(config.season_end) + timedelta(days=processing_delay_days)
    if date.fromisoformat(grid[-1].end_date) >= delayed_end:
        return grid
    return generate_time_grid(grid[0].start_date, delayed_end.isoformat(), time_step)


def schedule_feed_rows(
    config: BiomassSchedule,
    grid: tuple[TimeGridStep, ...] | None = None,
    *,
    processing_delay_days: int = 0,
) -> tuple[dict[str, object], ...]:
    """Resolve the declared normal availability profile on actual timestep bounds.

    Monthly collection fractions preserve the existing capped monthly intake.
    Daily allocation integrates the same assumed normal input curve; it does not
    interpolate process outputs or claim measured within-month collection timing.
    """

    if processing_delay_days < 0:
        raise ValueError("processing_delay_days must be non-negative.")
    if processing_delay_days and not grid:
        delayed_end = date.fromisoformat(config.season_end) + timedelta(days=processing_delay_days)
        grid = generate_time_grid(config.season_start, delayed_end.isoformat(), "monthly")
    if processing_delay_days and grid:
        timestep = "daily" if grid[0].duration_days == 1 else "weekly" if grid[0].duration_days <= 7 else "monthly"
        delayed_grid = extend_grid_for_processing_delay(grid, config, timestep, processing_delay_days)
        source_grid = generate_time_grid(delayed_grid[0].start_date, delayed_grid[-1].end_date, "daily")
        raw = schedule_feed_rows(config, source_grid)
        totals = {
            step.label: {
                "available_wet_biomass_kg": 0.0,
                "collected_biomass_kg": 0.0,
                "uncollected_biomass_kg": 0.0,
            }
            for step in delayed_grid
        }
        for row in raw:
            collected_on = date.fromisoformat(str(row["start_date"]))
            availability_step = next((item for item in delayed_grid if date.fromisoformat(item.start_date) <= collected_on <= date.fromisoformat(item.end_date)), None)
            release_date = collected_on + timedelta(days=processing_delay_days)
            processing_step = next((item for item in delayed_grid if date.fromisoformat(item.start_date) <= release_date <= date.fromisoformat(item.end_date)), None)
            if availability_step is not None:
                totals[availability_step.label]["available_wet_biomass_kg"] += float(row.get("available_wet_biomass_kg", 0.0))
                totals[availability_step.label]["uncollected_biomass_kg"] += float(row.get("uncollected_biomass_kg", 0.0))
            if processing_step is not None:
                totals[processing_step.label]["collected_biomass_kg"] += float(row.get("collected_biomass_kg", 0.0))
        return tuple({
            "time": step.label,
            "start_date": step.start_date,
            **totals[step.label],
            "moisture_fraction": None,
            "dry_matter_kg": None,
            "component_mass_fractions": {},
            "temperature_k": None,
            "source": "shared empirical annual biomass schedule",
            "feedstock_source_id": config.source_id,
            "feedstock_location": config.location,
            "provenance": f"shared_normal_supply_monthly_cap_v1_with_{processing_delay_days}_day_processing_delay",
            "processing_delay_days": processing_delay_days,
            "warnings": (
                "Biomass availability remains on the collection date; collected feed is released to processing after the declared storage delay. No fermentation or degradation is applied by this delay.",
            ),
        } for step in delayed_grid)

    schedule = build_empirical_biomass_schedule(config)
    start, end, peak = map(date.fromisoformat, (config.season_start, config.season_end, config.peak_date))
    def cdf(day):
        return 0.5 * (1.0 + erf((day - peak).days / (config.spread_days * sqrt(2.0))))
    monthly = {row["time_label"]: row for row in schedule["monthly"]}
    periods = [(row["time_label"], date.fromisoformat(row["time_label"] + "-01"), date(start.year, int(row["time_label"][-2:]), monthrange(start.year, int(row["time_label"][-2:]))[1])) for row in schedule["monthly"]] if grid is None else [(step.label, date.fromisoformat(step.start_date), date.fromisoformat(step.end_date)) for step in grid]
    records = []
    for label, period_start, period_end in periods:
        row = monthly.get(period_start.strftime("%Y-%m"))
        left, right = max(start, period_start), min(end, period_end)
        month_left = max(start, date(period_start.year, period_start.month, 1))
        month_right = min(end, date(period_start.year, period_start.month, monthrange(period_start.year, period_start.month)[1]))
        weight = (cdf(right + timedelta(days=1)) - cdf(left)) / (cdf(month_right + timedelta(days=1)) - cdf(month_left)) if row is not None and right >= left and month_right >= month_left else 0.0
        available = float(row["available_biomass_tonnes"]) * 1000 * weight if row else 0.0
        collected = float(row["processed_biomass_tonnes"]) * 1000 * weight if row else 0.0
        records.append({
            "time": label,
            "start_date": period_start.isoformat(),
            "available_wet_biomass_kg": available,
            "collected_biomass_kg": collected,
            "uncollected_biomass_kg": max(available - collected, 0.0),
            "moisture_fraction": None,
            "dry_matter_kg": None,
            "component_mass_fractions": {},
            "temperature_k": None,
            "source": "shared empirical annual biomass schedule",
            "feedstock_source_id": config.source_id,
            "feedstock_location": config.location,
            "provenance": "shared_normal_supply_monthly_cap_v1",
            "warnings": (
                "Collection timing integrates an assumed normal input profile; each month's collection fraction preserves the capped monthly intake. This is not measured daily availability.",
            ),
        })
    return tuple(records)
