"""Generate linked F1 baseline and selected candidate panels.

Run finalize_no_pef_library.py after visual QA to remove superseded plots and
rebuild the curated index. The optional --replace mode supports older layouts.
"""
from __future__ import annotations
import argparse
import csv
import json
import math
import time
from collections import Counter,defaultdict
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch,FancyBboxPatch,PathPatch
from matplotlib.path import Path as MPath
import numpy as np

ROOT=Path(__file__).resolve().parents[2]
OUT=Path(__file__).resolve().parent
DATA=OUT/'biosteam_frontiers'
MAN=json.loads((DATA/'selection_manifest.json').read_text(encoding='utf-8'))
MATCH=json.loads((DATA/'matched_protein_bypass_manifest.json').read_text(encoding='utf-8'))['pairs']
BG='#efebe6';PANEL='#f8f5f1';INK='#0c3338';MUTED='#587174'
GREEN='#408f4d';BLUE='#729ad2';YELLOW='#d1a520';ROSE='#d277a3';SAND='#e4b839'
COLORS=[GREEN,BLUE,YELLOW,ROSE,SAND]
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':9.5,'axes.titlesize':11,'axes.labelsize':9.5,
                     'axes.edgecolor':INK,'axes.labelcolor':INK,'text.color':INK,'xtick.color':INK,
                     'ytick.color':INK,'figure.facecolor':BG,'axes.facecolor':BG,
                     'savefig.facecolor':BG,'savefig.dpi':300})
INDEX=[]
STAGES={'pretreatment':'Preparation','protein':'Protein','ad':'Digestion','gas':'Gas upgrading','nutrients':'Nutrients'}
PRODUCTS={'dry_protein_product':'Protein','ammonium_product':'Ammonium','phosphorus_product':'Phosphorus',
          'potassium_concentrate':'Potassium','nutrient_rich_solids':'Nutrient solids'}
SOURCE='Saved BioSTEAM decision reports and Greenhub/results/runs/{run_id}/streams.json; candidate economic overlay'
NOTE=('BioSTEAM process outputs; screening process assumptions. TEA includes partial recorded capital/OPEX, '
      'benchmark product prices, subsidy, tax and candidate savings/uplifts. Climate objective is electricity-only '
      'attributional burden, excludes heat and substitution credits. Technical ranking gate remains false because '
      'storage evidence is unresolved. Financial projections repeat nominal annual accounts for 20 years and are '
      'not complete forecasts or balance sheets.')
H=8760
MW={'Methane':16.043,'CarbonDioxide':44.0095,'Ammonia':17.031,'HydrogenSulfide':34.081,
    'Nitrogen':28.0134,'Oxygen':31.998,'Hydrogen':2.01588}

def load(group,rank):
    return json.loads((DATA/group/f'rank_{rank:02d}.json').read_text(encoding='utf-8'))

def streams(r):
    path=ROOT/'Greenhub/results/runs'/r['run_id']/'streams.json'
    if not path.exists():path=OUT/'source_runs'/r['run_id']/'streams.json'
    return {x['stream_id']:x for x in json.loads(path.read_text(encoding='utf-8'))}

def mass(s,key):return s.get(key,{}).get('total_mass',{}).get('value',0) or 0

def gas_nm3(s,key):
    stream=s.get(key)
    if stream is None:return 0
    comp=stream['components'];unknown={k for k,v in comp.items() if v['value']>0 and k not in MW and k!='Water'}
    assert not unknown,(key,unknown)
    kmol=sum(v['value']/MW[k] for k,v in comp.items() if k in MW)
    return kmol*8.314462618*273.15/101.325*H

def route_label(r):
    p=r['annual']['products'];gas=(p.get('biomethane') or {}).get('value',0)
    present=[(p.get(k) or {}).get('value',0)>1e-8 for k in
             ('dry_protein_product','ammonium_product','phosphorus_product','potassium_concentrate')]
    return '  ·  '.join(f'{label} {"✓" if ok else "X"}' for label,ok in zip(
        ('Protein','Biogas','N','P','K'),(present[0],gas>1e-8,*present[1:])))

def product_name(r,product_id):
    if product_id=='biomethane':
        return 'Raw gas export' if r['configuration']['simulation']['scenarios']['biogas_upgrading']=='BG0' else 'Biomethane'
    return PRODUCTS.get(product_id,product_id or 'Other')

