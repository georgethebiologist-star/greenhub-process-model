"""Complete, isolated, assumption-enabled dynamic proxy calculations.

The conservative dynamic and empirical pathways remain unchanged. This module
composes the existing protein calculation-shadow path with traceable closure
policies for drying, AD, gas handling, and resource recovery. It is intended
for scenario inspection only and never represents validated GreenHub data.
"""

from __future__ import annotations

import csv
import json
import math
from collections import Counter
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Iterable, Mapping

from Greenhub.dynamic_integrated_proxy import (
    BiogasUpgradingMethod,
    DynamicDryingMethod,
    DynamicIntegratedProxyConfig,
    ResourceRecoveryMethod,
    build_dynamic_biogas_upgrading_policy,
    run_dynamic_integrated_proxy_scenario_step,
)
from Greenhub.dynamic_process import ProteinExtractionMethod
from Greenhub.time_grid import generate_time_grid


RESULTS_DIR = Path(__file__).resolve().parent / "results"
DATA_ROOT = Path(__file__).resolve().parent / "data"
LEGACY_RESULTS = RESULTS_DIR
MASS_TOLERANCE_KG_HR = 1e-8
STANDARD_MOLAR_VOLUME_M3_PER_KMOL = 22.414
MW_CH4_KG_PER_KMOL = 16.043
MW_CO2_KG_PER_KMOL = 44.009
MW_NH3_KG_PER_KMOL = 17.031
MW_H2S_KG_PER_KMOL = 34.081


@dataclass(frozen=True)
class TraceableProxyValue:
    """One scalar closure value with mandatory provenance and warning."""

    name: str
    value: float
    unit: str
    policy_id: str
    source_status: str
    certainty_class: str
    source_file: str = ""
    source_id: str = ""
    warning: str = ""

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True)
class DynamicCompleteProxyClosurePolicy:
    """All values that close the downstream proxy model, each fully traced."""

    policy_id: str
    values: tuple[TraceableProxyValue, ...]
    allow_assumptions: bool
    warnings: tuple[str, ...]
    activation_status: str = "complete_proxy_report_only"

    def get(self, name: str) -> TraceableProxyValue:
        for item in self.values:
            if item.name == name:
                return item
        raise KeyError(f"Complete proxy policy has no value named {name!r}.")

    def available(self, name: str) -> bool:
        return any(item.name == name for item in self.values)

    def to_dict(self) -> dict[str, object]:
        return {
            "policy_id": self.policy_id,
            "values": [item.to_dict() for item in self.values],
            "allow_assumptions": self.allow_assumptions,
            "warnings": list(self.warnings),
            "activation_status": self.activation_status,
        }


@dataclass(frozen=True)
class DynamicCompleteProxyConfig:
    """Opt-in configuration for the complete monthly proxy chain."""

    scenario_id: str = "dynamic_complete_proxy_baseline"
    start_date: str = "2026-05-01"
    end_date: str = "2026-11-30"
    time_step: str = "monthly"
    basis_feed_kg_per_hr: float = 1000.0
    protein_method: str = ProteinExtractionMethod.ISOELECTRIC.value
    drying_method: str = DynamicDryingMethod.MASS_ONLY.value
    ad_method: str = "bmp_material_conversion_proxy"
    upgrading_method: str = BiogasUpgradingMethod.WATER_SCRUBBING.value
    resource_recovery_methods: tuple[str, ...] = (
        ResourceRecoveryMethod.DIGESTATE_SEPARATION.value,
        ResourceRecoveryMethod.AMMONIA_RECOVERY.value,
        ResourceRecoveryMethod.PHOSPHORUS_RECOVERY.value,
        ResourceRecoveryMethod.POTASSIUM_WATER_CONCENTRATION.value,
        ResourceRecoveryMethod.ION_EXCHANGE.value,
    )
    drying_target_moisture_fraction: float = 0.15
    allow_assumptions: bool = True
    allow_proxy: bool = True
    include_press_cake_in_biogas: bool = False
    generic_protein_recovery_fraction: float | None = None
    generic_protein_policy_id: str = ""
    generic_protein_provenance_note: str = ""
    provenance: dict[str, object] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.scenario_id.strip():
            raise ValueError("scenario_id must not be empty.")
        if not math.isfinite(self.basis_feed_kg_per_hr) or self.basis_feed_kg_per_hr <= 0:
            raise ValueError("basis_feed_kg_per_hr must be finite and greater than zero.")
        if not 0.0 <= self.drying_target_moisture_fraction < 1.0:
            raise ValueError("drying_target_moisture_fraction must be in [0, 1).")
        ProteinExtractionMethod(self.protein_method)
        DynamicDryingMethod(self.drying_method)
        BiogasUpgradingMethod(self.upgrading_method)
        valid_resources = {item.value for item in ResourceRecoveryMethod}
        unknown = sorted(set(self.resource_recovery_methods) - valid_resources)
        if unknown:
            raise ValueError(f"Unknown resource recovery methods: {', '.join(unknown)}.")
        if len(self.resource_recovery_methods) != len(set(self.resource_recovery_methods)):
            raise ValueError("resource_recovery_methods must not contain duplicates.")
        if self.include_press_cake_in_biogas:
            raise ValueError("Press cake is an external output and cannot enter in-project AD.")
        if self.ad_method != "bmp_material_conversion_proxy":
            raise ValueError("ad_method currently supports only 'bmp_material_conversion_proxy'.")
        generate_time_grid(self.start_date, self.end_date, self.time_step)

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True)
class CompleteProxyStream:
    stream_id: str
    mass_kg_hr: float
    components_kg_hr: dict[str, float]
    metadata_kg_hr: dict[str, float]
    source_unit: str
    destination: str
    source_status: str
    warnings: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True)
class CompleteProxyUnitResult:
    unit_id: str
    method: str
    input_mass_kg_hr: float
    external_input_mass_kg_hr: float
    output_mass_kg_hr: float
    residual_kg_hr: float
    outputs: tuple[CompleteProxyStream, ...]
    metrics: dict[str, float | str | bool | None]
    evidence: tuple[TraceableProxyValue, ...]
    warnings: tuple[str, ...]
    blockers: tuple[str, ...]
    identity_closes: bool

    def to_dict(self) -> dict[str, object]:
        return {
            **asdict(self),
            "outputs": [item.to_dict() for item in self.outputs],
            "evidence": [item.to_dict() for item in self.evidence],
        }


@dataclass(frozen=True)
class DynamicCompleteProxyStepResult:
    scenario_id: str
    time_label: str
    config: DynamicCompleteProxyConfig
    closure_policy: DynamicCompleteProxyClosurePolicy
    protein_result: object
    drying: CompleteProxyUnitResult
    ad: CompleteProxyUnitResult
    gas_route: CompleteProxyUnitResult
    resource_recovery: tuple[CompleteProxyUnitResult, ...]
    system_outputs: dict[str, CompleteProxyStream]
    product_outputs: dict[str, float]
    energy_summary: dict[str, float]
    selected_alternatives: dict[str, object]
    warnings: tuple[str, ...]
    blockers: tuple[str, ...]
    balances: dict[str, float | bool]
    provenance: dict[str, object]
    can_drive_proxy_preview: bool
    can_drive_calculation_shadow_system: bool
    can_drive_complete_proxy_model: bool
    can_drive_simulation: bool = False
    validated_simulation_ready: bool = False
    activation_status: str = "complete_proxy_assumption_enabled_report_only"

    def to_dict(self, *, include_protein_result: bool = False) -> dict[str, object]:
        return {
            "scenario_id": self.scenario_id,
            "time_label": self.time_label,
            "config": self.config.to_dict(),
            "closure_policy": self.closure_policy.to_dict(),
            "protein_result": (
                self.protein_result.to_dict() if include_protein_result else {
                    "selected_method": self.config.protein_method,
                    "underlying_method": self.protein_result.protein_run.selected_method,
                    "policy_ids": dict(self.protein_result.protein_run.policy_ids),
                }
            ),
            "drying": self.drying.to_dict(),
            "ad": self.ad.to_dict(),
            "gas_route": self.gas_route.to_dict(),
            "resource_recovery": [item.to_dict() for item in self.resource_recovery],
            "system_outputs": {key: value.to_dict() for key, value in self.system_outputs.items()},
            "product_outputs": dict(self.product_outputs),
            "energy_summary": dict(self.energy_summary),
            "selected_alternatives": dict(self.selected_alternatives),
            "warnings": list(self.warnings),
            "blockers": list(self.blockers),
            "balances": dict(self.balances),
            "provenance": dict(self.provenance),
            "can_drive_proxy_preview": self.can_drive_proxy_preview,
            "can_drive_calculation_shadow_system": self.can_drive_calculation_shadow_system,
            "can_drive_complete_proxy_model": self.can_drive_complete_proxy_model,
            "can_drive_simulation": self.can_drive_simulation,
            "validated_simulation_ready": self.validated_simulation_ready,
            "activation_status": self.activation_status,
        }


