"""Build a traceable per-harvest extract of Nielsen et al. (2021), Tables 3–4."""
from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "Greenhub" / "data"
GROUP = DATA / "Pre-treatment" / "Feedstock"
AUDIT = DATA / "global_audit_package"
FILENAME = "fen_grass_biorefinery_fractionation_per_harvest_nielsen_2021_tables_3_4_reference.csv"
CSV_PATH = GROUP / FILENAME
SOURCE_ID = "SRC-NIELSEN-2021"
DOI = "10.3389/fenvs.2021.619258"
URL = f"https://doi.org/{DOI}"
RETRIEVED = "2026-11-08"

STREAMS = [
    ("plant_biomass", "DM yield"), ("plant_biomass", "CP yield"),
    ("pulp", "DM yield"), ("pulp", "CP yield"),
    ("protein_concentrate", "DM yield"), ("protein_concentrate", "CP yield"),
    ("brown_juice", "DM yield"), ("brown_juice", "CP yield"),
]
FIELDS = [
    "record_id", "source_id", "source_table", "measurement_year", "geography",
    "species", "treatment_harvest_cuts", "harvest_index", "harvest_week",
    "stream", "measurement", "reported_mean", "reported_sd",
    "reported_mean_text", "reported_sd_text", "unit", "source_basis_note",
    "record_status", "evidence_class", "quality_class", "activation_state",
    "limitations", "source_location", "retrieval_date",
]

