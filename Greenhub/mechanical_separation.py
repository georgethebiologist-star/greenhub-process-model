"""Traceable, report-only dynamic mechanical press preparation.

This module is independent from the empirical BioSTEAM and seasonal pathways.
It audits mechanical evidence, builds opt-in component partition policies, and
previews conservative stream allocations without creating model overrides.
"""

from __future__ import annotations

import csv
from collections import Counter, defaultdict
from dataclasses import asdict, dataclass
from math import isfinite
from pathlib import Path
from typing import Iterable, Mapping, Sequence

from Greenhub.dynamic_feedstock import DynamicFeedstockPools


PROJECT_ROOT = Path(__file__).resolve().parent.parent
MECHANICAL_DATA_DIR = PROJECT_ROOT / "Greenhub" / "data" / "Pre-treatment" / "Mechanical"
MECHANICAL_SOURCE_DATA = MECHANICAL_DATA_DIR / "greenhub_mechanical_pretreatment_pressing_data.csv"
PRESS_PARTITION_EVIDENCE_DATA = (
    MECHANICAL_DATA_DIR / "greenhub_mechanical_separation_component_partitioning.csv"
)
DEFAULT_EVIDENCE_SUMMARY_CSV = PROJECT_ROOT / "Greenhub" / "results" / "mechanical_partition_evidence_summary.csv"
DEFAULT_EVIDENCE_SUMMARY_MARKDOWN = PROJECT_ROOT / "docs" / "mechanical_partition_evidence_summary.md"

CURRENT_PRESS_BOUNDARY = (
    "Small-scale fractionation followed by fermentation/protein precipitation; "
    "final outputs are press cake, brown juice and protein concentrate"
)
CURRENT_PARTITION_SOURCE_ID = "S01_SANTAMARIA_FERNANDEZ_2020"
CURRENT_PARTITION_SPECIES = "Clover grass"
PRESS_STREAM_NAMES = ("press_cake", "brown_juice", "protein_concentrate")
_SOURCE_STREAM_NAMES = {
    "press cake": "press_cake",
    "brown juice": "brown_juice",
    "protein concentrate": "protein_concentrate",
}
_EXACT_POOL_COMPONENT_MAP = {
    "water": ("Water",),
    "ash": ("Ash",),
    "total ash": ("Ash",),
    "cellulose": ("Cellulose",),
    "hemicellulose": ("Hemicellulose",),
    "lignin": ("Lignin",),
    "sucrose": ("Sucrose",),
    "glucose": ("Glucose",),
    "fructose": ("Fructose",),
    "soluble protein": ("SolubleProtein",),
    "insoluble protein": ("SuspendedProtein",),
    "suspended protein": ("SuspendedProtein",),
}
_ELEMENT_METADATA_POOLS = {
    "carbon",
    "total nitrogen",
    "total phosphorus",
    "total potassium",
    "total sulfur",
}
_AGGREGATE_METADATA_POOLS = {"total solids", "volatile solids"}
_TOTAL_PROTEIN_POOLS = {"total protein", "crude protein"}
_TOTAL_SUGAR_POOLS = {"total sugar", "total sugars", "wsc", "total wsc", "water-soluble carbohydrates"}
_TOTAL_FIBER_POOLS = {"total fiber", "total fibre", "ndf", "adf"}


@dataclass(frozen=True)
class MechanicalSeparationYield:
    """One final product-stream yield from a reviewed process boundary."""

    stream_name: str
    fraction_of_feed: float
    source_record_id: str
    source_id: str
    source_title: str
    material: str
    process_step: str
    transferability_class: str
    confidence_class: str
    note: str

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True)
class MechanicalSeparationPolicy:
    """Source-backed total stream-yield policy."""

    yields: tuple[MechanicalSeparationYield, ...]
    policy_id: str = "clover_grass_mechanical_fractionation_s03_v1"
    activation_status: str = "report_only_not_model_active"
    boundary_note: str = (
        "Mechanical fractionation plus downstream protein recovery; these are "
        "not raw pressing-only product streams."
    )

    @property
    def yield_sum(self) -> float:
        return sum(item.fraction_of_feed for item in self.yields)

    def to_dict(self) -> dict[str, object]:
        return {
            "policy_id": self.policy_id,
            "activation_status": self.activation_status,
            "boundary_note": self.boundary_note,
            "yield_sum": self.yield_sum,
            "yields": [item.to_dict() for item in self.yields],
        }


@dataclass(frozen=True)
class PressPartitionEvidence:
    """Immutable source row containing a partition fraction or range."""

    record_id: str
    source_id: str
    source_title: str
    source_type: str
    material: str
    species_or_feedstock: str
    process_boundary: str
    process_step: str
    equipment_type: str
    product_stream: str
    component_or_pool: str
    response_parameter: str
    reported_value: str
    reported_unit: str
    normalized_value: str
    normalized_unit: str
    partition_fraction_raw: str
    partition_fraction: float | None
    mass_yield_fraction: str
    concentration_value: str
    concentration_unit: str
    basis: str
    feed_basis: str
    conditions: str
    transferability_class: str
    confidence_class: str
    source_url_or_doi: str
    page_or_table: str
    exact_quote_or_table_note: str
    activation_recommendation: str
    notes: str
    evidence_class: str
    validation_status: str
    blocked_reasons: tuple[str, ...]

    @property
    def is_eligible(self) -> bool:
        return self.validation_status == "eligible_report_only"

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True)
class PressPartitionContextRecord:
    """Composition, yield, validation, or metadata row without a partition."""

    record_id: str
    source_id: str
    material: str
    species_or_feedstock: str
    process_boundary: str
    process_step: str
    product_stream: str
    component_or_pool: str
    response_parameter: str
    reported_value: str
    reported_unit: str
    normalized_value: str
    normalized_unit: str
    basis: str
    feed_basis: str
    transferability_class: str
    confidence_class: str
    notes: str
    evidence_class: str

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True)
class PressPartitionEvidenceLoadResult:
    """Typed read-only result from the mechanical partition dataset."""

    source_file: str
    records: tuple[PressPartitionEvidence, ...]
    ignored_non_partition_rows: int
    context_records: tuple[PressPartitionContextRecord, ...] = ()

    @property
    def eligible_records(self) -> tuple[PressPartitionEvidence, ...]:
        return tuple(record for record in self.records if record.is_eligible)

    @property
    def blocked_records(self) -> tuple[PressPartitionEvidence, ...]:
        return tuple(record for record in self.records if not record.is_eligible)

    def to_dict(self) -> dict[str, object]:
        return {
            "source_file": self.source_file,
            "candidate_record_count": len(self.records),
            "eligible_record_count": len(self.eligible_records),
            "blocked_record_count": len(self.blocked_records),
            "ignored_non_partition_rows": self.ignored_non_partition_rows,
            "records": [record.to_dict() for record in self.records],
            "context_records": [record.to_dict() for record in self.context_records],
        }


