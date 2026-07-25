"""Analytical Phase 3 moisture and yield specifications."""

from __future__ import annotations

from dataclasses import dataclass


PRIORITY_MODES = {
    "cake_moisture_priority",
    "juice_yield_priority",
    "reconciliation_mode",
}


@dataclass(frozen=True)
class WaterPartitionResult:
    """Resolved two-outlet water allocation and achieved specifications."""

    water_to_liquid_kg_hr: float
    water_to_solids_kg_hr: float
    solids_moisture_fraction: float
    liquid_yield_fraction: float
    warning: str | None


def _fraction(value: float | None, name: str, *, upper_open: bool = False) -> float | None:
    if value is None:
        return None
    number = float(value)
    valid = 0.0 <= number < 1.0 if upper_open else 0.0 <= number <= 1.0
    if not valid:
        bound = "[0, 1)" if upper_open else "[0, 1]"
        raise ValueError(f"{name} must be within {bound}; received {number}.")
    return number


def solve_two_outlet_water_partition(
    *,
    available_water_kg_hr: float,
    solids_nonwater_kg_hr: float,
    liquid_nonwater_kg_hr: float,
    wet_feed_kg_hr: float,
    target_solids_moisture_fraction: float | None,
    target_liquid_yield_fraction: float | None = None,
    priority_mode: str = "cake_moisture_priority",
    fallback_water_recovery_to_liquid: float = 0.90,
    consistency_tolerance: float = 0.02,
) -> WaterPartitionResult:
    """Resolve water analytically while preserving all non-water recoveries.

    ``priority_mode`` selects which measured constraint controls when cake/sludge
    moisture and total liquid yield imply different water allocations. The
    reconciliation mode uses the midpoint of the two feasible allocations and
    reports both specifications as reconciled rather than measured exactly.
    """

    water = float(available_water_kg_hr)
    solids_nonwater = float(solids_nonwater_kg_hr)
    liquid_nonwater = float(liquid_nonwater_kg_hr)
    wet_feed = float(wet_feed_kg_hr)
    if min(water, solids_nonwater, liquid_nonwater) < -1e-12 or wet_feed <= 0.0:
        raise ValueError("Water allocation requires non-negative masses and a positive wet feed.")
    if priority_mode not in PRIORITY_MODES:
        raise ValueError(
            f"Unknown specification priority '{priority_mode}'. Expected one of {sorted(PRIORITY_MODES)}."
        )

    moisture = _fraction(
        target_solids_moisture_fraction,
        "Target solids moisture",
        upper_open=True,
    )
    liquid_yield = _fraction(target_liquid_yield_fraction, "Target liquid yield")
    fallback = _fraction(fallback_water_recovery_to_liquid, "Fallback water recovery")

    water_to_liquid_from_moisture = None
    if moisture is not None:
        required_solids_water = (
            solids_nonwater * moisture / (1.0 - moisture)
            if solids_nonwater > 0.0
            else 0.0
        )
        if required_solids_water > water + 1e-9:
            raise ValueError(
                "Target solids moisture is physically impossible: it requires "
                f"{required_solids_water:.6g} kg/hr water but only {water:.6g} kg/hr is available."
            )
        water_to_liquid_from_moisture = water - required_solids_water

    water_to_liquid_from_yield = None
    if liquid_yield is not None:
        required_liquid_total = liquid_yield * wet_feed
        water_to_liquid_from_yield = required_liquid_total - liquid_nonwater
        if water_to_liquid_from_yield < -1e-9 or water_to_liquid_from_yield > water + 1e-9:
            raise ValueError(
                "Target liquid yield is physically impossible for the fixed non-water partition: "
                f"required liquid water={water_to_liquid_from_yield:.6g} kg/hr, "
                f"available={water:.6g} kg/hr."
            )
        water_to_liquid_from_yield = min(max(water_to_liquid_from_yield, 0.0), water)

    warning = None
    if water_to_liquid_from_moisture is not None and water_to_liquid_from_yield is not None:
        implied_yield = (liquid_nonwater + water_to_liquid_from_moisture) / wet_feed
        gap = abs(implied_yield - liquid_yield)
        if gap > consistency_tolerance:
            warning = (
                "Target solids moisture and liquid yield are inconsistent by "
                f"{gap:.2%}; '{priority_mode}' determined the water split."
            )
        if priority_mode == "cake_moisture_priority":
            water_to_liquid = water_to_liquid_from_moisture
        elif priority_mode == "juice_yield_priority":
            water_to_liquid = water_to_liquid_from_yield
        else:
            water_to_liquid = 0.5 * (
                water_to_liquid_from_moisture + water_to_liquid_from_yield
            )
    elif water_to_liquid_from_moisture is not None:
        water_to_liquid = water_to_liquid_from_moisture
    elif water_to_liquid_from_yield is not None:
        water_to_liquid = water_to_liquid_from_yield
    else:
        water_to_liquid = water * float(fallback)

    water_to_liquid = min(max(float(water_to_liquid), 0.0), water)
    water_to_solids = water - water_to_liquid
    solids_total = solids_nonwater + water_to_solids
    liquid_total = liquid_nonwater + water_to_liquid
    achieved_moisture = water_to_solids / solids_total if solids_total > 0.0 else 0.0
    achieved_yield = liquid_total / wet_feed
    return WaterPartitionResult(
        water_to_liquid,
        water_to_solids,
        achieved_moisture,
        achieved_yield,
        warning,
    )

