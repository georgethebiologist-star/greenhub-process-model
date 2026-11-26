import csv
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "Greenhub/data/Resource recovery/Phosphorus_Recovery/fe_modified_biochar_phosphate_isotherm_bioden_reference.csv"


def test_bioden_phosphate_isotherm_preserves_conditions_and_separates_real_digestate():
    with DATA.open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    metadata = json.loads(DATA.with_suffix(".source.json").read_text(encoding="utf-8"))
    with (DATA.parent / "dataset_manifest.csv").open(encoding="utf-8-sig", newline="") as handle:
        manifest = list(csv.DictReader(handle))
    with (ROOT / "Greenhub/data/fair_input_catalog/master_input_catalog.csv").open(encoding="utf-8-sig", newline="") as handle:
        catalog = list(csv.DictReader(handle))

    assert len(rows) == 9
    assert len({row["observation_id"] for row in rows}) == 9
    assert {row["matrix"] for row in rows} == {"Synthetic phosphate solution"}
    assert {row["pH"] for row in rows} == {"7"}
    assert {row["contact_time_h"] for row in rows} == {"24"}
    assert [float(row["initial_phosphate_concentration_mg_P_L"]) for row in rows] == [10, 20, 50, 100, 150, 200, 500, 700, 1000]
    assert [float(row["reported_adsorption_capacity_mg_P_g_biochar"]) for row in rows] == [2.4, 4, 6.2, 7.9, 10, 12.2, 17.2, 23.1, 27.2]
    assert all(row["source_id"] == "BIODEN_T3.2_BIOCHAR_2024" for row in rows)
    assert all(row["quality_class"] == "B" and row["activation_state"] == "reference_only" for row in rows)
    assert metadata["synthetic_isotherm_conditions"]["solution_volume_ml"] == 50
    assert metadata["separate_real_digestate_test"]["initial_phosphate_as_P_mg_L"] == 230
    assert "separate text-level maximum" in metadata["limitations"][1]
    assert metadata["license_status"].startswith("No explicit reuse license identified")
    assert any(row["filename"] == DATA.name and row["row_count"] == "9" for row in manifest)
    asset = next(row for row in catalog if row["relative_path"].endswith(DATA.name))
    assert asset["source_ids"] == "BIODEN_T3.2_BIOCHAR_2024"
    assert asset["source_metadata_status"] == "linked_to_source_register"
