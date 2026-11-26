from __future__ import annotations

import ast
import csv
import json
import re
from collections import Counter
from pathlib import Path


ROOT = Path.cwd()
DATA_ROOT = ROOT / "Greenhub" / "data"
OUT_DIR = ROOT / "Greenhub" / "results"
OUT_JSON = OUT_DIR / "economic_inventory_catalog.json"
OUT_CSV = OUT_DIR / "economic_inventory_catalog.csv"

COST_TERMS = (
    "cost", "capex", "opex", "price", "currency", "eur", "usd",
    "purchase", "installed", "maintenance", "replacement",
)
SCALING_TERMS = (
    "scaling", "scale", "exponent", "reference_capacity",
    "capacity_basis", "capacity", "throughput",
)
EQUIPMENT_TERMS = (
    "equipment", "reactor", "digester", "tank", "pump", "column",
    "stripper", "absorber", "membrane", "centrifuge", "decanter",
    "dryer", "press", "separator", "chp", "engine", "compressor",
    "blower", "heat exchanger", "evaporator", "electrodialysis",
    "ion exchange", "psa", "scrubber", "packing", "mixer",
)
CONSUMABLE_TERMS = (
    "consumable", "reagent", "chemical", "acid", "base", "naoh",
    "caoh", "cao", "enzyme", "solvent", "mea", "polymer", "media",
    "adsorbent", "resin", "membrane module", "water", "makeup",
)
UTILITY_TERMS = (
    "utility", "electricity", "energy", "heat", "steam", "cooling",
    "power", "fuel", "duty",
)
SCENARIO_TERMS = ("scenario", "controller", "mode", "pathway")

CATALOG_COLUMNS = [
    "process_area",
    "process_step",
    "scenario_id",
    "item_category",
    "item_name",
    "parameter_id",
    "python_variable",
    "role_or_description",
    "quantity_value",
    "quantity_unit",
    "cost_value",
    "cost_unit",
    "currency",
    "cost_year",
    "scaling_factor",
    "scaling_reference_capacity",
    "scaling_reference_unit",
    "capacity_basis",
    "data_status",
    "source_id",
    "source_title",
    "doi_or_url",
    "source_file",
    "source_row",
    "notes",
    "tea_readiness",
]


def clean(value: object) -> str:
    if value is None:
        return ""
    return str(value).replace("\r", " ").replace("\n", " ").strip()


def lower_join(values: list[str]) -> str:
    return " ".join(clean(v).lower() for v in values if clean(v))


