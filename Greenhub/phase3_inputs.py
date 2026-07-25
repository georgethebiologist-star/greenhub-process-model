"""Workbook-backed scenario, grass-feed, and parameter inputs for Phase 3."""

from __future__ import annotations

from dataclasses import dataclass
from math import isfinite
from pathlib import Path
from typing import Any, Mapping

import pandas as pd

from Greenhub.input_data import (
    CONTROL_SHEET,
    INPUT_WORKBOOK_PATH,
    FeedSpecification,
    ensure_input_workbook,
    load_feed_specification,
)
from Greenhub.input_schema import (
    DATA_QUALITY_CLASSES,
    MEASUREMENT_STATUSES,
    InputRecord,
    as_bool,
    optional_float,
    optional_text,
)

GRASS_AVAILABILITY_SHEET = "GrassAvailability"
GRASS_MEASUREMENTS_SHEET = "GrassMeasurements"
PHASE3_PARAMETERS_SHEET = "Phase3Parameters"


def _parameter_value(value: Any) -> float | str | bool | None:
    if value is None or (isinstance(value, float) and not isfinite(value)):
        return None
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return float(value)
    text = str(value).strip()
    if not text or text.casefold() == "nan":
        return None
    if text.casefold() in {"true", "yes"}:
        return True
    if text.casefold() in {"false", "no"}:
        return False
    try:
        return float(text)
    except ValueError:
        return text


@dataclass(frozen=True)
class Phase3ParameterRecord:
    """One selected unit or scenario parameter with provenance."""

    category: str
    python_name: str
    value: float | str | bool | None
    unit: str | None
    scenario: str
    month: str | None
    minimum: float | None
    maximum: float | None
    required: bool
    measurement_status: str
    source_class: str
    reference: str | None
    comment: str | None
    calculation_method: str | None
    priority: int
    active: bool

    @classmethod
    def from_mapping(cls, row: Mapping[str, Any]) -> "Phase3ParameterRecord":
        record = cls(
            category=optional_text(row.get("category")) or "uncategorized",
            python_name=optional_text(row.get("python_name")) or "",
            value=_parameter_value(row.get("value")),
            unit=optional_text(row.get("unit")),
            scenario=optional_text(row.get("scenario")) or "All",
            month=optional_text(row.get("month")) or "All",
            minimum=optional_float(row.get("minimum")),
            maximum=optional_float(row.get("maximum")),
            required=as_bool(row.get("required"), False),
            measurement_status=optional_text(row.get("measurement_status")) or "not_measured",
            source_class=(optional_text(row.get("source_class")) or "E").upper(),
            reference=optional_text(row.get("reference")),
            comment=optional_text(row.get("comment")),
            calculation_method=optional_text(row.get("calculation_method")),
            priority=int(optional_float(row.get("priority")) or 100),
            active=as_bool(row.get("active"), True),
        )
        record.validate()
        return record

    def validate(self) -> None:
        if not self.python_name:
            raise ValueError("Phase 3 parameter rows require python_name.")
        if self.measurement_status not in MEASUREMENT_STATUSES:
            raise ValueError(
                f"Parameter '{self.python_name}' has invalid status '{self.measurement_status}'."
            )
        if self.source_class not in DATA_QUALITY_CLASSES:
            raise ValueError(
                f"Parameter '{self.python_name}' has invalid source class '{self.source_class}'."
            )
        if isinstance(self.value, float):
            if self.minimum is not None and self.value < self.minimum:
                raise ValueError(
                    f"Parameter '{self.python_name}' is below its minimum {self.minimum}."
                )
            if self.maximum is not None and self.value > self.maximum:
                raise ValueError(
                    f"Parameter '{self.python_name}' exceeds its maximum {self.maximum}."
                )

    def as_dict(self) -> dict[str, object]:
        return dict(self.__dict__)


@dataclass(frozen=True)
class Phase3InputBundle:
    """Resolved workbook inputs for one isolated front-end scenario."""

    scenario_id: str
    selected_month: str
    grass_sample_id: str
    structural_test_mode: bool
    feed_specification: FeedSpecification
    parameter_values: dict[str, float | str | bool]
    parameter_records: tuple[Phase3ParameterRecord, ...]
    warnings: tuple[str, ...]


def _load_control(path: Path) -> dict[str, object]:
    table = pd.read_excel(path, sheet_name=CONTROL_SHEET)
    if not {"parameter", "value"} <= set(table.columns):
        raise ValueError(f"'{CONTROL_SHEET}' must include parameter and value columns.")
    return {
        str(row["parameter"]).strip(): row["value"]
        for _, row in table.iterrows()
        if optional_text(row.get("parameter"))
    }


def _matches(value: object, selected: str) -> bool:
    text = optional_text(value) or "All"
    return text.casefold() in {"all", "annual", selected.casefold()}


