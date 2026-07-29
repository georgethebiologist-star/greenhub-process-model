"""Machine-readable schemas and field catalogs for GreenHub clients."""

from __future__ import annotations

import csv
from copy import deepcopy
from pathlib import Path

from Greenhub.parameters.serialization import write_json


ADVANCED_MODEL_DIR = Path(__file__).resolve().parents[1] / "data" / "advanced_model"


PARAMETER_OVERRIDE_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "required": ["parameter_id", "value"],
    "properties": {
        "parameter_id": {"type": "string", "minLength": 1},
        "value": {"type": ["number", "string", "boolean"]},
        "unit": {"type": ["string", "null"]},
        "reason": {"type": ["string", "null"]},
        "requester": {"type": ["string", "null"]},
        "provenance_note": {"type": ["string", "null"]},
        "rebuild_required": {"type": ["boolean", "null"]},
        "timestamp": {"type": ["string", "null"]},
    },
}

SCENARIO_SELECTION_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "feed_preparation": {"type": "string", "default": "F2"},
        "protein_recovery": {"type": "string", "default": "PR3"},
        "anaerobic_digestion": {"type": "string", "default": "AD1"},
        "biogas_upgrading": {"type": "string", "default": "BG2"},
        "nutrient_recovery": {"type": "string", "default": "NR4"},
        "process_order": {"type": "string", "enum": ["A", "B", "C", "D"], "default": "A"},
    },
}

SIMULATION_REQUEST_SCHEMA = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "$id": "simulation_request.schema.json",
    "title": "GreenHub SimulationRequest",
    "type": "object",
    "additionalProperties": False,
    "required": ["schema_version", "request_id", "project_id"],
    "properties": {
        "schema_version": {"const": "1.0.0"},
        "request_id": {"type": "string", "minLength": 1},
        "project_id": {"type": "string", "minLength": 1},
        "calculation_mode": {
            "type": "string",
            "enum": ["structural", "literature_default", "project_data", "calibrated", "expert_override"],
            "default": "structural",
        },
        "resolution_mode": {
            "type": "string",
            "enum": ["steady_state", "monthly_independent", "quasi_dynamic", "dynamic"],
            "default": "steady_state",
        },
        "selected_month": {"type": ["string", "null"], "default": "July"},
        "time_horizon": {
            "type": ["array", "null"],
            "prefixItems": [{"type": "string"}, {"type": "string"}],
            "minItems": 2,
            "maxItems": 2,
        },
        "scenarios": {"$ref": "#/$defs/scenario_selection"},
        "feed_overrides": {"$ref": "#/$defs/parameter_overrides"},
        "operating_overrides": {"$ref": "#/$defs/parameter_overrides"},
        "design_overrides": {"$ref": "#/$defs/parameter_overrides"},
        "expert_scientific_overrides": {"$ref": "#/$defs/parameter_overrides"},
        "requested_outputs": {
            "type": "array",
            "items": {
                "type": "object",
                "additionalProperties": False,
                "required": ["output_id"],
                "properties": {
                    "output_id": {"type": "string"},
                    "detail_level": {"type": "string", "default": "summary"},
                },
            },
        },
        "requested_plots": {
            "type": "array",
            "items": {
                "type": "object",
                "additionalProperties": False,
                "required": ["plot_id"],
                "properties": {
                    "plot_id": {"type": "string"},
                    "formats": {
                        "type": "array",
                        "items": {"type": "string", "enum": ["json", "csv", "png", "svg"]},
                    },
                },
            },
        },
        "export_formats": {
            "type": "array",
            "items": {"type": "string", "enum": ["json", "csv"]},
        },
        "strict_validation": {"type": "boolean", "default": True},
        "user_notes": {"type": ["string", "null"]},
    },
    "$defs": {
        "scenario_selection": SCENARIO_SELECTION_SCHEMA,
        "parameter_override": PARAMETER_OVERRIDE_SCHEMA,
        "parameter_overrides": {
            "type": "array",
            "items": {"$ref": "#/$defs/parameter_override"},
        },
    },
}

NUMERICAL_VALUE_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "required": ["value", "unit", "basis", "status", "origin", "warning", "uncertainty"],
    "properties": {
        "value": {"type": ["number", "integer", "null"]},
        "unit": {"type": ["string", "null"]},
        "basis": {"type": ["string", "null"]},
        "status": {"type": "string"},
        "origin": {"type": "string"},
        "warning": {"type": ["string", "null"]},
        "uncertainty": {"type": ["object", "null"]},
    },
}

