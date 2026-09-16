"""Calendar transformations, schedule caps and the frontend-facing reporting contract."""
import json

import pytest

from Greenhub.application.dynamic_complete_scenario import DynamicCompleteScenario, build_biomass_schedule
from Greenhub.application.biomass_schedule import build_empirical_biomass_schedule
from Greenhub.application.contracts import BiomassSchedule
from Greenhub.application.dynamic_complete_reporting_service import (
    METRIC_KINDS, aggregate_rates, build_scenario_summary, default_summary, summarize_biosteam_grid,
)
from Greenhub.dynamic_complete_proxy import DynamicCompleteProxyConfig, run_dynamic_complete_proxy_scenario_step
from Greenhub.dynamic_downstream_biosteam import run_dynamic_complete_biosteam_grid
from Greenhub.dynamic_economic_environmental import analyze_dynamic_complete_report
from Greenhub.time_grid import generate_time_grid


@pytest.fixture(scope="module")
def baseline():
    return default_summary()


def test_calendar_and_energy_conversions_with_leap_month_and_partial_month():
    rows = [{"time_label": s.label, "operating_hours": s.duration_hours,
             "rates": {"feed_processed": 1000, "electricity_demand": 100, "heat_demand": 100, "biomethane": 10}}
            for s in generate_time_grid("2024-02-15", "2024-03-31")]
    report = aggregate_rates(rows, year=2024, annualize=True)
    assert report["monthly"][0]["metrics"]["feed_processed"]["tonnes_per_month"] == 15 * 24
    assert report["monthly"][1]["metrics"]["feed_processed"]["tonnes_per_month"] == 31 * 24
    assert report["annual_summary"]["feed_processed"]["tonnes_per_year"] == 46 * 24
    assert report["annual_summary"]["electricity_demand"]["MWh_per_year"] == pytest.approx(46 * 24 * .1)
    assert report["annual_summary"]["heat_demand"]["GJ_per_year"] == pytest.approx(46 * 24 * .1)
    assert report["annual_summary"]["biomethane"]["m3_per_year"] == 46 * 24 * 10
    assert report["annualized_estimate"]["feed_processed"]["tonnes_per_year"] == 366 * 24


def test_default_schedule_integrates_30000_and_partial_months():
    schedule = build_biomass_schedule(DynamicCompleteScenario())
    assert schedule["annual_processed_tonnes"] == pytest.approx(30000)
    assert schedule["annual_available_tonnes"] == pytest.approx(30000)
    assert schedule["annual_unused_tonnes"] == pytest.approx(0)
    assert schedule["monthly"][3]["operating_hours"] == 16 * 24
    assert schedule["monthly"][10]["operating_hours"] == 15 * 24
    assert schedule["monthly"][0]["processed_biomass_tonnes"] == 0


def test_reduced_target_caps_curve_instead_of_rescaling_it():
    full = build_biomass_schedule(DynamicCompleteScenario())
    capped = build_biomass_schedule(DynamicCompleteScenario(annual_processed_biomass_tonnes=15000))
    assert capped["annual_processed_tonnes"] == pytest.approx(15000)
    assert capped["annual_available_tonnes"] == pytest.approx(30000)
    assert capped["annual_unused_tonnes"] == pytest.approx(15000)
    midsummer = [capped["monthly"][i]["processed_biomass_tonnes"] for i in (5, 6, 7)]
    assert midsummer == pytest.approx([midsummer[0]] * 3)
    assert capped["monthly"][3]["processed_biomass_tonnes"] == pytest.approx(full["monthly"][3]["processed_biomass_tonnes"])
    fractional = build_biomass_schedule(DynamicCompleteScenario(collection_refinery_fraction=.5))
    assert fractional["annual_processed_tonnes"] == pytest.approx(15000)


def test_empirical_annual_schedule_uses_the_same_distribution_and_cap_policy():
    dynamic = build_biomass_schedule(DynamicCompleteScenario())
    empirical = build_empirical_biomass_schedule(BiomassSchedule())
    assert empirical["annual_available_tonnes"] == pytest.approx(30000)
    assert empirical["annual_processed_tonnes"] == pytest.approx(30000)
    assert [row["available_biomass_tonnes"] for row in empirical["monthly"]] == pytest.approx(
        [row["available_biomass_tonnes"] for row in dynamic["monthly"]]
    )
    capped = build_empirical_biomass_schedule(
        BiomassSchedule(annual_processed_biomass_tonnes=15000)
    )
    midsummer = [capped["monthly"][index]["processed_biomass_tonnes"] for index in (5, 6, 7)]
    assert midsummer == pytest.approx([midsummer[0]] * 3)
    assert capped["annual_unused_tonnes"] == pytest.approx(15000)
    assert empirical["policy_id"] == "shared_normal_supply_monthly_cap_v1"


def test_active_months_and_hourly_capacity_do_not_rescale_availability():
    config = DynamicCompleteScenario(active_months=(5,), feed_basis="kg_per_hr", feed_kg_per_hr=1000)
    schedule = build_biomass_schedule(config)
    assert schedule["annual_processed_tonnes"] == pytest.approx(31 * 24)
    assert schedule["annual_available_tonnes"] == pytest.approx(30000)
    assert schedule["unmet_target_tonnes"] > 0
    assert sum(row["processed_biomass_tonnes"] for row in schedule["monthly"] if row["time_label"] != "2026-05") == 0


