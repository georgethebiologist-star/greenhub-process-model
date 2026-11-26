"""Transcribe ReJuice WP5 roadside-grass season and ensiled-juice context.

The source is a 2025 draft project deliverable combining literature and
stakeholder interviews. Its broad seasonal statements and approximate juice
yield are contextual evidence only, not a Greenhub monthly supply curve or
press calibration.
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
FILENAME = "rejuice_wp5_roadside_grass_seasonality_and_ensiled_juice_reference.csv"
CSV_PATH = GROUP / FILENAME
SIDECAR_PATH = Path(str(CSV_PATH) + ".source.json")
SOURCE_ID = "SRC-REJUICE-WP5-SEASONAL-CALENDAR-DRAFT-2025"
URL = "https://interregvlaned.eu/uploads/project-downloads/Seizoenskalender_deliverable_DRAFT.pdf"
RETRIEVED = "2026-11-08"
FIELDS = [
    "record_id", "source_id", "phase_relevance", "source_section", "metric",
    "reported_value", "unit", "measurement_basis", "observation_status",
    "evidence_class", "quality_class", "activation_state", "source_location",
    "geography_or_material", "limitations", "retrieval_date",
]

LIMITATIONS = {
    "REJUICE25-BERMGRAS-AVAILABILITY-WINDOW": (
        "The source labels this as regional availability, not a measured delivery calendar. It gives no annual or monthly "
        "tonnage by date, site, cut, owner, contractor, or route. It is not a Greenhub feed schedule."
    ),
    "REJUICE25-BERMGRAS-PEAK-WINDOWS": (
        "Broad regional peak windows are descriptive only; no monthly mass shares, cut-level records, or uncertainty are provided. "
        "The statement pools Netherlands and Flanders and cannot validate the model's monthly allocation."
    ),
    "REJUICE25-ENSILED-GRASS-JUICE-FRACTION": (
        "Approximate project-summary statement only. The feed batch, press, replicates, juice/fiber mass closure, moisture, and "
        "wet-versus-dry denominator are not stated. Do not use as a screw-press recovery factor or infer component recoveries."
    ),
    "REJUICE25-ENSILED-JUICE-PROTEIN-QUALITY": (
        "Qualitative statement in a draft review; no paired raw-grass/silage/juice measurements, assay method, amino-acid profile, "
        "or heat-precipitation yield is given. Cultivated silage process conditions are not Greenhub roadside-feed calibration."
    ),
}

ROWS = [
    {
        "record_id": "REJUICE25-BERMGRAS-AVAILABILITY-WINDOW",
        "phase_relevance": "1",
        "source_section": "5.1 Bermgras; printed p. 12",
        "metric": "regional_roadside_grass_availability_window",
        "reported_value": "May through November; not constant",
        "unit": "calendar months (qualitative)",
        "measurement_basis": "Seasonal review statement; no month-specific measured tonnage.",
        "observation_status": "reported_regional_seasonal_context",
        "evidence_class": "draft_project_review_secondary_literature_and_interviews",
        "quality_class": "B",
        "geography_or_material": "Roadside grass; Netherlands and Flanders pooled in the report section",
    },
    {
        "record_id": "REJUICE25-BERMGRAS-PEAK-WINDOWS",
        "phase_relevance": "1",
        "source_section": "5.1 Bermgras; printed p. 13",
        "metric": "reported_main_roadside_grass_availability_peaks",
        "reported_value": "Mid-June to mid-July; mid-September to mid-October",
        "unit": "calendar windows (qualitative)",
        "measurement_basis": "The report describes these as periods with the largest amounts; no month-by-month mass series or weighing basis is supplied.",
        "observation_status": "reported_regional_peak_windows_not_mass_distribution",
        "evidence_class": "draft_project_review_secondary_literature_and_interviews",
        "quality_class": "B",
        "geography_or_material": "Roadside grass; Netherlands and Flanders pooled in the report section",
    },
    {
        "record_id": "REJUICE25-ENSILED-GRASS-JUICE-FRACTION",
        "phase_relevance": "3;4",
        "source_section": "5.1 Bermgras; printed p. 13",
        "metric": "approximate_juice_fraction_from_ensiled_grass_pressing",
        "reported_value": "approximately 40",
        "unit": "% (basis unspecified)",
        "measurement_basis": "The draft says pressing ensiled grass yields approximately 40% juice; denominator and wet/dry basis are not reported.",
        "observation_status": "reported_approximate_project_context_value",
        "evidence_class": "draft_project_summary_estimate",
        "quality_class": "C",
        "geography_or_material": "Ensiled grass in the ReJuice project context; exact feed origin/cultivar and press conditions not stated",
    },
    {
        "record_id": "REJUICE25-ENSILED-JUICE-PROTEIN-QUALITY",
        "phase_relevance": "2;4",
        "source_section": "5.1 Bermgras; printed p. 13",
        "metric": "reported_effect_of_ensiling_on_thermal_protein_precipitation_suitability",
        "reported_value": "The draft states that ensiling degrades proteins to amino acids and peptides and that ensiled grass juice is unsuitable for heat precipitation.",
        "unit": "qualitative statement",
        "measurement_basis": "No paired composition or precipitation-yield measurement is given in this source passage.",
        "observation_status": "qualitative_process_claim_not_numeric_measurement",
        "evidence_class": "draft_project_review_process_statement",
        "quality_class": "C",
        "geography_or_material": "Ensiled roadside grass in the project review; exact feed origin and process conditions unstated",
    },
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
    rows = []
    for item in ROWS:
        record = {field: "" for field in FIELDS}
        record.update(item)
        record.update({
            "source_id": SOURCE_ID,
            "activation_state": "reference_only",
            "source_location": item["source_section"],
            "limitations": LIMITATIONS[item["record_id"]],
            "retrieval_date": RETRIEVED,
        })
        rows.append(record)
    if len({row["record_id"] for row in rows}) != len(rows):
        raise ValueError("Duplicate ReJuice reference record ID")
    _write(CSV_PATH, FIELDS, rows)
    digest = hashlib.sha256(CSV_PATH.read_bytes()).hexdigest()

    sidecar = {
        "dataset_id": "urn:greenhub:dataset:feedstock:rejuice-wp5-roadside-season-and-ensiled-juice:v1",
        "dataset_version": "1.0.0",
        "title": "ReJuice WP5 draft roadside-grass season and ensiled-juice context",
        "source_file": FILENAME,
        "source_file_sha256": digest,
        "source_id": SOURCE_ID,
        "citation": "Degieter, M., Schouteten, J. J., & Fernandes de Souza, M. (2025, April). WP5 Seizoenskalender [Draft deliverable]. ReJuice Interreg Vlaanderen-Nederland.",
        "doi": None,
        "source_url": URL,
        "publication_date": "2025-04",
        "retrieval_date": RETRIEVED,
        "geography": "Regional statements pool Netherlands and Flanders; individual roadside-grass sites are not identified.",
        "record_count": len(rows),
        "process_phases": [1, 2, 3, 4],
        "rights_status": "The linked deliverable is marked DRAFT; no explicit reuse license was identified. Only concise factual statements are transcribed with attribution; the PDF is not redistributed.",
        "evidence_class": "draft project deliverable combining secondary literature and stakeholder interviews",
        "quality_class": "B for source-reported regional season context; C for the approximate press-yield and qualitative process statements without measurement protocols",
        "activation_state": "reference_only",
        "calculation_connected": False,
        "runtime_parameter_mapping": None,
        "extraction_method": "Factual English transcription of four roadside-grass statements in Section 5.1. No monthly mass profile, yield denominator, conversion, or missing value was inferred.",
        "important_deduplication": "The draft repeats broad regional roadside-biomass totals attributed to Inagro and RVO (2014). Those totals were not re-imported here because the RVO report is already separately staged; this extract records only the additional seasonal and ensiled-juice statements.",
        "limitations": [
            "The report is explicitly a draft and states that it combines secondary literature with stakeholder interviews; the roadside section does not publish a cut-by-cut or monthly supply dataset.",
            "May–November and the two peak windows are regional qualitative statements, not measured monthly tonnage shares or a GreenHub delivery calendar.",
            "The approximate 40% juice figure has no reported press conditions, batch size, replicate uncertainty, wet/dry denominator, or closing mass balance; it is not a GreenHub press recovery factor.",
            "The qualitative protein statement has no paired assays or product yields and cannot activate protein precipitation equations.",
            "These regional review statements do not establish current Dutch roadside-grass contracts, accessible feed, or GreenHub-specific availability."
        ],
        "fair_metadata": {
            "findable": "Versioned local URN, source ID, full author/title/date citation, source URL, section/page location, and row IDs are supplied.",
            "accessible": "UTF-8 CSV and JSON sidecar are indexed through the local and global FAIR catalogs.",
            "interoperable": "Long-form records separate phase, metric, value, unit, measurement basis, observation status, evidence class, and limitations.",
            "reusable": "Draft status, evidence hierarchy, geographic transfer limits, missing bases, and runtime exclusion are explicit."
        }
    }
    SIDECAR_PATH.write_text(json.dumps(sidecar, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    source = {
        "source_id": SOURCE_ID,
        "source_title": "WP5 Seizoenskalender (draft)",
        "authors": "Margo Degieter; Joachim J. Schouteten; Marcella Fernandes de Souza",
        "year": "2025",
        "source_type": "Interreg project draft deliverable; secondary literature review and stakeholder interview synthesis",
        "doi_or_stable_identifier": "",
        "stable_url": URL,
        "material": "Roadside grass availability season and press-juice context; Netherlands/Flanders regional summary",
        "quality_notes": "Draft regional statements only. The broad seasonal window is qualitative, not a measured monthly availability profile. The approximate 40% ensiled-grass juice fraction lacks mass basis and press protocol. Reference-only; no runtime use.",
        "accessed_date": RETRIEVED,
    }
    _upsert(GROUP / "source_register.csv", "source_id", [source])
    _upsert(GROUP / "dataset_manifest.csv", "file_name", [{
        "file_name": FILENAME,
        "description": "Four regional seasonal and ensiled-grass juice statements from the ReJuice WP5 2025 draft; reference-only, not a GreenHub monthly supply curve or press calibration.",
        "row_count": len(rows),
        "schema_version": "1.0",
        "encoding": "UTF-8",
        "delimiter": ",",
        "integration_readiness": "traceable_draft_context_reference_only_not_runtime_eligible",
        "limitations": "No monthly tonnage shares; approx. 40% juice lacks feed/press denominator, conditions and mass balance; all records remain reference-only.",
    }])

    rel = f"Pre-treatment/Feedstock/{FILENAME}"
    _upsert(AUDIT / "global_source_register.csv", "dataset_path|source_id", [{
        "dataset_path": rel,
        "dataset_group": "Pre-treatment/Feedstock",
        "source_id": SOURCE_ID,
        "source_title": "WP5 Seizoenskalender (draft)",
        "authors": source["authors"],
        "year": "2025",
        "doi_or_stable_id": "",
        "url": URL,
        "source_type": source["source_type"],
        "notes": source["quality_notes"],
    }])
    _upsert(AUDIT / "global_dataset_manifest.csv", "dataset_path", [{
        "dataset_path": rel,
        "category": "Pre-treatment",
        "subgroup": "Seasonal roadside-grass context and ensiled-juice comparator; Phases 1–4",
        "filename": FILENAME,
        "row_count_observed": len(rows),
        "header_count": len(FIELDS),
        "headers": "; ".join(FIELDS),
        "standardized_status_values": "B;C;reference_only",
        "detected_readiness": "D3",
        "notes": "Draft regional review. No measured seasonal supply series or press mass balance; broad regional totals in the draft were excluded here to avoid duplicating the separately staged RVO data.",
    }])
    _upsert(AUDIT / "global_dataset_readiness.csv", "dataset_path", [{
        "dataset_path": rel,
        "category": "Pre-treatment",
        "subgroup": "Seasonal roadside-grass context and ensiled-juice comparator; Phases 1–4",
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
        "notes": "Numeric juice fraction is exact as an approximate source statement but lacks denominator and process conditions. It is not a validated equation input.",
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
        status = item.get("readiness", "")
        counts[status] = counts.get(status, 0) + 1
    summary["readiness_counts"] = counts
    summary["generated_at"] = datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")
    summary_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"dataset": rel, "rows": len(rows), "sha256": digest, "activation_state": "reference_only"}, indent=2))


if __name__ == "__main__":
    build()
