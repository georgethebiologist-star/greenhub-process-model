"""CSV and Excel reporting for GreenHub Phase 6 gas upgrading."""

from __future__ import annotations

from pathlib import Path
from typing import Iterable

import biosteam as bst
import pandas as pd

from Greenhub.chemicals import chemicals
from Greenhub.component_metadata import COMPONENT_METADATA
from Greenhub.phase4_validation import sum_stream_component_flows
from Greenhub.phase6_limitations import phase6_limitation_rows
from Greenhub.phase6_specifications import DRY_GAS_COMPONENTS, normal_volume_nm3_hr
from Greenhub.reporting import _format_workbook, _write_unit_tables
from Greenhub.scenarios import BIOGAS_UPGRADING_SCENARIOS
from Greenhub.settings import RESULTS_DIR, ensure_results_dir


def _phase6_units(model) -> tuple[object, ...]:
    """Return unique units introduced at the Phase 6 boundary."""

    return tuple(
        model.units[unit_id]
        for unit_id in dict.fromkeys(model.parameters["phase6_unit_ids"])
        if unit_id in model.units
    )


def _stream_rows(stream) -> list[dict[str, object]]:
    """Return complete component inventory for one stream."""

    total_mass = float(stream.F_mass)
    total_moles = float(stream.F_mol)
    return [
        {
            "stream_id": stream.ID,
            "component_id": component_id,
            "flow_kg_hr": float(stream.imass[component_id]),
            "flow_kmol_hr": float(stream.imol[component_id]),
            "mass_fraction": (
                float(stream.imass[component_id]) / total_mass
                if total_mass
                else 0.0
            ),
            "mol_fraction": (
                float(stream.imol[component_id]) / total_moles
                if total_moles
                else 0.0
            ),
            "phase": stream.phase,
            "temperature_k": stream.T,
            "pressure_pa": stream.P,
            "category": COMPONENT_METADATA[component_id].category,
            "subcategory": COMPONENT_METADATA[component_id].subcategory,
        }
        for component_id in chemicals.IDs
    ]


def _gas_rows(stream) -> list[dict[str, object]]:
    """Return wet and dry gas composition on the common Phase 6 basis."""

    dry_kmol = sum(float(stream.imol[ID]) for ID in DRY_GAS_COMPONENTS)
    wet_kmol = dry_kmol + float(stream.imol["Water"])
    rows = []
    for component_id in (*DRY_GAS_COMPONENTS, "Water"):
        flow = float(stream.imol[component_id])
        rows.append(
            {
                "stream_id": stream.ID,
                "component_id": component_id,
                "flow_kg_hr": float(stream.imass[component_id]),
                "flow_kmol_hr": flow,
                "wet_mol_fraction": flow / wet_kmol if wet_kmol else 0.0,
                "dry_mol_fraction": (
                    flow / dry_kmol
                    if dry_kmol and component_id != "Water"
                    else 0.0
                ),
                "ppmv_dry": (
                    flow / dry_kmol * 1e6
                    if dry_kmol and component_id != "Water"
                    else 0.0
                ),
                "wet_total_nm3_hr": normal_volume_nm3_hr(stream),
                "dry_total_nm3_hr": normal_volume_nm3_hr(stream, dry=True),
                "normal_basis": "0 degC and 101325 Pa",
            }
        )
    return rows


def _mass_balance_rows(model) -> list[dict[str, object]]:
    inlet = sum_stream_component_flows(
        (model.streams["raw_biogas"], *model.external_inputs)
    )
    expected = dict(inlet)
    for unit in _phase6_units(model):
        for component_id, delta in getattr(unit, "reaction_delta_kg_hr", {}).items():
            expected[component_id] += float(delta)
    outlet = sum_stream_component_flows(model.boundary_outputs)
    return [
        {
            "component_id": component_id,
            "external_inlet_kg_hr": inlet[component_id],
            "reaction_adjusted_inlet_kg_hr": expected[component_id],
            "external_outlet_kg_hr": outlet[component_id],
            "residual_kg_hr": expected[component_id] - outlet[component_id],
        }
        for component_id in chemicals.IDs
    ]


