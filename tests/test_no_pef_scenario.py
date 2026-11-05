import pytest

from Greenhub.systems import create_phase3_scenario


def test_only_non_pef_front_end_routes_are_enabled():
    active = create_phase3_scenario("F1").simulate()
    assert "U201" not in active.units
    for retired in ("F2", "F3"):
        with pytest.raises(ValueError, match="retired|disabled"):
            create_phase3_scenario(retired)

