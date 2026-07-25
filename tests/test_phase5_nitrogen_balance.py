def test_phase5_total_nitrogen_closes(phase5_snapshot):
    validation = phase5_snapshot.validation
    assert abs(validation.element_errors_kg_hr["nitrogen"]) < 1e-8
    assert validation.element_out_kg_hr["nitrogen"] == validation.element_in_kg_hr["nitrogen"]
