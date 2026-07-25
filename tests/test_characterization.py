import pytest

from Greenhub.characterization import characterize_feed


def test_complete_feed_data_characterizes(simple_input_mapping):
    result = characterize_feed(simple_input_mapping, ID="characterized_feed")
    assert result.stream.F_mass == pytest.approx(100.0)
    assert result.component_flows_kg_hr["Glucose"] == pytest.approx(1.0)
    assert result.component_flows_kg_hr["Water"] == pytest.approx(98.3)
    assert result.physical.volumetric_flow_m3_hr == pytest.approx(0.1)


def test_inconsistent_feed_data_raises(simple_input_mapping):
    for row in simple_input_mapping["records"]:
        if row["python_name"] == "glucose":
            row["value"] = 1200.0
    with pytest.raises(ValueError, match="exceed total wet feed mass"):
        characterize_feed(simple_input_mapping, ID="inconsistent_feed")


def test_concentration_data_requires_density(simple_input_mapping):
    simple_input_mapping["records"] = [row for row in simple_input_mapping["records"] if row["python_name"] != "density"]
    with pytest.raises(ValueError, match="Density"):
        characterize_feed(simple_input_mapping, ID="no_density_feed")
