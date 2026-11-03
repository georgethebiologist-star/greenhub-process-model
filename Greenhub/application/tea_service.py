"""Post-route screening TEA for empirical and dynamic GreenHub results.

This module is deliberately downstream of process formation.  It only reads
formed routes and result quantities; it never changes chemistry, yields,
utilities, scenario IDs, or model overrides.
"""

from __future__ import annotations

from collections import Counter, defaultdict
import csv
from dataclasses import asdict, dataclass, field, is_dataclass
from math import isfinite
from pathlib import Path
import re
from typing import Any, Iterable, Mapping, Sequence

from Greenhub.tea_costs import TEACostRecord, load_tea_cost_register
from Greenhub.tea_finance import (
    TEAFinancialAssumptions,
    TEAProductPrice,
    calculate_screening_financials,
    normalize_product_prices,
)
from Greenhub.time_grid import generate_time_grid


@dataclass(frozen=True)
class TEAProjectBasis:
    """Explicit project assumptions that may supplement simulation outputs."""

    staffing_people: int = 5
    paid_hours_per_person: float = 1500.0
    screening_estimates: bool = False
    operating_hours_per_year: float | None = None
    operating_days_per_year: float | None = None
    operating_hours_per_day: float | None = None
    annual_throughput_kg: float | None = None
    capacities: Mapping[str, object] = field(default_factory=dict)
    annual_quantities: Mapping[str, object] = field(default_factory=dict)
    installed_factors: Mapping[str, float] = field(default_factory=dict)
    include_cost_ids: tuple[str, ...] = ()
    exclude_cost_ids: tuple[str, ...] = ()
    explicit_route_tags: tuple[str, ...] = ()
    notes: str = ""
    currency: str = "EUR"
    price_year: int | None = None
    location: str = "Netherlands"
    cost_boundary_complete: bool = False
    price_basis_confirmed: bool = False
    boundary_exclusions: tuple[str, ...] = ()
    product_quality: Mapping[str, Mapping[str, object]] = field(default_factory=dict)
    cost_multipliers: Mapping[str, float] = field(default_factory=dict)
    capacity_ranges: Mapping[str, object] = field(default_factory=dict)
    allow_capacity_extrapolation: bool = False

    def __post_init__(self) -> None:
        if type(self.staffing_people) is not int or self.staffing_people < 0:
            raise ValueError("staffing_people must be a non-negative integer.")
        if not isfinite(self.paid_hours_per_person) or self.paid_hours_per_person < 0:
            raise ValueError("paid_hours_per_person must be finite and non-negative.")
        for name, value in (
            ("operating_hours_per_year", self.operating_hours_per_year),
            ("operating_days_per_year", self.operating_days_per_year),
            ("operating_hours_per_day", self.operating_hours_per_day),
            ("annual_throughput_kg", self.annual_throughput_kg),
        ):
            if value is not None and (not isfinite(float(value)) or float(value) < 0):
                raise ValueError(f"{name} must be a finite non-negative value or null.")
        if self.operating_hours_per_day is not None and self.operating_hours_per_day > 24:
            raise ValueError("operating_hours_per_day cannot exceed 24.")
        if self.operating_hours_per_year is not None and self.operating_hours_per_year > 8784:
            raise ValueError("operating_hours_per_year cannot exceed a leap year (8784 h).")
        if self.operating_days_per_year is not None and self.operating_days_per_year > 366:
            raise ValueError("operating_days_per_year cannot exceed 366.")
        if all(value is not None for value in (self.operating_hours_per_year, self.operating_days_per_year, self.operating_hours_per_day)) and abs(self.operating_hours_per_year - self.operating_days_per_year * self.operating_hours_per_day) > 1e-6:
            raise ValueError("Operating hours/year must equal operating days/year times hours/day.")
        if self.currency != "EUR":
            raise ValueError("The cost register is in EUR; explicitly convert source costs before using another currency.")
        if self.price_year is not None and (type(self.price_year) is not int or not 1900 <= self.price_year <= 2200):
            raise ValueError("price_year must be an integer within [1900, 2200] or null.")
        if self.price_basis_confirmed and self.price_year is None:
            raise ValueError("price_basis_confirmed requires price_year.")
        if (self.cost_boundary_complete or self.price_basis_confirmed) and not self.notes.strip():
            raise ValueError("A boundary/price-basis completeness declaration requires explanatory notes.")
        for name, mapping in (("capacities", self.capacities), ("annual_quantities", self.annual_quantities)):
            for key, raw in mapping.items():
                _quantity_value(raw, None)
        for cost_id, factor in self.installed_factors.items():
            if not isfinite(float(factor)) or float(factor) <= 0:
                raise ValueError(f"Installed factor for {cost_id} must be finite and positive.")
        for cost_id, factor in self.cost_multipliers.items():
            if not isfinite(float(factor)) or float(factor) <= 0:
                raise ValueError(f"Cost multiplier for {cost_id} must be finite and positive.")

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True)
class TEAReport:
    route_summary: dict[str, object]
    selected_cost_lines: tuple[dict[str, object], ...]
    excluded_alternatives: tuple[dict[str, object], ...]
    capex_lines: tuple[dict[str, object], ...]
    opex_lines: tuple[dict[str, object], ...]
    revenue_lines: tuple[dict[str, object], ...]
    missing_inputs: tuple[dict[str, object], ...]
    warnings: tuple[str, ...]
    totals: dict[str, object]
    financial_assumptions: dict[str, object]
    financial_kpis: dict[str, object]
    cash_flow: tuple[dict[str, object], ...]
    replacement_schedule: tuple[dict[str, object], ...]
    confidence_summary: dict[str, int]
    source_traceability: tuple[dict[str, object], ...]
    project_basis: dict[str, object] = field(default_factory=dict)
    project_assumption_traceability: tuple[dict[str, object], ...] = ()
    schema_version: str = "greenhub-tea-post-route-2.1"

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


def _project_assumption_traceability(basis):
    for field_name, mapping, unit in (
        ('capacities', basis.capacities, 'explicit record unit'),
        ('annual_quantities', basis.annual_quantities, 'explicit record unit'),
        ('installed_factors', basis.installed_factors, 'dimensionless'),
        ('cost_multipliers', basis.cost_multipliers, 'dimensionless'),
    ):
        for key, value in mapping.items():
            yield {'policy_id':f'tea.project.{field_name}.{key}','value':value,'unit':unit,
                   'source_status':'explicit_user_assumption','basis':field_name,'geography':basis.location,
                   'reference_year':basis.price_year,'source_url':'','source_table_or_page':'',
                   'retrieval_date':None,'evidence_class':'explicit_user_assumption',
                   'applicability':basis.notes or 'This project only; not validated.',
                   'conversion_method':'explicit project input','uncertainty':'unquantified',
                   'warning':'User input does not establish sourced accuracy or project completeness.'}


def calculate_empirical_tea(
    simulation_result: object,
    selected_routes: Sequence[str] | None = None,
    project_basis: TEAProjectBasis | Mapping[str, object] | None = None,
    *,
    cost_records: Sequence[TEACostRecord] | None = None,
    financial_assumptions: TEAFinancialAssumptions | Mapping[str, object] | None = None,
    logistics_result: object | None = None,
) -> TEAReport:
    """Calculate screening TEA after an empirical simulation has completed."""

    if simulation_result is None or not hasattr(simulation_result, "selected_scenarios"):
        raise TypeError("calculate_empirical_tea requires a completed SimulationResult.")
    status = str(getattr(simulation_result, "status", ""))
    if status and status != "completed":
        raise ValueError("Empirical TEA requires a completed simulation result.")
    basis = _coerce_project_basis(project_basis)
    finance = _coerce_financial_assumptions(financial_assumptions)
    route = _empirical_route(simulation_result, selected_routes, basis)
    if logistics_result is not None:
        # Explicit logistics evidence activates the matching transport cost
        # record without changing the formed process route or default TEA.
        route["explicit_route_tags"] = tuple(route.get("explicit_route_tags", ())) + ("feedstock_logistics",)
    measures = _empirical_measures(simulation_result, basis, logistics_result=logistics_result)
    records = tuple(cost_records) if cost_records is not None else load_tea_cost_register()
    if basis.screening_estimates:
        from .tea_screening import prepare_screening_basis
        basis, records = prepare_screening_basis(basis, records, measures, simulation_result)
        route = _empirical_route(simulation_result, selected_routes, basis)
        if logistics_result is not None:
            route["explicit_route_tags"] = tuple(route.get("explicit_route_tags", ())) + ("feedstock_logistics",)
    return _calculate_post_route_tea("empirical", route, measures, basis, finance, records)


def calculate_dynamic_tea(
    dynamic_result: object,
    selected_routes: Sequence[str] | None = None,
    project_basis: TEAProjectBasis | Mapping[str, object] | None = None,
    *,
    cost_records: Sequence[TEACostRecord] | None = None,
    financial_assumptions: TEAFinancialAssumptions | Mapping[str, object] | None = None,
) -> TEAReport:
    """Aggregate screening TEA from explicit dynamic steps or annual reporting.

    Missing time-step quantities are not interpolated.  A line that cannot be
    tied to an actual annual total is returned as ``missing_dynamic_quantity``.
    """

    if dynamic_result is None:
        raise TypeError("calculate_dynamic_tea requires a dynamic result or annual report.")
    basis = _coerce_project_basis(project_basis)
    finance = _coerce_financial_assumptions(financial_assumptions)
    route = _dynamic_route(dynamic_result, selected_routes, basis)
    measures = _dynamic_measures(dynamic_result, basis)
    return _calculate_post_route_tea(
        "dynamic", route, measures, basis, finance,
        tuple(cost_records) if cost_records is not None else load_tea_cost_register(),
    )


