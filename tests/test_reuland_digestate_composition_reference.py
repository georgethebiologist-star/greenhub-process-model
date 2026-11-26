import csv
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "Greenhub" / "data" / "Resource recovery" / "Digestate_and_Separation"
FILENAME = "reuland_digestate_composition_zenodo_v1_reference.csv"


def _rows(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as stream:
        return list(csv.DictReader(stream))


def test_reuland_digestate_reference_is_traceable_and_never_runtime_active():
    path = DATA / FILENAME
    rows = _rows(path)
    metadata = json.loads(path.with_suffix(".source.json").read_text(encoding="utf-8"))
    manifest = _rows(DATA / "dataset_manifest.csv")
    sources = _rows(DATA / "source_register.csv")
    catalog = _rows(ROOT / "Greenhub" / "data" / "fair_input_catalog" / "master_input_catalog.csv")

    assert len(rows) == metadata["source_rows_exported"] == 1884
    assert len({row["source_record_id"] for row in rows}) == len(rows)
    assert {row["Digestates"] for row in rows} == {"4", "5", "6", "8"}
    assert {row["Feedstock"] for row in rows if row["Feedstock"]} == {"1", "2", "3"}
    assert metadata["dataset_identifier"] == "https://doi.org/10.5281/zenodo.5526416"
    assert metadata["source_file_md5"] == "f743d5ebcc1c0de38709444e2dee1d17"
    assert metadata["activation_state"] == "reference_only"
    assert metadata["calculation_connected"] is False
    assert "not specific to roadside grass" in metadata["limitations"][0]
    assert any(row["filename"] == FILENAME and row["row_count"] == "1884" and row["integration_status"] == "traceable_reference_only_not_runtime_eligible" for row in manifest)
    assert any(row["source_id"] == "SRC_REULAND2021_EBA_V1" for row in sources)
    assert all(None not in row for row in sources)
    indexed = next(row for row in catalog if row["relative_path"].endswith(FILENAME))
    assert indexed["source_metadata_linkage"] == "direct_local_source_record"
    assert indexed["source_ids"] == "SRC_REULAND2021_EBA_V1"
    assert "10.5281/zenodo.5526416" in indexed["source_dois"].split(";")
