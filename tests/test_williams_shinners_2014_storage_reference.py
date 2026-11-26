import csv
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "Greenhub" / "data" / "storage"
FILENAME = "williams_shinners_perennial_grass_anaerobic_storage_2014_reference.csv"
SOURCE_ID = "SRC-WILLIAMS-SHINNERS-PERENNIAL-GRASS-STORAGE-2014"


def _rows(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def test_williams_shinners_storage_extract_is_traceable_and_reference_only():
    path = DATA_DIR / FILENAME
    rows = _rows(path)
    metadata = json.loads(path.with_suffix(path.suffix + ".source.json").read_text(encoding="utf-8"))
    manifest = _rows(DATA_DIR / "dataset_manifest.csv")
    sources = _rows(DATA_DIR / "source_register.csv")

    assert len(rows) == 6
    assert len({row["record_id"] for row in rows}) == 6
    assert {row["source_id"] for row in rows} == {SOURCE_ID}
    assert {row["quality_class"] for row in rows} == {"B"}
    assert {row["activation_state"] for row in rows} == {"reference_only"}
    assert {row["storage_duration_days"] for row in rows if row["scientific_name"] == "Panicum virgatum"} == {"222"}
    assert {row["storage_duration_days"] for row in rows if row["scientific_name"] == "Phalaris arundinacea"} == {"230"}

    by_id = {row["record_id"]: row for row in rows}
    swg_high_control = by_id["WILL14-SWG-CTRL-HIGH"]
    assert swg_high_control["table1_anaerobic_dm_loss_g_per_kg_dm"] == "26"
    assert swg_high_control["table1_additional_aerobic_dm_loss_7d_g_per_kg_dm"] == "38"
    assert swg_high_control["table3_cellulose_recovery_fraction"] == "0.94"
    assert swg_high_control["table3_hemicellulose_recovery_fraction"] == "1.06"
    assert swg_high_control["table5_hdd_7d_shallow_degC_day"] == "77"
    assert swg_high_control["table1_aerobic_7d_loss_group"] == "b"

    rcg_control = by_id["WILL14-RCG-CTRL-LOW"]
    assert rcg_control["table1_dm_removed_g_per_kg_material"] == "530"
    assert rcg_control["table5_dm_at_aerobic_exposure_start_g_per_kg_material"] == "536"
    assert rcg_control["table5_replicate_n"] == "not_reported"
    assert metadata["persistent_identifier"] == "doi:10.1016/j.biombioe.2014.03.037"
    assert metadata["activation_state"] == "reference_only"
    assert any("sequential" in item and "not a separate aerobic-storage" in item for item in metadata["limitations"])
    assert any("one farm-scale silo bag per species" in item for item in metadata["limitations"])

    source = next(row for row in sources if row["source_id"] == SOURCE_ID)
    assert "Tables 1, 3 and 5" in source["quality_notes"]
    manifest_entry = next(row for row in manifest if row["filename"] == FILENAME)
    assert manifest_entry["row_count"] == "6"
    assert manifest_entry["integration_status"] == "traceable_reference_only_not_runtime_eligible"


def test_williams_shinners_source_is_linked_in_fair_catalog():
    catalog_path = ROOT / "Greenhub" / "data" / "fair_input_catalog" / "master_input_catalog.json"
    catalog = json.loads(catalog_path.read_text(encoding="utf-8"))
    asset = next(asset for asset in catalog["assets"] if Path(asset["relative_path"]).name == FILENAME)
    assert SOURCE_ID in asset["source_ids"].split(";")
    assert "10.1016/j.biombioe.2014.03.037" in asset["source_dois"]

