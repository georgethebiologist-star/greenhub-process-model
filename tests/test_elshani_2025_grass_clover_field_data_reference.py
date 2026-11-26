import csv
import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PACKAGE = ROOT / "Greenhub" / "data" / "Pre-treatment" / "Feedstock" / "elshani_2025_grass_clover_field_data"
SOURCE_ID = "SRC-ELSHANI-2025-FIELD-DATA"


def read_rows(path):
    with path.open("r", encoding="utf-8-sig", newline="") as stream:
        return list(csv.DictReader(stream, delimiter=";"))


def test_cc0_field_dataset_is_preserved_with_checksums_and_scope_limits():
    sidecar = json.loads((PACKAGE / "dataset.source.json").read_text(encoding="utf-8"))
    assert sidecar["dataset_doi"] == "10.18710/F5Z8BR"
    assert sidecar["related_publication_doi"] == "10.1016/j.scitotenv.2025.180373"
    assert sidecar["license"].startswith("CC0 1.0")
    assert sidecar["source_file_md5"] == {
        "00_README_EnvImpactBiorefine.txt": "f9cb6d002ad1e2ee2879b62f9b19f073",
        "EnvImpactBiorefine_Data.csv": "cf0fcea3eaa2bac973e4548795fa9bdc",
        "EnvImpactBiorefine_Exp.csv": "03e967afa0c584bd7f877adcadcd9d68",
    }
    for filename, expected_md5 in sidecar["source_file_md5"].items():
        assert hashlib.md5((PACKAGE / filename).read_bytes()).hexdigest() == expected_md5
    assert sidecar["observations"]["observation_rows"] == 192
    assert "not define units for CP_* or clover_*" in sidecar["applicability_limit"]
    assert sidecar["activation_state"] == "reference_only"
    assert sidecar["readiness"] == "D3"


def test_field_observations_and_location_crosswalk_remain_source_coded():
    rows = read_rows(PACKAGE / "EnvImpactBiorefine_Data.csv")
    locations = read_rows(PACKAGE / "EnvImpactBiorefine_Exp.csv")
    assert len(rows) == 192
    assert len(locations) == 8
    assert {row["Exp_no"] for row in rows} == {row["Exp_no"] for row in locations}
    assert {row["N_rate"] for row in rows} == {"0", "8", "16", "24"}
    assert {row["Clover_mix"] for row in rows} == {"10", "20"}
    assert {row["No_cuts"] for row in rows} == {"3"}
    assert sum(row["Yield_cut1"] == "." for row in rows) == 0
    assert sum(row["CP_cut1"] == "." for row in rows) == 8
    assert sum(row["CP_cut3"] == "." for row in rows) == 16


def test_registration_is_reference_only_and_does_not_create_runtime_mapping():
    feedstock = ROOT / "Greenhub" / "data" / "Pre-treatment" / "Feedstock"
    with (feedstock / "source_register.csv").open("r", encoding="utf-8-sig", newline="") as stream:
        sources = list(csv.DictReader(stream))
    source = next(row for row in sources if row["source_id"] == SOURCE_ID)
    assert "not roadside" in source["quality_notes"]
    with (feedstock / "dataset_manifest.csv").open("r", encoding="utf-8-sig", newline="") as stream:
        manifest = list(csv.DictReader(stream))
    package_rows = [row for row in manifest if row["file_name"].startswith("elshani_2025_grass_clover_field_data/")]
    assert {row["row_count"] for row in package_rows} == {"192", "8"}
    assert all(row["integration_readiness"] == "reference_only_not_runtime_eligible" for row in package_rows)

    audit = ROOT / "Greenhub" / "data" / "global_audit_package"
    with (audit / "global_source_register.csv").open("r", encoding="utf-8-sig", newline="") as stream:
        global_sources = list(csv.DictReader(stream))
    linked_paths = {
        row["dataset_path"]
        for row in global_sources
        if row["source_id"] == SOURCE_ID
    }
    assert {
        "Pre-treatment/Feedstock/elshani_2025_grass_clover_field_data/EnvImpactBiorefine_Data.csv",
        "Pre-treatment/Feedstock/elshani_2025_grass_clover_field_data/EnvImpactBiorefine_Exp.csv",
        "Pre-treatment/Feedstock/elshani_2025_grass_clover_field_data/00_README_EnvImpactBiorefine.txt",
    } <= linked_paths
    with (audit / "source_dataset_checksums.csv").open("r", encoding="utf-8-sig", newline="") as stream:
        checksums = list(csv.DictReader(stream))
    assert any(
        row["dataset_path"] == "Pre-treatment/Feedstock/elshani_2025_grass_clover_field_data/00_README_EnvImpactBiorefine.txt"
        for row in checksums
    )
