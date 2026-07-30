"""Isolated, transport-neutral GreenHub simulation orchestration."""

from __future__ import annotations

from dataclasses import replace
from datetime import datetime, timezone
from pathlib import Path

from Greenhub.integration import create_integrated_greenhub_system
from Greenhub.state_engine import build_state_outputs
from Greenhub.parameters.enums import CalculationMode, ResolutionMode, ResultStatus
from Greenhub.parameters.serialization import write_json

from .contracts import SimulationRequest, ValidationIssue
from .contracts.results import RESULT_SCHEMA_VERSION, NumericalValue, SimulationResult
from .errors import RequestValidationError, RunStateError
from .export_service import ExportService
from .feed_profile_service import FeedProfileService
from .graph_service import GraphService
from .parameter_service import ParameterService
from .plot_service import PlotService
from .result_factory import (
    build_balances,
    build_parameter_results,
    build_process_areas,
    build_products,
    build_stream_results,
    build_unit_results,
    build_utilities,
    build_validation,
    numerical,
)
from .run_context import RunContext, RunState
from .run_repository import RunRepository
from .scenario_service import ScenarioService
from .seasonal_service import SeasonalSimulationService
from Greenhub.time_grid import generate_time_grid


class SimulationService:
    def __init__(
        self,
        repository: RunRepository | None = None,
        run_root: Path | None = None,
    ) -> None:
        self.repository = repository or RunRepository()
        self.run_root = run_root
        self.parameters = ParameterService()
        self.scenarios = ScenarioService()
        self.graphs = GraphService(self.repository)
        self.plots = PlotService(self.repository)
        self.exports = ExportService()
        self.feed_profiles = FeedProfileService()
        self.seasonal = SeasonalSimulationService(self.feed_profiles)

    def validate_request(self, request: SimulationRequest) -> tuple[ValidationIssue, ...]:
        issues = list(self.scenarios.validate_scenario_chain(request.scenarios))
        issues.extend(self.parameters.validate_overrides(request))
        if request.resolution_mode == ResolutionMode.DYNAMIC:
            issues.append(
                ValidationIssue(
                    code="RESOLUTION_MODE_NOT_IMPLEMENTED",
                    severity="error",
                    message=(
                        f"Resolution mode '{request.resolution_mode.value}' is not implemented for the "
                        "selected reference pathway; no steady-state downgrade was performed."
                    ),
                    blocking=True,
                    field="resolution_mode",
                )
            )
        seasonal_values_supplied = any(
            value is not None
            for value in (
                request.start_date, request.end_date, request.time_step,
                request.annual_biomass_target, request.operating_schedule,
                request.feed_supply_profile_id,
            )
        ) or request.initial_storage_inventory.total_mass_kg > 0.0
        if seasonal_values_supplied and request.resolution_mode != ResolutionMode.QUASI_DYNAMIC:
            issues.append(
                ValidationIssue(
                    code="SEASONAL_FIELDS_REQUIRE_QUASI_DYNAMIC",
                    severity="error",
                    message="Seasonal request fields require resolution_mode='quasi_dynamic'.",
                    blocking=True,
                    field="resolution_mode",
                )
            )
        if request.resolution_mode == ResolutionMode.QUASI_DYNAMIC:
            try:
                grid = generate_time_grid(request.start_date, request.end_date, request.time_step or "monthly")
                profile = self.feed_profiles.get_profile(request.feed_supply_profile_id)
                expected_resolution = "daily" if all(item.duration_days == 1 for item in grid) else "monthly"
                if profile.resolution != expected_resolution:
                    raise ValueError(
                        f"Feed profile '{profile.profile_id}' is {profile.resolution}, not {expected_resolution}."
                    )
                if expected_resolution == "daily" and request.operating_schedule is None:
                    raise ValueError("Daily simulation requires an explicit operating_schedule.")
                if profile.normalized and request.annual_biomass_target is None:
                    raise ValueError("A normalized feed profile requires annual_biomass_target.")
            except (KeyError, TypeError, ValueError) as error:
                issues.append(
                    ValidationIssue(
                        code="SEASONAL_REQUEST_INVALID",
                        severity="error",
                        message=str(error).strip("'"),
                        blocking=True,
                        field="feed_supply_profile_id",
                    )
                )
        if request.expert_scientific_overrides and request.calculation_mode != CalculationMode.EXPERT_OVERRIDE:
            issues.append(
                ValidationIssue(
                    code="EXPERT_MODE_REQUIRED",
                    severity="error",
                    message="Expert scientific overrides require calculation_mode='expert_override'.",
                    blocking=True,
                    field="expert_scientific_overrides",
                )
            )
        return tuple(issues)

    def create_run(self, request: SimulationRequest) -> str:
        issues = self.validate_request(request)
        blocking = [item for item in issues if item.blocking]
        if blocking:
            raise RequestValidationError("; ".join(item.message for item in blocking))
        context = RunContext.create(request, self.run_root) if self.run_root else RunContext.create(request)
        context.transition(RunState.RESOLVING_PARAMETERS)
        context.resolved_parameters = self.parameters.resolve_parameters(request)
        self.repository.add(context)
        write_json(context.run_directory / "simulation_request.json", request)
        return context.run_id

    def execute_run(self, run_id: str) -> SimulationResult:
        context = self.repository.get(run_id)
        if context.state not in {RunState.RESOLVING_PARAMETERS}:
            raise RunStateError(f"Run '{run_id}' cannot execute from state '{context.state.value}'.")
        request = context.request
        try:
            context.transition(RunState.BUILDING_SYSTEM)
            model_overrides = self.parameters.resolver.model_overrides(context.resolved_parameters)
            selection = request.scenarios
            seasonal = None
            if request.resolution_mode == ResolutionMode.QUASI_DYNAMIC:
                context.transition(RunState.SIMULATING)
                seasonal = self.seasonal.run(
                    request, context.resolved_parameters, dict(model_overrides)
                )
                model = seasonal.representative_model
            else:
                model = create_integrated_greenhub_system(
                    scenario_id=selection.nutrient_recovery,
                    biogas_upgrading_scenario_id=selection.biogas_upgrading,
                    anaerobic_digestion_scenario_id=selection.anaerobic_digestion,
                    protein_recovery_scenario_id=selection.protein_recovery,
                    feed_preparation_scenario_id=selection.feed_preparation,
                    selected_month=request.selected_month,
                    process_order=selection.process_order,
                    parameter_overrides=model_overrides or None,
                )
                context.transition(RunState.SIMULATING)
                model.simulate()
            context.model = model
            context.transition(RunState.VALIDATING_RESULTS)
            streams = build_stream_results(model)
            units = build_unit_results(model)
            balances = build_balances(model)
            validation = build_validation(model, balances)
            if request.strict_validation and not validation.passed:
                raise RuntimeError("Strict result validation failed.")
            products = build_products(model)
            utilities = build_utilities(units)
            state_outputs = build_state_outputs(model, context.resolved_parameters, request.resolution_mode.value)
            process_areas = build_process_areas(model, request.calculation_mode.value)
            graph = self.graphs.build_process_graph(
                model, run_id, request.calculation_mode.value
            )
            literature_pr1 = (
                request.calculation_mode == CalculationMode.LITERATURE_DEFAULT
                and selection.protein_recovery == "PR1"
            )
            plot_specs = self.plots.specifications(
                run_id,
                "/".join(selection.scenario_ids),
                literature_pr1,
                seasonal=seasonal,
            )
            overall = next(item for item in balances if item.balance_id == "overall_mass")
            total_power = sum((item.demand.value or 0.0) for item in utilities if item.kind == "electricity")
            summary = {
                "boundary_inlet_mass": overall.inlet,
                "boundary_outlet_mass": overall.outlet,
                "overall_mass_residual": overall.residual,
                "total_electricity_demand": numerical(
                    total_power, "kW", "sum of unit power consumption", "structured unit results"
                ),
                "dry_protein_product_mass": numerical(
                    model.streams["dry_protein_product"].F_mass if "dry_protein_product" in model.streams else 0.0,
                    "kg/hr", "wet stream", "BioSTEAM stream",
                ),
            }
            limitations = tuple(
                str(
                    getattr(item, "statement", None)
                    or getattr(item, "description", None)
                    or getattr(item, "limitation", None)
                    or item
                )
                for item in model.limitations
            )
            completed_at = datetime.now(timezone.utc).isoformat()
            result = SimulationResult(
                schema_version=RESULT_SCHEMA_VERSION,
                run_id=run_id,
                request_id=request.request_id,
                status="completed",
                selected_scenarios=selection,
                calculation_mode=request.calculation_mode,
                resolution_mode=request.resolution_mode,
                created_at=context.created_at,
                completed_at=completed_at,
                summary_kpis=summary,
                process_areas=process_areas,
                streams=streams,
                units=units,
                products=products,
                utilities=utilities,
                balances=balances,
                validation=validation,
                warnings=tuple(dict.fromkeys((*model.warnings, *(seasonal.warnings if seasonal else ())))),
                limitations=limitations,
                resolved_parameters=build_parameter_results(context.resolved_parameters),
                model_maturity={item.process_area_id: item.model_maturity for item in process_areas},
                dataset_readiness={"D1": 23, "D2": 25, "D3": 252, "D4": 1, "D5": 0},
                plots=plot_specs,
                graph=graph,
                export_references={},
                reproducibility_metadata=context.reproducibility,
                **{key: tuple(value) for key, value in state_outputs.items() if key != "resolution_mode"},
                **(
                    {
                        "time_grid": seasonal.time_grid,
                        "feed_supply_series": seasonal.feed_supply_series,
                        "storage_inventory_series": seasonal.storage_inventory_series,
                        "throughput_series": seasonal.throughput_series,
                        "capacity_utilization_series": seasonal.capacity_utilization_series,
                        "bottleneck_series": seasonal.bottleneck_series,
                        "product_series": seasonal.product_series,
                        "residual_series": seasonal.residual_series,
                        "utility_series": seasonal.utility_series,
                        "balance_residual_series": seasonal.balance_residual_series,
                        "process_state_series": seasonal.process_state_series,
                        "seasonal_summary": seasonal.seasonal_summary,
                    }
                    if seasonal else {}
                ),
            )
            context.result = result
            context.transition(RunState.GENERATING_OUTPUTS)
            references = self.exports.export_run(context, result, self.plots)
            result = replace(result, export_references=references)
            context.result = result
            write_json(context.run_directory / "simulation_result.json", result)
            context.transition(RunState.COMPLETED)
            return result
        except Exception as error:
            context.error = str(error)
            context.transition(RunState.FAILED)
            write_json(
                context.run_directory / "run_manifest.json",
                {
                    "run_id": context.run_id,
                    "status": "failed",
                    "state_history": context.state_history,
                    "error": str(error),
                },
            )
            raise

    def get_run_status(self, run_id: str) -> dict[str, object]:
        context = self.repository.get(run_id)
        return {
            "run_id": run_id,
            "status": context.state.value,
            "error": context.error,
            "state_history": tuple(context.state_history),
        }