@pytest.mark.parametrize("changes", [
    {"protein_method": ["isoelectric", "membrane"]}, {"gas_route": ["mea", "psa"]},
    {"protein_method": "heat"}, {"protein_method": "generic"}, {"protein_recovery_fraction": 1.1},
    {"include_press_cake_in_ad": True}, {"target_product_moisture": 1}, {"spread_days": 0},
    {"collection_refinery_fraction": -1}, {"annual_processed_biomass_tonnes": float("nan")},
    {"active_months": [13]}, {"active_months": [5, 5]}, {"resource_recovery_methods": ["bad"]},
    {"allow_assumptions": "false"}, {"season_end": "2025-01-01"}, {"unknown_option": 1},
])
def test_clear_scenario_validation(changes):
    with pytest.raises(ValueError):
        DynamicCompleteScenario.from_dict(changes)


def test_monthly_downstream_scaling_uses_schedule(baseline):
    may = baseline["monthly"][4]
    reference = run_dynamic_complete_proxy_scenario_step(DynamicCompleteProxyConfig(drying_method="spray_drying_proxy"), "2026-05")
    processed = may["processed_biomass_tonnes"]
    assert may["metrics"]["dried_protein_product"]["tonnes_per_month"] == pytest.approx(reference.product_outputs["dried_protein_product_kg_hr"] / 1000 * processed)
    assert may["metrics"]["biomethane"]["m3_per_month"] == pytest.approx(reference.product_outputs["biomethane_m3_hr"] * processed)
    assert may["metrics"]["electricity_demand"]["MWh_per_month"] > 0
    assert baseline["annual_summary"]["feed_processed"]["tonnes_per_year"] == pytest.approx(30000)
    assert all(check["parity_passed"] and check["empirical_flowsheet_unchanged"] and check["press_cake_boundary_valid"] for check in baseline["biosteam_checks"])


def test_frontend_visible_data_contract_and_traceability(baseline):
    json.dumps(baseline, allow_nan=False)
    assert baseline["readiness"]["validated_simulation_ready"] is False
    assert baseline["readiness"]["can_drive_complete_biosteam_proxy"] is True
    assert set(baseline["annual_summary"]) == set(METRIC_KINDS)
    assert all({"available_biomass_tonnes", "processed_biomass_tonnes", "unused_biomass_tonnes", "utilization_fraction"} <= row.keys() for row in baseline["biomass_schedule"]["monthly"])
    assert all({"policy_id", "value", "unit", "source_status", "certainty_class", "source_file", "source_id", "warning"} <= r.keys() for r in baseline["assumptions"])
    assert {"direct_dataset", "greenhub_legacy_proxy_result", "engineering_assumption"} <= baseline["assumption_counts"].keys()
    assert any(r["policy_id"] == "engineering_proxy_closure_v1" for r in baseline["assumptions"])
    assert not any(str(r["source_file"]).startswith(("C:", "/")) for r in baseline["assumptions"])


def test_strict_withholds_scaffold_production_and_analysis():
    report = build_scenario_summary({"active_months": [5], "allow_assumptions": False})
    assert report["blockers_count"] > 0
    assert not report["readiness"]["can_drive_complete_biosteam_proxy"]
    assert report["annual_summary"]["dried_protein_product"]["tonnes_per_year"] is None
    assert not report["analysis"]["proxy_analysis_ready"]
    assert report["analysis"]["economic"] is None


def test_heat_honors_explicit_recovery_and_mass_only_omits_utilities():
    low = build_scenario_summary({"active_months": [5], "protein_method": "heat", "protein_recovery_fraction": .1, "drying_method": "mass_only"})
    high = build_scenario_summary({"active_months": [5], "protein_method": "heat", "protein_recovery_fraction": .5})
    assert high["annual_summary"]["recovered_protein"]["tonnes_per_year"] > low["annual_summary"]["recovered_protein"]["tonnes_per_year"]
    assert low["annual_summary"]["drying_electricity"]["MWh_per_year"] == 0
    assert any("Mass-only" in w for w in low["warning_counts"])


def test_chp_and_unselected_recovery_residual():
    report = build_scenario_summary({"active_months": [5], "gas_route": "chp_utilities", "resource_recovery_methods": []})
    annual = report["annual_summary"]
    assert annual["biomethane"]["m3_per_year"] == 0
    assert annual["chp_electricity_output"]["MWh_per_year"] > 0
    assert annual["chp_heat_output"]["GJ_per_year"] > 0
    assert annual["final_residual_liquor"] == annual["digestate"]


def test_analysis_arithmetic_metadata_and_zero_denominators(baseline):
    analysis = analyze_dynamic_complete_report(baseline, {"electricity_price": 1})
    assert analysis["proxy_analysis_ready"]
    assert analysis["economic"]["costs_eur_per_year"]["electricity"] == pytest.approx(baseline["annual_summary"]["electricity_demand"]["MWh_per_year"] * 1000)
    assert sum(analysis["environmental"]["contributions_kg_co2e_per_year"].values()) == pytest.approx(analysis["environmental"]["net_kg_co2e_per_year"])
    assert all(r["source_status"] in {"user_input", "engineering_assumption"} and r["warning"] for r in analysis["assumptions"])
    empty = build_scenario_summary({"annual_processed_biomass_tonnes": 0})
    assert empty["analysis"]["economic"]["cost_eur_per_tonne_feed"] is None
    json.dumps(empty, allow_nan=False)
    with pytest.raises(ValueError):
        analyze_dynamic_complete_report(baseline, {"methane_gwp": float("inf")})


def test_existing_may_november_grid_is_not_silently_full_year():
    grid = run_dynamic_complete_biosteam_grid()
    report = summarize_biosteam_grid(grid, annualize=True)
    assert len(report["monthly"]) == 7
    assert report["annual_summary"]["feed_processed"]["tonnes_per_year"] == 214 * 24
    assert report["annualized_estimate"]["feed_processed"]["tonnes_per_year"] == 365 * 24
