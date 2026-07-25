import pytest

from Greenhub.systems import create_phase3_scenario


def test_centrifuge_removes_solids_and_retains_soluble_protein():
    model = create_phase3_scenario("F2").simulate()
    raw = model.streams["raw_liquid_fraction"]
    clarified = model.streams["clarified_liquid"]
    sludge = model.streams["primary_sludge"]
    assert clarified.imass["SuspendedProtein"] < raw.imass["SuspendedProtein"]
    assert clarified.imass["SolubleProtein"] / raw.imass["SolubleProtein"] == pytest.approx(0.98)
    assert sludge.imass["Sand"] > clarified.imass["Sand"]

