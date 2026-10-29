import json
from pathlib import Path

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
    DynamicProteinScenarioConfig,
    ProteinExtractionMethod,
    build_dataset_drying_policy,
    build_dataset_first_centrifugation_policy,
    build_dataset_protein_extraction_policy,
    build_dataset_residual_biogas_policy,
    build_dataset_second_centrifugation_policy,
    build_biogas_residual_mix,
    build_direct_raw_press_policy,
    build_raw_press_baseline_streams,
    demo_baseline_operational_policy,
    default_proxy_closure_policy,
    preview_baseline_dynamic_operational_scenario,
    preview_first_centrifugation,
    preview_protein_drying,
    preview_protein_extraction,
    preview_closed_proxy_dynamic_protein_pathway,
    preview_proxy_enabled_dynamic_operational_scenario,
    preview_second_centrifugation,
    run_dynamic_protein_scenario_grid,
    run_dynamic_protein_scenario_step,
    select_dynamic_protein_extraction_method,
    summarize_dynamic_protein_block_resolution,
    summarize_protein_method_alternatives,
    summarize_dynamic_protein_scenario_grid,
    validate_process_stream_mass_balance,
    write_proxy_dynamic_protein_pathway_reports,
    write_dynamic_protein_scenario_grid_reports,
)
from Greenhub.dynamic_unit_data import (
    load_ad_bmp_evidence,
    load_centrifuge_debris_capture_evidence,
    load_centrifuge_policy_evidence,
    load_direct_raw_press_evidence,
    load_isoelectric_recovery_evidence,
    load_second_centrifuge_capture_evidence,
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


@pytest.fixture(scope="module")
def closed_proxy_preview():
    return preview_closed_proxy_dynamic_protein_pathway()


@pytest.fixture(scope="module")
def dynamic_protein_grid_result():
    return run_dynamic_protein_scenario_grid(DynamicProteinScenarioConfig())


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


def test_residual_mix_rejects_press_cake_from_in_project_biogas_boundary():
    press_cake = _stream("press_cake", {"Cellulose": 0.20, "SuspendedProtein": 0.05})
    debris = _stream("cell_debris", {"SuspendedProtein": 0.02, "Water": 0.03})
    supernatant = _stream("final_supernatant", {"Water": 0.50, "Glucose": 0.10})
    with pytest.raises(ValueError, match="outside the in-project dynamic AD boundary"):
        build_biogas_residual_mix(
            debris,
            supernatant,
            press_cake=press_cake,
            include_press_cake=True,
        )

    result = build_biogas_residual_mix(debris, supernatant, press_cake=press_cake)
    candidate = _output(result, "biogas_feed_candidate")
    assert candidate.kg_per_kg_feed == pytest.approx(0.65)
    assert "Cellulose" not in candidate.component_masses_kg_per_kg_feed
    assert result.readiness_flags["has_proteins"] is True


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


def test_unit_evidence_loaders_preserve_named_proxy_records():
    cap = load_centrifuge_policy_evidence().by_parameter_id("CAP-ALF-001")
    rec = load_isoelectric_recovery_evidence().by_parameter_id("REC-001")
    bmp = load_ad_bmp_evidence().by_parameter_id("BMP_DFOS_VS")

    assert cap is not None and cap.evidence_class == "proxy_scenario_bound"
    assert cap.normalized_value == pytest.approx(0.8)
    assert rec is not None and rec.proxy_class == "n_to_soluble_protein_proxy"
    assert rec.basis == "precipitated N / N in cleared juice"
    assert bmp is not None and bmp.normalized_value == pytest.approx(0.52028)
    assert bmp.original_material == "grass biorefinery de-FOS whey"


def test_isoelectric_is_default_and_only_one_method_is_selected():
    policy = select_dynamic_protein_extraction_method()
    assert policy.method == ProteinExtractionMethod.ISOELECTRIC.value
    with pytest.raises(ValueError, match="choose one of"):
        select_dynamic_protein_extraction_method("isoelectric+membrane", allow_proxy=True)


def test_proxy_isoelectric_uses_rec_001_only_with_explicit_n_proxy_permission():
    strict = build_dataset_protein_extraction_policy(
        method="isoelectric",
        allow_proxy=True,
        allow_n_to_protein_proxy=False,
    )
    proxy = build_dataset_protein_extraction_policy(
        method="isoelectric",
        allow_proxy=True,
        allow_n_to_protein_proxy=True,
    )

    assert strict.soluble_protein_recovery_fraction is None
    assert strict.status == "blocked_requires_explicit_n_to_protein_proxy"
    assert strict.provenance["evidence_record_ids"] == ["REC-001", "LOSS-001", "ABD-001"]
    assert proxy.soluble_protein_recovery_fraction == pytest.approx(0.34)
    assert proxy.proxy_class == "n_to_soluble_protein_recovery_proxy"
    assert any("precipitated nitrogen" in warning for warning in proxy.warnings)


def test_proxy_first_centrifuge_uses_alfalfa_bound_without_inventing_debris_capture():
    strict = build_dataset_first_centrifugation_policy(allow_proxy=False)
    proxy = build_dataset_first_centrifugation_policy(allow_proxy=True)

    assert strict.soluble_protein_loss_fraction is None
    assert proxy.soluble_protein_loss_fraction == pytest.approx(0.2)
    assert proxy.suspended_protein_removal_fraction is None
    assert "suspended_protein_capture_missing" in proxy.blockers
    assert proxy.provenance["evidence_record_ids"] == ["CAP-ALF-001"]


def test_alternative_methods_are_inactive_until_selected_and_never_blended():
    alternatives = summarize_protein_method_alternatives()
    membrane = select_dynamic_protein_extraction_method("membrane", allow_proxy=True)

    assert alternatives["lactic_acid"]["active_by_default"] is False
    assert alternatives["membrane"]["can_run_proxy_preview"] is True
    assert membrane.method == "membrane"
    assert membrane.policy_id == "dataset_membrane_cp_rejection_proxy_v1"
    assert "REC-001" not in membrane.provenance["evidence_record_ids"]


def test_drying_stays_blocked_without_source_backed_target_moisture():
    policy = build_dataset_drying_policy(allow_proxy=True)
    assert policy.target_moisture_fraction is None
    assert "target_product_moisture_missing" in policy.blockers
    assert policy.can_drive_proxy_preview is False


def test_de_fos_bmp_is_proxy_metadata_for_supernatant_not_press_cake():
    policy = build_dataset_residual_biogas_policy(allow_proxy=True)
    assert policy.bmp_m3_ch4_per_kg_vs == pytest.approx(0.52028)
    assert policy.applicable_stream == "final_supernatant_only"
    assert policy.proxy_class == "de_fos_whey_for_supernatant_proxy"
    assert "residual_VS_missing" in policy.blockers


def test_residual_bmp_report_exposes_supernatant_basis_and_unmodeled_vs():
    preview = preview_proxy_enabled_dynamic_operational_scenario(
        proxy_closure_policy=default_proxy_closure_policy(),
    )
    metrics = preview.biogas_mix_preparation.metrics
    assert metrics["bmp_basis_stream"] == "final_supernatant_only"
    assert metrics["methane_potential_basis"].startswith("supernatant_vs")
    assert metrics["unmodeled_vs_kg_per_kg_feed"] is not None


def test_proxy_enabled_pathway_is_partial_report_only_and_excludes_press_cake_from_biogas():
    preview = preview_proxy_enabled_dynamic_operational_scenario()
    summary = summarize_dynamic_protein_block_resolution(preview)
    residual_inputs = {stream.stream_id for stream in preview.biogas_mix_preparation.inputs}

    assert preview.selected_method == "isoelectric"
    assert preview.method_policy["soluble_protein_recovery_fraction"] == pytest.approx(0.34)
    assert "press_cake" in preview.system_outputs
    assert "press_cake" not in residual_inputs
    assert residual_inputs == {"cell_debris", "final_supernatant"}
    assert summary["brown_juice_soluble_protein_available"] is True
    assert summary["selected_extraction_method_resolved"] is True
    assert summary["second_centrifuge_resolved"] is False
    assert summary["drying_resolved"] is False
    assert preview.can_drive_proxy_preview is False
    assert preview.can_drive_simulation is False
    json.dumps(preview.to_dict())


def test_selected_membrane_pathway_does_not_activate_isoelectric_policy():
    preview = preview_proxy_enabled_dynamic_operational_scenario(method="membrane")
    assert preview.selected_method == "membrane"
    assert preview.method_policy["policy_id"] == "dataset_membrane_cp_rejection_proxy_v1"
    assert "isoelectric" in preview.inactive_alternative_methods
    assert preview.protein_extraction.applied_policy["method"] == "membrane"


def test_proxy_enabled_operational_path_does_not_change_empirical_proxy_output():
    before = dict(load_feedstock_proxies())
    preview_proxy_enabled_dynamic_operational_scenario()
    assert dict(load_feedstock_proxies()) == before


def test_closed_proxy_pathway_is_preview_ready_but_not_simulation_ready(closed_proxy_preview):
    assert closed_proxy_preview.can_drive_proxy_preview is True
    assert closed_proxy_preview.can_drive_simulation is False
    assert closed_proxy_preview.validated_simulation_ready is False
    assert closed_proxy_preview.mass_balance_summary["overall_closes"] is True
    assert closed_proxy_preview.mass_balance_summary["identity_closes"] is True


def test_closed_proxy_press_cake_is_external_and_not_in_biogas(closed_proxy_preview):
    residual_inputs = {
        stream.stream_id for stream in closed_proxy_preview.biogas_mix_preparation.inputs
    }
    assert "press_cake" in closed_proxy_preview.system_outputs
    assert residual_inputs == {"cell_debris", "final_supernatant"}


def test_closed_proxy_drying_produces_product_and_preserves_protein(closed_proxy_preview):
    wet = _output(closed_proxy_preview.second_centrifugation, "wet_protein_cake")
    dried = _output(closed_proxy_preview.drying, "dried_protein_product")
    evaporated = _output(closed_proxy_preview.drying, "evaporated_water")

    assert dried.kg_per_kg_feed > 0.0
    assert dried.component_masses_kg_per_kg_feed["SolubleProtein"] == pytest.approx(
        wet.component_masses_kg_per_kg_feed["SolubleProtein"]
    )
    for component, mass in wet.component_masses_kg_per_kg_feed.items():
        if component != "Water":
            assert dried.component_masses_kg_per_kg_feed[component] == pytest.approx(mass)
    assert set(evaporated.component_masses_kg_per_kg_feed) == {"Water"}
    assert evaporated.component_masses_kg_per_kg_feed["Water"] > 0.0


def test_closed_proxy_residual_is_debris_plus_final_supernatant(closed_proxy_preview):
    debris = _output(closed_proxy_preview.first_centrifugation, "cell_debris")
    supernatant = _output(closed_proxy_preview.second_centrifugation, "final_supernatant")
    candidate = _output(closed_proxy_preview.biogas_mix_preparation, "biogas_feed_candidate")
    assert candidate.kg_per_kg_feed == pytest.approx(
        debris.kg_per_kg_feed + supernatant.kg_per_kg_feed
    )


def test_closed_proxy_vs_bmp_is_labelled_and_does_not_run_ad(closed_proxy_preview):
    residual = closed_proxy_preview.biogas_mix_preparation
    assert residual.metrics["estimated_residual_vs_kg_per_kg_feed"] > 0.0
    assert residual.metrics["bmp_eligible_vs_kg_per_kg_feed"] > 0.0
    assert residual.metrics["methane_potential_m3_ch4_per_kg_feed"] > 0.0
    assert residual.metrics["ad_kinetics_run"] is False
    assert residual.metrics["evidence_class"] == "mixed_proxy_and_engineering_proxy_closure"
    assert "AD_kinetics_not_implemented" in residual.blockers


def test_proxy_closure_assumptions_are_explicitly_labelled(closed_proxy_preview):
    closure = default_proxy_closure_policy()
    assert closure.evidence_class == "engineering_proxy_closure"
    assert closure.provenance["reason"] == "to close report-only proxy preview"
    assert closure.provenance["not_measured"] is True
    assert all(
        unit.applied_policy.get("status") == "proxy_enabled_report_only_closed"
        or unit.unit_id in {"protein_drying", "biogas_residual_mixer"}
        for unit in (
            closed_proxy_preview.raw_press,
            closed_proxy_preview.first_centrifugation,
            closed_proxy_preview.protein_extraction,
            closed_proxy_preview.second_centrifugation,
            closed_proxy_preview.drying,
            closed_proxy_preview.biogas_mix_preparation,
        )
    )


def test_proxy_pathway_csv_writers_create_three_inspectable_files(
    closed_proxy_preview,
    tmp_path,
):
    paths = write_proxy_dynamic_protein_pathway_reports(
        closed_proxy_preview,
        output_dir=tmp_path,
    )
    assert set(paths) == {"streams", "units", "summary"}
    for path in paths.values():
        assert Path(path).is_file()
    streams_text = Path(paths["streams"]).read_text(encoding="utf-8")
    summary_text = Path(paths["summary"]).read_text(encoding="utf-8")
    assert "component_mass_kg_per_kg_feed" in streams_text
    assert "engineering_proxy_closure" in streams_text
    assert "can_drive_proxy_preview" in summary_text


def test_closed_proxy_pathway_does_not_change_empirical_feedstock_output():
    before = dict(load_feedstock_proxies())
    preview_closed_proxy_dynamic_protein_pathway()
    assert dict(load_feedstock_proxies()) == before


def test_new_dynamic_unit_loaders_preserve_raw_centrifuge_source_records():
    raw = load_direct_raw_press_evidence()
    debris = load_centrifuge_debris_capture_evidence()
    second = load_second_centrifuge_capture_evidence()

    assert raw.by_parameter_id("RAW_0001").normalized_value == pytest.approx(0.4375)
    assert raw.by_parameter_id("RAW_0001").evidence_class == "direct_usable"
    assert debris.by_parameter_id("CEN_0011").normalized_value == pytest.approx(0.319961)
    assert debris.by_parameter_id("CEN_0013").normalized_value == pytest.approx(0.0827)
    assert debris.by_parameter_id("CEN_0030").evidence_class == "blocked_missing"
    assert second.by_parameter_id("PCEN_0003").normalized_value == pytest.approx(0.781)
    assert second.by_parameter_id("PCEN_0010").evidence_class == "proxy_scenario_bound"


def test_closed_raw_press_uses_direct_prg_yields_without_normalizing_losses(closed_proxy_preview):
    raw = closed_proxy_preview.raw_press
    policy = raw.applied_policy
    unrecovered = _output(raw, "raw_press_unrecovered_process_mass")

    assert policy["policy_id"] == "raw_press_lolium_perenne_2025"
    assert policy["press_cake_mass_yield_fraction"] == pytest.approx(0.4375)
    assert policy["brown_juice_mass_yield_fraction"] == pytest.approx(0.457447)
    assert policy["recovered_mass_closure_fraction"] == pytest.approx(0.894947)
    assert raw.metrics["source_yields_normalized"] is False
    assert raw.metrics["source_fresh_mass_yields"]["unrecovered"] == pytest.approx(0.105053)
    assert _output(raw, "press_cake").kg_per_kg_feed == pytest.approx(0.4375)
    assert _output(raw, "brown_juice").kg_per_kg_feed == pytest.approx(0.457447)
    assert unrecovered.kg_per_kg_feed == pytest.approx(0.105053)
    assert sum(stream.kg_per_kg_feed for stream in raw.outputs) == pytest.approx(1.0)
    assert _output(raw, "press_cake").kg_per_kg_feed + _output(raw, "brown_juice").kg_per_kg_feed < 1.0


def test_direct_raw_press_labels_total_cp_class_proxy():
    policy = build_direct_raw_press_policy(default_proxy_closure_policy())
    evidence = policy.provenance["field_evidence_class"]

    assert evidence["Water"] == "direct_grass_source"
    assert evidence["SolubleProtein"] == "total_crude_protein_proxy_for_soluble_suspended_classes"
    assert evidence["SuspendedProtein"] == "total_crude_protein_proxy_for_soluble_suspended_classes"
    assert policy.component_fractions_to_cake["SolubleProtein"] == pytest.approx(0.587)
    assert policy.component_fractions_to_juice["SolubleProtein"] == pytest.approx(0.410)


def test_closed_first_centrifuge_uses_cen_0011_and_cen_0013(closed_proxy_preview):
    unit = closed_proxy_preview.first_centrifugation
    debris = _output(unit, "cell_debris")
    brown = _output(closed_proxy_preview.raw_press, "brown_juice")

    assert unit.applied_policy["policy_id"] == "centrifuge_alfalfa_raw_debris_3500g_proxy"
    assert unit.metrics["source_record_ids"] == ["CEN_0011", "CEN_0013"]
    assert debris.kg_per_kg_feed == pytest.approx(brown.kg_per_kg_feed * 0.319961)
    assert unit.metrics["cell_debris_dry_mass_kg_per_kg_feed"] == pytest.approx(
        debris.kg_per_kg_feed * 0.0827
    )
    assert unit.metrics["evidence_class"] == "legume_proxy"


def test_closed_second_centrifuge_uses_direct_prg_cake_moisture(closed_proxy_preview):
    unit = closed_proxy_preview.second_centrifugation
    cake = _output(unit, "wet_protein_cake")
    moisture = cake.component_masses_kg_per_kg_feed["Water"] / cake.kg_per_kg_feed

    assert unit.applied_policy["policy_id"] == "second_centrifuge_prg_pH3_5_21000g"
    assert unit.metrics["source_record_ids"] == ["PCEN_0003"]
    assert moisture == pytest.approx(0.781)
    assert unit.metrics["evidence_class"] == "direct_grass_source"


def test_pcen_0010_is_optional_combined_route_lower_bound_not_centrifuge_capture():
    closure = default_proxy_closure_policy()
    default = build_dataset_second_centrifugation_policy(
        allow_proxy=True,
        closure_policy=closure,
    )
    envelope = build_dataset_second_centrifugation_policy(
        allow_proxy=True,
        closure_policy=closure,
        allow_combined_recovery_envelope=True,
    )

    assert default.combined_recovery_lower_bound is None
    assert envelope.combined_recovery_lower_bound == pytest.approx(0.90)
    assert envelope.protein_phase_capture_fraction == closure.protein_phase_capture_fraction
    assert "not pure centrifuge capture" in "|".join(envelope.warnings)


def test_closed_drying_uses_frontend_ready_15_percent_scenario_target(closed_proxy_preview):
    policy = closed_proxy_preview.drying.applied_policy
    dried = _output(closed_proxy_preview.drying, "dried_protein_product")
    moisture = dried.component_masses_kg_per_kg_feed["Water"] / dried.kg_per_kg_feed

    assert policy["target_moisture_fraction"] == pytest.approx(0.15)
    assert policy["provenance"]["field_evidence_class"]["target_moisture_fraction"] == "scenario_input_baseline"
    assert policy["provenance"]["scenario_input"]["future_frontend_ready"] is True
    assert moisture == pytest.approx(0.15)
    assert "drying_energy_missing" in closed_proxy_preview.drying.warnings


def test_closed_drying_accepts_explicit_scenario_target_override():
    preview = preview_closed_proxy_dynamic_protein_pathway(target_moisture_fraction=0.20)
    policy = preview.drying.applied_policy
    dried = _output(preview.drying, "dried_protein_product")

    assert policy["target_moisture_fraction"] == pytest.approx(0.20)
    assert policy["provenance"]["field_evidence_class"]["target_moisture_fraction"] == "scenario_input_override"
    assert dried.component_masses_kg_per_kg_feed["Water"] / dried.kg_per_kg_feed == pytest.approx(0.20)


def test_default_dynamic_protein_scenario_config_validates_monthly_grid():
    config = DynamicProteinScenarioConfig()
    step = run_dynamic_protein_scenario_step(config, "2026-05")

    assert config.time_step == "monthly"
    assert config.drying_target_moisture_fraction == pytest.approx(0.15)
    assert config.raw_press_policy_id == "raw_press_lolium_perenne_2025"
    assert step.policy_ids["dynamic_raw_press"] == "raw_press_lolium_perenne_2025"


def test_opt_in_process_water_changes_shared_feed_basis_and_closes_pathway():
    baseline = run_dynamic_protein_scenario_step(DynamicProteinScenarioConfig(), "2026-05")
    diluted = run_dynamic_protein_scenario_step(
        DynamicProteinScenarioConfig(pretreatment_water_addition_kg_per_kg_wet_feed=0.5),
        "2026-05",
    )

    assert diluted.pathway_preview.feed_pools.water_wet_fraction > baseline.pathway_preview.feed_pools.water_wet_fraction
    assert diluted.pathway_preview.feed_pools.provenance["process_water_addition_kg_per_kg_wet_feed"] == pytest.approx(0.5)
    assert diluted.pathway_preview.mass_balance_summary["closes"] is True
    assert diluted.pathway_preview.dynamic_press_bundle.feed_pools is diluted.pathway_preview.feed_pools


def test_negative_process_water_is_rejected():
    with pytest.raises(ValueError, match="pretreatment_water_addition"):
        DynamicProteinScenarioConfig(pretreatment_water_addition_kg_per_kg_wet_feed=-0.1)


@pytest.mark.parametrize("target", [-0.01, 1.0, 1.2])
def test_dynamic_protein_scenario_rejects_invalid_moisture_target(target):
    with pytest.raises(ValueError, match="drying_target_moisture_fraction must be >= 0 and < 1"):
        DynamicProteinScenarioConfig(drying_target_moisture_fraction=target)


def test_dynamic_protein_scenario_rejects_unknown_policy_id():
    with pytest.raises(ValueError, match="Unknown raw_press_policy_id"):
        DynamicProteinScenarioConfig(raw_press_policy_id="unknown_raw_press")


def test_press_cake_biogas_request_requires_external_scope_override():
    with pytest.raises(ValueError, match="external_scope_override=True"):
        DynamicProteinScenarioConfig(include_press_cake_in_biogas=True)


def test_grid_runner_returns_all_expected_monthly_labels(dynamic_protein_grid_result):
    assert [run.time_label for run in dynamic_protein_grid_result.runs] == [
        "2026-05",
        "2026-06",
        "2026-07",
        "2026-08",
        "2026-09",
        "2026-10",
        "2026-11",
    ]


def test_grid_steps_keep_press_cake_external_to_biogas(dynamic_protein_grid_result):
    for run in dynamic_protein_grid_result.runs:
        preview = run.pathway_preview
        assert preview is not None
        residual_inputs = {
            stream.stream_id for stream in preview.biogas_mix_preparation.inputs
        }
        assert "press_cake" in preview.system_outputs
        assert residual_inputs == {"cell_debris", "final_supernatant"}


def test_grid_steps_all_close_proxy_preview_not_simulation(dynamic_protein_grid_result):
    assert all(run.can_drive_proxy_preview for run in dynamic_protein_grid_result.runs)
    assert not any(run.can_drive_simulation for run in dynamic_protein_grid_result.runs)
    assert not any(run.validated_simulation_ready for run in dynamic_protein_grid_result.runs)


def test_grid_dried_product_varies_with_monthly_feedstock(dynamic_protein_grid_result):
    values = {
        run.output_masses_kg_per_kg_feed["dried_protein_product"]
        for run in dynamic_protein_grid_result.runs
    }
    assert len(values) > 1
    assert dynamic_protein_grid_result.output_ranges_kg_per_kg_feed[
        "dried_protein_product"
    ]["min"] < dynamic_protein_grid_result.output_ranges_kg_per_kg_feed[
        "dried_protein_product"
    ]["max"]


def test_grid_summary_is_json_safe(dynamic_protein_grid_result):
    summary = summarize_dynamic_protein_scenario_grid(dynamic_protein_grid_result)

    json.dumps(summary)
    assert summary["number_of_steps"] == 7
    assert summary["can_drive_proxy_preview_all_steps"] is True
    assert summary["can_drive_simulation_all_steps"] is False
    assert "biosteam_adapter_not_implemented" in summary["next_activation_blockers"]


def test_grid_csv_writers_create_four_traceable_reports(
    dynamic_protein_grid_result,
    tmp_path,
):
    paths = write_dynamic_protein_scenario_grid_reports(
        dynamic_protein_grid_result,
        output_dir=tmp_path,
    )

    assert set(paths) == {"summary", "streams", "units", "blockers"}
    for path in paths.values():
        assert Path(path).is_file()
    required = {
        "scenario_id",
        "time_label",
        "unit_id",
        "stream_id",
        "selected_method",
        "policy_ids",
        "evidence_class",
        "source_id",
        "record_id",
        "warning",
        "blocker",
    }
    for path in paths.values():
        header = set(Path(path).read_text(encoding="utf-8").splitlines()[0].split(","))
        assert required <= header


def test_grid_runner_does_not_change_empirical_feedstock_output():
    before = dict(load_feedstock_proxies())
    run_dynamic_protein_scenario_grid(DynamicProteinScenarioConfig())
    assert dict(load_feedstock_proxies()) == before
