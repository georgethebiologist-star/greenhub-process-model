"""Shared annual biomass-schedule adapter for empirical and proxy reporting."""

from __future__ import annotations

from Greenhub.application.contracts import BiomassSchedule
from Greenhub.application.dynamic_complete_scenario import (
    DynamicCompleteScenario,
    build_biomass_schedule,
)


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
    schedule["warning"] = (
        "Seasonality is a normal-distribution-like operating assumption, not measured biomass availability."
    )
    return schedule


def schedule_feed_rows(config: BiomassSchedule) -> tuple[dict[str, object], ...]:
    """Return explicit monthly empirical feed rows from the processed schedule plan."""

    schedule = build_empirical_biomass_schedule(config)
    return tuple(
        {
            "time": row["time_label"],
            "start_date": f'{row["time_label"]}-01',
            "available_wet_biomass_kg": float(row["processed_biomass_tonnes"]) * 1000.0,
            "collected_biomass_kg": float(row["processed_biomass_tonnes"]) * 1000.0,
            "uncollected_biomass_kg": 0.0,
            "moisture_fraction": None,
            "dry_matter_kg": None,
            "component_mass_fractions": {},
            "temperature_k": None,
            "source": "shared empirical annual biomass schedule",
            "provenance": "shared_normal_supply_monthly_cap_v1",
            "warnings": (
                "Monthly feed is the scheduled refinery intake; unprocessed availability is retained in the annual reporting ledger.",
            ),
        }
        for row in schedule["monthly"]
    )
