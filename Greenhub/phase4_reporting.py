"""Detailed CSV and Excel reporting for GreenHub Phase 4."""

from __future__ import annotations

from pathlib import Path

import biosteam as bst
import pandas as pd

from Greenhub.analytical import calculate_analytical_indicators
from Greenhub.chemicals import chemicals
from Greenhub.component_groups import COMPONENT_GROUPS
from Greenhub.component_metadata import COMPONENT_METADATA
from Greenhub.phase4_validation import (
    PROTEIN_POOL_IDS,
    stream_component_flows,
    sum_stream_component_flows,
)
from Greenhub.reporting import _format_workbook, _write_unit_tables
from Greenhub.scenarios import PROTEIN_RECOVERY_SCENARIOS
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
            "mass_fraction_dry": (
                float(stream.imass[ID]) / dry if dry and ID != "Water" else 0.0
            ),
            "category": COMPONENT_METADATA[ID].category,
            "subcategory": COMPONENT_METADATA[ID].subcategory,
            "source_or_status": "calculated stream inventory",
        }
        for ID in chemicals.IDs
    ]


def _protein_feed_rows(model) -> list[dict[str, object]]:
    feed = model.streams["clarified_protein_rich_liquid"]
    density = float(model.parameters["values"].get("phase4_feed_density_kg_m3", 1000.0))
    volume = feed.F_mass / density if density else 0.0
    rows = _stream_rows(feed)
    for row in rows:
        row["concentration_g_L"] = row["flow_kg_hr"] / volume if volume else None
        row["protein_inventory_class"] = (
            "recoverable_true_protein"
            if row["component_id"] in {"SolubleProtein", "SuspendedProtein"}
            else "peptide_not_recoverable_true_protein"
            if row["component_id"] == "Peptides"
            else "amino_acid_not_recoverable_true_protein"
            if row["component_id"] == "AminoAcids"
            else "non_protein"
        )
    return rows


def _acid_rows(model) -> list[dict[str, object]]:
    unit = model.units.get("M401")
    if unit is None or unit.acid_demand is None:
        return [{
            "scenario": model.scenario.scenario_id,
            "enabled": False,
            "method": "bypass_or_heat_only",
            "acid_type": model.parameters["values"].get("acid_type"),
            "pure_acid_kg_hr": 0.0,
            "acid_solution_kg_hr": 0.0,
            "reagent_water_kg_hr": 0.0,
            "pure_acid_dose_kg_m3": 0.0,
            "acid_kg_per_kg_dry_product": None,
            "initial_pH_metadata": model.parameters["values"].get("feed_pH"),
            "target_pH_metadata": model.parameters["values"].get("feed_pH"),
            "warning": "No acid is active in this scenario.",
        }]
    demand = unit.acid_demand
    return [{
        "scenario": model.scenario.scenario_id,
        "enabled": unit.parameters.enabled,
        "method": demand.method,
        "acid_type": demand.acid_type,
        "solution_mass_fraction": unit.parameters.acid_solution_mass_fraction,
        "acid_purity": unit.parameters.acid_purity,
        "pure_acid_kg_hr": demand.pure_acid_kg_hr,
        "acid_solution_kg_hr": demand.acid_solution_kg_hr,
        "reagent_water_kg_hr": demand.reagent_water_kg_hr,
        "acid_equivalents_kmol_hr": demand.acid_equivalents_kmol_hr,
        "pure_acid_dose_kg_m3": demand.pure_acid_dose_kg_m3,
        "acid_kg_per_kg_dry_product": model.metrics.get(
            "specific_acid_demand_kg_per_kg_dry_product"
        ),
        "initial_pH_metadata": demand.initial_pH,
        "target_pH_metadata": demand.target_pH,
        "warning": demand.warning,
    }]


def _precipitation_rows(model) -> list[dict[str, object]]:
    unit = model.units.get("R401")
    if unit is None:
        return [{
            "scenario": model.scenario.scenario_id,
            "active": False,
            "protein_transfer": None,
            "flow_kg_hr": 0.0,
            "recovery_fraction": 0.0,
            "method": "bypass",
        }]
    rows = []
    for name, value in unit.transfers_kg_hr.items():
        is_acid = name.endswith("PrecipitatedProtein")
        rows.append({
            "scenario": model.scenario.scenario_id,
            "active": bool(value) or (unit.parameters.acid_enabled if is_acid else unit.parameters.heat_enabled),
            "protein_transfer": name,
            "flow_kg_hr": value,
            "recovery_fraction": (
                unit.acid_recovery_fraction if is_acid else unit.heat_recovery_fraction
            ),
            "method": (
                unit.parameters.acid_recovery_mode if is_acid else unit.parameters.heat_recovery_mode
            ),
            "target_pH_metadata": unit.parameters.target_pH,
            "effective_pI": unit.parameters.effective_protein_pI,
            "temperature_C": unit.outs[0].T - 273.15,
            "residence_time_min": unit.parameters.residence_time_min,
        })
    return rows


