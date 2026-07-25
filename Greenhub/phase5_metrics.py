"""Common Phase 5 anaerobic-digestion metrics and seasonal aggregation."""

from __future__ import annotations

from dataclasses import dataclass

from Greenhub.analytical import calculate_analytical_indicators, calculate_elemental_flows
from Greenhub.chemicals import chemicals
from Greenhub.component_groups import COMPONENT_GROUPS
from Greenhub.component_metadata import COMPONENT_METADATA
from Greenhub.phase4_validation import stream_component_flows
from Greenhub.phase5_specifications import normal_volume_m3


def _safe_ratio(numerator: float, denominator: float) -> float | None:
    return numerator / denominator if denominator > 0.0 else None


def _heating_duty_kw(unit) -> float:
    return sum(max(0.0, float(utility.duty)) for utility in unit.heat_utilities) / 3600.0


def _cooling_duty_kw(unit) -> float:
    return -sum(min(0.0, float(utility.duty)) for utility in unit.heat_utilities) / 3600.0


def _stream_indicators(stream, density_kg_m3: float) -> dict[str, float | None]:
    volume = stream.F_mass / density_kg_m3 if density_kg_m3 > 0.0 else None
    return calculate_analytical_indicators(
        stream_component_flows(stream),
        volumetric_flow_m3_hr=volume,
    )


def _gas_values(stream) -> dict[str, float]:
    dry_ids = tuple(COMPONENT_GROUPS["biogas_components"])
    dry_kmol = sum(float(stream.imol[ID]) for ID in dry_ids)
    wet_kmol = dry_kmol + float(stream.imol["Water"])
    methane_kmol = float(stream.imol["Methane"])
    co2_kmol = float(stream.imol["CarbonDioxide"])
    h2s_kmol = float(stream.imol["HydrogenSulfide"])
    ammonia_kmol = float(stream.imol["Ammonia"])
    return {
        "wet_raw_biogas_nm3_hr": normal_volume_m3(wet_kmol),
        "dry_raw_biogas_nm3_hr": normal_volume_m3(dry_kmol),
        "raw_biogas_methane_nm3_hr": normal_volume_m3(methane_kmol),
        "raw_biogas_co2_nm3_hr": normal_volume_m3(co2_kmol),
        "raw_biogas_methane_dry_mol_fraction": methane_kmol / dry_kmol if dry_kmol else 0.0,
        "raw_biogas_co2_dry_mol_fraction": co2_kmol / dry_kmol if dry_kmol else 0.0,
        "raw_biogas_h2s_ppmv_dry": h2s_kmol / dry_kmol * 1e6 if dry_kmol else 0.0,
        "raw_biogas_ammonia_ppmv_dry": ammonia_kmol / dry_kmol * 1e6 if dry_kmol else 0.0,
        "raw_biogas_water_mol_fraction_wet": float(stream.imol["Water"]) / wet_kmol if wet_kmol else 0.0,
    }


