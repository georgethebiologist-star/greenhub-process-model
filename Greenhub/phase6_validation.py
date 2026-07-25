"""Conservation, gas-quality, and physical-consistency checks for Phase 6."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Mapping

from Greenhub.analytical import calculate_elemental_flows
from Greenhub.chemicals import chemicals
from Greenhub.component_groups import COMPONENT_GROUPS
from Greenhub.phase4_validation import sum_stream_component_flows
from Greenhub.phase6_specifications import DRY_GAS_COMPONENTS

STRICT_ELEMENTS = ("carbon", "hydrogen", "oxygen", "nitrogen", "phosphorus", "sulfur")


@dataclass(frozen=True)
class Phase6UnitBalance:
    """Mass and reaction-adjusted component residuals for one Phase 6 unit."""

    unit_id: str
    inlet_mass_kg_hr: float
    expected_outlet_mass_kg_hr: float
    actual_outlet_mass_kg_hr: float
    mass_error_kg_hr: float
    maximum_component_error_kg_hr: float


@dataclass(frozen=True)
class FeedQualityCheck:
    """One conditioned-gas property and its selected limit."""

    property_name: str
    value: float
    limit_type: str
    limit: float
    passed: bool
    unit: str


@dataclass(frozen=True)
class Phase6ValidationResult:
    """Complete Phase 6 boundary and technology validation result."""

    boundary_in_kg_hr: float
    boundary_out_kg_hr: float
    overall_error_kg_hr: float
    component_errors_kg_hr: dict[str, float]
    element_in_kg_hr: dict[str, float]
    element_out_kg_hr: dict[str, float]
    element_errors_kg_hr: dict[str, float]
    methane_balance_error_kg_hr: float
    unit_balances: tuple[Phase6UnitBalance, ...]
    feed_quality_checks: tuple[FeedQualityCheck, ...]
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


def _validate_unit(unit, tolerance: float) -> Phase6UnitBalance:
    inlet = sum_stream_component_flows(unit.ins)
    expected = _add_delta(inlet, getattr(unit, "reaction_delta_kg_hr", None))
    actual = sum_stream_component_flows(unit.outs)
    errors = {ID: expected[ID] - actual[ID] for ID in chemicals.IDs}
    inlet_mass = sum(inlet.values())
    expected_mass = sum(expected.values())
    actual_mass = sum(actual.values())
    mass_error = expected_mass - actual_mass
    maximum = max((abs(value) for value in errors.values()), default=0.0)
    if abs(mass_error) > tolerance or maximum > tolerance:
        raise RuntimeError(
            f"Phase 6 unit {unit.ID} balance failed: mass={mass_error:.6g}, "
            f"component={maximum:.6g} kg/hr."
        )
    return Phase6UnitBalance(
        unit.ID,
        inlet_mass,
        expected_mass,
        actual_mass,
        mass_error,
        maximum,
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
                f"Phase 6 stream '{stream.ID}' contains negative flows: {negatives}."
            )


def _gas_quality(stream) -> dict[str, float]:
    dry_kmol = sum(float(stream.imol[ID]) for ID in DRY_GAS_COMPONENTS)
    wet_kmol = dry_kmol + float(stream.imol["Water"])
    particulate = sum(
        float(stream.imass[ID])
        for ID in COMPONENT_GROUPS["phase6_particulates"]
    )
    return {
        "temperature_c": stream.T - 273.15,
        "pressure_bar": stream.P / 1e5,
        "water_mol_fraction_wet": float(stream.imol["Water"]) / wet_kmol if wet_kmol else 0.0,
        "h2s_ppmv_dry": float(stream.imol["HydrogenSulfide"]) / dry_kmol * 1e6 if dry_kmol else 0.0,
        "ammonia_ppmv_dry": float(stream.imol["Ammonia"]) / dry_kmol * 1e6 if dry_kmol else 0.0,
        "oxygen_mol_fraction_dry": float(stream.imol["Oxygen"]) / dry_kmol if dry_kmol else 0.0,
        "particulate_kg_hr": particulate,
        "siloxane_kg_hr": float(stream.imass["Siloxanes"]),
        "methane_mol_fraction_dry": float(stream.imol["Methane"]) / dry_kmol if dry_kmol else 0.0,
        "co2_mol_fraction_dry": float(stream.imol["CarbonDioxide"]) / dry_kmol if dry_kmol else 0.0,
    }


def _feed_quality_checks(model) -> tuple[FeedQualityCheck, ...]:
    limits = model.parameters.get("feed_quality_limits")
    if limits is None:
        return ()
    values = _gas_quality(model.streams["conditioned_biogas"])
    definitions = (
        ("temperature_c", "maximum", limits.maximum_temperature_c, "degC"),
        ("pressure_bar", "minimum", limits.minimum_pressure_bar, "bar"),
        ("water_mol_fraction_wet", "maximum", limits.maximum_water_mol_fraction_wet, "mol fraction"),
        ("h2s_ppmv_dry", "maximum", limits.maximum_h2s_ppmv_dry, "ppmv dry"),
        ("ammonia_ppmv_dry", "maximum", limits.maximum_ammonia_ppmv_dry, "ppmv dry"),
        ("oxygen_mol_fraction_dry", "maximum", limits.maximum_oxygen_mol_fraction_dry, "mol fraction dry"),
        ("particulate_kg_hr", "maximum", limits.maximum_particulate_kg_hr, "kg/hr"),
        ("siloxane_kg_hr", "maximum", limits.maximum_siloxane_kg_hr, "kg/hr"),
        ("methane_mol_fraction_dry", "minimum", limits.minimum_methane_mol_fraction_dry, "mol fraction dry"),
    )
    checks = []
    for name, limit_type, limit, unit in definitions:
        value = values[name]
        passed = value <= limit if limit_type == "maximum" else value >= limit
        checks.append(FeedQualityCheck(name, value, limit_type, limit, passed, unit))
    return tuple(checks)


def _validate_technology(model, tolerance: float) -> None:
    scenario_id = model.scenario.scenario_id
    feed = model.streams["conditioned_biogas"]
    product = model.streams["primary_gas_product"]
    reject = model.streams["reject_gas"]
    methane_in = float(feed.imass["Methane"])
    methane_product = float(product.imass["Methane"])
    if methane_product > methane_in + tolerance and not model.parameters.get("has_recycle"):
        raise RuntimeError("Phase 6 product methane exceeds upgrading-feed methane.")
    if scenario_id in {"BG2", "BG3", "BG4", "BG5"}:
        product_dry = _gas_quality(product)
        reject_dry = _gas_quality(reject)
        if reject.F_mass > tolerance and (
            reject_dry["co2_mol_fraction_dry"]
            <= product_dry["co2_mol_fraction_dry"]
        ):
            raise RuntimeError(
                f"{scenario_id} reject gas is not more CO2-rich than its biomethane product."
            )
    if scenario_id == "BG2":
        A611 = model.units["A611"]
        if A611.design_results["Fresh-water makeup"] < -tolerance:
            raise RuntimeError("BG2 fresh-water makeup cannot be negative.")
    elif scenario_id == "BG3":
        for unit_id in ("M621", "M622", "M623"):
            unit = model.units.get(unit_id)
            if unit is not None and not 0.0 <= unit.calculation.stage_cut <= 1.0:
                raise RuntimeError(f"{unit_id} stage cut is outside [0, 1].")
    elif scenario_id == "BG4":
        A631 = model.units["A631"]
        if A631.adsorbent_inventory_kg < -tolerance:
            raise RuntimeError("BG4 adsorbent inventory cannot be negative.")
    elif scenario_id == "BG5":
        A641 = model.units["A641"]
        H641 = model.units["H641"]
        if A641.rich_loading + tolerance < A641.lean_loading:
            raise RuntimeError("BG5 rich loading must exceed lean loading.")
        if H641.reboiler_duty_kw <= 0.0 and float(feed.imass["CarbonDioxide"]) > tolerance:
            raise RuntimeError("BG5 with CO2 capture requires positive regeneration heat.")


def validate_phase6_model(
    model,
    *,
    failure_tolerance_kg_hr: float = 1e-6,
    warning_tolerance_kg_hr: float = 1e-8,
) -> Phase6ValidationResult:
    """Validate Phase 6 mass, components, elements, methane, quality, and trends."""

    if failure_tolerance_kg_hr <= 0.0 or warning_tolerance_kg_hr < 0.0:
        raise ValueError("Phase 6 validation tolerances are invalid.")
    _assert_nonnegative(model.streams.values(), failure_tolerance_kg_hr)
    unit_ids = tuple(dict.fromkeys(model.parameters["phase6_unit_ids"]))
    unit_balances = tuple(
        _validate_unit(model.units[unit_id], failure_tolerance_kg_hr)
        for unit_id in unit_ids
        if unit_id in model.units
    )

    inlet_streams = (model.streams["raw_biogas"], *model.external_inputs)
    inlet = sum_stream_component_flows(inlet_streams)
    expected = dict(inlet)
    for unit_id in unit_ids:
        unit = model.units.get(unit_id)
        delta = getattr(unit, "reaction_delta_kg_hr", None) if unit is not None else None
        if delta:
            expected = _add_delta(expected, delta)
    outlet = sum_stream_component_flows(model.boundary_outputs)
    component_errors = {ID: expected[ID] - outlet[ID] for ID in chemicals.IDs}
    boundary_in = sum(inlet.values())
    boundary_out = sum(outlet.values())
    overall_error = sum(expected.values()) - boundary_out
    maximum_component = max((abs(value) for value in component_errors.values()), default=0.0)
    if abs(overall_error) > failure_tolerance_kg_hr or maximum_component > failure_tolerance_kg_hr:
        raise RuntimeError(
            "Phase 6 boundary component balance failed: "
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
            f"Phase 6 elemental balance failed: {failed_elements} kg/hr."
        )

    methane_in = float(inlet["Methane"])
    methane_out = float(outlet["Methane"])
    methane_error = methane_in - methane_out
    if abs(methane_error) > failure_tolerance_kg_hr:
        raise RuntimeError(
            f"Phase 6 methane balance failed by {methane_error:.6g} kg/hr."
        )
    checks = _feed_quality_checks(model)
    failed_quality = tuple(check for check in checks if not check.passed)
    warnings = list(model.warnings)
    for unit_id in unit_ids:
        unit = model.units.get(unit_id)
        if unit is not None:
            warnings.extend(getattr(unit, "warnings", ()))
    if failed_quality:
        description = "; ".join(
            f"{check.property_name}={check.value:.6g} ({check.limit_type} {check.limit:.6g} {check.unit})"
            for check in failed_quality
        )
        if model.input_bundle.structural_test_mode:
            warnings.append(
                "Conditioned-gas feed-quality warning in structural mode: " + description
            )
        else:
            raise RuntimeError("Conditioned gas is unsuitable for the selected upgrading route: " + description)
    if maximum_component > warning_tolerance_kg_hr:
        warnings.append("Phase 6 component residual exceeds the warning tolerance.")
    _validate_technology(model, failure_tolerance_kg_hr)
    lines = [
        "GreenHub Phase 6 validation report",
        "==================================",
        f"Scenario: {model.scenario.scenario_id} - {model.scenario.name}",
        f"Upstream: {model.input_bundle.phase3_scenario_id}/{model.input_bundle.phase4_scenario_id}/{model.input_bundle.phase5_scenario_id}",
        f"Boundary inlet mass:  {boundary_in:.6g} kg/hr",
        f"Boundary outlet mass: {boundary_out:.6g} kg/hr",
        f"Overall residual:     {overall_error:.3g} kg/hr",
        f"Methane residual:     {methane_error:.3g} kg/hr",
    ]
    lines.extend(
        f"{element.title()} residual: {element_errors[element]:.3g} kg/hr"
        for element in STRICT_ELEMENTS
    )
    lines.append(
        f"Conditioned-feed checks: {len(checks) - len(failed_quality)}/{len(checks)} passed"
    )
    lines.append(
        "PASS: unit and boundary mass, components, CHONPS elements, methane, non-negativity, and technology consistency."
    )
    return Phase6ValidationResult(
        boundary_in,
        boundary_out,
        overall_error,
        component_errors,
        element_in,
        element_out,
        element_errors,
        methane_error,
        unit_balances,
        checks,
        tuple(dict.fromkeys(warnings)),
        "\n".join(lines),
    )
