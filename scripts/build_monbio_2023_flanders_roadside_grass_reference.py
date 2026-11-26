"""Extract the roadside-grass portion of MONBIO 2.0 Table 27.

This is a regional, historical inventory comparator. It does not set the
GreenHub feed default or establish current, contracted, delivered supply.
"""
from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "Greenhub" / "data"
GROUP = DATA / "Pre-treatment" / "Feedstock"
AUDIT = DATA / "global_audit_package"
FILENAME = "monbio_2023_flanders_roadside_grass_inventory_reference.csv"
CSV_PATH = GROUP / FILENAME
SIDECAR_PATH = Path(str(CSV_PATH) + ".source.json")
SOURCE_ID = "SRC-MONBIO2-FLANDERS-ROADSIDECUTTINGS-2023"
TITLE = "Monitor van de Vlaamse bio-economie: update 2019-2020 (MONBIO 2.0), Eindrapport"
URL = "https://ilvo.vlaanderen.be/uploads/images/MONBIO2.0_rapport_FINAAL_2023-10-26-093333_wndy.pdf"
RETRIEVED = "2026-11-08"
FIELDS = [
    "record_id", "source_id", "report_title", "publisher", "report_year",
    "report_table", "management_actor", "reported_area_ha", "annual_dry_matter_tonnes",
    "underlying_data_period", "reported_method_or_note", "geography", "evidence_class",
    "quality_class", "activation_state", "transferability", "limitations", "retrieval_date",
]

LIMITATIONS = (
    "Historical Flemish regional inventory, not a GreenHub contracted catchment. The table combines "
    "different source years and methods (including wet-to-DM conversion, extrapolation, and a modeled "
    "railway estimate); its total is not a single-year measured delivery total. Area is not necessarily "
    "accessible or harvestable. No wet-mass basis, moisture by cut, parcel-level geometry, monthly supply, "
    "collection losses, or current contract records are reported. Reference-only; do not map to a Dutch "
    "default, seasonal schedule, or runtime parameter."
)

ACTORS = [
    ("MONBIO23-001", "Agentschap Wegen en Verkeer", "8230", "17809", "2010", "AWV weight tickets and invoices; fresh weight converted to dry matter using a 50% factor."),
    ("MONBIO23-002", "Municipalities", "12112", "44527", "2010", "Data from 257 municipalities extrapolated to Flanders."),
    ("MONBIO23-003", "De Vlaamse Waterweg", "2607", "6798", "2008", "Source data year 2008."),
    ("MONBIO23-004", "Infrabel", "724", "2898", "estimate", "Estimated from total railway length, a 2 × 4 m verge width, and 6 t DM/ha/year."),
    ("MONBIO23-005", "Reported roadside-grass subtotal", "", "72032", "mixed", "Source report subtotal across the four preceding actor rows; heterogeneous underlying periods and methods."),
]


