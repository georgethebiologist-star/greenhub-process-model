from Greenhub.systems import create_phase3_scenario


def test_repeated_scenarios_use_fresh_flowsheets_and_objects():
    first = create_phase3_scenario("F2")
    second = create_phase3_scenario("F2")
    assert first.flowsheet is not second.flowsheet
    assert first.units["U201"] is not second.units["U201"]
    first.simulate()
    second.simulate()
    assert first.metrics == second.metrics

