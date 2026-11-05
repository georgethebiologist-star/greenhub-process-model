"""Versioned HTTP adapter contract and isolation tests."""

from __future__ import annotations

import json
import re
import time
from io import BytesIO

import pytest

from api.app import create_app
from Greenhub.application.schema_export import openapi_schema


def test_decision_support_openapi_documents_additive_analysis_inputs():
    properties = openapi_schema()["paths"]["/api/v1/decision-support/evaluate"]["post"]["requestBody"]["content"]["application/json"]["schema"]["properties"]["configuration"]["properties"]
    assert properties["use_screening_lca_factors"]["default"] is False
    assert properties["logistics_result"]["type"] == ["object", "null"]
    feed_composition=openapi_schema()["components"]["schemas"]["SimulationRequest"]["properties"]["feed_composition"]
    assert feed_composition["additionalProperties"]["maximum"]==1.1
    assert "0.90 to 1.10" in feed_composition["description"]


def test_resolved_parameter_quality_metadata_is_optional_and_documented():
    item = openapi_schema()["components"]["schemas"]["SimulationResult"]["properties"]["resolved_parameters"]["items"]
    assert "quality_class" in item["properties"]
    assert "stable_identifier" in item["properties"]
    assert "source_url" in item["properties"]
    assert "uncertainty" in item["properties"]
    assert not {"quality_class", "stable_identifier", "uncertainty"} & set(item["required"])


def test_backend_batch_endpoint_accepts_exact_candidate_overrides(tmp_path):
    app = create_app(tmp_path)
    captured = {}
    def capture_start(configuration, specifications=None, **kwargs):
        captured.update(configuration=configuration, specifications=specifications, **kwargs)
        return {"job_id": "test-job"}
    app.decision_batch_jobs.start = capture_start
    payload = {
        "configuration": {"simulation": {}},
        "candidate_overrides": [{"sample_id": "S-42-0001", "overrides": {
            "simulation.wet_feed_rate_kg_hr": 100,
            "simulation.scenarios.protein_recovery": "PR1",
        }}],
        "count": 1, "seed": 42, "mode": "design",
    }
    status, report = invoke(app, "POST", "/api/v1/decision-support/batch-jobs", payload)
    assert status == 200
    assert report == {"job_id": "test-job"}
    assert captured["candidate_overrides"] == payload["candidate_overrides"]
    assert captured["count"] == 1


def test_default_api_reads_saved_pareto_job_from_legacy_results_root(tmp_path, monkeypatch):
    from Greenhub import settings
    from Greenhub.application.decision_batch_jobs import DecisionBatchJobs
    monkeypatch.setattr(settings, "RESULTS_DIR", tmp_path / "results")
    legacy = settings.RESULTS_DIR / "actual_pareto_2000"
    jobs = DecisionBatchJobs(legacy, lambda config: {
        "configuration_echo": config,
        "feasibility": {"eligible_for_ranking": False},
        "objectives": {},
    })
    started = jobs.start({"value": 0}, [{"path": "value", "low": 1, "high": 1}], count=1)
    complete = jobs.status(started["job_id"])
    deadline = time.monotonic() + 2
    while complete["status"] != "completed" and time.monotonic() < deadline:
        time.sleep(.01)
        complete = jobs.status(started["job_id"])

    api = create_app()
    status, report = invoke(api, "GET", f'/api/v1/decision-support/batch-jobs/{started["job_id"]}')
    assert status == 200
    assert report["status"] == "completed"
    sample_id = complete["samples"][0]["sample_id"]
    status, candidate = invoke(api, "GET", f'/api/v1/decision-support/batch-jobs/{started["job_id"]}/candidates/{sample_id}')
    assert status == 200
    assert candidate["outputs"]["configuration_echo"] == {"value": 1}