@dataclass(frozen=True)
class DynamicCompleteProxyGridResult:
    config: DynamicCompleteProxyConfig
    steps: tuple[DynamicCompleteProxyStepResult, ...]
    time_labels: tuple[str, ...]
    output_ranges: dict[str, dict[str, float]]
    blocker_counts: dict[str, int]
    warning_counts: dict[str, int]
    can_drive_complete_proxy_model_all_steps: bool
    mass_balances_close_all_steps: bool
    can_drive_simulation: bool = False
    validated_simulation_ready: bool = False
    activation_status: str = "complete_proxy_grid_report_only"

    def to_dict(self) -> dict[str, object]:
        return {
            "config": self.config.to_dict(),
            "steps": [item.to_dict() for item in self.steps],
            "time_labels": list(self.time_labels),
            "output_ranges": {key: dict(value) for key, value in self.output_ranges.items()},
            "blocker_counts": dict(self.blocker_counts),
            "warning_counts": dict(self.warning_counts),
            "can_drive_complete_proxy_model_all_steps": self.can_drive_complete_proxy_model_all_steps,
            "mass_balances_close_all_steps": self.mass_balances_close_all_steps,
            "can_drive_simulation": self.can_drive_simulation,
            "validated_simulation_ready": self.validated_simulation_ready,
            "activation_status": self.activation_status,
        }


def default_dynamic_complete_proxy_closure_policy(
    allow_assumptions: bool = True,
    target_moisture_fraction: float = 0.15,
) -> DynamicCompleteProxyClosurePolicy:
    """Build the audited dataset/legacy/assumption closure policy."""

    values = [
        _value("target_moisture_fraction", target_moisture_fraction, "kg water/kg wet product", "SCENARIO-DRY-TARGET", "user_input", "scenario input", "", "drying_target_moisture_fraction", "baseline is 0.15 and may be changed by a future scenario interface"),
        _value("bmp_ch4", 0.52028, "m3 CH4/kg VS", "BMP_DFOS_VS", "direct_dataset", "B-class grass-whey proxy", "Greenhub/data/Bigas production + upgrade/Feed BMP/ad_bmp_observations.csv", "BMP_DFOS_VS", "de-FOS whey is transferable only as a supernatant-like residual proxy"),
        _value("raw_biogas_ch4_fraction", 0.871, "m3 CH4/m3 dry gas", "BMP_DFOS_CH4FRAC", "direct_dataset", "B-class grass-whey proxy", "Greenhub/data/Bigas production + upgrade/Feed BMP/ad_bmp_observations.csv", "BMP_DFOS_CH4FRAC", "reported BMP bottle gas fraction, not GreenHub reactor validation"),
        _value("ad_t80_days", 5.0, "day", "BMP_DFOS_T80", "direct_dataset", "B-class grass-whey proxy", "Greenhub/data/Bigas production + upgrade/Feed BMP/ad_bmp_observations.csv", "BMP_DFOS_T80", "BMP bottle time marker; it is not a fitted dynamic reactor rate"),
        _value("ad_t90_days", 11.0, "day", "BMP_DFOS_T90", "direct_dataset", "B-class grass-whey proxy", "Greenhub/data/Bigas production + upgrade/Feed BMP/ad_bmp_observations.csv", "BMP_DFOS_T90", "BMP bottle time marker; it is not a fitted dynamic reactor rate"),
        _value("ad_hrt_days", 25.0, "day", "GH-LEGACY-AD1-HRT", "greenhub_legacy_proxy_result", "C-class internal model proxy", "Greenhub/results/digester_design_report.csv", "AD1_actual_HRT", "legacy structural digester sizing result, not selected dynamic kinetics"),
        _value("ad_heat_kwh_per_kg_feed", 1.4843796915999 / (0.2451051352196324 * 1000.0), "kWh/kg wet AD feed", "GH-LEGACY-AD1-HEAT", "greenhub_legacy_proxy_result", "C-class internal model proxy", "Greenhub/results/digester_design_report.csv", "AD1_total_external_heat", "legacy heat/load ratio assumes digestate-like density and is not a validated utility model"),
        _value("dryer_heat_mj_per_kg_water", 3.8581196581196577, "MJ/kg water", "GH-LEGACY-DRYER-PR3", "greenhub_legacy_proxy_result", "C-class internal model proxy", "Greenhub/results/dryer_energy_balance.csv", "PR3", "derived from legacy external heat divided by latent-water removal"),
        _value("dryer_electricity_kwh_per_kg_water", 0.15, "kWh/kg water", "GH-LEGACY-DRYER-PR3", "greenhub_legacy_proxy_result", "C-class internal model proxy", "Greenhub/results/dryer_energy_balance.csv", "PR3", "legacy utility-only dryer result; air system is not rigorous"),
        _value("digestate_ts_to_solids", 0.481, "fraction", "SP_TS_SOL", "direct_dataset", "B-class digestate proxy", "Greenhub/data/Resource recovery/Digestate_and_Separation/digestate_separation_performance.csv", "SP_TS_SOL", "typical mixed digestate performance, not GreenHub digestate validation"),
        _value("digestate_water_to_solids", 56.0 / 972.0, "fraction", "DC_2P8TS_WATER", "direct_dataset", "C-class decanter proxy", "Greenhub/data/Resource recovery/Digestate_and_Separation/digestate_separation_performance.csv", "DC_2P8TS_water_solid", "water split reconstructed from one source mass balance"),
        _value("digestate_n_to_solids", 0.17, "fraction", "SP_TN_SOL", "direct_dataset", "B-class digestate proxy", "Greenhub/data/Resource recovery/Digestate_and_Separation/digestate_separation_performance.csv", "SP_TN_SOL", "total-N partition, not ionic speciation"),
        _value("digestate_p_to_solids", 0.218, "fraction", "SP_PO4P_SOL", "direct_dataset", "B-class digestate proxy", "Greenhub/data/Resource recovery/Digestate_and_Separation/digestate_separation_performance.csv", "SP_PO4P_SOL", "orthophosphate-P proxy applied to proxy-speciated P"),
        _value("digestate_k_to_solids", 0.10, "fraction", "SP_K_SOL", "direct_dataset", "B-class digestate proxy", "Greenhub/data/Resource recovery/Digestate_and_Separation/digestate_separation_performance.csv", "SP_K_SOL", "typical K partition, not GreenHub validation"),
        _value("ammonia_recovery_fraction", 0.81, "fraction", "EX_ABBA_REM", "direct_dataset", "B-class livestock-digestate proxy", "Greenhub/data/Resource recovery/Ammonia_Recovery/ammonia_stripping_experiments.csv", "EX_ABBA_REM", "maximum reported removal; matrix and scale differ"),
        _value("phosphate_recovery_fraction", 0.988, "fraction", "EXP_KOLB_85", "direct_dataset", "C-class municipal-centrate proxy", "Greenhub/data/Resource recovery/Phosphorus_Recovery/precipitation_experiments.csv", "EXP_KOLB_85", "source-specific pH 8.5 result"),
        _value("clean_water_recovery_fraction", 0.51, "fraction", "WATER_REC", "direct_dataset", "B-class pilot digestate proxy", "Greenhub/data/Resource recovery/Potassium_and_Water_Concentration/water_recovery_and_quality.csv", "WATER_REC", "integrated membrane/SED train result, not RO-only"),
        _value("chp_electrical_efficiency", 0.345, "fraction", "CHP_PERF_E02", "direct_dataset", "B-class engine proxy", "Greenhub/data/Bigas production + upgrade/CHP_and_Utilities/chp_engine_performance.csv", "CHP_PERF_E02", "natural-gas rated engine; cleaned-biogas derating is unresolved"),
        _value("chp_thermal_efficiency", 0.444, "fraction", "CHP_PERF_E02", "direct_dataset", "B-class engine proxy", "Greenhub/data/Bigas production + upgrade/CHP_and_Utilities/chp_engine_performance.csv", "CHP_PERF_E02", "natural-gas rated engine; heat-use integration is unresolved"),
        _value("methane_lhv_kwh_per_m3", 9.94, "kWh/m3 CH4", "EQ-LHV-CH4-001", "literature_proxy", "B-class physical-property proxy", "Greenhub/data/Bigas production + upgrade/CHP_and_Utilities/chp_engine_performance.csv", "CH4_LHV_PROXY", "normal-volume basis must match the BMP gas basis"),
        _value("mea_electricity_kwh_per_m3", 0.14, "kWh/m3 raw gas", "MEA_EN_003", "direct_dataset", "B-class technology proxy", "Greenhub/data/Bigas production + upgrade/MEA/energy_and_duties.csv", "MEA_EN_003", "technology-scale energy value is not validated for GreenHub"),
        _value("mea_heat_kwh_per_m3", 0.55, "kWh/m3 raw gas", "MEA_EN_002", "direct_dataset", "B-class technology proxy", "Greenhub/data/Bigas production + upgrade/MEA/energy_and_duties.csv", "MEA_EN_002", "technology-scale heat value is not validated for GreenHub"),
    ]
    if allow_assumptions:
        values.extend([
            _assumption("standard_molar_volume", STANDARD_MOLAR_VOLUME_M3_PER_KMOL, "m3/kmol", "ASSUMP-AD-001", "normal gas conversion at 0 degC and 101325 Pa"),
            _assumption("bmp_realization_fraction", 1.0, "fraction of BMP potential", "ASSUMP-AD-004", "complete proxy assumes the selected BMP potential is realized; no kinetic reactor model is executed"),
            _assumption("ad_nh3_n_loss_fraction", 0.01, "kg gas-N/kg residual N", "ASSUMP-AD-002", "trace NH3 closes the proxy gas/digestate nitrogen ledger"),
            _assumption("ad_h2s_s_loss_fraction", 0.10, "kg gas-S/kg residual S", "ASSUMP-AD-003", "trace H2S closes the proxy gas/digestate sulfur ledger"),
            _assumption("residual_n_routing_fraction", 0.50, "fraction of whole-feed N", "ASSUMP-NUT-001", "elemental partition through protein recovery is not measured"),
            _assumption("residual_s_routing_fraction", 0.50, "fraction of whole-feed S", "ASSUMP-NUT-002", "elemental partition through protein recovery is not measured"),
            _assumption("phosphorus_dry_basis", 0.0035, "kg P/kg feed DM", "ASSUMP-NUT-003", "feed phosphorus is absent from the first dynamic field set"),
            _assumption("potassium_dry_basis", 0.025, "kg K/kg feed DM", "ASSUMP-NUT-004", "feed potassium is absent from the first dynamic field set"),
            _assumption("tan_fraction_total_n", 0.6288, "kg TAN-N/kg total N", "GH-LEGACY-P7-TAN", "legacy Phase 7 feed TAN/total-N ratio closes ionic speciation", source_status="greenhub_legacy_proxy_result", source_file="Greenhub/results/phase7_selected_metrics.csv"),
            _assumption("po4_fraction_total_p", 0.75, "kg PO4-P/kg total P", "ASSUMP-NUT-005", "orthophosphate fraction is needed for proxy struvite routing"),
            _assumption("k_ionic_fraction", 0.95, "kg ionic K/kg total K", "ASSUMP-NUT-006", "ionic potassium fraction is not measured"),
            _assumption("struvite_mass_per_kg_p", 245.41 / 30.973761998, "kg struvite/kg P", "EQ-STRUVITE-001", "ideal MgNH4PO4.6H2O stoichiometry; ignores competing ions"),
            _assumption("ammonium_salt_mass_per_kg_n", 1.5955786687313684 / 0.33826052553119096, "kg product/kg N", "GH-LEGACY-P7-AMMONIUM", "legacy Phase 7 ammonium product ratio includes acid and product water", source_status="greenhub_legacy_proxy_result", source_file="Greenhub/results/phase7_selected_metrics.csv"),
            _assumption("ion_exchange_remaining_tan_recovery", 0.85, "fraction", "ASSUMP-IX-001", "needed to close a report-only loaded-media product candidate"),
            _assumption("potassium_concentrate_k_fraction", 0.10, "kg K/kg wet concentrate", "ASSUMP-K-001", "product concentration is a scenario closure, not product validation"),
            _assumption("mea_methane_recovery", 0.995, "fraction", "ASSUMP-MEA-001", "MEA methane recovery is missing from the project dataset"),
            _assumption("mea_product_methane_fraction", 0.99, "fraction", "ASSUMP-MEA-002", "MEA product purity is a scenario closure"),
            _assumption("common_conditioning_electricity", 0.1642, "kWh/m3 raw gas", "GH-LEGACY-P6-COND-ENERGY", "legacy Phase 6 utilities normalized to raw gas flow", source_status="greenhub_legacy_proxy_result", source_file="Greenhub/results/phase6_energy_summary.csv"),
            _assumption("freeze_drying_electricity", 1.50, "kWh/kg water", "ASSUMP-DRY-FD-001", "no transferable scalar freeze-drying energy exists in the project data"),
        ])
    return DynamicCompleteProxyClosurePolicy(
        policy_id=("complete_proxy_closure_v1" if allow_assumptions else "complete_proxy_datasets_only_v1"),
        values=tuple(values),
        allow_assumptions=allow_assumptions,
        warnings=(
            "complete proxy closure is not measured GreenHub performance",
            "legacy result ratios are internal model references, not experimental truth",
            "validated_simulation_ready remains false",
        ),
    )


