"""Dependency-light WSGI adapter for the transport-neutral GreenHub services."""

from __future__ import annotations

import json
import mimetypes
import re
from dataclasses import dataclass
from io import BytesIO
from pathlib import Path
from typing import Callable, Iterable, Mapping
from urllib.parse import parse_qs, unquote

from Greenhub.application import (
    ParameterService,
    ResultService,
    RunRepository,
    ScenarioService,
    SimulationService,
)
from Greenhub.application.contracts import SCHEMA_VERSION, ScenarioSelection, SimulationRequest
from Greenhub.application.errors import (
    GreenHubApplicationError,
    RequestValidationError,
    RunNotFoundError,
    RunStateError,
)
from Greenhub.application.schema_export import openapi_schema
from Greenhub.parameters import CalculationMode, ParameterOverride, ResolutionMode
from Greenhub.parameters.serialization import to_json_compatible
from Greenhub.scientific_equations import EQUATION_REGISTRY


MAX_REQUEST_BYTES = 2 * 1024 * 1024
API_VERSION = "v1"
_WINDOWS_ABSOLUTE_PATH = re.compile(r"\b[A-Za-z]:[\\/]")


@dataclass(frozen=True)
class APIError(Exception):
    status: int
    code: str
    message: str
    details: tuple[object, ...] = ()


@dataclass(frozen=True)
class FileResponse:
    path: Path
    download_name: str


