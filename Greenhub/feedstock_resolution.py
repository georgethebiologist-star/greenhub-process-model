"""Report-only preview for time-aware feedstock proxy resolution gates."""

from __future__ import annotations

import csv
from collections import Counter
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable

from Greenhub.feedstock_proxy import FeedstockProxyCandidate, FeedstockProxyValue, feedstock_proxy_resolution_candidates, load_feedstock_proxies
from Greenhub.scientific_equations import moisture_wet_basis_from_total_solids
from Greenhub.time_grid import TimeGridStep, generate_time_grid


PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_CSV_REPORT = PROJECT_ROOT / "Greenhub" / "results" / "feedstock_resolution_gates.csv"
DEFAULT_MARKDOWN_REPORT = PROJECT_ROOT / "docs" / "feedstock_resolution_readiness.md"
DEFAULT_EQUATION_QUEUE_REPORT = PROJECT_ROOT / "docs" / "feedstock_equation_implementation_queue.md"
FEEDSTOCK_DATA_DIR = PROJECT_ROOT / "Greenhub" / "data" / "Pre-treatment" / "Feedstock"
FEEDSTOCK_EQUATION_REGISTRY = FEEDSTOCK_DATA_DIR / "equation_registry.csv"
GLOBAL_EQUATION_ACTIVATION_REGISTRY = PROJECT_ROOT / "Greenhub" / "data" / "global_audit_package" / "equation_activation_registry.csv"


FEEDSTOCK_BASIS_EXPECTATIONS: dict[str, dict[str, tuple[str, ...] | str]] = {
    "moisture_wet_basis": {
        "expected_units": ("kg water/kg wet biomass",),
        "compatible_units": ("kg/kg wet biomass",),
        "basis": "wet biomass",
    },
    "total_solids_wet_basis": {
        "expected_units": ("kg/kg wet feed",),
        "compatible_units": ("kg total solids/kg wet feed", "kg/kg wet biomass"),
        "basis": "wet feed",
    },
    "volatile_solids_dry_basis": {
        "expected_units": ("kg VS/kg dry matter", "kg VS/kg TS"),
        "compatible_units": ("kg/kg dry matter", "kg/kg TS"),
        "basis": "dry matter",
    },
    "ash_dry_basis": {
        "expected_units": ("kg/kg dry matter",),
        "compatible_units": ("percent dry matter", "% dry matter"),
        "basis": "dry matter",
    },
    "carbon_dry_basis": {
        "expected_units": ("kg/kg dry matter",),
        "compatible_units": ("percent dry matter", "% dry matter"),
        "basis": "dry matter",
    },
    "hydrogen_dry_basis": {
        "expected_units": ("kg/kg dry matter",),
        "compatible_units": ("percent dry matter", "% dry matter"),
        "basis": "dry matter",
    },
    "oxygen_dry_basis": {
        "expected_units": ("kg/kg dry matter",),
        "compatible_units": ("percent dry matter", "% dry matter"),
        "basis": "dry matter",
    },
    "nitrogen_dry_basis": {
        "expected_units": ("kg/kg dry matter",),
        "compatible_units": ("percent dry matter", "% dry matter"),
        "basis": "dry matter",
    },
    "sulfur_dry_basis": {
        "expected_units": ("kg/kg dry matter",),
        "compatible_units": ("percent dry matter", "% dry matter"),
        "basis": "dry matter",
    },
    "carbon_to_nitrogen_ratio": {
        "expected_units": ("kg C/kg N",),
        "compatible_units": (),
        "basis": "mass ratio",
    },
    "bulk_density": {
        "expected_units": ("kg/m3",),
        "compatible_units": (),
        "basis": "as received volume",
    },
    "total_protein_dry_basis": {
        "expected_units": ("kg/kg dry matter",),
        "compatible_units": ("percent dry matter", "% dry matter"),
        "basis": "dry matter",
    },
    "extractive_sugars_dry_basis": {
        "expected_units": ("kg/kg dry matter",),
        "compatible_units": ("percent dry matter", "% dry matter"),
        "basis": "dry matter",
    },
}


FEEDSTOCK_EQUIVALENT_UNIT_LABELS: set[tuple[str, str]] = {
    ("kg/kg wet biomass", "kg water/kg wet biomass"),
    ("kg/kg ts", "kg/kg dry matter"),
    ("kg vs/kg ts", "kg vs/kg dry matter"),
}


FEEDSTOCK_OBSERVED_VALUE_FIELDS = {
    "moisture_wet_basis",
    "volatile_solids_dry_basis",
    "ash_dry_basis",
    "carbon_dry_basis",
    "hydrogen_dry_basis",
    "oxygen_dry_basis",
    "nitrogen_dry_basis",
    "sulfur_dry_basis",
    "carbon_to_nitrogen_ratio",
    "bulk_density",
    "total_protein_dry_basis",
    "extractive_sugars_dry_basis",
}
FEEDSTOCK_REFERENCE_EQUATION_FIELDS = {"bmp_buswell", "bmp_boyle"}


class FeedstockResolutionMode:
    EMPIRICAL_EXISTING = "empirical_existing"
    MEASURED_PROJECT_DATA = "measured_project_data"
    LITERATURE_PROXY_STATIC = "literature_proxy_static"
    DYNAMIC_TIME_AWARE_REPORT_ONLY = "dynamic_time_aware_report_only"
    DYNAMIC_TIME_AWARE_ACTIVE_FUTURE = "dynamic_time_aware_active_future"
    EXPERT_OVERRIDE = "expert_override"


def default_feedstock_resolution_mode() -> str:
    return FeedstockResolutionMode.EMPIRICAL_EXISTING


def describe_feedstock_resolution_modes() -> dict[str, dict[str, object]]:
    return {
        FeedstockResolutionMode.EMPIRICAL_EXISTING: {
            "calculation_ready": True,
            "selectable_for_calculations": True,
            "status": "current_default",
            "notes": "Existing empirical GreenHub behavior; independent from proxy and dynamic reports.",
        },
        FeedstockResolutionMode.MEASURED_PROJECT_DATA: {
            "calculation_ready": False,
            "selectable_for_calculations": False,
            "status": "report_only_scaffold",
            "notes": "Outranks proxies only inside the report-only feedstock resolver for now.",
        },
        FeedstockResolutionMode.LITERATURE_PROXY_STATIC: {
            "calculation_ready": False,
            "selectable_for_calculations": False,
            "status": "report_only_scaffold",
            "notes": "Static literature proxy review path; does not overwrite empirical defaults.",
        },
        FeedstockResolutionMode.DYNAMIC_TIME_AWARE_REPORT_ONLY: {
            "calculation_ready": False,
            "selectable_for_calculations": False,
            "status": "report_only_scaffold",
            "notes": "Time-aware readiness and candidate preview only; no interpolation or activation.",
        },
        FeedstockResolutionMode.DYNAMIC_TIME_AWARE_ACTIVE_FUTURE: {
            "calculation_ready": False,
            "selectable_for_calculations": False,
            "status": "blocked_future_mode",
            "notes": "Documented future mode; blocked until separate activation design and safety tests exist.",
        },
        FeedstockResolutionMode.EXPERT_OVERRIDE: {
            "calculation_ready": False,
            "selectable_for_calculations": False,
            "status": "user_owned_high_risk_future_mode",
            "notes": "Reserved for explicit expert-owned overrides with provenance and review gates.",
        },
    }


