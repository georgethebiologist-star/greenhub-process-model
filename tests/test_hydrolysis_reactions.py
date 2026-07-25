def test_hydrolysis_ledger_is_bounded(representative_phase5_reactor):
    rows = representative_phase5_reactor.hydrolysis_rows
    assert rows
    for row in rows:
        assert 0.0 <= row["hydrolyzed_or_accessible_kg_hr"] <= row["inlet_kg_hr"] + 1e-12
        assert 0.0 <= row["hydrolysis_fraction"] <= 1.0
