"""CSV and Excel reporting for GreenHub Phase 3 front-end scenarios."""

from __future__ import annotations

from pathlib import Path

import biosteam as bst
import pandas as pd

from Greenhub.analytical import calculate_elemental_flows
from Greenhub.chemicals import chemicals
from Greenhub.component_metadata import COMPONENT_METADATA
from Greenhub.phase3_metrics import component_flows
from Greenhub.reporting import _format_workbook, _write_unit_tables
from Greenhub.settings import RESULTS_DIR, ensure_results_dir


def _stream_rows(stream) -> list[dict[str, object]]:
    total = float(stream.F_mass)
    return [
        {
            "stream_id": stream.ID,
            "component_id": ID,
            "flow_kg_hr": float(stream.imass[ID]),
            "mass_fraction": float(stream.imass[ID]) / total if total else 0.0,
            "category": COMPONENT_METADATA[ID].category,
            "subcategory": COMPONENT_METADATA[ID].subcategory,
        }
        for ID in chemicals.IDs
    ]


def _unit_partition_rows(unit, *, clarified: bool) -> list[dict[str, object]]:
    inlet_by_component = {
        ID: sum(float(stream.imass[ID]) for stream in unit.ins)
        for ID in chemicals.IDs
    }
    if clarified:
        first, second = unit.outs
        split_map = unit.splits_to_clarified
        source_map = unit.split_sources
        first_name, second_name = "clarified_kg_hr", "sludge_kg_hr"
    else:
        second, first = unit.outs
        split_map = unit.splits_to_juice
        source_map = unit.split_sources
        first_name, second_name = "raw_liquid_kg_hr", "fibre_cake_kg_hr"
    rows = []
    for ID in chemicals.IDs:
        inlet = inlet_by_component[ID]
        actual_split = float(first.imass[ID]) / inlet if inlet else None
        rows.append(
            {
                "component_id": ID,
                "inlet_kg_hr": inlet,
                "configured_fraction_to_liquid": (
                    actual_split if ID == "Water" else split_map[ID]
                ),
                "actual_fraction_to_liquid": actual_split,
                "split_source": "moisture_specification" if ID == "Water" else source_map[ID],
                first_name: float(first.imass[ID]),
                second_name: float(second.imass[ID]),
                "residual_kg_hr": inlet - float(first.imass[ID] + second.imass[ID]),
            }
        )
    return rows


def _pef_rows(model) -> list[dict[str, object]]:
    if "U201" not in model.units:
        return []
    unit = model.units["U201"]
    rows = [
        {
            "metric": "electricity",
            "value": float(unit.power_utility.consumption),
            "unit": "kW",
            "method": "wet t/h x kWh/t wet",
        },
        {
            "metric": "temperature_rise",
            "value": float(unit.outs[0].T - unit.ins[0].T),
            "unit": "degC",
            "method": unit.parameters.temperature_mode,
        },
        {
            "metric": "documented_mass_loss",
            "value": float(unit.outs[1].F_mass),
            "unit": "kg/hr",
            "method": "separate conserved loss stream",
        },
    ]
    rows.extend(
        {
            "metric": transfer,
            "value": value,
            "unit": "kg/hr",
            "method": "one-to-one empirical pool transfer",
        }
        for transfer, value in unit.transfers_kg_hr.items()
    )
    return rows


def _mass_balance_rows(model) -> list[dict[str, object]]:
    inlet = {
        ID: sum(float(stream.imass[ID]) for stream in model.system.ins)
        for ID in chemicals.IDs
    }
    expected = dict(inlet)
    if "U201" in model.units:
        for name, amount in model.units["U201"].transfers_kg_hr.items():
            source, target = name.split("_to_", 1)
            expected[source] -= float(amount)
            expected[target] += float(amount)
    outlet = {
        ID: sum(float(stream.imass[ID]) for stream in model.system.outs)
        for ID in chemicals.IDs
    }
    return [
        {
            "component_id": ID,
            "external_inlet_kg_hr": inlet[ID],
            "declared_transfer_adjusted_inlet_kg_hr": expected[ID],
            "external_outlet_kg_hr": outlet[ID],
            "residual_kg_hr": expected[ID] - outlet[ID],
        }
        for ID in chemicals.IDs
    ]


