from __future__ import annotations

import json
from pathlib import Path

import biosteam as bst
import pytest

from Greenhub.chemicals import chemicals, thermo
from Greenhub.application.dynamic_biosteam_service import DynamicBioSTEAMShadowService
from Greenhub.dynamic_biosteam_adapter import (
    DynamicBioSTEAMAdapterConfig,
    build_dynamic_biosteam_calculation_shadow_system,
    build_dynamic_biosteam_calculation_shadow_system_grid,
    build_dynamic_biosteam_shadow_system,
    build_dynamic_biosteam_shadow_system_grid,
    build_dynamic_biosteam_shadow_flowsheet,
    build_dynamic_biosteam_shadow_grid,
    validate_dynamic_biosteam_adapter_result,
    validate_dynamic_biosteam_calculation_shadow_system,
    validate_dynamic_biosteam_shadow_system,
    write_dynamic_biosteam_adapter_reports,
    write_dynamic_biosteam_calculation_shadow_reports,
    write_dynamic_biosteam_shadow_system_reports,
)
from Greenhub.dynamic_biosteam_units import (
    DynamicFirstCentrifugeCalculationUnit,
    DynamicFirstCentrifugeUnit,
    DynamicProteinDryerCalculationUnit,
    DynamicProteinDryerUnit,
    DynamicProteinExtractionCalculationUnit,
    DynamicProteinExtractionUnit,
    DynamicRawPressCalculationUnit,
    DynamicRawPressUnit,
    DynamicResidualMixerCalculationUnit,
    DynamicResidualMixerUnit,
    DynamicSecondCentrifugeCalculationUnit,
    DynamicSecondCentrifugeUnit,
)
from Greenhub.feedstock_proxy import load_feedstock_proxies
from Greenhub.dynamic_process import DynamicProteinScenarioConfig
from Greenhub.stream_templates import stream_template_table


@pytest.fixture(scope="module")
def adapter_result():
    return build_dynamic_biosteam_shadow_flowsheet(DynamicBioSTEAMAdapterConfig())


@pytest.fixture(scope="module")
def adapter_grid():
    return build_dynamic_biosteam_shadow_grid(
        DynamicBioSTEAMAdapterConfig(create_biosteam_objects=False)
    )


@pytest.fixture(scope="module")
def shadow_system_result():
    return build_dynamic_biosteam_shadow_system()


@pytest.fixture(scope="module")
def shadow_system_grid():
    return build_dynamic_biosteam_shadow_system_grid()


@pytest.fixture(scope="module")
def calculation_system_result():
    return build_dynamic_biosteam_calculation_shadow_system()


@pytest.fixture(scope="module")
def calculation_system_grid():
    return build_dynamic_biosteam_calculation_shadow_system_grid()


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


def _assert_stream_matches_record(stream, record):
    for component, mass in record.component_masses_kg_hr.items():
        assert float(stream.imass[component]) == pytest.approx(mass)
    assert float(stream.F_mass) == pytest.approx(record.total_component_kg_hr)


def test_shadow_system_builds_six_real_biosteam_units(shadow_system_result):
    expected_types = (
        DynamicRawPressUnit,
        DynamicFirstCentrifugeUnit,
        DynamicProteinExtractionUnit,
        DynamicSecondCentrifugeUnit,
        DynamicProteinDryerUnit,
        DynamicResidualMixerUnit,
    )
    assert len(shadow_system_result.units) == 6
    assert tuple(type(unit) for unit in shadow_system_result.units.values()) == expected_types
    assert len(tuple(shadow_system_result.system.units)) == 6


def test_shadow_system_unit_and_stream_ids_are_prefixed_and_isolated(
    shadow_system_result,
):
    assert all(unit.ID.startswith("dyn_2026_05_") for unit in shadow_system_result.units.values())
    assert all(stream.ID.startswith("dyn_2026_05_") for stream in shadow_system_result.streams.values())
    assert set(shadow_system_result.isolated_flowsheet.unit.data) == {
        unit.ID for unit in shadow_system_result.units.values()
    }
    assert shadow_system_result.system.ID in shadow_system_result.isolated_flowsheet.system.data
    assert not any(ID.startswith("dyn_2026_05_") for ID in bst.main_flowsheet.stream.data)


