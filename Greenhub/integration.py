"""Compatibility-first integrated interface for the GreenHub process model.

The scientific implementation remains in the historically named scenario
modules while this facade exposes the connected plant through process-area
terminology. This avoids moving validated code during the alpha restoration.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Mapping

import biosteam as bst

from Greenhub.input_data import INPUT_WORKBOOK_PATH, FeedSpecification
from Greenhub.phase7_inputs import Phase7InputBundle
from Greenhub.phase7_systems import Phase7Model, create_phase7_scenario


@dataclass(frozen=True)
class ScenarioConfiguration:
    """Selected scenario identifiers for one connected plant build."""

    feed_preparation: str
    protein_recovery: str
    anaerobic_digestion: str
    biogas_upgrading: str
    nutrient_recovery: str
    process_order: str
    selected_month: str
    structural_test_mode: bool
    input_basis: str

    @property
    def scenario_chain(self) -> str:
        """Return the stable workbook-facing scenario chain."""

        return "/".join(
            (
                self.feed_preparation,
                self.protein_recovery,
                self.anaerobic_digestion,
                self.biogas_upgrading,
                self.nutrient_recovery,
            )
        )


@dataclass(frozen=True)
class ProcessAreaView:
    """Named view of one process area's units, boundaries, and results."""

    key: str
    name: str
    units: Mapping[str, object]
    inlet_streams: Mapping[str, bst.Stream]
    outlet_streams: Mapping[str, bst.Stream]
    assumptions: tuple[str, ...]
    warnings: tuple[str, ...]
    validation: object | None
    metrics: Mapping[str, object]
    reports: Mapping[str, Path]


def _select_streams(
    streams: Mapping[str, bst.Stream],
    names: tuple[str, ...],
) -> dict[str, bst.Stream]:
    return {name: streams[name] for name in names if name in streams}


def _new_messages(
    messages: tuple[str, ...],
    upstream_messages: tuple[str, ...] = (),
) -> tuple[str, ...]:
    upstream = set(upstream_messages)
    return tuple(message for message in messages if message not in upstream)


def _new_units(
    current: Mapping[str, object],
    upstream: Mapping[str, object],
) -> dict[str, object]:
    return {unit_id: unit for unit_id, unit in current.items() if unit_id not in upstream}


