"""Read-only post-route climate inventory; missing evidence never becomes zero."""
import csv
from dataclasses import asdict, dataclass
from pathlib import Path
from Greenhub.lca_inventory import ClimateFactor, coerce_basis, coerce_flow, load_climate_factors, GROUPS, METHOD


@dataclass(frozen=True)
class LCAReport:
    payload: dict
    def to_dict(self): return self.payload


def screening_lca_factors():
    """Return opt-in utility and PR7 chemical climate factors for screening."""
    return {
        "electricity": ClimateFactor(
            factor_id="electricity", value=0.406463, quantity_unit="kWh",
            source_status="official_dataset", basis="JRC life-cycle electricity factor 0.406463 t CO2e/MWh, including upstream electricity supply-chain emissions",
            geography="Netherlands", reference_year=2021,
            source_url="https://doi.org/10.2905/JRC.4800KC0; https://data.europa.eu/89h/919df040-0252-4e4e-ad82-c054896e1641",
            source_table_page="Table3_EU_LC, Netherlands row, 2021 column",
            retrieval_date="2026-11-05", evidence_class="official_dataset",
            applicability="National Netherlands consumption mix; lifecycle grid factor, not a site-specific supplier factor. Published series ends in 2021.",
            conversion_method="1 t CO2e/MWh = 1 kg CO2e/kWh",
            uncertainty="Dataset point estimate; no probability distribution imposed.",
            warning="Includes upstream electricity supply-chain emissions and uses 2021 grid data.",
        ),
        "heat": ClimateFactor(
            factor_id="heat", value=30.96 / 277.7777777778, quantity_unit="kWh",
            source_status="direct_literature", basis="CE Delft reports 30.96 kg CO2e/GJ total end-user heat factor for Dutch heat grids in 2022; converted using 1 GJ = 277.7778 kWh",
            geography="Netherlands", reference_year=2022,
            source_url="https://cedelft.eu/publications/chain-emissions-for-heat-grids-in-2022-and-2030/",
            source_table_page="End-user heat-grid factor, 2022",
            retrieval_date="2026-11-05", evidence_class="B",
            applicability="Dutch average heat-grid factor based on reported 2022 heat-source deployment; not a site- or supplier-specific network factor.",
            conversion_method="30.96 kg CO2e/GJ ÷ 277.7778 kWh/GJ",
            uncertainty="Published national average; source page does not provide a probability distribution. Do not treat this point estimate as site-specific.",
            warning="Average 2022 heat-grid factor; not a supplier-specific plant factor.",
        ),
        **_screening_chemical_climate_factors(),
    }


def _screening_chemical_climate_factors():
    """Load opt-in PR7 reagent factors from their provenance register."""
    path = (
        Path(__file__).resolve().parents[1]
        / "data" / "Protein recovery" / "Membrane" / "biostimulant_chemical_lca_factors.csv"
    )
    with path.open("r", newline="", encoding="utf-8-sig") as handle:
        rows = list(csv.DictReader(handle))
    return {
        row["factor_id"]: ClimateFactor(
            factor_id=row["factor_id"],
            value=float(row["value"]),
            quantity_unit=row["quantity_unit"],
            source_status=row["source_status"],
            basis=f"{row['system_boundary']}; {row['allocation']}; {row['model_use']}",
            geography=row["geography"],
            reference_year=int(row["reference_year"]),
            source_url=row["source_url"],
            source_table_page=row["source_title"],
            retrieval_date=row["retrieval_date"],
            evidence_class=row["evidence_class"],
            applicability=row["model_use"],
            conversion_method="identity; factor value is kg CO2e per kg active reagent",
            uncertainty=row["uncertainty"],
            method=row["method"],
            warning=row["warning"],
        )
        for row in rows
    }