def expected_feedstock_basis(canonical_field: str) -> dict[str, object]:
    spec = FEEDSTOCK_BASIS_EXPECTATIONS.get(canonical_field)
    if spec is None:
        return {
            "canonical_field": canonical_field,
            "expected_units": (),
            "expected_unit": "",
            "compatible_units": (),
            "basis": "",
            "known_safe_field": False,
        }
    expected_units = tuple(spec["expected_units"])
    return {
        "canonical_field": canonical_field,
        "expected_units": expected_units,
        "expected_unit": _display_expected_unit(expected_units),
        "compatible_units": tuple(spec["compatible_units"]),
        "basis": spec["basis"],
        "known_safe_field": True,
    }


def validate_feedstock_candidate_basis(
    canonical_field: str,
    observed_unit: str | None,
    value: float | None = None,
) -> dict[str, object]:
    expectation = expected_feedstock_basis(canonical_field)
    observed = _normalize_unit(observed_unit)
    expected_units = tuple(expectation["expected_units"])
    compatible_units = tuple(expectation["compatible_units"])
    expected_display = str(expectation["expected_unit"])
    expected_normalized = {_normalize_unit(unit).casefold() for unit in expected_units}
    compatible_normalized = {_normalize_unit(unit).casefold() for unit in compatible_units}

    if not expectation["known_safe_field"]:
        status = "blocked_no_equation_mapping"
        blocked_reason = "no_basis_expectation"
    elif observed.casefold() in expected_normalized:
        status = "basis_ok"
        blocked_reason = ""
    elif observed.casefold() in compatible_normalized:
        status = "requires_basis_conversion"
        blocked_reason = "compatible_unit_not_exact"
    else:
        status = "blocked_wrong_basis"
        blocked_reason = "wrong_or_unclear_basis"

    return {
        "canonical_field": canonical_field,
        "basis_status": status,
        "expected_unit": expected_display,
        "observed_unit": observed,
        "requires_basis_conversion": status == "requires_basis_conversion",
        "blocked_reason": blocked_reason,
        "value": value,
    }


def describe_feedstock_conversion_policy() -> dict[str, object]:
    return {
        "automatic_numeric_conversion": False,
        "range_midpoints": "blocked",
        "statuses": {
            "allowed_exact_unit": "Observed unit exactly matches the expected unit; no conversion is required.",
            "allowed_with_no_numeric_change": "Observed unit is a known equivalent label; value is reported unchanged.",
            "possible_but_requires_explicit_conversion": "Conversion may be possible later, but this report-only layer does not convert.",
            "dimension_specific_no_generic_conversion": "Field needs a field-specific rule; no generic conversion is allowed.",
            "blocked_unknown_unit": "Unit is not recognized for this canonical field.",
        },
        "explicit_conversion_families": (
            "percentage to kg/kg",
            "g/kg to kg/kg",
            "mg/L to kg/m3",
        ),
    }


def can_convert_feedstock_unit(
    observed_unit: str | None,
    expected_unit: str | None,
    canonical_field: str,
    value_min: float | None = None,
    value_max: float | None = None,
) -> dict[str, object]:
    observed = _normalize_unit(observed_unit)
    expected = _normalize_unit(expected_unit)
    expected_options = _expected_unit_options(expected)
    observed_key = observed.casefold()
    expected_keys = {item.casefold() for item in expected_options}
    range_note = " Range values preserve min/max; no midpoint is derived." if value_min is not None or value_max is not None else ""

    if not observed or not expected:
        status = "blocked_unknown_unit"
        required = False
        allowed = False
        note = "Observed or expected unit is missing."
    elif observed_key in expected_keys:
        status = "allowed_exact_unit"
        required = False
        allowed = True
        note = "Exact expected unit; no conversion is required."
    elif _is_equivalent_feedstock_label(observed_key, expected_keys):
        status = "allowed_with_no_numeric_change"
        required = False
        allowed = True
        note = "Known equivalent unit label; numeric value is reported unchanged."
    elif canonical_field == "carbon_to_nitrogen_ratio" or canonical_field.casefold() == "ph":
        status = "dimension_specific_no_generic_conversion"
        required = False
        allowed = False
        note = "Dimension-specific field; no generic feedstock conversion is allowed."
    elif _requires_explicit_feedstock_conversion(observed_key, expected_keys):
        status = "possible_but_requires_explicit_conversion"
        required = True
        allowed = False
        note = "Conversion may be possible, but it requires an explicit reviewed conversion step."
    else:
        status = "blocked_unknown_unit"
        required = False
        allowed = False
        note = "Unknown or unsupported feedstock unit pairing."

    return {
        "canonical_field": canonical_field,
        "observed_unit": observed,
        "expected_unit": expected,
        "conversion_policy_status": status,
        "conversion_required": required,
        "conversion_allowed": allowed,
        "conversion_note": note + range_note,
        "preserves_range_values": value_min is not None or value_max is not None,
    }


def expected_feedstock_equation_mapping(
    candidates: Iterable[FeedstockProxyCandidate] | None = None,
) -> dict[str, dict[str, object]]:
    items = list(candidates) if candidates is not None else feedstock_proxy_resolution_candidates()
    mapping: dict[str, dict[str, object]] = {}
    for item in sorted(items, key=lambda candidate: (candidate.source_priority, candidate.parameter_id)):
        mapping.setdefault(item.canonical_field, validate_feedstock_equation_mapping(item))
    return mapping


def validate_feedstock_equation_mapping(candidate: FeedstockProxyCandidate) -> dict[str, object]:
    equation_id = _candidate_equation_id(candidate)
    registry_ids = _feedstock_equation_registry_ids()
    field = candidate.canonical_field

    if field in FEEDSTOCK_OBSERVED_VALUE_FIELDS and candidate.value is not None:
        return {
            "canonical_field": field,
            "parameter_id": candidate.parameter_id,
            "equation_mapping_status": "no_equation_required_observed_value",
            "equation_id": "",
            "equation_note": "Observed or directly reported composition value; no equation is required for report-only resolution.",
        }
    if field in FEEDSTOCK_REFERENCE_EQUATION_FIELDS:
        return {
            "canonical_field": field,
            "parameter_id": candidate.parameter_id,
            "equation_mapping_status": "equation_available_reference_only",
            "equation_id": equation_id,
            "equation_note": "BMP-related value remains reference-only and is not activated as a feedstock equation.",
        }
    if equation_id:
        if equation_id in registry_ids:
            return {
                "canonical_field": field,
                "parameter_id": candidate.parameter_id,
                "equation_mapping_status": "equation_available_reference_only",
                "equation_id": equation_id,
                "equation_note": "Equation is present in the feedstock registry, but remains reference-only.",
            }
        return {
            "canonical_field": field,
            "parameter_id": candidate.parameter_id,
            "equation_mapping_status": "blocked_unimplemented_equation",
            "equation_id": equation_id,
            "equation_note": "Equation is referenced by data but has no approved feedstock implementation.",
        }
    if candidate.readiness_category == "blocked_missing":
        return {
            "canonical_field": field,
            "parameter_id": candidate.parameter_id,
            "equation_mapping_status": "blocked_missing_inputs",
            "equation_id": "",
            "equation_note": "Candidate is missing required input data; no equation can be resolved.",
        }
    if candidate.requires_equation_mapping or candidate.readiness_category == "blocked_no_equation_mapping":
        return {
            "canonical_field": field,
            "parameter_id": candidate.parameter_id,
            "equation_mapping_status": "requires_equation_mapping",
            "equation_id": "",
            "equation_note": "Candidate needs an explicit equation mapping before any future activation.",
        }
    return {
        "canonical_field": field,
        "parameter_id": candidate.parameter_id,
        "equation_mapping_status": "requires_equation_mapping",
        "equation_id": "",
        "equation_note": "No feedstock equation mapping is currently assigned.",
    }


