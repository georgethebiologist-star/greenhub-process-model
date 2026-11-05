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


def test_process_page_design_override_units_are_accepted_and_applied():
    service = ParameterService()
    overrides = (
        ParameterOverride("phase4.acid_dose_kg_per_m3", 1.5, unit="kg/m³ liquid"),
        ParameterOverride("phase5.target_cod_olr_kg_m3_day", 3.25, unit="kg COD/m³/day"),
        ParameterOverride("phase5.digester_temperature_c", 42, unit="°C"),
        ParameterOverride("phase6.upgrading_minimum_methane_mol_fraction_dry", 0.4, unit="mol fraction"),
        ParameterOverride("phase7.struvite_phosphate_recovery_fraction", 0.72, unit="fraction"),
        ParameterOverride("phase7.ammonia_absorber_capture_efficiency", 0.93, unit="fraction"),
    )
    request = _request(
        calculation_mode=CalculationMode.LITERATURE_DEFAULT,
        scenarios=ScenarioSelection(protein_recovery="PR3", anaerobic_digestion="AD1",
                                    biogas_upgrading="BG2", nutrient_recovery="NR4"),
        design_overrides=overrides,
    )
    assert service.validate_overrides(request) == ()
    resolved = {item.parameter_id: item for item in service.resolve_parameters(request)}
    expected = {
        "phase4.acid_dose_kg_per_m3": 1.5,
        "phase5.target_cod_olr_kg_m3_day": 3.25,
        "phase5.digester_temperature_c": 42,
        "phase6.upgrading_minimum_methane_mol_fraction_dry": 0.4,
        "phase7.struvite_phosphate_recovery_fraction": 0.72,
        "phase7.ammonia_absorber_capture_efficiency": 0.93,
    }
    for parameter_id, value in expected.items():
        assert resolved[parameter_id].active_value == pytest.approx(value)
        assert resolved[parameter_id].override_status == "run_specific_user_override"
    model_overrides = service.resolver.model_overrides(tuple(resolved.values()))
    assert model_overrides["digester_temperature_c"] == 42
    assert model_overrides["target_cod_olr_kg_m3_day"] == 3.25
    assert model_overrides["upgrading_minimum_methane_mol_fraction_dry"] == 0.4


def test_dynamic_mode_is_not_silently_coerced_and_scenarios_are_validated():
    request = _request(resolution_mode=ResolutionMode.DYNAMIC)
    assert request.resolution_mode is ResolutionMode.DYNAMIC
    scenarios = ScenarioService()
    issues = scenarios.validate_scenario_chain(
        ScenarioSelection(protein_recovery="PR6")
    )
    assert any(item.blocking and item.code == "SCENARIO_DATA_GATE" for item in issues)
