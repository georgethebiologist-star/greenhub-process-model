import csv
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "Greenhub" / "data"
FOLDER = DATA / "Protein recovery" / "Isoelectric"
FILENAME = "alfalfa_green_biorefinery_press_and_precipitation_zhou_2023_reference.csv"
SOURCE_ID = "SRC-ZHOU-DTU-THESIS-2023-ALFALFA-PROTEIN"


def _read(path):
    with path.open(encoding="utf-8-sig", newline="") as stream:
        return list(csv.DictReader(stream))


def test_zhou_thesis_reference_preserves_source_scope_and_conflicts():
    path = FOLDER / FILENAME
    rows = _read(path)
    metadata = json.loads(path.with_suffix(".source.json").read_text(encoding="utf-8"))
    by_id = {row["record_id"]: row for row in rows}

    assert len(rows) == metadata["row_count"] == 56
    assert len(by_id) == len(rows)
    assert {row["source_id"] for row in rows} == {SOURCE_ID}
    assert {row["quality_class"] for row in rows} == {"B"}
    assert {row["activation_state"] for row in rows} == {"reference_only"}
    assert by_id["ZHOU23-T12-HCL-PROTEIN_PRECIPITATION"]["value"] == "12.6"
    assert by_id["ZHOU23-T12-HCL-PROTEIN_PRECIPITATION"]["unit"] == "% green juice"
    assert by_id["ZHOU23-T12-LA-LACTIC_ACID"]["value"] == "12.4"
    assert by_id["ZHOU23-MB-11-HYDROCHLORIC_ACID_SOLUTION_ADDED"]["value"] == "135.7"
    assert by_id["ZHOU23-MB-11-HYDROCHLORIC_ACID_SOLUTION_ADDED"]["unit"] == "g solution"
    assert by_id["ZHOU23-MB-02-FEED_WATER_CONTENT"]["value"] == "85.6"
    assert by_id["ZHOU23-MB-03-FEED_DRY_MATTER_MASS"]["value"] == "177.2"
    assert by_id["ZHOU23-MB-16-WET_GREEN_PROTEIN_PELLET_MASS_ACTUAL"]["value"] == "186.2"
    assert by_id["ZHOU23-T12-HCL-LACTIC_ACID"]["value"] == "—"
    assert "not normalized per kg feed" in " ".join(metadata["limitations"])
    assert metadata["calculation_connected"] is False

    local = _read(FOLDER / "dataset_manifest.csv")
    assert any(row["filename"] == FILENAME and row["row_count"] == "56" for row in local)
    global_sources = _read(DATA / "global_audit_package" / "global_source_register.csv")
    global_manifest = _read(DATA / "global_audit_package" / "global_dataset_manifest.csv")
    readiness = _read(DATA / "global_audit_package" / "global_dataset_readiness.csv")
    checksums = _read(DATA / "global_audit_package" / "source_dataset_checksums.csv")
    activation = _read(DATA / "global_audit_package" / "dataset_activation_matrix.csv")
    catalog = _read(DATA / "fair_input_catalog" / "master_input_catalog.csv")
    relative = f"Protein recovery/Isoelectric/{FILENAME}"
    assert sum(row["dataset_path"] == relative and row["source_id"] == SOURCE_ID for row in global_sources) == 1
    assert next(row for row in global_manifest if row["dataset_path"] == relative)["row_count_observed"] == "56"
    readiness_entry = next(row for row in readiness if row["dataset_path"] == relative)
    assert readiness_entry["readiness"] == "D3"
    assert readiness_entry["numeric_rows"] == "50"
    assert readiness_entry["unsourced_numeric_rows"] == "0"
    assert readiness_entry["numeric_rows_missing_exact_location"] == "0"
    assert next(row for row in checksums if row["dataset_path"] == relative)["sha256"] == metadata["sha256_csv"]
    activation_entry = next(row for row in activation if row["dataset_path"] == relative)
    assert activation_entry["integration_eligibility"] == "reference_only"
    assert activation_entry["active"] == "False"
    assert activation_entry["default_eligibility"] == "False"
    asset = next(row for row in catalog if row["relative_path"].endswith(FILENAME))
    assert asset["source_ids"] == SOURCE_ID
    assert asset["readiness"] == "reference_only"
    assert "orbit.dtu.dk" in asset["source_urls"]
    assert asset["source_metadata_status"] == "linked_to_source_register"

