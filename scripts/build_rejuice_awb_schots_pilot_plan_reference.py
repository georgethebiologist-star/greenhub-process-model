"""Stage a ReJuice roadside-grass-juice pilot plan as a data-acquisition lead.

The source describes planned scale and monitoring, not pilot performance data.
Values therefore remain project-plan context and are never runtime inputs.
"""
from __future__ import annotations

import csv
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "Greenhub" / "data"
GROUP = DATA / "Pre-treatment" / "Feedstock"
AUDIT = DATA / "global_audit_package"
FILENAME = "rejuice_awb_schots_grass_juice_ad_pilot_plan_2026_reference.csv"
CSV_PATH = GROUP / FILENAME
SIDECAR_PATH = Path(str(CSV_PATH) + ".source.json")
SOURCE_ID = "SRC-REJUICE-AWB-SCHOTS-PILOT-PLAN-2026"
URL = "https://interregvlaned.eu/nieuws/pilootreactor-biogas-bij-awb-schots"
NEWS_URL = "https://interregvlaned.eu/rejuice/nieuws-events"
RETRIEVED = "2026-11-08"
FIELDS = [
    "record_id", "source_id", "publication_date", "phase_relevance", "record_type",
    "reported_item", "value", "unit", "basis_or_status", "source_location",
    "evidence_class", "quality_class", "activation_state", "limitations", "retrieval_date",
]

LIMITATION = (
    "This is a project pilot-plan statement, not a measured operating result. The article does not provide actual commissioning status, "
    "date-resolved feed mass, grass source/composition, solids/flow basis, reactor loading, HRT, gas composition or measured yield, "
    "energy, water, reagent use, or digestate analyses. Do not use design/expected quantities as GreenHub feed availability, capacity, "
    "or process parameters. Request the pilot logs and lab records from project partners."
)

SOURCE_WORDING = [
    ("RJ-AWB-SCHOTS-REACTOR-VOLUME", "3;5", "planned_pilot_equipment_volume", "CSTR reactor volume", "2.5", "m3", "Pilot installation planned at A.W.B. Schots in February 2026; source does not establish actual commissioning."),
    ("RJ-AWB-SCHOTS-JUICE-THROUGHPUT", "1;3;5", "expected_annual_throughput", "Expected annual production of grass juice", "3000–9000", "t/year", "Expected project value; mass basis, production days, feed sites, press feed mass and measured operating history are absent."),
    ("RJ-AWB-SCHOTS-SEDIMENT", "3;5", "feed_material_description", "Small amount of sediment expected to accompany grass juice", "", "qualitative", "Sediment mass, composition, particle-size distribution and sampling protocol are not stated."),
    ("RJ-AWB-SCHOTS-LAB-TESTS", "5", "prior_test_program_description", "Continuous lab-scale grass-juice tests and CSTR/UASB comparison reported as completed", "", "qualitative", "The public project article reports the tests but gives no operating conditions or performance data."),
    ("RJ-AWB-SCHOTS-MONITOR-GAS", "5", "planned_monitoring", "Methane potential and biogas yield to be continuously monitored and evaluated", "", "qualitative", "Sensors, calibration, measurement basis, gas standard conditions, data availability and achieved values are not published."),
    ("RJ-AWB-SCHOTS-MONITOR-DIGESTATE", "7", "planned_monitoring", "Produced digestate characteristics to be investigated", "", "qualitative", "No digestate flow, nutrient speciation, contaminant assays, process conditions or product-quality results are published."),
]


