"""Transcribe Table 2 cell-wall sugar measurements from Glazowska et al. (2025).

This is a reference dataset, not a GreenHub calibration. The paper's unit note
is inconsistent with the table total and total-percent columns, so all source
numbers are preserved without unit normalization.
"""
from __future__ import annotations

import csv
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PACKAGE = ROOT / "Greenhub/data/Protein recovery/Lactic_Acid"
OUT = PACKAGE / "grass_clover_alfalfa_cellwall_sugar_fractionation_glazowska_2025_reference.csv"
SIDECAR = OUT.with_suffix(".source.json")
SOURCE_ID = "SRC-GLAZOWSKA-2025-CELLWALL"
DOI = "10.1007/s13399-023-05125-5"
URL = "https://orbit.dtu.dk/files/389605334/s13399-023-05125-5_1_.pdf"
RECORD_URL = "https://doi.org/10.1007/s13399-023-05125-5"
RETRIEVAL_DATE = "2026-11-08"

FIELDS = [
    "record_id", "source_id", "feedstock", "fraction_code", "fraction_name",
    "metric", "reported_value", "reported_unit", "unit_basis_status",
    "analytical_method", "reported_basis", "replicate_or_uncertainty",
    "process_context", "source_location", "evidence_class", "quality_class",
    "activation_state", "transferability", "limitations", "doi", "source_url",
    "retrieval_date",
]

METRICS = [
    ("glucose", "Glc"), ("xylose", "Xyl"), ("galactose", "Gal"),
    ("arabinose", "Ara"), ("mannose", "Man"), ("rhamnose", "Rha"),
    ("fucose", "Fuc"), ("glucuronic_acid", "GlcA"),
    ("galacturonic_acid", "GalA"),
]

# Values copied from Table 2, in the order of METRICS, followed by the source's
# total (micrograms) and total (%). The total check is transcription-only.
FRACTIONS = [
    ("alfalfa", "FM", "fresh matter", [288, 189, 117, 103, 37.3, 23.2, 10.8, 192, 71.3], 1032, 10.3),
    ("alfalfa", "PC", "press cake", [277, 183, 127, 118, 42.0, 24.6, 7.92, 160, 91.6], 1032, 10.3),
    ("alfalfa", "GJ", "green juice", [410, 283, 63.4, 32.8, 20.3, 14.0, 13.2, 257, 29.2], 1123, 11.2),
    ("alfalfa", "FF", "fiber filtrate", [309, 251, 101, 74.0, 26.0, 19.4, 14.3, 264, 49.0], 1109, 11.1),
    ("alfalfa", "BJ", "brown juice", [69.1, 411, 78.7, 25.7, 16.1, 24.2, 22.4, 262, 34.6], 944, 9.44),
    ("alfalfa", "LPC", "protein concentrate", [192, 62.5, 58.4, 35.8, 14.0, 31.3, 19.3, 91.1, 16.4], 521, 5.21),
    ("grass_clover", "FM", "fresh matter", [444, 237, 137, 116, 31.1, 14.2, 117, 327, 74.9], 1499, 15.0),
    ("grass_clover", "PC", "press cake", [337, 187, 123, 110, 28.1, 7.0, 21.7, 204, 67.4], 1086, 10.9),
    ("grass_clover", "GJ", "green juice", [921, 341, 161, 49.8, 45.1, 11.4, 481, 660, 25.1], 2696, 27.0),
    ("grass_clover", "FF", "fiber filtrate", [485, 244, 123, 92.3, 18.0, 3.2, 180, 317, 30.2], 1493, 14.9),
    ("grass_clover", "BJ", "brown juice", [199, 480, 100, 43.1, 31.9, 14.2, 521, 460, 43.3], 1893, 18.9),
    ("grass_clover", "LPC", "protein concentrate", [282, 49.9, 57.0, 19.9, 11.6, 33.2, 80.6, 121, 17.5], 673, 6.73),
]

