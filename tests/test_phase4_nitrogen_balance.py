
def test_phase4_nitrogen_closes_without_counting_ammonium_as_protein(simulated_phase4_pr3):
    validation = simulated_phase4_pr3.validation
    assert abs(validation.nitrogen_balance["nitrogen_balance_error_kg_hr"]) < 1e-6
    assert validation.protein_balance["protein_entering_kg_hr"] > 0.0
