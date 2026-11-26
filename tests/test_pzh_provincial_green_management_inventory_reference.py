import csv
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
FEEDSTOCK = ROOT / "Greenhub" / "data" / "Pre-treatment" / "Feedstock"
FEATURES = FEEDSTOCK / "pzh_provincial_roadside_and_ditch_management_inventory_2026_reference.csv"
SUMMARY = FEEDSTOCK / "pzh_provincial_roadside_and_ditch_management_by_frequency_2026_reference.csv"


def read_rows(path: Path):
    with path.open(encoding="utf-8-sig", newline="") as stream:
        return list(csv.DictReader(stream))


def test_pzh_management_extract_is_complete_traceable_and_reference_only():
    rows = read_rows(FEATURES)
    assert len(rows) == 16_358
    assert len({row["feature_id"] for row in rows}) == len(rows)
    assert {row["Type"] for row in rows} == {"berm", "slootkant"}
    assert {row["activation_state"] for row in rows} == {"reference_only"}
    assert {row["quality_class"] for row in rows} == {"B"}
    assert {row["source_id"] for row in rows} == {"SRC-PZH-GREEN-MANAGEMENT-2026"}
    assert all(row["feature_id"].startswith("ABS_W_GROEN.") for row in rows)

    counts = {kind: sum(row["Type"] == kind for row in rows) for kind in ("berm", "slootkant")}
    corrected_area = {
        kind: round(sum(float(row["Opp_correctie"]) for row in rows if row["Type"] == kind), 2)
        for kind in counts
    }
    assert counts == {"berm": 9_726, "slootkant": 6_632}
    assert corrected_area == {"berm": 5_885_056.46, "slootkant": 1_752_562.27}


def test_pzh_frequency_aggregate_reconciles_to_feature_extract():
    features = read_rows(FEATURES)
    summary = read_rows(SUMMARY)
    assert len(summary) == 29
    assert sum(int(row["feature_count"]) for row in summary) == len(features)
    for kind in ("berm", "slootkant"):
        source = [row for row in features if row["Type"] == kind]
        aggregated = [row for row in summary if row["feature_type"] == kind]
        assert sum(int(row["feature_count"]) for row in aggregated) == len(source)
        assert round(sum(float(row["slope_corrected_area_sum_m2"]) for row in aggregated), 2) == round(
            sum(float(row["Opp_correctie"]) for row in source), 2
        )
    assert {row["activation_state"] for row in summary} == {"reference_only"}
    assert {row["quality_class"] for row in summary} == {"B"}
    assert all("not harvested grass tonnage" in row["interpretation_limit"] for row in summary)