PROCESS_GRAPH_SCHEMA = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "$id": "process_graph_schema.json",
    "title": "GreenHub ProcessGraph",
    "type": "object",
    "additionalProperties": False,
    "required": ["schema_version", "run_id", "nodes", "edges"],
    "properties": {
        "schema_version": {"const": "1.0.0"},
        "run_id": {"type": "string"},
        "nodes": {
            "type": "array",
            "items": {
                "type": "object",
                "required": ["node_id", "unit_id", "display_name", "process_area", "active", "calculation_mode"],
                "properties": {
                    "node_id": {"type": "string"},
                    "unit_id": {"type": "string"},
                    "display_name": {"type": "string"},
                    "process_area": {"type": "string"},
                    "technology": {"type": ["string", "null"]},
                    "active": {"type": "boolean"},
                    "calculation_mode": {"type": "string"},
                    "model_maturity": {"type": "string"},
                    "warning_count": {"type": "integer", "minimum": 0},
                    "key_kpis": {"type": "object"},
                    "dashboard_group": {"type": "string"},
                },
            },
        },
        "edges": {
            "type": "array",
            "items": {
                "type": "object",
                "required": ["edge_id", "stream_id", "source_node", "target_node", "mass_flow", "phase", "active"],
                "properties": {
                    "edge_id": {"type": "string"},
                    "stream_id": {"type": "string"},
                    "source_node": {"type": ["string", "null"]},
                    "target_node": {"type": ["string", "null"]},
                    "mass_flow": {"$ref": "#/$defs/numerical_value"},
                    "phase": {"type": "string"},
                    "principal_components": {"type": "array", "items": {"type": "string"}},
                    "classification": {"type": "string"},
                    "active": {"type": "boolean"},
                    "warnings": {"type": "array", "items": {"type": "string"}},
                },
            },
        },
    },
    "$defs": {"numerical_value": NUMERICAL_VALUE_SCHEMA},
}

SIMULATION_RESULT_SCHEMA = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "$id": "simulation_result.schema.json",
    "title": "GreenHub SimulationResult",
    "type": "object",
    "additionalProperties": False,
    "required": [
        "schema_version", "run_id", "request_id", "status", "selected_scenarios",
        "calculation_mode", "resolution_mode", "summary_kpis", "process_areas",
        "streams", "units", "products", "utilities", "balances", "validation",
        "resolved_parameters", "plots", "graph", "export_references",
    ],
    "properties": {
        "schema_version": {"const": "1.0.0"},
        "run_id": {"type": "string"},
        "request_id": {"type": "string"},
        "status": {"type": "string"},
        "selected_scenarios": SCENARIO_SELECTION_SCHEMA,
        "calculation_mode": {"type": "string"},
        "resolution_mode": {"type": "string"},
        "created_at": {"type": "string"},
        "completed_at": {"type": ["string", "null"]},
        "summary_kpis": {"type": "object", "additionalProperties": {"$ref": "#/$defs/numerical_value"}},
        "process_areas": {"type": "array", "items": {"type": "object"}},
        "streams": {"type": "array", "items": {"type": "object"}},
        "units": {"type": "array", "items": {"type": "object"}},
        "products": {"type": "array", "items": {"type": "object"}},
        "utilities": {"type": "array", "items": {"type": "object"}},
        "balances": {"type": "array", "items": {"type": "object"}},
        "validation": {"type": "object"},
        "warnings": {"type": "array", "items": {"type": "string"}},
        "limitations": {"type": "array", "items": {"type": "string"}},
        "resolved_parameters": {"type": "array", "items": {"type": "object"}},
        "model_maturity": {"type": "object", "additionalProperties": {"type": "string"}},
        "dataset_readiness": {"type": "object", "additionalProperties": {"type": "integer"}},
        "plots": {"type": "array", "items": {"type": "object"}},
        "graph": {"$ref": "#/$defs/process_graph"},
        "export_references": {"type": "object", "additionalProperties": {"type": "string"}},
        "reproducibility_metadata": {"type": "object"},
    },
    "$defs": {
        "numerical_value": NUMERICAL_VALUE_SCHEMA,
        "process_graph": {key: value for key, value in PROCESS_GRAPH_SCHEMA.items() if key not in {"$schema", "$id", "$defs"}},
    },
}
SIMULATION_RESULT_SCHEMA["$defs"]["process_graph"]["$defs"] = {
    "numerical_value": NUMERICAL_VALUE_SCHEMA
}


