from Greenhub.systems import create_phase3_scenario


def test_f0_preserves_measured_liquid_mode():
    model = create_phase3_scenario("F0").simulate()
    assert list(model.units) == ["T101", "C301"]
    assert model.characterization.specification.entry_mode == "measured_liquid"
    assert "fibre_cake" not in model.streams

