"""Add traceable Dutch G-gas injection requirements as reference data only.

The law specifies gas-quality limits, not a universal biomethane methane
percentage. These records are deliberately not connected to runtime defaults.
"""
from __future__ import annotations

import csv
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "Greenhub" / "data"
PACKAGE = DATA / "Bigas production + upgrade" / "Common_Conditioning"
AUDIT = DATA / "global_audit_package"
SOURCE_ID = "SRC-NL-ENERGIEREGELING-G-QUALITY-2026"
SOURCE_TITLE = "Energieregeling, Annex 1, Part B: G-gas at injection into a connection or system coupling"
SOURCE_URL = "https://zoek.officielebekendmakingen.nl/stcrt-2025-37730.html"
SOURCE_ID_TEXT = "Staatscourant 2025, 37730"
RETRIEVED = "2026-11-08"
DATASET = "Bigas production + upgrade/Common_Conditioning/biomethane_specifications.csv"

SPEC_FIELDS = [
    "parameter_id", "python_variable", "value", "unit", "normalized_si_value",
    "normalized_si_unit", "basis", "process", "material_feed_type",
    "operating_conditions", "valid_range", "data_status", "source_id",
    "source_title", "authors", "year", "doi_or_stable_id", "exact_location",
    "notes", "uncertainty", "transferability", "country", "specification_year",
]
EQUATION_ID = "EQ_CC_NL_2026_G_GAS_CO2_CONDITIONAL_MAX"
EQUATION_FIELDS = [
    "equation_id", "equation_name", "exact_source_equation", "python_expression",
    "dependent_variable", "symbol_definitions", "units", "applicability",
    "original_material_or_system", "transferability", "source_id", "source_title",
    "authors", "year", "doi_or_stable_id", "exact_location", "limitations",
    "data_status",
]


