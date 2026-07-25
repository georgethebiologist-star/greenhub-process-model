def test_phase5_total_sulphur_closes(phase5_snapshot):
    validation = phase5_snapshot.validation
    assert abs(validation.element_errors_kg_hr["sulfur"]) < 1e-8
    assert validation.element_out_kg_hr["sulfur"] == validation.element_in_kg_hr["sulfur"]
