"""Immutable canonical parameter and resolution records."""

from __future__ import annotations

from dataclasses import dataclass, field
from math import isfinite
from typing import Any

from .enums import (
    ActivationState,
    CandidateKind,
    CalculationMode,
    EditabilityCategory,
    EditableMode,
    ReadinessState,
    ValueStatus,
)

JSONScalar = str | int | float | bool | None


def _validate_optional_number(value: float | None, name: str) -> None:
    if value is not None and not isfinite(float(value)):
        raise ValueError(f"{name} must be finite or null.")


@dataclass(frozen=True)
class Uncertainty:
    """Directly reported uncertainty without inferred distributions."""

    description: str
    lower: float | None = None
    upper: float | None = None
    unit: str | None = None

    def __post_init__(self) -> None:
        _validate_optional_number(self.lower, "Uncertainty lower bound")
        _validate_optional_number(self.upper, "Uncertainty upper bound")


@dataclass(frozen=True)
class Applicability:
    """Explicit hard-gate context for one parameter candidate."""

    scenario_ids: tuple[str, ...] = ()
    months: tuple[str, ...] = ()
    technologies: tuple[str, ...] = ()
    material_types: tuple[str, ...] = ()
    calculation_modes: tuple[CalculationMode, ...] = ()
    conditions: tuple[tuple[str, JSONScalar], ...] = ()


@dataclass(frozen=True)
class CanonicalParameter:
    """One unique parameter definition exposed to calculations and clients."""

    parameter_id: str
    display_name: str
    description: str
    process_area: str
    unit_operation: str | None = None
    unit_id: str | None = None
    scenario_ids: tuple[str, ...] = ()
    technology: str | None = None
    component: str | None = None
    material_type: str | None = None
    value: JSONScalar = None
    original_value: JSONScalar = None
    original_unit: str | None = None
    normalized_value: JSONScalar = None
    normalized_unit: str | None = None
    basis: str | None = None
    data_type: str = "number"
    source_dataset: str | None = None
    source_row_id: str | None = None
    source_title: str | None = None
    stable_identifier: str | None = None
    exact_source_location: str | None = None
    evidence_class: ValueStatus = ValueStatus.MISSING
    transferability_class: str | None = None
    quality_class: str | None = None
    uncertainty: Uncertainty | None = None
    applicability_conditions: Applicability = field(default_factory=Applicability)
    physical_lower_bound: float | None = None
    physical_upper_bound: float | None = None
    recommended_range: tuple[float | None, float | None] | None = None
    editability_category: EditabilityCategory = EditabilityCategory.IMMUTABLE_PROVENANCE
    editable_mode: EditableMode = EditableMode.READ_ONLY
    rebuild_required: bool = False
    dependency_parameter_ids: tuple[str, ...] = ()
    readiness_state: ReadinessState = ReadinessState.D3
    activation_state: ActivationState = ActivationState.REFERENCE_ONLY
    warnings: tuple[str, ...] = ()
    allowed_options: tuple[JSONScalar, ...] = ()
    input_type: str = "number"
    step: float | None = None
    affected_outputs: tuple[str, ...] = ()
    affected_units: tuple[str, ...] = ()
    affected_plots: tuple[str, ...] = ()
    model_parameter_name: str | None = None

    def __post_init__(self) -> None:
        if not self.parameter_id or not self.display_name:
            raise ValueError("Canonical parameters require parameter_id and display_name.")
        for value, name in (
            (self.physical_lower_bound, "Physical lower bound"),
            (self.physical_upper_bound, "Physical upper bound"),
            (self.step, "Step"),
        ):
            _validate_optional_number(value, name)
        if (
            self.physical_lower_bound is not None
            and self.physical_upper_bound is not None
            and self.physical_lower_bound > self.physical_upper_bound
        ):
            raise ValueError(f"Invalid physical bounds for '{self.parameter_id}'.")


@dataclass(frozen=True)
class ParameterCandidate:
    """One immutable candidate value for a canonical parameter."""

    candidate_id: str
    parameter_id: str
    value: JSONScalar
    unit: str | None
    source_kind: CandidateKind
    value_status: ValueStatus
    source_dataset: str | None = None
    source_row_id: str | None = None
    source_title: str | None = None
    stable_identifier: str | None = None
    exact_source_location: str | None = None
    evidence_class: str | None = None
    transferability_class: str | None = None
    quality_class: str | None = None
    basis: str | None = None
    uncertainty: Uncertainty | None = None
    applicability: Applicability = field(default_factory=Applicability)
    activation_state: ActivationState = ActivationState.ACTIVE
    readiness_state: ReadinessState = ReadinessState.D3
    warnings: tuple[str, ...] = ()
    provenance_chain: tuple[str, ...] = ()
    selection_priority: int = 100

    def __post_init__(self) -> None:
        if not self.candidate_id or not self.parameter_id:
            raise ValueError("Parameter candidates require candidate_id and parameter_id.")
        if isinstance(self.value, float) and not isfinite(self.value):
            raise ValueError("Parameter candidate values must be finite or null.")


@dataclass(frozen=True)
class RejectedCandidate:
    candidate_id: str
    reason: str


@dataclass(frozen=True)
class ResolvedParameter:
    """Deterministic resolution result, including rejected alternatives."""

    parameter_id: str
    active_value: JSONScalar
    unit: str | None
    source: str | None
    selected_candidate: ParameterCandidate | None
    rejected_candidates: tuple[RejectedCandidate, ...]
    selection_reason: str
    evidence_class: str | None
    transferability_class: str | None
    override_status: str
    warnings: tuple[str, ...]
    dependency_status: str
    blocked: bool = False


@dataclass(frozen=True)
class EditableParameter:
    """Dashboard-neutral metadata for one parameter control."""

    parameter_id: str
    label: str
    description: str
    value: JSONScalar
    default_value: JSONScalar
    unit: str | None
    input_type: str
    minimum: float | None
    maximum: float | None
    step: float | None
    allowed_options: tuple[JSONScalar, ...]
    editable_mode: EditableMode
    scientific_warning: str | None
    provenance: tuple[str, ...]
    rebuild_required: bool
    affected_outputs: tuple[str, ...]
    affected_units: tuple[str, ...]
    affected_plots: tuple[str, ...]


def scalar_type(value: Any) -> str:
    if isinstance(value, bool):
        return "boolean"
    if isinstance(value, str):
        return "string"
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return "number"
    return "null"
