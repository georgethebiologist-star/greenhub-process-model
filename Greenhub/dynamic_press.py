"""Report-only dynamic press bundles and downstream readiness previews."""

from __future__ import annotations

import csv
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable

from Greenhub.dynamic_feedstock import (
    DynamicFeedstockInputBundle,
    DynamicFeedstockPoolPolicy,
    DynamicFeedstockPools,
    build_dynamic_feedstock_pools,
)
from Greenhub.mechanical_separation import (
    DEFAULT_EVIDENCE_SUMMARY_CSV,
    DEFAULT_EVIDENCE_SUMMARY_MARKDOWN,
    ExplicitPressPartitionAssumption,
    FiberPartitionFallbackPolicy,
    MechanicalSeparationPolicy,
    MechanicalSeparationPreview,
    PressPartitionEvidenceLoadResult,
    PressPartitionPolicyBuildResult,
    TotalProteinPartitionFallbackPolicy,
    TotalSugarPartitionFallbackPolicy,
    WaterClosureCorrectionPolicy,
    build_conservative_press_partition_policy,
    default_mechanical_separation_policy,
    load_press_partition_evidence,
    preview_mechanical_separation,
    summarize_press_partition_evidence,
    write_press_partition_evidence_summary,
)


PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_DYNAMIC_PRESS_CSV = PROJECT_ROOT / "Greenhub" / "results" / "dynamic_press_preview.csv"
DEFAULT_DYNAMIC_PRESS_COMPONENTS_CSV = (
    PROJECT_ROOT / "Greenhub" / "results" / "dynamic_press_stream_components.csv"
)
DEFAULT_DYNAMIC_PRESS_MARKDOWN = PROJECT_ROOT / "docs" / "dynamic_press_preview.md"


@dataclass(frozen=True)
class DynamicPressStreamView:
    """One JSON-safe final stream view in kg/kg fresh feed."""

    stream_name: str
    total_stream_mass_kg_per_kg_feed: float
    component_masses_kg_per_kg_feed: dict[str, float]
    metadata_pool_masses_kg_per_kg_feed: dict[str, float]
    assigned_mass_kg_per_kg_feed: float
    unassigned_stream_capacity_kg_per_kg_feed: float

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True)
class DynamicPressReadiness:
    """Conservative downstream-readiness gates for the report-only preview."""

    liquid_has_soluble_protein: bool
    cake_has_suspended_protein: bool
    sugar_partition_ready: bool
    water_partition_ready: bool
    ash_partition_ready: bool
    fiber_partition_ready: bool
    residual_dry_matter_partition_ready: bool
    elemental_nutrient_partition_ready: bool
    can_feed_protein_extraction_preview: bool
    can_feed_ad_preview: bool
    can_feed_nutrient_recovery_preview: bool

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True)
class DynamicPressPreviewBundle:
    """Whole-feed pools, policy, stream views, and readiness in one object."""

    time_label: str
    feed_pools: DynamicFeedstockPools
    separation_policy: MechanicalSeparationPolicy
    partition_policy: PressPartitionPolicyBuildResult
    press_preview: MechanicalSeparationPreview
    press_cake: DynamicPressStreamView
    brown_juice: DynamicPressStreamView
    protein_concentrate: DynamicPressStreamView
    extraction_readiness: DynamicPressReadiness
    blockers: tuple[str, ...]
    activation_status: str = "report_only_not_model_active"

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True)
class ExtractionReadyStreamPreview:
    """Downstream data availability without constructing BioSTEAM streams."""

    time_label: str
    brown_juice_soluble_protein_kg_per_kg_feed: float | None
    brown_juice_sugars_kg_per_kg_feed: dict[str, float]
    brown_juice_water_kg_per_kg_feed: float | None
    brown_juice_ash_kg_per_kg_feed: float | None
    brown_juice_mineral_metadata_kg_per_kg_feed: dict[str, float]
    cake_suspended_protein_kg_per_kg_feed: float | None
    cake_fiber_pools_kg_per_kg_feed: dict[str, float]
    concentrate_protein_kg_per_kg_feed: dict[str, float]
    missing_protein_extraction_requirements: tuple[str, ...]
    missing_ad_requirements: tuple[str, ...]
    missing_nutrient_recovery_requirements: tuple[str, ...]
    warnings: tuple[str, ...]
    can_feed_protein_extraction_preview: bool
    can_feed_ad_preview: bool
    can_feed_nutrient_recovery_preview: bool
    activation_status: str = "report_only_not_biosteam_stream"

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


