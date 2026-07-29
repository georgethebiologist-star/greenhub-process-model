"""Strict JSON and CSV serialization without NaN, infinity, or domain objects."""

from __future__ import annotations

import csv
import json
from dataclasses import fields, is_dataclass
from datetime import date, datetime
from enum import Enum
from math import isfinite
from pathlib import Path
from typing import Any, Iterable, Mapping


def to_json_compatible(value: Any) -> Any:
    if value is None or isinstance(value, (str, bool, int)):
        return value
    if isinstance(value, float):
        if not isfinite(value):
            raise ValueError("NaN and infinity are not valid GreenHub API values.")
        return value
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, (date, datetime)):
        return value.isoformat()
    if isinstance(value, Path):
        return value.as_posix()
    if is_dataclass(value):
        return {
            item.name: to_json_compatible(getattr(value, item.name))
            for item in fields(value)
        }
    if isinstance(value, Mapping):
        return {str(key): to_json_compatible(item) for key, item in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [to_json_compatible(item) for item in value]
    item_method = getattr(value, "item", None)
    if callable(item_method):
        return to_json_compatible(item_method())
    raise TypeError(f"Unsupported serialized value type: {type(value).__name__}.")


def dumps(value: Any, *, indent: int = 2) -> str:
    return json.dumps(to_json_compatible(value), indent=indent, sort_keys=True, allow_nan=False)


def write_json(path: Path, value: Any) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(dumps(value) + "\n", encoding="utf-8")
    return path


def write_records_csv(path: Path, records: Iterable[Mapping[str, Any]]) -> Path:
    rows = [to_json_compatible(record) for record in records]
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        path.write_text("", encoding="utf-8")
        return path
    headers = list(rows[0])
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=headers)
        writer.writeheader()
        for row in rows:
            writer.writerow(
                {
                    key: json.dumps(value, sort_keys=True) if isinstance(value, (list, dict)) else value
                    for key, value in row.items()
                }
            )
    return path
