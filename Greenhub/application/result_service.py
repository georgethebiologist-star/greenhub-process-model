"""Read-only access to completed structured results."""

from Greenhub.feedstock_resolution import summarize_feedstock_resolution_gates, write_feedstock_resolution_report

from .annual_service import build_annual_summary
from .errors import RunStateError


class ResultService:
    def __init__(self, repository) -> None:
        self.repository = repository

    def _result(self, run_id):
        context = self.repository.get(run_id)
        if context.result is None:
            raise RunStateError(f"Run '{run_id}' has no completed result.")
        return context.result

    def get_summary(self, run_id):
        return self._result(run_id).summary_kpis

    def get_process_areas(self, run_id):
        return self._result(run_id).process_areas

    def get_process_area(self, run_id, process_area_id):
        return next(item for item in self._result(run_id).process_areas if item.process_area_id == process_area_id)

    def get_streams(self, run_id, detail_level="full"):
        return self._result(run_id).streams

    def get_units(self, run_id, detail_level="full"):
        return self._result(run_id).units

    def get_balances(self, run_id):
        return self._result(run_id).balances

    def get_utilities(self, run_id):
        return self._result(run_id).utilities

    def get_validation(self, run_id):
        return self._result(run_id).validation

    def get_provenance(self, run_id):
        return self.repository.get(run_id).resolved_parameters

    def get_exports(self, run_id):
        return self._result(run_id).export_references

    def get_time_series(self, run_id):
        result = self._result(run_id)
        return {
            "time_grid": result.time_grid,
            "feed_supply_series": result.feed_supply_series,
            "throughput_series": result.throughput_series,
            "product_series": result.product_series,
            "residual_series": result.residual_series,
            "utility_series": result.utility_series,
            "balance_residual_series": result.balance_residual_series,
            "process_state_series": result.process_state_series,
            "seasonal_summary": result.seasonal_summary,
        }

    def get_inventory(self, run_id):
        return self._result(run_id).storage_inventory_series

    def get_utilization(self, run_id):
        result = self._result(run_id)
        return {
            "capacity_utilization_series": result.capacity_utilization_series,
            "bottleneck_series": result.bottleneck_series,
        }

    def get_seasonal_summary(self, run_id):
        return self._result(run_id).seasonal_summary

    def get_annual_summary(self, run_id):
        context = self.repository.get(run_id)
        if context.result is None:
            raise RunStateError(f"Run '{run_id}' has no completed result.")
        return build_annual_summary(context.result, context.request)

    def get_feedstock_resolution_readiness(self):
        write_feedstock_resolution_report()
        summary = summarize_feedstock_resolution_gates()
        category_counts = {}
        for item in summary:
            category = str(item["category"])
            category_counts[category] = category_counts.get(category, 0) + int(item["count"])
        category_counts = dict(sorted(category_counts.items()))
        resolvable_fields = sorted(
            {str(item["canonical_field"]) for item in summary if item["category"] == "resolvable_now"}
        )
        blocked_category_counts = {
            category: count
            for category, count in category_counts.items()
            if category.startswith("blocked_")
        }
        return {
            "category_counts": category_counts,
            "artifact_names": {
                "csv": "Greenhub/results/feedstock_resolution_gates.csv",
                "markdown": "docs/feedstock_resolution_readiness.md",
            },
            "top_resolvable_fields": resolvable_fields,
            "blocked_category_counts": blocked_category_counts,
        }
