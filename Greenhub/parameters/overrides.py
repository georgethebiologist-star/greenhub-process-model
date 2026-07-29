"""Immutable user and saved-project override records."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from math import isfinite

from .models import JSONScalar


@dataclass(frozen=True)
class ParameterOverride:
    parameter_id: str
    value: JSONScalar
    unit: str | None = None
    reason: str | None = None
    requester: str | None = None
    provenance_note: str | None = None
    rebuild_required: bool | None = None
    timestamp: str | None = None

    def __post_init__(self) -> None:
        if not self.parameter_id:
            raise ValueError("Parameter overrides require parameter_id.")
        if self.value is None:
            raise ValueError("An override value cannot be null; omit the override instead.")
        if isinstance(self.value, float) and not isfinite(self.value):
            raise ValueError("Override values cannot be NaN or infinite.")

    @classmethod
    def create(cls, parameter_id: str, value: JSONScalar, **kwargs: object) -> "ParameterOverride":
        return cls(
            parameter_id=parameter_id,
            value=value,
            timestamp=datetime.now(timezone.utc).isoformat(),
            **kwargs,
        )
