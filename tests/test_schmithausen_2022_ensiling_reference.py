import csv
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "Greenhub" / "data" / "storage"
CSV_PATH = DATA / "grass_lucerne_ensiling_schmithausen_2022_reference.csv"
SOURCE_ID = "SRC-SCHMITHAUSEN-GRASS-LUCERNE-ENSILING-2022"


def _read_rows(path, require_well_formed=False):
    with path.open(encoding="utf-8-sig", newline="") as stream:
        reader = csv.DictReader(stream)
        rows = list(reader)
        assert reader.fieldnames
        if require_well_formed:
            assert all(None not in row for row in rows), "CSV row has more cells than the declared schema"
        return rows


def test_schmithausen_tables_are_transcribed_and_remain_reference_only():
    rows = _read_rows(CSV_PATH, require_well_formed=True)
    assert len(rows) == 86
    assert len({row["observation_id"] for row in rows}) == 86
    assert {row["source_id"] for row in rows} == {SOURCE_ID}
    assert {row["evidence_class"] for row in rows} == {"B_measured"}
    assert {row["activation_state"] for row in rows} == {"reference_only"}

    by_key = {(row["variant"], row["property"], row["sample_stage"]): row for row in rows}
    assert by_key[("G_SW", "dry_matter_concentration", "ensiling_loading")]["value"] == "21.5"
    assert by_key[("G_LW", "silage_density", "ensiling_loading")]["value"] == "159.1"
    assert by_key[("G_SW", "lactic_acid", "silage_day_149")]["value"] == "47.2"
    assert by_key[("G_SW", "lactic_acid", "silage_day_149")]["standard_deviation"] == "11.0"
    assert by_key[("L_SW", "ammonia_nitrogen_fraction", "silage_day_149")]["value"] == "788"
    assert by_key[("L_SW", "ammonia_nitrogen_fraction", "silage_day_149")]["standard_deviation"] == "66"
    assert by_key[("L_LW", "lactic_acid", "silage_day_149")]["value"] == "0.0"
    assert by_key[("L_LW", "lactic_acid", "silage_day_149")]["standard_deviation"] == "0.0"

    fresh = [row for row in rows if row["sample_stage"] == "fresh_before_ensiling"]
    assert len(fresh) == 18
    assert all(row["storage_day"] == "" for row in fresh)
    assert all(row["standard_deviation"] == "" for row in fresh)
    assert all(row["replicates"] == "" for row in fresh)
    assert all(row["source_location"].startswith("Table 3.") for row in rows)

    sidecar = json.loads(CSV_PATH.with_suffix(CSV_PATH.suffix + ".source.json").read_text(encoding="utf-8"))
    assert sidecar["persistent_identifier"] == "doi:10.1016/j.jenvman.2021.114142"
    assert sidecar["activation_state"] == "reference_only"
    assert "could not be quantified" in " ".join(sidecar["limitations"])
    assert "not an NH3 emission measurement" in " ".join(sidecar["limitations"])

    manifest = {row["filename"]: row for row in _read_rows(DATA / "dataset_manifest.csv")}
    assert manifest[CSV_PATH.name]["row_count"] == "86"
    assert manifest[CSV_PATH.name]["integration_status"] == "traceable_reference_only_not_runtime_eligible"
    source_register = {row["source_id"]: row for row in _read_rows(DATA / "source_register.csv")}
    assert source_register[SOURCE_ID]["doi_or_stable_identifier"] == "10.1016/j.jenvman.2021.114142"

