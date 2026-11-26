from __future__ import annotations

import csv
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "Greenhub" / "data" / "Pre-treatment" / "Feedstock"
FILENAME = "2seas_zeeland_regional_seasonal_feedstock_supply_2021_reference.csv"


def _rows(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as stream:
        rows = list(csv.DictReader(stream))
    assert all(None not in row for row in rows)
    return rows


def test_zeeland_area_and_seasonal_supply_bases_remain_separate() -> None:
    rows = _rows(DATA / FILENAME)
    sidecar = json.loads((DATA / f"{FILENAME}.source.json").read_text(encoding="utf-8"))
    manifest = _rows(DATA / "dataset_manifest.csv")

    assert len(rows) == sidecar["rows"] == 45
    assert len({row["record_id"] for row in rows}) == 45
    assert {row["source_id"] for row in rows} == {"SRC-MOOV-VITO-2021"}
    assert all(row["activation_state"] == "reference_only" for row in rows)

    by_key = {(row["table_id"], row["entity"], row["variable"], row["period"]): row for row in rows}
    assert by_key[("Table 9", "Total listed managers", "estimated_verge_area", "all")]["value"] == "2987"
    assert by_key[("Table 10", "Total mapped", "verge_area", "standard_mowing")]["value"] == "2340"
    assert by_key[("Table 11", "Total PZ plus WSS", "technical_supply", "annual_total")]["value"] == "42300"
    assert by_key[("Table 11", "Total PZ plus WSS", "one_cut_technical_supply", "annual_total")]["value"] == "25300"
    assert by_key[("Table 23", "Total PZ plus WSS", "technical_supply", "annual_total")]["unit"] == "t DM/year"
    assert by_key[("Figure 42", "Total PZ plus WSS", "current_collected_quantity", "annual_total")]["value"] == "250"
    assert "historical" in by_key[("Figure 42", "Total PZ plus WSS", "current_collected_share", "annual_total")]["limitations"]
    assert all(row["quality_class"] == "C" for row in rows if row["table_id"] in {"Table 11", "Table 23", "Figure 42"})
    assert sidecar["calculation_connected"] is False
    assert any(row["file_name"] == FILENAME and row["row_count"] == "45" for row in manifest)
