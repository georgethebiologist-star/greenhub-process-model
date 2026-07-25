"""Transparent Phase 4 acidification, recovery, cake, and dryer calculations."""

from __future__ import annotations

from dataclasses import dataclass
from math import exp, isfinite
from typing import Iterable, Mapping

from Greenhub.chemicals import chemicals

ACID_PROTON_EQUIVALENTS = {
    "HydrochloricAcid": 1.0,
    "SulfuricAcid": 2.0,
    "LacticAcid": 1.0,
}

NEUTRALIZATION_STOICHIOMETRY = {
    ("HydrochloricAcid", "SodiumHydroxide"): (1.0, 1.0, "SodiumChloride"),
    ("HydrochloricAcid", "CalciumHydroxide"): (2.0, 1.0, "CalciumChloride"),
    ("SulfuricAcid", "SodiumHydroxide"): (1.0, 2.0, "SodiumSulfate"),
    ("SulfuricAcid", "CalciumHydroxide"): (1.0, 1.0, "CalciumSulfate"),
}


def bounded_fraction(
    value: float,
    name: str,
    *,
    upper_open: bool = False,
    positive: bool = False,
) -> float:
    """Return a validated finite fraction."""

    number = float(value)
    lower_valid = number > 0.0 if positive else number >= 0.0
    upper_valid = number < 1.0 if upper_open else number <= 1.0
    if not isfinite(number) or not lower_valid or not upper_valid:
        left = "(0" if positive else "[0"
        right = "1)" if upper_open else "1]"
        raise ValueError(f"{name} must be within {left}, {right}; received {value!r}.")
    return number


def nonnegative(value: float, name: str) -> float:
    """Return a validated finite non-negative number."""

    number = float(value)
    if not isfinite(number) or number < 0.0:
        raise ValueError(f"{name} must be finite and non-negative; received {value!r}.")
    return number


def validate_pH(value: float, name: str = "pH") -> float:
    """Validate the screening-level aqueous pH range."""

    number = float(value)
    if not isfinite(number) or not 0.0 <= number <= 14.0:
        raise ValueError(f"{name} must be within [0, 14]; received {value!r}.")
    return number


@dataclass(frozen=True)
class AcidDemandResult:
    """Acid dose and commercial-solution flow on a pure-acid basis."""

    method: str
    acid_type: str
    initial_pH: float
    target_pH: float
    pure_acid_kg_hr: float
    acid_solution_kg_hr: float
    reagent_water_kg_hr: float
    acid_equivalents_kmol_hr: float
    pure_acid_dose_kg_m3: float
    warning: str | None = None


def interpolate_titration_dose(
    target_pH: float,
    points: Iterable[tuple[float, float]],
) -> float:
    """Linearly interpolate pure-acid dose from monotonic dose/pH points.

    Each point is ``(pure_acid_dose_kg_m3, resulting_pH)``. Extrapolation is
    intentionally rejected because a titration curve is only valid over its
    measured range.
    """

    target = validate_pH(target_pH, "Target pH")
    ordered = sorted((nonnegative(dose, "Titration dose"), validate_pH(pH)) for dose, pH in points)
    if len(ordered) < 2:
        raise ValueError("Titration interpolation requires at least two active points.")
    doses = [item[0] for item in ordered]
    p_values = [item[1] for item in ordered]
    if any(second <= first for first, second in zip(doses, doses[1:])):
        raise ValueError("Titration acid doses must increase strictly.")
    if any(second > first for first, second in zip(p_values, p_values[1:])):
        raise ValueError("Titration pH must be non-increasing as acid dose increases.")
    if target > p_values[0] or target < p_values[-1]:
        raise ValueError(
            f"Target pH {target:g} is outside the titration range "
            f"[{p_values[-1]:g}, {p_values[0]:g}]."
        )
    for (dose_a, pH_a), (dose_b, pH_b) in zip(ordered, ordered[1:]):
        if pH_a >= target >= pH_b:
            if abs(pH_a - pH_b) <= 1e-12:
                return dose_a
            fraction = (pH_a - target) / (pH_a - pH_b)
            return dose_a + fraction * (dose_b - dose_a)
    return ordered[-1][0]


