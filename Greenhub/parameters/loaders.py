"""Load immutable workbook defaults and approved literature candidates."""

from __future__ import annotations

import hashlib
import json
import re
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
LITERATURE_RECOVERY_METADATA_PATH = DATA_DIR / "Protein recovery" / "Isoelectric" / "recovery_metadata.json"
LITERATURE_OPERATING_PATH = DATA_DIR / "Pre-treatment" / "Mechanical" / "literature_operating_candidates.csv"
LITERATURE_OPERATING_METADATA_PATH = DATA_DIR / "Pre-treatment" / "Mechanical" / "literature_operating_candidates_metadata.json"
DAIRY_STRUVITE_PILOT_PATH = (
    DATA_DIR
    / "Resource recovery"
    / "Phosphorus_Recovery"
    / "dairy_digestate_nf_struvite_pilot_2023_reference.csv"
)
DAIRY_STRUVITE_PILOT_METADATA_PATH = DAIRY_STRUVITE_PILOT_PATH.with_suffix(".source.json")
LITERATURE_H2S_PATH = DATA_DIR / "Bigas production + upgrade" / "Water_Scrubbing" / "h2s_temperature_parameter.csv"
GUO_2022_PRECIPITATION_PATH = (
    DATA_DIR
    / "Protein recovery"
    / "Isoelectric"
    / "grass_clover_pilot_press_PEF_protein_separation_guo_2022_abstract_reference.csv"
)
GUO_2022_PRECIPITATION_METADATA_PATH = GUO_2022_PRECIPITATION_PATH.with_suffix(
    ".source.json"
)
QUARANTINE_PATH = DATA_DIR / "global_audit_package" / "global_quarantine_register.csv"
RELATIVE_WORKBOOK_PATH = "Greenhub/data/greenhub_feed_inputs.xlsx"
RELATIVE_RECOVERY_PATH = "Protein recovery/Isoelectric/recovery.csv"
RELATIVE_GUO_2022_PRECIPITATION_PATH = (
    "Protein recovery/Isoelectric/"
    "grass_clover_pilot_press_PEF_protein_separation_guo_2022_abstract_reference.csv"
)

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
        "F1",
        ("F0", "F1"),
        "Feed-preparation scenario",
    ),
    "control.scenario.protein_recovery": (
        "selected_phase4_scenario",
        "PR3",
        tuple(f"PR{i}" for i in range(8)),
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


def _sha256_workbook_sheet(workbook_path: Path, sheet_name: str) -> str:
    """Hash canonicalized values from one authoritative sheet, not the XLSX container.

    The workbook embeds generated FAIR snapshot sheets. Hashing the whole file
    makes their refresh alter the source hash stored inside those same snapshots,
    creating a self-reference loop. A sheet-value hash stays stable when only
    generated reporting sheets, formatting, or workbook packaging changes.
    """

    frame = pd.read_excel(workbook_path, sheet_name=sheet_name)
    payload = frame.to_json(
        orient="split",
        date_format="iso",
        force_ascii=False,
        double_precision=15,
    )
    digest = hashlib.sha256()
    digest.update(sheet_name.encode("utf-8"))
    digest.update(b"\0")
    digest.update(payload.encode("utf-8"))
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


def _stable_identifier_from_reference(reference: str | None) -> str | None:
    """Retain a DOI embedded in a workbook's existing reference field."""

    if not reference:
        return None
    match = re.search(r"10\.\d{4,9}/[^\s,;]+", str(reference))
    return match.group(0).rstrip(".,;)") if match else None


def _load_workbook_records(
    workbook_path: Path,
) -> tuple[list[CanonicalParameter], list[ParameterCandidate]]:
    parameters: dict[str, CanonicalParameter] = {}
    candidates: list[ParameterCandidate] = []
    for prefix, process_area, sheet, record_type in _PHASE_SHEETS:
        checksum = _sha256_workbook_sheet(workbook_path, sheet)
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
            stable_identifier = _stable_identifier_from_reference(
                getattr(record, "reference", None)
            )
            scenario_ids = _tuple_context(record.scenario)
            source_class = str(record.source_class).upper()
            literature_titles = {
                "10.1016/j.fufo.2022.100173": "Guo et al. (2022), Future Foods 6, 100173",
                "10.1016/j.biortech.2011.07.020": (
                    "Pakarinen et al. (2011), Bioresource Technology 102, 8952–8957"
                ),
                "10.1016/j.rser.2022.112092": (
                    "Egwu et al. (2022), Renewable and Sustainable Energy Reviews 158, 112092"
                ),
            }
            source_title = (
                literature_titles.get(stable_identifier, "GreenHub master input workbook")
            )
            guo_temperature_default = (
                parameter_id == "phase4.precipitation_temperature_C"
                and stable_identifier == "10.1016/j.fufo.2022.100173"
                and float(value) == 60.0
                and str(record.source_class).upper() == "C"
            )
            guo_precipitation_ph_default = (
                parameter_id == "phase4.target_pH"
                and stable_identifier == "10.1016/j.fufo.2022.100173"
                and float(value) == 5.0
                and str(record.source_class).upper() == "C"
            )
            guo_pr3_default = guo_temperature_default or guo_precipitation_ph_default
            ad1_literature_defaults = {
                "phase5.digester_temperature_c": (
                    "10.1016/j.biortech.2011.07.020", 35.0, "B"
                ),
                "phase5.digester_pH": (
                    "10.1016/j.rser.2022.112092", 7.2, "C"
                ),
                "phase5.target_vs_olr_kg_m3_day": (
                    "10.1016/j.rser.2022.112092", 1.5, "B"
                ),
            }
            expected_ad1_evidence = ad1_literature_defaults.get(parameter_id)
            ad1_literature_default = bool(
                expected_ad1_evidence
                and scenario_ids == ("AD1",)
                and stable_identifier == expected_ad1_evidence[0]
                and value is not None
                and float(value) == expected_ad1_evidence[1]
                and source_class == expected_ad1_evidence[2]
            )
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
                    source_title=source_title,
                    stable_identifier=stable_identifier,
                    exact_source_location=f"Sheet {sheet}, row {row_number}",
                    evidence_class=_source_kind(record)[1],
                    quality_class=str(record.source_class),
                    physical_lower_bound=getattr(record, "minimum", None),
                    physical_upper_bound=getattr(record, "maximum", None),
                    editability_category=edit_category,
                    editable_mode=edit_mode,
                    rebuild_required=False,
                    readiness_state=(
                        ReadinessState.D4
                        if guo_pr3_default or ad1_literature_default
                        else ReadinessState.D5
                    ),
                    activation_state=ActivationState.ACTIVE,
                    warnings=tuple(filter(None, (getattr(record, "comment", None),))),
                    input_type=scalar_type(value) if value is not None else "number",
                    affected_units=(),
                    model_parameter_name=record.python_name,
                )
            kind, value_status = _source_kind(record)
            retired_pef = bool(set(scenario_ids) & {"F2", "F3"})
            provenance_chain = [f"sha256:{checksum}", f"{sheet}:{row_number}"]
            if stable_identifier:
                provenance_chain.append(f"doi:{stable_identifier}")
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
                    source_title=source_title,
                    stable_identifier=stable_identifier,
                    exact_source_location=f"Sheet {sheet}, row {row_number}",
                    evidence_class=(
                        "literature_linked_assumption"
                        if stable_identifier and source_class == "C"
                        else str(record.measurement_status)
                    ),
                    quality_class=source_class,
                    applicability=Applicability(
                        scenario_ids=scenario_ids,
                        months=_tuple_context(record.month),
                    ),
                    activation_state=(
                        ActivationState.BLOCKED if retired_pef else ActivationState.ACTIVE
                    ),
                    readiness_state=(
                        ReadinessState.D4
                        if guo_pr3_default or ad1_literature_default
                        else ReadinessState.D5
                    ),
                    warnings=tuple(filter(None, (
                        getattr(record, "comment", None),
                        "F2/F3 PEF routes are retired; retained as blocked historical candidates."
                        if retired_pef else None,
                    ))),
                    provenance_chain=tuple(provenance_chain),
                    selection_priority=int(getattr(record, "priority", 100)),
                )
            )
    return list(parameters.values()), candidates


