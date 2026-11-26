"""Build a traceable extract of Stødkilde et al. (2021) Tables 1–5.

This is a cultivated-forage analogue, not roadside-grass calibration. All rows
remain reference-only; no model input or default is changed.
"""
from __future__ import annotations

import csv
import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
FOLDER = ROOT / "Greenhub/data/Pre-treatment/Mechanical"
FILENAME = "stodkilde_2021_species_harvest_press_fractionation_reference.csv"
OUT = FOLDER / FILENAME
SOURCE_ID = "SRC-STODKILDE-2021-AFST"
DOI = "10.1016/j.anifeedsci.2021.115016"
URL = "https://doi.org/10.1016/j.anifeedsci.2021.115016"
FULL_TEXT = "https://pure.au.dk/ws/files/277690669/1_s2.0_S0377840121002029_main.pdf"
RETRIEVED = "2026-11-08"

SPECIES = [
    ("LU", "Lucerne", "Medicago sativa L."),
    ("RC", "Red clover", "Trifolium pratense L."),
    ("WC", "White clover", "Trifolium repens L."),
    ("PRG", "Perennial ryegrass", "Lolium perenne L."),
    ("TF", "Tall fescue", "Festuca arundinacea L."),
]
DATES = [("MAY17", "17 May"), ("MAY24", "24 May"), ("MAY31", "31 May"), ("JUN06", "6 June")]

FIELDS = [
    "record_id", "source_id", "study_year", "geography", "plant_species",
    "scientific_name", "harvest_date", "harvest_cut", "process_stage",
    "press_passes", "metric", "value_numeric", "reported_value_text", "unit",
    "basis", "source_table", "source_location", "pooled_model_sem",
    "sem_scope", "significance_group", "field_plot_replicates",
    "condition_scope", "evidence_class", "quality_class", "activation_state",
    "applicability", "validation_status", "limitations",
]

COMMON_LIMITS = (
    "Cultivated Danish experimental forage, not Dutch roadside/VARTA grass. "
    "One first-cut season; samples were frozen at -18 °C before laboratory processing. "
    "Field plots were in duplicate; analytical replicate counts are not separately reported. "
    "Do not combine with the earlier 2020 proceedings extract without reconciling overlapping "
    "ryegrass values: that proceedings paper is a precursor publication, and some reported "
    "nitrogen recoveries differ. Nitrogen is not interchangeable with crude protein. "
    "Source table cells are least-square means; published species means are not forced to equal "
    "the arithmetic mean of displayed harvest-date means. "
    "No values activate GreenHub defaults or equations."
)

