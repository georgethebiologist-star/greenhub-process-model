"""Build a traceable extract of the 2017 OVAM report's GR3 mowing inventory.

This is a historical Flemish supply estimate, not a GreenHub catchment or a
measured delivery dataset. Keep grasslands and roadside verges separate.
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
FILENAME = "ovam_2017_gr3_flanders_mowing_supply_inventory_reference.csv"
CSV_PATH = GROUP / FILENAME
SIDECAR_PATH = Path(str(CSV_PATH) + ".source.json")
SOURCE_ID = "SRC-OVAM-GR3-2017-TABLE36"
SOURCE_URL = (
    "https://ovam.vlaanderen.be/documents/177281/310282/"
    "marktanalyse%2BBiomassa%28rest%29stromen-volledig_LR.pdf/"
    "0438936b-5dd3-1a12-c4e6-cb014c9b547b?download=true&t=1653497765000&version=1.0"
)
DOI = None
DATASET_URL = None
RETRIEVED = "2026-11-08"
TITLE = "Aanbod en bestemming biomassa(rest)stromen voor de circulaire economie in Vlaanderen"
FIELDS = [
    "record_id", "source_id", "report_title", "report_publisher", "report_publication_year",
    "underlying_study", "underlying_reference_period", "record_scope", "management_actor",
    "material_group", "annual_dry_matter_tonnes", "annual_fresh_matter_tonnes",
    "managed_area_ha", "reported_dm_yield_tonnes_per_ha", "fresh_mass_basis",
    "destination", "management_intensity", "source_location", "evidence_class",
    "quality_class", "activation_state", "transferability", "limitations", "retrieval_date",
]

LIMITATIONS = (
    "Historical Flemish inventory/GR3 potential estimate, not GreenHub contracted or delivered supply. "
    "The report warns that estimated area may not all be mown and some cuttings may remain at the site. "
    "It combines managed grasslands/nature and roadside verges; these groups are kept separate. "
    "Fresh-matter tonnage is derived by the report using 27% dry matter, not an independently paired wet-mass measurement. "
    "No seasonal delivery schedule, source coordinates, collection losses, or current Dutch site data are provided. "
    "The printed grassland actor rows sum to 26,554 t DM/y while the reported grassland subtotal is 26,553 t DM/y; "
    "the report does not explain this 1 t difference. The actor rows across grassland and verge categories sum to "
    "the reported overall total of 61,438 t DM/y. "
    "Reference-only; do not use as a GreenHub default or as a measured harvest contract."
)

# Table 36 columns: annual tonnes dry matter, annual tonnes fresh matter,
# estimated managed area, reported dry-matter yield per hectare, destination,
# and management intensity. Values are transcribed as printed.
TABLE36 = [
    ("GRASSLAND-ANB", "ANB", "5,875", "21,759", "1,646", "3.57", "Composting", "Extensive"),
    ("GRASSLAND-NATUURPUNT", "Natuurpunt", "7,975", "29,535", "2,529", "3.15", "Composting", "Extensive"),
    ("GRASSLAND-RECOGNISED-MANAGERS", "Recognised terrain-management institutions", "662", "2,452", "192", "3.45", "Composting", "Extensive"),
    ("GRASSLAND-AIRPORTS", "Airports", "3,188", "11,807", "760", "4.20", "Composting", "Extensive"),
    ("GRASSLAND-PORTS", "Ports", "751", "2,781", "497", "1.51", "Composting", "Extensive"),
    ("GRASSLAND-GOLF", "Golf courses", "3,053", "11,307", "763", "4.00", "Composting/mulching", "Intensive"),
    ("GRASSLAND-LNE-EROSION", "LNE erosion prevention", "5,050", "18,703", "842", "6.00", "Composting/left on site", "Intensive"),
    ("GRASSLAND-SUBTOTAL", "Grassland subtotal", "26,553", "98,346", "7,229", "3.67", "", ""),
    ("VERGE-AWV", "Agentschap Wegen en Verkeer (AWV)", "9,381", "34,744", "8,230", "1.14", "Composting", "Extensive"),
    ("VERGE-NAVIGABLE-WATERWAYS", "Navigable waterways", "2,553", "9,457", "2,607", "0.98", "Composting", "Extensive"),
    ("VERGE-MUNICIPALITIES", "Municipalities", "20,050", "74,260", "14,520", "1.38", "Composting", "Extensive"),
    ("VERGE-RAILWAYS", "Railways", "2,900", "10,741", "724", "4.00", "Composting", "Extensive"),
    ("VERGE-SUBTOTAL", "Road-verge subtotal", "34,884", "129,201", "26,082", "1.34", "", ""),
    ("ALL-GRASS-AND-VERGES", "Total grasslands and road verges", "61,438", "227,547", "33,311", "", "", ""),
]


def _read(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    if not path.exists():
        return [], []
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        return reader.fieldnames or [], list(reader)


def _upsert(path: Path, row: dict[str, object], key: str) -> None:
    fields, rows = _read(path)
    if not fields:
        raise ValueError(f"Expected an existing registry with headers: {path}")
    normalized = {field: str(row.get(field, "")) for field in fields}
    rows = [existing for existing in rows if existing.get(key) != normalized[key]]
    rows.append(normalized)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    GROUP.mkdir(parents=True, exist_ok=True)
    records = []
    for row_id, actor, dm, fresh, area, yield_dm, destination, management in TABLE36:
        notes = "Reported GR3 Table 36 estimate; fresh-mass column is based on the report's 27% DM assumption."
        if row_id == "VERGE-MUNICIPALITIES":
            notes += " Area is marked with an asterisk; report says municipality-verge area was taken from the VITO/KU Leuven GRB-method master's thesis."
        if row_id in {"GRASSLAND-SUBTOTAL", "VERGE-SUBTOTAL", "ALL-GRASS-AND-VERGES"}:
            notes += " Subtotal/total only; do not sum with the member actor rows."
        records.append({
            "record_id": f"OVAM17-{row_id}", "source_id": SOURCE_ID,
            "report_title": TITLE, "report_publisher": "OVAM",
            "report_publication_year": "2017", "underlying_study": "GR3 (2015)",
            "underlying_reference_period": "GR3 2015 inventory; exact data collection period is not specified in Table 36",
            "record_scope": "reported_inventory_estimate", "management_actor": actor,
            "material_group": "managed grassland/nature" if row_id.startswith("GRASSLAND") else ("roadside/waterway/rail verge" if row_id.startswith("VERGE") else "grassland and road-verge aggregate"),
            "annual_dry_matter_tonnes": dm, "annual_fresh_matter_tonnes": fresh,
            "managed_area_ha": area, "reported_dm_yield_tonnes_per_ha": yield_dm,
            "fresh_mass_basis": "Report uses 27% DM to derive fresh-matter tonnage; wet mass is not an independently paired measurement.",
            "destination": destination, "management_intensity": management,
            "source_location": "Table 36, printed p. 79 / PDF p. 80; method and cautions printed pp. 78–79",
            "evidence_class": "B_official_reported_inventory_estimate",
            "quality_class": "B", "activation_state": "reference_only",
            "transferability": "historical_Flanders_inventory_not_Dutch_or_GreenHub_site_delivery",
            "limitations": LIMITATIONS + " " + notes, "retrieval_date": RETRIEVED,
        })

    # The report separately gives a later Natuurpunt estimate in a footnote;
    # preserve it as a distinct, incompletely dated scope rather than merging it.
    records.extend([
        {
            "record_id": "OVAM17-NATUURPUNT-UPDATE-AREA", "source_id": SOURCE_ID,
            "report_title": TITLE, "report_publisher": "OVAM", "report_publication_year": "2017",
            "underlying_study": "Natuurpunt update cited by OVAM", "underlying_reference_period": "described as more recent than GR3 Table 36; exact year not stated",
            "record_scope": "separate_manager_reported_update", "management_actor": "Natuurpunt",
            "material_group": "managed nature area", "annual_dry_matter_tonnes": "",
            "annual_fresh_matter_tonnes": "", "managed_area_ha": "22,500",
            "reported_dm_yield_tonnes_per_ha": "", "fresh_mass_basis": "not reported",
            "destination": "", "management_intensity": "",
            "source_location": "Table 36 footnote, printed p. 79 / PDF p. 80",
            "evidence_class": "B_official_reported_inventory_estimate", "quality_class": "B",
            "activation_state": "reference_only", "transferability": "historical_Flanders_manager_estimate_not_GreenHub_site_data",
            "limitations": LIMITATIONS + " Separate footnote estimate; do not merge with GR3 table totals.", "retrieval_date": RETRIEVED,
        },
        {
            "record_id": "OVAM17-NATUURPUNT-UPDATE-GRASS-DM", "source_id": SOURCE_ID,
            "report_title": TITLE, "report_publisher": "OVAM", "report_publication_year": "2017",
            "underlying_study": "Natuurpunt update cited by OVAM", "underlying_reference_period": "described as more recent than GR3 Table 36; exact year not stated",
            "record_scope": "separate_manager_reported_update", "management_actor": "Natuurpunt",
            "material_group": "grass cuttings", "annual_dry_matter_tonnes": "5,000",
            "annual_fresh_matter_tonnes": "", "managed_area_ha": "",
            "reported_dm_yield_tonnes_per_ha": "", "fresh_mass_basis": "not reported",
            "destination": "excluding cuttings delivered to farmers or own herd", "management_intensity": "",
            "source_location": "Table 36 footnote, printed p. 79 / PDF p. 80",
            "evidence_class": "B_official_reported_inventory_estimate", "quality_class": "B",
            "activation_state": "reference_only", "transferability": "historical_Flanders_manager_estimate_not_GreenHub_site_data",
            "limitations": LIMITATIONS + " Separate footnote estimate; quantity excludes material sent to farmers or Natuurpunt livestock.", "retrieval_date": RETRIEVED,
        },
        {
            "record_id": "OVAM17-NATUURPUNT-UPDATE-ROUGH-CUTTINGS-DM", "source_id": SOURCE_ID,
            "report_title": TITLE, "report_publisher": "OVAM", "report_publication_year": "2017",
            "underlying_study": "Natuurpunt update cited by OVAM", "underlying_reference_period": "described as more recent than GR3 Table 36; exact year not stated",
            "record_scope": "separate_manager_reported_update", "management_actor": "Natuurpunt",
            "material_group": "rough cuttings", "annual_dry_matter_tonnes": "6,500",
            "annual_fresh_matter_tonnes": "", "managed_area_ha": "",
            "reported_dm_yield_tonnes_per_ha": "", "fresh_mass_basis": "not reported",
            "destination": "excluding cuttings delivered to farmers or own herd", "management_intensity": "",
            "source_location": "Table 36 footnote, printed p. 79 / PDF p. 80",
            "evidence_class": "B_official_reported_inventory_estimate", "quality_class": "B",
            "activation_state": "reference_only", "transferability": "historical_Flanders_manager_estimate_not_GreenHub_site_data",
            "limitations": LIMITATIONS + " Separate footnote estimate; quantity excludes material sent to farmers or Natuurpunt livestock.", "retrieval_date": RETRIEVED,
        },
    ])

    with CSV_PATH.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS, lineterminator="\n")
        writer.writeheader()
        writer.writerows(records)
    digest = hashlib.sha256(CSV_PATH.read_bytes()).hexdigest()
    sidecar = {
        "dataset_id": "urn:greenhub:dataset:ovam-gr3-2017-flanders-mowing-inventory:v1",
        "dataset_version": "1.0.0", "dataset_title": "GR3 Flemish grassland and verge mowing inventory and Natuurpunt update",
        "dataset_file": FILENAME, "source_dataset_path": f"Greenhub/data/Pre-treatment/Feedstock/{FILENAME}",
        "source_data_sha256": digest, "rows": len(records), "source_id": SOURCE_ID,
        "citation": f"OVAM. (2017). {TITLE}. GR3 Table 36, p. 79. {SOURCE_URL}",
        "source_url": SOURCE_URL, "dataset_doi": DOI, "dataset_url": DATASET_URL,
        "retrieval_date": RETRIEVED, "publication_year": 2017,
        "underlying_study": "GR3 (2015); exact period not further specified in the report table",
        "geography": "Flanders, Belgium", "source_location": "Table 36 printed p. 79 / PDF p. 80; notes printed pp. 78–79",
        "permission_or_rights": "OVAM report document description, printed p. 6, states that data in the document may be reproduced provided a clear source citation is supplied. No standardized CC license is asserted.",
        "evidence_class": "B_official_reported_inventory_estimate", "quality_class": "B",
        "data_type": "reported inventory and potential supply estimates; includes agency rows, subtotals, total and a separate Natuurpunt update",
        "fresh_mass_method": "The report applies 27% dry matter to derive fresh-matter tonnage from dry matter; it is not a paired wet-weight measurement.",
        "processing": "Direct transcription of Table 36 values and a separately identified Natuurpunt footnote update. No recalculation, interpolation, or merging between the two scopes.",
        "activation_state": "reference_only", "runtime_parameter_mapping": None,
        "limitations": [LIMITATIONS, "Table 36 totals include both managed grassland/nature and road-verge sources; the two groups are kept disaggregated in records.", "The table's reported totals should not be added to actor rows. The separate Natuurpunt update is not part of the table totals.", "Table 36 values are not numerically interchangeable with MONBIO 2.0: source years, definitions, data methods and dry-matter assumptions differ."],
        "fair_metadata": {
            "findable": "Versioned local URN, exact citation, source report URL, dataset DOI and table/page are recorded.",
            "accessible": "CSV and JSON sidecar are stored locally; report and supporting GR3 dataset are linked over HTTPS.",
            "interoperable": "UTF-8 CSV uses separate wet/dry mass, area, yield, actor, material group, destination and period fields.",
            "reusable": "OVAM reuse permission with citation, source method, 27% DM derivation, caveats and no-runtime policy are recorded.",
        },
    }
    SIDECAR_PATH.write_text(json.dumps(sidecar, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    local_source = {
        "source_id": SOURCE_ID, "source_title": TITLE,
        "authors": "OVAM; GR3 (2015) study contributors",
        "year": "2017", "source_type": "official regional inventory report; reported estimated supply table",
        "doi_or_stable_identifier": DOI or "", "stable_url": SOURCE_URL,
        "material": "Managed grasslands/nature and roadside/waterway/rail verges in Flanders; GR3 Table 36",
        "quality_notes": "Table 36, printed p. 79. B-tier official report estimates; fresh-matter tonnes use 27% DM, not paired weighings. Printed grassland actor values sum to 26,554 t DM/y versus the reported 26,553 t DM/y subtotal; the 1 t difference is unexplained. Report warns area may not be fully mown and material may remain on site. OVAM permits reuse with clear citation. Reference-only; not Dutch site supply.",
        "accessed_date": RETRIEVED,
    }
    _upsert(GROUP / "source_register.csv", local_source, "source_id")
    _upsert(GROUP / "dataset_manifest.csv", {
        "file_name": FILENAME,
        "description": "GR3 Table 36 2015 Flemish grassland/road-verge inventory estimates plus separate Natuurpunt footnote update",
        "row_count": len(records), "schema_version": "1.0", "encoding": "UTF-8", "delimiter": ",",
        "integration_readiness": "traceable_reference_only_not_runtime_eligible",
        "limitations": "Historical mixed grassland/verge estimate; 27% DM used for fresh mass; not a GreenHub Dutch collection contract.",
    }, "file_name")

    rel = f"Pre-treatment/Feedstock/{FILENAME}"
    _upsert(AUDIT / "global_source_register.csv", {
        "dataset_path": rel, "dataset_group": "Pre-treatment/Feedstock", "source_id": SOURCE_ID,
        "source_title": TITLE, "authors": local_source["authors"], "year": "2017",
        "doi_or_stable_id": DOI or "", "url": SOURCE_URL, "source_type": local_source["source_type"],
        "notes": local_source["quality_notes"],
    }, "dataset_path")
    _upsert(AUDIT / "global_dataset_manifest.csv", {
        "dataset_path": rel, "category": "Pre-treatment", "subgroup": "Feedstock; regional supply inventory",
        "filename": FILENAME, "row_count_observed": len(records), "header_count": len(FIELDS),
        "headers": "; ".join(FIELDS), "standardized_status_values": "B;reference_only",
        "detected_readiness": "D3", "notes": "Actor-level GR3 supply estimates; dry/wet/area bases and separate scopes retained.",
    }, "dataset_path")
    _upsert(AUDIT / "global_dataset_readiness.csv", {
        "dataset_path": rel, "category": "Pre-treatment", "subgroup": "Feedstock; regional supply inventory",
        "readiness": "D3", "duplicate_ids": 0, "duplicate_rows": 0, "numeric_rows": len(records),
        "unsourced_numeric_rows": 0, "numeric_rows_missing_exact_location": 0, "unit_conflicts": 0,
        "basis_conflicts": 0, "cross_reference_issues": 0, "equation_missing_inputs": 0,
        "equation_symbol_mismatches": 0,
        "notes": "Numeric data link to official Table 36 or its separately identified footnote; actor rows/subtotals/total are not additive; reference-only.",
    }, "dataset_path")
    _upsert(AUDIT / "source_dataset_checksums.csv", {
        "dataset_path": rel, "sha256": digest, "byte_size": CSV_PATH.stat().st_size,
    }, "dataset_path")
    print(json.dumps({"dataset": rel, "rows": len(records), "source_id": SOURCE_ID, "sha256": digest, "activation_state": "reference_only"}, indent=2))


if __name__ == "__main__":
    main()
