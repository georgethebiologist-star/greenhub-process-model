"""Stage abstract-reported alfalfa residual-sugar and fermentation evidence."""
from __future__ import annotations

import csv
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "Greenhub" / "data"
FOLDER = DATA / "Pre-treatment" / "Thermal_Enzymatic"
AUDIT = DATA / "global_audit_package"
FILENAME = "alfalfa_press_residue_sugar_platform_zhou_2024_abstract_reference.csv"
CSV_PATH = FOLDER / FILENAME
SIDECAR_PATH = CSV_PATH.with_suffix(".source.json")
SOURCE_ID = "SRC-ZHOU-2024-ALFALFA-RESIDUAL-SUGAR"
DOI = "10.1016/j.indcrop.2023.117927"
URL = "https://doi.org/10.1016/j.indcrop.2023.117927"
RECORD_URL = "https://orbit.dtu.dk/en/publications/development-of-a-sugar-platform-and-fermentation-media-from-resid/"
RETRIEVED = "2026-11-08"
FIELDS = [
    "record_id", "source_id", "phase_relevance", "source_section", "material",
    "process_step", "metric", "value", "unit", "basis", "condition_scope",
    "statistic", "replicate_count", "uncertainty", "source_location", "evidence_class",
    "quality_class", "activation_state", "transferability", "limitations",
]
TITLE = "Development of a sugar platform and fermentation media from residues from alfalfa biorefining"
AUTHORS = "Fa Zhou; Mikkel Hansen; Peter Ruhdal Jensen; Timothy John Hobley"


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
    keys = key.split("|")
    indexed = {tuple(row.get(item, "") for item in keys): row for row in rows}
    for entry in entries:
        identity = tuple(entry.get(item, "") for item in keys)
        if identity in indexed:
            indexed[identity].update(entry)
        else:
            rows.append(entry)
            indexed[identity] = rows[-1]
    _write(path, fields or list(entries[0]), rows)


