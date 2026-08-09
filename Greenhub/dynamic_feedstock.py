"""Preparation layer for future dynamic feedstock calculations.

This module resolves traceable evidence into immutable, per-time-step input
bundles. It deliberately does not create parameter overrides, activate dynamic
resolution mode, or modify the empirical BioSTEAM system.
"""

from __future__ import annotations

import csv
import json
from collections import Counter
from collections.abc import Mapping
from dataclasses import asdict, dataclass, replace
from datetime import date
from math import isfinite
from pathlib import Path
from typing import Iterable

from Greenhub.feedstock_proxy import FeedstockProxyCandidate, feedstock_proxy_resolution_candidates
from Greenhub.component_groups import get_group
from Greenhub.feedstock_resolution import (
    MeasuredFeedstockOverride,
    build_feedstock_evidence_pool,
    can_convert_feedstock_unit,
    expected_feedstock_basis,
    validate_feedstock_candidate_basis,
    validate_feedstock_equation_mapping,
)
from Greenhub.scientific_equations import moisture_wet_basis_from_total_solids
from Greenhub.time_grid import generate_time_grid


PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_CSV_REPORT = PROJECT_ROOT / "Greenhub" / "results" / "dynamic_feedstock_preview.csv"
DEFAULT_MARKDOWN_REPORT = PROJECT_ROOT / "docs" / "dynamic_feedstock_solver_preview.md"
DEFAULT_MEASURED_TEMPLATE = (
    PROJECT_ROOT / "Greenhub" / "data" / "Pre-treatment" / "Feedstock" / "measured_feedstock_template.csv"
)

MEASURED_FEEDSTOCK_COLUMNS = (
    "record_id",
    "canonical_field",
    "value",
    "unit",
    "time_label",
    "start_date",
    "end_date",
    "sample_id",
    "sample_location",
    "feedstock",
    "material_state",
    "measurement_method",
    "lab_reference",
    "source_id",
    "measured_date",
    "data_status",
    "notes",
)

MEASURED_DATA_STATUSES = {"measured_project", "project_measured", "validated_measured"}
MOISTURE_TS_TOLERANCE = 1e-6

FIRST_DYNAMIC_FEEDSTOCK_FIELDS = (
    "moisture_wet_basis",
    "total_solids_wet_basis",
    "volatile_solids_dry_basis",
    "ash_dry_basis",
    "carbon_dry_basis",
    "nitrogen_dry_basis",
    "sulfur_dry_basis",
    "bulk_density",
    "total_protein_dry_basis",
    "extractive_sugars_dry_basis",
)

EVIDENCE_PRIORITY = {
    "measured_project": 1,
    "user_override": 2,
    "direct_literature": 3,
    "derived_from_literature": 4,
    "engineering_assumption": 5,
    "indirect_proxy": 6,
    "missing": 7,
}

_SEASON_MONTHS = {
    "spring": {3, 4, 5},
    "summer": {6, 7, 8},
    "autumn": {9, 10, 11},
}

DEFAULT_ADAPTER_COMPONENT_MAPPINGS: dict[str, dict[str, float]] = {
    "ash_dry_basis": {"Ash": 1.0},
}

ADAPTER_ALLOWED_COMPONENT_TARGETS = {
    "ash_dry_basis": frozenset({"Ash"}),
    "total_protein_dry_basis": frozenset({"SolubleProtein", "SuspendedProtein"}),
    "extractive_sugars_dry_basis": get_group("soluble_sugars"),
}

ADAPTER_REQUIRED_COMPONENT_FIELDS = frozenset(
    {"ash_dry_basis", "total_protein_dry_basis", "extractive_sugars_dry_basis"}
)

ADAPTER_METADATA_REASONS = {
    "total_solids_wet_basis": "Used only to convert dry-basis pools to wet-feed fractions.",
    "volatile_solids_dry_basis": "Aggregate VS has no one-to-one component allocation.",
    "carbon_dry_basis": "Elemental carbon is validation metadata, not a feed component.",
    "nitrogen_dry_basis": "Elemental nitrogen cannot be assigned to a species without speciation data.",
    "sulfur_dry_basis": "Elemental sulfur cannot be assigned to a species without speciation data.",
    "bulk_density": "Bulk density is a physical property, not a component fraction.",
    "total_protein_dry_basis": "Total protein needs an explicit soluble/suspended protein allocation.",
    "extractive_sugars_dry_basis": "Extractive sugars need an explicit soluble-sugar species allocation.",
}


@dataclass(frozen=True)
class DynamicFeedstockFieldValue:
    """One selected or blocked canonical field in a dynamic input bundle."""

    canonical_field: str
    value: float | None
    value_min: float | None
    value_max: float | None
    unit: str
    basis: str
    selected_source: str
    selected_parameter_id: str
    certainty_class: str
    confidence_score: float
    resolution_status: str
    blocked_reason: str
    assumption: str
    provenance: dict[str, object]

    @property
    def resolved(self) -> bool:
        return self.value is not None and not self.blocked_reason

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True)
class MeasuredFeedstockRecord:
    """Validated project measurement with complete CSV provenance."""

    record_id: str
    canonical_field: str
    value: float
    unit: str
    time_label: str | None
    start_date: str
    end_date: str
    sample_id: str
    sample_location: str
    feedstock: str
    material_state: str
    measurement_method: str
    lab_reference: str | None
    source_id: str | None
    measured_date: str
    data_status: str
    notes: str


@dataclass(frozen=True)
class InvalidMeasuredFeedstockRow:
    """Rejected measured-data row retained for a readable validation report."""

    row_number: int
    record_id: str
    canonical_field: str
    time_label: str
    reasons: tuple[str, ...]

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True)
class MeasuredFeedstockLoadResult:
    """Usable measurements plus all non-usable row outcomes."""

    records: tuple[MeasuredFeedstockRecord, ...]
    invalid_rows: tuple[InvalidMeasuredFeedstockRow, ...]
    example_rows_skipped: int
    status_counts: dict[str, int]
    source_name: str

    def summary(self) -> dict[str, object]:
        status = "loaded_with_errors" if self.invalid_rows else "loaded"
        return {
            "status": status,
            "source_name": self.source_name,
            "usable_rows": len(self.records),
            "invalid_rows": len(self.invalid_rows),
            "example_rows_skipped": self.example_rows_skipped,
            "status_counts": dict(self.status_counts),
            "invalid_records": [item.to_dict() for item in self.invalid_rows],
        }


@dataclass(frozen=True)
class _MoistureTSReconciliation:
    fields: tuple[DynamicFeedstockFieldValue, ...]
    status: str
    reconciled_fields: tuple[str, ...]
    conflicts: tuple[dict[str, object], ...]
    warnings: tuple[str, ...]
    authoritative_field: str


@dataclass(frozen=True)
class DynamicFeedstockInputBundle:
    """Resolved dynamic feedstock preparation data for one time step."""

    time_label: str
    fields: tuple[DynamicFeedstockFieldValue, ...]
    unresolved_fields: tuple[str, ...]
    blocked_fields: tuple[str, ...]
    blocked_reasons: dict[str, str]
    assumptions: tuple[str, ...]
    provenance: tuple[dict[str, object], ...]
    warnings: tuple[str, ...]
    confidence_score: float
    allow_indirect: bool
    reconciliation_status: str
    reconciled_fields: tuple[str, ...]
    conflict_count: int
    reconciliation_warnings: tuple[str, ...]
    reconciliation_conflicts: tuple[dict[str, object], ...]
    authoritative_field: str
    measured_data_status: dict[str, object]
    calculation_ready: bool = False

    @property
    def resolved_fields(self) -> tuple[str, ...]:
        return tuple(item.canonical_field for item in self.fields if item.resolved)

    def to_dict(self) -> dict[str, object]:
        return {
            "time_label": self.time_label,
            "fields": [item.to_dict() for item in self.fields],
            "resolved_fields": list(self.resolved_fields),
            "unresolved_fields": list(self.unresolved_fields),
            "blocked_fields": list(self.blocked_fields),
            "blocked_reasons": dict(self.blocked_reasons),
            "assumptions": list(self.assumptions),
            "provenance": [dict(item) for item in self.provenance],
            "warnings": list(self.warnings),
            "confidence_score": self.confidence_score,
            "allow_indirect": self.allow_indirect,
            "reconciliation_status": self.reconciliation_status,
            "reconciled_fields": list(self.reconciled_fields),
            "conflict_count": self.conflict_count,
            "reconciliation_warnings": list(self.reconciliation_warnings),
            "reconciliation_conflicts": [dict(item) for item in self.reconciliation_conflicts],
            "authoritative_field": self.authoritative_field,
            "measured_data_status": dict(self.measured_data_status),
            "calculation_ready": self.calculation_ready,
        }


@dataclass(frozen=True)
class DynamicFeedstockPreviewResult:
    """Read-only output from the dynamic feedstock solver shell."""

    bundles: tuple[DynamicFeedstockInputBundle, ...]
    composition_preview: tuple[dict[str, object], ...]
    unresolved_summary: dict[str, int]
    blocked_summary: dict[str, int]
    confidence_summary: dict[str, int]
    provenance_summary: dict[str, int]
    source_class_summary: dict[str, int]
    warnings: tuple[str, ...]
    allow_indirect: bool
    reconciliation_status_summary: dict[str, int]
    conflict_count: int
    reconciled_fields: tuple[str, ...]
    reconciliation_warnings: tuple[str, ...]
    measured_data_status: dict[str, object]
    calculation_ready: bool = False
    activation_status: str = "dynamic_preparation_report_only"

    def to_dict(self) -> dict[str, object]:
        return {
            "bundles": [item.to_dict() for item in self.bundles],
            "composition_preview": [dict(item) for item in self.composition_preview],
            "unresolved_summary": dict(self.unresolved_summary),
            "blocked_summary": dict(self.blocked_summary),
            "confidence_summary": dict(self.confidence_summary),
            "provenance_summary": dict(self.provenance_summary),
            "source_class_summary": dict(self.source_class_summary),
            "warnings": list(self.warnings),
            "allow_indirect": self.allow_indirect,
            "reconciliation_status_summary": dict(self.reconciliation_status_summary),
            "conflict_count": self.conflict_count,
            "reconciled_fields": list(self.reconciled_fields),
            "reconciliation_warnings": list(self.reconciliation_warnings),
            "measured_data_status": dict(self.measured_data_status),
            "calculation_ready": self.calculation_ready,
            "activation_status": self.activation_status,
        }


