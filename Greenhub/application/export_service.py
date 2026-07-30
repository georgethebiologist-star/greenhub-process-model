"""Complete per-run JSON/CSV result export."""

from __future__ import annotations

from pathlib import Path

from Greenhub.parameters.provenance import provenance_record
from Greenhub.parameters.serialization import to_json_compatible, write_json, write_records_csv


class ExportService:
    def export_run(self, context, result, plot_service) -> dict[str, str]:
        root = context.run_directory
        (root / "plots").mkdir(exist_ok=True)
        (root / "reports").mkdir(exist_ok=True)
        references: dict[str, str] = {}

        def json_file(name, value):
            write_json(root / name, value)
            references[name.rsplit(".", 1)[0]] = name

        json_file("simulation_request.json", context.request)
        json_file("resolved_parameters.json", context.resolved_parameters)
        write_records_csv(
            root / "resolved_parameters.csv",
            (to_json_compatible(item) for item in context.resolved_parameters),
        )
        references["resolved_parameters_csv"] = "resolved_parameters.csv"
        json_file("provenance.json", tuple(provenance_record(item) for item in context.resolved_parameters))
        json_file("summary.json", result.summary_kpis)
        json_file("process_areas.json", result.process_areas)
        json_file("streams.json", result.streams)
        json_file("units.json", result.units)
        json_file("balances.json", result.balances)
        json_file("utilities.json", result.utilities)
        for field_name in ("process_state_snapshots", "process_state_history", "unit_state_summaries", "parameter_sensitivity", "equation_usage", "component_fate", "utility_consumption", "inventory_evolution"):
            json_file(f"{field_name}.json", getattr(result, field_name))
        seasonal_fields = (
            "time_grid", "feed_supply_series", "storage_inventory_series", "throughput_series",
            "capacity_utilization_series", "bottleneck_series", "product_series", "residual_series",
            "utility_series", "balance_residual_series", "process_state_series",
        )
        for field_name in seasonal_fields:
            values = getattr(result, field_name)
            json_file(f"{field_name}.json", values)
            if values:
                write_records_csv(
                    root / f"{field_name}.csv",
                    (to_json_compatible(item) for item in values),
                )
                references[f"{field_name}_csv"] = f"{field_name}.csv"
        json_file("seasonal_summary.json", result.seasonal_summary)
        json_file("products.json", result.products)
        json_file("validation.json", result.validation)
        json_file("graph.json", result.graph)
        json_file("simulation_result.json", result)
        for name, records in (
            ("streams", result.streams),
            ("units", result.units),
            ("balances", result.balances),
            ("utilities", result.utilities),
            ("products", result.products),
            ("validation", result.validation.issues),
        ):
            write_records_csv(root / f"{name}.csv", (to_json_compatible(item) for item in records))
            references[f"{name}_csv"] = f"{name}.csv"
        plot_manifest = []
        for specification in result.plots:
            files = plot_service.export_plot_data(context.run_id, specification.plot_id, root / "plots")
            plot_manifest.append(
                {
                    "plot_id": specification.plot_id,
                    "availability_status": specification.availability_status,
                    "files": {key: f"plots/{value}" for key, value in files.items()},
                }
            )
        json_file("plot_manifest.json", plot_manifest)
        manifest = {
            "schema_version": result.schema_version,
            "run_id": context.run_id,
            "status": result.status,
            "state_history": context.state_history,
            "files": dict(sorted(references.items())),
            "reproducibility": context.reproducibility,
        }
        json_file("run_manifest.json", manifest)
        return dict(sorted(references.items()))
