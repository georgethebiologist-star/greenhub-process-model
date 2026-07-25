"""Compatibility tests retained from the Phase 1 system foundation."""

from Greenhub.systems import create_greenhub_system


def test_system_simulates_and_outlets_are_non_negative():
    model = create_greenhub_system()
    model.system.simulate()
    assert model.streams["clarified_liquid"].F_mass >= 0.0
    assert model.streams["wet_solids"].F_mass >= 0.0


def test_repeated_system_creation_is_stable():
    first = create_greenhub_system()
    first.system.simulate()
    second = create_greenhub_system()
    second.system.simulate()
    assert first.system.ID == second.system.ID
    assert first.flowsheet is not second.flowsheet
    assert second.streams["feed"].ID == "raw_liquid_fraction"
