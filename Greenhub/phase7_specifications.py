"""Pure engineering equations for Phase 7 nutrient recovery.

These functions are intentionally independent of BioSTEAM registries. They
provide transparent Level-1 calculations that can be trend-tested before the
results are applied to mutable process streams.
"""

from __future__ import annotations

from dataclasses import dataclass
from math import exp, isfinite, pi, sqrt
from typing import Iterable

from Greenhub.equilibria import ammonia_equilibrium


def bounded_fraction(value: float, name: str) -> float:
    """Validate and return a finite fraction within [0, 1]."""

    result = float(value)
    if not isfinite(result) or not 0.0 <= result <= 1.0:
        raise ValueError(f"{name} must be a finite fraction in [0, 1].")
    return result


def nonnegative(value: float, name: str) -> float:
    """Validate and return a finite non-negative value."""

    result = float(value)
    if not isfinite(result) or result < 0.0:
        raise ValueError(f"{name} must be finite and non-negative.")
    return result


def positive(value: float, name: str) -> float:
    """Validate and return a finite strictly positive value."""

    result = nonnegative(value, name)
    if result <= 0.0:
        raise ValueError(f"{name} must be greater than zero.")
    return result


@dataclass(frozen=True)
class LiquidEntrainmentResult:
    """Liquid entrainment needed to meet a wet-cake moisture target."""

    entrained_liquid_fraction: float
    cake_water_kg_hr: float
    cake_dissolved_nonwater_kg_hr: float
    achieved_moisture_fraction: float
    target_feasible: bool


def solve_liquid_entrainment(
    *,
    captured_particulate_kg_hr: float,
    liquid_water_kg_hr: float,
    dissolved_nonwater_kg_hr: float,
    target_moisture_fraction: float,
) -> LiquidEntrainmentResult:
    """Solve a common entrainment fraction from a target wet-cake moisture.

    Captured particulate matter is fixed first. Water and dissolved material
    then enter the cake together as entrained centrate, rather than receiving
    unrelated arbitrary component splits.
    """

    captured = nonnegative(captured_particulate_kg_hr, "Captured particulate")
    water = nonnegative(liquid_water_kg_hr, "Liquid water")
    dissolved = nonnegative(dissolved_nonwater_kg_hr, "Dissolved non-water mass")
    moisture = bounded_fraction(target_moisture_fraction, "Target cake moisture")
    if moisture >= 1.0:
        raise ValueError("Target cake moisture must be below one.")
    denominator = water * (1.0 - moisture) - moisture * dissolved
    if captured == 0.0 or moisture == 0.0:
        entrainment = 0.0
    elif denominator <= 0.0:
        entrainment = 1.0
    else:
        entrainment = min(1.0, moisture * captured / denominator)
    cake_water = water * entrainment
    cake_dissolved = dissolved * entrainment
    total = captured + cake_water + cake_dissolved
    achieved = cake_water / total if total else 0.0
    return LiquidEntrainmentResult(
        entrainment,
        cake_water,
        cake_dissolved,
        achieved,
        abs(achieved - moisture) <= 1e-8,
    )


@dataclass(frozen=True)
class StruviteExtent:
    """Stoichiometrically limited MgNH4PO4.6H2O reaction extent."""

    product_kmol_hr: float
    magnesium_consumed_kmol_hr: float
    ammonium_consumed_kmol_hr: float
    phosphate_consumed_kmol_hr: float
    crystal_water_consumed_kmol_hr: float
    limiting_reagent: str
    target_recovery_fraction: float


