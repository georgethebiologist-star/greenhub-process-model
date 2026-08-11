"""Opt-in, report-only dynamic operational process previews.

The objects in this module are plain Python data structures. They do not create
BioSTEAM streams, mutate the empirical flowsheet, or connect to seasonal/API
services. Unsupported coefficients remain blockers; demo assumptions must be
requested explicitly.
"""

from __future__ import annotations

import csv
import json
from collections import Counter
from dataclasses import asdict, dataclass, field, replace
from enum import Enum
from math import isfinite
from pathlib import Path
from typing import Iterable, Mapping, Sequence

from Greenhub.dynamic_feedstock import (
    DynamicFeedstockInputBundle,
    DynamicFeedstockPoolPolicy,
    DynamicFeedstockPools,
    build_dynamic_feedstock_input_bundle,
    build_dynamic_feedstock_pools,
    default_literature_pool_policy,
)
from Greenhub.dynamic_press import DynamicPressPreviewBundle, build_dynamic_press_preview_bundle
from Greenhub.dynamic_unit_data import (
    DynamicUnitEvidence,
    load_ad_bmp_evidence,
    load_centrifuge_debris_capture_evidence,
    load_centrifuge_policy_evidence,
    load_direct_raw_press_evidence,
    load_drying_policy_evidence,
    load_isoelectric_recovery_evidence,
    load_lactic_acid_recovery_evidence,
    load_membrane_recovery_evidence,
    load_second_centrifuge_capture_evidence,
)
from Greenhub.mechanical_separation import (
    TotalSugarPartitionFallbackPolicy,
    WaterClosureCorrectionPolicy,
    load_press_partition_evidence,
)
from Greenhub.time_grid import (
    DEFAULT_SEASON_END,
    DEFAULT_SEASON_START,
    TimeGridStep,
    generate_time_grid,
)


SOLUBLE_SUGARS = ("Glucose", "Fructose", "Sucrose")
STRUCTURAL_FIBERS = ("Cellulose", "Hemicellulose", "Lignin")
PROTEIN_COMPONENTS = ("SolubleProtein", "SuspendedProtein")
MASS_TOLERANCE = 1e-12
BASELINE_TARGET_MOISTURE_FRACTION = 0.15
RESULTS_DIR = Path(__file__).resolve().parent / "results"
DEFAULT_RAW_PRESS_POLICY_ID = "raw_press_lolium_perenne_2025"
DEFAULT_FIRST_CENTRIFUGE_POLICY_ID = "centrifuge_alfalfa_raw_debris_3500g_proxy"
DEFAULT_SECOND_CENTRIFUGE_POLICY_ID = "second_centrifuge_prg_pH3_5_21000g"
SUPPORTED_RAW_PRESS_POLICY_IDS = frozenset({DEFAULT_RAW_PRESS_POLICY_ID})
SUPPORTED_FIRST_CENTRIFUGE_POLICY_IDS = frozenset({DEFAULT_FIRST_CENTRIFUGE_POLICY_ID})
SUPPORTED_SECOND_CENTRIFUGE_POLICY_IDS = frozenset({DEFAULT_SECOND_CENTRIFUGE_POLICY_ID})
GRID_OUTPUT_STREAM_IDS = (
    "press_cake",
    "brown_juice",
    "cell_debris",
    "clarified_juice",
    "wet_protein_cake",
    "dried_protein_product",
    "evaporated_water",
    "biogas_feed_candidate",
    "unrecovered_press_mass",
)


class ProteinExtractionMethod(str, Enum):
    """Mutually exclusive protein-recovery methods exposed by the backend."""

    ISOELECTRIC = "isoelectric"
    LACTIC_ACID = "lactic_acid"
    MEMBRANE = "membrane"
    HEAT = "heat"
    GENERIC = "generic"


@dataclass(frozen=True)
class DynamicProcessStream:
    """JSON-safe process stream on a one-kilogram fresh-feed basis."""

    stream_id: str
    time_label: str
    kg_per_kg_feed: float
    component_masses_kg_per_kg_feed: dict[str, float]
    metadata_pools_kg_per_kg_feed: dict[str, float]
    source_unit: str
    destination_hint: str
    provenance: dict[str, object]
    warnings: tuple[str, ...] = ()
    can_enter_simulation: bool = False

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True)
class DynamicUnitPolicy:
    """Generic explicit component split policy used by low-level helpers."""

    policy_id: str = "blocked_no_policy"
    component_fractions_to_primary: dict[str, float] = field(default_factory=dict)
    metadata_fractions_to_primary: dict[str, float] = field(default_factory=dict)
    provenance: dict[str, object] = field(default_factory=dict)
    status: str = "blocked_missing_values"
    activation_status: str = "report_only_not_model_active"

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True)
class DynamicRawPressPolicy:
    """Explicit raw-press component routing, independent from benchmark yields."""

    policy_id: str = "blocked_no_raw_press_partition_policy"
    component_fractions_to_cake: dict[str, float] = field(default_factory=dict)
    component_fractions_to_juice: dict[str, float] = field(default_factory=dict)
    metadata_fractions_to_cake: dict[str, float] = field(default_factory=dict)
    metadata_fractions_to_juice: dict[str, float] = field(default_factory=dict)
    press_cake_mass_yield_fraction: float | None = None
    brown_juice_mass_yield_fraction: float | None = None
    recovered_mass_closure_fraction: float | None = None
    preserve_unrecovered_process_mass: bool = False
    provenance: dict[str, object] = field(default_factory=dict)
    blockers: tuple[str, ...] = ()
    warnings: tuple[str, ...] = ()
    proxy_class: str = "none"
    proxy_enabled: bool = False
    partial_unmapped_allowed: bool = False
    status: str = "blocked_missing_values"
    activation_status: str = "report_only_not_model_active"

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True)
class DynamicCentrifugationPolicy:
    """First-centrifuge component capture policy."""

    policy_id: str = "blocked_no_first_centrifuge_policy"
    suspended_solids_removal_fraction: float | None = None
    suspended_protein_removal_fraction: float | None = None
    cell_debris_capture_fraction: float | None = None
    soluble_protein_loss_fraction: float | None = None
    sugar_loss_fraction: float | None = None
    ash_loss_fraction: float | None = None
    water_split_to_debris_fraction: float | None = None
    debris_wet_mass_fraction_of_feed_juice: float | None = None
    debris_dry_matter_fraction: float | None = None
    provenance: dict[str, object] = field(default_factory=dict)
    blockers: tuple[str, ...] = ()
    warnings: tuple[str, ...] = ()
    proxy_class: str = "none"
    proxy_enabled: bool = False
    can_drive_proxy_preview: bool = False
    status: str = "blocked_missing_values"
    activation_status: str = "report_only_not_model_active"

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True)
class DynamicProteinExtractionPolicy:
    """Clarified-juice protein extraction policy."""

    policy_id: str = "blocked_no_protein_extraction_policy"
    method: str = "generic"
    soluble_protein_recovery_fraction: float | None = None
    co_precipitated_ash_fraction: float | None = None
    co_precipitated_sugar_fraction: float | None = None
    water_to_protein_phase_fraction: float | None = None
    pH: float | None = None
    acid_demand_metadata: dict[str, object] = field(default_factory=dict)
    method_metadata: dict[str, object] = field(default_factory=dict)
    provenance: dict[str, object] = field(default_factory=dict)
    blockers: tuple[str, ...] = ()
    warnings: tuple[str, ...] = ()
    proxy_class: str = "none"
    proxy_enabled: bool = False
    can_drive_proxy_preview: bool = False
    status: str = "blocked_missing_values"
    activation_status: str = "report_only_not_model_active"

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True)
class DynamicRecoveryCentrifugationPolicy:
    """Second-centrifuge recovery policy for a protein-rich phase."""

    policy_id: str = "blocked_no_recovery_centrifuge_policy"
    protein_phase_capture_fraction: float | None = None
    soluble_protein_loss_to_supernatant_fraction: float | None = None
    water_retention_in_cake_fraction: float | None = None
    ash_retention_in_cake_fraction: float | None = None
    target_wet_cake_moisture_fraction: float | None = None
    combined_recovery_lower_bound: float | None = None
    provenance: dict[str, object] = field(default_factory=dict)
    blockers: tuple[str, ...] = ()
    warnings: tuple[str, ...] = ()
    proxy_class: str = "none"
    proxy_enabled: bool = False
    can_drive_proxy_preview: bool = False
    status: str = "blocked_missing_values"
    activation_status: str = "report_only_not_model_active"

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True)
class DynamicDryingPolicy:
    """Wet protein cake drying policy."""

    policy_id: str = "blocked_no_drying_policy"
    target_moisture_fraction: float | None = None
    water_removal_fraction: float | None = None
    drying_energy_kwh_per_kg_water: float | None = None
    provenance: dict[str, object] = field(default_factory=dict)
    blockers: tuple[str, ...] = ()
    warnings: tuple[str, ...] = ()
    proxy_class: str = "none"
    proxy_enabled: bool = False
    can_drive_proxy_preview: bool = False
    status: str = "blocked_missing_values"
    activation_status: str = "report_only_not_model_active"

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True)
class DynamicResidualBiogasPolicy:
    """BMP evidence metadata for supernatant/debris; no AD calculation."""

    policy_id: str = "blocked_no_residual_bmp_policy"
    bmp_m3_ch4_per_kg_vs: float | None = None
    bmp_basis: str = "VS basis"
    applicable_stream: str = "final_supernatant_only"
    residual_vs_estimation_policy: str = "blocked_no_vs_policy"
    include_residual_unallocated_dry_matter_as_vs: bool = False
    provenance: dict[str, object] = field(default_factory=dict)
    blockers: tuple[str, ...] = ()
    warnings: tuple[str, ...] = ()
    proxy_class: str = "none"
    proxy_enabled: bool = False
    status: str = "blocked_missing_values"
    activation_status: str = "report_only_not_model_active"

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True)
class DynamicProxyClosurePolicy:
    """Explicit engineering fallbacks used only to close a proxy preview."""

    policy_id: str
    raw_press_component_fractions_to_cake: dict[str, float]
    raw_press_metadata_fractions_to_cake: dict[str, float]
    suspended_solids_capture_fraction: float
    suspended_protein_capture_fraction: float
    cell_debris_capture_fraction: float
    water_split_to_debris_fraction: float
    sugar_loss_fraction: float
    ash_loss_fraction: float
    extraction_water_to_protein_phase_fraction: float
    extraction_ash_to_protein_phase_fraction: float
    extraction_sugar_to_protein_phase_fraction: float
    protein_phase_capture_fraction: float
    soluble_protein_loss_to_supernatant_fraction: float
    water_retention_in_cake_fraction: float
    ash_retention_in_cake_fraction: float
    target_moisture_fraction: float
    target_moisture_evidence_class: str
    drying_energy_kwh_per_kg_water: float | None
    residual_vs_estimation_policy: str
    include_residual_unallocated_dry_matter_as_vs: bool
    bmp_parameter_id: str = "BMP_DFOS_VS"
    evidence_class: str = "engineering_proxy_closure"
    status: str = "proxy_enabled_report_only"
    warnings: tuple[str, ...] = (
        "ENGINEERING PROXY CLOSURE: values are not measured or literature validated",
    )
    provenance: dict[str, object] = field(default_factory=dict)
    activation_status: str = "report_only_not_model_active"

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True)
class DynamicUnitResult:
    """Inputs, outputs, policy decisions, and balance for one preview unit."""

    unit_id: str
    unit_type: str
    time_label: str
    inputs: tuple[DynamicProcessStream, ...]
    outputs: tuple[DynamicProcessStream, ...]
    applied_policy: dict[str, object]
    blockers: tuple[str, ...]
    warnings: tuple[str, ...]
    mass_balance_summary: dict[str, object]
    readiness_flags: dict[str, bool]
    metrics: dict[str, object] = field(default_factory=dict)
    activation_status: str = "report_only_not_model_active"

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True)
class DynamicOperationalScenario:
    """All explicit policies for one operational pathway preview."""

    scenario_id: str
    scenario_name: str
    raw_press_policy: DynamicRawPressPolicy | None = None
    first_centrifugation_policy: DynamicCentrifugationPolicy | None = None
    protein_extraction_policy: DynamicProteinExtractionPolicy | None = None
    second_centrifugation_policy: DynamicRecoveryCentrifugationPolicy | None = None
    drying_policy: DynamicDryingPolicy | None = None
    residual_biogas_policy: DynamicResidualBiogasPolicy | None = None
    include_press_cake_in_biogas_mix: bool = False
    is_demo: bool = False
    provenance: dict[str, object] = field(default_factory=dict)
    activation_status: str = "report_only_not_model_active"

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True)
class DynamicPathwayPreview:
    """Complete or partial baseline pathway with every unit result retained."""

    time_label: str
    scenario: DynamicOperationalScenario
    feedstock_bundle: DynamicFeedstockInputBundle
    feed_pools: DynamicFeedstockPools
    dynamic_press_bundle: DynamicPressPreviewBundle
    raw_press: DynamicUnitResult
    first_centrifugation: DynamicUnitResult
    protein_extraction: DynamicUnitResult
    second_centrifugation: DynamicUnitResult
    drying: DynamicUnitResult
    biogas_mix_preparation: DynamicUnitResult
    final_outputs: tuple[DynamicProcessStream, ...]
    blockers: tuple[str, ...]
    warnings: tuple[str, ...]
    mass_balance_summary: dict[str, object]
    selected_method: str = ProteinExtractionMethod.ISOELECTRIC.value
    method_policy: dict[str, object] = field(default_factory=dict)
    method_alternatives_available: tuple[str, ...] = ()
    inactive_alternative_methods: tuple[str, ...] = ()
    active_unit_sequence: tuple[str, ...] = ()
    system_outputs: dict[str, object] = field(default_factory=dict)
    proxy_warnings: tuple[str, ...] = ()
    provenance: dict[str, object] = field(default_factory=dict)
    can_drive_proxy_preview: bool = False
    validated_simulation_ready: bool = False
    can_drive_simulation: bool = False
    activation_status: str = "report_only_not_model_active"

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True)
class DynamicProteinScenarioConfig:
    """Typed inputs for one opt-in grid-level protein-pathway scenario."""

    scenario_id: str = "proxy_protein_monthly_baseline"
    start_date: str = DEFAULT_SEASON_START
    end_date: str = DEFAULT_SEASON_END
    time_step: str = "monthly"
    protein_method: str = ProteinExtractionMethod.ISOELECTRIC.value
    raw_press_policy_id: str = DEFAULT_RAW_PRESS_POLICY_ID
    first_centrifuge_policy_id: str = DEFAULT_FIRST_CENTRIFUGE_POLICY_ID
    second_centrifuge_policy_id: str = DEFAULT_SECOND_CENTRIFUGE_POLICY_ID
    drying_target_moisture_fraction: float = BASELINE_TARGET_MOISTURE_FRACTION
    include_press_cake_in_biogas: bool = False
    external_scope_override: bool = False
    allow_proxy: bool = True
    allow_engineering_proxy_closure: bool = True
    allow_n_to_protein_proxy: bool = True
    notes: str = ""
    provenance: dict[str, object] = field(default_factory=dict)

    def __post_init__(self) -> None:
        _validate_dynamic_protein_scenario_config(self)

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True)
class DynamicProteinScenarioRun:
    """Compact outputs and retained full preview for one independent time step."""

    scenario_id: str
    time_label: str
    selected_method: str
    policy_ids: dict[str, str]
    source_record_ids: tuple[str, ...]
    output_masses_kg_per_kg_feed: dict[str, float]
    protein_metrics_kg_per_kg_feed: dict[str, float]
    residual_metrics: dict[str, object]
    can_drive_proxy_preview: bool
    can_drive_simulation: bool
    validated_simulation_ready: bool
    warnings: tuple[str, ...]
    blockers: tuple[str, ...]
    provenance: dict[str, object]
    pathway_preview: DynamicPathwayPreview | None = field(default=None, repr=False)
    activation_status: str = "report_only_not_model_active"

    def to_dict(self, *, include_preview: bool = False) -> dict[str, object]:
        result = asdict(self)
        if not include_preview:
            result.pop("pathway_preview", None)
        return result


@dataclass(frozen=True)
class DynamicProteinScenarioGridResult:
    """All independent time-step runs and their normalized-feed aggregation."""

    config: DynamicProteinScenarioConfig
    time_grid: tuple[TimeGridStep, ...]
    runs: tuple[DynamicProteinScenarioRun, ...]
    total_output_masses_kg_per_kg_feed_steps: dict[str, float]
    average_output_masses_kg_per_kg_feed: dict[str, float]
    output_ranges_kg_per_kg_feed: dict[str, dict[str, float]]
    blocker_counts: dict[str, int]
    warning_counts: dict[str, int]
    policy_ids_used: tuple[str, ...]
    evidence_class_counts: dict[str, int]
    provenance: dict[str, object]
    activation_status: str = "report_only_not_model_active"

    def to_dict(self, *, include_previews: bool = False) -> dict[str, object]:
        return {
            "config": self.config.to_dict(),
            "time_grid": [step.to_dict() for step in self.time_grid],
            "runs": [run.to_dict(include_preview=include_previews) for run in self.runs],
            "total_output_masses_kg_per_kg_feed_steps": dict(
                self.total_output_masses_kg_per_kg_feed_steps
            ),
            "average_output_masses_kg_per_kg_feed": dict(
                self.average_output_masses_kg_per_kg_feed
            ),
            "output_ranges_kg_per_kg_feed": {
                name: dict(values) for name, values in self.output_ranges_kg_per_kg_feed.items()
            },
            "blocker_counts": dict(self.blocker_counts),
            "warning_counts": dict(self.warning_counts),
            "policy_ids_used": list(self.policy_ids_used),
            "evidence_class_counts": dict(self.evidence_class_counts),
            "provenance": dict(self.provenance),
            "activation_status": self.activation_status,
        }


def describe_dynamic_protein_extraction_methods() -> dict[str, dict[str, object]]:
    """Describe mutually exclusive backend methods without selecting one."""

    return {
        ProteinExtractionMethod.ISOELECTRIC.value: {
            "baseline": True,
            "active_by_default": True,
            "evidence_files": ["recovery.csv", "protein_losses.csv", "acid_base_demand.csv"],
            "routing_anchor": "REC-001 only with explicit N-to-protein proxy permission",
            "expected_outputs": ["protein_rich_phase", "extraction_supernatant"],
        },
        ProteinExtractionMethod.LACTIC_ACID.value: {
            "baseline": False,
            "active_by_default": False,
            "evidence_files": ["protein_recovery_response.csv", "fermentation_time_series.csv"],
            "routing_anchor": "PR-005 whole-plant alfalfa recovery proxy; clarified-juice basis missing",
            "expected_outputs": ["protein_rich_phase", "extraction_supernatant"],
        },
        ProteinExtractionMethod.MEMBRANE.value: {
            "baseline": False,
            "active_by_default": False,
            "evidence_files": ["rejection_data_by_component.csv", "flux_time_series.csv", "energy_data.csv"],
            "routing_anchor": "REJ-001 crude-protein apparent rejection proxy",
            "expected_outputs": ["protein_rich_retentate", "permeate_supernatant"],
        },
        ProteinExtractionMethod.HEAT.value: {
            "baseline": False,
            "active_by_default": False,
            "evidence_files": [],
            "routing_anchor": "blocked: no audited recovery dataset",
            "expected_outputs": ["protein_rich_phase", "extraction_supernatant"],
        },
        ProteinExtractionMethod.GENERIC.value: {
            "baseline": False,
            "active_by_default": False,
            "evidence_files": [],
            "routing_anchor": "caller-supplied policy only",
            "expected_outputs": ["protein_rich_phase", "extraction_supernatant"],
        },
    }


def default_proxy_closure_policy() -> DynamicProxyClosurePolicy:
    """Return explicit pre-existing demo assumptions as closure-only values."""

    return DynamicProxyClosurePolicy(
        policy_id="engineering_proxy_closure_v1",
        raw_press_component_fractions_to_cake={
            "Water": 0.15,
            "Ash": 0.50,
            "SolubleProtein": 0.10,
            "SuspendedProtein": 0.80,
            "Glucose": 0.10,
            "Fructose": 0.10,
            "Sucrose": 0.10,
            "Cellulose": 0.90,
            "Hemicellulose": 0.90,
            "Lignin": 0.90,
        },
        raw_press_metadata_fractions_to_cake={
            "fructan": 0.10,
            "residual_unallocated_dry_matter": 0.70,
        },
        suspended_solids_capture_fraction=0.95,
        suspended_protein_capture_fraction=0.95,
        cell_debris_capture_fraction=0.90,
        water_split_to_debris_fraction=0.02,
        sugar_loss_fraction=0.01,
        ash_loss_fraction=0.50,
        extraction_water_to_protein_phase_fraction=0.05,
        extraction_ash_to_protein_phase_fraction=0.05,
        extraction_sugar_to_protein_phase_fraction=0.0,
        protein_phase_capture_fraction=0.98,
        soluble_protein_loss_to_supernatant_fraction=0.02,
        water_retention_in_cake_fraction=0.20,
        ash_retention_in_cake_fraction=0.80,
        target_moisture_fraction=BASELINE_TARGET_MOISTURE_FRACTION,
        target_moisture_evidence_class="scenario_input_baseline",
        drying_energy_kwh_per_kg_water=None,
        residual_vs_estimation_policy="known_organic_component_sum",
        include_residual_unallocated_dry_matter_as_vs=True,
        provenance={
            "reason": "to close report-only proxy preview",
            "origin": "values previously isolated in demo_baseline_operational_policy",
            "source_id": "engineering_proxy_closure",
            "record_id": "engineering_proxy_closure_v1",
            "not_measured": True,
            "not_literature_validated": True,
            "empirical_model_modified": False,
            "model_overrides": [],
        },
    )


