"""Deterministic, inspectable parameter candidate selection."""

from __future__ import annotations

from dataclasses import dataclass

from .enums import ActivationState, CalculationMode, CandidateKind
from .models import ParameterCandidate, RejectedCandidate


_PRECEDENCE = {
    CandidateKind.RUN_OVERRIDE: 1,
    CandidateKind.PROJECT_OVERRIDE: 2,
    CandidateKind.MEASURED_PROJECT: 3,
    CandidateKind.CALIBRATED_PROJECT: 4,
    CandidateKind.LITERATURE_DEFAULT: 5,
    CandidateKind.WORKBOOK: 6,
    CandidateKind.STRUCTURAL_PLACEHOLDER: 7,
    CandidateKind.MISSING: 8,
}


@dataclass(frozen=True)
class SelectionContext:
    calculation_mode: CalculationMode
    selected_scenarios: tuple[str, ...]
    month: str | None
    technologies: tuple[str, ...] = ()
    material_types: tuple[str, ...] = ()


@dataclass(frozen=True)
class CandidateSelection:
    selected: ParameterCandidate | None
    rejected: tuple[RejectedCandidate, ...]
    reason: str


def _allowed_in_mode(candidate: ParameterCandidate, mode: CalculationMode) -> bool:
    if candidate.source_kind == CandidateKind.LITERATURE_DEFAULT:
        return mode in {CalculationMode.LITERATURE_DEFAULT, CalculationMode.EXPERT_OVERRIDE}
    if candidate.source_kind == CandidateKind.CALIBRATED_PROJECT:
        return mode in {CalculationMode.CALIBRATED, CalculationMode.EXPERT_OVERRIDE}
    if candidate.source_kind == CandidateKind.MEASURED_PROJECT:
        return mode in {
            CalculationMode.PROJECT_DATA,
            CalculationMode.CALIBRATED,
            CalculationMode.EXPERT_OVERRIDE,
        }
    return True


def _hard_gate(candidate: ParameterCandidate, context: SelectionContext) -> str | None:
    if candidate.activation_state != ActivationState.ACTIVE:
        return f"activation state is {candidate.activation_state.value}"
    if candidate.value is None:
        return "candidate value is missing"
    if not _allowed_in_mode(candidate, context.calculation_mode):
        return f"source kind is not enabled in {context.calculation_mode.value} mode"
    applicability = candidate.applicability
    if applicability.calculation_modes and context.calculation_mode not in applicability.calculation_modes:
        return "calculation mode is outside candidate applicability"
    if applicability.scenario_ids and not set(applicability.scenario_ids) & set(context.selected_scenarios):
        return "selected scenario does not match"
    if applicability.months and context.month:
        months = {item.casefold() for item in applicability.months}
        if context.month.casefold() not in months and not months & {"all", "annual"}:
            return "selected month does not match"
    if applicability.technologies and not set(applicability.technologies) & set(context.technologies):
        return "technology does not match"
    if applicability.material_types and context.material_types:
        if not set(applicability.material_types) & set(context.material_types):
            return "material type does not match"
    return None


def select_candidate(
    candidates: tuple[ParameterCandidate, ...],
    context: SelectionContext,
) -> CandidateSelection:
    """Apply hard gates and precedence without opaque scoring or guessed ties."""

    eligible: list[ParameterCandidate] = []
    rejected: list[RejectedCandidate] = []
    for candidate in candidates:
        reason = _hard_gate(candidate, context)
        if reason:
            rejected.append(RejectedCandidate(candidate.candidate_id, reason))
        else:
            eligible.append(candidate)
    if not eligible:
        return CandidateSelection(None, tuple(rejected), "No candidate passed the explicit applicability gates.")
    best_precedence = min(_PRECEDENCE[item.source_kind] for item in eligible)
    finalists = [item for item in eligible if _PRECEDENCE[item.source_kind] == best_precedence]
    if len(finalists) > 1:
        specificities = {
            item.candidate_id: (
                bool(item.applicability.scenario_ids),
                bool(item.applicability.months),
                bool(item.applicability.technologies),
                bool(item.applicability.material_types),
            )
            for item in finalists
        }
        best_specificity = max(sum(value) for value in specificities.values())
        finalists = [item for item in finalists if sum(specificities[item.candidate_id]) == best_specificity]
    if len(finalists) > 1:
        best_priority = min(item.selection_priority for item in finalists)
        finalists = [item for item in finalists if item.selection_priority == best_priority]
    if len(finalists) != 1:
        for candidate in finalists:
            rejected.append(
                RejectedCandidate(candidate.candidate_id, "ambiguous equally ranked applicable candidate")
            )
        return CandidateSelection(
            None,
            tuple(sorted(rejected, key=lambda item: item.candidate_id)),
            "Resolution is blocked because equally ranked candidates cannot be distinguished defensibly.",
        )
    selected = finalists[0]
    rejected.extend(
        RejectedCandidate(item.candidate_id, "lower precedence than selected candidate")
        for item in eligible
        if item.candidate_id != selected.candidate_id
    )
    return CandidateSelection(
        selected,
        tuple(sorted(rejected, key=lambda item: item.candidate_id)),
        f"Selected {selected.candidate_id} by explicit source precedence and applicability gates.",
    )
