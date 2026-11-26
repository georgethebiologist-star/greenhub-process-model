import csv
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "Greenhub" / "data" / "Pre-treatment" / "Feedstock"
FILENAME = "pzh_roadside_mowing_quantity_and_schedule_reference.csv"


def _rows(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as stream:
        return list(csv.DictReader(stream))


def test_official_south_holland_mowing_claims_are_traceable_and_not_overinterpreted():
    path = DATA / FILENAME
    rows = _rows(path)
    metadata = json.loads(path.with_suffix(".source.json").read_text(encoding="utf-8"))
    sources = _rows(DATA / "source_register.csv")
    manifest = _rows(DATA / "dataset_manifest.csv")
    catalog = _rows(ROOT / "Greenhub" / "data" / "fair_input_catalog" / "master_input_catalog.csv")

    assert len(rows) == metadata["row_count"] == 8
    assert len({row["record_id"] for row in rows}) == 8
    assert {row["quality_class"] for row in rows} == {"B"}
    assert {row["activation_state"] for row in rows} == {"reference_only"}
    assert {row["source_id"] for row in rows} == {"SRC-PZH-VERGE-MOWING-2026"}

    by_id = {row["record_id"]: row for row in rows}
    mass = by_id["PZH-MOW26-ANNUAL-GRASS"]
    assert mass["reported_value"] == "10000"
    assert mass["qualifier"] == "approximately"
    assert mass["unit"] == "t/year"
    assert "moisture basis" in mass["uncertainty_or_limit"]
    assert "not specified" in mass["uncertainty_or_limit"]
    assert by_id["PZH-MOW26-WINDOW-1"]["reported_value"] == "June–July"
    assert by_id["PZH-MOW26-WINDOW-2"]["reported_value"] == "September–October"
    assert by_id["PZH-MOW26-REST"]["reported_value"] == "a few days"
    assert metadata["doi"] is None
    assert metadata["activation_state"] == "reference_only"
    assert any("tonnes-per-kilometre ratio is calculated" in limitation.lower() for limitation in metadata["limitations"])
    assert any(row["source_id"] == "SRC-PZH-VERGE-MOWING-2026" for row in sources)
    assert any(row["file_name"] == FILENAME and row["row_count"] == "8" for row in manifest)

    asset = next(row for row in catalog if row["relative_path"].endswith(FILENAME))
    assert asset["source_ids"] == "SRC-PZH-VERGE-MOWING-2026"
    assert asset["readiness"] == "reference_only"
