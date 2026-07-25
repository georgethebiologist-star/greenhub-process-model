def test_VFA_fates_are_recorded_in_acetogenesis(representative_phase5_reactor):
    rows = representative_phase5_reactor.acetogenesis_rows
    assert rows
    assert {row["category"] for row in rows} == {"vfa"}
    assert all(row["converted_cod_kg_hr"] >= 0.0 for row in rows)
