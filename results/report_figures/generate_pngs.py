"""Publication PNGs from saved, real GreenHub simulation outputs.

Run from the repository root with .venv/Scripts/python.exe. This script never
changes model inputs or fills missing financial/climate objectives.
"""
from __future__ import annotations

import csv
import json
import math
from collections import Counter, defaultdict
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import PathPatch, Rectangle
from matplotlib.path import Path as MPath

ROOT=Path(__file__).resolve().parents[2]
OUT=Path(__file__).resolve().parent
SRC=ROOT/'scientific_report'
BASE=json.loads((SRC/'baseline_report.json').read_text(encoding='utf-8'))
run_dir=next((SRC/'model_runs').iterdir())
STREAMS={x['stream_id']:x for x in json.loads((run_dir/'streams.json').read_text(encoding='utf-8'))}
UNITS=json.loads((run_dir/'units.json').read_text(encoding='utf-8'))
with (SRC/'route_comparison.csv').open(encoding='utf-8-sig',newline='') as f: old=list(csv.DictReader(f))
with (OUT/'extra_cases.csv').open(encoding='utf-8-sig',newline='') as f: extra=list(csv.DictReader(f))
ROUTES={x['case_id']:x for x in old+extra if not x.get('error')}
season_dir=next((ROOT/'Greenhub/results/checkpoint3c_may_nov_final').iterdir())
SEASON={name:json.loads((season_dir/(name+'.json')).read_text(encoding='utf-8')) for name in ('throughput_series','product_series','utility_series','feed_supply_series')}

BG='#efebe6'; PANEL='#f8f5f1'; INK='#0c3338'; MUTED='#587174'
GREEN='#408f4d'; BLUE='#729ad2'; YELLOW='#d1a520'; ROSE='#d277a3'; SAND='#e4b839'
STAGE={'feed_preparation_and_primary_separation':BLUE,'protein_recovery':GREEN,
       'anaerobic_digestion':YELLOW,'biogas_conditioning_and_upgrading':ROSE,
       'digestate_treatment_and_nutrient_recovery':SAND}
PRODUCT={'dry_protein_product':GREEN,'phosphorus_product':YELLOW,'ammonium_product':BLUE,
         'nutrient_rich_solids':SAND,'potassium_concentrate':ROSE}
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':10.5,'axes.titlesize':14,'axes.labelsize':11,
                     'axes.edgecolor':INK,'axes.labelcolor':INK,'text.color':INK,'xtick.color':INK,
                     'ytick.color':INK,'figure.facecolor':BG,'axes.facecolor':BG,
                     'savefig.facecolor':BG,'savefig.dpi':300})
INDEX=[]
H=8760.0

def number(row,key):
    value=row.get(key)
    return float(value) if value not in ('',None) else None

def save(fig,folder,name,title,description,source,scenario,units,notes=''):
    path=OUT/folder/f'{name}.png';path.parent.mkdir(parents=True,exist_ok=True)
    fig.tight_layout(pad=1.5)
    fig.savefig(path,dpi=300,bbox_inches='tight',pad_inches=.16)
    plt.close(fig)
    INDEX.append({'figure':name,'description':description,'source_dataset':source,'scenario':scenario,
                  'units':units,'file_location':str(path),'notes':notes})

def ax_style(ax,axis='x'):
    ax.spines[['top','right']].set_visible(False)
    ax.grid(axis=axis,alpha=.14,linewidth=.7)
    ax.set_axisbelow(True)

def hbar(folder,name,title,labels,values,unit,source,scenario,description,color=GREEN,notes='',sort=False):
    pairs=[(str(a),float(b)) for a,b in zip(labels,values) if b is not None and math.isfinite(float(b))]
    if not pairs:return
    if sort:pairs.sort(key=lambda x:x[1],reverse=True)
    fig,ax=plt.subplots(figsize=(7.35,max(3.2,0.42*len(pairs)+1.55)))
    labels,values=zip(*pairs); y=np.arange(len(values))
    ax.barh(y,values,color=color,height=.7);ax.set_yticks(y,labels);ax.invert_yaxis()
    ax.set_xlabel(unit);ax.set_title(title,loc='left',pad=12);ax_style(ax)
    if min(values)<0<max(values):ax.axvline(0,color=INK,lw=.9)
    save(fig,folder,name,title,description,source,scenario,unit,notes)

