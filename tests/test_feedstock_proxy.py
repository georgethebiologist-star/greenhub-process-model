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
