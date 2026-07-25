"""Detailed CSV and Excel reporting for GreenHub Phase 5."""

from __future__ import annotations

from dataclasses import asdict
from pathlib import Path

import biosteam as bst
import pandas as pd

from Greenhub.analytical import calculate_analytical_indicators
from Greenhub.chemicals import chemicals
from Greenhub.component_groups import COMPONENT_GROUPS
from Greenhub.component_metadata import COMPONENT_METADATA
from Greenhub.phase4_validation import (
    _adjust_plant_inventory,
    _apply_delta_ledger,
    stream_component_flows,
    sum_stream_component_flows,
)
from Greenhub.phase5_limitations import limitation_rows
from Greenhub.phase5_specifications import normal_volume_m3
from Greenhub.reporting import _format_workbook, _write_unit_tables
from Greenhub.scenarios import DIGESTION_SCENARIOS
from Greenhub.settings import RESULTS_DIR, ensure_results_dir


def _stream_rows(stream) -> list[dict[str, object]]:
    total = float(stream.F_mass)
    dry = total - float(stream.imass["Water"])
    return [
        {
            "stream_id": stream.ID,
            "component_id": ID,
            "flow_kg_hr": float(stream.imass[ID]),
            "mass_fraction_wet": float(stream.imass[ID]) / total if total else 0.0,
            "mass_fraction_dry": float(stream.imass[ID]) / dry if dry and ID != "Water" else 0.0,
            "category": COMPONENT_METADATA[ID].category,
            "subcategory": COMPONENT_METADATA[ID].subcategory,
            "cod_kg_o2_hr": float(stream.imass[ID]) * (COMPONENT_METADATA[ID].cod_factor or 0.0),
        }
        for ID in chemicals.IDs
    ]


def _feed_characterization_rows(model) -> list[dict[str, object]]:
    stream = model.streams["digester_feed"]
    density = float(model.parameters["values"].get("phase5_feed_density_kg_m3", 1000.0))
    volume = stream.F_mass / density if density else 0.0
    indicators = calculate_analytical_indicators(
        stream_component_flows(stream),
        volumetric_flow_m3_hr=volume,
    )
    rows = [
        {
            "record_type": "component",
            "name": row["component_id"],
            "value": row["flow_kg_hr"],
            "unit": "kg/hr",
            "concentration_g_L": row["flow_kg_hr"] / volume if volume else None,
            "status": "calculated from upstream stream",
        }
        for row in _stream_rows(stream)
    ]
    rows.extend(
        {
            "record_type": "analytical_indicator",
            "name": name,
            "value": value,
            "unit": "see indicator name",
            "concentration_g_L": None,
            "status": "derived from component metadata",
        }
        for name, value in indicators.items()
    )
    return rows


def _conditioning_rows(model) -> list[dict[str, object]]:
    unit = model.units["M501"]
    p = unit.parameters
    return [{
        "scenario": model.scenario.scenario_id,
        "enabled": p.enabled,
        "method": p.method,
        "inlet_pH_metadata": unit.inlet_pH,
        "target_pH_metadata": unit.outlet_pH,
        "base_type": p.base_type,
        "base_solution_mass_fraction": p.base_solution_mass_fraction,
        "base_purity": p.base_purity,
        "pure_base_kg_hr": unit.pure_base_kg_hr,
        "base_solution_kg_hr": unit.base_solution_kg_hr,
        "reagent_water_kg_hr": unit.reagent_water_kg_hr,
        "dilution_water_kg_hr": unit.dilution_water_kg_hr,
        "trace_nutrients_kg_hr": unit.ins[3].F_mass,
        "electricity_kw": float(unit.power_utility.consumption),
        "limitation": "pH is metadata; no buffering or electrolyte calculation",
    }]


