"""Register traceable FR0 fresh-perennial-ryegrass composition observations.

This is a reference-only literature comparator. It does not edit the active
feed profile; the profile's two literature-linked mappings are reviewed and
maintained separately so changes cannot silently bypass user inputs.
"""
from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "Greenhub" / "data"
FEED = DATA / "Pre-treatment" / "Feedstock"
AUDIT = DATA / "global_audit_package"
FILENAME = "fresh_ryegrass_composition_della_rosa_2022_reference.csv"
RELATIVE_PATH = f"Pre-treatment/Feedstock/{FILENAME}"
SOURCE_ID = "SRC-DELLAROSA-2022-RYEGRASS-COMPOSITION"
TITLE = (
    "Substituting ryegrass-based pasture with graded levels of forage rape in the diet of lambs "
    "decreases methane emissions and increases propionate, succinate, and primary alcohols in the rumen"
)
DOI = "10.1093/jas/skac223"
URL = f"https://doi.org/{DOI}"
AUTHORS = "Maria M. Della Rosa; Edgar Sandoval; Peter Reid; Dongwen Luo; David Pacheco; Peter H. Janssen; Arjan Jonker"
LICENSE = "Creative Commons Attribution 4.0 International (CC BY 4.0)"
RETRIEVAL_DATE = "2026-11-09"

FIELDS = [
    "observation_id", "source_id", "feedstock", "material_state", "ryegrass_fraction_pct",
    "parameter", "value", "standard_deviation", "unit", "basis", "geography",
    "sampling_period", "sample_replicates", "data_status", "method_or_calculation",
    "source_location", "evidence_class", "activation_state", "transferability",
    "applicability", "limitations",
]

COMMON_LIMITATION = (
    "Fresh cultivated New Zealand perennial ryegrass comparator, not roadside grass or the matched VARTA batch; "
    "composition-table replicate count is not stated; transfer uncertainty to GreenHub is unquantified."
)

