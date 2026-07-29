"""Provenance extraction for resolved parameters."""

from __future__ import annotations

from .models import ResolvedParameter


def provenance_record(parameter: ResolvedParameter) -> dict[str, object]:
    selected = parameter.selected_candidate
    return {
        "parameter_id": parameter.parameter_id,
        "candidate_id": selected.candidate_id if selected else None,
        "source_dataset": selected.source_dataset if selected else None,
        "source_row_id": selected.source_row_id if selected else None,
        "source_title": selected.source_title if selected else None,
        "stable_identifier": selected.stable_identifier if selected else None,
        "exact_source_location": selected.exact_source_location if selected else None,
        "value_status": selected.value_status.value if selected else "missing",
        "transferability_class": selected.transferability_class if selected else None,
        "provenance_chain": list(selected.provenance_chain) if selected else [],
        "warnings": list(parameter.warnings),
    }
