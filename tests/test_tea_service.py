"""Focused tests for post-route TEA selection, scaling, and isolation."""

import json
from dataclasses import replace

import pytest

from Greenhub.application.contracts import SCHEMA_VERSION, ScenarioSelection, SimulationRequest
from Greenhub.application.simulation_service import SimulationService
from Greenhub.application.dynamic_complete_reporting_service import build_scenario_summary
from Greenhub.application.tea_service import (
    TEAFinancialAssumptions,
    TEAProjectBasis,
    calculate_dynamic_tea,
    calculate_empirical_tea,
)
from Greenhub.tea_reporting import (
    build_tea_scenario_kpi_table,
    evaluate_tea_scenario_cases,
    sample_valid_dynamic_scenarios,
    sample_valid_empirical_scenarios,
    write_tea_scenario_kpi_reports,
)
from Greenhub.parameters import CalculationMode, ResolutionMode
from Greenhub.tea_costs import TEACostRecord, load_tea_cost_register


@pytest.fixture(scope="module")
def empirical_result(tmp_path_factory):
    request = SimulationRequest(
        SCHEMA_VERSION,
        "tea-empirical",
        "greenhub-tea-test",
        calculation_mode=CalculationMode.STRUCTURAL,
        resolution_mode=ResolutionMode.STEADY_STATE,
        scenarios=ScenarioSelection(
            feed_preparation="F2",
            protein_recovery="PR1",
            anaerobic_digestion="AD1",
            biogas_upgrading="BG2",
            nutrient_recovery="NR2",
            process_order="A",
        ),
    )
    service = SimulationService(run_root=tmp_path_factory.mktemp("tea-run"))
    return service.execute_run(service.create_run(request))


@pytest.fixture(scope="module")
def dynamic_result():
    return build_scenario_summary({"active_months": [5]})


def _record(
    cost_id: str,
    tags: tuple[str, ...],
    *,
    alternative_group: str | None = None,
    capacity: float | None = 10.0,
    capacity_unit: str = "m3/h",
    reference_value: float | None = 100_000.0,
    exponent: float | None = 0.6,
    installed_factor: float | None = 1.0,
    package_group: str | None = None,
    package_role: str | None = None,
) -> TEACostRecord:
    return TEACostRecord(
        cost_id=cost_id,
        process_area="test",
        process_step="Test step",
        equipment_or_cost_item=f"Test item {cost_id}",
        item_category="equipment",
        scenario_or_route_tags=tags,
        alternative_group=alternative_group,
        can_sum_by_default=True,
        cost_type="capex",
        reference_value_eur=reference_value,
        reference_unit="EUR/unit",
        reference_capacity=capacity,
        capacity_unit=capacity_unit,
        scaling_exponent=exponent,
        installed_factor=installed_factor,
        annual_unit_cost_eur=None,
        lifetime_years=None,
        replacement_frequency=None,
        source_title="Test source",
        source_url="https://example.test/source",
        confidence="test",
        notes="Synthetic test record.",
        package_group=package_group,
        package_role=package_role,
    )


def _financial_records():
    capex = _record("TEST-FIN-CAPEX", ("BG2",), capacity_unit="m3/h")
    electricity = replace(
        _record("TEST-FIN-ELECTRICITY", ("BG2",)),
        process_step="Electricity",
        equipment_or_cost_item="Purchased electricity",
        item_category="utility",
        cost_type="utility",
        reference_value_eur=None,
        reference_unit="EUR/kWh",
        reference_capacity=None,
        capacity_unit=None,
        scaling_exponent=None,
        installed_factor=None,
        annual_unit_cost_eur=0.20,
    )
    return capex, electricity


def test_explicit_logistics_result_supplies_annual_logistics_cost(empirical_result):
    logistics = replace(
        _record("TEST-LOGISTICS", ("F2",)),
        process_area="logistics",
        process_step="Feedstock transport",
        equipment_or_cost_item="Feedstock transport result",
        item_category="logistics",
        cost_type="logistics",
        reference_value_eur=None,
        reference_unit=None,
        reference_capacity=None,
        capacity_unit=None,
        scaling_exponent=None,
        installed_factor=None,
    )
    report = calculate_empirical_tea(
        empirical_result,
        cost_records=(logistics,),
        logistics_result={"transport_cost_currency": 1234.5, "limitations": []},
    ).to_dict()
    line = report["opex_lines"][0]
    assert line["annual_cost_eur"] == pytest.approx(1234.5)
    assert line["calculation_status"] == "calculated_from_logistics_result"


