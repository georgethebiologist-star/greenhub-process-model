"""Build traceable, reference-only observations from Echers et al. (2026)."""
from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "Greenhub" / "data"
GROUP = DATA / "Protein recovery" / "Membrane"
AUDIT = DATA / "global_audit_package"
FILENAME = "clover_grass_membrane_stream_composition_and_conditions_echers_2026_reference.csv"
SOURCE_ID = "ECHERS-CLOVER-GRASSPILOT-MEMBRANE-2026"
DOI = "10.1039/D5FB00771B"
DOI_URL = f"https://doi.org/{DOI}"
RETRIEVED = "2026-11-08"

FIELDS = [
    "record_id", "source_id", "phase", "experiment_id", "stage", "stream",
    "material", "geography", "trial_scale", "record_type", "metric",
    "reported_value", "numeric_value", "lower_bound", "upper_bound", "unit",
    "basis", "reported_uncertainty", "sample_count", "replication_context",
    "process_condition", "source_location", "evidence_class", "quality_class",
    "activation_state", "applicability", "limitations",
]

SOURCE_TITLE = (
    "Selective removal of green pigments and associated proteins from clover-grass "
    "protein concentrates: molecular insights into a non-destructive, two-stage "
    "membrane-based biorefinery concept for high-quality food protein production"
)
AUTHORS = (
    "Simon Gregersen Echers; Naim Abdul-Khalek; Nete Hassing Jensen; "
    "Anders Kjær Jørgensen; Tuve Mattsson; Mads Koustrup Jørgensen; "
    "Peter Stephensen Lübeck; Mette Lübeck"
)
GEO = "Denmark; study location 57°02′16.5″N, 9°58′42.4″E"
MATERIAL = (
    "Cultivated clover-grass blend (commercial Seed Mix 35; 13% white-clover and "
    "87% perennial-ryegrass seed blend; red clover was also observed in the field)"
)
LIMITS = (
    "One reported pilot batch of cultivated Danish clover-grass, not Dutch roadside "
    "grass. No paired stream mass flows or closed water/dry-matter/protein balance; "
    "do not infer recovery from concentration ratios. Reference-only; no GreenHub "
    "default, parameter, equation, TEA, LCA, or Pareto connection. Article is CC BY-NC "
    "3.0; non-commercial reuse restriction must be reviewed before commercial reuse."
)


def row(
    record_id: str,
    phase: str,
    stage: str,
    stream: str,
    record_type: str,
    metric: str,
    reported_value: str,
    numeric_value: str = "",
    unit: str = "",
    basis: str = "",
    uncertainty: str = "not reported",
    sample_count: str = "",
    replication: str = "",
    condition: str = "",
    source_location: str = "",
    material: str = MATERIAL,
    applicability: str = "Literature comparator for Phases 1–4 only; not directly transferable to GreenHub roadside-grass feed.",
    lower: str = "",
    upper: str = "",
) -> dict[str, str]:
    return {
        "record_id": record_id,
        "source_id": SOURCE_ID,
        "phase": phase,
        "experiment_id": "ECHERS-W33-2022-PILOT-BATCH",
        "stage": stage,
        "stream": stream,
        "material": material,
        "geography": GEO,
        "trial_scale": "pilot batch; study reports 15 kg crude harvested leaves",
        "record_type": record_type,
        "metric": metric,
        "reported_value": reported_value,
        "numeric_value": numeric_value,
        "lower_bound": lower,
        "upper_bound": upper,
        "unit": unit,
        "basis": basis,
        "reported_uncertainty": uncertainty,
        "sample_count": sample_count,
        "replication_context": replication,
        "process_condition": condition,
        "source_location": source_location,
        "evidence_class": "B_primary_literature_measurement_or_method",
        "quality_class": "B",
        "activation_state": "reference_only",
        "applicability": applicability,
        "limitations": LIMITS + (
            " DF C is a liquid diafiltered concentrate, not a dried product or packaged powder."
            if stream == "DF C" else ""
        ),
    }


ROWS: list[dict[str, str]] = []