def _separator_rows(model) -> list[dict[str, object]]:
    unit = model.units.get("C401")
    if unit is None:
        return []
    feed = unit.ins[0]
    cake, centrate = unit.outs
    rows = []
    for ID in chemicals.IDs:
        inlet = float(feed.imass[ID])
        detail = unit.partitioning.get(ID, {})
        rows.append({
            "component_id": ID,
            "inlet_kg_hr": inlet,
            "wet_cake_kg_hr": float(cake.imass[ID]),
            "centrate_kg_hr": float(centrate.imass[ID]),
            "actual_fraction_to_cake": float(cake.imass[ID]) / inlet if inlet else None,
            "fixed_capture_fraction": detail.get("fixed_capture_fraction"),
            "liquid_entrainment_fraction": detail.get("liquid_entrainment_fraction"),
            "split_source": (
                "analytical cake-moisture water allocation"
                if ID == "Water"
                else detail.get("source")
            ),
            "residual_kg_hr": inlet - float(cake.imass[ID]) - float(centrate.imass[ID]),
        })
    return rows


def _washing_rows(model) -> list[dict[str, object]]:
    unit = model.units.get("W401")
    if unit is None:
        return [{
            "scenario": model.scenario.scenario_id,
            "wash_enabled": False,
            "component_id": None,
            "inlet_cake_kg_hr": 0.0,
            "removed_to_filtrate_kg_hr": 0.0,
            "retained_in_cake_kg_hr": 0.0,
            "wash_water_kg_hr": 0.0,
            "comment": "No cake wash in this scenario.",
        }]
    cake = unit.ins[0]
    washed, filtrate = unit.outs
    return [
        {
            "scenario": model.scenario.scenario_id,
            "wash_enabled": True,
            "component_id": ID,
            "inlet_cake_kg_hr": float(cake.imass[ID]),
            "removed_to_filtrate_kg_hr": float(filtrate.imass[ID]),
            "retained_in_cake_kg_hr": float(washed.imass[ID]),
            "wash_water_kg_hr": unit.ins[1].F_mass if ID == "Water" else None,
            "comment": "Single-stage displacement wash; only configured solutes and protein loss are removed.",
        }
        for ID in chemicals.IDs
    ]


def _dewatering_rows(model) -> list[dict[str, object]]:
    unit = model.units.get("D401")
    if unit is None:
        return [{"scenario": model.scenario.scenario_id, "active": False}]
    return [{
        "scenario": model.scenario.scenario_id,
        "active": not unit.bypassed,
        "inlet_cake_kg_hr": unit.ins[0].F_mass,
        "dewatered_cake_kg_hr": unit.outs[0].F_mass,
        "filtrate_kg_hr": unit.outs[1].F_mass,
        "target_solids_fraction": unit.parameters.target_solids_fraction,
        "actual_solids_fraction": (
            (unit.outs[0].F_mass - float(unit.outs[0].imass["Water"])) / unit.outs[0].F_mass
            if unit.outs[0].F_mass
            else 0.0
        ),
        "water_removed_kg_hr": float(unit.outs[1].imass["Water"]),
        "protein_loss_kg_hr": sum(
            float(unit.outs[1].imass[ID]) for ID in PROTEIN_POOL_IDS
        ),
        "electricity_kw": float(unit.power_utility.consumption),
        "cost_available": bool(unit.purchase_cost),
    }]


