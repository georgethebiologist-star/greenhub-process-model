"""Record abstract-level screw-press protein-partition ranges from Damborg (2019).

The ranges are kept as ranges and are not converted into model coefficients.
"""
from __future__ import annotations

import csv
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
FOLDER = ROOT / "Greenhub/data/Pre-treatment/Mechanical"
CSV_PATH = FOLDER / "damborg_2019_thesis_press_protein_partition_ranges_reference.csv"
SIDECAR_PATH = CSV_PATH.with_suffix(".source.json")
SOURCE_ID = "SRC-DAMBORG-GREEN-BIOREFINERY-THESIS-2019"
TITLE = "Green biorefinery - characterisation and utilisation of the pulp fraction from extraction of green protein from grassland plants"
AUTHORS = "Vinni Kragbæk Damborg"
SOURCE_URL = "https://pure.au.dk/portal/en/publications/green-biorefinery-characterisation-and-utilisation-of-the-pulp-fr/"
RETRIEVED = "2026-11-08"

FIELDS = [
    "record_id", "phase_relevance", "experiment", "material", "process_step",
    "metric", "reported_value", "lower_bound", "upper_bound", "unit", "basis",
    "range_scope", "operating_conditions", "replicate_count", "uncertainty",
    "source_id", "source_location", "evidence_class", "quality_class",
    "activation_state", "transferability", "limitations",
]

ROWS = [
    {
        "record_id": "DAMBORG19-CP-MASS-TO-PULP",
        "phase_relevance": "3;4",
        "experiment": "Trial I; four common Danish grassland crops; source-reported aggregate range",
        "material": "White clover, red clover, lucerne and perennial ryegrass",
        "process_step": "Screw pressing; fibrous pulp fraction",
        "metric": "crude_protein_mass_recovered_in_pulp",
        "reported_value": "528–669",
        "lower_bound": "528",
        "upper_bound": "669",
        "unit": "g/kg input crude protein",
        "basis": "mass of crude protein in pulp per mass of crude protein in unprocessed input",
        "range_scope": "Range reported in thesis abstract across Trial I; not a confidence interval and not paired to species in the abstract.",
        "operating_conditions": "Four forage crops fractionated in a green biorefinery screw press; exact press settings and individual treatment pairing not available in the abstract.",
        "replicate_count": "Not stated in abstract",
        "uncertainty": "Range only; no SD, SE or confidence interval stated.",
        "source_location": "Aarhus University Pure thesis record, abstract, Trial I summary",
        "limitations": "Comparator from cultivated Danish forages; not roadside/VARTA grass. Do not interpret endpoints as one common treatment balance or as a GreenHub recovery coefficient.",
    },
    {
        "record_id": "DAMBORG19-CP-MASS-TO-CONCENTRATE",
        "phase_relevance": "3;4",
        "experiment": "Trial I; four common Danish grassland crops; source-reported aggregate range",
        "material": "Green protein concentrate from white clover, red clover, lucerne and perennial ryegrass",
        "process_step": "Protein concentration after screw pressing",
        "metric": "crude_protein_mass_recovered_in_protein_concentrate",
        "reported_value": "170–261",
        "lower_bound": "170",
        "upper_bound": "261",
        "unit": "g/kg input crude protein",
        "basis": "mass of crude protein recovered in concentrate per mass of crude protein in unprocessed input",
        "range_scope": "Range reported in thesis abstract across Trial I; not a confidence interval and not paired to species in the abstract.",
        "operating_conditions": "Protein extraction from four forage crops; abstract does not resolve the individual precipitation route or treatment for each range endpoint.",
        "replicate_count": "Not stated in abstract",
        "uncertainty": "Range only; no SD, SE or confidence interval stated.",
        "source_location": "Aarhus University Pure thesis record, abstract, Trial I summary",
        "limitations": "Comparator from cultivated Danish forages; not roadside/VARTA grass. Range is not the complement of pulp recovery; unreported protein may remain in juice/residual streams or reflect other balance terms.",
    },
    {
        "record_id": "DAMBORG19-RUP-PULP",
        "phase_relevance": "3;4",
        "experiment": "Trial II; source-reported aggregate range",
        "material": "Pulp from mechanically fractionated grassland crops",
        "process_step": "Screw-press pulp; protein rumen degradability assessment",
        "metric": "rumen_undegraded_protein_in_pulp",
        "reported_value": "353–421",
        "lower_bound": "353",
        "upper_bound": "421",
        "unit": "g/kg protein",
        "basis": "rumen-undegraded protein per total protein in pulp, as summarized by the thesis abstract",
        "range_scope": "Source-reported crop/treatment range; not a confidence interval.",
        "operating_conditions": "Abstract states protein passing the rumen undegraded and potentially digestible in the intestine; assay method and species-specific values not stated in the abstract.",
        "replicate_count": "Not stated in abstract",
        "uncertainty": "Range only; no SD, SE or confidence interval stated.",
        "source_location": "Aarhus University Pure thesis record, abstract, Trial II summary",
        "limitations": "Animal-feed digestibility endpoint, not protein mass recovery, product purity, or process conversion. Cultivated forage comparator only.",
    },
    {
        "record_id": "DAMBORG19-RUP-RAW-FORAGE",
        "phase_relevance": "1;3",
        "experiment": "Trial II; source-reported aggregate range",
        "material": "Unprocessed grassland forage",
        "process_step": "Feedstock comparator; protein rumen degradability assessment",
        "metric": "rumen_undegraded_protein_in_unprocessed_forage",
        "reported_value": "214–343",
        "lower_bound": "214",
        "upper_bound": "343",
        "unit": "g/kg protein",
        "basis": "rumen-undegraded protein per total protein in unprocessed forage, as summarized by the thesis abstract",
        "range_scope": "Source-reported crop/treatment range; not a confidence interval.",
        "operating_conditions": "Abstract states protein passing the rumen undegraded and potentially digestible in the intestine; assay method and species-specific values not stated in the abstract.",
        "replicate_count": "Not stated in abstract",
        "uncertainty": "Range only; no SD, SE or confidence interval stated.",
        "source_location": "Aarhus University Pure thesis record, abstract, Trial II summary",
        "limitations": "Animal-feed digestibility endpoint, not a direct protein extraction parameter. Cultivated forage comparator only; not roadside/VARTA grass.",
    },
]


