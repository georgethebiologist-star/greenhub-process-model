"""Load immutable workbook defaults and approved literature candidates."""

from __future__ import annotations

import hashlib
from dataclasses import replace
from functools import lru_cache
from pathlib import Path
from typing import Any, Iterable

import pandas as pd

from Greenhub.input_data import CONTROL_SHEET, INPUT_WORKBOOK_PATH
from Greenhub.phase3_inputs import PHASE3_PARAMETERS_SHEET, Phase3ParameterRecord, _load_control
from Greenhub.phase4_inputs import PHASE4_PARAMETERS_SHEET, Phase4ParameterRecord
from Greenhub.phase5_inputs import PHASE5_PARAMETERS_SHEET, Phase5ParameterRecord
from Greenhub.phase6_inputs import PHASE6_PARAMETERS_SHEET, Phase6ParameterRecord
from Greenhub.phase7_inputs import PHASE7_PARAMETERS_SHEET, Phase7ParameterRecord

from .enums import (
    ActivationState,
    CalculationMode,
    CandidateKind,
    EditabilityCategory,
    EditableMode,
    ReadinessState,
    ValueStatus,
)
from .models import Applicability, CanonicalParameter, ParameterCandidate, Uncertainty, scalar_type
from .registry import ParameterRegistry

DATA_DIR = Path(__file__).resolve().parents[1] / "data"
LITERATURE_RECOVERY_PATH = DATA_DIR / "Protein recovery" / "Isoelectric" / "recovery.csv"
QUARANTINE_PATH = DATA_DIR / "global_audit_package" / "global_quarantine_register.csv"
RELATIVE_WORKBOOK_PATH = "Greenhub/data/greenhub_feed_inputs.xlsx"
RELATIVE_RECOVERY_PATH = "Protein recovery/Isoelectric/recovery.csv"

_PHASE_SHEETS = (
    ("phase3", "feed_preparation_and_primary_separation", PHASE3_PARAMETERS_SHEET, Phase3ParameterRecord),
    ("phase4", "protein_recovery", PHASE4_PARAMETERS_SHEET, Phase4ParameterRecord),
    ("phase5", "anaerobic_digestion", PHASE5_PARAMETERS_SHEET, Phase5ParameterRecord),
    ("phase6", "biogas_conditioning_and_upgrading", PHASE6_PARAMETERS_SHEET, Phase6ParameterRecord),
    ("phase7", "digestate_treatment_and_nutrient_recovery", PHASE7_PARAMETERS_SHEET, Phase7ParameterRecord),
)

_SCENARIO_CONTROLS = {
    "control.scenario.feed_preparation": (
        "selected_phase3_scenario",
        "F2",
        ("F0", "F1", "F2", "F3"),
        "Feed-preparation scenario",
    ),
    "control.scenario.protein_recovery": (
        "selected_phase4_scenario",
        "PR3",
        tuple(f"PR{i}" for i in range(7)),
        "Protein-recovery scenario",
    ),
    "control.scenario.anaerobic_digestion": (
        "selected_phase5_scenario",
        "AD1",
        tuple(f"AD{i}" for i in range(6)),
        "Anaerobic-digestion scenario",
    ),
    "control.scenario.biogas_upgrading": (
        "selected_phase6_scenario",
        "BG2",
        tuple(f"BG{i}" for i in range(7)),
        "Biogas-upgrading scenario",
    ),
    "control.scenario.nutrient_recovery": (
        "selected_phase7_scenario",
        "NR4",
        tuple(f"NR{i}" for i in range(8)),
        "Nutrient-recovery scenario",
    ),
    "control.process_order": (
        "selected_phase7_process_order",
        "A",
        ("A", "B", "C", "D"),
        "Nutrient-recovery process order",
    ),
    "control.selected_month": (
        "selected_month",
        "July",
        (
            "January", "February", "March", "April", "May", "June",
            "July", "August", "September", "October", "November", "December",
        ),
        "Selected operating month",
    ),
}


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _editability(name: str, category: str) -> tuple[EditabilityCategory, EditableMode]:
    key = f"{category} {name}".casefold()
    if any(word in key for word in ("cost", "price", "maintenance", "lifetime", "replacement")):
        return EditabilityCategory.ECONOMIC_MAINTENANCE, EditableMode.ECONOMIC
    if any(word in key for word in ("rate_constant", "activation_energy", "yield", "recovery", "efficiency", "partition", "inhibition", "permeance")):
        return EditabilityCategory.SCIENTIFIC_MODEL, EditableMode.EXPERT
    if any(word in key for word in ("capacity", "diameter", "height", "area", "volume", "stage", "design")):
        return EditabilityCategory.EQUIPMENT_DESIGN, EditableMode.DESIGN
    if any(word in key for word in ("flow", "temperature", "pressure", "ph", "time", "dose", "speed", "power")):
        return EditabilityCategory.OPERATING_CONTROL, EditableMode.NORMAL
    return EditabilityCategory.OPERATING_CONTROL, EditableMode.NORMAL