def calculate_phase5_metrics(model, validation=None) -> dict[str, float | str | None]:
    """Calculate the common AD0-AD5 output schema for one steady month."""

    feed = model.streams["digester_feed"]
    conditioned = model.streams["conditioned_digester_feed"]
    digestate = model.streams["digestate"]
    raw_biogas = model.streams["raw_biogas"]
    uncaptured = model.streams["uncaptured_biogas"]
    density = float(model.parameters["values"].get("phase5_feed_density_kg_m3", 1000.0))
    feed_indicators = _stream_indicators(feed, density)
    digestate_indicators = _stream_indicators(digestate, density)
    feed_elements = calculate_elemental_flows(stream_component_flows(feed))
    digestate_elements = calculate_elemental_flows(stream_component_flows(digestate))
    M501 = model.units["M501"]
    R501 = model.units["R501"]
    H501 = model.units["H501"]
    sizing = R501.sizing_result
    geometry = R501.geometry_result
    heat = R501.heat_result
    gas = _gas_values(raw_biogas)
    methane_total = sum(
        float(stream.imass["Methane"])
        for stream in (raw_biogas, digestate, uncaptured)
    )
    methane_cod = methane_total * (COMPONENT_METADATA["Methane"].cod_factor or 0.0)
    feed_cod = float(feed_indicators.get("cod_kg_hr") or 0.0)
    digestate_cod = float(digestate_indicators.get("cod_kg_hr") or 0.0)
    feed_vs = float(feed_indicators.get("volatile_solids_kg_hr") or 0.0)
    digestate_vs = float(digestate_indicators.get("volatile_solids_kg_hr") or 0.0)
    conditioning_power = float(M501.power_utility.consumption)
    mixing_power = float(R501.power_utility.consumption)
    preheat = _heating_duty_kw(H501) if model.scenario.digestion_enabled else 0.0
    feed_cooling = _cooling_duty_kw(H501) if model.scenario.digestion_enabled else 0.0
    vessel_heat = float(heat.vessel_heat_loss_kw if heat else 0.0)
    upstream_raw = model.upstream_model.upstream_model.streams["raw_liquid_fraction"]
    grass = model.upstream_model.upstream_model.streams.get("roadside_grass")
    values: dict[str, float | str | None] = {
        "scenario": model.scenario.scenario_id,
        "phase4_scenario": model.input_bundle.phase4_scenario_id,
        "phase3_scenario": model.input_bundle.phase3_scenario_id,
        "month": model.input_bundle.selected_month,
        "structural_test_mode": str(model.input_bundle.structural_test_mode),
        "digestion_enabled": str(model.scenario.digestion_enabled),
        "digester_feed_kg_hr": feed.F_mass,
        "conditioned_digester_feed_kg_hr": conditioned.F_mass,
        "digester_feed_m3_hr": feed.F_mass / density,
        "digester_feed_cod_kg_hr": feed_cod,
        "digester_feed_soluble_cod_kg_hr": float(feed_indicators.get("soluble_cod_kg_hr") or 0.0),
        "digester_feed_particulate_cod_kg_hr": float(feed_indicators.get("particulate_cod_kg_hr") or 0.0),
        "digester_feed_vs_kg_hr": feed_vs,
        "digester_feed_total_n_kg_hr": feed_elements["nitrogen"],
        "digester_feed_total_p_kg_hr": feed_elements["phosphorus"],
        "digester_feed_total_s_kg_hr": feed_elements["sulfur"],
        "digester_feed_c_to_n_ratio": feed_indicators.get("c_to_n_ratio"),
        "digester_feed_cod_to_n_ratio": feed_indicators.get("cod_to_n_ratio"),
        "digester_feed_cod_to_p_ratio": feed_indicators.get("cod_to_p_ratio"),
        "conditioning_pure_base_kg_hr": float(M501.pure_base_kg_hr),
        "conditioning_base_solution_kg_hr": float(M501.base_solution_kg_hr),
        "conditioning_dilution_water_kg_hr": float(M501.dilution_water_kg_hr),
        "conditioning_power_kw": conditioning_power,
        "digester_inlet_pH_metadata": float(M501.inlet_pH),
        "digester_pH_metadata": float(R501.parameters.digester_pH),
        "digester_temperature_c": float(R501.parameters.digester_temperature_c),
        "digester_hrt_days": float(sizing.actual_hrt_days if sizing else 0.0),
        "digester_srt_days": float(R501.parameters.srt_days if model.scenario.digestion_enabled else 0.0),
        "working_volume_m3": float(sizing.selected_working_volume_m3 if sizing else 0.0),
        "total_digester_volume_m3": float(sizing.total_volume_m3 if sizing else 0.0),
        "number_of_digesters": float(sizing.number_of_digesters if sizing else 0.0),
        "digester_volume_per_tank_m3": float(sizing.volume_per_digester_m3 if sizing else 0.0),
        "digester_diameter_m": float(geometry.diameter_m if geometry else 0.0),
        "digester_liquid_height_m": float(geometry.liquid_height_m if geometry else 0.0),
        "actual_cod_olr_kg_m3_day": float(sizing.actual_cod_olr_kg_m3_day if sizing else 0.0),
        "actual_vs_olr_kg_m3_day": float(sizing.actual_vs_olr_kg_m3_day if sizing else 0.0),
        "sizing_disagreement_fraction": float(sizing.maximum_sizing_disagreement_fraction if sizing else 0.0),
        "converted_substrate_cod_kg_hr": float(R501.converted_cod_kg_hr),
        "methane_cod_kg_hr": methane_cod,
        "methane_produced_kg_hr": methane_total,
        "methane_exported_kg_hr": float(raw_biogas.imass["Methane"]),
        "dissolved_methane_kg_hr": float(digestate.imass["Methane"]),
        "uncaptured_methane_kg_hr": float(uncaptured.imass["Methane"]),
        "biomass_produced_kg_hr": float(R501.generated_kg_hr.get("MicrobialBiomass", 0.0)),
        "ammonium_generated_kg_hr": float(R501.generated_kg_hr.get("Ammonium", 0.0)),
        "orthophosphate_generated_kg_hr": float(R501.generated_kg_hr.get("Orthophosphate", 0.0)),
        "hydrogen_sulfide_generated_kg_hr": float(R501.generated_kg_hr.get("HydrogenSulfide", 0.0)),
        "pH_inhibition_factor": float(R501.pH_factor),
        "ammonia_inhibition_factor": float(R501.ammonia_factor),
        "digestate_flow_kg_hr": digestate.F_mass,
        "digestate_cod_kg_hr": digestate_cod,
        "digestate_vs_kg_hr": digestate_vs,
        "digestate_total_n_kg_hr": digestate_elements["nitrogen"],
        "digestate_total_p_kg_hr": digestate_elements["phosphorus"],
        "digestate_total_s_kg_hr": digestate_elements["sulfur"],
        "cod_removal_fraction": _safe_ratio(feed_cod - digestate_cod, feed_cod),
        "vs_removal_fraction": _safe_ratio(feed_vs - digestate_vs, feed_vs),
        "methane_yield_nm3_per_kg_feed_cod": _safe_ratio(gas["raw_biogas_methane_nm3_hr"], feed_cod),
        "methane_yield_nm3_per_kg_converted_cod": _safe_ratio(gas["raw_biogas_methane_nm3_hr"], float(R501.converted_cod_kg_hr)),
        "methane_yield_nm3_per_kg_feed_vs": _safe_ratio(gas["raw_biogas_methane_nm3_hr"], feed_vs),
        "methane_yield_nm3_per_t_raw_liquid": _safe_ratio(gas["raw_biogas_methane_nm3_hr"] * 1000.0, upstream_raw.F_mass),
        "methane_yield_nm3_per_t_wet_grass": (
            _safe_ratio(gas["raw_biogas_methane_nm3_hr"] * 1000.0, grass.F_mass)
            if grass is not None else None
        ),
        "digester_preheat_kw": preheat,
        "digester_feed_cooling_kw": feed_cooling,
        "digester_vessel_heat_loss_kw": vessel_heat,
        "total_phase5_heat_kw": preheat + vessel_heat,
        "total_phase5_cooling_kw": feed_cooling,
        "digester_mixing_power_kw": mixing_power,
        "total_phase5_electricity_kw": conditioning_power + mixing_power,
    }
    values.update(gas)
    if validation is not None:
        values.update(
            mass_balance_error_kg_hr=validation.overall_error_kg_hr,
            cod_balance_error_kg_hr=validation.cod_balance["cod_balance_error_kg_o2_hr"],
            carbon_balance_error_kg_hr=validation.element_errors_kg_hr["carbon"],
            nitrogen_balance_error_kg_hr=validation.element_errors_kg_hr["nitrogen"],
            phosphorus_balance_error_kg_hr=validation.element_errors_kg_hr["phosphorus"],
            sulphur_balance_error_kg_hr=validation.element_errors_kg_hr["sulfur"],
        )
    return values