def test_latest_pareto_api_exposes_grass_bonus_metadata_and_selected_scenarios(tmp_path, monkeypatch):
    from Greenhub import settings
    monkeypatch.setattr(settings, "RESULTS_DIR", tmp_path / "results")
    result_dir = settings.RESULTS_DIR / "pareto_rvo_2026"
    result_dir.mkdir(parents=True)
    metadata = {
        "schema_version": "greenhub-rvo-pareto-1.0",
        "grass_utilization_bonus": {"rates_eur_per_wet_tonne": [0, 10, 20, 30, 40, 50]},
        "groups": {"protein_enabled": {"sample_count": 6}},
        "groups_payload": {"protein_enabled": {
            "group": "protein_enabled", "sample_count": 6,
            "selected_candidates": {"grass_bonus_sensitivity": [{"sample_id": "P-GB20"}]},
            "samples": [{"sample_id": "large row payload must stay filtered"}],
        }},
    }
    (result_dir / "latest.json").write_text(json.dumps(metadata), encoding="utf-8")

    status, response = invoke(create_app(tmp_path), "GET", "/api/v1/decision-support/pareto/latest")

    assert status == 200
    assert response["grass_utilization_bonus"]["rates_eur_per_wet_tonne"] == [0, 10, 20, 30, 40, 50]
    assert response["groups_payload"]["protein_enabled"]["selected_candidates"]["grass_bonus_sensitivity"] == [{"sample_id": "P-GB20"}]
    assert "samples" not in response["groups_payload"]["protein_enabled"]


def test_latest_pareto_api_prefers_compact_generated_projection(tmp_path, monkeypatch):
    from Greenhub import settings
    monkeypatch.setattr(settings, "RESULTS_DIR", tmp_path / "results")
    result_dir = settings.RESULTS_DIR / "pareto_rvo_2026"
    result_dir.mkdir(parents=True)
    full = {"schema_version": "full", "groups_payload": {"large": {"samples": [{"large": "ledger"}]}}}
    compact = {"schema_version": "compact", "groups_payload": {"small": {"selected_candidates": {"x": [{"sample_id": "S-1"}]}}}}
    (result_dir / "latest.json").write_text(json.dumps(full), encoding="utf-8")
    (result_dir / "latest_ui.json").write_text(json.dumps(compact), encoding="utf-8")

    status, response = invoke(create_app(tmp_path), "GET", "/api/v1/decision-support/pareto/latest")

    assert status == 200
    assert response == compact


def test_stale_simulation_artifacts_are_not_served_after_restart(tmp_path):
    app=create_app(tmp_path)
    old_run_id='a'*32
    old_run=tmp_path/old_run_id
    old_run.mkdir()
    (old_run/'units.json').write_text('[{"unit_id":"stale"}]',encoding='utf-8')
    (old_run/'utilities.json').write_text('{"electricity_kwh":999}',encoding='utf-8')
    (old_run/'decision_support.json').write_text('{"npv":999999}',encoding='utf-8')
    (old_run/'graph.json').write_text('{"nodes":[{"unit_id":"stale"}]}',encoding='utf-8')
    (old_run/'annual_summary.json').write_text('{"feed_processed":{"value":999999}}',encoding='utf-8')
    stale_plots=old_run/'plots'
    stale_plots.mkdir()
    (stale_plots/'SEASONAL-STALE.json').write_text('{"series":[{"y":[999999]}]}',encoding='utf-8')

    status,units=invoke(app,'GET',f'/api/v1/simulations/{old_run_id}/units')
    assert status==404
    assert units['error']['code']=='run_not_found'

    status,utilities=invoke(app,'GET',f'/api/v1/simulations/{old_run_id}/utilities')
    assert status==404
    assert utilities['error']['code']=='run_not_found'

    for resource in ('graph','annual-summary','validation'):
        status,response=invoke(app,'GET',f'/api/v1/simulations/{old_run_id}/{resource}')
        assert status==404
        assert response['error']['code']=='run_not_found'

    status,plot=invoke(app,'GET',f'/api/v1/simulations/{old_run_id}/plots/SEASONAL-STALE')
    assert status==404
    assert plot['error']['code']=='run_not_found'

    status,artifact=invoke(app,'GET',f'/api/v1/simulations/{old_run_id}/artifacts/units.json')
    assert status==404
    assert artifact['error']['code']=='run_not_found'

    status,analysis=invoke(app,'GET',f'/api/v1/decision-support/runs/{old_run_id}')
    assert status==404
    assert analysis['error']['code']=='run_not_found'