def _element_rows(model) -> list[dict[str, object]]:
    inlet = {
        ID: sum(float(stream.imass[ID]) for stream in model.system.ins)
        for ID in chemicals.IDs
    }
    outlet = {
        ID: sum(float(stream.imass[ID]) for stream in model.system.outs)
        for ID in chemicals.IDs
    }
    inlet_elements = calculate_elemental_flows(inlet)
    outlet_elements = calculate_elemental_flows(outlet)
    return [
        {
            "element": element,
            "inlet_kg_hr": inlet_elements[element],
            "outlet_kg_hr": outlet_elements[element],
            "residual_kg_hr": inlet_elements[element] - outlet_elements[element],
        }
        for element in inlet_elements
    ]


def _energy_rows(model) -> list[dict[str, object]]:
    rows = [
        {
            "scenario": model.scenario.scenario_id,
            "unit_id": ID,
            "unit_operation": unit.line,
            "electricity_kw": float(unit.power_utility.consumption),
            "purchase_cost_available": bool(unit.purchase_cost),
            "cost_comment": (
                "BioSTEAM built-in correlation"
                if unit.purchase_cost
                else "No approved Phase 3 purchase-cost correlation"
            ),
        }
        for ID, unit in model.units.items()
    ]
    rows.append(
        {
            "scenario": model.scenario.scenario_id,
            "unit_id": "TOTAL",
            "unit_operation": "Front-end total",
            "electricity_kw": sum(row["electricity_kw"] for row in rows),
            "purchase_cost_available": any(row["purchase_cost_available"] for row in rows),
            "cost_comment": "Pumping is zero because no pressure-rise basis is available.",
        }
    )
    return rows


def _assumption_rows(model) -> list[dict[str, object]]:
    rows = []
    for record in model.input_bundle.parameter_records:
        rows.append(
            {
                "input_parameter": record.python_name,
                "value": record.value,
                "unit": record.unit,
                "source": record.reference,
                "measurement_status": record.measurement_status,
                "source_class": record.source_class,
                "scenario": model.scenario.scenario_id,
                "month": model.input_bundle.selected_month,
                "minimum": record.minimum,
                "maximum": record.maximum,
                "calculation_method": record.calculation_method,
                "warning": (
                    "Structural-test placeholder; replace before interpretation."
                    if record.source_class == "E" and record.value is not None
                    else record.comment
                ),
            }
        )
    rows.extend(
        {
            "input_parameter": "model_warning",
            "value": warning,
            "unit": None,
            "source": None,
            "measurement_status": "calculated",
            "source_class": "E",
            "scenario": model.scenario.scenario_id,
            "month": model.input_bundle.selected_month,
            "minimum": None,
            "maximum": None,
            "calculation_method": "model diagnostic",
            "warning": warning,
        }
        for warning in model.validation.warnings
    )
    return rows


