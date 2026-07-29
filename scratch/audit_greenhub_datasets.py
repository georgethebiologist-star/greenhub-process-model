from __future__ import annotations

import csv
import json
import math
import re
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


ROOT = Path(__file__).resolve().parents[1]
DATA_ROOT = ROOT / "Greenhub" / "data"
OUTPUT_DIR = DATA_ROOT / "global_audit_package"

TARGET_TOP_LEVELS = {
    "Pre-treatment",
    "Centrifuge",
    "Protein recovery",
    "Bigas production + upgrade",
    "Resource recovery",
}

STATUS_MAP = {
    "ready": "ready",
    "ready_as_registry": "ready",
    "ready_as_registry_not_calibrated": "incomplete",
    "ready_as_registry_not_calibrated.": "incomplete",
    "registry_ready_not_calibrated": "incomplete",
    "partial": "incomplete",
    "schema_ready_data_sparse": "schema_ready",
    "schema_ready": "schema_ready",
    "ready_for_loading": "loadable",
    "loadable": "loadable",
    "literature-reported": "sourced",
    "measured": "sourced",
    "reported": "sourced",
    "validated": "validated",
    "missing": "missing",
    "not available": "missing",
    "inactive": "inactive",
    "direct_needed": "missing",
}

STATUS_ORDER = {
    "missing": 0,
    "inactive": 1,
    "incomplete": 2,
    "schema_ready": 3,
    "loadable": 4,
    "sourced": 5,
    "validated": 6,
    "ready": 7,
}

NUMERIC_CANDIDATE_COLUMNS = (
    "value",
    "normalized_si_value",
    "numerical_value",
    "required_value",
    "capacity_value",
    "input_capacity_value",
    "electrical_output_kw",
    "temperature_c",
    "temperature_value",
    "pressure_value",
    "area_value",
    "module_lifetime_value",
    "replacement_cost_value",
    "purchase_cost_value",
    "capex_value",
    "lhv_value",
    "recoverable_heat_value",
    "parasitic_power_value",
    "methane_slip_value",
    "startup_time_value",
    "minimum_load_pct",
    "availability_pct",
    "maintenance_interval_value",
    "equipment_life_value",
    "load_fraction",
    "electrical_efficiency_pct",
    "thermal_efficiency_pct",
    "total_efficiency_pct",
)

ID_COLUMNS = (
    "parameter_id",
    "equation_id",
    "scenario_id",
    "register_id",
    "missing_id",
)

ROW_IDENTIFIER_COLUMNS = ID_COLUMNS + (
    "source_id",
    "dataset_id",
)

SOURCE_COLUMNS = (
    "source_id",
    "source_title",
    "doi_or_stable_id",
    "doi_or_stable_identifier",
    "source_url",
    "url",
)

LOCATION_COLUMNS = (
    "exact_location",
    "source_location",
)

UNIT_COLUMNS = (
    "unit",
    "normalized_si_unit",
    "capacity_unit",
    "input_capacity_unit",
    "lhv_unit",
    "jacket_water_temperature_unit",
    "exhaust_temperature_unit",
    "recoverable_heat_unit",
    "parasitic_power_unit",
    "methane_slip_unit",
    "startup_time_unit",
    "maintenance_interval_unit",
    "equipment_life_unit",
    "replacement_cost_unit",
    "purchase_cost_currency",
    "replacement_cost_currency",
    "capex_currency",
)

SYMBOL_SPLIT_RE = re.compile(r"[^A-Za-z0-9_]+")
PYTHON_TOKEN_RE = re.compile(r"\b[A-Za-z_][A-Za-z0-9_]*\b")


def canonicalize_status(value: str) -> str:
    text = (value or "").strip().lower().replace("-", "_").replace(" ", "_")
    return STATUS_MAP.get(text, text or "unknown")


def status_rank(value: str) -> int:
    return STATUS_ORDER.get(canonicalize_status(value), -1)


