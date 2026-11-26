import json
from dataclasses import replace

import pytest

from Greenhub.application.contracts import SCHEMA_VERSION, ScenarioSelection, SimulationRequest
from Greenhub.application.errors import RequestValidationError
from Greenhub.application.simulation_service import SimulationService
from Greenhub.integration import create_integrated_greenhub_system
from Greenhub.parameters import CalculationMode, ResolutionMode


SCENARIOS = ScenarioSelection(
    feed_preparation="F1",
    protein_recovery="PR1",
    anaerobic_digestion="AD1",
    biogas_upgrading="BG2",
    nutrient_recovery="NR2",
    process_order="A",
)


def _request(request_id, mode=CalculationMode.STRUCTURAL, resolution=ResolutionMode.STEADY_STATE):
    return SimulationRequest(
        SCHEMA_VERSION,
        request_id,
        "greenhub-test",
        calculation_mode=mode,
        resolution_mode=resolution,
        scenarios=SCENARIOS,
    )


def test_dynamic_request_is_blocked_without_downgrade(tmp_path):
    service = SimulationService(run_root=tmp_path)
    with pytest.raises(RequestValidationError, match="no steady-state downgrade"):
        service.create_run(_request("dynamic", resolution=ResolutionMode.DYNAMIC))


def test_isolated_structural_and_literature_runs_and_exports(tmp_path):
    service = SimulationService(run_root=tmp_path)
    structural_id = service.create_run(_request("structural"))
    structural = service.execute_run(structural_id)
    literature_id = service.create_run(_request("literature", CalculationMode.LITERATURE_DEFAULT))
    literature = service.execute_run(literature_id)

    structural_context = service.repository.get(structural_id)
    literature_context = service.repository.get(literature_id)
    assert structural_context.model.flowsheet is not literature_context.model.flowsheet
    structural_r401 = structural_context.model.units["R401"].acid_recovery_fraction
    literature_r401 = literature_context.model.units["R401"].acid_recovery_fraction
    assert literature_r401 == pytest.approx(0.38)
    assert structural_r401 != literature_r401
    structural_precipitation = next(item for item in structural.resolved_parameters if item.parameter_id == "phase4.precipitation_efficiency")
    literature_precipitation = next(item for item in literature.resolved_parameters if item.parameter_id == "phase4.precipitation_efficiency")
    assert structural_precipitation.quality_class == "E"
    assert literature_precipitation.quality_class == "C"
    assert literature_precipitation.stable_identifier == "10.3389/fsufs.2019.00112"
    assert literature_precipitation.source_url == "https://doi.org/10.3389/fsufs.2019.00112"
    assert literature_precipitation.source_title
    assert literature_precipitation.exact_source_location
    resolved_literature = {item.parameter_id: item for item in literature_context.resolved_parameters}
    assert resolved_literature["phase4.precipitation_efficiency"].selected_candidate.source_row_id == "REC-005"
    structural_pH = next(item for item in structural.resolved_parameters if item.parameter_id == "phase4.target_pH")
    literature_pH = next(item for item in literature.resolved_parameters if item.parameter_id == "phase4.target_pH")
    assert structural_pH.quality_class == "E"
    assert literature_pH.value == pytest.approx(4.5)
    assert literature_pH.quality_class == "C"
    assert resolved_literature["phase4.target_pH"].selected_candidate.source_row_id == "REC-006"
    assert resolved_literature["phase4.target_pH"].selected_candidate.readiness_state.value == "D4"
    assert structural.validation.passed and literature.validation.passed
    assert structural.summary_kpis["overall_mass_residual"].value == pytest.approx(0.0, abs=1e-6)
    assert literature.summary_kpis["overall_mass_residual"].value == pytest.approx(0.0, abs=1e-6)

    required = {
        "simulation_request.json", "resolved_parameters.json", "resolved_parameters.csv",
        "provenance.json", "summary.json", "process_areas.json", "streams.json",
        "streams.csv", "units.json", "units.csv", "balances.json", "balances.csv",
        "utilities.json", "utilities.csv", "products.json", "products.csv",
        "validation.json", "validation.csv", "graph.json", "plot_manifest.json",
        "simulation_result.json", "run_manifest.json",
    }
    assert required <= {item.name for item in literature_context.run_directory.iterdir()}
    payload = json.dumps(literature.to_dict(), allow_nan=False)
    assert "C:\\\\" not in payload
    assert ":\\\\" not in payload
    assert literature.graph.nodes and literature.graph.edges
    assert any(item.availability_status == "available" for item in literature.plots)


