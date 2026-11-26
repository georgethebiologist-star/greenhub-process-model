from __future__ import annotations

import csv
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "Greenhub" / "data" / "Bigas production + upgrade" / "Feed BMP"
DATA_FILE = DATA_DIR / "grass_manure_continuous_codigestion_moset_2017_abstract_reference.csv"


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as stream:
        return list(csv.DictReader(stream))


def test_moset_2017_abstract_extract_is_traceable_and_not_activated() -> None:
    rows = _read_csv(DATA_FILE)
    metadata = json.loads(DATA_FILE.with_name(DATA_FILE.name + ".source.json").read_text(encoding="utf-8"))
    manifest = _read_csv(DATA_DIR / "dataset_manifest.csv")
    sources = _read_csv(DATA_DIR / "source_register.csv")

    assert len(rows) == 16
    assert len({row["record_id"] for row in rows}) == len(rows)
    assert {row["phase"] for row in rows} == {"3;5", "5", "5;6", "5;7", "7"}
    assert {row["activation_state"] for row in rows} == {"reference_only"}
    assert {row["quality_class"] for row in rows} == {"B"}
    assert {row["doi"] for row in rows} == {"10.1016/j.energy.2017.08.068"}
    assert all(row["source_location"] == "Abstract" for row in rows)

    by_id = {row["record_id"]: row for row in rows}
    assert by_id["MOSET17-HRT"]["reported_value"] == "25"
    assert by_id["MOSET17-GRASS-INCLUSION"]["reported_value"] == "5"
    assert by_id["MOSET17-EXCORIATED-YIELD-15L"]["reported_value"] == "20"
    assert by_id["MOSET17-EXCORIATED-YIELD-30M3"]["reported_value"] == "35"
    assert "percentage points" in by_id["MOSET17-BIOGAS-CH4-FRACTION"]["limitations"]
    assert "do not use as a mixing-energy coefficient" in by_id["MOSET17-MIXING-ENERGY-EXTRA"]["limitations"]

    assert metadata["rows"] == len(rows)
    assert metadata["doi"] == "10.1016/j.energy.2017.08.068"
    assert metadata["activation_state"] == "reference_only"
    assert metadata["runtime_mapping"] == "none"
    assert any(row["filename"] == DATA_FILE.name and row["row_count"] == "16" for row in manifest)
    source = [row for row in sources if row["source_id"] == "SRC-MOSET-2017"]
    assert len(source) == 1
