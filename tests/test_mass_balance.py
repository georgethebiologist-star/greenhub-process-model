"""Phase 1 and Phase 2 mass-closure regression tests."""

import pytest

from Greenhub.systems import create_greenhub_system
from Greenhub.validation import validate_mass_balance


def test_overall_component_and_element_balances_close():
    model = create_greenhub_system()
    model.system.simulate()
    result = validate_mass_balance(model)
    assert result.overall_error_kg_hr == pytest.approx(0.0, abs=1e-6)
    assert max(abs(i) for i in result.component_errors_kg_hr.values()) <= 1e-6
    assert max(abs(i) for i in result.element_errors_kg_hr.values()) <= 1e-6


def test_expected_solids_recovery_occurs():
    model = create_greenhub_system()
    model.system.simulate()
    assert model.streams["wet_solids"].imass["SuspendedSolids"] > model.streams["clarified_liquid"].imass["SuspendedSolids"]
    assert model.streams["wet_solids"].imass["InertSolids"] > model.streams["clarified_liquid"].imass["InertSolids"]
