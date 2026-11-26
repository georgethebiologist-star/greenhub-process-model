"""Register published, assumption-based roadside supply scenarios from Poland.

The source table is a regional planning estimate, not a field measurement or a
GreenHub supply input. Pair labels are preserved positionally because the
accessible table rendering does not safely establish their named scenario.
"""
from __future__ import annotations

import csv
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "Greenhub/data"
FOLDER = DATA / "Pre-treatment/Feedstock"
AUDIT = DATA / "global_audit_package"
SOURCE_ID = "SRC-DUCZKOWSKA-2026-ROAD-BIOMASS"
DOI = "10.3390/en19174185"
DOI_URL = f"https://doi.org/{DOI}"
ARTICLE_URL = "https://www.mdpi.com/1996-1073/19/17/4185"
INSTITUTIONAL_RECORD_URL = "https://repo.uni.opole.pl/info/article/UOf780cd356572489298c7fb32adf52f71"
TITLE = "Roadside Grass Biomass Assessment and Capacity-Constrained Allocation Using Aerial Geographic Information"
AUTHORS = "Anna Duczkowska; Ryszard Beniak; Arkadiusz Gardecki; Joanna Rut; Michal Podpora; Bartlomiej Klin; David Kasperek"
RETRIEVED = "2026-11-08"

SUPPLY_FILE = FOLDER / "roadside_biomass_municipality_scenarios_duczkowska_2026_reference.csv"
CAPACITY_FILE = FOLDER / "roadside_biomass_collection_capacity_scenarios_duczkowska_2026_reference.csv"

SUPPLY_FIELDS = [
    "record_id", "source_id", "municipality_source_label", "geography", "reference_period",
    "metric", "reported_pair_position", "reported_value", "reported_unit",
    "normalized_value", "normalized_unit", "conversion_method", "basis",
    "evidence_type", "assumptions_and_conditions", "source_location", "evidence_class",
    "quality_class", "maturity_class", "activation_state", "transferability", "limitations",
]
CAPACITY_FIELDS = [
    "record_id", "source_id", "scenario_source_description", "north_center_capacity_t",
    "south_center_capacity_t", "nodes_assigned_to_south", "metric_basis", "geography",
    "source_location", "evidence_type", "evidence_class", "quality_class", "maturity_class",
    "activation_state", "limitations",
]

# Table 2, transcribed exactly as surfaced in the publisher's accessible full-text
# index. Gg-to-tonne normalization is a transparent unit conversion (1 Gg = 1000 t).
MUNICIPALITY_TABLE = [
    ("Kołobrzeg-Ustroń", (2.9, 5.4), 60.8, (30.4, 57.0), (19.5, 29.2)),
    ("Siemyśl", (2.4, 4.8), 50.2, (25.1, 37.6), (16.1, 24.1)),
    ("Dygowo", (2.9, 5.8), 60.4, (30.2, 45.3), (19.3, 29.0)),
    ("Gościno", (2.2, 4.4), 46.4, (23.2, 34.8), (14.9, 22.3)),
    ("Rymań", (3.8, 7.6), 79.4, (39.7, 59.6), (25.4, 38.1)),
]

COMMON_LIMITATIONS = (
    "Polish Kołobrzeg County planning estimate, not Dutch roadside supply or GreenHub field data. "
    "The source describes scenario calculations based on road/mowing information, aerial screening, "
    "and assumptions; it is not a weighbridge measurement or field-validated biomass model. "
    "The table's paired values are kept as positions A/B; this extract does not infer one-cut/two-cut "
    "labels, month allocation, or a fresh/dry mass basis. Not a runtime parameter or default."
)


