"""GreenHub project plug-in for the project-neutral biorefinery platform."""

from __future__ import annotations

import json
from pathlib import Path

from Greenhub.integration import create_integrated_greenhub_system
from biorefinery_platform import ProjectAdapter, ProjectDescriptor, ProjectRegistry


_DESCRIPTOR_PATH = Path(__file__).resolve().parents[1] / "data" / "platform" / "projects" / "greenhub.json"


def build_greenhub_model(request: object, month: str, model_overrides: dict[str, object]):
    """Build the existing GreenHub integrated pathway from a standard request.

    The request's ``project_id`` remains a compatibility/provenance label; project
    selection is a deployment-level concern until a versioned API selector exists.
    """

    selection = request.scenarios
    return create_integrated_greenhub_system(
        scenario_id=selection.nutrient_recovery,
        biogas_upgrading_scenario_id=selection.biogas_upgrading,
        anaerobic_digestion_scenario_id=selection.anaerobic_digestion,
        protein_recovery_scenario_id=selection.protein_recovery,
        feed_preparation_scenario_id=selection.feed_preparation,
        selected_month=month,
        process_order=selection.process_order,
        parameter_overrides=model_overrides or None,
        biostimulant_route=(
            None if request.biostimulant_route is None
            else request.biostimulant_route.to_dict()
        ),
    )


with _DESCRIPTOR_PATH.open("r", encoding="utf-8") as _file:
    GREENHUB_PROJECT_DESCRIPTOR = ProjectDescriptor.from_mapping(json.load(_file))

GREENHUB_PROJECT_ADAPTER = ProjectAdapter(
    descriptor=GREENHUB_PROJECT_DESCRIPTOR,
    build_model=build_greenhub_model,
)


def default_project_registry() -> ProjectRegistry:
    """Return the currently runnable project registry (GreenHub only)."""

    return ProjectRegistry((GREENHUB_PROJECT_ADAPTER,))
