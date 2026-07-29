"""Approved typed scientific equations; arbitrary expression evaluation is forbidden."""

from __future__ import annotations

from dataclasses import dataclass
from math import isfinite
from pathlib import Path
from typing import Callable

from Greenhub.parameters.serialization import write_records_csv


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
    )
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
