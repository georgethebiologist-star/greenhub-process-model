"""Support scenarios must never manufacture performance improvements."""
from copy import deepcopy
import json
from pathlib import Path

import pytest

from Greenhub.application.decision_support_service import (
    DEFAULT_BIOMETHANE_BONUS_EUR_PER_M3,
    DEFAULT_BIOMETHANE_BONUS_YEARS,
    _apply_candidate_economics,
    default_configuration,
)


@pytest.mark.parametrize('grant_fraction', [0, .3, .45, .6])
@pytest.mark.parametrize('rate', [0, .08])
def test_original_costs_and_sales_with_legacy_improvements(grant_fraction, rate):
    tea = {'totals': {'annual_revenue_eur': 100, 'annual_opex_eur': 150,
                     'screening_capital_basis_eur': 1000}}
    assumptions = {'labour_reduction': .3, 'logistics_reduction': .25,
                   'energy_reduction': .25, 'protein_yield_uplift': .2,
                   'nutrient_recovery_uplift': .15, 'capex_grant_fraction': grant_fraction,
                   'discount_rate': rate, 'project_lifetime_years': 20,
                   'opex_support_years': 15, 'opex_premium_eur_per_t_feed': 10}
    original = deepcopy(assumptions)
    result = _apply_candidate_economics(tea, assumptions, {'feed_processed': {'value': 2000}})
    totals = result['totals']
    assert assumptions == original
    assert totals['optimized_annual_revenue_eur'] == 100
    assert totals['optimized_annual_opex_eur'] == 150
    assert totals['optimization_savings_eur_per_year'] == 0
    assert totals['optimization_revenue_uplift_eur_per_year'] == 0
    assert 'labour_reduction' not in result['candidate_economics']['assumptions']
    expected = -1000 * (1-grant_fraction)
    expected += sum((-50 + (20 if year <= 15 else 0))/(1+rate)**year for year in range(1,21))
    assert totals['proxy_npv_eur'] == pytest.approx(expected)
    assert totals['proxy_npv_eur'] < 0


def test_retired_generic_subsidy_cannot_generate_a_grant():
    tea = {'totals': {'annual_revenue_eur': 100, 'annual_opex_eur': 150,
                     'screening_capital_basis_eur': 1000}}
    result = _apply_candidate_economics(tea, {'subsidy_rate': .2, 'eligible_capex_fraction': 1})
    assert result['totals']['subsidy_eur'] == 0


def test_biomethane_bonus_has_backend_default_and_uses_simulated_volume():
    defaults = default_configuration()['candidate_economics']
    assert defaults['biomethane_bonus_eur_per_m3'] == DEFAULT_BIOMETHANE_BONUS_EUR_PER_M3
    assert defaults['biomethane_bonus_years'] == DEFAULT_BIOMETHANE_BONUS_YEARS
    assert defaults['biomethane_bonus_enabled'] is False

    tea = {'totals': {'annual_revenue_eur': 100, 'annual_opex_eur': 50,
                     'screening_capital_basis_eur': 100}}
    result = _apply_candidate_economics(
        tea,
        {'biomethane_bonus_enabled': True, 'annual_biomethane_m3': 100},
        {'feed_processed': {'value': 0}},
    )
    economics = result['candidate_economics']
    assert economics['biomethane_bonus_eur_per_year'] == pytest.approx(187)
    assert economics['assumptions']['biomethane_bonus_eur_per_m3'] == DEFAULT_BIOMETHANE_BONUS_EUR_PER_M3
    assert economics['opex_support_years'] == 15

    override_tea = {'totals': {'annual_revenue_eur': 100, 'annual_opex_eur': 50,
                              'screening_capital_basis_eur': 100}}
    override = _apply_candidate_economics(
        override_tea,
        {'biomethane_bonus_enabled': True, 'annual_biomethane_m3': 100,
         'biomethane_bonus_eur_per_m3': 2.25, 'biomethane_bonus_years': 4},
        {'feed_processed': {'value': 0}},
    )['candidate_economics']
    assert override['biomethane_bonus_eur_per_year'] == pytest.approx(225)
    assert override['opex_support_years'] == 4


def test_all_published_scenarios_reconcile_to_original_operating_margin():
    source = Path(__file__).resolve().parents[1] / 'Greenhub/results/pareto_rvo_2026/latest.json'
    data = json.loads(source.read_text())
    for group in data['groups_payload'].values():
        by_id = {row['sample_id']: row for row in group['samples']}
        for row in group['samples']:
            if row.get('status') != 'evaluated':
                continue
            totals = row['tea_totals']
            assumptions = row['configuration']['candidate_economics']
            cash = totals['annual_revenue_eur'] - totals['annual_opex_eur']
            cash_flows = row['candidate_economics']['annual_cash_flows_eur']
            expected = sum(flow / (1 + assumptions['discount_rate'])**year
                           for year, flow in enumerate(cash_flows))
            assert totals['proxy_npv_eur'] == pytest.approx(expected, abs=.001)
            assert 'after-tax' in totals['proxy_npv_basis'].lower()
            assert totals['optimized_annual_revenue_eur'] == totals['annual_revenue_eur']
            assert totals['optimized_annual_opex_eur'] == totals['annual_opex_eur']
            assert totals['optimization_savings_eur_per_year'] == 0
            assert totals['optimization_revenue_uplift_eur_per_year'] == 0
            assert row['objectives']['operating_profit']['value'] == pytest.approx(cash)
            for key in ('labour_reduction', 'logistics_reduction', 'energy_reduction',
                        'protein_yield_uplift', 'nutrient_recovery_uplift'):
                assert key not in assumptions
        # Independently verify that every advertised frontier member is
        # nondominated under the recalculated objective values.
        for name, keys in [('net_carbon_vs_npv', ('net_carbon', 'npv')),
                           ('subsidy_vs_npv', ('subsidy_granted', 'npv')),
                           ('net_carbon_npv_subsidy', ('net_carbon', 'npv', 'subsidy_granted'))]:
            for point in group['fronts'][name]['points']:
                current = by_id[point['sample_id']]
                def score(row):
                    return tuple(row['objectives'][key]['value'] * (1 if key == 'npv' else -1) for key in keys)
                scores = score(current)
                for other in group['samples']:
                    if not all(other['objectives'][key]['eligible'] for key in keys):
                        continue
                    candidate = score(other)
                    assert not (all(a >= b for a, b in zip(candidate, scores))
                                and any(a > b for a, b in zip(candidate, scores)))
