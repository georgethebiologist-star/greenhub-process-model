"""Controlled vocabularies for GreenHub parameter resolution."""

from enum import StrEnum


class CalculationMode(StrEnum):
    STRUCTURAL = "structural"
    LITERATURE_DEFAULT = "literature_default"
    PROJECT_DATA = "project_data"
    CALIBRATED = "calibrated"
    EXPERT_OVERRIDE = "expert_override"


class ResolutionMode(StrEnum):
    STEADY_STATE = "steady_state"
    MONTHLY_INDEPENDENT = "monthly_independent"
    QUASI_DYNAMIC = "quasi_dynamic"
    DYNAMIC = "dynamic"


class CandidateKind(StrEnum):
    RUN_OVERRIDE = "run_specific_user_override"
    PROJECT_OVERRIDE = "saved_project_override"
    MEASURED_PROJECT = "measured_project"
    CALIBRATED_PROJECT = "calibrated_project"
    LITERATURE_DEFAULT = "literature_direct"
    WORKBOOK = "existing_workbook"
    STRUCTURAL_PLACEHOLDER = "structural_placeholder"
    MISSING = "missing"


class ValueStatus(StrEnum):
    MEASURED_PROJECT = "measured_project"
    CALIBRATED_PROJECT = "calibrated_project"
    LITERATURE_DIRECT = "literature_direct"
    FITTED_BY_SOURCE = "fitted_by_source"
    CALCULATED_FROM_SOURCE_EQUATION = "calculated_from_source_equation"
    MANUFACTURER_DIRECT = "manufacturer_direct"
    EXPLICIT_USER_OVERRIDE = "explicit_user_override"
    STRUCTURAL_PLACEHOLDER = "structural_placeholder"
    MISSING = "missing"
    NOT_APPLICABLE = "not_applicable"


class EditabilityCategory(StrEnum):
    SCENARIO_SELECTION = "scenario_selection"
    FEED_AND_SCHEDULING = "feed_and_scheduling"
    OPERATING_CONTROL = "operating_control"
    EQUIPMENT_DESIGN = "equipment_design"
    SCIENTIFIC_MODEL = "scientific_model_parameter"
    ECONOMIC_MAINTENANCE = "economic_maintenance"
    IMMUTABLE_PROVENANCE = "immutable_provenance_or_identity"


class EditableMode(StrEnum):
    NORMAL = "normal"
    DESIGN = "design"
    EXPERT = "expert"
    ECONOMIC = "economic"
    READ_ONLY = "read_only"


class ActivationState(StrEnum):
    BLOCKED = "blocked"
    REFERENCE_ONLY = "reference_only"
    ACTIVE = "active"


class ReadinessState(StrEnum):
    D1 = "D1"
    D2 = "D2"
    D3 = "D3"
    D4 = "D4"
    D5 = "D5"


class ResultStatus(StrEnum):
    CALCULATED = "calculated"
    MEASURED = "measured"
    OVERRIDDEN = "overridden"
    LITERATURE_DEFAULT = "literature_default"
    CALIBRATED = "calibrated"
    PLACEHOLDER = "placeholder"
    MISSING = "missing"
    BLOCKED = "blocked"
    NOT_APPLICABLE = "not_applicable"
    NOT_IMPLEMENTED = "not_implemented"
    FAILED = "failed"