OBSERVATIONS = [
    ("DM", "Dry matter", "145", "15", "g/kg fresh matter", "as received", "reported_mean_sd", "Oven-dried at 105 °C for 24 h; triplicate subsamples", "Table 1, FR0 column; Methods, Forage offered"),
    ("ASH", "Ash", "117", "3", "g/kg DM", "dry matter", "reported_mean_sd", "AOAC 942.05", "Table 1, FR0 column; Forage analysis"),
    ("CP", "Crude protein", "233", "11", "g/kg DM", "dry matter; N × 6.25", "reported_mean_sd", "AOAC 968.06; nitrogen multiplied by 6.25", "Table 1, FR0 column; Forage analysis"),
    ("CFAT", "Crude fat", "41", "3", "g/kg DM", "dry matter; operational crude-fat extract", "reported_mean_sd", "AOAC method code printed as 930.15; retained as printed and flagged for verification", "Table 1, FR0 column; Forage analysis"),
    ("NFC", "Non-fiber carbohydrates", "175", "24", "g/kg DM", "dry matter; author-calculated", "author_calculated", "100 − (crude protein + ash + crude fat + NDF); not an independent assay", "Table 1 footnote 2, FR0 column"),
    ("SUGARS", "Soluble sugars", "89", "17", "g/kg DM", "dry matter", "reported_mean_sd", "Extracted with ethanol:water (80:20); anthrone colorimetric method", "Table 1, FR0 column; Forage analysis"),
    ("NDF", "Neutral detergent fibre", "439", "13", "g/kg DM", "dry matter; residual ash included", "reported_mean_sd", "Van Soest et al. (1991)", "Table 1, FR0 column; Forage analysis"),
    ("ADF", "Acid detergent fibre", "236", "5", "g/kg DM", "dry matter; residual ash included", "reported_mean_sd", "Van Soest et al. (1991)", "Table 1, FR0 column; Forage analysis"),
    ("LIGNIN", "Lignin", "23", "3", "g/kg DM", "dry matter; residual ash included", "reported_mean_sd", "Van Soest et al. (1991)", "Table 1, FR0 column; Forage analysis"),
    ("NITRATE_N", "Nitrate nitrogen", "618", "155", "mg/kg DM", "dry matter; nitrogen mass, not nitrate-ion mass", "reported_mean_sd", "Cataldo et al. (1975) salicylic-acid colorimetric method", "Table 1, FR0 column; Forage analysis"),
    ("PECTIN", "Pectin (homogalacturonan)", "10", "0.6", "g/kg DM", "dry matter; homogalacturonan operationally defined as pectin", "reported_mean_sd", "Uronic-acid quantification following Blumenkrantz and Asboe-Hansen (1973)", "Table 1, FR0 column; Forage analysis"),
    ("INDF", "Indigestible NDF", "94", "2.7", "g/kg DM", "dry matter", "reported_mean_sd", "12-day in-situ rumen incubation; Huhtanen et al. (1994)", "Table 1, FR0 column; Methods, fecal samples and iNDF"),
    ("PDNDF", "Potentially digestible NDF", "338", "16.1", "g/kg DM", "dry matter; author-calculated", "author_calculated", "NDF − iNDF; not an independent assay", "Table 1 footnote 2, FR0 column"),
    ("P", "Phosphorus", "5.0", "0.18", "g/kg DM", "dry matter", "reported_mean_sd", "Mineral analysis following AOAC procedures", "Table 1, FR0 column; Forage analysis"),
    ("K", "Potassium", "44.1", "1.31", "g/kg DM", "dry matter", "reported_mean_sd", "Mineral analysis following AOAC procedures", "Table 1, FR0 column; Forage analysis"),
    ("S", "Sulfur", "4.1", "0.04", "g/kg DM", "dry matter", "reported_mean_sd", "Mineral analysis following AOAC procedures", "Table 1, FR0 column; Forage analysis"),
    ("CA", "Calcium", "5.2", "0.14", "g/kg DM", "dry matter", "reported_mean_sd", "Mineral analysis following AOAC procedures", "Table 1, FR0 column; Forage analysis"),
    ("MG", "Magnesium", "2.1", "0.05", "g/kg DM", "dry matter", "reported_mean_sd", "Mineral analysis following AOAC procedures", "Table 1, FR0 column; Forage analysis"),
    ("NA", "Sodium", "1.2", "0.06", "g/kg DM", "dry matter", "reported_mean_sd", "Mineral analysis following AOAC procedures", "Table 1, FR0 column; Forage analysis"),
    ("CL", "Chloride", "20.3", "0.84", "g/kg DM", "dry matter", "reported_mean_sd", "Mineral analysis following AOAC procedures", "Table 1, FR0 column; Forage analysis"),
    ("CO", "Cobalt", "36.1", "0.01", "µg/kg DM", "dry matter", "reported_mean_sd", "ICP-MS after nitric-acid/hydrogen-peroxide digestion", "Table 1, FR0 column; Forage analysis"),
]


