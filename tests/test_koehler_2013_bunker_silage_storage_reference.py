import csv
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "Greenhub" / "data" / "storage"
FILE = "koehler_2013_farm_scale_grass_bunker_silo_storage_reference.csv"


def _rows(path):
    with path.open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def test_koehler_summary_preserves_scope_and_negative_measurement_artifact():
    rows = _rows(DATA / FILE)
    assert len(rows) == 13
    by_id = {row["record_id"]: row for row in rows}
    assert by_id["KOH13-DMLOSS-MEAN"]["reported_value"] == "9"
    assert by_id["KOH13-DMLOSS-MIN"]["reported_value"] == "-2"
    assert "measurement/accounting error" in by_id["KOH13-DMLOSS-MIN"]["limitations"]
    assert "including feed-out" in by_id["KOH13-DMLOSS-MEAN"]["measurement_scope"]
    assert by_id["KOH13-CORR-FEEDOUT"]["sample_n"] == "19 paired observations"
    assert by_id["KOH13-CORR-FEEDOUT"]["unit"] == "dimensionless"
    assert all(row["quality_class"] == "B" for row in rows)
    assert all(row["activation_state"] == "reference_only" for row in rows)
    assert all(row["source_location"] and row["limitations"] for row in rows)


def test_koehler_source_and_global_inventory_are_linked():
    source_id = "SRC-KOEHLER-2013-GRASS-BUNKER-SILO"
    local_sources = {row["source_id"] for row in _rows(DATA / "source_register.csv")}
    local_manifest = {row["filename"] for row in _rows(DATA / "dataset_manifest.csv")}
    assert source_id in local_sources
    assert FILE in local_manifest

    audit = ROOT / "Greenhub" / "data" / "global_audit_package"
    global_sources = _rows(audit / "global_source_register.csv")
    global_manifest = _rows(audit / "global_dataset_manifest.csv")
    readiness = _rows(audit / "global_dataset_readiness.csv")
    target = f"storage/{FILE}"
    assert any(row["dataset_path"] == target and row["source_id"] == source_id for row in global_sources)
    assert any(row["dataset_path"] == target and row["detected_readiness"] == "D3" for row in global_manifest)
    assert any(row["dataset_path"] == target and row["readiness"] == "D3" for row in readiness)
    fair_catalog = _rows(ROOT / "Greenhub" / "data" / "fair_input_catalog" / "master_input_catalog.csv")
    fair_row = next(row for row in fair_catalog if row["relative_path"] == f"Greenhub/data/{target}")
    assert source_id in fair_row["source_ids"]
    assert fair_row["source_metadata_status"] == "linked_to_source_register"
    assert fair_row["readiness"] == "reference_only"
