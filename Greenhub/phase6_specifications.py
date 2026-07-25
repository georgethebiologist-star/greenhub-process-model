"""Pure engineering calculations for Phase 6 gas conditioning and upgrading.

The functions in this module do not mutate BioSTEAM streams. They provide the
transparent Level-1 equations used by the custom units and keep empirical
calibration separate from mechanistic calculations. Normal gas conditions are
0 degC and 101325 Pa, consistent with Phase 5.
"""

from __future__ import annotations

from dataclasses import dataclass
from math import ceil, exp, pi
from typing import Mapping

from Greenhub.phase5_specifications import (
    IDEAL_GAS_CONSTANT_PA_M3_PER_KMOL_K,
    NORMAL_M3_PER_KMOL,
    bounded_fraction,
    nonnegative,
    positive,
)

GPU_TO_KMOL_M2_H_BAR = 1.20528e-4
DRY_GAS_COMPONENTS = (
    "Methane",
    "CarbonDioxide",
    "Hydrogen",
    "HydrogenSulfide",
    "Ammonia",
    "Oxygen",
    "Nitrogen",
    "Siloxanes",
)


def normal_volume_nm3_hr(stream, *, dry: bool = False) -> float:
    """Return normal volumetric flow from stream molar inventory."""

    if dry:
        kmol = sum(float(stream.imol[ID]) for ID in DRY_GAS_COMPONENTS)
    else:
        kmol = sum(
            float(stream.imol[ID])
            for ID in (*DRY_GAS_COMPONENTS, "Water")
        )
    return max(0.0, kmol) * NORMAL_M3_PER_KMOL


def actual_gas_volume_m3_hr(kmol_hr: float, temperature_k: float, pressure_pa: float) -> float:
    """Return ideal-gas volumetric flow at stream conditions."""

    amount = nonnegative(kmol_hr, "Gas molar flow")
    temperature = positive(temperature_k, "Gas temperature")
    pressure = positive(pressure_pa, "Gas pressure")
    return amount * IDEAL_GAS_CONSTANT_PA_M3_PER_KMOL_K * temperature / pressure


def water_vapor_pressure_pa(temperature_k: float) -> float:
    """Return water saturation pressure using the Magnus equation.

    The correlation is used only over the Phase 6 conditioning range. It is
    adequate for structural moisture knock-out calculations but is not a
    rigorous mixed-gas fugacity model.
    """

    temperature_c = float(temperature_k) - 273.15
    if not -45.0 <= temperature_c <= 80.0:
        raise ValueError(
            "Phase 6 water-vapor correlation is restricted to -45 through 80 degC."
        )
    return 610.94 * exp(17.625 * temperature_c / (temperature_c + 243.04))


def saturated_water_kmol_hr(
    dry_gas_kmol_hr: float,
    temperature_k: float,
    pressure_pa: float,
) -> float:
    """Return saturated water flow for a specified dry-gas flow."""

    dry = nonnegative(dry_gas_kmol_hr, "Dry-gas flow")
    pressure = positive(pressure_pa, "Gas pressure")
    saturation_pressure = water_vapor_pressure_pa(temperature_k)
    if saturation_pressure >= pressure:
        raise ValueError("Gas pressure must exceed water saturation pressure.")
    wet_fraction = saturation_pressure / pressure
    return dry * wet_fraction / (1.0 - wet_fraction)


def empirical_absorption_fraction(
    reference_fraction: float,
    *,
    pressure_bar: float,
    reference_pressure_bar: float,
    water_to_gas_ratio: float,
    reference_water_to_gas_ratio: float,
    temperature_c: float,
    reference_temperature_c: float,
    temperature_coefficient_per_c: float,
) -> float:
    """Scale a calibrated absorption fraction with transparent drivers.

    The response is bounded and monotonic in pressure and water circulation.
    It is an apparent Level-1 partition model, not a Henry-law stage model.
    """

    base = bounded_fraction(reference_fraction, "Reference absorption fraction")
    pressure_factor = positive(pressure_bar, "Absorber pressure") / positive(
        reference_pressure_bar,
        "Reference absorber pressure",
    )
    liquid_factor = nonnegative(water_to_gas_ratio, "Water-to-gas ratio") / positive(
        reference_water_to_gas_ratio,
        "Reference water-to-gas ratio",
    )
    temperature_factor = exp(
        float(temperature_coefficient_per_c)
        * (float(reference_temperature_c) - float(temperature_c))
    )
    exposure = max(0.0, pressure_factor * liquid_factor * temperature_factor)
    if base >= 1.0:
        return 1.0
    return max(0.0, min(1.0, 1.0 - (1.0 - base) ** exposure))