def _calculate_post_route_tea(
    model_type: str,
    route: dict[str, object],
    measures: dict[str, object],
    basis: TEAProjectBasis,
    finance: TEAFinancialAssumptions,
    records: tuple[TEACostRecord, ...],
) -> TEAReport:
    selected, excluded, selection_warnings = _select_records(records, route, basis)
    capex_lines: list[dict[str, object]] = []
    opex_lines: list[dict[str, object]] = []
    revenue_lines: list[dict[str, object]] = []
    missing: list[dict[str, object]] = []
    warnings = list(selection_warnings)
    warnings.extend(str(item) for item in measures.get("quantity_warnings", ()))
    warnings.extend([
        "Legacy cost-register sources retain their original evidence and unharmonized price years; project-year normalization must be declared explicitly.",
        "Product quality and marketability are not validated by the process model. Screening prices are hypotheses, not offtake contracts.",
    ])

    # Indirect cost bases are evaluated only after all equipment lines exist.
    for record in sorted(selected, key=lambda item: {"capex": 0, "indirect": 1, "maintenance": 3}.get(item.cost_type, 2)):
        if record.cost_type == "capex":
            line, issues = _calculate_capex(record, measures, basis, model_type)
            capex_lines.append(line)
        elif record.cost_type == "indirect":
            line, issues = _calculate_indirect(record, capex_lines, basis, model_type)
            capex_lines.append(line)
        elif record.cost_type == "revenue":
            line, issues = _calculate_annual_line(record, measures, basis, model_type, revenue=True)
            revenue_lines.append(line)
        else:
            if basis.screening_estimates and record.cost_id == 'TEA-030' and _explicit_quantity(record, basis) is None:
                capital = sum(float(item.get('installed_cost_eur') or item.get('direct_cost_eur') or 0) for item in capex_lines)
                line = _line_base(record)
                line.update(annual_cost_eur=capital * float(record.rate_value), quantity=capital,
                            quantity_unit='EUR screening capital', unit_cost_eur=record.rate_value,
                            calculation_status='screening_maintenance_allowance',
                            warning='2% of known screening capital; incomplete capital understates maintenance. Mechanical wear excluded to avoid overlap.')
                issues = []
            else:
                line, issues = _calculate_annual_line(record, measures, basis, model_type, revenue=False)
            opex_lines.append(line)
        missing.extend(issues)

    cip_screen = measures.get("pr7_cip_reagent_screen")
    if measures.get("pr7_route_selected") and cip_screen:
        opex_lines.append({
            "cost_id": "PR7-CIP-REAGENTS",
            "process_area": "protein_recovery",
            "cost_type": "opex",
            "description": "PR7 NaOH and citric-acid CIP make-up chemicals",
            "annual_cost_eur": float(cip_screen["total_reagent_cost_eur_year"]),
            "quantity": float(cip_screen["solution_mass_replaced_kg_year_per_step"]),
            "quantity_unit": "kg/year per cleaning step",
            "unit_cost_eur": None,
            "calculation_status": "partial_user_input_screening",
            "source_status": "indicative_prices_and_explicit_user_activity_inputs",
            "input_source": cip_screen["input_source"],
            "cost_boundary": cip_screen["cost_boundary"],
            "warning": "Chemical make-up subtotal only; excludes CIP water, heating, labor, downtime, wastewater, and cleaning-loop recovery.",
        })

    if measures.get("pr7_route_selected"):
        module_screen = measures.get("pr7_membrane_module_screen")
        if isinstance(module_screen, Mapping):
            replacement_high = _number(module_screen.get("module_replacement_high_EUR_year"))
            replacement_low = _number(module_screen.get("module_replacement_low_EUR_year"))
            if replacement_high is not None:
                opex_lines.append({
                    "cost_id": "PR7-MEMBRANE-REPLACEMENT-SCREEN",
                    "process_area": "protein_recovery",
                    "cost_type": "opex",
                    "description": "PR7 membrane-module replacement allowance (upper-bound screen)",
                    "annual_cost_eur": replacement_high,
                    "quantity": _number(module_screen.get("area_m2")),
                    "quantity_unit": "m2 full resolved membrane area",
                    "unit_cost_eur": None,
                    "calculation_status": "partial_user_input_screening_upper_bound",
                    "source_status": "user_supplied_module_price_and_lifetime_ranges",
                    "input_source": "biostimulant_membrane_options.csv; biostimulant_membrane_gated_parameters.csv",
                    "cost_boundary": "membrane-module purchase replacement only; excludes installation, removal, labor, downtime, disposal, and working capital",
                    "range_low_eur_year": replacement_low,
                    "range_high_eur_year": replacement_high,
                    "selection_basis": "upper annualized bound: high module purchase price divided by 2.5-year low lifetime; no probability distribution is assumed",
                    "warning": "Included in annual OPEX only when the full PR7 membrane area is resolved; installation and replacement event financing remain incomplete.",
                })

    if measures.get("pr7_route_selected"):
        module_range = measures.get("pr7_membrane_module_screen_range")
        module_screen = measures.get("pr7_membrane_module_screen")
        module_cost_basis = module_screen or (
            module_range.get("minimum_area_cost_screen") if isinstance(module_range, Mapping) else None
        )
        if isinstance(module_cost_basis, Mapping):
            capex_lines.append({
                "cost_id": "PR7-MODULE-CAPEX-SCREEN",
                "process_area": "protein_recovery",
                "cost_type": "capex",
                "equipment_or_cost_item": "PR7 membrane module purchase (uninstalled screening range)",
                "direct_cost_eur": None,
                "installed_cost_eur": None,
                "direct_cost_range_low_eur": float(module_cost_basis["module_capex_low_EUR"]),
                "direct_cost_range_high_eur": float(module_cost_basis["module_capex_high_EUR"]),
                "project_capacity": module_cost_basis.get("area_m2"),
                "reference_capacity": 1.0,
                "project_capacity_unit": "m² membrane area",
                "capacity_unit": "m² membrane area",
                "calculation_status": "partial_user_input_screening_range",
                "source_status": "user_supplied_unverified_quote_range_converted_to_EUR",
                "input_source": "biostimulant_membrane_options.csv; biostimulant_membrane_gated_parameters.csv",
                "cost_boundary": "membrane module media only; excludes pressure vessel/skid, piping, pumps, instrumentation, installation, commissioning, and indirects",
                "area_basis": (
                    "full simulated membrane area"
                    if module_screen else "known-stream minimum area floor; unresolved component fate prevents a full-area estimate"
                ),
                "warning": "Range is disclosed as module purchase only and is excluded from direct and installed CAPEX totals until the full project boundary and installation basis are established.",
            })

    price_lines, price_missing, revenue_status, price_traceability = _product_price_lines(
        measures, basis, finance, revenue_lines, model_type=model_type
    )
    revenue_lines.extend(price_lines)
    missing.extend(price_missing)

    direct_values = [
        float(line["direct_cost_eur"])
        for line in capex_lines
        if line["cost_type"] == "capex" and line.get("direct_cost_eur") is not None
    ]
    installed_values = [
        float(line["installed_cost_eur"])
        for line in capex_lines
        if line.get("installed_cost_eur") is not None
    ]
    selected_direct = [line for line in capex_lines if line["cost_type"] == "capex"]
    installed_complete = bool(selected_direct) and all(
        line.get("installed_cost_eur") is not None for line in capex_lines
    )
    annual_opex = sum(float(line["annual_cost_eur"]) for line in opex_lines if line.get("annual_cost_eur") is not None)
    annual_revenue = sum(float(line["annual_revenue_eur"]) for line in revenue_lines if line.get("annual_revenue_eur") is not None)
    if revenue_status != "complete":
        warnings.append(
            "Annual revenue is incomplete because one or more selected saleable products lack a traceable price or compatible annual quantity."
        )
    if missing:
        warnings.append("Screening totals are partial because one or more selected cost lines lack required simulation or project-basis inputs.")
    capex_ids = {str(line["cost_id"]) for line in capex_lines}
    opex_ids = {str(line["cost_id"]) for line in opex_lines}
    capex_complete = installed_complete and not any(
        str(item.get("cost_id")) in capex_ids for item in missing
    )
    opex_complete = not any(str(item.get("cost_id")) in opex_ids for item in missing)
    selected_capex_complete, selected_opex_complete = capex_complete, opex_complete
    if not basis.cost_boundary_complete:
        missing.append({"cost_id": "PROJECT-BOUNDARY", "code": "unconfirmed_cost_boundary", "required_input": "Review equipment, installation, indirects, replacements, utilities, consumables, labor, maintenance, logistics and disposal; declare included boundary and exclusions."})
    if not basis.price_basis_confirmed:
        missing.append({"cost_id": "PROJECT-PRICE-BASIS", "code": "unconfirmed_price_basis", "required_input": "Confirm common EUR price year and location, with explicit cost_multipliers where conversion/escalation is necessary."})
    if measures.get("pr7_route_selected"):
        capex_complete = False
        opex_complete = False
        pr7_missing = [
            {"cost_id": "PR7-MODULE-CAPEX", "code": "missing_installed_skid_basis", "required_input": "Installed membrane skid and installation basis; the uninstalled module-only EUR range is displayed as a separate partial CAPEX line and excluded from installed CAPEX totals."},
            {"cost_id": "PR7-MODULE-REPLACEMENT", "code": "missing_replacement_disposal_basis", "required_input": "Disposal and replacement labor/downtime costs; only the membrane-module purchase allowance is estimated in EUR from the 2.5–3.0 year user-supplied life."},
            *(
                [{"cost_id": "PR7-CROSSFLOW", "code": "missing_crossflow_energy", "required_input": "Measured or sourced crossflow recirculation electricity in kWh/m³ clarified feed, excluding any separately modeled permeate-side pressure work."}]
                if not measures.get("pr7_crossflow_electricity_supplied") else []
            ),
            {"cost_id": "PR7-AUXILIARY-ENERGY", "code": "missing_other_auxiliary_energy", "required_input": "Controls, instrumentation, cleaning, and other auxiliary energy beyond the separately reported permeate-side pressure work and crossflow recirculation electricity."},
            {"cost_id": "PR7-PRODUCT-SPEC", "code": "missing_product_basis", "required_input": "Confirm retentate specification, actual annual sale volume and market/offtake basis. A user-supplied €1.50–3.50/L price may be explicitly screened against simulated retentate volume, but it is not validated revenue."},
        ]
        if (
            float(measures.get("annual_pr7_unresolved_mass_kg") or 0.0) > 1e-12
            or float(measures.get("pr7_unresolved_mass_kg_hr") or 0.0) > 1e-12
        ):
            component_ids = ", ".join(measures.get("pr7_unresolved_component_ids", ()))
            pr7_missing.append({
                "cost_id": "PR7-UNMAPPED-RETENTION",
                "code": "unresolved_membrane_component_fate",
                "required_input": (
                    f"Provide documented retention values and source notes for the unresolved component pools ({component_ids}). "
                    "Their mass is conserved at a separate outlet; retentate revenue, permeate downstream yield, and membrane area are partial."
                ),
            })
            revenue_status = "incomplete_unresolved_retention"
            warnings.append("PR7 sales are a partial lower-bound screen because unresolved membrane pools are excluded from retentate product volume and value.")
        if not cip_screen:
            pr7_missing.append({"cost_id": "PR7-CIP", "code": "missing_cip_activity_basis", "required_input": "CIP solution volume per step and make-up fraction per cycle, each with an evidence note. The 48 operating-hour interval and indicative EUR reagent prices are registered; validate cleaning demand and procurement grade for grass juice."})
        else:
            pr7_missing.append({"cost_id": "PR7-CIP-REMAINDER", "code": "incomplete_cip_boundary", "required_input": "CIP wastewater fate, downtime/labor, water, and energy. A PR7-CIP-REAGENTS line reports the explicit annual EUR make-up-chemical subtotal only."})
        target_vcf = _number(measures.get("pr7_target_concentration_factor"))
        actual_vcf = _number(measures.get("pr7_actual_volume_concentration_factor"))
        if target_vcf and actual_vcf and abs(actual_vcf - target_vcf) / target_vcf > 0.05:
            pr7_missing.append({
                "cost_id": "PR7-VCF-MISMATCH",
                "code": "target_actual_vcf_mismatch",
                "required_input": f"Actual model VCF {actual_vcf:.4g} differs from target VCF {target_vcf:.4g} by more than 5%; confirm final sale-volume and price basis.",
            })
        if not measures.get("pr7_pressure_work_supplied"):
            pr7_missing.append({"cost_id": "PR7-PRESSURE-WORK", "code": "missing_pressure_work_inputs", "required_input": "Sourced transmembrane pressure and pump efficiency for the idealized permeate-side electricity estimate."})
        if measures.get("pr7_membrane_technology") == "MEUF":
            meuf = measures.get("pr7_meuf_surfactant_screen")
            pr7_missing.append({"cost_id": "PR7-MEUF-SURFACTANT", "code": "incomplete_surfactant_cost_basis", "required_input": "SDS gross dose and unrecovered make-up are screened from the user-supplied dose/recovery basis when annual clarified-juice flow is available. Industrial-grade SDS price, acid identity/stoichiometry, recovery energy, replacement inventory, residual limit and disposal remain required; the €230/kg lab-grade listing is reference-only and excluded." if meuf else "MEUF SDS dose is not annualized because a steady-state clarified-juice flow and operating-hour basis are unavailable; price, acid identity/stoichiometry, recovery energy, residual limit and disposal remain required."})
        missing.extend(pr7_missing)
        selected_capex_complete = False
        selected_opex_complete = False
        if measures.get("pr7_membrane_module_screen"):
            warnings.append("PR7 membrane-module purchase remains excluded from installed CAPEX; the conservative annualized replacement upper bound is included in OPEX because full membrane area is resolved.")
        else:
            warnings.append("PR7 membrane module and replacement are not included in annual OPEX because only a known-stream area floor is available; unresolved feed-pool fate prevents a full-area estimate.")
        warnings.append("PR7 full-route TEA remains partial because CIP, crossflow auxiliaries, installed-module/skid CAPEX, replacement event financing and disposal, and product-basis inputs are incomplete.")
    capex_complete = capex_complete and basis.cost_boundary_complete and basis.price_basis_confirmed
    opex_complete = opex_complete and basis.cost_boundary_complete and basis.price_basis_confirmed
    replacement_schedule = _replacement_schedule(selected, capex_lines, finance)
    financial_kpis, cash_flow, financial_warnings = calculate_screening_financials(
        installed_capex_eur=sum(installed_values) if installed_complete else None,
        annual_opex_eur=annual_opex,
        annual_revenue_eur=annual_revenue,
        annual_feed_kg=_number(measures.get("annual_throughput_kg")),
        annual_protein_product_kg=_annual_protein_product_kg(measures),
        annual_biomethane_nm3=_annual_biomethane_nm3(measures),
        assumptions=finance,
        replacement_events=replacement_schedule,
        capex_complete=capex_complete,
        opex_complete=opex_complete,
        revenue_complete=revenue_status == "complete",
    )
    if basis.screening_estimates:
        warnings.append("Screening estimate: missing installation costs are excluded, not zero or verified installed costs; reference package and capacity assumptions are shown per line.")
    warnings.extend(financial_warnings)
    volume = measures.get('annual_products_m3', {}).get('biomethane')
    financial_kpis['cost_per_m3_biomethane_eur'] = annual_opex / volume if volume else None
    financial_kpis['gas_volume_basis_warning'] = 'Process m3 is not Nm3. Standard temperature, pressure and dry/wet basis are required for normalization.'
    totals = {
        "total_direct_capex_eur": sum(direct_values),
        "partial_direct_capex_eur": sum(direct_values),
        "partial_installed_capex_eur": sum(installed_values),
        "total_installed_capex_eur": sum(installed_values) if installed_complete and not any(line.get("calculation_status") in {"direct_cost_installation_excluded", "unscaled_reference_package_assumption"} for line in capex_lines) else None,
        "annual_opex_eur": annual_opex,
        "screening_estimates": basis.screening_estimates,
        "screening_capital_basis_eur": sum(installed_values) if basis.screening_estimates else None,
        "screening_operating_balance_eur_per_year": annual_revenue - annual_opex if basis.screening_estimates else None,
        "annual_revenue_eur": annual_revenue,
        "annual_gross_profit_eur": financial_kpis["annual_gross_profit_eur"],
        "net_operating_margin_eur_per_year": financial_kpis["net_operating_margin_eur_per_year"],
        "ebitda_like_operating_cash_flow_eur_per_year": financial_kpis["ebitda_like_operating_cash_flow_eur_per_year"],
        "partial_operating_margin_eur_per_year": annual_revenue - annual_opex,
        "capex_status": "complete_screening" if capex_complete else "partial",
        "opex_status": "complete_screening" if opex_complete else "partial",
        "profit_status": financial_kpis["profit_status"],
        "selected_capex_lines_complete": selected_capex_complete,
        "selected_opex_lines_complete": selected_opex_complete,
        "revenue_status": revenue_status,
        "totals_complete": not missing and capex_complete and opex_complete and revenue_status == "complete",
    }
    traceability = tuple(
        {
            "cost_id": record.cost_id,
            "source_title": record.source_title,
            "source_url": record.source_url,
            "confidence": record.confidence,
            "source_status": record.source_status,
            "source_sheet": record.source_sheet,
            "source_row": record.source_row,
            "value": record.reference_value_eur if record.reference_value_eur is not None else record.annual_unit_cost_eur,
            "unit": record.reference_unit,
            "basis": record.cost_boundary_includes,
            "geography": "source-specific; see source and notes",
            "reference_year": None,
            "retrieval_date": None,
            "evidence_class": record.source_status or "unspecified",
            "applicability": record.notes,
            "conversion_method": "Preserved compact-register EUR conversion; source year not independently normalized.",
            "uncertainty": record.confidence or "unquantified",
        }
        for record in selected
    ) + tuple(price_traceability)
    pr7_module_range = measures.get("pr7_membrane_module_screen_range")
    pr7_module = measures.get("pr7_membrane_module_screen") or (
        pr7_module_range.get("minimum_area_cost_screen")
        if pr7_module_range else None
    )
    if pr7_module:
        traceability += (
            {
                "cost_id": "PR7-MODULE-CAPEX-SCREEN",
                "source_title": "User-supplied PR7 membrane module price range",
                "source_url": pr7_module["fx_source"],
                "confidence": "user_supplied_unverified",
                "source_status": "user_supplied_unverified",
                "source_sheet": "biostimulant_membrane_options.csv",
                "source_row": None,
                "value": [pr7_module["module_capex_low_EUR"], pr7_module["module_capex_high_EUR"]],
                "unit": "EUR/module at simulated area",
                "basis": (
                    "known-stream permeate area floor only"
                    if not measures.get("pr7_membrane_module_screen")
                    else "module membrane area only"
                ),
                "geography": "not specified in supplied quote range",
                "reference_year": None,
                "retrieval_date": pr7_module["fx_date"],
                "evidence_class": "user-supplied quote converted using official FX reference rate",
                "applicability": pr7_module["cost_boundary"],
                "conversion_method": f"simulated area × supplied USD/m² range × {pr7_module['fx_eur_per_usd']} EUR/USD; ECB rate dated {pr7_module['fx_date']}",
                "source_value_usd": [
                    pr7_module.get(
                        "source_module_capex_low_USD",
                        pr7_module["module_capex_low_EUR"] / pr7_module["fx_eur_per_usd"],
                    ),
                    pr7_module.get(
                        "source_module_capex_high_USD",
                        pr7_module["module_capex_high_EUR"] / pr7_module["fx_eur_per_usd"],
                    ),
                ],
                "fx_source": pr7_module["fx_source"],
                "uncertainty": (
                    "known-stream area floor; unresolved pool fate prevents an upper area estimate; user-supplied price range and original quote date/scope are not verified"
                    if not measures.get("pr7_membrane_module_screen")
                    else "user-supplied price range; original quote date and installation scope not verified"
                ),
            },
            {
                "cost_id": "PR7-MODULE-LIFETIME-SCREEN",
                "source_title": "User-supplied PR7 membrane lifetime range",
                "source_url": "",
                "confidence": "user_supplied_unverified",
                "source_status": "user_supplied_unverified",
                "source_sheet": "biostimulant_membrane_gated_parameters.csv",
                "source_row": None,
                "value": [pr7_module["lifetime_min_year"], pr7_module["lifetime_max_year"]],
                "unit": "year",
                "basis": "linear annual replacement allowance screen only",
                "geography": "not specified",
                "reference_year": None,
                "retrieval_date": None,
                "evidence_class": "user_supplied_unverified",
                "applicability": "Does not include module installation, removal, disposal, downtime, or working capital.",
                "conversion_method": "straight-line EUR module purchase cost / lifetime range; excludes removal, disposal, labor and downtime",
                "uncertainty": "2.5–3.0 years supplied; no probability distribution",
            },
        )
    if measures.get("pr7_route_selected"):
        cost_reference_path = (
            Path(__file__).resolve().parents[1]
            / "data" / "Protein recovery" / "Membrane"
            / "biostimulant_membrane_cost_references.csv"
        )
        with cost_reference_path.open("r", newline="", encoding="utf-8-sig") as handle:
            for record in csv.DictReader(handle):
                if not record["reference_id"].startswith(("NF_", "GRASS_", "GRASSA_")):
                    continue
                traceability += ({
                    "cost_id": f"PR7-CONTEXT-{record['reference_id']}",
                    "source_title": record["source_title"],
                    "source_url": record["source_url"],
                    "confidence": "contextual_analogue_not_applied",
                    "source_status": "contextual_analogue_not_applied",
                    "source_sheet": "biostimulant_membrane_cost_references.csv",
                    "source_row": record["reference_id"],
                    "value": record["value_eur"],
                    "unit": record["unit"],
                    "basis": record["application_status"],
                    "geography": record["geographic_scope"],
                    "reference_year": record["source_date"],
                    "retrieval_date": record["source_date"],
                    "evidence_class": "contextual_analogue_not_applied",
                    "applicability": record["reason_not_applied_directly"],
                    "conversion_method": record["conversion_basis"],
                    "uncertainty": "Not transferred to GreenHub grass-juice TEA.",
                    "warning": "Reference shown for context only; excluded from CAPEX/OPEX totals.",
                },)
        if measures.get("pr7_crossflow_electricity_supplied"):
            traceability += ({
                "cost_id": "PR7-CROSSFLOW-ELECTRICITY",
                "source_title": "Explicit PR7 crossflow-specific electricity input",
                "source_url": "",
                "confidence": "explicit_user_input_requires_source_note",
                "source_status": "explicit_user_input",
                "source_sheet": "SimulationRequest.biostimulant_route",
                "source_row": None,
                "value": measures.get("pr7_crossflow_electricity_kwh_m3_feed"),
                "unit": "kWh/m3 clarified feed",
                "basis": "crossflow recirculation electricity, excluding separately modeled permeate-side pressure work",
                "geography": basis.location,
                "reference_year": basis.price_year,
                "retrieval_date": None,
                "evidence_class": "explicit_user_input",
                "applicability": "Applied to simulated clarified-juice volumetric feed and included in the BioSTEAM electricity utility.",
                "conversion_method": "specific electricity × modeled clarified-feed volume flow",
                "uncertainty": "Not propagated; caller must supply measurement/source note.",
                "warning": str(measures.get("pr7_crossflow_electricity_source") or ""),
            },)
    if cip_screen:
        traceability += tuple({
            "cost_id": "PR7-CIP-REAGENTS",
            "source_title": f"Registered {item['parameter_id']} price reference",
            "source_url": item["source_reference"],
            "confidence": item["source_status"],
            "source_status": item["source_status"],
            "source_sheet": "biostimulant_membrane_gated_parameters.csv",
            "source_row": None,
            "value": item["value"],
            "unit": item["units"],
            "basis": item["model_use"],
            "geography": "source-specific; see supplier listing",
            "reference_year": None,
            "retrieval_date": item["source_date"],
            "evidence_class": "indicative_price_reference_only",
            "applicability": "Applied to explicit PR7 reagent make-up quantity; verify grade, delivery terms, and current price.",
            "conversion_method": "EUR/t price multiplied by calculated annual reagent mass in tonnes.",
            "uncertainty": "Indicative supplier reference; not a procurement quote.",
        } for item in cip_screen["price_references"])
    route_summary = {
        **route,
        "model_type": model_type,
        "operating_hours_per_year": measures.get("operating_hours_per_year"),
        "annual_throughput_kg": measures.get("annual_throughput_kg"),
        "throughput_kg_per_hr": measures.get("throughput_kg_per_hr"),
        "annual_products_kg": measures.get("annual_products_kg", {}),
        "annual_products_m3": measures.get("annual_products_m3", {}),
        "pr7_target_concentration_factor": measures.get("pr7_target_concentration_factor"),
        "pr7_actual_volume_concentration_factor": measures.get("pr7_actual_volume_concentration_factor"),
        "pr7_feed_volume_m3_per_hr": measures.get("pr7_feed_volume_m3_per_hr"),
        "pr7_retentate_volume_m3_per_hr": measures.get("pr7_retentate_volume_m3_per_hr"),
        "annual_products_nm3": measures.get("annual_products_nm3", {}),
        "pr7_membrane_module_screen": measures.get("pr7_membrane_module_screen"),
        "pr7_membrane_module_screen_range": measures.get("pr7_membrane_module_screen_range"),
        "pr7_membrane_replacement_opex_eur_year": (
            measures.get("pr7_membrane_module_screen", {}).get("module_replacement_high_EUR_year")
            if measures.get("pr7_membrane_module_screen") else None
        ),
        "pr7_membrane_replacement_basis": "upper annualized replacement bound included in OPEX when full area is resolved; module purchase remains excluded from installed CAPEX",
        "pr7_crossflow_electricity_kwh_m3_feed": measures.get("pr7_crossflow_electricity_kwh_m3_feed"),
        "pr7_crossflow_electricity_source": measures.get("pr7_crossflow_electricity_source"),
        "pr7_crossflow_electricity_supplied": measures.get("pr7_crossflow_electricity_supplied", False),
        "pr7_cip_reagent_screen": measures.get("pr7_cip_reagent_screen"),
        "pr7_meuf_surfactant_screen": measures.get("pr7_meuf_surfactant_screen"),
        "quantity_warnings": measures.get("quantity_warnings", []),
        "partial_time_grid_totals": measures.get("partial_time_grid_totals", {}),
        "annual_chp_electricity_output_kwh": measures.get("annual_chp_electricity_output_kwh"),
        "annual_chp_heat_output_kwh": measures.get("annual_chp_heat_output_kwh"),
        "non_sale_product_reasons": dict(finance.non_sale_product_reasons),
        "tea_calculation_order": "formed_route_then_post_simulation_tea",
        "process_calculations_modified": False,
        "validated_tea_ready": False,
        "cost_boundary_complete": basis.cost_boundary_complete,
        "price_basis_confirmed": basis.price_basis_confirmed,
    }
    confidence_counts = Counter(item.confidence or "unspecified" for item in selected)
    confidence_counts.update(
        str(item.get("confidence") or "unspecified") for item in price_traceability
    )
    return TEAReport(
        route_summary=route_summary,
        selected_cost_lines=tuple(_selected_summary(item) for item in selected),
        excluded_alternatives=tuple(excluded),
        capex_lines=tuple(capex_lines),
        opex_lines=tuple(opex_lines),
        revenue_lines=tuple(revenue_lines),
        missing_inputs=tuple(missing),
        warnings=tuple(dict.fromkeys(warnings)),
        totals=totals,
        financial_assumptions=finance.to_dict(),
        financial_kpis=financial_kpis,
        cash_flow=cash_flow,
        replacement_schedule=tuple(replacement_schedule),
        confidence_summary=dict(sorted(confidence_counts.items())),
        source_traceability=traceability,
        project_basis=basis.to_dict(),
        project_assumption_traceability=tuple(_project_assumption_traceability(basis)),
    )


