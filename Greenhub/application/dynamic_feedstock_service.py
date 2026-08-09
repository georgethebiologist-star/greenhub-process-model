"""Read-only application service for dynamic feedstock preparation."""

from __future__ import annotations

from Greenhub.dynamic_feedstock import solve_feedstock_dynamic_preview


class DynamicFeedstockPreviewService:
    """Expose a small JSON-safe summary without activating model calculations."""

    def get_preview(self, **solve_kwargs: object) -> dict[str, object]:
        result = solve_feedstock_dynamic_preview(**solve_kwargs)
        resolved = sum(1 for row in result.composition_preview if row["value"] is not None)
        blocked = len(result.composition_preview) - resolved
        return {
            "time_steps": len(result.bundles),
            "resolved_field_count": resolved,
            "blocked_field_count": blocked,
            "confidence_summary": dict(result.confidence_summary),
            "source_class_summary": dict(result.source_class_summary),
            "reconciliation_status_summary": dict(result.reconciliation_status_summary),
            "conflict_count": result.conflict_count,
            "reconciled_fields": list(result.reconciled_fields),
            "measured_data_status": dict(result.measured_data_status),
            "calculation_ready": result.calculation_ready,
            "report_artifact_names": {
                "csv": "Greenhub/results/dynamic_feedstock_preview.csv",
                "markdown": "docs/dynamic_feedstock_solver_preview.md",
            },
        }