@dataclass(frozen=True)
class DynamicFeedProfilePreviewRow:
    """Feed-profile-compatible fractions that remain disconnected from simulations."""

    time_label: str
    moisture_fraction: float | None
    component_mass_fractions: dict[str, float]
    metadata_fields: dict[str, dict[str, object]]
    unmapped_fields: tuple[str, ...]
    warnings: tuple[str, ...]
    provenance: dict[str, object]
    can_drive_simulation: bool

    def to_dict(self) -> dict[str, object]:
        return {
            "time_label": self.time_label,
            "moisture_fraction": self.moisture_fraction,
            "component_mass_fractions": dict(self.component_mass_fractions),
            "metadata_fields": {key: dict(value) for key, value in self.metadata_fields.items()},
            "unmapped_fields": list(self.unmapped_fields),
            "warnings": list(self.warnings),
            "provenance": dict(self.provenance),
            "can_drive_simulation": self.can_drive_simulation,
        }


@dataclass(frozen=True)
class PoolFractionPolicy:
    """One literature pooling fraction and its sensitivity metadata."""

    default_fraction: float
    low_fraction: float
    high_fraction: float
    source_url: str
    certainty_class: str
    formula_surrogate: str
    normalization_note: str
    downstream_relevance: tuple[str, ...]

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True)
class DynamicFeedstockPoolPolicy:
    """Opt-in whole-grass pooling assumptions applied before any press split."""

    protein_pool: dict[str, PoolFractionPolicy]
    wsc_sugar_pool: dict[str, PoolFractionPolicy]
    leaf_dm_pool: dict[str, PoolFractionPolicy]
    fiber_subpool: dict[str, PoolFractionPolicy]
    policy_id: str = "literature_whole_grass_pooling_v1"
    activation_status: str = "opt_in_preview_only"

    @property
    def protein_soluble_fraction_mean(self) -> float:
        return self.protein_pool["soluble_protein"].default_fraction

    @property
    def protein_insoluble_fraction_mean(self) -> float:
        return self.protein_pool["insoluble_protein"].default_fraction

    def to_dict(self) -> dict[str, object]:
        return {
            "policy_id": self.policy_id,
            "activation_status": self.activation_status,
            "protein_pool": {key: value.to_dict() for key, value in self.protein_pool.items()},
            "wsc_sugar_pool": {key: value.to_dict() for key, value in self.wsc_sugar_pool.items()},
            "leaf_dm_pool": {key: value.to_dict() for key, value in self.leaf_dm_pool.items()},
            "fiber_subpool": {key: value.to_dict() for key, value in self.fiber_subpool.items()},
        }


@dataclass(frozen=True)
class DynamicFeedstockPools:
    """Whole-feed wet fractions before pressing or downstream conversion."""

    time_label: str
    water_wet_fraction: float
    ash_wet_fraction: float
    soluble_protein_wet_fraction: float
    insoluble_protein_wet_fraction: float
    fructan_wet_fraction: float
    sucrose_wet_fraction: float
    hexose_wet_fraction: float
    structural_fiber_wet_fraction: float
    cellulose_wet_fraction: float
    hemicellulose_wet_fraction: float
    lignin_wet_fraction: float
    residual_unallocated_dry_matter_wet_fraction: float
    total_allocated_wet_fraction: float
    component_mass_fractions: dict[str, float]
    pool_metadata: dict[str, dict[str, object]]
    metadata_only_pools: tuple[str, ...]
    normalization_records: tuple[str, ...]
    warnings: tuple[str, ...]
    provenance: dict[str, object]
    can_drive_simulation: bool = False

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


class DynamicFeedstockSolver:
    """Build report-only previews without mutating the empirical model."""

    def solve(
        self,
        *,
        start_date: str | None = None,
        end_date: str | None = None,
        time_step: str = "monthly",
        measured_values: Iterable[MeasuredFeedstockOverride] = (),
        measured_data_path: Path | str | None = None,
        user_overrides: Iterable[MeasuredFeedstockOverride] = (),
        allow_user_overrides: bool = False,
        allow_indirect: bool = False,
        candidates: Iterable[FeedstockProxyCandidate] | None = None,
        canonical_fields: Iterable[str] = FIRST_DYNAMIC_FEEDSTOCK_FIELDS,
    ) -> DynamicFeedstockPreviewResult:
        bundles = build_dynamic_feedstock_input_bundles_for_grid(
            start_date=start_date,
            end_date=end_date,
            time_step=time_step,
            measured_values=measured_values,
            measured_data_path=measured_data_path,
            user_overrides=user_overrides,
            allow_user_overrides=allow_user_overrides,
            allow_indirect=allow_indirect,
            candidates=candidates,
            canonical_fields=canonical_fields,
        )
        return _preview_result(bundles, allow_indirect)