def run_dynamic_complete_proxy_scenario_step(
    config: DynamicCompleteProxyConfig,
    time_label: str,
) -> DynamicCompleteProxyStepResult:
    """Run one independent complete-proxy month without touching global flowsheets."""

    policy = default_dynamic_complete_proxy_closure_policy(
        config.allow_assumptions,
        config.drying_target_moisture_fraction,
    )
    integrated_config, protein_warning = _integrated_config(config)
    protein = run_dynamic_integrated_proxy_scenario_step(integrated_config, time_label)
    drying = _complete_drying(protein, config, policy)
    ad = _complete_ad(protein, config, policy)
    gas = _complete_gas_route(ad, config, policy)
    resources = _complete_resource_recovery(ad, config, policy)
    resource_outputs = {stream.stream_id: stream for unit in resources for stream in unit.outputs}
    protein_streams = _protein_system_streams(protein, config.basis_feed_kg_per_hr)
    system_outputs = {
        "press_cake": protein_streams["press_cake"],
        "dried_protein_product": protein_streams["dried_protein_product"],
        **{stream.stream_id: stream for stream in gas.outputs},
        **resource_outputs,
    }
    warnings = tuple(
        warning
        for warning in dict.fromkeys((
            *policy.warnings,
            *(protein_warning,),
            *drying.warnings,
            *ad.warnings,
            *gas.warnings,
            *(warning for unit in resources for warning in unit.warnings),
        ))
        if warning
    )
    blockers = tuple(dict.fromkeys((
        *drying.blockers,
        *ad.blockers,
        *gas.blockers,
        *(blocker for unit in resources for blocker in unit.blockers),
        *(("protein_proxy_closure_disabled",) if not config.allow_assumptions else ()),
        *(("protein_pathway_not_calculation_ready",) if not protein.can_drive_calculation_shadow_system else ()),
    )))
    all_units = (drying, ad, gas, *resources)
    balances_close = all(unit.identity_closes for unit in all_units)
    complete = config.allow_assumptions and not blockers and balances_close and protein.can_drive_calculation_shadow_system
    products = {
        "press_cake_kg_hr": protein_streams["press_cake"].mass_kg_hr,
        "dried_protein_product_kg_hr": protein_streams["dried_protein_product"].mass_kg_hr,
        "dried_product_protein_kg_hr": protein.protein_run.protein_metrics_kg_per_kg_feed.get("dried_product_protein", 0.0) * config.basis_feed_kg_per_hr,
        "methane_kg_hr": float(ad.metrics.get("methane_kg_hr") or 0.0),
        "methane_m3_hr": float(ad.metrics.get("methane_m3_hr") or 0.0),
        "digestate_kg_hr": _stream(ad, "digestate").mass_kg_hr,
        **{f"{name}_kg_hr": stream.mass_kg_hr for name, stream in resource_outputs.items()},
    }
    products.update({key: float(value) for key, value in gas.metrics.items() if isinstance(value, (int, float)) and ("kg_hr" in key or "m3_hr" in key or "kwh_hr" in key)})
    return DynamicCompleteProxyStepResult(
        scenario_id=config.scenario_id,
        time_label=time_label,
        config=config,
        closure_policy=policy,
        protein_result=protein,
        drying=drying,
        ad=ad,
        gas_route=gas,
        resource_recovery=resources,
        system_outputs=system_outputs,
        product_outputs=products,
        energy_summary={
            "drying_heat_mj_hr": float(drying.metrics.get("heat_demand_mj_hr") or 0.0),
            "drying_electricity_kwh_hr": float(drying.metrics.get("electricity_kwh_hr") or 0.0),
            "gas_electricity_kwh_hr": float(gas.metrics.get("electricity_kwh_hr") or 0.0),
            "gas_heat_demand_kwh_hr": float(gas.metrics.get("heat_demand_kwh_hr") or 0.0),
            "ad_heat_demand_kwh_hr": float(ad.metrics.get("heat_demand_kwh_hr") or 0.0),
            "chp_electricity_output_kwh_hr": float(gas.metrics.get("chp_electricity_output_kwh_hr") or 0.0),
            "chp_heat_output_kwh_hr": float(gas.metrics.get("chp_heat_output_kwh_hr") or 0.0),
            "resource_electricity_kwh_hr": sum(float(unit.metrics.get("electricity_kwh_hr") or 0.0) for unit in resources),
            "resource_heat_kwh_hr": sum(float(unit.metrics.get("heat_demand_kwh_hr") or 0.0) for unit in resources),
        },
        selected_alternatives={
            "protein_method": config.protein_method,
            "drying_method": config.drying_method,
            "ad_method": config.ad_method,
            "upgrading_or_energy_route": config.upgrading_method,
            "resource_recovery_methods": list(config.resource_recovery_methods),
        },
        warnings=warnings,
        blockers=blockers,
        balances={
            "all_downstream_unit_balances_close": balances_close,
            "max_unit_residual_kg_hr": max(abs(unit.residual_kg_hr) for unit in all_units),
            "press_cake_in_ad": False,
        },
        provenance={
            "policy_id": policy.policy_id,
            "protein_policy_ids": dict(protein.protein_run.policy_ids),
            "press_cake_boundary": "external_system_output",
            "empirical_model_modified": False,
            "model_overrides": [],
        },
        can_drive_proxy_preview=protein.can_drive_proxy_preview,
        can_drive_calculation_shadow_system=protein.can_drive_calculation_shadow_system,
        can_drive_complete_proxy_model=complete,
    )


