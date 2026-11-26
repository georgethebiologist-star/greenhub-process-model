"""Transcribe reported storage-time tables for Jinmu grain grass silage.

This cultivated forage is a mechanism comparator, not Dutch roadside feed.
The package is reference-only and must not activate roadside storage kinetics.
"""
from __future__ import annotations

import csv
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "Greenhub" / "data"
FOLDER = DATA / "storage"
AUDIT = DATA / "global_audit_package"
FILENAME = "jinmu_grain_grass_silage_storage_time_tang_2025_reference.csv"
CSV_PATH = FOLDER / FILENAME
SIDECAR_PATH = CSV_PATH.with_suffix(".source.json")
SOURCE_ID = "SRC-TANG-JINMU-GRASS-ENSILING-2025"
DOI = "10.3390/microorganisms13091973"
URL = "https://pmc.ncbi.nlm.nih.gov/articles/PMC12471645/"
DOI_URL = f"https://doi.org/{DOI}"
RETRIEVED = "2026-11-08"
TIMES = (0, 3, 7, 15, 30, 60)
FIELDS = [
    "record_id", "source_id", "phase_relevance", "source_table", "species_or_blend",
    "material", "storage_days", "storage_temperature_C", "storage_condition", "metric",
    "statistic", "value", "unit", "basis", "SEM", "p_value_over_time",
    "significance_group", "replicate_count", "source_location", "method_summary",
    "evidence_class", "quality_class", "activation_state", "transferability", "limitations",
]

SOURCE = {
    "source_id": SOURCE_ID,
    "source_title": "Effect of Storage Time on the Fermentation Quality, Bacterial Community Structure, and Metabolic Profiles of Jinmu Grain Grass Silage",
    "authors": "Yaqin Tang; Qianqian Wang; Qiuyan Li; Yasong Wang; Lei Gong; Wenju Zhang; Junli Niu",
    "year": "2025",
    "source_type": "peer-reviewed primary experimental article; open access",
    "doi_or_stable_identifier": DOI,
    "stable_url": URL,
    "material": "Jinmu grain grass (Pennisetum genus) silage from the Eighth Regiment, First Division, Xinjiang Production and Construction Corps, China",
    "quality_notes": (
        "Tables 1 and 2 report storage-time means and SEM. Five vacuum bags were sampled per storage time. "
        "Table 1 does not state units/bases for its numeric composition values in the table headings or note; they are retained with basis unknown, not inferred. "
        "The experimental crop, geography, storage bags and climate are not GreenHub roadside-feed conditions."
    ),
    "accessed_date": RETRIEVED,
}


