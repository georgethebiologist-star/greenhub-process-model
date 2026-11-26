import csv
import json
from pathlib import Path


DATA = (
    Path(__file__).parents[1]
    / "Greenhub"
    / "data"
    / "Resource recovery"
    / "Digestate_and_Separation"
)
CSV_PATH = DATA / "clover_grass_biorefinery_partition_santamaria_fernandez_2020_reference.csv"
SOURCE_PATH = CSV_PATH.with_suffix(".source.json")
PZH_SCHEMA_CSV = (
    Path(__file__).parents[1]
    / "Greenhub"
    / "data"
    / "Pre-treatment"
    / "Feedstock"
    / "roadside_grass_pzh_green_area_inventory_field_dictionary.csv"
)
PZH_SUMMARY_CSV = PZH_SCHEMA_CSV.with_name("roadside_grass_pzh_inventory_2026_summary_reference.csv")


def read_csv(path):
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def test_clover_grass_reference_observations_are_traceable_and_not_activated():
    rows = read_csv(CSV_PATH)
    source = json.loads(SOURCE_PATH.read_text(encoding="utf-8"))
    register = read_csv(DATA / "source_register.csv")

    assert len(rows) == 69
    assert len({row["observation_id"] for row in rows}) == len(rows)
    assert {row["source_id"] for row in rows} == {source["source_id"]}
    assert source["doi"] == "10.1007/s12649-019-00842-3"
    assert source["activation_state"] == "reference_only"
    assert source["retrieval_date"]
    assert any(item["source_id"] == source["source_id"] for item in register)
    assert all(row["evidence_class"] == "B_reported_measurement" for row in rows)
    assert all(row["activation_state"] == "reference_only" for row in rows)
    assert all(row["reported_mean"] or row["status"] in {"not_determined", "below_detection_limit"} for row in rows)
    assert all(row["reported_mean"] for row in rows if row["status"] == "reported")


def test_clover_grass_reference_chemistry_mapping_and_ad_basis_are_consistent():
    rows = read_csv(CSV_PATH)
    by_key = {(row["scale"], row["stream"], row["parameter"]): row for row in rows}

    expected_n = {
        ("small-scale", "fresh biomass"): "3.1",
        ("small-scale", "press cake"): "4.9",
        ("small-scale", "brown juice"): "0.8",
        ("small-scale", "protein concentrate"): "13.2",
        ("pilot-scale", "fresh biomass"): "5.8",
        ("pilot-scale", "press cake"): "6.9",
        ("pilot-scale", "brown juice"): "0.6",
    }
    for (scale, stream), expected in expected_n.items():
        row = by_key[(scale, stream, "total_nitrogen")]
        assert row["reported_mean"] == expected
        assert row["unit"] == "g/kg"
        assert row["basis"] == "fresh matter"

    for scale, stream, expected in [
        ("small-scale", "fresh biomass", "26"),
        ("small-scale", "press cake", "33"),
        ("small-scale", "brown juice", "18"),
        ("small-scale", "protein concentrate", "8"),
        ("pilot-scale", "fresh biomass", "13"),
        ("pilot-scale", "press cake", "18"),
        ("pilot-scale", "brown juice", "15"),
    ]:
        assert by_key[(scale, stream, "C_to_N_ratio")]["reported_mean"] == expected

    assert by_key[("pilot-scale", "brown juice", "ammonia_N_fraction_total_N")]["status"] == "below_detection_limit"
    assert by_key[("pilot-scale", "brown juice", "ammonia_N_fraction_total_N")]["reported_mean"] == ""
    assert by_key[("pilot-scale", "reactor", "CH4_yield")]["reported_mean"] == "237.6"
    assert by_key[("pilot-scale", "reactor", "CH4_yield")]["unit"] == "mL CH4/g VS"
    assert "study-specific co-digestion mixture" in by_key[("pilot-scale", "reactor", "CH4_yield")]["limitations"]


def test_pzh_phase1_gis_source_is_english_and_reference_only():
    fields = read_csv(PZH_SCHEMA_CSV)
    source = json.loads(PZH_SCHEMA_CSV.with_suffix(".source.json").read_text(encoding="utf-8"))
    by_field = {row["source_field"]: row for row in fields}

    assert len(fields) == 16
    assert source["dataset_identifier"].endswith("a1dbcfc3-2533-46af-9483-7a102488b911")
    assert source["feature_type"] == "verkeer:ABS_W_GROEN"
    assert source["license"] == "Public domain, as stated by the national open-data catalog"
    assert source["model_readiness"] == "reference_only"
    assert by_field["Oppervlakte"]["english_field"] == "Polygon area"
    assert by_field["Opp_correctie"]["source_unit"] == "m2"
    assert "not harvested biomass" in source["limitations"][1]
    assert all(row["activation_status"] == "metadata_only" for row in fields)
    assert all(not row["source_definition_english"].strip().isdigit() for row in fields)


def test_pzh_phase1_inventory_aggregates_are_traceable_and_not_supply_estimates():
    rows = read_csv(PZH_SUMMARY_CSV)
    source = json.loads(
        PZH_SUMMARY_CSV.with_name(PZH_SUMMARY_CSV.stem + ".source.json").read_text(encoding="utf-8")
    )

    assert len(rows) == 33
    assert source["processing"]["source_records_retrieved"] == 37188
    assert source["processing"]["geometry_requested"] is False
    assert source["processing"]["aggregation_rows"] == len(rows)
    assert source["activation_state"] == "reference_only"
    assert {row["source_id"] for row in rows} == {source["source_id"]}
    assert {row["activation_state"] for row in rows} == {"reference_only"}
    assert not any("yield" in key.lower() or "availability" in key.lower() for key in rows[0])

    expected = {
        "berm": (9726, 5697043.8, 5885056.5),
        "grasstenen": (1884, 244751.8, 244751.8),
        "zichthoek": (16762, 3194152.1, 3194152.1),
    }
    for asset_type, (count, area, corrected_area) in expected.items():
        grouped = [row for row in rows if row["asset_type_source"] == asset_type]
        assert sum(int(row["feature_count"]) for row in grouped) == count
        assert abs(sum(float(row["mapped_area_m2"]) for row in grouped) - area) < 0.01
        assert abs(sum(float(row["slope_corrected_area_m2"]) for row in grouped) - corrected_area) < 0.01

    assert any(row["maintenance_frequency_source"] == "" for row in rows)
    assert any(row["mowing_description_source"] == "met meter maaien" for row in rows)
    assert "not a measured grass crop" in " ".join(source["limitations"]).lower()
