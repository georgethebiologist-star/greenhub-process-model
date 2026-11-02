"""Publication PNGs for selected saved BioSTEAM Pareto candidates.

The backend process runs are real simulations. Financial and climate objectives
retain their documented partial-screening boundaries. Projections are constant
nominal-account arithmetic, not a complete forecast or balance sheet.
"""
from __future__ import annotations
import csv
import json
import math
from collections import defaultdict
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

OUT=Path(__file__).resolve().parent
DATA=OUT/'biosteam_frontiers'
MANIFEST=json.loads((DATA/'selection_manifest.json').read_text(encoding='utf-8'))
BATCH=json.loads(Path(MANIFEST['source_batch']).read_text(encoding='utf-8'))
BG='#efebe6';INK='#0c3338';MUTED='#587174';GREEN='#408f4d';BLUE='#729ad2';YELLOW='#d1a520';ROSE='#d277a3';SAND='#e4b839'
COLORS=[GREEN,BLUE,YELLOW,ROSE,SAND,'#8caaa1']
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':10.5,'axes.titlesize':14,'axes.labelsize':11,
                     'axes.edgecolor':INK,'axes.labelcolor':INK,'text.color':INK,'xtick.color':INK,
                     'ytick.color':INK,'figure.facecolor':BG,'axes.facecolor':BG,
                     'savefig.facecolor':BG,'savefig.dpi':300})
INDEX=[]
SOURCE='Greenhub/results/actual_pareto_2000/decision_batches; biosteam_frontiers/rank_*.json'
SCOPE=('BioSTEAM process simulation with screening process assumptions and partial attributional climate inventory. '
       'Economic objective adds unverified product-price benchmarks, partial recorded CAPEX/OPEX, '
       'candidate labour/logistics/energy savings, yield uplifts, subsidy and tax overlay. '
       'Not a complete TEA/LCA or investment-grade optimum. The climate objective excludes substitution credits; '
       'the saved selected runs account for electricity only. Feed throughput varies across sampled candidates. '
       'Selected reports have eligible_for_ranking=false because of unresolved storage blockers.')
STAGE={'pretreatment':'Preparation','protein':'Protein','ad':'Digestion','gas':'Gas upgrading','nutrients':'Nutrients'}
PRODUCT={'dry_protein_product':'Protein','ammonium_product':'Ammonium product','phosphorus_product':'Phosphorus product',
         'nutrient_rich_solids':'Nutrient solids','potassium_concentrate':'Potassium concentrate'}

def style(ax,axis='x'):
    ax.spines[['top','right']].set_visible(False);ax.grid(axis=axis,alpha=.14,linewidth=.7);ax.set_axisbelow(True)

def save(fig,folder,name,desc,unit,scenario,notes=''):
    path=OUT/folder/f'{name}.png';path.parent.mkdir(parents=True,exist_ok=True)
    fig.tight_layout(pad=1.5);fig.savefig(path,dpi=300,bbox_inches='tight',pad_inches=.16);plt.close(fig)
    INDEX.append({'figure':name,'description':desc,'source_dataset':SOURCE,'scenario':scenario,
                  'units':unit,'file_location':str(path),'notes':SCOPE+' '+notes})

def hbar(folder,name,title,labels,values,unit,desc,scenario,color=GREEN,notes=''):
    fig,ax=plt.subplots(figsize=(7.35,max(3.2,.43*len(labels)+1.55)))
    y=np.arange(len(labels))
    if not any(abs(v)>1e-14 for v in values):
        ax.text(.5,.5,'Within numerical precision' if 'closure' in title.lower() else 'No modeled output',
                transform=ax.transAxes,ha='center',va='center',color=MUTED,fontsize=13)
        ax.set_xlim(0,1)
    else:ax.barh(y,values,color=color,height=.68)
    ax.set_yticks(y,labels);ax.invert_yaxis();ax.set_xlabel(unit);ax.set_title(title,loc='left',pad=12);style(ax)
    if min(values,default=0)<0<max(values,default=0):ax.axvline(0,color=INK,lw=.85)
    save(fig,folder,name,desc,unit,scenario,notes)