def build_direct_raw_press_policy(
    closure_policy: DynamicProxyClosurePolicy,
    *,
    allow_total_crude_protein_proxy: bool = True,
) -> DynamicRawPressPolicy:
    """Build the opt-in PRG raw-press policy without closing source losses."""

    evidence = load_direct_raw_press_evidence()
    required_ids = {
        "RAW_0001", "RAW_0002", "RAW_0003", "RAW_0010", "RAW_0011",
        "RAW_0012", "RAW_0013", "RAW_0014", "RAW_0015", "RAW_0016",
    }
    rows = {row.record_id: row for row in evidence.records if row.record_id in required_ids}
    missing = sorted(required_ids - set(rows))
    if missing:
        raise ValueError("Missing direct raw-press evidence records: " + ",".join(missing))
    values = {record_id: rows[record_id].normalized_value for record_id in required_ids}
    if any(value is None for value in values.values()):
        raise ValueError("Direct raw-press policy requires scalar RAW_0001-RAW_0016 records.")
    if not allow_total_crude_protein_proxy:
        raise ValueError(
            "The closed PRG raw-press policy requires explicit permission to use total crude "
            "protein for SolubleProtein and SuspendedProtein."
        )

    cake = dict(closure_policy.raw_press_component_fractions_to_cake)
    juice = {name: 1.0 - fraction for name, fraction in cake.items()}
    cake["Water"], juice["Water"] = values["RAW_0014"], values["RAW_0015"]
    for component in PROTEIN_COMPONENTS:
        cake[component], juice[component] = values["RAW_0012"], values["RAW_0013"]

    metadata_cake = dict(closure_policy.raw_press_metadata_fractions_to_cake)
    metadata_juice = {name: 1.0 - fraction for name, fraction in metadata_cake.items()}
    metadata_cake["residual_unallocated_dry_matter"] = values["RAW_0010"]
    metadata_juice["residual_unallocated_dry_matter"] = values["RAW_0011"]
    field_evidence = {
        name: (
            "direct_grass_source"
            if name == "Water"
            else "total_crude_protein_proxy_for_soluble_suspended_classes"
            if name in PROTEIN_COMPONENTS
            else "engineering_proxy_closure"
        )
        for name in cake
    }
    metadata_evidence = {
        "residual_unallocated_dry_matter": "direct_grass_source_bulk_dm_routing",
        "fructan": "engineering_proxy_closure",
    }
    source_closure = float(values["RAW_0003"])
    return DynamicRawPressPolicy(
        policy_id="raw_press_lolium_perenne_2025",
        component_fractions_to_cake=cake,
        component_fractions_to_juice=juice,
        metadata_fractions_to_cake=metadata_cake,
        metadata_fractions_to_juice=metadata_juice,
        press_cake_mass_yield_fraction=float(values["RAW_0001"]),
        brown_juice_mass_yield_fraction=float(values["RAW_0002"]),
        recovered_mass_closure_fraction=source_closure,
        preserve_unrecovered_process_mass=True,
        provenance={
            **_policy_provenance("raw_press_lolium_perenne_2025", rows.values()),
            "field_evidence_class": field_evidence,
            "metadata_field_evidence_class": metadata_evidence,
            "source_fresh_mass_yields": {
                "press_cake": values["RAW_0001"],
                "brown_juice": values["RAW_0002"],
                "recovered_closure": source_closure,
                "unrecovered": 1.0 - source_closure,
            },
            "source_water_closure": values["RAW_0016"],
            "source_dm_partition": {
                "press_cake": values["RAW_0010"],
                "brown_juice": values["RAW_0011"],
            },
            "source_protein_partition": {
                "press_cake": values["RAW_0012"],
                "brown_juice": values["RAW_0013"],
            },
            "engineering_closure": closure_policy.to_dict(),
            "model_overrides": [],
        },
        warnings=(
            "RAW_0001-RAW_0003 fresh-mass closure is preserved and not normalized",
            "RAW_0014-RAW_0016 water closure is preserved and not normalized",
            "PROXY: total crude protein partition is applied to both GreenHub protein classes",
            "engineering_proxy_closure remains for sugar, ash, and fiber-species routing",
            "source stream yields are reported benchmarks because dynamic feed DM may differ from source feed DM",
        ),
        proxy_class="mixed_direct_grass_source_and_engineering_proxy_closure",
        proxy_enabled=True,
        partial_unmapped_allowed=False,
        status="proxy_enabled_report_only_closed",
    )


def build_red_clover_raw_press_proxy_policy(
    closure_policy: DynamicProxyClosurePolicy,
) -> DynamicRawPressPolicy:
    """Build the optional red-clover raw-press proxy; never a default policy."""

    evidence = load_direct_raw_press_evidence()
    ids = {"RAW_0017", "RAW_0018", "RAW_0034", "RAW_0035", "RAW_0040", "RAW_0041", "RAW_0043", "RAW_0044", "RAW_0046", "RAW_0047", "RAW_0048"}
    rows = {row.record_id: row for row in evidence.records if row.record_id in ids}
    if ids - set(rows):
        raise ValueError("Red-clover raw-press evidence package is incomplete.")
    value = lambda record_id: float(rows[record_id].normalized_value)  # noqa: E731
    cake = dict(closure_policy.raw_press_component_fractions_to_cake)
    juice = {name: 1.0 - fraction for name, fraction in cake.items()}
    cake["Water"], juice["Water"] = value("RAW_0047"), value("RAW_0048")
    cake["Ash"], juice["Ash"] = value("RAW_0040"), value("RAW_0041")
    for component in PROTEIN_COMPONENTS:
        cake[component], juice[component] = value("RAW_0043"), value("RAW_0044")
    for component in SOLUBLE_SUGARS:
        juice[component] = value("RAW_0046")
        cake[component] = 0.0
    return DynamicRawPressPolicy(
        policy_id="raw_press_red_clover_cp_ash_sugar_proxy",
        component_fractions_to_cake=cake,
        component_fractions_to_juice=juice,
        metadata_fractions_to_cake=dict(closure_policy.raw_press_metadata_fractions_to_cake),
        metadata_fractions_to_juice={
            name: 1.0 - fraction
            for name, fraction in closure_policy.raw_press_metadata_fractions_to_cake.items()
        },
        press_cake_mass_yield_fraction=value("RAW_0017"),
        brown_juice_mass_yield_fraction=value("RAW_0018"),
        recovered_mass_closure_fraction=1.0,
        preserve_unrecovered_process_mass=True,
        provenance={
            **_policy_provenance("raw_press_red_clover_cp_ash_sugar_proxy", rows.values()),
            "field_evidence_class": "legume_proxy",
            "cake_sugar_partition_status": "not_determined_kept_unrecovered",
            "engineering_closure": closure_policy.to_dict(),
        },
        warnings=(
            "PROXY: red clover is a legume and not direct GreenHub grass evidence",
            "cake sugar was not determined; juice-side sugar release is not normalized",
            "red-clover water closure exceeds one and is preserved, not normalized",
        ),
        blockers=(
            "red_clover_water_closure_exceeds_one",
            "red_clover_cake_sugar_partition_not_determined",
        ),
        proxy_class="legume_proxy",
        proxy_enabled=True,
        status="proxy_enabled_report_only_optional",
    )


def select_dynamic_protein_extraction_method(
    method: str | ProteinExtractionMethod = ProteinExtractionMethod.ISOELECTRIC,
    *,
    allow_proxy: bool = False,
    allow_n_to_protein_proxy: bool = False,
) -> DynamicProteinExtractionPolicy:
    """Select exactly one method and return its independent policy object."""

    selected = _coerce_method(method)
    return build_dataset_protein_extraction_policy(
        method=selected.value,
        allow_proxy=allow_proxy,
        allow_n_to_protein_proxy=allow_n_to_protein_proxy,
    )


def build_dataset_first_centrifugation_policy(
    *,
    allow_proxy: bool = False,
    closure_policy: DynamicProxyClosurePolicy | None = None,
) -> DynamicCentrifugationPolicy:
    """Build the first-centrifuge policy from the audited alfalfa bound."""

    evidence = load_centrifuge_policy_evidence()
    cap = evidence.by_parameter_id("CAP-ALF-001")
    debris_evidence = load_centrifuge_debris_capture_evidence()
    wet_capture = debris_evidence.by_parameter_id("CEN_0011")
    sediment_dm = debris_evidence.by_parameter_id("CEN_0013")
    provenance = _policy_provenance("centrifuge", (cap,) if cap else ())
    if not allow_proxy or cap is None or cap.normalized_value is None:
        return DynamicCentrifugationPolicy(
            policy_id="dataset_first_centrifuge_strict_v1",
            provenance=provenance,
            blockers=("direct_greenhub_first_centrifuge_capture_missing",),
            warnings=("CAP-ALF-001_reported_not_applied",) if cap else (),
            status="blocked_strict_evidence_mode",
        )
    retention_lower_bound = cap.normalized_value
    if closure_policy is not None:
        if wet_capture is None or wet_capture.normalized_value is None:
            raise ValueError("CEN_0011 is required for the closed first-centrifuge proxy.")
        if sediment_dm is None or sediment_dm.normalized_value is None:
            raise ValueError("CEN_0013 is required for the closed first-centrifuge proxy.")
        return DynamicCentrifugationPolicy(
            policy_id="centrifuge_alfalfa_raw_debris_3500g_proxy",
            suspended_solids_removal_fraction=closure_policy.suspended_solids_capture_fraction,
            suspended_protein_removal_fraction=closure_policy.suspended_protein_capture_fraction,
            cell_debris_capture_fraction=closure_policy.cell_debris_capture_fraction,
            soluble_protein_loss_fraction=1.0 - retention_lower_bound,
            sugar_loss_fraction=closure_policy.sugar_loss_fraction,
            ash_loss_fraction=closure_policy.ash_loss_fraction,
            water_split_to_debris_fraction=closure_policy.water_split_to_debris_fraction,
            debris_wet_mass_fraction_of_feed_juice=wet_capture.normalized_value,
            debris_dry_matter_fraction=sediment_dm.normalized_value,
            provenance={
                **_policy_provenance(
                    "centrifuge_alfalfa_raw_debris_3500g_proxy",
                    tuple(row for row in (cap, wet_capture, sediment_dm) if row),
                ),
                "retention_lower_bound": retention_lower_bound,
                "derived_loss_upper_bound": 1.0 - retention_lower_bound,
                "field_evidence_class": {
                    "soluble_protein_loss_fraction": "proxy_scenario_bound",
                    "suspended_solids_removal_fraction": closure_policy.evidence_class,
                    "suspended_protein_removal_fraction": closure_policy.evidence_class,
                    "cell_debris_capture_fraction": closure_policy.evidence_class,
                    "sugar_loss_fraction": closure_policy.evidence_class,
                    "ash_loss_fraction": closure_policy.evidence_class,
                    "water_split_to_debris_fraction": closure_policy.evidence_class,
                    "debris_wet_mass_fraction_of_feed_juice": "legume_proxy",
                    "debris_dry_matter_fraction": "legume_proxy",
                },
                "engineering_closure": closure_policy.to_dict(),
            },
            warnings=(
                "PROXY: alfalfa green juice is not GreenHub brown juice",
                "PROXY: CAP-ALF-001 is a lower-bound retention result, not a point estimate",
                "PROXY: CEN_0011/CEN_0013 are B-class alfalfa raw-debris evidence",
                "CEN_0011 sediment contains green protein and fibre; it is not pure protein",
                *closure_policy.warnings,
            ),
            proxy_class="mixed_legume_proxy_and_engineering_proxy_closure",
            proxy_enabled=True,
            can_drive_proxy_preview=True,
            status="proxy_enabled_report_only_closed",
        )
    return DynamicCentrifugationPolicy(
        policy_id="dataset_first_centrifuge_alfalfa_proxy_v1",
        soluble_protein_loss_fraction=1.0 - retention_lower_bound,
        provenance={
            **provenance,
            "retention_lower_bound": retention_lower_bound,
            "derived_loss_upper_bound": 1.0 - retention_lower_bound,
            "bound_treatment": "scenario-bound complement; original >80% statement retained",
        },
        blockers=(
            "suspended_solids_capture_missing",
            "suspended_protein_capture_missing",
            "cell_debris_capture_missing",
            "water_and_solute_split_missing",
        ),
        warnings=(
            "PROXY: alfalfa green juice is not GreenHub brown juice",
            "PROXY: CAP-ALF-001 is a lower-bound retention result, not a point estimate",
        ),
        proxy_class="alfalfa_green_juice_retention_bound",
        proxy_enabled=True,
        can_drive_proxy_preview=False,
        status="proxy_enabled_report_only_partial",
    )


def build_proxy_raw_press_protein_policy(
    *,
    allow_proxy: bool = False,
) -> DynamicRawPressPolicy | None:
    """Map total protein with MSP_0150 while retaining all other unknown bulk."""

    evidence = load_press_partition_evidence()
    record = next((row for row in evidence.records if row.record_id == "MSP_0150"), None)
    if not allow_proxy or record is None or record.partition_fraction is None:
        return None
    juice_fraction = record.partition_fraction
    cake_fraction = 1.0 - juice_fraction
    trace = {
        "record_id": record.record_id,
        "source_id": record.source_id,
        "source_title": record.source_title,
        "doi_or_url": record.source_url_or_doi,
        "value": record.reported_value,
        "normalized_value": juice_fraction,
        "unit": record.reported_unit,
        "basis": record.basis,
        "proxy_class": "alfalfa_total_protein_to_greenhub_protein_classes",
        "transferability_to_greenhub": record.transferability_class,
        "original_material": record.species_or_feedstock,
        "original_process_boundary": record.process_boundary,
        "warning": "Not a validated GreenHub measurement; total protein does not resolve solubility classes.",
        "notes": record.notes,
    }
    return DynamicRawPressPolicy(
        policy_id="MSP_0150_total_protein_raw_press_proxy_v1",
        component_fractions_to_cake={
            "SolubleProtein": cake_fraction,
            "SuspendedProtein": cake_fraction,
        },
        provenance={
            "evidence": [trace],
            "evidence_record_ids": [record.record_id],
            "juice_protein_fraction": juice_fraction,
            "unmapped_components_remain_unresolved_bulk": True,
            "model_overrides": [],
        },
        blockers=("soluble_and_suspended_protein_partition_not_observed_separately",),
        warnings=(
            "PROXY: MSP_0150 alfalfa total-protein recovery is applied to both GreenHub protein classes",
            "PROXY: secondary-source total-protein evidence is not soluble-protein release validation",
        ),
        proxy_class="alfalfa_total_protein_proxy_for_solubility_classes",
        proxy_enabled=True,
        partial_unmapped_allowed=True,
        status="proxy_enabled_report_only_partial",
    )


def build_closed_proxy_raw_press_policy(
    closure_policy: DynamicProxyClosurePolicy,
) -> DynamicRawPressPolicy:
    """Build the closed preview using the direct PRG source boundary."""

    return build_direct_raw_press_policy(
        closure_policy,
        allow_total_crude_protein_proxy=True,
    )


def build_dataset_protein_extraction_policy(
    method: str = ProteinExtractionMethod.ISOELECTRIC.value,
    *,
    allow_proxy: bool = False,
    allow_n_to_protein_proxy: bool = False,
    closure_policy: DynamicProxyClosurePolicy | None = None,
) -> DynamicProteinExtractionPolicy:
    """Build one extraction policy; methods are never blended."""

    selected = _coerce_method(method)
    if selected is ProteinExtractionMethod.ISOELECTRIC:
        evidence = load_isoelectric_recovery_evidence()
        recovery = evidence.by_parameter_id("REC-001")
        loss = evidence.by_parameter_id("LOSS-001")
        target_ph = evidence.by_parameter_id("ABD-001")
        rows = tuple(row for row in (recovery, loss, target_ph) if row)
        provenance = _policy_provenance("isoelectric", rows)
        metadata = {
            "target_pH_range": target_ph.raw_value if target_ph else "",
            "non_precipitable_n_fraction": loss.normalized_value if loss else None,
            "non_precipitable_n_parameter_id": loss.parameter_id if loss else "",
            "acid_demand_status": "missing_not_inferred_from_target_pH",
        }
        if not (allow_proxy and allow_n_to_protein_proxy and recovery and recovery.normalized_value is not None):
            return DynamicProteinExtractionPolicy(
                policy_id="dataset_isoelectric_strict_v1",
                method=selected.value,
                method_metadata=metadata,
                provenance=provenance,
                blockers=("REC-001_is_nitrogen_basis_not_soluble_protein_recovery",),
                warnings=("REC-001_reported_not_applied",),
                status="blocked_requires_explicit_n_to_protein_proxy",
            )
        return _apply_extraction_closure(DynamicProteinExtractionPolicy(
            policy_id="dataset_isoelectric_n_proxy_v1",
            method=selected.value,
            soluble_protein_recovery_fraction=recovery.normalized_value,
            method_metadata=metadata,
            provenance=provenance,
            warnings=(
                "PROXY: REC-001 is precipitated nitrogen, not pure soluble-protein recovery",
                "PROXY: grass-clover cleared juice is not a validated GreenHub measurement",
                "acid_demand_missing_mass_routing_only",
            ),
            proxy_class="n_to_soluble_protein_recovery_proxy",
            proxy_enabled=True,
            can_drive_proxy_preview=True,
            status="proxy_enabled_report_only",
        ), closure_policy)

    if selected is ProteinExtractionMethod.LACTIC_ACID:
        evidence = load_lactic_acid_recovery_evidence()
        recovery = evidence.by_parameter_id("PR-005")
        provenance = _policy_provenance("lactic_acid", (recovery,) if recovery else ())
        if not allow_proxy or recovery is None or recovery.normalized_value is None:
            return DynamicProteinExtractionPolicy(
                policy_id="dataset_lactic_acid_strict_v1",
                method=selected.value,
                provenance=provenance,
                blockers=("clarified_juice_protein_recovery_missing",),
                warnings=("PR-005_reported_as_alternative_not_applied",) if recovery else (),
                status="blocked_wrong_recovery_basis",
            )
        return _apply_extraction_closure(DynamicProteinExtractionPolicy(
            policy_id="dataset_lactic_acid_plant_basis_proxy_v1",
            method=selected.value,
            soluble_protein_recovery_fraction=recovery.normalized_value,
            method_metadata={"recovery_basis": recovery.basis, "fermentation_route_active": True},
            provenance=provenance,
            warnings=(
                "PROXY: PR-005 is alfalfa whole-plant protein recovery, not clarified-juice recovery",
                "fermentation_kinetics_and_carbon_demand_not_activated",
            ),
            proxy_class="alfalfa_whole_plant_recovery_proxy",
            proxy_enabled=True,
            can_drive_proxy_preview=True,
            status="proxy_enabled_report_only_scenario_bound",
        ), closure_policy)

    if selected is ProteinExtractionMethod.MEMBRANE:
        evidence = load_membrane_recovery_evidence()
        rejection = evidence.by_parameter_id("REJ-001")
        provenance = _policy_provenance("membrane", (rejection,) if rejection else ())
        if not allow_proxy or rejection is None or rejection.normalized_value is None:
            return DynamicProteinExtractionPolicy(
                policy_id="dataset_membrane_strict_v1",
                method=selected.value,
                provenance=provenance,
                blockers=("soluble_protein_species_recovery_missing",),
                warnings=("REJ-001_crude_protein_rejection_reported_not_applied",) if rejection else (),
                status="blocked_requires_rejection_proxy",
            )
        return _apply_extraction_closure(DynamicProteinExtractionPolicy(
            policy_id="dataset_membrane_cp_rejection_proxy_v1",
            method=selected.value,
            soluble_protein_recovery_fraction=rejection.normalized_value,
            method_metadata={
                "apparent_rejection": rejection.normalized_value,
                "sugar_transmission_status": "missing",
                "energy_status": "missing",
            },
            provenance=provenance,
            warnings=(
                "PROXY: REJ-001 crude-protein rejection is used as soluble-protein retention",
                "PROXY: apparent rejection is not measured retentate mass recovery",
                "membrane_flux_energy_and_species_transmission_not_resolved",
            ),
            proxy_class="clover_grass_crude_protein_rejection_proxy",
            proxy_enabled=True,
            can_drive_proxy_preview=True,
            status="proxy_enabled_report_only",
        ), closure_policy)

    return DynamicProteinExtractionPolicy(
        policy_id=f"dataset_{selected.value}_blocked_v1",
        method=selected.value,
        blockers=(f"no_audited_{selected.value}_recovery_value",),
        status="blocked_missing_dataset",
    )