def _read(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    if not path.exists():
        return [], []
    with path.open(encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        return reader.fieldnames or [], list(reader)


def _upsert(path: Path, row: dict[str, object], key: str) -> None:
    fields, rows = _read(path)
    if not fields:
        raise ValueError(f"Missing CSV header: {path}")
    values = {field: str(row.get(field, "")) for field in fields}
    rows = [existing for existing in rows if existing.get(key) != values[key]]
    rows.append(values)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    GROUP.mkdir(parents=True, exist_ok=True)
    rows = [{
        "record_id": rid, "source_id": SOURCE_ID, "report_title": TITLE,
        "publisher": "ILVO (with VITO contributions); Flemish Bioeconomy Policy Plan context",
        "report_year": "2023", "report_table": "Table 27, printed p. 91 / PDF p. 92",
        "management_actor": actor, "reported_area_ha": area,
        "annual_dry_matter_tonnes": dm, "underlying_data_period": period,
        "reported_method_or_note": method, "geography": "Flanders, Belgium",
        "evidence_class": "official_secondary_inventory_mixed_measurement_extrapolation_estimate",
        "quality_class": "C", "activation_state": "reference_only",
        "transferability": "regional_inventory_comparator_not_Dutch_site_supply",
        "limitations": LIMITATIONS, "retrieval_date": RETRIEVED,
    } for rid, actor, area, dm, period, method in ACTORS]
    with CSV_PATH.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
    digest = hashlib.sha256(CSV_PATH.read_bytes()).hexdigest()
    sidecar = {
        "dataset_id": "urn:greenhub:dataset:monbio-2023-flanders-roadside-grass-reference:v1",
        "dataset_title": "MONBIO 2.0 Flemish roadside grass area and annual dry-matter inventory (Table 27 extract)",
        "source_dataset_path": f"Greenhub/data/Pre-treatment/Feedstock/{FILENAME}",
        "source_data_sha256": digest, "rows": len(rows), "persistent_identifier": "",
        "source_url": URL, "source_id": SOURCE_ID, "source_title": TITLE,
        "publisher": "ILVO; VITO contributions", "publication_year": 2023,
        "source_location": "Table 27, printed p. 91 / PDF p. 92; discussion printed pp. 89-90",
        "retrieval_date": RETRIEVED, "geography": "Flanders, Belgium",
        "material_scope": "Reported roadside-grass inventory only; excludes the table's nature-grass and other-grass subtotals.",
        "data_type": "reported regional area and annual dry-matter estimates; mixed underlying source years and estimation methods",
        "license_or_rights": "No explicit open reuse license identified in the report or hosting page. Only a short, factual table extract is stored with attribution; do not redistribute the source PDF.",
        "evidence_class": "C_official_secondary_inventory_mixed_measurement_extrapolation_estimate",
        "activation_state": "reference_only", "readiness": "D3",
        "conversion_policy": "No conversions or recalculation. Reported areas and dry-matter tonnes are preserved as printed. The total row area is intentionally blank because Table 27 does not print a roadside-area subtotal.",
        "limitations": [LIMITATIONS, "Underlying cited source years are 2008 or 2010, except the Infrabel modeled estimate. Report publication year 2023 is not the observation year."],
        "citation": f"Van Kerckhove et al. (2023). {TITLE}. Table 27. {URL}",
    }
    SIDECAR_PATH.write_text(json.dumps(sidecar, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    local_source = {
        "source_id": SOURCE_ID, "source_title": TITLE,
        "authors": "Van Kerckhove; Desmet; Peeters; Snellinx; Van Meensel; Versyck; Cuypers",
        "year": "2023", "source_type": "official regional inventory report; mixed-source estimates",
        "doi_or_stable_identifier": "", "stable_url": URL,
        "material": "Flemish roadside grass only; Table 27 area and annual dry-matter estimates",
        "quality_notes": "Quality C; underlying agency data span 2008/2010 and include measured-ticket conversion, extrapolation, and a modeled railway estimate. No explicit reuse license; reference-only.",
        "accessed_date": RETRIEVED,
    }
    _upsert(GROUP / "source_register.csv", local_source, "source_id")
    _upsert(GROUP / "dataset_manifest.csv", {
        "file_name": FILENAME,
        "description": "Flemish roadside-grass area and annual dry-matter estimate by managing actor; Table 27 extract",
        "row_count": len(rows), "schema_version": "1.0", "encoding": "UTF-8", "delimiter": ",",
        "integration_readiness": "source-traceable; reference_only",
        "limitations": "Mixed historical years and methods; not Dutch site-specific or delivered supply; no runtime activation.",
    }, "file_name")

    rel = f"Pre-treatment/Feedstock/{FILENAME}"
    _upsert(AUDIT / "global_source_register.csv", {
        "dataset_path": rel, "dataset_group": "Pre-treatment/Feedstock", "source_id": SOURCE_ID,
        "source_title": TITLE, "authors": local_source["authors"], "year": "2023",
        "doi_or_stable_id": "", "url": URL, "source_type": local_source["source_type"],
        "notes": local_source["quality_notes"],
    }, "dataset_path")
    _upsert(AUDIT / "global_dataset_manifest.csv", {
        "dataset_path": rel, "category": "Pre-treatment", "subgroup": "Feedstock",
        "filename": FILENAME, "row_count_observed": len(rows), "header_count": len(FIELDS),
        "headers": "; ".join(FIELDS), "standardized_status_values": "C;reference_only",
        "detected_readiness": "D3", "notes": "Reported Table 27 figures, source methods and years retained; no default activation.",
    }, "dataset_path")
    _upsert(AUDIT / "global_dataset_readiness.csv", {
        "dataset_path": rel, "category": "Pre-treatment", "subgroup": "Feedstock",
        "readiness": "D3", "duplicate_ids": 0, "duplicate_rows": 0,
        "numeric_rows": 9, "unsourced_numeric_rows": 0,
        "numeric_rows_missing_exact_location": 0, "unit_conflicts": 0,
        "basis_conflicts": 0, "cross_reference_issues": 0,
        "equation_missing_inputs": 0, "equation_symbol_mismatches": 0,
        "notes": "Five actor/total records; area and dry-matter values are reported facts, but total includes heterogeneous source years/methods; reference-only.",
    }, "dataset_path")
    _upsert(AUDIT / "source_dataset_checksums.csv", {
        "dataset_path": rel, "sha256": digest, "byte_size": CSV_PATH.stat().st_size,
    }, "dataset_path")
    print(json.dumps({"dataset": rel, "rows": len(rows), "source_id": SOURCE_ID, "sha256": digest, "activation_state": "reference_only"}, indent=2))


if __name__ == "__main__":
    main()
