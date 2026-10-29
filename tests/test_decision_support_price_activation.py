from Greenhub.application.decision_support_service import default_configuration, options


def test_screening_price_activation_is_opt_in_and_documented():
    config = default_configuration()
    assert config["financial_assumptions"]["use_screening_price_benchmarks"] is False
    assert config["use_screening_lca_factors"] is False
    available = options()
    assert "screening_tea_product_prices" in available
    assert "screening_price_activation" in available
    assert available["lca"]["screening_factors"]["electricity"]["source_status"] == "proxy_factor"
    assert "screening_activation" in available["lca"]
