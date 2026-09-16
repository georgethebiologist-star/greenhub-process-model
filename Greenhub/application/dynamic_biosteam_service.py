"""Opt-in application surface for the isolated dynamic BioSTEAM adapter."""

from __future__ import annotations

from Greenhub.dynamic_biosteam_adapter import (
    DynamicBioSTEAMAdapterConfig,
    DynamicBioSTEAMAdapterGridResult,
    DynamicBioSTEAMAdapterResult,
    build_dynamic_biosteam_calculation_shadow_system,
    build_dynamic_biosteam_calculation_shadow_system_grid,
    build_dynamic_biosteam_shadow_system,
    build_dynamic_biosteam_shadow_system_grid,
    build_dynamic_biosteam_shadow_flowsheet,
    build_dynamic_biosteam_shadow_grid,
)


def get_dynamic_biosteam_calculation_shadow_system(
    time_label: str = "2026-05",
    basis_feed_kg_per_hr: float = 1000.0,
) -> dict[str, object]:
    """Return a JSON-safe summary of one calculation-owning shadow system."""

    result = build_dynamic_biosteam_calculation_shadow_system(
        DynamicBioSTEAMAdapterConfig(
            time_label=time_label,
            basis_feed_kg_per_hr=basis_feed_kg_per_hr,
        )
    )
    return {
        "scenario_id": result.config.scenario_id,
        "time_label": result.config.time_label,
        "basis_feed_kg_per_hr": result.config.basis_feed_kg_per_hr,
        "system_id": result.system.ID if result.system is not None else None,
        "unit_ids": [unit.ID for unit in result.units.values()],
        "stream_ids": [stream.ID for stream in result.streams.values()],
        "payloads": result.payloads.to_dict(),
        "validation": result.validation.to_dict(),
        "can_drive_calculation_shadow_system": (
            result.can_drive_calculation_shadow_system
        ),
        "can_drive_simulation": result.can_drive_simulation,
        "validated_simulation_ready": result.validated_simulation_ready,
        "warnings": list(result.warnings),
        "blockers": list(result.blockers),
        "activation_status": result.activation_status,
    }


def get_dynamic_biosteam_calculation_shadow_grid(
    basis_feed_kg_per_hr: float = 1000.0,
) -> dict[str, object]:
    """Return a JSON-safe summary of the monthly calculation shadow batch."""

    result = build_dynamic_biosteam_calculation_shadow_system_grid(
        DynamicBioSTEAMAdapterConfig(basis_feed_kg_per_hr=basis_feed_kg_per_hr)
    )
    return {
        "scenario_id": result.config.scenario_id,
        "basis_feed_kg_per_hr": result.config.basis_feed_kg_per_hr,
        "time_labels": list(result.time_labels),
        "system_ids": [
            step.system.ID if step.system is not None else None
            for step in result.step_results
        ],
        "all_steps_parity_passed": result.all_steps_parity_passed,
        "all_steps_calculation_shadow_ready": (
            result.all_steps_calculation_shadow_ready
        ),
        "all_empirical_flowsheets_unchanged": (
            result.all_empirical_flowsheets_unchanged
        ),
        "warning_counts": dict(result.warning_counts),
        "blocker_counts": dict(result.blocker_counts),
        "can_drive_simulation": False,
        "validated_simulation_ready": False,
        "activation_status": result.activation_status,
    }


def get_dynamic_biosteam_shadow_preview(
    time_label: str = "2026-05",
    basis_feed_kg_per_hr: float = 1000.0,
) -> DynamicBioSTEAMAdapterResult:
    """Build one report-only shadow step without touching empirical services."""

    return build_dynamic_biosteam_shadow_flowsheet(
        DynamicBioSTEAMAdapterConfig(
            time_label=time_label,
            basis_feed_kg_per_hr=basis_feed_kg_per_hr,
        )
    )


def get_dynamic_biosteam_shadow_grid(
    basis_feed_kg_per_hr: float = 1000.0,
) -> DynamicBioSTEAMAdapterGridResult:
    """Build the independent monthly shadow batch without dynamic scheduling."""

    return build_dynamic_biosteam_shadow_grid(
        DynamicBioSTEAMAdapterConfig(basis_feed_kg_per_hr=basis_feed_kg_per_hr)
    )


