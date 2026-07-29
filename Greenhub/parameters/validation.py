"""Validation rules for canonical parameters and overrides."""

from __future__ import annotations

from .models import CanonicalParameter, JSONScalar
from .units import convert_value


def validate_value(parameter: CanonicalParameter, value: JSONScalar, unit: str | None) -> JSONScalar:
    """Return a normalized, validated value or raise an informative error."""

    if value is None:
        raise ValueError(f"'{parameter.parameter_id}' cannot be overridden with null.")
    if parameter.data_type == "boolean":
        if not isinstance(value, bool):
            raise TypeError(f"'{parameter.parameter_id}' requires a boolean value.")
        normalized: JSONScalar = value
    elif parameter.data_type in {"string", "categorical"}:
        if not isinstance(value, str):
            raise TypeError(f"'{parameter.parameter_id}' requires a string value.")
        normalized = value
    else:
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise TypeError(f"'{parameter.parameter_id}' requires a numerical value.")
        normalized = convert_value(float(value), unit or parameter.normalized_unit, parameter.normalized_unit)
        if parameter.physical_lower_bound is not None and normalized < parameter.physical_lower_bound:
            raise ValueError(
                f"'{parameter.parameter_id}' is below its lower bound {parameter.physical_lower_bound}."
            )
        if parameter.physical_upper_bound is not None and normalized > parameter.physical_upper_bound:
            raise ValueError(
                f"'{parameter.parameter_id}' exceeds its upper bound {parameter.physical_upper_bound}."
            )
    if parameter.allowed_options and normalized not in parameter.allowed_options:
        raise ValueError(
            f"'{parameter.parameter_id}' must be one of {parameter.allowed_options}; received {normalized!r}."
        )
    return normalized
