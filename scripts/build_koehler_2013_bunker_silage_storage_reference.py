"""Extract reported grass-bunker-silo summary evidence from Köhler et al. (2013).

The figures are farm-scale context for whole-silo losses, not roadside-grass
storage kinetics; the source's negative estimate is retained as a measurement
artifact and must never be interpreted as physical biomass generation.
"""
from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "Greenhub" / "data"
GROUP = DATA / "storage"
AUDIT = DATA / "global_audit_package"
FILENAME = "koehler_2013_farm_scale_grass_bunker_silo_storage_reference.csv"
CSV_PATH = GROUP / FILENAME
SIDECAR_PATH = Path(str(CSV_PATH) + ".source.json")
SOURCE_ID = "SRC-KOEHLER-2013-GRASS-BUNKER-SILO"
TITLE = "Dry matter losses of grass, lucerne and maize silages in bunker silos"
DOI = "10.23986/afsci.6715"
DOI_URL = f"https://doi.org/{DOI}"
PDF_URL = "https://journal.fi/afs/article/download/6715/6056/19691"
RETRIEVED = "2026-11-08"
FIELDS = [
    "record_id", "source_id", "study_title", "material_scope", "metric",
    "statistic", "reported_value", "unit", "basis", "sample_n", "source_location",
    "measurement_scope", "evidence_class", "quality_class", "activation_state",
    "transferability", "limitations", "retrieval_date",
]

LIMITATIONS = (
    "German dairy-farm bunker silage, not roadside/VARTA biomass or GreenHub storage. Total-in versus total-out "
    "covers silo ensiling/storage and feed-out as a combined interval; it is not a duration-resolved degradation "
    "kinetic or an aerobic-versus-anaerobic comparison. Negative reported loss is measurement/accounting error, "
    "not physical mass gain and must not be used as a negative loss coefficient. No runtime mapping or default."
)
CONTEXT = "26 grass silos on one organic and two conventional Bavarian farms; data collected 2008–2011; sealed for at least 6 weeks; feed-out averaged 3 months; grass sources included permanent grassland and some grass-clover/annual ryegrass."

ROWS = [
    ("DMLOSS-MEAN", "dry-matter loss", "mean", "9", "%", "percent of silage DM input", "26", "Results §3; p. 148", "Total-in versus total-out; combined silo period including feed-out."),
    ("DMLOSS-MIN", "dry-matter loss", "minimum", "-2", "%", "percent of silage DM input", "26", "Results §3; p. 148", "Negative estimate attributed by the authors to method/data precision; not physical loss."),
    ("DMLOSS-MAX", "dry-matter loss", "maximum", "26", "%", "percent of silage DM input", "26", "Results §3; p. 148", "Highest grass-silo loss; paper notes reheating, butyric acid, and low feed-out rate for this silo."),
    ("DENSITY-MEAN", "silo density", "mean", "194", "kg DM/m3", "dry matter per silo volume", "22", "Table 2; p. 147", "Measured on silo face; summary sample count differs from 26 total grass silos."),
    ("DENSITY-RANGE-MIN", "silo density", "minimum", "155", "kg DM/m3", "dry matter per silo volume", "22", "Table 2; p. 147", "Reported range minimum."),
    ("DENSITY-RANGE-MAX", "silo density", "maximum", "278", "kg DM/m3", "dry matter per silo volume", "22", "Table 2; p. 147", "Reported range maximum."),
    ("FEEDOUT-MEAN", "feed-out rate", "mean", "2.1", "m/week", "silo-face advance", "19", "Table 2; p. 147", "Silo-face advance; not a mass throughput rate."),
    ("FEEDOUT-RANGE-MIN", "feed-out rate", "minimum", "1.1", "m/week", "silo-face advance", "19", "Table 2; p. 147", "Reported range minimum."),
    ("FEEDOUT-RANGE-MAX", "feed-out rate", "maximum", "3.4", "m/week", "silo-face advance", "19", "Table 2; p. 147", "Reported range maximum."),
    ("CORR-DENSITY", "Pearson correlation: density vs DM loss", "correlation", "-0.039", "dimensionless", "Pearson r", "18 paired observations", "Table 3; p. 148", "No meaningful/significant grass-silo density correlation reported."),
    ("CORR-FEEDOUT", "Pearson correlation: feed-out rate vs DM loss", "correlation", "-0.570", "dimensionless", "Pearson r", "19 paired observations", "Table 3; p. 148", "Reported significant at 0.01 < p < 0.05; correlation is not a causal coefficient."),
    ("SILO-CLOSED", "closed storage duration", "minimum", "6", "weeks", "minimum closed silo duration", "not applicable", "Methods; p. 146", "All silos remained closed at least six weeks before feed-out."),
    ("FEEDOUT-DURATION", "feed-out duration", "mean", "3", "months", "average removal period", "not applicable", "Methods; p. 146", "Average removal period, not a measured residence-time distribution."),
]