def _select_records(
    records: tuple[TEACostRecord, ...],
    route: dict[str, object],
    basis: TEAProjectBasis,
) -> tuple[list[TEACostRecord], list[dict[str, object]], list[str]]:
    formed = set(str(item) for item in route["route_tags"])
    explicit = set(str(item) for item in route.get("explicit_route_tags", ())) | set(basis.explicit_route_tags)
    includes = set(basis.include_cost_ids)
    excludes = set(basis.exclude_cost_ids)
    selected: list[TEACostRecord] = []
    excluded_lines: list[dict[str, object]] = []
    for record in records:
        matched = sorted(set(record.scenario_or_route_tags) & formed)
        explicitly_matched = bool(set(record.scenario_or_route_tags) & explicit)
        if record.cost_id in excludes:
            excluded_lines.append(_excluded(record, "explicit_project_exclusion"))
        elif record.cost_id in includes:
            selected.append(record)
        elif not matched and not explicitly_matched:
            if record.alternative_group:
                excluded_lines.append(_excluded(record, "unselected_route_alternative"))
        elif not record.can_sum_by_default and not explicitly_matched:
            excluded_lines.append(_excluded(record, "explicit_project_basis_required"))
        else:
            selected.append(record)

    warnings: list[str] = []
    grouped: dict[str, list[TEACostRecord]] = defaultdict(list)
    for record in selected:
        if record.alternative_group:
            grouped[record.alternative_group].append(record)
    for group, candidates in grouped.items():
        if len(candidates) <= 1:
            continue
        explicit_candidates = [
            item for item in candidates
            if item.cost_id in includes or set(item.scenario_or_route_tags) & explicit
        ]
        if len(explicit_candidates) == len(candidates):
            warnings.append(f"Multiple '{group}' units were retained because the formed route explicitly selected each alternative.")
            continue
        keep = explicit_candidates[0] if len(explicit_candidates) == 1 else sorted(candidates, key=lambda item: item.cost_id)[0]
        for record in candidates:
            if record is keep:
                continue
            selected.remove(record)
            excluded_lines.append(_excluded(record, f"alternative_group_{group}_selected_{keep.cost_id}"))

    packages: dict[str, list[TEACostRecord]] = defaultdict(list)
    for record in selected:
        if record.package_group:
            packages[record.package_group].append(record)
    for group, candidates in packages.items():
        package_rows = [item for item in candidates if item.package_role == "package"]
        subcomponents = [item for item in candidates if item.package_role == "subcomponent"]
        if package_rows and subcomponents:
            for record in subcomponents:
                selected.remove(record)
                excluded_lines.append(_excluded(record, f"included_in_selected_package_{package_rows[0].cost_id}"))
            warnings.append(f"Package/subcomponent double counting was blocked for '{group}'.")
    return selected, excluded_lines, warnings


