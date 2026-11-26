import csv
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
FOLDER = ROOT / "Greenhub" / "data" / "Bigas production + upgrade" / "Feed BMP"


def _rows(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as stream:
        return list(csv.DictReader(stream))


def test_fulltext_process_extract_preserves_source_basis_and_conflicts():
    path = FOLDER / "roadside_grass_AD_2024_fulltext_process_reference.csv"
    rows = _rows(path)
    by_id = {row["record_id"]: row for row in rows}
    metadata = json.loads(path.with_suffix(".source.json").read_text(encoding="utf-8"))

    assert len(rows) == 81
    assert len(by_id) == len(rows)
    assert {row["source_id"] for row in rows} == {"SOUZA2024"}
    assert {row["quality_class"] for row in rows} == {"B"}
    assert {row["activation_state"] for row in rows} == {"reference_only"}
    assert by_id["SOUZA24-T1-WET-DM"]["reported_value"] == "57.3"
    assert by_id["SOUZA24-T1-DRY-BMP"]["reported_value"] == "323"
    assert by_id["SOUZA24-WET-CH4-YIELD"]["reported_value"] == "237"
    assert by_id["SOUZA24-WET-CH4-YIELD"]["reported_unit"] == "mL CH4/g DOM"
    assert by_id["SOUZA24-WET-MIX-OFF"]["metric"] == "mixing_cycle_period"
    assert "90 seconds mixing on each 480-second cycle" in by_id["SOUZA24-WET-MIX-OFF"]["qualifier"]
    assert by_id["SOUZA24-LF2-GAS"]["reported_value"] == "78550"
    assert "Not attributable to batch 2 grass alone" in by_id["SOUZA24-LF2-GAS"]["uncertainty_or_limit"]
    assert metadata["doi"] == "10.1016/j.wasman.2024.04.018"
    assert metadata["rows"] == len(rows)
    assert metadata["activation_state"] == "reference_only"
    assert metadata["parameter_registry_mapping"] == "none"
    assert any("not averaged or reconciled" in item for item in metadata["limitations"])


def test_fulltext_digestate_extract_quarantines_implausible_nutrient_and_unclosed_flows():
    path = FOLDER / "roadside_grass_AD_2024_fulltext_digestate_reference.csv"
    rows = _rows(path)
    by_id = {row["record_id"]: row for row in rows}
    metadata = json.loads(path.with_suffix(".source.json").read_text(encoding="utf-8"))

    assert len(rows) == 12
    assert len(by_id) == len(rows)
    assert {row["source_id"] for row in rows} == {"SOUZA2024"}
    assert {row["quality_class"] for row in rows} == {"B"}
    assert {row["activation_state"] for row in rows} == {"reference_only"}
    assert by_id["SOUZA24-MB-LIQUID-RECOVERY"]["reported_value"] == "47-57"
    assert by_id["SOUZA24-MB-FIBER-DRY"]["reported_value"] == "5-8"
    assert by_id["SOUZA24-DIGESTATE-K"]["reported_value"] == "1808"
    assert "quarantined" in by_id["SOUZA24-DIGESTATE-K"]["observation_type"]
    assert by_id["SOUZA24-LF-LEACHATE-CL"]["reported_value"] == "2.8"
    assert metadata["doi"] == "10.1016/j.wasman.2024.04.018"
    assert metadata["rows"] == len(rows)
    assert metadata["activation_state"] == "reference_only"
    assert any("do not sum them as a closed balance" in item for item in metadata["limitations"])


def test_fulltext_companions_registered_and_not_runtime_connected():
    manifest = _rows(FOLDER / "dataset_manifest.csv")
    sources = _rows(FOLDER / "source_register.csv")
    catalog = _rows(ROOT / "Greenhub" / "data" / "fair_input_catalog" / "master_input_catalog.csv")
    manifest_by_name = {row["filename"]: row for row in manifest}
    source = next(row for row in sources if row["source_id"] == "SOUZA2024")

    for filename, count in (
        ("roadside_grass_AD_2024_fulltext_process_reference.csv", "81"),
        ("roadside_grass_AD_2024_fulltext_digestate_reference.csv", "12"),
    ):
        entry = manifest_by_name[filename]
        assert entry["row_count"] == count
        assert entry["integration_status"] == "traceable_reference_only_not_runtime_eligible"
        assert entry["primary_key"] == "record_id"

    assert "full-text process and digestate companions" in source["quality_notes"]
    for filename in (
        "roadside_grass_AD_2024_fulltext_process_reference.csv",
        "roadside_grass_AD_2024_fulltext_digestate_reference.csv",
    ):
        asset = next(row for row in catalog if row["relative_path"].endswith(filename))
        assert asset["source_ids"] == "SOUZA2024"
        assert asset["source_dois"] == "10.1016/j.wasman.2024.04.018"
        assert asset["readiness"] == "reference_only"
    code = "\n".join(file.read_text(encoding="utf-8") for file in (ROOT / "Greenhub").rglob("*.py"))
    assert "roadside_grass_AD_2024_fulltext_process_reference.csv" not in code
    assert "roadside_grass_AD_2024_fulltext_digestate_reference.csv" not in code
