import csv
import json
import pytest


def test_pareto_design_request_uses_traceable_monthly_zeeland_supply():
    import json
    import scripts.run_rvo_pareto_analysis as runner
    from Greenhub.application.contracts import SimulationRequest

    base = json.loads(runner.SOURCE.read_text(encoding="utf-8"))["configuration"]
    runner.pin_default_feed_profile(base)
    design = runner.make_designs(base, "protein_enabled", 1, runner.SEED)[0]
    request = SimulationRequest.from_dict(design["configuration"]["simulation"])
    schedule = request.biomass_schedule
    assert schedule.annual_available_biomass_tonnes == pytest.approx(25300)
    assert sum(schedule.monthly_availability_tonnes) == pytest.approx(25300)
    assert sum(schedule.monthly_availability_tonnes[5:8]) == pytest.approx(25300)
    assert sum(schedule.monthly_availability_tonnes[8:11]) == pytest.approx(0)
    assert schedule.availability_evidence_class == "B"
    assert schedule.availability_temporal_profile_quality_class == "C"
    assert schedule.availability_source_id == "SRC-MOOV-VITO-2021"
    assert design["configuration"]["simulation"]["time_step"] == "monthly"
    supply = runner._zeeland_two_cut_supply()
    assert supply["summer_tonnes"] + supply["autumn_tonnes"] == pytest.approx(supply["annual_tonnes"])
    assert sum(supply["monthly_tonnes"]) == pytest.approx(supply["annual_tonnes"])
    assert supply["source_locations"]["ZL-TWO-CUT-SUMMER"] == "Table 11; PDF p.32"


def test_harvest_scenario_descriptions_distinguish_source_totals_from_timing_assumptions():
    import scripts.run_rvo_pareto_analysis as runner

    regimes = {item["id"]: item for item in runner.HARVEST_REGIMES}
    assert set(regimes) == {
        "ZEELAND_ONE_CUT_LATE_SUMMER",
        "ZEELAND_ONE_CUT_LATE_AUTUMN",
        "ZEELAND_TWO_CUT_JUNE_AUGUST",
        "ZEELAND_TWO_CUT_JUNE_LATE_AUTUMN",
    }
    assert "scenario assumption" in " ".join(regimes["ZEELAND_ONE_CUT_LATE_SUMMER"]["harvest_windows"])
    assert "C-class scenario assumption" in " ".join(regimes["ZEELAND_ONE_CUT_LATE_AUTUMN"]["harvest_windows"])
    for regime_id in ("ZEELAND_TWO_CUT_JUNE_AUGUST", "ZEELAND_TWO_CUT_JUNE_LATE_AUTUMN"):
        window = " ".join(regimes[regime_id]["harvest_windows"])
        assert "broad summer and autumn totals" in window
        assert "source does not specify exact cut dates" in window
        assert "June, then late August" not in window


def test_dated_harvest_events_shift_into_processing_months_and_close_delay_inventory():
    from Greenhub.application.biomass_schedule import schedule_feed_rows
    from Greenhub.application.contracts import BiomassSchedule
    from Greenhub.time_grid import generate_time_grid

    config = BiomassSchedule(
        annual_available_biomass_tonnes=42_300.0,
        annual_processed_biomass_tonnes=42_300.0,
        processing_delay_days=14,
        collection_refinery_fraction=1.0,
        season_start="2026-06-01",
        season_end="2026-11-15",
        peak_date="2026-07-31",
        active_months=(6, 7, 8, 9, 10, 11),
        harvest_events=(
            {"date": "2026-07-31", "available_biomass_tonnes": 25_300.0},
            {"date": "2026-10-31", "available_biomass_tonnes": 17_000.0},
        ),
    )
    rows = schedule_feed_rows(
        config,
        generate_time_grid("2026-01-01", "2026-12-31", "monthly"),
        processing_delay_days=14,
    )

    assert sum(row["available_wet_biomass_kg"] for row in rows) == pytest.approx(42_300_000.0)
    assert sum(row["harvested_biomass_kg"] for row in rows) == pytest.approx(42_300_000.0)
    assert sum(row["collected_biomass_kg"] for row in rows) == pytest.approx(42_300_000.0)
    by_month = {row["time"]: row for row in rows}
    assert by_month["2026-07"]["harvest_event_dates"] == ("2026-07-31",)
    assert by_month["2026-08"]["processing_release_dates"] == ("2026-08-14",)
    assert by_month["2026-10"]["harvest_event_dates"] == ("2026-10-31",)
    assert by_month["2026-11"]["processing_release_dates"] == ("2026-11-14",)
    assert by_month["2026-07"]["available_wet_biomass_kg"] == pytest.approx(25_300_000.0)
    assert by_month["2026-10"]["available_wet_biomass_kg"] == pytest.approx(17_000_000.0)
    assert rows[-1]["collection_delay_inventory_remaining_kg"] == pytest.approx(0.0, abs=1e-8)
    assert all(abs(row["collection_delay_inventory_residual_kg"]) < 1e-8 for row in rows)