def build_rows() -> list[dict[str, str]]:
    rows = []

    def add(record_id: str, metric: str, value: str, unit: str, basis: str, condition: str):
        rows.append({
            "record_id": record_id, "source_id": SOURCE_ID, "phase_relevance": "5",
            "source_section": "Abstract; DTU Orbit record, lines 19–22",
            "material": "Cultivated alfalfa biorefinery press pulp, pulp hydrolysate, or brown juice",
            "process_step": "residual pulp pretreatment, enzymatic saccharification, or lactic-acid fermentation",
            "metric": metric, "value": value, "unit": unit, "basis": basis,
            "condition_scope": condition, "statistic": "abstract-reported result/condition",
            "replicate_count": "not reported in abstract", "uncertainty": "not reported in abstract",
            "source_location": "Peer-reviewed article abstract; DTU Orbit institutional record",
            "evidence_class": "B_primary_article_abstract_reported", "quality_class": "B",
            "activation_state": "reference_only",
            "transferability": "Cultivated alfalfa residual stream and a pulp hydrolysis/fermentation route; not Dutch roadside grass or GreenHub's configured residual-AD route.",
            "limitations": "Abstract-level only; full methods, replicate count, uncertainty, complete balances, utilities, and scale are not available in this extract. Not a GreenHub default or route calibration.",
        })

    observations = [
        ("PRETREATMENT-CHLORITE", "sodium_chlorite_concentration", "6", "%", "Reported pretreatment concentration; percentage basis not specified in abstract", "Alfalfa pulp delignification"),
        ("PRETREATMENT-LIGNIN-REMOVAL", "lignin_removal", "79.8", "%", "Fraction of source pulp lignin removed, as abstract-reported", "6% sodium-chlorite pretreatment"),
        ("PRETREATMENT-GLUCAN-RETENTION", "glucan_retention", "89.1", "%", "Fraction of source glucan retained, as abstract-reported", "6% sodium-chlorite pretreatment"),
        ("PRETREATMENT-XYLAN-RETENTION", "xylan_retention", "75.4", "%", "Fraction of source xylan retained, as abstract-reported", "6% sodium-chlorite pretreatment"),
        ("HYDROLYSIS-CELLULASE-LOADING", "cellulase_loading", "10", "FPU/g dry substrate", "Enzyme loading per dry substrate", "Cellulase hydrolysis"),
        ("HYDROLYSIS-DURATION", "hydrolysis_duration", "48", "h", "Reported hydrolysis duration", "Cellulase hydrolysis"),
        ("HYDROLYSIS-GLUCAN-CONVERSION", "glucan_conversion_to_glucose", "81.0", "%", "Reported conversion of glucan to glucose", "Cellulase hydrolysis"),
        ("HYDROLYSIS-XYLAN-CONVERSION", "xylan_conversion_to_xylose", "79.3", "%", "Reported conversion of xylan to xylose", "Cellulase hydrolysis"),
        ("HYDROLYSIS-BIOMASS-LOADING", "biomass_loading", "10", "% w/v", "Biomass loading in hydrolysis; exact liquid-volume convention not further specified in abstract", "Saccharification using deionized water for suspension"),
        ("HYDROLYSIS-GLUCOSE-CONCENTRATION", "glucose_concentration", "35.2", "g/L", "Concentration in hydrolysate", "10% w/v biomass loading; deionized water suspension"),
        ("HYDROLYSIS-XYLOSE-CONCENTRATION", "xylose_concentration", "13.0", "g/L", "Concentration in hydrolysate", "10% w/v biomass loading; deionized water suspension"),
        ("BROWN-JUICE-LACTIC-ACID-BASELINE", "lactic_acid_concentration", "12.8", "g/L", "Concentration in fermented brown juice", "Brown juice fermented without further additions using Lactococcus lactis KF 147"),
        ("BROWN-JUICE-HYDROLYSATE-15-VOL", "pulp_hydrolysate_supplement", "15", "% v/v", "Reported supplementation level", "Brown-juice fermentation; abstract maps the lower endpoint to 17.4 g/L lactic acid"),
        ("BROWN-JUICE-LACTIC-ACID-15-VOL", "lactic_acid_concentration", "17.4", "g/L", "Concentration in fermented brown juice", "Pulp hydrolysate supplementation at 15% v/v"),
        ("BROWN-JUICE-HYDROLYSATE-70-VOL", "pulp_hydrolysate_supplement", "70", "% v/v", "Reported supplementation level", "Brown-juice fermentation; abstract maps the upper endpoint to 28.8 g/L lactic acid"),
        ("BROWN-JUICE-LACTIC-ACID-70-VOL", "lactic_acid_concentration", "28.8", "g/L", "Concentration in fermented brown juice", "Pulp hydrolysate supplementation at 70% v/v"),
    ]
    for suffix, metric, value, unit, basis, condition in observations:
        add(f"ZHOU24-{suffix}", metric, value, unit, basis, condition)
    return rows


def _number(value: str) -> bool:
    try:
        float(value)
        return True
    except (TypeError, ValueError):
        return False