def test_pr3_guo_literature_conditions_reach_calculation_and_result_contract(tmp_path):
    request = replace(
        _request("guo-pr3-literature", CalculationMode.LITERATURE_DEFAULT),
        scenarios=ScenarioSelection(
            feed_preparation="F1",
            protein_recovery="PR3",
            anaerobic_digestion="AD1",
            biogas_upgrading="BG2",
            nutrient_recovery="NR2",
            process_order="A",
        ),
    )
    service = SimulationService(run_root=tmp_path)
    run_id = service.create_run(request)
    result = service.execute_run(run_id)
    context = service.repository.get(run_id)
    reported = {item.parameter_id: item for item in result.resolved_parameters}

    assert reported["phase4.target_pH"].value == pytest.approx(5.0)
    assert reported["phase4.target_pH"].quality_class == "B"
    assert reported["phase4.target_pH"].stable_identifier == "10.1016/j.fufo.2022.100173"
    assert reported["phase4.target_pH"].exact_source_location == "Article abstract"
    assert reported["phase4.precipitation_temperature_C"].value == pytest.approx(60.0)
    assert reported["phase4.precipitation_temperature_C"].quality_class == "B"

    phase4 = context.model.legacy_model.upstream_model.upstream_model.upstream_model
    assert phase4.parameters["values"]["target_pH"] == pytest.approx(5.0)
    assert phase4.parameters["values"]["precipitation_temperature_C"] == pytest.approx(60.0)
    assert result.validation.passed


def test_pr3_default_precipitation_temperature_reports_linked_proxy_evidence(tmp_path):
    request = replace(
        _request("guo-pr3-default-evidence"),
        scenarios=ScenarioSelection(
            feed_preparation="F1",
            protein_recovery="PR3",
            anaerobic_digestion="AD1",
            biogas_upgrading="BG2",
            nutrient_recovery="NR2",
            process_order="A",
        ),
    )
    service = SimulationService(run_root=tmp_path)
    run_id = service.create_run(request)
    result = service.execute_run(run_id)
    context = service.repository.get(run_id)
    reported = {item.parameter_id: item for item in result.resolved_parameters}
    selected = {item.parameter_id: item for item in context.resolved_parameters}
    temperature = reported["phase4.precipitation_temperature_C"]
    candidate = selected["phase4.precipitation_temperature_C"].selected_candidate
    pH = reported["phase4.target_pH"]
    pH_candidate = selected["phase4.target_pH"].selected_candidate

    assert temperature.value == pytest.approx(60.0)
    assert temperature.quality_class == "C"
    assert temperature.stable_identifier == "10.1016/j.fufo.2022.100173"
    assert temperature.source_url == "https://doi.org/10.1016/j.fufo.2022.100173"
    assert candidate.readiness_state.value == "D4"
    assert candidate.source_row_id == "Phase4Parameters:90"
    assert candidate.evidence_class == "literature_linked_assumption"
    assert pH.value == pytest.approx(5.0)
    assert pH.quality_class == "C"
    assert pH.stable_identifier == "10.1016/j.fufo.2022.100173"
    assert pH_candidate.readiness_state.value == "D4"
    assert pH_candidate.source_row_id == "Phase4Parameters:91"
    assert pH_candidate.evidence_class == "literature_linked_assumption"
    phase4 = context.model.legacy_model.upstream_model.upstream_model.upstream_model
    assert phase4.parameters["values"]["precipitation_temperature_C"] == pytest.approx(60.0)
    assert phase4.parameters["values"]["target_pH"] == pytest.approx(5.0)
    assert result.validation.passed