def vbar(folder,name,title,labels,values,unit,source,scenario,description,color=GREEN,notes=''):
    fig,ax=plt.subplots(figsize=(7.35,4.5));x=np.arange(len(values))
    ax.bar(x,values,color=color,width=.66);ax.set_xticks(x,labels,rotation=20,ha='right')
    ax.set_ylabel(unit);ax.set_title(title,loc='left',pad=12);ax_style(ax,'y')
    save(fig,folder,name,title,description,source,scenario,unit,notes)

def comp(stream):return {k:v['value'] for k,v in STREAMS[stream]['components'].items()}
def stream_mass(stream):return STREAMS[stream]['total_mass']['value']
def normalized_dry_volume(stream,hours=H):
    # Dry ideal-gas amount at 273.15 K, 101325 Pa. Explicit MW in kg/kmol.
    MW={'Methane':16.043,'CarbonDioxide':44.0095,'Ammonia':17.031,
        'HydrogenSulfide':34.081,'Nitrogen':28.0134,'Oxygen':31.998}
    masses=comp(stream)
    other=set(masses)-set(MW)-{'Water'}
    assert not other, f'Unsupported gas components: {other}'
    kmol=sum(v/MW[k] for k,v in masses.items() if k in MW)
    return kmol*8.314462618*273.15/101.325*hours

gas_note='Dry ideal-gas Nm3 at 273.15 K and 101325 Pa; species mass divided by stated molecular weight.'
base_name='F2 PR3 AD1 BG2 NR4 A; July steady state annualized 8760 h'

# 01 baseline: all axes are dimensionally homogeneous.
feed=comp('roadside_grass')
groups={'Water':['Water'],'Structural fibres':['Cellulose','Hemicellulose','Lignin'],
        'Protein and peptides':['SolubleProtein','SuspendedProtein','AminoAcids','Peptides'],
        'Other organics':['Lipids','EntrappedSugars','Starch','Pectin','ParticulateBiodegradableOrganics','NonBiodegradableOrganics'],
        'Ash and minerals':['Ash','InertSolids','Sand','Ammonium','DissolvedPhosphorus','OrganicNitrogen','ParticulateNitrogen','ParticulatePhosphorus','ParticulatePotassium','PotassiumIon','SuspendedSolids'],
        'Other trace components':['HeavyMetals','Litter','Microplastics','PathogenIndicators','PersistentOrganics','Pesticides']}
used=set(x for vs in groups.values() for x in vs);assert used==set(feed)
hbar('01_baseline','feedstock_composition','Feed composition',list(groups),[sum(feed[k] for k in vs)/10 for vs in groups.values()],
     '% wet mass','roadside_grass stream components',base_name,'Grouped model inlet composition; structural inputs',BLUE)
hbar('01_baseline','front_end_split','Front end split',['Press cake','Raw liquid fraction','Preparation loss'],
     [stream_mass('pressed_fibre_cake')*H/1000,stream_mass('raw_liquid_fraction')*H/1000,
      (stream_mass('roadside_grass')-stream_mass('prepared_roadside_grass'))*H/1000],
     't/y','streams.json',base_name,'Mass destinations before downstream recovery',GREEN)

