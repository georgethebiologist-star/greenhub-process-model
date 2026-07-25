def test_acidogenesis_is_separate_from_hydrolysis(representative_phase5_reactor):
    reactor = representative_phase5_reactor
    assert reactor.acidogenesis_rows
    for row in reactor.acidogenesis_rows:
        assert row["ultimately_converted_kg_hr"] <= row["accessible_kg_hr"] + 1e-12
