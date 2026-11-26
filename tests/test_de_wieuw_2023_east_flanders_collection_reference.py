from __future__ import annotations

import csv
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "Greenhub" / "data" / "Pre-treatment" / "Feedstock"
DATA_FILE = DATA_DIR / "east_flanders_roadside_grass_collection_points_de_wieuw_2023_reference.csv"


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as stream:
        return list(csv.DictReader(stream))


def test_collection_point_estimates_preserve_source_totals_and_limits() -> None:
    rows = _read_csv(DATA_FILE)
    metadata = json.loads(DATA_FILE.with_name(DATA_FILE.name + ".source.json").read_text(encoding="utf-8"))
    source_rows = _read_csv(DATA_DIR / "source_register.csv")
    manifest_rows = _read_csv(DATA_DIR / "dataset_manifest.csv")

    assert len(rows) == metadata["rows"] == 43
    assert all(len(row) == 13 and all(value is not None for value in row.values()) for row in rows)
    assert len({row["record_id"] for row in rows}) == len(rows)

    locations = [row for row in rows if row["location_id"]]
    assert len(locations) == 41
    assert [row["location_id"] for row in locations] == [f"X{i}" for i in range(1, 42)]
    assert sum(int(row["reported_value"]) for row in locations) == 9931
    assert {row["activation_state"] for row in rows} == {"reference_only"}
    assert {row["quality_class"] for row in rows} == {"B"}
    assert {row["doi"] for row in rows} == {"10.3390/su151814006"}
    assert {row["reported_unit"] for row in rows} == {"t wet matter"}

    by_id = {row["record_id"]: row for row in rows}
    assert by_id["DF23-TABLE-TOTAL"]["reported_value"] == "9931"
    assert by_id["DF23-SCENARIO1-TOTAL"]["reported_value"] == "9841"
    assert "differs" in by_id["DF23-SCENARIO1-TOTAL"]["basis"]

    source = [row for row in source_rows if row["source_id"] == "SRC-DEWIEUW-2023"]
    assert len(source) == 1
    assert "CC BY 4.0" in source[0]["quality_notes"]
    manifest = [row for row in manifest_rows if row["file_name"] == DATA_FILE.name]
    assert len(manifest) == 1 and manifest[0]["row_count"] == "43"
    assert metadata["license"] == "Creative Commons Attribution 4.0 International (CC BY 4.0)"
    assert metadata["activation_state"] == "reference_only"
    assert metadata["runtime_parameter_mapping"] is None