@dataclass(frozen=True)
class PressPartitionTripletSummary:
    """Three-stream availability and closure for one source component pool."""

    source_id: str
    species_or_feedstock: str
    process_boundary: str
    component_or_pool: str
    record_ids: tuple[str, ...]
    stream_shares: dict[str, float]
    complete_three_stream_triplet: bool
    boundary_matches: bool
    closure_sum: float | None
    closure_within_tolerance: bool
    evidence_class: str
    disposition: str
    reasons: tuple[str, ...]

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True)
class PressPartitionEvidenceSummary:
    """JSON-safe audit summary of candidate and contextual mechanical rows."""

    source_file: str
    candidate_record_count: int
    context_record_count: int
    eligible_scalar_count: int
    blocked_record_count: int
    status_counts: dict[str, int]
    blocked_reason_counts: dict[str, int]
    evidence_class_counts: dict[str, int]
    component_pool_counts: dict[str, int]
    product_stream_counts: dict[str, int]
    complete_triplets: tuple[PressPartitionTripletSummary, ...]
    close_but_not_usable: tuple[PressPartitionTripletSummary, ...]
    fallback_candidates: tuple[PressPartitionTripletSummary, ...]
    metadata_or_validation_record_ids: tuple[str, ...]
    warnings: tuple[str, ...]

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True)
class WaterClosureCorrectionPolicy:
    """Explicit permission to normalize one selected Water triplet."""

    policy_id: str
    rationale: str
    explicitly_enabled: bool = True

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True)
class TotalProteinPartitionFallbackPolicy:
    """Explicit permission to proxy total protein across solubility classes."""

    policy_id: str
    rationale: str
    explicitly_enabled: bool = True

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True)
class TotalSugarPartitionFallbackPolicy:
    """Explicit permission to proxy total WSC across modeled sugar species."""

    policy_id: str
    rationale: str
    explicitly_enabled: bool = True

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True)
class FiberPartitionFallbackPolicy:
    """Explicit permission to proxy a defensible total-fiber partition."""

    policy_id: str
    rationale: str
    explicitly_enabled: bool = True

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True)
class ExplicitPressPartitionAssumption:
    """Caller-supplied report-only component partition with provenance."""

    component: str
    shares: dict[str, float]
    assumption_id: str
    rationale: str
    source_id: str = ""
    notes: str = ""

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True)
class PressComponentPartitionRule:
    """One applied, blocked, or metadata-only partition decision."""

    rule_id: str
    target_name: str
    target_kind: str
    source_pool: str
    rule_type: str
    status: str
    stream_shares: dict[str, float]
    original_stream_shares: dict[str, float]
    original_closure_sum: float | None
    certainty_class: str
    source_record_ids: tuple[str, ...]
    source_id: str
    material: str
    process_boundary: str
    basis: str
    transferability_class: str
    confidence_class: str
    notes: str
    warnings: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True)
class PressComponentPartitionPolicy:
    """Explicit report-only rule collection for one mechanical boundary."""

    policy_id: str
    process_boundary: str
    source_id: str
    species_or_feedstock: str
    rules: tuple[PressComponentPartitionRule, ...]
    allowed_metadata_only_pools: tuple[str, ...]
    fallback_status: dict[str, bool]
    activation_status: str = "report_only_not_model_active"

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True)
class PressPartitionPolicyBuildResult:
    """Candidate policy plus explicit applied/blocked decisions."""

    policy: PressComponentPartitionPolicy
    applied_rules: tuple[PressComponentPartitionRule, ...]
    blocked_rules: tuple[PressComponentPartitionRule, ...]
    metadata_only_rules: tuple[PressComponentPartitionRule, ...]
    unmapped_components: tuple[str, ...]
    metadata_only_pools: tuple[str, ...]
    warnings: tuple[str, ...]
    provenance: dict[str, object]

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True)
class PressPartitionSelection:
    """Backward-compatible source selection view."""

    component_partitions: dict[str, dict[str, float]]
    component_provenance: dict[str, tuple[dict[str, object], ...]]
    evidence_only_pools: tuple[str, ...]
    blocked_record_ids: tuple[str, ...]
    warnings: tuple[str, ...]

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True)
class MechanicalSeparationPreview:
    """Mass-conserving component and metadata allocation preview."""

    time_label: str
    stream_masses_kg_per_kg_feed: dict[str, float]
    stream_component_masses_kg_per_kg_feed: dict[str, dict[str, float]]
    stream_metadata_pools_kg_per_kg_feed: dict[str, dict[str, float]]
    unmapped_component_masses_kg_per_kg_feed: dict[str, float]
    unmapped_components: tuple[str, ...]
    unmapped_pool_metadata: dict[str, dict[str, object]]
    component_mass_balance_residuals: dict[str, float]
    stream_mass_balance_summary: dict[str, dict[str, object]]
    applied_partition_rules: tuple[dict[str, object], ...]
    blocked_partition_rules: tuple[dict[str, object], ...]
    blocked_partition_record_ids: tuple[str, ...]
    warnings: tuple[str, ...]
    provenance: dict[str, object]
    can_drive_simulation: bool = False

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


def default_mechanical_separation_policy() -> MechanicalSeparationPolicy:
    """Return the current closed clover-grass final-stream yield policy."""

    source_title = "Potential Nutrient Recovery in a Green Biorefinery for Production of Feed, Fuel and Fertilizer"
    common = {
        "source_id": "S03_SANTAMARIA_2020",
        "source_title": source_title,
        "material": "Clover grass biomass",
        "process_step": "Mechanical fractionation and protein recovery",
        "transferability_class": "A_direct_grass_or_green_forage",
        "confidence_class": "A",
        "note": "Source-reported final product fraction; boundary includes downstream protein recovery.",
    }
    return MechanicalSeparationPolicy(
        yields=(
            MechanicalSeparationYield("press_cake", 0.395, "M068", **common),
            MechanicalSeparationYield("brown_juice", 0.568, "M069", **common),
            MechanicalSeparationYield("protein_concentrate", 0.037, "M070", **common),
        )
    )


