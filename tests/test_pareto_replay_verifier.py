from scripts.verify_pareto_replay import process_request_cache_key


def test_replay_cache_ignores_only_post_route_financial_and_lca_overlays():
    base = {
        "simulation": {"scenarios": {"protein_recovery": "PR1"}, "feed": {"kg_hr": 1000}},
        "candidate_economics": {"capex_grant_fraction": 0.0, "grass_utilization_bonus_eur_per_t_feed": 0},
        "tea": {"electricity_cost_eur_per_mwh": 70},
        "lca": {"electricity_factor": 0.2},
    }
    finance_overlay = {
        **base,
        "candidate_economics": {"capex_grant_fraction": 0.6, "grass_utilization_bonus_eur_per_t_feed": 50},
        "tea": {"electricity_cost_eur_per_mwh": 120},
        "lca": {"electricity_factor": 0.7},
    }
    changed_process = {**base, "simulation": {**base["simulation"], "feed": {"kg_hr": 2000}}}

    assert process_request_cache_key(base) == process_request_cache_key(finance_overlay)
    assert process_request_cache_key(base) != process_request_cache_key(changed_process)


def test_replay_cache_separates_screening_process_assumption_mode():
    configuration = {"simulation": {"scenarios": {"protein_recovery": "PR1"}}}
    screened = {**configuration, "use_screening_process_assumptions": True}

    assert process_request_cache_key(configuration) != process_request_cache_key(screened)
