import csv
import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
FOLDER = ROOT / "Greenhub" / "data" / "Bigas production + upgrade" / "AD reactor"
FILENAME = "guanlao_2019_roadside_grass_thermophilic_ad_reference.csv"
SOURCE_ID = "SRC-GUANLAO-2019-ROADSIDE-GRASS-AD"


def _rows(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as stream:
        return list(csv.DictReader(stream))


def test_guanlao_thesis_preserves_roadside_and_managed_grass_boundaries():
    path = FOLDER / FILENAME
    rows = _rows(path)
    metadata = json.loads(path.with_suffix(".source.json").read_text(encoding="utf-8"))
    assert len(rows) == metadata["row_count"]
    assert len({row["record_id"] for row in rows}) == len(rows)
    assert {row["source_id"] for row in rows} == {SOURCE_ID}
    assert {row["quality_class"] for row in rows} == {"B"}
    assert {row["activation_state"] for row in rows} == {"reference_only"}

    by_id = {row["record_id"]: row for row in rows}
    assert by_id["GUA19-BATCH-1-FEED-DRY_MATTER_CONTENT"]["reported_value"] == "57.3"
    assert "roadside" in by_id["GUA19-DIGESTER-1-BATCH-1-ROADSIDE-ACTUAL-CH4"]["material_batch"].lower()
    assert by_id["GUA19-DIGESTER-1-BATCH-1-ROADSIDE-ACTUAL-CH4"]["reported_value"] == "188.19"
    assert "managed grassland" in by_id["GUA19-DIGESTER-1-UNTREATED_ACTUAL_METHANE_PRODUCTIVITY"]["material_batch"].lower()
    assert by_id["GUA19-DIGESTER-1-UNTREATED_ACTUAL_METHANE_PRODUCTIVITY"]["reported_value"] == "188.34"

    abstract_bmp = by_id["GUA19-BATCH-1-FEED-CALCULATED_METHANE_POTENTIAL"]
    assert "EPi-test" in abstract_bmp["basis"]
    assert "not an independently run standardized BMP assay" in abstract_bmp["basis"]
    table16 = by_id["GUA19-TABLE16-UNTREATED-SUMMARY-ACTUAL_METHANE_PRODUCTIVITY_SUMMARY_TABLE16"]
    assert table16["reported_value"] == "188.74"
    assert "not reconciled" in table16["limitations"]

    digestate_methods = [row for row in rows if row["record_type"] == "digestate_analysis_method"]
    assert digestate_methods
    assert all(not row["reported_value"] for row in digestate_methods)
    assert all("as zero" in row["limitations"] for row in digestate_methods)

    seed = by_id["GUA19-SEED-DIGESTER_SEED_EXPOSURE_TIME_SHORT"]
    assert "Commercial_bird_seed_proxy" in seed["transferability"]
    assert metadata["doi"] is None
    assert metadata["calculation_connected"] is False
    assert any(row["source_id"] == SOURCE_ID for row in _rows(FOLDER / "source_register.csv"))
    assert any(row["filename"] == FILENAME for row in _rows(FOLDER / "dataset_manifest.csv"))

    catalog = _rows(ROOT / "Greenhub" / "data" / "fair_input_catalog" / "master_input_catalog.csv")
    asset = next(row for row in catalog if row["relative_path"].endswith(FILENAME))
    assert SOURCE_ID in asset["source_ids"]
    assert asset["readiness"] == "reference_only"

    audit = ROOT / "Greenhub" / "data" / "global_audit_package"
    relpath = f"Bigas production + upgrade/AD reactor/{FILENAME}"
    readiness = next(row for row in _rows(audit / "global_dataset_readiness.csv") if row["dataset_path"] == relpath)
    assert readiness["readiness"] == "D3"
    checksum = next(row for row in _rows(audit / "source_dataset_checksums.csv") if row["dataset_path"] == relpath)
    assert checksum["sha256"] == hashlib.sha256(path.read_bytes()).hexdigest()
