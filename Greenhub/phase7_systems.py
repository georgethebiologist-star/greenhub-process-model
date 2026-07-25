"""Integrated Phase 7 digestate-processing and nutrient-recovery factories."""

from __future__ import annotations

import gc
from dataclasses import dataclass, field
from pathlib import Path
from typing import Mapping

import biosteam as bst

from Greenhub.input_data import INPUT_WORKBOOK_PATH
from Greenhub.phase7_inputs import Phase7InputBundle, load_phase7_inputs
from Greenhub.phase7_units import (
    AcidAbsorber,
    AlkalineConditioner,
    AmmoniaStripper,
    CalciumPhosphateReactor,
    CrystalSeparator,
    DigestateEqualization,
    DigestateSolidLiquidSeparator,
    IonExchangeBed,
    IonExchangeRegeneration,
    NutrientProductDryer,
    NutrientProductWasher,
    PotassiumEvaporator,
    PotassiumMembraneConcentrator,
    ProcessHeater,
    ProductStorage,
    StruviteCrystallizer,
    acid_parameters_from_mapping,
    calcium_parameters_from_mapping,
    crystal_parameters_from_mapping,
    equalization_parameters_from_mapping,
    finishing_parameters_from_mapping,
    ion_exchange_parameters_from_mapping,
    potassium_parameters_from_mapping,
    separation_parameters_from_mapping,
    stripping_parameters_from_mapping,
    struvite_parameters_from_mapping,
)
from Greenhub.scenarios import NutrientRecoveryScenario, get_nutrient_recovery_scenario
from Greenhub.settings import OPERATING_HOURS_PER_YEAR
from Greenhub.systems import Phase6Model, _phase5_boundary_side_products, create_phase6_scenario

PHASE7_SYSTEM_ID = "greenhub_phase7"


def _required_float(values: Mapping[str, object], name: str) -> float:
    value = values.get(name)
    if value is None or isinstance(value, bool):
        raise ValueError(f"Required Phase 7 parameter '{name}' is missing or non-numeric.")
    return float(value)


def _deduplicate_streams(streams) -> tuple[bst.Stream, ...]:
    result: list[bst.Stream] = []
    seen: set[int] = set()
    for stream in streams:
        if id(stream) not in seen:
            result.append(stream)
            seen.add(id(stream))
    return tuple(result)


@dataclass
class Phase7Model:
    """Structured Phase 7 bundle linked to the actual Phase 5 digestate."""

    flowsheet: bst.Flowsheet
    system: bst.System
    scenario: NutrientRecoveryScenario
    upstream_model: Phase6Model
    units: dict[str, object]
    streams: dict[str, bst.Stream]
    parameters: dict[str, object]
    input_bundle: Phase7InputBundle
    external_inputs: tuple[bst.Stream, ...]
    boundary_outputs: tuple[bst.Stream, ...]
    warnings: tuple[str, ...]
    assumptions: tuple[str, ...]
    limitations: tuple[object, ...] = ()
    data_needs: tuple[str, ...] = ()
    validation: object | None = None
    metrics: dict[str, object] = field(default_factory=dict)
    reports: dict[str, Path] = field(default_factory=dict)
    seasonal_result: object | None = None

    def simulate(self) -> "Phase7Model":
        """Simulate the integrated Phase 1-7 graph and refresh all validations."""

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
        from Greenhub.phase7_limitations import build_phase7_limitations
        from Greenhub.phase7_metrics import calculate_phase7_metrics
        from Greenhub.phase7_validation import validate_phase7_model

        self.system.simulate()
        phase6 = self.upstream_model
        phase5 = phase6.upstream_model
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
        phase6.validation = validate_phase6_model(phase6)
        phase6.metrics = calculate_phase6_metrics(phase6, phase6.validation)
        phase6.limitations = build_phase6_limitations(phase6)
        self.validation = validate_phase7_model(self)
        self.metrics = calculate_phase7_metrics(self, self.validation)
        self.limitations = build_phase7_limitations(self)
        self.data_needs = tuple(
            dict.fromkeys(
                limitation.data_needed
                for limitation in self.limitations
                if limitation.data_needed
            )
        )
        return self


def _add_unit(collection: dict[str, object], unit) -> None:
    collection[unit.ID] = unit


