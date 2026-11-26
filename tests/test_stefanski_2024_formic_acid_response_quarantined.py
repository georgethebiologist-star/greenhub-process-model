import csv
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "Greenhub" / "data" / "Pre-treatment" / "Feedstock"
CSV_PATH = DATA_DIR / "grass_liquid_formic_acid_table1_response_stefanski_2024_reference.csv"
SOURCE_ID = "SRC-STEFANSKI-EGF-2024"


def _rows(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as stream:
        reader = csv.DictReader(stream)
        rows = list(reader)
        assert reader.fieldnames
        assert all(None not in row and all(value is not None for value in row.values()) for row in rows)
        return rows


def test_formic_acid_response_values_are_exactly_preserved_but_quarantined():
    rows = _rows(CSV_PATH)
    assert len(rows) == 20
    assert len({row["record_id"] for row in rows}) == 20
    assert {row["source_id"] for row in rows} == {SOURCE_ID}
    assert {row["activation_state"] for row in rows} == {"reference_only"}
    assert {row["basis_status"] for row in rows} == {"unresolved_source_unit_physical_consistency_check_failed"}
    assert {row["replicates"] for row in rows} == {"3"}
    assert {row["metric"] for row in rows} == {
        "dry_matter_extraction_rate",
        "ash_extraction_rate",
        "crude_protein_extraction_rate",
        "true_protein_extraction_rate",
    }
    assert all(row["reported_unit"] == "g kg fresh liquid^-1" for row in rows)

    by_id = {row["record_id"]: row for row in rows}
    assert by_id["STEF24-RESP-CP-FA0"]["value"] == "630"
    assert by_id["STEF24-RESP-TP-FA6"]["value"] == "953"
    assert by_id["STEF24-RESP-DM-FA8"]["sem"] == "6.9"
    assert by_id["STEF24-RESP-ASH-FA10"]["p_quadratic"] == "0.600"

    metadata = json.loads(CSV_PATH.with_suffix(".csv.source.json").read_text(encoding="utf-8"))
    assert metadata["basis_quality_gate"]["status"] == "unresolved_source_unit_physical_consistency_check_failed"
    assert "Do not interpret" in metadata["basis_quality_gate"]["rule"]
    assert metadata["activation_state"] == "reference_only"

    dose_data = json.loads((DATA_DIR / "grass_liquid_formic_acid_precipitation_stefanski_2024_reference.csv.source.json").read_text(encoding="utf-8"))
    assert "companion grass_liquid_formic_acid_table1_response_stefanski_2024_reference.csv" in dose_data["response_table_data"]
    manifest = {row["file_name"]: row for row in _rows(DATA_DIR / "dataset_manifest.csv")}
    assert manifest[CSV_PATH.name]["row_count"] == "20"
    catalog = _rows(ROOT / "Greenhub" / "data" / "fair_input_catalog" / "master_input_catalog.csv")
    asset = next(row for row in catalog if row["relative_path"].endswith(CSV_PATH.name))
    assert asset["source_ids"] == SOURCE_ID
    assert asset["readiness"] == "reference_only"
