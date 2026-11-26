import csv
import json
from pathlib import Path

from biorefinery_platform.data_catalog import build_catalog_bundle


ROOT = Path(__file__).resolve().parents[1]
DATA_PATH = ROOT / "Greenhub/data/Bigas production + upgrade/AD reactor/ryegrass_silage_two_phase_maus_2020_process_reference.csv"
PROFILE_PATH = ROOT / "biorefinery_platform/examples/material_profiles/perennial_ryegrass_silage_maus_2020.json"


def test_maus_reference_keeps_gas_basis_and_reactor_results_separate():
    with DATA_PATH.open("r", encoding="utf-8", newline="") as source:
        rows = list(csv.DictReader(source))

    assert len(rows) == 33
    assert len({row["record_id"] for row in rows}) == len(rows)
    by_id = {row["record_id"]: row for row in rows}
    assert by_id["MAUS20-AD-PERF-01"]["parameter"] == "biogas_yield"
    assert by_id["MAUS20-AD-PERF-01"]["reported_unit"] == "L_N/kg VS"
    assert by_id["MAUS20-AD-PERF-07"]["parameter"] == "methane_yield"
    assert by_id["MAUS20-AD-PERF-07"]["reported_value"] == "337"
    assert by_id["MAUS20-AD-PERF-09"]["parameter"] == "reference_batch_methane_yield"
    assert "not methane yield" in by_id["MAUS20-AD-PERF-01"]["limitations"]
    assert by_id["MAUS20-AD-CONFIG-09"]["parameter"] == "batch_fermentation_retention_time"
    assert by_id["MAUS20-AD-CONFIG-09"]["reported_unit"] == "day"
    assert all(row["activation_state"] == "reference_only" for row in rows)


def test_maus_material_profile_is_project_neutral_but_not_context_independent():
    profile = json.loads(PROFILE_PATH.read_text(encoding="utf-8"))
    assert profile["project_id"] is None
    assert profile["context_independent"] is False
    assert profile["data_scope_class"] == "technology_and_material_specific"
    assert profile["activation_state"] == "reference_only"
    assert profile["mass_composition"] == []
    assert profile["closure"]["status"] == "not_checked"
    assert all(item["quality_class"] == "B" for item in profile["analytical_properties"])
    properties = {row["property_id"]: row for row in profile["analytical_properties"]}
    assert properties["propionic_acid"]["value"] == "<0.04"
    assert properties["propionic_acid"]["status"] == "not_detected"
    assert properties["chemical_oxygen_demand"]["unit"] == "g O2/kg fresh mass"
    assert any("not a raw-grass composition" in gap for gap in profile["metadata_gaps"])


def test_maus_ad_dataset_is_findable_in_reuse_catalog_without_runtime_promotion():
    bundle = build_catalog_bundle()
    row = next(item for item in bundle["datasets"] if item["filename"] == DATA_PATH.name)
    assert row["source_ids"] == ["SRC-MAUS-2020-RYEGRASS-AD"]
    assert any("10.1186/s40793-020-00354-x" in item for item in row["source_dois_or_stable_ids"])
    assert row["detected_readiness"] == "D2"
    assert row["context_independent"] is False
    assert row["metadata_gaps"] == []
    assert bundle["counts"]["d4_promotions"] == 0
