"""BioSTEAM flowsheet and isolated system factories for GreenHub."""

from __future__ import annotations

from dataclasses import dataclass, field, replace
from pathlib import Path
from typing import Any, Mapping

import biosteam as bst

from Greenhub.characterization import CharacterizationResult
from Greenhub.characterization import characterize_feed
from Greenhub.input_data import FeedSpecification
from Greenhub.phase3_inputs import INPUT_WORKBOOK_PATH, Phase3InputBundle, load_phase3_inputs
from Greenhub.phase3_units import (
    FeedPreparation,
    PrimaryCentrifuge,
    PulsedElectricField,
    ScrewPress,
    centrifuge_parameters_from_mapping,
    pef_parameters_from_mapping,
    preparation_parameters_from_mapping,
    press_parameters_from_mapping,
)
from Greenhub.phase4_inputs import Phase4InputBundle, load_phase4_inputs
from Greenhub.phase4_units import (
    AcidificationMixer,
    CakeWasher,
    MechanicalDewatering,
    NeutralizationMixer,
    ProteinDryer,
    ProteinPrecipitation,
    ProteinSeparator,
    acidification_parameters_from_mapping,
    dewatering_parameters_from_mapping,
    dryer_parameters_from_mapping,
    neutralization_parameters_from_mapping,
    precipitation_parameters_from_mapping,
    separator_parameters_from_mapping,
    washing_parameters_from_mapping,
)
from Greenhub.phase5_inputs import Phase5InputBundle, load_phase5_inputs
from Greenhub.phase5_units import (
    AnaerobicDigester,
    BiogasDisengagement,
    DigesterFeedConditioner,
    conditioning_parameters_from_mapping,
    digestion_parameters_from_mapping,
    gas_partition_parameters_from_mapping,
)
from Greenhub.phase6_inputs import Phase6InputBundle, load_phase6_inputs
from Greenhub.phase6_units import (
    AmmoniaRemoval,
    CondensateSeparator,
    HydrogenSulfideRemoval,
    ParticleSiloxaneFilter,
    RawBiogasCooler,
    pretreatment_parameters_from_mapping,
)
from Greenhub.phase6_upgrading import (
    GasWaterSeparator,
    MEAAbsorber,
    MEAReboiler,
    MEAStripper,
    LeanHeatRecovery,
    MembraneStage,
    PressureSwingAdsorber,
    RefluxCondenser,
    RichLeanHeatExchanger,
    WaterAbsorber,
    WaterFlashTank,
    WaterRegenerator,
    feed_quality_limits_from_mapping,
    mea_parameters_from_mapping,
    membrane_parameters_from_mapping,
    psa_parameters_from_mapping,
    water_scrubbing_parameters_from_mapping,
)
from Greenhub.scenarios import (
    DigestionScenario,
    BiogasUpgradingScenario,
    FrontEndScenario,
    ProteinRecoveryScenario,
    get_digestion_scenario,
    get_biogas_upgrading_scenario,
    get_front_end_scenario,
    get_protein_recovery_scenario,
)
from Greenhub.separator import ResolvedSeparatorSplits, SeparatorParameters
from Greenhub.settings import OPERATING_HOURS_PER_YEAR
from Greenhub.units import create_units

FLOWSHEET_ID = "greenhub"
SYSTEM_ID = "greenhub_phase2_sys"
PHASE3_SYSTEM_ID = "greenhub_phase3"
PHASE4_SYSTEM_ID = "greenhub_phase4"
PHASE5_SYSTEM_ID = "greenhub_phase5"
PHASE6_SYSTEM_ID = "greenhub_phase6"


@dataclass(frozen=True)
class GreenHubModel:
    """Structured container for all useful active Phase 2 model objects."""

    flowsheet: bst.Flowsheet
    system: bst.System
    units: dict[str, object]
    streams: dict[str, bst.Stream]
    feed_specification: FeedSpecification
    characterization: CharacterizationResult
    separator_splits: ResolvedSeparatorSplits


def create_greenhub_flowsheet(ID: str = FLOWSHEET_ID) -> bst.Flowsheet:
    """Create and activate a fresh named flowsheet for safe in-session rebuilds."""

    flowsheet = bst.Flowsheet(ID)
    bst.main_flowsheet.set_flowsheet(flowsheet)
    bst.main_flowsheet.clear()
    return flowsheet


def create_greenhub_system(
    feed_specification: FeedSpecification | None = None,
    separator_parameters: SeparatorParameters | None = None,
) -> GreenHubModel:
    """Build the transparent no-recycle Phase 2 system from the flowsheet."""

    flowsheet = create_greenhub_flowsheet()
    unit_objects = create_units(feed_specification, separator_parameters)
    streams = {
        "feed": unit_objects["feed"],
        "stored_liquid_fraction": unit_objects["stored_liquid_fraction"],
        "clarified_liquid": unit_objects["clarified_liquid"],
        "wet_solids": unit_objects["wet_solids"],
    }
    system = bst.main_flowsheet.create_system(
        ID=SYSTEM_ID,
        ends=(streams["clarified_liquid"], streams["wet_solids"]),
        operating_hours=OPERATING_HOURS_PER_YEAR,
    )
    return GreenHubModel(
        flowsheet=flowsheet,
        system=system,
        units={"T101": unit_objects["T101"], "S101": unit_objects["S101"]},
        streams=streams,
        feed_specification=unit_objects["feed_specification"],
        characterization=unit_objects["characterization"],
        separator_splits=unit_objects["separator_splits"],
    )


@dataclass
class Phase3Model:
    """Structured Phase 3 bundle with an end-to-end simulation method."""

    flowsheet: bst.Flowsheet
    system: bst.System
    scenario: FrontEndScenario
    units: dict[str, object]
    streams: dict[str, bst.Stream]
    parameters: dict[str, object]
    input_bundle: Phase3InputBundle
    feed_specification: FeedSpecification
    characterization: CharacterizationResult
    warnings: tuple[str, ...]
    raw_liquid_interface: object | None = None
    validation: object | None = None
    metrics: dict[str, object] = field(default_factory=dict)

    def simulate(self) -> "Phase3Model":
        """Simulate, validate, and calculate the standardized result bundle."""

        from Greenhub.phase3_metrics import create_raw_liquid_interface, calculate_phase3_metrics
        from Greenhub.phase3_validation import validate_phase3_model

        self.system.simulate()
        self.raw_liquid_interface = create_raw_liquid_interface(self)
        self.validation = validate_phase3_model(self)
        self.metrics = calculate_phase3_metrics(self, self.validation)
        return self


def _create_phase3_flowsheet(scenario_id: str) -> bst.Flowsheet:
    """Create an isolated named flowsheet so repeated scenario builds are safe."""

    flowsheet = bst.Flowsheet(f"greenhub_phase3_{scenario_id.lower()}")
    bst.main_flowsheet.set_flowsheet(flowsheet)
    bst.main_flowsheet.clear()
    return flowsheet