def test_monthly_availability_is_not_collected_outside_active_months():
    from Greenhub.application.biomass_schedule import build_empirical_biomass_schedule
    from Greenhub.application.contracts import BiomassSchedule

    monthly_supply = (10.0, 0.0, 0.0, 0.0, 0.0, 0.0, 10.0, 0.0, 0.0, 0.0, 0.0, 0.0)
    schedule = build_empirical_biomass_schedule(BiomassSchedule(
        annual_available_biomass_tonnes=20.0,
        annual_processed_biomass_tonnes=20.0,
        feed_basis="tonnes_per_year",
        season_start="2026-01-01",
        season_end="2026-12-31",
        peak_date="2026-07-15",
        active_months=(7,),
        monthly_availability_tonnes=monthly_supply,
    ))

    assert schedule["monthly"][0]["operating_hours"] == 0.0
    assert schedule["monthly"][0]["processed_biomass_tonnes"] == 0.0
    assert schedule["monthly"][6]["processed_biomass_tonnes"] == pytest.approx(10.0)
    assert schedule["annual_available_tonnes"] == pytest.approx(20.0)
    assert schedule["annual_processed_tonnes"] == pytest.approx(10.0)
    assert schedule["annual_unused_tonnes"] == pytest.approx(10.0)

from Greenhub.pareto_reporting import (
    load_pareto_results,
    pareto_ui_projection,
    publish_pareto_ui_artifacts,
)
from scripts.run_rvo_pareto_analysis import (
    DEFAULT_FEED_COMPOSITION,
    SUPPORT_CASE_IDS,
    _manifest_for_groups,
    _saleable_products,
    _scenario_catalog,
    _annual_biomethane_volume_nm3,
    _write_support_ledger,
    make_designs,
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
                'scenario_catalog': [candidate],
                'samples': [{'raw_outputs': 'large simulation detail'}],
            },
        },
    }

    projected = pareto_ui_projection(source)

    assert projected['schema_version'] == source['schema_version']
    assert projected['groups_payload']['protein_enabled']['selected_candidates']['grass_bonus_sensitivity'][0] == candidate
    assert projected['groups_payload']['protein_enabled']['scenario_catalog'] == [candidate]
    assert projected['groups_payload']['protein_enabled']['fronts'] == source['groups_payload']['protein_enabled']['fronts']
    assert 'samples' not in projected['groups_payload']['protein_enabled']
    assert 'unrelated_large_field' not in projected


