"""Register the original Zenodo raw files underlying the methane-loss summary.

The source files are retained byte-for-byte. This builder adds provenance and
catalog records only; it does not calculate or activate GreenHub parameters.
"""
from __future__ import annotations

import csv
import hashlib
import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "Greenhub" / "data"
GROUP = DATA / "lca" / "source_data"
AUDIT = DATA / "global_audit_package"
RETRIEVED = "2026-11-08"
SOURCE_ID = "SRC-WECHSELBERGER-2023"
DATA_DOI = "10.5281/zenodo.7474206"
V1_DOI = "10.5281/zenodo.7422108"
ARTICLE_DOI = "10.1016/j.wasman.2022.12.012"
FILES = [
    {
        "name": "wechselberger_et_al_2023_measurement_data_raw.csv",
        "source_name": "Wechselberger_et_al_2023_data.csv",
        "md5": "d35a0df634b1000bb936eee46aa7a3cb",
        "kind": "raw_measurement_data",
        "description": "Verbatim 294-row, 32-field measurement and secondary-data file underlying Table 2 emission factors.",
        "rows": 294,
        "encoding": "Windows-1252 (verified against source-file checksum; bytes preserved)",
        "delimiter": ",",
        "limitations": "Contains primary and secondary observations across mixed feedstocks and technologies. Missing values are source-coded NA. Not grass-specific and not a GreenHub default.",
    },
    {
        "name": "wechselberger_et_al_2023_glossary_raw.csv",
        "source_name": "Glossary.csv",
        "md5": "37d36bbf21a5ec651cf1459dc220804c",
        "kind": "variable_glossary",
        "description": "Verbatim glossary defining the raw dataset's 32 variables.",
        "rows": 32,
        "encoding": "Windows-1252 (verified against source-file checksum; bytes preserved)",
        "delimiter": ";",
        "limitations": "Source glossary; variable definitions do not resolve cross-technology transferability or GreenHub-specific measurement gaps.",
    },
    {
        "name": "wechselberger_et_al_2023_R_code_raw.Rmd",
        "source_name": "Wechselberger_et_al_2023_R_code.Rmd",
        "md5": "47c53939bc683071d8cb35a0db41b430",
        "kind": "analysis_code",
        "description": "Verbatim R Markdown code supplied by the dataset authors to calculate the published emission-factor summaries.",
        "rows": 0,
        "encoding": "Windows-1252 (verified against source-file checksum; bytes preserved)",
        "delimiter": "",
        "limitations": "Preserved for reproducibility; not executed here and not part of GreenHub runtime calculations.",
    },
]