def _write_csv(path: Path, fields: list[str], rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def _read_csv(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    with path.open(encoding="utf-8-sig", newline="") as stream:
        reader = csv.DictReader(stream)
        return list(reader.fieldnames or []), list(reader)


def _upsert(path: Path, key: str, entries: list[dict[str, str]]) -> None:
    fields, rows = _read_csv(path)
    if not fields:
        fields = list(entries[0])
    key_columns = key.split("|")
    identity = lambda row: tuple(row.get(column, "") for column in key_columns)
    index = {identity(row): row for row in rows}
    for entry in entries:
        item_key = identity(entry)
        if item_key in index:
            index[item_key].update(entry)
        else:
            rows.append(entry)
            index[item_key] = rows[-1]
    _write_csv(path, fields, rows)


def _row(
    table: str, metric: str, day: int, value: str, *, unit: str, basis: str,
    sem: str, p_value: str, group: str = "", source_location: str,
) -> dict[str, str]:
    limitations = (
        "Not roadside/VARTA/GreenHub biomass. Do not treat concentration or fermentation changes as retained mass, "
        "storage loss, gas emissions, or a transferable kinetic parameter."
    )
    if table == "Table 1" and metric != "relative_feeding_value":
        limitations += " Table 1 omits the unit and analytical basis; no conventional forage unit or dry-matter basis was inferred."
    if value == "ND":
        limitations += " Source reports not detected (ND); this is censored/non-detect text, not zero."
    return {
        "record_id": f"TANG25-{table[-1]}-{metric.upper()}-{day:03d}D",
        "source_id": SOURCE_ID,
        "phase_relevance": "2;5",
        "source_table": table,
        "species_or_blend": "Jinmu grain grass (Pennisetum genus)",
        "material": "vacuum-bag ensiled forage",
        "storage_days": str(day),
        "storage_temperature_C": "",
        "storage_condition": "Chopped to 1–2 cm; mixed; vacuum bag 30 × 50 cm; stored in a shaded, light-proof area; no additive is reported in the described preparation.",
        "metric": metric,
        "statistic": "reported mean",
        "value": value,
        "unit": unit,
        "basis": basis,
        "SEM": sem,
        "p_value_over_time": p_value,
        "significance_group": group,
        "replicate_count": "5 bags per storage time",
        "source_location": source_location,
        "method_summary": "Samples were taken by opening five vacuum bags per storage time; silage extract was prepared by soaking 20 g in 180 mL distilled water at 4 °C for 24 h. Nutrient assays followed cited Chinese standards; organic acids were analyzed by HPLC.",
        "evidence_class": "B_measured",
        "quality_class": "B",
        "activation_state": "reference_only",
        "transferability": "Cultivated Pennisetum forage in Xinjiang, China; useful only as a fermentation/storage comparator, not a Dutch roadside-grass parameter source.",
        "limitations": limitations,
    }


def build_rows() -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    table1 = [
        ("dry_matter_content", ["18.47", "18.64", "19.50", "19.35", "17.82", "17.07"], "1.351", "0.244", ["", "", "", "", "", ""]),
        ("ether_extract", ["10.45", "11.05", "10.74", "10.69", "10.54", "10.54"], "1.326", "0.750", ["", "", "", "", "", ""]),
        ("crude_protein", ["11.62", "10.32", "10.11", "7.93", "9.49", "9.31"], "0.954", "0.679", ["", "", "", "", "", ""]),
        ("neutral_detergent_fiber", ["75.04", "75.17", "75.06", "74.64", "74.04", "73.55"], "5.761", "0.297", ["", "", "", "", "", ""]),
        ("acid_detergent_fiber", ["42.78", "42.70", "42.36", "41.88", "41.01", "40.77"], "1.791", "0.294", ["", "", "", "", "", ""]),
        ("relative_feeding_value", ["68.89", "68.85", "69.28", "70.14", "71.56", "72.27"], "2.170", "0.048", ["b", "b", "b", "b", "a", "a"]),
    ]
    table2 = [
        ("pH", ["6.16", "5.47", "5.06", "4.51", "4.33", "4.01"], "pH", "as measured; aqueous silage extract", "0.093", "<0.001", ["a", "b", "bc", "cd", "de", "e"]),
        ("ammonia_nitrogen_to_total_nitrogen", ["0.93", "3.07", "3.42", "3.89", "4.32", "5.08"], "%", "NH3-N as a percentage of total nitrogen; source table basis", "1.033", "<0.001", ["e", "d", "c", "bc", "b", "a"]),
        ("lactic_acid", ["0.54", "1.07", "1.77", "2.94", "5.37", "6.57"], "% DM", "dry-matter basis", "0.915", "<0.001", ["d", "de", "d", "c", "b", "a"]),
        ("acetic_acid", ["0.29", "0.84", "1.07", "1.12", "2.08", "2.77"], "% DM", "dry-matter basis", "0.487", "0.017", ["d", "cd", "c", "c", "b", "a"]),
        ("propionic_acid", ["ND", "0.04", "0.05", "0.06", "0.07", "0.08"], "% DM", "dry-matter basis", "0.006", "0.001", ["", "b", "b", "b", "ab", "a"]),
        ("butyric_acid", ["ND", "ND", "ND", "ND", "ND", "ND"], "% DM", "dry-matter basis", "-", "-", ["", "", "", "", "", ""]),
    ]
    for metric, values, sem, p_value, groups in table1:
        for day, value, group in zip(TIMES, values, groups):
            rows.append(_row(
                "Table 1", metric, day, value,
                unit="unit not stated in source table" if metric != "relative_feeding_value" else "index; source formula",
                basis="not stated in source table" if metric != "relative_feeding_value" else "source-defined calculated index; formula uses NDF and ADF",
                sem=sem, p_value=p_value, group=group,
                source_location="Article Table 1; nutritional composition table and note",
            ))
    for metric, values, unit, basis, sem, p_value, groups in table2:
        for day, value, group in zip(TIMES, values, groups):
            rows.append(_row(
                "Table 2", metric, day, value, unit=unit, basis=basis,
                sem=sem, p_value=p_value, group=group,
                source_location="Article Table 2; fermentation-quality table and note",
            ))
    return rows


def _register(rows: list[dict[str, str]]) -> None:
    _upsert(FOLDER / "source_register.csv", "source_id", [SOURCE])
    _upsert(FOLDER / "dataset_manifest.csv", "filename", [{
        "filename": FILENAME,
        "description": "Reported 0–60-day nutritional and fermentation observations for cultivated Jinmu grain grass silage; reference-only comparator, not roadside-feed kinetics.",
        "row_count": str(len(rows)),
        "schema_version": "1.0",
        "encoding": "UTF-8",
        "delimiter": ",",
        "integration_status": "traceable_reference_only_not_runtime_eligible",
        "primary_key": "record_id",
    }])
    rel = f"storage/{FILENAME}"
    _upsert(AUDIT / "global_source_register.csv", "dataset_path|source_id", [{
        "dataset_path": rel, "dataset_group": "storage", "source_id": SOURCE_ID,
        "source_title": SOURCE["source_title"], "authors": SOURCE["authors"], "year": SOURCE["year"],
        "doi_or_stable_id": DOI, "url": URL, "source_type": SOURCE["source_type"],
        "notes": SOURCE["quality_notes"],
    }])
    numeric_rows = sum(_is_number(row["value"]) for row in rows)
    _upsert(AUDIT / "global_dataset_manifest.csv", "dataset_path", [{
        "dataset_path": rel, "category": "storage", "subgroup": "forage silage time-series comparator; Phases 2 and 5",
        "filename": FILENAME, "row_count_observed": str(len(rows)), "header_count": str(len(FIELDS)),
        "headers": "; ".join(FIELDS), "standardized_status_values": "B;reference_only",
        "detected_readiness": "D3",
        "notes": "Article Tables 1–2; Table 1 does not state units/bases for five composition measures; experimental feed and setting are not roadside grass.",
    }])
    _upsert(AUDIT / "global_dataset_readiness.csv", "dataset_path", [{
        "dataset_path": rel, "category": "storage", "subgroup": "forage silage time-series comparator; Phases 2 and 5",
        "readiness": "D3", "duplicate_ids": "0", "duplicate_rows": "0",
        "numeric_rows": str(numeric_rows), "unsourced_numeric_rows": "0",
        "numeric_rows_missing_exact_location": "0", "unit_conflicts": "0", "basis_conflicts": "0",
        "cross_reference_issues": "0", "equation_missing_inputs": "0", "equation_symbol_mismatches": "0",
        "notes": "Exact Table 1/2 citation locations recorded. Table 1 unknown units/bases retained explicitly; ND is not zero; no runtime linkage.",
    }])
    checksums = [{
        "dataset_path": f"storage/{path.name}",
        "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        "byte_size": str(path.stat().st_size),
    } for path in (CSV_PATH, SIDECAR_PATH)]
    _upsert(AUDIT / "source_dataset_checksums.csv", "dataset_path", checksums)
    summary_path = AUDIT / "global_validation_summary.json"
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    _, manifests = _read_csv(AUDIT / "global_dataset_manifest.csv")
    _, readiness = _read_csv(AUDIT / "global_dataset_readiness.csv")
    summary["dataset_count"] = len(manifests)
    counts: dict[str, int] = {}
    for item in readiness:
        counts[item.get("readiness", "")] = counts.get(item.get("readiness", ""), 0) + 1
    summary["readiness_counts"] = counts
    summary["generated_at"] = datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")
    summary_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _is_number(value: str) -> bool:
    try:
        float(value)
        return True
    except (TypeError, ValueError):
        return False


def main() -> None:
    rows = build_rows()
    if len(rows) != 72 or len({row["record_id"] for row in rows}) != len(rows):
        raise ValueError("Expected 72 unique source-table records")
    _write_csv(CSV_PATH, FIELDS, rows)
    digest = hashlib.sha256(CSV_PATH.read_bytes()).hexdigest()
    sidecar = {
        "dataset_id": "urn:greenhub:dataset:storage:jinmu-grass-silage-tang-2025:v1",
        "persistent_identifier_status": "Repository-local identifier for this transcription; DOI identifies the article, not this derived table extract.",
        "dataset_version": "1.0.0",
        "title": "Jinmu grain grass silage storage-time composition and fermentation observations",
        "source_ids": [SOURCE_ID],
        "citation": "Tang, Y. et al. (2025). Effect of Storage Time on the Fermentation Quality, Bacterial Community Structure, and Metabolic Profiles of Jinmu Grain Grass Silage. Microorganisms, 13(9), 1973. https://doi.org/10.3390/microorganisms13091973",
        "doi": DOI,
        "source_url": URL,
        "retrieval_date": RETRIEVED,
        "source_locations": ["Table 1 (nutritional composition)", "Table 2 (fermentation quality)", "Sections 2.1–2.3 (sample preparation and assays)"],
        "reference_year": 2025,
        "experiment_year": None,
        "geography": "Eighth Regiment, First Division, Xinjiang Production and Construction Corps, China",
        "material_scope": "Jinmu grain grass, a Pennisetum genus forage; cultivated, chopped, mixed and vacuum-bag ensiled; not roadside grass.",
        "experimental_conditions": "Grass chopped to 1–2 cm, mixed, placed into 30 × 50 cm vacuum bags, and stored shaded/light-proof. Five bags were opened at each of 0, 3, 7, 15, 30 and 60 days. Storage temperature is not reported.",
        "license": "Creative Commons Attribution 4.0 International (CC BY 4.0), stated on the article page.",
        "evidence_class": "B_measured",
        "quality_class": "B",
        "activation_state": "reference_only",
        "calculation_connected": False,
        "row_count": len(rows),
        "sha256_csv": digest,
        "transcription_policy": "Tables 1 and 2 means, SEM, p-values and significance letters are transcribed without conversion. Non-detects remain ND. Table 1 units and bases are not supplied in its table and are not inferred.",
        "fair_metadata": {
            "findable": "Local URN, title, authors, publication year, DOI, source URL and exact tables are indexed.",
            "accessible": "UTF-8 CSV and JSON sidecar are stored in the repository; the article is open access.",
            "interoperable": "Long-form records expose storage time, metric, value, unit, basis, statistic, significance group and source location.",
            "reusable": "CC BY 4.0, methods, replicate design, unknown table units, non-detect handling, scope and transferability are recorded.",
        },
        "limitations": [
            "This is cultivated Jinmu/Pennisetum forage from Xinjiang, China, not Dutch roadside grass or GreenHub feed.",
            "Storage temperature and source experiment year are not stated; no temperature-dependent effect is inferred.",
            "Table 1 omits units/bases for the reported composition values; those values are preserved but are not canonical input candidates.",
            "The table reports means and SEM, not replicate-level measurements; five bags were sampled at each time point.",
            "Concentration/fermentation changes are not mass retention, fresh-matter loss, leachate, or emissions measurements.",
            "No kinetic rates were fit; the extract is reference-only and not mapped to a GreenHub runtime parameter.",
        ],
    }
    SIDECAR_PATH.write_text(json.dumps(sidecar, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    _register(rows)
    print(json.dumps({"file": str(CSV_PATH), "rows": len(rows), "sha256": digest}, indent=2))


if __name__ == "__main__":
    main()
