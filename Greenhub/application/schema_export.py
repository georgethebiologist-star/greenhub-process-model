"""Machine-readable schemas and field catalogs for GreenHub clients."""

from __future__ import annotations

import csv
from copy import deepcopy
from pathlib import Path

from Greenhub.parameters.serialization import write_json
from .contracts.requests import (
    FEED_COMPOSITION_MAX_TOTAL,
    FEED_COMPOSITION_MIN_TOTAL,
    FEED_COMPOSITION_NORMALIZED_TOTAL,
)


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
        "feed_preparation": {"type": "string", "default": "F1"},
        "protein_recovery": {"type": "string", "default": "PR3"},
        "anaerobic_digestion": {"type": "string", "default": "AD1"},
        "biogas_upgrading": {"type": "string", "default": "BG2"},
        "nutrient_recovery": {"type": "string", "default": "NR4"},
        "process_order": {"type": "string", "enum": ["A", "B", "C", "D"], "default": "A"},
    },
}

OPERATING_SCHEDULE_SCHEMA = {
    "type": ["object", "null"],
    "additionalProperties": False,
    "properties": {
        "operating_days_per_week": {"type": ["number", "null"], "minimum": 0, "maximum": 7},
        "operating_hours_per_day": {"type": ["number", "null"], "minimum": 0, "maximum": 24},
        "target_throughput_kg_hr": {"type": ["number", "null"], "minimum": 0},
        "operating_dates": {"type": "array", "items": {"type": "string", "format": "date"}},
        "shutdown_dates": {"type": "array", "items": {"type": "string", "format": "date"}},
    },
}

BIOMASS_SCHEDULE_SCHEMA = {
    "type": ["object", "null"],
    "additionalProperties": False,
    "properties": {
        "annual_available_biomass_tonnes": {"type": "number", "minimum": 0, "default": 30000},
        "annual_processed_biomass_tonnes": {"type": "number", "minimum": 0, "default": 30000},
        "processing_delay_days": {"type": "integer", "minimum": 0, "maximum": 365, "default": 14},
        "collection_refinery_fraction": {"type": "number", "minimum": 0, "maximum": 1, "default": 1},
        "feed_basis": {"type": "string", "enum": ["tonnes_per_year", "kg_per_hr"]},
        "feed_kg_per_hr": {"type": "number", "minimum": 0},
        "season_start": {"type": "string", "format": "date"},
        "season_end": {"type": "string", "format": "date"},
        "peak_date": {"type": "string", "format": "date"},
        "spread_days": {"type": "number", "minimum": 1, "maximum": 366},
        "active_months": {"type": "array", "items": {"type": "integer", "minimum": 1, "maximum": 12}, "uniqueItems": True},
    },
}

