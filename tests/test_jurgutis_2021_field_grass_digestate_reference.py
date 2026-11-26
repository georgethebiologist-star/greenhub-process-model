from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "Greenhub/data/Bigas production + upgrade/Feed BMP"
FILENAME = "field_grass_digestate_fertilisation_yield_nutrients_bmp_jurgutis_2021_reference.csv"
CSV_PATH = DATA / FILENAME
RELATIVE_PATH = f"Bigas production + upgrade/Feed BMP/{FILENAME}"
SOURCE_ID = "SRC-JURGUTIS-FIELD-GRASS-DIGESTATE-2021"


def _rows(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as stream:
        return list(csv.DictReader(stream))


def test_field_yield_nutrients_bmp_and_digestate_observations_are_traceable():
    rows = _rows(CSV_PATH)
    assert len(rows) == 205
    assert len({row["observation_id"] for row in rows}) == len(rows)
    assert {row["source_id"] for row in rows} == {SOURCE_ID}
    assert {row["evidence_class"] for row in rows} == {"B_measured_literature_observation"}
    assert {row["activation_state"] for row in rows} == {"reference_only"}
    assert all(row["source_location"] for row in rows if row["numeric_value"])

    by_id = {row["observation_id"]: row for row in rows}
    assert by_id["JURGUTIS21-YIELD-N170-SOLID-2018_2020_MEAN"]["numeric_value"] == "14.9"
    assert by_id["JURGUTIS21-YIELD-N85-LIQUID-MEAN-SOURCE-DISAGREEMENT"]["numeric_value"] == ""
    assert "10.10" in by_id["JURGUTIS21-YIELD-N85-LIQUID-MEAN-SOURCE-DISAGREEMENT"]["reported_value"]
    assert "10.11" in by_id["JURGUTIS21-YIELD-N85-LIQUID-MEAN-SOURCE-DISAGREEMENT"]["reported_value"]
    assert by_id["JURGUTIS21-GRASS-TOTAL-SOLIDS-CONTROL-2020"]["numeric_value"] == ""
    assert "no 2020 control" in by_id["JURGUTIS21-GRASS-TOTAL-SOLIDS-CONTROL-2018"]["limitations"]
    assert by_id["JURGUTIS21-PLANT-N-N170-LIQUID-2020"]["numeric_value"] == "3.19"
    assert by_id["JURGUTIS21-BMP-N170-LIQUID-2020-4"]["numeric_value"] == "222"
    assert by_id["JURGUTIS21-DIGESTATE-2019-LIQUID-TKN"]["unit"] == "%"
    assert by_id["JURGUTIS21-DIGESTATE-2020-BEFORE-SEPARATION-VFA"]["unit"] == "g L-1"
    assert "first week of July" in by_id["JURGUTIS21-CONTEXT-HARVEST-TIMING-CONFLICT"]["reported_value"]
    assert "second half of September" in by_id["JURGUTIS21-CONTEXT-HARVEST-TIMING-CONFLICT"]["reported_value"]


def test_sidecar_and_registers_mark_comparator_only_and_report_basis_limits():
    sidecar = json.loads(Path(str(CSV_PATH) + ".source.json").read_text(encoding="utf-8"))
    assert sidecar["doi"] == "10.1016/j.biombioe.2021.106211"
    assert sidecar["source_id"] == SOURCE_ID
    assert sidecar["record_count"] == 205
    assert sidecar["quality_class"] == "B"
    assert sidecar["sha256"] == hashlib.sha256(CSV_PATH.read_bytes()).hexdigest()
    assert "not Dutch roadside" in sidecar["limitations"][0]
    assert "harvest-timing inconsistency" in sidecar["limitations"][2]
    assert "10.10" in sidecar["limitations"][3] and "10.11" in sidecar["limitations"][3]
    assert "reference-only" in sidecar["runtime_policy"].lower()

    local_sources = _rows(DATA / "source_register.csv")
    local_ad_sources = _rows(DATA / "ad_source_register.csv")
    local_manifest = _rows(DATA / "dataset_manifest.csv")
    assert any(row["source_id"] == SOURCE_ID for row in local_sources)
    assert any(row["source_id"] == SOURCE_ID for row in local_ad_sources)
    manifest = next(row for row in local_manifest if row["filename"] == FILENAME)
    assert manifest["row_count"] == "205"
    assert manifest["integration_status"] == "traceable_reference_only_not_runtime_eligible"

    audit = ROOT / "Greenhub/data/global_audit_package"
    global_sources = _rows(audit / "global_source_register.csv")
    manifests = _rows(audit / "global_dataset_manifest.csv")
    readiness = _rows(audit / "global_dataset_readiness.csv")
    source = next(row for row in global_sources if row["dataset_path"] == RELATIVE_PATH)
    manifest = next(row for row in manifests if row["dataset_path"] == RELATIVE_PATH)
    gate = next(row for row in readiness if row["dataset_path"] == RELATIVE_PATH)
    assert source["source_id"] == SOURCE_ID
    assert source["doi_or_stable_id"] == sidecar["doi"]
    assert manifest["row_count_observed"] == "205"
    assert manifest["detected_readiness"] == gate["readiness"] == "D3"
    assert gate["unsourced_numeric_rows"] == "0"
    activation = next(
        row for row in _rows(audit / "dataset_activation_matrix.csv")
        if row["dataset_path"] == RELATIVE_PATH
    )
    assert activation["integration_eligibility"] == "reference_only"
    assert activation["active"] == "False"
    assert activation["default_eligibility"] == "False"
    checksum = next(
        row for row in _rows(audit / "source_dataset_checksums.csv")
        if row["dataset_path"] == RELATIVE_PATH
    )
    assert checksum["sha256"] == sidecar["sha256"]


def test_fair_catalog_indexes_the_jurgutis_dataset_and_source():
    catalog_path = ROOT / "Greenhub/data/fair_input_catalog/master_input_catalog.json"
    catalog = json.loads(catalog_path.read_text(encoding="utf-8"))
    asset = next(
        row for row in catalog["assets"]
        if row["relative_path"] == f"Greenhub/data/{RELATIVE_PATH}"
    )
    assert SOURCE_ID in asset["source_ids"].split(";")
    assert "10.1016/j.biombioe.2021.106211" in asset["source_dois"].split(";")
    assert str(asset["observed_rows"]) == "205"
    assert asset["readiness"] == "reference_only"
    assert asset["source_metadata_status"] == "linked_to_source_register"

