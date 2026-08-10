"""Transparent annual aggregation for steady-state and quasi-dynamic runs."""

from __future__ import annotations

from datetime import date


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
            "utilities_kwh": {
                key: float(utilities_by_time.get(label, {}).get(key, 0.0))
                for key in ("electricity_kwh", "heating_kwh", "cooling_kwh")
            },
            "mass_residual_kg": float(balances_by_time.get(label, {}).get("overall_mass_residual_kg", 0.0)),
        })
    return {
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
    return {
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