# A compact mass-flow Sankey using proportional ribbons and no duplicated downstream streams.
fig,ax=plt.subplots(figsize=(7.35,4.2));ax.set_xlim(0,10);ax.set_ylim(0,10);ax.axis('off')
feed_rate=stream_mass('roadside_grass');cake=stream_mass('pressed_fibre_cake');juice=stream_mass('raw_liquid_fraction');loss=feed_rate-cake-juice
assert abs(cake+juice+loss-feed_rate)<1e-6 and loss>=0
ax.add_patch(Rectangle((.4,2),1.7,6,facecolor=BLUE,edgecolor='none'))
ax.text(1.25,5,'Grass\n1000 kg/h',ha='center',va='center',color='white',fontsize=11)
for y0,y1,height,col,label in [(2,2.3,6*cake/feed_rate,SAND,f'Press cake\n{cake:.1f} kg/h'),
                                (2+6*cake/feed_rate,5.1,6*juice/feed_rate,GREEN,f'Raw liquid\n{juice:.1f} kg/h'),
                                (2+6*(cake+juice)/feed_rate,8.55,6*loss/feed_rate,ROSE,f'Loss\n{loss:.1f} kg/h')]:
    source_height=6*({'Press cake':cake,'Raw liquid':juice,'Loss':loss}[label.split('\n')[0]])/feed_rate
    target_height=max(.12,source_height)
    verts=[(2.1,y0),(3.7,y0),(6.1,y1),(7.3,y1),(7.3,y1+target_height),(6.1,y1+target_height),(3.7,y0+source_height),(2.1,y0+source_height),(2.1,y0)]
    codes=[MPath.MOVETO]+[MPath.CURVE4]*3+[MPath.LINETO]+[MPath.CURVE4]*3+[MPath.CLOSEPOLY]
    ax.add_patch(PathPatch(MPath(verts,codes),facecolor=col,alpha=.78,edgecolor='none'))
    ax.text(7.5,y1+target_height/2,label,va='center',fontsize=10)
ax.set_title('Grass fractionation',loc='left')
save(fig,'01_baseline','grass_fractionation_sankey','Grass fractionation','Front-end mass conservation from modeled streams','streams.json',base_name,'kg/h','Preparation loss is 3.3 kg/h; ribbon width proportional to mass.')

prod=BASE['annual']['products']
hbar('01_baseline','annual_solid_products','Annual product streams',
     ['Dry protein','P product','Ammonium product','Nutrient solids'],
     [prod[k]['value']/1000 for k in ('dry_protein_product','phosphorus_product','ammonium_product','nutrient_rich_solids')],
     't/y of reported stream','baseline_report.json annual.products',base_name,'Reported stream mass; not pure constituent mass',GREEN)
hbar('01_baseline','gas_product_volumes','Gas product volumes',['Raw dry biogas','Upgraded dry biomethane'],
     [normalized_dry_volume('raw_biogas'),normalized_dry_volume('water_scrubber_biomethane')],
     'Nm³/y','streams.json gas components',base_name,'Gas volume converted from component masses',BLUE,gas_note)

times=[x['time'][5:] for x in SEASON['throughput_series']]
through=[x['actual_throughput_kg']/1000 for x in SEASON['throughput_series']]
vbar('01_baseline','seasonal_throughput','Seasonal throughput',times,through,'t/month',
     'checkpoint3c_may_nov_final/throughput_series.json','2026 May–Nov quasi-dynamic F2 PR3 AD1 BG2 NR4 A',
     'Separate saved seasonal operational example; not comparable as annual total to baseline',BLUE)
vbar('01_baseline','seasonal_capacity_use','Seasonal capacity use',times,
     [100*x['actual_throughput_kg']/x['maximum_throughput_kg'] for x in SEASON['throughput_series']],
     '% modeled capacity','checkpoint3c_may_nov_final/throughput_series.json',
     '2026 May–Nov quasi-dynamic F2 PR3 AD1 BG2 NR4 A',
     'Actual monthly feed divided by modeled maximum throughput',GREEN)

# 02 technical: unit utilities, energy and production profiles.
electric=[(u['display_name']+' ('+u['unit_id']+')',u['power']['value']*H/1000) for u in UNITS if u.get('power') and u['power'].get('value') and u['power']['value']>0]
electric_top=sorted(electric,key=lambda x:x[1],reverse=True)[:12]
hbar('02_technical','electricity_by_unit','Electricity by unit',[x[0] for x in electric],[x[1] for x in electric],
     'MWh/y','units.json power',base_name,'Every unit with positive modeled power',BLUE,sort=True)
