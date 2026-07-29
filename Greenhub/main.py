"""Run, validate, compare, and report the integrated GreenHub process model."""

from __future__ import annotations

import gc
from pathlib import Path
import shutil

from Greenhub.input_data import INPUT_WORKBOOK_PATH, ensure_input_workbook
from Greenhub.integrated_reporting import save_integrated_reports
from Greenhub.integration import create_integrated_greenhub_system
from Greenhub.model_completeness import write_model_completeness_reports
from Greenhub.phase7_reporting import save_phase7_reports, snapshot_phase7_comparison
from Greenhub.phase7_systems import create_phase7_scenario, simulate_phase7_season
from Greenhub.scenarios import NUTRIENT_RECOVERY_SCENARIOS
from Greenhub.settings import RESULTS_DIR, ensure_results_dir, initialize_environment

ACTIVE_PHASE7_SCENARIOS = tuple(f"NR{i}" for i in range(8))


def _print_stream(label: str, stream) -> None:
    """Print every non-zero component in one stream on a kg/hr basis."""

    print(f"\n{label}")
    print(
        f"  Total: {stream.F_mass:.6g} kg/hr; "
        f"T={stream.T:.2f} K; P={stream.P:.0f} Pa; phase={stream.phase}"
    )
    for component_id in stream.chemicals.IDs:
        flow = float(stream.imass[component_id])
        if flow > 0.0:
            print(f"  {component_id:<30} {flow:>12.6g} kg/hr")


def _save_flowsheet_diagram(system, output_path: Path) -> bool:
    """Save the complete plant diagram without making Graphviz mandatory."""

    output_path.parent.mkdir(parents=True, exist_ok=True)
    try:
        import os
        graphviz_bin = r"C:\Program Files\Graphviz\bin"
        os.environ["PATH"] = graphviz_bin + os.pathsep + os.environ.get("PATH", "")
        system.diagram(
            kind="thorough",
            file=str(output_path.with_suffix("")),
            format="png",
            display=False,
            label=True,
            title="Integrated GreenHub Biomass Valorization System",
        )
    except Exception as error:  # pragma: no cover - external Graphviz behavior
        print(
            "\nFlowsheet diagram was not generated. Verify that "
            "C:\\Program Files\\Graphviz\\bin\\dot.exe exists and that the Python "
            f"graphviz package is installed. Original error: {error}"
        )
        return False
    if not output_path.exists():
        print(f"\nGraphviz returned without creating the expected file: {output_path}")
        return False
    print(f"\nFlowsheet diagram saved to: {output_path}")
    return True


def _print_scenario_readiness() -> None:
    print("\nNutrient-recovery scenario architecture")
    for scenario in NUTRIENT_RECOVERY_SCENARIOS.values():
        status = "active" if scenario.active else "inactive/data-gated"
        print(
            f"  {scenario.scenario_id}: {scenario.name} [{status}; "
            f"default order {scenario.default_order}]"
        )