@dataclass(frozen=True)
class SeasonalPhase5Result:
    """Monthly quantities, annual totals, and peak sizing for one AD route."""

    monthly_rows: tuple[dict[str, object], ...]
    annual_totals: dict[str, float]
    peak_design: dict[str, float | str]
    warnings: tuple[str, ...]


def aggregate_monthly_phase5_metrics(
    monthly_models: list[object],
    warnings: tuple[str, ...] = (),
) -> SeasonalPhase5Result:
    """Aggregate independent monthly steady states using each month's hours."""

    rows: list[dict[str, object]] = []
    annual = {
        "digester_feed_kg": 0.0,
        "raw_biogas_nm3": 0.0,
        "methane_nm3": 0.0,
        "digestate_kg": 0.0,
        "pure_base_kg": 0.0,
        "phase5_heat_kwh": 0.0,
        "phase5_cooling_kwh": 0.0,
        "phase5_electricity_kwh": 0.0,
    }
    peak = {"month": "", "working_volume_m3": 0.0, "total_digester_volume_m3": 0.0}
    for model in monthly_models:
        metrics = model.metrics or calculate_phase5_metrics(model, model.validation)
        hours = (
            model.upstream_model.upstream_model.input_bundle.feed_specification.operating_days
            * 24.0
        )
        row: dict[str, object] = {
            "scenario": model.scenario.scenario_id,
            "phase4_scenario": model.input_bundle.phase4_scenario_id,
            "phase3_scenario": model.input_bundle.phase3_scenario_id,
            "month": model.input_bundle.selected_month,
            "operating_hours": hours,
            "digester_feed_kg": float(metrics["digester_feed_kg_hr"] or 0.0) * hours,
            "raw_biogas_nm3": float(metrics["wet_raw_biogas_nm3_hr"] or 0.0) * hours,
            "methane_nm3": float(metrics["raw_biogas_methane_nm3_hr"] or 0.0) * hours,
            "digestate_kg": float(metrics["digestate_flow_kg_hr"] or 0.0) * hours,
            "pure_base_kg": float(metrics["conditioning_pure_base_kg_hr"] or 0.0) * hours,
            "phase5_heat_kwh": float(metrics["total_phase5_heat_kw"] or 0.0) * hours,
            "phase5_cooling_kwh": float(metrics["total_phase5_cooling_kw"] or 0.0) * hours,
            "phase5_electricity_kwh": float(metrics["total_phase5_electricity_kw"] or 0.0) * hours,
            "working_volume_m3": float(metrics["working_volume_m3"] or 0.0),
            "total_digester_volume_m3": float(metrics["total_digester_volume_m3"] or 0.0),
            "methane_dry_mol_fraction": float(metrics["raw_biogas_methane_dry_mol_fraction"] or 0.0),
        }
        for name in annual:
            annual[name] += float(row[name])
        if float(row["working_volume_m3"]) > float(peak["working_volume_m3"]):
            peak = {
                "month": str(row["month"]),
                "working_volume_m3": float(row["working_volume_m3"]),
                "total_digester_volume_m3": float(row["total_digester_volume_m3"]),
            }
        rows.append(row)
    return SeasonalPhase5Result(tuple(rows), annual, peak, warnings)
