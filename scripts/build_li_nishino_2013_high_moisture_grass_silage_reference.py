"""Transcribe grass-only time-course measurements from Li & Nishino (2013).

This is a reference dataset, not a GreenHub storage model or a source of fitted
degradation rates. The paper's table-level standard errors and significance
markers are preserved as reported.
"""
from __future__ import annotations

import csv
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
FOLDER = ROOT / "Greenhub/data/storage"
CSV_PATH = FOLDER / "high_moisture_grass_silage_fermentation_li_nishino_2013_reference.csv"
SIDECAR_PATH = CSV_PATH.with_suffix(".source.json")
SOURCE_ID = "SRC-LI-NISHINO-HIGH-MOISTURE-GRASS-SILAGE-2013"
DOI = "10.5713/ajas.2013.13175"
DOI_URL = f"https://doi.org/{DOI}"
PDF_URL = "https://pdfs.semanticscholar.org/88f9/afac9640505395e009a5a816f05a7d62556f.pdf"
PMC_URL = "https://pmc.ncbi.nlm.nih.gov/articles/PMC4093406/"
TITLE = (
    "Effects of Ensiling Fermentation and Aerobic Deterioration on the Bacterial "
    "Community in Italian Ryegrass, Guinea Grass, and Whole-crop Maize Silages "
    "Stored at High Moisture Content"
)
AUTHORS = "Yanbing Li; Naoki Nishino"
RETRIEVED = "2026-11-08"

FIELDS = [
    "record_id", "species", "harvest_date", "maturity", "chop_length_mm",
    "sample_mass_g", "storage_stage", "anaerobic_storage_days",
    "aerobic_exposure_days", "storage_temperature", "metric", "value",
    "unit", "reported_value_with_significance_marker", "significance_marker",
    "reported_SE", "SE_scope", "aerobic_comparison_test", "replicate_context",
    "analytical_method_context", "source_id", "source_location", "quality_class",
    "evidence_class", "activation_state", "transferability", "notes",
]

OPENING_DAYS = [3, 7, 14, 28, 56, 120]
AIR_DAYS = [14, 28, 56, 120]
METRICS = {
    "dry_matter": "g/kg fresh material",
    "pH": "dimensionless",
    "lactic_acid": "g/kg dry matter",
    "acetic_acid": "g/kg dry matter",
    "propionic_acid": "g/kg dry matter",
    "2_3_butanediol": "g/kg dry matter",
    "butyric_acid": "g/kg dry matter",
    "ethanol": "g/kg dry matter",
}

