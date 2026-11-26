from __future__ import annotations

import csv
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "Greenhub" / "data" / "Pre-treatment" / "Feedstock"
FILENAME = "roadside_cutting_field_decay_schaffers_1998_reference.csv"


def _rows(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as stream:
        return list(csv.DictReader(stream))


def test_schaffers_field_decay_reference_is_traceable_and_not_activated() -> None:
    rows = _rows(DATA / FILENAME)
    sidecar = json.loads((DATA / f"{FILENAME}.source.json").read_text(encoding="utf-8"))
    sources = _rows(DATA / "source_register.csv")
    manifest = _rows(DATA / "dataset_manifest.csv")

    assert len(rows) == sidecar["rows"] == 8
    assert {row["source_id"] for row in rows} == {"SRC-SCHAFFERS-1998"}
    assert {row["quality_class"] for row in rows} == {"B"}
    assert {row["activation_state"] for row in rows} == {"reference_only"}
    assert sidecar["doi"] == "10.1046/j.1365-2664.1998.00316.x"
    assert sidecar["calculation_connected"] is False
    assert "fresh cuttings left in field" in " ".join(sidecar["limitations"])
    by_plot = {row["plot_name"]: row for row in rows}
    assert by_plot["Dodewaard"]["dm_asymptotic_fraction"] == "0.54"
    assert by_plot["Dodewaard"]["dm_k_per_week"] == "0.083"
    assert by_plot["Almelo"]["n_asymptotic_fraction"] == ""
    assert by_plot["Rossum east"]["n_fit_r2"] == "0.20"
    assert any(row["source_id"] == "SRC-SCHAFFERS-1998" for row in sources)
    assert any(row["file_name"] == FILENAME and row["row_count"] == "8" for row in manifest)