def add_composition(stream: str, dm: str | None, dm_sd: str | None, cp: str | None, cp_sd: str | None) -> None:
    phase = "1" if stream == "Biomass" else "3" if stream == "Raw juice" else "4"
    if dm is not None:
        ROWS.append(row(
            f"ECHERS26-{stream.upper().replace(' ', '-')}-DM", phase, "feed characterization / fractionation",
            stream, "measured_stream_property", "dry_matter_content", dm, dm, "% wet mass",
            "mass of dry residue / wet stream mass × 100; gravimetric overnight at 105 °C",
            f"SD {dm_sd} percentage points", "2",
            "Table 1 reports mean ± SD, n=2. One pilot batch; these are not independent process-batch replicates.",
            "No stream flow is supplied; concentration is not a mass recovery.", "Table 1; Methods 2.2.1",
            applicability="Cultivated Danish clover-grass comparator for Phase 1 feed-state and Phase 3/4 stream-composition evidence; reference-only.",
        ))
    else:
        ROWS.append(row(
            f"ECHERS26-{stream.upper().replace(' ', '-')}-DM", phase, "fractionation stream characterization",
            stream, "not_reported", "dry_matter_content", "not recorded", unit="% wet mass",
            basis="Table footnote states this stream was not analyzed for DM.", sample_count="",
            replication="Not measured/reported; do not impute.", source_location="Table 1 footnote",
        ))
    if cp is not None:
        ROWS.append(row(
            f"ECHERS26-{stream.upper().replace(' ', '-')}-CP", phase, "feed characterization / fractionation",
            stream, "measured_stream_property", "crude_protein_content", cp, cp, "% dry matter",
            "Crude protein = total N × 6.25; denominator is stream dry matter",
            f"SD {cp_sd} percentage points", "2",
            "Table 1 reports mean ± SD, n=2. The paper describes duplicate CP determinations; not independent process-batch replicates.",
            "CP is N×6.25, not a directly measured protein recovery.", "Table 1; Methods 2.2.1",
            applicability="Cultivated Danish clover-grass comparator for Phase 1 feed-state and Phase 3/4 stream-composition evidence; reference-only.",
        ))
    else:
        ROWS.append(row(
            f"ECHERS26-{stream.upper().replace(' ', '-')}-CP", phase, "fractionation stream characterization",
            stream, "not_reported", "crude_protein_content", "not recorded", unit="% dry matter",
            basis="Table footnote states this stream was not analyzed for crude protein.", sample_count="",
            replication="Not measured/reported; do not impute.", source_location="Table 1 footnote",
        ))


# Table 1: transcribed as reported; no concentration-to-recovery conversions.
for values in [
    ("Biomass", "14.20", "2.15", "24.97", "0.74"),
    ("Raw juice", "3.42", "0.02", "20.62", "0.36"),
    ("S1 feed", "3.36", "0.02", "20.46", "0.05"),
    ("S1 ret", "5.48", "0.01", "38.73", "0.67"),
    ("S1 perm", "2.37", "0.35", "10.33", "0.20"),
    ("S2 ret", "2.14", "0.00", "21.05", "0.87"),
    ("S2 perm", None, None, None, None),
    ("DF perm", None, None, None, None),
    ("DF C", "0.48", "0.00", "57.70", "0.86"),
]:
    add_composition(*values)


def add_condition(record_id: str, phase: str, stage: str, stream: str, metric: str,
                  value: str, numeric: str = "", unit: str = "", basis: str = "",
                  source_location: str = "Methods 2.1", condition: str = "") -> None:
    ROWS.append(row(
        record_id, phase, stage, stream, "reported_operating_condition", metric,
        value, numeric, unit, basis, "not reported", "",
        "Single pilot-batch method; no repeatability/uncertainty reported for this setting.",
        condition, source_location,
        applicability="Source-specific comparator only. Do not treat as a GreenHub design setpoint without route, scale, feed, and equipment validation.",
    ))


# Phase 1 feed identity, handling, and wet-basis batch observations.
add_condition("ECHERS26-SEED-MIX-WHITE-CLOVER", "1", "feed description", "harvested biomass",
              "white_clover_seed_mix_fraction", "13", "13", "% seed blend",
              "Commercial Seed Mix 35 specification, not measured harvested species fraction.",
              "Methods 2.1; field also contained observed red clover")
add_condition("ECHERS26-SEED-MIX-RYEGRASS", "1", "feed description", "harvested biomass",
              "perennial_ryegrass_seed_mix_fraction", "87", "87", "% seed blend",
              "Commercial Seed Mix 35 specification, not measured harvested species fraction.",
              "Methods 2.1; field also contained observed red clover")
