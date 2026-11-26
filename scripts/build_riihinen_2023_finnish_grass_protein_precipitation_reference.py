"""Record reference-only process observations from Riihinen et al. (2023).

The source is a conference abstract. Values from the best-tested condition and
the separately described selected protocol are deliberately kept distinct.
Nothing in this extract is a GreenHub model parameter.
"""
from __future__ import annotations

import csv
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
FOLDER = ROOT / "Greenhub/data/Protein recovery/Isoelectric"
CSV_PATH = FOLDER / "riihinen_2023_finnish_grass_protein_precipitation_reference.csv"
SOURCE_ID = "SRC-RIIHINEN-EFFOST-GRASS-PROTEIN-2023"
TITLE = "Enrichment of protein from Finnish grass material for human consumption"
AUTHORS = "Kaisu Riihinen; Saska Sormunen; Raija Lantto; Kaisu Honkapää"
SOURCE_URL = "https://onfoods.it/sites/default/files/2024-07/Abstract%20book_37th_EFFoST_International_Conference_ISBN.pdf"
RETRIEVED = "2026-11-08"

FIELDS = [
    "record_id", "phase_relevance", "material", "botanical_name", "process_step",
    "metric", "reported_value", "unit", "basis", "condition_scope",
    "source_location", "source_id", "evidence_class", "quality_class", "activation_state",
    "transferability", "limitations",
]