def _element_rows(model) -> list[dict[str, object]]:
    return [
        {
            "element": element,
            "external_inlet_kg_hr": model.validation.element_in_kg_hr[element],
            "external_outlet_kg_hr": model.validation.element_out_kg_hr[element],
            "residual_kg_hr": model.validation.element_errors_kg_hr[element],
            "status": "validated",
        }
        for element in model.validation.element_in_kg_hr
    ]


def _quality_rows(model) -> list[dict[str, object]]:
    return [
        {
            "property": check.property_name,
            "conditioned_gas_value": check.value,
            "limit_type": check.limit_type,
            "selected_limit": check.limit,
            "unit": check.unit,
            "passed": check.passed,
            "interpretation": (
                "structural check only; not a grid-compliance claim"
            ),
        }
        for check in model.validation.feed_quality_checks
    ]


def _energy_rows(model) -> list[dict[str, object]]:
    rows = []
    for unit in _phase6_units(model):
        heating = sum(
            max(0.0, float(utility.duty)) for utility in unit.heat_utilities
        ) / 3600.0
        cooling = -sum(
            min(0.0, float(utility.duty)) for utility in unit.heat_utilities
        ) / 3600.0
        rows.append(
            {
                "unit_id": unit.ID,
                "operation": unit.line,
                "electricity_kw": float(unit.power_utility.consumption),
                "heating_kw": heating,
                "cooling_kw": cooling,
                "purchase_cost_available": bool(unit.purchase_cost),
                "cost_basis": (
                    "BioSTEAM built-in correlation"
                    if unit.purchase_cost
                    else "no approved custom Phase 6 CAPEX basis"
                ),
            }
        )
    rows.append(
        {
            "unit_id": "TOTAL",
            "operation": "Phase 6 local utilities",
            "electricity_kw": sum(float(row["electricity_kw"]) for row in rows),
            "heating_kw": sum(float(row["heating_kw"]) for row in rows),
            "cooling_kw": sum(float(row["cooling_kw"]) for row in rows),
            "purchase_cost_available": any(
                bool(row["purchase_cost_available"]) for row in rows
            ),
            "cost_basis": (
                "Local duties only; plant-wide utility integration is deferred"
            ),
        }
    )
    return rows


def _unit_rows(model) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for unit in _phase6_units(model):
        base = {
            "unit_id": unit.ID,
            "operation": unit.line,
            "inlets": ", ".join(stream.ID for stream in unit.ins),
            "outlets": ", ".join(stream.ID for stream in unit.outs),
            "power_kw": float(unit.power_utility.consumption),
            "net_heat_kw": sum(
                float(utility.duty) for utility in unit.heat_utilities
            ) / 3600.0,
            "purchase_cost": (
                sum(unit.purchase_costs.values()) if unit.purchase_costs else None
            ),
            "warnings": " | ".join(getattr(unit, "warnings", ())),
            "limitation_ids": "; ".join(
                getattr(unit, "limitation_ids", ())
            ),
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
            rows.append(
                {
                    **base,
                    "design_item": None,
                    "design_value": None,
                    "design_unit": None,
                }
            )
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
            "phase_introduced": 6,
            "comment": assumption,
        }
        for assumption in model.assumptions
    )
    return rows


def _methane_destination_rows(model) -> list[dict[str, object]]:
    feed = float(model.streams["raw_biogas"].imass["Methane"])
    destinations = (
        ("gas_product", model.streams["primary_gas_product"]),
        ("reject_gas", model.streams["reject_gas"]),
        ("conditioning_wastewater", model.streams["conditioning_wastewater"]),
        ("upgrading_wastewater", model.streams["technology_wastewater"]),
        ("conditioning_spent_material", model.streams["conditioning_spent_material"]),
        ("upgrading_spent_material", model.streams["technology_spent_material"]),
    )
    rows = [
        {
            "destination": name,
            "methane_kg_hr": float(stream.imass["Methane"]),
            "fraction_of_raw_biogas_methane": (
                float(stream.imass["Methane"]) / feed if feed else 0.0
            ),
        }
        for name, stream in destinations
    ]
    assigned = sum(float(row["methane_kg_hr"]) for row in rows)
    rows.append(
        {
            "destination": "unassigned_residual",
            "methane_kg_hr": feed - assigned,
            "fraction_of_raw_biogas_methane": (
                (feed - assigned) / feed if feed else 0.0
            ),
        }
    )
    return rows


