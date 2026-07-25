import pytest

from Greenhub.systems import create_greenhub_system
from Greenhub.validation import validate_mass_balance


def test_phase2_system_uses_characterized_feed():
    model = create_greenhub_system()
    model.system.simulate()
    validation = validate_mass_balance(model)
    assert model.feed_specification.entry_mode == "measured_liquid"
    assert model.characterization.stream is model.streams["feed"]
    assert validation.overall_error_kg_hr == pytest.approx(0.0, abs=1e-6)


def test_repeated_phase2_builds_do_not_reuse_stale_objects():
    first = create_greenhub_system()
    second = create_greenhub_system()
    assert first.flowsheet is not second.flowsheet
    assert first.units["T101"] is not second.units["T101"]
