import csv
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "Greenhub" / "data" / "storage"
CSV_PATH = DATA / "grass_clippings_silage_storage_bmp_yeo_2023_abstract_reference.csv"


def _read_rows(path):
    with path.open(encoding="utf-8-sig", newline="") as stream:
        return list(csv.DictReader(stream))


def test_yeo_abstract_storage_records_are_traceable_reference_only_and_do_not_invent_kinetics():
    rows = _read_rows(CSV_PATH)
    assert len(rows) == 11
    assert len({row["record_id"] for row in rows}) == len(rows)
    assert {row["activation_state"] for row in rows} == {"reference_only"}
    assert {row["evidence_class"] for row in rows} == {"B"}
    assert all(row["source_id"] == "SRC-YEO-GRASS-CLIPPINGS-STORAGE-2023" for row in rows)

    endpoints = {
        row["record_id"]: row["value"]
        for row in rows
        if row["value"] not in {"", "not reported"}
    }
    assert endpoints["YEO23-BMP-PP-0D"] == "0.269"
    assert endpoints["YEO23-BMP-PP-180D"] == "0.217"
    assert endpoints["YEO23-NDF-PP-180D"] == "77.12"
    assert endpoints["YEO23-ADF-PP-180D"] == "54.65"
    assert endpoints["YEO23-CP-PP-180D"] == "6.24"
    intermediate = next(row for row in rows if row["record_id"] == "YEO23-BMP-PP-OTHER")
    assert intermediate["value"] == "not reported"
    assert "fitted first-order" in next(row for row in rows if row["record_id"] == "YEO23-BMP-PP-180D")["extraction_note"]

    sidecar = json.loads(CSV_PATH.with_suffix(CSV_PATH.suffix + ".source.json").read_text(encoding="utf-8"))
    assert sidecar["persistent_identifier"] is None
    assert sidecar["activation_state"] == "reference_only"
    assert "not specified" in " ".join(sidecar["limitations"])

    manifest = {row["filename"]: row for row in _read_rows(DATA / "dataset_manifest.csv")}
    assert manifest[CSV_PATH.name]["row_count"] == "11"
    assert manifest[CSV_PATH.name]["integration_status"] == "traceable_reference_only_not_runtime_eligible"
    source_register = {row["source_id"]: row for row in _read_rows(DATA / "source_register.csv")}
    assert source_register["SRC-YEO-GRASS-CLIPPINGS-STORAGE-2023"]["doi_or_stable_identifier"].startswith("No DOI identified")