def calculate_acid_demand(
    *,
    method: str,
    acid_type: str,
    liquid_flow_m3_hr: float,
    initial_pH: float,
    target_pH: float,
    acid_solution_mass_fraction: float,
    acid_purity: float,
    empirical_dose_kg_per_m3: float | None = None,
    alkalinity_mg_caco3_L: float | None = None,
    buffer_capacity_mol_H_per_L_pH: float | None = None,
    titration_points: Iterable[tuple[float, float]] = (),
) -> AcidDemandResult:
    """Calculate acid solution flow without claiming electrolyte equilibrium."""

    method = str(method).strip().casefold()
    if acid_type not in ACID_PROTON_EQUIVALENTS:
        raise ValueError(f"Unsupported Phase 4 acid type '{acid_type}'.")
    volume = nonnegative(liquid_flow_m3_hr, "Liquid flow")
    initial = validate_pH(initial_pH, "Initial pH")
    target = validate_pH(target_pH, "Target pH")
    if target > initial + 1e-12:
        raise ValueError(
            f"Acidification target pH {target:g} exceeds inlet pH {initial:g}; use a base-conditioning method."
        )
    solution_fraction = bounded_fraction(
        acid_solution_mass_fraction,
        "Acid solution mass fraction",
        upper_open=False,
        positive=True,
    )
    purity = bounded_fraction(acid_purity, "Acid purity", positive=True)
    active_fraction = solution_fraction * purity
    warning = None

    if volume == 0.0 or abs(target - initial) <= 1e-12:
        pure_acid = 0.0
        dose = 0.0
    elif method == "empirical_dose":
        if empirical_dose_kg_per_m3 is None:
            raise ValueError("Empirical acid-demand mode requires acid_dose_kg_per_m3.")
        dose = nonnegative(empirical_dose_kg_per_m3, "Empirical acid dose")
        pure_acid = dose * volume
    elif method == "acid_equivalent":
        if alkalinity_mg_caco3_L is None:
            raise ValueError("Acid-equivalent mode requires feed alkalinity in mg CaCO3/L.")
        alkalinity = nonnegative(alkalinity_mg_caco3_L, "Feed alkalinity")
        buffer_capacity = nonnegative(
            buffer_capacity_mol_H_per_L_pH or 0.0,
            "Buffer capacity",
        )
        alkalinity_equivalents = alkalinity / 50_000.0 * volume
        free_h_equivalents = max(0.0, 10.0 ** (-target) - 10.0 ** (-initial)) * volume
        buffer_equivalents = buffer_capacity * (initial - target) * volume
        acid_equivalents = alkalinity_equivalents + free_h_equivalents + buffer_equivalents
        acid_kmol = acid_equivalents / ACID_PROTON_EQUIVALENTS[acid_type]
        pure_acid = acid_kmol * chemicals[acid_type].MW
        dose = pure_acid / volume
        warning = "Simplified acid-equivalent balance; electrolyte activities are not resolved."
    elif method == "titration_curve":
        dose = interpolate_titration_dose(target, titration_points)
        pure_acid = dose * volume
    else:
        raise ValueError(
            "acid_demand_method must be 'empirical_dose', 'acid_equivalent', or 'titration_curve'."
        )

    solution = pure_acid / active_fraction if pure_acid else 0.0
    water = solution - pure_acid
    acid_kmol = pure_acid / chemicals[acid_type].MW if pure_acid else 0.0
    equivalents = acid_kmol * ACID_PROTON_EQUIVALENTS[acid_type]
    return AcidDemandResult(
        method,
        acid_type,
        initial,
        target,
        pure_acid,
        solution,
        water,
        equivalents,
        dose,
        warning,
    )


def pH_response_recovery(
    *,
    pH: float,
    isoelectric_pH: float,
    width: float,
    maximum_recovery: float,
) -> float:
    """Return a bounded Gaussian aggregate-pI response."""

    pH = validate_pH(pH)
    pI = validate_pH(isoelectric_pH, "Effective protein pI")
    width = float(width)
    if not isfinite(width) or width <= 0.0:
        raise ValueError("The aggregate-pI width parameter must be positive.")
    maximum = bounded_fraction(maximum_recovery, "Maximum precipitation recovery")
    return maximum * exp(-0.5 * ((pH - pI) / width) ** 2)