def grouped(folder,name,title,labels,series,unit,desc,scenario,notes=''):
    fig,ax=plt.subplots(figsize=(7.35,max(3.5,.43*len(labels)+1.5)))
    y=np.arange(len(labels));width=.72/len(series)
    for i,(label,values,color) in enumerate(series):ax.barh(y+(i-(len(series)-1)/2)*width,values,height=width,color=color,label=label)
    ax.set_yticks(y,labels);ax.invert_yaxis();ax.set_xlabel(unit);ax.set_title(title,loc='left',pad=12)
    ax.legend(frameon=False,fontsize=8.8);style(ax)
    save(fig,folder,name,desc,unit,scenario,notes)

def heatmap(folder,name,title,rows,columns,matrix,formats,desc,scenario,notes='',unit_override=None):
    a=np.asarray(matrix,dtype=float);span=np.ptp(a,axis=0);span[span==0]=1;z=(a-a.min(axis=0))/span
    fig,ax=plt.subplots(figsize=(8.4,max(4,.43*len(rows)+1.6)));ax.imshow(z,cmap='YlGn',aspect='auto',vmin=0,vmax=1)
    ax.set_xticks(range(len(columns)),columns,rotation=24,ha='right');ax.set_yticks(range(len(rows)),rows)
    for i in range(len(rows)):
        for j in range(len(columns)):
            col=plt.cm.YlGn(z[i,j]);lum=.2126*col[0]+.7152*col[1]+.0722*col[2]
            ax.text(j,i,formats[j].format(a[i,j]),ha='center',va='center',fontsize=8.5,color=INK if lum>.52 else 'white')
    ax.tick_params(length=0);ax.set_title(title,loc='left',pad=12)
    save(fig,folder,name,desc,unit_override or '; '.join(columns),scenario,notes+' Cell colors normalize within each column.')

def money(r):
    t=r['tea']['totals'];e=r['tea']['candidate_economics']['assumptions']
    cap=t['subsidy_adjusted_capex_eur'];revenue=t['optimized_annual_revenue_eur'];opex=t['optimized_annual_opex_eur'];tax=t['tax_eur_per_year']
    cash=revenue-opex-tax
    annuity=e['project_lifetime_years'];discount=e['discount_rate']
    charge=cap*(discount/(1-(1+discount)**-annuity) if discount else 1/annuity)
    assert math.isclose(cash-charge,t['optimized_after_tax_profit_eur_per_year'],rel_tol=1e-9,abs_tol=1e-5)
    npv=-cap+sum(cash/(1+discount)**yr for yr in range(1,annuity+1))
    assert math.isclose(npv,t['optimized_after_tax_profit_eur_per_year']*(1-(1+discount)**-annuity)/discount,rel_tol=1e-9)
    return cap,revenue,opex,tax,cash,npv

def lines(r,kind,key):
    result=defaultdict(float)
    for line in r['tea'][kind]:
        value=line.get(key)
        if isinstance(value,(int,float)) and math.isfinite(value):
            label=line.get('process_area') if kind!='revenue_lines' else PRODUCT.get(line.get('product_id'),line.get('product_id','Other'))
            result[label or 'Other']+=value
    return result

def stage(r,field):
    hours=r['analysis_period']['operating_hours']
    return {STAGE[x['stage_id']]:(max(0,x.get(field) or 0) if field=='heat_duty_kw' else (x.get(field) or 0))*hours/1000
            for x in r['annual']['process_pathway'] if x['stage_id'] in STAGE}

def gas_volume(r):
    # Revenue line carries dry product-gas volume at 293.15 K, including BG0 raw export.
    for line in r['tea']['revenue_lines']:
        if line.get('product_id')=='biomethane' and line.get('quantity_unit')=='m3/year' and line.get('quantity') is not None:
            return line['quantity']
    return 0.0

