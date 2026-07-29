"""Canonical parameter resolver with separate override layers."""

from __future__ import annotations

from dataclasses import replace
from typing import Iterable, Mapping

from .enums import ActivationState, CandidateKind, ValueStatus
from .models import ParameterCandidate, ResolvedParameter
from .overrides import ParameterOverride
from .registry import ParameterRegistry
from .selectors import SelectionContext, select_candidate
from .validation import validate_value


def _override_candidate(
    registry: ParameterRegistry,
    override: ParameterOverride,
    kind: CandidateKind,
) -> ParameterCandidate:
    definition = registry.get(override.parameter_id)
    value = validate_value(definition, override.value, override.unit)
    return ParameterCandidate(
        candidate_id=f"{kind.value}:{override.parameter_id}",
        parameter_id=override.parameter_id,
        value=value,
        unit=definition.normalized_unit,
        source_kind=kind,
        value_status=ValueStatus.EXPLICIT_USER_OVERRIDE,
        source_title=override.requester or kind.value,
        exact_source_location=override.reason,
        activation_state=ActivationState.ACTIVE,
        warnings=tuple(filter(None, (override.provenance_note,))),
        provenance_chain=(kind.value, override.parameter_id),
    )


class ParameterResolver:
    def __init__(self, registry: ParameterRegistry) -> None:
        self.registry = registry

    def resolve(
        self,
        context: SelectionContext,
        *,
        run_overrides: Iterable[ParameterOverride] = (),
        project_overrides: Iterable[ParameterOverride] = (),
    ) -> tuple[ResolvedParameter, ...]:
        run_map = {item.parameter_id: item for item in run_overrides}
        project_map = {item.parameter_id: item for item in project_overrides}
        unknown = (set(run_map) | set(project_map)) - {item.parameter_id for item in self.registry}
        if unknown:
            raise KeyError(f"Overrides reference unknown parameters: {sorted(unknown)}")
        resolved = []
        for definition in self.registry:
            candidates = list(self.registry.candidates_for(definition.parameter_id))
            if definition.parameter_id in project_map:
                candidates.append(
                    _override_candidate(
                        self.registry,
                        project_map[definition.parameter_id],
                        CandidateKind.PROJECT_OVERRIDE,
                    )
                )
            if definition.parameter_id in run_map:
                candidates.append(
                    _override_candidate(
                        self.registry,
                        run_map[definition.parameter_id],
                        CandidateKind.RUN_OVERRIDE,
                    )
                )
            selection = select_candidate(tuple(candidates), context)
            selected = selection.selected
            dependencies = tuple(
                dependency
                for dependency in definition.dependency_parameter_ids
                if dependency not in {item.parameter_id for item in resolved if not item.blocked}
            )
            blocked = selected is None or bool(dependencies)
            warnings = tuple(selected.warnings if selected else ())
            if dependencies:
                warnings += (f"Unresolved dependencies: {dependencies}",)
            resolved.append(
                ResolvedParameter(
                    parameter_id=definition.parameter_id,
                    active_value=None if blocked else selected.value,
                    unit=definition.normalized_unit,
                    source=selected.source_title if selected else None,
                    selected_candidate=selected,
                    rejected_candidates=selection.rejected,
                    selection_reason=selection.reason,
                    evidence_class=selected.value_status.value if selected else None,
                    transferability_class=selected.transferability_class if selected else None,
                    override_status=(
                        selected.source_kind.value
                        if selected and selected.source_kind in {CandidateKind.RUN_OVERRIDE, CandidateKind.PROJECT_OVERRIDE}
                        else "not_overridden"
                    ),
                    warnings=warnings,
                    dependency_status="resolved" if not dependencies else "blocked",
                    blocked=blocked,
                )
            )
        return tuple(resolved)

    def model_overrides(
        self,
        resolved: Iterable[ResolvedParameter],
    ) -> Mapping[str, object]:
        values: dict[str, object] = {}
        for item in resolved:
            definition = self.registry.get(item.parameter_id)
            if item.blocked or definition.model_parameter_name is None:
                continue
            if item.selected_candidate and item.selected_candidate.source_kind in {
                CandidateKind.RUN_OVERRIDE,
                CandidateKind.PROJECT_OVERRIDE,
                CandidateKind.LITERATURE_DEFAULT,
                CandidateKind.MEASURED_PROJECT,
                CandidateKind.CALIBRATED_PROJECT,
            }:
                values[definition.model_parameter_name] = item.active_value
        return values
