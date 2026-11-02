"""Dense comparisons from saved non-PEF BioSTEAM runs and explicit arithmetic sweeps.

The sampled batch is a design-space Monte Carlo experiment, not a probability
model for plant outcomes. No uncertainty confidence intervals are inferred.
"""
from __future__ import annotations
import csv,json,math,time
from collections import Counter,defaultdict
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
from results.report_figures import generate_dense_candidate_pngs as d

ROOT=d.ROOT;OUT=d.OUT;DATA=d.DATA
MAN=json.loads((DATA/'selection_manifest.json').read_text(encoding='utf-8'))
BATCH=json.loads(Path(MAN['source_batch']).read_text(encoding='utf-8'))
FULL=[d.load('all',i) for i in range(11)]
PR0=[d.load('protein_bypass',i) for i in range(11)]
MATCH=[d.load('matched_protein_bypass',i) for i in range(11)]
BASE=json.loads((OUT/'baseline_no_pef_screening.json').read_text(encoding='utf-8'))
SAMPLES=[s for s in BATCH['samples'] if s['status']=='evaluated' and
         s['configuration']['simulation']['scenarios']['feed_preparation']=='F1' and
         all(s['outputs']['objectives'][k]['eligible'] for k in ('operating_profit','climate'))]
COLORS={'PR0':d.BLUE,'PR1':d.YELLOW,'PR2':d.ROSE,'PR3':d.GREEN}
INDEX=[]

def figure(title,height=6.05):
    f,a=plt.subplots(2,2,figsize=(7.55,height));f.suptitle(title,x=.05,y=.99,ha='left',fontsize=14)
    return f,a.ravel()

def save(f,folder,name,description,units,source,notes):
    path=OUT/folder/f'{name}.png';path.parent.mkdir(parents=True,exist_ok=True)
    f.tight_layout(rect=(0,.01,1,.94),pad=1.2,w_pad=1.25,h_pad=1.45)
    temporary=path.with_name(path.stem+'_rendering.png')
    try:
        for attempt in range(6):
            try:
                f.savefig(temporary,dpi=300,bbox_inches='tight',pad_inches=.12)
                temporary.replace(path)
                break
            except OSError:
                if attempt==5:raise
                time.sleep(.25*(attempt+1))
    finally:
        plt.close(f)
        if temporary.exists():temporary.unlink()
    INDEX.append({'figure':path.relative_to(OUT).with_suffix('').as_posix().replace('/','__'),
                  'description':description,'source_dataset':source,
                  'scenario':'F1 non-PEF saved BioSTEAM batch and selected exact reruns',
                  'units':units,'file_location':str(path),'notes':notes})

def label(ax,title,xlab='',ylab='',grid='y'):
    ax.set_title(title,loc='left');ax.set_xlabel(xlab);ax.set_ylabel(ylab);d.style(ax,grid)

def obj(r,key):return r['objectives'][key]['value']
def feed_t(r):return r['annual']['feed_processed']['value']/1000
def profit(s):return s['outputs']['objectives']['operating_profit']['value']
def climate(s):return s['outputs']['objectives']['climate']['value']
def feed_sample(s):return s['configuration']['simulation']['wet_feed_rate_kg_hr']*8760/1000