add_condition("ECHERS26-CRUDE-HARVEST-MASS", "1", "harvest", "harvested leaves",
              "crude_harvested_leaf_mass", "15", "15", "kg batch^-1",
              "Crude leaf mass as reported; do not infer a general yield or area-based yield.")
add_condition("ECHERS26-HARVEST-DRY-MASS", "1", "harvest", "harvested leaves",
              "harvested_leaf_dry_mass", "2.1", "2.1", "kg DM batch^-1",
              "Study-reported batch dry mass; do not infer annual/area yield.")
add_condition("ECHERS26-HARVEST-TO-PROCESS", "1", "feed handling", "harvested leaves",
              "harvest_to_processing_time", "within 1", "1", "h",
              "Reported as processed within one hour; upper bound only, exact elapsed time not reported.")

# Phase 3 screw pressing and Phase 4 membrane separation.
add_condition("ECHERS26-STABILIZER-RATIO", "3", "slurry preparation", "biomass plus stabilizing solution",
              "reported_biomass_stabilizer_mass_ratio", "1:2 (w/w)", "", "w/w ratio",
              "Article gives ratio text but not unambiguously which material is numerator. Stored verbatim; no dilution ratio inferred.")
add_condition("ECHERS26-SHREDDING-DURATION", "3", "size reduction", "slurry feed",
              "shredding_duration", "minimum 5", "5", "min", "Lower bound; blender power is described as maximum but no wattage is given.")
add_condition("ECHERS26-SHREDDING-TEMPERATURE", "3", "size reduction", "slurry feed",
              "shredding_temperature", "20", "20", "°C", "Reported operating temperature during shredding.")
add_condition("ECHERS26-SCREW-PRESS-SPEED", "3", "wet fractionation", "clover-grass slurry",
              "screw_press_speed", "3.3", "3.3", "rpm", "KP6 screw press, source-reported rotational speed.")
add_condition("ECHERS26-SCREW-PRESS-COUNTERPRESSURE", "3", "wet fractionation", "clover-grass slurry",
              "screw_press_counterpressure", "4", "4", "bar", "KP6 screw press counterpressure.")
add_condition("ECHERS26-STRAINER-OPENING", "3", "wet fractionation", "clover-grass slurry",
              "screw_press_strainer_opening", "1 × 1", "", "mm × mm", "Strainer hole size as reported.")
add_condition("ECHERS26-S1-MEMBRANE-PORE", "4", "first membrane stage", "S1 feed",
              "nominal_membrane_pore_size", "60", "60", "nm", "Ceramic HTM membrane.")
add_condition("ECHERS26-S1-CROSSFLOW", "4", "first membrane stage", "S1 feed",
              "crossflow_velocity", "3", "3", "m s^-1", "Do not confuse with second-stage volumetric crossflow.")
add_condition("ECHERS26-S1-TMP", "4", "first membrane stage", "S1 feed",
              "transmembrane_pressure", "0.3–0.4", "", "bar", "Quasi-constant source-reported range; filtration stopped at VCF 4.7.")
add_condition("ECHERS26-S1-VCF", "4", "first membrane stage", "S1 feed",
              "volume_concentration_factor", "4.7", "4.7", "dimensionless", "Endpoint for first-stage filtration.")
add_condition("ECHERS26-S2-MEMBRANE-MWCO", "4", "second membrane stage", "S1 permeate",
              "nominal_molecular_weight_cutoff", "10", "10", "kDa", "Polymeric PES membrane.")
add_condition("ECHERS26-S2-TMP", "4", "second membrane stage", "S1 permeate",
              "transmembrane_pressure", "2", "2", "bar", "Second-stage filtration stopped at VCF 4.6.")
add_condition("ECHERS26-S2-VCF", "4", "second membrane stage", "S1 permeate",
              "volume_concentration_factor", "4.6", "4.6", "dimensionless", "Endpoint for second-stage filtration.")
add_condition("ECHERS26-DF-FACTOR", "4", "diafiltration", "S2 retentate",
              "diafiltration_factor", "9.8", "9.8", "diafiltration volume / permeate volume",
              "Source-defined diafactor; not a directly reported water mass or net water consumption.")
add_condition("ECHERS26-S2-DF-CROSSFLOW", "4", "second membrane stage and diafiltration", "membrane rig",
              "volumetric_crossflow", "approximately 2.9", "2.9", "m^3 h^-1",
              "Volumetric crossflow during second-stage filtration and subsequent diafiltration; not membrane flux.")