def _design_rows(model) -> list[dict[str, object]]:
    unit = model.units["R501"]
    row: dict[str, object] = {
        "scenario": model.scenario.scenario_id,
        "digester_type": model.scenario.digester_type,
        "temperature_mode": model.scenario.temperature_mode,
        "calculation_mode": unit.parameters.calculation_mode,
        "enabled": unit.parameters.enabled,
        "capex_available": False,
        "design_status": "structural screening only",
    }
    for prefix, result in (
        ("sizing", unit.sizing_result),
        ("geometry", unit.geometry_result),
        ("heat", unit.heat_result),
    ):
        if result is not None:
            row.update({f"{prefix}_{key}": value for key, value in asdict(result).items()})
    row.update({f"design_{key}": value for key, value in unit.design_results.items()})
    return [row]


def _stoichiometry_rows(model) -> list[dict[str, object]]:
    unit = model.units["R501"]
    rows = [dict(row, record_type="component_fate") for row in unit.component_fates]
    rows.extend(
        {
            "record_type": "reaction_delta",
            "component_id": ID,
            "inlet_kg_hr": float(unit.ins[0].imass[ID]),
            "converted_kg_hr": -min(0.0, delta),
            "generated_kg_hr": max(0.0, delta),
            "net_delta_kg_hr": delta,
        }
        for ID, delta in unit.reaction_delta_kg_hr.items()
        if abs(delta) > 1e-15
    )
    return rows


def _gas_rows(model) -> list[dict[str, object]]:
    stream = model.streams["raw_biogas"]
    IDs = tuple(COMPONENT_GROUPS["biogas_components"] | {"Water"})
    wet_kmol = sum(float(stream.imol[ID]) for ID in IDs)
    dry_kmol = sum(float(stream.imol[ID]) for ID in IDs if ID != "Water")
    return [
        {
            "component_id": ID,
            "flow_kg_hr": float(stream.imass[ID]),
            "flow_kmol_hr": float(stream.imol[ID]),
            "normal_volume_nm3_hr": normal_volume_m3(float(stream.imol[ID])),
            "wet_mol_fraction": float(stream.imol[ID]) / wet_kmol if wet_kmol else 0.0,
            "dry_mol_fraction": (
                float(stream.imol[ID]) / dry_kmol if dry_kmol and ID != "Water" else 0.0
            ),
            "ppmv_dry": (
                float(stream.imol[ID]) / dry_kmol * 1e6 if dry_kmol and ID != "Water" else 0.0
            ),
            "gas_basis": "0 degC and 101325 Pa normal conditions",
        }
        for ID in IDs
    ]


def _mass_balance_rows(model) -> list[dict[str, object]]:
    inlet = sum_stream_component_flows(model.system.ins)
    expected = _adjust_plant_inventory(model.upstream_model, inlet)
    expected = _apply_delta_ledger(
        expected,
        getattr(model.units["R501"], "reaction_delta_kg_hr", {}),
    )
    outlet = sum_stream_component_flows(model.system.outs)
    return [
        {
            "component_id": ID,
            "external_inlet_kg_hr": inlet[ID],
            "reaction_adjusted_inlet_kg_hr": expected[ID],
            "external_outlet_kg_hr": outlet[ID],
            "residual_kg_hr": expected[ID] - outlet[ID],
        }
        for ID in chemicals.IDs
    ]


def _element_rows(model) -> list[dict[str, object]]:
    return [
        {
            "element": name,
            "external_inlet_kg_hr": model.validation.element_in_kg_hr[name],
            "external_outlet_kg_hr": model.validation.element_out_kg_hr[name],
            "residual_kg_hr": model.validation.element_errors_kg_hr[name],
            "validation_status": (
                "strict"
                if name in {"carbon", "nitrogen", "phosphorus", "sulfur"}
                else "informational_pseudo_component_limit"
            ),
        }
        for name in model.validation.element_in_kg_hr
    ]