def pareto_dashboard():
    f,a=figure('Non-PEF Pareto selection')
    for ax,group,reports,front,title in [(a[0],'all',FULL,MAN['groups']['all']['front'],'All protein routes'),
                                         (a[1],'protein_bypass',PR0,MAN['groups']['protein_bypass']['front'],'Protein bypass')]:
        cloud=[s for s in SAMPLES if group=='all' or s['configuration']['simulation']['scenarios']['protein_recovery']=='PR0']
        ax.scatter([profit(s)/1000 for s in cloud],[climate(s)/1000 for s in cloud],s=7,c=d.BLUE,alpha=.13,rasterized=True)
        ax.plot([p['profit_eur_y']/1000 for p in front],[p['climate_kg_co2e_y']/1000 for p in front],color=d.MUTED,lw=1.1)
        for rank,r in enumerate(reports):
            ax.scatter(obj(r,'operating_profit')/1000,obj(r,'climate')/1000,s=56,
                       c=d.ROSE if rank==0 else d.GREEN if rank==10 else d.YELLOW,edgecolors=d.INK,lw=.5,zorder=3)
            if rank in (0,5,10):ax.annotate(str(rank),(obj(r,'operating_profit')/1000,obj(r,'climate')/1000),
                                            xytext=(5,5),textcoords='offset points',fontsize=7)
        label(ax,title,'Profit (k€/year)','Burden (t CO₂-eq/year)')
    ranks=np.arange(11)
    for rr,name,color in [(FULL,'All routes',d.GREEN),(PR0,'PR0',d.BLUE)]:
        a[2].plot(ranks,[obj(r,'operating_profit')/feed_t(r) for r in rr],marker='o',ms=3,color=color,label=name)
        a[3].plot(ranks,[obj(r,'climate')/feed_t(r) for r in rr],marker='o',ms=3,color=color,label=name)
    label(a[2],'Profit intensity','Rank','€/t wet grass');label(a[3],'Climate intensity','Rank','kg CO₂-eq/t wet grass')
    a[2].legend(frameon=False,fontsize=7.5);a[3].legend(frameon=False,fontsize=7.5)
    save(f,'07_optimization','non_pef_pareto_dashboard','Non-PEF screening fronts with selected ranks and feed-normalized objectives',
         'k€/year; t CO₂-eq/year; €/t; kg CO₂-eq/t',MAN['source_batch'],
         'Rank 0 is economic endpoint (rose); rank 10 is environmental endpoint (green). Electricity-only attributional burden at 0.20 kg CO₂e/kWh. Throughput varies; front is screening-level.')

def climate_dashboard():
    cases=[BASE,FULL[0],FULL[5],FULL[10],PR0[0],PR0[10]];names=['Baseline','Full 0','Full 5','Full 10','PR0 0','PR0 10']
    stages=['Preparation','Protein','Digestion','Gas upgrading','Nutrients'];colors=[d.BLUE,d.GREEN,d.YELLOW,d.ROSE,d.SAND]
    f,a=figure('Attributional climate inventory')
    bottoms=np.zeros(len(cases))
    for stage,color in zip(stages,colors):
        vals=np.array([d.stage(r,'power_kw').get(stage,0)*.2 for r in cases]);a[0].bar(names,vals,bottom=bottoms,color=color,label=stage);bottoms+=vals
    label(a[0],'Electricity burden','','t CO₂-eq/year');a[0].tick_params(axis='x',rotation=25);a[0].legend(frameon=False,fontsize=6.5,ncol=2)
    a[1].bar(names,[b*1000/feed_t(r) for b,r in zip(bottoms,cases)],color=d.ROSE)
    label(a[1],'Feed intensity','','kg CO₂-eq/t grass');a[1].tick_params(axis='x',rotation=25)
    for stage,color in zip(stages,colors):a[2].plot(names,[d.stage(r,'heat_duty_kw').get(stage,0) for r in cases],marker='o',ms=3,color=color,label=stage)
    label(a[2],'Heat inventory','','MWh/year');a[2].tick_params(axis='x',rotation=25)
    missing=[sum(x.get('status')=='missing_factor' for x in r['lca']['inventory']) for r in cases]
    a[3].bar(names,missing,color=d.YELLOW);label(a[3],'Missing LCA factors','','inventory flows');a[3].tick_params(axis='x',rotation=25)
    save(f,'04_lca','non_pef_attributional_burden','Electricity-only attributional burden and uncharacterized heat/inventory across selected non-PEF routes',
         't CO₂-eq/year; kg CO₂-eq/t; MWh/year; inventory flows','Exact BioSTEAM reports; annual process pathway; LCA inventory',
         'The climate account applies the saved screening factor 0.20 kg CO₂e/kWh to modeled electricity. Heat and other inventory flows are shown separately and are not converted to CO₂e without factors. No offset or substitution credit is used.')

