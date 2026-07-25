"""Common Phase 4 performance metrics and seasonal aggregation."""

from __future__ import annotations

from dataclasses import dataclass

from Greenhub.analytical import calculate_analytical_indicators, calculate_elemental_flows
from Greenhub.chemicals import chemicals
from Greenhub.component_groups import COMPONENT_GROUPS
from Greenhub.component_metadata import COMPONENT_METADATA
from Greenhub.phase4_validation import PROTEIN_POOL_IDS, stream_component_flows


def _sum_ids(stream, component_ids) -> float:
    return sum(float(stream.imass[ID]) for ID in component_ids)


def _safe_ratio(numerator: float, denominator: float) -> float | None:
    return numerator / denominator if denominator > 0.0 else None


def _heat_duty_kw(unit) -> float:
    return sum(abs(float(utility.duty)) for utility in unit.heat_utilities) / 3600.0


def _phase4_power(model) -> float:
    phase4_ids = {"M401", "H401", "R401", "C401", "W401", "D401", "DR401", "M402", "M403"}
    return sum(
        float(unit.power_utility.consumption)
        for ID, unit in model.units.items()
        if ID in phase4_ids
    )


def _stream_indicators(stream, density_kg_m3: float) -> dict[str, float | None]:
    volume = stream.F_mass / density_kg_m3 if density_kg_m3 > 0.0 else None
    return calculate_analytical_indicators(
        stream_component_flows(stream),
        volumetric_flow_m3_hr=volume,
    )


