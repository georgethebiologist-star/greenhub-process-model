"""Pure engineering calculations for GreenHub Phase 5 anaerobic digestion.

These functions deliberately separate steady-state screening calculations from
BioSTEAM stream mutation. They do not implement ADM1, dynamic biology,
electrolyte equilibrium, or gas-film mass transfer.
"""

from __future__ import annotations

from dataclasses import dataclass
from math import ceil, exp, pi

NORMAL_TEMPERATURE_K = 273.15
NORMAL_PRESSURE_PA = 101_325.0
IDEAL_GAS_CONSTANT_PA_M3_PER_KMOL_K = 8_314.462618
NORMAL_M3_PER_KMOL = (
    IDEAL_GAS_CONSTANT_PA_M3_PER_KMOL_K
    * NORMAL_TEMPERATURE_K
    / NORMAL_PRESSURE_PA
)


def nonnegative(value: float, name: str) -> float:
    """Return a finite non-negative value or raise a descriptive error."""

    result = float(value)
    if result < 0.0:
        raise ValueError(f"{name} must be non-negative; received {result}.")
    return result


def positive(value: float, name: str) -> float:
    """Return a finite positive value or raise a descriptive error."""

    result = float(value)
    if result <= 0.0:
        raise ValueError(f"{name} must be positive; received {result}.")
    return result


def bounded_fraction(
    value: float,
    name: str,
    *,
    positive_lower: bool = False,
    open_upper: bool = False,
) -> float:
    """Validate a fraction using explicitly selected endpoint conventions."""

    result = float(value)
    lower_ok = result > 0.0 if positive_lower else result >= 0.0
    upper_ok = result < 1.0 if open_upper else result <= 1.0
    if not lower_ok or not upper_ok:
        left = "(0" if positive_lower else "[0"
        right = "1)" if open_upper else "1]"
        raise ValueError(f"{name} must be within {left}, {right}; received {result}.")
    return result


def validate_pH(value: float, name: str = "pH") -> float:
    """Validate a screening-level aqueous pH value."""

    result = float(value)
    if not 0.0 <= result <= 14.0:
        raise ValueError(f"{name} must be within [0, 14]; received {result}.")
    return result


def first_order_conversion(
    rate_constant_per_day: float,
    residence_time_days: float,
    *,
    maximum_conversion: float = 1.0,
) -> float:
    """Return a bounded first-order conversion for future kinetic modes."""

    rate = nonnegative(rate_constant_per_day, "First-order rate constant")
    time = nonnegative(residence_time_days, "Residence time")
    maximum = bounded_fraction(maximum_conversion, "Maximum conversion")
    return maximum * (1.0 - exp(-rate * time))


def pH_inhibition_factor(
    pH: float,
    *,
    minimum_pH: float,
    optimum_pH_low: float,
    optimum_pH_high: float,
    maximum_pH: float,
) -> float:
    """Return a bounded piecewise-linear screening factor for digester pH."""

    pH = validate_pH(pH, "Digester pH")
    points = tuple(
        validate_pH(value, name)
        for value, name in (
            (minimum_pH, "Minimum digester pH"),
            (optimum_pH_low, "Lower optimum pH"),
            (optimum_pH_high, "Upper optimum pH"),
            (maximum_pH, "Maximum digester pH"),
        )
    )
    if not points[0] < points[1] <= points[2] < points[3]:
        raise ValueError(
            "Digester pH limits must satisfy minimum < optimum low <= "
            "optimum high < maximum."
        )
    if pH <= points[0] or pH >= points[3]:
        return 0.0
    if points[1] <= pH <= points[2]:
        return 1.0
    if pH < points[1]:
        return (pH - points[0]) / (points[1] - points[0])
    return (points[3] - pH) / (points[3] - points[2])


def ammonia_inhibition_factor(
    free_ammonia_n_kg_m3: float,
    *,
    enabled: bool,
    inhibition_constant_kg_n_m3: float | None,
) -> float:
    """Return an empirical non-competitive FAN inhibition factor."""

    concentration = nonnegative(
        free_ammonia_n_kg_m3,
        "Free-ammonia nitrogen concentration",
    )
    if not enabled:
        return 1.0
    if inhibition_constant_kg_n_m3 is None:
        raise ValueError(
            "Enabled ammonia inhibition requires an inhibition constant."
        )
    constant = positive(
        inhibition_constant_kg_n_m3,
        "Ammonia inhibition constant",
    )
    return 1.0 / (1.0 + concentration / constant)


