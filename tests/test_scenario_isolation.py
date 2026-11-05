from Greenhub.systems import create_phase3_scenario


def test_repeated_scenarios_use_fresh_flowsheets_and_objects():
    first = create_phase3_scenario("F1")
    second = create_phase3_scenario("F1")
    assert first.flowsheet is not second.flowsheet
    assert first.units["S201"] is not second.units["S201"]
    assert "U201" not in first.units and "U201" not in second.units
    first.simulate()
    second.simulate()
    assert first.metrics == second.metrics

