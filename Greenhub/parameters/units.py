"""Small explicit unit-conversion contract for parameter overrides."""

from __future__ import annotations

from math import isfinite


_LINEAR_CONVERSIONS: dict[tuple[str, str], tuple[float, float]] = {
    ("%", "fraction"): (0.01, 0.0),
    ("vol %", "fraction"): (0.01, 0.0),
    ("fraction", "%"): (100.0, 0.0),
    ("fraction", "vol %"): (100.0, 0.0),
    ("min", "s"): (60.0, 0.0),
    ("s", "min"): (1.0 / 60.0, 0.0),
    ("hr", "s"): (3600.0, 0.0),
    ("s", "hr"): (1.0 / 3600.0, 0.0),
    ("day", "s"): (86400.0, 0.0),
    ("s", "day"): (1.0 / 86400.0, 0.0),
    ("degc", "k"): (1.0, 273.15),
    ("k", "degc"): (1.0, -273.15),
    ("l ch4/kg vs", "m3 ch4/kg vs"): (0.001, 0.0),
    ("ml ch4/g vs", "m3 ch4/kg vs"): (0.001, 0.0),
}


def normalize_unit(unit: str | None) -> str | None:
    if unit is None:
        return None
    text = " ".join(str(unit).strip().split())
    return text or None


def convert_value(value: float, from_unit: str | None, to_unit: str | None) -> float:
    """Convert only an explicitly supported pair; never infer dimensions."""

    numeric = float(value)
    if not isfinite(numeric):
        raise ValueError("Override values must be finite.")
    source = normalize_unit(from_unit)
    target = normalize_unit(to_unit)
    if source == target or source is None and target is None:
        return numeric
    if source is None or target is None:
        raise ValueError(f"Cannot convert between unitless and unit-bearing values: {source!r} -> {target!r}.")
    key = (source.casefold(), target.casefold())
    try:
        factor, offset = _LINEAR_CONVERSIONS[key]
    except KeyError as error:
        raise ValueError(f"Unsupported unit conversion: '{source}' -> '{target}'.") from error
    return numeric * factor + offset
