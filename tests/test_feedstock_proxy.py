import csv
import json

import pytest

from Greenhub.scientific_equations import moisture_wet_basis_from_total_solids
from Greenhub.feedstock_proxy import (
    feedstock_proxy_resolution_candidates,
    load_feedstock_proxies,
    summarize_feedstock_proxy_evidence,
)
from Greenhub.feedstock_resolution import (
    FeedstockResolutionMode,
    MeasuredFeedstockOverride,
    build_feedstock_equation_implementation_queue,
    build_feedstock_evidence_pool,
    can_convert_feedstock_unit,
    default_feedstock_resolution_mode,
    derive_feedstock_report_values,
    describe_feedstock_resolution_modes,
    describe_feedstock_conversion_policy,
    expected_feedstock_basis,
    expected_feedstock_equation_mapping,
    feedstock_resolution_to_report_rows,
    preview_feedstock_resolution_gates,
    resolve_feedstock_candidate,
    resolve_feedstock_candidates_for_grid,
    resolve_with_measured_overrides,
    summarize_feedstock_resolution_gates,
    validate_feedstock_candidate_basis,
    validate_feedstock_equation_mapping,
    validate_measured_feedstock_overrides,
    write_feedstock_resolution_report,
)
from Greenhub.dynamic_feedstock import (
    DEFAULT_MEASURED_TEMPLATE,
    FIRST_DYNAMIC_FEEDSTOCK_FIELDS,
    build_dynamic_feedstock_input_bundle,
    build_dynamic_feedstock_pools,
    default_literature_pool_policy,
    dynamic_bundle_to_feed_profile_row,
    dynamic_bundles_to_feed_profile_preview,
    load_measured_feedstock_csv,
    solve_feedstock_dynamic_preview,
    write_dynamic_feedstock_preview_reports,
)
from Greenhub.mechanical_separation import (
    CURRENT_PARTITION_SOURCE_ID,
    CURRENT_PARTITION_SPECIES,
    CURRENT_PRESS_BOUNDARY,
    TotalProteinPartitionFallbackPolicy,
    WaterClosureCorrectionPolicy,
    build_conservative_press_partition_policy,
    default_mechanical_separation_policy,
    load_press_partition_evidence,
    preview_mechanical_separation,
    summarize_press_partition_evidence,
)
from Greenhub.dynamic_press import (
    build_dynamic_press_preview_bundle,
    build_extraction_ready_stream_preview,
    write_dynamic_press_preview_reports,
)


def test_loader_prefers_new_direct_roadside_rows_over_old_overlap():
    proxies = load_feedstock_proxies()

    ash = proxies["ash_dry_basis"]
    assert ash.source_file == "roadside_grass_composition_scientific.csv"
    assert ash.parameter_id == "fresh_ash"
    assert ash.value == 0.179

    nitrogen = proxies["nitrogen_dry_basis"]
    assert nitrogen.source_file == "roadside_grass_composition_scientific.csv"
    assert nitrogen.parameter_id == "fresh_nitrogen"
    assert nitrogen.value == 0.021


def test_missing_indirect_and_reference_rows_are_not_active_values():
    proxies = load_feedstock_proxies()

    assert "glf_density" not in proxies
    assert "solid_true_protein" not in proxies
    assert "bmp_buswell" not in proxies
    assert "bmp_boyle" not in proxies

    assert proxies["total_protein_dry_basis"].parameter_id == "protein"
    assert proxies["extractive_sugars_dry_basis"].parameter_id == "extractive_sugars"


def test_active_proxy_output_unchanged_by_evidence_candidates():
    proxies = load_feedstock_proxies()
    before = dict(proxies)
    feedstock_proxy_resolution_candidates()
    after = dict(load_feedstock_proxies())

    assert after == before


def test_direct_literature_proxy_candidates_are_separate_from_active_output():
    candidates = feedstock_proxy_resolution_candidates()
    fresh_ash = next(item for item in candidates if item.parameter_id == "fresh_ash")

    assert fresh_ash.readiness_category == "direct_literature_proxy"
    assert fresh_ash.can_activate_by_default is True
    assert load_feedstock_proxies()["ash_dry_basis"].parameter_id == "fresh_ash"


def test_indirect_extended_candidates_are_sensitivity_only():
    candidates = feedstock_proxy_resolution_candidates()
    cellulose = next(item for item in candidates if item.parameter_id == "solid_cellulose_proxy_lolium_2025")

    assert cellulose.readiness_category == "sensitivity_only_indirect_proxy"
    assert cellulose.requires_user_selection is True
    assert cellulose.can_activate_by_default is False


def test_missing_rows_are_blocked_missing():
    candidates = feedstock_proxy_resolution_candidates()
    true_protein = next(
        item
        for item in candidates
        if item.parameter_id == "solid_true_protein"
        and item.source_file == "roadside_grass_missing_proxy_candidates_extended.csv"
    )

    assert true_protein.readiness_category == "blocked_missing"
    assert true_protein.value is None


def test_summary_helper_returns_json_safe_category_counts():
    summary = summarize_feedstock_proxy_evidence()

    assert summary
    assert all(set(item) == {"category", "count", "source_file"} for item in summary)
    assert all(isinstance(item["category"], str) for item in summary)
    assert all(isinstance(item["source_file"], str) for item in summary)
    assert all(isinstance(item["count"], int) for item in summary)
    json.dumps(summary)


def test_time_aware_resolution_preview_keeps_direct_rows_report_only():
    previews = preview_feedstock_resolution_gates()
    ash = next(item for item in previews if item.parameter_id == "fresh_ash")

    assert ash.category == "resolvable_now"
    assert ash.time_basis == "static"
    assert ash.no_interpolation is True
    assert ash.applicable_months == ("2026-05", "2026-06", "2026-07", "2026-08", "2026-09", "2026-10", "2026-11")


def test_time_aware_resolution_summary_is_json_safe_and_blocks_unmapped_time():
    previews = preview_feedstock_resolution_gates(start_date="2026-01-01", end_date="2026-02-28")
    spring_total_solids = next(item for item in previews if item.parameter_id == "SEAS-CZ-SP-TS")

    assert spring_total_solids.category == "blocked_time_mapping"
    assert spring_total_solids.time_basis == "monthly"
    assert spring_total_solids.applicable_months == ()

    summary = summarize_feedstock_resolution_gates(previews)
    assert all(set(item) == {"category", "count", "canonical_field", "source_file"} for item in summary)
    json.dumps(summary)