def _apply_extraction_closure(
    policy: DynamicProteinExtractionPolicy,
    closure_policy: DynamicProxyClosurePolicy | None,
) -> DynamicProteinExtractionPolicy:
    if closure_policy is None:
        return policy
    return replace(
        policy,
        co_precipitated_ash_fraction=closure_policy.extraction_ash_to_protein_phase_fraction,
        co_precipitated_sugar_fraction=closure_policy.extraction_sugar_to_protein_phase_fraction,
        water_to_protein_phase_fraction=closure_policy.extraction_water_to_protein_phase_fraction,
        provenance={
            **policy.provenance,
            "field_evidence_class": {
                "soluble_protein_recovery_fraction": policy.proxy_class,
                "co_precipitated_ash_fraction": closure_policy.evidence_class,
                "co_precipitated_sugar_fraction": closure_policy.evidence_class,
                "water_to_protein_phase_fraction": closure_policy.evidence_class,
            },
            "engineering_closure": closure_policy.to_dict(),
        },
        warnings=tuple(dict.fromkeys((*policy.warnings, *closure_policy.warnings))),
        proxy_class="mixed_source_proxy_and_engineering_proxy_closure",
        status="proxy_enabled_report_only_closed",
    )


def build_dataset_second_centrifugation_policy(
    *,
    allow_proxy: bool = False,
    closure_policy: DynamicProxyClosurePolicy | None = None,
    allow_combined_recovery_envelope: bool = False,
) -> DynamicRecoveryCentrifugationPolicy:
    """Keep precipitate capture and wet-cake water blocked when absent."""

    evidence = load_isoelectric_recovery_evidence()
    capture = evidence.by_parameter_id("SEP-M01")
    moisture = evidence.by_parameter_id("MOI-M01")
    if allow_proxy and closure_policy is not None:
        second_evidence = load_second_centrifuge_capture_evidence()
        direct_moisture = second_evidence.by_parameter_id("PCEN_0003")
        recovery_envelope = second_evidence.by_parameter_id("PCEN_0010")
        if direct_moisture is None or direct_moisture.normalized_value is None:
            raise ValueError("PCEN_0003 is required for closed second-centrifuge cake moisture.")
        combined_lower_bound = 0.90 if allow_combined_recovery_envelope and recovery_envelope else None
        return DynamicRecoveryCentrifugationPolicy(
            policy_id="second_centrifuge_prg_pH3_5_21000g",
            protein_phase_capture_fraction=closure_policy.protein_phase_capture_fraction,
            soluble_protein_loss_to_supernatant_fraction=closure_policy.soluble_protein_loss_to_supernatant_fraction,
            water_retention_in_cake_fraction=closure_policy.water_retention_in_cake_fraction,
            ash_retention_in_cake_fraction=closure_policy.ash_retention_in_cake_fraction,
            target_wet_cake_moisture_fraction=direct_moisture.normalized_value,
            combined_recovery_lower_bound=combined_lower_bound,
            provenance={
                **_policy_provenance(
                    "second_centrifuge_prg_pH3_5_21000g",
                    tuple(
                        row
                        for row in (direct_moisture, recovery_envelope)
                        if row
                    ),
                ),
                "field_evidence_class": {
                    "protein_phase_capture_fraction": closure_policy.evidence_class,
                    "soluble_protein_loss_to_supernatant_fraction": closure_policy.evidence_class,
                    "water_retention_in_cake_fraction": "superseded_by_direct_wet_cake_moisture",
                    "target_wet_cake_moisture_fraction": "direct_grass_source",
                    "ash_retention_in_cake_fraction": closure_policy.evidence_class,
                    "combined_recovery_lower_bound": (
                        "source_lower_bound"
                    ),
                },
                "PCEN_0010_interpretation": (
                    "0.90 conservative lower bound for combined precipitation plus centrifugation; "
                    "not used as pure centrifuge capture"
                    if combined_lower_bound is not None
                    else "available but inactive; explicit opt-in required"
                ),
                "engineering_closure": closure_policy.to_dict(),
            },
            warnings=(
                "PCEN_0003 direct PRG wet-cake moisture applied for pH 3.5 route",
                "engineering proxy closure remains for centrifuge-only protein and ash capture",
                *(("PCEN_0010 0.90 is a combined-route lower bound, not pure centrifuge capture",) if combined_lower_bound is not None else ()),
            ),
            proxy_class="mixed_direct_grass_source_and_engineering_proxy_closure",
            proxy_enabled=True,
            can_drive_proxy_preview=True,
            status="proxy_enabled_report_only_closed",
        )
    return DynamicRecoveryCentrifugationPolicy(
        policy_id="dataset_second_centrifuge_blocked_v1",
        provenance=_policy_provenance("isoelectric_second_separation", tuple(row for row in (capture, moisture) if row)),
        blockers=("precipitated_protein_capture_missing", "wet_cake_moisture_missing"),
        warnings=(
            "no compatible proxy applied: precipitation recovery is not separator capture",
            "allow_proxy does not authorize invention of cake water split",
        ) if allow_proxy else (),
        proxy_enabled=allow_proxy,
        status="blocked_missing_source_values",
    )


def build_dataset_drying_policy(
    *,
    allow_proxy: bool = False,
    closure_policy: DynamicProxyClosurePolicy | None = None,
) -> DynamicDryingPolicy:
    """Build a drying policy; envelopes never become target moisture values."""

    evidence = load_drying_policy_evidence()
    target_rows = tuple(
        row for row in evidence.records
        if row.python_variable in {"outlet_moisture", "residual_moisture", "grass_outlet_moisture"}
    )
    if allow_proxy and closure_policy is not None:
        blockers = ()
        warnings = list(closure_policy.warnings)
        if closure_policy.drying_energy_kwh_per_kg_water is None:
            warnings.append("drying_energy_missing")
        return DynamicDryingPolicy(
            policy_id="dataset_protein_drying_closed_proxy_v1",
            target_moisture_fraction=closure_policy.target_moisture_fraction,
            drying_energy_kwh_per_kg_water=closure_policy.drying_energy_kwh_per_kg_water,
            provenance={
                **_policy_provenance("drying", target_rows),
                "field_evidence_class": {
                    "target_moisture_fraction": closure_policy.target_moisture_evidence_class,
                    "drying_energy_kwh_per_kg_water": (
                        closure_policy.evidence_class
                        if closure_policy.drying_energy_kwh_per_kg_water is not None
                        else "blocked_missing"
                    ),
                },
                "engineering_closure": closure_policy.to_dict(),
                "scenario_input": {
                    "field": "target_moisture_fraction",
                    "value": closure_policy.target_moisture_fraction,
                    "baseline_default": BASELINE_TARGET_MOISTURE_FRACTION,
                    "future_frontend_ready": True,
                    "evidence_class": closure_policy.target_moisture_evidence_class,
                },
            },
            blockers=blockers,
            warnings=tuple(warnings),
            proxy_class="scenario_input_baseline_with_missing_energy",
            proxy_enabled=True,
            can_drive_proxy_preview=True,
            status="proxy_enabled_report_only_mass_closed",
        )
    return DynamicDryingPolicy(
        policy_id="dataset_protein_drying_blocked_v1",
        provenance=_policy_provenance("drying", target_rows),
        blockers=("target_product_moisture_missing", "drying_energy_missing"),
        warnings=(
            "proxy operating-temperature envelopes are not product-moisture targets",
            "no source-backed target moisture or specific energy was applied",
        ) if allow_proxy else (),
        proxy_enabled=allow_proxy,
        status="blocked_missing_source_values",
    )


def build_dataset_residual_biogas_policy(
    *,
    allow_proxy: bool = False,
    closure_policy: DynamicProxyClosurePolicy | None = None,
) -> DynamicResidualBiogasPolicy:
    """Attach de-FOS whey BMP only to a supernatant-like residual preview."""

    evidence = load_ad_bmp_evidence()
    bmp = evidence.by_parameter_id("BMP_DFOS_VS")
    provenance = _policy_provenance("residual_biogas", (bmp,) if bmp else ())
    if not allow_proxy or bmp is None or bmp.normalized_value is None:
        return DynamicResidualBiogasPolicy(
            policy_id="dataset_residual_bmp_strict_v1",
            provenance=provenance,
            blockers=("greenhub_supernatant_BMP_missing", "residual_VS_missing"),
            warnings=("BMP_DFOS_VS_reported_not_applied",) if bmp else (),
            status="blocked_strict_evidence_mode",
        )
    closure_enabled = closure_policy is not None
    return DynamicResidualBiogasPolicy(
        policy_id="dataset_de_fos_whey_bmp_proxy_v1",
        bmp_m3_ch4_per_kg_vs=bmp.normalized_value,
        bmp_basis=bmp.normalized_unit,
        residual_vs_estimation_policy=(
            closure_policy.residual_vs_estimation_policy
            if closure_policy
            else "blocked_no_vs_policy"
        ),
        include_residual_unallocated_dry_matter_as_vs=bool(
            closure_policy and closure_policy.include_residual_unallocated_dry_matter_as_vs
        ),
        provenance={
            **provenance,
            **({
                "field_evidence_class": {
                    "residual_vs_estimation_policy": closure_policy.evidence_class,
                    "include_residual_unallocated_dry_matter_as_vs": closure_policy.evidence_class,
                    "bmp_m3_ch4_per_kg_vs": "proxy_usable",
                },
                "engineering_closure": closure_policy.to_dict(),
            } if closure_policy else {}),
        },
        blockers=(("AD_kinetics_not_implemented",) if closure_enabled else ("residual_VS_missing", "AD_kinetics_not_implemented")),
        warnings=(
            "PROXY: de-FOS grass whey BMP applies only to the supernatant-like fraction",
            "cell debris is combined by mass but has no assigned BMP",
            "press cake is excluded from the in-project AD boundary",
            *((closure_policy.warnings) if closure_policy else ()),
            *(("PROXY: residual unallocated dry matter counted as VS-like",) if closure_policy and closure_policy.include_residual_unallocated_dry_matter_as_vs else ()),
        ),
        proxy_class="de_fos_whey_for_supernatant_proxy",
        proxy_enabled=True,
        status="proxy_enabled_report_only_vs_closed" if closure_enabled else "proxy_enabled_report_only_metadata",
    )


def summarize_protein_method_alternatives() -> dict[str, dict[str, object]]:
    """Summarize strict and proxy readiness for each selectable method."""

    descriptions = describe_dynamic_protein_extraction_methods()
    summary: dict[str, dict[str, object]] = {}
    for method in ProteinExtractionMethod:
        strict = select_dynamic_protein_extraction_method(method, allow_proxy=False)
        proxy = select_dynamic_protein_extraction_method(
            method,
            allow_proxy=True,
            allow_n_to_protein_proxy=method is ProteinExtractionMethod.ISOELECTRIC,
        )
        summary[method.value] = {
            **descriptions[method.value],
            "strict_status": strict.status,
            "proxy_status": proxy.status,
            "required_missing_values": list(strict.blockers),
            "can_run_proxy_preview": proxy.can_drive_proxy_preview,
            "can_run_validated_simulation": False,
            "proxy_warnings": list(proxy.warnings),
        }
    return summary


def _coerce_method(method: str | ProteinExtractionMethod) -> ProteinExtractionMethod:
    try:
        return method if isinstance(method, ProteinExtractionMethod) else ProteinExtractionMethod(str(method))
    except ValueError as error:
        allowed = ", ".join(item.value for item in ProteinExtractionMethod)
        raise ValueError(f"Unsupported protein extraction method {method!r}; choose one of: {allowed}.") from error


def _policy_provenance(
    policy_area: str,
    rows: Iterable[DynamicUnitEvidence | None],
) -> dict[str, object]:
    evidence = [row for row in rows if row is not None]
    return {
        "policy_area": policy_area,
        "evidence": [_evidence_trace(row) for row in evidence],
        "evidence_record_ids": [row.parameter_id for row in evidence],
        "model_overrides": [],
        "empirical_model_modified": False,
    }


def _evidence_trace(row: DynamicUnitEvidence) -> dict[str, object]:
    return {
        "parameter_id": row.parameter_id,
        "record_id": row.record_id,
        "source_file": row.source_file,
        "value": row.raw_value,
        "normalized_value": row.normalized_value,
        "unit": row.unit,
        "normalized_unit": row.normalized_unit,
        "basis": row.basis,
        "proxy_class": row.proxy_class,
        "transferability_to_greenhub": row.transferability_to_greenhub,
        "source_id": row.source_id,
        "source_title": row.source_title,
        "doi_or_url": row.doi_or_url,
        "original_material": row.original_material,
        "original_process_boundary": row.original_process_boundary,
        "warning": "Not a validated GreenHub measurement" if "proxy" in row.evidence_class else "",
        "notes": row.notes,
    }


def validate_process_stream_mass_balance(
    stream: DynamicProcessStream,
    *,
    tolerance: float = MASS_TOLERANCE,
) -> dict[str, object]:
    """Validate nonnegative stream data and return its accounted-mass summary."""

    if not stream.stream_id:
        raise ValueError("DynamicProcessStream requires a stream_id.")
    if not isfinite(stream.kg_per_kg_feed) or stream.kg_per_kg_feed < -tolerance:
        raise ValueError(f"{stream.stream_id} has invalid total mass.")
    all_values = (*stream.component_masses_kg_per_kg_feed.values(), *stream.metadata_pools_kg_per_kg_feed.values())
    if any(not isfinite(value) or value < -tolerance for value in all_values):
        raise ValueError(f"{stream.stream_id} contains invalid component or metadata mass.")
    component_total = sum(stream.component_masses_kg_per_kg_feed.values())
    metadata_total = sum(stream.metadata_pools_kg_per_kg_feed.values())
    accounted = component_total + metadata_total
    residual = stream.kg_per_kg_feed - accounted
    if residual < -tolerance:
        raise ValueError(
            f"{stream.stream_id} accounted mass exceeds total by {-residual:.12g} kg/kg feed."
        )
    return {
        "stream_id": stream.stream_id,
        "total_mass_kg_per_kg_feed": stream.kg_per_kg_feed,
        "component_mass_kg_per_kg_feed": component_total,
        "metadata_pool_mass_kg_per_kg_feed": metadata_total,
        "accounted_mass_kg_per_kg_feed": accounted,
        "unaccounted_mass_kg_per_kg_feed": max(residual, 0.0),
        "closes": abs(residual) <= tolerance,
    }


def combine_process_streams(
    streams: Iterable[DynamicProcessStream],
    stream_id: str,
    destination_hint: str,
) -> DynamicProcessStream:
    """Combine streams by component and metadata identity without reaction."""

    items = tuple(streams)
    if not items:
        raise ValueError("At least one process stream is required for combination.")
    time_labels = {stream.time_label for stream in items}
    if len(time_labels) != 1:
        raise ValueError("Cannot combine process streams with different time labels.")
    components: dict[str, float] = {}
    metadata: dict[str, float] = {}
    for stream in items:
        validate_process_stream_mass_balance(stream)
        _accumulate(components, stream.component_masses_kg_per_kg_feed)
        _accumulate(metadata, stream.metadata_pools_kg_per_kg_feed)
    combined = DynamicProcessStream(
        stream_id=stream_id,
        time_label=items[0].time_label,
        kg_per_kg_feed=sum(stream.kg_per_kg_feed for stream in items),
        component_masses_kg_per_kg_feed=dict(sorted(components.items())),
        metadata_pools_kg_per_kg_feed=dict(sorted(metadata.items())),
        source_unit="stream_combiner",
        destination_hint=destination_hint,
        provenance={"combined_stream_ids": [stream.stream_id for stream in items]},
        warnings=tuple(dict.fromkeys(warning for stream in items for warning in stream.warnings)),
        can_enter_simulation=False,
    )
    validate_process_stream_mass_balance(combined)
    return combined


def move_component_fraction(
    input_stream: DynamicProcessStream,
    component: str,
    fraction: float,
    output_a: str,
    output_b: str,
) -> tuple[DynamicProcessStream, DynamicProcessStream]:
    """Split one selected component into two component-only streams."""

    _validate_fraction(fraction, f"{component} split fraction")
    mass = input_stream.component_masses_kg_per_kg_feed.get(component, 0.0)
    to_a = mass * fraction
    return (
        _new_stream(output_a, input_stream.time_label, {component: to_a}, {}, "component_mover", "preview"),
        _new_stream(output_b, input_stream.time_label, {component: mass - to_a}, {}, "component_mover", "preview"),
    )


def split_stream_by_component_policy(
    input_stream: DynamicProcessStream,
    policy: DynamicUnitPolicy,
    *,
    primary_stream_id: str = "primary_output",
    secondary_stream_id: str = "secondary_output",
    source_unit: str = "dynamic_component_splitter",
    primary_destination: str = "review",
    secondary_destination: str = "review",
) -> DynamicUnitResult:
    """Apply a fully explicit generic split; unspecified identities go secondary."""

    components = {
        name: _validated_or_zero(policy.component_fractions_to_primary.get(name), f"{name} fraction")
        for name in input_stream.component_masses_kg_per_kg_feed
    }
    metadata = {
        name: _validated_or_zero(policy.metadata_fractions_to_primary.get(name), f"{name} metadata fraction")
        for name in input_stream.metadata_pools_kg_per_kg_feed
    }
    primary, secondary = _partition_stream(
        input_stream,
        components,
        metadata,
        primary_stream_id,
        secondary_stream_id,
        source_unit,
        primary_destination,
        secondary_destination,
    )
    return _unit_result(
        source_unit,
        "generic_component_split",
        (input_stream,),
        (primary, secondary),
        policy.to_dict(),
        (),
        (),
        {"split_preview_ready": True},
    )


