from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
GROUP = ROOT / "Greenhub" / "data" / "Pre-treatment" / "Feedstock"
FILENAME = "greenhub_autumn_roadside_grass_600t_announcement_reference.csv"
REL = f"Pre-treatment/Feedstock/{FILENAME}"


def _rows(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as stream:
        return list(csv.DictReader(stream))


def test_600_t_announcement_is_not_treated_as_measured_or_available_supply():
    path = GROUP / FILENAME
    rows = _rows(path)
    row = rows[0]
    sidecar = json.loads(Path(str(path) + ".source.json").read_text(encoding="utf-8"))

    assert len(rows) == sidecar["record_count"] == 1
    assert row["reported_value"] == "600"
    assert row["unit"] == "t"
    assert row["quality_class"] == "not_applicable_announced_plan_not_measurement"
    assert row["activation_state"] == "reference_only"
    assert row["publication_date"] == ""
    assert row["event_date_context"] == "2025-11-07"
    assert "wet/dry basis" in row["measurement_basis"]
    assert "completion" in row["limitations"]
    assert "not evidence" in row["limitations"]
    assert sidecar["calculation_connected"] is False
    assert sidecar["runtime_parameter_mapping"] is None
    assert len(sidecar["source_urls"]) == 3


def test_600_t_announcement_is_fair_registered_and_checksummed():
    path = GROUP / FILENAME
    sources = _rows(GROUP / "source_register.csv")
    manifests = _rows(GROUP / "dataset_manifest.csv")
    audit = ROOT / "Greenhub" / "data" / "global_audit_package"
    global_source = next(row for row in _rows(audit / "global_source_register.csv") if row["dataset_path"] == REL)
    manifest = next(row for row in _rows(audit / "global_dataset_manifest.csv") if row["dataset_path"] == REL)
    readiness = next(row for row in _rows(audit / "global_dataset_readiness.csv") if row["dataset_path"] == REL)
    checksum = next(row for row in _rows(audit / "source_dataset_checksums.csv") if row["dataset_path"] == REL)

    assert any(row["source_id"] == "SRC-GHZH-AUTUMN-ROADGRASS-600T-ANNOUNCEMENT-2025" for row in sources)
    assert any(row["file_name"] == FILENAME and row["row_count"] == "1" for row in manifests)
    assert global_source["year"] == "2025"
    assert manifest["detected_readiness"] == "D3"
    assert readiness["numeric_rows"] == "1"
    assert readiness["unsourced_numeric_rows"] == "0"
    assert checksum["sha256"] == hashlib.sha256(path.read_bytes()).hexdigest()
