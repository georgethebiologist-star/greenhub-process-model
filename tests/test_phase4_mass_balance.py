
def test_phase4_overall_and_component_mass_close(simulated_phase4_pr3):
    validation = simulated_phase4_pr3.validation
    assert abs(validation.overall_error_kg_hr) < 1e-6
    assert max(abs(value) for value in validation.component_errors_kg_hr.values()) < 1e-6
