from __future__ import annotations

import csv
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "Greenhub" / "data" / "Pre-treatment" / "Feedstock" / "grassification_roadside_press_juice_characterization_2018_2019_reference.csv"


def test_grassification_roadside_juice_data_is_traceable_and_reference_only() -> None:
    with DATA.open(encoding="utf-8-sig", newline="") as stream:
        rows = list(csv.DictReader(stream))
    metadata = json.loads(DATA.with_suffix(".source.json").read_text(encoding="utf-8"))
    with (DATA.parent / "source_register.csv").open(encoding="utf-8-sig", newline="") as stream:
        sources = list(csv.DictReader(stream))
    with (DATA.parent / "dataset_manifest.csv").open(encoding="utf-8-sig", newline="") as stream:
        manifest = list(csv.DictReader(stream))

    assert len(rows) == 24
    assert len({row["observation_id"] for row in rows}) == len(rows)
    assert {row["session_id"] for row in rows} == {"S1", "S2"}
    assert {row["activation_state"] for row in rows} == {"reference_only"}
    assert {row["evidence_class"] for row in rows} == {"B_measured"}
    assert all(row["source_id"] == "SRC-GRASSIFICATION-D231-2020" for row in rows)

    by_id = {row["observation_id"]: row for row in rows}
    assert by_id["GRASSIF-D231-S1-LIQUID-YIELD"]["value"] == "42.8"
    assert by_id["GRASSIF-D231-S2-TS"]["value"] == "11.76"
    assert by_id["GRASSIF-D231-S2-PROTEIN-RAW"]["value"] == "24.57"
    assert by_id["GRASSIF-D231-S2-PROTEIN-SOLID"]["fraction"] == "solid fraction after centrifugation"
    assert "ammonium salts" in by_id["GRASSIF-D231-S2-PROTEIN-SOLID"]["limitations"]

    assert metadata["source_id"] == "SRC-GRASSIFICATION-D231-2020"
    assert metadata["activation_state"] == "reference_only"
    assert "no explicit reuse license" in metadata["license"].lower()
    assert any(row["source_id"] == "SRC-GRASSIFICATION-D231-2020" for row in sources)
    assert any(row["file_name"] == DATA.name and row["row_count"] == "24" for row in manifest)
