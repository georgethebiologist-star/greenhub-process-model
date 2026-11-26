import csv
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "Greenhub" / "data"
FOLDER = DATA / "Pre-treatment" / "Thermal_Enzymatic"
FILENAME = "alfalfa_sodium_chlorite_and_sugar_fermentation_tables_zhou_2023_reference.csv"
SOURCE_ID = "SRC-ZHOU-DTU-THESIS-2023-ALFALFA-PROTEIN"


def _read(path):
    with path.open(encoding="utf-8-sig", newline="") as stream:
        return list(csv.DictReader(stream))


def test_zhou_2023_detailed_tables_are_traceable_reference_only_data():
    path = FOLDER / FILENAME
    rows = _read(path)
    metadata = json.loads(path.with_suffix(".source.json").read_text(encoding="utf-8"))
    by_id = {row["record_id"]: row for row in rows}
    assert len(rows) == metadata["row_count"] == 207
    assert len(by_id) == len(rows)
    assert metadata["numeric_row_count"] == 197
    assert {row["source_id"] for row in rows} == {SOURCE_ID}
    assert {row["quality_class"] for row in rows} == {"B"}
    assert {row["activation_state"] for row in rows} == {"reference_only"}

    # Verify source transcription, not a fitted or normalized GreenHub value.
    assert by_id["ZHOU23-T42-SC6-DELIGNIFICATION"]["value"] == "79.57"
    assert "SD=1.55" in by_id["ZHOU23-T42-SC6-DELIGNIFICATION"]["uncertainty"]
    assert by_id["ZHOU23-T42-SC6-DELIGNIFICATION"]["unit"] == "%"
    assert by_id["ZHOU23-T42-SC0-SOLID_RECOVERY"]["value"] == "na"
    assert by_id["ZHOU23-T41-PRESS2-PROTEIN"]["value"] == "17.27"
    assert by_id["ZHOU23-T41-PRESS2-PROTEIN"]["unit"] == "g/100 g DM"
    assert by_id["ZHOU23-T41-PRESS2-TEMPERATURE_AT_STEP_END"]["value"] == "37 - 47"
    assert by_id["ZHOU23-T41-RAW-PULP_RECOVERY"]["value"] == "-"
    assert by_id["ZHOU23-T43-ASH70-MAXIMUM_LACTIC_ACID_CONCENTRATION"]["value"] == "28.8"
    assert by_id["ZHOU23-T44-ASH50-XYLOSE_CONSUMPTION"]["value"] == "4.7"
    assert "every 2 h" in by_id["ZHOU23-T43-ASH15-INITIAL_GLUCOSE"]["condition_scope"]
    assert "every 6 h" in by_id["ZHOU23-T44-ASH15-INITIAL_GLUCOSE"]["condition_scope"]
    assert "exact n is not reported" in rows[0]["replicate_count"]
    assert metadata["calculation_connected"] is False
    assert "not Dutch roadside/VARTA grass" in " ".join(metadata["limitations"])
    assert "No explicit reuse license identified" in metadata["license_or_rights"]

    manifest = _read(FOLDER / "dataset_manifest.csv")
    assert any(row["filename"] == FILENAME and row["row_count"] == "207" for row in manifest)
    audit = DATA / "global_audit_package"
    relative = f"Pre-treatment/Thermal_Enzymatic/{FILENAME}"
    source = next(row for row in _read(audit / "global_source_register.csv") if row["dataset_path"] == relative)
    assert source["source_id"] == SOURCE_ID
    assert source["doi_or_stable_id"] == "10.1016/j.indcrop.2023.117927"
    readiness = next(row for row in _read(audit / "global_dataset_readiness.csv") if row["dataset_path"] == relative)
    assert readiness["numeric_rows"] == "197"
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