def plot_cash(folder,prefix,scenario,r):
    cap,revenue,opex,tax,cash,npv=money(r);years=np.arange(21)
    discount=r['tea']['candidate_economics']['assumptions']['discount_rate']
    cumulative=np.array([-cap+y*cash for y in years])/1000
    discounted=np.array([-cap+sum(cash/(1+discount)**j for j in range(1,y+1)) for y in years])/1000
    fig,ax=plt.subplots(figsize=(7.35,4.5));ax.plot(years,cumulative,color=GREEN,lw=2.2,label='Nominal cash balance')
    ax.plot(years,discounted,color=BLUE,lw=2.2,label='Discounted cash balance')
    ax.axhline(0,color=INK,lw=.8);ax.set_xlabel('Projection year');ax.set_ylabel('Cumulative cash (€ thousand)')
    ax.set_title('20-year cash balance',loc='left',pad=12);ax.legend(frameon=False);style(ax,'y')
    save(fig,folder,prefix+'_cash_balance_20y','Constant-account cumulative cash and discounted cash balance over 20 years',
         '€ thousand',scenario,'Year 0 is subsidy-adjusted partial equipment capital; years 1–20 repeat modeled after-tax operating cash. No inflation, debt, replacement, working capital, depreciation or terminal value.')
    fig,ax=plt.subplots(figsize=(7.35,4.2));ax.plot(years,np.maximum(0,cap-years*cash)/1000,color=ROSE,lw=2.2)
    ax.set_xlabel('Projection year');ax.set_ylabel('Unrecovered capital (€ thousand)')
    ax.set_title('Capital recovery balance',loc='left',pad=12);style(ax,'y')
    save(fig,folder,prefix+'_capital_balance_20y','Undiscounted capital balance remaining under constant after-tax cash flow',
         '€ thousand',scenario,'This is a capital recovery calculation, not a balance sheet.')

reports={}
for group,data in MANIFEST['groups'].items():
    reports[group]=[(row,json.loads(Path(row['report']).read_text(encoding='utf-8'))) for row in data['ranks']]
MATCHED_FILE=DATA/'matched_protein_bypass_manifest.json'
MATCHED_PAIRS=json.loads(MATCHED_FILE.read_text(encoding='utf-8'))['pairs'] if MATCHED_FILE.exists() else []
if MATCHED_PAIRS:
    reports['matched_bypass']=[]
    for pair in MATCHED_PAIRS:
        r=json.loads(Path(pair['matched_report']).read_text(encoding='utf-8'))
        row={'rank':pair['rank'],'sample_id':f'matched-PR0-{pair["rank"]:02d}',
             'source_sample_id':pair['source_sample_id'],'report':pair['matched_report'],
             'configuration':r['configuration']['simulation']['scenarios'],
             'feed_rate_kg_h':pair['feed_rate_kg_h'],
             'profit_eur_y':pair['matched_profit_eur_y'],
             'climate_kg_co2e_y':pair['matched_climate_kg_co2e_y']}
        reports['matched_bypass'].append((row,r))

