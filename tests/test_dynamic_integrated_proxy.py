from __future__ import annotations

import json
from pathlib import Path

import biosteam as bst
import pytest

from Greenhub.dynamic_integrated_proxy import (
    BiogasUpgradingMethod,
    DynamicIntegratedProxyConfig,
    ResourceRecoveryMethod,
    run_dynamic_integrated_proxy_scenario_grid,
    run_dynamic_integrated_proxy_scenario_step,
    summarize_biogas_upgrading_alternatives,
    summarize_dynamic_drying_alternatives,
    summarize_resource_recovery_alternatives,
    write_dynamic_integrated_proxy_reports,
)
from Greenhub.feedstock_proxy import load_feedstock_proxies


@pytest.fixture(scope="module")
def baseline_step():
    return run_dynamic_integrated_proxy_scenario_step(
        DynamicIntegratedProxyConfig(), "2026-05"
    )


@pytest.fixture(scope="module")
def integrated_grid():
    return run_dynamic_integrated_proxy_scenario_grid()


def test_isoelectric_remains_baseline_and_calculation_ready(baseline_step):
    assert baseline_step.protein_run.selected_method == "isoelectric"
    assert baseline_step.can_drive_proxy_preview is True
    assert baseline_step.can_drive_calculation_shadow_system is True
    assert baseline_step.can_drive_simulation is False
    assert baseline_step.validated_simulation_ready is False


@pytest.mark.parametrize(
    "method,record_id",
    (("lactic_acid", "PR-005"), ("membrane", "REJ-001")),
)
def test_supported_protein_alternatives_are_mutually_exclusive_and_traceable(
    method, record_id
):
    result = run_dynamic_integrated_proxy_scenario_step(
        DynamicIntegratedProxyConfig(protein_method=method), "2026-05"
    )
    assert result.protein_run.selected_method == method
    assert result.can_drive_calculation_shadow_system is True
    assert record_id in result.protein_run.source_record_ids
    assert "REC-001" not in result.protein_run.source_record_ids


def test_invalid_blended_protein_method_is_rejected():
    with pytest.raises(ValueError):
        DynamicIntegratedProxyConfig(protein_method="isoelectric+membrane")


def test_generic_protein_method_requires_and_uses_explicit_caller_policy():
    blocked = run_dynamic_integrated_proxy_scenario_step(
        DynamicIntegratedProxyConfig(protein_method="generic"), "2026-05"
    )
    assert blocked.can_drive_calculation_shadow_system is False
    configured = run_dynamic_integrated_proxy_scenario_step(
        DynamicIntegratedProxyConfig(
            protein_method="generic",
            generic_protein_recovery_fraction=0.40,
            generic_protein_policy_id="user_generic_001",
            generic_protein_provenance_note="researcher scenario input",
        ),
        "2026-05",
    )
    assert configured.can_drive_calculation_shadow_system is True
    assert configured.protein_run.policy_ids["protein_extraction"] == "user_generic_001"
    assert "EXPLICIT USER ASSUMPTION" in " ".join(configured.warnings)


def test_drying_mass_target_remains_15_percent_and_energy_is_explicitly_blocked(
    baseline_step,
):
    assert baseline_step.drying.payload.target_moisture_fraction == pytest.approx(0.15)
    assert baseline_step.drying.water_removed_kg_hr > 0.0
    assert baseline_step.drying.protein_preserved is True
    assert baseline_step.drying.mass_preview_ready is True
    assert baseline_step.drying.energy_preview_ready is False
    assert "drying_energy_missing" in baseline_step.drying.blockers
    alternatives = summarize_dynamic_drying_alternatives()
    assert alternatives["spray_drying_proxy"]["energy_preview_ready"] is False
    assert alternatives["freeze_drying_proxy"]["energy_preview_ready"] is False


def test_ad_preview_uses_only_debris_and_supernatant_boundary(baseline_step):
    assert baseline_step.ad.press_cake_included is False
    assert baseline_step.ad.residual_feed_kg_hr > 0.0
    assert baseline_step.product_outputs["press_cake_kg_hr"] > 0.0
    assert "press cake excluded" in " ".join(baseline_step.ad.warnings)


