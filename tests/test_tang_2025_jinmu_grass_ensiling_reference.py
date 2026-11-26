import csv
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "Greenhub" / "data"
FOLDER = DATA / "storage"
FILENAME = "jinmu_grain_grass_silage_storage_time_tang_2025_reference.csv"
SOURCE_ID = "SRC-TANG-JINMU-GRASS-ENSILING-2025"


def _read(path: Path):
    with path.open(encoding="utf-8-sig", newline="") as stream:
        return list(csv.DictReader(stream))


def test_tang_silage_storage_time_series_is_traceable_and_not_activated():
    path = FOLDER / FILENAME
    rows = _read(path)
    metadata = json.loads(path.with_suffix(".source.json").read_text(encoding="utf-8"))
    by_id = {row["record_id"]: row for row in rows}

    assert len(rows) == metadata["row_count"] == 72
    assert len(by_id) == len(rows)
    assert {row["source_id"] for row in rows} == {SOURCE_ID}
    assert {row["quality_class"] for row in rows} == {"B"}
    assert {row["activation_state"] for row in rows} == {"reference_only"}
    assert all(row["replicate_count"] == "5 bags per storage time" for row in rows)
    assert {row["storage_days"] for row in rows} == {"0", "3", "7", "15", "30", "60"}

    assert by_id["TANG25-2-PH-000D"]["value"] == "6.16"
    assert by_id["TANG25-2-PH-060D"]["value"] == "4.01"
    assert by_id["TANG25-2-AMMONIA_NITROGEN_TO_TOTAL_NITROGEN-060D"]["value"] == "5.08"
    assert by_id["TANG25-2-LACTIC_ACID-060D"]["value"] == "6.57"
    assert by_id["TANG25-2-PROPIONIC_ACID-000D"]["value"] == "ND"
    assert by_id["TANG25-2-BUTYRIC_ACID-060D"]["value"] == "ND"
    assert "not zero" in by_id["TANG25-2-BUTYRIC_ACID-060D"]["limitations"]
    assert by_id["TANG25-1-CRUDE_PROTEIN-000D"]["unit"] == "unit not stated in source table"
    assert by_id["TANG25-1-CRUDE_PROTEIN-000D"]["basis"] == "not stated in source table"
    assert "was inferred" in by_id["TANG25-1-CRUDE_PROTEIN-000D"]["limitations"]
    assert all("not a Dutch roadside-grass parameter source" in row["transferability"] for row in rows)

    assert metadata["calculation_connected"] is False
    assert metadata["license"].endswith("CC BY 4.0), stated on the article page.")
    assert metadata["row_count"] == 72
    assert sum(row["value"] != "ND" for row in rows) == 65

    sources = _read(FOLDER / "source_register.csv")
    manifests = _read(FOLDER / "dataset_manifest.csv")
    global_sources = _read(DATA / "global_audit_package" / "global_source_register.csv")
    global_manifest = _read(DATA / "global_audit_package" / "global_dataset_manifest.csv")
    readiness = _read(DATA / "global_audit_package" / "global_dataset_readiness.csv")
    checksums = _read(DATA / "global_audit_package" / "source_dataset_checksums.csv")
    catalog = _read(DATA / "fair_input_catalog" / "master_input_catalog.csv")

    assert any(row["source_id"] == SOURCE_ID and row["doi_or_stable_identifier"] == "10.3390/microorganisms13091973" for row in sources)
    assert any(row["filename"] == FILENAME and row["row_count"] == "72" for row in manifests)
    relative = f"storage/{FILENAME}"
    assert sum(row["dataset_path"] == relative for row in global_sources) == 1
    global_entry = next(row for row in global_manifest if row["dataset_path"] == relative)
    assert global_entry["row_count_observed"] == "72"
    assert global_entry["detected_readiness"] == "D3"
    readiness_entry = next(row for row in readiness if row["dataset_path"] == relative)
    assert readiness_entry["numeric_rows"] == "65"
    assert readiness_entry["numeric_rows_missing_exact_location"] == "0"
    checksum = next(row for row in checksums if row["dataset_path"] == relative)
    assert checksum["sha256"] == metadata["sha256_csv"]
    asset = next(row for row in catalog if row["relative_path"].endswith(FILENAME))
    assert asset["source_ids"] == SOURCE_ID
    assert asset["readiness"] == "reference_only"
