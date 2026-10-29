"""Isolated BioSTEAM shadow adapter for the dynamic protein pathway.

The records in this module are authoritative. BioSTEAM streams contain only
exact GreenHub chemicals; unresolved pools remain visible in parallel record
metadata. All named streams are created in a temporary flowsheet context so
the empirical flowsheet registry is restored before a result is returned.
"""

from __future__ import annotations

import csv
import json
import math
import re
import threading
from collections import Counter
from collections.abc import Mapping, Sequence
from dataclasses import asdict, dataclass, field, replace
from pathlib import Path
from typing import Any

import biosteam as bst

from Greenhub.dynamic_process import (
    DynamicPathwayPreview,
    DynamicProcessStream,
    DynamicProteinScenarioConfig,
    DynamicProteinScenarioGridResult,
    DynamicProteinScenarioRun,
    DynamicUnitResult,
    run_dynamic_protein_scenario_grid,
    run_dynamic_protein_scenario_step,
)
from Greenhub.time_grid import generate_time_grid

RESULTS_DIR = Path(__file__).resolve().parent / "results"
ADAPTER_MODE = "shadow_mass_only"
CALCULATION_ADAPTER_MODE = "calculation_shadow_system_report_only"
SUPPORTED_ADAPTER_MODES = frozenset((ADAPTER_MODE, CALCULATION_ADAPTER_MODE))
MASS_TOLERANCE_KG_HR = 1e-7
_FLOWSHEET_LOCK = threading.RLock()

EXACT_BIOSTEAM_COMPONENTS = (
    "Water",
    "Ash",
    "SolubleProtein",
    "SuspendedProtein",
    "Glucose",
    "Fructose",
    "Sucrose",
    "Cellulose",
    "Hemicellulose",
    "Lignin",
)

EXPECTED_DYNAMIC_STREAM_IDS = (
    "press_cake",
    "brown_juice",
    "clarified_juice",
    "cell_debris",
    "protein_rich_phase",
    "extraction_supernatant",
    "wet_protein_cake",
    "final_supernatant",
    "dried_protein_product",
    "evaporated_water",
    "biogas_feed_candidate",
    "raw_press_unrecovered_process_mass",
)

FINAL_OUTPUT_STREAM_IDS = (
    "press_cake",
    "dried_protein_product",
    "evaporated_water",
    "biogas_feed_candidate",
    "raw_press_unrecovered_process_mass",
)


@dataclass(frozen=True)
class DynamicBioSTEAMAdapterConfig:
    """Opt-in configuration for one isolated shadow conversion."""

    scenario_id: str = "proxy_protein_monthly_baseline"
    time_label: str = "2026-05"
    basis_feed_kg_per_hr: float = 1000.0
    pretreatment_water_addition_kg_per_kg_wet_feed: float = 0.0
    press_energy_kwh_per_t_wet_feed: float | None = None
    adapter_mode: str = ADAPTER_MODE
    include_press_cake_output: bool = True
    include_biogas_candidate_output: bool = True
    include_evaporated_water_output: bool = True
    selected_stream_ids: tuple[str, ...] | None = None
    allow_proxy_preview: bool = True
    create_biosteam_objects: bool = True
    connect_to_empirical_flowsheet: bool = False
    allow_out_of_grid_time_label: bool = False
    scenario_config: DynamicProteinScenarioConfig | None = field(
        default=None, repr=False, compare=False
    )
    provenance: dict[str, object] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not math.isfinite(float(self.basis_feed_kg_per_hr)) or self.basis_feed_kg_per_hr <= 0:
            raise ValueError("basis_feed_kg_per_hr must be a finite value greater than zero.")
        if (not math.isfinite(float(self.pretreatment_water_addition_kg_per_kg_wet_feed))
                or self.pretreatment_water_addition_kg_per_kg_wet_feed < 0):
            raise ValueError("pretreatment_water_addition_kg_per_kg_wet_feed must be finite and non-negative.")
        if self.press_energy_kwh_per_t_wet_feed is not None and (
                not math.isfinite(float(self.press_energy_kwh_per_t_wet_feed))
                or self.press_energy_kwh_per_t_wet_feed < 0):
            raise ValueError("press_energy_kwh_per_t_wet_feed must be finite and non-negative.")
        if self.adapter_mode not in SUPPORTED_ADAPTER_MODES:
            supported = ", ".join(sorted(SUPPORTED_ADAPTER_MODES))
            raise ValueError(f"adapter_mode must be one of: {supported}.")
        if self.connect_to_empirical_flowsheet:
            raise ValueError("The dynamic adapter cannot connect to the empirical flowsheet.")
        if not self.time_label:
            raise ValueError("time_label must be provided.")
        if self.selected_stream_ids is not None:
            unknown = sorted(set(self.selected_stream_ids) - set(EXPECTED_DYNAMIC_STREAM_IDS))
            if unknown:
                raise ValueError(f"Unknown selected dynamic stream IDs: {', '.join(unknown)}.")
        scenario = self.resolved_scenario_config()
        labels = {step.label for step in generate_time_grid(
            scenario.start_date, scenario.end_date, scenario.time_step
        )}
        if self.time_label not in labels and not self.allow_out_of_grid_time_label:
            raise ValueError(
                f"time_label '{self.time_label}' is not in the configured dynamic scenario grid."
            )

    def resolved_scenario_config(self) -> DynamicProteinScenarioConfig:
        scenario = self.scenario_config
        if scenario is None:
            return DynamicProteinScenarioConfig(
                scenario_id=self.scenario_id,
                pretreatment_water_addition_kg_per_kg_wet_feed=self.pretreatment_water_addition_kg_per_kg_wet_feed,
                press_energy_kwh_per_t_wet_feed=self.press_energy_kwh_per_t_wet_feed,
            )
        if scenario.scenario_id != self.scenario_id:
            raise ValueError("scenario_id must match scenario_config.scenario_id.")
        if (
            self.pretreatment_water_addition_kg_per_kg_wet_feed
            and abs(
                scenario.pretreatment_water_addition_kg_per_kg_wet_feed
                - self.pretreatment_water_addition_kg_per_kg_wet_feed
            ) > 1e-12
        ):
            raise ValueError(
                "Adapter pretreatment water and scenario pretreatment water must agree."
            )
        if (
            self.press_energy_kwh_per_t_wet_feed is not None
            and scenario.press_energy_kwh_per_t_wet_feed is not None
            and abs(scenario.press_energy_kwh_per_t_wet_feed - self.press_energy_kwh_per_t_wet_feed) > 1e-12
        ):
            raise ValueError("Adapter press energy and scenario press energy must agree.")
        if (
            self.press_energy_kwh_per_t_wet_feed is not None
            and scenario.press_energy_kwh_per_t_wet_feed is None
        ):
            return replace(
                scenario,
                press_energy_kwh_per_t_wet_feed=self.press_energy_kwh_per_t_wet_feed,
            )
        return scenario

    def to_dict(self) -> dict[str, object]:
        result = asdict(self)
        scenario = self.scenario_config
        result["scenario_config"] = scenario.to_dict() if scenario else None
        return result


@dataclass(frozen=True)
class DynamicBioSTEAMStreamRecord:
    """Scaled stream inventory retained independently of BioSTEAM objects."""

    scenario_id: str
    time_label: str
    adapter_stream_id: str
    source_dynamic_stream_id: str
    source_unit_id: str
    destination_hint: str
    basis_feed_kg_per_hr: float
    source_kg_per_kg_feed: float
    stream_mass_kg_hr: float
    component_masses_kg_hr: dict[str, float]
    metadata_pools_kg_hr: dict[str, float]
    total_component_kg_hr: float
    total_metadata_kg_hr: float
    unassigned_mass_kg_hr: float
    policy_ids: tuple[str, ...]
    policy_status: str
    evidence_classes: tuple[str, ...]
    source_ids: tuple[str, ...]
    record_ids: tuple[str, ...]
    warnings: tuple[str, ...]
    blockers: tuple[str, ...]
    provenance: dict[str, object]
    created_biosteam_stream_id: str | None = None

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True)
class DynamicBioSTEAMMassBalance:
    """Validation result for one independent shadow adapter step."""

    basis_feed_kg_hr: float
    final_output_mass_kg_hr: float
    overall_residual_kg_hr: float
    overall_closes: bool
    component_residuals_kg_hr: dict[str, float]
    metadata_residuals_kg_hr: dict[str, float]
    identity_closes: bool
    per_stream_component_residuals_kg_hr: dict[str, float]
    per_stream_component_masses_match: bool
    metadata_preserved_in_records: bool
    source_stream_masses_match: bool
    press_cake_boundary_valid: bool
    dried_protein_matches_source: bool
    evaporated_water_matches_source: bool
    empirical_flowsheet_unchanged: bool
    closes: bool
    warnings: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True)
class DynamicBioSTEAMUnitSpec:
    """Typed handoff only; no real BioSTEAM unit is implemented here."""

    dynamic_unit_id: str
    future_biosteam_unit_id: str
    expected_input_stream_ids: tuple[str, ...]
    expected_output_stream_ids: tuple[str, ...]
    implementation_status: str = "future_unit_not_implemented"

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True)
class DynamicBioSTEAMAdapterResult:
    """One time-step shadow conversion and its isolated BioSTEAM objects."""

    config: DynamicBioSTEAMAdapterConfig
    source_run: DynamicProteinScenarioRun
    records: tuple[DynamicBioSTEAMStreamRecord, ...]
    biosteam_streams: dict[str, Any]
    isolated_flowsheet: Any | None
    mass_balance: DynamicBioSTEAMMassBalance
    future_unit_specs: tuple[DynamicBioSTEAMUnitSpec, ...]
    warnings: tuple[str, ...]
    blockers: tuple[str, ...]
    provenance: dict[str, object]
    can_drive_shadow_adapter: bool
    can_drive_simulation: bool = False
    validated_simulation_ready: bool = False
    activation_status: str = "shadow_mass_only_report_only"

    def to_dict(self) -> dict[str, object]:
        return {
            "config": self.config.to_dict(),
            "source_run": self.source_run.to_dict(),
            "records": [record.to_dict() for record in self.records],
            "created_biosteam_stream_ids": sorted(self.biosteam_streams),
            "isolated_flowsheet_id": getattr(self.isolated_flowsheet, "ID", None),
            "mass_balance": self.mass_balance.to_dict(),
            "future_unit_specs": [spec.to_dict() for spec in self.future_unit_specs],
            "warnings": list(self.warnings),
            "blockers": list(self.blockers),
            "provenance": dict(self.provenance),
            "can_drive_shadow_adapter": self.can_drive_shadow_adapter,
            "can_drive_simulation": self.can_drive_simulation,
            "validated_simulation_ready": self.validated_simulation_ready,
            "activation_status": self.activation_status,
        }