def build_raw_press_baseline_streams(
    dynamic_press_bundle: DynamicPressPreviewBundle,
    policy: DynamicRawPressPolicy | None = None,
) -> DynamicUnitResult:
    """Create raw-press outputs; explicit policies may retain a loss stream."""

    feed = _feed_stream_from_pools(dynamic_press_bundle.feed_pools)
    if policy is not None and policy.partial_unmapped_allowed:
        benchmark = build_raw_press_baseline_streams(dynamic_press_bundle, None)
        return _apply_partial_raw_press_policy(feed, benchmark, policy)
    blockers: list[str] = []
    warnings: list[str] = []
    if policy is not None:
        missing_components = sorted(
            set(feed.component_masses_kg_per_kg_feed) - set(policy.component_fractions_to_cake)
        )
        required_metadata = {
            name for name in feed.metadata_pools_kg_per_kg_feed if name != "hexose_subtotal"
        }
        missing_metadata = sorted(required_metadata - set(policy.metadata_fractions_to_cake))
        if missing_components:
            blockers.append("raw_press_missing_component_fractions:" + ",".join(missing_components))
        if missing_metadata:
            blockers.append("raw_press_missing_metadata_fractions:" + ",".join(missing_metadata))
        component_fractions = {
            name: _validated_or_zero(policy.component_fractions_to_cake.get(name), f"{name} cake fraction")
            for name in feed.component_masses_kg_per_kg_feed
        }
        metadata_fractions = {
            name: _validated_or_zero(policy.metadata_fractions_to_cake.get(name), f"{name} cake fraction")
            for name in feed.metadata_pools_kg_per_kg_feed
        }
        if policy.preserve_unrecovered_process_mass:
            component_juice_fractions = {
                name: _validated_or_zero(
                    policy.component_fractions_to_juice.get(
                        name,
                        1.0 - component_fractions[name],
                    ),
                    f"{name} juice fraction",
                )
                for name in feed.component_masses_kg_per_kg_feed
            }
            metadata_juice_fractions = {
                name: _validated_or_zero(
                    policy.metadata_fractions_to_juice.get(
                        name,
                        1.0 - metadata_fractions[name],
                    ),
                    f"{name} juice fraction",
                )
                for name in feed.metadata_pools_kg_per_kg_feed
            }
            routing_reconciliation: dict[str, object] = {}
            if (
                policy.press_cake_mass_yield_fraction is not None
                and policy.brown_juice_mass_yield_fraction is not None
            ):
                field_evidence = policy.provenance.get("field_evidence_class", {})
                metadata_evidence = policy.provenance.get("metadata_field_evidence_class", {})
                fixed_components = {
                    name
                    for name, evidence_class in field_evidence.items()
                    if evidence_class != "engineering_proxy_closure"
                }
                fixed_metadata = {
                    name
                    for name, evidence_class in metadata_evidence.items()
                    if evidence_class != "engineering_proxy_closure"
                }
                (
                    component_fractions,
                    component_juice_fractions,
                    metadata_fractions,
                    metadata_juice_fractions,
                    routing_reconciliation,
                ) = _reconcile_raw_press_to_source_stream_yields(
                    feed,
                    component_fractions,
                    component_juice_fractions,
                    metadata_fractions,
                    metadata_juice_fractions,
                    float(policy.press_cake_mass_yield_fraction),
                    float(policy.brown_juice_mass_yield_fraction),
                    fixed_components,
                    fixed_metadata,
                )
                warnings.append(
                    "engineering sugar/ash/fiber routing adjusted to source fresh-stream yields; direct partitions unchanged"
                )
            press_cake, brown_juice, unrecovered = _partition_stream_three_way(
                feed,
                component_fractions,
                component_juice_fractions,
                metadata_fractions,
                metadata_juice_fractions,
                "press_cake",
                "brown_juice",
                "raw_press_unrecovered_process_mass",
                "dynamic_raw_press",
            )
            outputs = (press_cake, brown_juice, unrecovered)
            source_yields = {
                "press_cake": policy.press_cake_mass_yield_fraction,
                "brown_juice": policy.brown_juice_mass_yield_fraction,
                "recovered_closure": policy.recovered_mass_closure_fraction,
                "unrecovered": (
                    None
                    if policy.recovered_mass_closure_fraction is None
                    else 1.0 - policy.recovered_mass_closure_fraction
                ),
            }
            warnings.append("unrecovered raw-press inventory retained as an explicit report-only stream")
        else:
            press_cake, brown_juice = _partition_stream(
                feed,
                component_fractions,
                metadata_fractions,
                "press_cake",
                "brown_juice",
                "dynamic_raw_press",
                "system_output_or_explicit_material_route",
                "first_centrifugation",
            )
            outputs = (press_cake, brown_juice)
            source_yields = {}
            routing_reconciliation = {}
        applied_policy = policy.to_dict()
    else:
        press_view = dynamic_press_bundle.press_cake
        juice_view = dynamic_press_bundle.brown_juice
        benchmark_view = dynamic_press_bundle.protein_concentrate
        cake_components = dict(press_view.component_masses_kg_per_kg_feed)
        cake_metadata = dict(press_view.metadata_pool_masses_kg_per_kg_feed)
        juice_components = dict(juice_view.component_masses_kg_per_kg_feed)
        _accumulate(juice_components, benchmark_view.component_masses_kg_per_kg_feed)
        juice_metadata = dict(juice_view.metadata_pool_masses_kg_per_kg_feed)
        _accumulate(juice_metadata, benchmark_view.metadata_pool_masses_kg_per_kg_feed)
        cake_unresolved = press_view.unassigned_stream_capacity_kg_per_kg_feed
        juice_unresolved = (
            juice_view.unassigned_stream_capacity_kg_per_kg_feed
            + benchmark_view.unassigned_stream_capacity_kg_per_kg_feed
        )
        if cake_unresolved > MASS_TOLERANCE:
            cake_metadata["unresolved_bulk_mass"] = cake_unresolved
        if juice_unresolved > MASS_TOLERANCE:
            juice_metadata["unresolved_bulk_mass"] = juice_unresolved
        press_cake = _new_stream(
            "press_cake",
            feed.time_label,
            cake_components,
            cake_metadata,
            "dynamic_raw_press_adapter",
            "system_output_or_explicit_material_route",
            provenance={
                "source_stream": "press_cake",
                "benchmark_boundary": dynamic_press_bundle.separation_policy.boundary_note,
            },
        )
        brown_juice = _new_stream(
            "brown_juice",
            feed.time_label,
            juice_components,
            juice_metadata,
            "dynamic_raw_press_adapter",
            "first_centrifugation",
            provenance={
                "source_streams_recombined": ["brown_juice", "protein_concentrate"],
                "protein_concentrate_active_raw_output": False,
                "benchmark_concentrate_mass_kg_per_kg_feed": benchmark_view.total_stream_mass_kg_per_kg_feed,
                "boundary_interpretation": "Recombined final liquid products to represent the pre-extraction raw juice precursor.",
            },
        )
        unresolved_components = dynamic_press_bundle.press_preview.unmapped_components
        if unresolved_components:
            blockers.append("raw_press_unmapped_components:" + ",".join(unresolved_components))
        blockers.extend(dynamic_press_bundle.blockers)
        warnings.append("source_protein_concentrate_recombined_as_benchmark_not_active_raw_output")
        applied_policy = {
            "policy_id": "source_boundary_recombination_preview",
            "status": "benchmark_derived_report_only",
            "protein_concentrate_active_raw_output": False,
        }
        outputs = (press_cake, brown_juice)
        source_yields = {}
        routing_reconciliation = {}
    result = _unit_result(
        "dynamic_raw_press",
        "raw_press_boundary_adapter",
        (feed,),
        outputs,
        applied_policy,
        tuple(dict.fromkeys(blockers)),
        tuple(warnings),
        {
            "two_stream_raw_boundary_created": len(outputs) == 2,
            "unrecovered_process_mass_explicit": len(outputs) == 3,
            "protein_concentrate_active_raw_output": False,
            "brown_juice_partition_ready": not blockers,
        },
        allow_unresolved_identity=policy is None,
        metrics={
            "source_fresh_mass_yields": source_yields,
            "calculated_dynamic_stream_masses": {
                stream.stream_id: stream.kg_per_kg_feed for stream in outputs
            },
            "source_yields_normalized": False,
            "engineering_routing_reconciliation": routing_reconciliation,
        },
    )
    return result


def _apply_partial_raw_press_policy(
    feed: DynamicProcessStream,
    benchmark: DynamicUnitResult,
    policy: DynamicRawPressPolicy,
) -> DynamicUnitResult:
    """Replace unresolved benchmark bulk with only explicitly mapped components."""

    cake = _output(benchmark, "press_cake")
    juice = _output(benchmark, "brown_juice")
    cake_components = dict(cake.component_masses_kg_per_kg_feed)
    juice_components = dict(juice.component_masses_kg_per_kg_feed)
    cake_metadata = dict(cake.metadata_pools_kg_per_kg_feed)
    juice_metadata = dict(juice.metadata_pools_kg_per_kg_feed)

    for component, cake_fraction in policy.component_fractions_to_cake.items():
        _validate_fraction(cake_fraction, f"{component} cake fraction")
        feed_mass = feed.component_masses_kg_per_kg_feed.get(component, 0.0)
        old_cake = cake_components.pop(component, 0.0)
        old_juice = juice_components.pop(component, 0.0)
        cake_metadata["unresolved_bulk_mass"] = cake_metadata.get("unresolved_bulk_mass", 0.0) + old_cake
        juice_metadata["unresolved_bulk_mass"] = juice_metadata.get("unresolved_bulk_mass", 0.0) + old_juice
        cake_mass = feed_mass * cake_fraction
        juice_mass = feed_mass - cake_mass
        if cake_metadata.get("unresolved_bulk_mass", 0.0) + MASS_TOLERANCE < cake_mass:
            raise ValueError(f"Partial raw-press policy exceeds press-cake unresolved capacity for {component}.")
        if juice_metadata.get("unresolved_bulk_mass", 0.0) + MASS_TOLERANCE < juice_mass:
            raise ValueError(f"Partial raw-press policy exceeds brown-juice unresolved capacity for {component}.")
        cake_metadata["unresolved_bulk_mass"] -= cake_mass
        juice_metadata["unresolved_bulk_mass"] -= juice_mass
        cake_components[component] = cake_mass
        juice_components[component] = juice_mass

    press_cake = _new_stream(
        "press_cake",
        feed.time_label,
        cake_components,
        cake_metadata,
        "dynamic_raw_press_proxy_adapter",
        "system_output_external_downstream_scope",
        provenance={**cake.provenance, **policy.provenance},
        warnings=policy.warnings,
    )
    brown_juice = _new_stream(
        "brown_juice",
        feed.time_label,
        juice_components,
        juice_metadata,
        "dynamic_raw_press_proxy_adapter",
        "first_centrifugation",
        provenance={**juice.provenance, **policy.provenance},
        warnings=policy.warnings,
    )
    return _unit_result(
        "dynamic_raw_press",
        "raw_press_boundary_adapter",
        (feed,),
        (press_cake, brown_juice),
        policy.to_dict(),
        (*benchmark.blockers, *policy.blockers),
        (*benchmark.warnings, *policy.warnings),
        {
            "two_stream_raw_boundary_created": True,
            "protein_concentrate_active_raw_output": False,
            "brown_juice_partition_ready": False,
            "partial_protein_proxy_applied": True,
        },
        allow_unresolved_identity=True,
    )


def preview_first_centrifugation(
    brown_juice_stream: DynamicProcessStream,
    policy: DynamicCentrifugationPolicy | None,
) -> DynamicUnitResult:
    """Separate particulate pools from brown juice without losing material."""

    blockers: list[str] = []
    warnings: list[str] = []
    if policy is None:
        blockers.append("first_centrifugation_policy_missing")
        clarified = _copy_stream(
            brown_juice_stream,
            "clarified_juice",
            "first_centrifugation",
            "protein_extraction",
            warning="first_centrifugation_not_applied",
        )
        debris = _empty_stream("cell_debris", brown_juice_stream.time_label, "first_centrifugation", "biogas_residual_mix")
        applied_policy = DynamicCentrifugationPolicy().to_dict()
    else:
        blockers.extend(policy.blockers)
        warnings.extend(policy.warnings)
        required = {
            "suspended_solids_removal_fraction": policy.suspended_solids_removal_fraction,
            "suspended_protein_removal_fraction": policy.suspended_protein_removal_fraction,
            "cell_debris_capture_fraction": policy.cell_debris_capture_fraction,
            "soluble_protein_loss_fraction": policy.soluble_protein_loss_fraction,
            "sugar_loss_fraction": policy.sugar_loss_fraction,
            "ash_loss_fraction": policy.ash_loss_fraction,
            "water_split_to_debris_fraction": policy.water_split_to_debris_fraction,
        }
        missing = [name for name, value in required.items() if value is None]
        blockers.extend(f"first_centrifugation_missing:{name}" for name in missing)
        values = {name: _validated_or_zero(value, name) for name, value in required.items()}
        if (
            policy.debris_wet_mass_fraction_of_feed_juice is not None
            and policy.debris_dry_matter_fraction is not None
        ):
            debris, clarified, source_target_metrics = _partition_first_centrifuge_to_source_targets(
                brown_juice_stream,
                values,
                policy.debris_wet_mass_fraction_of_feed_juice,
                policy.debris_dry_matter_fraction,
            )
            warnings.append(
                "CEN_0011/CEN_0013 set total sediment wet mass and DM; composition allocation remains proxy closure"
            )
        else:
            fractions: dict[str, float] = {}
            for component in brown_juice_stream.component_masses_kg_per_kg_feed:
                if component == "SuspendedProtein":
                    fractions[component] = values["suspended_protein_removal_fraction"]
                elif component == "SuspendedSolids":
                    fractions[component] = values["suspended_solids_removal_fraction"]
                elif component in STRUCTURAL_FIBERS:
                    fractions[component] = values["cell_debris_capture_fraction"]
                elif component == "SolubleProtein":
                    fractions[component] = values["soluble_protein_loss_fraction"]
                elif component in SOLUBLE_SUGARS:
                    fractions[component] = values["sugar_loss_fraction"]
                elif component == "Ash":
                    fractions[component] = values["ash_loss_fraction"]
                elif component == "Water":
                    fractions[component] = values["water_split_to_debris_fraction"]
                else:
                    fractions[component] = 0.0
            metadata_fractions = {
                name: (
                    values["sugar_loss_fraction"]
                    if name == "fructan"
                    else values["cell_debris_capture_fraction"]
                    if name == "residual_unallocated_dry_matter"
                    else 0.0
                )
                for name in brown_juice_stream.metadata_pools_kg_per_kg_feed
            }
            debris, clarified = _partition_stream(
                brown_juice_stream,
                fractions,
                metadata_fractions,
                "cell_debris",
                "clarified_juice",
                "first_centrifugation",
                "biogas_residual_mix",
                "protein_extraction",
            )
            source_target_metrics = {}
        applied_policy = policy.to_dict()
    return _unit_result(
        "first_centrifugation",
        "solid_liquid_centrifugation_preview",
        (brown_juice_stream,),
        (clarified, debris),
        applied_policy,
        tuple(blockers),
        tuple(warnings),
        {
            "mass_preview_ready": not blockers,
            "cell_debris_routed_to_biogas": True,
            "clarified_juice_ready_for_extraction": not blockers,
        },
        metrics=source_target_metrics if policy is not None else {},
    )


def _partition_first_centrifuge_to_source_targets(
    brown_juice: DynamicProcessStream,
    fractions: Mapping[str, float],
    wet_sediment_fraction: float,
    sediment_dm_fraction: float,
) -> tuple[DynamicProcessStream, DynamicProcessStream, dict[str, object]]:
    """Match source sediment wet mass/DM while retaining proxy composition weights."""

    _validate_fraction(wet_sediment_fraction, "wet sediment fraction")
    _validate_fraction(sediment_dm_fraction, "sediment dry matter fraction")
    target_wet = brown_juice.kg_per_kg_feed * wet_sediment_fraction
    target_dry = target_wet * sediment_dm_fraction
    target_water = target_wet - target_dry
    available_water = brown_juice.component_masses_kg_per_kg_feed.get("Water", 0.0)
    if target_water > available_water + MASS_TOLERANCE:
        raise ValueError("CEN_0011 wet sediment target requires more Water than brown juice contains.")

    desired_components: dict[str, float] = {}
    for component, mass in brown_juice.component_masses_kg_per_kg_feed.items():
        if component == "Water":
            continue
        if component == "SuspendedProtein":
            fraction = fractions["suspended_protein_removal_fraction"]
        elif component == "SuspendedSolids":
            fraction = fractions["suspended_solids_removal_fraction"]
        elif component in STRUCTURAL_FIBERS:
            fraction = fractions["cell_debris_capture_fraction"]
        elif component == "SolubleProtein":
            fraction = fractions["soluble_protein_loss_fraction"]
        elif component in SOLUBLE_SUGARS:
            fraction = fractions["sugar_loss_fraction"]
        elif component == "Ash":
            fraction = fractions["ash_loss_fraction"]
        else:
            fraction = 0.0
        desired_components[component] = mass * fraction
    desired_metadata = {
        name: mass * (
            fractions["sugar_loss_fraction"]
            if name == "fructan"
            else fractions["cell_debris_capture_fraction"]
            if name == "residual_unallocated_dry_matter"
            else 0.0
        )
        for name, mass in brown_juice.metadata_pools_kg_per_kg_feed.items()
    }
    desired_total = sum(desired_components.values()) + sum(desired_metadata.values())
    if desired_total <= MASS_TOLERANCE and target_dry > MASS_TOLERANCE:
        raise ValueError("CEN_0013 sediment DM cannot be allocated without component capture weights.")
    scale = 0.0 if desired_total <= MASS_TOLERANCE else target_dry / desired_total
    debris_components = {
        name: mass * scale for name, mass in desired_components.items()
    }
    debris_metadata = {
        name: mass * scale for name, mass in desired_metadata.items()
    }
    for name, captured in debris_components.items():
        if captured > brown_juice.component_masses_kg_per_kg_feed[name] + MASS_TOLERANCE:
            raise ValueError(f"CEN sediment DM target over-captures component {name}.")
    for name, captured in debris_metadata.items():
        if captured > brown_juice.metadata_pools_kg_per_kg_feed[name] + MASS_TOLERANCE:
            raise ValueError(f"CEN sediment DM target over-captures metadata pool {name}.")
    debris_components["Water"] = target_water
    clarified_components = {
        name: mass - debris_components.get(name, 0.0)
        for name, mass in brown_juice.component_masses_kg_per_kg_feed.items()
    }
    clarified_metadata = {
        name: mass - debris_metadata.get(name, 0.0)
        for name, mass in brown_juice.metadata_pools_kg_per_kg_feed.items()
    }
    provenance = {
        "wet_sediment_fraction": wet_sediment_fraction,
        "sediment_dm_fraction": sediment_dm_fraction,
        "composition_weight_scale": scale,
        "source_records": ["CEN_0011", "CEN_0013"],
        "evidence_class": "legume_proxy",
    }
    debris = _new_stream(
        "cell_debris",
        brown_juice.time_label,
        debris_components,
        debris_metadata,
        "first_centrifugation",
        "biogas_residual_mix",
        provenance=provenance,
    )
    clarified = _new_stream(
        "clarified_juice",
        brown_juice.time_label,
        clarified_components,
        clarified_metadata,
        "first_centrifugation",
        "protein_extraction",
        provenance=provenance,
    )
    return debris, clarified, {
        "source_wet_sediment_fraction": wet_sediment_fraction,
        "source_sediment_dm_fraction": sediment_dm_fraction,
        "cell_debris_wet_mass_kg_per_kg_feed": debris.kg_per_kg_feed,
        "cell_debris_dry_mass_kg_per_kg_feed": target_dry,
        "composition_weight_scale": scale,
        "evidence_class": "legume_proxy",
        "source_record_ids": ["CEN_0011", "CEN_0013"],
    }


def preview_protein_extraction(
    clarified_juice_stream: DynamicProcessStream,
    policy: DynamicProteinExtractionPolicy | None,
) -> DynamicUnitResult:
    """Recover soluble protein while retaining unrecovered solutes in liquid."""

    blockers: list[str] = []
    warnings: list[str] = []
    if policy is None:
        blockers.append("protein_extraction_policy_missing")
        protein_phase = _empty_stream("protein_rich_phase", clarified_juice_stream.time_label, "protein_extraction", "second_centrifugation")
        supernatant = _copy_stream(
            clarified_juice_stream,
            "extraction_supernatant",
            "protein_extraction",
            "second_centrifugation_then_biogas",
            warning="protein_extraction_not_applied",
        )
        applied_policy = DynamicProteinExtractionPolicy().to_dict()
    else:
        blockers.extend(policy.blockers)
        warnings.extend(policy.warnings)
        if policy.method not in {"isoelectric", "lactic_acid", "membrane", "heat", "generic"}:
            raise ValueError(f"Unsupported dynamic protein extraction method: {policy.method}.")
        if policy.soluble_protein_recovery_fraction is None:
            blockers.append("protein_extraction_missing:soluble_protein_recovery_fraction")
        recovery = _validated_or_zero(
            policy.soluble_protein_recovery_fraction,
            "soluble protein recovery fraction",
        )
        ash_fraction = _validated_or_zero(policy.co_precipitated_ash_fraction, "co-precipitated ash fraction")
        sugar_fraction = _validated_or_zero(policy.co_precipitated_sugar_fraction, "co-precipitated sugar fraction")
        water_fraction = _validated_or_zero(policy.water_to_protein_phase_fraction, "water to protein phase fraction")
        if policy.co_precipitated_ash_fraction is None:
            warnings.append("co_precipitated_ash_unspecified_kept_in_supernatant")
        if policy.co_precipitated_sugar_fraction is None:
            warnings.append("co_precipitated_sugar_unspecified_kept_in_supernatant")
        if policy.water_to_protein_phase_fraction is None:
            warnings.append("water_split_unspecified_kept_in_supernatant")
        fractions = {
            component: (
                recovery
                if component == "SolubleProtein"
                else ash_fraction
                if component == "Ash"
                else sugar_fraction
                if component in SOLUBLE_SUGARS
                else water_fraction
                if component == "Water"
                else 0.0
            )
            for component in clarified_juice_stream.component_masses_kg_per_kg_feed
        }
        metadata_fractions = {
            name: sugar_fraction if name == "fructan" else 0.0
            for name in clarified_juice_stream.metadata_pools_kg_per_kg_feed
        }
        protein_phase, supernatant = _partition_stream(
            clarified_juice_stream,
            fractions,
            metadata_fractions,
            "protein_rich_phase",
            "extraction_supernatant",
            "protein_extraction",
            "second_centrifugation",
            "second_centrifugation_then_biogas",
        )
        applied_policy = policy.to_dict()
    return _unit_result(
        "protein_extraction",
        "protein_extraction_preview",
        (clarified_juice_stream,),
        (protein_phase, supernatant),
        applied_policy,
        tuple(blockers),
        tuple(warnings),
        {
            "mass_preview_ready": not blockers,
            "protein_phase_created": protein_phase.component_masses_kg_per_kg_feed.get("SolubleProtein", 0.0) > 0.0,
            "tea_lca_active": False,
        },
    )


