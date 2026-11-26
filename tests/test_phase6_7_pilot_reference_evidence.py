import csv
import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def _rows(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as stream:
        return list(csv.DictReader(stream))


def test_phase4_precipitation_table2_transcription_is_complete_and_reference_only():
    folder = ROOT / "Greenhub" / "data" / "Protein recovery" / "Isoelectric"
    path = folder / "lignosulfonate_precipitation_reference_2019.csv"
    rows = _rows(path)
    metadata = json.loads(path.with_suffix(".source.json").read_text(encoding="utf-8"))
    manifest = _rows(folder / "dataset_manifest.csv")
    fair_assets = _rows(ROOT / "Greenhub" / "data" / "fair_input_catalog" / "master_input_catalog.csv")

    assert len(rows) == 12
    assert len({row["observation_id"] for row in rows}) == 12
    assert {row["source_id"] for row in rows} == {"SRC003"}
    assert {row["activation_state"] for row in rows} == {"reference_only"}
    assert {row["feedstock"] for row in rows} == {
        "perennial_ryegrass_Lolium_perenne_cv_Mahogany",
        "red_clover_Trifolium_pratense_cv_Callisto",
    }
    ryegrass = {row["treatment"]: row for row in rows if row["feedstock"].startswith("perennial_ryegrass")}
    assert ryegrass["isoelectric"]["reported_crude_protein_pct_dm"] == "30.4"
    assert ryegrass["isoelectric"]["nitrogen_recovery_pct_juice_total_n"] == "70"
    assert any(row["feedstock"].startswith("perennial_ryegrass") and row["treatment"] == "lignosulfonate" and row["reported_condition"] == "0.5_N_equivalent" for row in rows)
    assert any(row["treatment"] == "lignosulfonate" and row["reported_condition"] == "4.0_N_equivalent" for row in rows)
    assert all("total N" in row["basis"] for row in rows)
    assert metadata["doi"] == "10.3389/fsufs.2019.00112"
    assert metadata["source_table"] == "Table 2"
    assert metadata["license"] == "CC BY 4.0"
    assert "not equivalent to isolated true-protein recovery" in metadata["limitations"][0]
    assert any(row["filename"] == path.name and row["row_count"] == "12" and row["integration_readiness"] == "reference_only" for row in manifest)
    asset = next(row for row in fair_assets if row["relative_path"].endswith(path.name))
    assert asset["source_ids"] == "SRC003"
    assert asset["source_dois"] == "10.3389/fsufs.2019.00112"
    assert asset["source_metadata_linkage"] == "direct_local_source_record"
    assert asset["license_or_rights"] == "CC BY 4.0"

    code = "\n".join(file.read_text(encoding="utf-8") for file in (ROOT / "Greenhub").rglob("*.py"))
    assert path.name not in code


def test_phase7_dutch_farm_nutrient_recovery_comparator_preserves_basis_and_limits():
    folder = ROOT / "Greenhub" / "data" / "Resource recovery" / "Phosphorus_Recovery"
    path = folder / "demarke_manure_digestate_nutrient_recovery_2019_reference.csv"
    rows = _rows(path)
    metadata = json.loads(path.with_suffix(".source.json").read_text(encoding="utf-8"))
    sources = _rows(folder / "source_register.csv")
    manifest = _rows(folder / "dataset_manifest.csv")
    catalog = _rows(ROOT / "Greenhub" / "data" / "fair_input_catalog" / "master_input_catalog.csv")

    assert len(rows) == 18
    assert len({row["record_id"] for row in rows}) == 18
    assert {row["source_id"] for row in rows} == {"SZYMANASKA2019"}
    assert {row["activation_state"] for row in rows} == {"reference_only"}
    assert {row["quality_class"] for row in rows} == {"B"}
    assert all(row["basis"] == "wet basis" for row in rows if row["unit"] != "pH" and row["stream"] != "combined_nutrient_recovery_train")
    assert {row["basis"] for row in rows if row["stream"] == "combined_nutrient_recovery_train"} == {"source-reported concentration difference"}
    assert next(row for row in rows if row["metric"] == "water_soluble_phosphorus")["reported_value"] == "183.0"
    assert next(row for row in rows if row["metric"] == "phosphorus_recovery_efficiency")["reported_value"] == "43.8"
    n_eff = next(row for row in rows if row["metric"] == "nitrogen_recovery_efficiency")
    assert "cannot isolate struvite or stripping recovery" in n_eff["notes"]
    assert metadata["doi"] == "10.3390/en12010155"
    assert metadata["license"] == "CC BY 4.0 (stated in full-text article footer)"
    assert "not roadside grass" in metadata["limitations"][0]
    assert sum(row["source_id"] == "SZYMANASKA2019" for row in sources) == 1
    assert any(row["filename"] == path.name and row["row_count"] == "18" and row["integration_status"] == "traceable_reference_only_not_runtime_eligible" for row in manifest)
    asset = next(row for row in catalog if row["relative_path"].endswith(path.name))
    assert asset["source_ids"] == "SZYMANASKA2019"
    assert asset["source_dois"] == "10.3390/en12010155"
    assert asset["readiness"] == "reference_only"

    code = "\n".join(file.read_text(encoding="utf-8") for file in (ROOT / "Greenhub").rglob("*.py"))
    assert path.name not in code


def test_phase4_7_green_forage_mineral_partition_preserves_table_basis_and_gaps():
    folder = ROOT / "Greenhub" / "data" / "Protein recovery" / "Isoelectric"
    path = folder / "green_forage_fraction_mineral_partition_hansen_2022_reference.csv"
    rows = _rows(path)
    metadata = json.loads(path.with_suffix(".source.json").read_text(encoding="utf-8"))
    sources = _rows(folder / "source_register.csv")
    manifest = _rows(folder / "dataset_manifest.csv")
    catalog = _rows(ROOT / "Greenhub" / "data" / "fair_input_catalog" / "master_input_catalog.csv")

    assert len(rows) == 20
    assert len({row["record_id"] for row in rows}) == 20
    assert {row["source_id"] for row in rows} == {"HANSEN2022"}
    assert {row["activation_state"] for row in rows} == {"reference_only"}
    assert {row["quality_class"] for row in rows} == {"B"}
    assert {row["forage"] for row in rows} == {"white_clover", "red_clover", "lucerne", "perennial_ryegrass"}
    assert {row["fraction"] for row in rows} == {"whole_plant", "pulp", "green_juice", "green_protein", "brown_juice"}
    assert next(row for row in rows if row["record_id"] == "HANSEN22-PR-GREENJUICE")["K_g_per_kg_DM"] == "56.8"
    assert next(row for row in rows if row["record_id"] == "HANSEN22-PR-BROWNJUICE")["P_g_per_kg_DM"] == "9.78"
    assert next(row for row in rows if row["record_id"] == "HANSEN22-PR-GREENPROTEIN")["Cu_mg_per_kg_DM"] == "26.6"
    assert all(row["fraction"] not in {"green_protein", "brown_juice"} or row["season_scope"] == "July September" for row in rows)
    assert metadata["doi"] is None
    assert metadata["table_statistics"]["sample_count"] == 52
    assert metadata["table_statistics"]["largest_SEM_by_analyte"]["Cu_mg_per_kg_DM"] == 1.261
    assert metadata["license"].startswith("No explicit reuse license identified")
    assert any("not fraction flow rates or elemental mass balances" in limitation for limitation in metadata["limitations"])
    assert sum(row["source_id"] == "HANSEN2022" for row in sources) == 1
    assert any(row["filename"] == path.name and row["row_count"] == "20" and row["integration_readiness"] == "reference_only" for row in manifest)
    asset = next(row for row in catalog if row["relative_path"].endswith(path.name))
    assert asset["source_ids"] == "HANSEN2022"
    assert asset["readiness"] == "reference_only"

    code = "\n".join(file.read_text(encoding="utf-8") for file in (ROOT / "Greenhub").rglob("*.py"))
    assert path.name not in code


def test_phase5_roadside_grass_ad_abstract_keeps_unpaired_yields_and_unknown_dom_basis():
    folder = ROOT / "Greenhub" / "data" / "Bigas production + upgrade" / "Feed BMP"
    path = folder / "roadside_grass_residual_AD_2024_abstract_reference.csv"
    rows = _rows(path)
    metadata = json.loads(path.with_suffix(".source.json").read_text(encoding="utf-8"))
    sources = _rows(folder / "source_register.csv")
    manifest = _rows(folder / "dataset_manifest.csv")
    fair_assets = _rows(ROOT / "Greenhub" / "data" / "fair_input_catalog" / "master_input_catalog.csv")

    assert len(rows) == 5
    assert len({row["observation_id"] for row in rows}) == 5
    assert {row["source_id"] for row in rows} == {"SOUZA2024"}
    assert {row["activation_state"] for row in rows} == {"reference_only"}
    yield_row = next(row for row in rows if row["metric"] == "peak_biogas_yield")
    methane_row = next(row for row in rows if row["metric"] == "methane_fraction")
    assert yield_row["reported_value"] == "700"
    assert yield_row["qualifier"].startswith("up to")
    assert "DOM" in yield_row["unit"] and "not verified" in yield_row["basis_or_denominator"]
    assert methane_row["reported_value"] == "49-55"
    assert "not reported in the abstract" in methane_row["notes"]
    assert metadata["doi"] == "10.1016/j.wasman.2024.04.018"
    assert "No reuse license identified" in metadata["license"]
    assert "not configuration-paired" in metadata["limitations"][0]
    assert sum(row["source_id"] == "SOUZA2024" for row in sources) == 1
    assert any(row["filename"] == path.name and row["row_count"] == "5" and row["integration_status"] == "traceable_reference_only_not_runtime_eligible" for row in manifest)
    asset = next(row for row in fair_assets if row["relative_path"].endswith(path.name))
    assert asset["source_ids"] == "SOUZA2024"
    assert asset["source_dois"] == "10.1016/j.wasman.2024.04.018"
    assert asset["observed_rows"] == "5"
    assert asset["readiness"] == "reference_only"

    code = "\n".join(file.read_text(encoding="utf-8") for file in (ROOT / "Greenhub").rglob("*.py"))
    assert path.name not in code


def test_phase6_water_scrubber_abstract_evidence_is_reference_only_and_traceable():
    folder = ROOT / "Greenhub" / "data" / "Bigas production + upgrade" / "Water_Scrubbing"
    path = folder / "farm_scale_vacuum_water_scrubber_2023_reference.csv"
    rows = _rows(path)
    metadata = json.loads(path.with_suffix(".source.json").read_text(encoding="utf-8"))
    sources = _rows(folder / "source_register.csv")
    manifest = _rows(folder / "dataset_manifest.csv")

    assert len(rows) == 9
    assert len({row["record_id"] for row in rows}) == len(rows)
    assert {row["source_id"] for row in rows} == {"SRC008"}
    assert {row["activation_state"] for row in rows} == {"reference_only"}
    assert any(row["metric"] == "reported_energy_consumption_baseline" and row["reported_value"] == "0.8" and row["unit"] == "kWh/Nm3 raw biogas" for row in rows)
    assert any(row["metric"] == "reported_product_methane_purity_threshold" and row["reported_value"] == "97" for row in rows)
    assert any("not methane recovery" in row["notes"] for row in rows)
    assert metadata["doi"] == "10.1016/j.apenergy.2023.121781"
    assert metadata["activation"] == "reference_only"
    assert "not verified" in metadata["license"].lower()
    assert sum(row["source_id"] == "SRC008" for row in sources) == 1
    assert any(row["filename"] == path.name and row["row_count"] == "9" and row["integration_status"] == "traceable_reference_only_not_runtime_eligible" for row in manifest)


def test_phase7_dairy_digestate_pilot_is_not_promoted_to_greenhub_defaults():
    folder = ROOT / "Greenhub" / "data" / "Resource recovery" / "Phosphorus_Recovery"
    path = folder / "dairy_digestate_nf_struvite_pilot_2023_reference.csv"
    rows = _rows(path)
    metadata = json.loads(path.with_suffix(".source.json").read_text(encoding="utf-8"))
    sources = _rows(folder / "source_register.csv")
    manifest = _rows(folder / "dataset_manifest.csv")

    assert len(rows) == 7
    assert len({row["record_id"] for row in rows}) == len(rows)
    assert {row["source_id"] for row in rows} == {"TSARIDOU2023"}
    assert {row["activation_state"] for row in rows} == {"reference_only"}
    assert any(row["metric"] == "retentate_orthophosphate_phosphorus" and row["unit"] == "mg/L as PO4-P" for row in rows)
    assert any(row["metric"] == "struvite_precipitation_molar_ratio_n_mg_p" and row["reported_value"] == "1:1.5:1.5" for row in rows)
    assert metadata["doi"] == "10.30955/gnc2023.00314"
    assert metadata["license"] == "CC BY 4.0 (publisher page terms)"
    assert "not greenhub grass digestate" in metadata["limitations"][0].lower()
    assert sum(row["source_id"] == "TSARIDOU2023" for row in sources) == 1
    assert any(row["filename"] == path.name and row["row_count"] == "7" and row["integration_status"] == "traceable_reference_only_not_runtime_eligible" for row in manifest)
    assert sum(row["filename"] == "source_register.csv" for row in manifest) == 1
    assert any(row["filename"] == "source_register.csv" and row["row_count"] == str(len(sources)) for row in manifest)

    parameter_loader = ROOT / "Greenhub" / "parameters" / "loaders.py"
    references = [
        file for file in (ROOT / "Greenhub").rglob("*.py")
        if path.name in file.read_text(encoding="utf-8")
    ]
    assert references == [parameter_loader]
    loader_text = parameter_loader.read_text(encoding="utf-8")
    assert "The source stream was nanofiltration retentate" in loader_text
    assert "GreenHub NR2 does not include that nanofiltration step" in loader_text


def test_phase7_green_biorefinery_digestate_composition_preserves_source_bases_and_gaps():
    folder = ROOT / "Greenhub" / "data" / "Resource recovery" / "Phosphorus_Recovery"
    path = folder / "green_biorefinery_digestate_nutrient_reference_2022.csv"
    rows = _rows(path)
    metadata = json.loads(path.with_suffix(".source.json").read_text(encoding="utf-8"))
    sources = _rows(folder / "source_register.csv")
    manifest = _rows(folder / "dataset_manifest.csv")
    catalog_path = ROOT / "Greenhub" / "data" / "fair_input_catalog" / "master_input_catalog.csv"
    catalog = _rows(catalog_path)

    assert len(rows) == 59
    assert len({row["observation_id"] for row in rows}) == len(rows)
    assert {row["source_id"] for row in rows} == {"RAVINDRAN2022"}
    assert {row["activation_state"] for row in rows} == {"reference_only"}
    assert sum(row["reported_value"].replace(".", "", 1).isdigit() for row in rows) == 53
    assert {row["basis"] for row in rows if row["parameter"] in {"Moisture", "Total solids", "Ammonia"}} == {"as received"}
    assert {row["basis"] for row in rows if row["parameter"] == "Phosphorus"} == {"dry matter"}
    assert not any(row["material"] == "grass whey digestate" and row["parameter"] == "Aluminium" for row in rows)
    assert any(row["parameter"] == "Phosphorus" and row["material"] == "grass whey digestate" and row["reported_value"] == "11788" for row in rows)
    assert metadata["doi"] == "10.3390/cleantechnol4010003"
    assert metadata["license"] == "CC BY 4.0"
    assert sum(row["source_id"] == "RAVINDRAN2022" for row in sources) == 1
    assert any(row["filename"] == path.name and row["row_count"] == "59" and row["populated_numeric_rows"] == "53" for row in manifest)
    asset = next(row for row in catalog if row["relative_path"].endswith(path.name))
    assert asset["source_ids"] == "RAVINDRAN2022"
    assert asset["source_dois"] == "10.3390/cleantechnol4010003"
    assert asset["observed_rows"] == "59"
    assert asset["readiness"] == "reference_only"
    assert asset["source_metadata_linkage"] == "direct_dataset_path"

    code = "\n".join(file.read_text(encoding="utf-8") for file in (ROOT / "Greenhub").rglob("*.py"))
    assert path.name not in code


def test_phase7_rizzioli_2025_membrane_dataset_is_traceable_and_reference_only():
    folder = ROOT / "Greenhub" / "data" / "Resource recovery" / "Phosphorus_Recovery"
    stream_path = folder / "agricultural_digestate_membrane_recovery_rizzioli_2025_reference.csv"
    recovery_path = folder / "agricultural_digestate_recovery_yields_rizzioli_2025_reference.csv"
    feed_path = folder / "agricultural_digestate_feed_characterization_rizzioli_2025_reference.csv"
    stream_rows = _rows(stream_path)
    recovery_rows = _rows(recovery_path)
    feed_rows = _rows(feed_path)
    feed_metadata = json.loads(feed_path.with_suffix(".source.json").read_text(encoding="utf-8"))
    recovery_metadata = json.loads(recovery_path.with_suffix(".source.json").read_text(encoding="utf-8"))
    metadata = json.loads(stream_path.with_suffix(".source.json").read_text(encoding="utf-8"))
    sources = _rows(folder / "source_register.csv")
    manifest = _rows(folder / "dataset_manifest.csv")

    assert len(stream_rows) == 29
    assert len({row["record_id"] for row in stream_rows}) == 29
    assert len(recovery_rows) == 15
    assert len({row["record_id"] for row in recovery_rows}) == 15
    assert len(feed_rows) == 10
    assert len({row["record_id"] for row in feed_rows}) == 10
    assert next(row for row in feed_rows if row["parameter"] == "orthophosphate phosphorus")["reported_mean"] == "0.21"
    line2_water = next(row for row in recovery_rows if row["configuration"] == "Line 2 UF+RO" and row["analyte_or_stream"].startswith("water"))
    line2_ammonium = next(row for row in recovery_rows if row["configuration"] == "Line 2 UF+RO" and row["analyte_or_stream"] == "ammonium-N")
    assert line2_water["total_recovery_mean_pct"] == "32.75"
    assert line2_water["total_recovery_SD_pct"] == "1.86"
    assert line2_ammonium["recovery_in_RO_retentate_mean_pct"] == "46.50"
    assert any(row["reported_value_status"] == "EC not determined" and row["electrical_conductivity_mS_per_cm"] == "" for row in stream_rows)
    assert metadata["doi"] == "10.1016/j.jclepro.2025.144958"
    assert metadata["evidence_class"] == "B"
    assert "CC BY 4.0" in metadata["data_license"]
    assert metadata["integration_status"].startswith("reference_only")
    assert "not grass-only" in metadata["feedstock_scope"]
    assert feed_metadata["source_id"] == recovery_metadata["source_id"] == metadata["source_id"] == "RIZZIOLI2025"
    assert feed_metadata["source_file"] == feed_path.name
    assert recovery_metadata["source_file"] == recovery_path.name
    assert feed_metadata["doi"] == recovery_metadata["doi"] == metadata["doi"]
    for data_path in (feed_path, stream_path, recovery_path):
        digest = hashlib.sha256(data_path.read_bytes()).hexdigest().upper()
        assert metadata["file_checksums_sha256"][data_path.name] == digest
    assert feed_metadata["sha256"] == hashlib.sha256(feed_path.read_bytes()).hexdigest().upper()
    assert recovery_metadata["sha256"] == hashlib.sha256(recovery_path.read_bytes()).hexdigest().upper()
    assert sum(row["source_id"] == "RIZZIOLI2025" for row in sources) == 1
    assert any(row["filename"] == stream_path.name and row["row_count"] == "29" for row in manifest)
    assert any(row["filename"] == recovery_path.name and row["row_count"] == "15" for row in manifest)
    assert any(row["filename"] == feed_path.name and row["row_count"] == "10" for row in manifest)

    catalog = _rows(ROOT / "Greenhub" / "data" / "fair_input_catalog" / "master_input_catalog.csv")
    for dataset_path in (feed_path, stream_path, recovery_path):
        asset = next(row for row in catalog if row["relative_path"].endswith(dataset_path.name))
        assert asset["source_ids"] == "RIZZIOLI2025"
        assert asset["source_dois"] == "10.1016/j.jclepro.2025.144958"
        assert asset["readiness"] == "reference_only"

    code = "\n".join(file.read_text(encoding="utf-8") for file in (ROOT / "Greenhub").rglob("*.py"))
    assert stream_path.name not in code
    assert recovery_path.name not in code
    assert feed_path.name not in code
