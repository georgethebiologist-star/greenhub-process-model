"""Mass, element, analytical, split, and charge diagnostics for Phase 2."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping

from Greenhub.analytical import calculate_elemental_flows
from Greenhub.chemicals import chemicals
from Greenhub.separator import SeparatorParameters, resolve_separator_splits

ION_CHARGES = {
    "HydrogenIon": 1,
    "HydroxideIon": -1,
    "Ammonium": 1,
    "NitrateIon": -1,
    "NitriteIon": -1,
    "Orthophosphate": -3,
    "PotassiumIon": 1,
    "SodiumIon": 1,
    "MagnesiumIon": 2,
    "CalciumIon": 2,
    "ChlorideIon": -1,
    "SulfateIon": -2,
    "BicarbonateIon": -1,
    "CarbonateIon": -2,
}


@dataclass(frozen=True)
class ChargeBalanceDiagnostic:
    cation_equivalents_kmol_hr: float
    anion_equivalents_kmol_hr: float
    net_equivalents_kmol_hr: float
    relative_error: float | None
    status: str


@dataclass(frozen=True)
class ValidationResult:
    """Structured Phase 2 validation output."""

    overall_in_kg_hr: float
    overall_out_kg_hr: float
    overall_error_kg_hr: float
    component_errors_kg_hr: dict[str, float]
    element_errors_kg_hr: dict[str, float]
    charge_balance: ChargeBalanceDiagnostic
    warnings: tuple[str, ...]
    report: str


def validate_split_bounds(splits: Mapping[str, float] | None = None) -> None:
    """Ensure every fraction-to-clarified value is physically bounded."""

    splits = splits or resolve_separator_splits(SeparatorParameters()).splits_to_clarified
    invalid = {ID: value for ID, value in splits.items() if not 0.0 <= float(value) <= 1.0}
    if invalid:
        raise ValueError(f"Separator split fractions must be within [0, 1]: {invalid}")


def charge_balance_diagnostic(component_flows: Mapping[str, float]) -> ChargeBalanceDiagnostic:
    """Calculate an ion-equivalent diagnostic without automatic correction."""

    cations = 0.0
    anions = 0.0
    for component_id, charge in ION_CHARGES.items():
        kmol_hr = float(component_flows.get(component_id, 0.0)) / chemicals[component_id].MW
        equivalents = kmol_hr * charge
        if charge > 0:
            cations += equivalents
        else:
            anions += -equivalents
    total = cations + anions
    net = cations - anions
    relative = abs(net) / total if total > 0.0 else None
    if relative is None:
        status = "insufficient_ionic_data"
    elif relative <= 0.10:
        status = "pass"
    elif relative <= 0.30:
        status = "warning"
    else:
        status = "large_gap"
    return ChargeBalanceDiagnostic(cations, anions, net, relative, status)


def validate_characterization(model) -> tuple[str, ...]:
    """Validate physical relationships and return non-fatal scientific warnings."""

    indicators = model.characterization.indicators
    physical = model.characterization.physical
    warnings = list(model.characterization.warnings)
    wet = float(indicators["total_wet_mass_kg_hr"] or 0.0)
    dry = float(indicators["dry_solids_kg_hr"] or 0.0)
    volatile = float(indicators["volatile_solids_kg_hr"] or 0.0)
    tss = float(indicators["tss_kg_hr"] or 0.0)
    if wet <= 0.0:
        raise ValueError("Characterized total wet mass must be positive.")
    if dry < -1e-9 or dry > wet + 1e-9:
        raise ValueError("Characterized dry solids must be within total wet mass.")
    if volatile > dry + 1e-9:
        raise ValueError("Calculated volatile solids exceed dry solids.")
    if tss > dry + 1e-9:
        raise ValueError("Calculated suspended solids exceed dry solids.")
    if physical.pH is not None and not 0.0 <= physical.pH <= 14.0:
        raise ValueError("Stream pH must be within [0, 14].")
    for row in model.characterization.reconciliation:
        if row.status == "large_gap":
            warnings.append(f"Large analytical reconciliation gap for '{row.measurement}'.")
    return tuple(dict.fromkeys(warnings))


def validate_mass_balance(model, tolerance: float = 1e-6) -> ValidationResult:
    """Validate active-system component, total-mass, and elemental closure."""

    splits = model.separator_splits.splits_to_clarified
    validate_split_bounds(splits)
    feed = model.streams["feed"]
    clarified = model.streams["clarified_liquid"]
    wet_solids = model.streams["wet_solids"]

    overall_in = float(feed.F_mass)
    overall_out = float(clarified.F_mass + wet_solids.F_mass)
    overall_error = overall_in - overall_out
    if abs(overall_error) > tolerance:
        raise RuntimeError(
            f"Overall mass balance failed: inlet={overall_in:.6g}, "
            f"outlet={overall_out:.6g}, residual={overall_error:.6g} kg/hr."
        )

    component_errors: dict[str, float] = {}
    inlet_flows: dict[str, float] = {}
    outlet_flows: dict[str, float] = {}
    for component_id in chemicals.IDs:
        inlet = float(feed.imass[component_id])
        outlet = float(clarified.imass[component_id] + wet_solids.imass[component_id])
        residual = inlet - outlet
        component_errors[component_id] = residual
        inlet_flows[component_id] = inlet
        outlet_flows[component_id] = outlet
        if abs(residual) > tolerance:
            raise RuntimeError(
                f"Component mass balance failed for {component_id}: "
                f"inlet={inlet:.6g}, outlet={outlet:.6g}, residual={residual:.6g} kg/hr."
            )

    inlet_elements = calculate_elemental_flows(inlet_flows)
    outlet_elements = calculate_elemental_flows(outlet_flows)
    element_errors = {
        element: inlet_elements[element] - outlet_elements[element]
        for element in inlet_elements
    }
    invalid_elements = {key: value for key, value in element_errors.items() if abs(value) > tolerance}
    if invalid_elements:
        raise RuntimeError(f"Elemental balance failed: {invalid_elements}")

    if 1.0 - splits["SuspendedSolids"] <= 0.5:
        raise RuntimeError("Wet-solids stream does not capture most SuspendedSolids.")
    if 1.0 - splits["InertSolids"] <= 0.5:
        raise RuntimeError("Wet-solids stream does not capture most InertSolids.")
    if splits["Glucose"] <= 0.5 or splits["SolubleProtein"] <= 0.5:
        raise RuntimeError("Clarified stream does not retain most soluble feed material.")

    warnings = validate_characterization(model)
    charge = charge_balance_diagnostic(inlet_flows)
    lines = [
        "Phase 2 validation report",
        "=========================",
        f"Overall inlet mass:  {overall_in:.6g} kg/hr",
        f"Overall outlet mass: {overall_out:.6g} kg/hr",
        f"Overall residual:    {overall_error:.3g} kg/hr",
        f"Maximum component residual: {max(abs(i) for i in component_errors.values()):.3g} kg/hr",
        f"Maximum element residual:   {max(abs(i) for i in element_errors.values()):.3g} kg/hr",
        "",
        "Separator logic",
        f"  SuspendedSolids to wet solids: {1.0 - splits['SuspendedSolids']:.1%}",
        f"  InertSolids to wet solids:     {1.0 - splits['InertSolids']:.1%}",
        f"  Glucose to clarified liquid:   {splits['Glucose']:.1%}",
        f"  SolubleProtein to clarified:   {splits['SolubleProtein']:.1%}",
        "",
        "Charge diagnostic",
        f"  Cation equivalents: {charge.cation_equivalents_kmol_hr:.6g} kmol charge/hr",
        f"  Anion equivalents:  {charge.anion_equivalents_kmol_hr:.6g} kmol charge/hr",
        f"  Status: {charge.status}",
    ]
    if warnings:
        lines.extend(["", "Warnings", *[f"  {warning}" for warning in warnings]])
    return ValidationResult(overall_in, overall_out, overall_error, component_errors, element_errors, charge, warnings, "\n".join(lines))


def separator_partitioning_rows(model) -> list[dict[str, object]]:
    """Return component-wise S101 partitioning for reports."""

    feed = model.streams["feed"]
    clarified = model.streams["clarified_liquid"]
    solids = model.streams["wet_solids"]
    rows = []
    for component_id in chemicals.IDs:
        inlet = float(feed.imass[component_id])
        rows.append(
            {
                "component_id": component_id,
                "inlet_kg_hr": inlet,
                "split_to_clarified": model.separator_splits.splits_to_clarified[component_id],
                "split_source": model.separator_splits.source_by_component[component_id],
                "clarified_kg_hr": float(clarified.imass[component_id]),
                "wet_solids_kg_hr": float(solids.imass[component_id]),
                "component_residual_kg_hr": inlet - float(clarified.imass[component_id] + solids.imass[component_id]),
            }
        )
    return rows
