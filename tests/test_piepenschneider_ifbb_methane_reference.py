import csv
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "Greenhub/data/Bigas production + upgrade/Feed BMP/roadside_verge_ifbb_methane_potential_piepenschneider_2016_reference.csv"


def test_piepenschneider_press_fluid_methane_value_preserves_scope_and_maturity():
    with DATA.open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    metadata = json.loads(DATA.with_suffix(".source.json").read_text(encoding="utf-8"))

    assert len(rows) == 1
    row = rows[0]
    assert row["source_id"] == "SRC-PIEPENSCHNEIDER-2016"
    assert row["reported_value"] == "292"
    assert row["reported_unit"] == "L_N CH4/kg VS"
    assert row["basis"] == "Volatile solids in press fluid"
    assert row["qualifier"] == "Highest reported press-fluid yield"
    assert row["quality_class"] == "B"
    assert row["activation_state"] == "reference_only"
    assert metadata["doi"] == "10.1016/j.biombioe.2015.12.012"
    assert "maximum" in metadata["limitations"][0].lower()
    assert "not reported in the abstract" in metadata["method_details"].lower()