# The value strings retain the superscript comparison letters from Tables 2–3.
# SE is the single row-level SE printed for that set of storage conditions.
SERIES = {
    "Italian ryegrass": {
        "harvest_date": "2009-05-19",
        "crop_maturity": "late heading; first growth",
        "pre_ensiled": {"dry_matter": "212", "pH": "5.86"},
        "opening_SE": {
            "dry_matter": "1.98", "pH": "0.05", "lactic_acid": "3.91",
            "acetic_acid": "1.46", "propionic_acid": "1.17",
            "2_3_butanediol": "3.68", "butyric_acid": "1.21", "ethanol": "1.92",
        },
        "air_SE": {
            "dry_matter": "7.89", "pH": "0.17", "lactic_acid": "4.48",
            "acetic_acid": "3.57", "propionic_acid": "4.45",
            "2_3_butanediol": "5.78", "butyric_acid": "5.28", "ethanol": "2.14",
        },
        "aerobic_test": {
            "dry_matter": ["NS", "NS", "NS", "NS"],
            "pH": ["**", "**", "NS", "NS"],
            "lactic_acid": ["**", "**", "NS", "NS"],
            "acetic_acid": ["NS", "NS", "*", "NS"],
            "propionic_acid": ["**", "NS", "*", "NS"],
            "2_3_butanediol": ["NS", "**", "NS", "NS"],
            "butyric_acid": ["NS", "**", "NS", "NS"],
            "ethanol": ["**", "**", "**", "**"],
        },
        "opening": {
            "dry_matter": ["186a", "182abc", "182abc", "183ab", "173c", "176bc"],
            "pH": ["5.54a", "5.47a", "5.04b", "4.97bc", "4.66d", "4.79cd"],
            "lactic_acid": ["8.66c", "21.4bc", "30.0ab", "40.0a", "39.6ab", "25.1abc"],
            "acetic_acid": ["6.16b", "5.19b", "4.44b", "6.11b", "6.91ab", "13.7a"],
            "propionic_acid": ["8.32a", "6.59ab", "4.91ab", "2.24b", "2.49b", "9.05a"],
            "2_3_butanediol": ["58.2b", "71.5ab", "67.0ab", "75.6ab", "64.3ab", "77.2a"],
            "butyric_acid": ["15.6b", "8.02b", "16.5b", "30.4a", "23.6ab", "36.7a"],
            "ethanol": ["27.7b", "39.8a", "34.7ab", "39.3a", "33.7ab", "29.6b"],
        },
        "air": {
            "dry_matter": ["189", "178", "175", "189"],
            "pH": ["6.72y", "7.05x", "4.73z", "4.81z"],
            "lactic_acid": ["8.91y", "6.68y", "47.6x", "26.7xy"],
            "acetic_acid": ["8.85xy", "6.22y", "11.7x", "13.8x"],
            "propionic_acid": ["17.2x", "4.03y", "11.8xy", "6.05y"],
            "2_3_butanediol": ["67.5xy", "12.8y", "80.7x", "68.3xy"],
            "butyric_acid": ["12.0y", "5.69y", "41.2x", "35.5x"],
            "ethanol": ["0.67y", "0.77y", "8.54x", "10.0x"],
        },
    },
    "Guinea grass": {
        "harvest_date": "2009-08-04",
        "crop_maturity": "late heading; first growth",
        "pre_ensiled": {"dry_matter": "170", "pH": "6.28"},
        "opening_SE": {
            "dry_matter": "2.40", "pH": "0.06", "lactic_acid": "1.15",
            "acetic_acid": "2.15", "propionic_acid": "0.90",
            "2_3_butanediol": "0.95", "butyric_acid": "19.4", "ethanol": "2.73",
        },
        "air_SE": {
            "dry_matter": "2.66", "pH": "0.06", "lactic_acid": "0.49",
            "acetic_acid": "5.77", "propionic_acid": "0.60",
            "2_3_butanediol": "7.29", "butyric_acid": "3.28", "ethanol": "1.73",
        },
        "aerobic_test": {
            "dry_matter": ["NS", "*", "*", "NS"],
            "pH": ["**", "**", "NS", "NS"],
            "lactic_acid": ["**", "**", "NS", "NS"],
            "acetic_acid": ["**", "**", "NS", "NS"],
            "propionic_acid": ["NS", "NS", "NS", "NS"],
            "2_3_butanediol": ["**", "*", "*", "*"],
            "butyric_acid": ["NS", "NS", "NS", "**"],
            "ethanol": ["*", "*", "*", "*"],
        },
        "opening": {
            "dry_matter": ["166a", "162ab", "167a", "152b", "153b", "151b"],
            "pH": ["5.96bc", "6.01bc", "5.58d", "6.67a", "6.19b", "5.80cd"],
            "lactic_acid": ["14.0a", "7.67bc", "11.2ab", "2.96cd", "1.34d", "2.96cd"],
            "acetic_acid": ["26.0c", "39.6b", "42.1b", "44.9b", "56.8a", "57.8a"],
            "propionic_acid": ["0.60a", "0.00a", "1.00a", "2.26a", "3.25a", "2.32a"],
            "2_3_butanediol": ["4.47", "4.35", "4.28", "3.91", "2.34", "6.21"],
            "butyric_acid": ["0.00b", "0.00b", "0.00b", "8.66a", "14.7a", "62.4c"],
            "ethanol": ["3.20b", "7.09ab", "7.48ab", "10.3ab", "18.9a", "18.9a"],
        },
        "air": {
            "dry_matter": ["166x", "162xy", "163x", "151y"],
            "pH": ["8.96x", "8.72x", "6.01y", "5.71z"],
            "lactic_acid": ["0.00", "0.42", "0.32", "1.53"],
            "acetic_acid": ["0.00y", "2.13y", "50.0x", "54.5x"],
            "propionic_acid": ["0.00", "0.00", "0.86", "1.63"],
            "2_3_butanediol": ["0.00y", "0.00y", "8.66x", "8.68x"],
            "butyric_acid": ["0.00y", "0.00y", "11.5x", "36.3x"],
            "ethanol": ["0.00y", "0.00y", "7.50x", "5.90x"],
        },
    },
}


def _split_reported_value(value: str) -> tuple[str, str]:
    index = len(value)
    while index and value[index - 1].isalpha():
        index -= 1
    return value[:index], value[index:]


