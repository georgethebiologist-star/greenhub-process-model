import csv
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
FEEDSTOCK = ROOT / "Greenhub/data/Pre-treatment/Feedstock"
SOURCE_ID = "SRC-DUCZKOWSKA-2026-ROAD-BIOMASS"


def _rows(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as stream:
        return list(csv.DictReader(stream))


def test_published_spatial_supply_estimates_are_traceable_and_not_runtime_inputs():
    supply_path = FEEDSTOCK / "roadside_biomass_municipality_scenarios_duczkowska_2026_reference.csv"
    supply = _rows(supply_path)
    assert len(supply) == 35
    assert len({row["record_id"] for row in supply}) == len(supply)
    assert {row["source_id"] for row in supply} == {SOURCE_ID}
    assert {row["quality_class"] for row in supply} == {"B"}
    assert {row["maturity_class"] for row in supply} == {"D3"}
    assert {row["activation_state"] for row in supply} == {"reference_only"}

    mass_rows = [row for row in supply if row["metric"] == "mowed_roadside_biomass"]
    assert len(mass_rows) == 10
    assert {row["reported_unit"] for row in mass_rows} == {"Gg/a"}
    assert {row["normalized_unit"] for row in mass_rows} == {"t/a"}
    assert all(float(row["normalized_value"]) == 1000 * float(row["reported_value"]) for row in mass_rows)
    assert all("basis" in row and row["basis"] for row in mass_rows)
    assert all("not Dutch" in row["limitations"] for row in mass_rows)

    useful = [row for row in supply if row["metric"] == "useful_energy_potential"]
    assert sum(float(row["reported_value"]) for row in useful if row["reported_pair_position"] == "A") == 95.2
    assert sum(float(row["reported_value"]) for row in useful if row["reported_pair_position"] == "B") == 142.7

    metadata = json.loads(supply_path.with_suffix(".csv.source.json").read_text(encoding="utf-8"))
    assert metadata["doi"] == "10.3390/en19174185"
    assert metadata["calculation_connected"] is False
    assert metadata["parameter_registry_mapping"] is None
    assert metadata["quality_class"] == "B"


def test_reported_capacity_allocation_cases_preserve_missing_configuration():
    capacity_path = FEEDSTOCK / "roadside_biomass_collection_capacity_scenarios_duczkowska_2026_reference.csv"
    rows = _rows(capacity_path)
    assert len(rows) == 3
    assert len({row["record_id"] for row in rows}) == 3
    assert {row["activation_state"] for row in rows} == {"reference_only"}
    by_capacity = {int(row["south_center_capacity_t"]): row for row in rows}
    assert by_capacity[3000]["nodes_assigned_to_south"] == "25"
    assert by_capacity[5000]["nodes_assigned_to_south"] == "36"
    assert by_capacity[5875]["north_center_capacity_t"] == "5875"
    assert by_capacity[5875]["nodes_assigned_to_south"] == "41"
    assert by_capacity[3000]["north_center_capacity_t"] == ""
    assert by_capacity[5000]["north_center_capacity_t"] == ""


def test_spatial_reference_datasets_are_indexed_as_external_scenarios():
    catalog = _rows(ROOT / "Greenhub/data/fair_input_catalog/master_input_catalog.csv")
    by_path = {row["relative_path"].replace("\\", "/"): row for row in catalog}
    for filename in (
        "roadside_biomass_municipality_scenarios_duczkowska_2026_reference.csv",
        "roadside_biomass_collection_capacity_scenarios_duczkowska_2026_reference.csv",
    ):
        path = f"Greenhub/data/Pre-treatment/Feedstock/{filename}"
        assert by_path[path]["role"] == "spatial_supply_scenario_reference"
        assert by_path[path]["readiness"] == "reference_only"
        assert by_path[path]["maturity"] == "D3"
        assert by_path[path]["activation_state"] == "reference_only"
        assert SOURCE_ID in by_path[path]["source_ids"]

    local_register = _rows(FEEDSTOCK / "source_register.csv")
    assert sum(row["source_id"] == SOURCE_ID for row in local_register) == 1
    manifest = _rows(FEEDSTOCK / "dataset_manifest.csv")
    assert all(any(row["file_name"] == filename for row in manifest) for filename in (
        "roadside_biomass_municipality_scenarios_duczkowska_2026_reference.csv",
        "roadside_biomass_collection_capacity_scenarios_duczkowska_2026_reference.csv",
    ))
