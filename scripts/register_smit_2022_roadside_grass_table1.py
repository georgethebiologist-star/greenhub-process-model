"""Register roadside-grass feedstock measurements transcribed from Smit et al. Table 1.

The records are literature comparators only. This script deliberately does not
change the feedstock defaults or any process-model inputs.
"""
from __future__ import annotations

import csv
import hashlib
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "Greenhub" / "data"
FOLDER = DATA / "Pre-treatment" / "Feedstock"
AUDIT = DATA / "global_audit_package"
FILENAME = "roadside_grass_composition_scientific.csv"
CSV_PATH = FOLDER / FILENAME
SOURCE_ID = "SRC-SMIT-2022"
TITLE = "Biomass Pre-Extraction as a Versatile Strategy to Improve Biorefinery Feedstock Flexibility, Sugar Yields, and Lignin Purity"
AUTHORS = (
    "Arjan T. Smit; André van Zomeren; Karla Dussan; Luke A. Riddell; "
    "Wouter J. J. Huijgen; Jan Wilco Dijkstra; Pieter C. A. Bruijnincx"
)
DOI = "10.1021/acssuschemeng.2c00838"
URL = f"https://doi.org/{DOI}"
PAPER_URL = "https://publications.tno.nl/publication/34639501/OO02n8/smit-2022-biomass.pdf"
RETRIEVED = "2026-11-08"


