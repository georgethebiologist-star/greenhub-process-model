def test_phase5_carbon_closes(phase5_snapshot):
    assert abs(phase5_snapshot.validation.element_errors_kg_hr["carbon"]) < 1e-8