def _aggregate_streams(
    *,
    unit_id: str,
    output_id: str,
    sources: list[bst.Stream],
    units: dict[str, object],
) -> bst.Stream:
    if not sources:
        return bst.Stream(output_id)
    mixer = bst.Mixer(
        ID=unit_id,
        ins=tuple(sources),
        outs=output_id,
        conserve_phases=True,
    )
    _add_unit(units, mixer)
    return mixer - 0


def _attach_equalization(
    feed: bst.Stream,
    values: Mapping[str, object],
    units: dict[str, object],
    streams: dict[str, bst.Stream],
) -> tuple[bst.Stream, bst.Stream, object]:
    parameters = equalization_parameters_from_mapping(values)
    tank = DigestateEqualization(
        ID="T701",
        ins=feed,
        outs=("equalized_digestate", "equalization_offgas"),
        parameters=parameters,
    )
    _add_unit(units, tank)
    streams.update(equalized_digestate=tank - 0, equalization_offgas=tank - 1)
    return tank - 0, tank - 1, parameters


def _attach_separation(
    feed: bst.Stream,
    values: Mapping[str, object],
    units: dict[str, object],
    streams: dict[str, bst.Stream],
) -> tuple[bst.Stream, bst.Stream, object]:
    parameters = separation_parameters_from_mapping(values)
    separator = DigestateSolidLiquidSeparator(
        ID="S701",
        ins=feed,
        outs=("nutrient_rich_digestate_solids", "nutrient_rich_centrate"),
        parameters=parameters,
    )
    _add_unit(units, separator)
    streams.update(
        nutrient_rich_solids=separator - 0,
        nutrient_rich_centrate=separator - 1,
    )
    return separator - 0, separator - 1, parameters


def _attach_phosphorus_route(
    feed: bst.Stream,
    *,
    route: str,
    values: Mapping[str, object],
    units: dict[str, object],
    streams: dict[str, bst.Stream],
    external_inputs: list[bst.Stream],
    wastewater_sources: list[bst.Stream],
    offgas_sources: list[bst.Stream],
) -> tuple[bst.Stream, bst.Stream, dict[str, object]]:
    finishing = finishing_parameters_from_mapping(values)
    crystal_parameters = crystal_parameters_from_mapping(values, route=route)
    if route == "struvite":
        magnesium = bst.Stream("struvite_magnesium_solution")
        base = bst.Stream("struvite_base_solution")
        seed = bst.Stream("struvite_seed")
        reactor_parameters = struvite_parameters_from_mapping(values)
        reactor = StruviteCrystallizer(
            ID="R711",
            ins=(feed, magnesium, base, seed),
            outs="struvite_slurry",
            parameters=reactor_parameters,
        )
        separator_id = "S711"
        raw_product_id = "raw_wet_struvite_product"
        mother_liquor_id = "struvite_mother_liquor"
        washer_id = "W711"
        washed_id = "washed_struvite_product"
        wash_effluent_id = "struvite_wash_effluent"
        dryer_id = "D711"
        product_id = "struvite_product"
        exhaust_id = "struvite_dryer_exhaust"
        external_inputs.extend((magnesium, base, seed))
        streams.update(
            struvite_magnesium_solution=magnesium,
            struvite_base_solution=base,
            struvite_seed=seed,
        )
    elif route == "calcium_phosphate":
        calcium = bst.Stream("calcium_reagent_solution")
        base = bst.Stream("calcium_phosphate_base_solution")
        reactor_parameters = calcium_parameters_from_mapping(values)
        reactor = CalciumPhosphateReactor(
            ID="R712",
            ins=(feed, calcium, base),
            outs="calcium_phosphate_slurry",
            parameters=reactor_parameters,
        )
        separator_id = "S712"
        raw_product_id = "raw_wet_calcium_phosphate_product"
        mother_liquor_id = "calcium_phosphate_mother_liquor"
        washer_id = "W712"
        washed_id = "washed_calcium_phosphate_product"
        wash_effluent_id = "calcium_phosphate_wash_effluent"
        dryer_id = "D712"
        product_id = "calcium_phosphate_product"
        exhaust_id = "calcium_phosphate_dryer_exhaust"
        external_inputs.extend((calcium, base))
        streams.update(
            calcium_reagent_solution=calcium,
            calcium_phosphate_base_solution=base,
        )
    else:
        raise ValueError(f"Unsupported Phase 7 phosphorus route '{route}'.")

    separator = CrystalSeparator(
        ID=separator_id,
        ins=reactor - 0,
        outs=(raw_product_id, mother_liquor_id),
        parameters=crystal_parameters,
    )
    wash_water = bst.Stream(f"{route}_wash_water")
    washer = NutrientProductWasher(
        ID=washer_id,
        ins=(separator - 0, wash_water),
        outs=(washed_id, wash_effluent_id),
        target_product_ids=crystal_parameters.target_product_ids,
        parameters=finishing,
    )
    dryer = NutrientProductDryer(
        ID=dryer_id,
        ins=washer - 0,
        outs=(product_id, exhaust_id),
        parameters=finishing,
    )
    for unit in (reactor, separator, washer, dryer):
        _add_unit(units, unit)
    external_inputs.append(wash_water)
    wastewater_sources.append(washer - 1)
    offgas_sources.append(dryer - 1)
    streams.update(
        phosphorus_reactor_feed=feed,
        phosphorus_slurry=reactor - 0,
        raw_phosphorus_product=separator - 0,
        phosphorus_depleted_liquor=separator - 1,
        phosphorus_wash_water=wash_water,
        phosphorus_wash_effluent=washer - 1,
        phosphorus_product=dryer - 0,
        phosphorus_dryer_exhaust=dryer - 1,
    )
    return separator - 1, dryer - 0, {
        "reactor": reactor_parameters,
        "crystal_separator": crystal_parameters,
        "finishing": finishing,
    }