def is_number(value: str | None) -> bool:
    if value is None:
        return False
    text = str(value).strip()
    if not text:
        return False
    try:
        number = float(text)
    except ValueError:
        return False
    return not math.isnan(number)


def clean(value: str | None) -> str:
    return "" if value is None else str(value).strip()


def extract_dataset_group(relative_path: Path) -> tuple[str, str]:
    top = relative_path.parts[0]
    subgroup = relative_path.parts[1] if len(relative_path.parts) > 2 else top
    return top, subgroup


def row_identifier(row: dict[str, str], fallback: str) -> str:
    for key in ROW_IDENTIFIER_COLUMNS:
        value = clean(row.get(key))
        if value:
            return value
    return fallback


def source_location_present(row: dict[str, str]) -> bool:
    if any(clean(row.get(column)) for column in LOCATION_COLUMNS):
        return True
    for key, value in row.items():
        key_l = key.lower()
        if "page" in key_l or "table" in key_l or "section" in key_l:
            if clean(value):
                return True
    return False


def has_direct_source(row: dict[str, str]) -> bool:
    return bool(clean(row.get("source_id")) or clean(row.get("source_title")))


def extract_symbols(symbol_field: str) -> set[str]:
    if not symbol_field:
        return set()
    symbols = set()
    for chunk in re.split(r"[;,]", symbol_field):
        chunk = chunk.strip()
        if not chunk:
            continue
        match = re.match(r"^([A-Za-z_][A-Za-z0-9_]*)\s*[:=]", chunk)
        if match:
            symbols.add(match.group(1))
        elif re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", chunk):
            symbols.add(chunk)
    return symbols


def extract_python_variables(expression: str) -> set[str]:
    if not expression:
        return set()
    excluded = {
        "math",
        "log",
        "log10",
        "exp",
        "min",
        "max",
        "pow",
        "if",
        "else",
        "for",
        "in",
        "and",
        "or",
        "not",
        "true",
        "false",
    }
    variables = set()
    for token in PYTHON_TOKEN_RE.findall(expression):
        if token.lower() not in excluded and not token.isupper():
            variables.add(token)
    return variables


@dataclass
class DatasetSummary:
    path: Path
    category: str
    subgroup: str
    row_count: int
    headers: list[str]
    duplicate_ids: int
    duplicate_rows: int
    numeric_rows: int
    unsourced_numeric_rows: int
    missing_location_rows: int
    unit_conflicts: int
    basis_conflicts: int
    cross_reference_issues: int
    equation_missing_inputs: int
    equation_symbol_mismatches: int
    cost_overlap_flags: int
    standardized_statuses: str
    dataset_readiness: str
    notes: str


def collect_csv_files() -> list[Path]:
    files: list[Path] = []
    for path in DATA_ROOT.rglob("*.csv"):
        rel = path.relative_to(DATA_ROOT)
        if rel.parts[0] not in TARGET_TOP_LEVELS:
            continue
        if rel.parts[0] == "global_audit_package":
            continue
        files.append(path)
    return sorted(files)


