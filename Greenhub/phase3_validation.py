"""Plant-wide and unit-level conservation checks for Phase 3."""

from __future__ import annotations

from dataclasses import dataclass

from Greenhub.analytical import calculate_elemental_flows
from Greenhub.chemicals import chemicals
from Greenhub.component_groups import COMPONENT_GROUPS
from Greenhub.component_metadata import COMPONENT_METADATA


def _stream_flows(stream) -> dict[str, float]:
    return {ID: float(stream.imass[ID]) for ID in chemicals.IDs}


def _sum_streams(streams) -> dict[str, float]:
    return {
        ID: sum(float(stream.imass[ID]) for stream in streams)
        for ID in chemicals.IDs
    }


def _cod(flows: dict[str, float]) -> float:
    return sum(
        flow * (COMPONENT_METADATA[ID].cod_factor or 0.0)
        for ID, flow in flows.items()
    )


def _apply_declared_pef_transfers(flows: dict[str, float], pef_unit) -> dict[str, float]:
    """Return the expected post-PEF inventory after declared pool transfers."""

    adjusted = dict(flows)
    for transfer_name, amount in pef_unit.transfers_kg_hr.items():
        source, target = transfer_name.split("_to_", 1)
        adjusted[source] -= float(amount)
        adjusted[target] += float(amount)
    return adjusted


@dataclass(frozen=True)
class UnitBalanceResult:
    unit_id: str
    mass_error_kg_hr: float
    maximum_component_error_kg_hr: float
    maximum_element_error_kg_hr: float


@dataclass(frozen=True)
class Phase3ValidationResult:
    overall_in_kg_hr: float
    overall_out_kg_hr: float
    overall_error_kg_hr: float
    component_errors_kg_hr: dict[str, float]
    element_errors_kg_hr: dict[str, float]
    unit_balances: tuple[UnitBalanceResult, ...]
    warnings: tuple[str, ...]
    report: str


def _validate_flows(
    label: str,
    inlet_flows: dict[str, float],
    outlet_flows: dict[str, float],
    tolerance: float,
) -> UnitBalanceResult:
    component_errors = {
        ID: inlet_flows[ID] - outlet_flows[ID]
        for ID in chemicals.IDs
    }
    mass_error = sum(inlet_flows.values()) - sum(outlet_flows.values())
    inlet_elements = calculate_elemental_flows(inlet_flows)
    outlet_elements = calculate_elemental_flows(outlet_flows)
    element_errors = {
        element: inlet_elements[element] - outlet_elements[element]
        for element in inlet_elements
    }
    max_component = max(abs(value) for value in component_errors.values())
    max_element = max(abs(value) for value in element_errors.values())
    if abs(mass_error) > tolerance or max_component > tolerance or max_element > tolerance:
        raise RuntimeError(
            f"{label} balance failed: mass={mass_error:.6g}, "
            f"max component={max_component:.6g}, max element={max_element:.6g} kg/hr."
        )
    return UnitBalanceResult(label, mass_error, max_component, max_element)


