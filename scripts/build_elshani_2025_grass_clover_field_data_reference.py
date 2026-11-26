"""Import the CC0 DataverseNO field-data package for Elshani et al. (2025).

The source files are stored byte-for-byte. The extract is evidence-only and is
not mapped to GreenHub runtime parameters.
"""
from __future__ import annotations

import csv
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from urllib.request import Request, urlopen


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "Greenhub" / "data"
FEEDSTOCK = DATA / "Pre-treatment" / "Feedstock"
PACKAGE = FEEDSTOCK / "elshani_2025_grass_clover_field_data"
SOURCE_ID = "SRC-ELSHANI-2025-FIELD-DATA"
DATASET_DOI = "10.18710/F5Z8BR"
ARTICLE_DOI = "10.1016/j.scitotenv.2025.180373"
RETRIEVED = "2026-11-08"
API = "https://dataverse.no/api/datasets/:persistentId/?persistentId=doi:10.18710/F5Z8BR"
EXPECTED = {
    "00_README_EnvImpactBiorefine.txt": "f9cb6d002ad1e2ee2879b62f9b19f073",
    "EnvImpactBiorefine_Data.csv": "cf0fcea3eaa2bac973e4548795fa9bdc",
    "EnvImpactBiorefine_Exp.csv": "03e967afa0c584bd7f877adcadcd9d68",
}
DESCRIPTIONS = {
    "EnvImpactBiorefine_Data.csv": (
        "192 source-format treatment/location/year summaries for DM yield, crude-protein "
        "and red-clover observations from eight Norwegian grass-clover field experiments."
    ),
    "EnvImpactBiorefine_Exp.csv": (
        "Eight source-format experiment-location records with region, altitude, soil class "
        "and coordinates; linked to the treatment data by Exp_no."
    ),
}
LIMITATIONS = (
    "Cultivated timothy/meadow-fescue/red-clover field experiments in Norway, not roadside "
    "grass or GreenHub supply. The 192 rows are treatment summaries; measurements were pooled "
    "or averaged across three replicates, not replicate-level raw data. Source README defines "
    "yield columns as g/m2 and N_rate codes as 0/8/16/24 = 0/80/160/240 kg N/ha, but does not "
    "define units for CP_* or clover_* columns; preserve those source values without conversion. "
    "Dot is the missing-data code. No runtime/default use."
)


def get(url: str) -> bytes:
    request = Request(url, headers={"User-Agent": "GreenHub-data-provenance/1.0"})
    with urlopen(request, timeout=45) as response:
        return response.read()


def read_csv(path: Path, delimiter: str = ",") -> tuple[list[str], list[dict[str, str]]]:
    with path.open("r", encoding="utf-8-sig", newline="") as stream:
        reader = csv.DictReader(stream, delimiter=delimiter)
        return reader.fieldnames or [], list(reader)


def append_once(path: Path, row: dict[str, object], key: str) -> None:
    with path.open("r", encoding="utf-8-sig", newline="") as stream:
        reader = csv.DictReader(stream)
        fields = reader.fieldnames or []
        existing = list(reader)
    matches = [item for item in existing if item.get(key) == str(row.get(key, ""))]
    if matches:
        if len(matches) != 1 or any(matches[0].get(field, "") != str(row.get(field, "")) for field in fields):
            raise ValueError(f"Conflicting registration in {path}: {row.get(key)}")
        return
    with path.open("a", encoding="utf-8", newline="") as stream:
        csv.DictWriter(stream, fieldnames=fields, lineterminator="\n", extrasaction="ignore").writerow(
            {field: row.get(field, "") for field in fields}
        )