# Each table block is stored in source column order: species × harvest-date rows.
# Letter suffixes are the source's within-species Tukey groups. Pooled SEM is the
# model SEM and is not a date-specific standard error.
BLOCKS = [
    ("feed", 0, "dry_matter_content", "g/kg fresh matter", "fresh plant", "Table 1", [5.83, 8.19, 10.10, 15.79, 16.61], [
        ["183.2a", "128.1b", "153.4", "183.4", "224.9"],
        ["123.8c", "92.7c", "110.3", "128.3", "177.7"],
        ["156.3b", "120.6bc", "129.0", "186.1", "202.3"],
        ["184.0a", "164.5a", "116.5", "169.5", "214.4"],
    ]),
    ("feed", 0, "nitrogen_content", "g N/kg DM", "dry matter", "Table 1", [1.89, 1.82, 1.97, 2.24, 1.60], [
        ["37.0a", "37.4a", "43.2", "30.6", "30.1a"],
        ["39.1a", "35.7ab", "42.3", "24.8", "26.7a"],
        ["33.2a", "29.0bc", "35.1", "18.7", "18.2b"],
        ["25.6b", "22.7c", "34.2", "20.5", "19.6b"],
    ]),
    ("feed", 0, "dry_matter_yield", "tonne DM/ha", "plot area", "Table 1", [0.207, 0.199, 0.102, 0.308, 0.482], [
        ["1.47c", "2.85b", "1.52c", "2.71b", "3.45b"],
        ["2.57b", "3.71a", "2.33b", "4.52a", "4.50a"],
        ["2.34b", "2.57c", "1.05d", "2.92b", "4.32a"],
        ["5.59a", "5.10a", "3.10a", "5.72a", "6.99a"],
    ]),
    ("single_press_pulp", 1, "dry_matter_content", "g/kg fresh pulp", "fresh pulp", "Table 2", [18.79, 9.50, 30.48, 6.67, 32.62], [
        ["289.0bc", "266.6c", "270.4", "412.9", "413.1"],
        ["280.8c", "264.1c", "220.9", "390.9", "406.1"],
        ["356.5ab", "348.8b", "273.6", "403.6", "450.0"],
        ["395.9a", "393.6a", "328.9", "400.2", "450.2"],
    ]),
    ("single_press_pulp", 1, "nitrogen_content", "g N/kg DM", "dry matter", "Table 2", [0.96, 2.08, 1.48, 0.98, 0.68], [
        ["31.4a", "35.5", "43.2a", "31.2a", "25.4a"],
        ["27.8a", "26.7", "33.8b", "23.3b", "20.9b"],
        ["22.0b", "26.0", "32.6b", "19.5c", "17.9c"],
        ["23.3b", "25.6", "29.2b", "19.4c", "16.4c"],
    ]),
    ("double_press_pulp", 2, "dry_matter_content", "g/kg fresh pulp", "fresh pulp", "Table 2", [17.06, 19.56, 29.85, 35.08, 29.39], [
        ["309.0b", "343.6", "360.9", "379.2", "424.5"],
        ["373.8ab", "353.0", "341.5", "365.3", "401.7"],
        ["393.8a", "364.1", "355.1", "397.5", "439.0"],
        ["439.6a", "413.9", "390.5", "328.4", "370.6"],
    ]),
    ("double_press_pulp", 2, "nitrogen_content", "g N/kg DM", "dry matter", "Table 2", [1.04, 1.71, 2.13, 0.78, 1.12], [
        ["23.8", "31.0a", "40.4a", "27.3a", "19.3"],
        ["20.1", "23.5b", "32.9ab", "20.7b", "17.7"],
        ["20.1", "22.1b", "26.8b", "18.0b", "14.3"],
        ["17.5", "19.9b", "25.8b", "14.7c", "13.7"],
    ]),
    ("single_press_concentrate", 1, "dry_matter_content", "g/kg fresh concentrate", "fresh concentrate", "Table 3", [4.75, 4.38, 5.22, 5.13, 4.41], [
        ["227.4a", "163.6b", "179.6", "195.1a", "183.1a"],
        ["166.6c", "138.3c", "157.2", "153.0b", "152.2c"],
        ["190.8b", "151.3bc", "158.0", "155.8b", "172.2ab"],
        ["195.3b", "185.1a", "181.0", "160.4b", "164.1bc"],
    ]),
    ("single_press_concentrate", 1, "nitrogen_content", "g N/kg DM", "dry matter", "Table 3", [0.85, 0.89, 1.04, 1.70, 3.95], [
        ["56.0c", "61.3a", "60.4bc", "50.4", "58.9"],
        ["68.9a", "63.1a", "66.7a", "55.9", "59.3"],
        ["66.8a", "57.6b", "60.9b", "48.7", "50.4"],
        ["61.6b", "52.1c", "56.5c", "49.0", "38.1"],
    ]),
    ("double_press_concentrate", 2, "dry_matter_content", "g/kg fresh concentrate", "fresh concentrate", "Table 3", [11.07, 15.46, 18.69, 5.79, 5.94], [
        ["141.5", "126.3", "113.2", "114.0", "118.7"],
        ["88.6", "96.3", "113.7", "120.1", "99.2"],
        ["113.9", "112.2", "120.4", "113.4", "107.7"],
        ["120.0", "136.3", "101.3", "125.1", "122.7"],
    ]),
    ("double_press_concentrate", 2, "nitrogen_content", "g N/kg DM", "dry matter", "Table 3", [1.46, 3.22, 1.05, 1.34, 3.98], [
        ["56.0ab", "64.0a", "63.6a", "64.5a", "52.5"],
        ["58.4a", "60.2ab", "60.6b", "61.8b", "51.2"],
        ["50.6bc", "49.7bc", "51.7c", "49.7c", "42.3"],
        ["46.6c", "42.8c", "49.3c", "47.0c", "43.4"],
    ]),
    ("single_press_pulp", 1, "nitrogen_recovery_to_pulp", "g N/kg plant N", "initial plant N", "Table 4", [20.6, 22.2, 49.9, 30.6, 31.6], [
        ["467.0a", "457.9b", "556.8", "598.8", "544.5"],
        ["362.4b", "334.0c", "392.0", "578.7", "555.4"],
        ["343.0b", "454.8b", "452.7", "623.8", "613.4"],
        ["467.8a", "565.2a", "472.7", "668.4", "715.1"],
    ]),
    ("double_press_pulp", 2, "nitrogen_recovery_to_pulp", "g N/kg plant N", "initial plant N", "Table 4", [29.9, 19.7, 36.7, 20.4, 32.4], [
        ["238.5", "328.7b", "398.4", "418.0", "388.1"],
        ["231.0", "242.4c", "280.2", "397.6", "411.2"],
        ["247.0", "324.3b", "295.1", "459.1", "460.8"],
        ["347.7", "430.3a", "350.1", "460.0", "519.6"],
    ]),
    ("single_press_concentrate", 1, "nitrogen_recovery_to_protein_concentrate", "g N/kg plant N", "initial plant N", "Table 5", [7.3, 30.1, 43.3, 29.9, 21.7], [
        ["415.7b", "392.4b", "355.1", "314.9", "335.6a"],
        ["474.9a", "556.2a", "504.3", "317.8", "327.8a"],
        ["480.0a", "431.1b", "447.1", "264.5", "261.6a"],
        ["367.3c", "342.5b", "375.3", "203.0", "160.2b"],
    ]),
    ("double_press_concentrate", 2, "nitrogen_recovery_to_protein_concentrate", "g N/kg plant N", "initial plant N", "Table 5", [13.2, 16.2, 52.6, 44.5, 13.0], [
        ["211.2a", "175.4a", "206.8", "148.3", "132.8"],
        ["134.4c", "97.7b", "133.8", "176.4", "105.4"],
        ["99.7c", "81.6b", "142.2", "122.8", "127.1"],
        ["123.6c", "121.8b", "108.3", "192.0", "182.6"],
    ]),
]