def preview_second_centrifugation(
    protein_rich_phase: DynamicProcessStream,
    extraction_supernatant: DynamicProcessStream,
    policy: DynamicRecoveryCentrifugationPolicy | None,
) -> DynamicUnitResult:
    """Capture a wet protein cake and combine all losses with supernatant."""

    blockers: list[str] = []
    warnings: list[str] = []
    if policy is None:
        blockers.append("second_centrifugation_policy_missing")
        wet_cake = _empty_stream("wet_protein_cake", protein_rich_phase.time_label, "second_centrifugation", "protein_drying")
        final_supernatant = combine_process_streams(
            (protein_rich_phase, extraction_supernatant),
            "final_supernatant",
            "biogas_residual_mix",
        )
        final_supernatant = _replace_source(final_supernatant, "second_centrifugation")
        applied_policy = DynamicRecoveryCentrifugationPolicy().to_dict()
    else:
        blockers.extend(policy.blockers)
        warnings.extend(policy.warnings)
        required = {
            "protein_phase_capture_fraction": policy.protein_phase_capture_fraction,
            "soluble_protein_loss_to_supernatant_fraction": policy.soluble_protein_loss_to_supernatant_fraction,
            "water_retention_in_cake_fraction": policy.water_retention_in_cake_fraction,
            "ash_retention_in_cake_fraction": policy.ash_retention_in_cake_fraction,
        }
        missing = [name for name, value in required.items() if value is None]
        blockers.extend(f"second_centrifugation_missing:{name}" for name in missing)
        values = {name: _validated_or_zero(value, name) for name, value in required.items()}
        protein_capture = values["protein_phase_capture_fraction"] * (
            1.0 - values["soluble_protein_loss_to_supernatant_fraction"]
        )
        fractions = {
            component: (
                protein_capture
                if component in PROTEIN_COMPONENTS
                else values["water_retention_in_cake_fraction"]
                if component == "Water"
                else values["ash_retention_in_cake_fraction"]
                if component == "Ash"
                else 0.0
            )
            for component in protein_rich_phase.component_masses_kg_per_kg_feed
        }
        source_target_metrics: dict[str, object] = {}
        if policy.target_wet_cake_moisture_fraction is not None:
            target_moisture = policy.target_wet_cake_moisture_fraction
            if not isfinite(target_moisture) or not 0.0 <= target_moisture < 1.0:
                raise ValueError("Wet protein cake moisture target must be in [0, 1).")
            captured_dry_mass = sum(
                mass * fractions.get(component, 0.0)
                for component, mass in protein_rich_phase.component_masses_kg_per_kg_feed.items()
                if component != "Water"
            )
            required_water = (
                0.0
                if captured_dry_mass <= MASS_TOLERANCE
                else target_moisture * captured_dry_mass / (1.0 - target_moisture)
            )
            available_water = protein_rich_phase.component_masses_kg_per_kg_feed.get("Water", 0.0)
            supernatant_water = extraction_supernatant.component_masses_kg_per_kg_feed.get("Water", 0.0)
            if required_water > available_water + supernatant_water + MASS_TOLERANCE:
                raise ValueError("PCEN_0003 wet-cake moisture requires more Water than the separator feed contains.")
            water_from_phase = min(required_water, available_water)
            additional_supernatant_water = required_water - water_from_phase
            fractions["Water"] = 0.0 if available_water <= MASS_TOLERANCE else water_from_phase / available_water
            warnings.append(
                "PCEN_0003 wet-cake moisture is authoritative; engineering water-retention fraction is not used"
            )
            source_target_metrics = {
                "target_wet_cake_moisture_fraction": target_moisture,
                "target_wet_cake_dry_mass_kg_per_kg_feed": captured_dry_mass,
                "target_wet_cake_water_kg_per_kg_feed": required_water,
                "water_retained_from_extraction_supernatant_kg_per_kg_feed": additional_supernatant_water,
                "evidence_class": "direct_grass_source",
                "source_record_ids": ["PCEN_0003"],
                "combined_recovery_lower_bound": policy.combined_recovery_lower_bound,
                "combined_recovery_lower_bound_applied_as_centrifuge_capture": False,
            }
        cake_from_phase, phase_loss = _partition_stream(
            protein_rich_phase,
            fractions,
            {name: 0.0 for name in protein_rich_phase.metadata_pools_kg_per_kg_feed},
            "wet_protein_cake",
            "protein_phase_centrifuge_loss",
            "second_centrifugation",
            "protein_drying",
            "final_supernatant",
        )
        additional_supernatant_water = (
            source_target_metrics.get("water_retained_from_extraction_supernatant_kg_per_kg_feed", 0.0)
            if source_target_metrics
            else 0.0
        )
        if additional_supernatant_water > MASS_TOLERANCE:
            remaining_supernatant_components = dict(
                extraction_supernatant.component_masses_kg_per_kg_feed
            )
            remaining_supernatant_components["Water"] = (
                remaining_supernatant_components.get("Water", 0.0)
                - float(additional_supernatant_water)
            )
            remaining_extraction_supernatant = _new_stream(
                "extraction_supernatant_after_cake_water_retention",
                extraction_supernatant.time_label,
                remaining_supernatant_components,
                extraction_supernatant.metadata_pools_kg_per_kg_feed,
                "second_centrifugation",
                "final_supernatant",
                provenance={"water_retained_to_match_record_id": "PCEN_0003"},
            )
            retained_water = _new_stream(
                "wet_cake_retained_water",
                extraction_supernatant.time_label,
                {"Water": float(additional_supernatant_water)},
                {},
                "second_centrifugation",
                "wet_protein_cake",
                provenance={"source_record_id": "PCEN_0003"},
            )
            wet_cake = combine_process_streams(
                (cake_from_phase, retained_water),
                "wet_protein_cake",
                "protein_drying",
            )
            wet_cake = _replace_source(wet_cake, "second_centrifugation")
        else:
            remaining_extraction_supernatant = extraction_supernatant
            wet_cake = cake_from_phase
        final_supernatant = combine_process_streams(
            (remaining_extraction_supernatant, phase_loss),
            "final_supernatant",
            "biogas_residual_mix",
        )
        final_supernatant = _replace_source(final_supernatant, "second_centrifugation")
        applied_policy = policy.to_dict()
    return _unit_result(
        "second_centrifugation",
        "protein_recovery_centrifugation_preview",
        (protein_rich_phase, extraction_supernatant),
        (wet_cake, final_supernatant),
        applied_policy,
        tuple(blockers),
        tuple(warnings),
        {
            "mass_preview_ready": not blockers,
            "wet_protein_cake_created": sum(wet_cake.component_masses_kg_per_kg_feed.values()) > 0.0,
            "final_supernatant_routed_to_biogas": True,
        },
        metrics=source_target_metrics if policy is not None else {},
    )


def preview_protein_drying(
    wet_protein_cake: DynamicProcessStream,
    policy: DynamicDryingPolicy | None,
) -> DynamicUnitResult:
    """Remove Water only and preserve every non-water mass exactly."""

    blockers: list[str] = []
    warnings: list[str] = []
    if policy is not None:
        blockers.extend(policy.blockers)
        warnings.extend(policy.warnings)
    if policy is None or policy.target_moisture_fraction is None:
        blockers.append("drying_target_moisture_missing")
        dried = _copy_stream(
            wet_protein_cake,
            "dried_protein_product",
            "protein_drying",
            "protein_product_storage",
            warning="drying_not_applied",
        )
        evaporated = _empty_stream("evaporated_water", wet_protein_cake.time_label, "protein_drying", "excluded_from_biogas_by_default")
        applied_policy = (policy or DynamicDryingPolicy()).to_dict()
        mass_ready = False
        energy_ready = False
    else:
        target = policy.target_moisture_fraction
        if not isfinite(target) or not 0.0 <= target < 1.0:
            raise ValueError("Drying target moisture fraction must be in [0, 1).")
        current_water = wet_protein_cake.component_masses_kg_per_kg_feed.get("Water", 0.0)
        dry_mass = wet_protein_cake.kg_per_kg_feed - current_water
        target_water = 0.0 if dry_mass <= 0.0 else target * dry_mass / (1.0 - target)
        water_removed = max(current_water - target_water, 0.0)
        remaining_water = current_water - water_removed
        components = dict(wet_protein_cake.component_masses_kg_per_kg_feed)
        if "Water" in components or remaining_water > 0.0:
            components["Water"] = remaining_water
        dried = _new_stream(
            "dried_protein_product",
            wet_protein_cake.time_label,
            components,
            dict(wet_protein_cake.metadata_pools_kg_per_kg_feed),
            "protein_drying",
            "protein_product_storage",
            provenance={"target_moisture_fraction": target},
        )
        evaporated = _new_stream(
            "evaporated_water",
            wet_protein_cake.time_label,
            {"Water": water_removed} if water_removed > 0.0 else {},
            {},
            "protein_drying",
            "excluded_from_biogas_by_default",
        )
        if policy.water_removal_fraction is not None:
            _validate_fraction(policy.water_removal_fraction, "water removal fraction")
            implied = 0.0 if current_water == 0.0 else water_removed / current_water
            if abs(implied - policy.water_removal_fraction) > 1e-9:
                warnings.append("water_removal_fraction_not_used_target_moisture_is_authoritative")
        if policy.drying_energy_kwh_per_kg_water is None:
            warnings.append("drying_energy_missing")
        elif policy.drying_energy_kwh_per_kg_water < 0.0:
            raise ValueError("Drying energy must be non-negative.")
        applied_policy = policy.to_dict()
        mass_ready = True
        energy_ready = policy.drying_energy_kwh_per_kg_water is not None
    return _unit_result(
        "protein_drying",
        "protein_drying_preview",
        (wet_protein_cake,),
        (dried, evaporated),
        applied_policy,
        tuple(blockers),
        tuple(warnings),
        {
            "mass_preview_ready": mass_ready,
            "energy_preview_ready": energy_ready,
            "tea_lca_active": False,
        },
    )


def build_biogas_residual_mix(
    cell_debris: DynamicProcessStream,
    final_supernatant: DynamicProcessStream,
    *,
    press_cake: DynamicProcessStream | None = None,
    include_press_cake: bool = False,
    policy: DynamicResidualBiogasPolicy | None = None,
) -> DynamicUnitResult:
    """Combine explicitly routed residuals without running anaerobic digestion."""

    inputs: list[DynamicProcessStream] = [cell_debris, final_supernatant]
    warnings: list[str] = []
    if include_press_cake:
        raise ValueError(
            "Press cake is outside the in-project dynamic AD boundary; use a separate external-scope report."
        )
    if press_cake is not None:
        warnings.append("press_cake_recorded_as_system_output_not_in_biogas_mix")
    candidate = combine_process_streams(inputs, "biogas_feed_candidate", "future_anaerobic_digestion")
    candidate = _replace_source(candidate, "biogas_residual_mixer")
    carbohydrates = sum(
        candidate.component_masses_kg_per_kg_feed.get(name, 0.0)
        for name in (*SOLUBLE_SUGARS, *STRUCTURAL_FIBERS)
    ) + sum(
        candidate.metadata_pools_kg_per_kg_feed.get(name, 0.0)
        for name in ("fructan", "residual_unallocated_dry_matter")
    )
    proteins = sum(candidate.component_masses_kg_per_kg_feed.get(name, 0.0) for name in PROTEIN_COMPONENTS)
    if policy is not None:
        warnings.extend(policy.warnings)
    bmp_available = bool(policy and policy.bmp_m3_ch4_per_kg_vs is not None)
    vs_policy_enabled = bool(
        policy and policy.residual_vs_estimation_policy == "known_organic_component_sum"
    )
    supernatant_vs = _estimate_vs_like_mass(
        final_supernatant,
        include_residual_unallocated=bool(
            policy and policy.include_residual_unallocated_dry_matter_as_vs
        ),
    ) if vs_policy_enabled else None
    debris_vs = _estimate_vs_like_mass(
        cell_debris,
        include_residual_unallocated=bool(
            policy and policy.include_residual_unallocated_dry_matter_as_vs
        ),
    ) if vs_policy_enabled else None
    total_vs = (
        supernatant_vs + debris_vs
        if supernatant_vs is not None and debris_vs is not None
        else None
    )
    methane_potential = (
        supernatant_vs * policy.bmp_m3_ch4_per_kg_vs
        if supernatant_vs is not None and policy and policy.bmp_m3_ch4_per_kg_vs is not None
        else None
    )
    readiness = {
        "has_carbohydrates": carbohydrates > 0.0,
        "has_proteins": proteins > 0.0,
        "missing_COD": True,
        "missing_BMP": not bmp_available,
        "bmp_proxy_available": bmp_available,
        "missing_VS": total_vs is None,
        "methane_potential_preview_available": methane_potential is not None,
        "missing_biodegradability": True,
        "missing_nutrient_speciation": True,
        "ad_active": False,
    }
    blockers = [
        "biogas_feed_missing_COD",
        "biogas_feed_missing_biodegradability",
        "biogas_feed_missing_nutrient_speciation",
    ]
    if total_vs is None:
        blockers.append("biogas_feed_missing_VS")
    if not bmp_available:
        blockers.append("biogas_feed_missing_BMP")
    if policy is not None:
        blockers.extend(policy.blockers)
    return _unit_result(
        "biogas_residual_mixer",
        "biogas_feed_preparation_preview",
        tuple(inputs),
        (candidate,),
        {
            "policy_id": "residual_mass_combination_only",
            "include_press_cake": include_press_cake,
            "bmp_policy": policy.to_dict() if policy else None,
            "status": "report_only",
        },
        tuple(dict.fromkeys(blockers)),
        tuple(dict.fromkeys(warnings)),
        readiness,
        metrics={
            "estimated_supernatant_vs_kg_per_kg_feed": supernatant_vs,
            "estimated_cell_debris_vs_kg_per_kg_feed": debris_vs,
            "estimated_residual_vs_kg_per_kg_feed": total_vs,
            "bmp_eligible_vs_kg_per_kg_feed": supernatant_vs,
            "bmp_m3_ch4_per_kg_vs": policy.bmp_m3_ch4_per_kg_vs if policy else None,
            "methane_potential_m3_ch4_per_kg_feed": methane_potential,
            "ad_kinetics_run": False,
            "evidence_class": (
                "mixed_proxy_and_engineering_proxy_closure"
                if methane_potential is not None
                else "blocked"
            ),
        },
    )


def _estimate_vs_like_mass(
    stream: DynamicProcessStream,
    *,
    include_residual_unallocated: bool,
) -> float:
    organic_components = {
        *PROTEIN_COMPONENTS,
        *SOLUBLE_SUGARS,
        *STRUCTURAL_FIBERS,
    }
    total = sum(
        mass
        for component, mass in stream.component_masses_kg_per_kg_feed.items()
        if component in organic_components
    )
    total += stream.metadata_pools_kg_per_kg_feed.get("fructan", 0.0)
    if include_residual_unallocated:
        total += stream.metadata_pools_kg_per_kg_feed.get(
            "residual_unallocated_dry_matter",
            0.0,
        )
    return total


def preview_baseline_dynamic_operational_scenario(
    *,
    time_label: str = "2026-05",
    feedstock_bundle: DynamicFeedstockInputBundle | None = None,
    pool_policy: DynamicFeedstockPoolPolicy | None = None,
    scenario: DynamicOperationalScenario | None = None,
    dynamic_press_bundle: DynamicPressPreviewBundle | None = None,
) -> DynamicPathwayPreview:
    """Run every report-only stage and return partial outputs when blocked."""

    scenario = scenario or DynamicOperationalScenario(
        scenario_id="baseline_dynamic_operational_blocked_v1",
        scenario_name="Conservative baseline dynamic operational preview",
    )
    feedstock_bundle = feedstock_bundle or build_dynamic_feedstock_input_bundle(time_label)
    pool_policy = pool_policy or default_literature_pool_policy()
    pools = build_dynamic_feedstock_pools(feedstock_bundle, pool_policy)
    press_bundle = dynamic_press_bundle or build_dynamic_press_preview_bundle(pools)
    if press_bundle.time_label != pools.time_label:
        raise ValueError("Dynamic press bundle time label does not match the feedstock bundle.")
    raw_press = build_raw_press_baseline_streams(press_bundle, scenario.raw_press_policy)
    press_cake = _output(raw_press, "press_cake")
    brown_juice = _output(raw_press, "brown_juice")
    first = preview_first_centrifugation(brown_juice, scenario.first_centrifugation_policy)
    clarified = _output(first, "clarified_juice")
    debris = _output(first, "cell_debris")
    extraction = preview_protein_extraction(clarified, scenario.protein_extraction_policy)
    protein_phase = _output(extraction, "protein_rich_phase")
    extraction_supernatant = _output(extraction, "extraction_supernatant")
    second = preview_second_centrifugation(
        protein_phase,
        extraction_supernatant,
        scenario.second_centrifugation_policy,
    )
    wet_cake = _output(second, "wet_protein_cake")
    final_supernatant = _output(second, "final_supernatant")
    drying = preview_protein_drying(wet_cake, scenario.drying_policy)
    residual = build_biogas_residual_mix(
        debris,
        final_supernatant,
        press_cake=press_cake,
        include_press_cake=False,
        policy=scenario.residual_biogas_policy,
    )
    final_outputs = [
        _output(drying, "dried_protein_product"),
        _output(drying, "evaporated_water"),
        _output(residual, "biogas_feed_candidate"),
    ]
    final_outputs.append(press_cake)
    unrecovered_press = next(
        (
            stream
            for stream in raw_press.outputs
            if stream.stream_id == "raw_press_unrecovered_process_mass"
        ),
        None,
    )
    if unrecovered_press is not None:
        final_outputs.append(unrecovered_press)
    units = (raw_press, first, extraction, second, drying, residual)
    blockers = tuple(dict.fromkeys(blocker for unit in units for blocker in unit.blockers))
    warning_values = [warning for unit in units for warning in unit.warnings]
    if scenario.include_press_cake_in_biogas_mix:
        warning_values.append("press_cake_in_biogas_request_ignored_project_boundary_requires_external_scope")
    warnings = tuple(dict.fromkeys(warning_values))
    pathway_balance = _mass_balance(
        (_feed_stream_from_pools(pools),),
        tuple(final_outputs),
        allow_unresolved_identity=not scenario.is_demo,
    )
    if not pathway_balance["closes"]:
        raise ValueError("Dynamic pathway preview failed overall mass conservation.")
    return DynamicPathwayPreview(
        time_label=feedstock_bundle.time_label,
        scenario=scenario,
        feedstock_bundle=feedstock_bundle,
        feed_pools=pools,
        dynamic_press_bundle=press_bundle,
        raw_press=raw_press,
        first_centrifugation=first,
        protein_extraction=extraction,
        second_centrifugation=second,
        drying=drying,
        biogas_mix_preparation=residual,
        final_outputs=tuple(final_outputs),
        blockers=blockers,
        warnings=warnings,
        mass_balance_summary=pathway_balance,
        selected_method=(
            scenario.protein_extraction_policy.method
            if scenario.protein_extraction_policy
            else ProteinExtractionMethod.ISOELECTRIC.value
        ),
        method_policy=(scenario.protein_extraction_policy.to_dict() if scenario.protein_extraction_policy else {}),
        active_unit_sequence=(
            "dynamic_raw_press",
            "first_centrifugation",
            "protein_extraction",
            "second_centrifugation",
            "protein_drying",
            "biogas_residual_mixer",
        ),
        system_outputs={stream.stream_id: stream.to_dict() for stream in final_outputs},
        provenance={
            "mode": "conservative_report_only",
            "press_cake_boundary": "system_output_external_downstream_scope",
            "empirical_model_modified": False,
            "model_overrides": [],
        },
        can_drive_simulation=False,
    )


