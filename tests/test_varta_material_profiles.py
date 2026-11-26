import csv
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PROFILE_DIR = ROOT / "biorefinery_platform/examples/material_profiles"
FEED_CSV = ROOT / "Greenhub/data/Pre-treatment/Feedstock/varta_2026_grass_fiber_measurements.csv"
JUICE_CSV = ROOT / "Greenhub/data/Pre-treatment/Feedstock/varta_2026_grass_juice_measurements.csv"


def _rows(path):
    with path.open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def _profile(filename):
    return json.loads((PROFILE_DIR / filename).read_text(encoding="utf-8"))


def _assert_profile_shape(profile):
    assert {
        "schema_version", "record_id", "project_id", "data_scope_class",
        "context_independent", "material", "mass_composition",
        "analytical_properties", "closure", "activation_state",
        "provenance", "metadata_gaps",
    }.issubset(profile)
    assert profile["context_independent"] is False
    assert profile["data_scope_class"] == "material_or_site_specific"
    assert profile["mass_composition"] == []
    assert profile["closure"]["status"] == "not_checked"
    assert profile["activation_state"] == "reference_only"
    assert profile["provenance"][0]["source_id"] == "SRC-VARTA-2026-10-27"
    assert profile["provenance"][0]["doi_or_stable_id"].startswith("VARTA_2026_10_27")
    assert all(item["unit"] and item["sample_basis"] for item in profile["analytical_properties"])
    assert all(item["status"] in {"measured", "not_reported"} for item in profile["analytical_properties"])


def _assert_source_value(profile, row, property_id, column):
    prop = next(item for item in profile["analytical_properties"] if item["property_id"] == property_id)
    raw = row[column]
    if raw == "":
        assert prop["value"] is None
        assert prop["status"] == "not_reported"
    else:
        assert float(prop["value"]) == float(raw)
        assert prop["status"] == "measured"


def test_varta_whole_grass_and_reterra_samples_are_distinct_analytical_profiles():
    rows = _rows(FEED_CSV)
    by_name = {row["sample_name_english"]: row for row in rows}
    cases = [
        (
            "varta_2026_greenhub_whole_grass.json",
            "Greenhub whole grass",
            "dry_matter_percent",
            {
                "total_nitrogen": "nitrogen_g_kg_dm",
                "total_phosphorus": "phosphorus_g_kg_dm",
                "total_potassium": "potassium_g_kg_dm",
                "chloride": "chloride_g_kg_dm",
                "crude_protein": "crude_protein_g_kg_dm",
            },
        ),
        (
            "varta_2026_reterra_road_verge_grass_n36.json",
            "Reterra road-verge grass N36",
            "dry_matter_percent",
            {
                "crude_protein": "crude_protein_g_kg_dm",
                "crude_protein_as_received": "crude_protein_g_kg_product",
                "total_nitrogen": "nitrogen_g_kg_dm",
                "total_phosphorus": "phosphorus_g_kg_dm",
                "total_potassium": "potassium_g_kg_dm",
                "chloride": "chloride_g_kg_dm",
            },
        ),
    ]
    for filename, sample_name, dm_column, property_columns in cases:
        profile = _profile(filename)
        _assert_profile_shape(profile)
        row = by_name[sample_name]
        assert profile["material"]["sampling_time"] == row["sample_date"]
        assert int(profile["provenance"][0]["source_location"].split("source row ")[1].split(",")[0]) == int(row["source_row"])
        _assert_source_value(profile, row, "dry_matter_content", dm_column)
        for property_id, column in property_columns.items():
            _assert_source_value(profile, row, property_id, column)

    greenhub = _profile("varta_2026_greenhub_whole_grass.json")
    reterra = _profile("varta_2026_reterra_road_verge_grass_n36.json")
    assert greenhub["record_id"] != reterra["record_id"]
    assert "not the GreenHub whole-grass sample" in " ".join(reterra["metadata_gaps"])
    assert any(item["status"] == "not_reported" for item in greenhub["analytical_properties"])
    estimate = next(item for item in greenhub["derived_analytical_properties"] if item["property_id"] == "crude_protein_equivalent_n_times_6_25")
    assert estimate["value"] == 21.0 * 6.25
    assert estimate["quality_class"] == "C"
    assert estimate["activation_state"] == "reference_only"
    assert estimate["calculation"]["input_property_ids"] == ["total_nitrogen"]
    assert "not a measured crude-protein result" in " ".join(estimate["limitations"]).lower()
    assert greenhub["mass_composition"] == []


def test_varta_greenhub_juice_is_not_linked_to_raw_feed_or_used_as_a_flow():
    profile = _profile("varta_2026_greenhub_grass_juice.json")
    _assert_profile_shape(profile)
    rows = _rows(JUICE_CSV)
    row = next(item for item in rows if item["sample_name_english"] == "Greenhub (grass sample)")
    assert row["sample_date"] == ""
    assert "source row 5" in profile["provenance"][0]["source_location"]
    for prop, column in {
        "ammonium": "ammonium_mg_l",
        "nitrite": "nitrite_mg_l",
        "nitrate": "nitrate_mg_l",
        "potassium": "potassium_mg_l",
        "phosphate": "phosphate_mg_l",
        "chloride": "chloride_mg_l",
        "sulfate": "sulfate_mg_l",
        "calcium": "calcium_mg_l",
        "magnesium": "magnesium_mg_l",
        "silicon_dioxide": "silicon_dioxide_mg_l",
        "iron": "iron_mg_l",
    }.items():
        _assert_source_value(profile, row, prop, column)
    assert "Parent raw-grass lot" in profile["material"]["treatment_history"]
    assert any("not proven to originate" in item for item in profile["metadata_gaps"])
    assert any("No sample volume" in item for item in profile["metadata_gaps"])
