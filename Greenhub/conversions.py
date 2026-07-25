"""Dimension-aware unit conversions for GreenHub feed characterization."""

from __future__ import annotations

from math import isfinite

P_TO_P2O5 = 2.291
K_TO_K2O = 1.205
N_TO_NH4 = 18.03846 / 14.0067
N_TO_NH3 = 17.03052 / 14.0067
P_TO_PO4 = 94.971361 / 30.973762
N_TO_NO3 = 62.0049 / 14.0067
P_TO_STRUVITE = 245.406 / 30.973762
N_TO_STRUVITE = 245.406 / 14.0067


def normalize_unit(unit: str) -> str:
    """Normalize common Unicode and spelling variants without changing basis."""

    if not isinstance(unit, str) or not unit.strip():
        raise ValueError("A non-empty unit is required.")
    normalized = unit.strip().lower()
    replacements = {
        "³": "3",
        "₂": "2",
        "₃": "3",
        "₄": "4",
        "⁺": "+",
        "⁻": "-",
        "·": ".",
        " ": "",
        "per": "/",
        "hour": "h",
        "hr": "h",
        "year": "y",
        "day": "d",
        "litre": "l",
        "liter": "l",
    }
    for old, new in replacements.items():
        normalized = normalized.replace(old, new)
    aliases = {
        "kg/h": "kg/h",
        "kgph": "kg/h",
        "t/d": "t/d",
        "tonne/d": "t/d",
        "t/y": "t/y",
        "kg/y": "kg/y",
        "m3/h": "m3/h",
        "m3/d": "m3/d",
        "l/h": "l/h",
        "mg/l": "mg/l",
        "g/l": "g/l",
        "kg/m3": "kg/m3",
        "mg/kgwet": "mg/kgwet",
        "g/kgwet": "g/kgwet",
        "g/kgts": "g/kgts",
        "%wetmass": "%wetmass",
        "%wet": "%wetmass",
        "%ts": "%ts",
        "wt.%": "wt.%",
        "wt%": "wt.%",
        "massfraction": "mass_fraction",
        "kg/kgtotal": "mass_fraction",
        "mol/l": "mol/l",
        "mmol/l": "mmol/l",
        "mgcaCO3/l".lower(): "mgcaco3/l",
        "mgcaco3/l": "mgcaco3/l",
        "mgN/l".lower(): "mgn/l",
        "mgp/l": "mgp/l",
        "mgk/l": "mgk/l",
        "degc": "degc",
        "°c": "degc",
        "k": "k",
        "-": "-",
        "ph": "ph",
        "ms/cm": "ms/cm",
        "ntu": "ntu",
        "mpa.s": "mpa.s",
        "um": "um",
    }
    return aliases.get(normalized, normalized)


def _finite_nonnegative(value: float, label: str) -> float:
    number = float(value)
    if not isfinite(number) or number < 0.0:
        raise ValueError(f"{label} must be a finite, non-negative number; received {value!r}.")
    return number


def flow_to_kg_hr(
    value: float,
    unit: str,
    *,
    density_kg_m3: float | None = None,
    operating_hours_per_year: float = 8760.0,
) -> float:
    """Convert supported mass or volumetric flows to kg/h."""

    value = _finite_nonnegative(value, "Flow")
    unit = normalize_unit(unit)
    if unit == "kg/h":
        return value
    if unit == "t/d":
        return value * 1000.0 / 24.0
    if unit == "t/y":
        return value * 1000.0 / operating_hours_per_year
    if unit == "kg/y":
        return value / operating_hours_per_year
    if unit in {"m3/h", "m3/d", "l/h"}:
        if density_kg_m3 is None:
            raise ValueError(f"Density in kg/m3 is required to convert '{unit}' to kg/h.")
        density = _finite_nonnegative(density_kg_m3, "Density")
        volume_m3_h = value
        if unit == "m3/d":
            volume_m3_h /= 24.0
        elif unit == "l/h":
            volume_m3_h /= 1000.0
        return volume_m3_h * density
    raise ValueError(f"Unsupported flow unit '{unit}'.")


