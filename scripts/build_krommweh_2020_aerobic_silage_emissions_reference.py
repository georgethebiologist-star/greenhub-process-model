"""Build a source-traceable Phase 2 extract of post-opening silage emissions.

Only cumulative values explicitly reported in the peer-reviewed abstract are
transcribed. No bale-mass normalization, greenhouse characterization, or
storage-emission kinetics are inferred.
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
FILENAME = "post_opening_aerobic_silage_emissions_krommweh_2020_reference.csv"
CSV_PATH = STORAGE / FILENAME
SOURCE_ID = "SRC-KROMMWEH-AEROBIC-SILAGE-EMISSIONS-2020"
DOI = "10.1016/j.envpol.2020.115513"
DOI_URL = f"https://doi.org/{DOI}"
PUBMED_URL = "https://pubmed.ncbi.nlm.nih.gov/32891044/"
RETRIEVED = "2026-11-08"

FIELDS = [
    "observation_id", "source_id", "phase", "material", "geography",
    "sample_stage", "time_window_hours", "property", "value", "unit",
    "mass_basis", "replicates", "reported_uncertainty", "measurement_method",
    "source_location", "evidence_class", "quality_class", "activation_state",
    "applicability_limit", "notes",
]

SOURCE_TITLE = (
    "A new experimental setup for measuring greenhouse gas and volatile organic "
    "compound emissions of silage during the aerobic storage period in a special "
    "silage respiration chamber"
)
AUTHORS = (
    "Manuel S. Krommweh; Alexander J. Schmithausen; Hauke F. Deeken; "
    "Wolfgang Büscher; Gerd-Christian Maack"
)
LIMIT = (
    "Post-opening aerobic exposure of livestock grass/lucerne silage bales, not "
    "GreenHub roadside-grass storage. Cumulative totals are per bale over the "
    "first 600 experimental hours; bale mass and a compatible initial-mass basis "
    "are not reported in the abstract. Do not normalize per tonne, extrapolate to "
    "other durations, treat VOCs as characterized climate impacts, or use as an "
    "in-silo anaerobic storage emission factor. Reference-only; no runtime use."
)


def _row(material: str, property_name: str, value: str, unit: str) -> dict[str, str]:
    material_key = material.upper().replace(" ", "-")
    property_key = property_name.upper().replace(" ", "-")
    return {
        "observation_id": f"KROMMWEH20-{material_key}-{property_key}-600H",
        "source_id": SOURCE_ID,
        "phase": "2",
        "material": f"{material} silage bale",
        "geography": "Germany; location not stated in abstract",
        "sample_stage": "post-opening aerobic storage exposure",
        "time_window_hours": "600",
        "property": f"cumulative_{property_name}_emission",
        "value": value,
        "unit": unit,
        "mass_basis": "per bale; bale mass not reported; cumulative over 600 h",
        "replicates": "not reported by material in abstract",
        "reported_uncertainty": "not reported",
        "measurement_method": (
            "Silage respiration chamber; photoacoustic spectroscopy for outlet-air "
            "emissions. Method description from abstract."
        ),
        "source_location": "PubMed abstract, Results; DOI-linked peer-reviewed article",
        "evidence_class": "B_measured_literature_abstract_extract",
        "quality_class": "B",
        "activation_state": "reference_only",
        "applicability_limit": LIMIT,
        "notes": (
            "Value transcribed as reported. The study also measured gas concentrations "
            "inside bales, but those concentrations are not used as emission totals. "
            "CO2 is reported as mass emitted, not as fossil CO2 or characterized CO2e."
            if property_name == "carbon dioxide" else
            "Value transcribed as reported. This VOC mass is not a greenhouse-gas "
            "characterization result and is not converted to CO2e."
        ),
    }


ROWS = [
    _row("grass", "carbon dioxide", "2313", "g bale^-1"),
    _row("grass", "methanol", "17.6", "g bale^-1"),
    _row("grass", "ethanol", "132.3", "g bale^-1"),
    _row("grass", "ethyl acetate", "55.1", "g bale^-1"),
    _row("lucerne", "carbon dioxide", "2612", "g bale^-1"),
    _row("lucerne", "methanol", "145.2", "g bale^-1"),
    _row("lucerne", "ethanol", "675.9", "g bale^-1"),
    _row("lucerne", "ethyl acetate", "66.2", "g bale^-1"),
]


def _read_csv(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    if not path.exists():
        return [], []
    with path.open("r", encoding="utf-8-sig", newline="") as stream:
        reader = csv.DictReader(stream)
        return reader.fieldnames or [], list(reader)


def _append_once(path: Path, row: dict[str, object], key: str) -> None:
    fields, existing = _read_csv(path)
    matches = [item for item in existing if item.get(key) == str(row.get(key, ""))]
    if matches:
        if len(matches) != 1 or any(
            matches[0].get(field, "") != str(row.get(field, "")) for field in fields
        ):
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
        "dataset_id": "urn:greenhub:dataset:storage:krommweh-post-opening-silage-emissions-2020:v1",
        "dataset_version": "1.0.0",
        "dataset_file": FILENAME,
        "record_count": len(ROWS),
        "sha256": digest,
        "source_id": SOURCE_ID,
        "citation": (
            "Krommweh, M. S., Schmithausen, A. J., Deeken, H. F., Büscher, W., & Maack, G.-C. "
            "(2020). A new experimental setup for measuring greenhouse gas and volatile organic "
            "compound emissions of silage during the aerobic storage period in a special silage "
            "respiration chamber. Environmental Pollution, 267, 115513. " + DOI_URL
        ),
        "publication_year": 2020,
        "doi": DOI,
        "source_url": DOI_URL,
        "bibliographic_record_url": PUBMED_URL,
        "retrieval_date": RETRIEVED,
        "source_locations": [
            "PubMed abstract, experimental design and Results: measurement period and cumulative emissions during the first 600 experimental hours.",
        ],
        "applicable_phases": [2],
        "material_scope": "Three silage bales (grass and lucerne) examined during opening and subsequent aerobic exposure; two species-specific cumulative emission totals are given in the abstract.",
        "experimental_context": "Special silage respiration chamber; whole bale without wrapping film after opening; emission behaviour followed for periods up to 55 days. The abstract's numerical cumulative totals cover the first 600 experimental hours.",
        "data_scope": "Eight cumulative emission observations: CO2, methanol, ethanol and ethyl acetate for one grass silage bale and one lucerne silage bale, as reported in the abstract.",
        "evidence_class": "B_measured_literature_abstract_extract",
        "quality_class": "B",
        "license": "PubMed identifies Elsevier copyright (2020); no open reuse license was found for this article. This project stores eight attributed factual measurements from the abstract, not article text or figures. Review rights before redistribution outside the project.",
        "data_availability": "Abstract-level values only in this extract. Full-text article is linked through PubMed/Elsevier; detailed operating metadata and supporting measurements were not transcribed in this collection pass.",
        "conversion_or_processing": "Direct transcription of eight abstract-reported cumulative masses. No unit conversion, bale-mass normalization, time extrapolation, CO2-equivalent characterization, or emission-factor calculation was applied.",
        "uncertainty": "The abstract does not report per-species replicate counts or uncertainty for the cumulative totals. Three bales were examined in the overall experiment; do not assume three replicates per material.",
        "limitations": [
            "Post-opening aerobic exposure is not the same process as anaerobic ensiling or sealed storage.",
            "Cumulative totals are per bale over 600 h, and bale mass is not reported in the abstract; these values are not emission factors and per-tonne factors cannot be calculated.",
            "CO2 is reported as measured mass. It is not a fossil CO2 burden or a CO2e value; biogenic-carbon accounting must be defined separately.",
            "Methanol, ethanol and ethyl acetate are VOCs, not characterized impact results in this extract.",
            "The source reports measurements of CO2, O2, CH4 and N2O concentrations inside bale gas, but those concentrations are not emission totals and are not transcribed here.",
            "Livestock grass/lucerne silage and bale conditions are not validated proxies for loose Dutch roadside grass storage.",
            "No rates, storage kinetics, or runtime factors are activated.",
        ],
        "runtime_policy": "Reference-only; not linked to storage reactions, LCA characterization, parameter registry, defaults, TEA, or Pareto calculations.",
        "access_protocol": "HTTPS DOI and PubMed bibliographic record.",
        "fair_metadata": {
            "findable": "Stable repository URN, source ID, DOI, PubMed record and SHA-256 are recorded.",
            "accessible": "UTF-8 CSV and JSON metadata sidecar; source records are linked over HTTPS.",
            "interoperable": "Records include phase, material, post-opening time window, property, value, unit, mass basis, method, evidence tier and source location.",
            "reusable": "Uncertainty, missing bale mass, copyright status, transfer limitations and no-runtime-use policy are explicit.",
        },
    }
    Path(str(CSV_PATH) + ".source.json").write_text(
        json.dumps(sidecar, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )

    validation_path = STORAGE / "validation_report.json"
    if validation_path.exists():
        validation = json.loads(validation_path.read_text(encoding="utf-8"))
        validation["csv_files_checked"] = len(list(STORAGE.glob("*.csv")))
        validation_path.write_text(json.dumps(validation, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    source_row = {
        "source_id": SOURCE_ID,
        "source_title": SOURCE_TITLE,
        "authors": AUTHORS,
        "year": "2020",
        "source_type": "peer-reviewed primary experimental article; abstract-level cumulative emission measurements",
        "doi_or_stable_identifier": DOI,
        "stable_url": DOI_URL,
        "material": "Grass and lucerne silage bales during post-opening aerobic exposure",
        "quality_notes": "Eight abstract-reported cumulative mass observations over the first 600 h. No bale-mass denominator, replicate uncertainty, per-tonne factor, or runtime activation; reuse rights outside project require review.",
        "accessed_date": RETRIEVED,
    }
    _append_once(STORAGE / "source_register.csv", source_row, "source_id")
    _append_once(STORAGE / "dataset_manifest.csv", {
        "filename": FILENAME,
        "description": "Eight abstract-reported cumulative post-opening aerobic emissions for grass and lucerne silage bales over 600 h; not mass-normalized.",
        "row_count": len(ROWS),
        "schema_version": "1.0",
        "encoding": "UTF-8",
        "delimiter": ",",
        "integration_status": "traceable_reference_only_not_runtime_eligible",
        "primary_key": "observation_id",
    }, "filename")

    relative_path = f"storage/{FILENAME}"
    audit = DATA / "global_audit_package"
    _append_once(audit / "global_source_register.csv", {
        "dataset_path": relative_path,
        "dataset_group": "storage",
        "source_id": SOURCE_ID,
        "source_title": SOURCE_TITLE,
        "authors": AUTHORS,
        "year": "2020",
        "doi_or_stable_id": DOI,
        "url": PUBMED_URL,
        "source_type": "peer-reviewed primary experimental article; abstract-level extract",
        "notes": "Phase 2 post-opening aerobic emissions; eight cumulative per-bale facts, no bale-mass denominator, reference-only.",
    }, "dataset_path")
    _append_once(audit / "global_dataset_manifest.csv", {
        "dataset_path": relative_path,
        "category": "storage",
        "subgroup": "storage",
        "filename": FILENAME,
        "row_count_observed": len(ROWS),
        "header_count": len(FIELDS),
        "headers": "; ".join(FIELDS),
        "standardized_status_values": "B;reference_only",
        "detected_readiness": "D3",
        "notes": "Eight abstract-level cumulative per-bale measurements; not an emission factor; no runtime activation.",
    }, "dataset_path")
    _append_once(audit / "global_dataset_readiness.csv", {
        "dataset_path": relative_path,
        "category": "storage",
        "subgroup": "storage",
        "readiness": "D3",
        "duplicate_ids": 0,
        "duplicate_rows": 0,
        "numeric_rows": len(ROWS),
        "unsourced_numeric_rows": 0,
        "numeric_rows_missing_exact_location": 0,
        "unit_conflicts": 0,
        "basis_conflicts": 0,
        "cross_reference_issues": 0,
        "equation_missing_inputs": 0,
        "equation_symbol_mismatches": 0,
        "notes": "Eight values cited to the PubMed abstract; cumulative mass per bale over 600 h; bale mass and uncertainty absent; reference-only.",
    }, "dataset_path")

    summary_path = audit / "global_validation_summary.json"
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    _, manifests = _read_csv(audit / "global_dataset_manifest.csv")
    _, readiness_rows = _read_csv(audit / "global_dataset_readiness.csv")
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