def build_dynamic_press_preview_bundle(
    bundle_or_pools: DynamicFeedstockInputBundle | DynamicFeedstockPools,
    *,
    pool_policy: DynamicFeedstockPoolPolicy | None = None,
    separation_policy: MechanicalSeparationPolicy | None = None,
    partition_evidence: PressPartitionEvidenceLoadResult | None = None,
    partition_policy: PressPartitionPolicyBuildResult | None = None,
    water_closure_correction: WaterClosureCorrectionPolicy | None = None,
    total_protein_fallback: TotalProteinPartitionFallbackPolicy | None = None,
    total_sugar_fallback: TotalSugarPartitionFallbackPolicy | None = None,
    fiber_fallback: FiberPartitionFallbackPolicy | None = None,
    explicit_assumptions: Iterable[ExplicitPressPartitionAssumption] = (),
    allowed_metadata_only_pools: Iterable[str] = (),
    closure_tolerance: float = 1e-6,
) -> DynamicPressPreviewBundle:
    """Build a report-only press bundle from a resolved bundle or feed pools."""

    if isinstance(bundle_or_pools, DynamicFeedstockPools):
        pools = bundle_or_pools
    else:
        if pool_policy is None:
            raise ValueError("A DynamicFeedstockPoolPolicy is required when building pools from an input bundle.")
        pools = build_dynamic_feedstock_pools(bundle_or_pools, pool_policy)
    separation_policy = separation_policy or default_mechanical_separation_policy()
    evidence = partition_evidence or load_press_partition_evidence()
    policy_result = partition_policy or build_conservative_press_partition_policy(
        evidence,
        closure_tolerance=closure_tolerance,
        water_closure_correction=water_closure_correction,
        total_protein_fallback=total_protein_fallback,
        total_sugar_fallback=total_sugar_fallback,
        fiber_fallback=fiber_fallback,
        explicit_assumptions=explicit_assumptions,
        allowed_metadata_only_pools=allowed_metadata_only_pools,
    )
    preview = preview_mechanical_separation(
        pools,
        separation_policy,
        partition_policy=policy_result,
        closure_tolerance=closure_tolerance,
    )
    views = {
        stream: _stream_view(preview, stream)
        for stream in ("press_cake", "brown_juice", "protein_concentrate")
    }
    readiness, blockers = _readiness(preview, policy_result, views)
    return DynamicPressPreviewBundle(
        time_label=pools.time_label,
        feed_pools=pools,
        separation_policy=separation_policy,
        partition_policy=policy_result,
        press_preview=preview,
        press_cake=views["press_cake"],
        brown_juice=views["brown_juice"],
        protein_concentrate=views["protein_concentrate"],
        extraction_readiness=readiness,
        blockers=blockers,
    )


