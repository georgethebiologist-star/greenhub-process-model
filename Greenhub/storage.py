"""
Greenhub.storage

Lightweight storage and degradation framework.
- Provides a StorageModel that tracks inventory (kg), capacity, and optional degradation.
- If degradation parameters are missing, the model records a clear provenance/limitation
  and does not silently convert missing data into zeros: inventory remains unchanged
  except for explicit inflow/outflow.

This module is intentionally small and additive so it can be integrated safely as a
compatibility-friendly process-area helper. It does not change any existing factories
or integration surfaces; integration into seasonal controllers is additive and must be
opted-in by higher-level code.

Provenance: each simulation step returns a `provenance` dict listing applied methods
and any limitations or sources. No external data is assumed.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from math import exp
from typing import Optional, Dict, Any


@dataclass
class StorageModel:
    """Simple storage inventory with optional first-order degradation.

    Parameters
    - capacity_kg: optional storage capacity. If None, storage is unbounded.
    - initial_inventory_kg: starting mass in kg.
    - degradation_rate_per_day: optional first-order degradation constant (1/day).
      If None, degradation is explicitly considered not implemented for provenance.
    """

    capacity_kg: Optional[float] = None
    initial_inventory_kg: float = 0.0
    degradation_rate_per_day: Optional[float] = None

    # runtime state
    inventory_kg: float = field(init=False)

    def __post_init__(self) -> None:
        self.inventory_kg = float(self.initial_inventory_kg)

    def simulate_step(self, inflow_kg: float = 0.0, outflow_kg: float = 0.0, days: float = 1.0) -> Dict[str, Any]:
        """Advance storage by one step.

        Returns a dict with keys:
        - inventory_kg: new inventory after accounting inflow/outflow and degradation (if applied)
        - applied_degradation_kg: mass lost to degradation (0.0 if not implemented or zero)
        - overflow_kg: mass that could not be stored because capacity was exceeded
        - provenance: dict documenting applied methods, limitations, and sources
        """
        provenance: Dict[str, Any] = {
            "methods": [],
            "limitations": [],
            "sources": [],
        }

        # apply inflow
        self.inventory_kg += float(inflow_kg)
        provenance["methods"].append({"inflow_kg": float(inflow_kg)})

        # apply outflow (withdrawal before degradation to match perfectly-mixed withdraw assumption)
        withdrawal = float(outflow_kg)
        if withdrawal < 0:
            raise ValueError("outflow_kg must be non-negative")
        withdrawn = min(withdrawal, self.inventory_kg)
        self.inventory_kg -= withdrawn
        provenance["methods"].append({"outflow_kg": withdrawn})

        # apply degradation if parameter is provided
        applied_degradation_kg = 0.0
        if self.degradation_rate_per_day is None:
            # Explicitly mark degradation as not implemented / missing-data
            provenance["limitations"].append("degradation_not_implemented")
            provenance["methods"].append({"degradation": "not_implemented"})
            applied_degradation_kg = 0.0
        else:
            # first-order loss: mass_after = mass_before * exp(-k * days)
            k = float(self.degradation_rate_per_day)
            if k < 0:
                raise ValueError("degradation_rate_per_day must be non-negative")
            mass_before = self.inventory_kg
            mass_after = mass_before * exp(-k * float(days))
            applied_degradation_kg = mass_before - mass_after
            self.inventory_kg = mass_after
            provenance["methods"].append({"degradation": {"k_1_per_day": k, "days": float(days)}})
            provenance["sources"].append("user_provided_degradation_rate")

        # apply capacity limit and compute overflow
        overflow_kg = 0.0
        if self.capacity_kg is not None:
            if self.inventory_kg > float(self.capacity_kg):
                overflow_kg = self.inventory_kg - float(self.capacity_kg)
                self.inventory_kg = float(self.capacity_kg)
                provenance["limitations"].append("capacity_overflow")

        provenance_summary = {
            "applied_degradation_kg": applied_degradation_kg,
            "overflow_kg": overflow_kg,
            "inventory_kg": self.inventory_kg,
        }

        return {"inventory_kg": self.inventory_kg, "applied_degradation_kg": applied_degradation_kg, "overflow_kg": overflow_kg, "provenance": provenance, "summary": provenance_summary}

    def to_dict(self) -> Dict[str, Any]:
        return {
            "capacity_kg": self.capacity_kg,
            "inventory_kg": self.inventory_kg,
            "degradation_rate_per_day": self.degradation_rate_per_day,
        }
