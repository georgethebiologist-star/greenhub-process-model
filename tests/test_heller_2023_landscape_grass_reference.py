from __future__ import annotations

import csv
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "Greenhub" / "data" / "Pre-treatment" / "Mechanical"
SOURCE_ID = "S13_HELLER_2023_LANDSCAPE_GRASS"
DOI = "10.3390/en16248091"


def _rows(filename: str) -> list[dict[str, str]]:
    with (DATA_DIR / filename).open("r", encoding="utf-8-sig", newline="") as stream:
        return list(csv.DictReader(stream))


def test_heller_landscape_grass_extracts_are_traceable_reference_only() -> None:
    files = {
        "composition": "landscape_management_grass_heller_2023_composition_reference.csv",
        "harvest": "landscape_management_grass_heller_2023_harvest_pretreatment_reference.csv",
        "bmp": "landscape_management_grass_heller_2023_bmp_kinetics_reference.csv",
    }
    expected_counts = {"composition": 4, "harvest": 5, "bmp": 5}
    all_ids: set[str] = set()

    for group, filename in files.items():
        rows = _rows(filename)
        metadata = json.loads((DATA_DIR / f"{filename}.source.json").read_text(encoding="utf-8"))
        assert len(rows) == expected_counts[group]
        assert metadata["source_id"] == SOURCE_ID
        assert metadata["doi"] == DOI
        assert metadata["quality_class"] == "B"
        assert metadata["activation_state"] == "reference_only"
        assert metadata["calculation_connected"] is False
        assert metadata["runtime_parameter_mapping"] is None
        for row in rows:
            assert row["source_id"] == SOURCE_ID
            assert row["doi"] == DOI
            assert row["quality_class"] == "B"
            assert row["activation_state"] == "reference_only"
            location = row["source_location"]
            assert location
            if group == "composition":
                assert location.startswith("Table 1")
            elif group == "harvest":
                assert "Table 2" in location or "Results" in location
            else:
                assert location.startswith(("Table 3", "Table 4", "Results"))
            assert row["record_id"] not in all_ids
            all_ids.add(row["record_id"])

    composition = {row["treatment_variant"]: row for row in _rows(files["composition"])}
    assert composition["UT"]["ts_pct_fm"] == "26.9"
    assert composition["UT"]["vs_pct_ts"] == "89.3"
    assert composition["BM"]["sugars_g_kg_vs"] == "27.0"

    harvest = {row["record_id"]: row for row in _rows(files["harvest"])}
    assert harvest["HLR23-FIRST-CUT-YIELD"]["first_cut_volatile_solids_yield_t_vs_ha"] == "3.10"
    assert harvest["HLR23-HARV-CFG"]["pretreatment_energy_kwh_t_fm"] == "7.79"
    assert harvest["HLR23-HARV-AG"]["reported_incremental_energy_balance_kwh_t_vs"] == "-18.3"

    bmp = {row["treatment_variant"]: row for row in _rows(files["bmp"])}
    assert bmp["UT"]["smy_l_ch4_kg_vs_mean"] == "263.9"
    assert bmp["BM"]["smy_l_ch4_kg_vs_mean"] == "279.1"
    assert bmp["AG"]["gompertz_rm_l_ch4_kg_vs_day_mean"] == "26.2"


def test_heller_datasets_are_discoverable_in_fair_catalog() -> None:
    catalog_path = ROOT / "Greenhub" / "data" / "fair_input_catalog" / "master_input_catalog.json"
    catalog = json.loads(catalog_path.read_text(encoding="utf-8"))
    assets = {Path(asset["relative_path"]).name: asset for asset in catalog["assets"]}
    for filename in (
        "landscape_management_grass_heller_2023_composition_reference.csv",
        "landscape_management_grass_heller_2023_harvest_pretreatment_reference.csv",
        "landscape_management_grass_heller_2023_bmp_kinetics_reference.csv",
    ):
        asset = assets[filename]
        assert SOURCE_ID in asset["source_ids"].split(";")
        assert DOI in asset["source_dois"].split(";")
        assert asset["source_metadata_status"] in {
            "linked_to_source_register",
            "linked_to_local_source_record",
        }
