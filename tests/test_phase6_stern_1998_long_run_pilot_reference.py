import csv
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "Greenhub/data/Bigas production + upgrade/Membrane"
DATASET = DATA / "bench_scale_long_run_pilot_stern_1998_reference.csv"


def _rows(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as stream:
        reader = csv.DictReader(stream)
        rows = list(reader)
        assert reader.fieldnames
        assert all(None not in row and all(value is not None for value in row.values()) for row in rows)
        return rows


def test_stern_long_run_pilot_extract_preserves_ranges_and_limitations():
    rows = _rows(DATASET)
    by_id = {row["record_id"]: row for row in rows}
    sources = {row["source_id"]: row for row in _rows(DATA / "source_register.csv")}
    manifest = {row["filename"]: row for row in _rows(DATA / "dataset_manifest.csv")}
    metadata = json.loads(DATASET.with_suffix(".csv.source.json").read_text(encoding="utf-8"))

    assert len(rows) == 13
    assert len(by_id) == 13
    assert {row["activation_state"] for row in rows} == {"reference_only"}
    assert {row["quality_class"] for row in rows} == {"B"}
    assert {row["source_id"] for row in rows} == {"STERN1998"}
    assert by_id["STERN98-03"]["reported_value"] == ">1000"
    assert by_id["STERN98-05"]["reported_value"] == "0.34-0.41"
    assert by_id["STERN98-10"]["reported_value"] == "92-95"
    assert by_id["STERN98-11"]["basis_or_denominator"] == "retentate product composition"
    assert "Do not infer methane recovery" in by_id["STERN98-10"]["notes"]
    assert sources["STERN1998"]["doi_or_stable_identifier"] == "10.1016/S0376-7388(98)00238-5"
    assert manifest[DATASET.name]["row_count"] == "13"
    assert manifest["source_register.csv"]["row_count"] == "9"
    assert all((ROOT / row["relative_path"].replace("/", "\\")).is_file() for row in manifest.values())
    assert metadata["activation_state"] == "reference_only"
    assert "recovery" in " ".join(metadata["limitations"]).lower()


def test_stern_long_run_pilot_is_indexed_with_its_doi():
    catalog = _rows(ROOT / "Greenhub/data/fair_input_catalog/master_input_catalog.csv")
    asset = next(row for row in catalog if row["relative_path"].endswith(DATASET.name))

    assert asset["source_ids"] == "STERN1998"
    assert "10.1016/S0376-7388(98)00238-5" in asset["source_dois"]
    assert asset["readiness"] == "reference_only"
    assert asset["source_metadata_status"] == "linked_to_source_register"
