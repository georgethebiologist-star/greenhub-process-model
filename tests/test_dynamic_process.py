import json

import pytest

from Greenhub.dynamic_feedstock import (
    build_dynamic_feedstock_input_bundle,
    build_dynamic_feedstock_pools,
    default_literature_pool_policy,
)
from Greenhub.dynamic_press import build_dynamic_press_preview_bundle
from Greenhub.dynamic_process import (
    DynamicCentrifugationPolicy,
    DynamicDryingPolicy,
    DynamicProcessStream,
    DynamicProteinExtractionPolicy,
    DynamicRecoveryCentrifugationPolicy,
    build_biogas_residual_mix,
    build_raw_press_baseline_streams,
    demo_baseline_operational_policy,
    preview_baseline_dynamic_operational_scenario,
    preview_first_centrifugation,
    preview_protein_drying,
    preview_protein_extraction,
    preview_second_centrifugation,
    validate_process_stream_mass_balance,
)
from Greenhub.feedstock_proxy import load_feedstock_proxies


def _stream(stream_id, components, *, metadata=None, destination="test"):
    metadata = metadata or {}
    return DynamicProcessStream(
        stream_id=stream_id,
        time_label="2026-05",
        kg_per_kg_feed=sum(components.values()) + sum(metadata.values()),
        component_masses_kg_per_kg_feed=dict(components),
        metadata_pools_kg_per_kg_feed=dict(metadata),
        source_unit="test_fixture",
        destination_hint=destination,
        provenance={"certainty_class": "test_fixture"},
    )


def _output(result, stream_id):
    return next(stream for stream in result.outputs if stream.stream_id == stream_id)


def _press_bundle():
    pools = build_dynamic_feedstock_pools(
        build_dynamic_feedstock_input_bundle("2026-05"),
        default_literature_pool_policy(),
    )
    return build_dynamic_press_preview_bundle(pools)


def test_raw_press_baseline_has_only_cake_and_brown_juice_active_outputs():
    result = build_raw_press_baseline_streams(_press_bundle())

    assert {stream.stream_id for stream in result.outputs} == {"press_cake", "brown_juice"}
    assert result.readiness_flags["protein_concentrate_active_raw_output"] is False
    assert _output(result, "press_cake").kg_per_kg_feed == pytest.approx(0.395)
    assert _output(result, "brown_juice").kg_per_kg_feed == pytest.approx(0.568 + 0.037)
    assert result.mass_balance_summary["overall_closes"] is True
    assert result.mass_balance_summary["identity_closes"] is False
    assert "protein_concentrate" not in {stream.stream_id for stream in result.outputs}


def test_explicit_raw_press_policy_routes_soluble_protein_to_brown_juice():
    press_bundle = _press_bundle()
    scenario = demo_baseline_operational_policy()
    result = build_raw_press_baseline_streams(press_bundle, scenario.raw_press_policy)
    brown_juice = _output(result, "brown_juice")
    feed_soluble = press_bundle.feed_pools.component_mass_fractions["SolubleProtein"]

    assert brown_juice.component_masses_kg_per_kg_feed["SolubleProtein"] == pytest.approx(
        feed_soluble * 0.90
    )
    assert result.mass_balance_summary["identity_closes"] is True


def test_first_centrifugation_retains_soluble_protein_and_captures_particulates():
    brown_juice = _stream(
        "brown_juice",
        {
            "Water": 0.70,
            "SolubleProtein": 0.10,
            "SuspendedProtein": 0.05,
            "SuspendedSolids": 0.03,
            "Glucose": 0.02,
        },
    )
    policy = DynamicCentrifugationPolicy(
        policy_id="test_first_centrifuge",
        suspended_solids_removal_fraction=0.95,
        suspended_protein_removal_fraction=0.90,
        cell_debris_capture_fraction=0.90,
        soluble_protein_loss_fraction=0.02,
        sugar_loss_fraction=0.01,
        ash_loss_fraction=0.50,
        water_split_to_debris_fraction=0.01,
        status="explicit_test_policy",
    )
    result = preview_first_centrifugation(brown_juice, policy)
    clarified = _output(result, "clarified_juice")
    debris = _output(result, "cell_debris")

    assert clarified.component_masses_kg_per_kg_feed["SolubleProtein"] == pytest.approx(0.098)
    assert debris.component_masses_kg_per_kg_feed["SuspendedProtein"] == pytest.approx(0.045)
    assert debris.component_masses_kg_per_kg_feed["SuspendedSolids"] == pytest.approx(0.0285)
    assert result.mass_balance_summary["closes"] is True


def test_protein_extraction_recovers_soluble_protein_and_keeps_sugars_in_supernatant():
    clarified = _stream(
        "clarified_juice",
        {"Water": 0.80, "SolubleProtein": 0.10, "Glucose": 0.04, "Sucrose": 0.06},
    )
    policy = DynamicProteinExtractionPolicy(
        policy_id="test_extraction",
        method="generic",
        soluble_protein_recovery_fraction=0.75,
        water_to_protein_phase_fraction=0.05,
        status="explicit_test_policy",
    )
    result = preview_protein_extraction(clarified, policy)
    protein_phase = _output(result, "protein_rich_phase")
    supernatant = _output(result, "extraction_supernatant")

    assert protein_phase.component_masses_kg_per_kg_feed["SolubleProtein"] == pytest.approx(0.075)
    assert supernatant.component_masses_kg_per_kg_feed["SolubleProtein"] == pytest.approx(0.025)
    assert "Glucose" not in protein_phase.component_masses_kg_per_kg_feed
    assert supernatant.component_masses_kg_per_kg_feed["Glucose"] == pytest.approx(0.04)
    assert supernatant.component_masses_kg_per_kg_feed["Sucrose"] == pytest.approx(0.06)
    assert result.mass_balance_summary["closes"] is True


