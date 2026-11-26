from scripts.verify_pareto_replay import representative_design_rows


def test_replay_verifier_fills_designs_missing_preferred_support_case():
    catalog = [
        {"sample_id": "A0", "design_id": "route-a", "support_case": "C0-GB0"},
        {"sample_id": "A1", "design_id": "route-a", "support_case": "C0-GB10"},
        {"sample_id": "B1", "design_id": "route-b", "support_case": "C45-GB30"},
    ]

    selected = representative_design_rows(catalog)

    assert set(selected) == {"route-a", "route-b"}
    assert selected["route-a"]["sample_id"] == "A0"
    assert selected["route-b"]["sample_id"] == "B1"
