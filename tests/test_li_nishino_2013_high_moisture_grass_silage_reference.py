import csv
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "Greenhub" / "data" / "storage"
FILENAME = "high_moisture_grass_silage_fermentation_li_nishino_2013_reference.csv"
SOURCE_ID = "SRC-LI-NISHINO-HIGH-MOISTURE-GRASS-SILAGE-2013"


def _rows(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as stream:
        return list(csv.DictReader(stream))


def test_li_nishino_grass_silage_time_course_is_traceable_and_not_activated():
    path = DATA / FILENAME
    rows = _rows(path)
    metadata = json.loads(path.with_suffix(".source.json").read_text(encoding="utf-8"))
    manifest = _rows(DATA / "dataset_manifest.csv")
    sources = _rows(DATA / "source_register.csv")
    catalog = _rows(ROOT / "Greenhub" / "data" / "fair_input_catalog" / "master_input_catalog.csv")
    global_manifest = _rows(ROOT / "Greenhub" / "data" / "global_audit_package" / "global_dataset_manifest.csv")
    global_readiness = _rows(ROOT / "Greenhub" / "data" / "global_audit_package" / "global_dataset_readiness.csv")
    checksums = _rows(ROOT / "Greenhub" / "data" / "global_audit_package" / "source_dataset_checksums.csv")

    assert len(rows) == metadata["row_count"] == 164
    assert len({row["record_id"] for row in rows}) == 164
    assert {row["source_id"] for row in rows} == {SOURCE_ID}
    assert {row["species"] for row in rows} == {"Italian ryegrass", "Guinea grass"}
    assert {row["quality_class"] for row in rows} == {"B"}
    assert {row["activation_state"] for row in rows} == {"reference_only"}
    assert {row["evidence_class"] for row in rows} == {
        "primary_peer_reviewed_experimental_article_table_transcription"
    }

    by_key = {
        (row["species"], row["storage_stage"], row["anaerobic_storage_days"], row["metric"]): row
        for row in rows
    }
    assert by_key[("Italian ryegrass", "pre_ensiled_fresh_crop", "0", "dry_matter")]["value"] == "212"
    assert by_key[("Guinea grass", "pre_ensiled_fresh_crop", "0", "pH")]["value"] == "6.28"
    ryegrass_120d_butyrate = by_key[("Italian ryegrass", "anaerobic_silo_opening", "120", "butyric_acid")]
    assert ryegrass_120d_butyrate["value"] == "36.7"
    assert ryegrass_120d_butyrate["reported_value_with_significance_marker"] == "36.7a"
    assert ryegrass_120d_butyrate["reported_SE"] == "1.21"
    assert ryegrass_120d_butyrate["unit"] == "g/kg dry matter"

    guinea_120d_butyrate = by_key[("Guinea grass", "anaerobic_silo_opening", "120", "butyric_acid")]
    assert guinea_120d_butyrate["value"] == "62.4"
    assert guinea_120d_butyrate["reported_value_with_significance_marker"] == "62.4c"

    ryegrass_14d_air_pH = by_key[("Italian ryegrass", "after_7_day_aerobic_exposure", "14", "pH")]
    assert ryegrass_14d_air_pH["value"] == "6.72"
    assert ryegrass_14d_air_pH["aerobic_exposure_days"] == "7"
    assert ryegrass_14d_air_pH["aerobic_comparison_test"] == "**"

    assert all(row["metric"] != "water_soluble_carbohydrates" for row in rows)
    assert all(
        row["replicate_context"].startswith("Three separately prepared silage bags")
        for row in rows if row["storage_stage"] != "pre_ensiled_fresh_crop"
    )
    assert all(
        row["replicate_context"].startswith("Chemical measurements reported as means of duplicate analyses")
        for row in rows if row["storage_stage"] == "pre_ensiled_fresh_crop"
    )
    assert all(
        "not an observation-specific interval" in row["SE_scope"]
        for row in rows if row["reported_SE"]
    )
    assert all(
        row["SE_scope"] == "No standard error reported for this Table 1 value"
        for row in rows if not row["reported_SE"]
    )
    assert metadata["doi"] == "10.5713/ajas.2013.13175"
    assert metadata["calculation_connected"] is False
    assert any("124 g/kg DM" in item and "25 g/kg DM" in item for item in metadata["limitations"])
    assert "No explicit open data-reuse license" in metadata["license_or_rights"]
    assert any(row["source_id"] == SOURCE_ID for row in sources)
    assert any(row["filename"] == FILENAME and row["row_count"] == "164" for row in manifest)

    asset = next(row for row in catalog if row["relative_path"].endswith(FILENAME))
    assert SOURCE_ID in asset["source_ids"]
    assert asset["readiness"] == "reference_only"

    global_path = f"storage/{FILENAME}"
    global_dataset = next(row for row in global_manifest if row["dataset_path"] == global_path)
    readiness = next(row for row in global_readiness if row["dataset_path"] == global_path)
    checksum = next(row for row in checksums if row["dataset_path"] == global_path)
    assert global_dataset["detected_readiness"] == "D3"
    assert global_dataset["row_count_observed"] == "164"
    assert readiness["numeric_rows"] == "164"
    assert readiness["numeric_rows_missing_exact_location"] == "0"
    assert checksum["sha256"] == metadata["sha256_csv"]
