"""Immutable canonical parameter registry."""

from __future__ import annotations

from types import MappingProxyType
from typing import Iterable, Iterator

from .models import CanonicalParameter, ParameterCandidate


class ParameterRegistry:
    """Validated immutable definitions and source candidates."""

    def __init__(
        self,
        parameters: Iterable[CanonicalParameter],
        candidates: Iterable[ParameterCandidate],
    ) -> None:
        definitions: dict[str, CanonicalParameter] = {}
        for parameter in parameters:
            if parameter.parameter_id in definitions:
                raise ValueError(f"Duplicate canonical parameter ID '{parameter.parameter_id}'.")
            definitions[parameter.parameter_id] = parameter
        candidate_map: dict[str, list[ParameterCandidate]] = {key: [] for key in definitions}
        candidate_ids: set[str] = set()
        for candidate in candidates:
            if candidate.candidate_id in candidate_ids:
                raise ValueError(f"Duplicate parameter candidate ID '{candidate.candidate_id}'.")
            if candidate.parameter_id not in definitions:
                raise KeyError(
                    f"Candidate '{candidate.candidate_id}' references unknown parameter "
                    f"'{candidate.parameter_id}'."
                )
            candidate_ids.add(candidate.candidate_id)
            candidate_map[candidate.parameter_id].append(candidate)
        self._parameters = MappingProxyType(definitions)
        self._candidates = MappingProxyType(
            {
                key: tuple(sorted(values, key=lambda item: item.candidate_id))
                for key, values in candidate_map.items()
            }
        )

    def __len__(self) -> int:
        return len(self._parameters)

    def __iter__(self) -> Iterator[CanonicalParameter]:
        for key in sorted(self._parameters):
            yield self._parameters[key]

    def get(self, parameter_id: str) -> CanonicalParameter:
        try:
            return self._parameters[parameter_id]
        except KeyError as error:
            raise KeyError(f"Unknown canonical parameter '{parameter_id}'.") from error

    def candidates_for(self, parameter_id: str) -> tuple[ParameterCandidate, ...]:
        self.get(parameter_id)
        return self._candidates[parameter_id]

    @property
    def candidates(self) -> tuple[ParameterCandidate, ...]:
        return tuple(
            candidate
            for parameter_id in sorted(self._candidates)
            for candidate in self._candidates[parameter_id]
        )