def _financial_assumptions():
    return TEAFinancialAssumptions(
        project_lifetime_years=12,
        discount_rate=0.08,
        tax_rate=0.0,
        depreciation_method="none",
        product_prices={
            "dry_protein_product": {
                "value": 100.0,
                "unit": "EUR/kg",
                "source_status": "user_input",
                "source_title": "Synthetic test assumption",
                "notes": "Test-only explicit price.",
            }
        },
        revenue_product_ids=("dry_protein_product",),
        non_sale_product_reasons={
            name: "Synthetic test boundary: no sale of this coproduct; not a plant market assumption."
            for name in ("press_cake", "biomethane", "phosphorus_product", "ammonium_product", "potassium_concentrate", "recovered_water", "nutrient_rich_solids", "ion_exchange_product")
        },
    )


def test_compact_register_is_normalized_and_traceable():
    records = load_tea_cost_register()
    assert len(records) == 55
    assert len({item.cost_id for item in records}) == len(records)
    assert {"TEA-017-PSA", "TEA-017-WATER_SCRUBBING", "TEA-017-MEMBRANE_UPGRADING"} <= {
        item.cost_id for item in records
    }
    assert all(item.source_title and item.source_url for item in records)


def test_empirical_result_is_unchanged_and_tea_requires_completed_result(empirical_result):
    before = empirical_result.to_dict()
    report = calculate_empirical_tea(
        empirical_result,
        project_basis=TEAProjectBasis(operating_hours_per_year=1000.0),
    )
    assert empirical_result.to_dict() == before
    assert report.route_summary["tea_calculation_order"] == "formed_route_then_post_simulation_tea"
    assert report.route_summary["process_calculations_modified"] is False
    json.dumps(report.to_dict(), allow_nan=False)
    with pytest.raises(TypeError, match="completed SimulationResult"):
        calculate_empirical_tea(None)


def test_scaled_capex_uses_explicit_capacity_and_exact_formula(empirical_result):
    record = _record("TEST-SCALE", ("BG2",))
    report = calculate_empirical_tea(
        empirical_result,
        project_basis=TEAProjectBasis(
            capacities={"TEST-SCALE": {"value": 20.0, "unit": "m3/h"}},
        ),
        cost_records=(record,),
    )
    line = report.capex_lines[0]
    expected = 100_000.0 * (20.0 / 10.0) ** 0.6
    assert line["direct_cost_eur"] == pytest.approx(expected)
    assert line["installed_cost_eur"] == pytest.approx(expected)


def test_missing_capacity_blocks_scaled_capex_without_invention(empirical_result):
    record = _record("TEST-MISSING", ("BG2",), capacity_unit="membrane area m2")
    report = calculate_empirical_tea(empirical_result, cost_records=(record,))
    assert report.capex_lines[0]["direct_cost_eur"] is None
    assert any(item["cost_id"] == "TEST-MISSING" and item["code"] == "missing_capacity" for item in report.missing_inputs)


def test_unselected_route_alternatives_are_excluded(empirical_result):
    water = _record("TEST-WATER", ("BG2",), alternative_group="upgrader")
    membrane = _record("TEST-MEMBRANE", ("BG3",), alternative_group="upgrader")
    report = calculate_empirical_tea(empirical_result, cost_records=(water, membrane))
    assert [item["cost_id"] for item in report.selected_cost_lines] == ["TEST-WATER"]
    assert any(item["cost_id"] == "TEST-MEMBRANE" and item["reason"] == "unselected_route_alternative" for item in report.excluded_alternatives)


def test_package_and_included_subcomponent_are_not_double_counted(empirical_result):
    package = _record(
        "TEST-PACKAGE", ("BG2",), package_group="test_package", package_role="package"
    )
    component = _record(
        "TEST-COMPONENT", ("BG2",), package_group="test_package", package_role="subcomponent"
    )
    report = calculate_empirical_tea(empirical_result, cost_records=(package, component))
    assert [item["cost_id"] for item in report.selected_cost_lines] == ["TEST-PACKAGE"]
    assert any(
        item["cost_id"] == "TEST-COMPONENT" and item["reason"].startswith("included_in_selected_package")
        for item in report.excluded_alternatives
    )