def newfig(title,r,rows=2,cols=2,height=6):
    fig,axes=plt.subplots(rows,cols,figsize=(7.55,height))
    fig.suptitle(title,x=.05,y=.99,ha='left',fontsize=14,color=INK)
    fig.text(.98,.985,route_label(r),ha='right',va='top',fontsize=8,color=MUTED)
    return fig,np.asarray(axes).reshape(-1)

def style(ax,grid='x'):
    ax.spines[['top','right']].set_visible(False)
    ax.grid(axis=grid,alpha=.13,lw=.65);ax.set_axisbelow(True)

def bar(ax,title,labels,values,unit,color=GREEN):
    pairs=[(label,value) for label,value in zip(labels,values) if value is not None and abs(value)>1e-10]
    if not pairs:
        ax.set_title(title,loc='left',pad=6);ax.text(.5,.5,'No modeled output',ha='center',va='center',transform=ax.transAxes,color=MUTED)
        ax.set_xticks([]);ax.set_yticks([]);ax.spines[:].set_visible(False);return
    labels,values=zip(*pairs);y=np.arange(len(labels));ax.barh(y,values,color=color,height=.65)
    ax.set_yticks(y,labels);ax.invert_yaxis();ax.set_xlabel(unit,fontsize=8.5)
    ax.set_title(title,loc='left',pad=6);style(ax)
    if min(values)<0<max(values):ax.axvline(0,color=INK,lw=.7)

def save(fig,folder,name,description,units,scenario,notes=''):
    path=OUT/folder/f'{name}.png';path.parent.mkdir(parents=True,exist_ok=True)
    fig.tight_layout(rect=(0,.02,1,.93),pad=1.15,w_pad=1.15,h_pad=1.35)
    temporary=path.with_name(path.stem+'_rendering.png')
    try:
        for attempt in range(6):
            try:
                fig.savefig(temporary,dpi=300,bbox_inches='tight',pad_inches=.12)
                temporary.replace(path)
                break
            except OSError:
                if attempt==5:raise
                time.sleep(.25*(attempt+1))
    finally:
        plt.close(fig)
        if temporary.exists():temporary.unlink()
    figure_id=path.relative_to(OUT).with_suffix('').as_posix().replace('/','__')
    INDEX.append({'figure':figure_id,'description':description,'source_dataset':SOURCE,
                  'scenario':scenario,'units':units,'file_location':str(path),'notes':NOTE+' '+notes})

def account(r):
    t=r['tea']['totals'];a=r['tea']['candidate_economics']['assumptions']
    cap=t['subsidy_adjusted_capex_eur'];rev=t['optimized_annual_revenue_eur'];op=t['optimized_annual_opex_eur'];tax=t['tax_eur_per_year']
    cash=rev-op-tax;disc=a['discount_rate'];years=a['project_lifetime_years']
    npv=-cap+sum(cash/(1+disc)**i for i in range(1,years+1))
    assert years==20 and math.isclose(t['optimized_after_tax_profit_eur_per_year'],cash-cap*disc/(1-(1+disc)**-years),rel_tol=1e-8)
    return cap,rev,op,tax,cash,npv

def stage(r,key):
    return {STAGES[x['stage_id']]:max(0,x.get(key) or 0)*H/1000
            for x in r['annual']['process_pathway'] if x['stage_id'] in STAGES}

def ribbon(ax,x0,x1,y0,y1,width,color,alpha=.85):
    # Connect equal-height cross sections. Width is proportional to inlet mass.
    dy=width/2;verts=[(x0,y0-dy),(x0+(x1-x0)*.5,y0-dy),(x0+(x1-x0)*.5,y1-dy),(x1,y1-dy),
                      (x1,y1+dy),(x0+(x1-x0)*.5,y1+dy),(x0+(x1-x0)*.5,y0+dy),(x0,y0+dy),(x0,y0-dy)]
    codes=[MPath.MOVETO,MPath.CURVE4,MPath.CURVE4,MPath.CURVE4,MPath.LINETO,
           MPath.CURVE4,MPath.CURVE4,MPath.CURVE4,MPath.CLOSEPOLY]
    ax.add_patch(PathPatch(MPath(verts,codes),facecolor=color,edgecolor='none',alpha=alpha))

