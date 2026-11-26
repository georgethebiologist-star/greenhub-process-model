"""Transparent annual aggregation for steady-state and quasi-dynamic runs."""

from __future__ import annotations

from collections import Counter
from datetime import date

from .biomass_schedule import (
    build_empirical_biomass_schedule,
    extend_grid_for_processing_delay,
    schedule_feed_rows,
)
from Greenhub.time_grid import generate_time_grid
from .water_reporting import fresh_water_kg_per_hour_from_result, kg_to_m3
from .material_fate import accumulate_material_fate, finalize_material_fate


PRODUCT_KEYS = (
    "dry_protein_product",
    "biostimulant_product",
    "biomethane",
    "phosphorus_product",
    "ammonium_product",
    "potassium_concentrate",
    "nutrient_rich_solids",
)

STRUVITE_SCENARIOS = {"NR2", "NR4", "NR7"}


def _named_nutrient_products(products: dict[str, float], request) -> dict[str, float]:
    """Expose chemically specific nutrient names without breaking legacy keys."""
    route = getattr(getattr(request, "scenarios", None), "nutrient_recovery", "")
    if route in STRUVITE_SCENARIOS:
        return {"struvite_product": float(products.get("phosphorus_product", 0.0))}
    if route == "NR5":
        return {"calcium_phosphate_product": float(products.get("phosphorus_product", 0.0))}
    return {}


def build_annual_summary(result, request) -> dict[str, object]:
    """Return decision-ready annual totals without obscuring the calculation basis."""

    if result.seasonal_summary and result.throughput_series:
        return _from_quasi_dynamic(result, request)
    return _annualize_steady_state(result, request)


def _from_quasi_dynamic(result, request) -> dict[str, object]:
    seasonal = result.seasonal_summary
    full_year = bool(result.time_grid and result.time_grid[0]['start_date'].endswith('-01-01') and result.time_grid[-1]['end_date'].endswith('-12-31') and result.time_grid[0]['start_date'][:4] == result.time_grid[-1]['end_date'][:4])
    suffix = 'year' if full_year else 'reported period'
    products = {key: float(seasonal.get("total_products_kg", {}).get(key, 0.0)) for key in PRODUCT_KEYS}
    utilities = seasonal.get("total_utilities", {})
    fresh_water_kg = _optional_number(utilities.get("fresh_water_kg"))
    processed = float(seasonal.get("total_biomass_processed_kg", 0.0))
    process_residual = float(seasonal.get("process_mass_residual_kg", 0.0))
    storage_residual = float(seasonal.get("storage_mass_residual_kg", 0.0))
    operating_hours = sum(float(item.get("available_operating_hours", 0.0)) for item in result.throughput_series)
    monthly = []
    products_by_time = {item.get("time"): item for item in result.product_series}
    utilities_by_time = {item.get("time"): item for item in result.utility_series}
    balances_by_time = {item.get("time"): item for item in result.balance_residual_series}
    for throughput in result.throughput_series:
        label = throughput.get("time")
        monthly.append({
            "period": label,
            "feed_processed_kg": float(throughput.get("actual_throughput_kg", 0.0)),
            "products_kg": dict(products_by_time.get(label, {}).get("products_kg", {})),
            "intermediate_streams_kg": dict(products_by_time.get(label, {}).get("intermediate_streams_kg", {})),
            "volumetric_products_m3": dict(products_by_time.get(label, {}).get("volumetric_products_m3", {})),
            "utilities_kwh": {
                key: float(utilities_by_time.get(label, {}).get(key, 0.0))
                for key in ("electricity_kwh", "heating_kwh", "cooling_kwh")
            },
            "fresh_water_m3": (
                kg_to_m3(float(utilities_by_time[label]["fresh_water_kg"]))
                if label in utilities_by_time and utilities_by_time[label].get("fresh_water_kg") is not None
                else None
            ),
            "mass_residual_kg": float(balances_by_time.get(label, {}).get("overall_mass_residual_kg", 0.0)),
        })
    volumetric_products = {}
    for row in monthly:
        for name, value in row["volumetric_products_m3"].items():
            volumetric_products[name] = volumetric_products.get(name, 0.0) + float(value)
    if any(len(str(row['period']))>7 for row in monthly):
        grouped={}
        for row in monthly:
            key=str(row['period'])[:7]
            if key not in grouped:
                grouped[key]={'period':key,'feed_processed_kg':0.0,'mass_residual_kg':0.0,'products_kg':{},'intermediate_streams_kg':{},'volumetric_products_m3':{},'utilities_kwh':{},'fresh_water_m3':0.0}
            target=grouped[key]
            for field in ('feed_processed_kg','mass_residual_kg'): target[field]+=row[field]
            target['fresh_water_m3'] = None if target['fresh_water_m3'] is None or row['fresh_water_m3'] is None else target['fresh_water_m3'] + row['fresh_water_m3']
            for field in ('products_kg','intermediate_streams_kg','volumetric_products_m3','utilities_kwh'):
                for name,value in row[field].items(): target[field][name]=target[field].get(name,0)+value
        monthly=list(grouped.values())
    summary = {
        "method": "quasi_dynamic_integration",
        "method_label": "Integrated from actual model timesteps",
        "basis": "Mass, product and utility totals are summed from the quasi-dynamic time steps; rates are not multiplied by a generic annual factor.",
        "period": {
            "start_date": request.start_date,
            "end_date": request.end_date,
            "operating_hours": operating_hours,
            "schedule_source": "Run operating calendar and monthly feed profile",
            "full_calendar_year": full_year,
            "totals_basis": suffix,
        },
        "feed_processed": _value(processed, f"kg/{suffix}"),
        "products": {key: _value(value, f"kg/{suffix}") for key, value in products.items()},
        "volumetric_products": {key: _value(value, f"m3/{suffix}") for key, value in volumetric_products.items()},
        "named_products": {key: _value(value, f"kg/{suffix}") for key, value in _named_nutrient_products(products, request).items()},
        "utilities": {
            "electricity": _value(float(utilities.get("electricity_kwh", 0.0)), f"kWh/{suffix}"),
            "heating": _value(float(utilities.get("heating_kwh", 0.0)), f"kWh/{suffix}"),
            "cooling": _value(float(utilities.get("cooling_kwh", 0.0)), f"kWh/{suffix}"),
            "fresh_water_mass": _value(fresh_water_kg, f"kg/{suffix}"),
            "fresh_water": _value(None if fresh_water_kg is None else kg_to_m3(fresh_water_kg), f"m3/{suffix}"),
        },
        "balance": _balance_summary(
            processed, process_residual, storage_residual,
            dict(seasonal.get("element_residuals_kg", {})), result.validation.passed,
        ),
        "monthly": monthly,
        "warnings": tuple(result.warnings),
    }
    summary["material_fate"] = finalize_material_fate(
        seasonal.get("material_fate_totals", {}),
        "Integrated from actual model timesteps; component and elemental amounts are kg/year or kg/reported period.",
    )
    return _with_empirical_reporting(summary, result, request)