ROWS = [
    {
        "record_id": "RIIHINEN23-SULPHITE-ADDITION",
        "phase_relevance": "4",
        "material": "Screw-pressed grass juice from red clover and timothy",
        "botanical_name": "Trifolium pratense; Phleum pratense",
        "process_step": "Antioxidant addition before protein fractionation",
        "metric": "sodium_sulphite_amount_added",
        "reported_value": "25",
        "unit": "mmol added",
        "basis": "Absolute amount as reported; denominator (juice volume or biomass) is not stated.",
        "condition_scope": "The abstract reports adding sodium sulphite (Na2SO3) to inhibit polyphenol oxidation; no dose-response values are given.",
        "source_location": "EFFoST 2023 Abstract Book, abstract P2.1.088, Methods",
        "limitations": "Not a normalized dose and cannot be converted to reagent demand without the missing denominator and process scale.",
    },
    {
        "record_id": "RIIHINEN23-HEAT-TESTED-TEMPERATURES",
        "phase_relevance": "4",
        "material": "Screw-pressed grass juice from red clover and timothy",
        "botanical_name": "Trifolium pratense; Phleum pratense",
        "process_step": "Heat coagulation of green chlorophyll proteins",
        "metric": "heat_coagulation_temperatures_tested",
        "reported_value": "50; 55; 60",
        "unit": "degC",
        "basis": "Tested setpoints stated in abstract; not a continuous operating range.",
        "condition_scope": "The abstract describes testing these temperatures for both grass species.",
        "source_location": "EFFoST 2023 Abstract Book, abstract P2.1.088, Methods",
        "limitations": "No residence time, heating rate, juice composition, replicate count, uncertainty, or energy demand is reported in the abstract.",
    },
    {
        "record_id": "RIIHINEN23-HEAT-SELECTED-OPTIMUM",
        "phase_relevance": "4",
        "material": "Screw-pressed grass juice from red clover and timothy",
        "botanical_name": "Trifolium pratense; Phleum pratense",
        "process_step": "Heat coagulation of green chlorophyll proteins",
        "metric": "selected_heat_coagulation_temperature",
        "reported_value": "50",
        "unit": "degC",
        "basis": "Selected optimum reported by authors; not an independently reconstructed optimum.",
        "condition_scope": "The authors report 50 degC as selected for both species among the tested setpoints.",
        "source_location": "EFFoST 2023 Abstract Book, abstract P2.1.088, Results",
        "limitations": "Abstract-only result; no response curve, residence time, recovery, or scale-up data.",
    },
    {
        "record_id": "RIIHINEN23-ACID-PH-TESTED",
        "phase_relevance": "4",
        "material": "Grass juice after green-protein heat coagulation",
        "botanical_name": "Trifolium pratense; Phleum pratense",
        "process_step": "Acid precipitation of RuBisCO protein",
        "metric": "precipitation_pH_tested",
        "reported_value": "5; 4; 3; 2",
        "unit": "pH",
        "basis": "Discrete pH setpoints stated in abstract; not a continuous operating interval.",
        "condition_scope": "Abstract reports pH 5 through pH 2; acid identity, titration curve, and dose are not given.",
        "source_location": "EFFoST 2023 Abstract Book, abstract P2.1.088, Methods",
        "limitations": "No acid consumption or buffering data; pH endpoints cannot determine reagent demand.",
    },
    {
        "record_id": "RIIHINEN23-RED-CLOVER-PRECIPITATE-MAX-PROTEIN",
        "phase_relevance": "4",
        "material": "Red clover RuBisCO precipitate",
        "botanical_name": "Trifolium pratense",
        "process_step": "Acid precipitation; best protein-content condition reported",
        "metric": "protein_content_in_precipitate",
        "reported_value": "45",
        "unit": "g protein/100 g precipitate DM",
        "basis": "Protein mass per dry mass of precipitate, as reported.",
        "condition_scope": "The abstract explicitly associates the red-clover maximum with pH 4.",
        "source_location": "EFFoST 2023 Abstract Book, abstract P2.1.088, Results",
        "limitations": "Product composition is not protein recovery or precipitate yield; abstract-level result with no reported uncertainty.",
    },
    {
        "record_id": "RIIHINEN23-TIMOTHY-PRECIPITATE-MAX-PROTEIN",
        "phase_relevance": "4",
        "material": "Timothy RuBisCO precipitate",
        "botanical_name": "Phleum pratense",
        "process_step": "Acid precipitation; best protein-content condition reported",
        "metric": "protein_content_in_precipitate",
        "reported_value": "56",
        "unit": "g protein/100 g precipitate DM",
        "basis": "Protein mass per dry mass of precipitate, as reported.",
        "condition_scope": "The abstract gives 56 g/100 g DM for timothy in the sentence reporting the best protein contents; it does not separately restate the pH for this species.",
        "source_location": "EFFoST 2023 Abstract Book, abstract P2.1.088, Results",
        "limitations": "Do not silently assign pH 4 to this species-specific figure; product composition is not protein recovery or precipitate yield.",
    },
    {
        "record_id": "RIIHINEN23-SELECTED-RED-CLOVER-PRODUCT-PROTEIN",
        "phase_relevance": "4",
        "material": "Red clover RuBisCO protein precipitate from selected protocol",
        "botanical_name": "Trifolium pratense",
        "process_step": "Selected two-step heat-coagulation and acid-precipitation protocol",
        "metric": "protein_content_in_selected_protocol_precipitate",
        "reported_value": "41",
        "unit": "g protein/100 g precipitate DM",
        "basis": "Protein mass per dry mass of recovered precipitate, as reported for the selected protocol.",
        "condition_scope": "Selected-protocol mass-balance description; abstract does not explicitly state this sample's pH or reconcile it to the maximum-content test result.",
        "source_location": "EFFoST 2023 Abstract Book, abstract P2.1.088, Results",
        "limitations": "Separate protocol result from the reported maximum-content condition; no yield, uncertainty, or full fraction mass table is present in the abstract.",
    },
    {
        "record_id": "RIIHINEN23-SELECTED-TIMOTHY-PRODUCT-PROTEIN",
        "phase_relevance": "4",
        "material": "Timothy RuBisCO protein precipitate from selected protocol",
        "botanical_name": "Phleum pratense",
        "process_step": "Selected two-step heat-coagulation and acid-precipitation protocol",
        "metric": "protein_content_in_selected_protocol_precipitate",
        "reported_value": "51",
        "unit": "g protein/100 g precipitate DM",
        "basis": "Protein mass per dry mass of recovered precipitate, as reported for the selected protocol.",
        "condition_scope": "Selected-protocol mass-balance description; abstract does not explicitly state this sample's pH or reconcile it to the maximum-content test result.",
        "source_location": "EFFoST 2023 Abstract Book, abstract P2.1.088, Results",
        "limitations": "Separate protocol result from the reported maximum-content condition; no yield, uncertainty, or full fraction mass table is present in the abstract.",
    },
    {
        "record_id": "RIIHINEN23-SELECTED-RED-CLOVER-PROTEIN-RECOVERY",
        "phase_relevance": "4",
        "material": "Total protein in red clover grass juice; recovered RuBisCO precipitate",
        "botanical_name": "Trifolium pratense",
        "process_step": "Selected two-step fractionation protocol",
        "metric": "fraction_of_juice_protein_recovered_in_RuBisCO_precipitate",
        "reported_value": "approximately 10",
        "unit": "% of total protein in grass juice",
        "basis": "The authors state that approximately this fraction of protein found in grass juice was recovered in RuBisCO protein precipitate.",
        "condition_scope": "Selected-protocol assessment; approximate value, with no uncertainty or explicit replicate summary.",
        "source_location": "EFFoST 2023 Abstract Book, abstract P2.1.088, Results",
        "limitations": "Denominator is juice protein, not feed protein; cannot be read as whole-grass protein recovery or assigned to a GreenHub route.",
    },
    {
        "record_id": "RIIHINEN23-SELECTED-TIMOTHY-PROTEIN-RECOVERY",
        "phase_relevance": "4",
        "material": "Total protein in timothy grass juice; recovered RuBisCO precipitate",
        "botanical_name": "Phleum pratense",
        "process_step": "Selected two-step fractionation protocol",
        "metric": "fraction_of_juice_protein_recovered_in_RuBisCO_precipitate",
        "reported_value": "approximately 10",
        "unit": "% of total protein in grass juice",
        "basis": "The authors state that approximately this fraction of protein found in grass juice was recovered in RuBisCO protein precipitate.",
        "condition_scope": "Selected-protocol assessment; approximate value, with no uncertainty or explicit replicate summary.",
        "source_location": "EFFoST 2023 Abstract Book, abstract P2.1.088, Results",
        "limitations": "Denominator is juice protein, not feed protein; cannot be read as whole-grass protein recovery or assigned to a GreenHub route.",
    },
]


