import csv
import json
from pathlib import Path

from biorefinery_platform.data_catalog import build_dataset_reuse_catalog


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "Greenhub/data/Pre-treatment/Mechanical"


def _rows(path: Path):
    with path.open("r", encoding="utf-8-sig", newline="") as file:
        return list(csv.DictReader(file))


def test_king_2012_table_values_are_traceable_and_reference_only():
    path = DATA / "king_2012_grass_silage_fractionation_table_data_reference.csv"
    rows = _rows(path)
    assert len(rows) == 33
    assert len({row["record_id"] for row in rows}) == 33
    assert all(row["quality_class"] == "B" for row in rows)
    assert all(row["activation_state"] == "reference_only" for row in rows)
    assert all(row["runtime_usage"] == "reference_only; not calculation-connected" for row in rows)

    table2 = [row for row in rows if row["table_id"] == "Table 2"]
    observed = {
        (float(row["press_pressure_mpa"]), int(row["wash_count"]), row["response_parameter"]): float(row["reported_value"])
        for row in table2
    }
    assert observed[(1.5, 1, "solubles_response_fraction")] == 0.88
    assert observed[(3.0, 2, "press_cake_dry_matter")] == 310
    assert observed[(4.5, 3, "press_cake_ndf")] == 787
    ambiguous = [row for row in rows if row["response_parameter"] == "solubles_response_fraction"]
    assert all("do not use" in row["data_definition_note"].lower() for row in ambiguous)
    assert any("definition conflict" in row["data_definition_note"].lower() for row in ambiguous)
    assert any("footnote states solubles in press-cake" in row["data_definition_note"] for row in ambiguous)

    metadata = json.loads(path.with_name(path.name + ".source.json").read_text(encoding="utf-8"))
    assert metadata["source_url"].startswith("https://www.europeangrassland.org/")
    assert "rights" in metadata["license"].lower()
    assert metadata["runtime_mapping"] == "none"


def test_king_datasets_are_indexed_as_feed_and_protocol_specific():
    catalog = build_dataset_reuse_catalog()
    selected = {
        row["filename"]: row
        for row in catalog
        if str(row["filename"]).startswith("king_2012_grass_silage_")
    }
    assert set(selected) == {
        "king_2012_grass_silage_pressing_design_evidence_reference.csv",
        "king_2012_grass_silage_fractionation_table_data_reference.csv",
    }
    assert all(row["technology_family_id"] == "pretreatment_fractionation" for row in selected.values())
    assert all(row["portability_class"] == "technology_and_feedstock_specific" for row in selected.values())
    assert all(row["linked_source_count"] >= 1 for row in selected.values())