RESULT_FIELDS = (
    ("summary_kpis", "object", None, "Compact run-level key performance indicators."),
    ("process_areas[]", "ProcessAreaResult", None, "Area membership, boundary streams, maturity, and metrics."),
    ("streams[].total_mass", "NumericalValue", "kg/hr", "Total wet stream mass flow."),
    ("streams[].components", "object<NumericalValue>", "kg/hr", "Component mass-flow mapping."),
    ("units[].power", "NumericalValue", "kW", "Unit electricity demand."),
    ("balances[].residual", "NumericalValue", "kg/hr or kmol/hr", "Signed outlet-minus-inlet residual."),
    ("products[].mass_flow", "NumericalValue", "kg/hr", "Product stream wet mass flow."),
    ("resolved_parameters[]", "ParameterResolutionResult", None, "Resolved value, source, status, and warnings."),
    ("validation", "ValidationSummary", None, "Blocking and warning validation findings."),
    ("graph", "ProcessGraph", None, "Frontend-ready unit and stream topology."),
    ("plots[]", "PlotSpecification", None, "Stable plot metadata and availability."),
    ("export_references", "object<string>", None, "Run-relative artifact references only."),
)


PLOT_CATALOG = (
    {"plot_id": "SYS-AREA-MASS", "process_area": "integrated_system", "x_unit": None, "y_unit": "kg/hr", "availability": "available"},
    {"plot_id": "VALIDATION-RESIDUALS", "process_area": "integrated_system", "x_unit": None, "y_unit": "kg/hr", "availability": "available"},
    {"plot_id": "SYS-UNIT-POWER", "process_area": "shared_utilities_and_supporting_operations", "x_unit": None, "y_unit": "kW", "availability": "available"},
    {"plot_id": "DATA-READINESS", "process_area": "data_governance", "x_unit": None, "y_unit": "count", "availability": "available"},
    {"plot_id": "PR-PRECIP-RECOVERY", "process_area": "protein_recovery", "x_unit": None, "y_unit": "fraction", "availability": "conditional: PR1 literature_default"},
)

PARAMETER_VALIDATION_REQUEST_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "required": ["parameter_id", "value"],
    "properties": {
        "parameter_id": {"type": "string", "minLength": 1},
        "value": {"type": ["number", "string", "boolean"]},
        "unit": {"type": ["string", "null"]},
        "reason": {"type": ["string", "null"]},
        "calculation_mode": {
            "type": "string",
            "enum": ["structural", "literature_default", "project_data", "calibrated", "expert_override"],
        },
        "selected_month": {"type": ["string", "null"]},
        "scenarios": SCENARIO_SELECTION_SCHEMA,
    },
}


def _component_schema(name: str, schema: dict[str, object]) -> dict[str, object]:
    value = deepcopy(schema)
    value.pop("$schema", None)
    value.pop("$id", None)

    def rewrite(item: object) -> object:
        if isinstance(item, dict):
            return {
                key: (
                    f"#/components/schemas/{name}/$defs/{child.removeprefix('#/$defs/')}"
                    if key == "$ref" and isinstance(child, str) and child.startswith("#/$defs/")
                    else rewrite(child)
                )
                for key, child in item.items()
            }
        if isinstance(item, list):
            return [rewrite(child) for child in item]
        return item

    return rewrite(value)


