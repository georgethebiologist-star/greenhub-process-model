import csv
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "Greenhub" / "data" / "Resource recovery" / "Phosphorus_Recovery"
CSV_PATH = DATA / "demarke_struvite_crop_fertilizer_efficiency_szymanska_2019_reference.csv"
SOURCE_ID = "SZYMANASKA2019_FERTILIZER_USE"


def _read_rows(path):
    with path.open(encoding="utf-8-sig", newline="") as stream:
        reader = csv.DictReader(stream)
        rows = list(reader)
        assert reader.fieldnames
        assert all(None not in row for row in rows), "CSV row has more cells than the declared schema"
        return rows


def test_szymanska_struvite_crop_use_data_preserve_basis_and_remain_reference_only():
    rows = _read_rows(CSV_PATH)
    assert len(rows) == 42
    assert len({row["record_id"] for row in rows}) == 42
    assert {row["source_id"] for row in rows} == {SOURCE_ID}
    assert {row["activation_state"] for row in rows} == {"reference_only"}
    assert {row["evidence_class"] for row in rows} == {"B_measured", "B_source_calculated"}

    by_id = {row["record_id"]: row for row in rows}
    assert by_id["SZ19-STRN-SL-GRASS-N-RFE"]["value"] == "112.1"
    assert by_id["SZ19-STRN-LS-GRASS-P-RFE"]["value"] == "97.7"
    assert by_id["SZ19-AP-LS-MAIZE-P-RFE"]["value"] == "100.0"
    assert by_id["SZ19-DOSE-STRN-N"]["value"] == "1.8"
    assert by_id["SZ19-GRASS-ANR-SL"]["treatment"] == "STR_and_STR_plus_N"
    assert by_id["SZ19-GRASS-ANR-SL"]["standard_deviation"] == ""
    assert by_id["SZ19-MAIZE-APR-LS-AP"]["value"] == "26.7"
    assert all(row["standard_deviation"] == "" for row in rows if row["metric"] == "relative_fertilizer_efficiency")

    sidecar = json.loads(CSV_PATH.with_suffix(CSV_PATH.suffix + ".source.json").read_text(encoding="utf-8"))
    assert sidecar["persistent_identifier"] == "doi:10.3390/en12020296"
    assert sidecar["activation_state"] == "reference_only"
    assert "not grass digestate" in " ".join(sidecar["limitations"])
    assert "not digitized" in " ".join(sidecar["limitations"])

    manifest = {row["filename"]: row for row in _read_rows(DATA / "dataset_manifest.csv")}
    assert manifest[CSV_PATH.name]["row_count"] == "42"
    sources = {row["source_id"]: row for row in _read_rows(DATA / "source_register.csv")}
    assert sources[SOURCE_ID]["doi_or_stable_id"] == "10.3390/en12020296"