def _load_scenario_controls(
    workbook_path: Path,
) -> tuple[list[CanonicalParameter], list[ParameterCandidate]]:
    control = _load_control(workbook_path)
    checksum = _sha256_workbook_sheet(workbook_path, CONTROL_SHEET)
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
        & quarantine["row_id"].eq("REC-005")
    ]
    if not blocked.empty:
        raise ValueError("REC-005 is quarantined and cannot be activated.")
    table = pd.read_csv(LITERATURE_RECOVERY_PATH)
    rows = table[table["parameter_id"].eq("REC-005")]
    if len(rows) != 1:
        raise ValueError("Expected exactly one REC-005 literature row.")
    row = rows.iloc[0]
    metadata = json.loads(LITERATURE_RECOVERY_METADATA_PATH.read_text(encoding="utf-8"))["records"]["REC-005"]
    value = float(row["normalized_si_value"])
    return ParameterCandidate(
        candidate_id="literature:protein-isoelectric:REC-005",
        parameter_id="phase4.precipitation_efficiency",
        value=value,
        unit="fraction",
        source_kind=CandidateKind.LITERATURE_DEFAULT,
        value_status=ValueStatus.LITERATURE_DIRECT,
        source_dataset=RELATIVE_RECOVERY_PATH,
        source_row_id="REC-005",
        source_title=str(row["source_title"]),
        stable_identifier=str(metadata["source_doi"]),
        exact_source_location=str(metadata["source_location"]),
        evidence_class=str(row["data_status"]),
        transferability_class=str(metadata["transferability_class"]),
        # The observation itself is B-class measured literature. Its use as a
        # GreenHub soluble-protein recovery fraction is an indirect transfer
        # from total-N precipitation, so the model-facing input is C-class.
        quality_class=str(metadata.get("application_quality_class", metadata["quality_class"])),
        basis=str(row["basis"]),
        applicability=Applicability(
            scenario_ids=("PR1",),
            calculation_modes=(CalculationMode.LITERATURE_DEFAULT, CalculationMode.EXPERT_OVERRIDE),
        ),
        activation_state=ActivationState.ACTIVE,
        readiness_state=ReadinessState.D4,
        warnings=(
            str(metadata["runtime_mapping"]),
            "The source material is cultivated ryegrass juice processed with a water-assisted second press and clarification; project-specific roadside-grass validation remains required.",
        ),
        provenance_chain=(
            f"sha256:{_sha256(LITERATURE_RECOVERY_PATH)}",
            "REC-005",
            "EQ-MB-001",
        ),
    )


