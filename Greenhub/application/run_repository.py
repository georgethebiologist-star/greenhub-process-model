"""Thread-safe in-process run repository."""

from __future__ import annotations

from threading import RLock

from .errors import RunNotFoundError
from .run_context import RunContext


class RunRepository:
    def __init__(self) -> None:
        self._runs: dict[str, RunContext] = {}
        self._lock = RLock()

    def add(self, context: RunContext) -> None:
        with self._lock:
            if context.run_id in self._runs:
                raise ValueError(f"Run '{context.run_id}' already exists.")
            self._runs[context.run_id] = context

    def get(self, run_id: str) -> RunContext:
        with self._lock:
            try:
                return self._runs[run_id]
            except KeyError as error:
                raise RunNotFoundError(f"Unknown run '{run_id}'.") from error

    def list_ids(self) -> tuple[str, ...]:
        with self._lock:
            return tuple(sorted(self._runs))
