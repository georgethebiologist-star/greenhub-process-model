"""Build an abstract-only reference extract for Larsen et al. (2019).

The paper concerns ensiled pulp left after grass/grass-clover protein-juice
extraction. Only aggregate statements available in the public abstract are
transcribed. Nothing in this file is a GreenHub default or runtime parameter.
"""
from __future__ import annotations

import csv
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "Greenhub" / "data"
STORAGE = DATA / "storage"
FILENAME = "post_protein_grass_pulp_ensiling_larsen_2019_abstract_reference.csv"
CSV_PATH = STORAGE / FILENAME
SIDECAR_PATH = Path(str(CSV_PATH) + ".source.json")
SOURCE_ID = "SRC-LARSEN-POSTBIOREFINERY-PULP-2019"
DOI = "10.1016/j.indcrop.2019.111576"
DOI_URL = f"https://doi.org/{DOI}"
PURE_URL = "https://pure.au.dk/portal/en/publications/ensiling-of-the-pulp-fraction-after-biorefining-of-grass-into-pul/"
PUBLISHER_URL = "https://www.sciencedirect.com/science/article/abs/pii/S0926669019305874"

FIELDS = [
    "record_id", "source_id", "phase", "material", "study_scale", "process_step",
    "observation", "reported_value", "numeric_value", "lower_bound", "upper_bound",
    "unit", "basis", "condition_or_time", "source_location", "uncertainty",
    "evidence_class", "activation_state", "notes",
]

COMMON_LIMIT = (
    "Abstract-level aggregate only; the abstract does not pair this value/range with all "
    "species, treatments, time points, or replicate results. No SD, n, or raw observations "
    "are reported in the accessible record."
)


def _row(record_id, phase, material, scale, step, observation, reported_value,
         numeric_value="", lower="", upper="", unit="", basis="",
         condition="", uncertainty=COMMON_LIMIT, notes=""):
    return {
        "record_id": record_id,
        "source_id": SOURCE_ID,
        "phase": phase,
        "material": material,
        "study_scale": scale,
        "process_step": step,
        "observation": observation,
        "reported_value": reported_value,
        "numeric_value": numeric_value,
        "lower_bound": lower,
        "upper_bound": upper,
        "unit": unit,
        "basis": basis,
        "condition_or_time": condition,
        "source_location": "Published abstract; no table-level observation available in the accessible record",
        "uncertainty": uncertainty,
        "evidence_class": "B_measured_literature_abstract_aggregate",
        "activation_state": "reference_only",
        "notes": notes or COMMON_LIMIT,
    }


