"""Read-only dataset governance for the advanced-model integration checkpoints."""

from __future__ import annotations

import csv
import hashlib
import json
from collections import Counter, defaultdict
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable, Mapping, Sequence

DATA_DIR = Path(__file__).resolve().parent / "data"
AUDIT_DIR = DATA_DIR / "global_audit_package"

INTEGRATION_ELIGIBILITY = frozenset(
    {
        "blocked",
        "reference_only",
        "eligible_default",
        "eligible_calibration",
        "eligible_validation",
        "active",
    }
)

ISSUE_POLICIES: Mapping[str, tuple[str, str]] = {
    "duplicate_identifier_within_dataset": (
        "Assign a unique canonical row identifier without changing the scientific value; retain the original identifier in provenance.",
        "parameter loading, deterministic selection, provenance, and every calculation using this dataset",
    ),
    "missing_direct_source": (
        "Add a traceable direct scientific or manufacturer source and evidence classification.",
        "default selection, calibration, validation, and scientific reporting",
    ),
    "missing_exact_source_location": (
        "Add the exact table, page, figure, equation, section, or manufacturer-document location.",
        "default selection, source reproduction, validation, and scientific reporting",
    ),
    "conflicting_units": (
        "Resolve the source unit contract and normalization using source evidence; preserve the original unit text.",
        "all quantitative calculations and dimensional validation using this row",
    ),
    "conflicting_bases": (
        "Resolve the material, concentration, time, wet/dry, mass/molar, or equipment basis from source evidence.",
        "all quantitative calculations, scaling, and comparisons using this row",
    ),
    "equation_symbol_mismatch": (
        "Map every expression symbol to an approved typed input with a unit contract and source definition.",
        "equation activation and every model that calls the equation",
    ),
    "equation_required_inputs_unavailable": (
        "Supply every required input through an eligible parameter with units, basis, applicability, and provenance.",
        "equation activation and every model that calls the equation",
    ),
    "potential_cost_double_counting": (
        "Assign cost ownership, included and excluded equipment, overlap group, basis, year, currency, and selected state before aggregation.",
        "purchase-cost, installed-cost, replacement-cost, utility-cost, and future TEA aggregation",
    ),
}

_SEVERITY_ORDER = {"low": 0, "medium": 1, "high": 2, "critical": 3}
_NON_COST_BLOCKERS = frozenset(ISSUE_POLICIES) - {"potential_cost_double_counting"}


@dataclass(frozen=True)
class QuarantineRecord:
    """One blocked source row with all currently reported reasons aggregated."""

    quarantine_id: str
    dataset: str
    row_id: str
    parameter: str
    reason: str
    severity: str
    required_correction: str
    calculation_pathways_affected: str
    integration_eligibility: str
    issue_types: str
    source_issue_count: int


@dataclass(frozen=True)
class DatasetActivationRecord:
    """Dataset-level integration decision for Checkpoint 1."""

    dataset_path: str
    category: str
    subgroup: str
    audit_readiness: str
    integration_eligibility: str
    default_eligibility: bool
    calculation_connected: bool
    active: bool
    source_issue_count: int
    quarantine_row_count: int
    issue_types: str
    cost_pathway_status: str
    selection_reason: str
    required_action: str
    source_checksum_sha256: str


@dataclass(frozen=True)
class EquationActivationRecord:
    """Controlled equation status without evaluating source expressions."""

    dataset_path: str
    dataset_group: str
    equation_id: str
    equation_name: str
    source_row_count: int
    integration_eligibility: str
    active: bool
    symbol_mapping_resolved: bool
    required_inputs_resolved: bool
    source_complete: bool
    typed_implementation_present: bool
    dimensional_test_present: bool
    reference_value_test_present: bool
    trend_test_present: bool
    boundary_test_present: bool
    invalid_input_test_present: bool
    undefined_expression_symbols: str
    likely_missing_inputs: str
    source_id: str
    source_title: str
    exact_source_location: str
    activation_reason: str
    required_action: str