def test_feedstock_resolution_report_writer_outputs_csv_and_markdown(tmp_path):
    csv_path = tmp_path / "feedstock_resolution_gates.csv"
    markdown_path = tmp_path / "feedstock_resolution_readiness.md"

    out = write_feedstock_resolution_report(csv_path=csv_path, markdown_path=markdown_path)

    assert out["csv_path"] == str(csv_path)
    assert out["markdown_path"] == str(markdown_path)
    assert csv_path.exists()
    assert markdown_path.exists()
    csv_text = csv_path.read_text(encoding="utf-8")
    markdown_text = markdown_path.read_text(encoding="utf-8")
    assert "blocked_missing" in csv_text
    assert "requires_user_selection" in csv_text
    assert "blocked_missing" in markdown_text
    assert "requires_user_selection" in markdown_text


def test_report_only_candidate_resolver_selects_direct_field():
    resolved = resolve_feedstock_candidate("ash_dry_basis", "2026-07")

    assert resolved.resolution_status == "direct_literature_proxy"
    assert resolved.selected_parameter_id == "fresh_ash"
    assert resolved.value == 0.179
    assert resolved.provenance["mode"] == "report_only"


def test_indirect_candidate_requires_explicit_allow_indirect():
    blocked = resolve_feedstock_candidate("cellulose_dry_basis", "2026-07")
    allowed = resolve_feedstock_candidate("cellulose_dry_basis", "2026-07", allow_indirect=True)

    assert blocked.resolution_status == "requires_user_selection"
    assert blocked.selected_parameter_id is None
    assert blocked.value is None
    assert allowed.resolution_status == "sensitivity_only_indirect_proxy"
    assert allowed.selected_parameter_id
    assert allowed.requires_user_selection is True


def test_missing_candidate_resolution_returns_blocked():
    resolved = resolve_feedstock_candidate("true_protein_dry_basis", "2026-07")

    assert resolved.resolution_status == "blocked_missing"
    assert resolved.blocked_reason == "missing_value"
    assert resolved.selected_parameter_id is None
    assert resolved.value is None


def test_grid_candidate_resolver_returns_each_field_time_combination():
    records = resolve_feedstock_candidates_for_grid(
        ["ash_dry_basis", "true_protein_dry_basis"],
        ["2026-06", "2026-07"],
    )

    assert len(records) == 4
    assert {(item.canonical_field, item.time_label) for item in records} == {
        ("ash_dry_basis", "2026-06"),
        ("ash_dry_basis", "2026-07"),
        ("true_protein_dry_basis", "2026-06"),
        ("true_protein_dry_basis", "2026-07"),
    }


def test_measured_override_outranks_direct_literature_proxy():
    override = MeasuredFeedstockOverride(
        canonical_field="ash_dry_basis",
        value=0.2,
        unit="kg/kg dry matter",
        source_id="GH-LAB-001",
        lab_reference="lab-report-1",
    )
    resolved = resolve_with_measured_overrides("ash_dry_basis", "2026-07", [override])

    assert resolved.resolution_status == "measured_project_data"
    assert resolved.value == 0.2
    assert resolved.selected_parameter_id == "measured:ash_dry_basis"


def test_measured_override_wrong_unit_requires_basis_conversion():
    override = MeasuredFeedstockOverride(
        canonical_field="ash_dry_basis",
        value=20.0,
        unit="percent dry matter",
        source_id="GH-LAB-001",
    )
    validation = validate_measured_feedstock_overrides([override])[0]
    resolved = resolve_with_measured_overrides("ash_dry_basis", "2026-07", [override])

    assert validation["resolution_status"] == "requires_basis_conversion"
    assert resolved.resolution_status == "requires_basis_conversion"
    assert resolved.blocked_reason == "unit_mismatch"
    assert resolved.value is None


def test_measured_override_missing_metadata_is_flagged():
    override = MeasuredFeedstockOverride(
        canonical_field="ash_dry_basis",
        value=0.2,
        unit="kg/kg dry matter",
    )
    validation = validate_measured_feedstock_overrides([override])[0]
    resolved = resolve_with_measured_overrides("ash_dry_basis", "2026-07", [override])

    assert "missing_source_or_lab_reference" in validation["warnings"]
    assert "missing_source_or_lab_reference" in resolved.provenance["warnings"]


def test_report_only_conversion_never_returns_model_overrides_key():
    records = [
        resolve_feedstock_candidate("ash_dry_basis", "2026-07"),
        resolve_feedstock_candidate("true_protein_dry_basis", "2026-07"),
    ]
    rows = feedstock_resolution_to_report_rows(records)

    assert rows
    assert all("model_overrides" not in row for row in rows)


def test_default_feedstock_resolver_mode_is_report_only_and_empirical_safe():
    resolved = resolve_feedstock_candidate("ash_dry_basis", "2026-07")
    rows = feedstock_resolution_to_report_rows([resolved])

    assert FeedstockResolutionMode.EMPIRICAL_EXISTING == "empirical_existing"
    assert FeedstockResolutionMode.DYNAMIC_TIME_AWARE_REPORT_ONLY == "dynamic_time_aware_report_only"
    assert resolved.provenance["mode"] == "report_only"
    assert all("model_overrides" not in row for row in rows)


def test_feedstock_resolution_modes_keep_dynamic_active_future_blocked():
    modes = describe_feedstock_resolution_modes()

    assert default_feedstock_resolution_mode() == FeedstockResolutionMode.EMPIRICAL_EXISTING
    future = modes[FeedstockResolutionMode.DYNAMIC_TIME_AWARE_ACTIVE_FUTURE]
    assert future["status"] == "blocked_future_mode"
    assert future["calculation_ready"] is False
    assert future["selectable_for_calculations"] is False


def test_feedstock_basis_gate_exact_expected_unit_passes():
    expectation = expected_feedstock_basis("ash_dry_basis")
    result = validate_feedstock_candidate_basis("ash_dry_basis", "kg/kg dry matter", value=0.179)

    assert expectation["expected_unit"] == "kg/kg dry matter"
    assert result["basis_status"] == "basis_ok"
    assert result["requires_basis_conversion"] is False
    assert result["value"] == 0.179


def test_feedstock_basis_gate_compatible_non_exact_unit_requires_conversion():
    result = validate_feedstock_candidate_basis("ash_dry_basis", "percent dry matter", value=17.9)

    assert result["basis_status"] == "requires_basis_conversion"
    assert result["requires_basis_conversion"] is True
    assert result["value"] == 17.9