# Each rank receives the same graph set. Zero-product routes retain the zero bar.
for group,items in reports.items():
    for row,r in items:
        rank=row['rank'];name=f'biosteam_{group}_rank_{rank:02d}'
        folder=f'08_candidate_comparison/biosteam/{group}/rank_{rank:02d}'
        scenario=f'{group} rank {rank}; {row["sample_id"]}; {row["feed_rate_kg_h"]:.1f} kg/h; 8760 h/y'
        annual=r['annual'];feed=annual['feed_processed']['value']/1000
        hbar(folder,name+'_solid_products','Solid products',list(PRODUCT.values()),
             [(annual['products'].get(k) or {}).get('value',0)/1000 for k in PRODUCT],
             't/year','Annual product stream masses from BioSTEAM',scenario,GREEN,
             'Wet product stream mass where the model reports it; not pure nutrient mass.')
        hbar(folder,name+'_biomethane','Gas export volume',['Dry exported gas'],[gas_volume(r)],
             'm³/year','Revenue-account dry gas export at 293.15 K; raw for BG0 and upgraded for selected BG routes',scenario,ROSE,
             'Saleable dry product at the benchmark-price reference basis, not raw biogas or methane Nm³.')
        for metric,title,color in [('power_kw','Electricity by stage',BLUE),('heat_duty_kw','Heating by stage',ROSE)]:
            values=stage(r,metric)
            hbar(folder,name+'_'+metric,title,list(values),list(values.values()),'MWh/year',
                 f'BioSTEAM pathway {metric} annualized by 8760 hours',scenario,color,
                 'Positive heat duty is heating; negative heat duty is omitted from this heating figure.' if metric=='heat_duty_kw' else '')
        unit_power=sorted(((u['unit_id'],u['demand']*r['analysis_period']['operating_hours']/1000)
                           for u in r['state_outputs']['utility_consumption']
                           if u['kind']=='electricity' and u['demand']>0),key=lambda x:x[1],reverse=True)
        assert math.isclose(sum(v for _,v in unit_power)*1000,annual['utilities']['electricity']['value'],rel_tol=1e-6)
        hbar(folder,name+'_electricity_by_unit','Electricity by unit',
             [k for k,_ in unit_power[:12]],[v for _,v in unit_power[:12]],'MWh/year',
             'Twelve largest unit electricity demands from BioSTEAM',scenario,BLUE,
             'Top 12 units only; all unit demands reconcile to the annual electricity total.')
        power=stage(r,'power_kw');factor=r['objectives']['climate']['value']/annual['utilities']['electricity']['value']
        climate={k:v*1000*factor/1000 for k,v in power.items()}
        assert math.isclose(sum(climate.values())*1000,r['objectives']['climate']['value'],rel_tol=1e-6)
        hbar(folder,name+'_climate_by_stage','Climate by stage',list(climate),list(climate.values()),
             't CO₂-eq/year','Attributional electricity burden distributed by simulated stage electricity',scenario,BLUE,
             'All included climate burden is electricity at 0.20 kg CO2e/kWh; heat, reagents, products and credits are outside this partial climate objective.')
        capex=lines(r,'capex_lines','direct_cost_eur');opex=lines(r,'opex_lines','annual_cost_eur');rev=lines(r,'revenue_lines','annual_revenue_eur')
        for suffix,title,values,color in [('capex','Partial direct CAPEX',capex,YELLOW),
                                          ('opex','Recorded OPEX',opex,ROSE),('revenue','Product revenue',rev,GREEN)]:
            empty=not values
            if empty:values={'No calculated line':0.0}
            scale=1000;unit='€ thousand' if suffix=='capex' else '€ thousand/year'
            hbar(folder,name+'_'+suffix,title,list(values),[v/scale for v in values.values()],unit,
                 f'Calculated {suffix} lines from selected backend candidate',scenario,color,
                 ('No calculated line in the saved TEA report. ' if empty else '')+
                 ('Uncalculated cost lines are absent; totals are incomplete.' if suffix!='revenue' else 'Industrial benchmark product prices are screening assumptions.'))
        t=r['tea']['totals'];cap,revenue,op,tax,cash,npv=money(r)
        grouped(folder,name+'_finance_bridge','Financial bridge',['Annual accounts'],[
            ('Revenue',[revenue/1000],GREEN),('Recorded OPEX',[op/1000],ROSE),
            ('Tax',[tax/1000],YELLOW),('After-tax cash',[cash/1000],BLUE)],
            '€ thousand/year','Candidate overlay annual financial account',scenario,
            'After-tax cash excludes annualized capital charge; partial OPEX substantially understates full project costs.')
        grouped(folder,name+'_economic_adjustments','Economic adjustments',['Candidate overlay'],[
            ('Savings',[t['optimization_savings_eur_per_year']/1000],GREEN),
            ('Revenue uplift',[t['optimization_revenue_uplift_eur_per_year']/1000],BLUE)],
            '€ thousand/year','Candidate annual savings and assumed revenue uplift',scenario,
            'Savings and uplift are candidate screening assumptions, not measured operating changes.')
        hbar(folder,name+'_subsidy','Capital subsidy',['One-time subsidy'],[t['subsidy_eur']/1000],
             '€ thousand','Candidate subsidy deducted from partial capital basis',scenario,YELLOW)
        plot_cash(folder,name,scenario,r)
        balance=annual['balance'];elements={k:v for k,v in balance['element_residuals_kg'].items() if k in ('carbon','nitrogen','phosphorus','potassium')}
        hbar(folder,name+'_element_balance','Element closure',list(elements),[abs(v) for v in elements.values()],
             'absolute kg/year','Absolute C, N, P and K model balance residuals',scenario,BLUE)
        hbar(folder,name+'_feed_and_output','Feed throughput',['Processed wet feed'],[feed],
             't/year','Annual processed wet biomass at selected feed rate',scenario,GREEN)

