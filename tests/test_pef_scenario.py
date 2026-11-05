import pytest

from Greenhub.systems import create_phase3_scenario


def test_f2_pef_scenario_remains_disabled_without_validated_activation_data():
    with pytest.raises(ValueError, match="retired|disabled"):
        create_phase3_scenario("F2")