def _source_kind(record: Any) -> tuple[CandidateKind, ValueStatus]:
    status = str(getattr(record, "measurement_status", "")).casefold()
    source_class = str(getattr(record, "source_class", "E")).upper()
    if "calibrat" in status:
        return CandidateKind.CALIBRATED_PROJECT, ValueStatus.CALIBRATED_PROJECT
    if "measured" in status and "not_measured" not in status and source_class != "E":
        return CandidateKind.MEASURED_PROJECT, ValueStatus.MEASURED_PROJECT
    if source_class == "E":
        return CandidateKind.STRUCTURAL_PLACEHOLDER, ValueStatus.STRUCTURAL_PLACEHOLDER
    return CandidateKind.WORKBOOK, ValueStatus.STRUCTURAL_PLACEHOLDER


def _tuple_context(value: object) -> tuple[str, ...]:
    text = str(value or "All").strip()
    return () if text.casefold() in {"all", "annual"} else (text,)


def _normalized_unit(unit: str | None) -> str | None:
    """Normalize only explicit dimensionless fraction labels used by the workbook."""

    if unit is None:
        return None
    key = " ".join(str(unit).strip().split()).casefold()
    if key == "fraction" or key.startswith("fraction of "):
        return "fraction"
    return str(unit).strip()


def _load_workbook_records(
    workbook_path: Path,
) -> tuple[list[CanonicalParameter], list[ParameterCandidate]]:
    parameters: dict[str, CanonicalParameter] = {}
    candidates: list[ParameterCandidate] = []
    checksum = _sha256(workbook_path)
    for prefix, process_area, sheet, record_type in _PHASE_SHEETS:
        table = pd.read_excel(workbook_path, sheet_name=sheet)
        for row_number, (_, row) in enumerate(table.iterrows(), start=2):
            record = record_type.from_mapping(row)
            if not record.active:
                continue
            parameter_id = f"{prefix}.{record.python_name}"
            category = str(getattr(record, "category", "uncategorized"))
            label = str(getattr(record, "name", "") or record.python_name).replace("_", " ").strip().title()
            edit_category, edit_mode = _editability(record.python_name, category)
            value = record.value
            unit = record.unit
            normalized_unit = _normalized_unit(unit)
            if parameter_id not in parameters:
                parameters[parameter_id] = CanonicalParameter(
                    parameter_id=parameter_id,
                    display_name=label,
                    description=str(getattr(record, "comment", None) or f"Workbook parameter '{record.python_name}'."),
                    process_area=process_area,
                    unit_operation=category,
                    scenario_ids=_tuple_context(record.scenario),
                    value=value,
                    original_value=value,
                    original_unit=unit,
                    normalized_value=value,
                    normalized_unit=normalized_unit,
                    data_type=scalar_type(value) if value is not None else "number",
                    source_dataset=RELATIVE_WORKBOOK_PATH,
                    source_row_id=f"{sheet}:{row_number}",
                    source_title="GreenHub master input workbook",
                    exact_source_location=f"Sheet {sheet}, row {row_number}",
                    evidence_class=_source_kind(record)[1],
                    quality_class=str(record.source_class),
                    physical_lower_bound=getattr(record, "minimum", None),
                    physical_upper_bound=getattr(record, "maximum", None),
                    editability_category=edit_category,
                    editable_mode=edit_mode,
                    rebuild_required=False,
                    readiness_state=ReadinessState.D5,
                    activation_state=ActivationState.ACTIVE,
                    warnings=tuple(filter(None, (getattr(record, "comment", None),))),
                    input_type=scalar_type(value) if value is not None else "number",
                    affected_units=(),
                    model_parameter_name=record.python_name,
                )
            kind, value_status = _source_kind(record)
            candidates.append(
                ParameterCandidate(
                    candidate_id=f"workbook:{prefix}:{record.python_name}:{record.scenario}:{record.month}:{row_number}",
                    parameter_id=parameter_id,
                    value=value,
                    unit=normalized_unit,
                    source_kind=kind,
                    value_status=value_status,
                    source_dataset=RELATIVE_WORKBOOK_PATH,
                    source_row_id=f"{sheet}:{row_number}",
                    source_title="GreenHub master input workbook",
                    exact_source_location=f"Sheet {sheet}, row {row_number}",
                    evidence_class=str(record.measurement_status),
                    quality_class=str(record.source_class),
                    applicability=Applicability(
                        scenario_ids=_tuple_context(record.scenario),
                        months=_tuple_context(record.month),
                    ),
                    activation_state=ActivationState.ACTIVE,
                    readiness_state=ReadinessState.D5,
                    warnings=tuple(filter(None, (getattr(record, "comment", None),))),
                    provenance_chain=(f"sha256:{checksum}", f"{sheet}:{row_number}"),
                    selection_priority=int(getattr(record, "priority", 100)),
                )
            )
    return list(parameters.values()), candidates


