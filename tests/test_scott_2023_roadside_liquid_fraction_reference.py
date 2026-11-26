from __future__ import annotations

import csv
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "Greenhub" / "data" / "Resource recovery" / "Phosphorus_Recovery"
FILENAME = "roadside_grass_liquid_fraction_nutrient_metals_scott_2023_reference.csv"


def _rows(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as stream:
        return list(csv.DictReader(stream))


def test_scott_press_liquid_nutrient_data_preserves_basis_license_and_limits() -> None:
    rows = _rows(DATA / FILENAME)
    metadata = json.loads((DATA / f"{FILENAME}.source.json").read_text(encoding="utf-8"))
    manifest = _rows(DATA / "dataset_manifest.csv")
    catalog = _rows(ROOT / "Greenhub" / "data" / "fair_input_catalog" / "master_input_catalog.csv")

    assert len(rows) == metadata["rows"] == 18
    by_id = {row["record_id"]: row for row in rows}
    assert by_id["SCOTT23-GLF-N"]["mean_mg_per_kg_fresh_matter"] == "1280"
    assert by_id["SCOTT23-GLF-N"]["mean_mg_per_kg_dry_matter"] == "38788"
    assert by_id["SCOTT23-GLF-Cd"]["maximum_permissible_concentration_mg_per_kg_dry_matter"] == "1.5"
    assert by_id["SCOTT23-GLF-Cr"]["mean_mg_per_kg_dry_matter"] == "2.4"
    assert by_id["SCOTT23-GLF-Hg"]["mean_mg_per_kg_fresh_matter"] == "0.00"
    assert all(row["replicates"] == "3" and row["quality_class"] == "B" for row in rows)
    assert all(row["activation_state"] == "reference_only" for row in rows)
    assert "CC BY-NC" in metadata["license"]
    assert metadata["calculation_connected"] is False
    assert any(row["filename"] == FILENAME and row["row_count"] == "18" for row in manifest)
    indexed = next(row for row in catalog if row["relative_path"].endswith(FILENAME))
    assert indexed["source_ids"] == "SRC-SCOTT-2023"
    assert indexed["source_dois"] == "10.1002/jpln.202200308"
