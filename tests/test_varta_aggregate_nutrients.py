import csv
from pathlib import Path

import pytest

from Greenhub.phase3_inputs import VARTA_DEFAULT_GRASS_SAMPLE, load_roadside_grass_specification


@pytest.mark.parametrize(
    ("name", "source_field", "reported_g_kg_dm"),
    [
        ("total_nitrogen", "nitrogen_g_kg_dm", 21.0),
        ("total_phosphorus", "phosphorus_g_kg_dm", 2.8),
        ("total_potassium", "potassium_g_kg_dm", 29.1),
    ],
)
def test_varta_aggregate_nutrients_keep_measurement_provenance_and_convert_basis(
    name, source_field, reported_g_kg_dm
):
    source_path = Path("Greenhub/data/Pre-treatment/Feedstock/varta_2026_grass_fiber_measurements.csv")
    with source_path.open(encoding="utf-8-sig", newline="") as source_file:
        source_rows = list(csv.DictReader(source_file))
    source_row = next(row for row in source_rows if row["sample_name_english"] == "Greenhub whole grass")
    dry_matter_fraction = float(source_row["dry_matter_fraction"]) / 100.0
    assert float(source_row[source_field]) == pytest.approx(reported_g_kg_dm)

    feed = load_roadside_grass_specification(
        scenario_id="F1", selected_month="July", sample_id=VARTA_DEFAULT_GRASS_SAMPLE
    )
    record = next(
        item for item in feed.records
        if item.python_name == name and item.sample_id == VARTA_DEFAULT_GRASS_SAMPLE
    )

    assert record.value == pytest.approx(reported_g_kg_dm * dry_matter_fraction / 1000.0)
    assert record.measurement_status == "calculated"
    assert record.source_class == "A"
    assert "wet basis" in record.basis
    assert "row 7" in record.reference
    assert "dry_matter_fraction / 1000" in record.reference
