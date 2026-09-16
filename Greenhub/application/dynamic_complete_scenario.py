"""Dashboard contract and calendar-aware biomass supply; no empirical model imports."""
from __future__ import annotations

import calendar
import math
from dataclasses import asdict, dataclass, fields
from datetime import date, timedelta

PROTEIN_METHODS = ("isoelectric", "lactic_acid", "membrane", "heat", "generic")
DRYING_METHODS = ("mass_only", "spray_drying_proxy", "freeze_drying_proxy")
GAS_ROUTES = ("none", "common_conditioning", "membrane", "psa", "water_scrubbing", "mea", "chp_utilities")
RESOURCE_METHODS = ("digestate_separation", "ammonia_recovery", "phosphorus_recovery", "potassium_water_concentration", "ion_exchange")


@dataclass(frozen=True)
class DynamicCompleteScenario:
    annual_available_biomass_tonnes: float = 30000.0
    annual_processed_biomass_tonnes: float = 30000.0
    collection_refinery_fraction: float = 1.0
    feed_basis: str = "tonnes_per_year"
    feed_kg_per_hr: float = 1000.0
    season_start: str = "2026-04-15"
    season_end: str = "2026-11-15"
    peak_date: str = "2026-07-31"
    spread_days: float = 55.0
    full_year: bool = False
    active_months: tuple[int, ...] = tuple(range(1, 13))
    annualize: bool = False
    protein_method: str = "isoelectric"
    protein_recovery_fraction: float | None = None
    drying_method: str = "spray_drying_proxy"
    target_product_moisture: float = 0.15
    gas_route: str = "water_scrubbing"
    resource_recovery_methods: tuple[str, ...] = RESOURCE_METHODS
    allow_assumptions: bool = True
    show_strict_mode_blockers: bool = True
    include_press_cake_in_ad: bool = False

    def __post_init__(self):
        for name in ("full_year", "annualize", "allow_assumptions", "show_strict_mode_blockers", "include_press_cake_in_ad"):
            if type(getattr(self, name)) is not bool:
                raise ValueError(f"{name} must be true or false.")
        for name in ("annual_available_biomass_tonnes", "annual_processed_biomass_tonnes", "collection_refinery_fraction", "feed_kg_per_hr", "spread_days", "target_product_moisture", "protein_recovery_fraction"):
            value = getattr(self, name)
            if value is None and name == "protein_recovery_fraction":
                continue
            if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or value < 0:
                raise ValueError(f"{name} must be a finite non-negative number.")
        if not 1 <= self.spread_days <= 366:
            raise ValueError("spread_days must be between 1 and 366.")
        if self.collection_refinery_fraction > 1 or self.target_product_moisture >= 1:
            raise ValueError("Collection fraction must be in [0, 1]; product moisture must be in [0, 1).")
        if self.protein_recovery_fraction is not None and self.protein_recovery_fraction > 1:
            raise ValueError("protein_recovery_fraction must be in [0, 1].")
        for name, choices in (("feed_basis", ("kg_per_hr", "tonnes_per_year")), ("protein_method", PROTEIN_METHODS), ("drying_method", DRYING_METHODS), ("gas_route", GAS_ROUTES)):
            if getattr(self, name) not in choices:
                raise ValueError(f"Select exactly one {name}: {', '.join(choices)}.")
        if self.protein_method in ("generic", "heat") and self.protein_recovery_fraction is None:
            raise ValueError("Heat and generic protein methods require an explicit protein_recovery_fraction in [0, 1].")
        if self.include_press_cake_in_ad:
            raise ValueError("Press cake is an external product and cannot enter AD.")
        if not isinstance(self.active_months, (tuple, list)) or any(type(m) is not int or m not in range(1, 13) for m in self.active_months) or len(set(self.active_months)) != len(self.active_months):
            raise ValueError("active_months must contain unique month numbers from 1 to 12.")
        if not isinstance(self.resource_recovery_methods, (tuple, list)) or any(m not in RESOURCE_METHODS for m in self.resource_recovery_methods) or len(set(self.resource_recovery_methods)) != len(self.resource_recovery_methods):
            raise ValueError("Select unique supported resource recovery methods.")
        object.__setattr__(self, "active_months", tuple(sorted(self.active_months)))
        object.__setattr__(self, "resource_recovery_methods", tuple(m for m in RESOURCE_METHODS if m in self.resource_recovery_methods))
        try:
            start, end, peak = map(date.fromisoformat, (self.season_start, self.season_end, self.peak_date))
        except (TypeError, ValueError) as exc:
            raise ValueError("Season and peak dates must use YYYY-MM-DD.") from exc
        if start.year != end.year or end < start or not 2000 <= start.year <= 2100:
            raise ValueError("The season must be ordered within one calendar year (2000–2100).")
        if peak.year != start.year or (not self.full_year and not start <= peak <= end):
            raise ValueError("peak_date must fall within the collection season.")

    @classmethod
    def from_dict(cls, payload):
        if not isinstance(payload, dict):
            raise ValueError("Scenario must be a JSON object.")
        unknown = set(payload) - {f.name for f in fields(cls)}
        if unknown:
            raise ValueError(f"Unknown scenario fields: {', '.join(sorted(unknown))}.")
        return cls(**payload)

    def to_dict(self):
        return asdict(self)


