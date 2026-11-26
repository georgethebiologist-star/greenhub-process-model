"""Register byte-verifiable source assets behind the Bakker roadside-biomass extract."""
from __future__ import annotations

import csv
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "Greenhub/data"
FOLDER = DATA / "Pre-treatment/Feedstock"
SOURCE_FOLDER = FOLDER / "road_verge_standing_biomass_bakker_2026_source"
AUDIT = DATA / "global_audit_package"
SOURCE_ID = "SRC_BAKKER_ROADVERGE_BIOMASS_2026"
DATASET_DOI = "10.5281/zenodo.15349657"
CONCEPT_DOI = "10.5281/zenodo.15349656"
ARTICLE_DOI = "10.1111/avsc.70085"
ZENODO_RECORD = "https://zenodo.org/records/15349657"
ARTICLE_URL = f"https://doi.org/{ARTICLE_DOI}"
RETRIEVED = "2026-11-08"
ASSETS = {
    "Biomass.csv": {
        "md5": "a6769824448e47dad1ff3b2ff882c53c",
        "description": "Original Zenodo Biomass.csv preserved byte-for-byte; 120 measured standing-biomass rows, including the source blank.",
        "row_count": 120,
        "encoding": "UTF-8",
        "delimiter": ";",
        "role": "verbatim_source_data",
    },
    "Analysis.R": {
        "md5": "3a6e7bacc886ef5c1a5e9257a6aee684",
        "description": "Original Zenodo R analysis script; documents source g DM/m2 to t DM/ha conversion and statistical use.",
        "row_count": "",
        "encoding": "UTF-8",
        "delimiter": "not_applicable",
        "role": "source_analysis_script",
    },
}