BIOSTIMULANT_ROUTE_SCHEMA = {
    "type": ["object", "null"],
    "additionalProperties": False,
    "required": ["technology_id", "retention_matrix_source"],
    "oneOf": [
        {"required": ["flux_L_m2_h", "flux_source"]},
        {"required": ["feed_to_reference_concentration_ratio", "flux_model_source", "transmembrane_pressure_bar", "pressure_source", "viscosity_Pa_s", "viscosity_source"]},
    ],
    "properties": {
        "technology_id": {"type": "string", "enum": ["TUF", "LNF", "MEUF"]},
        "flux_L_m2_h": {"type": ["number", "null"], "exclusiveMinimum": 0, "description": "Explicit empirical operating flux. Select this or the resistance method, not both."},
        "flux_source": {"type": ["string", "null"], "minLength": 1, "description": "Evidence note required when an explicit empirical flux is supplied."},
        "feed_to_reference_concentration_ratio": {"type": ["number", "null"], "exclusiveMinimum": 0, "description": "Optional Cf/C0 ratio for resistance-based flux calculation; no default is assumed."},
        "flux_model_source": {"type": ["string", "null"], "minLength": 1, "description": "Required evidence/basis note for the supplied Cf/C0 input."},
        "viscosity_Pa_s": {"type": ["number", "null"], "exclusiveMinimum": 0, "description": "Measured clarified-juice viscosity for the active no-fermentation feed; fermented-juice register value is not reused."},
        "viscosity_source": {"type": ["string", "null"], "minLength": 1, "description": "Evidence note required with viscosity_Pa_s for the resistance flux method."},
        "retention_matrix_source": {"type": "string", "minLength": 1},
        "transmembrane_pressure_bar": {"type": ["number", "null"], "exclusiveMinimum": 0, "description": "Optional TMP; required with Cf/C0 for resistance-based flux, or with pump efficiency for pressure-work electricity."},
        "pressure_source": {"type": ["string", "null"], "minLength": 1},
        "pump_efficiency_fraction": {"type": ["number", "null"], "exclusiveMinimum": 0, "maximum": 1, "description": "Optional; when supplied it requires TMP and its own source note."},
        "pump_efficiency_source": {"type": ["string", "null"], "minLength": 1},
        "crossflow_electricity_kwh_m3_feed": {"type": ["number", "null"], "minimum": 0, "description": "Optional explicit crossflow recirculation electricity per m3 clarified feed; added to BioSTEAM electricity utilities and excludes separately modeled permeate-side pressure work."},
        "crossflow_electricity_source": {"type": ["string", "null"], "minLength": 1, "description": "Required measurement/source note when crossflow_electricity_kwh_m3_feed is supplied."},
        "component_retention_overrides": {"type": "object", "additionalProperties": {"type": "number", "minimum": 0, "maximum": 1}},
        "component_retention_override_sources": {"type": "object", "additionalProperties": {"type": "string", "minLength": 1}},
        "use_hormone_benchmarks": {"type": "boolean", "default": False, "description": "Explicitly add the user-supplied clarified-juice hormone benchmark as a separately tracked screening analyte feed; off by default."},
        "hormone_benchmark_source": {"type": ["string", "null"], "minLength": 1, "description": "Required evidence note when use_hormone_benchmarks is true."},
        "cip_solution_volume_L_per_step": {"type": ["number", "null"], "exclusiveMinimum": 0, "description": "Optional same nominal working-solution volume for each sequential CIP step; requires make-up fraction and evidence note."},
        "cip_makeup_fraction_per_cycle": {"type": ["number", "null"], "minimum": 0, "maximum": 1, "description": "Fraction of each CIP working-solution batch replaced/made up after each event; requires volume and evidence note."},
        "cip_input_source": {"type": ["string", "null"], "minLength": 1, "description": "Required source/evidence note when CIP volume and make-up fraction are supplied."},
    },
}