def _read(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    with path.open(encoding="utf-8-sig", newline="") as stream:
        reader = csv.DictReader(stream)
        return list(reader.fieldnames or []), list(reader)


def _write(path: Path, fields: list[str], rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def _upsert(path: Path, key: str, entries: list[dict[str, object]]) -> None:
    fields, rows = _read(path)
    if not fields:
        fields = list(entries[0])
    keys = key.split("|")
    identity = lambda row: tuple(row.get(column, "") for column in keys)
    index = {identity(row): row for row in rows}
    for entry in entries:
        normalized = {field: str(entry.get(field, "")) for field in fields}
        entry_key = identity(normalized)
        if entry_key in index:
            index[entry_key].update(normalized)
        else:
            rows.append(normalized)
            index[entry_key] = rows[-1]
    _write(path, fields, rows)


def build() -> None:
    rows = [{
        "record_id": f"REJUICE26-{record_suffix}",
        "source_id": SOURCE_ID,
        "publication_date": "2026-02-06",
        "phase_relevance": phases,
        "record_type": record_type,
        "reported_item": item,
        "value": value,
        "unit": unit,
        "basis_or_status": basis,
        "source_location": "Interreg ReJuice article, published 2026-02-06; section 'Opzet en doelstellingen van de pilootinstallatie'.",
        "evidence_class": "first_party_interreg_pilot_plan",
        "quality_class": "not_applicable_project_plan_not_measurement",
        "activation_state": "reference_only",
        "limitations": LIMITATION,
        "retrieval_date": RETRIEVED,
    } for record_suffix, phases, record_type, item, value, unit, basis in SOURCE_WORDING]
    if len({row["record_id"] for row in rows}) != len(rows):
        raise ValueError("Duplicate ReJuice pilot plan record ID")
    _write(CSV_PATH, FIELDS, rows)
    digest = hashlib.sha256(CSV_PATH.read_bytes()).hexdigest()

    sidecar = {
        "dataset_id": "urn:greenhub:dataset:feedstock:rejuice-awb-schots-grass-juice-ad-pilot-plan-2026:v1",
        "dataset_version": "1.0.0",
        "title": "ReJuice AWB Schots grass-juice AD pilot plan and announced monitoring",
        "source_file": FILENAME,
        "source_file_sha256": digest,
        "source_id": SOURCE_ID,
        "citation": "ReJuice / Interreg Vlaanderen-Nederland. (2026-02-06). Pilootreactor biogas bij AWB Schots.",
        "source_url": URL,
        "project_news_url": NEWS_URL,
        "doi": None,
        "publication_date": "2026-02-06",
        "retrieval_date": RETRIEVED,
        "geography": "Belgium; pilot site identified as A.W.B. Schots, but no exact plot/feed catchment is supplied in the article.",
        "record_count": len(rows),
        "process_phases": [1, 3, 5, 7],
        "rights_status": "No explicit dataset reuse license identified; concise factual plan statements are transcribed with attribution. Source pages are linked, not redistributed.",
        "evidence_class": "first-party project plan",
        "quality_class": "not_applicable_project_plan_not_measurement",
        "activation_state": "reference_only",
        "calculation_connected": False,
        "runtime_parameter_mapping": None,
        "data_handling": "The 2.5 m3 value is a planned reactor size, and 3000–9000 t/year is expected grass-juice output, not measured throughput. Monitoring topics are plans, not published observations. The public article states the installation was planned for February 2026; no claim is made here that it was or was not commissioned.",
        "data_collection_lead": {
            "priority": "high",
            "phases": [1, 3, 5, 7],
            "request_from_partners": [
                "commissioning and operation dates; feed source, harvest date, delivered and press-feed mass",
                "grass and juice wet mass, dry matter, VS, soluble COD, composition, sediment mass and sample IDs",
                "press feed/juice/fiber flows and paired composition",
                "CSTR volume and working volume, HRT, OLR, temperature, pH, alkalinity, recirculation, uptime and feed schedule",
                "daily standardized biogas flow and CH4/CO2/H2S, meter calibration, methane yield denominator and uncertainty",
                "digestate flow, TS/VS, total/dissolved N/P/K, ammonium, COD, conductivity, metals and separation partition",
                "utility, water, chemical and operator logs with timestamps"
            ],
            "official_project_news_checked_through": "2026-11-08",
            "follow_up_event": "The official ReJuice news page lists a final event for 2027-02-22; use this as a retrieval lead, not as proof results will be released."
        },
        "limitations": [
            LIMITATION,
            "The expected 3000–9000 t/year quantity is grass juice output, not raw grass supply; it must not be equated to GreenHub's seasonal roadside-feed inventory.",
            "The public page is a project announcement, not a technical report, raw-data repository, or commissioning certificate.",
            "No GreenHub user should infer local route parity from this Belgian pilot without matching feed, press configuration, sediment load, basis, and reactor conditions."
        ],
        "fair_metadata": {
            "findable": "Versioned local URN, source ID, project article and news URLs, publication date, and unique observation-plan records are supplied.",
            "accessible": "UTF-8 CSV and JSON sidecar are indexed in local/global registers and the FAIR catalog.",
            "interoperable": "Rows separate phase, plan/monitoring item, value, unit, basis/status, evidence and limitations.",
            "reusable": "Planned versus measured status is explicit, with a prioritized request list for future primary observations."
        }
    }
    SIDECAR_PATH.write_text(json.dumps(sidecar, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    source = {
        "source_id": SOURCE_ID,
        "source_title": "Pilootreactor biogas bij AWB Schots",
        "authors": "ReJuice / Interreg Vlaanderen-Nederland",
        "year": "2026",
        "source_type": "first-party Interreg pilot-plan announcement",
        "doi_or_stable_identifier": "",
        "stable_url": URL,
        "material": "Grass juice from locally pressed grass; Belgian pilot CSTR and digestate monitoring plan",
        "quality_notes": "Planned equipment, expected throughput and planned monitoring only; no measured pilot performance is published in this article. Use as a data-acquisition lead, not a GreenHub process parameter.",
        "accessed_date": RETRIEVED,
    }
    _upsert(GROUP / "source_register.csv", "source_id", [source])
    _upsert(GROUP / "dataset_manifest.csv", "file_name", [{
        "file_name": FILENAME,
        "description": "Six first-party ReJuice pilot-plan and monitoring records for grass-juice AD and digestate; no performance measurements.",
        "row_count": len(rows),
        "schema_version": "1.0",
        "encoding": "UTF-8",
        "delimiter": ",",
        "integration_readiness": "traceable_data_acquisition_lead_reference_only_not_runtime_eligible",
        "limitations": "Pilot commissioning and actual operation are not verified; 3000–9000 t/year is an expected juice flow, not measured grass supply.",
    }])
    rel = f"Pre-treatment/Feedstock/{FILENAME}"
    _upsert(AUDIT / "global_source_register.csv", "dataset_path|source_id", [{
        "dataset_path": rel,
        "dataset_group": "Pre-treatment/Feedstock",
        "source_id": SOURCE_ID,
        "source_title": source["source_title"],
        "authors": source["authors"],
        "year": "2026",
        "doi_or_stable_id": "",
        "url": f"{URL}; {NEWS_URL}",
        "source_type": source["source_type"],
        "notes": source["quality_notes"],
    }])
    _upsert(AUDIT / "global_dataset_manifest.csv", "dataset_path", [{
        "dataset_path": rel,
        "category": "Pre-treatment",
        "subgroup": "Grass-juice AD pilot plan and data-acquisition lead; Phases 1, 3, 5 and 7",
        "filename": FILENAME,
        "row_count_observed": len(rows),
        "header_count": len(FIELDS),
        "headers": "; ".join(FIELDS),
        "standardized_status_values": "project_plan;reference_only",
        "detected_readiness": "D3",
        "notes": "Planning data only. No measured mass flows, gas yields, utilities or digestate assays; partners are the primary-data source.",
    }])
    _upsert(AUDIT / "global_dataset_readiness.csv", "dataset_path", [{
        "dataset_path": rel,
        "category": "Pre-treatment",
        "subgroup": "Grass-juice AD pilot plan and data-acquisition lead; Phases 1, 3, 5 and 7",
        "readiness": "D3",
        "duplicate_ids": 0,
        "duplicate_rows": 0,
        "numeric_rows": 2,
        "unsourced_numeric_rows": 0,
        "numeric_rows_missing_exact_location": 0,
        "unit_conflicts": 0,
        "basis_conflicts": 0,
        "cross_reference_issues": 0,
        "equation_missing_inputs": 0,
        "equation_symbol_mismatches": 0,
        "notes": "Both numeric records are linked but are a planned reactor volume and expected throughput range, not measurements; no runtime mapping.",
    }])
    checksums = [{
        "dataset_path": f"Pre-treatment/Feedstock/{path.name}",
        "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        "byte_size": path.stat().st_size,
    } for path in (CSV_PATH, SIDECAR_PATH)]
    _upsert(AUDIT / "source_dataset_checksums.csv", "dataset_path", checksums)
    summary_path = AUDIT / "global_validation_summary.json"
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    _, manifests = _read(AUDIT / "global_dataset_manifest.csv")
    _, readiness = _read(AUDIT / "global_dataset_readiness.csv")
    summary["dataset_count"] = len(manifests)
    counts: dict[str, int] = {}
    for item in readiness:
        label = item.get("readiness", "")
        counts[label] = counts.get(label, 0) + 1
    summary["readiness_counts"] = counts
    summary["generated_at"] = datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")
    summary_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"dataset": rel, "rows": len(rows), "sha256": digest, "activation_state": "reference_only"}, indent=2))


if __name__ == "__main__":
    build()