def run_dynamic_complete_proxy_scenario_grid(
    config: DynamicCompleteProxyConfig | None = None,
) -> DynamicCompleteProxyGridResult:
    config = config or DynamicCompleteProxyConfig()
    steps = tuple(
        run_dynamic_complete_proxy_scenario_step(config, item.label)
        for item in generate_time_grid(config.start_date, config.end_date, config.time_step)
    )
    keys = sorted({key for step in steps for key in step.product_outputs})
    ranges = {
        key: {
            "min": min(float(step.product_outputs.get(key, 0.0)) for step in steps),
            "max": max(float(step.product_outputs.get(key, 0.0)) for step in steps),
        }
        for key in keys
    }
    return DynamicCompleteProxyGridResult(
        config=config,
        steps=steps,
        time_labels=tuple(step.time_label for step in steps),
        output_ranges=ranges,
        blocker_counts=dict(sorted(Counter(item for step in steps for item in step.blockers).items())),
        warning_counts=dict(sorted(Counter(item for step in steps for item in step.warnings if item).items())),
        can_drive_complete_proxy_model_all_steps=all(step.can_drive_complete_proxy_model for step in steps),
        mass_balances_close_all_steps=all(bool(step.balances["all_downstream_unit_balances_close"]) for step in steps),
    )


def summarize_dynamic_complete_proxy_grid(
    result: DynamicCompleteProxyGridResult,
) -> dict[str, object]:
    return {
        "scenario_id": result.config.scenario_id,
        "time_labels": list(result.time_labels),
        "selected_alternatives": {
            "protein_method": result.config.protein_method,
            "drying_method": result.config.drying_method,
            "ad_method": result.config.ad_method,
            "upgrading_or_energy_route": result.config.upgrading_method,
            "resource_recovery_methods": list(result.config.resource_recovery_methods),
        },
        "output_ranges": {key: dict(value) for key, value in result.output_ranges.items()},
        "blocker_counts": dict(result.blocker_counts),
        "warning_counts": dict(result.warning_counts),
        "can_drive_proxy_preview_all_steps": all(step.can_drive_proxy_preview for step in result.steps),
        "can_drive_calculation_shadow_system_all_steps": all(step.can_drive_calculation_shadow_system for step in result.steps),
        "can_drive_complete_proxy_model_all_steps": result.can_drive_complete_proxy_model_all_steps,
        "mass_balances_close_all_steps": result.mass_balances_close_all_steps,
        "can_drive_simulation": False,
        "validated_simulation_ready": False,
        "next_validation_needs": [
            "project-measured residual COD, VS destruction, and elemental partitions",
            "GreenHub gas-upgrading performance and utilities at selected scale",
            "digestate TAN/PO4/K speciation and recovery tests",
            "dryer trials and complete utility integration",
        ],
    }


