"""Opt-in integrated proxy previews downstream of the dynamic protein pathway.

This module composes the isolated calculation-shadow protein system with
traceable drying-energy, BMP, gas-upgrading, and resource-recovery previews.
It never mutates or connects to the empirical BioSTEAM flowsheet.
"""

from __future__ import annotations

import csv
import json
import math
from collections import Counter
from dataclasses import asdict, dataclass, field
from enum import Enum
from pathlib import Path
from typing import Iterable

from Greenhub.dynamic_process import (
    DynamicProteinScenarioConfig,
    DynamicProteinScenarioRun,
    ProteinExtractionMethod,
    run_dynamic_protein_scenario_step,
)
from Greenhub.dynamic_unit_data import load_ad_bmp_evidence
from Greenhub.time_grid import generate_time_grid


DATA_ROOT = Path(__file__).resolve().parent / "data"
RESULTS_DIR = Path(__file__).resolve().parent / "results"


class DynamicDryingMethod(str, Enum):
    MASS_ONLY = "mass_only"
    SPRAY_DRYING_PROXY = "spray_drying_proxy"
    FREEZE_DRYING_PROXY = "freeze_drying_proxy"


class BiogasUpgradingMethod(str, Enum):
    NONE = "none"
    COMMON_CONDITIONING = "common_conditioning"
    MEMBRANE = "membrane"
    PSA = "psa"
    WATER_SCRUBBING = "water_scrubbing"
    MEA = "mea"
    CHP_UTILITIES = "chp_utilities"


class ResourceRecoveryMethod(str, Enum):
    AMMONIA_RECOVERY = "ammonia_recovery"
    PHOSPHORUS_RECOVERY = "phosphorus_recovery"
    POTASSIUM_WATER_CONCENTRATION = "potassium_water_concentration"
    DIGESTATE_SEPARATION = "digestate_separation"
    ION_EXCHANGE = "ion_exchange"


@dataclass(frozen=True)
class IntegratedEvidenceReference:
    record_id: str
    source_id: str
    source_title: str
    source_url: str
    source_file: str
    evidence_class: str
    original_material: str
    original_process_boundary: str
    basis: str
    value: float | None
    unit: str
    notes: str = ""

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True)
class DynamicIntegratedProxyConfig:
    scenario_id: str = "dynamic_integrated_proxy_baseline"
    start_date: str = "2026-05-01"
    end_date: str = "2026-11-30"
    time_step: str = "monthly"
    basis_feed_kg_per_hr: float = 1000.0
    protein_method: str = ProteinExtractionMethod.ISOELECTRIC.value
    drying_method: str = DynamicDryingMethod.MASS_ONLY.value
    drying_target_moisture_fraction: float = 0.15
    biogas_method: str = "bmp_potential_only"
    upgrading_method: str = BiogasUpgradingMethod.NONE.value
    fertilizer_methods: tuple[str, ...] = ()
    allow_proxy: bool = True
    allow_engineering_proxy_closure: bool = True
    allow_n_to_protein_proxy: bool = True
    generic_protein_recovery_fraction: float | None = None
    generic_protein_policy_id: str = ""
    generic_protein_provenance_note: str = ""
    include_press_cake_in_biogas: bool = False
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
        unknown = sorted(set(self.fertilizer_methods) - {item.value for item in ResourceRecoveryMethod})
        if unknown:
            raise ValueError(f"Unknown fertilizer methods: {', '.join(unknown)}.")
        if self.include_press_cake_in_biogas:
            raise ValueError("Press cake cannot enter the in-project biogas pathway.")
        if self.biogas_method != "bmp_potential_only":
            raise ValueError("biogas_method currently supports only 'bmp_potential_only'.")
        generate_time_grid(self.start_date, self.end_date, self.time_step)

    def protein_config(self) -> DynamicProteinScenarioConfig:
        return DynamicProteinScenarioConfig(
            scenario_id=self.scenario_id,
            start_date=self.start_date,
            end_date=self.end_date,
            time_step=self.time_step,
            protein_method=self.protein_method,
            drying_target_moisture_fraction=self.drying_target_moisture_fraction,
            allow_proxy=self.allow_proxy,
            allow_engineering_proxy_closure=self.allow_engineering_proxy_closure,
            allow_n_to_protein_proxy=self.allow_n_to_protein_proxy,
            generic_protein_recovery_fraction=self.generic_protein_recovery_fraction,
            generic_protein_policy_id=self.generic_protein_policy_id,
            generic_protein_provenance_note=self.generic_protein_provenance_note,
            include_press_cake_in_biogas=False,
            provenance={
                **self.provenance,
                "integrated_proxy_parent": self.scenario_id,
            },
        )

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True)
class DynamicDryingEnergyPayload:
    method: str
    target_moisture_fraction: float
    specific_heat_demand_mj_per_kg_water: float | None
    specific_electric_demand_kwh_per_kg_water: float | None
    evidence: tuple[IntegratedEvidenceReference, ...]
    evidence_class: str
    policy_id: str
    warnings: tuple[str, ...]
    blockers: tuple[str, ...]
    activation_status: str = "proxy_report_only"

    def to_dict(self) -> dict[str, object]:
        data = asdict(self)
        data["evidence"] = [item.to_dict() for item in self.evidence]
        return data


