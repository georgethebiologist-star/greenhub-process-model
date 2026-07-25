
def test_product_quality_metrics_are_physical(simulated_phase4_pr3):
    metrics = simulated_phase4_pr3.metrics
    assert 0.0 < metrics["protein_purity_dry_basis_fraction"] <= 1.0
    assert 0.0 <= metrics["product_moisture_fraction"] < 1.0
    assert metrics["product_classification"] == "unclassified"