# Paired series: full front versus separately computed PR0-only front.
for group,items in reports.items():
    if group=='matched_bypass':continue
    rows=[x[0] for x in items];rr=[x[1] for x in items];labels=[str(x['rank']) for x in rows]
    folder='07_optimization' if group=='all' else '07_optimization/protein_bypass'
    scenario=f'{group} backend batch; 2000 total simulations, seed 42; objective-eligible {MANIFEST["groups"][group]["eligible_count"]}'
    front=MANIFEST['groups'][group]['front'];fig,ax=plt.subplots(figsize=(7.35,4.65))
    cloud=[s for s in BATCH['samples'] if s['status']=='evaluated' and
           s['configuration']['simulation']['scenarios']['feed_preparation']=='F1' and
           (group=='all' or s['configuration']['simulation']['scenarios']['protein_recovery']=='PR0') and
           s['outputs']['objectives']['operating_profit']['eligible'] and s['outputs']['objectives']['climate']['eligible']]
    ax.scatter([s['outputs']['objectives']['operating_profit']['value']/1000 for s in cloud],
               [s['outputs']['objectives']['climate']['value']/1000 for s in cloud],
               color=BLUE,s=9,alpha=.18,edgecolors='none',rasterized=True)
    ax.scatter([p['profit_eur_y']/1000 for p in front],[p['climate_kg_co2e_y']/1000 for p in front],
               color=MUTED,s=20,alpha=.8)
    ax.plot([p['profit_eur_y']/1000 for p in front],[p['climate_kg_co2e_y']/1000 for p in front],color=MUTED,lw=1.3)
    for row in rows:
        x=row['profit_eur_y']/1000;y=row['climate_kg_co2e_y']/1000
        ax.scatter(x,y,s=78,color=ROSE if row['rank']==0 else GREEN if row['rank']==10 else YELLOW,
                   edgecolors=INK,linewidth=.65,zorder=3)
        offset=(-11,-15) if group=='all' and row['rank']==4 else (11,8) if group=='all' and row['rank']==5 else (0,8)
        ax.annotate(str(row['rank']),(x,y),xytext=offset,textcoords='offset points',fontsize=8,ha='center')
    ax.set_xlabel('After-tax screening profit (€ thousand/year)');ax.set_ylabel('Attributional burden (t CO₂-eq/year)')
    ax.set_title('BioSTEAM Pareto ranks',loc='left',pad=12);style(ax,'y')
    save(fig,folder,f'biosteam_{group}_ranked_front','Backend-evaluated screening frontier with ranks 0–10',
         '€ thousand/year; t CO₂-eq/year',scenario,
         'Rank 0 has highest after-tax screening profit; rank 10 lowest partial attributional climate burden. PR0 front is recomputed from existing BioSTEAM runs.')
    hbar(folder,f'biosteam_{group}_profit_ranks','Profit by rank',labels,[x['profit_eur_y']/1000 for x in rows],
         '€ thousand/year','Backend candidate-adjusted screening profit',scenario,GREEN)
    hbar(folder,f'biosteam_{group}_climate_ranks','Climate by rank',labels,[x['climate_kg_co2e_y']/1000 for x in rows],
         't CO₂-eq/year','Partial attributional electricity burden by ranked candidate',scenario,BLUE)
    feed=[r['annual']['feed_processed']['value']/1000 for r in rr]
    hbar(folder,f'biosteam_{group}_feed_ranks','Feed by rank',labels,feed,'t/year',
         'Simulated annual wet feed across ranks',scenario,SAND,
         'Ranks differ in throughput; use the accompanying intensity graphs before attributing differences to technology.')
    hbar(folder,f'biosteam_{group}_profit_intensity','Profit intensity',labels,
         [row['profit_eur_y']/f for row,f in zip(rows,feed)],'€/t processed',
         'Annualized screening profit normalized to simulated wet feed',scenario,GREEN)
    hbar(folder,f'biosteam_{group}_climate_intensity','Climate intensity',labels,
         [row['climate_kg_co2e_y']/f for row,f in zip(rows,feed)],'kg CO₂-eq/t processed',
         'Partial attributional climate burden per wet tonne',scenario,ROSE)
    metrics=[('feed',1,'Feed (kt/y)','{:.1f}'),('profit',1,'Profit (€k/y)','{:.0f}'),
             ('climate',1,'Climate (t/y)','{:.0f}'),('npv',1,'NPV (€m)','{:.2f}'),
             ('energy',1,'Electricity (MWh/y)','{:.0f}')]
    matrix=[]
    for row,r,f in zip(rows,rr,feed):
        cap,rev,op,tax,cash,npv=money(r)
        matrix.append([f/1000,row['profit_eur_y']/1000,row['climate_kg_co2e_y']/1000,
                       npv/1e6,r['annual']['utilities']['electricity']['value']/1000])
    heatmap(folder,f'biosteam_{group}_kpi_heatmap','Ranked candidate KPIs',labels,
            [m[2] for m in metrics],matrix,[m[3] for m in metrics],
            'Feed, screening finance, partial climate and electricity for ranked cases',scenario,
            'NPV is projected from subsidy-adjusted partial direct capital and constant after-tax operating cash; it is not the base TEA financial KPI.')
    for suffix,title,key,scale,unit,color in [('capital','Partial capital','subsidy_adjusted_capex_eur',1000,'€ thousand',YELLOW),
                                               ('opex','Recorded OPEX','optimized_annual_opex_eur',1000,'€ thousand/year',ROSE),
                                               ('revenue','Revenue','optimized_annual_revenue_eur',1000,'€ thousand/year',GREEN),
                                               ('subsidy','Subsidy','subsidy_eur',1000,'€ thousand',SAND)]:
        hbar(folder,f'biosteam_{group}_{suffix}_ranks',title,labels,
             [r['tea']['totals'][key]/scale for r in rr],unit,f'{title} among ranked candidates',scenario,color)
    hbar(folder,f'biosteam_{group}_npv_ranks','Projected NPV',labels,[money(r)[-1]/1e6 for r in rr],
         '€ million','20-year constant-account NPV across ranked candidates',scenario,BLUE,
         'Partial-account projection; full installed CAPEX and OPEX are unavailable.')
    hbar(folder,f'biosteam_{group}_protein_ranks','Protein production',labels,
         [(r['annual']['products'].get('dry_protein_product') or {}).get('value',0)/1000 for r in rr],
         't/year','Modeled dry protein product by ranked case',scenario,GREEN)
    hbar(folder,f'biosteam_{group}_gas_ranks','Gas export volume',labels,[gas_volume(r) for r in rr],
         'm³/year','Revenue-account dry gas export at 293.15 K; raw for BG0 and upgraded for selected BG routes',scenario,ROSE)
    grouped(folder,f'biosteam_{group}_energy_ranks','Energy by rank',labels,[
        ('Electricity',[r['annual']['utilities']['electricity']['value']/1000 for r in rr],BLUE),
        ('Heat',[r['annual']['utilities']['heating']['value']/1000 for r in rr],ROSE)],
        'MWh/year','Annual electricity and heating demand across ranked candidates',scenario)
    hbar(folder,f'biosteam_{group}_labour_ranks','Labour reduction',labels,
         [100*r['tea']['candidate_economics']['assumptions']['labour_reduction'] for r in rr],
         '% assumed reduction','Sampled candidate labour-reduction overlay',scenario,BLUE,
         'Reduction is an economic assumption, not a measured staffing outcome.')
    # Categorical route map: text is the actual selected code, color groups codes only.
    route_keys=['feed_preparation','protein_recovery','anaerobic_digestion','biogas_upgrading','nutrient_recovery']
    route_titles=['Feed','Protein','AD','Gas','Nutrients']
    code_palette={'F1':BLUE,'F2':GREEN,'PR0':BG,'PR1':BLUE,'PR2':YELLOW,'PR3':GREEN,
                  'AD0':BG,'AD1':YELLOW,'AD3':ROSE,'BG0':BG,'BG2':GREEN,'BG3':BLUE,'BG4':ROSE,
                  'NR0':BG,'NR1':BLUE,'NR2':YELLOW,'NR3':ROSE,'NR4':GREEN}
    fig,ax=plt.subplots(figsize=(7.35,6.1))
    for i,row in enumerate(rows):
        for j,key in enumerate(route_keys):
            code=row['configuration'][key]
            ax.add_patch(plt.Rectangle((j-.5,i-.5),1,1,facecolor=code_palette.get(code,BG),edgecolor=BG,lw=2))
            ax.text(j,i,code,ha='center',va='center',fontsize=10,
                    color='white' if code_palette.get(code,BG) in (GREEN,ROSE) else INK)
    ax.set_xlim(-.5,len(route_keys)-.5);ax.set_ylim(len(rows)-.5,-.5)
    ax.set_xticks(range(len(route_keys)),route_titles);ax.set_yticks(range(len(rows)),labels)
    ax.tick_params(length=0);ax.set_title('Selected route codes',loc='left',pad=12)
    save(fig,folder,f'biosteam_{group}_route_matrix','Actual route configuration codes for ranked candidates',
         'route code',scenario,'Cell color identifies route code; colors are categorical and carry no performance order.')
    stage_labels=list(STAGE.values())
    heatmap(folder,f'biosteam_{group}_stage_energy_heatmap','Stage electricity',labels,
            stage_labels,[[stage(r,'power_kw')[k] for k in stage_labels] for r in rr],
            ['{:.0f}']*len(stage_labels),'Simulated electricity by process stage across ranked candidates',
            scenario,'Cell values in MWh/year.',unit_override='MWh/year')

