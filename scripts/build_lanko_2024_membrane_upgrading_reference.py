"""Build a traceable Phase 6 reference extract for the Buivydas et al. study."""
from __future__ import annotations

import csv
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "Greenhub" / "data"
FOLDER = DATA / "Bigas production + upgrade" / "Membrane"
AUDIT = DATA / "global_audit_package"
FILENAME = "variable_methane_feed_membrane_upgrading_energy_slip_buivydas_2024_reference.csv"
CSV_PATH = FOLDER / FILENAME
SIDECAR_PATH = CSV_PATH.with_suffix(CSV_PATH.suffix + ".source.json")
SOURCE_ID = "BUIVYDAS-MEMBRANE-UPGRADING-2024"
DOI = "10.3390/su16083323"
URL = "https://www.mdpi.com/2071-1050/16/8/3323"
PDF_URL = "https://gs.elaba.lt/object/elaba%3A193725890/193725890.pdf"
RETRIEVED = "2026-11-08"

FIELDS = [
    "record_id", "source_id", "phase", "experiment_id", "record_type", "metric",
    "reported_value", "numeric_value", "reported_deviation", "deviation_statistic",
    "unit", "basis_or_denominator", "stream", "inlet_methane_vol_percent",
    "blended_inlet_flow_Nm3_h", "upgrading_system", "source_table", "source_location",
    "evidence_class", "quality_class", "activation_state", "transferability",
    "uncertainty_or_limit", "notes",
]

TITLE = (
    "A Life Cycle Assessment of Methane Slip in Biogas Upgrading Based on Permeable "
    "Membrane Technology with Variable Methane Concentration in Raw Biogas"
)
AUTHORS = "E. Buivydas; K. Navickas; K. Venslauskas"
SYSTEM = (
    "Three-stage permeable hollow-fibre membrane upgrader; 16 bar compression; "
    "upgraded-gas recycle used to prepare inlet methane concentrations; cooling and filtration"
)
TRANSFER = (
    "Lithuanian membrane-upgrader comparator at 35 Nm3/h blended inlet flow; not a "
    "GreenHub-specific calibration or universal membrane performance curve."
)
LIMITS = (
    "The source varies inlet methane by blending plant biogas with upgraded-gas recycle; "
    "35 Nm3/h is the blended upgrader inlet, not demonstrated net raw-digester-gas throughput. "
    "The table's 'deviation' statistic is not identified in the table and is not relabeled SD or SE. "
    "Table 2 labels methane slip as % vol, while the methods describe a controlled limit of "
    "0.5% of total inlet methane; preserve both statements and do not treat it as an unconstrained "
    "slip response. Normal-volume reference conditions are not specified in the tables. "
    "Reference-only: no runtime parameter, default, equation, TEA/LCA factor, or Pareto case is changed."
)

CASES = [
    {"id": "CM-50", "ch4": (50.0, 0.1), "flow": (35.0, 0.15), "power": (10.28, 0.04),
     "product_flow": (18.05, 0.1), "product_ch4": (96.46, 0.36), "slip": (0.5, 0.03)},
    {"id": "CM-60", "ch4": (60.0, 0.2), "flow": (35.0, 0.12), "power": (10.21, 0.04),
     "product_flow": (21.67, 0.2), "product_ch4": (96.43, 0.41), "slip": (0.5, 0.01)},
    {"id": "CM-70", "ch4": (70.0, 0.2), "flow": (35.0, 0.18), "power": (10.11, 0.02),
     "product_flow": (25.26, 0.1), "product_ch4": (96.52, 0.39), "slip": (0.5, 0.02)},
    {"id": "CM-80", "ch4": (80.0, 0.1), "flow": (35.0, 0.14), "power": (9.99, 0.03),
     "product_flow": (28.79, 0.1), "product_ch4": (96.77, 0.42), "slip": (0.5, 0.01)},
]