def build_feedstock_equation_implementation_queue(
    markdown_path: Path = DEFAULT_EQUATION_QUEUE_REPORT,
) -> list[dict[str, object]]:
    """Build a report-only queue from feedstock and feedstock-adjacent equation registries."""

    queue: dict[tuple[str, str], dict[str, object]] = {}
    typed_ids = _typed_equation_ids()
    typed_activation = _typed_equation_activation_statuses()
    audit_rows = _global_feedstock_audit_rows()
    audit_by_id = {(row.get("dataset_group", ""), row.get("equation_id", "")): row for row in audit_rows}

    for row in _read_csv_rows(FEEDSTOCK_EQUATION_REGISTRY):
        item = _queue_item_from_feedstock_registry_row(row, typed_ids, typed_activation, audit_by_id)
        queue[(str(item["source_file"]), str(item["equation_id"]))] = item

    for source_file in ("roadside_grass_composition_scientific.csv", "roadside_grass_missing_proxy_candidates_extended.csv"):
        for row in _read_csv_rows(FEEDSTOCK_DATA_DIR / source_file):
            if not row.get("equation_id", ""):
                continue
            item = _queue_item_from_data_equation_row(row, source_file, typed_ids, typed_activation)
            queue.setdefault((str(item["source_file"]), str(item["equation_id"])), item)

    for row in audit_rows:
        item = _queue_item_from_global_audit_row(row, typed_ids, typed_activation)
        queue.setdefault((str(item["source_file"]), str(item["equation_id"])), item)

    items = sorted(queue.values(), key=lambda item: (str(item["implementation_status"]), str(item["equation_id"])))
    _write_feedstock_equation_queue_report(markdown_path, items)
    return items


def derive_feedstock_report_values(
    allow_derived: bool = False,
    proxies: dict[str, FeedstockProxyValue] | None = None,
) -> list[dict[str, object]]:
    """Return feedstock values for reporting, optionally appending typed derivations."""

    items = dict(proxies) if proxies is not None else load_feedstock_proxies()
    rows = [_feedstock_proxy_report_row(item) for item in items.values()]
    if not allow_derived:
        return rows

    total_solids = items.get("total_solids_wet_basis")
    if total_solids is None:
        return rows
    input_basis = validate_feedstock_candidate_basis("total_solids_wet_basis", total_solids.unit, total_solids.value)
    output_basis = validate_feedstock_candidate_basis("moisture_wet_basis", "kg water/kg wet biomass")
    if input_basis["basis_status"] not in {"basis_ok", "requires_basis_conversion"} or output_basis["basis_status"] != "basis_ok":
        return rows

    derived_value = moisture_wet_basis_from_total_solids(total_solids.value)
    rows.append(
        {
            "canonical_field": "moisture_wet_basis",
            "value": derived_value,
            "unit": "kg water/kg wet biomass",
            "equation_id": "EQ-CALC-001",
            "source_parameter_id": total_solids.parameter_id,
            "status": "derived_report_only",
            "activation_status": "report_only",
            "provenance": {
                "mode": "report_only",
                "source_field": "total_solids_wet_basis",
                "source_file": total_solids.source_file,
                "source_unit": total_solids.unit,
                "input_basis_status": input_basis["basis_status"],
                "output_basis_status": output_basis["basis_status"],
                "observed_moisture_overwritten": False,
            },
        }
    )
    return rows


@dataclass(frozen=True)
class FeedstockResolutionPreview:
    canonical_field: str
    category: str
    source_file: str
    parameter_id: str
    time_basis: str
    applicable_months: tuple[str, ...]
    seasonal_class: str | None
    no_interpolation: bool
    candidate_readiness: str
    can_activate_by_default: bool
    requires_user_selection: bool
    requires_equation_mapping: bool
    requires_basis_conversion: bool
    source_priority: int
    value: float | None
    unit: str
    value_min: float | None
    value_max: float | None
    evidence_quality: str
    direct_or_indirect: str
    blocked_reason: str
    doi_or_url: str
    limitation_note: str

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True)
class FeedstockCandidateResolution:
    canonical_field: str
    time_label: str
    selected_parameter_id: str | None
    value: float | None
    value_min: float | None
    value_max: float | None
    unit: str
    source_priority: int | None
    resolution_status: str
    blocked_reason: str
    requires_user_selection: bool
    basis_status: str
    expected_unit: str
    observed_unit: str
    requires_basis_conversion: bool
    conversion_policy_status: str
    conversion_required: bool
    conversion_allowed: bool
    conversion_note: str
    equation_mapping_status: str
    equation_id: str
    equation_note: str
    provenance: dict[str, object]

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True)
class MeasuredFeedstockOverride:
    canonical_field: str
    value: float
    unit: str
    time_label: str | None = None
    source_id: str | None = None
    lab_reference: str | None = None
    notes: str = ""

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


def preview_feedstock_resolution_gates(
    start_date: str | None = None,
    end_date: str | None = None,
    time_step: str = "monthly",
    candidates: Iterable[FeedstockProxyCandidate] | None = None,
) -> list[FeedstockResolutionPreview]:
    """Combine feedstock evidence candidates with a generated time grid.

    This is report-only. It does not enable dynamic resolution, interpolate
    seasonal data, or return values for model calculations.
    """

    grid = generate_time_grid(start_date, end_date, time_step)
    items = list(candidates) if candidates is not None else feedstock_proxy_resolution_candidates()
    return [_preview_from_candidate(item, grid, time_step) for item in items]


