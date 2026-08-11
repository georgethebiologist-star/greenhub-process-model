from __future__ import annotations

import json
from pathlib import Path

import biosteam as bst
import pytest

from Greenhub.chemicals import chemicals, thermo
from Greenhub.application.dynamic_biosteam_service import DynamicBioSTEAMShadowService
from Greenhub.dynamic_biosteam_adapter import (
    DynamicBioSTEAMAdapterConfig,
    build_dynamic_biosteam_shadow_flowsheet,
    build_dynamic_biosteam_shadow_grid,
    validate_dynamic_biosteam_adapter_result,
    write_dynamic_biosteam_adapter_reports,
)
from Greenhub.feedstock_proxy import load_feedstock_proxies
from Greenhub.stream_templates import stream_template_table


@pytest.fixture(scope="module")
def adapter_result():
    return build_dynamic_biosteam_shadow_flowsheet(DynamicBioSTEAMAdapterConfig())


@pytest.fixture(scope="module")
def adapter_grid():
    return build_dynamic_biosteam_shadow_grid(
        DynamicBioSTEAMAdapterConfig(create_biosteam_objects=False)
    )


def _records_by_source(result):
    return {record.source_dynamic_stream_id: record for record in result.records}


def test_one_step_adapter_creates_expected_stream_records(adapter_result):
    expected = {
        "press_cake",
        "brown_juice",
        "raw_press_unrecovered_process_mass",
        "clarified_juice",
        "cell_debris",
        "protein_rich_phase",
        "extraction_supernatant",
        "wet_protein_cake",
        "final_supernatant",
        "dried_protein_product",
        "evaporated_water",
        "biogas_feed_candidate",
    }
    assert {record.source_dynamic_stream_id for record in adapter_result.records} == expected
    assert len(adapter_result.biosteam_streams) == len(expected)
    assert all(record.adapter_stream_id.startswith("dyn_2026_05_") for record in adapter_result.records)
    assert set(adapter_result.isolated_flowsheet.stream.data) == set(
        adapter_result.biosteam_streams
    )


def test_adapter_scales_kg_per_kg_feed_to_kg_per_hour(adapter_result):
    for record in adapter_result.records:
        assert record.stream_mass_kg_hr == pytest.approx(
            record.source_kg_per_kg_feed * 1000.0
        )
        assert (
            record.total_component_kg_hr
            + record.total_metadata_kg_hr
            + record.unassigned_mass_kg_hr
        ) == pytest.approx(record.stream_mass_kg_hr)


def test_biosteam_exact_component_masses_match_records(adapter_result):
    for record in adapter_result.records:
        stream = adapter_result.biosteam_streams[record.adapter_stream_id]
        for component, mass in record.component_masses_kg_hr.items():
            assert float(stream.imass[component]) == pytest.approx(mass)
        assert float(stream.F_mass) == pytest.approx(record.total_component_kg_hr)


def test_metadata_pools_remain_explicit_and_are_not_hidden_as_chemicals(adapter_result):
    records = _records_by_source(adapter_result)
    metadata_records = [record for record in records.values() if record.metadata_pools_kg_hr]
    assert metadata_records
    assert any("fructan" in record.metadata_pools_kg_hr for record in metadata_records)
    assert any(
        "residual_unallocated_dry_matter" in record.metadata_pools_kg_hr
        for record in metadata_records
    )
    for record in metadata_records:
        stream = adapter_result.biosteam_streams[record.adapter_stream_id]
        assert float(stream.F_mass) == pytest.approx(record.total_component_kg_hr)
        assert record.total_metadata_kg_hr > 0.0


def test_press_cake_is_external_output_and_not_biogas_input(adapter_result):
    records = _records_by_source(adapter_result)
    preview = adapter_result.source_run.pathway_preview
    assert preview is not None
    assert "press_cake" in records
    assert {stream.stream_id for stream in preview.biogas_mix_preparation.inputs} == {
        "cell_debris",
        "final_supernatant",
    }
    assert adapter_result.mass_balance.press_cake_boundary_valid is True


def test_dried_protein_and_evaporated_water_match_dynamic_source(adapter_result):
    records = _records_by_source(adapter_result)
    preview = adapter_result.source_run.pathway_preview
    assert preview is not None
    dried = records["dried_protein_product"]
    evaporated = records["evaporated_water"]
    expected_protein = adapter_result.source_run.protein_metrics_kg_per_kg_feed[
        "dried_product_protein"
    ] * 1000.0
    assert sum(
        dried.component_masses_kg_hr.get(component, 0.0)
        for component in ("SolubleProtein", "SuspendedProtein")
    ) == pytest.approx(expected_protein)
    wet_stream = next(
        stream
        for stream in preview.second_centrifugation.outputs
        if stream.stream_id == "wet_protein_cake"
    )
    dried_stream = next(
        stream for stream in preview.drying.outputs if stream.stream_id == "dried_protein_product"
    )
    removed_water = (
        wet_stream.component_masses_kg_per_kg_feed.get("Water", 0.0)
        - dried_stream.component_masses_kg_per_kg_feed.get("Water", 0.0)
    ) * 1000.0
    assert evaporated.component_masses_kg_hr["Water"] == pytest.approx(removed_water)


