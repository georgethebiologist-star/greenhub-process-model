"""Shared annual biomass-schedule adapter for empirical and proxy reporting."""

from __future__ import annotations

from calendar import monthrange
import csv
from datetime import date, timedelta
from functools import lru_cache
from math import erf, sqrt
from pathlib import Path

from Greenhub.application.contracts import BiomassSchedule
from Greenhub.application.dynamic_complete_scenario import (
    DynamicCompleteScenario,
    build_biomass_schedule,
)
from Greenhub.time_grid import TimeGridStep, generate_time_grid


@lru_cache(maxsize=1)
def _roadside_standing_biomass_reference() -> dict[str, object]:
    """Load published Dutch site-standing-biomass context without treating it as supply."""
    path = (Path(__file__).resolve().parents[2] / 'Greenhub' / 'data' / 'Pre-treatment'
            / 'Feedstock' / 'roadside_grass_site_productivity_2023.csv')
    with path.open(encoding='utf-8', newline='') as handle:
        rows = list(csv.DictReader(handle))
    values = [float(row['productivity_t_dm_ha']) for row in rows if row.get('productivity_t_dm_ha')]
    if not values:
        return {'status': 'unavailable', 'source_dataset': path.name}
    return {
        'status': 'literature_reference_not_used_as_supply',
        'quality_class': 'B',
        'site_count': len(values),
        'mean_t_dm_per_ha': sum(values) / len(values),
        'minimum_t_dm_per_ha': min(values),
        'maximum_t_dm_per_ha': max(values),
        'measurement_basis': 'Mean of mid-June and late-August 2023 dry standing biomass; not annual collected yield.',
        'source_dataset': 'Greenhub/data/Pre-treatment/Feedstock/roadside_grass_site_productivity_2023.csv',
        'source_dataset_doi': '10.5281/zenodo.15349657',
        'source_article_doi': '10.1111/avsc.70085',
        'source_url': 'https://doi.org/10.5281/zenodo.15349657',
        'warning': 'Do not substitute this standing-biomass reference for annual wet feed availability. Accessible area, cut fraction, regrowth, moisture, and collection losses remain unresolved.',
    }


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
    if config.monthly_availability_tonnes is not None:
        schedule = _apply_monthly_availability(schedule, config)
    schedule["policy_id"] = (
        "dated_harvest_events_with_monthly_capacity_v1"
        if config.harvest_events is not None
        else "source_monthly_supply_with_monthly_cap_v1"
        if config.monthly_availability_tonnes is not None
        else "shared_normal_supply_monthly_cap_v1"
    )
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
        "published_dutch_standing_biomass_reference": _roadside_standing_biomass_reference(),
        "monthly_availability_tonnes": config.monthly_availability_tonnes,
        "harvest_events": None if config.harvest_events is None else [
            {"date": event.date, "available_biomass_tonnes": event.available_biomass_tonnes}
            for event in config.harvest_events
        ],
        "availability_evidence_class": config.availability_evidence_class,
        "availability_status": config.availability_status,
        "availability_note": config.availability_note,
        "availability_temporal_profile_quality_class": config.availability_temporal_profile_quality_class,
        "availability_source_id": config.availability_source_id,
        "availability_source_url": config.availability_source_url,
    }
    schedule["warning"] = (
        "Availability is assigned to explicit harvest-event dates; dates or event-mass allocations remain scenario assumptions unless individually sourced."
        if config.harvest_events is not None
        else "Monthly supply follows the attached source totals; timing within each populated month is uniformly allocated as an explicit temporal-profile assumption."
        if config.monthly_availability_tonnes is not None
        else "Seasonality is a normal-distribution-like operating assumption, not measured biomass availability."
    )
    return schedule