def main() -> None:
    rows = build_rows()
    if len({row["record_id"] for row in rows}) != len(rows):
        raise ValueError("Duplicate Zhou 2024 article record IDs")
    _write(CSV_PATH, FIELDS, rows)
    digest = hashlib.sha256(CSV_PATH.read_bytes()).hexdigest()
    sidecar = {
        "dataset_id": "urn:greenhub:dataset:pre-treatment:zhou-2024-alfalfa-residual-sugar-platform:v1",
        "dataset_version": "1.0.0",
        "persistent_identifier_status": "Local URN identifies this extract; DOI identifies the source article.",
        "title": "Alfalfa press-residue pretreatment, sugar hydrolysis and brown-juice fermentation observations",
        "source_id": SOURCE_ID,
        "citation": f"Zhou, F., Hansen, M., Jensen, P. R., & Hobley, T. J. (2024). {TITLE}. Industrial Crops and Products, 209, 117927. https://doi.org/{DOI}",
        "doi": DOI, "source_url": URL, "repository_record": RECORD_URL,
        "retrieval_date": RETRIEVED, "source_location": "Article abstract; DTU Orbit record lines 19–22",
        "geography": "Technical University of Denmark research; exact alfalfa field site/cultivar not specified in the abstract.",
        "material_scope": "Alfalfa-derived pulp and brown juice from a green-biorefinery route.",
        "license_or_rights": "No explicit reuse license identified on the DTU record checked; retain citation and factual abstract-level extract, and verify publisher terms before external redistribution.",
        "evidence_class": "B_peer_reviewed_primary_article_abstract_only",
        "quality_class": "B", "activation_state": "reference_only", "calculation_connected": False,
        "row_count": len(rows), "sha256_csv": digest,
        "transcription_policy": "Only explicit abstract values and their stated condition links are transcribed; absent uncertainties, methods and process balances are not inferred.",
        "limitations": [
            "The dataset is abstract-level, not a transcription of full article tables or raw data; the publication page directs access through DTU Findit.",
            "Alfalfa residual pulp and fermented brown juice are not GreenHub roadside-grass streams.",
            "This hydrolysis/lactic-fermentation value pathway is not a configured GreenHub route; values are not transferable yields or operating defaults.",
            "The 6% sodium-chlorite percentage basis, replicate count, uncertainties, detailed water/reagent demand, utilities, and full mass balance are not stated in the abstract.",
            "No explicit reuse license was found on the institutional record; check publisher terms before redistributing beyond citation and factual metadata.",
        ],
    }
    SIDECAR_PATH.write_text(json.dumps(sidecar, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    local_source = {
        "source_id": SOURCE_ID, "source_type": "peer-reviewed article; abstract-level extraction",
        "title": TITLE, "authors": AUTHORS, "year": "2024", "doi_or_stable_identifier": DOI,
        "publisher": "Elsevier; Industrial Crops and Products", "url": URL,
        "material_scope": "Alfalfa-derived press pulp, pulp hydrolysate and brown juice",
        "source_quality": "peer-reviewed primary article; only abstract values staged",
        "access_date": RETRIEVED,
        "notes": "DOI and DTU Orbit record verify article identity and abstract values. No explicit reuse license identified; reference-only, no GreenHub defaults.",
    }
    _upsert(FOLDER / "source_register.csv", "source_id", [local_source])
    _upsert(FOLDER / "dataset_manifest.csv", "filename", [{
        "dataset_id": "DS-TE-ZHOU24-001", "filename": FILENAME,
        "purpose": "Abstract-reported alfalfa press-residue delignification, saccharification and brown-juice fermentation; Phase 5 comparator.",
        "row_count": str(len(rows)), "primary_key": "record_id", "encoding": "UTF-8",
        "delimiter": ",", "integration_readiness": "reference_only_D3",
        "known_limitations": "Abstract-only; alfalfa route; percentage basis, uncertainty, scale, utility and component balances incomplete; no explicit reuse license found.",
    }])

    rel = f"Pre-treatment/Thermal_Enzymatic/{FILENAME}"
    _upsert(AUDIT / "global_source_register.csv", "dataset_path|source_id", [{
        "dataset_path": rel, "dataset_group": "Pre-treatment/Thermal_Enzymatic", "source_id": SOURCE_ID,
        "source_title": TITLE, "authors": AUTHORS, "year": "2024", "doi_or_stable_id": DOI,
        "url": URL, "source_type": "peer-reviewed article; abstract-level extraction",
        "notes": "Alfalfa press-residue sugar platform; abstract values only; not GreenHub residual-AD route; reference-only; reuse rights not identified.",
    }])
    numeric_rows = sum(_number(row["value"]) for row in rows)
    _upsert(AUDIT / "global_dataset_manifest.csv", "dataset_path", [{
        "dataset_path": rel, "category": "Pre-treatment", "subgroup": "alfalfa residual pulp hydrolysis and brown-juice fermentation; Phase 5",
        "filename": FILENAME, "row_count_observed": str(len(rows)), "header_count": str(len(FIELDS)),
        "headers": "; ".join(FIELDS), "standardized_status_values": "B;reference_only", "detected_readiness": "D3",
        "notes": "Abstract-level article values; transferability, process basis and limitations explicit; no runtime mapping.",
    }])
    _upsert(AUDIT / "global_dataset_readiness.csv", "dataset_path", [{
        "dataset_path": rel, "category": "Pre-treatment", "subgroup": "alfalfa residual pulp hydrolysis and brown-juice fermentation; Phase 5",
        "readiness": "D3", "duplicate_ids": "0", "duplicate_rows": "0", "numeric_rows": str(numeric_rows),
        "unsourced_numeric_rows": "0", "numeric_rows_missing_exact_location": "0", "unit_conflicts": "0",
        "basis_conflicts": "0", "cross_reference_issues": "0", "equation_missing_inputs": "0",
        "equation_symbol_mismatches": "0", "notes": "Abstract values linked to DOI and DTU record; unreported bases/uncertainty remain explicit.",
    }])
    checksums = [{"dataset_path": f"Pre-treatment/Thermal_Enzymatic/{path.name}",
                  "sha256": hashlib.sha256(path.read_bytes()).hexdigest(), "byte_size": str(path.stat().st_size)}
                 for path in (CSV_PATH, SIDECAR_PATH)]
    _upsert(AUDIT / "source_dataset_checksums.csv", "dataset_path", checksums)
    _upsert(AUDIT / "dataset_activation_matrix.csv", "dataset_path", [{
        "dataset_path": rel, "category": "Pre-treatment", "subgroup": "alfalfa residual pulp hydrolysis and brown-juice fermentation; Phase 5",
        "audit_readiness": "D3", "integration_eligibility": "reference_only", "default_eligibility": "False",
        "calculation_connected": "False", "active": "False", "source_issue_count": "0", "quarantine_row_count": "0",
        "issue_types": "none", "cost_pathway_status": "not_applicable",
        "selection_reason": "Abstract-level alfalfa route data are source-linked but are not GreenHub roadside-residual validation or a configured process pathway.",
        "required_action": "Use only as a bounded literature comparator; obtain full-text methods and GreenHub matched residual trials before any route activation.",
        "source_checksum_sha256": digest,
    }])

    registry_summary_path = AUDIT / "checkpoint1_registry_summary.json"
    registry_summary = json.loads(registry_summary_path.read_text(encoding="utf-8"))
    _, activation_rows = _read(AUDIT / "dataset_activation_matrix.csv")
    eligibility_counts: dict[str, int] = {}
    for item in activation_rows:
        key = item.get("integration_eligibility", "")
        eligibility_counts[key] = eligibility_counts.get(key, 0) + 1
    registry_summary.update(
        source_dataset_count=len(activation_rows), dataset_eligibility_counts=dict(sorted(eligibility_counts.items())),
        active_dataset_count=sum(item.get("active") == "True" for item in activation_rows),
        default_eligible_dataset_count=sum(item.get("default_eligibility") == "True" for item in activation_rows),
        source_checksum_count=sum(bool(item.get("source_checksum_sha256")) for item in activation_rows),
    )
    registry_summary_path.write_text(json.dumps(registry_summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    summary_path = AUDIT / "global_validation_summary.json"
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    _, manifests = _read(AUDIT / "global_dataset_manifest.csv")
    _, readiness = _read(AUDIT / "global_dataset_readiness.csv")
    readiness_counts: dict[str, int] = {}
    for item in readiness:
        key = item.get("readiness", "")
        readiness_counts[key] = readiness_counts.get(key, 0) + 1
    summary.update(dataset_count=len(manifests), readiness_counts=readiness_counts,
                   generated_at=datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z"))
    summary_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"dataset": str(CSV_PATH), "rows": len(rows), "numeric_rows": numeric_rows, "sha256": digest}, indent=2))


if __name__ == "__main__":
    main()
