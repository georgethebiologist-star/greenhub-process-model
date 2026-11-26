import csv
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "Greenhub" / "data" / "Pre-treatment" / "Feedstock"


def test_municipal_verge_records_are_traceable_and_reference_only():
    path = DATA / "municipal_verge_management_reference.csv"
    with path.open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))

    assert len(rows) == 11
    assert {row["source_id"] for row in rows} == {
        "SRC-NUENEN-GREENPLAN-2022",
        "SRC-LANSINGERLAND-MOWING-2026",
    }
    assert all(row["activation_state"] == "reference_only" for row in rows)
    assert all(row["source_location"] and row["limitations"] for row in rows)

    area_rows = [row for row in rows if row["area_value"]]
    assert len(area_rows) == 8
    assert all(row["area_unit"] == "m2" for row in area_rows)
    assert all(not row["first_cut_window"] for row in area_rows)

    schedule_rows = [row for row in rows if row["first_cut_window"]]
    assert len(schedule_rows) == 2
    assert all(not row["area_value"] for row in schedule_rows)
    assert any("weeks 24-26" in row["first_cut_window"] for row in schedule_rows)
    assert any("weeks 16-17" in row["first_cut_window"] for row in schedule_rows)


def test_municipal_verge_sources_are_registered_and_manifested():
    with (DATA / "source_register.csv").open(encoding="utf-8", newline="") as handle:
        source_ids = {row["source_id"] for row in csv.DictReader(handle)}
    with (DATA / "dataset_manifest.csv").open(encoding="utf-8", newline="") as handle:
        filenames = {row["file_name"] for row in csv.DictReader(handle)}

    assert {"SRC-NUENEN-GREENPLAN-2022", "SRC-LANSINGERLAND-MOWING-2026"} <= source_ids
    assert "municipal_verge_management_reference.csv" in filenames

    audit = ROOT / "Greenhub" / "data" / "global_audit_package"
    with (audit / "global_source_register.csv").open(encoding="utf-8-sig", newline="") as handle:
        global_sources = list(csv.DictReader(handle))
    with (audit / "global_dataset_manifest.csv").open(encoding="utf-8-sig", newline="") as handle:
        global_manifest = list(csv.DictReader(handle))
    with (audit / "global_dataset_readiness.csv").open(encoding="utf-8-sig", newline="") as handle:
        readiness = list(csv.DictReader(handle))

    assert {"SRC-NUENEN-GREENPLAN-2022", "SRC-LANSINGERLAND-MOWING-2026"} <= {
        row["source_id"] for row in global_sources
    }
    target = "Pre-treatment/Feedstock/municipal_verge_management_reference.csv"
    assert any(row["dataset_path"] == target for row in global_manifest)
    assert any(row["dataset_path"] == target and row["readiness"] == "D3" for row in readiness)