def test_api_and_static_preview_publish_the_same_bounded_scenario_catalog(tmp_path):
    candidate = {'sample_id': 'seasonal-run', 'configuration': {'simulation': {
        'biomass_schedule': {'monthly_availability_tonnes': [0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0]}
    }}}
    source = {'groups_payload': {'protein_enabled': {'scenario_catalog': [candidate]}}}
    api_path = tmp_path / 'results' / 'latest_ui.json'
    preview_path = tmp_path / 'frontend' / 'public' / 'greenhub-pareto-latest.json'
    publish_pareto_ui_artifacts(source, api_path, preview_path)
    api_payload = json.loads(api_path.read_text(encoding='utf-8'))
    preview_payload = json.loads(preview_path.read_text(encoding='utf-8'))
    assert api_payload == preview_payload
    assert api_payload['groups_payload']['protein_enabled']['scenario_catalog'][0] == candidate


def test_pareto_configuration_pins_default_profile_without_overriding_explicit_feed():
    defaulted = {'simulation': {}}
    pinned = pin_default_feed_profile(defaulted)
    assert pinned['simulation']['feed_composition'] == DEFAULT_FEED_COMPOSITION

    explicit = {'simulation': {'feed_composition': {'Water': 0.91, 'DryMatter': 0.09}}}
    pin_default_feed_profile(explicit)
    assert explicit['simulation']['feed_composition'] == {'Water': 0.91, 'DryMatter': 0.09}


def test_pareto_designs_use_saved_seasonal_schedule_and_route_inputs():
    import json
    import scripts.run_rvo_pareto_analysis as runner
    from pathlib import Path

    root = Path(__file__).resolve().parents[1]
    base = json.loads((root / 'results/report_figures/no_pef_F1.json').read_text(encoding='utf-8'))['configuration']
    design = make_designs(base, 'protein_bypass', 1, 17)[0]
    simulation = design['configuration']['simulation']
    schedule = simulation['biomass_schedule']

    assert simulation['resolution_mode'] == 'quasi_dynamic'
    assert simulation['start_date'] == '2026-01-01'
    assert simulation['end_date'] == '2026-12-31'
    assert simulation['time_step'] == 'monthly'
    assert simulation['wet_feed_rate_kg_hr'] is None
    assert (schedule['season_start'], schedule['season_end']) == ('2026-06-01', '2026-08-31')
    assert schedule['annual_available_biomass_tonnes'] == pytest.approx(25300)
    assert schedule['availability_evidence_class'] == 'B'
    assert '25,300 t fresh/year' in schedule['availability_note']
    assert sum(schedule['monthly_availability_tonnes'][5:8]) == pytest.approx(25300)
    assert 0 < schedule['annual_processed_biomass_tonnes'] <= schedule['annual_available_biomass_tonnes']
    assert simulation['annual_biomass_target'] == schedule['annual_processed_biomass_tonnes'] * 1000
    assert simulation['operating_schedule']['target_throughput_kg_hr'] == schedule['feed_kg_per_hr']
    assert simulation['scenarios']['protein_recovery'] == 'PR0'
    from Greenhub.application.contracts.requests import SimulationRequest
    parsed_request = SimulationRequest.from_dict(simulation)
    assert parsed_request.biomass_schedule is not None
    assert parsed_request.biomass_schedule.season_start == schedule['season_start']
    assert parsed_request.biomass_schedule.season_end == schedule['season_end']
    assert parsed_request.scenarios.protein_recovery == 'PR0'
    assert schedule['availability_temporal_profile_quality_class'] == 'C'
    assert schedule['availability_source_id'] == 'SRC-MOOV-VITO-2021'
    assert 1 <= len(schedule['active_months']) < 12
    from scripts.run_rvo_pareto_analysis import HARVEST_REGIMES
    designs = make_designs(base, 'protein_bypass', len(HARVEST_REGIMES), 17)
    assert {item['seasonal_profile']['regime_id'] for item in designs} == {item['id'] for item in HARVEST_REGIMES}
    assert all(item['seasonal_profile']['quality_class'] == 'B' for item in designs)
    assert all(item['seasonal_profile']['within_window_profile_quality_class'] == 'C' for item in designs)
    assert len({tuple(item['configuration']['simulation']['biomass_schedule']['monthly_availability_tonnes']) for item in designs}) == len(HARVEST_REGIMES)
    assert {item['configuration']['simulation']['biomass_schedule']['annual_available_biomass_tonnes'] for item in designs} == {25300, 42300}
    for regime, item in zip(HARVEST_REGIMES, designs):
        simulation = item['configuration']['simulation']
        schedule = simulation['biomass_schedule']
        hours = runner._effective_processing_hours(regime, 14, 7, 24)
        assert schedule['annual_processed_biomass_tonnes'] == pytest.approx(
            min(schedule['annual_available_biomass_tonnes'], schedule['feed_kg_per_hr'] * hours / 1000)
        )
        from Greenhub.application.biomass_schedule import schedule_feed_rows
        from Greenhub.time_grid import generate_time_grid
        grid = generate_time_grid('2026-01-01', '2026-12-31', 'monthly')
        feed_rows = schedule_feed_rows(
            SimulationRequest.from_dict(simulation).biomass_schedule,
            grid,
            processing_delay_days=14,
        )
        assert sum(row['available_wet_biomass_kg'] for row in feed_rows) / 1000 == pytest.approx(
            schedule['annual_available_biomass_tonnes']
        )
        assert sum(row['collected_biomass_kg'] for row in feed_rows) / 1000 == pytest.approx(
            schedule['annual_processed_biomass_tonnes']
        )


