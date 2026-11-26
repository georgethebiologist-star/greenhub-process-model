import csv
import json
from pathlib import Path


DATA = (
    Path(__file__).parents[1]
    / "Greenhub"
    / "data"
    / "Pre-treatment"
    / "Feedstock"
)


def test_supplied_bermgrass_report_is_staged_with_limits_and_without_personal_metadata():
    path = DATA / "brs_roadside_grass_pilot_2021_draft_reference.csv"
    with path.open(encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))
    source = json.loads(Path(f"{path}.source.json").read_text(encoding="utf-8"))

    assert len(rows) == 105
    assert {row["record_type"] for row in rows} == {"measurement"}
    assert all(row["source_page"] and row["source_location"] for row in rows)
    assert not any("requester" in row.values() for row in rows)
    assert source["activation_state"] == "reference_only"
    assert source["doi"] is None
    assert "not present" in source["underlying_report_status"]
    assert any("not fully balanced" in item for item in source["limitations"])
    assert "requester metadata" in source["privacy"].lower()


def test_reported_mass_balance_warning_and_mixed_bases_are_preserved():
    path = DATA / "brs_roadside_grass_pilot_2021_draft_reference.csv"
    with path.open(encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))

    assert any(row["section"] == "Mass balance" for row in rows)
    assert any(row["section"] == "Material processing" and row["value"] == "5:1" for row in rows)
    assert any(row["section"] == "Conclusion" and row["value"] == "11" for row in rows)
    assert any("mass % of input dry matter" in row["unit"] for row in rows)


def test_varta_explicit_dm_percent_matches_legacy_alias_and_workbook_archive_is_present():
    path = DATA / "varta_2026_grass_fiber_measurements.csv"
    with path.open(encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))

    assert len(rows) == 18
    assert all(row["dry_matter_percent"] == row["dry_matter_fraction"] for row in rows)
    greenhub = next(row for row in rows if row["sample_name_english"] == "Greenhub whole grass")
    assert greenhub["dry_matter_percent"] == "14.3"
    assert (DATA / "261027 Nutriënten Grasmonsters VARTA.xlsx").is_file()


def test_nielsen_table1_harvest_yield_reference_has_unique_provenance_and_annual_rows():
    path = DATA / "fen_grass_harvest_yield_cp_nielsen_2021_table1_reference.csv"
    with path.open(encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))
    source = json.loads(Path(f"{path}.source.json").read_text(encoding="utf-8"))

    assert len(rows) == 40
    assert len({row["observation_id"] for row in rows}) == 40
    assert source["doi"] == "10.3389/fenvs.2021.619258"
    assert source["license"] == "Creative Commons Attribution (CC BY), as stated in the article"
    assert source["activation_state"] == "reference_only"
    assert {row["species"] for row in rows} == {"reed canary grass", "tall fescue"}
    assert all(row["source_class"] == "B" and row["activation_state"] == "reference_only" for row in rows)

    annual = {
        (row["species"], row["management_cuts"]): float(row["dm_yield_mean_t_dm_ha"])
        for row in rows
        if row["observation_type"] == "annual_average"
    }
    assert annual[("reed canary grass", "2")] == 15.6
    assert annual[("tall fescue", "5")] == 9.8
    assert any(row["observation_type"] == "individual_cut" and row["harvest_week"] == "24" for row in rows)
    assert "confounded" in source["limitations"][1]


def test_fair_catalog_links_each_new_asset_to_its_own_source_only():
    path = DATA.parents[1] / "fair_input_catalog" / "master_input_catalog.csv"
    with path.open(encoding="utf-8-sig", newline="") as handle:
        assets = list(csv.DictReader(handle))
    by_suffix = {row["relative_path"].split("/")[-1]: row for row in assets}

    varta = by_suffix["261027 Nutriënten Grasmonsters VARTA.xlsx"]
    supplied_report = by_suffix["brs_roadside_grass_pilot_2021_draft_reference.csv"]
    nielsen = by_suffix["fen_grass_harvest_yield_cp_nielsen_2021_table1_reference.csv"]
    fractionation = by_suffix[
        "fen_grass_biorefinery_fractionation_annual_nielsen_2021_tables_3_4_reference.csv"
    ]
    cncps = by_suffix["fen_grass_protein_fraction_extractability_nielsen_2021_table2_reference.csv"]

    assert varta["source_metadata_status"] == "linked_to_source_register"
    assert not varta["source_dois"]
    assert supplied_report["source_metadata_status"] == "linked_to_source_register"
    assert not supplied_report["source_dois"]
    assert nielsen["source_dois"] == "10.3389/fenvs.2021.619258"
    assert fractionation["source_dois"] == "10.3389/fenvs.2021.619258"
    assert cncps["source_dois"] == "10.3389/fenvs.2021.619258"


def test_nielsen_annual_fractionation_values_preserve_streams_sd_and_nonclosure():
    path = DATA / "fen_grass_biorefinery_fractionation_annual_nielsen_2021_tables_3_4_reference.csv"
    with path.open(encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))
    source = json.loads(Path(f"{path}.source.json").read_text(encoding="utf-8"))

    assert len(rows) == 8
    assert len({row["observation_id"] for row in rows}) == 8
    assert {row["species"] for row in rows} == {"reed canary grass", "tall fescue"}
    assert all(row["source_table"] in {"3", "4"} for row in rows)
    assert all(row["source_class"] == "B" and row["activation_state"] == "reference_only" for row in rows)
    rcg_two_cuts = next(row for row in rows if row["species"] == "reed canary grass" and row["harvest_cuts"] == "2")
    assert rcg_two_cuts["annual_input_dm_mean_t_ha_year"] == "15.6"
    assert rcg_two_cuts["protein_concentrate_cp_mean_t_ha_year"] == "0.6"
    # Keep source-reported mean discrepancy visible; do not force the balance closed.
    dm_products = sum(float(rcg_two_cuts[f"{stream}_dm_mean_t_ha_year"]) for stream in ("pulp", "protein_concentrate", "brown_juice"))
    assert dm_products == 15.1
    assert dm_products != float(rcg_two_cuts["annual_input_dm_mean_t_ha_year"])
    assert rcg_two_cuts["brown_juice_cp_sd_t_ha_year"] == "0.2"
    assert "do not sum exactly" in source["limitations"][0]
    assert "does not report" in source["process_conditions"]


def test_nielsen_table2_cncps_fractions_are_explicitly_not_process_recoveries():
    path = DATA / "fen_grass_protein_fraction_extractability_nielsen_2021_table2_reference.csv"
    with path.open(encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))
    source = json.loads(Path(f"{path}.source.json").read_text(encoding="utf-8"))

    assert len(rows) == 10
    assert len({row["observation_id"] for row in rows}) == 10
    assert all(row["source_table"] == "2" for row in rows)
    assert all(row["activation_state"] == "reference_only" for row in rows)
    rcg_five_cuts = next(row for row in rows if row["species"] == "reed canary grass" and row["harvest_cuts"] == "5")
    assert rcg_five_cuts["annual_neutral_extractable_b1_b2_mean_g_kg_dm"] == "117"
    assert rcg_five_cuts["annual_neutral_extractable_b1_b2_share_total_cp_percent"] == "49"
    assert rcg_five_cuts["annual_potentially_extractable_b1_b2_b3_mean_g_kg_dm"] == "173"
    assert rcg_five_cuts["annual_potentially_extractable_b1_b2_b3_share_total_cp_percent"] == "76"
    assert "not equivalent to screw-press release" in source["limitations"][0]
