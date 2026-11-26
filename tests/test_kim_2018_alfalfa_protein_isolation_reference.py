import csv
import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "Greenhub/data/Pre-treatment/Thermal_Enzymatic"
DATA_PATH = DATA_DIR / "alfalfa_enzyme_assisted_protein_isolation_2018_reference.csv"
SIDECAR_PATH = Path(str(DATA_PATH) + ".source.json")


def _rows(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as stream:
        return list(csv.DictReader(stream))


def _one(rows: list[dict[str, str]], record_id: str) -> dict[str, str]:
    matches = [row for row in rows if row["record_id"] == record_id]
    assert len(matches) == 1
    return matches[0]


def test_kim_2018_values_preserve_recovery_gap_and_reference_only_status():
    rows = _rows(DATA_PATH)
    sidecar = json.loads(SIDECAR_PATH.read_text(encoding="utf-8"))

    assert len(rows) == 43
    assert sum(bool(row["value"]) or bool(row["value_low"]) or bool(row["value_high"]) for row in rows) == 42
    assert len({row["record_id"] for row in rows}) == len(rows)
    assert all(row["source_id"] == "SRC-ENZ-003" for row in rows)
    assert all(row["source_url"] == "https://alfalfa.org/pdf/USAFRI/Final%20Reports/2018/18Kim.pdf" for row in rows)
    assert all(row["exact_source_location"] for row in rows)
    assert all(row["quality_class"] == "B" for row in rows)
    assert all(row["transferability"].endswith("not_roadside_or_greenhub") for row in rows)

    solubilized = _one(rows, "KIM18-MB-13")
    final_yield = _one(rows, "KIM18-MB-15")
    closure = _one(rows, "KIM18-MB-16")
    assert solubilized["value"] == "62.8"
    assert final_yield["value"] == "7"
    assert closure["value"] == "110"
    assert "double counted" in closure["notes"]

    dry_control = _one(rows, "KIM18-DRY-01")
    fresh_control = _one(rows, "KIM18-DRY-02")
    fresh_dry_ratio = _one(rows, "KIM18-DRY-03")
    assert dry_control["value"] == "41.0"
    assert fresh_control["value"] == "46.8"
    assert fresh_dry_ratio["value"] == "1.6"
    assert "not a wet-leaf extraction" in fresh_control["operating_conditions"]

    source_derived = _one(rows, "KIM18-MB-03")
    assert source_derived["record_type"] == "reported-derived"
    assert "not a directly isolated/dried measurement" in source_derived["notes"]

    qualitative = _one(rows, "KIM18-SCR-07")
    assert qualitative["value"] == ""
    assert qualitative["record_type"] == "qualitative-reported"

    assert sidecar["record_count"] == len(rows)
    assert sidecar["sha256"] == hashlib.sha256(DATA_PATH.read_bytes()).hexdigest()
    assert not sidecar["doi"]
    assert "no explicit reuse license" in sidecar["license"].lower()
    assert "Graph-only point values were not digitized" in sidecar["data_structure"]
    assert "no storage duration" in sidecar["phase_coverage"]["2"]
    assert "62.8% solubilization but only 7% final precipitated protein" in sidecar["applicability_limitations"][3]

    activation = [
        row for row in _rows(ROOT / "Greenhub/data/global_audit_package/dataset_activation_matrix.csv")
        if row["dataset_path"] == "Pre-treatment/Thermal_Enzymatic/alfalfa_enzyme_assisted_protein_isolation_2018_reference.csv"
    ]
    assert len(activation) == 1
    assert activation[0]["integration_eligibility"] == "reference_only"
    assert activation[0]["default_eligibility"].lower() == "false"
    assert activation[0]["active"].lower() == "false"

    source = [row for row in _rows(DATA_DIR / "source_register.csv") if row["source_id"] == "SRC-ENZ-003"]
    assert len(source) == 1
    assert source[0]["url"] == sidecar["source_url"]
    manifest = [row for row in _rows(DATA_DIR / "dataset_manifest.csv") if row["filename"] == DATA_PATH.name]
    assert len(manifest) == 1
    assert manifest[0]["primary_key"] == "record_id"
    validation = [row for row in _rows(DATA_DIR / "validation_report.csv") if row["filename"] == DATA_PATH.name]
    assert len(validation) == 1
    assert validation[0]["unique_nonblank_primary_keys"] == "pass"
    assert validation[0]["populated_numeric_traceability"] == "pass"