@dataclass
class IntegratedGreenHubModel:
    """One connected GreenHub plant with meaningful process-area access."""

    legacy_model: Phase7Model
    source_workbook_path: Path = INPUT_WORKBOOK_PATH
    process_areas: dict[str, ProcessAreaView] = field(init=False)
    model_completeness: tuple[object, ...] = field(default_factory=tuple)
    integrated_report_paths: dict[str, Path] = field(default_factory=dict)
    dataset_provenance: dict[str, str] = field(init=False)

    def __post_init__(self) -> None:
        self.dataset_provenance = {
            "master_input_workbook": str(self.source_workbook_path.resolve()),
            "master_input_status": "D5 - loaded, validated, connected, tested, and reported",
            "protein_recovery_dataset_directory": str(
                Path(__file__).resolve().parent / "data" / "Protein recovery"
            ),
            "protein_recovery_dataset_status": (
                "D1-D2 - inventoried but intentionally disconnected pending required data, "
                "schema validation, and scientific calibration"
            ),
        }
        self._refresh_process_areas()

    @property
    def system(self) -> bst.System:
        return self.legacy_model.system

    @property
    def flowsheet(self) -> bst.Flowsheet:
        return self.legacy_model.flowsheet

    @property
    def units(self) -> Mapping[str, object]:
        return self.legacy_model.units

    @property
    def streams(self) -> Mapping[str, bst.Stream]:
        return self.legacy_model.streams

    @property
    def feed_specification(self) -> FeedSpecification:
        phase3 = self.legacy_model.upstream_model.upstream_model.upstream_model.upstream_model
        return phase3.feed_specification

    @property
    def scenario_configuration(self) -> ScenarioConfiguration:
        bundle = self.legacy_model.input_bundle
        return ScenarioConfiguration(
            feed_preparation=bundle.phase3_scenario_id,
            protein_recovery=bundle.phase4_scenario_id,
            anaerobic_digestion=bundle.phase5_scenario_id,
            biogas_upgrading=bundle.phase6_scenario_id,
            nutrient_recovery=bundle.scenario_id,
            process_order=bundle.process_order,
            selected_month=bundle.selected_month,
            structural_test_mode=bundle.structural_test_mode,
            input_basis=bundle.input_basis,
        )

    @property
    def warnings(self) -> tuple[str, ...]:
        return self.legacy_model.warnings

    @property
    def assumptions(self) -> tuple[str, ...]:
        phase6 = self.legacy_model.upstream_model
        phase5 = phase6.upstream_model
        phase4 = phase5.upstream_model
        return tuple(
            dict.fromkeys(
                (
                    *phase4.assumptions,
                    *phase5.assumptions,
                    *phase6.assumptions,
                    *self.legacy_model.assumptions,
                )
            )
        )

    @property
    def validation_report(self) -> object | None:
        return self.legacy_model.validation

    @property
    def metrics(self) -> Mapping[str, object]:
        return self.legacy_model.metrics

    @property
    def report_paths(self) -> Mapping[str, Path]:
        return {**self.legacy_model.reports, **self.integrated_report_paths}

    @property
    def limitations(self) -> tuple[object, ...]:
        phase6 = self.legacy_model.upstream_model
        phase5 = phase6.upstream_model
        return tuple(
            dict.fromkeys(
                (
                    *phase5.limitations,
                    *phase6.limitations,
                    *self.legacy_model.limitations,
                )
            )
        )

    def simulate(self) -> "IntegratedGreenHubModel":
        """Simulate the existing connected graph and refresh area views."""

        self.legacy_model.simulate()
        self._refresh_process_areas()
        return self

    def get_process_area(self, key: str) -> ProcessAreaView:
        """Return one process area or raise an informative key error."""

        try:
            return self.process_areas[key]
        except KeyError as error:
            choices = ", ".join(self.process_areas)
            raise KeyError(f"Unknown process area '{key}'. Available areas: {choices}.") from error

    def _refresh_process_areas(self) -> None:
        model = self.legacy_model
        phase6 = model.upstream_model
        phase5 = phase6.upstream_model
        phase4 = phase5.upstream_model
        phase3 = phase4.upstream_model
        streams = model.streams

        phase4_units = _new_units(phase4.units, phase3.units)
        phase5_units = _new_units(phase5.units, phase4.units)
        phase6_units = _new_units(phase6.units, phase5.units)
        phase7_units = _new_units(model.units, phase6.units)

        self.process_areas = {
            "feedstock_and_characterization": ProcessAreaView(
                key="feedstock_and_characterization",
                name="Feedstock and Characterization",
                units={},
                inlet_streams=_select_streams(streams, ("feed", "roadside_grass", "measured_liquid_fraction")),
                outlet_streams=_select_streams(streams, ("feed", "roadside_grass", "measured_liquid_fraction")),
                assumptions=(),
                warnings=tuple(phase3.characterization.warnings),
                validation=None,
                metrics={
                    "monthly_total_mass_kg": phase3.feed_specification.monthly_total_mass_kg,
                    "average_mass_flow_kg_hr": phase3.feed_specification.total_mass_flow_kg_hr,
                },
                reports={},
            ),
            "feed_preparation_and_primary_separation": ProcessAreaView(
                key="feed_preparation_and_primary_separation",
                name="Feed Preparation and Primary Separation",
                units=dict(phase3.units),
                inlet_streams=_select_streams(streams, ("feed", "roadside_grass", "measured_liquid_fraction")),
                outlet_streams=_select_streams(
                    streams,
                    ("clarified_liquid", "fibre_cake", "primary_sludge", "preparation_rejects", "pef_documented_loss"),
                ),
                assumptions=(),
                warnings=phase3.warnings,
                validation=phase3.validation,
                metrics=phase3.metrics,
                reports={},
            ),
            "protein_recovery": ProcessAreaView(
                key="protein_recovery",
                name="Protein Recovery",
                units=phase4_units,
                inlet_streams=_select_streams(streams, ("clarified_protein_rich_liquid", "clarified_liquid")),
                outlet_streams=_select_streams(
                    streams,
                    ("dry_protein_product", "conditioned_protein_depleted_liquid", "dryer_exhaust"),
                ),
                assumptions=phase4.assumptions,
                warnings=_new_messages(phase4.warnings, phase3.warnings),
                validation=phase4.validation,
                metrics=phase4.metrics,
                reports=phase4.reports,
            ),
            "anaerobic_digestion": ProcessAreaView(
                key="anaerobic_digestion",
                name="Anaerobic Digestion",
                units=phase5_units,
                inlet_streams=_select_streams(streams, ("digester_feed",)),
                outlet_streams=_select_streams(streams, ("raw_biogas", "digestate", "uncaptured_biogas")),
                assumptions=phase5.assumptions,
                warnings=_new_messages(phase5.warnings, phase4.warnings),
                validation=phase5.validation,
                metrics=phase5.metrics,
                reports=phase5.reports,
            ),
            "biogas_conditioning_and_upgrading": ProcessAreaView(
                key="biogas_conditioning_and_upgrading",
                name="Biogas Conditioning and Upgrading",
                units=phase6_units,
                inlet_streams=_select_streams(streams, ("raw_biogas",)),
                outlet_streams=_select_streams(
                    streams,
                    ("biomethane", "gas_product", "reject_gas", "technology_wastewater", "technology_spent_material"),
                ),
                assumptions=phase6.assumptions,
                warnings=_new_messages(phase6.warnings, phase5.warnings),
                validation=phase6.validation,
                metrics=phase6.metrics,
                reports=phase6.reports,
            ),
            "digestate_treatment_and_nutrient_recovery": ProcessAreaView(
                key="digestate_treatment_and_nutrient_recovery",
                name="Digestate Treatment and Nutrient Recovery",
                units=phase7_units,
                inlet_streams=_select_streams(streams, ("digestate_feed", "digestate")),
                outlet_streams=_select_streams(
                    streams,
                    (
                        "nutrient_rich_solids",
                        "phosphorus_product",
                        "ammonium_product",
                        "potassium_concentrate",
                        "treated_water",
                        "residual_liquor",
                        "phase7_wastewater",
                        "phase7_offgas",
                        "untreated_digestate",
                    ),
                ),
                assumptions=model.assumptions,
                warnings=_new_messages(model.warnings, phase6.warnings),
                validation=model.validation,
                metrics=model.metrics,
                reports=model.reports,
            ),
            "shared_utilities_and_supporting_operations": ProcessAreaView(
                key="shared_utilities_and_supporting_operations",
                name="Shared Utilities and Supporting Operations",
                units={},
                inlet_streams={},
                outlet_streams={},
                assumptions=(
                    "No active plant-wide CHP or shared-utility network is implemented; utility production remains a documented gap.",
                ),
                warnings=(
                    "Shared utility production is not yet implemented, so recovered heat and generated electricity are not inferred.",
                ),
                validation=None,
                metrics={
                    "recovered_heat_available_kw": model.parameters.get("recovered_heat_available_kw", 0.0),
                    "chp_electricity_available_kw": model.parameters.get("chp_electricity_available_kw", 0.0),
                },
                reports={},
            ),
        }


