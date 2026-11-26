import csv
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "Greenhub" / "data" / "Pre-treatment" / "Feedstock"
FILE_NAME = "flemish_roadside_grass_quality_survey_2020_summary_reference.csv"


def _rows(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def test_flemish_survey_summary_is_traceable_and_not_runtime_activated():
    observations = _rows(DATA_DIR / FILE_NAME)
    sources = _rows(DATA_DIR / "source_register.csv")
    manifest = _rows(DATA_DIR / "dataset_manifest.csv")
    metadata_path = DATA_DIR / f"{FILE_NAME.removesuffix('.csv')}.source.json"
    metadata = json.loads(metadata_path.read_text(encoding="utf-8"))

    assert len(observations) == metadata["rows"] == 11
    assert len({row["observation_id"] for row in observations}) == len(observations)
    assert {row["source_id"] for row in observations} == {"SRC-EUROFINS-FLEMISH-2021"}
    assert sum(row["parameter"] == "cadmium_threshold_exceedance" for row in observations) == 4
    assert sum(row["parameter"] == "visible_litter" for row in observations) == 4
    assert {row["activation_state"] for row in observations} == {"reference_only"}
    assert any(row["source_id"] == "SRC-EUROFINS-FLEMISH-2021" for row in sources)
    assert sum(row["file_name"] == FILE_NAME for row in manifest) == 1
    assert "not a GreenHub" in metadata["limitations"][3]
    assert "No explicit" in metadata["license"]
    assert metadata["activation_state"] == "reference_only"

    cadmium = {
        row["sample_group"]: row["reported_count"]
        for row in observations
        if row["parameter"] == "cadmium_threshold_exceedance"
    }
    assert cadmium == {
        "ANB nature grassland": "1",
        "DVW waterway verge": "2",
        "AWV regional-road verge": "2",
        "AWV motorway verge": "1",
    }