def load_press_partition_evidence(
    path: str | Path = PRESS_PARTITION_EVIDENCE_DATA,
    *,
    expected_boundary: str = CURRENT_PRESS_BOUNDARY,
) -> PressPartitionEvidenceLoadResult:
    """Load all partition candidates and retain non-partition context rows."""

    source_path = Path(path)
    candidates: list[PressPartitionEvidence] = []
    context: list[PressPartitionContextRecord] = []
    with source_path.open("r", encoding="utf-8-sig", newline="") as file:
        for row in csv.DictReader(file):
            raw_fraction = str(row.get("partition_fraction", "")).strip()
            if raw_fraction:
                candidates.append(_parse_partition_evidence_row(row, raw_fraction, expected_boundary))
            else:
                context.append(_parse_context_record(row))
    return PressPartitionEvidenceLoadResult(
        source_file=source_path.name,
        records=tuple(candidates),
        ignored_non_partition_rows=len(context),
        context_records=tuple(context),
    )


def summarize_press_partition_evidence(
    evidence: PressPartitionEvidenceLoadResult | None = None,
    *,
    selected_source_id: str = CURRENT_PARTITION_SOURCE_ID,
    selected_species: str = CURRENT_PARTITION_SPECIES,
    selected_boundary: str = CURRENT_PRESS_BOUNDARY,
    closure_tolerance: float = 1e-6,
) -> PressPartitionEvidenceSummary:
    """Summarize statuses, reasons, and complete stream triplets."""

    evidence = evidence or load_press_partition_evidence(expected_boundary=selected_boundary)
    status_counts = Counter(record.validation_status for record in evidence.records)
    reason_counts = Counter(reason for record in evidence.records for reason in record.blocked_reasons)
    class_counts = Counter(record.evidence_class for record in evidence.records)
    class_counts.update(record.evidence_class for record in evidence.context_records)
    pool_counts = Counter(record.component_or_pool for record in evidence.records)
    stream_counts = Counter(record.product_stream for record in evidence.records)

    grouped: dict[tuple[str, str, str, str], list[PressPartitionEvidence]] = defaultdict(list)
    for record in evidence.records:
        grouped[
            (
                record.source_id,
                record.species_or_feedstock,
                record.process_boundary,
                record.component_or_pool.strip().lower(),
            )
        ].append(record)

    triplets: list[PressPartitionTripletSummary] = []
    for (source_id, species, boundary, pool), records in sorted(grouped.items()):
        scalar_stream_records = [
            record
            for record in records
            if record.partition_fraction is not None
            and record.product_stream.strip().lower() in _SOURCE_STREAM_NAMES
        ]
        by_stream = {
            _SOURCE_STREAM_NAMES[record.product_stream.strip().lower()]: record
            for record in scalar_stream_records
        }
        complete = set(by_stream) == set(PRESS_STREAM_NAMES) and len(scalar_stream_records) == 3
        shares = {
            stream: float(record.partition_fraction)
            for stream, record in by_stream.items()
            if record.partition_fraction is not None
        }
        closure_sum = sum(shares.values()) if complete else None
        closure_ok = closure_sum is not None and abs(closure_sum - 1.0) <= closure_tolerance
        boundary_matches = boundary == selected_boundary
        evidence_class = _classify_pool(pool)
        reasons: list[str] = []
        if not complete:
            reasons.append("incomplete_three_stream_partition")
        if not boundary_matches:
            reasons.append("incompatible_process_boundary")
        if complete and not closure_ok:
            reasons.append("component_partition_does_not_close")
        if source_id != selected_source_id or species != selected_species:
            reasons.append("not_selected_source_or_material")
        disposition = _triplet_disposition(evidence_class, complete, boundary_matches, closure_ok)
        triplets.append(
            PressPartitionTripletSummary(
                source_id=source_id,
                species_or_feedstock=species,
                process_boundary=boundary,
                component_or_pool=pool,
                record_ids=tuple(record.record_id for record in scalar_stream_records),
                stream_shares=dict(sorted(shares.items())),
                complete_three_stream_triplet=complete,
                boundary_matches=boundary_matches,
                closure_sum=closure_sum,
                closure_within_tolerance=closure_ok,
                evidence_class=evidence_class,
                disposition=disposition,
                reasons=tuple(reasons),
            )
        )

    selected_triplets = tuple(
        triplet
        for triplet in triplets
        if triplet.source_id == selected_source_id
        and triplet.species_or_feedstock == selected_species
        and triplet.complete_three_stream_triplet
    )
    close_not_usable = tuple(
        triplet
        for triplet in selected_triplets
        if triplet.disposition != "source_backed_component_candidate"
    )
    fallback_candidates = tuple(
        triplet
        for triplet in selected_triplets
        if triplet.disposition.endswith("fallback_candidate")
    )
    metadata_ids = tuple(
        record.record_id
        for record in (*evidence.records, *evidence.context_records)
        if record.evidence_class in {
            "composition_only",
            "element_only_metadata",
            "aggregate_pool_metadata",
            "validation_only",
        }
    )
    warnings = (
        "Source ranges remain ranges; no midpoint was calculated.",
        "Complete elemental triplets are metadata and are not mapped to Ash.",
        "The selected boundary includes downstream protein recovery and is not raw pressing only.",
    )
    return PressPartitionEvidenceSummary(
        source_file=evidence.source_file,
        candidate_record_count=len(evidence.records),
        context_record_count=len(evidence.context_records),
        eligible_scalar_count=len(evidence.eligible_records),
        blocked_record_count=len(evidence.blocked_records),
        status_counts=dict(sorted(status_counts.items())),
        blocked_reason_counts=dict(sorted(reason_counts.items())),
        evidence_class_counts=dict(sorted(class_counts.items())),
        component_pool_counts=dict(sorted(pool_counts.items())),
        product_stream_counts=dict(sorted(stream_counts.items())),
        complete_triplets=selected_triplets,
        close_but_not_usable=close_not_usable,
        fallback_candidates=fallback_candidates,
        metadata_or_validation_record_ids=metadata_ids,
        warnings=warnings,
    )