def rel(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def process_area_from_path(path: Path) -> tuple[str, str]:
    try:
        parts = path.relative_to(DATA_ROOT).parts
    except ValueError:
        return ("code/docs", "")
    if len(parts) >= 2:
        return (parts[0], parts[1])
    if parts:
        return (parts[0], "")
    return ("", "")


def first(row: dict[str, str], names: tuple[str, ...]) -> str:
    by_lower = {str(k).lower(): k for k in row if k is not None}
    for name in names:
        key = by_lower.get(name.lower())
        if key is not None and clean(row.get(key)):
            return clean(row.get(key))
    for key, value in row.items():
        if key is None:
            continue
        lk = key.lower()
        if any(name.lower() in lk for name in names) and clean(value):
            return clean(value)
    return ""


def numeric_like(value: str) -> bool:
    text = clean(value).replace(",", "")
    return bool(re.fullmatch(r"[-+]?\d+(\.\d+)?([eE][-+]?\d+)?", text))


def classify_category(path: Path, row: dict[str, str]) -> str:
    text = lower_join([rel(path), *row.keys(), *row.values()])
    if any(term in text for term in COST_TERMS):
        if any(term in text for term in EQUIPMENT_TERMS):
            return "equipment_cost"
        return "cost_or_price"
    if any(term in text for term in CONSUMABLE_TERMS):
        return "consumable"
    if any(term in text for term in UTILITY_TERMS):
        return "utility"
    if any(term in text for term in EQUIPMENT_TERMS):
        return "equipment"
    if any(term in text for term in SCENARIO_TERMS):
        return "scenario"
    if "missing" in text or "assumption" in text:
        return "missing_or_assumption"
    return "process_parameter"


def is_relevant_file(path: Path) -> bool:
    text = rel(path).lower()
    terms = COST_TERMS + SCALING_TERMS + EQUIPMENT_TERMS + CONSUMABLE_TERMS + UTILITY_TERMS + SCENARIO_TERMS
    return any(term in text for term in terms) or path.name in {
        "dataset_manifest.csv",
        "source_register.csv",
        "global_cost_overlap_register.csv",
        "cost_ownership_registry.csv",
    }


def is_relevant_row(path: Path, row: dict[str, str]) -> bool:
    if is_relevant_file(path):
        return True
    text = lower_join([*row.keys(), *row.values()])
    terms = COST_TERMS + SCALING_TERMS + EQUIPMENT_TERMS + CONSUMABLE_TERMS + UTILITY_TERMS + SCENARIO_TERMS
    return any(term in text for term in terms)


def value_from_fields(row: dict[str, str], keywords: tuple[str, ...]) -> str:
    for key, value in row.items():
        if key is None:
            continue
        lk = key.lower()
        if any(term in lk for term in keywords) and clean(value):
            return clean(value)
    return ""


def build_catalog_row(path: Path, row: dict[str, str], row_num: int) -> dict[str, str]:
    major, minor = process_area_from_path(path)
    category = classify_category(path, row)
    item_name = first(row, (
        "equipment_type", "equipment_name", "item_name", "name", "parameter_name",
        "python_variable", "equation_name", "process", "unit_operation", "cost_id",
        "parameter_id",
    ))
    parameter_id = first(row, ("parameter_id", "cost_id", "equipment_id", "equation_id", "dataset_id"))
    process_step = first(row, ("process", "unit_operation", "equipment_type", "technology", "pathway"))
    quantity_value = first(row, ("value", "normalized_si_value", "capacity", "energy", "demand", "rate"))
    quantity_unit = first(row, ("unit", "normalized_si_unit", "capacity_unit", "energy_unit", "demand_unit", "rate_unit"))
    cost_value = value_from_fields(row, ("purchase_cost", "installed_cost", "equipment_cost", "module_cost", "cost", "price"))
    cost_unit = first(row, ("cost_unit", "price_unit", "polymer_unit_cost_unit", "unit"))
    currency = first(row, ("currency",))
    cost_year = first(row, ("cost_year", "year"))
    scaling_factor = first(row, ("scaling_exponent", "scale_exponent", "scaling_factor", "exponent"))
    source_url = first(row, ("source_url", "doi_or_stable_identifier", "doi", "url"))
    data_status = first(row, ("data_status", "cost_status", "status", "activation_status", "readiness_status"))
    notes = first(row, ("notes", "limitations", "limitation", "blocked_reason", "recommended_next_action"))

    missing_cost = category in {"equipment_cost", "cost_or_price"} and not cost_value
    has_cost = bool(cost_value and (numeric_like(cost_value) or currency or "eur" in cost_unit.lower() or "usd" in cost_unit.lower()))
    has_scaling = bool(scaling_factor)
    if "missing" in lower_join([data_status, notes, item_name, parameter_id]):
        readiness = "missing_or_blocked"
    elif has_cost or has_scaling:
        readiness = "has_cost_or_scaling_data"
    elif missing_cost:
        readiness = "needs_cost_data"
    elif category in {"equipment", "consumable", "utility"}:
        readiness = "inventory_identified_needs_cost_basis"
    else:
        readiness = "reference_or_process_context"

    return {
        "process_area": major,
        "process_step": process_step or minor,
        "scenario_id": first(row, ("scenario_id", "scenario", "mode_id", "pathway_id")),
        "item_category": category,
        "item_name": item_name,
        "parameter_id": parameter_id,
        "python_variable": first(row, ("python_variable",)),
        "role_or_description": first(row, ("description", "basis", "applicability", "parameter_description")),
        "quantity_value": quantity_value,
        "quantity_unit": quantity_unit,
        "cost_value": cost_value,
        "cost_unit": cost_unit,
        "currency": currency,
        "cost_year": cost_year,
        "scaling_factor": scaling_factor,
        "scaling_reference_capacity": first(row, ("scaling_reference_capacity", "reference_capacity")),
        "scaling_reference_unit": first(row, ("scaling_reference_unit", "reference_capacity_unit")),
        "capacity_basis": first(row, ("capacity_basis", "capacity", "capacity_unit", "valid_range")),
        "data_status": data_status,
        "source_id": first(row, ("source_id",)),
        "source_title": first(row, ("source_title", "source")),
        "doi_or_url": source_url,
        "source_file": rel(path),
        "source_row": str(row_num),
        "notes": notes,
        "tea_readiness": readiness,
    }


def read_csv_rows(path: Path) -> list[dict[str, str]]:
    for encoding in ("utf-8-sig", "utf-8", "cp1252"):
        try:
            with path.open("r", encoding=encoding, newline="") as handle:
                sample = handle.read(4096)
                handle.seek(0)
                dialect = csv.Sniffer().sniff(sample) if sample.strip() else csv.excel
                reader = csv.DictReader(handle, dialect=dialect)
                return [dict(row) for row in reader]
        except Exception:
            continue
    return []


def collect_catalog() -> tuple[list[dict[str, str]], list[dict[str, str]], list[dict[str, str]]]:
    catalog: list[dict[str, str]] = []
    scenarios: list[dict[str, str]] = []
    sources: list[dict[str, str]] = []

    for path in sorted(DATA_ROOT.rglob("*.csv")):
        rows = read_csv_rows(path)
        if not rows:
            continue
        major, minor = process_area_from_path(path)
        source_record = {
            "source_file": rel(path),
            "process_area": major,
            "process_step": minor,
            "row_count": str(len(rows)),
            "included_reason": "relevant" if is_relevant_file(path) else "scanned",
        }
        sources.append(source_record)
        for idx, row in enumerate(rows, start=2):
            if is_relevant_row(path, row):
                catalog.append(build_catalog_row(path, row, idx))
            if "scenario" in path.name.lower() or first(row, ("scenario_id", "scenario")):
                scenarios.append({
                    "process_area": major,
                    "process_step": minor,
                    "scenario_id": first(row, ("scenario_id", "scenario", "mode_id", "pathway_id")),
                    "scenario_name": first(row, ("scenario_name", "name", "description", "python_variable")),
                    "technology_or_process": first(row, ("technology", "process", "unit_operation", "equipment_type")),
                    "data_status": first(row, ("data_status", "status", "activation_status")),
                    "source_file": rel(path),
                    "source_row": str(idx),
                    "notes": first(row, ("notes", "limitations", "basis")),
                })

    return catalog, scenarios, sources


def collect_code_units() -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    unit_files = [
        ROOT / "Greenhub" / "units.py",
        ROOT / "Greenhub" / "phase3_units.py",
        ROOT / "Greenhub" / "phase4_units.py",
        ROOT / "Greenhub" / "phase5_units.py",
        ROOT / "Greenhub" / "phase6_units.py",
        ROOT / "Greenhub" / "phase7_units.py",
        ROOT / "Greenhub" / "dynamic_biosteam_units.py",
        ROOT / "Greenhub" / "logistics.py",
        ROOT / "Greenhub" / "storage.py",
        ROOT / "Greenhub" / "dynamic_economic_environmental.py",
    ]
    class_pattern = re.compile(r"^\s*class\s+([A-Za-z_][A-Za-z0-9_]*)")
    factor_pattern = re.compile(r'"([^"]+)":\s*\(([-+0-9.eE]+),\s*"([^"]+)"\)')
    for path in unit_files:
        if not path.exists():
            continue
        text = path.read_text(encoding="utf-8", errors="ignore")
        for line_no, line in enumerate(text.splitlines(), start=1):
            match = class_pattern.match(line)
            if match:
                rows.append({
                    "record_type": "unit_or_helper_class",
                    "name": match.group(1),
                    "value": "",
                    "unit": "",
                    "source_file": rel(path),
                    "source_line": str(line_no),
                    "notes": "Code class; include for equipment/process inventory boundary review.",
                })
            for factor, value, unit in factor_pattern.findall(line):
                rows.append({
                    "record_type": "economic_default_factor",
                    "name": factor,
                    "value": value,
                    "unit": unit,
                    "source_file": rel(path),
                    "source_line": str(line_no),
                    "notes": "Default economic/environmental proxy factor in code.",
                })
    return rows


def collect_global_notes() -> list[dict[str, str]]:
    notes: list[dict[str, str]] = []
    summary_path = ROOT / "Greenhub" / "data" / "global_audit_package" / "checkpoint1_registry_summary.json"
    if summary_path.exists():
        data = json.loads(summary_path.read_text(encoding="utf-8"))
        for key, value in data.items():
            if "cost" in key.lower():
                notes.append({
                    "topic": key,
                    "value": str(value),
                    "source_file": rel(summary_path),
                    "notes": "Global audit package cost-overlap status.",
                })
    return notes


def write_csv(path: Path, rows: list[dict[str, str]], columns: list[str]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    catalog, scenarios, sources = collect_catalog()
    code_units = collect_code_units()
    global_notes = collect_global_notes()

    known_costs_scaling = [
        row for row in catalog
        if row["tea_readiness"] == "has_cost_or_scaling_data"
        or row["cost_value"] or row["scaling_factor"]
    ]
    missing_costs = [
        row for row in catalog
        if row["tea_readiness"] in {"missing_or_blocked", "needs_cost_data", "inventory_identified_needs_cost_basis"}
    ]
    category_counts = Counter(row["item_category"] for row in catalog)
    readiness_counts = Counter(row["tea_readiness"] for row in catalog)

    readme = [
        {
            "topic": "scope",
            "value": "Greenhub/data source CSVs plus selected process/economic code; historical Greenhub/results/run outputs excluded to avoid stale duplicate inventories.",
        },
        {
            "topic": "interpretation",
            "value": "Rows preserve available values, units, cost years, currencies, scaling exponents and source files. Blank costs mean not found in source, not zero.",
        },
        {
            "topic": "cost_overlap_warning",
            "value": "Global audit records unresolved cost overlaps; cost records should not be aggregated until ownership/boundaries are resolved.",
        },
    ]

    payload = {
        "readme": readme,
        "summary": {
            "catalog_rows": len(catalog),
            "scenario_rows": len(scenarios),
            "known_cost_or_scaling_rows": len(known_costs_scaling),
            "missing_or_needs_basis_rows": len(missing_costs),
            "category_counts": dict(category_counts),
            "readiness_counts": dict(readiness_counts),
        },
        "inventory_cost_catalog": catalog,
        "process_scenarios": scenarios,
        "known_costs_scaling": known_costs_scaling,
        "missing_cost_items": missing_costs,
        "code_units_utilities": code_units,
        "source_files": sources,
        "global_notes": global_notes,
    }
    OUT_JSON.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    write_csv(OUT_CSV, catalog, CATALOG_COLUMNS)
    print(json.dumps(payload["summary"], indent=2))
    print(str(OUT_JSON))
    print(str(OUT_CSV))


if __name__ == "__main__":
    main()
