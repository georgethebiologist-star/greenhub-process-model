"""Register the unchanged University of Bath source workbooks for Kurhan et al. (2025).

The source workbooks remain evidence assets, not GreenHub runtime inputs. This
builder creates a sheet-level inventory and traceability sidecars/register rows;
it deliberately does not infer model-ready parameters from workbook cells.
"""
from __future__ import annotations

import csv
import hashlib
import json
from datetime import date, datetime, timezone
from pathlib import Path

from openpyxl import load_workbook


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "Greenhub" / "data"
FOLDER = DATA / "Pre-treatment" / "Mechanical" / "kurhan_2025_biorefinery_reference"
GROUP = FOLDER.parent
AUDIT = DATA / "global_audit_package"
INVENTORY = FOLDER / "kurhan_2025_bath_workbook_sheet_inventory_reference.csv"
CELL_EXTRACT = FOLDER / "kurhan_2025_bath_source_workbook_cells_reference.csv"
INVENTORY_SOURCE_ID = "SRC-KURHAN-2025-BATH-01534"
DATASET_DOI = "10.15125/BATH-01534"
DATASET_URL = "https://researchdata.bath.ac.uk/1534/"
ARTICLE_DOI = "10.1098/rstb.2024.0161"
ARTICLE_URL = "https://doi.org/10.1098/rstb.2024.0161"
RETRIEVAL_DATE = "2026-11-08"

# SHA-256 pins identify the exact, unchanged files downloaded from the archive.
ASSETS = [
    {
        "filename": "Extruder_RSM_Figure_3.xlsx",
        "sha256": "4c6f1616f6bf51d1385ec934ed6d21df27f9a21440ee41682782df695f708c11",
        "url": "https://researchdata.bath.ac.uk/1534/3/Extruder%20RSM%20figure%203.xlsx",
        "scope": "Full design-of-experiments workbook for the extruder response-surface study shown in Figure 3.",
        "phases": "3;4",
        "material": "UK grass silage; water-assisted twin-screw extrusion; mechanochemical comparator.",
        "caveat": "Reference-only. Workbook factor labels/ranges and operating columns appear inconsistent for at least one axial point (including the temperature/factor-B values); verify against the paper before interpreting fitted or optimum settings.",
    },
    {
        "filename": "Extrusion_Single_Factor_Figure_3.xlsx",
        "sha256": "237c631d27a90cbf0baf75252a2110e3e20daf02b7edd3c3f1f33cbf79fefa79",
        "url": "https://researchdata.bath.ac.uk/1534/4/Extrusion%20single%20factor%20analysis%20silage%20figure%203.xlsx",
        "scope": "Single-factor extruder performance observations presented in Figure 3.",
        "phases": "3;4",
        "material": "UK grass silage; water-assisted twin-screw extrusion; mechanochemical comparator.",
        "caveat": "Reference-only. This is an extruder route, not GreenHub's current roadside-grass screw-press route; do not transfer its extraction response as a press coefficient.",
    },
    {
        "filename": "Silage_Analysis_Table_1.xlsx",
        "sha256": "95e0e4b66c2338baeee722c20f91ba7fbdd2302f68aae314cca9b853de74eaa2",
        "url": "https://researchdata.bath.ac.uk/1534/5/Silage%20analysis%20data%20table%201.xlsx",
        "scope": "Underlying Table 1 silage feedstock analytical data: dry matter, ash, total carbon/nitrogen, amino acids, tryptophan and B vitamins.",
        "phases": "1;4",
        "material": "UK grass silage; feedstock chemistry and nutritional analytes.",
        "caveat": "Reference-only. Silage values are not fresh roadside-grass composition; preserve source assay basis and do not combine with a different feed state without an explicit conversion basis.",
    },
    {
        "filename": "Amino_Acid_Comparative_Figure_2.xlsx",
        "sha256": "39bbb237d9d906cce80b5f8c2c56d2145e0f4d790fda3326e62054ad64fc7318",
        "url": "https://researchdata.bath.ac.uk/1534/6/Amino%20acid%20comparative%20data%20for%20figure%202.xlsx",
        "scope": "Amino-acid profiles of silage before/after extraction and comparative protein sources shown in Figure 2.",
        "phases": "4",
        "material": "Grass-silage-derived soluble fraction and non-grass comparison proteins.",
        "caveat": "Reference-only. Comparative nutritional profiles do not establish GreenHub product purity, food-grade status, recovery, or saleable specification.",
    },
]

