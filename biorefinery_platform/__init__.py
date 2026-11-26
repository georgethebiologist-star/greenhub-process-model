"""Shared, project-neutral primitives for multi-project biorefinery tools."""

from .registry import ProjectAdapter, ProjectDescriptor, ProjectRegistry

__all__ = ["ProjectAdapter", "ProjectDescriptor", "ProjectRegistry"]