@dataclass(frozen=True)
class DynamicBioSTEAMAdapterGridResult:
    """Independent monthly shadow adapters with no scheduling semantics."""

    config: DynamicBioSTEAMAdapterConfig
    source_grid: DynamicProteinScenarioGridResult
    step_results: tuple[DynamicBioSTEAMAdapterResult, ...]
    time_labels: tuple[str, ...]
    all_steps_close: bool
    all_empirical_flowsheets_unchanged: bool
    warning_counts: dict[str, int]
    blocker_counts: dict[str, int]
    provenance: dict[str, object]
    activation_status: str = "shadow_mass_only_grid_report_only"

    def to_dict(self) -> dict[str, object]:
        return {
            "config": self.config.to_dict(),
            "source_grid": self.source_grid.to_dict(),
            "step_results": [result.to_dict() for result in self.step_results],
            "time_labels": list(self.time_labels),
            "all_steps_close": self.all_steps_close,
            "all_empirical_flowsheets_unchanged": self.all_empirical_flowsheets_unchanged,
            "warning_counts": dict(self.warning_counts),
            "blocker_counts": dict(self.blocker_counts),
            "provenance": dict(self.provenance),
            "activation_status": self.activation_status,
        }


@dataclass(frozen=True)
class DynamicBioSTEAMShadowUnitBalance:
    """Exact-component balance and target parity for one shadow unit."""

    unit_id: str
    unit_type: str
    input_mass_kg_hr: float
    output_mass_kg_hr: float
    residual_kg_hr: float
    component_residuals_kg_hr: dict[str, float]
    identity_closes: bool
    outputs_match_adapter_records: bool
    closes: bool

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True)
class DynamicBioSTEAMShadowSystemBalance:
    """System-level exact-component and adapter-inclusive validation."""

    input_component_mass_kg_hr: float
    terminal_component_mass_kg_hr: float
    exact_component_residual_kg_hr: float
    component_residuals_kg_hr: dict[str, float]
    exact_component_identity_closes: bool
    adapter_full_mass_closes: bool
    adapter_metadata_identity_closes: bool
    all_unit_outputs_match_adapter_records: bool
    unit_balances: tuple[DynamicBioSTEAMShadowUnitBalance, ...]
    press_cake_boundary_valid: bool
    empirical_flowsheet_unchanged: bool
    closes: bool
    warnings: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, object]:
        result = asdict(self)
        result["unit_balances"] = [balance.to_dict() for balance in self.unit_balances]
        return result


@dataclass(frozen=True)
class DynamicBioSTEAMShadowSystemResult:
    """One isolated real-BioSTEAM-unit shadow system."""

    config: DynamicBioSTEAMAdapterConfig
    source_adapter: DynamicBioSTEAMAdapterResult
    feed_record: DynamicBioSTEAMStreamRecord
    adapter_records: tuple[DynamicBioSTEAMStreamRecord, ...]
    system: Any
    units: dict[str, Any]
    streams: dict[str, Any]
    isolated_flowsheet: Any
    mass_balance: DynamicBioSTEAMShadowSystemBalance
    warnings: tuple[str, ...]
    blockers: tuple[str, ...]
    provenance: dict[str, object]
    can_drive_shadow_system: bool
    can_drive_simulation: bool = False
    validated_simulation_ready: bool = False
    activation_status: str = "target_output_shadow_system_report_only"

    def to_dict(self) -> dict[str, object]:
        return {
            "config": self.config.to_dict(),
            "source_adapter": self.source_adapter.to_dict(),
            "feed_record": self.feed_record.to_dict(),
            "adapter_records": [record.to_dict() for record in self.adapter_records],
            "system_id": self.system.ID,
            "unit_ids": {name: unit.ID for name, unit in self.units.items()},
            "stream_ids": {name: stream.ID for name, stream in self.streams.items()},
            "isolated_flowsheet_id": self.isolated_flowsheet.ID,
            "mass_balance": self.mass_balance.to_dict(),
            "warnings": list(self.warnings),
            "blockers": list(self.blockers),
            "provenance": dict(self.provenance),
            "can_drive_shadow_system": self.can_drive_shadow_system,
            "can_drive_simulation": self.can_drive_simulation,
            "validated_simulation_ready": self.validated_simulation_ready,
            "activation_status": self.activation_status,
        }


@dataclass(frozen=True)
class DynamicBioSTEAMShadowSystemGridResult:
    """Seven independent monthly shadow systems with no time integration."""

    config: DynamicBioSTEAMAdapterConfig
    step_results: tuple[DynamicBioSTEAMShadowSystemResult, ...]
    time_labels: tuple[str, ...]
    all_steps_close: bool
    all_steps_shadow_ready: bool
    all_empirical_flowsheets_unchanged: bool
    warning_counts: dict[str, int]
    blocker_counts: dict[str, int]
    provenance: dict[str, object]
    activation_status: str = "target_output_shadow_system_grid_report_only"

    def to_dict(self) -> dict[str, object]:
        return {
            "config": self.config.to_dict(),
            "step_results": [result.to_dict() for result in self.step_results],
            "time_labels": list(self.time_labels),
            "all_steps_close": self.all_steps_close,
            "all_steps_shadow_ready": self.all_steps_shadow_ready,
            "all_empirical_flowsheets_unchanged": self.all_empirical_flowsheets_unchanged,
            "warning_counts": dict(self.warning_counts),
            "blocker_counts": dict(self.blocker_counts),
            "provenance": dict(self.provenance),
            "activation_status": self.activation_status,
        }


@dataclass(frozen=True)
class DynamicBioSTEAMCalculationUnitParity:
    unit_key: str
    unit_id: str
    unit_type: str
    input_mass_kg_hr: float
    output_mass_kg_hr: float
    residual_kg_hr: float
    parity_residual_kg_hr: float
    identity_closes: bool
    target_parity_passed: bool
    policy_id: str
    evidence_classes: tuple[str, ...]
    warnings: tuple[str, ...]
    blockers: tuple[str, ...]

    def to_dict(self) -> dict[str, object]: return asdict(self)


@dataclass(frozen=True)
class DynamicBioSTEAMCalculationValidation:
    unit_parities: tuple[DynamicBioSTEAMCalculationUnitParity, ...]
    all_unit_parity_passed: bool
    exact_component_identity_closes: bool
    adapter_full_mass_closes: bool
    metadata_records_preserved: bool
    press_cake_boundary_valid: bool
    empirical_flowsheet_unchanged: bool
    selected_method: str
    selected_method_calculation_ready: bool
    closes: bool
    warnings: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, object]:
        result = asdict(self)
        result["unit_parities"] = [item.to_dict() for item in self.unit_parities]
        return result


@dataclass(frozen=True)
class DynamicBioSTEAMCalculationSystemResult:
    config: DynamicBioSTEAMAdapterConfig
    source_adapter: DynamicBioSTEAMAdapterResult
    feed_record: DynamicBioSTEAMStreamRecord
    adapter_records: tuple[DynamicBioSTEAMStreamRecord, ...]
    payloads: Any
    system: Any | None
    units: dict[str, Any]
    streams: dict[str, Any]
    isolated_flowsheet: Any | None
    validation: DynamicBioSTEAMCalculationValidation
    warnings: tuple[str, ...]
    blockers: tuple[str, ...]
    provenance: dict[str, object]
    can_drive_calculation_shadow_system: bool
    can_drive_simulation: bool = False
    validated_simulation_ready: bool = False
    activation_status: str = "calculation_shadow_system_report_only"

    def to_dict(self) -> dict[str, object]:
        return {
            "config": self.config.to_dict(),
            "source_adapter": self.source_adapter.to_dict(),
            "feed_record": self.feed_record.to_dict(),
            "adapter_records": [record.to_dict() for record in self.adapter_records],
            "payloads": self.payloads.to_dict(),
            "system_id": self.system.ID if self.system is not None else None,
            "unit_ids": {name: unit.ID for name, unit in self.units.items()},
            "stream_ids": {name: stream.ID for name, stream in self.streams.items()},
            "isolated_flowsheet_id": (
                self.isolated_flowsheet.ID if self.isolated_flowsheet is not None else None
            ),
            "validation": self.validation.to_dict(),
            "warnings": list(self.warnings),
            "blockers": list(self.blockers),
            "provenance": dict(self.provenance),
            "can_drive_calculation_shadow_system": self.can_drive_calculation_shadow_system,
            "pretreatment_utilities": summarize_pretreatment_utilities(self),
            "can_drive_simulation": self.can_drive_simulation,
            "validated_simulation_ready": self.validated_simulation_ready,
            "activation_status": self.activation_status,
        }


@dataclass(frozen=True)
class DynamicBioSTEAMCalculationGridResult:
    config: DynamicBioSTEAMAdapterConfig
    step_results: tuple[DynamicBioSTEAMCalculationSystemResult, ...]
    time_labels: tuple[str, ...]
    all_steps_parity_passed: bool
    all_steps_calculation_shadow_ready: bool
    all_empirical_flowsheets_unchanged: bool
    warning_counts: dict[str, int]
    blocker_counts: dict[str, int]
    provenance: dict[str, object]
    activation_status: str = "calculation_shadow_system_grid_report_only"

    def to_dict(self) -> dict[str, object]:
        return {
            "config": self.config.to_dict(),
            "step_results": [result.to_dict() for result in self.step_results],
            "time_labels": list(self.time_labels),
            "all_steps_parity_passed": self.all_steps_parity_passed,
            "all_steps_calculation_shadow_ready": self.all_steps_calculation_shadow_ready,
            "all_empirical_flowsheets_unchanged": self.all_empirical_flowsheets_unchanged,
            "warning_counts": dict(self.warning_counts),
            "blocker_counts": dict(self.blocker_counts),
            "provenance": dict(self.provenance),
            "activation_status": self.activation_status,
        }


def dynamic_biosteam_unit_specs() -> tuple[DynamicBioSTEAMUnitSpec, ...]:
    """Return the reviewed mapping for the next real-unit implementation stage."""

    return (
        DynamicBioSTEAMUnitSpec("dynamic_raw_press", "DPR101", ("whole_feed",), ("press_cake", "brown_juice", "raw_press_unrecovered_process_mass")),
        DynamicBioSTEAMUnitSpec("first_centrifugation", "DCF101", ("brown_juice",), ("clarified_juice", "cell_debris")),
        DynamicBioSTEAMUnitSpec("protein_extraction", "DPE201", ("clarified_juice",), ("protein_rich_phase", "extraction_supernatant")),
        DynamicBioSTEAMUnitSpec("second_centrifugation", "DCF202", ("protein_rich_phase", "extraction_supernatant"), ("wet_protein_cake", "final_supernatant")),
        DynamicBioSTEAMUnitSpec("protein_drying", "DDR301", ("wet_protein_cake",), ("dried_protein_product", "evaporated_water")),
        DynamicBioSTEAMUnitSpec("biogas_residual_mixer", "DMX401", ("cell_debris", "final_supernatant"), ("biogas_feed_candidate",)),
    )