def _attach_stripping_route(
    feed: bst.Stream,
    *,
    values: Mapping[str, object],
    units: dict[str, object],
    streams: dict[str, bst.Stream],
    external_inputs: list[bst.Stream],
    offgas_sources: list[bst.Stream],
) -> tuple[bst.Stream, bst.Stream, dict[str, object]]:
    stripping = stripping_parameters_from_mapping(values)
    absorption = acid_parameters_from_mapping(values)
    base = bst.Stream("ammonia_stripper_base_solution")
    conditioner = AlkalineConditioner(
        ID="M721",
        ins=(feed, base),
        outs="alkaline_conditioned_liquor",
        base_id=str(values["ammonia_base_type"]),
        solution_mass_fraction=_required_float(values, "ammonia_base_solution_mass_fraction"),
        pure_base_dose_kg_m3=_required_float(values, "ammonia_base_dose_kg_m3"),
        target_pH=stripping.pH,
        density_kg_m3=stripping.density_kg_m3,
        mixing_power_kw_m3=_required_float(values, "ammonia_conditioning_mixing_power_kw_m3"),
    )
    heater = ProcessHeater(
        ID="H721",
        ins=conditioner - 0,
        outs="heated_stripper_feed",
        target_temperature_c=stripping.temperature_c,
        heat_capacity_kj_kg_k=_required_float(values, "phase7_liquid_heat_capacity_kj_kg_k"),
    )
    carrier = bst.Stream("ammonia_stripping_carrier")
    stripper = AmmoniaStripper(
        ID="A721",
        ins=(heater - 0, carrier),
        outs=("nitrogen_depleted_liquor", "ammonia_rich_strip_gas"),
        parameters=stripping,
    )
    acid = bst.Stream("ammonia_absorber_acid_solution")
    absorber_water = bst.Stream("ammonia_absorber_makeup_water")
    absorber = AcidAbsorber(
        ID="A722",
        ins=(stripper - 1, acid, absorber_water),
        outs=("cleaned_strip_gas", "ammonium_salt_solution"),
        parameters=absorption,
    )
    storage = ProductStorage(
        ID="V722",
        ins=absorber - 1,
        outs="ammonium_salt_product",
        residence_time_h=_required_float(values, "ammonium_product_storage_time_h"),
    )
    for unit in (conditioner, heater, stripper, absorber, storage):
        _add_unit(units, unit)
    external_inputs.extend((base, carrier, acid, absorber_water))
    offgas_sources.append(absorber - 0)
    streams.update(
        ammonia_recovery_feed=feed,
        ammonia_stripper_base_solution=base,
        alkaline_conditioned_liquor=conditioner - 0,
        heated_stripper_feed=heater - 0,
        ammonia_stripping_carrier=carrier,
        nitrogen_depleted_liquor=stripper - 0,
        ammonia_rich_strip_gas=stripper - 1,
        ammonia_absorber_acid_solution=acid,
        ammonia_absorber_makeup_water=absorber_water,
        cleaned_strip_gas=absorber - 0,
        ammonium_salt_solution=absorber - 1,
        ammonium_product=storage - 0,
    )
    return stripper - 0, storage - 0, {
        "stripping": stripping,
        "acid_absorption": absorption,
    }