def test_pareto_normalizes_biomethane_mass_to_the_shared_normal_volume_basis():
    from scripts.run_rvo_pareto_analysis import BIOMETHANE_DENSITY_KG_PER_NM3

    assert BIOMETHANE_DENSITY_KG_PER_NM3 == pytest.approx(0.71751)
    annual = {
        'products': {'biomethane': {'value': 823.3154767747374, 'unit': 'kg/year'}},
        'volumetric_products': {'biomethane': {'value': 862.5349317375517, 'unit': 'm3/year'}},
    }
    volume, basis = _annual_biomethane_volume_nm3(annual)
    assert volume == pytest.approx(823.3154767747374 / BIOMETHANE_DENSITY_KG_PER_NM3)
    assert basis == 'annual.products.biomethane.kg_divided_by_traceable_kg_per_Nm3_density'

    fallback, fallback_basis = _annual_biomethane_volume_nm3({'volumetric_products': annual['volumetric_products']})
    assert fallback == 862.5349317375517
    assert fallback_basis == 'fallback_annual.volumetric_products.biomethane_model_condition_m3'


def test_scenario_catalog_balances_support_cases_and_keeps_runnable_inputs():
    from scripts.run_rvo_pareto_analysis import GRASS_BONUS_RATES_EUR_PER_WET_T, SUPPORT_SCENARIOS

    rows = []
    for design_index in range(42):
        for grant_id in SUPPORT_SCENARIOS:
            for bonus in GRASS_BONUS_RATES_EUR_PER_WET_T:
                case = f'{grant_id}-GB{bonus}'
                rows.append({
                    'status': 'evaluated', 'sample_id': f'D{design_index}-{case}',
                    'design_id': f'D{design_index}', 'support_case': case,
                    'configuration': {'simulation': {'scenarios': {'protein_recovery': 'PR0'},
                        'biomass_schedule': {'annual_available_biomass_tonnes': 30000,
                            'annual_processed_biomass_tonnes': 1000}},
                        'candidate_economics': {'grass_utilization_bonus_eur_per_t_feed': bonus}},
                    'objectives': {'npv': {'value': 1}, 'climate': {'value': 2}},
                    'tea_totals': {}, 'candidate_economics': {}, 'lca_totals': {},
                    'lca_readiness': {}, 'lca_missing_inputs': [],
                    'seasonal_profile': {'regime_id': 'AUG_SINGLE_CUT', 'quality_class': 'B'},
                    'annual': {'feed_processed': {'value': 800000}, 'biomass_schedule': {
                        'ending_inventory_tonnes': 100,
                        'annual_operating_hours': 336,
                        'monthly': [
                        {'time_label': '2026-08', 'available_biomass_tonnes': 800,
                         'collected_at_harvest_tonnes': 700,
                         'collected_for_processing_tonnes': 650,
                         'collection_delay_harvest_tonnes': 700,
                         'collection_delay_release_tonnes': 650,
                         'collection_delay_inventory_entering_tonnes': 0,
                         'collection_delay_inventory_remaining_tonnes': 50,
                         'collection_delay_inventory_peak_tonnes': 50,
                         'collection_delay_inventory_mass_residual_tonnes': 0,
                         'processed_biomass_tonnes': 700,
                         'uncollected_biomass_tonnes': 100,
                         'operating_hours': 336,
                         'basis_feed_kg_per_hr': 2083.3333333333335,
                         'utilization_fraction': 0.875,
                         'utilization_basis': 'collected_at_harvest / available_biomass',
                         'ending_inventory_tonnes': 100,
                         'storage_inventory_entering_tonnes': 0,
                         'biomass_received_after_storage_conditions_tonnes': 800,
                         'storage_withdrawn_tonnes': 700,
                         'storage_overflow_tonnes': 0,
                         'storage_degradation_loss_tonnes': 0,
                         'storage_mass_residual_tonnes': 0},
                    ]}},
                    'feasibility': {'eligible_for_ranking': True},
                    'product_gate': {'eligible': True},
                })
    catalog = _scenario_catalog(rows)
    expected_cases = {
        f'{grant_id}-GB{bonus}'
        for grant_id in SUPPORT_SCENARIOS
        for bonus in GRASS_BONUS_RATES_EUR_PER_WET_T
    }
    assert len(catalog) == 100
    assert len({row['sample_id'] for row in catalog}) == 100
    assert {row['support_case'] for row in catalog} == expected_cases
    counts = {case: sum(row['support_case'] == case for row in catalog) for case in expected_cases}
    assert set(counts.values()) <= {4, 5}
    assert all(row['configuration']['simulation']['biomass_schedule'] for row in catalog)
    assert all(row['seasonal_availability_profile']['regime_id'] == 'AUG_SINGLE_CUT' for row in catalog)
    assert all(row['seasonal_feed_profile'][0]['available_biomass_tonnes'] == 800 for row in catalog)
    profile = catalog[0]['seasonal_feed_profile'][0]
    assert profile['collected_at_harvest_tonnes'] == 700
    assert profile['collected_for_processing_tonnes'] == 650
    assert profile['operating_hours'] == 336
    assert profile['ending_inventory_tonnes'] == 100
    assert profile['storage_withdrawn_tonnes'] == 700
    assert profile['collection_delay_harvest_tonnes'] == 700
    assert profile['collection_delay_release_tonnes'] == 650
    assert profile['collection_delay_inventory_remaining_tonnes'] == 50
    assert profile['collection_delay_inventory_mass_residual_tonnes'] == 0
    assert catalog[0]['ending_inventory_tonnes'] == 100
    assert catalog[0]['annual_processing_operating_hours'] == 336
    assert profile['utilization_basis'] == 'collected_at_harvest / available_biomass'
    assert all(row['requested_feed_target_tonnes'] == 1000 for row in catalog)
    assert all(row['actual_feed_processed_tonnes'] == 800 for row in catalog)
    assert all(row['unmet_feed_target_tonnes'] == 200 for row in catalog)