def dynamic_process_stream_to_adapter_record(
    stream: DynamicProcessStream,
    basis_feed_kg_per_hr: float,
    *,
    scenario_id: str = "dynamic_protein_shadow",
    unit: DynamicUnitResult | None = None,
) -> DynamicBioSTEAMStreamRecord:
    """Scale one normalized dynamic stream without changing its identities."""

    basis = float(basis_feed_kg_per_hr)
    if not math.isfinite(basis) or basis <= 0:
        raise ValueError("basis_feed_kg_per_hr must be a finite value greater than zero.")
    component_masses = {
        name: float(mass) * basis
        for name, mass in stream.component_masses_kg_per_kg_feed.items()
    }
    metadata_masses = {
        name: float(mass) * basis
        for name, mass in stream.metadata_pools_kg_per_kg_feed.items()
    }
    stream_mass = float(stream.kg_per_kg_feed) * basis
    component_total = sum(component_masses.values())
    metadata_total = sum(metadata_masses.values())
    trace = _trace_unit(unit)
    adapter_id = _adapter_stream_id(stream.time_label, stream.stream_id)
    return DynamicBioSTEAMStreamRecord(
        scenario_id=scenario_id,
        time_label=stream.time_label,
        adapter_stream_id=adapter_id,
        source_dynamic_stream_id=stream.stream_id,
        source_unit_id=unit.unit_id if unit else stream.source_unit,
        destination_hint=stream.destination_hint,
        basis_feed_kg_per_hr=basis,
        source_kg_per_kg_feed=float(stream.kg_per_kg_feed),
        stream_mass_kg_hr=stream_mass,
        component_masses_kg_hr=component_masses,
        metadata_pools_kg_hr=metadata_masses,
        total_component_kg_hr=component_total,
        total_metadata_kg_hr=metadata_total,
        unassigned_mass_kg_hr=stream_mass - component_total - metadata_total,
        policy_ids=trace["policy_ids"],
        policy_status=trace["policy_status"],
        evidence_classes=trace["evidence_classes"],
        source_ids=trace["source_ids"],
        record_ids=trace["record_ids"],
        warnings=tuple(dict.fromkeys((*stream.warnings, *(unit.warnings if unit else ())))),
        blockers=unit.blockers if unit else (),
        provenance={
            "source_stream": stream.to_dict(),
            "source_unit_policy": dict(unit.applied_policy) if unit else {},
            "adapter_rule": "exact_components_to_biosteam_metadata_pools_parallel",
            "model_overrides": [],
        },
    )


def dynamic_pathway_to_adapter_records(
    preview: DynamicPathwayPreview,
    config: DynamicBioSTEAMAdapterConfig,
) -> tuple[DynamicBioSTEAMStreamRecord, ...]:
    """Convert every unique pathway output to a scaled, traceable record."""

    records: list[DynamicBioSTEAMStreamRecord] = []
    selected = set(config.selected_stream_ids or EXPECTED_DYNAMIC_STREAM_IDS)
    if not config.include_press_cake_output:
        selected.discard("press_cake")
    if not config.include_biogas_candidate_output:
        selected.discard("biogas_feed_candidate")
    if not config.include_evaporated_water_output:
        selected.discard("evaporated_water")
    seen: set[str] = set()
    for unit in _pathway_units(preview):
        for stream in unit.outputs:
            if stream.stream_id not in selected or stream.stream_id in seen:
                continue
            records.append(dynamic_process_stream_to_adapter_record(
                stream,
                config.basis_feed_kg_per_hr,
                scenario_id=config.scenario_id,
                unit=unit,
            ))
            seen.add(stream.stream_id)
    return tuple(records)


def adapter_record_to_biosteam_stream(
    record: DynamicBioSTEAMStreamRecord,
    chemicals: object | None = None,
) -> bst.Stream:
    """Create one named stream safely, using an isolated context if needed."""

    from Greenhub.chemicals import chemicals as project_chemicals, thermo as project_thermo

    thermo = project_thermo
    if chemicals is not None:
        if hasattr(chemicals, "chemicals"):
            thermo = chemicals
        else:
            import thermosteam as tmo

            thermo = tmo.Thermo(chemicals)
    elif project_chemicals is not project_thermo.chemicals:  # pragma: no cover
        raise RuntimeError("GreenHub chemical package is internally inconsistent.")

    def create() -> bst.Stream:
        flows = {
            name: mass
            for name, mass in record.component_masses_kg_hr.items()
            if name in EXACT_BIOSTEAM_COMPONENTS and mass > 0.0
        }
        unknown = sorted(set(record.component_masses_kg_hr) - set(EXACT_BIOSTEAM_COMPONENTS))
        if unknown:
            raise KeyError(
                "Dynamic adapter encountered component identities without an approved exact "
                f"BioSTEAM mapping: {', '.join(unknown)}."
            )
        return bst.Stream(
            ID=record.adapter_stream_id,
            thermo=thermo,
            units="kg/hr",
            **flows,
        )

    with _FLOWSHEET_LOCK:
        current = bst.main_flowsheet.get_flowsheet()
        if current.ID.startswith("greenhub_dynamic_shadow_"):
            return create()
        isolated = bst.Flowsheet(f"greenhub_dynamic_shadow_single_{record.adapter_stream_id}")
        try:
            with isolated:
                return create()
        finally:
            _unregister_isolated_flowsheet(isolated)


def build_dynamic_biosteam_shadow_streams(
    preview_or_grid_step: DynamicPathwayPreview | DynamicProteinScenarioRun,
    config: DynamicBioSTEAMAdapterConfig,
) -> dict[str, bst.Stream]:
    """Create all selected exact-component streams in one isolated flowsheet."""

    preview = (
        preview_or_grid_step.pathway_preview
        if isinstance(preview_or_grid_step, DynamicProteinScenarioRun)
        else preview_or_grid_step
    )
    if preview is None:
        raise ValueError("The dynamic scenario step has no pathway preview to adapt.")
    records = dynamic_pathway_to_adapter_records(preview, config)
    flowsheet = bst.Flowsheet(_shadow_flowsheet_id(config.scenario_id, preview.time_label))
    streams: dict[str, bst.Stream] = {}
    with _FLOWSHEET_LOCK:
        try:
            with flowsheet:
                for record in records:
                    streams[record.adapter_stream_id] = adapter_record_to_biosteam_stream(record)
        finally:
            _unregister_isolated_flowsheet(flowsheet)
    return streams


def build_dynamic_biosteam_shadow_flowsheet(
    config: DynamicBioSTEAMAdapterConfig,
) -> DynamicBioSTEAMAdapterResult:
    """Build and validate one independent monthly shadow stream set."""

    scenario_config = config.resolved_scenario_config()
    run = run_dynamic_protein_scenario_step(scenario_config, config.time_label)
    return _build_adapter_result_from_run(config, run)


def validate_dynamic_biosteam_adapter_result(
    result: DynamicBioSTEAMAdapterResult,
    *,
    tolerance_kg_hr: float = MASS_TOLERANCE_KG_HR,
) -> DynamicBioSTEAMMassBalance:
    """Validate source scaling, BioSTEAM identity, and final pathway closure."""

    preview = result.source_run.pathway_preview
    if preview is None:
        raise ValueError("Cannot validate an adapter result without a source pathway preview.")
    records = {record.source_dynamic_stream_id: record for record in result.records}
    source_streams = _source_stream_lookup(preview)
    source_match = all(
        abs(record.stream_mass_kg_hr - source_streams[name].kg_per_kg_feed * result.config.basis_feed_kg_per_hr)
        <= tolerance_kg_hr
        for name, record in records.items()
    )

    per_stream: dict[str, float] = {}
    for record in result.records:
        stream = result.biosteam_streams.get(record.adapter_stream_id)
        if stream is None:
            per_stream[record.adapter_stream_id] = 0.0 if not result.config.create_biosteam_objects else math.inf
            continue
        residuals = [
            float(stream.imass[name]) - mass
            for name, mass in record.component_masses_kg_hr.items()
        ]
        per_stream[record.adapter_stream_id] = max((abs(value) for value in residuals), default=0.0)
    per_stream_match = all(value <= tolerance_kg_hr for value in per_stream.values())

    raw_input = preview.raw_press.inputs[0]
    input_components = {
        name: mass * result.config.basis_feed_kg_per_hr
        for name, mass in raw_input.component_masses_kg_per_kg_feed.items()
    }
    input_metadata = {
        name: mass * result.config.basis_feed_kg_per_hr
        for name, mass in raw_input.metadata_pools_kg_per_kg_feed.items()
    }
    final_records = [records[name] for name in FINAL_OUTPUT_STREAM_IDS if name in records]
    output_mass = sum(record.stream_mass_kg_hr for record in final_records)
    output_components = _sum_mappings(record.component_masses_kg_hr for record in final_records)
    output_metadata = _sum_mappings(record.metadata_pools_kg_hr for record in final_records)
    component_residuals = _mapping_residuals(input_components, output_components)
    metadata_residuals = _mapping_residuals(input_metadata, output_metadata)
    overall_residual = result.config.basis_feed_kg_per_hr - output_mass
    overall_closes = abs(overall_residual) <= tolerance_kg_hr
    identity_closes = all(
        abs(value) <= tolerance_kg_hr
        for value in (*component_residuals.values(), *metadata_residuals.values())
    )
    metadata_preserved = all(
        abs(record.stream_mass_kg_hr - record.total_component_kg_hr - record.total_metadata_kg_hr - record.unassigned_mass_kg_hr)
        <= tolerance_kg_hr
        for record in result.records
    )
    residual_input_ids = {
        stream.stream_id for stream in preview.biogas_mix_preparation.inputs
    }
    press_boundary = (
        "press_cake" in records
        and "press_cake" not in residual_input_ids
        and residual_input_ids == {"cell_debris", "final_supernatant"}
    )
    dried_source = source_streams["dried_protein_product"]
    dried_record = records.get("dried_protein_product")
    dried_match = dried_record is not None and all(
        abs(
            dried_record.component_masses_kg_hr.get(name, 0.0)
            - dried_source.component_masses_kg_per_kg_feed.get(name, 0.0)
            * result.config.basis_feed_kg_per_hr
        ) <= tolerance_kg_hr
        for name in ("SolubleProtein", "SuspendedProtein")
    )
    evaporated_source = source_streams["evaporated_water"]
    evaporated_record = records.get("evaporated_water")
    wet_source = source_streams["wet_protein_cake"]
    water_removed = (
        wet_source.component_masses_kg_per_kg_feed.get("Water", 0.0)
        - dried_source.component_masses_kg_per_kg_feed.get("Water", 0.0)
    ) * result.config.basis_feed_kg_per_hr
    evaporated_match = evaporated_record is not None and abs(
        evaporated_record.component_masses_kg_hr.get("Water", 0.0)
        - evaporated_source.component_masses_kg_per_kg_feed.get("Water", 0.0)
        * result.config.basis_feed_kg_per_hr
    ) <= tolerance_kg_hr and abs(
        evaporated_record.component_masses_kg_hr.get("Water", 0.0) - water_removed
    ) <= tolerance_kg_hr
    empirical_unchanged = bool(result.provenance.get("empirical_flowsheet_unchanged"))
    warnings = []
    if not result.config.create_biosteam_objects:
        warnings.append("biosteam_object_creation_disabled_records_only")
    if not overall_closes:
        warnings.append("selected_adapter_final_outputs_do_not_close_feed_mass")
    closes = all((
        overall_closes,
        identity_closes,
        per_stream_match,
        metadata_preserved,
        source_match,
        press_boundary,
        dried_match,
        evaporated_match,
        empirical_unchanged,
    ))
    return DynamicBioSTEAMMassBalance(
        basis_feed_kg_hr=result.config.basis_feed_kg_per_hr,
        final_output_mass_kg_hr=output_mass,
        overall_residual_kg_hr=overall_residual,
        overall_closes=overall_closes,
        component_residuals_kg_hr=component_residuals,
        metadata_residuals_kg_hr=metadata_residuals,
        identity_closes=identity_closes,
        per_stream_component_residuals_kg_hr=per_stream,
        per_stream_component_masses_match=per_stream_match,
        metadata_preserved_in_records=metadata_preserved,
        source_stream_masses_match=source_match,
        press_cake_boundary_valid=press_boundary,
        dried_protein_matches_source=dried_match,
        evaporated_water_matches_source=evaporated_match,
        empirical_flowsheet_unchanged=empirical_unchanged,
        closes=closes,
        warnings=tuple(warnings),
    )