def _attach_ion_exchange_route(
    feed: bst.Stream,
    *,
    values: Mapping[str, object],
    units: dict[str, object],
    streams: dict[str, bst.Stream],
    external_inputs: list[bst.Stream],
) -> tuple[bst.Stream, bst.Stream, dict[str, object]]:
    parameters = ion_exchange_parameters_from_mapping(values)
    regenerated = bst.Stream(
        "regenerated_zeolite_recycle",
        SodiumZeolite=1.0,
        units="kmol/hr",
    )
    bed = IonExchangeBed(
        ID="A731",
        ins=(feed, regenerated),
        outs=("ion_exchange_treated_liquor", "loaded_ammonium_zeolite"),
        parameters=parameters,
    )
    brine = bst.Stream("ion_exchange_nacl_brine")
    rinse = bst.Stream("ion_exchange_rinse_water")
    regenerator = IonExchangeRegeneration(
        ID="R731",
        ins=(bed - 1, brine, rinse),
        outs=(regenerated, "ammonium_rich_regenerant_solution"),
        parameters=parameters,
    )
    storage = ProductStorage(
        ID="V722",
        ins=regenerator - 1,
        outs="ammonium_rich_regenerant_product",
        residence_time_h=_required_float(values, "ammonium_product_storage_time_h"),
    )
    for unit in (bed, regenerator, storage):
        _add_unit(units, unit)
    external_inputs.extend((brine, rinse))
    streams.update(
        ammonia_recovery_feed=feed,
        regenerated_zeolite_recycle=regenerated,
        loaded_ammonium_zeolite=bed - 1,
        ion_exchange_nacl_brine=brine,
        ion_exchange_rinse_water=rinse,
        nitrogen_depleted_liquor=bed - 0,
        ammonium_rich_regenerant_solution=regenerator - 1,
        ammonium_product=storage - 0,
    )
    return bed - 0, storage - 0, {"ion_exchange": parameters}


def _attach_potassium_route(
    feed: bst.Stream,
    *,
    values: Mapping[str, object],
    units: dict[str, object],
    streams: dict[str, bst.Stream],
    external_inputs: list[bst.Stream],
    wastewater_sources: list[bst.Stream],
    offgas_sources: list[bst.Stream],
) -> tuple[bst.Stream, bst.Stream | None, dict[str, object]]:
    parameters = potassium_parameters_from_mapping(values)
    if parameters.method == "evaporation":
        concentrator = PotassiumEvaporator(
            ID="E741",
            ins=feed,
            outs=("raw_potassium_concentrate", "evaporator_vapor"),
            parameters=parameters,
        )
        treated_water = None
        offgas_sources.append(concentrator - 1)
        streams["evaporator_vapor"] = concentrator - 1
    elif parameters.method == "membrane":
        cleaning = bst.Stream("potassium_membrane_cleaning_water")
        concentrator = PotassiumMembraneConcentrator(
            ID="M741",
            ins=(feed, cleaning),
            outs=(
                "raw_potassium_concentrate",
                "treated_water",
                "potassium_membrane_cleaning_wastewater",
            ),
            parameters=parameters,
        )
        treated_water = concentrator - 1
        external_inputs.append(cleaning)
        wastewater_sources.append(concentrator - 2)
        streams.update(
            potassium_membrane_cleaning_water=cleaning,
            treated_water=treated_water,
            potassium_membrane_cleaning_wastewater=concentrator - 2,
        )
    else:
        raise ValueError("Potassium concentration method must be evaporation or membrane.")
    storage = ProductStorage(
        ID="V741",
        ins=concentrator - 0,
        outs="potassium_rich_concentrate",
        residence_time_h=_required_float(values, "potassium_product_storage_time_h"),
    )
    for unit in (concentrator, storage):
        _add_unit(units, unit)
    streams.update(
        potassium_recovery_feed=feed,
        raw_potassium_concentrate=concentrator - 0,
        potassium_concentrate=storage - 0,
    )
    return storage - 0, treated_water, {"potassium": parameters}


