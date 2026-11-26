from __future__ import annotations

import csv
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "Greenhub" / "data" / "Pre-treatment" / "Feedstock"
FILENAME = "hdsr_mowing_material_digestion_projection_2021_reference.csv"


def _rows(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as stream:
        return list(csv.DictReader(stream))


def test_hdsr_projected_feed_and_biogas_are_linked_reference_only() -> None:
    rows = _rows(DATA / FILENAME)
    metadata = json.loads((DATA / f"{FILENAME}.source.json").read_text(encoding="utf-8"))
    manifest = _rows(DATA / "dataset_manifest.csv")
    sources = _rows(DATA / "source_register.csv")
    catalog = _rows(ROOT / "Greenhub" / "data" / "fair_input_catalog" / "master_input_catalog.csv")

    assert len(rows) == metadata["rows"] == 2
    by_id = {row["record_id"]: row for row in rows}
    feed = by_id["HDSR21-NEWGEIN-FEED-30000"]
    gas = by_id["HDSR21-NEWGEIN-BIOGAS-3400000"]
    assert feed["reported_value"] == "30000"
    assert feed["unit"] == "t/year (wet/dry basis unstated)"
    assert gas["reported_value"] == "3400000"
    assert gas["unit"] == "m3 biogas/year (reference conditions unstated)"
    assert feed["scenario"] == gas["scenario"]
    assert all(row["quality_class"] == "B" and row["activation_state"] == "reference_only" for row in rows)
    assert "no measured gas yield" in gas["basis_or_denominator"]
    assert "procurement" in feed["limitations"]
    assert metadata["calculation_connected"] is False
    assert metadata["runtime_parameter_mapping"] is None
    assert any(row["file_name"] == FILENAME and row["row_count"] == "2" for row in manifest)
    assert "SRC-HDSR-BIOMASS-PROJECTION-2021" in {row["source_id"] for row in sources}
    asset = next(row for row in catalog if row["relative_path"].endswith(FILENAME))
    assert asset["source_ids"] == "SRC-HDSR-BIOMASS-PROJECTION-2021"
    assert asset["readiness"] == "reference_only"
    assert asset["maturity"] == "D3"
    assert asset["activation_state"] == "reference_only"

    # This project proposal is evidence for scope only, not an activated process calculation.
    package_code = "\n".join(path.read_text(encoding="utf-8") for path in (ROOT / "Greenhub").rglob("*.py"))
    assert FILENAME not in package_code