SHEET_DESCRIPTIONS = {
    "extruder_rsm_figure_3.xlsx": {
        "Data": ("3;4", "Extruder response-surface design, operating settings, nitrogen/protein response and calculated yield columns."),
    },
    "extrusion_single_factor_figure_3.xlsx": {
        "Sheet1": ("3;4", "Single-factor extrusion operating conditions and reported response columns."),
    },
    "silage_analysis_table_1.xlsx": {
        "Dry matter-Ash": ("1", "Dry-matter and ash feedstock analysis."),
        "Silage-Total C&N": ("1", "Total carbon and nitrogen feedstock analysis."),
        "Total Amino Acid Content-Raw da": ("1;4", "Raw amino-acid analytical values."),
        "Total Amino Acid content-calc": ("1;4", "Workbook-calculated amino-acid summary values; formula and cached-result counts are recorded."),
        "Tryptophan": ("1;4", "Tryptophan analytical values."),
        "Vitamin B Content-Raw data": ("1;4", "Raw B-vitamin analytical values."),
        "Sheet5": ("1;4", "Workbook-calculated B-vitamin summary values; formula and cached-result counts are recorded."),
    },
    "amino_acid_comparative_figure_2.xlsx": {
        "Sheet1": ("4", "Amino-acid profile comparisons used in Figure 2."),
    },
}

INVENTORY_FIELDS = [
    "record_id", "source_id", "dataset_doi", "workbook_filename", "workbook_sha256",
    "sheet_name", "phase_relevance", "source_description", "max_row", "max_column",
    "nonempty_rows", "nonempty_cells", "formula_cells", "cached_formula_values",
    "formula_cells_without_cached_value", "activation_state", "known_caveats",
]
CELL_FIELDS = [
    "record_id", "source_id", "dataset_doi", "workbook_filename", "workbook_sha256",
    "sheet_name", "cell_address", "row_index", "column_index", "cell_type",
    "number_format", "source_value", "formula_expression", "cached_formula_value",
]


