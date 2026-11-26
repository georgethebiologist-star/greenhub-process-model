import csv
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "Greenhub/data/Pre-treatment/Feedstock"
FILENAME = "greenhub_zuid_holland_processing_capacity_ambitions_2026_reference.csv"


def _rows(path):
    with path.open(encoding="utf-8-sig", newline="") as stream:
        return list(csv.DictReader(stream))


def test_capacity_ambitions_are_traceable_separate_targets_not_model_inputs():
    rows = _rows(DATA_DIR / FILENAME)
    sidecar = json.loads((DATA_DIR / f"{FILENAME}.source.json").read_text(encoding="utf-8"))
    sources = _rows(DATA_DIR / "source_register.csv")
    manifest = _rows(DATA_DIR / "dataset_manifest.csv")

    assert len(rows) == sidecar["rows"] == 2
    assert {row["value"] for row in rows} == {"30000"}
    assert {row["unit"] for row in rows} == {"t/year"}
    assert {row["quality_class"] for row in rows} == {"not_applicable_project_target"}
    assert {row["activation_state"] for row in rows} == {"reference_only"}
    grass = next(row for row in rows if "Roadside verge" in row["target_scope"])
    mixed = next(row for row in rows if "horticulture" in row["target_scope"])
    assert "3–5 years" in grass["reported_timeframe"]
    assert grass["source_url"] != mixed["source_url"]
    assert "not installed" in grass["limitations"]
    assert "must not be added" in mixed["limitations"]
    assert sidecar["calculation_connected"] is False
    assert sidecar["runtime_parameter_mapping"] is None
    assert any(row["source_id"] == "SRC-GHZH-CAPACITY-AMBITION-2026" for row in sources)
    assert any(row["file_name"] == FILENAME and row["row_count"] == "2" for row in manifest)