def test_service_structural_result_matches_direct_factory(tmp_path):
    service = SimulationService(run_root=tmp_path)
    run_id = service.create_run(_request("equivalence"))
    service_result = service.execute_run(run_id)
    direct = create_integrated_greenhub_system(
        scenario_id=SCENARIOS.nutrient_recovery,
        biogas_upgrading_scenario_id=SCENARIOS.biogas_upgrading,
        anaerobic_digestion_scenario_id=SCENARIOS.anaerobic_digestion,
        protein_recovery_scenario_id=SCENARIOS.protein_recovery,
        feed_preparation_scenario_id=SCENARIOS.feed_preparation,
        selected_month="July",
        process_order=SCENARIOS.process_order,
        feed_composition=_request("direct-equivalent").feed_composition,
    ).simulate()
    assert service_result.summary_kpis["boundary_inlet_mass"].value == pytest.approx(
        direct.validation_report.boundary_in_kg_hr, rel=0.0, abs=1e-9
    )
    assert service_result.summary_kpis["boundary_outlet_mass"].value == pytest.approx(
        direct.validation_report.boundary_out_kg_hr, rel=0.0, abs=1e-9
    )
    assert service.repository.get(run_id).model.flowsheet is not direct.flowsheet


def test_service_uses_canonical_default_and_applies_feed_composition_override(tmp_path):
    from pathlib import Path

    profile_path = (
        Path(__file__).parents[1]
        / "Greenhub/data/Pre-treatment/Feedstock/greenhub_feed_composition_defaults.json"
    )
    profile = json.loads(profile_path.read_text(encoding="utf-8"))["compounds"]
    expected = {key: row["wet_mass_fraction"] for key, row in profile.items()}
    changed = dict(expected)
    changed["Water"] -= 0.05  # 95% wet-mass total; contract normalizes it to 100%.

    service = SimulationService(run_root=tmp_path)
    scenarios = ScenarioSelection(
        feed_preparation="F1",
        protein_recovery="PR3",
        anaerobic_digestion="AD1",
        biogas_upgrading="BG2",
        nutrient_recovery="NR4",
        process_order="A",
    )

    def execute(request_id, composition=None):
        request = SimulationRequest(
            SCHEMA_VERSION,
            request_id,
            "greenhub-composition-test",
            calculation_mode=CalculationMode.STRUCTURAL,
            resolution_mode=ResolutionMode.STEADY_STATE,
            scenarios=scenarios,
            wet_feed_rate_kg_hr=1000.0,
            feed_composition={} if composition is None else composition,
            strict_validation=False,
        )
        run_id = service.create_run(request)
        result = service.execute_run(run_id)
        model = service.repository.get(run_id).model
        feed = model.streams["feed"]
        return result, float(feed.imass["Water"]), float(feed.imass["SolubleProtein"])

    baseline, baseline_water, baseline_soluble_protein = execute("composition-default")
    modified, modified_water, modified_soluble_protein = execute("composition-modified", changed)

    assert baseline_water == pytest.approx(857.0)
    assert baseline_soluble_protein == pytest.approx(expected["SolubleProtein"] * 1000.0)
    assert modified_water == pytest.approx((expected["Water"] - 0.05) / 0.95 * 1000.0)
    assert modified_soluble_protein == pytest.approx(expected["SolubleProtein"] / 0.95 * 1000.0)
    baseline_feed_result = next(stream for stream in baseline.streams if "feed" in stream.aliases)
    modified_feed_result = next(stream for stream in modified.streams if "feed" in stream.aliases)
    assert baseline_feed_result.components["HeavyMetals"].value == pytest.approx(
        expected["HeavyMetals"] * 1000.0
    )
    assert modified_feed_result.components["HeavyMetals"].value == pytest.approx(
        expected["HeavyMetals"] / 0.95 * 1000.0
    )
    assert baseline_feed_result.components["ChlorideIon"].value == pytest.approx(
        expected["ChlorideIon"] * 1000.0
    )
    assert baseline_feed_result.components["Starch"].value == pytest.approx(
        expected["Starch"] * 1000.0
    )
    assert modified_feed_result.components["ChlorideIon"].value == pytest.approx(
        expected["ChlorideIon"] / 0.95 * 1000.0
    )
    assert baseline.summary_kpis["dry_protein_product_mass"].value != pytest.approx(
        modified.summary_kpis["dry_protein_product_mass"].value
    )