def flow_map(group,rank,r,s,folder,scenario):
    fig,axes=newfig('Grass to products',r,1,3,5.4);a,b,c=axes
    feed=mass(s,'roadside_grass');juice=mass(s,'raw_liquid_fraction');fiber=mass(s,'pressed_fibre_cake');reject=mass(s,'preparation_rejects')
    assert feed>0 and abs(feed-juice-fiber-reject)<max(1e-4,feed*1e-7)
    a.set_xlim(0,1);a.set_ylim(0,1);a.axis('off');a.set_title('Grass split',loc='left',pad=6)
    a.add_patch(plt.Rectangle((.025,.17),.13,.67,color=INK))
    segments=[(juice,.68,GREEN,'Juice'),(fiber,.35,BLUE,'Fibre'),(reject,.08,ROSE,'Reject')]
    base=.84
    for value,y,color,label in segments:
        height=.67*value/feed;ribbon(a,.155,.59,base-height/2,y,height,color);base-=height
        a.text(.63,y,f'{label}\n{value/feed:.3f} kg',ha='left',va='center',fontsize=8.5)
    a.text(.025,.93,'Grass  1.000 kg',fontsize=8.5,ha='left')
    b.set_xlim(0,1);b.set_ylim(0,1);b.axis('off');b.set_title('Juice pathway',loc='left',pad=6)
    stages=[('Juice',juice,GREEN),('Protein depleted',mass(s,'protein_depleted_liquid'),GREEN),
            ('Digester feed',mass(s,'conditioned_digester_feed'),YELLOW),
            ('Digestate',mass(s,'digestate'),SAND)]
    stages=[row for row in stages if row[1]>1e-10]
    positions=np.linspace(.83,.29,len(stages))
    for i,((label,value,color),y) in enumerate(zip(stages,positions)):
        box=FancyBboxPatch((.07,y-.047),.83,.094,boxstyle='round,pad=.012',facecolor=color,edgecolor='none',alpha=.86)
        b.add_patch(box);b.text(.485,y,f'{label}  {value/feed:.3f} kg',ha='center',va='center',fontsize=7.7,
                            color='white' if color==GREEN else INK)
        if i<len(stages)-1:b.add_patch(FancyArrowPatch((.485,y-.055),(.485,positions[i+1]+.06),arrowstyle='-|>',mutation_scale=11,lw=1.1,color=MUTED))
    b.text(.07,.12,'Selected intermediate streams',fontsize=7.8,color=MUTED)
    c.set_xlim(0,1);c.set_ylim(0,1);c.axis('off');c.set_title('Recovered outputs',loc='left',pad=6)
    product_rows=[('Protein','dry_protein_product',GREEN),('N product','ammonium_product',BLUE),
                  ('P product','phosphorus_product',YELLOW),('K product','potassium_concentrate',ROSE),
                  ('Nutrient solids','nutrient_rich_solids',SAND)]
    solid=[(name,(r['annual']['products'].get(key) or {}).get('value',0)/H/feed,color)
           for name,key,color in product_rows]
    solid=[row for row in solid if row[1]>1e-10]
    for (name,value,color),y in zip(solid,np.linspace(.82,.36,max(len(solid),2))):
        c.add_patch(FancyBboxPatch((.04,y-.037),.08,.074,boxstyle='round,pad=.004',facecolor=color,edgecolor='none'))
        c.text(.16,y,f'{name}  {value:.4f} kg',va='center',fontsize=7.9)
    product_ids={p['product_id']:p['stream_id'] for p in r['products']}
    raw=gas_nm3(s,'raw_biogas')/H/feed;up=gas_nm3(s,product_ids.get('biomethane',''))/H/feed
    if raw>0:c.text(.04,.21,f'Raw gas  {raw:.4f} Nm³',fontsize=8,color=ROSE)
    gas_label='Raw export' if r['configuration']['simulation']['scenarios']['biogas_upgrading']=='BG0' else 'Upgraded'
    if up>0:c.text(.04,.13,f'{gas_label}  {up:.4f} Nm³',fontsize=8,color=ROSE)
    c.text(.04,.04,'per kg wet grass',fontsize=7.8,color=MUTED)
    save(fig,folder,'01_grass_to_products','Mass-proportional grass split plus modeled downstream stream/product map',
         'kg/kg wet grass; dry Nm³/kg wet grass',scenario,'Front-end split closes exactly at 1 kg wet grass. Downstream columns show selected actual stream/product quantities, not a closed Sankey: process water, reagents, evaporation and side streams are omitted. Dry normal gas volume uses 273.15 K and 101325 Pa.')