# Matched protein-off variants isolate route effect at fixed feed and overlay inputs.
if MATCHED_PAIRS:
    folder='06_scenario_comparison/biosteam_matched_protein_bypass'
    scenario='Full-front ranks 0–10 rerun with PR0 only; same feed and candidate economics per pair'
    labels=[str(p['rank']) for p in MATCHED_PAIRS]
    original=[json.loads(Path(p['original_report']).read_text(encoding='utf-8')) for p in MATCHED_PAIRS]
    bypass=[json.loads(Path(p['matched_report']).read_text(encoding='utf-8')) for p in MATCHED_PAIRS]
    def pairbar(name,title,key,scale,unit,description,color=GREEN):
        values=[(b['objectives'][key]['value']-a['objectives'][key]['value'])/scale for a,b in zip(original,bypass)]
        hbar(folder,name,title,labels,values,unit,description,scenario,color,
             'Difference is PR0 minus original route; only protein recovery code changes within each pair.')
    pairbar('biosteam_matched_profit_change','Profit effect of PR0','operating_profit',1000,
            '€ thousand/year','Change in after-tax screening profit from bypassing protein',GREEN)
    pairbar('biosteam_matched_climate_change','Climate effect of PR0','climate',1000,
            't CO₂-eq/year','Change in partial attributional climate burden from bypassing protein',BLUE)
    for suffix,title,value,unit,color in [
        ('revenue','Product revenue',lambda r:r['tea']['totals']['optimized_annual_revenue_eur']/1000,'€ thousand/year',GREEN),
        ('opex','Recorded OPEX',lambda r:r['tea']['totals']['optimized_annual_opex_eur']/1000,'€ thousand/year',ROSE),
        ('npv','Projected NPV',lambda r:money(r)[-1]/1e6,'€ million',BLUE),
        ('electricity','Electricity',lambda r:r['annual']['utilities']['electricity']['value']/1000,'MWh/year',YELLOW),
        ('protein','Protein product',lambda r:(r['annual']['products'].get('dry_protein_product') or {}).get('value',0)/1000,'t/year',GREEN),
        ('gas','Gas export volume',gas_volume,'m³/year',ROSE)]:
        grouped(folder,f'biosteam_matched_{suffix}_comparison',title,labels,[
            ('Original',[value(r) for r in original],BLUE),('PR0',[value(r) for r in bypass],color)],
            unit,f'Paired original versus protein-bypass {title.lower()}',scenario,
            'Pairs retain identical feed rate and sampled economic assumptions. Financial accounts remain incomplete.')
    fig,ax=plt.subplots(figsize=(7.35,4.65))
    ax.scatter([r['objectives']['operating_profit']['value']/1000 for r in bypass],
               [r['objectives']['climate']['value']/1000 for r in bypass],s=55,color=ROSE,edgecolors=INK,linewidth=.5)
    for i,r in enumerate(bypass):
        ax.annotate(str(i),(r['objectives']['operating_profit']['value']/1000,
                            r['objectives']['climate']['value']/1000),xytext=(2,6),textcoords='offset points',fontsize=8)
    ax.set_xlabel('After-tax screening profit (€ thousand/year)');ax.set_ylabel('Attributional burden (t CO₂-eq/year)')
    ax.set_title('Matched PR0 outcomes',loc='left',pad=12);style(ax,'y')
    save(fig,folder,'biosteam_matched_pr0_outcomes','Matched protein-bypass outcomes retaining full-front rank labels',
         '€ thousand/year; t CO₂-eq/year',scenario,
         'These 11 points are paired counterfactual reruns, not all necessarily nondominated.')