def _dryer_mass_rows(model) -> list[dict[str, object]]:
    unit = model.units.get("DR401")
    if unit is None or unit.mass_result is None:
        return [{"scenario": model.scenario.scenario_id, "active": False}]
    result = unit.mass_result
    return [{
        "scenario": model.scenario.scenario_id,
        "active": True,
        "dryer_type": unit.parameters.dryer_type,
        "inlet_cake_kg_hr": unit.ins[0].F_mass,
        "inlet_dry_matter_kg_hr": result.inlet_dry_matter_kg_hr + sum(unit.dry_losses_kg_hr.values()),
        "retained_dry_matter_kg_hr": result.inlet_dry_matter_kg_hr,
        "inlet_water_kg_hr": result.inlet_water_kg_hr,
        "product_kg_hr": unit.outs[0].F_mass,
        "product_water_kg_hr": result.product_water_kg_hr,
        "evaporated_water_kg_hr": result.evaporated_water_kg_hr,
        "dry_dust_and_entrainment_kg_hr": unit.outs[1].F_mass - float(unit.outs[1].imass["Water"]),
        "target_product_moisture_fraction": unit.parameters.target_product_moisture_fraction,
        "actual_product_moisture_fraction": result.product_moisture_fraction,
        "protein_degradation_transfer_kg_hr": sum(unit.transfers_kg_hr.values()),
        "mass_residual_kg_hr": unit.ins[0].F_mass - unit.outs[0].F_mass - unit.outs[1].F_mass,
    }]


def _dryer_energy_rows(model) -> list[dict[str, object]]:
    unit = model.units.get("DR401")
    if unit is None or unit.energy_result is None:
        return [{"scenario": model.scenario.scenario_id, "active": False}]
    result = unit.energy_result
    return [{
        "scenario": model.scenario.scenario_id,
        "active": True,
        "calculation_method": result.calculation_method,
        "heat_source": unit.parameters.heat_source,
        "sensible_water_kj_hr": result.sensible_water_kj_hr,
        "sensible_dry_solids_kj_hr": result.sensible_dry_solids_kj_hr,
        "latent_heat_kj_hr": result.latent_heat_kj_hr,
        "useful_heat_kj_hr": result.useful_heat_kj_hr,
        "thermal_efficiency": unit.parameters.thermal_efficiency,
        "heat_loss_fraction": unit.parameters.heat_loss_fraction,
        "external_heat_kj_hr": result.external_heat_kj_hr,
        "external_heat_kw": result.external_heat_kw,
        "electricity_kw": float(unit.power_utility.consumption),
        "air_model": "utility_only_no_air_mass_or_humidity",
        "heat_recovery_credit": 0.0,
    }]


def _neutralization_rows(model) -> list[dict[str, object]]:
    unit = model.units.get("M403")
    if unit is None or not hasattr(unit, "base_demand") or unit.base_demand is None:
        return [{
            "scenario": model.scenario.scenario_id,
            "active": False,
            "component_id": None,
            "reaction_delta_kg_hr": 0.0,
            "comment": "No acid/base neutralization in bypass scenario.",
        }]
    demand = unit.base_demand
    return [
        {
            "scenario": model.scenario.scenario_id,
            "active": True,
            "acid_type": demand.acid_type,
            "base_type": demand.base_type,
            "salt_type": demand.salt_type,
            "component_id": ID,
            "reaction_delta_kg_hr": unit.reaction_delta_kg_hr[ID],
            "residual_acid_entering_kg_hr": demand.acid_kg_hr if ID == demand.acid_type else None,
            "neutralized_acid_kg_hr": unit.neutralized_acid_kg_hr if ID == demand.acid_type else None,
            "pure_base_kg_hr": demand.pure_base_kg_hr if ID == demand.base_type else None,
            "base_solution_kg_hr": demand.base_solution_kg_hr if ID == demand.base_type else None,
            "reagent_water_kg_hr": demand.reagent_water_kg_hr if ID == "Water" else None,
            "salt_generated_kg_hr": unit.salt_generated_kg_hr if ID == demand.salt_type else None,
            "initial_pH_metadata": unit.inlet_pH,
            "target_pH_metadata": unit.outlet_pH,
            "comment": "Validated molecular salt reaction; pH remains non-rigorous metadata.",
        }
        for ID in chemicals.IDs
        if abs(unit.reaction_delta_kg_hr[ID]) > 0.0
        or ID in {demand.acid_type, demand.base_type, demand.salt_type, "Water"}
    ]


def _adjusted_plant_flows(model) -> tuple[dict[str, float], dict[str, float], dict[str, float]]:
    raw_inlet = sum_stream_component_flows(model.system.ins)
    adjusted = dict(raw_inlet)
    for unit_id in ("U201", "R401", "DR401"):
        unit = model.units.get(unit_id)
        if unit is None:
            continue
        for name, amount in getattr(unit, "transfers_kg_hr", {}).items():
            source, target = name.split("_to_", 1)
            adjusted[source] -= float(amount)
            adjusted[target] += float(amount)
    unit = model.units.get("M403")
    if unit is not None:
        for ID, delta in getattr(unit, "reaction_delta_kg_hr", {}).items():
            adjusted[ID] += float(delta)
    outlet = sum_stream_component_flows(model.system.outs)
    return raw_inlet, adjusted, outlet


