"""Register the Table 1 wet-fractionation measurements from Aakjaer Pedersen et al. (2025).

The extract is a traceable, reference-only literature dataset. It does not
calibrate roadside grass or activate a GreenHub runtime parameter.
"""
from __future__ import annotations

import csv
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "Greenhub" / "data"
PACKAGE = DATA / "Pre-treatment" / "Mechanical"
AUDIT = DATA / "global_audit_package"
FILENAME = "perennial_ryegrass_wet_fractionation_aakjaer_pedersen_2025_reference.csv"
CSV_PATH = PACKAGE / FILENAME
SIDECAR_PATH = Path(str(CSV_PATH) + ".source.json")
DOI = "10.3390/proteomes13010008"
DOI_URL = f"https://doi.org/{DOI}"
ARTICLE_URL = "https://www.mdpi.com/2227-7382/13/1/8"
SOURCE_ID = "S14_AAKJAER_PEDERSEN_2025"
TITLE = "Identifying Endogenous Proteins of Perennial Ryegrass (Lolium perenne) with Ex Vivo Antioxidant Activity"
AUTHORS = "Aakjaer Pedersen; Andersen; Heiselberg; Brigsted; Støvring; Mailund Mikkelsen; Hansen; Rusbjerg-Weberskov; Lübeck; Echers"
RETRIEVED = "2026-11-08"

FIELDS = [
    "record_id", "source_id", "source_title", "authors", "publication_year",
    "species_or_feedstock", "cultivation_batch", "process_step", "stream",
    "metric", "reported_value", "reported_sd", "uncertainty_statistic",
    "reported_unit", "normalized_value", "normalized_sd", "normalized_unit",
    "basis", "replicate_count", "source_location", "evidence_class",
    "quality_class", "transferability", "readiness", "activation_state", "notes",
]

COMMON = (
    "Controlled-growth-chamber perennial ryegrass (Lolium perenne var. Abosan 1), "
    "not Dutch roadside/VARTA grass. Table 1 reports batch-2 crude fractions after "
    "immediate wet fractionation using an Angelia 8500 S juicer at standard settings. "
    "Reference-only comparator; not a GreenHub default, runtime parameter, or complete "
    "press balance."
)


def _record(record_id: str, stream: str, metric: str, value: str, reported_unit: str,
            normalized_value: str, normalized_unit: str, basis: str, *, sd: str = "",
            uncertainty_statistic: str = "not_reported", note: str = "") -> dict[str, str]:
    normalized_sd = ""
    if sd:
        normalized_sd = str(float(sd) / 100 if "percent" in reported_unit.lower() else float(sd))
    return {
        "record_id": record_id,
        "source_id": SOURCE_ID,
        "source_title": TITLE,
        "authors": AUTHORS,
        "publication_year": "2025",
        "species_or_feedstock": "Lolium perenne var. Abosan 1",
        "cultivation_batch": "Batch 2; 50 days in controlled growth chamber",
        "process_step": "Immediate wet fractionation; Angelia 8500 S juicer, standard settings",
        "stream": stream,
        "metric": metric,
        "reported_value": value,
        "reported_sd": sd,
        "uncertainty_statistic": uncertainty_statistic,
        "reported_unit": reported_unit,
        "normalized_value": normalized_value,
        "normalized_sd": normalized_sd,
        "normalized_unit": normalized_unit,
        "basis": basis,
        "replicate_count": "n >= 3 (Table 1 footnote; no exact n reported)",
        "source_location": "Table 1; Methods §§2.1–2.2; Results §3.1",
        "evidence_class": "B_measured_literature",
        "quality_class": "B",
        "transferability": "perennial_grass_laboratory_comparator",
        "readiness": "D3_reference_only",
        "activation_state": "reference_only",
        "notes": f"{COMMON} {note}".strip(),
    }


