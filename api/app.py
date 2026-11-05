"""Dependency-light WSGI adapter for the transport-neutral GreenHub services."""

from __future__ import annotations

import json
import mimetypes
import re
import csv
from dataclasses import asdict, dataclass
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
    inline: bool = False


class GreenHubAPI:
    """WSGI application that delegates all scientific work to application services."""

    def __init__(self, run_root: Path | None = None) -> None:
        self.repository = RunRepository()
        self.simulations = SimulationService(self.repository, run_root=run_root)
        self.parameters: ParameterService = self.simulations.parameters
        self.scenarios: ScenarioService = self.simulations.scenarios
        self.results = ResultService(self.repository)
        from Greenhub.application.decision_batch_jobs import DecisionBatchJobs
        from Greenhub.settings import RESULTS_DIR
        self.decision_batch_jobs = DecisionBatchJobs(
            (run_root or RESULTS_DIR / "runs"),
            __import__("Greenhub.application.decision_support_service", fromlist=["DecisionSupportService"]).DecisionSupportService(self.simulations).evaluate,
        )
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
        except NotImplementedError as error:
            message = str(error).strip("'") or "The selected process scenario is gated by missing data."
            return self._respond(start_response, 422, self._error_payload(APIError(422, "scenario_gated", message)))
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
        if path.startswith("/api/v1/biostimulant/"):
            from Greenhub.biostimulant_screening import (
                FLUX_BASELINE_L_M2_H,
                calculate_component_split_balance,
                calculate_cip_reagent_screen,
                calculate_energy_tea_lca_screen,
                calculate_hormone_capture,
                compare_empirical_and_film_retention,
                calculate_membrane_area_and_revenue,
                calculate_meuf_surfactant_screen,
                calculate_resistance_flux,
                estimate_pressure_work_electricity,
                simulate_biostimulant_membrane_unit,
                split_component_flows,
            )
            if method == "GET" and path == "/api/v1/biostimulant/options":
                return {
                    "scenario_id": "PR7",
                    "status": "screening_and_biosteam_unit; unresolved_pool_fate_preserved; complete_tea_lca_retention_gated",
                    "feed_boundary": "clarified grass juice; no 14-day pre-membrane fermentation/storage",
                    "fermentation_included": False,
                    "pre_membrane_fermentation_included": False,
                    "downstream_digestion_basis": "controlled by the selected anaerobic_digestion scenario; PR7 permeate proceeds downstream",
                    "technologies": [
                        {"id": key, "nominal_flux_L_m2_h": value, "flux_basis": "user-supplied screening baseline"}
                        for key, value in FLUX_BASELINE_L_M2_H.items()
                    ],
                    "required_inputs": ["feed_volume_m3_year", "technology_id", "operating_hours_year"],
                    "full_plant_route": {
                        "scenario_id": "PR7",
                        "benchmark_hormone_option": "use_hormone_benchmarks",
                        "benchmark_hormone_default": False,
                        "benchmark_hormone_source_required": True,
                        "benchmark_hormone_basis": "User-supplied clarified-juice concentrations converted with simulated clarified-liquid volume; separate analyte-equivalent feed; screening proxy, not measured GreenHub composition. The supplied free/bound split is discussed for 14-day anaerobic material and is unvalidated at the no-fermentation PR7 boundary.",
                        "fermentation_included": False,
                        "pre_membrane_fermentation_included": False,
                        "downstream_digestion_basis": "controlled by the selected anaerobic_digestion scenario; PR7 permeate proceeds downstream",
                    },
                    "optional_inputs": ["concentration_factor", "price_EUR_L", "flux_L_m2_h", "resistance_flux_model", "run_id", "component_flows_kg_hr", "component_flows_source", "component_retention_overrides", "component_retention_override_sources", "transmembrane_pressure_bar", "pump_efficiency_fraction", "annual_electricity_kwh", "electricity_kg_co2e_kwh", "electricity_price_eur_kwh", "annual_heat_kwh", "heat_kg_co2e_kwh", "heat_price_eur_kwh", "operational_input_sources", "cip_solution_volume_L_per_step", "cip_makeup_fraction_per_cycle", "cip_input_source", "include_cip_screening_lca"],
                    "override_rule": "Every per-component retention override requires a matching source/evidence note.",
                    "full_plant_retention_gate": {
                        "observed_unmapped_component_ids": ["Lipids", "NonBiodegradableOrganics", "OrganicNitrogen", "PersistentOrganics", "Pesticides"],
                        "scope_note": "Observed for the default clarified-grass-juice case; active IDs depend on feed composition.",
                        "required_action": "Provide a documented per-component retention and source note for every nonzero pool without a class retention; otherwise product/permeate allocation, membrane-area point estimate, complete TEA revenue, and climate LCA remain gated while the mass-balanced unresolved outlet is reported.",
                        "meuf_missing_component_class_retention": ["crude_proteins", "peptides_amino_acids", "sugars", "divalent_salts", "monovalent_salts"],
                    },
                    "limitations": [
                        "Benchmark hormone concentrations and retentions are user-supplied proxies, not project measurements.",
                        "The supplied free/bound split is described for a 14-day anaerobic state and is unvalidated for this no-fermentation PR7 feed boundary.",
                        "Free/bound fractions describe feed composition. Tight-UF free-pool retention is recalculated at the selected flux with the supplied sigma/Peclet relation; bound-state retention and loose-NF/MEUF values remain empirical screening proxies, not independently validated measurements.",
                        "Hormone capture is analyte-equivalent mass; carrier mass, product purity, and full retentate composition are not predicted.",
                        "Unmapped or class-retention-missing pool mass is conserved at a separate unresolved BioSTEAM outlet; dependent full-route results remain incomplete.",
                        "Area assumes permeate = feed × (1 − 1/VCF), with no downtime or flux decline.",
                        "Gross revenue is a screening calculation and excludes membrane CAPEX, cleaning, labor, and other OPEX.",
                        "Gross sales use the assumed concentration-factor volume and are not calculated from or validated by the simulated BioSTEAM retentate volume or product specification.",
                        "Optional pressure-work electricity is a lower-bound estimate; it excludes crossflow recirculation, pressure losses, CIP, and auxiliaries.",
                        "Optional energy TEA/LCA uses only user-entered annual utility quantities, prices, and factors with source notes; it is not a full route assessment.",
                    "No fermentation stage is included.",
                    "Resistance-model flux requires measured no-fermentation juice viscosity and sourced TMP and Cf/C0; the fermented-juice register viscosity is not reused.",
                    ],
                }
            if method == "POST" and path == "/api/v1/biostimulant/screen":
                payload = dict(self._read_json(environ))
                allowed = {
                    "feed_volume_m3_year", "technology_id", "operating_hours_year",
                    "concentration_factor", "price_EUR_L", "flux_L_m2_h",
                    "resistance_flux_model",
                    "component_flows_kg_hr", "component_retention_overrides",
                    "component_retention_override_sources",
                    "component_flows_source",
                    "run_id",
                    "annual_electricity_kwh", "electricity_kg_co2e_kwh", "electricity_price_eur_kwh",
                    "annual_heat_kwh", "heat_kg_co2e_kwh", "heat_price_eur_kwh", "operational_input_sources",
                    "transmembrane_pressure_bar", "pump_efficiency_fraction",
                    "cip_solution_volume_L_per_step", "cip_makeup_fraction_per_cycle", "cip_input_source",
                    "include_cip_screening_lca",
                }
                if set(payload) - allowed:
                    raise ValueError("Unknown biostimulant screening fields.")
                if "include_cip_screening_lca" in payload and not isinstance(payload["include_cip_screening_lca"], bool):
                    raise ValueError("include_cip_screening_lca must be a boolean.")
                required = {"feed_volume_m3_year", "technology_id", "operating_hours_year"}
                if not required.issubset(payload):
                    raise ValueError("feed_volume_m3_year, technology_id, and operating_hours_year are required.")
                resistance_flux_model = payload.get("resistance_flux_model")
                resistance_flux_result = None
                if resistance_flux_model is not None:
                    if payload.get("flux_L_m2_h") is not None:
                        raise ValueError("Select either flux_L_m2_h or resistance_flux_model, not both.")
                    if not isinstance(resistance_flux_model, dict):
                        raise ValueError("resistance_flux_model must be an object.")
                    required_resistance_fields = {
                        "pressure_bar", "pressure_source", "feed_to_reference_concentration_ratio",
                        "ratio_source", "viscosity_Pa_s", "viscosity_source",
                    }
                    if set(resistance_flux_model) != required_resistance_fields:
                        raise ValueError("resistance_flux_model requires TMP, Cf/C0, measured viscosity and a source note for each.")
                    if any(not isinstance(resistance_flux_model[key], str) or not resistance_flux_model[key].strip()
                           for key in ("pressure_source", "ratio_source", "viscosity_source")):
                        raise ValueError("Resistance-model TMP, Cf/C0, and viscosity each require a source/evidence note.")
                    if str(payload["technology_id"]).strip().upper() == "MEUF":
                        raise ValueError("The resistance model is parameterized for TUF and LNF only; MEUF requires an empirical flux basis.")
                    resistance_flux_result = calculate_resistance_flux(
                        payload["technology_id"],
                        resistance_flux_model["pressure_bar"],
                        resistance_flux_model["feed_to_reference_concentration_ratio"],
                        viscosity_Pa_s=resistance_flux_model["viscosity_Pa_s"],
                    )
                selected_flux = payload.get("flux_L_m2_h")
                selected_flux_basis = "caller-supplied empirical flux" if selected_flux is not None else "user-supplied nominal empirical baseline"
                if selected_flux is None and resistance_flux_result is not None:
                    selected_flux = resistance_flux_result.predicted_flux_L_m2_h
                    selected_flux_basis = "resistance equation using sourced TMP, Cf/C0, and unfermented-juice viscosity"
                capture = calculate_hormone_capture(
                    payload["feed_volume_m3_year"], payload["technology_id"],
                    flux_L_m2_h=selected_flux,
                )
                film_retention_diagnostics = compare_empirical_and_film_retention(
                    payload["technology_id"], selected_flux or FLUX_BASELINE_L_M2_H[str(payload["technology_id"]).strip().upper()]
                )
                membrane = calculate_membrane_area_and_revenue(
                    payload["feed_volume_m3_year"], payload["technology_id"],
                    operating_hours_year=payload["operating_hours_year"],
                    **{key: payload[key] for key in ("concentration_factor", "price_EUR_L") if key in payload},
                    **({"flux_L_m2_h": selected_flux} if selected_flux is not None else {}),
                )
                meuf_surfactant_screen = (
                    calculate_meuf_surfactant_screen(payload["feed_volume_m3_year"])
                    if str(payload["technology_id"]).strip().upper() == "MEUF" else None
                )
                cip_keys = {"cip_solution_volume_L_per_step", "cip_makeup_fraction_per_cycle", "cip_input_source"}
                cip_supplied = cip_keys & set(payload)
                if cip_supplied and cip_supplied != cip_keys:
                    raise ValueError("CIP screening requires solution volume per step, make-up fraction per cycle, and an evidence note together.")
                if payload.get("include_cip_screening_lca") and cip_supplied != cip_keys:
                    raise ValueError("include_cip_screening_lca requires the complete CIP input set.")
                cip_reagent_screen = None
                if cip_supplied:
                    cip_reagent_screen = calculate_cip_reagent_screen(
                        operating_hours_year=payload["operating_hours_year"],
                        solution_volume_L_per_step=payload["cip_solution_volume_L_per_step"],
                        makeup_fraction_per_cycle=payload["cip_makeup_fraction_per_cycle"],
                        input_source=payload["cip_input_source"],
                        include_screening_lca=bool(payload.get("include_cip_screening_lca", False)),
                    )
                energy_input_names = (
                    "annual_electricity_kwh", "electricity_kg_co2e_kwh", "electricity_price_eur_kwh",
                    "annual_heat_kwh", "heat_kg_co2e_kwh", "heat_price_eur_kwh",
                )
                operational_sources = payload.get("operational_input_sources", {})
                if not isinstance(operational_sources, dict):
                    raise ValueError("operational_input_sources must be an object.")
                hydraulic_keys = {"transmembrane_pressure_bar", "pump_efficiency_fraction"}
                hydraulic_supplied = hydraulic_keys & set(payload)
                if hydraulic_supplied and hydraulic_supplied != hydraulic_keys:
                    raise ValueError("Pressure-work screening requires both transmembrane_pressure_bar and pump_efficiency_fraction.")
                hydraulic_estimate = None
                energy_values = {key: payload[key] for key in energy_input_names if key in payload}
                expected_source_keys = set(energy_values) | hydraulic_supplied
                if set(operational_sources) != expected_source_keys:
                    raise ValueError("operational_input_sources must contain exactly one source note for every supplied utility or hydraulic input.")
                energy_sources = {key: value for key, value in operational_sources.items() if key not in hydraulic_keys}
                if hydraulic_supplied:
                    if "annual_electricity_kwh" in energy_values:
                        raise ValueError("Enter annual electricity or pressure-work inputs, not both.")
                    for key in hydraulic_keys:
                        if not isinstance(operational_sources.get(key), str) or not operational_sources[key].strip():
                            raise ValueError(f"A source/evidence note is required for {key}.")
                    hydraulic_estimate = estimate_pressure_work_electricity(
                        payload["feed_volume_m3_year"], membrane.concentration_factor,
                        payload["transmembrane_pressure_bar"], payload["pump_efficiency_fraction"],
                    )
                    energy_values["annual_electricity_kwh"] = hydraulic_estimate["electricity_kwh_year"]
                    energy_sources["annual_electricity_kwh"] = (
                        "Calculated pressure-work estimate; TMP: " + operational_sources["transmembrane_pressure_bar"]
                        + "; pump efficiency: " + operational_sources["pump_efficiency_fraction"]
                    )
                energy_assessment = calculate_energy_tea_lca_screen(
                    **energy_values, input_sources=energy_sources,
                )
                mass_split = None
                component_balance = None
                biosteam_unit = None
                component_flows = payload.get("component_flows_kg_hr")
                component_source = "caller-supplied component flows"
                component_stream_id = None
                feed_volume_consistency = None
                flow_source = payload.get("component_flows_source")
                if component_flows is not None:
                    if not isinstance(component_flows, dict) or not component_flows:
                        raise ValueError("component_flows_kg_hr must be a non-empty object keyed by GreenHub component ID.")
                    if payload.get("run_id"):
                        raise ValueError("Provide either run_id or component_flows_kg_hr, not both.")
                    if not isinstance(flow_source, str) or not flow_source.strip():
                        raise ValueError("Caller-supplied component_flows_kg_hr requires a source/evidence note.")
                    component_source = "caller-supplied component flows: " + flow_source.strip()
                elif flow_source is not None:
                    raise ValueError("component_flows_source requires component_flows_kg_hr.")
                overrides = payload.get("component_retention_overrides", {})
                override_sources = payload.get("component_retention_override_sources", {})
                if not isinstance(overrides, dict):
                    raise ValueError("component_retention_overrides must be an object keyed by component ID.")
                if not isinstance(override_sources, dict):
                    raise ValueError("component_retention_override_sources must be an object keyed by component ID.")
                if set(overrides) != set(override_sources):
                    raise ValueError("Each component retention override must have exactly one matching source/evidence note.")
                if any(not isinstance(source, str) or not source.strip() for source in override_sources.values()):
                    raise ValueError("Each component retention override source must be a non-empty evidence note.")
                if component_flows is None and not payload.get("run_id") and (overrides or override_sources):
                    raise ValueError("Retention overrides require component_flows_kg_hr or run_id.")
                if payload.get("run_id"):
                    if component_flows is not None:
                        raise ValueError("Provide either run_id or component_flows_kg_hr, not both.")
                    run_streams = self.results.get_streams(str(payload["run_id"]))
                    feed_stream = next((
                        stream for stream in run_streams
                        if "clarified_protein_rich_liquid" in stream.aliases
                        or stream.stream_id == "clarified_protein_rich_liquid"
                    ), None)
                    if feed_stream is None:
                        raise ValueError("The requested simulation has no clarified grass-juice stream.")
                    component_flows = {
                        ID: value.value for ID, value in feed_stream.components.items()
                        if value.value is not None
                    }
                    component_source = "selected completed BioSTEAM run"
                    component_stream_id = feed_stream.stream_id
                    stream_mass_kg_hr = sum(
                        float(value.value) for value in feed_stream.components.values()
                        if value.value is not None
                    )
                    density_kg_m3 = 1000.0
                    density_source = "documented model default"
                    for parameter in self.results.get_provenance(str(payload["run_id"])):
                        if parameter.parameter_id.endswith("phase4_feed_density_kg_m3") and parameter.value is not None:
                            resolved_density = float(parameter.value)
                            if resolved_density > 0.0:
                                density_kg_m3 = resolved_density
                                density_source = parameter.source or "resolved model parameter"
                            break
                    implied_volume = stream_mass_kg_hr / density_kg_m3 * float(payload["operating_hours_year"])
                    entered_volume = float(payload["feed_volume_m3_year"])
                    difference_pct = (
                        abs(entered_volume - implied_volume) / implied_volume * 100.0
                        if implied_volume > 0.0 else None
                    )
                    feed_volume_consistency = {
                        "entered_volume_m3_year": entered_volume,
                        "stream_mass_flow_kg_hr": stream_mass_kg_hr,
                        "stream_implied_volume_m3_year": implied_volume,
                        "density_basis_kg_m3": density_kg_m3,
                        "density_source": density_source,
                        "difference_pct": difference_pct,
                        "status": "aligned" if difference_pct is not None and difference_pct <= 5.0 else "review",
                    }
                if component_flows is not None:
                    if not isinstance(component_flows, dict):
                        raise ValueError("component_flows_kg_hr must be an object keyed by GreenHub component ID.")
                    mass_split = split_component_flows(
                        component_flows, payload["technology_id"],
                        component_retention_overrides=overrides,
                        concentration_factor=payload.get("concentration_factor"),
                        flux_L_m2_h=selected_flux,
                    )
                    component_balance = calculate_component_split_balance(
                        component_flows, payload["technology_id"],
                        component_retention_overrides=overrides,
                        concentration_factor=payload.get("concentration_factor"),
                        flux_L_m2_h=selected_flux,
                    )
                    if component_stream_id is None:
                        stream_mass_kg_hr = sum(float(value) for value in component_flows.values())
                        density_kg_m3 = 1000.0
                        implied_volume = stream_mass_kg_hr / density_kg_m3 * float(payload["operating_hours_year"])
                        entered_volume = float(payload["feed_volume_m3_year"])
                        difference_pct = (
                            abs(entered_volume - implied_volume) / implied_volume * 100.0
                            if implied_volume > 0.0 else None
                        )
                        feed_volume_consistency = {
                            "entered_volume_m3_year": entered_volume,
                            "stream_mass_flow_kg_hr": stream_mass_kg_hr,
                            "stream_implied_volume_m3_year": implied_volume,
                            "density_basis_kg_m3": density_kg_m3,
                            "density_source": "user-supplied screening convention: 1 kg juice ≈ 1 L",
                            "difference_pct": difference_pct,
                            "status": "aligned" if difference_pct is not None and difference_pct <= 5.0 else "review",
                        }
                    biosteam_unit = simulate_biostimulant_membrane_unit(
                        component_flows, payload["technology_id"],
                        operating_hours_year=payload["operating_hours_year"],
                        flux_L_m2_h=selected_flux,
                        component_retention_overrides=overrides,
                        concentration_factor=payload.get("concentration_factor"),
                    )
                return {
                    "scenario_id": "PR7",
                    "status": (
                        "BioSTEAM membrane-unit simulation; unresolved component fate remains gated"
                        if biosteam_unit and mass_split is not None and not mass_split["complete_mass_split"]
                        else "BioSTEAM membrane-unit simulation; screening scope only"
                        if biosteam_unit else "screening_only; component coverage gate remains open"
                    ),
                    "feed_boundary": "clarified grass juice; no 14-day pre-membrane fermentation/storage",
                    "fermentation_included": False,
                    "pre_membrane_fermentation_included": False,
                    "downstream_digestion_basis": "controlled by the selected anaerobic_digestion scenario; PR7 permeate proceeds downstream",
                    "hormone_capture": [asdict(item) for item in capture],
                    "membrane_screen": {**asdict(membrane), "flux_basis": selected_flux_basis},
                    "resistance_flux_result": asdict(resistance_flux_result) if resistance_flux_result is not None else None,
                    "film_retention_diagnostics": film_retention_diagnostics,
                    "meuf_surfactant_screen": meuf_surfactant_screen,
                    "cip_reagent_screen": cip_reagent_screen,
                    "energy_tea_lca_screen": energy_assessment,
                    "hydraulic_energy_estimate": hydraulic_estimate,
                    "component_mass_split": mass_split,
                    "component_balance": component_balance,
                    "biosteam_unit": biosteam_unit,
                    "component_mass_split_source": component_source if mass_split is not None else None,
                    "component_flows_source": flow_source if component_flows is not None and not component_stream_id else None,
                    "component_stream_id": component_stream_id,
                    "component_retention_override_sources": override_sources if mass_split is not None else {},
                    "feed_volume_consistency": feed_volume_consistency,
                    "mass_balance_readiness": (
                        None if mass_split is None else {
                            "complete": mass_split["complete_mass_split"],
                            "component_fate_complete": mass_split["complete_mass_split"],
                            "mass_balanced": abs(float(mass_split["mass_error_kg_hr"])) <= 1e-8,
                            "unmapped_nonzero_components": list(mass_split["unmapped_component_ids"]),
                            "unmapped_component_flows_kg_hr": {
                                ID: float(component_flows.get(ID, 0.0))
                                for ID in mass_split["unmapped_component_ids"]
                            },
                            "mass_error_kg_hr": mass_split["mass_error_kg_hr"],
                        }
                    ),
                    "tea_readiness": {
                        "status": "partial_screen_only",
                        "available": ["gross_sales_revenue_EUR_year", "membrane_module_CAPEX_EUR_range", "annualized_module_replacement_EUR_year_range"] + (["CIP_reagent_makeup_cost_EUR_year"] if cip_reagent_screen else []),
                        "missing_or_excluded": [
                            "installed skid, installation and balance-of-plant CAPEX", "original membrane quote price year",
                            "labor, crossflow pumping, and CIP downtime, water, energy, and waste-treatment OPEX; optional CIP reagent screen is reported separately when activity inputs are supplied",
                            "validated product quality, saleable yield, and sale-specification price (only the user-supplied €1.50–3.50/L concentrate proxy is available)",
                        ],
                        "replacement_basis": "EUR module purchase cost converted at dated ECB reference FX and straight-line annualized over the user-supplied 2.5–3 year module life; excludes removal, disposal, labor, and downtime; not discounted cash flow",
                        "reference_only": [
                            {"item": "NaOH 50 wt% solution", "value": "€235/t", "source": "https://eucx.eu/katalog/laugen", "note": "Indicative listed price dated 2026-11-01; reference-only until CIP volume and make-up fraction are established; procurement terms require confirmation."},
                            {"item": "Citric acid bulk", "value": "€1,610/t", "source": "https://fdcm.eu/products/citric-acid/", "note": "Supplier listing at €1.61/kg; grade and delivery terms require confirmation; reference-only until CIP volume and make-up fraction are established."},
                            {"item": "Dutch full-scale NF CIP interval", "value": "0.6–0.7 events/year", "source": "https://doi.org/10.1016/j.desal.2020.114865", "note": "Four Dutch drinking-water NF systems treating anoxic groundwater; reference context only. Feed fouling behavior is not transferable to GreenHub grass juice."},
                            {"item": "Dutch full-scale RO CIP interval", "value": "7–17 events/year", "source": "https://doi.org/10.1016/j.desal.2020.114865", "note": "Three Dutch RO plants treating surface water or municipal effluent; reference context only. These frequencies do not replace the user-supplied 48 operating-hour PR7 screening interval."},
                            {"item": "NF CIP protocol comparator", "value": "2 wt% citric acid and 0.01 M NaOH; 3 h each", "source": "https://doi.org/10.1016/j.desal.2020.114865", "note": "Protocol from Dutch full-scale water NF plants; differs from the user-supplied PR7 recipe and is not used to calculate PR7 chemical consumption."},
                            {"item": "NF installed-system comparator", "value": "€300,000–350,000 per 100 m³/h permeate", "source": "https://emis.vito.be/nl/bbt/bbt-tools/selectiesystemen/wass/technieken/nanofiltratie", "note": "Water-treatment benchmark; not scaled into GreenHub CAPEX."},
                            {"item": "Commercial NF package comparator", "value": "about €3,911 per 1 m³/h feed", "source": "https://www.tandfonline.com/doi/full/10.1080/15685551.2015.1092012", "note": "2015 biscuit-effluent estimate converted at current ECB FX, not inflation-adjusted or applied to GreenHub."},
                            {"item": "Vegetable amino-acid biostimulant, 1,000 L", "value": "€2.609/L ex VAT", "source": "https://agrinutriment.fr/produit/acides-amines-metabolisme-azote/", "note": "Public supplier listing for a vegetable-protein hydrolysate with 24% free amino acids and 4.3% total N; unlike PR7 hormone-enriched grass-juice concentrate, therefore context only and excluded from PR7 revenue."},
                        ],
                    },
                    "lca_readiness": {
                        "status": energy_assessment["climate_status"],
                        "missing_or_excluded": [
                            "membrane pumping electricity and pump efficiency", "CIP solution volumes and make-up fraction unless supplied; cleaning wastewater fate; reagent climate factors are available only through the explicit screening-factor option or project-specific overrides",
                            "MEUF surfactant price, acid precipitation inventory, recovery energy, and residual fate; the returned SDS screen is a material-use estimate only", "membrane manufacture and replacement impacts",
                            "product substitution and use-phase fate",
                        ],
                        "reference_only": [
                            {"item": "Hollow-fiber PSF/NMP membrane fabrication", "value": "4.399 kg CO₂-eq/m²", "source": "https://pub.epsilon.slu.se/22742/1/yadav_p_et_al_210311.pdf", "note": "European electricity mix; reference only, not applied to the supplied PES/PA spiral-wound modules."},
                            {"item": "Hollow-fiber PSF/DMAc membrane fabrication", "value": "3.120 kg CO₂-eq/m²", "source": "https://pub.epsilon.slu.se/22742/1/yadav_p_et_al_210311.pdf", "note": "European electricity mix; reference only, not applied to the supplied PES/PA spiral-wound modules."},
                        ],
                    },
                    "limitations": [
                        "Hormone input concentrations and retentions are provisional user-supplied benchmarks; the supplied free/bound split is discussed for a 14-day anaerobic state and is unvalidated for fresh, unfermented PR7 feed.",
                        "Capture values are analyte-equivalent; carrier mass and product purity are excluded.",
                        "Benchmark hormone capture is calculated separately and is not added to the model component mass split unless the selected feed stream contains those hormone pools.",
                        "Area assumes the supplied flux is constant and includes no cleaning downtime or fouling decline.",
                        "Revenue is gross screening revenue only; CAPEX and OPEX are incomplete.",
                        "Membrane module quotes are converted to EUR using the dated ECB reference rate; the original quote date is unknown, and the module-only values exclude installation and balance-of-plant equipment.",
                    ],
                }
        if path.startswith('/api/v1/decision-support/'):
            from Greenhub.application.decision_support_service import DecisionSupportService, options
            from Greenhub.scenario_exploration import run_batch, sensitivity
            if method == 'GET' and path == '/api/v1/decision-support/options':
                return options()
            figure_match = re.fullmatch(r'/api/v1/decision-support/pareto/latest/figures/(protein_enabled|protein_bypass)', path)
            if method == 'GET' and figure_match:
                from Greenhub.settings import PROJECT_ROOT
                group = figure_match.group(1)
                artifact = PROJECT_ROOT / 'results' / 'report_figures' / '10_rvo_2026_support_adjusted' / '07_optimization' / f'pareto_3d_carbon_npv_support_{group}.png'
                if not artifact.is_file():
                    raise APIError(404, 'pareto_figure_not_found', 'The current Pareto figure is not available.')
                return FileResponse(artifact, artifact.name, inline=True)
            figure_index_path = '/api/v1/decision-support/pareto/latest/figure-index'
            if method == 'GET' and path == figure_index_path:
                from Greenhub.settings import PROJECT_ROOT
                index_path = PROJECT_ROOT / 'results' / 'report_figures' / '10_rvo_2026_support_adjusted' / 'rvo_pareto_figure_index.csv'
                if not index_path.is_file():
                    raise APIError(404, 'pareto_figure_index_not_found', 'The current Pareto figure index is not available.')
                figures = []
                with index_path.open(encoding='utf-8-sig', newline='') as stream:
                    for figure_id, row in enumerate(csv.DictReader(stream), 1):
                        relative_path = Path(row['file_location'])
                        artifact = (PROJECT_ROOT / relative_path).resolve()
                        root = (PROJECT_ROOT / 'results' / 'report_figures' / '10_rvo_2026_support_adjusted').resolve()
                        if not artifact.is_relative_to(root) or not artifact.is_file():
                            continue
                        figures.append({
                            'figure_id': figure_id,
                            'figure_name': row.get('figure_name'),
                            'description': row.get('description'),
                            'source_dataset': row.get('source_dataset'),
                            'scenario': row.get('scenario'),
                            'units': row.get('units'),
                            'category': relative_path.parent.as_posix(),
                            'image_url': f"/decision-support/pareto/latest/figures/by-id/{figure_id}",
                        })
                return {'schema_version': 'greenhub-rvo-figures-1.0', 'count': len(figures), 'figures': figures}
            figure_by_id = re.fullmatch(r'/api/v1/decision-support/pareto/latest/figures/by-id/(\d+)', path)
            if method == 'GET' and figure_by_id:
                from Greenhub.settings import PROJECT_ROOT
                index_path = PROJECT_ROOT / 'results' / 'report_figures' / '10_rvo_2026_support_adjusted' / 'rvo_pareto_figure_index.csv'
                figure_id = int(figure_by_id.group(1))
                if not index_path.is_file():
                    raise APIError(404, 'pareto_figure_index_not_found', 'The current Pareto figure index is not available.')
                with index_path.open(encoding='utf-8-sig', newline='') as stream:
                    row = next((item for number, item in enumerate(csv.DictReader(stream), 1) if number == figure_id), None)
                if row is None:
                    raise APIError(404, 'pareto_figure_not_found', 'The requested indexed Pareto figure is not available.')
                artifact = (PROJECT_ROOT / row['file_location']).resolve()
                root = (PROJECT_ROOT / 'results' / 'report_figures' / '10_rvo_2026_support_adjusted').resolve()
                if not artifact.is_relative_to(root) or not artifact.is_file():
                    raise APIError(404, 'pareto_figure_not_found', 'The requested indexed Pareto figure is not available.')
                return FileResponse(artifact, artifact.name, inline=True)
            if method == 'GET' and path == '/api/v1/decision-support/pareto/latest/report':
                from Greenhub.settings import PROJECT_ROOT
                artifact = PROJECT_ROOT / 'results' / 'complete_model_report_rvo_2026' / 'GreenHub_RVO_Pareto_Report.pdf'
                if not artifact.is_file():
                    raise APIError(404, 'pareto_report_not_found', 'The current Pareto report is not available.')
                return FileResponse(artifact, artifact.name)
            if method == 'GET' and path == '/api/v1/decision-support/pareto/latest':
                from Greenhub.settings import RESULTS_DIR
                artifact = RESULTS_DIR / 'pareto_rvo_2026' / 'latest.json'
                if not artifact.exists():
                    raise APIError(404, 'pareto_not_found', 'No replacement RVO Pareto analysis has been published yet.')
                source = json.loads(artifact.read_text(encoding='utf-8'))
                groups = {}
                for name, result in source.get('groups_payload', {}).items():
                    groups[name] = {
                        'group': result.get('group'),
                        'requested_designs': result.get('requested_designs'),
                        'sample_count': result.get('sample_count'),
                        'evaluated_count': result.get('evaluated_count'),
                        'rejected_count': result.get('rejected_count'),
                        'fronts': result.get('fronts', {}),
                        'selected_candidates': result.get('selected_candidates', {}),
                    }
                return {key: source.get(key) for key in (
                    'schema_version', 'created_at_utc', 'seed', 'designs_per_protein_group',
                    'feed_preparation', 'optimization_objectives', 'support_scenarios',
                    'grant_awarding_organization', 'financial_basis', 'carbon_basis',
                    'biomethane_support_conversion', 'limitations', 'groups',
                )} | {'groups_payload': groups}
            job_match = re.fullmatch(r'/api/v1/decision-support/batch-jobs/([a-zA-Z0-9]+)(?:/(cancel|resume))?', path)
            if job_match:
                job_id, action = job_match.groups()
                if method == 'GET' and action is None: return self.decision_batch_jobs.status(job_id)
                if method == 'POST' and action == 'cancel': return self.decision_batch_jobs.cancel(job_id)
                if method == 'POST' and action == 'resume': return self.decision_batch_jobs.resume(job_id)
                raise APIError(405, 'method_not_allowed', 'Unsupported decision batch job action.')
            candidate_match = re.fullmatch(r'/api/v1/decision-support/batch-jobs/([a-zA-Z0-9]+)/candidates/([a-zA-Z0-9_-]+)', path)
            if method == 'GET' and candidate_match:
                return self.decision_batch_jobs.candidate(*candidate_match.groups())
            if method == 'POST' and path == '/api/v1/decision-support/batch-jobs':
                payload = dict(self._read_json(environ))
                allowed = {'configuration','specifications','candidate_overrides','count','seed','mode'}
                has_sampling = 'specifications' in payload
                has_overrides = 'candidate_overrides' in payload
                if set(payload) - allowed or 'configuration' not in payload or has_sampling == has_overrides:
                    raise ValueError('Provide configuration and exactly one of specifications or candidate_overrides, with optional count/seed/mode.')
                return self.decision_batch_jobs.start(payload['configuration'], payload.get('specifications'),
                    candidate_overrides=payload.get('candidate_overrides'), count=payload.get('count',128),
                    seed=payload.get('seed',42), mode=payload.get('mode','design'))
            service = DecisionSupportService(self.simulations)
            if method == 'POST' and path == '/api/v1/decision-support/evaluate':
                payload=dict(self._read_json(environ))
                if set(payload) != {'configuration'}: raise ValueError('Provide configuration only.')
                return service.evaluate(payload['configuration'])
            if method == 'POST' and path in ('/api/v1/decision-support/batch', '/api/v1/decision-support/sensitivity'):
                from pathlib import Path
                from uuid import uuid4
                payload=dict(self._read_json(environ))
                if path.endswith('/batch'):
                    allowed={'configuration','specifications','count','seed','mode','runtime_limit_seconds'}
                    if set(payload)-allowed: raise ValueError('Unknown batch fields.')
                    base=payload.pop('configuration')
                    report=run_batch(service.evaluate,base,**payload)
                else:
                    if set(payload) != {'configuration','variations'}: raise ValueError('Provide configuration and variations.')
                    report=sensitivity(service.evaluate,payload['configuration'],payload['variations'])
                batch_id=uuid4().hex
                root=self.simulations.run_root
                if root is None:
                    from Greenhub.settings import RESULTS_DIR
                    root=RESULTS_DIR/'runs'
                folder=Path(root)/'decision_batches'; folder.mkdir(parents=True,exist_ok=True)
                report['batch_id']=batch_id
                report['artifact_name']='decision_batches/'+batch_id+'.json'
                (folder/(batch_id+'.json')).write_text(json.dumps(report,indent=2,allow_nan=False),encoding='utf-8')
                return report
            match=re.fullmatch(r'/api/v1/decision-support/runs/([a-zA-Z0-9_-]+)',path)
            if method=='GET' and match:
                artifact=self._stored_run_directory(match.group(1))/'decision_support.json'
                if not artifact.exists(): raise APIError(404,'analysis_not_found','No decision-support analysis exists for this run.')
                return json.loads(artifact.read_text(encoding='utf-8'))
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
        self.repository.get(run_id)
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

    def _stored_run_directory(self, run_id: str) -> Path:
        from Greenhub.settings import RESULTS_DIR
        root = Path(self.simulations.run_root or RESULTS_DIR / "runs").resolve()
        context = self.repository.get(run_id)
        candidate = Path(context.run_directory).resolve()
        expected = (root / run_id).resolve()
        if candidate != expected or root not in candidate.parents or not candidate.is_dir():
            raise APIError(404, "run_not_found", f"Stored run '{run_id}' was not found.")
        return candidate

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
            ("Content-Disposition", f'{"inline" if response.inline else "attachment"}; filename="{response.download_name}"'),
            ("Access-Control-Allow-Origin", "*"),
            ("Access-Control-Allow-Methods", "GET, POST, OPTIONS"),
        ])
        return [encoded]


def create_app(run_root: Path | None = None) -> GreenHubAPI:
    return GreenHubAPI(run_root=run_root)


application = create_app()