def main() -> None:
    """Configure, simulate, validate, compare, and report the complete plant."""

    initialize_environment()
    ensure_results_dir()
    ensure_input_workbook()
    integrated_model = create_integrated_greenhub_system().simulate()
    model = integrated_model.legacy_model
    specification = integrated_model.feed_specification
    configuration = integrated_model.scenario_configuration

    print("Integrated GreenHub system summary")
    print("==================================")
    print("System ID:", model.system.ID)
    print("Flowsheet ID:", model.flowsheet.ID)
    print("Input workbook:", INPUT_WORKBOOK_PATH)
    print("Scenario chain:", configuration.scenario_chain)
    print("Nutrient-recovery process order:", configuration.process_order)
    print("Sample:", specification.sample_id)
    print("Selected month:", specification.selected_month)
    print("Monthly feed mass:", f"{specification.monthly_total_mass_kg:.6g} kg")
    print("Average upstream feed flow:", f"{specification.total_mass_flow_kg_hr:.6g} kg/hr")
    print("Structural-test mode:", configuration.structural_test_mode)
    print("Input basis:", configuration.input_basis)
    print("Custom-unit CAPEX: unavailable where no approved correlation exists; no unsupported cost was invented.")
    print("Product eligibility: not assessed.")
    print("Configuration comparison: engineering inventories only; not ranked.")
    print("Recovered heat and CHP electricity: zero unless a verified interface is supplied.")

    stream_labels = (
        ("digestate_feed", "Digestate from the actual Phase 5 scenario"),
        ("nutrient_rich_solids", "Nutrient-rich digestate solids"),
        ("nutrient_rich_centrate", "Separated centrate"),
        ("phosphorus_product", "Phosphorus product"),
        ("ammonium_product", "Ammonium recovery product"),
        ("potassium_concentrate", "Potassium-rich non-selective concentrate"),
        ("treated_water", "Treated-water candidate"),
        ("residual_liquor", "Final residual liquor"),
        ("phase7_wastewater", "Phase 7 wastewater"),
        ("phase7_offgas", "Phase 7 off-gas or vapor"),
        ("untreated_digestate", "Untreated digestate reference output"),
    )
    for name, label in stream_labels:
        stream = model.streams.get(name)
        if stream is not None:
            _print_stream(label, stream)

    print("\nProcess-area unit results")
    for area in integrated_model.process_areas.values():
        if not area.units:
            continue
        print(f"\n{area.name}")
        for unit in area.units.values():
            print(unit.results())
    print("\nSystem results")
    print(model.system.results())

    print("\nSelected nutrient-recovery and utility metrics")
    for name in (
        "digestate_processed_kg_hr",
        "nutrient_rich_solids_kg_hr",
        "phosphorus_product_kg_hr",
        "ammonium_product_kg_hr",
        "potassium_concentrate_kg_hr",
        "total_p_recovery_fraction",
        "total_n_recovery_fraction",
        "k_recovery_in_concentrate_fraction",
        "chemical_reagent_kg_hr",
        "fresh_process_water_kg_hr",
        "gross_electricity_kw",
        "gross_heat_demand_kw",
        "recovered_heat_used_kw",
        "external_heat_kw",
        "grid_electricity_kw",
    ):
        print(f"  {name}: {model.metrics.get(name)}")
    print(f"\n{model.validation.report}")

    print("\nDocumented integrated-model simplifications")
    for assumption in integrated_model.assumptions:
        print(f"  - {assumption}")
    print("\nHigh-priority missing-data limitations")
    for limitation in integrated_model.limitations:
        if limitation.priority == "high":
            print(f"  - {limitation.limitation_id}: {limitation.description}")
    _print_scenario_readiness()

    flowsheet_path = RESULTS_DIR / "integrated_greenhub_flowsheet.png"
    diagram_created = _save_flowsheet_diagram(model.system, flowsheet_path)
    if diagram_created:
        shutil.copyfile(flowsheet_path, RESULTS_DIR / "phase7_flowsheet.png")

    completeness_outputs = write_model_completeness_reports(integrated_model)
    integrated_outputs = save_integrated_reports(
        integrated_model,
        completeness=integrated_model.model_completeness,
    )

    comparison_models = []
    for scenario_id in ACTIVE_PHASE7_SCENARIOS:
        if scenario_id == model.scenario.scenario_id:
            comparison_models.append(snapshot_phase7_comparison(model))
        else:
            comparison_model = create_phase7_scenario(
                scenario_id,
                phase6_scenario_id=model.input_bundle.phase6_scenario_id,
                phase5_scenario_id=model.input_bundle.phase5_scenario_id,
                phase4_scenario_id=model.input_bundle.phase4_scenario_id,
                phase3_scenario_id=model.input_bundle.phase3_scenario_id,
                selected_month=model.input_bundle.selected_month,
                process_order=NUTRIENT_RECOVERY_SCENARIOS[scenario_id].default_order,
            ).simulate()
            comparison_models.append(snapshot_phase7_comparison(comparison_model))
            del comparison_model
            gc.collect()
    seasonal_result = simulate_phase7_season(
        model.scenario.scenario_id,
        phase6_scenario_id=model.input_bundle.phase6_scenario_id,
        phase5_scenario_id=model.input_bundle.phase5_scenario_id,
        phase4_scenario_id=model.input_bundle.phase4_scenario_id,
        phase3_scenario_id=model.input_bundle.phase3_scenario_id,
        process_order=model.input_bundle.process_order,
    )
    model.seasonal_result = seasonal_result
    compatibility_outputs = save_phase7_reports(
        model,
        flowsheet_path=flowsheet_path,
        scenario_models=tuple(comparison_models),
        seasonal_result=seasonal_result,
    )
    outputs = {
        **completeness_outputs,
        **integrated_outputs,
        **compatibility_outputs,
    }
    print("\nGenerated integrated and compatibility outputs")
    for label, path in outputs.items():
        if path.exists():
            print(f"  {label}: {path}")


if __name__ == "__main__":
    main()