@dataclass(frozen=True)
class ColumnGeometry:
    """Screening geometry for a vertical gas-contacting column."""

    gas_flow_m3_hr: float
    cross_section_m2: float
    diameter_m: float
    packing_height_m: float
    total_volume_m3: float
    superficial_velocity_m_s: float


def size_gas_column(
    *,
    gas_kmol_hr: float,
    temperature_k: float,
    pressure_pa: float,
    design_superficial_velocity_m_s: float,
    packing_height_m: float,
) -> ColumnGeometry:
    """Size a screening packed column from ideal-gas flow and velocity."""

    velocity = positive(design_superficial_velocity_m_s, "Superficial velocity")
    height = positive(packing_height_m, "Packing height")
    gas_flow = actual_gas_volume_m3_hr(gas_kmol_hr, temperature_k, pressure_pa)
    area = gas_flow / 3600.0 / velocity if gas_flow else 0.0
    diameter = (4.0 * area / pi) ** 0.5 if area else 0.0
    return ColumnGeometry(
        gas_flow,
        area,
        diameter,
        height,
        area * height,
        velocity if gas_flow else 0.0,
    )


def gas_vessel_volume_m3(
    *,
    gas_kmol_hr: float,
    temperature_k: float,
    pressure_pa: float,
    residence_time_min: float,
) -> float:
    """Return working gas volume from residence time and actual flow."""

    residence = nonnegative(residence_time_min, "Residence time")
    flow = actual_gas_volume_m3_hr(gas_kmol_hr, temperature_k, pressure_pa)
    return flow * residence / 60.0


def liquid_vessel_volume_m3(
    *,
    liquid_flow_kg_hr: float,
    density_kg_m3: float,
    residence_time_min: float,
) -> float:
    """Return liquid working volume from mass flow, density, and residence."""

    mass = nonnegative(liquid_flow_kg_hr, "Liquid mass flow")
    density = positive(density_kg_m3, "Liquid density")
    residence = nonnegative(residence_time_min, "Residence time")
    return mass / density * residence / 60.0


def pump_power_kw(
    *,
    liquid_flow_kg_hr: float,
    density_kg_m3: float,
    pressure_in_pa: float,
    pressure_out_pa: float,
    efficiency: float,
) -> float:
    """Return incompressible hydraulic-pump electricity."""

    mass = nonnegative(liquid_flow_kg_hr, "Liquid mass flow")
    density = positive(density_kg_m3, "Liquid density")
    eta = bounded_fraction(efficiency, "Pump efficiency", positive_lower=True)
    pressure_rise = max(0.0, float(pressure_out_pa) - float(pressure_in_pa))
    volume_m3_s = mass / density / 3600.0
    return volume_m3_s * pressure_rise / eta / 1000.0


def ideal_gas_compressor_power_kw(
    *,
    molar_flow_kmol_hr: float,
    inlet_temperature_k: float,
    inlet_pressure_pa: float,
    outlet_pressure_pa: float,
    isentropic_efficiency: float,
    heat_capacity_ratio: float = 1.30,
) -> float:
    """Return ideal-gas isentropic compressor power for reference checks."""

    flow = nonnegative(molar_flow_kmol_hr, "Compressor molar flow")
    temperature = positive(inlet_temperature_k, "Compressor inlet temperature")
    p_in = positive(inlet_pressure_pa, "Compressor inlet pressure")
    p_out = positive(outlet_pressure_pa, "Compressor outlet pressure")
    eta = bounded_fraction(
        isentropic_efficiency,
        "Compressor isentropic efficiency",
        positive_lower=True,
    )
    gamma = float(heat_capacity_ratio)
    if gamma <= 1.0:
        raise ValueError("Heat-capacity ratio must exceed 1.")
    if p_out <= p_in or flow == 0.0:
        return 0.0
    work_kj_kmol = (
        gamma
        / (gamma - 1.0)
        * 8.314462618
        * temperature
        * ((p_out / p_in) ** ((gamma - 1.0) / gamma) - 1.0)
        / eta
    )
    return flow * work_kj_kmol / 3600.0