def main() -> None:
    metadata = json.loads(get(API).decode("utf-8"))
    files = {
        item["dataFile"]["filename"]: item["dataFile"]
        for item in metadata["data"]["latestVersion"]["files"]
    }
    if set(files) != set(EXPECTED):
        raise ValueError(f"Unexpected DataverseNO file set: {sorted(files)}")
    if str(metadata["data"]["latestVersion"].get("versionNumber")) != "1":
        raise ValueError("Unexpected dataset version; review before importing")

    PACKAGE.mkdir(parents=True, exist_ok=True)
    checksums: dict[str, str] = {}
    for filename, expected_md5 in EXPECTED.items():
        file_info = files[filename]
        if file_info.get("md5") != expected_md5:
            raise ValueError(f"DataverseNO metadata checksum changed for {filename}")
        target = PACKAGE / filename
        if target.exists():
            payload = target.read_bytes()
            if hashlib.md5(payload).hexdigest() != expected_md5:
                raise ValueError(f"Preserving existing file with unexpected contents: {target}")
        else:
            payload = get(f"https://dataverse.no/api/access/datafile/{file_info['id']}")
            if hashlib.md5(payload).hexdigest() != expected_md5:
                raise ValueError(f"Downloaded checksum mismatch for {filename}")
            target.write_bytes(payload)
        checksums[filename] = hashlib.md5(payload).hexdigest()

    _, observations = read_csv(PACKAGE / "EnvImpactBiorefine_Data.csv", delimiter=";")
    _, locations = read_csv(PACKAGE / "EnvImpactBiorefine_Exp.csv", delimiter=";")
    if len(observations) != 192 or len(locations) != 8:
        raise ValueError(f"Unexpected record counts: observations={len(observations)}, locations={len(locations)}")
    if {row["Exp_no"] for row in observations} != {row["Exp_no"] for row in locations}:
        raise ValueError("The experiment-location crosswalk does not cover the observed experiment IDs")
    if any(row["No_cuts"] != "3" for row in observations):
        raise ValueError("Unexpected cutting-regime values; review source version")
    if {row["N_rate"] for row in observations} != {"0", "8", "16", "24"}:
        raise ValueError("Unexpected source-coded N-rate levels")
    if {row["Clover_mix"] for row in observations} != {"10", "20"}:
        raise ValueError("Unexpected source-coded clover seeding-rate levels")

    sidecar = {
        "source_id": SOURCE_ID,
        "dataset_title": "Background data for: Climate impact and land use of processing grass-clover biomass cultivated under different nitrogen fertilization rates in green biorefinery",
        "dataset_doi": DATASET_DOI,
        "dataset_version": "1.0",
        "related_publication_doi": ARTICLE_DOI,
        "authors": ["Narta Elshani", "Håvard Steinshamn", "Steffen Adler", "Johan Nilsson", "Pernilla Tidåker"],
        "publisher": "DataverseNO",
        "publication_date": "2026-10-30",
        "retrieval_date": RETRIEVED,
        "license": "CC0 1.0 Universal Public Domain Dedication",
        "license_url": "https://creativecommons.org/publicdomain/zero/1.0/",
        "source_api": API,
        "source_file_md5": checksums,
        "file_bytes": {name: int(files[name]["filesize"]) for name in EXPECTED},
        "observations": {
            "main_file": "EnvImpactBiorefine_Data.csv",
            "observation_rows": len(observations),
            "location_file": "EnvImpactBiorefine_Exp.csv",
            "location_rows": len(locations),
            "join_key": "Exp_no",
            "delimiter": ";",
            "yield_columns_unit_as_defined_by_source_readme": "g/m2 dry matter",
            "n_rate_codes_kg_n_ha": {"0": 0, "8": 80, "16": 160, "24": 240},
            "clover_mix_source_codes_percent_of_seed_mix": [10, 20],
            "cp_and_clover_observation_column_units": "Not defined in the source README; values retained without unit assignment or conversion.",
            "missing_value_code": ".",
            "replicate_treatment": "Source README states chemical-analysis samples were pooled and DM yields averaged across three replicates by treatment, cut, location and year.",
        },
        "experimental_context": {
            "crop": "Cultivated grass-clover ley: timothy, meadow fescue, red clover",
            "geography": "Eight Norwegian sites in Southern and Central Norway",
            "field_experiment_period": "2009-2013",
            "production_years": "1-3",
            "cuts": "Three cuts per season in the released dataset",
            "status": "Measured field-trial summaries in a CC0 secondary data publication; not raw replicate data.",
        },
        "evidence_class": "direct literature; published field-experiment dataset",
        "quality_class": "B",
        "activation_state": "reference_only",
        "readiness": "D3",
        "runtime_policy": "Do not map to roadside-grass defaults, process parameters, route, UI overrides or Pareto calculations.",
        "applicability_limit": LIMITATIONS,
        "fair": {
            "findable": "Dataset DOI, related article DOI, local source ID and checksummed asset paths are recorded.",
            "accessible": "Public DataverseNO API and CC0 license.",
            "interoperable": "UTF-8 semicolon CSVs; source Exp_no joins experiment records to a separate location crosswalk.",
            "reusable": "Raw source files are preserved byte-for-byte; source README, file checksums, mapping limits and missingness codes are recorded.",
        },
    }
    sidecar_path = PACKAGE / "dataset.source.json"
    encoded_sidecar = json.dumps(sidecar, ensure_ascii=False, indent=2) + "\n"
    if sidecar_path.exists() and sidecar_path.read_text(encoding="utf-8") != encoded_sidecar:
        raise ValueError(f"Preserving existing sidecar with different contents: {sidecar_path}")
    sidecar_path.write_text(encoded_sidecar, encoding="utf-8")

    source_row = {
        "source_id": SOURCE_ID,
        "source_title": sidecar["dataset_title"],
        "authors": "; ".join(sidecar["authors"]),
        "year": "2026 (dataset release); field experiments 2009-2013; related article 2025",
        "source_type": "CC0 field-experiment dataset; DataverseNO public repository",
        "doi_or_stable_identifier": f"doi:{DATASET_DOI}",
        "stable_url": f"https://doi.org/{DATASET_DOI}",
        "material": sidecar["experimental_context"]["crop"],
        "quality_notes": f"192 treatment/location/year summaries across eight Norwegian sites, 2009-2013; three-cut swards, N-rate and clover-seeding treatments. Yield is g/m2 DM per source README; CP/clover column units are undefined there. Means/pooling across three replicates; not roadside feed. Related article DOI {ARTICLE_DOI}; reference-only.",
        "accessed_date": RETRIEVED,
    }
    append_once(FEEDSTOCK / "source_register.csv", source_row, "source_id")

    relative_files = {
        "EnvImpactBiorefine_Data.csv": f"Pre-treatment/Feedstock/{PACKAGE.name}/EnvImpactBiorefine_Data.csv",
        "EnvImpactBiorefine_Exp.csv": f"Pre-treatment/Feedstock/{PACKAGE.name}/EnvImpactBiorefine_Exp.csv",
    }
    local_manifest = FEEDSTOCK / "dataset_manifest.csv"
    for filename, relative_path in relative_files.items():
        append_once(local_manifest, {
            "file_name": f"{PACKAGE.name}/{filename}",
            "description": DESCRIPTIONS[filename],
            "row_count": 192 if filename == "EnvImpactBiorefine_Data.csv" else 8,
            "schema_version": "1.0",
            "encoding": "UTF-8",
            "delimiter": ";",
            "integration_readiness": "reference_only_not_runtime_eligible",
            "limitations": LIMITATIONS + f" Source asset path: {relative_path}.",
        }, "file_name")

    audit = DATA / "global_audit_package"
    for filename, relative_path in relative_files.items():
        is_main = filename == "EnvImpactBiorefine_Data.csv"
        append_once(audit / "global_source_register.csv", {
            "dataset_path": relative_path,
            "dataset_group": "Pre-treatment/Feedstock",
            "source_id": SOURCE_ID,
            "source_title": sidecar["dataset_title"],
            "authors": "; ".join(sidecar["authors"]),
            "year": "2026 (dataset release); field experiments 2009-2013",
            "doi_or_stable_id": f"doi:{DATASET_DOI}; article doi:{ARTICLE_DOI}",
            "url": f"https://doi.org/{DATASET_DOI}",
            "source_type": "CC0 field-experiment dataset; DataverseNO public repository",
            "notes": DESCRIPTIONS[filename] + " " + LIMITATIONS,
        }, "dataset_path")
        _, fields = read_csv(PACKAGE / filename, delimiter=";")
        append_once(audit / "global_dataset_manifest.csv", {
            "dataset_path": relative_path,
            "category": "Pre-treatment",
            "subgroup": "Feedstock",
            "filename": filename,
            "row_count_observed": 192 if is_main else 8,
            "header_count": len(fields[0]) if fields else 0,
            "headers": "; ".join(fields[0].keys()) if fields else "",
            "standardized_status_values": "B;reference_only",
            "detected_readiness": "D3",
            "notes": DESCRIPTIONS[filename] + " CP/clover column units in main file are undefined in its README; no runtime use.",
        }, "dataset_path")
        append_once(audit / "global_dataset_readiness.csv", {
            "dataset_path": relative_path,
            "category": "Pre-treatment",
            "subgroup": "Feedstock",
            "readiness": "D3",
            "duplicate_ids": 0,
            "duplicate_rows": 0,
            "numeric_rows": 192 if is_main else 8,
            "unsourced_numeric_rows": 0,
            "numeric_rows_missing_exact_location": 0,
            "unit_conflicts": 0,
            "basis_conflicts": 0,
            "cross_reference_issues": 0,
            "equation_missing_inputs": 0,
            "equation_symbol_mismatches": 0,
            "notes": "Source-linked CC0 field data; Exp_no location crosswalk checked; main dataset units are incomplete for CP/clover columns; reference-only.",
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

    print(json.dumps({
        "dataset_doi": DATASET_DOI,
        "article_doi": ARTICLE_DOI,
        "observations": len(observations),
        "locations": len(locations),
        "source_checksums_md5": checksums,
        "activation_state": "reference_only",
        "readiness": "D3",
    }, indent=2))


if __name__ == "__main__":
    main()