ROWS = [
    _record("AAP25-001", "raw grass", "fraction fresh mass", "75.2", "g per Table 1 sample", "75.2", "g per Table 1 sample", "fresh mass"),
    _record("AAP25-002", "raw grass", "dry matter concentration", "19.2", "percent wet basis", "0.192", "kg DM/kg wet grass", "wet mass", sd="1.1", uncertainty_statistic="SD"),
    _record("AAP25-003", "raw grass", "dry matter distribution", "100", "percent of input DM", "1.00", "kg DM/kg input DM", "input DM"),
    _record("AAP25-004", "raw grass", "crude protein concentration", "11.2", "percent DM", "0.112", "kg CP/kg DM", "dry matter", sd="0.4", uncertainty_statistic="SD", note="CP estimated from elemental nitrogen using N × 6.25."),
    _record("AAP25-005", "raw grass", "crude protein distribution", "100", "percent of input CP", "1.00", "kg CP/kg input CP", "input CP"),
    _record("AAP25-006", "pulp", "fraction fresh mass", "32.9", "g per Table 1 sample", "32.9", "g per Table 1 sample", "fresh mass"),
    _record("AAP25-007", "pulp", "dry matter concentration", "27.7", "percent wet basis", "0.277", "kg DM/kg wet pulp", "wet mass", sd="3.1", uncertainty_statistic="SD"),
    _record("AAP25-008", "pulp", "dry matter distribution", "63.0", "percent of input DM", "0.630", "kg DM/kg input DM", "input DM"),
    _record("AAP25-009", "pulp", "crude protein concentration", "10.4", "percent DM", "0.104", "kg CP/kg DM", "dry matter", sd="0.4", uncertainty_statistic="SD", note="CP estimated from elemental nitrogen using N × 6.25."),
    _record("AAP25-010", "pulp", "crude protein distribution", "58.7", "percent of input CP", "0.587", "kg CP/kg input CP", "input CP"),
    _record("AAP25-011", "green juice", "fraction fresh mass", "34.4", "g per Table 1 sample", "34.4", "g per Table 1 sample", "fresh mass"),
    _record("AAP25-012", "green juice", "dry matter concentration", "15.5", "percent wet basis", "0.155", "kg DM/kg wet juice", "wet mass", sd="2.1", uncertainty_statistic="SD"),
    _record("AAP25-013", "green juice", "dry matter distribution", "36.9", "percent of input DM", "0.369", "kg DM/kg input DM", "input DM"),
    _record("AAP25-014", "green juice", "crude protein concentration", "12.5", "percent DM", "0.125", "kg CP/kg DM", "dry matter", sd="0.5", uncertainty_statistic="SD", note="CP estimated from elemental nitrogen using N × 6.25."),
    _record("AAP25-015", "green juice", "crude protein distribution", "41.0", "percent of input CP", "0.410", "kg CP/kg input CP", "input CP"),
]


