"""Conservation and plausibility checks for GreenHub Phase 5."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Mapping

from Greenhub.analytical import calculate_elemental_flows
from Greenhub.chemicals import chemicals
from Greenhub.component_metadata import COMPONENT_METADATA
from Greenhub.phase4_validation import (
    _adjust_plant_inventory,
    _apply_delta_ledger,
    sum_stream_component_flows,
)

STRICT_ELEMENTS = ("carbon", "nitrogen", "phosphorus", "sulfur")
INFORMATIONAL_ELEMENTS = ("hydrogen", "oxygen")


def _cod(flows: Mapping[str, float]) -> float:
    return sum(
        float(value) * (COMPONENT_METADATA[component_id].cod_factor or 0.0)
        for component_id, value in flows.items()
    )


@dataclass(frozen=True)
class Phase5UnitBalance:
    """Mass and component residuals around one Phase 5 unit."""

    unit_id: str
    inlet_mass_kg_hr: float
    outlet_mass_kg_hr: float
    mass_error_kg_hr: float
    maximum_component_error_kg_hr: float


@dataclass(frozen=True)
class Phase5ValidationResult:
    """Complete Phase 5 validation result for reporting and tests."""

    overall_in_kg_hr: float
    overall_out_kg_hr: float
    overall_error_kg_hr: float
    component_errors_kg_hr: dict[str, float]
    element_in_kg_hr: dict[str, float]
    element_out_kg_hr: dict[str, float]
    element_errors_kg_hr: dict[str, float]
    cod_balance: dict[str, float]
    methane_check: dict[str, float]
    unit_balances: tuple[Phase5UnitBalance, ...]
    warnings: tuple[str, ...]
    report: str


def _expected_unit_outlet(unit) -> dict[str, float]:
    expected = sum_stream_component_flows(unit.ins)
    if unit.ID == "R501":
        expected = _apply_delta_ledger(
            expected,
            getattr(unit, "reaction_delta_kg_hr", {}),
        )
    return expected


def _validate_unit(unit, tolerance: float) -> Phase5UnitBalance:
    expected = _expected_unit_outlet(unit)
    actual = sum_stream_component_flows(unit.outs)
    errors = {ID: expected[ID] - actual[ID] for ID in chemicals.IDs}
    inlet_mass = sum(expected.values())
    outlet_mass = sum(actual.values())
    mass_error = inlet_mass - outlet_mass
    maximum = max((abs(value) for value in errors.values()), default=0.0)
    if abs(mass_error) > tolerance or maximum > tolerance:
        raise RuntimeError(
            f"Phase 5 unit {unit.ID} balance failed: mass={mass_error:.6g}, "
            f"component={maximum:.6g} kg/hr."
        )
    return Phase5UnitBalance(unit.ID, inlet_mass, outlet_mass, mass_error, maximum)


def _assert_nonnegative(streams: Iterable[object], tolerance: float) -> None:
    for stream in streams:
        negatives = {
            ID: float(stream.imass[ID])
            for ID in chemicals.IDs
            if float(stream.imass[ID]) < -tolerance
        }
        if negatives:
            raise RuntimeError(
                f"Phase 5 stream '{stream.ID}' contains negative flows: {negatives}."
            )


def validate_phase5_model(
    model,
    *,
    failure_tolerance_kg_hr: float = 1e-6,
    warning_tolerance_kg_hr: float = 1e-8,
) -> Phase5ValidationResult:
    """Validate unit and whole-plant mass, COD, C, N, P, and S balances."""

    if failure_tolerance_kg_hr <= 0.0 or warning_tolerance_kg_hr < 0.0:
        raise ValueError("Phase 5 validation tolerances are invalid.")
    _assert_nonnegative(model.streams.values(), failure_tolerance_kg_hr)
    unit_balances = tuple(
        _validate_unit(model.units[unit_id], failure_tolerance_kg_hr)
        for unit_id in ("M501", "H501", "R501", "V501")
        if unit_id in model.units
    )

    inlet = sum_stream_component_flows(model.system.ins)
    expected = _adjust_plant_inventory(model.upstream_model, inlet)
    reactor = model.units.get("R501")
    if reactor is not None:
        expected = _apply_delta_ledger(
            expected,
            getattr(reactor, "reaction_delta_kg_hr", {}),
        )
    outlet = sum_stream_component_flows(model.system.outs)
    component_errors = {ID: expected[ID] - outlet[ID] for ID in chemicals.IDs}
    overall_in = sum(inlet.values())
    overall_out = sum(outlet.values())
    overall_error = sum(expected.values()) - overall_out
    maximum_component = max(
        (abs(value) for value in component_errors.values()),
        default=0.0,
    )
    if abs(overall_error) > failure_tolerance_kg_hr or maximum_component > failure_tolerance_kg_hr:
        raise RuntimeError(
            "Phase 5 plant-wide component balance failed: "
            f"mass={overall_error:.6g}, component={maximum_component:.6g} kg/hr."
        )

    element_in = calculate_elemental_flows(inlet)
    element_out = calculate_elemental_flows(outlet)
    element_errors = {
        element: element_in[element] - element_out[element]
        for element in element_in
    }
    failed_elements = {
        element: element_errors[element]
        for element in STRICT_ELEMENTS
        if abs(element_errors[element]) > failure_tolerance_kg_hr
    }
    if failed_elements:
        raise RuntimeError(
            "Phase 5 elemental balance failed for C/N/P/S: "
            f"{failed_elements} kg/hr."
        )

    cod_in = _cod(inlet)
    cod_out = _cod(outlet)
    cod_error = cod_in - cod_out
    if abs(cod_error) > failure_tolerance_kg_hr:
        raise RuntimeError(f"Phase 5 COD balance failed by {cod_error:.6g} kg O2/hr.")
    cod_balance = {
        "cod_in_kg_o2_hr": cod_in,
        "cod_out_kg_o2_hr": cod_out,
        "cod_removed_from_liquid_kg_o2_hr": (
            float(getattr(reactor, "converted_cod_kg_hr", 0.0))
            if reactor is not None
            else 0.0
        ),
        "cod_balance_error_kg_o2_hr": cod_error,
    }

    methane_cod_factor = COMPONENT_METADATA["Methane"].cod_factor or 1.0
    methane_total = sum(float(stream.imass["Methane"]) for stream in model.system.outs)
    converted_cod = float(getattr(reactor, "converted_cod_kg_hr", 0.0)) if reactor else 0.0
    theoretical_methane = converted_cod / methane_cod_factor
    if methane_total > theoretical_methane + failure_tolerance_kg_hr:
        raise RuntimeError(
            "Produced methane exceeds the converted-COD theoretical ceiling: "
            f"{methane_total:.6g} > {theoretical_methane:.6g} kg/hr."
        )
    if not model.scenario.digestion_enabled and methane_total > failure_tolerance_kg_hr:
        raise RuntimeError("AD0 must not produce methane.")
    methane_check = {
        "methane_total_kg_hr": methane_total,
        "theoretical_methane_ceiling_kg_hr": theoretical_methane,
        "fraction_of_ceiling": methane_total / theoretical_methane if theoretical_methane else 0.0,
    }

    warnings = list(model.warnings)
    for unit_id in ("M501", "R501", "V501"):
        unit = model.units.get(unit_id)
        if unit is not None:
            warnings.extend(getattr(unit, "warnings", ()))
    warnings.append(
        "Hydrogen and oxygen residuals are informational only because formula-free pseudo-components "
        "do not support defensible full atom balances."
    )
    if maximum_component > warning_tolerance_kg_hr:
        warnings.append("Plant component residual exceeds the warning tolerance.")
    lines = [
        "GreenHub Phase 5 validation report",
        "==================================",
        f"Scenario: {model.scenario.scenario_id}",
        f"Upstream: {model.input_bundle.phase3_scenario_id}/{model.input_bundle.phase4_scenario_id}",
        f"Overall inlet mass:  {overall_in:.6g} kg/hr",
        f"Overall outlet mass: {overall_out:.6g} kg/hr",
        f"Overall residual:    {overall_error:.3g} kg/hr",
        f"COD residual:        {cod_error:.3g} kg O2/hr",
    ]
    lines.extend(
        f"{element.title()} residual: {element_errors[element]:.3g} kg/hr"
        for element in STRICT_ELEMENTS
    )
    lines.append(
        f"Methane/theoretical ceiling: {methane_total:.6g}/{theoretical_methane:.6g} kg/hr"
    )
    lines.append("PASS: mass, components, COD, C, N, P, S, non-negativity, and methane ceiling.")
    return Phase5ValidationResult(
        overall_in,
        overall_out,
        overall_error,
        component_errors,
        element_in,
        element_out,
        element_errors,
        cod_balance,
        methane_check,
        unit_balances,
        tuple(dict.fromkeys(warnings)),
        "\n".join(lines),
    )