def test_feedstock_basis_gate_wrong_basis_blocks_calculation_readiness():
    result = validate_feedstock_candidate_basis("ash_dry_basis", "kg/kg wet biomass", value=0.1)

    assert result["basis_status"] == "blocked_wrong_basis"
    assert result["blocked_reason"] == "wrong_or_unclear_basis"
    assert result["value"] == 0.1


def test_feedstock_resolver_records_basis_metadata_without_numeric_conversion():
    result = validate_feedstock_candidate_basis("volatile_solids_dry_basis", "kg/kg dry matter", value=0.67)
    resolved = resolve_feedstock_candidate("ash_dry_basis", "2026-07")

    assert result["basis_status"] == "requires_basis_conversion"
    assert result["value"] == 0.67
    assert resolved.basis_status == "basis_ok"
    assert resolved.expected_unit == "kg/kg dry matter"
    assert resolved.observed_unit == "kg/kg dry matter"
    assert resolved.requires_basis_conversion is False


def test_feedstock_conversion_policy_exact_unit_allowed_without_conversion():
    policy = describe_feedstock_conversion_policy()
    result = can_convert_feedstock_unit("kg/kg dry matter", "kg/kg dry matter", "ash_dry_basis")

    assert policy["automatic_numeric_conversion"] is False
    assert result["conversion_policy_status"] == "allowed_exact_unit"
    assert result["conversion_required"] is False
    assert result["conversion_allowed"] is True


def test_feedstock_conversion_policy_percent_requires_explicit_conversion():
    result = can_convert_feedstock_unit("percent dry matter", "kg/kg dry matter", "ash_dry_basis")

    assert result["conversion_policy_status"] == "possible_but_requires_explicit_conversion"
    assert result["conversion_required"] is True
    assert result["conversion_allowed"] is False


def test_feedstock_conversion_policy_range_values_keep_min_max_not_midpoint():
    result = can_convert_feedstock_unit(
        "g/kg dry matter",
        "kg/kg dry matter",
        "total_protein_dry_basis",
        value_min=100.0,
        value_max=150.0,
    )

    assert result["conversion_policy_status"] == "possible_but_requires_explicit_conversion"
    assert result["preserves_range_values"] is True
    assert "no midpoint" in result["conversion_note"]


def test_feedstock_conversion_policy_unknown_unit_is_blocked():
    result = can_convert_feedstock_unit("bushels/acre", "kg/kg dry matter", "ash_dry_basis")

    assert result["conversion_policy_status"] == "blocked_unknown_unit"
    assert result["conversion_required"] is False
    assert result["conversion_allowed"] is False


def test_feedstock_resolver_record_includes_conversion_policy_metadata():
    resolved = resolve_feedstock_candidate("ash_dry_basis", "2026-07")

    assert resolved.conversion_policy_status == "allowed_exact_unit"
    assert resolved.conversion_required is False
    assert resolved.conversion_allowed is True
    assert resolved.conversion_note


def test_feedstock_equation_mapping_observed_ash_and_moisture_need_no_equation():
    candidates = feedstock_proxy_resolution_candidates()
    ash = next(item for item in candidates if item.parameter_id == "fresh_ash")
    moisture = next(item for item in candidates if item.parameter_id == "road_verge_moisture_as_received")

    assert validate_feedstock_equation_mapping(ash)["equation_mapping_status"] == "no_equation_required_observed_value"
    assert validate_feedstock_equation_mapping(moisture)["equation_mapping_status"] == "no_equation_required_observed_value"


def test_feedstock_equation_mapping_bmp_stays_reference_only():
    mapping = expected_feedstock_equation_mapping()

    assert mapping["bmp_buswell"]["equation_mapping_status"] == "equation_available_reference_only"
    assert mapping["bmp_buswell"]["equation_id"] == ""


def test_feedstock_equation_mapping_missing_dynamic_field_is_blocked():
    resolved = resolve_feedstock_candidate("solid_ph", "2026-07")

    assert resolved.resolution_status == "blocked_missing"
    assert resolved.equation_mapping_status == "blocked_missing_inputs"
    assert resolved.equation_id == ""


def test_feedstock_resolver_rows_include_equation_mapping_metadata():
    rows = feedstock_resolution_to_report_rows([resolve_feedstock_candidate("ash_dry_basis", "2026-07")])

    assert rows[0]["equation_mapping_status"] == "no_equation_required_observed_value"
    assert "equation_id" in rows[0]
    assert rows[0]["equation_note"]


def test_feedstock_equation_implementation_queue_is_report_only(tmp_path):
    queue = build_feedstock_equation_implementation_queue(tmp_path / "feedstock_equation_implementation_queue.md")
    by_id = {item["equation_id"]: item for item in queue}

    assert "fresh_ash" not in {item["output_field"] for item in queue}
    assert by_id["EQ-CALC-001"]["implementation_status"] == "implemented_typed"
    assert by_id["EQ-CALC-001"]["activation_status"] == "report_only"
    assert by_id["EQ003"]["activation_status"] == "reference_only"
    assert by_id["EQ003"]["implementation_status"] != "implemented_typed"
    assert by_id["EQ_CP_MASS_WEIGHTED"]["implementation_status"] == "blocked_missing_inputs"
    assert any(item["implementation_status"] == "blocked_dynamic_model_scope" for item in queue)


def test_eq_calc_001_moisture_from_total_solids_identity():
    assert moisture_wet_basis_from_total_solids(0.38) == pytest.approx(0.62)


def test_eq_calc_001_rejects_invalid_total_solids():
    with pytest.raises(ValueError):
        moisture_wet_basis_from_total_solids(-0.01)
    with pytest.raises(ValueError):
        moisture_wet_basis_from_total_solids(1.01)


def test_derive_feedstock_report_values_adds_eq_calc_001_when_allowed():
    rows = derive_feedstock_report_values(allow_derived=True)
    derived = next(item for item in rows if item["status"] == "derived_report_only")

    assert derived["canonical_field"] == "moisture_wet_basis"
    assert derived["value"] == pytest.approx(0.62)
    assert derived["unit"] == "kg water/kg wet biomass"
    assert derived["equation_id"] == "EQ-CALC-001"
    assert derived["source_parameter_id"] == "COMP-CZ-SP-TS"
    assert derived["activation_status"] == "report_only"


def test_derive_feedstock_report_values_does_not_overwrite_direct_moisture_by_default():
    default_rows = derive_feedstock_report_values()
    derived_rows = derive_feedstock_report_values(allow_derived=True)

    assert not any(item["status"] == "derived_report_only" for item in default_rows)
    observed_moisture = [
        item
        for item in derived_rows
        if item["canonical_field"] == "moisture_wet_basis" and item["status"] != "derived_report_only"
    ]
    derived_moisture = [
        item
        for item in derived_rows
        if item["canonical_field"] == "moisture_wet_basis" and item["status"] == "derived_report_only"
    ]
    assert observed_moisture
    assert derived_moisture


