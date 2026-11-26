import csv
import json
from pathlib import Path

from biorefinery_platform.data_catalog import build_catalog_bundle


ROOT = Path(__file__).resolve().parents[1]
CSV_PATH = ROOT / "Greenhub/data/Pre-treatment/Mechanical/ryegrass_press_juice_varriale_2024_reference.csv"
PROFILE_PATH = ROOT / "biorefinery_platform/examples/material_profiles/ryegrass_press_juice_varriale_2024.json"


def test_press_juice_reference_is_complete_traceable_and_state_scoped():
    with CSV_PATH.open("r", encoding="utf-8", newline="") as file:
        rows = list(csv.DictReader(file))
    profile = json.loads(PROFILE_PATH.read_text(encoding="utf-8"))

    assert len(rows) == 18
    assert len({row["record_id"] for row in rows}) == len(rows)
    assert profile["project_id"] is None
    assert profile["data_scope_class"] == "technology_and_material_specific"
    assert profile["context_independent"] is False
    assert profile["activation_state"] == "reference_only"
    assert profile["mass_composition"] == []
    assert profile["closure"]["status"] == "not_checked"
    assert any("raw-feed UI" in gap for gap in profile["metadata_gaps"])
    assert profile["provenance"][0]["doi_or_stable_id"] == "10.1007/s00253-024-13224-0"

    properties = {item["property_id"]: item for item in profile["analytical_properties"]}
    assert len(properties) == len(rows)
    for row in rows:
        prop = properties[row["parameter"]]
        assert prop["unit"] == row["unit"]
        if row["result_status"] == "left_censored":
            assert prop["value"] == "<0.01"
            assert prop["detection_limit"] == "0.01 g/L"
            assert prop["status"] == "not_detected"
            assert not row["reported_value"]
        else:
            assert float(prop["value"]) == float(row["reported_value"])
            assert prop["status"] == "literature_value"


def test_press_juice_reference_is_discoverable_but_not_runtime_activated():
    bundle = build_catalog_bundle()
    row = next(item for item in bundle["datasets"] if item["filename"] == CSV_PATH.name)
    assert row["source_ids"] == ["S14_VARRIALE_2024_JUICE"]
    assert any("10.1007/s00253-024-13224-0" in value for value in row["source_dois_or_stable_ids"])
    assert row["source_locations"] == ["Table 1"]
    assert row["source_licenses"] == ["CC BY 4.0"]
    assert row["detected_readiness"] == "D3"
    assert row["activation_state"] == "reference_only"
    assert row["data_status_values"] == "reported;left_censored"
    assert row["context_independent"] is False
    assert row["metadata_gaps"] == []
    assert bundle["counts"]["d4_promotions"] == 0