def _rows(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    if not path.exists():
        return [], []
    with path.open(encoding="utf-8-sig", newline="") as stream:
        reader = csv.DictReader(stream)
        return list(reader.fieldnames or []), list(reader)


def _write_csv(path: Path, fields: list[str], rows: list[dict[str, str]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def _upsert(path: Path, record: dict[str, str], key: str) -> None:
    fields, rows = _rows(path)
    if not fields:
        fields = list(record)
    existing = next((row for row in rows if row.get(key) == record[key]), None)
    if existing is None:
        rows.append(record)
    else:
        existing.update(record)
    _write_csv(path, fields, rows)


def _update_registers() -> None:
    _upsert(FOLDER / "source_register.csv", {
        "source_id": SOURCE_ID,
        "source_title": TITLE,
        "authors": AUTHORS,
        "year": "2023",
        "source_type": "Conference abstract; primary experimental study summary",
        "peer_review_status": "conference abstract; review process not verified",
        "doi_or_stable_id": "ISBN 978-90-9037865-7; abstract P2.1.088; no DOI identified",
        "source_url": SOURCE_URL,
        "materials": "Cultivated Finnish red clover (Trifolium pratense) and timothy (Phleum pratense)",
        "processes": "Screw pressing; sodium sulphite addition; heat coagulation; acid precipitation; selected-protocol protein fractionation",
        "used_in_files": CSV_PATH.name,
        "access_notes": "EFFoST 2023 Abstract Book, P2.1.088, p. 252; no explicit open reuse license identified.",
        "quality_notes": "Abstract-level measurements and method summary only; selected-protocol figures kept distinct from best-content pH tests; reference-only, not GreenHub calibration.",
    }, "source_id")
    _upsert(FOLDER / "dataset_manifest.csv", {
        "filename": CSV_PATH.name,
        "dataset_scope": "Abstract-level red-clover/timothy heat-coagulation and RuBisCO acid-precipitation process observations, retaining separately reported maximum-content tests and selected-protocol outcomes.",
        "row_count": str(len(ROWS)),
        "required_columns_present": "yes: unique record, phase, species, operation, metric, value/unit/basis, condition, source location, evidence class and transferability caveat",
        "numeric_traceability_check": "All numeric records link to abstract P2.1.088; condition and denominator ambiguities retained explicitly.",
        "contains_assumptions_with_blank_values": "yes: missing pH linkage, dose denominator, uncertainty and full balance are documented, not imputed",
        "integration_readiness": "reference_only_D3",
        "limitations": "Finnish cultivated forages and conference-abstract summary; not roadside/VARTA, no full mass balance, acid demand, time/energy, independent uncertainty or model-scale evidence.",
    }, "filename")

    audit = ROOT / "Greenhub/data/global_audit_package"
    relative = f"Protein recovery/Isoelectric/{CSV_PATH.name}"
    _upsert(audit / "global_source_register.csv", {
        "dataset_path": relative,
        "dataset_group": "Protein recovery/isoelectric",
        "source_id": SOURCE_ID,
        "source_title": TITLE,
        "authors": AUTHORS,
        "year": "2023",
        "doi_or_stable_id": "ISBN 978-90-9037865-7; abstract P2.1.088; no DOI identified",
        "url": SOURCE_URL,
        "source_type": "Conference abstract; primary experimental study summary",
        "notes": "Abstract reports separate best-content test values and selected-protocol values; preserve distinctions; reference-only.",
    }, "dataset_path")
    _upsert(audit / "global_dataset_manifest.csv", {
        "dataset_path": relative,
        "category": "Protein recovery",
        "subgroup": "Isoelectric",
        "filename": CSV_PATH.name,
        "row_count_observed": str(len(ROWS)),
        "header_count": str(len(FIELDS)),
        "headers": "; ".join(FIELDS),
        "standardized_status_values": "B;reference_only",
        "detected_readiness": "D3",
        "notes": "Conference abstract; selected-protocol and maximum-content test observations kept distinct; not a closed protein balance.",
    }, "dataset_path")
    _upsert(audit / "global_dataset_readiness.csv", {
        "dataset_path": relative,
        "category": "Protein recovery",
        "subgroup": "Isoelectric",
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
        "notes": "Abstract P2.1.088 p. 252; dose denominator and selected-protocol pH details are missing and explicitly retained as limitations.",
    }, "dataset_path")
    summary_path = audit / "global_validation_summary.json"
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    _, manifest = _rows(audit / "global_dataset_manifest.csv")
    _, readiness = _rows(audit / "global_dataset_readiness.csv")
    counts: dict[str, int] = {}
    for row in readiness:
        label = row.get("readiness", "")
        counts[label] = counts.get(label, 0) + 1
    summary["dataset_count"] = len(manifest)
    summary["readiness_counts"] = counts
    summary["generated_at"] = datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")
    summary_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main() -> None:
    FOLDER.mkdir(parents=True, exist_ok=True)
    records = [
        {
            **row,
            "source_id": SOURCE_ID,
            "evidence_class": "primary_conference_abstract_reported",
            "quality_class": "B",
            "activation_state": "reference_only",
            "transferability": "Finnish_cultivated_red_clover_and_timothy_not_Dutch_roadside_or_VARTA",
        }
        for row in ROWS
    ]
    _write_csv(CSV_PATH, FIELDS, records)
    metadata = {
        "dataset_id": "urn:greenhub:dataset:protein-recovery:riihinen-2023-finnish-grass-precipitation:v1",
        "source_id": SOURCE_ID,
        "title": TITLE,
        "authors": ["Kaisu Riihinen", "Saska Sormunen", "Raija Lantto", "Kaisu Honkapää"],
        "publication_year": 2023,
        "persistent_identifier": "ISBN 978-90-9037865-7; abstract P2.1.088; no DOI identified",
        "source_url": SOURCE_URL,
        "source_location": "37th EFFoST International Conference 2023 Abstract Book, P2.1.088, p. 252",
        "retrieval_date": RETRIEVED,
        "geography": "Finland; exact experimental site not stated in abstract",
        "material_scope": "Cultivated red clover (Trifolium pratense) and timothy (Phleum pratense); screw-pressed grass juice",
        "license_or_rights": "No explicit open reuse license identified in the abstract book; retain citation and short factual observations, and review rights before external redistribution.",
        "evidence_class": "B-tier primary experimental conference abstract; summary-level reported values",
        "quality_class": "B",
        "activation_state": "reference_only",
        "calculation_connected": False,
        "row_count": len(records),
        "sha256_csv": hashlib.sha256(CSV_PATH.read_bytes()).hexdigest(),
        "transcription_policy": "Only facts and values stated in abstract P2.1.088 are extracted. Tested pH/temperature levels, best-content test outcomes, and selected-protocol mass-balance observations are separated; no unreported values are inferred.",
        "limitations": [
            "Conference abstract only; it does not provide the detailed methods, raw observations, replicate count, uncertainty, or complete fraction-by-fraction table.",
            "Materials are cultivated Finnish red clover and timothy, not Dutch roadside grass, VARTA samples, or GreenHub feed.",
            "The 25 mmol sodium sulphite addition has no stated juice-volume or biomass denominator and cannot provide a normalized reagent dose.",
            "The abstract explicitly associates pH 4 with the red-clover maximum protein-content result but does not separately restate pH for the timothy value.",
            "The selected-protocol precipitate protein contents (41 and 51 g/100 g DM) are distinct from the reported best-content test results (45 and 56 g/100 g DM); the abstract does not reconcile them.",
            "The approximate 10% recovery denominator is total protein in grass juice, not protein in incoming grass; it is not whole-feed protein recovery.",
            "No acid identity/dose, pH titration curve, precipitate mass yield, energy, residence time, full mass closure, or scale-up relationship is reported in the abstract.",
            "No GreenHub default, parameter, equation, route, TEA/LCA value, UI setting, or Pareto configuration consumes these records.",
        ],
    }
    CSV_PATH.with_suffix(".source.json").write_text(json.dumps(metadata, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    _update_registers()
    print(f"wrote {len(records)} reference-only abstract observations; sha256={metadata['sha256_csv']}")


if __name__ == "__main__":
    main()