def test_derive_feedstock_report_values_includes_eq_calc_001_provenance():
    rows = derive_feedstock_report_values(allow_derived=True)
    derived = next(item for item in rows if item["status"] == "derived_report_only")

    assert derived["provenance"]["mode"] == "report_only"
    assert derived["provenance"]["source_field"] == "total_solids_wet_basis"
    assert derived["provenance"]["observed_moisture_overwritten"] is False


def test_feedstock_evidence_pool_direct_literature_confidence_exceeds_indirect_proxy():
    pool = build_feedstock_evidence_pool()
    direct = next(item for item in pool if item["parameter_id"] == "fresh_ash")
    indirect = next(item for item in pool if item["parameter_id"] == "solid_cellulose_proxy_lolium_2025")

    assert direct["certainty_class"] == "direct_literature"
    assert indirect["certainty_class"] == "indirect_proxy"
    assert direct["confidence_score"] > indirect["confidence_score"]


def test_feedstock_evidence_pool_includes_missing_rows_as_blocked_report_only():
    pool = build_feedstock_evidence_pool()
    missing = next(
        item
        for item in pool
        if item["parameter_id"] == "solid_true_protein"
        and item["certainty_class"] == "missing"
    )

    assert missing["confidence_score"] == 0.0
    assert missing["use_status"] == "blocked_report_only"
    assert missing["requires_user_confirmation"] is True


def test_feedstock_evidence_pool_user_override_confirmation_depends_on_source():
    unsourced = MeasuredFeedstockOverride("ash_dry_basis", 0.2, "kg/kg dry matter")
    sourced = MeasuredFeedstockOverride("ash_dry_basis", 0.21, "kg/kg dry matter", source_id="user-note-1")
    pool = build_feedstock_evidence_pool(user_overrides=[unsourced, sourced])
    overrides = [item for item in pool if item["certainty_class"] == "user_override"]

    assert len(overrides) == 2
    assert any(item["confidence_score"] == 0.5 and item["requires_user_confirmation"] is True for item in overrides)
    assert any(item["confidence_score"] == 0.6 and item["requires_user_confirmation"] is False for item in overrides)


def test_dynamic_feedstock_preview_is_typed_and_does_not_change_empirical_proxies():
    before = dict(load_feedstock_proxies())
    result = solve_feedstock_dynamic_preview(
        start_date="2026-05-01",
        end_date="2026-07-31",
        time_step="monthly",
    )

    assert len(result.bundles) == 3
    assert all(len(bundle.fields) == len(FIRST_DYNAMIC_FEEDSTOCK_FIELDS) for bundle in result.bundles)
    assert result.calculation_ready is False
    assert result.activation_status == "dynamic_preparation_report_only"
    assert "model_overrides" not in result.to_dict()
    assert dict(load_feedstock_proxies()) == before
    json.dumps(result.to_dict())


def test_dynamic_feedstock_priority_measured_then_explicit_user_then_literature():
    measured = MeasuredFeedstockOverride(
        "ash_dry_basis",
        0.2,
        "kg/kg dry matter",
        source_id="lab-2026-ash",
    )
    user = MeasuredFeedstockOverride(
        "ash_dry_basis",
        0.21,
        "kg/kg dry matter",
        source_id="expert-2026-ash",
        notes="Explicit scenario override for preview testing.",
    )

    measured_bundle = build_dynamic_feedstock_input_bundle(
        "2026-07",
        measured_values=[measured],
        user_overrides=[user],
        allow_user_overrides=True,
    )
    measured_ash = next(item for item in measured_bundle.fields if item.canonical_field == "ash_dry_basis")
    assert measured_ash.value == pytest.approx(0.2)
    assert measured_ash.certainty_class == "measured_project"

    user_bundle = build_dynamic_feedstock_input_bundle(
        "2026-07",
        user_overrides=[user],
        allow_user_overrides=True,
    )
    user_ash = next(item for item in user_bundle.fields if item.canonical_field == "ash_dry_basis")
    assert user_ash.value == pytest.approx(0.21)
    assert user_ash.certainty_class == "user_override"

    literature_bundle = build_dynamic_feedstock_input_bundle("2026-07", user_overrides=[user])
    literature_ash = next(item for item in literature_bundle.fields if item.canonical_field == "ash_dry_basis")
    assert literature_ash.value == pytest.approx(0.179)
    assert literature_ash.certainty_class == "direct_literature"
    assert "2026-07:ash_dry_basis:user_override_not_explicitly_enabled" in literature_bundle.warnings


def test_dynamic_feedstock_time_specific_measurement_does_not_leak_to_other_steps():
    measured = MeasuredFeedstockOverride(
        "bulk_density",
        250.0,
        "kg/m3",
        time_label="2026-06",
        lab_reference="density-run-06",
    )
    may = build_dynamic_feedstock_input_bundle("2026-05", measured_values=[measured])
    june = build_dynamic_feedstock_input_bundle("2026-06", measured_values=[measured])
    may_density = next(item for item in may.fields if item.canonical_field == "bulk_density")
    june_density = next(item for item in june.fields if item.canonical_field == "bulk_density")

    assert may_density.certainty_class == "direct_literature"
    assert june_density.certainty_class == "measured_project"
    assert june_density.value == pytest.approx(250.0)


def test_dynamic_feedstock_report_writers_use_explicit_artifact_names(tmp_path):
    result = solve_feedstock_dynamic_preview(
        start_date="2026-05-01",
        end_date="2026-05-31",
    )
    artifacts = write_dynamic_feedstock_preview_reports(
        result,
        csv_path=tmp_path / "dynamic_feedstock_preview.csv",
        markdown_path=tmp_path / "dynamic_feedstock_solver_preview.md",
    )

    assert artifacts == {
        "csv": "dynamic_feedstock_preview.csv",
        "markdown": "dynamic_feedstock_solver_preview.md",
    }
    assert (tmp_path / "dynamic_feedstock_preview.csv").is_file()
    markdown = (tmp_path / "dynamic_feedstock_solver_preview.md").read_text(encoding="utf-8")
    assert "does not activate dynamic calculation mode" in markdown
    assert "Range midpoint calculation: disabled" in markdown