def finance_dashboard():
    cases=[BASE,FULL[0],FULL[5],FULL[10],PR0[0],PR0[10]];names=['Baseline','Full 0','Full 5','Full 10','PR0 0','PR0 10']
    f,a=figure('Economic route accounts')
    vals=[d.account(r) for r in cases];x=np.arange(len(cases))
    for key,ix,color in [('Revenue',1,d.GREEN),('OPEX',2,d.BLUE),('Tax',3,d.ROSE)]:
        a[0].plot(x,[v[ix]/1000 for v in vals],marker='o',ms=3,color=color,label=key)
    label(a[0],'Annual accounts','','k€/year');a[0].set_xticks(x,names,rotation=25);a[0].legend(frameon=False,fontsize=7)
    a[1].bar(names,[v[4]/1000 for v in vals],color=d.GREEN);label(a[1],'Operating cash','','k€/year');a[1].tick_params(axis='x',rotation=25)
    a[2].bar(names,[v[5]/1e6 for v in vals],color=d.BLUE);label(a[2],'20-year NPV','','€ million');a[2].tick_params(axis='x',rotation=25)
    a[3].bar(names,[r['tea']['totals']['partial_direct_capex_eur']/1000 for r in cases],color=d.YELLOW,label='Direct CAPEX')
    a[3].bar(names,[r['tea']['totals']['subsidy_eur']/1000 for r in cases],color=d.ROSE,label='Subsidy')
    label(a[3],'Capital and subsidy','','€ thousand');a[3].tick_params(axis='x',rotation=25);a[3].legend(frameon=False,fontsize=7)
    save(f,'03_tea','non_pef_economic_accounts','Partial BioSTEAM financial accounts and constant-account NPV for baseline and selected non-PEF candidates',
         'k€/year; € million; € thousand','Baseline screening report; exact non-PEF Pareto reports',
         'Baseline uses benchmark product prices with zero optimization savings/subsidy. Candidate cases retain sampled savings and subsidy. CAPEX/OPEX are incomplete; NPV repeats nominal annual cash for 20 years at 8%.')

def hotspots():
    cases=[BASE,FULL[0],FULL[10],PR0[0]];names=['Baseline','Full 0','Full 10','PR0 0'];stages=['Preparation','Protein','Digestion','Gas upgrading','Nutrients']
    f,a=figure('Process hotspots')
    width=.19;x=np.arange(len(stages))
    for i,(r,name) in enumerate(zip(cases,names)):
        a[0].bar(x+(i-1.5)*width,[d.stage(r,'power_kw').get(k,0) for k in stages],width,label=name)
        a[1].bar(x+(i-1.5)*width,[d.stage(r,'heat_duty_kw').get(k,0) for k in stages],width,label=name)
    for ax,title in [(a[0],'Electricity by stage'),(a[1],'Heat by stage')]:
        label(ax,title,'','MWh/year');ax.set_xticks(x,['Prep','Protein','AD','Gas','Nutrients'],rotation=20)
    a[0].legend(frameon=False,fontsize=6.5,ncol=2)
    for i,(r,name) in enumerate(zip(cases,names)):
        top=sorted(((u['unit_id'],u['demand']*8760/1000) for u in r['state_outputs']['utility_consumption']
                    if u['kind']=='electricity' and u['demand']>0),key=lambda v:-v[1])[:3]
        a[2].barh([f'{name} {unit}' for unit,_ in top],[v for _,v in top],color=[d.BLUE,d.GREEN,d.ROSE,d.YELLOW][i])
    label(a[2],'Largest equipment','MWh/year','');a[2].invert_yaxis()
    a[3].scatter([d.account(r)[4]/feed_t(r) for r in cases],
                 [r['annual']['utilities']['electricity']['value']/1000/feed_t(r) for r in cases],
                 s=85,c=[d.BLUE,d.GREEN,d.ROSE,d.YELLOW],edgecolors=d.INK,lw=.5)
    for r,name in zip(cases,names):a[3].annotate(name,(d.account(r)[4]/feed_t(r),r['annual']['utilities']['electricity']['value']/1000/feed_t(r)),xytext=(4,4),textcoords='offset points',fontsize=7)
    label(a[3],'Cash versus power','€/t grass','MWh/t grass')
    save(f,'05_hotspots','non_pef_utility_cost_hotspots','Stage and unit energy hotspots with feed-normalized economic relation',
         'MWh/year; €/t; MWh/t','Exact non-PEF BioSTEAM reports',
         'Only modeled utility demand is shown. No reagent series or empty reagent bars. Cash uses incomplete recorded OPEX/CAPEX and screening product prices.')