@dataclass(frozen=True)
class DynamicDryingEnergyPreview:
    payload: DynamicDryingEnergyPayload
    water_removed_kg_hr: float
    heat_demand_mj_hr: float | None
    electric_demand_kwh_hr: float | None
    protein_preserved: bool
    mass_preview_ready: bool
    energy_preview_ready: bool
    warnings: tuple[str, ...]
    blockers: tuple[str, ...]

    def to_dict(self) -> dict[str, object]:
        data = asdict(self)
        data["payload"] = self.payload.to_dict()
        return data


@dataclass(frozen=True)
class DynamicADPreviewPayload:
    policy_id: str
    bmp_m3_ch4_per_kg_vs: float | None
    methane_fraction: float | None
    t80_days: float | None
    t90_days: float | None
    vs_estimation_policy: str
    evidence: tuple[IntegratedEvidenceReference, ...]
    evidence_class: str
    warnings: tuple[str, ...]
    blockers: tuple[str, ...]
    activation_status: str = "bmp_potential_report_only"

    def to_dict(self) -> dict[str, object]:
        data = asdict(self)
        data["evidence"] = [item.to_dict() for item in self.evidence]
        return data


@dataclass(frozen=True)
class DynamicADPreviewResult:
    payload: DynamicADPreviewPayload
    residual_feed_kg_hr: float
    residual_vs_kg_hr: float | None
    bmp_eligible_vs_kg_hr: float | None
    methane_potential_m3_hr: float | None
    raw_biogas_potential_m3_hr: float | None
    carbon_dioxide_potential_m3_hr: float | None
    digestate_feed_placeholder_kg_hr: float
    press_cake_included: bool
    kinetics_run: bool
    potential_ready: bool
    warnings: tuple[str, ...]
    blockers: tuple[str, ...]

    def to_dict(self) -> dict[str, object]:
        data = asdict(self)
        data["payload"] = self.payload.to_dict()
        return data


@dataclass(frozen=True)
class DynamicBiogasUpgradingPolicy:
    method: str
    policy_id: str
    methane_recovery_fraction: float | None
    product_methane_fraction: float | None
    specific_electricity_kwh_per_m3_raw_gas: float | None
    specific_heat_kwh_per_m3_raw_gas: float | None
    evidence: tuple[IntegratedEvidenceReference, ...]
    evidence_class: str
    warnings: tuple[str, ...]
    blockers: tuple[str, ...]
    calculation_ready: bool
    activation_status: str = "proxy_report_only"

    def to_dict(self) -> dict[str, object]:
        data = asdict(self)
        data["evidence"] = [item.to_dict() for item in self.evidence]
        return data


@dataclass(frozen=True)
class DynamicBiogasUpgradingPreview:
    policy: DynamicBiogasUpgradingPolicy
    raw_biogas_m3_hr: float | None
    biomethane_product_m3_hr: float | None
    biomethane_methane_m3_hr: float | None
    reject_gas_m3_hr: float | None
    methane_slip_m3_hr: float | None
    electric_demand_kwh_hr: float | None
    heat_demand_kwh_hr: float | None
    calculation_ready: bool
    warnings: tuple[str, ...]
    blockers: tuple[str, ...]

    def to_dict(self) -> dict[str, object]:
        data = asdict(self)
        data["policy"] = self.policy.to_dict()
        return data


@dataclass(frozen=True)
class DynamicFertilizerRecoveryPreview:
    method: str
    selected: bool
    available_data_files: tuple[str, ...]
    product_candidates: dict[str, float | None]
    required_inputs: tuple[str, ...]
    evidence_class: str
    warnings: tuple[str, ...]
    blockers: tuple[str, ...]
    calculation_ready: bool = False
    activation_status: str = "resource_recovery_report_only"

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True)
class DynamicIntegratedProxyStepResult:
    scenario_id: str
    time_label: str
    config: DynamicIntegratedProxyConfig
    protein_run: DynamicProteinScenarioRun
    drying: DynamicDryingEnergyPreview
    ad: DynamicADPreviewResult
    upgrading: DynamicBiogasUpgradingPreview
    resource_recovery: tuple[DynamicFertilizerRecoveryPreview, ...]
    selected_alternatives: dict[str, object]
    inactive_alternatives: dict[str, tuple[str, ...]]
    product_outputs: dict[str, float | None]
    energy_summary: dict[str, float | None]
    warnings: tuple[str, ...]
    blockers: tuple[str, ...]
    provenance: dict[str, object]
    can_drive_proxy_preview: bool
    can_drive_calculation_shadow_system: bool
    can_drive_simulation: bool = False
    validated_simulation_ready: bool = False
    activation_status: str = "integrated_proxy_report_only"

    def to_dict(self, *, include_protein_run: bool = False) -> dict[str, object]:
        return {
            "scenario_id": self.scenario_id,
            "time_label": self.time_label,
            "config": self.config.to_dict(),
            "protein_run": self.protein_run.to_dict() if include_protein_run else {
                "selected_method": self.protein_run.selected_method,
                "policy_ids": dict(self.protein_run.policy_ids),
                "source_record_ids": list(self.protein_run.source_record_ids),
            },
            "drying": self.drying.to_dict(),
            "ad": self.ad.to_dict(),
            "upgrading": self.upgrading.to_dict(),
            "resource_recovery": [item.to_dict() for item in self.resource_recovery],
            "selected_alternatives": dict(self.selected_alternatives),
            "inactive_alternatives": {
                key: list(value) for key, value in self.inactive_alternatives.items()
            },
            "product_outputs": dict(self.product_outputs),
            "energy_summary": dict(self.energy_summary),
            "warnings": list(self.warnings),
            "blockers": list(self.blockers),
            "provenance": dict(self.provenance),
            "can_drive_proxy_preview": self.can_drive_proxy_preview,
            "can_drive_calculation_shadow_system": self.can_drive_calculation_shadow_system,
            "can_drive_simulation": self.can_drive_simulation,
            "validated_simulation_ready": self.validated_simulation_ready,
            "activation_status": self.activation_status,
        }