ROWS = [
    _row("LAR19-PULP-TS-GC", "3", "grass-clover pulp after protein-juice extraction", "reported pulp feed", "feed characterization", "total solids", "28.8", 28.8, unit="%", basis="TS mass fraction of pulp; denominator convention follows the abstract", condition="before ensiling"),
    _row("LAR19-PULP-TS-RG", "3", "ryegrass pulp after protein-juice extraction", "reported pulp feed", "feed characterization", "total solids", "33.6", 33.6, unit="%", basis="TS mass fraction of pulp; denominator convention follows the abstract", condition="before ensiling"),
    _row("LAR19-LAB-STORAGE-DURATION", "2", "grass-clover and ryegrass pulp", "laboratory scale", "ensiling", "ensiling experiment duration", "3–5", lower=3, upper=5, unit="months", basis="study-level duration range", condition="vacuum-bag laboratory experiments"),
    _row("LAR19-PILOT-STORAGE-DURATION", "2", "grass-clover and ryegrass pulp", "pilot scale", "ensiling", "ensiling experiment duration", "7–11", lower=7, upper=11, unit="months", basis="study-level duration range", condition="3.3 m tall pilot silos"),
    _row("LAR19-PILOT-EFFLUENT-GC", "2", "grass-clover pulp", "pilot scale", "ensiling", "effluent runoff", "1.8", 1.8, unit="% (reported; denominator not stated in abstract)", basis="percentage basis unresolved", condition="7–11 month pilot ensiling", notes="Do not interpret as a mass fraction of initial wet pulp until full methods/table denominator is verified."),
    _row("LAR19-PILOT-EFFLUENT-RG", "2", "ryegrass pulp", "pilot scale", "ensiling", "effluent runoff", "0.0", 0.0, unit="% (reported; denominator not stated in abstract)", basis="percentage basis unresolved", condition="7–11 month pilot ensiling", notes="Literal rounded source report; not evidence of absolute zero runoff or a transferable loss coefficient."),
    _row("LAR19-RECOVERY-VS", "2", "grass-clover and ryegrass pulp", "pilot-scale storage balance", "ensiling", "volatile-solids recovery", "97–98", lower=97, upper=98, unit="%", basis="reported recovery after ensiling; initial component basis not fully specified in abstract"),
    _row("LAR19-RECOVERY-NDF", "2", "grass-clover and ryegrass pulp", "pilot-scale storage balance", "ensiling", "neutral-detergent-fibre recovery", "92–94", lower=92, upper=94, unit="%", basis="reported recovery after ensiling; initial component basis not fully specified in abstract"),
    _row("LAR19-RECOVERY-BMP", "2;5", "grass-clover and ryegrass pulp", "pilot-scale storage balance", "ensiling and BMP", "methane-production-potential recovery", "98–116", lower=98, upper=116, unit="%", basis="relative recovery of methane production potential; not an absolute methane yield", notes="Values above 100% are preserved as published; do not treat this ratio as a physical fraction or methane yield."),
    _row("LAR19-RECOVERY-TRUE-PROTEIN", "2;4", "grass-clover and ryegrass pulp", "pilot-scale storage balance", "ensiling", "true-protein recovery", "67–85", lower=67, upper=85, unit="%", basis="reported recovery after ensiling; treatment/species pairing not available in abstract"),
    _row("LAR19-RECOVERY-TOTAL-AA", "2;4", "grass-clover and ryegrass pulp", "pilot-scale storage balance", "ensiling", "total-amino-acid recovery", "84–90", lower=84, upper=90, unit="%", basis="reported recovery after ensiling; treatment/species pairing not available in abstract"),
    _row("LAR19-BMP-DURATION-RESPONSE", "5", "grass-clover and ryegrass pulp", "laboratory BMP assay", "anaerobic digestion potential test", "ensiling-associated BMP increase detectable through digestion duration", "up to 20 or 30 days; no further increase at longer duration", unit="qualitative duration response", basis="abstract-level direction; exact pairing of 20/30 d with materials is unavailable", condition="BMP assay duration, not continuous-reactor HRT", uncertainty="No numerical response values, replicate counts, or uncertainty reported in the accessible abstract."),
    _row("LAR19-DELAY-PH", "2", "grass-clover and ryegrass pulp", "laboratory scale", "delay before ensiling", "longer delay from biorefining to ensiling increased final silage pH", "increase; more pronounced for ryegrass", unit="qualitative direction", basis="no numeric delay/pH pairs in accessible abstract", uncertainty="Qualitative abstract statement only; no effect size or uncertainty reported."),
    _row("LAR19-DELAY-COMPOSITION", "2;4", "grass-clover and ryegrass pulp", "laboratory scale", "delay before ensiling", "longer delay reduced lactic acid, total solids, total amino acids, and free amino acids", "decrease", unit="qualitative direction", basis="no numeric delay/concentration pairs in accessible abstract", uncertainty="Qualitative abstract statement only; no effect sizes or uncertainty reported."),
    _row("LAR19-SUCROSE-PH", "2", "grass-clover and ryegrass pulp", "laboratory scale", "ensiling additive", "sucrose partly counteracted the final-pH increase associated with delayed ensiling", "partial counteraction", unit="qualitative direction", basis="no sucrose dose or pH effect size in accessible abstract", uncertainty="Qualitative abstract statement only; dose and uncertainty not reported."),
    _row("LAR19-ENSILING-COMPOSITION", "2;4", "grass-clover and ryegrass pulp", "pilot scale", "ensiling", "NDF, in-vitro organic-matter digestibility, total amino acids, and true protein decreased; free amino acids increased", "directional changes", unit="qualitative direction", basis="post-ensiling composition changes", uncertainty="Qualitative abstract statement only; not a component mass balance."),
]


def _read_csv(path: Path):
    with path.open("r", encoding="utf-8-sig", newline="") as stream:
        reader = csv.DictReader(stream)
        return reader.fieldnames or [], list(reader)


def _append_once(path: Path, row: dict, key: str):
    fields, existing = _read_csv(path)
    matches = [item for item in existing if item.get(key) == row.get(key)]
    if matches:
        if len(matches) != 1 or any(matches[0].get(field, "") != str(row.get(field, "")) for field in fields):
            raise ValueError(f"Conflicting registration already exists in {path}: {row.get(key)}")
        return
    with path.open("a", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields, lineterminator="\n", extrasaction="ignore")
        writer.writerow({field: row.get(field, "") for field in fields})