def temperature_adjusted_rate_constant(
    *,
    reference_rate_per_min: float,
    activation_energy_kj_per_mol: float,
    temperature_K: float,
    reference_temperature_K: float,
) -> float:
    """Return an Arrhenius-adjusted first-order rate with guarded exponent."""

    rate = nonnegative(reference_rate_per_min, "Reference rate constant")
    activation = nonnegative(activation_energy_kj_per_mol, "Activation energy")
    temperature = float(temperature_K)
    reference_temperature = float(reference_temperature_K)
    if temperature <= 0.0 or reference_temperature <= 0.0:
        raise ValueError("Kinetic temperatures must be above absolute zero.")
    exponent = -(activation * 1000.0 / 8.314462618) * (
        1.0 / temperature - 1.0 / reference_temperature
    )
    return rate * exp(min(700.0, max(-700.0, exponent)))


def first_order_recovery(
    *,
    maximum_recovery: float,
    rate_constant_per_min: float,
    residence_time_min: float,
) -> float:
    """Return Xmax * (1 - exp(-k*t))."""

    maximum = bounded_fraction(maximum_recovery, "Maximum recovery")
    rate = nonnegative(rate_constant_per_min, "Rate constant")
    residence = nonnegative(residence_time_min, "Residence time")
    return maximum * (1.0 - exp(-rate * residence))


def resolve_recovery(
    *,
    mode: str,
    direct_recovery: float | None,
    maximum_recovery: float,
    pH: float,
    isoelectric_pH: float,
    pH_width: float,
    residence_time_min: float,
    rate_constant_per_min: float | None = None,
    activation_energy_kj_per_mol: float | None = None,
    temperature_K: float = 298.15,
    reference_temperature_K: float = 298.15,
) -> float:
    """Resolve direct, pH-response, or first-order protein recovery."""

    key = str(mode).strip().casefold()
    if key == "direct_yield":
        if direct_recovery is None:
            raise ValueError("Direct-yield mode requires precipitation_efficiency.")
        return bounded_fraction(direct_recovery, "Direct precipitation efficiency")
    pH_limit = pH_response_recovery(
        pH=pH,
        isoelectric_pH=isoelectric_pH,
        width=pH_width,
        maximum_recovery=maximum_recovery,
    )
    if key == "ph_response":
        return pH_limit
    if key == "first_order":
        if rate_constant_per_min is None:
            raise ValueError("First-order mode requires rate_constant_per_min.")
        rate = nonnegative(rate_constant_per_min, "Rate constant")
        if activation_energy_kj_per_mol is not None:
            rate = temperature_adjusted_rate_constant(
                reference_rate_per_min=rate,
                activation_energy_kj_per_mol=activation_energy_kj_per_mol,
                temperature_K=temperature_K,
                reference_temperature_K=reference_temperature_K,
            )
        kinetic = first_order_recovery(
            maximum_recovery=pH_limit,
            rate_constant_per_min=rate,
            residence_time_min=residence_time_min,
        )
        return min(pH_limit, kinetic)
    raise ValueError("kinetic_model must be 'direct_yield', 'ph_response', or 'first_order'.")


@dataclass(frozen=True)
class LiquidEntrainmentResult:
    """Analytical liquid entrainment required for a target cake moisture."""

    liquid_entrainment_fraction: float
    cake_water_kg_hr: float
    cake_dissolved_solids_kg_hr: float
    achieved_cake_moisture_fraction: float