def write_press_partition_evidence_summary(
    summary: PressPartitionEvidenceSummary,
    *,
    csv_path: str | Path = DEFAULT_EVIDENCE_SUMMARY_CSV,
    markdown_path: str | Path = DEFAULT_EVIDENCE_SUMMARY_MARKDOWN,
) -> dict[str, str]:
    """Write compact evidence audit artifacts to deterministic locations."""

    csv_target = Path(csv_path)
    markdown_target = Path(markdown_path)
    csv_target.parent.mkdir(parents=True, exist_ok=True)
    markdown_target.parent.mkdir(parents=True, exist_ok=True)
    fields = (
        "source_id",
        "species_or_feedstock",
        "component_or_pool",
        "complete_three_stream_triplet",
        "closure_sum",
        "closure_within_tolerance",
        "evidence_class",
        "disposition",
        "record_ids",
        "reasons",
    )
    with csv_target.open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=fields)
        writer.writeheader()
        for triplet in summary.complete_triplets:
            writer.writerow(
                {
                    **{field: getattr(triplet, field) for field in fields if field not in {"record_ids", "reasons"}},
                    "record_ids": "|".join(triplet.record_ids),
                    "reasons": "|".join(triplet.reasons),
                }
            )
    markdown_target.write_text(_evidence_summary_markdown(summary), encoding="utf-8")
    return {"csv": csv_target.name, "markdown": markdown_target.name}


def build_conservative_press_partition_policy(
    evidence: PressPartitionEvidenceLoadResult | None = None,
    *,
    source_id: str = CURRENT_PARTITION_SOURCE_ID,
    species_or_feedstock: str = CURRENT_PARTITION_SPECIES,
    process_boundary: str = CURRENT_PRESS_BOUNDARY,
    closure_tolerance: float = 1e-6,
    water_closure_correction: WaterClosureCorrectionPolicy | None = None,
    total_protein_fallback: TotalProteinPartitionFallbackPolicy | None = None,
    total_sugar_fallback: TotalSugarPartitionFallbackPolicy | None = None,
    fiber_fallback: FiberPartitionFallbackPolicy | None = None,
    explicit_assumptions: Iterable[ExplicitPressPartitionAssumption] = (),
    allowed_metadata_only_pools: Iterable[str] = (),
) -> PressPartitionPolicyBuildResult:
    """Build a candidate policy without activating unsafe evidence by default."""

    evidence = evidence or load_press_partition_evidence(expected_boundary=process_boundary)
    relevant = [
        record
        for record in evidence.records
        if record.source_id == source_id
        and record.species_or_feedstock == species_or_feedstock
        and record.process_boundary == process_boundary
        and record.partition_fraction is not None
        and record.product_stream.strip().lower() in _SOURCE_STREAM_NAMES
    ]
    grouped: dict[str, list[PressPartitionEvidence]] = defaultdict(list)
    for record in relevant:
        grouped[record.component_or_pool.strip().lower()].append(record)

    rules: list[PressComponentPartitionRule] = []
    warnings: list[str] = []
    for pool, records in sorted(grouped.items()):
        triplet = _complete_stream_partition(records)
        evidence_class = _classify_pool(pool)
        if triplet is None:
            rules.append(_blocked_rule(pool, records, "incomplete_three_stream_partition"))
            continue
        original_shares = _shares_from_records(triplet)
        closure_sum = sum(original_shares.values())
        closure_ok = abs(closure_sum - 1.0) <= closure_tolerance
        exact_targets = _EXACT_POOL_COMPONENT_MAP.get(pool, ())

        if exact_targets and closure_ok:
            for target in exact_targets:
                rules.append(
                    _rule_from_records(
                        target,
                        "component",
                        pool,
                        "source_backed",
                        "applied",
                        original_shares,
                        original_shares,
                        closure_sum,
                        "direct_literature",
                        triplet,
                    )
                )
            continue
        if pool == "water" and exact_targets and not closure_ok:
            if water_closure_correction and water_closure_correction.explicitly_enabled:
                corrected = {stream: share / closure_sum for stream, share in original_shares.items()}
                rules.append(
                    _rule_from_records(
                        "Water",
                        "component",
                        pool,
                        "closure_corrected_literature",
                        "applied",
                        corrected,
                        original_shares,
                        closure_sum,
                        "closure_corrected_literature",
                        triplet,
                        warnings=("analytical_closure_corrected",),
                    )
                )
                warnings.append("analytical_closure_corrected")
            else:
                rules.append(_blocked_rule(pool, triplet, f"source_partition_closure_{closure_sum:.6f}"))
            continue
        if pool in _TOTAL_PROTEIN_POOLS:
            _append_fallback_rules(
                rules,
                triplet,
                pool,
                closure_ok,
                total_protein_fallback,
                ("SolubleProtein", "SuspendedProtein"),
                "total_protein_proxy_for_solubility_classes",
                warnings,
            )
            continue
        if pool in _TOTAL_SUGAR_POOLS:
            _append_fallback_rules(
                rules,
                triplet,
                pool,
                closure_ok,
                total_sugar_fallback,
                ("Sucrose", "Glucose", "Fructose", "pool:fructan"),
                "total_wsc_proxy_for_species",
                warnings,
            )
            continue
        if pool in _TOTAL_FIBER_POOLS:
            _append_fallback_rules(
                rules,
                triplet,
                pool,
                closure_ok,
                fiber_fallback,
                ("Cellulose", "Hemicellulose", "Lignin"),
                "total_fiber_proxy_for_structural_species",
                warnings,
            )
            continue
        if evidence_class in {"element_only_metadata", "aggregate_pool_metadata"}:
            rules.append(
                _rule_from_records(
                    pool,
                    "metadata_pool",
                    pool,
                    "metadata_only",
                    "metadata_only",
                    {},
                    original_shares,
                    closure_sum,
                    "direct_literature_metadata",
                    triplet,
                    warnings=("not_mapped_to_model_component",),
                )
            )
            continue
        reason = "component_partition_does_not_close" if not closure_ok else "no_exact_component_mapping"
        rules.append(_blocked_rule(pool, triplet, reason))

    for assumption in explicit_assumptions:
        shares = {str(stream): float(value) for stream, value in assumption.shares.items()}
        _validate_component_partition(assumption.component, shares, set(PRESS_STREAM_NAMES))
        rules = [rule for rule in rules if rule.target_name != assumption.component]
        rules.append(
            PressComponentPartitionRule(
                rule_id=assumption.assumption_id,
                target_name=assumption.component,
                target_kind="component",
                source_pool=assumption.component,
                rule_type="explicit_user_assumption",
                status="applied",
                stream_shares=shares,
                original_stream_shares=shares,
                original_closure_sum=sum(shares.values()),
                certainty_class="explicit_user_assumption",
                source_record_ids=(),
                source_id=assumption.source_id,
                material="user-defined scenario",
                process_boundary=process_boundary,
                basis="component mass fraction of feed component",
                transferability_class="user_scenario",
                confidence_class="user_defined",
                notes=f"{assumption.rationale} {assumption.notes}".strip(),
                warnings=("explicit_user_assumption",),
            )
        )
        warnings.append(f"{assumption.component}:explicit_user_assumption")

    applied = tuple(rule for rule in rules if rule.status == "applied")
    blocked = tuple(rule for rule in rules if rule.status == "blocked")
    metadata_rules = tuple(rule for rule in rules if rule.status == "metadata_only")
    warnings.extend(warning for rule in blocked for warning in rule.warnings)
    applied_targets = {rule.target_name for rule in applied if rule.target_kind == "component"}
    dynamic_components = {
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
    }
    unmapped = tuple(sorted(dynamic_components - applied_targets))
    metadata_pools = tuple(sorted({rule.source_pool for rule in metadata_rules} | {"fructan", "residual_unallocated_dry_matter"}))
    fallback_status = {
        "water_closure_correction": bool(water_closure_correction and water_closure_correction.explicitly_enabled),
        "total_protein": bool(total_protein_fallback and total_protein_fallback.explicitly_enabled),
        "total_sugar_wsc": bool(total_sugar_fallback and total_sugar_fallback.explicitly_enabled),
        "fiber": bool(fiber_fallback and fiber_fallback.explicitly_enabled),
    }
    policy = PressComponentPartitionPolicy(
        policy_id="conservative_dynamic_press_partition_v1",
        process_boundary=process_boundary,
        source_id=source_id,
        species_or_feedstock=species_or_feedstock,
        rules=tuple(rules),
        allowed_metadata_only_pools=tuple(sorted(set(allowed_metadata_only_pools))),
        fallback_status=fallback_status,
    )
    return PressPartitionPolicyBuildResult(
        policy=policy,
        applied_rules=applied,
        blocked_rules=blocked,
        metadata_only_rules=metadata_rules,
        unmapped_components=unmapped,
        metadata_only_pools=metadata_pools,
        warnings=tuple(dict.fromkeys(warnings)),
        provenance={
            "evidence_source_file": evidence.source_file,
            "selected_source_id": source_id,
            "selected_species_or_feedstock": species_or_feedstock,
            "selected_process_boundary": process_boundary,
            "closure_tolerance": closure_tolerance,
            "fallbacks_are_opt_in": True,
            "normal_simulation_integration": False,
        },
    )


