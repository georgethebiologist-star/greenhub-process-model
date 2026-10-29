from pathlib import Path
import pytest

from Greenhub.phase3_inputs import VARTA_DEFAULT_GRASS_SAMPLE, load_roadside_grass_specification


def test_varta_default_grass_profile_is_traceable_and_measured():
    feed = load_roadside_grass_specification(scenario_id="F2", selected_month="July", sample_id=VARTA_DEFAULT_GRASS_SAMPLE)
    solids = next(item for item in feed.records if item.python_name == "total_solids" and item.sample_id == VARTA_DEFAULT_GRASS_SAMPLE)
    assert solids.value == pytest.approx(0.143)
    assert solids.measurement_status == "measured"
    assert "VARTA_2026_10_27" in (solids.reference or "")
    assert Path("Greenhub/data/Pre-treatment/Feedstock/varta_2026_dataset_traceability.csv").exists()
