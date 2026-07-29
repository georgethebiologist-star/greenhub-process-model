"""CSV and Excel reporting for Phase 7 nutrient recovery."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Mapping

import biosteam as bst
import pandas as pd

from Greenhub.analytical import calculate_elemental_flows
from Greenhub.chemicals import chemicals
from Greenhub.component_groups import COMPONENT_GROUPS
from Greenhub.component_metadata import COMPONENT_METADATA
from Greenhub.phase4_validation import sum_stream_component_flows
from Greenhub.phase6_reporting import _format_workbook, _write_unit_tables
from Greenhub.phase7_limitations import phase7_limitation_rows
from Greenhub.reporting_io import atomic_excel_writer
from Greenhub.scenarios import NUTRIENT_RECOVERY_SCENARIOS
from Greenhub.settings import RESULTS_DIR, ensure_results_dir


def _stream_rows(stream) -> list[dict[str, object]]:
    rows = []
    for component_id in chemicals.IDs:
        flow = float(stream.imass[component_id])
        if flow != 0.0:
            rows.append(
                {
                    "stream": stream.ID,
                    "component": component_id,
                    "flow_kg_hr": flow,
                    "phase": stream.phase,
                    "temperature_k": stream.T,
                    "pressure_pa": stream.P,
                }
            )
    if not rows:
        rows.append(
            {
                "stream": stream.ID,
                "component": None,
                "flow_kg_hr": 0.0,
                "phase": stream.phase,
                "temperature_k": stream.T,
                "pressure_pa": stream.P,
            }
        )
    return rows


def _unit_rows(model, unit_ids: Iterable[str]) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for unit_id in unit_ids:
        unit = model.units.get(unit_id)
        if unit is None:
            continue
        base = {
            "unit_id": unit.ID,
            "operation": unit.line,
            "inlets": ", ".join(stream.ID for stream in unit.ins),
            "outlets": ", ".join(stream.ID for stream in unit.outs),
            "power_kw": float(unit.power_utility.consumption),
            "net_heat_kw": sum(float(utility.duty) for utility in unit.heat_utilities) / 3600.0,
            "purchase_cost": sum(unit.purchase_costs.values()) if unit.purchase_costs else None,
            "cost_basis": (
                "BioSTEAM built-in correlation"
                if unit.purchase_costs
                else "no approved custom Phase 7 CAPEX basis"
            ),
            "warnings": " | ".join(getattr(unit, "warnings", ())),
            "limitation_ids": "; ".join(getattr(unit, "limitation_ids", ())),
        }
        if unit.design_results:
            for name, value in unit.design_results.items():
                rows.append(
                    {
                        **base,
                        "design_item": name,
                        "design_value": value,
                        "design_unit": getattr(unit, "_units", {}).get(name),
                    }
                )
        else:
            rows.append({**base, "design_item": None, "design_value": None, "design_unit": None})
    return rows or [{"status": "not active in selected scenario"}]


def _separation_rows(model) -> list[dict[str, object]]:
    separator = model.units.get("S701")
    if separator is None:
        return [{"status": "not active in selected scenario"}]
    rows = []
    for component_id in chemicals.IDs:
        feed = float(separator.ins[0].imass[component_id])
        if feed == 0.0:
            continue
        solids = float(separator.outs[0].imass[component_id])
        rows.append(
            {
                "technology": separator.technology,
                "component": component_id,
                "feed_kg_hr": feed,
                "solids_kg_hr": solids,
                "centrate_kg_hr": float(separator.outs[1].imass[component_id]),
                "fraction_to_solids": solids / feed,
                "physical_class": (
                    "suspended" if component_id in COMPONENT_GROUPS["suspended_solids"] else "dissolved/entrained"
                ),
            }
        )
    return rows


def _product_quality_rows(model) -> list[dict[str, object]]:
    names = (
        "nutrient_rich_solids",
        "phosphorus_product",
        "ammonium_product",
        "potassium_concentrate",
        "treated_water",
        "residual_liquor",
        "phase7_wastewater",
        "phase7_offgas",
    )
    rows: list[dict[str, object]] = []
    for name in names:
        stream = model.streams.get(name)
        if stream is None:
            continue
        dry_mass = stream.F_mass - float(stream.imass["Water"])
        for component_id in chemicals.IDs:
            flow = float(stream.imass[component_id])
            if flow == 0.0:
                continue
            metadata = COMPONENT_METADATA[component_id]
            rows.append(
                {
                    "product_or_residual": name,
                    "stream_id": stream.ID,
                    "component": component_id,
                    "flow_kg_hr": flow,
                    "wet_mass_fraction": flow / stream.F_mass if stream.F_mass else 0.0,
                    "mg_per_kg_dry_product": flow * 1e6 / dry_mass if dry_mass > 0.0 else None,
                    "nitrogen_kg_hr": flow * metadata.nitrogen_mass_fraction,
                    "phosphorus_kg_hr": flow * metadata.phosphorus_mass_fraction,
                    "potassium_kg_hr": flow * metadata.potassium_mass_fraction,
                    "magnesium_kg_hr": flow * metadata.magnesium_mass_fraction,
                    "calcium_kg_hr": flow * metadata.calcium_mass_fraction,
                    "sulfur_kg_hr": flow * metadata.sulfur_mass_fraction,
                    "chloride_kg_hr": flow * metadata.chloride_mass_fraction,
                    "is_contaminant_pool": component_id in COMPONENT_GROUPS["contaminants"],
                    "regulatory_status": "not assessed",
                }
            )
    return rows or [{"status": "no Phase 7 products in selected scenario"}]


def _reagent_rows(model) -> list[dict[str, object]]:
    rows = []
    for stream in model.external_inputs:
        for component_id in chemicals.IDs:
            flow = float(stream.imass[component_id])
            if flow != 0.0:
                rows.append(
                    {
                        "stream": stream.ID,
                        "component": component_id,
                        "flow_kg_hr": flow,
                        "role": (
                            "process water"
                            if component_id == "Water"
                            else "carrier gas"
                            if component_id in {"Oxygen", "Nitrogen"}
                            else "chemical reagent"
                        ),
                    }
                )
    return rows or [{"status": "no Phase 7 external reagent in selected scenario"}]


def _mass_balance_rows(model) -> list[dict[str, object]]:
    validation = model.validation
    rows = [
        {
            "basis": "total mass",
            "component": "TOTAL",
            "boundary_in_kg_hr": validation.boundary_in_kg_hr,
            "boundary_out_kg_hr": validation.boundary_out_kg_hr,
            "residual_kg_hr": validation.overall_error_kg_hr,
        }
    ]
    outlet = sum_stream_component_flows(model.boundary_outputs)
    for component_id, error in validation.component_errors_kg_hr.items():
        expected = float(outlet[component_id]) + float(error)
        if expected != 0.0 or outlet[component_id] != 0.0 or error != 0.0:
            rows.append(
                {
                    "basis": "reaction-adjusted component",
                    "component": component_id,
                    "boundary_in_kg_hr": expected,
                    "boundary_out_kg_hr": outlet[component_id],
                    "residual_kg_hr": error,
                }
            )
    return rows


def _element_rows(model) -> list[dict[str, object]]:
    validation = model.validation
    return [
        {
            "element": element,
            "in_kg_hr": validation.element_in_kg_hr[element],
            "out_kg_hr": validation.element_out_kg_hr[element],
            "residual_kg_hr": validation.element_errors_kg_hr[element],
        }
        for element in validation.element_in_kg_hr
    ]


def _element_destination_rows(model, element: str) -> list[dict[str, object]]:
    rows = [
        {
            "location": "complete Phase 7 boundary",
            "direction": "input",
            "element": element,
            "flow_kg_hr": model.validation.element_in_kg_hr[element],
        }
    ]
    for stream in model.boundary_outputs:
        flow = calculate_elemental_flows(sum_stream_component_flows((stream,)))[element]
        rows.append(
            {
                "location": stream.ID,
                "direction": "output",
                "element": element,
                "flow_kg_hr": flow,
            }
        )
    rows.append(
        {
            "location": "balance residual",
            "direction": "residual",
            "element": element,
            "flow_kg_hr": model.validation.element_errors_kg_hr[element],
        }
    )
    return rows


def _energy_rows(model) -> list[dict[str, object]]:
    rows = []
    for unit_id in model.parameters["phase7_unit_ids"]:
        unit = model.units[unit_id]
        inlet_enthalpy = sum(float(stream.H) for stream in unit.ins)
        outlet_enthalpy = sum(float(stream.H) for stream in unit.outs)
        heating = sum(max(0.0, float(utility.duty)) for utility in unit.heat_utilities) / 3600.0
        cooling = -sum(min(0.0, float(utility.duty)) for utility in unit.heat_utilities) / 3600.0
        rows.append(
            {
                "unit_id": unit_id,
                "operation": unit.line,
                "inlet_enthalpy_kj_hr": inlet_enthalpy,
                "outlet_enthalpy_kj_hr": outlet_enthalpy,
                "heating_kw": heating,
                "cooling_kw": cooling,
                "gross_reported_heat_kw": float(getattr(unit, "gross_heat_kw", 0.0)),
                "heat_loss_at_feed_temperature_kw": float(
                    unit.design_results.get("Heat loss at feed temperature", 0.0)
                ),
                "neutralization_heat_kw": float(getattr(unit, "neutralization_heat_kw", 0.0)),
                "electricity_kw": float(unit.power_utility.consumption),
                "energy_balance_scope": "steady-state unit interface; custom-unit enthalpy rigor is screening-level",
            }
        )
    return rows or [{"status": "no Phase 7 equipment in selected scenario"}]


def _utility_rows(model) -> list[dict[str, object]]:
    names = (
        "gross_electricity_kw",
        "chp_electricity_available_kw",
        "chp_electricity_used_kw",
        "grid_electricity_kw",
        "net_electricity_export_kw",
        "gross_heat_demand_kw",
        "temperature_eligible_heat_demand_kw",
        "recovered_heat_available_kw",
        "recovered_heat_temperature_c",
        "recovered_heat_used_kw",
        "external_heat_kw",
        "cooling_demand_kw",
        "utility_interface_source",
    )
    return [{"metric": name, "value": model.metrics.get(name)} for name in names]


def _assumption_rows(model) -> list[dict[str, object]]:
    rows = [record.as_dict() for record in model.input_bundle.parameter_records]
    rows.extend(
        {
            "category": "model_boundary",
            "name": "documented model assumption",
            "python_name": "model_assumption",
            "value": assumption,
            "unit": None,
            "scenario": model.scenario.scenario_id,
            "month": model.input_bundle.selected_month,
            "required": True,
            "measurement_status": "calculated",
            "source_class": "E",
            "measured_or_assumed": "assumed",
            "active": True,
            "phase_introduced": 7,
            "comment": assumption,
        }
        for assumption in model.assumptions
    )
    return rows


@dataclass(frozen=True)
class Phase7ComparisonSnapshot:
    """Scenario values needed by the unranked engineering comparison."""

    scenario_id: str
    scenario_name: str
    process_order: str
    metrics: Mapping[str, object]


def snapshot_phase7_comparison(model) -> Phase7ComparisonSnapshot:
    """Detach comparison metrics from the complete simulated flowsheet graph."""

    return Phase7ComparisonSnapshot(
        scenario_id=model.scenario.scenario_id,
        scenario_name=model.scenario.name,
        process_order=model.input_bundle.process_order,
        metrics=dict(model.metrics),
    )


def _comparison_rows(models: Iterable[object]) -> list[dict[str, object]]:
    rows = []
    for model in models:
        snapshot = (
            model
            if isinstance(model, Phase7ComparisonSnapshot)
            else snapshot_phase7_comparison(model)
        )
        metrics = snapshot.metrics
        rows.append(
            {
                "scenario": snapshot.scenario_id,
                "scenario_name": snapshot.scenario_name,
                "process_order": snapshot.process_order,
                "digestate_kg_hr": metrics["digestate_processed_kg_hr"],
                "solid_product_kg_hr": metrics["nutrient_rich_solids_kg_hr"],
                "phosphorus_product_kg_hr": metrics["phosphorus_product_kg_hr"],
                "ammonium_product_kg_hr": metrics["ammonium_product_kg_hr"],
                "potassium_concentrate_kg_hr": metrics["potassium_concentrate_kg_hr"],
                "P_recovery_percent": 100.0 * float(metrics["total_p_recovery_fraction"]),
                "N_recovery_percent": 100.0 * float(metrics["total_n_recovery_fraction"]),
                "K_to_concentrate_percent": 100.0 * float(metrics["k_recovery_in_concentrate_fraction"]),
                "chemical_reagent_kg_hr": metrics["chemical_reagent_kg_hr"],
                "fresh_water_kg_hr": metrics["fresh_process_water_kg_hr"],
                "electricity_kw": metrics["gross_electricity_kw"],
                "gross_heat_kw": metrics["gross_heat_demand_kw"],
                "external_heat_kw": metrics["external_heat_kw"],
                "product_compliance_status": "not assessed",
                "input_quality": "class E structural baseline",
                "ranking_status": "not ranked",
            }
        )
    return rows


def _scenario_rows() -> list[dict[str, object]]:
    return [
        {
            "scenario": scenario.scenario_id,
            "name": scenario.name,
            "active": scenario.active,
            "default_order": scenario.default_order,
            "separation_enabled": scenario.separation_enabled,
            "phosphorus_route": scenario.phosphorus_route,
            "ammonia_route": scenario.ammonia_route,
            "potassium_route": scenario.potassium_route,
            "description": scenario.description,
        }
        for scenario in NUTRIENT_RECOVERY_SCENARIOS.values()
    ]


def save_phase7_reports(
    model,
    *,
    flowsheet_path: Path,
    scenario_models: tuple[object, ...],
    seasonal_result,
    results_dir: Path = RESULTS_DIR,
) -> dict[str, Path]:
    """Write selected-scenario, comparison, seasonal, and limitation reports."""

    ensure_results_dir()
    results_dir.mkdir(parents=True, exist_ok=True)
    limitations = phase7_limitation_rows(model)
    assumptions = _assumption_rows(model)
    seasonal_rows = list(seasonal_result.monthly_rows) if seasonal_result else []
    tables = {
        "phase7_digestate_feed.csv": pd.DataFrame(_stream_rows(model.streams["digestate_feed"])),
        "phase7_separation_report.csv": pd.DataFrame(_separation_rows(model)),
        "phase7_struvite_report.csv": pd.DataFrame(_unit_rows(model, ("R711", "S711", "W711", "D711"))),
        "phase7_calcium_phosphate_report.csv": pd.DataFrame(_unit_rows(model, ("R712", "S712", "W712", "D712"))),
        "phase7_ammonia_stripping_report.csv": pd.DataFrame(_unit_rows(model, ("M721", "H721", "A721"))),
        "phase7_acid_absorption_report.csv": pd.DataFrame(_unit_rows(model, ("A722", "V722"))),
        "phase7_ion_exchange_report.csv": pd.DataFrame(_unit_rows(model, ("A731", "R731"))),
        "phase7_potassium_report.csv": pd.DataFrame(_unit_rows(model, ("E741", "M741", "V741"))),
        "phase7_product_quality.csv": pd.DataFrame(_product_quality_rows(model)),
        "phase7_reagent_balance.csv": pd.DataFrame(_reagent_rows(model)),
        "phase7_mass_balance.csv": pd.DataFrame(_mass_balance_rows(model)),
        "phase7_nitrogen_balance.csv": pd.DataFrame(_element_destination_rows(model, "nitrogen")),
        "phase7_phosphorus_balance.csv": pd.DataFrame(_element_destination_rows(model, "phosphorus")),
        "phase7_potassium_balance.csv": pd.DataFrame(_element_destination_rows(model, "potassium")),
        "phase7_sulphur_balance.csv": pd.DataFrame(_element_destination_rows(model, "sulfur")),
        "phase7_chloride_balance.csv": pd.DataFrame(_element_destination_rows(model, "chloride")),
        "phase7_energy_balance.csv": pd.DataFrame(_energy_rows(model)),
        "phase7_utility_summary.csv": pd.DataFrame(_utility_rows(model)),
        "phase7_seasonal_summary.csv": pd.DataFrame(seasonal_rows),
        "phase7_assumptions.csv": pd.DataFrame(assumptions),
        "phase7_elemental_balance.csv": pd.DataFrame(_element_rows(model)),
        "phase7_model_limitations.csv": pd.DataFrame(limitations),
        "phase7_selected_metrics.csv": pd.DataFrame(model.metrics.items(), columns=["metric", "value"]),
    }
    paths: dict[str, Path] = {"flowsheet": flowsheet_path}
    for filename, table in tables.items():
        path = results_dir / filename
        table.to_csv(path, index=False)
        paths[filename] = path

    comparison_path = results_dir / "phase7_scenario_comparison.xlsx"
    comparison = pd.DataFrame(_comparison_rows(scenario_models))
    with atomic_excel_writer(comparison_path) as writer:
        comparison.to_excel(writer, sheet_name="Engineering comparison", index=False)
        comparison.set_index("scenario").transpose().rename_axis("metric").reset_index().to_excel(
            writer, sheet_name="Metrics by scenario", index=False
        )
        pd.DataFrame(_scenario_rows()).to_excel(writer, sheet_name="Scenario architecture", index=False)
        pd.DataFrame(
            [{
                "interpretation": (
                    "Engineering inventory comparison only. No alternative is ranked because "
                    "Phase 7 values are class-E placeholders, product eligibility is unverified, "
                    "the plant utility network is incomplete, and no decision method is active."
                )
            }]
        ).to_excel(writer, sheet_name="Read me", index=False)
        _format_workbook(writer.book)
    paths["scenario_comparison"] = comparison_path

    limitations_path = results_dir / "phase7_limitations_and_data_needs.xlsx"
    with atomic_excel_writer(limitations_path) as writer:
        pd.DataFrame(limitations).to_excel(writer, sheet_name="Limitation register", index=False)
        pd.DataFrame([row for row in limitations if row["priority"] == "high"]).to_excel(
            writer, sheet_name="High priority data", index=False
        )
        pd.DataFrame(assumptions).to_excel(writer, sheet_name="Selected assumptions", index=False)
        pd.DataFrame(_scenario_rows()).to_excel(writer, sheet_name="Scenario architecture", index=False)
        _format_workbook(writer.book)
    paths["limitations_and_data_needs"] = limitations_path

    report_path = results_dir / "phase7_nutrient_recovery_report.xlsx"
    with atomic_excel_writer(report_path) as writer:
        tables["phase7_selected_metrics.csv"].to_excel(writer, sheet_name="Overview", index=False)
        pd.DataFrame([{
            "scenario": model.scenario.scenario_id,
            "name": model.scenario.name,
            "process_order": model.input_bundle.process_order,
            "upstream_chain": (
                f"{model.input_bundle.phase3_scenario_id}/"
                f"{model.input_bundle.phase4_scenario_id}/"
                f"{model.input_bundle.phase5_scenario_id}/"
                f"{model.input_bundle.phase6_scenario_id}"
            ),
            "month": model.input_bundle.selected_month,
            "structural_test_mode": model.input_bundle.structural_test_mode,
            "ranking": "not ranked",
        }]).to_excel(writer, sheet_name="Scenario", index=False)
        tables["phase7_digestate_feed.csv"].to_excel(writer, sheet_name="Digestate feed", index=False)
        tables["phase7_separation_report.csv"].to_excel(writer, sheet_name="Separation", index=False)
        pd.concat(
            [tables["phase7_struvite_report.csv"], tables["phase7_calcium_phosphate_report.csv"]],
            ignore_index=True,
        ).to_excel(writer, sheet_name="Phosphorus recovery", index=False)
        pd.concat(
            [tables["phase7_ammonia_stripping_report.csv"], tables["phase7_acid_absorption_report.csv"], tables["phase7_ion_exchange_report.csv"]],
            ignore_index=True,
        ).to_excel(writer, sheet_name="Ammonia recovery", index=False)
        tables["phase7_potassium_report.csv"].to_excel(writer, sheet_name="Potassium concentration", index=False)
        tables["phase7_product_quality.csv"].to_excel(writer, sheet_name="Products", index=False)
        tables["phase7_reagent_balance.csv"].to_excel(writer, sheet_name="Reagent use", index=False)
        tables["phase7_utility_summary.csv"].to_excel(writer, sheet_name="Utilities", index=False)
        tables["phase7_energy_balance.csv"].to_excel(writer, sheet_name="Energy balance", index=False)
        tables["phase7_mass_balance.csv"].to_excel(writer, sheet_name="Mass balances", index=False)
        tables["phase7_elemental_balance.csv"].to_excel(writer, sheet_name="Elemental balances", index=False)
        pd.DataFrame(seasonal_rows).to_excel(writer, sheet_name="Seasonal results", index=False)
        pd.DataFrame([seasonal_result.annual_totals] if seasonal_result else []).to_excel(
            writer, sheet_name="Annual totals", index=False
        )
        pd.DataFrame([seasonal_result.peak_design] if seasonal_result else []).to_excel(
            writer, sheet_name="Peak design", index=False
        )
        pd.DataFrame({"warning": model.validation.warnings}).to_excel(writer, sheet_name="Warnings", index=False)
        pd.DataFrame(assumptions).to_excel(writer, sheet_name="Assumptions", index=False)
        pd.DataFrame(limitations).to_excel(writer, sheet_name="Limitations", index=False)
        model.system.results().to_excel(writer, sheet_name="System results")
        bst.report.stream_table(
            model.system.streams,
            flow="kg/hr",
            percent=False,
            T="K",
            P="Pa",
        ).to_excel(writer, sheet_name="Stream table")
        _write_unit_tables(
            writer,
            "Unit results",
            bst.report.unit_result_tables(
                model.system.units,
                include_utilities=True,
                include_total_cost=True,
                include_installed_cost=True,
            ),
        )
        _format_workbook(writer.book)
    paths["nutrient_recovery_report"] = report_path
    return paths