def create_phase3_scenario(
    scenario_id: str | None = None,
    *,
    selected_month: str | None = None,
    workbook_path: Path = INPUT_WORKBOOK_PATH,
    parameter_overrides: Mapping[str, object] | None = None,
    input_bundle: Phase3InputBundle | None = None,
) -> Phase3Model:
    """Build one fresh F0-F3 system without simulating it."""

    bundle = input_bundle or load_phase3_inputs(
        workbook_path,
        scenario_id=scenario_id,
        selected_month=selected_month,
    )
    if scenario_id and bundle.scenario_id != scenario_id.upper():
        raise ValueError("Provided Phase3InputBundle does not match requested scenario.")
    scenario = get_front_end_scenario(bundle.scenario_id)
    values = dict(bundle.parameter_values)
    if parameter_overrides:
        values.update(parameter_overrides)
    flowsheet = _create_phase3_flowsheet(scenario.scenario_id)

    centrifuge_parameters = centrifuge_parameters_from_mapping(values)
    units: dict[str, object] = {}
    streams: dict[str, bst.Stream] = {}
    parameters: dict[str, object] = {
        "values": values,
        "centrifuge": centrifuge_parameters,
    }
    warnings = list(bundle.warnings)

    if scenario.entry_mode == "measured_liquid":
        characterization = characterize_feed(
            bundle.feed_specification,
            ID="measured_liquid_fraction",
        )
        feed = characterization.stream
        if characterization.physical.density_kg_m3:
            density_values = dict(values)
            density_values["raw_liquid_density_kg_m3"] = characterization.physical.density_kg_m3
            centrifuge_parameters = centrifuge_parameters_from_mapping(density_values)
            parameters["centrifuge"] = centrifuge_parameters
        T101 = bst.StorageTank(
            ID="T101",
            ins=feed,
            outs="raw_liquid_fraction",
            tau=float(values.get("measured_liquid_storage_time_h", 24.0)),
            vessel_type="Floating roof",
        )
        units["T101"] = T101
        raw_liquid = T101 - 0
        streams.update(
            feed=feed,
            measured_liquid_fraction=feed,
            raw_liquid_fraction=raw_liquid,
        )
        ends: list[bst.Stream] = []
        warnings.append(
            "T101 may operate below its validated cost-correlation range; the BioSTEAM warning is retained."
        )
    else:
        characterization = characterize_feed(
            bundle.feed_specification,
            ID="roadside_grass",
        )
        feed = characterization.stream
        preparation_parameters = preparation_parameters_from_mapping(values)
        U101 = FeedPreparation(
            ID="U101",
            ins=feed,
            outs=("prepared_roadside_grass", "preparation_rejects"),
            parameters=preparation_parameters,
        )
        units["U101"] = U101
        parameters["preparation"] = preparation_parameters
        press_inlet = U101 - 0
        ends = [U101 - 1]
        streams.update(
            feed=feed,
            roadside_grass=feed,
            prepared_grass=U101 - 0,
            preparation_rejects=U101 - 1,
        )

        pef_parameters = None
        if scenario.pef_enabled:
            pef_parameters = pef_parameters_from_mapping(values)
            U201 = PulsedElectricField(
                ID="U201",
                ins=press_inlet,
                outs=("pef_treated_grass", "pef_documented_loss"),
                parameters=pef_parameters,
            )
            units["U201"] = U201
            parameters["pef"] = pef_parameters
            press_inlet = U201 - 0
            ends.append(U201 - 1)
            streams.update(
                pef_treated_grass=U201 - 0,
                pef_documented_loss=U201 - 1,
            )
            warnings.append(
                "PEF release and juice-yield enhancement are empirical structural assumptions, not kinetic predictions."
            )

        press_parameters = press_parameters_from_mapping(values, pef=pef_parameters)
        S201 = ScrewPress(
            ID="S201",
            ins=press_inlet,
            outs=("pressed_fibre_cake", "raw_liquid_fraction"),
            parameters=press_parameters,
        )
        units["S201"] = S201
        parameters["press"] = press_parameters
        raw_liquid = S201 - 1
        ends.append(S201 - 0)
        streams.update(
            fibre_cake=S201 - 0,
            raw_liquid_fraction=raw_liquid,
        )

    wash_water = bst.Stream("centrifuge_wash_water")
    polymer = bst.Stream("centrifuge_flocculant")
    C301 = PrimaryCentrifuge(
        ID="C301",
        ins=(raw_liquid, wash_water, polymer),
        outs=("clarified_protein_rich_liquid", "primary_sludge"),
        parameters=centrifuge_parameters,
    )
    units["C301"] = C301
    streams.update(
        centrifuge_wash_water=wash_water,
        centrifuge_flocculant=polymer,
        clarified_liquid=C301 - 0,
        primary_sludge=C301 - 1,
    )
    ends.extend((C301 - 0, C301 - 1))

    system = bst.main_flowsheet.create_system(
        ID=f"{PHASE3_SYSTEM_ID}_{scenario.scenario_id.lower()}",
        ends=tuple(ends),
        operating_hours=OPERATING_HOURS_PER_YEAR,
    )
    active_custom_unit_ids = [
        ID for ID in ("U101", "U201", "S201", "C301") if ID in units
    ]
    active_custom_units = ", ".join(active_custom_unit_ids)
    cost_verb = "has" if len(active_custom_unit_ids) == 1 else "have"
    warnings.extend(
        (
            "No transfer pump is active because no pressure-rise requirement is available; pumping electricity is zero.",
            f"{active_custom_units} {cost_verb} no purchase cost because no approved GreenHub cost correlation is available.",
        )
    )
    if bundle.structural_test_mode:
        warnings.append(
            "Structural-test mode is active; quality-class E inputs are not final measured or literature assumptions."
        )
    return Phase3Model(
        flowsheet,
        system,
        scenario,
        units,
        streams,
        parameters,
        bundle,
        bundle.feed_specification,
        characterization,
        tuple(dict.fromkeys(warnings)),
    )


def create_measured_liquid_system(**kwargs) -> Phase3Model:
    """Build F0 measured-liquid storage and primary centrifugation."""

    return create_phase3_scenario("F0", **kwargs)


def create_no_pef_front_end_system(**kwargs) -> Phase3Model:
    """Build F1 roadside-grass pressing without PEF."""

    return create_phase3_scenario("F1", **kwargs)


def create_pef_front_end_system(
    *,
    sensitivity_ready: bool = False,
    **kwargs,
) -> Phase3Model:
    """Build F2 or sensitivity-ready F3 PEF front end."""

    return create_phase3_scenario("F3" if sensitivity_ready else "F2", **kwargs)


def simulate_phase3_season(
    scenario_id: str,
    *,
    workbook_path: Path = INPUT_WORKBOOK_PATH,
    months: tuple[str, ...] = (
        "January",
        "February",
        "March",
        "April",
        "May",
        "June",
        "July",
        "August",
        "September",
        "October",
        "November",
        "December",
    ),
) -> object:
    """Simulate all available months and report missing seasonal inputs."""

    from Greenhub.phase3_metrics import aggregate_monthly_metrics

    models = []
    warnings = []
    for month in months:
        try:
            model = create_phase3_scenario(
                scenario_id,
                selected_month=month,
                workbook_path=workbook_path,
            )
            model.simulate()
            models.append(model)
        except ValueError as error:
            warnings.append(f"{month}: {error}")
    if not models:
        raise ValueError(f"No monthly Phase 3 simulations succeeded for scenario {scenario_id}.")
    return aggregate_monthly_metrics(models, tuple(warnings))


@dataclass
class Phase4Model:
    """Structured Phase 4 bundle with an end-to-end simulation method."""

    flowsheet: bst.Flowsheet
    system: bst.System
    scenario: ProteinRecoveryScenario
    upstream_model: Phase3Model
    units: dict[str, object]
    streams: dict[str, bst.Stream]
    parameters: dict[str, object]
    input_bundle: Phase4InputBundle
    warnings: tuple[str, ...]
    assumptions: tuple[str, ...]
    reports: dict[str, Path] = field(default_factory=dict)
    validation: object | None = None
    metrics: dict[str, object] = field(default_factory=dict)

    def simulate(self) -> "Phase4Model":
        """Simulate the complete plant, then validate and calculate metrics."""

        from Greenhub.phase3_metrics import calculate_phase3_metrics, create_raw_liquid_interface
        from Greenhub.phase3_validation import validate_phase3_model
        from Greenhub.phase4_metrics import calculate_phase4_metrics
        from Greenhub.phase4_validation import validate_phase4_model

        self.system.simulate()
        self.upstream_model.raw_liquid_interface = create_raw_liquid_interface(self.upstream_model)
        self.upstream_model.validation = validate_phase3_model(self.upstream_model)
        self.upstream_model.metrics = calculate_phase3_metrics(
            self.upstream_model,
            self.upstream_model.validation,
        )
        self.validation = validate_phase4_model(self)
        self.metrics = calculate_phase4_metrics(self, self.validation)
        return self


def _phase4_side_products(upstream: Phase3Model) -> list[bst.Stream]:
    """Return upstream boundary outlets other than clarified liquid."""

    names = (
        "preparation_rejects",
        "pef_documented_loss",
        "fibre_cake",
        "primary_sludge",
    )
    return [upstream.streams[name] for name in names if name in upstream.streams]


