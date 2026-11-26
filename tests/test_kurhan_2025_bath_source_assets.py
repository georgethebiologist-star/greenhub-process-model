import csv
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "Greenhub/data/Pre-treatment/Mechanical/kurhan_2025_biorefinery_reference"
SOURCE_ID = "SRC-KURHAN-2025-BATH-01534"


def _rows(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as stream:
        return list(csv.DictReader(stream))


def test_bath_workbooks_are_traceable_reference_only_assets():
    inventory_path = DATA / "kurhan_2025_bath_workbook_sheet_inventory_reference.csv"
    inventory = _rows(inventory_path)
    cell_path = DATA / "kurhan_2025_bath_source_workbook_cells_reference.csv"
    cells = _rows(cell_path)
    assert len(inventory) == 10
    assert len({row["record_id"] for row in inventory}) == len(inventory)
    assert {row["source_id"] for row in inventory} == {SOURCE_ID}
    assert {row["dataset_doi"] for row in inventory} == {"10.15125/BATH-01534"}
    assert {row["activation_state"] for row in inventory} == {"reference_only"}
    assert sum(int(row["formula_cells"]) for row in inventory) == 1224
    assert sum(int(row["cached_formula_values"]) for row in inventory) == 1224
    assert sum(int(row["formula_cells_without_cached_value"]) for row in inventory) == 0
    assert len(cells) == sum(int(row["nonempty_cells"]) for row in inventory)
    assert len({row["record_id"] for row in cells}) == len(cells)
    assert len({(row["workbook_filename"], row["sheet_name"], row["cell_address"]) for row in cells}) == len(cells)
    formula_cells = [row for row in cells if row["cell_type"] == "formula"]
    assert len(formula_cells) == 1224
    assert all(row["formula_expression"].startswith("=") for row in formula_cells)
    assert all(row["cached_formula_value"] != "" for row in formula_cells)
    cell_metadata = json.loads(cell_path.with_suffix(".csv.source.json").read_text(encoding="utf-8"))
    assert cell_metadata["row_count"] == len(cells)
    assert cell_metadata["activation_state"] == "reference_only"
    assert cell_metadata["calculation_connected"] is False

    expected = {
        "Extruder_RSM_Figure_3.xlsx": "4c6f1616f6bf51d1385ec934ed6d21df27f9a21440ee41682782df695f708c11",
        "Extrusion_Single_Factor_Figure_3.xlsx": "237c631d27a90cbf0baf75252a2110e3e20daf02b7edd3c3f1f33cbf79fefa79",
        "Silage_Analysis_Table_1.xlsx": "95e0e4b66c2338baeee722c20f91ba7fbdd2302f68aae314cca9b853de74eaa2",
        "Amino_Acid_Comparative_Figure_2.xlsx": "39bbb237d9d906cce80b5f8c2c56d2145e0f4d790fda3326e62054ad64fc7318",
    }
    for filename, digest in expected.items():
        path = DATA / filename
        metadata = json.loads(path.with_suffix(".source.json").read_text(encoding="utf-8"))
        assert path.stat().st_size < 100_000_000
        assert metadata["source_file"] == filename
        assert metadata["source_id"] == SOURCE_ID
        assert metadata["persistent_identifier"] == "10.15125/BATH-01534"
        assert metadata["article_doi"] == "10.1098/rstb.2024.0161"
        assert "CC BY 4.0" in metadata["license_or_rights"]
        assert metadata["source_data_sha256"] == digest
        assert metadata["activation_state"] == "reference_only"
        assert metadata["calculation_connected"] is False
        assert metadata["parameter_registry_mapping"] is None

    catalog = _rows(ROOT / "Greenhub/data/fair_input_catalog/master_input_catalog.csv")
    by_path = {row["relative_path"].replace("\\", "/"): row for row in catalog}
    for filename in expected:
        path = f"Greenhub/data/Pre-treatment/Mechanical/kurhan_2025_biorefinery_reference/{filename}"
        assert by_path[path]["role"] == "reference_source_workbook"
        assert by_path[path]["maturity"] == "D3"
        assert by_path[path]["activation_state"] == "reference_only"
        assert SOURCE_ID in by_path[path]["source_ids"]
    inventory_catalog_path = (
        "Greenhub/data/Pre-treatment/Mechanical/kurhan_2025_biorefinery_reference/"
        "kurhan_2025_bath_workbook_sheet_inventory_reference.csv"
    )
    assert by_path[inventory_catalog_path]["role"] == "source_workbook_inventory"
    assert "not experimental observations" in by_path[inventory_catalog_path]["runtime_usage_and_precedence"]
    cells_catalog_path = (
        "Greenhub/data/Pre-treatment/Mechanical/kurhan_2025_biorefinery_reference/"
        "kurhan_2025_bath_source_workbook_cells_reference.csv"
    )
    assert by_path[cells_catalog_path]["role"] == "reference_cell_level_source_extract"
    assert by_path[cells_catalog_path]["maturity"] == "D3"
    assert by_path[cells_catalog_path]["activation_state"] == "reference_only"

    mechanical_register = _rows(ROOT / "Greenhub/data/Pre-treatment/Mechanical/source_register.csv")
    assert sum(row["source_id"] == SOURCE_ID for row in mechanical_register) == 1
    local_manifest = _rows(ROOT / "Greenhub/data/Pre-treatment/Mechanical/dataset_manifest.csv")
    assert all(any(row["filename"] == filename for row in local_manifest) for filename in expected)