def load_measured_feedstock_csv(
    path: Path | str = DEFAULT_MEASURED_TEMPLATE,
) -> MeasuredFeedstockLoadResult:
    """Load validated project measurements without creating model overrides."""

    source_path = Path(path)
    if not source_path.is_file():
        raise FileNotFoundError(f"Measured feedstock CSV not found: {source_path}")
    with source_path.open(newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        missing_columns = [item for item in MEASURED_FEEDSTOCK_COLUMNS if item not in (reader.fieldnames or ())]
        if missing_columns:
            raise ValueError(f"Measured feedstock CSV is missing columns: {', '.join(missing_columns)}")
        rows = list(reader)

    staged: list[tuple[int, MeasuredFeedstockRecord]] = []
    invalid: list[InvalidMeasuredFeedstockRow] = []
    examples = 0
    statuses = Counter()
    for row_number, raw in enumerate(rows, start=2):
        row = {key: str(raw.get(key, "") or "").strip() for key in MEASURED_FEEDSTOCK_COLUMNS}
        status = row["data_status"].casefold()
        statuses[status or "blank"] += 1
        if status == "example_do_not_use":
            examples += 1
            continue
        reasons, value = _validate_measured_csv_row(row)
        if reasons:
            invalid.append(
                InvalidMeasuredFeedstockRow(
                    row_number=row_number,
                    record_id=row["record_id"],
                    canonical_field=row["canonical_field"],
                    time_label=row["time_label"],
                    reasons=tuple(reasons),
                )
            )
            continue
        assert value is not None
        staged.append(
            (
                row_number,
                MeasuredFeedstockRecord(
                    record_id=row["record_id"] or f"row-{row_number}",
                    canonical_field=row["canonical_field"],
                    value=value,
                    unit=row["unit"],
                    time_label=row["time_label"] or None,
                    start_date=row["start_date"],
                    end_date=row["end_date"],
                    sample_id=row["sample_id"],
                    sample_location=row["sample_location"],
                    feedstock=row["feedstock"],
                    material_state=row["material_state"],
                    measurement_method=row["measurement_method"],
                    lab_reference=row["lab_reference"] or None,
                    source_id=row["source_id"] or None,
                    measured_date=row["measured_date"],
                    data_status=status,
                    notes=row["notes"],
                ),
            )
        )

    duplicate_keys = {
        key
        for key, count in Counter((record.canonical_field, record.time_label) for _, record in staged).items()
        if count > 1
    }
    records = []
    for row_number, record in staged:
        if (record.canonical_field, record.time_label) in duplicate_keys:
            invalid.append(
                InvalidMeasuredFeedstockRow(
                    row_number=row_number,
                    record_id=record.record_id,
                    canonical_field=record.canonical_field,
                    time_label=record.time_label or "static",
                    reasons=("duplicate_canonical_field_time_label",),
                )
            )
        else:
            records.append(record)
    return MeasuredFeedstockLoadResult(
        records=tuple(records),
        invalid_rows=tuple(sorted(invalid, key=lambda item: item.row_number)),
        example_rows_skipped=examples,
        status_counts=dict(sorted(statuses.items())),
        source_name=source_path.name,
    )


def _validate_measured_csv_row(row: dict[str, str]) -> tuple[list[str], float | None]:
    reasons: list[str] = []
    status = row["data_status"].casefold()
    field = row["canonical_field"]
    if status not in MEASURED_DATA_STATUSES:
        reasons.append("unsupported_data_status")
    if not field:
        reasons.append("missing_canonical_field")
    elif field not in FIRST_DYNAMIC_FEEDSTOCK_FIELDS:
        reasons.append("unsupported_first_dynamic_field")
    if not row["unit"]:
        reasons.append("missing_unit")
    if not (row["source_id"] or row["lab_reference"]):
        reasons.append("missing_source_id_or_lab_reference")

    try:
        value = float(row["value"])
    except (TypeError, ValueError):
        value = None
        reasons.append("missing_or_non_numeric_value")
    else:
        if not isfinite(value):
            reasons.append("non_finite_value")
        elif field == "bulk_density" and value <= 0.0:
            reasons.append("bulk_density_must_be_positive")
        elif field != "bulk_density" and not 0.0 <= value <= 1.0:
            reasons.append("composition_fraction_outside_0_1")

    time_label = row["time_label"]
    if time_label and not _valid_explicit_time_label(time_label):
        reasons.append("invalid_explicit_time_label")
    for name in ("start_date", "end_date", "measured_date"):
        if row[name] and not _valid_iso_date(row[name]):
            reasons.append(f"invalid_{name}")
    if bool(row["start_date"]) != bool(row["end_date"]):
        reasons.append("incomplete_date_range")
    if row["start_date"] and row["end_date"] and _valid_iso_date(row["start_date"]) and _valid_iso_date(row["end_date"]):
        if date.fromisoformat(row["end_date"]) < date.fromisoformat(row["start_date"]):
            reasons.append("end_date_precedes_start_date")

    if field and row["unit"] and value is not None and isfinite(value):
        basis = validate_feedstock_candidate_basis(field, row["unit"], value)
        policy = can_convert_feedstock_unit(row["unit"], str(basis["expected_unit"]), field)
        if not policy["conversion_allowed"] or policy["conversion_required"]:
            reasons.append(str(policy["conversion_policy_status"]))
    return list(dict.fromkeys(reasons)), value


def _valid_explicit_time_label(value: str) -> bool:
    try:
        if len(value) == 7:
            date.fromisoformat(f"{value}-01")
            return value[4] == "-"
        if len(value) == 10:
            date.fromisoformat(value)
            return True
    except ValueError:
        return False
    return False


def _valid_iso_date(value: str) -> bool:
    try:
        date.fromisoformat(value)
    except ValueError:
        return False
    return True


def _measured_data_status(
    loaded: MeasuredFeedstockLoadResult | None,
    in_memory_rows: int,
) -> dict[str, object]:
    if loaded is None:
        return {
            "status": "in_memory" if in_memory_rows else "not_supplied",
            "source_name": "",
            "usable_rows": in_memory_rows,
            "invalid_rows": 0,
            "example_rows_skipped": 0,
            "status_counts": {},
            "invalid_records": [],
            "in_memory_rows": in_memory_rows,
        }
    summary = loaded.summary()
    summary["in_memory_rows"] = in_memory_rows
    summary["usable_rows"] = int(summary["usable_rows"]) + in_memory_rows
    return summary


def build_dynamic_feedstock_input_bundle(
    time_label: str,
    *,
    measured_values: Iterable[MeasuredFeedstockOverride] = (),
    measured_data_path: Path | str | None = None,
    user_overrides: Iterable[MeasuredFeedstockOverride] = (),
    allow_user_overrides: bool = False,
    allow_indirect: bool = False,
    candidates: Iterable[FeedstockProxyCandidate] | None = None,
    canonical_fields: Iterable[str] = FIRST_DYNAMIC_FEEDSTOCK_FIELDS,
    _measured_load_result: MeasuredFeedstockLoadResult | None = None,
) -> DynamicFeedstockInputBundle:
    """Resolve a non-activating input bundle for one explicit time label."""

    fields = tuple(dict.fromkeys(canonical_fields))
    if not fields:
        raise ValueError("canonical_fields must contain at least one field.")
    loaded = _measured_load_result
    if loaded is None and measured_data_path is not None:
        loaded = load_measured_feedstock_csv(measured_data_path)
    in_memory_measured = tuple(measured_values)
    measured = in_memory_measured + (loaded.records if loaded is not None else ())
    measured_status = _measured_data_status(loaded, len(in_memory_measured))
    overrides = tuple(user_overrides)
    candidate_items = tuple(candidates) if candidates is not None else tuple(feedstock_proxy_resolution_candidates())
    pool = build_feedstock_evidence_pool(measured, overrides, candidate_items)
    evidence_lookup = _evidence_lookup(pool)
    resolved = []
    bundle_warnings: list[str] = []

    for field in fields:
        item, warnings = _resolve_field(
            field,
            time_label,
            measured,
            overrides,
            allow_user_overrides,
            allow_indirect,
            candidate_items,
            pool,
            evidence_lookup,
        )
        resolved.append(item)
        bundle_warnings.extend(warnings)

    reconciliation = _reconcile_moisture_total_solids(time_label, resolved)
    resolved = list(reconciliation.fields)
    bundle_warnings.extend(reconciliation.warnings)
    unresolved = tuple(item.canonical_field for item in resolved if not item.resolved)
    blocked_reasons = {item.canonical_field: item.blocked_reason for item in resolved if item.blocked_reason}
    assumptions = tuple(item.assumption for item in resolved if item.assumption)
    provenance = tuple(item.provenance for item in resolved)
    confidences = [item.confidence_score for item in resolved if item.resolved]
    confidence_score = sum(confidences) / len(confidences) if confidences else 0.0
    return DynamicFeedstockInputBundle(
        time_label=time_label,
        fields=tuple(resolved),
        unresolved_fields=unresolved,
        blocked_fields=tuple(blocked_reasons),
        blocked_reasons=blocked_reasons,
        assumptions=assumptions,
        provenance=provenance,
        warnings=tuple(dict.fromkeys(bundle_warnings)),
        confidence_score=confidence_score,
        allow_indirect=allow_indirect,
        reconciliation_status=reconciliation.status,
        reconciled_fields=reconciliation.reconciled_fields,
        conflict_count=len(reconciliation.conflicts),
        reconciliation_warnings=reconciliation.warnings,
        reconciliation_conflicts=reconciliation.conflicts,
        authoritative_field=reconciliation.authoritative_field,
        measured_data_status=measured_status,
    )


def build_dynamic_feedstock_input_bundles_for_grid(
    *,
    start_date: str | None = None,
    end_date: str | None = None,
    time_step: str = "monthly",
    measured_values: Iterable[MeasuredFeedstockOverride] = (),
    measured_data_path: Path | str | None = None,
    user_overrides: Iterable[MeasuredFeedstockOverride] = (),
    allow_user_overrides: bool = False,
    allow_indirect: bool = False,
    candidates: Iterable[FeedstockProxyCandidate] | None = None,
    canonical_fields: Iterable[str] = FIRST_DYNAMIC_FEEDSTOCK_FIELDS,
) -> tuple[DynamicFeedstockInputBundle, ...]:
    """Use the existing deterministic grid to build one bundle per step."""

    grid = generate_time_grid(start_date, end_date, time_step)
    measured = tuple(measured_values)
    loaded = load_measured_feedstock_csv(measured_data_path) if measured_data_path is not None else None
    overrides = tuple(user_overrides)
    candidate_items = tuple(candidates) if candidates is not None else tuple(feedstock_proxy_resolution_candidates())
    fields = tuple(canonical_fields)
    return tuple(
        build_dynamic_feedstock_input_bundle(
            step.label,
            measured_values=measured,
            measured_data_path=None,
            user_overrides=overrides,
            allow_user_overrides=allow_user_overrides,
            allow_indirect=allow_indirect,
            candidates=candidate_items,
            canonical_fields=fields,
            _measured_load_result=loaded,
        )
        for step in grid
    )


def solve_feedstock_dynamic_preview(**kwargs: object) -> DynamicFeedstockPreviewResult:
    """Convenience entry point for the non-activating solver shell."""

    return DynamicFeedstockSolver().solve(**kwargs)


def default_literature_pool_policy() -> DynamicFeedstockPoolPolicy:
    """Return the user-supplied literature assumptions for whole-grass pooling."""

    protein_url = "https://pmc.ncbi.nlm.nih.gov/articles/PMC11741079/"
    sugar_url = "https://www.nzgajournal.org.nz/index.php/ProNZGA/article/download/2826/2454/4219"
    fiber_url = "https://www.sciencedirect.com/science/article/pii/S0022030213003780"
    certainty = "user_supplied_literature_assumption"
    protein_note = "The supplied 0.50/0.50 means already sum to 1.0; no normalization was required."
    protein_formula = "(C4.94H7.76O1.52N1.28S0.04)n"
    protein_pool = {
        "soluble_protein": PoolFractionPolicy(
            0.5, 0.5, 0.5, protein_url, certainty, protein_formula, protein_note,
            ("protein_extraction", "anaerobic_digestion", "nutrient_recovery"),
        ),
        "insoluble_protein": PoolFractionPolicy(
            0.5, 0.5, 0.5, protein_url, certainty, protein_formula, protein_note,
            ("protein_extraction", "anaerobic_digestion", "nutrient_recovery"),
        ),
    }
    wsc_sugar_pool = _normalized_pool_policy(
        ranges={"fructan": (0.50, 0.70), "sucrose": (0.20, 0.30), "hexose": (0.10, 0.15)},
        source_url=sugar_url,
        certainty_class=certainty,
        formulas={"fructan": "(C6H10O5)n", "sucrose": "C12H22O11", "hexose": "C6H12O6"},
        downstream_relevance=("anaerobic_digestion",),
        pool_name="WSC sugar",
    )
    leaf_dm_pool = _normalized_pool_policy(
        ranges={"structural_fiber": (0.35, 0.70), "non_structural": (0.30, 0.65)},
        source_url=fiber_url,
        certainty_class=certainty,
        formulas={
            "structural_fiber": "aggregate structural carbohydrate/fiber pool",
            "non_structural": "aggregate WSC and protein pool",
        },
        downstream_relevance=("protein_extraction", "anaerobic_digestion"),
        pool_name="leaf dry-matter",
    )
    fiber_subpool = _normalized_pool_policy(
        ranges={"hemicellulose": (0.15, 0.25), "cellulose": (0.18, 0.30), "lignin": (0.02, 0.06)},
        source_url=fiber_url,
        certainty_class=certainty,
        formulas={
            "hemicellulose": "approximately (C5H8O4)n",
            "cellulose": "(C6H10O5)n",
            "lignin": "approximately (C9H10O2(OCH3)0.9-1.7)n; representative metadata only",
        },
        downstream_relevance=("anaerobic_digestion",),
        pool_name="structural fiber",
    )
    return DynamicFeedstockPoolPolicy(protein_pool, wsc_sugar_pool, leaf_dm_pool, fiber_subpool)


def _normalized_pool_policy(
    *,
    ranges: Mapping[str, tuple[float, float]],
    source_url: str,
    certainty_class: str,
    formulas: Mapping[str, str],
    downstream_relevance: tuple[str, ...],
    pool_name: str,
) -> dict[str, PoolFractionPolicy]:
    means = {key: (low + high) / 2.0 for key, (low, high) in ranges.items()}
    denominator = sum(means.values())
    if denominator <= 0.0:
        raise ValueError(f"{pool_name} mean fractions must sum above zero.")
    normalized = {key: value / denominator for key, value in means.items()}
    changed = abs(denominator - 1.0) > 1e-12
    note = (
        f"Raw range means summed to {denominator:.6g} and were normalized to 1.0. "
        "Low/high bounds are preserved as source sensitivity metadata and are not midpoint-derived scenarios."
        if changed
        else "Raw range means already summed to 1.0; low/high bounds are preserved for sensitivity metadata."
    )
    return {
        key: PoolFractionPolicy(
            default_fraction=normalized[key],
            low_fraction=low,
            high_fraction=high,
            source_url=source_url,
            certainty_class=certainty_class,
            formula_surrogate=formulas[key],
            normalization_note=note,
            downstream_relevance=downstream_relevance,
        )
        for key, (low, high) in ranges.items()
    }


def build_dynamic_feedstock_pools(
    bundle: DynamicFeedstockInputBundle,
    policy: DynamicFeedstockPoolPolicy,
) -> DynamicFeedstockPools:
    """Allocate whole-feed pools on a wet basis before any pressing operation."""

    if not isinstance(policy, DynamicFeedstockPoolPolicy):
        raise TypeError("Whole-feed pooling requires an explicit DynamicFeedstockPoolPolicy.")
    by_field = {item.canonical_field: item for item in bundle.fields}
    required = (
        "moisture_wet_basis",
        "total_solids_wet_basis",
        "ash_dry_basis",
        "total_protein_dry_basis",
        "extractive_sugars_dry_basis",
    )
    unresolved = [field for field in required if field not in by_field or not by_field[field].resolved]
    if unresolved:
        raise ValueError(f"Whole-feed pooling requires resolved fields: {', '.join(unresolved)}.")

    moisture = float(by_field["moisture_wet_basis"].value)
    dry_matter = float(by_field["total_solids_wet_basis"].value)
    ash_dm = float(by_field["ash_dry_basis"].value)
    protein_dm = float(by_field["total_protein_dry_basis"].value)
    sugar_dm = float(by_field["extractive_sugars_dry_basis"].value)
    fixed_dm = ash_dm + protein_dm + sugar_dm
    if fixed_dm > 1.0 + 1e-12:
        raise ValueError(
            "Ash, total protein, and extractive sugars exceed total dry matter; evidence values were not normalized."
        )

    structural_default = policy.leaf_dm_pool["structural_fiber"].default_fraction
    available_structural_dm = max(1.0 - fixed_dm, 0.0)
    structural_dm = min(structural_default, available_structural_dm)
    residual_dm = max(1.0 - fixed_dm - structural_dm, 0.0)
    normalization_records = [
        policy.wsc_sugar_pool["fructan"].normalization_note,
        policy.leaf_dm_pool["structural_fiber"].normalization_note,
        policy.fiber_subpool["cellulose"].normalization_note,
    ]
    warnings: list[str] = []
    if structural_dm + 1e-12 < structural_default:
        note = (
            f"Structural fiber default {structural_default:.6g} kg/kg DM was limited to "
            f"{structural_dm:.6g} kg/kg DM after fixed evidence pools; fixed evidence was not rescaled."
        )
        normalization_records.append(note)
        warnings.append(f"{bundle.time_label}:pooling:structural_fiber_limited_by_available_dry_matter")

    soluble_protein = dry_matter * protein_dm * policy.protein_soluble_fraction_mean
    insoluble_protein = dry_matter * protein_dm * policy.protein_insoluble_fraction_mean
    fructan = dry_matter * sugar_dm * policy.wsc_sugar_pool["fructan"].default_fraction
    sucrose = dry_matter * sugar_dm * policy.wsc_sugar_pool["sucrose"].default_fraction
    hexose = dry_matter * sugar_dm * policy.wsc_sugar_pool["hexose"].default_fraction
    glucose = hexose * 0.5
    fructose = hexose * 0.5
    structural_fiber = dry_matter * structural_dm
    cellulose = structural_fiber * policy.fiber_subpool["cellulose"].default_fraction
    hemicellulose = structural_fiber * policy.fiber_subpool["hemicellulose"].default_fraction
    lignin = structural_fiber * policy.fiber_subpool["lignin"].default_fraction
    ash = dry_matter * ash_dm
    residual = dry_matter * residual_dm

    allocated_parts = (
        moisture,
        ash,
        soluble_protein,
        insoluble_protein,
        fructan,
        sucrose,
        hexose,
        cellulose,
        hemicellulose,
        lignin,
        residual,
    )
    if any(not isfinite(value) or value < -1e-12 for value in allocated_parts):
        raise ValueError("Whole-feed pooling produced a non-finite or negative wet fraction.")
    total_allocated = sum(max(value, 0.0) for value in allocated_parts)
    if total_allocated > 1.0 + 1e-9:
        raise ValueError(f"Whole-feed pooling exceeds wet-feed mass by {total_allocated - 1.0:.6g}.")

    component_fractions = {
        "Water": moisture,
        "Ash": ash,
        "SolubleProtein": soluble_protein,
        "SuspendedProtein": insoluble_protein,
        "Fructose": fructose,
        "Glucose": glucose,
        "Sucrose": sucrose,
        "Cellulose": cellulose,
        "Hemicellulose": hemicellulose,
        "Lignin": lignin,
    }
    metadata_only = ("fructan", "hexose_subtotal", "residual_unallocated_dry_matter")
    warnings.extend(
        f"{bundle.time_label}:pooling:{pool}:no_exact_existing_component"
        for pool in metadata_only[:1]
    )
    warnings.append(f"{bundle.time_label}:pooling:hexose_split_50_50_glucose_fructose_assumption")
    warnings.append(f"{bundle.time_label}:pooling:residual_unallocated_dry_matter:explicit_unresolved_pool")
    pool_metadata = _pool_output_metadata(policy, by_field, structural_dm, residual_dm)
    return DynamicFeedstockPools(
        time_label=bundle.time_label,
        water_wet_fraction=moisture,
        ash_wet_fraction=ash,
        soluble_protein_wet_fraction=soluble_protein,
        insoluble_protein_wet_fraction=insoluble_protein,
        fructan_wet_fraction=fructan,
        sucrose_wet_fraction=sucrose,
        hexose_wet_fraction=hexose,
        structural_fiber_wet_fraction=structural_fiber,
        cellulose_wet_fraction=cellulose,
        hemicellulose_wet_fraction=hemicellulose,
        lignin_wet_fraction=lignin,
        residual_unallocated_dry_matter_wet_fraction=residual,
        total_allocated_wet_fraction=total_allocated,
        component_mass_fractions=component_fractions,
        pool_metadata=pool_metadata,
        metadata_only_pools=metadata_only,
        normalization_records=tuple(dict.fromkeys(normalization_records)),
        warnings=tuple(dict.fromkeys(warnings)),
        provenance={
            "policy_id": policy.policy_id,
            "activation_status": policy.activation_status,
            "boundary": "whole_grass_before_press_split",
            "source_fields": {field: by_field[field].to_dict() for field in required},
            "fixed_dry_matter_fraction": fixed_dm,
            "structural_dry_matter_fraction": structural_dm,
            "residual_dry_matter_fraction": residual_dm,
            "normal_simulation_integration": False,
        },
    )


def _pool_output_metadata(
    policy: DynamicFeedstockPoolPolicy,
    by_field: Mapping[str, DynamicFeedstockFieldValue],
    structural_dm: float,
    residual_dm: float,
) -> dict[str, dict[str, object]]:
    metadata = {
        "soluble_protein": policy.protein_pool["soluble_protein"].to_dict(),
        "insoluble_protein": policy.protein_pool["insoluble_protein"].to_dict(),
        "fructan": policy.wsc_sugar_pool["fructan"].to_dict(),
        "sucrose": policy.wsc_sugar_pool["sucrose"].to_dict(),
        "hexose": policy.wsc_sugar_pool["hexose"].to_dict(),
        "glucose": {
            **policy.wsc_sugar_pool["hexose"].to_dict(),
            "default_fraction": policy.wsc_sugar_pool["hexose"].default_fraction * 0.5,
            "low_fraction": policy.wsc_sugar_pool["hexose"].low_fraction * 0.5,
            "high_fraction": policy.wsc_sugar_pool["hexose"].high_fraction * 0.5,
            "formula_surrogate": "C6H12O6",
            "normalization_note": (
                "Assumed 50% of combined hexose subtotal; report-only split until a "
                "source-specific glucose/fructose ratio is available."
            ),
        },
        "fructose": {
            **policy.wsc_sugar_pool["hexose"].to_dict(),
            "default_fraction": policy.wsc_sugar_pool["hexose"].default_fraction * 0.5,
            "low_fraction": policy.wsc_sugar_pool["hexose"].low_fraction * 0.5,
            "high_fraction": policy.wsc_sugar_pool["hexose"].high_fraction * 0.5,
            "formula_surrogate": "C6H12O6",
            "normalization_note": (
                "Assumed 50% of combined hexose subtotal; report-only split until a "
                "source-specific glucose/fructose ratio is available."
            ),
        },
        "structural_fiber": policy.leaf_dm_pool["structural_fiber"].to_dict(),
        "non_structural": policy.leaf_dm_pool["non_structural"].to_dict(),
        "cellulose": policy.fiber_subpool["cellulose"].to_dict(),
        "hemicellulose": policy.fiber_subpool["hemicellulose"].to_dict(),
        "lignin": policy.fiber_subpool["lignin"].to_dict(),
    }
    metadata["structural_fiber"]["applied_dry_matter_fraction"] = structural_dm
    metadata["residual_unallocated_dry_matter"] = {
        "default_fraction": residual_dm,
        "low_fraction": None,
        "high_fraction": None,
        "source_url": "",
        "certainty_class": "calculated_mass_balance_residual",
        "formula_surrogate": "unresolved whole-feed dry-matter pool",
        "normalization_note": "Explicit remainder after ash, protein, WSC, and structural fiber allocation.",
        "downstream_relevance": ("outside_scope",),
    }
    for field, pool in (
        ("moisture_wet_basis", "water"),
        ("ash_dry_basis", "ash"),
    ):
        item = by_field[field]
        metadata[pool] = {
            "default_fraction": item.value,
            "low_fraction": item.value_min,
            "high_fraction": item.value_max,
            "source_url": str(item.provenance.get("doi_or_url", "")),
            "certainty_class": item.certainty_class,
            "formula_surrogate": "H2O" if pool == "water" else "lumped Ash pseudo-component",
            "normalization_note": "Resolved bundle value; no pooling normalization.",
            "downstream_relevance": ("outside_scope",),
        }
    return metadata


def dynamic_bundle_to_feed_profile_row(
    bundle: DynamicFeedstockInputBundle,
    *,
    component_mappings: Mapping[str, Mapping[str, float]] | None = None,
    pool_policy: DynamicFeedstockPoolPolicy | None = None,
) -> DynamicFeedProfilePreviewRow:
    """Translate one validated bundle into a disconnected feed-profile preview row.

    Default mapping is intentionally limited to the exact ``Ash`` pseudo-
    component. Protein and sugar pools require explicit caller-owned allocation
    maps before they can become component fractions.
    """

    if pool_policy is not None and component_mappings and any(
        field in component_mappings for field in ("total_protein_dry_basis", "extractive_sugars_dry_basis")
    ):
        raise ValueError("Pooling policy owns protein and WSC allocations; do not also supply canonical mappings.")
    effective_mappings = dict(component_mappings or {})
    if pool_policy is not None:
        effective_mappings["total_protein_dry_basis"] = {
            "SolubleProtein": pool_policy.protein_soluble_fraction_mean,
            "SuspendedProtein": pool_policy.protein_insoluble_fraction_mean,
        }
    mappings, mapping_sources = _validated_adapter_mappings(effective_mappings)
    by_field = {item.canonical_field: item for item in bundle.fields}
    warnings = list(bundle.warnings)
    metadata: dict[str, dict[str, object]] = {}
    unmapped: list[str] = []
    component_fractions: dict[str, float] = {}
    mapping_provenance: dict[str, object] = {}

    moisture = by_field.get("moisture_wet_basis")
    moisture_fraction = float(moisture.value) if moisture is not None and moisture.resolved else None
    if moisture_fraction is None:
        warnings.append(f"{bundle.time_label}:adapter:moisture_wet_basis_unresolved")

    total_solids = by_field.get("total_solids_wet_basis")
    total_solids_fraction = (
        float(total_solids.value) if total_solids is not None and total_solids.resolved else None
    )
    if total_solids_fraction is None:
        warnings.append(f"{bundle.time_label}:adapter:total_solids_wet_basis_unresolved")

    for item in bundle.fields:
        field = item.canonical_field
        if field == "moisture_wet_basis":
            continue
        allocation = mappings.get(field)
        if allocation is not None and item.resolved and total_solids_fraction is not None:
            assert item.value is not None
            wet_pool_fraction = float(item.value) * total_solids_fraction
            for component, share in allocation.items():
                component_fractions[component] = component_fractions.get(component, 0.0) + wet_pool_fraction * share
            mapping_provenance[field] = {
                "source": mapping_sources[field],
                "dry_basis_value": item.value,
                "total_solids_wet_basis": total_solids_fraction,
                "wet_feed_pool_fraction": wet_pool_fraction,
                "component_allocation": dict(allocation),
                "field_provenance": dict(item.provenance),
            }
            continue

        metadata[field] = item.to_dict()
        unmapped.append(field)
        if allocation is not None and not item.resolved:
            reason = "resolved value is required before component mapping"
        elif allocation is not None and total_solids_fraction is None:
            reason = "total solids is required for dry-to-wet basis conversion"
        else:
            reason = ADAPTER_METADATA_REASONS.get(field, "No reviewed component mapping exists.")
        warnings.append(f"{bundle.time_label}:adapter:{field}:{reason}")

    fraction_total = (moisture_fraction or 0.0) + sum(component_fractions.values())
    fractions_valid = fraction_total <= 1.0 + 1e-12
    if not fractions_valid:
        warnings.append(f"{bundle.time_label}:adapter:mapped_fractions_exceed_wet_feed_mass")

    missing_required_mappings = sorted(ADAPTER_REQUIRED_COMPONENT_FIELDS - set(mappings))
    if missing_required_mappings:
        warnings.append(
            f"{bundle.time_label}:adapter:required_component_mappings_missing:"
            f"{','.join(missing_required_mappings)}"
        )
    invalid_measured_rows = int(bundle.measured_data_status.get("invalid_rows", 0))
    if invalid_measured_rows:
        warnings.append(f"{bundle.time_label}:adapter:invalid_measured_rows_present")

    required_values_resolved = all(
        by_field.get(field) is not None and by_field[field].resolved
        for field in ADAPTER_REQUIRED_COMPONENT_FIELDS
    )
    can_drive = bool(
        moisture_fraction is not None
        and total_solids_fraction is not None
        and not missing_required_mappings
        and required_values_resolved
        and fractions_valid
        and not bundle.unresolved_fields
        and invalid_measured_rows == 0
        and bundle.reconciliation_status not in {"blocked_missing_pair", "not_applicable"}
    )
    base_row = DynamicFeedProfilePreviewRow(
        time_label=bundle.time_label,
        moisture_fraction=moisture_fraction,
        component_mass_fractions=dict(sorted(component_fractions.items())),
        metadata_fields=dict(sorted(metadata.items())),
        unmapped_fields=tuple(sorted(unmapped)),
        warnings=tuple(dict.fromkeys(warnings)),
        provenance={
            "adapter_status": "opt_in_preview_only",
            "bundle_reconciliation_status": bundle.reconciliation_status,
            "bundle_authoritative_field": bundle.authoritative_field,
            "moisture_provenance": moisture.to_dict() if moisture is not None else {},
            "total_solids_provenance": total_solids.to_dict() if total_solids is not None else {},
            "mapping_provenance": mapping_provenance,
            "missing_required_component_mappings": missing_required_mappings,
            "normal_simulation_integration": False,
        },
        can_drive_simulation=can_drive,
    )
    if pool_policy is None:
        return base_row

    pools = build_dynamic_feedstock_pools(bundle, pool_policy)
    pooled_components = dict(base_row.component_mass_fractions)
    for component, fraction in pools.component_mass_fractions.items():
        if component == "Water":
            continue
        pooled_components[component] = fraction
    pooled_metadata = dict(base_row.metadata_fields)
    pooled_metadata["whole_feed_pooling"] = pools.to_dict()
    pooled_unmapped = tuple(
        sorted(set(base_row.unmapped_fields) | {f"pool:{name}" for name in pools.metadata_only_pools})
    )
    pooled_provenance = {
        **base_row.provenance,
        "whole_feed_pooling": pools.provenance,
        "pool_policy": pool_policy.to_dict(),
    }
    return replace(
        base_row,
        component_mass_fractions=dict(sorted(pooled_components.items())),
        metadata_fields=dict(sorted(pooled_metadata.items())),
        unmapped_fields=pooled_unmapped,
        warnings=tuple(dict.fromkeys((*base_row.warnings, *pools.warnings))),
        provenance=pooled_provenance,
        can_drive_simulation=False,
    )


def dynamic_bundles_to_feed_profile_preview(
    bundles: Iterable[DynamicFeedstockInputBundle],
    *,
    component_mappings: Mapping[str, Mapping[str, float]] | None = None,
    pool_policy: DynamicFeedstockPoolPolicy | None = None,
) -> tuple[DynamicFeedProfilePreviewRow, ...]:
    """Translate bundles without registering a profile or changing simulations."""

    return tuple(
        dynamic_bundle_to_feed_profile_row(
            bundle,
            component_mappings=component_mappings,
            pool_policy=pool_policy,
        )
        for bundle in bundles
    )


def _validated_adapter_mappings(
    supplied: Mapping[str, Mapping[str, float]] | None,
) -> tuple[dict[str, dict[str, float]], dict[str, str]]:
    mappings = {field: dict(allocation) for field, allocation in DEFAULT_ADAPTER_COMPONENT_MAPPINGS.items()}
    sources = {field: "reviewed_default_exact_component" for field in mappings}
    for field, allocation in (supplied or {}).items():
        if field not in ADAPTER_ALLOWED_COMPONENT_TARGETS:
            raise ValueError(f"Dynamic adapter has no allowed component targets for '{field}'.")
        values = {str(component): float(share) for component, share in allocation.items()}
        if not values:
            raise ValueError(f"Dynamic adapter mapping for '{field}' cannot be empty.")
        unknown = sorted(set(values) - ADAPTER_ALLOWED_COMPONENT_TARGETS[field])
        if unknown:
            raise ValueError(f"Dynamic adapter mapping for '{field}' has unsupported targets: {', '.join(unknown)}.")
        if any(not isfinite(share) or share < 0.0 for share in values.values()):
            raise ValueError(f"Dynamic adapter mapping shares for '{field}' must be finite and non-negative.")
        if abs(sum(values.values()) - 1.0) > 1e-12:
            raise ValueError(f"Dynamic adapter mapping shares for '{field}' must sum to one.")
        mappings[field] = values
        sources[field] = "explicit_caller_allocation"
    return mappings, sources


def write_dynamic_feedstock_preview_reports(
    result: DynamicFeedstockPreviewResult | None = None,
    *,
    csv_path: Path = DEFAULT_CSV_REPORT,
    markdown_path: Path = DEFAULT_MARKDOWN_REPORT,
    **solve_kwargs: object,
) -> dict[str, str]:
    """Write concise preview artifacts and return project-relative names."""

    preview = result or solve_feedstock_dynamic_preview(**solve_kwargs)
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    markdown_path.parent.mkdir(parents=True, exist_ok=True)
    rows = list(preview.composition_preview)
    columns = (
        "time_label",
        "canonical_field",
        "value",
        "value_min",
        "value_max",
        "unit",
        "basis",
        "selected_source",
        "selected_parameter_id",
        "certainty_class",
        "confidence_score",
        "resolution_status",
        "blocked_reason",
        "assumption",
        "reconciliation_status",
        "reconciled_fields",
        "authoritative_field",
        "conflict_count",
        "reconciliation_warnings",
        "measured_data_status",
        "provenance",
    )
    with csv_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns)
        writer.writeheader()
        for row in rows:
            serialized = dict(row)
            for name in ("reconciled_fields", "reconciliation_warnings", "measured_data_status", "provenance"):
                serialized[name] = json.dumps(serialized[name], sort_keys=True)
            writer.writerow(serialized)
    markdown_path.write_text(_markdown_report(preview), encoding="utf-8")
    return {
        "csv": _project_relative_name(csv_path),
        "markdown": _project_relative_name(markdown_path),
    }


