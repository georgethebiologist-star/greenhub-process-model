import csv
import json
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "Greenhub" / "data" / "Protein recovery" / "Isoelectric"
FILENAME = "nynas_2021_green_biomass_feed_nitrogen_and_dry_matter_reference.csv"


def _rows(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as stream:
        return list(csv.DictReader(stream))


def test_nynas_2021_feed_table_is_traceable_and_keeps_dm_and_n_bases_distinct():
    path = DATA_DIR / FILENAME
    rows = _rows(path)
    metadata = json.loads(path.with_suffix(".csv.source.json").read_text(encoding="utf-8"))
    manifest = _rows(DATA_DIR / "dataset_manifest.csv")
    catalog = _rows(ROOT / "Greenhub" / "data" / "fair_input_catalog" / "master_input_catalog.csv")

    assert len(rows) == metadata["observations"] == 18
    assert len({row["observation_id"] for row in rows}) == 18
    assert Counter(row["measure"] for row in rows) == {
        "nitrogen_content": 9,
        "dry_matter_content": 9,
    }
    assert {row["source_id"] for row in rows} == {"SRC002"}
    assert {row["activation_state"] for row in rows} == {"reference_only"}
    assert {row["quality_class"] for row in rows} == {"B"}

    lucerne_n = next(row for row in rows if row["biomass"] == "Lucerne" and row["measure"] == "nitrogen_content")
    lucerne_dm = next(row for row in rows if row["biomass"] == "Lucerne" and row["measure"] == "dry_matter_content")
    spinach_n = next(row for row in rows if row["biomass"] == "Spinach" and row["measure"] == "nitrogen_content")
    assert float(lucerne_n["value"]) == 2.8
    assert lucerne_n["basis"] == "dry matter basis"
    assert float(lucerne_dm["value"]) == 20.9
    assert lucerne_dm["basis"] == "fresh biomass, as received"
    assert lucerne_n["collection_date"] == "2018-05-25"
    assert spinach_n["value"] == "4.8"
    assert spinach_n["collection_date"] == "retail date not stated"
    assert spinach_n["source_context"] == "Italian retail baby spinach used as a model crop"

    assert metadata["doi"] == metadata["source_doi"] == "10.3390/foods10112533"
    assert metadata["license"] == "CC BY 4.0"
    assert metadata["activation_state"] == "reference_only"
    assert metadata["calculation_connected"] is False
    assert "Table 1 feed values are retained as a separate source table" in metadata["table_specificity_note"]
    assert any(row["filename"] == FILENAME and row["row_count"] == "18" for row in manifest)

    indexed = next(row for row in catalog if row["relative_path"].endswith(FILENAME))
    assert indexed["source_ids"] == "SRC002"
    assert indexed["source_dois"] == "10.3390/foods10112533"
    assert indexed["readiness"] == "reference_only"
    assert indexed["source_metadata_linkage"] == "direct_dataset_path"