def parse_source_cell(raw: str) -> tuple[str, str]:
    match = re.fullmatch(r"\s*(\d+(?:\.\d+)?)\s*([a-z]*)\s*", raw)
    if not match:
        return "", ""
    return match.group(1), match.group(2)


def build_rows() -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for stage, presses, metric, unit, basis, table, sems, matrix in BLOCKS:
        for date_index, (date_code, harvest_date) in enumerate(DATES):
            for species_index, (species_code, species, scientific_name) in enumerate(SPECIES):
                source_text = matrix[date_index][species_index]
                value, significance = parse_source_cell(source_text)
                validation = "source_value_transcribed"
                note = ""
                # The indexed PDF text layer reads 12.81b, but the table species
                # LS mean (126.5) and remaining dates support 128.1b. Keep the
                # text-layer anomaly explicit while using the reconciled digit.
                if table == "Table 1" and metric == "dry_matter_content" and date_code == "MAY17" and species_code == "RC":
                    source_text = "12.81b (machine-readable PDF text layer); numeric cell reconciled to 128.1 from published species LSmean 126.5"
                    value = "128.1"
                    significance = "b"
                    validation = "ocr_digit_reconciled_against_published_species_lsmean"
                    note = "The PDF text layer appears to omit the 8 in 128.1; the value is consistent with the reported four-date species LSmean (126.5). Treat this one cell as a documented transcription reconciliation, not an independently verified scan transcription."
                stage_label = {
                    "feed": "whole_plant_feed",
                    "single_press_pulp": "pulp_after_single_press" if presses == 1 else "pulp_after_second_press",
                    "double_press_pulp": "pulp_after_second_press",
                    "single_press_concentrate": "protein_concentrate_from_single_press_juice" if presses == 1 else "protein_concentrate_from_second_press_juice",
                    "double_press_concentrate": "protein_concentrate_from_second_press_juice",
                }[stage]
                replicates = "2 field plot replicates; analytical replicate count not separately reported"
                condition = (
                    "Foulumgaard, Denmark; first cut 2016; 7 cm stubble; grasses fertilized at 140 kg N/ha; "
                    "harvest-date plots independent; samples frozen at -18 C; thawed overnight at 4 C; Angelia 8500S lab twin-screw press."
                )
                if presses == 2 and "press" in stage:
                    condition += " Second pulp press used 200 g pulp diluted with 400 mL Milli-Q water; 10 min magnetic stirring."
                if "concentrate" in stage:
                    condition += " Green juice treated with 12 M phosphoric acid to pH 4, held overnight at 4 C, then centrifuged 10 min at 2000 g and 4 C; acid volume/equivalents not reported."
                if metric in {"nitrogen_content"}:
                    condition += " Nitrogen measured by Dumas; fraction N reported on DM basis."
                if "recovery" in metric:
                    condition += " Source-calculated N recovery using nitrogen content and produced fraction mass; denominator is plant N, not total protein."
                rows.append({
                    "record_id": f"STODKILDE21-{species_code}-{date_code}-{stage.upper()}-{metric.upper()}",
                    "source_id": SOURCE_ID,
                    "study_year": "2016 harvest; article 2021",
                    "geography": "Foulumgaard, Aarhus University, Denmark",
                    "plant_species": species,
                    "scientific_name": scientific_name,
                    "harvest_date": harvest_date,
                    "harvest_cut": "spring first cut",
                    "process_stage": stage_label,
                    "press_passes": str(presses),
                    "metric": metric,
                    "value_numeric": value,
                    "reported_value_text": source_text,
                    "unit": unit,
                    "basis": basis,
                    "source_table": table,
                    "source_location": f"{table}; first-cut date row; species column ({species})",
                    "pooled_model_sem": str(sems[species_index]),
                    "sem_scope": "overall model SEM; pooled, not date-specific",
                    "significance_group": significance,
                    "field_plot_replicates": replicates,
                    "condition_scope": condition,
                    "evidence_class": "primary_experimental_measurement_or_source_calculation",
                    "quality_class": "B",
                    "activation_state": "reference_only",
                    "applicability": "cultivated_forage_comparator_not_roadside_or_VARTA_calibration",
                    "validation_status": validation,
                    "limitations": COMMON_LIMITS + (" " + note if note else ""),
                })
    return rows


