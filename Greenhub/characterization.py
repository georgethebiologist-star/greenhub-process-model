"""Convert measured GreenHub data into a detailed BioSTEAM feed stream."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

import biosteam as bst
import pandas as pd

from Greenhub.analytical import calculate_analytical_indicators
from Greenhub.chemicals import chemicals
from Greenhub.conversions import (
    N_TO_NH3,
    N_TO_NH4,
    P_TO_PO4,
    concentration_to_kg_hr,
    temperature_to_kelvin,
)
from Greenhub.equilibria import ammonia_equilibrium
from Greenhub.input_data import FeedSpecification, control_flag
from Greenhub.input_schema import InputRecord, optional_float
from Greenhub.reconciliation import ReconciliationRow, reconcile_measurements
from Greenhub.settings import DEFAULT_PRESSURE_PA, DEFAULT_TEMPERATURE_K


@dataclass(frozen=True)
class StreamCharacterization:
    """Measured physical and analytical properties associated with a stream."""

    pH: float | None
    density_kg_m3: float | None
    conductivity_mS_cm: float | None
    viscosity_mPa_s: float | None
    turbidity_NTU: float | None
    alkalinity_mg_CaCO3_L: float | None
    particle_size_um: float | None
    temperature_K: float
    pressure_Pa: float
    volumetric_flow_m3_hr: float | None


@dataclass(frozen=True)
class CharacterizationResult:
    """Characterized stream plus allocation, diagnostics, and provenance."""

    stream: bst.Stream
    specification: FeedSpecification
    component_flows_kg_hr: dict[str, float]
    physical: StreamCharacterization
    indicators: dict[str, float | None]
    reconciliation: tuple[ReconciliationRow, ...]
    allocation_rows: tuple[dict[str, Any], ...]
    data_quality_rows: tuple[dict[str, Any], ...]
    warnings: tuple[str, ...]


def _coerce_specification(input_data: FeedSpecification | Mapping[str, Any]) -> FeedSpecification:
    if isinstance(input_data, FeedSpecification):
        return input_data
    if not isinstance(input_data, Mapping):
        raise TypeError("input_data must be a FeedSpecification or mapping.")
    raw_records = input_data.get("records", ())
    records = tuple(i if isinstance(i, InputRecord) else InputRecord.from_mapping(i) for i in raw_records)
    total_flow = float(input_data["total_mass_flow_kg_hr"])
    if total_flow <= 0.0:
        raise ValueError("total_mass_flow_kg_hr must be positive.")
    return FeedSpecification(
        selected_month=str(input_data.get("selected_month", "July")),
        sample_id=str(input_data.get("sample_id", "baseline")),
        scenario=str(input_data.get("scenario", "baseline")),
        entry_mode=str(input_data.get("entry_mode", "measured_liquid")),
        monthly_total_mass_kg=float(input_data.get("monthly_total_mass_kg", total_flow * 24.0)),
        operating_days=float(input_data.get("operating_days", 1.0)),
        total_mass_flow_kg_hr=total_flow,
        records=records,
        control=dict(input_data.get("control", {})),
        monthly_table=pd.DataFrame(),
        measurements_table=pd.DataFrame([record.__dict__ for record in records]),
    )


def _record_by_name(records: tuple[InputRecord, ...], python_name: str) -> InputRecord | None:
    matches = [record for record in records if record.python_name == python_name and record.value is not None]
    return min(matches, key=lambda record: record.priority) if matches else None


def _physical_value(records: tuple[InputRecord, ...], python_name: str) -> float | None:
    record = _record_by_name(records, python_name)
    return record.value if record else None


def _reported_mass_factor(record: InputRecord, target: str) -> float:
    basis = (record.basis or "").strip().upper()
    if target == "Ammonium" and basis in {"N", "NH4-N", "TAN-N"}:
        return N_TO_NH4
    if target == "Ammonia" and basis in {"N", "NH3-N", "TAN-N"}:
        return N_TO_NH3
    if target == "NitrateIon" and basis in {"N", "NO3-N"}:
        return chemicals.NitrateIon.MW / 14.0067
    if target == "NitriteIon" and basis in {"N", "NO2-N"}:
        return chemicals.NitriteIon.MW / 14.0067
    if target == "Orthophosphate" and basis in {"P", "PO4-P"}:
        return P_TO_PO4
    return 1.0


def characterize_feed(
    input_data: FeedSpecification | Mapping[str, Any],
    *,
    sample_id: str | None = None,
    flow_basis: str = "kg/hr",
    ID: str = "raw_liquid_fraction",
) -> CharacterizationResult:
    """Characterize the selected measured-liquid dataset and create its stream."""

    if flow_basis not in {"kg/hr", "kg/h"}:
        raise ValueError("Phase 2 characterization currently uses canonical flow_basis='kg/hr'.")
    specification = _coerce_specification(input_data)
    if sample_id and sample_id.casefold() != specification.sample_id.casefold():
        raise ValueError(f"Requested sample_id '{sample_id}' does not match loaded sample '{specification.sample_id}'.")
    records = specification.records
    total_mass_flow = specification.total_mass_flow_kg_hr
    warnings: list[str] = []

    density = _physical_value(records, "density")
    volumetric_flow = total_mass_flow / density if density and density > 0.0 else None
    concentration_records = [
        record for record in records
        if record.value is not None and record.unit and "/L" in record.unit.replace(" ", "")
    ]
    if concentration_records and volumetric_flow is None:
        raise ValueError("Density is required because the selected dataset contains concentration-based component inputs.")

    temperature_record = _record_by_name(records, "temperature")
    temperature = (
        temperature_to_kelvin(temperature_record.value, temperature_record.unit or "degC")
        if temperature_record
        else DEFAULT_TEMPERATURE_K
    )
    pressure = _physical_value(records, "pressure") or DEFAULT_PRESSURE_PA
    pH = _physical_value(records, "ph")
    if pH is not None and not 0.0 <= pH <= 14.0:
        raise ValueError(f"pH must be within [0, 14]; received {pH}.")

    ts_record = _record_by_name(records, "total_solids")
    dry_solids_flow = None
    if ts_record and ts_record.value is not None:
        dry_solids_flow = concentration_to_kg_hr(
            ts_record.value,
            ts_record.unit or "g/L",
            wet_mass_flow_kg_hr=total_mass_flow,
            volumetric_flow_m3_hr=volumetric_flow,
        )

    selected_by_target: dict[str, InputRecord] = {}
    for record in records:
        if record.data_type != "component" or record.value is None or not record.allocation_target:
            continue
        target = record.allocation_target
        # Dissolved phosphate reported on a kg-P basis is canonicalized to a
        # physical PO4 component. The legacy DissolvedPhosphorus component is
        # retained only for genuinely unspeciated P-equivalent inventories.
        basis = (record.basis or "").strip().upper()
        if target == "DissolvedPhosphorus" and basis in {"P", "PO4-P"}:
            target = "Orthophosphate"
        if target not in chemicals.IDs:
            raise KeyError(f"Input '{record.python_name}' targets unknown component '{target}'.")
        existing = selected_by_target.get(target)
        if existing is None or record.priority < existing.priority:
            selected_by_target[target] = record

    component_flows: dict[str, float] = {}
    allocation_rows: list[dict[str, Any]] = []
    for target, record in selected_by_target.items():
        flow = concentration_to_kg_hr(
            record.value,
            record.unit or "kg/h",
            wet_mass_flow_kg_hr=total_mass_flow,
            dry_solids_flow_kg_hr=dry_solids_flow,
            volumetric_flow_m3_hr=volumetric_flow,
            molecular_weight_g_mol=float(chemicals[target].MW),
        )
        flow *= _reported_mass_factor(record, target)
        component_flows[target] = flow
        allocation_rows.append(
            {
                "input": record.python_name,
                "original_value": record.value,
                "original_unit": record.unit,
                "basis": record.basis,
                "allocation_target": target,
                "reported_allocation_target": record.allocation_target,
                "component_flow_kg_hr": flow,
                "status": record.measurement_status,
                "source_class": record.source_class,
                "reference": record.reference,
            }
        )

    specified_water = component_flows.pop("Water", None)
    nonwater_mass = sum(component_flows.values())
    tolerance = max(1e-9, total_mass_flow * 1e-9)
    if nonwater_mass > total_mass_flow + tolerance:
        raise ValueError(
            "Characterized non-water components exceed total wet feed mass: "
            f"{nonwater_mass:.6g} > {total_mass_flow:.6g} kg/hr."
        )
    residual_water = total_mass_flow - nonwater_mass
    if specified_water is not None and abs(specified_water - residual_water) > max(tolerance, total_mass_flow * 0.01):
        warnings.append("Entered water differs from balance-calculated water by more than 1%; balance-calculated water was used.")
    component_flows["Water"] = residual_water
    allocation_rows.append(
        {
            "input": "water_by_difference",
            "original_value": specified_water,
            "original_unit": "kg/hr" if specified_water is not None else None,
            "basis": "wet_mass_balance",
            "allocation_target": "Water",
            "component_flow_kg_hr": residual_water,
            "status": "calculated",
            "source_class": "E" if specified_water is None else "D",
            "reference": "Total wet flow minus allocated non-water components",
        }
    )

    stream = bst.Stream(ID=ID, T=temperature, P=pressure, units="kg/hr", **component_flows)
    alkalinity = _physical_value(records, "alkalinity")
    physical = StreamCharacterization(
        pH=pH,
        density_kg_m3=density,
        conductivity_mS_cm=_physical_value(records, "conductivity"),
        viscosity_mPa_s=_physical_value(records, "viscosity"),
        turbidity_NTU=_physical_value(records, "turbidity"),
        alkalinity_mg_CaCO3_L=alkalinity,
        particle_size_um=_physical_value(records, "particle_size"),
        temperature_K=temperature,
        pressure_Pa=pressure,
        volumetric_flow_m3_hr=volumetric_flow,
    )
    indicators = calculate_analytical_indicators(
        component_flows,
        volumetric_flow_m3_hr=volumetric_flow,
        alkalinity_mg_caco3_L=alkalinity,
    )
    reconciliation = reconcile_measurements(records, indicators)

    if pH is not None:
        total_ammonia_n = (
            component_flows.get("Ammonium", 0.0) * 14.0067 / chemicals.Ammonium.MW
            + component_flows.get("Ammonia", 0.0) * 14.0067 / chemicals.Ammonia.MW
        )
        if total_ammonia_n > 0.0:
            speciation = ammonia_equilibrium(total_ammonia_n, pH, temperature)
            indicators["unionized_ammonia_fraction"] = speciation.unionized_fraction
            indicators["equilibrium_ammonia_n_kg_hr"] = speciation.ammonia_n
            indicators["equilibrium_ammonium_n_kg_hr"] = speciation.ammonium_n

    if dry_solids_flow is not None:
        calculated_dry = float(indicators["dry_solids_kg_hr"] or 0.0)
        relative_gap = abs(calculated_dry - dry_solids_flow) / max(dry_solids_flow, 1e-12)
        if relative_gap > 0.20:
            warnings.append("Measured total solids and allocated non-water component mass differ by more than 20%.")

    data_quality_rows = []
    for record in records:
        warning = None
        if record.value is None:
            warning = "No value supplied; record was preserved as missing and did not add mass."
        elif record.source_class == "E":
            warning = "Placeholder/unknown quality input; replace before interpreting scenario performance."
        data_quality_rows.append(
            {
                "python_name": record.python_name,
                "value": record.value,
                "unit": record.unit,
                "measurement_status": record.measurement_status,
                "source_class": record.source_class,
                "source_description": {
                    "A": "Project measurement",
                    "B": "Supplier or industry data",
                    "C": "Peer-reviewed literature",
                    "D": "Engineering estimate",
                    "E": "Placeholder or unknown",
                }[record.source_class],
                "warning": warning,
            }
        )
    if control_flag(specification, "estimate_unknown_residuals", False):
        warnings.append("Residual estimation was requested, but no aggregate-constrained residual model is enabled in Phase 2; no residual component was invented.")

    return CharacterizationResult(
        stream=stream,
        specification=specification,
        component_flows_kg_hr=component_flows,
        physical=physical,
        indicators=indicators,
        reconciliation=reconciliation,
        allocation_rows=tuple(allocation_rows),
        data_quality_rows=tuple(data_quality_rows),
        warnings=tuple(warnings),
    )