def write_dynamic_complete_proxy_reports(
    result: DynamicCompleteProxyGridResult,
    output_dir: str | Path | None = None,
) -> dict[str, str]:
    target = Path(output_dir) if output_dir is not None else RESULTS_DIR
    target.mkdir(parents=True, exist_ok=True)
    names = (
        "summary", "streams", "units", "alternatives", "assumptions", "balances", "blockers"
    )
    paths = {name: target / f"dynamic_complete_proxy_{name}.csv" for name in names}
    summary_rows: list[dict[str, object]] = []
    stream_rows: list[dict[str, object]] = []
    unit_rows: list[dict[str, object]] = []
    alternative_rows: list[dict[str, object]] = []
    assumption_rows: list[dict[str, object]] = []
    balance_rows: list[dict[str, object]] = []
    blocker_rows: list[dict[str, object]] = []
    for step in result.steps:
        summary_rows.append({
            "scenario_id": step.scenario_id,
            "time_label": step.time_label,
            "can_drive_complete_proxy_model": step.can_drive_complete_proxy_model,
            "can_drive_simulation": False,
            "validated_simulation_ready": False,
            "selected_alternatives": json.dumps(step.selected_alternatives, sort_keys=True),
            "product_outputs": json.dumps(step.product_outputs, sort_keys=True),
            "energy_summary": json.dumps(step.energy_summary, sort_keys=True),
        })
        units = (step.drying, step.ad, step.gas_route, *step.resource_recovery)
        for unit in units:
            unit_rows.append({
                "scenario_id": step.scenario_id, "time_label": step.time_label,
                "unit_id": unit.unit_id, "method": unit.method,
                "input_mass_kg_hr": unit.input_mass_kg_hr,
                "external_input_mass_kg_hr": unit.external_input_mass_kg_hr,
                "output_mass_kg_hr": unit.output_mass_kg_hr,
                "residual_kg_hr": unit.residual_kg_hr,
                "identity_closes": unit.identity_closes,
                "metrics": json.dumps(unit.metrics, sort_keys=True),
            })
            balance_rows.append({
                "scenario_id": step.scenario_id, "time_label": step.time_label,
                "unit_id": unit.unit_id, "input_plus_external_kg_hr": unit.input_mass_kg_hr + unit.external_input_mass_kg_hr,
                "output_kg_hr": unit.output_mass_kg_hr, "residual_kg_hr": unit.residual_kg_hr,
                "identity_closes": unit.identity_closes,
            })
            for stream in unit.outputs:
                entries = [(name, mass, "", "") for name, mass in stream.components_kg_hr.items()]
                entries += [("", "", name, mass) for name, mass in stream.metadata_kg_hr.items()]
                if not entries:
                    entries = [("", "", "", "")]
                for component, component_mass, metadata, metadata_mass in entries:
                    stream_rows.append({
                        "scenario_id": step.scenario_id, "time_label": step.time_label,
                        "unit_id": unit.unit_id, "stream_id": stream.stream_id,
                        "stream_mass_kg_hr": stream.mass_kg_hr,
                        "component": component, "component_mass_kg_hr": component_mass,
                        "metadata_pool": metadata, "metadata_mass_kg_hr": metadata_mass,
                        "source_status": stream.source_status,
                    })
        for name, selection in step.selected_alternatives.items():
            alternative_rows.append({
                "scenario_id": step.scenario_id, "time_label": step.time_label,
                "category": name, "selected": json.dumps(selection), "active": True,
            })
        for item in step.closure_policy.values:
            assumption_rows.append({"scenario_id": step.scenario_id, "time_label": step.time_label, **item.to_dict()})
        for warning in step.warnings:
            blocker_rows.append({"scenario_id": step.scenario_id, "time_label": step.time_label, "record_type": "warning", "message": warning})
        for blocker in step.blockers:
            blocker_rows.append({"scenario_id": step.scenario_id, "time_label": step.time_label, "record_type": "blocker", "message": blocker})
    _write_rows(paths["summary"], summary_rows)
    _write_rows(paths["streams"], stream_rows)
    _write_rows(paths["units"], unit_rows)
    _write_rows(paths["alternatives"], alternative_rows)
    _write_rows(paths["assumptions"], assumption_rows)
    _write_rows(paths["balances"], balance_rows)
    _write_rows(paths["blockers"], blocker_rows, fallback_fields=("scenario_id", "time_label", "record_type", "message"))
    return {key: str(path) for key, path in paths.items()}


def _integrated_config(config: DynamicCompleteProxyConfig) -> tuple[DynamicIntegratedProxyConfig, str]:
    method = config.protein_method
    generic_fraction = config.generic_protein_recovery_fraction
    generic_id = config.generic_protein_policy_id
    generic_note = config.generic_protein_provenance_note
    warning = ""
    if method == ProteinExtractionMethod.HEAT.value and config.allow_assumptions:
        method = ProteinExtractionMethod.GENERIC.value
        generic_fraction = 0.34 if generic_fraction is None else generic_fraction
        generic_id = generic_id or "ASSUMP-PROTEIN-HEAT-001"
        generic_note = generic_note or "heat route represented by explicit generic recovery solely to close proxy mode"
        warning = f"HEAT PROXY: no audited heat-recovery dataset; explicit generic {generic_fraction:g} recovery closure used"
    elif method == ProteinExtractionMethod.GENERIC.value and config.allow_assumptions and generic_fraction is None:
        generic_fraction = 0.34
        generic_id = "ASSUMP-PROTEIN-GENERIC-001"
        generic_note = "explicit complete-proxy generic recovery assumption"
        warning = "GENERIC PROXY: 0.34 recovery is an engineering closure, not measured performance"
    return DynamicIntegratedProxyConfig(
        scenario_id=config.scenario_id,
        start_date=config.start_date,
        end_date=config.end_date,
        time_step=config.time_step,
        basis_feed_kg_per_hr=config.basis_feed_kg_per_hr,
        protein_method=method,
        drying_method=DynamicDryingMethod.MASS_ONLY.value,
        drying_target_moisture_fraction=config.drying_target_moisture_fraction,
        upgrading_method=BiogasUpgradingMethod.NONE.value,
        fertilizer_methods=(),
        allow_proxy=config.allow_proxy,
        # The established protein shadow builder cannot instantiate a partially
        # blocked press system. Retain its closed stream scaffold for reporting,
        # then add an explicit complete-layer blocker when assumptions are off.
        allow_engineering_proxy_closure=True,
        allow_n_to_protein_proxy=True,
        generic_protein_recovery_fraction=generic_fraction,
        generic_protein_policy_id=generic_id,
        generic_protein_provenance_note=generic_note,
        include_press_cake_in_biogas=False,
        provenance={**config.provenance, "complete_proxy_parent": config.scenario_id, "requested_protein_method": config.protein_method},
    ), warning


def _complete_drying(protein: object, config: DynamicCompleteProxyConfig, policy: DynamicCompleteProxyClosurePolicy) -> CompleteProxyUnitResult:
    water = protein.protein_run.output_masses_kg_per_kg_feed.get("evaporated_water", 0.0) * config.basis_feed_kg_per_hr
    evidence: list[TraceableProxyValue] = []
    blockers: list[str] = []
    heat = electricity = 0.0
    method = DynamicDryingMethod(config.drying_method)
    evidence.append(policy.get("target_moisture_fraction"))
    if method is DynamicDryingMethod.FREEZE_DRYING_PROXY:
        if policy.available("freeze_drying_electricity"):
            item = policy.get("freeze_drying_electricity")
            evidence.append(item)
            electricity = water * item.value
        else:
            blockers.append("freeze_drying_energy_missing_without_assumptions")
    elif method is DynamicDryingMethod.SPRAY_DRYING_PROXY:
        for name in ("dryer_heat_mj_per_kg_water", "dryer_electricity_kwh_per_kg_water"):
            item = policy.get(name)
            evidence.append(item)
        heat = water * policy.get("dryer_heat_mj_per_kg_water").value
        electricity = water * policy.get("dryer_electricity_kwh_per_kg_water").value
    product_mass = protein.protein_run.output_masses_kg_per_kg_feed.get("dried_protein_product", 0.0) * config.basis_feed_kg_per_hr
    outputs = (
        CompleteProxyStream("dried_protein_product", product_mass, {"protein": protein.protein_run.protein_metrics_kg_per_kg_feed.get("dried_product_protein", 0.0) * config.basis_feed_kg_per_hr}, {}, "complete_proxy_dryer", "system_product", "dynamic_process_calculation"),
        CompleteProxyStream("evaporated_water", water, {"Water": water}, {}, "complete_proxy_dryer", "utility_or_condensation", "dynamic_process_calculation"),
    )
    input_mass = product_mass + water
    warning = ("Mass-only drying excludes energy; zero reported dryer demand is not a zero-energy claim."
               if method is DynamicDryingMethod.MASS_ONLY else "dryer energy is a legacy or engineering proxy; no TEA/LCA is activated")
    return _unit("complete_proxy_dryer", method.value, input_mass, 0.0, outputs, {"water_removed_kg_hr": water, "heat_demand_mj_hr": heat, "electricity_kwh_hr": electricity, "target_moisture_fraction": config.drying_target_moisture_fraction, "protein_preserved": True}, evidence, (warning,), blockers)


