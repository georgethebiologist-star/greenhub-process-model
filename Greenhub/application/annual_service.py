"""Transparent annual aggregation for steady-state and quasi-dynamic runs."""

from __future__ import annotations

from datetime import date

from .biomass_schedule import build_empirical_biomass_schedule


PRODUCT_KEYS = (
    "dry_protein_product",
    "biomethane",
    "phosphorus_product",
    "ammonium_product",
    "potassium_concentrate",
    "nutrient_rich_solids",
)


def build_annual_summary(result, request) -> dict[str, object]:
    """Return decision-ready annual totals without obscuring the calculation basis."""

    if result.seasonal_summary and result.throughput_series:
        return _from_quasi_dynamic(result, request)
    return _annualize_steady_state(result, request)


def _from_quasi_dynamic(result, request) -> dict[str, object]:
    seasonal = result.seasonal_summary
    products = {key: float(seasonal.get("total_products_kg", {}).get(key, 0.0)) for key in PRODUCT_KEYS}
    utilities = seasonal.get("total_utilities", {})
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
            "mass_residual_kg": float(balances_by_time.get(label, {}).get("overall_mass_residual_kg", 0.0)),
        })
    summary = {
        "method": "quasi_dynamic_integration",
        "method_label": "Integrated from monthly model steps",
        "basis": "Mass, product and utility totals are summed from the quasi-dynamic time steps; rates are not multiplied by a generic annual factor.",
        "period": {
            "start_date": request.start_date,
            "end_date": request.end_date,
            "operating_hours": operating_hours,
            "schedule_source": "Run operating calendar and monthly feed profile",
        },
        "feed_processed": _value(processed, "kg/year"),
        "products": {key: _value(value, "kg/year") for key, value in products.items()},
        "utilities": {
            "electricity": _value(float(utilities.get("electricity_kwh", 0.0)), "kWh/year"),
            "heating": _value(float(utilities.get("heating_kwh", 0.0)), "kWh/year"),
            "cooling": _value(float(utilities.get("cooling_kwh", 0.0)), "kWh/year"),
        },
        "balance": _balance_summary(
            processed, process_residual, storage_residual,
            dict(seasonal.get("element_residuals_kg", {})), result.validation.passed,
        ),
        "monthly": monthly,
        "warnings": tuple(result.warnings),
    }
    return _with_empirical_reporting(summary, result, request)


def _annualize_steady_state(result, request) -> dict[str, object]:
    operating_hours, schedule_source = _annual_operating_hours(request.operating_schedule)
    products = {
        key: float(next((item.mass_flow.value or 0.0 for item in result.products if item.product_id == key), 0.0))
        * operating_hours
        for key in PRODUCT_KEYS
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
    overall = next((item for item in result.balances if item.balance_id == "overall_mass"), None)
    inlet = float(overall.inlet.value or 0.0) * operating_hours if overall else 0.0
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
        "feed_processed": _value(inlet, "kg/year"),
        "products": {key: _value(value, "kg/year") for key, value in products.items()},
        "utilities": {
            "electricity": _value(electricity, "kWh/year"),
            "heating": _value(heating_kj / 3600.0, "kWh/year"),
            "cooling": _value(cooling_kj / 3600.0, "kWh/year"),
        },
        "balance": _balance_summary(inlet, process_residual, 0.0, element_residuals, result.validation.passed),
        "monthly": (),
        "warnings": (
            "Annual totals are steady-state annualizations, not measured or simulated month-by-month totals.",
            *result.warnings,
        ),
    }
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
    return {"value": float(value), "unit": unit}


def _with_empirical_reporting(summary: dict[str, object], result, request) -> dict[str, object]:
    """Attach a JSON-safe display adapter without changing empirical calculations."""

    monthly = list(summary["monthly"])
    schedule = _schedule_report(result, request, monthly)
    summary["biomass_schedule"] = schedule
    summary["chart_data"] = _chart_data(monthly, schedule, summary)
    summary["chart_contract"] = {
        "schedule": "tonnes/month",
        "bulk_streams": "tonnes/month",
        "small_products": "tonnes/month",
        "biomethane": "m3/month",
        "electricity": "MWh/month",
        "heat": "GJ/month",
        "annual_electricity": "MWh/year",
        "annual_heat": "GJ/year",
    }
    utilities = summary["utilities"]
    summary["display_utilities"] = {
        "electricity": _value(float(utilities.get("electricity", {}).get("value", 0.0)) / 1000.0, "MWh/year"),
        "heating": _value(float(utilities.get("heating", {}).get("value", 0.0)) * 0.0036, "GJ/year"),
        "cooling": _value(float(utilities.get("cooling", {}).get("value", 0.0)) * 0.0036, "GJ/year"),
    }
    summary["process_pathway"] = _process_pathway(result)
    summary["reporting_status"] = {
        "model": "empirical",
        "schedule_policy": schedule["policy_id"],
        "validated_simulation_ready": bool(result.validation.passed),
        "note": "Display adapter only; empirical and dynamic proxy calculations remain independent.",
    }
    return summary


