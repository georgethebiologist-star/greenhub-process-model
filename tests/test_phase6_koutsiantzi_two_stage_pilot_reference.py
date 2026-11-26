import csv
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "Greenhub/data/Bigas production + upgrade/Membrane"
DATASET = DATA / "two_stage_polyimide_pilot_koutsiantzi_2024_reference.csv"


def _rows(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as stream:
        reader = csv.DictReader(stream)
        rows = list(reader)
        assert reader.fieldnames
        assert all(None not in row and all(value is not None for value in row.values()) for row in rows)
        return rows


def test_two_stage_pilot_observations_are_traceable_and_not_activated():
    rows = _rows(DATASET)
    by_id = {row["record_id"]: row for row in rows}
    sources = {row["source_id"]: row for row in _rows(DATA / "source_register.csv")}
    manifest = {row["filename"]: row for row in _rows(DATA / "dataset_manifest.csv")}
    metadata = json.loads(DATASET.with_suffix(".csv.source.json").read_text(encoding="utf-8"))

    assert len(rows) == 10
    assert len(by_id) == len(rows)
    assert {row["activation_state"] for row in rows} == {"reference_only"}
    assert {row["quality_class"] for row in rows} == {"B"}
    assert {row["source_id"] for row in rows} == {"KOUTSIANTZI2024", "KOUTSIANTZI_THESIS_2024"}
    assert by_id["KOUTSI24-04"]["reported_value"] == "95.7"
    assert by_id["KOUTSI24-05"]["reported_value"] == "82.4"
    assert by_id["KOUTSI24-06"]["reported_value"] == "17.5"
    assert by_id["KOUTSI24-08"]["reported_value"] == "67"
    assert by_id["KOUTSITHESIS24-01"]["reported_value"] == "87.8"
    assert by_id["KOUTSI24-08"]["evidence_class"] == "B_modelled"
    assert by_id["KOUTSI24-04"]["evidence_class"] == "B_measured"
    assert "Conflicts" in by_id["KOUTSI24-08"]["uncertainty_or_limit"]
    assert sources["KOUTSIANTZI2024"]["doi_or_stable_identifier"] == "10.1016/j.envres.2023.118080"
    assert sources["KOUTSIANTZI_THESIS_2024"]["doi_or_stable_identifier"] == "10.12681/eadd/57788"
    assert manifest[DATASET.name]["row_count"] == "10"
    assert manifest[DATASET.name]["relative_path"].replace("/", "\\") == str(DATASET.relative_to(ROOT)).replace("/", "\\")
    assert all((ROOT / row["relative_path"].replace("/", "\\")).is_file() for row in manifest.values())
    assert metadata["activation_state"] == "reference_only"
    assert "67%" in metadata["known_discrepancy"] and "87.8%" in metadata["known_discrepancy"]


def test_two_stage_pilot_is_registered_in_fair_catalog_after_refresh():
    catalog_path = ROOT / "Greenhub/data/fair_input_catalog/master_input_catalog.csv"
    if not catalog_path.is_file():
        catalog_path = ROOT / "Greenhub/results/fair_input_catalog/master_input_catalog.csv"
    catalog = _rows(catalog_path)
    asset = next(row for row in catalog if row["relative_path"].endswith(DATASET.name))

    assert asset["source_ids"] == "KOUTSIANTZI2024;KOUTSIANTZI_THESIS_2024"
    assert "10.1016/j.envres.2023.118080" in asset["source_dois"]
    assert "10.12681/eadd/57788" in asset["source_dois"]
    assert asset["readiness"] == "reference_only"
    assert asset["source_metadata_status"] == "linked_to_source_register"
