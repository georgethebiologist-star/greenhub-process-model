"""Mass-conserving wet-biomass storage inventory bookkeeping."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class StorageInventory:
    total_mass_kg: float = 0.0
    component_masses_kg: dict[str, float] = field(default_factory=dict)
    age_mass_kg_h: float = 0.0
    temperature_mass_kg_k: float = 0.0

    @property
    def average_age_h(self) -> float:
        return self.age_mass_kg_h / self.total_mass_kg if self.total_mass_kg > 0.0 else 0.0

    @property
    def temperature_k(self) -> float | None:
        return self.temperature_mass_kg_k / self.total_mass_kg if self.total_mass_kg > 0.0 else None

    def receive(
        self,
        mass_kg: float,
        component_masses_kg: dict[str, float],
        temperature_k: float | None,
        capacity_kg: float | None,
    ) -> float:
        if mass_kg < 0.0:
            raise ValueError("Received storage mass must be non-negative.")
        if abs(sum(component_masses_kg.values()) - mass_kg) > max(1e-8, mass_kg * 1e-9):
            raise ValueError("Received component masses must sum to received wet mass.")
        self.total_mass_kg += mass_kg
        for name, value in component_masses_kg.items():
            self.component_masses_kg[name] = self.component_masses_kg.get(name, 0.0) + value
        if temperature_k is not None:
            self.temperature_mass_kg_k += mass_kg * temperature_k
        overflow = max(self.total_mass_kg - capacity_kg, 0.0) if capacity_kg is not None else 0.0
        if overflow:
            self._remove_proportionally(overflow)
        return overflow

    def withdraw(self, requested_kg: float) -> tuple[float, dict[str, float]]:
        if requested_kg < 0.0:
            raise ValueError("Requested withdrawal must be non-negative.")
        withdrawn = min(requested_kg, self.total_mass_kg)
        components = self._remove_proportionally(withdrawn)
        return withdrawn, components

    def age(self, duration_h: float) -> None:
        if duration_h < 0.0:
            raise ValueError("Storage duration must be non-negative.")
        self.age_mass_kg_h += self.total_mass_kg * duration_h

    def _remove_proportionally(self, mass_kg: float) -> dict[str, float]:
        if mass_kg <= 0.0 or self.total_mass_kg <= 0.0:
            return {name: 0.0 for name in self.component_masses_kg}
        fraction = min(mass_kg / self.total_mass_kg, 1.0)
        removed = {}
        for name, value in tuple(self.component_masses_kg.items()):
            amount = value * fraction
            removed[name] = amount
            remaining = value - amount
            if abs(remaining) < 1e-12:
                self.component_masses_kg.pop(name, None)
            else:
                self.component_masses_kg[name] = remaining
        self.age_mass_kg_h *= 1.0 - fraction
        self.temperature_mass_kg_k *= 1.0 - fraction
        self.total_mass_kg *= 1.0 - fraction
        if self.total_mass_kg < 1e-12:
            self.total_mass_kg = 0.0
            self.age_mass_kg_h = 0.0
            self.temperature_mass_kg_k = 0.0
        return removed