def _calculate_capex(
    record: TEACostRecord,
    measures: dict[str, object],
    basis: TEAProjectBasis,
    model_type: str,
) -> tuple[dict[str, object], list[dict[str, object]]]:
    line = _line_base(record)
    missing: list[dict[str, object]] = []
    capacity = _capacity_for(record, measures, basis)
    code_prefix = "missing_dynamic_" if model_type == "dynamic" else "missing_"
    if record.reference_value_eur is None:
        missing.append(_missing(record, f"{code_prefix}reference_value", "reference_value_eur"))
    if record.reference_capacity is None or record.reference_capacity <= 0 or record.scaling_exponent is None:
        missing.append(_missing(record, "missing_scaling_input", "reference_capacity/scaling_exponent"))
    if capacity is None:
        missing.append(_missing(record, f"{code_prefix}capacity", record.capacity_unit or "project capacity"))
    if not missing:
        project_value, project_unit, source = capacity
        converted = _convert_unit(project_value, project_unit, record.capacity_unit)
        if converted is None:
            missing.append(_missing(record, "incompatible_capacity_unit", f"{project_unit} -> {record.capacity_unit}"))
        elif converted <= 0:
            missing.append(_missing(record, "invalid_design_capacity", "positive capacity for selected equipment"))
        else:
            scale_range = basis.capacity_ranges.get(record.cost_id)
            if scale_range is not None:
                if not isinstance(scale_range, Mapping):
                    raise ValueError("capacity_ranges entries require min, max and unit.")
                minimum = _convert_unit(float(scale_range["min"]), str(scale_range["unit"]), record.capacity_unit)
                maximum = _convert_unit(float(scale_range["max"]), str(scale_range["unit"]), record.capacity_unit)
                if minimum is None or maximum is None or not 0 < minimum <= maximum:
                    raise ValueError("Capacity range must have positive compatible min <= max.")
                outside = not minimum <= converted <= maximum
                line["scaling_range_status"] = "explicit_extrapolation" if outside else "within_declared_range"
                if outside and not basis.allow_capacity_extrapolation:
                    line.update(direct_cost_eur=None, installed_cost_eur=None, calculation_status="blocked_outside_capacity_range")
                    return line, [_missing(record, "outside_capacity_range", f"design capacity in [{minimum}, {maximum}] {record.capacity_unit}; explicit extrapolation opt-in required")]
            else:
                line["scaling_range_status"] = "range_not_established"
            direct = float(record.reference_value_eur) * (
                converted / float(record.reference_capacity)
            ) ** float(record.scaling_exponent) * basis.cost_multipliers.get(record.cost_id, 1.0)
            factor = basis.installed_factors.get(record.cost_id, record.installed_factor)
            line.update(
                project_capacity=converted,
                project_capacity_unit=record.capacity_unit,
                capacity_source=source,
                cost_multiplier=basis.cost_multipliers.get(record.cost_id, 1.0),
                direct_cost_eur=direct,
                installed_factor=float(factor) if factor is not None else None,
                installed_cost_eur=direct * float(factor) if factor is not None else None,
                calculation_status="calculated" if factor is not None else "direct_cost_only_missing_installed_factor",
            )
            if factor is None:
                missing.append(_missing(record, "missing_installed_factor", "installed_factor"))
    if basis.screening_estimates:
        if line.get("direct_cost_eur") is None and record.reference_value_eur is not None and record.reference_capacity is None and any(token in (record.reference_unit or "").lower() for token in ("eur/package", "eur/unit", "eur/system")):
            direct = float(record.reference_value_eur) * basis.cost_multipliers.get(record.cost_id, 1.0)
            factor = basis.installed_factors.get(record.cost_id, record.installed_factor)
            line.update(direct_cost_eur=direct, installed_cost_eur=direct * (float(factor) if factor is not None else 1.0), installed_factor=factor,
                        calculation_status="unscaled_reference_package_assumption",
                        warning=str(line.get("warning", "")) + " Unscaled reference package used; project/reference capacity match is unverified. Installation excluded where factor is missing.")
            missing = []
        elif line.get("direct_cost_eur") is not None and line.get("installed_cost_eur") is None:
            line.update(installed_cost_eur=line["direct_cost_eur"], calculation_status="direct_cost_installation_excluded",
                        warning=str(line.get("warning", "")) + " Installation factor missing: direct equipment cost used for screening; installation remains excluded.")
            missing = [item for item in missing if item['code'] != 'missing_installed_factor']
    if "calculation_status" not in line:
        line.update(direct_cost_eur=None, installed_cost_eur=None, calculation_status="not_calculated")
    return line, missing


def _calculate_indirect(
    record: TEACostRecord,
    capex_lines: list[dict[str, object]],
    basis: TEAProjectBasis,
    model_type: str,
) -> tuple[dict[str, object], list[dict[str, object]]]:
    line = _line_base(record)
    quantity = _explicit_quantity(record, basis)
    if quantity is None:
        code = "missing_dynamic_quantity" if model_type == "dynamic" else "missing_quantity"
        line.update(direct_cost_eur=None, installed_cost_eur=None, calculation_status="not_calculated")
        return line, [_missing(record, code, "explicit indirect-cost basis")]
    value, unit, source = quantity
    rate = record.rate_value if record.rate_value is not None else record.reference_value_eur
    if rate is None:
        line.update(direct_cost_eur=None, installed_cost_eur=None, calculation_status="not_calculated")
        return line, [_missing(record, "missing_rate", "indirect cost rate")]
    amount = value * rate * basis.cost_multipliers.get(record.cost_id, 1.0)
    line.update(
        quantity=value, quantity_unit=unit, quantity_source=source,
        direct_cost_eur=None, installed_cost_eur=amount,
        calculation_status="calculated_explicit_project_basis",
    )
    return line, []


def _calculate_annual_line(
    record: TEACostRecord,
    measures: dict[str, object],
    basis: TEAProjectBasis,
    model_type: str,
    *,
    revenue: bool,
) -> tuple[dict[str, object], list[dict[str, object]]]:
    line = _line_base(record)
    if record.cost_type == "logistics" and measures.get("annual_logistics_cost_eur") is not None:
        amount = float(measures["annual_logistics_cost_eur"]) * basis.cost_multipliers.get(record.cost_id, 1.0)
        line.update(
            quantity=1.0, quantity_unit="annual result", quantity_source="explicit logistics result",
            unit_cost_eur=amount, calculation_status="calculated_from_logistics_result",
            cost_multiplier=basis.cost_multipliers.get(record.cost_id, 1.0), annual_cost_eur=amount,
        )
        return line, []
    quantity = _annual_quantity_for(record, measures, basis, revenue)
    rate = record.annual_unit_cost_eur
    if rate is None and record.cost_type in {"maintenance", "indirect"}:
        rate = record.rate_value
    missing: list[dict[str, object]] = []
    if quantity is None:
        code = "missing_dynamic_quantity" if model_type == "dynamic" else "missing_quantity"
        missing.append(_missing(record, code, "annual simulation quantity or explicit project basis"))
    if rate is None:
        missing.append(_missing(record, "missing_unit_cost", "annual_unit_cost_eur"))
    if missing:
        line.update(calculation_status="not_calculated")
        line["annual_revenue_eur" if revenue else "annual_cost_eur"] = None
        return line, missing
    value, unit, source = quantity
    target_unit = _cost_denominator(record.reference_unit or record.rate_unit)
    converted = value if target_unit is None else _convert_unit(value, unit, target_unit)
    if converted is None:
        line.update(calculation_status="not_calculated")
        line["annual_revenue_eur" if revenue else "annual_cost_eur"] = None
        return line, [_missing(record, "incompatible_quantity_unit", f"{unit} -> {target_unit}")]
    amount = converted * float(rate) * basis.cost_multipliers.get(record.cost_id, 1.0)
    line.update(
        quantity=converted, quantity_unit=target_unit or unit, quantity_source=source,
        unit_cost_eur=float(rate), calculation_status="calculated",
        cost_multiplier=basis.cost_multipliers.get(record.cost_id, 1.0),
    )
    line["annual_revenue_eur" if revenue else "annual_cost_eur"] = amount
    return line, []


def _empirical_route(result: object, selected_routes: Sequence[str] | None, basis: TEAProjectBasis) -> dict[str, object]:
    selection = result.selected_scenarios
    ids = tuple(selection.scenario_ids)
    explicit = tuple(str(item) for item in (selected_routes or ())) + tuple(basis.explicit_route_tags)
    tags = set(ids) | set(explicit) | {"electricity"}
    aliases = {
        "F0": ("measured_liquid",), "F1": ("raw_press",), "F2": ("raw_press", "pef"), "F3": ("raw_press", "pef"),
        "PR0": ("no_protein_recovery",), "PR1": ("isoelectric",), "PR2": ("heat",),
        "PR3": ("isoelectric", "heat"), "PR4": ("lactic_acid",), "PR6": ("membrane_protein",),
        "BG0": ("raw_biogas",), "BG1": ("chp", "chp_utilities"), "BG2": ("water_scrubbing",),
        "BG3": ("membrane_upgrading",), "BG4": ("psa",), "BG5": ("mea",),
        "NR1": ("digestate_separation",), "NR2": ("digestate_separation", "phosphorus_recovery"),
        "NR3": ("digestate_separation", "ammonia_recovery"),
        "NR4": ("digestate_separation", "phosphorus_recovery", "ammonia_recovery"),
        "NR5": ("digestate_separation", "phosphorus_recovery"),
        "NR6": ("digestate_separation", "ion_exchange"),
        "NR7": ("digestate_separation", "phosphorus_recovery", "ammonia_recovery", "potassium_water_concentration"),
    }
    for scenario_id in ids:
        tags.update(aliases.get(scenario_id, ()))
    unit_ids = tuple(str(item.unit_id) for item in result.units)
    return {
        "scenario_ids": list(ids),
        "formed_unit_ids": list(unit_ids),
        "route_tags": sorted(tags),
        "explicit_route_tags": sorted(set(explicit)),
    }