def solve_liquid_entrainment_for_cake_moisture(
    *,
    fixed_cake_dry_solids_kg_hr: float,
    dissolved_solids_available_kg_hr: float,
    water_available_kg_hr: float,
    target_cake_moisture_fraction: float,
) -> LiquidEntrainmentResult:
    """Solve one entrained-liquid fraction without changing captured solids."""

    fixed = nonnegative(fixed_cake_dry_solids_kg_hr, "Fixed cake dry solids")
    dissolved = nonnegative(dissolved_solids_available_kg_hr, "Available dissolved solids")
    water = nonnegative(water_available_kg_hr, "Available water")
    moisture = bounded_fraction(
        target_cake_moisture_fraction,
        "Target cake moisture",
        upper_open=True,
    )
    if fixed == 0.0:
        if moisture == 0.0:
            return LiquidEntrainmentResult(0.0, 0.0, 0.0, 0.0)
        raise ValueError("A wet cake cannot be formed when no fixed dry solids are captured.")
    if moisture == 0.0:
        return LiquidEntrainmentResult(0.0, 0.0, 0.0, 0.0)
    denominator = (1.0 - moisture) * water - moisture * dissolved
    if denominator <= 0.0:
        raise ValueError(
            "Target cake moisture is impossible because the available liquid is too concentrated."
        )
    fraction = moisture * fixed / denominator
    if fraction > 1.0 + 1e-12:
        raise ValueError(
            "Target cake moisture requires more liquid than is available in the separator feed."
        )
    fraction = min(max(fraction, 0.0), 1.0)
    cake_water = water * fraction
    cake_dissolved = dissolved * fraction
    cake_total = fixed + cake_dissolved + cake_water
    achieved = cake_water / cake_total if cake_total else 0.0
    return LiquidEntrainmentResult(fraction, cake_water, cake_dissolved, achieved)


@dataclass(frozen=True)
class DryerMassResult:
    """Dryer water-removal result before optional dry-matter losses."""

    inlet_dry_matter_kg_hr: float
    inlet_water_kg_hr: float
    product_water_kg_hr: float
    evaporated_water_kg_hr: float
    target_product_mass_kg_hr: float
    inlet_moisture_fraction: float
    product_moisture_fraction: float


def solve_dryer_mass_balance(
    *,
    inlet_dry_matter_kg_hr: float,
    inlet_water_kg_hr: float,
    target_product_moisture_fraction: float,
) -> DryerMassResult:
    """Calculate target product water and evaporation with exact closure."""

    dry = nonnegative(inlet_dry_matter_kg_hr, "Dryer inlet dry matter")
    water = nonnegative(inlet_water_kg_hr, "Dryer inlet water")
    target = bounded_fraction(
        target_product_moisture_fraction,
        "Target product moisture",
        upper_open=True,
    )
    total = dry + water
    inlet_moisture = water / total if total else 0.0
    if total == 0.0:
        return DryerMassResult(0.0, 0.0, 0.0, 0.0, 0.0, 0.0, target)
    if dry == 0.0:
        raise ValueError("A dry-protein product cannot be specified for a water-only dryer feed.")
    if target > inlet_moisture + 1e-12:
        raise ValueError(
            f"Target product moisture {target:.3%} exceeds inlet cake moisture {inlet_moisture:.3%}."
        )
    product_water = dry * target / (1.0 - target)
    product_water = min(product_water, water)
    evaporated = water - product_water
    product_mass = dry + product_water
    achieved = product_water / product_mass if product_mass else 0.0
    return DryerMassResult(dry, water, product_water, evaporated, product_mass, inlet_moisture, achieved)


@dataclass(frozen=True)
class DryerEnergyResult:
    """Screening-level selected-method dryer energy balance."""

    calculation_method: str
    sensible_water_kj_hr: float
    sensible_dry_solids_kj_hr: float
    latent_heat_kj_hr: float
    useful_heat_kj_hr: float
    external_heat_kj_hr: float
    external_heat_kw: float