def select_source_backed_press_partitions(
    evidence: PressPartitionEvidenceLoadResult,
    *,
    source_id: str = CURRENT_PARTITION_SOURCE_ID,
    species_or_feedstock: str = CURRENT_PARTITION_SPECIES,
    closure_tolerance: float = 1e-6,
    total_protein_fallback: TotalProteinPartitionFallbackPolicy | None = None,
) -> PressPartitionSelection:
    """Return the legacy selection view from the conservative policy builder."""

    result = build_conservative_press_partition_policy(
        evidence,
        source_id=source_id,
        species_or_feedstock=species_or_feedstock,
        closure_tolerance=closure_tolerance,
        total_protein_fallback=total_protein_fallback,
    )
    partitions = {
        rule.target_name: dict(rule.stream_shares)
        for rule in result.applied_rules
        if rule.target_kind == "component"
    }
    provenance = {
        rule.target_name: tuple(
            record.to_dict()
            for record in evidence.records
            if record.record_id in rule.source_record_ids
        )
        for rule in result.applied_rules
        if rule.target_kind == "component"
    }
    blocked_ids = tuple(
        sorted({record_id for rule in result.blocked_rules for record_id in rule.source_record_ids})
    )
    evidence_only = tuple(sorted(rule.source_pool for rule in result.metadata_only_rules))
    return PressPartitionSelection(partitions, provenance, evidence_only, blocked_ids, result.warnings)


