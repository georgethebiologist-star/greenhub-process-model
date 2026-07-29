"""Convert a simulated integrated model into JSON-safe result contracts."""

from __future__ import annotations

from math import isfinite

from Greenhub.parameters.enums import CandidateKind, ResultStatus
from Greenhub.parameters.serialization import to_json_compatible

from .contracts import ValidationIssue
from .contracts.results import (
    BalanceResult,
    NumericalValue,
    ParameterResolutionResult,
    ProcessAreaResult,
    ProductResult,
    StreamResult,
    UnitResult,
    UtilityResult,
    ValidationSummary,
)


def numerical(value, unit, basis, origin, status=ResultStatus.CALCULATED, warning=None):
    numeric = float(value) if value is not None else None
    if numeric is not None and not isfinite(numeric):
        return NumericalValue(None, unit, basis, ResultStatus.MISSING, origin, "Non-finite source value was not serialized.")
    return NumericalValue(numeric, unit, basis, status, origin, warning)


def build_stream_results(model) -> tuple[StreamResult, ...]:
    grouped = {}
    for alias, stream in model.streams.items():
        grouped.setdefault(id(stream), {"stream": stream, "aliases": []})["aliases"].append(alias)
    results = []
    for item in sorted(grouped.values(), key=lambda row: str(row["stream"].ID)):
        stream = item["stream"]
        components = {
            component: numerical(
                float(stream.imass[component]), "kg/hr", "component mass flow", "BioSTEAM stream"
            )
            for component in stream.chemicals.IDs
            if float(stream.imass[component]) != 0.0
        }
        source = getattr(stream, "source", None)
        sink = getattr(stream, "sink", None)
        results.append(
            StreamResult(
                stream_id=str(stream.ID),
                aliases=tuple(sorted(item["aliases"])),
                total_mass=numerical(stream.F_mass, "kg/hr", "stream total", "BioSTEAM stream"),
                temperature=numerical(stream.T, "K", "absolute temperature", "BioSTEAM stream"),
                pressure=numerical(stream.P, "Pa", "absolute pressure", "BioSTEAM stream"),
                phase=str(stream.phase),
                components=components,
                source_unit=str(source.ID) if source is not None else None,
                sink_unit=str(sink.ID) if sink is not None else None,
            )
        )
    return tuple(results)


def build_unit_results(model) -> tuple[UnitResult, ...]:
    area_by_unit = {
        unit_id: area_id
        for area_id, area in model.process_areas.items()
        for unit_id in area.units
    }
    results = []
    for unit_id, unit in sorted(model.units.items()):
        units = getattr(unit, "_units", {})
        design = {}
        for key, value in getattr(unit, "design_results", {}).items():
            try:
                design[key] = numerical(value, units.get(key), "unit design result", f"{unit_id} design")
            except (TypeError, ValueError):
                continue
        heat = tuple(
            numerical(item.duty, "kJ/hr", "heat utility duty", f"{unit_id} heat utility")
            for item in getattr(unit, "heat_utilities", ())
        )
        results.append(
            UnitResult(
                unit_id=unit_id,
                display_name=str(getattr(unit, "line", None) or type(unit).__name__),
                process_area=area_by_unit.get(unit_id, "unassigned"),
                design_results=design,
                power=numerical(
                    getattr(unit.power_utility, "consumption", 0.0),
                    "kW", "instantaneous demand", f"{unit_id} power utility",
                ),
                heat_duties=heat,
                warnings=tuple(getattr(unit, "warnings", ())),
            )
        )
    return tuple(results)


def build_process_areas(model, calculation_mode: str) -> tuple[ProcessAreaResult, ...]:
    results = []
    for area_id, area in model.process_areas.items():
        try:
            metrics = to_json_compatible(dict(area.metrics))
        except (TypeError, ValueError):
            metrics = {}
        maturity = "D4" if area_id == "protein_recovery" and calculation_mode == "literature_default" else "structural"
        results.append(
            ProcessAreaResult(
                process_area_id=area_id,
                display_name=area.name,
                unit_ids=tuple(sorted(area.units)),
                inlet_stream_ids=tuple(sorted({str(item.ID) for item in area.inlet_streams.values()})),
                outlet_stream_ids=tuple(sorted({str(item.ID) for item in area.outlet_streams.values()})),
                metrics=metrics,
                model_maturity=maturity,
                warnings=tuple(area.warnings),
            )
        )
    return tuple(results)