def mc_dashboard():
    f,a=figure('Non-PEF design sweep');pr=np.array([profit(s)/1000 for s in SAMPLES]);cl=np.array([climate(s)/1000 for s in SAMPLES]);fr=np.array([feed_sample(s) for s in SAMPLES])
    for route,color in COLORS.items():
        ss=[s for s in SAMPLES if s['configuration']['simulation']['scenarios']['protein_recovery']==route]
        a[0].scatter([profit(s)/1000 for s in ss],[climate(s)/1000 for s in ss],s=8,alpha=.35,c=color,label=route,rasterized=True)
    label(a[0],'Sampled designs','Profit (k€/year)','Burden (t CO₂-eq/year)');a[0].legend(frameon=False,fontsize=7)
    a[1].hist(pr,bins=32,color=d.GREEN,alpha=.88);label(a[1],'Profit distribution','k€/year','sampled designs')
    a[2].hist(cl,bins=32,color=d.ROSE,alpha=.88);label(a[2],'Burden distribution','t CO₂-eq/year','sampled designs')
    a[3].scatter(pr*1000/fr,cl*1000/fr,s=7,c=d.BLUE,alpha=.25,rasterized=True)
    label(a[3],'Feed-normalized designs','€/t grass','kg CO₂-eq/t grass')
    save(f,'09_uncertainty','non_pef_monte_carlo_design_sweep','Distribution of 1049 eligible saved non-PEF random design evaluations',
         'k€/year; t CO₂-eq/year; €/t; kg CO₂-eq/t',MAN['source_batch'],
         'Monte Carlo here denotes the saved random design-space sampling. Route, throughput and economic assumptions vary independently. Frequencies are not calibrated probabilities or confidence intervals. Climate is electricity-only attributional burden.')

def parameter_dashboard():
    f,a=figure('Sampled parameter response')
    parameters=[('labour_reduction','Labour saving'),('logistics_reduction','Logistics saving'),
                ('energy_reduction','Energy saving'),('protein_yield_uplift','Protein uplift')]
    y=np.array([profit(s)/feed_sample(s) for s in SAMPLES])
    for ax,(key,title) in zip(a,parameters):
        x=np.array([s['configuration']['candidate_economics'][key]*100 for s in SAMPLES])
        ax.scatter(x,y,s=7,c=[COLORS[s['configuration']['simulation']['scenarios']['protein_recovery']] for s in SAMPLES],alpha=.23,rasterized=True)
        label(ax,title,'% assumed','€/t grass')
    save(f,'09_uncertainty','non_pef_parameter_response','Observed screening profit intensity against sampled candidate economic parameters',
         '%; €/t wet grass',MAN['source_batch'],
         'Each dot is an actual saved BioSTEAM evaluation; other route and economic inputs vary simultaneously. Scatter is descriptive association, not one-factor causal sensitivity or a probability model.')

def tornado_and_surface():
    r=FULL[0];cap,rev,op,tax,cash,npv=d.account(r);rate=.08;ann=sum((1+rate)**-y for y in range(1,21));tax_rate=r['tea']['candidate_economics']['assumptions']['tax_rate']
    def value(price=1,opex=1,capital=1,discount=.08):
        pretax=rev*price-op*opex;after=pretax-max(0,pretax)*tax_rate
        return -cap*capital+sum(after/(1+discount)**y for y in range(1,21))
    f,a=figure('Economic sensitivity')
    specs=[('Product prices',dict(price=.9),dict(price=1.1)),('Recorded OPEX',dict(opex=1.1),dict(opex=.9)),
           ('Partial CAPEX',dict(capital=1.1),dict(capital=.9)),('Discount rate',dict(discount=.10),dict(discount=.06))]
    low=[value(**lo)/1e6 for _,lo,hi in specs];high=[value(**hi)/1e6 for _,lo,hi in specs]
    y=np.arange(len(specs));a[0].barh(y,np.array(high)-np.array(low),left=low,color=d.ROSE,height=.55)
    a[0].axvline(npv/1e6,color=d.INK,lw=1,ls='--');a[0].set_yticks(y,[s[0] for s in specs]);a[0].invert_yaxis();label(a[0],'NPV tornado','€ million','')
    prices=np.linspace(.7,1.3,41);costs=np.linspace(.7,1.3,41)
    z=np.array([[value(price=p,opex=c)/1e6 for p in prices] for c in costs]);im=a[1].imshow(z,origin='lower',extent=[70,130,70,130],aspect='auto',cmap='RdYlGn')
    if z.min()<=0<=z.max():a[1].contour(prices*100,costs*100,z,levels=[0],colors=d.INK,linewidths=1)
    label(a[1],'Price and OPEX','Price factor (%)','OPEX factor (%)');f.colorbar(im,ax=a[1],label='NPV (€ million)',shrink=.7)
    a[2].plot(prices*100,[value(price=p)/1e6 for p in prices],color=d.GREEN);a[2].axhline(0,color=d.INK,lw=.7)
    label(a[2],'Price response','Price factor (%)','NPV (€ million)')
    discounts=np.linspace(.04,.14,40);a[3].plot(discounts*100,[value(discount=x)/1e6 for x in discounts],color=d.BLUE)
    label(a[3],'Discount response','Discount rate (%)','NPV (€ million)')
    save(f,'09_uncertainty','non_pef_economic_tornado','Deterministic one-factor NPV sensitivity and two-factor price/OPEX surface for full-front rank 0',
         '€ million; %','Full-front rank 0 recorded revenue, OPEX and partial capital',
         'Arithmetic postprocessing of one saved run. Price, OPEX and CAPEX tornado ranges are ±10%; discount is 6–10%. Tax is applied to positive operating surplus. These are explicit hypothetical bounds, not stochastic uncertainty intervals.')

