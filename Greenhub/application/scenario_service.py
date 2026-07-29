"""Scenario discovery and chain validation."""

from __future__ import annotations

from dataclasses import asdict

from Greenhub.scenarios import (
    BIOGAS_UPGRADING_SCENARIOS,
    DIGESTION_SCENARIOS,
    FRONT_END_SCENARIOS,
    NUTRIENT_RECOVERY_SCENARIOS,
    PROTEIN_RECOVERY_SCENARIOS,
)

from .contracts import ScenarioSelection, ValidationIssue


class ScenarioService:
    _groups = {
        "feed_preparation": FRONT_END_SCENARIOS,
        "protein_recovery": PROTEIN_RECOVERY_SCENARIOS,
        "anaerobic_digestion": DIGESTION_SCENARIOS,
        "biogas_upgrading": BIOGAS_UPGRADING_SCENARIOS,
        "nutrient_recovery": NUTRIENT_RECOVERY_SCENARIOS,
    }

    def list_scenarios(self) -> dict[str, tuple[dict[str, object], ...]]:
        return {
            group: tuple(asdict(item) for item in scenarios.values())
            for group, scenarios in self._groups.items()
        }

    def list_process_areas(self) -> tuple[dict[str, str], ...]:
        return tuple(
            {"process_area_id": key, "display_name": key.replace("_", " ").title()}
            for key in (
                "feedstock_and_characterization",
                "feed_preparation_and_primary_separation",
                "protein_recovery",
                "anaerobic_digestion",
                "biogas_conditioning_and_upgrading",
                "digestate_treatment_and_nutrient_recovery",
                "shared_utilities_and_supporting_operations",
            )
        )

    def validate_scenario_chain(self, selection: ScenarioSelection) -> tuple[ValidationIssue, ...]:
        issues = []
        selected = {
            "feed_preparation": selection.feed_preparation,
            "protein_recovery": selection.protein_recovery,
            "anaerobic_digestion": selection.anaerobic_digestion,
            "biogas_upgrading": selection.biogas_upgrading,
            "nutrient_recovery": selection.nutrient_recovery,
        }
        for group, scenario_id in selected.items():
            scenario = self._groups[group].get(scenario_id)
            if scenario is None:
                issues.append(
                    ValidationIssue(
                        code="SCENARIO_UNKNOWN",
                        severity="error",
                        message=f"Unknown {group} scenario '{scenario_id}'.",
                        blocking=True,
                        field=group,
                    )
                )
                continue
            if hasattr(scenario, "active") and not scenario.active:
                issues.append(
                    ValidationIssue(
                        code="SCENARIO_DATA_GATE",
                        severity="error",
                        message=f"Scenario '{scenario_id}' is inactive because its data gate is incomplete.",
                        blocking=True,
                        field=group,
                    )
                )
        if selection.process_order not in {"A", "B", "C", "D"}:
            issues.append(
                ValidationIssue(
                    code="PROCESS_ORDER_INVALID",
                    severity="error",
                    message="Process order must be A, B, C, or D.",
                    blocking=True,
                    field="process_order",
                )
            )
        return tuple(issues)

    def get_scenario_requirements(self, scenario_id: str) -> tuple[str, ...]:
        for scenarios in self._groups.values():
            scenario = scenarios.get(scenario_id)
            if scenario is not None:
                return tuple(getattr(scenario, "missing_data_requirements", ()))
        raise KeyError(f"Unknown scenario '{scenario_id}'.")