def _annualize_steady_state(result, request) -> dict[str, object]:
    operating_hours, schedule_source = _annual_operating_hours(request.operating_schedule)
    products = {
        key: float(next((item.mass_flow.value or 0.0 for item in result.products if item.product_id == key), 0.0))
        * operating_hours
        for key in PRODUCT_KEYS
    }
    volumetric_products = {
        item.product_id: float(item.volumetric_flow.value) * operating_hours
        for item in result.products
        if item.volumetric_flow is not None and item.volumetric_flow.value is not None
    }
    electricity = sum(
        float(item.demand.value or 0.0) for item in result.utilities if item.kind == "electricity"
    ) * operating_hours
    heating_kj = sum(
        max(float(item.demand.value or 0.0), 0.0) for item in result.utilities if item.kind == "heat"
    ) * operating_hours
    cooling_kj = -sum(
        min(float(item.demand.value or 0.0), 0.0) for item in result.utilities if item.kind == "heat"
    ) * operating_hours
    fresh_water_kg = fresh_water_kg_per_hour_from_result(result.streams) * operating_hours
    overall = next((item for item in result.balances if item.balance_id == "overall_mass"), None)
    inlet = float(overall.inlet.value or 0.0) * operating_hours if overall else 0.0
    feed_stream = next((item for item in result.streams if "feed" in item.aliases or item.stream_id == "feed"), None)
    processed_feed = float(feed_stream.total_mass.value) * operating_hours if feed_stream is not None and feed_stream.total_mass.value is not None else None
    process_residual = float(overall.residual.value or 0.0) * operating_hours if overall else 0.0
    element_residuals = {
        item.balance_id.removeprefix("element_"): float(item.residual.value or 0.0) * operating_hours
        for item in result.balances if item.balance_id.startswith("element_")
    }
    summary = {
        "method": "steady_state_annualization",
        "method_label": "Annualized from the selected steady-state month",
        "basis": "Steady-state mass and utility rates are multiplied by the stated annual operating hours. Seasonal feed variation, storage and downtime beyond the schedule assumption are not simulated.",
        "period": {
            "start_date": None,
            "end_date": None,
            "operating_hours": operating_hours,
            "schedule_source": schedule_source,
        },
        "feed_processed": {"value": processed_feed, "unit": "kg/year"},
        "products": {key: _value(value, "kg/year") for key, value in products.items()},
        "volumetric_products": {key: _value(value, "m3/year") for key, value in volumetric_products.items()},
        "named_products": {key: _value(value, "kg/year") for key, value in _named_nutrient_products(products, request).items()},
        "utilities": {
            "electricity": _value(electricity, "kWh/year"),
            "heating": _value(heating_kj / 3600.0, "kWh/year"),
            "cooling": _value(cooling_kj / 3600.0, "kWh/year"),
            "fresh_water_mass": _value(fresh_water_kg, "kg/year"),
            "fresh_water": _value(kg_to_m3(fresh_water_kg), "m3/year"),
        },
        "balance": _balance_summary(inlet, process_residual, 0.0, element_residuals, result.validation.passed),
        "monthly": (),
        "warnings": (
            "Annual totals are steady-state annualizations, not measured or simulated month-by-month totals.",
            *result.warnings,
        ),
    }
    material_totals: dict[str, object] = {}
    accumulate_material_fate(material_totals, result.streams, operating_hours)
    summary["material_fate"] = finalize_material_fate(
        material_totals,
        "Selected steady-state stream rates multiplied by annual operating hours; component and elemental amounts are kg/year.",
    )
    return _with_empirical_reporting(summary, result, request)


