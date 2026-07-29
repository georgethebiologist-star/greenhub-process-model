import json

import pytest

from Greenhub.application.contracts import SCHEMA_VERSION, ScenarioSelection, SimulationRequest
from Greenhub.application.errors import RequestValidationError
from Greenhub.application.simulation_service import SimulationService
from Greenhub.integration import create_integrated_greenhub_system
from Greenhub.parameters import CalculationMode, ResolutionMode


SCENARIOS = ScenarioSelection(
    feed_preparation="F2",
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
    assert literature_r401 == pytest.approx(0.34)
    assert structural_r401 != literature_r401
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
    ).simulate()
    assert service_result.summary_kpis["boundary_inlet_mass"].value == pytest.approx(
        direct.validation_report.boundary_in_kg_hr, rel=0.0, abs=1e-9
    )
    assert service_result.summary_kpis["boundary_outlet_mass"].value == pytest.approx(
        direct.validation_report.boundary_out_kg_hr, rel=0.0, abs=1e-9
    )
    assert service.repository.get(run_id).model.flowsheet is not direct.flowsheet