def material_dashboard(r,s,folder,scenario):
    fig,ax=newfig('Material and products',r,2,2,6.15)
    feed=mass(s,'roadside_grass');split=[mass(s,k) for k in ('raw_liquid_fraction','pressed_fibre_cake','preparation_rejects')]
    ax[0].barh(['Grass split'],[split[0]],color=GREEN,label='Juice')
    ax[0].barh(['Grass split'],[split[1]],left=[split[0]],color=BLUE,label='Fibre')
    ax[0].barh(['Grass split'],[split[2]],left=[split[0]+split[1]],color=ROSE,label='Rejects')
    ax[0].set_xlabel('kg/h');ax[0].set_title('Feed destinations',loc='left');ax[0].legend(frameon=False,ncol=3,fontsize=7.5);style(ax[0])
    solid={v:(r['annual']['products'].get(k) or {}).get('value',0)/1000 for k,v in PRODUCTS.items()}
    bar(ax[1],'Solid products',list(solid),list(solid.values()),'t/year',GREEN)
    product_ids={p['product_id']:p['stream_id'] for p in r['products']}
    raw=gas_nm3(s,'raw_biogas');up=gas_nm3(s,product_ids.get('biomethane',''))
    gas_label='Raw gas export' if r['configuration']['simulation']['scenarios']['biogas_upgrading']=='BG0' else 'Upgraded gas'
    bar(ax[2],'Gas at normal conditions',['Raw biogas',gas_label],[raw,up],'dry Nm³/year',ROSE)
    feed_t=r['annual']['feed_processed']['value']/1000
    yields={k:(r['annual']['products'].get(p) or {}).get('value',0)/feed_t for k,p in
            [('Protein','dry_protein_product'),('Ammonium product','ammonium_product'),('Nutrient solids','nutrient_rich_solids')]}
    bar(ax[3],'Specific product yields',list(yields),list(yields.values()),'kg/t wet feed',YELLOW)
    save(fig,folder,'02_material_and_products','Front-end split, solid products, dry gas volumes and specific yields',
         'kg/h; t/year; dry Nm³/year; kg/t feed',scenario,
         'Raw and upgraded dry gas volumes independently normalized to 273.15 K and 101325 Pa; they are not saleable atmospheric m³. Product stream masses are not pure N/P/K.')

def energy_dashboard(r,folder,scenario):
    fig,ax=newfig('Energy and climate hotspots',r,2,2,6.35)
    e=stage(r,'power_kw');h=stage(r,'heat_duty_kw')
    bar(ax[0],'Electricity by stage',list(e),list(e.values()),'MWh/year',BLUE)
    bar(ax[1],'Heat by stage',list(h),list(h.values()),'MWh/year',ROSE)
    units=sorted(((u['unit_id'],u['demand']*H/1000) for u in r['state_outputs']['utility_consumption']
                  if u['kind']=='electricity' and u['demand']>0),key=lambda x:x[1],reverse=True)[:7]
    bar(ax[2],'Largest electricity units',[x[0] for x in units],[x[1] for x in units],'MWh/year',BLUE)
    climate={k:v*.2 for k,v in e.items()}
    objective=r['objectives']['climate']['value']
    if objective is not None:assert math.isclose(sum(climate.values())*1000,objective,rel_tol=1e-6)
    bar(ax[3],'Electricity climate load',list(climate),list(climate.values()),'t CO₂-eq/year',YELLOW)
    save(fig,folder,'03_energy_and_climate','Stage and unit utility hotspots and included climate load',
         'MWh/year; t CO₂-eq/year',scenario,'Climate subplot is the partial electricity burden only, 0.20 kg CO2e/kWh; heat and other process burdens are not included.')

