"""Focused inventory completeness, accounting separation and unit regressions."""
from copy import deepcopy
from dataclasses import replace
import json
from types import SimpleNamespace as NS

import pytest

from Greenhub.application.lca_service import calculate_empirical_lca, calculate_lca_inventory, logistics_to_lca_inventory, screening_lca_factors
from Greenhub.lca_inventory import GROUPS, LCAProjectBasis, load_climate_factors


def basis(*groups, **values):
    return LCAProjectBasis(
        boundary="Explicit synthetic test boundary, not a whole biorefinery LCA",
        included_groups=groups,
        exclusions={g: "Outside synthetic test boundary" for g in GROUPS if g not in groups},
        inventory_completeness={g: {"status": "complete", "note": "Explicit synthetic test inventory"} for g in groups},
        **values,
    )


def flow(name="methane", **values):
    return dict(flow_id=name, group="process_emissions", quantity=2, unit="kg",
                factor_id="biogenic_methane", accounting_key=name,
                source_id="synthetic-test", **values)


def simulation(*, utilities=(), seasonal_summary=None, storage=(), streams=()):
    return NS(status="completed", run_id="test", seasonal_summary=seasonal_summary,
              utilities=utilities, storage_inventory_series=storage, streams=streams,
              product_series=())


def utility(kind, value, unit):
    return NS(kind=kind, demand=NS(value=value, unit=unit))


def test_all_missing_is_null_and_known_contribution_survives():
    missing={**flow(), "quantity": None}
    report=calculate_lca_inventory([missing], basis("process_emissions")).to_dict()
    assert report["totals"]["partial_climate_kg_co2e_per_year"] is None
    assert report["totals"]["climate_kg_co2e_per_year"] is None
    partial=calculate_lca_inventory([missing, flow("known")], basis("process_emissions")).to_dict()
    assert partial["totals"]["partial_climate_kg_co2e_per_year"] == 54
    assert not partial["readiness"]["climate_objective_eligible"]


def test_unknown_credit_does_not_erase_attributional_total():
    credit={**flow("credit"), "factor_id": "missing_counterfactual", "direction": "credit",
            "quality_verified": True, "counterfactual": "Synthetic displaced service", "available_quantity": 2}
    report=calculate_lca_inventory([flow(), credit], basis("process_emissions", substitution_enabled=True)).to_dict()
    assert report["totals"]["climate_kg_co2e_per_year"] == 54
    assert report["totals"]["substitution_net_kg_co2e_per_year"] is None
    assert report["totals"]["substitution_credit_kg_co2e_per_year"] is None
    assert report["substitution_missing_inputs"]
    assert report["readiness"]["climate_objective_eligible"]
    assert not report["readiness"]["substitution_objective_eligible"]


def test_memorandum_alone_cannot_assert_zero_impact():
    memo={**flow("biogenic_co2"), "factor_id": None, "direction": "memorandum"}
    report=calculate_lca_inventory([memo], basis("process_emissions")).to_dict()
    assert report["totals"]["climate_kg_co2e_per_year"] is None
    assert report["inventory"][0]["quantity"] == 2
    zero={**flow("explicit_no_other_emissions"), "quantity": 0, "factor_id": None}
    report=calculate_lca_inventory([memo, zero], basis("process_emissions")).to_dict()
    assert report["totals"]["climate_kg_co2e_per_year"] == 0


def test_static_missing_utility_propagates_instead_of_becoming_zero():
    result=simulation(utilities=[utility("electricity", 4, "kW"), utility("electricity", None, "kW")])
    report=calculate_empirical_lca(result, basis("electricity", operating_hours_per_year=100)).to_dict()
    assert report["inventory"][0]["quantity"] is None
    assert "missing_quantity" in report["missing_inputs"][0]
    empty=calculate_empirical_lca(simulation(), basis("electricity", operating_hours_per_year=100)).to_dict()
    assert empty["inventory"][0]["quantity"] is None


def test_static_heat_kj_per_hour_to_kwh_no_generation_credit():
    result=simulation(utilities=[utility("electricity", 5, "kW"), utility("electricity", -3, "kW"),
                                 utility("heat", 3600, "kJ/hr"), utility("heat", -7200, "kJ/hr")])
    before=deepcopy(result)
    report=calculate_empirical_lca(result, basis("electricity", "heat", operating_hours_per_year=100)).to_dict()
    quantities={row["flow_id"]: row["quantity"] for row in report["inventory"]}
    assert quantities == {"electricity": 500, "heat": 100}
    assert result == before
    assert report["totals"]["climate_kg_co2e_per_year"] is None
    result.utilities[0].demand.unit="MW"
    with pytest.raises(ValueError, match="electricity demand"):
        calculate_empirical_lca(result, basis("electricity", operating_hours_per_year=100))


def test_seasonal_totals_are_not_multiplied_by_operating_hours_again():
    result=simulation(seasonal_summary={"total_utilities": {"electricity_kwh": 30, "heating_kwh": 50}})
    report=calculate_empirical_lca(result, basis("electricity", "heat", operating_hours_per_year=100)).to_dict()
    assert [row["quantity"] for row in report["inventory"]] == [30, 50]


