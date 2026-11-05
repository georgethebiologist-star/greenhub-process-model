import csv

from Greenhub.pareto_reporting import pareto_ui_projection
from scripts.run_rvo_pareto_analysis import (
    DEFAULT_FEED_COMPOSITION,
    SUPPORT_CASE_IDS,
    _manifest_for_groups,
    _saleable_products,
    _write_support_ledger,
    pin_default_feed_profile,
)


def test_ui_projection_keeps_reported_scenarios_and_omits_full_evaluation_ledger():
    candidate = {
        'sample_id': 'sample-1',
        'configuration': {'candidate_economics': {'grass_utilization_bonus_eur_per_t_feed': 50}},
        'values': {'npv': 123.0},
        'tea_totals': {'proxy_npv_eur': 123.0},
    }
    source = {
        'schema_version': 'greenhub-rvo-pareto-1.2',
        'created_at_utc': '2026-11-05T00:00:00Z',
        'unrelated_large_field': {'raw_outputs': [1, 2, 3]},
        'groups': {'protein_enabled': {'evaluated_count': 3}},
        'groups_payload': {
            'protein_enabled': {
                'group': 'protein_enabled', 'requested_designs': 2,
                'sample_count': 3, 'evaluated_count': 3, 'rejected_count': 0,
                'fronts': {'net_carbon_vs_npv': {'points': [{'sample_id': 'sample-1'}]}},
                'selected_candidates': {'grass_bonus_sensitivity': [candidate]},
                'samples': [{'raw_outputs': 'large simulation detail'}],
            },
        },
    }

    projected = pareto_ui_projection(source)

    assert projected['schema_version'] == source['schema_version']
    assert projected['groups_payload']['protein_enabled']['selected_candidates']['grass_bonus_sensitivity'][0] == candidate
    assert projected['groups_payload']['protein_enabled']['fronts'] == source['groups_payload']['protein_enabled']['fronts']
    assert 'samples' not in projected['groups_payload']['protein_enabled']
    assert 'unrelated_large_field' not in projected


def test_pareto_configuration_pins_default_profile_without_overriding_explicit_feed():
    defaulted = {'simulation': {}}
    pinned = pin_default_feed_profile(defaulted)
    assert pinned['simulation']['feed_composition'] == DEFAULT_FEED_COMPOSITION

    explicit = {'simulation': {'feed_composition': {'Water': 0.91, 'DryMatter': 0.09}}}
    pin_default_feed_profile(explicit)
    assert explicit['simulation']['feed_composition'] == {'Water': 0.91, 'DryMatter': 0.09}


def test_manifest_reports_all_grant_by_grass_bonus_fronts():
    empty_front = {'points': []}
    group = {
        'requested_designs': 1,
        'sample_count': 0,
        'evaluated_count': 0,
        'rejected_count': 0,
        'fronts': {
            'net_carbon_vs_npv': empty_front,
            'subsidy_vs_npv': empty_front,
            'net_carbon_npv_subsidy': empty_front,
            'by_support_case': {case: empty_front for case in SUPPORT_CASE_IDS},
        },
        'selected_candidates': {case: [] for case in SUPPORT_CASE_IDS},
    }
    manifest = _manifest_for_groups(
        {'protein_enabled': group, 'protein_bypass': group}, workers=1, elapsed_seconds=0,
    )
    assert set(manifest['groups']['protein_enabled']['support_front_counts']) == set(SUPPORT_CASE_IDS)
    assert len(manifest['groups']['protein_bypass']['support_front_counts']) == 24
    assert len(manifest['groups']['protein_enabled']['selected_candidate_counts']) == 24


def test_product_gate_rejects_zero_product_scenarios_and_accepts_any_real_product_flow():
    assert _saleable_products({'products': {
        'dry_protein_product': {'value': 0.0},
        'biomethane': {'value': 0.0},
        'ammonium_product': {'value': 0.0},
    }}) == []
    assert _saleable_products({'products': {
        'dry_protein_product': {'value': 0.0},
        'biomethane': {'value': 0.001},
    }}) == ['biomethane']


def test_published_pareto_excludes_productless_scenarios_and_exposes_more_candidates():
    import json
    from pathlib import Path

    root = Path(__file__).resolve().parents[1]
    payload = json.loads((root / 'Greenhub/results/pareto_rvo_2026/latest_ui.json').read_text(encoding='utf-8'))
    assert payload['product_eligibility']['checked_products']
    for group in ('protein_enabled', 'protein_bypass'):
        data = payload['groups_payload'][group]
        assert len(data['fronts']['by_support_case']) == 24
        assert len(data['selected_candidates']['subsidy_vs_npv']) >= 20
        assert len(data['selected_candidates']['net_carbon_vs_npv']) >= 20
        candidates = [row for rows in data['selected_candidates'].values() for row in rows]
        assert candidates
        assert all(row['product_gate']['eligible'] for row in candidates)
    assert payload['groups_payload']['protein_bypass']['rejected_count'] > 0


def test_traceability_ledger_retains_rejections_and_missing_values_as_blank(tmp_path):
    output = tmp_path / 'scenario-ledger.csv'
    groups = {'protein_bypass': {'samples': [
        {
            'sample_id': 'eligible-1', 'status': 'evaluated', 'support_case': 'C0-GB0',
            'annual': {'feed_processed': {'value': 1000}},
            'product_gate': {'eligible': True, 'saleable_products': ['biomethane']},
            'configuration': {'candidate_economics': {'grass_utilization_bonus_eur_per_t_feed': 0}},
            'tea_totals': {'annual_revenue_eur': 10, 'annual_opex_eur': 4},
            'objectives': {'net_carbon': {'value': 2}},
        },
        {
            'sample_id': 'rejected-1', 'status': 'rejected', 'support_case': 'C0-GB0',
            'product_gate': {'eligible': False, 'saleable_products': []},
            'rejection_reason': 'No saleable product',
        },
    ]}}

    _write_support_ledger(groups, output, include_rejected=True)

    with output.open(encoding='utf-8-sig', newline='') as stream:
        rows = {row['sample_id']: row for row in csv.DictReader(stream)}
    assert set(rows) == {'eligible-1', 'rejected-1'}
    assert rows['rejected-1']['scenario_status'] == 'rejected'
    assert rows['rejected-1']['product_gate_eligible'] == 'False'
    assert rows['rejected-1']['wet_feed_t_per_year'] == ''
    assert rows['eligible-1']['original_operating_profit_eur_per_year'] == '6'
