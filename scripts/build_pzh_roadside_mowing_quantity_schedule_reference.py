"""Capture South Holland's official annual mowing quantity and schedule statements.

The values are first-party published statements, not weighbridge records or a
spatially resolved harvest inventory. They remain reference-only.
"""
from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
FOLDER = ROOT / "Greenhub/data/Pre-treatment/Feedstock"
CSV_PATH = FOLDER / "pzh_roadside_mowing_quantity_and_schedule_reference.csv"
SIDECAR_PATH = CSV_PATH.with_suffix(".source.json")
SOURCE_ID = "SRC-PZH-VERGE-MOWING-2026"
SOURCE_URL = "https://werkenvoor.zuid-holland.nl/artikelen/de-bermen-in-zuid-holland-komen-tot-bloei/"
RETRIEVED = "2026-11-08"
TITLE = "De bermen in Zuid-Holland komen tot bloei: Een maaibeleid voor duurzaamheid en circulariteit"

FIELDS = [
    "record_id", "metric", "reported_value", "qualifier", "unit", "phase_relevance",
    "geography", "management_context", "source_id", "source_title", "publisher",
    "publication_date", "source_url", "source_location", "evidence_class",
    "quality_class", "activation_state", "measurement_basis", "uncertainty_or_limit",
    "notes",
]


def build_rows() -> list[dict[str, str]]:
    observations = [
        ("PZH-MOW26-ROAD-LENGTH", "provincially managed roads and verges", "647", "", "km", "1", "line 17", "Road-network extent; not a measure of verge area or feedstock.", "As stated by the Province; no GIS or measurement method given on this page."),
        ("PZH-MOW26-ANNUAL-GRASS", "grass mown from provincial verges per year", "10000", "approximately", "t/year", "1", "line 33", "Annual mass basis, moisture basis, included assets and weighing method are not specified; not all material is necessarily contracted, accessible or accepted by a plant.", "Direct transcription of the Province's approximate annual statement; do not infer wet/dry tonnes or availability fraction."),
        ("PZH-MOW26-SAFETY-ROUND", "annual safety mowing round", "April", "one described round", "calendar month", "1", "line 27", "Safety-related round for roundabouts, intersections and sightlines, distinct from ecological verge rounds.", "Schedule as published; no mass or treated area per round."),
        ("PZH-MOW26-MAIN-ROUNDS", "ecological verge mowing rounds", "2", "per year", "rounds/year", "1", "lines 22 and 27", "Described for ecologically managed provincial verges; road-specific mowing plans remain in place.", "Management frequency, not an assertion that every polygon produces harvestable grass in both rounds."),
        ("PZH-MOW26-WINDOW-1", "first annual ecological mowing window", "June–July", "reported window", "calendar months", "1", "line 27", "Province-wide narrative schedule with route-specific plans.", "No month-by-month mass profile or fixed dates are published."),
        ("PZH-MOW26-WINDOW-2", "second annual ecological mowing window", "September–October", "reported window", "calendar months", "1", "line 27", "Province-wide narrative schedule with route-specific plans.", "No month-by-month mass profile or fixed dates are published."),
        ("PZH-MOW26-REST", "cuttings left in field before pickup", "a few days", "qualitative source phrase", "not quantified", "1;2", "line 30", "Rest period is intended to allow insects to leave the cuttings.", "Not a calibrated drying duration; no moisture endpoint, weather, or mass loss reported."),
        ("PZH-MOW26-PICKUP", "preferred collection equipment", "pickup wagon after mowing/rest", "preferred practice", "qualitative", "1;3", "lines 29–30", "The article also mentions a disc mower as a preferred mowing method.", "No machine capacity, operating speed, fuel, collection efficiency, or losses reported."),
    ]
    rows = []
    for record_id, metric, value, qualifier, unit, phases, location, limit, note in observations:
        rows.append({
            "record_id": record_id,
            "metric": metric,
            "reported_value": value,
            "qualifier": qualifier,
            "unit": unit,
            "phase_relevance": phases,
            "geography": "Province of South Holland, Netherlands",
            "management_context": "Provincial ecological roadside-verge management; article says province-specific road plans are used.",
            "source_id": SOURCE_ID,
            "source_title": TITLE,
            "publisher": "Province of South Holland (official provincial website)",
            "publication_date": "not displayed on page",
            "source_url": SOURCE_URL,
            "source_location": location,
            "evidence_class": "official_first_party_management_statement",
            "quality_class": "B",
            "activation_state": "reference_only",
            "measurement_basis": "Direct English translation/paraphrase of the official Dutch page; no new numeric calculation.",
            "uncertainty_or_limit": limit,
            "notes": note,
        })
    return rows