def _resolve_field(
    field: str,
    time_label: str,
    measured: tuple[MeasuredFeedstockOverride | MeasuredFeedstockRecord, ...],
    overrides: tuple[MeasuredFeedstockOverride, ...],
    allow_user_overrides: bool,
    allow_indirect: bool,
    candidates: tuple[FeedstockProxyCandidate, ...],
    pool: list[dict[str, object]],
    evidence_lookup: dict[tuple[str, str, str], dict[str, object]],
) -> tuple[DynamicFeedstockFieldValue, list[str]]:
    warnings: list[str] = []
    measured_match, measured_error = _select_override(measured, field, time_label)
    if measured_error:
        return _blocked_field(field, measured_error, "measured_project"), [f"{time_label}:{field}:{measured_error}"]
    if measured_match is not None:
        if not (measured_match.source_id or measured_match.lab_reference):
            reason = "measured_value_missing_source_or_lab_reference"
            return _blocked_field(field, reason, "measured_project"), [f"{time_label}:{field}:{reason}"]
        selected = _field_from_override(measured_match, time_label, "measured_project", 1.0)
        if selected.blocked_reason:
            warnings.append(f"{time_label}:{field}:{selected.blocked_reason}")
        return selected, warnings

    override_match, override_error = _select_override(overrides, field, time_label)
    if override_error and allow_user_overrides:
        return _blocked_field(field, override_error, "user_override"), [f"{time_label}:{field}:{override_error}"]
    if override_match is not None:
        if not allow_user_overrides:
            warnings.append(f"{time_label}:{field}:user_override_not_explicitly_enabled")
        elif not override_match.notes.strip() or not (override_match.source_id or override_match.lab_reference):
            reason = "user_override_requires_source_and_provenance_note"
            return _blocked_field(field, reason, "user_override"), [f"{time_label}:{field}:{reason}"]
        else:
            selected = _field_from_override(override_match, time_label, "user_override", 0.6)
            if selected.blocked_reason:
                warnings.append(f"{time_label}:{field}:{selected.blocked_reason}")
            return selected, warnings

    field_candidates = [item for item in candidates if item.canonical_field == field]
    ranked = sorted(
        field_candidates,
        key=lambda item: (
            EVIDENCE_PRIORITY.get(_candidate_certainty(item, evidence_lookup), 99),
            item.source_priority,
            item.parameter_id,
            item.source_file,
        ),
    )
    rejection_reasons: list[str] = []
    for certainty_stage in ("measured_project", "direct_literature", "derived_from_literature"):
        for candidate in ranked:
            certainty = _candidate_certainty(candidate, evidence_lookup)
            if certainty != certainty_stage:
                continue
            if not _candidate_applies(candidate, time_label):
                rejection_reasons.append("no_explicit_time_mapping")
                continue
            result = _field_from_candidate(candidate, certainty, evidence_lookup)
            if result.resolved:
                return result, warnings
            rejection_reasons.append(result.blocked_reason)

    assumption_rows = [
        row
        for row in pool
        if row["canonical_field"] == field and row["certainty_class"] == "engineering_assumption"
    ]
    for row in assumption_rows:
        result = _field_from_assumption(row)
        if result.resolved:
            return result, warnings
        rejection_reasons.append(result.blocked_reason)

    indirect_candidates = [
        item for item in ranked if _candidate_certainty(item, evidence_lookup) == "indirect_proxy"
    ]
    if indirect_candidates and not allow_indirect:
        rejection_reasons.append("indirect_proxy_not_allowed")
    if allow_indirect:
        for candidate in indirect_candidates:
            if not _candidate_applies(candidate, time_label):
                rejection_reasons.append("no_explicit_time_mapping")
                continue
            result = _field_from_candidate(candidate, "indirect_proxy", evidence_lookup)
            if result.resolved:
                return result, warnings
            rejection_reasons.append(result.blocked_reason)

    reason = next((item for item in rejection_reasons if item), "no_evidence_candidate")
    warnings.append(f"{time_label}:{field}:{reason}")
    return _blocked_field(field, reason, "missing"), warnings