def _comparison_rows(models: Iterable[object]) -> list[dict[str, object]]:
    rows = []
    for model in models:
        metrics = model.metrics
        rows.append(
            {
                "scenario": metrics["scenario"],
                "scenario_name": metrics["scenario_name"],
                "calculation_level": metrics["calculation_level"],
                "raw_biogas_processed_Nm3_hr": metrics["raw_biogas_processed_nm3_hr"],
                "biomethane_produced_Nm3_hr": metrics["biomethane_produced_nm3_hr"],
                "CH4_purity_dry_mol_percent": 100.0 * metrics["methane_purity_dry_fraction"],
                "CH4_recovery_percent": 100.0 * metrics["methane_recovery_fraction"],
                "CH4_slip_percent": 100.0 * metrics["methane_slip_fraction"],
                "CO2_removal_percent": 100.0 * metrics["co2_removal_fraction"],
                "product_pressure_bar": metrics["product_pressure_bar"],
                "electricity_kWh_per_Nm3_biomethane": metrics["electricity_kwh_per_nm3_biomethane"],
                "heat_MJ_per_Nm3_biomethane": metrics["heat_mj_per_nm3_biomethane"],
                "cooling_MJ_per_Nm3_biomethane": metrics["cooling_mj_per_nm3_biomethane"],
                "fresh_water_kg_per_Nm3_biomethane": metrics["fresh_water_kg_per_nm3_biomethane"],
                "wastewater_kg_per_Nm3_biomethane": metrics["wastewater_kg_per_nm3_biomethane"],
                "chemical_makeup_kg_hr": metrics["chemical_makeup_kg_hr"],
                "reject_gas_CH4_mol_percent_dry": 100.0 * metrics["reject_gas_methane_mol_fraction_dry"],
                "net_usable_energy_kw_direct_basis": metrics["net_usable_energy_kw_direct_basis"],
                "specific_equipment_capacity": metrics["specific_equipment_capacity"],
                "specific_equipment_capacity_unit": metrics["specific_equipment_capacity_unit"],
                "active_recycle": metrics["active_recycle"],
                "input_quality_class": "E structural baseline",
                "ranking_status": "not ranked",
            }
        )
    return rows


def _scenario_readiness_rows() -> list[dict[str, object]]:
    return [
        {
            "scenario": scenario.scenario_id,
            "name": scenario.name,
            "active": scenario.active,
            "pretreatment_enabled": scenario.pretreatment_enabled,
            "upgrading_enabled": scenario.upgrading_enabled,
            "mechanism": scenario.mechanism,
            "description": scenario.description,
            "missing_data_requirements": "; ".join(
                scenario.missing_data_requirements
            ),
        }
        for scenario in BIOGAS_UPGRADING_SCENARIOS.values()
    ]