def test_one_step_adapter_validates_global_and_identity_balance(adapter_result):
    balance = validate_dynamic_biosteam_adapter_result(adapter_result)
    assert balance.overall_closes is True
    assert balance.identity_closes is True
    assert balance.per_stream_component_masses_match is True
    assert balance.metadata_preserved_in_records is True
    assert balance.source_stream_masses_match is True
    assert balance.closes is True
    assert adapter_result.can_drive_shadow_adapter is True
    assert adapter_result.can_drive_simulation is False
    assert adapter_result.validated_simulation_ready is False


def test_grid_adapter_covers_all_seven_months_and_is_json_safe(adapter_grid):
    assert adapter_grid.time_labels == (
        "2026-05",
        "2026-06",
        "2026-07",
        "2026-08",
        "2026-09",
        "2026-10",
        "2026-11",
    )
    assert adapter_grid.all_steps_close is True
    assert adapter_grid.all_empirical_flowsheets_unchanged is True
    json.dumps(adapter_grid.to_dict())


def test_adapter_report_writer_creates_three_csvs(adapter_result, tmp_path):
    paths = write_dynamic_biosteam_adapter_reports(adapter_result, output_dir=tmp_path)
    assert set(paths) == {"streams", "balance", "provenance"}
    for path in paths.values():
        assert Path(path).is_file()
    assert "created_biosteam_stream_id" in Path(paths["streams"]).read_text(encoding="utf-8")
    assert "empirical_flowsheet_unchanged" in Path(paths["balance"]).read_text(encoding="utf-8")
    assert "source_unit_policy" in Path(paths["provenance"]).read_text(encoding="utf-8")


def test_adapter_preserves_policy_and_evidence_trace(adapter_result):
    records = _records_by_source(adapter_result)
    raw = records["press_cake"]
    first = records["cell_debris"]
    second = records["wet_protein_cake"]
    assert "raw_press_lolium_perenne_2025" in raw.policy_ids
    assert "RAW_0001" in raw.record_ids
    assert "CEN_0011" in first.record_ids
    assert "PCEN_0003" in second.record_ids
    assert raw.evidence_classes
    assert raw.warnings


def test_repeated_adapter_build_restores_empirical_registry_and_templates():
    before_flowsheet = bst.main_flowsheet.get_flowsheet()
    before_registry = dict(bst.main_flowsheet.stream.data)
    before_chemical_ids = tuple(chemicals.IDs)
    before_templates = stream_template_table()
    before_proxies = dict(load_feedstock_proxies())
    before_thermo = bst.settings.get_thermo()

    first = build_dynamic_biosteam_shadow_flowsheet(DynamicBioSTEAMAdapterConfig())
    second = build_dynamic_biosteam_shadow_flowsheet(DynamicBioSTEAMAdapterConfig())

    assert first.isolated_flowsheet is not second.isolated_flowsheet
    assert bst.main_flowsheet.get_flowsheet() is before_flowsheet
    assert before_registry.keys() == bst.main_flowsheet.stream.data.keys()
    assert all(
        before_registry[key] is bst.main_flowsheet.stream.data[key]
        for key in before_registry
    )
    assert not any(ID.startswith("dyn_") for ID in bst.main_flowsheet.stream.data)
    assert tuple(chemicals.IDs) == before_chemical_ids
    assert bst.settings.get_thermo() is before_thermo
    assert all(stream.thermo is thermo for stream in first.biosteam_streams.values())
    assert stream_template_table() == before_templates
    assert dict(load_feedstock_proxies()) == before_proxies


@pytest.mark.parametrize("basis", [0.0, -1.0])
def test_adapter_rejects_nonpositive_feed_basis(basis):
    with pytest.raises(ValueError, match="basis_feed_kg_per_hr"):
        DynamicBioSTEAMAdapterConfig(basis_feed_kg_per_hr=basis)


def test_adapter_rejects_empirical_flowsheet_connection():
    with pytest.raises(ValueError, match="cannot connect to the empirical flowsheet"):
        DynamicBioSTEAMAdapterConfig(connect_to_empirical_flowsheet=True)


def test_non_http_service_exposes_opt_in_shadow_preview():
    result = DynamicBioSTEAMShadowService().get_preview(
        time_label="2026-05",
        basis_feed_kg_per_hr=250.0,
    )
    assert result.config.basis_feed_kg_per_hr == pytest.approx(250.0)
    assert result.can_drive_shadow_adapter is True
    assert result.can_drive_simulation is False