def _select_override(
    values: tuple[MeasuredFeedstockOverride | MeasuredFeedstockRecord, ...],
    field: str,
    time_label: str,
) -> tuple[MeasuredFeedstockOverride | MeasuredFeedstockRecord | None, str]:
    exact = [item for item in values if item.canonical_field == field and item.time_label == time_label]
    static = [item for item in values if item.canonical_field == field and item.time_label is None]
    matches = exact or static
    if len(matches) > 1:
        return None, "ambiguous_duplicate_override"
    return (matches[0], "") if matches else (None, "")


def _field_from_override(
    override: MeasuredFeedstockOverride | MeasuredFeedstockRecord,
    time_label: str,
    certainty: str,
    confidence: float,
) -> DynamicFeedstockFieldValue:
    basis = validate_feedstock_candidate_basis(override.canonical_field, override.unit, override.value)
    policy = can_convert_feedstock_unit(override.unit, str(basis["expected_unit"]), override.canonical_field)
    if not policy["conversion_allowed"] or policy["conversion_required"]:
        return _blocked_field(override.canonical_field, str(policy["conversion_policy_status"]), certainty)
    source = override.source_id or override.lab_reference or ""
    record_id = getattr(override, "record_id", "")
    measurement_metadata = {
        key: getattr(override, key, "")
        for key in (
            "record_id",
            "start_date",
            "end_date",
            "sample_id",
            "sample_location",
            "feedstock",
            "material_state",
            "measurement_method",
            "measured_date",
            "data_status",
        )
        if getattr(override, key, "")
    }
    return DynamicFeedstockFieldValue(
        canonical_field=override.canonical_field,
        value=float(override.value),
        value_min=None,
        value_max=None,
        unit=override.unit,
        basis=str(expected_feedstock_basis(override.canonical_field)["basis"]),
        selected_source=source,
        selected_parameter_id=record_id or f"{certainty}:{override.canonical_field}",
        certainty_class=certainty,
        confidence_score=confidence,
        resolution_status="resolved_dynamic_input_preview",
        blocked_reason="",
        assumption="",
        provenance={
            "time_label": time_label,
            "source_kind": certainty,
            "source_id": override.source_id,
            "lab_reference": override.lab_reference,
            "notes": override.notes,
            "time_mapping": "exact" if override.time_label else "static",
            "conversion_policy_status": policy["conversion_policy_status"],
            "activation_status": "report_only",
            "measurement_metadata": measurement_metadata,
        },
    )


