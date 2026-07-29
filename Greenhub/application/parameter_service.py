"""Pure-Python parameter discovery, validation, and resolution service."""

from __future__ import annotations

from typing import Mapping

from Greenhub.parameters import (
    ParameterResolver,
    SelectionContext,
    build_editable_registry,
    load_default_registry,
)

from .contracts import SimulationRequest, ValidationIssue


class ParameterService:
    def __init__(self) -> None:
        self.registry = load_default_registry()
        self.resolver = ParameterResolver(self.registry)

    def list_parameters(self, filters: Mapping[str, object] | None = None):
        parameters = tuple(self.registry)
        if not filters:
            return parameters
        return tuple(
            item
            for item in parameters
            if all(getattr(item, key, None) == value for key, value in filters.items())
        )

    def get_parameter(self, parameter_id: str):
        return self.registry.get(parameter_id)

    def list_parameter_sources(self, parameter_id: str):
        return self.registry.candidates_for(parameter_id)

    def _context(self, request: SimulationRequest) -> SelectionContext:
        return SelectionContext(
            calculation_mode=request.calculation_mode,
            selected_scenarios=request.scenarios.scenario_ids,
            month=request.selected_month,
        )

    def validate_overrides(self, request: SimulationRequest) -> tuple[ValidationIssue, ...]:
        try:
            self.resolver.resolve(self._context(request), run_overrides=request.all_overrides)
        except (KeyError, TypeError, ValueError) as error:
            return (
                ValidationIssue(
                    code="PARAMETER_OVERRIDE_INVALID",
                    severity="error",
                    message=str(error),
                    blocking=True,
                    field="parameter_overrides",
                ),
            )
        return ()

    def resolve_parameters(self, request: SimulationRequest):
        return self.resolver.resolve(
            self._context(request),
            run_overrides=request.all_overrides,
        )

    def list_editable_parameters(self, request: SimulationRequest):
        return build_editable_registry(self.registry, self.resolve_parameters(request))
