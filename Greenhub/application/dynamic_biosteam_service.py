"""Opt-in application surface for the isolated dynamic BioSTEAM adapter."""

from __future__ import annotations

from Greenhub.dynamic_biosteam_adapter import (
    DynamicBioSTEAMAdapterConfig,
    DynamicBioSTEAMAdapterGridResult,
    DynamicBioSTEAMAdapterResult,
    build_dynamic_biosteam_shadow_flowsheet,
    build_dynamic_biosteam_shadow_grid,
)


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