def _field_from_candidate(
    candidate: FeedstockProxyCandidate,
    certainty: str,
    evidence_lookup: dict[tuple[str, str, str], dict[str, object]],
) -> DynamicFeedstockFieldValue:
    evidence = _candidate_evidence(candidate, evidence_lookup)
    if candidate.value is None:
        reason = "range_without_scalar_blocked" if candidate.value_min is not None or candidate.value_max is not None else "missing_value"
        return _blocked_field(candidate.canonical_field, reason, certainty, candidate.value_min, candidate.value_max)
    basis = validate_feedstock_candidate_basis(candidate.canonical_field, candidate.unit, candidate.value)
    policy = can_convert_feedstock_unit(
        candidate.unit,
        str(basis["expected_unit"]),
        candidate.canonical_field,
        candidate.value_min,
        candidate.value_max,
    )
    if not policy["conversion_allowed"] or policy["conversion_required"]:
        return _blocked_field(
            candidate.canonical_field,
            str(policy["conversion_policy_status"]),
            certainty,
            candidate.value_min,
            candidate.value_max,
        )
    equation = validate_feedstock_equation_mapping(candidate)
    if certainty == "derived_from_literature" and equation["equation_mapping_status"] not in {
        "no_equation_required_observed_value",
        "equation_available_reference_only",
    }:
        return _blocked_field(candidate.canonical_field, str(equation["equation_mapping_status"]), certainty)
    source = candidate.source_title or candidate.source_file
    seasonal = _seasonal_class(candidate.parameter_id)
    return DynamicFeedstockFieldValue(
        canonical_field=candidate.canonical_field,
        value=float(candidate.value),
        value_min=candidate.value_min,
        value_max=candidate.value_max,
        unit=candidate.unit,
        basis=str(expected_feedstock_basis(candidate.canonical_field)["basis"]),
        selected_source=source,
        selected_parameter_id=candidate.parameter_id,
        certainty_class=certainty,
        confidence_score=float(evidence.get("confidence_score", 0.0)),
        resolution_status="resolved_dynamic_input_preview",
        blocked_reason="",
        assumption="",
        provenance={
            "source_file": candidate.source_file,
            "source_title": candidate.source_title,
            "doi_or_url": candidate.doi_or_url,
            "parameter_id": candidate.parameter_id,
            "evidence_quality": candidate.evidence_quality,
            "direct_or_indirect": candidate.direct_or_indirect,
            "limitation_note": candidate.limitation_note,
            "time_mapping": seasonal or "static",
            "conversion_policy_status": policy["conversion_policy_status"],
            "equation_mapping_status": equation["equation_mapping_status"],
            "activation_status": "report_only",
        },
    )