def test_dynamic_feedstock_reconciles_literature_moisture_ts_conflict_with_audit_trail():
    bundle = build_dynamic_feedstock_input_bundle("2026-05")
    moisture = next(item for item in bundle.fields if item.canonical_field == "moisture_wet_basis")
    solids = next(item for item in bundle.fields if item.canonical_field == "total_solids_wet_basis")

    assert bundle.reconciliation_status == "reconciled_conflict"
    assert bundle.authoritative_field == "total_solids_wet_basis"
    assert bundle.reconciled_fields == ("moisture_wet_basis",)
    assert bundle.conflict_count == 1
    assert solids.value == pytest.approx(0.38)
    assert moisture.value == pytest.approx(0.62)
    assert moisture.certainty_class == "derived_from_literature"
    reconciliation = moisture.provenance["reconciliation"]
    assert reconciliation["original_counterpart_value"] == pytest.approx(0.76)
    assert reconciliation["silent_overwrite"] is False
    assert bundle.reconciliation_conflicts[0]["original_conflicting_value"] == pytest.approx(0.76)


def test_dynamic_feedstock_measured_moisture_wins_and_derives_ts_in_preview_only():
    measured = MeasuredFeedstockOverride(
        "moisture_wet_basis",
        0.8,
        "kg water/kg wet biomass",
        time_label="2026-06",
        lab_reference="moisture-lab-06",
    )
    bundle = build_dynamic_feedstock_input_bundle("2026-06", measured_values=[measured])
    moisture = next(item for item in bundle.fields if item.canonical_field == "moisture_wet_basis")
    solids = next(item for item in bundle.fields if item.canonical_field == "total_solids_wet_basis")

    assert bundle.authoritative_field == "moisture_wet_basis"
    assert moisture.certainty_class == "measured_project"
    assert solids.value == pytest.approx(0.2)
    assert solids.certainty_class == "derived_from_measured_project"
    assert solids.provenance["reconciliation"]["original_counterpart_value"] == pytest.approx(0.2583)
    assert bundle.calculation_ready is False
    assert "model_overrides" not in bundle.to_dict()


def test_dynamic_feedstock_accepts_consistent_measured_moisture_ts_pair():
    measured = [
        MeasuredFeedstockOverride(
            "moisture_wet_basis",
            0.8,
            "kg water/kg wet biomass",
            source_id="measurement-set-1",
        ),
        MeasuredFeedstockOverride(
            "total_solids_wet_basis",
            0.2,
            "kg/kg wet feed",
            source_id="measurement-set-1",
        ),
    ]
    bundle = build_dynamic_feedstock_input_bundle("2026-06", measured_values=measured)

    assert bundle.reconciliation_status == "consistent"
    assert bundle.reconciled_fields == ()
    assert bundle.conflict_count == 0
    assert bundle.authoritative_field == ""


def test_measured_feedstock_csv_loader_skips_examples_and_reports_invalid_rows(tmp_path):
    path = tmp_path / "measured.csv"
    path.write_text(
        "record_id,canonical_field,value,unit,time_label,start_date,end_date,sample_id,sample_location,feedstock,material_state,measurement_method,lab_reference,source_id,measured_date,data_status,notes\n"
        "EXAMPLE,ash_dry_basis,,kg/kg dry matter,YYYY-MM,,,,,,,,LAB,SOURCE,,example_do_not_use,template only\n"
        "ASH-06,ash_dry_basis,0.2,kg/kg dry matter,2026-06,,,S-06,intake,roadside grass,fresh,gravimetric,LAB-06,,2026-06-15,measured_project,validated result\n"
        "BAD-N,nitrogen_dry_basis,not-a-number,kg/kg dry matter,2026-06,,,,,,,,,,,measured_project,invalid result\n",
        encoding="utf-8",
    )

    loaded = load_measured_feedstock_csv(path)
    assert len(loaded.records) == 1
    assert loaded.example_rows_skipped == 1
    assert len(loaded.invalid_rows) == 1
    assert "missing_or_non_numeric_value" in loaded.invalid_rows[0].reasons
    assert "missing_source_id_or_lab_reference" in loaded.invalid_rows[0].reasons

    result = solve_feedstock_dynamic_preview(
        start_date="2026-06-01",
        end_date="2026-06-30",
        measured_data_path=path,
    )
    ash = next(item for item in result.bundles[0].fields if item.canonical_field == "ash_dry_basis")
    assert ash.value == pytest.approx(0.2)
    assert ash.certainty_class == "measured_project"
    assert result.measured_data_status["usable_rows"] == 1
    assert result.measured_data_status["invalid_rows"] == 1


def test_measured_feedstock_template_contains_no_usable_example_values():
    loaded = load_measured_feedstock_csv(DEFAULT_MEASURED_TEMPLATE)

    assert loaded.records == ()
    assert loaded.invalid_rows == ()
    assert loaded.example_rows_skipped == 1


def test_dynamic_adapter_maps_moisture_and_reviewed_ash_to_feed_profile_fractions():
    bundle = build_dynamic_feedstock_input_bundle("2026-05")
    row = dynamic_bundle_to_feed_profile_row(bundle)

    assert row.time_label == "2026-05"
    assert row.moisture_fraction == pytest.approx(0.62)
    assert row.component_mass_fractions == {"Ash": pytest.approx(0.179 * 0.38)}
    assert "Water" not in row.component_mass_fractions
    assert row.provenance["normal_simulation_integration"] is False
    assert "model_overrides" not in row.to_dict()


def test_dynamic_adapter_keeps_unsupported_aggregate_fields_as_metadata_with_warnings():
    row = dynamic_bundle_to_feed_profile_row(build_dynamic_feedstock_input_bundle("2026-06"))

    expected_unmapped = {
        "total_solids_wet_basis",
        "volatile_solids_dry_basis",
        "carbon_dry_basis",
        "nitrogen_dry_basis",
        "sulfur_dry_basis",
        "bulk_density",
        "total_protein_dry_basis",
        "extractive_sugars_dry_basis",
    }
    assert set(row.unmapped_fields) == expected_unmapped
    assert expected_unmapped <= set(row.metadata_fields)
    assert any("total_protein_dry_basis" in warning for warning in row.warnings)
    assert any("extractive_sugars_dry_basis" in warning for warning in row.warnings)
    assert any("carbon_dry_basis" in warning for warning in row.warnings)