def get_dynamic_biosteam_shadow_system(
    time_label: str = "2026-05",
    basis_feed_kg_per_hr: float = 1000.0,
) -> dict[str, object]:
    """Return a JSON-safe summary of one isolated six-unit system."""

    result = build_dynamic_biosteam_shadow_system(
        time_label=time_label,
        basis_feed_kg_per_hr=basis_feed_kg_per_hr,
    )
    return {
        "scenario_id": result.config.scenario_id,
        "time_label": result.config.time_label,
        "basis_feed_kg_per_hr": result.config.basis_feed_kg_per_hr,
        "system_id": result.system.ID,
        "unit_ids": [unit.ID for unit in result.units.values()],
        "stream_ids": [stream.ID for stream in result.streams.values()],
        "mass_balance": result.mass_balance.to_dict(),
        "can_drive_shadow_system": result.can_drive_shadow_system,
        "can_drive_simulation": result.can_drive_simulation,
        "validated_simulation_ready": result.validated_simulation_ready,
        "warnings": list(result.warnings),
        "blockers": list(result.blockers),
        "activation_status": result.activation_status,
    }


def get_dynamic_biosteam_shadow_system_grid(
    basis_feed_kg_per_hr: float = 1000.0,
) -> dict[str, object]:
    """Return a JSON-safe summary of independent monthly shadow systems."""

    result = build_dynamic_biosteam_shadow_system_grid(
        DynamicBioSTEAMAdapterConfig(basis_feed_kg_per_hr=basis_feed_kg_per_hr)
    )
    return {
        "scenario_id": result.config.scenario_id,
        "basis_feed_kg_per_hr": result.config.basis_feed_kg_per_hr,
        "time_labels": list(result.time_labels),
        "system_ids": [step.system.ID for step in result.step_results],
        "all_steps_close": result.all_steps_close,
        "all_steps_shadow_ready": result.all_steps_shadow_ready,
        "all_empirical_flowsheets_unchanged": (
            result.all_empirical_flowsheets_unchanged
        ),
        "warning_counts": dict(result.warning_counts),
        "blocker_counts": dict(result.blocker_counts),
        "can_drive_simulation": False,
        "validated_simulation_ready": False,
        "activation_status": result.activation_status,
    }


class DynamicBioSTEAMShadowService:
    """Small non-HTTP service wrapper for future dependency injection."""

    def get_preview(
        self,
        time_label: str = "2026-05",
        basis_feed_kg_per_hr: float = 1000.0,
    ) -> DynamicBioSTEAMAdapterResult:
        return get_dynamic_biosteam_shadow_preview(time_label, basis_feed_kg_per_hr)

    def get_grid(
        self,
        basis_feed_kg_per_hr: float = 1000.0,
    ) -> DynamicBioSTEAMAdapterGridResult:
        return get_dynamic_biosteam_shadow_grid(basis_feed_kg_per_hr)

    def get_shadow_system(
        self,
        time_label: str = "2026-05",
        basis_feed_kg_per_hr: float = 1000.0,
    ) -> dict[str, object]:
        return get_dynamic_biosteam_shadow_system(
            time_label, basis_feed_kg_per_hr
        )

    def get_shadow_system_grid(
        self,
        basis_feed_kg_per_hr: float = 1000.0,
    ) -> dict[str, object]:
        return get_dynamic_biosteam_shadow_system_grid(basis_feed_kg_per_hr)

    def get_calculation_shadow_system(
        self,
        time_label: str = "2026-05",
        basis_feed_kg_per_hr: float = 1000.0,
    ) -> dict[str, object]:
        return get_dynamic_biosteam_calculation_shadow_system(
            time_label, basis_feed_kg_per_hr
        )

    def get_calculation_shadow_grid(
        self,
        basis_feed_kg_per_hr: float = 1000.0,
    ) -> dict[str, object]:
        return get_dynamic_biosteam_calculation_shadow_grid(
            basis_feed_kg_per_hr
        )
