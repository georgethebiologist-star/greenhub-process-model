import csv
import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
FOLDER = ROOT / "Greenhub" / "data" / "Bigas production + upgrade" / "Feed BMP"
RVO_FILE = "rvo_2014_grass_supply_storage_chain_cost_reference.csv"
VGNG_FILE = "van_gras_naar_gas_2025_regional_feed_quality_tea_reference.csv"


def _rows(path: Path):
    with path.open(encoding="utf-8-sig", newline="") as stream:
        return list(csv.DictReader(stream))


def _by_id(rows):
    assert len({row["record_id"] for row in rows}) == len(rows)
    return {row["record_id"]: row for row in rows}


def test_rvo_extract_preserves_supply_bases_and_quarantines_inconsistencies():
    rows = _rows(FOLDER / RVO_FILE)
    metadata = json.loads((FOLDER / "rvo_2014_grass_supply_storage_chain_cost_reference.source.json").read_text(encoding="utf-8"))
    records = _by_id(rows)
    assert len(rows) == metadata["record_count"]
    assert metadata["doi"] is None
    assert metadata["calculation_connected"] is False
    assert {row["source_id"] for row in rows} == {"SRC-RVO-BRINKMANN-GRASS-2014"}
    assert {row["activation_state"] for row in rows} == {"reference_only"}

    assert records["RVO14-PROCEDE-VERGE-DM"]["value_numeric"] == "240000"
    assert records["RVO14-PROCEDE-VERGE-FRESH-LOW"]["lower_bound"] == "800000"
    assert records["RVO14-PROCEDE-VERGE-FRESH-HIGH"]["upper_bound"] == "1200000"
    assert "not a measured or contracted supply" in records["RVO14-PROCEDE-VERGE-DM"]["limitations"]
    waterway_dm = records["RVO14-PROCEDE-WATERWAY-DM"]
    assert waterway_dm["value_numeric"] == "350"
    assert waterway_dm["validation_status"] == "source_unit_scale_anomaly_unresolved"
    assert "do not infer 350 kton" in waterway_dm["limitations"]

    good = records["RVO14-STORAGE-POTENTIAL-LOSS-GOOD"]
    assert good["unit"] == "% initial biogas potential"
    assert "not fresh-mass or dry-matter" in good["limitations"]
    assert records["RVO14-SDE-GRASS-PRICE-50"]["lower_bound"] == "-8"
    assert records["RVO14-SDE-GRASS-PRICE-150"]["upper_bound"] == "14"

    conflicting = [records["RVO14-JANSEN-GAS-30DM-EXAMPLE-A"], records["RVO14-JANSEN-GAS-30DM-EXAMPLE-B"]]
    assert {row["value_numeric"] for row in conflicting} == {"90", "120"}
    assert all(row["validation_status"] == "source_internal_contradiction_quarantined" for row in conflicting)


def test_vgng_extract_keeps_regional_estimates_and_table4_mismatch_reference_only():
    rows = _rows(FOLDER / VGNG_FILE)
    metadata = json.loads((FOLDER / "van_gras_naar_gas_2025_regional_feed_quality_tea_reference.source.json").read_text(encoding="utf-8"))
    records = _by_id(rows)
    assert len(rows) == metadata["record_count"]
    assert metadata["doi"] is None
    assert metadata["calculation_connected"] is False
    assert {row["source_id"] for row in rows} == {"SRC-VGNG-INTERREG-2025"}
    assert {row["activation_state"] for row in rows} == {"reference_only"}

    assert records["VGNG25-T2-VERGE-NORTH"]["value_numeric"] == "274"
    assert "no accessible fraction or delivery quantity" in records["VGNG25-T2-VERGE-NORTH"]["limitations"]
    assert records["VGNG25-FACTOR-THEORETICAL-METHANE"]["value_numeric"] == "580"
    gas_rows = [row for row in rows if row["metric"] == "reported_total_green_gas_potential"]
    assert len(gas_rows) == 4
    assert {row["validation_status"] for row in gas_rows} == {"table_potential_not_reconciled_to_580_factor"}
    assert {row["value_numeric"] for row in gas_rows} == {"67", "43", "375", "31"}

    unreported = records["VGNG25-T3-CUT-GRASS-EMISSION_FACTOR"]
    assert unreported["value_numeric"] == ""
    assert unreported["validation_status"] == "not_reported"
    assert "functional unit boundary" in unreported["basis"]

    manifest = _rows(FOLDER / "dataset_manifest.csv")
    assert {row["filename"] for row in manifest} >= {RVO_FILE, VGNG_FILE}
    sources = _rows(FOLDER / "source_register.csv")
    assert {row["source_id"] for row in sources} >= {"SRC-RVO-BRINKMANN-GRASS-2014", "SRC-VGNG-INTERREG-2025"}

    audit = ROOT / "Greenhub" / "data" / "global_audit_package"
    for filename in (RVO_FILE, VGNG_FILE):
        relative = f"Bigas production + upgrade/Feed BMP/{filename}"
        global_manifest = next(row for row in _rows(audit / "global_dataset_manifest.csv") if row["dataset_path"] == relative)
        assert global_manifest["detected_readiness"] == "D3"
        readiness = next(row for row in _rows(audit / "global_dataset_readiness.csv") if row["dataset_path"] == relative)
        assert readiness["readiness"] == "D3"
        checksum = next(row for row in _rows(audit / "source_dataset_checksums.csv") if row["dataset_path"] == relative)
        assert checksum["sha256"] == hashlib.sha256((FOLDER / filename).read_bytes()).hexdigest()

    catalog_path = ROOT / "Greenhub" / "data" / "fair_input_catalog" / "master_input_catalog.csv"
    if catalog_path.exists():
        catalog = _rows(catalog_path)
        for filename, source_id in ((RVO_FILE, "SRC-RVO-BRINKMANN-GRASS-2014"), (VGNG_FILE, "SRC-VGNG-INTERREG-2025")):
            asset = next(row for row in catalog if row["relative_path"].endswith(filename))
            assert source_id in asset["source_ids"]
            assert asset["readiness"] == "reference_only"