def test_second_centrifugation_creates_wet_cake_and_final_supernatant():
    protein_phase = _stream(
        "protein_rich_phase",
        {"Water": 0.20, "SolubleProtein": 0.10, "Ash": 0.01},
    )
    extraction_supernatant = _stream(
        "extraction_supernatant",
        {"Water": 0.50, "Glucose": 0.10, "SolubleProtein": 0.02},
    )
    policy = DynamicRecoveryCentrifugationPolicy(
        policy_id="test_second_centrifuge",
        protein_phase_capture_fraction=0.98,
        soluble_protein_loss_to_supernatant_fraction=0.02,
        water_retention_in_cake_fraction=0.20,
        ash_retention_in_cake_fraction=0.80,
        status="explicit_test_policy",
    )
    result = preview_second_centrifugation(protein_phase, extraction_supernatant, policy)
    wet_cake = _output(result, "wet_protein_cake")
    final_supernatant = _output(result, "final_supernatant")

    assert wet_cake.component_masses_kg_per_kg_feed["SolubleProtein"] == pytest.approx(
        0.10 * 0.98 * 0.98
    )
    assert final_supernatant.component_masses_kg_per_kg_feed["Glucose"] == pytest.approx(0.10)
    assert result.mass_balance_summary["closes"] is True


def test_drying_removes_only_water_and_preserves_protein():
    wet_cake = _stream("wet_protein_cake", {"Water": 0.80, "SolubleProtein": 0.20})
    result = preview_protein_drying(
        wet_cake,
        DynamicDryingPolicy(
            policy_id="test_drying",
            target_moisture_fraction=0.10,
            status="explicit_test_policy",
        ),
    )
    dried = _output(result, "dried_protein_product")
    evaporated = _output(result, "evaporated_water")

    assert dried.component_masses_kg_per_kg_feed["SolubleProtein"] == pytest.approx(0.20)
    assert evaporated.component_masses_kg_per_kg_feed == {
        "Water": pytest.approx(0.80 - (0.10 * 0.20 / 0.90))
    }
    assert set(evaporated.component_masses_kg_per_kg_feed) == {"Water"}
    assert "drying_energy_missing" in result.warnings
    assert result.mass_balance_summary["closes"] is True


def test_residual_mix_combines_press_cake_debris_and_supernatant_when_explicitly_routed():
    press_cake = _stream("press_cake", {"Cellulose": 0.20, "SuspendedProtein": 0.05})
    debris = _stream("cell_debris", {"SuspendedProtein": 0.02, "Water": 0.03})
    supernatant = _stream("final_supernatant", {"Water": 0.50, "Glucose": 0.10})
    result = build_biogas_residual_mix(
        debris,
        supernatant,
        press_cake=press_cake,
        include_press_cake=True,
    )
    candidate = _output(result, "biogas_feed_candidate")

    assert candidate.kg_per_kg_feed == pytest.approx(0.90)
    assert candidate.component_masses_kg_per_kg_feed["SuspendedProtein"] == pytest.approx(0.07)
    assert result.readiness_flags["has_carbohydrates"] is True
    assert result.readiness_flags["has_proteins"] is True
    assert result.readiness_flags["missing_COD"] is True


def test_default_orchestrator_returns_mass_conserving_partial_blocked_preview():
    preview = preview_baseline_dynamic_operational_scenario()
    residual_input_ids = {stream.stream_id for stream in preview.biogas_mix_preparation.inputs}

    assert preview.can_drive_simulation is False
    assert preview.scenario.is_demo is False
    assert preview.mass_balance_summary["overall_closes"] is True
    assert preview.mass_balance_summary["identity_closes"] is False
    assert preview.blockers
    assert "press_cake" not in residual_input_ids
    assert any(stream.stream_id == "press_cake" for stream in preview.final_outputs)
    json.dumps(preview.to_dict())


def test_demo_policy_runs_full_identity_conserving_preview_but_stays_report_only():
    scenario = demo_baseline_operational_policy()
    preview = preview_baseline_dynamic_operational_scenario(scenario=scenario)

    assert scenario.is_demo is True
    assert scenario.raw_press_policy.status == "demo_engineering_assumption"
    assert preview.mass_balance_summary["closes"] is True
    assert preview.mass_balance_summary["identity_closes"] is True
    assert preview.first_centrifugation.readiness_flags["mass_preview_ready"] is True
    assert preview.protein_extraction.readiness_flags["protein_phase_created"] is True
    assert preview.second_centrifugation.readiness_flags["wet_protein_cake_created"] is True
    assert preview.drying.readiness_flags["mass_preview_ready"] is True
    assert preview.can_drive_simulation is False
    assert all(stream.can_enter_simulation is False for stream in preview.final_outputs)


def test_dynamic_operational_preview_does_not_change_empirical_feedstock_proxies():
    before = dict(load_feedstock_proxies())

    preview_baseline_dynamic_operational_scenario()
    preview_baseline_dynamic_operational_scenario(scenario=demo_baseline_operational_policy())

    assert dict(load_feedstock_proxies()) == before