def validate_phase3_model(
    model,
    *,
    failure_tolerance_kg_hr: float = 1e-6,
    warning_tolerance_kg_hr: float = 1e-8,
) -> Phase3ValidationResult:
    """Validate every custom unit and the complete isolated scenario boundary."""

    if failure_tolerance_kg_hr <= 0.0 or warning_tolerance_kg_hr < 0.0:
        raise ValueError("Validation tolerances must be non-negative and failure tolerance positive.")
    unit_results = []
    for unit in model.system.units:
        unit_inlet_flows = _sum_streams(unit.ins)
        if unit.ID == "U201":
            unit_inlet_flows = _apply_declared_pef_transfers(unit_inlet_flows, unit)
        unit_results.append(
            _validate_flows(
                unit.ID,
                unit_inlet_flows,
                _sum_streams(unit.outs),
                failure_tolerance_kg_hr,
            )
        )

    inlet_flows = _sum_streams(model.system.ins)
    outlet_flows = _sum_streams(model.system.outs)
    reconciled_inlet_flows = (
        _apply_declared_pef_transfers(inlet_flows, model.units["U201"])
        if "U201" in model.units
        else inlet_flows
    )
    plant = _validate_flows(
        "plant_wide",
        reconciled_inlet_flows,
        outlet_flows,
        failure_tolerance_kg_hr,
    )
    component_errors = {
        ID: reconciled_inlet_flows[ID] - outlet_flows[ID]
        for ID in chemicals.IDs
    }
    inlet_elements = calculate_elemental_flows(reconciled_inlet_flows)
    outlet_elements = calculate_elemental_flows(outlet_flows)
    element_errors = {
        element: inlet_elements[element] - outlet_elements[element]
        for element in inlet_elements
    }

    warnings = list(model.warnings)
    for unit in model.units.values():
        warnings.extend(getattr(unit, "warnings", ()))
    if max(abs(value) for value in component_errors.values()) > warning_tolerance_kg_hr:
        warnings.append("Plant component residual exceeds the configured warning tolerance.")

    if "U201" in model.units:
        unit = model.units["U201"]
        feed_flows = _sum_streams(unit.ins)
        product_flows = _sum_streams(unit.outs)
        if abs(_cod(feed_flows) - _cod(product_flows)) > failure_tolerance_kg_hr:
            raise RuntimeError("PEF COD conservation failed; a transfer changed COD inventory.")
        protein_ids = COMPONENT_GROUPS["protein_equivalents"]
        protein_in = sum(feed_flows[ID] for ID in protein_ids)
        protein_out = sum(product_flows[ID] for ID in protein_ids)
        if abs(protein_in - protein_out) > failure_tolerance_kg_hr:
            raise RuntimeError("PEF protein conservation failed.")

    raw = model.streams["raw_liquid_fraction"]
    clarified = model.streams["clarified_liquid"]
    sludge = model.streams["primary_sludge"]
    raw_tss = sum(float(raw.imass[ID]) for ID in COMPONENT_GROUPS["suspended_solids"])
    clarified_tss = sum(float(clarified.imass[ID]) for ID in COMPONENT_GROUPS["suspended_solids"])
    if raw_tss > 0.0 and clarified_tss >= raw_tss:
        raise RuntimeError("Primary centrifuge did not reduce suspended solids in clarified liquid.")
    if float(clarified.imass["SolubleProtein"]) < float(sludge.imass["SolubleProtein"]):
        raise RuntimeError("Primary centrifuge sends more soluble protein to sludge than clarified liquid.")

    overall_in = sum(inlet_flows.values())
    overall_out = sum(outlet_flows.values())
    lines = [
        "GreenHub Phase 3 validation report",
        "==================================",
        f"Scenario: {model.scenario.scenario_id}",
        f"Overall inlet mass:  {overall_in:.6g} kg/hr",
        f"Overall outlet mass: {overall_out:.6g} kg/hr",
        f"Overall residual:    {plant.mass_error_kg_hr:.3g} kg/hr",
        f"Maximum component residual: {plant.maximum_component_error_kg_hr:.3g} kg/hr",
        f"Maximum element residual:   {plant.maximum_element_error_kg_hr:.3g} kg/hr",
        "",
        "Unit balances",
    ]
    lines.extend(
        f"  {result.unit_id}: mass={result.mass_error_kg_hr:.3g}, "
        f"component={result.maximum_component_error_kg_hr:.3g}, "
        f"element={result.maximum_element_error_kg_hr:.3g} kg/hr"
        for result in unit_results
    )
    if warnings:
        lines.extend(["", "Warnings", *[f"  {warning}" for warning in dict.fromkeys(warnings)]])
    return Phase3ValidationResult(
        overall_in,
        overall_out,
        plant.mass_error_kg_hr,
        component_errors,
        element_errors,
        tuple(unit_results),
        tuple(dict.fromkeys(warnings)),
        "\n".join(lines),
    )