# Table values are kept as printed. Each event contains the eight paired values
# (mean, SD) for biomass DM/CP, pulp DM/CP, concentrate DM/CP, and brown-juice DM/CP.
# The table caption gives a common annual yield unit, but the rows are indexed by
# cut and harvest week. No conversion or re-interpretation is applied here.
HARVESTS = {
    "reed_canary_grass": {
        "table": "Table 3",
        "cuts": {
            2: [(1, 24, ["8.8", "3.3", "2.0", "0.7", "6.9", "2.7", "0.9", "0.2", "0.8", "0.2", "0.3", "0.1", "0.9", "0.4", "0.2", "0.1"]),
                (2, 36, ["6.8", "4.4", "1.4", "0.9", "4.6", "3.3", "0.5", "0.3", "0.9", "0.4", "0.3", "0.1", "1.0", "0.6", "0.2", "0.1"])],
            3: [(1, 20, ["1.6", "0.7", "0.3", "0.2", "1.0", "0.5", "0.2", "0.1", "0.3", "0.1", "0.1", ">0.0", "0.2", "0.1", ">0.0", ">0.0"]),
                (2, 32, ["5.5", "1.4", "0.8", ">0.0", "4.2", "1.0", "0.4", "0.1", "0.4", "0.1", "0.1", ">0.0", "0.6", "0.3", "0.1", ">0.0"]),
                (3, 42, ["3.2", "0.7", "0.8", "0.2", "1.9", "0.4", "0.2", ">0.0", "0.5", "0.1", "0.2", "0.1", "0.6", "0.2", "0.1", ">0.0"])],
            4: [(1, 20, ["2.0", "0.7", "0.4", "0.1", "1.3", "0.5", "0.2", "0.1", "0.3", "0.1", "0.1", ">0.0", "0.3", "0.1", ">0.0", ">0.0"]),
                (2, 24, ["4.0", "1.3", "1.1", "0.3", "2.9", "1.0", "0.3", "0.2", "0.5", "0.1", "0.2", "0.1", "0.4", "0.1", "0.1", ">0.0"]),
                (3, 36, ["8.8", "4.5", "1.5", "0.6", "6.1", "3.1", "0.5", "0.2", "1.1", "0.5", "0.3", "0.1", "1.3", "0.7", "0.2", "0.1"]),
                (4, 42, ["1.3", "NA", "0.3", "NA", "0.8", "NA", "0.1", "NA", "0.3", "NA", "0.1", "NA", "0.2", "NA", ">0.0", "NA"])],
            5: [(1, 20, ["1.7", "0.6", "0.3", "0.1", "1.1", "0.4", "0.2", ">0.0", "0.3", "0.1", "0.1", ">0.0", "0.2", "0.1", ">0.0", ">0.0"]),
                (2, 24, ["3.9", "1.0", "1.1", "0.2", "2.8", "0.8", "0.4", ">0.0", "0.4", "0.1", "0.2", ">0.0", "0.3", "0.2", "0.1", ">0.0"]),
                (3, 32, ["6.5", "1.3", "1.1", "0.2", "5.0", "1.3", "0.5", "0.1", "0.4", "0.1", "0.1", ">0.0", "0.7", "0.1", "0.1", ">0.0"]),
                (4, 36, ["2.4", "2.1", "0.6", "0.6", "1.5", "1.4", "0.2", "0.2", "0.4", "0.3", "0.2", "0.1", "0.3", "0.3", "0.1", "0.1"]),
                (5, 42, ["NA"] * 16)],
        },
    },
    "tall_fescue": {
        "table": "Table 4",
        "cuts": {
            2: [(1, 24, ["7.9", "1.9", "1.8", "0.5", "6.0", "1.5", "0.7", "0.1", "0.7", "0.2", "0.3", "0.1", "0.9", "0.3", "0.1", "0.1"]),
                (2, 36, ["5.5", "2.9", "1.1", "0.4", "3.5", "1.8", "0.4", "0.1", "0.5", "0.3", "0.2", "0.1", "1.0", "0.6", "0.1", ">0.0"])],
            3: [(1, 20, ["1.3", "0.8", "0.3", "0.2", "0.9", "0.5", "0.1", "0.1", "0.2", "0.1", "0.1", "0.1", "0.2", "0.1", ">0.0", ">0.0"]),
                (2, 32, ["5.1", "2.7", "0.8", "0.3", "3.8", "1.9", "0.4", "0.2", "0.4", "0.2", "0.1", ">0.0", "0.7", "0.4", "0.1", ">0.0"]),
                (3, 42, ["2.6", "1.2", "0.7", "0.3", "1.5", "0.7", "0.2", "0.1", "0.4", "0.3", "0.2", "0.1", "0.5", "0.2", "0.1", ">0.0"])],
            4: [(1, 20, ["1.0", "0.7", "0.2", "0.1", "0.6", "0.4", "0.1", "0.1", "0.2", "0.1", "0.1", "0.1", "0.1", "0.1", ">0.0", ">0.0"]),
                (2, 24, ["2.7", "1.6", "0.7", "0.4", "1.9", "1.1", "0.3", "0.2", "0.3", "0.2", "0.2", "0.1", "0.3", "0.2", "0.1", ">0.0"]),
                (3, 36, ["5.5", "1.7", "1.1", "0.2", "3.7", "1.2", "0.4", "0.1", "0.6", "0.2", "0.2", "0.1", "0.9", "0.4", "0.2", ">0.0"]),
                (4, 42, ["1.0", "NA", "0.3", "NA"] + ["NA"] * 12)],
            5: [(1, 20, ["0.9", "0.5", "0.2", "0.1", "0.6", "0.3", "0.1", "0.1", "0.1", "0.1", "0.1", ">0.0", "0.1", "0.1", ">0.0", ">0.0"]),
                (2, 24, ["2.4", "1.8", "0.6", "0.4", "1.7", "1.2", "0.3", "0.2", "0.3", "0.2", "0.1", "0.1", "0.3", "0.2", ">0.0", ">0.0"]),
                (3, 32, ["4.7", "1.2", "0.8", "0.2", "3.5", "0.7", "0.4", "0.1", "0.4", "0.1", "0.1", ">0.0", "0.6", "0.3", "0.1", ">0.0"]),
                (4, 36, ["1.1", "0.1", "0.3", ">0.0", "0.6", "0.1", "0.1", ">0.0", "0.1", "0.1", "0.1", ">0.0", "0.2", ">0.0", ">0.0", ">0.0"]),
                (5, 42, ["1.1", "0.1", "0.3", ">0.0", "0.6", "0.1", "0.1", ">0.0", "0.3", ">0.0", "0.1", ">0.0", "0.2", ">0.0", ">0.0", ">0.0"])],
        },
    },
}


