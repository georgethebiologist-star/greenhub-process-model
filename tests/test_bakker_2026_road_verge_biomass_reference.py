import csv
import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "Greenhub" / "data" / "Pre-treatment" / "Feedstock"
FILENAME = "road_verge_standing_biomass_bakker_2026_zenodo_reference.csv"


def _rows(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as stream:
        return list(csv.DictReader(stream))


def test_bakker_road_verge_biomass_is_traceable_and_reference_only():
    path = DATA / FILENAME
    rows = _rows(path)
    metadata = json.loads(path.with_suffix(".source.json").read_text(encoding="utf-8"))
    manifest = _rows(DATA / "dataset_manifest.csv")
    sources = _rows(DATA / "source_register.csv")
    catalog = _rows(ROOT / "Greenhub" / "data" / "fair_input_catalog" / "master_input_catalog.csv")

    assert len(rows) == metadata["rows"] == 120
    assert len({row["observation_id"] for row in rows}) == len(rows)
    assert len({row["road_verge"] for row in rows}) == 10
    assert {row["month_sampled"] for row in rows} == {"Jun", "Aug"}
    assert {row["mowing_treatment"] for row in rows} == {
        "Aug", "Nov", "JunhAug", "JunhNov", "JunAug", "JunNov"
    }
    assert sum(row["biomass_data_status"] == "missing_in_source" for row in rows) == 1
    assert all(row["standing_biomass_g_dm_m2"] == "" for row in rows if row["biomass_data_status"] == "missing_in_source")
    assert metadata["dataset_doi"] == "10.5281/zenodo.15349657"
    assert metadata["concept_doi"] == "10.5281/zenodo.15349656"
    assert metadata["license"] == "CC BY 4.0 (Zenodo version record metadata)"
    assert metadata["activation_state"] == "reference_only"
    assert metadata["calculation_connected"] is False
    assert "standing-biomass snapshots" in metadata["limitations"][0]
    assert any(row["file_name"] == FILENAME and row["row_count"] == "120" and "reference_only" in row["integration_readiness"] for row in manifest)
    assert any(row["source_id"] == "SRC_BAKKER_ROADVERGE_BIOMASS_2026" for row in sources)
    indexed = next(row for row in catalog if row["relative_path"].endswith(FILENAME))
    assert indexed["source_metadata_linkage"] == "direct_local_source_record"
    assert indexed["source_ids"] == "SRC_BAKKER_ROADVERGE_BIOMASS_2026"
    assert "10.5281/zenodo.15349657" in indexed["source_dois"].split(";")


def test_bakker_verbatim_source_assets_are_checksum_verified_and_reproducible():
    source_dir = DATA / "road_verge_standing_biomass_bakker_2026_source"
    raw_source = source_dir / "Biomass.csv"
    analysis = source_dir / "Analysis.R"
    expected_md5 = {
        raw_source: "a6769824448e47dad1ff3b2ff882c53c",
        analysis: "3a6e7bacc886ef5c1a5e9257a6aee684",
    }
    for path, digest in expected_md5.items():
        assert path.stat().st_size < 100_000_000
        assert hashlib.md5(path.read_bytes()).hexdigest() == digest
        metadata = json.loads(path.with_suffix(path.suffix + ".source.json").read_text(encoding="utf-8"))
        assert metadata["source_md5"] == digest
        assert metadata["dataset_doi"] == "10.5281/zenodo.15349657"
        assert metadata["license"].startswith("CC BY 4.0")
        assert metadata["activation_state"] == "reference_only"
        assert metadata["calculation_connected"] is False

    with raw_source.open(encoding="utf-8-sig", newline="") as stream:
        exact_rows = list(csv.DictReader(stream, delimiter=";"))
    with (DATA / "Biomass.csv").open(encoding="utf-8-sig", newline="") as stream:
        compatibility_rows = list(csv.DictReader(stream, delimiter=";"))
    assert exact_rows == compatibility_rows
    assert len(exact_rows) == 120
    assert "*10/1000" in analysis.read_text(encoding="utf-8")

    catalog = _rows(ROOT / "Greenhub" / "data" / "fair_input_catalog" / "master_input_catalog.csv")
    by_path = {row["relative_path"].replace("\\", "/"): row for row in catalog}
    raw_catalog_path = (
        "Greenhub/data/Pre-treatment/Feedstock/road_verge_standing_biomass_bakker_2026_source/Biomass.csv"
    )
    code_catalog_path = (
        "Greenhub/data/Pre-treatment/Feedstock/road_verge_standing_biomass_bakker_2026_source/Analysis.R"
    )
    assert by_path[raw_catalog_path]["role"] == "reference_source_data"
    assert by_path[code_catalog_path]["role"] == "reference_analysis_script"
    assert by_path[raw_catalog_path]["source_ids"] == "SRC_BAKKER_ROADVERGE_BIOMASS_2026"