def _schedule_report(result, request, monthly: list[dict[str, object]]) -> dict[str, object]:
    actual = {str(row["period"]): float(row["feed_processed_kg"]) / 1000.0 for row in monthly}
    if request.biomass_schedule is not None:
        planned = build_empirical_biomass_schedule(request.biomass_schedule)
        rows = []
        for row in planned["monthly"]:
            actual_processed = actual.get(str(row["time_label"]), 0.0)
            processed = float(row["processed_biomass_tonnes"])
            available = float(row["available_biomass_tonnes"])
            rows.append({
                **row,
                "planned_processed_biomass_tonnes": processed,
                "actual_processed_biomass_tonnes": actual_processed,
                "unused_biomass_tonnes": max(available - processed, 0.0),
                "utilization_fraction": processed / available if available else 0.0,
                "utilization_percent": 100.0 * processed / available if available else 0.0,
            })
        available_total = sum(float(row["available_biomass_tonnes"]) for row in rows)
        processed_total = sum(float(row["processed_biomass_tonnes"]) for row in rows)
        return {
            **{key: value for key, value in planned.items() if key != "monthly"},
            "monthly": rows,
            "annual_available_tonnes": available_total,
            "annual_processed_tonnes": processed_total,
            "annual_unused_tonnes": max(available_total - processed_total, 0.0),
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


def _chart_data(
    monthly: list[dict[str, object]],
    schedule: dict[str, object],
    summary: dict[str, object],
) -> dict[str, object]:
    schedule_rows = {str(row["time_label"]): row for row in schedule["monthly"]}
    bulk, products, gas, energy, balance = [], [], [], [], []
    for row in monthly:
        period = str(row["period"])
        product = row["products_kg"]
        intermediate = row.get("intermediate_streams_kg", {})
        utilities = row["utilities_kwh"]
        bulk.append({
            "period": period,
            "feed_processed_tonnes": float(row["feed_processed_kg"]) / 1000.0,
            "press_cake_tonnes": float(intermediate.get("pressed_fibre_cake", 0.0)) / 1000.0,
            "digestate_tonnes": float(intermediate.get("digestate", 0.0)) / 1000.0,
        })
        products.append({
            "period": period,
            "protein_tonnes": float(product.get("dry_protein_product", 0.0)) / 1000.0,
            "phosphorus_product_tonnes": float(product.get("phosphorus_product", 0.0)) / 1000.0,
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
        if float(value.get("value", 0.0)) > 0.0
    ]
    return {
        "schedule": [dict(row) for row in schedule_rows.values()],
        "bulk_streams": bulk,
        "small_products": products,
        "biomethane": gas,
        "energy": energy,
        "mass_balance": balance,
        "annual_product_mix": product_mix,
        "groups": {
            "large_mass": ("feed_processed_tonnes", "press_cake_tonnes", "digestate_tonnes"),
            "small_products": (
                "protein_tonnes", "phosphorus_product_tonnes", "ammonium_product_tonnes",
                "potassium_concentrate_tonnes", "nutrient_rich_solids_tonnes",
            ),
        },
    }


def _process_pathway(result) -> list[dict[str, object]]:
    stage_definitions = (
        ("feed", "Feed", {"feedstock_and_characterization", "front_end"}),
        ("pretreatment", "Pre-treatment / press", {"feed_preparation_and_primary_separation"}),
        ("protein", "Protein recovery", {"protein_recovery"}),
        ("ad", "Anaerobic digestion", {"anaerobic_digestion"}),
        ("gas", "Gas upgrading / CHP", {"biogas_conditioning_and_upgrading", "biogas_upgrading"}),
        ("nutrients", "Nutrient recovery / products", {"digestate_treatment_and_nutrient_recovery", "nutrient_recovery"}),
    )
    areas = {item.process_area_id: item for item in result.process_areas}
    units = {item.unit_id: item for item in result.units}
    products = {item.product_id: float(item.mass_flow.value or 0.0) for item in result.products}
    product_stages = {
        "protein": ("dry_protein_product",),
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