def preview_proxy_enabled_dynamic_operational_scenario(
    *,
    method: str = ProteinExtractionMethod.ISOELECTRIC.value,
    allow_proxy: bool = True,
    allow_n_to_protein_proxy: bool = True,
    include_press_cake_in_biogas: bool = False,
    time_label: str = "2026-05",
    feedstock_bundle: DynamicFeedstockInputBundle | None = None,
    pool_policy: DynamicFeedstockPoolPolicy | None = None,
    proxy_closure_policy: DynamicProxyClosurePolicy | None = None,
) -> DynamicPathwayPreview:
    """Build the opt-in dataset-backed protein pathway without model activation."""

    selected = _coerce_method(method)
    if include_press_cake_in_biogas:
        raise ValueError(
            "Press cake is a GreenHub system output and cannot enter the in-project biogas candidate."
        )
    feedstock_bundle = feedstock_bundle or build_dynamic_feedstock_input_bundle(time_label)
    pool_policy = pool_policy or default_literature_pool_policy()
    pools = build_dynamic_feedstock_pools(feedstock_bundle, pool_policy)

    press_kwargs: dict[str, object] = {}
    if allow_proxy:
        press_kwargs = {
            "water_closure_correction": WaterClosureCorrectionPolicy(
                policy_id="proxy_path_water_closure_v1",
                rationale="Explicit analytical closure correction for the selected source Water triplet.",
            ),
            "total_sugar_fallback": TotalSugarPartitionFallbackPolicy(
                policy_id="proxy_path_total_wsc_v1",
                rationale="Explicitly apply the source total-WSC split to modeled soluble sugars.",
            ),
        }
    press_bundle = build_dynamic_press_preview_bundle(pools, **press_kwargs)
    extraction_policy = build_dataset_protein_extraction_policy(
        method=selected.value,
        allow_proxy=allow_proxy,
        allow_n_to_protein_proxy=allow_n_to_protein_proxy,
        closure_policy=proxy_closure_policy,
    )
    raw_press_policy = (
        build_closed_proxy_raw_press_policy(proxy_closure_policy)
        if proxy_closure_policy is not None
        else build_proxy_raw_press_protein_policy(allow_proxy=allow_proxy)
    )
    scenario = DynamicOperationalScenario(
        scenario_id=f"proxy_enabled_{selected.value}_protein_pathway_v1",
        scenario_name=f"Proxy-enabled report-only {selected.value} protein pathway",
        raw_press_policy=raw_press_policy,
        first_centrifugation_policy=build_dataset_first_centrifugation_policy(
            allow_proxy=allow_proxy,
            closure_policy=proxy_closure_policy,
        ),
        protein_extraction_policy=extraction_policy,
        second_centrifugation_policy=build_dataset_second_centrifugation_policy(
            allow_proxy=allow_proxy,
            closure_policy=proxy_closure_policy,
        ),
        drying_policy=build_dataset_drying_policy(
            allow_proxy=allow_proxy,
            closure_policy=proxy_closure_policy,
        ),
        residual_biogas_policy=build_dataset_residual_biogas_policy(
            allow_proxy=allow_proxy,
            closure_policy=proxy_closure_policy,
        ),
        include_press_cake_in_biogas_mix=False,
        provenance={
            "mode": "proxy_enabled_report_only" if allow_proxy else "strict_report_only",
            "selected_method": selected.value,
            "allow_n_to_protein_proxy": allow_n_to_protein_proxy,
            "proxy_closure_policy": proxy_closure_policy.to_dict() if proxy_closure_policy else None,
            "press_cake_boundary": "external_downstream_scope",
            "empirical_model_modified": False,
            "model_overrides": [],
        },
    )
    preview = preview_baseline_dynamic_operational_scenario(
        feedstock_bundle=feedstock_bundle,
        pool_policy=pool_policy,
        scenario=scenario,
        dynamic_press_bundle=press_bundle,
    )
    alternatives = tuple(item.value for item in ProteinExtractionMethod if item is not selected)
    dried = next(stream for stream in preview.final_outputs if stream.stream_id == "dried_protein_product")
    brown = _output(preview.raw_press, "brown_juice")
    unit_proxy_ready = (
        not preview.first_centrifugation.blockers
        and not preview.protein_extraction.blockers
        and not preview.second_centrifugation.blockers
        and not preview.drying.blockers
    )
    protein_flow_ready = (
        brown.component_masses_kg_per_kg_feed.get("SolubleProtein", 0.0) > 0.0
        and dried.component_masses_kg_per_kg_feed.get("SolubleProtein", 0.0) > 0.0
    )
    required_streams = {
        "brown_juice": _output(preview.raw_press, "brown_juice"),
        "clarified_juice": _output(preview.first_centrifugation, "clarified_juice"),
        "protein_rich_phase": _output(preview.protein_extraction, "protein_rich_phase"),
        "wet_protein_cake": _output(preview.second_centrifugation, "wet_protein_cake"),
        "dried_protein_product": dried,
        "biogas_feed_candidate": _output(preview.biogas_mix_preparation, "biogas_feed_candidate"),
    }
    streams_ready = all(stream.kg_per_kg_feed > MASS_TOLERANCE for stream in required_streams.values())
    can_drive_proxy_preview = bool(
        allow_proxy
        and proxy_closure_policy is not None
        and unit_proxy_ready
        and protein_flow_ready
        and streams_ready
        and preview.mass_balance_summary["identity_closes"]
    )
    proxy_warnings = tuple(
        dict.fromkeys(
            warning
            for unit in (
                preview.raw_press,
                preview.first_centrifugation,
                preview.protein_extraction,
                preview.second_centrifugation,
                preview.drying,
                preview.biogas_mix_preparation,
            )
            for warning in unit.warnings
            if "PROXY" in warning or "proxy" in warning.lower() or "closure" in warning.lower()
        )
    )
    return replace(
        preview,
        selected_method=selected.value,
        method_policy=extraction_policy.to_dict(),
        method_alternatives_available=tuple(item.value for item in ProteinExtractionMethod),
        inactive_alternative_methods=alternatives,
        system_outputs={stream.stream_id: stream.to_dict() for stream in preview.final_outputs},
        proxy_warnings=proxy_warnings,
        provenance={
            **preview.provenance,
            **scenario.provenance,
            "fallbacks_enabled": [
                name
                for name, enabled in press_bundle.partition_policy.policy.fallback_status.items()
                if enabled
            ],
            "validated_greenhub_simulation": False,
        },
        can_drive_proxy_preview=can_drive_proxy_preview,
        validated_simulation_ready=False,
        can_drive_simulation=False,
        activation_status="proxy_enabled_report_only_not_model_active" if allow_proxy else "strict_report_only_not_model_active",
    )


def preview_closed_proxy_dynamic_protein_pathway(
    *,
    time_label: str = "2026-05",
    method: str = ProteinExtractionMethod.ISOELECTRIC.value,
    closure_policy: DynamicProxyClosurePolicy | None = None,
    target_moisture_fraction: float | None = None,
    feedstock_bundle: DynamicFeedstockInputBundle | None = None,
    pool_policy: DynamicFeedstockPoolPolicy | None = None,
) -> DynamicPathwayPreview:
    """Run a complete, non-validated proxy closure for process inspection."""

    closure_policy = closure_policy or default_proxy_closure_policy()
    if target_moisture_fraction is not None:
        if not isfinite(target_moisture_fraction) or not 0.0 <= target_moisture_fraction < 1.0:
            raise ValueError("Scenario target moisture fraction must be in [0, 1).")
        closure_policy = replace(
            closure_policy,
            target_moisture_fraction=target_moisture_fraction,
            target_moisture_evidence_class="scenario_input_override",
        )
    return preview_proxy_enabled_dynamic_operational_scenario(
        method=method,
        allow_proxy=True,
        allow_n_to_protein_proxy=True,
        include_press_cake_in_biogas=False,
        time_label=time_label,
        feedstock_bundle=feedstock_bundle,
        pool_policy=pool_policy,
        proxy_closure_policy=closure_policy,
    )


def _validate_dynamic_protein_scenario_config(config: DynamicProteinScenarioConfig) -> None:
    if not config.scenario_id.strip():
        raise ValueError("scenario_id must not be empty.")
    if (
        not isfinite(config.drying_target_moisture_fraction)
        or not 0.0 <= config.drying_target_moisture_fraction < 1.0
    ):
        raise ValueError("drying_target_moisture_fraction must be >= 0 and < 1.")
    _coerce_method(config.protein_method)
    _validate_policy_id(
        config.raw_press_policy_id,
        SUPPORTED_RAW_PRESS_POLICY_IDS,
        "raw_press_policy_id",
    )
    _validate_policy_id(
        config.first_centrifuge_policy_id,
        SUPPORTED_FIRST_CENTRIFUGE_POLICY_IDS,
        "first_centrifuge_policy_id",
    )
    _validate_policy_id(
        config.second_centrifuge_policy_id,
        SUPPORTED_SECOND_CENTRIFUGE_POLICY_IDS,
        "second_centrifuge_policy_id",
    )
    if config.include_press_cake_in_biogas and not config.external_scope_override:
        raise ValueError(
            "include_press_cake_in_biogas=True requires external_scope_override=True; "
            "press cake is excluded from the in-project biogas boundary."
        )
    generate_time_grid(config.start_date, config.end_date, config.time_step)


def _validate_policy_id(value: str, supported: frozenset[str], field_name: str) -> None:
    if value not in supported:
        choices = ", ".join(sorted(supported))
        raise ValueError(f"Unknown {field_name} {value!r}; supported IDs: {choices}.")


def run_dynamic_protein_scenario_step(
    config: DynamicProteinScenarioConfig,
    time_label: str,
) -> DynamicProteinScenarioRun:
    """Run one independent report-only scenario step without global mutation."""

    _validate_dynamic_protein_scenario_config(config)
    feedstock_bundle = build_dynamic_feedstock_input_bundle(time_label)
    pool_policy = default_literature_pool_policy()
    closure_policy: DynamicProxyClosurePolicy | None = None
    if config.allow_proxy and config.allow_engineering_proxy_closure:
        moisture_class = (
            "scenario_input_baseline"
            if abs(
                config.drying_target_moisture_fraction
                - BASELINE_TARGET_MOISTURE_FRACTION
            ) <= MASS_TOLERANCE
            else "scenario_input_override"
        )
        closure_policy = replace(
            default_proxy_closure_policy(),
            target_moisture_fraction=config.drying_target_moisture_fraction,
            target_moisture_evidence_class=moisture_class,
        )
    preview = preview_proxy_enabled_dynamic_operational_scenario(
        method=config.protein_method,
        allow_proxy=config.allow_proxy,
        allow_n_to_protein_proxy=config.allow_n_to_protein_proxy,
        include_press_cake_in_biogas=False,
        time_label=time_label,
        feedstock_bundle=feedstock_bundle,
        pool_policy=pool_policy,
        proxy_closure_policy=closure_policy,
    )
    units = _pathway_units(preview)
    policy_ids = {
        unit.unit_id: _unit_policy_id(unit)
        for unit in units
        if _unit_policy_id(unit)
    }
    source_record_ids = tuple(
        sorted(
            {
                record_id
                for unit in units
                for record_id in _collect_nested_values(unit.applied_policy, "record_id")
                | _collect_nested_values(unit.applied_policy, "parameter_id")
            }
        )
    )
    output_masses = _grid_output_masses(preview)
    brown = _output(preview.raw_press, "brown_juice")
    clarified = _output(preview.first_centrifugation, "clarified_juice")
    wet_cake = _output(preview.second_centrifugation, "wet_protein_cake")
    dried = _output(preview.drying, "dried_protein_product")
    protein_metrics = {
        "brown_juice_soluble_protein": brown.component_masses_kg_per_kg_feed.get(
            "SolubleProtein", 0.0
        ),
        "clarified_juice_soluble_protein": clarified.component_masses_kg_per_kg_feed.get(
            "SolubleProtein", 0.0
        ),
        "recovered_protein": sum(
            wet_cake.component_masses_kg_per_kg_feed.get(name, 0.0)
            for name in PROTEIN_COMPONENTS
        ),
        "dried_product_protein": sum(
            dried.component_masses_kg_per_kg_feed.get(name, 0.0)
            for name in PROTEIN_COMPONENTS
        ),
    }
    residual = preview.biogas_mix_preparation.metrics
    residual_metrics = {
        "estimated_residual_vs": residual.get(
            "estimated_residual_vs_kg_per_kg_feed"
        ),
        "methane_potential_m3_ch4_per_kg_feed": residual.get(
            "methane_potential_m3_ch4_per_kg_feed"
        ),
        "ad_kinetics_run": residual.get("ad_kinetics_run", False),
    }
    warnings = list(preview.warnings)
    if config.include_press_cake_in_biogas and config.external_scope_override:
        warnings.append(
            "external_scope_override_recorded_only; press cake remains excluded from in-project biogas"
        )
    return DynamicProteinScenarioRun(
        scenario_id=config.scenario_id,
        time_label=time_label,
        selected_method=preview.selected_method,
        policy_ids=policy_ids,
        source_record_ids=source_record_ids,
        output_masses_kg_per_kg_feed=output_masses,
        protein_metrics_kg_per_kg_feed=protein_metrics,
        residual_metrics=residual_metrics,
        can_drive_proxy_preview=preview.can_drive_proxy_preview,
        can_drive_simulation=preview.can_drive_simulation,
        validated_simulation_ready=preview.validated_simulation_ready,
        warnings=tuple(dict.fromkeys(warnings)),
        blockers=preview.blockers,
        provenance={
            "config": config.to_dict(),
            "requested_policy_ids": _requested_policy_ids(config),
            "source_record_ids": list(source_record_ids),
            "feedstock_bundle_time_label": feedstock_bundle.time_label,
            "feedstock_confidence_score": feedstock_bundle.confidence_score,
            "press_cake_boundary": "system_output_external_downstream_scope",
            "model_overrides": [],
            "empirical_model_modified": False,
            "biosteam_adapter_active": False,
        },
        pathway_preview=preview,
        activation_status="proxy_enabled_grid_step_report_only",
    )


def run_dynamic_protein_scenario_grid(
    config: DynamicProteinScenarioConfig,
) -> DynamicProteinScenarioGridResult:
    """Run all generated time steps independently and retain blocked steps."""

    _validate_dynamic_protein_scenario_config(config)
    grid = generate_time_grid(config.start_date, config.end_date, config.time_step)
    runs: list[DynamicProteinScenarioRun] = []
    for step in grid:
        try:
            runs.append(run_dynamic_protein_scenario_step(config, step.label))
        except ValueError as error:
            runs.append(_failed_dynamic_protein_scenario_run(config, step, error))
    output_values = {
        stream_id: [run.output_masses_kg_per_kg_feed.get(stream_id, 0.0) for run in runs]
        for stream_id in GRID_OUTPUT_STREAM_IDS
    }
    totals = {name: sum(values) for name, values in output_values.items()}
    averages = {
        name: (sum(values) / len(values) if values else 0.0)
        for name, values in output_values.items()
    }
    ranges = {
        name: {
            "min": min(values) if values else 0.0,
            "max": max(values) if values else 0.0,
        }
        for name, values in output_values.items()
    }
    blocker_counts = Counter(blocker for run in runs for blocker in run.blockers)
    warning_counts = Counter(warning for run in runs for warning in run.warnings)
    policy_ids = tuple(
        sorted({policy_id for run in runs for policy_id in run.policy_ids.values()})
    )
    evidence_counts = Counter()
    for run in runs:
        if run.pathway_preview is None:
            continue
        evidence_counts.update(_scenario_evidence_classes(run.pathway_preview))
    return DynamicProteinScenarioGridResult(
        config=config,
        time_grid=grid,
        runs=tuple(runs),
        total_output_masses_kg_per_kg_feed_steps=totals,
        average_output_masses_kg_per_kg_feed=averages,
        output_ranges_kg_per_kg_feed=ranges,
        blocker_counts=dict(sorted(blocker_counts.items())),
        warning_counts=dict(sorted(warning_counts.items())),
        policy_ids_used=policy_ids,
        evidence_class_counts=dict(sorted(evidence_counts.items())),
        provenance={
            "runner": "run_dynamic_protein_scenario_grid",
            "time_step_independence": True,
            "interpolation_applied": False,
            "aggregation_basis": "sum_and_average_of_per_kg_feed_step_previews",
            "evidence_count_basis": "unit_evidence_class_tokens",
            "model_overrides": [],
            "empirical_model_modified": False,
            "biosteam_adapter_active": False,
        },
        activation_status="proxy_enabled_grid_report_only",
    )


def summarize_dynamic_protein_scenario_grid(
    result: DynamicProteinScenarioGridResult,
) -> dict[str, object]:
    """Return the compact JSON-safe activation and range summary."""

    proxy_ready = all(run.can_drive_proxy_preview for run in result.runs)
    simulation_ready = all(run.can_drive_simulation for run in result.runs)
    validated_ready = all(run.validated_simulation_ready for run in result.runs)
    next_blockers = set(result.blocker_counts)
    if any("drying_energy_missing" in run.warnings for run in result.runs):
        next_blockers.add("drying_energy_missing")
    if result.evidence_class_counts.get("engineering", 0):
        next_blockers.add("engineering_proxy_closure_requires_validation")
    if result.evidence_class_counts.get("proxy", 0):
        next_blockers.add("proxy_evidence_requires_greenhub_validation")
    next_blockers.add("biosteam_adapter_not_implemented")
    return {
        "scenario_id": result.config.scenario_id,
        "number_of_steps": len(result.runs),
        "time_labels": [run.time_label for run in result.runs],
        "selected_method": result.config.protein_method,
        "policy_ids": list(result.policy_ids_used),
        "can_drive_proxy_preview_all_steps": proxy_ready,
        "can_drive_simulation_all_steps": simulation_ready,
        "validated_simulation_ready_all_steps": validated_ready,
        "output_ranges_kg_per_kg_feed": {
            name: dict(values) for name, values in result.output_ranges_kg_per_kg_feed.items()
        },
        "total_output_masses_kg_per_kg_feed_steps": dict(
            result.total_output_masses_kg_per_kg_feed_steps
        ),
        "average_output_masses_kg_per_kg_feed": dict(
            result.average_output_masses_kg_per_kg_feed
        ),
        "blocker_counts": dict(result.blocker_counts),
        "warning_counts": dict(result.warning_counts),
        "evidence_class_counts": dict(result.evidence_class_counts),
        "next_activation_blockers": sorted(next_blockers),
        "activation_status": result.activation_status,
    }


