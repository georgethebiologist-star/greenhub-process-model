"""Load the completed missing-data register as traceable model inputs.

The register contains both usable screening inputs and unresolved/blocked items.
This module keeps those classes distinct so downstream calculations can consume
only explicit numeric baselines while reports retain the full provenance.
"""

from __future__ import annotations

import csv
import re
from dataclasses import dataclass
from pathlib import Path

from Greenhub.settings import DATA_DIR


DEFAULT_COMPLETE_DATA_PATH = (
    DATA_DIR / "Pre-treatment" / "Feedstock" / "expanded_process_data_register.csv"
)


@dataclass(frozen=True)
class CompletedInputRecord:
    """One row from the completed register, including its provenance."""

    gap_id: str
    category: str
    name: str
    value_text: str
    units: str
    scenario_or_basis: str
    value_status: str
    evidence_type: str
    source_reference: str
    numeric_value: float | None
    numeric_lower: float | None
    numeric_upper: float | None
    usable_as_screening_input: bool


_NUMBER = re.compile(r"\d+(?:[.,]\d+)?(?:[eE][-+]?\d+)?")


def _numbers(text: str) -> list[float]:
    values: list[float] = []
    for match in _NUMBER.findall(text or ""):
        try:
            values.append(float(match.replace(",", ".")))
        except ValueError:
            continue
    return values


def _numeric_summary(value_text: str) -> tuple[float | None, float | None, float | None]:
    values = _numbers(value_text)
    if not values:
        return None, None, None
    if len(values) == 1:
        return values[0], values[0], values[0]
    return None, min(values), max(values)


def load_completed_input_register(
    path: Path = DEFAULT_COMPLETE_DATA_PATH,
) -> tuple[CompletedInputRecord, ...]:
    """Load all completed-register rows without dropping unresolved values."""

    if not path.exists():
        raise FileNotFoundError(f"Completed input register not found: {path}")
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))
    required = {
        "gap_id",
        "category",
        "missing_or_incomplete_item",
        "filled_baseline_value_or_range",
        "filled_units",
        "scenario_or_basis",
        "evidence_type",
        "source_url_or_project_reference",
        "value_status",
    }
    missing = required - set(rows[0] if rows else ())
    if missing:
        raise ValueError(f"Completed input register is missing columns: {sorted(missing)}")

    records: list[CompletedInputRecord] = []
    for row in rows:
        value_text = (row.get("filled_baseline_value_or_range") or "").strip()
        numeric_value, numeric_lower, numeric_upper = _numeric_summary(value_text)
        status = (row.get("value_status") or "").strip()
        usable = (
            numeric_value is not None
            and "blocked" not in status.casefold()
            and "not assigned" not in value_text.casefold()
            and "no single" not in value_text.casefold()
            and "vendor quotes required" not in value_text.casefold()
        )
        records.append(
            CompletedInputRecord(
                gap_id=(row.get("gap_id") or "").strip(),
                category=(row.get("category") or "").strip(),
                name=(row.get("missing_or_incomplete_item") or "").strip(),
                value_text=value_text,
                units=(row.get("filled_units") or "").strip(),
                scenario_or_basis=(row.get("scenario_or_basis") or "").strip(),
                value_status=status,
                evidence_type=(row.get("evidence_type") or "").strip(),
                source_reference=(row.get("source_url_or_project_reference") or "").strip(),
                numeric_value=numeric_value,
                numeric_lower=numeric_lower,
                numeric_upper=numeric_upper,
                usable_as_screening_input=usable,
            )
        )
    return tuple(records)


def completed_input_summary(path: Path = DEFAULT_COMPLETE_DATA_PATH) -> dict[str, int]:
    """Return compact counts for reporting and input validation."""

    records = load_completed_input_register(path)
    return {
        "record_count": len(records),
        "numeric_baseline_count": sum(r.numeric_value is not None for r in records),
        "screening_input_count": sum(r.usable_as_screening_input for r in records),
        "unresolved_or_blocked_count": sum(not r.usable_as_screening_input for r in records),
    }