def create_phase4_scenario(
    scenario_id: str | None = None,
    *,
    phase3_scenario_id: str | None = None,
    selected_month: str | None = None,
    workbook_path: Path = INPUT_WORKBOOK_PATH,
    parameter_overrides: Mapping[str, object] | None = None,
    input_bundle: Phase4InputBundle | None = None,
) -> Phase4Model:
    """Build one fresh PR0-PR6 model without simulating it.

    PR4-PR6 remain deliberately inactive until their scenario-specific data
    requirements are supplied. The active PR0-PR3 systems share the same
    clarified-liquid inlet and common output naming.
    """

    bundle = input_bundle or load_phase4_inputs(
        workbook_path,
        scenario_id=scenario_id,
        phase3_scenario_id=phase3_scenario_id,
        selected_month=selected_month,
    )
    if scenario_id and bundle.scenario_id != scenario_id.upper():
        raise ValueError("Provided Phase4InputBundle does not match requested scenario.")
    if phase3_scenario_id and bundle.phase3_scenario_id != phase3_scenario_id.upper():
        raise ValueError("Provided Phase4InputBundle does not match requested upstream scenario.")
    scenario = get_protein_recovery_scenario(bundle.scenario_id)
    if not scenario.active:
        requirements = ", ".join(scenario.missing_data_requirements)
        raise NotImplementedError(
            f"Phase 4 scenario {scenario.scenario_id} is inactive because the following "
            f"data are missing: {requirements}."
        )

    values = dict(bundle.parameter_values)
    if parameter_overrides:
        values.update(parameter_overrides)
    upstream = create_phase3_scenario(
        bundle.phase3_scenario_id,
        selected_month=bundle.selected_month,
        workbook_path=workbook_path,
        parameter_overrides=parameter_overrides,
    )
    flowsheet = upstream.flowsheet
    units = dict(upstream.units)
    streams = dict(upstream.streams)
    clarified = upstream.streams["clarified_liquid"]
    streams["clarified_protein_rich_liquid"] = clarified
    parameters: dict[str, object] = {
        "values": values,
        "phase3": upstream.parameters,
    }
    warnings = list(bundle.warnings)
    warnings.extend(upstream.warnings)
    assumptions = [
        "Phase 4 pH values are screening-level metadata, not electrolyte-equilibrium predictions.",
        "Protein precipitation and heat coagulation are mass-conserving empirical pool transfers.",
        "Custom Phase 4 units have no CAPEX because no approved project correlation is available.",
        "Drying air is utility-only; no air mass, humidity, or recycle calculation is claimed.",
    ]
    side_products = _phase4_side_products(upstream)

    if scenario.scenario_id == "PR0":
        M403 = bst.Mixer(
            ID="M403",
            ins=clarified,
            outs="conditioned_protein_depleted_liquid",
        )
        dry_product = bst.Stream("dry_protein_product")
        dryer_exhaust = bst.Stream("dryer_exhaust")
        acid_solution = bst.Stream("acid_solution")
        base_solution = bst.Stream("base_solution")
        wash_water = bst.Stream("protein_cake_wash_water")
        units["M403"] = M403
        streams.update(
            acid_solution=acid_solution,
            base_solution=base_solution,
            protein_cake_wash_water=wash_water,
            protein_depleted_liquid=clarified,
            conditioned_protein_depleted_liquid=M403 - 0,
            dry_protein_product=dry_product,
            dryer_exhaust=dryer_exhaust,
        )
        final_ends = side_products + [M403 - 0]
        assumptions.append("PR0 bypasses protein recovery and preserves clarified-liquid protein for later pathways.")
    else:
        titration_points = tuple(
            (point.acid_dose_kg_m3, point.resulting_pH)
            for point in bundle.titration_points
        )
        acid_parameters = acidification_parameters_from_mapping(
            values,
            enabled=scenario.acid_enabled,
            titration_points=titration_points,
        )
        precipitation_parameters = precipitation_parameters_from_mapping(
            values,
            acid_enabled=scenario.acid_enabled,
            heat_enabled=scenario.heat_enabled,
        )
        separator_parameters = separator_parameters_from_mapping(values)
        washing_parameters = washing_parameters_from_mapping(
            values,
            enabled=scenario.wash_enabled,
        )
        dewatering_parameters = dewatering_parameters_from_mapping(values)
        drying_parameters = dryer_parameters_from_mapping(values)
        neutralization_parameters = neutralization_parameters_from_mapping(
            values,
            acid_enabled=scenario.acid_enabled,
        )
        parameters.update(
            acidification=acid_parameters,
            precipitation=precipitation_parameters,
            separator=separator_parameters,
            washing=washing_parameters,
            dewatering=dewatering_parameters,
            drying=drying_parameters,
            neutralization=neutralization_parameters,
        )

        acid_solution = bst.Stream("acid_solution")
        M401 = AcidificationMixer(
            ID="M401",
            ins=(clarified, acid_solution),
            outs="acidified_protein_liquid",
            parameters=acid_parameters,
        )
        precipitation_feed = M401 - 0
        units["M401"] = M401
        streams.update(
            acid_solution=acid_solution,
            acidified_protein_liquid=M401 - 0,
        )

        if scenario.heat_enabled:
            H401 = bst.HXutility(
                ID="H401",
                ins=precipitation_feed,
                outs="heated_protein_liquid",
                T=precipitation_parameters.precipitation_temperature_C + 273.15,
            )
            precipitation_feed = H401 - 0
            units["H401"] = H401
            streams["heated_protein_liquid"] = H401 - 0
        else:
            streams["heated_protein_liquid"] = precipitation_feed

        R401 = ProteinPrecipitation(
            ID="R401",
            ins=precipitation_feed,
            outs="protein_precipitation_slurry",
            parameters=precipitation_parameters,
        )
        C401 = ProteinSeparator(
            ID="C401",
            ins=R401 - 0,
            outs=("wet_protein_cake", "protein_centrate"),
            parameters=separator_parameters,
        )
        units.update(R401=R401, C401=C401)
        streams.update(
            protein_precipitation_slurry=R401 - 0,
            wet_protein_cake=C401 - 0,
            protein_centrate=C401 - 1,
        )

        wash_water = bst.Stream("protein_cake_wash_water")
        wash_filtrate = bst.Stream("protein_cake_wash_filtrate")
        cake_to_dewatering = C401 - 0
        liquid_side_streams: list[bst.Stream] = [C401 - 1]
        if scenario.wash_enabled:
            W401 = CakeWasher(
                ID="W401",
                ins=(C401 - 0, wash_water),
                outs=("washed_protein_cake", wash_filtrate),
                parameters=washing_parameters,
            )
            units["W401"] = W401
            cake_to_dewatering = W401 - 0
            liquid_side_streams.append(W401 - 1)
            streams.update(
                washed_protein_cake=W401 - 0,
                protein_cake_wash_filtrate=W401 - 1,
            )
        else:
            streams.update(
                washed_protein_cake=C401 - 0,
                protein_cake_wash_filtrate=wash_filtrate,
            )
        streams["protein_cake_wash_water"] = wash_water

        D401 = MechanicalDewatering(
            ID="D401",
            ins=cake_to_dewatering,
            outs=("dewatered_protein_cake", "dewatering_filtrate"),
            parameters=dewatering_parameters,
        )
        DR401 = ProteinDryer(
            ID="DR401",
            ins=D401 - 0,
            outs=("dry_protein_product", "dryer_exhaust"),
            parameters=drying_parameters,
        )
        liquid_side_streams.append(D401 - 1)
        M402 = bst.Mixer(
            ID="M402",
            ins=tuple(liquid_side_streams),
            outs="protein_depleted_liquid",
        )
        base_solution = bst.Stream("base_solution")
        M403 = NeutralizationMixer(
            ID="M403",
            ins=(M402 - 0, base_solution),
            outs="conditioned_protein_depleted_liquid",
            parameters=neutralization_parameters,
        )
        units.update(D401=D401, DR401=DR401, M402=M402, M403=M403)
        streams.update(
            dewatered_protein_cake=D401 - 0,
            dewatering_filtrate=D401 - 1,
            dry_protein_product=DR401 - 0,
            dryer_exhaust=DR401 - 1,
            protein_depleted_liquid=M402 - 0,
            base_solution=base_solution,
            conditioned_protein_depleted_liquid=M403 - 0,
        )
        final_ends = side_products + [DR401 - 0, DR401 - 1, M403 - 0]
        warnings.extend(
            (
                "The protein separator, washer, dewatering unit, dryer, and mixers have no purchase-cost model.",
                "The low-temperature belt dryer is a structural selection suitable for wet cake; vendor data remain required.",
            )
        )

    system = bst.main_flowsheet.create_system(
        ID=(
            f"{PHASE4_SYSTEM_ID}_{bundle.phase3_scenario_id.lower()}_"
            f"{scenario.scenario_id.lower()}"
        ),
        ends=tuple(final_ends),
        operating_hours=OPERATING_HOURS_PER_YEAR,
    )
    if bundle.structural_test_mode:
        warnings.append(
            "Phase 4 structural-test mode is active; class E values are placeholders, not design data."
        )
    return Phase4Model(
        flowsheet=flowsheet,
        system=system,
        scenario=scenario,
        upstream_model=upstream,
        units=units,
        streams=streams,
        parameters=parameters,
        input_bundle=bundle,
        warnings=tuple(dict.fromkeys(warnings)),
        assumptions=tuple(assumptions),
    )


def create_acid_precipitation_system(**kwargs) -> Phase4Model:
    """Build active PR1 acid precipitation."""

    return create_phase4_scenario("PR1", **kwargs)


def create_heat_coagulation_system(**kwargs) -> Phase4Model:
    """Build active PR2 heat coagulation."""

    return create_phase4_scenario("PR2", **kwargs)


def create_combined_protein_recovery_system(**kwargs) -> Phase4Model:
    """Build active PR3 combined acid, heat, and cake washing."""

    return create_phase4_scenario("PR3", **kwargs)


def create_lactic_fermentation_protein_system(**kwargs) -> Phase4Model:
    """Raise the documented PR4 missing-data status."""

    return create_phase4_scenario("PR4", **kwargs)


def create_co2_precipitation_system(**kwargs) -> Phase4Model:
    """Raise the documented PR5 missing-data status."""

    return create_phase4_scenario("PR5", **kwargs)