@dataclass(frozen=True)
class DynamicIntegratedProxyGridResult:
    config: DynamicIntegratedProxyConfig
    steps: tuple[DynamicIntegratedProxyStepResult, ...]
    time_labels: tuple[str, ...]
    all_steps_proxy_ready: bool
    all_steps_calculation_shadow_ready: bool
    blocker_counts: dict[str, int]
    warning_counts: dict[str, int]
    output_ranges: dict[str, dict[str, float]]
    activation_status: str = "integrated_proxy_grid_report_only"

    def to_dict(self) -> dict[str, object]:
        return {
            "config": self.config.to_dict(),
            "steps": [step.to_dict() for step in self.steps],
            "time_labels": list(self.time_labels),
            "all_steps_proxy_ready": self.all_steps_proxy_ready,
            "all_steps_calculation_shadow_ready": self.all_steps_calculation_shadow_ready,
            "blocker_counts": dict(self.blocker_counts),
            "warning_counts": dict(self.warning_counts),
            "output_ranges": {key: dict(value) for key, value in self.output_ranges.items()},
            "activation_status": self.activation_status,
        }


def build_dynamic_drying_energy_preview(
    run: DynamicProteinScenarioRun,
    config: DynamicIntegratedProxyConfig,
) -> DynamicDryingEnergyPreview:
    """Calculate dryer water removal and apply energy only when scalar evidence exists."""

    method = DynamicDryingMethod(config.drying_method)
    removed = run.output_masses_kg_per_kg_feed.get("evaporated_water", 0.0) * config.basis_feed_kg_per_hr
    evidence: tuple[IntegratedEvidenceReference, ...] = ()
    blockers: list[str] = []
    warnings: list[str] = []
    heat_specific = None
    electric_specific = None
    if method is DynamicDryingMethod.MASS_ONLY:
        blockers.append("drying_energy_missing")
        warnings.append("mass_only_drying_selected; target moisture is a scenario input")
        evidence_class = "scenario_input_baseline"
    else:
        folder = DATA_ROOT / "Protein recovery" / "Drying"
        filenames = (
            ("spray_drying_observations.csv", "spray_drying_parameters.csv")
            if method is DynamicDryingMethod.SPRAY_DRYING_PROXY
            else ("freeze_drying_observations.csv", "freeze_drying_parameters.csv")
        )
        scalar_energy = []
        for filename in filenames:
            for row in _read_rows(folder / filename):
                value = _number(row.get("energy_demand", ""))
                if value is not None:
                    scalar_energy.append(_evidence(row, folder / filename, "proxy_scenario_bound", value=value))
        evidence = tuple(scalar_energy)
        blockers.append("drying_energy_missing_source_scalar")
        warnings.append(f"{method.value} evidence contains operating envelopes but no transferable scalar energy demand")
        evidence_class = "blocked_missing"
    payload = DynamicDryingEnergyPayload(
        method=method.value,
        target_moisture_fraction=config.drying_target_moisture_fraction,
        specific_heat_demand_mj_per_kg_water=heat_specific,
        specific_electric_demand_kwh_per_kg_water=electric_specific,
        evidence=evidence,
        evidence_class=evidence_class,
        policy_id=f"dynamic_{method.value}_energy_preview_v1",
        warnings=tuple(warnings),
        blockers=tuple(blockers),
    )
    return DynamicDryingEnergyPreview(
        payload=payload,
        water_removed_kg_hr=removed,
        heat_demand_mj_hr=(removed * heat_specific if heat_specific is not None else None),
        electric_demand_kwh_hr=(removed * electric_specific if electric_specific is not None else None),
        protein_preserved=run.protein_metrics_kg_per_kg_feed.get("recovered_protein") == run.protein_metrics_kg_per_kg_feed.get("dried_product_protein"),
        mass_preview_ready=removed >= 0.0,
        energy_preview_ready=heat_specific is not None or electric_specific is not None,
        warnings=tuple(warnings),
        blockers=tuple(blockers),
    )


def summarize_dynamic_drying_alternatives() -> dict[str, dict[str, object]]:
    """Describe mutually exclusive dryer choices without inventing energy values."""

    return {
        DynamicDryingMethod.MASS_ONLY.value: {
            "mass_preview_ready": True,
            "energy_preview_ready": False,
            "evidence_class": "scenario_input_baseline",
            "available_data_files": [],
            "blockers": ["drying_energy_missing"],
        },
        DynamicDryingMethod.SPRAY_DRYING_PROXY.value: {
            "mass_preview_ready": True,
            "energy_preview_ready": False,
            "evidence_class": "operating_envelope_only",
            "available_data_files": [
                "spray_drying_observations.csv", "spray_drying_parameters.csv"
            ],
            "blockers": ["drying_energy_missing_source_scalar"],
        },
        DynamicDryingMethod.FREEZE_DRYING_PROXY.value: {
            "mass_preview_ready": True,
            "energy_preview_ready": False,
            "evidence_class": "operating_envelope_only",
            "available_data_files": [
                "freeze_drying_observations.csv", "freeze_drying_parameters.csv"
            ],
            "blockers": ["drying_energy_missing_source_scalar"],
        },
    }