def finance_dashboard(r,folder,scenario):
    fig,ax=newfig('Economic accounts',r,2,2,6.15);t=r['tea']['totals'];cap,rev,op,tax,cash,npv=account(r)
    revenues=defaultdict(float)
    for line in r['tea']['revenue_lines']:
        if line.get('annual_revenue_eur') is not None:revenues[product_name(r,line.get('product_id'))]+=line['annual_revenue_eur']/1000
    bar(ax[0],'Product revenue',list(revenues) or ['No priced product'],list(revenues.values()) or [0],
        '€ thousand/year',GREEN)
    bar(ax[1],'Annual budget',['Revenue','Recorded OPEX','Tax','After-tax cash'],
        [rev/1000,op/1000,tax/1000,cash/1000],'€ thousand/year',BLUE)
    bar(ax[2],'Capital and subsidy',['Partial direct CAPEX','One-time subsidy','Net capital basis'],
        [t['partial_direct_capex_eur']/1000,t['subsidy_eur']/1000,cap/1000],'€ thousand',YELLOW)
    bar(ax[3],'Candidate adjustments',['Assumed annual savings','Assumed revenue uplift'],
        [t['optimization_savings_eur_per_year']/1000,t['optimization_revenue_uplift_eur_per_year']/1000],
        '€ thousand/year',ROSE)
    save(fig,folder,'04_economic_accounts','Product revenue, partial annual budget, capital subsidy and candidate overlays',
         '€ thousand; € thousand/year',scenario,'Capital bar is one-time while other panels are annual. CAPEX/OPEX exclude uncalculated items; apparent profit is not a full TEA result.')

def projection_dashboard(r,folder,scenario):
    fig,ax=newfig('20-year financial projection',r,2,2,6.2)
    cap,rev,op,tax,cash,npv=account(r);discount=r['tea']['candidate_economics']['assumptions']['discount_rate']
    years=np.arange(21);nom=np.array([-cap+y*cash for y in years])/1000
    disc=np.array([-cap+sum(cash/(1+discount)**j for j in range(1,y+1)) for y in years])/1000
    ax[0].plot(years,nom,color=GREEN,label='Nominal');ax[0].plot(years,disc,color=BLUE,label='Discounted')
    ax[0].axhline(0,color=INK,lw=.7);ax[0].set_title('Cumulative cash',loc='left');ax[0].set_ylabel('€ thousand');ax[0].legend(frameon=False,fontsize=8);style(ax[0],'y')
    revenues=defaultdict(float)
    for line in r['tea']['revenue_lines']:
        if line.get('annual_revenue_eur') is not None:
            revenues[product_name(r,line.get('product_id'))]+=line['annual_revenue_eur']/1000
    revenues={k:v for k,v in revenues.items() if v>1e-10}
    if revenues:
        ax[1].stackplot(years,*[years*v for v in revenues.values()],labels=list(revenues),colors=COLORS[:len(revenues)],alpha=.87)
        ax[1].legend(frameon=False,fontsize=7.2,loc='upper left')
    else:ax[1].text(.5,.5,'No priced products',transform=ax[1].transAxes,ha='center',va='center',color=MUTED)
    ax[1].set_title('Cumulative product revenue',loc='left');ax[1].set_ylabel('€ thousand');style(ax[1],'y')
    for a in ax[:2]:a.set_xlabel('Projection year')
    bar(ax[2],'Annual operating account',['Revenue','OPEX','Tax','Cash'],[rev/1000,op/1000,tax/1000,cash/1000],
        '€ thousand/year',GREEN)
    bar(ax[3],'Project cash metrics',['Year 0 capital','20-year NPV','Year 20 nominal cash'],
        [-cap/1000,npv/1000,nom[-1]],'€ thousand',BLUE)
    save(fig,folder,'05_cashflow_and_product_revenue','Constant-account cash flow and cumulative product revenue over 20 years',
         '€ thousand; € thousand/year',scenario,
         'Year 0 is subsidy-adjusted partial capital; years 1–20 repeat current after-tax operating cash and product revenues. No financing, working capital, replacements, inflation or terminal value. This is not a balance sheet.')