def test_shadow_raw_press_outputs_match_adapter_records(shadow_system_result):
    records = {
        record.source_dynamic_stream_id: record
        for record in shadow_system_result.adapter_records
    }
    for stream_id in (
        "press_cake",
        "brown_juice",
        "raw_press_unrecovered_process_mass",
    ):
        _assert_stream_matches_record(
            shadow_system_result.streams[stream_id], records[stream_id]
        )


def test_shadow_first_centrifuge_outputs_match_adapter_records(shadow_system_result):
    records = {
        record.source_dynamic_stream_id: record
        for record in shadow_system_result.adapter_records
    }
    for stream_id in ("clarified_juice", "cell_debris"):
        _assert_stream_matches_record(
            shadow_system_result.streams[stream_id], records[stream_id]
        )


def test_shadow_protein_extraction_outputs_match_adapter_records(shadow_system_result):
    records = {
        record.source_dynamic_stream_id: record
        for record in shadow_system_result.adapter_records
    }
    for stream_id in ("protein_rich_phase", "extraction_supernatant"):
        _assert_stream_matches_record(
            shadow_system_result.streams[stream_id], records[stream_id]
        )


def test_shadow_second_centrifuge_and_dryer_preserve_protein_and_remove_only_water(
    shadow_system_result,
):
    records = {
        record.source_dynamic_stream_id: record
        for record in shadow_system_result.adapter_records
    }
    for stream_id in (
        "wet_protein_cake",
        "final_supernatant",
        "dried_protein_product",
        "evaporated_water",
    ):
        _assert_stream_matches_record(
            shadow_system_result.streams[stream_id], records[stream_id]
        )
    wet = shadow_system_result.streams["wet_protein_cake"]
    dried = shadow_system_result.streams["dried_protein_product"]
    evaporated = shadow_system_result.streams["evaporated_water"]
    assert float(dried.imass["SolubleProtein"]) == pytest.approx(
        float(wet.imass["SolubleProtein"])
    )
    for component in chemicals.IDs:
        if component != "Water":
            assert float(dried.imass[component]) == pytest.approx(float(wet.imass[component]))
    assert float(evaporated.F_mass) == pytest.approx(float(evaporated.imass["Water"]))
    assert float(wet.imass["Water"] - dried.imass["Water"]) == pytest.approx(
        float(evaporated.imass["Water"])
    )


def test_shadow_residual_mixer_excludes_press_cake(shadow_system_result):
    mixer = shadow_system_result.units["residual_mixer"]
    assert {stream.ID for stream in mixer.ins} == {
        shadow_system_result.streams["cell_debris"].ID,
        shadow_system_result.streams["final_supernatant"].ID,
    }
    assert shadow_system_result.streams["press_cake"].ID not in {
        stream.ID for stream in mixer.ins
    }


def test_shadow_system_validates_exact_and_metadata_inclusive_closure(
    shadow_system_result,
):
    balance = validate_dynamic_biosteam_shadow_system(shadow_system_result)
    assert balance.exact_component_identity_closes is True
    assert balance.adapter_full_mass_closes is True
    assert balance.adapter_metadata_identity_closes is True
    assert balance.all_unit_outputs_match_adapter_records is True
    assert balance.press_cake_boundary_valid is True
    assert balance.empirical_flowsheet_unchanged is True
    assert balance.closes is True
    assert shadow_system_result.can_drive_shadow_system is True
    assert shadow_system_result.can_drive_simulation is False