# Pigment concentrations explicitly reported in Results. Do not infer component recovery.
for stream, value in [
    ("Raw juice", "7.7"),
    ("S1 ret", "77"),
    ("S1 perm", "0.27"),
    ("S2 ret", "0.20"),
    ("DF C", "0.009"),
]:
    ROWS.append(row(
        f"ECHERS26-{stream.upper().replace(' ', '-')}-TOTAL-PIGMENT", "3" if stream == "Raw juice" else "4",
        "wet fractionation and membrane purification", stream, "measured_stream_property",
        "total_chlorophylls_and_carotenoids", value, value, "µg g^-1 DM",
        "Sum of chlorophyll a, chlorophyll b, and total carotenoids, relative to stream DM; source text values.",
        "uncertainty not reported for the text-extracted value", "3",
        "Methods state all streams were analyzed in triplicate; no numeric SD for these text-extracted values.",
        "Acetone extraction and UV/Vis; source notes pigment quantification in S2 permeate and DF permeate was unreliable.",
        "Results 3.1; Fig. 1B; Methods 2.2.3",
        applicability="Study-specific pigment partition/concentration comparator; stream concentrations alone do not give mass recovery.",
    ))

for record_id, metric, value, basis in [
    ("ECHERS26-S1-PIGMENT-DEPLETION", "total_pigment_depletion_S1_feed_to_S1_permeate", "96", "Source-reported relative decrease in pigment concentration; not a mass-based removal efficiency."),
    ("ECHERS26-OVERALL-PIGMENT-DEPLETION", "total_pigment_depletion_S1_feed_to_DF_C", "99.9", "Source-reported overall concentration depletion; not a mass-based recovery/removal because paired stream flow is unavailable."),
]:
    ROWS.append(row(
        record_id, "4", "membrane purification", "S1 feed to downstream stream",
        "reported_comparison", metric, value, value, "%", basis,
        "No uncertainty stated for the text-reported percentage", "3",
        "Pigment assays were performed in triplicate; no numeric SD for this text-extracted comparison.",
        "Concentration comparison only; paired stream mass flows not supplied.",
        "Results 3.1",
        applicability="Reported study comparison only; must not be interpreted as an overall component mass balance.",
    ))