def build_dynamic_biosteam_shadow_grid(
    config: DynamicBioSTEAMAdapterConfig,
) -> DynamicBioSTEAMAdapterGridResult:
    """Build independent monthly adapters; this is not dynamic scheduling."""

    source_grid = run_dynamic_protein_scenario_grid(config.resolved_scenario_config())
    results = tuple(
        _build_adapter_result_from_run(replace(config, time_label=run.time_label), run)
        for run in source_grid.runs
    )
    warnings = Counter(item for result in results for item in result.warnings)
    blockers = Counter(item for result in results for item in result.blockers)
    return DynamicBioSTEAMAdapterGridResult(
        config=config,
        source_grid=source_grid,
        step_results=results,
        time_labels=tuple(result.config.time_label for result in results),
        all_steps_close=all(result.mass_balance.closes for result in results),
        all_empirical_flowsheets_unchanged=all(
            result.mass_balance.empirical_flowsheet_unchanged for result in results
        ),
        warning_counts=dict(sorted(warnings.items())),
        blocker_counts=dict(sorted(blockers.items())),
        provenance={
            "batch_semantics": "independent_monthly_shadow_flowsheets",
            "dynamic_scheduling_active": False,
            "empirical_model_modified": False,
            "model_overrides": [],
        },
    )


def write_dynamic_biosteam_adapter_reports(
    result_or_grid: DynamicBioSTEAMAdapterResult | DynamicBioSTEAMAdapterGridResult,
    output_dir: str | Path | None = None,
) -> dict[str, str]:
    """Write stream, balance, and provenance audit CSVs."""

    target = Path(output_dir) if output_dir is not None else RESULTS_DIR
    target.mkdir(parents=True, exist_ok=True)
    paths = {
        "streams": target / "dynamic_biosteam_adapter_streams.csv",
        "balance": target / "dynamic_biosteam_adapter_balance.csv",
        "provenance": target / "dynamic_biosteam_adapter_provenance.csv",
    }
    results = (
        result_or_grid.step_results
        if isinstance(result_or_grid, DynamicBioSTEAMAdapterGridResult)
        else (result_or_grid,)
    )
    stream_rows: list[dict[str, object]] = []
    provenance_rows: list[dict[str, object]] = []
    balance_rows: list[dict[str, object]] = []
    for result in results:
        for record in result.records:
            common = _record_report_common(record)
            entries = [
                {"component": name, "component_kg_hr": mass, "metadata_pool": "", "metadata_kg_hr": ""}
                for name, mass in record.component_masses_kg_hr.items()
            ] + [
                {"component": "", "component_kg_hr": "", "metadata_pool": name, "metadata_kg_hr": mass}
                for name, mass in record.metadata_pools_kg_hr.items()
            ]
            for entry in entries or [{"component": "", "component_kg_hr": "", "metadata_pool": "", "metadata_kg_hr": ""}]:
                stream_rows.append({**common, **entry})
            provenance_rows.append({
                **common,
                "provenance_json": json.dumps(record.provenance, sort_keys=True),
            })
        balance = result.mass_balance
        balance_rows.append({
            "scenario_id": result.config.scenario_id,
            "time_label": result.config.time_label,
            "adapter_stream_id": "",
            "source_dynamic_stream_id": "final_outputs",
            "source_unit_id": "pathway_boundary",
            "component": "",
            "component_kg_hr": "",
            "metadata_pool": "",
            "metadata_kg_hr": "",
            "stream_mass_kg_hr": balance.final_output_mass_kg_hr,
            "unassigned_mass_kg_hr": balance.overall_residual_kg_hr,
            "evidence_class": "shadow_mass_identity_validation",
            "policy_status": result.activation_status,
            "source_id": "",
            "record_id": "",
            "warning": "|".join(balance.warnings),
            "blocker": "|".join(result.blockers),
            "created_biosteam_stream_id": "",
            "overall_closes": balance.overall_closes,
            "identity_closes": balance.identity_closes,
            "per_stream_component_masses_match": balance.per_stream_component_masses_match,
            "metadata_preserved_in_records": balance.metadata_preserved_in_records,
            "press_cake_boundary_valid": balance.press_cake_boundary_valid,
            "empirical_flowsheet_unchanged": balance.empirical_flowsheet_unchanged,
            "adapter_closes": balance.closes,
            "component_residuals_json": json.dumps(balance.component_residuals_kg_hr, sort_keys=True),
            "metadata_residuals_json": json.dumps(balance.metadata_residuals_kg_hr, sort_keys=True),
        })
    common_fields = (
        "scenario_id", "time_label", "adapter_stream_id", "source_dynamic_stream_id",
        "source_unit_id", "component", "component_kg_hr", "metadata_pool",
        "metadata_kg_hr", "stream_mass_kg_hr", "unassigned_mass_kg_hr",
        "policy_ids", "evidence_class", "policy_status", "source_id", "record_id", "warning",
        "blocker", "created_biosteam_stream_id",
    )
    _write_rows(paths["streams"], common_fields, stream_rows)
    _write_rows(paths["provenance"], common_fields + ("provenance_json",), provenance_rows)
    _write_rows(paths["balance"], common_fields + (
        "overall_closes", "identity_closes", "per_stream_component_masses_match",
        "metadata_preserved_in_records", "press_cake_boundary_valid",
        "empirical_flowsheet_unchanged", "adapter_closes",
        "component_residuals_json", "metadata_residuals_json",
    ), balance_rows)
    return {name: str(path) for name, path in paths.items()}


def build_dynamic_biosteam_shadow_system(
    time_label: str = "2026-05",
    basis_feed_kg_per_hr: float = 1000.0,
    *,
    config: DynamicBioSTEAMAdapterConfig | None = None,
) -> DynamicBioSTEAMShadowSystemResult:
    """Build one isolated six-unit target-output BioSTEAM system."""

    if config is None:
        config = DynamicBioSTEAMAdapterConfig(
            time_label=time_label,
            basis_feed_kg_per_hr=basis_feed_kg_per_hr,
        )
    elif time_label != "2026-05" or basis_feed_kg_per_hr != 1000.0:
        config = replace(
            config,
            time_label=time_label,
            basis_feed_kg_per_hr=basis_feed_kg_per_hr,
        )
    run = run_dynamic_protein_scenario_step(
        config.resolved_scenario_config(), config.time_label
    )
    return _build_shadow_system_from_run(config, run)


def validate_dynamic_biosteam_shadow_system(
    result: DynamicBioSTEAMShadowSystemResult,
    *,
    tolerance_kg_hr: float = MASS_TOLERANCE_KG_HR,
) -> DynamicBioSTEAMShadowSystemBalance:
    """Validate every target-output unit and the isolated system boundary."""

    records = {
        record.source_dynamic_stream_id: record for record in result.adapter_records
    }
    unit_output_ids = {
        "raw_press": (
            "press_cake",
            "brown_juice",
            "raw_press_unrecovered_process_mass",
        ),
        "first_centrifuge": ("clarified_juice", "cell_debris"),
        "protein_extraction": ("protein_rich_phase", "extraction_supernatant"),
        "second_centrifuge": ("wet_protein_cake", "final_supernatant"),
        "protein_dryer": ("dried_protein_product", "evaporated_water"),
        "residual_mixer": ("biogas_feed_candidate",),
    }
    unit_balances: list[DynamicBioSTEAMShadowUnitBalance] = []
    for name, unit in result.units.items():
        input_components = _stream_component_inventory(unit.ins)
        output_components = _stream_component_inventory(unit.outs)
        residuals = _mapping_residuals(input_components, output_components)
        input_mass = sum(input_components.values())
        output_mass = sum(output_components.values())
        residual = input_mass - output_mass
        identity_closes = all(
            abs(value) <= tolerance_kg_hr for value in residuals.values()
        )
        outputs_match = all(
            _biosteam_stream_matches_record(
                result.streams[stream_id], records[stream_id], tolerance_kg_hr
            )
            for stream_id in unit_output_ids[name]
        )
        unit_balances.append(
            DynamicBioSTEAMShadowUnitBalance(
                unit_id=unit.ID,
                unit_type=type(unit).__name__,
                input_mass_kg_hr=input_mass,
                output_mass_kg_hr=output_mass,
                residual_kg_hr=residual,
                component_residuals_kg_hr=residuals,
                identity_closes=identity_closes,
                outputs_match_adapter_records=outputs_match,
                closes=abs(residual) <= tolerance_kg_hr and identity_closes and outputs_match,
            )
        )

    terminal_ids = FINAL_OUTPUT_STREAM_IDS
    input_components = dict(result.feed_record.component_masses_kg_hr)
    terminal_components = _stream_component_inventory(
        tuple(result.streams[name] for name in terminal_ids)
    )
    component_residuals = _mapping_residuals(input_components, terminal_components)
    input_mass = sum(input_components.values())
    terminal_mass = sum(terminal_components.values())
    exact_residual = input_mass - terminal_mass
    exact_identity_closes = all(
        abs(value) <= tolerance_kg_hr for value in component_residuals.values()
    )
    residual_inputs = {
        stream.ID for stream in result.units["residual_mixer"].ins
    }
    press_boundary = (
        result.streams["press_cake"].ID not in residual_inputs
        and residual_inputs
        == {
            result.streams["cell_debris"].ID,
            result.streams["final_supernatant"].ID,
        }
    )
    adapter_balance = result.source_adapter.mass_balance
    all_outputs_match = all(
        balance.outputs_match_adapter_records for balance in unit_balances
    )
    empirical_unchanged = bool(
        result.provenance.get("empirical_flowsheet_unchanged")
    )
    closes = all(
        (
            abs(exact_residual) <= tolerance_kg_hr,
            exact_identity_closes,
            adapter_balance.overall_closes,
            adapter_balance.identity_closes,
            all(balance.closes for balance in unit_balances),
            all_outputs_match,
            press_boundary,
            empirical_unchanged,
        )
    )
    warnings = () if closes else ("shadow_system_validation_incomplete",)
    return DynamicBioSTEAMShadowSystemBalance(
        input_component_mass_kg_hr=input_mass,
        terminal_component_mass_kg_hr=terminal_mass,
        exact_component_residual_kg_hr=exact_residual,
        component_residuals_kg_hr=component_residuals,
        exact_component_identity_closes=exact_identity_closes,
        adapter_full_mass_closes=adapter_balance.overall_closes,
        adapter_metadata_identity_closes=adapter_balance.identity_closes,
        all_unit_outputs_match_adapter_records=all_outputs_match,
        unit_balances=tuple(unit_balances),
        press_cake_boundary_valid=press_boundary,
        empirical_flowsheet_unchanged=empirical_unchanged,
        closes=closes,
        warnings=warnings,
    )