UNIT_LIMITATION = (
    "The Table 2 footnote says measurements are µg mg−1 AIR, while its Total column is µg, "
    "the method uses 10 mg AIR, and Total (%) does not reconcile with the footnote unit. "
    "Source values are transcribed literally; no unit conversion or inferred correction is applied."
)
TRANSFERABILITY = (
    "Danish cultivated alfalfa or a cultivated grass-clover mixture; comparator for Phase 3–5 stream composition only. "
    "Not roadside/VARTA grass, not a component mass balance, and not a GreenHub runtime input."
)


def build_rows() -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for feedstock, fraction_code, fraction_name, values, total, total_percent in FRACTIONS:
        records = [(metric, value, "µg mg−1 AIR (Table 2 footnote)", "conflict_with_total_columns")
                   for (metric, _), value in zip(METRICS, values, strict=True)]
        records.extend([
            ("total_non_cellulosic_monosaccharides", total, "µg (Table 2 column heading)", "source_basis_conflict"),
            ("total_non_cellulosic_monosaccharides_percent", total_percent, "% (Table 2 column heading)", "source_basis_conflict"),
        ])
        for metric, value, unit, unit_status in records:
            rows.append({
                "record_id": f"GLAZ25-{feedstock.upper()}-{fraction_code}-{metric.upper()}",
                "source_id": SOURCE_ID,
                "feedstock": feedstock,
                "fraction_code": fraction_code,
                "fraction_name": fraction_name,
                "metric": metric,
                "reported_value": str(value),
                "reported_unit": unit,
                "unit_basis_status": unit_status,
                "analytical_method": "TFA hydrolysis followed by HPLC-RI; neutral sugars and uronic acids",
                "reported_basis": "Alcohol-insoluble residue (AIR) from the indicated dried process fraction; literal source values",
                "replicate_or_uncertainty": "No SD/SE or HPLC replicate count printed for Table 2",
                "process_context": "Pilot green-biomass refining by screw pressing, juice filtration, lactic-acid fermentation/isoelectric precipitation, and centrifugation; feedstocks and equipment differ by crop",
                "source_location": "Table 2, journal p. 2991; Methods §§2.1–2.5, pp. 2985–2987",
                "evidence_class": "B_measured_primary_literature",
                "quality_class": "B",
                "activation_state": "reference_only",
                "transferability": TRANSFERABILITY,
                "limitations": UNIT_LIMITATION + " Values describe analyte abundance within AIR, not concentration per kg wet feed, a component mass balance, or mass recovered in a process stream.",
                "doi": DOI,
                "source_url": RECORD_URL,
                "retrieval_date": RETRIEVAL_DATE,
            })
    return rows