def read_csv(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        return list(reader.fieldnames or []), list(reader)


def write_csv(path: Path, fields: list[str], rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def append_once(path: Path, row_data: dict[str, str], key: str) -> None:
    fields, rows = read_csv(path)
    existing = [item for item in rows if item.get(key) == row_data.get(key)]
    if existing:
        if len(existing) != 1 or any(existing[0].get(k, "") != v for k, v in row_data.items()):
            raise ValueError(f"Conflicting pre-existing {key}={row_data.get(key)!r} in {path}")
        return
    write_csv(path, fields, [*rows, row_data])


def main() -> None:
    csv_path = GROUP / FILENAME
    write_csv(csv_path, FIELDS, ROWS)
    checksum = hashlib.sha256(csv_path.read_bytes()).hexdigest()
    source_url = "https://pubs.rsc.org/en/content/articlehtml/2026/fb/d5fb00771b"
    fulltext_pdf = "https://pubs.rsc.org/en/content/articlepdf/2026/fb/d5fb00771b"
    supplementary_pdf = "https://www.rsc.org/suppdata/d5/fb/d5fb00771b/d5fb00771b1.pdf"
    sidecar = {
        "dataset_id": "urn:greenhub:dataset:protein-recovery:echers-clover-grass-membrane-2026:v1",
        "persistent_identifier_status": "Repository-local stable dataset identifier; source DOI and publisher-hosted article/SI URLs recorded.",
        "dataset_version": "1.0.0",
        "source_file": FILENAME,
        "source_file_sha256": checksum,
        "source_id": SOURCE_ID,
        "title": "Clover-grass pilot membrane stream composition, pigment observations and operating conditions",
        "citation": "Echers, S. G., Abdul-Khalek, N., Jensen, N. H., Jørgensen, A. K., Mattsson, T., Jørgensen, M. K., Lübeck, P. S., & Lübeck, M. (2026). Selective removal of green pigments and associated proteins from clover-grass protein concentrates: molecular insights into a non-destructive, two-stage membrane-based biorefinery concept for high-quality food protein production. Sustainable Food Technology, 4, 1689–1713. https://doi.org/10.1039/D5FB00771B",
        "persistent_identifier": f"doi:{DOI}",
        "source_url": DOI_URL,
        "publisher_article_url": source_url,
        "publisher_fulltext_pdf_url": fulltext_pdf,
        "publisher_supplementary_information_url": supplementary_pdf,
        "retrieval_date": RETRIEVED,
        "reference_year": 2026,
        "experiment_year": 2022,
        "geography": GEO,
        "source_locations": ["Methods 2.1–2.2.3; Table 1; Results 3.1; Figure 1B"],
        "evidence_class": "B_primary_literature_measurement_and_reported_process_conditions",
        "license": "Creative Commons Attribution-NonCommercial 3.0 Unported (CC BY-NC 3.0), as stated by the publisher. Redistribution and any commercial reuse must comply with this restriction; this extract contains factual observations and method values only, not article text or figures.",
        "material_scope": "One pilot batch of cultivated Danish clover-grass. Seed Mix 35 was specified as 13% white clover and 87% perennial ryegrass; red clover was also observed. It is not roadside grass and is not the GreenHub isoelectric-precipitation route.",
        "data_scope": f"{len(ROWS)} structured records: stream DM and CP including explicit not-reported entries, selected pilot handling/press/membrane conditions, text-reported total pigment concentrations and reported concentration-depletion comparisons.",
        "experimental_context": {
            "harvest_date": "2022-08-15",
            "feed_handling": "15 kg crude harvested leaves (2.1 kg DM) processed within one hour; processing batch is not a seasonal yield measurement.",
            "wet_fractionation": "Stabilizing solution ratio reported as 1:2 w/w without unambiguous numerator orientation; shredded at 20 °C for at least 5 min; KP6 screw press at 3.3 rpm and 4 bar counterpressure; strainer holes 1 × 1 mm.",
            "membrane_conditions": "S1: ceramic 60 nm membrane, crossflow velocity 3 m/s, TMP 0.3–0.4 bar, VCF 4.7. S2: 10 kDa polymeric PES, 2 bar TMP, VCF 4.6; diafiltration factor 9.8; second-stage/DF volumetric crossflow approximately 2.9 m³/h.",
            "analytical_basis": "DM gravimetric; CP estimated as total N × 6.25; Table 1 gives mean ± SD, n=2. Pigment analysis by acetone extraction/UV-Vis; methods report triplicate analyses.",
        },
        "conversion_or_processing": "Values transcribed as reported. No conversion, stream-flow reconstruction, component recovery, water balance, annualization, scale-up, or transfer factor was applied. Text-reported ratios and ambiguous settings are retained verbatim.",
        "uncertainty": "Table 1 reports SD with n=2; the process-batch independence of those analytical replicates is not established. Pigment text values have no numeric SD in the extracted result. Operating conditions are from one pilot batch and lack repeatability estimates.",
        "limitations": [
            "Concentrations cannot establish component recovery without paired stream flow or mass data; no such balance is supplied by this extract.",
            "DF C is a liquid concentrate measured at 0.48% DM, not a dried powder or final packaged product.",
            "S2 permeate and diafiltration permeate DM and CP are explicitly not reported; no imputation was made.",
            "The 1:2 biomass/stabilizer ratio orientation is not resolved from the article text and is stored verbatim.",
            "The trial is one cultivated Danish clover-grass batch, not roadside feed, a seasonal supply dataset, or an independently replicated plant campaign.",
            "This membrane train differs from GreenHub's baseline precipitation route. No route substitution, parameter activation, or product recovery coefficient is inferred.",
            "The article has a CC BY-NC 3.0 license. Commercial reuse requires a rights review.",
            "The article reports a related patent and author-company relationships; this is disclosed as context, not an adjustment to the measurements.",
        ],
        "activation_state": "reference_only",
        "calculation_connected": False,
        "runtime_parameter_mapping": None,
        "fair_metadata": {
            "findable": "Local persistent dataset identifier, source ID, DOI, publisher article and SI URLs, and SHA-256 recorded.",
            "accessible": "UTF-8 CSV and JSON sidecar; primary source linked over HTTPS.",
            "interoperable": "Long-form records expose phase, process stage, stream, metric, value, unit, basis, uncertainty, exact source location, evidence class and activation state.",
            "reusable": "Reproducible builder, explicit missingness, replicate limits, rights, non-transferability, and no-runtime-use policy recorded.",
        },
    }
    (GROUP / FILENAME.replace(".csv", ".source.json")).write_text(
        json.dumps(sidecar, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    validation_path = GROUP / "validation_report.json"
    validation = json.loads(validation_path.read_text(encoding="utf-8"))
    validation["csv_files_checked"] = len(list(GROUP.glob("*.csv")))
    validation_path.write_text(json.dumps(validation, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    append_once(GROUP / "source_register.csv", {
        "source_id": SOURCE_ID,
        "source_title": SOURCE_TITLE,
        "authors": AUTHORS,
        "year": "2026",
        "source_type": "peer-reviewed primary experimental article",
        "doi_or_stable_id": DOI,
        "source_url": DOI_URL,
        "materials": "Cultivated Danish clover-grass blend; not roadside grass",
        "key_use": "Phase 1 stream composition; Phase 3 screw-press conditions; Phase 4 membrane conditions and stream quality",
        "limitations": "One pilot batch; no closed stream balance or recoveries; reference-only; CC BY-NC 3.0; no runtime activation.",
    }, "source_id")
    append_once(GROUP / "dataset_manifest.csv", {
        "filename": FILENAME,
        "scope": "Echers et al. clover-grass pilot stream composition, pigment and operating-condition observations",
        "row_count": str(len(ROWS)),
        "validation_status": "PASS",
        "integration_readiness": "reference_only",
    }, "filename")

    relative_path = f"Protein recovery/Membrane/{FILENAME}"
    append_once(AUDIT / "global_source_register.csv", {
        "dataset_path": relative_path,
        "dataset_group": "Membrane",
        "source_id": SOURCE_ID,
        "source_title": SOURCE_TITLE,
        "authors": AUTHORS,
        "year": "2026",
        "doi_or_stable_id": DOI,
        "url": DOI_URL,
        "source_type": "peer-reviewed primary experimental article; direct Table 1, Methods and Results extract",
        "notes": "Phase 1/3/4 cultivated-clover-grass pilot comparator. One batch, no closed material balance; reference-only and CC BY-NC 3.0.",
    }, "dataset_path")
    append_once(AUDIT / "global_dataset_manifest.csv", {
        "dataset_path": relative_path,
        "category": "Protein recovery",
        "subgroup": "Membrane",
        "filename": FILENAME,
        "row_count_observed": str(len(ROWS)),
        "header_count": str(len(FIELDS)),
        "headers": "; ".join(FIELDS),
        "standardized_status_values": "B;reference_only",
        "detected_readiness": "D3",
        "notes": "Source-located table, method and result observations; includes not-reported stream data; no stream-flow balance or runtime link.",
    }, "dataset_path")
    numeric_rows = sum(bool(item["numeric_value"]) for item in ROWS)
    not_reported_rows = sum(item["record_type"] == "not_reported" for item in ROWS)
    append_once(AUDIT / "global_dataset_readiness.csv", {
        "dataset_path": relative_path,
        "category": "Protein recovery",
        "subgroup": "Membrane",
        "readiness": "D3",
        "duplicate_ids": "0",
        "duplicate_rows": "0",
        "numeric_rows": str(numeric_rows),
        "unsourced_numeric_rows": "0",
        "numeric_rows_missing_exact_location": "0",
        "unit_conflicts": "0",
        "basis_conflicts": "0",
        "cross_reference_issues": "0",
        "equation_missing_inputs": "0",
        "equation_symbol_mismatches": "0",
        "notes": f"{numeric_rows} numeric records, {not_reported_rows} explicit not-reported composition records. Pilot comparator only; concentration is not recovery; CC BY-NC 3.0; reference-only.",
    }, "dataset_path")

    summary_path = AUDIT / "global_validation_summary.json"
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    _, manifests = read_csv(AUDIT / "global_dataset_manifest.csv")
    _, readiness = read_csv(AUDIT / "global_dataset_readiness.csv")
    summary["dataset_count"] = len(manifests)
    counts: dict[str, int] = {}
    for item in readiness:
        status = item.get("readiness", "")
        counts[status] = counts.get(status, 0) + 1
    summary["readiness_counts"] = counts
    summary["generated_at"] = "2026-11-08T00:00:00Z"
    summary_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"dataset": relative_path, "rows": len(ROWS), "numeric_rows": numeric_rows, "sha256": checksum}, indent=2))


if __name__ == "__main__":
    main()
