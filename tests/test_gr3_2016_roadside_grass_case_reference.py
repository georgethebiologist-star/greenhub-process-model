from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GROUP = ROOT / "Greenhub" / "data" / "Pre-treatment" / "Feedstock"
FILENAME = "gr3_2016_roadside_grass_biogas_cases_reference.csv"
REL = f"Pre-treatment/Feedstock/{FILENAME}"


def _read(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def test_gr3_case_extract_retains_phase_basis_and_case_status() -> None:
    path = GROUP / FILENAME
    rows = _read(path)
    sidecar = json.loads(Path(str(path) + ".source.json").read_text(encoding="utf-8"))
    assert len(rows) == sidecar["record_count"] == 16
    assert len({row["record_id"] for row in rows}) == 16
    assert {row["source_id"] for row in rows} == {"SRC-GR3-2016-ROADSIDEBIOMASS-CASES"}
    assert {row["quality_class"] for row in rows} == {"B"}
    assert {row["activation_state"] for row in rows} == {"reference_only"}
    assert sidecar["runtime_parameter_mapping"] is None
    assert sidecar["doi"] is None
    assert "No explicit open license" in sidecar["rights_status"]

    by_id = {row["record_id"]: row for row in rows}
    assert by_id["GR3-2016-NL-ANNUAL-FRESH-GRASS"]["reported_value"] == "1200"
    assert by_id["GR3-2016-NL-FRESH-YIELD-BASIS"]["reported_value"] == "7"
    assert by_id["GR3-2016-NL-BIOGAS-YIELD-RANGE"]["lower_value"] == "130"
    assert by_id["GR3-2016-NL-BIOGAS-YIELD-RANGE"]["upper_value"] == "185"
    assert "methane content" in by_id["GR3-2016-NL-BIOGAS-YIELD-RANGE"]["limitations"]
    assert by_id["GR3-2016-NL-WET-AD-PARTICLE-SIZE"]["reported_value"] == "<1"
    assert "checking" in by_id["GR3-2016-NL-WET-AD-PARTICLE-SIZE"]["limitations"]
    assert by_id["GR3-2016-BAC-HARVEST-SEASONALITY"]["reported_value"] == "frequent; year-round, mainly summer"
    assert by_id["GR3-2016-NL-PROFIT-SCENARIO"]["observation_status"] == "reported_case_calculation"
    assert "Definition of profit" in by_id["GR3-2016-NL-PROFIT-SCENARIO"]["limitations"]


def test_gr3_case_extract_is_registered_and_checksummed() -> None:
    source = next(row for row in _read(GROUP / "source_register.csv") if row["source_id"] == "SRC-GR3-2016-ROADSIDEBIOMASS-CASES")
    manifest = next(row for row in _read(GROUP / "dataset_manifest.csv") if row["file_name"] == FILENAME)
    audit = ROOT / "Greenhub" / "data" / "global_audit_package"
    global_source = next(row for row in _read(audit / "global_source_register.csv") if row["dataset_path"] == REL)
    readiness = next(row for row in _read(audit / "global_dataset_readiness.csv") if row["dataset_path"] == REL)
    checksum = next(row for row in _read(audit / "source_dataset_checksums.csv") if row["dataset_path"] == REL)
    assert source["year"] == "2016"
    assert global_source["source_id"] == "SRC-GR3-2016-ROADSIDEBIOMASS-CASES"
    assert manifest["integration_readiness"] == "traceable_reference_only_not_runtime_eligible"
    # Two records are qualitative seasonal timing; the remaining 14 report
    # numeric points, ranges, approximations or inequalities.
    assert readiness["numeric_rows"] == "14"
    assert readiness["unsourced_numeric_rows"] == "0"
    assert checksum["sha256"] == hashlib.sha256((GROUP / FILENAME).read_bytes()).hexdigest()