def create_ultrafiltration_protein_system(**kwargs) -> Phase4Model:
    """Raise the documented PR6 missing-data status."""

    return create_phase4_scenario("PR6", **kwargs)


def simulate_phase4_season(
    scenario_id: str,
    *,
    phase3_scenario_id: str | None = None,
    workbook_path: Path = INPUT_WORKBOOK_PATH,
    months: tuple[str, ...] = (
        "January",
        "February",
        "March",
        "April",
        "May",
        "June",
        "July",
        "August",
        "September",
        "October",
        "November",
        "December",
    ),
) -> object:
    """Simulate monthly Phase 4 rates and aggregate annual quantities."""

    from Greenhub.phase4_metrics import aggregate_monthly_phase4_metrics

    models = []
    warnings = []
    for month in months:
        try:
            model = create_phase4_scenario(
                scenario_id,
                phase3_scenario_id=phase3_scenario_id,
                selected_month=month,
                workbook_path=workbook_path,
            ).simulate()
            models.append(model)
        except ValueError as error:
            warnings.append(f"{month}: {error}")
    if not models:
        raise ValueError(f"No monthly Phase 4 simulations succeeded for scenario {scenario_id}.")
    return aggregate_monthly_phase4_metrics(models, tuple(warnings))


@dataclass
class Phase5Model:
    """Structured Phase 5 bundle with nested upstream models and named outputs."""

    flowsheet: bst.Flowsheet
    system: bst.System
    scenario: DigestionScenario
    upstream_model: Phase4Model
    units: dict[str, object]
    streams: dict[str, bst.Stream]
    parameters: dict[str, object]
    input_bundle: Phase5InputBundle
    warnings: tuple[str, ...]
    assumptions: tuple[str, ...]
    reactions: dict[str, object] = field(default_factory=dict)
    data_needs: tuple[str, ...] = ()
    limitations: tuple[object, ...] = ()
    reports: dict[str, Path] = field(default_factory=dict)
    validation: object | None = None
    metrics: dict[str, object] = field(default_factory=dict)

    def simulate(self) -> "Phase5Model":
        """Simulate the complete plant and refresh all nested validation results."""

        from Greenhub.phase3_metrics import calculate_phase3_metrics, create_raw_liquid_interface
        from Greenhub.phase3_validation import validate_phase3_model
        from Greenhub.phase4_metrics import calculate_phase4_metrics
        from Greenhub.phase4_validation import validate_phase4_model
        from Greenhub.phase5_limitations import build_limitations
        from Greenhub.phase5_metrics import calculate_phase5_metrics
        from Greenhub.phase5_validation import validate_phase5_model

        self.system.simulate()
        phase3 = self.upstream_model.upstream_model
        phase3.raw_liquid_interface = create_raw_liquid_interface(phase3)
        phase3.validation = validate_phase3_model(phase3)
        phase3.metrics = calculate_phase3_metrics(phase3, phase3.validation)
        self.upstream_model.validation = validate_phase4_model(self.upstream_model)
        self.upstream_model.metrics = calculate_phase4_metrics(
            self.upstream_model,
            self.upstream_model.validation,
        )
        self.validation = validate_phase5_model(self)
        self.metrics = calculate_phase5_metrics(self, self.validation)
        self.limitations = build_limitations(self)
        reactor = self.units["R501"]
        self.reactions = {
            "architecture": (
                "hydrolysis",
                "acidogenesis",
                "acetogenesis",
                "methanogenesis",
                "biomass formation",
                "mineralization",
                "sulphate reduction",
                "residual COD allocation",
            ),
            "calculation_mode": reactor.parameters.calculation_mode,
            "hydrolysis": tuple(dict(row) for row in reactor.hydrolysis_rows),
            "acidogenesis": tuple(dict(row) for row in reactor.acidogenesis_rows),
            "acetogenesis": tuple(dict(row) for row in reactor.acetogenesis_rows),
            "methanogenesis": tuple(dict(row) for row in reactor.methanogenesis_rows),
            "mineralization": tuple(dict(row) for row in reactor.mineralization_rows),
        }
        self.data_needs = tuple(
            dict.fromkeys(
                limitation.data_needed
                for limitation in self.limitations
                if limitation.data_needed
            )
        )
        return self


def _phase5_boundary_side_products(model: Phase4Model) -> list[bst.Stream]:
    """Return products that remain external when Phase 4 liquid enters digestion."""

    ends = _phase4_side_products(model.upstream_model)
    if model.scenario.scenario_id != "PR0":
        ends.extend(
            (
                model.streams["dry_protein_product"],
                model.streams["dryer_exhaust"],
            )
        )
    return ends


def create_phase5_scenario(
    scenario_id: str | None = None,
    *,
    phase4_scenario_id: str | None = None,
    phase3_scenario_id: str | None = None,
    selected_month: str | None = None,
    workbook_path: Path = INPUT_WORKBOOK_PATH,
    parameter_overrides: Mapping[str, object] | None = None,
    input_bundle: Phase5InputBundle | None = None,
) -> Phase5Model:
    """Build one fresh AD0-AD5 model without simulating it.

    AD4 and AD5 are deliberately registered but inactive until their
    configuration-specific biological, hydraulic, and separation data exist.
    """

    bundle = input_bundle or load_phase5_inputs(
        workbook_path,
        scenario_id=scenario_id,
        phase4_scenario_id=phase4_scenario_id,
        phase3_scenario_id=phase3_scenario_id,
        selected_month=selected_month,
    )
    if scenario_id and bundle.scenario_id != scenario_id.upper():
        raise ValueError("Provided Phase5InputBundle does not match requested scenario.")
    scenario = get_digestion_scenario(bundle.scenario_id)
    if not scenario.active:
        requirements = ", ".join(scenario.missing_data_requirements)
        raise NotImplementedError(
            f"Phase 5 scenario {scenario.scenario_id} is inactive because the following "
            f"data are missing: {requirements}."
        )

    effective_phase4 = "PR0" if scenario.feed_mode == "direct_protein_rich" else bundle.phase4_scenario_id
    if effective_phase4 != bundle.phase4_scenario_id:
        bundle = replace(bundle, phase4_scenario_id=effective_phase4)
    values = dict(bundle.parameter_values)
    if parameter_overrides:
        values.update(parameter_overrides)
    upstream = create_phase4_scenario(
        effective_phase4,
        phase3_scenario_id=bundle.phase3_scenario_id,
        selected_month=bundle.selected_month,
        workbook_path=workbook_path,
        parameter_overrides=parameter_overrides,
    )
    flowsheet = upstream.flowsheet
    units = dict(upstream.units)
    streams = dict(upstream.streams)
    # AD2 selects PR0, whose M403 is a material-conservative pass-through.
    # Using its outlet preserves a fully docked BioSTEAM graph while retaining
    # the clarified protein-rich composition.
    feed = upstream.streams["conditioned_protein_depleted_liquid"]

    conditioning = conditioning_parameters_from_mapping(
        values,
        enabled=scenario.digestion_enabled,
    )
    digestion = digestion_parameters_from_mapping(
        values,
        enabled=scenario.digestion_enabled,
    )
    gas_partition = gas_partition_parameters_from_mapping(values)
    if not scenario.digestion_enabled:
        gas_partition = replace(
            gas_partition,
            gas_capture_efficiency=0.0,
            dissolved_methane_fraction=1.0,
            dissolved_co2_fraction=1.0,
            dissolved_hydrogen_fraction=1.0,
            h2s_gas_transfer_fraction=0.0,
            ammonia_gas_transfer_fraction=0.0,
            raw_biogas_water_vapor_mol_fraction=0.0,
        )
    parameters: dict[str, object] = {
        "values": values,
        "phase4": upstream.parameters,
        "conditioning": conditioning,
        "digestion": digestion,
        "gas_partition": gas_partition,
    }

    base_solution = bst.Stream("digester_base_solution")
    dilution_water = bst.Stream("digester_dilution_water")
    trace_nutrients = bst.Stream("trace_nutrient_solution")
    M501 = DigesterFeedConditioner(
        ID="M501",
        ins=(feed, base_solution, dilution_water, trace_nutrients),
        outs="conditioned_digester_feed",
        parameters=conditioning,
    )
    target_temperature = (
        digestion.digester_temperature_c + 273.15
        if scenario.digestion_enabled
        else feed.T
    )
    H501 = bst.HXutility(
        ID="H501",
        ins=M501 - 0,
        outs="temperature_conditioned_digester_feed",
        T=target_temperature,
    )
    R501 = AnaerobicDigester(
        ID="R501",
        ins=H501 - 0,
        outs="digester_broth",
        parameters=digestion,
    )
    V501 = BiogasDisengagement(
        ID="V501",
        ins=R501 - 0,
        outs=("raw_biogas", "digestate", "uncaptured_biogas"),
        parameters=gas_partition,
        digester_pH=digestion.digester_pH,
    )
    units.update(M501=M501, H501=H501, R501=R501, V501=V501)
    streams.update(
        digester_feed=feed,
        digester_base_solution=base_solution,
        digester_dilution_water=dilution_water,
        trace_nutrient_solution=trace_nutrients,
        conditioned_digester_feed=M501 - 0,
        temperature_conditioned_digester_feed=H501 - 0,
        digester_broth=R501 - 0,
        raw_biogas=V501 - 0,
        digestate=V501 - 1,
        uncaptured_biogas=V501 - 2,
    )
    final_ends = _phase5_boundary_side_products(upstream) + [V501 - 0, V501 - 1, V501 - 2]
    system = bst.main_flowsheet.create_system(
        ID=(
            f"{PHASE5_SYSTEM_ID}_{bundle.phase3_scenario_id.lower()}_"
            f"{effective_phase4.lower()}_{scenario.scenario_id.lower()}"
        ),
        ends=tuple(final_ends),
        operating_hours=OPERATING_HOURS_PER_YEAR,
    )
    warnings = list(bundle.warnings)
    warnings.extend(upstream.warnings)
    assumptions = [
        "Phase 5 uses independent monthly steady states; no equalization dynamics are claimed.",
        "R501 is a staged hybrid component/COD fate model, not ADM1.",
        "Gas-liquid partitioning uses empirical Level-1 fractions, not Henry-law or kLa predictions.",
        "One combined microbial-biomass pool is used because population-specific data are unavailable.",
        "Custom Phase 5 units have zero CAPEX because no approved correlation or vendor quote is available.",
        "Persistent contaminant pools are conserved and sanitation is not claimed.",
    ]
    if bundle.structural_test_mode:
        warnings.append(
            "Phase 5 structural-test mode is active; class E values are placeholders, not design data."
        )
    model = Phase5Model(
        flowsheet=flowsheet,
        system=system,
        scenario=scenario,
        upstream_model=upstream,
        units=units,
        streams=streams,
        parameters=parameters,
        input_bundle=bundle,
        warnings=tuple(dict.fromkeys(warnings)),
        assumptions=tuple(assumptions),
        reactions={
            "architecture": (
                "hydrolysis",
                "acidogenesis",
                "acetogenesis",
                "methanogenesis",
                "biomass formation",
                "mineralization",
                "sulphate reduction",
                "residual COD allocation",
            ),
            "calculation_mode": digestion.calculation_mode,
        },
    )
    from Greenhub.phase5_limitations import build_limitations

    model.limitations = build_limitations(model)
    model.data_needs = tuple(
        dict.fromkeys(
            limitation.data_needed
            for limitation in model.limitations
            if limitation.data_needed
        )
    )
    return model