def _mass_balance_rows(model) -> list[dict[str, object]]:
    raw, adjusted, outlet = _adjusted_plant_flows(model)
    return [
        {
            "component_id": ID,
            "external_inlet_kg_hr": raw[ID],
            "transfer_and_reaction_adjusted_inlet_kg_hr": adjusted[ID],
            "external_outlet_kg_hr": outlet[ID],
            "residual_kg_hr": adjusted[ID] - outlet[ID],
        }
        for ID in chemicals.IDs
    ]


def _element_rows(model) -> list[dict[str, object]]:
    validation = model.validation
    return [
        {
            "element": name,
            "adjusted_inlet_kg_hr": validation.element_in_kg_hr[name],
            "external_outlet_kg_hr": validation.element_out_kg_hr[name],
            "residual_kg_hr": validation.element_errors_kg_hr[name],
        }
        for name in validation.element_in_kg_hr
    ]


def _energy_rows(model) -> list[dict[str, object]]:
    phase4_ids = ("M401", "H401", "R401", "C401", "W401", "D401", "DR401", "M402", "M403")
    rows = []
    for ID in phase4_ids:
        if ID not in model.units:
            continue
        unit = model.units[ID]
        rows.append({
            "scenario": model.scenario.scenario_id,
            "unit_id": ID,
            "unit_operation": unit.line,
            "electricity_kw": float(unit.power_utility.consumption),
            "heating_duty_kw": sum(
                max(0.0, float(utility.duty)) for utility in unit.heat_utilities
            ) / 3600.0,
            "cooling_duty_kw": sum(
                min(0.0, float(utility.duty)) for utility in unit.heat_utilities
            ) / 3600.0,
            "purchase_cost_available": bool(unit.purchase_cost),
            "cost_comment": (
                "BioSTEAM built-in correlation"
                if unit.purchase_cost
                else "No approved Phase 4 purchase-cost correlation"
            ),
        })
    rows.append({
        "scenario": model.scenario.scenario_id,
        "unit_id": "TOTAL",
        "unit_operation": "Phase 4 total",
        "electricity_kw": sum(float(row["electricity_kw"]) for row in rows),
        "heating_duty_kw": sum(float(row["heating_duty_kw"]) for row in rows),
        "cooling_duty_kw": sum(float(row["cooling_duty_kw"]) for row in rows),
        "purchase_cost_available": any(bool(row["purchase_cost_available"]) for row in rows),
        "cost_comment": "No hypothetical heat-recovery credit is subtracted.",
    })
    return rows


def _assumption_rows(model) -> list[dict[str, object]]:
    rows = [
        {
            "input_parameter": record.python_name,
            "value": record.value,
            "unit": record.unit,
            "scenario_scope": record.scenario,
            "selected_scenario": model.scenario.scenario_id,
            "month": model.input_bundle.selected_month,
            "minimum": record.minimum,
            "maximum": record.maximum,
            "distribution": record.distribution,
            "required": record.required,
            "measurement_status": record.measurement_status,
            "source_class": record.source_class,
            "reference": record.reference,
            "calculation_method": record.calculation_method,
            "measured_or_assumed": record.measured_or_assumed,
            "active": record.active,
            "phase_introduced": record.phase_introduced,
            "comment": record.comment,
        }
        for record in model.input_bundle.parameter_records
    ]
    rows.extend({
        "input_parameter": "model_assumption",
        "value": assumption,
        "unit": None,
        "scenario_scope": model.scenario.scenario_id,
        "selected_scenario": model.scenario.scenario_id,
        "month": model.input_bundle.selected_month,
        "measurement_status": "calculated",
        "source_class": "E",
        "calculation_method": "documented model boundary",
        "measured_or_assumed": "assumed",
        "active": True,
        "phase_introduced": 4,
        "comment": assumption,
    } for assumption in model.assumptions)
    return rows