def _literature_isoelectric_target_ph_candidate() -> ParameterCandidate:
    """Load the opt-in scalar endpoint of the published ryegrass pH range."""

    quarantine = pd.read_csv(QUARANTINE_PATH)
    blocked = quarantine[
        quarantine["dataset"].eq(RELATIVE_RECOVERY_PATH)
        & quarantine["row_id"].eq("REC-006")
    ]
    if not blocked.empty:
        raise ValueError("REC-006 is quarantined and cannot be activated.")
    table = pd.read_csv(LITERATURE_RECOVERY_PATH).fillna("")
    rows = table[table["parameter_id"].eq("REC-006")]
    if len(rows) != 1:
        raise ValueError("Expected exactly one REC-006 isoelectric pH row.")
    row = rows.iloc[0]
    metadata = json.loads(LITERATURE_RECOVERY_METADATA_PATH.read_text(encoding="utf-8"))
    details = metadata.get("records", {}).get("REC-006")
    if not isinstance(details, dict):
        raise ValueError("Missing provenance metadata for isoelectric pH candidate REC-006.")
    doi = str(row["doi_or_stable_id"])
    source_url = str(row["source_url"])
    if not doi or doi != str(details.get("source_doi", "")) or doi not in source_url:
        raise ValueError("REC-006 requires matching DOI and source URL metadata.")
    if str(row["unit"]).lower() != "ph" or str(row["valid_range"]).find("4.0") < 0:
        raise ValueError("REC-006 must retain its reported pH interval and pH unit.")
    return ParameterCandidate(
        candidate_id="literature:protein-isoelectric:REC-006",
        parameter_id="phase4.target_pH",
        value=float(row["value"]),
        unit="pH",
        source_kind=CandidateKind.LITERATURE_DEFAULT,
        value_status=ValueStatus.LITERATURE_DIRECT,
        source_dataset=RELATIVE_RECOVERY_PATH,
        source_row_id="REC-006",
        source_title=str(row["source_title"]),
        stable_identifier=doi,
        exact_source_location=str(row["source_location"]),
        evidence_class=str(details["evidence_class"]),
        transferability_class=str(details["transferability_class"]),
        quality_class=str(details["application_quality_class"]),
        basis=str(row["basis"]),
        applicability=Applicability(
            scenario_ids=("PR1",),
            calculation_modes=(CalculationMode.LITERATURE_DEFAULT, CalculationMode.EXPERT_OVERRIDE),
        ),
        activation_state=ActivationState.ACTIVE,
        readiness_state=ReadinessState.D4,
        warnings=(
            str(details["runtime_mapping"]),
            "The paper reports a pH 4.0–4.5 interval; the scalar 4.5 endpoint is an explicit assumption, not a unique optimum.",
            "The source uses cultivated ryegrass and a water-assisted double-press/clarification boundary, not GreenHub roadside feed.",
        ),
        provenance_chain=(
            f"sha256:{_sha256(LITERATURE_RECOVERY_PATH)}",
            "REC-006",
            f"doi:{doi}",
        ),
        selection_priority=5,
    )


