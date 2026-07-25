"""Common and technology-specific engineering metrics for Phase 6."""

from __future__ import annotations

from Greenhub.chemicals import chemicals
from Greenhub.phase6_specifications import DRY_GAS_COMPONENTS, normal_volume_nm3_hr

METHANE_LHV_MJ_NM3 = 35.8


def _safe_ratio(numerator: float, denominator: float) -> float:
    return float(numerator) / float(denominator) if denominator else 0.0


def _gas_metrics(stream, prefix: str) -> dict[str, float]:
    dry_kmol = sum(float(stream.imol[ID]) for ID in DRY_GAS_COMPONENTS)
    wet_kmol = dry_kmol + float(stream.imol["Water"])
    methane = float(stream.imol["Methane"])
    co2 = float(stream.imol["CarbonDioxide"])
    return {
        f"{prefix}_wet_nm3_hr": normal_volume_nm3_hr(stream),
        f"{prefix}_dry_nm3_hr": normal_volume_nm3_hr(stream, dry=True),
        f"{prefix}_methane_nm3_hr": methane * 22.413969545014137,
        f"{prefix}_methane_mol_fraction_wet": _safe_ratio(methane, wet_kmol),
        f"{prefix}_methane_mol_fraction_dry": _safe_ratio(methane, dry_kmol),
        f"{prefix}_co2_mol_fraction_dry": _safe_ratio(co2, dry_kmol),
        f"{prefix}_h2s_ppmv_dry": _safe_ratio(float(stream.imol["HydrogenSulfide"]), dry_kmol) * 1e6,
        f"{prefix}_ammonia_ppmv_dry": _safe_ratio(float(stream.imol["Ammonia"]), dry_kmol) * 1e6,
        f"{prefix}_water_mol_fraction_wet": _safe_ratio(float(stream.imol["Water"]), wet_kmol),
        f"{prefix}_pressure_bar": stream.P / 1e5,
        f"{prefix}_temperature_c": stream.T - 273.15,
    }


def _phase6_units(model):
    for unit_id in dict.fromkeys(model.parameters["phase6_unit_ids"]):
        unit = model.units.get(unit_id)
        if unit is not None:
            yield unit


def _utility_totals(model) -> tuple[float, float, float]:
    electricity_kw = 0.0
    heating_kw = 0.0
    cooling_kw = 0.0
    for unit in _phase6_units(model):
        electricity_kw += float(unit.power_utility.consumption)
        for utility in unit.heat_utilities:
            duty_kw = float(utility.duty) / 3600.0
            if duty_kw >= 0.0:
                heating_kw += duty_kw
            else:
                cooling_kw -= duty_kw
    return electricity_kw, heating_kw, cooling_kw


def _external_makeup(model) -> tuple[float, float]:
    fresh_water = 0.0
    chemical_makeup = 0.0
    for stream in model.external_inputs:
        fresh_water += float(stream.imass["Water"])
        for ID in chemicals.IDs:
            if ID not in {"Water", "Oxygen", "Nitrogen"}:
                chemical_makeup += float(stream.imass[ID])
    return fresh_water, chemical_makeup