def write_dynamic_protein_scenario_grid_reports(
    result: DynamicProteinScenarioGridResult,
    output_dir: str | Path | None = None,
) -> dict[str, str]:
    """Write four traceable CSV artifacts for one grid scenario result."""

    target = Path(output_dir) if output_dir is not None else RESULTS_DIR
    target.mkdir(parents=True, exist_ok=True)
    summary_path = target / "dynamic_protein_grid_summary.csv"
    streams_path = target / "dynamic_protein_grid_streams.csv"
    units_path = target / "dynamic_protein_grid_units.csv"
    blockers_path = target / "dynamic_protein_grid_blockers.csv"
    common_fields = (
        "scenario_id",
        "time_label",
        "unit_id",
        "stream_id",
        "kg_per_kg_feed",
        "component",
        "component_mass_kg_per_kg_feed",
        "metadata_pool",
        "metadata_mass_kg_per_kg_feed",
        "selected_method",
        "policy_ids",
        "evidence_class",
        "source_id",
        "record_id",
        "warning",
        "blocker",
    )

    stream_rows: list[dict[str, object]] = []
    unit_rows: list[dict[str, object]] = []
    blocker_rows: list[dict[str, object]] = []
    for run in result.runs:
        preview = run.pathway_preview
        if preview is None:
            for blocker in run.blockers:
                blocker_rows.append({
                    **_grid_base_row(run),
                    "record_type": "blocker",
                    "message": blocker,
                    "count": 1,
                    "blocker": blocker,
                })
            continue
        unit_warning_values: set[str] = set()
        unit_blocker_values: set[str] = set()
        for unit in _pathway_units(preview):
            trace = _unit_trace_columns(unit)
            base = _grid_base_row(run, unit=unit, trace=trace)
            unit_rows.append({
                **base,
                "stream_id": "|".join(stream.stream_id for stream in unit.outputs),
                "kg_per_kg_feed": unit.mass_balance_summary["output_mass_kg_per_kg_feed"],
                "unit_type": unit.unit_type,
                "input_streams": "|".join(stream.stream_id for stream in unit.inputs),
                "output_streams": "|".join(stream.stream_id for stream in unit.outputs),
                "input_mass_kg_per_kg_feed": unit.mass_balance_summary["input_mass_kg_per_kg_feed"],
                "output_mass_kg_per_kg_feed": unit.mass_balance_summary["output_mass_kg_per_kg_feed"],
                "mass_balance_residual_kg_per_kg_feed": unit.mass_balance_summary["residual_kg_per_kg_feed"],
                "identity_closes": unit.mass_balance_summary["identity_closes"],
                "metrics_json": json.dumps(unit.metrics, sort_keys=True),
            })
            for stream in unit.outputs:
                entries = [
                    (component, mass, "", "")
                    for component, mass in stream.component_masses_kg_per_kg_feed.items()
                ] + [
                    ("", "", pool, mass)
                    for pool, mass in stream.metadata_pools_kg_per_kg_feed.items()
                ]
                if not entries:
                    entries = [("", "", "", "")]
                for component, component_mass, metadata_pool, metadata_mass in entries:
                    stream_rows.append({
                        **base,
                        "stream_id": stream.stream_id,
                        "kg_per_kg_feed": stream.kg_per_kg_feed,
                        "component": component,
                        "component_mass_kg_per_kg_feed": component_mass,
                        "metadata_pool": metadata_pool,
                        "metadata_mass_kg_per_kg_feed": metadata_mass,
                    })
            for warning in unit.warnings:
                unit_warning_values.add(warning)
                blocker_rows.append({
                    **base,
                    "record_type": "warning",
                    "message": warning,
                    "count": 1,
                    "warning": warning,
                    "blocker": "",
                })
            for blocker in unit.blockers:
                unit_blocker_values.add(blocker)
                blocker_rows.append({
                    **base,
                    "record_type": "blocker",
                    "message": blocker,
                    "count": 1,
                    "warning": "",
                    "blocker": blocker,
                })
        for warning in set(run.warnings) - unit_warning_values:
            blocker_rows.append({
                **_grid_base_row(run),
                "record_type": "warning",
                "message": warning,
                "count": 1,
                "warning": warning,
                "blocker": "",
            })
        for blocker in set(run.blockers) - unit_blocker_values:
            blocker_rows.append({
                **_grid_base_row(run),
                "record_type": "blocker",
                "message": blocker,
                "count": 1,
                "warning": "",
                "blocker": blocker,
            })

    summary_rows: list[dict[str, object]] = []
    for run in result.runs:
        trace = _scenario_run_trace(run)
        summary_rows.append({
            **_grid_base_row(run, trace=trace),
            "unit_id": "scenario_step_summary",
            "number_of_steps": 1,
            "can_drive_proxy_preview": run.can_drive_proxy_preview,
            "can_drive_simulation": run.can_drive_simulation,
            "validated_simulation_ready": run.validated_simulation_ready,
            "output_masses_json": json.dumps(run.output_masses_kg_per_kg_feed, sort_keys=True),
            "total_output_masses_json": json.dumps(
                run.output_masses_kg_per_kg_feed, sort_keys=True
            ),
            "average_output_masses_json": json.dumps(
                run.output_masses_kg_per_kg_feed, sort_keys=True
            ),
            "protein_metrics_json": json.dumps(run.protein_metrics_kg_per_kg_feed, sort_keys=True),
            "residual_metrics_json": json.dumps(run.residual_metrics, sort_keys=True),
            "output_ranges_json": "",
            "blocker_counts_json": json.dumps(Counter(run.blockers), sort_keys=True),
            "warning_counts_json": json.dumps(Counter(run.warnings), sort_keys=True),
            "evidence_class_counts_json": "",
        })
    compact = summarize_dynamic_protein_scenario_grid(result)
    summary_rows.append({
        **_empty_grid_common_row(
            scenario_id=result.config.scenario_id,
            time_label="ALL",
            selected_method=result.config.protein_method,
            policy_ids="|".join(result.policy_ids_used),
        ),
        "unit_id": "grid_summary",
        "number_of_steps": len(result.runs),
        "can_drive_proxy_preview": compact["can_drive_proxy_preview_all_steps"],
        "can_drive_simulation": compact["can_drive_simulation_all_steps"],
        "validated_simulation_ready": compact["validated_simulation_ready_all_steps"],
        "output_masses_json": json.dumps(
            result.average_output_masses_kg_per_kg_feed, sort_keys=True
        ),
        "total_output_masses_json": json.dumps(
            result.total_output_masses_kg_per_kg_feed_steps, sort_keys=True
        ),
        "average_output_masses_json": json.dumps(
            result.average_output_masses_kg_per_kg_feed, sort_keys=True
        ),
        "protein_metrics_json": "",
        "residual_metrics_json": "",
        "output_ranges_json": json.dumps(result.output_ranges_kg_per_kg_feed, sort_keys=True),
        "blocker_counts_json": json.dumps(result.blocker_counts, sort_keys=True),
        "warning_counts_json": json.dumps(result.warning_counts, sort_keys=True),
        "evidence_class_counts_json": json.dumps(result.evidence_class_counts, sort_keys=True),
        "blocker": "|".join(compact["next_activation_blockers"]),
    })

    summary_fields = common_fields + (
        "number_of_steps",
        "can_drive_proxy_preview",
        "can_drive_simulation",
        "validated_simulation_ready",
        "output_masses_json",
        "total_output_masses_json",
        "average_output_masses_json",
        "protein_metrics_json",
        "residual_metrics_json",
        "output_ranges_json",
        "blocker_counts_json",
        "warning_counts_json",
        "evidence_class_counts_json",
    )
    unit_fields = common_fields + (
        "unit_type",
        "input_streams",
        "output_streams",
        "input_mass_kg_per_kg_feed",
        "output_mass_kg_per_kg_feed",
        "mass_balance_residual_kg_per_kg_feed",
        "identity_closes",
        "metrics_json",
    )
    blocker_fields = common_fields + ("record_type", "message", "count")
    _write_dict_rows(summary_path, summary_fields, summary_rows)
    _write_dict_rows(streams_path, common_fields, stream_rows)
    _write_dict_rows(units_path, unit_fields, unit_rows)
    _write_dict_rows(blockers_path, blocker_fields, blocker_rows)
    return {
        "summary": str(summary_path),
        "streams": str(streams_path),
        "units": str(units_path),
        "blockers": str(blockers_path),
    }


def _requested_policy_ids(config: DynamicProteinScenarioConfig) -> dict[str, str]:
    return {
        "raw_press": config.raw_press_policy_id,
        "first_centrifuge": config.first_centrifuge_policy_id,
        "second_centrifuge": config.second_centrifuge_policy_id,
    }


def _unit_policy_id(unit: DynamicUnitResult) -> str:
    policy_id = unit.applied_policy.get("policy_id")
    if policy_id:
        return str(policy_id)
    nested = _collect_nested_values(unit.applied_policy, "policy_id")
    return sorted(nested)[0] if nested else ""


def _grid_output_masses(preview: DynamicPathwayPreview) -> dict[str, float]:
    stream_lookup = {
        "press_cake": _output(preview.raw_press, "press_cake"),
        "brown_juice": _output(preview.raw_press, "brown_juice"),
        "cell_debris": _output(preview.first_centrifugation, "cell_debris"),
        "clarified_juice": _output(preview.first_centrifugation, "clarified_juice"),
        "wet_protein_cake": _output(preview.second_centrifugation, "wet_protein_cake"),
        "dried_protein_product": _output(preview.drying, "dried_protein_product"),
        "evaporated_water": _output(preview.drying, "evaporated_water"),
        "biogas_feed_candidate": _output(
            preview.biogas_mix_preparation, "biogas_feed_candidate"
        ),
    }
    unrecovered = next(
        (
            stream
            for stream in preview.raw_press.outputs
            if stream.stream_id == "raw_press_unrecovered_process_mass"
        ),
        None,
    )
    return {
        **{name: stream.kg_per_kg_feed for name, stream in stream_lookup.items()},
        "unrecovered_press_mass": unrecovered.kg_per_kg_feed if unrecovered else 0.0,
    }


def _failed_dynamic_protein_scenario_run(
    config: DynamicProteinScenarioConfig,
    step: TimeGridStep,
    error: ValueError,
) -> DynamicProteinScenarioRun:
    blocker = f"scenario_step_value_error:{type(error).__name__}:{error}"
    return DynamicProteinScenarioRun(
        scenario_id=config.scenario_id,
        time_label=step.label,
        selected_method=config.protein_method,
        policy_ids=_requested_policy_ids(config),
        source_record_ids=(),
        output_masses_kg_per_kg_feed={name: 0.0 for name in GRID_OUTPUT_STREAM_IDS},
        protein_metrics_kg_per_kg_feed={
            "brown_juice_soluble_protein": 0.0,
            "clarified_juice_soluble_protein": 0.0,
            "recovered_protein": 0.0,
            "dried_product_protein": 0.0,
        },
        residual_metrics={},
        can_drive_proxy_preview=False,
        can_drive_simulation=False,
        validated_simulation_ready=False,
        warnings=("time_step_retained_after_value_error",),
        blockers=(blocker,),
        provenance={
            "config": config.to_dict(),
            "time_grid_step": step.to_dict(),
            "error": str(error),
            "model_overrides": [],
            "empirical_model_modified": False,
        },
        pathway_preview=None,
        activation_status="report_only_step_failed_validation",
    )


def _scenario_evidence_classes(preview: DynamicPathwayPreview) -> list[str]:
    categories: list[str] = []
    for unit in _pathway_units(preview):
        for token in _unit_trace_columns(unit)["evidence_class"].split("|"):
            lowered = token.casefold()
            if "engineering" in lowered:
                categories.append("engineering")
            elif "direct" in lowered:
                categories.append("direct")
            elif "scenario_input" in lowered:
                categories.append("scenario_input")
            elif any(marker in lowered for marker in ("proxy", "legume", "lower_bound")):
                categories.append("proxy")
            elif "blocked" in lowered or "missing" in lowered:
                categories.append("blocked")
            elif token:
                categories.append("other")
    return categories


def _scenario_run_trace(run: DynamicProteinScenarioRun) -> dict[str, str]:
    if run.pathway_preview is None:
        return {"evidence_class": "blocked", "source_id": "", "record_id": ""}
    traces = [_unit_trace_columns(unit) for unit in _pathway_units(run.pathway_preview)]
    return {
        "evidence_class": "|".join(
            sorted({item for trace in traces for item in trace["evidence_class"].split("|") if item})
        ),
        "source_id": "|".join(
            sorted({item for trace in traces for item in trace["source_id"].split("|") if item})
        ),
        "record_id": "|".join(run.source_record_ids),
    }


def _grid_base_row(
    run: DynamicProteinScenarioRun,
    *,
    unit: DynamicUnitResult | None = None,
    trace: Mapping[str, str] | None = None,
) -> dict[str, object]:
    trace = trace or _scenario_run_trace(run)
    return _empty_grid_common_row(
        scenario_id=run.scenario_id,
        time_label=run.time_label,
        selected_method=run.selected_method,
        policy_ids="|".join(f"{key}:{value}" for key, value in sorted(run.policy_ids.items())),
        unit_id=unit.unit_id if unit else "",
        evidence_class=trace.get("evidence_class", ""),
        source_id=trace.get("source_id", ""),
        record_id=trace.get("record_id", ""),
        warning="|".join(unit.warnings if unit else run.warnings),
        blocker="|".join(unit.blockers if unit else run.blockers),
    )


def _empty_grid_common_row(
    *,
    scenario_id: str,
    time_label: str,
    selected_method: str,
    policy_ids: str,
    unit_id: str = "",
    evidence_class: str = "",
    source_id: str = "",
    record_id: str = "",
    warning: str = "",
    blocker: str = "",
) -> dict[str, object]:
    return {
        "scenario_id": scenario_id,
        "time_label": time_label,
        "unit_id": unit_id,
        "stream_id": "",
        "kg_per_kg_feed": "",
        "component": "",
        "component_mass_kg_per_kg_feed": "",
        "metadata_pool": "",
        "metadata_mass_kg_per_kg_feed": "",
        "selected_method": selected_method,
        "policy_ids": policy_ids,
        "evidence_class": evidence_class,
        "source_id": source_id,
        "record_id": record_id,
        "warning": warning,
        "blocker": blocker,
    }


def write_proxy_dynamic_protein_pathway_reports(
    preview: DynamicPathwayPreview | None = None,
    *,
    output_dir: str | Path = RESULTS_DIR,
) -> dict[str, str]:
    """Write inspectable stream, unit, and summary CSVs for one preview."""

    preview = preview or preview_closed_proxy_dynamic_protein_pathway()
    target = Path(output_dir)
    target.mkdir(parents=True, exist_ok=True)
    streams_path = target / "proxy_dynamic_protein_pathway_streams.csv"
    units_path = target / "proxy_dynamic_protein_pathway_units.csv"
    summary_path = target / "proxy_dynamic_protein_pathway_summary.csv"
    units = _pathway_units(preview)

    stream_fields = (
        "time_label",
        "unit_id",
        "stream_id",
        "kg_per_kg_feed",
        "component",
        "component_mass_kg_per_kg_feed",
        "metadata_pool",
        "metadata_mass_kg_per_kg_feed",
        "policy_status",
        "evidence_class",
        "source_id",
        "record_id",
        "warning",
        "blocker",
    )
    stream_rows: list[dict[str, object]] = []
    for unit in units:
        trace = _unit_trace_columns(unit)
        for stream in unit.outputs:
            entries = [
                (component, mass, "", "")
                for component, mass in stream.component_masses_kg_per_kg_feed.items()
            ] + [
                ("", "", pool, mass)
                for pool, mass in stream.metadata_pools_kg_per_kg_feed.items()
            ]
            if not entries:
                entries = [("", "", "", "")]
            for component, component_mass, metadata_pool, metadata_mass in entries:
                stream_rows.append({
                    "time_label": preview.time_label,
                    "unit_id": unit.unit_id,
                    "stream_id": stream.stream_id,
                    "kg_per_kg_feed": stream.kg_per_kg_feed,
                    "component": component,
                    "component_mass_kg_per_kg_feed": component_mass,
                    "metadata_pool": metadata_pool,
                    "metadata_mass_kg_per_kg_feed": metadata_mass,
                    **trace,
                })
    _write_dict_rows(streams_path, stream_fields, stream_rows)

    unit_fields = (
        "time_label",
        "unit_id",
        "unit_type",
        "input_streams",
        "output_streams",
        "input_mass_kg_per_kg_feed",
        "output_mass_kg_per_kg_feed",
        "mass_balance_residual_kg_per_kg_feed",
        "identity_closes",
        "policy_status",
        "evidence_class",
        "source_id",
        "record_id",
        "warning",
        "blocker",
        "metrics_json",
    )
    unit_rows = []
    for unit in units:
        unit_rows.append({
            "time_label": preview.time_label,
            "unit_id": unit.unit_id,
            "unit_type": unit.unit_type,
            "input_streams": "|".join(stream.stream_id for stream in unit.inputs),
            "output_streams": "|".join(stream.stream_id for stream in unit.outputs),
            "input_mass_kg_per_kg_feed": unit.mass_balance_summary["input_mass_kg_per_kg_feed"],
            "output_mass_kg_per_kg_feed": unit.mass_balance_summary["output_mass_kg_per_kg_feed"],
            "mass_balance_residual_kg_per_kg_feed": unit.mass_balance_summary["residual_kg_per_kg_feed"],
            "identity_closes": unit.mass_balance_summary["identity_closes"],
            **_unit_trace_columns(unit),
            "metrics_json": json.dumps(unit.metrics, sort_keys=True),
        })
    _write_dict_rows(units_path, unit_fields, unit_rows)

    dried = _output(preview.drying, "dried_protein_product")
    residual_metrics = preview.biogas_mix_preparation.metrics
    summary_fields = (
        "time_label",
        "selected_method",
        "can_drive_proxy_preview",
        "can_drive_simulation",
        "validated_simulation_ready",
        "overall_mass_closes",
        "component_identity_closes",
        "dried_product_kg_per_kg_feed",
        "dried_protein_kg_per_kg_feed",
        "estimated_residual_vs_kg_per_kg_feed",
        "bmp_eligible_vs_kg_per_kg_feed",
        "methane_potential_m3_ch4_per_kg_feed",
        "policy_status",
        "evidence_class",
        "source_id",
        "record_id",
        "warning",
        "blocker",
    )
    unit_traces = [_unit_trace_columns(unit) for unit in units]
    summary_trace = {
        "policy_status": "|".join(sorted({trace["policy_status"] for trace in unit_traces})),
        "evidence_class": "|".join(
            sorted(
                {
                    item
                    for trace in unit_traces
                    for item in trace["evidence_class"].split("|")
                    if item
                }
            )
        ),
        "source_id": "|".join(
            sorted({item for trace in unit_traces for item in trace["source_id"].split("|") if item})
        ),
        "record_id": "|".join(
            sorted({item for trace in unit_traces for item in trace["record_id"].split("|") if item})
        ),
    }
    _write_dict_rows(summary_path, summary_fields, [{
        "time_label": preview.time_label,
        "selected_method": preview.selected_method,
        "can_drive_proxy_preview": preview.can_drive_proxy_preview,
        "can_drive_simulation": preview.can_drive_simulation,
        "validated_simulation_ready": preview.validated_simulation_ready,
        "overall_mass_closes": preview.mass_balance_summary["overall_closes"],
        "component_identity_closes": preview.mass_balance_summary["identity_closes"],
        "dried_product_kg_per_kg_feed": dried.kg_per_kg_feed,
        "dried_protein_kg_per_kg_feed": dried.component_masses_kg_per_kg_feed.get("SolubleProtein", 0.0),
        "estimated_residual_vs_kg_per_kg_feed": residual_metrics.get("estimated_residual_vs_kg_per_kg_feed"),
        "bmp_eligible_vs_kg_per_kg_feed": residual_metrics.get("bmp_eligible_vs_kg_per_kg_feed"),
        "methane_potential_m3_ch4_per_kg_feed": residual_metrics.get("methane_potential_m3_ch4_per_kg_feed"),
        **summary_trace,
        "warning": "|".join(preview.warnings),
        "blocker": "|".join(preview.blockers),
    }])
    return {
        "streams": str(streams_path),
        "units": str(units_path),
        "summary": str(summary_path),
    }


def _pathway_units(preview: DynamicPathwayPreview) -> tuple[DynamicUnitResult, ...]:
    return (
        preview.raw_press,
        preview.first_centrifugation,
        preview.protein_extraction,
        preview.second_centrifugation,
        preview.drying,
        preview.biogas_mix_preparation,
    )


def _unit_trace_columns(unit: DynamicUnitResult) -> dict[str, str]:
    policy = unit.applied_policy
    nested_policy = policy.get("bmp_policy") if isinstance(policy.get("bmp_policy"), dict) else {}
    policy_status = str(policy.get("status") or nested_policy.get("status") or "report_only")
    provenance = policy.get("provenance", {})
    field_classes = _collect_scalar_values(
        provenance.get("field_evidence_class", {}) if isinstance(provenance, Mapping) else {}
    )
    field_classes.update(
        _collect_scalar_values(
            provenance.get("metadata_field_evidence_class", {})
            if isinstance(provenance, Mapping)
            else {}
        )
    )
    evidence_class = "|".join(sorted(field_classes)) or str(
        policy.get("proxy_class")
        or nested_policy.get("proxy_class")
        or "report_only"
    )
    source_ids = sorted(_collect_nested_values(policy, "source_id"))
    record_ids = sorted(
        _collect_nested_values(policy, "record_id")
        | _collect_nested_values(policy, "parameter_id")
    )
    return {
        "policy_status": policy_status,
        "evidence_class": evidence_class,
        "source_id": "|".join(source_ids),
        "record_id": "|".join(record_ids),
        "warning": "|".join(unit.warnings),
        "blocker": "|".join(unit.blockers),
    }


def _collect_scalar_values(value: object) -> set[str]:
    if isinstance(value, Mapping):
        return {
            str(item)
            for item in value.values()
            if isinstance(item, (str, int, float)) and str(item)
        }
    return set()


def _collect_nested_values(value: object, key: str) -> set[str]:
    found: set[str] = set()
    if isinstance(value, Mapping):
        for item_key, item_value in value.items():
            if item_key == key and isinstance(item_value, (str, int, float)) and str(item_value):
                found.add(str(item_value))
            found.update(_collect_nested_values(item_value, key))
    elif isinstance(value, (list, tuple)):
        for item in value:
            found.update(_collect_nested_values(item, key))
    return found


def _write_dict_rows(
    path: Path,
    fieldnames: Sequence[str],
    rows: Iterable[Mapping[str, object]],
) -> None:
    with path.open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def summarize_dynamic_protein_block_resolution(
    preview: DynamicPathwayPreview,
) -> dict[str, object]:
    """Return a JSON-safe unit-by-unit protein-path readiness explanation."""

    brown = _output(preview.raw_press, "brown_juice")
    clarified = _output(preview.first_centrifugation, "clarified_juice")
    dried = _output(preview.drying, "dried_protein_product")
    method_summary = summarize_protein_method_alternatives()
    return {
        "selected_method": preview.selected_method,
        "baseline_method": ProteinExtractionMethod.ISOELECTRIC.value,
        "brown_juice_available": brown.kg_per_kg_feed > 0.0,
        "brown_juice_soluble_protein_available": brown.component_masses_kg_per_kg_feed.get("SolubleProtein", 0.0) > 0.0,
        "first_centrifuge_resolved": not preview.first_centrifugation.blockers,
        "clarified_juice_available": clarified.kg_per_kg_feed > 0.0,
        "selected_extraction_method_resolved": not preview.protein_extraction.blockers,
        "second_centrifuge_resolved": not preview.second_centrifugation.blockers,
        "drying_resolved": not preview.drying.blockers,
        "dried_protein_product_produced": dried.component_masses_kg_per_kg_feed.get("SolubleProtein", 0.0) > 0.0,
        "selected_policy_status": preview.method_policy.get("status", ""),
        "selected_policy_proxy_class": preview.method_policy.get("proxy_class", "none"),
        "inactive_alternative_methods": list(preview.inactive_alternative_methods),
        "alternative_status": method_summary,
        "validated_simulation_blockers": list(preview.blockers),
        "proxy_warnings": list(preview.proxy_warnings),
        "can_drive_proxy_preview": preview.can_drive_proxy_preview,
        "can_drive_simulation": False,
    }


