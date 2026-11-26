from __future__ import annotations

import csv
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "Greenhub" / "data" / "Pre-treatment" / "Feedstock"
FILENAME = "grass_liquid_formic_acid_precipitation_stefanski_2024_reference.csv"
SOURCE_ID = "SRC-STEFANSKI-EGF-2024"


def _rows(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as stream:
        return list(csv.DictReader(stream))


def test_stefanski_precipitation_reference_is_traceable_and_blocked_from_activation() -> None:
    rows = _rows(DATA / FILENAME)
    metadata = json.loads((DATA / f"{FILENAME}.source.json").read_text(encoding="utf-8"))
    sources = _rows(DATA / "source_register.csv")
    manifest = _rows(DATA / "dataset_manifest.csv")
    catalog = _rows(ROOT / "Greenhub" / "data" / "fair_input_catalog" / "master_input_catalog.csv")

    assert len(rows) == metadata["rows"] == 5
    assert {row["brown_liquid_pH_mean"] for row in rows} == {"4.41", "3.70", "3.49", "3.33", "3.21"}
    assert all(row["quality_class"] == "B" for row in rows)
    assert all(row["activation_state"] == "reference_only" for row in rows)
    assert all(row["dose_consistency_status"] in {"consistent_zero", "conflicting_source_dose_10fold"} for row in rows)
    assert "tenfold" in metadata["dose_basis_check"]
    assert metadata["calculation_connected"] is False
    assert metadata["runtime_parameter_mapping"] is None
    assert any(row["source_id"] == SOURCE_ID and not row["doi_or_stable_identifier"] for row in sources)
    assert any(row["file_name"] == FILENAME and row["row_count"] == "5" for row in manifest)
    indexed = next(row for row in catalog if row["relative_path"].endswith(FILENAME))
    assert SOURCE_ID in indexed["source_ids"]
    assert indexed["readiness"] == "reference_only"
    assert indexed["source_metadata_status"] in {"linked_to_source_register", "linked_to_local_source_record"}