def create_no_digestion_system(**kwargs) -> Phase5Model:
    """Build AD0 no-digestion bypass."""

    return create_phase5_scenario("AD0", **kwargs)


def create_post_protein_recovery_digestion_system(**kwargs) -> Phase5Model:
    """Build AD1 mesophilic digestion after protein recovery."""

    return create_phase5_scenario("AD1", **kwargs)


def create_direct_digestion_system(**kwargs) -> Phase5Model:
    """Build AD2 direct digestion through the PR0 bypass."""

    return create_phase5_scenario("AD2", **kwargs)


def create_thermophilic_digestion_system(**kwargs) -> Phase5Model:
    """Build AD3 structural thermophilic digestion."""

    return create_phase5_scenario("AD3", **kwargs)


def create_two_stage_digestion_system(**kwargs) -> Phase5Model:
    """Raise the documented AD4 missing-data status."""

    return create_phase5_scenario("AD4", **kwargs)


def simulate_phase5_season(
    scenario_id: str,
    *,
    phase4_scenario_id: str | None = None,
    phase3_scenario_id: str | None = None,
    workbook_path: Path = INPUT_WORKBOOK_PATH,
    months: tuple[str, ...] = (
        "January",
        "February",
        "March",
        "April",
        "May",
        "June",
        "July",
        "August",
        "September",
        "October",
        "November",
        "December",
    ),
) -> object:
    """Simulate monthly AD steady states and size from the peak requirement."""

    from Greenhub.phase5_metrics import aggregate_monthly_phase5_metrics

    models = []
    warnings = []
    for month in months:
        try:
            models.append(
                create_phase5_scenario(
                    scenario_id,
                    phase4_scenario_id=phase4_scenario_id,
                    phase3_scenario_id=phase3_scenario_id,
                    selected_month=month,
                    workbook_path=workbook_path,
                ).simulate()
            )
        except ValueError as error:
            warnings.append(f"{month}: {error}")
    if not models:
        raise ValueError(f"No monthly Phase 5 simulations succeeded for scenario {scenario_id}.")
    return aggregate_monthly_phase5_metrics(models, tuple(warnings))


@dataclass
class Phase6Model:
    """Structured Phase 6 bundle with named gas products and boundary streams."""

    flowsheet: bst.Flowsheet
    system: bst.System
    scenario: BiogasUpgradingScenario
    upstream_model: Phase5Model
    units: dict[str, object]
    streams: dict[str, bst.Stream]
    parameters: dict[str, object]
    input_bundle: Phase6InputBundle
    external_inputs: tuple[bst.Stream, ...]
    boundary_outputs: tuple[bst.Stream, ...]
    warnings: tuple[str, ...]
    assumptions: tuple[str, ...]
    limitations: tuple[object, ...] = ()
    data_needs: tuple[str, ...] = ()
    validation: object | None = None
    metrics: dict[str, object] = field(default_factory=dict)
    reports: dict[str, Path] = field(default_factory=dict)

    def simulate(self) -> "Phase6Model":
        """Simulate the integrated Phase 1-6 plant and refresh validations."""

        from Greenhub.phase3_metrics import calculate_phase3_metrics, create_raw_liquid_interface
        from Greenhub.phase3_validation import validate_phase3_model
        from Greenhub.phase4_metrics import calculate_phase4_metrics
        from Greenhub.phase4_validation import validate_phase4_model
        from Greenhub.phase5_limitations import build_limitations
        from Greenhub.phase5_metrics import calculate_phase5_metrics
        from Greenhub.phase5_validation import validate_phase5_model
        from Greenhub.phase6_limitations import build_phase6_limitations
        from Greenhub.phase6_metrics import calculate_phase6_metrics
        from Greenhub.phase6_validation import validate_phase6_model

        self.system.simulate()
        phase5 = self.upstream_model
        phase4 = phase5.upstream_model
        phase3 = phase4.upstream_model
        phase3.raw_liquid_interface = create_raw_liquid_interface(phase3)
        phase3.validation = validate_phase3_model(phase3)
        phase3.metrics = calculate_phase3_metrics(phase3, phase3.validation)
        phase4.validation = validate_phase4_model(phase4)
        phase4.metrics = calculate_phase4_metrics(phase4, phase4.validation)
        phase5.validation = validate_phase5_model(phase5)
        phase5.metrics = calculate_phase5_metrics(phase5, phase5.validation)
        phase5.limitations = build_limitations(phase5)
        self.validation = validate_phase6_model(self)
        self.metrics = calculate_phase6_metrics(self, self.validation)
        self.limitations = build_phase6_limitations(self)
        self.data_needs = tuple(
            dict.fromkeys(
                limitation.data_needed
                for limitation in self.limitations
                if limitation.data_needed
            )
        )
        return self