def test_shadow_system_grid_validates_all_seven_months(shadow_system_grid):
    assert shadow_system_grid.time_labels == (
        "2026-05",
        "2026-06",
        "2026-07",
        "2026-08",
        "2026-09",
        "2026-10",
        "2026-11",
    )
    assert len(shadow_system_grid.step_results) == 7
    assert shadow_system_grid.all_steps_close is True
    assert shadow_system_grid.all_steps_shadow_ready is True
    assert shadow_system_grid.all_empirical_flowsheets_unchanged is True
    json.dumps(shadow_system_grid.to_dict())


def test_shadow_system_build_restores_all_empirical_registries():
    before_flowsheet = bst.main_flowsheet.get_flowsheet()
    before = tuple(
        tuple(sorted((item.ID, id(item)) for item in registry))
        for registry in before_flowsheet.registries
    )
    before_templates = stream_template_table()
    before_chemicals = tuple(chemicals.IDs)
    before_proxies = dict(load_feedstock_proxies())

    result = build_dynamic_biosteam_shadow_system()

    assert result.mass_balance.empirical_flowsheet_unchanged is True
    assert bst.main_flowsheet.get_flowsheet() is before_flowsheet
    assert tuple(
        tuple(sorted((item.ID, id(item)) for item in registry))
        for registry in before_flowsheet.registries
    ) == before
    assert stream_template_table() == before_templates
    assert tuple(chemicals.IDs) == before_chemicals
    assert dict(load_feedstock_proxies()) == before_proxies


def test_shadow_system_reports_are_written(shadow_system_grid, tmp_path):
    paths = write_dynamic_biosteam_shadow_system_reports(
        shadow_system_grid, output_dir=tmp_path
    )
    assert set(paths) == {"units", "balance"}
    for path in paths.values():
        assert Path(path).is_file()
    unit_text = Path(paths["units"]).read_text(encoding="utf-8")
    balance_text = Path(paths["balance"]).read_text(encoding="utf-8")
    assert "DynamicRawPressUnit" in unit_text
    assert "dyn_2026_05_protein_shadow_sys" in balance_text


def test_shadow_system_service_summary_is_json_safe():
    summary = DynamicBioSTEAMShadowService().get_shadow_system(
        time_label="2026-05", basis_feed_kg_per_hr=100.0
    )
    json.dumps(summary)
    assert len(summary["unit_ids"]) == 6
    assert summary["can_drive_shadow_system"] is True
    assert summary["can_drive_simulation"] is False


def test_calculation_shadow_system_builds_six_calculation_units(
    calculation_system_result,
):
    expected_types = (
        DynamicRawPressCalculationUnit,
        DynamicFirstCentrifugeCalculationUnit,
        DynamicProteinExtractionCalculationUnit,
        DynamicSecondCentrifugeCalculationUnit,
        DynamicProteinDryerCalculationUnit,
        DynamicResidualMixerCalculationUnit,
    )
    assert tuple(type(unit) for unit in calculation_system_result.units.values()) == expected_types
    assert calculation_system_result.config.adapter_mode == (
        "calculation_shadow_system_report_only"
    )
    assert all(
        unit.shadow_mode == "calculation_shadow_system_report_only"
        for unit in calculation_system_result.units.values()
    )


@pytest.mark.parametrize(
    "unit_key,output_ids",
    [
        ("raw_press", ("press_cake", "brown_juice", "raw_press_unrecovered_process_mass")),
        ("first_centrifuge", ("clarified_juice", "cell_debris")),
        ("protein_extraction", ("protein_rich_phase", "extraction_supernatant")),
    ],
)
def test_calculation_partition_units_match_target_records(
    calculation_system_result, unit_key, output_ids
):
    records = {
        record.source_dynamic_stream_id: record
        for record in calculation_system_result.adapter_records
    }
    for stream_id in output_ids:
        _assert_stream_matches_record(
            calculation_system_result.streams[stream_id], records[stream_id]
        )
    parity = next(
        item for item in calculation_system_result.validation.unit_parities
        if item.unit_key == unit_key
    )
    assert parity.target_parity_passed is True
    assert parity.identity_closes is True