def test_zero_storage_ledger_is_explicit_but_partial_reaction_subset_blocks():
    result=simulation(storage=[{"time": "steady", "incoming_residence": {"emissions_kg": {}, "blockers": []}}])
    report=calculate_empirical_lca(result, basis("storage_emissions", operating_hours_per_year=100)).to_dict()
    assert report["totals"]["climate_kg_co2e_per_year"] == 0
    result.storage_inventory_series[0]["incoming_residence"]={
        "emissions_kg": {"Methane": 1, "CarbonDioxide": 10}, "emissions_inventory_complete": False, "blockers": []}
    report=calculate_empirical_lca(result, basis("storage_emissions", operating_hours_per_year=100)).to_dict()
    assert report["totals"]["partial_climate_kg_co2e_per_year"] == 2700
    assert report["totals"]["climate_kg_co2e_per_year"] is None
    assert any("unresolved_pathways" in issue for issue in report["missing_inputs"])


def test_terminal_gas_fate_required_and_missing_species_not_dropped():
    stream=NS(sink_unit=None, aliases=("reject_gas",), components={"Methane": NS(value=2), "CarbonDioxide": NS(value=3)})
    result=simulation(streams=[stream])
    unresolved=calculate_empirical_lca(result, basis("process_emissions", operating_hours_per_year=100)).to_dict()
    assert unresolved["totals"]["climate_kg_co2e_per_year"] is None
    emitted=calculate_empirical_lca(result, basis("process_emissions", operating_hours_per_year=100, terminal_gas_fate="emitted")).to_dict()
    assert emitted["totals"]["climate_kg_co2e_per_year"] == 5400
    result.streams[0].components["Methane"].value=None
    missing=calculate_empirical_lca(result, basis("process_emissions", operating_hours_per_year=100, terminal_gas_fate="emitted")).to_dict()
    assert missing["totals"]["climate_kg_co2e_per_year"] is None


def test_units_metadata_duplicates_and_complete_functional_units():
    report=calculate_lca_inventory([flow()], basis("process_emissions", annual_throughput_kg=1000, annual_dry_feed_kg=200)).to_dict()
    assert report["totals"]["kg_co2e_per_tonne_wet_feed"] == 54
    assert report["totals"]["kg_co2e_per_tonne_dry_feed"] == 270
    assert report["readiness"]["validated_lca_ready"] is False
    json.dumps(report, allow_nan=False)
    with pytest.raises(ValueError, match="Duplicate"):
        calculate_lca_inventory([flow(), flow()], basis("process_emissions"))
    with pytest.raises(ValueError, match="units"):
        calculate_lca_inventory([{**flow(), "unit": "tonne"}], basis("process_emissions"))
    with pytest.raises(ValueError, match="metadata"):
        load_climate_factors({"electricity": 0.4})


def test_supplied_utility_factor_is_separate_and_traceable():
    factor=replace(load_climate_factors()["electricity"], value=0.2, source_status="engineering_assumption",
                   evidence_class="engineering_assumption", applicability="Synthetic test only",
                   warning="Not a measured electricity footprint")
    result=simulation(utilities=[utility("electricity", 5, "kW")])
    report=calculate_empirical_lca(result, basis("electricity", operating_hours_per_year=100), factors={"electricity": factor}).to_dict()
    assert report["totals"]["climate_kg_co2e_per_year"] == 100
    assert next(f for f in report["factors"] if f["factor_id"]=="electricity")["source_status"] == "engineering_assumption"


def test_screening_electricity_factor_is_explicitly_traceable_and_opt_in():
    factor = screening_lca_factors()["electricity"]
    assert factor.value == pytest.approx(0.20)
    assert factor.source_status == "proxy_factor"
    assert factor.reference_year == 2024
    assert factor.source_url


def test_screening_factor_is_available_from_application_package():
    from Greenhub.application import screening_lca_factors as exported
    assert exported()["electricity"].factor_id == "electricity"


def test_logistics_connects_to_lca_using_its_explicit_fuel_emission_factor():
    rows = logistics_to_lca_inventory({"emissions_kg_co2": 12.5, "limitations": []})
    assert rows[0]["group"] == "transport"
    assert rows[0]["quantity"] == pytest.approx(12.5)
    report = calculate_lca_inventory(rows, basis("transport")).to_dict()
    assert report["totals"]["climate_kg_co2e_per_year"] == pytest.approx(12.5)
    assert report["inventory"][0]["factor_id"] == "fossil_co2"


def test_pretreatment_water_inventory_uses_existing_materials_group():
    from Greenhub.pretreatment_state import apply_screening_pretreatment_state

    state = apply_screening_pretreatment_state(
        {"Water": 100.0, "SolubleProtein": 10.0},
        water_addition_kg_per_kg_wet_feed=0.5,
    )
    rows = state.to_lca_inventory(annualization_factor=10.0)
    report = calculate_lca_inventory(rows, basis("materials")).to_dict()
    water = next(item for item in report["inventory"] if item["flow_id"] == "pretreatment_added_water")
    assert water["quantity"] == pytest.approx(550.0)
    assert water["status"] == "missing_factor"