def read_csv(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    if not path.exists():
        return [], []
    with path.open(encoding="utf-8-sig", newline="") as stream:
        reader = csv.DictReader(stream)
        return list(reader.fieldnames or []), list(reader)


def write_csv(path: Path, fields: list[str], rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def upsert(path: Path, key_fields: tuple[str, ...], entry: dict[str, object]) -> None:
    fields, rows = read_csv(path)
    if not fields or any(key not in fields for key in key_fields):
        raise ValueError(f"Unexpected or missing CSV schema in {path}")
    key = tuple(str(entry.get(field, "")) for field in key_fields)
    rows = [row for row in rows if tuple(row.get(field, "") for field in key_fields) != key]
    rows.append({field: entry.get(field, "") for field in fields})
    write_csv(path, fields, rows)


def main() -> None:
    dataset_path = FEED / FILENAME
    rows: list[dict[str, object]] = []
    for suffix, parameter, value, sd, unit, basis, status, method, location in OBSERVATIONS:
        rows.append({
            "observation_id": f"DR22-FR0-{suffix}",
            "source_id": SOURCE_ID,
            "feedstock": "Perennial ryegrass (Lolium perenne cv. Ceres 150), FR0 treatment (100% ryegrass)",
            "material_state": "fresh forage; vegetative growth stage",
            "ryegrass_fraction_pct": "100",
            "parameter": parameter,
            "value": value,
            "standard_deviation": sd,
            "unit": unit,
            "basis": basis,
            "geography": "AgResearch Aorangi Farm, Palmerston North, New Zealand",
            "sampling_period": "July–August 2020",
            "sample_replicates": "Not stated for the Table 1 composition means; values reported as mean ± SD",
            "data_status": status,
            "method_or_calculation": method,
            "source_location": location,
            "evidence_class": "B_author_calculated" if status == "author_calculated" else "B_literature_measurement",
            "activation_state": "reference_only",
            "transferability": "proxy_low",
            "applicability": "Fresh cultivated ryegrass comparator; potential composition proxy only, not a Dutch roadside-grass result.",
            "limitations": COMMON_LIMITATION,
        })
    if len(rows) != 21 or len({str(row["observation_id"]) for row in rows}) != 21:
        raise ValueError("Expected 21 unique source-located FR0 observations")
    write_csv(dataset_path, FIELDS, rows)

    sidecar = {
        "dataset_file": FILENAME,
        "dataset_title": "Fresh perennial ryegrass feed composition (FR0) from Della Rosa et al. (2022), Table 1",
        "source_id": SOURCE_ID,
        "source_title": TITLE,
        "authors": AUTHORS,
        "publication_year": 2022,
        "doi": DOI,
        "source_url": URL,
        "license": LICENSE,
        "retrieval_date": RETRIEVAL_DATE,
        "source_location": "Table 1, FR0 (100% perennial ryegrass) column; printed p. 3; Methods, Forage analysis",
        "geography": "AgResearch Aorangi Farm, Palmerston North, New Zealand",
        "material_scope": "Fresh perennial ryegrass (Lolium perenne cv. Ceres 150), vegetative growth stage, sampled July–August 2020; the dataset contains the FR0 100% ryegrass column only.",
        "sample_design": "Daily forage was harvested and subsampled; samples were pooled within measurement batches as described by the article. Table 1 reports mean ± SD; the independent replicate count for the chemical-composition means is not stated.",
        "measurement_basis": "Reported source units and bases are preserved row-by-row. Dry-matter-basis values are not converted in this reference dataset.",
        "methods": "The paper reports dry matter by oven-drying at 105 °C for 24 h in triplicate; ash, crude protein and crude fat with cited AOAC methods; NDF/ADF/lignin using Van Soest et al. (1991); soluble sugars by ethanol:water extraction and anthrone; pectin as homogalacturonan using Blumenkrantz and Asboe-Hansen (1973); nitrate-N using Cataldo et al. (1975); cobalt by ICP-MS after nitric-acid/hydrogen-peroxide digestion. The crude-fat AOAC code is transcribed as printed in the article and should be verified before analytical-method equivalence is assumed.",
        "conversion_and_scaling": "Reference rows retain the reported mean and SD. The active GreenHub profile converts pectin and crude-fat proxy values to wet-basis mass fractions using the separately measured VARTA dry-matter fraction 0.143. It also converts the reported nitrate-N mean and SD to nitrate-ion mass with the NO3-/N molecular-weight ratio, then applies the same separate VARTA dry-matter fraction. These are explicit cross-source class-C assumptions, not matched sample measurements.",
        "uncertainty": "Within-study SD is reported. Composition-table replicate count and between-batch variation are not stated; transfer uncertainty from cultivated New Zealand ryegrass to Dutch roadside grass is unquantified.",
        "evidence_class": "B_literature_measurement; author-calculated values are identified per row",
        "activation_state": "reference_only as a source dataset; its nitrate-N row informs one separately derived class-C UI profile proxy",
        "related_technology_family_ids": ["pretreatment_fractionation", "protein_recovery", "anaerobic_digestion"],
        "data_scope": "material_or_site_specific",
        "limitations": [
            "The FR0 source material is cultivated New Zealand ryegrass, not roadside grass, GreenHub/VARTA feed, or a Dutch seasonal sample.",
            "The composition-table independent replicate count is not stated; mean ± SD is preserved without inventing n.",
            "NFC and potentially digestible NDF are author-calculated and are not independent measurements.",
            "Crude fat is an operational extract and is not chemically identical to a pure lipid pseudo-component.",
            "Nitrate-N is nitrogen mass and is converted to nitrate-ion mass only in the cited class-C proxy, using the explicit molecular-weight ratio.",
            "The nitrate-derived profile value is not a matched GreenHub measurement; the source dataset remains a cultivated-ryegrass comparator and does not validate project composition or close VARTA assay gaps.",
        ],
        "redistribution_note": "Open-access article states CC BY 4.0; cite the article and preserve source units, table location, and limitations.",
    }
    (FEED / (Path(FILENAME).stem + ".source.json")).write_text(
        json.dumps(sidecar, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )

    local_source = {
        "source_id": SOURCE_ID,
        "source_title": TITLE,
        "authors": AUTHORS,
        "year": "2022",
        "source_type": "peer_reviewed_primary_research_article_open_access",
        "doi_or_stable_identifier": DOI,
        "stable_url": URL,
        "material": "Fresh cultivated perennial ryegrass (Lolium perenne cv. Ceres 150), FR0 (100% ryegrass), Aorangi Farm, Palmerston North, New Zealand; sampled July–August 2020.",
        "quality_notes": "Table 1 source-located mean ± SD observations, CC BY 4.0. Composition-table n not stated; author-calculated NFC and pdNDF are labeled. FR0 is a cultivated-ryegrass comparator, not roadside grass or a VARTA measurement. The nitrate-N row informs a separate class-C UI profile proxy; it is not activated as a direct GreenHub measurement. Crude-fat method code is preserved as printed pending verification.",
        "accessed_date": RETRIEVAL_DATE,
    }
    upsert(FEED / "source_register.csv", ("source_id",), local_source)
    local_manifest = {
        "file_name": FILENAME,
        "description": "Source-located FR0 fresh-perennial-ryegrass composition means and standard deviations from Della Rosa et al. (2022), Table 1; one nitrate-N row informs a separate class-C UI profile proxy, while the source dataset remains a literature comparator.",
        "row_count": str(len(rows)),
        "schema_version": "1.0.0",
        "encoding": "UTF-8",
        "delimiter": ",",
        "integration_readiness": "source-traceable; one row informs a separate class-C UI proxy; source dataset remains reference-only",
        "limitations": "Cultivated New Zealand ryegrass, not roadside/VARTA feed. Means and SD retained; composition-table n is not stated. Derived NFC/pdNDF and the pectin, crude-fat, and nitrate wet-basis conversions are explicitly documented as proxies; the printed crude-fat method-code caveat remains.",
    }
    upsert(FEED / "dataset_manifest.csv", ("file_name",), local_manifest)

    digest = hashlib.sha256(dataset_path.read_bytes()).hexdigest()
    size = str(dataset_path.stat().st_size)
    statuses = "; ".join(sorted({str(row["data_status"]) for row in rows}))
    headers = "; ".join(FIELDS)
    upsert(AUDIT / "source_dataset_checksums.csv", ("dataset_path",), {
        "dataset_path": RELATIVE_PATH, "sha256": digest, "byte_size": size,
    })
    upsert(AUDIT / "global_dataset_manifest.csv", ("dataset_path",), {
        "dataset_path": RELATIVE_PATH, "category": "Pre-treatment", "subgroup": "Feedstock",
        "filename": FILENAME, "row_count_observed": str(len(rows)), "header_count": str(len(FIELDS)),
        "headers": headers, "standardized_status_values": statuses, "detected_readiness": "D3",
        "notes": "21 source-located FR0 composition rows; cultivated ryegrass comparator. Nitrate-N informs one separate class-C UI profile proxy; no row represents a matched roadside/VARTA measurement.",
    })
    upsert(AUDIT / "global_source_register.csv", ("dataset_path",), {
        "dataset_path": RELATIVE_PATH, "dataset_group": "Feedstock", "source_id": SOURCE_ID,
        "source_title": TITLE, "authors": AUTHORS, "year": "2022", "doi_or_stable_id": DOI,
        "url": URL, "source_type": "peer_reviewed_primary_research_article_open_access",
        "notes": f"CC BY 4.0; FR0 fresh ryegrass comparison; Table 1, printed p. 3; retrieved {RETRIEVAL_DATE}; not roadside/VARTA.",
    })
    upsert(AUDIT / "global_dataset_readiness.csv", ("dataset_path",), {
        "dataset_path": RELATIVE_PATH, "category": "Pre-treatment", "subgroup": "Feedstock", "readiness": "D3",
        "duplicate_ids": "0", "duplicate_rows": "0", "numeric_rows": str(len(rows)),
        "unsourced_numeric_rows": "0", "numeric_rows_missing_exact_location": "0", "unit_conflicts": "0",
        "basis_conflicts": "0", "cross_reference_issues": "0", "equation_missing_inputs": "0",
        "equation_symbol_mismatches": "0", "notes": "All 21 values have a DOI, table locator, basis, and reference-only status; composition-table n not stated.",
    })
    upsert(AUDIT / "dataset_activation_matrix.csv", ("dataset_path",), {
        "dataset_path": RELATIVE_PATH, "category": "Pre-treatment", "subgroup": "Feedstock",
        "audit_readiness": "D3", "integration_eligibility": "reference_only", "default_eligibility": "False",
        "calculation_connected": "False", "active": "False", "source_issue_count": "0",
        "quarantine_row_count": "0", "issue_types": "none", "cost_pathway_status": "not_applicable",
        "selection_reason": "Fresh cultivated ryegrass comparator, not GreenHub roadside/VARTA feed.",
        "required_action": "Keep reference-only; require matched roadside-grass assays before direct default activation.",
        "source_checksum_sha256": digest,
    })
    units_path = AUDIT / "global_unit_registry.csv"
    units_fields, unit_rows = read_csv(units_path)
    unit_rows = [row for row in unit_rows if row.get("dataset_path") != RELATIVE_PATH]
    unit_rows.extend({
        "dataset_path": RELATIVE_PATH, "dataset_group": "Feedstock", "column_name": "unit",
        "unit_text": str(row["unit"]), "status_standardized": str(row["data_status"]),
    } for row in rows)
    write_csv(units_path, units_fields, unit_rows)
    variable_path = AUDIT / "global_variable_dictionary.csv"
    variable_fields, variable_rows = read_csv(variable_path)
    variable_rows = [row for row in variable_rows if row.get("dataset_path") != RELATIVE_PATH]
    variable_rows.extend({
        "dataset_path": RELATIVE_PATH, "dataset_group": "Feedstock", "row_id": str(row["observation_id"]),
        "python_variable": "", "parameter_name": str(row["parameter"]), "numeric_column": "value",
        "original_value": str(row["value"]), "original_unit": str(row["unit"]),
        "normalized_si_value": "", "normalized_si_unit": "", "basis": str(row["basis"]),
        "status_original": str(row["data_status"]),
        "status_standardized": "author_calculated" if row["data_status"] == "author_calculated" else "literature_reported",
        "source_id": SOURCE_ID, "source_title": TITLE, "exact_location": str(row["source_location"]),
    } for row in rows)
    write_csv(variable_path, variable_fields, variable_rows)
    print(f"registered {len(rows)} source rows; reference-only; sha256={digest}")


if __name__ == "__main__":
    main()