def _create_phase6_pretreatment(
    model: Phase5Model,
    scenario: BiogasUpgradingScenario,
    values: Mapping[str, object],
) -> tuple[
    dict[str, object],
    dict[str, bst.Stream],
    list[bst.Stream],
    bst.Stream,
    bst.Stream,
]:
    """Attach the common G601-S601-R601-R602-F601 conditioning train."""

    enabled = scenario.pretreatment_enabled and bool(values.get("pretreatment_enabled", True))
    parameters = pretreatment_parameters_from_mapping(values, enabled=enabled)
    raw_biogas = model.streams["raw_biogas"]
    G601 = RawBiogasCooler(
        ID="G601",
        ins=raw_biogas,
        outs="cooled_raw_biogas",
        parameters=parameters.cooling,
    )
    S601 = CondensateSeparator(
        ID="S601",
        ins=G601 - 0,
        outs=("dewatered_raw_biogas", "raw_biogas_condensate"),
        parameters=parameters.condensate,
    )
    fresh_h2s_media = bst.Stream("fresh_h2s_removal_media")
    desulfurization_air = bst.Stream("desulfurization_air")
    R601 = HydrogenSulfideRemoval(
        ID="R601",
        ins=(S601 - 0, fresh_h2s_media, desulfurization_air),
        outs=("desulfurized_biogas", "spent_h2s_removal_media"),
        parameters=parameters.h2s,
    )
    ammonia_wash_water = bst.Stream("ammonia_scrubber_water")
    ammonia_acid_solution = bst.Stream("ammonia_scrubber_acid_solution")
    R602 = AmmoniaRemoval(
        ID="R602",
        ins=(R601 - 0, ammonia_wash_water, ammonia_acid_solution),
        outs=("ammonia_polished_biogas", "ammonia_scrubber_liquor"),
        parameters=parameters.ammonia,
    )
    fresh_filter_media = bst.Stream("fresh_particle_siloxane_filter_media")
    F601 = ParticleSiloxaneFilter(
        ID="F601",
        ins=(R602 - 0, fresh_filter_media),
        outs=("conditioned_biogas", "spent_particle_siloxane_filter_media"),
        parameters=parameters.filtration,
    )
    M606 = bst.Mixer(
        ID="M606",
        ins=(S601 - 1, R602 - 1),
        outs="conditioning_wastewater",
    )
    M607 = bst.Mixer(
        ID="M607",
        ins=(R601 - 1, F601 - 1),
        outs="conditioning_spent_material",
        conserve_phases=True,
    )
    units = {
        unit.ID: unit
        for unit in (G601, S601, R601, R602, F601, M606, M607)
    }
    streams = {
        "raw_biogas": raw_biogas,
        "cooled_raw_biogas": G601 - 0,
        "raw_biogas_condensate": S601 - 1,
        "dewatered_raw_biogas": S601 - 0,
        "fresh_h2s_removal_media": fresh_h2s_media,
        "desulfurization_air": desulfurization_air,
        "spent_h2s_removal_media": R601 - 1,
        "desulfurized_biogas": R601 - 0,
        "ammonia_scrubber_water": ammonia_wash_water,
        "ammonia_scrubber_acid_solution": ammonia_acid_solution,
        "ammonia_scrubber_liquor": R602 - 1,
        "ammonia_polished_biogas": R602 - 0,
        "fresh_particle_siloxane_filter_media": fresh_filter_media,
        "spent_particle_siloxane_filter_media": F601 - 1,
        "conditioned_biogas": F601 - 0,
        "conditioning_wastewater": M606 - 0,
        "conditioning_spent_material": M607 - 0,
    }
    external_inputs = [
        fresh_h2s_media,
        desulfurization_air,
        ammonia_wash_water,
        ammonia_acid_solution,
        fresh_filter_media,
    ]
    return units, streams, external_inputs, M606 - 0, M607 - 0


def _create_bg0_reference(
    conditioned_biogas: bst.Stream,
) -> tuple[dict[str, object], dict[str, bst.Stream], list[bst.Stream], bool]:
    S609 = bst.Splitter(
        ID="S609",
        ins=conditioned_biogas,
        outs=("raw_biogas_export", "raw_biogas_reference_reject"),
        split=1.0,
    )
    wastewater = bst.Stream("bg0_technology_wastewater")
    spent = bst.Stream("bg0_technology_spent_material")
    return (
        {"S609": S609},
        {
            "gas_product": S609 - 0,
            "biomethane": S609 - 0,
            "reject_gas": S609 - 1,
            "technology_wastewater": wastewater,
            "technology_spent_material": spent,
        },
        [],
        False,
    )


def _create_bg2_water_scrubbing(
    conditioned_biogas: bst.Stream,
    values: Mapping[str, object],
) -> tuple[dict[str, object], dict[str, bst.Stream], list[bst.Stream], bool]:
    parameters = water_scrubbing_parameters_from_mapping(values)
    units: dict[str, object] = {}
    streams: dict[str, bst.Stream] = {}
    external_inputs: list[bst.Stream] = []
    has_flash_recycle = parameters.flash_gas_recycle_fraction > 0.0
    flash_recycle = bst.Stream("water_scrubber_flash_gas_recycle")
    if has_flash_recycle:
        M610 = bst.Mixer(
            ID="M610",
            ins=(conditioned_biogas, flash_recycle),
            outs="water_scrubber_compressor_feed",
        )
        compressor_feed = M610 - 0
        units[M610.ID] = M610
    else:
        compressor_feed = conditioned_biogas
    C611 = bst.IsentropicCompressor(
        ID="C611",
        ins=compressor_feed,
        outs="compressed_water_scrubber_feed",
        P=parameters.absorber_pressure_bar * 1e5,
        eta=parameters.compressor_efficiency,
        vle=False,
    )
    E611 = bst.HXutility(
        ID="E611",
        ins=C611 - 0,
        outs="cooled_water_scrubber_feed",
        T=parameters.absorber_temperature_c + 273.15,
        cool_only=True,
    )
    fresh_water = bst.Stream("fresh_scrubbing_water")
    water_recycle = bst.Stream("pressurized_recycled_scrubbing_water")
    once_through = parameters.water_mode == "once_through"
    absorber_recycle = (
        bst.Stream("zero_recycled_scrubbing_water")
        if once_through
        else water_recycle
    )
    A611 = WaterAbsorber(
        ID="A611",
        ins=(E611 - 0, absorber_recycle, fresh_water),
        outs=("water_scrubber_absorber_gas", "co2_rich_scrubbing_water"),
        parameters=parameters,
    )
    V611 = GasWaterSeparator(
        ID="V611",
        ins=A611 - 0,
        outs=("water_scrubber_flash_product", "water_scrubber_product_condensate"),
        water_removal_fraction=parameters.product_flash_water_removal_fraction,
        pressure_drop_pa=0.0,
        limitation_id="LIM-P6-008",
    )
    D611 = GasWaterSeparator(
        ID="D611",
        ins=V611 - 0,
        outs=("water_scrubber_biomethane", "water_scrubber_dryer_condensate"),
        water_removal_fraction=parameters.product_dryer_water_removal_fraction,
        pressure_drop_pa=parameters.dryer_pressure_drop_pa,
        limitation_id="LIM-P6-008",
    )
    V612 = WaterFlashTank(
        ID="V612",
        ins=A611 - 1,
        outs=("water_scrubber_flash_gas", "flashed_scrubbing_water"),
        parameters=parameters,
    )
    A612 = WaterRegenerator(
        ID="A612",
        ins=V612 - 1,
        outs=(
            "water_scrubber_regeneration_offgas",
            "regenerated_scrubbing_water",
            "water_scrubber_purge_water",
        ),
        parameters=parameters,
    )
    P611 = bst.Pump(
        ID="P611",
        ins=A612 - 1,
        outs=water_recycle,
        P=parameters.absorber_pressure_bar * 1e5,
    )
    flash_reject = V612 - 0
    if has_flash_recycle:
        S610 = bst.Splitter(
            ID="S610",
            ins=V612 - 0,
            outs=(flash_recycle, "water_scrubber_flash_reject"),
            split=parameters.flash_gas_recycle_fraction,
        )
        flash_reject = S610 - 1
        units[S610.ID] = S610
    M618_inputs = [V611 - 1, D611 - 1, A612 - 2]
    if once_through:
        M618_inputs.append(P611 - 0)
    M618 = bst.Mixer(
        ID="M618",
        ins=tuple(M618_inputs),
        outs="water_scrubber_wastewater",
    )
    M619 = bst.Mixer(
        ID="M619",
        ins=(flash_reject, A612 - 0),
        outs="water_scrubber_reject_gas",
        conserve_phases=True,
    )
    spent = bst.Stream("water_scrubber_spent_material")
    for unit in (C611, E611, A611, V611, D611, V612, A612, P611, M618, M619):
        units[unit.ID] = unit
    streams.update(
        gas_product=D611 - 0,
        biomethane=D611 - 0,
        reject_gas=M619 - 0,
        technology_wastewater=M618 - 0,
        technology_spent_material=spent,
        fresh_scrubbing_water=fresh_water,
        water_scrubber_flash_gas=V612 - 0,
        regenerated_scrubbing_water=A612 - 1,
        pressurized_recycled_scrubbing_water=P611 - 0,
    )
    external_inputs.append(fresh_water)
    return units, streams, external_inputs, (not once_through or has_flash_recycle)