def build_dynamic_biosteam_shadow_system_grid(
    config: DynamicBioSTEAMAdapterConfig | None = None,
) -> DynamicBioSTEAMShadowSystemGridResult:
    """Build seven independent monthly unit systems without time integration."""

    config = config or DynamicBioSTEAMAdapterConfig()
    source_grid = run_dynamic_protein_scenario_grid(config.resolved_scenario_config())
    results = tuple(
        _build_shadow_system_from_run(replace(config, time_label=run.time_label), run)
        for run in source_grid.runs
    )
    warning_counts = Counter(item for result in results for item in result.warnings)
    blocker_counts = Counter(item for result in results for item in result.blockers)
    return DynamicBioSTEAMShadowSystemGridResult(
        config=config,
        step_results=results,
        time_labels=tuple(result.config.time_label for result in results),
        all_steps_close=all(result.mass_balance.closes for result in results),
        all_steps_shadow_ready=all(result.can_drive_shadow_system for result in results),
        all_empirical_flowsheets_unchanged=all(
            result.mass_balance.empirical_flowsheet_unchanged for result in results
        ),
        warning_counts=dict(sorted(warning_counts.items())),
        blocker_counts=dict(sorted(blocker_counts.items())),
        provenance={
            "batch_semantics": "independent_monthly_target_output_biosteam_systems",
            "continuous_dynamic_scheduling_active": False,
            "calculation_owning_units_active": False,
            "empirical_model_modified": False,
            "model_overrides": [],
        },
    )


def write_dynamic_biosteam_shadow_system_reports(
    result_or_grid: (
        DynamicBioSTEAMShadowSystemResult | DynamicBioSTEAMShadowSystemGridResult
    ),
    output_dir: str | Path | None = None,
) -> dict[str, str]:
    """Write concise unit and system balance reports for shadow systems."""

    target = Path(output_dir) if output_dir is not None else RESULTS_DIR
    target.mkdir(parents=True, exist_ok=True)
    paths = {
        "units": target / "dynamic_biosteam_shadow_units.csv",
        "balance": target / "dynamic_biosteam_shadow_system_balance.csv",
    }
    results = (
        result_or_grid.step_results
        if isinstance(result_or_grid, DynamicBioSTEAMShadowSystemGridResult)
        else (result_or_grid,)
    )
    fields = (
        "time_label",
        "unit_id",
        "unit_type",
        "input_streams",
        "output_streams",
        "input_mass_kg_hr",
        "output_mass_kg_hr",
        "residual_kg_hr",
        "identity_closes",
        "policy_status",
        "evidence_class",
        "warning",
        "blocker",
    )
    unit_rows: list[dict[str, object]] = []
    balance_rows: list[dict[str, object]] = []
    for result in results:
        balances = {item.unit_id: item for item in result.mass_balance.unit_balances}
        for unit in result.units.values():
            balance = balances[unit.ID]
            unit_rows.append(
                {
                    "time_label": result.config.time_label,
                    "unit_id": unit.ID,
                    "unit_type": type(unit).__name__,
                    "input_streams": "|".join(stream.ID for stream in unit.ins),
                    "output_streams": "|".join(stream.ID for stream in unit.outs),
                    "input_mass_kg_hr": balance.input_mass_kg_hr,
                    "output_mass_kg_hr": balance.output_mass_kg_hr,
                    "residual_kg_hr": balance.residual_kg_hr,
                    "identity_closes": balance.identity_closes,
                    "policy_status": unit.shadow_policy_status,
                    "evidence_class": "|".join(unit.shadow_evidence_classes),
                    "warning": "|".join(unit.shadow_warnings),
                    "blocker": "|".join(unit.shadow_blockers),
                }
            )
        balance_rows.append(
            {
                "time_label": result.config.time_label,
                "unit_id": result.system.ID,
                "unit_type": "bst.System",
                "input_streams": result.streams["whole_feed"].ID,
                "output_streams": "|".join(
                    result.streams[name].ID for name in FINAL_OUTPUT_STREAM_IDS
                ),
                "input_mass_kg_hr": result.source_adapter.mass_balance.basis_feed_kg_hr,
                "output_mass_kg_hr": result.source_adapter.mass_balance.final_output_mass_kg_hr,
                "residual_kg_hr": result.source_adapter.mass_balance.overall_residual_kg_hr,
                "identity_closes": (
                    result.mass_balance.exact_component_identity_closes
                    and result.mass_balance.adapter_metadata_identity_closes
                ),
                "policy_status": result.activation_status,
                "evidence_class": "target_output_shadow_from_traceable_dynamic_records",
                "warning": "|".join(result.warnings),
                "blocker": "|".join(result.blockers),
            }
        )
    _write_rows(paths["units"], fields, unit_rows)
    _write_rows(paths["balance"], fields, balance_rows)
    return {name: str(path) for name, path in paths.items()}


def build_dynamic_biosteam_calculation_shadow_system(
    config: DynamicBioSTEAMAdapterConfig | None = None,
) -> DynamicBioSTEAMCalculationSystemResult:
    """Build one isolated system whose units calculate from policy payloads."""

    config = config or DynamicBioSTEAMAdapterConfig(
        adapter_mode=CALCULATION_ADAPTER_MODE
    )
    if config.adapter_mode == ADAPTER_MODE:
        config = replace(config, adapter_mode=CALCULATION_ADAPTER_MODE)
    run = run_dynamic_protein_scenario_step(
        config.resolved_scenario_config(), config.time_label
    )
    return _build_calculation_shadow_system_from_run(config, run)


def validate_dynamic_biosteam_calculation_shadow_system(
    result: DynamicBioSTEAMCalculationSystemResult,
    *,
    tolerance_kg_hr: float = MASS_TOLERANCE_KG_HR,
) -> DynamicBioSTEAMCalculationValidation:
    """Validate calculation ownership against authoritative adapter records."""

    if result.system is None:
        return result.validation
    records = {
        record.source_dynamic_stream_id: record for record in result.adapter_records
    }
    unit_outputs = {
        "raw_press": (
            "press_cake", "brown_juice", "raw_press_unrecovered_process_mass"
        ),
        "first_centrifuge": ("clarified_juice", "cell_debris"),
        "protein_extraction": ("protein_rich_phase", "extraction_supernatant"),
        "second_centrifuge": ("wet_protein_cake", "final_supernatant"),
        "protein_dryer": ("dried_protein_product", "evaporated_water"),
        "residual_mixer": ("biogas_feed_candidate",),
    }
    parities: list[DynamicBioSTEAMCalculationUnitParity] = []
    for key, unit in result.units.items():
        input_inventory = _stream_component_inventory(unit.ins)
        output_inventory = _stream_component_inventory(unit.outs)
        component_residuals = _mapping_residuals(input_inventory, output_inventory)
        input_mass = sum(input_inventory.values())
        output_mass = sum(output_inventory.values())
        residual = input_mass - output_mass
        identity_closes = all(
            abs(value) <= tolerance_kg_hr for value in component_residuals.values()
        )
        parity_values: list[float] = []
        for stream_id in unit_outputs[key]:
            stream = result.streams[stream_id]
            record = records[stream_id]
            parity_values.append(abs(float(stream.F_mass) - record.total_component_kg_hr))
            parity_values.extend(
                abs(float(stream.imass[name]) - mass)
                for name, mass in record.component_masses_kg_hr.items()
            )
        parity_residual = max(parity_values, default=0.0)
        parity_passed = parity_residual <= tolerance_kg_hr
        payload = unit.calculation_payload
        parities.append(
            DynamicBioSTEAMCalculationUnitParity(
                unit_key=key,
                unit_id=unit.ID,
                unit_type=type(unit).__name__,
                input_mass_kg_hr=input_mass,
                output_mass_kg_hr=output_mass,
                residual_kg_hr=residual,
                parity_residual_kg_hr=parity_residual,
                identity_closes=identity_closes,
                target_parity_passed=parity_passed,
                policy_id=payload.policy_id,
                evidence_classes=payload.evidence_classes,
                warnings=payload.warnings,
                blockers=payload.blockers,
            )
        )
    terminal = _stream_component_inventory(
        tuple(result.streams[name] for name in FINAL_OUTPUT_STREAM_IDS)
    )
    exact_residuals = _mapping_residuals(
        result.feed_record.component_masses_kg_hr, terminal
    )
    exact_identity = all(
        abs(value) <= tolerance_kg_hr for value in exact_residuals.values()
    )
    residual_inputs = {stream.ID for stream in result.units["residual_mixer"].ins}
    press_boundary = residual_inputs == {
        result.streams["cell_debris"].ID,
        result.streams["final_supernatant"].ID,
    } and result.streams["press_cake"].ID not in residual_inputs
    metadata_preserved = (
        result.source_adapter.mass_balance.metadata_preserved_in_records
        and any(record.metadata_pools_kg_hr for record in result.adapter_records)
    )
    empirical_unchanged = bool(
        result.provenance.get("empirical_flowsheet_unchanged")
    )
    method_payload = result.payloads.protein_extraction
    all_parity = all(item.target_parity_passed for item in parities)
    closes = all(
        (
            all_parity,
            all(item.identity_closes for item in parities),
            exact_identity,
            result.source_adapter.mass_balance.overall_closes,
            metadata_preserved,
            press_boundary,
            empirical_unchanged,
            method_payload.calculation_ready,
        )
    )
    return DynamicBioSTEAMCalculationValidation(
        unit_parities=tuple(parities),
        all_unit_parity_passed=all_parity,
        exact_component_identity_closes=exact_identity,
        adapter_full_mass_closes=result.source_adapter.mass_balance.overall_closes,
        metadata_records_preserved=metadata_preserved,
        press_cake_boundary_valid=press_boundary,
        empirical_flowsheet_unchanged=empirical_unchanged,
        selected_method=method_payload.method,
        selected_method_calculation_ready=method_payload.calculation_ready,
        closes=closes,
        warnings=() if closes else ("calculation_shadow_validation_incomplete",),
    )