def test_dynamic_tea_uses_annual_outputs_without_interpolation():
    dynamic_report = {
        "scenario": {
            "scenario_id": "dynamic-tea-test",
            "protein_method": "isoelectric",
            "drying_method": "mass_only",
            "ad_method": "bmp_material_conversion_proxy",
            "gas_route": "water_scrubbing",
            "resource_recovery_methods": [],
        },
        "annual_summary": {
            "feed_processed": {"tonnes_per_year": 100.0},
            "electricity_demand": {"MWh_per_year": 2.0},
            "heat_demand": {"GJ_per_year": 3.6},
            "dried_protein_product": {"tonnes_per_year": 1.0},
        },
        "biomass_schedule": {
            "peak_throughput_kg_per_hr": 1000.0,
            "monthly": [{"operating_hours": 100.0}],
        },
        "monthly": [],
    }
    report = calculate_dynamic_tea(dynamic_report)
    electricity = next(item for item in report.opex_lines if item["cost_id"] == "TEA-036")
    assert electricity["quantity"] == pytest.approx(2000.0)
    assert electricity["annual_cost_eur"] == pytest.approx(2000.0 * 0.1991)
    assert report.route_summary["annual_throughput_kg"] == pytest.approx(100_000.0)
    assert any(item["code"] == "missing_dynamic_quantity" for item in report.missing_inputs)


def test_dynamic_reporting_contract_selects_only_formed_upgrader(dynamic_result):
    report = calculate_dynamic_tea(dynamic_result)
    selected = {item["cost_id"] for item in report.selected_cost_lines}
    assert "TEA-017-WATER_SCRUBBING" in selected
    assert "TEA-017-PSA" not in selected
    assert "TEA-017-MEMBRANE_UPGRADING" not in selected
    expected = dynamic_result["annual_summary"]["feed_processed"]["tonnes_per_year"] * 1000.0
    assert report.route_summary["annual_throughput_kg"] == pytest.approx(expected)
    assert report.route_summary["model_type"] == "dynamic"


def test_report_contains_selected_source_traceability(empirical_result):
    report = calculate_empirical_tea(empirical_result)
    selected = {item["cost_id"] for item in report.selected_cost_lines}
    traced = {item["cost_id"] for item in report.source_traceability}
    assert selected == traced
    assert all(item["source_title"] and item["source_url"] for item in report.source_traceability)


def test_empirical_screening_financial_kpis_calculate_from_explicit_assumptions(empirical_result):
    report = calculate_empirical_tea(
        empirical_result,
        project_basis=TEAProjectBasis(
            cost_boundary_complete=True, price_basis_confirmed=True, price_year=2026,
            notes='Synthetic complete test boundary and common price basis, not a real plant.',
            operating_hours_per_year=1000.0,
            capacities={"TEST-FIN-CAPEX": {"value": 10.0, "unit": "m3/h"}},
        ),
        cost_records=_financial_records(),
        financial_assumptions=_financial_assumptions(),
    )
    assert report.totals["revenue_status"] == "complete"
    assert report.financial_kpis["financial_kpi_status"] == "calculated_screening"
    assert report.financial_kpis["npv_eur"] is not None
    assert report.financial_kpis["irr"] is not None
    assert report.financial_kpis["simple_payback_years"] is not None
    assert report.financial_kpis["cost_per_tonne_wet_feed_eur"] is not None
    assert report.financial_kpis["cost_per_kg_protein_product_eur"] is not None
    assert any(
        item["cost_id"] == "PRODUCT-PRICE-DRY_PROTEIN_PRODUCT"
        and item["source_status"] == "user_input"
        for item in report.source_traceability
    )


