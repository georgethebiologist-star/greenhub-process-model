import pytest

from Greenhub.systems import create_phase4_scenario


@pytest.mark.parametrize("scenario", ["PR4", "PR5", "PR6"])
def test_inactive_alternatives_raise_with_missing_requirements(scenario):
    with pytest.raises(NotImplementedError, match="data are missing"):
        create_phase4_scenario(scenario)
