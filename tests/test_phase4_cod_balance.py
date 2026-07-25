
def test_phase4_cod_and_toc_are_redistributed_not_destroyed(simulated_phase4_pr3):
    validation = simulated_phase4_pr3.validation
    assert abs(validation.cod_balance["cod_balance_error_kg_hr"]) < 1e-6
    assert abs(validation.toc_balance["toc_balance_error_kg_hr"]) < 1e-6
