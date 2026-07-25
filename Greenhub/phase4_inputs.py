"""Workbook-backed Phase 4 scenario, parameter, and empirical-data inputs."""

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

PHASE4_PARAMETERS_SHEET = "Phase4Parameters"
ACID_TITRATION_SHEET = "AcidTitration"
PROTEIN_RECOVERY_DATA_SHEET = "ProteinRecoveryData"


@dataclass(frozen=True)
class Phase4ParameterRecord:
    """One resolved Phase 4 input with bounds and provenance."""

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

    @classmethod
    def from_mapping(cls, row: Mapping[str, Any]) -> "Phase4ParameterRecord":
        """Create and validate one record from a workbook row."""

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
            phase_introduced=int(optional_float(row.get("phase_introduced")) or 4),
        )
        record.validate()
        return record

    def validate(self) -> None:
        """Validate identifiers, provenance, and numerical bounds."""

        if not self.python_name:
            raise ValueError("Phase 4 parameter rows require python_name.")
        if self.measurement_status not in MEASUREMENT_STATUSES:
            raise ValueError(
                f"Phase 4 parameter '{self.python_name}' has invalid status "
                f"'{self.measurement_status}'."
            )
        if self.source_class not in DATA_QUALITY_CLASSES:
            raise ValueError(
                f"Phase 4 parameter '{self.python_name}' has invalid source class "
                f"'{self.source_class}'."
            )
        if isinstance(self.value, float):
            if self.minimum is not None and self.value < self.minimum:
                raise ValueError(
                    f"Phase 4 parameter '{self.python_name}' is below minimum {self.minimum}."
                )
            if self.maximum is not None and self.value > self.maximum:
                raise ValueError(
                    f"Phase 4 parameter '{self.python_name}' exceeds maximum {self.maximum}."
                )

    def as_dict(self) -> dict[str, object]:
        return dict(self.__dict__)


@dataclass(frozen=True)
class TitrationPointRecord:
    """One measured or placeholder acid-dose/pH point."""

    curve_id: str
    acid_type: str
    sample_id: str
    scenario: str
    month: str
    acid_dose_kg_m3: float
    resulting_pH: float
    measurement_status: str
    source_class: str
    reference: str | None
    comment: str | None

    @classmethod
    def from_mapping(cls, row: Mapping[str, Any]) -> "TitrationPointRecord":
        dose = optional_float(row.get("acid_dose_kg_m3"))
        pH = optional_float(row.get("resulting_pH"))
        if dose is None or pH is None:
            raise ValueError("Active acid-titration rows require dose and resulting_pH.")
        record = cls(
            curve_id=optional_text(row.get("curve_id")) or "",
            acid_type=optional_text(row.get("acid_type")) or "HydrochloricAcid",
            sample_id=optional_text(row.get("sample_id")) or "All",
            scenario=optional_text(row.get("scenario")) or "All",
            month=optional_text(row.get("month")) or "All",
            acid_dose_kg_m3=float(dose),
            resulting_pH=float(pH),
            measurement_status=optional_text(row.get("measurement_status")) or "not_measured",
            source_class=(optional_text(row.get("source_class")) or "E").upper(),
            reference=optional_text(row.get("reference")),
            comment=optional_text(row.get("comment")),
        )
        if not record.curve_id:
            raise ValueError("Active acid-titration rows require curve_id.")
        if record.acid_dose_kg_m3 < 0.0 or not 0.0 <= record.resulting_pH <= 14.0:
            raise ValueError("Acid-titration dose must be non-negative and pH within [0, 14].")
        if record.measurement_status not in MEASUREMENT_STATUSES:
            raise ValueError("Acid-titration row has an invalid measurement status.")
        if record.source_class not in DATA_QUALITY_CLASSES:
            raise ValueError("Acid-titration row has an invalid source class.")
        return record