def _annual_operating_hours(schedule) -> tuple[float, str]:
    if schedule is None:
        return 8760.0, "Continuous-operation assumption (8,760 hours/year)"
    hours_per_day = float(schedule.operating_hours_per_day if schedule.operating_hours_per_day is not None else 24.0)
    shutdown = {date.fromisoformat(item) for item in schedule.shutdown_dates}
    if schedule.operating_dates:
        operating = {date.fromisoformat(item) for item in schedule.operating_dates} - shutdown
        return len(operating) * hours_per_day, "Explicit operating dates supplied with the run"
    days_per_week = float(schedule.operating_days_per_week if schedule.operating_days_per_week is not None else 7.0)
    hours = min(8760.0, 365.0 / 7.0 * days_per_week * hours_per_day)
    return hours, f"{days_per_week:g} operating days/week at {hours_per_day:g} hours/day"


def _balance_summary(feed_kg: float, process_residual_kg: float, storage_residual_kg: float,
                     element_residuals: dict[str, object], passed: bool) -> dict[str, object]:
    denominator = abs(feed_kg)
    closure = 100.0 if denominator == 0.0 and process_residual_kg == 0.0 else (
        0.0 if denominator == 0.0 else 100.0 * (1.0 - abs(process_residual_kg) / denominator)
    )
    return {
        "overall_closure_pct": closure,
        "process_mass_residual_kg": process_residual_kg,
        "storage_mass_residual_kg": storage_residual_kg,
        "element_residuals_kg": {str(key): float(value) for key, value in element_residuals.items()},
        "passed": bool(passed),
    }


def _value(value: float, unit: str) -> dict[str, object]:
    return {"value": None if value is None else float(value), "unit": unit}


def _optional_number(value) -> float | None:
    return None if value is None else float(value)


def _with_empirical_reporting(summary: dict[str, object], result, request) -> dict[str, object]:
    """Attach a JSON-safe display adapter without changing empirical calculations."""

    monthly = list(summary["monthly"])
    schedule = _schedule_report(result, request, monthly)
    summary["biomass_schedule"] = schedule
    chart_rows = _interval_chart_rows(result) if request.time_step in {"weekly", "daily"} else monthly
    summary["chart_data"] = _chart_data(monthly, schedule, summary, chart_rows)
    summary["chart_contract"] = {
        "schedule": "tonnes/month",
        "schedule_timeseries": "tonnes/week" if request.time_step == "weekly" else "tonnes/day" if request.time_step == "daily" else "tonnes/month",
        "process_timestep": request.time_step or "monthly",
        "bulk_streams": "tonnes per actual model timestep; monthly charts split weekly amounts by interval days",
        "small_products": "tonnes per actual model timestep; monthly charts split weekly amounts by interval days",
        "biomethane": "m3 per actual model timestep; monthly charts split weekly amounts by interval days",
        "volumetric_products": "m3/year or m3/reported period",
        "electricity": "kWh per actual model timestep",
        "heat": "kWh per actual model timestep",
        "annual_electricity": "MWh/year",
        "annual_heat": "GJ/year",
        "fresh_water": "m3 per actual model timestep; converted from external makeup-water mass at 1000 kg/m3",
    }
    utilities = summary["utilities"]
    suffix=summary['period'].get('totals_basis','year')
    summary["display_utilities"] = {
        "electricity": _value(float(utilities.get("electricity", {}).get("value", 0.0)) / 1000.0, f"MWh/{suffix}"),
        "heating": _value(float(utilities.get("heating", {}).get("value", 0.0)) * 0.0036, f"GJ/{suffix}"),
        "cooling": _value(float(utilities.get("cooling", {}).get("value", 0.0)) * 0.0036, f"GJ/{suffix}"),
        "fresh_water": utilities.get("fresh_water", _value(0.0, f"m3/{suffix}")),
    }
    summary["process_pathway"] = _process_pathway(result)
    summary["reporting_status"] = {
        "model": "empirical",
        "schedule_policy": schedule["policy_id"],
        "validated_simulation_ready": False,
        "numerical_balance_checks_passed": bool(result.validation.passed),
        "note": "Display adapter only; empirical and dynamic proxy calculations remain independent.",
    }
    return summary


