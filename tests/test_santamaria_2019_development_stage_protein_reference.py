import csv
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "Greenhub" / "data" / "Protein recovery" / "Lactic_Acid"
CSV_PATH = DATA / "forage_development_stage_lactic_fermentation_protein_yield_santamaria_2019_reference.csv"
SOURCE_ID = "SRC-SANTAMARIA-2019-DEVELOPMENT-STAGE"


def _read_rows(path):
    with path.open(encoding="utf-8-sig", newline="") as stream:
        reader = csv.DictReader(stream)
        rows = list(reader)
        assert reader.fieldnames
        assert all(None not in row for row in rows), "CSV row has more cells than the declared schema"
        return rows


def test_abstract_stage_yield_ranges_keep_denominators_and_remain_reference_only():
    rows = _read_rows(CSV_PATH)
    assert len(rows) == 5
    assert len({row["observation_id"] for row in rows}) == 5
    assert {row["source_id"] for row in rows} == {SOURCE_ID}
    assert {row["quality_class"] for row in rows} == {"B"}
    assert {row["activation_state"] for row in rows} == {"reference_only"}

    by_id = {row["observation_id"]: row for row in rows}
    assert (by_id["SF19-ALL-PLANT-PROTEIN-TO-LPC"]["reported_min"],
            by_id["SF19-ALL-PLANT-PROTEIN-TO-LPC"]["reported_max"]) == ("24", "42")
    juice = by_id["SF19-JUICE-PROTEIN-TO-LPC-MAX"]
    assert juice["reported_max"] == "86" and juice["reported_min"] == ""
    assert (by_id["SF19-RED-CLOVER-CP-EXTRACTED"]["reported_min"],
            by_id["SF19-RED-CLOVER-CP-EXTRACTED"]["reported_max"]) == ("65", "98")
    assert "crude protein" in by_id["SF19-RED-CLOVER-CP-EXTRACTED"]["unit"]
    assert "dry LPC" in by_id["SF19-RED-CLOVER-DRY-LPC-YIELD"]["unit"]
    assert "reduced with maturity" in by_id["SF19-MATURITY-EFFECT"]["reported_basis"]

    sidecar = json.loads(CSV_PATH.with_suffix(CSV_PATH.suffix + ".source.json").read_text(encoding="utf-8"))
    assert sidecar["persistent_identifier"] == "doi:10.1016/j.jclepro.2019.01.292"
    assert "CC BY-NC-ND 4.0" in sidecar["license"]
    assert sidecar["runtime_parameter_mapping"] == []

    manifest_rows = _read_rows(DATA / "dataset_manifest.csv")
    manifest = {row["filename"]: row for row in manifest_rows}
    assert len(manifest_rows) == len(manifest)
    assert manifest[CSV_PATH.name]["row_count"] == "5"
    assert manifest[CSV_PATH.name]["integration_readiness"] == "reference_only"
    source_rows = _read_rows(DATA / "source_register.csv")
    sources = {row["source_id"]: row for row in source_rows}
    assert len(source_rows) == len(sources)
    assert sources[SOURCE_ID]["doi_or_stable_id"] == "10.1016/j.jclepro.2019.01.292"
