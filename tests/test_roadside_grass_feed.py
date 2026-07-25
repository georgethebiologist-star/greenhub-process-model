import pytest

from Greenhub.characterization import characterize_feed
from Greenhub.phase3_inputs import load_roadside_grass_specification


def test_roadside_grass_feed_uses_separate_grass_data():
    specification = load_roadside_grass_specification(scenario_id="F2", selected_month="July")
    result = characterize_feed(specification, ID="roadside_grass_test")
    assert specification.entry_mode == "roadside_grass"
    assert result.stream.F_mass == pytest.approx(420000 / (31 * 24))
    assert result.stream.imass["Cellulose"] > 0.0
    assert result.stream.imass["EntrappedSugars"] > 0.0
    assert result.stream.imass["Water"] / result.stream.F_mass == pytest.approx(0.65)

