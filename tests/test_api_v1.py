"""Versioned HTTP adapter contract and isolation tests."""

from __future__ import annotations

import json
import re
from io import BytesIO

import pytest

from api.app import create_app


def invoke(app, method: str, path: str, payload=None, query: str = ""):
    body = b"" if payload is None else json.dumps(payload, allow_nan=False).encode("utf-8")
    captured = {}

    def start_response(status, headers):
        captured["status"] = int(status.split()[0])
        captured["headers"] = dict(headers)

    environ = {
        "REQUEST_METHOD": method,
        "PATH_INFO": path,
        "QUERY_STRING": query,
        "CONTENT_LENGTH": str(len(body)),
        "CONTENT_TYPE": "application/json",
        "wsgi.input": BytesIO(body),
    }
    encoded = b"".join(app(environ, start_response))
    return captured["status"], json.loads(encoded)


def request_payload(**updates):
    payload = {
        "schema_version": "1.0.0",
        "request_id": "api-test-request",
        "project_id": "api-test-project",
        "calculation_mode": "structural",
        "resolution_mode": "steady_state",
        "selected_month": "July",
        "scenarios": {
            "feed_preparation": "F2",
            "protein_recovery": "PR3",
            "anaerobic_digestion": "AD1",
            "biogas_upgrading": "BG2",
            "nutrient_recovery": "NR4",
            "process_order": "A",
        },
    }
    payload.update(updates)
    return payload


def test_discovery_and_openapi_endpoints_are_versioned(tmp_path):
    app = create_app(tmp_path)
    status, health = invoke(app, "GET", "/api/v1/health")
    assert status == 200
    assert health == {"api_version": "v1", "schema_version": "1.0.0", "status": "ok"}

    status, model_info = invoke(app, "GET", "/api/v1/model/info")
    assert status == 200
    assert model_info["active_equation_ids"] == ["EQ-MB-001"]
    assert model_info["scientific_core"] == "transport-neutral"

    status, document = invoke(app, "GET", "/api/v1/openapi.json")
    assert status == 200
    assert document["openapi"] == "3.1.0"
    assert "/api/v1/simulations/{run_id}/validation" in document["paths"]
    assert not any(
        reference.startswith("#/$defs/")
        for reference in re.findall(r'"\\$ref":\s*"([^"]+)"', json.dumps(document))
    )
    assert document["paths"]["/api/v1/simulations"]["post"]["responses"]["201"]["content"]["application/json"]["schema"] == {
        "$ref": "#/components/schemas/SimulationResult"
    }

    status, response = invoke(app, "GET", "/api/v1/parameters/not-a-parameter")
    assert status == 404
    assert response["error"]["code"] == "parameter_not_found"


@pytest.mark.parametrize(
    "payload, expected_code",
    [
        (request_payload(resolution_mode="dynamic"), "request_validation_failed"),
        (request_payload(unexpected_expression="__import__('os')"), "invalid_request"),
    ],
)
def test_simulation_request_errors_are_structured_and_do_not_leak(payload, expected_code, tmp_path):
    app = create_app(tmp_path)
    status, response = invoke(app, "POST", "/api/v1/simulations", payload)
    assert status == 422
    assert response["error"]["code"] == expected_code
    rendered = json.dumps(response, allow_nan=False)
    assert "Traceback" not in rendered
    assert not re.search(r"[A-Za-z]:[\\/]", rendered)


def test_simulation_and_result_endpoints_return_json_safe_service_results(tmp_path):
    app = create_app(tmp_path)
    status, result = invoke(app, "POST", "/api/v1/simulations", request_payload())
    assert status == 201
    assert result["status"] == "completed"
    assert result["validation"]["passed"] is True
    assert result["summary_kpis"]["boundary_inlet_mass"]["value"] == pytest.approx(403.9938456027056)
    assert result["summary_kpis"]["boundary_outlet_mass"]["value"] == pytest.approx(403.99384560661497)
    run_id = result["run_id"]

    for resource in (
        "status", "summary", "process-areas", "streams", "units", "balances",
        "utilities", "validation", "graph", "plots", "provenance", "exports",
    ):
        endpoint_status, response = invoke(app, "GET", f"/api/v1/simulations/{run_id}/{resource}")
        assert endpoint_status == 200, resource
        rendered = json.dumps(response, allow_nan=False)
        assert not re.search(r"[A-Za-z]:[\\/]", rendered), resource

    plot_id = result["plots"][0]["plot_id"]
    plot_status, plot = invoke(app, "GET", f"/api/v1/simulations/{run_id}/plots/{plot_id}")
    assert plot_status == 200
    assert plot["specification"]["plot_id"] == plot_id
    assert plot["series"]


def test_parameter_validation_uses_canonical_bounds(tmp_path):
    app = create_app(tmp_path)
    status, response = invoke(
        app,
        "POST",
        "/api/v1/parameters/validate",
        {"parameter_id": "phase4.precipitation_efficiency", "value": 1.1, "unit": "fraction"},
    )
    assert status == 200
    assert response["valid"] is False
    assert response["issues"][0]["blocking"] is True