def _apply_monthly_availability(schedule: dict[str, object], config: BiomassSchedule) -> dict[str, object]:
    """Apply supplied month totals, preserving the common monthly-cap policy."""
    monthly = list(schedule["monthly"])
    source = config.monthly_availability_tonnes
    assert source is not None
    for index, row in enumerate(monthly):
        month = index + 1
        available = float(source[index])
        hours = float(row["operating_hours"]) if month in config.active_months else 0.0
        capacity = (
            min(available, config.feed_kg_per_hr * hours / 1000.0)
            if config.feed_basis == "kg_per_hr" else available
        ) if hours > 0.0 else 0.0
        row["available_biomass_tonnes"] = available
        row["capacity"] = capacity if hours else 0.0
    available = sum(float(row["available_biomass_tonnes"]) for row in monthly)
    requested = min(config.annual_processed_biomass_tonnes, available * config.collection_refinery_fraction)
    target = min(requested, sum(float(row["capacity"]) for row in monthly))
    low, high = 0.0, max((float(row["capacity"]) for row in monthly), default=0.0)
    for _ in range(80):
        cap = (low + high) / 2.0
        if sum(min(float(row["capacity"]), cap) for row in monthly) < target:
            low = cap
        else:
            high = cap
    for row in monthly:
        capacity = float(row.pop("capacity"))
        processed = min(capacity, high)
        amount = float(row["available_biomass_tonnes"])
        hours = float(row["operating_hours"])
        row.update(
            processed_biomass_tonnes=processed,
            unused_biomass_tonnes=max(0.0, amount - processed),
            utilization_fraction=processed / amount if amount else 0.0,
            basis_feed_kg_per_hr=processed * 1000.0 / hours if hours else 0.0,
        )
    processed = sum(float(row["processed_biomass_tonnes"]) for row in monthly)
    schedule.update(
        monthly=monthly,
        annual_available_tonnes=available,
        annual_processed_tonnes=processed,
        annual_unused_tonnes=max(0.0, available - processed),
        requested_processed_tonnes=requested,
        unmet_target_tonnes=max(0.0, requested - processed),
        monthly_processing_cap_tonnes=high,
        utilization_fraction=processed / available if available else 0.0,
        peak_month_processed_tonnes=max((float(row["processed_biomass_tonnes"]) for row in monthly), default=0.0),
        peak_throughput_kg_per_hr=max((float(row["basis_feed_kg_per_hr"]) for row in monthly), default=0.0),
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
    A supplied month-total profile is spread uniformly within each source month;
    the default profile retains its prior normal-curve assumption.
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
                "harvested_biomass_kg": 0.0,
                "collected_biomass_kg": 0.0,
                "uncollected_biomass_kg": 0.0,
                "harvest_event_dates": [],
                "processing_release_dates": [],
            }
            for step in delayed_grid
        }
        harvested_by_day: dict[str, float] = {}
        released_by_day: dict[str, float] = {}
        for row in raw:
            collected_on = date.fromisoformat(str(row["start_date"]))
            availability_step = next((item for item in delayed_grid if date.fromisoformat(item.start_date) <= collected_on <= date.fromisoformat(item.end_date)), None)
            release_date = collected_on + timedelta(days=processing_delay_days)
            processing_step = next((item for item in delayed_grid if date.fromisoformat(item.start_date) <= release_date <= date.fromisoformat(item.end_date)), None)
            if availability_step is not None:
                totals[availability_step.label]["available_wet_biomass_kg"] += float(row.get("available_wet_biomass_kg", 0.0))
                harvested = float(row.get("collected_biomass_kg", 0.0))
                totals[availability_step.label]["harvested_biomass_kg"] += harvested
                if harvested > 0.0:
                    totals[availability_step.label]["harvest_event_dates"].extend(
                        row.get("harvest_event_dates", (collected_on.isoformat(),))
                    )
                harvested_by_day[collected_on.isoformat()] = harvested_by_day.get(collected_on.isoformat(), 0.0) + harvested
                totals[availability_step.label]["uncollected_biomass_kg"] += float(row.get("uncollected_biomass_kg", 0.0))
            if processing_step is not None:
                released = float(row.get("collected_biomass_kg", 0.0))
                totals[processing_step.label]["collected_biomass_kg"] += released
                if released > 0.0:
                    totals[processing_step.label]["processing_release_dates"].append(release_date.isoformat())
                release_label = release_date.isoformat()
                released_by_day[release_label] = released_by_day.get(release_label, 0.0) + released
        delay_inventory_peaks = {step.label: 0.0 for step in delayed_grid}
        upstream_daily_inventory_kg = 0.0
        for daily_step in source_grid:
            day = date.fromisoformat(daily_step.start_date)
            period = next((step for step in delayed_grid if date.fromisoformat(step.start_date) <= day <= date.fromisoformat(step.end_date)), None)
            if period is None:
                continue
            upstream_daily_inventory_kg += harvested_by_day.get(day.isoformat(), 0.0)
            delay_inventory_peaks[period.label] = max(delay_inventory_peaks[period.label], upstream_daily_inventory_kg)
            upstream_daily_inventory_kg -= released_by_day.get(day.isoformat(), 0.0)
            if upstream_daily_inventory_kg < -max(1e-8, delay_inventory_peaks[period.label] * 1e-10):
                raise RuntimeError("Collection-delay inventory became negative during a daily harvest/release step.")
            upstream_daily_inventory_kg = max(upstream_daily_inventory_kg, 0.0)
        collection_delay_inventory_kg = 0.0
        for step in delayed_grid:
            values = totals[step.label]
            entering = collection_delay_inventory_kg
            harvested = float(values["harvested_biomass_kg"])
            released = float(values["collected_biomass_kg"])
            ending = entering + harvested - released
            if ending < -max(1e-8, (entering + harvested) * 1e-10):
                raise RuntimeError("Collection-delay inventory became negative; harvest/release schedule is inconsistent.")
            ending = max(ending, 0.0)
            values["collection_delay_inventory_entering_kg"] = entering
            values["collection_delay_inventory_remaining_kg"] = ending
            values["collection_delay_inventory_residual_kg"] = entering + harvested - released - ending
            values["collection_delay_inventory_peak_kg"] = max(delay_inventory_peaks.get(step.label, 0.0), entering, ending)
            collection_delay_inventory_kg = ending
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
            "upstream_residence_days": processing_delay_days,
            "harvest_event_dates": tuple(dict.fromkeys(totals[step.label]["harvest_event_dates"])),
            "processing_release_dates": tuple(dict.fromkeys(totals[step.label]["processing_release_dates"])),
            "warnings": (
                "Biomass availability remains on the collection date; collected feed is released to processing after the declared storage delay. No fermentation or degradation is applied by this delay.",
            ),
        } for step in delayed_grid)

    schedule = build_empirical_biomass_schedule(config)
    if config.harvest_events is not None:
        monthly = {row["time_label"]: row for row in schedule["monthly"]}
        event_rows = []
        for event in config.harvest_events:
            event_date = date.fromisoformat(event.date)
            scheduled = monthly[event_date.strftime("%Y-%m")]
            month_available = float(scheduled["available_biomass_tonnes"])
            month_collected = float(scheduled["processed_biomass_tonnes"])
            collection_fraction = month_collected / month_available if month_available else 0.0
            available_kg = float(event.available_biomass_tonnes) * 1000.0
            event_rows.append((event_date, available_kg, available_kg * collection_fraction))
        periods = (
            [
                (
                    row["time_label"],
                    date.fromisoformat(row["time_label"] + "-01"),
                    date(
                        date.fromisoformat(row["time_label"] + "-01").year,
                        date.fromisoformat(row["time_label"] + "-01").month,
                        monthrange(
                            date.fromisoformat(row["time_label"] + "-01").year,
                            date.fromisoformat(row["time_label"] + "-01").month,
                        )[1],
                    ),
                )
                for row in schedule["monthly"]
            ]
            if grid is None
            else [(step.label, date.fromisoformat(step.start_date), date.fromisoformat(step.end_date)) for step in grid]
        )
        records = []
        for label, period_start, period_end in periods:
            events = [(day, available, collected) for day, available, collected in event_rows if period_start <= day <= period_end]
            available = sum(item[1] for item in events)
            collected = sum(item[2] for item in events)
            records.append({
                "time": label,
                "start_date": period_start.isoformat(),
                "available_wet_biomass_kg": available,
                "collected_biomass_kg": collected,
                "harvested_biomass_kg": collected,
                "uncollected_biomass_kg": max(available - collected, 0.0),
                "collection_delay_inventory_entering_kg": 0.0,
                "collection_delay_inventory_remaining_kg": 0.0,
                "collection_delay_inventory_residual_kg": 0.0,
                "collection_delay_inventory_peak_kg": 0.0,
                "upstream_residence_days": 0,
                "harvest_event_dates": tuple(day.isoformat() for day, _, _ in events),
                "processing_release_dates": tuple(day.isoformat() for day, _, _ in events),
                "moisture_fraction": None,
                "dry_matter_kg": None,
                "component_mass_fractions": {},
                "temperature_k": None,
                "source": "dated biomass harvest-event schedule",
                "feedstock_source_id": config.source_id,
                "feedstock_location": config.location,
                "provenance": str(schedule["policy_id"]),
                "warnings": (
                    "Biomass is available only on the declared event dates; event-date provenance and uncertainty are carried in the request metadata.",
                ),
            })
        return tuple(records)
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
        if config.monthly_availability_tonnes is not None:
            overlap_days = max(0, (right - left).days + 1) if row is not None else 0
            month_days = max(0, (month_right - month_left).days + 1)
            weight = overlap_days / month_days if month_days else 0.0
        else:
            weight = (cdf(right + timedelta(days=1)) - cdf(left)) / (cdf(month_right + timedelta(days=1)) - cdf(month_left)) if row is not None and right >= left and month_right >= month_left else 0.0
        available = float(row["available_biomass_tonnes"]) * 1000 * weight if row else 0.0
        collected = float(row["processed_biomass_tonnes"]) * 1000 * weight if row else 0.0
        records.append({
            "time": label,
            "start_date": period_start.isoformat(),
            "available_wet_biomass_kg": available,
            "collected_biomass_kg": collected,
            "harvested_biomass_kg": collected,
            "uncollected_biomass_kg": max(available - collected, 0.0),
            "collection_delay_inventory_entering_kg": 0.0,
            "collection_delay_inventory_remaining_kg": 0.0,
            "collection_delay_inventory_residual_kg": 0.0,
            "collection_delay_inventory_peak_kg": 0.0,
            "upstream_residence_days": 0,
            "moisture_fraction": None,
            "dry_matter_kg": None,
            "component_mass_fractions": {},
            "temperature_k": None,
            "source": "shared empirical annual biomass schedule",
            "feedstock_source_id": config.source_id,
            "feedstock_location": config.location,
            "provenance": str(schedule["policy_id"]),
            "warnings": (
                "Monthly source totals are distributed uniformly within each populated month; this within-month timing assumption is not measured."
                if config.monthly_availability_tonnes is not None
                else "Collection timing integrates an assumed normal input profile; each month's collection fraction preserves the capped monthly intake. This is not measured daily availability.",
            ),
        })
    return tuple(records)