hbar('02_technical','electricity_top_units','Largest electricity users',[x[0] for x in electric_top],
     [x[1] for x in electric_top],'MWh/y','units.json power',base_name,
     'Twelve largest modeled electrical users; complete chart also supplied',BLUE)
heat=[];cool=[]
for u in UNITS:
    for duty in u.get('heat_duties',[]):
        assert duty['unit']=='kJ/hr'
        value=duty['value']*H/3.6e6
        if value>0:heat.append((u['display_name']+' ('+u['unit_id']+')',value))
        elif value<0:cool.append((u['display_name']+' ('+u['unit_id']+')',abs(value)))
hbar('02_technical','heating_by_unit','Heating by unit',[x[0] for x in heat],[x[1] for x in heat],
     'MWh/y','units.json heat_duties',base_name,'Positive heating duty by unit',ROSE,sort=True)
hbar('02_technical','cooling_by_unit','Cooling by unit',[x[0] for x in cool],[x[1] for x in cool],
     'MWh/y','units.json heat_duties',base_name,'Magnitude of negative heat duty by unit',BLUE,sort=True)

stages=BASE['annual']['process_pathway'];stage_labs=[s['label'].replace(' / CHP','') for s in stages if s['stage_id']!='feed']
stage_e=[sum((u['power']['value'] or 0)*H/1000 for u in UNITS if u['process_area']==key and u.get('power')) for key in STAGE]
stage_keys=list(STAGE);stage_labels=['Preparation','Protein','Digestion','Gas upgrading','Nutrient recovery']
assert len(stage_keys)==5
hbar('02_technical','electricity_by_stage','Electricity by stage',stage_labels,stage_e,
     'MWh/y','units.json power and process_area',base_name,'Stage-level purchased electricity demand',BLUE)
stage_h=[]
for key in stage_keys:
    stage_h.append(sum(max(d['value'],0)*H/3.6e6 for u in UNITS if u['process_area']==key for d in u.get('heat_duties',[])))
hbar('02_technical','heating_by_stage','Heating by stage',stage_labels,stage_h,
     'MWh/y','units.json heat_duties and process_area',base_name,'Stage-level positive heat duty',ROSE)

feed_t=BASE['annual']['feed_processed']['value']/1000
hbar('02_technical','specific_product_yields','Specific product yields',['Dry protein','P product','Ammonium product','Nutrient solids'],
     [prod[k]['value']/feed_t for k in ('dry_protein_product','phosphorus_product','ammonium_product','nutrient_rich_solids')],
     'kg stream/t fresh grass','baseline_report.json annual.products',base_name,'Stream mass per tonne feed',GREEN)
season_prod=SEASON['product_series']
vbar('02_technical','seasonal_protein','Seasonal protein',times,[x['products_kg']['dry_protein_product']/1000 for x in season_prod],
     't/month','checkpoint3c_may_nov_final/product_series.json','2026 May–Nov quasi-dynamic route','Seasonal dry-protein product',GREEN)
vbar('02_technical','seasonal_ammonium','Seasonal ammonium',times,[x['products_kg']['ammonium_product']/1000 for x in season_prod],
     't/month of reported stream','checkpoint3c_may_nov_final/product_series.json','2026 May–Nov quasi-dynamic route','Seasonal ammonium product stream',BLUE)

# 03 TEA: supported partial accounts only.
cap=[x for x in BASE['tea']['capex_lines'] if x.get('direct_cost_eur') is not None]
hbar('03_tea','partial_direct_capex','Partial direct CAPEX',[x['equipment_or_cost_item'][:34] for x in cap],
     [x['direct_cost_eur'] for x in cap],'€ direct purchase','baseline_report.json tea.capex_lines',base_name,
     'Calculated direct equipment entries only; installed plant CAPEX unresolved',YELLOW)