def _read(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        return list(reader.fieldnames or []), list(reader)


def _write(path: Path, fields: list[str], rows: list[dict[str, object]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n", extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def _append_once(path: Path, row: dict[str, object], key: str) -> bool:
    fields, rows = _read(path)
    key_value = str(row.get(key, ""))
    existing = [item for item in rows if item.get(key, "") == key_value]
    if existing:
        expected = {field: str(row.get(field, "")) for field in fields}
        if len(existing) != 1 or any(existing[0].get(field, "") != value for field, value in expected.items()):
            raise ValueError(f"Conflicting {key}={key_value!r} in {path}")
        return False
    rows.append({field: str(row.get(field, "")) for field in fields})
    _write(path, fields, rows)
    return True


def _spec(
    code: str,
    name: str,
    value: str,
    unit: str,
    conditions: str,
    location: str,
    note: str = "",
) -> dict[str, str]:
    return {
        "parameter_id": f"BMS_NL_2026_GGAS_{code}",
        "python_variable": f"nl_2026_ggas_{name}",
        "value": value,
        "unit": unit,
        "normalized_si_value": value,
        "normalized_si_unit": unit,
        "basis": "Dutch statutory G-gas injection quality requirement; exact network category applies",
        "process": "biomethane grid injection",
        "material_feed_type": "G-gas at injection into a connection or system coupling",
        "operating_conditions": conditions,
        "valid_range": "statutory limit; see stated category and Annex 1 footnotes",
        "data_status": "official_regulatory_requirement",
        "source_id": SOURCE_ID,
        "source_title": SOURCE_TITLE,
        "authors": "Minister of Climate Policy and Green Growth, Netherlands",
        "year": "2025",
        "doi_or_stable_id": SOURCE_ID_TEXT,
        "exact_location": location,
        "notes": (note + " " if note else "") + (
            "Effective from 2026-01-01. Reference-only: do not treat as a universal product target or runtime default."
        ),
        "uncertainty": "Not a statistical estimate; applicability depends on the statutory network category and any listed exception.",
        "transferability": "direct only for Dutch G-gas injection in the stated connection/network category",
        "country": "Netherlands",
        "specification_year": "2026",
    }


ANNEX_B = "Annex 1, Part B (G-gas at injection into a connection or system coupling)"
ROWS = [
    _spec("WOBBE_MIN_STANDARD", "wobbe_min_standard", "43.46", "MJ/m3(n)", "standard band; hourly averages", f"{ANNEX_B}, Wobbe-index row", "Footnote 1 permits only bounded and frequency-limited excursions below the standard band."),
    _spec("WOBBE_MAX_STANDARD", "wobbe_max_standard", "44.41", "MJ/m3(n)", "standard band; hourly averages", f"{ANNEX_B}, Wobbe-index row", "Footnote 2 permits limited exceedances only for a distribution around the upper bound with standard deviation at most 0.1 MJ/m3(n)."),
    _spec("WOBBE_MIN_ABSOLUTE", "wobbe_min_absolute", "42.96", "MJ/m3(n)", "absolute bound when gas is at least 99 mol% combined CH4, CO2, N2 and O2", f"{ANNEX_B}, footnote 1 to Wobbe-index row"),
    _spec("WOBBE_MAX_ABSOLUTE", "wobbe_max_absolute", "44.91", "MJ/m3(n)", "absolute bound when gas is at least 99 mol% combined CH4, CO2, N2 and O2", f"{ANNEX_B}, footnote 1 to Wobbe-index row"),
    _spec("HIGHER_HC_MAX", "higher_hydrocarbons_max", "5", "mol% propane equivalent", "all G-gas injection categories", f"{ANNEX_B}, higher-hydrocarbons row"),
    _spec("GAS_CONDENSATE_MAX", "gas_condensate_max", "80", "mg/m3(n)", "at -3 degC, at every pressure", f"{ANNEX_B}, gas-condensate row"),
    _spec("WATER_DEW_POINT_RTL_HTL_MAX", "water_dew_point_rtl_htl_max", "-8", "degC", "RTL and HTL; at 70 bar(a)", f"{ANNEX_B}, water-dew-point row"),
    _spec("WATER_DEW_POINT_DISTRIBUTION_MAX", "water_dew_point_distribution_max", "-10", "degC", "gas distribution system; at 8 bar(a)", f"{ANNEX_B}, water-dew-point row"),
    _spec("TEMP_RTL_HTL_MIN", "temperature_rtl_htl_min", "5", "degC", "RTL and HTL", f"{ANNEX_B}, temperature row"),
    _spec("TEMP_RTL_HTL_MAX", "temperature_rtl_htl_max", "30", "degC", "RTL and HTL", f"{ANNEX_B}, temperature row"),
    _spec("TEMP_DISTRIBUTION_MIN", "temperature_distribution_min", "5", "degC", "gas distribution system; footnote 3 allows conditional deviation", f"{ANNEX_B}, temperature row"),
    _spec("TEMP_DISTRIBUTION_MAX", "temperature_distribution_max", "20", "degC", "gas distribution system; footnote 3 allows conditional deviation", f"{ANNEX_B}, temperature row", "An alternative inlet temperature can be accepted subject to proof of material compatibility and reaching 5–20 degC at the connection valve."),
    _spec("O2_RTL_DISTRIBUTION_MAX", "o2_rtl_distribution_max", "0.5", "mol%", "RTL and gas distribution system", f"{ANNEX_B}, oxygen row"),
    _spec("O2_HTL_MAX", "o2_htl_max", "0.0005", "mol%", "HTL", f"{ANNEX_B}, oxygen row"),
    _spec("CO2_RTL_DISTRIBUTION_TABLE_MAX", "co2_rtl_distribution_table_max", "10.34", "mol%", "RTL and gas distribution system, subject to footnote 4 and connection exceptions", f"{ANNEX_B}, carbon-dioxide row and footnote 4", "For CO2 above 6 mol% and combined CH4+CO2+N2+O2 at least 99 mol%, the conditional formula and 3 mol% exceptions may impose a lower maximum."),
    _spec("CO2_HTL_MAX", "co2_htl_max", "3", "mol%", "HTL", f"{ANNEX_B}, carbon-dioxide row"),
    _spec("H2_HTL_MAX", "h2_htl_max", "0.02", "mol%", "HTL", f"{ANNEX_B}, hydrogen row"),
    _spec("H2_RTL_DISTRIBUTION_MAX", "h2_rtl_distribution_max", "0.5", "mol%", "RTL and gas distribution system", f"{ANNEX_B}, hydrogen row"),
    _spec("ORGANIC_CHLORINE_MAX", "organic_chlorine_max", "5", "mg Cl/m3(n)", "as organochlorine compounds", f"{ANNEX_B}, chlorine row"),
    _spec("ORGANIC_FLUORINE_MAX", "organic_fluorine_max", "5", "mg F/m3(n)", "as organofluorine compounds", f"{ANNEX_B}, fluorine row"),
    _spec("CO_MAX", "carbon_monoxide_max", "2900", "mg/m3(n)", "all G-gas injection categories", f"{ANNEX_B}, carbon-monoxide row"),
    _spec("PATHOGENIC_MICROBES_MAX", "pathogenic_microbes_max", "500", "count/m3(n)", "all G-gas injection categories", f"{ANNEX_B}, pathogenic-microbes row"),
    _spec("PARTICLES_GT_5UM_MAX", "particles_gt_5um_max", "100", "mg/m3(n)", "particles larger than 5 micrometres", f"{ANNEX_B}, particles row"),
    _spec("INORGANIC_SULPHUR_MAX", "inorganic_sulphur_max", "5", "mg S/m3(n)", "as inorganically bound sulphur", f"{ANNEX_B}, inorganic-sulphur row"),
    _spec("ALKYLTHIOLS_MAX", "alkylthiols_max", "6", "mg S/m3(n)", "as alkylthiols", f"{ANNEX_B}, alkylthiols row"),
    _spec("TOTAL_S_PRE_ODOR_PEAK_MAX", "total_s_pre_odor_peak_max", "20", "mg S/m3(n)", "before odorization; peak value", f"{ANNEX_B}, total-sulphur row"),
    _spec("TOTAL_S_PRE_ODOR_ANNUAL_AVG_MAX", "total_s_pre_odor_annual_avg_max", "5.5", "mg S/m3(n)", "before odorization; annual average", f"{ANNEX_B}, total-sulphur row"),
    _spec("TOTAL_S_POST_ODOR_PEAK_MAX", "total_s_post_odor_peak_max", "31", "mg S/m3(n)", "after odorization; peak value", f"{ANNEX_B}, total-sulphur row"),
    _spec("TOTAL_S_POST_ODOR_ANNUAL_AVG_MAX", "total_s_post_odor_annual_avg_max", "16.5", "mg S/m3(n)", "after odorization; annual average", f"{ANNEX_B}, total-sulphur row"),
    _spec("THT_HTL_FLEVOLAND_MIN", "tht_htl_flevoland_min", "10", "mg THT/m3(n)", "HTL Flevoland; odorized gas", f"{ANNEX_B}, THT row and footnote 5"),
    _spec("THT_HTL_FLEVOLAND_MAX", "tht_htl_flevoland_max", "40", "mg THT/m3(n)", "HTL Flevoland; odorized gas", f"{ANNEX_B}, THT row and footnote 5"),
    _spec("THT_HTL_ODORLESS", "tht_htl_odorless", "0", "mg THT/m3(n)", "HTL; odorless gas", f"{ANNEX_B}, THT row and footnote 5"),
    _spec("THT_RTL_DISTRIBUTION_MIN", "tht_rtl_distribution_min", "10", "mg THT/m3(n)", "RTL or gas distribution system; odorized gas", f"{ANNEX_B}, THT row and footnote 5"),
    _spec("THT_RTL_DISTRIBUTION_MAX", "tht_rtl_distribution_max", "40", "mg THT/m3(n)", "RTL or gas distribution system; odorized gas", f"{ANNEX_B}, THT row and footnote 5"),
    _spec("SILICON_MAX", "silicon_max", "0.1", "mg Si/m3(n)", "as silicon-containing compounds", f"{ANNEX_B}, silicon row"),
]

EQUATION = {
    "equation_id": EQUATION_ID,
    "equation_name": "Conditional Dutch G-gas injection maximum for CO2",
    "exact_source_equation": "CO2_max = min(10.32 - 0.72*N2 - 0.87*O2, 10.56 - 0.746*N2 - 1.01*O2)",
    "python_expression": "co2_max_mol_percent = min(10.32 - 0.72*n2_mol_percent - 0.87*o2_mol_percent, 10.56 - 0.746*n2_mol_percent - 1.01*o2_mol_percent)",
    "dependent_variable": "CO2_max",
    "symbol_definitions": "N2 and O2 are injection-point mole percentages; coefficients and outputs are in mol%.",
    "units": "mol% for N2, O2, and CO2_max",
    "applicability": "Only when CH4+CO2+N2+O2 >= 99 mol% and CO2 > 6 mol%; check additional 3 mol% connection exceptions before use.",
    "original_material_or_system": "Dutch G-gas injection into a connection or system coupling",
    "transferability": "direct only under the specified Dutch G-gas legal conditions; not a universal upgrading target",
    "source_id": SOURCE_ID,
    "source_title": SOURCE_TITLE,
    "authors": "Minister of Climate Policy and Green Growth, Netherlands",
    "year": "2025",
    "doi_or_stable_id": SOURCE_ID_TEXT,
    "exact_location": f"{ANNEX_B}, footnote 4 to carbon-dioxide row",
    "limitations": "Reference formula only. Requires injection-point N2/O2, gas-composition scope test, and connection-exception selection. No approved typed runtime implementation or project connection classification.",
    "data_status": "official_regulatory_requirement",
}


def _append_or_validate(path: Path, rows: list[dict[str, str]], key: str, fields: list[str]) -> int:
    actual_fields, existing = _read(path)
    if actual_fields != fields:
        raise ValueError(f"Unexpected schema in {path}: {actual_fields}")
    by_key = {row[key]: row for row in existing}
    inserted = 0
    for row in rows:
        old = by_key.get(row[key])
        if old is not None:
            if any(old.get(field, "") != row.get(field, "") for field in fields):
                raise ValueError(f"Conflicting {key}={row[key]!r} in {path}")
            continue
        existing.append(row)
        by_key[row[key]] = row
        inserted += 1
    if inserted:
        _write(path, fields, existing)
    return inserted


def _upsert_manifest(path: Path, filename: str, count: int, limitations: str | None = None) -> None:
    fields, rows = _read(path)
    match = next((row for row in rows if row.get("file_name") == filename), None)
    if match is None:
        raise ValueError(f"Missing local manifest entry: {filename}")
    match["row_count"] = str(count)
    if limitations:
        match["limitations"] = limitations
    _write(path, fields, rows)


def _global_upsert(path: Path, row: dict[str, str], key: str) -> None:
    fields, rows = _read(path)
    existing = next((item for item in rows if item.get(key) == row.get(key)), None)
    if existing is not None:
        for field in fields:
            if field in row and existing.get(field, "") != row[field]:
                raise ValueError(f"Conflicting {key}={row.get(key)!r} in {path}, field {field}")
        return
    rows.append({field: row.get(field, "") for field in fields})
    _write(path, fields, rows)


def _sync_audit(spec_rows: list[dict[str, str]], spec_count: int) -> None:
    manifest_path = AUDIT / "global_dataset_manifest.csv"
    readiness_path = AUDIT / "global_dataset_readiness.csv"
    readiness_fields, readiness = _read(readiness_path)
    # Rebuild this generated index from its intact readiness index and the
    # authoritative CSV inputs. This also repairs a malformed prior manifest
    # header without touching any scientific input values.
    manifest_fields = [
        "dataset_path", "category", "subgroup", "filename", "row_count_observed",
        "header_count", "headers", "standardized_status_values", "detected_readiness", "notes",
    ]
    manifests: list[dict[str, str]] = []
    for ready_row in readiness:
        dataset_path = ready_row["dataset_path"]
        source_path = DATA / Path(dataset_path)
        headers, source_rows = _read(source_path)
        statuses = sorted({
            str(value).strip().lower().replace("-", "_").replace(" ", "_")
            for source_row in source_rows
            for key, value in source_row.items()
            if key in {"data_status", "status", "integration_status", "quality_class", "activation_state"} and str(value).strip()
        })
        manifests.append({
            "dataset_path": dataset_path,
            "category": ready_row.get("category", ""),
            "subgroup": ready_row.get("subgroup", ""),
            "filename": source_path.name,
            "row_count_observed": str(len(source_rows)),
            "header_count": str(len(headers)),
            "headers": "; ".join(headers),
            "standardized_status_values": ";".join(statuses),
            "detected_readiness": ready_row.get("readiness", ""),
            "notes": ready_row.get("notes", ""),
        })
    manifest = next(row for row in manifests if row.get("dataset_path") == DATASET)
    manifest["row_count_observed"] = str(spec_count)
    manifest["standardized_status_values"] = "literature_reported;official_regulatory_requirement"
    manifest["notes"] = "Historical literature and current Dutch statutory G-gas data remain country/year/network separated; reference only."
    equation_specs = [
        ("Bigas production + upgrade/Common_Conditioning/conditioning_equation_registry.csv", "conditioning_equation_registry.csv"),
        ("Bigas production + upgrade/Common_Conditioning/equation_registry.csv", "equation_registry.csv"),
    ]
    for dataset_path, _ in equation_specs:
        row = next(item for item in manifests if item.get("dataset_path") == dataset_path)
        row["row_count_observed"] = "4"
        row["standardized_status_values"] = "assumption;calculated_from_source_formula;fitted_by_source;official_regulatory_requirement"
    _write(manifest_path, manifest_fields, manifests)

    row = next(item for item in readiness if item.get("dataset_path") == DATASET)
    row["numeric_rows"] = str(spec_count)
    row["notes"] = "Historical sources retain four unresolved basis conflicts; Dutch 2026 statutory rows have traceable locations and remain reference-only, with no connection-specific runtime activation."
    for dataset_path, _ in equation_specs:
        row = next(item for item in readiness if item.get("dataset_path") == dataset_path)
        row["equation_missing_inputs"] = "4"
        row["notes"] = "Three prior equations plus one statutory conditional CO2 rule; the new rule lacks connection-specific typed inputs and remains blocked."
    _write(readiness_path, readiness_fields, readiness)

    source_row = {
        "dataset_path": DATASET,
        "dataset_group": "Common_Conditioning",
        "source_id": SOURCE_ID,
        "source_title": SOURCE_TITLE,
        "authors": "Minister of Climate Policy and Green Growth, Netherlands",
        "year": "2025",
        "doi_or_stable_id": SOURCE_ID_TEXT,
        "url": SOURCE_URL,
        "source_type": "official ministerial regulation",
        "notes": "Annex 1 Part B G-gas injection quality; effective 2026-01-01. Does not define a universal methane minimum; connection/operator applicability remains to be resolved.",
    }
    _global_upsert(AUDIT / "global_source_register.csv", source_row, "source_id")

    variable_path = AUDIT / "global_variable_dictionary.csv"
    variable_fields, variable_rows = _read(variable_path)
    existing_ids = {item.get("row_id", "") for item in variable_rows if item.get("dataset_path") == DATASET}
    for item in spec_rows:
        if item["parameter_id"] in existing_ids:
            continue
        for numeric_column in ("value", "normalized_si_value"):
            variable_rows.append({
                "dataset_path": DATASET,
                "dataset_group": "Common_Conditioning",
                "row_id": item["parameter_id"],
                "python_variable": item["python_variable"],
                "parameter_name": item["parameter_id"],
                "numeric_column": numeric_column,
                "original_value": item["value"],
                "original_unit": item["unit"],
                "normalized_si_value": item["normalized_si_value"],
                "normalized_si_unit": item["normalized_si_unit"],
                "basis": item["basis"],
                "status_original": item["data_status"],
                "status_standardized": "official_regulatory_requirement",
                "source_id": SOURCE_ID,
                "source_title": SOURCE_TITLE,
                "exact_location": item["exact_location"],
            })
    _write(variable_path, variable_fields, variable_rows)

    unit_path = AUDIT / "global_unit_registry.csv"
    unit_fields, unit_rows = _read(unit_path)
    unit_keys = {(item.get("dataset_path"), item.get("column_name"), item.get("unit_text"), item.get("status_standardized")) for item in unit_rows}
    for item in spec_rows:
        for column_name, unit_text in (("unit", item["unit"]), ("normalized_si_unit", item["normalized_si_unit"])):
            key = (DATASET, column_name, unit_text, "official_regulatory_requirement")
            if key not in unit_keys:
                unit_rows.append(dict(zip(unit_fields, key)))
                unit_keys.add(key)
    _write(unit_path, unit_fields, unit_rows)

    for dataset_path, _ in equation_specs:
        global_eq = {
            "dataset_path": dataset_path,
            "dataset_group": "Common_Conditioning",
            "equation_id": EQUATION_ID,
            "equation_name": EQUATION["equation_name"],
            "python_expression": EQUATION["python_expression"],
            "symbol_definition_field": "symbol_definitions",
            "status_standardized": "official_regulatory_requirement",
            "source_id": SOURCE_ID,
            "source_title": SOURCE_TITLE,
            "exact_location": EQUATION["exact_location"],
            "undefined_expression_symbols": "",
            "likely_missing_inputs": "connection category; injection-point N2 and O2; statutory exception applicability",
        }
        fields, equation_rows = _read(AUDIT / "global_equation_registry.csv")
        matches = [r for r in equation_rows if r.get("dataset_path") == dataset_path and r.get("equation_id") == EQUATION_ID]
        if not matches:
            equation_rows.append({field: global_eq.get(field, "") for field in fields})
            _write(AUDIT / "global_equation_registry.csv", fields, equation_rows)
        elif len(matches) != 1:
            raise ValueError(f"Unexpected duplicate equation registration for {dataset_path}")

    issue_path = AUDIT / "global_validation_issues.csv"
    issue_fields, issues = _read(issue_path)
    for dataset_path, _ in equation_specs:
        issue = {
            "issue_type": "equation_required_inputs_unavailable",
            "dataset_path": dataset_path,
            "row_id": EQUATION_ID,
            "python_variable": EQUATION["equation_name"],
            "details": "Lawful conditional rule is staged, but connection category, injection-point N2/O2, and exception state are not configured as typed project inputs.",
            "severity": "medium",
        }
        if not any(r.get("dataset_path") == dataset_path and r.get("row_id") == EQUATION_ID and r.get("issue_type") == issue["issue_type"] for r in issues):
            issues.append({field: issue.get(field, "") for field in issue_fields})
    _write(issue_path, issue_fields, issues)

    summary_path = AUDIT / "global_validation_summary.json"
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    issues = _read(issue_path)[1]
    counts: dict[str, int] = {}
    for item in issues:
        key = item.get("issue_type", "")
        counts[key] = counts.get(key, 0) + 1
    summary["issue_count"] = len(issues)
    summary["issue_counts_by_type"] = counts
    summary["generated_at"] = datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")
    summary_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _update_gap_register() -> None:
    for path in (
        ROOT / "docs" / "missing_data_gap_analysis.csv",
        DATA / "Pre-treatment" / "Feedstock" / "expanded_process_data_register.csv",
        DATA / "Pre-treatment" / "Feedstock" / "complete_missing_data_with_traceability.csv",
    ):
        fields, rows = _read(path)
        row = next(item for item in rows if item.get("gap_id") == "BG-001")
        row["status"] = "partially_implemented"
        row["suggested_source_or_estimation"] = SOURCE_URL + "; exact Dutch network operator connection agreement required"
        row["effect_on_model_outputs"] = "Statutory G-gas quality limits are available as reference evidence; exact project connection/operator acceptance, upgrading selection and revenue remain incomplete."
        row["data_required_and_units"] = "Connection category; CH4 product acceptance; CO2 mol%; H2S; moisture/dew point; O2/H2; pressure; Nm3(n) reference basis; operator-specific approval"
        row["repository_trace"] = "Greenhub/data/Bigas production + upgrade/Common_Conditioning/biomethane_specifications.csv; exact connection-specific acceptance still missing"
        _write(path, fields, rows)


def main() -> None:
    spec_path = PACKAGE / "biomethane_specifications.csv"
    _append_or_validate(spec_path, ROWS, "parameter_id", SPEC_FIELDS)
    _, all_specs = _read(spec_path)
    if len({row["parameter_id"] for row in all_specs}) != len(all_specs):
        raise ValueError("Duplicate parameter IDs in biomethane specifications")

    equation_rows_added = 0
    for filename in ("conditioning_equation_registry.csv", "equation_registry.csv"):
        equation_rows_added += _append_or_validate(PACKAGE / filename, [EQUATION], "equation_id", EQUATION_FIELDS)

    source = {
        "source_id": SOURCE_ID,
        "source_title": SOURCE_TITLE,
        "authors": "Minister of Climate Policy and Green Growth, Netherlands",
        "year": "2025",
        "doi_or_stable_id": SOURCE_ID_TEXT,
        "source_type": "official ministerial regulation",
        "publisher": "Government of the Netherlands",
        "url": SOURCE_URL,
        "accessed": RETRIEVED,
        "notes": "Annex 1 Part B statutory G-gas injection requirements effective 2026-01-01. Does not establish a universal methane minimum; network and connection applicability remains specific.",
    }
    source_added = _append_once(PACKAGE / "source_register.csv", source, "source_id")

    missing_path = PACKAGE / "assumption_and_missing_data_register.csv"
    missing_fields, missing_rows = _read(missing_path)
    missing_id = "AMR_BG_NL_2026_CONNECTION_CH4_TARGET"
    if not any(row.get("register_id") == missing_id for row in missing_rows):
        missing_rows.append({
            "register_id": missing_id,
            "related_file": "biomethane_specifications.csv",
            "parameter_id": "BMS_NL_2026_CONNECTION_CH4_MIN_UNSPECIFIED",
            "python_variable": "nl_2026_connection_specific_ch4_acceptance_missing",
            "status": "missing",
            "requirement_or_assumption": "A single minimum methane fraction is not specified by Annex 1 Part B; obtain the exact project connection/off-taker acceptance and network category.",
            "why_missing_or_limited": "A G-gas injection specification is multi-parameter and conditional; Wobbe, CO2 and network-specific limits cannot be reduced to one universal CH4 percentage.",
            "recommended_primary_source": "Written technical acceptance from the responsible Dutch gas network operator and intended off-taker; confirm exact injection point and gas-quality measurement protocol.",
            "integration_action": "Keep the 97 vol-% screening placeholder non-regulatory and non-default; do not activate until the target connection and required analyses are documented.",
            "priority": "high",
        })
        _write(missing_path, missing_fields, missing_rows)

    _upsert_manifest(PACKAGE / "dataset_manifest.csv", "biomethane_specifications.csv", len(all_specs), "Historical literature and Dutch 2026 statutory G-gas limits are separately country/year/network scoped. No universal CH4 minimum is supplied; exact project connection/operator acceptance is unresolved. Reference-only; no runtime default activation.")
    _upsert_manifest(PACKAGE / "dataset_manifest.csv", "conditioning_equation_registry.csv", 4)
    _upsert_manifest(PACKAGE / "dataset_manifest.csv", "equation_registry.csv", 4)
    _upsert_manifest(PACKAGE / "dataset_manifest.csv", "source_register.csv", len(_read(PACKAGE / "source_register.csv")[1]))
    _upsert_manifest(PACKAGE / "dataset_manifest.csv", "assumption_and_missing_data_register.csv", len(missing_rows))

    _sync_audit(ROWS, len(all_specs))
    _update_gap_register()

    sidecar = {
        "dataset_id": "urn:greenhub:dataset:common-conditioning:biomethane-specifications:v2",
        "dataset_version": "2.0.0",
        "dataset_file": "biomethane_specifications.csv",
        "record_count": len(all_specs),
        "sha256": hashlib.sha256(spec_path.read_bytes()).hexdigest(),
        "retrieval_date": RETRIEVED,
        "access_protocol": "UTF-8 CSV and HTTPS references",
        "source_ids": ["SRC001", "SRC002", SOURCE_ID],
        "new_source": {"title": SOURCE_TITLE, "stable_identifier": SOURCE_ID_TEXT, "url": SOURCE_URL, "effective_date": "2026-01-01", "source_location": "Annex 1 Part B and footnotes 1–6"},
        "evidence_class": "mixed historical literature and official statutory requirements; see row-level source metadata",
        "license_or_rights": "Government publication link; reuse governed by the source publication terms and applicable Dutch open-government rules. No CC license is asserted for the aggregated dataset.",
        "processing": "Direct transcription of legal requirements; split ranges into bounds. Preserved original units and country, network category, conditions and footnote applicability. No methane minimum was inferred.",
        "runtime_policy": "Reference-only. Not linked to parameter registry, runtime defaults, upgrading performance or product-price qualification.",
        "limitations": ["The Dutch G-gas table is not an operator acceptance for the project connection.", "No single minimum methane fraction is stated in Annex 1 Part B.", "Pressure, standard-volume convention, exact injection point, exceptions and off-taker acceptance must be confirmed for the intended project.", "The conditional CO2 equation is registered but is blocked from runtime use until required typed inputs and exception applicability are resolved.", "Historical comparison records from 2009 and Danish 2020 remain intact and must not be merged with the 2026 Dutch requirements."],
        "fair_metadata": {"findable": "Stable local URN, source ID, official gazette identifier and HTTPS URL.", "accessible": "Machine-readable CSV and JSON sidecar; source accessible via HTTPS.", "interoperable": "Country, specification year, statutory network category, values, units, exact legal locations and status are explicit.", "reusable": "Source history preserved; conditionality, unresolved project inputs, runtime exclusion and rights limitations are stated."},
    }
    (PACKAGE / "biomethane_specifications.csv.source.json").write_text(json.dumps(sidecar, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"rows_total": len(all_specs), "rows_added": max(0, len(all_specs) - 23), "equation_rows_added": equation_rows_added, "source_added": source_added, "source_id": SOURCE_ID, "runtime_activation": False}, indent=2))


if __name__ == "__main__":
    main()