def read_csv(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        rows = [{key: clean(value) for key, value in row.items()} for row in reader]
        return list(reader.fieldnames or []), rows


def write_csv(path: Path, fieldnames: list[str], rows: Iterable[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({key: row.get(key, "") for key in fieldnames})


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    csv_files = collect_csv_files()

    source_register_entries: list[dict[str, object]] = []
    variable_rows: list[dict[str, object]] = []
    unit_rows: list[dict[str, object]] = []
    equation_rows: list[dict[str, object]] = []
    missing_rows: list[dict[str, object]] = []
    manifest_rows: list[dict[str, object]] = []
    readiness_rows: list[dict[str, object]] = []
    validation_issues: list[dict[str, object]] = []
    dataset_summaries: list[DatasetSummary] = []
    file_lookup = {path.relative_to(DATA_ROOT).as_posix().lower(): path for path in csv_files}

    cost_entries_by_key: dict[tuple[str, str, str], list[tuple[Path, str, str]]] = defaultdict(list)

    for path in csv_files:
        rel = path.relative_to(DATA_ROOT)
        category, subgroup = extract_dataset_group(rel)
        headers, rows = read_csv(path)
        row_count = len(rows)
        id_counter: Counter[str] = Counter()
        row_counter: Counter[tuple[tuple[str, str], ...]] = Counter()
        duplicate_ids = 0
        duplicate_rows = 0
        numeric_rows = 0
        unsourced_numeric_rows = 0
        missing_location_rows = 0
        dataset_unit_conflicts = 0
        dataset_basis_conflicts = 0
        cross_reference_issues = 0
        equation_missing_inputs = 0
        equation_symbol_mismatches = 0
        cost_overlap_flags = 0
        statuses: set[str] = set()

        unit_sets: dict[str, set[str]] = defaultdict(set)
        basis_sets: dict[str, set[str]] = defaultdict(set)
        local_variables: set[str] = set()
        local_source_ids: set[str] = set()

        for index, row in enumerate(rows, start=2):
            rid = row_identifier(row, f"{rel.as_posix()}:{index}")
            for id_column in ID_COLUMNS:
                value = clean(row.get(id_column))
                if value:
                    id_counter[value] += 1
            row_counter[tuple(sorted(row.items()))] += 1

            if clean(row.get("source_id")):
                local_source_ids.add(clean(row["source_id"]))

            status = clean(row.get("data_status") or row.get("status") or row.get("integration_status"))
            if status:
                statuses.add(canonicalize_status(status))

            python_variable = clean(row.get("python_variable"))
            if python_variable:
                local_variables.add(python_variable)

            for unit_column in UNIT_COLUMNS:
                unit_value = clean(row.get(unit_column))
                if unit_value:
                    unit_rows.append(
                        {
                            "dataset_path": rel.as_posix(),
                            "dataset_group": subgroup,
                            "column_name": unit_column,
                            "unit_text": unit_value,
                            "status_standardized": canonicalize_status(status),
                        }
                    )

            if python_variable and clean(row.get("unit")):
                unit_sets[python_variable].add(clean(row.get("unit")))
            if python_variable and clean(row.get("basis")):
                basis_sets[python_variable].add(clean(row.get("basis")))

            numeric_here = False
            for numeric_column in NUMERIC_CANDIDATE_COLUMNS:
                if is_number(row.get(numeric_column)):
                    numeric_here = True
                    variable_rows.append(
                        {
                            "dataset_path": rel.as_posix(),
                            "dataset_group": subgroup,
                            "row_id": rid,
                            "python_variable": python_variable,
                            "parameter_name": clean(row.get("parameter_name")),
                            "numeric_column": numeric_column,
                            "original_value": clean(row.get(numeric_column)),
                            "original_unit": clean(row.get("unit")),
                            "normalized_si_value": clean(row.get("normalized_si_value")),
                            "normalized_si_unit": clean(row.get("normalized_si_unit")),
                            "basis": clean(row.get("basis")),
                            "status_original": status,
                            "status_standardized": canonicalize_status(status),
                            "source_id": clean(row.get("source_id")),
                            "source_title": clean(row.get("source_title")),
                            "exact_location": clean(row.get("exact_location") or row.get("source_location")),
                        }
                    )
            if numeric_here:
                numeric_rows += 1
                if not has_direct_source(row):
                    unsourced_numeric_rows += 1
                    validation_issues.append(
                        {
                            "issue_type": "missing_direct_source",
                            "dataset_path": rel.as_posix(),
                            "row_id": rid,
                            "python_variable": python_variable,
                            "details": "Numeric row has no source_id or source_title.",
                            "severity": "high",
                        }
                    )
                if not source_location_present(row):
                    missing_location_rows += 1
                    validation_issues.append(
                        {
                            "issue_type": "missing_exact_source_location",
                            "dataset_path": rel.as_posix(),
                            "row_id": rid,
                            "python_variable": python_variable,
                            "details": "Numeric row lacks table/page/section/equation or machine-readable location.",
                            "severity": "high",
                        }
                    )

            for ref_column in ("filename", "file_name", "target_file", "related_file", "affected_files"):
                reference = clean(row.get(ref_column))
                if not reference:
                    continue
                if ref_column == "affected_files":
                    parts = [part.strip() for part in reference.split(";") if part.strip()]
                else:
                    parts = [reference]
                for part in parts:
                    part_key = part.replace("\\", "/").lower()
                    sibling_key = f"{rel.parent.as_posix().lower()}/{part_key}"
                    if part_key.endswith(".csv") and part_key not in file_lookup and sibling_key not in file_lookup:
                        cross_reference_issues += 1
                        validation_issues.append(
                            {
                                "issue_type": "broken_file_reference",
                                "dataset_path": rel.as_posix(),
                                "row_id": rid,
                                "python_variable": python_variable,
                                "details": f"Referenced file '{part}' was not found under Greenhub/data.",
                                "severity": "medium",
                            }
                        )

            if "equation_id" in row:
                symbol_field = clean(
                    row.get("symbol_definitions")
                    or row.get("symbol_definitions_and_units")
                    or row.get("symbols_and_units")
                    or row.get("symbol_units")
                    or row.get("units")
                )
                expression = clean(row.get("python_expression"))
                symbols = extract_symbols(symbol_field)
                expression_vars = extract_python_variables(expression)
                undefined = sorted(expression_vars - symbols - local_variables)
                if undefined:
                    equation_symbol_mismatches += 1
                    validation_issues.append(
                        {
                            "issue_type": "equation_symbol_mismatch",
                            "dataset_path": rel.as_posix(),
                            "row_id": rid,
                            "python_variable": clean(row.get("equation_name")),
                            "details": f"Expression variables not defined in symbol list or dataset variables: {', '.join(undefined)}",
                            "severity": "medium",
                        }
                    )

                missing_inputs = sorted(
                    variable
                    for variable in expression_vars
                    if variable not in local_variables and variable not in symbols
                )
                if missing_inputs:
                    equation_missing_inputs += 1
                    validation_issues.append(
                        {
                            "issue_type": "equation_required_inputs_unavailable",
                            "dataset_path": rel.as_posix(),
                            "row_id": rid,
                            "python_variable": clean(row.get("equation_name")),
                            "details": f"Equation symbols appear unavailable in local dataset variables: {', '.join(missing_inputs)}",
                            "severity": "medium",
                        }
                    )

                equation_rows.append(
                    {
                        "dataset_path": rel.as_posix(),
                        "dataset_group": subgroup,
                        "equation_id": clean(row.get("equation_id")),
                        "equation_name": clean(row.get("equation_name")),
                        "python_expression": expression,
                        "symbol_definition_field": symbol_field,
                        "status_standardized": canonicalize_status(status),
                        "source_id": clean(row.get("source_id")),
                        "source_title": clean(row.get("source_title")),
                        "exact_location": clean(row.get("exact_location") or row.get("source_location")),
                        "undefined_expression_symbols": ", ".join(undefined),
                        "likely_missing_inputs": ", ".join(missing_inputs),
                    }
                )

            source_register_like = rel.name.lower() == "source_register.csv"
            if source_register_like:
                source_register_entries.extend(
                    {
                        "dataset_path": rel.as_posix(),
                        "dataset_group": subgroup,
                        "source_id": clean(row.get("source_id")),
                        "source_title": clean(row.get("source_title")),
                        "authors": clean(row.get("authors") or row.get("authors_or_organization")),
                        "year": clean(row.get("year")),
                        "doi_or_stable_id": clean(row.get("doi_or_stable_id") or row.get("doi_or_stable_identifier")),
                        "url": clean(row.get("url") or row.get("source_url")),
                        "source_type": clean(row.get("source_type")),
                        "notes": clean(row.get("notes") or row.get("quality_notes") or row.get("quality_and_transferability")),
                    }
                    for row in rows
                )

            if "missing_id" in row or "register_id" in row:
                missing_rows.append(
                    {
                        "dataset_path": rel.as_posix(),
                        "dataset_group": subgroup,
                        "missing_item_id": clean(row.get("missing_id") or row.get("register_id")),
                        "target_file": clean(row.get("target_file") or row.get("related_file")),
                        "python_variable": clean(row.get("python_variable") or row.get("parameter_or_topic")),
                        "reason_missing": clean(
                            row.get("reason_missing")
                            or row.get("why_missing_or_limited")
                            or row.get("current_coverage")
                            or row.get("notes")
                        ),
                        "required_for": clean(row.get("required_for") or row.get("integration_action")),
                        "priority": clean(row.get("priority")),
                        "status_standardized": canonicalize_status(status or row.get("data_status", "")),
                    }
                )

            if "cost" in rel.name.lower() or "equipment" in rel.name.lower():
                equipment_key = (
                    clean(row.get("equipment_tag") or row.get("equipment_or_system") or row.get("technology") or row.get("manufacturer_model")),
                    clean(row.get("python_variable")),
                    clean(row.get("cost_scope") or row.get("capex_basis") or row.get("basis")),
                )
                if any(equipment_key):
                    cost_entries_by_key[equipment_key].append((path, rid, clean(row.get("parameter_id"))))

        duplicate_ids = sum(count - 1 for count in id_counter.values() if count > 1)
        duplicate_rows = sum(count - 1 for count in row_counter.values() if count > 1)

        for identifier, count in id_counter.items():
            if count > 1:
                validation_issues.append(
                    {
                        "issue_type": "duplicate_identifier_within_dataset",
                        "dataset_path": rel.as_posix(),
                        "row_id": identifier,
                        "python_variable": "",
                        "details": f"Identifier '{identifier}' appears {count} times in the same dataset.",
                        "severity": "high",
                    }
                )

        for variable, units in unit_sets.items():
            if len(units) > 1:
                dataset_unit_conflicts += 1
                validation_issues.append(
                    {
                        "issue_type": "conflicting_units",
                        "dataset_path": rel.as_posix(),
                        "row_id": variable,
                        "python_variable": variable,
                        "details": f"Variable appears with multiple original units: {', '.join(sorted(units))}",
                        "severity": "medium",
                    }
                )
        for variable, bases in basis_sets.items():
            if len(bases) > 1:
                dataset_basis_conflicts += 1
                validation_issues.append(
                    {
                        "issue_type": "conflicting_bases",
                        "dataset_path": rel.as_posix(),
                        "row_id": variable,
                        "python_variable": variable,
                        "details": f"Variable appears with multiple bases: {', '.join(sorted(bases))}",
                        "severity": "medium",
                    }
                )

        readiness = "D3"
        notes = []
        if duplicate_ids or cross_reference_issues:
            readiness = "D1"
            notes.append("ID or cross-reference issues found.")
        elif unsourced_numeric_rows or missing_location_rows:
            readiness = "D2"
            notes.append("Loadable but source traceability incomplete.")
        elif "validation_report.csv" in rel.name.lower() or "validation_report.json" in rel.name.lower():
            readiness = "D3"
            notes.append("Validation artifact is loadable but not calculation-connected in this audit.")
        else:
            readiness = "D3"

        if rel.name.lower().endswith("equation_registry.csv") or "equation" in rel.name.lower():
            if equation_missing_inputs or equation_symbol_mismatches:
                if readiness != "D1":
                    readiness = "D2"

        standardized_statuses = "; ".join(sorted(statuses))
        dataset_summaries.append(
            DatasetSummary(
                path=rel,
                category=category,
                subgroup=subgroup,
                row_count=row_count,
                headers=headers,
                duplicate_ids=duplicate_ids,
                duplicate_rows=duplicate_rows,
                numeric_rows=numeric_rows,
                unsourced_numeric_rows=unsourced_numeric_rows,
                missing_location_rows=missing_location_rows,
                unit_conflicts=dataset_unit_conflicts,
                basis_conflicts=dataset_basis_conflicts,
                cross_reference_issues=cross_reference_issues,
                equation_missing_inputs=equation_missing_inputs,
                equation_symbol_mismatches=equation_symbol_mismatches,
                cost_overlap_flags=cost_overlap_flags,
                standardized_statuses=standardized_statuses,
                dataset_readiness=readiness,
                notes=" ".join(notes),
            )
        )

    cost_overlap_rows = []
    for key, entries in cost_entries_by_key.items():
        rels = sorted({path.relative_to(DATA_ROOT).as_posix() for path, _, _ in entries})
        if len(rels) > 1 and key[1]:
            cost_overlap_rows.append(
                {
                    "equipment_or_technology": key[0],
                    "python_variable": key[1],
                    "cost_scope_or_basis": key[2],
                    "dataset_count": len(rels),
                    "datasets": "; ".join(rels),
                    "double_counting_risk": "review_required",
                }
            )
            for rel in rels:
                validation_issues.append(
                    {
                        "issue_type": "potential_cost_double_counting",
                        "dataset_path": rel,
                        "row_id": key[1],
                        "python_variable": key[1],
                        "details": f"Cost-like variable also appears in: {'; '.join(rels)}",
                        "severity": "medium",
                    }
                )

    manifest_rows = [
        {
            "dataset_path": summary.path.as_posix(),
            "category": summary.category,
            "subgroup": summary.subgroup,
            "filename": summary.path.name,
            "row_count_observed": summary.row_count,
            "header_count": len(summary.headers),
            "headers": "; ".join(summary.headers),
            "standardized_status_values": summary.standardized_statuses,
            "detected_readiness": summary.dataset_readiness,
            "notes": summary.notes,
        }
        for summary in dataset_summaries
    ]

    readiness_rows = [
        {
            "dataset_path": summary.path.as_posix(),
            "category": summary.category,
            "subgroup": summary.subgroup,
            "readiness": summary.dataset_readiness,
            "duplicate_ids": summary.duplicate_ids,
            "duplicate_rows": summary.duplicate_rows,
            "numeric_rows": summary.numeric_rows,
            "unsourced_numeric_rows": summary.unsourced_numeric_rows,
            "numeric_rows_missing_exact_location": summary.missing_location_rows,
            "unit_conflicts": summary.unit_conflicts,
            "basis_conflicts": summary.basis_conflicts,
            "cross_reference_issues": summary.cross_reference_issues,
            "equation_missing_inputs": summary.equation_missing_inputs,
            "equation_symbol_mismatches": summary.equation_symbol_mismatches,
            "notes": summary.notes,
        }
        for summary in dataset_summaries
    ]

    variable_dictionary_rows = []
    seen_variable_keys = set()
    for row in variable_rows:
        key = (row["dataset_path"], row["python_variable"], row["numeric_column"], row["original_unit"], row["basis"])
        if key in seen_variable_keys:
            continue
        seen_variable_keys.add(key)
        variable_dictionary_rows.append(row)

    write_csv(
        OUTPUT_DIR / "global_dataset_manifest.csv",
        [
            "dataset_path",
            "category",
            "subgroup",
            "filename",
            "row_count_observed",
            "header_count",
            "headers",
            "standardized_status_values",
            "detected_readiness",
            "notes",
        ],
        manifest_rows,
    )
    write_csv(
        OUTPUT_DIR / "global_source_register.csv",
        [
            "dataset_path",
            "dataset_group",
            "source_id",
            "source_title",
            "authors",
            "year",
            "doi_or_stable_id",
            "url",
            "source_type",
            "notes",
        ],
        source_register_entries,
    )
    write_csv(
        OUTPUT_DIR / "global_unit_registry.csv",
        [
            "dataset_path",
            "dataset_group",
            "column_name",
            "unit_text",
            "status_standardized",
        ],
        unit_rows,
    )
    write_csv(
        OUTPUT_DIR / "global_equation_registry.csv",
        [
            "dataset_path",
            "dataset_group",
            "equation_id",
            "equation_name",
            "python_expression",
            "symbol_definition_field",
            "status_standardized",
            "source_id",
            "source_title",
            "exact_location",
            "undefined_expression_symbols",
            "likely_missing_inputs",
        ],
        equation_rows,
    )
    write_csv(
        OUTPUT_DIR / "global_missing_data_register.csv",
        [
            "dataset_path",
            "dataset_group",
            "missing_item_id",
            "target_file",
            "python_variable",
            "reason_missing",
            "required_for",
            "priority",
            "status_standardized",
        ],
        missing_rows,
    )
    write_csv(
        OUTPUT_DIR / "global_dataset_readiness.csv",
        [
            "dataset_path",
            "category",
            "subgroup",
            "readiness",
            "duplicate_ids",
            "duplicate_rows",
            "numeric_rows",
            "unsourced_numeric_rows",
            "numeric_rows_missing_exact_location",
            "unit_conflicts",
            "basis_conflicts",
            "cross_reference_issues",
            "equation_missing_inputs",
            "equation_symbol_mismatches",
            "notes",
        ],
        readiness_rows,
    )
    write_csv(
        OUTPUT_DIR / "global_variable_dictionary.csv",
        [
            "dataset_path",
            "dataset_group",
            "row_id",
            "python_variable",
            "parameter_name",
            "numeric_column",
            "original_value",
            "original_unit",
            "normalized_si_value",
            "normalized_si_unit",
            "basis",
            "status_original",
            "status_standardized",
            "source_id",
            "source_title",
            "exact_location",
        ],
        variable_dictionary_rows,
    )
    write_csv(
        OUTPUT_DIR / "global_cost_overlap_register.csv",
        [
            "equipment_or_technology",
            "python_variable",
            "cost_scope_or_basis",
            "dataset_count",
            "datasets",
            "double_counting_risk",
        ],
        cost_overlap_rows,
    )
    write_csv(
        OUTPUT_DIR / "global_validation_issues.csv",
        [
            "issue_type",
            "dataset_path",
            "row_id",
            "python_variable",
            "details",
            "severity",
        ],
        validation_issues,
    )

    summary = {
        "generated_at": "2026-07-29",
        "dataset_count": len(dataset_summaries),
        "issue_count": len(validation_issues),
        "issue_counts_by_type": dict(Counter(issue["issue_type"] for issue in validation_issues)),
        "readiness_counts": dict(Counter(row["readiness"] for row in readiness_rows)),
    }
    (OUTPUT_DIR / "global_validation_summary.json").write_text(
        json.dumps(summary, indent=2),
        encoding="utf-8",
    )
    report_lines = [
        "# GreenHub Literature Dataset Audit",
        "",
        f"- Audited CSV datasets: {len(dataset_summaries)}",
        f"- Total flagged issues: {len(validation_issues)}",
        f"- Readiness counts: {summary['readiness_counts']}",
        f"- Issue counts by type: {summary['issue_counts_by_type']}",
        "",
        "## Main findings",
        "",
        "- Readiness was assigned conservatively. No dataset was promoted to D4 or D5 in this packaging task.",
        "- D1 indicates duplicated identifiers within a dataset or broken file references.",
        "- D2 indicates structurally loadable datasets whose equation packages still have unresolved input or symbol gaps.",
        "- D3 indicates datasets that are loadable at schema level, but not calculation-connected by this audit.",
        "- Potential cost overlap flags indicate places where CAPEX-like variables appear in multiple datasets and should be reviewed before any TEA integration.",
        "",
        "## Output package",
        "",
        "- global_dataset_manifest.csv",
        "- global_source_register.csv",
        "- global_unit_registry.csv",
        "- global_equation_registry.csv",
        "- global_missing_data_register.csv",
        "- global_dataset_readiness.csv",
        "- global_variable_dictionary.csv",
        "- global_cost_overlap_register.csv",
        "- global_validation_issues.csv",
        "- global_validation_summary.json",
        "",
    ]
    (OUTPUT_DIR / "global_validation_report.md").write_text("\n".join(report_lines), encoding="utf-8")


if __name__ == "__main__":
    main()