def test_dynamic_screening_financial_kpis_use_summed_annual_outputs():
    dynamic_report = {
        "scenario": {
            "scenario_id": "dynamic-finance",
            "protein_method": "isoelectric",
            "drying_method": "mass_only",
            "ad_method": "bmp_material_conversion_proxy",
            "gas_route": "water_scrubbing",
            "resource_recovery_methods": [],
        },
        "annual_summary": {
            "feed_processed": {"tonnes_per_year": 100.0},
            "electricity_demand": {"MWh_per_year": 2.0},
            "heat_demand": {"GJ_per_year": 3.6},
            "dried_protein_product": {"tonnes_per_year": 1.0},
            "biomethane": {"m3_per_year": 5000.0},
        },
        "biomass_schedule": {
            "peak_throughput_kg_per_hr": 1000.0,
            "monthly": [{"operating_hours": 100.0}],
        },
        "monthly": [],
    }
    report = calculate_dynamic_tea(
        dynamic_report,
        project_basis=TEAProjectBasis(
            cost_boundary_complete=True, price_basis_confirmed=True, price_year=2026,
            notes='Synthetic complete test boundary and common price basis, not a real plant.',
            capacities={"TEST-FIN-CAPEX": {"value": 10.0, "unit": "m3/h"}},
        ),
        cost_records=_financial_records(),
        financial_assumptions=_financial_assumptions(),
    )
    assert report.financial_kpis["financial_kpi_status"] == "calculated_screening"
    assert report.route_summary["annual_products_m3"]["biomethane"] == pytest.approx(5000.0)
    assert report.financial_kpis["npv_eur"] is not None
    assert report.financial_kpis["cost_per_nm3_biomethane_eur"] is None
    assert report.financial_kpis["cost_per_m3_biomethane_eur"] is not None


def test_missing_product_prices_keep_revenue_and_returns_incomplete(empirical_result):
    assumptions = replace(
        _financial_assumptions(),
        product_prices={},
    )
    report = calculate_empirical_tea(
        empirical_result,
        project_basis=TEAProjectBasis(
            operating_hours_per_year=1000.0,
            capacities={"TEST-FIN-CAPEX": {"value": 10.0, "unit": "m3/h"}},
        ),
        cost_records=_financial_records(),
        financial_assumptions=assumptions,
    )
    assert report.totals["annual_revenue_eur"] == 0.0
    assert report.totals["revenue_status"] == "incomplete"
    assert report.financial_kpis["npv_eur"] is None
    assert any(item["code"] == "missing_product_price" for item in report.missing_inputs)


def test_cash_flow_kpis_are_deterministic_for_fixed_assumptions(empirical_result):
    capex, electricity = _financial_records()
    records = (replace(capex, lifetime_years=4.0), electricity)
    kwargs = dict(
        project_basis=TEAProjectBasis(
            operating_hours_per_year=1000.0,
            capacities={"TEST-FIN-CAPEX": {"value": 10.0, "unit": "m3/h"}},
        ),
        cost_records=records,
        financial_assumptions=_financial_assumptions(),
    )
    first = calculate_empirical_tea(empirical_result, **kwargs)
    second = calculate_empirical_tea(empirical_result, **kwargs)
    assert first.financial_kpis == second.financial_kpis
    assert first.cash_flow == second.cash_flow
    assert [item["year"] for item in first.replacement_schedule] == [4, 8]


def test_reproducible_scenario_sampling_and_kpi_report_writer(
    empirical_result, dynamic_result, tmp_path
):
    assert sample_valid_empirical_scenarios(5, seed=17) == sample_valid_empirical_scenarios(5, seed=17)
    dynamic_a = sample_valid_dynamic_scenarios(5, seed=17)
    dynamic_b = sample_valid_dynamic_scenarios(5, seed=17)
    assert [item["config"].to_dict() for item in dynamic_a] == [
        item["config"].to_dict() for item in dynamic_b
    ]
    evaluated = evaluate_tea_scenario_cases(
        (
            {"scenario_label": "empirical_case", "simulation_type": "empirical"},
            {"scenario_label": "dynamic_case", "simulation_type": "dynamic"},
        ),
        empirical_runner=lambda case: empirical_result,
        dynamic_runner=lambda case: dynamic_result,
    )
    rows = build_tea_scenario_kpi_table(evaluated)
    assert len(rows) == 2
    assert tuple(rows[0]) == (
        "scenario_label", "simulation_type", "selected_routes", "annual_feed_tonnes",
        "total_installed_capex_eur", "partial_direct_capex_eur", "capex_status", "opex_status", "profit_status", "annual_opex_eur", "annual_revenue_eur",
        "annual_profit_eur", "npv_eur", "irr", "simple_payback_years",
        "discounted_payback_years", "cost_per_tonne_feed_eur", "revenue_status",
        "missing_input_count", "warning_count", "confidence_summary",
    )
    paths = write_tea_scenario_kpi_reports(rows, results_dir=tmp_path, docs_dir=tmp_path)
    assert all(path.exists() for path in paths.values())
    json.loads(paths["json"].read_text(encoding="utf-8"))