def read_csv(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        return list(reader.fieldnames or []), list(reader)


def upsert(path: Path, row: dict[str, object], key: str) -> None:
    fields, rows = read_csv(path)
    if not fields:
        raise ValueError(f"Expected CSV headers in {path}")
    normalized = {field: str(row.get(field, "")) for field in fields}
    rows = [item for item in rows if item.get(key) != normalized[key]]
    rows.append(normalized)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    GROUP.mkdir(parents=True, exist_ok=True)
    source_register = DATA / "lca" / "source_register.csv"
    _, sources = read_csv(source_register)
    source = next((row for row in sources if row.get("source_id") == SOURCE_ID), None)
    if not source or source.get("doi_or_stable_identifier") != ARTICLE_DOI:
        raise ValueError("Expected the existing article-level source-register entry before adding raw data.")

    data_file = GROUP / FILES[0]["name"]
    with data_file.open("r", encoding="cp1252", newline="") as handle:
        raw_rows = list(csv.DictReader(handle))
    if len(raw_rows) != 294 or len(raw_rows[0]) != 32:
        raise ValueError(f"Unexpected raw dataset structure: {len(raw_rows)} records, {len(raw_rows[0])} fields")
    stage_counts = dict(sorted(Counter(row["process_stage"] for row in raw_rows).items()))
    countries = sorted({row["country"] for row in raw_rows if row.get("country")})

    created = []
    for item in FILES:
        path = GROUP / item["name"]
        payload = path.read_bytes()
        source_md5 = hashlib.md5(payload).hexdigest()
        if source_md5 != item["md5"]:
            raise ValueError(f"Downloaded source file does not match Zenodo MD5: {item['name']} ({source_md5})")
        sha256 = hashlib.sha256(payload).hexdigest()
        rel = f"lca/source_data/{item['name']}"
        sidecar = {
            "dataset_id": f"urn:greenhub:dataset:wechselberger-2023:{item['kind']}:v1",
            "dataset_version": "1.0.0",
            "title": item["description"],
            "source_file": item["name"],
            "source_file_sha256": sha256,
            "source_file_md5": source_md5,
            "source_record_doi": DATA_DOI,
            "source_record_url": f"https://doi.org/{DATA_DOI}",
            "source_v1_doi": V1_DOI,
            "source_v1_url": f"https://doi.org/{V1_DOI}",
            "article_doi": ARTICLE_DOI,
            "article_url": f"https://doi.org/{ARTICLE_DOI}",
            "citation": "Wechselberger, V. et al. (2023). Methane losses from different biogas plant technologies. Waste Management, 157, 110–120.",
            "source_filename": item["source_name"],
            "source_publisher": "Zenodo",
            "source_version": "v2; Zenodo states the v2 data are the same as v1",
            "retrieval_date": RETRIEVED,
            "license": "CC BY 4.0, as displayed for the v1 record; v2 states the data are unchanged from v1 but does not display a separate rights statement",
            "license_url": "https://creativecommons.org/licenses/by/4.0/",
            "evidence_class": "B_primary_measurement_and_secondary_data",
            "quality_class": "B",
            "record_count_or_variables": item["rows"],
            "encoding": item["encoding"],
            "delimiter": item["delimiter"],
            "geography": "Primary harmonized campaign in Austria, Germany, Sweden and Switzerland; the combined source file also includes secondary records from other countries listed in the raw rows.",
            "primary_measurement_geography": "Austria, Germany, Sweden and Switzerland",
            "source_description": "Underlying data for harmonized methane-emission measurements at 33 biogas plants; includes primary and secondary data and an author-supplied analysis script.",
            "process_stage_counts": stage_counts if item["kind"] == "raw_measurement_data" else {},
            "countries_in_data": countries if item["kind"] == "raw_measurement_data" else [],
            "activation_state": "reference_only",
            "readiness": "D3",
            "runtime_parameter_mapping": None,
            "transferability": "Technology and feedstock comparator only; mixed substrates and plant configurations, not GreenHub or roadside-grass specific.",
            "limitations": [item["limitations"], "The source summary factors are already transcribed separately in GreenHub; raw records are retained to support evidence review and potential future stratification, not to double-count observations.", "No probability distribution, GreenHub leakage default, or technology-specific GreenHub factor is inferred."],
        }
        Path(str(path) + ".source.json").write_text(json.dumps(sidecar, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        upsert(GROUP / "dataset_manifest.csv", {
            "filename": item["name"], "description": item["description"], "row_count": item["rows"],
            "schema_version": "source-verbatim", "encoding": item["encoding"], "delimiter": item["delimiter"],
            "integration_readiness": "traceable_reference_only_not_runtime_eligible",
            "limitations": item["limitations"],
        }, "filename")
        upsert(AUDIT / "global_source_register.csv", {
            "dataset_path": rel, "dataset_group": "lca/source_data", "source_id": SOURCE_ID,
            "source_title": "Methane losses from different biogas plant technologies — underlying data",
            "authors": source.get("authors", ""), "year": "2023", "doi_or_stable_id": DATA_DOI,
            "url": f"https://doi.org/{DATA_DOI}", "source_type": "peer-reviewed study linked open measurement dataset",
            "notes": f"Zenodo v2 raw {item['kind']}; CC BY 4.0 is displayed for v1 and v2 says data unchanged; reference-only; no GreenHub runtime mapping.",
        }, "dataset_path")
        upsert(AUDIT / "global_dataset_manifest.csv", {
            "dataset_path": rel, "category": "LCA", "subgroup": "Methane emissions; underlying measurements",
            "filename": item["name"], "row_count_observed": item["rows"],
            "header_count": 32 if item["kind"] == "raw_measurement_data" else (3 if item["kind"] == "variable_glossary" else 0),
            "headers": "; ".join(raw_rows[0].keys()) if item["kind"] == "raw_measurement_data" else item["kind"],
            "standardized_status_values": "B;reference_only", "detected_readiness": "D3",
            "notes": item["limitations"],
        }, "dataset_path")
        numeric_rows = len(raw_rows) if item["kind"] == "raw_measurement_data" else 0
        upsert(AUDIT / "global_dataset_readiness.csv", {
            "dataset_path": rel, "category": "LCA", "subgroup": "Methane emissions; underlying measurements",
            "readiness": "D3", "duplicate_ids": 0, "duplicate_rows": 0, "numeric_rows": numeric_rows,
            "unsourced_numeric_rows": 0, "numeric_rows_missing_exact_location": 0, "unit_conflicts": 0,
            "basis_conflicts": 0, "cross_reference_issues": 0, "equation_missing_inputs": 0,
            "equation_symbol_mismatches": 0, "notes": "Raw source data are cited and checksum-verified; mixed primary/secondary sources and non-GreenHub applicability remain explicit.",
        }, "dataset_path")
        upsert(AUDIT / "source_dataset_checksums.csv", {
            "dataset_path": rel, "sha256": sha256, "byte_size": len(payload),
        }, "dataset_path")
        created.append({"dataset": rel, "bytes": len(payload), "md5": source_md5, "sha256": sha256})

    updated_source = dict(source)
    updated_source["source_type"] = "peer-reviewed measurement article with open Zenodo raw data, glossary and analysis code"
    updated_source["quality_notes"] = (
        "Table 2 aggregate extract and verbatim Zenodo v2 source files (294 records, 32 fields, glossary and R Markdown code) are retained. "
        "The Zenodo v1 record displays CC BY 4.0; v2 states its data are the same as v1 but omits a separate rights statement. "
        "Mixed substrates and technology contexts; reference-only, not GreenHub defaults or grass-specific factors."
    )
    updated_source["accessed_date"] = RETRIEVED
    upsert(source_register, updated_source, "source_id")
    print(json.dumps({"registered_files": created, "records": len(raw_rows), "fields": len(raw_rows[0]), "process_stages": stage_counts, "activation_state": "reference_only"}, indent=2))


if __name__ == "__main__":
    main()