def calculate_phase6_metrics(model, validation=None) -> dict[str, float | str | None]:
    """Return a common BG0-BG6 comparison schema for one steady month."""

    raw = model.streams["raw_biogas"]
    conditioned = model.streams["conditioned_biogas"]
    product = model.streams["primary_gas_product"]
    reject = model.streams["reject_gas"]
    wastewater = model.streams["phase6_wastewater"]
    spent = model.streams["phase6_spent_material"]
    technology_wastewater = model.streams["technology_wastewater"]
    technology_spent = model.streams["technology_spent_material"]
    conditioning_wastewater = model.streams["conditioning_wastewater"]
    conditioning_spent = model.streams["conditioning_spent_material"]
    electricity_kw, heat_kw, cooling_kw = _utility_totals(model)
    fresh_water_kg_hr, chemical_makeup_kg_hr = _external_makeup(model)
    feed_methane = float(conditioned.imass["Methane"])
    raw_methane = float(raw.imass["Methane"])
    product_methane = float(product.imass["Methane"])
    reject_methane = float(reject.imass["Methane"])
    wastewater_methane = float(technology_wastewater.imass["Methane"])
    spent_methane = float(technology_spent.imass["Methane"])
    conditioning_wastewater_methane = float(
        conditioning_wastewater.imass["Methane"]
    )
    conditioning_spent_methane = float(conditioning_spent.imass["Methane"])
    feed_co2 = float(conditioned.imass["CarbonDioxide"])
    product_co2 = float(product.imass["CarbonDioxide"])
    product_nm3 = normal_volume_nm3_hr(product, dry=True)
    raw_nm3 = normal_volume_nm3_hr(raw)
    product_methane_nm3 = float(product.imol["Methane"]) * 22.413969545014137
    product_energy_kw = product_methane_nm3 * METHANE_LHV_MJ_NM3 / 3.6
    direct_net_energy_kw = product_energy_kw - electricity_kw - heat_kw
    values: dict[str, float | str | None] = {
        "scenario": model.scenario.scenario_id,
        "scenario_name": model.scenario.name,
        "mechanism": model.scenario.mechanism,
        "phase5_scenario": model.input_bundle.phase5_scenario_id,
        "phase4_scenario": model.input_bundle.phase4_scenario_id,
        "phase3_scenario": model.input_bundle.phase3_scenario_id,
        "month": model.input_bundle.selected_month,
        "structural_test_mode": str(model.input_bundle.structural_test_mode),
        "raw_biogas_processed_nm3_hr": raw_nm3,
        "conditioned_biogas_nm3_hr": normal_volume_nm3_hr(conditioned),
        "biomethane_produced_nm3_hr": product_nm3 if model.scenario.upgrading_enabled else 0.0,
        "primary_gas_product_nm3_hr": product_nm3,
        "methane_purity_wet_fraction": _safe_ratio(float(product.imol["Methane"]), sum(float(product.imol[ID]) for ID in (*DRY_GAS_COMPONENTS, "Water"))),
        "methane_purity_dry_fraction": _safe_ratio(float(product.imol["Methane"]), sum(float(product.imol[ID]) for ID in DRY_GAS_COMPONENTS)),
        "methane_recovery_fraction": _safe_ratio(product_methane, feed_methane),
        "phase6_methane_recovery_from_raw_fraction": _safe_ratio(product_methane, raw_methane),
        "methane_slip_fraction": _safe_ratio(feed_methane - product_methane, feed_methane),
        "methane_to_reject_kg_hr": reject_methane,
        "methane_to_wastewater_kg_hr": wastewater_methane,
        "methane_to_spent_material_kg_hr": spent_methane,
        "methane_unassigned_kg_hr": feed_methane - product_methane - reject_methane - wastewater_methane - spent_methane,
        "conditioning_methane_to_wastewater_kg_hr": conditioning_wastewater_methane,
        "conditioning_methane_to_spent_material_kg_hr": conditioning_spent_methane,
        "phase6_total_methane_to_wastewater_kg_hr": float(wastewater.imass["Methane"]),
        "phase6_total_methane_to_spent_material_kg_hr": float(spent.imass["Methane"]),
        "phase6_methane_unassigned_from_raw_kg_hr": (
            raw_methane
            - product_methane
            - reject_methane
            - float(wastewater.imass["Methane"])
            - float(spent.imass["Methane"])
        ),
        "co2_removal_fraction": _safe_ratio(feed_co2 - product_co2, feed_co2),
        "co2_to_reject_kg_hr": float(reject.imass["CarbonDioxide"]),
        "co2_to_wastewater_kg_hr": float(wastewater.imass["CarbonDioxide"]),
        "co2_to_spent_material_kg_hr": float(spent.imass["CarbonDioxide"]),
        "product_pressure_bar": product.P / 1e5,
        "electricity_use_kw": electricity_kw,
        "heat_use_kw": heat_kw,
        "cooling_duty_kw": cooling_kw,
        "electricity_kwh_per_nm3_raw_biogas": _safe_ratio(electricity_kw, raw_nm3),
        "electricity_kwh_per_nm3_biomethane": _safe_ratio(electricity_kw, product_nm3),
        "heat_mj_per_nm3_biomethane": _safe_ratio(heat_kw * 3.6, product_nm3),
        "cooling_mj_per_nm3_biomethane": _safe_ratio(cooling_kw * 3.6, product_nm3),
        "fresh_water_kg_hr": fresh_water_kg_hr,
        "fresh_water_kg_per_nm3_biomethane": _safe_ratio(fresh_water_kg_hr, product_nm3),
        "wastewater_kg_hr": wastewater.F_mass,
        "wastewater_kg_per_nm3_biomethane": _safe_ratio(wastewater.F_mass, product_nm3),
        "chemical_makeup_kg_hr": chemical_makeup_kg_hr,
        "reject_gas_methane_mol_fraction_dry": _safe_ratio(float(reject.imol["Methane"]), sum(float(reject.imol[ID]) for ID in DRY_GAS_COMPONENTS)),
        "gross_product_methane_energy_kw_lhv": product_energy_kw,
        "net_usable_energy_kw_direct_basis": direct_net_energy_kw,
        "active_recycle": "yes" if model.parameters.get("has_recycle") else "no",
        "total_primary_energy_per_nm3_biomethane": None,
    }
    values.update(_gas_metrics(raw, "raw_biogas"))
    values.update(_gas_metrics(conditioned, "conditioned_biogas"))
    values.update(_gas_metrics(product, "product_gas"))
    values.update(_gas_metrics(reject, "reject_gas"))
    scenario = model.scenario.scenario_id
    if scenario == "BG2":
        A611 = model.units["A611"]
        V612 = model.units["V612"]
        A612 = model.units["A612"]
        values.update(
            calculation_level=A611.parameters.calculation_level,
            gross_circulating_water_kg_hr=A611.design_results["Gross circulating water"],
            recycled_water_kg_hr=A612.design_results["Recycled water"],
            purge_water_kg_hr=A612.design_results["Purge water"],
            absorber_column_diameter_m=A611.design_results["Column diameter"],
            absorber_packing_height_m=A611.design_results["Packing height"],
            flash_gas_methane_kg_hr=V612.design_results["Methane recovered"],
            specific_equipment_capacity=A611.design_results["Gross circulating water"],
            specific_equipment_capacity_unit="kg/hr gross water circulation",
        )
    elif scenario == "BG3":
        stages = [model.units[ID] for ID in ("M621", "M622", "M623") if ID in model.units]
        total_area = sum(stage.area_m2 for stage in stages)
        values.update(
            calculation_level="segmented_solution_diffusion",
            membrane_number_of_stages=len(stages),
            total_membrane_area_m2=total_area,
            stage1_stage_cut=stages[0].calculation.stage_cut if stages else 0.0,
            stage2_stage_cut=stages[1].calculation.stage_cut if len(stages) > 1 else None,
            stage3_stage_cut=stages[2].calculation.stage_cut if len(stages) > 2 else None,
            membrane_module_count=sum(stage.design_results["Module count"] for stage in stages),
            specific_equipment_capacity=total_area,
            specific_equipment_capacity_unit="m2 active membrane",
        )
    elif scenario == "BG4":
        A631 = model.units["A631"]
        values.update(
            calculation_level="calibrated_cycle_average",
            psa_adsorbent_inventory_kg=A631.adsorbent_inventory_kg,
            psa_bed_volume_m3=A631.design_results["Bed volume"],
            psa_cycle_time_min=A631.design_results["Cycle time"],
            psa_purge_methane_kg_hr=float(model.streams["psa_purge_gas"].imass["Methane"]),
            specific_equipment_capacity=A631.adsorbent_inventory_kg,
            specific_equipment_capacity_unit="kg adsorbent inventory",
        )
    elif scenario == "BG5":
        A641 = model.units["A641"]
        H641 = model.units["H641"]
        A642 = model.units["A642"]
        values.update(
            calculation_level="equivalent_loading",
            mea_circulation_kg_hr=A641.design_results["MEA circulation"],
            mea_makeup_kg_hr=A641.design_results["Fresh MEA"],
            mea_rich_loading_mol_mol=A641.rich_loading,
            mea_lean_loading_mol_mol=A642.lean_loading,
            mea_reboiler_duty_kw=H641.reboiler_duty_kw,
            mea_degradation_kg_hr=A642.degraded_mea_kg_hr,
            specific_equipment_capacity=A641.design_results["MEA circulation"],
            specific_equipment_capacity_unit="kg/hr MEA circulation",
        )
    else:
        values.update(
            calculation_level="reference_export",
            specific_equipment_capacity=0.0,
            specific_equipment_capacity_unit="not applicable",
        )
    if validation is not None:
        values.update(
            mass_balance_error_kg_hr=validation.overall_error_kg_hr,
            methane_balance_error_kg_hr=validation.methane_balance_error_kg_hr,
            carbon_balance_error_kg_hr=validation.element_errors_kg_hr["carbon"],
            nitrogen_balance_error_kg_hr=validation.element_errors_kg_hr["nitrogen"],
            sulfur_balance_error_kg_hr=validation.element_errors_kg_hr["sulfur"],
            feed_quality_checks_passed=sum(check.passed for check in validation.feed_quality_checks),
            feed_quality_checks_total=len(validation.feed_quality_checks),
        )
    return values
