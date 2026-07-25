
def test_phase4_tracked_elements_close(simulated_phase4_pr3):
    assert max(
        abs(value) for value in simulated_phase4_pr3.validation.element_errors_kg_hr.values()
    ) < 1e-6
