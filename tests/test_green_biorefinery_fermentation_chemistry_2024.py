import csv
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "Greenhub" / "data" / "Pre-treatment" / "Mechanical"
FILE_NAME = "green_biorefinery_fermentation_chemistry_2024_reference.csv"


def _rows(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def test_resch_fermentation_chemistry_is_traceable_and_reference_only():
    rows = _rows(DATA_DIR / FILE_NAME)
    metadata = json.loads(
        (DATA_DIR / FILE_NAME.replace(".csv", ".source.json")).read_text(encoding="utf-8")
    )
    sources = _rows(DATA_DIR / "source_register.csv")
    manifest = _rows(DATA_DIR / "dataset_manifest.csv")

    assert len(rows) == metadata["rows"] == 28
    assert len({row["observation_id"] for row in rows}) == 28
    assert {row["source_id"] for row in rows} == {"S06_RESCH_2024"}
    assert {row["activation_state"] for row in rows} == {"reference_only"}
    assert {row["evidence_class"] for row in rows} == {"B_measured"}
    assert {row["process_stage"] for row in rows} == {
        "silage", "press_juice", "press_cake_fresh", "press_cake_reensiled"
    }
    assert {row["fermentation_parameter"] for row in rows} == {
        "lactic_acid", "acetic_acid", "butyric_acid", "propionic_acid",
        "ethanol", "ammonia", "pH"
    }
    assert all(row["grass_clover_mean"] and row["red_clover_mean"] for row in rows)
    assert sum(row["unit"] == "g/kg DM" for row in rows) == 24
    assert sum(row["unit"] == "pH" for row in rows) == 4
    assert "not an emission factor" in next(
        row["limitations"] for row in rows if row["fermentation_parameter"] == "ammonia"
    )
    assert "pH is not acidity reserve" in next(
        row["limitations"] for row in rows if row["fermentation_parameter"] == "pH"
    )

    pH_reensiled = next(
        row for row in rows
        if row["fermentation_parameter"] == "pH" and row["process_stage"] == "press_cake_reensiled"
    )
    assert (pH_reensiled["grass_clover_mean"], pH_reensiled["red_clover_mean"]) == ("4.10", "4.22")
    assert sum(row["source_id"] == "S06_RESCH_2024" for row in sources) == 1
    assert sum(row["filename"] == FILE_NAME for row in manifest) == 1
    assert "exact Creative Commons subtype" in metadata["license_status"]
