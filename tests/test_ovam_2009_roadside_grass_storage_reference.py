from __future__ import annotations

import csv
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE_ID = "SRC-OVAM-BDB-2009-ROADGRASS"
REPORT_URL = "https://www.bdb.be/files/rap200901.pdf"
STORAGE_DIR = ROOT / "Greenhub" / "data" / "storage"
BMP_DIR = ROOT / "Greenhub" / "data" / "Bigas production + upgrade" / "Feed BMP"


def _rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as stream:
        return list(csv.DictReader(stream))


def test_ovam_silo_final_states_preserve_basis_and_nonactivation() -> None:
    filename = "roadside_grass_ensiling_quality_ovam_2009_reference.csv"
    path = STORAGE_DIR / filename
    rows = _rows(path)
    metadata = json.loads(path.with_suffix(".csv.source.json").read_text(encoding="utf-8"))
    manifest = _rows(STORAGE_DIR / "dataset_manifest.csv")
    sources = _rows(STORAGE_DIR / "source_register.csv")

    assert len(rows) == metadata["rows"] == 7
    assert len({row["record_id"] for row in rows}) == 7
    assert all(row["source_id"] == SOURCE_ID for row in rows)
    assert all(row["activation_state"] == "reference_only" for row in rows)
    assert all(row["quality_class"] == "B" for row in rows)
    assert all(row["storage_duration_weeks"] == "10" for row in rows)
    assert metadata["persistent_identifier"] is None
    assert metadata["calculation_connected"] is False
    assert metadata["runtime_parameter_mapping"] is None
    assert "cannot be quantified" in " ".join(metadata["major_limitations"])

    grass_only = next(row for row in rows if row["record_id"] == "OVAM09-SILO-GRASS")
    assert grass_only["dry_matter_pct_fm"] == "35.6"
    assert grass_only["measured_ph"] == "5.5"
    assert grass_only["stable_silage_ph_criterion"] == "4.6"
    assert sum(row["co_stream"] == "none" for row in rows) == 1
    assert any(row["stable_silage_ph_criterion"] == "4.7-4.8" for row in rows)

    entry = next(row for row in manifest if row["filename"] == filename)
    assert entry["row_count"] == "7"
    assert entry["integration_status"] == "traceable_reference_only_not_runtime_eligible"
    assert any(row["source_id"] == SOURCE_ID for row in sources)


def test_ovam_storage_related_bmp_keeps_methane_and_biogas_distinct() -> None:
    filename = "roadside_grass_storage_bmp_ovam_2009_reference.csv"
    path = BMP_DIR / filename
    rows = _rows(path)
    metadata = json.loads(path.with_suffix(".csv.source.json").read_text(encoding="utf-8"))
    manifest = _rows(BMP_DIR / "dataset_manifest.csv")
    sources = _rows(BMP_DIR / "source_register.csv")

    assert len(rows) == metadata["rows"] == 9
    assert len({row["record_id"] for row in rows}) == 9
    assert all(row["source_id"] == SOURCE_ID for row in rows)
    assert all(row["activation_state"] == "reference_only" for row in rows)
    assert all(row["quality_class"] == "B" for row in rows)
    assert metadata["calculation_connected"] is False

    by_id = {row["record_id"]: row for row in rows}
    assert by_id["OVAM09-LEENK-MES-FLAIL-17"]["biogas_yield_value"] == "114.41"
    assert by_id["OVAM09-LEENK-MES-FLAIL-17"]["biogas_yield_basis"] == "volatile solids"
    assert by_id["OVAM09-LEENK-MES-FLAIL-17"]["methane_fraction_pct"] == "66.7"
    assert by_id["OVAM09-LEENK-THERM-FLAIL-FRESH"]["methane_fraction_pct"] == ""
    assert by_id["OVAM09-SILO-MONO-BMP"]["biogas_yield_value"] == "83.3"
    assert by_id["OVAM09-SILO-MONO-BMP"]["biogas_yield_basis"].startswith("sample-added")
    assert by_id["OVAM09-SILO-MONO-BMP"]["methane_fraction_pct"] == ""

    entry = next(row for row in manifest if row["filename"] == filename)
    assert entry["row_count"] == "9"
    assert any(row["source_id"] == SOURCE_ID for row in sources)


def test_ovam_datasets_are_indexed_with_source_linkage() -> None:
    catalog_path = ROOT / "Greenhub" / "data" / "fair_input_catalog" / "master_input_catalog.json"
    catalog = json.loads(catalog_path.read_text(encoding="utf-8"))
    assets = {Path(asset["relative_path"]).name: asset for asset in catalog["assets"]}
    for filename in (
        "roadside_grass_ensiling_quality_ovam_2009_reference.csv",
        "roadside_grass_storage_bmp_ovam_2009_reference.csv",
        "ravels_roadside_grass_collection_conditions_ovam_2009_reference.csv",
    ):
        asset = assets[filename]
        assert SOURCE_ID in asset["source_ids"].split(";")
        assert REPORT_URL in asset["source_urls"]
        assert asset["source_metadata_status"] in {
            "linked_to_source_register",
            "linked_to_local_source_record",
        }


def test_ovam_collection_observation_is_not_an_annual_supply_estimate() -> None:
    data_dir = ROOT / "Greenhub" / "data" / "Pre-treatment" / "Feedstock"
    filename = "ravels_roadside_grass_collection_conditions_ovam_2009_reference.csv"
    path = data_dir / filename
    rows = _rows(path)
    metadata = json.loads(path.with_suffix(".csv.source.json").read_text(encoding="utf-8"))
    manifest = _rows(data_dir / "dataset_manifest.csv")
    sources = _rows(data_dir / "source_register.csv")

    assert len(rows) == metadata["rows"] == 1
    row = rows[0]
    assert row["source_id"] == SOURCE_ID
    assert row["loads_delivered_n"] == "4"
    assert row["reported_mass_per_load_value"] == "25"
    assert "little under" in row["reported_mass_qualifier"]
    assert row["maximum_interim_storage_days"] == "3"
    assert row["activation_state"] == "reference_only"
    assert metadata["calculation_connected"] is False
    assert metadata["persistent_identifier"] is None
    assert any(item["file_name"] == filename and item["row_count"] == "1" for item in manifest)
    assert any(item["source_id"] == SOURCE_ID for item in sources)
