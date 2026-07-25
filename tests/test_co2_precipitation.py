import pytest

from Greenhub.systems import create_co2_precipitation_system


def test_co2_precipitation_remains_inactive_without_transfer_data():
    with pytest.raises(NotImplementedError, match="CO2 dissolution efficiency"):
        create_co2_precipitation_system()