def test_dynamic_adapter_cannot_drive_without_explicit_protein_and_sugar_mappings():
    bundle = build_dynamic_feedstock_input_bundle("2026-07")
    default_row = dynamic_bundle_to_feed_profile_row(bundle)
    explicit_row = dynamic_bundle_to_feed_profile_row(
        bundle,
        component_mappings={
            "total_protein_dry_basis": {"SolubleProtein": 0.5, "SuspendedProtein": 0.5},
            "extractive_sugars_dry_basis": {"Glucose": 1.0},
        },
    )

    assert default_row.can_drive_simulation is False
    assert set(default_row.provenance["missing_required_component_mappings"]) == {
        "total_protein_dry_basis",
        "extractive_sugars_dry_basis",
    }
    assert explicit_row.can_drive_simulation is True
    assert explicit_row.component_mass_fractions["SolubleProtein"] == pytest.approx(0.107 * 0.2583 * 0.5)
    assert explicit_row.component_mass_fractions["SuspendedProtein"] == pytest.approx(0.107 * 0.2583 * 0.5)
    assert explicit_row.component_mass_fractions["Glucose"] == pytest.approx(0.072 * 0.2583)


def test_dynamic_adapter_preview_does_not_change_empirical_proxy_output():
    before = dict(load_feedstock_proxies())
    result = solve_feedstock_dynamic_preview(
        start_date="2026-05-01",
        end_date="2026-07-31",
    )
    rows = dynamic_bundles_to_feed_profile_preview(result.bundles)

    assert len(rows) == 3
    assert all(row.can_drive_simulation is False for row in rows)
    assert dict(load_feedstock_proxies()) == before


def test_observed_total_solids_does_not_require_equation_mapping():
    candidate = next(
        item
        for item in feedstock_proxy_resolution_candidates()
        if item.parameter_id == "COMP-CZ-SP-TS"
    )

    mapping = validate_feedstock_equation_mapping(candidate)
    assert mapping["equation_mapping_status"] == "no_equation_required_observed_value"


def test_whole_feed_pooling_is_opt_in_and_default_adapter_is_unchanged():
    bundle = build_dynamic_feedstock_input_bundle("2026-05")
    default_row = dynamic_bundle_to_feed_profile_row(bundle)
    pooled_row = dynamic_bundle_to_feed_profile_row(
        bundle,
        pool_policy=default_literature_pool_policy(),
    )

    assert default_row.component_mass_fractions == {"Ash": pytest.approx(0.179 * 0.38)}
    assert "whole_feed_pooling" not in default_row.metadata_fields
    assert set(pooled_row.component_mass_fractions) == {
        "Ash",
        "Cellulose",
        "Fructose",
        "Glucose",
        "Hemicellulose",
        "Lignin",
        "SolubleProtein",
        "Sucrose",
        "SuspendedProtein",
    }
    assert pooled_row.can_drive_simulation is False


def test_whole_feed_pooling_splits_total_protein_equally_on_wet_basis():
    bundle = build_dynamic_feedstock_input_bundle("2026-05")
    pools = build_dynamic_feedstock_pools(bundle, default_literature_pool_policy())
    total_protein_wet = 0.38 * 0.107

    assert pools.soluble_protein_wet_fraction == pytest.approx(total_protein_wet * 0.5)
    assert pools.insoluble_protein_wet_fraction == pytest.approx(total_protein_wet * 0.5)
    assert pools.soluble_protein_wet_fraction + pools.insoluble_protein_wet_fraction == pytest.approx(
        total_protein_wet
    )
    assert pools.component_mass_fractions["SolubleProtein"] == pytest.approx(total_protein_wet * 0.5)
    assert pools.component_mass_fractions["SuspendedProtein"] == pytest.approx(total_protein_wet * 0.5)


def test_whole_feed_sugar_means_are_normalized_and_ranges_preserved():
    policy = default_literature_pool_policy()
    sugar = policy.wsc_sugar_pool

    assert sum(item.default_fraction for item in sugar.values()) == pytest.approx(1.0)
    assert sugar["fructan"].default_fraction == pytest.approx(0.60 / 0.975)
    assert sugar["sucrose"].default_fraction == pytest.approx(0.25 / 0.975)
    assert sugar["hexose"].default_fraction == pytest.approx(0.125 / 0.975)
    assert (sugar["fructan"].low_fraction, sugar["fructan"].high_fraction) == (0.50, 0.70)
    assert (sugar["sucrose"].low_fraction, sugar["sucrose"].high_fraction) == (0.20, 0.30)
    assert (sugar["hexose"].low_fraction, sugar["hexose"].high_fraction) == (0.10, 0.15)
    assert "normalized to 1.0" in sugar["fructan"].normalization_note


def test_whole_feed_pooling_maps_hexose_to_glucose_and_fructose():
    pools = build_dynamic_feedstock_pools(
        build_dynamic_feedstock_input_bundle("2026-05"),
        default_literature_pool_policy(),
    )

    assert pools.component_mass_fractions["Glucose"] == pytest.approx(pools.hexose_wet_fraction * 0.5)
    assert pools.component_mass_fractions["Fructose"] == pytest.approx(pools.hexose_wet_fraction * 0.5)
    assert (
        pools.component_mass_fractions["Glucose"] + pools.component_mass_fractions["Fructose"]
    ) == pytest.approx(pools.hexose_wet_fraction)
    assert "hexose_subtotal" in pools.metadata_only_pools
    assert "hexose_split_50_50_glucose_fructose_assumption" in " ".join(pools.warnings)


def test_whole_feed_fiber_means_are_normalized_and_ranges_preserved():
    policy = default_literature_pool_policy()
    fiber = policy.fiber_subpool

    assert sum(item.default_fraction for item in fiber.values()) == pytest.approx(1.0)
    assert fiber["hemicellulose"].default_fraction == pytest.approx(0.20 / 0.48)
    assert fiber["cellulose"].default_fraction == pytest.approx(0.24 / 0.48)
    assert fiber["lignin"].default_fraction == pytest.approx(0.04 / 0.48)
    assert (fiber["hemicellulose"].low_fraction, fiber["hemicellulose"].high_fraction) == (0.15, 0.25)
    assert (fiber["cellulose"].low_fraction, fiber["cellulose"].high_fraction) == (0.18, 0.30)
    assert (fiber["lignin"].low_fraction, fiber["lignin"].high_fraction) == (0.02, 0.06)
    assert "representative metadata only" in fiber["lignin"].formula_surrogate


def test_whole_feed_pooling_reports_nonnegative_residual_and_closes_wet_mass():
    pools = build_dynamic_feedstock_pools(
        build_dynamic_feedstock_input_bundle("2026-05"),
        default_literature_pool_policy(),
    )

    assert pools.residual_unallocated_dry_matter_wet_fraction == pytest.approx(
        0.38 * (1.0 - 0.179 - 0.107 - 0.072 - 0.525)
    )
    assert pools.residual_unallocated_dry_matter_wet_fraction >= 0.0
    assert pools.total_allocated_wet_fraction == pytest.approx(1.0)
    assert set(pools.metadata_only_pools) == {"fructan", "hexose_subtotal", "residual_unallocated_dry_matter"}
    assert "model_overrides" not in pools.to_dict()