def build_rows() -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for species, series in SERIES.items():
        species_key = "IR" if species == "Italian ryegrass" else "GG"
        common = {
            "species": species,
            "harvest_date": series["harvest_date"],
            "maturity": series["crop_maturity"],
            "chop_length_mm": "25",
            "sample_mass_g": "300",
            "storage_temperature": "Ambient; numeric temperature not reported",
            "replicate_context": "Three separately prepared silage bags per storage condition; chemical analyses performed in duplicate. The reported row-level SE is retained without reinterpreting its statistical nesting.",
            "analytical_method_context": "DM by oven drying at 60 °C for 48 h; pH and fermentation acids/alcohols from water extracts; source reports duplicate analyses.",
            "source_id": SOURCE_ID,
            "quality_class": "B",
            "evidence_class": "primary_peer_reviewed_experimental_article_table_transcription",
            "activation_state": "reference_only",
            "transferability": "cultivated_grass_silage_comparator_not_Dutch_roadside_or_GreenHub_feed",
            "notes": "No storage-loss fraction, elemental balance, protein-quality change, methane potential, or emissions are inferred from these concentration measurements. No time interpolation or kinetic fitting performed.",
        }
        for metric, value in series["pre_ensiled"].items():
            rows.append({
                **common,
                "record_id": f"LINI13-{species_key}-FRESH-{metric.upper()}",
                "storage_stage": "pre_ensiled_fresh_crop",
                "anaerobic_storage_days": "0",
                "aerobic_exposure_days": "0",
                "storage_temperature": "",
                "metric": metric,
                "value": value,
                "unit": METRICS[metric],
                "reported_value_with_significance_marker": value,
                "significance_marker": "",
                "reported_SE": "",
                "SE_scope": "No standard error reported for this Table 1 value",
                "aerobic_comparison_test": "",
                "replicate_context": "Chemical measurements reported as means of duplicate analyses; independent field replication is not reported for these pre-ensiled values.",
                "source_location": "Table 1",
            })
        for metric, unit in METRICS.items():
            for day_index, day in enumerate(OPENING_DAYS):
                reported = series["opening"][metric][day_index]
                value, marker = _split_reported_value(reported)
                rows.append({
                    **common,
                    "record_id": f"LINI13-{species_key}-OPEN-{day}D-{metric.upper()}",
                    "storage_stage": "anaerobic_silo_opening",
                    "anaerobic_storage_days": str(day),
                    "aerobic_exposure_days": "0",
                    "metric": metric,
                    "value": value,
                    "unit": unit,
                    "reported_value_with_significance_marker": reported,
                    "significance_marker": marker,
                    "reported_SE": series["opening_SE"][metric],
                    "SE_scope": "single row-level SE reported for the six anaerobic storage-duration means; not an observation-specific interval",
                    "aerobic_comparison_test": "",
                    "source_location": "Table 2" if species_key == "IR" else "Table 3",
                })
            for day_index, day in enumerate(AIR_DAYS):
                reported = series["air"][metric][day_index]
                value, marker = _split_reported_value(reported)
                rows.append({
                    **common,
                    "record_id": f"LINI13-{species_key}-AIR7-{day}D-{metric.upper()}",
                    "storage_stage": "after_7_day_aerobic_exposure",
                    "anaerobic_storage_days": str(day),
                    "aerobic_exposure_days": "7",
                    "metric": metric,
                    "value": value,
                    "unit": unit,
                    "reported_value_with_significance_marker": reported,
                    "significance_marker": marker,
                    "reported_SE": series["air_SE"][metric],
                    "SE_scope": "single row-level SE reported for the four post-exposure storage-age means; not an observation-specific interval",
                    "aerobic_comparison_test": series["aerobic_test"][metric][day_index],
                    "source_location": "Table 2" if species_key == "IR" else "Table 3",
                })
    return rows