def test_dynamic_complete_endpoints_are_opt_in_json_safe(tmp_path):
    app = create_app(tmp_path)
    for endpoint in ("options", "default-summary", "assumptions"):
        status, data = invoke(app, "GET", f"/api/v1/dynamic-complete/{endpoint}")
        assert status == 200
        encoded = json.dumps(data, allow_nan=False)
        assert not re.search(r"\b[A-Za-z]:[\\/]", encoded)
        if endpoint == "default-summary":
            assert data["readiness"]["validated_simulation_ready"] is False
            assert data["biomass_schedule"]["annual_processed_tonnes"] == pytest.approx(30000)
            assert data["analysis"]["proxy_analysis_ready"] is True
    status, strict = invoke(app, "POST", "/api/v1/dynamic-complete/scenario-summary", {"scenario": {"allow_assumptions": False, "active_months": [5]}})
    assert status == 200
    assert strict["blockers_count"] > 0
    assert strict["analysis"]["proxy_analysis_ready"] is False
    for payload in ({"scenario": {"protein_method": "heat"}}, {"scenario": {"gas_route": ["psa", "mea"]}}, {"scenario": {"include_press_cake_in_ad": True}}, {"scenario": None}):
        status, data = invoke(app, "POST", "/api/v1/dynamic-complete/scenario-summary", payload)
        assert status == 422
        assert data["error"]["message"]


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


def invoke_bytes(app, method: str, path: str):
    captured = {}

    def start_response(status, headers):
        captured["status"] = int(status.split()[0])
        captured["headers"] = dict(headers)

    environ = {
        "REQUEST_METHOD": method,
        "PATH_INFO": path,
        "QUERY_STRING": "",
        "CONTENT_LENGTH": "0",
        "wsgi.input": BytesIO(),
    }
    encoded = b"".join(app(environ, start_response))
    return captured["status"], captured["headers"], encoded