INITIAL_INVENTORY_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "total_mass_kg": {"type": "number", "minimum": 0, "default": 0},
        "moisture_fraction": {"type": ["number", "null"], "minimum": 0, "maximum": 1},
        "component_mass_fractions": {"type": "object", "additionalProperties": {"type": "number", "minimum": 0}},
        "temperature_k": {"type": ["number", "null"], "exclusiveMinimum": 0},
        "storage_age_h": {"type": "number", "minimum": 0, "default": 0},
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
        "start_date": {"type": ["string", "null"], "format": "date"},
        "end_date": {"type": ["string", "null"], "format": "date"},
        "time_step": {"type": ["string", "null"], "enum": ["monthly", "weekly", "daily", None]},
        "annual_biomass_target": {"type": ["number", "null"], "exclusiveMinimum": 0},
        "operating_schedule": {"$ref": "#/$defs/operating_schedule"},
        "biomass_schedule": {"$ref": "#/$defs/biomass_schedule"},
        "initial_storage_inventory": {"$ref": "#/$defs/initial_storage_inventory"},
        "feed_supply_profile_id": {"type": ["string", "null"]},
        "wet_feed_rate_kg_hr": {"type": ["number", "null"], "exclusiveMinimum": 0},
        "plant_capacity_kg_hr": {"type": ["number", "null"], "exclusiveMinimum": 0},
        "feed_composition": {
            "type": "object",
            "description": (
                "Wet-mass fractions for canonical GreenHub compound IDs only. If omitted or empty, "
                "the canonical GreenHub feed profile is applied. Supplied totals from "
                f"{FEED_COMPOSITION_MIN_TOTAL:.2f} to {FEED_COMPOSITION_MAX_TOTAL:.2f} are normalized "
                f"to {FEED_COMPOSITION_NORMALIZED_TOTAL:.2f} by the request contract."
            ),
            "x-total-minimum": FEED_COMPOSITION_MIN_TOTAL,
            "x-total-maximum": FEED_COMPOSITION_MAX_TOTAL,
            "x-normalized-total": FEED_COMPOSITION_NORMALIZED_TOTAL,
            "additionalProperties": {"type":"number","minimum":0,"maximum":FEED_COMPOSITION_MAX_TOTAL},
        },
        "storage_conditions": {"type": ["object", "null"], "description":"Opt-in component retention or source-gated grass reaction package; see decision-support options."},
        "biostimulant_route": BIOSTIMULANT_ROUTE_SCHEMA,
    },
    "$defs": {
        "scenario_selection": SCENARIO_SELECTION_SCHEMA,
        "parameter_override": PARAMETER_OVERRIDE_SCHEMA,
        "parameter_overrides": {
            "type": "array",
            "items": {"$ref": "#/$defs/parameter_override"},
        },
        "operating_schedule": OPERATING_SCHEDULE_SCHEMA,
        "biomass_schedule": BIOMASS_SCHEDULE_SCHEMA,
        "biostimulant_route": BIOSTIMULANT_ROUTE_SCHEMA,
        "initial_storage_inventory": INITIAL_INVENTORY_SCHEMA,
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

PARAMETER_RESOLUTION_RESULT_SCHEMA = {
    "type": "object",
    "required": ["parameter_id", "value", "unit", "status", "source", "selection_reason", "warnings"],
    "properties": {
        "parameter_id": {"type": "string"},
        "value": {},
        "unit": {"type": ["string", "null"]},
        "status": {"type": "string"},
        "source": {"type": ["string", "null"]},
        "selection_reason": {"type": "string"},
        "warnings": {"type": "array", "items": {"type": "string"}},
        # Optional additive evidence metadata; clients built for 1.0 may ignore it.
        "quality_class": {"type": ["string", "null"], "enum": ["A", "B", "C", "D", "E", None]},
        "evidence_class": {"type": ["string", "null"]},
        "source_title": {"type": ["string", "null"]},
        "stable_identifier": {"type": ["string", "null"]},
        "source_url": {"type": ["string", "null"], "format": "uri"},
        "exact_source_location": {"type": ["string", "null"]},
        "basis": {"type": ["string", "null"]},
        "uncertainty": {"type": ["object", "string", "null"]},
    },
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
        "resolved_parameters": {"type": "array", "items": PARAMETER_RESOLUTION_RESULT_SCHEMA},
        "model_maturity": {"type": "object", "additionalProperties": {"type": "string"}},
        "dataset_readiness": {"type": "object", "additionalProperties": {"type": "integer"}},
        "plots": {"type": "array", "items": {"type": "object"}},
        "graph": {"$ref": "#/$defs/process_graph"},
        "export_references": {"type": "object", "additionalProperties": {"type": "string"}},
        "reproducibility_metadata": {"type": "object"},
        "time_grid": {"type": "array", "items": {"type": "object"}},
        "feed_supply_series": {"type": "array", "items": {"type": "object"}},
        "storage_inventory_series": {"type": "array", "items": {"type": "object"}},
        "throughput_series": {"type": "array", "items": {"type": "object"}},
        "capacity_utilization_series": {"type": "array", "items": {"type": "object"}},
        "bottleneck_series": {"type": "array", "items": {"type": "object"}},
        "product_series": {"type": "array", "items": {"type": "object"}},
        "residual_series": {"type": "array", "items": {"type": "object"}},
        "utility_series": {"type": "array", "items": {"type": "object"}},
        "balance_residual_series": {"type": "array", "items": {"type": "object"}},
        "process_state_series": {"type": "array", "items": {"type": "object"}},
        "seasonal_summary": {"type": ["object", "null"]},
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
    ("process_areas[].metrics.biostimulant_product_*", "number|null", "kg/hr", "PR7 wet concentrate component totals and elemental N/P/K/carbon values; separately tracks product moisture and solids."),
    ("process_areas[].metrics.biostimulant_crossflow_electricity_kwh_m3_feed", "number|null", "kWh/m3 feed", "Optional source-noted PR7 crossflow recirculation specific electricity, added to the BioSTEAM electricity utility; excludes optional permeate-side pressure work."),
    ("process_areas[].metrics.biostimulant_crossflow_electricity_kw", "number|null", "kW", "PR7 crossflow electricity derived from the explicit kWh/m3 clarified-feed input and simulated feed volumetric flow."),
    ("process_areas[].metrics.biostimulant_crossflow_electricity_source", "string|null", None, "User-supplied provenance note for the PR7 crossflow-specific electricity input."),
    ("biostimulant_screen.film_retention_diagnostics", "object", None, "TUF free-state sigma/Peclet retention is applied at selected flux; LNF free-state film predictions remain diagnostic beside empirical screening factors; bound-state predictions are withheld pending diffusivity."),
    ("streams[].total_mass", "NumericalValue", "kg/hr", "Total wet stream mass flow."),
    ("streams[].components", "object<NumericalValue>", "kg/hr", "Component mass-flow mapping."),
    ("units[].power", "NumericalValue", "kW", "Unit electricity demand."),
    ("balances[].residual", "NumericalValue", "kg/hr or kmol/hr", "Signed outlet-minus-inlet residual."),
    ("products[].mass_flow", "NumericalValue", "kg/hr", "Product stream wet mass flow."),
    ("products[].volumetric_flow", "NumericalValue", "m3/hr", "Product stream volume flow at modeled BioSTEAM conditions; distinct from normalized gas volume."),
    ("annual.volumetric_products", "object<NumericalValue>", "m3/year or m3/reported period", "Annualized product volume at the modelled BioSTEAM stream conditions; not normalized Nm3."),
    ("resolved_parameters[]", "ParameterResolutionResult", None, "Resolved value, source, status, warnings, plus optional additive evidence metadata (quality class, source identifier/title/location, basis, and uncertainty)."),
    ("validation", "ValidationSummary", None, "Blocking and warning validation findings."),
    ("graph", "ProcessGraph", None, "Frontend-ready unit and stream topology."),
    ("plots[]", "PlotSpecification", None, "Stable plot metadata and availability."),
    ("export_references", "object<string>", None, "Run-relative artifact references only."),
    ("feed_supply_series[]", "object", "kg", "Available, collected, and uncollected wet biomass with provenance."),
    ("storage_inventory_series[]", "object", "kg", "Storage receipts, withdrawals, overflow, inventory, and age."),
    ("throughput_series[]", "object", "kg and kg/hr", "Scheduled, capacity-limited process throughput."),
    ("capacity_utilization_series[]", "object", "fraction", "Eligible unit load, capacity, and utilization."),
    ("seasonal_summary", "object", None, "Integrated seasonal feed, storage, product, utility, and balance totals."),
    ("seasonal_summary.active_process_operating_hours", "number|null", "h/year", "Seasonal hours with positive modeled refinery throughput; used for operating-hour-based PR7 CIP cycles."),
    ("seasonal_summary.pr7_feed_volume_m3_year", "number|null", "m3/year", "Clarified-juice volumetric feed through PR7_M101, integrated across seasonal timesteps."),
    ("seasonal_summary.pr7_peak_membrane_area_m2", "number|null", "m2", "Peak monthly PR7 membrane area for seasonal module-cost screening."),
    ("seasonal_summary.pr7_maximum_peak_membrane_area_m2", "number|null", "m2", "Upper area unavailable when unresolved component volume is not resolved."),
)


PLOT_CATALOG = (
    {"plot_id": "SYS-AREA-MASS", "process_area": "integrated_system", "x_unit": None, "y_unit": "kg/hr", "availability": "available"},
    {"plot_id": "VALIDATION-RESIDUALS", "process_area": "integrated_system", "x_unit": None, "y_unit": "kg/hr", "availability": "available"},
    {"plot_id": "SYS-UNIT-POWER", "process_area": "shared_utilities_and_supporting_operations", "x_unit": None, "y_unit": "kW", "availability": "available"},
    {"plot_id": "DATA-READINESS", "process_area": "data_governance", "x_unit": None, "y_unit": "count", "availability": "available"},
    {"plot_id": "PR-PRECIP-RECOVERY", "process_area": "protein_recovery", "x_unit": None, "y_unit": "fraction", "availability": "conditional: PR1 literature_default"},
    {"plot_id": "PR7-MASS-SPLIT", "process_area": "protein_recovery", "x_unit": None, "y_unit": "kg/hr", "availability": "conditional: PR7 full-plant run"},
    {"plot_id": "PR7-HORMONE-CAPTURE", "process_area": "protein_recovery", "x_unit": None, "y_unit": "mg/hr", "availability": "conditional: PR7 full-plant run"},
    {"plot_id": "PR7-PRODUCT-PROFILE", "process_area": "protein_recovery", "x_unit": None, "y_unit": "kg/hr", "availability": "conditional: PR7 full-plant run"},
    {"plot_id": "PR7-ENERGY-BREAKDOWN", "process_area": "protein_recovery", "x_unit": None, "y_unit": "kW", "availability": "conditional: PR7 with sourced pressure-work and/or crossflow electricity inputs"},
    {"plot_id": "SEASONAL-FEED", "process_area": "feedstock_and_characterization", "x_unit": None, "y_unit": "kg", "availability": "conditional: quasi_dynamic"},
    {"plot_id": "SEASONAL-INVENTORY", "process_area": "feedstock_and_characterization", "x_unit": None, "y_unit": "kg", "availability": "conditional: quasi_dynamic"},
    {"plot_id": "SEASONAL-THROUGHPUT", "process_area": "integrated_system", "x_unit": None, "y_unit": "kg/hr", "availability": "conditional: quasi_dynamic"},
    {"plot_id": "SEASONAL-UTILIZATION", "process_area": "integrated_system", "x_unit": None, "y_unit": "fraction", "availability": "conditional: eligible capacity"},
    {"plot_id": "SEASONAL-PRODUCTS", "process_area": "integrated_system", "x_unit": None, "y_unit": "kg", "availability": "conditional: calculated products"},
    {"plot_id": "SEASONAL-BIOSTIMULANT", "process_area": "protein_recovery", "x_unit": None, "y_unit": "kg/month", "availability": "conditional: PR7 seasonal simulation"},
    {"plot_id": "SEASONAL-BIOSTIMULANT-VOLUME", "process_area": "protein_recovery", "x_unit": None, "y_unit": "m3/month", "availability": "conditional: PR7 seasonal simulation"},
    {"plot_id": "SEASONAL-ELECTRICITY", "process_area": "shared_utilities_and_supporting_operations", "x_unit": None, "y_unit": "kWh", "availability": "conditional: quasi_dynamic"},
    {"plot_id": "SEASONAL-MASS-RESIDUAL", "process_area": "integrated_system", "x_unit": None, "y_unit": "kg", "availability": "conditional: quasi_dynamic"},
)

FEED_PROFILE_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "required": ["profile_id", "resolution", "points"],
    "properties": {
        "profile_id": {"type": "string", "minLength": 1},
        "display_name": {"type": "string"},
        "resolution": {"type": "string", "enum": ["monthly", "daily"]},
        "normalized": {"type": "boolean", "default": False},
        "provenance": {"type": "string"},
        "warnings": {"type": "array", "items": {"type": "string"}},
        "points": {
            "type": "array",
            "items": {
                "type": "object",
                "required": ["period"],
                "properties": {
                    "period": {"type": "string"},
                    "available_wet_biomass_kg": {"type": ["number", "null"], "minimum": 0},
                    "normalized_weight": {"type": ["number", "null"], "minimum": 0},
                    "collection_fraction": {"type": "number", "minimum": 0, "maximum": 1},
                    "moisture_fraction": {"type": ["number", "null"], "minimum": 0, "maximum": 1},
                    "component_mass_fractions": {"type": "object", "additionalProperties": {"type": "number", "minimum": 0}},
                    "temperature_k": {"type": ["number", "null"]},
                    "source": {"type": "string"},
                    "provenance": {"type": ["string", "null"]},
                    "warnings": {"type": "array", "items": {"type": "string"}},
                },
            },
        },
    },
}

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
    add('/api/v1/decision-support/options', 'GET', 'decisionSupportOptions')
    add('/api/v1/decision-support/pareto/latest', 'GET', 'getLatestRvoParetoAnalysis')
    paths['/api/v1/decision-support/pareto/latest']['get']['description'] = (
        'Returns the latest no-PEF BioSTEAM Pareto analysis, with separate protein-enabled and '
        'protein-bypassed groups, RVO-labelled support what-if cases, selected candidates and fronts.'
    )
    add('/api/v1/decision-support/pareto/latest/figures/{group}', 'GET', 'getLatestRvoParetoFigure')
    paths['/api/v1/decision-support/pareto/latest/figures/{group}']['get']['parameters'] = [{
        'name': 'group', 'in': 'path', 'required': True,
        'schema': {'type': 'string', 'enum': ['protein_enabled', 'protein_bypass']},
    }]
    paths['/api/v1/decision-support/pareto/latest/figures/{group}']['get']['responses']['200'] = {
        'description': 'Static 3D Pareto PNG for the selected protein group.',
        'content': {'image/png': {'schema': {'type': 'string', 'format': 'binary'}}},
    }
    add('/api/v1/decision-support/pareto/latest/figure-index', 'GET', 'getLatestRvoParetoFigureIndex')
    paths['/api/v1/decision-support/pareto/latest/figure-index']['get']['description'] = (
        'Returns the current indexed PNG library with source dataset, scenario, units, category, and image URL.'
    )
    add('/api/v1/decision-support/pareto/latest/figures/by-id/{figure_id}', 'GET', 'getLatestRvoParetoFigureById')
    paths['/api/v1/decision-support/pareto/latest/figures/by-id/{figure_id}']['get']['parameters'] = [{
        'name': 'figure_id', 'in': 'path', 'required': True, 'schema': {'type': 'integer', 'minimum': 1},
    }]
    paths['/api/v1/decision-support/pareto/latest/figures/by-id/{figure_id}']['get']['responses']['200'] = {
        'description': 'An indexed current Pareto-analysis PNG figure.',
        'content': {'image/png': {'schema': {'type': 'string', 'format': 'binary'}}},
    }
    add('/api/v1/decision-support/pareto/latest/report', 'GET', 'downloadLatestRvoParetoReport')
    paths['/api/v1/decision-support/pareto/latest/report']['get']['responses']['200'] = {
        'description': 'Current PDF report with selected candidates and the indexed PNG atlas.',
        'content': {'application/pdf': {'schema': {'type': 'string', 'format': 'binary'}}},
    }
    add('/api/v1/decision-support/runs/{run_id}', 'GET', 'decisionSupportRun')
    for action in ('evaluate','batch','sensitivity'):
        route='/api/v1/decision-support/'+action
        add(route, 'POST', 'decisionSupport'+action.title())
        paths[route]['post']['requestBody']={'required':True,'content':{'application/json':{'schema':{'type':'object','required':['configuration'],'properties':{'configuration':{'type':'object','required':['simulation'],'properties':{
            'simulation':{'$ref':'#/components/schemas/SimulationRequest'},
            'use_screening_process_assumptions':{'type':'boolean','default':False,'description':'Explicitly opt in to the traceable screening process-assumption profile.'},
            'use_screening_lca_factors':{'type':'boolean','default':False,'description':'Explicitly opt in to traceable Netherlands electricity and heat factors plus PR7 CIP reagent production factors; these are screening values and project-specific factors should replace them.'},
            'logistics_result':{'type':['object','null'],'description':'Optional precomputed logistics result forwarded to TEA and LCA; it does not alter process chemistry or balances.'},
            'financial_assumptions':{'type':'object'},'climate_factors':{'type':'object'},'additional_inventory':{'type':'array','items':{'type':'object'}},
        }}}}}}}
    add("/api/v1/model/info", "GET", "modelInfo")
    add("/api/v1/scenarios", "GET", "listScenarios")
    add("/api/v1/biostimulant/options", "GET", "biostimulantScreeningOptions")
    add("/api/v1/biostimulant/screen", "POST", "screenBiostimulantRoute")
    paths["/api/v1/biostimulant/options"]["get"]["description"] = (
        "Returns PR7 membrane-screening options. The screen uses clarified grass juice with no 14-day pre-membrane fermentation/storage; any downstream digestion remains controlled by the separate AD scenario. TUF/LNF co-retention inputs and MEUF gaps are separately identified."
    )
    paths["/api/v1/biostimulant/screen"]["post"]["description"] = (
        "Calculates provisional analyte capture, membrane area, and gross revenue. Choose either empirical flux or the resistance model; conflicting flux methods are rejected. TUF free-state retention uses the sigma/Peclet relation at selected flux; supplied bound-pool factors remain empirical, and LNF film predictions are diagnostic. If component flows are supplied, the isolated BioSTEAM unit runs and conserves pools without documented retentions at a separate unresolved outlet. This is not a full plant simulation; unresolved pools gate complete product allocation, TEA and LCA."
    )
    paths["/api/v1/biostimulant/screen"]["post"]["responses"]["200"]["content"] = {
        "application/json": {"schema": {
            "type": "object",
            "properties": {
                "biosteam_unit": {"type": ["object", "null"], "properties": {
                    "membrane_area_m2": {"type": ["number", "null"], "description": "Point estimate is null when unresolved outlet mass is nonzero."},
                    "minimum_membrane_area_m2": {"type": "number", "description": "Known-permeate membrane-area floor (m²); unresolved pools are excluded."},
                    "maximum_membrane_area_m2": {"type": ["number", "null"], "description": "Upper membrane-area screen (m²), null while any component fate remains unresolved."},
                    "unresolved_stream_id": {"type": "string"},
                    "unresolved_components_kg_hr": {"type": "object", "additionalProperties": {"type": "number"}},
                    "unresolved_mass_kg_hr": {"type": "number", "description": "Unresolved outlet mass flow (kg/h)."},
                    "unresolved_kg_year": {"type": "number", "description": "Unresolved outlet mass over supplied operating hours (kg/year)."},
                    "mass_closure_error_kg_hr": {"type": "number", "description": "Overall unit mass closure error (kg/h)."},
                }},
                "film_retention_diagnostics": {
                    "type": "object",
                    "description": "TUF free-state sigma/Peclet retention is applied at selected flux; LNF free-state predictions are diagnostic beside empirical screen factors. Bound predictions are null until bound-payload diffusivity is supplied.",
                    "properties": {
                        "technology_id": {"type": "string"},
                        "status": {"type": "string"},
                        "flux_L_m2_h": {"type": "number"},
                        "applied_to_process_split": {"type": "boolean"},
                        "comparison_basis": {"type": "string"},
                        "analytes": {"type": "array", "items": {"type": "object", "properties": {
                            "solute_id": {"type": "string"},
                            "weighted_state_retention_fraction": {"type": "number", "description": "Free/bound weighted process retention using the state-specific basis reported below."},
                            "process_split_free_retention_fraction": {"type": "number"},
                            "process_split_bound_retention_fraction": {"type": "number"},
                            "film_free_retention_fraction": {"type": "number"},
                            "film_free_peclet_number": {"type": "number"},
                            "reflection_coefficient": {"type": "number"},
                            "bound_film_retention_fraction": {"type": ["number", "null"]},
                            "bound_prediction_status": {"type": "string"},
                        }}},
                    },
                },
                "component_mass_split": {"type": ["object", "null"], "properties": {
                    "complete_mass_split": {"type": "boolean"},
                    "unmapped_component_ids": {"type": "array", "items": {"type": "string"}},
                    "unresolved_kg_hr": {"type": "object", "additionalProperties": {"type": "number"}},
                    "mass_error_kg_hr": {"type": "number"},
                }},
                "mass_balance_readiness": {"type": ["object", "null"], "properties": {
                    "component_fate_complete": {"type": "boolean"},
                    "mass_balanced": {"type": "boolean"},
                    "unmapped_nonzero_components": {"type": "array", "items": {"type": "string"}},
                }},
            },
        }},
    }
    paths["/api/v1/biostimulant/screen"]["post"]["requestBody"] = {
        "required": True,
        "content": {"application/json": {"schema": {
            "type": "object", "additionalProperties": False,
            "required": ["feed_volume_m3_year", "technology_id", "operating_hours_year"],
            "not": {"required": ["flux_L_m2_h", "resistance_flux_model"]},
            "properties": {
                "feed_volume_m3_year": {"type": "number", "minimum": 0, "description": "Annual clarified-juice feed volume (m³/year)."},
                "technology_id": {"type": "string", "enum": ["TUF", "LNF", "MEUF"]},
                "operating_hours_year": {"type": "number", "exclusiveMinimum": 0},
                "concentration_factor": {"type": "number", "exclusiveMinimum": 1, "default": 10, "description": "Retentate concentration factor; default is the user-supplied value in the PR7 parameter register."},
                "price_EUR_L": {"type": "number", "minimum": 0, "default": 2.5, "description": "Screening bulk-concentrate price; default is the user-supplied nominal value in the PR7 parameter register."},
                "flux_L_m2_h": {"type": "number", "exclusiveMinimum": 0},
                "resistance_flux_model": {
                    "type": "object", "additionalProperties": False,
                    "required": ["pressure_bar", "pressure_source", "feed_to_reference_concentration_ratio", "ratio_source", "viscosity_Pa_s", "viscosity_source"],
                    "properties": {
                        "pressure_bar": {"type": "number", "exclusiveMinimum": 0},
                        "pressure_source": {"type": "string", "minLength": 1},
                        "feed_to_reference_concentration_ratio": {"type": "number", "exclusiveMinimum": 0},
                        "ratio_source": {"type": "string", "minLength": 1},
                        "viscosity_Pa_s": {"type": "number", "exclusiveMinimum": 0, "description": "Measured clarified-juice viscosity for the no-fermentation feed; fermented-juice viscosity is not reused."},
                        "viscosity_source": {"type": "string", "minLength": 1},
                    },
                    "description": "Resistance-equation flux method for TUF/LNF. Select this or empirical flux_L_m2_h, not both.",
                },
                "transmembrane_pressure_bar": {"type": "number", "exclusiveMinimum": 0, "description": "Optional pressure-work estimate input; requires pump_efficiency_fraction and matching evidence notes."},
                "pump_efficiency_fraction": {"type": "number", "exclusiveMinimum": 0, "maximum": 1, "description": "Caller-supplied pump efficiency for the pressure-work estimate; no default is assumed."},
                "run_id": {"type": "string", "description": "Optional completed model run; uses its clarified-protein-rich-liquid component flows for the co-retention split."},
                "component_flows_kg_hr": {"type": "object", "additionalProperties": {"type": "number", "minimum": 0}, "description": "Optional actual feed component flows in kg/hour. Pools without a documented class retention are conserved in unresolved_kg_hr rather than assigned a guessed fraction."},
                "component_flows_source": {"type": "string", "minLength": 1, "description": "Required source/evidence note for caller-supplied component_flows_kg_hr; not required when flows are loaded from run_id."},
                "component_retention_overrides": {"type": "object", "additionalProperties": {"type": "number", "minimum": 0, "maximum": 1}, "description": "Explicit per-component retention fractions; each key must also appear in component_retention_override_sources."},
                "component_retention_override_sources": {"type": "object", "additionalProperties": {"type": "string", "minLength": 1}, "description": "Required source/evidence note matching each explicit retention override."},
                "annual_electricity_kwh": {"type": "number", "minimum": 0},
                "electricity_kg_co2e_kwh": {"type": "number", "minimum": 0},
                "electricity_price_eur_kwh": {"type": "number", "minimum": 0},
                "annual_heat_kwh": {"type": "number", "minimum": 0},
                "heat_kg_co2e_kwh": {"type": "number", "minimum": 0},
                "heat_price_eur_kwh": {"type": "number", "minimum": 0},
                "operational_input_sources": {"type": "object", "additionalProperties": {"type": "string", "minLength": 1}, "description": "Required source note for every supplied annual activity, emission factor, or energy price. Use explicit zero activity with a source note when the utility is not used."},
                "cip_solution_volume_L_per_step": {"type": "number", "exclusiveMinimum": 0, "description": "Optional working-solution volume for each sequential CIP reagent step; requires make-up fraction and evidence note."},
                "cip_makeup_fraction_per_cycle": {"type": "number", "minimum": 0, "maximum": 1},
                "cip_input_source": {"type": "string", "minLength": 1},
                "include_cip_screening_lca": {"type": "boolean", "default": False, "description": "Explicitly apply registered attributional upstream NaOH and citric-acid production factors to CIP chemical inventory; excludes cleaning wastewater and utilities."},
            },
        }}},
    }
    add("/api/v1/process-areas", "GET", "listProcessAreas")
    add("/api/v1/feed-profiles", "GET", "listFeedProfiles")
    add(
        "/api/v1/feed-profiles", "POST", "registerFeedProfile",
        request_schema="FeedProfile", created=True,
    )
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
        ("time-series", "getSimulationTimeSeries"), ("inventory", "getSimulationInventory"),
        ("utilization", "getSimulationUtilization"), ("seasonal-summary", "getSeasonalSummary"),
        ("annual-summary", "getAnnualSummary"),
    ):
        add(f"/api/v1/simulations/{{run_id}}/{suffix}", "GET", operation)
    add("/api/v1/simulations/{run_id}/graph", "GET", "getSimulationGraph", response_schema="ProcessGraph")
    add("/api/v1/simulations/{run_id}/plots/{plot_id}", "GET", "getSimulationPlot")
    add("/api/v1/openapi.json", "GET", "openApiDocument")
    for suffix, operation in (("default-summary", "dynamicCompleteDefaultSummary"), ("options", "dynamicCompleteOptions"), ("assumptions", "dynamicCompleteAssumptions")):
        add(f"/api/v1/dynamic-complete/{suffix}", "GET", operation)
    add("/api/v1/dynamic-complete/scenario-summary", "POST", "dynamicCompleteScenarioSummary")
    paths["/api/v1/dynamic-complete/scenario-summary"]["post"]["requestBody"] = {
        "required": True, "content": {"application/json": {"schema": {
            "type": "object", "additionalProperties": False, "required": ["scenario"],
            "properties": {"scenario": {"type": "object", "description": "Opt-in scenario fields and defaults are listed at /api/v1/dynamic-complete/options; unknown fields are rejected."},
                           "analysis_factors": {"type": "object", "additionalProperties": {"type": "number", "minimum": 0}}},
        }}}
    }
    for path, methods in paths.items():
        parameters = []
        if "{run_id}" in path:
            parameters.append({"name": "run_id", "in": "path", "required": True, "schema": {"type": "string"}})
        if "{parameter_id}" in path:
            parameters.append({"name": "parameter_id", "in": "path", "required": True, "schema": {"type": "string"}})
        if "{plot_id}" in path:
            parameters.append({"name": "plot_id", "in": "path", "required": True, "schema": {"type": "string"}})
        if "{group}" in path and not methods.get("get", {}).get("parameters"):
            parameters.append({"name": "group", "in": "path", "required": True, "schema": {"type": "string", "enum": ["protein_enabled", "protein_bypass"]}})
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
                "FeedProfile": FEED_PROFILE_SCHEMA,
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