def calculate_lca_inventory(inventory, project_basis=None, *, factors=None):
    basis=coerce_basis(project_basis); factors=load_climate_factors(factors)
    rows=[]; keys=set(); missing=[]; credit_missing=[]; inventory_gaps=[]
    partial=0.0; credits=0.0; burden_count=0; credit_count=0
    for raw in inventory:
        flow=coerce_flow(raw)
        if flow.accounting_key in keys:
            raise ValueError("Duplicate inventory accounting key: "+flow.accounting_key)
        keys.add(flow.accounting_key)
        if flow.group not in basis.included_groups: continue
        factor=factors.get(flow.factor_id)
        impact=None
        if flow.direction=='credit' and not basis.substitution_enabled:
            status='substitution_disabled'
        elif flow.direction=='memorandum':
            status='memorandum'
            if flow.quantity is None: inventory_gaps.append(flow.flow_id+': missing memorandum quantity')
        elif flow.quantity is None: status='missing_quantity'
        elif factor is not None and flow.unit!=factor.quantity_unit:
            raise ValueError(f"Incompatible inventory/factor units for {flow.flow_id}.")
        elif flow.quantity==0:
            # An explicit zero activity is evidence, unlike an absent flow/factor.
            status='explicit_zero_quantity'; impact=0.0
        elif factor is None or factor.value is None: status='missing_factor'
        else:
            status='characterized'; impact=flow.quantity*factor.value
        if impact is not None:
            if flow.direction=='credit': credits+=impact; credit_count+=1
            else: partial+=impact; burden_count+=1
        if status in ('missing_quantity','missing_factor'):
            (credit_missing if flow.direction=='credit' else missing).append(flow.flow_id+': '+status)
        rows.append({**flow.to_dict(),'climate_kg_co2e':impact,'status':status})
    for group in basis.included_groups:
        declaration=basis.inventory_completeness.get(group,{})
        if declaration.get('status')!='complete': missing.append(group+': inventory boundary incomplete')
        if not any(row['group']==group and row['direction']=='burden' for row in rows):
            missing.append(group+': no explicit burden inventory (zero must be declared as a flow)')
    complete=not missing
    total=partial if complete else None
    credit_complete=basis.substitution_enabled and credit_count>0 and not credit_missing
    wet=basis.annual_throughput_kg; dry=basis.annual_dry_feed_kg
    return LCAReport({
        'schema_version':'greenhub-climate-inventory-1.0','analysis_type':'climate_screening_not_complete_LCA',
        'project_basis':asdict(basis),'method':METHOD,
        'scope_declaration':{
            'boundary':basis.boundary,
            'functional_units':{
                'annual_total':'kg CO2e/year',
                'wet_feed_intensity':'kg CO2e/tonne wet feed',
                'dry_feed_intensity':'kg CO2e/tonne dry feed',
            },
            'reference_flows':{
                'wet_feed_kg_per_year':wet,
                'dry_feed_kg_per_year':dry,
            },
            'allocation': 'whole-plant attributional burdens; coproduct substitution credits reported separately',
            'substitution_enabled':basis.substitution_enabled,
            'included_inventory_groups':list(basis.included_groups),
            'excluded_inventory_groups':dict(basis.exclusions),
        },
        'inventory':rows,
        'totals':{'climate_kg_co2e_per_year':total,'partial_climate_kg_co2e_per_year':partial if burden_count else None,
                  'substitution_credit_kg_co2e_per_year':credits if credit_complete else None,
                  'partial_substitution_credit_kg_co2e_per_year':credits if credit_count else None,
                  'substitution_net_kg_co2e_per_year':partial-credits if complete and credit_complete else None,
                  'kg_co2e_per_tonne_wet_feed':total/(wet/1000) if total is not None and wet else None,
                  'kg_co2e_per_tonne_dry_feed':total/(dry/1000) if total is not None and dry else None},
        'missing_inputs':missing,'substitution_missing_inputs':credit_missing,'inventory_gaps':inventory_gaps,
        'factors':[factor.to_dict() for factor in factors.values()],
        'readiness':{'climate_objective_eligible':complete,'substitution_objective_eligible':complete and credit_complete,
                     'validated_lca_ready':False},
        'warnings':['Only climate is characterized. Nutrient emissions require separate characterization factors.',
                    'Whole-plant attributional burdens and optional quality-verified substitution credits are reported separately.',
                    'Biogenic CO2 is reported as a memorandum, without claiming permanent carbon storage or a complete carbon cycle.']})