def _data_gap_rows(model) -> list[dict[str, object]]:
    rows = [
        {
            "category": record.category,
            "item": record.python_name,
            "scenario": record.scenario,
            "status": "missing_optional_value",
            "requirement_or_action": record.comment,
        }
        for record in model.input_bundle.parameter_records
        if record.value is None
    ]
    for scenario in PROTEIN_RECOVERY_SCENARIOS.values():
        if scenario.active:
            continue
        for requirement in scenario.missing_data_requirements:
            rows.append({
                "category": "inactive_alternative",
                "item": requirement,
                "scenario": scenario.scenario_id,
                "status": "required_before_activation",
                "requirement_or_action": scenario.description,
            })
    rows.extend([
        {
            "category": "equipment_costing",
            "item": "Phase 4 custom-unit CAPEX",
            "scenario": model.scenario.scenario_id,
            "status": "not_available",
            "requirement_or_action": "Obtain vendor quotes or approved project-specific correlations.",
        },
        {
            "category": "drying",
            "item": "Air flow and humidity",
            "scenario": model.scenario.scenario_id,
            "status": "not_modelled",
            "requirement_or_action": "Add psychrometric data before detailed dryer design.",
        },
        {
            "category": "product_quality",
            "item": "External classification criteria",
            "scenario": model.scenario.scenario_id,
            "status": "not_available",
            "requirement_or_action": "Add legal, microbiological, contaminant, and compositional criteria before classification.",
        },
    ])
    return rows


def _unit_detail_rows(model) -> list[dict[str, object]]:
    rows = []
    phase4_ids = {"M401", "H401", "R401", "C401", "W401", "D401", "DR401", "M402", "M403"}
    for ID, unit in model.units.items():
        if ID not in phase4_ids:
            continue
        base = {
            "unit_id": ID,
            "unit_operation": unit.line,
            "inlets": ", ".join(stream.ID for stream in unit.ins),
            "outlets": ", ".join(stream.ID for stream in unit.outs),
            "temperature_K": unit.outs[0].T if unit.outs else None,
            "pressure_Pa": unit.outs[0].P if unit.outs else None,
            "power_kw": float(unit.power_utility.consumption),
            "heat_duty_kw": sum(float(i.duty) for i in unit.heat_utilities) / 3600.0,
            "purchase_cost": sum(unit.purchase_costs.values()) if unit.purchase_costs else None,
            "installed_cost": unit.installed_cost if unit.purchase_costs else None,
            "warnings": " | ".join(getattr(unit, "warnings", ())),
        }
        if unit.design_results:
            for name, value in unit.design_results.items():
                row = dict(base)
                row.update(design_item=name, design_value=value, design_unit=unit._units.get(name))
                rows.append(row)
        else:
            rows.append({**base, "design_item": None, "design_value": None, "design_unit": None})
    return rows


