"""Master-workbook loading for seasonal Phase 2 feed characterization."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import pandas as pd

from Greenhub.input_schema import InputRecord, as_bool, optional_float, optional_text
from Greenhub.settings import DATA_DIR

INPUT_WORKBOOK_PATH = DATA_DIR / "greenhub_feed_inputs.xlsx"
README_SHEET = "ReadMe"
CONTROL_SHEET = "ModelControl"
MONTHLY_SHEET = "MonthlyMass"
MEASUREMENTS_SHEET = "FeedMeasurements"
PARAMETERS_SHEET = "Parameters"
METADATA_SHEET = "ComponentMetadata"

# Backward-compatible name retained for external notebooks from Phase 1.
COMPOSITION_SHEET = MEASUREMENTS_SHEET


@dataclass(frozen=True)
class FeedSpecification:
    """Selected seasonal feed dataset before component characterization."""

    selected_month: str
    sample_id: str
    scenario: str
    entry_mode: str
    monthly_total_mass_kg: float
    operating_days: float
    total_mass_flow_kg_hr: float
    records: tuple[InputRecord, ...]
    control: dict[str, object]
    monthly_table: pd.DataFrame
    measurements_table: pd.DataFrame


def ensure_input_workbook(path: Path = INPUT_WORKBOOK_PATH) -> Path:
    """Return the versioned master input workbook or raise a clear error."""

    if not path.exists():
        raise FileNotFoundError(
            f"GreenHub master input workbook was not found at '{path}'. "
            "Restore Greenhub/data/greenhub_feed_inputs.xlsx from the project files."
        )
    return path


def _control_mapping(control_df: pd.DataFrame) -> dict[str, object]:
    required = {"parameter", "value"}
    missing = required - set(control_df.columns)
    if missing:
        raise ValueError(f"'{CONTROL_SHEET}' is missing columns: {sorted(missing)}")
    return {
        str(row["parameter"]).strip(): row["value"]
        for _, row in control_df.iterrows()
        if optional_text(row.get("parameter"))
    }


def _control_text(control: dict[str, object], name: str, default: str) -> str:
    return optional_text(control.get(name)) or default


def load_feed_specification(
    path: Path = INPUT_WORKBOOK_PATH,
    *,
    selected_month: str | None = None,
    sample_id: str | None = None,
    scenario: str | None = None,
) -> FeedSpecification:
    """Load the active sample, scenario, and month from the master workbook."""

    path = ensure_input_workbook(path)
    control_df = pd.read_excel(path, sheet_name=CONTROL_SHEET)
    monthly_df = pd.read_excel(path, sheet_name=MONTHLY_SHEET)
    measurements_df = pd.read_excel(path, sheet_name=MEASUREMENTS_SHEET)
    control = _control_mapping(control_df)

    selected_month = selected_month or _control_text(control, "selected_month", "July")
    sample_id = sample_id or _control_text(control, "selected_sample_id", "baseline")
    scenario = scenario or _control_text(control, "selected_scenario", "baseline")
    entry_mode = _control_text(control, "entry_mode", "measured_liquid")
    if entry_mode != "measured_liquid":
        raise NotImplementedError(
            "Phase 2 fully implements only entry_mode='measured_liquid'. "
            "The roadside-grass mode is schema-ready but deferred to Phase 3."
        )

    month_names = monthly_df["month"].astype(str).str.casefold()
    mask = month_names.eq(selected_month.casefold())
    if "sample_id" in monthly_df:
        mask &= monthly_df["sample_id"].astype(str).str.casefold().eq(sample_id.casefold())
    if "scenario" in monthly_df:
        mask &= monthly_df["scenario"].astype(str).str.casefold().eq(scenario.casefold())
    month_rows = monthly_df.loc[mask]
    if month_rows.empty:
        raise ValueError(
            f"No MonthlyMass row matches sample='{sample_id}', scenario='{scenario}', "
            f"month='{selected_month}'."
        )
    month_row = month_rows.iloc[0]
    monthly_mass = optional_float(month_row.get("total_liquid_mass_kg"))
    operating_days = optional_float(month_row.get("operating_days"))
    if monthly_mass is None or monthly_mass <= 0.0:
        raise ValueError("Selected monthly liquid mass must be greater than zero.")
    if operating_days is None or operating_days <= 0.0:
        raise ValueError("Selected operating days must be greater than zero.")
    total_mass_flow = monthly_mass / (operating_days * 24.0)

    records: list[InputRecord] = []
    for _, row in measurements_df.iterrows():
        row_sample = optional_text(row.get("sample_id")) or "baseline"
        row_scenario = optional_text(row.get("scenario")) or "baseline"
        row_month = optional_text(row.get("month"))
        if row_sample.casefold() != sample_id.casefold() or row_scenario.casefold() != scenario.casefold():
            continue
        if row_month and row_month.casefold() not in {selected_month.casefold(), "all", "annual"}:
            continue
        record = InputRecord.from_mapping(row)
        if record.active:
            records.append(record)

    if not records:
        raise ValueError("The selected feed dataset contains no active input records.")

    return FeedSpecification(
        selected_month=selected_month,
        sample_id=sample_id,
        scenario=scenario,
        entry_mode=entry_mode,
        monthly_total_mass_kg=monthly_mass,
        operating_days=operating_days,
        total_mass_flow_kg_hr=total_mass_flow,
        records=tuple(records),
        control=control,
        monthly_table=monthly_df,
        measurements_table=measurements_df,
    )


def load_input_records_csv(path: Path) -> tuple[InputRecord, ...]:
    """Load normalized input records from a CSV file for tests or data exchange."""

    table = pd.read_csv(path)
    records = tuple(InputRecord.from_mapping(row) for _, row in table.iterrows())
    if not records:
        raise ValueError(f"Input CSV '{path}' contains no records.")
    return records


def control_flag(specification: FeedSpecification, name: str, default: bool = False) -> bool:
    """Read a boolean control from a loaded feed specification."""

    return as_bool(specification.control.get(name), default)
