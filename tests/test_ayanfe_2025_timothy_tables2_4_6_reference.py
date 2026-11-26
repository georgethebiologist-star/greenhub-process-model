import csv
import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DATASET = ROOT / "Greenhub/data/storage/timothy_silage_fermentation_effluent_and_press_liquid_ayanfe_2025_tables2_4_6_reference.csv"
SIDECAR = Path(str(DATASET) + ".source.json")


def _rows():
    with DATASET.open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def test_ayanfe_2025_tables2_4_6_dataset_is_complete_and_reference_only():
    rows = _rows()
    assert len(rows) == 519
    assert {row["source_table"] for row in rows} == {"2", "3", "4", "6"}
    assert len({row["observation_id"] for row in rows}) == len(rows)
    assert {row["quality_class"] for row in rows} == {"B"}
    assert {row["runtime_status"] for row in rows} == {"reference_only_not_runtime_eligible"}


def test_key_silage_and_press_results_preserve_reported_basis_and_statistics():
    rows = _rows()
    by_id = {row["observation_id"]: row for row in rows}
    pg_intact_control_dm = by_id["AY25_T2_DRY_MATTER_01"]
    assert float(pg_intact_control_dm["reported_mean"]) == 268
    assert pg_intact_control_dm["unit"] == "g/kg"
    assert pg_intact_control_dm["basis"] == "fresh ensiled material"
    assert float(pg_intact_control_dm["reported_sem"]) == 2.2
    assert pg_intact_control_dm["p_biomass_type_x_additive"] == "0.073"

    regrowth_wilted_fa2_stability = by_id["AY25_T3_AEROBIC_STABILITY_09"]
    assert float(regrowth_wilted_fa2_stability["reported_mean"]) == 117
    assert "244 h observation length" in regrowth_wilted_fa2_stability["source_note"]

    pressed_liquid_yield = by_id["AY25_T6_LIQUID_YIELD_01"]
    assert float(pressed_liquid_yield["reported_mean"]) == 0.702
    assert pressed_liquid_yield["biomass_type"] == "Intact"
    assert pressed_liquid_yield["additive"] == "Control"
    assert pressed_liquid_yield["press_type"].startswith("double-screw press")


def test_pooled_effluent_is_not_given_inferential_statistics_or_zero_imputation():
    rows = [row for row in _rows() if row["source_table"] == "4"]
    assert len(rows) == 60
    ammonia_fa2 = next(row for row in rows if row["parameter"] == "ammonia_n" and row["additive"] == "FA2")
    assert ammonia_fa2["reported_mean"] == "0"
    assert ammonia_fa2["reported_sem"] == ""
    assert ammonia_fa2["p_additive"] == ""
    assert "pooled to one treatment composite" in ammonia_fa2["replication_context"]


def test_sidecar_captures_source_and_transferability_limits():
    metadata = json.loads(SIDECAR.read_text(encoding="utf-8"))
    assert metadata["doi"] == "10.1111/gfs.12722"
    assert metadata["license"].startswith("Creative Commons Attribution 4.0")
    assert metadata["record_count"] == 519
    assert metadata["sha256"] == hashlib.sha256(DATASET.read_bytes()).hexdigest()
    assert "roadside grass" in " ".join(metadata["limitations"])
    assert "runtime parameters" in metadata["runtime_policy"].lower()


def test_dataset_is_linked_from_local_and_global_fair_registers():
    with (ROOT / "Greenhub/data/storage/source_register.csv").open(encoding="utf-8-sig", newline="") as handle:
        sources = list(csv.DictReader(handle))
    source = next(row for row in sources if row["source_id"] == "S14_AYANFE_2025_GFS12722")
    assert source["doi_or_stable_identifier"] == "10.1111/gfs.12722"

    with (ROOT / "Greenhub/data/storage/dataset_manifest.csv").open(encoding="utf-8-sig", newline="") as handle:
        manifest = list(csv.DictReader(handle))
    assert next(row for row in manifest if row["filename"] == DATASET.name)["row_count"] == "519"

    with (ROOT / "Greenhub/data/global_audit_package/global_dataset_manifest.csv").open(encoding="utf-8-sig", newline="") as handle:
        global_manifest = list(csv.DictReader(handle))
    global_row = next(row for row in global_manifest if row["dataset_path"] == f"storage/{DATASET.name}")
    assert global_row["header_count"] == "24"
    assert global_row["detected_readiness"] == "D3"

    catalog = json.loads((ROOT / "Greenhub/data/fair_input_catalog/master_input_catalog.json").read_text(encoding="utf-8"))
    asset = next(row for row in catalog["assets"] if row["relative_path"] == DATASET.relative_to(ROOT).as_posix())
    assert "S14_AYANFE_2025_GFS12722" in asset["source_ids"].split(";")
    assert "10.1111/gfs.12722" in asset["source_dois"].split(";")
    assert asset["source_metadata_status"] == "linked_to_source_register"
    assert asset["readiness"] == "reference_only"

