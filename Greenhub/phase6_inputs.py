"""Workbook-backed controls and parameter registry for GreenHub Phase 6."""

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

PHASE6_PARAMETERS_SHEET = "Phase6Parameters"


@dataclass(frozen=True)
class Phase6ParameterRecord:
    """One resolved Phase 6 input with provenance and data-quality metadata."""

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
    def from_mapping(cls, row: Mapping[str, Any]) -> "Phase6ParameterRecord":
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
            phase_introduced=int(optional_float(row.get("phase_introduced")) or 6),
            limitation_id=optional_text(row.get("limitation_id")),
        )
        record.validate()
        return record

    def validate(self) -> None:
        if not self.python_name:
            raise ValueError("Phase 6 parameter rows require python_name.")
        if self.measurement_status not in MEASUREMENT_STATUSES:
            raise ValueError(
                f"Phase 6 parameter '{self.python_name}' has invalid measurement "
                f"status '{self.measurement_status}'."
            )
        if self.source_class not in DATA_QUALITY_CLASSES:
            raise ValueError(
                f"Phase 6 parameter '{self.python_name}' has invalid source class "
                f"'{self.source_class}'."
            )
        if isinstance(self.value, float):
            if self.minimum is not None and self.value < self.minimum:
                raise ValueError(
                    f"Phase 6 parameter '{self.python_name}' is below minimum "
                    f"{self.minimum}."
                )
            if self.maximum is not None and self.value > self.maximum:
                raise ValueError(
                    f"Phase 6 parameter '{self.python_name}' exceeds maximum "
                    f"{self.maximum}."
                )

    def as_dict(self) -> dict[str, object]:
        return dict(self.__dict__)


@dataclass(frozen=True)
class Phase6InputBundle:
    """Resolved Phase 6 controls for one isolated scenario build."""

    scenario_id: str
    phase5_scenario_id: str
    phase4_scenario_id: str
    phase3_scenario_id: str
    selected_month: str
    structural_test_mode: bool
    input_basis: str
    parameter_values: dict[str, float | str | bool]
    parameter_records: tuple[Phase6ParameterRecord, ...]
    warnings: tuple[str, ...]


def _resolve_parameter_records(
    table: pd.DataFrame,
    *,
    scenario_id: str,
    selected_month: str,
) -> tuple[Phase6ParameterRecord, ...]:
    candidates: dict[str, list[tuple[int, Phase6ParameterRecord]]] = {}
    for _, row in table.iterrows():
        record = Phase6ParameterRecord.from_mapping(row)
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


def load_phase6_parameters(
    path: Path = INPUT_WORKBOOK_PATH,
    *,
    scenario_id: str,
    selected_month: str,
    structural_test_mode: bool,
) -> tuple[
    dict[str, float | str | bool],
    tuple[Phase6ParameterRecord, ...],
    tuple[str, ...],
]:
    """Resolve scenario/month values and enforce Phase 6 data gates."""

    workbook = ensure_input_workbook(path)
    try:
        table = pd.read_excel(workbook, sheet_name=PHASE6_PARAMETERS_SHEET)
    except ValueError as error:
        raise ValueError(
            f"Master workbook is missing required sheet '{PHASE6_PARAMETERS_SHEET}'."
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
    if missing:
        raise ValueError(f"Missing required Phase 6 parameters: {missing}")
    if not structural_test_mode:
        placeholders = sorted(
            record.python_name
            for record in records
            if record.required
            and record.value is not None
            and record.source_class == "E"
        )
        if placeholders:
            raise ValueError(
                "Phase 6 structural-test mode is disabled, but required "
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
    warnings = (
        (
            f"{placeholder_count} selected Phase 6 parameters use quality class E; "
            "replace them before scientific, design, economic, or configuration-selection interpretation."
        ),
    ) if placeholder_count else ()
    return values, records, warnings


def load_phase6_inputs(
    path: Path = INPUT_WORKBOOK_PATH,
    *,
    scenario_id: str | None = None,
    phase5_scenario_id: str | None = None,
    phase4_scenario_id: str | None = None,
    phase3_scenario_id: str | None = None,
    selected_month: str | None = None,
) -> Phase6InputBundle:
    """Load selected BG0-BG6 controls from the master workbook."""

    workbook = ensure_input_workbook(path)
    control = _load_control(workbook)
    scenario = (
        scenario_id
        or optional_text(control.get("selected_phase6_scenario"))
        or "BG2"
    ).upper()
    if scenario not in {f"BG{i}" for i in range(7)}:
        raise ValueError("selected_phase6_scenario must be BG0 through BG6.")
    phase5 = (
        phase5_scenario_id
        or optional_text(control.get("selected_phase5_scenario"))
        or "AD1"
    ).upper()
    if phase5 not in {f"AD{i}" for i in range(6)}:
        raise ValueError("Phase 6 upstream digestion scenario must be AD0-AD5.")
    phase4 = (
        phase4_scenario_id
        or optional_text(control.get("selected_phase4_scenario"))
        or "PR3"
    ).upper()
    if phase4 not in {f"PR{i}" for i in range(7)}:
        raise ValueError("Phase 6 upstream protein scenario must be PR0-PR6.")
    phase3 = (
        phase3_scenario_id
        or optional_text(control.get("selected_phase3_scenario"))
        or "F2"
    ).upper()
    if phase3 not in {"F0", "F1", "F2", "F3"}:
        raise ValueError("Phase 6 upstream front-end scenario must be F0-F3.")
    month = selected_month or optional_text(control.get("selected_month")) or "July"
    structural = as_bool(
        control.get("phase6_structural_test_mode"),
        as_bool(control.get("structural_test_mode"), False),
    )
    input_basis = (
        optional_text(control.get("phase6_input_basis"))
        or ("structural_test" if structural else "project_data")
    )
    values, records, warnings = load_phase6_parameters(
        workbook,
        scenario_id=scenario,
        selected_month=month,
        structural_test_mode=structural,
    )
    return Phase6InputBundle(
        scenario,
        phase5,
        phase4,
        phase3,
        month,
        structural,
        input_basis,
        values,
        records,
        warnings,
    )