def _schedule_report(result, request, monthly: list[dict[str, object]]) -> dict[str, object]:
    actual = {}
    for row in monthly:
        month=str(row["period"])[:7]
        actual[month]=actual.get(month,0.0)+float(row["feed_processed_kg"])/1000.0
    if request.biomass_schedule is not None:
        grid_by_label = {
            str(step.get("label")): str(step.get("start_date", ""))[:7]
            for step in (getattr(result, "time_grid", ()) or ())
            if step.get("label") and step.get("start_date")
        }

        def month_for_step(item: dict[str, object]) -> str:
            label = str(item.get("time", ""))
            return grid_by_label.get(label, label[:7])

        operating_hours_by_month: dict[str, float] = {}
        throughput_by_month: dict[str, float] = {}
        for item in getattr(result, "throughput_series", ()) or ():
            month = month_for_step(item)
            if not month:
                continue
            operating_hours_by_month[month] = operating_hours_by_month.get(month, 0.0) + float(
                item.get("available_operating_hours", 0.0) or 0.0
            )
            throughput_by_month[month] = throughput_by_month.get(month, 0.0) + float(
                item.get("actual_throughput_kg", 0.0) or 0.0
            )

        inventory_by_month: dict[str, dict[str, float]] = {}
        for item in getattr(result, "storage_inventory_series", ()) or ():
            month = month_for_step(item)
            if not month:
                continue
            values = inventory_by_month.setdefault(month, {
                "inventory_entering_kg": float(item.get("inventory_entering_kg", 0.0) or 0.0),
                "biomass_received_kg": 0.0,
                "biomass_withdrawn_kg": 0.0,
                "processed_feed_storage_age_mass_kg_h": 0.0,
                "overflow_kg": 0.0,
                "degradation_loss_kg": 0.0,
                "inventory_remaining_kg": 0.0,
                "storage_mass_residual_kg": 0.0,
            })
            for field in (
                "biomass_received_kg", "biomass_withdrawn_kg", "overflow_kg",
                "degradation_loss_kg", "storage_mass_residual_kg",
            ):
                values[field] += float(item.get(field, 0.0) or 0.0)
            withdrawn = float(item.get("biomass_withdrawn_kg", 0.0) or 0.0)
            processed_age = item.get("processed_feed_storage_age_h")
            if withdrawn > 0.0 and processed_age is not None:
                values["processed_feed_storage_age_mass_kg_h"] += withdrawn * float(processed_age)
            # Series rows are ordered by timestep; the last remaining inventory
            # is the monthly closing stock, not a sum over daily/weekly stocks.
            values["inventory_remaining_kg"] = float(item.get("inventory_remaining_kg", 0.0) or 0.0)

        planned = build_empirical_biomass_schedule(request.biomass_schedule)
        grid = generate_time_grid(request.start_date, request.end_date, request.time_step or "monthly")
        grid = extend_grid_for_processing_delay(
            grid, request.biomass_schedule, request.time_step or "monthly",
            request.biomass_schedule.processing_delay_days,
        )
        delayed_supply: dict[str, dict[str, float]] = {}
        delayed_supply_intervals: dict[str, dict[str, float]] = {}
        harvest_dates_by_month: dict[str, list[str]] = {}
        release_dates_by_month: dict[str, list[str]] = {}
        for supply_row in schedule_feed_rows(
            request.biomass_schedule,
            grid,
            processing_delay_days=request.biomass_schedule.processing_delay_days,
        ):
            key = str(supply_row["time"])[:7]
            harvest_dates_by_month.setdefault(key, []).extend(
                str(item) for item in supply_row.get("harvest_event_dates", ())
            )
            release_dates_by_month.setdefault(key, []).extend(
                str(item) for item in supply_row.get("processing_release_dates", ())
            )
            target = delayed_supply.setdefault(key, {
                "available_wet_biomass_kg": 0.0,
                "harvested_biomass_kg": 0.0,
                "collected_biomass_kg": 0.0,
                "uncollected_biomass_kg": 0.0,
                "collection_delay_inventory_entering_kg": 0.0,
                "collection_delay_inventory_remaining_kg": 0.0,
                "collection_delay_inventory_residual_kg": 0.0,
                "collection_delay_inventory_peak_kg": 0.0,
            })
            for field in target:
                value = float(supply_row.get(field, 0.0))
                if field == "collection_delay_inventory_peak_kg":
                    target[field] = max(target[field], value)
                else:
                    target[field] += value
            interval_target = delayed_supply_intervals.setdefault(str(supply_row["time"]), {
                "available_wet_biomass_kg": 0.0,
                "harvested_biomass_kg": 0.0,
                "collected_biomass_kg": 0.0,
                "collection_delay_inventory_entering_kg": 0.0,
                "collection_delay_inventory_remaining_kg": 0.0,
                "collection_delay_inventory_residual_kg": 0.0,
                "collection_delay_inventory_peak_kg": 0.0,
            })
            for field in interval_target:
                interval_target[field] += float(supply_row.get(field, 0.0))
        actual_intervals = {
            str(row.get("time")): float(row.get("actual_throughput_kg", 0.0)) / 1000.0
            for row in result.throughput_series
        }
        interval_rows = [{
            "period": period,
            "available_biomass_tonnes": float(values["available_wet_biomass_kg"]) / 1000.0,
            "harvested_biomass_tonnes": float(values["harvested_biomass_kg"]) / 1000.0,
            "collection_delay_inventory_entering_tonnes": float(values["collection_delay_inventory_entering_kg"]) / 1000.0,
            "collection_delay_inventory_remaining_tonnes": float(values["collection_delay_inventory_remaining_kg"]) / 1000.0,
            "collection_delay_inventory_mass_residual_tonnes": float(values["collection_delay_inventory_residual_kg"]) / 1000.0,
            "collection_delay_inventory_peak_tonnes": float(values["collection_delay_inventory_peak_kg"]) / 1000.0,
            "processed_biomass_tonnes": actual_intervals.get(period, 0.0),
            "released_to_processing_tonnes": float(values["collected_biomass_kg"]) / 1000.0,
        } for period, values in sorted(delayed_supply_intervals.items())]
        rows = []
        planned_by_month = {str(row["time_label"]): row for row in planned["monthly"]}
        periods = sorted(set(planned_by_month) | set(delayed_supply) | set(actual))
        for period in periods:
            row = planned_by_month.get(period, {"time_label": period, "available_biomass_tonnes": 0.0, "processed_biomass_tonnes": 0.0})
            schedule_row = delayed_supply.get(period, {})
            actual_processed = actual.get(period, 0.0)
            operating_hours = operating_hours_by_month.get(period, float(row.get("operating_hours", 0.0) or 0.0))
            throughput_kg = throughput_by_month.get(period, actual_processed * 1000.0)
            collected_for_processing = float(schedule_row.get("collected_biomass_kg", 0.0)) / 1000.0
            available = float(schedule_row.get("available_wet_biomass_kg", 0.0)) / 1000.0
            collected_at_harvest = float(
                schedule_row.get("harvested_biomass_kg", row.get("processed_biomass_tonnes", 0.0) * 1000.0)
            ) / 1000.0
            uncollected = float(schedule_row.get("uncollected_biomass_kg", 0.0)) / 1000.0
            rows.append({
                **row,
                # The collection calendar is shifted by storage residence; use
                # the actual controller hours, including the post-harvest tail,
                # rather than the unshifted harvest-month hours in the plan.
                "operating_hours": operating_hours,
                "basis_feed_kg_per_hr": throughput_kg / operating_hours if operating_hours else 0.0,
                "available_biomass_tonnes": available,
                # Preserve the legacy field as the amount released to processing
                # this period; add explicit fields so delayed harvest and process
                # dates are not conflated in seasonal reporting.
                "planned_processed_biomass_tonnes": collected_for_processing,
                "collected_at_harvest_tonnes": collected_at_harvest,
                "collected_for_processing_tonnes": collected_for_processing,
                "collection_delay_inventory_entering_tonnes": float(schedule_row.get("collection_delay_inventory_entering_kg", 0.0)) / 1000.0,
                "collection_delay_harvest_tonnes": float(schedule_row.get("harvested_biomass_kg", 0.0)) / 1000.0,
                "collection_delay_release_tonnes": collected_for_processing,
                "collection_delay_inventory_remaining_tonnes": float(schedule_row.get("collection_delay_inventory_remaining_kg", 0.0)) / 1000.0,
                "collection_delay_inventory_mass_residual_tonnes": float(schedule_row.get("collection_delay_inventory_residual_kg", 0.0)) / 1000.0,
                "collection_delay_inventory_peak_tonnes": float(schedule_row.get("collection_delay_inventory_peak_kg", 0.0)) / 1000.0,
                "processed_biomass_tonnes": actual_processed,
                "actual_processed_biomass_tonnes": actual_processed,
                "unprocessed_available_biomass_tonnes": max(available-collected_at_harvest,0.0),
                # Legacy field: retained for existing consumers. Use the new
                # uncollected_biomass_tonnes field for harvest-date losses.
                "unused_biomass_tonnes": max(available-collected_for_processing,0.0),
                "uncollected_biomass_tonnes": uncollected,
                **({
                    "storage_inventory_entering_tonnes": stock["inventory_entering_kg"] / 1000.0,
                    "biomass_received_after_storage_conditions_tonnes": stock["biomass_received_kg"] / 1000.0,
                    "storage_withdrawn_tonnes": stock["biomass_withdrawn_kg"] / 1000.0,
                    "storage_overflow_tonnes": stock["overflow_kg"] / 1000.0,
                    "storage_degradation_loss_tonnes": stock["degradation_loss_kg"] / 1000.0,
                    "ending_inventory_tonnes": stock["inventory_remaining_kg"] / 1000.0,
                    "storage_mass_residual_tonnes": stock["storage_mass_residual_kg"] / 1000.0,
                    "processed_feed_storage_age_hours": (
                        stock["processed_feed_storage_age_mass_kg_h"] / stock["biomass_withdrawn_kg"]
                        if stock["biomass_withdrawn_kg"] > 0.0 else None
                    ),
                } if (stock := inventory_by_month.get(period)) is not None else {}),
                # Month-level availability and throughput are time-shifted by
                # storage, so the comparable monthly utilization is the harvest
                # collection fraction, not processing divided by harvest-month supply.
                "utilization_fraction": collected_at_harvest / available if available else 0.0,
                "utilization_percent": 100.0 * collected_at_harvest / available if available else 0.0,
                "utilization_basis": "collected_at_harvest / available_biomass",
                "harvest_event_dates": tuple(dict.fromkeys(harvest_dates_by_month.get(period, ()))),
                "processing_release_dates": tuple(dict.fromkeys(release_dates_by_month.get(period, ()))),
            })
        available_total = sum(float(row["available_biomass_tonnes"]) for row in rows)
        processed_total = sum(float(row["processed_biomass_tonnes"]) for row in rows)
        harvested_total = sum(float(row["collected_at_harvest_tonnes"]) for row in rows)
        released_total = sum(float(row["collected_for_processing_tonnes"]) for row in rows)
        uncollected_total = sum(float(row["uncollected_biomass_tonnes"]) for row in rows)
        user_target = float(request.biomass_schedule.annual_processed_biomass_tonnes)
        effective_target = float(planned["requested_processed_tonnes"])
        capacity_shortfall = max(effective_target - processed_total, 0.0)
        bottlenecks = Counter(
            str(row.get("bottleneck_unit"))
            for row in getattr(result, "bottleneck_series", ())
            if row.get("bottleneck_unit")
        )
        bottleneck_unit_id = bottlenecks.most_common(1)[0][0] if bottlenecks else None
        bottleneck_unit_name = next(
            (unit.display_name for unit in getattr(result, "units", ()) if unit.unit_id == bottleneck_unit_id),
            bottleneck_unit_id,
        )
        return {
            **{key: value for key, value in planned.items() if key != "monthly"},
            "monthly": rows,
            "timeseries": interval_rows,
            "user_requested_target_tonnes": user_target,
            "effective_target_tonnes": effective_target,
            "equipment_capacity_shortfall_tonnes": capacity_shortfall,
            "throughput_capacity_limited": capacity_shortfall > max(1.0, effective_target * 1e-6),
            "throughput_bottleneck_unit_id": bottleneck_unit_id if capacity_shortfall > 0.0 else None,
            "throughput_bottleneck_unit_name": bottleneck_unit_name if capacity_shortfall > 0.0 else None,
            "equipment_capacity_scale_factor": float(result.seasonal_summary.get("equipment_capacity_scale_factor", 1.0)),
            "equipment_scale_design_peak_kg_hr": float(result.seasonal_summary.get("equipment_scale_design_peak_kg_hr", 0.0)),
            "equipment_capacity_costing_status": "structural_capacity_scaled_no_capex_repricing",
            "processing_delay_days": request.biomass_schedule.processing_delay_days,
            "harvest_events": None if request.biomass_schedule.harvest_events is None else [
                {
                    "date": event.date,
                    "available_biomass_tonnes": event.available_biomass_tonnes,
                    "evidence_class": request.biomass_schedule.availability_evidence_class,
                    "temporal_profile_quality_class": request.biomass_schedule.availability_temporal_profile_quality_class,
                    "source_id": request.biomass_schedule.availability_source_id,
                    "source_url": request.biomass_schedule.availability_source_url,
                    "status": request.biomass_schedule.availability_status,
                }
                for event in request.biomass_schedule.harvest_events
            ],
            "processing_start_date": result.seasonal_summary.get("processing_start_date"),
            "processing_end_date": result.seasonal_summary.get("processing_end_date"),
            "annual_operating_hours": sum(operating_hours_by_month.values()),
            "annual_available_tonnes": available_total,
            "annual_collected_tonnes": harvested_total,
            "annual_collection_fraction": harvested_total / available_total if available_total else 0.0,
            "annual_collected_for_processing_tonnes": released_total,
            "collection_delay_inventory_peak_tonnes": max(
                (float(row.get("collection_delay_inventory_peak_tonnes", 0.0)) for row in rows),
                default=0.0,
            ),
            "collection_delay_inventory_final_tonnes": (
                float(rows[-1].get("collection_delay_inventory_remaining_tonnes", 0.0))
                if rows else 0.0
            ),
            "collection_delay_inventory_max_abs_mass_residual_tonnes": max(
                (abs(float(row.get("collection_delay_inventory_mass_residual_tonnes", 0.0))) for row in rows),
                default=0.0,
            ),
            "annual_processed_tonnes": processed_total,
            # Retain the established aggregate contract; the explicit
            # annual_uncollected_tonnes field is the source-calendar quantity.
            "annual_unused_tonnes": max(available_total - processed_total, 0.0),
            "annual_uncollected_tonnes": uncollected_total,
            "annual_supply_minus_actual_processing_tonnes": max(available_total - processed_total, 0.0),
            "ending_inventory_tonnes": float(result.seasonal_summary.get("final_inventory_kg",0))/1000,
            "utilization_fraction": processed_total / available_total if available_total else 0.0,
            "peak_month_processed_tonnes": max((float(row["processed_biomass_tonnes"]) for row in rows), default=0.0),
        }
    rows = [
        {
            "time_label": str(row["period"]),
            "available_biomass_tonnes": float(row["feed_processed_kg"]) / 1000.0,
            "planned_processed_biomass_tonnes": float(row["feed_processed_kg"]) / 1000.0,
            "processed_biomass_tonnes": float(row["feed_processed_kg"]) / 1000.0,
            "unused_biomass_tonnes": 0.0,
            "utilization_fraction": 1.0 if float(row["feed_processed_kg"]) else 0.0,
            "utilization_percent": 100.0 if float(row["feed_processed_kg"]) else 0.0,
        }
        for row in monthly
    ]
    processed = sum(float(row["processed_biomass_tonnes"]) for row in rows)
    return {
        "monthly": rows,
        "timeseries": [
            {"period": str(row["period"]),
             "available_biomass_tonnes": float(row["feed_processed_kg"]) / 1000.0,
             "processed_biomass_tonnes": float(row["feed_processed_kg"]) / 1000.0}
            for row in monthly
        ],
        "annual_available_tonnes": processed,
        "annual_processed_tonnes": processed,
        "annual_unused_tonnes": 0.0,
        "utilization_fraction": 1.0 if processed else 0.0,
        "peak_month_processed_tonnes": max((float(row["processed_biomass_tonnes"]) for row in rows), default=0.0),
        "peak_throughput_kg_per_hr": float(result.seasonal_summary.get("peak_throughput_kg_hr", 0.0)) if result.seasonal_summary else 0.0,
        "policy_id": "existing_empirical_feed_profile",
        "source_status": "model_input",
        "warning": "No shared annual biomass schedule was supplied; displayed availability equals empirical intake.",
    }


