import csv
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "Greenhub" / "data" / "Pre-treatment" / "Feedstock"
FILE = "monbio_2023_flanders_roadside_grass_inventory_reference.csv"


def _rows(path):
    with path.open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def test_monbio_roadside_grass_values_are_reported_and_not_normalized():
    rows = _rows(DATA / FILE)
    assert len(rows) == 5
    assert {row["management_actor"] for row in rows} == {
        "Agentschap Wegen en Verkeer", "Municipalities", "De Vlaamse Waterweg",
        "Infrabel", "Reported roadside-grass subtotal",
    }
    total = next(row for row in rows if row["record_id"] == "MONBIO23-005")
    assert total["annual_dry_matter_tonnes"] == "72032"
    assert total["reported_area_ha"] == ""
    assert all(row["quality_class"] == "C" for row in rows)
    assert all(row["activation_state"] == "reference_only" for row in rows)
    assert all(row["limitations"] and row["reported_method_or_note"] for row in rows)
    assert "extrapolated" in rows[1]["reported_method_or_note"]
    assert "estimate" in rows[3]["underlying_data_period"]


def test_monbio_source_and_global_inventory_are_linked():
    source_id = "SRC-MONBIO2-FLANDERS-ROADSIDECUTTINGS-2023"
    local_sources = {row["source_id"] for row in _rows(DATA / "source_register.csv")}
    local_manifest = {row["file_name"] for row in _rows(DATA / "dataset_manifest.csv")}
    assert source_id in local_sources
    assert FILE in local_manifest

    audit = ROOT / "Greenhub" / "data" / "global_audit_package"
    global_sources = _rows(audit / "global_source_register.csv")
    global_manifest = _rows(audit / "global_dataset_manifest.csv")
    readiness = _rows(audit / "global_dataset_readiness.csv")
    target = f"Pre-treatment/Feedstock/{FILE}"
    assert any(row["dataset_path"] == target and row["source_id"] == source_id for row in global_sources)
    assert any(row["dataset_path"] == target and row["detected_readiness"] == "D3" for row in global_manifest)
    assert any(row["dataset_path"] == target and row["readiness"] == "D3" for row in readiness)
    fair_catalog = _rows(ROOT / "Greenhub" / "data" / "fair_input_catalog" / "master_input_catalog.csv")
    fair_row = next(row for row in fair_catalog if row["relative_path"] == f"Greenhub/data/{target}")
    assert source_id in fair_row["source_ids"]
    assert fair_row["source_metadata_status"] == "linked_to_source_register"
    assert fair_row["readiness"] == "reference_only"