def calculate_dryer_energy(
    *,
    calculation_method: str,
    inlet_water_kg_hr: float,
    dry_solids_kg_hr: float,
    evaporated_water_kg_hr: float,
    inlet_temperature_K: float,
    product_temperature_K: float,
    thermal_efficiency: float,
    latent_heat_kj_per_kg: float = 2257.0,
    water_heat_capacity_kj_per_kg_K: float = 4.18,
    solids_heat_capacity_kj_per_kg_K: float = 1.8,
    specific_heat_demand_kj_per_kg_water: float | None = None,
) -> DryerEnergyResult:
    """Calculate one, and only one, selected dryer heat-demand method."""

    method = str(calculation_method).strip().casefold()
    inlet_water = nonnegative(inlet_water_kg_hr, "Dryer inlet water")
    dry_solids = nonnegative(dry_solids_kg_hr, "Dryer dry solids")
    evaporated = nonnegative(evaporated_water_kg_hr, "Evaporated water")
    if evaporated > inlet_water + 1e-9:
        raise ValueError("Evaporated water cannot exceed dryer inlet water.")
    efficiency = bounded_fraction(thermal_efficiency, "Dryer thermal efficiency", positive=True)
    delta_T = max(0.0, float(product_temperature_K) - float(inlet_temperature_K))
    if method == "thermodynamic":
        sensible_water = inlet_water * nonnegative(
            water_heat_capacity_kj_per_kg_K,
            "Water heat capacity",
        ) * delta_T
        sensible_solids = dry_solids * nonnegative(
            solids_heat_capacity_kj_per_kg_K,
            "Solids heat capacity",
        ) * delta_T
        latent = evaporated * nonnegative(latent_heat_kj_per_kg, "Latent heat")
        useful = sensible_water + sensible_solids + latent
    elif method == "specific_heat_demand":
        if specific_heat_demand_kj_per_kg_water is None:
            raise ValueError(
                "specific_heat_demand mode requires specific_heat_demand_kj_per_kg_water."
            )
        sensible_water = 0.0
        sensible_solids = 0.0
        latent = 0.0
        useful = evaporated * nonnegative(
            specific_heat_demand_kj_per_kg_water,
            "Specific dryer heat demand",
        )
    else:
        raise ValueError(
            "dryer_energy_method must be 'thermodynamic' or 'specific_heat_demand'."
        )
    external = useful / efficiency if useful else 0.0
    return DryerEnergyResult(
        method,
        sensible_water,
        sensible_solids,
        latent,
        useful,
        external,
        external / 3600.0,
    )


@dataclass(frozen=True)
class BaseDemandResult:
    """Pure-base and commercial-solution requirement for one acid/base pair."""

    acid_type: str
    base_type: str
    salt_type: str
    acid_kg_hr: float
    pure_base_kg_hr: float
    base_solution_kg_hr: float
    reagent_water_kg_hr: float


def calculate_stoichiometric_base_demand(
    *,
    acid_type: str,
    base_type: str,
    acid_kg_hr: float,
    base_solution_mass_fraction: float,
    base_purity: float,
) -> BaseDemandResult:
    """Calculate ideal base demand for the selected molecular salt reaction."""

    try:
        acid_coefficient, base_coefficient, salt = NEUTRALIZATION_STOICHIOMETRY[
            (acid_type, base_type)
        ]
    except KeyError as error:
        raise ValueError(
            f"Unsupported neutralization pair '{acid_type}' + '{base_type}'."
        ) from error
    acid_mass = nonnegative(acid_kg_hr, "Neutralized acid")
    solution_fraction = bounded_fraction(
        base_solution_mass_fraction,
        "Base solution mass fraction",
        positive=True,
    )
    purity = bounded_fraction(base_purity, "Base purity", positive=True)
    acid_kmol = acid_mass / chemicals[acid_type].MW if acid_mass else 0.0
    base_kmol = acid_kmol * base_coefficient / acid_coefficient
    pure_base = base_kmol * chemicals[base_type].MW
    solution = pure_base / (solution_fraction * purity) if pure_base else 0.0
    return BaseDemandResult(
        acid_type,
        base_type,
        salt,
        acid_mass,
        pure_base,
        solution,
        solution - pure_base,
    )


def validate_component_fraction_mapping(
    values: Mapping[str, float],
    *,
    label: str,
    known_components: Iterable[str],
) -> None:
    """Validate an auditable component-specific fraction mapping."""

    known = set(known_components)
    unknown = set(values) - known
    if unknown:
        raise KeyError(f"{label} contains unknown components: {sorted(unknown)}")
    for component_id, value in values.items():
        bounded_fraction(value, f"{label} fraction for {component_id}")