def build_biomass_schedule(config: DynamicCompleteScenario) -> dict:
    """Integrate a truncated normal, then cap processing without rescaling supply.

    Annual input mode solves a common monthly tonnage ceiling. Hourly mode
    imposes an operating-hour capacity as well. Dates are inclusive; no storage.
    """
    year = date.fromisoformat(config.season_start).year
    start = date(year, 1, 1) if config.full_year else date.fromisoformat(config.season_start)
    end = date(year, 12, 31) if config.full_year else date.fromisoformat(config.season_end)
    peak = date.fromisoformat(config.peak_date)
    def cdf(day):
        return 0.5 * (1 + math.erf((day - peak).days / (config.spread_days * math.sqrt(2))))
    denominator = cdf(end + timedelta(days=1)) - cdf(start)
    rows = []
    for month in range(1, 13):
        days = calendar.monthrange(year, month)[1]
        left, right = max(start, date(year, month, 1)), min(end, date(year, month, days))
        season_days = max(0, (right - left).days + 1)
        available = config.annual_available_biomass_tonnes * (cdf(right + timedelta(days=1)) - cdf(left)) / denominator if season_days else 0.0
        hours = season_days * 24 if month in config.active_months else 0
        capacity = min(available, config.feed_kg_per_hr * hours / 1000) if config.feed_basis == "kg_per_hr" else available
        rows.append(dict(time_label=f"{year}-{month:02d}", calendar_hours=days * 24,
                         operating_hours=hours, available_biomass_tonnes=available,
                         capacity=capacity if hours else 0.0))
    requested = min(config.annual_processed_biomass_tonnes, config.annual_available_biomass_tonnes * config.collection_refinery_fraction)
    target = min(requested, sum(r["capacity"] for r in rows))
    lo, hi = 0.0, max((r["capacity"] for r in rows), default=0.0)
    for _ in range(80):
        mid = (lo + hi) / 2
        if sum(min(r["capacity"], mid) for r in rows) < target:
            lo = mid
        else:
            hi = mid
    for row in rows:
        processed = min(row.pop("capacity"), hi)
        available, hours = row["available_biomass_tonnes"], row["operating_hours"]
        row.update(processed_biomass_tonnes=processed, unused_biomass_tonnes=max(0, available - processed),
                   utilization_fraction=processed / available if available else 0.0,
                   basis_feed_kg_per_hr=processed * 1000 / hours if hours else 0.0)
    processed = sum(r["processed_biomass_tonnes"] for r in rows)
    available = sum(r["available_biomass_tonnes"] for r in rows)
    return dict(monthly=rows, annual_available_tonnes=available, annual_processed_tonnes=processed,
                annual_unused_tonnes=max(0, available - processed), requested_processed_tonnes=requested,
                unmet_target_tonnes=max(0, requested - processed), monthly_processing_cap_tonnes=hi,
                utilization_fraction=processed / available if available else 0.0,
                peak_month_processed_tonnes=max(r["processed_biomass_tonnes"] for r in rows),
                peak_throughput_kg_per_hr=max(r["basis_feed_kg_per_hr"] for r in rows))


def scenario_options():
    return {"defaults": DynamicCompleteScenario().to_dict(), "protein_methods": PROTEIN_METHODS,
            "drying_methods": DRYING_METHODS, "gas_routes": GAS_ROUTES,
            "resource_recovery_methods": RESOURCE_METHODS,
            "validated_simulation_ready": False, "mode": "opt_in_complete_biosteam_proxy"}