def _validate_order(scenario: NutrientRecoveryScenario, order: str) -> None:
    if scenario.scenario_id in {"NR0", "NR1"}:
        return
    if order == "D":
        raise ValueError(f"{scenario.scenario_id} includes targeted recovery and cannot use Order D.")
    if order == "C" and scenario.phosphorus_route == "none":
        raise ValueError("Order C requires an active phosphorus-recovery route.")


def create_phase7_scenario(
    scenario_id: str | None = None,
    *,
    phase6_scenario_id: str | None = None,
    phase5_scenario_id: str | None = None,
    phase4_scenario_id: str | None = None,
    phase3_scenario_id: str | None = None,
    selected_month: str | None = None,
    process_order: str | None = None,
    workbook_path: Path = INPUT_WORKBOOK_PATH,
    parameter_overrides: Mapping[str, object] | None = None,
    input_bundle: Phase7InputBundle | None = None,
) -> Phase7Model:
    """Build one fresh NR0-NR7 integrated model without simulating it."""

    bundle = input_bundle or load_phase7_inputs(
        workbook_path,
        scenario_id=scenario_id,
        phase6_scenario_id=phase6_scenario_id,
        phase5_scenario_id=phase5_scenario_id,
        phase4_scenario_id=phase4_scenario_id,
        phase3_scenario_id=phase3_scenario_id,
        selected_month=selected_month,
        process_order=process_order,
    )
    if scenario_id and bundle.scenario_id != scenario_id.upper():
        raise ValueError("Provided Phase7InputBundle does not match requested scenario.")
    scenario = get_nutrient_recovery_scenario(bundle.scenario_id)
    if not scenario.active:
        raise NotImplementedError(f"Phase 7 scenario {scenario.scenario_id} is inactive.")
    _validate_order(scenario, bundle.process_order)
    values = dict(bundle.parameter_values)
    if parameter_overrides:
        values.update(parameter_overrides)
    upstream = create_phase6_scenario(
        bundle.phase6_scenario_id,
        phase5_scenario_id=bundle.phase5_scenario_id,
        phase4_scenario_id=bundle.phase4_scenario_id,
        phase3_scenario_id=bundle.phase3_scenario_id,
        selected_month=bundle.selected_month,
        workbook_path=workbook_path,
    )
    flowsheet = upstream.flowsheet
    units = dict(upstream.units)
    streams = dict(upstream.streams)
    digestate = upstream.streams["digestate"]
    streams["digestate_feed"] = digestate
    external_inputs: list[bst.Stream] = []
    wastewater_sources: list[bst.Stream] = []
    offgas_sources: list[bst.Stream] = []
    phase7_parameters: dict[str, object] = {}
    boundary_outputs: list[bst.Stream] = []
    phase7_unit_start = set(units)

    if scenario.scenario_id == "NR0":
        streams["untreated_digestate"] = digestate
        boundary_outputs.append(digestate)
    else:
        active, equalization_offgas, equalization = _attach_equalization(
            digestate, values, units, streams
        )
        phase7_parameters["equalization"] = equalization
        offgas_sources.append(equalization_offgas)
        phosphorus_product = None
        ammonium_product = None
        potassium_product = None
        treated_water = None

        if bundle.process_order == "C":
            active, phosphorus_product, phosphorus_parameters = _attach_phosphorus_route(
                active,
                route=scenario.phosphorus_route,
                values=values,
                units=units,
                streams=streams,
                external_inputs=external_inputs,
                wastewater_sources=wastewater_sources,
                offgas_sources=offgas_sources,
            )
            phase7_parameters["phosphorus"] = phosphorus_parameters
            solids, active, separation = _attach_separation(active, values, units, streams)
        else:
            solids, active, separation = _attach_separation(active, values, units, streams)
        phase7_parameters["separation"] = separation

        def apply_phosphorus(current: bst.Stream) -> bst.Stream:
            nonlocal phosphorus_product
            if scenario.phosphorus_route == "none" or phosphorus_product is not None:
                return current
            current, phosphorus_product, phosphorus_parameters = _attach_phosphorus_route(
                current,
                route=scenario.phosphorus_route,
                values=values,
                units=units,
                streams=streams,
                external_inputs=external_inputs,
                wastewater_sources=wastewater_sources,
                offgas_sources=offgas_sources,
            )
            phase7_parameters["phosphorus"] = phosphorus_parameters
            return current

        def apply_ammonia(current: bst.Stream) -> bst.Stream:
            nonlocal ammonium_product
            if scenario.ammonia_route == "none":
                return current
            if scenario.ammonia_route == "stripping":
                current, ammonium_product, ammonia_parameters = _attach_stripping_route(
                    current,
                    values=values,
                    units=units,
                    streams=streams,
                    external_inputs=external_inputs,
                    offgas_sources=offgas_sources,
                )
            elif scenario.ammonia_route == "ion_exchange":
                current, ammonium_product, ammonia_parameters = _attach_ion_exchange_route(
                    current,
                    values=values,
                    units=units,
                    streams=streams,
                    external_inputs=external_inputs,
                )
            else:
                raise ValueError(f"Unsupported ammonia route '{scenario.ammonia_route}'.")
            phase7_parameters["ammonia"] = ammonia_parameters
            return current

        if bundle.process_order == "B":
            active = apply_ammonia(active)
            active = apply_phosphorus(active)
        elif bundle.process_order in {"A", "C"}:
            active = apply_phosphorus(active)
            active = apply_ammonia(active)

        if scenario.potassium_route == "concentration":
            potassium_product, treated_water, potassium_parameters = _attach_potassium_route(
                active,
                values=values,
                units=units,
                streams=streams,
                external_inputs=external_inputs,
                wastewater_sources=wastewater_sources,
                offgas_sources=offgas_sources,
            )
            phase7_parameters.update(potassium_parameters)
        else:
            streams["residual_liquor"] = active

        phase7_wastewater = _aggregate_streams(
            unit_id="M798",
            output_id="phase7_wastewater",
            sources=wastewater_sources,
            units=units,
        )
        phase7_offgas = _aggregate_streams(
            unit_id="M799",
            output_id="phase7_offgas",
            sources=offgas_sources,
            units=units,
        )
        streams.update(
            phase7_wastewater=phase7_wastewater,
            phase7_offgas=phase7_offgas,
        )
        boundary_outputs.append(solids)
        if phosphorus_product is not None:
            boundary_outputs.append(phosphorus_product)
        if ammonium_product is not None:
            boundary_outputs.append(ammonium_product)
        if potassium_product is not None:
            boundary_outputs.append(potassium_product)
            if treated_water is not None:
                boundary_outputs.append(treated_water)
        else:
            boundary_outputs.append(active)
        if wastewater_sources:
            boundary_outputs.append(phase7_wastewater)
        if offgas_sources:
            boundary_outputs.append(phase7_offgas)

    boundary = _deduplicate_streams(boundary_outputs)
    final_ends = [
        *_phase5_boundary_side_products(upstream.upstream_model.upstream_model),
        upstream.streams["uncaptured_biogas"],
        *upstream.boundary_outputs,
        *boundary,
    ]
    phase7_unit_ids = tuple(unit_id for unit_id in units if unit_id not in phase7_unit_start)
    has_recycle = bool(upstream.parameters.get("has_recycle")) or scenario.ammonia_route == "ion_exchange"
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
            f"{PHASE7_SYSTEM_ID}_{bundle.phase3_scenario_id.lower()}_"
            f"{bundle.phase4_scenario_id.lower()}_{bundle.phase5_scenario_id.lower()}_"
            f"{bundle.phase6_scenario_id.lower()}_{scenario.scenario_id.lower()}_"
            f"order{bundle.process_order.lower()}"
        ),
        ends=tuple(final_ends),
        operating_hours=OPERATING_HOURS_PER_YEAR,
        **system_kwargs,
    )
    if has_recycle:
        system.set_tolerance(
            mol=1e-8,
            rmol=1e-7,
            T=1e-4,
            subsystems=True,
            maxiter=200,
            method="aitken",
        )
    parameters: dict[str, object] = {
        "values": values,
        "phase7": phase7_parameters,
        "phase7_unit_ids": phase7_unit_ids,
        "has_recycle": has_recycle,
        "recovered_heat_available_kw": float(values.get("phase7_recovered_heat_available_kw", 0.0)),
        "recovered_heat_temperature_c": float(values.get("phase7_recovered_heat_temperature_c", 0.0)),
        "heat_recovery_efficiency": float(values.get("phase7_heat_recovery_efficiency", 0.0)),
        "chp_electricity_available_kw": float(values.get("phase7_chp_electricity_available_kw", 0.0)),
        "sizing_safety_factor": float(values.get("phase7_sizing_safety_factor", 1.0)),
    }
    warnings = [*bundle.warnings, *upstream.warnings]
    assumptions = (
        "Phase 7 receives the selected Phase 5 digestate through the integrated Phase 6 graph; no fixed digestate template is used.",
        "Independent monthly steady states represent seasonality; no hourly tank dynamics or campaign scheduling is claimed.",
        "Only explicit Orthophosphate is available to mineral precipitation; unspeciated P-equivalent pools remain unrecovered.",
        "R711/R712 and A721 are formula-balanced Level-1 engineering models, not rigorous electrolyte or rate-based simulations.",
        "Potassium concentration is non-selective and no pure potassium fertilizer is claimed.",
        "Custom Phase 7 equipment has zero CAPEX because approved cost correlations and vendor quotations are unavailable.",
        "The repository has no active CHP or plant utility network; recovered heat defaults to zero and is only credited through a bounded temperature-compatible interface.",
        "Nutrient products and treated water require experimental characterization and regulatory assessment before any eligibility claim.",
    )
    if bundle.structural_test_mode:
        warnings.append(
            "Phase 7 structural-test mode is active; quality-class E recoveries, reagent doses, utilities, and design values are placeholders."
        )
    model = Phase7Model(
        flowsheet=flowsheet,
        system=system,
        scenario=scenario,
        upstream_model=upstream,
        units=units,
        streams=streams,
        parameters=parameters,
        input_bundle=bundle,
        external_inputs=tuple(external_inputs),
        boundary_outputs=boundary,
        warnings=tuple(dict.fromkeys(warnings)),
        assumptions=assumptions,
    )
    from Greenhub.phase7_limitations import build_phase7_limitations

    model.limitations = build_phase7_limitations(model)
    model.data_needs = tuple(
        dict.fromkeys(
            limitation.data_needed
            for limitation in model.limitations
            if limitation.data_needed
        )
    )
    return model


