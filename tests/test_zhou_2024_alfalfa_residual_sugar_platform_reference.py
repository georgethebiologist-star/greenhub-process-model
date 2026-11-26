import csv
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "Greenhub" / "data"
FOLDER = DATA / "Pre-treatment" / "Thermal_Enzymatic"
FILENAME = "alfalfa_press_residue_sugar_platform_zhou_2024_abstract_reference.csv"
SOURCE_ID = "SRC-ZHOU-2024-ALFALFA-RESIDUAL-SUGAR"


def _read(path):
    with path.open(encoding="utf-8-sig", newline="") as stream:
        return list(csv.DictReader(stream))


def test_zhou_2024_residual_sugar_data_are_traceable_and_reference_only():
    path = FOLDER / FILENAME
    rows = _read(path)
    metadata = json.loads(path.with_suffix(".source.json").read_text(encoding="utf-8"))
    by_id = {row["record_id"]: row for row in rows}
    assert len(rows) == metadata["row_count"] == 16
    assert len(by_id) == len(rows)
    assert {row["source_id"] for row in rows} == {SOURCE_ID}
    assert {row["quality_class"] for row in rows} == {"B"}
    assert {row["activation_state"] for row in rows} == {"reference_only"}
    assert by_id["ZHOU24-HYDROLYSIS-GLUCOSE-CONCENTRATION"]["value"] == "35.2"
    assert by_id["ZHOU24-HYDROLYSIS-GLUCOSE-CONCENTRATION"]["unit"] == "g/L"
    assert by_id["ZHOU24-BROWN-JUICE-LACTIC-ACID-BASELINE"]["value"] == "12.8"
    assert by_id["ZHOU24-BROWN-JUICE-LACTIC-ACID-70-VOL"]["value"] == "28.8"
    assert "abstract-level" in " ".join(metadata["limitations"])
    assert "not GreenHub roadside-grass" in " ".join(metadata["limitations"])
    assert metadata["calculation_connected"] is False

    manifest = _read(FOLDER / "dataset_manifest.csv")
    assert any(row["filename"] == FILENAME and row["row_count"] == "16" for row in manifest)
    audit = DATA / "global_audit_package"
    relative = f"Pre-treatment/Thermal_Enzymatic/{FILENAME}"
    source = next(row for row in _read(audit / "global_source_register.csv") if row["dataset_path"] == relative)
    assert source["source_id"] == SOURCE_ID
    assert source["doi_or_stable_id"] == "10.1016/j.indcrop.2023.117927"
    readiness = next(row for row in _read(audit / "global_dataset_readiness.csv") if row["dataset_path"] == relative)
    assert readiness["numeric_rows"] == "16"
    assert readiness["unsourced_numeric_rows"] == "0"
    checksum = next(row for row in _read(audit / "source_dataset_checksums.csv") if row["dataset_path"] == relative)
    assert checksum["sha256"] == metadata["sha256_csv"]
    activation = next(row for row in _read(audit / "dataset_activation_matrix.csv") if row["dataset_path"] == relative)
    assert activation["integration_eligibility"] == "reference_only"
    assert activation["active"] == "False"
    asset = next(row for row in _read(DATA / "fair_input_catalog" / "master_input_catalog.csv") if row["relative_path"].endswith(FILENAME))
    assert asset["source_ids"] == SOURCE_ID
    assert asset["source_dois"] == "10.1016/j.indcrop.2023.117927"
    assert asset["readiness"] == "reference_only"