def logistics_to_lca_inventory(logistics_result, *, source_id="logistics"):
    """Convert an explicit logistics result into a traceable transport flow.

    The logistics module reports fuel-combustion emissions after applying its
    explicit fuel emission factor. Treat that result as a characterized fossil
    CO2 mass using the registry identity factor; unresolved logistics inputs
    still remain missing rather than becoming zero.
    """
    if hasattr(logistics_result, "to_dict"):
        logistics_result = logistics_result.to_dict()
    if not isinstance(logistics_result, dict):
        raise TypeError("logistics_result must be a mapping or provide to_dict().")
    limitations = tuple(logistics_result.get("limitations") or ())
    return ({
        "flow_id": "feedstock_transport",
        "group": "transport",
        "quantity": None if limitations else logistics_result.get("emissions_kg_co2"),
        "unit": "kg",
        "factor_id": "fossil_co2",
        "accounting_key": "transport_feedstock_combustion",
        "source_id": source_id,
        "source_status": "model_output" if not limitations else "incomplete_input",
        "warning": "Logistics result is already characterized from explicit fuel use and fuel emission factor; fossil CO2 identity factor applied."
        + ((" Limitations: " + "; ".join(str(item) for item in limitations)) if limitations else ""),
        "basis": "explicit logistics result; kg CO2e activity before characterization",
        "conversion_method": "identity",
    },)