def save_phase3_reports(
    model,
    *,
    flowsheet_path: Path,
    scenario_models: tuple[object, ...],
    seasonal_result,
    results_dir: Path = RESULTS_DIR,
) -> dict[str, Path]:
    """Write the required detailed Phase 3 CSV and Excel outputs."""

    ensure_results_dir()
    results_dir.mkdir(parents=True, exist_ok=True)
    empty_stream_columns = [
        "stream_id", "component_id", "flow_kg_hr", "mass_fraction", "category", "subcategory"
    ]
    tables = {
        "phase3_monthly_results.csv": pd.DataFrame(seasonal_result.monthly_rows),
        "pef_performance.csv": pd.DataFrame(_pef_rows(model), columns=["metric", "value", "unit", "method"]),
        "press_partitioning.csv": pd.DataFrame(
            _unit_partition_rows(model.units["S201"], clarified=False) if "S201" in model.units else []
        ),
        "centrifuge_partitioning.csv": pd.DataFrame(_unit_partition_rows(model.units["C301"], clarified=True)),
        "fibre_cake_composition.csv": pd.DataFrame(
            _stream_rows(model.streams["fibre_cake"]) if "fibre_cake" in model.streams else [],
            columns=empty_stream_columns,
        ),
        "raw_liquid_composition.csv": pd.DataFrame(_stream_rows(model.streams["raw_liquid_fraction"])),
        "clarified_liquid_composition.csv": pd.DataFrame(_stream_rows(model.streams["clarified_liquid"])),
        "primary_sludge_composition.csv": pd.DataFrame(_stream_rows(model.streams["primary_sludge"])),
        "phase3_mass_balance.csv": pd.DataFrame(_mass_balance_rows(model)),
        "phase3_elemental_balance.csv": pd.DataFrame(_element_rows(model)),
        "phase3_energy_summary.csv": pd.DataFrame(_energy_rows(model)),
        "phase3_assumption_register.csv": pd.DataFrame(_assumption_rows(model)),
    }
    paths: dict[str, Path] = {"flowsheet": flowsheet_path}
    for filename, table in tables.items():
        path = results_dir / filename
        table.to_csv(path, index=False)
        paths[filename] = path

    comparison = pd.DataFrame([candidate.metrics for candidate in scenario_models])
    comparison_by_metric = (
        comparison.set_index("scenario")
        .transpose()
        .rename_axis("metric")
        .reset_index()
    )
    comparison_path = results_dir / "phase3_scenario_comparison.xlsx"
    with pd.ExcelWriter(comparison_path, engine="openpyxl") as writer:
        comparison_by_metric.to_excel(writer, sheet_name="Scenario comparison", index=False)
        tables["phase3_monthly_results.csv"].to_excel(writer, sheet_name="Monthly selected", index=False)
        pd.DataFrame([seasonal_result.annual_totals]).to_excel(writer, sheet_name="Annual totals", index=False)
        pd.DataFrame(
            [
                {
                    "scenario": candidate.scenario.scenario_id,
                    "warning": warning,
                }
                for candidate in scenario_models
                for warning in candidate.validation.warnings
            ]
        ).to_excel(writer, sheet_name="Scenario warnings", index=False)
        _format_workbook(writer.book)
    paths["scenario_comparison"] = comparison_path

    report_path = results_dir / "phase3_front_end_report.xlsx"
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
            "Unit results",
            bst.report.unit_result_tables(
                model.system.units,
                include_utilities=True,
                include_total_cost=True,
                include_installed_cost=True,
            ),
        )
        pd.DataFrame(model.raw_liquid_interface.indicators.items(), columns=["indicator", "value"]).to_excel(
            writer, sheet_name="Raw liquid interface", index=False
        )
        tables["pef_performance.csv"].to_excel(writer, sheet_name="PEF", index=False)
        tables["press_partitioning.csv"].to_excel(writer, sheet_name="Press", index=False)
        tables["centrifuge_partitioning.csv"].to_excel(writer, sheet_name="Centrifuge", index=False)
        tables["phase3_energy_summary.csv"].to_excel(writer, sheet_name="Energy", index=False)
        tables["phase3_mass_balance.csv"].to_excel(writer, sheet_name="Mass balance", index=False)
        tables["phase3_elemental_balance.csv"].to_excel(writer, sheet_name="Element balance", index=False)
        tables["phase3_assumption_register.csv"].to_excel(writer, sheet_name="Assumptions", index=False)
        pd.DataFrame([{"validation_report": model.validation.report}]).to_excel(
            writer, sheet_name="Validation", index=False
        )
        if flowsheet_path.exists():
            from openpyxl.drawing.image import Image as XLImage

            worksheet = writer.book.create_sheet("Flowsheet")
            worksheet.add_image(XLImage(str(flowsheet_path)), "A1")
        _format_workbook(writer.book)
    paths["front_end_report"] = report_path
    return paths