def save_phase6_reports(
    model,
    *,
    flowsheet_path: Path,
    scenario_models: tuple[object, ...],
    results_dir: Path = RESULTS_DIR,
) -> dict[str, Path]:
    """Write selected-scenario, comparison, and limitation reports."""

    ensure_results_dir()
    results_dir.mkdir(parents=True, exist_ok=True)
    limitations = phase6_limitation_rows(model)
    assumptions = _assumption_rows(model)
    tables = {
        "phase6_raw_biogas.csv": pd.DataFrame(_gas_rows(model.streams["raw_biogas"])),
        "phase6_conditioned_biogas.csv": pd.DataFrame(_gas_rows(model.streams["conditioned_biogas"])),
        "phase6_primary_gas_product.csv": pd.DataFrame(_gas_rows(model.streams["primary_gas_product"])),
        "phase6_reject_gas.csv": pd.DataFrame(_gas_rows(model.streams["reject_gas"])),
        "phase6_wastewater.csv": pd.DataFrame(_stream_rows(model.streams["phase6_wastewater"])),
        "phase6_spent_material.csv": pd.DataFrame(_stream_rows(model.streams["phase6_spent_material"])),
        "phase6_mass_balance.csv": pd.DataFrame(_mass_balance_rows(model)),
        "phase6_elemental_balance.csv": pd.DataFrame(_element_rows(model)),
        "phase6_methane_destinations.csv": pd.DataFrame(_methane_destination_rows(model)),
        "phase6_feed_quality.csv": pd.DataFrame(_quality_rows(model)),
        "phase6_energy_summary.csv": pd.DataFrame(_energy_rows(model)),
        "phase6_unit_design.csv": pd.DataFrame(_unit_rows(model)),
        "phase6_assumption_register.csv": pd.DataFrame(assumptions),
        "phase6_model_limitations.csv": pd.DataFrame(limitations),
        "phase6_selected_metrics.csv": pd.DataFrame(
            model.metrics.items(), columns=["metric", "value"]
        ),
    }
    paths: dict[str, Path] = {"flowsheet": flowsheet_path}
    for filename, table in tables.items():
        path = results_dir / filename
        table.to_csv(path, index=False)
        paths[filename] = path

    comparison = pd.DataFrame(_comparison_rows(scenario_models))
    comparison_path = results_dir / "phase6_upgrading_comparison.xlsx"
    with pd.ExcelWriter(comparison_path, engine="openpyxl") as writer:
        comparison.to_excel(writer, sheet_name="Engineering comparison", index=False)
        comparison.set_index("scenario").transpose().rename_axis("metric").reset_index().to_excel(
            writer,
            sheet_name="Metrics by scenario",
            index=False,
        )
        pd.DataFrame(_scenario_readiness_rows()).to_excel(
            writer,
            sheet_name="Scenario readiness",
            index=False,
        )
        pd.DataFrame(
            [{
                "interpretation": (
                    "Engineering comparison only. No alternative is ranked because "
                    "Phase 6 inputs are class-E structural values and no decision "
                    "method is active."
                )
            }]
        ).to_excel(writer, sheet_name="Read me", index=False)
        _format_workbook(writer.book)
    paths["upgrading_comparison"] = comparison_path

    limitations_path = results_dir / "phase6_limitations_and_data_needs.xlsx"
    with pd.ExcelWriter(limitations_path, engine="openpyxl") as writer:
        pd.DataFrame(limitations).to_excel(
            writer,
            sheet_name="Limitation register",
            index=False,
        )
        pd.DataFrame(
            [row for row in limitations if row["priority"] == "high"]
        ).to_excel(writer, sheet_name="High priority data", index=False)
        pd.DataFrame(assumptions).to_excel(
            writer,
            sheet_name="Selected assumptions",
            index=False,
        )
        pd.DataFrame(_scenario_readiness_rows()).to_excel(
            writer,
            sheet_name="Scenario data gates",
            index=False,
        )
        _format_workbook(writer.book)
    paths["limitations_and_data_needs"] = limitations_path

    report_path = results_dir / "phase6_biomethane_upgrading_report.xlsx"
    with pd.ExcelWriter(report_path, engine="openpyxl") as writer:
        tables["phase6_selected_metrics.csv"].to_excel(
            writer, sheet_name="Summary", index=False
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
        sheet_map = {
            "Raw biogas": "phase6_raw_biogas.csv",
            "Conditioned gas": "phase6_conditioned_biogas.csv",
            "Gas product": "phase6_primary_gas_product.csv",
            "Reject gas": "phase6_reject_gas.csv",
            "Wastewater": "phase6_wastewater.csv",
            "Spent material": "phase6_spent_material.csv",
            "Mass balance": "phase6_mass_balance.csv",
            "Element balance": "phase6_elemental_balance.csv",
            "Methane destinations": "phase6_methane_destinations.csv",
            "Feed quality": "phase6_feed_quality.csv",
            "Energy": "phase6_energy_summary.csv",
            "Unit design": "phase6_unit_design.csv",
            "Assumptions": "phase6_assumption_register.csv",
            "Limitations": "phase6_model_limitations.csv",
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
    paths["biomethane_upgrading_report"] = report_path
    model.reports.update(paths)
    return paths
