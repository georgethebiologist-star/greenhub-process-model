"""Minimal project plug-in registry; project chemistry stays in project packages."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Iterable, Mapping


ModelBuilder = Callable[[object, str, Mapping[str, object]], object]


@dataclass(frozen=True)
class ProjectDescriptor:
    project_id: str
    display_name: str
    status: str
    adapter_entrypoint: str
    technology_family_ids: tuple[str, ...]
    route_template_ids: tuple[str, ...] = ()
    description: str = ""
    data_context: str = ""

    @classmethod
    def from_mapping(cls, values: Mapping[str, object]) -> "ProjectDescriptor":
        required = ("project_id", "display_name", "status", "adapter_entrypoint")
        missing = [key for key in required if not str(values.get(key, "")).strip()]
        if missing:
            raise ValueError("Project descriptor is missing: " + ", ".join(missing))
        family_ids = values.get("technology_family_ids", ())
        if isinstance(family_ids, str) or not isinstance(family_ids, Iterable):
            raise ValueError("technology_family_ids must be a sequence of family identifiers.")
        route_template_ids = values.get("route_template_ids", ())
        if isinstance(route_template_ids, str) or not isinstance(route_template_ids, Iterable):
            raise ValueError("route_template_ids must be a sequence of route-template identifiers.")
        return cls(
            project_id=str(values["project_id"]),
            display_name=str(values["display_name"]),
            status=str(values["status"]),
            adapter_entrypoint=str(values["adapter_entrypoint"]),
            technology_family_ids=tuple(str(item) for item in family_ids),
            route_template_ids=tuple(str(item) for item in route_template_ids),
            description=str(values.get("description", "")),
            data_context=str(values.get("data_context", "")),
        )


@dataclass(frozen=True)
class ProjectAdapter:
    descriptor: ProjectDescriptor
    build_model: ModelBuilder


class ProjectRegistry:
    """Maps deployment-selected projects to their model builders.

    The generic registry does not import a project package. A deployment composes
    registrations explicitly, keeping chemistry and project-specific defaults out
    of the shared platform layer.
    """

    def __init__(self, adapters: Iterable[ProjectAdapter] = ()) -> None:
        self._adapters: dict[str, ProjectAdapter] = {}
        for adapter in adapters:
            self.register(adapter)

    def register(self, adapter: ProjectAdapter) -> None:
        project_id = adapter.descriptor.project_id
        if project_id in self._adapters:
            raise ValueError(f"Project '{project_id}' is already registered.")
        self._adapters[project_id] = adapter

    def get(self, project_id: str) -> ProjectAdapter:
        try:
            return self._adapters[project_id]
        except KeyError as error:
            raise KeyError(f"Project '{project_id}' is not registered.") from error

    def list_descriptors(self) -> tuple[ProjectDescriptor, ...]:
        return tuple(self._adapters[key].descriptor for key in sorted(self._adapters))
