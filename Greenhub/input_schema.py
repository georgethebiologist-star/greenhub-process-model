"""Input schemas and data-quality conventions for Phase 2."""

from __future__ import annotations

from dataclasses import dataclass
from math import isfinite
from typing import Any, Mapping

DATA_QUALITY_CLASSES = {
    "A": "Project measurement",
    "B": "Supplier or industry data",
    "C": "Peer-reviewed literature",
    "D": "Engineering estimate",
    "E": "Placeholder or unknown",
}

MEASUREMENT_STATUSES = {
    "measured",
    "assumed",
    "estimated",
    "calculated",
    "not_measured",
    "below_detection_limit",
    "assumed_absent",
    "intentionally_excluded",
}

DATA_TYPES = {"component", "aggregate", "physical", "flow", "parameter"}
SUPPORTED_DISTRIBUTIONS = {"none", "uniform", "triangular", "normal", "lognormal"}


def optional_float(value: Any) -> float | None:
    """Return a finite float or None for a blank/NaN spreadsheet value."""

    if value is None or value == "":
        return None
    try:
        number = float(value)
    except (TypeError, ValueError) as error:
        raise ValueError(f"Expected a numeric value or blank, received {value!r}.") from error
    return number if isfinite(number) else None


def optional_text(value: Any) -> str | None:
    """Return stripped text or None for a blank/NaN spreadsheet value."""

    if value is None:
        return None
    text = str(value).strip()
    return None if not text or text.casefold() == "nan" else text


def as_bool(value: Any, default: bool = False) -> bool:
    """Parse common spreadsheet boolean values."""

    if value is None or (isinstance(value, float) and not isfinite(value)):
        return default
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return bool(value)
    text = str(value).strip().casefold()
    if text in {"true", "yes", "y", "1"}:
        return True
    if text in {"false", "no", "n", "0", ""}:
        return False
    raise ValueError(f"Cannot parse boolean value {value!r}.")


@dataclass(frozen=True)
class InputRecord:
    """One measured, assumed, calculated, or missing project input."""

    name: str
    python_name: str
    value: float | None
    unit: str | None
    basis: str | None
    stream: str
    sample_id: str
    scenario: str
    month: str | None
    minimum: float | None
    maximum: float | None
    distribution: str
    standard_deviation: float | None
    data_type: str
    measurement_status: str
    source_class: str
    reference: str | None
    comment: str | None
    priority: int
    allocation_target: str | None
    active: bool

    @classmethod
    def from_mapping(cls, row: Mapping[str, Any]) -> "InputRecord":
        """Build and validate a record from a spreadsheet or dictionary row."""

        record = cls(
            name=optional_text(row.get("name")) or "",
            python_name=optional_text(row.get("python_name")) or "",
            value=optional_float(row.get("value")),
            unit=optional_text(row.get("unit")),
            basis=optional_text(row.get("basis")),
            stream=optional_text(row.get("stream")) or "raw_liquid_fraction",
            sample_id=optional_text(row.get("sample_id")) or "baseline",
            scenario=optional_text(row.get("scenario")) or "baseline",
            month=optional_text(row.get("month")),
            minimum=optional_float(row.get("minimum")),
            maximum=optional_float(row.get("maximum")),
            distribution=(optional_text(row.get("distribution")) or "none").casefold(),
            standard_deviation=optional_float(row.get("standard_deviation")),
            data_type=(optional_text(row.get("data_type")) or "component").casefold(),
            measurement_status=(optional_text(row.get("measurement_status")) or "not_measured").casefold(),
            source_class=(optional_text(row.get("source_class")) or "E").upper(),
            reference=optional_text(row.get("reference")),
            comment=optional_text(row.get("comment")),
            priority=int(optional_float(row.get("priority")) or 100),
            allocation_target=optional_text(row.get("allocation_target")),
            active=as_bool(row.get("active"), True),
        )
        record.validate()
        return record

    def validate(self) -> None:
        """Validate field combinations while preserving legitimate missing data."""

        if not self.name or not self.python_name:
            raise ValueError("Every input record requires both 'name' and 'python_name'.")
        if self.data_type not in DATA_TYPES:
            raise ValueError(f"Invalid data_type '{self.data_type}' for '{self.python_name}'.")
        if self.measurement_status not in MEASUREMENT_STATUSES:
            raise ValueError(f"Invalid measurement_status '{self.measurement_status}'.")
        if self.source_class not in DATA_QUALITY_CLASSES:
            raise ValueError(f"Invalid source_class '{self.source_class}'.")
        if self.distribution not in SUPPORTED_DISTRIBUTIONS:
            raise ValueError(f"Invalid distribution '{self.distribution}'.")
        if self.value is not None and self.value < 0.0 and self.python_name != "temperature":
            raise ValueError(f"Input '{self.python_name}' cannot be negative.")
        if self.minimum is not None and self.maximum is not None and self.minimum > self.maximum:
            raise ValueError(f"Input '{self.python_name}' has minimum greater than maximum.")
        if self.value is not None and self.minimum is not None and self.value < self.minimum:
            raise ValueError(f"Input '{self.python_name}' is below its declared minimum.")
        if self.value is not None and self.maximum is not None and self.value > self.maximum:
            raise ValueError(f"Input '{self.python_name}' is above its declared maximum.")
        if self.value is not None and not self.unit:
            raise ValueError(f"Input '{self.python_name}' has a value but no unit.")
        if self.data_type == "component" and self.active and not self.allocation_target:
            raise ValueError(f"Active component input '{self.python_name}' requires an allocation_target.")


@dataclass(frozen=True)
class ParameterDefinition:
    """Central registry entry for a current or future model parameter."""

    category: str
    name: str
    python_name: str
    value: float | None
    unit: str
    minimum: float | None
    maximum: float | None
    distribution: str
    required: bool
    source: str
    comment: str
    phase_introduced: int
    active: bool