@dataclass(frozen=True)
class ProteinRecoveryDataPoint:
    """Optional empirical recovery observation at one pH, time, and temperature."""

    dataset_id: str
    scenario: str
    pH: float
    temperature_C: float
    residence_time_min: float
    recovery_fraction: float
    source_class: str
    reference: str | None

    @classmethod
    def from_mapping(cls, row: Mapping[str, Any]) -> "ProteinRecoveryDataPoint":
        values = {
            name: optional_float(row.get(name))
            for name in ("pH", "temperature_C", "residence_time_min", "recovery_fraction")
        }
        if any(value is None for value in values.values()):
            raise ValueError("Active protein-recovery data rows require pH, temperature, time, and recovery.")
        record = cls(
            dataset_id=optional_text(row.get("dataset_id")) or "",
            scenario=optional_text(row.get("scenario")) or "All",
            pH=float(values["pH"]),
            temperature_C=float(values["temperature_C"]),
            residence_time_min=float(values["residence_time_min"]),
            recovery_fraction=float(values["recovery_fraction"]),
            source_class=(optional_text(row.get("source_class")) or "E").upper(),
            reference=optional_text(row.get("reference")),
        )
        if not record.dataset_id:
            raise ValueError("Active protein-recovery data rows require dataset_id.")
        if not 0.0 <= record.pH <= 14.0:
            raise ValueError("Empirical recovery pH must be within [0, 14].")
        if record.residence_time_min < 0.0 or not 0.0 <= record.recovery_fraction <= 1.0:
            raise ValueError("Empirical recovery time and fraction are outside physical bounds.")
        if record.source_class not in DATA_QUALITY_CLASSES:
            raise ValueError("Empirical recovery row has an invalid source class.")
        return record


@dataclass(frozen=True)
class Phase4InputBundle:
    """Resolved Phase 4 controls and scientific inputs for one isolated build."""

    scenario_id: str
    phase3_scenario_id: str
    selected_month: str
    structural_test_mode: bool
    parameter_values: dict[str, float | str | bool]
    parameter_records: tuple[Phase4ParameterRecord, ...]
    titration_points: tuple[TitrationPointRecord, ...]
    recovery_data: tuple[ProteinRecoveryDataPoint, ...]
    warnings: tuple[str, ...]


def _resolve_parameter_records(
    table: pd.DataFrame,
    *,
    scenario_id: str,
    selected_month: str,
) -> tuple[Phase4ParameterRecord, ...]:
    candidates: dict[str, list[tuple[int, Phase4ParameterRecord]]] = {}
    for _, row in table.iterrows():
        record = Phase4ParameterRecord.from_mapping(row)
        if not record.active:
            continue
        if not _matches(record.scenario, scenario_id) or not _matches(record.month, selected_month):
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


def load_phase4_parameters(
    path: Path = INPUT_WORKBOOK_PATH,
    *,
    scenario_id: str,
    selected_month: str,
    structural_test_mode: bool,
) -> tuple[dict[str, float | str | bool], tuple[Phase4ParameterRecord, ...], tuple[str, ...]]:
    """Load scenario/month precedence with missing-data and quality checks."""

    workbook = ensure_input_workbook(path)
    table = pd.read_excel(workbook, sheet_name=PHASE4_PARAMETERS_SHEET)
    records = _resolve_parameter_records(
        table,
        scenario_id=scenario_id,
        selected_month=selected_month,
    )
    missing = sorted(
        record.python_name for record in records if record.required and record.value is None
    )
    if missing:
        raise ValueError(f"Missing required Phase 4 parameters: {missing}")
    if not structural_test_mode:
        placeholders = sorted(
            record.python_name
            for record in records
            if record.required and record.value is not None and record.source_class == "E"
        )
        if placeholders:
            raise ValueError(
                "Phase 4 structural-test mode is disabled, but required quality-class E "
                f"values remain: {placeholders}."
            )
    values = {
        record.python_name: record.value
        for record in records
        if record.value is not None
    }
    placeholder_count = sum(
        record.value is not None and record.source_class == "E" for record in records
    )
    warnings = (
        (
            f"{placeholder_count} selected Phase 4 parameters use quality class E; "
            "replace them before scientific or economic interpretation."
        ),
    ) if placeholder_count else ()
    return values, records, warnings


