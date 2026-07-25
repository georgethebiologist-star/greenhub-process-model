"""Material, nutrient, product, utility, and seasonal metrics for Phase 7."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from Greenhub.analytical import calculate_elemental_flows
from Greenhub.chemicals import chemicals
from Greenhub.component_groups import COMPONENT_GROUPS
from Greenhub.component_metadata import COMPONENT_METADATA
from Greenhub.phase4_validation import sum_stream_component_flows
from Greenhub.phase7_specifications import peak_sizing


def _safe_ratio(numerator: float, denominator: float) -> float:
    return float(numerator) / float(denominator) if denominator else 0.0


def _stream(model, name: str):
    return model.streams.get(name)


def _mass(model, name: str) -> float:
    stream = _stream(model, name)
    return float(stream.F_mass) if stream is not None else 0.0


def _component(stream, component_id: str) -> float:
    return float(stream.imass[component_id]) if stream is not None else 0.0


def _elements(stream) -> dict[str, float]:
    if stream is None:
        return {name: 0.0 for name in calculate_elemental_flows({}).keys()}
    return calculate_elemental_flows(sum_stream_component_flows((stream,)))


def _phase7_units(model) -> Iterable[object]:
    for unit_id in dict.fromkeys(model.parameters["phase7_unit_ids"]):
        yield model.units[unit_id]


def _thermal_demand_temperature_c(unit) -> float:
    if hasattr(unit, "target_temperature_c"):
        return float(unit.target_temperature_c)
    parameters = getattr(unit, "parameters", None)
    for name in ("temperature_c", "evaporation_temperature_c", "drying_temperature_c"):
        if parameters is not None and hasattr(parameters, name):
            return float(getattr(parameters, name))
    return 25.0


def _utility_metrics(model) -> dict[str, float | str]:
    electricity = 0.0
    heat = 0.0
    cooling = 0.0
    eligible_heat = 0.0
    phase6_metrics = model.upstream_model.metrics
    actual_heat = max(
        float(phase6_metrics.get(key, 0.0) or 0.0)
        for key in ("surplus_heat_available_kw", "phase6_surplus_heat_kw", "chp_surplus_heat_kw")
    )
    available_heat = (
        actual_heat
        if actual_heat > 0.0
        else float(model.parameters.get("recovered_heat_available_kw", 0.0))
    )
    source_temperature = float(
        phase6_metrics.get("surplus_heat_temperature_c", 0.0)
        or model.parameters.get("recovered_heat_temperature_c", 0.0)
    )
    recovery_efficiency = max(
        0.0,
        min(1.0, float(model.parameters.get("heat_recovery_efficiency", 0.0))),
    )
    for unit in _phase7_units(model):
        electricity += float(unit.power_utility.consumption)
        unit_heat = 0.0
        for utility in unit.heat_utilities:
            duty_kw = float(utility.duty) / 3600.0
            if duty_kw >= 0.0:
                heat += duty_kw
                unit_heat += duty_kw
            else:
                cooling -= duty_kw
        if _thermal_demand_temperature_c(unit) <= source_temperature:
            eligible_heat += unit_heat
    recovered_heat = min(eligible_heat, available_heat * recovery_efficiency)
    external_heat = max(0.0, heat - recovered_heat)
    actual_electricity = max(
        float(phase6_metrics.get(key, 0.0) or 0.0)
        for key in ("surplus_electricity_available_kw", "chp_surplus_electricity_kw")
    )
    available_electricity = (
        actual_electricity
        if actual_electricity > 0.0
        else float(model.parameters.get("chp_electricity_available_kw", 0.0))
    )
    chp_used = min(electricity, available_electricity)
    return {
        "gross_electricity_kw": electricity,
        "chp_electricity_available_kw": available_electricity,
        "chp_electricity_used_kw": chp_used,
        "grid_electricity_kw": max(0.0, electricity - chp_used),
        "net_electricity_export_kw": max(0.0, available_electricity - electricity),
        "gross_heat_demand_kw": heat,
        "temperature_eligible_heat_demand_kw": eligible_heat,
        "recovered_heat_available_kw": available_heat,
        "recovered_heat_temperature_c": source_temperature,
        "recovered_heat_used_kw": recovered_heat,
        "external_heat_kw": external_heat,
        "cooling_demand_kw": cooling,
        "utility_interface_source": (
            "upstream Phase 6 metrics" if actual_heat > 0.0 or actual_electricity > 0.0
            else "explicit structural interface; current Phase 6 network unavailable"
        ),
    }


def _external_inputs(model) -> dict[str, float]:
    totals = {ID: 0.0 for ID in chemicals.IDs}
    for stream in model.external_inputs:
        for ID in chemicals.IDs:
            totals[ID] += float(stream.imass[ID])
    return totals


def _contaminants(stream) -> tuple[float, float]:
    if stream is None:
        return 0.0, 0.0
    total = sum(float(stream.imass[ID]) for ID in COMPONENT_GROUPS["contaminants"])
    dry = stream.F_mass - float(stream.imass["Water"])
    return total, _safe_ratio(total * 1e6, dry)


def calculate_phase7_metrics(model, validation=None) -> dict[str, float | str | None]:
    """Return the common NR0-NR7 engineering metric schema."""

    digestate = model.streams["digestate_feed"]
    solids = _stream(model, "nutrient_rich_solids")
    centrate = _stream(model, "nutrient_rich_centrate")
    phosphorus_product = _stream(model, "phosphorus_product")
    ammonium_product = _stream(model, "ammonium_product")
    potassium_product = _stream(model, "potassium_concentrate")
    treated_water = _stream(model, "treated_water")
    residual_liquor = _stream(model, "residual_liquor")
    wastewater = _stream(model, "phase7_wastewater")
    offgas = _stream(model, "phase7_offgas")
    feed_elements = _elements(digestate)
    solids_elements = _elements(solids)
    centrate_elements = _elements(centrate)
    p_product_elements = _elements(phosphorus_product)
    n_product_elements = _elements(ammonium_product)
    k_product_elements = _elements(potassium_product)
    water_elements = _elements(treated_water)
    residual_elements = _elements(residual_liquor)
    offgas_elements = _elements(offgas)
    external = _external_inputs(model)
    utilities = _utility_metrics(model)
    p_contaminants, p_contaminants_mg_kg = _contaminants(phosphorus_product)
    n_contaminants, n_contaminants_mg_kg = _contaminants(ammonium_product)
    k_contaminants, k_contaminants_mg_kg = _contaminants(potassium_product)
    solids_contaminants, solids_contaminants_mg_kg = _contaminants(solids)

    tan_n = sum(
        float(digestate.imass[ID]) * COMPONENT_METADATA[ID].nitrogen_mass_fraction
        for ID in ("Ammonia", "Ammonium")
    )
    phosphate_p = (
        float(digestate.imass["Orthophosphate"])
        * COMPONENT_METADATA["Orthophosphate"].phosphorus_mass_fraction
    )
    particulate_p = (
        float(digestate.imass["ParticulatePhosphorus"])
        * COMPONENT_METADATA["ParticulatePhosphorus"].phosphorus_mass_fraction
    )
    struvite = _component(phosphorus_product, "Struvite")
    calcium_products = sum(
        _component(phosphorus_product, ID)
        for ID in COMPONENT_GROUPS["phase7_phosphorus_products"] - {"Struvite"}
    )
    p_in_struvite = struvite * COMPONENT_METADATA["Struvite"].phosphorus_mass_fraction
    n_in_struvite = struvite * COMPONENT_METADATA["Struvite"].nitrogen_mass_fraction
    p_in_calcium = sum(
        _component(phosphorus_product, ID) * COMPONENT_METADATA[ID].phosphorus_mass_fraction
        for ID in COMPONENT_GROUPS["phase7_phosphorus_products"] - {"Struvite"}
    )
    stripper = model.units.get("A721")
    nh3_stripped = float(getattr(stripper, "ammonia_stripped_kg_hr", 0.0))
    nh3_stripped_n = nh3_stripped * COMPONENT_METADATA["Ammonia"].nitrogen_mass_fraction

    p_dry = _mass(model, "phosphorus_product") - _component(phosphorus_product, "Water")
    p_target = struvite + calcium_products
    p_moisture = _safe_ratio(_component(phosphorus_product, "Water"), _mass(model, "phosphorus_product"))
    p_purity = _safe_ratio(p_target, p_dry)
    n_salts = sum(
        _component(ammonium_product, ID)
        for ID in ("AmmoniumSulfate", "AmmoniumChloride")
    )
    n_salt_concentration = _safe_ratio(n_salts, _mass(model, "ammonium_product"))
    k_volume = _safe_ratio(_mass(model, "potassium_concentrate"), float(model.parameters["values"].get("phase7_digestate_density_kg_m3", 1000.0)))
    k_concentration = _safe_ratio(_component(potassium_product, "PotassiumIon"), k_volume)
    theoretical_struvite_kmol = min(
        float(digestate.imol["Orthophosphate"]),
        float(digestate.imol["Ammonium"]),
        float(digestate.imol["MagnesiumIon"]),
    )
    reagent_mass = sum(external.values())
    chemical_mass = sum(
        value
        for ID, value in external.items()
        if ID not in {"Water", "Oxygen", "Nitrogen"}
    )
    values: dict[str, float | str | None] = {
        "scenario": model.scenario.scenario_id,
        "scenario_name": model.scenario.name,
        "process_order": model.input_bundle.process_order,
        "phase6_scenario": model.input_bundle.phase6_scenario_id,
        "phase5_scenario": model.input_bundle.phase5_scenario_id,
        "phase4_scenario": model.input_bundle.phase4_scenario_id,
        "phase3_scenario": model.input_bundle.phase3_scenario_id,
        "month": model.input_bundle.selected_month,
        "structural_test_mode": str(model.input_bundle.structural_test_mode),
        "calculation_level": "formula-balanced Level-1 engineering model",
        "digestate_processed_kg_hr": digestate.F_mass,
        "digestate_water_kg_hr": float(digestate.imass["Water"]),
        "nutrient_rich_solids_kg_hr": _mass(model, "nutrient_rich_solids"),
        "centrate_kg_hr": _mass(model, "nutrient_rich_centrate"),
        "residual_liquor_kg_hr": _mass(model, "residual_liquor"),
        "treated_water_kg_hr": _mass(model, "treated_water"),
        "phase7_wastewater_kg_hr": _mass(model, "phase7_wastewater"),
        "phase7_offgas_kg_hr": _mass(model, "phase7_offgas"),
        "phosphorus_product_kg_hr": _mass(model, "phosphorus_product"),
        "ammonium_product_kg_hr": _mass(model, "ammonium_product"),
        "potassium_concentrate_kg_hr": _mass(model, "potassium_concentrate"),
        "total_external_reagent_and_water_kg_hr": reagent_mass,
        "chemical_reagent_kg_hr": chemical_mass,
        "fresh_process_water_kg_hr": external["Water"],
        "feed_total_n_kg_hr": feed_elements["nitrogen"],
        "feed_tan_n_kg_hr": tan_n,
        "nh3_stripped_kg_hr": nh3_stripped,
        "nh3_stripped_n_kg_hr": nh3_stripped_n,
        "n_recovered_in_struvite_kg_hr": n_in_struvite,
        "n_recovered_in_ammonium_product_kg_hr": n_product_elements["nitrogen"],
        "n_remaining_in_solids_kg_hr": solids_elements["nitrogen"],
        "n_remaining_in_liquid_kg_hr": residual_elements["nitrogen"] + water_elements["nitrogen"],
        "gaseous_n_kg_hr": offgas_elements["nitrogen"],
        "total_n_recovery_fraction": _safe_ratio(n_in_struvite + n_product_elements["nitrogen"], feed_elements["nitrogen"]),
        "feed_total_p_kg_hr": feed_elements["phosphorus"],
        "feed_orthophosphate_p_kg_hr": phosphate_p,
        "feed_particulate_p_kg_hr": particulate_p,
        "p_recovered_in_struvite_kg_hr": p_in_struvite,
        "p_recovered_in_calcium_phosphate_kg_hr": p_in_calcium,
        "p_remaining_in_solids_kg_hr": solids_elements["phosphorus"],
        "p_remaining_in_liquid_kg_hr": residual_elements["phosphorus"] + water_elements["phosphorus"],
        "total_p_recovery_fraction": _safe_ratio(p_product_elements["phosphorus"], feed_elements["phosphorus"]),
        "theoretical_struvite_kg_hr_from_digestate_species": theoretical_struvite_kmol * chemicals.Struvite.MW,
        "feed_k_kg_hr": feed_elements["potassium"],
        "k_in_solids_kg_hr": solids_elements["potassium"],
        "k_in_centrate_kg_hr": centrate_elements["potassium"],
        "k_in_concentrate_kg_hr": k_product_elements["potassium"],
        "k_in_treated_water_kg_hr": water_elements["potassium"],
        "k_recovery_in_concentrate_fraction": _safe_ratio(k_product_elements["potassium"], feed_elements["potassium"]),
        "magnesium_reagent_kg_hr": sum(external[ID] for ID in COMPONENT_GROUPS["phase7_magnesium_reagents"]),
        "calcium_reagent_kg_hr": sum(external[ID] for ID in COMPONENT_GROUPS["phase7_calcium_reagents"]),
        "sodium_hydroxide_kg_hr": external["SodiumHydroxide"],
        "potassium_hydroxide_kg_hr": external["PotassiumHydroxide"],
        "sulfuric_acid_kg_hr": external["SulfuricAcid"],
        "hydrochloric_acid_kg_hr": external["HydrochloricAcid"],
        "sodium_chloride_kg_hr": external["SodiumChloride"],
        "struvite_product_kg_hr": struvite,
        "calcium_phosphate_products_kg_hr": calcium_products,
        "phosphorus_product_moisture_fraction": p_moisture,
        "phosphorus_product_target_mineral_purity_dry_fraction": p_purity,
        "ammonium_salt_kg_hr": n_salts,
        "ammonium_salt_mass_fraction": n_salt_concentration,
        "potassium_concentration_kg_m3": k_concentration,
        "solids_contaminants_kg_hr": solids_contaminants,
        "solids_contaminants_mg_kg_dry": solids_contaminants_mg_kg,
        "phosphorus_product_contaminants_kg_hr": p_contaminants,
        "phosphorus_product_contaminants_mg_kg_dry": p_contaminants_mg_kg,
        "ammonium_product_contaminants_kg_hr": n_contaminants,
        "ammonium_product_contaminants_mg_kg_dry": n_contaminants_mg_kg,
        "potassium_product_contaminants_kg_hr": k_contaminants,
        "potassium_product_contaminants_mg_kg_dry": k_contaminants_mg_kg,
        "ranking_status": "not ranked",
        "product_compliance_status": "not assessed",
    }
    values.update(utilities)
    for unit_id in model.parameters["phase7_unit_ids"]:
        unit = model.units[unit_id]
        for name, value in unit.design_results.items():
            if isinstance(value, (int, float)):
                key = name.casefold().replace(" ", "_").replace("-", "_")
                values[f"{unit_id.lower()}_{key}"] = float(value)
    if validation is not None:
        values.update(
            mass_balance_error_kg_hr=validation.overall_error_kg_hr,
            water_balance_error_kg_hr=validation.water_component_error_kg_hr,
            carbon_balance_error_kg_hr=validation.element_errors_kg_hr["carbon"],
            nitrogen_balance_error_kg_hr=validation.element_errors_kg_hr["nitrogen"],
            phosphorus_balance_error_kg_hr=validation.element_errors_kg_hr["phosphorus"],
            potassium_balance_error_kg_hr=validation.element_errors_kg_hr["potassium"],
            magnesium_balance_error_kg_hr=validation.element_errors_kg_hr["magnesium"],
            calcium_balance_error_kg_hr=validation.element_errors_kg_hr["calcium"],
            sulfur_balance_error_kg_hr=validation.element_errors_kg_hr["sulfur"],
            chloride_balance_error_kg_hr=validation.element_errors_kg_hr["chloride"],
        )
    return values


@dataclass(frozen=True)
class SeasonalPhase7Result:
    """Monthly quantities, annual totals, and peak-month equipment sizing."""

    monthly_rows: tuple[dict[str, object], ...]
    annual_totals: dict[str, float]
    peak_design: dict[str, float | str]
    warnings: tuple[str, ...]


@dataclass(frozen=True)
class MonthlyPhase7Snapshot:
    """Lightweight monthly result retained after its BioSTEAM graph is released."""

    scenario_id: str
    process_order: str
    month: str
    operating_hours: float
    sizing_safety_factor: float
    metrics: dict[str, object]
    design_values: dict[str, float]


PEAK_DESIGN_ITEMS = {
    "T701": "Total volume",
    "S701": "Feed throughput",
    "R711": "Working volume",
    "R712": "Working volume",
    "A721": "Liquid throughput",
    "A731": "Bed volume",
    "E741": "Water evaporated",
    "M741": "Membrane area",
    "V722": "Working mass",
    "V741": "Working mass",
}


def snapshot_monthly_phase7_model(model) -> MonthlyPhase7Snapshot:
    """Copy the values needed for annual aggregation from one simulated model."""

    metrics = dict(model.metrics or calculate_phase7_metrics(model, model.validation))
    phase3 = model.upstream_model.upstream_model.upstream_model.upstream_model
    design_values: dict[str, float] = {}
    for unit_id, design_item in PEAK_DESIGN_ITEMS.items():
        unit = model.units.get(unit_id)
        if unit is not None and design_item in unit.design_results:
            key = f"{unit_id}_{design_item}".replace(" ", "_").casefold()
            design_values[key] = float(unit.design_results[design_item])
    return MonthlyPhase7Snapshot(
        scenario_id=model.scenario.scenario_id,
        process_order=model.input_bundle.process_order,
        month=model.input_bundle.selected_month,
        operating_hours=phase3.feed_specification.operating_days * 24.0,
        sizing_safety_factor=float(model.parameters.get("sizing_safety_factor", 1.0)),
        metrics=metrics,
        design_values=design_values,
    )


def aggregate_monthly_phase7_metrics(
    monthly_models: list[object],
    warnings: tuple[str, ...] = (),
) -> SeasonalPhase7Result:
    """Aggregate independent monthly steady states and peak-size key equipment."""

    rows: list[dict[str, object]] = []
    annual_names = (
        "digestate_processed_kg",
        "phosphorus_product_kg",
        "ammonium_product_kg",
        "potassium_concentrate_kg",
        "recovered_n_kg",
        "recovered_p_kg",
        "recovered_k_kg",
        "chemical_reagent_kg",
        "fresh_process_water_kg",
        "gross_electricity_kwh",
        "external_heat_kwh",
        "recovered_heat_kwh",
    )
    annual = {name: 0.0 for name in annual_names}
    if not monthly_models:
        raise ValueError("At least one monthly Phase 7 result is required.")
    snapshots = [
        item
        if isinstance(item, MonthlyPhase7Snapshot)
        else snapshot_monthly_phase7_model(item)
        for item in monthly_models
    ]
    peak_values: dict[str, list[tuple[str, float]]] = {}
    safety_factor = snapshots[0].sizing_safety_factor
    for snapshot in snapshots:
        metrics = snapshot.metrics
        hours = snapshot.operating_hours
        row: dict[str, object] = {
            "scenario": snapshot.scenario_id,
            "process_order": snapshot.process_order,
            "month": snapshot.month,
            "operating_hours": hours,
            "digestate_processed_kg": float(metrics["digestate_processed_kg_hr"] or 0.0) * hours,
            "phosphorus_product_kg": float(metrics["phosphorus_product_kg_hr"] or 0.0) * hours,
            "ammonium_product_kg": float(metrics["ammonium_product_kg_hr"] or 0.0) * hours,
            "potassium_concentrate_kg": float(metrics["potassium_concentrate_kg_hr"] or 0.0) * hours,
            "recovered_n_kg": (
                float(metrics["n_recovered_in_struvite_kg_hr"] or 0.0)
                + float(metrics["n_recovered_in_ammonium_product_kg_hr"] or 0.0)
            ) * hours,
            "recovered_p_kg": (
                float(metrics["p_recovered_in_struvite_kg_hr"] or 0.0)
                + float(metrics["p_recovered_in_calcium_phosphate_kg_hr"] or 0.0)
            ) * hours,
            "recovered_k_kg": float(metrics["k_in_concentrate_kg_hr"] or 0.0) * hours,
            "chemical_reagent_kg": float(metrics["chemical_reagent_kg_hr"] or 0.0) * hours,
            "fresh_process_water_kg": float(metrics["fresh_process_water_kg_hr"] or 0.0) * hours,
            "gross_electricity_kwh": float(metrics["gross_electricity_kw"] or 0.0) * hours,
            "external_heat_kwh": float(metrics["external_heat_kw"] or 0.0) * hours,
            "recovered_heat_kwh": float(metrics["recovered_heat_used_kw"] or 0.0) * hours,
        }
        for name in annual:
            annual[name] += float(row[name])
        for key, value in snapshot.design_values.items():
            row[key] = value
            peak_values.setdefault(key, []).append((snapshot.month, value))
        rows.append(row)
    peak: dict[str, float | str] = {"sizing_rule": "peak month times safety factor"}
    for key, month_values in peak_values.items():
        result = peak_sizing((value for _, value in month_values), safety_factor)
        peak_month = max(month_values, key=lambda item: item[1])[0]
        peak[f"{key}_peak_month"] = peak_month
        peak[f"{key}_peak"] = result.peak_value
        peak[f"{key}_design"] = result.design_value
        peak[f"{key}_minimum_turndown_fraction"] = result.minimum_turndown_fraction
    return SeasonalPhase7Result(tuple(rows), annual, peak, warnings)