def preview_mechanical_separation(
    pools: DynamicFeedstockPools,
    policy: MechanicalSeparationPolicy,
    *,
    partition_evidence: PressPartitionEvidenceLoadResult | None = None,
    partition_policy: PressPartitionPolicyBuildResult | PressComponentPartitionPolicy | None = None,
    component_partition: Mapping[str, Mapping[str, float]] | None = None,
    explicit_assumptions: Iterable[ExplicitPressPartitionAssumption] = (),
    water_closure_correction: WaterClosureCorrectionPolicy | None = None,
    total_protein_fallback: TotalProteinPartitionFallbackPolicy | None = None,
    total_sugar_fallback: TotalSugarPartitionFallbackPolicy | None = None,
    fiber_fallback: FiberPartitionFallbackPolicy | None = None,
    closure_tolerance: float = 1e-6,
) -> MechanicalSeparationPreview:
    """Allocate safe component rules across final streams in kg/kg feed."""

    _validate_policy(policy)
    stream_masses = {item.stream_name: item.fraction_of_feed for item in policy.yields}
    stream_names = set(stream_masses)
    legacy_assumptions = tuple(
        ExplicitPressPartitionAssumption(
            component=str(component),
            shares={str(stream): float(value) for stream, value in shares.items()},
            assumption_id=f"explicit_{component}",
            rationale="Legacy explicit component_partition argument.",
        )
        for component, shares in (component_partition or {}).items()
    )
    all_assumptions = (*explicit_assumptions, *legacy_assumptions)
    if partition_policy is None:
        if partition_evidence is None and not all_assumptions:
            policy_result = _empty_partition_policy_result()
        else:
            policy_result = build_conservative_press_partition_policy(
                partition_evidence,
                closure_tolerance=closure_tolerance,
                water_closure_correction=water_closure_correction,
                total_protein_fallback=total_protein_fallback,
                total_sugar_fallback=total_sugar_fallback,
                fiber_fallback=fiber_fallback,
                explicit_assumptions=all_assumptions,
            )
    elif isinstance(partition_policy, PressPartitionPolicyBuildResult):
        policy_result = partition_policy
        if all_assumptions:
            raise ValueError("Pass explicit assumptions to the policy builder, not with a built policy result.")
    else:
        policy_result = _result_from_policy(partition_policy)
        if all_assumptions:
            raise ValueError("Pass explicit assumptions to the policy builder, not with a policy object.")

    component_rules = {
        rule.target_name: rule
        for rule in policy_result.applied_rules
        if rule.target_kind == "component"
    }
    metadata_rules = {
        rule.target_name.removeprefix("pool:"): rule
        for rule in policy_result.applied_rules
        if rule.target_kind == "metadata_pool"
    }
    stream_components: dict[str, dict[str, float]] = {name: {} for name in stream_masses}
    stream_metadata: dict[str, dict[str, float]] = {name: {} for name in stream_masses}
    unmapped: dict[str, float] = {}
    residuals: dict[str, float] = {}
    warnings: list[str] = [*pools.warnings, *policy_result.warnings]

    for component, wet_fraction in pools.component_mass_fractions.items():
        rule = component_rules.get(component)
        if rule is None:
            unmapped[component] = wet_fraction
            residuals[component] = 0.0
            warnings.append(f"{pools.time_label}:mechanical_separation:{component}:missing_partition")
            continue
        _validate_component_partition(component, rule.stream_shares, stream_names)
        output_total = 0.0
        for stream in stream_masses:
            mass = wet_fraction * rule.stream_shares.get(stream, 0.0)
            stream_components[stream][component] = mass
            output_total += mass
        residual = wet_fraction - output_total
        residuals[component] = residual
        if abs(residual) > 1e-12:
            raise ValueError(f"Component mass balance failed for {component}: residual {residual:.12g}.")

    metadata_masses = _metadata_pool_masses(pools)
    for pool_name, wet_fraction in metadata_masses.items():
        rule = metadata_rules.get(pool_name)
        if rule is None:
            continue
        _validate_component_partition(f"pool:{pool_name}", rule.stream_shares, stream_names)
        for stream in stream_masses:
            stream_metadata[stream][pool_name] = wet_fraction * rule.stream_shares.get(stream, 0.0)

    mass_summary: dict[str, dict[str, object]] = {}
    for stream, stream_yield in stream_masses.items():
        assigned_components = sum(stream_components[stream].values())
        assigned_metadata = sum(stream_metadata[stream].values())
        assigned_total = assigned_components + assigned_metadata
        if assigned_total > stream_yield + 1e-12:
            raise ValueError(
                f"Assigned mass in {stream} ({assigned_total:.12g}) exceeds stream yield ({stream_yield:.12g})."
            )
        mass_summary[stream] = {
            "stream_yield_kg_per_kg_feed": stream_yield,
            "assigned_component_mass_kg_per_kg_feed": assigned_components,
            "assigned_metadata_pool_mass_kg_per_kg_feed": assigned_metadata,
            "total_assigned_mass_kg_per_kg_feed": assigned_total,
            "unassigned_stream_capacity_kg_per_kg_feed": stream_yield - assigned_total,
            "assigned_mass_equals_stream_yield": abs(assigned_total - stream_yield) <= 1e-12,
            "overallocated": False,
        }

    mapped_metadata = set(metadata_rules)
    unmapped_pool_metadata = _unmapped_pool_metadata(pools, mapped_metadata)
    required_pool_blocks = {
        name
        for name, metadata in unmapped_pool_metadata.items()
        if metadata["requires_partition"]
        and name not in policy_result.policy.allowed_metadata_only_pools
    }
    blocked_ids = tuple(
        sorted({record_id for rule in policy_result.blocked_rules for record_id in rule.source_record_ids})
    )
    can_drive = (
        not unmapped
        and not required_pool_blocks
        and not policy_result.blocked_rules
        and all(abs(value) <= 1e-12 for value in residuals.values())
    )
    corrected = any(rule.rule_type == "closure_corrected_literature" for rule in policy_result.applied_rules)
    status = "explicit_only" if partition_evidence is None and partition_policy is None else "partition_policy_reviewed"
    return MechanicalSeparationPreview(
        time_label=pools.time_label,
        stream_masses_kg_per_kg_feed=dict(sorted(stream_masses.items())),
        stream_component_masses_kg_per_kg_feed={
            stream: dict(sorted(values.items())) for stream, values in sorted(stream_components.items())
        },
        stream_metadata_pools_kg_per_kg_feed={
            stream: dict(sorted(values.items())) for stream, values in sorted(stream_metadata.items())
        },
        unmapped_component_masses_kg_per_kg_feed=dict(sorted(unmapped.items())),
        unmapped_components=tuple(sorted(unmapped)),
        unmapped_pool_metadata=unmapped_pool_metadata,
        component_mass_balance_residuals=dict(sorted(residuals.items())),
        stream_mass_balance_summary=dict(sorted(mass_summary.items())),
        applied_partition_rules=tuple(rule.to_dict() for rule in policy_result.applied_rules),
        blocked_partition_rules=tuple(rule.to_dict() for rule in policy_result.blocked_rules),
        blocked_partition_record_ids=blocked_ids,
        warnings=tuple(dict.fromkeys(warnings)),
        provenance={
            "policy": policy.to_dict(),
            "partition_policy": policy_result.policy.to_dict(),
            "feed_pool_boundary": pools.provenance.get("boundary"),
            "feed_pool_policy_id": pools.provenance.get("policy_id"),
            "component_partition_status": status,
            "evidence_source_file": policy_result.provenance.get("evidence_source_file"),
            "source_values_normalized": corrected,
            "normal_simulation_integration": False,
        },
        can_drive_simulation=can_drive,
    )


def _parse_partition_evidence_row(
    row: Mapping[str, str],
    raw_fraction: str,
    expected_boundary: str,
) -> PressPartitionEvidence:
    reasons: list[str] = []
    try:
        fraction = float(raw_fraction)
    except ValueError:
        fraction = None
        reasons.append("non_scalar_partition_fraction")
    if fraction is not None and (not isfinite(fraction) or not 0.0 <= fraction <= 1.0):
        reasons.append("partition_fraction_out_of_bounds")
    boundary = str(row.get("process_boundary", "")).strip()
    if not boundary:
        reasons.append("unclear_process_boundary")
    elif boundary != expected_boundary:
        reasons.append("incompatible_process_boundary")
    product_stream = str(row.get("product_stream", "")).strip()
    if product_stream.lower() not in _SOURCE_STREAM_NAMES:
        reasons.append("incompatible_or_diagnostic_product_stream")
    basis = str(row.get("basis", "")).strip()
    feed_basis = str(row.get("feed_basis", "")).strip()
    if not basis or not feed_basis:
        reasons.append("missing_partition_basis")
    if basis.lower() in {
        "retained protein",
        "inherent liquid",
        "juice and protein recovery",
        "relative to untreated control",
    }:
        reasons.append("incompatible_component_partition_basis")
    pool = str(row.get("component_or_pool", "")).strip()
    values: defaultdict[str, str] = defaultdict(
        str,
        {key: str(value or "").strip() for key, value in row.items()},
    )
    return PressPartitionEvidence(
        record_id=values["record_id"],
        source_id=values["source_id"],
        source_title=values["source_title"],
        source_type=values["source_type"],
        material=values["material"],
        species_or_feedstock=values["species_or_feedstock"],
        process_boundary=boundary,
        process_step=values["process_step"],
        equipment_type=values["equipment_type"],
        product_stream=product_stream,
        component_or_pool=pool,
        response_parameter=values["response_parameter"],
        reported_value=values["reported_value"],
        reported_unit=values["reported_unit"],
        normalized_value=values["normalized_value"],
        normalized_unit=values["normalized_unit"],
        partition_fraction_raw=raw_fraction,
        partition_fraction=fraction,
        mass_yield_fraction=values["mass_yield_fraction"],
        concentration_value=values["concentration_value"],
        concentration_unit=values["concentration_unit"],
        basis=basis,
        feed_basis=feed_basis,
        conditions=values["conditions"],
        transferability_class=values["transferability_class"],
        confidence_class=values["confidence_class"],
        source_url_or_doi=values["source_url_or_doi"],
        page_or_table=values["page_or_table"],
        exact_quote_or_table_note=values["exact_quote_or_table_note"],
        activation_recommendation=values["activation_recommendation"],
        notes=values["notes"],
        evidence_class=_classify_pool(pool.lower()),
        validation_status="blocked_report_only" if reasons else "eligible_report_only",
        blocked_reasons=tuple(dict.fromkeys(reasons)),
    )


