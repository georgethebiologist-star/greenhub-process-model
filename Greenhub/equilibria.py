"""Transparent acid-base speciation utilities for Phase 2 diagnostics."""

from __future__ import annotations

from dataclasses import dataclass

from Greenhub.conversions import N_TO_NH3, N_TO_NH4


def _validate_ph_temperature(pH: float, temperature_K: float) -> tuple[float, float]:
    pH = float(pH)
    temperature_K = float(temperature_K)
    if not 0.0 <= pH <= 14.0:
        raise ValueError(f"pH must be within [0, 14]; received {pH}.")
    if not 273.15 <= temperature_K <= 373.15:
        raise ValueError("Phase 2 aqueous speciation functions support 273.15-373.15 K.")
    return pH, temperature_K


@dataclass(frozen=True)
class AmmoniaSpeciation:
    """TAN distribution on both N-equivalent and compound-mass bases."""

    total_ammonia_n: float
    ammonium_n: float
    ammonia_n: float
    ammonium_mass: float
    ammonia_mass: float
    unionized_fraction: float
    pKa: float


def ammonia_equilibrium(total_ammonia_n: float, pH: float, temperature_K: float) -> AmmoniaSpeciation:
    """Calculate NH4+/NH3 using pKa = 0.09018 + 2729.92/T.

    The input and the two ``*_n`` outputs use the same N-equivalent unit. The
    engineering relation is commonly attributed to Emerson et al. (1975).
    """

    pH, temperature_K = _validate_ph_temperature(pH, temperature_K)
    total_ammonia_n = float(total_ammonia_n)
    if total_ammonia_n < 0.0:
        raise ValueError("Total ammonia nitrogen cannot be negative.")
    pKa = 0.09018 + 2729.92 / temperature_K
    unionized_fraction = 1.0 / (1.0 + 10.0 ** (pKa - pH))
    ammonia_n = total_ammonia_n * unionized_fraction
    ammonium_n = total_ammonia_n - ammonia_n
    return AmmoniaSpeciation(
        total_ammonia_n=total_ammonia_n,
        ammonium_n=ammonium_n,
        ammonia_n=ammonia_n,
        ammonium_mass=ammonium_n * N_TO_NH4,
        ammonia_mass=ammonia_n * N_TO_NH3,
        unionized_fraction=unionized_fraction,
        pKa=pKa,
    )


def _triprotic_fractions(pH: float, pKa1: float, pKa2: float, pKa3: float) -> tuple[float, float, float, float]:
    h = 10.0 ** (-pH)
    ka1, ka2, ka3 = 10.0 ** (-pKa1), 10.0 ** (-pKa2), 10.0 ** (-pKa3)
    denominator = h**3 + ka1 * h**2 + ka1 * ka2 * h + ka1 * ka2 * ka3
    return (
        h**3 / denominator,
        ka1 * h**2 / denominator,
        ka1 * ka2 * h / denominator,
        ka1 * ka2 * ka3 / denominator,
    )


def phosphate_speciation(pH: float, temperature_K: float = 298.15) -> dict[str, float]:
    """Return phosphate fractions using 25 C dilute-solution pKa values."""

    pH, _ = _validate_ph_temperature(pH, temperature_K)
    fractions = _triprotic_fractions(pH, 2.148, 7.198, 12.375)
    return dict(zip(("H3PO4", "H2PO4-", "HPO4-2", "PO4-3"), fractions, strict=True))


def inorganic_carbon_speciation(pH: float, temperature_K: float = 298.15) -> dict[str, float]:
    """Return CO2/HCO3-/CO3-2 fractions using 25 C apparent pKa values."""

    pH, _ = _validate_ph_temperature(pH, temperature_K)
    h = 10.0 ** (-pH)
    ka1, ka2 = 10.0 ** (-6.35), 10.0 ** (-10.33)
    denominator = h * h + ka1 * h + ka1 * ka2
    return {
        "CO2_aq_plus_H2CO3": h * h / denominator,
        "HCO3-": ka1 * h / denominator,
        "CO3-2": ka1 * ka2 / denominator,
    }


def sulfide_speciation(pH: float, temperature_K: float = 298.15) -> dict[str, float]:
    """Return H2S/HS-/S-2 fractions using screening-level pKa values."""

    pH, _ = _validate_ph_temperature(pH, temperature_K)
    h = 10.0 ** (-pH)
    ka1, ka2 = 10.0 ** (-7.0), 10.0 ** (-14.0)
    denominator = h * h + ka1 * h + ka1 * ka2
    return {
        "H2S": h * h / denominator,
        "HS-": ka1 * h / denominator,
        "S-2": ka1 * ka2 / denominator,
    }