def struvite_extent(
    *,
    magnesium_kmol_hr: float,
    ammonium_kmol_hr: float,
    phosphate_kmol_hr: float,
    target_phosphate_recovery_fraction: float,
) -> StruviteExtent:
    """Return a 1:1:1-limited struvite extent with six waters per mole."""

    available = {
        "magnesium": nonnegative(magnesium_kmol_hr, "Available magnesium"),
        "ammonium": nonnegative(ammonium_kmol_hr, "Available ammonium"),
        "phosphate": nonnegative(phosphate_kmol_hr, "Available phosphate"),
    }
    target = bounded_fraction(
        target_phosphate_recovery_fraction,
        "Target phosphate recovery",
    )
    target_extent = available["phosphate"] * target
    extent = min(target_extent, available["magnesium"], available["ammonium"])
    candidates = {
        "target": target_extent,
        "magnesium": available["magnesium"],
        "ammonium": available["ammonium"],
    }
    limiting = min(candidates, key=candidates.get)
    return StruviteExtent(extent, extent, extent, extent, 6.0 * extent, limiting, target)


@dataclass(frozen=True)
class CalciumPhosphateExtent:
    """Stoichiometric extent for a selected simplified calcium mineral."""

    product_id: str
    product_kmol_hr: float
    calcium_consumed_kmol_hr: float
    phosphate_consumed_kmol_hr: float
    water_consumed_kmol_hr: float
    hydroxide_consumed_kmol_hr: float
    hydroxide_generated_kmol_hr: float
    limiting_reagent: str


def calcium_phosphate_extent(
    *,
    product_id: str,
    calcium_kmol_hr: float,
    phosphate_kmol_hr: float,
    hydroxide_kmol_hr: float,
    target_phosphate_recovery_fraction: float,
) -> CalciumPhosphateExtent:
    """Return a balanced extent for Ca3(PO4)2, CaHPO4, or Ca5(PO4)3OH."""

    calcium = nonnegative(calcium_kmol_hr, "Available calcium")
    phosphate = nonnegative(phosphate_kmol_hr, "Available phosphate")
    hydroxide = nonnegative(hydroxide_kmol_hr, "Available hydroxide")
    target = bounded_fraction(target_phosphate_recovery_fraction, "Target P recovery")
    stoichiometry = {
        "CalciumPhosphate": (3.0, 2.0, 0.0, 0.0, 0.0),
        # Ca + PO4 + H2O -> CaHPO4 + OH
        "DicalciumPhosphate": (1.0, 1.0, 1.0, 0.0, 1.0),
        "Hydroxyapatite": (5.0, 3.0, 0.0, 1.0, 0.0),
    }
    try:
        ca_per, p_per, water_per, oh_per, oh_generated = stoichiometry[product_id]
    except KeyError as error:
        raise ValueError(
            "Calcium-phosphate product must be CalciumPhosphate, "
            "DicalciumPhosphate, or Hydroxyapatite."
        ) from error
    limits = {
        "target": phosphate * target / p_per,
        "calcium": calcium / ca_per,
        "phosphate": phosphate / p_per,
    }
    if oh_per:
        limits["hydroxide"] = hydroxide / oh_per
    limiting = min(limits, key=limits.get)
    extent = limits[limiting]
    return CalciumPhosphateExtent(
        product_id,
        extent,
        extent * ca_per,
        extent * p_per,
        extent * water_per,
        extent * oh_per,
        extent * oh_generated,
        limiting,
    )


@dataclass(frozen=True)
class StrippingCalculation:
    """Level-1 ammonia equilibrium and gas-transfer calculation."""

    free_ammonia_fraction: float
    transfer_units: float
    removal_fraction: float
    pressure_factor: float
    gas_ratio_factor: float


