import csv
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "Greenhub" / "data" / "Pre-treatment" / "Mechanical"
FILE_NAME = "green_biorefinery_mass_balance_resch_2024_table5_reference.csv"


def _rows(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def test_resch_table5_mass_balance_is_traceable_and_not_runtime_active():
    rows = _rows(DATA_DIR / FILE_NAME)
    metadata = json.loads(
        (DATA_DIR / FILE_NAME.replace(".csv", ".source.json")).read_text(encoding="utf-8")
    )
    manifest = _rows(DATA_DIR / "dataset_manifest.csv")

    assert len(rows) == metadata["rows"] == 30
    assert len({row["observation_id"] for row in rows}) == len(rows)
    assert {row["source_id"] for row in rows} == {"S06_RESCH_2024"}
    assert {row["activation_state"] for row in rows} == {"reference_only"}
    assert {row["process_stage"] for row in rows} == {
        "wilted_forage", "silage", "press_juice", "press_cake_fresh", "press_cake_reensiled"
    }
    assert {row["parameter"] for row in rows} == {
        "dry_matter_yield", "crude_protein_yield", "neutral_detergent_fibre_yield",
        "sugar_yield", "crude_ash_yield", "volatile_organic_compounds_yield"
    }
    assert all(row["unit"] == "kg/ha" and row["basis"] == "dry matter" for row in rows)
    assert sum(row["evidence_class"] == "not_reported" for row in rows) == 1
    assert sum(row["evidence_class"] == "not_analyzed" for row in rows) == 1
    juice_cp = next(row for row in rows if row["observation_id"] == "RESCH24-MB-CP-JUICE")
    assert (juice_cp["grass_clover_mean"], juice_cp["red_clover_mean"], juice_cp["residual_standard_deviation"]) == ("143", "160", "9")
    assert sum(row["filename"] == FILE_NAME for row in manifest) == 1
    assert "not Dutch roadside grass" in metadata["limitations"][0]