def build_dynamic_ad_preview_payload() -> DynamicADPreviewPayload:
    evidence = load_ad_bmp_evidence()
    selected = tuple(
        row for row in (
            evidence.by_parameter_id("BMP_DFOS_VS"),
            evidence.by_parameter_id("BMP_DFOS_CH4FRAC"),
            evidence.by_parameter_id("BMP_DFOS_T80"),
            evidence.by_parameter_id("BMP_DFOS_T90"),
        ) if row is not None
    )
    by_id = {row.parameter_id: row for row in selected}
    references = tuple(
        IntegratedEvidenceReference(
            record_id=row.parameter_id,
            source_id=row.source_id,
            source_title=row.source_title,
            source_url=row.doi_or_url,
            source_file=row.source_file,
            evidence_class=row.evidence_class,
            original_material=row.original_material,
            original_process_boundary=row.original_process_boundary,
            basis=row.basis,
            value=row.normalized_value,
            unit=row.normalized_unit or row.unit,
            notes=row.notes,
        ) for row in selected
    )
    bmp = by_id.get("BMP_DFOS_VS")
    methane_fraction = by_id.get("BMP_DFOS_CH4FRAC")
    blockers = ["AD_conversion_kinetics_not_implemented", "digestate_conversion_yield_missing", "AD_heat_and_retention_time_not_selected"]
    if bmp is None or bmp.normalized_value is None:
        blockers.append("BMP_DFOS_VS_missing")
    return DynamicADPreviewPayload(
        policy_id="dfos_supernatant_bmp_potential_v1",
        bmp_m3_ch4_per_kg_vs=bmp.normalized_value if bmp else None,
        methane_fraction=methane_fraction.normalized_value if methane_fraction else None,
        t80_days=(by_id["BMP_DFOS_T80"].normalized_value / 86400.0 if by_id.get("BMP_DFOS_T80") and by_id["BMP_DFOS_T80"].normalized_value is not None else None),
        t90_days=(by_id["BMP_DFOS_T90"].normalized_value / 86400.0 if by_id.get("BMP_DFOS_T90") and by_id["BMP_DFOS_T90"].normalized_value is not None else None),
        vs_estimation_policy="proteins_sugars_fibers_fructan_plus_explicit_residual_dm_proxy",
        evidence=references,
        evidence_class="mixed_direct_residual_proxy_and_engineering_vs_classification",
        warnings=(
            "PROXY: de-FOS grass whey BMP applies to the supernatant-like residual, not separated cell debris",
            "BMP time markers are reported; no AD kinetic state equations are executed",
            "press cake excluded from the in-project AD boundary",
        ),
        blockers=tuple(blockers),
    )


def preview_dynamic_ad(
    run: DynamicProteinScenarioRun,
    config: DynamicIntegratedProxyConfig,
) -> DynamicADPreviewResult:
    payload = build_dynamic_ad_preview_payload()
    basis = config.basis_feed_kg_per_hr
    vs_per_feed = run.residual_metrics.get("estimated_residual_vs")
    vs = float(vs_per_feed) * basis if vs_per_feed is not None else None
    methane = (
        vs * payload.bmp_m3_ch4_per_kg_vs
        if vs is not None and payload.bmp_m3_ch4_per_kg_vs is not None
        else None
    )
    raw_gas = (
        methane / payload.methane_fraction
        if methane is not None and payload.methane_fraction not in (None, 0.0)
        else None
    )
    co2 = raw_gas - methane if raw_gas is not None and methane is not None else None
    residual_mass = run.output_masses_kg_per_kg_feed.get("biogas_feed_candidate", 0.0) * basis
    blockers = list(payload.blockers)
    if vs is None:
        blockers.append("residual_VS_unresolved")
    return DynamicADPreviewResult(
        payload=payload,
        residual_feed_kg_hr=residual_mass,
        residual_vs_kg_hr=vs,
        bmp_eligible_vs_kg_hr=vs,
        methane_potential_m3_hr=methane,
        raw_biogas_potential_m3_hr=raw_gas,
        carbon_dioxide_potential_m3_hr=co2,
        digestate_feed_placeholder_kg_hr=residual_mass,
        press_cake_included=False,
        kinetics_run=False,
        potential_ready=methane is not None,
        warnings=payload.warnings,
        blockers=tuple(dict.fromkeys(blockers)),
    )


