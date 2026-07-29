import json

import pytest

from Greenhub.application.contracts import (
    SCHEMA_VERSION,
    ScenarioSelection,
    SimulationRequest,
)
from Greenhub.application.parameter_service import ParameterService
from Greenhub.application.scenario_service import ScenarioService
from Greenhub.parameters import CalculationMode, ParameterOverride, ResolutionMode


def _request(**kwargs):
    values = {
        "schema_version": SCHEMA_VERSION,
        "request_id": "request-1",
        "project_id": "greenhub-test",
    }
    values.update(kwargs)
    return SimulationRequest(**values)


def test_request_round_trip_is_json_safe_and_versioned():
    request = _request(
        calculation_mode=CalculationMode.EXPERT_OVERRIDE,
        resolution_mode=ResolutionMode.STEADY_STATE,
        operating_overrides=(
            ParameterOverride("phase4.precipitation_efficiency", 0.3, unit="fraction"),
        ),
    )
    payload = request.to_dict()
    json.dumps(payload, allow_nan=False)
    rebuilt = SimulationRequest.from_dict(payload)
    assert rebuilt == request
    with pytest.raises(ValueError):
        SimulationRequest(schema_version="2.0", request_id="x", project_id="y")


def test_parameter_service_exposes_sources_and_validates_overrides():
    service = ParameterService()
    request = _request(
        calculation_mode=CalculationMode.LITERATURE_DEFAULT,
        scenarios=ScenarioSelection(protein_recovery="PR1"),
    )
    resolved = {item.parameter_id: item for item in service.resolve_parameters(request)}
    assert resolved["phase4.precipitation_efficiency"].active_value == pytest.approx(0.34)
    assert service.validate_overrides(request) == ()
    sources = service.list_parameter_sources("phase4.precipitation_efficiency")
    assert any(item.source_row_id == "REC-001" for item in sources)


def test_dynamic_mode_is_not_silently_coerced_and_scenarios_are_validated():
    request = _request(resolution_mode=ResolutionMode.DYNAMIC)
    assert request.resolution_mode is ResolutionMode.DYNAMIC
    scenarios = ScenarioService()
    issues = scenarios.validate_scenario_chain(
        ScenarioSelection(protein_recovery="PR6")
    )
    assert any(item.blocking and item.code == "SCENARIO_DATA_GATE" for item in issues)