MEASUREMENTS = [
    ("ch4", "inlet_methane_content", "upgrader_inlet_biogas_methane_vol_percent", "% vol", "blended upgrader inlet gas", "Table 1"),
    ("flow", "blended_inlet_flow", "upgrader_inlet_biogas_flow", "Nm3/h (as reported)", "blended upgrader inlet gas", "Table 1"),
    ("power", "electricity_consumption_rate", "upgrading_electricity_consumption_rate", "kWh/h (as reported)", "membrane upgrading unit", "Table 1"),
    ("product_flow", "biomethane_product_flow", "biomethane_product_flow", "Nm3/h (as reported)", "upgraded product gas", "Table 2"),
    ("product_ch4", "biomethane_methane_content", "biomethane_methane_vol_percent", "% vol", "upgraded product gas", "Table 2"),
    ("slip", "methane_slip", "methane_slip", "% vol (as table-labelled)", "off-gas / methane-slip control", "Table 2"),
]


def build_rows() -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for case in CASES:
        for case_key, metric_key, metric, unit, stream, table in MEASUREMENTS:
            mean, deviation = case[case_key]
            slip_basis = (
                "Table 2 reports % vol; Methods 2.4 state the controlled limit was 0.5% of total "
                "methane in biogas. Denominator/definition is retained as ambiguous, not normalized."
                if metric_key == "methane_slip" else
                "Source-reported arithmetic mean; flow basis is the reported upgrader stream."
            )
            rows.append({
                "record_id": f"BUIVYDAS24-{case['id']}-{metric_key.upper()}",
                "source_id": SOURCE_ID,
                "phase": "6",
                "experiment_id": case["id"],
                "record_type": "measured_mean_with_reported_deviation",
                "metric": metric,
                "reported_value": f"{mean:g}",
                "numeric_value": f"{mean:g}",
                "reported_deviation": f"{deviation:g}",
                "deviation_statistic": "Source labels this as deviation; SD/SE or other statistic not specified in the table.",
                "unit": unit,
                "basis_or_denominator": slip_basis,
                "stream": stream,
                "inlet_methane_vol_percent": f"{case['ch4'][0]:g}",
                "blended_inlet_flow_Nm3_h": f"{case['flow'][0]:g}",
                "upgrading_system": SYSTEM,
                "source_table": table,
                "source_location": f"{table}; experimental results, section 3.1" if table == "Table 1" else f"{table}; experimental results, section 3.1 and methane-slip control description in section 2.4",
                "evidence_class": "B_measured_literature",
                "quality_class": "B",
                "activation_state": "reference_only",
                "transferability": TRANSFER,
                "uncertainty_or_limit": LIMITS,
                "notes": (
                    "The inlet methane setting was prepared by blending plant biogas with upgraded-gas recycle; "
                    "do not interpret as four independent raw-biogas compositions."
                    if metric_key == "inlet_methane_content" else
                    "Deviation retained verbatim in magnitude; uncertainty statistic is not inferred."
                ),
            })
    return rows


