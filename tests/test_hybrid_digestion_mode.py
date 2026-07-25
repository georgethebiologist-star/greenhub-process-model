def test_hybrid_mode_uses_one_selected_fate_path(representative_phase5_reactor):
    reactor = representative_phase5_reactor
    assert reactor.parameters.calculation_mode == "hybrid"
    assert reactor.converted_cod_kg_hr > reactor.methane_cod_kg_hr > 0.0
