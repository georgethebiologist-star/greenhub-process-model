"""Deterministic monthly and daily grids for quasi-dynamic runs."""

from __future__ import annotations

from calendar import monthrange
from dataclasses import asdict, dataclass
from datetime import date, timedelta

DEFAULT_SEASON_START = "2026-05-01"
DEFAULT_SEASON_END = "2026-11-30"


@dataclass(frozen=True)
class TimeGridStep:
    index: int
    start_date: str
    end_date: str
    label: str
    duration_days: int
    duration_hours: float

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


def _parse(value: str, name: str) -> date:
    try:
        return date.fromisoformat(value)
    except (TypeError, ValueError) as error:
        raise ValueError(f"{name} must use ISO date format YYYY-MM-DD.") from error


def generate_time_grid(
    start_date: str | None = None,
    end_date: str | None = None,
    time_step: str = "monthly",
) -> tuple[TimeGridStep, ...]:
    """Create inclusive calendar steps, clipped to the requested boundaries."""

    start = _parse(start_date or DEFAULT_SEASON_START, "start_date")
    end = _parse(end_date or DEFAULT_SEASON_END, "end_date")
    if end < start:
        raise ValueError("end_date must not precede start_date.")
    if time_step not in {"monthly", "daily"}:
        raise ValueError("time_step must be 'monthly' or 'daily'.")
    steps = []
    cursor = start
    while cursor <= end:
        if time_step == "daily":
            step_end = cursor
            label = cursor.isoformat()
        else:
            last_day = monthrange(cursor.year, cursor.month)[1]
            step_end = min(date(cursor.year, cursor.month, last_day), end)
            label = cursor.strftime("%Y-%m")
        days = (step_end - cursor).days + 1
        steps.append(
            TimeGridStep(len(steps), cursor.isoformat(), step_end.isoformat(), label, days, days * 24.0)
        )
        cursor = step_end + timedelta(days=1)
    return tuple(steps)