def _read_csv(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    with path.open(encoding="utf-8-sig", newline="") as stream:
        reader = csv.DictReader(stream)
        return list(reader.fieldnames or []), list(reader)


def _write_csv(path: Path, fields: list[str], rows: list[dict[str, str]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def _upsert(path: Path, record: dict[str, str], key: str) -> None:
    fields, rows = _read_csv(path)
    existing = next((row for row in rows if row.get(key) == record[key]), None)
    if existing is None:
        rows.append(record)
    else:
        existing.update(record)
    _write_csv(path, fields, rows)


def _update_local_registers() -> None:
    _upsert(FOLDER / "source_register.csv", {
        "source_id": SOURCE_ID,
        "source_type": "University PhD thesis; abstract-level primary research summary",
        "title": TITLE,
        "authors": AUTHORS,
        "year": "2019",
        "doi_or_stable_identifier": "No DOI identified; Aarhus University Pure publication record",
        "publisher": "Aarhus University",
        "url": SOURCE_URL,
        "material_scope": "Four common Danish grassland crops and their screw-pressed fractions; cultivated feedstock comparator",
        "source_quality": "Primary doctoral thesis; only abstract-level ranges transcribed here. No explicit reuse license identified.",
        "access_date": RETRIEVED,
        "notes": "Four source-reported ranges from Trial I/II; no species pairing, replicate count or statistical uncertainty in the accessible abstract.",
    }, "source_id")
    _upsert(FOLDER / "dataset_manifest.csv", {
        "dataset_id": "DS-DAMBORG19-PROTEIN-PARTITION-RANGES",
        "filename": CSV_PATH.name,
        "purpose": "Thesis-abstract ranges for crude-protein partition to pulp/concentrate and rumen-undegraded protein in pulp/raw forage; reference-only.",
        "row_count": str(len(ROWS)),
        "primary_key": "record_id",
        "encoding": "UTF-8",
        "delimiter": ",",
        "integration_readiness": "reference_only_D3",
        "material_state_rule": "All values retain source-reported protein-mass or protein-mass fraction basis; ranges are not matched between crops.",
        "known_limitations": "Abstract-only; no species-level pairing, full press balance, uncertainty, reagent/energy conditions or GreenHub transferability.",
    }, "filename")


def _update_global_registers() -> None:
    audit = ROOT / "Greenhub/data/global_audit_package"
    relative_path = f"Pre-treatment/Mechanical/{CSV_PATH.name}"
    _upsert(audit / "global_source_register.csv", {
        "dataset_path": relative_path,
        "dataset_group": "Mechanical pretreatment",
        "source_id": SOURCE_ID,
        "source_title": TITLE,
        "authors": AUTHORS,
        "year": "2019",
        "doi_or_stable_id": "No DOI identified; Aarhus University Pure record",
        "url": SOURCE_URL,
        "source_type": "University PhD thesis; abstract-level primary research summary",
        "notes": "Four abstract ranges only; no species pairing or uncertainty. No DOI identified for the thesis record.",
    }, "dataset_path")
    _upsert(audit / "global_dataset_manifest.csv", {
        "dataset_path": relative_path,
        "category": "Pre-treatment",
        "subgroup": "Mechanical",
        "filename": CSV_PATH.name,
        "row_count_observed": str(len(ROWS)),
        "header_count": str(len(FIELDS)),
        "headers": "; ".join(FIELDS),
        "standardized_status_values": "B;reference_only",
        "detected_readiness": "D3",
        "notes": "Four thesis-abstract ranges; preserve as unpaired ranges, not calibrated separation coefficients.",
    }, "dataset_path")
    _upsert(audit / "global_dataset_readiness.csv", {
        "dataset_path": relative_path,
        "category": "Pre-treatment",
        "subgroup": "Mechanical",
        "readiness": "D3",
        "duplicate_ids": "0",
        "duplicate_rows": "0",
        "numeric_rows": str(len(ROWS)),
        "unsourced_numeric_rows": "0",
        "numeric_rows_missing_exact_location": "0",
        "unit_conflicts": "0",
        "basis_conflicts": "0",
        "cross_reference_issues": "0",
        "equation_missing_inputs": "0",
        "equation_symbol_mismatches": "0",
        "notes": "Source location is the university thesis abstract; range endpoints retained without inferred crop pairing or uncertainty.",
    }, "dataset_path")
    summary_path = audit / "global_validation_summary.json"
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    _, manifest_rows = _read_csv(audit / "global_dataset_manifest.csv")
    _, readiness_rows = _read_csv(audit / "global_dataset_readiness.csv")
    readiness_counts: dict[str, int] = {}
    for row in readiness_rows:
        readiness = row.get("readiness", "")
        readiness_counts[readiness] = readiness_counts.get(readiness, 0) + 1
    summary["dataset_count"] = len(manifest_rows)
    summary["readiness_counts"] = readiness_counts
    summary["generated_at"] = datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")
    summary_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main() -> None:
    rows = [
        {
            **row,
            "source_id": SOURCE_ID,
            "evidence_class": "primary_phd_thesis_abstract_reported_range",
            "quality_class": "B",
            "activation_state": "reference_only",
            "transferability": "cultivated_Danish_forage_comparator_not_Dutch_roadside_or_VARTA",
        }
        for row in ROWS
    ]
    _write_csv(CSV_PATH, FIELDS, rows)
    digest = hashlib.sha256(CSV_PATH.read_bytes()).hexdigest()
    metadata = {
        "dataset_id": "urn:greenhub:dataset:pretreatment:damborg-2019-thesis-protein-partition-ranges:v1",
        "title": TITLE,
        "source_id": SOURCE_ID,
        "authors": [AUTHORS],
        "publication_year": 2019,
        "source_url": SOURCE_URL,
        "doi": None,
        "geography": "Danish grassland crops; exact experiment site not established from the abstract",
        "retrieval_date": RETRIEVED,
        "source_location": "Aarhus University Pure publication record, thesis abstract, Trial I and Trial II summaries",
        "methods_summary": "The thesis abstract describes protein extraction from four common Danish grassland crops using physical screw-press treatment and subsequent protein concentration. The four transcribed values are ranges across the abstract's crop/trial context.",
        "license_or_rights": "No explicit reuse license identified for the thesis record. This extract contains short factual ranges with citation, not thesis text or figures; review rights before external redistribution.",
        "evidence_class": "B-tier primary doctoral thesis; abstract-level reported ranges",
        "quality_class": "B",
        "activation_state": "reference_only",
        "calculation_connected": False,
        "row_count": len(rows),
        "sha256_csv": digest,
        "transcription_policy": "Only four ranges explicitly stated in the institutional thesis abstract are transcribed. No species mapping, paired recovery, mass-balance closure, uncertainty, or process equation is inferred.",
        "limitations": [
            "The feedstocks are cultivated Danish forage crops, not Dutch roadside grass, VARTA samples, or GreenHub feed.",
            "The accessible source is an abstract-level institutional thesis record; press settings, precipitation route, individual species values, replicate counts, and full trial-level tables are not transcribed.",
            "Reported range endpoints are not paired across metrics and must not be summed as if they describe one mass balance.",
            "Ranges are not confidence intervals and contain no recoverable SD/SE from the accessible abstract.",
            "Rumen-undegraded protein is an animal nutrition endpoint, not a process protein recovery or market-quality guarantee.",
            "No GreenHub default, parameter, equation, route, TEA/LCA value, or Pareto configuration consumes these records.",
        ],
    }
    SIDECAR_PATH.write_text(json.dumps(metadata, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    _update_local_registers()
    _update_global_registers()
    print(f"wrote {len(ROWS)} thesis reference ranges; sha256={digest}")


if __name__ == "__main__":
    main()