def _literature_guo_precipitation_candidates() -> list[ParameterCandidate]:
    """Expose the two reported PR3 precipitation conditions as opt-in candidates.

    The source is an abstract-level grass/clover pilot comparator. Only its
    reported pH and temperature are calculation-connected; reported relative
    yield gains and product composition remain reference-only.
    """

    source_rows = {
        "GUO2022_PRECIPITATION_PH": (
            "phase4.target_pH",
            "precipitation_pH",
            5.0,
            "pH",
        ),
        "GUO2022_PRECIPITATION_TEMPERATURE": (
            "phase4.precipitation_temperature_C",
            "precipitation_temperature",
            60.0,
            "°C",
        ),
    }
    quarantine = pd.read_csv(QUARANTINE_PATH).fillna("")
    blocked = quarantine[
        quarantine["dataset"].astype(str).str.replace("\\", "/", regex=False).str.endswith(
            RELATIVE_GUO_2022_PRECIPITATION_PATH
        )
        & quarantine["row_id"].astype(str).isin(source_rows)
    ]
    if not blocked.empty:
        raise ValueError("A Guo et al. 2022 precipitation record is quarantined and cannot be activated.")

    table = pd.read_csv(GUO_2022_PRECIPITATION_PATH).fillna("")
    metadata = json.loads(GUO_2022_PRECIPITATION_METADATA_PATH.read_text(encoding="utf-8"))
    doi = str(metadata.get("publication_doi", ""))
    if not doi or metadata.get("source_id") != "SRC_GUO_GRASS_PEF_2022":
        raise ValueError("Guo et al. 2022 precipitation records require source identity and DOI metadata.")
    if doi != "10.1016/j.fufo.2022.100173":
        raise ValueError("Guo et al. 2022 precipitation DOI does not match the approved source record.")

    candidates = []
    for row_id, (parameter_id, metric, expected_value, unit) in source_rows.items():
        matches = table[table["observation_id"].eq(row_id)]
        if len(matches) != 1:
            raise ValueError(f"Expected exactly one Guo et al. 2022 observation for {row_id}.")
        row = matches.iloc[0]
        if (
            row["reported_metric"] != metric
            or row["publication_doi"] != doi
            or row["source_id"] != metadata["source_id"]
            or row["source_location"] != "Abstract"
            or float(row["value"]) != expected_value
        ):
            raise ValueError(f"Guo et al. 2022 observation {row_id} failed its source-integrity checks.")
        candidates.append(
            ParameterCandidate(
                candidate_id=f"literature:guo-2022:{row_id}",
                parameter_id=parameter_id,
                value=expected_value,
                unit=unit,
                source_kind=CandidateKind.LITERATURE_DEFAULT,
                value_status=ValueStatus.LITERATURE_DIRECT,
                source_dataset=RELATIVE_GUO_2022_PRECIPITATION_PATH,
                source_row_id=row_id,
                source_title=str(metadata["dataset_title"]),
                stable_identifier=doi,
                exact_source_location="Article abstract",
                evidence_class=str(row["evidence_class"]),
                quality_class="B",
                basis=(
                    f"Reported {metric.replace('_', ' ')} condition; "
                    f"source basis: {row['basis_or_comparison']}."
                ),
                applicability=Applicability(
                    scenario_ids=("PR3",),
                    calculation_modes=(CalculationMode.LITERATURE_DEFAULT, CalculationMode.EXPERT_OVERRIDE),
                ),
                activation_state=ActivationState.ACTIVE,
                readiness_state=ReadinessState.D4,
                warnings=(
                    "Opt-in PR3 comparator only: the source used cultivated 70:30 perennial-ryegrass/white-clover juice after industrial PEF and pilot screw pressing, not Dutch roadside grass.",
                    "Abstract-level operating condition; the source does not establish GreenHub-specific reagent demand, precipitation recovery, residence time, or heat duty.",
                    "Structural/workbook defaults remain selected outside literature-default or expert-override mode; explicit run/project overrides retain precedence.",
                ),
                provenance_chain=(
                    f"sha256:{_sha256(GUO_2022_PRECIPITATION_PATH)}",
                    row_id,
                    f"doi:{doi}",
                ),
                selection_priority=5,
            )
        )
    return candidates