def build_dynamic_biosteam_calculation_shadow_system_grid(
    config: DynamicBioSTEAMAdapterConfig | None = None,
) -> DynamicBioSTEAMCalculationGridResult:
    """Build independent monthly calculation systems for the configured grid."""

    config = config or DynamicBioSTEAMAdapterConfig(
        adapter_mode=CALCULATION_ADAPTER_MODE
    )
    if config.adapter_mode == ADAPTER_MODE:
        config = replace(config, adapter_mode=CALCULATION_ADAPTER_MODE)
    source_grid = run_dynamic_protein_scenario_grid(config.resolved_scenario_config())
    results = tuple(
        _build_calculation_shadow_system_from_run(
            replace(config, time_label=run.time_label), run
        )
        for run in source_grid.runs
    )
    warnings = Counter(item for result in results for item in result.warnings)
    blockers = Counter(item for result in results for item in result.blockers)
    return DynamicBioSTEAMCalculationGridResult(
        config=config,
        step_results=results,
        time_labels=tuple(result.config.time_label for result in results),
        all_steps_parity_passed=all(
            result.validation.all_unit_parity_passed for result in results
        ),
        all_steps_calculation_shadow_ready=all(
            result.can_drive_calculation_shadow_system for result in results
        ),
        all_empirical_flowsheets_unchanged=all(
            result.validation.empirical_flowsheet_unchanged for result in results
        ),
        warning_counts=dict(sorted(warnings.items())),
        blocker_counts=dict(sorted(blockers.items())),
        provenance={
            "batch_semantics": "independent_monthly_calculation_shadow_systems",
            "selected_method": config.resolved_scenario_config().protein_method,
            "continuous_dynamic_scheduling_active": False,
            "empirical_model_modified": False,
            "model_overrides": [],
        },
    )


def write_dynamic_biosteam_calculation_shadow_reports(
    result_or_grid: (
        DynamicBioSTEAMCalculationSystemResult | DynamicBioSTEAMCalculationGridResult
    ),
    output_dir: str | Path | None = None,
) -> dict[str, str]:
    """Write unit, balance, and parity reports for calculation shadow mode."""

    target = Path(output_dir) if output_dir is not None else RESULTS_DIR
    target.mkdir(parents=True, exist_ok=True)
    paths = {
        "units": target / "dynamic_biosteam_calculation_units.csv",
        "balance": target / "dynamic_biosteam_calculation_balance.csv",
        "parity": target / "dynamic_biosteam_calculation_parity.csv",
    }
    results = (
        result_or_grid.step_results
        if isinstance(result_or_grid, DynamicBioSTEAMCalculationGridResult)
        else (result_or_grid,)
    )
    fields = (
        "time_label", "unit_id", "unit_type", "calculation_mode", "policy_id",
        "input_mass_kg_hr", "output_mass_kg_hr", "residual_kg_hr",
        "parity_residual_kg_hr", "identity_closes", "target_parity_passed",
        "evidence_class", "warning", "blocker",
        "water_added_kg_hr", "press_energy_kwh_hr",
    )
    unit_rows: list[dict[str, object]] = []
    parity_rows: list[dict[str, object]] = []
    balance_rows: list[dict[str, object]] = []
    for result in results:
        for parity in result.validation.unit_parities:
            row = {
                "time_label": result.config.time_label,
                "unit_id": parity.unit_id,
                "unit_type": parity.unit_type,
                "calculation_mode": result.activation_status,
                "policy_id": parity.policy_id,
                "input_mass_kg_hr": parity.input_mass_kg_hr,
                "output_mass_kg_hr": parity.output_mass_kg_hr,
                "residual_kg_hr": parity.residual_kg_hr,
                "parity_residual_kg_hr": parity.parity_residual_kg_hr,
                "identity_closes": parity.identity_closes,
                "target_parity_passed": parity.target_parity_passed,
                "evidence_class": "|".join(parity.evidence_classes),
                "warning": "|".join(parity.warnings),
                "blocker": "|".join(parity.blockers),
            }
            unit = result.units.get(parity.unit_id) if result.units else None
            row["water_added_kg_hr"] = getattr(unit, "water_added_kg_hr", 0.0)
            row["press_energy_kwh_hr"] = getattr(unit, "press_energy_kwh_hr", 0.0)
            unit_rows.append(row)
            parity_rows.append(dict(row))
        balance_rows.append({
            "time_label": result.config.time_label,
            "unit_id": result.system.ID if result.system is not None else "blocked",
            "unit_type": "bst.System" if result.system is not None else "blocked_system",
            "calculation_mode": result.activation_status,
            "policy_id": result.payloads.protein_extraction.policy_id,
            "input_mass_kg_hr": result.source_adapter.mass_balance.basis_feed_kg_hr,
            "output_mass_kg_hr": result.source_adapter.mass_balance.final_output_mass_kg_hr,
            "residual_kg_hr": result.source_adapter.mass_balance.overall_residual_kg_hr,
            "parity_residual_kg_hr": max(
                (item.parity_residual_kg_hr for item in result.validation.unit_parities),
                default=0.0,
            ),
            "identity_closes": result.validation.exact_component_identity_closes,
            "target_parity_passed": result.validation.all_unit_parity_passed,
            "evidence_class": "calculation_shadow_from_resolved_policy_payloads",
            "warning": "|".join(result.warnings),
            "blocker": "|".join(result.blockers),
        })
    _write_rows(paths["units"], fields, unit_rows)
    _write_rows(paths["balance"], fields, balance_rows)
    _write_rows(paths["parity"], fields, parity_rows)
    return {name: str(path) for name, path in paths.items()}


def summarize_pretreatment_utilities(
    result_or_grid: DynamicBioSTEAMCalculationSystemResult | DynamicBioSTEAMCalculationGridResult,
    operating_hours_by_time_label: Mapping[str, float] | None = None,
) -> dict[str, object]:
    """Aggregate raw-press dilution and energy from calculation-shadow steps."""

    results = (
        result_or_grid.step_results
        if isinstance(result_or_grid, DynamicBioSTEAMCalculationGridResult)
        else (result_or_grid,)
    )
    rows = []
    hours_complete = operating_hours_by_time_label is not None
    for result in results:
        unit = next((item for item in result.units.values() if item.ID.endswith("_raw_press")), None)
        hours = None if operating_hours_by_time_label is None else float(operating_hours_by_time_label.get(result.config.time_label, 0.0))
        if hours is None:
            hours_complete = False
        rows.append({
            "time_label": result.config.time_label,
            "water_added_kg_hr": float(getattr(unit, "water_added_kg_hr", 0.0)),
            "press_energy_kwh_hr": float(getattr(unit, "press_energy_kwh_hr", 0.0)),
            "operating_hours": hours,
            "water_added_kg": None if hours is None else float(getattr(unit, "water_added_kg_hr", 0.0)) * hours,
            "press_energy_kwh": None if hours is None else float(getattr(unit, "press_energy_kwh_hr", 0.0)) * hours,
            "status": "reported_unit_state" if unit is not None else "unavailable",
        })
    annual_water = sum(row["water_added_kg"] for row in rows) if hours_complete else None
    annual_energy = sum(row["press_energy_kwh"] for row in rows) if hours_complete else None
    return {
        "water_added_kg_hr_total": sum(row["water_added_kg_hr"] for row in rows),
        "press_energy_kwh_hr_total": sum(row["press_energy_kwh_hr"] for row in rows),
        "timestep_count": len(rows),
        "rows": rows,
        "annual_water_added_kg": annual_water,
        "annual_press_energy_kwh": annual_energy,
        "annualization_status": "complete" if hours_complete else "incomplete_missing_operating_hours",
        "basis": "sum of dynamic raw-press unit states; hours are not annualized without an operating schedule",
        "status": "complete_for_reported_timesteps" if rows else "unavailable",
    }