def _complete_ad(protein: object, config: DynamicCompleteProxyConfig, policy: DynamicCompleteProxyClosurePolicy) -> CompleteProxyUnitResult:
    stream = protein.protein_run.pathway_preview.biogas_mix_preparation.outputs[0]
    basis = config.basis_feed_kg_per_hr
    components = {name: mass * basis for name, mass in stream.component_masses_kg_per_kg_feed.items()}
    metadata = {name: mass * basis for name, mass in stream.metadata_pools_kg_per_kg_feed.items()}
    feed_mass = stream.kg_per_kg_feed * basis
    blockers: list[str] = []
    evidence = [
        policy.get("bmp_ch4"),
        policy.get("raw_biogas_ch4_fraction"),
        policy.get("ad_t80_days"),
        policy.get("ad_t90_days"),
        policy.get("ad_hrt_days"),
        policy.get("ad_heat_kwh_per_kg_feed"),
    ]
    vs = float(protein.protein_run.residual_metrics.get("estimated_residual_vs") or 0.0) * basis
    realization = policy.get("bmp_realization_fraction").value if policy.available("bmp_realization_fraction") else 1.0
    if policy.available("bmp_realization_fraction"):
        evidence.append(policy.get("bmp_realization_fraction"))
    methane_m3 = vs * policy.get("bmp_ch4").value * realization
    raw_m3 = methane_m3 / policy.get("raw_biogas_ch4_fraction").value
    co2_m3 = raw_m3 - methane_m3
    methane_kg = methane_m3 / STANDARD_MOLAR_VOLUME_M3_PER_KMOL * MW_CH4_KG_PER_KMOL
    co2_kg = co2_m3 / STANDARD_MOLAR_VOLUME_M3_PER_KMOL * MW_CO2_KG_PER_KMOL
    feed_bundle = protein.protein_run.pathway_preview.feedstock_bundle
    dry_fraction = next(item.value for item in feed_bundle.fields if item.canonical_field == "total_solids_wet_basis")
    n_db = next(item.value for item in feed_bundle.fields if item.canonical_field == "nitrogen_dry_basis")
    s_db = next(item.value for item in feed_bundle.fields if item.canonical_field == "sulfur_dry_basis")
    if policy.allow_assumptions:
        required = ("residual_n_routing_fraction", "residual_s_routing_fraction", "phosphorus_dry_basis", "potassium_dry_basis", "ad_nh3_n_loss_fraction", "ad_h2s_s_loss_fraction")
        evidence.extend(policy.get(name) for name in required)
        total_n = basis * dry_fraction * n_db * policy.get("residual_n_routing_fraction").value
        total_s = basis * dry_fraction * s_db * policy.get("residual_s_routing_fraction").value
        total_p = basis * dry_fraction * policy.get("phosphorus_dry_basis").value
        total_k = basis * dry_fraction * policy.get("potassium_dry_basis").value
        gas_n = total_n * policy.get("ad_nh3_n_loss_fraction").value
        gas_s = total_s * policy.get("ad_h2s_s_loss_fraction").value
        nh3_kg = gas_n * MW_NH3_KG_PER_KMOL / 14.0067
        h2s_kg = gas_s * MW_H2S_KG_PER_KMOL / 32.065
    else:
        total_n = total_s = total_p = total_k = gas_n = gas_s = nh3_kg = h2s_kg = 0.0
        blockers.extend(("residual_element_partition_missing", "digestate_N_P_K_S_speciation_missing", "trace_gas_conversion_missing"))
    gas_mass = methane_kg + co2_kg + nh3_kg + h2s_kg
    if gas_mass > feed_mass + MASS_TOLERANCE_KG_HR:
        blockers.append("BMP_gas_mass_exceeds_residual_feed_mass")
        gas_mass = feed_mass
    digestate_mass = max(feed_mass - gas_mass, 0.0)
    water = min(components.get("Water", 0.0), digestate_mass)
    dry = digestate_mass - water
    gas = CompleteProxyStream("raw_biogas", gas_mass, {"Methane": methane_kg, "CarbonDioxide": co2_kg, "Ammonia": nh3_kg, "HydrogenSulfide": h2s_kg}, {"normal_volume_m3_hr": raw_m3}, "dynamic_ad_proxy", "gas_conditioning_or_energy_route", "mixed_direct_proxy_and_assumption", ("no ADM1 or reactor kinetics executed",))
    digestate = CompleteProxyStream("digestate", digestate_mass, {"Water": water, "DryMatter": dry}, {"total_N": max(total_n - gas_n, 0.0), "total_P": total_p, "total_K": total_k, "total_S": max(total_s - gas_s, 0.0), "Ash": components.get("Ash", 0.0), "residual_VS": max(vs - gas_mass, 0.0)}, "dynamic_ad_proxy", "resource_recovery", "mixed_proxy_and_assumption", ("element pools are metadata and are not ionic species",))
    warnings = ("press cake excluded from AD", "BMP potential is converted to a mass-conserving proxy gas/digestate split", "AD kinetics, inhibition, and reactor design are not executed")
    return _unit("dynamic_ad_proxy", config.ad_method, feed_mass, 0.0, (gas, digestate), {"residual_feed_kg_hr": feed_mass, "estimated_vs_kg_hr": vs, "methane_m3_hr": methane_m3, "methane_kg_hr": methane_kg, "co2_m3_hr": co2_m3, "co2_kg_hr": co2_kg, "raw_biogas_m3_hr": raw_m3, "digestate_kg_hr": digestate_mass, "digestate_water_kg_hr": water, "digestate_dry_matter_kg_hr": dry, "t80_days": policy.get("ad_t80_days").value, "t90_days": policy.get("ad_t90_days").value, "hrt_days": policy.get("ad_hrt_days").value, "heat_demand_kwh_hr": feed_mass * policy.get("ad_heat_kwh_per_kg_feed").value, "kinetics_run": False, "press_cake_included": False}, evidence, warnings, blockers)


