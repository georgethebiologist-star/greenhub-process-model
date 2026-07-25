"""Standardized raw-liquid interfaces, metrics, and seasonal aggregation."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from Greenhub.analytical import calculate_analytical_indicators
from Greenhub.chemicals import chemicals
from Greenhub.component_groups import COMPONENT_GROUPS
from Greenhub.component_metadata import COMPONENT_METADATA


def component_flows(stream) -> dict[str, float]:
    """Return all component mass flows from a stream in kg/hr."""

    return {ID: float(stream.imass[ID]) for ID in chemicals.IDs}


def _sum_group(stream, group_name: str) -> float:
    return sum(float(stream.imass[ID]) for ID in COMPONENT_GROUPS[group_name])


def _element(stream, element_field: str) -> float:
    return sum(
        float(stream.imass[ID]) * getattr(COMPONENT_METADATA[ID], element_field)
        for ID in chemicals.IDs
    )


def _safe_ratio(numerator: float, denominator: float) -> float | None:
    return numerator / denominator if denominator > 0.0 else None


@dataclass(frozen=True)
class RawLiquidInterface:
    """Common Mode A/Mode B characterization immediately before C301."""

    source_mode: str
    stream_id: str
    component_flows_kg_hr: dict[str, float]
    density_kg_m3: float
    volumetric_flow_m3_hr: float
    pH: float | None
    conductivity_mS_cm: float | None
    alkalinity_mg_CaCO3_L: float | None
    particle_size_um: float | None
    indicators: dict[str, float | None]
    measured_reconciliation: tuple[object, ...]
    data_quality_rows: tuple[dict[str, Any], ...]
    warnings: tuple[str, ...]


def create_raw_liquid_interface(model) -> RawLiquidInterface:
    """Recalculate Mode A indicators and preserve Mode B measured diagnostics."""

    stream = model.streams["raw_liquid_fraction"]
    density = float(model.parameters["centrifuge"].feed_density_kg_m3)
    volume = stream.F_mass / density if density > 0.0 else 0.0
    characterization = model.characterization
    if model.scenario.entry_mode == "measured_liquid":
        physical = characterization.physical
        pH = physical.pH
        conductivity = physical.conductivity_mS_cm
        alkalinity = physical.alkalinity_mg_CaCO3_L
        particle_size = physical.particle_size_um
        reconciliation = characterization.reconciliation
        quality = characterization.data_quality_rows
        warnings = characterization.warnings
    else:
        pH = None
        conductivity = None
        alkalinity = None
        particle_size = None
        reconciliation = ()
        quality = characterization.data_quality_rows
        warnings = (
            "Roadside-grass mode recalculates raw-liquid indicators from component mass; "
            "raw-liquid pH, conductivity, alkalinity, and particle size remain missing.",
        )
    indicators = calculate_analytical_indicators(
        component_flows(stream),
        volumetric_flow_m3_hr=volume,
        alkalinity_mg_caco3_L=alkalinity,
    )
    return RawLiquidInterface(
        model.scenario.entry_mode,
        stream.ID,
        component_flows(stream),
        density,
        volume,
        pH,
        conductivity,
        alkalinity,
        particle_size,
        indicators,
        tuple(reconciliation),
        tuple(quality),
        tuple(warnings),
    )


def calculate_phase3_metrics(model, validation=None) -> dict[str, float | str | None]:
    """Calculate comparable F0-F3 front-end performance metrics."""

    raw = model.streams["raw_liquid_fraction"]
    clarified = model.streams["clarified_liquid"]
    sludge = model.streams["primary_sludge"]
    grass = model.streams.get("roadside_grass")
    cake = model.streams.get("fibre_cake")
    grass_mass = grass.F_mass if grass is not None else 0.0
    raw_indicators = calculate_analytical_indicators(
        component_flows(raw),
        volumetric_flow_m3_hr=raw.F_mass / model.parameters["centrifuge"].feed_density_kg_m3,
    )
    clarified_indicators = calculate_analytical_indicators(
        component_flows(clarified),
        volumetric_flow_m3_hr=clarified.F_mass / model.parameters["centrifuge"].feed_density_kg_m3,
    )
    cake_water = float(cake.imass["Water"]) if cake is not None else 0.0
    cake_moisture = cake_water / cake.F_mass if cake is not None and cake.F_mass else None
    grass_protein = _sum_group(grass, "protein_equivalents") if grass is not None else 0.0
    grass_sugars = (
        _sum_group(grass, "soluble_sugars") + _sum_group(grass, "entrapped_sugars")
        if grass is not None
        else 0.0
    )
    raw_protein = _sum_group(raw, "protein_equivalents")
    raw_soluble_protein = float(raw.imass["SolubleProtein"])
    raw_sugars = _sum_group(raw, "soluble_sugars")
    power_by_unit = {
        ID: float(unit.power_utility.consumption)
        for ID, unit in model.units.items()
    }
    pef_power = power_by_unit.get("U201", 0.0)
    preparation_power = power_by_unit.get("U101", 0.0)
    press_power = power_by_unit.get("S201", 0.0)
    centrifuge_power = power_by_unit.get("C301", 0.0)
    total_power = sum(power_by_unit.values())
    raw_tss = float(raw_indicators.get("tss_kg_hr") or 0.0)
    clarified_tss = float(clarified_indicators.get("tss_kg_hr") or 0.0)
    metrics: dict[str, float | str | None] = {
        "scenario": model.scenario.scenario_id,
        "month": model.input_bundle.selected_month,
        "entry_mode": model.scenario.entry_mode,
        "wet_grass_throughput_kg_hr": grass_mass if grass is not None else None,
        "raw_liquid_flow_kg_hr": raw.F_mass,
        "liquid_yield_fraction": _safe_ratio(raw.F_mass, grass_mass),
        "fibre_cake_flow_kg_hr": cake.F_mass if cake is not None else None,
        "dry_cake_yield_fraction": (
            _safe_ratio(cake.F_mass - cake_water, grass_mass) if cake is not None else None
        ),
        "cake_moisture_fraction": cake_moisture,
        "clarified_liquid_flow_kg_hr": clarified.F_mass,
        "primary_sludge_flow_kg_hr": sludge.F_mass,
        "soluble_protein_in_raw_liquid_kg_hr": raw_soluble_protein,
        "total_protein_in_raw_liquid_kg_hr": raw_protein,
        "soluble_sugars_in_raw_liquid_kg_hr": raw_sugars,
        "cod_in_raw_liquid_kg_hr": float(raw_indicators.get("cod_kg_hr") or 0.0),
        "tss_in_raw_liquid_kg_hr": raw_tss,
        "nitrogen_in_raw_liquid_kg_hr": _element(raw, "nitrogen_mass_fraction"),
        "phosphorus_in_raw_liquid_kg_hr": _element(raw, "phosphorus_mass_fraction"),
        "potassium_in_raw_liquid_kg_hr": _element(raw, "potassium_mass_fraction"),
        "protein_retained_in_cake_kg_hr": _sum_group(cake, "protein_equivalents") if cake is not None else None,
        "cod_retained_in_cake_kg_hr": (
            float(calculate_analytical_indicators(component_flows(cake), volumetric_flow_m3_hr=None)["cod_kg_hr"])
            if cake is not None
            else None
        ),
        "nitrogen_retained_in_cake_kg_hr": _element(cake, "nitrogen_mass_fraction") if cake is not None else None,
        "phosphorus_retained_in_cake_kg_hr": _element(cake, "phosphorus_mass_fraction") if cake is not None else None,
        "potassium_retained_in_cake_kg_hr": _element(cake, "potassium_mass_fraction") if cake is not None else None,
        "contaminants_in_cake_kg_hr": _sum_group(cake, "contaminants") if cake is not None else None,
        "contaminants_in_sludge_kg_hr": _sum_group(sludge, "contaminants"),
        "protein_extraction_fraction": _safe_ratio(raw_protein, grass_protein),
        "soluble_protein_extraction_fraction": _safe_ratio(raw_soluble_protein, grass_protein),
        "sugar_extraction_fraction": _safe_ratio(raw_sugars, grass_sugars),
        "nitrogen_extraction_fraction": (
            _safe_ratio(_element(raw, "nitrogen_mass_fraction"), _element(grass, "nitrogen_mass_fraction"))
            if grass is not None
            else None
        ),
        "phosphorus_extraction_fraction": (
            _safe_ratio(_element(raw, "phosphorus_mass_fraction"), _element(grass, "phosphorus_mass_fraction"))
            if grass is not None
            else None
        ),
        "potassium_extraction_fraction": (
            _safe_ratio(_element(raw, "potassium_mass_fraction"), _element(grass, "potassium_mass_fraction"))
            if grass is not None
            else None
        ),
        "clarification_efficiency_fraction": _safe_ratio(raw_tss - clarified_tss, raw_tss),
        "protein_retention_in_liquid_fraction": _safe_ratio(
            float(clarified.imass["SolubleProtein"]),
            float(raw.imass["SolubleProtein"]),
        ),
        "preparation_electricity_kw": preparation_power,
        "pef_electricity_kw": pef_power,
        "pressing_electricity_kw": press_power,
        "centrifuge_electricity_kw": centrifuge_power,
        "pumping_electricity_kw": 0.0,
        "total_front_end_electricity_kw": total_power,
        "specific_electricity_kwh_per_t_wet_grass": (
            _safe_ratio(total_power, grass_mass / 1000.0) if grass is not None else None
        ),
        "process_water_kg_hr": model.streams["centrifuge_wash_water"].F_mass,
    }
    if validation is not None:
        metrics["mass_balance_error_kg_hr"] = validation.overall_error_kg_hr
        metrics["maximum_element_error_kg_hr"] = max(
            (abs(value) for value in validation.element_errors_kg_hr.values()),
            default=0.0,
        )
    return metrics


@dataclass(frozen=True)
class SeasonalFrontEndResult:
    monthly_rows: tuple[dict[str, object], ...]
    annual_totals: dict[str, float]
    warnings: tuple[str, ...]


def aggregate_monthly_metrics(
    monthly_models: list[object],
    warnings: tuple[str, ...] = (),
) -> SeasonalFrontEndResult:
    """Convert steady monthly rates to monthly quantities and annual totals."""

    rows: list[dict[str, object]] = []
    annual = {
        "wet_grass_mass_kg": 0.0,
        "raw_liquid_mass_kg": 0.0,
        "fibre_cake_mass_kg": 0.0,
        "clarified_liquid_mass_kg": 0.0,
        "primary_sludge_mass_kg": 0.0,
        "electricity_kwh": 0.0,
    }
    for model in monthly_models:
        hours = model.input_bundle.feed_specification.operating_days * 24.0
        metrics = model.metrics or calculate_phase3_metrics(model, model.validation)
        row = {
            "scenario": model.scenario.scenario_id,
            "month": model.input_bundle.selected_month,
            "operating_hours": hours,
            "wet_grass_mass_kg": (metrics["wet_grass_throughput_kg_hr"] or 0.0) * hours,
            "raw_liquid_mass_kg": metrics["raw_liquid_flow_kg_hr"] * hours,
            "fibre_cake_mass_kg": (metrics["fibre_cake_flow_kg_hr"] or 0.0) * hours,
            "clarified_liquid_mass_kg": metrics["clarified_liquid_flow_kg_hr"] * hours,
            "primary_sludge_mass_kg": metrics["primary_sludge_flow_kg_hr"] * hours,
            "electricity_kwh": metrics["total_front_end_electricity_kw"] * hours,
        }
        rows.append(row)
        for key in annual:
            annual[key] += float(row[key])
    return SeasonalFrontEndResult(tuple(rows), annual, warnings)