def _parse_context_record(row: Mapping[str, str]) -> PressPartitionContextRecord:
    values: defaultdict[str, str] = defaultdict(
        str,
        {key: str(value or "").strip() for key, value in row.items()},
    )
    response = values["response_parameter"].lower()
    if "closure" in response or values["product_stream"].lower() in {"all final streams", "all products"}:
        evidence_class = "validation_only"
    elif values["mass_yield_fraction"]:
        evidence_class = "mass_yield"
    elif values["concentration_value"] or "concentration" in response or "composition" in response:
        evidence_class = "composition_only"
    else:
        evidence_class = _classify_pool(values["component_or_pool"].lower())
    return PressPartitionContextRecord(
        record_id=values["record_id"],
        source_id=values["source_id"],
        material=values["material"],
        species_or_feedstock=values["species_or_feedstock"],
        process_boundary=values["process_boundary"],
        process_step=values["process_step"],
        product_stream=values["product_stream"],
        component_or_pool=values["component_or_pool"],
        response_parameter=values["response_parameter"],
        reported_value=values["reported_value"],
        reported_unit=values["reported_unit"],
        normalized_value=values["normalized_value"],
        normalized_unit=values["normalized_unit"],
        basis=values["basis"],
        feed_basis=values["feed_basis"],
        transferability_class=values["transferability_class"],
        confidence_class=values["confidence_class"],
        notes=values["notes"],
        evidence_class=evidence_class,
    )


def _classify_pool(pool: str) -> str:
    if pool in _ELEMENT_METADATA_POOLS:
        return "element_only_metadata"
    if pool in _AGGREGATE_METADATA_POOLS:
        return "aggregate_pool_metadata"
    if pool in _TOTAL_PROTEIN_POOLS:
        return "total_protein_fallback_candidate"
    if pool in _TOTAL_SUGAR_POOLS:
        return "total_wsc_fallback_candidate"
    if pool in _TOTAL_FIBER_POOLS:
        return "total_fiber_fallback_candidate"
    if pool in _EXACT_POOL_COMPONENT_MAP:
        return "exact_component_candidate"
    return "metadata_only"


def _triplet_disposition(
    evidence_class: str,
    complete: bool,
    boundary_matches: bool,
    closure_ok: bool,
) -> str:
    if not complete:
        return "blocked_incomplete"
    if not boundary_matches:
        return "blocked_wrong_boundary"
    if evidence_class == "exact_component_candidate" and closure_ok:
        return "source_backed_component_candidate"
    if evidence_class == "exact_component_candidate" and not closure_ok:
        return "closure_correction_fallback_candidate"
    if evidence_class.endswith("fallback_candidate"):
        return evidence_class
    return "metadata_or_validation_only"


def _complete_stream_partition(
    records: Iterable[PressPartitionEvidence],
) -> tuple[PressPartitionEvidence, ...] | None:
    by_stream: dict[str, PressPartitionEvidence] = {}
    for record in records:
        stream = _SOURCE_STREAM_NAMES.get(record.product_stream.strip().lower())
        if stream is None or stream in by_stream or record.partition_fraction is None:
            continue
        by_stream[stream] = record
    if set(by_stream) != set(PRESS_STREAM_NAMES):
        return None
    return tuple(by_stream[stream] for stream in PRESS_STREAM_NAMES)


def _shares_from_records(records: Sequence[PressPartitionEvidence]) -> dict[str, float]:
    return {
        _SOURCE_STREAM_NAMES[record.product_stream.strip().lower()]: float(record.partition_fraction)
        for record in records
        if record.partition_fraction is not None
    }


def _rule_from_records(
    target_name: str,
    target_kind: str,
    source_pool: str,
    rule_type: str,
    status: str,
    shares: Mapping[str, float],
    original_shares: Mapping[str, float],
    original_closure_sum: float | None,
    certainty_class: str,
    records: Sequence[PressPartitionEvidence],
    *,
    warnings: tuple[str, ...] = (),
) -> PressComponentPartitionRule:
    first = records[0]
    return PressComponentPartitionRule(
        rule_id=f"{rule_type}:{target_name}",
        target_name=target_name,
        target_kind=target_kind,
        source_pool=source_pool,
        rule_type=rule_type,
        status=status,
        stream_shares=dict(sorted(shares.items())),
        original_stream_shares=dict(sorted(original_shares.items())),
        original_closure_sum=original_closure_sum,
        certainty_class=certainty_class,
        source_record_ids=tuple(record.record_id for record in records),
        source_id=first.source_id,
        material=f"{first.material}; {first.species_or_feedstock}",
        process_boundary=first.process_boundary,
        basis=first.basis,
        transferability_class=first.transferability_class,
        confidence_class=first.confidence_class,
        notes=" | ".join(record.notes for record in records if record.notes),
        warnings=warnings,
    )


def _blocked_rule(
    source_pool: str,
    records: Sequence[PressPartitionEvidence],
    reason: str,
) -> PressComponentPartitionRule:
    shares = _shares_from_records(records)
    return _rule_from_records(
        source_pool,
        "metadata_pool",
        source_pool,
        "blocked",
        "blocked",
        {},
        shares,
        sum(shares.values()) if shares else None,
        "blocked",
        records,
        warnings=(reason,),
    )