def _complete_gas_route(ad: CompleteProxyUnitResult, config: DynamicCompleteProxyConfig, policy: DynamicCompleteProxyClosurePolicy) -> CompleteProxyUnitResult:
    raw = _stream(ad, "raw_biogas")
    method = BiogasUpgradingMethod(config.upgrading_method)
    ch4 = raw.components_kg_hr.get("Methane", 0.0)
    co2 = raw.components_kg_hr.get("CarbonDioxide", 0.0)
    traces = {key: value for key, value in raw.components_kg_hr.items() if key not in {"Methane", "CarbonDioxide"}}
    raw_m3 = float(raw.metadata_kg_hr.get("normal_volume_m3_hr", 0.0))
    methane_m3 = ch4 / MW_CH4_KG_PER_KMOL * STANDARD_MOLAR_VOLUME_M3_PER_KMOL
    evidence: list[TraceableProxyValue] = []
    blockers: list[str] = []
    metrics: dict[str, float | str | bool | None] = {"raw_biogas_m3_hr": raw_m3, "electricity_kwh_hr": 0.0, "heat_demand_kwh_hr": 0.0}
    outputs: tuple[CompleteProxyStream, ...]
    if method is BiogasUpgradingMethod.NONE:
        outputs = (CompleteProxyStream("raw_biogas_product", raw.mass_kg_hr, dict(raw.components_kg_hr), dict(raw.metadata_kg_hr), "gas_route_none", "unconditioned_gas_output", "proxy_ad_output"),)
    elif method is BiogasUpgradingMethod.COMMON_CONDITIONING:
        retentions = _legacy_conditioning_retentions()
        for component, retention in sorted(retentions.items()):
            evidence.append(_value(
                f"conditioning_{component}_retention",
                retention,
                "fraction",
                f"GH-LEGACY-P6-COND-{component.upper()}",
                "greenhub_legacy_proxy_result",
                "C-class internal model proxy",
                "Greenhub/results/phase6_raw_biogas.csv|Greenhub/results/phase6_conditioned_biogas.csv",
                component,
                "legacy Phase 6 conditioning ratio is not measured GreenHub performance",
            ))
        conditioned_components = {name: mass * retentions.get(name, 1.0) for name, mass in raw.components_kg_hr.items()}
        removed = {name: mass - conditioned_components[name] for name, mass in raw.components_kg_hr.items()}
        outputs = (
            CompleteProxyStream("conditioned_biogas", sum(conditioned_components.values()), conditioned_components, {}, "common_conditioning", "upgrading_or_chp", "greenhub_legacy_proxy_result"),
            CompleteProxyStream("conditioning_residual", sum(removed.values()), removed, {}, "common_conditioning", "treatment_residual", "greenhub_legacy_proxy_result"),
        )
        if policy.available("common_conditioning_electricity"):
            item = policy.get("common_conditioning_electricity")
            evidence.append(item)
            metrics["electricity_kwh_hr"] = raw_m3 * item.value
        elif not policy.allow_assumptions:
            blockers.append("common_conditioning_energy_missing")
    elif method is BiogasUpgradingMethod.CHP_UTILITIES:
        evidence.extend((policy.get("chp_electrical_efficiency"), policy.get("chp_thermal_efficiency"), policy.get("methane_lhv_kwh_per_m3")))
        fuel = methane_m3 * policy.get("methane_lhv_kwh_per_m3").value
        metrics.update({"chp_electricity_output_kwh_hr": fuel * policy.get("chp_electrical_efficiency").value, "chp_heat_output_kwh_hr": fuel * policy.get("chp_thermal_efficiency").value, "methane_to_chp_m3_hr": methane_m3})
        outputs = (CompleteProxyStream("chp_flue_gas_proxy", raw.mass_kg_hr, {"CarbonDioxideEquivalent": raw.mass_kg_hr}, {"energy_input_kwh_hr": fuel}, "chp_energy_route", "energy_and_emissions_preview", "literature_proxy", ("combustion stoichiometry is not expanded",)),)
    else:
        integrated_policy = build_dynamic_biogas_upgrading_policy(method)
        evidence.extend(
            TraceableProxyValue(
                name=f"{method.value}_{item.record_id}",
                value=float(item.value),
                unit=item.unit,
                policy_id=integrated_policy.policy_id,
                source_status="direct_dataset",
                certainty_class=item.evidence_class,
                source_file=item.source_file,
                source_id=item.record_id or item.source_id,
                warning="technology proxy is not validated for GreenHub gas composition or scale",
            )
            for item in integrated_policy.evidence
            if item.value is not None
        )
        recovery = integrated_policy.methane_recovery_fraction
        purity = integrated_policy.product_methane_fraction
        if method is BiogasUpgradingMethod.MEA and recovery is None and policy.allow_assumptions:
            recovery = policy.get("mea_methane_recovery").value
            purity = policy.get("mea_product_methane_fraction").value
            evidence.extend((policy.get("mea_methane_recovery"), policy.get("mea_product_methane_fraction")))
        if recovery is None or purity is None:
            blockers.extend(("methane_recovery_missing", "product_methane_fraction_missing"))
            recovery = purity = 0.0
        recovered_ch4 = ch4 * recovery
        slip_ch4 = ch4 - recovered_ch4
        product_total = recovered_ch4 / max(purity, 1e-30)
        product_co2 = min(max(product_total - recovered_ch4, 0.0), co2)
        reject_components = {"Methane": slip_ch4, "CarbonDioxide": max(co2 - product_co2, 0.0), **traces}
        outputs = (
            CompleteProxyStream("biomethane_product", recovered_ch4 + product_co2, {"Methane": recovered_ch4, "CarbonDioxide": product_co2}, {}, f"{method.value}_upgrading", "biomethane_product", integrated_policy.evidence_class),
            CompleteProxyStream("reject_gas", sum(reject_components.values()), reject_components, {}, f"{method.value}_upgrading", "offgas_management", integrated_policy.evidence_class),
        )
        electric_specific = integrated_policy.specific_electricity_kwh_per_m3_raw_gas
        heat_specific = integrated_policy.specific_heat_kwh_per_m3_raw_gas
        if method is BiogasUpgradingMethod.MEA:
            electric_specific = policy.get("mea_electricity_kwh_per_m3").value
            heat_specific = policy.get("mea_heat_kwh_per_m3").value
            evidence.extend((policy.get("mea_electricity_kwh_per_m3"), policy.get("mea_heat_kwh_per_m3")))
        metrics.update({"biomethane_kg_hr": outputs[0].mass_kg_hr, "biomethane_methane_kg_hr": recovered_ch4, "methane_slip_kg_hr": slip_ch4, "biomethane_m3_hr": methane_m3 * recovery / max(purity, 1e-30), "electricity_kwh_hr": raw_m3 * float(electric_specific or 0.0), "heat_demand_kwh_hr": raw_m3 * float(heat_specific or 0.0)})
    warnings = (f"{method.value} is a mutually exclusive proxy gas route", "technology performance is not validated at GreenHub composition or scale")
    return _unit("dynamic_gas_route", method.value, raw.mass_kg_hr, 0.0, outputs, metrics, evidence, warnings, blockers)


