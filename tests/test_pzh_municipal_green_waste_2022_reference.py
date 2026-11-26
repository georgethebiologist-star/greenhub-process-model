from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
FEEDSTOCK = ROOT / "Greenhub" / "data" / "Pre-treatment" / "Feedstock"
FILENAME = "pzh_municipal_green_waste_cbs_2022_reference.csv"
DATASET = FEEDSTOCK / FILENAME
SOURCE_ID = "SRC-ZH-GREEN-WASTE-WFS-2026"


def rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as stream:
        reader = csv.DictReader(stream)
        result = list(reader)
        assert reader.fieldnames
        assert all(None not in row for row in result)
        return result


def test_pzh_wfs_municipal_estimates_preserve_values_and_scope():
    records = rows(DATASET)
    assert len(records) == 50
    assert len({record["record_id"] for record in records}) == 50
    assert len({record["municipality"] for record in records}) == 50
    assert {record["source_id"] for record in records} == {SOURCE_ID}
    assert {record["reference_year"] for record in records} == {"2022"}
    assert {record["reported_unit"] for record in records} == {"t/year (wet/dry basis unspecified)"}
    assert {record["quality_class"] for record in records} == {"B"}
    assert {record["activation_state"] for record in records} == {"reference_only"}

    by_name = {record["municipality"]: record for record in records}
    assert by_name["Alblasserdam"]["reported_value"] == "407"
    assert by_name["Rijswijk (ZH.)"]["reported_value"] == "13278"
    assert by_name["Rotterdam"]["reported_value"] == "16213"
    assert by_name["Schiedam"]["reported_value"] == "11257"
    assert by_name["Voorne aan Zee"]["reported_value"] == "1297"
    assert sum(int(record["reported_value"]) for record in records) == 90321
    assert all("not a grass-only quantity" in record["applicability_limit"] for record in records)


def test_pzh_wfs_dataset_records_catalog_total_conflict_and_reference_only_gate():
    sidecar = json.loads(Path(str(DATASET) + ".source.json").read_text(encoding="utf-8"))
    assert sidecar["source_id"] == SOURCE_ID
    assert sidecar["related_source_ids"] == [
        "SRC-ZH-GREEN-WASTE-DATA-2026",
        "SRC-ZH-BIOMASS-INVENTORY-2023",
    ]
    assert sidecar["record_count"] == 50
    assert sidecar["sha256"] == hashlib.sha256(DATASET.read_bytes()).hexdigest()
    assert "90,321 t/year" in sidecar["transcription_and_validation"]
    assert "76,084 t/year" in sidecar["transcription_and_validation"]
    assert "not reconciled" in sidecar["transcription_and_validation"]
    assert "not a roadside-grass or GreenHub supply input" in sidecar["runtime_policy"]

    source = next(item for item in rows(FEEDSTOCK / "source_register.csv") if item["source_id"] == SOURCE_ID)
    manifest = next(item for item in rows(FEEDSTOCK / "dataset_manifest.csv") if item["file_name"] == FILENAME)
    relative_path = f"Pre-treatment/Feedstock/{FILENAME}"
    audit = ROOT / "Greenhub" / "data" / "global_audit_package"
    global_source = next(item for item in rows(audit / "global_source_register.csv") if item["dataset_path"] == relative_path)
    global_manifest = next(item for item in rows(audit / "global_dataset_manifest.csv") if item["dataset_path"] == relative_path)
    readiness = next(item for item in rows(audit / "global_dataset_readiness.csv") if item["dataset_path"] == relative_path)

    assert source["doi_or_stable_identifier"] == "data.overheid.nl:0f08e50f-6483-4d62-8a29-16a049e5c5ec"
    assert manifest["integration_readiness"] == "traceable_reference_only_not_runtime_eligible"
    assert global_source["source_id"] == SOURCE_ID
    assert global_manifest["detected_readiness"] == readiness["readiness"] == "D3"
    assert readiness["numeric_rows"] == "50"
    assert readiness["unsourced_numeric_rows"] == "0"
    assert readiness["numeric_rows_missing_exact_location"] == "0"
