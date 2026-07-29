"""Isolated run state and reproducibility metadata."""

from __future__ import annotations

import hashlib
import importlib.metadata
import subprocess
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import StrEnum
from pathlib import Path
from uuid import uuid4

from Greenhub.input_data import INPUT_WORKBOOK_PATH
from Greenhub.parameters.models import ResolvedParameter
from Greenhub.settings import RESULTS_DIR

from .contracts import SimulationRequest


class RunState(StrEnum):
    VALIDATING = "validating"
    RESOLVING_PARAMETERS = "resolving_parameters"
    BUILDING_SYSTEM = "building_system"
    SIMULATING = "simulating"
    VALIDATING_RESULTS = "validating_results"
    GENERATING_OUTPUTS = "generating_outputs"
    COMPLETED = "completed"
    FAILED = "failed"


def _sha256(path: Path) -> str | None:
    if not path.exists():
        return None
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _git_commit() -> str | None:
    try:
        result = subprocess.run(
            ("git", "rev-parse", "HEAD"),
            cwd=Path(__file__).resolve().parents[2],
            check=True,
            capture_output=True,
            text=True,
        )
    except (OSError, subprocess.CalledProcessError):
        return None
    return result.stdout.strip() or None


def reproducibility_metadata() -> dict[str, object]:
    versions = {}
    for package in ("biosteam", "thermosteam", "pandas", "openpyxl", "scipy"):
        try:
            versions[package] = importlib.metadata.version(package)
        except importlib.metadata.PackageNotFoundError:
            versions[package] = None
    return {
        "git_commit": _git_commit(),
        "software_versions": versions,
        "workbook_checksum_sha256": _sha256(INPUT_WORKBOOK_PATH),
        "source_dataset_checksum_registry": "data/global_audit_package/source_dataset_checksums.csv",
    }


@dataclass
class RunContext:
    run_id: str
    request: SimulationRequest
    run_directory: Path
    created_at: str
    state: RunState = RunState.VALIDATING
    state_history: list[tuple[str, str]] = field(default_factory=list)
    resolved_parameters: tuple[ResolvedParameter, ...] = ()
    model: object | None = None
    result: object | None = None
    error: str | None = None
    reproducibility: dict[str, object] = field(default_factory=reproducibility_metadata)

    @classmethod
    def create(
        cls,
        request: SimulationRequest,
        root: Path = RESULTS_DIR / "runs",
    ) -> "RunContext":
        run_id = uuid4().hex
        created = datetime.now(timezone.utc).isoformat()
        directory = root / run_id
        directory.mkdir(parents=True, exist_ok=False)
        context = cls(run_id, request, directory, created)
        context.state_history.append((RunState.VALIDATING.value, created))
        return context

    def transition(self, state: RunState) -> None:
        self.state = state
        self.state_history.append((state.value, datetime.now(timezone.utc).isoformat()))

    @property
    def relative_directory(self) -> str:
        return f"runs/{self.run_id}"
