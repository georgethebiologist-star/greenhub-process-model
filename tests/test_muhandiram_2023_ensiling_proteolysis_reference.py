import csv
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "Greenhub" / "data"
FOLDER = DATA / "storage"
FILENAME = "cultivated_ryegrass_festulolium_ensiling_proteolysis_muhandiram_2023_reference.csv"
SOURCE_ID = "SRC-MUHANDIRAM-GRASS-ENSILING-2023-REFERENCE"


def _read(path: Path):
    with path.open(encoding="utf-8-sig", newline="") as stream:
        return list(csv.DictReader(stream))


def test_muhandiram_tables_are_traceable_and_remain_reference_only():
    path = FOLDER / FILENAME
    rows = _read(path)
    metadata = json.loads(path.with_suffix(".source.json").read_text(encoding="utf-8"))
    by_id = {row["record_id"]: row for row in rows}

    assert len(rows) == metadata["row_count"] == 264
    assert len(by_id) == len(rows)
    assert {row["source_id"] for row in rows} == {SOURCE_ID}
    assert {row["quality_class"] for row in rows} == {"B"}
    assert {row["activation_state"] for row in rows} == {"reference_only"}
    assert metadata["calculation_connected"] is False
    assert metadata["license"].endswith("CC BY 4.0), stated on the open-access article.")

    assert by_id["MUH23-T2-2-WSC-cultivar_time_series-Ryegrass-00"]["value"] == "144.8"
    assert by_id["MUH23-T2-2-WSC-cultivar_time_series-Ryegrass-06"]["value"] == "37.7"
    assert by_id["MUH23-T2-2-SOLUBLE_N-cultivar_time_series-LpXFg-06"]["value"] == "605"
    assert by_id["MUH23-T3-4-PH-cultivar_time_series-LpXFg-02"]["source_annotation"] == "B"
    assert by_id["MUH23-T3-4-WSC-pooled_mean_time_series-Mean-06"]["value"] == "45.6"
    assert by_id["MUH23-T3-4-AMMONIA-N-pooled_mean_time_series-Mean-06"]["value"] == "68.3"
    assert by_id["MUH23-T3-4-SOLUBLE_N-pooled_mean_time_series-Mean-06"]["elapsed_hours_from_ensiling"] == "2160"
    assert all("not Dutch roadside/VARTA or GreenHub feed" in row["limitations"] for row in rows)
    assert all(row["replicates_or_sample_design"] for row in rows)

    sources = _read(FOLDER / "source_register.csv")
    manifests = _read(FOLDER / "dataset_manifest.csv")
    global_sources = _read(DATA / "global_audit_package" / "global_source_register.csv")
    global_manifest = _read(DATA / "global_audit_package" / "global_dataset_manifest.csv")
    readiness = _read(DATA / "global_audit_package" / "global_dataset_readiness.csv")
    checksums = _read(DATA / "global_audit_package" / "source_dataset_checksums.csv")
    catalog = _read(DATA / "fair_input_catalog" / "master_input_catalog.csv")

    assert any(row["source_id"] == SOURCE_ID and row["doi_or_stable_identifier"] == "10.1002/fes3.475" for row in sources)
    assert any(row["filename"] == FILENAME and row["row_count"] == "264" for row in manifests)
    relative = f"storage/{FILENAME}"
    assert sum(row["dataset_path"] == relative for row in global_sources) == 1
    global_entry = next(row for row in global_manifest if row["dataset_path"] == relative)
    assert global_entry["row_count_observed"] == "264"
    assert global_entry["detected_readiness"] == "D3"
    readiness_entry = next(row for row in readiness if row["dataset_path"] == relative)
    assert readiness_entry["numeric_rows"] == "264"
    assert readiness_entry["numeric_rows_missing_exact_location"] == "0"
    checksum = next(row for row in checksums if row["dataset_path"] == relative)
    assert checksum["sha256"] == metadata["sha256_csv"]
    asset = next(row for row in catalog if row["relative_path"].endswith(FILENAME))
    assert asset["source_ids"] == SOURCE_ID
    assert asset["readiness"] == "reference_only"