def _load_scenario_controls(
    workbook_path: Path,
) -> tuple[list[CanonicalParameter], list[ParameterCandidate]]:
    control = _load_control(workbook_path)
    checksum = _sha256(workbook_path)
    definitions = []
    candidates = []
    for parameter_id, (workbook_name, fallback, options, label) in _SCENARIO_CONTROLS.items():
        value = str(control.get(workbook_name) or fallback)
        definitions.append(
            CanonicalParameter(
                parameter_id=parameter_id,
                display_name=label,
                description=f"Versioned selection corresponding to ModelControl.{workbook_name}.",
                process_area="model_control",
                value=value,
                original_value=value,
                normalized_value=value,
                data_type="categorical",
                source_dataset=RELATIVE_WORKBOOK_PATH,
                source_row_id=workbook_name,
                source_title="GreenHub master input workbook",
                exact_source_location=f"Sheet {CONTROL_SHEET}, parameter {workbook_name}",
                evidence_class=ValueStatus.STRUCTURAL_PLACEHOLDER,
                quality_class="project_control",
                editability_category=(
                    EditabilityCategory.FEED_AND_SCHEDULING
                    if parameter_id.endswith("selected_month")
                    else EditabilityCategory.SCENARIO_SELECTION
                ),
                editable_mode=EditableMode.NORMAL,
                rebuild_required=True,
                readiness_state=ReadinessState.D5,
                activation_state=ActivationState.ACTIVE,
                allowed_options=options,
                input_type="select",
            )
        )
        candidates.append(
            ParameterCandidate(
                candidate_id=f"workbook:control:{workbook_name}",
                parameter_id=parameter_id,
                value=value,
                unit=None,
                source_kind=CandidateKind.WORKBOOK,
                value_status=ValueStatus.STRUCTURAL_PLACEHOLDER,
                source_dataset=RELATIVE_WORKBOOK_PATH,
                source_row_id=workbook_name,
                source_title="GreenHub master input workbook",
                exact_source_location=f"Sheet {CONTROL_SHEET}, parameter {workbook_name}",
                activation_state=ActivationState.ACTIVE,
                readiness_state=ReadinessState.D5,
                provenance_chain=(f"sha256:{checksum}", workbook_name),
            )
        )
    return definitions, candidates


def _seasonal_storage_control() -> CanonicalParameter:
    """Expose storage capacity without inventing a default or source candidate."""

    return CanonicalParameter(
        parameter_id="seasonal.storage_capacity_kg",
        display_name="Seasonal biomass storage capacity",
        description="Maximum wet-biomass inventory. Leave null for an explicitly unbounded structural fallback.",
        process_area="feedstock_and_characterization",
        unit_operation="seasonal biomass storage",
        normalized_unit="kg",
        data_type="number",
        evidence_class=ValueStatus.MISSING,
        physical_lower_bound=0.0,
        editability_category=EditabilityCategory.EQUIPMENT_DESIGN,
        editable_mode=EditableMode.DESIGN,
        rebuild_required=False,
        readiness_state=ReadinessState.D1,
        activation_state=ActivationState.ACTIVE,
        warnings=("No project storage capacity is available; an explicit override is required to calculate overflow.",),
        input_type="number",
        affected_outputs=("storage_inventory_series", "throughput_series", "seasonal_summary"),
        affected_plots=("SEASONAL-INVENTORY",),
    )