def _literature_operating_candidates() -> list[ParameterCandidate]:
    """Load directly reported screw-press and digester setpoints as opt-in evidence."""

    table = pd.read_csv(LITERATURE_OPERATING_PATH).fillna("")
    metadata = json.loads(LITERATURE_OPERATING_METADATA_PATH.read_text(encoding="utf-8"))
    records = metadata.get("records", {})
    candidates = []
    for _, row in table.iterrows():
        candidate_id = str(row["candidate_id"])
        details = records.get(candidate_id)
        if not isinstance(details, dict):
            raise ValueError(f"Missing provenance metadata for literature candidate {candidate_id}.")
        doi = str(row["doi"])
        source_url = str(row["source_url"])
        if not doi or not source_url or doi not in source_url:
            raise ValueError(f"Literature candidate {candidate_id} has incomplete DOI/source URL metadata.")
        modes = (CalculationMode.LITERATURE_DEFAULT, CalculationMode.EXPERT_OVERRIDE)
        candidates.append(
            ParameterCandidate(
                candidate_id=f"literature:operating:{candidate_id}",
                parameter_id=str(row["parameter_id"]),
                value=float(row["value"]),
                unit=str(row["unit"]),
                source_kind=CandidateKind.LITERATURE_DEFAULT,
                value_status=ValueStatus.LITERATURE_DIRECT,
                source_dataset="Greenhub/data/Pre-treatment/Mechanical/literature_operating_candidates.csv",
                source_row_id=candidate_id,
                source_title=str(row["source_title"]),
                stable_identifier=doi,
                exact_source_location=str(row["source_location"]),
                evidence_class="directly_reported_peer_reviewed_literature",
                transferability_class=str(row["transferability_class"]),
                quality_class=str(row["quality_class"]),
                basis=str(row["measurement_basis"]),
                applicability=Applicability(
                    scenario_ids=(str(row["scenario_id"]),),
                    calculation_modes=modes,
                ),
                activation_state=ActivationState.ACTIVE,
                readiness_state=ReadinessState.D4,
                warnings=(
                    str(row["runtime_warning"]),
                    f"Evidence metadata: {details['applicability']}",
                ),
                provenance_chain=(
                    f"sha256:{_sha256(LITERATURE_OPERATING_PATH)}",
                    candidate_id,
                    f"doi:{doi}",
                ),
                selection_priority=5,
            )
        )
    return candidates