@dataclass(frozen=True)
class DigesterSizingResult:
    """Reconciled CSTR sizing results for one steady-state feed."""

    sizing_mode: str
    liquid_flow_m3_hr: float
    cod_load_kg_day: float
    vs_load_kg_day: float
    volume_by_hrt_m3: float
    volume_by_cod_olr_m3: float
    volume_by_vs_olr_m3: float
    selected_working_volume_m3: float
    total_volume_m3: float
    headspace_volume_m3: float
    number_of_digesters: int
    volume_per_digester_m3: float
    actual_hrt_days: float
    actual_cod_olr_kg_m3_day: float
    actual_vs_olr_kg_m3_day: float
    maximum_sizing_disagreement_fraction: float


def calculate_digester_sizing(
    *,
    liquid_flow_m3_hr: float,
    cod_load_kg_hr: float,
    vs_load_kg_hr: float,
    hrt_days: float,
    target_cod_olr_kg_m3_day: float,
    target_vs_olr_kg_m3_day: float,
    sizing_mode: str,
    working_volume_fraction: float,
    headspace_fraction: float,
    maximum_single_tank_volume_m3: float | None,
) -> DigesterSizingResult:
    """Size a digester using HRT, COD OLR, VS OLR, or their maximum."""

    flow = nonnegative(liquid_flow_m3_hr, "Liquid flow")
    cod = nonnegative(cod_load_kg_hr, "COD load")
    vs = nonnegative(vs_load_kg_hr, "VS load")
    hrt = positive(hrt_days, "Hydraulic retention time")
    cod_olr = positive(target_cod_olr_kg_m3_day, "Target COD OLR")
    vs_olr = positive(target_vs_olr_kg_m3_day, "Target VS OLR")
    working_fraction = bounded_fraction(
        working_volume_fraction,
        "Working-volume fraction",
        positive_lower=True,
    )
    headspace = bounded_fraction(
        headspace_fraction,
        "Headspace fraction",
        open_upper=True,
    )
    volume_hrt = flow * 24.0 * hrt
    volume_cod = cod * 24.0 / cod_olr
    volume_vs = vs * 24.0 / vs_olr
    candidates = {
        "HRT_priority": volume_hrt,
        "COD_OLR_priority": volume_cod,
        "VS_OLR_priority": volume_vs,
        "maximum_required_volume": max(volume_hrt, volume_cod, volume_vs),
        "reconciliation_mode": max(volume_hrt, volume_cod, volume_vs),
    }
    if sizing_mode not in candidates:
        raise ValueError(
            "Digester sizing_mode must be HRT_priority, COD_OLR_priority, "
            "VS_OLR_priority, maximum_required_volume, or reconciliation_mode."
        )
    selected = candidates[sizing_mode]
    if flow > 0.0 and selected <= 0.0:
        raise ValueError("A positive feed requires positive digester working volume.")
    if selected <= 0.0:
        total = headspace_volume = volume_per_tank = 0.0
        count = 0
        actual_hrt = actual_cod = actual_vs = 0.0
    else:
        liquid_capacity = selected / working_fraction
        total = liquid_capacity / (1.0 - headspace)
        headspace_volume = total - liquid_capacity
        if maximum_single_tank_volume_m3 is None:
            count = 1
        else:
            maximum = positive(
                maximum_single_tank_volume_m3,
                "Maximum single-tank volume",
            )
            count = max(1, ceil(total / maximum))
        volume_per_tank = total / count
        actual_hrt = selected / (flow * 24.0) if flow else 0.0
        actual_cod = cod * 24.0 / selected
        actual_vs = vs * 24.0 / selected
    positive_candidates = [value for value in (volume_hrt, volume_cod, volume_vs) if value > 0.0]
    disagreement = (
        (max(positive_candidates) - min(positive_candidates)) / max(positive_candidates)
        if len(positive_candidates) > 1
        else 0.0
    )
    return DigesterSizingResult(
        sizing_mode,
        flow,
        cod * 24.0,
        vs * 24.0,
        volume_hrt,
        volume_cod,
        volume_vs,
        selected,
        total,
        headspace_volume,
        count,
        volume_per_tank,
        actual_hrt,
        actual_cod,
        actual_vs,
        disagreement,
    )


