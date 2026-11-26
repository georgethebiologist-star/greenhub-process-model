"""Stage Greenhub's autumn roadside-grass processing announcement as provenance.

The announced quantity is not a weighbridge measurement and is deliberately
kept outside runtime inputs. It is separate from the later 600 t GKB-own-grass
Bokashi figure in Greenhub's dry-run recap.
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
FILENAME = "greenhub_autumn_roadside_grass_600t_announcement_reference.csv"
CSV_PATH = GROUP / FILENAME
SIDECAR_PATH = Path(str(CSV_PATH) + ".source.json")
SOURCE_ID = "SRC-GHZH-AUTUMN-ROADGRASS-600T-ANNOUNCEMENT-2025"
RETRIEVED = "2026-11-08"
LINKEDIN_URL = "https://nl.linkedin.com/posts/greenhub-zuid-holland_van-bermgras-tot-bouwmateriaal-en-bodemproduct-activity-7389307797911478272-BwKN"
NETWORK_URL = "https://natuurlijkereststromen.nl/aan-de-slag-met-uitvoeringsagenda-greenhub/"
EVENT_URL = "https://greenhub-zuidholland.nl/samen-door-de-bermgrasdeur/"
FIELDS = [
    "record_id", "source_id", "publication_date", "event_date_context",
    "campaign_season_label", "phase", "record_type", "observation",
    "reported_value", "unit", "measurement_basis", "evidence_class",
    "quality_class", "activation_state", "source_urls", "source_location",
    "limitations", "retrieval_date",
]

TITLE = "Greenhub Zuid-Holland announcement of approximately 600 t roadside grass for autumn processing"
SOURCE_NOTES = (
    "First-party project announcement, repeated by the Natuurlijke Reststromen network. The quantity is an approximate "
    "planned seasonal processing statement, not a verified measured delivery. The exact social-post timestamp and mass basis "
    "are not supplied. Keep distinct from the later 600 t GKB-own-grass Bokashi figure."
)


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
    identity = lambda row: tuple(row.get(item, "") for item in keys)
    index = {identity(row): row for row in rows}
    for entry in entries:
        normalized = {field: str(entry.get(field, "")) for field in fields}
        match = identity(normalized)
        if match in index:
            index[match].update(normalized)
        else:
            rows.append(normalized)
            index[match] = rows[-1]
    _write(path, fields, rows)


def build() -> None:
    row = {
        "record_id": "GHZH-AUTUMN-ROADGRASS-600T-ANNOUNCED",
        "source_id": SOURCE_ID,
        "publication_date": "",
        "event_date_context": "2025-11-07",
        "campaign_season_label": "Autumn; 2025 is contextual inference from the dated agenda event, not proof of processing completion",
        "phase": "1;3;4",
        "record_type": "announced_approximate_seasonal_processing_quantity",
        "observation": "Greenhub said it would process approximately 600 t of roadside grass into construction material and soil product that autumn, supplied by two large market parties",
        "reported_value": "600",
        "unit": "t",
        "measurement_basis": "The announcement says tonnes of roadside grass; wet/dry basis, weighing method, date-specific deliveries, source split, moisture and rejected material are not reported.",
        "evidence_class": "first_party_project_announcement_repeated_by_regional_network",
        "quality_class": "not_applicable_announced_plan_not_measurement",
        "activation_state": "reference_only",
        "source_urls": f"{LINKEDIN_URL}; {NETWORK_URL}; {EVENT_URL}",
        "source_location": "Greenhub Zuid-Holland LinkedIn post and Natuurlijke Reststromen article, section 'Aanbod en vraag stimuleren'; the Greenhub event page dates the related 23-organization agenda event to 2025-11-07.",
        "limitations": (
            "Announcement only: no weighbridge tickets, delivery log, date-resolved quantity, composition, or confirmation of completion is public. "
            "The exact LinkedIn publication timestamp is not exposed; 2025-11-07 is event-date context, not asserted as the post publication date. "
            "Do not annualize, combine with other collection claims, or use as an available-supply/runtime input. Greenhub's 2025-11-28 dry-run recap separately reports 600 t of GKB's own grass to Bokashi; that distinct stream is not evidence that this roadside-grass announcement was completed."
        ),
        "retrieval_date": RETRIEVED,
    }
    _write(CSV_PATH, FIELDS, [row])
    digest = hashlib.sha256(CSV_PATH.read_bytes()).hexdigest()
    sidecar = {
        "dataset_id": "urn:greenhub:dataset:feedstock:autumn-roadside-grass-600t-announcement:v1",
        "dataset_version": "1.0.0",
        "title": TITLE,
        "source_file": FILENAME,
        "source_file_sha256": digest,
        "source_id": SOURCE_ID,
        "citation": "Greenhub Zuid-Holland. (social post; exact publication timestamp not exposed). 'Van bermgras tot bouwmateriaal en bodemproduct'. The associated Greenhub agenda event is dated 7 November 2025. Repeated by Vernieuwersnetwerk Natuurlijke Reststromen, 'Aan de slag met Uitvoeringsagenda Greenhub'.",
        "source_urls": [LINKEDIN_URL, NETWORK_URL, EVENT_URL],
        "doi": None,
        "publication_date": None,
        "event_date_context": "2025-11-07",
        "retrieval_date": RETRIEVED,
        "geography": "Greenhub Zuid-Holland, Netherlands; exact source sites and supplier locations not disclosed",
        "record_count": 1,
        "process_phases": [1, 3, 4],
        "rights_status": "No explicit dataset reuse license identified; only a concise factual statement is transcribed with attribution. Source pages are linked, not redistributed.",
        "evidence_class": "first_party_project_announcement_repeated_by_regional_network",
        "quality_class": "not_applicable_announced_plan_not_measurement",
        "activation_state": "reference_only",
        "calculation_connected": False,
        "runtime_parameter_mapping": None,
        "data_handling": "The source says approximately 600 tonnes of roadside grass would be processed that autumn into construction material and soil product, with delivery by two large market parties. It does not provide measured delivered mass or completion evidence. The associated 7 November 2025 agenda-event date provides context for interpreting 'this autumn'; the social post's exact timestamp is unavailable.",
        "limitations": [
            "No weighbridge records, delivery dates, site/supplier split, wet/dry basis, moisture, contamination, composition, reject mass, uncertainty or realized throughput are public.",
            "A later Greenhub dry-run report separately gives 600 t of GKB's own grass for Bokashi; it is a different described material/use and must not be treated as confirmation of the roadside announcement.",
            "The approximate announced quantity is not annual availability, contractually secured supply, installed capacity, or a validated value for the simulation.",
            "Greenhub's official event page confirms the agenda event date, not the 600 t quantity; the quantity is sourced from the first-party Greenhub post and its regional-network reproduction."
        ],
        "fair_metadata": {
            "findable": "Repository-local versioned URN, source ID, three source URLs, and a unique row ID are supplied.",
            "accessible": "UTF-8 CSV and JSON provenance sidecar are indexed in the project's FAIR catalog.",
            "interoperable": "Long-form CSV separates reported quantity, unit, measurement basis, campaign timing, evidence/quality class, phase relevance, and activation state.",
            "reusable": "Source wording scope, date inference, non-measurement status, later same-number/different-stream report, and runtime exclusion are explicit."
        }
    }
    SIDECAR_PATH.write_text(json.dumps(sidecar, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    local_source = {
        "source_id": SOURCE_ID,
        "source_title": TITLE,
        "authors": "Greenhub Zuid-Holland; repeated by Vernieuwersnetwerk Natuurlijke Reststromen",
        "year": "2025",
        "source_type": "first-party project announcement and regional network reproduction",
        "doi_or_stable_identifier": "",
        "stable_url": LINKEDIN_URL,
        "material": "Announced seasonal processing of South Holland roadside grass into construction material and soil product",
        "quality_notes": SOURCE_NOTES,
        "accessed_date": RETRIEVED,
    }
    _upsert(GROUP / "source_register.csv", "source_id", [local_source])
    _upsert(GROUP / "dataset_manifest.csv", "file_name", [{
        "file_name": FILENAME,
        "description": "Single first-party announcement of approximately 600 t roadside-grass processing for an autumn campaign; plan only, not verified realized tonnage.",
        "row_count": 1,
        "schema_version": "1.0",
        "encoding": "UTF-8",
        "delimiter": ",",
        "integration_readiness": "traceable_project_announcement_reference_only_not_supply_input",
        "limitations": "No delivered-mass records or wet/dry basis; date is event-context only; a separate same-number GKB-own-grass Bokashi quantity is not confirmation.",
    }])

    rel = f"Pre-treatment/Feedstock/{FILENAME}"
    _upsert(AUDIT / "global_source_register.csv", "dataset_path|source_id", [{
        "dataset_path": rel,
        "dataset_group": "Pre-treatment/Feedstock",
        "source_id": SOURCE_ID,
        "source_title": TITLE,
        "authors": local_source["authors"],
        "year": "2025",
        "doi_or_stable_id": "",
        "url": f"{LINKEDIN_URL}; {NETWORK_URL}; {EVENT_URL}",
        "source_type": local_source["source_type"],
        "notes": SOURCE_NOTES,
    }])
    _upsert(AUDIT / "global_dataset_manifest.csv", "dataset_path", [{
        "dataset_path": rel,
        "category": "Pre-treatment",
        "subgroup": "Greenhub announced seasonal feed quantity; Phase 1 with planned route context in Phases 3–4",
        "filename": FILENAME,
        "row_count_observed": 1,
        "header_count": len(FIELDS),
        "headers": "; ".join(FIELDS),
        "standardized_status_values": "project_announcement;reference_only",
        "detected_readiness": "D3",
        "notes": "Approximate planned quantity; no measurement/basis/completion evidence. Kept distinct from 600 t GKB own grass to Bokashi.",
    }])
    _upsert(AUDIT / "global_dataset_readiness.csv", "dataset_path", [{
        "dataset_path": rel,
        "category": "Pre-treatment",
        "subgroup": "Greenhub announced seasonal feed quantity; Phase 1 with planned route context in Phases 3–4",
        "readiness": "D3",
        "duplicate_ids": 0,
        "duplicate_rows": 0,
        "numeric_rows": 1,
        "unsourced_numeric_rows": 0,
        "numeric_rows_missing_exact_location": 0,
        "unit_conflicts": 0,
        "basis_conflicts": 0,
        "cross_reference_issues": 0,
        "equation_missing_inputs": 0,
        "equation_symbol_mismatches": 0,
        "notes": "Numeric value has exact linked announcement source; despite its numeric form it is a planned approximate quantity, not a measured supply observation. Basis and realized status absent.",
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
    print(json.dumps({"dataset": rel, "rows": 1, "sha256": digest, "activation_state": "reference_only"}, indent=2))


if __name__ == "__main__":
    build()