def create_integrated_greenhub_system(
    scenario_id: str | None = None,
    *,
    biogas_upgrading_scenario_id: str | None = None,
    anaerobic_digestion_scenario_id: str | None = None,
    protein_recovery_scenario_id: str | None = None,
    feed_preparation_scenario_id: str | None = None,
    selected_month: str | None = None,
    process_order: str | None = None,
    workbook_path: Path = INPUT_WORKBOOK_PATH,
    parameter_overrides: Mapping[str, object] | None = None,
    input_bundle: Phase7InputBundle | None = None,
) -> IntegratedGreenHubModel:
    """Build the complete plant through the established, tested factory.

    Historical workbook IDs remain unchanged. The longer argument names are
    intentional user-facing aliases for the old phase-numbered arguments.
    """

    legacy_model = create_phase7_scenario(
        scenario_id,
        phase6_scenario_id=biogas_upgrading_scenario_id,
        phase5_scenario_id=anaerobic_digestion_scenario_id,
        phase4_scenario_id=protein_recovery_scenario_id,
        phase3_scenario_id=feed_preparation_scenario_id,
        selected_month=selected_month,
        process_order=process_order,
        workbook_path=workbook_path,
        parameter_overrides=parameter_overrides,
        input_bundle=input_bundle,
    )
    return IntegratedGreenHubModel(legacy_model, source_workbook_path=workbook_path)