def calculate_empirical_lca(result, project_basis=None, *, factors=None, additional_inventory=(), logistics_result=None):
    if result is None or not hasattr(result,'seasonal_summary') or getattr(result,'status','completed')!='completed':
        raise ValueError('LCA requires a completed empirical or seasonal SimulationResult.')
    basis=coerce_basis(project_basis); seasonal=result.seasonal_summary
    hours=basis.operating_hours_per_year
    if seasonal:
        if getattr(getattr(result, "selected_scenarios", None), "protein_recovery", None) == "PR7":
            hours = seasonal.get("active_process_operating_hours")
        energy=seasonal.get('total_utilities',{})
        electricity=energy.get('electricity_kwh'); heat=energy.get('heating_kwh')
    else:
        def annual_utility(kind):
            utilities=[u for u in result.utilities if u.kind==kind]
            if hours is None or not utilities or any(u.demand.value is None for u in utilities): return None
            if kind=='electricity':
                if any(u.demand.unit not in ('kW','kWh/hr','kWh/h') for u in utilities):
                    raise ValueError('Empirical electricity demand must be kW or kWh/h.')
                # Negative electricity is generation; it is not automatically a supply credit.
                return sum(max(0,float(u.demand.value)) for u in utilities)*hours
            if any(u.demand.unit not in ('kJ/hr','kJ/h') for u in utilities):
                raise ValueError('Empirical heat demand must be kJ/h.')
            return sum(max(0,float(u.demand.value)) for u in utilities)/3600*hours
        electricity=annual_utility('electricity'); heat=annual_utility('heat')
    def row(name,group,q,unit,factor,*,source_id=None,**kwargs):
        return dict(flow_id=name,group=group,quantity=q,unit=unit,factor_id=factor,accounting_key=name,source_id=source_id or 'simulation:'+result.run_id,**kwargs)
    inventory=[row('electricity','electricity',electricity,'kWh','electricity'),row('heat','heat',heat,'kWh','heat')]
    if getattr(getattr(result, "selected_scenarios", None), "protein_recovery", None) == "PR7":
        pr7_unit = next((item for item in result.units if item.unit_id == "PR7_M101"), None)
        pr7_metrics = next((item.metrics for item in result.process_areas if item.process_area_id == "protein_recovery"), {})
        pressure_known = bool(
            pr7_unit
            and pr7_unit.design_results.get("Transmembrane pressure") is not None
            and pr7_unit.design_results.get("Pump efficiency") is not None
        )
        if not pressure_known:
            inventory.append(row(
                "pr7_permeate_pressure_work", "electricity", None, "kWh", "electricity",
                warning="No sourced TMP/pump-efficiency pair supplied; PR7 idealized permeate-side electricity is unresolved.",
                source_id="simulation:PR7_M101",
            ))
        if pr7_metrics.get("biostimulant_crossflow_electricity_kwh_m3_feed") is None:
            inventory.append(row(
                "pr7_crossflow_electricity", "electricity", None, "kWh", "electricity",
                warning="Crossflow recirculation electricity is unresolved; no specific-energy default is assumed.",
                source_id="simulation:PR7_M101"))
        inventory.append(row(
            "pr7_other_auxiliary_electricity", "electricity", None, "kWh", "electricity",
            warning="Controls, instrumentation, cleaning, and other auxiliary electricity are not modeled; supplied crossflow energy is already included in the whole-plant electricity flow.",
            source_id="simulation:PR7_M101"))
        cip_volume = pr7_metrics.get("biostimulant_cip_solution_volume_L_per_step")
        cip_makeup = pr7_metrics.get("biostimulant_cip_makeup_fraction_per_cycle")
        cip_source = pr7_metrics.get("biostimulant_cip_input_source")
        pr7_cip_hours = (
            seasonal.get("active_process_operating_hours")
            if seasonal else hours
        )
        if cip_volume is not None and cip_makeup is not None and cip_source and pr7_cip_hours is not None:
            from Greenhub.biostimulant_screening import calculate_cip_reagent_screen
            cip = calculate_cip_reagent_screen(
                operating_hours_year=float(pr7_cip_hours),
                solution_volume_L_per_step=float(cip_volume),
                makeup_fraction_per_cycle=float(cip_makeup),
                input_source=str(cip_source),
            )
            inventory.extend((
                row("pr7_cip_naoh_active_makeup", "materials", cip["naoh"]["active_naoh_kg_year"], "kg", "pr7_cip_naoh_active",
                    warning="CIP active NaOH quantified; opt-in European industry-average upstream factor applied when screening factors are enabled. Cleaning wastewater fate remains unresolved.",
                    source_id="simulation:PR7_M101"),
                row("pr7_cip_citric_acid_makeup", "materials", cip["citric_acid"]["citric_acid_kg_year"], "kg", "pr7_cip_citric_acid",
                    warning="CIP citric acid quantified; opt-in Belgian producer cradle-to-gate proxy applied when screening factors are enabled. Cleaning wastewater fate remains unresolved.",
                    source_id="simulation:PR7_M101"),
            ))
        else:
            inventory.append(row(
                "pr7_cip_chemical_inventory", "materials", None, "kg", None,
                warning="CIP solution volume and make-up fraction with evidence note are required to calculate the working-chemical inventory; upstream production factors and waste fate are also missing.",
                source_id="simulation:PR7_M101"))
        if getattr(result.selected_scenarios, "protein_recovery", None) == "PR7":
            if pr7_metrics.get("biostimulant_membrane_technology") == "MEUF":
                meuf_inventory = None
                feed_rate = pr7_metrics.get("biostimulant_feed_volume_m3_hr")
                if seasonal:
                    annual_feed_volume = seasonal.get("pr7_feed_volume_m3_year")
                    if annual_feed_volume is not None:
                        from Greenhub.biostimulant_screening import calculate_meuf_surfactant_screen
                        meuf_inventory = calculate_meuf_surfactant_screen(float(annual_feed_volume))
                elif feed_rate is not None and hours is not None:
                    from Greenhub.biostimulant_screening import calculate_meuf_surfactant_screen
                    meuf_inventory = calculate_meuf_surfactant_screen(float(feed_rate) * float(hours))
                if meuf_inventory:
                    for dose_key, label in (("dose_low", "low"), ("dose_high", "high")):
                        dose = meuf_inventory[dose_key]
                        inventory.append(row(
                            f"pr7_meuf_sds_makeup_{label}", "materials",
                            dose["unrecovered_makeup_SDS_kg_year"], "kg", None,
                            scenario=label,
                            warning="Calculated unrecovered SDS screening quantity from the user-supplied CMC dose and 94.5% recovery; no upstream climate factor, acid inventory, residual-fate allocation, or single selected dose is available.",
                            source_id="simulation:PR7_M101"))
                else:
                    inventory.append(row(
                        "pr7_meuf_surfactant_makeup", "materials", None, "kg", None,
                        warning="Annual MEUF SDS make-up is unresolved because no supported clarified-juice volume basis is available.",
                        source_id="simulation:PR7_M101"))
        unresolved_mass_kg_year = None
        unresolved_ids = ()
        if seasonal:
            unresolved_mass_kg_year = seasonal.get("pr7_unresolved_mass_kg_year")
            unresolved_ids = seasonal.get("pr7_unresolved_component_ids", ())
        else:
            unresolved_stream = next(
                (stream for stream in result.streams if "biostimulant_unresolved" in stream.aliases), None
            )
            if unresolved_stream is not None:
                if hours is not None:
                    unresolved_mass_kg_year = float(unresolved_stream.total_mass.value or 0.0) * float(hours)
                unresolved_ids = tuple(
                    component_id for component_id, value in unresolved_stream.components.items()
                    if value.value is not None and float(value.value) > 1e-12
                )
                unresolved_rate = float(unresolved_stream.total_mass.value or 0.0)
            else:
                unresolved_rate = 0.0
        unresolved_present = (
            unresolved_mass_kg_year is not None and float(unresolved_mass_kg_year) > 1e-12
        ) or (not seasonal and unresolved_rate > 1e-12)
        if unresolved_present:
            unresolved_quantity = (
                float(unresolved_mass_kg_year)
                if unresolved_mass_kg_year is not None else None
            )
            inventory.append(row(
                "pr7_unresolved_membrane_pool_fate", "materials", unresolved_quantity, "kg", None,
                direction="burden", compartment="unresolved",
                warning=("PR7 mass is conserved at the unresolved outlet, but component-specific membrane fate is unknown; "
                         "quantity is annualized only when an operating-hours basis is available; "
                         "no climate factor or product allocation is applied. Pools: " + ", ".join(unresolved_ids)),
                source_id="simulation:PR7_M101"))
    # Exported process gases are inventories, not automatically atmospheric emissions.
    terminal={}
    if seasonal:
        for step in result.product_series:
            for name,components in step.get('terminal_gases_kg',{}).items():
                for chemical,mass in components.items(): terminal[(name,chemical)]=terminal.get((name,chemical),0)+mass
    else:
        for stream in result.streams:
            if stream.sink_unit is not None: continue
            names=set(stream.aliases)&{'uncaptured_biogas','reject_gas','phase7_offgas','chp_exhaust'}
            if not names: continue
            for chemical,mass in stream.components.items():
                if mass.value is None or mass.value>0:
                    terminal[(sorted(names)[0],chemical)]=float(mass.value)*hours if mass.value is not None and hours is not None else None
    for (name,chemical),mass in terminal.items():
        factor={'Methane':'biogenic_methane','NitrousOxide':'nitrous_oxide'}.get(chemical)
        memorandum=chemical in {'CarbonDioxide','Water','Nitrogen','Oxygen','Ammonia','HydrogenSulfide'}
        inventory.append(row('process_'+name+'_'+chemical,'process_emissions',mass,'kg',factor if basis.terminal_gas_fate=='emitted' else None,
                             direction='memorandum' if memorandum else 'burden',compartment='air' if basis.terminal_gas_fate=='emitted' else 'unresolved',
                             warning='Terminal gas fate unresolved.' if basis.terminal_gas_fate=='unresolved' else 'Explicit assumption: terminal gas emitted with no flare/recovery. NH3/H2S remain nutrient/toxicity inventory; not characterized in climate-only scope.'))
    storage=[]
    for entry in result.storage_inventory_series:
        for stage in ('incoming_residence','carried_inventory_reactions'):
            report=entry.get(stage)
            if not report: continue
            mult=1 if seasonal else hours
            emissions=report.get('emissions_kg')
            if emissions is None: storage.append(row('storage_unknown_'+stage+'_'+str(entry['time']),'storage_emissions',None,'kg',None))
            else:
                for chemical, mass in emissions.items():
                    factor={'CarbonDioxide':'biogenic_co2','Methane':'biogenic_methane'}.get(chemical)
                    storage.append(row('storage_'+stage+'_'+str(entry['time'])+'_'+chemical,'storage_emissions',mass*mult if mult is not None else None,'kg',factor,direction='memorandum' if chemical=='CarbonDioxide' else 'burden'))
                if not emissions and not report.get('blockers'):
                    storage.append(row('storage_no_emissions_'+stage+'_'+str(entry['time']),'storage_emissions',0.0,'kg',None,
                                       warning='Explicit no-emission ledger for this modeled residence period; not inferred from missing kinetics.'))
                if report.get('emissions_inventory_complete') is False or report.get('blockers'):
                    storage.append(row('storage_unresolved_pathways_'+stage+'_'+str(entry['time']),'storage_emissions',None,'kg',None,
                                       warning='Storage reaction subset has unresolved pathways, leaching or blocked species; group declaration cannot remove this gap.'))
        if entry.get('degradation_loss_kg',0)>0 and not entry.get('carried_inventory_reactions'):
            storage.append(row('storage_uncharacterized_'+str(entry['time']),'storage_emissions',entry['degradation_loss_kg'],'kg',None))
    inventory+=storage
    if basis.methane_emitted_fraction is not None:
        # Requires a separately supplied measured/modelled raw methane quantity;
        # biomethane product is not silently used as a raw-gas methane surrogate.
        inventory.append(row('unresolved_methane_leakage','process_emissions',None,'kg','biogenic_methane',warning='Supply methane leakage mass in additional_inventory; fraction alone lacks an eligible raw methane basis.'))
    extra_rows = list(additional_inventory)
    if logistics_result is not None:
        extra_rows.extend(logistics_to_lca_inventory(logistics_result))
    extra=[coerce_flow(flow) for flow in extra_rows]
    for flow in extra:
        if any(r['accounting_key']==flow.accounting_key for r in inventory):
            raise ValueError('Additional inventory duplicates process accounting key: '+flow.accounting_key)
    inventory+=extra
    return calculate_lca_inventory(inventory,basis,factors=factors)


def lca_options():
    return {'project_basis':asdict(coerce_basis(None)),'factor_templates':[f.to_dict() for f in load_climate_factors().values()],
            'screening_factors': {key: value.to_dict() for key, value in screening_lca_factors().items()},
            'inventory_groups':GROUPS,'supported_impacts':['climate_GWP100'],
            'screening_activation':'Set use_screening_lca_factors=true to opt in to Netherlands utility plus PR7 CIP reagent factors; explicit climate_factors overrides take precedence. PR7 membrane manufacture/replacement and unresolved auxiliary inventories remain uncharacterized.',
            'note':'Missing utility factors and inventories require explicit evidence; no generic fertilizer credit is applied. PR7 membrane-manufacturing figures in the evidence register are reference-only and are not included in climate totals.'}