def save_phase4_reports(
    model,
    *,
    flowsheet_path: Path,
    scenario_models: tuple[object, ...],
    seasonal_result,
    results_dir: Path = RESULTS_DIR,
) -> dict[str, Path]:
    """Write every required detailed Phase 4 CSV and Excel output."""

    ensure_results_dir()
    results_dir.mkdir(parents=True, exist_ok=True)
    tables = {
        "protein_feed_characterization.csv": pd.DataFrame(_protein_feed_rows(model)),
        "acid_demand_report.csv": pd.DataFrame(_acid_rows(model)),
        "protein_precipitation_report.csv": pd.DataFrame(_precipitation_rows(model)),
        "protein_separator_partitioning.csv": pd.DataFrame(_separator_rows(model)),
        "wet_protein_cake_composition.csv": pd.DataFrame(
            _stream_rows(model.streams["wet_protein_cake"])
            if "wet_protein_cake" in model.streams
            else []
        ),
        "washing_report.csv": pd.DataFrame(_washing_rows(model)),
        "dewatering_report.csv": pd.DataFrame(_dewatering_rows(model)),
        "dryer_mass_balance.csv": pd.DataFrame(_dryer_mass_rows(model)),
        "dryer_energy_balance.csv": pd.DataFrame(_dryer_energy_rows(model)),
        "dry_protein_product_composition.csv": pd.DataFrame(
            _stream_rows(model.streams["dry_protein_product"])
        ),
        "protein_depleted_liquid_composition.csv": pd.DataFrame(
            _stream_rows(model.streams["conditioned_protein_depleted_liquid"])
        ),
        "neutralization_and_salt_report.csv": pd.DataFrame(_neutralization_rows(model)),
        "phase4_mass_balance.csv": pd.DataFrame(_mass_balance_rows(model)),
        "phase4_elemental_balance.csv": pd.DataFrame(_element_rows(model)),
        "phase4_nitrogen_balance.csv": pd.DataFrame([model.validation.nitrogen_balance]),
        "phase4_cod_balance.csv": pd.DataFrame([
            {**model.validation.cod_balance, **model.validation.toc_balance}
        ]),
        "phase4_energy_summary.csv": pd.DataFrame(_energy_rows(model)),
        "phase4_monthly_results.csv": pd.DataFrame(seasonal_result.monthly_rows),
        "phase4_assumption_register.csv": pd.DataFrame(_assumption_rows(model)),
        "phase4_data_gaps.csv": pd.DataFrame(_data_gap_rows(model)),
    }
    paths: dict[str, Path] = {"flowsheet": flowsheet_path}
    for filename, table in tables.items():
        path = results_dir / filename
        table.to_csv(path, index=False)
        paths[filename] = path

    comparison = pd.DataFrame([candidate.metrics for candidate in scenario_models])
    comparison_by_metric = comparison.set_index("scenario").transpose().rename_axis("metric").reset_index()
    comparison_path = results_dir / "phase4_scenario_comparison.xlsx"
    with pd.ExcelWriter(comparison_path, engine="openpyxl") as writer:
        comparison_by_metric.to_excel(writer, sheet_name="Scenario comparison", index=False)
        pd.DataFrame(seasonal_result.monthly_rows).to_excel(writer, sheet_name="Monthly selected", index=False)
        pd.DataFrame([seasonal_result.annual_totals]).to_excel(writer, sheet_name="Annual totals", index=False)
        pd.DataFrame([
            {
                "scenario": scenario.scenario_id,
                "name": scenario.name,
                "active": scenario.active,
                "description": scenario.description,
                "missing_data_requirements": "; ".join(scenario.missing_data_requirements),
            }
            for scenario in PROTEIN_RECOVERY_SCENARIOS.values()
        ]).to_excel(writer, sheet_name="Scenario readiness", index=False)
        pd.DataFrame([
            {"scenario": candidate.scenario.scenario_id, "warning": warning}
            for candidate in scenario_models
            for warning in candidate.validation.warnings
        ]).to_excel(writer, sheet_name="Scenario warnings", index=False)
        _format_workbook(writer.book)
    paths["scenario_comparison"] = comparison_path

    report_path = results_dir / "phase4_protein_recovery_report.xlsx"
    with pd.ExcelWriter(report_path, engine="openpyxl") as writer:
        pd.DataFrame(model.metrics.items(), columns=["metric", "value"]).to_excel(
            writer,
            sheet_name="Summary",
            index=False,
        )
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
            "BioSTEAM unit results",
            bst.report.unit_result_tables(
                model.system.units,
                include_utilities=True,
                include_total_cost=True,
                include_installed_cost=True,
            ),
        )
        pd.DataFrame(_unit_detail_rows(model)).to_excel(writer, sheet_name="Phase4 unit details", index=False)
        sheet_map = {
            "Acid demand": "acid_demand_report.csv",
            "Precipitation": "protein_precipitation_report.csv",
            "Separator": "protein_separator_partitioning.csv",
            "Wet cake": "wet_protein_cake_composition.csv",
            "Washing": "washing_report.csv",
            "Dewatering": "dewatering_report.csv",
            "Dryer mass": "dryer_mass_balance.csv",
            "Dryer energy": "dryer_energy_balance.csv",
            "Dry product": "dry_protein_product_composition.csv",
            "Conditioned liquid": "protein_depleted_liquid_composition.csv",
            "Neutralization": "neutralization_and_salt_report.csv",
            "Mass balance": "phase4_mass_balance.csv",
            "Element balance": "phase4_elemental_balance.csv",
            "Nitrogen balance": "phase4_nitrogen_balance.csv",
            "COD and TOC": "phase4_cod_balance.csv",
            "Energy": "phase4_energy_summary.csv",
            "Assumptions": "phase4_assumption_register.csv",
            "Data gaps": "phase4_data_gaps.csv",
        }
        for sheet_name, filename in sheet_map.items():
            tables[filename].to_excel(writer, sheet_name=sheet_name, index=False)
        pd.DataFrame([{"validation_report": model.validation.report}]).to_excel(
            writer,
            sheet_name="Validation",
            index=False,
        )
        if flowsheet_path.exists():
            from openpyxl.drawing.image import Image as XLImage

            worksheet = writer.book.create_sheet("Flowsheet")
            worksheet.add_image(XLImage(str(flowsheet_path)), "A1")
        _format_workbook(writer.book)
    paths["protein_recovery_report"] = report_path
    model.reports.update(paths)
    return paths
