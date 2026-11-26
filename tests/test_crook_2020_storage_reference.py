import csv
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def _rows(path):
    with path.open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def test_crook_storage_table_extract_is_traceable_and_not_runtime_eligible():
    data_dir = ROOT / "Greenhub/data/storage"
    data_path = data_dir / "annual_ryegrass_bale_silage_85d_crook_2020_reference.csv"
    rows = _rows(data_path)
    assert len(rows) == 26
    assert len({row["record_id"] for row in rows}) == 26
    assert {row["source_id"] for row in rows} == {"SRC-GRASS-RYEGRASS-STORAGE-2020"}
    assert {row["evidence_class"] for row in rows} == {"B_measured"}
    assert {row["quality_class"] for row in rows} == {"B"}
    assert {row["activation_state"] for row in rows} == {"reference_only"}
    assert {row["storage_days"] for row in rows} == {"85"}

    by_id = {row["record_id"]: row for row in rows}
    assert by_id["CROOK20-T2-DRY-DM-RECOVERY"]["value"] == "97.8"
    assert by_id["CROOK20-T2-WET-DM-RECOVERY"]["standard_error"] == "3.10"
    assert by_id["CROOK20-T4-D2-DM-RECOVERY"]["value"] == "99.2"
    assert by_id["CROOK20-T4-D3-NH3N"]["unit"] == "percent_total_nitrogen"
    assert "not an ammonia emission" in by_id["CROOK20-T4-D3-NH3N"]["limitations"]
    assert by_id["CROOK20-T2-DRY-DM"]["basis"] == "wet_mass_basis"

    metadata = json.loads(data_path.with_suffix(data_path.suffix + ".source.json").read_text(encoding="utf-8"))
    assert metadata["persistent_identifier"] == "doi:10.1002/cft2.20015"
    assert any("38 ± 9.5%" in item and "30 ± 9.5%" in item for item in metadata["limitations"])
    assert any("pooled" in item for item in metadata["limitations"])

    source = next(row for row in _rows(data_dir / "source_register.csv")
                  if row["source_id"] == "SRC-GRASS-RYEGRASS-STORAGE-2020")
    assert "annual_ryegrass_bale_silage_85d_crook_2020_reference.csv" in source["quality_notes"]
    manifest = _rows(data_dir / "dataset_manifest.csv")
    entry = next(row for row in manifest if row["filename"] == data_path.name)
    assert entry["row_count"] == "26"
    assert entry["integration_status"] == "traceable_reference_only_not_runtime_eligible"