def _read(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    if not path.exists():
        return [], []
    with path.open(encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        return reader.fieldnames or [], list(reader)


def _upsert(path: Path, row: dict[str, object], key: str) -> None:
    fields, rows = _read(path)
    if not fields:
        raise ValueError(f"Missing CSV header: {path}")
    values = {field: str(row.get(field, "")) for field in fields}
    rows = [old for old in rows if old.get(key) != values[key]]
    rows.append(values)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    records = [{
        "record_id": f"KOH13-{rid}", "source_id": SOURCE_ID, "study_title": TITLE,
        "material_scope": CONTEXT, "metric": metric, "statistic": stat,
        "reported_value": value, "unit": unit, "basis": basis, "sample_n": n,
        "source_location": location, "measurement_scope": scope,
        "evidence_class": "B_measured_farm_scale_literature_summary", "quality_class": "B",
        "activation_state": "reference_only",
        "transferability": "farm_scale_livestock_grass_silage_not_roadside_or_GreenHub_storage",
        "limitations": LIMITATIONS, "retrieval_date": RETRIEVED,
    } for rid, metric, stat, value, unit, basis, n, location, scope in ROWS]
    with CSV_PATH.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS, lineterminator="\n")
        writer.writeheader()
        writer.writerows(records)
    digest = hashlib.sha256(CSV_PATH.read_bytes()).hexdigest()
    sidecar = {
        "dataset_id": "urn:greenhub:dataset:koehler-2013-grass-bunker-silo-storage-reference:v1",
        "dataset_title": "Farm-scale grass bunker-silo loss and management summary extract",
        "source_dataset_path": f"Greenhub/data/storage/{FILENAME}", "source_data_sha256": digest,
        "rows": len(records), "persistent_identifier": DOI, "source_url": DOI_URL,
        "full_text_url": PDF_URL, "source_id": SOURCE_ID, "source_title": TITLE,
        "authors": ["Brigitte Köhler", "Michael Diepolder", "Johannes Ostertag", "Stefan Thurner", "Hubert Spiekers"],
        "journal": "Agricultural and Food Science", "publication": "2013, 22, 145–150",
        "source_location": "Table 2 p. 147; Table 3 and Results p. 148; Methods pp. 145–146",
        "retrieval_date": RETRIEVED, "geography": "Bavaria, Germany",
        "material_scope": CONTEXT,
        "data_type": "primary farm measurements reported as summary statistics; underlying silo-level rows not reported as an open data file",
        "license_or_rights": "Publisher/article page identifies copyright; no explicit open reuse license was confirmed. Only a short factual summary with attribution is stored; do not redistribute the article PDF.",
        "evidence_class": "B_measured_farm_scale_literature_summary", "quality_class": "B",
        "activation_state": "reference_only", "readiness": "D3",
        "measurement_scope": "Total-in vs total-out dry-matter accounting over silo ensiling/storage and feed-out. Not storage-only and not a temporal kinetic curve.",
        "negative_loss_handling": "The source explicitly attributes negative loss estimates to measurement/accounting error. Preserve the reported minimum for audit only; never use it as a physical negative loss or model coefficient.",
        "limitations": [LIMITATIONS, "No raw observations per silo or time series are deposited in the article; summary sample counts vary by metric."],
        "citation": f"Köhler et al. (2013). {TITLE}. Agricultural and Food Science 22:145–150. {DOI_URL}",
    }
    SIDECAR_PATH.write_text(json.dumps(sidecar, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    local_source = {
        "source_id": SOURCE_ID, "source_title": TITLE,
        "authors": "Köhler; Diepolder; Ostertag; Thurner; Spiekers", "year": "2013",
        "source_type": "peer-reviewed primary farm-scale measurement study; summary extract",
        "doi_or_stable_identifier": DOI, "stable_url": DOI_URL,
        "material": "26 grass silos among 48 farm-scale bunker silos; Bavaria, Germany",
        "quality_notes": "B-tier primary measurements; no raw silo rows. Total-in/out includes feed-out; not roadside grass or GreenHub storage. Copyright identified; no open reuse license confirmed; reference-only.",
        "accessed_date": RETRIEVED,
    }
    _upsert(GROUP / "source_register.csv", local_source, "source_id")
    _upsert(GROUP / "dataset_manifest.csv", {
        "filename": FILENAME,
        "description": "Reported grass-silo DM loss, density, feed-out and timing summaries from a 26-silo subset",
        "row_count": len(records), "schema_version": "1.0", "encoding": "UTF-8", "delimiter": ",",
        "integration_status": "reference_only_not_runtime_eligible",
        "primary_key": "record_id",
    }, "filename")
    rel = f"storage/{FILENAME}"
    _upsert(AUDIT / "global_source_register.csv", {
        "dataset_path": rel, "dataset_group": "storage", "source_id": SOURCE_ID,
        "source_title": TITLE, "authors": local_source["authors"], "year": "2013",
        "doi_or_stable_id": DOI, "url": DOI_URL, "source_type": local_source["source_type"],
        "notes": local_source["quality_notes"],
    }, "dataset_path")
    _upsert(AUDIT / "global_dataset_manifest.csv", {
        "dataset_path": rel, "category": "storage", "subgroup": "storage evidence",
        "filename": FILENAME, "row_count_observed": len(records), "header_count": len(FIELDS),
        "headers": "; ".join(FIELDS), "standardized_status_values": "B;reference_only",
        "detected_readiness": "D3", "notes": "Farm-scale total silo loss including feed-out; negative min preserved as measurement error, never physical mass gain.",
    }, "dataset_path")
    _upsert(AUDIT / "global_dataset_readiness.csv", {
        "dataset_path": rel, "category": "storage", "subgroup": "storage evidence",
        "readiness": "D3", "duplicate_ids": 0, "duplicate_rows": 0,
        "numeric_rows": len(records), "unsourced_numeric_rows": 0,
        "numeric_rows_missing_exact_location": 0, "unit_conflicts": 0,
        "basis_conflicts": 0, "cross_reference_issues": 0,
        "equation_missing_inputs": 0, "equation_symbol_mismatches": 0,
        "notes": "Source-located summary extract with units and measurement scope; non-roadside reference only; not a kinetic coefficient.",
    }, "dataset_path")
    _upsert(AUDIT / "source_dataset_checksums.csv", {
        "dataset_path": rel, "sha256": digest, "byte_size": CSV_PATH.stat().st_size,
    }, "dataset_path")
    print(json.dumps({"dataset": rel, "rows": len(records), "source_id": SOURCE_ID, "sha256": digest, "activation_state": "reference_only"}, indent=2))


if __name__ == "__main__":
    main()