def _load_titration_points(
    path: Path,
    *,
    curve_id: str | None,
    acid_type: str,
    scenario_id: str,
    selected_month: str,
) -> tuple[TitrationPointRecord, ...]:
    if not curve_id:
        return ()
    table = pd.read_excel(path, sheet_name=ACID_TITRATION_SHEET)
    points = []
    for _, row in table.iterrows():
        if not as_bool(row.get("active"), False):
            continue
        if (optional_text(row.get("curve_id")) or "").casefold() != curve_id.casefold():
            continue
        if (optional_text(row.get("acid_type")) or acid_type).casefold() != acid_type.casefold():
            continue
        if not _matches(row.get("scenario"), scenario_id) or not _matches(row.get("month"), selected_month):
            continue
        points.append(TitrationPointRecord.from_mapping(row))
    return tuple(sorted(points, key=lambda item: item.acid_dose_kg_m3))


def _load_recovery_data(
    path: Path,
    *,
    dataset_id: str | None,
    scenario_id: str,
) -> tuple[ProteinRecoveryDataPoint, ...]:
    if not dataset_id:
        return ()
    table = pd.read_excel(path, sheet_name=PROTEIN_RECOVERY_DATA_SHEET)
    points = []
    for _, row in table.iterrows():
        if not as_bool(row.get("active"), False):
            continue
        if (optional_text(row.get("dataset_id")) or "").casefold() != dataset_id.casefold():
            continue
        if not _matches(row.get("scenario"), scenario_id):
            continue
        points.append(ProteinRecoveryDataPoint.from_mapping(row))
    return tuple(points)


def load_phase4_inputs(
    path: Path = INPUT_WORKBOOK_PATH,
    *,
    scenario_id: str | None = None,
    phase3_scenario_id: str | None = None,
    selected_month: str | None = None,
) -> Phase4InputBundle:
    """Load selected PR0-PR6 controls and Phase 4 inputs from the master workbook."""

    workbook = ensure_input_workbook(path)
    control = _load_control(workbook)
    scenario = (
        scenario_id
        or optional_text(control.get("selected_phase4_scenario"))
        or "PR3"
    ).upper()
    if scenario not in {f"PR{i}" for i in range(7)}:
        raise ValueError("selected_phase4_scenario must be PR0, PR1, PR2, PR3, PR4, PR5, or PR6.")
    upstream = (
        phase3_scenario_id
        or optional_text(control.get("selected_phase3_scenario"))
        or "F2"
    ).upper()
    if upstream not in {"F0", "F1", "F2", "F3"}:
        raise ValueError("Phase 4 upstream scenario must be F0, F1, F2, or F3.")
    month = selected_month or optional_text(control.get("selected_month")) or "July"
    structural = as_bool(
        control.get("phase4_structural_test_mode"),
        as_bool(control.get("structural_test_mode"), False),
    )
    values, records, warnings = load_phase4_parameters(
        workbook,
        scenario_id=scenario,
        selected_month=month,
        structural_test_mode=structural,
    )
    acid_type = str(values.get("acid_type", "HydrochloricAcid"))
    curve_id = optional_text(values.get("acid_titration_curve_id"))
    dataset_id = optional_text(values.get("protein_recovery_dataset_id"))
    titration = _load_titration_points(
        workbook,
        curve_id=curve_id,
        acid_type=acid_type,
        scenario_id=scenario,
        selected_month=month,
    )
    recovery = _load_recovery_data(
        workbook,
        dataset_id=dataset_id,
        scenario_id=scenario,
    )
    if str(values.get("acid_demand_method", "")).casefold() == "titration_curve" and len(titration) < 2:
        raise ValueError(
            "Titration-curve acid demand requires at least two active AcidTitration rows."
        )
    return Phase4InputBundle(
        scenario,
        upstream,
        month,
        structural,
        values,
        records,
        titration,
        recovery,
        warnings,
    )