def resolve_feedstock_candidate(
    canonical_field: str,
    time_label: str,
    mode: str = "report_only",
    allow_indirect: bool = False,
    candidates: Iterable[FeedstockProxyCandidate] | None = None,
) -> FeedstockCandidateResolution:
    """Select one feedstock candidate for reporting without activating it."""

    if mode != "report_only":
        raise ValueError("Feedstock candidate resolution is report_only only.")
    items = [item for item in (candidates or feedstock_proxy_resolution_candidates()) if item.canonical_field == canonical_field]
    if not items:
        return _blocked_resolution(canonical_field, time_label, "blocked_missing", "no_candidate")

    ranked = sorted(items, key=lambda item: (item.source_priority, item.parameter_id))
    for item in ranked:
        time_block = _time_blocked(item, time_label)
        if time_block:
            continue
        if item.readiness_category == "project_data_ready":
            return _resolution_from_candidate(item, time_label, "measured_project_data", "", False)
        if item.readiness_category == "direct_literature_proxy" and item.can_activate_by_default:
            return _resolution_from_candidate(item, time_label, "direct_literature_proxy", "", False)
        if item.readiness_category == "fallback_literature_proxy":
            return _resolution_from_candidate(item, time_label, "fallback_literature_proxy", "", False)
        if item.readiness_category == "sensitivity_only_indirect_proxy":
            if allow_indirect:
                return _resolution_from_candidate(item, time_label, "sensitivity_only_indirect_proxy", "", True)
            return _resolution_from_candidate(item, time_label, "requires_user_selection", "indirect_not_allowed", True)
        if item.readiness_category in {"blocked_missing", "blocked_wrong_basis", "blocked_no_equation_mapping"}:
            return _resolution_from_candidate(item, time_label, item.readiness_category, _blocked_reason(item.readiness_category), True)

    first = ranked[0]
    if _time_blocked(first, time_label):
        return _resolution_from_candidate(first, time_label, "blocked_time_mapping", "no_time_grid_overlap", True)
    return _resolution_from_candidate(first, time_label, "requires_user_selection", "not_default_resolvable", True)


def resolve_feedstock_candidates_for_grid(
    canonical_fields: Iterable[str],
    time_labels: Iterable[str],
    mode: str = "report_only",
    allow_indirect: bool = False,
    candidates: Iterable[FeedstockProxyCandidate] | None = None,
) -> list[FeedstockCandidateResolution]:
    items = list(candidates) if candidates is not None else feedstock_proxy_resolution_candidates()
    return [
        resolve_feedstock_candidate(field, label, mode=mode, allow_indirect=allow_indirect, candidates=items)
        for field in canonical_fields
        for label in time_labels
    ]


def validate_measured_feedstock_overrides(
    overrides: Iterable[MeasuredFeedstockOverride],
    candidates: Iterable[FeedstockProxyCandidate] | None = None,
) -> list[dict[str, object]]:
    items = list(candidates) if candidates is not None else feedstock_proxy_resolution_candidates()
    return [_validate_measured_override(override, items) for override in overrides]


def resolve_with_measured_overrides(
    canonical_field: str,
    time_label: str,
    measured_overrides: Iterable[MeasuredFeedstockOverride] = (),
    mode: str = "report_only",
    allow_indirect: bool = False,
    candidates: Iterable[FeedstockProxyCandidate] | None = None,
) -> FeedstockCandidateResolution:
    if mode != "report_only":
        raise ValueError("Feedstock candidate resolution is report_only only.")
    items = list(candidates) if candidates is not None else feedstock_proxy_resolution_candidates()
    matches = [
        item
        for item in measured_overrides
        if item.canonical_field == canonical_field and (item.time_label is None or item.time_label == time_label)
    ]
    if matches:
        validation = _validate_measured_override(matches[0], items)
        if validation["resolution_status"] == "measured_project_data":
            return _resolution_from_measured_override(matches[0], time_label, validation)
        return _blocked_resolution(
            canonical_field,
            time_label,
            str(validation["resolution_status"]),
            str(validation["blocked_reason"]),
            expected_unit=str(validation.get("expected_unit", "")),
            observed_unit=str(validation.get("observed_unit", validation.get("unit", ""))),
            requires_basis_conversion=validation["resolution_status"] == "requires_basis_conversion",
            conversion_policy_status=str(validation.get("conversion_policy_status", "")),
            conversion_required=bool(validation.get("conversion_required", False)),
            conversion_allowed=bool(validation.get("conversion_allowed", False)),
            conversion_note=str(validation.get("conversion_note", "")),
        )
    return resolve_feedstock_candidate(
        canonical_field,
        time_label,
        mode=mode,
        allow_indirect=allow_indirect,
        candidates=items,
    )


def feedstock_resolution_to_report_rows(
    records: Iterable[FeedstockCandidateResolution],
) -> list[dict[str, object]]:
    return [
        {
            "canonical_field": item.canonical_field,
            "time_label": item.time_label,
            "selected_parameter_id": item.selected_parameter_id,
            "value": item.value,
            "value_min": item.value_min,
            "value_max": item.value_max,
            "unit": item.unit,
            "source_priority": item.source_priority,
            "resolution_status": item.resolution_status,
            "blocked_reason": item.blocked_reason,
            "requires_user_selection": item.requires_user_selection,
            "basis_status": item.basis_status,
            "expected_unit": item.expected_unit,
            "observed_unit": item.observed_unit,
            "requires_basis_conversion": item.requires_basis_conversion,
            "conversion_policy_status": item.conversion_policy_status,
            "conversion_required": item.conversion_required,
            "conversion_allowed": item.conversion_allowed,
            "conversion_note": item.conversion_note,
            "equation_mapping_status": item.equation_mapping_status,
            "equation_id": item.equation_id,
            "equation_note": item.equation_note,
            "provenance": item.provenance,
        }
        for item in records
    ]


def summarize_feedstock_resolution_gates(
    previews: Iterable[FeedstockResolutionPreview] | None = None,
) -> list[dict[str, object]]:
    items = list(previews) if previews is not None else preview_feedstock_resolution_gates()
    counts: dict[tuple[str, str, str], int] = {}
    for item in items:
        key = (item.category, item.canonical_field, item.source_file)
        counts[key] = counts.get(key, 0) + 1
    return [
        {"category": category, "count": count, "canonical_field": field, "source_file": source_file}
        for (category, field, source_file), count in sorted(counts.items())
    ]


def write_feedstock_resolution_report(
    csv_path: Path = DEFAULT_CSV_REPORT,
    markdown_path: Path = DEFAULT_MARKDOWN_REPORT,
    start_date: str | None = None,
    end_date: str | None = None,
    time_step: str = "monthly",
) -> dict[str, str]:
    """Write read-only feedstock resolution readiness reports."""

    previews = preview_feedstock_resolution_gates(start_date, end_date, time_step)
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    markdown_path.parent.mkdir(parents=True, exist_ok=True)
    _write_csv_report(csv_path, previews)
    _write_markdown_report(markdown_path, previews)
    return {"csv_path": str(csv_path), "markdown_path": str(markdown_path)}