def test_whole_feed_pooling_does_not_change_empirical_proxy_output():
    before = dict(load_feedstock_proxies())
    bundle = build_dynamic_feedstock_input_bundle("2026-07")
    policy = default_literature_pool_policy()
    build_dynamic_feedstock_pools(bundle, policy)
    dynamic_bundle_to_feed_profile_row(bundle, pool_policy=policy)

    assert dict(load_feedstock_proxies()) == before


def test_mechanical_separation_policy_uses_source_backed_closed_yields():
    policy = default_mechanical_separation_policy()

    assert policy.yield_sum == pytest.approx(1.0)
    assert {item.stream_name: item.fraction_of_feed for item in policy.yields} == {
        "press_cake": pytest.approx(0.395),
        "brown_juice": pytest.approx(0.568),
        "protein_concentrate": pytest.approx(0.037),
    }
    assert {item.source_id for item in policy.yields} == {"S03_SANTAMARIA_2020"}


def test_mechanical_separation_default_keeps_components_unmapped():
    pools = build_dynamic_feedstock_pools(
        build_dynamic_feedstock_input_bundle("2026-05"),
        default_literature_pool_policy(),
    )
    preview = preview_mechanical_separation(pools, default_mechanical_separation_policy())

    assert preview.stream_masses_kg_per_kg_feed == {
        "brown_juice": pytest.approx(0.568),
        "press_cake": pytest.approx(0.395),
        "protein_concentrate": pytest.approx(0.037),
    }
    assert "SolubleProtein" in preview.unmapped_components
    assert "SuspendedProtein" in preview.unmapped_components
    assert preview.can_drive_simulation is False
    assert preview.provenance["component_partition_status"] == "explicit_only"


def test_mechanical_separation_explicit_partition_conserves_component_mass():
    pools = build_dynamic_feedstock_pools(
        build_dynamic_feedstock_input_bundle("2026-05"),
        default_literature_pool_policy(),
    )
    preview = preview_mechanical_separation(
        pools,
        default_mechanical_separation_policy(),
        component_partition={
            "SolubleProtein": {"brown_juice": 0.8, "press_cake": 0.1, "protein_concentrate": 0.1},
            "SuspendedProtein": {"brown_juice": 0.1, "press_cake": 0.9, "protein_concentrate": 0.0},
        },
    )

    soluble_total = sum(
        stream.get("SolubleProtein", 0.0)
        for stream in preview.stream_component_masses_kg_per_kg_feed.values()
    )
    suspended_total = sum(
        stream.get("SuspendedProtein", 0.0)
        for stream in preview.stream_component_masses_kg_per_kg_feed.values()
    )

    assert soluble_total == pytest.approx(pools.component_mass_fractions["SolubleProtein"])
    assert suspended_total == pytest.approx(pools.component_mass_fractions["SuspendedProtein"])
    assert "SolubleProtein" not in preview.unmapped_components
    assert "SuspendedProtein" not in preview.unmapped_components


def test_press_partition_loader_reads_typed_records_and_flags_incompatible_boundaries():
    loaded = load_press_partition_evidence()
    water = next(record for record in loaded.records if record.record_id == "MSP_0125")
    generic_protein_range = next(record for record in loaded.records if record.record_id == "MSP_0130")

    assert loaded.source_file == "greenhub_mechanical_separation_component_partitioning.csv"
    assert water.partition_fraction == pytest.approx(0.313008)
    assert water.partition_fraction_raw == "0.313008"
    assert water.basis == "Water mass"
    assert water.feed_basis == "1 kg fresh biomass"
    assert water.transferability_class == "B_legume_or_green_biomass_proxy"
    assert water.confidence_class == "A"
    assert water.is_eligible is True
    assert generic_protein_range.partition_fraction is None
    assert "non_scalar_partition_fraction" in generic_protein_range.blocked_reasons
    assert "incompatible_process_boundary" in generic_protein_range.blocked_reasons


def test_source_evidence_preview_blocks_nonclosing_water_and_preserves_source_values():
    before = dict(load_feedstock_proxies())
    pools = build_dynamic_feedstock_pools(
        build_dynamic_feedstock_input_bundle("2026-05"),
        default_literature_pool_policy(),
    )
    evidence = load_press_partition_evidence()
    preview = preview_mechanical_separation(
        pools,
        default_mechanical_separation_policy(),
        partition_evidence=evidence,
    )

    assert "Water" in preview.unmapped_components
    assert {"MSP_0125", "MSP_0126", "MSP_0127"} <= set(preview.blocked_partition_record_ids)
    assert any("source_partition_closure_1.017012" in warning for warning in preview.warnings)
    assert preview.provenance["source_values_normalized"] is False
    assert preview.can_drive_simulation is False
    assert dict(load_feedstock_proxies()) == before


def test_explicit_press_preview_reports_zero_component_balance_residuals():
    pools = build_dynamic_feedstock_pools(
        build_dynamic_feedstock_input_bundle("2026-05"),
        default_literature_pool_policy(),
    )
    preview = preview_mechanical_separation(
        pools,
        default_mechanical_separation_policy(),
        component_partition={
            "SolubleProtein": {
                "press_cake": 0.1,
                "brown_juice": 0.8,
                "protein_concentrate": 0.1,
            }
        },
    )

    assert preview.component_mass_balance_residuals["SolubleProtein"] == pytest.approx(0.0)
    assert preview.unmapped_component_masses_kg_per_kg_feed["SuspendedProtein"] == pytest.approx(
        pools.component_mass_fractions["SuspendedProtein"]
    )
    assert "residual_unallocated_dry_matter" in preview.unmapped_pool_metadata


def test_press_evidence_summary_identifies_selected_water_closure_blocker():
    summary = summarize_press_partition_evidence(load_press_partition_evidence())
    water = next(item for item in summary.complete_triplets if item.component_or_pool == "water")

    assert water.complete_three_stream_triplet is True
    assert water.closure_sum == pytest.approx(1.017012)
    assert water.closure_within_tolerance is False
    assert water.disposition == "closure_correction_fallback_candidate"
    assert set(water.record_ids) == {"MSP_0125", "MSP_0126", "MSP_0127"}
    assert "component_partition_does_not_close" in water.reasons


