import csv
import json
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "Greenhub" / "data" / "Resource recovery" / "Phosphorus_Recovery"
CSV_PATH = DATA / "demarke_struvite_second_year_grass_soil_szymanska_2020_reference.csv"
SOURCE_ID = "SZYMANASKA2020_SECOND_YEAR_FERTILIZER_USE"


def _read_rows(path):
    with path.open(encoding="utf-8-sig", newline="") as stream:
        reader = csv.DictReader(stream)
        rows = list(reader)
        assert reader.fieldnames
        assert all(None not in row for row in rows), "CSV row has more cells than the declared schema"
        return rows


def test_second_year_struvite_dataset_preserves_source_scope_and_does_not_activate():
    rows = _read_rows(CSV_PATH)
    assert len(rows) == 185
    assert len({row["record_id"] for row in rows}) == 185
    assert {row["source_id"] for row in rows} == {SOURCE_ID}
    assert {row["activation_state"] for row in rows} == {"reference_only"}
    assert {row["quality_class"] for row in rows} == {"B"}
    assert all(row["value"] for row in rows)

    by_table = Counter(row["source_table"] for row in rows)
    assert by_table == {
        "Table 1": 12,
        "Table 2": 96,
        "Table 3": 12,
        "Table 4": 48,
        "Results 3.1 / Figure 1": 8,
        "Results 3.3 / Figure 2": 4,
        "Results 3.3 / Figure 4": 5,
    }

    by_id = {row["record_id"]: row for row in rows}
    assert by_id["SZ20-T2-LS-STR_PLUS_N-P-H4"]["value"] == "7.2"
    assert by_id["SZ20-T3-LS-STR_PLUS_N-N-RFE"]["value"] == "681.2"
    assert by_id["SZ20-T4-SL-STR-available_phosphorus_Mehlich3"]["value"] == "192.78"
    assert by_id["SZ20-YIELD-LS-STR_and_STR_PLUS_N"]["value"] == "52.7"
    assert by_id["SZ20-UPTAKE-LS-STR-N"]["value"] == "1397.4"
    assert by_id["SZ20-T2-SL-KTR-N-H2"]["significance_group"] == "ns"
    assert all(row["standard_deviation"] == "" for row in rows)
    assert by_id["SZ20-YIELD-LS-STR_and_STR_PLUS_N"]["treatment"] == "STR_and_STR_PLUS_N"

    sidecar = json.loads(CSV_PATH.with_suffix(CSV_PATH.suffix + ".source.json").read_text(encoding="utf-8"))
    assert sidecar["persistent_identifier"] == "doi:10.3390/en13205342"
    assert sidecar["license"] == "Creative Commons Attribution 4.0 International (CC BY 4.0), as stated in the published article footer."
    assert sidecar["activation_state"] == "reference_only"
    limitations = " ".join(sidecar["limitations"])
    assert "not roadside-grass-derived" in limitations
    assert "not digitized" in limitations
    assert sidecar["runtime_parameter_mapping"] == []

    manifest = {row["filename"]: row for row in _read_rows(DATA / "dataset_manifest.csv")}
    assert manifest[CSV_PATH.name]["row_count"] == "185"
    assert manifest[CSV_PATH.name]["populated_numeric_rows"] == "185"
    sources = {row["source_id"]: row for row in _read_rows(DATA / "source_register.csv")}
    assert sources[SOURCE_ID]["doi_or_stable_id"] == "10.3390/en13205342"