opex=[x for x in BASE['tea']['opex_lines'] if x.get('annual_cost_eur') is not None]
hbar('03_tea','partial_opex','Partial annual OPEX',[x['equipment_or_cost_item'][:35] for x in opex],
     [x['annual_cost_eur'] for x in opex],'€/y booked cost','baseline_report.json tea.opex_lines',base_name,
     'Calculated OPEX entries only; full plant OPEX unresolved',ROSE)
miss=Counter(x['code'] for x in BASE['tea']['missing_inputs'])
hbar('03_tea','tea_missing_inputs','TEA input gaps',[x.replace('_',' ') for x in miss],list(miss.values()),'missing input records',
     'baseline_report.json tea.missing_inputs',base_name,'Incomplete inputs blocking full investment KPIs',YELLOW,sort=True)
cap_status=Counter(x.get('calculation_status','unspecified') for x in BASE['tea']['capex_lines'])
hbar('03_tea','capex_line_status','CAPEX line status',[x.replace('_',' ') for x in cap_status],list(cap_status.values()),'selected equipment lines',
     'baseline_report.json tea.capex_lines',base_name,'Status of selected CAPEX records',YELLOW,sort=True)

# 04 LCA: activity and missing-factor evidence, never CO2e totals.
hbar('04_lca','energy_inventory','Energy inventory',['Electricity','Delivered heat'],
     [BASE['annual']['utilities']['electricity']['value']/1000,BASE['annual']['utilities']['heating']['value']/1000],
     'MWh/y','baseline_report.json annual.utilities',base_name,'Activities awaiting characterized utility factors',BLUE)
lca_missing=Counter(str(x).split(':')[0] for x in BASE['lca']['missing_inputs'])
hbar('04_lca','lca_inventory_gaps','LCA inventory gaps',[x.replace('process_uncaptured_biogas_Methane','Uncaptured methane').replace('process_reject_gas_Methane','Reject methane').replace('_',' ') for x in lca_missing],list(lca_missing.values()),'missing input records',
     'baseline_report.json lca.missing_inputs',base_name,'Climate inventory and factor blockers',ROSE,sort=True)

# 05 hotspots: transparent utilities and reagent inputs.
electric_sorted=sorted(electric,key=lambda x:x[1],reverse=True)
cum=np.cumsum([x[1] for x in electric_sorted])/sum(x[1] for x in electric_sorted)*100
fig,ax=plt.subplots(figsize=(7.35,5.3));xx=np.arange(len(electric_sorted));ax.bar(xx,[x[1] for x in electric_sorted],color=BLUE)
ax.set_xticks(xx,[x[0].split(' (')[1].rstrip(')') for x in electric_sorted],rotation=70,ha='right',fontsize=8)
ax.set_ylabel('MWh/y');ax.set_title('Electricity concentration',loc='left');ax_style(ax,'y')
ax2=ax.twinx();ax2.plot(xx,cum,color=GREEN,lw=2);ax2.set_ylabel('Cumulative share (%)');ax2.set_ylim(0,105)
save(fig,'05_hotspots','electricity_pareto','Electricity concentration','Unit electricity Pareto chart','units.json power',base_name,'MWh/y and cumulative %')

reagents=defaultdict(float)
for stream in STREAMS.values():
    if stream['source_unit'] is None and stream['stream_id']!='roadside_grass':
        for comp_name,value in stream['components'].items():
            if comp_name in {'HydrochloricAcid','SulfuricAcid','SodiumHydroxide','ActivatedCarbon'}:
                reagents[comp_name]+=value['value']*H
hbar('05_hotspots','reagent_inputs','Reagent inputs',list(reagents),list(reagents.values()),'kg/y of chemical component',
     'streams.json external input components',base_name,'Annualized external reagent component mass; no cost assigned',ROSE,sort=True)

nutrient=[ROUTES[k] for k in ('no_targeted_nutrients','struvite_only','ammonium_only','baseline_F2_PR3_AD1_BG2_NR4_A')]
nlabs=['NR0 bypass','NR2 P','NR3 N','NR4 P+N']
base_e=number(nutrient[0],'electricity_kwh_year');base_h=number(nutrient[0],'heating_kwh_year')
hbar('05_hotspots','incremental_electricity','Added electricity',nlabs[1:],
     [(number(r,'electricity_kwh_year')-base_e)/1000 for r in nutrient[1:]],'MWh/y versus NR0',
     'route_comparison.csv',base_name,'Incremental electrical duty of nutrient routes',BLUE)