def _field_from_assumption(row: dict[str, object]) -> DynamicFeedstockFieldValue:
    field = str(row["canonical_field"])
    value = row.get("value")
    if value is None:
        return _blocked_field(field, "assumption_missing_numeric_value", "engineering_assumption")
    basis = validate_feedstock_candidate_basis(field, str(row.get("unit", "")), float(value))
    policy = can_convert_feedstock_unit(str(row.get("unit", "")), str(basis["expected_unit"]), field)
    if not policy["conversion_allowed"] or policy["conversion_required"]:
        return _blocked_field(field, str(policy["conversion_policy_status"]), "engineering_assumption")
    note = str(row.get("limitation_note", ""))
    return DynamicFeedstockFieldValue(
        canonical_field=field,
        value=float(value),
        value_min=None,
        value_max=None,
        unit=str(row.get("unit", "")),
        basis=str(expected_feedstock_basis(field)["basis"]),
        selected_source=str(row.get("source", "")),
        selected_parameter_id=str(row.get("parameter_id", "")),
        certainty_class="engineering_assumption",
        confidence_score=float(row.get("confidence_score", 0.25)),
        resolution_status="resolved_dynamic_input_preview",
        blocked_reason="",
        assumption=note or str(row.get("parameter_id", "")),
        provenance={
            "source_kind": "engineering_assumption",
            "source": row.get("source", ""),
            "limitation_note": note,
            "time_mapping": "static",
            "conversion_policy_status": policy["conversion_policy_status"],
            "activation_status": "report_only",
        },
    )


def _blocked_field(
    field: str,
    reason: str,
    certainty: str,
    value_min: float | None = None,
    value_max: float | None = None,
) -> DynamicFeedstockFieldValue:
    expectation = expected_feedstock_basis(field)
    return DynamicFeedstockFieldValue(
        canonical_field=field,
        value=None,
        value_min=value_min,
        value_max=value_max,
        unit=str(expectation["expected_unit"]),
        basis=str(expectation["basis"]),
        selected_source="",
        selected_parameter_id="",
        certainty_class=certainty,
        confidence_score=0.0,
        resolution_status="blocked_dynamic_input_preview",
        blocked_reason=reason,
        assumption="",
        provenance={"activation_status": "report_only", "blocked_reason": reason},
    )


def _candidate_applies(candidate: FeedstockProxyCandidate, time_label: str) -> bool:
    seasonal = _seasonal_class(candidate.parameter_id)
    if seasonal is None:
        return True
    month = _month_from_label(time_label)
    return month in _SEASON_MONTHS[seasonal] if month is not None else False


def _seasonal_class(parameter_id: str) -> str | None:
    upper = parameter_id.upper()
    if "-SP-" in upper:
        return "spring"
    if "-SU-" in upper:
        return "summer"
    if "-AU-" in upper:
        return "autumn"
    return None


def _month_from_label(label: str) -> int | None:
    if len(label) >= 7 and label[4] == "-" and label[5:7].isdigit():
        month = int(label[5:7])
        return month if 1 <= month <= 12 else None
    return None


def _evidence_lookup(pool: list[dict[str, object]]) -> dict[tuple[str, str, str], dict[str, object]]:
    lookup = {}
    for row in pool:
        key = (str(row["canonical_field"]), str(row["parameter_id"]), str(row.get("unit", "")))
        lookup.setdefault(key, row)
    return lookup


def _candidate_evidence(
    candidate: FeedstockProxyCandidate,
    lookup: dict[tuple[str, str, str], dict[str, object]],
) -> dict[str, object]:
    return lookup.get((candidate.canonical_field, candidate.parameter_id, candidate.unit), {})


def _candidate_certainty(
    candidate: FeedstockProxyCandidate,
    lookup: dict[tuple[str, str, str], dict[str, object]],
) -> str:
    return str(_candidate_evidence(candidate, lookup).get("certainty_class", "missing"))


def _reconcile_moisture_total_solids(
    time_label: str,
    fields: list[DynamicFeedstockFieldValue],
) -> _MoistureTSReconciliation:
    by_field = {item.canonical_field: item for item in fields}
    moisture = by_field.get("moisture_wet_basis")
    solids = by_field.get("total_solids_wet_basis")
    if moisture is None or solids is None:
        return _MoistureTSReconciliation(tuple(fields), "not_applicable", (), (), (), "")
    if not moisture.resolved and not solids.resolved:
        return _MoistureTSReconciliation(tuple(fields), "blocked_missing_pair", (), (), (), "")
    if moisture.resolved and solids.resolved:
        assert moisture.value is not None and solids.value is not None
        if abs((moisture.value + solids.value) - 1.0) <= MOISTURE_TS_TOLERANCE:
            return _MoistureTSReconciliation(tuple(fields), "consistent", (), (), (), "")
        authoritative = min((moisture, solids), key=_moisture_ts_authority_rank)
        conflicting = solids if authoritative is moisture else moisture
        derived = _derive_moisture_ts_counterpart(authoritative, conflicting, time_label, conflict=True)
        conflict = {
            "time_label": time_label,
            "authoritative_field": authoritative.canonical_field,
            "authoritative_value": authoritative.value,
            "authoritative_source": authoritative.selected_source,
            "conflicting_field": conflicting.canonical_field,
            "original_conflicting_value": conflicting.value,
            "original_conflicting_source": conflicting.selected_source,
            "reconciled_value": derived.value,
            "selection_rule": "evidence_priority_then_confidence_then_time_specificity_then_ts_tie_break",
            "relation": "EQ-CALC-001" if authoritative is solids else "inverse(EQ-CALC-001)",
            "tolerance": MOISTURE_TS_TOLERANCE,
        }
        updated = tuple(derived if item.canonical_field == conflicting.canonical_field else item for item in fields)
        warning = (
            f"{time_label}:moisture_ts_conflict_reconciled:"
            f"authoritative={authoritative.canonical_field}:reconciled={conflicting.canonical_field}"
        )
        return _MoistureTSReconciliation(
            updated,
            "reconciled_conflict",
            (conflicting.canonical_field,),
            (conflict,),
            (warning,),
            authoritative.canonical_field,
        )

    authoritative = moisture if moisture.resolved else solids
    missing = solids if moisture.resolved else moisture
    derived = _derive_moisture_ts_counterpart(authoritative, missing, time_label, conflict=False)
    updated = tuple(derived if item.canonical_field == missing.canonical_field else item for item in fields)
    return _MoistureTSReconciliation(
        updated,
        "derived_missing_counterpart",
        (missing.canonical_field,),
        (),
        (),
        authoritative.canonical_field,
    )


def _moisture_ts_authority_rank(item: DynamicFeedstockFieldValue) -> tuple[int, float, int, int]:
    priority = EVIDENCE_PRIORITY.get(item.certainty_class, 99)
    time_mapping = str(item.provenance.get("time_mapping", ""))
    time_rank = 0 if time_mapping == "exact" else 1
    field_tie_break = 0 if item.canonical_field == "total_solids_wet_basis" else 1
    return priority, -item.confidence_score, time_rank, field_tie_break


