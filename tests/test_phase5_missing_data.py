import pytest

from Greenhub.phase5_inputs import load_phase5_inputs
from Greenhub.phase5_units import digestion_parameters_from_mapping


def test_required_missing_and_invalid_values_fail_but_optional_blank_is_safe(phase5_values):
    missing = dict(phase5_values)
    missing.pop("digester_hrt_days")
    with pytest.raises(ValueError, match="digester_hrt_days"):
        digestion_parameters_from_mapping(missing, enabled=True)
    invalid = dict(phase5_values, methanogenesis_conversion=1.1)
    with pytest.raises(ValueError, match="within"):
        digestion_parameters_from_mapping(invalid, enabled=True)
    bundle = load_phase5_inputs(scenario_id="AD1")
    assert "ammonia_inhibition_constant_kg_n_m3" not in bundle.parameter_values
    assert not bool(bundle.parameter_values["free_ammonia_inhibition_enabled"])