def _append_fallback_rules(
    rules: list[PressComponentPartitionRule],
    records: Sequence[PressPartitionEvidence],
    pool: str,
    closure_ok: bool,
    fallback: object | None,
    targets: Sequence[str],
    rule_type: str,
    warnings: list[str],
) -> None:
    enabled = bool(fallback and getattr(fallback, "explicitly_enabled", False))
    shares = _shares_from_records(records)
    if not closure_ok:
        rules.append(_blocked_rule(pool, records, "aggregate_partition_does_not_close"))
        return
    if not enabled:
        rules.append(_blocked_rule(pool, records, f"{rule_type}_not_enabled"))
        return
    for target in targets:
        target_kind = "metadata_pool" if target.startswith("pool:") else "component"
        rules.append(
            _rule_from_records(
                target,
                target_kind,
                pool,
                rule_type,
                "applied",
                shares,
                shares,
                sum(shares.values()),
                rule_type,
                records,
                warnings=(f"{rule_type}:species_behavior_not_observed",),
            )
        )
    warnings.append(f"{pool}:{rule_type}:explicitly_enabled")


def _empty_partition_policy_result() -> PressPartitionPolicyBuildResult:
    policy = PressComponentPartitionPolicy(
        policy_id="empty_dynamic_press_partition_preview",
        process_boundary=CURRENT_PRESS_BOUNDARY,
        source_id="",
        species_or_feedstock="",
        rules=(),
        allowed_metadata_only_pools=(),
        fallback_status={
            "water_closure_correction": False,
            "total_protein": False,
            "total_sugar_wsc": False,
            "fiber": False,
        },
    )
    return PressPartitionPolicyBuildResult(
        policy=policy,
        applied_rules=(),
        blocked_rules=(),
        metadata_only_rules=(),
        unmapped_components=(),
        metadata_only_pools=(),
        warnings=(),
        provenance={"evidence_source_file": None, "normal_simulation_integration": False},
    )


def _result_from_policy(policy: PressComponentPartitionPolicy) -> PressPartitionPolicyBuildResult:
    return PressPartitionPolicyBuildResult(
        policy=policy,
        applied_rules=tuple(rule for rule in policy.rules if rule.status == "applied"),
        blocked_rules=tuple(rule for rule in policy.rules if rule.status == "blocked"),
        metadata_only_rules=tuple(rule for rule in policy.rules if rule.status == "metadata_only"),
        unmapped_components=(),
        metadata_only_pools=(),
        warnings=tuple(warning for rule in policy.rules for warning in rule.warnings),
        provenance={"evidence_source_file": None, "normal_simulation_integration": False},
    )


def _metadata_pool_masses(pools: DynamicFeedstockPools) -> dict[str, float]:
    return {
        "fructan": pools.fructan_wet_fraction,
        "hexose_subtotal": pools.hexose_wet_fraction,
        "residual_unallocated_dry_matter": pools.residual_unallocated_dry_matter_wet_fraction,
    }


def _unmapped_pool_metadata(
    pools: DynamicFeedstockPools,
    mapped_pools: set[str] | None = None,
) -> dict[str, dict[str, object]]:
    mapped_pools = mapped_pools or set()
    wet_fractions = _metadata_pool_masses(pools)
    metadata: dict[str, dict[str, object]] = {}
    for name in pools.metadata_only_pools:
        if name in mapped_pools:
            continue
        metadata[name] = {
            "wet_fraction_kg_per_kg_feed": wet_fractions.get(name),
            "requires_partition": name != "hexose_subtotal",
            "mass_accounting_role": (
                "subtotal_already_represented_by_glucose_and_fructose"
                if name == "hexose_subtotal"
                else "unmapped_feed_pool"
            ),
            "pool_metadata": pools.pool_metadata.get(name, {}),
        }
    return dict(sorted(metadata.items()))


def _validate_component_partition(
    component: str,
    shares: Mapping[str, float],
    stream_names: set[str],
) -> None:
    unknown = sorted(set(shares) - stream_names)
    if unknown:
        raise ValueError(f"Unknown separation stream(s) for {component}: {', '.join(unknown)}.")
    if any(not isfinite(value) or value < 0.0 for value in shares.values()):
        raise ValueError(f"Partition shares for {component} must be finite and non-negative.")
    if abs(sum(shares.values()) - 1.0) > 1e-12:
        raise ValueError(f"Partition shares for {component} must sum to 1.0.")


def _validate_policy(policy: MechanicalSeparationPolicy) -> None:
    if not policy.yields:
        raise ValueError("Mechanical separation policy requires at least one stream yield.")
    for item in policy.yields:
        if not isfinite(item.fraction_of_feed) or item.fraction_of_feed < 0.0:
            raise ValueError(f"Invalid yield for stream {item.stream_name}.")
    if abs(policy.yield_sum - 1.0) > 1e-9:
        raise ValueError(f"Mechanical separation yields must close to 1.0; got {policy.yield_sum:.12g}.")


def _evidence_summary_markdown(summary: PressPartitionEvidenceSummary) -> str:
    lines = [
        "# Mechanical Partition Evidence Summary",
        "",
        "This report audits source evidence only. It does not activate dynamic or empirical calculations.",
        "",
        "## Record Status",
        "",
        f"- Candidate partition rows: `{summary.candidate_record_count}`",
        f"- Context/composition/yield rows: `{summary.context_record_count}`",
        f"- Eligible scalar rows at the selected boundary: `{summary.eligible_scalar_count}`",
        f"- Blocked candidate rows: `{summary.blocked_record_count}`",
        "",
        "## Selected Complete Triplets",
        "",
        "| Pool | Closure | Class | Disposition |",
        "|---|---:|---|---|",
    ]
    for triplet in summary.complete_triplets:
        closure = "" if triplet.closure_sum is None else f"{triplet.closure_sum:.6f}"
        lines.append(
            f"| {triplet.component_or_pool} | {closure} | {triplet.evidence_class} | {triplet.disposition} |"
        )
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "Water is the only exact component candidate. Its selected shares total `1.017012`, so the conservative policy blocks it unless an explicit closure-correction policy is supplied.",
            "TS, VS, C, N, P, K, and S are aggregate or elemental metadata and are not mapped to GreenHub components.",
            "Protein, WSC species, ash, and structural-fiber components do not have complete source-compatible triplets for this selected boundary.",
            "",
            "## Warnings",
            "",
        ]
    )
    lines.extend(f"- {warning}" for warning in summary.warnings)
    return "\n".join(lines) + "\n"
