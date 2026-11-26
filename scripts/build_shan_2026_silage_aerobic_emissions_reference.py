"""Build a cautious Phase 2 extract from Shan et al. (2026) abstract facts.

The abstract provides area-normalized early-period emission estimates with an
unidentified +/- statistic and approximate emission lags. Those facts are kept
as reported and reference-only; no storage rate or per-feed emission factor is
derived.
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
FILENAME = "silage_feedout_co2_ethanol_emissions_shan_2026_abstract_reference.csv"
CSV_PATH = STORAGE / FILENAME
SOURCE_ID = "SRC-SHAN-SILAGE-FEEDOUT-EMISSIONS-2026"
DOI = "10.1016/j.jece.2026.121987"
DOI_URL = f"https://doi.org/{DOI}"
PUBLISHER_URL = "https://www.sciencedirect.com/science/article/pii/S2213343726009619"
RETRIEVED = "2026-11-08"

FIELDS = [
    "observation_id", "source_id", "phase", "material", "treatment_scope",
    "exposure_window", "response", "reported_value", "reported_uncertainty",
    "reported_statistic_type", "unit_as_reported", "basis", "source_location",
    "evidence_class", "quality_class", "activation_state",
    "applicability_limit", "notes",
]

LIMIT = (
    "Mini-silo feed-out experiment in cultivated ryegrass and maize, not Dutch "
    "roadside grass or GreenHub storage. The abstract does not identify the "
    "statistic represented by the +/- term, give a dry-matter or mass denominator, "
    "or separate results by additive treatment. Do not interpret as a storage rate, "
    "mass-specific emission factor, or runtime/LCA factor. Reference-only."
)


def emission_row(material: str, gas: str, value: str, uncertainty: str) -> dict[str, str]:
    material_key = material.upper()
    gas_key = gas.upper().replace(" ", "-")
    return {
        "observation_id": f"SHAN26-{material_key}-{gas_key}-0_10H",
        "source_id": SOURCE_ID,
        "phase": "2",
        "material": f"{material} silage",
        "treatment_scope": (
            "1.5 L mini-silos with and without commercial bio-additive; abstract "
            "does not assign this summary value to a treatment"
        ),
        "exposure_window": "initial 0–10 h aerobic-stable period after exposure to air",
        "response": f"initial {gas} emission",
        "reported_value": value,
        "reported_uncertainty": uncertainty,
        "reported_statistic_type": "central value and ± term as printed; statistic not identified in abstract",
        "unit_as_reported": "10^-2 mol m^-2",
        "basis": "per area; no feed-mass or dry-matter denominator reported",
        "source_location": "Publisher abstract, result (ii)",
        "evidence_class": "B_measured_literature_abstract_extract",
        "quality_class": "B",
        "activation_state": "reference_only",
        "applicability_limit": LIMIT,
        "notes": (
            "Values are transcribed as the printed central value and ± term; "
            "the ± statistic, replicate basis, treatment aggregation and exact "
            "emitted-area definition were not recoverable from the accessible abstract. "
            "No conversion or scaling applied."
        ),
    }


def lag_row(material: str, hours: str) -> dict[str, str]:
    return {
        "observation_id": f"SHAN26-{material.upper()}-CO2-ETHANOL-LAG",
        "source_id": SOURCE_ID,
        "phase": "2",
        "material": f"{material} silage",
        "treatment_scope": "with/without commercial bio-additive; summary treatment not specified",
        "exposure_window": "aerobic-unstable period after exposure to air",
        "response": "approximate lag between CO2 and ethanol emissions",
        "reported_value": hours,
        "reported_uncertainty": "not reported",
        "reported_statistic_type": "approximate duration as described in abstract",
        "unit_as_reported": "h",
        "basis": "elapsed time between emission signals; no feed-mass basis",
        "source_location": "Publisher abstract, result (iv)",
        "evidence_class": "B_measured_literature_abstract_extract",
        "quality_class": "B",
        "activation_state": "reference_only",
        "applicability_limit": LIMIT,
        "notes": "Approximate lag only; not a kinetic parameter and not fitted to GreenHub storage.",
    }


ROWS = [
    emission_row("maize", "carbon dioxide", "1.104", "1.294"),
    emission_row("maize", "ethanol", "0.570", "0.807"),
    emission_row("ryegrass", "carbon dioxide", "0.805", "0.888"),
    emission_row("ryegrass", "ethanol", "0.060", "0.408"),
    lag_row("maize", "approximately 40"),
    lag_row("ryegrass", "approximately 100"),
]

SOURCE_TITLE = (
    "Determining characteristics of CO2 and ethanol emissions from microbial "
    "respiration in silage by partitioning of aerobic/anaerobic metabolites"
)
AUTHORS = "Guilin Shan; Yurui Sun; Wolfgang Buescher; Christian Maack; Wilfried Berchtold; David A. Grantz"


def read_csv(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    if not path.exists():
        return [], []
    with path.open("r", encoding="utf-8-sig", newline="") as stream:
        reader = csv.DictReader(stream)
        return reader.fieldnames or [], list(reader)


def append_once(path: Path, row: dict[str, object], key: str) -> None:
    fields, existing = read_csv(path)
    matches = [item for item in existing if item.get(key) == str(row.get(key, ""))]
    if matches:
        if len(matches) != 1 or any(matches[0].get(field, "") != str(row.get(field, "")) for field in fields):
            raise ValueError(f"Conflicting registration in {path}: {row.get(key)}")
        return
    with path.open("a", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields, lineterminator="\n", extrasaction="ignore")
        writer.writerow({field: row.get(field, "") for field in fields})


def main() -> None:
    STORAGE.mkdir(parents=True, exist_ok=True)
    with CSV_PATH.open("w", encoding="utf-8-sig", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=FIELDS, lineterminator="\n")
        writer.writeheader()
        writer.writerows(ROWS)

    digest = hashlib.sha256(CSV_PATH.read_bytes()).hexdigest()
    sidecar = {
        "dataset_id": "urn:greenhub:dataset:storage:shan-silage-feedout-emissions-2026:v1",
        "dataset_version": "1.0.0",
        "dataset_file": FILENAME,
        "record_count": len(ROWS),
        "sha256": digest,
        "source_id": SOURCE_ID,
        "citation": (
            "Shan, G., Sun, Y., Buescher, W., Maack, C., Berchtold, W., & Grantz, D. A. (2026). "
            "Determining characteristics of CO2 and ethanol emissions from microbial respiration "
            "in silage by partitioning of aerobic/anaerobic metabolites. Journal of Environmental "
            "Chemical Engineering, 14(2), 121987. " + DOI_URL
        ),
        "publication_year": 2026,
        "doi": DOI,
        "source_url": PUBLISHER_URL,
        "retrieval_date": RETRIEVED,
        "source_locations": ["Publisher abstract, results (ii) and (iv)."],
        "applicable_phases": [2],
        "geography": "Not stated in accessible abstract; authors include German and US affiliations.",
        "material_scope": "Cultivated ryegrass and maize mini-silo silages during post-opening feed-out exposure.",
        "experimental_context": (
            "1.5-L glass jars with and without a commercial bio-additive; samples exposed to air "
            "immediately at start of the feed-out test. Abstract reports 320 h total maize test "
            "and 600 h total ryegrass test. Initial emission summaries apply to the 0–10 h "
            "aerobic-stable period."
        ),
        "data_scope": (
            "Four abstract-reported initial area-normalized emission summaries (two materials by "
            "two gases) and two approximate CO2/ethanol emission lags. No time-series points or raw data."
        ),
        "evidence_class": "B_measured_literature_abstract_extract",
        "quality_class": "B",
        "license": (
            "Publisher record marks the article open access under a Creative Commons license, "
            "but the exact license text was not accessible during this extraction. Only attributed "
            "abstract-level factual values are stored; confirm license terms before external redistribution."
        ),
        "data_availability": "The article abstract states that data will be made available on request; no underlying time series was accessed.",
        "conversion_or_processing": (
            "Direct transcription of abstract values. The reported 10^-2 scale is retained in the unit; "
            "the ± term is retained separately without assigning SD/SE or another statistic. "
            "No mass normalization, interpolation, kinetic fit, or emission-factor calculation."
        ),
        "uncertainty": (
            "Abstract reports a ± term for four emission summaries but does not identify its statistical "
            "meaning, replicate count, treatment aggregation, or area definition. Approximate lags have "
            "no interval reported."
        ),
        "limitations": [
            "Cultivated crop silages in mini-jars are not Dutch roadside grass or GreenHub storage.",
            "The reported emission basis is mol m^-2; no feed mass or dry matter denominator is given.",
            "The ± statistic and aggregation across additive treatments are unspecified in the abstract.",
            "The data statement says underlying data are available on request; no time series or replicate data were obtained.",
            "The study concerns feed-out exposure after opening, not sealed-storage degradation kinetics.",
            "No values are connected to storage equations, LCA factors, defaults, runtime, TEA or Pareto calculations.",
        ],
        "runtime_policy": "Reference-only; not mapped to storage model or LCA because feed-mass scaling and variability definition are unresolved.",
        "access_protocol": "Publisher article/abstract available via HTTPS DOI; underlying dataset stated available on request.",
        "fair_metadata": {
            "findable": "Local URN, source ID, DOI, publisher URL, and SHA-256 recorded.",
            "accessible": "UTF-8 CSV and JSON sidecar stored locally; source abstract is retrievable over HTTPS.",
            "interoperable": "Long-form observations preserve phase, material, condition, response, source unit and unknown basis/statistic fields.",
            "reusable": "Provenance, source-access limitation, uncertainty ambiguity, applicability and no-runtime-use policy are explicit.",
        },
    }
    (STORAGE / f"{FILENAME}.source.json").write_text(json.dumps(sidecar, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    append_once(STORAGE / "source_register.csv", {
        "source_id": SOURCE_ID, "source_title": SOURCE_TITLE, "authors": AUTHORS,
        "year": "2026", "source_type": "peer-reviewed primary experimental article; abstract-level measured emission extract",
        "doi_or_stable_identifier": DOI, "stable_url": DOI_URL,
        "material": "Cultivated ryegrass and maize mini-silo silage during post-opening feed-out exposure",
        "quality_notes": "Six abstract facts; ± statistic, feed-mass denominator and treatment aggregation unresolved; data on request; reference-only.",
        "accessed_date": RETRIEVED,
    }, "source_id")
    append_once(STORAGE / "dataset_manifest.csv", {
        "filename": FILENAME,
        "description": "Four abstract-reported initial area-normalized CO2/ethanol emission summaries and two approximate emission lags; no feed-mass normalization or kinetic fit.",
        "row_count": len(ROWS), "schema_version": "1.0", "encoding": "UTF-8", "delimiter": ",",
        "integration_status": "traceable_reference_only_not_runtime_eligible", "primary_key": "observation_id",
    }, "filename")

    relative_path = f"storage/{FILENAME}"
    audit = DATA / "global_audit_package"
    append_once(audit / "global_source_register.csv", {
        "dataset_path": relative_path, "dataset_group": "storage", "source_id": SOURCE_ID,
        "source_title": SOURCE_TITLE, "authors": AUTHORS, "year": "2026", "doi_or_stable_id": DOI,
        "url": PUBLISHER_URL, "source_type": "peer-reviewed primary experimental article; abstract-level extract",
        "notes": "Phase 2 post-opening emissions; uncertainty statistic, treatment aggregation and feed-mass denominator unresolved; reference-only.",
    }, "dataset_path")
    append_once(audit / "global_dataset_manifest.csv", {
        "dataset_path": relative_path, "category": "storage", "subgroup": "storage", "filename": FILENAME,
        "row_count_observed": len(ROWS), "header_count": len(FIELDS), "headers": "; ".join(FIELDS),
        "standardized_status_values": "B;reference_only", "detected_readiness": "D3",
        "notes": "Six source-located abstract facts; no dry-matter/mass scaling or runtime connection.",
    }, "dataset_path")
    append_once(audit / "global_dataset_readiness.csv", {
        "dataset_path": relative_path, "category": "storage", "subgroup": "storage", "readiness": "D3",
        "duplicate_ids": 0, "duplicate_rows": 0, "numeric_rows": 6, "unsourced_numeric_rows": 0,
        "numeric_rows_missing_exact_location": 0, "unit_conflicts": 0, "basis_conflicts": 0,
        "cross_reference_issues": 0, "equation_missing_inputs": 0, "equation_symbol_mismatches": 0,
        "notes": "Abstract-only numeric facts; source locations explicit; basis/statistic caveats prevent calculation use.",
    }, "dataset_path")

    summary_path = audit / "global_validation_summary.json"
    if summary_path.exists():
        summary = json.loads(summary_path.read_text(encoding="utf-8"))
        _, manifests = read_csv(audit / "global_dataset_manifest.csv")
        _, readiness_rows = read_csv(audit / "global_dataset_readiness.csv")
        summary["dataset_count"] = len(manifests)
        summary["generated_at"] = datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")
        counts: dict[str, int] = {}
        for item in readiness_rows:
            value = item.get("readiness", "")
            counts[value] = counts.get(value, 0) + 1
        summary["readiness_counts"] = counts
        summary_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    print(json.dumps({"dataset": FILENAME, "rows": len(ROWS), "sha256": digest, "source_id": SOURCE_ID}, indent=2))


if __name__ == "__main__":
    main()