def _preview_from_candidate(
    candidate: FeedstockProxyCandidate,
    grid: tuple[TimeGridStep, ...],
    time_step: str,
) -> FeedstockResolutionPreview:
    seasonal_class = _seasonal_class(candidate.parameter_id)
    time_basis = _time_basis(candidate, seasonal_class, time_step)
    applicable_months = _applicable_months(grid, seasonal_class)
    category = _resolution_category(candidate, seasonal_class, applicable_months)
    return FeedstockResolutionPreview(
        canonical_field=candidate.canonical_field,
        category=category,
        source_file=candidate.source_file,
        parameter_id=candidate.parameter_id,
        time_basis=time_basis,
        applicable_months=applicable_months,
        seasonal_class=seasonal_class,
        no_interpolation=True,
        candidate_readiness=candidate.readiness_category,
        can_activate_by_default=candidate.can_activate_by_default,
        requires_user_selection=candidate.requires_user_selection,
        requires_equation_mapping=candidate.requires_equation_mapping,
        requires_basis_conversion=candidate.requires_basis_conversion,
        source_priority=candidate.source_priority,
        value=candidate.value,
        unit=candidate.unit,
        value_min=candidate.value_min,
        value_max=candidate.value_max,
        evidence_quality=candidate.evidence_quality,
        direct_or_indirect=candidate.direct_or_indirect,
        blocked_reason=_blocked_reason(category),
        doi_or_url=candidate.doi_or_url,
        limitation_note=candidate.limitation_note,
    )


def _validate_measured_override(
    override: MeasuredFeedstockOverride,
    candidates: list[FeedstockProxyCandidate],
) -> dict[str, object]:
    basis = validate_feedstock_candidate_basis(override.canonical_field, override.unit, override.value)
    expected_unit = str(basis["expected_unit"]) or _expected_unit(override.canonical_field, candidates)
    policy = can_convert_feedstock_unit(override.unit, expected_unit, override.canonical_field)
    warnings = []
    if not override.source_id and not override.lab_reference:
        warnings.append("missing_source_or_lab_reference")
    if basis["basis_status"] in {"requires_basis_conversion", "blocked_wrong_basis", "blocked_no_equation_mapping"}:
        return {
            "canonical_field": override.canonical_field,
            "resolution_status": basis["basis_status"],
            "blocked_reason": "unit_mismatch"
            if basis["basis_status"] == "requires_basis_conversion"
            else basis["blocked_reason"],
            "expected_unit": expected_unit,
            "observed_unit": basis["observed_unit"],
            "unit": override.unit,
            "conversion_policy_status": policy["conversion_policy_status"],
            "conversion_required": policy["conversion_required"],
            "conversion_allowed": policy["conversion_allowed"],
            "conversion_note": policy["conversion_note"],
            "warnings": warnings,
        }
    return {
        "canonical_field": override.canonical_field,
        "resolution_status": "measured_project_data",
        "blocked_reason": "",
        "expected_unit": expected_unit,
        "observed_unit": basis["observed_unit"],
        "unit": override.unit,
        "conversion_policy_status": policy["conversion_policy_status"],
        "conversion_required": policy["conversion_required"],
        "conversion_allowed": policy["conversion_allowed"],
        "conversion_note": policy["conversion_note"],
        "warnings": warnings,
    }


def _expected_unit(canonical_field: str, candidates: list[FeedstockProxyCandidate]) -> str:
    for item in sorted(candidates, key=lambda candidate: (candidate.source_priority, candidate.parameter_id)):
        if item.canonical_field == canonical_field and item.unit:
            return item.unit
    return ""


def _display_expected_unit(expected_units: tuple[str, ...]) -> str:
    return " or ".join(expected_units)


def _normalize_unit(unit: str | None) -> str:
    return " ".join(str(unit or "").strip().split())


def _candidate_equation_id(candidate: FeedstockProxyCandidate) -> str:
    row = _candidate_source_row(candidate)
    return row.get("equation_id", "") if row else ""


def _candidate_source_row(candidate: FeedstockProxyCandidate) -> dict[str, str]:
    path = FEEDSTOCK_DATA_DIR / candidate.source_file
    if not path.exists():
        return {}
    for row in _read_csv_rows(path):
        if row.get("parameter_id", "") == candidate.parameter_id:
            return row
    return {}


def _feedstock_equation_registry_ids() -> set[str]:
    if not FEEDSTOCK_EQUATION_REGISTRY.exists():
        return set()
    return {row.get("equation_id", "") for row in _read_csv_rows(FEEDSTOCK_EQUATION_REGISTRY) if row.get("equation_id", "")}


def _read_csv_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def _feedstock_proxy_report_row(item: FeedstockProxyValue) -> dict[str, object]:
    return {
        "canonical_field": item.canonical_field,
        "value": item.value,
        "unit": item.unit,
        "equation_id": "",
        "source_parameter_id": item.parameter_id,
        "status": item.status,
        "activation_status": "report_only",
        "provenance": {
            "mode": "report_only",
            "source_file": item.source_file,
            "direct_or_indirect": item.direct_or_indirect,
            "notes": item.notes,
        },
    }


def _typed_equation_ids() -> set[str]:
    try:
        from Greenhub.scientific_equations import EQUATION_REGISTRY
    except Exception:
        return set()
    return set(EQUATION_REGISTRY)


def _typed_equation_activation_statuses() -> dict[str, str]:
    try:
        from Greenhub.scientific_equations import EQUATION_REGISTRY
    except Exception:
        return {}
    return {equation_id: definition.activation_status for equation_id, definition in EQUATION_REGISTRY.items()}


def _global_feedstock_audit_rows() -> list[dict[str, str]]:
    if not GLOBAL_EQUATION_ACTIVATION_REGISTRY.exists():
        return []
    rows = _read_csv_rows(GLOBAL_EQUATION_ACTIVATION_REGISTRY)
    return [
        row
        for row in rows
        if row.get("dataset_group", "") in {"Feedstock", "Feed BMP"}
        or row.get("dataset_path", "").startswith("Pre-treatment/Feedstock/")
        or row.get("dataset_path", "").startswith("Bigas production + upgrade/Feed BMP/")
    ]


def _queue_item_from_feedstock_registry_row(
    row: dict[str, str],
    typed_ids: set[str],
    typed_activation: dict[str, str],
    audit_by_id: dict[tuple[str, str], dict[str, str]],
) -> dict[str, object]:
    audit = audit_by_id.get(("Feedstock", row.get("equation_id", "")), {})
    status, blocked_reason, next_action = _classify_feedstock_registry_equation(row, typed_ids, audit)
    return {
        "equation_id": row.get("equation_id", ""),
        "canonical_field": _canonical_field_from_equation_output(row.get("dependent_variable", "")),
        "source_file": "Pre-treatment/Feedstock/equation_registry.csv",
        "required_inputs": _split_symbols(row.get("independent_variables", "")),
        "output_field": row.get("dependent_variable", ""),
        "equation_text": row.get("python_expression", "") or row.get("exact_source_equation", ""),
        "source_or_doi": row.get("doi_or_stable_identifier", "") or row.get("source_id", ""),
        "activation_status": typed_activation.get(row.get("equation_id", ""), "reference_only"),
        "implementation_status": status,
        "blocked_reason": blocked_reason,
        "recommended_next_action": next_action,
    }