def test_conservative_press_policy_does_not_apply_nonclosing_water():
    result = build_conservative_press_partition_policy(load_press_partition_evidence())

    assert "Water" in result.unmapped_components
    assert not any(rule.target_name == "Water" for rule in result.applied_rules)
    water_rule = next(rule for rule in result.blocked_rules if rule.source_pool == "water")
    assert water_rule.original_closure_sum == pytest.approx(1.017012)
    assert "source_partition_closure_1.017012" in water_rule.warnings
    assert result.policy.fallback_status["water_closure_correction"] is False


def test_water_closure_correction_is_explicit_and_conserves_water_mass():
    pools = build_dynamic_feedstock_pools(
        build_dynamic_feedstock_input_bundle("2026-05"),
        default_literature_pool_policy(),
    )
    correction = WaterClosureCorrectionPolicy(
        policy_id="reviewed_water_closure_test",
        rationale="Test-only explicit correction of the published analytical closure.",
    )
    policy = build_conservative_press_partition_policy(
        load_press_partition_evidence(),
        water_closure_correction=correction,
    )
    preview = preview_mechanical_separation(
        pools,
        default_mechanical_separation_policy(),
        partition_policy=policy,
    )
    water_rule = next(rule for rule in policy.applied_rules if rule.target_name == "Water")
    allocated_water = sum(
        stream.get("Water", 0.0)
        for stream in preview.stream_component_masses_kg_per_kg_feed.values()
    )

    assert water_rule.rule_type == "closure_corrected_literature"
    assert sum(water_rule.original_stream_shares.values()) == pytest.approx(1.017012)
    assert sum(water_rule.stream_shares.values()) == pytest.approx(1.0)
    assert "analytical_closure_corrected" in water_rule.warnings
    assert allocated_water == pytest.approx(pools.component_mass_fractions["Water"])
    assert preview.component_mass_balance_residuals["Water"] == pytest.approx(0.0)
    assert preview.provenance["source_values_normalized"] is True


def test_total_protein_fallback_requires_explicit_policy_when_complete_source_exists(tmp_path):
    path = tmp_path / "protein_partition.csv"
    fieldnames = [
        "record_id",
        "source_id",
        "source_title",
        "material",
        "species_or_feedstock",
        "process_boundary",
        "process_step",
        "product_stream",
        "component_or_pool",
        "response_parameter",
        "reported_value",
        "reported_unit",
        "basis",
        "feed_basis",
        "partition_fraction",
        "transferability_class",
        "confidence_class",
        "notes",
    ]
    with path.open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        for record_id, stream, share in (
            ("TP-C", "Press cake", 0.5),
            ("TP-J", "Brown juice", 0.4),
            ("TP-P", "Protein concentrate", 0.1),
        ):
            writer.writerow(
                {
                    "record_id": record_id,
                    "source_id": CURRENT_PARTITION_SOURCE_ID,
                    "source_title": "Synthetic complete source fixture",
                    "material": "Fresh green biomass",
                    "species_or_feedstock": CURRENT_PARTITION_SPECIES,
                    "process_boundary": CURRENT_PRESS_BOUNDARY,
                    "process_step": "Fractionation and downstream protein recovery",
                    "product_stream": stream,
                    "component_or_pool": "total protein",
                    "response_parameter": "Total protein partition",
                    "reported_value": str(share),
                    "reported_unit": "kg/kg feed protein",
                    "basis": "Feed total protein",
                    "feed_basis": "1 kg fresh biomass",
                    "partition_fraction": str(share),
                    "transferability_class": "test_fixture",
                    "confidence_class": "test_fixture",
                    "notes": "Synthetic test fixture; not project evidence.",
                }
            )
    evidence = load_press_partition_evidence(path)
    default_result = build_conservative_press_partition_policy(evidence)
    enabled_result = build_conservative_press_partition_policy(
        evidence,
        total_protein_fallback=TotalProteinPartitionFallbackPolicy(
            policy_id="reviewed_total_protein_test",
            rationale="Test-only explicit proxy across protein solubility classes.",
        ),
    )

    assert not any(rule.target_name == "SolubleProtein" for rule in default_result.applied_rules)
    assert any("total_protein_proxy_for_solubility_classes_not_enabled" in rule.warnings for rule in default_result.blocked_rules)
    assert {rule.target_name for rule in enabled_result.applied_rules} == {
        "SolubleProtein",
        "SuspendedProtein",
    }
    assert all(
        rule.rule_type == "total_protein_proxy_for_solubility_classes"
        for rule in enabled_result.applied_rules
    )


def test_dynamic_press_bundle_is_json_safe_and_reports_incomplete_stream_assignment(tmp_path):
    before = dict(load_feedstock_proxies())
    pools = build_dynamic_feedstock_pools(
        build_dynamic_feedstock_input_bundle("2026-05"),
        default_literature_pool_policy(),
    )
    bundle = build_dynamic_press_preview_bundle(
        pools,
        water_closure_correction=WaterClosureCorrectionPolicy(
            policy_id="reviewed_water_closure_test",
            rationale="Test-only explicit correction.",
        ),
    )
    extraction = build_extraction_ready_stream_preview(bundle)
    artifacts = write_dynamic_press_preview_reports(
        [bundle],
        summary_csv_path=tmp_path / "dynamic_press_preview.csv",
        components_csv_path=tmp_path / "dynamic_press_stream_components.csv",
        markdown_path=tmp_path / "dynamic_press_preview.md",
        write_evidence_summary=False,
    )

    json.dumps(bundle.to_dict())
    json.dumps(extraction.to_dict())
    assert bundle.extraction_readiness.water_partition_ready is True
    assert bundle.extraction_readiness.can_feed_protein_extraction_preview is False
    assert bundle.extraction_readiness.can_feed_ad_preview is False
    assert bundle.extraction_readiness.can_feed_nutrient_recovery_preview is False
    assert all(
        summary["assigned_mass_equals_stream_yield"] is False
        for summary in bundle.press_preview.stream_mass_balance_summary.values()
    )
    assert bundle.press_preview.can_drive_simulation is False
    assert extraction.brown_juice_water_kg_per_kg_feed is not None
    assert extraction.brown_juice_soluble_protein_kg_per_kg_feed is None
    assert set(artifacts) == {"summary_csv", "components_csv", "markdown"}
    assert (tmp_path / "dynamic_press_preview.csv").is_file()
    assert (tmp_path / "dynamic_press_stream_components.csv").is_file()
    assert (tmp_path / "dynamic_press_preview.md").is_file()
    assert dict(load_feedstock_proxies()) == before