def calculate_phase4_metrics(model, validation=None) -> dict[str, float | str | None]:
    """Calculate the PR0-PR6 common output schema for one steady month."""

    feed = model.streams["clarified_protein_rich_liquid"]
    product = model.streams["dry_protein_product"]
    residual = model.streams["conditioned_protein_depleted_liquid"]
    exhaust = model.streams["dryer_exhaust"]
    density = float(model.parameters["values"].get("phase4_feed_density_kg_m3", 1000.0))
    feed_indicators = _stream_indicators(feed, density)
    residual_indicators = _stream_indicators(residual, density)
    feed_protein = _sum_ids(feed, PROTEIN_POOL_IDS)
    feed_recoverable = _sum_ids(feed, {"SolubleProtein", "SuspendedProtein"})
    feed_peptides = float(feed.imass["Peptides"])
    feed_amino_acids = float(feed.imass["AminoAcids"])
    product_protein = _sum_ids(product, PROTEIN_POOL_IDS)
    usable_product_protein = _sum_ids(
        product,
        COMPONENT_GROUPS["protein_product_components"],
    )
    product_dry_matter = product.F_mass - float(product.imass["Water"])
    product_moisture = float(product.imass["Water"]) / product.F_mass if product.F_mass else 0.0
    protein_purity_dry = _safe_ratio(product_protein, product_dry_matter)
    protein_purity_wet = _safe_ratio(product_protein, product.F_mass)
    dry_product = product_dry_matter
    acid_solution = model.streams["acid_solution"]
    base_solution = model.streams["base_solution"]
    acid_type = str(model.parameters["values"].get("acid_type", "HydrochloricAcid"))
    base_type = str(model.parameters["values"].get("base_type", "SodiumHydroxide"))
    pure_acid = float(acid_solution.imass[acid_type])
    pure_base = float(base_solution.imass[base_type])
    wash_water = model.streams["protein_cake_wash_water"].F_mass
    salt = _sum_ids(residual, COMPONENT_GROUPS["neutralization_salts"])
    salt_generated = float(getattr(model.units.get("M403"), "salt_generated_kg_hr", 0.0))
    R401 = model.units.get("R401")
    C401 = model.units.get("C401")
    W401 = model.units.get("W401")
    D401 = model.units.get("D401")
    DR401 = model.units.get("DR401")
    precipitated = sum(getattr(R401, "transfers_kg_hr", {}).values()) if R401 else 0.0
    wet_cake_protein = (
        _sum_ids(model.streams["wet_protein_cake"], PROTEIN_POOL_IDS)
        if "wet_protein_cake" in model.streams
        else 0.0
    )
    wash_loss = (
        _sum_ids(model.streams["protein_cake_wash_filtrate"], PROTEIN_POOL_IDS)
        if W401 is not None
        else 0.0
    )
    dewatering_loss = (
        _sum_ids(model.streams["dewatering_filtrate"], PROTEIN_POOL_IDS)
        if D401 is not None
        else 0.0
    )
    dryer_protein_loss = _sum_ids(exhaust, PROTEIN_POOL_IDS)
    dryer_degradation = sum(getattr(DR401, "transfers_kg_hr", {}).values()) if DR401 else 0.0
    preheat_duty = _heat_duty_kw(model.units["H401"]) if "H401" in model.units else 0.0
    dryer_duty = _heat_duty_kw(DR401) if DR401 is not None else 0.0
    total_heat = preheat_duty + dryer_duty
    power = _phase4_power(model)
    evaporated_water = float(exhaust.imass["Water"])
    grass = model.upstream_model.streams.get("roadside_grass")
    raw_liquid = model.upstream_model.streams["raw_liquid_fraction"]
    grass_dry = (
        grass.F_mass - float(grass.imass["Water"])
        if grass is not None
        else 0.0
    )
    product_elements = calculate_elemental_flows(stream_component_flows(product))
    product_ash = sum(
        float(product.imass[ID]) * COMPONENT_METADATA[ID].ash_fraction
        for ID in chemicals.IDs
    )
    product_carbohydrate = _sum_ids(
        product,
        COMPONENT_GROUPS["soluble_sugars"]
        | COMPONENT_GROUPS["entrapped_sugars"]
        | COMPONENT_GROUPS["structural_carbohydrates"],
    )
    product_lipid = float(product.imass["Lipids"])
    product_contaminants = _sum_ids(product, COMPONENT_GROUPS["contaminants"])
    residual_protein = _sum_ids(residual, PROTEIN_POOL_IDS)
    values: dict[str, float | str | None] = {
        "scenario": model.scenario.scenario_id,
        "upstream_scenario": model.input_bundle.phase3_scenario_id,
        "month": model.input_bundle.selected_month,
        "structural_test_mode": str(model.input_bundle.structural_test_mode),
        "clarified_liquid_flow_kg_hr": feed.F_mass,
        "clarified_liquid_protein_concentration_g_L": (
            feed_protein / (feed.F_mass / density) if feed.F_mass else None
        ),
        "recoverable_protein_entering_kg_hr": feed_recoverable,
        "protein_entering_kg_hr": feed_protein,
        "peptides_entering_kg_hr": feed_peptides,
        "amino_acids_entering_kg_hr": feed_amino_acids,
        "protein_precipitated_kg_hr": precipitated,
        "protein_captured_in_wet_cake_kg_hr": wet_cake_protein,
        "protein_wash_loss_kg_hr": wash_loss,
        "protein_dewatering_loss_kg_hr": dewatering_loss,
        "protein_dryer_loss_kg_hr": dryer_protein_loss,
        "protein_thermally_degraded_kg_hr": dryer_degradation,
        "protein_in_dry_product_kg_hr": product_protein,
        "usable_protein_in_product_kg_hr": usable_product_protein,
        "residual_liquid_protein_kg_hr": residual_protein,
        "precipitation_yield_fraction": _safe_ratio(precipitated, feed_recoverable),
        "separator_capture_fraction": _safe_ratio(wet_cake_protein, precipitated),
        "overall_protein_recovery_fraction": _safe_ratio(product_protein, feed_protein),
        "dry_protein_product_flow_kg_hr": product.F_mass,
        "dry_product_dry_matter_kg_hr": dry_product,
        "product_moisture_fraction": product_moisture,
        "protein_purity_dry_basis_fraction": protein_purity_dry,
        "protein_purity_wet_basis_fraction": protein_purity_wet,
        "product_ash_kg_hr": product_ash,
        "product_carbohydrate_kg_hr": product_carbohydrate,
        "product_lipid_kg_hr": product_lipid,
        "product_nitrogen_kg_hr": product_elements["nitrogen"],
        "product_phosphorus_kg_hr": product_elements["phosphorus"],
        "product_sodium_kg_hr": product_elements["sodium"],
        "product_chloride_kg_hr": product_elements["chloride"],
        "product_sulfur_kg_hr": product_elements["sulfur"],
        "product_salt_kg_hr": _sum_ids(product, COMPONENT_GROUPS["neutralization_salts"]),
        "product_contaminants_kg_hr": product_contaminants,
        "product_classification": "unclassified",
        "pure_acid_kg_hr": pure_acid,
        "acid_solution_kg_hr": acid_solution.F_mass,
        "pure_base_kg_hr": pure_base,
        "base_solution_kg_hr": base_solution.F_mass,
        "salt_generated_kg_hr": salt_generated,
        "residual_liquid_salt_kg_hr": salt,
        "wash_water_kg_hr": wash_water,
        "process_water_kg_hr": wash_water + float(acid_solution.imass["Water"]) + float(base_solution.imass["Water"]),
        "preheating_duty_kw": preheat_duty,
        "dryer_duty_kw": dryer_duty,
        "total_phase4_heat_duty_kw": total_heat,
        "phase4_electricity_kw": power,
        "dryer_evaporated_water_kg_hr": evaporated_water,
        "conditioned_liquid_flow_kg_hr": residual.F_mass,
        "residual_cod_kg_hr": float(residual_indicators.get("cod_kg_hr") or 0.0),
        "residual_soluble_cod_kg_hr": float(residual_indicators.get("soluble_cod_kg_hr") or 0.0),
        "residual_nitrogen_kg_hr": float(residual_indicators.get("total_nitrogen_kg_hr") or 0.0),
        "residual_ammonium_nitrogen_kg_hr": sum(
            float(residual.imass[ID]) * COMPONENT_METADATA[ID].nitrogen_mass_fraction
            for ID in {"Ammonia", "Ammonium"}
        ),
        "residual_phosphorus_kg_hr": float(residual_indicators.get("total_phosphorus_kg_hr") or 0.0),
        "residual_potassium_kg_hr": float(residual_indicators.get("potassium_kg_hr") or 0.0),
        "residual_tds_kg_hr": float(residual_indicators.get("tds_kg_hr") or 0.0),
        "residual_contaminants_kg_hr": _sum_ids(residual, COMPONENT_GROUPS["contaminants"]),
        "feed_cod_kg_hr": float(feed_indicators.get("cod_kg_hr") or 0.0),
        "specific_acid_demand_kg_per_kg_dry_product": _safe_ratio(pure_acid, dry_product),
        "specific_base_demand_kg_per_kg_dry_product": _safe_ratio(pure_base, dry_product),
        "specific_heat_demand_kwh_per_kg_dry_product": _safe_ratio(total_heat, dry_product),
        "specific_electricity_kwh_per_kg_dry_product": _safe_ratio(power, dry_product),
        "water_evaporation_intensity_kg_per_kg_dry_product": _safe_ratio(evaporated_water, dry_product),
        "wash_water_intensity_kg_per_kg_dry_product": _safe_ratio(wash_water, dry_product),
        "product_yield_kg_per_t_clarified_liquid": _safe_ratio(product.F_mass * 1000.0, feed.F_mass),
        "product_yield_kg_per_t_raw_liquid": _safe_ratio(product.F_mass * 1000.0, raw_liquid.F_mass),
        "product_yield_kg_per_t_wet_grass": (
            _safe_ratio(product.F_mass * 1000.0, grass.F_mass) if grass is not None else None
        ),
        "product_yield_kg_per_t_dry_grass": (
            _safe_ratio(product.F_mass * 1000.0, grass_dry) if grass is not None else None
        ),
        "feed_pH_metadata": float(model.parameters["values"].get("feed_pH", 0.0)),
        "precipitation_pH_metadata": float(model.parameters["values"].get("target_pH", 0.0)),
        "conditioned_pH_metadata": (
            float(model.parameters["values"].get("target_digester_feed_pH", 0.0))
            if model.scenario.scenario_id != "PR0"
            else float(model.parameters["values"].get("feed_pH", 0.0))
        ),
    }
    if validation is not None:
        values["mass_balance_error_kg_hr"] = validation.overall_error_kg_hr
        values["maximum_element_error_kg_hr"] = max(
            (abs(value) for value in validation.element_errors_kg_hr.values()),
            default=0.0,
        )
        values["nitrogen_balance_error_kg_hr"] = validation.nitrogen_balance["nitrogen_balance_error_kg_hr"]
        values["cod_balance_error_kg_hr"] = validation.cod_balance["cod_balance_error_kg_hr"]
    return values


