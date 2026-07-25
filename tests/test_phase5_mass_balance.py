def test_phase5_overall_and_component_mass_close(phase5_snapshot):
    validation = phase5_snapshot.validation
    assert abs(validation.overall_error_kg_hr) < 1e-8
    assert max(abs(value) for value in validation.component_errors_kg_hr.values()) < 1e-8
    assert all(abs(row.mass_error_kg_hr) < 1e-8 for row in validation.unit_balances)