def _literature_struvite_candidates() -> list[ParameterCandidate]:
    """Expose calculation-connected struvite conditions as NR2-only proxies.

    The source is an NF retentate from dairy-effluent digestion, not GreenHub
    grass digestate. Only magnesium:P stoichiometry and residence time are
    connected to the current crystallizer equations; the reported pH condition
    remains reference-only because pH does not currently determine reagent dose
    or recovery in this Level-1 model.
    """

    table = pd.read_csv(DAIRY_STRUVITE_PILOT_PATH, dtype=str).fillna("")
    metadata = json.loads(DAIRY_STRUVITE_PILOT_METADATA_PATH.read_text(encoding="utf-8"))
    doi = str(metadata.get("doi", ""))
    source_url = str(metadata.get("url", ""))
    source_title = str(metadata.get("title", ""))
    source_id = str(metadata.get("source_id", ""))
    if not doi or doi not in source_url or not source_title or source_id != "TSARIDOU2023":
        raise ValueError("Dairy-digestate struvite candidates require matching DOI/source metadata.")

    rows = {str(row["record_id"]): row for _, row in table.iterrows()}
    ratio_id = "TSARIDOU2023-04"
    residence_id = "TSARIDOU2023-06"
    if ratio_id not in rows or residence_id not in rows:
        raise ValueError("The dairy-digestate struvite source is missing a required operating record.")

    ratio_row = rows[ratio_id]
    if (
        ratio_row["source_id"] != source_id
        or ratio_row["metric"] != "struvite_precipitation_molar_ratio_n_mg_p"
        or ratio_row["unit"] != "mol/mol/mol"
        or ratio_row["quality_class"] != "B"
    ):
        raise ValueError("The reported N:Mg:P ratio row does not match its registered source metadata.")
    try:
        n_mg_p = tuple(float(part.strip()) for part in ratio_row["reported_value"].split(":"))
    except (TypeError, ValueError) as error:
        raise ValueError("The struvite molar ratio must retain the reported N:Mg:P ordering.") from error
    if len(n_mg_p) != 3 or n_mg_p[0] <= 0 or n_mg_p[2] <= 0:
        raise ValueError("The reported N:Mg:P ratio must contain three positive values.")
    magnesium_to_phosphorus = n_mg_p[1] / n_mg_p[2]

    residence_row = rows[residence_id]
    if (
        residence_row["source_id"] != source_id
        or residence_row["metric"] != "struvite_precipitation_time"
        or residence_row["unit"] != "min"
        or residence_row["quality_class"] != "B"
    ):
        raise ValueError("The struvite residence-time row does not match its registered source metadata.")

    mappings = (
        (
            ratio_id,
            ratio_row,
            "phase7.struvite_magnesium_to_p_molar_ratio",
            magnesium_to_phosphorus,
            "mol Mg/mol P",
            "Source reports N:Mg:P = "
            + ":".join(f"{part:g}" for part in n_mg_p)
            + f"; the exact model Mg:P ratio is {magnesium_to_phosphorus:g} mol/mol.",
            "The current reactor applies this ratio to available Orthophosphate for magnesium-reagent demand.",
        ),
        (
            residence_id,
            residence_row,
            "phase7.struvite_residence_time_min",
            float(residence_row["reported_value"]),
            "min",
            str(residence_row["notes"]),
            "Residence time scales the modeled crystallizer working volume and mixer electricity; no residence-dependent recovery kinetics are represented.",
        ),
    )
    modes = (CalculationMode.LITERATURE_DEFAULT, CalculationMode.EXPERT_OVERRIDE)
    candidates: list[ParameterCandidate] = []
    for row_id, row, parameter_id, value, unit, exact_basis, equation_note in mappings:
        candidates.append(
            ParameterCandidate(
                candidate_id=f"literature:nutrient-recovery:{row_id}",
                parameter_id=parameter_id,
                value=value,
                unit=unit,
                source_kind=CandidateKind.LITERATURE_DEFAULT,
                value_status=ValueStatus.LITERATURE_DIRECT,
                source_dataset=(
                    "Greenhub/data/Resource recovery/Phosphorus_Recovery/"
                    "dairy_digestate_nf_struvite_pilot_2023_reference.csv"
                ),
                source_row_id=row_id,
                source_title=source_title,
                stable_identifier=doi,
                exact_source_location=str(row["source_location"]),
                evidence_class=str(row["evidence_class"]),
                transferability_class=(
                    "C screening proxy: dairy-effluent digestate NF retentate to GreenHub grass digestate; not a matched-matrix calibration"
                ),
                quality_class="C",
                basis=f"{row['basis_or_denominator']}; {exact_basis}",
                uncertainty=Uncertainty(
                    description=str(row["uncertainty_or_limit"]),
                    unit=unit,
                ),
                applicability=Applicability(
                    scenario_ids=("NR2",),
                    calculation_modes=modes,
                ),
                activation_state=ActivationState.ACTIVE,
                readiness_state=ReadinessState.D4,
                warnings=(
                    str(row["transferability"]),
                    str(row["uncertainty_or_limit"]),
                    equation_note,
                    "The source stream was nanofiltration retentate; GreenHub NR2 does not include that nanofiltration step.",
                ),
                provenance_chain=(
                    f"sha256:{_sha256(DAIRY_STRUVITE_PILOT_PATH)}",
                    row_id,
                    f"doi:{doi}",
                ),
                selection_priority=5,
            )
        )
    return candidates