def read_csv(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    with path.open("r", encoding="utf-8-sig", newline="") as stream:
        reader = csv.DictReader(stream)
        return list(reader.fieldnames or []), list(reader)


def upsert(path: Path, row: dict[str, object], key: str) -> None:
    fields, rows = read_csv(path)
    if not fields:
        raise ValueError(f"Expected existing CSV headers: {path}")
    normalized = {field: str(row.get(field, "")) for field in fields}
    rows = [existing for existing in rows if existing.get(key) != normalized[key]]
    rows.append(normalized)
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def parse_reported(text: str) -> tuple[str, str, str]:
    if text == "NA":
        return "", "NA", "not_reported_NA"
    if text.startswith(">"):
        return "", text, "reported_threshold_or_censored_at_table_precision"
    return text, text, "reported_numeric"


def main() -> None:
    GROUP.mkdir(parents=True, exist_ok=True)
    rows: list[dict[str, str]] = []
    for species, spec in HARVESTS.items():
        for n_cuts, events in spec["cuts"].items():
            for harvest_index, week, values in events:
                if len(values) != 16:
                    raise ValueError(f"Expected 16 mean/SD cells, got {len(values)}: {species}, {n_cuts}, {week}")
                for offset, (stream, measure) in enumerate(STREAMS):
                    mean_text, sd_text = values[offset * 2: offset * 2 + 2]
                    mean, mean_rendered, mean_status = parse_reported(mean_text)
                    sd, sd_rendered, sd_status = parse_reported(sd_text)
                    status = "reported"
                    if mean_status == "not_reported_NA":
                        status = "not_available_source_NA_insufficient_biomass_note"
                    elif sd_status == "not_reported_NA":
                        status = "mean_reported_sd_unavailable_source_NA_single_replicate"
                    elif mean_status.startswith("reported_threshold"):
                        status = "reported_mean_at_table_precision_threshold"
                    elif sd_status.startswith("reported_threshold"):
                        status = "reported_mean_sd_at_table_precision_threshold"
                    rows.append({
                        "record_id": f"NF21-{spec['table'].replace(' ', '')}-{species.upper()}-{n_cuts}CUT-C{harvest_index}-W{week}-{stream.upper()}-{measure.split()[0].upper()}",
                        "source_id": SOURCE_ID, "source_table": spec["table"],
                        "measurement_year": "2019", "geography": "Vejrumbro, Central Jutland, Denmark",
                        "species": species.replace("_", " "), "treatment_harvest_cuts": str(n_cuts),
                        "harvest_index": str(harvest_index), "harvest_week": str(week),
                        "stream": stream, "measurement": measure,
                        "reported_mean": mean, "reported_sd": sd,
                        "reported_mean_text": mean_rendered, "reported_sd_text": sd_rendered,
                        "unit": "t ha^-1 year^-1 (Table 3/4 caption; per-cut rows indexed by harvest week)",
                        "source_basis_note": "Source table caption states all yields in t ha^-1 year^-1; records are per-cut rows, not the annual-average rows. Values are preserved as reported and are not converted or reinterpreted.",
                        "record_status": status,
                        "evidence_class": "B_primary_field_and_laboratory_measurement_reported_in_table",
                        "quality_class": "B", "activation_state": "reference_only",
                        "limitations": "Cultivated flood-tolerant forage grasses on one Danish fen peatland; four-block field study, lab-scale twin-screw press and acid precipitation. Not roadside/VARTA feed or GreenHub route calibration. Press conditions and stream losses may not transfer. The source reports insufficient biomass for some press runs; NA and >0.0 are preserved without imputation.",
                        "source_location": f"{spec['table']}, per-harvest row {harvest_index} (week {week}); article DOI table",
                        "retrieval_date": RETRIEVED,
                    })

    with CSV_PATH.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=FIELDS, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
    digest = hashlib.sha256(CSV_PATH.read_bytes()).hexdigest()
    sidecar = {
        "dataset_id": "urn:greenhub:dataset:nielsen-2021-fen-grass-per-harvest-fraction-yields:v1",
        "dataset_version": "1.0.0", "title": "Per-harvest dry-matter and crude-protein yields in flood-tolerant grass screw-press fractions",
        "source_file": FILENAME, "source_file_sha256": digest, "record_count": len(rows),
        "source_id": SOURCE_ID,
        "citation": "Nielsen, C. K., Stødkilde, L., Jørgensen, U. & Lærke, P. E. (2021). Effects of Harvest and Fertilization Frequency on Protein Yield and Extractability From Flood-Tolerant Perennial Grasses Cultivated on a fen Peatland. Frontiers in Environmental Science, 9, 619258.",
        "doi": DOI, "source_url": URL, "full_text_url": "https://www.frontiersin.org/journals/environmental-science/articles/10.3389/fenvs.2021.619258/full",
        "retrieval_date": RETRIEVED, "geography": "Vejrumbro, Central Jutland, Denmark",
        "measurement_year": 2019, "source_tables": [3, 4], "license": "CC BY 4.0, as stated in the article copyright notice.",
        "design": "Four-block field experiment; reed canary grass and tall fescue; one to five annual harvest treatments. Tables 3 and 4 report dry-matter and crude-protein yields in plant biomass, pulp, protein concentrate and brown juice.",
        "method": "Published per-harvest rows in Tables 3 and 4 transcribed. The source table caption states all yields in t ha^-1 year^-1; per-harvest rows are indexed by cut number and harvest week. Unit text is retained and no per-cut or annual conversion is performed. Table 3/4 annual averages are already represented in a sibling reference dataset and are not duplicated here.",
        "activation_state": "reference_only", "runtime_parameter_mapping": None,
        "limitations": [
            "This is cultivated reed canary grass and tall fescue on a Danish fen peatland, not mixed Dutch roadside grass or GreenHub feed.",
            "The field trial used a lab-scale twin-screw press; one-cut biomass could not be pressed because of advanced lignification.",
            "Pressing and acid precipitation conditions are laboratory methods; reagent volume/equivalents and GreenHub-scale performance are not established.",
            "NA values, one-replicate SD omissions, and >0.0 source thresholds remain explicitly represented; no values are imputed.",
            "The same-source annual rows remain in fen_grass_biorefinery_fractionation_annual_nielsen_2021_tables_3_4_reference.csv; this file contains only per-harvest rows.",
        ],
    }
    Path(str(CSV_PATH) + ".source.json").write_text(json.dumps(sidecar, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    upsert(GROUP / "dataset_manifest.csv", {
        "file_name": FILENAME, "description": "Nielsen et al. (2021) per-harvest Table 3/4 yields for biomass and screw-pressed streams",
        "row_count": len(rows), "schema_version": "1.0", "encoding": "UTF-8", "delimiter": ",",
        "integration_readiness": "traceable_reference_only_not_runtime_eligible",
        "limitations": "Cultivated Danish fen grasses and lab-scale fractionation; source caption units retained verbatim; no GreenHub transfer or runtime activation.",
    }, "file_name")
    rel = f"Pre-treatment/Feedstock/{FILENAME}"
    upsert(AUDIT / "global_source_register.csv", {
        "dataset_path": rel, "dataset_group": "Pre-treatment/Feedstock", "source_id": SOURCE_ID,
        "source_title": "Effects of Harvest and Fertilization Frequency on Protein Yield and Extractability From Flood-Tolerant Perennial Grasses Cultivated on a fen Peatland",
        "authors": "Claudia Kalla Nielsen; Lene Stødkilde; Uffe Jørgensen; Poul Erik Lærke", "year": "2021",
        "doi_or_stable_id": DOI, "url": URL,
        "source_type": "peer-reviewed open-access field and lab experiment; per-harvest table values",
        "notes": "Tables 3–4 per-harvest biomass, pulp, protein-concentrate and brown-juice DM/CP yields. Same-source annual averages are staged separately. Reference-only; source unit-basis caveat preserved.",
    }, "dataset_path")
    upsert(AUDIT / "global_dataset_manifest.csv", {
        "dataset_path": rel, "category": "Pre-treatment", "subgroup": "Feedstock; seasonal fractionation comparator",
        "filename": FILENAME, "row_count_observed": len(rows), "header_count": len(FIELDS),
        "headers": "; ".join(FIELDS), "standardized_status_values": "B;reference_only",
        "detected_readiness": "D3", "notes": "Per-harvest Tables 3/4; table unit caption retained; not roadside grass or GreenHub calibration.",
    }, "dataset_path")
    upsert(AUDIT / "global_dataset_readiness.csv", {
        "dataset_path": rel, "category": "Pre-treatment", "subgroup": "Feedstock; seasonal fractionation comparator",
        "readiness": "D3", "duplicate_ids": 0, "duplicate_rows": 0, "numeric_rows": sum(bool(row["reported_mean"]) for row in rows),
        "unsourced_numeric_rows": 0, "numeric_rows_missing_exact_location": 0, "unit_conflicts": 0,
        "basis_conflicts": 0, "cross_reference_issues": 0, "equation_missing_inputs": 0,
        "equation_symbol_mismatches": 0, "notes": "Table-specific means/SD text and exact harvest week are retained; NA and >0.0 do not become numbers.",
    }, "dataset_path")
    upsert(AUDIT / "source_dataset_checksums.csv", {
        "dataset_path": rel, "sha256": digest, "byte_size": CSV_PATH.stat().st_size,
    }, "dataset_path")

    source_register = GROUP / "source_register.csv"
    _, sources = read_csv(source_register)
    source = next((item for item in sources if item.get("source_id") == SOURCE_ID), None)
    if not source:
        raise ValueError("Expected the existing SRC-NIELSEN-2021 source-register row.")
    updated = dict(source)
    note = "Per-harvest Table 3/4 stream yields are staged separately from the existing annual-average extract; source unit caption retained verbatim; reference-only."
    if note not in updated.get("quality_notes", ""):
        updated["quality_notes"] = (updated.get("quality_notes", "") + " " + note).strip()
    upsert(source_register, updated, "source_id")
    print(json.dumps({"dataset": rel, "records": len(rows), "sha256": digest, "activation_state": "reference_only"}, indent=2))


if __name__ == "__main__":
    main()