def _queue_item_from_data_equation_row(
    row: dict[str, str],
    source_file: str,
    typed_ids: set[str],
    typed_activation: dict[str, str],
) -> dict[str, object]:
    status, blocked_reason, next_action = _classify_data_equation_row(row, typed_ids)
    return {
        "equation_id": row.get("equation_id", ""),
        "canonical_field": _canonical_field_from_parameter_id(row.get("parameter_id", "")),
        "source_file": source_file,
        "required_inputs": _split_symbols(row.get("calculation_inputs", "")),
        "output_field": row.get("parameter_id", ""),
        "equation_text": row.get("equation", "") or row.get("calculation_method", ""),
        "source_or_doi": row.get("doi", "") or row.get("url", "") or row.get("source_title", ""),
        "activation_status": typed_activation.get(row.get("equation_id", ""), "reference_only"),
        "implementation_status": status,
        "blocked_reason": blocked_reason,
        "recommended_next_action": next_action,
    }


def _queue_item_from_global_audit_row(
    row: dict[str, str],
    typed_ids: set[str],
    typed_activation: dict[str, str],
) -> dict[str, object]:
    status, blocked_reason, next_action = _classify_global_audit_equation(row, typed_ids)
    return {
        "equation_id": row.get("equation_id", ""),
        "canonical_field": _canonical_field_from_equation_output(row.get("equation_name", "")),
        "source_file": row.get("dataset_path", ""),
        "required_inputs": _split_symbols(row.get("likely_missing_inputs", "")),
        "output_field": row.get("equation_name", ""),
        "equation_text": row.get("equation_name", ""),
        "source_or_doi": row.get("source_title", "") or row.get("source_id", ""),
        "activation_status": typed_activation.get(
            row.get("equation_id", ""),
            "active" if row.get("active", "") == "True" else "reference_only",
        ),
        "implementation_status": status,
        "blocked_reason": blocked_reason,
        "recommended_next_action": next_action,
    }


def _classify_feedstock_registry_equation(
    row: dict[str, str],
    typed_ids: set[str],
    audit: dict[str, str],
) -> tuple[str, str, str]:
    equation_id = row.get("equation_id", "")
    if equation_id in typed_ids:
        return "implemented_typed", "", "Keep typed implementation under existing activation tests."
    text = " ".join([row.get("equation_name", ""), row.get("applicability", ""), row.get("limitations", "")]).lower()
    if equation_id == "EQ-CALC-001":
        return "ready_for_typed_implementation", "", "Implement typed wet-basis moisture identity with unit and boundary tests, still report-only."
    if audit and audit.get("integration_eligibility", "") == "blocked":
        if "temperature" in text or "precipitation" in text or "hydrothermal" in text:
            return "blocked_dynamic_model_scope", "weather/time-dependent dynamic feedstock equation", "Define dynamic weather/time inputs and scope before typed implementation."
        return "needs_input_mapping", audit.get("likely_missing_inputs", ""), audit.get("required_action", "")
    if "temperature" in text or "precipitation" in text or "hydrothermal" in text:
        return "blocked_dynamic_model_scope", "weather/time-dependent dynamic feedstock equation", "Define dynamic weather/time inputs and scope before typed implementation."
    return "needs_source_review", "source equation remains reference-only", "Review source equation, dimensions, and target canonical field."


def _classify_data_equation_row(row: dict[str, str], typed_ids: set[str]) -> tuple[str, str, str]:
    equation_id = row.get("equation_id", "")
    if equation_id in typed_ids:
        return "implemented_typed", "", "Keep typed implementation under existing activation tests."
    text = " ".join([equation_id, row.get("parameter_id", ""), row.get("limitation_note", ""), row.get("calculation_method", "")]).lower()
    if row.get("evidence_status", "") == "equation_only":
        return "blocked_missing_inputs", row.get("limitation_note", ""), "Source missing component inputs before typed implementation."
    if "bmp" in text or "gompertz" in text or "kinetic" in text:
        return "blocked_dynamic_model_scope", "BMP or kinetic equation is outside current feedstock resolver scope.", "Keep as reference until dynamic digestion scope is explicitly designed."
    if "×" in row.get("calculation_method", "") or "mg/l" in row.get("calculation_method", "").lower():
        return "needs_unit_conversion_policy", "calculation depends on explicit unit conversion", "Add reviewed conversion test preserving original and SI values."
    return "needs_source_review", "source equation referenced by data row but not reviewed for typed implementation", "Review equation source, inputs, units, and canonical output."


def _classify_global_audit_equation(row: dict[str, str], typed_ids: set[str]) -> tuple[str, str, str]:
    equation_id = row.get("equation_id", "")
    if equation_id in typed_ids or row.get("typed_implementation_present", "") == "True" and row.get("active", "") == "True":
        return "implemented_typed", "", "Keep typed implementation under existing activation tests."
    group = row.get("dataset_group", "")
    name = row.get("equation_name", "").lower()
    if group == "Feed BMP" and ("gompertz" in name or row.get("integration_eligibility", "") == "blocked"):
        return "blocked_dynamic_model_scope", row.get("activation_reason", ""), "Keep out of feedstock resolution until dynamic digestion scope is designed."
    if row.get("required_inputs_resolved", "") != "True":
        return "needs_input_mapping", row.get("likely_missing_inputs", ""), row.get("required_action", "")
    if row.get("source_complete", "") != "True":
        return "needs_source_review", row.get("activation_reason", ""), row.get("required_action", "")
    return "needs_source_review", "catalogued equation has no approved typed implementation", row.get("required_action", "")


def _split_symbols(text: str) -> tuple[str, ...]:
    cleaned = text.strip()
    if not cleaned or cleaned == "none":
        return ()
    return tuple(item.strip() for item in cleaned.replace(";", ",").split(",") if item.strip())


def _canonical_field_from_parameter_id(parameter_id: str) -> str:
    for candidate in feedstock_proxy_resolution_candidates():
        if candidate.parameter_id == parameter_id:
            return candidate.canonical_field
    return parameter_id


def _canonical_field_from_equation_output(output: str) -> str:
    text = output.casefold()
    if "moisture" in text:
        return "moisture_wet_basis"
    if "cellulose" in text:
        return "cellulose_dry_basis"
    if "hemicellulose" in text:
        return "hemicellulose_dry_basis"
    if "lignin" in text:
        return "lignin_dry_basis"
    if "buswell" in text:
        return "bmp_buswell"
    if "boyle" in text:
        return "bmp_boyle"
    if "fixed carbon" in text:
        return "fixed_carbon_dry_basis"
    return output


