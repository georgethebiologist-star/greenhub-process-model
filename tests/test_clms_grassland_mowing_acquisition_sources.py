import csv
import hashlib
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "Greenhub" / "data"
FOLDER = DATA / "Pre-treatment" / "Feedstock"
SOURCE_IDS = {
    "SRC-CLMS-GRAME-GRASSLAND-MOWING-EVENTS": "10.2909/114e8cae-1cd7-4adc-8c5f-a04863fc6af9",
    "SRC-CLMS-GRAMD-GRASSLAND-MOWING-DATES": "10.2909/660d00f1-c6de-4db6-9979-0be124ceb7f0",
}


def _rows(path: Path):
    with path.open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def test_clms_mowing_products_are_registered_as_metadata_leads_only():
    local_source_rows = _rows(FOLDER / "source_register.csv")
    local_sources = {row["source_id"]: row for row in local_source_rows}
    for source_id, doi in SOURCE_IDS.items():
        row = local_sources[source_id]
        assert row["doi_or_stable_identifier"] == doi
        assert row["stable_url"] == f"https://doi.org/{doi}"
        assert "no raster payload" in row["quality_notes"]
        assert "not roadside-specific" in row["quality_notes"]
        assert "reference metadata only" in row["quality_notes"].lower()

    local_manifest = {row["file_name"]: row for row in _rows(FOLDER / "dataset_manifest.csv")}
    source_row = local_manifest["source_register.csv"]
    assert source_row["row_count"] == str(len(local_source_rows))
    assert "no product raster payload is staged" in source_row["description"]

    global_source = [
        row for row in _rows(DATA / "global_audit_package/global_source_register.csv")
        if row["dataset_path"] == "Pre-treatment/Feedstock/source_register.csv"
        and row["source_id"] in SOURCE_IDS
    ]
    assert {row["source_id"] for row in global_source} == set(SOURCE_IDS)

    local_register_path = FOLDER / "source_register.csv"
    checksum = hashlib.sha256(local_register_path.read_bytes()).hexdigest()
    checksum_row = next(
        row for row in _rows(DATA / "global_audit_package/source_dataset_checksums.csv")
        if row["dataset_path"] == "Pre-treatment/Feedstock/source_register.csv"
    )
    assert checksum_row["sha256"] == checksum