def test_compact_scenario_catalog_preserves_support_and_harvest_regimes():
    from Greenhub.pareto_reporting import compact_pareto_scenario_catalog

    candidates = []
    support_cases = ('C0-GB0', 'C30-GB10', 'C45-GB30', 'C60-GB50')
    regimes = ('one_cut_summer', 'one_cut_autumn', 'two_cut_summer', 'two_cut_autumn')
    for support_case in support_cases:
        for regime in regimes:
            for variant in range(4):
                candidates.append({
                    'sample_id': f'{support_case}-{regime}-{variant}',
                    'design_id': f'{regime}-{variant}',
                    'support_case': support_case,
                    'seasonal_availability_profile': {'regime_id': regime},
                })

    compact = compact_pareto_scenario_catalog(candidates, max_points=16)

    assert len(compact) == 16
    assert {row['sample_id'] for row in compact} <= {row['sample_id'] for row in candidates}
    assert {row['support_case'] for row in compact} == set(support_cases)
    assert {row['seasonal_availability_profile']['regime_id'] for row in compact} == set(regimes)
    assert len({row['sample_id'] for row in compact}) == len(compact)
    assert len({row['design_id'] for row in compact}) == 16, 'Keep one distinct physical design per available design before adding finance overlays.'


def test_compact_scenario_catalog_prioritizes_distinct_process_designs_over_finance_overlays():
    from Greenhub.pareto_reporting import compact_pareto_scenario_catalog

    support_cases = [f'C{grant}-GB{grass}' for grant in (0, 30, 45, 60) for grass in (0, 10, 20, 30, 40, 50)]
    candidates = [
        {'sample_id': f'design-{design:02d}-{support}', 'design_id': f'design-{design:02d}',
         'support_case': support, 'seasonal_availability_profile': {'regime_id': f'regime-{design % 4}'}}
        for design in range(50) for support in support_cases
    ]

    compact = compact_pareto_scenario_catalog(candidates, max_points=100)

    assert len(compact) == 100
    assert len({row['design_id'] for row in compact}) == 50
    assert {row['support_case'] for row in compact} >= set(support_cases)
    assert {row['sample_id'] for row in compact} <= {row['sample_id'] for row in candidates}