def _literature_h2s_candidates() -> tuple[list[CanonicalParameter], list[ParameterCandidate]]:
    """Load measured-literature fit coefficients for BG2 H2S solubility."""

    table = pd.read_csv(LITERATURE_H2S_PATH).fillna("")
    expected = {
        "WS_H2S_T_001": ("phase6.water_scrubber_h2s_solubility_fit_low_a", "1", "water_scrubber_h2s_solubility_fit_low_a"),
        "WS_H2S_T_002": ("phase6.water_scrubber_h2s_solubility_fit_low_b_k", "K", "water_scrubber_h2s_solubility_fit_low_b_k"),
        "WS_H2S_T_003": ("phase6.water_scrubber_h2s_solubility_fit_high_a", "1", "water_scrubber_h2s_solubility_fit_high_a"),
        "WS_H2S_T_004": ("phase6.water_scrubber_h2s_solubility_fit_high_b_k", "K", "water_scrubber_h2s_solubility_fit_high_b_k"),
        "WS_H2S_T_005": ("phase6.water_scrubber_h2s_solubility_fit_high_c", "1", "water_scrubber_h2s_solubility_fit_high_c"),
        "WS_H2S_T_006": ("phase6.water_scrubber_h2s_solubility_fit_high_d_per_k", "1/K", "water_scrubber_h2s_solubility_fit_high_d_per_k"),
        "WS_H2S_T_007": ("phase6.water_scrubber_h2s_solubility_fit_transition_temperature_k", "K", "water_scrubber_h2s_solubility_fit_transition_temperature_k"),
        "WS_H2S_T_008": ("phase6.water_scrubber_h2s_solubility_fit_minimum_temperature_k", "K", "water_scrubber_h2s_solubility_fit_minimum_temperature_k"),
        "WS_H2S_T_009": ("phase6.water_scrubber_h2s_solubility_fit_maximum_temperature_k", "K", "water_scrubber_h2s_solubility_fit_maximum_temperature_k"),
    }
    if set(table["candidate_id"].astype(str)) != set(expected):
        raise ValueError("H2S solubility fit dataset must contain the nine registered coefficients and bounds.")
    definitions: list[CanonicalParameter] = []
    candidates: list[ParameterCandidate] = []
    for _, row in table.iterrows():
        candidate_id = str(row["candidate_id"])
        parameter_id, unit, model_name = expected[candidate_id]
        doi = str(row["doi"])
        source_url = str(row["source_url"])
        if not doi or not source_url or doi not in source_url:
            raise ValueError(f"H2S solubility evidence {candidate_id} requires a DOI-linked source URL.")
        if str(row["parameter_id"]) != parameter_id or str(row["unit"]) != unit:
            raise ValueError(f"H2S solubility evidence {candidate_id} has an unexpected parameter ID or unit.")
        common = dict(
            source_dataset="Greenhub/data/Bigas production + upgrade/Water_Scrubbing/h2s_temperature_parameter.csv",
            source_row_id=candidate_id,
            source_title=str(row["source_title"]),
            stable_identifier=doi,
            exact_source_location=str(row["source_location"]),
            quality_class="B",
            transferability_class="Direct pure-water equilibrium fit coefficient; not a full packed-column efficiency model",
            basis=str(row["basis"]),
            uncertainty=Uncertainty(
                description=str(row["uncertainty"]),
                unit=unit,
            ) if str(row["uncertainty"]).strip() else None,
        )
        definitions.append(CanonicalParameter(
            parameter_id=parameter_id,
            display_name=f"H2S solubility fit parameter {candidate_id[-1]}",
            description="Coefficient or validity boundary in the IUPAC-evaluated pure-water H2S mole-fraction-solubility fits.",
            process_area="biogas_conditioning_and_upgrading",
            unit_operation="water scrubbing absorber",
            unit_id="A611",
            scenario_ids=("BG2",),
            component="HydrogenSulfide",
            value=None,
            original_value=float(row["value"]),
            original_unit=unit,
            normalized_value=float(row["normalized_value"]),
            normalized_unit=str(row["normalized_unit"]),
            evidence_class=ValueStatus.FITTED_BY_SOURCE,
            physical_lower_bound=None if parameter_id.endswith("_a") else 0.0,
            editability_category=EditabilityCategory.SCIENTIFIC_MODEL,
            editable_mode=EditableMode.EXPERT,
            readiness_state=ReadinessState.D4,
            activation_state=ActivationState.ACTIVE,
            warnings=(
                "Applies to dilute H2S in pure water; pH/speciation, electrolyte effects, high-pressure non-ideality, and packed-column transfer remain unmodeled.",
                "The existing H2S reference absorption fraction remains a separate calibrated structural input.",
            ),
            affected_outputs=("BG2 H2S absorption", "biomethane composition"),
            affected_units=("A611",),
            model_parameter_name=model_name,
            **common,
        ))
        candidates.append(ParameterCandidate(
            candidate_id=f"literature:water-scrubbing:{candidate_id}",
            parameter_id=parameter_id,
            value=float(row["value"]),
            unit=unit,
            source_kind=CandidateKind.LITERATURE_DEFAULT,
            value_status=ValueStatus.FITTED_BY_SOURCE,
            evidence_class="calculated_from_measured_literature_equation",
            applicability=Applicability(
                scenario_ids=("BG2",),
                calculation_modes=(CalculationMode.LITERATURE_DEFAULT, CalculationMode.EXPERT_OVERRIDE),
            ),
            activation_state=ActivationState.ACTIVE,
            readiness_state=ReadinessState.D4,
            warnings=(
                "Relative pure-water solubility correction only; calibrated base absorption and gas-liquid transfer remain empirical.",
            ),
            provenance_chain=(candidate_id, f"doi:{doi}"),
            selection_priority=5,
            **common,
        ))
    return definitions, candidates


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
    candidates.append(_literature_isoelectric_target_ph_candidate())
    candidates.extend(_literature_guo_precipitation_candidates())
    candidates.extend(_literature_operating_candidates())
    candidates.extend(_literature_struvite_candidates())
    h2s_definitions, h2s_candidates = _literature_h2s_candidates()
    parameters.extend(h2s_definitions)
    candidates.extend(h2s_candidates)
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