@dataclass(frozen=True)
class DigesterGeometryResult:
    """Screening-level cylindrical geometry for all parallel digesters."""

    diameter_m: float
    liquid_height_m: float
    total_height_m: float
    surface_area_m2: float
    insulation_area_m2: float


def calculate_digester_geometry(
    *,
    sizing: DigesterSizingResult,
    height_to_diameter_ratio: float,
    freeboard_m: float,
) -> DigesterGeometryResult:
    """Return conceptual cylindrical dimensions without structural thickness."""

    ratio = positive(height_to_diameter_ratio, "Height-to-diameter ratio")
    freeboard = nonnegative(freeboard_m, "Freeboard")
    if sizing.number_of_digesters == 0:
        return DigesterGeometryResult(0.0, 0.0, 0.0, 0.0, 0.0)
    diameter = (4.0 * sizing.volume_per_digester_m3 / (pi * ratio)) ** (1.0 / 3.0)
    liquid_height = ratio * diameter
    total_height = liquid_height + freeboard
    side = pi * diameter * total_height
    roof = pi * diameter**2 / 4.0
    per_tank_surface = side + 2.0 * roof
    per_tank_insulation = side + roof
    return DigesterGeometryResult(
        diameter,
        liquid_height,
        total_height,
        per_tank_surface * sizing.number_of_digesters,
        per_tank_insulation * sizing.number_of_digesters,
    )


@dataclass(frozen=True)
class DigesterHeatResult:
    """Sensible-feed and steady heat-loss requirements."""

    feed_sensible_heat_kw: float
    vessel_heat_loss_kw: float
    total_external_heat_kw: float


def calculate_digester_heat(
    *,
    feed_mass_kg_hr: float,
    heat_capacity_kj_kg_k: float,
    feed_temperature_k: float,
    digester_temperature_k: float,
    ambient_temperature_k: float,
    insulation_u_value_w_m2_k: float,
    insulation_area_m2: float,
    feed_heating_efficiency: float,
) -> DigesterHeatResult:
    """Calculate heating without reaction heat or hypothetical heat recovery."""

    mass = nonnegative(feed_mass_kg_hr, "Digester feed mass")
    cp = positive(heat_capacity_kj_kg_k, "Feed heat capacity")
    efficiency = bounded_fraction(
        feed_heating_efficiency,
        "Feed heating efficiency",
        positive_lower=True,
    )
    u_value = nonnegative(insulation_u_value_w_m2_k, "Insulation U-value")
    area = nonnegative(insulation_area_m2, "Insulation area")
    sensible = max(
        0.0,
        mass * cp * (float(digester_temperature_k) - float(feed_temperature_k)) / 3600.0,
    )
    loss = max(
        0.0,
        u_value
        * area
        * (float(digester_temperature_k) - float(ambient_temperature_k))
        / 1000.0,
    )
    return DigesterHeatResult(sensible, loss, sensible / efficiency + loss)


def calculate_mixing_power(
    *,
    working_volume_m3: float,
    specific_mixing_power_kw_m3: float,
    mixing_schedule_fraction: float,
    motor_efficiency: float,
) -> tuple[float, float]:
    """Return shaft and average electrical mixing power in kW."""

    volume = nonnegative(working_volume_m3, "Working volume")
    specific = nonnegative(specific_mixing_power_kw_m3, "Specific mixing power")
    schedule = bounded_fraction(mixing_schedule_fraction, "Mixing schedule")
    efficiency = bounded_fraction(
        motor_efficiency,
        "Mixing motor efficiency",
        positive_lower=True,
    )
    shaft = volume * specific
    return shaft, shaft * schedule / efficiency


def normal_volume_m3(kmol: float) -> float:
    """Convert kmol to Nm3 at the centrally defined normal condition."""

    return nonnegative(kmol, "Gas amount") * NORMAL_M3_PER_KMOL