def _complete_resource_recovery(ad: CompleteProxyUnitResult, config: DynamicCompleteProxyConfig, policy: DynamicCompleteProxyClosurePolicy) -> tuple[CompleteProxyUnitResult, ...]:
    selected = config.resource_recovery_methods
    digestate = _stream(ad, "digestate")
    state_mass = digestate.mass_kg_hr
    water = digestate.components_kg_hr.get("Water", 0.0)
    dry = digestate.components_kg_hr.get("DryMatter", 0.0)
    nutrients = {name: float(digestate.metadata_kg_hr.get(name, 0.0)) for name in ("total_N", "total_P", "total_K", "total_S")}
    results: list[CompleteProxyUnitResult] = []
    for method_name in selected:
        method = ResourceRecoveryMethod(method_name)
        input_mass = state_mass
        evidence: list[TraceableProxyValue] = []
        blockers: list[str] = []
        external = 0.0
        outputs: tuple[CompleteProxyStream, ...]
        metrics: dict[str, float | str | bool | None] = {"electricity_kwh_hr": 0.0, "heat_demand_kwh_hr": 0.0}
        if method is ResourceRecoveryMethod.DIGESTATE_SEPARATION:
            evidence.extend(policy.get(name) for name in ("digestate_ts_to_solids", "digestate_water_to_solids", "digestate_n_to_solids", "digestate_p_to_solids", "digestate_k_to_solids"))
            solid_dry = dry * policy.get("digestate_ts_to_solids").value
            solid_water = water * policy.get("digestate_water_to_solids").value
            solids_mass = solid_dry + solid_water
            solids_nutrients = {
                "total_N": nutrients["total_N"] * policy.get("digestate_n_to_solids").value,
                "total_P": nutrients["total_P"] * policy.get("digestate_p_to_solids").value,
                "total_K": nutrients["total_K"] * policy.get("digestate_k_to_solids").value,
                "total_S": nutrients["total_S"] * policy.get("digestate_ts_to_solids").value,
            }
            liquid_nutrients = {key: nutrients[key] - solids_nutrients[key] for key in nutrients}
            liquid_mass = state_mass - solids_mass
            outputs = (
                CompleteProxyStream("nutrient_rich_solids", solids_mass, {"Water": solid_water, "DryMatter": solid_dry}, solids_nutrients, "digestate_separation", "external_fertilizer_candidate", "direct_dataset_proxy"),
                CompleteProxyStream("digestate_liquid", liquid_mass, {"Water": water - solid_water, "DryMatter": dry - solid_dry}, liquid_nutrients, "digestate_separation", "sequential_resource_recovery", "direct_dataset_proxy"),
            )
            state_mass, water, dry, nutrients = liquid_mass, water - solid_water, dry - solid_dry, liquid_nutrients
        elif method is ResourceRecoveryMethod.AMMONIA_RECOVERY:
            if not policy.available("tan_fraction_total_n"):
                blockers.append("missing_TAN_speciation_without_assumptions")
                outputs = (_residual_stream("ammonia_recovery_blocked_liquor", state_mass, water, dry, nutrients, method.value),)
            else:
                evidence.extend(policy.get(name) for name in ("tan_fraction_total_n", "ammonia_recovery_fraction", "ammonium_salt_mass_per_kg_n"))
                tan_n = nutrients["total_N"] * policy.get("tan_fraction_total_n").value
                recovered_n = tan_n * policy.get("ammonia_recovery_fraction").value
                product_mass = recovered_n * policy.get("ammonium_salt_mass_per_kg_n").value
                external = max(product_mass - recovered_n, 0.0)
                state_mass -= recovered_n
                nutrients["total_N"] -= recovered_n
                outputs = (
                    CompleteProxyStream("ammonium_product", product_mass, {"RecoveredNitrogen": recovered_n, "CarrierAndWater": external}, {"recovered_N": recovered_n}, "ammonia_recovery", "fertilizer_candidate", "mixed_dataset_legacy_proxy"),
                    _residual_stream("ammonia_depleted_liquor", state_mass, water, max(dry - recovered_n, 0.0), nutrients, method.value),
                )
                dry = max(dry - recovered_n, 0.0)
                metrics.update({"recovered_n_kg_hr": recovered_n, "ammonium_product_kg_hr": product_mass})
        elif method is ResourceRecoveryMethod.PHOSPHORUS_RECOVERY:
            if not policy.available("po4_fraction_total_p"):
                blockers.append("missing_PO4_speciation_without_assumptions")
                outputs = (_residual_stream("phosphorus_recovery_blocked_liquor", state_mass, water, dry, nutrients, method.value),)
            else:
                evidence.extend(policy.get(name) for name in ("po4_fraction_total_p", "phosphate_recovery_fraction", "struvite_mass_per_kg_p"))
                po4_p = nutrients["total_P"] * policy.get("po4_fraction_total_p").value
                recovered_p = po4_p * policy.get("phosphate_recovery_fraction").value
                struvite = recovered_p * policy.get("struvite_mass_per_kg_p").value
                external = max(struvite - recovered_p, 0.0)
                state_mass -= recovered_p
                nutrients["total_P"] -= recovered_p
                outputs = (
                    CompleteProxyStream("struvite_product", struvite, {"StruviteEquivalent": struvite}, {"recovered_P": recovered_p}, "phosphorus_recovery", "fertilizer_candidate", "mixed_dataset_stoichiometric_proxy"),
                    _residual_stream("phosphorus_depleted_liquor", state_mass, water, max(dry - recovered_p, 0.0), nutrients, method.value),
                )
                dry = max(dry - recovered_p, 0.0)
                metrics.update({"recovered_p_kg_hr": recovered_p, "struvite_product_kg_hr": struvite})
        elif method is ResourceRecoveryMethod.POTASSIUM_WATER_CONCENTRATION:
            if not policy.available("k_ionic_fraction"):
                blockers.append("missing_K_speciation_without_assumptions")
                outputs = (_residual_stream("potassium_recovery_blocked_liquor", state_mass, water, dry, nutrients, method.value),)
            else:
                evidence.extend(policy.get(name) for name in ("k_ionic_fraction", "clean_water_recovery_fraction", "potassium_concentrate_k_fraction"))
                ionic_k = nutrients["total_K"] * policy.get("k_ionic_fraction").value
                recovered_water = water * policy.get("clean_water_recovery_fraction").value
                concentrate = ionic_k / policy.get("potassium_concentrate_k_fraction").value if ionic_k else 0.0
                carrier_water = max(concentrate - ionic_k, 0.0)
                available_water = max(water - recovered_water, 0.0)
                carrier_water = min(carrier_water, available_water)
                concentrate = ionic_k + carrier_water
                state_mass -= recovered_water + ionic_k + carrier_water
                water -= recovered_water + carrier_water
                dry = max(dry - ionic_k, 0.0)
                nutrients["total_K"] -= ionic_k
                outputs = (
                    CompleteProxyStream("potassium_concentrate", concentrate, {"Potassium": ionic_k, "Water": carrier_water}, {"recovered_K": ionic_k}, "potassium_water_concentration", "fertilizer_candidate", "mixed_dataset_assumption_proxy"),
                    CompleteProxyStream("recovered_water", recovered_water, {"Water": recovered_water}, {}, "potassium_water_concentration", "water_reuse_candidate", "direct_dataset_proxy", ("water quality is not regulatory-validated",)),
                    _residual_stream("concentration_residual_liquor", state_mass, water, dry, nutrients, method.value),
                )
                metrics.update({"recovered_k_kg_hr": ionic_k, "potassium_concentrate_kg_hr": concentrate, "recovered_water_kg_hr": recovered_water})
        else:
            if not policy.available("ion_exchange_remaining_tan_recovery") or not policy.available("tan_fraction_total_n"):
                blockers.append("ion_exchange_capacity_and_NH4_speciation_missing_without_assumptions")
                outputs = (_residual_stream("ion_exchange_blocked_liquor", state_mass, water, dry, nutrients, method.value),)
            else:
                evidence.extend((policy.get("ion_exchange_remaining_tan_recovery"), policy.get("tan_fraction_total_n")))
                captured_n = nutrients["total_N"] * policy.get("tan_fraction_total_n").value * policy.get("ion_exchange_remaining_tan_recovery").value
                state_mass -= captured_n
                dry = max(dry - captured_n, 0.0)
                nutrients["total_N"] -= captured_n
                outputs = (
                    CompleteProxyStream("ammonium_ion_exchange_product", captured_n, {"CapturedNitrogenEquivalent": captured_n}, {"recovered_N": captured_n}, "ion_exchange", "regeneration_or_fertilizer_candidate", "engineering_assumption", ("media and regenerant mass are not represented",)),
                    _residual_stream("final_residual_liquor", state_mass, water, dry, nutrients, method.value),
                )
                metrics.update({"captured_n_kg_hr": captured_n})
        results.append(_unit(f"dynamic_{method.value}", method.value, input_mass, external, outputs, metrics, evidence, ("resource product is a proxy candidate; quality and regulatory status are not validated",), blockers))
    return tuple(results)


def _protein_system_streams(protein: object, basis: float) -> dict[str, CompleteProxyStream]:
    run = protein.protein_run
    return {
        "press_cake": CompleteProxyStream("press_cake", run.output_masses_kg_per_kg_feed.get("press_cake", 0.0) * basis, {}, {}, "raw_press", "external_scope_output", "dynamic_process_calculation", ("excluded from in-project AD",)),
        "dried_protein_product": CompleteProxyStream("dried_protein_product", run.output_masses_kg_per_kg_feed.get("dried_protein_product", 0.0) * basis, {"SolubleProtein": run.protein_metrics_kg_per_kg_feed.get("dried_product_protein", 0.0) * basis}, {}, "protein_dryer", "system_product", "dynamic_process_calculation"),
    }


def _legacy_conditioning_retentions() -> dict[str, float]:
    raw = _component_flows(LEGACY_RESULTS / "phase6_raw_biogas.csv")
    conditioned = _component_flows(LEGACY_RESULTS / "phase6_conditioned_biogas.csv")
    return {name: conditioned.get(name, 0.0) / mass if mass else 0.0 for name, mass in raw.items()}


def _component_flows(path: Path) -> dict[str, float]:
    if not path.is_file():
        return {}
    with path.open(newline="", encoding="utf-8-sig") as file:
        return {row["component_id"]: float(row["flow_kg_hr"]) for row in csv.DictReader(file)}


def _residual_stream(stream_id: str, mass: float, water: float, dry: float, nutrients: Mapping[str, float], source: str) -> CompleteProxyStream:
    return CompleteProxyStream(stream_id, max(mass, 0.0), {"Water": max(water, 0.0), "DryMatter": max(dry, 0.0)}, dict(nutrients), source, "next_recovery_step_or_residual_output", "proxy_mass_ledger")


def _stream(unit: CompleteProxyUnitResult, stream_id: str) -> CompleteProxyStream:
    return next(item for item in unit.outputs if item.stream_id == stream_id)


def _unit(unit_id: str, method: str, input_mass: float, external: float, outputs: Iterable[CompleteProxyStream], metrics: dict[str, float | str | bool | None], evidence: Iterable[TraceableProxyValue], warnings: Iterable[str], blockers: Iterable[str]) -> CompleteProxyUnitResult:
    output_tuple = tuple(outputs)
    output_mass = sum(item.mass_kg_hr for item in output_tuple)
    residual = input_mass + external - output_mass
    return CompleteProxyUnitResult(unit_id, method, input_mass, external, output_mass, residual, output_tuple, metrics, tuple(evidence), tuple(item for item in warnings if item), tuple(dict.fromkeys(blockers)), abs(residual) <= MASS_TOLERANCE_KG_HR)


def _value(name: str, value: float, unit: str, policy_id: str, source_status: str, certainty: str, source_file: str, source_id: str, warning: str) -> TraceableProxyValue:
    return TraceableProxyValue(name, value, unit, policy_id, source_status, certainty, source_file, source_id, warning)


def _assumption(name: str, value: float, unit: str, policy_id: str, warning: str, *, source_status: str = "engineering_assumption", source_file: str = "") -> TraceableProxyValue:
    return TraceableProxyValue(name, value, unit, policy_id, source_status, "D-class proxy closure", source_file, policy_id, warning)


def _write_rows(path: Path, rows: list[dict[str, object]], fallback_fields: tuple[str, ...] = ()) -> None:
    fields = list(rows[0]) if rows else list(fallback_fields)
    with path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)