def _write_feedstock_equation_queue_report(path: Path, items: list[dict[str, object]]) -> None:
    counts = Counter(str(item["implementation_status"]) for item in items)
    ready = [item for item in items if item["implementation_status"] == "ready_for_typed_implementation"]
    blocked = [item for item in items if str(item["implementation_status"]).startswith("blocked_")]
    lines = [
        "# Feedstock Equation Implementation Queue",
        "",
        "This report is read-only. It does not implement equations, activate parameters, enable dynamic mode, or modify model calculations.",
        "",
        "## Status Counts",
        "",
    ]
    lines.extend(f"- `{status}`: {count}" for status, count in sorted(counts.items()))
    lines.extend(["", "## First Safest Candidate", ""])
    if ready:
        first = sorted(ready, key=lambda item: str(item["equation_id"]))[0]
        lines.append(f"- `{first['equation_id']}` for `{first['canonical_field']}`: {first['recommended_next_action']}")
    else:
        lines.append("- None.")
    lines.extend(["", "## Blocked Or Out Of Scope", ""])
    lines.extend(
        f"- `{item['equation_id']}` (`{item['implementation_status']}`): {item['blocked_reason']}"
        for item in blocked
    )
    lines.extend(["", "## Queue", ""])
    for item in items:
        lines.extend(
            [
                f"### {item['equation_id']}",
                "",
                f"- canonical_field: `{item['canonical_field']}`",
                f"- source_file: `{item['source_file']}`",
                f"- implementation_status: `{item['implementation_status']}`",
                f"- activation_status: `{item['activation_status']}`",
                f"- required_inputs: `{'; '.join(item['required_inputs']) if item['required_inputs'] else 'none'}`",
                f"- output_field: `{item['output_field']}`",
                f"- source_or_doi: `{item['source_or_doi']}`",
                f"- blocked_reason: {item['blocked_reason'] or 'none'}",
                f"- recommended_next_action: {item['recommended_next_action']}",
                "",
            ]
        )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def _expected_unit_options(expected_unit: str) -> tuple[str, ...]:
    return tuple(item.strip() for item in expected_unit.split(" or ") if item.strip())


def _is_equivalent_feedstock_label(observed_key: str, expected_keys: set[str]) -> bool:
    for left, right in FEEDSTOCK_EQUIVALENT_UNIT_LABELS:
        left_key = left.casefold()
        right_key = right.casefold()
        if observed_key == left_key and right_key in expected_keys:
            return True
        if observed_key == right_key and left_key in expected_keys:
            return True
    return False


def _requires_explicit_feedstock_conversion(observed_key: str, expected_keys: set[str]) -> bool:
    expects_fraction = any("kg/kg" in item or "kg vs/kg" in item for item in expected_keys)
    expects_density = "kg/m3" in expected_keys
    if expects_fraction and observed_key in {"%", "percent", "percent dry matter", "% dry matter"}:
        return True
    if expects_fraction and observed_key in {"g/kg", "g/kg dry matter", "g/kg ts"}:
        return True
    if expects_density and observed_key in {"mg/l", "mg/litre", "mg/liter"}:
        return True
    return False


def _resolution_from_measured_override(
    override: MeasuredFeedstockOverride,
    time_label: str,
    validation: dict[str, object],
) -> FeedstockCandidateResolution:
    return FeedstockCandidateResolution(
        canonical_field=override.canonical_field,
        time_label=time_label,
        selected_parameter_id=f"measured:{override.canonical_field}",
        value=float(override.value),
        value_min=None,
        value_max=None,
        unit=override.unit,
        source_priority=0,
        resolution_status="measured_project_data",
        blocked_reason="",
        requires_user_selection=False,
        basis_status="basis_ok",
        expected_unit=str(validation.get("expected_unit", "")),
        observed_unit=override.unit,
        requires_basis_conversion=False,
        conversion_policy_status="allowed_exact_unit",
        conversion_required=bool(validation.get("conversion_required", False)),
        conversion_allowed=bool(validation.get("conversion_allowed", True)),
        conversion_note=str(validation.get("conversion_note", "Exact expected unit; no conversion is required.")),
        equation_mapping_status="no_equation_required_observed_value",
        equation_id="",
        equation_note="Measured project value; no equation is required in the report-only resolver.",
        provenance={
            "mode": "report_only",
            "source_kind": "measured_project_data",
            "source_id": override.source_id,
            "lab_reference": override.lab_reference,
            "notes": override.notes,
            "warnings": tuple(validation.get("warnings", ())),
        },
    )


def _candidate_may_resolve(candidate: FeedstockProxyCandidate, allow_indirect: bool) -> bool:
    if candidate.readiness_category in {"project_data_ready", "direct_literature_proxy", "fallback_literature_proxy"}:
        return True
    return candidate.readiness_category == "sensitivity_only_indirect_proxy" and allow_indirect


def _time_blocked(candidate: FeedstockProxyCandidate, time_label: str) -> bool:
    seasonal_class = _seasonal_class(candidate.parameter_id)
    if seasonal_class is None:
        return False
    month = _month_from_time_label(time_label)
    if month is None:
        return True
    months = {
        "spring": {"03", "04", "05"},
        "summer": {"06", "07", "08"},
        "autumn": {"09", "10", "11"},
    }[seasonal_class]
    return month not in months


def _month_from_time_label(time_label: str) -> str | None:
    if len(time_label) >= 7 and time_label[4] == "-":
        month = time_label[5:7]
        if month.isdigit():
            return month
    return None


def _resolution_from_candidate(
    candidate: FeedstockProxyCandidate,
    time_label: str,
    status: str,
    blocked_reason: str,
    requires_user_selection: bool,
) -> FeedstockCandidateResolution:
    basis = validate_feedstock_candidate_basis(candidate.canonical_field, candidate.unit, candidate.value)
    equation = validate_feedstock_equation_mapping(candidate)
    policy = can_convert_feedstock_unit(
        candidate.unit,
        str(basis["expected_unit"]),
        candidate.canonical_field,
        value_min=candidate.value_min,
        value_max=candidate.value_max,
    )
    basis_status = str(basis["basis_status"])
    final_status = "blocked_wrong_basis" if basis_status == "blocked_wrong_basis" else status
    final_blocked_reason = str(basis["blocked_reason"]) if basis_status == "blocked_wrong_basis" else blocked_reason
    blocked = final_status.startswith("blocked_") or final_status == "requires_user_selection"
    return FeedstockCandidateResolution(
        canonical_field=candidate.canonical_field,
        time_label=time_label,
        selected_parameter_id=None if blocked else candidate.parameter_id,
        value=None if blocked else candidate.value,
        value_min=None if blocked else candidate.value_min,
        value_max=None if blocked else candidate.value_max,
        unit=candidate.unit,
        source_priority=candidate.source_priority,
        resolution_status=final_status,
        blocked_reason=final_blocked_reason,
        requires_user_selection=requires_user_selection or blocked,
        basis_status=basis_status,
        expected_unit=str(basis["expected_unit"]),
        observed_unit=str(basis["observed_unit"]),
        requires_basis_conversion=bool(basis["requires_basis_conversion"]),
        conversion_policy_status=str(policy["conversion_policy_status"]),
        conversion_required=bool(policy["conversion_required"]),
        conversion_allowed=bool(policy["conversion_allowed"]),
        conversion_note=str(policy["conversion_note"]),
        equation_mapping_status=str(equation["equation_mapping_status"]),
        equation_id=str(equation["equation_id"]),
        equation_note=str(equation["equation_note"]),
        provenance={
            "mode": "report_only",
            "source_file": candidate.source_file,
            "source_title": candidate.source_title,
            "doi_or_url": candidate.doi_or_url,
            "evidence_quality": candidate.evidence_quality,
            "direct_or_indirect": candidate.direct_or_indirect,
            "readiness_category": candidate.readiness_category,
            "limitation_note": candidate.limitation_note,
        },
    )