def test_isoelectric_calculation_owns_soluble_protein_recovery(
    calculation_system_result,
):
    unit = calculation_system_result.units["protein_extraction"]
    payload = unit.calculation_payload
    clarified = calculation_system_result.streams["clarified_juice"]
    rich = calculation_system_result.streams["protein_rich_phase"]
    assert payload.method == "isoelectric"
    assert payload.allow_n_to_protein_proxy is True
    assert payload.soluble_protein_recovery_fraction == pytest.approx(0.34)
    assert float(rich.imass["SolubleProtein"]) == pytest.approx(
        float(clarified.imass["SolubleProtein"]) * 0.34
    )
    assert "REC-001" in payload.source_metadata["record_ids"]


def test_second_centrifuge_and_dryer_calculate_moisture_without_protein_loss(
    calculation_system_result,
):
    second = calculation_system_result.units["second_centrifuge"].calculation_payload
    dryer = calculation_system_result.units["protein_dryer"].calculation_payload
    wet = calculation_system_result.streams["wet_protein_cake"]
    dried = calculation_system_result.streams["dried_protein_product"]
    evaporated = calculation_system_result.streams["evaporated_water"]
    assert second.target_wet_cake_moisture_fraction == pytest.approx(0.781)
    assert "PCEN_0003" in second.source_metadata["record_ids"]
    assert dryer.target_moisture_fraction == pytest.approx(0.15)
    assert float(dried.imass["SolubleProtein"]) == pytest.approx(
        float(wet.imass["SolubleProtein"])
    )
    assert float(dried.imass["Water"]) / float(dried.F_mass) == pytest.approx(0.15)
    assert float(evaporated.F_mass) == pytest.approx(float(evaporated.imass["Water"]))


def test_calculation_residual_mixer_excludes_press_cake(calculation_system_result):
    mixer = calculation_system_result.units["residual_mixer"]
    assert {stream.ID for stream in mixer.ins} == {
        calculation_system_result.streams["cell_debris"].ID,
        calculation_system_result.streams["final_supernatant"].ID,
    }
    assert calculation_system_result.streams["press_cake"].ID not in {
        stream.ID for stream in mixer.ins
    }


def test_calculation_validation_closes_and_preserves_metadata(
    calculation_system_result,
):
    validation = validate_dynamic_biosteam_calculation_shadow_system(
        calculation_system_result
    )
    assert validation.all_unit_parity_passed is True
    assert validation.exact_component_identity_closes is True
    assert validation.adapter_full_mass_closes is True
    assert validation.metadata_records_preserved is True
    assert validation.press_cake_boundary_valid is True
    assert validation.empirical_flowsheet_unchanged is True
    assert validation.closes is True
    assert calculation_system_result.can_drive_calculation_shadow_system is True
    assert calculation_system_result.can_drive_simulation is False


def test_calculation_shadow_grid_validates_all_months(calculation_system_grid):
    assert calculation_system_grid.time_labels == (
        "2026-05", "2026-06", "2026-07", "2026-08", "2026-09", "2026-10", "2026-11"
    )
    assert calculation_system_grid.all_steps_parity_passed is True
    assert calculation_system_grid.all_steps_calculation_shadow_ready is True
    assert calculation_system_grid.all_empirical_flowsheets_unchanged is True
    assert all(
        step.can_drive_calculation_shadow_system
        for step in calculation_system_grid.step_results
    )
    json.dumps(calculation_system_grid.to_dict())


def test_calculation_reports_are_written(calculation_system_grid, tmp_path):
    paths = write_dynamic_biosteam_calculation_shadow_reports(
        calculation_system_grid, output_dir=tmp_path
    )
    assert set(paths) == {"units", "balance", "parity"}
    assert all(Path(path).is_file() for path in paths.values())
    assert "DynamicProteinExtractionCalculationUnit" in Path(paths["units"]).read_text(
        encoding="utf-8"
    )
    assert "target_parity_passed" in Path(paths["parity"]).read_text(
        encoding="utf-8"
    )