def _build_calculation_shadow_system_from_run(
    config: DynamicBioSTEAMAdapterConfig,
    run: DynamicProteinScenarioRun,
) -> DynamicBioSTEAMCalculationSystemResult:
    from Greenhub.chemicals import thermo
    from Greenhub.dynamic_biosteam_units import (
        DynamicFirstCentrifugeCalculationUnit,
        DynamicProteinDryerCalculationUnit,
        DynamicProteinExtractionCalculationUnit,
        DynamicRawPressCalculationUnit,
        DynamicResidualMixerCalculationUnit,
        DynamicSecondCentrifugeCalculationUnit,
        build_dynamic_protein_calculation_payloads,
    )

    preview = run.pathway_preview
    if preview is None:
        raise ValueError(f"Dynamic scenario step '{run.time_label}' has no pathway preview.")
    payloads = build_dynamic_protein_calculation_payloads(run)
    source_adapter = _build_adapter_result_from_run(
        replace(config, create_biosteam_objects=False),
        run,
        require_proxy_ready=False,
    )
    feed_record = dynamic_process_stream_to_adapter_record(
        preview.raw_press.inputs[0],
        config.basis_feed_kg_per_hr,
        scenario_id=config.scenario_id,
    )
    method_payload = payloads.protein_extraction
    if not method_payload.calculation_ready:
        blocker = f"protein_method_not_calculation_ready:{method_payload.method}"
        validation = DynamicBioSTEAMCalculationValidation(
            unit_parities=(),
            all_unit_parity_passed=False,
            exact_component_identity_closes=False,
            adapter_full_mass_closes=source_adapter.mass_balance.overall_closes,
            metadata_records_preserved=(
                source_adapter.mass_balance.metadata_preserved_in_records
            ),
            press_cake_boundary_valid=True,
            empirical_flowsheet_unchanged=True,
            selected_method=method_payload.method,
            selected_method_calculation_ready=False,
            closes=False,
            warnings=("selected_method_returned_as_blocked_without_system_build",),
        )
        return DynamicBioSTEAMCalculationSystemResult(
            config=config,
            source_adapter=source_adapter,
            feed_record=feed_record,
            adapter_records=source_adapter.records,
            payloads=payloads,
            system=None,
            units={},
            streams={},
            isolated_flowsheet=None,
            validation=validation,
            warnings=tuple(dict.fromkeys((*run.warnings, *validation.warnings))),
            blockers=tuple(dict.fromkeys((*run.blockers, blocker))),
            provenance={
                "mode": "calculation_shadow_system_report_only_blocked_method",
                "selected_method": method_payload.method,
                "empirical_model_modified": False,
                "model_overrides": [],
            },
            can_drive_calculation_shadow_system=False,
        )

    records = {
        record.source_dynamic_stream_id: record for record in source_adapter.records
    }
    with _FLOWSHEET_LOCK:
        before_flowsheet = bst.main_flowsheet.get_flowsheet()
        before_registries = _flowsheet_registry_snapshot(before_flowsheet)
        flowsheet = bst.Flowsheet(
            f"greenhub_dynamic_calculation_shadow_{_safe_id(config.scenario_id)}_"
            f"{_safe_id(run.time_label)}"
        )
        try:
            with flowsheet:
                streams = {
                    "whole_feed": bst.Stream(
                        ID=feed_record.adapter_stream_id,
                        thermo=thermo,
                        units="kg/hr",
                        **feed_record.component_masses_kg_hr,
                    )
                }
                for stream_id, record in records.items():
                    streams[stream_id] = bst.Stream(
                        ID=record.adapter_stream_id,
                        thermo=thermo,
                    )
                prefix = f"dyn_{_safe_id(run.time_label)}_calc"
                units = {
                    "raw_press": DynamicRawPressCalculationUnit(
                        f"{prefix}_raw_press",
                        ins=streams["whole_feed"],
                        outs=(streams["press_cake"], streams["brown_juice"],
                              streams["raw_press_unrecovered_process_mass"]),
                        thermo=thermo,
                        payload=payloads.raw_press,
                    ),
                    "first_centrifuge": DynamicFirstCentrifugeCalculationUnit(
                        f"{prefix}_first_centrifuge",
                        ins=streams["brown_juice"],
                        outs=(streams["clarified_juice"], streams["cell_debris"]),
                        thermo=thermo,
                        payload=payloads.first_centrifuge,
                    ),
                    "protein_extraction": DynamicProteinExtractionCalculationUnit(
                        f"{prefix}_protein_extraction",
                        ins=streams["clarified_juice"],
                        outs=(streams["protein_rich_phase"], streams["extraction_supernatant"]),
                        thermo=thermo,
                        payload=payloads.protein_extraction,
                    ),
                    "second_centrifuge": DynamicSecondCentrifugeCalculationUnit(
                        f"{prefix}_second_centrifuge",
                        ins=(streams["protein_rich_phase"], streams["extraction_supernatant"]),
                        outs=(streams["wet_protein_cake"], streams["final_supernatant"]),
                        thermo=thermo,
                        payload=payloads.second_centrifuge,
                    ),
                    "protein_dryer": DynamicProteinDryerCalculationUnit(
                        f"{prefix}_protein_dryer",
                        ins=streams["wet_protein_cake"],
                        outs=(streams["dried_protein_product"], streams["evaporated_water"]),
                        thermo=thermo,
                        payload=payloads.protein_dryer,
                    ),
                    "residual_mixer": DynamicResidualMixerCalculationUnit(
                        f"{prefix}_residual_mixer",
                        ins=(streams["cell_debris"], streams["final_supernatant"]),
                        outs=streams["biogas_feed_candidate"],
                        thermo=thermo,
                        payload=payloads.residual_mixer,
                    ),
                }
                system = bst.System.from_units(
                    ID=f"{prefix}_protein_shadow_sys",
                    units=tuple(units.values()),
                )
                system.simulate()
        finally:
            _unregister_isolated_flowsheet(flowsheet)
        after_flowsheet = bst.main_flowsheet.get_flowsheet()
        empirical_unchanged = (
            after_flowsheet is before_flowsheet
            and _flowsheet_registry_snapshot(after_flowsheet) == before_registries
        )

    placeholder = DynamicBioSTEAMCalculationValidation(
        unit_parities=(), all_unit_parity_passed=False,
        exact_component_identity_closes=False,
        adapter_full_mass_closes=source_adapter.mass_balance.overall_closes,
        metadata_records_preserved=source_adapter.mass_balance.metadata_preserved_in_records,
        press_cake_boundary_valid=False,
        empirical_flowsheet_unchanged=empirical_unchanged,
        selected_method=method_payload.method,
        selected_method_calculation_ready=method_payload.calculation_ready,
        closes=False,
    )
    provisional = DynamicBioSTEAMCalculationSystemResult(
        config=config,
        source_adapter=source_adapter,
        feed_record=feed_record,
        adapter_records=source_adapter.records,
        payloads=payloads,
        system=system,
        units=units,
        streams=streams,
        isolated_flowsheet=flowsheet,
        validation=placeholder,
        warnings=tuple(dict.fromkeys((*run.warnings, "calculation_units_use_resolved_policy_payloads"))),
        blockers=run.blockers,
        provenance={
            "mode": "calculation_shadow_system_report_only",
            "selected_method": method_payload.method,
            "fraction_origin": "resolved_conservative_dynamic_process_unit_outputs",
            "target_output_masses_stored_in_units": False,
            "metadata_storage": "parallel_adapter_records_only",
            "press_cake_boundary": "external_system_output",
            "empirical_flowsheet_id_before": before_flowsheet.ID,
            "empirical_flowsheet_id_after": after_flowsheet.ID,
            "empirical_flowsheet_unchanged": empirical_unchanged,
            "model_overrides": [],
        },
        can_drive_calculation_shadow_system=False,
    )
    validation = validate_dynamic_biosteam_calculation_shadow_system(provisional)
    return replace(
        provisional,
        validation=validation,
        can_drive_calculation_shadow_system=validation.closes,
    )


def _build_shadow_system_from_run(
    config: DynamicBioSTEAMAdapterConfig,
    run: DynamicProteinScenarioRun,
) -> DynamicBioSTEAMShadowSystemResult:
    """Build one system from an existing source run without recalculation."""

    from Greenhub.chemicals import thermo
    from Greenhub.dynamic_biosteam_units import (
        DynamicFirstCentrifugeUnit,
        DynamicProteinDryerUnit,
        DynamicProteinExtractionUnit,
        DynamicRawPressUnit,
        DynamicResidualMixerUnit,
        DynamicSecondCentrifugeUnit,
    )

    preview = run.pathway_preview
    if preview is None:
        raise ValueError(f"Dynamic scenario step '{run.time_label}' has no pathway preview.")
    source_adapter = _build_adapter_result_from_run(
        replace(config, create_biosteam_objects=False), run
    )
    records = {
        record.source_dynamic_stream_id: record for record in source_adapter.records
    }
    feed_record = dynamic_process_stream_to_adapter_record(
        preview.raw_press.inputs[0],
        config.basis_feed_kg_per_hr,
        scenario_id=config.scenario_id,
    )

    with _FLOWSHEET_LOCK:
        before_flowsheet = bst.main_flowsheet.get_flowsheet()
        before_registries = _flowsheet_registry_snapshot(before_flowsheet)
        flowsheet = bst.Flowsheet(
            f"greenhub_dynamic_shadow_system_{_safe_id(config.scenario_id)}_"
            f"{_safe_id(run.time_label)}"
        )
        try:
            with flowsheet:
                streams = {
                    "whole_feed": bst.Stream(
                        ID=feed_record.adapter_stream_id,
                        thermo=thermo,
                        units="kg/hr",
                        **feed_record.component_masses_kg_hr,
                    )
                }
                for stream_id, record in records.items():
                    streams[stream_id] = bst.Stream(
                        ID=record.adapter_stream_id,
                        thermo=thermo,
                    )

                prefix = f"dyn_{_safe_id(run.time_label)}"
                units = {
                    "raw_press": DynamicRawPressUnit(
                        f"{prefix}_raw_press",
                        ins=streams["whole_feed"],
                        outs=(
                            streams["press_cake"],
                            streams["brown_juice"],
                            streams["raw_press_unrecovered_process_mass"],
                        ),
                        thermo=thermo,
                        **_shadow_unit_target_kwargs(
                            records,
                            (
                                "press_cake",
                                "brown_juice",
                                "raw_press_unrecovered_process_mass",
                            ),
                        ),
                    ),
                    "first_centrifuge": DynamicFirstCentrifugeUnit(
                        f"{prefix}_first_centrifuge",
                        ins=streams["brown_juice"],
                        outs=(streams["clarified_juice"], streams["cell_debris"]),
                        thermo=thermo,
                        **_shadow_unit_target_kwargs(
                            records, ("clarified_juice", "cell_debris")
                        ),
                    ),
                    "protein_extraction": DynamicProteinExtractionUnit(
                        f"{prefix}_protein_extraction",
                        ins=streams["clarified_juice"],
                        outs=(
                            streams["protein_rich_phase"],
                            streams["extraction_supernatant"],
                        ),
                        thermo=thermo,
                        **_shadow_unit_target_kwargs(
                            records,
                            ("protein_rich_phase", "extraction_supernatant"),
                        ),
                    ),
                    "second_centrifuge": DynamicSecondCentrifugeUnit(
                        f"{prefix}_second_centrifuge",
                        ins=(
                            streams["protein_rich_phase"],
                            streams["extraction_supernatant"],
                        ),
                        outs=(
                            streams["wet_protein_cake"],
                            streams["final_supernatant"],
                        ),
                        thermo=thermo,
                        **_shadow_unit_target_kwargs(
                            records, ("wet_protein_cake", "final_supernatant")
                        ),
                    ),
                    "protein_dryer": DynamicProteinDryerUnit(
                        f"{prefix}_protein_dryer",
                        ins=streams["wet_protein_cake"],
                        outs=(
                            streams["dried_protein_product"],
                            streams["evaporated_water"],
                        ),
                        thermo=thermo,
                        **_shadow_unit_target_kwargs(
                            records, ("dried_protein_product", "evaporated_water")
                        ),
                    ),
                    "residual_mixer": DynamicResidualMixerUnit(
                        f"{prefix}_residual_mixer",
                        ins=(streams["cell_debris"], streams["final_supernatant"]),
                        outs=streams["biogas_feed_candidate"],
                        thermo=thermo,
                        **_shadow_unit_target_kwargs(
                            records, ("biogas_feed_candidate",)
                        ),
                    ),
                }
                system = bst.System.from_units(
                    ID=f"{prefix}_protein_shadow_sys",
                    units=tuple(units.values()),
                )
                system.simulate()
        finally:
            _unregister_isolated_flowsheet(flowsheet)
        after_flowsheet = bst.main_flowsheet.get_flowsheet()
        empirical_unchanged = (
            after_flowsheet is before_flowsheet
            and _flowsheet_registry_snapshot(after_flowsheet) == before_registries
        )

    placeholder = DynamicBioSTEAMShadowSystemBalance(
        input_component_mass_kg_hr=0.0,
        terminal_component_mass_kg_hr=0.0,
        exact_component_residual_kg_hr=0.0,
        component_residuals_kg_hr={},
        exact_component_identity_closes=False,
        adapter_full_mass_closes=False,
        adapter_metadata_identity_closes=False,
        all_unit_outputs_match_adapter_records=False,
        unit_balances=(),
        press_cake_boundary_valid=False,
        empirical_flowsheet_unchanged=empirical_unchanged,
        closes=False,
    )
    provisional = DynamicBioSTEAMShadowSystemResult(
        config=config,
        source_adapter=source_adapter,
        feed_record=feed_record,
        adapter_records=source_adapter.records,
        system=system,
        units=units,
        streams=streams,
        isolated_flowsheet=flowsheet,
        mass_balance=placeholder,
        warnings=tuple(
            dict.fromkeys(
                (*run.warnings, "target_output_units_do_not_own_scientific_calculations")
            )
        ),
        blockers=run.blockers,
        provenance={
            "mode": "target_output_shadow_system_report_only",
            "scientific_calculation_owner": "Greenhub.dynamic_process",
            "bioSTEAM_unit_role": "reproduce_validated_target_component_masses",
            "metadata_storage": "parallel_adapter_records_only",
            "press_cake_boundary": "external_system_output",
            "empirical_flowsheet_id_before": before_flowsheet.ID,
            "empirical_flowsheet_id_after": after_flowsheet.ID,
            "empirical_flowsheet_unchanged": empirical_unchanged,
            "isolated_flowsheet_registered_after_build": False,
            "model_overrides": [],
        },
        can_drive_shadow_system=False,
    )
    balance = validate_dynamic_biosteam_shadow_system(provisional)
    return replace(
        provisional,
        mass_balance=balance,
        can_drive_shadow_system=balance.closes and run.can_drive_proxy_preview,
    )


