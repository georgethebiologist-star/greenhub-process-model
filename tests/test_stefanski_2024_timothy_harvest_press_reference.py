import csv
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "Greenhub" / "data" / "Pre-treatment" / "Feedstock"
CSV_PATH = DATA_DIR / "timothy_harvest_and_press_liquid_stefanski_2024_reference.csv"
SOURCE_ID = "SRC-STEFANSKI-EGF2024-HARVEST"


def _rows(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as stream:
        reader = csv.DictReader(stream)
        rows = list(reader)
        assert reader.fieldnames
        assert all(None not in row and all(value is not None for value in row.values()) for row in rows)
        return rows


def test_timothy_cut_and_press_liquid_matrix_is_traceable_and_not_activated():
    rows = _rows(CSV_PATH)
    assert len(rows) == 15
    assert len({row["record_id"] for row in rows}) == 15
    assert {row["source_id"] for row in rows} == {SOURCE_ID}
    assert {row["activation_state"] for row in rows} == {"reference_only"}
    assert {row["quality_class"] for row in rows} == {"reference_only"}
    assert {row["evidence_class"] for row in rows} == {"B_measured"}
    assert {row["cut"] for row in rows} == {"first", "second"}
    assert {row["replicates"] for row in rows} == {"3"}

    by_id = {row["record_id"]: row for row in rows}
    assert by_id["STEF24-HARV-C1-20230605-N100"]["grass_dm_g_kg_fresh"] == "299"
    assert by_id["STEF24-HARV-C1-20230605-N100"]["juice_yield_kg_ha"] == "3085"
    assert by_id["STEF24-HARV-C1-20230619-N160"]["juice_n_yield_kg_ha"] == "19.1"
    assert by_id["STEF24-HARV-C2-20230731-N140"]["juice_yield_kg_ha"] == "13983"
    assert by_id["STEF24-HARV-C2-20230807-N140"]["juice_dm_g_kg_liquid"] == "70"
    assert by_id["STEF24-HARV-C2-20230807-N140"]["sem_juice_yield_kg_ha"] == "504.7"

    metadata = json.loads(CSV_PATH.with_suffix(".csv.source.json").read_text(encoding="utf-8"))
    assert metadata["source_id"] == SOURCE_ID
    assert metadata["persistent_identifier"] is None
    assert metadata["rows"] == 15
    assert metadata["activation_state"] == "reference_only"
    assert "not Dutch roadside grass" in " ".join(metadata["limitations"])
    assert "reuse license" in " ".join(metadata["limitations"])

    manifest = {row["file_name"]: row for row in _rows(DATA_DIR / "dataset_manifest.csv")}
    assert manifest[CSV_PATH.name]["row_count"] == "15"
    sources = {row["source_id"]: row for row in _rows(DATA_DIR / "source_register.csv")}
    assert sources[SOURCE_ID]["doi_or_stable_identifier"] == ""
    assert "EGF2024.pdf" in sources[SOURCE_ID]["stable_url"]
    catalog = _rows(ROOT / "Greenhub" / "data" / "fair_input_catalog" / "master_input_catalog.csv")
    asset = next(row for row in catalog if row["relative_path"].endswith(CSV_PATH.name))
    assert asset["source_ids"] == SOURCE_ID
    assert asset["readiness"] == "reference_only"