def _energy_rows(model) -> list[dict[str, object]]:
    rows = []
    for ID in ("M501", "H501", "R501", "V501"):
        unit = model.units[ID]
        rows.append({
            "unit_id": ID,
            "operation": unit.line,
            "electricity_kw": float(unit.power_utility.consumption),
            "heating_kw": sum(max(0.0, float(i.duty)) for i in unit.heat_utilities) / 3600.0,
            "cooling_kw": sum(min(0.0, float(i.duty)) for i in unit.heat_utilities) / 3600.0,
            "purchase_cost_available": bool(unit.purchase_cost),
            "cost_basis": "BioSTEAM built-in" if unit.purchase_cost else "no approved Phase 5 CAPEX basis",
        })
    rows.append({
        "unit_id": "TOTAL",
        "operation": "Phase 5 total",
        "electricity_kw": sum(float(i["electricity_kw"]) for i in rows),
        "heating_kw": sum(float(i["heating_kw"]) for i in rows),
        "cooling_kw": sum(float(i["cooling_kw"]) for i in rows),
        "purchase_cost_available": any(bool(i["purchase_cost_available"]) for i in rows),
        "cost_basis": "No heat-recovery credit and no invented custom-unit CAPEX",
    })
    return rows


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
            "phase_introduced": 5,
            "comment": assumption,
        }
        for assumption in model.assumptions
    )
    return rows


def _unit_rows(model) -> list[dict[str, object]]:
    rows = []
    for ID in ("M501", "H501", "R501", "V501"):
        unit = model.units[ID]
        base = {
            "unit_id": ID,
            "operation": unit.line,
            "inlets": ", ".join(i.ID for i in unit.ins),
            "outlets": ", ".join(i.ID for i in unit.outs),
            "power_kw": float(unit.power_utility.consumption),
            "net_heat_kw": sum(float(i.duty) for i in unit.heat_utilities) / 3600.0,
            "purchase_cost": sum(unit.purchase_costs.values()) if unit.purchase_costs else None,
            "warnings": " | ".join(getattr(unit, "warnings", ())),
            "limitation_ids": "; ".join(getattr(unit, "limitation_ids", ())),
        }
        if unit.design_results:
            for name, value in unit.design_results.items():
                rows.append({**base, "design_item": name, "design_value": value, "design_unit": unit._units.get(name)})
        else:
            rows.append({**base, "design_item": None, "design_value": None, "design_unit": None})
    return rows