def build_extraction_ready_stream_preview(
    press_bundle: DynamicPressPreviewBundle,
) -> ExtractionReadyStreamPreview:
    """Expose only mapped downstream quantities and explicit missing gates."""

    juice = press_bundle.brown_juice.component_masses_kg_per_kg_feed
    cake = press_bundle.press_cake.component_masses_kg_per_kg_feed
    concentrate = press_bundle.protein_concentrate.component_masses_kg_per_kg_feed
    metadata = press_bundle.brown_juice.metadata_pool_masses_kg_per_kg_feed
    readiness = press_bundle.extraction_readiness
    protein_missing: list[str] = []
    if not readiness.water_partition_ready:
        protein_missing.append("brown_juice_water_partition")
    if not readiness.liquid_has_soluble_protein:
        protein_missing.append("brown_juice_soluble_protein_partition")
    if "SolubleProtein" not in concentrate and "SuspendedProtein" not in concentrate:
        protein_missing.append("protein_concentrate_protein_partition")

    ad_missing: list[str] = []
    if not readiness.water_partition_ready:
        ad_missing.append("water_partition")
    if not readiness.sugar_partition_ready:
        ad_missing.append("sugar_and_fructan_partition")
    if not readiness.fiber_partition_ready:
        ad_missing.append("structural_fiber_partition")
    if not readiness.residual_dry_matter_partition_ready:
        ad_missing.append("residual_dry_matter_partition")
    if not readiness.liquid_has_soluble_protein or not readiness.cake_has_suspended_protein:
        ad_missing.append("protein_pool_partition")

    nutrient_missing: list[str] = []
    if not readiness.water_partition_ready:
        nutrient_missing.append("water_partition")
    if not readiness.elemental_nutrient_partition_ready:
        nutrient_missing.append("N_P_K_S_species_partition")
    if not readiness.ash_partition_ready:
        nutrient_missing.append("total_ash_partition")

    return ExtractionReadyStreamPreview(
        time_label=press_bundle.time_label,
        brown_juice_soluble_protein_kg_per_kg_feed=juice.get("SolubleProtein"),
        brown_juice_sugars_kg_per_kg_feed={
            component: juice[component]
            for component in ("Sucrose", "Glucose", "Fructose")
            if component in juice
        },
        brown_juice_water_kg_per_kg_feed=juice.get("Water"),
        brown_juice_ash_kg_per_kg_feed=juice.get("Ash"),
        brown_juice_mineral_metadata_kg_per_kg_feed={
            name: value
            for name, value in metadata.items()
            if name in {"total nitrogen", "total phosphorus", "total potassium", "total sulfur"}
        },
        cake_suspended_protein_kg_per_kg_feed=cake.get("SuspendedProtein"),
        cake_fiber_pools_kg_per_kg_feed={
            component: cake[component]
            for component in ("Cellulose", "Hemicellulose", "Lignin")
            if component in cake
        },
        concentrate_protein_kg_per_kg_feed={
            component: concentrate[component]
            for component in ("SolubleProtein", "SuspendedProtein")
            if component in concentrate
        },
        missing_protein_extraction_requirements=tuple(protein_missing),
        missing_ad_requirements=tuple(ad_missing),
        missing_nutrient_recovery_requirements=tuple(nutrient_missing),
        warnings=tuple(dict.fromkeys((*press_bundle.press_preview.warnings, *press_bundle.blockers))),
        can_feed_protein_extraction_preview=readiness.can_feed_protein_extraction_preview,
        can_feed_ad_preview=readiness.can_feed_ad_preview,
        can_feed_nutrient_recovery_preview=readiness.can_feed_nutrient_recovery_preview,
    )


def write_dynamic_press_preview_reports(
    bundles: Iterable[DynamicPressPreviewBundle],
    *,
    summary_csv_path: str | Path = DEFAULT_DYNAMIC_PRESS_CSV,
    components_csv_path: str | Path = DEFAULT_DYNAMIC_PRESS_COMPONENTS_CSV,
    markdown_path: str | Path = DEFAULT_DYNAMIC_PRESS_MARKDOWN,
    write_evidence_summary: bool = True,
) -> dict[str, str]:
    """Write deterministic summary, component, and Markdown preview reports."""

    bundle_list = tuple(bundles)
    if not bundle_list:
        raise ValueError("At least one DynamicPressPreviewBundle is required for reporting.")
    summary_target = Path(summary_csv_path)
    components_target = Path(components_csv_path)
    markdown_target = Path(markdown_path)
    for target in (summary_target, components_target, markdown_target):
        target.parent.mkdir(parents=True, exist_ok=True)

    summary_fields = (
        "time_label",
        "press_cake_yield",
        "brown_juice_yield",
        "protein_concentrate_yield",
        "applied_rule_count",
        "blocked_rule_count",
        "unmapped_component_count",
        "water_partition_ready",
        "protein_extraction_ready",
        "ad_ready",
        "nutrient_recovery_ready",
        "can_drive_simulation",
        "fallbacks_enabled",
        "blockers",
    )
    with summary_target.open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=summary_fields)
        writer.writeheader()
        for bundle in bundle_list:
            readiness = bundle.extraction_readiness
            writer.writerow(
                {
                    "time_label": bundle.time_label,
                    "press_cake_yield": bundle.press_preview.stream_masses_kg_per_kg_feed["press_cake"],
                    "brown_juice_yield": bundle.press_preview.stream_masses_kg_per_kg_feed["brown_juice"],
                    "protein_concentrate_yield": bundle.press_preview.stream_masses_kg_per_kg_feed["protein_concentrate"],
                    "applied_rule_count": len(bundle.partition_policy.applied_rules),
                    "blocked_rule_count": len(bundle.partition_policy.blocked_rules),
                    "unmapped_component_count": len(bundle.press_preview.unmapped_components),
                    "water_partition_ready": readiness.water_partition_ready,
                    "protein_extraction_ready": readiness.can_feed_protein_extraction_preview,
                    "ad_ready": readiness.can_feed_ad_preview,
                    "nutrient_recovery_ready": readiness.can_feed_nutrient_recovery_preview,
                    "can_drive_simulation": bundle.press_preview.can_drive_simulation,
                    "fallbacks_enabled": "|".join(
                        name for name, enabled in bundle.partition_policy.policy.fallback_status.items() if enabled
                    ),
                    "blockers": "|".join(bundle.blockers),
                }
            )

    component_fields = ("time_label", "stream", "record_type", "name", "mass_kg_per_kg_feed")
    with components_target.open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=component_fields)
        writer.writeheader()
        for bundle in bundle_list:
            for stream, values in bundle.press_preview.stream_component_masses_kg_per_kg_feed.items():
                for name, mass in values.items():
                    writer.writerow(
                        {
                            "time_label": bundle.time_label,
                            "stream": stream,
                            "record_type": "component",
                            "name": name,
                            "mass_kg_per_kg_feed": mass,
                        }
                    )
            for stream, values in bundle.press_preview.stream_metadata_pools_kg_per_kg_feed.items():
                for name, mass in values.items():
                    writer.writerow(
                        {
                            "time_label": bundle.time_label,
                            "stream": stream,
                            "record_type": "metadata_pool",
                            "name": name,
                            "mass_kg_per_kg_feed": mass,
                        }
                    )
    markdown_target.write_text(_dynamic_press_markdown(bundle_list), encoding="utf-8")
    artifacts = {
        "summary_csv": summary_target.name,
        "components_csv": components_target.name,
        "markdown": markdown_target.name,
    }
    if write_evidence_summary:
        evidence_summary = summarize_press_partition_evidence()
        evidence_artifacts = write_press_partition_evidence_summary(
            evidence_summary,
            csv_path=DEFAULT_EVIDENCE_SUMMARY_CSV,
            markdown_path=DEFAULT_EVIDENCE_SUMMARY_MARKDOWN,
        )
        artifacts.update({f"evidence_{key}": value for key, value in evidence_artifacts.items()})
    return artifacts


