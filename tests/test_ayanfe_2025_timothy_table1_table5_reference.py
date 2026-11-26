import csv
import importlib.util
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "Greenhub" / "data" / "Pre-treatment" / "Mechanical"
CSV_PATH = DATA / "timothy_feed_and_press_liquid_ayanfe_2025_tables1_5_reference.csv"
SOURCE_ID = "S14_AYANFE_2025_GFS12722"


def _rows():
    with CSV_PATH.open(encoding="utf-8", newline="") as stream:
        return list(csv.DictReader(stream))


def test_tables_1_and_5_are_complete_traceable_and_reference_only():
    rows = _rows()
    assert len(rows) == 150
    assert Counter(row["table_number"] for row in rows) == {"1": 45, "5": 105}
    assert {row["source_id"] for row in rows} == {SOURCE_ID}
    assert {row["quality_class"] for row in rows} == {"B"}
    assert {row["activation_state"] for row in rows} == {"reference_only"}
    assert all(row["reported_value"] != "" for row in rows)
    assert all(row["replicate_n"] == "" for row in rows)

    lookup = {
        (row["table_number"], row["condition_id"], row["response_parameter"]): row
        for row in rows
    }
    assert lookup[("1", "EXP1_PG_INTACT", "dry_matter")]["reported_value"] == "276"
    assert lookup[("1", "EXP2_REG_INTACT", "dry_matter")]["reported_value"] == "195"
    assert lookup[("5", "EXP1_PG_INTACT_PSS", "liquid_yield")]["reported_value"] == "0.301"
    assert lookup[("5", "EXP2_REG_INTACT_DSP", "liquid_crude_protein")]["reported_value"] == "139"
    assert lookup[("5", "EXP2_REG_INTACT_DSP", "captured_crude_protein_fraction")]["reported_value"] == "0.268"
    assert lookup[("5", "EXP2_REG_WILTED_DSP", "liquid_zinc")]["reported_value"] == "35"

    primary_yield = lookup[("5", "EXP1_PG_INTACT_PSS", "liquid_yield")]
    assert "denominator is unresolved" in primary_yield["notes"]
    assert primary_yield["reported_unit"] == "g liquid/g fresh sample"


def test_reference_extract_matches_reproducible_builder_and_is_registered():
    script = ROOT / "scripts" / "build_ayanfe_2025_timothy_table1_table5_reference.py"
    spec = importlib.util.spec_from_file_location("ayanfe_reference_builder", script)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)

    assert _rows() == module.build_rows()
    sidecar = CSV_PATH.with_suffix(CSV_PATH.suffix + ".source.json")
    metadata = sidecar.read_text(encoding="utf-8")
    assert '"doi": "10.1111/gfs.12722"' in metadata
    assert '"license": "Creative Commons Attribution 4.0 International (CC BY 4.0)"' in metadata
    assert '"runtime_policy": "reference_only;' in metadata

    source_register = (DATA / "source_register.csv").read_text(encoding="utf-8")
    manifest = (DATA / "dataset_manifest.csv").read_text(encoding="utf-8")
    assert source_register.count(SOURCE_ID) == 1
    assert manifest.count("timothy_feed_and_press_liquid_ayanfe_2025_tables1_5_reference.csv") == 1

