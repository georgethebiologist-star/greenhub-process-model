"""Conservation and physical-consistency checks for GreenHub Phase 7."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Mapping

from Greenhub.analytical import calculate_elemental_flows
from Greenhub.chemicals import chemicals
from Greenhub.component_groups import COMPONENT_GROUPS
from Greenhub.phase4_validation import sum_stream_component_flows

STRICT_ELEMENTS = (
    "carbon",
    "hydrogen",
    "oxygen",
    "nitrogen",
    "phosphorus",
    "potassium",
    "magnesium",
    "calcium",
    "sulfur",
    "chloride",
    "sodium",
)


@dataclass(frozen=True)
class Phase7UnitBalance:
    """Reaction-adjusted conservation residuals for one Phase 7 unit."""

    unit_id: str
    inlet_mass_kg_hr: float
    outlet_mass_kg_hr: float
    mass_error_kg_hr: float
    maximum_component_error_kg_hr: float
    maximum_element_error_kg_hr: float


@dataclass(frozen=True)
class Phase7ValidationResult:
    """Complete Phase 7 boundary, nutrient, and contaminant validation."""

    boundary_in_kg_hr: float
    boundary_out_kg_hr: float
    overall_error_kg_hr: float
    water_component_error_kg_hr: float
    component_errors_kg_hr: dict[str, float]
    element_in_kg_hr: dict[str, float]
    element_out_kg_hr: dict[str, float]
    element_errors_kg_hr: dict[str, float]
    contaminant_errors_kg_hr: dict[str, float]
    nutrient_destinations_kg_hr: dict[str, dict[str, float]]
    unit_balances: tuple[Phase7UnitBalance, ...]
    warnings: tuple[str, ...]
    report: str


def _add_delta(
    flows: Mapping[str, float],
    delta: Mapping[str, float] | None,
) -> dict[str, float]:
    result = {ID: float(flows.get(ID, 0.0)) for ID in chemicals.IDs}
    if delta:
        for ID, value in delta.items():
            result[ID] += float(value)
    return result


def _validate_unit(unit, tolerance: float) -> Phase7UnitBalance:
    inlet = sum_stream_component_flows(unit.ins)
    delta = getattr(unit, "reaction_delta_kg_hr", None)
    expected = _add_delta(inlet, delta)
    actual = sum_stream_component_flows(unit.outs)
    component_errors = {ID: expected[ID] - actual[ID] for ID in chemicals.IDs}
    inlet_elements = calculate_elemental_flows(inlet)
    outlet_elements = calculate_elemental_flows(actual)
    element_errors = {
        element: inlet_elements[element] - outlet_elements[element]
        for element in inlet_elements
    }
    raw_mass_error = sum(inlet.values()) - sum(actual.values())
    maximum_component = max((abs(value) for value in component_errors.values()), default=0.0)
    maximum_element = max((abs(value) for value in element_errors.values()), default=0.0)
    if abs(sum(expected.values()) - sum(actual.values())) > tolerance or maximum_component > tolerance:
        raise RuntimeError(
            f"Phase 7 unit {unit.ID} component balance failed: "
            f"mass={sum(expected.values()) - sum(actual.values()):.6g}, "
            f"component={maximum_component:.6g} kg/hr."
        )
    if abs(raw_mass_error) > tolerance or maximum_element > tolerance:
        raise RuntimeError(
            f"Phase 7 unit {unit.ID} reaction is not mass/element balanced: "
            f"mass={raw_mass_error:.6g}, element={maximum_element:.6g} kg/hr."
        )
    return Phase7UnitBalance(
        unit.ID,
        sum(inlet.values()),
        sum(actual.values()),
        raw_mass_error,
        maximum_component,
        maximum_element,
    )


def _assert_nonnegative(streams: Iterable[object], tolerance: float) -> None:
    for stream in streams:
        negatives = {
            ID: float(stream.imass[ID])
            for ID in chemicals.IDs
            if float(stream.imass[ID]) < -tolerance
        }
        if negatives:
            raise RuntimeError(
                f"Phase 7 stream '{stream.ID}' contains negative flows: {negatives}."
            )
        if stream.P <= 0.0:
            raise RuntimeError(f"Phase 7 stream '{stream.ID}' has non-positive pressure.")


def _assert_bounded_unit_values(model, tolerance: float) -> None:
    for unit_id in model.parameters["phase7_unit_ids"]:
        unit = model.units[unit_id]
        for attribute in (
            "component_capture_to_solids",
            "component_capture_to_product",
            "component_rejections",
        ):
            values = getattr(unit, attribute, {})
            for name, value in values.items():
                if value < -tolerance or value > 1.0 + tolerance:
                    raise RuntimeError(
                        f"{unit_id} value {attribute}[{name}]={value} is outside [0, 1]."
                    )
        calculation = getattr(unit, "calculation", None)
        if calculation is not None:
            for attribute in ("removal_fraction", "water_recovery_fraction"):
                if hasattr(calculation, attribute):
                    value = float(getattr(calculation, attribute))
                    if value < -tolerance or value > 1.0 + tolerance:
                        raise RuntimeError(
                            f"{unit_id} calculated {attribute}={value} is outside [0, 1]."
                        )


def _validate_separator_logic(model, tolerance: float) -> None:
    separator = model.units.get("S701")
    if separator is None:
        return
    feed = separator.ins[0]
    solids, centrate = separator.outs
    for component_id in ("SuspendedSolids", "InertSolids", "MicrobialBiomass", "ParticulatePhosphorus"):
        available = float(feed.imass[component_id])
        configured = separator.component_capture_to_solids.get(component_id, 0.0)
        actual = float(solids.imass[component_id]) / available if available else configured
        if available > tolerance and abs(actual - configured) > tolerance:
            raise RuntimeError(f"S701 does not reproduce the configured {component_id} capture.")
        if available > tolerance and configured >= 0.5 and actual < 0.5 - tolerance:
            raise RuntimeError(f"S701 must send most {component_id} to nutrient-rich solids.")
    for component_id in ("Ammonium", "PotassiumIon", "Orthophosphate", "SulfateIon", "ChlorideIon"):
        available = float(feed.imass[component_id])
        if available <= tolerance:
            continue
        centrate_fraction = float(centrate.imass[component_id]) / available
        if centrate_fraction < 0.5 - tolerance:
            raise RuntimeError(f"S701 must retain most soluble {component_id} in centrate.")


def _nutrient_destinations(model) -> dict[str, dict[str, float]]:
    destinations: dict[str, dict[str, float]] = {
        element: {} for element in ("nitrogen", "phosphorus", "potassium", "magnesium", "calcium")
    }
    for stream in model.boundary_outputs:
        elements = calculate_elemental_flows(sum_stream_component_flows((stream,)))
        for element in destinations:
            destinations[element][stream.ID] = elements[element]
    return destinations


def validate_phase7_model(
    model,
    *,
    failure_tolerance_kg_hr: float = 1e-6,
    warning_tolerance_kg_hr: float = 1e-8,
) -> Phase7ValidationResult:
    """Validate Phase 7 units, boundary, elements, nutrients, and contaminants."""

    if failure_tolerance_kg_hr <= 0.0 or warning_tolerance_kg_hr < 0.0:
        raise ValueError("Phase 7 validation tolerances are invalid.")
    _assert_nonnegative(model.streams.values(), failure_tolerance_kg_hr)
    unit_ids = tuple(dict.fromkeys(model.parameters["phase7_unit_ids"]))
    unit_balances = tuple(
        _validate_unit(model.units[unit_id], failure_tolerance_kg_hr)
        for unit_id in unit_ids
    )
    _assert_bounded_unit_values(model, failure_tolerance_kg_hr)
    _validate_separator_logic(model, failure_tolerance_kg_hr)

    inlet_streams = (model.streams["digestate_feed"], *model.external_inputs)
    inlet = sum_stream_component_flows(inlet_streams)
    expected = dict(inlet)
    for unit_id in unit_ids:
        expected = _add_delta(
            expected,
            getattr(model.units[unit_id], "reaction_delta_kg_hr", None),
        )
    outlet = sum_stream_component_flows(model.boundary_outputs)
    component_errors = {ID: expected[ID] - outlet[ID] for ID in chemicals.IDs}
    boundary_in = sum(inlet.values())
    boundary_out = sum(outlet.values())
    overall_error = boundary_in - boundary_out
    water_error = component_errors["Water"]
    maximum_component = max((abs(value) for value in component_errors.values()), default=0.0)
    if abs(overall_error) > failure_tolerance_kg_hr or maximum_component > failure_tolerance_kg_hr:
        raise RuntimeError(
            "Phase 7 boundary component balance failed: "
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
        raise RuntimeError(f"Phase 7 elemental balance failed: {failed_elements} kg/hr.")

    contaminant_errors = {
        ID: float(inlet[ID]) - float(outlet[ID])
        for ID in COMPONENT_GROUPS["contaminants"]
    }
    failed_contaminants = {
        ID: error
        for ID, error in contaminant_errors.items()
        if abs(error) > failure_tolerance_kg_hr
    }
    if failed_contaminants:
        raise RuntimeError(
            f"Phase 7 persistent-contaminant balance failed: {failed_contaminants}."
        )

    destinations = _nutrient_destinations(model)
    warnings = list(model.warnings)
    for unit_id in unit_ids:
        warnings.extend(getattr(model.units[unit_id], "warnings", ()))
    if maximum_component > warning_tolerance_kg_hr:
        warnings.append("Phase 7 component residual exceeds the warning tolerance.")
    if model.scenario.potassium_route == "concentration":
        warnings.append(
            "The potassium-rich stream is a non-selective salt concentrate; product purity is not implied."
        )
    if model.parameters["recovered_heat_available_kw"] <= 0.0:
        warnings.append(
            "No recovered heat is available from the current upstream model; Phase 7 thermal demand remains external."
        )
    lines = [
        "GreenHub Phase 7 validation report",
        "==================================",
        f"Scenario: {model.scenario.scenario_id} - {model.scenario.name}",
        f"Process order: {model.input_bundle.process_order}",
        (
            "Upstream: "
            f"{model.input_bundle.phase3_scenario_id}/"
            f"{model.input_bundle.phase4_scenario_id}/"
            f"{model.input_bundle.phase5_scenario_id}/"
            f"{model.input_bundle.phase6_scenario_id}"
        ),
        f"Boundary inlet mass:  {boundary_in:.6g} kg/hr",
        f"Boundary outlet mass: {boundary_out:.6g} kg/hr",
        f"Overall residual:     {overall_error:.3g} kg/hr",
        f"Water-ledger residual:{water_error: .3g} kg/hr",
    ]
    lines.extend(
        f"{element.title()} residual: {element_errors[element]:.3g} kg/hr"
        for element in STRICT_ELEMENTS
    )
    lines.append(
        "PASS: total mass, reaction-adjusted components, water ledger, strict elements, "
        "counterions, contaminants, non-negativity, split bounds, and separation logic."
    )
    return Phase7ValidationResult(
        boundary_in,
        boundary_out,
        overall_error,
        water_error,
        component_errors,
        element_in,
        element_out,
        element_errors,
        contaminant_errors,
        destinations,
        unit_balances,
        tuple(dict.fromkeys(warnings)),
        "\n".join(lines),
    )
