import csv
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "Greenhub" / "data" / "Bigas production + upgrade" / "Feed BMP"
CSV_PATH = DATA_DIR / "nyangau_2023_brown_juice_ensiling_ad_digestate_nutrient_reference.csv"
SOURCE_ID = "SRC-NYANGAU-2023-BJ-ENSILING-AD-NUTRIENT"


def _rows():
    with CSV_PATH.open(encoding="utf-8", newline="") as stream:
        return list(csv.DictReader(stream))


def test_nyangau_extract_has_complete_provenance_and_unique_long_form_keys():
    rows = _rows()
    assert len(rows) == 464
    assert len({row["record_id"] for row in rows}) == len(rows)
    assert all(row["source_id"] == SOURCE_ID for row in rows)
    assert all(row["activation_state"] == "reference_only" for row in rows)
    assert all(row["evidence_class"] == "B_measured_primary_literature" for row in rows)

    sidecar = json.loads(CSV_PATH.with_suffix(CSV_PATH.suffix + ".source.json").read_text(encoding="utf-8"))
    assert sidecar["persistent_identifier"] == "doi:10.1016/j.eti.2023.103248"
    assert sidecar["license"] == "CC BY 4.0, stated in the published article."
    assert sidecar["row_count"] == len(rows)
    assert sidecar["readiness"] == "D3"


def test_nyangau_table_values_preserve_bases_censoring_and_missingness():
    rows = _rows()
    by_key = {(row["table_id"], row["material"], row["metric"], row["condition"]): row for row in rows}

    bmp = by_key[("Table 3", "wheat straw", "batch_BMP", "Straw+BJlabsilage")]
    assert bmp["reported_mean"] == "329.9"
    assert bmp["reported_uncertainty"] == "3.4"
    assert bmp["uncertainty_type"] == "standard error when printed"
    assert bmp["reported_unit"] == "mL CH4/g VS"

    bdl = by_key[("Table 1", "StrawField", "citric_acid", "field-scale raw straw")]
    assert bdl["reported_mean"] == ""
    assert bdl["data_status"] == "below_detection_limit"

    unreported = by_key[("Table 1", "StrawField", "dry_matter_loss", "field-scale raw straw")]
    assert unreported["reported_mean"] == ""
    assert unreported["data_status"] == "not_reported_or_not_applicable"

    nutrient = by_key[("Table 4", "Co-dig CM2+Press cake", "soil_inorganic_nitrogen_concentration", "80 days after amendment")]
    assert nutrient["reported_mean"] == "139.3"
    assert nutrient["reported_uncertainty"] == "4.17"
    assert nutrient["reported_unit"] == "mg N/kg soil"
    assert "not a direct fertilizer-substitution factor" in nutrient["notes"]


def test_nyangau_registration_points_to_the_reference_extract_only():
    manifest = DATA_DIR / "dataset_manifest.csv"
    with manifest.open(encoding="utf-8-sig", newline="") as stream:
        rows = list(csv.DictReader(stream))
    record = next(row for row in rows if row["filename"] == CSV_PATH.name)
    assert record["row_count"] == "464"
    assert record["integration_status"] == "traceable_reference_only_not_runtime_eligible"

    for register_name in ("source_register.csv", "ad_source_register.csv"):
        with (DATA_DIR / register_name).open(encoding="utf-8-sig", newline="") as stream:
            sources = list(csv.DictReader(stream))
        source = next(row for row in sources if row["source_id"] == SOURCE_ID)
        assert source["doi_or_stable_id"] == "10.1016/j.eti.2023.103248"
