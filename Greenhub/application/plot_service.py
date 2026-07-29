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

    def specifications(self, run_id: str, scenario: str, literature_pr1: bool) -> tuple[PlotSpecification, ...]:
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
        else:
            series = ()
        return PlotData(specification, series)

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
            axis.bar(positions, [0.0 if value is None else value for value in series.y], label=series.label)
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
