"""Post-route life-cycle inventory and climate characterization contracts.

No process state is changed here. Missing activity data or factors stay missing.
Only climate is characterized; nutrient and biogenic-carbon flows remain visible.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, field, fields
import json
import math
from pathlib import Path
from typing import Mapping


METHOD = "IPCC AR6 WGI (2021), Table 7.15, GWP100"
GROUPS = ("electricity", "heat", "materials", "transport", "storage_emissions",
          "process_emissions", "waste", "feedstock_production", "equipment")
DEFAULT_GROUPS = GROUPS[:7]


def nonnegative(value, name):
    if value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or value < 0:
        raise ValueError(f"{name} must be a finite non-negative number or null.")
    return float(value)


@dataclass(frozen=True)
class ClimateFactor:
    factor_id: str
    value: float | None
    quantity_unit: str
    source_status: str
    basis: str
    geography: str
    reference_year: int | None
    source_url: str
    source_table_page: str
    retrieval_date: str
    evidence_class: str
    applicability: str
    conversion_method: str
    uncertainty: str
    method: str = METHOD
    warning: str = ""

    def __post_init__(self):
        nonnegative(self.value, f"Factor {self.factor_id}")
        for name in ("factor_id", "quantity_unit", "source_status", "basis", "geography", "evidence_class",
                     "applicability", "conversion_method", "uncertainty", "method"):
            if not isinstance(getattr(self, name), str) or not getattr(self, name).strip():
                raise ValueError(f"Factor {self.factor_id}: {name} must be explicit.")
        if self.value is not None and self.source_status in ("direct_literature", "official_dataset", "measured") and not self.source_url:
            raise ValueError(f"Sourced factor {self.factor_id} requires a source URL or DOI.")
        if self.value is not None and self.source_status == "missing":
            raise ValueError("A missing factor cannot contain a numeric value.")

    def to_dict(self):
        return {**asdict(self), "unit": f"kg CO2e/{self.quantity_unit}"}


@dataclass(frozen=True)
class InventoryFlow:
    flow_id: str
    group: str
    quantity: float | None
    unit: str
    accounting_key: str
    factor_id: str | None = None
    direction: str = "burden"
    compartment: str = "technosphere"
    source_status: str = "process_output"
    source_id: str = ""
    warning: str = ""
    basis: str = "annual inventory, summed modeled periods; no off-season extrapolation"
    geography: str = "project location"
    reference_year: int | None = None
    source_url: str = ""
    source_table_page: str = ""
    retrieval_date: str = ""
    evidence_class: str = "model_output"
    applicability: str = "this formed process scenario only"
    conversion_method: str = "identity"
    uncertainty: str = "not quantified; inherited process uncertainty"
    counterfactual: str = ""
    quality_verified: bool = False
    available_quantity: float | None = None

    def __post_init__(self):
        nonnegative(self.quantity, self.flow_id)
        nonnegative(self.available_quantity, f"{self.flow_id}.available_quantity")
        if not self.flow_id or not self.accounting_key or not self.unit or not self.source_id:
            raise ValueError("Inventory flow requires flow_id, accounting_key, unit and source_id.")
        if self.group not in GROUPS:
            raise ValueError(f"Unknown inventory group: {self.group}")
        if self.direction not in ("burden", "credit", "memorandum"):
            raise ValueError("Inventory direction must be burden, credit or memorandum.")
        if self.direction == "credit":
            if not self.counterfactual or not self.quality_verified or self.available_quantity is None:
                raise ValueError("Substitution requires counterfactual, verified product quality and available_quantity.")
            if self.quantity is not None and self.quantity > self.available_quantity + 1e-9:
                raise ValueError("Displaced quantity cannot exceed the verified available product quantity.")

    def to_dict(self):
        return asdict(self)


@dataclass(frozen=True)
class LCAProjectBasis:
    location: str = "Netherlands"
    reference_year: int | None = None
    boundary: str = "collection-to-factory-gate climate screening"
    included_groups: tuple[str, ...] = DEFAULT_GROUPS
    exclusions: Mapping[str, str] = field(default_factory=lambda: {
        "feedstock_production": "Cultivation and land-use change excluded from collection-to-gate boundary; no zero-burden claim.",
        "equipment": "Embodied equipment excluded from this operational screening boundary.",
        "product_use_and_end_of_life": "Outside factory gate; no permanent biogenic carbon storage credited.",
    })
    allocation: str = "whole_plant_no_product_allocation"
    operating_hours_per_year: float | None = None
    annual_throughput_kg: float | None = None
    annual_dry_feed_kg: float | None = None
    methane_emitted_fraction: float | None = None
    inventory_completeness: Mapping[str, object] = field(default_factory=dict)
    substitution_enabled: bool = False
    terminal_gas_fate: str = 'unresolved'

    def __post_init__(self):
        if self.terminal_gas_fate not in ('unresolved','emitted'):
            raise ValueError('terminal_gas_fate must be unresolved or emitted (explicit no-flare/no-recovery assumption).')
        for name in ("operating_hours_per_year", "annual_throughput_kg", "annual_dry_feed_kg", "methane_emitted_fraction"):
            nonnegative(getattr(self, name), name)
        if self.operating_hours_per_year is not None and self.operating_hours_per_year > 8784:
            raise ValueError("Annual operating hours cannot exceed a leap calendar year (8784).")
        if self.methane_emitted_fraction is not None and self.methane_emitted_fraction > 1:
            raise ValueError("methane_emitted_fraction must be in [0, 1].")
        if self.annual_dry_feed_kg is not None and self.annual_throughput_kg is not None and self.annual_dry_feed_kg > self.annual_throughput_kg + 1e-9:
            raise ValueError("Annual dry feed cannot exceed annual wet feed.")
        if not self.boundary or self.allocation != "whole_plant_no_product_allocation":
            raise ValueError("Specify boundary; only whole_plant_no_product_allocation is currently supported.")
        if not self.included_groups or set(self.included_groups) - set(GROUPS) or len(set(self.included_groups)) != len(self.included_groups):
            raise ValueError("included_groups must be a non-empty unique selection of supported inventory groups.")
        for group in set(GROUPS) - set(self.included_groups):
            if not self.exclusions.get(group):
                raise ValueError(f"Explicit boundary exclusion rationale required for {group}.")
        if set(self.included_groups) & set(self.exclusions):
            raise ValueError("An inventory group cannot be both included and excluded.")
        for group, declaration in self.inventory_completeness.items():
            if group not in self.included_groups or not isinstance(declaration, Mapping) or declaration.get("status") not in ("complete", "partial", "missing") or not declaration.get("note"):
                raise ValueError("Inventory completeness requires included group -> {status: complete/partial/missing, note: rationale}.")


def load_climate_factors(overrides=None):
    path = Path(__file__).parent / "data" / "lca" / "climate_factors.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    factors = {item["factor_id"]: ClimateFactor(**item) for item in data["factors"]}
    if overrides is not None:
        if not isinstance(overrides, Mapping):
            raise ValueError("Climate factor overrides must be a mapping of IDs to metadata records.")
        for key, value in overrides.items():
            if isinstance(value, ClimateFactor):
                factor = value
            elif isinstance(value, Mapping):
                # Metadata cannot be inherited from a published default while changing its value.
                allowed = {f.name for f in fields(ClimateFactor)}
                record = dict(value)
                record.pop("unit", None)
                record.setdefault("factor_id", key)
                try:
                    factor = ClimateFactor(**{k: v for k, v in record.items() if k in allowed})
                except TypeError as error:
                    raise ValueError(f"Factor {key} requires complete provenance metadata: {error}") from error
            else:
                raise ValueError(f"Factor {key} requires a metadata object, not a bare number.")
            if factor.factor_id != key:
                raise ValueError("Factor ID does not match override key.")
            factors[key] = factor
    return factors


def coerce_basis(basis):
    if isinstance(basis, LCAProjectBasis):
        return basis
    if basis is None:
        return LCAProjectBasis()
    if not isinstance(basis, Mapping):
        raise ValueError("LCA project basis must be an object.")
    data = dict(basis)
    if "included_groups" in data:
        data["included_groups"] = tuple(data["included_groups"])
    try:
        return LCAProjectBasis(**data)
    except TypeError as error:
        raise ValueError(f"Invalid LCA project basis: {error}") from error


def coerce_flow(flow):
    if isinstance(flow, InventoryFlow):
        return flow
    if not isinstance(flow, Mapping):
        raise ValueError("Inventory flow must be an object.")
    try:
        return InventoryFlow(**dict(flow))
    except TypeError as error:
        raise ValueError(f"Invalid inventory flow: {error}") from error