hbar('05_hotspots','incremental_heating','Added heating',nlabs[1:],
     [(number(r,'heating_kwh_year')-base_h)/1000 for r in nutrient[1:]],'MWh/y versus NR0',
     'route_comparison.csv',base_name,'Incremental positive heat duty of nutrient routes',ROSE)

fig,ax=plt.subplots(figsize=(7.35,4.7))
x=np.arange(len(nutrient));w=.35
ax.bar(x-w/2,[number(r,'electricity_kwh_year')/1000 for r in nutrient],w,color=BLUE,label='Electricity')
ax.bar(x+w/2,[number(r,'heating_kwh_year')/1000 for r in nutrient],w,color=ROSE,label='Heating')
ax.set_xticks(x,nlabs);ax.set_ylabel('MWh/y');ax.set_title('Nutrient route energy',loc='left');ax.legend(frameon=False)
ax_style(ax,'y');save(fig,'05_hotspots','nutrient_route_energy','Nutrient route energy','Matched-route utility trade-off',
                       'route_comparison.csv',base_name,'MWh/y')

# 06 scenario comparisons: all saved cases retain 1 t/h and 8760 h; only one route dimension changes per extra case.
all_rows=list(ROUTES.values())
assert all(abs(number(r,'feed_kg_year')-8760000)<.01 for r in all_rows)
select=['no_targeted_nutrients','struvite_only','ammonium_only','baseline_F2_PR3_AD1_BG2_NR4_A',
        'calcium_phosphate_NR5','ion_exchange_NR6','potassium_NR7']
rows=[ROUTES[k] for k in select];labs=['NR0','NR2','NR3','NR4','NR5','NR6','NR7']
vbar('06_scenario_comparison','nutrient_route_electricity','Nutrient electricity',labs,
     [number(r,'electricity_kwh_year')/1000 for r in rows],'MWh/y','route_comparison.csv + extra_cases.csv',
     'Matched structural nutrient routes','Electricity across nutrient technology routes',BLUE)
vbar('06_scenario_comparison','nutrient_route_heating','Nutrient heating',labs,
     [number(r,'heating_kwh_year')/1000 for r in rows],'MWh/y','route_comparison.csv + extra_cases.csv',
     'Matched structural nutrient routes','Heating across nutrient technology routes',ROSE)
same_product_rows=[ROUTES[k] for k in ('no_targeted_nutrients','struvite_only','ammonium_only','baseline_F2_PR3_AD1_BG2_NR4_A','potassium_NR7')]
same_product_labels=['NR0','NR2','NR3','NR4','NR7']
vbar('06_scenario_comparison','phosphorus_product_routes','Struvite route streams',same_product_labels,
     [number(r,'phosphorus_product_kg_year')/1000 for r in same_product_rows],'t/y product stream',
     'route_comparison.csv + extra_cases.csv','Matched routes with same P product identity',
     'P product stream, not elemental P; NR5 calcium phosphate excluded',YELLOW)
vbar('06_scenario_comparison','ammonium_product_routes','Ammonium route streams',same_product_labels,
     [number(r,'ammonium_product_kg_year')/1000 for r in same_product_rows],'t/y product stream',
     'route_comparison.csv + extra_cases.csv','Matched routes with same ammonium product identity',
     'Ammonium product stream, not elemental N; NR6 zeolite product excluded',BLUE)

base=ROUTES['baseline_F2_PR3_AD1_BG2_NR4_A'];nopef=ROUTES['no_pef_F1']
hbar('06_scenario_comparison','pef_protein_effect','PEF protein contrast',['F1 no PEF','F2 PEF'],
     [number(nopef,'dry_protein_product_kg_year')/1000,number(base,'dry_protein_product_kg_year')/1000],
     't/y dry protein stream','extra_cases.csv + route_comparison.csv','F1 versus F2; other route IDs matched',
     'Structural PEF difference, not measured yield response',GREEN)