def build_dynamic_biogas_upgrading_policy(
    method: str | BiogasUpgradingMethod,
) -> DynamicBiogasUpgradingPolicy:
    selected = method if isinstance(method, BiogasUpgradingMethod) else BiogasUpgradingMethod(method)
    if selected is BiogasUpgradingMethod.NONE:
        return DynamicBiogasUpgradingPolicy(
            method=selected.value,
            policy_id="no_upgrading_selected",
            methane_recovery_fraction=None,
            product_methane_fraction=None,
            specific_electricity_kwh_per_m3_raw_gas=None,
            specific_heat_kwh_per_m3_raw_gas=None,
            evidence=(), evidence_class="not_selected", warnings=(), blockers=(), calculation_ready=True,
        )
    specs = {
        BiogasUpgradingMethod.MEMBRANE: (
            "Membrane", "performance_observations.csv", "MEM_PERF_002", "performance_observations.csv", "MEM_PERF_001", "energy_demand.csv", "MEM_EN_001"
        ),
        BiogasUpgradingMethod.WATER_SCRUBBING: (
            "Water_Scrubbing", "methane_slip.csv", "WS_SLIP_001", "methane_and_co2_absorption.csv", "WS_ABS_003", "energy.csv", "WS_EN_003"
        ),
        BiogasUpgradingMethod.PSA: (
            "PSA", "performance_recovery_and_purge.csv", "PSA_PERF_002", "performance_recovery_and_purge.csv", "PSA_PERF_001", "vacuum_and_compression_energy.csv", "PSA_EN_001"
        ),
    }
    if selected in specs:
        folder_name, recovery_file, recovery_id, purity_file, purity_id, energy_file, energy_id = specs[selected]
        folder = DATA_ROOT / "Bigas production + upgrade" / folder_name
        recovery_row = _row_by_id(folder / recovery_file, recovery_id)
        purity_row = _row_by_id(folder / purity_file, purity_id)
        energy_row = _row_by_id(folder / energy_file, energy_id)
        recovery = _row_value(recovery_row)
        if selected is BiogasUpgradingMethod.WATER_SCRUBBING and recovery is not None:
            recovery = 1.0 - recovery
        purity = _row_value(purity_row)
        energy_j = _row_value(energy_row)
        energy = energy_j / 3_600_000.0 if energy_j is not None else None
        refs = tuple(
            _evidence(row, path, "source_backed_upgrading_proxy")
            for row, path in (
                (recovery_row, folder / recovery_file),
                (purity_row, folder / purity_file),
                (energy_row, folder / energy_file),
            ) if row
        )
        blockers = []
        if recovery is None: blockers.append("methane_recovery_missing")
        if purity is None: blockers.append("product_methane_fraction_missing")
        return DynamicBiogasUpgradingPolicy(
            method=selected.value,
            policy_id=f"{selected.value}_source_preview_v1",
            methane_recovery_fraction=recovery,
            product_methane_fraction=purity,
            specific_electricity_kwh_per_m3_raw_gas=energy,
            specific_heat_kwh_per_m3_raw_gas=None,
            evidence=refs,
            evidence_class="source_backed_technology_proxy",
            warnings=(
                "technology performance is not validated for GreenHub gas composition or scale",
                "selected scalar record is retained as a scenario point; source ranges are not averaged",
            ),
            blockers=tuple(blockers),
            calculation_ready=not blockers,
        )
    folder_map = {
        BiogasUpgradingMethod.MEA: "MEA",
        BiogasUpgradingMethod.COMMON_CONDITIONING: "Common_Conditioning",
        BiogasUpgradingMethod.CHP_UTILITIES: "CHP_and_Utilities",
    }
    blockers = {
        BiogasUpgradingMethod.MEA: ("MEA_methane_recovery_or_slip_missing",),
        BiogasUpgradingMethod.COMMON_CONDITIONING: ("conditioning_is_not_a_CO2_upgrading_route",),
        BiogasUpgradingMethod.CHP_UTILITIES: ("CHP_is_an_energy_route_not_biomethane_upgrading",),
    }[selected]
    return DynamicBiogasUpgradingPolicy(
        method=selected.value,
        policy_id=f"{selected.value}_blocked_preview_v1",
        methane_recovery_fraction=None,
        product_methane_fraction=None,
        specific_electricity_kwh_per_m3_raw_gas=None,
        specific_heat_kwh_per_m3_raw_gas=None,
        evidence=(),
        evidence_class="metadata_only",
        warnings=(f"dataset package available: {folder_map[selected]}",),
        blockers=blockers,
        calculation_ready=False,
    )


def preview_dynamic_biogas_upgrading(
    ad: DynamicADPreviewResult,
    method: str | BiogasUpgradingMethod,
) -> DynamicBiogasUpgradingPreview:
    policy = build_dynamic_biogas_upgrading_policy(method)
    if policy.method == BiogasUpgradingMethod.NONE.value:
        return DynamicBiogasUpgradingPreview(
            policy=policy,
            raw_biogas_m3_hr=ad.raw_biogas_potential_m3_hr,
            biomethane_product_m3_hr=None,
            biomethane_methane_m3_hr=None,
            reject_gas_m3_hr=None,
            methane_slip_m3_hr=None,
            electric_demand_kwh_hr=None,
            heat_demand_kwh_hr=None,
            calculation_ready=True,
            warnings=("upgrading_not_selected",), blockers=(),
        )
    blockers = list(policy.blockers)
    if ad.raw_biogas_potential_m3_hr is None or ad.methane_potential_m3_hr is None:
        blockers.append("raw_biogas_potential_unavailable")
    ready = policy.calculation_ready and not blockers
    recovered_methane = (
        ad.methane_potential_m3_hr * policy.methane_recovery_fraction
        if ready and policy.methane_recovery_fraction is not None and ad.methane_potential_m3_hr is not None
        else None
    )
    product = (
        recovered_methane / policy.product_methane_fraction
        if recovered_methane is not None and policy.product_methane_fraction
        else None
    )
    raw = ad.raw_biogas_potential_m3_hr
    return DynamicBiogasUpgradingPreview(
        policy=policy,
        raw_biogas_m3_hr=raw,
        biomethane_product_m3_hr=product,
        biomethane_methane_m3_hr=recovered_methane,
        reject_gas_m3_hr=(max(raw - product, 0.0) if raw is not None and product is not None else None),
        methane_slip_m3_hr=(ad.methane_potential_m3_hr - recovered_methane if recovered_methane is not None and ad.methane_potential_m3_hr is not None else None),
        electric_demand_kwh_hr=(raw * policy.specific_electricity_kwh_per_m3_raw_gas if raw is not None and policy.specific_electricity_kwh_per_m3_raw_gas is not None else None),
        heat_demand_kwh_hr=(raw * policy.specific_heat_kwh_per_m3_raw_gas if raw is not None and policy.specific_heat_kwh_per_m3_raw_gas is not None else None),
        calculation_ready=ready,
        warnings=policy.warnings,
        blockers=tuple(dict.fromkeys(blockers)),
    )


