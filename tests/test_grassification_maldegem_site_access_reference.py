from __future__ import annotations

import csv
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DATA = (
    ROOT
    / "Greenhub"
    / "data"
    / "Pre-treatment"
    / "Mechanical"
    / "grassification_maldegem_site_access_observations_2019_reference.csv"
)


def test_site_access_observations_preserve_units_missingness_and_scope() -> None:
    with DATA.open(encoding="utf-8-sig", newline="") as stream:
        rows = list(csv.DictReader(stream))
    metadata = json.loads(DATA.with_name(DATA.name + ".source.json").read_text(encoding="utf-8"))

    assert len(rows) == 30
    assert len({row["observation_id"] for row in rows}) == 30
    assert {row["activation_state"] for row in rows} == {"reference_only"}
    assert {row["quality_class"] for row in rows} == {"B"}
    assert {row["source_id"] for row in rows} == {"S12_GRASSIFICATION_D112_2019"}
    assert {row["parameter"] for row in rows} == {
        "slope_angle",
        "manual_pin_penetration",
        "visible_litter_class",
    }

    slope = {
        row["site_id"]: row["value"]
        for row in rows
        if row["parameter"] == "slope_angle"
    }
    assert slope == {
        str(site): value
        for site, value in enumerate(("18", "17", "15", "51", "20", "24", "15", "21", "27", "10"), 1)
    }
    point_four = [row for row in rows if row["site_id"] == "4"]
    assert all(row["latitude"] == "" and row["longitude"] == "" for row in point_four)
    assert {row["reported_text"] for row in rows if row["parameter"] == "visible_litter_class"} == {
        "Very clean",
        "Clean",
    }
    assert "not a standardized" in metadata["uncertainty"].lower()
    assert metadata["activation_state"] == "reference_only"
    assert metadata["runtime_mapping"] == "none"
