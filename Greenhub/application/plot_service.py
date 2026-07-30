"""Structured plot data and optional static rendering."""

from __future__ import annotations

import csv
from pathlib import Path

from Greenhub.parameters.serialization import write_json

from .contracts.results import PlotData, PlotSeries, PlotSpecification
from .errors import RunStateError


class PlotService:
    def __init__(self, repository=None) -> None:
        self.repository = repository

    def specifications(
        self, run_id: str, scenario: str, literature_pr1: bool, seasonal=None
    ) -> tuple[PlotSpecification, ...]:
        common = dict(scenario=scenario, run_id=run_id, warnings=(), availability_status="available")
        plots = [
            PlotSpecification(
                "SYS-AREA-MASS", "Process-area outlet mass", "integrated_system",
                "Process area", "Outlet mass flow", None, "kg/hr",
                ("process_areas.outlet_stream_ids", "streams.total_mass"), **common,
            ),
            PlotSpecification(
                "VALIDATION-RESIDUALS", "Mass and elemental balance residuals", "integrated_system",
                "Balance", "Residual", None, "kg/hr", ("balances.residual",), **common,
            ),
            PlotSpecification(
                "SYS-UNIT-POWER", "Unit electricity demand", "shared_utilities_and_supporting_operations",
                "Unit", "Electricity demand", None, "kW", ("units.power",), **common,
            ),
            PlotSpecification(
                "DATA-READINESS", "Dataset readiness distribution", "data_governance",
                "Readiness class", "Dataset count", None, "count", ("dataset_readiness",), **common,
            ),
            PlotSpecification(
                "STATE-FLOW", "Process-state flow by active unit", "integrated_system",
                "Unit", "Flow", None, "kg/hr", ("process_state_snapshots.flow_kg_hr",), **common,
            ),
            PlotSpecification(
                "STATE-COD", "COD fate by active unit", "integrated_system",
                "Unit", "COD", None, "kg/hr", ("component_fate.cod_kg_hr",), **common,
            ),
            PlotSpecification(
                "INVENTORY-EVOLUTION", "Quasi-dynamic inventory evolution", "integrated_system",
                "Inventory", "Final inventory", None, "kg", ("inventory_evolution.final_kg",), **common,
            ),
        ]
        plots.append(
            PlotSpecification(
                "PR-PRECIP-RECOVERY", "R401 direct precipitation recovery", "protein_recovery",
                "Scenario", "Recovered fraction", None, "fraction",
                ("units.R401.design_results.Acid recovery",),
                scenario=scenario,
                run_id=run_id,
                warnings=(
                    "REC-001 is a grass-clover total-N recovery mapped to the GreenHub soluble-protein pool.",
                ) if literature_pr1 else ("Available only for PR1 literature_default activation.",),
                availability_status="available" if literature_pr1 else "unavailable_scenario",
            )
        )
        if seasonal is not None:
            plots.extend(self._seasonal_specifications(run_id, scenario, seasonal))
        return tuple(plots)

    @staticmethod
    def _seasonal_specifications(run_id: str, scenario: str, seasonal) -> tuple[PlotSpecification, ...]:
        common = dict(scenario=scenario, run_id=run_id, warnings=(), availability_status="available")

        def spec(plot_id, title, y_label, y_unit, fields, area="integrated_system"):
            return PlotSpecification(
                plot_id, title, area, "Time", y_label, None, y_unit, tuple(fields), **common
            )

        plots = [
            spec("SEASONAL-FEED", "Biomass available and collected", "Wet biomass", "kg", ("feed_supply_series",), "feedstock_and_characterization"),
            spec("SEASONAL-PROCESSED", "Biomass processed and unprocessed", "Wet biomass", "kg", ("throughput_series", "storage_inventory_series"), "feedstock_and_characterization"),
            spec("SEASONAL-INVENTORY", "Storage inventory", "Wet inventory", "kg", ("storage_inventory_series.inventory_remaining_kg",), "feedstock_and_characterization"),
            spec("SEASONAL-STORAGE-AGE", "Storage age", "Average storage age", "h", ("storage_inventory_series.storage_age_h",), "feedstock_and_characterization"),
            spec("SEASONAL-THROUGHPUT", "Process throughput", "Throughput", "kg/hr", ("throughput_series.actual_throughput_kg_hr",)),
            spec("SEASONAL-MASS-RESIDUAL", "Seasonal mass-balance residual", "Residual", "kg", ("balance_residual_series.overall_mass_residual_kg",)),
        ]
        if seasonal.capacity_utilization_series:
            plots.append(spec("SEASONAL-UTILIZATION", "Unit capacity utilization", "Utilization", "fraction", ("capacity_utilization_series",)))
        if any(item["bottleneck_unit"] for item in seasonal.bottleneck_series):
            plots.append(spec("SEASONAL-BOTTLENECK", "Bottleneck unit over time", "Bottleneck indicator", "binary", ("bottleneck_series",)))
        product_names = sorted({name for row in seasonal.product_series for name, value in row["products_kg"].items() if value > 0.0})
        if product_names:
            plots.append(spec("SEASONAL-PRODUCTS", "Product generation", "Product mass", "kg", ("product_series",)))
        if "dry_protein_product" in product_names:
            plots.append(spec("SEASONAL-PROTEIN", "Protein production", "Dry protein product", "kg", ("product_series.dry_protein_product",), "protein_recovery"))
        if "biomethane" in product_names:
            plots.append(spec("SEASONAL-BIOMETHANE", "Biomethane production", "Biomethane", "kg", ("product_series.biomethane",), "biogas_conditioning_and_upgrading"))
        nutrients = {"phosphorus_product", "ammonium_product", "potassium_concentrate", "nutrient_rich_solids"}
        if nutrients & set(product_names):
            plots.append(spec("SEASONAL-NUTRIENTS", "Nutrient product generation", "Product mass", "kg", ("product_series",), "digestate_treatment_and_nutrient_recovery"))
        for key, plot_id, title in (
            ("electricity_kwh", "SEASONAL-ELECTRICITY", "Electricity demand"),
            ("heating_kwh", "SEASONAL-HEATING", "Heating demand"),
            ("cooling_kwh", "SEASONAL-COOLING", "Cooling demand"),
        ):
            if any(float(item[key]) > 0.0 for item in seasonal.utility_series):
                plots.append(spec(plot_id, title, "Energy", "kWh", (f"utility_series.{key}",), "shared_utilities_and_supporting_operations"))
        elements = {name for row in seasonal.balance_residual_series for name in row["element_residuals_kg"]}
        if elements & {"carbon", "nitrogen", "phosphorus", "potassium"}:
            plots.append(spec("SEASONAL-ELEMENT-RESIDUALS", "C/N/P/K balance residuals", "Residual", "kg", ("balance_residual_series.element_residuals_kg",)))
        return tuple(plots)

    def build_plot_data(self, result, plot_id: str) -> PlotData:
        specifications = {item.plot_id: item for item in result.plots}
        try:
            specification = specifications[plot_id]
        except KeyError as error:
            raise KeyError(f"Unknown plot '{plot_id}'.") from error
        if specification.availability_status != "available":
            return PlotData(specification, ())
        streams = {item.stream_id: item for item in result.streams}
        if plot_id == "SYS-AREA-MASS":
            x = []
            y = []
            for area in result.process_areas:
                x.append(area.display_name)
                y.append(sum(streams[item].total_mass.value or 0.0 for item in area.outlet_stream_ids if item in streams))
            series = (PlotSeries("outlet_mass", "Outlet mass", tuple(x), tuple(y)),)
        elif plot_id == "VALIDATION-RESIDUALS":
            series = (
                PlotSeries(
                    "residual", "Residual",
                    tuple(item.balance_id for item in result.balances),
                    tuple(item.residual.value for item in result.balances),
                ),
            )
        elif plot_id == "SYS-UNIT-POWER":
            active = [item for item in result.units if (item.power.value or 0.0) > 0.0]
            series = (
                PlotSeries(
                    "power", "Electricity",
                    tuple(item.unit_id for item in active),
                    tuple(item.power.value for item in active),
                ),
            )
        elif plot_id == "DATA-READINESS":
            series = (
                PlotSeries(
                    "datasets", "Datasets",
                    tuple(result.dataset_readiness),
                    tuple(result.dataset_readiness.values()),
                ),
            )
        elif plot_id == "PR-PRECIP-RECOVERY":
            unit = next(item for item in result.units if item.unit_id == "R401")
            recovery = unit.design_results["Acid recovery"].value
            series = (PlotSeries("recovery", "Recovery", (result.selected_scenarios.protein_recovery,), (recovery,)),)
        elif plot_id == "STATE-FLOW":
            series = (PlotSeries("flow", "Flow", tuple(x["unit_id"] for x in result.process_state_snapshots), tuple(x["flow_kg_hr"] for x in result.process_state_snapshots)),)
        elif plot_id == "STATE-COD":
            series = (PlotSeries("cod", "COD", tuple(x["unit_id"] for x in result.component_fate), tuple(x["cod_kg_hr"] for x in result.component_fate)),)
        elif plot_id == "INVENTORY-EVOLUTION":
            series = (PlotSeries("inventory", "Final inventory", tuple(x["inventory_id"] for x in result.inventory_evolution), tuple(x["final_kg"] for x in result.inventory_evolution)),)
        elif plot_id.startswith("SEASONAL-"):
            series = self._build_seasonal_plot(result, plot_id)
        else:
            series = ()
        return PlotData(specification, series)

    @staticmethod
    def _build_seasonal_plot(result, plot_id: str) -> tuple[PlotSeries, ...]:
        if plot_id == "SEASONAL-FEED":
            rows = result.feed_supply_series
            x = tuple(item["time"] for item in rows)
            return (
                PlotSeries("available", "Available", x, tuple(item["available_wet_biomass_kg"] for item in rows)),
                PlotSeries("collected", "Collected", x, tuple(item["collected_biomass_kg"] for item in rows)),
            )
        if plot_id == "SEASONAL-PROCESSED":
            rows = result.throughput_series
            x = tuple(item["time"] for item in rows)
            return (
                PlotSeries("processed", "Processed", x, tuple(item["actual_throughput_kg"] for item in rows)),
                PlotSeries("unprocessed", "Ending inventory", x, tuple(item["backlog_kg"] for item in rows)),
            )
        if plot_id in {"SEASONAL-INVENTORY", "SEASONAL-STORAGE-AGE"}:
            key = "inventory_remaining_kg" if plot_id.endswith("INVENTORY") else "storage_age_h"
            rows = result.storage_inventory_series
            return (PlotSeries(key, key.replace("_", " ").title(), tuple(item["time"] for item in rows), tuple(item[key] for item in rows)),)
        if plot_id == "SEASONAL-THROUGHPUT":
            rows = result.throughput_series
            return (PlotSeries("throughput", "Throughput", tuple(item["time"] for item in rows), tuple(item["actual_throughput_kg_hr"] for item in rows)),)
        if plot_id == "SEASONAL-UTILIZATION":
            rows = result.capacity_utilization_series
            times = tuple(item["time"] for item in result.throughput_series)
            return tuple(
                PlotSeries(unit, unit, times, tuple(next((row["utilization"] for row in rows if row["time"] == time and row["unit_id"] == unit), 0.0) for time in times))
                for unit in sorted({item["unit_id"] for item in rows})
            )
        if plot_id == "SEASONAL-BOTTLENECK":
            rows = result.bottleneck_series
            return tuple(
                PlotSeries(unit, unit, tuple(item["time"] for item in rows), tuple(1.0 if item["bottleneck_unit"] == unit else 0.0 for item in rows))
                for unit in sorted({item["bottleneck_unit"] for item in rows if item["bottleneck_unit"]})
            )
        if plot_id in {"SEASONAL-PRODUCTS", "SEASONAL-PROTEIN", "SEASONAL-BIOMETHANE", "SEASONAL-NUTRIENTS"}:
            rows = result.product_series
            names = sorted({name for item in rows for name, value in item["products_kg"].items() if value > 0.0})
            filters = {
                "SEASONAL-PROTEIN": {"dry_protein_product"},
                "SEASONAL-BIOMETHANE": {"biomethane"},
                "SEASONAL-NUTRIENTS": {"phosphorus_product", "ammonium_product", "potassium_concentrate", "nutrient_rich_solids"},
            }
            if plot_id in filters:
                names = [name for name in names if name in filters[plot_id]]
            return tuple(
                PlotSeries(name, name.replace("_", " ").title(), tuple(item["time"] for item in rows), tuple(item["products_kg"].get(name, 0.0) for item in rows))
                for name in names
            )
        utility_keys = {
            "SEASONAL-ELECTRICITY": "electricity_kwh",
            "SEASONAL-HEATING": "heating_kwh",
            "SEASONAL-COOLING": "cooling_kwh",
        }
        if plot_id in utility_keys:
            key = utility_keys[plot_id]
            rows = result.utility_series
            return (PlotSeries(key, key.replace("_", " ").title(), tuple(item["time"] for item in rows), tuple(item[key] for item in rows)),)
        if plot_id == "SEASONAL-MASS-RESIDUAL":
            rows = result.balance_residual_series
            return (PlotSeries("mass_residual", "Mass residual", tuple(item["time"] for item in rows), tuple(item["overall_mass_residual_kg"] for item in rows)),)
        if plot_id == "SEASONAL-ELEMENT-RESIDUALS":
            rows = result.balance_residual_series
            symbols = {
                "carbon": "C",
                "nitrogen": "N",
                "phosphorus": "P",
                "potassium": "K",
            }
            names = [name for name in symbols if any(name in item["element_residuals_kg"] for item in rows)]
            return tuple(
                PlotSeries(name, symbols[name], tuple(item["time"] for item in rows), tuple(item["element_residuals_kg"].get(name, 0.0) for item in rows))
                for name in names
            )
        return ()

    def list_plots(self, run_id: str):
        return self._result(run_id).plots

    def get_plot_data(self, run_id: str, plot_id: str) -> PlotData:
        return self.build_plot_data(self._result(run_id), plot_id)

    def _result(self, run_id: str):
        context = self.repository.get(run_id)
        if context.result is None:
            raise RunStateError(f"Run '{run_id}' has no completed result.")
        return context.result

    def export_plot_data(self, run_id: str, plot_id: str, output_dir: Path) -> dict[str, str]:
        data = self.get_plot_data(run_id, plot_id)
        output_dir.mkdir(parents=True, exist_ok=True)
        json_path = write_json(output_dir / f"{plot_id}.json", data)
        csv_path = output_dir / f"{plot_id}.csv"
        with csv_path.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=("series_id", "label", "x", "y"))
            writer.writeheader()
            for series in data.series:
                for x, y in zip(series.x, series.y):
                    writer.writerow({"series_id": series.series_id, "label": series.label, "x": x, "y": y})
        references = {"json": json_path.name, "csv": csv_path.name}
        if data.series:
            for format_name in ("png", "svg"):
                path = self._render(data, output_dir / f"{plot_id}.{format_name}")
                references[format_name] = path.name
        return references

    def render_plot(self, run_id: str, plot_id: str, format: str = "png") -> str:
        if format not in {"png", "svg"}:
            raise ValueError("Static plot format must be png or svg.")
        context = self.repository.get(run_id)
        data = self.get_plot_data(run_id, plot_id)
        if not data.series:
            raise RunStateError(f"Plot '{plot_id}' is not available for this run.")
        path = self._render(data, context.run_directory / "plots" / f"{plot_id}.{format}")
        return f"plots/{path.name}"

    @staticmethod
    def _render(data: PlotData, path: Path) -> Path:
        import matplotlib

        matplotlib.use("Agg", force=True)
        import matplotlib.pyplot as plt

        path.parent.mkdir(parents=True, exist_ok=True)
        figure, axis = plt.subplots(figsize=(9, 5.4))
        for series in data.series:
            positions = list(range(len(series.x)))
            values = [0.0 if value is None else value for value in series.y]
            if data.specification.plot_id.startswith("SEASONAL-"):
                axis.plot(positions, values, marker="o", linewidth=2.0, label=series.label)
            else:
                axis.bar(positions, values, label=series.label)
            axis.set_xticks(positions, [str(value) for value in series.x], rotation=35, ha="right")
        axis.set_title(data.specification.title)
        axis.set_xlabel(data.specification.x_axis_label)
        axis.set_ylabel(
            f"{data.specification.y_axis_label} [{data.specification.y_unit}]"
            if data.specification.y_unit else data.specification.y_axis_label
        )
        if len(data.series) > 1:
            axis.legend()
        figure.tight_layout()
        figure.savefig(path, dpi=180)
        plt.close(figure)
        return path