@dataclass(frozen=True)
class CostOwnershipRecord:
    """Unresolved ownership contract for one potential cross-dataset cost overlap."""

    cost_record_id: str
    equipment_or_technology: str
    python_variable: str
    owning_unit_or_facility: str
    included_equipment: str
    excluded_equipment: str
    cost_scope_or_basis: str
    currency: str
    cost_year: str
    capacity_basis: str
    scale_exponent_or_source_equation: str
    source: str
    overlap_group: str
    selected_state: str
    resolution_status: str
    dataset_count: int
    datasets: str
    required_action: str


def _read_csv(path: Path, required_columns: Iterable[str]) -> list[dict[str, str]]:
    if not path.is_file():
        raise FileNotFoundError(f"Required audit file is missing: {path}")
    with path.open("r", encoding="utf-8-sig", newline="") as file:
        reader = csv.DictReader(file)
        columns = set(reader.fieldnames or ())
        missing = sorted(set(required_columns) - columns)
        if missing:
            raise ValueError(f"{path.name} is missing required columns: {missing}")
        return [dict(row) for row in reader]


def _write_csv(path: Path, records: Sequence[object]) -> None:
    if not records:
        raise ValueError(f"Refusing to write an empty governance register: {path}")
    rows = [asdict(record) for record in records]
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    with temporary.open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    temporary.replace(path)