def load_roadside_grass_specification(
    path: Path = INPUT_WORKBOOK_PATH,
    *,
    scenario_id: str,
    selected_month: str | None = None,
    sample_id: str | None = None,
) -> FeedSpecification:
    """Create a seasonal incoming-grass specification without liquid-feed reuse."""

    path = ensure_input_workbook(path)
    control = _load_control(path)
    month = selected_month or optional_text(control.get("selected_month")) or "July"
    sample = sample_id or optional_text(control.get("selected_grass_sample_id")) or "grass_baseline"
    availability = pd.read_excel(path, sheet_name=GRASS_AVAILABILITY_SHEET)
    measurements = pd.read_excel(path, sheet_name=GRASS_MEASUREMENTS_SHEET)

    candidates = availability[
        availability["sample_id"].astype(str).str.casefold().eq(sample.casefold())
        & availability["month"].astype(str).str.casefold().eq(month.casefold())
        & availability["scenario"].map(lambda value: _matches(value, scenario_id))
    ].copy()
    if candidates.empty:
        raise ValueError(
            f"No grass availability matches sample='{sample}', scenario='{scenario_id}', month='{month}'."
        )
    candidates["_specific"] = candidates["scenario"].astype(str).str.casefold().eq(
        scenario_id.casefold()
    )
    row = candidates.sort_values("_specific", ascending=False).iloc[0]
    monthly_mass = optional_float(row.get("total_wet_grass_mass_kg"))
    operating_days = optional_float(row.get("operating_days"))
    if monthly_mass is None or monthly_mass <= 0.0:
        raise ValueError("Selected monthly wet-grass mass must be greater than zero.")
    if operating_days is None or operating_days <= 0.0:
        raise ValueError("Selected grass operating days must be greater than zero.")

    records: list[InputRecord] = []
    selected_rows = measurements[
        measurements["sample_id"].astype(str).str.casefold().eq(sample.casefold())
        & measurements["scenario"].map(lambda value: _matches(value, scenario_id))
        & measurements["month"].map(lambda value: _matches(value, month))
    ]
    for _, measurement in selected_rows.iterrows():
        record = InputRecord.from_mapping(measurement)
        if record.active:
            records.append(record)
    if not records:
        raise ValueError("The selected roadside-grass dataset has no active measurements.")

    return FeedSpecification(
        selected_month=month,
        sample_id=sample,
        scenario=scenario_id,
        entry_mode="roadside_grass",
        monthly_total_mass_kg=monthly_mass,
        operating_days=operating_days,
        total_mass_flow_kg_hr=monthly_mass / (operating_days * 24.0),
        records=tuple(records),
        control=control,
        monthly_table=availability,
        measurements_table=measurements,
    )


def load_phase3_parameters(
    path: Path = INPUT_WORKBOOK_PATH,
    *,
    scenario_id: str,
    selected_month: str,
    structural_test_mode: bool,
) -> tuple[dict[str, float | str | bool], tuple[Phase3ParameterRecord, ...], tuple[str, ...]]:
    """Resolve scenario/month overrides with explicit provenance and bounds."""

    table = pd.read_excel(ensure_input_workbook(path), sheet_name=PHASE3_PARAMETERS_SHEET)
    candidates: dict[str, list[tuple[int, Phase3ParameterRecord]]] = {}
    for _, row in table.iterrows():
        record = Phase3ParameterRecord.from_mapping(row)
        if not record.active:
            continue
        if not _matches(record.scenario, scenario_id) or not _matches(record.month, selected_month):
            continue
        score = 0
        if record.scenario.casefold() == scenario_id.casefold():
            score += 2
        if (record.month or "All").casefold() == selected_month.casefold():
            score += 1
        candidates.setdefault(record.python_name, []).append((score, record))

    selected: list[Phase3ParameterRecord] = []
    for records in candidates.values():
        selected.append(sorted(records, key=lambda item: (-item[0], item[1].priority))[0][1])
    missing = sorted(record.python_name for record in selected if record.required and record.value is None)
    if missing:
        raise ValueError(f"Missing required Phase 3 parameters: {missing}")
    if not structural_test_mode:
        placeholders = sorted(
            record.python_name
            for record in selected
            if record.required and record.source_class == "E"
        )
        if placeholders:
            raise ValueError(
                "Structural-test mode is disabled, but required quality-class E values remain: "
                f"{placeholders}."
            )
    values = {
        record.python_name: record.value
        for record in selected
        if record.value is not None
    }
    placeholder_count = sum(
        record.value is not None and record.source_class == "E"
        for record in selected
    )
    warnings = (
        (
            f"{placeholder_count} selected Phase 3 parameters use quality class E; "
            "see the assumption register for individual records."
        ),
    ) if placeholder_count else ()
    return values, tuple(sorted(selected, key=lambda item: (item.category, item.python_name))), warnings


def load_phase3_inputs(
    path: Path = INPUT_WORKBOOK_PATH,
    *,
    scenario_id: str | None = None,
    selected_month: str | None = None,
) -> Phase3InputBundle:
    """Load the selected F0-F3 scenario and its standardized feed inputs."""

    path = ensure_input_workbook(path)
    control = _load_control(path)
    scenario = scenario_id or optional_text(control.get("selected_phase3_scenario")) or "F0"
    scenario = scenario.upper()
    if scenario not in {"F0", "F1", "F2", "F3"}:
        raise ValueError("selected_phase3_scenario must be one of F0, F1, F2, or F3.")
    month = selected_month or optional_text(control.get("selected_month")) or "July"
    grass_sample = optional_text(control.get("selected_grass_sample_id")) or "grass_baseline"
    structural = as_bool(control.get("structural_test_mode"), False)
    if scenario == "F0":
        feed = load_feed_specification(path, selected_month=month)
    else:
        feed = load_roadside_grass_specification(
            path,
            scenario_id=scenario,
            selected_month=month,
            sample_id=grass_sample,
        )
    values, records, warnings = load_phase3_parameters(
        path,
        scenario_id=scenario,
        selected_month=month,
        structural_test_mode=structural,
    )
    return Phase3InputBundle(
        scenario,
        month,
        grass_sample,
        structural,
        feed,
        values,
        records,
        warnings,
    )