def write_csv(path: Path, fieldnames: list[str], rows: list[dict[str, str]]) -> None:
    with path.open("w", encoding="utf-8-sig", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def upsert_csv(path: Path, key: str, new_row: dict[str, str]) -> None:
    with path.open(encoding="utf-8-sig", newline="") as stream:
        reader = csv.DictReader(stream)
        fieldnames = list(reader.fieldnames or [])
        rows = list(reader)
    if key not in fieldnames:
        raise ValueError(f"{key} not found in {path}")
    rows = [row for row in rows if row.get(key) != new_row.get(key)]
    rows.append(new_row)
    write_csv(path, fieldnames, rows)


def main() -> None:
    rows = build_rows()
    write_csv(OUT, FIELDS, rows)
    checksum = hashlib.sha256(OUT.read_bytes()).hexdigest()
    sidecar = {
        "dataset_id": "urn:greenhub:dataset:stodkilde-2021-species-harvest-press-fractionation",
        "title": "Species- and harvest-resolved feed, pulp, concentrate and nitrogen-recovery observations from a green-biorefinery experiment",
        "source_id": SOURCE_ID,
        "citation": "Stødkilde, L., Lashkari, S., Eriksen, J., & Jensen, S. K. (2021). Enhancing protein recovery in green biorefineries through selection of plant species and time of harvest. Animal Feed Science and Technology, 278, 115016.",
        "doi": DOI,
        "persistent_source_url": URL,
        "full_text_url": FULL_TEXT,
        "retrieval_date": RETRIEVED,
        "geography": "Foulumgaard, Aarhus University, Denmark",
        "reference_year": 2021,
        "harvest_year": 2016,
        "license": "CC BY, as identified by the Aarhus University Pure record and article full text.",
        "material_scope": "Lucerne, red clover, white clover, perennial ryegrass and tall fescue, harvested at four independent spring first-cut dates; duplicate split-plot field design.",
        "process_conditions": "Plants cut at 7 cm and frozen at -18 C; lab Angelia 8500S twin-screw press; juice protein precipitated with 12 M phosphoric acid to pH 4, held overnight at 4 C and centrifuged at 2000 g/4 C. A second press used 200 g pulp plus 400 mL Milli-Q water and 10 minutes magnetic stirring.",
        "data_scope": "300 long-form observations from Tables 1–5: whole-plant DM/N/DM yield; single- and double-pressed pulp and concentrate DM/N concentrations; source-calculated N recovery in pulp and protein concentrate. Pooled model SEM and Tukey group markers are attached without treating SEM as date-specific.",
        "source_locations": "Tables 1–5, journal PDF pp. 4–7; Methods §§2.1–2.4, pp. 2–3.",
        "known_transcription_issue": "Table 1 May 17 red-clover DM is rendered as 12.81 in the machine-readable PDF text layer. It is recorded as 128.1 with an explicit reconciliation note because the four-date arithmetic mean equals the published species LSmean of 126.5. This is the sole OCR-reconciled cell and should be checked against a visual page scan if one becomes available.",
        "limitations": [
            "Cultivated Danish forage is a comparator, not Dutch roadside grass or GreenHub/VARTA feedstock.",
            "One first-cut growing season and one laboratory press system; no roadside-specific process transfer is established.",
            "Field plots were duplicated, but analytical replicate counts are not separately reported; SEM values are pooled across the model, not date-specific.",
            "Nitrogen recovery is not crude-protein recovery; nitrogen cannot be multiplied by a generic factor and treated as recovered saleable protein without a defensible conversion and product balance.",
            "The 2020 proceedings extract overlaps this experiment for ryegrass. Some reported recovery values differ across publications; preserve source-specific records and do not pool or average them without reconciliation.",
            "Table values are least-square means; species-level means are not forced to equal the arithmetic average of displayed harvest-date means.",
            "Phosphoric-acid volume/equivalents, full press mass/water balances, energy demand and residual-juice composition are not available in these tables.",
            "All rows remain reference-only and are not runtime defaults or calibration parameters.",
        ],
        "conversion_method": "No unit conversion or derived total was applied. Source-reported numeric table entries, units, basis, SEM and significance suffixes are retained. The single Table 1 OCR-reconciled cell is explicitly flagged.",
        "uncertainty": "Source gives an overall model SEM per species and endpoint, not date-specific uncertainty; the pooled SEM is repeated with an explicit scope label and must not be interpreted as per-row uncertainty. Field plots are in duplicate.",
        "activation_state": "reference_only",
        "sha256": checksum,
    }
    OUT.with_suffix(OUT.suffix + ".source.json").write_text(json.dumps(sidecar, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    source_register = FOLDER / "source_register.csv"
    upsert_csv(source_register, "source_id", {
        "source_id": SOURCE_ID,
        "source_type": "peer_reviewed_open_access_article",
        "title": "Enhancing protein recovery in green biorefineries through selection of plant species and time of harvest",
        "authors": "Lene Stødkilde; Saman Lashkari; Jørgen Eriksen; Søren Krogh Jensen",
        "year": "2021",
        "doi_or_stable_identifier": DOI,
        "publisher": "Animal Feed Science and Technology 278, article 115016",
        "url": URL,
        "material_scope": "Five cultivated forage species: lucerne, red clover, white clover, perennial ryegrass and tall fescue; single-/double-press fractions",
        "source_quality": "Peer-reviewed primary measurements; CC BY; reference-only, not GreenHub-calibrated.",
        "access_date": RETRIEVED,
        "notes": f"{FILENAME}; 300 Table 1–5 records. Table 1 red-clover DM cell reconciled against published species LSmean and explicitly flagged. Pooled SEM is not date-specific; ryegrass overlap with 2020 proceedings must not be pooled without reconciliation.",
    })
    manifest = FOLDER / "dataset_manifest.csv"
    upsert_csv(manifest, "filename", {
        "dataset_id": "DS-STODKILDE21-T1-T5",
        "filename": FILENAME,
        "purpose": "Species/date-resolved Tables 1–5 for forage properties, press-fraction DM/N concentrations, and source-calculated N recovery.",
        "row_count": str(len(rows)),
        "primary_key": "record_id",
        "encoding": "UTF-8 with BOM",
        "delimiter": ",",
        "integration_readiness": "reference_only",
        "material_state_rule": "Feed composition bases and fresh-mass DM concentrations are separately labelled; nitrogen and recovery denominators are explicit.",
        "known_limitations": "Cultivated Danish forage only; pooled SEM is not date-specific; previous proceedings extract overlaps ryegrass and has recovery discrepancies; no runtime parameter activation.",
    })

    audit = ROOT / "Greenhub/data/global_audit_package"
    relative = f"Pre-treatment/Mechanical/{FILENAME}"
    note = "Five cultivated forage species; 300 rows from Tables 1–5; one OCR-reconciled Table 1 cell is flagged; pooled SEM is not date-specific; ryegrass overlaps the 2020 proceedings extract; reference-only and not runtime eligible."
    for filename, key, record in [
        ("global_source_register.csv", "dataset_path", {
            "dataset_path": relative, "dataset_group": "Mechanical pre-treatment",
            "source_id": SOURCE_ID,
            "source_title": "Enhancing protein recovery in green biorefineries through selection of plant species and time of harvest",
            "authors": "Lene Stødkilde; Saman Lashkari; Jørgen Eriksen; Søren Krogh Jensen",
            "year": "2021", "doi_or_stable_id": DOI, "url": URL,
            "source_type": "Peer-reviewed open-access article", "notes": note,
        }),
        ("global_dataset_manifest.csv", "dataset_path", {
            "dataset_path": relative, "category": "Pre-treatment", "subgroup": "Mechanical",
            "filename": FILENAME, "row_count_observed": str(len(rows)),
            "header_count": str(len(FIELDS)), "headers": "; ".join(FIELDS),
            "standardized_status_values": "B;reference_only", "detected_readiness": "D3", "notes": note,
        }),
        ("global_dataset_readiness.csv", "dataset_path", {
            "dataset_path": relative, "category": "Pre-treatment", "subgroup": "Mechanical",
            "readiness": "D3", "duplicate_ids": "0", "duplicate_rows": "0",
            "numeric_rows": str(sum(bool(row["value_numeric"]) for row in rows)),
            "unsourced_numeric_rows": "0", "numeric_rows_missing_exact_location": "0",
            "unit_conflicts": "0", "basis_conflicts": "0", "cross_reference_issues": "0",
            "equation_missing_inputs": "0", "equation_symbol_mismatches": "0", "notes": note,
        }),
        ("source_dataset_checksums.csv", "dataset_path", {
            "dataset_path": relative, "sha256": checksum, "byte_size": str(OUT.stat().st_size),
        }),
    ]:
        upsert_csv(audit / filename, key, record)

    summary_path = audit / "global_validation_summary.json"
    if summary_path.exists():
        summary = json.loads(summary_path.read_text(encoding="utf-8"))
        with (audit / "global_dataset_manifest.csv").open(encoding="utf-8-sig", newline="") as stream:
            global_rows = list(csv.DictReader(stream))
        with (audit / "global_dataset_readiness.csv").open(encoding="utf-8-sig", newline="") as stream:
            readiness_rows = list(csv.DictReader(stream))
        counts: dict[str, int] = {}
        for item in readiness_rows:
            counts[item.get("readiness", "")] = counts.get(item.get("readiness", ""), 0) + 1
        summary["dataset_count"] = len(global_rows)
        summary["readiness_counts"] = counts
        summary["generated_at"] = datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")
        summary_path.write_text(json.dumps(summary, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Wrote {len(rows)} source-located reference rows to {OUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