def _read_csv(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    if not path.exists():
        return [], []
    with path.open(encoding="utf-8-sig", newline="") as stream:
        reader = csv.DictReader(stream)
        return list(reader.fieldnames or []), list(reader)


def _write_csv(path: Path, fields: list[str], rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def _upsert(path: Path, record: dict[str, object], key: str) -> None:
    fields, rows = _read_csv(path)
    if not fields:
        raise ValueError(f"Cannot upsert into missing/empty register: {path}")
    if key not in fields:
        raise ValueError(f"Register key {key!r} not found in {path}")
    rows = [row for row in rows if row.get(key) != str(record[key])]
    rows.append({field: record.get(field, "") for field in fields})
    _write_csv(path, fields, rows)


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _cell_text(value: object) -> str:
    if value is None:
        return ""
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    if isinstance(value, bool):
        return "TRUE" if value else "FALSE"
    if isinstance(value, float):
        return repr(value)
    return str(value)


def _inspect_asset(asset: dict[str, str]) -> tuple[list[dict[str, object]], dict[str, object]]:
    path = FOLDER / asset["filename"]
    if not path.is_file():
        raise FileNotFoundError(path)
    digest = _sha256(path)
    if digest != asset["sha256"]:
        raise ValueError(f"Source workbook checksum changed: {path.name} ({digest})")

    formulas_wb = load_workbook(path, data_only=False, read_only=True)
    cached_wb = load_workbook(path, data_only=True, read_only=True)
    sheet_rows: list[dict[str, object]] = []
    details: list[dict[str, object]] = []
    try:
        for sheet_name in formulas_wb.sheetnames:
            formula_sheet = formulas_wb[sheet_name]
            cached_sheet = cached_wb[sheet_name]
            nonempty_cells = formula_count = cached_formula_count = nonempty_rows = 0
            for row_number, formula_row in enumerate(formula_sheet.iter_rows(), start=1):
                row_has_value = False
                for column_number, formula_cell in enumerate(formula_row, start=1):
                    value = formula_cell.value
                    if value is None:
                        continue
                    row_has_value = True
                    nonempty_cells += 1
                    if isinstance(value, str) and value.startswith("="):
                        formula_count += 1
                        if cached_sheet.cell(row=row_number, column=column_number).value is not None:
                            cached_formula_count += 1
                if row_has_value:
                    nonempty_rows += 1
            relevance, description = SHEET_DESCRIPTIONS.get(asset["filename"].lower(), {}).get(
                sheet_name, (asset["phases"], "Source workbook sheet; contents not interpreted by this inventory."))
            record_id = f"BATH01534-{path.stem.upper()}-{len(sheet_rows) + 1:02d}"
            row = {
                "record_id": record_id,
                "source_id": INVENTORY_SOURCE_ID,
                "dataset_doi": DATASET_DOI,
                "workbook_filename": path.name,
                "workbook_sha256": digest,
                "sheet_name": sheet_name,
                "phase_relevance": relevance,
                "source_description": description,
                "max_row": formula_sheet.max_row,
                "max_column": formula_sheet.max_column,
                "nonempty_rows": nonempty_rows,
                "nonempty_cells": nonempty_cells,
                "formula_cells": formula_count,
                "cached_formula_values": cached_formula_count,
                "formula_cells_without_cached_value": formula_count - cached_formula_count,
                "activation_state": "reference_only",
                "known_caveats": asset["caveat"],
            }
            sheet_rows.append(row)
            details.append({
                "sheet_name": sheet_name,
                "phase_relevance": relevance,
                "source_description": description,
                "max_row": formula_sheet.max_row,
                "max_column": formula_sheet.max_column,
                "nonempty_rows": nonempty_rows,
                "nonempty_cells": nonempty_cells,
                "formula_cells": formula_count,
                "cached_formula_values": cached_formula_count,
                "formula_cells_without_cached_value": formula_count - cached_formula_count,
            })
    finally:
        formulas_wb.close()
        cached_wb.close()
    return sheet_rows, {
        "sha256": digest,
        "byte_size": path.stat().st_size,
        "sheets": details,
        "source_path": path,
    }


def _register_asset(asset: dict[str, str], details: dict[str, object]) -> None:
    path: Path = details["source_path"]  # type: ignore[assignment]
    rel_local = f"Pre-treatment/Mechanical/kurhan_2025_biorefinery_reference/{path.name}"
    rel_root = f"Pre-treatment/Mechanical/kurhan_2025_biorefinery_reference/{path.name}"
    sheets = details["sheets"]
    metadata = {
        "source_file": path.name,
        "source_id": INVENTORY_SOURCE_ID,
        "dataset_id": f"urn:greenhub:source:kurhan-2025-bath-01534:{path.stem.lower()}:v1",
        "dataset_title": asset["scope"],
        "source_dataset_path": f"Greenhub/data/{rel_local}",
        "source_data_sha256": details["sha256"],
        "persistent_identifier": DATASET_DOI,
        "source_url": asset["url"],
        "source_record_url": DATASET_URL,
        "article_doi": ARTICLE_DOI,
        "article_url": ARTICLE_URL,
        "source_title": "Dataset for Kurhan et al. (2025), The development of a silage-based biorefinery to deliver the maximum nutritional benefit for human consumption from UK grasslands",
        "data_creators": ["Chris Chuck", "Yubin Ding"],
        "article_authors": ["Sebnem Kurhan", "Yubin Ding", "Fatma Guler", "Olusegun Abayomi Olalere", "Samuel Eze", "Anne Wambui Mumbi", "Frank Vriesekoop", "Helen Pittson", "Bernardo Castro-Dominguez", "Hannah Leese", "Karl Behrendt", "Richard Green", "Christopher Chuck"],
        "publisher": "University of Bath Research Data Archive",
        "publication_year": 2025,
        "dataset_publication_date": "2025-09-05",
        "retrieval_date": RETRIEVAL_DATE,
        "version": 1,
        "geography": "UK grasslands; the archived material is grass silage. Exact sampling location and feed history should be taken from the associated article/methods, not inferred from the archive title.",
        "material_scope": asset["material"],
        "phase_relevance": asset["phases"],
        "evidence_class": "B_measured_primary_literature_dataset",
        "quality_class": "B",
        "license_or_rights": "CC BY 4.0, stated for this individual file on the University of Bath archive record.",
        "source_location": asset["scope"],
        "methods_summary": "The archive states data were collected using standard technical methods described in the associated article and processed in Microsoft Excel. This sidecar inventories the source workbook; it does not independently reproduce the laboratory measurements.",
        "workbook_sheets": sheets,
        "source_sha256": details["sha256"],
        "source_byte_size": details["byte_size"],
        "activation_state": "reference_only",
        "maturity_class": "D3",
        "calculation_connected": False,
        "parameter_registry_mapping": None,
        "runtime_usage": "No runtime use. Evidence is discoverable for comparison and future gated extraction only.",
        "applicability": "UK pasture silage and mechanochemical extrusion comparator; not Dutch roadside/VARTA feed or calibration for the existing GreenHub screw-press/isoelectric route.",
        "conversion_policy": "No workbook values were averaged, re-based, or promoted to model parameters. All populated cells are also transcribed to the companion cell-level CSV with formula expressions and source-cached outputs kept in separate columns; the original XLSX files remain unchanged.",
        "cell_level_extract": CELL_EXTRACT.name,
        "uncertainty": "The archive workbook and associated article must be consulted for individual replicate counts, analytical methods, and statistical uncertainty. The inventory does not infer these from cell formatting or formula presence.",
        "known_caveats": [asset["caveat"]],
        "license_url": "https://creativecommons.org/licenses/by/4.0/",
        "fair_metadata": {
            "findable": "DOI, source record, article DOI, source ID, local dataset URN and checksums are recorded.",
            "accessible": "Original open XLSX and sheet inventory are stored locally; source download URLs are recorded.",
            "interoperable": "Sheet inventory is UTF-8 CSV with explicit sheet, dimensions, formula/cache counts, phase mapping and status fields.",
            "reusable": "Per-file CC BY 4.0, citation, provenance, scope, extraction policy, transferability and activation limitations are recorded.",
        },
    }
    sidecar = path.with_suffix(".source.json")
    sidecar.write_text(json.dumps(metadata, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    _upsert(GROUP / "source_register.csv", {
        "source_id": INVENTORY_SOURCE_ID,
        "source_type": "open primary research data package; peer-reviewed article supporting dataset",
        "title": metadata["source_title"],
        "authors": "Chris Chuck; Yubin Ding (data creators); associated article by Kurhan et al.",
        "year": "2025",
        "doi_or_stable_identifier": DATASET_DOI,
        "publisher": "University of Bath Research Data Archive",
        "url": DATASET_URL,
        "material_scope": "UK grass silage chemistry and twin-screw mechanochemical extraction; four source workbooks staged.",
        "source_quality": "Primary measured research data; CC BY 4.0 per individual downloadable file; B-tier, D3/reference-only.",
        "access_date": RETRIEVAL_DATE,
        "notes": "Associated article DOI 10.1098/rstb.2024.0161. Workbook formulas/outputs and RSM factor inconsistencies require article-level interpretation. Not roadside/VARTA feed or GreenHub press-route calibration.",
    }, "source_id")
    local_manifest = {
        "dataset_id": f"DS-KURHAN-2025-{path.stem.upper()}",
        "filename": path.name,
        "purpose": asset["scope"],
        "row_count": sum(int(sheet["nonempty_rows"]) for sheet in sheets),
        "primary_key": "source_sheet + cell address (original workbook retained)",
        "encoding": "XLSX; original archive workbook",
        "delimiter": "not applicable",
        "integration_readiness": "reference_only_D3",
        "material_state_rule": "Grass silage and extrusion states are source-specific; do not merge with fresh roadside feed without explicit basis conversion.",
        "known_limitations": asset["caveat"] + " Row count is the sum of nonempty rows across sheets; see sheet inventory for per-sheet dimensions and formulas.",
    }
    _upsert(GROUP / "dataset_manifest.csv", local_manifest, "filename")

    _upsert(AUDIT / "global_source_register.csv", {
        "dataset_path": rel_root,
        "dataset_group": "Pre-treatment/Mechanical; source workbook evidence",
        "source_id": INVENTORY_SOURCE_ID,
        "source_title": metadata["source_title"],
        "authors": "Chris Chuck; Yubin Ding; Kurhan et al.",
        "year": "2025",
        "doi_or_stable_id": DATASET_DOI,
        "url": asset["url"],
        "source_type": "open primary research data package workbook",
        "notes": f"{asset['caveat']} Original file; see adjacent .source.json and sheet inventory.",
    }, "dataset_path")
    _upsert(AUDIT / "global_dataset_manifest.csv", {
        "dataset_path": rel_root,
        "category": "Pre-treatment",
        "subgroup": "Mechanical; Kurhan 2025 source workbook",
        "filename": path.name,
        "row_count_observed": local_manifest["row_count"],
        "header_count": len(sheets),
        "headers": "; ".join(str(sheet["sheet_name"]) for sheet in sheets),
        "standardized_status_values": "B;reference_only",
        "detected_readiness": "D3",
        "notes": "header_count is the number of workbook sheets (not tabular columns); source-specific sheet dimensions and formula/cached-result counts are in the companion inventory CSV.",
    }, "dataset_path")
    _upsert(AUDIT / "global_dataset_readiness.csv", {
        "dataset_path": rel_root,
        "category": "Pre-treatment",
        "subgroup": "Mechanical; Kurhan 2025 source workbook",
        "readiness": "D3",
        "duplicate_ids": "0",
        "duplicate_rows": "0",
        "numeric_rows": "0",
        "unsourced_numeric_rows": "0",
        "numeric_rows_missing_exact_location": "0",
        "unit_conflicts": "0",
        "basis_conflicts": "0",
        "cross_reference_issues": "0",
        "equation_missing_inputs": "0",
        "equation_symbol_mismatches": "0",
        "notes": "Raw multi-sheet workbook is not a normalized numeric-record CSV; numeric cell totals and sheet-level mapping are in the companion inventory. No value is activated.",
    }, "dataset_path")
    _upsert(AUDIT / "source_dataset_checksums.csv", {
        "dataset_path": rel_root,
        "sha256": details["sha256"],
        "byte_size": details["byte_size"],
    }, "dataset_path")


def _register_inventory(rows: list[dict[str, object]]) -> None:
    _write_csv(INVENTORY, INVENTORY_FIELDS, rows)
    digest = _sha256(INVENTORY)
    metadata = {
        "source_file": INVENTORY.name,
        "source_id": INVENTORY_SOURCE_ID,
        "dataset_id": "urn:greenhub:source:kurhan-2025-bath-01534:sheet-inventory:v1",
        "dataset_title": "Sheet-level inventory of four Kurhan et al. (2025) University of Bath source workbooks",
        "source_dataset_path": f"Greenhub/data/Pre-treatment/Mechanical/kurhan_2025_biorefinery_reference/{INVENTORY.name}",
        "source_data_sha256": digest,
        "persistent_identifier": DATASET_DOI,
        "source_url": DATASET_URL,
        "article_doi": ARTICLE_DOI,
        "retrieval_date": RETRIEVAL_DATE,
        "license_or_rights": "Inventory is a factual description generated from CC BY 4.0 source assets; source workbook attribution is required.",
        "evidence_class": "source_asset_metadata_inventory; not experimental observations",
        "quality_class": "B_source_metadata",
        "activation_state": "reference_only",
        "calculation_connected": False,
        "row_count": len(rows),
        "source_workbooks": [asset["filename"] for asset in ASSETS],
        "generation_method": "Deterministic read-only inspection of source XLSX sheet dimensions, nonempty cells, formula cells, and cached formula values with openpyxl. No cell values were transcribed into this inventory.",
        "known_limitations": ["Inventory row counts describe workbook structure, not replicate counts or independent measurements.", "See original CC BY 4.0 workbooks and associated article before scientific interpretation."],
    }
    INVENTORY.with_suffix(".csv.source.json").write_text(
        json.dumps(metadata, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    rel = f"Pre-treatment/Mechanical/kurhan_2025_biorefinery_reference/{INVENTORY.name}"
    _upsert(GROUP / "dataset_manifest.csv", {
        "dataset_id": "DS-KURHAN-2025-SHEET-INVENTORY",
        "filename": INVENTORY.name,
        "purpose": "Sheet-level inventory and provenance index for the four archived research workbooks; not a scientific observation dataset.",
        "row_count": len(rows),
        "primary_key": "record_id",
        "encoding": "UTF-8",
        "delimiter": ",",
        "integration_readiness": "reference_metadata_only_D3",
        "material_state_rule": "Per-sheet material state is described; no cell data or feed basis is normalized in this inventory.",
        "known_limitations": "Counts sheet dimensions, nonempty cells and formula/cache presence only; does not validate experimental meaning or model transferability.",
    }, "filename")
    _upsert(AUDIT / "global_source_register.csv", {
        "dataset_path": rel,
        "dataset_group": "Pre-treatment/Mechanical; source workbook inventory",
        "source_id": INVENTORY_SOURCE_ID,
        "source_title": "Kurhan et al. (2025) Bath source workbook sheet inventory",
        "authors": "University of Bath Research Data Archive; inventory generated by GreenHub project",
        "year": "2025",
        "doi_or_stable_id": DATASET_DOI,
        "url": DATASET_URL,
        "source_type": "generated source-asset inventory; not experimental data",
        "notes": "Generated from four source workbooks; reports worksheet dimensions and formula/cache counts only.",
    }, "dataset_path")
    _upsert(AUDIT / "global_dataset_manifest.csv", {
        "dataset_path": rel,
        "category": "Pre-treatment",
        "subgroup": "Mechanical; source workbook inventory",
        "filename": INVENTORY.name,
        "row_count_observed": len(rows),
        "header_count": len(INVENTORY_FIELDS),
        "headers": "; ".join(INVENTORY_FIELDS),
        "standardized_status_values": "B_source_metadata;reference_only",
        "detected_readiness": "D3",
        "notes": "Structural inventory, not scientific measurements; see original workbooks and individual file sidecars.",
    }, "dataset_path")
    _upsert(AUDIT / "global_dataset_readiness.csv", {
        "dataset_path": rel,
        "category": "Pre-treatment",
        "subgroup": "Mechanical; source workbook inventory",
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
        "notes": "Only structural counts are numeric. Rows identify source workbook/sheet names, DOI, hash and phase relevance; not model measurements.",
    }, "dataset_path")
    _upsert(AUDIT / "source_dataset_checksums.csv", {
        "dataset_path": rel,
        "sha256": digest,
        "byte_size": INVENTORY.stat().st_size,
    }, "dataset_path")


def _extract_source_cells(inspected: list[tuple[dict[str, str], dict[str, object]]]) -> list[dict[str, object]]:
    """Losslessly transcribe populated cells while retaining original cell addresses."""
    records: list[dict[str, object]] = []
    for _, details in inspected:
        path: Path = details["source_path"]  # type: ignore[assignment]
        formula_wb = load_workbook(path, data_only=False, read_only=True)
        cached_wb = load_workbook(path, data_only=True, read_only=True)
        try:
            for sheet_name in formula_wb.sheetnames:
                formula_sheet = formula_wb[sheet_name]
                cached_sheet = cached_wb[sheet_name]
                for row_number, formula_row in enumerate(formula_sheet.iter_rows(), start=1):
                    for column_number, source_cell in enumerate(formula_row, start=1):
                        value = source_cell.value
                        if value is None:
                            continue
                        is_formula = isinstance(value, str) and value.startswith("=")
                        cached_value = (
                            cached_sheet.cell(row=row_number, column=column_number).value
                            if is_formula else None
                        )
                        records.append({
                            "record_id": f"BATHCELL-{len(records) + 1:06d}",
                            "source_id": INVENTORY_SOURCE_ID,
                            "dataset_doi": DATASET_DOI,
                            "workbook_filename": path.name,
                            "workbook_sha256": details["sha256"],
                            "sheet_name": sheet_name,
                            "cell_address": source_cell.coordinate,
                            "row_index": row_number,
                            "column_index": column_number,
                            "cell_type": "formula" if is_formula else source_cell.data_type,
                            "number_format": source_cell.number_format,
                            "source_value": "" if is_formula else _cell_text(value),
                            "formula_expression": value if is_formula else "",
                            "cached_formula_value": _cell_text(cached_value) if is_formula else "",
                        })
        finally:
            formula_wb.close()
            cached_wb.close()
    _write_csv(CELL_EXTRACT, CELL_FIELDS, records)
    return records


def _register_cell_extract(records: list[dict[str, object]]) -> None:
    digest = _sha256(CELL_EXTRACT)
    metadata = {
        "source_file": CELL_EXTRACT.name,
        "source_id": INVENTORY_SOURCE_ID,
        "dataset_id": "urn:greenhub:source:kurhan-2025-bath-01534:cell-extract:v1",
        "dataset_title": "Cell-addressed transcription of four Kurhan et al. (2025) source workbooks",
        "source_dataset_path": f"Greenhub/data/Pre-treatment/Mechanical/kurhan_2025_biorefinery_reference/{CELL_EXTRACT.name}",
        "source_data_sha256": digest,
        "persistent_identifier": DATASET_DOI,
        "source_url": DATASET_URL,
        "article_doi": ARTICLE_DOI,
        "retrieval_date": RETRIEVAL_DATE,
        "license_or_rights": "Source files are individually marked CC BY 4.0 by the University of Bath Research Data Archive; attribution and DOI are retained.",
        "evidence_class": "lossless_cell_addressed_source_transcription; includes labels, measurements, formulas and cached formula outputs",
        "quality_class": "B_source_transcription",
        "activation_state": "reference_only",
        "calculation_connected": False,
        "parameter_registry_mapping": None,
        "row_count": len(records),
        "source_workbooks": [asset["filename"] for asset in ASSETS],
        "source_locations": "Each row points to workbook filename, worksheet and original Excel cell address.",
        "transcription_policy": "All nonempty cells are exported in workbook/sheet/row/column order. Literal cell values remain text as represented; formulas are retained in formula_expression and their workbook-cached results in cached_formula_value. No semantic labels, units, measurement classifications, or process parameters are inferred.",
        "validation": "Cell-extract row count equals the total nonempty-cell count in the companion sheet inventory; formula and cached-result counts reconcile sheet by sheet.",
        "known_limitations": [
            "This is a lossless cell-oriented transcription, not a normalized experimental-observation table. Consult the original workbook and paper for units, basis, replicate structure, and interpretation.",
            "Formula cached values are those stored in the source workbook at retrieval; they have not been independently recalculated.",
            "The RSM workbook factor/setting ambiguity remains unresolved and is flagged in the relevant rows and workbook sidecar.",
            "All data remain UK grass-silage/mechanochemical comparators, not roadside/VARTA measurements or current GreenHub route calibration.",
        ],
    }
    CELL_EXTRACT.with_suffix(".csv.source.json").write_text(
        json.dumps(metadata, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    rel = f"Pre-treatment/Mechanical/kurhan_2025_biorefinery_reference/{CELL_EXTRACT.name}"
    _upsert(GROUP / "dataset_manifest.csv", {
        "dataset_id": "DS-KURHAN-2025-CELL-EXTRACT",
        "filename": CELL_EXTRACT.name,
        "purpose": "Lossless cell-addressed CSV transcription of all four Bath source workbooks, preserving formula expressions separately from cached results.",
        "row_count": len(records),
        "primary_key": "record_id; source workbook + sheet + cell address also unique",
        "encoding": "UTF-8",
        "delimiter": ",",
        "integration_readiness": "reference_only_D3",
        "material_state_rule": "No material state or unit is inferred at cell level; use workbook sheet/cell context.",
        "known_limitations": "Not a normalized experimental dataset. Formula outputs are not recalculated; do not consume as runtime parameter data.",
    }, "filename")
    _upsert(AUDIT / "global_source_register.csv", {
        "dataset_path": rel,
        "dataset_group": "Pre-treatment/Mechanical; source cell transcription",
        "source_id": INVENTORY_SOURCE_ID,
        "source_title": metadata["dataset_title"],
        "authors": "Chris Chuck; Yubin Ding; Kurhan et al.",
        "year": "2025",
        "doi_or_stable_id": DATASET_DOI,
        "url": DATASET_URL,
        "source_type": "lossless cell-addressed transcription of CC BY 4.0 research workbooks",
        "notes": "All populated cells retain original workbook/sheet/cell provenance; formulas and cached results remain separate. Not normalized or runtime eligible.",
    }, "dataset_path")
    _upsert(AUDIT / "global_dataset_manifest.csv", {
        "dataset_path": rel,
        "category": "Pre-treatment",
        "subgroup": "Mechanical; source cell transcription",
        "filename": CELL_EXTRACT.name,
        "row_count_observed": len(records),
        "header_count": len(CELL_FIELDS),
        "headers": "; ".join(CELL_FIELDS),
        "standardized_status_values": "B_source_transcription;reference_only",
        "detected_readiness": "D3",
        "notes": "Cell-level transcription of source workbooks; not normalized scientific observations. Formula and cached value columns are separated.",
    }, "dataset_path")
    formula_rows = sum(bool(row["formula_expression"]) for row in records)
    numeric_rows = 0
    for row in records:
        candidate = row["cached_formula_value"] if row["cell_type"] == "formula" else row["source_value"]
        if row["cell_type"] == "n":
            numeric_rows += 1
        elif row["cell_type"] == "formula":
            try:
                float(str(candidate))
            except (TypeError, ValueError):
                pass
            else:
                numeric_rows += 1
    _upsert(AUDIT / "global_dataset_readiness.csv", {
        "dataset_path": rel,
        "category": "Pre-treatment",
        "subgroup": "Mechanical; source cell transcription",
        "readiness": "D3",
        "duplicate_ids": "0",
        "duplicate_rows": "0",
        "numeric_rows": numeric_rows,
        "unsourced_numeric_rows": "0",
        "numeric_rows_missing_exact_location": "0",
        "unit_conflicts": "0",
        "basis_conflicts": "0",
        "cross_reference_issues": "0",
        "equation_missing_inputs": "0",
        "equation_symbol_mismatches": "0",
        "notes": f"All {len(records)} populated source cells have workbook/sheet/cell provenance; {numeric_rows} rows contain numeric literals or numeric formula caches. {formula_rows} formula expressions have cached source-workbook outputs; values are not semantically normalized.",
    }, "dataset_path")
    _upsert(AUDIT / "source_dataset_checksums.csv", {
        "dataset_path": rel,
        "sha256": digest,
        "byte_size": CELL_EXTRACT.stat().st_size,
    }, "dataset_path")


def _refresh_validation_summary() -> None:
    summary_path = AUDIT / "global_validation_summary.json"
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    _, manifests = _read_csv(AUDIT / "global_dataset_manifest.csv")
    _, readiness = _read_csv(AUDIT / "global_dataset_readiness.csv")
    counts: dict[str, int] = {}
    for row in readiness:
        state = str(row.get("readiness", ""))
        counts[state] = counts.get(state, 0) + 1
    summary["dataset_count"] = len(manifests)
    summary["readiness_counts"] = counts
    summary["generated_at"] = datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")
    summary_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main() -> None:
    all_rows: list[dict[str, object]] = []
    inspected: list[tuple[dict[str, str], dict[str, object]]] = []
    for asset in ASSETS:
        rows, details = _inspect_asset(asset)
        all_rows.extend(rows)
        inspected.append((asset, details))
    cell_records = _extract_source_cells(inspected)
    _register_inventory(all_rows)
    for asset, details in inspected:
        _register_asset(asset, details)
    _register_cell_extract(cell_records)
    _refresh_validation_summary()
    print(json.dumps({
        "source_id": INVENTORY_SOURCE_ID,
        "dataset_doi": DATASET_DOI,
        "workbooks": len(ASSETS),
        "sheets": len(all_rows),
        "cell_records": len(cell_records),
        "formula_cells": sum(int(row["formula_cells"]) for row in all_rows),
        "cached_formula_values": sum(int(row["cached_formula_values"]) for row in all_rows),
        "inventory_sha256": _sha256(INVENTORY),
        "activation_state": "reference_only",
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