def _read(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    if not path.exists():
        return [], []
    with path.open(encoding="utf-8-sig", newline="") as stream:
        reader = csv.DictReader(stream)
        return reader.fieldnames or [], list(reader)


def _upsert(path: Path, row: dict[str, object], key: str) -> None:
    fields, rows = _read(path)
    if not fields:
        raise ValueError(f"Missing CSV header: {path}")
    values = {field: str(row.get(field, "")) for field in fields}
    matches = [i for i, existing in enumerate(rows) if existing.get(key) == values.get(key)]
    if matches:
        rows[matches[0]] = values
        rows = [item for i, item in enumerate(rows) if i == matches[0] or item.get(key) != values.get(key)]
    else:
        rows.append(values)
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    PACKAGE.mkdir(parents=True, exist_ok=True)
    with CSV_PATH.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=FIELDS, lineterminator="\n")
        writer.writeheader()
        writer.writerows(ROWS)

    digest = hashlib.sha256(CSV_PATH.read_bytes()).hexdigest()
    sidecar = {
        "dataset_id": "urn:greenhub:dataset:perennial-ryegrass-wet-fractionation-aakjaer-pedersen-2025:v1",
        "dataset_title": "Perennial ryegrass wet-fractionation mass balance and crude-protein partition (Table 1 extract)",
        "source_dataset_path": f"Greenhub/data/Pre-treatment/Mechanical/{FILENAME}",
        "source_data_sha256": digest,
        "rows": len(ROWS),
        "persistent_identifier": DOI,
        "source_url": DOI_URL,
        "article_url": ARTICLE_URL,
        "source_title": TITLE,
        "authors": AUTHORS.split("; "),
        "journal": "Proteomes",
        "publication": "2025, 13(1), 8",
        "publication_date": "2025-02-05",
        "source_location": "Table 1; Methods §§2.1–2.2; Results §3.1",
        "retrieval_date": RETRIEVED,
        "geography": "Aalborg University, Denmark; controlled growth chamber",
        "material_scope": "Lolium perenne var. Abosan 1, batch 2, cultivated for 50 days; fresh grass, pulp and green juice",
        "evidence_class": "B",
        "data_type": "measured literature observations; source table means and reported standard deviations",
        "license": "CC BY 4.0",
        "conversion_policy": "Percentages were divided by 100 for fraction-valued normalized fields. No fresh-to-dry, density, mass-flow, or protein-speciation conversions were inferred.",
        "uncertainty": "Table 1 reports mean ± SD (n >= 3) for dry-matter and crude-protein concentrations. The exact n is not stated in the table; wet fraction masses and distribution percentages have no printed SD.",
        "limitations": [
            "Controlled-grown perennial ryegrass is not roadside/VARTA grass and is not a seasonal or site-specific GreenHub feed sample.",
            "The article uses a laboratory juicer at standard settings; operating settings and scale are not a GreenHub screw-press validation.",
            "The apparent wet-mass deficit is not an independently measured water-loss stream; do not use it as a process loss coefficient.",
            "Crude protein is total nitrogen multiplied by 6.25; it is not a soluble-protein assay.",
            "No runtime parameter, model default, parameter-registry value, TEA/LCA factor, or Pareto result is activated from this extract."
        ],
        "activation_state": "reference_only",
        "readiness": "D3",
        "citation": f"Aakjaer Pedersen et al. (2025). {TITLE}. Proteomes 13(1), 8. https://doi.org/{DOI}",
    }
    SIDECAR_PATH.write_text(json.dumps(sidecar, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    local_source = {
        "source_id": SOURCE_ID,
        "source_type": "peer_reviewed_open_access_article",
        "title": TITLE,
        "authors": AUTHORS,
        "year": "2025",
        "doi_or_stable_identifier": DOI,
        "publisher": "MDPI; Proteomes 13(1), 8",
        "url": DOI_URL,
        "material_scope": sidecar["material_scope"],
        "source_quality": "Peer-reviewed primary experimental study; Table 1 means; CC BY 4.0",
        "access_date": RETRIEVED,
        "notes": "Table 1 extraction for Phases 1/3/4 comparator discovery. Table 1: mass, DM and CP distribution across raw grass, pulp and juice. Controlled-grown perennial ryegrass, reference-only and not roadside-grass calibration.",
    }
    _upsert(PACKAGE / "source_register.csv", local_source, "source_id")
    _upsert(PACKAGE / "dataset_manifest.csv", {
        "dataset_id": "DS-008",
        "filename": FILENAME,
        "purpose": "Table 1 fresh-mass, dry-matter and crude-protein wet-fractionation reference observations for perennial ryegrass",
        "row_count": len(ROWS),
        "primary_key": "record_id",
        "encoding": "UTF-8",
        "delimiter": ",",
        "integration_readiness": "reference_only_not_runtime_eligible",
        "material_state_rule": "Wet-mass concentration bases, dry-matter concentration bases, and input-component distributions are separately labelled.",
        "known_limitations": "Controlled-grown forage, laboratory juicer, no roadside transfer validation, no soluble-protein assay or runtime activation.",
    }, "filename")

    rel = f"Pre-treatment/Mechanical/{FILENAME}"
    _upsert(AUDIT / "global_source_register.csv", {
        "dataset_path": rel,
        "dataset_group": "Pre-treatment/Mechanical",
        "source_id": SOURCE_ID,
        "source_title": TITLE,
        "authors": AUTHORS,
        "year": "2025",
        "doi_or_stable_id": DOI,
        "url": DOI_URL,
        "source_type": "peer_reviewed_open_access_article; CC BY 4.0",
        "notes": "Table 1, controlled-grown perennial ryegrass wet-fractionation measurements; B-tier, D3/reference-only; not roadside-grass calibration.",
    }, "dataset_path")
    _upsert(AUDIT / "global_dataset_manifest.csv", {
        "dataset_path": rel,
        "category": "Pre-treatment",
        "subgroup": "Mechanical",
        "filename": FILENAME,
        "row_count_observed": len(ROWS),
        "header_count": len(FIELDS),
        "headers": "; ".join(FIELDS),
        "standardized_status_values": "B;reference_only",
        "detected_readiness": "D3",
        "notes": "Table 1 values; normalized percentages only; controlled-grown forage comparator; no runtime activation.",
    }, "dataset_path")
    _upsert(AUDIT / "global_dataset_readiness.csv", {
        "dataset_path": rel,
        "category": "Pre-treatment",
        "subgroup": "Mechanical",
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
        "notes": "Source-located Table 1 reference extract with explicit wet/dry bases; not roadside-specific or runtime eligible.",
    }, "dataset_path")
    _upsert(AUDIT / "source_dataset_checksums.csv", {
        "dataset_path": rel,
        "sha256": digest,
        "byte_size": CSV_PATH.stat().st_size,
    }, "dataset_path")

    summary_path = AUDIT / "global_validation_summary.json"
    if summary_path.exists():
        summary = json.loads(summary_path.read_text(encoding="utf-8"))
        _, manifests = _read(AUDIT / "global_dataset_manifest.csv")
        _, readiness = _read(AUDIT / "global_dataset_readiness.csv")
        summary["dataset_count"] = len(manifests)
        summary["generated_at"] = datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")
        counts: dict[str, int] = {}
        for row in readiness:
            key = row.get("readiness", "")
            counts[key] = counts.get(key, 0) + 1
        summary["readiness_counts"] = counts
        summary_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    print(json.dumps({"dataset": rel, "rows": len(ROWS), "source_id": SOURCE_ID, "sha256": digest, "activation_state": "reference_only"}, indent=2))


if __name__ == "__main__":
    main()
