"""Export deterministic machine-readable Checkpoint 2 parameter registries."""

from __future__ import annotations

from pathlib import Path

from Greenhub.settings import DATA_DIR
from Greenhub.scientific_equations import export_equation_activation_registry

from .editable_registry import build_editable_registry
from .enums import CalculationMode
from .loaders import load_default_registry
from .resolver import ParameterResolver
from .selectors import SelectionContext
from .serialization import to_json_compatible, write_records_csv

OUTPUT_DIR = DATA_DIR / "advanced_model"


def export_parameter_registries(output_dir: Path = OUTPUT_DIR) -> dict[str, Path]:
    registry = load_default_registry()
    control = {
        item.parameter_id: item.value
        for item in registry
        if item.parameter_id.startswith("control.")
    }
    selected_scenarios = tuple(
        str(control[key])
        for key in (
            "control.scenario.feed_preparation",
            "control.scenario.protein_recovery",
            "control.scenario.anaerobic_digestion",
            "control.scenario.biogas_upgrading",
            "control.scenario.nutrient_recovery",
        )
    )
    context = SelectionContext(
        calculation_mode=CalculationMode.STRUCTURAL,
        selected_scenarios=selected_scenarios,
        month=str(control["control.selected_month"]),
    )
    resolved = ParameterResolver(registry).resolve(context)
    editable = build_editable_registry(registry, resolved)
    output_dir.mkdir(parents=True, exist_ok=True)
    canonical_path = write_records_csv(
        output_dir / "canonical_parameter_registry.csv",
        (to_json_compatible(item) for item in registry),
    )
    editable_path = write_records_csv(
        output_dir / "editable_parameter_registry.csv",
        (to_json_compatible(item) for item in editable),
    )
    activation_path = write_records_csv(
        output_dir / "parameter_activation_registry.csv",
        (
            {
                "candidate_id": item.candidate_id,
                "parameter_id": item.parameter_id,
                "source_dataset": item.source_dataset,
                "source_row_id": item.source_row_id,
                "activation_state": item.activation_state.value,
                "readiness_state": item.readiness_state.value,
                "value_status": item.value_status.value,
                "calculation_modes": [mode.value for mode in item.applicability.calculation_modes],
                "scenario_ids": list(item.applicability.scenario_ids),
                "warnings": list(item.warnings),
            }
            for item in registry.candidates
        ),
    )
    equation_path = export_equation_activation_registry(
        output_dir / "equation_activation_registry.csv"
    )
    return {
        "canonical_parameter_registry": canonical_path,
        "editable_parameter_registry": editable_path,
        "parameter_activation_registry": activation_path,
        "equation_activation_registry": equation_path,
    }


def main() -> None:
    for name, path in export_parameter_registries().items():
        print(f"{name}: {path}")


if __name__ == "__main__":
    main()