def _shadow_unit_target_kwargs(
    records: Mapping[str, DynamicBioSTEAMStreamRecord],
    output_ids: Sequence[str],
) -> dict[str, object]:
    selected = tuple(records[name] for name in output_ids)
    return {
        "target_output_component_masses": tuple(
            record.component_masses_kg_hr for record in selected
        ),
        "target_output_stream_ids": tuple(output_ids),
        "policy_id": "|".join(
            sorted({item for record in selected for item in record.policy_ids})
        ),
        "policy_status": "|".join(
            sorted({record.policy_status for record in selected})
        ),
        "evidence_classes": tuple(
            sorted({item for record in selected for item in record.evidence_classes})
        ),
        "warnings": tuple(
            dict.fromkeys(item for record in selected for item in record.warnings)
        ),
        "blockers": tuple(
            dict.fromkeys(item for record in selected for item in record.blockers)
        ),
        "provenance": {
            "source_dynamic_stream_ids": list(output_ids),
            "source_ids": sorted(
                {item for record in selected for item in record.source_ids}
            ),
            "record_ids": sorted(
                {item for record in selected for item in record.record_ids}
            ),
            "target_output_mode": True,
        },
    }


def _biosteam_stream_matches_record(
    stream: bst.Stream,
    record: DynamicBioSTEAMStreamRecord,
    tolerance_kg_hr: float,
) -> bool:
    return all(
        abs(float(stream.imass[name]) - mass) <= tolerance_kg_hr
        for name, mass in record.component_masses_kg_hr.items()
    ) and abs(float(stream.F_mass) - record.total_component_kg_hr) <= tolerance_kg_hr


def _stream_component_inventory(streams: Sequence[bst.Stream]) -> dict[str, float]:
    inventory: dict[str, float] = {}
    for stream in streams:
        for name in EXACT_BIOSTEAM_COMPONENTS:
            mass = float(stream.imass[name])
            if mass:
                inventory[name] = inventory.get(name, 0.0) + mass
    return inventory


def _flowsheet_registry_snapshot(
    flowsheet: bst.Flowsheet,
) -> tuple[tuple[tuple[str, int], ...], ...]:
    return tuple(
        tuple(sorted((item.ID, id(item)) for item in registry))
        for registry in flowsheet.registries
    )


def _build_adapter_result_from_run(
    config: DynamicBioSTEAMAdapterConfig,
    run: DynamicProteinScenarioRun,
    *,
    require_proxy_ready: bool = True,
) -> DynamicBioSTEAMAdapterResult:
    preview = run.pathway_preview
    if preview is None:
        raise ValueError(f"Dynamic scenario step '{run.time_label}' has no pathway preview.")
    if require_proxy_ready and not run.can_drive_proxy_preview and config.allow_proxy_preview:
        raise ValueError(f"Dynamic scenario step '{run.time_label}' cannot drive proxy preview.")
    if not config.allow_proxy_preview:
        raise ValueError("The current shadow adapter requires allow_proxy_preview=True.")

    records = dynamic_pathway_to_adapter_records(preview, config)
    flowsheet = None
    streams: dict[str, bst.Stream] = {}
    with _FLOWSHEET_LOCK:
        before_flowsheet = bst.main_flowsheet.get_flowsheet()
        before_streams = dict(bst.main_flowsheet.stream.data)
        if config.create_biosteam_objects:
            flowsheet = bst.Flowsheet(_shadow_flowsheet_id(config.scenario_id, run.time_label))
            try:
                with flowsheet:
                    for record in records:
                        stream = adapter_record_to_biosteam_stream(record)
                        streams[record.adapter_stream_id] = stream
            finally:
                _unregister_isolated_flowsheet(flowsheet)
        after_flowsheet = bst.main_flowsheet.get_flowsheet()
        after_streams = dict(bst.main_flowsheet.stream.data)
    empirical_unchanged = (
        after_flowsheet is before_flowsheet
        and before_streams.keys() == after_streams.keys()
        and all(before_streams[key] is after_streams[key] for key in before_streams)
    )
    records = tuple(
        replace(
            record,
            created_biosteam_stream_id=(
                record.adapter_stream_id if record.adapter_stream_id in streams else None
            ),
        )
        for record in records
    )
    placeholder = DynamicBioSTEAMMassBalance(
        basis_feed_kg_hr=config.basis_feed_kg_per_hr,
        final_output_mass_kg_hr=0.0,
        overall_residual_kg_hr=config.basis_feed_kg_per_hr,
        overall_closes=False,
        component_residuals_kg_hr={},
        metadata_residuals_kg_hr={},
        identity_closes=False,
        per_stream_component_residuals_kg_hr={},
        per_stream_component_masses_match=False,
        metadata_preserved_in_records=False,
        source_stream_masses_match=False,
        press_cake_boundary_valid=False,
        dried_protein_matches_source=False,
        evaporated_water_matches_source=False,
        empirical_flowsheet_unchanged=empirical_unchanged,
        closes=False,
    )
    provisional = DynamicBioSTEAMAdapterResult(
        config=config,
        source_run=run,
        records=records,
        biosteam_streams=streams,
        isolated_flowsheet=flowsheet,
        mass_balance=placeholder,
        future_unit_specs=dynamic_biosteam_unit_specs(),
        warnings=tuple(dict.fromkeys((*run.warnings, "validated_simulation_remains_disabled"))),
        blockers=run.blockers,
        provenance={
            "adapter_mode": ADAPTER_MODE,
            "source_policy_ids": dict(run.policy_ids),
            "source_record_ids": list(run.source_record_ids),
            "empirical_flowsheet_id_before": before_flowsheet.ID,
            "empirical_flowsheet_id_after": after_flowsheet.ID,
            "empirical_flowsheet_unchanged": empirical_unchanged,
            "isolated_flowsheet_registered_after_build": False,
            "metadata_forced_into_chemicals": False,
            "model_overrides": [],
        },
        can_drive_shadow_adapter=False,
    )
    balance = validate_dynamic_biosteam_adapter_result(provisional)
    return replace(
        provisional,
        mass_balance=balance,
        can_drive_shadow_adapter=balance.closes and run.can_drive_proxy_preview,
    )


def _pathway_units(preview: DynamicPathwayPreview) -> tuple[DynamicUnitResult, ...]:
    return (
        preview.raw_press,
        preview.first_centrifugation,
        preview.protein_extraction,
        preview.second_centrifugation,
        preview.drying,
        preview.biogas_mix_preparation,
    )


def _source_stream_lookup(preview: DynamicPathwayPreview) -> dict[str, DynamicProcessStream]:
    return {
        stream.stream_id: stream
        for unit in _pathway_units(preview)
        for stream in unit.outputs
    }


def _adapter_stream_id(time_label: str, stream_id: str) -> str:
    return f"dyn_{_safe_id(time_label)}_{_safe_id(stream_id)}"


def _shadow_flowsheet_id(scenario_id: str, time_label: str) -> str:
    return f"greenhub_dynamic_shadow_{_safe_id(scenario_id)}_{_safe_id(time_label)}"


def _safe_id(value: str) -> str:
    return re.sub(r"[^A-Za-z0-9_]", "_", value).strip("_")


def _unregister_isolated_flowsheet(flowsheet: bst.Flowsheet) -> None:
    registry = bst.Flowsheet.flowsheet.__dict__
    if registry.get(flowsheet.ID) is flowsheet and bst.main_flowsheet.get_flowsheet() is not flowsheet:
        registry.pop(flowsheet.ID, None)


def _trace_unit(unit: DynamicUnitResult | None) -> dict[str, tuple[str, ...] | str]:
    if unit is None:
        return {
            "policy_ids": (), "policy_status": "record_only", "evidence_classes": (),
            "source_ids": (), "record_ids": (),
        }
    policy = unit.applied_policy
    policy_ids = _collect_key_values(policy, {"policy_id"})
    source_ids = _collect_key_values(policy, {"source_id"})
    record_ids = _collect_key_values(policy, {"record_id", "parameter_id"})
    evidence = _collect_key_values(
        policy,
        {"evidence_class", "proxy_class", "field_evidence_class", "metadata_field_evidence_class"},
        include_mapping_values=True,
    )
    return {
        "policy_ids": tuple(sorted(policy_ids)),
        "policy_status": str(policy.get("status", unit.activation_status)),
        "evidence_classes": tuple(sorted(evidence)),
        "source_ids": tuple(sorted(source_ids)),
        "record_ids": tuple(sorted(record_ids)),
    }


def _collect_key_values(
    value: object,
    keys: set[str],
    *,
    include_mapping_values: bool = False,
) -> set[str]:
    found: set[str] = set()
    if isinstance(value, Mapping):
        for key, nested in value.items():
            if key in keys:
                if isinstance(nested, Mapping) and include_mapping_values:
                    found.update(str(item) for item in nested.values() if item not in (None, ""))
                elif isinstance(nested, (list, tuple, set)):
                    found.update(str(item) for item in nested if item not in (None, ""))
                elif nested not in (None, "") and not isinstance(nested, Mapping):
                    found.add(str(nested))
            found.update(_collect_key_values(nested, keys, include_mapping_values=include_mapping_values))
    elif isinstance(value, (list, tuple, set)):
        for nested in value:
            found.update(_collect_key_values(nested, keys, include_mapping_values=include_mapping_values))
    return found


def _sum_mappings(mappings: Sequence[Mapping[str, float]]) -> dict[str, float]:
    result: dict[str, float] = {}
    for mapping in mappings:
        for name, value in mapping.items():
            result[name] = result.get(name, 0.0) + float(value)
    return result


def _mapping_residuals(
    inputs: Mapping[str, float], outputs: Mapping[str, float]
) -> dict[str, float]:
    return {
        name: inputs.get(name, 0.0) - outputs.get(name, 0.0)
        for name in sorted(set(inputs) | set(outputs))
    }


def _record_report_common(record: DynamicBioSTEAMStreamRecord) -> dict[str, object]:
    return {
        "scenario_id": record.scenario_id,
        "time_label": record.time_label,
        "adapter_stream_id": record.adapter_stream_id,
        "source_dynamic_stream_id": record.source_dynamic_stream_id,
        "source_unit_id": record.source_unit_id,
        "stream_mass_kg_hr": record.stream_mass_kg_hr,
        "unassigned_mass_kg_hr": record.unassigned_mass_kg_hr,
        "policy_ids": "|".join(record.policy_ids),
        "evidence_class": "|".join(record.evidence_classes),
        "policy_status": record.policy_status,
        "source_id": "|".join(record.source_ids),
        "record_id": "|".join(record.record_ids),
        "warning": "|".join(record.warnings),
        "blocker": "|".join(record.blockers),
        "created_biosteam_stream_id": record.created_biosteam_stream_id or "",
    }


def _write_rows(path: Path, fields: Sequence[str], rows: Sequence[Mapping[str, object]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)
