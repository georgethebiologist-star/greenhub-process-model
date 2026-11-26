from __future__ import annotations

import csv
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "Greenhub" / "data" / "Pre-treatment" / "Feedstock"
FILENAME = "2seas_verge_grass_seasonal_harvest_potential_2021_reference.csv"


def _rows(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as stream:
        rows = list(csv.DictReader(stream))
    assert all(None not in row for row in rows)
    return rows


def test_2seas_seasonal_harvest_estimates_are_traceable_and_not_activated() -> None:
    rows = _rows(DATA / FILENAME)
    metadata = json.loads((DATA / f"{FILENAME}.source.json").read_text(encoding="utf-8"))
    manifest = _rows(DATA / "dataset_manifest.csv")
    catalog = _rows(ROOT / "Greenhub" / "data" / "fair_input_catalog" / "master_input_catalog.csv")

    assert len(rows) == metadata["rows"] == 30
    assert {row["source_id"] for row in rows} == {"SRC-MOOV-VITO-2021"}
    assert {row["feedstock_type"] for row in rows} == {
        "AWV-RR grass", "AWV-HW grass", "MUN grass", "PZ grass", "WSS grass"
    }
    assert {row["harvest_period"] for row in rows} == {"summer", "autumn", "annual_total"}
    assert {row["quantity_type"] for row in rows} == {"theoretical", "technical"}
    assert {row["unit"] for row in rows} == {"t fresh/ha"}
    assert all(row["activation_state"] == "reference_only" for row in rows)
    assert all(row["quality_class"] == "B" for row in rows if row["quantity_type"] == "theoretical")
    assert all(row["quality_class"] == "C" for row in rows if row["quantity_type"] == "technical")

    lookup = {(r["demo_id"], r["feedstock_type"], r["harvest_period"], r["quantity_type"]): r for r in rows}
    assert lookup[("DEMO2", "PZ grass", "summer", "theoretical")]["value"] == "13.8"
    assert lookup[("DEMO2", "PZ grass", "annual_total", "technical")]["value"] == "16.6"
    assert "70%" in lookup[("DEMO2", "PZ grass", "summer", "technical")]["source_derivation"]
    assert metadata["doi"] is None
    assert metadata["calculation_connected"] is False
    assert any(row["file_name"] == FILENAME and row["row_count"] == "30" for row in manifest)
    asset = next(row for row in catalog if row["relative_path"].endswith(FILENAME))
    assert asset["source_ids"] == "SRC-MOOV-VITO-2021"
    assert asset["source_urls"].startswith("https://moov.vito.be/")
