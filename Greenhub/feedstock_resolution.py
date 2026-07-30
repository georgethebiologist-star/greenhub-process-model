"""Report-only preview for time-aware feedstock proxy resolution gates."""

from __future__ import annotations

import csv
from collections import Counter
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable

from Greenhub.feedstock_proxy import FeedstockProxyCandidate, feedstock_proxy_resolution_candidates
from Greenhub.time_grid import TimeGridStep, generate_time_grid


PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_CSV_REPORT = PROJECT_ROOT / "Greenhub" / "results" / "feedstock_resolution_gates.csv"
DEFAULT_MARKDOWN_REPORT = PROJECT_ROOT / "docs" / "feedstock_resolution_readiness.md"


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