def test_calculation_service_summaries_are_json_safe():
    service = DynamicBioSTEAMShadowService()
    step = service.get_calculation_shadow_system("2026-05", 100.0)
    grid = service.get_calculation_shadow_grid(100.0)
    json.dumps(step)
    json.dumps(grid)
    assert step["can_drive_calculation_shadow_system"] is True
    assert grid["all_steps_calculation_shadow_ready"] is True
    assert step["can_drive_simulation"] is False


def test_adapter_pretreatment_water_is_applied_on_shared_dynamic_basis():
    config = DynamicBioSTEAMAdapterConfig(
        pretreatment_water_addition_kg_per_kg_wet_feed=0.25,
        press_energy_kwh_per_t_wet_feed=1.0,
    )
    resolved = config.resolved_scenario_config()
    assert resolved.pretreatment_water_addition_kg_per_kg_wet_feed == pytest.approx(0.25)
    result = build_dynamic_biosteam_calculation_shadow_system(config)
    assert result.config.resolved_scenario_config().pretreatment_water_addition_kg_per_kg_wet_feed == pytest.approx(0.25)
    assert result.payloads.raw_press.press_energy_kwh_per_t_wet_feed == pytest.approx(1.0)
    assert result.feed_record.component_masses_kg_hr["Water"] > 600.0
    utilities = result.to_dict()["pretreatment_utilities"]
    diluted_feed_kg_hr = sum(result.feed_record.component_masses_kg_hr.values())
    original_wet_feed_kg_hr = diluted_feed_kg_hr / 1.25
    assert utilities["water_added_kg_hr_total"] == pytest.approx(original_wet_feed_kg_hr * 0.25)
    assert utilities["press_energy_kwh_hr_total"] == pytest.approx(original_wet_feed_kg_hr / 1000.0)
    press = next(unit for unit in result.units.values() if hasattr(unit, "pretreatment_state"))
    state = press.pretreatment_state
    for component, mass in result.feed_record.component_masses_kg_hr.items():
        assert state.output_component_masses_kg_hr[component] == pytest.approx(mass)
        if component != "Water":
            assert state.input_component_masses_kg_hr[component] == pytest.approx(mass)
    assert state.mass_residual_kg_hr == pytest.approx(0.0, abs=1e-9)
    assert result.validation.empirical_flowsheet_unchanged is True


def test_adapter_and_scenario_pretreatment_water_conflict_is_rejected():
    scenario = DynamicProteinScenarioConfig(pretreatment_water_addition_kg_per_kg_wet_feed=0.1)
    with pytest.raises(ValueError, match="must agree"):
        DynamicBioSTEAMAdapterConfig(
            scenario_config=scenario,
            pretreatment_water_addition_kg_per_kg_wet_feed=0.2,
        )


def test_calculation_build_restores_empirical_registry_and_target_mode_still_works():
    before_flowsheet = bst.main_flowsheet.get_flowsheet()
    before = tuple(
        tuple(sorted((item.ID, id(item)) for item in registry))
        for registry in before_flowsheet.registries
    )
    calculation = build_dynamic_biosteam_calculation_shadow_system()
    target = build_dynamic_biosteam_shadow_system()
    assert calculation.validation.empirical_flowsheet_unchanged is True
    assert target.mass_balance.empirical_flowsheet_unchanged is True
    assert bst.main_flowsheet.get_flowsheet() is before_flowsheet
    assert tuple(
        tuple(sorted((item.ID, id(item)) for item in registry))
        for registry in before_flowsheet.registries
    ) == before
    assert target.can_drive_shadow_system is True


def test_unsupported_heat_calculation_method_returns_typed_blocked_result():
    scenario = DynamicProteinScenarioConfig(protein_method="heat")
    result = build_dynamic_biosteam_calculation_shadow_system(
        DynamicBioSTEAMAdapterConfig(scenario_config=scenario)
    )
    assert result.system is None
    assert result.validation.selected_method == "heat"
    assert result.validation.selected_method_calculation_ready is False
    assert result.can_drive_calculation_shadow_system is False
    assert "protein_method_not_calculation_ready:heat" in result.blockers