def build_balances(model) -> tuple[BalanceResult, ...]:
    validation = model.validation_report
    if validation is None:
        return ()
    balances = [
        BalanceResult(
            "overall_mass",
            "integrated_system",
            numerical(validation.boundary_in_kg_hr, "kg/hr", "boundary inlet", "Phase 7 validation"),
            numerical(validation.boundary_out_kg_hr, "kg/hr", "boundary outlet", "Phase 7 validation"),
            numerical(validation.overall_error_kg_hr, "kg/hr", "inlet minus outlet", "Phase 7 validation"),
            abs(validation.overall_error_kg_hr) <= 1e-6,
        )
    ]
    for element, residual in validation.element_errors_kg_hr.items():
        balances.append(
            BalanceResult(
                f"element_{element}",
                "integrated_system",
                numerical(validation.element_in_kg_hr[element], "kg/hr", element, "Phase 7 validation"),
                numerical(validation.element_out_kg_hr[element], "kg/hr", element, "Phase 7 validation"),
                numerical(residual, "kg/hr", "inlet minus outlet", "Phase 7 validation"),
                abs(residual) <= 1e-6,
            )
        )
    return tuple(balances)


def build_utilities(units: tuple[UnitResult, ...]) -> tuple[UtilityResult, ...]:
    results = []
    for unit in units:
        results.append(UtilityResult(f"{unit.unit_id}:electricity", unit.unit_id, "electricity", unit.power))
        for index, duty in enumerate(unit.heat_duties, start=1):
            results.append(UtilityResult(f"{unit.unit_id}:heat:{index}", unit.unit_id, "heat", duty))
    return tuple(results)


def build_products(model) -> tuple[ProductResult, ...]:
    names = (
        "dry_protein_product", "biomethane", "phosphorus_product",
        "ammonium_product", "potassium_concentrate", "nutrient_rich_solids",
    )
    return tuple(
        ProductResult(
            name,
            str(model.streams[name].ID),
            numerical(model.streams[name].F_mass, "kg/hr", "wet stream", "BioSTEAM stream"),
            "candidate_product_not_regulatory_qualified",
        )
        for name in names
        if name in model.streams
    )


def build_parameter_results(resolved) -> tuple[ParameterResolutionResult, ...]:
    results = []
    for item in resolved:
        selected = item.selected_candidate
        if item.blocked:
            status = ResultStatus.BLOCKED
        elif selected and selected.source_kind in {CandidateKind.RUN_OVERRIDE, CandidateKind.PROJECT_OVERRIDE}:
            status = ResultStatus.OVERRIDDEN
        elif selected and selected.source_kind == CandidateKind.LITERATURE_DEFAULT:
            status = ResultStatus.LITERATURE_DEFAULT
        elif selected and selected.source_kind == CandidateKind.MEASURED_PROJECT:
            status = ResultStatus.MEASURED
        elif selected and selected.source_kind == CandidateKind.CALIBRATED_PROJECT:
            status = ResultStatus.CALIBRATED
        else:
            status = ResultStatus.PLACEHOLDER
        results.append(
            ParameterResolutionResult(
                item.parameter_id,
                item.active_value,
                item.unit,
                status,
                item.source,
                item.selection_reason,
                item.warnings,
            )
        )
    return tuple(results)


def build_validation(model, balances) -> ValidationSummary:
    issues = tuple(
        ValidationIssue(
            code="BALANCE_FAILED",
            severity="error",
            message=f"Balance '{item.balance_id}' exceeds tolerance.",
            blocking=True,
            process_area=item.process_area,
            object_id=item.balance_id,
        )
        for item in balances
        if not item.passed
    )
    warning_count = len(model.warnings)
    return ValidationSummary(not issues, len(issues), warning_count, issues)