def simulate_phase7_season(
    scenario_id: str,
    *,
    phase6_scenario_id: str | None = None,
    phase5_scenario_id: str | None = None,
    phase4_scenario_id: str | None = None,
    phase3_scenario_id: str | None = None,
    process_order: str | None = None,
    workbook_path: Path = INPUT_WORKBOOK_PATH,
    months: tuple[str, ...] = (
        "January", "February", "March", "April", "May", "June",
        "July", "August", "September", "October", "November", "December",
    ),
) -> object:
    """Simulate independent monthly nutrient-recovery states and aggregate them."""

    from Greenhub.phase7_metrics import (
        aggregate_monthly_phase7_metrics,
        snapshot_monthly_phase7_model,
    )

    monthly_snapshots: list[object] = []
    warnings: list[str] = []
    for month in months:
        try:
            monthly_model = create_phase7_scenario(
                scenario_id,
                phase6_scenario_id=phase6_scenario_id,
                phase5_scenario_id=phase5_scenario_id,
                phase4_scenario_id=phase4_scenario_id,
                phase3_scenario_id=phase3_scenario_id,
                selected_month=month,
                process_order=process_order,
                workbook_path=workbook_path,
            )
            monthly_model.simulate()
            monthly_snapshots.append(snapshot_monthly_phase7_model(monthly_model))
            del monthly_model
            gc.collect()
        except (ValueError, NotImplementedError) as error:
            warnings.append(f"{month}: {error}")
    if not monthly_snapshots:
        raise ValueError(f"No monthly Phase 7 simulations succeeded for scenario {scenario_id}.")
    return aggregate_monthly_phase7_metrics(monthly_snapshots, tuple(warnings))