def _blocked_resolution(
    canonical_field: str,
    time_label: str,
    status: str,
    blocked_reason: str,
    expected_unit: str = "",
    observed_unit: str = "",
    requires_basis_conversion: bool = False,
    conversion_policy_status: str = "",
    conversion_required: bool = False,
    conversion_allowed: bool = False,
    conversion_note: str = "",
    equation_mapping_status: str = "",
    equation_id: str = "",
    equation_note: str = "",
) -> FeedstockCandidateResolution:
    return FeedstockCandidateResolution(
        canonical_field=canonical_field,
        time_label=time_label,
        selected_parameter_id=None,
        value=None,
        value_min=None,
        value_max=None,
        unit="",
        source_priority=None,
        resolution_status=status,
        blocked_reason=blocked_reason,
        requires_user_selection=True,
        basis_status=status if status in {"requires_basis_conversion", "blocked_wrong_basis"} else "",
        expected_unit=expected_unit,
        observed_unit=observed_unit,
        requires_basis_conversion=requires_basis_conversion,
        conversion_policy_status=conversion_policy_status,
        conversion_required=conversion_required,
        conversion_allowed=conversion_allowed,
        conversion_note=conversion_note,
        equation_mapping_status=equation_mapping_status,
        equation_id=equation_id,
        equation_note=equation_note,
        provenance={"mode": "report_only"},
    )


def _write_csv_report(path: Path, previews: list[FeedstockResolutionPreview]) -> None:
    columns = [
        "canonical_field",
        "parameter_id",
        "resolution_status",
        "time_basis",
        "applicable_time_labels",
        "source_priority",
        "source_file",
        "value",
        "unit",
        "value_min",
        "value_max",
        "evidence_quality",
        "direct_or_indirect",
        "requires_user_selection",
        "requires_equation_mapping",
        "requires_basis_conversion",
        "blocked_reason",
        "doi_or_url",
        "limitation_note",
    ]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns)
        writer.writeheader()
        for item in previews:
            writer.writerow(
                {
                    "canonical_field": item.canonical_field,
                    "parameter_id": item.parameter_id,
                    "resolution_status": item.category,
                    "time_basis": item.time_basis,
                    "applicable_time_labels": ";".join(item.applicable_months),
                    "source_priority": item.source_priority,
                    "source_file": item.source_file,
                    "value": "" if item.value is None else item.value,
                    "unit": item.unit,
                    "value_min": "" if item.value_min is None else item.value_min,
                    "value_max": "" if item.value_max is None else item.value_max,
                    "evidence_quality": item.evidence_quality,
                    "direct_or_indirect": item.direct_or_indirect,
                    "requires_user_selection": item.requires_user_selection,
                    "requires_equation_mapping": item.requires_equation_mapping,
                    "requires_basis_conversion": item.requires_basis_conversion,
                    "blocked_reason": item.blocked_reason,
                    "doi_or_url": item.doi_or_url,
                    "limitation_note": item.limitation_note,
                }
            )


def _write_markdown_report(path: Path, previews: list[FeedstockResolutionPreview]) -> None:
    counts = Counter(item.category for item in previews)
    resolvable = sorted({item.canonical_field for item in previews if item.category == "resolvable_now"})
    blocked = sorted({item.canonical_field for item in previews if item.category.startswith("blocked_")})
    user_selection = sorted({item.canonical_field for item in previews if item.category == "requires_user_selection"})
    lines = [
        "# Feedstock Resolution Readiness",
        "",
        "This report is read-only. It does not activate calculations, enable dynamic resolution, or interpolate seasonal data.",
        "",
        "## Category Counts",
        "",
    ]
    lines.extend(f"- `{category}`: {count}" for category, count in sorted(counts.items()))
    lines.extend(
        [
            "",
            "## Resolvable Fields",
            "",
        ]
    )
    lines.extend(f"- `{field}`" for field in resolvable)
    lines.extend(
        [
            "",
            "## Blocked Fields",
            "",
        ]
    )
    lines.extend(f"- `{field}`" for field in blocked)
    lines.extend(
        [
            "",
            "## User-Selection-Only Fields",
            "",
        ]
    )
    lines.extend(f"- `{field}`" for field in user_selection)
    lines.extend(
        [
            "",
            "## Override Rule",
            "",
            "Actual measured GreenHub data overrides every proxy candidate, including direct literature rows.",
            "",
            "## Activation Rule",
            "",
            "No candidate in this report is consumed by model calculations. Seasonal data are not interpolated by default.",
            "",
        ]
    )
    path.write_text("\n".join(lines), encoding="utf-8")


def _resolution_category(
    candidate: FeedstockProxyCandidate,
    seasonal_class: str | None,
    applicable_months: tuple[str, ...],
) -> str:
    if candidate.readiness_category == "blocked_missing":
        return "blocked_missing"
    if candidate.readiness_category == "blocked_wrong_basis":
        return "blocked_wrong_basis"
    if candidate.readiness_category == "blocked_no_equation_mapping":
        return "blocked_no_equation_mapping"
    if seasonal_class is not None and not applicable_months:
        return "blocked_time_mapping"
    if candidate.can_activate_by_default:
        return "resolvable_now"
    return "requires_user_selection"


def _blocked_reason(category: str) -> str:
    reasons = {
        "blocked_missing": "missing_value",
        "blocked_wrong_basis": "wrong_or_unclear_basis",
        "blocked_no_equation_mapping": "no_equation_mapping",
        "blocked_time_mapping": "no_time_grid_overlap",
    }
    return reasons.get(category, "")


def _time_basis(candidate: FeedstockProxyCandidate, seasonal_class: str | None, time_step: str) -> str:
    if seasonal_class is not None or candidate.source_file == "seasonal_feed_variability.csv":
        return "monthly" if time_step == "monthly" else "daily"
    return "static"


def _seasonal_class(parameter_id: str) -> str | None:
    upper = parameter_id.upper()
    if "-SP-" in upper:
        return "spring"
    if "-SU-" in upper:
        return "summer"
    if "-AU-" in upper:
        return "autumn"
    return None


def _applicable_months(grid: tuple[TimeGridStep, ...], seasonal_class: str | None) -> tuple[str, ...]:
    if seasonal_class is None:
        return tuple(step.label for step in grid)
    month_numbers = {
        "spring": {"03", "04", "05"},
        "summer": {"06", "07", "08"},
        "autumn": {"09", "10", "11"},
    }[seasonal_class]
    labels = []
    for step in grid:
        month = step.start_date[5:7]
        if month in month_numbers:
            labels.append(step.label)
    return tuple(labels)