def _read_csv(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    with path.open(encoding="utf-8-sig", newline="") as stream:
        reader = csv.DictReader(stream)
        return list(reader.fieldnames or []), list(reader)


def _write_csv(path: Path, fields: list[str], rows: list[dict[str, object]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def _upsert(path: Path, record: dict[str, object], key: str) -> None:
    fields, rows = _read_csv(path)
    if not fields or key not in fields:
        raise ValueError(f"Expected register key {key!r} in {path}")
    rows = [row for row in rows if row.get(key) != str(record[key])]
    rows.append({field: record.get(field, "") for field in fields})
    _write_csv(path, fields, rows)


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _metadata(path: Path, rows: list[dict[str, object]], scope: str, digest: str) -> dict[str, object]:
    return {
        "source_file": path.name,
        "source_id": SOURCE_ID,
        "dataset_id": f"urn:greenhub:dataset:duczkowska-2026:{path.stem}:v1",
        "dataset_title": scope,
        "source_dataset_path": f"Greenhub/data/Pre-treatment/Feedstock/{path.name}",
        "source_data_sha256": digest,
        "persistent_identifier": DOI,
        "doi": DOI,
        "source_url": DOI_URL,
        "article_url": ARTICLE_URL,
        "institutional_record_url": INSTITUTIONAL_RECORD_URL,
        "source_title": TITLE,
        "authors": AUTHORS.split("; "),
        "publisher": "MDPI / Energies; Opole University of Technology institutional bibliography",
        "publication_year": 2026,
        "publication_date": "2026-09-04",
        "retrieval_date": RETRIEVED,
        "source_location": "Table 2; Sections 2.1–2.5 and 3.3–3.5; conclusions.",
        "license_or_rights": "CC BY 4.0 as recorded in the Opole University institutional bibliography record for the publisher version.",
        "license_url": "https://creativecommons.org/licenses/by/4.0/",
        "geography": "Kołobrzeg County, West Pomeranian Voivodeship, Poland.",
        "evidence_class": "B_primary_literature_published_scenario_estimates_not_direct_measurements",
        "quality_class": "B",
        "maturity_class": "D3",
        "activation_state": "reference_only",
        "calculation_connected": False,
        "parameter_registry_mapping": None,
        "row_count": len(rows),
        "data_origin": "Article reports derived estimates using county-road/mowing information and visually screened 2024 orthophotography; road data were obtained from the county LP-Portal. The study does not provide the underlying road-node/segment dataset in its data statement.",
        "methods_and_assumptions": [
            "Two mowing periods per year are discussed for Polish road-maintenance practice; this is not a measured Dutch seasonal profile.",
            "For a volume-based pathway the paper assumes 1.5 m3/km, 0.3 recoverable fraction, bulk density 0.212 t/m3, calorific value 13 GJ/t and useful-energy efficiency 0.8.",
            "Table 2 also presents municipality mowing mass values; the article states these are mass-based and are not converted using the volume-based density assumption.",
            "No field validation of the estimated biomass quantities is reported; no operational collection costs or vehicle-routing optimization are included.",
        ],
        "transcription_policy": "Table 2 values are transcribed as reported. For mowed-mass values only, Gg/a is additionally converted to t/a using 1 Gg = 1000 t. Table pairs are assigned positional labels A/B only; no scenario name or wet/dry basis is inferred.",
        "uncertainty": "No replicate-level measurement uncertainty is reported for the scenario estimates. Their uncertainty is assumption- and spatial-screening-dependent; not represented as a statistical interval.",
        "applicability": "Useful as an external Phase 1 spatial-supply and collection-capacity method/benchmark. Not an annual delivered supply estimate for the Netherlands, GreenHub, or any specific road authority.",
        "known_limitations": [COMMON_LIMITATIONS, "Source-table pair labels and mass basis are not resolved in this extract; preserve the paper and source citation for review."],
        "records_sha256": digest,
        "fair_metadata": {
            "findable": "DOI, institutional record URL, article URL, dataset URN and checksum are recorded.",
            "accessible": "The published article is linked; data are transcribed into local UTF-8 CSVs and indexed in the FAIR catalog.",
            "interoperable": "Each metric has explicit reported and normalized units, geography, metric identity and source location.",
            "reusable": "CC BY 4.0 attribution, estimate-vs-measurement distinction, assumptions, conversion, uncertainty and transfer limits are explicit.",
        },
    }


def _register_file(path: Path, rows: list[dict[str, object]], fields: list[str], purpose: str, readiness_note: str) -> None:
    digest = _sha256(path)
    sidecar = _metadata(path, rows, purpose, digest)
    path.with_suffix(".csv.source.json").write_text(json.dumps(sidecar, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    rel = f"Pre-treatment/Feedstock/{path.name}"
    _upsert(FOLDER / "dataset_manifest.csv", {
        "file_name": path.name,
        "description": purpose,
        "row_count": len(rows),
        "schema_version": "1.0",
        "encoding": "UTF-8",
        "delimiter": ",",
        "integration_readiness": "traceable_reference_only_not_runtime_eligible",
        "limitations": readiness_note,
    }, "file_name")
    _upsert(AUDIT / "global_source_register.csv", {
        "dataset_path": rel,
        "dataset_group": "Pre-treatment/Feedstock; external roadside spatial-supply comparator",
        "source_id": SOURCE_ID,
        "source_title": TITLE,
        "authors": AUTHORS,
        "year": "2026",
        "doi_or_stable_id": DOI,
        "url": DOI_URL,
        "source_type": "peer-reviewed open-access study; published spatial scenario estimate",
        "notes": readiness_note,
    }, "dataset_path")
    _upsert(AUDIT / "global_dataset_manifest.csv", {
        "dataset_path": rel,
        "category": "Pre-treatment",
        "subgroup": "Feedstock; Polish roadside-grass spatial supply comparator",
        "filename": path.name,
        "row_count_observed": len(rows),
        "header_count": len(fields),
        "headers": "; ".join(fields),
        "standardized_status_values": "B;reference_only",
        "detected_readiness": "D3",
        "notes": readiness_note,
    }, "dataset_path")
    _upsert(AUDIT / "global_dataset_readiness.csv", {
        "dataset_path": rel,
        "category": "Pre-treatment",
        "subgroup": "Feedstock; Polish roadside-grass spatial supply comparator",
        "readiness": "D3",
        "duplicate_ids": "0",
        "duplicate_rows": "0",
        "numeric_rows": len(rows),
        "unsourced_numeric_rows": "0",
        "numeric_rows_missing_exact_location": "0",
        "unit_conflicts": "0",
        "basis_conflicts": "0",
        "cross_reference_issues": "0",
        "equation_missing_inputs": "0",
        "equation_symbol_mismatches": "0",
        "notes": readiness_note,
    }, "dataset_path")
    _upsert(AUDIT / "source_dataset_checksums.csv", {
        "dataset_path": rel,
        "sha256": digest,
        "byte_size": path.stat().st_size,
    }, "dataset_path")


def _refresh_summary() -> None:
    summary_path = AUDIT / "global_validation_summary.json"
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    _, manifests = _read_csv(AUDIT / "global_dataset_manifest.csv")
    _, readiness = _read_csv(AUDIT / "global_dataset_readiness.csv")
    counts: dict[str, int] = {}
    for row in readiness:
        value = row.get("readiness", "")
        counts[value] = counts.get(value, 0) + 1
    summary["dataset_count"] = len(manifests)
    summary["readiness_counts"] = counts
    summary["generated_at"] = datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")
    summary_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main() -> None:
    supply_rows: list[dict[str, object]] = []
    for municipality, mowing, theoretical, technical, useful in MUNICIPALITY_TABLE:
        metrics = [
            ("mowed_roadside_biomass", "A", mowing[0], "Gg/a", mowing[0] * 1000, "t/a", "1 Gg = 1000 t"),
            ("mowed_roadside_biomass", "B", mowing[1], "Gg/a", mowing[1] * 1000, "t/a", "1 Gg = 1000 t"),
            ("theoretical_energy_potential", "", theoretical, "TJ", theoretical, "TJ", "Source unit retained; no conversion"),
            ("technical_energy_potential", "A", technical[0], "TJ", technical[0], "TJ", "Source unit retained; no conversion"),
            ("technical_energy_potential", "B", technical[1], "TJ", technical[1], "TJ", "Source unit retained; no conversion"),
            ("useful_energy_potential", "A", useful[0], "TJ/a", useful[0], "TJ/a", "Source unit retained; no conversion"),
            ("useful_energy_potential", "B", useful[1], "TJ/a", useful[1], "TJ/a", "Source unit retained; no conversion"),
        ]
        for metric, pair, value, unit, normalized, normalized_unit, conversion in metrics:
            supply_rows.append({
                "record_id": f"DUC26-{len(supply_rows) + 1:03d}",
                "source_id": SOURCE_ID,
                "municipality_source_label": municipality,
                "geography": "Kołobrzeg County, Poland",
                "reference_period": "Published 2026; source data access dates 2024/2025; estimate annualized by the article",
                "metric": metric,
                "reported_pair_position": pair,
                "reported_value": value,
                "reported_unit": unit,
                "normalized_value": normalized,
                "normalized_unit": normalized_unit,
                "conversion_method": conversion,
                "basis": (
                    "Annual mowed roadside biomass; source table does not establish wet/dry basis or name the two paired cases."
                    if metric == "mowed_roadside_biomass" else
                    "Source-reported planning estimate; Table 2 unit retained; not a measured plant energy output."
                ),
                "evidence_type": "published spatial scenario estimate based on road/mowing records, aerial screening, and stated assumptions; not field-measured delivered supply",
                "assumptions_and_conditions": "Two annual mowing periods are discussed. The article's volume pathway assumes 1.5 m3/km, 0.3 recoverable fraction, 0.212 t/m3 bulk density, 13 GJ/t calorific value and 0.8 useful-energy efficiency. Table 2 mass values are stated to be independent mass-based inputs.",
                "source_location": "Table 2; Sections 2.3 and 3.3",
                "evidence_class": "B_primary_literature_published_scenario_estimate",
                "quality_class": "B",
                "maturity_class": "D3",
                "activation_state": "reference_only",
                "transferability": "Polish county-road comparator; not Dutch roadside/VARTA or GreenHub site evidence",
                "limitations": COMMON_LIMITATIONS,
            })
    _write_csv(SUPPLY_FILE, SUPPLY_FIELDS, supply_rows)

    capacity_rows = [
        {
            "record_id": "DUC26-CAP-001", "source_id": SOURCE_ID,
            "scenario_source_description": "Reported southern collection-centre capacity case; other-centre capacity not transcribed as it is not specified in the accessible abstract.",
            "north_center_capacity_t": "", "south_center_capacity_t": 3000,
            "nodes_assigned_to_south": 25, "metric_basis": "Count of road nodes assigned by the paper's custom network-allocation procedure.",
            "geography": "Kołobrzeg County, Poland", "source_location": "Abstract; Section 3.5; Conclusions",
            "evidence_type": "reported algorithmic scenario result; not a measured transport outcome",
            "evidence_class": "B_primary_literature_reported_scenario_result", "quality_class": "B", "maturity_class": "D3",
            "activation_state": "reference_only", "limitations": COMMON_LIMITATIONS,
        },
        {
            "record_id": "DUC26-CAP-002", "source_id": SOURCE_ID,
            "scenario_source_description": "Reported southern-center capacity case; capacity of the other center is not stated in the Figure 7 caption.",
            "north_center_capacity_t": "", "south_center_capacity_t": 5000,
            "nodes_assigned_to_south": 36, "metric_basis": "Count of road nodes assigned by the paper's custom network-allocation procedure.",
            "geography": "Kołobrzeg County, Poland", "source_location": "Figure 7 caption",
            "evidence_type": "reported algorithmic scenario result; not a measured transport outcome",
            "evidence_class": "B_primary_literature_reported_scenario_result", "quality_class": "B", "maturity_class": "D3",
            "activation_state": "reference_only", "limitations": COMMON_LIMITATIONS,
        },
        {
            "record_id": "DUC26-CAP-003", "source_id": SOURCE_ID,
            "scenario_source_description": "Equal storage-capacity limits at both collection centres.",
            "north_center_capacity_t": 5875, "south_center_capacity_t": 5875,
            "nodes_assigned_to_south": 41, "metric_basis": "Count of road nodes assigned by the paper's custom network-allocation procedure.",
            "geography": "Kołobrzeg County, Poland", "source_location": "Abstract; Section 3.5; Conclusions",
            "evidence_type": "reported algorithmic scenario result; not a measured transport outcome",
            "evidence_class": "B_primary_literature_reported_scenario_result", "quality_class": "B", "maturity_class": "D3",
            "activation_state": "reference_only", "limitations": COMMON_LIMITATIONS,
        },
    ]
    _write_csv(CAPACITY_FILE, CAPACITY_FIELDS, capacity_rows)

    _upsert(FOLDER / "source_register.csv", {
        "source_id": SOURCE_ID,
        "source_title": TITLE,
        "authors": AUTHORS,
        "year": "2026",
        "source_type": "peer-reviewed open-access journal article; spatial planning scenario estimates",
        "doi_or_stable_identifier": DOI,
        "stable_url": DOI_URL,
        "material": "Roadside grass in Kołobrzeg County, Poland; five municipality-level planning estimates and three collection-centre capacity-allocation summaries.",
        "quality_notes": "B-tier published estimate/scenario results, not field-measured delivered supply. CC BY 4.0 is shown in the Opole University institutional record. Not GreenHub-calibrated or activated.",
        "accessed_date": RETRIEVED,
    }, "source_id")

    _register_file(SUPPLY_FILE, supply_rows, SUPPLY_FIELDS,
        "Table 2 municipality-level roadside biomass, theoretical/technical energy, and useful-energy estimates from Duczkowska et al. (2026).",
        "Five Polish municipality rows in long format; paired source values retain positional A/B labels because the exact scenario labels and mass basis are not established here. Derived scenario estimates only.")
    _register_file(CAPACITY_FILE, capacity_rows, CAPACITY_FIELDS,
        "Three published collection-centre capacity-allocation scenario summaries; southern-center assigned-node counts.",
        "Only three headline scenario results are transcribed; the 3000 t and 5000 t cases do not state the other center's capacity in the cited source locations. Underlying road-node assignments and route distances are not supplied by this extract.")
    _refresh_summary()
    print(json.dumps({
        "source_id": SOURCE_ID,
        "doi": DOI,
        "municipal_supply_records": len(supply_rows),
        "capacity_scenario_records": len(capacity_rows),
        "supply_sha256": _sha256(SUPPLY_FILE),
        "capacity_sha256": _sha256(CAPACITY_FILE),
        "activation_state": "reference_only",
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
