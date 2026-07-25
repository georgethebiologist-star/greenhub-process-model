def test_phase5_COD_closes_and_methane_is_bounded(phase5_snapshot):
    validation = phase5_snapshot.validation
    assert abs(validation.cod_balance["cod_balance_error_kg_o2_hr"]) < 1e-8
    assert validation.methane_check["methane_total_kg_hr"] <= validation.methane_check["theoretical_methane_ceiling_kg_hr"]
