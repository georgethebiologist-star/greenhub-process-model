from __future__ import annotations

import csv
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "Greenhub" / "data" / "Bigas production + upgrade" / "AD kinetics"
FILENAME = "roadside_grass_juice_continuous_digestion_chopda_2026_abstract_reference.csv"


def _rows(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as stream:
        rows = list(csv.DictReader(stream))
    assert all(None not in row for row in rows)
    return rows


def test_chopda_abstract_data_are_source_limited_and_not_activated() -> None:
    rows = _rows(DATA / FILENAME)
    sidecar = json.loads((DATA / f"{FILENAME}.source.json").read_text(encoding="utf-8"))
    sources = _rows(DATA / "source_register.csv")
    manifest = _rows(DATA / "dataset_manifest.csv")

    assert len(rows) == sidecar["rows"] == 4
    assert {row["quality_class"] for row in rows} == {"B"}
    assert {row["activation_state"] for row in rows} == {"reference_only"}
    assert {row["source_id"] for row in rows} == {"SRC-CHOPDA-2026"}
    assert rows[0]["value"] == "39.9"
    assert "Denominator" in rows[0]["feed_basis"]
    assert "fresh matter" in rows[0]["feed_basis"]
    assert sidecar["doi"] == "10.1007/s12649-025-03274-4"
    assert sidecar["calculation_connected"] is False
    assert any("permission to share underlying data" in item for item in sidecar["limitations"])
    assert any(row["source_id"] == "SRC-CHOPDA-2026" for row in sources)
    assert any(row["filename"] == FILENAME and row["row_count"] == "4" for row in manifest)