hbar('06_scenario_comparison','pef_electricity_effect','PEF electricity',['F1 no PEF','F2 PEF'],
     [number(nopef,'electricity_kwh_year')/1000,number(base,'electricity_kwh_year')/1000],
     'MWh/y','extra_cases.csv + route_comparison.csv','F1 versus F2; other route IDs matched',
     'Added power of F2 structural route',BLUE)
orderb=ROUTES['nutrient_order_B']
hbar('06_scenario_comparison','process_order_difference','Process order difference',
     ['P product stream','Ammonium product stream'],
     [number(orderb,'phosphorus_product_kg_year')-number(base,'phosphorus_product_kg_year'),
      number(orderb,'ammonium_product_kg_year')-number(base,'ammonium_product_kg_year')],
     'kg/y, order B minus A','extra_cases.csv + route_comparison.csv','NR4 order A versus B',
     'Small sequencing effects shown as direct differences',YELLOW)

def gas_vol_from_report(name):
    report=json.loads((OUT/(name+'.json')).read_text(encoding='utf-8'))
    run=OUT/'source_runs'/report['run_id']
    streams={x['stream_id']:x for x in json.loads((run/'streams.json').read_text(encoding='utf-8'))}
    product=next((x for x in streams.values() if 'biomethane' in x.get('aliases',[])),None)
    if product is None:return None
    MW={'Methane':16.043,'CarbonDioxide':44.0095,'Ammonia':17.031,'HydrogenSulfide':34.081,'Nitrogen':28.0134,'Oxygen':31.998}
    return sum(v['value']/MW[k] for k,v in product['components'].items() if k in MW)*8.314462618*273.15/101.325*H
gas_labels=['Water scrubber','Membrane','PSA'];gas_values=[normalized_dry_volume('water_scrubber_biomethane'),gas_vol_from_report('membrane_BG3'),gas_vol_from_report('psa_BG4')]
hbar('06_scenario_comparison','upgrader_gas_volume','Upgraded gas volume',gas_labels,gas_values,
     'dry Nm³/y','baseline streams.json + extra run streams.json','BG2 versus BG3 versus BG4; other routes matched',
     'Dry product gas at normal conditions; purity varies',GREEN,gas_note)

# Route KPI heatmap: comparable units are scaled per column, values are printed, no currency/climate included.
metrics=[('Electricity\nMWh/y','electricity_kwh_year',1/1000,'MWh/y'),('Heating\nMWh/y','heating_kwh_year',1/1000,'MWh/y'),
         ('P stream\nt/y','phosphorus_product_kg_year',1/1000,'t/y'),('Ammonium\nt/y','ammonium_product_kg_year',1/1000,'t/y')]
heatmap_rows=rows[:4];heatmap_labels=labs[:4]
matrix=np.array([[number(r,k)*scale for _,k,scale,_ in metrics] for r in heatmap_rows],dtype=float)
scaled=np.column_stack([(matrix[:,j]-matrix[:,j].min())/(np.ptp(matrix[:,j]) or 1) for j in range(matrix.shape[1])])
fig,ax=plt.subplots(figsize=(7.35,5.1));im=ax.imshow(scaled,cmap='YlGnBu',aspect='auto',vmin=0,vmax=1)
ax.set_xticks(range(len(metrics)),[m[0] for m in metrics]);ax.set_yticks(range(len(heatmap_labels)),heatmap_labels)
for i in range(len(heatmap_labels)):
    for j in range(len(metrics)):
        ax.text(j,i,f'{matrix[i,j]:,.1f}',ha='center',va='center',fontsize=9,color=INK if scaled[i,j]<.65 else 'white')