def _dynamic_route(dynamic_result: object, selected_routes: Sequence[str] | None, basis: TEAProjectBasis) -> dict[str, object]:
    payload = _object_payload(dynamic_result)
    config = payload.get("scenario") or payload.get("config") or {}
    if not isinstance(config, Mapping):
        config = _object_payload(config)
    protein = str(config.get("protein_method", ""))
    drying = str(config.get("drying_method", ""))
    upgrading = str(config.get("upgrading_method") or config.get("gas_route") or "")
    ad = str(config.get("ad_method", ""))
    resources = tuple(str(item) for item in config.get("resource_recovery_methods", ()) or ())
    explicit = tuple(str(item) for item in (selected_routes or ())) + tuple(basis.explicit_route_tags)
    tags = {drying, ad, "electricity", *resources, *explicit}
    tags.add("membrane_protein" if protein == "membrane" else protein)
    tags.add("membrane_upgrading" if upgrading == "membrane" else upgrading)
    aliases = {
        "isoelectric": ("PR1",), "lactic_acid": ("PR4",), "membrane": ("PR6", "membrane_protein"),
        "water_scrubbing": ("BG2",), "membrane_upgrading": ("BG3",), "psa": ("BG4",),
        "mea": ("BG5",), "chp_utilities": ("BG1", "chp"),
        "digestate_separation": ("NR1",), "ammonia_recovery": ("NR3",),
        "phosphorus_recovery": ("NR2",), "ion_exchange": ("NR6",),
        "potassium_water_concentration": ("NR7",),
    }
    for item in tuple(tags):
        tags.update(aliases.get(item, ()))
    tags.discard("")
    return {
        "scenario_id": config.get("scenario_id") or payload.get("scenario_id"),
        "selected_methods": {
            "protein_method": protein, "drying_method": drying,
            "ad_method": ad, "upgrading_method": upgrading,
            "resource_recovery_methods": list(resources),
        },
        "formed_unit_ids": _dynamic_unit_ids(payload),
        "route_tags": sorted(tags),
        "explicit_route_tags": sorted(set(explicit)),
    }


def _empirical_measures(result: object, basis: TEAProjectBasis, *, logistics_result: object | None = None) -> dict[str, object]:
    measures: dict[str, object] = {"source": "empirical_simulation_result"}
    if logistics_result is not None:
        payload = logistics_result.to_dict() if hasattr(logistics_result, "to_dict") else logistics_result
        if not isinstance(payload, Mapping):
            raise TypeError("logistics_result must be a mapping or provide to_dict().")
        limitations = tuple(payload.get("limitations") or ())
        measures["annual_logistics_cost_eur"] = None if limitations else _number(payload.get("transport_cost_currency"))
        measures["logistics_provenance"] = {
            "source_status": "model_output" if not limitations else "incomplete_input",
            "limitations": list(limitations),
        }
    measures["detected_saleable_products"] = [
        str(item.product_id)
        for item in result.products
        if _number(item.mass_flow.value) != 0 and _slug(str(item.product_id)) in _SALEABLE_PRODUCTS
    ]
    if getattr(result.selected_scenarios, "protein_recovery", None) == "PR7":
        measures["pr7_route_selected"] = True
        membrane_unit = next((item for item in result.units if item.unit_id == "PR7_M101"), None)
        area_item = membrane_unit.design_results.get("Membrane area") if membrane_unit else None
        area_m2 = _number(getattr(area_item, "value", None))
        minimum_area_m2 = _number(getattr(membrane_unit.design_results.get("Minimum membrane area"), "value", None)) if membrane_unit else None
        maximum_area_m2 = _number(getattr(membrane_unit.design_results.get("Maximum membrane area"), "value", None)) if membrane_unit else None
        if result.seasonal_summary:
            peak_area = _number(result.seasonal_summary.get("pr7_peak_membrane_area_m2"))
            if peak_area is not None:
                area_m2 = peak_area
            minimum_area_m2 = _number(result.seasonal_summary.get("pr7_minimum_peak_membrane_area_m2"))
            maximum_area_m2 = _number(result.seasonal_summary.get("pr7_maximum_peak_membrane_area_m2"))
        protein_area = next((item for item in result.process_areas if item.process_area_id == "protein_recovery"), None)
        technology = protein_area.metrics.get("biostimulant_membrane_technology") if protein_area else None
        measures["pr7_membrane_technology"] = str(technology) if technology else None
        if area_m2 is not None and technology:
            from Greenhub.biostimulant_screening import calculate_membrane_module_cost_range
            measures["pr7_membrane_module_screen"] = calculate_membrane_module_cost_range(str(technology), area_m2)
            measures["pr7_membrane_module_screen"]["area_basis"] = (
                "peak monthly membrane area" if result.seasonal_summary else "steady-state membrane area"
            )
        else:
            measures["pr7_membrane_module_screen"] = None
            if not technology:
                message = "PR7 membrane technology is missing; no membrane-module cost or replacement screen was derived."
            elif minimum_area_m2 is not None and maximum_area_m2 is None:
                message = (
                    "PR7 full membrane area is unresolved because some nonzero feed pools lack retention/fate data; "
                    "only the known-stream minimum-area module-cost floor is reported, with no replacement OPEX."
                )
            else:
                message = "PR7 usable membrane area is unresolved; no full module-cost or replacement screen was derived."
            measures.setdefault("quantity_warnings", []).append(message)
        if technology and minimum_area_m2 is not None and (
            maximum_area_m2 is None or maximum_area_m2 >= minimum_area_m2
        ):
            from Greenhub.biostimulant_screening import calculate_membrane_module_cost_range
            measures["pr7_membrane_module_screen_range"] = {
                "technology_id": str(technology),
                "minimum_area_m2": minimum_area_m2,
                "maximum_area_m2": maximum_area_m2,
                "minimum_area_cost_screen": calculate_membrane_module_cost_range(str(technology), minimum_area_m2),
                "maximum_area_cost_screen": (
                    calculate_membrane_module_cost_range(str(technology), maximum_area_m2)
                    if maximum_area_m2 is not None else None
                ),
                "status": "known_stream_area_floor_only_unresolved_pool_fate" if maximum_area_m2 is None else "membrane_area_screen",
            }
        if membrane_unit:
            for key, design_name in (
                ("pr7_target_concentration_factor", "Target concentration factor"),
                ("pr7_actual_volume_concentration_factor", "Actual volume concentration factor"),
                ("pr7_feed_volume_m3_per_hr", "Feed volumetric flow"),
                ("pr7_retentate_volume_m3_per_hr", "Retentate volumetric flow"),
            ):
                design_value = membrane_unit.design_results.get(design_name)
                measures[key] = _number(getattr(design_value, "value", None))
        if protein_area:
            measures["pr7_cip_solution_volume_L_per_step"] = protein_area.metrics.get("biostimulant_cip_solution_volume_L_per_step")
            measures["pr7_cip_makeup_fraction_per_cycle"] = protein_area.metrics.get("biostimulant_cip_makeup_fraction_per_cycle")
            measures["pr7_cip_input_source"] = protein_area.metrics.get("biostimulant_cip_input_source")
            measures["pr7_crossflow_electricity_kwh_m3_feed"] = protein_area.metrics.get("biostimulant_crossflow_electricity_kwh_m3_feed")
            measures["pr7_crossflow_electricity_source"] = protein_area.metrics.get("biostimulant_crossflow_electricity_source")
            measures["pr7_crossflow_electricity_supplied"] = (
                measures["pr7_crossflow_electricity_kwh_m3_feed"] is not None
                and bool(measures["pr7_crossflow_electricity_source"])
            )
        pressure_work_supplied = bool(
            membrane_unit
            and membrane_unit.design_results.get("Transmembrane pressure") is not None
            and membrane_unit.design_results.get("Pump efficiency") is not None
        )
        measures["pr7_pressure_work_supplied"] = pressure_work_supplied
    feed = next((item for item in result.streams if 'feed' in item.aliases or item.stream_id == 'feed'), None)
    if feed and feed.total_mass.value is not None:
        measures["throughput_kg_per_hr"] = float(feed.total_mass.value)
    if result.throughput_series:
        measures["throughput_kg_per_hr"] = max(float(row['actual_throughput_kg_hr']) for row in result.throughput_series)
    hours = _basis_operating_hours(basis)
    if result.seasonal_summary and result.throughput_series:
        # Integrated quantities have an established period; a TEA basis may
        # confirm it but must not replace it with a different denominator.
        hours = _sum_known(item.get("available_operating_hours") for item in result.throughput_series)
        measures["scheduled_operating_hours"] = float(hours or 0.0)
        measures["active_process_operating_hours"] = float(
            result.seasonal_summary.get("active_process_operating_hours", 0.0) or 0.0
        )
        if result.selected_scenarios.protein_recovery == "PR7":
            measures["annual_pr7_feed_volume_m3"] = float(
                result.seasonal_summary.get("pr7_feed_volume_m3_year", 0.0) or 0.0
            )
            measures["annual_pr7_unresolved_mass_kg"] = float(
                result.seasonal_summary.get("pr7_unresolved_mass_kg_year", 0.0) or 0.0
            )
            measures["pr7_unresolved_component_ids"] = tuple(
                result.seasonal_summary.get("pr7_unresolved_component_ids", ())
            )
    if hours is not None:
        measures["operating_hours_per_year"] = float(hours)
    if measures.get("pr7_route_selected") and not result.seasonal_summary and hours is not None:
        unresolved_stream = next((item for item in result.streams if "biostimulant_unresolved" in item.aliases), None)
        unresolved_rate = _number(unresolved_stream.total_mass.value) if unresolved_stream else 0.0
        measures["pr7_unresolved_mass_kg_hr"] = unresolved_rate or 0.0
        measures["annual_pr7_unresolved_mass_kg"] = (unresolved_rate or 0.0) * float(hours)
        measures["pr7_unresolved_component_ids"] = tuple(
            component_id for component_id, value in unresolved_stream.components.items()
            if (_number(value.value) or 0.0) > 1e-12
        ) if unresolved_stream else ()
    elif measures.get("pr7_route_selected") and not result.seasonal_summary:
        unresolved_stream = next((item for item in result.streams if "biostimulant_unresolved" in item.aliases), None)
        measures["pr7_unresolved_mass_kg_hr"] = _number(unresolved_stream.total_mass.value) if unresolved_stream else 0.0
        measures["pr7_unresolved_component_ids"] = tuple(
            component_id for component_id, value in unresolved_stream.components.items()
            if (_number(value.value) or 0.0) > 1e-12
        ) if unresolved_stream else ()
    if (
        measures.get("pr7_route_selected")
        and measures.get("pr7_cip_solution_volume_L_per_step") is not None
        and measures.get("pr7_cip_makeup_fraction_per_cycle") is not None
        and measures.get("pr7_cip_input_source")
        and hours is not None
    ):
        from Greenhub.biostimulant_screening import calculate_cip_reagent_screen
        measures["pr7_cip_reagent_screen"] = calculate_cip_reagent_screen(
            operating_hours_year=float(
                measures.get("active_process_operating_hours", hours)
                if result.seasonal_summary else hours
            ),
            solution_volume_L_per_step=float(measures["pr7_cip_solution_volume_L_per_step"]),
            makeup_fraction_per_cycle=float(measures["pr7_cip_makeup_fraction_per_cycle"]),
            input_source=str(measures["pr7_cip_input_source"]),
        )
    if (
        measures.get("pr7_route_selected")
        and measures.get("pr7_membrane_technology") == "MEUF"
        and (
            measures.get("annual_pr7_feed_volume_m3") is not None
            or measures.get("pr7_feed_volume_m3_per_hr") is not None
        )
        and (hours is not None or result.seasonal_summary)
    ):
        from Greenhub.biostimulant_screening import calculate_meuf_surfactant_screen
        measures["pr7_meuf_surfactant_screen"] = calculate_meuf_surfactant_screen(
            float(measures.get("annual_pr7_feed_volume_m3") or 0.0)
            if result.seasonal_summary else
            float(measures["pr7_feed_volume_m3_per_hr"]) * float(hours)
        )
    annual_throughput = None
    if result.seasonal_summary:
        annual_throughput = _number(result.seasonal_summary.get("total_biomass_processed_kg"))
    if annual_throughput is None and hours is not None and measures.get("throughput_kg_per_hr") is not None:
        annual_throughput = float(measures["throughput_kg_per_hr"]) * float(hours)
    if annual_throughput is not None:
        measures["annual_throughput_kg"] = float(annual_throughput)

    if result.seasonal_summary:
        utilities = result.seasonal_summary.get("total_utilities", {})
        measures["annual_electricity_kwh"] = _number(utilities.get("electricity_kwh"))
        measures["annual_heat_kwh"] = _number(utilities.get("heating_kwh"))
        measures["annual_cooling_kwh"] = _number(utilities.get("cooling_kwh"))
        measures["annual_products_kg"] = {
            str(key): float(value) for key, value in result.seasonal_summary.get("total_products_kg", {}).items()
        }
        volume_totals: defaultdict[str, float] = defaultdict(float)
        for row in result.product_series:
            for key, value in row.get("volumetric_products_m3", {}).items():
                volume_totals[str(key)] += float(value)
        measures["annual_products_m3"] = dict(volume_totals)
    elif hours is not None:
        electricity_kw = _sum_known(item.demand.value for item in result.utilities if item.kind == "electricity")
        heat_values = [item.demand.value for item in result.utilities if item.kind == "heat"]
        heat_kj_hr = None if any(value is None for value in heat_values) else sum(max(float(value), 0.0) for value in heat_values)
        cooling_kj_hr = None if any(value is None for value in heat_values) else -sum(min(float(value), 0.0) for value in heat_values)
        measures.update(
            annual_electricity_kwh=None if electricity_kw is None else electricity_kw * hours,
            annual_heat_kwh=None if heat_kj_hr is None else heat_kj_hr / 3600.0 * hours,
            annual_cooling_kwh=None if cooling_kj_hr is None else cooling_kj_hr / 3600.0 * hours,
            annual_products_kg={
                str(item.product_id): None if item.mass_flow.value is None else float(item.mass_flow.value) * hours for item in result.products
            },
            annual_products_m3={
                str(item.product_id): None if item.volumetric_flow is None or item.volumetric_flow.value is None else float(item.volumetric_flow.value) * hours
                for item in result.products if item.volumetric_flow is not None
            },
        )
    from .sale_quantities import SALE_COMPONENTS, dry_gas_kmol, reference_volume_m3
    components, gas_moles = {}, {}
    if result.seasonal_summary:
        for row in result.product_series:
            for product, values in row.get('sale_components_kg', {}).items():
                target = components.setdefault(product, {})
                for component, value in values.items():
                    target[component] = None if value is None or target.get(component, 0.0) is None else target.get(component, 0.0) + float(value)
            for product, value in row.get('dry_gas_products_kmol', {}).items():
                gas_moles[product] = None if value is None or gas_moles.get(product, 0.0) is None else gas_moles.get(product, 0.0) + float(value)
    elif hours is not None:
        streams = {stream.stream_id: stream for stream in result.streams}
        for product in result.products:
            stream = streams.get(product.stream_id)
            component = SALE_COMPONENTS.get(product.product_id)
            if stream is not None and component:
                value = stream.components.get(component)
                components[product.product_id] = {component: 0.0 if value is None else None if value.value is None else float(value.value) * hours}
            if product.product_id == 'biomethane' and stream is not None:
                kmol = dry_gas_kmol({name: value.value for name, value in stream.components.items()})
                if kmol is not None:
                    gas_moles['biomethane'] = kmol * hours
    measures['annual_product_components_kg'] = components
    measures['annual_dry_gas_kmol'] = gas_moles
    measures['annual_products_nm3'] = {key: None if value is None else reference_volume_m3(value, 273.15) for key, value in gas_moles.items()}
    measures["formed_units"] = tuple(result.units)
    measures["design_capacities"] = tuple(
        {
            "unit_id": unit.unit_id,
            "process_area": unit.process_area,
            "design_name": name,
            "value": float(value.value),
            "unit": value.unit,
        }
        for unit in result.units
        for name, value in unit.design_results.items()
        if value.value is not None
    )
    return _with_basis_measures(measures, basis)


