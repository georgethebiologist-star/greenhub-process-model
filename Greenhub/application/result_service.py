"""Read-only access to completed structured results."""

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
