from Greenhub.systems import create_phase3_scenario


def test_f2_improves_liquid_and_soluble_protein_recovery():
    no_pef = create_phase3_scenario("F1").simulate()
    pef = create_phase3_scenario("F2").simulate()
    assert pef.metrics["raw_liquid_flow_kg_hr"] > no_pef.metrics["raw_liquid_flow_kg_hr"]
    assert pef.metrics["soluble_protein_in_raw_liquid_kg_hr"] > no_pef.metrics["soluble_protein_in_raw_liquid_kg_hr"]