ax.set_title('Nutrient route KPIs',loc='left');fig.colorbar(im,ax=ax,label='Within-column relative scale',shrink=.75)
save(fig,'06_scenario_comparison','nutrient_route_kpi_heatmap','Nutrient route KPIs',
     'Comparable structural route KPIs; color scaled separately within each column',
     'route_comparison.csv','F2 PR3 AD1 BG2, NR0/NR2/NR3/NR4, 1 t/h, 8760 h','MWh/y and t/y shown in cells',
     'Within-column colors do not imply an aggregate score.')

# 08 candidate comparison: labelled structural candidates, not optimized designs.
chosen=['no_targeted_nutrients','struvite_only','ammonium_only','baseline_F2_PR3_AD1_BG2_NR4_A']
clabel=['NR0 bypass','NR2 P','NR3 N','NR4 P+N']
for key,title,unit,color in [('electricity_kwh_year','Candidate electricity','MWh/y',BLUE),
                             ('heating_kwh_year','Candidate heating','MWh/y',ROSE)]:
    scale=1/1000
    hbar('08_candidate_comparison',key.replace('_kg_year','').replace('_kwh_year','')+'_cases',title,clabel,
         [number(ROUTES[k],key)*scale for k in chosen],unit,'route_comparison.csv','Matched structural cases; not optimized',
         'Technical comparison only; no complete financial/climate ranking',color)

# 09 uncertainty and model quality: deterministic evidence, no synthetic probability intervals.
status=Counter(x.get('status','unspecified') for x in BASE['process_parameter_evidence'])
hbar('09_uncertainty','parameter_evidence_status','Parameter status',list(status),list(status.values()),
     'resolved parameter records','baseline_report.json process_parameter_evidence',base_name,
     'Reported status, not an experimental/literature/proxy census',YELLOW)
warning_group=Counter()
for w in BASE['warnings']:
    category='Structural assumptions' if 'class E' in w or 'structural' in w.lower() else 'Equipment and cost' if 'cost' in w or 'dryer' in w else 'Process assumptions'
    warning_group[category]+=1
hbar('09_uncertainty','warnings_by_category','Warning categories',list(warning_group),list(warning_group.values()),
     'warning messages','baseline_report.json warnings',base_name,'Analyst grouping; model does not assign severity',ROSE)
hbar('09_uncertainty','route_mass_residuals','Route mass residuals',
     [r['case_id'].replace('_',' ')[:28] for r in all_rows],
     [abs(number(r,'mass_residual_kg_year')) for r in all_rows],
     'absolute kg/y','route_comparison.csv + extra_cases.csv','Matched structural cases',
     'Overall numerical mass residual across runs',GREEN,sort=True)
factor_status=Counter(x['source_status'] for x in BASE['lca']['factors'])
hbar('09_uncertainty','climate_factor_status','Climate factor status',list(factor_status),list(factor_status.values()),
     'factor records','baseline_report.json lca.factors',base_name,
     'Factor evidence status; inventory completeness remains unresolved',YELLOW)

for supplemental in ('proxy_figure_index.csv','biosteam_figure_index.csv'):
    index_path=OUT/supplemental
    if index_path.exists():
        with index_path.open(encoding='utf-8-sig',newline='') as f:
            INDEX.extend(csv.DictReader(f))
with (OUT/'figure_index.csv').open('w',newline='',encoding='utf-8-sig') as f:
    writer=csv.DictWriter(f,fieldnames=list(INDEX[0]));writer.writeheader();writer.writerows(INDEX)
(OUT/'generation_manifest.json').write_text(json.dumps({'figure_count':len(INDEX),'baseline_run_id':BASE['run_id'],
    'baseline_git_commit':BASE['provenance']['process'].get('git_commit'),
    'extra_case_ids':list(ROUTES),'gas_normalization':gas_note,
    'omitted_objectives':['complete installed CAPEX','complete OPEX','revenue','NPV','IRR','complete GHG','Pareto optimum','MCDA'],
    'source_files':['scientific_report/baseline_report.json','scientific_report/route_comparison.csv',
                    'results/report_figures/extra_cases.csv','Greenhub/results/checkpoint3c_may_nov_final']},indent=2),encoding='utf-8')
print(f'Indexed {len(INDEX)} PNG figures')
