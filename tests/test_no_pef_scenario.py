from Greenhub.systems import create_phase3_scenario


def test_f1_has_no_pef_and_lower_electricity():
    no_pef = create_phase3_scenario("F1").simulate()
    pef = create_phase3_scenario("F2").simulate()
    assert "U201" not in no_pef.units
    assert no_pef.metrics["total_front_end_electricity_kw"] < pef.metrics["total_front_end_electricity_kw"]