# Existing figure index remains the union of actual baseline, frontend proxy and BioSTEAM series.
fields=['figure','description','source_dataset','scenario','units','file_location','notes']
ranking=[]
for group,items in reports.items():
    for row,r in items:
        t=r['tea']['totals'];cap,rev,op,tax,cash,npv=money(r)
        ranking.append({'group':group,'rank':row['rank'],'sample_id':row['sample_id'],
                        'run_id':r['run_id'],'feed_t_year':r['annual']['feed_processed']['value']/1000,
                        'profit_eur_year':row['profit_eur_y'],
                        'climate_kg_co2eq_year':row['climate_kg_co2e_y'],
                        'profit_eur_t_feed':row['profit_eur_y']/(r['annual']['feed_processed']['value']/1000),
                        'climate_kg_co2eq_t_feed':row['climate_kg_co2e_y']/(r['annual']['feed_processed']['value']/1000),
                        'partial_direct_capex_eur':t['partial_direct_capex_eur'],
                        'subsidy_eur':t['subsidy_eur'],'subsidy_adjusted_capex_eur':cap,
                        'recorded_opex_eur_year':op,'screening_revenue_eur_year':rev,
                        'after_tax_operating_cash_eur_year':cash,'projected_partial_npv_eur':npv,
                        'labour_reduction_fraction':r['tea']['candidate_economics']['assumptions']['labour_reduction'],
                        'protein_route':row['configuration']['protein_recovery'],
                        'ad_route':row['configuration']['anaerobic_digestion'],
                        'gas_route':row['configuration']['biogas_upgrading'],
                        'nutrient_route':row['configuration']['nutrient_recovery'],
                        'eligible_for_ranking':r['feasibility']['eligible_for_ranking'],
                        'storage_blocker_count':len(r['feasibility']['storage_blockers'])})