def summarize_biogas_upgrading_alternatives() -> dict[str, dict[str, object]]:
    return {
        method.value: build_dynamic_biogas_upgrading_policy(method).to_dict()
        for method in BiogasUpgradingMethod
    }


def summarize_resource_recovery_alternatives(
    selected_methods: Iterable[str] = (),
) -> tuple[DynamicFertilizerRecoveryPreview, ...]:
    selected = set(selected_methods)
    definitions = {
        ResourceRecoveryMethod.AMMONIA_RECOVERY: (
            "Ammonia_Recovery", ("ammonium_product",), ("TAN", "NH4", "pH", "alkalinity")
        ),
        ResourceRecoveryMethod.PHOSPHORUS_RECOVERY: (
            "Phosphorus_Recovery", ("struvite_product", "calcium_phosphate_product"), ("PO4", "Mg", "Ca", "pH", "alkalinity", "competing_ions")
        ),
        ResourceRecoveryMethod.POTASSIUM_WATER_CONCENTRATION: (
            "Potassium_and_Water_Concentration", ("potassium_concentrate", "recovered_water"), ("K_speciation", "ionic_strength", "scaling_ions")
        ),
        ResourceRecoveryMethod.DIGESTATE_SEPARATION: (
            "Digestate_and_Separation", ("digestate_liquid", "digestate_solids"), ("digestate_TS", "particle_distribution", "separation_efficiency")
        ),
        ResourceRecoveryMethod.ION_EXCHANGE: (
            "Ion_Exchange", ("ammonium_ion_exchange_product",), ("NH4", "competing_ions", "breakthrough_capacity", "regenerant")
        ),
    }
    previews = []
    for method, (folder, products, requirements) in definitions.items():
        path = DATA_ROOT / "Resource recovery" / folder
        files = tuple(sorted(item.name for item in path.glob("*.csv") if "cost" not in item.name))
        blockers = tuple(f"missing_{item}" for item in requirements)
        previews.append(DynamicFertilizerRecoveryPreview(
            method=method.value,
            selected=method.value in selected,
            available_data_files=files,
            product_candidates={name: None for name in products},
            required_inputs=requirements,
            evidence_class="dataset_available_input_speciation_blocked",
            warnings=("no elemental-to-ionic-species conversion is applied",),
            blockers=blockers,
            calculation_ready=False,
        ))
    return tuple(previews)


def summarize_protein_calculation_alternatives() -> dict[str, dict[str, object]]:
    return {
        ProteinExtractionMethod.ISOELECTRIC.value: {
            "calculation_ready": True, "policy_anchor": "REC-001", "evidence_class": "N-to-protein proxy",
        },
        ProteinExtractionMethod.LACTIC_ACID.value: {
            "calculation_ready": True, "policy_anchor": "PR-005", "evidence_class": "whole-plant scenario-bound proxy",
        },
        ProteinExtractionMethod.MEMBRANE.value: {
            "calculation_ready": True, "policy_anchor": "REJ-001", "evidence_class": "crude-protein rejection proxy",
        },
        ProteinExtractionMethod.HEAT.value: {
            "calculation_ready": False, "policy_anchor": None, "blockers": ["no_audited_heat_recovery_value"],
        },
        ProteinExtractionMethod.GENERIC.value: {
            "calculation_ready": False,
            "calculation_ready_with_explicit_policy": True,
            "policy_anchor": "caller policy ID and provenance note",
            "blockers": ["explicit_caller_recovery_policy_required"],
        },
    }


