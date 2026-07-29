"""Versioned, transport-neutral simulation input contracts."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping

from Greenhub.parameters.enums import CalculationMode, ResolutionMode
from Greenhub.parameters.overrides import ParameterOverride
from Greenhub.parameters.serialization import to_json_compatible

SCHEMA_VERSION = "1.0.0"


@dataclass(frozen=True)
class ScenarioSelection:
    feed_preparation: str = "F2"
    protein_recovery: str = "PR3"
    anaerobic_digestion: str = "AD1"
    biogas_upgrading: str = "BG2"
    nutrient_recovery: str = "NR4"
    process_order: str = "A"

    @property
    def scenario_ids(self) -> tuple[str, ...]:
        return (
            self.feed_preparation,
            self.protein_recovery,
            self.anaerobic_digestion,
            self.biogas_upgrading,
            self.nutrient_recovery,
        )


@dataclass(frozen=True)
class RequestedOutput:
    output_id: str
    detail_level: str = "summary"


@dataclass(frozen=True)
class RequestedPlot:
    plot_id: str
    formats: tuple[str, ...] = ("json", "csv", "png")


@dataclass(frozen=True)
class ValidationIssue:
    code: str
    severity: str
    message: str
    blocking: bool
    process_area: str | None = None
    object_id: str | None = None
    field: str | None = None
    observed_value: object | None = None
    expected_condition: str | None = None


@dataclass(frozen=True)
class SimulationRequest:
    schema_version: str
    request_id: str
    project_id: str
    calculation_mode: CalculationMode = CalculationMode.STRUCTURAL
    resolution_mode: ResolutionMode = ResolutionMode.STEADY_STATE
    selected_month: str | None = "July"
    time_horizon: tuple[str, str] | None = None
    scenarios: ScenarioSelection = field(default_factory=ScenarioSelection)
    feed_overrides: tuple[ParameterOverride, ...] = ()
    operating_overrides: tuple[ParameterOverride, ...] = ()
    design_overrides: tuple[ParameterOverride, ...] = ()
    expert_scientific_overrides: tuple[ParameterOverride, ...] = ()
    requested_outputs: tuple[RequestedOutput, ...] = ()
    requested_plots: tuple[RequestedPlot, ...] = ()
    export_formats: tuple[str, ...] = ("json", "csv")
    strict_validation: bool = True
    user_notes: str | None = None

    def __post_init__(self) -> None:
        if self.schema_version != SCHEMA_VERSION:
            raise ValueError(
                f"Unsupported SimulationRequest schema '{self.schema_version}'; expected '{SCHEMA_VERSION}'."
            )
        if not self.request_id or not self.project_id:
            raise ValueError("SimulationRequest requires request_id and project_id.")
        if self.time_horizon is not None and len(self.time_horizon) != 2:
            raise ValueError("time_horizon must contain exactly two values.")
        if not isinstance(self.strict_validation, bool):
            raise TypeError("strict_validation must be a boolean.")

    @property
    def all_overrides(self) -> tuple[ParameterOverride, ...]:
        return (
            *self.feed_overrides,
            *self.operating_overrides,
            *self.design_overrides,
            *self.expert_scientific_overrides,
        )

    def to_dict(self) -> dict[str, object]:
        return to_json_compatible(self)

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> "SimulationRequest":
        allowed_fields = {
            "schema_version", "request_id", "project_id", "calculation_mode",
            "resolution_mode", "selected_month", "time_horizon", "scenarios",
            "feed_overrides", "operating_overrides", "design_overrides",
            "expert_scientific_overrides", "requested_outputs", "requested_plots",
            "export_formats", "strict_validation", "user_notes",
        }
        unknown_fields = sorted(set(payload) - allowed_fields)
        if unknown_fields:
            raise ValueError(f"Unknown SimulationRequest fields: {', '.join(unknown_fields)}.")
        for required in ("schema_version", "request_id", "project_id"):
            if not isinstance(payload.get(required), str) or not payload[required]:
                raise ValueError(f"SimulationRequest field '{required}' must be a non-empty string.")
        if "strict_validation" in payload and not isinstance(payload["strict_validation"], bool):
            raise TypeError("strict_validation must be a boolean.")
        scenario_payload = payload.get("scenarios") or {}
        scenarios = (
            scenario_payload
            if isinstance(scenario_payload, ScenarioSelection)
            else ScenarioSelection(**dict(scenario_payload))
        )

        def overrides(name: str) -> tuple[ParameterOverride, ...]:
            values = payload.get(name) or ()
            return tuple(
                item if isinstance(item, ParameterOverride) else ParameterOverride(**dict(item))
                for item in values
            )

        return cls(
            schema_version=str(payload.get("schema_version", SCHEMA_VERSION)),
            request_id=str(payload.get("request_id", "")),
            project_id=str(payload.get("project_id", "")),
            calculation_mode=CalculationMode(payload.get("calculation_mode", "structural")),
            resolution_mode=ResolutionMode(payload.get("resolution_mode", "steady_state")),
            selected_month=payload.get("selected_month"),
            time_horizon=tuple(payload["time_horizon"]) if payload.get("time_horizon") else None,
            scenarios=scenarios,
            feed_overrides=overrides("feed_overrides"),
            operating_overrides=overrides("operating_overrides"),
            design_overrides=overrides("design_overrides"),
            expert_scientific_overrides=overrides("expert_scientific_overrides"),
            requested_outputs=tuple(
                item if isinstance(item, RequestedOutput) else RequestedOutput(**dict(item))
                for item in payload.get("requested_outputs", ())
            ),
            requested_plots=tuple(
                item if isinstance(item, RequestedPlot) else RequestedPlot(
                    plot_id=item["plot_id"], formats=tuple(item.get("formats", ("json", "csv", "png")))
                )
                for item in payload.get("requested_plots", ())
            ),
            export_formats=tuple(payload.get("export_formats", ("json", "csv"))),
            strict_validation=payload.get("strict_validation", True),
            user_notes=payload.get("user_notes"),
        )
