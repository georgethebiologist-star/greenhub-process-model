import csv
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "Greenhub" / "data"
FOLDER = DATA / "storage"
FILENAME = "wet_green_protein_paste_storage_santamaria_stodkilde_2019_2021_reference.csv"
REPORT_ID = "SRC-SANTAMARIA-STODKILDE-WET-PASTE-2019"
ABSTRACT_ID = "SRC-OKNET-ECOFEED-WET-PROTEIN-SHELF-LIFE-2021"


def _read(path: Path):
    with path.open(encoding="utf-8-sig", newline="") as stream:
        return list(csv.DictReader(stream))


def test_wet_protein_paste_storage_reference_is_scoped_and_traceable():
    path = FOLDER / FILENAME
    rows = _read(path)
    metadata = json.loads(path.with_suffix(".source.json").read_text(encoding="utf-8"))
    source_register = _read(FOLDER / "source_register.csv")
    local_manifest = _read(FOLDER / "dataset_manifest.csv")
    global_sources = _read(DATA / "global_audit_package" / "global_source_register.csv")
    global_manifest = _read(DATA / "global_audit_package" / "global_dataset_manifest.csv")
    readiness = _read(DATA / "global_audit_package" / "global_dataset_readiness.csv")
    checksums = _read(DATA / "global_audit_package" / "source_dataset_checksums.csv")
    catalog = _read(DATA / "fair_input_catalog" / "master_input_catalog.csv")

    assert len(rows) == metadata["row_count"] == 17
    assert len({row["record_id"] for row in rows}) == len(rows)
    assert {row["source_id"] for row in rows} == {REPORT_ID, ABSTRACT_ID}
    assert {row["quality_class"] for row in rows} == {"B"}
    assert {row["activation_state"] for row in rows} == {"reference_only"}
    assert all("not roadside" in row["transferability"] for row in rows)

    by_id = {row["record_id"]: row for row in rows}
    assert by_id["SST19-ALFALFA-DM-T0"]["value"] == "31"
    assert by_id["SST19-RED-CLOVER-OM-T0"]["value"] == "19"
    assert by_id["SST19-RYEGRASS-PH-4C-12M"]["value"] == "3.8"
    assert by_id["SST21-CG-CP-T0"]["value"] == "48.5"
    assert by_id["SST21-CG-MET-T0"]["value"] == "10.8"
    assert by_id["SST21-CG-LYS-T0"]["value"] == "31.4"
    assert by_id["SST21-CG-STABLE-24C"]["value"] == "2"
    assert by_id["SST21-CG-STABLE-4C"]["value"] == "3"
    assert "does not define the stability criterion" in by_id["SST21-CG-STABLE-24C"]["limitations"]
    assert "no unreported values were digitized" in by_id["SST21-CG-TESTED-STORAGE-DESIGN"]["limitations"]

    assert metadata["calculation_connected"] is False
    assert "No explicit open data-reuse license" in metadata["license_or_rights"]
    assert "does not reconcile arithmetically" in " ".join(metadata["limitations"])
    assert {row["source_id"] for row in source_register if row["source_id"] in {REPORT_ID, ABSTRACT_ID}} == {REPORT_ID, ABSTRACT_ID}
    assert any(row["filename"] == FILENAME and row["row_count"] == "17" for row in local_manifest)

    relative = f"storage/{FILENAME}"
    assert sum(row["dataset_path"] == relative for row in global_sources) == 2
    global_entry = next(row for row in global_manifest if row["dataset_path"] == relative)
    assert global_entry["row_count_observed"] == "17"
    assert global_entry["detected_readiness"] == "D3"
    readiness_entry = next(row for row in readiness if row["dataset_path"] == relative)
    assert readiness_entry["numeric_rows"] == "14"
    assert readiness_entry["numeric_rows_missing_exact_location"] == "0"

    dataset_checksum = next(row for row in checksums if row["dataset_path"] == relative)
    assert dataset_checksum["sha256"] == metadata["sha256_csv"]
    asset = next(row for row in catalog if row["relative_path"].endswith(FILENAME))
    assert set(asset["source_ids"].split(";")) == {REPORT_ID, ABSTRACT_ID}
    assert asset["readiness"] == "reference_only"
