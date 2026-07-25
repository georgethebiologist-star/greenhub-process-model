def test_methanogenesis_respects_available_COD(representative_phase5_reactor):
    row = representative_phase5_reactor.methanogenesis_rows[0]
    assert 0.0 <= row["methane_cod_kg_hr"] <= row["available_methanogenic_cod_kg_hr"]
    assert row["methane_kg_hr"] > 0.0