def _stream_view(preview: MechanicalSeparationPreview, stream: str) -> DynamicPressStreamView:
    summary = preview.stream_mass_balance_summary[stream]
    return DynamicPressStreamView(
        stream_name=stream,
        total_stream_mass_kg_per_kg_feed=preview.stream_masses_kg_per_kg_feed[stream],
        component_masses_kg_per_kg_feed=dict(preview.stream_component_masses_kg_per_kg_feed[stream]),
        metadata_pool_masses_kg_per_kg_feed=dict(preview.stream_metadata_pools_kg_per_kg_feed[stream]),
        assigned_mass_kg_per_kg_feed=float(summary["total_assigned_mass_kg_per_kg_feed"]),
        unassigned_stream_capacity_kg_per_kg_feed=float(
            summary["unassigned_stream_capacity_kg_per_kg_feed"]
        ),
    )


def _readiness(
    preview: MechanicalSeparationPreview,
    policy: PressPartitionPolicyBuildResult,
    views: dict[str, DynamicPressStreamView],
) -> tuple[DynamicPressReadiness, tuple[str, ...]]:
    applied_components = {
        rule.target_name
        for rule in policy.applied_rules
        if rule.target_kind == "component"
    }
    applied_metadata = {
        rule.target_name.removeprefix("pool:")
        for rule in policy.applied_rules
        if rule.target_kind == "metadata_pool"
    }
    juice = views["brown_juice"].component_masses_kg_per_kg_feed
    cake = views["press_cake"].component_masses_kg_per_kg_feed
    liquid_has_soluble = juice.get("SolubleProtein", 0.0) > 0.0
    cake_has_suspended = cake.get("SuspendedProtein", 0.0) > 0.0
    sugar_ready = {"Sucrose", "Glucose", "Fructose"} <= applied_components and "fructan" in applied_metadata
    water_ready = "Water" in applied_components
    ash_ready = "Ash" in applied_components
    fiber_ready = {"Cellulose", "Hemicellulose", "Lignin"} <= applied_components
    residual_ready = (
        "residual_unallocated_dry_matter" in applied_metadata
        or "residual_unallocated_dry_matter" in policy.policy.allowed_metadata_only_pools
    )
    nutrient_ready = {
        "total nitrogen",
        "total phosphorus",
        "total potassium",
        "total sulfur",
    } <= applied_metadata
    protein_ready = liquid_has_soluble and water_ready
    ad_ready = (
        water_ready
        and sugar_ready
        and fiber_ready
        and residual_ready
        and liquid_has_soluble
        and cake_has_suspended
    )
    nutrient_recovery_ready = water_ready and ash_ready and nutrient_ready
    readiness = DynamicPressReadiness(
        liquid_has_soluble_protein=liquid_has_soluble,
        cake_has_suspended_protein=cake_has_suspended,
        sugar_partition_ready=sugar_ready,
        water_partition_ready=water_ready,
        ash_partition_ready=ash_ready,
        fiber_partition_ready=fiber_ready,
        residual_dry_matter_partition_ready=residual_ready,
        elemental_nutrient_partition_ready=nutrient_ready,
        can_feed_protein_extraction_preview=protein_ready,
        can_feed_ad_preview=ad_ready,
        can_feed_nutrient_recovery_preview=nutrient_recovery_ready,
    )
    blockers: list[str] = []
    if preview.unmapped_components:
        blockers.append("unmapped_components:" + ",".join(preview.unmapped_components))
    required_unmapped_pools = [
        name
        for name, metadata in preview.unmapped_pool_metadata.items()
        if metadata["requires_partition"] and name not in policy.policy.allowed_metadata_only_pools
    ]
    if required_unmapped_pools:
        blockers.append("unmapped_required_pools:" + ",".join(required_unmapped_pools))
    if policy.blocked_rules:
        blockers.append("blocked_partition_rules:" + ",".join(rule.rule_id for rule in policy.blocked_rules))
    if not nutrient_ready:
        blockers.append("elemental_nutrient_speciation_not_partitioned")
    if not preview.can_drive_simulation:
        blockers.append("normal_simulation_integration_disabled")
    return readiness, tuple(dict.fromkeys(blockers))