def openapi_schema() -> dict[str, object]:
    """Return the OpenAPI document used by the standard-library adapter."""
    paths: dict[str, object] = {}

    def add(
        path: str,
        method: str,
        operation_id: str,
        *,
        request_schema: str | None = None,
        response_schema: str | None = None,
        created: bool = False,
    ) -> None:
        operation: dict[str, object] = {
            "operationId": operation_id,
            "responses": {
                "201" if created else "200": {
                    "description": "Successful GreenHub response",
                    "content": {
                        "application/json": {
                            "schema": (
                                {"$ref": f"#/components/schemas/{response_schema}"}
                                if response_schema else {"type": ["object", "array"]}
                            )
                        }
                    },
                },
                "422": {"$ref": "#/components/responses/ValidationError"},
                "404": {"$ref": "#/components/responses/NotFound"},
            },
        }
        if request_schema:
            operation["requestBody"] = {
                "required": True,
                "content": {
                    "application/json": {
                        "schema": {"$ref": f"#/components/schemas/{request_schema}"}
                    }
                },
            }
        paths.setdefault(path, {})[method.lower()] = operation

    add("/api/v1/health", "GET", "health")
    add("/api/v1/model/info", "GET", "modelInfo")
    add("/api/v1/scenarios", "GET", "listScenarios")
    add("/api/v1/process-areas", "GET", "listProcessAreas")
    add("/api/v1/parameters", "GET", "listParameters")
    add("/api/v1/parameters/{parameter_id}", "GET", "getParameter")
    add(
        "/api/v1/parameters/validate", "POST", "validateParameter",
        request_schema="ParameterValidationRequest",
    )
    add(
        "/api/v1/simulations", "POST", "createSimulation",
        request_schema="SimulationRequest", response_schema="SimulationResult", created=True,
    )
    for suffix, operation in (
        ("status", "getSimulationStatus"), ("summary", "getSimulationSummary"),
        ("process-areas", "getSimulationProcessAreas"), ("streams", "getSimulationStreams"),
        ("units", "getSimulationUnits"), ("balances", "getSimulationBalances"),
        ("utilities", "getSimulationUtilities"), ("validation", "getSimulationValidation"),
        ("graph", "getSimulationGraph"), ("plots", "listSimulationPlots"),
        ("provenance", "getSimulationProvenance"), ("exports", "getSimulationExports"),
    ):
        add(f"/api/v1/simulations/{{run_id}}/{suffix}", "GET", operation)
    add("/api/v1/simulations/{run_id}/graph", "GET", "getSimulationGraph", response_schema="ProcessGraph")
    add("/api/v1/simulations/{run_id}/plots/{plot_id}", "GET", "getSimulationPlot")
    add("/api/v1/openapi.json", "GET", "openApiDocument")
    for path, methods in paths.items():
        parameters = []
        if "{run_id}" in path:
            parameters.append({"name": "run_id", "in": "path", "required": True, "schema": {"type": "string"}})
        if "{parameter_id}" in path:
            parameters.append({"name": "parameter_id", "in": "path", "required": True, "schema": {"type": "string"}})
        if "{plot_id}" in path:
            parameters.append({"name": "plot_id", "in": "path", "required": True, "schema": {"type": "string"}})
        if parameters:
            for operation in methods.values():
                operation["parameters"] = parameters
    return {
        "openapi": "3.1.0",
        "info": {"title": "GreenHub Scientific Model API", "version": "1.0.0"},
        "servers": [{"url": "/"}],
        "paths": paths,
        "components": {
            "schemas": {
                "SimulationRequest": _component_schema("SimulationRequest", SIMULATION_REQUEST_SCHEMA),
                "SimulationResult": _component_schema("SimulationResult", SIMULATION_RESULT_SCHEMA),
                "ProcessGraph": _component_schema("ProcessGraph", PROCESS_GRAPH_SCHEMA),
                "ParameterValidationRequest": PARAMETER_VALIDATION_REQUEST_SCHEMA,
                "Error": {
                    "type": "object",
                    "required": ["error"],
                    "properties": {
                        "error": {
                            "type": "object",
                            "required": ["code", "message", "status", "details"],
                            "properties": {
                                "code": {"type": "string"}, "message": {"type": "string"},
                                "status": {"type": "integer"}, "details": {"type": "array"},
                            },
                        }
                    },
                },
            },
            "responses": {
                "ValidationError": {"description": "Invalid request", "content": {"application/json": {"schema": {"$ref": "#/components/schemas/Error"}}}},
                "NotFound": {"description": "Resource not found", "content": {"application/json": {"schema": {"$ref": "#/components/schemas/Error"}}}},
            },
        },
    }


def export_machine_contracts(output_dir: Path = ADVANCED_MODEL_DIR) -> tuple[Path, ...]:
    """Write deterministic API/frontend contract artifacts."""
    output_dir.mkdir(parents=True, exist_ok=True)
    outputs = [
        write_json(output_dir / "simulation_request.schema.json", SIMULATION_REQUEST_SCHEMA),
        write_json(output_dir / "simulation_result.schema.json", SIMULATION_RESULT_SCHEMA),
        write_json(output_dir / "process_graph_schema.json", PROCESS_GRAPH_SCHEMA),
        write_json(output_dir / "plot_manifest.json", PLOT_CATALOG),
        write_json(output_dir / "openapi.json", openapi_schema()),
    ]
    field_path = output_dir / "result_field_dictionary.csv"
    with field_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(("field_path", "data_type", "unit", "description"))
        writer.writerows(RESULT_FIELDS)
    outputs.append(field_path)
    return tuple(outputs)


def main() -> None:
    for path in export_machine_contracts():
        print(path)


if __name__ == "__main__":
    main()
