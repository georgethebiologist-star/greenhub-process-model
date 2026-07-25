def test_phase5_energy_terms_are_explicit_and_nonnegative(phase5_snapshot):
    metrics = phase5_snapshot.metrics
    assert metrics["total_phase5_heat_kw"] >= 0.0
    assert metrics["total_phase5_cooling_kw"] >= 0.0
    assert metrics["total_phase5_electricity_kw"] >= 0.0
    assert metrics["total_phase5_heat_kw"] == metrics["digester_preheat_kw"] + metrics["digester_vessel_heat_loss_kw"]