def _dynamic_press_markdown(bundles: tuple[DynamicPressPreviewBundle, ...]) -> str:
    first = bundles[0]
    fallback_status = first.partition_policy.policy.fallback_status
    lines = [
        "# Dynamic Press Preview",
        "",
        "This is a report-only dynamic feedstock/separation preparation artifact. It does not modify empirical, seasonal, API, or BioSTEAM calculations.",
        "",
        "## Data Used",
        "",
        "- `greenhub_mechanical_pretreatment_pressing_data.csv`: final stream yields `0.395/0.568/0.037`.",
        "- `greenhub_mechanical_separation_component_partitioning.csv`: component and metadata partition evidence.",
        "- Mechanical `source_register.csv`, `assumption_and_missing_data_register.csv`, and `equation_registry.csv` were audited for boundary and missing-data context.",
        "",
        "## Fallback Status",
        "",
    ]
    lines.extend(f"- `{name}`: `{'enabled' if enabled else 'disabled'}`" for name, enabled in fallback_status.items())
    lines.extend(
        [
            "",
            "## Stream Mass Split",
            "",
            "| Stream | kg/kg feed | Assigned components/pools | Unassigned capacity |",
            "|---|---:|---:|---:|",
        ]
    )
    for stream, summary in first.press_preview.stream_mass_balance_summary.items():
        lines.append(
            f"| {stream} | {summary['stream_yield_kg_per_kg_feed']:.6f} | "
            f"{summary['total_assigned_mass_kg_per_kg_feed']:.6f} | "
            f"{summary['unassigned_stream_capacity_kg_per_kg_feed']:.6f} |"
        )
    readiness = first.extraction_readiness
    lines.extend(
        [
            "",
            "## Downstream Readiness",
            "",
            "| Pathway | Ready |",
            "|---|---|",
            f"| Protein extraction preview | {readiness.can_feed_protein_extraction_preview} |",
            f"| Anaerobic digestion preview | {readiness.can_feed_ad_preview} |",
            f"| Nutrient recovery preview | {readiness.can_feed_nutrient_recovery_preview} |",
            "",
            "## Blockers",
            "",
        ]
    )
    lines.extend(f"- {blocker}" for blocker in first.blockers)
    lines.extend(
        [
            "",
            "## Activation Status",
            "",
            f"`can_drive_simulation = {first.press_preview.can_drive_simulation}`. Unmapped pools are not forced to fill stream yields, and empirical calculations remain independent.",
        ]
    )
    return "\n".join(lines) + "\n"
