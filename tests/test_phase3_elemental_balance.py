import pytest

from Greenhub.systems import create_phase3_scenario


def test_phase3_elements_close_with_pef_transfers():
    model = create_phase3_scenario("F2").simulate()
    assert max(abs(value) for value in model.validation.element_errors_kg_hr.values()) == pytest.approx(0.0, abs=1e-9)