def _write_csv(path: Path, rows: list[dict[str, str]], fields: list[str]) -> None:
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def _update_register() -> None:
    path = FOLDER / "source_register.csv"
    with path.open(encoding="utf-8-sig", newline="") as stream:
        reader = csv.DictReader(stream)
        fields = list(reader.fieldnames or [])
        rows = list(reader)
    existing = next((row for row in rows if row.get("source_id") == SOURCE_ID), None)
    source = {
        "source_id": SOURCE_ID,
        "source_title": TITLE,
        "authors": "Province of South Holland (provincial staff interview/narrative)",
        "year": "",
        "source_type": "official provincial management webpage",
        "doi_or_stable_identifier": "",
        "stable_url": SOURCE_URL,
        "material": "Province-managed roadside verges and mowing operations, South Holland, Netherlands",
        "quality_notes": "Official first-party narrative; states approx. 10,000 t grass mown/year, 647 km roads/verges, annual safety and ecological mowing windows, and collection practice. Moisture/mass basis and underlying weighing records are not given. Do not treat as delivered/accessible plant supply.",
        "accessed_date": RETRIEVED,
    }
    if existing is None:
        rows.append(source)
    else:
        existing.update(source)
    _write_csv(path, rows, fields)


def _update_manifest(count: int) -> None:
    path = FOLDER / "dataset_manifest.csv"
    with path.open(encoding="utf-8-sig", newline="") as stream:
        reader = csv.DictReader(stream)
        fields = list(reader.fieldnames or [])
        rows = list(reader)
    entry = {
        "file_name": CSV_PATH.name,
        "description": "Official South Holland annual verge-grass quantity, road-network context and mowing/collection schedule statements.",
        "row_count": str(count),
        "schema_version": "1.0",
        "encoding": "UTF-8",
        "delimiter": ",",
        "integration_readiness": "traceable_reference_only_not_runtime_eligible",
        "limitations": "Official narrative, not weighbridge or GIS harvest records; annual mass basis and accepted/accessibly collected share unknown; schedules are not measured seasonal tonnage profiles.",
    }
    existing = next((row for row in rows if row.get("file_name") == CSV_PATH.name), None)
    if existing is None:
        rows.append(entry)
    else:
        existing.update(entry)
    _write_csv(path, rows, fields)


def main() -> None:
    rows = build_rows()
    _write_csv(CSV_PATH, rows, FIELDS)
    digest = hashlib.sha256(CSV_PATH.read_bytes()).hexdigest()
    metadata = {
        "dataset_id": "urn:greenhub:dataset:feedstock:pzh-roadside-mowing-quantity-schedule:v1",
        "title": "South Holland roadside mowing quantity and schedule reference",
        "source_id": SOURCE_ID,
        "source_title": TITLE,
        "publisher": "Province of South Holland",
        "doi": None,
        "source_url": SOURCE_URL,
        "geography": "Province of South Holland, Netherlands",
        "retrieval_date": RETRIEVED,
        "source_locations": "Page lines 17, 22, 27, and 29–34 in the retrieved official page text; record-level line references are in the CSV.",
        "evidence_class": "official first-party management statement; underlying measurements not published",
        "quality_class": "B",
        "license_or_rights": "No explicit open-data license identified for this webpage; factual statements are transcribed with attribution; review rights before external redistribution.",
        "activation_state": "reference_only",
        "calculation_connected": False,
        "row_count": len(rows),
        "sha256_csv": digest,
        "data_handling": "English translations/paraphrases of published facts. No wet/dry interpretation, annualization, yield conversion, seasonal mass allocation or availability share is inferred.",
        "limitations": [
            "The approximately 10,000 t/year figure does not state whether mass is wet or dry, whether it is weighed, which assets are included, or what fraction is accessible and deliverable to GreenHub.",
            "The 647 km figure is road-network context, not verge area or an identified biomass denominator; no tonnes-per-kilometre ratio is calculated.",
            "The article describes an April safety round and two ecological mowing windows (June–July and September–October), but gives no seasonal mass split or measured annual availability profile.",
            "A few days of field rest is qualitative and is not converted into a storage-duration or drying parameter.",
            "No scenario input, runtime default, process model, UI setting, TEA/LCA calculation or Pareto output is changed.",
        ],
    }
    SIDECAR_PATH.write_text(json.dumps(metadata, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    _update_register()
    _update_manifest(len(rows))
    print(f"wrote {len(rows)} official-source reference records; sha256={digest}")


if __name__ == "__main__":
    main()