with (OUT/'biosteam_candidate_ranking.csv').open('w',newline='',encoding='utf-8-sig') as f:
    w=csv.DictWriter(f,fieldnames=list(ranking[0]));w.writeheader();w.writerows(ranking)
with (OUT/'biosteam_figure_index.csv').open('w',newline='',encoding='utf-8-sig') as f:
    w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows(INDEX)
with (OUT/'figure_index.csv').open(encoding='utf-8-sig',newline='') as f:
    previous=[r for r in csv.DictReader(f) if not r['figure'].startswith('biosteam_')]
with (OUT/'figure_index.csv').open('w',newline='',encoding='utf-8-sig') as f:
    w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows(previous+INDEX)
(OUT/'biosteam_frontier_manifest.json').write_text(json.dumps({
    'new_figure_count':len(INDEX),'job_id':MANIFEST['job_id'],'rank_definition':MANIFEST['rank_definition'],
    'all_front_count':MANIFEST['groups']['all']['front_count'],
    'protein_bypass_front_count':MANIFEST['groups']['protein_bypass']['front_count'],
    'scope':SCOPE,'projection':'constant annual optimized revenue and recorded OPEX; flat nominal 20 years; one-time subsidy-adjusted partial capital at year 0; 8% discount; no financing, inflation, replacements, working capital or terminal value',
    'matched_protein_bypass_cases':len(MATCHED_PAIRS),
    'magnesium_series':'omitted from displayed graphs'},indent=2),encoding='utf-8')
print(f'Generated {len(INDEX)} BioSTEAM frontier PNGs; combined index {len(previous)+len(INDEX)}')
