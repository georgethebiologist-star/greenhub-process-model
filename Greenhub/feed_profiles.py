"""Validated time-dependent feed profiles without weather or growth inference."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from math import isfinite
from pathlib import Path
from typing import Iterable

import pandas as pd

from Greenhub.input_data import INPUT_WORKBOOK_PATH
from Greenhub.phase3_inputs import GRASS_AVAILABILITY_SHEET
from Greenhub.time_grid import TimeGridStep


@dataclass(frozen=True)
class FeedProfilePoint:
    period: str
    available_wet_biomass_kg: float | None = None
    normalized_weight: float | None = None
    collection_fraction: float = 1.0
    moisture_fraction: float | None = None
    component_mass_fractions: dict[str, float] = field(default_factory=dict)
    temperature_k: float | None = None
    source: str = "user_supplied"
    provenance: str | None = None
    warnings: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        numbers = (
            self.available_wet_biomass_kg,
            self.normalized_weight,
            self.collection_fraction,
            self.moisture_fraction,
            self.temperature_k,
            *self.component_mass_fractions.values(),
        )
        if any(value is not None and not isfinite(float(value)) for value in numbers):
            raise ValueError("Feed profile values must be finite or null.")
        if self.available_wet_biomass_kg is not None and self.available_wet_biomass_kg < 0.0:
            raise ValueError("available_wet_biomass_kg must be non-negative.")
        if self.normalized_weight is not None and self.normalized_weight < 0.0:
            raise ValueError("normalized_weight must be non-negative.")
        if not 0.0 <= self.collection_fraction <= 1.0:
            raise ValueError("collection_fraction must be within [0, 1].")
        if self.moisture_fraction is not None and not 0.0 <= self.moisture_fraction <= 1.0:
            raise ValueError("moisture_fraction must be within [0, 1].")
        if self.temperature_k is not None and self.temperature_k <= 0.0:
            raise ValueError("temperature_k must be greater than zero when supplied.")
        if any(value < 0.0 for value in self.component_mass_fractions.values()):
            raise ValueError("Component mass fractions must be non-negative.")
        if sum(self.component_mass_fractions.values()) > 1.0 + 1e-12:
            raise ValueError("Component mass fractions cannot sum above one.")


@dataclass(frozen=True)
class FeedProfile:
    profile_id: str
    display_name: str
    resolution: str
    normalized: bool
    points: tuple[FeedProfilePoint, ...]
    source: str
    provenance: str
    warnings: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not self.profile_id or self.resolution not in {"monthly", "daily"}:
            raise ValueError("Feed profiles require an ID and monthly or daily resolution.")
        periods = [item.period.casefold() for item in self.points]
        if len(periods) != len(set(periods)):
            raise ValueError(f"Feed profile '{self.profile_id}' contains duplicate periods.")
        if self.normalized and not any((item.normalized_weight or 0.0) > 0.0 for item in self.points):
            raise ValueError("A normalized feed profile requires at least one positive weight.")

    def metadata(self) -> dict[str, object]:
        return {
            "profile_id": self.profile_id,
            "display_name": self.display_name,
            "resolution": self.resolution,
            "normalized": self.normalized,
            "source": self.source,
            "provenance": self.provenance,
            "point_count": len(self.points),
            "warnings": self.warnings,
        }


def load_feed_profile_csv(path: Path, profile_id: str, *, normalized: bool = False) -> FeedProfile:
    """Load an explicit CSV profile; no interpolation or weather relation is applied."""

    table = pd.read_csv(path)
    if "period" not in table:
        raise ValueError("Feed profile CSV requires a 'period' column.")
    component_columns = [name for name in table if name.startswith("component_fraction:")]
    points = []
    for _, row in table.iterrows():
        points.append(
            FeedProfilePoint(
                period=str(row["period"]),
                available_wet_biomass_kg=_optional_number(row.get("available_wet_biomass_kg")),
                normalized_weight=_optional_number(row.get("normalized_weight")),
                collection_fraction=(
                    1.0
                    if _optional_number(row.get("collection_fraction")) is None
                    else float(row.get("collection_fraction"))
                ),
                moisture_fraction=_optional_number(row.get("moisture_fraction")),
                component_mass_fractions={
                    name.split(":", 1)[1]: float(row[name])
                    for name in component_columns
                    if _optional_number(row.get(name)) is not None
                },
                temperature_k=_optional_number(row.get("temperature_k")),
                source=str(row.get("source") or "csv_user_profile"),
                provenance=str(row.get("provenance") or path.name),
            )
        )
    resolution = _infer_resolution(item.period for item in points)
    return FeedProfile(profile_id, profile_id, resolution, normalized, tuple(points), "csv", path.name)


def load_workbook_feed_profiles(path: Path = INPUT_WORKBOOK_PATH) -> tuple[FeedProfile, ...]:
    """Expose direct and normalized monthly profiles from the existing workbook."""

    table = pd.read_excel(path, sheet_name=GRASS_AVAILABILITY_SHEET)
    rows = table[table["sample_id"].astype(str).str.casefold().eq("grass_baseline")]
    points = []
    for _, row in rows.iterrows():
        mass = _optional_number(row.get("total_wet_grass_mass_kg"))
        if mass is None:
            continue
        points.append(
            FeedProfilePoint(
                period=str(row["month"]),
                available_wet_biomass_kg=mass,
                normalized_weight=mass,
                source="GreenHub master input workbook",
                provenance=f"{GRASS_AVAILABILITY_SHEET}:{row.get('month')}",
                warnings=("Composition and temperature are resolved from workbook characterization at run time.",),
            )
        )
    direct = FeedProfile(
        "workbook_default", "Workbook monthly grass availability", "monthly", False,
        tuple(points), "GreenHub master input workbook", GRASS_AVAILABILITY_SHEET,
    )
    normalized = FeedProfile(
        "workbook_normalized", "Normalized workbook seasonal profile", "monthly", True,
        tuple(points), "GreenHub master input workbook", GRASS_AVAILABILITY_SHEET,
        ("Weights are scaled only to an explicit annual_biomass_target.",),
    )
    return direct, normalized


def resolve_feed_profile(
    profile: FeedProfile,
    grid: tuple[TimeGridStep, ...],
    annual_biomass_target: float | None,
) -> tuple[dict[str, object], ...]:
    """Resolve profile points onto a matching grid and optionally scale weights."""

    if profile.resolution != ("daily" if all(item.duration_days == 1 for item in grid) else "monthly"):
        raise ValueError(
            f"Profile '{profile.profile_id}' has {profile.resolution} data and cannot drive this grid without interpolation."
        )
    matches = []
    by_period = {item.period.casefold(): item for item in profile.points}
    month_lookup = (
        {_month_key(item.period): item for item in profile.points if not _has_explicit_year(item.period)}
        if profile.resolution == "monthly" else {}
    )
    for step in grid:
        if profile.resolution == "daily":
            point = by_period.get(step.start_date.casefold())
        else:
            month_name = date.fromisoformat(step.start_date).strftime("%B").casefold()
            point = (
                by_period.get(step.label.casefold())
                or by_period.get(step.start_date.casefold())
                or month_lookup.get(month_name)
            )
        matches.append(point)
    if profile.normalized:
        if annual_biomass_target is None:
            raise ValueError(f"Normalized profile '{profile.profile_id}' requires annual_biomass_target.")
        denominator = sum((item.normalized_weight or 0.0) for item in matches if item is not None)
        if denominator <= 0.0:
            raise ValueError("Selected horizon contains no positive normalized feed weights.")
    else:
        denominator = 1.0
    records = []
    for step, point in zip(grid, matches):
        warnings = [] if point is not None else ["No feed-supply point is available for this time step; zero feed was used."]
        if point is None:
            available = 0.0
            collection = 1.0
            moisture = temperature = None
            components = {}
            source = profile.source
            provenance = profile.provenance
        else:
            available = (
                annual_biomass_target * (point.normalized_weight or 0.0) / denominator
                if profile.normalized else (point.available_wet_biomass_kg or 0.0)
            )
            collection = point.collection_fraction
            moisture = point.moisture_fraction
            temperature = point.temperature_k
            components = dict(point.component_mass_fractions)
            source = point.source
            provenance = point.provenance
            warnings.extend(point.warnings)
        records.append({
            "time": step.label,
            "start_date": step.start_date,
            "available_wet_biomass_kg": float(available),
            "collected_biomass_kg": float(available * collection),
            "uncollected_biomass_kg": float(available * (1.0 - collection)),
            "moisture_fraction": moisture,
            "dry_matter_kg": None if moisture is None else float(available * (1.0 - moisture)),
            "component_mass_fractions": components,
            "temperature_k": temperature,
            "source": source,
            "provenance": provenance,
            "warnings": tuple(warnings),
        })
    return tuple(records)


def feed_profile_from_mapping(payload: dict[str, object]) -> FeedProfile:
    points = tuple(
        FeedProfilePoint(
            period=str(item["period"]),
            available_wet_biomass_kg=item.get("available_wet_biomass_kg"),
            normalized_weight=item.get("normalized_weight"),
            collection_fraction=item.get("collection_fraction", 1.0),
            moisture_fraction=item.get("moisture_fraction"),
            component_mass_fractions=dict(item.get("component_mass_fractions", {})),
            temperature_k=item.get("temperature_k"),
            source=str(item.get("source", "api_user_profile")),
            provenance=item.get("provenance"),
            warnings=tuple(item.get("warnings", ())),
        )
        for item in payload.get("points", ())
    )
    return FeedProfile(
        profile_id=str(payload.get("profile_id", "")),
        display_name=str(payload.get("display_name") or payload.get("profile_id") or ""),
        resolution=str(payload.get("resolution", "monthly")),
        normalized=bool(payload.get("normalized", False)),
        points=points,
        source="api_user_profile",
        provenance=str(payload.get("provenance") or "API request"),
        warnings=tuple(payload.get("warnings", ())),
    )


def _optional_number(value: object) -> float | None:
    if value is None or pd.isna(value):
        return None
    return float(value)


def _infer_resolution(periods: Iterable[str]) -> str:
    values = tuple(periods)
    if values and all(_is_date(value) for value in values):
        return "daily"
    return "monthly"


def _is_date(value: str) -> bool:
    try:
        date.fromisoformat(value)
    except ValueError:
        return False
    return True


def _month_key(value: str) -> str:
    text = value.strip()
    try:
        parsed = date.fromisoformat(f"{text}-01" if len(text) == 7 else text)
        return parsed.strftime("%B").casefold()
    except ValueError:
        return text.casefold()


def _has_explicit_year(value: str) -> bool:
    text = value.strip()
    try:
        date.fromisoformat(f"{text}-01" if len(text) == 7 else text)
    except ValueError:
        return False
    return True