def _read_csv(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    with path.open(encoding="utf-8-sig", newline="") as stream:
        reader = csv.DictReader(stream)
        return list(reader.fieldnames or []), list(reader)


def _write_csv(path: Path, fields: list[str], rows: list[dict[str, object]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def _upsert(path: Path, record: dict[str, object], key: str) -> None:
    fields, rows = _read_csv(path)
    if not fields or key not in fields:
        raise ValueError(f"Expected register key {key!r} in {path}")
    rows = [row for row in rows if row.get(key) != str(record[key])]
    rows.append({field: record.get(field, "") for field in fields})
    _write_csv(path, fields, rows)


def _digests(path: Path) -> tuple[str, str]:
    raw = path.read_bytes()
    return hashlib.md5(raw).hexdigest(), hashlib.sha256(raw).hexdigest()


def _sidecar(path: Path, details: dict[str, object], sha256: str) -> dict[str, object]:
    return {
        "source_id": SOURCE_ID,
        "dataset_title": "Grassland management in a changing climate: Dutch road-verge standing biomass measurements",
        "source_asset": path.name,
        "source_asset_role": details["role"],
        "source_asset_path": path.relative_to(DATA).as_posix(),
        "source_record_filename": path.name,
        "dataset_doi": DATASET_DOI,
        "concept_doi": CONCEPT_DOI,
        "article_doi": ARTICLE_DOI,
        "source_url": ZENODO_RECORD,
        "article_url": ARTICLE_URL,
        "creators": ["Wiene Bakker", "Jeroen Scheper", "Wim Ozinga", "Philippine Vergeer"],
        "dataset_record_date": "2025-05-06",
        "article_publication_year": 2026,
        "retrieval_date": RETRIEVED,
        "license": "CC BY 4.0, as stated by Zenodo version record 15349657; this does not assert reuse rights for the article.",
        "license_url": "https://creativecommons.org/licenses/by/4.0/",
        "source_md5": details["md5"],
        "source_sha256": sha256,
        "source_byte_size": path.stat().st_size,
        "row_count": details["row_count"],
        "encoding": details["encoding"],
        "delimiter": details["delimiter"],
        "measurement_context": "Ten Dutch roadside grasslands; standing biomass sampled just before mowing in June and August 2023; first experimental block only.",
        "interpretation": "Measured literature observations, not harvested/delivered annual yield or GreenHub contracted feed. Reference-only; no runtime parameter mapping.",
        "paired_derived_asset": "Greenhub/data/Pre-treatment/Feedstock/road_verge_standing_biomass_bakker_2026_zenodo_reference.csv",
        "limitations": [
            "The source is a plot-level standing-biomass snapshot, not machine-collected mass or deliverable supply.",
            "The single source-missing biomass value remains missing; no imputation is performed.",
            "The exact source bytes are retained separately from the previously standardized Biomass.csv copy, whose record values are equivalent but line endings were normalized.",
            "Analysis.R documents the dimensional conversion: source g DM/m2 multiplied by 10/1000 to obtain t DM/ha.",
        ],
        "activation_state": "reference_only",
        "calculation_connected": False,
        "parameter_registry_mapping": None,
    }


def _register_asset(path: Path, details: dict[str, object]) -> None:
    md5, sha256 = _digests(path)
    if md5.lower() != details["md5"]:
        raise ValueError(f"Zenodo checksum mismatch for {path.name}: {md5}")
    metadata = _sidecar(path, details, sha256)
    path.with_suffix(path.suffix + ".source.json").write_text(
        json.dumps(metadata, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    relative = path.relative_to(DATA).as_posix()
    manifest_path = f"road_verge_standing_biomass_bakker_2026_source/{path.name}"
    _upsert(FOLDER / "dataset_manifest.csv", {
        "file_name": manifest_path,
        "description": details["description"],
        "row_count": details["row_count"],
        "schema_version": "1.0",
        "encoding": details["encoding"],
        "delimiter": details["delimiter"],
        "integration_readiness": "source-traceable; exact Zenodo asset; reference_only; no runtime mapping",
        "limitations": "See adjacent source.json for exact DOI, license, checksum, context, units, and transfer limitations.",
    }, "file_name")
    _upsert(AUDIT / "global_source_register.csv", {
        "dataset_path": relative,
        "dataset_group": "Pre-treatment/Feedstock; original Bakker et al. roadside-biomass dataset assets",
        "source_id": SOURCE_ID,
        "source_title": "Grassland management in a changing climate: Insights from a Dutch road verge study — data and scripts",
        "authors": "Wiene Bakker; Jeroen Scheper; Wim Ozinga; Philippine Vergeer",
        "year": "2025",
        "doi_or_stable_id": DATASET_DOI,
        "url": ZENODO_RECORD,
        "source_type": f"open research dataset source asset ({details['role']}); CC BY 4.0",
        "notes": f"Exact Zenodo version asset; MD5 {md5}. Linked article DOI {ARTICLE_DOI}. Reference-only; standing biomass is not collected supply.",
    }, "dataset_path")
    _upsert(AUDIT / "global_dataset_manifest.csv", {
        "dataset_path": relative,
        "category": "Pre-treatment",
        "subgroup": "Feedstock; Bakker Dutch roadside biomass source package",
        "filename": path.name,
        "row_count_observed": details["row_count"],
        "header_count": 6 if path.name == "Biomass.csv" else 0,
        "headers": "Roadverge; Month; Mow; Soiltype; Biomass; Productivity" if path.name == "Biomass.csv" else "source code",
        "standardized_status_values": "source_verbatim;reference_only",
        "detected_readiness": "D3",
        "notes": details["description"],
    }, "dataset_path")
    _upsert(AUDIT / "global_dataset_readiness.csv", {
        "dataset_path": relative,
        "category": "Pre-treatment",
        "subgroup": "Feedstock; Bakker Dutch roadside biomass source package",
        "readiness": "D3",
        "duplicate_ids": "0",
        "duplicate_rows": "0",
        "numeric_rows": details["row_count"] if path.name == "Biomass.csv" else "0",
        "unsourced_numeric_rows": "0",
        "numeric_rows_missing_exact_location": "0",
        "unit_conflicts": "0",
        "basis_conflicts": "0",
        "cross_reference_issues": "0",
        "equation_missing_inputs": "0",
        "equation_symbol_mismatches": "0",
        "notes": "DOI-linked source package asset; no runtime activation. Exact source row values may include one missing biomass measurement." if path.name == "Biomass.csv" else "Companion authors' analysis code; not executed by GreenHub.",
    }, "dataset_path")
    _upsert(AUDIT / "source_dataset_checksums.csv", {
        "dataset_path": relative,
        "sha256": sha256,
        "byte_size": path.stat().st_size,
    }, "dataset_path")


def _update_related_source_notes() -> None:
    register = FOLDER / "source_register.csv"
    fields, rows = _read_csv(register)
    updates = {
        SOURCE_ID: "Exact Zenodo Biomass.csv and Analysis.R are now preserved in the linked source subfolder with verified Zenodo MD5 and local SHA-256. The root-level semicolon CSV remains for compatibility; parsed values match, with line endings normalized.",
        "SRC-BAKKER-AVSC-DATA-2025": "Biomass.csv contains 120 plot observations; exact Zenodo Biomass.csv and Analysis.R are now vendored in the linked source subfolder with verified checksums. Values are standing biomass, not annual harvested supply or delivered feed.",
    }
    found = {source_id: 0 for source_id in updates}
    for row in rows:
        source_id = row.get("source_id", "")
        if source_id not in updates:
            continue
        found[source_id] += 1
        note = row.get("quality_notes", "")
        if source_id == "SRC-BAKKER-AVSC-DATA-2025":
            # Normalize prior versions of this note before appending the current
            # traceability statement. This keeps repeated builder runs idempotent.
            note = note.replace(updates[source_id], "")
            note = note.replace(
                "Analysis.R is available from the version record but is not vendored. ",
                "",
            )
            note = note.replace("Biomass.csv contains 120 plot observations; ", "")
            note = note.replace(
                "Values are standing biomass, not annual harvested supply or delivered feed.",
                "",
            )
        else:
            note = note.replace(updates[source_id], "")
        row["quality_notes"] = f"{note.rstrip()} {updates[source_id]}".strip()
    if any(count > 1 for count in found.values()):
        raise ValueError(f"Expected unique Bakker source IDs, found {found}")
    _write_csv(register, fields, rows)


def _refresh_summary() -> None:
    summary_path = AUDIT / "global_validation_summary.json"
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    _, manifests = _read_csv(AUDIT / "global_dataset_manifest.csv")
    _, readiness = _read_csv(AUDIT / "global_dataset_readiness.csv")
    counts: dict[str, int] = {}
    for row in readiness:
        value = row.get("readiness", "")
        counts[value] = counts.get(value, 0) + 1
    summary["dataset_count"] = len(manifests)
    summary["readiness_counts"] = counts
    summary["generated_at"] = datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")
    summary_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main() -> None:
    for filename, details in ASSETS.items():
        path = SOURCE_FOLDER / filename
        if not path.exists():
            raise FileNotFoundError(path)
        _register_asset(path, details)
    _update_related_source_notes()
    print(json.dumps({"source_id": SOURCE_ID, "registered_assets": list(ASSETS)}, indent=2))
    _refresh_summary()


if __name__ == "__main__":
    main()