def _create_bg3_membranes(
    conditioned_biogas: bst.Stream,
    values: Mapping[str, object],
) -> tuple[dict[str, object], dict[str, bst.Stream], list[bst.Stream], bool]:
    parameters = membrane_parameters_from_mapping(values)
    units: dict[str, object] = {}
    recycle_active = parameters.number_of_stages > 1 and parameters.recycle_fraction > 0.0
    membrane_recycle = bst.Stream("membrane_permeate_recycle")
    if recycle_active:
        M620 = bst.Mixer(
            ID="M620",
            ins=(conditioned_biogas, membrane_recycle),
            outs="membrane_compressor_feed",
        )
        compressor_feed = M620 - 0
        units[M620.ID] = M620
    else:
        compressor_feed = conditioned_biogas
    C621 = bst.IsentropicCompressor(
        ID="C621",
        ins=compressor_feed,
        outs="compressed_membrane_feed",
        P=parameters.feed_pressure_bar * 1e5,
        eta=parameters.compressor_efficiency,
        vle=False,
    )
    E621 = bst.HXutility(
        ID="E621",
        ins=C621 - 0,
        outs="cooled_membrane_feed",
        T=parameters.aftercooler_temperature_c + 273.15,
        cool_only=True,
    )
    D621 = GasWaterSeparator(
        ID="D621",
        ins=E621 - 0,
        outs=("dry_membrane_feed", "membrane_guard_condensate"),
        water_removal_fraction=parameters.dryer_water_removal_fraction,
        pressure_drop_pa=parameters.dryer_pressure_drop_pa,
        limitation_id="LIM-P6-008",
    )
    areas = (
        parameters.membrane_area_stage1_m2,
        parameters.membrane_area_stage2_m2,
        parameters.membrane_area_stage3_m2,
    )
    feed = D621 - 0
    permeates: list[bst.Stream] = []
    stages: list[MembraneStage] = []
    for index in range(parameters.number_of_stages):
        stage = MembraneStage(
            ID=f"M62{index + 1}",
            ins=feed,
            outs=(f"membrane_stage_{index + 1}_retentate", f"membrane_stage_{index + 1}_permeate"),
            parameters=parameters,
            stage_number=index + 1,
            area_m2=areas[index],
        )
        stages.append(stage)
        units[stage.ID] = stage
        feed = stage - 0
        permeates.append(stage - 1)
    reject_inputs: list[bst.Stream] = [permeates[0]]
    if recycle_active:
        M628 = bst.Mixer(
            ID="M628",
            ins=tuple(permeates[1:]),
            outs="combined_downstream_membrane_permeate",
            conserve_phases=True,
        )
        S622 = bst.Splitter(
            ID="S622",
            ins=M628 - 0,
            outs=(membrane_recycle, "unrecycled_downstream_membrane_permeate"),
            split=parameters.recycle_fraction,
        )
        units.update(M628=M628, S622=S622)
        reject_inputs.append(S622 - 1)
    else:
        reject_inputs.extend(permeates[1:])
    M629 = bst.Mixer(
        ID="M629",
        ins=tuple(reject_inputs),
        outs="membrane_reject_gas",
        conserve_phases=True,
    )
    units.update(C621=C621, E621=E621, D621=D621, M629=M629)
    spent = bst.Stream("membrane_spent_material")
    streams = {
        "gas_product": feed,
        "biomethane": feed,
        "reject_gas": M629 - 0,
        "technology_wastewater": D621 - 1,
        "technology_spent_material": spent,
        "dry_membrane_feed": D621 - 0,
        "membrane_permeate_recycle": membrane_recycle,
    }
    return units, streams, [], recycle_active


def _create_bg4_psa(
    conditioned_biogas: bst.Stream,
    values: Mapping[str, object],
) -> tuple[dict[str, object], dict[str, bst.Stream], list[bst.Stream], bool]:
    parameters = psa_parameters_from_mapping(values)
    units: dict[str, object] = {}
    recycle_active = parameters.purge_recycle_fraction > 0.0
    purge_recycle = bst.Stream("psa_purge_recycle")
    if recycle_active:
        M630 = bst.Mixer(
            ID="M630",
            ins=(conditioned_biogas, purge_recycle),
            outs="psa_compressor_feed",
        )
        compressor_feed = M630 - 0
        units[M630.ID] = M630
    else:
        compressor_feed = conditioned_biogas
    C631 = bst.IsentropicCompressor(
        ID="C631",
        ins=compressor_feed,
        outs="compressed_psa_feed",
        P=parameters.adsorption_pressure_bar * 1e5,
        eta=parameters.compressor_efficiency,
        vle=False,
    )
    D631 = GasWaterSeparator(
        ID="D631",
        ins=C631 - 0,
        outs=("dry_psa_feed", "psa_guard_condensate"),
        water_removal_fraction=parameters.dryer_water_removal_fraction,
        pressure_drop_pa=parameters.dryer_pressure_drop_pa,
        limitation_id="LIM-P6-008",
    )
    fresh_adsorbent = bst.Stream("fresh_psa_adsorbent")
    A631 = PressureSwingAdsorber(
        ID="A631",
        ins=(D631 - 0, fresh_adsorbent),
        outs=("psa_biomethane", "psa_blowdown_gas", "psa_purge_gas", "spent_psa_adsorbent"),
        parameters=parameters,
    )
    purge_reject = A631 - 2
    if recycle_active:
        S631 = bst.Splitter(
            ID="S631",
            ins=A631 - 2,
            outs=(purge_recycle, "unrecycled_psa_purge"),
            split=parameters.purge_recycle_fraction,
        )
        units[S631.ID] = S631
        purge_reject = S631 - 1
    M639 = bst.Mixer(
        ID="M639",
        ins=(A631 - 1, purge_reject),
        outs="psa_reject_gas",
        conserve_phases=True,
    )
    units.update(C631=C631, D631=D631, A631=A631, M639=M639)
    streams = {
        "gas_product": A631 - 0,
        "biomethane": A631 - 0,
        "reject_gas": M639 - 0,
        "technology_wastewater": D631 - 1,
        "technology_spent_material": A631 - 3,
        "fresh_psa_adsorbent": fresh_adsorbent,
        "psa_purge_gas": A631 - 2,
        "psa_blowdown_gas": A631 - 1,
    }
    return units, streams, [fresh_adsorbent], recycle_active


def _create_bg5_mea(
    conditioned_biogas: bst.Stream,
    values: Mapping[str, object],
) -> tuple[dict[str, object], dict[str, bst.Stream], list[bst.Stream], bool]:
    parameters = mea_parameters_from_mapping(values)
    C641 = bst.IsentropicCompressor(
        ID="C641",
        ins=conditioned_biogas,
        outs="compressed_mea_absorber_feed",
        P=parameters.absorber_pressure_bar * 1e5,
        eta=parameters.compressor_efficiency,
        vle=False,
    )
    E640 = bst.HXutility(
        ID="E640",
        ins=C641 - 0,
        outs="cooled_mea_absorber_feed",
        T=parameters.absorber_temperature_c + 273.15,
        cool_only=True,
    )
    lean_recycle = bst.Stream("lean_mea_recycle")
    fresh_makeup = bst.Stream("fresh_mea_solution_makeup")
    A641 = MEAAbsorber(
        ID="A641",
        ins=(E640 - 0, lean_recycle, fresh_makeup),
        outs=("mea_biomethane", "rich_mea_solution"),
        parameters=parameters,
    )
    E641 = RichLeanHeatExchanger(
        ID="E641",
        ins=A641 - 1,
        outs="preheated_rich_mea",
        parameters=parameters,
    )
    H641 = MEAReboiler(
        ID="H641",
        ins=E641 - 0,
        outs="heated_rich_mea",
        parameters=parameters,
    )
    A642 = MEAStripper(
        ID="A642",
        ins=H641 - 0,
        outs=("stripped_lean_mea", "wet_mea_regenerator_overhead", "spent_mea_solvent"),
        parameters=parameters,
    )
    V641 = RefluxCondenser(
        ID="V641",
        ins=A642 - 1,
        outs=("mea_reject_gas", "mea_reflux", "mea_wastewater"),
        parameters=parameters,
    )
    E643 = LeanHeatRecovery(
        ID="E643",
        ins=A642 - 0,
        outs="heat_recovered_lean_mea",
        parameters=parameters,
        rich_side=E641,
    )
    P641 = bst.Pump(
        ID="P641",
        ins=E643 - 0,
        outs="pumped_lean_mea",
        P=parameters.pump_pressure_bar * 1e5,
    )
    E642 = bst.HXutility(
        ID="E642",
        ins=P641 - 0,
        outs="cooled_lean_mea",
        T=parameters.lean_cooler_temperature_c + 273.15,
        cool_only=True,
    )
    M641 = bst.Mixer(
        ID="M641",
        ins=(E642 - 0, V641 - 1),
        outs=lean_recycle,
    )
    units = {
        unit.ID: unit
        for unit in (
            C641,
            E640,
            A641,
            E641,
            H641,
            A642,
            V641,
            E643,
            P641,
            E642,
            M641,
        )
    }
    streams = {
        "gas_product": A641 - 0,
        "biomethane": A641 - 0,
        "reject_gas": V641 - 0,
        "technology_wastewater": V641 - 2,
        "technology_spent_material": A642 - 2,
        "fresh_mea_solution_makeup": fresh_makeup,
        "lean_mea_recycle": lean_recycle,
        "rich_mea_solution": A641 - 1,
        "wet_mea_regenerator_overhead": A642 - 1,
    }
    return units, streams, [fresh_makeup], True