def _dynamic_measures(dynamic_result: object, basis: TEAProjectBasis) -> dict[str, object]:
    payload = _object_payload(dynamic_result)
    measures: dict[str, object] = {"source": "dynamic_time_steps_without_interpolation"}
    annual = payload.get("annual_summary")
    if isinstance(annual, Mapping):
        feed = annual.get("feed_processed", {})
        measures["annual_throughput_kg"] = _metric_to_base(feed, "mass")
        electricity = annual.get("electricity_demand", {})
        heat = annual.get("heat_demand", {})
        measures["annual_electricity_kwh"] = _energy_metric(electricity, "electricity")
        measures["annual_heat_kwh"] = _energy_metric(heat, "heat")
        products: dict[str, float] = {}
        for name, metric in annual.items():
            if isinstance(metric, Mapping) and name != "feed_processed":
                value = _metric_to_base(metric, "mass")
                if value is not None:
                    products[str(name)] = value
        measures["annual_products_kg"] = products
        volumes: dict[str, float] = {}
        normal_volumes: dict[str, float] = {}
        for name, metric in annual.items():
            if isinstance(metric, Mapping) and name != "feed_processed":
                value = _metric_to_base(metric, "gas")
                if value is not None:
                    volumes[str(name)] = value
                value = _metric_to_base(metric, "normal_gas")
                if value is not None:
                    normal_volumes[str(name)] = value
        measures["annual_products_m3"] = volumes
        measures["annual_products_nm3"] = normal_volumes
        schedule = payload.get("biomass_schedule", {})
        if isinstance(schedule, Mapping):
            monthly_schedule = schedule.get("monthly", ())
            if monthly_schedule:
                measures["operating_hours_per_year"] = _sum_known(row.get("operating_hours") for row in monthly_schedule)
            measures["throughput_kg_per_hr"] = _number(schedule.get("peak_throughput_kg_per_hr"))
        monthly = payload.get("monthly", ())
        if isinstance(monthly, Sequence):
            raw_rates = [
                _number(row.get("metrics", {}).get("raw_biogas", {}).get("m3_per_hr"))
                for row in monthly if isinstance(row, Mapping)
            ]
            raw_rates = [value for value in raw_rates if value is not None]
            if raw_rates:
                measures["raw_biogas_m3_per_hr"] = max(raw_rates)
            normal_rates = [
                _number(row.get("metrics", {}).get("raw_biogas", {}).get("Nm3_per_hr"))
                for row in monthly if isinstance(row, Mapping)
            ]
            if normal_rates and all(value is not None for value in normal_rates):
                measures["raw_biogas_nm3_per_hr"] = max(normal_rates)
        return _with_basis_measures(measures, basis)

    steps = payload.get("steps")
    config = payload.get("config", {})
    if isinstance(steps, Sequence) and steps:
        start = str(config.get("start_date", ""))
        end = str(config.get("end_date", ""))
        time_step = str(config.get("time_step", "monthly"))
        durations = {item.label: item.duration_hours for item in generate_time_grid(start, end, time_step)}
        steps = [dict(step) if isinstance(step, Mapping) else _object_payload(step) for step in steps]
        labels = [str(step.get("time_label", "")) for step in steps]
        if len(set(labels)) != len(labels) or set(labels) - set(durations):
            raise ValueError("Dynamic TEA steps require unique labels from the declared time grid.")
        grid_complete = set(labels) == set(durations)
        energy_keys = set().union(*(step.get("energy_summary", {}).keys() for step in steps))
        product_keys = set().union(*(step.get("product_outputs", {}).keys() for step in steps))
        warnings: list[str] = []

        def integrated(values, name):
            values = list(values)
            known_sum = sum(value * durations[label] for value, label in zip(values, labels) if value is not None)
            if not grid_complete or any(value is None for value in values):
                measures.setdefault("partial_time_grid_totals", {})[name] = known_sum
                warnings.append(f"{name}: missing time steps or values; known subtotal retained separately, annual quantity withheld.")
                return None
            return known_sum

        def energy_rates(kind, output=False):
            keys = [key for key in energy_keys if kind in key and ("output" in key) == output]
            if not keys:
                return [None] * len(steps)
            return [_sum_known(
                None if _number(step.get("energy_summary", {}).get(key)) is None else
                float(step["energy_summary"][key]) / (3.6 if "mj" in key.lower() else 1.0)
                for key in keys
            ) for step in steps]

        feed_rates = [_number(step.get("config", config).get("basis_feed_kg_per_hr")) for step in steps]
        electricity_rates, heat_rates = energy_rates("electricity"), energy_rates("heat")
        measures.update(
            annual_throughput_kg=integrated(feed_rates, "annual_throughput_kg"),
            operating_hours_per_year=sum(durations.values()) if grid_complete else None,
            throughput_kg_per_hr=max(feed_rates) if all(value is not None for value in feed_rates) and grid_complete else None,
            annual_electricity_kwh=integrated(electricity_rates, "annual_electricity_kwh"),
            annual_heat_kwh=integrated(heat_rates, "annual_heat_kwh"),
            heat_demand_kw=max(heat_rates) if all(value is not None for value in heat_rates) and grid_complete else None,
        )
        for kind in ("electricity", "heat"):
            if any(kind in key and "output" in key for key in energy_keys):
                name = f"annual_chp_{kind}_output_kwh"
                measures[name] = integrated(energy_rates(kind, output=True), name)
        for suffix, collection in (("_kg_hr", "annual_products_kg"), ("_m3_hr", "annual_products_m3"), ("_Nm3_hr", "annual_products_nm3")):
            measures[collection] = {
                key.removesuffix(suffix): integrated((_number(step.get("product_outputs", {}).get(key)) for step in steps), f"{collection}.{key}")
                for key in sorted(product_keys) if key.endswith(suffix)
            }
        for measure_name, stage, key in (
            ("raw_biogas_m3_per_hr", "gas_route", "raw_biogas_m3_hr"),
            ("raw_biogas_nm3_per_hr", "gas_route", "raw_biogas_Nm3_hr"),
            ("drying_water_removed_kg_per_hr", "drying", "water_removed_kg_hr"),
            ("chp_electricity_kw", "gas_route", "chp_electricity_output_kwh_hr"),
        ):
            values = [_number(step.get(stage, {}).get("metrics", {}).get(key)) for step in steps]
            measures[measure_name] = max(values) if grid_complete and all(value is not None for value in values) else None
        measures["quantity_warnings"] = warnings
    return _with_basis_measures(measures, basis)


def _with_basis_measures(measures: dict[str, object], basis: TEAProjectBasis) -> dict[str, object]:
    hours = _basis_operating_hours(basis)
    for name, declared in (("operating_hours_per_year", hours), ("annual_throughput_kg", basis.annual_throughput_kg)):
        if declared is None:
            continue
        actual = _number(measures.get(name))
        if actual is not None and abs(float(declared) - actual) > max(1e-6, abs(actual) * 1e-8):
            raise ValueError(f"TEA {name} ({declared}) conflicts with simulation quantity ({actual}); rerun the process to change its basis.")
        if actual is None:
            measures[name] = float(declared)
    return measures


def _sum_known(values: Iterable[object]) -> float | None:
    numbers = [_number(value) for value in values]
    return None if any(value is None for value in numbers) else sum(numbers)


def _basis_operating_hours(basis: TEAProjectBasis) -> float | None:
    if basis.operating_hours_per_year is not None:
        return float(basis.operating_hours_per_year)
    if basis.operating_days_per_year is not None and basis.operating_hours_per_day is not None:
        return float(basis.operating_days_per_year) * float(basis.operating_hours_per_day)
    return None


