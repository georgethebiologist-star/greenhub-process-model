from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
GROUP = ROOT / "Greenhub" / "data" / "Pre-treatment" / "Feedstock"
FILENAME = "rejuice_wp5_roadside_grass_seasonality_and_ensiled_juice_reference.csv"
REL = f"Pre-treatment/Feedstock/{FILENAME}"


def _rows(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as stream:
        return list(csv.DictReader(stream))


def test_rejuice_calendar_extract_preserves_limits_and_nonactivation():
    path = GROUP / FILENAME
    rows = _rows(path)
    sidecar = json.loads(Path(str(path) + ".source.json").read_text(encoding="utf-8"))
    by_id = {row["record_id"]: row for row in rows}

    assert len(rows) == sidecar["record_count"] == 4
    assert len(by_id) == 4
    assert {row["source_id"] for row in rows} == {"SRC-REJUICE-WP5-SEASONAL-CALENDAR-DRAFT-2025"}
    assert {row["activation_state"] for row in rows} == {"reference_only"}
    assert by_id["REJUICE25-BERMGRAS-AVAILABILITY-WINDOW"]["reported_value"] == "May through November; not constant"
    assert by_id["REJUICE25-BERMGRAS-PEAK-WINDOWS"]["reported_value"] == "Mid-June to mid-July; mid-September to mid-October"
    juice = by_id["REJUICE25-ENSILED-GRASS-JUICE-FRACTION"]
    assert juice["reported_value"] == "approximately 40"
    assert "basis unspecified" in juice["unit"]
    assert "do not use" in juice["limitations"].lower()
    assert sidecar["calculation_connected"] is False
    assert sidecar["runtime_parameter_mapping"] is None
    assert "monthly tonnage shares" in sidecar["limitations"][1]
    assert "RVO (2014)" in sidecar["important_deduplication"]


def test_rejuice_calendar_extract_is_registered_and_checksummed():
    path = GROUP / FILENAME
    audit = ROOT / "Greenhub" / "data" / "global_audit_package"
    local_source = _rows(GROUP / "source_register.csv")
    local_manifest = _rows(GROUP / "dataset_manifest.csv")
    global_source = next(row for row in _rows(audit / "global_source_register.csv") if row["dataset_path"] == REL)
    manifest = next(row for row in _rows(audit / "global_dataset_manifest.csv") if row["dataset_path"] == REL)
    readiness = next(row for row in _rows(audit / "global_dataset_readiness.csv") if row["dataset_path"] == REL)
    checksum = next(row for row in _rows(audit / "source_dataset_checksums.csv") if row["dataset_path"] == REL)

    assert any(row["source_id"] == "SRC-REJUICE-WP5-SEASONAL-CALENDAR-DRAFT-2025" for row in local_source)
    assert any(row["file_name"] == FILENAME and row["row_count"] == "4" for row in local_manifest)
    assert global_source["year"] == "2025"
    assert manifest["detected_readiness"] == "D3"
    assert readiness["numeric_rows"] == "1"
    assert readiness["unsourced_numeric_rows"] == "0"
    assert checksum["sha256"] == hashlib.sha256(path.read_bytes()).hexdigest()
