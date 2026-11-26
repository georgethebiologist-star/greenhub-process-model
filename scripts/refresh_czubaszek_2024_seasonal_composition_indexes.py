"""Refresh indexes for the 2024 roadside-grass seasonal composition extract.

The CSV is a reference-only transcription of published Table 1 and Table 8
measurements. This script updates local/global manifests and checksum/unit
indexes; it does not change runtime inputs or the source observations.
"""
from __future__ import annotations

import csv
import hashlib
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "Greenhub" / "data"
FEED = DATA / "Pre-treatment" / "Feedstock"
AUDIT = DATA / "global_audit_package"
DATASET = FEED / "roadside_grass_seasonal_composition_2024.csv"
RELATIVE_PATH = "Pre-treatment/Feedstock/roadside_grass_seasonal_composition_2024.csv"
SOURCE_ID = "SRC-CZUBASZEK-2024"
DOI_URL = "https://doi.org/10.3390/en17071751"
TITLE = "Possibilities of Utilising Biomass Collected from Road Verges to Produce Biogas and Biodiesel"
SOURCE_NOTE = (
    "Tables 1 and 8 report seasonal fresh/ensiled roadside-grass composition and summed FAMEs; "
    "samples collected in 2019 in Białystok, Poland; mean ± SD, n=3. CC BY 4.0. "
    "FAMEs are not crude fat; totals do not establish nutrient speciation. Reference-only, "
    "not GreenHub/Dutch feed or an active default. Retrieved 2026-11-09."
)


def read_csv(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    with path.open(encoding="utf-8-sig", newline="") as stream:
        reader = csv.DictReader(stream)
        return list(reader.fieldnames or []), list(reader)


def write_csv(path: Path, fields: list[str], rows: list[dict[str, str]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def upsert(path: Path, key: str, value: str, entry: dict[str, str]) -> None:
    fields, rows = read_csv(path)
    existing = next((row for row in rows if row.get(key) == value), None)
    if existing is None:
        rows.append({field: entry.get(field, "") for field in fields})
    else:
        existing.update({field: entry[field] for field in fields if field in entry})
    write_csv(path, fields, rows)


def main() -> None:
    fields, observations = read_csv(DATASET)
    if len(observations) != 72 or len({row["observation_id"] for row in observations}) != 72:
        raise ValueError("Expected 72 unique observations in the reviewed reference extract")
    if any(row["activation_state"] != "reference_only" for row in observations):
        raise ValueError("Reference-only dataset contains a row with an unexpected activation state")

    digest = hashlib.sha256(DATASET.read_bytes()).hexdigest()
    byte_size = str(DATASET.stat().st_size)
    numeric_rows = sum(bool(row.get("value", "").strip()) for row in observations)
    status_values = "; ".join(sorted({row["data_status"] for row in observations}))
    header_list = "; ".join(fields)

    upsert(AUDIT / "source_dataset_checksums.csv", "dataset_path", RELATIVE_PATH, {
        "dataset_path": RELATIVE_PATH, "sha256": digest, "byte_size": byte_size,
    })
    upsert(AUDIT / "global_dataset_manifest.csv", "dataset_path", RELATIVE_PATH, {
        "dataset_path": RELATIVE_PATH,
        "category": "Pre-treatment",
        "subgroup": "Feedstock",
        "filename": DATASET.name,
        "row_count_observed": str(len(observations)),
        "header_count": str(len(fields)),
        "headers": header_list,
        "standardized_status_values": status_values,
        "detected_readiness": "D3",
        "notes": "Reference-only 2019 Białystok comparator; Table 8 FAME records are not crude-lipid values.",
    })

    readiness_path = AUDIT / "global_dataset_readiness.csv"
    readiness_fields, readiness_rows = read_csv(readiness_path)
    readiness = next(row for row in readiness_rows if row.get("dataset_path") == RELATIVE_PATH)
    readiness.update({
        "numeric_rows": str(numeric_rows),
        "unsourced_numeric_rows": "0",
        "numeric_rows_missing_exact_location": "0",
        "notes": "72 unique reference observations; two sodium entries remain censored/missing; no runtime activation.",
    })
    write_csv(readiness_path, readiness_fields, readiness_rows)

    activation_path = AUDIT / "dataset_activation_matrix.csv"
    activation_fields, activation_rows = read_csv(activation_path)
    activation = next(row for row in activation_rows if row.get("dataset_path") == RELATIVE_PATH)
    activation["source_checksum_sha256"] = digest
    write_csv(activation_path, activation_fields, activation_rows)

    unit_path = AUDIT / "global_unit_registry.csv"
    unit_fields, unit_rows = read_csv(unit_path)
    unit_rows = [row for row in unit_rows if row.get("dataset_path") != RELATIVE_PATH]
    unit_rows.extend({
        "dataset_path": RELATIVE_PATH,
        "dataset_group": "Feedstock",
        "column_name": "unit",
        "unit_text": row["unit"],
        "status_standardized": row["data_status"],
    } for row in observations)
    write_csv(unit_path, unit_fields, unit_rows)

    source_index = AUDIT / "global_source_register.csv"
    source_index_fields, source_index_rows = read_csv(source_index)
    for row in source_index_rows:
        if row.get("source_id") == SOURCE_ID:
            row["url"] = DOI_URL
            row["notes"] = SOURCE_NOTE
    write_csv(source_index, source_index_fields, source_index_rows)

    print(f"indexed {len(observations)} reference rows; numeric={numeric_rows}; sha256={digest}")


if __name__ == "__main__":
    main()