def volcano():
    ranks=np.arange(11);dp=np.array([(obj(b,'operating_profit')-obj(o,'operating_profit'))/1000 for o,b in zip(FULL,MATCH)])
    dc=np.array([(obj(b,'climate')-obj(o,'climate'))/1000 for o,b in zip(FULL,MATCH)])
    f,a=figure('Protein bypass trade-offs')
    a[0].scatter(dp,dc,s=90,c=[d.ROSE if x<0 else d.GREEN for x in dp],edgecolors=d.INK,lw=.5)
    for i,(x,y) in enumerate(zip(dp,dc)):
        if i==10:continue
        a[0].annotate('9, 10' if i==9 else str(i),(x,y),xytext=(4,4),textcoords='offset points',fontsize=7)
    a[0].axhline(0,color=d.INK,lw=.7);a[0].axvline(0,color=d.INK,lw=.7);label(a[0],'Profit–burden volcano','Δ profit (k€/year)','Δ burden (t CO₂-eq/year)')
    a[1].bar(ranks,dp,color=d.GREEN);label(a[1],'Profit effect','Full-front rank','k€/year')
    a[2].bar(ranks,dc,color=d.BLUE);label(a[2],'Climate effect','Full-front rank','t CO₂-eq/year')
    a[3].scatter(dp*1000/np.array([feed_t(r) for r in FULL]),dc*1000/np.array([feed_t(r) for r in FULL]),
                 c=d.ROSE,s=65,edgecolors=d.INK,lw=.5)
    label(a[3],'Feed-normalized effect','Δ €/t grass','Δ kg CO₂-eq/t grass')
    save(f,'09_uncertainty','non_pef_protein_bypass_volcano','Paired protein-bypass economic and climate changes at fixed feed and economic assumptions',
         'k€/year; t CO₂-eq/year; €/t; kg CO₂-eq/t','Full-front and matched protein-bypass exact BioSTEAM reruns',
         'Each pair changes only protein recovery to PR0. Negative climate change means lower electricity-only attributional burden. This is a deterministic intervention comparison, not statistical significance.')