def ammonia_stripping_fraction(
    *,
    pH: float,
    temperature_k: float,
    pressure_pa: float,
    gas_to_liquid_ratio: float,
    packing_height_m: float,
    transfer_coefficient: float,
    reference_gas_to_liquid_ratio: float = 500.0,
    reference_packing_height_m: float = 6.0,
) -> StrippingCalculation:
    """Calculate a monotonic apparent stripping fraction.

    The equilibrium term uses the existing temperature-dependent ammonium pKa.
    The transfer term is an empirical NTU-like expression and is not presented
    as a rate-based packed-column model.
    """

    pressure = positive(pressure_pa, "Stripper pressure")
    gas_ratio = nonnegative(gas_to_liquid_ratio, "Gas-to-liquid ratio")
    height = nonnegative(packing_height_m, "Packing height")
    coefficient = nonnegative(transfer_coefficient, "Transfer coefficient")
    free = ammonia_equilibrium(1.0, pH, temperature_k).unionized_fraction
    pressure_factor = sqrt(101325.0 / pressure)
    gas_factor = sqrt(gas_ratio / positive(reference_gas_to_liquid_ratio, "Reference gas ratio"))
    height_factor = height / positive(reference_packing_height_m, "Reference packing height")
    temperature_factor = (temperature_k / 298.15) ** 1.5
    transfer_units = coefficient * gas_factor * height_factor * pressure_factor * temperature_factor
    removal = 1.0 - exp(-transfer_units * free)
    return StrippingCalculation(
        free,
        transfer_units,
        bounded_fraction(removal, "Calculated ammonia removal"),
        pressure_factor,
        gas_factor,
    )


def packed_column_diameter_m(
    actual_gas_m3_hr: float,
    superficial_velocity_m_s: float,
) -> float:
    """Calculate a circular packed-column diameter from gas velocity."""

    flow = nonnegative(actual_gas_m3_hr, "Actual gas flow") / 3600.0
    velocity = positive(superficial_velocity_m_s, "Superficial gas velocity")
    area = flow / velocity
    return sqrt(4.0 * area / pi) if area else 0.0


def gas_mover_power_kw(
    *,
    actual_gas_m3_hr: float,
    pressure_rise_pa: float,
    efficiency: float,
) -> float:
    """Return isothermal screening shaft power from Q*dP/efficiency."""

    flow_m3_s = nonnegative(actual_gas_m3_hr, "Actual gas flow") / 3600.0
    pressure_rise = nonnegative(pressure_rise_pa, "Pressure rise")
    eta = bounded_fraction(efficiency, "Gas-mover efficiency")
    if eta <= 0.0:
        raise ValueError("Gas-mover efficiency must be above zero.")
    return flow_m3_s * pressure_rise / eta / 1000.0


@dataclass(frozen=True)
class AcidCaptureExtent:
    """Stoichiometric ammonia capture in H2SO4 or HCl."""

    acid_id: str
    product_id: str
    ammonia_captured_kmol_hr: float
    acid_consumed_kmol_hr: float
    product_kmol_hr: float
    residual_ammonia_kmol_hr: float
    residual_acid_kmol_hr: float


def acid_capture_extent(
    *,
    acid_id: str,
    ammonia_kmol_hr: float,
    acid_kmol_hr: float,
    absorber_efficiency: float,
) -> AcidCaptureExtent:
    """Limit ammonium-salt formation by ammonia, acid, and absorber capture."""

    ammonia = nonnegative(ammonia_kmol_hr, "Ammonia feed")
    acid = nonnegative(acid_kmol_hr, "Acid feed")
    efficiency = bounded_fraction(absorber_efficiency, "Absorber efficiency")
    if acid_id == "SulfuricAcid":
        ammonia_per_acid = 2.0
        product_id = "AmmoniumSulfate"
        ammonia_per_product = 2.0
    elif acid_id == "HydrochloricAcid":
        ammonia_per_acid = 1.0
        product_id = "AmmoniumChloride"
        ammonia_per_product = 1.0
    else:
        raise ValueError("Acid absorber supports SulfuricAcid or HydrochloricAcid.")
    captured = min(ammonia * efficiency, acid * ammonia_per_acid)
    consumed_acid = captured / ammonia_per_acid
    product = captured / ammonia_per_product
    return AcidCaptureExtent(
        acid_id,
        product_id,
        captured,
        consumed_acid,
        product,
        ammonia - captured,
        acid - consumed_acid,
    )