def _interval_chart_rows(result) -> list[dict[str, object]]:
    products_by_time = {str(row.get("time")): row for row in result.product_series}
    utilities_by_time = {str(row.get("time")): row for row in result.utility_series}
    balances_by_time = {str(row.get("time")): row for row in result.balance_residual_series}
    rows = []
    for throughput in result.throughput_series:
        period = str(throughput.get("time"))
        product_row = products_by_time.get(period, {})
        utility_row = utilities_by_time.get(period, {})
        balance_row = balances_by_time.get(period, {})
        rows.append({
            "period": period,
            "feed_processed_kg": float(throughput.get("actual_throughput_kg", 0.0)),
            "products_kg": dict(product_row.get("products_kg", {})),
            "intermediate_streams_kg": dict(product_row.get("intermediate_streams_kg", {})),
            "volumetric_products_m3": dict(product_row.get("volumetric_products_m3", {})),
            "utilities_kwh": {
                key: float(utility_row.get(key, 0.0))
                for key in ("electricity_kwh", "heating_kwh", "cooling_kwh")
            },
            "mass_residual_kg": float(balance_row.get("overall_mass_residual_kg", 0.0)),
        })
    return rows


def _chart_data(
    monthly: list[dict[str, object]],
    schedule: dict[str, object],
    summary: dict[str, object],
    chart_rows: list[dict[str, object]] | None = None,
) -> dict[str, object]:
    schedule_rows = {str(row["time_label"]): row for row in schedule["monthly"]}
    bulk, products, gas, energy, balance = [], [], [], [], []
    for row in chart_rows if chart_rows is not None else monthly:
        period = str(row["period"])
        product = row["products_kg"]
        intermediate = row.get("intermediate_streams_kg", {})
        utilities = row["utilities_kwh"]
        bulk.append({
            "period": period,
            "feed_processed_tonnes": float(row["feed_processed_kg"]) / 1000.0,
            "press_cake_tonnes": float(intermediate.get("pressed_fibre_cake", 0.0)) / 1000.0,
            "juice_tonnes": float(intermediate.get("raw_liquid_fraction", 0.0)) / 1000.0,
            "digestate_tonnes": float(intermediate.get("digestate", 0.0)) / 1000.0,
        })
        products.append({
            "period": period,
            "protein_tonnes": float(product.get("dry_protein_product", 0.0)) / 1000.0,
            "biostimulant_product_tonnes": float(product.get("biostimulant_product", 0.0)) / 1000.0,
            "phosphorus_product_tonnes": float(product.get("phosphorus_product", 0.0)) / 1000.0,
            "struvite_tonnes": float(product.get("phosphorus_product", 0.0)) / 1000.0,
            "ammonium_product_tonnes": float(product.get("ammonium_product", 0.0)) / 1000.0,
            "potassium_concentrate_tonnes": float(product.get("potassium_concentrate", 0.0)) / 1000.0,
            "nutrient_rich_solids_tonnes": float(product.get("nutrient_rich_solids", 0.0)) / 1000.0,
        })
        gas.append({
            "period": period,
            "biomethane_m3": float(row.get("volumetric_products_m3", {}).get("biomethane", 0.0)),
        })
        energy.append({
            "period": period,
            "electricity_MWh": float(utilities.get("electricity_kwh", 0.0)) / 1000.0,
            "heating_GJ": float(utilities.get("heating_kwh", 0.0)) * 0.0036,
            "cooling_GJ": float(utilities.get("cooling_kwh", 0.0)) * 0.0036,
        })
        feed = float(row["feed_processed_kg"])
        residual = float(row["mass_residual_kg"])
        balance.append({
            "period": period,
            "closure_percent": 100.0 if feed == 0.0 else 100.0 * (1.0 - abs(residual) / feed),
            "residual_kg": residual,
        })
    annual_products = summary["products"]
    product_mix = [
        {"product": key, "tonnes_per_year": float(value.get("value", 0.0)) / 1000.0}
        for key, value in annual_products.items()
        if key != "biomethane" and float(value.get("value", 0.0)) > 0.0
    ]
    volumetric_product_mix = [
        {"product": key, "volume_m3_per_year": float(value.get("value", 0.0))}
        for key, value in summary.get("volumetric_products", {}).items()
        if float(value.get("value", 0.0)) > 0.0
    ]
    return {
        "schedule": [dict(row) for row in schedule_rows.values()],
        "schedule_timeseries": [dict(row) for row in schedule.get("timeseries", [])],
        "bulk_streams": bulk,
        "small_products": products,
        "biomethane": gas,
        "energy": energy,
        "mass_balance": balance,
        "annual_product_mix": product_mix,
        "annual_volumetric_product_mix": volumetric_product_mix,
        "groups": {
            "large_mass": ("feed_processed_tonnes", "press_cake_tonnes", "juice_tonnes", "digestate_tonnes"),
            "small_products": (
                "protein_tonnes", "biostimulant_product_tonnes", "phosphorus_product_tonnes", "ammonium_product_tonnes",
                "potassium_concentrate_tonnes", "nutrient_rich_solids_tonnes",
            ),
        },
    }


