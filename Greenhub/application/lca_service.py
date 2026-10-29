"""Read-only post-route climate inventory; missing evidence never becomes zero."""
from dataclasses import asdict, dataclass
from Greenhub.lca_inventory import ClimateFactor, coerce_basis, coerce_flow, load_climate_factors, GROUPS, METHOD


@dataclass(frozen=True)
class LCAReport:
    payload: dict
    def to_dict(self): return self.payload


def screening_lca_factors():
    """Return opt-in screening factors already present in the data register."""
    return {
        "electricity": ClimateFactor(
            factor_id="electricity", value=0.20, quantity_unit="kWh",
            source_status="proxy_factor", basis="CBS integral electricity generation factor",
            geography="Netherlands", reference_year=2024,
            source_url="https://www.cbs.nl/en-gb/background/2025/49/energy-and-emission-factors-electricity-update-2024",
            source_table_page="Electricity emission factors update 2024",
            retrieval_date="2026-10-28", evidence_class="official_dataset_proxy",
            applicability="Screening proxy for Dutch electricity generation; replace with declared consumption LCI.",
            conversion_method="identity", uncertainty="Consumption mix and market-boundary uncertainty not quantified",
            warning="Opt-in screening proxy; not a supplier-specific attributional or consequential electricity LCI.",
        )
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
    def row(name,group,q,unit,factor,**kwargs):
        return dict(flow_id=name,group=group,quantity=q,unit=unit,factor_id=factor,accounting_key=name,source_id='simulation:'+result.run_id,**kwargs)
    inventory=[row('electricity','electricity',electricity,'kWh','electricity'),row('heat','heat',heat,'kWh','heat')]
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
            'screening_activation':'Set use_screening_lca_factors=true to opt in; explicit climate_factors overrides take precedence.',
            'note':'Missing utility factors and inventories require explicit evidence; no generic fertilizer credit is applied.'}