def _capacity_for(record: TEACostRecord, measures: dict[str, object], basis: TEAProjectBasis) -> tuple[float, str, str] | None:
    explicit = _lookup_mapping(basis.capacities, record)
    if explicit is not None:
        value, unit = _quantity_value(explicit, record.capacity_unit)
        return value, unit, "explicit_project_basis"
    unit = _norm_unit(record.capacity_unit)
    if "wet t/h" in unit or "wet tonnes/h" in unit:
        value = _number(measures.get("throughput_kg_per_hr"))
        return None if value is None else (value / 1000.0, "wet t/h", "simulation_boundary_throughput")
    if "nm3/h" in unit:
        value = _number(measures.get("raw_biogas_nm3_per_hr"))
        return None if value is None else (value, "Nm3/h raw gas", "dynamic_raw_biogas_rate")
    if "kg water" in unit and "/h" in unit:
        value = _number(measures.get("drying_water_removed_kg_per_hr"))
        return None if value is None else (value, "kg water evaporated/h", "dynamic_dryer_output")
    if "kw electric" in unit or "kwe" in unit:
        value = _number(measures.get("chp_electricity_kw"))
        return None if value is None else (value, "kW electric", "dynamic_chp_output")
    if "kwth" in unit:
        value = _number(measures.get("heat_demand_kw"))
        return None if value is None else (value, "kWth", "simulation_heat_demand")
    compatible: list[tuple[float, str, str]] = []
    record_tokens = set(_slug(record.process_area).split("_")) | set(_slug(record.process_step).split("_"))
    for item in measures.get("design_capacities", ()):
        if not isinstance(item, Mapping):
            continue
        unit_tokens = set(_slug(str(item.get("process_area", ""))).split("_"))
        name_tokens = set(_slug(str(item.get("design_name", ""))).split("_"))
        if not (record_tokens & (unit_tokens | name_tokens)):
            continue
        converted = _convert_unit(float(item["value"]), str(item.get("unit") or ""), record.capacity_unit)
        if converted is not None:
            compatible.append((converted, str(record.capacity_unit or ""), f"unit_design:{item['unit_id']}:{item['design_name']}"))
    if compatible and max(item[0] for item in compatible) - min(item[0] for item in compatible) <= 1e-9:
        return compatible[0]
    return None


def _annual_quantity_for(
    record: TEACostRecord,
    measures: dict[str, object],
    basis: TEAProjectBasis,
    revenue: bool,
) -> tuple[float, str, str] | None:
    explicit = _explicit_quantity(record, basis)
    if explicit is not None:
        return explicit
    if record.cost_type in {"labor", "maintenance", "logistics", "indirect"}:
        return None
    step = _slug(record.process_step)
    item = _slug(record.equipment_or_cost_item)
    if record.cost_type == "utility" and "electricity" in (step + item):
        value = _number(measures.get("annual_electricity_kwh"))
        return None if value is None else (value, "kWh/year", "simulation_utility_output")
    if record.cost_type == "utility" and any(token in step + item for token in ("heat", "natural_gas")):
        value = _number(measures.get("annual_heat_kwh"))
        return None if value is None else (value, "kWh/year", "simulation_heat_output")
    if record.cost_type == "revenue" or revenue:
        products = measures.get("annual_products_kg", {})
        if isinstance(products, Mapping):
            for name, value in products.items():
                if _slug(str(name)) in item or item in _slug(str(name)):
                    return float(value), "kg/year", "simulation_product_output"
    return None


def _explicit_quantity(record: TEACostRecord, basis: TEAProjectBasis) -> tuple[float, str, str] | None:
    raw = _lookup_mapping(basis.annual_quantities, record)
    if raw is None:
        return None
    value, unit = _quantity_value(raw, _cost_denominator(record.reference_unit or record.rate_unit))
    return value, unit, "explicit_project_basis"


def _lookup_mapping(values: Mapping[str, object], record: TEACostRecord) -> object | None:
    keys = (
        record.cost_id, record.process_step, record.equipment_or_cost_item,
        _slug(record.process_step), _slug(record.equipment_or_cost_item),
    )
    for key in keys:
        if key in values:
            return values[key]
    return None


def _quantity_value(raw: object, default_unit: str | None) -> tuple[float, str]:
    if isinstance(raw, Mapping):
        value = raw.get("value")
        unit = str(raw.get("unit") or default_unit or "unspecified")
    elif isinstance(raw, (tuple, list)) and len(raw) == 2:
        value, unit = raw
        unit = str(unit)
    else:
        value, unit = raw, default_unit or "unspecified"
    numeric = float(value)
    if not isfinite(numeric) or numeric < 0:
        raise ValueError("TEA project quantities must be finite and non-negative.")
    return numeric, unit


def _convert_unit(value: float, from_unit: str | None, to_unit: str | None) -> float | None:
    source, target = _norm_unit(from_unit), _norm_unit(to_unit)
    if not target or source == target or source == "unspecified":
        return value
    aliases = {
        "kg/year": "kg/y", "kg/y": "kg/y", "kg per year": "kg/y",
        "t/year": "t/y", "tonnes/year": "t/y", "wet tonnes/year": "t/y", "wet t/y": "t/y",
        "kwh/year": "kwh/y", "kwh": "kwh/y", "mwh/year": "mwh/y", "mwh": "mwh/y",
        "gj/year": "gj/y", "gj": "gj/y", "m3/year": "m3/y", "m3/y": "m3/y",
        "l/year": "l/y", "l/y": "l/y",
        "wet t/h": "t/h", "wet tonnes/h": "t/h", "t/h": "t/h",
        "nm3/h raw gas": "nm3/h", "nm3/h": "nm3/h",
        "m3/hr": "m3/h", "m3/h": "m3/h", "kg/hr": "kg/h", "kg/h": "kg/h",
        "kw electric": "kw", "kwe": "kw", "kw": "kw", "kwth": "kwth",
        "working volume m3": "m3", "m3": "m3",
        "kg water evaporated/h": "kg/h", "kg water removed/h": "kg/h",
    }
    source, target = aliases.get(source, source), aliases.get(target, target)
    if source == target:
        return value
    conversions = {
        ("kg/y", "t/y"): 1 / 1000.0, ("t/y", "kg/y"): 1000.0,
        ("mwh/y", "kwh/y"): 1000.0, ("kwh/y", "mwh/y"): 1 / 1000.0,
        ("gj/y", "kwh/y"): 1 / 0.0036, ("kwh/y", "gj/y"): 0.0036,
        ("m3/y", "l/y"): 1000.0, ("l/y", "m3/y"): 1 / 1000.0,
    }
    factor = conversions.get((source, target))
    return None if factor is None else value * factor


def _cost_denominator(unit: str | None) -> str | None:
    text = str(unit or "").lower()
    if "eur/" not in text:
        return None
    denominator = text.split("eur/", 1)[1].split(";", 1)[0].strip()
    denominator = denominator.replace(" excl vat", "").replace(" useful", "")
    if denominator.startswith(("kwh", "kwhth")):
        return "kWh/year"
    if denominator.startswith("m3"):
        return "m3/year"
    if denominator.startswith("t ") or denominator.startswith("t/") or "tonne" in denominator:
        return "t/year"
    if denominator.startswith("kg"):
        return "kg/year"
    if "paid hour" in denominator:
        return "paid hour"
    if "pollution unit" in denominator:
        return "pollution unit/year"
    if "set/year" in denominator:
        return "set/year"
    if "l resin" in denominator or denominator.startswith("l"):
        return "L/year"
    if "m2" in denominator:
        return "m2/year"
    return denominator


def _object_payload(value: object) -> dict[str, Any]:
    if isinstance(value, Mapping):
        return dict(value)
    if hasattr(value, "to_dict"):
        return dict(value.to_dict())
    if is_dataclass(value):
        return asdict(value)
    raise TypeError(f"Unsupported dynamic TEA result type: {type(value).__name__}")


def _dynamic_unit_ids(payload: Mapping[str, object]) -> list[str]:
    ids: set[str] = set()
    for step in payload.get("steps", ()) or ():
        if not isinstance(step, Mapping):
            step = _object_payload(step)
        for key in ("drying", "ad", "gas_route"):
            value = step.get(key)
            if isinstance(value, Mapping) and value.get("unit_id"):
                ids.add(str(value["unit_id"]))
        for value in step.get("resource_recovery", ()) or ():
            if isinstance(value, Mapping) and value.get("unit_id"):
                ids.add(str(value["unit_id"]))
    return sorted(ids)


def _metric_to_base(metric: object, kind: str) -> float | None:
    if not isinstance(metric, Mapping):
        return None
    if kind == "mass":
        if metric.get("kg_per_year") is not None:
            return float(metric["kg_per_year"])
        if metric.get("tonnes_per_year") is not None:
            return float(metric["tonnes_per_year"]) * 1000.0
    if kind == "normal_gas":
        if metric.get("Nm3_per_year") is not None:
            return float(metric["Nm3_per_year"])
    if kind == "gas":
        if metric.get("m3_per_year") is not None:
            return float(metric["m3_per_year"])
    return None


def _energy_metric(metric: object, kind: str) -> float | None:
    if not isinstance(metric, Mapping):
        return None
    if kind == "electricity":
        if metric.get("kWh_per_year") is not None:
            return float(metric["kWh_per_year"])
        if metric.get("MWh_per_year") is not None:
            return float(metric["MWh_per_year"]) * 1000.0
    if kind == "heat":
        if metric.get("kWh_per_year") is not None:
            return float(metric["kWh_per_year"])
        if metric.get("GJ_per_year") is not None:
            return float(metric["GJ_per_year"]) / 0.0036
    return None


def _coerce_project_basis(value: TEAProjectBasis | Mapping[str, object] | None) -> TEAProjectBasis:
    if value is None:
        return TEAProjectBasis()
    if isinstance(value, TEAProjectBasis):
        return value
    if isinstance(value, Mapping):
        return TEAProjectBasis(**dict(value))
    raise TypeError("project_basis must be TEAProjectBasis, a mapping, or null.")


def _coerce_financial_assumptions(
    value: TEAFinancialAssumptions | Mapping[str, object] | None,
) -> TEAFinancialAssumptions:
    if value is None:
        return TEAFinancialAssumptions()
    if isinstance(value, TEAFinancialAssumptions):
        return value
    if isinstance(value, Mapping):
        return TEAFinancialAssumptions(**dict(value))
    raise TypeError(
        "financial_assumptions must be TEAFinancialAssumptions, a mapping, or null."
    )


_SALEABLE_PRODUCTS = {
    "dry_protein_product",
    "dried_protein_product",
    "biostimulant_product",
    "biomethane",
    "biomethane_product",
    "press_cake",
    "phosphorus_product",
    "struvite_candidate",
    "struvite_product",
    "ammonium_product",
    "potassium_concentrate",
    "recovered_water",
    "nutrient_rich_solids",
    "ion_exchange_product",
}

_PRODUCT_ALIASES = {
    "dry_protein_product": ("dry_protein_product", "dried_protein_product"),
    "dried_protein_product": ("dried_protein_product", "dry_protein_product"),
    "biomethane": ("biomethane", "biomethane_product"),
    "biomethane_product": ("biomethane_product", "biomethane"),
    "phosphorus_product": ("phosphorus_product", "struvite_candidate", "struvite_product"),
    "struvite_candidate": ("struvite_candidate", "struvite_product", "phosphorus_product"),
    "struvite_product": ("struvite_product", "struvite_candidate", "phosphorus_product"),
}


def _canonical_product_id(product_id: str) -> str:
    if product_id in {"dry_protein_product", "dried_protein_product"}:
        return "dry_protein_product"
    if product_id in {"biomethane", "biomethane_product"}:
        return "biomethane"
    if product_id in {"phosphorus_product", "struvite_candidate", "struvite_product"}:
        return "phosphorus_product"
    return product_id