def quality_dashboard(r,folder,scenario):
    fig,ax=newfig('Balance and evidence',r,2,2,6.05)
    b=r['annual']['balance'];ax[0].set_title('Element closure',loc='left')
    residuals=[abs(b['element_residuals_kg'][k]) for k in ('carbon','nitrogen','phosphorus','potassium')]
    for i,(label,value) in enumerate(zip(('C','N','P','K'),residuals)):
        y=.78-i*.19
        ax[0].text(.05,y,label,transform=ax[0].transAxes,va='center',weight='bold',color=INK)
        ax[0].text(.95,y,f'{value:.2g} kg/year',transform=ax[0].transAxes,
                   va='center',ha='right',color=MUTED)
        ax[0].axhline(y-.085,xmin=.05,xmax=.95,color=INK,alpha=.1,lw=.6)
    ax[0].text(.05,.04,'Numerical residuals',transform=ax[0].transAxes,color=MUTED,fontsize=8)
    ax[0].set_xticks([]);ax[0].set_yticks([]);ax[0].spines[:].set_visible(False)
    evidence=r['maturity_summary'].get('process_parameter_evidence') or {}
    labels=list(evidence)[:8];bar(ax[1],'Parameter evidence',labels,[evidence[k] for k in labels],'records',YELLOW)
    tea=r['tea']['totals'];bar(ax[2],'Account completeness',
        ['CAPEX lines','OPEX lines','Revenue lines'],
        [sum(x.get('direct_cost_eur') is not None for x in r['tea']['capex_lines']),
         sum(x.get('annual_cost_eur') is not None for x in r['tea']['opex_lines']),
         sum(x.get('annual_revenue_eur') is not None for x in r['tea']['revenue_lines'])],
        'calculated lines',ROSE)
    warnings=Counter('Storage' if 'retention rate' in w else 'Other' for w in r['warnings'])
    bar(ax[3],'Model warnings',list(warnings) or ['None'],list(warnings.values()) or [0],
        'warning records',SAND)
    save(fig,folder,'06_balance_and_evidence','Numerical closure, evidence counts, calculated account lines and warnings',
         'kg/year; records',scenario,'Near-zero elemental residuals show arithmetic closure, not experimental validation. Technical ranking gate is false.')

def seasonal_dashboard():
    run=next((ROOT/'Greenhub/results/checkpoint3c_may_nov_final').iterdir())
    read=lambda k:json.loads((run/f'{k}_series.json').read_text(encoding='utf-8'))
    through=read('throughput');products=read('product');utility=read('utility')
    months=[x['time'][5:] for x in through];x=np.arange(len(months))
    fig,ax=plt.subplots(2,2,figsize=(7.55,6.1));a=ax.ravel()
    a[0].bar(x,[v['actual_throughput_kg']/1000 for v in through],color=GREEN)
    a[0].set_title('Processed biomass',loc='left');a[0].set_ylabel('t/month')
    for key,label,color in [('dry_protein_product','Protein',GREEN),('ammonium_product','Ammonium product',BLUE),
                            ('nutrient_rich_solids','Nutrient solids',YELLOW)]:
        a[1].plot(x,[v['products_kg'].get(key,0)/1000 for v in products],marker='o',ms=3,label=label,color=color)
    a[1].set_title('Solid products',loc='left');a[1].set_ylabel('t/month');a[1].legend(frameon=False,fontsize=7.7)
    for key,label,color in [('electricity_kwh','Electricity',BLUE),('heating_kwh','Heat',ROSE)]:
        a[2].plot(x,[v[key]/1000 for v in utility],marker='o',ms=3,label=label,color=color)
    a[2].set_title('Utility demand',loc='left');a[2].set_ylabel('MWh/month');a[2].legend(frameon=False,fontsize=7.7)
    a[3].bar(x,[100*v['actual_throughput_kg']/v['maximum_throughput_kg'] for v in through],color=SAND)
    a[3].set_title('Capacity use',loc='left');a[3].set_ylabel('%')
    for z in a:z.set_xticks(x,months);style(z,'y')
    fig.suptitle('Seasonal process response',x=.05,y=.99,ha='left',fontsize=14)
    save(fig,'02_technical','seasonal_process_dashboard','Saved May–November quasi-dynamic biomass, product and utility trajectories',
         't/month; MWh/month; %','Separate 2026 May–November quasi-dynamic F2 PR3 AD1 BG2 NR4 A run',
         'This is a distinct seasonal case, not a time series for selected steady-state Pareto candidates; no kinetic parameters are inferred.')

