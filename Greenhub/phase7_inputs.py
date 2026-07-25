"""Workbook-backed controls and parameter registry for GreenHub Phase 7."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

import pandas as pd

from Greenhub.input_data import INPUT_WORKBOOK_PATH, ensure_input_workbook
from Greenhub.input_schema import (
    DATA_QUALITY_CLASSES,
    MEASUREMENT_STATUSES,
    as_bool,
    optional_float,
    optional_text,
)
from Greenhub.phase3_inputs import _load_control, _matches, _parameter_value
from Greenhub.scenarios import get_nutrient_recovery_scenario

PHASE7_PARAMETERS_SHEET = "Phase7Parameters"


@dataclass(frozen=True)
class Phase7ParameterRecord:
    """One resolved Phase 7 input with provenance and quality metadata."""

    category: str
    name: str
    python_name: str
    value: float | str | bool | None
    unit: str | None
    scenario: str
    month: str
    minimum: float | None
    maximum: float | None
    distribution: str
    required: bool
    measurement_status: str
    source_class: str
    reference: str | None
    comment: str | None
    calculation_method: str | None
    measured_or_assumed: str
    priority: int
    active: bool
    phase_introduced: int
    limitation_id: str | None

    @classmethod
    def from_mapping(cls, row: Mapping[str, Any]) -> "Phase7ParameterRecord":
        record = cls(
            category=optional_text(row.get("category")) or "uncategorized",
            name=optional_text(row.get("name")) or optional_text(row.get("python_name")) or "",
            python_name=optional_text(row.get("python_name")) or "",
            value=_parameter_value(row.get("value")),
            unit=optional_text(row.get("unit")),
            scenario=optional_text(row.get("scenario")) or "All",
            month=optional_text(row.get("month")) or "All",
            minimum=optional_float(row.get("minimum")),
            maximum=optional_float(row.get("maximum")),
            distribution=optional_text(row.get("distribution")) or "none",
            required=as_bool(row.get("required"), False),
            measurement_status=optional_text(row.get("measurement_status")) or "not_measured",
            source_class=(optional_text(row.get("source_class")) or "E").upper(),
            reference=optional_text(row.get("reference")),
            comment=optional_text(row.get("comment")),
            calculation_method=optional_text(row.get("calculation_method")),
            measured_or_assumed=optional_text(row.get("measured_or_assumed")) or "assumed",
            priority=int(optional_float(row.get("priority")) or 100),
            active=as_bool(row.get("active"), True),
            phase_introduced=int(optional_float(row.get("phase_introduced")) or 7),
            limitation_id=optional_text(row.get("limitation_id")),
        )
        record.validate()
        return record

    def validate(self) -> None:
        if not self.python_name:
            raise ValueError("Phase 7 parameter rows require python_name.")
        if self.measurement_status not in MEASUREMENT_STATUSES:
            raise ValueError(
                f"Phase 7 parameter '{self.python_name}' has invalid measurement "
                f"status '{self.measurement_status}'."
            )
        if self.source_class not in DATA_QUALITY_CLASSES:
            raise ValueError(
                f"Phase 7 parameter '{self.python_name}' has invalid source class "
                f"'{self.source_class}'."
            )
        if isinstance(self.value, float):
            if self.minimum is not None and self.value < self.minimum:
                raise ValueError(
                    f"Phase 7 parameter '{self.python_name}' is below minimum {self.minimum}."
                )
            if self.maximum is not None and self.value > self.maximum:
                raise ValueError(
                    f"Phase 7 parameter '{self.python_name}' exceeds maximum {self.maximum}."
                )

    def as_dict(self) -> dict[str, object]:
        return dict(self.__dict__)


@dataclass(frozen=True)
class Phase7InputBundle:
    """Resolved Phase 7 and upstream controls for one isolated build."""

    scenario_id: str
    phase6_scenario_id: str
    phase5_scenario_id: str
    phase4_scenario_id: str
    phase3_scenario_id: str
    selected_month: str
    process_order: str
    structural_test_mode: bool
    input_basis: str
    parameter_values: dict[str, float | str | bool]
    parameter_records: tuple[Phase7ParameterRecord, ...]
    warnings: tuple[str, ...]


def _resolve_parameter_records(
    table: pd.DataFrame,
    *,
    scenario_id: str,
    selected_month: str,
) -> tuple[Phase7ParameterRecord, ...]:
    candidates: dict[str, list[tuple[int, Phase7ParameterRecord]]] = {}
    for _, row in table.iterrows():
        record = Phase7ParameterRecord.from_mapping(row)
        if not record.active:
            continue
        if not _matches(record.scenario, scenario_id) or not _matches(
            record.month,
            selected_month,
        ):
            continue
        score = 0
        if record.scenario.casefold() == scenario_id.casefold():
            score += 2
        if record.month.casefold() == selected_month.casefold():
            score += 1
        candidates.setdefault(record.python_name, []).append((score, record))
    selected = [
        sorted(records, key=lambda item: (-item[0], item[1].priority))[0][1]
        for records in candidates.values()
    ]
    return tuple(sorted(selected, key=lambda item: (item.category, item.python_name)))


def load_phase7_parameters(
    path: Path = INPUT_WORKBOOK_PATH,
    *,
    scenario_id: str,
    selected_month: str,
    structural_test_mode: bool,
) -> tuple[
    dict[str, float | str | bool],
    tuple[Phase7ParameterRecord, ...],
    tuple[str, ...],
]:
    """Resolve scenario/month values without coercing blank cells to zero."""

    workbook = ensure_input_workbook(path)
    try:
        table = pd.read_excel(workbook, sheet_name=PHASE7_PARAMETERS_SHEET)
    except ValueError as error:
        raise ValueError(
            f"Master workbook is missing required sheet '{PHASE7_PARAMETERS_SHEET}'."
        ) from error
    records = _resolve_parameter_records(
        table,
        scenario_id=scenario_id,
        selected_month=selected_month,
    )
    missing = sorted(
        record.python_name
        for record in records
        if record.required and record.value is None
    )
    warnings: list[str] = []
    if missing and not structural_test_mode:
        raise ValueError(f"Missing required Phase 7 parameters: {missing}")
    if missing:
        warnings.append(
            "Structural-test mode retained missing required Phase 7 inputs; "
            f"affected factories may remain data-gated: {missing}."
        )
    if not structural_test_mode:
        placeholders = sorted(
            record.python_name
            for record in records
            if record.required and record.value is not None and record.source_class == "E"
        )
        if placeholders:
            raise ValueError(
                "Phase 7 structural-test mode is disabled, but required "
                f"quality-class E values remain: {placeholders}."
            )
    values = {
        record.python_name: record.value
        for record in records
        if record.value is not None
    }
    placeholder_count = sum(
        record.value is not None and record.source_class == "E"
        for record in records
    )
    if placeholder_count:
        warnings.append(
            f"{placeholder_count} selected Phase 7 parameters use quality class E; "
            "replace them before design, fertilizer-quality, economic, or configuration-selection interpretation."
        )
    return values, records, tuple(warnings)


def load_phase7_inputs(
    path: Path = INPUT_WORKBOOK_PATH,
    *,
    scenario_id: str | None = None,
    phase6_scenario_id: str | None = None,
    phase5_scenario_id: str | None = None,
    phase4_scenario_id: str | None = None,
    phase3_scenario_id: str | None = None,
    selected_month: str | None = None,
    process_order: str | None = None,
) -> Phase7InputBundle:
    """Load selected NR0-NR7 controls and their actual upstream scenario chain."""

    workbook = ensure_input_workbook(path)
    control = _load_control(workbook)
    scenario_id = (
        scenario_id
        or optional_text(control.get("selected_phase7_scenario"))
        or "NR4"
    ).upper()
    scenario = get_nutrient_recovery_scenario(scenario_id)
    phase6 = (
        phase6_scenario_id
        or optional_text(control.get("selected_phase6_scenario"))
        or "BG2"
    ).upper()
    phase5 = (
        phase5_scenario_id
        or optional_text(control.get("selected_phase5_scenario"))
        or "AD1"
    ).upper()
    phase4 = (
        phase4_scenario_id
        or optional_text(control.get("selected_phase4_scenario"))
        or "PR3"
    ).upper()
    phase3 = (
        phase3_scenario_id
        or optional_text(control.get("selected_phase3_scenario"))
        or "F2"
    ).upper()
    if phase6 not in {f"BG{i}" for i in range(7)}:
        raise ValueError("Phase 7 upstream biogas scenario must be BG0-BG6.")
    if phase5 not in {f"AD{i}" for i in range(6)}:
        raise ValueError("Phase 7 upstream digestion scenario must be AD0-AD5.")
    if phase4 not in {f"PR{i}" for i in range(7)}:
        raise ValueError("Phase 7 upstream protein scenario must be PR0-PR6.")
    if phase3 not in {"F0", "F1", "F2", "F3"}:
        raise ValueError("Phase 7 upstream front-end scenario must be F0-F3.")
    month = selected_month or optional_text(control.get("selected_month")) or "July"
    structural = as_bool(
        control.get("phase7_structural_test_mode"),
        as_bool(control.get("structural_test_mode"), False),
    )
    values, records, warnings = load_phase7_parameters(
        workbook,
        scenario_id=scenario_id,
        selected_month=month,
        structural_test_mode=structural,
    )
    selected_order = (
        process_order
        or optional_text(control.get("selected_phase7_process_order"))
        or optional_text(values.get("phase7_process_order"))
        or scenario.default_order
    ).upper()
    if selected_order not in {"A", "B", "C", "D"}:
        raise ValueError("Phase 7 process order must be A, B, C, or D.")
    if scenario_id in {"NR0", "NR1"}:
        selected_order = "D"
    input_basis = (
        optional_text(control.get("phase7_input_basis"))
        or ("structural_test" if structural else "project_data")
    )
    return Phase7InputBundle(
        scenario_id,
        phase6,
        phase5,
        phase4,
        phase3,
        month,
        selected_order,
        structural,
        input_basis,
        values,
        records,
        warnings,
    )
