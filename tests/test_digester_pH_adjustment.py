import pytest

from Greenhub.phase5_units import conditioning_parameters_from_mapping


def test_pH_conditioning_is_bounded_metadata(phase5_values):
    parameters = conditioning_parameters_from_mapping(phase5_values, enabled=True)
    assert parameters.target_pH >= parameters.inlet_pH
    bad = dict(phase5_values, target_digester_feed_pH=6.0)
    with pytest.raises(ValueError, match="cannot be below"):
        conditioning_parameters_from_mapping(bad, enabled=True)