def run_dynamic_integrated_proxy_scenario_step(
    config: DynamicIntegratedProxyConfig,
    time_label: str,
) -> DynamicIntegratedProxyStepResult:
    """Run one isolated protein calculation system plus downstream previews."""

    protein_run = run_dynamic_protein_scenario_step(config.protein_config(), time_label)
    from Greenhub.dynamic_biosteam_adapter import (
        DynamicBioSTEAMAdapterConfig,
        build_dynamic_biosteam_calculation_shadow_system,
    )
    adapter_config = DynamicBioSTEAMAdapterConfig(
        scenario_id=config.scenario_id,
        time_label=time_label,
        basis_feed_kg_per_hr=config.basis_feed_kg_per_hr,
        scenario_config=config.protein_config(),
    )
    calculation = build_dynamic_biosteam_calculation_shadow_system(adapter_config)
    drying = build_dynamic_drying_energy_preview(protein_run, config)
    ad = preview_dynamic_ad(protein_run, config)
    upgrading = preview_dynamic_biogas_upgrading(ad, config.upgrading_method)
    resources = summarize_resource_recovery_alternatives(config.fertilizer_methods)
    selected_resources = tuple(item for item in resources if item.selected)
    warnings = tuple(dict.fromkeys((
        *protein_run.warnings, *drying.warnings, *ad.warnings, *upgrading.warnings,
        *(warning for item in selected_resources for warning in item.warnings),
    )))
    blockers = tuple(dict.fromkeys((
        *protein_run.blockers, *drying.blockers, *ad.blockers, *upgrading.blockers,
        *(blocker for item in selected_resources for blocker in item.blockers),
    )))
    basis = config.basis_feed_kg_per_hr
    products = {
        "press_cake_kg_hr": protein_run.output_masses_kg_per_kg_feed.get("press_cake", 0.0) * basis,
        "dried_protein_product_kg_hr": protein_run.output_masses_kg_per_kg_feed.get("dried_protein_product", 0.0) * basis,
        "dried_product_protein_kg_hr": protein_run.protein_metrics_kg_per_kg_feed.get("dried_product_protein", 0.0) * basis,
        "methane_potential_m3_hr": ad.methane_potential_m3_hr,
        "biomethane_product_m3_hr": upgrading.biomethane_product_m3_hr,
        **{
            f"{name}_kg_hr": value
            for item in selected_resources
            for name, value in item.product_candidates.items()
        },
    }
    can_proxy = protein_run.can_drive_proxy_preview and drying.mass_preview_ready and ad.potential_ready and (upgrading.calculation_ready or config.upgrading_method == "none")
    can_calculation = calculation.can_drive_calculation_shadow_system and can_proxy
    return DynamicIntegratedProxyStepResult(
        scenario_id=config.scenario_id,
        time_label=time_label,
        config=config,
        protein_run=protein_run,
        drying=drying,
        ad=ad,
        upgrading=upgrading,
        resource_recovery=resources,
        selected_alternatives={
            "protein_method": config.protein_method,
            "drying_method": config.drying_method,
            "biogas_method": config.biogas_method,
            "upgrading_method": config.upgrading_method,
            "fertilizer_methods": list(config.fertilizer_methods),
        },
        inactive_alternatives={
            "protein_methods": tuple(item.value for item in ProteinExtractionMethod if item.value != config.protein_method),
            "drying_methods": tuple(item.value for item in DynamicDryingMethod if item.value != config.drying_method),
            "upgrading_methods": tuple(item.value for item in BiogasUpgradingMethod if item.value != config.upgrading_method),
        },
        product_outputs=products,
        energy_summary={
            "drying_heat_mj_hr": drying.heat_demand_mj_hr,
            "drying_electricity_kwh_hr": drying.electric_demand_kwh_hr,
            "upgrading_electricity_kwh_hr": upgrading.electric_demand_kwh_hr,
            "upgrading_heat_kwh_hr": upgrading.heat_demand_kwh_hr,
        },
        warnings=warnings,
        blockers=blockers,
        provenance={
            "protein_policy_ids": dict(protein_run.policy_ids),
            "protein_source_record_ids": list(protein_run.source_record_ids),
            "drying_policy_id": drying.payload.policy_id,
            "ad_policy_id": ad.payload.policy_id,
            "upgrading_policy_id": upgrading.policy.policy_id,
            "press_cake_boundary": "external_system_output",
            "empirical_model_modified": False,
            "model_overrides": [],
        },
        can_drive_proxy_preview=can_proxy,
        can_drive_calculation_shadow_system=can_calculation,
    )


def run_dynamic_integrated_proxy_scenario_grid(
    config: DynamicIntegratedProxyConfig | None = None,
) -> DynamicIntegratedProxyGridResult:
    config = config or DynamicIntegratedProxyConfig()
    grid = generate_time_grid(config.start_date, config.end_date, config.time_step)
    steps = tuple(run_dynamic_integrated_proxy_scenario_step(config, item.label) for item in grid)
    blockers = Counter(item for step in steps for item in step.blockers)
    warnings = Counter(item for step in steps for item in step.warnings)
    keys = sorted({key for step in steps for key, value in step.product_outputs.items() if isinstance(value, (int, float))})
    ranges = {}
    for key in keys:
        values = [float(step.product_outputs[key]) for step in steps if step.product_outputs.get(key) is not None]
        if values:
            ranges[key] = {"min": min(values), "max": max(values)}
    return DynamicIntegratedProxyGridResult(
        config=config,
        steps=steps,
        time_labels=tuple(step.time_label for step in steps),
        all_steps_proxy_ready=all(step.can_drive_proxy_preview for step in steps),
        all_steps_calculation_shadow_ready=all(step.can_drive_calculation_shadow_system for step in steps),
        blocker_counts=dict(sorted(blockers.items())),
        warning_counts=dict(sorted(warnings.items())),
        output_ranges=ranges,
    )


