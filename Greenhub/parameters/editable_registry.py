"""Frontend-neutral editable parameter metadata."""

from __future__ import annotations

from .enums import EditableMode
from .models import EditableParameter, ResolvedParameter
from .registry import ParameterRegistry


def build_editable_registry(
    registry: ParameterRegistry,
    resolved: tuple[ResolvedParameter, ...],
) -> tuple[EditableParameter, ...]:
    by_id = {item.parameter_id: item for item in resolved}
    controls = []
    for definition in registry:
        item = by_id[definition.parameter_id]
        selected = item.selected_candidate
        warning = "; ".join((*definition.warnings, *item.warnings)) or None
        controls.append(
            EditableParameter(
                parameter_id=definition.parameter_id,
                label=definition.display_name,
                description=definition.description,
                value=item.active_value,
                default_value=definition.normalized_value,
                unit=definition.normalized_unit,
                input_type=definition.input_type,
                minimum=definition.physical_lower_bound,
                maximum=definition.physical_upper_bound,
                step=definition.step,
                allowed_options=definition.allowed_options,
                editable_mode=definition.editable_mode,
                scientific_warning=warning,
                provenance=selected.provenance_chain if selected else (),
                rebuild_required=definition.rebuild_required,
                affected_outputs=definition.affected_outputs,
                affected_units=definition.affected_units,
                affected_plots=definition.affected_plots,
            )
        )
    return tuple(controls)
