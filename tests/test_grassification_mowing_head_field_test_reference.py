from __future__ import annotations

import csv
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "Greenhub" / "data" / "Pre-treatment" / "Mechanical" / "grassification_mowing_head_field_test_2019_reference.csv"


def test_grassification_mowing_trial_is_traceable_and_preserves_conflict() -> None:
    with DATA.open(encoding="utf-8-sig", newline="") as stream:
        rows = list(csv.DictReader(stream))
    metadata = json.loads(DATA.with_suffix(".source.json").read_text(encoding="utf-8"))
    with (DATA.parent / "source_register.csv").open(encoding="utf-8-sig", newline="") as stream:
        sources = list(csv.DictReader(stream))
    with (DATA.parent / "dataset_manifest.csv").open(encoding="utf-8-sig", newline="") as stream:
        manifest = list(csv.DictReader(stream))

    assert len(rows) == 36
    assert len({row["observation_id"] for row in rows}) == len(rows)
    assert {row["activation_state"] for row in rows} == {"reference_only"}
    assert {row["evidence_class"] for row in rows} == {"B_measured"}
    assert all(row["source_id"] == "S12_GRASSIFICATION_D112_2019" for row in rows)

    by_id = {row["observation_id"]: row for row in rows}
    assert by_id["GRASSIF-D112-VANDAELE-SPEED-A"]["value"] == "3.7"
    assert by_id["GRASSIF-D112-HERDER-BIN-CAPACITY"]["value"] == "12"
    assert by_id["GRASSIF-D112-FLAIL-DM-TABLE"]["value"] == "27"
    assert by_id["GRASSIF-D112-FLAIL-SAND-TABLE"]["value"] == "2.8"
    assert by_id["GRASSIF-D112-FLAIL-SAND-PROSE"]["value"] == "2.9"
    assert by_id["GRASSIF-D112-FLAIL-FIBRE-BIN-LT4"]["value"] == "10.4"

    assert metadata["source_id"] == "S12_GRASSIFICATION_D112_2019"
    assert metadata["activation_state"] == "reference_only"
    assert "no explicit reuse license" in metadata["license"].lower()
    assert any(row["source_id"] == "S12_GRASSIFICATION_D112_2019" for row in sources)
    assert any(row["filename"] == DATA.name and row["row_count"] == "36" for row in manifest)
