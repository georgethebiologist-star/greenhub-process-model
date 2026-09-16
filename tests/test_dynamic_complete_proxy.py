from __future__ import annotations

import json
from pathlib import Path

import biosteam as bst
import pytest

from Greenhub.dynamic_complete_proxy import (
    DynamicCompleteProxyConfig,
    run_dynamic_complete_proxy_scenario_grid,
    run_dynamic_complete_proxy_scenario_step,
    summarize_dynamic_complete_proxy_grid,
    write_dynamic_complete_proxy_reports,
)
from Greenhub.feedstock_proxy import load_feedstock_proxies


@pytest.fixture(scope="module")
def complete_step():
    return run_dynamic_complete_proxy_scenario_step(
        DynamicCompleteProxyConfig(), "2026-05"
    )


@pytest.fixture(scope="module")
def complete_grid():
    return run_dynamic_complete_proxy_scenario_grid()


def test_complete_proxy_grid_closes_all_months_without_missing_blockers(complete_grid):
    assert complete_grid.time_labels == (
        "2026-05", "2026-06", "2026-07", "2026-08", "2026-09", "2026-10", "2026-11"
    )
    assert complete_grid.can_drive_complete_proxy_model_all_steps is True
    assert complete_grid.mass_balances_close_all_steps is True
    assert complete_grid.blocker_counts == {}
    assert all(step.can_drive_simulation is False for step in complete_grid.steps)
    assert all(step.validated_simulation_ready is False for step in complete_grid.steps)


def test_datasets_only_mode_preserves_blockers_instead_of_failing():
    result = run_dynamic_complete_proxy_scenario_step(
        DynamicCompleteProxyConfig(allow_assumptions=False), "2026-05"
    )
    assert result.can_drive_complete_proxy_model is False
    assert "digestate_N_P_K_S_speciation_missing" in result.blockers
    assert "protein_proxy_closure_disabled" in result.blockers
    assert result.balances["all_downstream_unit_balances_close"] is True


def test_press_cake_is_external_and_never_enters_ad(complete_step):
    assert complete_step.system_outputs["press_cake"].destination == "external_scope_output"
    assert complete_step.ad.metrics["press_cake_included"] is False
    assert complete_step.ad.input_mass_kg_hr == pytest.approx(
        complete_step.protein_result.ad.residual_feed_kg_hr
    )
    assert complete_step.ad.input_mass_kg_hr < complete_step.config.basis_feed_kg_per_hr


def test_exactly_one_protein_method_is_active(complete_step):
    assert complete_step.selected_alternatives["protein_method"] == "isoelectric"
    assert complete_step.protein_result.protein_run.selected_method == "isoelectric"
    with pytest.raises(ValueError):
        DynamicCompleteProxyConfig(protein_method="isoelectric+membrane")


def test_upgrading_alternatives_produce_distinct_traceable_outputs():
    membrane = run_dynamic_complete_proxy_scenario_step(
        DynamicCompleteProxyConfig(
            upgrading_method="membrane", resource_recovery_methods=()
        ),
        "2026-05",
    )
    psa = run_dynamic_complete_proxy_scenario_step(
        DynamicCompleteProxyConfig(
            upgrading_method="psa", resource_recovery_methods=()
        ),
        "2026-05",
    )
    assert membrane.gas_route.method == "membrane"
    assert psa.gas_route.method == "psa"
    assert membrane.gas_route.metrics["biomethane_m3_hr"] != pytest.approx(
        psa.gas_route.metrics["biomethane_m3_hr"]
    )
    assert membrane.gas_route.blockers == ()
    assert psa.gas_route.blockers == ()
    assert any(item.source_status == "direct_dataset" for item in membrane.gas_route.evidence)


def test_resource_recovery_sequence_produces_candidate_products(complete_step):
    expected = {
        "nutrient_rich_solids",
        "ammonium_product",
        "struvite_product",
        "potassium_concentrate",
        "recovered_water",
        "ammonium_ion_exchange_product",
        "final_residual_liquor",
    }
    assert expected <= set(complete_step.system_outputs)
    assert all(complete_step.system_outputs[name].mass_kg_hr >= 0.0 for name in expected)
    assert len(complete_step.resource_recovery) == 5


def test_ad_and_resource_mass_balances_close(complete_step):
    units = (
        complete_step.drying,
        complete_step.ad,
        complete_step.gas_route,
        *complete_step.resource_recovery,
    )
    assert all(unit.identity_closes for unit in units)
    assert max(abs(unit.residual_kg_hr) for unit in units) <= 1e-8
    assert complete_step.ad.output_mass_kg_hr == pytest.approx(
        complete_step.ad.input_mass_kg_hr
    )


def test_every_closure_value_is_typed_and_warned(complete_step):
    statuses = {
        "direct_dataset",
        "greenhub_legacy_proxy_result",
        "literature_proxy",
        "engineering_assumption",
        "user_input",
    }
    assert complete_step.closure_policy.values
    assert all(item.source_status in statuses for item in complete_step.closure_policy.values)
    assert all(item.policy_id and item.certainty_class and item.warning for item in complete_step.closure_policy.values)
    assert any(item.source_status == "engineering_assumption" for item in complete_step.closure_policy.values)
    assert any(item.source_status == "greenhub_legacy_proxy_result" for item in complete_step.closure_policy.values)


def test_complete_grid_summary_is_json_safe(complete_grid):
    summary = summarize_dynamic_complete_proxy_grid(complete_grid)
    assert summary["can_drive_complete_proxy_model_all_steps"] is True
    assert summary["validated_simulation_ready"] is False
    json.dumps(summary)


def test_complete_report_writer_creates_all_seven_csvs(complete_grid, tmp_path):
    paths = write_dynamic_complete_proxy_reports(complete_grid, tmp_path)
    assert set(paths) == {
        "summary", "streams", "units", "alternatives", "assumptions", "balances", "blockers"
    }
    assert all(Path(path).is_file() for path in paths.values())
    assert "source_status" in Path(paths["assumptions"]).read_text(encoding="utf-8")
    assert "identity_closes" in Path(paths["balances"]).read_text(encoding="utf-8")


def test_complete_proxy_does_not_mutate_empirical_registry_or_proxy_data():
    flowsheet = bst.main_flowsheet.get_flowsheet()
    registries = tuple(
        tuple(sorted((item.ID, id(item)) for item in registry))
        for registry in flowsheet.registries
    )
    proxies = dict(load_feedstock_proxies())
    result = run_dynamic_complete_proxy_scenario_step(
        DynamicCompleteProxyConfig(
            upgrading_method="common_conditioning",
            resource_recovery_methods=(),
        ),
        "2026-05",
    )
    assert result.can_drive_complete_proxy_model is True
    assert bst.main_flowsheet.get_flowsheet() is flowsheet
    assert tuple(
        tuple(sorted((item.ID, id(item)) for item in registry))
        for registry in flowsheet.registries
    ) == registries
    assert dict(load_feedstock_proxies()) == proxies