def _read(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    with path.open(encoding="utf-8-sig", newline="") as stream:
        reader = csv.DictReader(stream)
        return list(reader.fieldnames or []), list(reader)


def _write(path: Path, fields: list[str], rows: list[dict[str, str]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def _upsert(path: Path, key: str, entries: list[dict[str, str]]) -> None:
    fields, rows = _read(path)
    key_columns = key.split("|")
    indexed = {tuple(row.get(column, "") for column in key_columns): row for row in rows}
    for entry in entries:
        identity = tuple(entry.get(column, "") for column in key_columns)
        if identity in indexed:
            indexed[identity].update(entry)
        else:
            rows.append(entry)
            indexed[identity] = rows[-1]
    _write(path, fields or list(entries[0]), rows)


def _record(
    parameter_id: str,
    name: str,
    symbol: str,
    value: str,
    source_unit: str,
    normalized_value: str,
    normalized_unit: str,
    *,
    method: str = "Direct transcription from Table 1",
    equation: str = "",
    inputs: str = "",
    calculation: str = "No conversion",
    status: str = "reported",
    directness: str = "direct",
    note: str = "",
) -> dict[str, str]:
    dry_basis_caveat = (
        "Table 1 reports % w/w; the article describes feedstock composition as dry basis in Figure 2. "
        "Dry-basis normalization follows that section-level basis; Table 1 does not restate it row-by-row."
    )
    return {
        "dataset_id": "RG_COMP_V1",
        "parameter_id": parameter_id,
        "parameter_name": name,
        "symbol": symbol,
        "value_original": value,
        "unit_original": source_unit,
        "value_si": normalized_value,
        "unit_si": normalized_unit,
        "value_min": "",
        "value_max": "",
        "uncertainty_type": "not_reported_in_table",
        "uncertainty_value": "",
        "material_or_equipment": "Untreated roadside grass",
        "feedstock": "Roadside grass (study sample; location and sampling season not specified in Table 1)",
        "system_type": "Solid biomass / biorefinery",
        "scale": "Laboratory feedstock characterization",
        "operating_conditions": "Untreated feedstock; before aqueous-acetone pre-extraction",
        "measurement_method": method,
        "equation_id": "",
        "equation": equation,
        "calculation_inputs": inputs,
        "calculation_method": calculation,
        "source_type": "Peer-reviewed experimental study",
        "source_title": TITLE,
        "authors": AUTHORS,
        "year": "2022",
        "journal_or_publisher": "ACS Sustainable Chemistry & Engineering 10(18):6012–6022",
        "doi": DOI,
        "url": PAPER_URL,
        "page_table_figure": "Table 1; Results, Feedstock Selection and Composition; Figure 2 basis note",
        "evidence_status": status,
        "evidence_quality": "high",
        "direct_or_indirect": directness,
        "applicability_note": (
            "Direct roadside-grass comparator measured for an organosolv biorefinery study; "
            "not Dutch GreenHub/VARTA feedstock and not a seasonal or site-representative mean."
        ),
        "limitation_note": (
            "Table 1 provides no row-level uncertainty or exact sample location/season. "
            + dry_basis_caveat
            + " Do not use as a GreenHub default or add overlapping extractive/protein pools."
        ),
        "notes": "Reference-only; no runtime activation. " + note,
    }


def _records() -> list[dict[str, str]]:
    records = [
        _record("water_soluble_extractives", "Water-soluble organic extractives", "Extractives_water", "1.5", "% w/w", "0.015", "kg/kg dry matter", note="Table reports water-soluble organic extractives; do not equate to total soluble sugars."),
        _record("solvent_soluble_extractives", "Solvent-soluble organic extractives", "Extractives_acetone", "1.8", "% w/w", "0.018", "kg/kg dry matter", note="Source extraction pool; acetone-soluble, not a GreenHub pretreatment yield."),
        _record("solid_cellulose", "Cellulose (reported as glucan)", "Glucan", "34.4", "% w/w", "0.344", "kg/kg dry matter", note="Source analyte is glucan; retained as glucan-based cellulose characterization."),
        _record(
            "solid_hemicellulose", "Hemicellulose (sum of reported polymeric sugars)", "Hemicellulose",
            "24.0", "% w/w", "0.240", "kg/kg dry matter", method="Derived by transparent summation of Table 1 analytes",
            equation="xylan + arabinan + galactan + mannan + rhamnan",
            inputs="19.4 + 3.3 + 1.2 + 0.0 + 0.1 (% w/w)",
            calculation="Sum of the five directly reported polymeric hemicellulose sugar rows; no additional factor.",
            status="derived_from_reported_values", directness="derived_from_direct",
            note="A derived total, not an independently measured Table 1 row; component rows are retained separately.",
        ),
        _record("xylan", "Xylan", "Xylan", "19.4", "% w/w", "0.194", "kg/kg dry matter", note="Direct Table 1 polymeric sugar component."),
        _record("arabinan", "Arabinan", "Arabinan", "3.3", "% w/w", "0.033", "kg/kg dry matter", note="Direct Table 1 polymeric sugar component."),
        _record("galactan", "Galactan", "Galactan", "1.2", "% w/w", "0.012", "kg/kg dry matter", note="Direct Table 1 polymeric sugar component."),
        _record("mannan", "Mannan", "Mannan", "0.0", "% w/w", "0.000", "kg/kg dry matter", note="Source-reported zero; not a missing value."),
        _record("rhamnan", "Rhamnan", "Rhamnan", "0.1", "% w/w", "0.001", "kg/kg dry matter", note="Direct Table 1 polymeric sugar component."),
        _record("solid_lignin", "Total lignin (AIL + ASL)", "AIL+ASL", "16.9", "% w/w", "0.169", "kg/kg dry matter", note="Acid-insoluble lignin plus acid-soluble lignin, as reported."),
        _record("fresh_ash", "Ash", "Ash", "4.2", "% w/w", "0.042", "kg/kg dry matter", note="Separate measured roadside-grass comparator; do not replace the existing Brown et al. observation."),
        _record(
            "liquor_absorbing_capacity", "Liquor absorbing capacity", "LAC", "4.0", "g/g feed", "4.0", "g/g feed",
            note="Table 1 reports a feed-normalized absorption capacity; feed moisture/conditioning basis is not fully stated.",
        ),
        _record(
            "acid_neutralizing_capacity", "Acid-neutralizing capacity", "ANC", "0.31", "mmol H+/g feed", "0.31", "mmol H+/g feed",
            note="Table 1 characterization, not a GreenHub acid dose or process neutralization requirement.",
        ),
    ]
    return records


def main() -> None:
    fields, existing = _read(CSV_PATH)
    records = _records()
    keys = {(row.get("dataset_id", ""), row.get("parameter_id", ""), row.get("source_title", "")) for row in existing}
    for row in records:
        key = (row["dataset_id"], row["parameter_id"], row["source_title"])
        if key not in keys:
            existing.append(row)
            keys.add(key)
    _write(CSV_PATH, fields, existing)
    digest = hashlib.sha256(CSV_PATH.read_bytes()).hexdigest()

    source_register_path = FOLDER / "source_register.csv"
    _upsert(source_register_path, "source_id", [{
        "source_id": SOURCE_ID, "source_title": TITLE, "authors": AUTHORS, "year": "2022",
        "source_type": "peer-reviewed open-access experimental article", "doi_or_stable_identifier": DOI,
        "stable_url": URL, "material": "Roadside-grass composition; study location and season not specified in Table 1",
        "quality_notes": "Table 1 roadside-grass organic extractives, polymeric sugars, lignin, ash, liquor absorption and acid-neutralizing capacity; Phase 1 and 3 comparator. No row-level uncertainty or exact sample location/season. Table 1 gives % w/w while the composition section identifies dry basis in Figure 2; normalized basis is an explicit interpretation. Extractive/protein/sugar pools may overlap. CC BY 4.0. Reference-only; no GreenHub default or runtime activation.",
        "accessed_date": RETRIEVED,
    }])
    source_fields, source_rows = _read(source_register_path)
    source_digest = hashlib.sha256(source_register_path.read_bytes()).hexdigest()
    _upsert(FOLDER / "dataset_manifest.csv", "file_name", [{
        "file_name": "source_register.csv",
        "description": "Local bibliographic and dataset provenance register for staged Phase 1–7 evidence.",
        "row_count": str(len(source_rows)), "schema_version": "1.0", "encoding": "UTF-8", "delimiter": ",",
        "integration_readiness": "source-traceable; reference-only evidence",
        "limitations": "Some sources have no DOI or reuse license. Keep article and dataset identifiers distinct; two pre-existing Zuid-Holland citation duplicates are retained.",
    }])
    _upsert(FOLDER / "dataset_manifest.csv", "file_name", [{
        "file_name": FILENAME,
        "description": "Mixed-source roadside-grass composition and physical-property evidence; includes direct Smit et al. Table 1 comparator observations and explicit missing fields.",
        "row_count": str(len(existing)), "schema_version": "1.0",
        "encoding": "UTF-8", "delimiter": ",",
        "integration_readiness": "reference_only; D1 audit gate remains blocked",
        "limitations": "Multiple feedstock studies and analytical bases; Smit values are comparator-only and do not replace GreenHub feed measurements or defaults.",
    }])

    rel = f"Pre-treatment/Feedstock/{FILENAME}"
    _upsert(AUDIT / "global_source_register.csv", "dataset_path|source_id", [{
        "dataset_path": "Pre-treatment/Feedstock/source_register.csv", "dataset_group": "Feedstock",
        "source_id": SOURCE_ID, "source_title": TITLE, "authors": AUTHORS, "year": "2022",
        "doi_or_stable_id": DOI, "url": URL,
        "source_type": "peer-reviewed open-access experimental article",
        "notes": "Table 1 adds roadside-grass extractive fractions, glucan/hemicellulose components, lignin, ash, liquor absorption and acid-neutralizing capacity; source location/season and row uncertainty are unreported. CC BY 4.0. Comparator-only; no default or runtime activation.",
    }])
    _upsert(AUDIT / "global_dataset_manifest.csv", "dataset_path", [{
        "dataset_path": rel, "category": "Pre-treatment", "subgroup": "Feedstock",
        "filename": FILENAME, "row_count_observed": str(len(existing)), "header_count": str(len(fields)),
        "headers": "; ".join(fields), "standardized_status_values": "reported; derived_from_reported_values; missing",
        "detected_readiness": "D1",
        "notes": "Updated for 13 additional Table 1 records from Smit et al. (2022). Existing D1 identity/reference issues remain; evidence is reference-only and not a default.",
    }])
    source_register_rel = "Pre-treatment/Feedstock/source_register.csv"
    _upsert(AUDIT / "global_dataset_manifest.csv", "dataset_path", [{
        "dataset_path": source_register_rel, "category": "Pre-treatment", "subgroup": "Feedstock",
        "filename": "source_register.csv", "row_count_observed": str(len(source_rows)),
        "header_count": str(len(source_fields)), "headers": "; ".join(source_fields),
        "detected_readiness": "D3",
        "notes": "Bibliographic metadata index; sources remain evidence-only unless separately activated after validation.",
    }])
    _upsert(AUDIT / "source_dataset_checksums.csv", "dataset_path", [{
        "dataset_path": rel, "sha256": digest, "byte_size": str(CSV_PATH.stat().st_size),
    }])
    _upsert(AUDIT / "source_dataset_checksums.csv", "dataset_path", [{
        "dataset_path": source_register_rel, "sha256": source_digest,
        "byte_size": str(source_register_path.stat().st_size),
    }])
    activation_path = AUDIT / "dataset_activation_matrix.csv"
    _upsert(activation_path, "dataset_path", [{"dataset_path": rel, "source_checksum_sha256": digest}])
    _upsert(activation_path, "dataset_path", [{
        "dataset_path": source_register_rel, "source_checksum_sha256": source_digest,
    }])

    print(f"rows={len(existing)} registered={len(records)} sha256={digest}")


if __name__ == "__main__":
    main()