def request_payload(**updates):
    payload = {
        "schema_version": "1.0.0",
        "request_id": "api-test-request",
        "project_id": "api-test-project",
        "calculation_mode": "structural",
        "resolution_mode": "steady_state",
        "selected_month": "July",
        "scenarios": {
            "feed_preparation": "F1",
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
    assert result["summary_kpis"]["boundary_inlet_mass"]["value"] == pytest.approx(409.9083178971942)
    assert result["summary_kpis"]["boundary_outlet_mass"]["value"] == pytest.approx(409.9083179012139)
    run_id = result["run_id"]

    for resource in (
        "status", "summary", "process-areas", "streams", "units", "balances",
        "utilities", "validation", "graph", "plots", "provenance", "exports",
        "annual-summary",
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

    annual_status, annual = invoke(app, "GET", f"/api/v1/simulations/{run_id}/annual-summary")
    assert annual_status == 200
    assert annual["method"] == "steady_state_annualization"
    assert annual["period"]["operating_hours"] == 8760.0
    assert annual["feed_processed"]["value"] == pytest.approx(
        next(s for s in result['streams'] if 'feed' in s['aliases'])['total_mass']['value'] * 8760.0
    )
    assert annual["products"]["dry_protein_product"]["unit"] == "kg/year"
    assert annual["utilities"]["electricity"]["unit"] == "kWh/year"
    assert annual["balance"]["passed"] is True

    exports_status, exports = invoke(app, "GET", f"/api/v1/simulations/{run_id}/exports")
    assert exports_status == 200
    assert exports["annual_summary"] == "annual_summary.json"
    file_status, headers, contents = invoke_bytes(
        app, "GET", f"/api/v1/simulations/{run_id}/artifacts/annual_summary.json"
    )
    assert file_status == 200
    assert headers["Content-Disposition"] == 'attachment; filename="annual_summary.json"'
    assert json.loads(contents)["method"] == "steady_state_annualization"

    missing_status, missing = invoke(app, "GET", f"/api/v1/simulations/{run_id}/artifacts/../simulation_request.json")
    assert missing_status == 404
    assert missing["error"]["code"] == "artifact_not_found"


def test_empirical_annual_reporting_exposes_shared_schedule_and_chart_contract(tmp_path):
    app = create_app(tmp_path)
    payload = request_payload(
        resolution_mode="quasi_dynamic",
        selected_month="July",
        start_date="2026-01-01",
        end_date="2026-12-31",
        time_step="monthly",
        annual_biomass_target=30_000_000,
        biomass_schedule={
            "annual_available_biomass_tonnes": 30000,
            "annual_processed_biomass_tonnes": 30000,
            "collection_refinery_fraction": 1.0,
            "feed_basis": "tonnes_per_year",
            "feed_kg_per_hr": 10000,
            "season_start": "2026-04-15",
            "season_end": "2026-11-15",
            "peak_date": "2026-07-31",
            "spread_days": 55,
            "active_months": list(range(1, 13)),
        },
    )
    status, result = invoke(app, "POST", "/api/v1/simulations", payload)
    assert status == 201
    annual_status, annual = invoke(
        app, "GET", f'/api/v1/simulations/{result["run_id"]}/annual-summary'
    )
    assert annual_status == 200
    schedule = annual["biomass_schedule"]
    assert schedule["annual_available_tonnes"] == pytest.approx(30000)
    assert schedule["annual_processed_tonnes"] == pytest.approx(result['seasonal_summary']['total_biomass_processed_kg']/1000)
    assert sum(r['planned_processed_biomass_tonnes'] for r in schedule['monthly']) == pytest.approx(30000)
    assert schedule['ending_inventory_tonnes'] == pytest.approx(result['seasonal_summary']['final_inventory_kg']/1000)
    assert annual['reporting_status']['validated_simulation_ready'] is False
    assert schedule["policy_id"] == "shared_normal_supply_monthly_cap_v1"
    assert len(schedule["monthly"]) == 12
    assert {
        "schedule", "bulk_streams", "small_products", "biomethane", "energy",
        "mass_balance", "annual_product_mix", "groups",
    } <= annual["chart_data"].keys()
    assert annual["chart_data"]["groups"]["large_mass"] == [
        "feed_processed_tonnes", "press_cake_tonnes", "juice_tonnes", "digestate_tonnes"
    ]
    assert "protein_tonnes" in annual["chart_data"]["groups"]["small_products"]
    assert annual["chart_contract"]["electricity"] == "kWh per actual model timestep"
    assert annual["chart_contract"]["heat"] == "kWh per actual model timestep"
    assert annual["display_utilities"]["electricity"]["unit"] == "MWh/year"
    assert annual["display_utilities"]["heating"]["unit"] == "GJ/year"
    assert [stage["stage_id"] for stage in annual["process_pathway"]] == [
        "feed", "pretreatment", "protein", "ad", "gas", "nutrients"
    ]
    assert annual["reporting_status"]["model"] == "empirical"
    assert not re.search(r"[A-Za-z]:[\\/]", json.dumps(annual, allow_nan=False))


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


def test_feedstock_resolution_readiness_endpoint_is_json_safe(tmp_path):
    app = create_app(tmp_path)
    status, response = invoke(app, "GET", "/api/v1/feedstock-resolution/readiness")

    assert status == 200
    assert response["category_counts"]["resolvable_now"] >= 1
    assert "blocked_missing" in response["blocked_category_counts"]
    assert "requires_user_selection" in response["category_counts"]
    assert response["artifact_names"] == {
        "csv": "Greenhub/results/feedstock_resolution_gates.csv",
        "markdown": "docs/feedstock_resolution_readiness.md",
    }
    assert response["top_resolvable_fields"]
    assert not re.search(r"[A-Za-z]:[\\/]", json.dumps(response, allow_nan=False))
