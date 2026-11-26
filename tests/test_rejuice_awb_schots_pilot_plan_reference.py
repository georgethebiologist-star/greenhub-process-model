from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
GROUP = ROOT / "Greenhub" / "data" / "Pre-treatment" / "Feedstock"
FILENAME = "rejuice_awb_schots_grass_juice_ad_pilot_plan_2026_reference.csv"
REL = f"Pre-treatment/Feedstock/{FILENAME}"


def _rows(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as stream:
        return list(csv.DictReader(stream))


def test_pilot_plan_values_are_not_misrepresented_as_results():
    path = GROUP / FILENAME
    rows = _rows(path)
    sidecar = json.loads(Path(str(path) + ".source.json").read_text(encoding="utf-8"))
    by_id = {row["record_id"]: row for row in rows}

    assert len(rows) == sidecar["record_count"] == 6
    assert by_id["REJUICE26-RJ-AWB-SCHOTS-REACTOR-VOLUME"]["value"] == "2.5"
    throughput = by_id["REJUICE26-RJ-AWB-SCHOTS-JUICE-THROUGHPUT"]
    assert throughput["value"] == "3000–9000"
    assert throughput["unit"] == "t/year"
    assert "Expected project value" in throughput["basis_or_status"]
    assert all(row["quality_class"] == "not_applicable_project_plan_not_measurement" for row in rows)
    assert all(row["activation_state"] == "reference_only" for row in rows)
    assert sidecar["calculation_connected"] is False
    assert sidecar["runtime_parameter_mapping"] is None
    assert sidecar["data_collection_lead"]["follow_up_event"]
    assert "not a measured" in sidecar["limitations"][0]


def test_pilot_plan_is_registered_and_checksummed():
    path = GROUP / FILENAME
    audit = ROOT / "Greenhub" / "data" / "global_audit_package"
    sources = _rows(GROUP / "source_register.csv")
    local_manifest = _rows(GROUP / "dataset_manifest.csv")
    global_source = next(row for row in _rows(audit / "global_source_register.csv") if row["dataset_path"] == REL)
    manifest = next(row for row in _rows(audit / "global_dataset_manifest.csv") if row["dataset_path"] == REL)
    readiness = next(row for row in _rows(audit / "global_dataset_readiness.csv") if row["dataset_path"] == REL)
    checksum = next(row for row in _rows(audit / "source_dataset_checksums.csv") if row["dataset_path"] == REL)

    assert any(row["source_id"] == "SRC-REJUICE-AWB-SCHOTS-PILOT-PLAN-2026" for row in sources)
    assert any(row["file_name"] == FILENAME and row["row_count"] == "6" for row in local_manifest)
    assert global_source["year"] == "2026"
    assert manifest["detected_readiness"] == "D3"
    assert readiness["numeric_rows"] == "2"
    assert readiness["unsourced_numeric_rows"] == "0"
    assert checksum["sha256"] == hashlib.sha256(path.read_bytes()).hexdigest()