@dataclass(frozen=True)
class MembraneStageCalculation:
    """Result of one segmented solution-diffusion membrane calculation."""

    retentate_kmol_hr: dict[str, float]
    permeate_kmol_hr: dict[str, float]
    stage_cut: float
    feed_kmol_hr: float
    permeate_total_kmol_hr: float
    area_m2: float
    segments: int
    average_feed_pressure_bar: float


def segmented_membrane_separation(
    feed_kmol_hr: Mapping[str, float],
    *,
    permeance_gpu: Mapping[str, float],
    membrane_area_m2: float,
    feed_pressure_bar: float,
    permeate_pressure_bar: float,
    pressure_drop_bar: float,
    segments: int,
) -> MembraneStageCalculation:
    """Solve sequential membrane segments using partial-pressure flux.

    Flux follows ``J_i = permeance_i * (p_feed_i - p_perm_i)``. Permeate
    composition is updated after every segment and transfer is capped by local
    feed availability. Stage cut is therefore an output, never an independent
    purity/recovery specification.
    """

    area = positive(membrane_area_m2, "Membrane area")
    p_feed = positive(feed_pressure_bar, "Membrane feed pressure")
    p_perm = positive(permeate_pressure_bar, "Membrane permeate pressure")
    drop = nonnegative(pressure_drop_bar, "Membrane pressure drop")
    if p_feed - drop <= p_perm:
        raise ValueError("Membrane retentate pressure must exceed permeate pressure.")
    count = int(segments)
    if count < 1:
        raise ValueError("Membrane segments must be at least 1.")
    remaining = {ID: nonnegative(value, f"{ID} membrane feed") for ID, value in feed_kmol_hr.items()}
    permeated = {ID: 0.0 for ID in remaining}
    feed_total = sum(remaining.values())
    if feed_total == 0.0:
        return MembraneStageCalculation(
            remaining,
            permeated,
            0.0,
            0.0,
            0.0,
            area,
            count,
            p_feed - drop / 2.0,
        )
    area_segment = area / count
    for index in range(count):
        total_remaining = sum(remaining.values())
        if total_remaining <= 1e-15:
            break
        y_feed = {ID: value / total_remaining for ID, value in remaining.items()}
        total_permeated = sum(permeated.values())
        if total_permeated > 1e-15:
            y_perm = {ID: value / total_permeated for ID, value in permeated.items()}
        else:
            weights = {
                ID: max(0.0, float(permeance_gpu.get(ID, 0.0))) * fraction
                for ID, fraction in y_feed.items()
            }
            weight_total = sum(weights.values())
            y_perm = {
                ID: value / weight_total if weight_total else 0.0
                for ID, value in weights.items()
            }
        local_pressure = p_feed - drop * (index + 0.5) / count
        proposed: dict[str, float] = {}
        for ID, available in remaining.items():
            permeance = nonnegative(
                float(permeance_gpu.get(ID, 0.0)),
                f"{ID} permeance",
            )
            driving_bar = max(
                0.0,
                y_feed[ID] * local_pressure - y_perm[ID] * p_perm,
            )
            transfer = (
                permeance
                * GPU_TO_KMOL_M2_H_BAR
                * driving_bar
                * area_segment
            )
            proposed[ID] = min(available, max(0.0, transfer))
        # Limiting each segment prevents a coarse discretization from draining
        # the complete local feed before composition can be updated.
        proposed_total = sum(proposed.values())
        maximum_segment_transfer = 0.80 * total_remaining
        scale = (
            maximum_segment_transfer / proposed_total
            if proposed_total > maximum_segment_transfer > 0.0
            else 1.0
        )
        for ID, transfer in proposed.items():
            actual = min(remaining[ID], transfer * scale)
            remaining[ID] -= actual
            permeated[ID] += actual
    permeate_total = sum(permeated.values())
    return MembraneStageCalculation(
        remaining,
        permeated,
        permeate_total / feed_total,
        feed_total,
        permeate_total,
        area,
        count,
        p_feed - drop / 2.0,
    )


def module_count(area_m2: float, nominal_module_area_m2: float) -> int:
    """Return whole membrane-module count from required active area."""

    area = nonnegative(area_m2, "Membrane area")
    nominal = positive(nominal_module_area_m2, "Nominal module area")
    return ceil(area / nominal) if area else 0
