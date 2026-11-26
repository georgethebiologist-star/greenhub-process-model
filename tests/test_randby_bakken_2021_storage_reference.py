import csv
import hashlib
import json
from collections import defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "Greenhub" / "data"
FOLDER = DATA / "storage"
CSV_PATH = FOLDER / "grass_silage_storage_system_losses_randby_bakken_2021_reference.csv"
SOURCE_ID = "SRC-RANDBY-BAKKEN-GRASS-SILAGE-2021"


def _rows(path: Path):
    with path.open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def test_randby_bakken_storage_extract_is_traceable_and_reference_only():
    rows = _rows(CSV_PATH)
    assert len(rows) == 67
    assert len({row["observation_id"] for row in rows}) == len(rows)
    assert {row["source_id"] for row in rows} == {SOURCE_ID}
    assert {row["evidence_class"] for row in rows} == {"B_measured_literature"}
    assert {row["quality_class"] for row in rows} == {"B"}
    assert {row["activation_state"] for row in rows} == {"reference_only"}

    table3 = [row for row in rows if row["table"] == "3"]
    assert len(table3) == 60
    assert {row["replicate_count"] for row in table3 if row["silo_type"] == "bunker"} == {"3"}
    assert {row["replicate_count"] for row in table3 if row["silo_type"] != "bunker"} == {"9"}
    assert {row["storage_duration_days"] for row in table3} == {""}

    # Source Table 3 closes the reported crop/crop-DM disposition within
    # rounding: offered silage + wasted silage + invisible losses = 1000.
    totals = defaultdict(float)
    by_treatment = {}
    for row in table3:
        key = (row["observation_id"].rsplit("-", 2)[0], row["basis"])
        totals[key] += float(row["value"])
        by_treatment[(row["silo_type"], row["additive"], row["sealing"], row["measurement"], row["basis"])] = row
    assert len(totals) == 20
    assert all(abs(total - 1000) <= 1.0 for total in totals.values())

    bunker_control = by_treatment[("bunker", "untreated", "not_applicable", "invisible_losses", "initial_crop_dry_matter")]
    bale_control = by_treatment[("round_bale", "untreated", "immediate", "invisible_losses", "initial_crop_dry_matter")]
    assert float(bunker_control["value"]) == 146
    assert float(bale_control["value"]) == 68.6
    assert bunker_control["unit"] == "g/kg crop DM"
    assert bunker_control["standard_error"] == "27.3"

    metadata = json.loads(CSV_PATH.with_suffix(CSV_PATH.suffix + ".source.json").read_text(encoding="utf-8"))
    assert metadata["persistent_identifier"] == "doi:10.1016/j.anifeedsci.2021.114868"
    assert "CC BY 4.0" in metadata["license"]
    assert metadata["experiment_year"] == 2017
    assert any("cultivated norwegian grass-clover" in item.lower() for item in metadata["limitations"])
    assert any("estimated correction" in item for item in metadata["limitations"])

    local_source = next(row for row in _rows(FOLDER / "source_register.csv") if row["source_id"] == SOURCE_ID)
    assert local_source["doi_or_stable_identifier"] == "10.1016/j.anifeedsci.2021.114868"
    manifest = {row["filename"]: row for row in _rows(FOLDER / "dataset_manifest.csv")}
    assert manifest[CSV_PATH.name]["row_count"] == "67"
    assert manifest[CSV_PATH.name]["integration_status"] == "traceable_reference_only_not_runtime_eligible"

    relative = "storage/" + CSV_PATH.name
    checksum = hashlib.sha256(CSV_PATH.read_bytes()).hexdigest()
    checksum_row = next(row for row in _rows(DATA / "global_audit_package/source_dataset_checksums.csv") if row["dataset_path"] == relative)
    assert checksum_row["sha256"] == checksum
    activation = next(row for row in _rows(DATA / "global_audit_package/dataset_activation_matrix.csv") if row["dataset_path"] == relative)
    assert activation["integration_eligibility"] == "reference_only"
    assert activation["default_eligibility"] == "False"
    assert activation["calculation_connected"] == "False"
    assert activation["active"] == "False"

    catalog = json.loads((DATA / "fair_input_catalog/master_input_catalog.json").read_text(encoding="utf-8"))
    asset = next(row for row in catalog["assets"] if row["relative_path"].endswith(CSV_PATH.name))
    assert asset["source_metadata_status"] == "linked_to_source_register"
    assert "10.1016/j.anifeedsci.2021.114868" in asset["source_dois"]
    assert "CC BY 4.0" in asset["license_or_rights"]