@dataclass(frozen=True)
class IonExchangeDesign:
    """Steady-state-average zeolite loading and regeneration design."""

    recovered_ammonium_kg_hr: float
    bed_media_kg: float
    bed_volume_m3: float
    service_time_h: float
    regeneration_frequency_per_day: float
    nacl_kg_hr: float


def ion_exchange_design(
    *,
    ammonium_feed_kg_hr: float,
    recovery_fraction: float,
    capacity_kg_nh4_per_kg_media: float,
    breakthrough_fraction: float,
    service_time_h: float,
    bed_bulk_density_kg_m3: float,
    nacl_molar_ratio: float,
    ammonium_mw: float = 18.03846,
    sodium_chloride_mw: float = 58.44277,
) -> IonExchangeDesign:
    """Size exchange media and NaCl from captured ammonium equivalents."""

    feed = nonnegative(ammonium_feed_kg_hr, "Ammonium feed")
    recovery = bounded_fraction(recovery_fraction, "Ion-exchange recovery")
    capacity = positive(capacity_kg_nh4_per_kg_media, "Exchange capacity")
    breakthrough = bounded_fraction(breakthrough_fraction, "Breakthrough fraction")
    if breakthrough <= 0.0:
        raise ValueError("Breakthrough fraction must be above zero.")
    service = positive(service_time_h, "Service time")
    density = positive(bed_bulk_density_kg_m3, "Bed bulk density")
    ratio = positive(nacl_molar_ratio, "NaCl molar ratio")
    recovered = feed * recovery
    media = recovered * service / (capacity * breakthrough)
    nacl = recovered / ammonium_mw * sodium_chloride_mw * ratio
    return IonExchangeDesign(
        recovered,
        media,
        media / density,
        service,
        24.0 / service,
        nacl,
    )


@dataclass(frozen=True)
class MembraneWaterRecovery:
    """Pressure-responsive membrane water-recovery result."""

    net_driving_pressure_bar: float
    water_recovery_fraction: float
    membrane_area_m2: float


def membrane_water_recovery(
    *,
    feed_water_kg_hr: float,
    applied_pressure_bar: float,
    osmotic_pressure_bar: float,
    reference_net_pressure_bar: float,
    reference_water_recovery_fraction: float,
    water_flux_l_m2_hr: float,
) -> MembraneWaterRecovery:
    """Calculate water recovery and membrane area from net pressure and flux."""

    water = nonnegative(feed_water_kg_hr, "Feed water")
    applied = nonnegative(applied_pressure_bar, "Applied pressure")
    osmotic = nonnegative(osmotic_pressure_bar, "Osmotic pressure")
    reference_pressure = positive(reference_net_pressure_bar, "Reference net pressure")
    reference_recovery = bounded_fraction(
        reference_water_recovery_fraction,
        "Reference water recovery",
    )
    flux = positive(water_flux_l_m2_hr, "Water flux")
    net = max(0.0, applied - osmotic)
    recovery = min(0.95, reference_recovery * sqrt(net / reference_pressure)) if net else 0.0
    permeate_l_hr = water * recovery
    return MembraneWaterRecovery(net, recovery, permeate_l_hr / flux)


@dataclass(frozen=True)
class PeakSizingResult:
    """Peak and turndown statistics for independent monthly steady states."""

    peak_value: float
    design_value: float
    minimum_positive_value: float
    minimum_turndown_fraction: float


def peak_sizing(values: Iterable[float], safety_factor: float = 1.0) -> PeakSizingResult:
    """Return peak-month design value and minimum positive turndown."""

    cleaned = [nonnegative(value, "Monthly sizing value") for value in values]
    if not cleaned:
        raise ValueError("At least one monthly sizing value is required.")
    factor = positive(safety_factor, "Sizing safety factor")
    peak = max(cleaned)
    positive_values = [value for value in cleaned if value > 0.0]
    minimum = min(positive_values) if positive_values else 0.0
    turndown = minimum / peak if peak else 0.0
    return PeakSizingResult(peak, peak * factor, minimum, turndown)
