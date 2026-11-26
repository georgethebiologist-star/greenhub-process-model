import csv
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "Greenhub/data/Pre-treatment/Feedstock"
FILENAME = "greenhub_bermgras_canvas_quality_routing_2025_reference.csv"


def _rows(path):
    with path.open(encoding="utf-8-sig", newline="") as stream:
        return list(csv.DictReader(stream))


def test_bermgras_canvas_guidance_is_qualitative_traceable_and_not_activated():
    rows = _rows(DATA_DIR / FILENAME)
    sidecar = json.loads((DATA_DIR / f"{FILENAME}.source.json").read_text(encoding="utf-8"))
    sources = _rows(DATA_DIR / "source_register.csv")
    manifest = _rows(DATA_DIR / "dataset_manifest.csv")

    assert len(rows) == sidecar["rows"] == 7
    assert {row["source_id"] for row in rows} == {"SRC-GHZH-KEUZEHULP-2025"}
    assert {row["phase"] for row in rows} == {"1"}
    assert {row["quality_class"] for row in rows} == {"not_applicable_guidance"}
    assert {row["activation_state"] for row in rows} == {"reference_only"}
    by_id = {row["record_id"]: row for row in rows}
    assert "A+ or A" in by_id["GHZH-QC-GREEN"]["reported_threshold"]
    assert by_id["GHZH-QC-ORANGE"]["reported_threshold"] == "CROW visual-quality B"
    assert by_id["GHZH-QC-RED"]["reported_threshold"] == "CROW visual-quality C or D"
    assert "first metre" in by_id["GHZH-QC-ROAD-SAFETY-STRIP"]["classification"]
    assert "tyre wear" in by_id["GHZH-QC-INVISIBLE-CONTAMINATION"]["classification"]
    assert all(row["reported_threshold"] == "" for row in rows[3:])
    assert sidecar["calculation_connected"] is False
    assert sidecar["runtime_parameter_mapping"] is None
    assert any(row["source_id"] == "SRC-GHZH-KEUZEHULP-2025" for row in sources)
    assert any(row["file_name"] == FILENAME and row["row_count"] == "7" for row in manifest)