def _write_csv(path: Path, rows: list[dict[str, str]], fields: list[str]) -> None:
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def _update_local_registers(count: int) -> None:
    source_path = FOLDER / "source_register.csv"
    with source_path.open(encoding="utf-8-sig", newline="") as stream:
        reader = csv.DictReader(stream)
        source_fields = list(reader.fieldnames or [])
        source_rows = list(reader)
    source = {
        "source_id": SOURCE_ID,
        "source_title": TITLE,
        "authors": AUTHORS,
        "year": "2013",
        "source_type": "peer-reviewed primary experimental article; selected grass-only Tables 2–3 transcription",
        "doi_or_stable_identifier": DOI,
        "stable_url": DOI_URL,
        "material": "Direct-cut, high-moisture Italian ryegrass and guinea grass silages; 3–120 d sealed storage and 7 d aerobic exposure at 25 °C",
        "quality_notes": "Table means and row-level SE transcribed with significance markers; triplicate silage bags and duplicate chemical analyses. Cultivated forage comparator, not Dutch roadside or GreenHub feed. No loss rate, kinetic fit, emissions, BMP, or protein-quality inference. WSC in Table 1 conflicts with the Results narrative and is intentionally excluded. No explicit reuse license identified; copyright notice states © 2013 by the journal.",
        "accessed_date": RETRIEVED,
    }
    existing = next((row for row in source_rows if row.get("source_id") == SOURCE_ID), None)
    if existing is None:
        source_rows.append(source)
    else:
        existing.update(source)
    _write_csv(source_path, source_rows, source_fields)

    manifest_path = FOLDER / "dataset_manifest.csv"
    with manifest_path.open(encoding="utf-8-sig", newline="") as stream:
        reader = csv.DictReader(stream)
        manifest_fields = list(reader.fieldnames or [])
        manifest_rows = list(reader)
    entry = {
        "filename": CSV_PATH.name,
        "description": "Grass-only pre-ensiling DM/pH plus anaerobic-storage fermentation chemistry and post-opening seven-day aerobic-exposure means; source-reported uncertainty and significance markers retained; reference-only.",
        "row_count": str(count),
        "schema_version": "1.0",
        "encoding": "UTF-8",
        "delimiter": ",",
        "integration_status": "traceable_reference_only_not_runtime_eligible",
        "primary_key": "record_id",
    }
    existing_entry = next((row for row in manifest_rows if row.get("filename") == CSV_PATH.name), None)
    if existing_entry is None:
        manifest_rows.append(entry)
    else:
        existing_entry.update(entry)
    _write_csv(manifest_path, manifest_rows, manifest_fields)


