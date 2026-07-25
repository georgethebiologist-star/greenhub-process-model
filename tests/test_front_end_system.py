from Greenhub.systems import create_phase3_scenario


def test_f2_front_end_contains_required_units_and_streams():
    model = create_phase3_scenario("F2").simulate()
    assert list(model.units) == ["U101", "U201", "S201", "C301"]
    assert {"fibre_cake", "raw_liquid_fraction", "clarified_liquid", "primary_sludge"} <= set(model.streams)
    assert all(stream.F_mass >= 0.0 for stream in model.system.streams)