def technical_profiles():
    cases=[BASE,FULL[0],FULL[5],FULL[10],PR0[0],PR0[10]];names=['Baseline','Full 0','Full 5','Full 10','PR0 0','PR0 10'];x=np.arange(len(cases))
    f,a=figure('Technical route profiles')
    products=[('Protein','dry_protein_product',d.GREEN),('N product','ammonium_product',d.BLUE),
              ('P product','phosphorus_product',d.YELLOW),('Nutrient solids','nutrient_rich_solids',d.SAND)]
    bottom=np.zeros(len(cases))
    for name,key,color in products:
        v=np.array([(r['annual']['products'].get(key) or {}).get('value',0)/feed_t(r) for r in cases]);a[0].bar(x,v,bottom=bottom,color=color,label=name);bottom+=v
    label(a[0],'Solid stream yields','','kg/t grass');a[0].legend(frameon=False,fontsize=6.5,ncol=2)
    raw=[];up=[]
    for r in cases:
        s=d.streams(r);ids={p['product_id']:p['stream_id'] for p in r['products']}
        raw.append(d.gas_nm3(s,'raw_biogas')/feed_t(r));up.append(d.gas_nm3(s,ids.get('biomethane',''))/feed_t(r))
    a[1].bar(x-.19,raw,.38,color=d.ROSE,label='Raw biogas');a[1].bar(x+.19,up,.38,color=d.GREEN,label='Export gas')
    label(a[1],'Dry gas yields','','Nm³/t grass');a[1].legend(frameon=False,fontsize=7)
    a[2].bar(x-.19,[r['annual']['utilities']['electricity']['value']/1000/feed_t(r) for r in cases],.38,color=d.BLUE,label='Electricity')
    a[2].bar(x+.19,[r['annual']['utilities']['heating']['value']/1000/feed_t(r) for r in cases],.38,color=d.ROSE,label='Heat')
    label(a[2],'Utility intensity','','MWh/t grass');a[2].legend(frameon=False,fontsize=7)
    a[3].bar(x,[feed_t(r)/1000 for r in cases],color=d.GREEN);label(a[3],'Processed biomass','','kt/year')
    for ax in a:ax.set_xticks(x,names,rotation=25)
    save(f,'02_technical','non_pef_route_profiles','Feed-normalized solids, distinct raw/upgraded gas volumes, utility demand and annual feed for selected F1 routes',
         'kg/t; dry Nm³/t; MWh/t; kt/year','Exact F1 BioSTEAM reports and saved gas stream components',
         'Solid yields are reported stream mass, not pure nutrient mass. Export gas is raw for BG0 and upgraded for other BG routes. Gas volumes use dry ideal gas at 273.15 K and 101325 Pa. All routes use F1 without PEF.')

def frontier_process():
    ranks=np.arange(11);f,a=figure('Process along the frontier')
    for rr,name,color in [(FULL,'All routes',d.GREEN),(PR0,'PR0',d.BLUE)]:
        a[0].plot(ranks,[(r['annual']['products'].get('dry_protein_product') or {}).get('value',0)/feed_t(r) for r in rr],marker='o',ms=3,color=color,label=name)
        a[1].plot(ranks,[(r['annual']['products'].get('ammonium_product') or {}).get('value',0)/feed_t(r) for r in rr],marker='o',ms=3,color=color,label=name)
        a[2].plot(ranks,[r['annual']['utilities']['electricity']['value']/1000/feed_t(r) for r in rr],marker='o',ms=3,color=color,label=name)
        a[3].plot(ranks,[r['annual']['utilities']['heating']['value']/1000/feed_t(r) for r in rr],marker='o',ms=3,color=color,label=name)
    for ax,title,unit in zip(a,['Protein stream','Ammonium stream','Electricity intensity','Heat intensity'],
                             ['kg/t grass','kg/t grass','MWh/t grass','MWh/t grass']):
        label(ax,title,'Rank',unit);ax.set_xticks(ranks[::2])
    a[0].legend(frameon=False,fontsize=7)
    save(f,'02_technical','non_pef_frontier_process','Product-stream and utility intensities across two independently selected F1 fronts',
         'kg/t; MWh/t','22 exact selected non-PEF BioSTEAM reports',
         'Independent ranks need not share feed or technology; intensities divide saved annual quantities by each run’s wet feed. Missing products appear as zero trajectories only where a bypass is meaningful.')