def save_phase5_reports(
    model,
    *,
    flowsheet_path: Path,
    scenario_models: tuple[object, ...],
    seasonal_result,
    results_dir: Path = RESULTS_DIR,
) -> dict[str, Path]:
    """Write detailed Phase 5 CSV, comparison, limitation, and system reports."""

    ensure_results_dir()
    results_dir.mkdir(parents=True, exist_ok=True)
    reactor = model.units["R501"]
    separator = model.units["V501"]
    speciation = reactor.ammonia_speciation
    mass_rows = _mass_balance_rows(model)
    element_rows = _element_rows(model)
    assumptions = _assumption_rows(model)
    limitations = limitation_rows(model)
    tables = {
        "digester_feed_characterization.csv": pd.DataFrame(_feed_characterization_rows(model)),
        "digester_conditioning_report.csv": pd.DataFrame(_conditioning_rows(model)),
        "digester_design_report.csv": pd.DataFrame(_design_rows(model)),
        "hydrolysis_report.csv": pd.DataFrame(reactor.hydrolysis_rows),
        "acidogenesis_report.csv": pd.DataFrame(reactor.acidogenesis_rows),
        "acetogenesis_report.csv": pd.DataFrame(reactor.acetogenesis_rows),
        "methanogenesis_report.csv": pd.DataFrame(reactor.methanogenesis_rows),
        "digestion_stoichiometry_report.csv": pd.DataFrame(_stoichiometry_rows(model)),
        "raw_biogas_composition.csv": pd.DataFrame(_gas_rows(model)),
        "digestate_composition.csv": pd.DataFrame(_stream_rows(model.streams["digestate"])),
        "gas_liquid_partitioning.csv": pd.DataFrame(separator.partition_rows),
        "dissolved_methane_report.csv": pd.DataFrame([{
            "methane_produced_kg_hr": model.metrics["methane_produced_kg_hr"],
            "methane_in_raw_biogas_kg_hr": model.metrics["methane_exported_kg_hr"],
            "dissolved_methane_kg_hr": model.metrics["dissolved_methane_kg_hr"],
            "uncaptured_methane_kg_hr": model.metrics["uncaptured_methane_kg_hr"],
            "empirical_dissolved_fraction": separator.parameters.dissolved_methane_fraction,
            "capture_efficiency": separator.parameters.gas_capture_efficiency,
        }]),
        "ammonia_equilibrium_report.csv": pd.DataFrame([asdict(speciation) if speciation else {
            "status": "no TAN speciation because digestion is disabled"
        }]),
        "sulphur_conversion_report.csv": pd.DataFrame([{
            "sulfate_reduction_enabled": reactor.parameters.sulfate_reduction_enabled,
            "sulfate_reduction_fraction": reactor.parameters.sulfate_reduction_fraction,
            "hydrogen_sulfide_generated_kg_hr": reactor.generated_kg_hr.get("HydrogenSulfide", 0.0),
            "raw_biogas_h2s_ppmv_dry": model.metrics["raw_biogas_h2s_ppmv_dry"],
        }]),
        "phosphorus_mineralization_report.csv": pd.DataFrame([
            row for row in reactor.mineralization_rows if row.get("element") == "phosphorus"
        ]),
        "phase5_mass_balance.csv": pd.DataFrame(mass_rows),
        "phase5_COD_balance.csv": pd.DataFrame([model.validation.cod_balance]),
        "phase5_elemental_balance.csv": pd.DataFrame(element_rows),
        "phase5_nitrogen_balance.csv": pd.DataFrame([row for row in element_rows if row["element"] == "nitrogen"]),
        "phase5_phosphorus_balance.csv": pd.DataFrame([row for row in element_rows if row["element"] == "phosphorus"]),
        "phase5_sulphur_balance.csv": pd.DataFrame([row for row in element_rows if row["element"] == "sulfur"]),
        "phase5_energy_summary.csv": pd.DataFrame(_energy_rows(model)),
        "phase5_monthly_results.csv": pd.DataFrame(seasonal_result.monthly_rows),
        "phase5_assumption_register.csv": pd.DataFrame(assumptions),
        "model_limitations.csv": pd.DataFrame(limitations),
    }
    paths: dict[str, Path] = {"flowsheet": flowsheet_path}
    for filename, table in tables.items():
        path = results_dir / filename
        table.to_csv(path, index=False)
        paths[filename] = path

    comparison = pd.DataFrame([candidate.metrics for candidate in scenario_models])
    comparison_path = results_dir / "phase5_scenario_comparison.xlsx"
    with pd.ExcelWriter(comparison_path, engine="openpyxl") as writer:
        comparison.to_excel(writer, sheet_name="Scenario metrics", index=False)
        comparison.set_index("scenario").transpose().rename_axis("metric").reset_index().to_excel(
            writer, sheet_name="Metrics by scenario", index=False
        )
        pd.DataFrame(seasonal_result.monthly_rows).to_excel(writer, sheet_name="Monthly selected", index=False)
        pd.DataFrame([seasonal_result.annual_totals]).to_excel(writer, sheet_name="Annual totals", index=False)
        pd.DataFrame([seasonal_result.peak_design]).to_excel(writer, sheet_name="Peak design", index=False)
        pd.DataFrame([
            {
                "scenario": scenario.scenario_id,
                "name": scenario.name,
                "active": scenario.active,
                "feed_mode": scenario.feed_mode,
                "digester_type": scenario.digester_type,
                "description": scenario.description,
                "missing_data_requirements": "; ".join(scenario.missing_data_requirements),
            }
            for scenario in DIGESTION_SCENARIOS.values()
        ]).to_excel(writer, sheet_name="Scenario readiness", index=False)
        _format_workbook(writer.book)
    paths["scenario_comparison"] = comparison_path

    limitation_path = results_dir / "phase5_limitations_and_data_needs.xlsx"
    with pd.ExcelWriter(limitation_path, engine="openpyxl") as writer:
        pd.DataFrame(limitations).to_excel(writer, sheet_name="Limitation register", index=False)
        pd.DataFrame([
            row for row in limitations if row["priority"] == "high"
        ]).to_excel(writer, sheet_name="High priority data", index=False)
        pd.DataFrame(assumptions).to_excel(writer, sheet_name="Selected assumptions", index=False)
        pd.DataFrame([
            {
                "scenario": scenario.scenario_id,
                "active": scenario.active,
                "missing_data_requirements": "; ".join(scenario.missing_data_requirements),
            }
            for scenario in DIGESTION_SCENARIOS.values()
        ]).to_excel(writer, sheet_name="Scenario data gates", index=False)
        _format_workbook(writer.book)
    paths["limitations_and_data_needs"] = limitation_path

    report_path = results_dir / "phase5_anaerobic_digestion_report.xlsx"
    with pd.ExcelWriter(report_path, engine="openpyxl") as writer:
        pd.DataFrame(model.metrics.items(), columns=["metric", "value"]).to_excel(writer, sheet_name="Summary", index=False)
        model.system.results().to_excel(writer, sheet_name="System results")
        bst.report.stream_table(model.system.streams, flow="kg/hr", percent=False, T="K", P="Pa").to_excel(
            writer, sheet_name="Stream table"
        )
        _write_unit_tables(
            writer,
            "BioSTEAM unit results",
            bst.report.unit_result_tables(
                model.system.units,
                include_utilities=True,
                include_total_cost=True,
                include_installed_cost=True,
            ),
        )
        pd.DataFrame(_unit_rows(model)).to_excel(writer, sheet_name="Phase5 unit details", index=False)
        sheet_map = {
            "Feed characterization": "digester_feed_characterization.csv",
            "Conditioning": "digester_conditioning_report.csv",
            "Digester design": "digester_design_report.csv",
            "Hydrolysis": "hydrolysis_report.csv",
            "Acidogenesis": "acidogenesis_report.csv",
            "Acetogenesis": "acetogenesis_report.csv",
            "Methanogenesis": "methanogenesis_report.csv",
            "Stoichiometry": "digestion_stoichiometry_report.csv",
            "Raw biogas": "raw_biogas_composition.csv",
            "Digestate": "digestate_composition.csv",
            "Gas partition": "gas_liquid_partitioning.csv",
            "Dissolved methane": "dissolved_methane_report.csv",
            "Ammonia equilibrium": "ammonia_equilibrium_report.csv",
            "Sulphur": "sulphur_conversion_report.csv",
            "Phosphorus": "phosphorus_mineralization_report.csv",
            "Mass balance": "phase5_mass_balance.csv",
            "COD balance": "phase5_COD_balance.csv",
            "Element balance": "phase5_elemental_balance.csv",
            "Energy": "phase5_energy_summary.csv",
            "Assumptions": "phase5_assumption_register.csv",
            "Limitations": "model_limitations.csv",
        }
        for sheet_name, filename in sheet_map.items():
            tables[filename].to_excel(writer, sheet_name=sheet_name, index=False)
        pd.DataFrame([{"validation_report": model.validation.report}]).to_excel(
            writer, sheet_name="Validation", index=False
        )
        if flowsheet_path.exists():
            from openpyxl.drawing.image import Image as XLImage

            worksheet = writer.book.create_sheet("Flowsheet")
            worksheet.add_image(XLImage(str(flowsheet_path)), "A1")
        _format_workbook(writer.book)
    paths["anaerobic_digestion_report"] = report_path
    model.reports.update(paths)
    return paths