def read_rows(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    with path.open(encoding="utf-8-sig", newline="") as stream:
        reader = csv.DictReader(stream)
        return list(reader.fieldnames or []), list(reader)


def write_rows(path: Path, fields: list[str], rows: list[dict[str, str]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def upsert(path: Path, record: dict[str, str], key: str) -> None:
    fields, rows = read_rows(path)
    current = next((row for row in rows if row.get(key) == record[key]), None)
    if current is None:
        rows.append(record)
    else:
        current.update(record)
    write_rows(path, fields, rows)


def main() -> None:
    rows = build_rows()
    PACKAGE.mkdir(parents=True, exist_ok=True)
    write_rows(OUT, FIELDS, rows)
    digest = hashlib.sha256(OUT.read_bytes()).hexdigest()
    sidecar = {
        "source_id": SOURCE_ID,
        "dataset_title": "Cell-wall monosaccharide composition across alfalfa and grass-clover biorefinery fractions",
        "dataset_doi": DOI,
        "source_url": RECORD_URL,
        "full_text_url": URL,
        "authors": ["Sylwia Głazowska", "Emil Gundersen", "Stefan Heiske", "Mette Lübeck", "Jozef Mravec", "Bodil Jørgensen"],
        "publication_year": 2025,
        "doi_first_published_online": 2023,
        "journal": "Biomass Conversion and Biorefinery 15, 2983–2995",
        "retrieval_date": RETRIEVAL_DATE,
        "license": "CC BY 4.0 stated in article",
        "source_file": OUT.name,
        "source_file_sha256": digest,
        "row_count": len(rows),
        "source_location": "Table 2, p. 2991; methods §§2.1–2.5, pp. 2985–2987",
        "geography": "Denmark",
        "feedstocks": {
            "alfalfa": "Organic Medicago sativa harvested in September 2019 at Aarhus University Foulum.",
            "grass_clover": "Organically grown ForageMax45 harvested August 2019 near Skive; reported species ratio 40:42:9:9 for perennial ryegrass, hybrid ryegrass/festulolium, white clover, red clover.",
        },
        "process_context": "Alfalfa was shredded to about 5 cm and processed in a Vincent CP4 single-screw press, filtered at 150 µm, fermented overnight at 38 °C with Lactobacillus salivarius BC1001, acidified to about pH 4.2, and dewatered in a horizontal decanter. Grass-clover was chopped to 1–3 cm, fractionated in a Cir-tech EFB 25 twin-screw press with 250/100 µm sieves and fiber recirculation, then fermented and dewatered in a decanter at 12 L/min. Table 2 reports AIR monosaccharides across FM, PC, GJ, FF, BJ, and LPC.",
        "analytical_method": "TFA hydrolysis of AIR followed by HPLC-RI for neutral sugars and uronic acids.",
        "source_unit_conflict": UNIT_LIMITATION,
        "reported_unit_policy": "Transcribe Table 2 values literally. Analyte values use the footnote wording; total and percent use their own column headings. Do not normalize, convert, or derive wet-stream concentrations until the authors resolve the unit conflict.",
        "uncertainty": "Table 2 does not print SD/SE or an HPLC replicate count; do not treat CoMPP technical replicate counts as Table 2 replicate counts.",
        "evidence_class": "B_measured_primary_literature",
        "quality_class": "B",
        "activation_state": "reference_only",
        "transferability": TRANSFERABILITY,
        "limitations": [
            "Cultivated Danish feedstocks, not roadside or VARTA grass.",
            "AIR-normalized sugar measurements are not flow-weighted component mass balances or wet-feed concentrations.",
            "The article's Table 2 unit note conflicts with its total columns and total percentages; no correction is assumed.",
            "No table-level uncertainty or process-batch replication is given for the Table 2 HPLC values.",
            "The data are not connected to runtime parameters, defaults, TEA/LCA, or Pareto outputs.",
        ],
        "rights_note": "The article states CC BY 4.0; cite the article and identify this as a transcription with a source-unit caveat.",
    }
    SIDECAR.write_text(json.dumps(sidecar, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    upsert(PACKAGE / "source_register.csv", {
        "source_id": SOURCE_ID,
        "source_title": "Tracking digestible and non-digestible cell wall components during protein concentrate production from grass-clover and alfalfa",
        "authors": "Sylwia Głazowska; Emil Gundersen; Stefan Heiske; Mette Lübeck; Jozef Mravec; Bodil Jørgensen",
        "year": "2025",
        "source_type": "peer-reviewed primary experimental article; pilot biorefinery fraction analyses",
        "doi_or_stable_id": DOI,
        "source_url": RECORD_URL,
        "primary_or_secondary": "primary",
        "materials": "cultivated alfalfa and grass-clover; fresh matter, press cake, green juice, fiber filtrate, brown juice and leaf protein concentrate",
        "key_use": "Phase 3–5 comparative cell-wall monosaccharide distribution across protein-biorefinary process fractions",
        "limitations": "Reference-only. Danish cultivated forage, not roadside/VARTA; AIR-normalized composition is not a component mass balance. Table 2 footnote unit conflicts with its total columns and percentages; values are transcribed literally without correction. CC BY 4.0 stated in article.",
    }, "source_id")
    upsert(PACKAGE / "dataset_manifest.csv", {
        "filename": OUT.name,
        "purpose": "Table 2 HPLC-RI monosaccharide values in AIR across alfalfa and grass-clover process fractions; reference-only.",
        "row_count": str(len(rows)),
        "validation_status": "PASS_WITH_SOURCE_UNIT_CAVEAT",
        "integration_readiness": "reference_only_D3",
        "key_limitation": "Cultivated feed comparator, no stream mass balance or HPLC uncertainty, and source unit conflict is preserved without correction.",
    }, "filename")


if __name__ == "__main__":
    main()