def _update_global_registers(count: int) -> None:
    audit = ROOT / "Greenhub/data/global_audit_package"
    relative_path = f"storage/{CSV_PATH.name}"
    source_path = audit / "global_source_register.csv"
    with source_path.open(encoding="utf-8-sig", newline="") as stream:
        reader = csv.DictReader(stream)
        source_fields = list(reader.fieldnames or [])
        source_rows = list(reader)
    source_record = {
        "dataset_path": relative_path,
        "dataset_group": "storage",
        "source_id": SOURCE_ID,
        "source_title": TITLE,
        "authors": AUTHORS,
        "year": "2013",
        "doi_or_stable_id": DOI,
        "url": DOI_URL,
        "source_type": "peer-reviewed primary experimental article; grass-only Tables 1–3 transcription",
        "notes": "164 source-located values for pre-ensiled DM/pH and grass-silage storage chemistry. Cultivated forage comparator; no kinetics or GreenHub parameter activation. WSC source discrepancy excluded; reuse rights not explicitly licensed.",
    }
    existing_source = next((row for row in source_rows if row.get("dataset_path") == relative_path), None)
    if existing_source is None:
        source_rows.append(source_record)
    else:
        existing_source.update(source_record)
    _write_csv(source_path, source_rows, source_fields)

    manifest_path = audit / "global_dataset_manifest.csv"
    with manifest_path.open(encoding="utf-8-sig", newline="") as stream:
        reader = csv.DictReader(stream)
        manifest_fields = list(reader.fieldnames or [])
        manifest_rows = list(reader)
    manifest_record = {
        "dataset_path": relative_path,
        "category": "storage",
        "subgroup": "storage",
        "filename": CSV_PATH.name,
        "row_count_observed": str(count),
        "header_count": str(len(FIELDS)),
        "headers": "; ".join(FIELDS),
        "standardized_status_values": "B;reference_only",
        "detected_readiness": "D3",
        "notes": "Grass-only pre-ensiling and storage chemistry; exact source tables and conditions recorded. Measured concentration series are not mass losses, emissions, or fitted kinetics.",
    }
    existing_manifest = next((row for row in manifest_rows if row.get("dataset_path") == relative_path), None)
    if existing_manifest is None:
        manifest_rows.append(manifest_record)
    else:
        existing_manifest.update(manifest_record)
    _write_csv(manifest_path, manifest_rows, manifest_fields)

    readiness_path = audit / "global_dataset_readiness.csv"
    with readiness_path.open(encoding="utf-8-sig", newline="") as stream:
        reader = csv.DictReader(stream)
        readiness_fields = list(reader.fieldnames or [])
        readiness_rows = list(reader)
    readiness_record = {
        "dataset_path": relative_path,
        "category": "storage",
        "subgroup": "storage",
        "readiness": "D3",
        "duplicate_ids": "0",
        "duplicate_rows": "0",
        "numeric_rows": str(count),
        "unsourced_numeric_rows": "0",
        "numeric_rows_missing_exact_location": "0",
        "unit_conflicts": "0",
        "basis_conflicts": "0",
        "cross_reference_issues": "0",
        "equation_missing_inputs": "0",
        "equation_symbol_mismatches": "0",
        "notes": "Source-located primary-literature values; reference-only and not calculation-connected. Source discrepancy and basis limitations are recorded in the sidecar.",
    }
    existing_readiness = next((row for row in readiness_rows if row.get("dataset_path") == relative_path), None)
    if existing_readiness is None:
        readiness_rows.append(readiness_record)
    else:
        existing_readiness.update(readiness_record)
    _write_csv(readiness_path, readiness_rows, readiness_fields)

    summary_path = audit / "global_validation_summary.json"
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    summary["dataset_count"] = len(manifest_rows)
    readiness_counts: dict[str, int] = {}
    for item in readiness_rows:
        value = item.get("readiness", "")
        readiness_counts[value] = readiness_counts.get(value, 0) + 1
    summary["readiness_counts"] = readiness_counts
    summary["generated_at"] = datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")
    summary_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main() -> None:
    rows = build_rows()
    _write_csv(CSV_PATH, rows, FIELDS)
    digest = hashlib.sha256(CSV_PATH.read_bytes()).hexdigest()
    metadata = {
        "dataset_id": "urn:greenhub:dataset:storage:li-nishino-2013-high-moisture-grass-silage:v1",
        "title": TITLE,
        "source_id": SOURCE_ID,
        "authors": ["Yanbing Li", "Naoki Nishino"],
        "publication_year": 2013,
        "journal": "Asian-Australasian Journal of Animal Sciences",
        "volume_issue_pages": "26(9), 1304–1312",
        "doi": DOI,
        "source_url": DOI_URL,
        "full_text_urls": [PDF_URL, PMC_URL],
        "geography": "Experimental field location is not asserted from the author affiliations; methods state harvest dates but the extracted report does not establish a Dutch or GreenHub collection location.",
        "retrieval_date": RETRIEVED,
        "source_location": "Tables 2–3, pp. 1306–1307; relevant methods pp. 1305–1306.",
        "methods_summary": "First-growth direct-cut forage harvested at late heading, chopped to approximately 25 mm, packed 300 g per laminated bag, vacuum sealed, no additives, triplicate bags, ambient storage for 3, 7, 14, 28, 56 or 120 d. For aerobic challenge, 150 g from 14-, 28-, 56- or 120-d silage was placed uncompacted in an uncovered 500-mL bottle and exposed to air for 7 d at 25 °C. DM dried at 60 °C for 48 h; fermentation chemistry from water extracts; chemical analyses in duplicate.",
        "license_or_rights": "No explicit open data-reuse license identified. The article states copyright © 2013 by Asian-Australasian Journal of Animal Sciences. This repository contains a limited factual transcription with citations, not the article or figures; review rights before external redistribution.",
        "evidence_class": "B-tier peer-reviewed primary experimental measurements; table transcription",
        "quality_class": "B",
        "activation_state": "reference_only",
        "calculation_connected": False,
        "row_count": len(rows),
        "sha256_csv": digest,
        "transcription_policy": "Italian ryegrass and guinea grass fresh-crop DM/pH from Table 1 and physicochemical rows from Tables 2–3 are transcribed. Values, row-level SE, comparison letters, and t-test markers are retained. No missing timepoints are interpolated and no kinetic parameters are estimated.",
        "limitations": [
            "This is cultivated forage silage, not roadside grass or VARTA/GreenHub feed. Transferability must be validated before parameter use.",
            "The study concerns high-moisture direct-cut silage; sealed storage was described as ambient without numeric temperature or a temperature time series.",
            "The reported measurements are concentrations and pH, not feed mass recovery, dry-matter loss, component inventories, leachate, emissions, methane potential, or protein quality.",
            "The table's row-level SE is repeated for each condition only to preserve table scope; the source does not provide individual observation-level confidence intervals in these tables.",
            "The aerobic challenge is a single seven-day exposure at 25 °C in small, uncompacted, uncovered bottles; it is not a general post-opening kinetic model.",
            "Table 1 reports Italian ryegrass WSC as 124 g/kg DM while the Results narrative reports 25 g/kg DM. This unresolved source inconsistency is not silently resolved; WSC is excluded from this extract.",
            "No explicit reuse license was identified; the paper carries a 2013 journal copyright notice.",
            "No storage curve, degradation coefficient, emission factor, methane yield, model default, or GreenHub parameter mapping is inferred.",
        ],
    }
    SIDECAR_PATH.write_text(json.dumps(metadata, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    _update_local_registers(len(rows))
    _update_global_registers(len(rows))
    print(f"wrote {len(rows)} grass silage reference observations; sha256={digest}")


if __name__ == "__main__":
    main()
