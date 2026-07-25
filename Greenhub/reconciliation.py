"""Measured-versus-calculated reconciliation without mass double counting."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

from Greenhub.input_schema import InputRecord

INDICATOR_MAP = {
    "total_soluble_sugars": "soluble_sugars_g_L",
    "total_protein": "total_protein_g_L",
    "total_vfas": "vfa_g_L",
    "total_solids": "ts_g_L",
    "volatile_solids": "vs_g_L",
    "total_suspended_solids": "tss_mg_L",
    "total_dissolved_solids": "tds_mg_L",
    "cod": "cod_mg_L",
    "soluble_cod": "soluble_cod_mg_L",
    "particulate_cod": "particulate_cod_mg_L",
    "toc": "toc_mg_L",
    "total_nitrogen": "total_nitrogen_mg_L",
    "tkn": "tkn_mg_L",
    "total_phosphorus": "total_phosphorus_mg_L",
}


@dataclass(frozen=True)
class ReconciliationRow:
    measurement: str
    measured_value: float | None
    measured_unit: str | None
    calculated_value: float | None
    calculated_indicator: str | None
    absolute_difference: float | None
    relative_difference: float | None
    status: str
    warning: str | None

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


def reconcile_measurements(
    records: tuple[InputRecord, ...],
    indicators: dict[str, float | None],
    *,
    warning_threshold: float = 0.20,
    failure_threshold: float = 0.50,
) -> tuple[ReconciliationRow, ...]:
    """Compare aggregate observations with component-derived indicators."""

    rows: list[ReconciliationRow] = []
    for record in records:
        if record.data_type != "aggregate":
            continue
        indicator_name = INDICATOR_MAP.get(record.python_name)
        calculated = indicators.get(indicator_name) if indicator_name else None
        if record.value is None:
            rows.append(ReconciliationRow(record.python_name, None, record.unit, calculated, indicator_name, None, None, "not_measured", None))
            continue
        if calculated is None or indicator_name is None:
            rows.append(ReconciliationRow(record.python_name, record.value, record.unit, calculated, indicator_name, None, None, "not_comparable", "No compatible calculated indicator is available."))
            continue
        absolute = calculated - record.value
        relative = abs(absolute) / max(abs(record.value), 1e-12)
        status = "pass" if relative <= warning_threshold else "warning"
        warning = None
        if relative > failure_threshold:
            status = "large_gap"
            warning = "Measured and calculated values differ by more than the configured failure threshold."
        elif relative > warning_threshold:
            warning = "Measured and calculated values differ by more than the configured warning threshold."
        rows.append(ReconciliationRow(record.python_name, record.value, record.unit, calculated, indicator_name, absolute, relative, status, warning))
    return tuple(rows)