def climate_hotspot_matrix():
    stages=['Preparation','Protein','Digestion','Gas upgrading','Nutrients'];rr=FULL+PR0;labels=['F'+str(i) for i in range(11)]+['B'+str(i) for i in range(11)]
    burden=np.array([[d.stage(r,'power_kw').get(k,0)*.2*1000/feed_t(r) for k in stages] for r in rr])
    heat=np.array([[d.stage(r,'heat_duty_kw').get(k,0)/feed_t(r) for k in stages] for r in rr])
    f,a=figure('Climate hotspot matrix',6.45)
    im=a[0].imshow(burden,aspect='auto',cmap='YlOrRd');a[0].set_xticks(range(5),['Prep','Protein','AD','Gas','Nutrients'],rotation=25);a[0].set_yticks(range(0,22,2),labels[::2]);a[0].set_title('Burden by stage',loc='left');f.colorbar(im,ax=a[0],label='kg CO₂-eq/t',shrink=.7)
    hm=a[1].imshow(heat,aspect='auto',cmap='YlGnBu');a[1].set_xticks(range(5),['Prep','Protein','AD','Gas','Nutrients'],rotation=25);a[1].set_yticks(range(0,22,2),labels[::2]);a[1].set_title('Uncharacterized heat',loc='left');f.colorbar(hm,ax=a[1],label='MWh/t',shrink=.7)
    a[2].bar(np.arange(11)-.19,burden[:11].sum(axis=1),.38,color=d.GREEN,label='Full');a[2].bar(np.arange(11)+.19,burden[11:].sum(axis=1),.38,color=d.BLUE,label='PR0')
    label(a[2],'Total electricity burden','Rank','kg CO₂-eq/t');a[2].legend(frameon=False,fontsize=7)
    a[3].scatter([d.account(r)[4]/feed_t(r) for r in rr],burden.sum(axis=1),
                 c=[d.GREEN]*11+[d.BLUE]*11,s=55,edgecolors=d.INK,lw=.4)
    label(a[3],'Cash–burden relation','Operating cash (€/t)','kg CO₂-eq/t')
    save(f,'04_lca','non_pef_climate_hotspot_matrix','Stage attributional electricity burden and separately inventoried heat across 22 selected F1 routes',
         'kg CO₂-eq/t; MWh/t; €/t','22 exact non-PEF BioSTEAM reports',
         'F denotes full-front rank and B protein-bypass rank. Electricity is characterized at 0.20 kg CO₂e/kWh; heat has no validated factor and is not added to burden.')

def climate_factor_sensitivity():
    cases=[BASE,FULL[0],FULL[10],PR0[0],PR0[10]];names=['Baseline','Full 0','Full 10','PR0 0','PR0 10'];colors=[d.BLUE,d.GREEN,d.ROSE,d.YELLOW,d.SAND]
    factors=np.linspace(.05,.4,60);f,a=figure('Electricity factor sensitivity')
    for r,name,color in zip(cases,names,colors):
        power=r['annual']['utilities']['electricity']['value']
        a[0].plot(factors,power*factors/1000,label=name,color=color)
        a[1].plot(factors,power*factors/feed_t(r),label=name,color=color)
    a[0].axvline(.2,color=d.INK,lw=.8,ls='--');a[1].axvline(.2,color=d.INK,lw=.8,ls='--')
    label(a[0],'Annual burden','Factor (kg CO₂-eq/kWh)','t CO₂-eq/year');a[0].legend(frameon=False,fontsize=7)
    label(a[1],'Feed intensity','Factor (kg CO₂-eq/kWh)','kg CO₂-eq/t')
    a[2].bar(names,[r['annual']['utilities']['electricity']['value']/1000 for r in cases],color=colors)
    label(a[2],'Modeled electricity','','MWh/year');a[2].tick_params(axis='x',rotation=25)
    a[3].bar(names,[r['annual']['utilities']['electricity']['value']/feed_t(r) for r in cases],color=colors)
    label(a[3],'Electricity intensity','','kWh/t grass');a[3].tick_params(axis='x',rotation=25)
    save(f,'04_lca','non_pef_electricity_factor_sensitivity','Deterministic attributional electricity factor scenarios on actual F1 utility inventories',
         'kg CO₂-eq/kWh; t CO₂-eq/year; kg CO₂-eq/t; MWh/year; kWh/t','Exact non-PEF BioSTEAM utility inventories',
         'Factor range 0.05–0.40 kg CO₂e/kWh is an explicit sensitivity sweep, not an empirical uncertainty distribution. Dashed line marks the saved screening factor 0.20. Heat and other missing LCA factors remain uncharacterized.')

