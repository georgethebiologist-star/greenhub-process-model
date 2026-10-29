"""Mass-balance-safe screening calculations for pretreatment state updates."""

from __future__ import annotations

from dataclasses import dataclass, asdict
from math import isfinite
from typing import Mapping


@dataclass(frozen=True)
class PretreatmentStateResult:
    input_component_masses_kg_hr: dict[str, float]
    output_component_masses_kg_hr: dict[str, float]
    water_added_kg_hr: float
    press_energy_kwh_hr: float
    mass_residual_kg_hr: float
    equation_usage: tuple[str, ...]
    parameter_usage: tuple[str, ...]
    status: str
    warnings: tuple[str, ...]

    def to_dict(self) -> dict[str, object]:
        return asdict(self)

    def to_lca_inventory(self, *, annualization_factor: float | None = None) -> tuple[dict[str, object], ...]:
        """Return explicit LCA additional-inventory rows when annualized."""

        if annualization_factor is None:
            return ()
        factor = float(annualization_factor)
        if not isfinite(factor) or factor < 0:
            raise ValueError("annualization_factor must be finite and non-negative.")
        return (
            {
                "flow_id": "pretreatment_press_electricity",
                "accounting_key": "pretreatment_press_electricity",
                "group": "electricity",
                "quantity": self.press_energy_kwh_hr * factor,
                "unit": "kWh",
                "factor_id": "electricity",
                "direction": "burden",
                "source_id": "pretreatment_state",
                "warning": "Screening press-energy assumption; replace with measured or supplier data.",
            },
            {
                "flow_id": "pretreatment_added_water",
                "accounting_key": "pretreatment_added_water",
                "group": "materials",
                "quantity": self.water_added_kg_hr * factor,
                "unit": "kg",
                "factor_id": None,
                "direction": "burden",
                "source_id": "pretreatment_state",
                "warning": "Added process water is reported as an input; no water-treatment burden is inferred without a supplied factor.",
            },
        )


def apply_screening_pretreatment_state(
    component_masses_kg_hr: Mapping[str, float],
    *,
    water_addition_kg_per_kg_wet_feed: float = 0.0,
    press_energy_kwh_per_t_wet_feed: float | None = None,
) -> PretreatmentStateResult:
    """Apply explicit dilution and press-energy assumptions to a feed state.

    The calculation changes only water and utilities. No component recovery or
    separation is inferred here; those remain owned by the existing raw-press
    route. Defaults therefore reproduce the incoming state exactly.
    """

    if any(not isfinite(float(value)) or float(value) < 0 for value in component_masses_kg_hr.values()):
        raise ValueError("Pretreatment component masses must be finite and non-negative.")
    water_ratio = float(water_addition_kg_per_kg_wet_feed)
    if not isfinite(water_ratio) or water_ratio < 0:
        raise ValueError("water_addition_kg_per_kg_wet_feed must be finite and non-negative.")
    if press_energy_kwh_per_t_wet_feed is not None and (
        not isfinite(float(press_energy_kwh_per_t_wet_feed))
        or float(press_energy_kwh_per_t_wet_feed) < 0
    ):
        raise ValueError("press_energy_kwh_per_t_wet_feed must be finite and non-negative.")

    inputs = {str(key): float(value) for key, value in component_masses_kg_hr.items()}
    wet_feed = sum(inputs.values())
    water_added = wet_feed * water_ratio
    outputs = dict(inputs)
    outputs["Water"] = outputs.get("Water", 0.0) + water_added
    energy = wet_feed / 1000.0 * float(press_energy_kwh_per_t_wet_feed or 0.0)
    residual = sum(outputs.values()) - (wet_feed + water_added)
    warnings = (
        "Screening dilution changes only water inventory; no solids or component recovery is inferred.",
    ) if water_added else ()
    return PretreatmentStateResult(
        input_component_masses_kg_hr=inputs,
        output_component_masses_kg_hr=outputs,
        water_added_kg_hr=water_added,
        press_energy_kwh_hr=energy,
        mass_residual_kg_hr=residual,
        equation_usage=("pretreatment.water_addition = wet_feed_mass × water_addition_ratio",
                        "pretreatment.press_energy = wet_feed_tonnes_per_hour × press_energy_per_tonne"),
        parameter_usage=("phase3.pretreatment.water_addition_kg_per_kg_wet_feed",
                         "phase3.pretreatment.press_energy_kwh_per_t_wet_feed"),
        status="screening_assumption" if water_added or energy else "baseline_no_override",
        warnings=warnings,
    )