def create_phase6_scenario(
    scenario_id: str | None = None,
    *,
    phase5_scenario_id: str | None = None,
    phase4_scenario_id: str | None = None,
    phase3_scenario_id: str | None = None,
    selected_month: str | None = None,
    workbook_path: Path = INPUT_WORKBOOK_PATH,
    parameter_overrides: Mapping[str, object] | None = None,
    input_bundle: Phase6InputBundle | None = None,
) -> Phase6Model:
    """Build a fresh BG0-BG6 model without simulating it."""

    bundle = input_bundle or load_phase6_inputs(
        workbook_path,
        scenario_id=scenario_id,
        phase5_scenario_id=phase5_scenario_id,
        phase4_scenario_id=phase4_scenario_id,
        phase3_scenario_id=phase3_scenario_id,
        selected_month=selected_month,
    )
    if scenario_id and bundle.scenario_id != scenario_id.upper():
        raise ValueError("Provided Phase6InputBundle does not match requested scenario.")
    scenario = get_biogas_upgrading_scenario(bundle.scenario_id)
    if not scenario.active:
        requirements = ", ".join(scenario.missing_data_requirements)
        raise NotImplementedError(
            f"Phase 6 scenario {scenario.scenario_id} is inactive because the following "
            f"data or engineering section is missing: {requirements}."
        )
    values = dict(bundle.parameter_values)
    if parameter_overrides:
        values.update(parameter_overrides)
    upstream = create_phase5_scenario(
        bundle.phase5_scenario_id,
        phase4_scenario_id=bundle.phase4_scenario_id,
        phase3_scenario_id=bundle.phase3_scenario_id,
        selected_month=bundle.selected_month,
        workbook_path=workbook_path,
        parameter_overrides=parameter_overrides,
    )
    flowsheet = upstream.flowsheet
    units = dict(upstream.units)
    streams = dict(upstream.streams)
    pretreatment_units, pretreatment_streams, external_inputs, common_wastewater, common_spent = (
        _create_phase6_pretreatment(upstream, scenario, values)
    )
    units.update(pretreatment_units)
    streams.update(pretreatment_streams)
    conditioned = pretreatment_streams["conditioned_biogas"]
    if scenario.scenario_id == "BG0":
        technology_units, technology_streams, technology_inputs, has_recycle = _create_bg0_reference(conditioned)
        technology_parameters = None
    elif scenario.scenario_id == "BG2":
        technology_units, technology_streams, technology_inputs, has_recycle = _create_bg2_water_scrubbing(conditioned, values)
        technology_parameters = water_scrubbing_parameters_from_mapping(values)
    elif scenario.scenario_id == "BG3":
        technology_units, technology_streams, technology_inputs, has_recycle = _create_bg3_membranes(conditioned, values)
        technology_parameters = membrane_parameters_from_mapping(values)
    elif scenario.scenario_id == "BG4":
        technology_units, technology_streams, technology_inputs, has_recycle = _create_bg4_psa(conditioned, values)
        technology_parameters = psa_parameters_from_mapping(values)
    elif scenario.scenario_id == "BG5":
        technology_units, technology_streams, technology_inputs, has_recycle = _create_bg5_mea(conditioned, values)
        technology_parameters = mea_parameters_from_mapping(values)
    else:  # Defensive: inactive BG1/BG6 are rejected above.
        raise NotImplementedError(f"No active factory for {scenario.scenario_id}.")
    units.update(technology_units)
    streams.update(technology_streams)
    external_inputs.extend(technology_inputs)
    M698 = bst.Mixer(
        ID="M698",
        ins=(common_wastewater, technology_streams["technology_wastewater"]),
        outs="phase6_wastewater",
        conserve_phases=True,
    )
    M699 = bst.Mixer(
        ID="M699",
        ins=(common_spent, technology_streams["technology_spent_material"]),
        outs="phase6_spent_material",
        conserve_phases=True,
    )
    units.update(M698=M698, M699=M699)
    streams.update(
        phase6_wastewater=M698 - 0,
        phase6_spent_material=M699 - 0,
        primary_gas_product=technology_streams["gas_product"],
    )
    boundary_outputs = (
        technology_streams["gas_product"],
        technology_streams["reject_gas"],
        M698 - 0,
        M699 - 0,
    )
    final_ends = _phase5_boundary_side_products(upstream.upstream_model) + [
        upstream.streams["digestate"],
        upstream.streams["uncaptured_biogas"],
        *boundary_outputs,
    ]
    system_kwargs: dict[str, object] = {}
    if has_recycle:
        system_kwargs.update(
            method="aitken",
            maxiter=200,
            molar_tolerance=1e-8,
            relative_molar_tolerance=1e-7,
            temperature_tolerance=1e-4,
        )
    system = bst.main_flowsheet.create_system(
        ID=(
            f"{PHASE6_SYSTEM_ID}_{bundle.phase3_scenario_id.lower()}_"
            f"{bundle.phase4_scenario_id.lower()}_{bundle.phase5_scenario_id.lower()}_"
            f"{scenario.scenario_id.lower()}"
        ),
        ends=tuple(final_ends),
        operating_hours=OPERATING_HOURS_PER_YEAR,
        **system_kwargs,
    )
    if has_recycle:
        # BioSTEAM may place detected recycle loops in generated subsystems.
        # Propagate the Phase 6 tolerances so those loops do not retain the
        # substantially looser System defaults.
        system.set_tolerance(
            mol=1e-8,
            rmol=1e-7,
            T=1e-4,
            subsystems=True,
            maxiter=200,
            method="aitken",
        )
    quality_limits = (
        feed_quality_limits_from_mapping(values)
        if scenario.upgrading_enabled
        else None
    )
    parameters: dict[str, object] = {
        "values": values,
        "pretreatment": pretreatment_parameters_from_mapping(
            values,
            enabled=scenario.pretreatment_enabled and bool(values.get("pretreatment_enabled", True)),
        ),
        "technology": technology_parameters,
        "feed_quality_limits": quality_limits,
        "phase6_unit_ids": tuple(unit.ID for unit in technology_units.values())
        + tuple(pretreatment_units)
        + ("M698", "M699"),
        "has_recycle": has_recycle,
    }
    warnings = list(bundle.warnings)
    warnings.extend(upstream.warnings)
    assumptions = (
        "Phase 6 starts at the Phase 5 raw-biogas stream and does not redefine methane production.",
        "BG2-BG5 use technology-specific Level-1 models with class-E structural inputs pending calibration.",
        "Normal gas volumes use 0 degC and 101325 Pa; wet and dry bases are reported separately.",
        "Custom Phase 6 units have zero CAPEX because no approved correlation or vendor quotation exists.",
        "BG1 CHP, final biomethane compression/storage/grid injection, and the plant-wide utility network are intentionally deferred to the next Phase 6 section.",
        "BG6 remains inactive until validated low-temperature thermodynamics and refrigeration design data exist.",
    )
    if bundle.structural_test_mode:
        warnings.append(
            "Phase 6 structural-test mode is active; class-E gas-cleaning and upgrading values are not validated design data."
        )
    model = Phase6Model(
        flowsheet=flowsheet,
        system=system,
        scenario=scenario,
        upstream_model=upstream,
        units=units,
        streams=streams,
        parameters=parameters,
        input_bundle=bundle,
        external_inputs=tuple(external_inputs),
        boundary_outputs=boundary_outputs,
        warnings=tuple(dict.fromkeys(warnings)),
        assumptions=assumptions,
    )
    from Greenhub.phase6_limitations import build_phase6_limitations

    model.limitations = build_phase6_limitations(model)
    model.data_needs = tuple(
        dict.fromkeys(
            limitation.data_needed
            for limitation in model.limitations
            if limitation.data_needed
        )
    )
    return model


def create_raw_biogas_export_system(**kwargs) -> Phase6Model:
    """Build BG0 raw-biogas export reference."""

    return create_phase6_scenario("BG0", **kwargs)


def create_water_scrubbing_system(**kwargs) -> Phase6Model:
    """Build BG2 high-pressure water-scrubbing pathway."""

    return create_phase6_scenario("BG2", **kwargs)


def create_membrane_upgrading_system(**kwargs) -> Phase6Model:
    """Build BG3 segmented membrane pathway."""

    return create_phase6_scenario("BG3", **kwargs)


def create_psa_upgrading_system(**kwargs) -> Phase6Model:
    """Build BG4 cycle-average PSA pathway."""

    return create_phase6_scenario("BG4", **kwargs)


def create_mea_upgrading_system(**kwargs) -> Phase6Model:
    """Build BG5 equivalent-loading MEA pathway."""

    return create_phase6_scenario("BG5", **kwargs)


def create_phase7_scenario(*args, **kwargs):
    """Build an NR0-NR7 model through the isolated Phase 7 factory."""

    from Greenhub.phase7_systems import create_phase7_scenario as factory

    return factory(*args, **kwargs)


def simulate_phase7_season(*args, **kwargs):
    """Aggregate independent monthly Phase 7 steady states."""

    from Greenhub.phase7_systems import simulate_phase7_season as simulator

    return simulator(*args, **kwargs)