def test_saved_projection_restores_collection_delay_inventory_from_authoritative_monthly_result():
    from copy import deepcopy
    from scripts.compact_pareto_ui_catalog import compact_saved_projection
    from Greenhub.application.biomass_schedule import schedule_feed_rows
    from Greenhub.application.contracts import SimulationRequest
    from Greenhub.time_grid import generate_time_grid

    simulation = {
        "schema_version": "1.0.0", "request_id": "test-delay-ledger", "project_id": "greenhub",
        "start_date": "2026-01-01", "end_date": "2026-12-31", "time_step": "monthly",
        "biomass_schedule": {
            "annual_available_biomass_tonnes": 20, "annual_processed_biomass_tonnes": 10,
            "processing_delay_days": 14, "collection_refinery_fraction": 1,
            "feed_basis": "tonnes_per_year", "feed_kg_per_hr": 1000,
            "season_start": "2026-06-01", "season_end": "2026-08-31",
            "peak_date": "2026-07-01", "spread_days": 20, "active_months": [6, 8],
            "monthly_availability_tonnes": [0, 0, 0, 0, 0, 10, 0, 10, 0, 0, 0, 0],
        },
    }
    request = SimulationRequest.from_dict(simulation)
    grid = generate_time_grid("2026-01-01", "2026-12-31", "monthly")
    ledger = schedule_feed_rows(
        request.biomass_schedule, grid,
        processing_delay_days=request.biomass_schedule.processing_delay_days,
    )
    configuration = {"simulation": simulation}
    months = [{
        "time_label": row["time"],
        "available_biomass_tonnes": row["available_wet_biomass_kg"] / 1000,
        "collected_at_harvest_tonnes": row["harvested_biomass_kg"] / 1000,
        "collected_for_processing_tonnes": row["collected_biomass_kg"] / 1000,
    } for row in ledger]
    fields = {
        "collection_delay_harvest_tonnes": "harvested_biomass_kg",
        "collection_delay_release_tonnes": "collected_biomass_kg",
        "collection_delay_inventory_entering_tonnes": "collection_delay_inventory_entering_kg",
        "collection_delay_inventory_remaining_tonnes": "collection_delay_inventory_remaining_kg",
        "collection_delay_inventory_peak_tonnes": "collection_delay_inventory_peak_kg",
        "collection_delay_inventory_mass_residual_tonnes": "collection_delay_inventory_residual_kg",
    }
    saved_sample = {
        "sample_id": "route-1-C0-GB0",
        "configuration": configuration,
        "annual": {"biomass_schedule": {"monthly": months}},
    }
    candidate = {
        "sample_id": saved_sample["sample_id"],
        "configuration": configuration,
        "support_case": "C0-GB0",
        "seasonal_availability_profile": {"regime_id": "two_cut_summer"},
    }
    source = {"groups_payload": {
        name: {
            "scenario_catalog": [deepcopy(candidate)],
            "selected_candidates": {
                "test": [deepcopy(candidate)],
                "test-duplicate": [deepcopy(candidate)],
            },
        }
        for name in ("protein_enabled", "protein_bypass")
    }}
    source_groups = {
        name: {"samples": [saved_sample]}
        for name in ("protein_enabled", "protein_bypass")
    }

    projection, _ = compact_saved_projection(source, source_groups)

    for group in projection["groups_payload"].values():
        catalog_row = group["scenario_catalog"][0]
        selected_rows = [
            row
            for rows in group["selected_candidates"].values()
            for row in rows
        ]
        for projected_row, selected_month in zip(catalog_row["seasonal_feed_profile"], ledger):
            for output_field, source_field in fields.items():
                expected = selected_month[source_field] / 1000
                assert projected_row[output_field] == expected
        assert len(selected_rows) == 2
        for selected_row in selected_rows:
            for projected_row, selected_month in zip(selected_row["seasonal_feed_profile"], ledger):
                for output_field, source_field in fields.items():
                    expected = selected_month[source_field] / 1000
                    assert projected_row[output_field] == expected


