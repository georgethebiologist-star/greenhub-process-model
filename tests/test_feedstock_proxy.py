import json

from Greenhub.feedstock_proxy import (
    feedstock_proxy_resolution_candidates,
    load_feedstock_proxies,
    summarize_feedstock_proxy_evidence,
)
from Greenhub.feedstock_resolution import (
    preview_feedstock_resolution_gates,
    summarize_feedstock_resolution_gates,
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
