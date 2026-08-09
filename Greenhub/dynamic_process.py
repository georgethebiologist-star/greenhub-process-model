"""Opt-in, report-only dynamic operational process previews.

The objects in this module are plain Python data structures. They do not create
BioSTEAM streams, mutate the empirical flowsheet, or connect to seasonal/API
services. Unsupported coefficients remain blockers; demo assumptions must be
requested explicitly.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from math import isfinite
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


SOLUBLE_SUGARS = ("Glucose", "Fructose", "Sucrose")
STRUCTURAL_FIBERS = ("Cellulose", "Hemicellulose", "Lignin")
PROTEIN_COMPONENTS = ("SolubleProtein", "SuspendedProtein")
MASS_TOLERANCE = 1e-12


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
    metadata_fractions_to_cake: dict[str, float] = field(default_factory=dict)
    provenance: dict[str, object] = field(default_factory=dict)
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
    provenance: dict[str, object] = field(default_factory=dict)
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
    provenance: dict[str, object] = field(default_factory=dict)
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
    provenance: dict[str, object] = field(default_factory=dict)
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
    status: str = "blocked_missing_values"
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
    can_drive_simulation: bool = False
    activation_status: str = "report_only_not_model_active"

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


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
    """Create two raw-press outputs; source concentrate remains benchmark only."""

    feed = _feed_stream_from_pools(dynamic_press_bundle.feed_pools)
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
    result = _unit_result(
        "dynamic_raw_press",
        "raw_press_boundary_adapter",
        (feed,),
        (press_cake, brown_juice),
        applied_policy,
        tuple(dict.fromkeys(blockers)),
        tuple(warnings),
        {
            "two_stream_raw_boundary_created": True,
            "protein_concentrate_active_raw_output": False,
            "brown_juice_partition_ready": not blockers,
        },
        allow_unresolved_identity=policy is None,
    )
    return result


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
    )


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
        wet_cake = cake_from_phase
        final_supernatant = combine_process_streams(
            (extraction_supernatant, phase_loss),
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
    )


def preview_protein_drying(
    wet_protein_cake: DynamicProcessStream,
    policy: DynamicDryingPolicy | None,
) -> DynamicUnitResult:
    """Remove Water only and preserve every non-water mass exactly."""

    blockers: list[str] = []
    warnings: list[str] = []
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
) -> DynamicUnitResult:
    """Combine explicitly routed residuals without running anaerobic digestion."""

    inputs: list[DynamicProcessStream] = [cell_debris, final_supernatant]
    warnings: list[str] = []
    if include_press_cake:
        if press_cake is None:
            raise ValueError("press_cake is required when include_press_cake=True.")
        inputs.append(press_cake)
        warnings.append("press_cake_explicitly_routed_to_biogas_candidate")
    elif press_cake is not None:
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
    readiness = {
        "has_carbohydrates": carbohydrates > 0.0,
        "has_proteins": proteins > 0.0,
        "missing_COD": True,
        "missing_BMP": True,
        "missing_biodegradability": True,
        "missing_nutrient_speciation": True,
        "ad_active": False,
    }
    blockers = (
        "biogas_feed_missing_COD",
        "biogas_feed_missing_BMP",
        "biogas_feed_missing_biodegradability",
        "biogas_feed_missing_nutrient_speciation",
    )
    return _unit_result(
        "biogas_residual_mixer",
        "biogas_feed_preparation_preview",
        tuple(inputs),
        (candidate,),
        {
            "policy_id": "residual_mass_combination_only",
            "include_press_cake": include_press_cake,
            "status": "report_only",
        },
        blockers,
        tuple(warnings),
        readiness,
    )


def preview_baseline_dynamic_operational_scenario(
    *,
    time_label: str = "2026-05",
    feedstock_bundle: DynamicFeedstockInputBundle | None = None,
    pool_policy: DynamicFeedstockPoolPolicy | None = None,
    scenario: DynamicOperationalScenario | None = None,
) -> DynamicPathwayPreview:
    """Run every report-only stage and return partial outputs when blocked."""

    scenario = scenario or DynamicOperationalScenario(
        scenario_id="baseline_dynamic_operational_blocked_v1",
        scenario_name="Conservative baseline dynamic operational preview",
    )
    feedstock_bundle = feedstock_bundle or build_dynamic_feedstock_input_bundle(time_label)
    pool_policy = pool_policy or default_literature_pool_policy()
    pools = build_dynamic_feedstock_pools(feedstock_bundle, pool_policy)
    press_bundle = build_dynamic_press_preview_bundle(pools)
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
        include_press_cake=scenario.include_press_cake_in_biogas_mix,
    )
    final_outputs = [
        _output(drying, "dried_protein_product"),
        _output(drying, "evaporated_water"),
        _output(residual, "biogas_feed_candidate"),
    ]
    if not scenario.include_press_cake_in_biogas_mix:
        final_outputs.append(press_cake)
    units = (raw_press, first, extraction, second, drying, residual)
    blockers = tuple(dict.fromkeys(blocker for unit in units for blocker in unit.blockers))
    warnings = tuple(dict.fromkeys(warning for unit in units for warning in unit.warnings))
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
        can_drive_simulation=False,
    )


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
        include_press_cake_in_biogas_mix=True,
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


def _validated_or_zero(value: float | None, label: str) -> float:
    if value is None:
        return 0.0
    _validate_fraction(value, label)
    return value
