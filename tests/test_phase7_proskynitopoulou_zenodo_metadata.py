import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "Greenhub/data/Resource recovery/Phosphorus_Recovery"


def test_phase7_public_dataset_is_findable_but_license_gate_is_preserved():
    record = json.loads(
        (DATA / "proskynitopoulou_2024_pilot_data_zenodo.source.json").read_text(encoding="utf-8")
    )
    assert record["doi"] == "10.5281/zenodo.15040664"
    assert record["activation_state"] == "reference_only_external"
    assert record["data_license"] is None
    assert len(record["files"]) == 4
    assert sum(item["size_bytes"] for item in record["files"]) == record["combined_size_bytes"]
    assert all(item["md5"] for item in record["files"])
    assert "No supplementary file content" in record["data_handling"]
    assert "CC BY-NC-ND 4.0" in record["related_publication"]["article_license"]
