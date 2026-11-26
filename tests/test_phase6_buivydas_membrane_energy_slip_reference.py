import csv
import hashlib
import importlib.util
import json
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "Greenhub" / "data" / "Bigas production + upgrade" / "Membrane"
DATASET = DATA / "variable_methane_feed_membrane_upgrading_energy_slip_buivydas_2024_reference.csv"
SOURCE_ID = "BUIVYDAS-MEMBRANE-UPGRADING-2024"


def _rows(path):
    with path.open(encoding="utf-8-sig", newline="") as stream:
        return list(csv.DictReader(stream))


def test_measured_cases_preserve_units_deviations_and_recycle_control_context():
    rows = _rows(DATASET)
    assert len(rows) == 24
    assert len({row["record_id"] for row in rows}) == 24
    assert {row["source_id"] for row in rows} == {SOURCE_ID}
    assert {row["quality_class"] for row in rows} == {"B"}
    assert {row["activation_state"] for row in rows} == {"reference_only"}
    assert Counter(row["experiment_id"] for row in rows) == {
        "CM-50": 6, "CM-60": 6, "CM-70": 6, "CM-80": 6,
    }
    assert Counter(row["metric"] for row in rows) == {
        "upgrader_inlet_biogas_methane_vol_percent": 4,
        "upgrader_inlet_biogas_flow": 4,
        "upgrading_electricity_consumption_rate": 4,
        "biomethane_product_flow": 4,
        "biomethane_methane_vol_percent": 4,
        "methane_slip": 4,
    }
    by_id = {row["record_id"]: row for row in rows}
    assert by_id["BUIVYDAS24-CM-50-ELECTRICITY_CONSUMPTION_RATE"]["reported_value"] == "10.28"
    assert by_id["BUIVYDAS24-CM-80-BIOMETHANE_PRODUCT_FLOW"]["reported_value"] == "28.79"
    assert by_id["BUIVYDAS24-CM-70-METHANE_SLIP"]["reported_deviation"] == "0.02"
    assert "blended upgrader inlet" in by_id["BUIVYDAS24-CM-50-BLENDED_INLET_FLOW"]["stream"]
    assert "ambiguous" in by_id["BUIVYDAS24-CM-50-METHANE_SLIP"]["basis_or_denominator"]
    assert all(row["reported_deviation"] for row in rows)


def test_sidecar_registers_and_fair_catalog_keep_the_asset_reference_only():
    rows = _rows(DATASET)
    sidecar_path = DATASET.with_suffix(DATASET.suffix + ".source.json")
    metadata = json.loads(sidecar_path.read_text(encoding="utf-8"))
    assert metadata["doi"] == "10.3390/su16083323"
    assert metadata["license"] == "Creative Commons Attribution 4.0 International (CC BY 4.0), stated in the article."
    assert metadata["calculation_connected"] is False
    assert metadata["row_count"] == 24
    assert hashlib.sha256(DATASET.read_bytes()).hexdigest() == metadata["sha256_csv"]

    sources = {row["source_id"]: row for row in _rows(DATA / "source_register.csv")}
    manifest = {row["filename"]: row for row in _rows(DATA / "dataset_manifest.csv")}
    assert sources[SOURCE_ID]["doi_or_stable_identifier"] == "10.3390/su16083323"
    assert manifest[DATASET.name]["row_count"] == "24"

    script = ROOT / "scripts" / "build_lanko_2024_membrane_upgrading_reference.py"
    spec = importlib.util.spec_from_file_location("buivydas_membrane_reference_builder", script)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    assert rows == module.build_rows()

    catalog = _rows(ROOT / "Greenhub" / "data" / "fair_input_catalog" / "master_input_catalog.csv")
    asset = next(row for row in catalog if row["relative_path"].endswith(DATASET.name))
    assert asset["source_ids"] == SOURCE_ID
    assert "10.3390/su16083323" in asset["source_dois"]
    assert asset["source_metadata_status"] == "linked_to_source_register"