@dataclass(frozen=True)
class SeasonalPhase4Result:
    """Monthly quantities and annual totals for one Phase 4 configuration."""

    monthly_rows: tuple[dict[str, object], ...]
    annual_totals: dict[str, float]
    warnings: tuple[str, ...]


def aggregate_monthly_phase4_metrics(
    monthly_models: list[object],
    warnings: tuple[str, ...] = (),
) -> SeasonalPhase4Result:
    """Convert monthly steady rates to quantities without annual averaging."""

    rows: list[dict[str, object]] = []
    rate_to_quantity = {
        "clarified_liquid_mass_kg": "clarified_liquid_flow_kg_hr",
        "protein_entering_kg": "protein_entering_kg_hr",
        "protein_recovered_kg": "protein_in_dry_product_kg_hr",
        "protein_product_kg": "dry_protein_product_flow_kg_hr",
        "pure_acid_kg": "pure_acid_kg_hr",
        "pure_base_kg": "pure_base_kg_hr",
        "dryer_water_evaporation_kg": "dryer_evaporated_water_kg_hr",
        "conditioned_liquid_mass_kg": "conditioned_liquid_flow_kg_hr",
        "wash_water_kg": "wash_water_kg_hr",
        "salt_generated_kg": "salt_generated_kg_hr",
    }
    annual = {name: 0.0 for name in rate_to_quantity}
    annual.update(phase4_heat_kwh=0.0, phase4_electricity_kwh=0.0)
    for model in monthly_models:
        metrics = model.metrics or calculate_phase4_metrics(model, model.validation)
        hours = model.upstream_model.input_bundle.feed_specification.operating_days * 24.0
        row: dict[str, object] = {
            "scenario": model.scenario.scenario_id,
            "upstream_scenario": model.input_bundle.phase3_scenario_id,
            "month": model.input_bundle.selected_month,
            "operating_hours": hours,
            "protein_concentration_g_L": metrics["clarified_liquid_protein_concentration_g_L"],
        }
        for quantity_name, rate_name in rate_to_quantity.items():
            row[quantity_name] = float(metrics[rate_name] or 0.0) * hours
            annual[quantity_name] += float(row[quantity_name])
        row["phase4_heat_kwh"] = float(metrics["total_phase4_heat_duty_kw"] or 0.0) * hours
        row["phase4_electricity_kwh"] = float(metrics["phase4_electricity_kw"] or 0.0) * hours
        annual["phase4_heat_kwh"] += float(row["phase4_heat_kwh"])
        annual["phase4_electricity_kwh"] += float(row["phase4_electricity_kwh"])
        rows.append(row)
    return SeasonalPhase4Result(tuple(rows), annual, warnings)