def comparison_dashboards():
    full=[load('all',i) for i in range(11)];pr0=[load('protein_bypass',i) for i in range(11)];matched=[load('matched_protein_bypass',i) for i in range(11)]
    ranks=np.arange(11)
    fig,ax=plt.subplots(2,2,figsize=(7.55,6.1));a=ax.ravel()
    for rr,label,color in [(full,'Full front',GREEN),(pr0,'PR0 front',BLUE),(matched,'Matched PR0',ROSE)]:
        a[0].plot(ranks,[r['objectives']['operating_profit']['value']/1000 for r in rr],marker='o',ms=3,color=color,label=label)
        a[1].plot(ranks,[r['objectives']['climate']['value']/1000 for r in rr],marker='o',ms=3,color=color,label=label)
        feed=[r['annual']['feed_processed']['value']/1000 for r in rr]
        a[2].plot(ranks,[r['objectives']['operating_profit']['value']/f for r,f in zip(rr,feed)],marker='o',ms=3,color=color,label=label)
        a[3].plot(ranks,[r['objectives']['climate']['value']/f for r,f in zip(rr,feed)],marker='o',ms=3,color=color,label=label)
    for z,title,unit in zip(a,['Annual profit','Climate burden','Profit intensity','Climate intensity'],
                            ['€ thousand/year','t CO₂-eq/year','€/t feed','kg CO₂-eq/t feed']):
        z.set_title(title,loc='left');z.set_xlabel('Rank');z.set_ylabel(unit);z.set_xticks(ranks[::2]);style(z,'y')
    a[0].legend(frameon=False,fontsize=7.5);fig.suptitle('Frontier comparison',x=.05,y=.99,ha='left',fontsize=14)
    save(fig,'06_scenario_comparison/biosteam_dense','three_series_profit_climate',
         'Profit and partial climate burden across full, independent PR0 and matched PR0 series',
         '€ thousand/year; t CO₂-eq/year; €/t; kg CO₂-eq/t','Full/PR0 fronts and matched protein-bypass reruns',
         'Ranks in the independently optimized fronts are not matched technology or throughput pairs; matched PR0 retains the full-front rank identity.')
    fig,ax=plt.subplots(2,2,figsize=(7.55,6.1));a=ax.ravel()
    deltas=[('Profit',[(b['objectives']['operating_profit']['value']-o['objectives']['operating_profit']['value'])/1000 for o,b in zip(full,matched)],'€ thousand/year',GREEN),
            ('Climate',[(b['objectives']['climate']['value']-o['objectives']['climate']['value'])/1000 for o,b in zip(full,matched)],'t CO₂-eq/year',BLUE),
            ('Revenue',[(account(b)[1]-account(o)[1])/1000 for o,b in zip(full,matched)],'€ thousand/year',ROSE),
            ('Electricity',[(b['annual']['utilities']['electricity']['value']-o['annual']['utilities']['electricity']['value'])/1000 for o,b in zip(full,matched)],'MWh/year',YELLOW)]
    for z,(title,vals,unit,color) in zip(a,deltas):
        z.bar(ranks,vals,color=color);z.axhline(0,color=INK,lw=.7);z.set_title(title+' change',loc='left');z.set_ylabel(unit);z.set_xticks(ranks[::2]);z.set_xlabel('Full-front rank');style(z,'y')
    fig.suptitle('Protein bypass effects',x=.05,y=.99,ha='left',fontsize=14)
    save(fig,'06_scenario_comparison/biosteam_dense','matched_protein_bypass_effects',
         'Paired PR0 minus original effects on profit, climate, revenue and electricity',
         '€ thousand/year; t CO₂-eq/year; MWh/year','11 matched full-front protein-bypass reruns',
         'Only protein recovery code changed per pair; route 10 was already PR0 and has zero change.')
    fig,ax=plt.subplots(2,2,figsize=(7.55,6.1));a=ax.ravel()
    for rr,label,color in [(full,'Full front',GREEN),(pr0,'PR0 front',BLUE)]:
        a[0].plot(ranks,[account(r)[-1]/1e6 for r in rr],marker='o',ms=3,color=color,label=label)
        a[1].plot(ranks,[account(r)[1]/1000 for r in rr],marker='o',ms=3,color=color,label=label)
        a[2].plot(ranks,[account(r)[2]/1000 for r in rr],marker='o',ms=3,color=color,label=label)
        a[3].plot(ranks,[r['tea']['totals']['subsidy_eur']/1000 for r in rr],marker='o',ms=3,color=color,label=label)
    for z,title,unit in zip(a,['Projected NPV','Annual revenue','Recorded OPEX','One-time subsidy'],
                            ['€ million','€ thousand/year','€ thousand/year','€ thousand']):
        z.set_title(title,loc='left');z.set_ylabel(unit);z.set_xlabel('Rank');z.set_xticks(ranks[::2]);style(z,'y')
    a[0].legend(frameon=False,fontsize=8);fig.suptitle('Candidate financial comparison',x=.05,y=.99,ha='left',fontsize=14)
    save(fig,'06_scenario_comparison/biosteam_dense','frontier_financial_accounts',
         'Projected NPV, revenue, recorded OPEX and subsidy across two independent frontiers',
         '€ million; € thousand/year; € thousand','Full and protein-bypass BioSTEAM screening fronts',
         'These are partial financial accounts and nominal 20-year constant-account projections; independent front ranks have different throughput.')