def _write_json(path: Path, payload: Mapping[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    temporary.replace(path)


def _stable_id(prefix: str, *parts: str) -> str:
    digest = hashlib.sha256("\x1f".join(parts).encode("utf-8")).hexdigest()[:12]
    return f"{prefix}-{digest.upper()}"


def _source_path(dataset_path: str) -> Path:
    path = (DATA_DIR / Path(dataset_path.replace("/", "\\"))).resolve()
    data_root = DATA_DIR.resolve()
    if not path.is_relative_to(data_root):
        raise ValueError(f"Dataset path escapes Greenhub/data: {dataset_path}")
    if not path.is_file():
        raise FileNotFoundError(f"Manifest dataset does not exist: {dataset_path}")
    return path


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as file:
        for block in iter(lambda: file.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def source_dataset_checksums(
    manifest_rows: Sequence[Mapping[str, str]],
) -> dict[str, str]:
    """Return SHA-256 checksums for the 301 manifest-listed source datasets."""

    checksums: dict[str, str] = {}
    for row in manifest_rows:
        dataset_path = row["dataset_path"]
        if dataset_path in checksums:
            raise ValueError(f"Duplicate dataset path in global manifest: {dataset_path}")
        checksums[dataset_path] = _sha256(_source_path(dataset_path))
    return checksums


def build_quarantine_register(
    issue_rows: Sequence[Mapping[str, str]],
) -> tuple[QuarantineRecord, ...]:
    """Aggregate audit issues into unique blocked source-row records."""

    grouped: dict[tuple[str, str, str], list[Mapping[str, str]]] = defaultdict(list)
    for issue in issue_rows:
        issue_type = issue["issue_type"].strip()
        if issue_type not in ISSUE_POLICIES:
            raise ValueError(f"No quarantine policy exists for issue type: {issue_type}")
        key = (
            issue["dataset_path"].strip(),
            issue["row_id"].strip() or "[dataset-level]",
            issue["python_variable"].strip() or "[not specified]",
        )
        grouped[key].append(issue)

    records: list[QuarantineRecord] = []
    for (dataset, row_id, parameter), issues in sorted(grouped.items()):
        issue_types = sorted({issue["issue_type"].strip() for issue in issues})
        reasons = sorted(
            {
                f"{issue['issue_type'].strip()}: {issue['details'].strip()}"
                for issue in issues
            }
        )
        corrections = sorted({ISSUE_POLICIES[item][0] for item in issue_types})
        pathways = sorted({ISSUE_POLICIES[item][1] for item in issue_types})
        severities = [issue["severity"].strip().lower() for issue in issues]
        severity = max(severities, key=lambda value: _SEVERITY_ORDER.get(value, -1))
        records.append(
            QuarantineRecord(
                quarantine_id=_stable_id("Q", dataset, row_id, parameter),
                dataset=dataset,
                row_id=row_id,
                parameter=parameter,
                reason=" | ".join(reasons),
                severity=severity,
                required_correction=" | ".join(corrections),
                calculation_pathways_affected=" | ".join(pathways),
                integration_eligibility="blocked",
                issue_types="; ".join(issue_types),
                source_issue_count=len(issues),
            )
        )
    return tuple(records)


def build_dataset_activation_matrix(
    readiness_rows: Sequence[Mapping[str, str]],
    issue_rows: Sequence[Mapping[str, str]],
    quarantine_records: Sequence[QuarantineRecord],
    checksums: Mapping[str, str],
) -> tuple[DatasetActivationRecord, ...]:
    """Create conservative dataset decisions without activating any row."""

    issues_by_dataset: dict[str, list[Mapping[str, str]]] = defaultdict(list)
    for issue in issue_rows:
        issues_by_dataset[issue["dataset_path"].strip()].append(issue)
    quarantine_counts = Counter(record.dataset for record in quarantine_records)

    records: list[DatasetActivationRecord] = []
    for row in sorted(readiness_rows, key=lambda item: item["dataset_path"]):
        dataset_path = row["dataset_path"].strip()
        readiness = row["readiness"].strip()
        issues = issues_by_dataset.get(dataset_path, [])
        issue_types = sorted({issue["issue_type"].strip() for issue in issues})
        non_cost_blockers = sorted(set(issue_types) & _NON_COST_BLOCKERS)
        if readiness in {"D1", "D2"} or non_cost_blockers:
            eligibility = "blocked"
            reason = (
                f"Audit readiness {readiness} or unresolved non-cost defects block calculation integration."
            )
            action = "Resolve all quarantined identity, source, unit, basis, and equation defects, then rerun the audit gate."
        elif readiness == "D3":
            eligibility = "reference_only"
            reason = "Schema-loadable D3 evidence has not passed GreenHub applicability, parameter, equation, and validation gates."
            action = "Review row applicability and transferability for one selected unit; do not select a default before unit-level tests."
        else:
            raise ValueError(f"Unsupported dataset readiness '{readiness}' for {dataset_path}")
        if eligibility not in INTEGRATION_ELIGIBILITY:
            raise AssertionError(f"Invalid integration eligibility: {eligibility}")
        records.append(
            DatasetActivationRecord(
                dataset_path=dataset_path,
                category=row["category"].strip(),
                subgroup=row["subgroup"].strip(),
                audit_readiness=readiness,
                integration_eligibility=eligibility,
                default_eligibility=False,
                calculation_connected=False,
                active=False,
                source_issue_count=len(issues),
                quarantine_row_count=quarantine_counts[dataset_path],
                issue_types="; ".join(issue_types) if issue_types else "none",
                cost_pathway_status=(
                    "blocked"
                    if "potential_cost_double_counting" in issue_types
                    else "not_assessed"
                ),
                selection_reason=reason,
                required_action=action,
                source_checksum_sha256=checksums[dataset_path],
            )
        )
    return tuple(records)


def build_equation_activation_registry(
    equation_rows: Sequence[Mapping[str, str]],
) -> tuple[EquationActivationRecord, ...]:
    """Block unsafe equations and keep complete-but-unimplemented rows reference-only."""

    records: list[EquationActivationRecord] = []
    grouped: dict[tuple[str, str], list[Mapping[str, str]]] = defaultdict(list)
    for row in equation_rows:
        key = (row["dataset_path"].strip(), row["equation_id"].strip())
        grouped[key].append(row)
    for key, source_rows in sorted(grouped.items()):
        row = source_rows[0]
        undefined = "; ".join(
            sorted(
                {
                    item["undefined_expression_symbols"].strip()
                    for item in source_rows
                    if item["undefined_expression_symbols"].strip()
                }
            )
        )
        missing_inputs = "; ".join(
            sorted(
                {
                    item["likely_missing_inputs"].strip()
                    for item in source_rows
                    if item["likely_missing_inputs"].strip()
                }
            )
        )
        source_complete = bool(
            row["source_id"].strip()
            and row["source_title"].strip()
            and row["exact_location"].strip()
        )
        symbol_mapping_resolved = not bool(undefined)
        required_inputs_resolved = not bool(missing_inputs)
        duplicate_identity = len(source_rows) > 1
        if (
            duplicate_identity
            or not symbol_mapping_resolved
            or not required_inputs_resolved
            or not source_complete
        ):
            eligibility = "blocked"
            activation_reason = "Duplicate identity, unresolved symbols, required inputs, or source-location metadata block implementation."
            required_action = "Resolve duplicate identity and source metadata plus every typed symbol/input contract before implementing the equation."
        else:
            eligibility = "reference_only"
            activation_reason = "Source equation is catalogued but has no approved typed implementation and test package."
            required_action = "Implement an approved function with dimensional, source-reference, trend, boundary, and invalid-input tests."
        records.append(
            EquationActivationRecord(
                dataset_path=key[0],
                dataset_group=row["dataset_group"].strip(),
                equation_id=key[1],
                equation_name=row["equation_name"].strip() or "missing",
                source_row_count=len(source_rows),
                integration_eligibility=eligibility,
                active=False,
                symbol_mapping_resolved=symbol_mapping_resolved,
                required_inputs_resolved=required_inputs_resolved,
                source_complete=source_complete,
                typed_implementation_present=False,
                dimensional_test_present=False,
                reference_value_test_present=False,
                trend_test_present=False,
                boundary_test_present=False,
                invalid_input_test_present=False,
                undefined_expression_symbols=undefined or "none",
                likely_missing_inputs=missing_inputs or "none",
                source_id=row["source_id"].strip() or "missing",
                source_title=row["source_title"].strip() or "missing",
                exact_source_location=row["exact_location"].strip() or "missing",
                activation_reason=activation_reason,
                required_action=required_action,
            )
        )
    return tuple(records)


def build_cost_ownership_registry(
    cost_rows: Sequence[Mapping[str, str]],
) -> tuple[CostOwnershipRecord, ...]:
    """Create explicit unresolved ownership rows; no cost is selected or summed."""

    records: list[CostOwnershipRecord] = []
    for row in sorted(
        cost_rows,
        key=lambda item: (item["python_variable"], item["datasets"]),
    ):
        variable = row["python_variable"].strip()
        datasets = row["datasets"].strip()
        overlap_group = _stable_id("COST", variable, datasets)
        records.append(
            CostOwnershipRecord(
                cost_record_id=overlap_group,
                equipment_or_technology=row["equipment_or_technology"].strip() or "missing",
                python_variable=variable,
                owning_unit_or_facility="missing",
                included_equipment="missing",
                excluded_equipment="missing",
                cost_scope_or_basis=row["cost_scope_or_basis"].strip() or "missing",
                currency="missing",
                cost_year="missing",
                capacity_basis="missing",
                scale_exponent_or_source_equation="missing",
                source="missing; inspect listed datasets before ownership resolution",
                overlap_group=overlap_group,
                selected_state="not_selected",
                resolution_status="blocked",
                dataset_count=int(row["dataset_count"]),
                datasets=datasets,
                required_action="Assign one owner and explicit inclusions/exclusions, then verify basis, year, currency, scaling, and source before cost aggregation.",
            )
        )
    return tuple(records)


def build_checkpoint1_registries(output_dir: Path = AUDIT_DIR) -> dict[str, object]:
    """Validate the global audit and write deterministic Checkpoint 1 registers."""

    summary_path = AUDIT_DIR / "global_validation_summary.json"
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    manifest = _read_csv(
        AUDIT_DIR / "global_dataset_manifest.csv",
        {"dataset_path", "category", "subgroup", "detected_readiness"},
    )
    readiness = _read_csv(
        AUDIT_DIR / "global_dataset_readiness.csv",
        {"dataset_path", "category", "subgroup", "readiness"},
    )
    issues = _read_csv(
        AUDIT_DIR / "global_validation_issues.csv",
        {"issue_type", "dataset_path", "row_id", "python_variable", "details", "severity"},
    )
    equations = _read_csv(
        AUDIT_DIR / "global_equation_registry.csv",
        {
            "dataset_path",
            "dataset_group",
            "equation_id",
            "equation_name",
            "source_id",
            "source_title",
            "exact_location",
            "undefined_expression_symbols",
            "likely_missing_inputs",
        },
    )
    costs = _read_csv(
        AUDIT_DIR / "global_cost_overlap_register.csv",
        {
            "equipment_or_technology",
            "python_variable",
            "cost_scope_or_basis",
            "dataset_count",
            "datasets",
        },
    )
    expected_datasets = int(summary["dataset_count"])
    expected_issues = int(summary["issue_count"])
    if len(manifest) != expected_datasets or len(readiness) != expected_datasets:
        raise ValueError(
            "Global dataset counts disagree: "
            f"summary={expected_datasets}, manifest={len(manifest)}, readiness={len(readiness)}"
        )
    if len(issues) != expected_issues:
        raise ValueError(
            f"Global issue counts disagree: summary={expected_issues}, issues={len(issues)}"
        )

    checksums = source_dataset_checksums(manifest)
    quarantine = build_quarantine_register(issues)
    activation = build_dataset_activation_matrix(
        readiness,
        issues,
        quarantine,
        checksums,
    )
    equation_activation = build_equation_activation_registry(equations)
    cost_ownership = build_cost_ownership_registry(costs)

    output_paths = {
        "quarantine": output_dir / "global_quarantine_register.csv",
        "dataset_activation": output_dir / "dataset_activation_matrix.csv",
        "equation_activation": output_dir / "equation_activation_registry.csv",
        "cost_ownership": output_dir / "cost_ownership_registry.csv",
        "source_checksums": output_dir / "source_dataset_checksums.csv",
        "summary": output_dir / "checkpoint1_registry_summary.json",
    }
    _write_csv(output_paths["quarantine"], quarantine)
    _write_csv(output_paths["dataset_activation"], activation)
    _write_csv(output_paths["equation_activation"], equation_activation)
    _write_csv(output_paths["cost_ownership"], cost_ownership)

    checksum_rows = tuple(
        SourceChecksumRecord(
            dataset_path=dataset_path,
            sha256=checksum,
            byte_size=_source_path(dataset_path).stat().st_size,
        )
        for dataset_path, checksum in sorted(checksums.items())
    )
    _write_csv(output_paths["source_checksums"], checksum_rows)

    eligibility_counts = Counter(record.integration_eligibility for record in activation)
    equation_counts = Counter(
        record.integration_eligibility for record in equation_activation
    )
    checkpoint_summary: dict[str, object] = {
        "source_audit_generated_at": summary.get("generated_at"),
        "source_dataset_count": len(manifest),
        "source_issue_count": len(issues),
        "quarantine_row_count": len(quarantine),
        "dataset_eligibility_counts": dict(sorted(eligibility_counts.items())),
        "active_dataset_count": sum(record.active for record in activation),
        "default_eligible_dataset_count": sum(
            record.default_eligibility for record in activation
        ),
        "equation_count": len(equation_activation),
        "equation_eligibility_counts": dict(sorted(equation_counts.items())),
        "active_equation_count": sum(record.active for record in equation_activation),
        "cost_overlap_group_count": len(cost_ownership),
        "resolved_cost_overlap_count": sum(
            record.resolution_status != "blocked" for record in cost_ownership
        ),
        "source_checksum_count": len(checksums),
        "scientific_values_modified": False,
    }
    _write_json(output_paths["summary"], checkpoint_summary)
    return {
        "paths": output_paths,
        "summary": checkpoint_summary,
        "quarantine": quarantine,
        "dataset_activation": activation,
        "equation_activation": equation_activation,
        "cost_ownership": cost_ownership,
    }


@dataclass(frozen=True)
class SourceChecksumRecord:
    """Immutable checksum evidence for one manifest-listed source CSV."""

    dataset_path: str
    sha256: str
    byte_size: int


def main() -> None:
    """Generate and summarize Checkpoint 1 governance outputs."""

    result = build_checkpoint1_registries()
    print(json.dumps(result["summary"], indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
