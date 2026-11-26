import csv
import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
FEED_DIR = ROOT / "Greenhub" / "data" / "Pre-treatment" / "Feedstock"
BMP_DIR = ROOT / "Greenhub" / "data" / "Bigas production + upgrade" / "Feed BMP"


def _rows(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def test_seasonal_composition_evidence_is_complete_and_traceable():
    rows = _rows(FEED_DIR / "roadside_grass_seasonal_composition_2024.csv")
    source_rows = _rows(FEED_DIR / "source_register.csv")
    manifest = _rows(FEED_DIR / "dataset_manifest.csv")

    assert len(rows) == 72
    assert len({row["observation_id"] for row in rows}) == len(rows)
    assert {row["source_id"] for row in rows} == {"SRC-CZUBASZEK-2024"}
    assert any(row["source_id"] == "SRC-CZUBASZEK-2024" for row in source_rows)
    assert any(row["file_name"] == "roadside_grass_seasonal_composition_2024.csv" for row in manifest)
    assert {row["evidence_class"] for row in rows} == {"literature_measurement"}
    assert {row["activation_state"] for row in rows} == {"reference_only"}

    censored = [row for row in rows if row["data_status"] == "below_detection"]
    assert len(censored) == 2
    assert all(row["value"] == "" and row["standard_deviation"] == "" for row in censored)
    assert all(row["material_state"] == "grass silage" or row["material_state"] == "fresh grass" for row in rows)

    fames = [row for row in rows if row["parameter"].endswith("fatty acid methyl esters")]
    assert len(fames) == 24
    assert {row["unit"] for row in fames} == {"µg/g DM"}
    assert {row["basis"] for row in fames} == {"DM"}
    assert {row["sample_year"] for row in fames} == {"2019"}
    assert {row["source_location"] for row in fames} == {"Table 8 p. 12"}
    assert {row["activation_state"] for row in fames} == {"reference_only"}
    assert all("not equivalent to total crude lipid" in row["transferability"] for row in fames)
    source = json.loads((FEED_DIR / "roadside_grass_seasonal_composition_2024.source.json").read_text(encoding="utf-8"))
    assert source["doi"] == "10.3390/en17071751"
    assert source["license"] == "CC BY 4.0"
    assert "Table 8" in source["source_location"]
    assert "FAME concentration is not equivalent to crude fat" in source["unit_and_basis_notes"]

    relative_path = "Pre-treatment/Feedstock/roadside_grass_seasonal_composition_2024.csv"
    audit_dir = ROOT / "Greenhub" / "data" / "global_audit_package"
    digest = hashlib.sha256((FEED_DIR / "roadside_grass_seasonal_composition_2024.csv").read_bytes()).hexdigest()
    checksums = _rows(audit_dir / "source_dataset_checksums.csv")
    manifest_rows = _rows(audit_dir / "global_dataset_manifest.csv")
    readiness_rows = _rows(audit_dir / "global_dataset_readiness.csv")
    unit_rows = _rows(audit_dir / "global_unit_registry.csv")
    activation_rows = _rows(audit_dir / "dataset_activation_matrix.csv")
    checksum = next(row for row in checksums if row["dataset_path"] == relative_path)
    manifest_row = next(row for row in manifest_rows if row["dataset_path"] == relative_path)
    readiness_row = next(row for row in readiness_rows if row["dataset_path"] == relative_path)
    activation_row = next(row for row in activation_rows if row["dataset_path"] == relative_path)
    assert checksum["sha256"] == digest
    assert manifest_row["row_count_observed"] == "72"
    assert readiness_row["numeric_rows"] == "70"
    assert len([row for row in unit_rows if row["dataset_path"] == relative_path]) == 72
    assert activation_row["calculation_connected"] == "False"
    assert activation_row["active"] == "False"

    master_catalog = _rows(ROOT / "Greenhub" / "data" / "fair_input_catalog" / "master_input_catalog.csv")
    asset = next(row for row in master_catalog if row["relative_path"].endswith("roadside_grass_seasonal_composition_2024.csv"))
    assert asset["observed_rows"] == "72"
    assert asset["readiness"] == "reference_only"
    assert "10.3390/en17071751" in asset["source_dois"].split(";")
    assert asset["license_or_rights"] == "CC BY 4.0"


def test_seasonal_biogas_and_methane_are_not_conflated():
    path = BMP_DIR / "ad_roadside_seasonal_biogas_reference_2024.csv"
    rows = _rows(path)
    source = json.loads((BMP_DIR / "ad_roadside_seasonal_biogas_reference_2024.source.json").read_text(encoding="utf-8"))
    manifest = _rows(BMP_DIR / "dataset_manifest.csv")

    assert len(rows) == 10
    assert len({row["observation_id"] for row in rows}) == len(rows)
    assert source["doi"] == "10.3390/en17071751"
    assert source["license"] == "CC BY 4.0"
    assert {row["activation_state"] for row in rows} == {"reference_only"}
    assert len([row for row in rows if row["parameter"] == "Cumulative specific biogas production"]) == 4
    methane = [row for row in rows if row["parameter"] == "Methane concentration in biogas"]
    assert len(methane) == 6
    assert all(row["unit"] == "%" for row in methane)
    assert all("biogas/kg VS" in row["unit"] for row in rows if row["parameter"] == "Cumulative specific biogas production")
    assert any(row["filename"] == path.name for row in manifest)


def test_phase7_cross_method_digestate_ranges_remain_non_numeric():
    directory = ROOT / "Greenhub" / "data" / "Resource recovery" / "Phosphorus_Recovery"
    rows = _rows(directory / "phase7_cattail_digestate_recovery_reference.csv")
    source_rows = _rows(directory / "source_register.csv")
    manifest = _rows(directory / "dataset_manifest.csv")

    assert len(rows) == 4
    assert len({row["observation_id"] for row in rows}) == 4
    assert all(row["source_id"] == "PETROVIC2021" for row in rows)
    assert all(row["numeric_value"] == "" for row in rows)
    assert {row["activation_state"] for row in rows} == {"reference_only"}
    assert any(row["doi_or_stable_id"] == "10.1016/j.jenvman.2021.112593" for row in source_rows)
    assert any(row["filename"] == "phase7_cattail_digestate_recovery_reference.csv" for row in manifest)
    assert next(row for row in rows if row["parameter"] == "N recovery efficiency")["reported_value"] == "85–92"


def test_brown_roadside_grass_composition_and_supply_are_traceable_reference_data():
    feedstock_dir = ROOT / "Greenhub" / "data" / "Pre-treatment" / "Feedstock"
    composition = _rows(feedstock_dir / "road_verge_composition_2020.csv")
    supply = _rows(feedstock_dir / "road_verge_supply_scenarios_lincolnshire_2020.csv")
    manifest = _rows(feedstock_dir / "dataset_manifest.csv")
    sources = _rows(feedstock_dir / "source_register.csv")

    assert len(composition) == 22
    assert len({row["observation_id"] for row in composition}) == len(composition)
    assert {row["source_id"] for row in composition} == {"SRC-BROWN-2020"}
    assert {row["activation_state"] for row in composition} == {"reference_only"}
    assert {row["geography"] for row in composition} == {"Lincolnshire, England, UK"}
    assert next(row for row in composition if row["observation_id"] == "BROWN2020-FRESH-ASH")["reported_value"] == "17.9"
    assert next(row for row in composition if row["observation_id"] == "BROWN2020-ENSILED-BMPTH-BUSWELL")["reported_value"] == "519"
    censored_sulfur = next(row for row in composition if row["observation_id"] == "BROWN2020-ENSILED-S")
    assert censored_sulfur["reported_value"] == ""
    assert censored_sulfur["data_status"] == "not_detected"
    assert all(row["data_status"] == "author_calculated" and "complete biodegradation" in row["limitations"].lower() for row in composition if "BMPTH" in row["observation_id"])

    assert len(supply) == 21
    assert len({row["scenario_id"] for row in supply}) == len(supply)
    assert {row["activation_state"] for row in supply} == {"reference_only"}
    assert {row["assumed_annual_cuts"] for row in supply} == {"1"}
    assert {row["assumed_fresh_yield_t_per_ha"] for row in supply} == {"12.5"}
    assert next(row for row in supply if row["scenario_id"] == "LINCS-2020-R20-W20")["reported_fresh_grass_tonnes"] == "30089"
    assert all("not measured" in row["limitations"].lower() for row in supply)

    for filename in ("road_verge_composition_2020.csv", "road_verge_supply_scenarios_lincolnshire_2020.csv"):
        assert any(row["file_name"] == filename for row in manifest)
    assert any(row["source_id"] == "SRC-BROWN-2020" for row in sources)
    catalog = _rows(ROOT / "Greenhub" / "data" / "fair_input_catalog" / "master_input_catalog.csv")
    brown_asset = next(row for row in catalog if row["relative_path"].endswith("road_verge_composition_2020.csv"))
    assert "SRC-BROWN-2020" in brown_asset["source_ids"].split(";")
    assert "10.1016/j.biombioe.2020.105570" in brown_asset["source_dois"].split(";")
    assert "https://doi.org/10.1016/j.biombioe.2020.105570" in brown_asset["source_urls"]
    assert brown_asset["observed_rows"] == "22"
    assert brown_asset["readiness"] == "reference_only"
    # A direct global dataset-path record takes precedence over the adjacent sidecar label.
    assert brown_asset["source_metadata_linkage"] == "direct_local_source_record"
    composition_metadata = json.loads((feedstock_dir / "road_verge_composition_2020.source.json").read_text(encoding="utf-8"))
    supply_metadata = json.loads((feedstock_dir / "road_verge_supply_scenarios_lincolnshire_2020.source.json").read_text(encoding="utf-8"))
    assert composition_metadata["doi"] == supply_metadata["doi"] == "10.1016/j.biombioe.2020.105570"
    assert composition_metadata["license"] == supply_metadata["license"] == "CC BY 4.0"
    assert "assumed fresh yield 12.5 tonnes per hectare" in supply_metadata["scenario_basis"]
    code = "\n".join(path.read_text(encoding="utf-8") for path in (ROOT / "Greenhub").rglob("*.py"))
    assert "road_verge_composition_2020.csv" not in code
    assert "road_verge_supply_scenarios_lincolnshire_2020.csv" not in code


def test_zuid_holland_annual_mowing_mass_is_context_only_and_basis_is_not_inferred():
    feedstock_dir = ROOT / "Greenhub" / "data" / "Pre-treatment" / "Feedstock"
    rows = _rows(feedstock_dir / "roadside_grass_availability_evidence.csv")
    sources = _rows(feedstock_dir / "source_register.csv")
    manifest = _rows(feedstock_dir / "dataset_manifest.csv")
    assert len(rows) == 22
    assert len({row["record_id"] for row in rows}) == len(rows)

    mass = next(row for row in rows if row["record_id"] == "AV-ZH-PROVINCE-ANNUAL-MOWED-MASS")
    schedule = next(row for row in rows if row["record_id"] == "AV-ZH-PROVINCE-MOWING-SCHEDULE")
    rws_schedule = next(row for row in rows if row["record_id"] == "AV-RWS-MOWING-FREQUENCY")
    municipal = next(row for row in rows if row["record_id"] == "AV-ZH-MUNICIPAL-GREEN-WASTE-TOTAL")
    previous_inventory = next(row for row in rows if row["record_id"] == "AV-ZH-INVENTORY-PRIOR-46100")
    current_inventory = next(row for row in rows if row["record_id"] == "AV-ZH-INVENTORY-2023-60102")
    assert mass["value"] == "10000"
    assert mass["unit"] == "t/year (mass basis unstated)"
    assert mass["quality_class"] == "B"
    assert mass["activation_state"] == "staged_evidence"
    assert "Do not convert to DM" in mass["limitations"]
    assert schedule["value"] == "2"
    assert schedule["cuts_per_year"] == "2"
    assert "June–July and September–October" in schedule["measurement_basis"]
    assert "numeric field-rest duration" in schedule["limitations"]
    assert rws_schedule["value"] == "1"
    assert rws_schedule["unit"] == "cuts/year (usually; not universal)"
    assert rws_schedule["activation_state"] == "staged_evidence"
    assert "not a route-specific harvest schedule" in rws_schedule["applicability"]
    assert municipal["value"] == "76084"
    assert municipal["unit"] == "t/year (mixed green waste; basis as dataset)"
    assert municipal["quality_class"] == "B"
    assert municipal["activation_state"] == "staged_evidence"
    assert "Do not treat as grass supply" in municipal["limitations"]
    assert previous_inventory["value"] == "46100"
    assert current_inventory["value"] == "60102"
    assert previous_inventory["source_id"] == current_inventory["source_id"] == "SRC-ZH-BIOMASS-INVENTORY-2023"
    assert previous_inventory["activation_state"] == current_inventory["activation_state"] == "staged_evidence"
    assert "do not sum" in previous_inventory["limitations"]
    assert "current inventory found 60,102" in current_inventory["measurement_basis"]
    assert "SRC-ZH-BIOMASS-INVENTORY-2023" in {row["source_id"] for row in sources}
    provincial_source = next(row for row in sources if row["source_id"] == "SRC-ZH-PROVINCIE-BERMGRAS-UNDATED")
    assert provincial_source["doi_or_stable_identifier"] == ""
    assert provincial_source["stable_url"].startswith("https://werkenvoor.zuid-holland.nl/")
    assert any(
        row["file_name"] == "roadside_grass_availability_evidence.csv" and row["row_count"] == "22"
        for row in manifest
    )
    catalog = _rows(ROOT / "Greenhub" / "data" / "fair_input_catalog" / "master_input_catalog.csv")
    asset = next(row for row in catalog if row["relative_path"].endswith("roadside_grass_availability_evidence.csv"))
    metadata = json.loads((feedstock_dir / "roadside_grass_availability_evidence.source.json").read_text(encoding="utf-8"))
    # Preserve the exact global dataset-path linkage even when a local sidecar is also present.
    assert asset["source_metadata_linkage"] == "direct_local_source_record"
    assert "SRC-ZH-PROVINCIE-BERMGRAS-UNDATED" in asset["source_ids"].split(";")
    assert "SRC-ARBOR-UTRECHT-2015" in asset["source_ids"].split(";")
    assert "SRC-RWS-BERMONDERHOUD-CURRENT" in asset["source_ids"].split(";")
    assert metadata["source_file"] == "roadside_grass_availability_evidence.csv"
    assert "0f08e50f-6483-4d62-8a29-16a049e5c5ec" in metadata["persistent_identifier"]
    assert "public domain" in metadata["license"]

    utrecht_collected = next(row for row in rows if row["record_id"] == "AV-ARBOR-UTRECHT-COLLECTED-60000")
    utrecht_uncollected = next(row for row in rows if row["record_id"] == "AV-ARBOR-UTRECHT-UNCOLLECTED-70000")
    utrecht_total = next(row for row in rows if row["record_id"] == "AV-ARBOR-UTRECHT-MAX-POTENTIAL-130000")
    utrecht_schedule = next(row for row in rows if row["record_id"] == "AV-ARBOR-UTRECHT-MOWING-SCHEDULE")
    assert utrecht_collected["value"] == "60000"
    assert utrecht_uncollected["value"] == "70000"
    assert utrecht_total["value"] == "130000"
    assert "not an independent third supply stream" in utrecht_total["limitations"]
    assert "mass basis unstated" in utrecht_collected["unit"]
    assert all(row["quality_class"] == "B" and row["activation_state"] == "staged_evidence"
               for row in (utrecht_collected, utrecht_uncollected, utrecht_total, utrecht_schedule))
    assert utrecht_schedule["cuts_per_year"] == "2"
    assert utrecht_schedule["first_cut_window"] == "May–June"
    assert utrecht_schedule["final_cut_window"] == "September–October"
    assert "SRC-ARBOR-UTRECHT-2015" in {row["source_id"] for row in sources}
    assert "No DOI" in next(row for row in sources if row["source_id"] == "SRC-ARBOR-UTRECHT-2015")["quality_notes"]

    # This is a reported regional maintenance quantity, not a scenario input or a feed default.


def test_german_roadside_yield_management_means_are_traceable_and_not_defaults():
    path = ROOT / "Greenhub/data/Pre-treatment/Feedstock/roadside_verge_yield_management_piepenschneider_2016_reference.csv"
    with path.open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    metadata = json.loads(path.with_suffix(".source.json").read_text(encoding="utf-8"))
    manifest = _rows(ROOT / "Greenhub/data/Pre-treatment/Feedstock/dataset_manifest.csv")
    catalog = _rows(ROOT / "Greenhub/data/fair_input_catalog/master_input_catalog.csv")

    assert len(rows) == 3
    assert {row["source_id"] for row in rows} == {"SRC-PIEPENSCHNEIDER-2016"}
    yields = {row["management_regime"]: float(row["reported_value"]) for row in rows}
    assert yields == {"Repeated mulching": 3.24, "Four-cut harvest": 3.33, "Two-cut harvest": 5.68}
    assert all(row["unit"] == "t DM/ha/year" for row in rows)
    assert all(row["quality_class"] == "B" and row["activation_state"] == "reference_only" for row in rows)
    assert "No open reuse license identified" in metadata["license_status"]
    assert "not Dutch" in metadata["limitations"][0]
    assert any(row["file_name"] == path.name and row["row_count"] == "3" for row in manifest)
    asset = next(row for row in catalog if row["relative_path"].endswith(path.name))
    assert asset["source_ids"] == "SRC-PIEPENSCHNEIDER-2016"
    assert asset["source_dois"] == "10.1016/j.biombioe.2015.12.012"
    assert asset["readiness"] == "reference_only"