def main(replace=False):
    groups=['all','protein_bypass','matched_protein_bypass']
    baseline=json.loads((OUT/'baseline_no_pef_screening.json').read_text(encoding='utf-8'))
    baseline_streams=streams(baseline);baseline_folder='01_baseline/combined'
    baseline_scenario=f'F1 PR3 AD1 BG2 NR4 A reference; {baseline["run_id"]}; 1000 kg/h; 8760 h/year; zero savings/subsidy, benchmark product prices'
    flow_map('baseline',0,baseline,baseline_streams,baseline_folder,baseline_scenario)
    material_dashboard(baseline,baseline_streams,baseline_folder,baseline_scenario)
    energy_dashboard(baseline,baseline_folder,baseline_scenario)
    finance_dashboard(baseline,baseline_folder,baseline_scenario)
    projection_dashboard(baseline,baseline_folder,baseline_scenario)
    quality_dashboard(baseline,baseline_folder,baseline_scenario)
    for group in groups:
        for rank in range(11):
            r=load(group,rank);s=streams(r);folder=f'08_candidate_comparison/biosteam/{group}/rank_{rank:02d}/combined'
            scenario=f'{group} rank {rank}; {r["run_id"]}; {r["configuration"]["simulation"]["wet_feed_rate_kg_hr"]:.1f} kg/h; 8760 h/year'
            flow_map(group,rank,r,s,folder,scenario)
            material_dashboard(r,s,folder,scenario)
            energy_dashboard(r,folder,scenario)
            finance_dashboard(r,folder,scenario)
            projection_dashboard(r,folder,scenario)
            quality_dashboard(r,folder,scenario)
    comparison_dashboards()
    fields=['figure','description','source_dataset','scenario','units','file_location','notes']
    with (OUT/'dense_figure_index.csv').open('w',newline='',encoding='utf-8-sig') as f:
        w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows(INDEX)
    if replace:
        with (OUT/'figure_index.csv').open(encoding='utf-8-sig',newline='') as f:
            previous=list(csv.DictReader(f))
        kept=[];deleted=[]
        for row in previous:
            path=Path(row['file_location']).resolve()
            is_sparse=(path.parent.name.startswith('rank_') and path.parent.parent.name in (*groups,'matched_bypass') and
                       path.name.startswith('biosteam_') and path.suffix.lower()=='.png')
            is_old_seasonal=path==(OUT/'02_technical/seasonal_process_dashboard.png').resolve()
            if is_sparse:
                assert path.is_relative_to((OUT/'08_candidate_comparison/biosteam').resolve())
                deleted.append(path)
            elif is_old_seasonal:deleted.append(path)
            elif row['figure'] not in {x['figure'] for x in INDEX}:kept.append(row)
        for path in deleted:path.unlink()
        with (OUT/'figure_index.csv').open('w',newline='',encoding='utf-8-sig') as f:
            w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows(kept+INDEX)
        # The baseline generator uses this supplemental index on later reruns.
        group_model=[x for x in kept if x['figure'].startswith('biosteam_')]
        with (OUT/'biosteam_figure_index.csv').open('w',newline='',encoding='utf-8-sig') as f:
            w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows(group_model+INDEX)
        print(f'Replaced {len(deleted)} sparse PNGs with {len(INDEX)} dense PNGs; total index {len(kept)+len(INDEX)}')
    else:print(f'Generated {len(INDEX)} dense PNGs for visual review; sparse originals retained')

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--replace',action='store_true');args=parser.parse_args()
    main(args.replace)
