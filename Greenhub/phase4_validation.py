"""Unit and plant-wide conservation checks for GreenHub Phase 4."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Mapping

from Greenhub.analytical import calculate_elemental_flows
from Greenhub.chemicals import chemicals
from Greenhub.component_metadata import COMPONENT_METADATA

PROTEIN_POOL_IDS = frozenset(
    {
        "SolubleProtein",
        "SuspendedProtein",
        "PrecipitatedProtein",
        "HeatCoagulatedProtein",
        "DegradedProtein",
    }
)


def stream_component_flows(stream) -> dict[str, float]:
    """Return every active component flow in kg/hr."""

    return {ID: float(stream.imass[ID]) for ID in chemicals.IDs}


def sum_stream_component_flows(streams: Iterable[object]) -> dict[str, float]:
    """Sum component flows across a stream collection."""

    return {
        ID: sum(float(stream.imass[ID]) for stream in streams)
        for ID in chemicals.IDs
    }


def _apply_transfer_ledger(
    flows: dict[str, float],
    transfers: Mapping[str, float],
) -> dict[str, float]:
    adjusted = dict(flows)
    for name, value in transfers.items():
        source, target = name.split("_to_", 1)
        amount = float(value)
        adjusted[source] -= amount
        adjusted[target] += amount
    return adjusted


def _apply_delta_ledger(
    flows: dict[str, float],
    deltas: Mapping[str, float],
) -> dict[str, float]:
    adjusted = dict(flows)
    for ID, delta in deltas.items():
        adjusted[ID] += float(delta)
    return adjusted


def _cod(flows: Mapping[str, float]) -> float:
    return sum(
        float(flow) * (COMPONENT_METADATA[ID].cod_factor or 0.0)
        for ID, flow in flows.items()
    )


def _toc(flows: Mapping[str, float]) -> float:
    return sum(
        float(flow) * (COMPONENT_METADATA[ID].toc_factor or 0.0)
        for ID, flow in flows.items()
    )


def _protein(flows: Mapping[str, float]) -> float:
    return sum(float(flows.get(ID, 0.0)) for ID in PROTEIN_POOL_IDS)


@dataclass(frozen=True)
class Phase4UnitBalance:
    """Conservation residuals around one active Phase 4 unit."""

    unit_id: str
    inlet_mass_kg_hr: float
    outlet_mass_kg_hr: float
    mass_error_kg_hr: float
    maximum_component_error_kg_hr: float
    maximum_element_error_kg_hr: float


@dataclass(frozen=True)
class Phase4ValidationResult:
    """Structured Phase 4 validation result used by reports and tests."""

    overall_in_kg_hr: float
    overall_out_kg_hr: float
    overall_error_kg_hr: float
    component_errors_kg_hr: dict[str, float]
    element_in_kg_hr: dict[str, float]
    element_out_kg_hr: dict[str, float]
    element_errors_kg_hr: dict[str, float]
    protein_balance: dict[str, float]
    nitrogen_balance: dict[str, float]
    cod_balance: dict[str, float]
    toc_balance: dict[str, float]
    unit_balances: tuple[Phase4UnitBalance, ...]
    warnings: tuple[str, ...]
    report: str


def _expected_unit_outlet_flows(unit) -> dict[str, float]:
    expected = sum_stream_component_flows(unit.ins)
    if unit.ID in {"R401", "DR401"}:
        expected = _apply_transfer_ledger(expected, getattr(unit, "transfers_kg_hr", {}))
    if unit.ID == "M403" and hasattr(unit, "reaction_delta_kg_hr"):
        expected = _apply_delta_ledger(expected, unit.reaction_delta_kg_hr)
    return expected


def _validate_one_unit(unit, tolerance: float) -> Phase4UnitBalance:
    expected = _expected_unit_outlet_flows(unit)
    actual = sum_stream_component_flows(unit.outs)
    component_errors = {ID: expected[ID] - actual[ID] for ID in chemicals.IDs}
    expected_elements = calculate_elemental_flows(expected)
    actual_elements = calculate_elemental_flows(actual)
    element_errors = {
        name: expected_elements[name] - actual_elements[name]
        for name in expected_elements
    }
    inlet_mass = sum(expected.values())
    outlet_mass = sum(actual.values())
    mass_error = inlet_mass - outlet_mass
    max_component = max(abs(value) for value in component_errors.values())
    max_element = max(abs(value) for value in element_errors.values())
    if abs(mass_error) > tolerance or max_component > tolerance or max_element > tolerance:
        raise RuntimeError(
            f"Phase 4 unit {unit.ID} balance failed: mass={mass_error:.6g}, "
            f"component={max_component:.6g}, element={max_element:.6g} kg/hr."
        )
    return Phase4UnitBalance(
        unit.ID,
        inlet_mass,
        outlet_mass,
        mass_error,
        max_component,
        max_element,
    )


def _adjust_plant_inventory(model, inlet_flows: dict[str, float]) -> dict[str, float]:
    adjusted = dict(inlet_flows)
    for unit_id in ("U201", "R401", "DR401"):
        unit = model.units.get(unit_id)
        if unit is not None:
            adjusted = _apply_transfer_ledger(
                adjusted,
                getattr(unit, "transfers_kg_hr", {}),
            )
    neutralization = model.units.get("M403")
    if neutralization is not None and hasattr(neutralization, "reaction_delta_kg_hr"):
        adjusted = _apply_delta_ledger(
            adjusted,
            neutralization.reaction_delta_kg_hr,
        )
    return adjusted


def _assert_nonnegative_streams(model, tolerance: float) -> None:
    for name, stream in model.streams.items():
        negatives = {
            ID: float(stream.imass[ID])
            for ID in chemicals.IDs
            if float(stream.imass[ID]) < -tolerance
        }
        if negatives:
            raise RuntimeError(f"Phase 4 stream '{name}' contains negative flows: {negatives}.")


def validate_phase4_model(
    model,
    *,
    failure_tolerance_kg_hr: float = 1e-6,
    warning_tolerance_kg_hr: float = 1e-8,
) -> Phase4ValidationResult:
    """Validate active units and the complete feed-to-products boundary."""

    if failure_tolerance_kg_hr <= 0.0 or warning_tolerance_kg_hr < 0.0:
        raise ValueError("Phase 4 validation tolerances are invalid.")
    _assert_nonnegative_streams(model, failure_tolerance_kg_hr)
    phase4_ids = ("M401", "H401", "R401", "C401", "W401", "D401", "DR401", "M402", "M403")
    unit_balances = tuple(
        _validate_one_unit(model.units[ID], failure_tolerance_kg_hr)
        for ID in phase4_ids
        if ID in model.units
    )

    inlet_raw = sum_stream_component_flows(model.system.ins)
    expected_out = _adjust_plant_inventory(model, inlet_raw)
    actual_out = sum_stream_component_flows(model.system.outs)
    component_errors = {
        ID: expected_out[ID] - actual_out[ID]
        for ID in chemicals.IDs
    }
    overall_in = sum(inlet_raw.values())
    overall_out = sum(actual_out.values())
    overall_error = sum(expected_out.values()) - overall_out
    max_component = max(abs(value) for value in component_errors.values())
    element_in = calculate_elemental_flows(expected_out)
    element_out = calculate_elemental_flows(actual_out)
    element_errors = {
        name: element_in[name] - element_out[name]
        for name in element_in
    }
    max_element = max(abs(value) for value in element_errors.values())
    if (
        abs(overall_error) > failure_tolerance_kg_hr
        or max_component > failure_tolerance_kg_hr
        or max_element > failure_tolerance_kg_hr
    ):
        raise RuntimeError(
            "Phase 4 plant-wide balance failed: "
            f"mass={overall_error:.6g}, component={max_component:.6g}, "
            f"element={max_element:.6g} kg/hr."
        )

    protein_feed = _protein(stream_component_flows(model.streams["clarified_protein_rich_liquid"]))
    protein_product = _protein(stream_component_flows(model.streams["dry_protein_product"]))
    protein_liquid = _protein(
        stream_component_flows(model.streams["conditioned_protein_depleted_liquid"])
    )
    protein_exhaust = _protein(stream_component_flows(model.streams["dryer_exhaust"]))
    protein_error = protein_feed - protein_product - protein_liquid - protein_exhaust
    if abs(protein_error) > failure_tolerance_kg_hr:
        raise RuntimeError(f"Phase 4 protein inventory failed by {protein_error:.6g} kg/hr.")
    protein_balance = {
        "protein_entering_kg_hr": protein_feed,
        "protein_in_product_kg_hr": protein_product,
        "protein_in_conditioned_liquid_kg_hr": protein_liquid,
        "protein_in_dryer_exhaust_kg_hr": protein_exhaust,
        "protein_balance_error_kg_hr": protein_error,
    }

    phase4_feed_flows = stream_component_flows(model.streams["clarified_protein_rich_liquid"])
    product_flows = stream_component_flows(model.streams["dry_protein_product"])
    residual_flows = stream_component_flows(model.streams["conditioned_protein_depleted_liquid"])
    exhaust_flows = stream_component_flows(model.streams["dryer_exhaust"])
    nitrogen_feed = calculate_elemental_flows(phase4_feed_flows)["nitrogen"]
    nitrogen_product = calculate_elemental_flows(product_flows)["nitrogen"]
    nitrogen_residual = calculate_elemental_flows(residual_flows)["nitrogen"]
    nitrogen_exhaust = calculate_elemental_flows(exhaust_flows)["nitrogen"]
    nitrogen_error = nitrogen_feed - nitrogen_product - nitrogen_residual - nitrogen_exhaust
    if abs(nitrogen_error) > failure_tolerance_kg_hr:
        raise RuntimeError(f"Phase 4 nitrogen balance failed by {nitrogen_error:.6g} kg/hr.")
    nitrogen_balance = {
        "nitrogen_entering_kg_hr": nitrogen_feed,
        "nitrogen_in_product_kg_hr": nitrogen_product,
        "nitrogen_in_conditioned_liquid_kg_hr": nitrogen_residual,
        "nitrogen_in_dryer_exhaust_kg_hr": nitrogen_exhaust,
        "nitrogen_balance_error_kg_hr": nitrogen_error,
    }

    cod_feed = _cod(phase4_feed_flows)
    cod_product = _cod(product_flows)
    cod_residual = _cod(residual_flows)
    cod_exhaust = _cod(exhaust_flows)
    cod_error = cod_feed - cod_product - cod_residual - cod_exhaust
    if abs(cod_error) > failure_tolerance_kg_hr:
        raise RuntimeError(f"Phase 4 COD balance failed by {cod_error:.6g} kg O2/hr.")
    cod_balance = {
        "cod_entering_kg_hr": cod_feed,
        "cod_in_product_kg_hr": cod_product,
        "cod_in_conditioned_liquid_kg_hr": cod_residual,
        "cod_in_dryer_exhaust_kg_hr": cod_exhaust,
        "cod_balance_error_kg_hr": cod_error,
    }

    toc_feed = _toc(phase4_feed_flows)
    toc_product = _toc(product_flows)
    toc_residual = _toc(residual_flows)
    toc_exhaust = _toc(exhaust_flows)
    toc_error = toc_feed - toc_product - toc_residual - toc_exhaust
    if abs(toc_error) > failure_tolerance_kg_hr:
        raise RuntimeError(f"Phase 4 TOC balance failed by {toc_error:.6g} kg C/hr.")
    toc_balance = {
        "toc_entering_kg_hr": toc_feed,
        "toc_in_product_kg_hr": toc_product,
        "toc_in_conditioned_liquid_kg_hr": toc_residual,
        "toc_in_dryer_exhaust_kg_hr": toc_exhaust,
        "toc_balance_error_kg_hr": toc_error,
    }

    if model.scenario.scenario_id != "PR0":
        wet_cake = model.streams["wet_protein_cake"]
        moisture = float(wet_cake.imass["Water"]) / wet_cake.F_mass if wet_cake.F_mass else 0.0
        target = model.parameters["separator"].cake_moisture_fraction
        if abs(moisture - target) > failure_tolerance_kg_hr:
            raise RuntimeError(
                f"Protein-separator cake moisture is {moisture:.6g}, not target {target:.6g}."
            )
        product = model.streams["dry_protein_product"]
        product_moisture = float(product.imass["Water"]) / product.F_mass if product.F_mass else 0.0
        product_target = model.parameters["drying"].target_product_moisture_fraction
        if abs(product_moisture - product_target) > failure_tolerance_kg_hr:
            raise RuntimeError(
                f"Dry product moisture is {product_moisture:.6g}, not target {product_target:.6g}."
            )

    warnings = list(model.warnings)
    for unit in model.units.values():
        warnings.extend(getattr(unit, "warnings", ()))
    if max_component > warning_tolerance_kg_hr:
        warnings.append("Plant component residual exceeds the configured warning tolerance.")
    lines = [
        "GreenHub Phase 4 validation report",
        "==================================",
        f"Scenario: {model.scenario.scenario_id}",
        f"Upstream scenario: {model.input_bundle.phase3_scenario_id}",
        f"Overall inlet mass:  {overall_in:.6g} kg/hr",
        f"Overall outlet mass: {overall_out:.6g} kg/hr",
        f"Overall residual:    {overall_error:.3g} kg/hr",
        f"Maximum component residual: {max_component:.3g} kg/hr",
        f"Maximum element residual:   {max_element:.3g} kg/hr",
        f"Protein residual: {protein_error:.3g} kg/hr",
        f"Nitrogen residual: {nitrogen_error:.3g} kg/hr",
        f"COD residual: {cod_error:.3g} kg O2/hr",
        f"TOC residual: {toc_error:.3g} kg C/hr",
        "",
        "Phase 4 unit balances",
    ]
    lines.extend(
        f"  {item.unit_id}: mass={item.mass_error_kg_hr:.3g}, "
        f"component={item.maximum_component_error_kg_hr:.3g}, "
        f"element={item.maximum_element_error_kg_hr:.3g} kg/hr"
        for item in unit_balances
    )
    if warnings:
        lines.extend(["", "Warnings", *[f"  {item}" for item in dict.fromkeys(warnings)]])
    return Phase4ValidationResult(
        overall_in,
        overall_out,
        overall_error,
        component_errors,
        element_in,
        element_out,
        element_errors,
        protein_balance,
        nitrogen_balance,
        cod_balance,
        toc_balance,
        unit_balances,
        tuple(dict.fromkeys(warnings)),
        "\n".join(lines),
    )