def _product_price_lines(
    measures: Mapping[str, object],
    basis: TEAProjectBasis,
    finance: TEAFinancialAssumptions,
    register_revenue_lines: Sequence[Mapping[str, object]],
    *,
    model_type: str,
) -> tuple[
    list[dict[str, object]],
    list[dict[str, object]],
    str,
    list[dict[str, object]],
]:
    prices = {}
    for item in normalize_product_prices(finance.product_prices):
        canonical = _canonical_product_id(item.product_id)
        if canonical in prices:
            raise ValueError(f"Duplicate product-price aliases for {canonical}; supply one price per product.")
        prices[canonical] = item
    detected = _detected_saleable_products(measures)
    required = list(finance.revenue_product_ids) if finance.revenue_product_ids else detected
    canonical_required = [_canonical_product_id(item) for item in required]
    if len(set(canonical_required)) != len(canonical_required):
        raise ValueError("revenue_product_ids contains duplicate aliases for the same product.")
    non_sale = {_canonical_product_id(name): reason for name, reason in finance.non_sale_product_reasons.items()}
    lines: list[dict[str, object]] = []
    missing: list[dict[str, object]] = []
    traceability: list[dict[str, object]] = []
    calculated = 0
    # An explicit subset is a revenue scope, not evidence that other products
    # have no value or disposal liability. Such products remain disclosed.
    omitted = [name for name in detected if _canonical_product_id(name) not in canonical_required]
    for product_id in omitted:
        if _canonical_product_id(product_id) not in non_sale:
            missing.append({"cost_id": f"PRODUCT-PRICE-{_slug(product_id).upper()}", "code": "omitted_product_disposition", "required_input": f"Price or non_sale_product_reasons for {product_id}; omitted from explicit revenue scope."})
    for product_id in required:
        if _canonical_product_id(product_id) in non_sale:
            if _canonical_product_id(product_id) in prices:
                raise ValueError(f"{product_id} cannot have both a price and a non-sale disposition.")
            calculated += 1
            continue
        if _register_revenue_covers(product_id, register_revenue_lines):
            calculated += 1
            continue
        price = prices.get(_canonical_product_id(product_id))
        if price is None:
            missing.append(
                {
                    "cost_id": f"PRODUCT-PRICE-{_slug(product_id).upper()}",
                    "process_step": "Product revenue",
                    "code": "missing_product_price",
                    "required_input": product_id,
                }
            )
            continue
        if price.quality_basis == 'matched_specification':
            actual_quality = next((basis.product_quality[alias] for alias in _PRODUCT_ALIASES.get(product_id, (product_id,)) if alias in basis.product_quality), {})
            mismatches = [key for key, value in price.quality_requirements.items() if actual_quality.get(key) != value]
            if mismatches:
                missing.append({'cost_id':f'PRODUCT-PRICE-{_slug(product_id).upper()}', 'code':'unmatched_product_quality', 'required_input':', '.join(mismatches)})
                continue
        if price.quantity_component:
            mass = measures.get('annual_product_components_kg', {}).get(_canonical_product_id(product_id), {}).get(price.quantity_component)
            quantity = None if mass is None else (mass, 'kg/year', f'confirmed_component:{price.quantity_component}; dry pure-compound equivalent, finishing/grade unverified')
        elif _canonical_product_id(product_id) == 'biomethane' and price.gas_reference_temperature_k is not None:
            from .sale_quantities import reference_volume_m3
            moles = measures.get('annual_dry_gas_kmol', {}).get('biomethane')
            quantity = None if moles is None else (reference_volume_m3(moles, price.gas_reference_temperature_k, price.gas_reference_pressure_pa), 'm3/year', f'dry gas at {price.gas_reference_temperature_k} K and {price.gas_reference_pressure_pa} Pa; ideal-gas reference conversion')
        else:
            quantity = _annual_product_quantity(product_id, price.unit, measures, basis)
        if quantity is None:
            missing.append(
                {
                    "cost_id": f"PRODUCT-PRICE-{_slug(product_id).upper()}",
                    "process_step": "Product revenue",
                    "code": "missing_dynamic_product_quantity"
                    if model_type == "dynamic"
                    else "missing_product_quantity",
                    "required_input": f"annual {product_id} quantity compatible with {price.unit}",
                }
            )
            continue
        value, unit, source = quantity
        price_basis = _product_price_basis(price.unit)
        converted = _convert_product_quantity(value, unit, price_basis)
        if converted is None:
            missing.append(
                {
                    "cost_id": f"PRODUCT-PRICE-{_slug(product_id).upper()}",
                    "process_step": "Product revenue",
                    "code": "incompatible_product_price_unit",
                    "required_input": f"{unit} -> {price.unit}",
                }
            )
            continue
        revenue = converted * float(price.value_eur_per_unit)
        cost_id = f"PRODUCT-PRICE-{_slug(product_id).upper()}"
        lines.append(
            {
                "cost_id": cost_id,
                "process_area": "products",
                "process_step": "Product revenue",
                "equipment_or_cost_item": price.display_name or product_id,
                "cost_type": "revenue",
                "alternative_group": None,
                "route_tags": [],
                "confidence": price.source_status,
                "reference_value_eur": price.value_eur_per_unit,
                "reference_unit": price.unit,
                "quantity": converted,
                "quantity_unit": price_basis,
                "quantity_source": source,
                "unit_cost_eur": price.value_eur_per_unit,
                "annual_revenue_eur": revenue,
                "calculation_status": "calculated_from_explicit_product_price",
                "source_status": price.source_status,
                "warning": price.notes,
                "product_id": product_id,
                "quantity_component": price.quantity_component,
                "gas_reference_temperature_k": price.gas_reference_temperature_k,
                "gas_reference_pressure_pa": price.gas_reference_pressure_pa,
            }
        )
        traceability.append(
            {
                **price.to_dict(),
                "policy_id": f"tea.product_price.{product_id}",
                "cost_id": cost_id,
                "source_title": price.source_title,
                "source_url": price.source_url,
                "confidence": price.source_status,
                "source_status": price.source_status,
                "source_sheet": "explicit_financial_assumptions",
                "source_row": None,
            }
        )
        calculated += 1
    if missing:
        status = "partial" if calculated else "incomplete"
    elif not required:
        status = "complete"
    elif calculated == len(required):
        status = "complete"
    elif calculated:
        status = "partial"
    else:
        status = "incomplete"
    return lines, missing, status, traceability


def _detected_saleable_products(measures: Mapping[str, object]) -> list[str]:
    found: list[str] = [
        str(name) for name in measures.get("detected_saleable_products", ())
    ]
    for collection in ("annual_products_kg", "annual_products_m3", "annual_products_nm3"):
        values = measures.get(collection, {})
        if not isinstance(values, Mapping):
            continue
        for name, value in values.items():
            if _number(value) != 0 and _slug(str(name)) in _SALEABLE_PRODUCTS and str(name) not in found:
                found.append(str(name))
    unique: dict[str, str] = {}
    for name in found:
        unique.setdefault(_canonical_product_id(name), name)
    return list(unique.values())


def _register_revenue_covers(
    product_id: str, lines: Sequence[Mapping[str, object]]
) -> bool:
    aliases = _PRODUCT_ALIASES.get(product_id, (product_id,))
    return any(
        line.get("annual_revenue_eur") is not None
        and any(_slug(alias) in _slug(str(line.get("equipment_or_cost_item", ""))) for alias in aliases)
        for line in lines
    )


def _annual_product_quantity(
    product_id: str,
    price_unit: str,
    measures: Mapping[str, object],
    basis: TEAProjectBasis,
) -> tuple[float, str, str] | None:
    aliases = _PRODUCT_ALIASES.get(product_id, (product_id,))
    for alias in aliases:
        raw = basis.annual_quantities.get(alias)
        if raw is not None:
            value, unit = _quantity_value(raw, _product_price_basis(price_unit))
            return value, unit, "explicit_project_basis"
    price_basis = _product_price_basis(price_unit)
    target = 'annual_products_nm3' if price_basis == 'Nm3/year' else "annual_products_m3" if price_basis in {"m3/year", "L/year"} else "annual_products_kg"
    values = measures.get(target, {})
    if isinstance(values, Mapping):
        for alias in aliases:
            if alias in values and _number(values[alias]) is not None:
                unit = 'm3/year' if target == 'annual_products_m3' else price_basis if target == 'annual_products_nm3' else 'kg/year'
                return float(values[alias]), unit, "simulation_product_output"
    return None


def _product_price_basis(unit: str) -> str:
    normalized = unit.strip().lower().replace(" ", "")
    if normalized in {"eur/t", "eur/tonne", "€/t", "€/tonne"}:
        return "t/year"
    if normalized in {'eur/nm3','€/nm3'}:
        return 'Nm3/year'
    if normalized in {"eur/m3", "€/m3"}:
        return "m3/year"
    if normalized in {"eur/l", "€/l"}:
        return "L/year"
    return "kg/year"


def _convert_product_quantity(value: float, unit: str, target: str) -> float | None:
    return _convert_unit(value, unit, target)


def _annual_protein_product_kg(measures: Mapping[str, object]) -> float | None:
    products = measures.get("annual_products_kg", {})
    if not isinstance(products, Mapping):
        return None
    for name in ("dry_protein_product", "dried_protein_product"):
        if _number(products.get(name)) is not None:
            return float(products[name])
    return None


def _annual_biomethane_nm3(measures: Mapping[str, object]) -> float | None:
    products = measures.get("annual_products_nm3", {})
    if not isinstance(products, Mapping):
        return None
    for name in ("biomethane", "biomethane_product"):
        if _number(products.get(name)) is not None:
            return float(products[name])
    return None


def _replacement_schedule(
    selected_records: Sequence[TEACostRecord],
    capex_lines: Sequence[Mapping[str, object]],
    finance: TEAFinancialAssumptions,
) -> list[dict[str, object]]:
    if finance.project_lifetime_years is None:
        return []
    line_by_id = {str(line["cost_id"]): line for line in capex_lines}
    events: list[dict[str, object]] = []
    for record in selected_records:
        if record.cost_type != "capex":
            continue
        installed = _number(line_by_id.get(record.cost_id, {}).get("installed_cost_eur"))
        if installed is None:
            continue
        years = tuple(finance.replacement_years_by_cost_id.get(record.cost_id, ()))
        source = "explicit_financial_assumption"
        replacement_interval = record.lifetime_years
        if replacement_interval is None and record.replacement_frequency:
            match = re.search(
                r"([0-9]+(?:\.[0-9]+)?)\s*(?:year|yr)",
                record.replacement_frequency.lower(),
            )
            replacement_interval = float(match.group(1)) if match else None
        if not years and replacement_interval and replacement_interval > 0:
            interval = int(round(replacement_interval))
            if abs(interval - replacement_interval) <= 1e-9:
                years = tuple(
                    range(interval, int(finance.project_lifetime_years), interval)
                )
                source = "cost_register_lifetime_or_replacement_frequency"
        fraction = float(finance.replacement_cost_fraction_by_cost_id.get(record.cost_id, 1.0))
        for year in years:
            if year <= int(finance.project_lifetime_years):
                events.append(
                    {
                        "cost_id": record.cost_id,
                        "year": year,
                        "replacement_cost_fraction": fraction,
                        "replacement_capex_eur": installed * fraction,
                        "source": source,
                        "warning": "Full installed-cost replacement is used unless an explicit cost fraction is supplied.",
                    }
                )
    return sorted(events, key=lambda item: (int(item["year"]), str(item["cost_id"])))


def _selected_summary(record: TEACostRecord) -> dict[str, object]:
    return {
        "cost_id": record.cost_id,
        "process_area": record.process_area,
        "process_step": record.process_step,
        "equipment_or_cost_item": record.equipment_or_cost_item,
        "cost_type": record.cost_type,
        "alternative_group": record.alternative_group,
        "route_tags": list(record.scenario_or_route_tags),
        "confidence": record.confidence,
    }


def _line_base(record: TEACostRecord) -> dict[str, object]:
    return {
        **_selected_summary(record),
        "reference_value_eur": record.reference_value_eur,
        "reference_unit": record.reference_unit,
        "reference_capacity": record.reference_capacity,
        "capacity_unit": record.capacity_unit,
        "scaling_exponent": record.scaling_exponent,
        "source_status": record.source_status,
        "warning": record.notes,
    }


def _excluded(record: TEACostRecord, reason: str) -> dict[str, object]:
    return {
        "cost_id": record.cost_id,
        "equipment_or_cost_item": record.equipment_or_cost_item,
        "alternative_group": record.alternative_group,
        "reason": reason,
    }


def _missing(record: TEACostRecord, code: str, required_input: str) -> dict[str, object]:
    return {
        "cost_id": record.cost_id,
        "code": code,
        "required_input": required_input,
        "message": f"{record.equipment_or_cost_item}: {required_input} is required; no value was invented.",
    }


def _number(value: object) -> float | None:
    if value is None or isinstance(value, bool):
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number if isfinite(number) else None


def _slug(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", str(value).lower()).strip("_")


def _norm_unit(value: str | None) -> str:
    return re.sub(r"\s+", " ", str(value or "").strip().lower())


__all__ = (
    "TEAFinancialAssumptions",
    "TEAProjectBasis",
    "TEAProductPrice",
    "TEAReport",
    "calculate_dynamic_tea",
    "calculate_empirical_tea",
)
