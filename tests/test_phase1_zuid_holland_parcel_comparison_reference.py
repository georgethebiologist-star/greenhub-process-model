from __future__ import annotations

import csv
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "Greenhub" / "data" / "Pre-treatment" / "Feedstock"
DATA_FILE = DATA_DIR / "zuid_holland_bermmaaisel_parcel_areas_and_quantity_comparison_2021_reference.csv"


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as stream:
        reader = csv.DictReader(stream)
        rows = list(reader)
        assert reader.fieldnames
        assert all(None not in row and all(value is not None for value in row.values()) for row in rows)
        return rows


def test_south_holland_parcel_data_separates_reported_estimated_and_potential_values() -> None:
    rows = _read_csv(DATA_FILE)
    metadata = json.loads(DATA_FILE.with_name(DATA_FILE.name + ".source.json").read_text(encoding="utf-8"))
    source_rows = _read_csv(DATA_DIR / "source_register.csv")
    manifest_rows = _read_csv(DATA_DIR / "dataset_manifest.csv")
    catalog_rows = _read_csv(ROOT / "Greenhub" / "data" / "fair_input_catalog" / "master_input_catalog.csv")

    assert len(rows) == metadata["record_count"] == 12
    assert len({row["record_id"] for row in rows}) == 12
    assert {row["activation_state"] for row in rows} == {"reference_only"}
    assert {row["source_id"] for row in rows} == {"SRC-PZH-BERMMAAISEL-2021"}
    assert {row["doi"] for row in rows} == {""}

    by_id = {row["record_id"]: row for row in rows}
    assert by_id["PZH21-PROVINCE-FOUR-PARCEL-TOTAL"]["reported_value"] == "11000"
    assert by_id["PZH21-EAST-COLLECTED"]["reported_value"] == "1500"
    assert by_id["PZH21-WEST-COLLECTED"]["reported_value"] == "2500"
    assert by_id["PZH21-SOUTH-COLLECTED-ESTIMATE"]["reported_value"] == "3500"
    assert by_id["PZH21-NORTH-LITERATURE-POTENTIAL"]["reported_value"] == "3482"
    assert "no North value is inferred" in metadata["limitations"][2]
    assert "does not state" in metadata["mass_basis"]
    assert not any(row["parcel_id"] == "north" and "collected_quantity" in row["metric"] for row in rows)
    assert {row["quality_class"] for row in rows if row["metric"] == "source_calculated_fresh_biomass_potential"} == {"C"}

    source = [row for row in source_rows if row["source_id"] == "SRC-PZH-BERMMAAISEL-2021"]
    assert len(source) == 1 and source[0]["doi_or_stable_identifier"] == ""
    manifest = [row for row in manifest_rows if row["file_name"] == DATA_FILE.name]
    assert len(manifest) == 1 and manifest[0]["row_count"] == "12"
    assert "not_runtime_eligible" in manifest[0]["integration_readiness"]
    asset = [row for row in catalog_rows if row["relative_path"].endswith(DATA_FILE.name)]
    assert len(asset) == 1
    assert asset[0]["source_ids"] == "SRC-PZH-BERMMAAISEL-2021"
    assert asset[0]["source_metadata_status"] == "linked_to_source_register"