class GreenHubAPI:
    """WSGI application that delegates all scientific work to application services."""

    def __init__(self, run_root: Path | None = None) -> None:
        self.repository = RunRepository()
        self.simulations = SimulationService(self.repository, run_root=run_root)
        self.parameters: ParameterService = self.simulations.parameters
        self.scenarios: ScenarioService = self.simulations.scenarios
        self.results = ResultService(self.repository)
        self.graphs = self.simulations.graphs
        self.plots = self.simulations.plots

    def __call__(self, environ: Mapping[str, object], start_response: Callable) -> Iterable[bytes]:
        try:
            method = str(environ.get("REQUEST_METHOD", "GET")).upper()
            path = unquote(str(environ.get("PATH_INFO", "/"))).rstrip("/") or "/"
            if method == "OPTIONS":
                return self._respond(start_response, 200, {"status": "ok"})
            payload = self._dispatch(method, path, environ)
            if isinstance(payload, FileResponse):
                return self._respond_file(start_response, payload)
            status = 201 if method == "POST" and path in {"/api/v1/simulations", "/api/v1/feed-profiles"} else 200
            return self._respond(start_response, status, payload)
        except APIError as error:
            return self._respond(start_response, error.status, self._error_payload(error))
        except RunNotFoundError as error:
            return self._respond(start_response, 404, self._error_payload(APIError(404, error.code, str(error))))
        except RequestValidationError as error:
            return self._respond(start_response, 422, self._error_payload(APIError(422, error.code, str(error))))
        except RunStateError as error:
            return self._respond(start_response, 409, self._error_payload(APIError(409, error.code, str(error))))
        except (KeyError, TypeError, ValueError) as error:
            message = str(error).strip("'") or "The request is invalid."
            return self._respond(start_response, 422, self._error_payload(APIError(422, "invalid_request", message)))
        except GreenHubApplicationError as error:
            return self._respond(start_response, 400, self._error_payload(APIError(400, error.code, str(error))))
        except Exception:
            return self._respond(
                start_response,
                500,
                self._error_payload(APIError(500, "internal_error", "The simulation service could not complete the request.")),
            )

    def _dispatch(self, method: str, path: str, environ: Mapping[str, object]) -> object:
        if path.startswith("/api/v1/dynamic-complete/"):
            # Lazy opt-in import: empirical endpoints keep their existing execution path.
            from Greenhub.application.dynamic_complete_reporting_service import (
                build_scenario_summary, default_summary, reporting_options,
            )
            if method == "GET" and path == "/api/v1/dynamic-complete/default-summary":
                return default_summary()
            if method == "GET" and path == "/api/v1/dynamic-complete/options":
                return reporting_options()
            if method == "GET" and path == "/api/v1/dynamic-complete/assumptions":
                report = default_summary()
                return {key: report[key] for key in ("assumptions", "assumption_counts", "top_assumptions", "readiness")} | {"analysis_assumptions": report["analysis"]["assumptions"]}
            if method == "POST" and path == "/api/v1/dynamic-complete/scenario-summary":
                payload = dict(self._read_json(environ))
                if set(payload) - {"scenario", "analysis_factors"}:
                    raise ValueError("Use a scenario object and optional analysis_factors object.")
                if not isinstance(payload.get("scenario"), dict):
                    raise ValueError("scenario is required (use {} for baseline).")
                return build_scenario_summary(payload["scenario"], payload.get("analysis_factors"))
        if method == "GET" and path == "/api/v1/health":
            return {"status": "ok", "api_version": API_VERSION, "schema_version": SCHEMA_VERSION}
        if method == "GET" and path == "/api/v1/openapi.json":
            return openapi_schema()
        if method == "GET" and path == "/api/v1/model/info":
            return self._model_info()
        if method == "GET" and path == "/api/v1/feedstock-resolution/readiness":
            return self.results.get_feedstock_resolution_readiness()
        if method == "GET" and path == "/api/v1/scenarios":
            return self.scenarios.list_scenarios()
        if method == "GET" and path == "/api/v1/process-areas":
            return self.scenarios.list_process_areas()
        if method == "GET" and path == "/api/v1/feed-profiles":
            return self.simulations.feed_profiles.list_profiles()
        if method == "POST" and path == "/api/v1/feed-profiles":
            return self.simulations.feed_profiles.register_mapping(dict(self._read_json(environ))).metadata()
        if method == "GET" and path == "/api/v1/parameters":
            return self._list_parameters(environ)
        if method == "POST" and path == "/api/v1/parameters/validate":
            return self._validate_parameter(self._read_json(environ))
        if method == "POST" and path == "/api/v1/simulations":
            request = SimulationRequest.from_dict(self._read_json(environ))
            run_id = self.simulations.create_run(request)
            return self.simulations.execute_run(run_id)
        parameter_match = re.fullmatch(r"/api/v1/parameters/([^/]+)", path)
        if method == "GET" and parameter_match:
            parameter_id = parameter_match.group(1)
            try:
                parameter = self.parameters.get_parameter(parameter_id)
            except KeyError as error:
                raise APIError(404, "parameter_not_found", f"Unknown parameter '{parameter_id}'.") from error
            return {
                "parameter": parameter,
                "sources": self.parameters.list_parameter_sources(parameter_id),
            }
        plot_match = re.fullmatch(r"/api/v1/simulations/([a-f0-9]+)/plots/([^/]+)", path)
        if method == "GET" and plot_match:
            try:
                return self.plots.get_plot_data(*plot_match.groups())
            except KeyError as error:
                raise APIError(404, "plot_not_found", str(error).strip("'")) from error
        artifact_match = re.fullmatch(r"/api/v1/simulations/([a-f0-9]+)/artifacts/(.+)", path)
        if method == "GET" and artifact_match:
            return self._artifact(*artifact_match.groups())
        run_match = re.fullmatch(r"/api/v1/simulations/([a-f0-9]+)/([^/]+)", path)
        if method == "GET" and run_match:
            return self._run_resource(*run_match.groups())
        if path.startswith("/api/v1/"):
            raise APIError(405, "method_not_allowed", f"No {method} operation is defined for '{path}'.")
        raise APIError(404, "route_not_found", "The requested API route does not exist.")

    def _model_info(self) -> dict[str, object]:
        return {
            "model": "GreenHub BioSTEAM scientific process model",
            "api_version": API_VERSION,
            "request_schema_version": SCHEMA_VERSION,
            "calculation_modes": tuple(item.value for item in CalculationMode),
            "resolution_modes": tuple(item.value for item in ResolutionMode),
            "parameter_count": len(self.parameters.registry),
            "active_equation_ids": tuple(
                item.equation_id
                for item in EQUATION_REGISTRY.values()
                if item.activation_status == "active"
            ),
            "execution_model": "synchronous isolated run",
            "scientific_core": "transport-neutral",
        }

    def _default_request(self, **changes: object) -> SimulationRequest:
        values = {
            "schema_version": SCHEMA_VERSION,
            "request_id": "parameter-discovery",
            "project_id": "greenhub",
        }
        values.update(changes)
        return SimulationRequest(**values)

    def _list_parameters(self, environ: Mapping[str, object]) -> tuple[object, ...]:
        query = parse_qs(str(environ.get("QUERY_STRING", "")), keep_blank_values=False)
        mode = CalculationMode(query.get("calculation_mode", ["structural"])[0])
        month = query.get("selected_month", ["July"])[0]
        request = self._default_request(calculation_mode=mode, selected_month=month)
        controls = self.parameters.list_editable_parameters(request)
        process_area = query.get("process_area", [None])[0]
        if process_area is None:
            return controls
        definitions = {item.parameter_id: item for item in self.parameters.list_parameters({"process_area": process_area})}
        return tuple(item for item in controls if item.parameter_id in definitions)

    def _validate_parameter(self, payload: Mapping[str, object]) -> dict[str, object]:
        if "simulation_request" in payload:
            request = SimulationRequest.from_dict(payload["simulation_request"])
        else:
            parameter_id = str(payload.get("parameter_id", ""))
            if not parameter_id or "value" not in payload:
                raise ValueError("parameter_id and value are required.")
            scenario_payload = payload.get("scenarios") or {}
            override = ParameterOverride(
                parameter_id=parameter_id,
                value=payload["value"],
                unit=payload.get("unit"),
                reason=payload.get("reason"),
            )
            request = self._default_request(
                calculation_mode=CalculationMode(payload.get("calculation_mode", "structural")),
                selected_month=payload.get("selected_month", "July"),
                scenarios=ScenarioSelection(**dict(scenario_payload)),
                design_overrides=(override,),
            )
        issues = self.simulations.validate_request(request)
        resolved = () if any(item.blocking for item in issues) else self.parameters.resolve_parameters(request)
        selected_ids = {item.parameter_id for item in request.all_overrides}
        selected = tuple(item for item in resolved if item.parameter_id in selected_ids)
        return {
            "valid": not any(item.blocking for item in issues),
            "issues": issues,
            "resolved_parameters": selected,
        }

    def _run_resource(self, run_id: str, resource: str) -> object:
        context = self.repository.get(run_id)
        resources = {
            "status": lambda: self.simulations.get_run_status(run_id),
            "summary": lambda: self.results.get_summary(run_id),
            "process-areas": lambda: self.results.get_process_areas(run_id),
            "streams": lambda: self.results.get_streams(run_id),
            "units": lambda: self.results.get_units(run_id),
            "balances": lambda: self.results.get_balances(run_id),
            "utilities": lambda: self.results.get_utilities(run_id),
            "validation": lambda: self.results.get_validation(run_id),
            "graph": lambda: self.graphs.get_process_graph(run_id),
            "plots": lambda: self.plots.list_plots(run_id),
            "provenance": lambda: self.results.get_provenance(run_id),
            "exports": lambda: self.results.get_exports(run_id),
            "time-series": lambda: self.results.get_time_series(run_id),
            "inventory": lambda: self.results.get_inventory(run_id),
            "utilization": lambda: self.results.get_utilization(run_id),
            "seasonal-summary": lambda: self.results.get_seasonal_summary(run_id),
            "annual-summary": lambda: self.results.get_annual_summary(run_id),
        }
        try:
            return resources[resource]()
        except KeyError as error:
            raise APIError(404, "resource_not_found", f"Unknown simulation resource '{resource}'.") from error

    def _artifact(self, run_id: str, reference: str) -> FileResponse:
        context = self.repository.get(run_id)
        if context.result is None:
            raise RunStateError(f"Run '{run_id}' has no completed result.")
        allowed = set(context.result.export_references.values())
        if reference not in allowed:
            raise APIError(404, "artifact_not_found", "The requested run artifact is not available.")
        root = context.run_directory.resolve()
        candidate = (root / reference).resolve()
        if root not in candidate.parents or not candidate.is_file():
            raise APIError(404, "artifact_not_found", "The requested run artifact is not available.")
        return FileResponse(candidate, candidate.name)

    @staticmethod
    def _read_json(environ: Mapping[str, object]) -> Mapping[str, object]:
        try:
            length = int(environ.get("CONTENT_LENGTH") or 0)
        except (TypeError, ValueError) as error:
            raise APIError(400, "invalid_content_length", "CONTENT_LENGTH must be an integer.") from error
        if length <= 0:
            raise APIError(400, "empty_request_body", "A JSON request body is required.")
        if length > MAX_REQUEST_BYTES:
            raise APIError(413, "request_too_large", "The JSON request body exceeds 2 MiB.")
        stream = environ.get("wsgi.input")
        if not hasattr(stream, "read"):
            stream = BytesIO()
        try:
            payload = json.loads(stream.read(length).decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as error:
            raise APIError(400, "invalid_json", "The request body is not valid UTF-8 JSON.") from error
        if not isinstance(payload, dict):
            raise APIError(422, "invalid_request", "The JSON request body must be an object.")
        return payload

    @staticmethod
    def _error_payload(error: APIError) -> dict[str, object]:
        return {
            "error": {
                "code": error.code,
                "message": error.message,
                "status": error.status,
                "details": error.details,
            }
        }

    @staticmethod
    def _respond(start_response: Callable, status: int, payload: object) -> list[bytes]:
        value = to_json_compatible(payload)
        encoded = json.dumps(value, sort_keys=True, allow_nan=False).encode("utf-8")
        if _WINDOWS_ABSOLUTE_PATH.search(encoded.decode("utf-8")):
            encoded = json.dumps(
                GreenHubAPI._error_payload(APIError(500, "unsafe_response", "A local path was removed from the response.")),
                sort_keys=True,
            ).encode("utf-8")
            status = 500
        status_line = {
            200: "200 OK", 201: "201 Created", 400: "400 Bad Request", 404: "404 Not Found",
            405: "405 Method Not Allowed", 409: "409 Conflict", 413: "413 Payload Too Large",
            422: "422 Unprocessable Entity", 500: "500 Internal Server Error",
        }[status]
        start_response(status_line, [
            ("Content-Type", "application/json; charset=utf-8"),
            ("Content-Length", str(len(encoded))),
            ("Access-Control-Allow-Origin", "*"),
            ("Access-Control-Allow-Headers", "Content-Type, Authorization"),
            ("Access-Control-Allow-Methods", "GET, POST, OPTIONS"),
        ])
        return [encoded]

    @staticmethod
    def _respond_file(start_response: Callable, response: FileResponse) -> list[bytes]:
        encoded = response.path.read_bytes()
        content_type = mimetypes.guess_type(response.download_name)[0] or "application/octet-stream"
        start_response("200 OK", [
            ("Content-Type", content_type),
            ("Content-Length", str(len(encoded))),
            ("Content-Disposition", f'attachment; filename="{response.download_name}"'),
            ("Access-Control-Allow-Origin", "*"),
            ("Access-Control-Allow-Methods", "GET, POST, OPTIONS"),
        ])
        return [encoded]


def create_app(run_root: Path | None = None) -> GreenHubAPI:
    return GreenHubAPI(run_root=run_root)


application = create_app()
