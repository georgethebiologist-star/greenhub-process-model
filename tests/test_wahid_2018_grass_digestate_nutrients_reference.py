import csv
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "Greenhub/data/Resource recovery/Digestate_and_Separation"
DATA_PATH = DATA_DIR / "grass_mixture_AD_digestate_macro_nutrients_wahid_2018_reference.csv"


def _rows(path):
    with path.open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def test_wahid_digestate_nutrients_are_basis_preserving_and_reference_only():
    rows = _rows(DATA_PATH)
    assert len(rows) == 48
    assert len({row["observation_id"] for row in rows}) == 48
    assert {row["feedstock_regime"] for row in rows} == {"2-cut", "4-cut"}
    assert {row["stream"] for row in rows} == {"feed_mixture", "digestate"}
    assert {row["activation_state"] for row in rows} == {"reference_only"}
    assert {row["quality_class"] for row in rows} == {"B"}
    assert {row["storage_or_AD_day"] for row in rows} == {"0", "70"}

    by_id = {row["observation_id"]: row for row in rows}
    assert by_id["WAHID18-LU4-DIG-TAN"]["reported_mean"] == "0.24"
    assert by_id["WAHID18-MIX4-FEED-P"]["unit"] == "g/kg"
    assert by_id["WAHID18-MIX4-DIG-P"]["basis"] == "fresh_matter"
    assert by_id["WAHID18-MIX2-DIG-S"]["reported_mean"] == "0.25"
    assert by_id["WAHID18-MIX2-DIG-K"]["reported_sd"] == ""

    metadata = json.loads(DATA_PATH.with_suffix(DATA_PATH.suffix + ".source.json").read_text(encoding="utf-8"))
    assert metadata["persistent_identifier"] == "doi:10.1016/j.biombioe.2017.12.029"
    assert any("40:60" in item for item in metadata["limitations"])
    assert any("flow" in item for item in metadata["limitations"])

    sources = _rows(DATA_DIR / "source_register.csv")
    source = next(row for row in sources if row["source_id"] == "SRC_WAHID2018_GRASS_AD_NUTRIENTS")
    assert source["doi_or_stable_id"] == "10.1016/j.biombioe.2017.12.029"
    manifest = _rows(DATA_DIR / "dataset_manifest.csv")
    assert any(row["filename"] == DATA_PATH.name and row["row_count"] == "48" for row in manifest)
