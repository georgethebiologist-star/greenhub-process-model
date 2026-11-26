import csv
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "Greenhub" / "data" / "Pre-treatment" / "Feedstock"
CSV_PATH = DATA / "urban_roadside_grass_yield_ifbb_piepenschneider_2016_proceedings_reference.csv"
SOURCE_ID = "SRC-PIEPENSCHNEIDER-URBAN-GRASS-2016-CONFERENCE"


def _read_rows(path):
    with path.open(encoding="utf-8-sig", newline="") as stream:
        reader = csv.DictReader(stream)
        rows = list(reader)
        assert reader.fieldnames
        assert all(None not in row for row in rows), "CSV row has more cells than the declared schema"
        assert all(row.get(None) is None for row in rows)
        return rows


def test_piepenschneider_proceedings_yearly_yields_and_process_evidence_are_traceable():
    rows = _read_rows(CSV_PATH)
    assert len(rows) == 19
    assert len({row["record_id"] for row in rows}) == len(rows)
    assert {row["source_id"] for row in rows} == {SOURCE_ID}
    assert {row["evidence_class"] for row in rows} == {"B_measured"}
    assert {row["activation_state"] for row in rows} == {"reference_only"}

    by_id = {row["record_id"]: row for row in rows}
    assert by_id["PIP16-PROC-YIELD-2013-2CUT"]["value"] == "4.79"
    assert by_id["PIP16-PROC-YIELD-2013-2CUT"]["standard_deviation"] == "3.82"
    assert by_id["PIP16-PROC-YIELD-2014-2CUT"]["value"] == "6.57"
    assert by_id["PIP16-PROC-YIELD-MEAN-4CUT"]["value"] == "3.33"
    assert by_id["PIP16-PROC-CH4-PRESS-FLUID"]["value"] == "269"
    assert by_id["PIP16-PROC-CH4-PRESS-FLUID"]["unit"] == "L_N_per_kg_VS"
    assert by_id["PIP16-PROC-MASH-TIME"]["value"] == "15"
    assert by_id["PIP16-PROC-MASH-WATER"]["value"] == "warm water"
    assert by_id["PIP16-PROC-GROSS-ENERGY-IFBB"]["evidence_kind"] == "source_calculated"

    sidecar = json.loads(CSV_PATH.with_suffix(CSV_PATH.suffix + ".source.json").read_text(encoding="utf-8"))
    assert sidecar["persistent_identifier"] is None
    assert sidecar["activation_state"] == "reference_only"
    assert "269" in " ".join(sidecar["limitations"])
    assert "292" in " ".join(sidecar["limitations"])

    manifest = {row["file_name"]: row for row in _read_rows(DATA / "dataset_manifest.csv")}
    assert manifest[CSV_PATH.name]["row_count"] == "19"
    assert "reference_only" in manifest[CSV_PATH.name]["integration_readiness"]
    sources = {row["source_id"]: row for row in _read_rows(DATA / "source_register.csv")}
    assert sources[SOURCE_ID]["doi_or_stable_identifier"] == "no DOI identified"