def environmental_tornado():
    cases=[BASE,FULL[0],FULL[10],PR0[0]];names=['Baseline','Full 0','Full 10','PR0 0']
    f,a=figure('Environmental sensitivity')
    power=FULL[0]['annual']['utilities']['electricity']['value'];reference=power*.2/1000
    ranges=[('Electricity factor',power*.15/1000,power*.25/1000),
            ('Electricity demand',reference*.9,reference*1.1),
            ('Operating hours',reference*.95,reference*1.05)]
    yy=np.arange(len(ranges));a[0].barh(yy,[hi-lo for _,lo,hi in ranges],left=[lo for _,lo,hi in ranges],color=d.ROSE)
    a[0].axvline(reference,color=d.INK,lw=.8,ls='--');a[0].set_yticks(yy,[x[0] for x in ranges]);a[0].invert_yaxis()
    label(a[0],'Rank 0 burden tornado','t CO₂-eq/year','')
    levels=[.15,.20,.25]
    for i,(r,name) in enumerate(zip(cases,names)):
        demand=r['annual']['utilities']['electricity']['value'];a[1].plot(levels,[demand*v/1000 for v in levels],marker='o',ms=3,label=name)
    label(a[1],'Factor scenarios','kg CO₂-eq/kWh','t CO₂-eq/year');a[1].legend(frameon=False,fontsize=7)
    a[2].bar(names,[r['annual']['utilities']['electricity']['value']*.2/feed_t(r) for r in cases],color=[d.BLUE,d.GREEN,d.ROSE,d.YELLOW])
    label(a[2],'Reference intensity','','kg CO₂-eq/t grass');a[2].tick_params(axis='x',rotation=25)
    a[3].bar(names,[r['annual']['utilities']['heating']['value']/1000/feed_t(r) for r in cases],color=d.SAND)
    label(a[3],'Uncharacterized heat','','MWh/t grass');a[3].tick_params(axis='x',rotation=25)
    save(f,'09_uncertainty','non_pef_environmental_tornado','Deterministic electricity-factor, demand and operating-hours sensitivity of partial attributional burden',
         't CO₂-eq/year; kg CO₂-eq/t; MWh/t','Exact F1 electricity and heat inventories',
         'Rank-0 tornado uses 0.15–0.25 kg CO₂e/kWh, ±10% electricity and ±5% operating hours as explicit hypothetical ranges. Hours affect annual burden but not per-tonne intensity at constant process rates. No full LCA or probabilistic interval is implied.')

def route_design_distributions():
    groups={k:[s for s in SAMPLES if s['configuration']['simulation']['scenarios']['protein_recovery']==k]
            for k in COLORS}
    f,a=figure('Route design distributions')
    measures=[('Profit intensity',lambda s:profit(s)/feed_sample(s),'€/t grass'),
              ('Climate intensity',lambda s:climate(s)/feed_sample(s),'kg CO₂-eq/t grass'),
              ('Wet feed rate',lambda s:s['configuration']['simulation']['wet_feed_rate_kg_hr']/1000,'t/h'),
              ('Electricity intensity',lambda s:climate(s)/.2/feed_sample(s),'kWh/t grass')]
    for ax,(title,fn,unit) in zip(a,measures):
        data=[[fn(s) for s in ss] for ss in groups.values()]
        parts=ax.violinplot(data,showmedians=True,showextrema=False)
        for body,color in zip(parts['bodies'],COLORS.values()):body.set_facecolor(color);body.set_edgecolor('none');body.set_alpha(.8)
        parts['cmedians'].set_color(d.INK);ax.set_xticks(range(1,5),list(groups))
        label(ax,title,'Protein route',unit)
    save(f,'09_uncertainty','non_pef_route_design_distributions','Distribution of actual sampled F1 design outcomes by protein technology route',
         '€/t; kg CO₂-eq/t; t/h; kWh/t',MAN['source_batch'],
         'Violin widths describe the saved random design sweep, not empirical probabilities. Other technology, throughput and economic settings vary within each protein-route group. Electricity intensity is inferred from the saved 0.20 kg CO₂e/kWh electricity-only climate objective.')

def main():
    pareto_dashboard();climate_dashboard();finance_dashboard();hotspots();mc_dashboard();parameter_dashboard();tornado_and_surface();volcano()
    technical_profiles();frontier_process();climate_hotspot_matrix();climate_factor_sensitivity()
    environmental_tornado();route_design_distributions()
    fields=['figure','description','source_dataset','scenario','units','file_location','notes']
    with (OUT/'no_pef_analysis_figure_index.csv').open('w',encoding='utf-8-sig',newline='') as f:
        w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows(INDEX)
    print('Generated',len(INDEX),'dense non-PEF analysis figures')

if __name__=='__main__':main()