def test_bmp_potential_and_time_markers_are_calculated(baseline_step):
    assert baseline_step.ad.payload.bmp_m3_ch4_per_kg_vs == pytest.approx(0.52028)
    assert baseline_step.ad.payload.methane_fraction == pytest.approx(0.871)
    assert baseline_step.ad.payload.t80_days == pytest.approx(5.0)
    assert baseline_step.ad.payload.t90_days == pytest.approx(11.0)
    assert baseline_step.ad.methane_potential_m3_hr > 0.0
    assert baseline_step.ad.potential_ready is True
    assert baseline_step.ad.kinetics_run is False


def test_upgrading_alternatives_are_separate_and_not_blended():
    alternatives = summarize_biogas_upgrading_alternatives()
    assert alternatives["membrane"]["calculation_ready"] is True
    assert alternatives["water_scrubbing"]["calculation_ready"] is True
    assert alternatives["psa"]["calculation_ready"] is True
    assert alternatives["mea"]["calculation_ready"] is False
    result = run_dynamic_integrated_proxy_scenario_step(
        DynamicIntegratedProxyConfig(upgrading_method="membrane"), "2026-05"
    )
    assert result.upgrading.policy.method == "membrane"
    assert result.upgrading.biomethane_product_m3_hr > 0.0
    assert result.upgrading.policy.methane_recovery_fraction == pytest.approx(0.987)
    assert result.upgrading.policy.product_methane_fraction == pytest.approx(0.984)
    assert result.upgrading.electric_demand_kwh_hr > 0.0


def test_resource_recovery_alternatives_preserve_speciation_blockers():
    previews = summarize_resource_recovery_alternatives(
        (ResourceRecoveryMethod.AMMONIA_RECOVERY.value,)
    )
    ammonia = next(item for item in previews if item.method == "ammonia_recovery")
    phosphorus = next(item for item in previews if item.method == "phosphorus_recovery")
    assert ammonia.selected is True
    assert ammonia.calculation_ready is False
    assert "missing_TAN" in ammonia.blockers
    assert all(value is None for value in ammonia.product_candidates.values())
    assert "missing_PO4" in phosphorus.blockers


def test_integrated_grid_covers_may_through_november(integrated_grid):
    assert integrated_grid.time_labels == (
        "2026-05", "2026-06", "2026-07", "2026-08", "2026-09", "2026-10", "2026-11"
    )
    assert integrated_grid.all_steps_proxy_ready is True
    assert integrated_grid.all_steps_calculation_shadow_ready is True
    assert integrated_grid.output_ranges["dried_protein_product_kg_hr"]["max"] > integrated_grid.output_ranges["dried_protein_product_kg_hr"]["min"]
    json.dumps(integrated_grid.to_dict())


def test_integrated_reports_are_written(integrated_grid, tmp_path):
    paths = write_dynamic_integrated_proxy_reports(integrated_grid, tmp_path)
    assert set(paths) == {"summary", "streams", "units", "alternatives", "blockers"}
    assert all(Path(path).is_file() for path in paths.values())
    assert "methane_potential_m3_hr" in Path(paths["summary"]).read_text(encoding="utf-8")
    assert "resource_recovery" in Path(paths["alternatives"]).read_text(encoding="utf-8")


def test_integrated_runner_does_not_mutate_empirical_flowsheet_or_proxy_data():
    before_flowsheet = bst.main_flowsheet.get_flowsheet()
    before_registries = tuple(
        tuple(sorted((item.ID, id(item)) for item in registry))
        for registry in before_flowsheet.registries
    )
    before_proxies = dict(load_feedstock_proxies())
    result = run_dynamic_integrated_proxy_scenario_step(
        DynamicIntegratedProxyConfig(upgrading_method=BiogasUpgradingMethod.PSA.value),
        "2026-05",
    )
    assert result.can_drive_simulation is False
    assert bst.main_flowsheet.get_flowsheet() is before_flowsheet
    assert tuple(
        tuple(sorted((item.ID, id(item)) for item in registry))
        for registry in before_flowsheet.registries
    ) == before_registries
    assert dict(load_feedstock_proxies()) == before_proxies