def demo_baseline_operational_policy() -> DynamicOperationalScenario:
    """Return explicit illustrative assumptions for end-to-end mass movement."""

    demo_note = {
        "certainty_class": "demo_engineering_assumption",
        "not_a_project_default": True,
        "scientific_activation": False,
    }
    raw_component_fractions = {
        "Water": 0.15,
        "Ash": 0.50,
        "SolubleProtein": 0.10,
        "SuspendedProtein": 0.80,
        "Glucose": 0.10,
        "Fructose": 0.10,
        "Sucrose": 0.10,
        "Cellulose": 0.90,
        "Hemicellulose": 0.90,
        "Lignin": 0.90,
    }
    raw_metadata_fractions = {
        "fructan": 0.10,
        "residual_unallocated_dry_matter": 0.70,
    }
    return DynamicOperationalScenario(
        scenario_id="demo_baseline_operational_assumptions_v1",
        scenario_name="Demonstration-only dynamic press and protein recovery pathway",
        raw_press_policy=DynamicRawPressPolicy(
            policy_id="demo_raw_press_component_routing_v1",
            component_fractions_to_cake=raw_component_fractions,
            metadata_fractions_to_cake=raw_metadata_fractions,
            provenance=demo_note,
            status="demo_engineering_assumption",
        ),
        first_centrifugation_policy=DynamicCentrifugationPolicy(
            policy_id="demo_first_centrifugation_v1",
            suspended_solids_removal_fraction=0.95,
            suspended_protein_removal_fraction=0.95,
            cell_debris_capture_fraction=0.90,
            soluble_protein_loss_fraction=0.02,
            sugar_loss_fraction=0.01,
            ash_loss_fraction=0.50,
            water_split_to_debris_fraction=0.02,
            provenance=demo_note,
            status="demo_engineering_assumption",
        ),
        protein_extraction_policy=DynamicProteinExtractionPolicy(
            policy_id="demo_generic_protein_extraction_v1",
            method="generic",
            soluble_protein_recovery_fraction=0.75,
            co_precipitated_ash_fraction=0.05,
            co_precipitated_sugar_fraction=0.01,
            water_to_protein_phase_fraction=0.05,
            provenance=demo_note,
            status="demo_engineering_assumption",
        ),
        second_centrifugation_policy=DynamicRecoveryCentrifugationPolicy(
            policy_id="demo_second_centrifugation_v1",
            protein_phase_capture_fraction=0.98,
            soluble_protein_loss_to_supernatant_fraction=0.02,
            water_retention_in_cake_fraction=0.20,
            ash_retention_in_cake_fraction=0.80,
            provenance=demo_note,
            status="demo_engineering_assumption",
        ),
        drying_policy=DynamicDryingPolicy(
            policy_id="demo_protein_drying_v1",
            target_moisture_fraction=0.10,
            provenance=demo_note,
            status="demo_engineering_assumption",
        ),
        include_press_cake_in_biogas_mix=False,
        is_demo=True,
        provenance=demo_note,
    )


def _feed_stream_from_pools(pools: DynamicFeedstockPools) -> DynamicProcessStream:
    metadata = {
        "fructan": pools.fructan_wet_fraction,
        "residual_unallocated_dry_matter": pools.residual_unallocated_dry_matter_wet_fraction,
    }
    return _new_stream(
        "whole_feed",
        pools.time_label,
        dict(pools.component_mass_fractions),
        metadata,
        "whole_feed_pooling",
        "dynamic_raw_press",
        provenance={"pool_policy_id": pools.provenance.get("policy_id")},
    )


def _partition_stream(
    input_stream: DynamicProcessStream,
    component_fractions_to_primary: Mapping[str, float],
    metadata_fractions_to_primary: Mapping[str, float],
    primary_id: str,
    secondary_id: str,
    source_unit: str,
    primary_destination: str,
    secondary_destination: str,
) -> tuple[DynamicProcessStream, DynamicProcessStream]:
    primary_components: dict[str, float] = {}
    secondary_components: dict[str, float] = {}
    for name, mass in input_stream.component_masses_kg_per_kg_feed.items():
        fraction = component_fractions_to_primary.get(name, 0.0)
        _validate_fraction(fraction, f"{name} primary split")
        primary_components[name] = mass * fraction
        secondary_components[name] = mass - primary_components[name]
    primary_metadata: dict[str, float] = {}
    secondary_metadata: dict[str, float] = {}
    for name, mass in input_stream.metadata_pools_kg_per_kg_feed.items():
        fraction = metadata_fractions_to_primary.get(name, 0.0)
        _validate_fraction(fraction, f"{name} primary metadata split")
        primary_metadata[name] = mass * fraction
        secondary_metadata[name] = mass - primary_metadata[name]
    primary = _new_stream(
        primary_id,
        input_stream.time_label,
        primary_components,
        primary_metadata,
        source_unit,
        primary_destination,
    )
    secondary = _new_stream(
        secondary_id,
        input_stream.time_label,
        secondary_components,
        secondary_metadata,
        source_unit,
        secondary_destination,
    )
    return primary, secondary


def _partition_stream_three_way(
    input_stream: DynamicProcessStream,
    component_fractions_to_cake: Mapping[str, float],
    component_fractions_to_juice: Mapping[str, float],
    metadata_fractions_to_cake: Mapping[str, float],
    metadata_fractions_to_juice: Mapping[str, float],
    cake_id: str,
    juice_id: str,
    unrecovered_id: str,
    source_unit: str,
) -> tuple[DynamicProcessStream, DynamicProcessStream, DynamicProcessStream]:
    """Partition without forcing analytical or process closure into two streams."""

    cake_components: dict[str, float] = {}
    juice_components: dict[str, float] = {}
    lost_components: dict[str, float] = {}
    for name, mass in input_stream.component_masses_kg_per_kg_feed.items():
        cake_fraction = component_fractions_to_cake.get(name, 0.0)
        juice_fraction = component_fractions_to_juice.get(name, 0.0)
        _validate_nonclosing_split(cake_fraction, juice_fraction, name)
        cake_components[name] = mass * cake_fraction
        juice_components[name] = mass * juice_fraction
        lost_components[name] = mass * (1.0 - cake_fraction - juice_fraction)

    cake_metadata: dict[str, float] = {}
    juice_metadata: dict[str, float] = {}
    lost_metadata: dict[str, float] = {}
    for name, mass in input_stream.metadata_pools_kg_per_kg_feed.items():
        cake_fraction = metadata_fractions_to_cake.get(name, 0.0)
        juice_fraction = metadata_fractions_to_juice.get(name, 0.0)
        _validate_nonclosing_split(cake_fraction, juice_fraction, name)
        cake_metadata[name] = mass * cake_fraction
        juice_metadata[name] = mass * juice_fraction
        lost_metadata[name] = mass * (1.0 - cake_fraction - juice_fraction)

    common = {"source_boundary": "raw_press", "source_values_normalized": False}
    return (
        _new_stream(
            cake_id,
            input_stream.time_label,
            cake_components,
            cake_metadata,
            source_unit,
            "system_output_external_downstream_scope",
            provenance={**common, "product_role": "recovered_press_cake"},
        ),
        _new_stream(
            juice_id,
            input_stream.time_label,
            juice_components,
            juice_metadata,
            source_unit,
            "first_centrifugation",
            provenance={**common, "product_role": "recovered_raw_green_juice"},
        ),
        _new_stream(
            unrecovered_id,
            input_stream.time_label,
            lost_components,
            lost_metadata,
            source_unit,
            "process_loss_or_holdup_report_only",
            provenance={
                **common,
                "product_role": "explicit_unrecovered_process_inventory",
                "not_a_product_stream": True,
            },
            warnings=("unrecovered process mass retained; fate is not assigned",),
        ),
    )


def _reconcile_raw_press_to_source_stream_yields(
    feed: DynamicProcessStream,
    component_cake: Mapping[str, float],
    component_juice: Mapping[str, float],
    metadata_cake: Mapping[str, float],
    metadata_juice: Mapping[str, float],
    cake_yield: float,
    juice_yield: float,
    fixed_components: set[str],
    fixed_metadata: set[str],
) -> tuple[dict[str, float], dict[str, float], dict[str, float], dict[str, float], dict[str, object]]:
    """Fit unsupported routing to source yields without changing direct splits."""

    _validate_fraction(cake_yield, "source press-cake yield")
    _validate_fraction(juice_yield, "source brown-juice yield")
    if cake_yield + juice_yield > 1.0 + MASS_TOLERANCE:
        raise ValueError("Source raw-press recovered stream yields exceed feed mass.")

    identities: dict[tuple[str, str], float] = {
        **{("component", name): mass for name, mass in feed.component_masses_kg_per_kg_feed.items()},
        **{("metadata", name): mass for name, mass in feed.metadata_pools_kg_per_kg_feed.items()},
    }
    fixed = {
        *(('component', name) for name in fixed_components),
        *(('metadata', name) for name in fixed_metadata),
    }
    cake_fraction = {
        **{("component", name): component_cake[name] for name in feed.component_masses_kg_per_kg_feed},
        **{("metadata", name): metadata_cake[name] for name in feed.metadata_pools_kg_per_kg_feed},
    }
    juice_fraction = {
        **{("component", name): component_juice[name] for name in feed.component_masses_kg_per_kg_feed},
        **{("metadata", name): metadata_juice[name] for name in feed.metadata_pools_kg_per_kg_feed},
    }
    fixed_cake = sum(identities[key] * cake_fraction[key] for key in fixed)
    fixed_juice = sum(identities[key] * juice_fraction[key] for key in fixed)
    adjustable = {key: mass for key, mass in identities.items() if key not in fixed}
    cake_target = cake_yield - fixed_cake
    juice_target = juice_yield - fixed_juice
    if cake_target < -MASS_TOLERANCE or juice_target < -MASS_TOLERANCE:
        raise ValueError("Direct component partitions exceed source raw-press stream yields.")
    if cake_target + juice_target > sum(adjustable.values()) + MASS_TOLERANCE:
        raise ValueError("Source stream yields cannot be reached with unsupported routing capacity.")

    cake_allocations = _weighted_bounded_allocation(
        adjustable,
        {key: mass * cake_fraction[key] for key, mass in adjustable.items()},
        max(cake_target, 0.0),
    )
    remaining = {
        key: mass - cake_allocations.get(key, 0.0) for key, mass in adjustable.items()
    }
    juice_allocations = _weighted_bounded_allocation(
        remaining,
        {key: mass * juice_fraction[key] for key, mass in remaining.items()},
        max(juice_target, 0.0),
    )
    for key, mass in adjustable.items():
        cake_fraction[key] = 0.0 if mass <= MASS_TOLERANCE else cake_allocations[key] / mass
        juice_fraction[key] = 0.0 if mass <= MASS_TOLERANCE else juice_allocations[key] / mass

    component_cake_out = {
        name: cake_fraction[("component", name)] for name in feed.component_masses_kg_per_kg_feed
    }
    component_juice_out = {
        name: juice_fraction[("component", name)] for name in feed.component_masses_kg_per_kg_feed
    }
    metadata_cake_out = {
        name: cake_fraction[("metadata", name)] for name in feed.metadata_pools_kg_per_kg_feed
    }
    metadata_juice_out = {
        name: juice_fraction[("metadata", name)] for name in feed.metadata_pools_kg_per_kg_feed
    }
    return (
        component_cake_out,
        component_juice_out,
        metadata_cake_out,
        metadata_juice_out,
        {
            "policy": "engineering_proxy_closure_to_source_stream_yields",
            "direct_partitions_changed": False,
            "source_stream_yields_normalized": False,
            "target_press_cake_kg_per_kg_feed": cake_yield,
            "target_brown_juice_kg_per_kg_feed": juice_yield,
            "target_unrecovered_kg_per_kg_feed": 1.0 - cake_yield - juice_yield,
            "adjusted_identities": [f"{kind}:{name}" for kind, name in sorted(adjustable)],
        },
    )


def _weighted_bounded_allocation(
    capacities: Mapping[tuple[str, str], float],
    weights: Mapping[tuple[str, str], float],
    target: float,
) -> dict[tuple[str, str], float]:
    """Allocate a target by weights while respecting each identity capacity."""

    allocations = {key: 0.0 for key in capacities}
    active = {key for key, capacity in capacities.items() if capacity > MASS_TOLERANCE}
    remaining_target = target
    while active and remaining_target > MASS_TOLERANCE:
        weight_sum = sum(max(weights.get(key, 0.0), 0.0) for key in active)
        if weight_sum <= MASS_TOLERANCE:
            shares = {
                key: remaining_target * capacities[key] / sum(capacities[item] for item in active)
                for key in active
            }
        else:
            shares = {
                key: remaining_target * max(weights.get(key, 0.0), 0.0) / weight_sum
                for key in active
            }
        capped = False
        for key in tuple(active):
            available = capacities[key] - allocations[key]
            if shares[key] >= available - MASS_TOLERANCE:
                allocations[key] += available
                remaining_target -= available
                active.remove(key)
                capped = True
        if not capped:
            for key, share in shares.items():
                allocations[key] += share
            remaining_target = 0.0
    if remaining_target > 1e-10:
        raise ValueError("Unable to allocate raw-press source stream target within component capacities.")
    return allocations


def _new_stream(
    stream_id: str,
    time_label: str,
    components: Mapping[str, float],
    metadata: Mapping[str, float],
    source_unit: str,
    destination_hint: str,
    *,
    provenance: Mapping[str, object] | None = None,
    warnings: Iterable[str] = (),
) -> DynamicProcessStream:
    clean_components = {name: value for name, value in components.items() if value > MASS_TOLERANCE}
    clean_metadata = {name: value for name, value in metadata.items() if value > MASS_TOLERANCE}
    stream = DynamicProcessStream(
        stream_id=stream_id,
        time_label=time_label,
        kg_per_kg_feed=sum(clean_components.values()) + sum(clean_metadata.values()),
        component_masses_kg_per_kg_feed=dict(sorted(clean_components.items())),
        metadata_pools_kg_per_kg_feed=dict(sorted(clean_metadata.items())),
        source_unit=source_unit,
        destination_hint=destination_hint,
        provenance=dict(provenance or {}),
        warnings=tuple(dict.fromkeys(warnings)),
        can_enter_simulation=False,
    )
    validate_process_stream_mass_balance(stream)
    return stream


def _copy_stream(
    stream: DynamicProcessStream,
    stream_id: str,
    source_unit: str,
    destination_hint: str,
    *,
    warning: str = "",
) -> DynamicProcessStream:
    return _new_stream(
        stream_id,
        stream.time_label,
        stream.component_masses_kg_per_kg_feed,
        stream.metadata_pools_kg_per_kg_feed,
        source_unit,
        destination_hint,
        provenance={"copied_from": stream.stream_id, "policy_applied": False},
        warnings=(*stream.warnings, *((warning,) if warning else ())),
    )


def _empty_stream(stream_id: str, time_label: str, source_unit: str, destination_hint: str) -> DynamicProcessStream:
    return _new_stream(stream_id, time_label, {}, {}, source_unit, destination_hint)


def _replace_source(stream: DynamicProcessStream, source_unit: str) -> DynamicProcessStream:
    return DynamicProcessStream(
        stream_id=stream.stream_id,
        time_label=stream.time_label,
        kg_per_kg_feed=stream.kg_per_kg_feed,
        component_masses_kg_per_kg_feed=dict(stream.component_masses_kg_per_kg_feed),
        metadata_pools_kg_per_kg_feed=dict(stream.metadata_pools_kg_per_kg_feed),
        source_unit=source_unit,
        destination_hint=stream.destination_hint,
        provenance=dict(stream.provenance),
        warnings=stream.warnings,
        can_enter_simulation=False,
    )


def _unit_result(
    unit_id: str,
    unit_type: str,
    inputs: tuple[DynamicProcessStream, ...],
    outputs: tuple[DynamicProcessStream, ...],
    applied_policy: dict[str, object],
    blockers: tuple[str, ...],
    warnings: tuple[str, ...],
    readiness_flags: dict[str, bool],
    *,
    allow_unresolved_identity: bool = False,
    metrics: Mapping[str, object] | None = None,
) -> DynamicUnitResult:
    balance = _mass_balance(inputs, outputs, allow_unresolved_identity=allow_unresolved_identity)
    if not balance["closes"]:
        raise ValueError(f"{unit_id} failed mass conservation: {balance['residual_kg_per_kg_feed']:.12g}.")
    return DynamicUnitResult(
        unit_id=unit_id,
        unit_type=unit_type,
        time_label=inputs[0].time_label,
        inputs=inputs,
        outputs=outputs,
        applied_policy=applied_policy,
        blockers=tuple(dict.fromkeys(blockers)),
        warnings=tuple(dict.fromkeys(warnings)),
        mass_balance_summary=balance,
        readiness_flags=readiness_flags,
        metrics=dict(metrics or {}),
    )


def _mass_balance(
    inputs: Sequence[DynamicProcessStream],
    outputs: Sequence[DynamicProcessStream],
    *,
    allow_unresolved_identity: bool = False,
) -> dict[str, object]:
    input_mass = sum(stream.kg_per_kg_feed for stream in inputs)
    output_mass = sum(stream.kg_per_kg_feed for stream in outputs)
    residual = input_mass - output_mass
    input_components: dict[str, float] = {}
    output_components: dict[str, float] = {}
    input_metadata: dict[str, float] = {}
    output_metadata: dict[str, float] = {}
    for stream in inputs:
        validate_process_stream_mass_balance(stream)
        _accumulate(input_components, stream.component_masses_kg_per_kg_feed)
        _accumulate(input_metadata, stream.metadata_pools_kg_per_kg_feed)
    for stream in outputs:
        validate_process_stream_mass_balance(stream)
        _accumulate(output_components, stream.component_masses_kg_per_kg_feed)
        _accumulate(output_metadata, stream.metadata_pools_kg_per_kg_feed)
    component_residuals = {
        name: input_components.get(name, 0.0) - output_components.get(name, 0.0)
        for name in sorted(set(input_components) | set(output_components))
    }
    metadata_residuals = {
        name: input_metadata.get(name, 0.0) - output_metadata.get(name, 0.0)
        for name in sorted(set(input_metadata) | set(output_metadata))
    }
    overall_closes = abs(residual) <= MASS_TOLERANCE
    identity_closes = (
        all(abs(value) <= MASS_TOLERANCE for value in component_residuals.values())
        and all(abs(value) <= MASS_TOLERANCE for value in metadata_residuals.values())
    )
    closes = overall_closes and (identity_closes or allow_unresolved_identity)
    return {
        "input_mass_kg_per_kg_feed": input_mass,
        "output_mass_kg_per_kg_feed": output_mass,
        "residual_kg_per_kg_feed": residual,
        "component_residuals_kg_per_kg_feed": component_residuals,
        "metadata_pool_residuals_kg_per_kg_feed": metadata_residuals,
        "overall_closes": overall_closes,
        "identity_closes": identity_closes,
        "unresolved_identity_allowed": allow_unresolved_identity,
        "closes": closes,
    }


def _output(result: DynamicUnitResult, stream_id: str) -> DynamicProcessStream:
    try:
        return next(stream for stream in result.outputs if stream.stream_id == stream_id)
    except StopIteration as error:
        raise KeyError(f"Unit {result.unit_id} has no output stream {stream_id}.") from error


def _accumulate(target: dict[str, float], values: Mapping[str, float]) -> None:
    for name, value in values.items():
        target[name] = target.get(name, 0.0) + value


def _validate_fraction(value: float, label: str) -> None:
    if not isfinite(value) or not 0.0 <= value <= 1.0:
        raise ValueError(f"{label} must be a finite fraction in [0, 1].")


def _validate_nonclosing_split(cake_fraction: float, juice_fraction: float, label: str) -> None:
    _validate_fraction(cake_fraction, f"{label} cake fraction")
    _validate_fraction(juice_fraction, f"{label} juice fraction")
    if cake_fraction + juice_fraction > 1.0 + MASS_TOLERANCE:
        raise ValueError(f"{label} cake and juice fractions exceed 1 without a valid closure.")


def _validated_or_zero(value: float | None, label: str) -> float:
    if value is None:
        return 0.0
    _validate_fraction(value, label)
    return value
