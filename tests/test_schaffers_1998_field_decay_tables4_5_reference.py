from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "Greenhub" / "data" / "Pre-treatment" / "Feedstock"
FILENAME = "roadside_cutting_field_decay_schaffers_1998_tables4_5_reference.csv"


def _rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as stream:
        return list(csv.DictReader(stream))


def test_schaffers_tables4_5_reference_is_source_located_and_not_activated() -> None:
    path = DATA / FILENAME
    rows = _rows(path)
    sidecar = json.loads(Path(f"{path}.source.json").read_text(encoding="utf-8"))
    sources = _rows(DATA / "source_register.csv")
    manifests = _rows(DATA / "dataset_manifest.csv")
    table4 = [row for row in rows if row["source_table"] == "Table 4"]
    table5 = [row for row in rows if row["source_table"] == "Table 5"]

    assert len(rows) == sidecar["record_count"] == 92
    assert len(table4) == 64
    assert len(table5) == 28
    assert {row["source_id"] for row in rows} == {"SRC-SCHAFFERS-1998"}
    assert {row["quality_class"] for row in rows} == {"B"}
    assert {row["activation_state"] for row in rows} == {"reference_only"}
    assert sidecar["runtime_parameter_mapping"] is None
    assert sidecar["source_file_sha256"] == hashlib.sha256(path.read_bytes()).hexdigest()
    assert sidecar["doi"] == "10.1046/j.1365-2664.1998.00316.x"
    assert "model-estimated community means" in " ".join(sidecar["limitations"])

    t4 = {row["record_id"]: row for row in table4}
    assert t4["SCH98-T4-DRY_WEIGHT-Ran-W1"]["reported_value"] == "77.5"
    assert t4["SCH98-T4-DRY_WEIGHT-Arrh-W1"]["significance_marker"] == "*"
    assert t4["SCH98-T4-POTASSIUM-Ran-K"]["reported_value"] == "0.091"
    assert t4["SCH98-T4-POTASSIUM-Arrh-K"]["reported_value"] == "0.054"
    assert all(
        row["unit"] == "% of initial amount remaining"
        for row in table4
        if row["record_type"] != "asymptotic_rate_constant"
    )

    t5 = {row["record_id"]: row for row in table5}
    assert t5["SCH98-T5-DRY_WEIGHT-1"]["coefficient_b"] == "0.74"
    assert t5["SCH98-T5-DRY_WEIGHT-1"]["coefficient_c"] == "60.3"
    assert t5["SCH98-T5-NITROGEN-ASYMPTOTIC"]["significance_p"] == "0.019"
    assert t5["SCH98-T5-POTASSIUM-ASYMPTOTIC"]["record_type"] == "no_satisfactory_fit_reported"
    assert t5["SCH98-T5-POTASSIUM-ASYMPTOTIC"]["coefficient_b"] == ""

    assert any(row["source_id"] == "SRC-SCHAFFERS-1998" for row in sources)
    assert any(row["file_name"] == FILENAME and row["row_count"] == "92" for row in manifests)