def _seasonal_degradation_control() -> CanonicalParameter:
    """Expose an opt-in seasonal degradation rate (1/day) without inventing defaults."""

    return CanonicalParameter(
        parameter_id="seasonal.storage_degradation_rate_per_day",
        display_name="Seasonal storage degradation rate (1/day)",
        description=(
            "First-order degradation rate constant (1/day) applied to stored wet-biomass when supplied. "
            "Leave null to preserve previous behaviour (no degradation)."
        ),
        process_area="feedstock_and_characterization",
        unit_operation="seasonal biomass storage",
        normalized_unit="1/day",
        data_type="number",
        evidence_class=ValueStatus.MISSING,
        physical_lower_bound=0.0,
        editability_category=EditabilityCategory.SCIENTIFIC_MODEL,
        editable_mode=EditableMode.EXPERT,
        rebuild_required=False,
        readiness_state=ReadinessState.D1,
        activation_state=ActivationState.ACTIVE,
        warnings=("No validated degradation rates are available; supply a project or literature value to enable degradation." ,),
        input_type="number",
        affected_outputs=("storage_inventory_series", "seasonal_summary"),
    )


def _literature_precipitation_candidate() -> ParameterCandidate:
    quarantine = pd.read_csv(QUARANTINE_PATH)
    blocked = quarantine[
        quarantine["dataset"].eq(RELATIVE_RECOVERY_PATH)
        & quarantine["row_id"].eq("REC-001")
    ]
    if not blocked.empty:
        raise ValueError("REC-001 is quarantined and cannot be activated.")
    table = pd.read_csv(LITERATURE_RECOVERY_PATH)
    rows = table[table["parameter_id"].eq("REC-001")]
    if len(rows) != 1:
        raise ValueError("Expected exactly one REC-001 literature row.")
    row = rows.iloc[0]
    value = float(row["normalized_si_value"])
    return ParameterCandidate(
        candidate_id="literature:protein-isoelectric:REC-001",
        parameter_id="phase4.precipitation_efficiency",
        value=value,
        unit="fraction",
        source_kind=CandidateKind.LITERATURE_DEFAULT,
        value_status=ValueStatus.LITERATURE_DIRECT,
        source_dataset=RELATIVE_RECOVERY_PATH,
        source_row_id="REC-001",
        source_title=str(row["source_title"]),
        stable_identifier=str(row["doi_or_stable_id"]),
        exact_source_location=str(row["source_location"]),
        evidence_class=str(row["data_status"]),
        transferability_class=str(row["transferability_to_grass"]),
        quality_class="peer_reviewed_direct_grass_clover",
        basis=str(row["basis"]),
        applicability=Applicability(
            scenario_ids=("PR1",),
            calculation_modes=(CalculationMode.LITERATURE_DEFAULT, CalculationMode.EXPERT_OVERRIDE),
        ),
        activation_state=ActivationState.ACTIVE,
        readiness_state=ReadinessState.D4,
        warnings=(
            "REC-001 is reported on incoming total-N basis; GreenHub applies the fraction only to its lumped soluble-protein pool.",
            "The source material is grass-clover cleared juice, so project-specific grass-juice validation remains required.",
        ),
        provenance_chain=(
            f"sha256:{_sha256(LITERATURE_RECOVERY_PATH)}",
            "REC-001",
            "EQ-MB-001",
        ),
    )


@lru_cache(maxsize=8)
def _cached_registry(path_text: str, mtime_ns: int, size: int) -> ParameterRegistry:
    del mtime_ns, size
    workbook = Path(path_text)
    parameters, candidates = _load_workbook_records(workbook)
    control_parameters, control_candidates = _load_scenario_controls(workbook)
    parameters.extend(control_parameters)
    parameters.append(_seasonal_storage_control())
    parameters.append(_seasonal_degradation_control())
    candidates.extend(control_candidates)
    candidates.append(_literature_precipitation_candidate())
    updated = []
    for parameter in parameters:
        if parameter.parameter_id == "phase4.precipitation_efficiency":
            parameter = replace(
                parameter,
                readiness_state=ReadinessState.D4,
                activation_state=ActivationState.ACTIVE,
                affected_units=("R401",),
                affected_outputs=("dry_protein_product", "conditioned_protein_depleted_liquid"),
                affected_plots=("PR-PRECIP-RECOVERY",),
                warnings=parameter.warnings + (
                    "A D4 literature candidate is active only in PR1 literature_default or expert_override mode.",
                ),
            )
        updated.append(parameter)
    return ParameterRegistry(updated, candidates)


def load_default_registry(workbook_path: Path = INPUT_WORKBOOK_PATH) -> ParameterRegistry:
    path = Path(workbook_path).resolve()
    stat = path.stat()
    return _cached_registry(str(path), stat.st_mtime_ns, stat.st_size)