def write_dynamic_integrated_proxy_reports(
    result: DynamicIntegratedProxyGridResult,
    output_dir: str | Path | None = None,
) -> dict[str, str]:
    target = Path(output_dir) if output_dir is not None else RESULTS_DIR
    target.mkdir(parents=True, exist_ok=True)
    paths = {
        "summary": target / "dynamic_integrated_proxy_summary.csv",
        "streams": target / "dynamic_integrated_proxy_streams.csv",
        "units": target / "dynamic_integrated_proxy_units.csv",
        "alternatives": target / "dynamic_integrated_proxy_alternatives.csv",
        "blockers": target / "dynamic_integrated_proxy_blockers.csv",
    }
    summary_rows = []
    stream_rows = []
    unit_rows = []
    alternative_rows = []
    blocker_rows = []
    for step in result.steps:
        common = {
            "scenario_id": step.scenario_id,
            "time_label": step.time_label,
            "protein_method": step.config.protein_method,
            "drying_method": step.config.drying_method,
            "biogas_method": step.config.biogas_method,
            "upgrading_method": step.config.upgrading_method,
            "fertilizer_methods": "|".join(step.config.fertilizer_methods),
        }
        summary_rows.append({
            **common, **step.product_outputs, **step.energy_summary,
            "can_drive_proxy_preview": step.can_drive_proxy_preview,
            "can_drive_calculation_shadow_system": step.can_drive_calculation_shadow_system,
            "can_drive_simulation": False,
        })
        for stream_id, mass in step.protein_run.output_masses_kg_per_kg_feed.items():
            stream_rows.append({**common, "stream_id": stream_id, "mass_kg_hr": mass * step.config.basis_feed_kg_per_hr, "evidence_class": "dynamic_protein_proxy_pathway"})
        stream_rows.extend((
            {**common, "stream_id": "raw_biogas_potential", "mass_kg_hr": "", "volume_m3_hr": step.ad.raw_biogas_potential_m3_hr, "evidence_class": step.ad.payload.evidence_class},
            {**common, "stream_id": "biomethane_product", "mass_kg_hr": "", "volume_m3_hr": step.upgrading.biomethane_product_m3_hr, "evidence_class": step.upgrading.policy.evidence_class},
        ))
        unit_rows.extend((
            {**common, "unit_id": "protein_calculation_shadow_system", "policy_id": step.protein_run.policy_ids.get("protein_extraction", ""), "status": step.can_drive_calculation_shadow_system},
            {**common, "unit_id": "drying_energy_preview", "policy_id": step.drying.payload.policy_id, "status": step.drying.energy_preview_ready},
            {**common, "unit_id": "ad_bmp_preview", "policy_id": step.ad.payload.policy_id, "status": step.ad.potential_ready},
            {**common, "unit_id": "biogas_upgrading_preview", "policy_id": step.upgrading.policy.policy_id, "status": step.upgrading.calculation_ready},
        ))
        for item in step.resource_recovery:
            alternative_rows.append({**common, "category": "resource_recovery", "method": item.method, "selected": item.selected, "calculation_ready": item.calculation_ready, "evidence_class": item.evidence_class, "blockers": "|".join(item.blockers)})
        for method, policy in summarize_biogas_upgrading_alternatives().items():
            alternative_rows.append({**common, "category": "biogas_upgrading", "method": method, "selected": method == step.config.upgrading_method, "calculation_ready": policy["calculation_ready"], "evidence_class": policy["evidence_class"], "blockers": "|".join(policy["blockers"])})
        blocker_rows.extend({**common, "blocker": blocker} for blocker in step.blockers)
    _write_rows(paths["summary"], summary_rows)
    _write_rows(paths["streams"], stream_rows)
    _write_rows(paths["units"], unit_rows)
    _write_rows(paths["alternatives"], alternative_rows)
    _write_rows(paths["blockers"], blocker_rows)
    return {key: str(path) for key, path in paths.items()}


def _read_rows(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8-sig", newline="") as file:
        return [
            {str(key): str(value or "").strip() for key, value in row.items() if key}
            for row in csv.DictReader(file)
        ]


def _row_by_id(path: Path, record_id: str) -> dict[str, str]:
    return next((row for row in _read_rows(path) if _record_id(row) == record_id), {})


def _record_id(row: dict[str, str]) -> str:
    return row.get("parameter_id") or row.get("record_id") or row.get("observation_id") or ""


def _row_value(row: dict[str, str]) -> float | None:
    return _number(row.get("normalized_si_value", "")) or _number(row.get("normalized_value", "")) or _number(row.get("value", ""))


def _number(value: str) -> float | None:
    text = str(value or "").strip().replace(",", ".")
    if not text or any(marker in text for marker in ("<", ">", "–", "—", " to ")):
        return None
    try:
        return float(text)
    except ValueError:
        return None


def _evidence(
    row: dict[str, str],
    path: Path,
    evidence_class: str,
    *,
    value: float | None = None,
) -> IntegratedEvidenceReference:
    return IntegratedEvidenceReference(
        record_id=_record_id(row),
        source_id=row.get("source_id", ""),
        source_title=row.get("source_title", ""),
        source_url=row.get("source_url", "") or row.get("doi_or_stable_identifier", "") or row.get("doi_or_stable_id", ""),
        source_file=path.resolve().relative_to(Path(__file__).resolve().parents[1]).as_posix(),
        evidence_class=evidence_class,
        original_material=row.get("material_feed_type", "") or row.get("material_or_feed", ""),
        original_process_boundary=row.get("process", ""),
        basis=row.get("basis", ""),
        value=value if value is not None else _row_value(row),
        unit=row.get("normalized_si_unit", "") or row.get("unit", ""),
        notes=row.get("notes", ""),
    )


def _write_rows(path: Path, rows: list[dict[str, object]]) -> None:
    fields = sorted({key for row in rows for key in row}) or ["status"]
    with path.open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow({key: _csv_value(row.get(key, "")) for key in fields})


def _csv_value(value: object) -> object:
    if isinstance(value, (dict, list, tuple)):
        return json.dumps(value, sort_keys=True)
    return value