def concentration_to_kg_hr(
    value: float,
    unit: str,
    *,
    wet_mass_flow_kg_hr: float | None = None,
    dry_solids_flow_kg_hr: float | None = None,
    volumetric_flow_m3_hr: float | None = None,
    molecular_weight_g_mol: float | None = None,
) -> float:
    """Convert a supported concentration or composition basis to kg/h."""

    value = _finite_nonnegative(value, "Concentration")
    unit = normalize_unit(unit)
    if unit in {"mg/l", "mgn/l", "mgp/l", "mgk/l", "mgcaco3/l"}:
        if volumetric_flow_m3_hr is None:
            raise ValueError(f"Volumetric flow is required for '{unit}'.")
        return value * 0.001 * volumetric_flow_m3_hr
    if unit in {"g/l", "kg/m3"}:
        if volumetric_flow_m3_hr is None:
            raise ValueError(f"Volumetric flow is required for '{unit}'.")
        return value * volumetric_flow_m3_hr
    if unit == "mg/kgwet":
        if wet_mass_flow_kg_hr is None:
            raise ValueError("Wet mass flow is required for 'mg/kg wet'.")
        return value * 1e-6 * wet_mass_flow_kg_hr
    if unit == "g/kgwet":
        if wet_mass_flow_kg_hr is None:
            raise ValueError("Wet mass flow is required for 'g/kg wet'.")
        return value * 1e-3 * wet_mass_flow_kg_hr
    if unit == "g/kgts":
        if dry_solids_flow_kg_hr is None:
            raise ValueError("Dry-solids flow is required for 'g/kg TS'.")
        return value * 1e-3 * dry_solids_flow_kg_hr
    if unit in {"%wetmass", "wt.%"}:
        if wet_mass_flow_kg_hr is None:
            raise ValueError(f"Wet mass flow is required for '{unit}'.")
        return value / 100.0 * wet_mass_flow_kg_hr
    if unit == "mass_fraction":
        if wet_mass_flow_kg_hr is None:
            raise ValueError("Wet mass flow is required for mass fractions.")
        if value > 1.0:
            raise ValueError("Mass fractions cannot exceed 1.")
        return value * wet_mass_flow_kg_hr
    if unit == "%ts":
        if dry_solids_flow_kg_hr is None:
            raise ValueError("Dry-solids flow is required for '% TS'.")
        return value / 100.0 * dry_solids_flow_kg_hr
    if unit in {"mol/l", "mmol/l"}:
        if volumetric_flow_m3_hr is None or molecular_weight_g_mol is None:
            raise ValueError(f"Volumetric flow and molecular weight are required for '{unit}'.")
        factor = 1.0 if unit == "mol/l" else 0.001
        return value * factor * molecular_weight_g_mol * volumetric_flow_m3_hr
    if unit == "kg/h":
        return value
    raise ValueError(f"Unsupported concentration or composition unit '{unit}'.")


def convert_element_reporting(value: float, from_basis: str, to_basis: str) -> float:
    """Convert common N, P, and K element-equivalent reporting bases."""

    value = _finite_nonnegative(value, "Reported element quantity")
    key = (from_basis.strip().upper(), to_basis.strip().upper())
    factors = {
        ("N", "NH4+"): N_TO_NH4,
        ("NH4-N", "NH4+"): N_TO_NH4,
        ("N", "NH3"): N_TO_NH3,
        ("NH3-N", "NH3"): N_TO_NH3,
        ("P", "PO4-3"): P_TO_PO4,
        ("PO4-P", "PO4-3"): P_TO_PO4,
        ("P", "P2O5"): P_TO_P2O5,
        ("K", "K2O"): K_TO_K2O,
        ("N", "NO3-"): N_TO_NO3,
        ("NO3-N", "NO3-"): N_TO_NO3,
        ("P", "STRUVITE"): P_TO_STRUVITE,
        ("STRUVITE-P", "STRUVITE"): P_TO_STRUVITE,
        ("N", "STRUVITE"): N_TO_STRUVITE,
        ("STRUVITE-N", "STRUVITE"): N_TO_STRUVITE,
        ("NH4+", "N"): 1.0 / N_TO_NH4,
        ("NH3", "N"): 1.0 / N_TO_NH3,
        ("NO3-", "N"): 1.0 / N_TO_NO3,
        ("PO4-3", "P"): 1.0 / P_TO_PO4,
        ("P2O5", "P"): 1.0 / P_TO_P2O5,
        ("K2O", "K"): 1.0 / K_TO_K2O,
        ("STRUVITE", "P"): 1.0 / P_TO_STRUVITE,
        ("STRUVITE", "N"): 1.0 / N_TO_STRUVITE,
    }
    if key[0] == key[1]:
        return value
    try:
        return value * factors[key]
    except KeyError as error:
        raise ValueError(f"Unsupported element reporting conversion {key[0]} -> {key[1]}.") from error


def temperature_to_kelvin(value: float, unit: str) -> float:
    """Convert Celsius or Kelvin to Kelvin."""

    unit = normalize_unit(unit)
    temperature = float(value)
    if unit == "k":
        result = temperature
    elif unit == "degc":
        result = temperature + 273.15
    else:
        raise ValueError(f"Unsupported temperature unit '{unit}'.")
    if result <= 0.0:
        raise ValueError("Temperature must be above absolute zero.")
    return result
