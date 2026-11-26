import csv
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "Greenhub" / "data" / "Pre-treatment" / "Feedstock"
FILENAME = "czubaszek_2023_fresh_grass_ultimate_and_metals_reference.csv"


def _rows(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as stream:
        return list(csv.DictReader(stream))


def test_czubaszek_table3_table4_incremental_extract_is_traceable_and_reference_only():
    path = DATA / FILENAME
    rows = _rows(path)
    metadata = json.loads(path.with_suffix(".source.json").read_text(encoding="utf-8"))
    manifest = _rows(DATA / "dataset_manifest.csv")
    sources = _rows(DATA / "source_register.csv")
    catalog = _rows(ROOT / "Greenhub" / "data" / "fair_input_catalog" / "master_input_catalog.csv")

    assert len(rows) == metadata["rows"] == 42
    assert len({row["record_id"] for row in rows}) == 42
    assert {row["source_id"] for row in rows} == {"SRC-CZUBASZEK-2023"}
    assert {row["quality_class"] for row in rows} == {"B"}
    assert {row["activation_state"] for row in rows} == {"reference_only"}
    assert {row["harvest_season"] for row in rows} == {"spring", "summer", "autumn"}

    lookup = {(row["metric"], row["harvest_season"]): row for row in rows}
    assert lookup[("elemental_carbon", "autumn")]["reported_mean"] == "41.91"
    assert lookup[("elemental_nitrogen", "summer")]["reported_sd"] == "0.00"
    assert lookup[("volatile_matter", "spring")]["statistical_group"] == "a"
    assert lookup[("chromium", "spring")]["reported_mean"] == "14.43"
    assert lookup[("iron", "spring")]["unit"] == "mg/kg DM"

    non_detects = [row for row in rows if row["observation_status"] == "not_detected"]
    assert {(row["metric"], row["harvest_season"]) for row in non_detects} == {
        ("copper", "spring"), ("copper", "summer"), ("mercury", "spring")
    }
    assert all(row["reported_mean"] == row["reported_sd"] == "" for row in non_detects)
    assert all(row["source_reported_text"] == "n.d. (not detected)" for row in non_detects)
    assert all("analytical" in row["field_replicates"] for row in rows)
    assert not {"ash", "sulfur"} & {row["metric"] for row in rows}

    assert metadata["doi"] == "10.3390/en16114488"
    assert metadata["license"] == "CC BY 4.0 as stated by the article; transcribed values and source citation are retained."
    assert metadata["calculation_connected"] is True
    assert metadata["activation_state"] == "partially_calculation_connected_profile_default_proxy"
    assert any("not an as-received wet-feed dataset" in item for item in metadata["limitations"])
    assert any(row["source_id"] == "SRC-CZUBASZEK-2023" for row in sources)
    assert any(row["file_name"] == FILENAME and row["row_count"] == "42" for row in manifest)

    asset = next(row for row in catalog if row["relative_path"].endswith(FILENAME))
    assert asset["source_ids"] == "SRC-CZUBASZEK-2023"
    assert asset["source_dois"] == "10.3390/en16114488"
    assert asset["maturity"] == "D4"
    assert asset["activation_state"] == "reference_only"