def _process_pathway(result) -> list[dict[str, object]]:
    stage_definitions = [
        ("feed", "Feed", {"feedstock_and_characterization", "front_end"}),
        ("pretreatment", "Pre-treatment / press", {"feed_preparation_and_primary_separation"}),
    ]
    is_pr7 = getattr(result.selected_scenarios, "protein_recovery", None) == "PR7"
    stage_definitions.append((
        "biostimulant" if is_pr7 else "protein",
        "Biostimulant membrane recovery" if is_pr7 else "Protein recovery",
        {"protein_recovery"},
    ))
    stage_definitions.extend((
        ("ad", "Anaerobic digestion", {"anaerobic_digestion"}),
        ("gas", "Gas upgrading / CHP", {"biogas_conditioning_and_upgrading", "biogas_upgrading"}),
        ("nutrients", "Nutrient recovery / products", {"digestate_treatment_and_nutrient_recovery", "nutrient_recovery"}),
    ))
    areas = {item.process_area_id: item for item in result.process_areas}
    units = {item.unit_id: item for item in result.units}
    products = {item.product_id: float(item.mass_flow.value or 0.0) for item in result.products}
    product_stages = {
        "protein": ("dry_protein_product",),
        "biostimulant": ("biostimulant_product",),
        "gas": ("biomethane",),
        "nutrients": ("phosphorus_product", "ammonium_product", "potassium_concentrate", "nutrient_rich_solids"),
    }
    stages = []
    for stage_id, label, area_ids in stage_definitions:
        selected_areas = [areas[item] for item in area_ids if item in areas]
        unit_ids = tuple(dict.fromkeys(unit for area in selected_areas for unit in area.unit_ids))
        stage_units = [units[item] for item in unit_ids if item in units]
        power = sum(max(float(unit.power.value or 0.0), 0.0) for unit in stage_units)
        heat = sum(
            max(float(duty.value or 0.0), 0.0) / 3600.0
            for unit in stage_units for duty in unit.heat_duties
        )
        stage_products = {name: products.get(name, 0.0) for name in product_stages.get(stage_id, ())}
        stages.append({
            "stage_id": stage_id,
            "label": label,
            "active_unit_names": tuple(unit.display_name for unit in stage_units),
            "unit_count": len(stage_units),
            "products_kg_hr": stage_products,
            "power_kw": power if power > 1e-9 else None,
            "heat_duty_kw": heat if heat > 1e-9 else None,
            "limitations": tuple(dict.fromkeys(warning for area in selected_areas for warning in area.warnings)),
            "data_quality": ", ".join(sorted({area.model_maturity for area in selected_areas})) or "not modelled",
        })
    return stages