def _read_csv(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    with path.open(encoding="utf-8-sig", newline="") as stream:
        reader = csv.DictReader(stream)
        return list(reader.fieldnames or []), list(reader)


def _upsert(path: Path, key: str, entries: list[dict[str, str]]) -> None:
    fields, rows = _read_csv(path)
    keys = key.split("|")
    index = {tuple(row.get(field, "") for field in keys): row for row in rows}
    for entry in entries:
        identity = tuple(entry.get(field, "") for field in keys)
        if identity in index:
            index[identity].update(entry)
        else:
            rows.append(entry)
            index[identity] = rows[-1]
    with path.open("w", encoding="utf-8-sig", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields or list(entries[0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def _register(rows: list[dict[str, str]]) -> None:
    _upsert(FOLDER / "source_register.csv", "source_id", [{
        "source_id": SOURCE_ID, "source_title": TITLE, "authors": AUTHORS, "year": "2024",
        "source_type": "peer-reviewed open-access article; measured membrane-upgrader campaign and LCA",
        "doi_or_stable_identifier": DOI, "source_url": URL, "accessed_date": RETRIEVED,
        "notes": "Tables 1–2 are measured at a 35 Nm3/h blended upgrader inlet across four methane settings. Methane slip is actively controlled; not a generic slip response. CC BY 4.0.",
    }])
    _upsert(FOLDER / "dataset_manifest.csv", "filename", [{
        "filename": FILENAME, "relative_path": f"Greenhub/data/Bigas production + upgrade/Membrane/{FILENAME}",
        "description": "Measured inlet/outlet gas flow, methane content, upgrader electricity rate and reported methane-slip values for four 35 Nm3/h blended inlet cases; 24 rows, plus source deviations.",
        "row_count": str(len(rows)), "encoding": "UTF-8", "delimiter": ",",
        "integration_status": "reference_only_measured_campaign_controlled_slip_and_recycle_boundary",
    }])

    rel = f"Bigas production + upgrade/Membrane/{FILENAME}"
    _upsert(AUDIT / "global_source_register.csv", "dataset_path|source_id", [{
        "dataset_path": rel, "dataset_group": "Bigas production + upgrade", "source_id": SOURCE_ID,
        "source_title": TITLE, "authors": AUTHORS, "year": "2024", "doi_or_stable_id": DOI,
        "url": URL, "source_type": "peer-reviewed primary measured membrane-upgrader campaign",
        "notes": LIMITS,
    }])
    _upsert(AUDIT / "global_dataset_manifest.csv", "dataset_path", [{
        "dataset_path": rel, "category": "Bigas production + upgrade", "subgroup": "membrane upgrading measured input/output campaign; Phase 6",
        "filename": FILENAME, "row_count_observed": str(len(rows)), "header_count": str(len(FIELDS)),
        "headers": "; ".join(FIELDS), "standardized_status_values": "B;reference_only",
        "detected_readiness": "D3",
        "notes": "Four measured cases use 35 Nm3/h blended upgrader feed with recycle. Slip is controlled at 0.5% of inlet methane per methods; not a free-running response curve.",
    }])
    _upsert(AUDIT / "global_dataset_readiness.csv", "dataset_path", [{
        "dataset_path": rel, "category": "Bigas production + upgrade", "subgroup": "membrane upgrading measured input/output campaign; Phase 6",
        "readiness": "D3", "duplicate_ids": "0", "duplicate_rows": "0", "numeric_rows": str(len(rows)),
        "unsourced_numeric_rows": "0", "numeric_rows_missing_exact_location": "0", "unit_conflicts": "0",
        "basis_conflicts": "1", "cross_reference_issues": "0", "equation_missing_inputs": "0",
        "equation_symbol_mismatches": "0",
        "notes": "All numerical records are Table 1–2 measured means with source-reported deviations; deviation type is not stated. Methane-slip table basis is ambiguous against the controlled-slip method statement. Reference-only.",
    }])
    checksum_rows = [{
        "dataset_path": f"Bigas production + upgrade/Membrane/{path.name}",
        "sha256": hashlib.sha256(path.read_bytes()).hexdigest(), "byte_size": str(path.stat().st_size),
    } for path in (CSV_PATH, SIDECAR_PATH)]
    _upsert(AUDIT / "source_dataset_checksums.csv", "dataset_path", checksum_rows)

    summary_path = AUDIT / "global_validation_summary.json"
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    _, manifests = _read_csv(AUDIT / "global_dataset_manifest.csv")
    _, readiness = _read_csv(AUDIT / "global_dataset_readiness.csv")
    counts: dict[str, int] = {}
    for item in readiness:
        label = item.get("readiness", "")
        counts[label] = counts.get(label, 0) + 1
    summary["dataset_count"] = len(manifests)
    summary["readiness_counts"] = counts
    summary["generated_at"] = datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")
    summary_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main() -> None:
    rows = build_rows()
    if len(rows) != 24 or len({row["record_id"] for row in rows}) != len(rows):
        raise ValueError("Expected 24 unique measured records (six metrics in four cases).")
    FOLDER.mkdir(parents=True, exist_ok=True)
    with CSV_PATH.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=FIELDS, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
    digest = hashlib.sha256(CSV_PATH.read_bytes()).hexdigest()
    sidecar = {
        "dataset_id": "urn:greenhub:dataset:membrane:buivydas-variable-methane-feed-upgrading-2024:v1",
        "persistent_identifier_status": "Repository-local URN identifies this derivative extract; DOI identifies the article, not this extract.",
        "dataset_version": "1.0.0", "title": "Measured membrane-upgrading response at four blended inlet methane settings",
        "source_file": FILENAME, "source_id": SOURCE_ID,
        "citation": "Buivydas, E., Navickas, K., & Venslauskas, K. (2024). A Life Cycle Assessment of Methane Slip in Biogas Upgrading Based on Permeable Membrane Technology with Variable Methane Concentration in Raw Biogas. Sustainability, 16(8), 3323. https://doi.org/10.3390/su16083323",
        "doi": DOI, "source_url": URL, "full_text_access_url": PDF_URL,
        "retrieval_date": RETRIEVED, "reference_year": 2024,
        "geography": "Lithuania; location of the biogas-upgrading demonstration described by the article.",
        "license": "Creative Commons Attribution 4.0 International (CC BY 4.0), stated in the article.",
        "license_url": "https://creativecommons.org/licenses/by/4.0/",
        "evidence_class": "B_measured_literature", "quality_class": "B",
        "activation_state": "reference_only", "calculation_connected": False,
        "row_count": len(rows), "sha256_csv": digest,
        "experimental_design": "Four measured upgrader cases (CM-50, CM-60, CM-70, CM-80) at nominally 35 Nm3/h blended inlet flow; Table 1 reports inlet composition/flow/electricity consumption and Table 2 reports biomethane flow/purity and methane slip. The system is a three-stage permeable hollow-fibre membrane train with 16 bar compression. Upgraded gas was recycled to prepare elevated inlet methane fractions.",
        "transcription_policy": "Table 1–2 means and their reported deviations are transcribed. The paper does not identify whether the deviations are SD, SE or another statistic in the tables; no label is inferred. Units and gas-flow reference conditions are retained as source-reported.",
        "derived_values": "No derived recovery or methane balance is supplied. If specific energy is later calculated, use the reported power-rate means divided by the matching measured flow means; propagate uncertainty separately and respect the blended/recycle boundary.",
        "known_source_ambiguities": [
            "Table 2 labels methane slip as % vol, while section 2.4 describes a controlled 0.5% limit relative to total methane in the inlet biogas. The extract preserves the table value and flags denominator ambiguity; it is not a free-running slip-performance response.",
            "The 35 Nm3/h feed is a blended upgrader inlet including upgraded-gas recycle used to set the four methane concentrations; it is not net raw biogas production from the digester.",
            "The tables do not identify the statistic represented by each reported deviation or the reference temperature/pressure for Nm3.",
            "The article's specific LCA scores use its own functional unit, system boundary, energy mix, and CML baseline; they are not imported as GreenHub impact factors.",
        ],
        "limitations": [
            "A single three-stage membrane upgrading system and fixed blended inlet flow do not establish a general scale-up curve or a GreenHub plant-specific energy factor.",
            "The reported methane-slip value is under active control and should not be used to calibrate uncontrolled membrane slip.",
            "The input gas is blended with recycled product; separate net raw-feed/recycle flow data are not included in the two tables.",
            "No GreenHub runtime parameter, default, equation, route, scenario ID, TEA/LCA factor, or Pareto result is changed.",
        ],
        "fair_metadata": {
            "findable": "Repository-local dataset URN, article DOI, source register, article tables/section locators, and generated FAIR catalog record.",
            "accessible": "UTF-8 CSV and JSON sidecar; article is openly available under CC BY 4.0.",
            "interoperable": "Long-form CSV carries case, measured stream, metric, reported mean/deviation, unit, basis and source-table fields.",
            "reusable": "License, methods, flow/recycle boundary, controlled methane-slip condition, statistical and unit ambiguities, and transfer limits are recorded.",
        },
    }
    SIDECAR_PATH.write_text(json.dumps(sidecar, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    _register(rows)
    print(json.dumps({"file": str(CSV_PATH), "rows": len(rows), "sha256": digest}, indent=2))


if __name__ == "__main__":
    main()
