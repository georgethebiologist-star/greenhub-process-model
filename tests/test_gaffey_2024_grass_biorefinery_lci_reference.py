import csv
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "Greenhub" / "data" / "lca" / "source_data"
CSV_PATH = DATA_DIR / "gaffey_2024_grass_biorefinery_lci_table3_reference.csv"
SOURCE_ID = "SRC-GAFFEY-2024-GBR-LCA-TABLE3"


def _rows(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as stream:
        reader = csv.DictReader(stream)
        rows = list(reader)
        assert reader.fieldnames
        assert all(None not in row and all(value is not None for value in row.values()) for row in rows)
        return rows


def test_gaffey_table3_lci_is_traceable_and_keeps_credits_distinct_from_flows():
    rows = _rows(CSV_PATH)
    assert len(rows) == 42
    assert len({row["record_id"] for row in rows}) == 42
    assert {row["source_id"] for row in rows} == {SOURCE_ID}
    assert {row["activation_state"] for row in rows} == {"reference_only"}
    assert {row["quality_class"] for row in rows} == {"B"}
    assert {row["reference_flow"] for row in rows} == {"1_t_LPC_CP"}
    assert {row["F1TP1"] == "" for row in rows} == {False}

    by_id = {row["record_id"]: row for row in rows}
    assert by_id["GAFFEY24-T3-016"]["F1TP1"] == "39.87"
    assert by_id["GAFFEY24-T3-017"]["unit_as_published"] == "kW"
    assert by_id["GAFFEY24-T3-017"]["F1TP1"] == "4625"
    assert by_id["GAFFEY24-T3-023"]["F1TP1"] == "-6129"
    assert by_id["GAFFEY24-T3-023"]["sign_interpretation"] == "negative_substitution_credit"
    assert by_id["GAFFEY24-T3-026"]["unit_as_published"] == "kg_P2O5"
    assert by_id["GAFFEY24-T3-038"]["unit_as_published"] == "kgNO3"
    assert by_id["GAFFEY24-T3-042"]["F2TP2"] == "1732"

    metadata = json.loads(CSV_PATH.with_suffix(".csv.source.json").read_text(encoding="utf-8"))
    assert metadata["persistent_identifier"] == "doi:10.1016/j.scitotenv.2024.175035"
    assert metadata["functional_unit"].startswith("1 t dry matter")
    assert metadata["activation_state"] == "reference_only"
    assert "403" in metadata["supplementary_data_status"]
    assert "not negative physical" in metadata["sign_convention"]

    sources = {row["source_id"]: row for row in _rows(ROOT / "Greenhub" / "data" / "lca" / "source_register.csv")}
    assert sources[SOURCE_ID]["doi_or_stable_identifier"] == "10.1016/j.scitotenv.2024.175035"
    catalog = _rows(ROOT / "Greenhub" / "data" / "fair_input_catalog" / "master_input_catalog.csv")
    asset = next(row for row in catalog if row["relative_path"].endswith(CSV_PATH.name))
    assert asset["source_ids"] == SOURCE_ID
    assert asset["source_dois"] == "10.1016/j.scitotenv.2024.175035"
    assert asset["readiness"] == "reference_only"
    assert asset["source_metadata_status"] == "linked_to_source_register"
