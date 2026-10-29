"""Compatibility entry point for the post-route screening TEA layer."""

from __future__ import annotations

from Greenhub.application.tea_service import (
    TEAProjectBasis,
    TEAReport,
    calculate_dynamic_tea,
    calculate_empirical_tea,
)
from Greenhub.tea_costs import TEACostRecord, load_tea_cost_register
from Greenhub.tea_finance import TEAFinancialAssumptions, TEAProductPrice


def not_implemented_message() -> str:
    """Return the remaining investment-grade TEA scope statement."""

    return "Screening post-route TEA is available; investment-grade TEA is not implemented."


__all__ = (
    "TEACostRecord",
    "TEAFinancialAssumptions",
    "TEAProductPrice",
    "TEAProjectBasis",
    "TEAReport",
    "calculate_dynamic_tea",
    "calculate_empirical_tea",
    "load_tea_cost_register",
    "not_implemented_message",
)