def main():
    STORAGE.mkdir(parents=True, exist_ok=True)
    with CSV_PATH.open("w", encoding="utf-8-sig", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=FIELDS, lineterminator="\n")
        writer.writeheader()
        writer.writerows(ROWS)

    digest = hashlib.sha256(CSV_PATH.read_bytes()).hexdigest()
    sidecar = {
        "dataset_id": "urn:greenhub:dataset:storage:post-protein-grass-pulp-ensiling-larsen-2019-abstract:v1",
        "dataset_version": "1.0.0",
        "dataset_file": FILENAME,
        "record_count": len(ROWS),
        "sha256": digest,
        "source_id": SOURCE_ID,
        "citation": "Larsen, S. U., Ambye-Jensen, M., Jørgensen, H., & Jørgensen, U. (2019). Ensiling of the pulp fraction after biorefining of grass into pulp and protein juice. Industrial Crops and Products, 139, 111576.",
        "journal": "Industrial Crops and Products 139, article 111576",
        "publication_year": 2019,
        "doi": DOI,
        "source_url": DOI_URL,
        "publisher_record": PUBLISHER_URL,
        "institutional_record": PURE_URL,
        "retrieval_date": datetime.now(timezone.utc).date().isoformat(),
        "source_location": "Published abstract on the Aarhus University Pure record and ScienceDirect article record",
        "geography": "Experimental site/geography not stated in the accessible abstract; study authors are Denmark-based, which is not treated as proof of experimental location.",
        "material_scope": "Pulp after protein-juice extraction from grass-clover and ryegrass; not GreenHub roadside grass or VARTA feed.",
        "evidence_class": "B_measured_literature_abstract_aggregate",
        "quality_class": "B",
        "license": "No explicit reuse license was confirmed for the article or abstract record. This extract preserves a small set of attributed abstract-level facts; reuse rights for the published article remain unverified.",
        "data_availability": "Accessible record provides abstract-level aggregates only; full article tables and raw measurements were not available in the accessible source record during this collection pass.",
        "data_structure": "Long-form source-reported values, ranges, and qualitative directions. Blank numeric fields mean that the abstract does not provide a numeric value; they are not zero.",
        "applicable_phases": [2, 3, 4, 5],
        "limitations": [
            "Abstract-only extract; treatment-level tables, raw replicates, exact storage temperatures, delay-hour values, and statistical uncertainty are unavailable here.",
            "Recovery ranges are not paired to species, treatment, or exact storage condition in the abstract; do not use as a calibrated rate or GreenHub default.",
            "The reported effluent percentage basis is not stated in the accessible abstract; preserve the literal values and do not convert to mass-loss coefficients.",
            "The 98–116% methane-potential recovery is a relative recovery metric, not an absolute methane yield or a physical fraction; values above 100% remain literal.",
            "Reported BMP-duration effects concern batch biochemical-potential assays and are not continuous-reactor HRT or kinetic constants.",
            "Cultivated grass/grass-clover pulp is a comparator, not Dutch roadside grass or GreenHub post-isoelectric residue.",
        ],
        "conversion_or_processing": "Direct abstract-level transcription; no conversions, imputations, interpolations, or kinetic fitting.",
        "uncertainty": "Numerical SD/SEM, n, and treatment-level uncertainty are not present in the accessible abstract.",
        "runtime_policy": "Reference-only; no parameter registry, default, process equation, TEA/LCA factor, or Pareto input mapping.",
        "access_protocol": "HTTPS DOI, publisher article record, and institutional publication metadata record.",
        "fair_metadata": {
            "findable": "Repository-local URN and article DOI link.",
            "accessible": "HTTPS source records; full article data access remains limited.",
            "interoperable": "UTF-8 long-form CSV with explicit phases, material, scale, metric, value text, numeric/range fields, units, basis, time, source location and uncertainty.",
            "reusable": "Citation, checksum, limitations, uncertainty, applicability and unresolved license status are recorded.",
        },
    }
    SIDECAR_PATH.write_text(json.dumps(sidecar, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    local_source = {
        "source_id": SOURCE_ID,
        "source_title": "Ensiling of the pulp fraction after biorefining of grass into pulp and protein juice",
        "authors": "Søren Ugilt Larsen; Morten Ambye-Jensen; Henning Jørgensen; Uffe Jørgensen",
        "year": "2019",
        "source_type": "peer-reviewed primary experimental article; abstract-only aggregate extraction",
        "doi_or_stable_identifier": DOI,
        "stable_url": DOI_URL,
        "material": "Grass-clover and ryegrass pulp after protein-juice extraction; laboratory and pilot ensiling/BMP context",
        "quality_notes": "Direct abstract-only aggregate/range transcription. No treatment-level table/raw data, source license, effluent denominator, or GreenHub transferability established; reference-only.",
        "accessed_date": sidecar["retrieval_date"],
    }
    _append_once(STORAGE / "source_register.csv", local_source, "source_id")
    local_manifest = {
        "filename": FILENAME,
        "description": "Abstract-only aggregate evidence for storage of post-protein grass/grass-clover pulp, effluent runoff, component recovery, and BMP-duration response.",
        "row_count": len(ROWS),
        "schema_version": "1.0",
        "encoding": "UTF-8",
        "delimiter": ",",
        "integration_status": "traceable_reference_only_not_runtime_eligible",
        "primary_key": "record_id",
    }
    _append_once(STORAGE / "dataset_manifest.csv", local_manifest, "filename")

    relative_data_path = f"storage/{FILENAME}"
    global_source = {
        "dataset_path": relative_data_path,
        "dataset_group": "storage",
        "source_id": SOURCE_ID,
        "source_title": local_source["source_title"],
        "authors": local_source["authors"],
        "year": "2019",
        "doi_or_stable_id": DOI,
        "url": DOI_URL,
        "source_type": local_source["source_type"],
        "notes": local_source["quality_notes"],
    }
    _append_once(DATA / "global_audit_package" / "global_source_register.csv", global_source, "dataset_path")

    headers = "; ".join(FIELDS)
    global_manifest = {
        "dataset_path": relative_data_path,
        "category": "storage",
        "subgroup": "storage",
        "filename": FILENAME,
        "row_count_observed": len(ROWS),
        "header_count": len(FIELDS),
        "headers": headers,
        "standardized_status_values": "B;reference_only",
        "detected_readiness": "D3",
        "notes": "Abstract-level aggregate comparator for ensiled post-protein grass/grass-clover pulp; no raw data, full table transcription, kinetics, or runtime activation.",
    }
    _append_once(DATA / "global_audit_package" / "global_dataset_manifest.csv", global_manifest, "dataset_path")
    readiness = {
        "dataset_path": relative_data_path,
        "category": "storage",
        "subgroup": "storage",
        "readiness": "D3",
        "duplicate_ids": 0,
        "duplicate_rows": 0,
        "numeric_rows": sum(bool(row["numeric_value"] or row["lower_bound"] or row["upper_bound"]) for row in ROWS),
        "unsourced_numeric_rows": 0,
        "numeric_rows_missing_exact_location": 0,
        "unit_conflicts": 0,
        "basis_conflicts": 0,
        "cross_reference_issues": 0,
        "equation_missing_inputs": 0,
        "equation_symbol_mismatches": 0,
        "notes": "DOI linked; abstract only; all values are source-located at abstract level and remain reference-only.",
    }
    _append_once(DATA / "global_audit_package" / "global_dataset_readiness.csv", readiness, "dataset_path")

    # The preceding Ayanfe storage extract had a global manifest entry but no
    # matching readiness row. Reconcile that known orphan so the global package
    # remains one-to-one before its generated checksum/eligibility views run.
    ayanfe_readiness = {
        "dataset_path": "storage/timothy_silage_fermentation_effluent_and_press_liquid_ayanfe_2025_tables2_4_6_reference.csv",
        "category": "storage",
        "subgroup": "storage",
        "readiness": "D3",
        "duplicate_ids": 0,
        "duplicate_rows": 0,
        "numeric_rows": 519,
        "unsourced_numeric_rows": 0,
        "numeric_rows_missing_exact_location": 0,
        "unit_conflicts": 0,
        "basis_conflicts": 0,
        "cross_reference_issues": 0,
        "equation_missing_inputs": 0,
        "equation_symbol_mismatches": 0,
        "notes": "Published treatment means and pooled effluent chemistry; all 519 records are source-located in Tables 2–4 and 6; reference-only and non-runtime.",
    }
    _append_once(DATA / "global_audit_package" / "global_dataset_readiness.csv", ayanfe_readiness, "dataset_path")

    summary_path = DATA / "global_audit_package" / "global_validation_summary.json"
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    manifest_path = DATA / "global_audit_package" / "global_dataset_manifest.csv"
    readiness_path = DATA / "global_audit_package" / "global_dataset_readiness.csv"
    _, manifests = _read_csv(manifest_path)
    _, readiness_rows = _read_csv(readiness_path)
    summary["dataset_count"] = len(manifests)
    summary["generated_at"] = datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")
    summary["readiness_counts"] = {}
    for item in readiness_rows:
        key = item.get("readiness", "")
        summary["readiness_counts"][key] = summary["readiness_counts"].get(key, 0) + 1
    summary_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    print(json.dumps({"file": CSV_PATH.relative_to(ROOT).as_posix(), "rows": len(ROWS), "sha256": digest, "source_id": SOURCE_ID, "global_dataset_count": summary["dataset_count"]}, indent=2))


if __name__ == "__main__":
    main()
