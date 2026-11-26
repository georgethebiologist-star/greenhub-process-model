"""Approved typed scientific equations; arbitrary expression evaluation is forbidden."""

from __future__ import annotations

from dataclasses import dataclass
from math import isfinite
from pathlib import Path
from typing import Callable

from Greenhub.parameters.serialization import write_records_csv
from Greenhub.phase6_specifications import h2s_solubility_temperature_ratio


@dataclass(frozen=True)
class ProteinPrecipitationBalance:
    protein_in_kg_hr: float
    protein_supernatant_kg_hr: float
    protein_cake_kg_hr: float
    protein_loss_kg_hr: float
    residual_kg_hr: float


def protein_precipitation_mass_balance(
    protein_in_kg_hr: float,
    recovery_fraction: float,
    protein_loss_kg_hr: float = 0.0,
) -> ProteinPrecipitationBalance:
    """Implement EQ-MB-001 on one consistent kg/h protein basis."""

    incoming = float(protein_in_kg_hr)
    recovery = float(recovery_fraction)
    loss = float(protein_loss_kg_hr)
    if not all(isfinite(item) for item in (incoming, recovery, loss)):
        raise ValueError("EQ-MB-001 inputs must be finite.")
    if incoming < 0.0 or loss < 0.0:
        raise ValueError("EQ-MB-001 mass inputs must be non-negative.")
    if not 0.0 <= recovery <= 1.0:
        raise ValueError("EQ-MB-001 recovery_fraction must be within [0, 1].")
    cake = incoming * recovery
    if cake + loss > incoming + 1e-12:
        raise ValueError("EQ-MB-001 cake plus loss cannot exceed incoming protein.")
    supernatant = incoming - cake - loss
    residual = incoming - supernatant - cake - loss
    return ProteinPrecipitationBalance(incoming, supernatant, cake, loss, residual)


def moisture_wet_basis_from_total_solids(total_solids_wet_basis: float) -> float:
    """Implement EQ-CALC-001 as a bounded wet-basis mass-fraction identity."""

    total_solids = float(total_solids_wet_basis)
    if not isfinite(total_solids):
        raise ValueError("EQ-CALC-001 total_solids_wet_basis must be finite.")
    if not 0.0 <= total_solids <= 1.0:
        raise ValueError("EQ-CALC-001 total_solids_wet_basis must be within [0, 1].")
    moisture = 1.0 - total_solids
    if not 0.0 <= moisture <= 1.0:
        raise ValueError("EQ-CALC-001 moisture_wet_basis result must be within [0, 1].")
    return moisture


@dataclass(frozen=True)
class EquationDefinition:
    equation_id: str
    function: Callable[..., object]
    process_area: str
    unit_operation: str
    input_symbols: tuple[str, ...]
    canonical_parameter_ids: tuple[str, ...]
    input_units: tuple[str, ...]
    output_units: tuple[str, ...]
    applicability: str
    source: str
    source_location: str
    limitations: str
    activation_status: str
    readiness_state: str


EQUATION_REGISTRY = {
    "EQ-MB-001": EquationDefinition(
        equation_id="EQ-MB-001",
        function=protein_precipitation_mass_balance,
        process_area="protein_recovery",
        unit_operation="direct isoelectric precipitation",
        input_symbols=("m_protein_in", "recovery_fraction", "m_protein_loss"),
        canonical_parameter_ids=("phase4.precipitation_efficiency",),
        input_units=("kg/hr", "fraction", "kg/hr"),
        output_units=("kg/hr", "kg/hr", "kg/hr", "kg/hr"),
        applicability="Mass-conserving soluble-protein pool transfer in R401.",
        source="Protein recovery/Isoelectric/equation_registry.csv",
        source_location="EQ-MB-001; fundamental mass balance",
        limitations="Protein and non-protein nitrogen must not be conflated in experimental interpretation.",
        activation_status="active",
        readiness_state="D4",
    ),
    "EQ-CALC-001": EquationDefinition(
        equation_id="EQ-CALC-001",
        function=moisture_wet_basis_from_total_solids,
        process_area="feedstock",
        unit_operation="roadside grass feedstock proxy",
        input_symbols=("total_solids_wet_basis",),
        canonical_parameter_ids=("moisture_wet_basis",),
        input_units=("fraction wet basis",),
        output_units=("fraction wet basis",),
        applicability="Wet-basis moisture identity from total solids on the same wet basis.",
        source="Pre-treatment/Feedstock/equation_registry.csv",
        source_location="EQ-CALC-001; wet-basis moisture from total solids",
        limitations="Report-only typed helper; not consumed by model calculations.",
        activation_status="report_only",
        readiness_state="typed_not_active",
    ),
    "EQ-P6-WS-H2S-001": EquationDefinition(
        equation_id="EQ-P6-WS-H2S-001",
        function=h2s_solubility_temperature_ratio,
        process_area="biogas_conditioning_and_upgrading",
        unit_operation="water scrubbing absorber",
        input_symbols=("temperature_c", "reference_temperature_c", "low_A", "low_B_k", "high_A", "high_B_k", "high_C", "high_D_per_k", "transition_K", "minimum_K", "maximum_K"),
        canonical_parameter_ids=(
            "phase6.water_scrubber_h2s_solubility_fit_low_a",
            "phase6.water_scrubber_h2s_solubility_fit_low_b_k",
            "phase6.water_scrubber_h2s_solubility_fit_high_a",
            "phase6.water_scrubber_h2s_solubility_fit_high_b_k",
            "phase6.water_scrubber_h2s_solubility_fit_high_c",
            "phase6.water_scrubber_h2s_solubility_fit_high_d_per_k",
            "phase6.water_scrubber_h2s_solubility_fit_transition_temperature_k",
            "phase6.water_scrubber_h2s_solubility_fit_minimum_temperature_k",
            "phase6.water_scrubber_h2s_solubility_fit_maximum_temperature_k",
        ),
        input_units=("degC", "degC", "1", "K", "1", "K", "1", "1/K", "K", "K", "K"),
        output_units=("dimensionless relative solubility ratio",),
        applicability="Relative dilute pure-water H2S equilibrium-solubility response in BG2 absorber A611; modifies the existing calibrated apparent-partition model only in literature_default or expert_override mode.",
        source="Bigas production + upgrade/Water_Scrubbing/h2s_temperature_parameter.csv",
        source_location="WS_H2S_T_001–009; piecewise IUPAC-evaluated Clarke & Glew measured-solubility fits and reported validity boundaries",
        limitations="Does not model H2S reference removal, pH/speciation, electrolyte effects, non-ideality, kLa, packing, or stage efficiency.",
        activation_status="active_mode_gated",
        readiness_state="D4",
    ),
}


def export_equation_activation_registry(path: Path) -> Path:
    return write_records_csv(
        path,
        (
            {
                "equation_id": item.equation_id,
                "python_function": item.function.__name__,
                "process_area": item.process_area,
                "unit_operation": item.unit_operation,
                "input_symbols": list(item.input_symbols),
                "canonical_parameter_ids": list(item.canonical_parameter_ids),
                "input_units": list(item.input_units),
                "output_units": list(item.output_units),
                "applicability": item.applicability,
                "source": item.source,
                "source_location": item.source_location,
                "limitations": item.limitations,
                "activation_status": item.activation_status,
                "readiness_state": item.readiness_state,
            }
            for item in EQUATION_REGISTRY.values()
        ),
    )