def test_pareto_loader_reassembles_bounded_sample_shards(tmp_path):
    import json

    (tmp_path / 'latest.json').write_text(json.dumps({'groups_payload': {'protein_enabled': {}}}), encoding='utf-8')
    (tmp_path / 'protein_enabled_batch.json').write_text(json.dumps({
        'group': 'protein_enabled', 'sample_shards': ['protein_enabled_samples_001.json', 'protein_enabled_samples_002.json'],
    }), encoding='utf-8')
    for filename, sample_id in (('protein_enabled_samples_001.json', 'A'), ('protein_enabled_samples_002.json', 'B')):
        (tmp_path / filename).write_text(json.dumps({'samples': [{'sample_id': sample_id}]}), encoding='utf-8')

    loaded = load_pareto_results(tmp_path)

    assert [row['sample_id'] for row in loaded['groups_payload']['protein_enabled']['samples']] == ['A', 'B']


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


def test_published_pareto_has_200_positive_high_throughput_scenarios():
    import json
    from pathlib import Path

    root = Path(__file__).resolve().parents[1]
    payload = json.loads((root / 'Greenhub/results/pareto_positive_200_2026/latest_ui.json').read_text(encoding='utf-8'))
    assert payload['product_eligibility']['checked_products']
    all_candidates = []
    for group in ('protein_enabled', 'protein_bypass'):
        data = payload['groups_payload'][group]
        assert len(data['fronts']['by_support_case']) == 24
        assert len(data['scenario_catalog']) == 100
        assert all(row.get('configuration', {}).get('simulation', {}).get('biomass_schedule')
                   for row in data['scenario_catalog'])
        assert all(row['product_gate']['eligible'] for row in data['scenario_catalog'])
        all_candidates.extend(data['scenario_catalog'])
    assert len({row['sample_id'] for row in all_candidates}) == 200
    assert all(row['values']['npv'] > 0 and row['actual_feed_processed_tonnes'] > 14_000
               for row in all_candidates)
    assert sum(18_000 <= row['actual_feed_processed_tonnes'] <= 25_000
               for row in all_candidates) == 150
    assert sum(row['supply_cohort'] == 'hypothetical_import' for row in all_candidates) == 15


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
    assert float(rows['eligible-1']['original_operating_profit_eur_per_year']) == pytest.approx(6)
