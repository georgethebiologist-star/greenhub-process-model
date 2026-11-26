from __future__ import annotations

import csv
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "Greenhub" / "data" / "Pre-treatment" / "Feedstock"
FILENAME = "roadside_grass_harvest_performance_brown_2020_reference.csv"


def _rows(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as stream:
        return list(csv.DictReader(stream))


def test_brown_harvest_observations_are_traceable_and_not_default_activated() -> None:
    path = DATA / FILENAME
    rows = _rows(path)
    metadata = json.loads((DATA / f"{FILENAME}.source.json").read_text(encoding="utf-8"))
    manifest = _rows(DATA / "dataset_manifest.csv")
    catalog = _rows(ROOT / "Greenhub" / "data" / "fair_input_catalog" / "master_input_catalog.csv")

    assert len(rows) == metadata["rows"] == 2
    by_year = {row["harvest_year"]: row for row in rows}
    assert set(by_year) == {"2016", "2018"}
    assert by_year["2016"]["fresh_yield_t_per_ha"] == "12.5"
    assert by_year["2016"]["dry_matter_yield_t_dm_per_ha"] == "3.0"
    assert by_year["2016"]["average_collection_rate_t_per_h"] == ""
    assert by_year["2018"]["average_collection_rate_t_per_h"] == "3.0"
    assert by_year["2018"]["travel_speed_km_per_h"] == "5.0"
    assert by_year["2018"]["road_travel_speed_km_per_h"] == "60"
    assert by_year["2018"]["very_wet_harvest_speed_km_per_h"] == "3"
    assert by_year["2018"]["harvester_capacity_t"] == "15"
    assert by_year["2016"]["road_travel_speed_km_per_h"] == ""
    assert by_year["2016"]["harvester_capacity_t"] == ""
    assert all(row["quality_class"] == "B" and row["activation_state"] == "reference_only" for row in rows)
    assert metadata["doi"] == "10.1016/j.biombioe.2020.105570"
    assert metadata["calculation_connected"] is False
    assert any(row["file_name"] == FILENAME and row["row_count"] == "2" for row in manifest)
    indexed = next(row for row in catalog if row["relative_path"].endswith(FILENAME))
    assert indexed["source_ids"] == "SRC-BROWN-2020"
    assert indexed["source_dois"] == "10.1016/j.biombioe.2020.105570"