def _derive_moisture_ts_counterpart(
    authoritative: DynamicFeedstockFieldValue,
    original_counterpart: DynamicFeedstockFieldValue,
    time_label: str,
    *,
    conflict: bool,
) -> DynamicFeedstockFieldValue:
    assert authoritative.value is not None
    if authoritative.canonical_field == "total_solids_wet_basis":
        target_field = "moisture_wet_basis"
        derived_value = moisture_wet_basis_from_total_solids(authoritative.value)
        unit = "kg water/kg wet biomass"
        relation = "EQ-CALC-001"
    else:
        target_field = "total_solids_wet_basis"
        derived_value = _total_solids_wet_basis_from_moisture(authoritative.value)
        unit = "kg/kg wet feed"
        relation = "inverse(EQ-CALC-001)"
    if original_counterpart.canonical_field != target_field:
        raise ValueError("Moisture/TS reconciliation received an unexpected counterpart field.")

    certainty, confidence = _derived_certainty(authoritative)
    reconciliation_provenance = {
        "status": "conflict_reconciled" if conflict else "missing_counterpart_derived",
        "time_label": time_label,
        "authoritative_field": authoritative.canonical_field,
        "authoritative_value": authoritative.value,
        "authoritative_source": authoritative.selected_source,
        "authoritative_parameter_id": authoritative.selected_parameter_id,
        "original_counterpart_value": original_counterpart.value,
        "original_counterpart_source": original_counterpart.selected_source,
        "original_counterpart_parameter_id": original_counterpart.selected_parameter_id,
        "original_counterpart_certainty": original_counterpart.certainty_class,
        "relation": relation,
        "tolerance": MOISTURE_TS_TOLERANCE,
        "silent_overwrite": False,
        "activation_status": "report_only",
    }
    return replace(
        original_counterpart,
        value=derived_value,
        value_min=None,
        value_max=None,
        unit=unit,
        basis=str(expected_feedstock_basis(target_field)["basis"]),
        selected_source=authoritative.selected_source,
        selected_parameter_id=f"{relation}:{authoritative.selected_parameter_id}",
        certainty_class=certainty,
        confidence_score=confidence,
        resolution_status="resolved_reconciled_dynamic_input_preview",
        blocked_reason="",
        provenance={**original_counterpart.provenance, "reconciliation": reconciliation_provenance},
    )


def _derived_certainty(authoritative: DynamicFeedstockFieldValue) -> tuple[str, float]:
    if authoritative.certainty_class == "measured_project":
        return "derived_from_measured_project", min(authoritative.confidence_score, 0.95)
    if authoritative.certainty_class == "user_override":
        return "derived_from_user_override", min(authoritative.confidence_score, 0.55)
    return "derived_from_literature", min(authoritative.confidence_score, 0.65)


def _total_solids_wet_basis_from_moisture(moisture_wet_basis: float) -> float:
    moisture = float(moisture_wet_basis)
    if not isfinite(moisture) or not 0.0 <= moisture <= 1.0:
        raise ValueError("Inverse EQ-CALC-001 moisture_wet_basis must be finite and within [0, 1].")
    return 1.0 - moisture


def _preview_result(
    bundles: tuple[DynamicFeedstockInputBundle, ...],
    allow_indirect: bool,
) -> DynamicFeedstockPreviewResult:
    rows = []
    unresolved = Counter()
    blocked = Counter()
    confidence = Counter()
    provenance = Counter()
    source_classes = Counter({"measured": 0, "proxy": 0, "literature": 0})
    reconciliation_statuses = Counter()
    warnings: list[str] = []
    reconciliation_warnings: list[str] = []
    reconciled_fields: set[str] = set()
    conflict_count = 0
    for bundle in bundles:
        warnings.extend(bundle.warnings)
        reconciliation_warnings.extend(bundle.reconciliation_warnings)
        reconciled_fields.update(bundle.reconciled_fields)
        conflict_count += bundle.conflict_count
        reconciliation_statuses[bundle.reconciliation_status] += 1
        unresolved.update(bundle.unresolved_fields)
        blocked.update(bundle.blocked_reasons.values())
        for item in bundle.fields:
            row = item.to_dict()
            row["time_label"] = bundle.time_label
            row["reconciliation_status"] = bundle.reconciliation_status
            row["reconciled_fields"] = list(bundle.reconciled_fields)
            row["authoritative_field"] = bundle.authoritative_field
            row["conflict_count"] = bundle.conflict_count
            row["reconciliation_warnings"] = list(bundle.reconciliation_warnings)
            row["measured_data_status"] = dict(bundle.measured_data_status)
            rows.append(row)
            confidence[item.certainty_class if item.resolved else "blocked"] += 1
            if item.resolved:
                provenance[item.certainty_class] += 1
                source_classes[_source_class(item.certainty_class)] += 1
            else:
                source_classes["blocked"] += 1
    measured_status = dict(bundles[0].measured_data_status) if bundles else _measured_data_status(None, 0)
    return DynamicFeedstockPreviewResult(
        bundles=bundles,
        composition_preview=tuple(rows),
        unresolved_summary=dict(sorted(unresolved.items())),
        blocked_summary=dict(sorted(blocked.items())),
        confidence_summary=dict(sorted(confidence.items())),
        provenance_summary=dict(sorted(provenance.items())),
        source_class_summary=dict(sorted(source_classes.items())),
        warnings=tuple(dict.fromkeys(warnings)),
        allow_indirect=allow_indirect,
        reconciliation_status_summary=dict(sorted(reconciliation_statuses.items())),
        conflict_count=conflict_count,
        reconciled_fields=tuple(sorted(reconciled_fields)),
        reconciliation_warnings=tuple(dict.fromkeys(reconciliation_warnings)),
        measured_data_status=measured_status,
    )


def _source_class(certainty_class: str) -> str:
    if certainty_class == "measured_project":
        return "measured"
    if certainty_class == "user_override":
        return "user_override"
    if certainty_class == "direct_literature":
        return "literature"
    if certainty_class.startswith("derived_from_"):
        return "derived"
    if certainty_class == "engineering_assumption":
        return "assumption"
    if certainty_class == "indirect_proxy":
        return "proxy"
    return certainty_class


def _markdown_report(result: DynamicFeedstockPreviewResult) -> str:
    resolved_count = sum(1 for row in result.composition_preview if row["value"] is not None)
    blocked_count = len(result.composition_preview) - resolved_count
    lines = [
        "# Dynamic Feedstock Solver Preview",
        "",
        "This artifact is a dynamic-solving preparation report. It does not activate dynamic calculation mode, create model overrides, or change the empirical BioSTEAM model.",
        "",
        "## Status",
        "",
        f"- Time steps: {len(result.bundles)}",
        f"- Resolved field-time values: {resolved_count}",
        f"- Blocked field-time values: {blocked_count}",
        f"- Moisture/TS conflicts reconciled: {result.conflict_count}",
        f"- Reconciled fields: {', '.join(result.reconciled_fields) or 'none'}",
        f"- Indirect proxies allowed: {result.allow_indirect}",
        "- Interpolation: disabled",
        "- Range midpoint calculation: disabled",
        "- Calculation ready: False",
        "- Activation readiness: False",
        "",
        "## Confidence Distribution",
        "",
    ]
    lines.extend(f"- `{key}`: {value}" for key, value in result.confidence_summary.items())
    lines.extend(["", "## Source Distribution", ""])
    lines.extend(f"- `{key}`: {value}" for key, value in result.source_class_summary.items())
    lines.extend(["", "## Moisture And Total Solids Reconciliation", ""])
    lines.extend(f"- `{key}`: {value} time step(s)" for key, value in result.reconciliation_status_summary.items())
    authoritative = Counter(bundle.authoritative_field or "none" for bundle in result.bundles)
    lines.extend(f"- authoritative `{key}`: {value} time step(s)" for key, value in sorted(authoritative.items()))
    lines.append(f"- tolerance: {MOISTURE_TS_TOLERANCE}")
    lines.append("- conflicting original values: preserved in CSV provenance and bundle conflict records")
    lines.extend(["", "## Measured Data", ""])
    measured = result.measured_data_status
    lines.extend(
        [
            f"- status: `{measured.get('status', 'not_supplied')}`",
            f"- source: `{measured.get('source_name') or 'none'}`",
            f"- usable rows: {measured.get('usable_rows', 0)}",
            f"- invalid rows: {measured.get('invalid_rows', 0)}",
            f"- example rows skipped: {measured.get('example_rows_skipped', 0)}",
        ]
    )
    invalid_records = measured.get("invalid_records", [])
    if invalid_records:
        lines.extend(
            f"- invalid `{item.get('record_id') or 'unnamed'}` row {item['row_number']}: {', '.join(item['reasons'])}"
            for item in invalid_records
        )
    lines.extend(["", "## Blocked Fields", ""])
    if result.unresolved_summary:
        lines.extend(f"- `{key}`: {value} time step(s)" for key, value in result.unresolved_summary.items())
    else:
        lines.append("- None in this preview; activation remains blocked by validation and model-integration gates.")
    lines.extend(["", "## Assumptions", ""])
    assumptions = sorted({item for bundle in result.bundles for item in bundle.assumptions})
    lines.extend(f"- {item}" for item in assumptions) if assumptions else lines.append("- No engineering assumptions selected.")
    lines.extend(["", "## Warnings", ""])
    lines.extend(f"- `{item}`" for item in result.warnings) if result.warnings else lines.append("- None.")
    lines.extend(
        [
            "",
            "## Activation Boundary",
            "",
            "The bundles are typed inputs for a future solver, but they remain preview-only. Moisture/TS conflicts are now reconciled transparently; real activation still requires measured-data review, remaining cross-field validation gates, explicit parameter mapping, and regression tests proving the empirical path is unchanged.",
            "",
        ]
    )
    return "\n".join(lines)


def _project_relative_name(path: Path) -> str:
    try:
        return path.resolve().relative_to(PROJECT_ROOT.resolve()).as_posix()
    except ValueError:
        return path.name


def main() -> None:
    artifacts = write_dynamic_feedstock_preview_reports()
    print(json.dumps(artifacts, indent=2))


if __name__ == "__main__":
    main()
