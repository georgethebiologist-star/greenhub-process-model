import React, {useMemo, useState} from 'react';
import {CartesianGrid, Legend, LineChart, Line, ResponsiveContainer, Tooltip, XAxis, YAxis} from 'recharts';
import type {AnnualSummary,SimulationResult} from '../types';

type FeedId='available'|'processed'|'press_cake'|'digestate';
type ProductId='protein'|'biostimulant'|'nutrient'|'ammonium'|'potassium'|'nutrient_solids'|'biomethane';
type EnergyId='electricity'|'heat'|'cooling';
type GraphId='feed'|'products'|'energy';
type Definition={id:string;label:string;source:'schedule'|'schedule_timeseries'|'bulk_streams'|'small_products'|'biomethane'|'energy';key:string;color:string;unit:string;convert?:(value:number)=>number};

const feedSeries:Definition[]=[
  {id:'available',label:'Available biomass',source:'schedule_timeseries',key:'available_biomass_tonnes',color:'#408f4d',unit:'t/week'},
  {id:'processed',label:'Biomass processed',source:'schedule_timeseries',key:'processed_biomass_tonnes',color:'#729ad2',unit:'t/week'},
  {id:'press_cake',label:'Press cake',source:'bulk_streams',key:'press_cake_tonnes',color:'#d1a520',unit:'t/week'},
  {id:'digestate',label:'Juice',source:'bulk_streams',key:'juice_tonnes',color:'#b77436',unit:'t/week'},
];
const energySeries:Definition[]=[
  {id:'electricity',label:'Electricity',source:'energy',key:'electricity_MWh',color:'#d277a3',unit:'MWh/month'},
  {id:'heat',label:'Heat',source:'energy',key:'heating_GJ',color:'#d1a520',unit:'MWh/month',convert:value=>value/3.6},
  {id:'cooling',label:'Cooling',source:'energy',key:'cooling_GJ',color:'#729ad2',unit:'MWh/month',convert:value=>value/3.6},
];

function steadyMonthlyRows(annual:AnnualSummary, result:SimulationResult, definition:Definition) {
  const annualFeed=Math.max(0,Number(annual.feed_processed?.value||0)/1000);
  const cakeStream=result.streams.find(stream=>/pressed[_\s-]?fibre[_\s-]?cake|press[_\s-]?cake/i.test(`${stream.id} ${stream.name}`));
  const annualCake=Math.max(0,Number(cakeStream?.mass_flow_kgh||0)*Number(annual.period?.operating_hours||0)/1000);
  let total=0;
  if(definition.id==='available')total=Math.max(annualFeed,Number(annual.biomass_schedule?.annual_available_tonnes||0));
  else if(definition.id==='processed')total=annualFeed;
  else if(definition.id==='press_cake')total=annualCake;
  else if(definition.id==='digestate')total=Math.max(0,annualFeed-annualCake);
  else if(definition.id==='biomethane')total=Number(annual.volumetric_products?.biomethane?.value||0);
  else if(definition.source==='energy'){
    const key=definition.id==='electricity'?'electricity':definition.id==='heat'?'heating':'cooling';
    const kwh=Number(annual.utilities?.[key]?.value||0);
    total=definition.id==='electricity'?kwh/1000:kwh*0.0036;
  } else {
    const productKey:Record<string,string>={protein:'dry_protein_product',biostimulant:'biostimulant_product',nutrient:'phosphorus_product',ammonium:'ammonium_product',potassium:'potassium_concentrate',nutrient_solids:'nutrient_rich_solids'};
    total=Number(annual.products?.[productKey[definition.id]]?.value||0)/1000;
  }
  const value=total/12;
  const year=Number(String(result.timestamp||'').slice(0,4))||new Date().getFullYear();
  return Array.from({length:12},(_,month)=>({period:`${year}-${String(month+1).padStart(2,'0')}`,value}));
}

function monthlyRows(annual:AnnualSummary|undefined, definition:Definition, result?:SimulationResult) {
  if(annual?.method==='steady_state_annualization'&&result)return steadyMonthlyRows(annual,result,definition);
  const rows=(annual?.chart_data?.[definition.source]||[]).flatMap(row=>{
    const period=String(row.period??row.time_label??'');
    const raw=definition.id==='digestate'
      ? Math.max(0,Number(row.feed_processed_tonnes||0)-Number(row.press_cake_tonnes||0))
      : row[definition.key]??undefined;
    if(!period||typeof raw!=='number')return [];
    return [{period,value:definition.convert?definition.convert(raw):raw}];
  });
  const grouped=new Map<string,number>();
  for(const row of rows){
    if(/^\d{4}-\d{2}$/.test(row.period)){grouped.set(row.period,(grouped.get(row.period)||0)+row.value);continue;}
    const periodEnd=new Date(`${row.period}T12:00:00`);
    const periodStart=new Date(periodEnd);periodStart.setDate(periodStart.getDate()-6);
    const periodDays=(periodEnd.getTime()-periodStart.getTime())/86400000+1;
    for(let cursor=new Date(periodStart);cursor<=periodEnd;cursor.setDate(cursor.getDate()+1)){
      const key=`${cursor.getFullYear()}-${String(cursor.getMonth()+1).padStart(2,'0')}`;
      grouped.set(key,(grouped.get(key)||0)+row.value/periodDays);
    }
  }
  return [...grouped].map(([period,value])=>({period,value})).sort((a,b)=>a.period.localeCompare(b.period));
}

function intervalRows(annual:AnnualSummary|undefined, definition:Definition, result?:SimulationResult) {
  if(annual?.method==='steady_state_annualization'&&result)return steadyMonthlyRows(annual,result,definition);
  const primary=annual?.chart_data?.[definition.source]||[];
  const sourceRows=primary.length?primary:(definition.source==='schedule_timeseries'?(annual?.chart_data?.schedule||[]):[]);
  return sourceRows.flatMap(row=>{
    const period=String(row.period??row.time_label??'');
    const raw=definition.id==='digestate'
      ? Math.max(0,Number(row.feed_processed_tonnes||0)-Number(row.press_cake_tonnes||0))
      : row[definition.key]??undefined;
    if(!period||typeof raw!=='number')return [];
    return [{period,value:definition.convert?definition.convert(raw):raw}];
  }).sort((a,b)=>a.period.localeCompare(b.period));
}

function monthTick(period:string) {
  const parts=period.split('-');
  const month=Number(parts[1]);
  return month>=1&&month<=12?new Intl.DateTimeFormat('en',{month:'short'}).format(new Date(2026,month-1,1)):period;
}

function monthLabel(period:string) {
  const parts=period.split('-');
  const month=Number(parts[1]);
  return month>=1&&month<=12?`${new Intl.DateTimeFormat('en',{month:'long'}).format(new Date(2026,month-1,1))}${parts[0]?` ${parts[0]}`:''}`:period;
}

function intervalLabel(period:string) {
  if(/^\d{4}-\d{2}-\d{2}$/.test(period))return `Week ending ${new Intl.DateTimeFormat('en',{day:'numeric',month:'short',year:'numeric'}).format(new Date(`${period}T12:00:00`))}`;
  return monthLabel(period);
}

function calendarMonthTicks(rows:Array<{period:string}>) {
  const seen=new Set<string>();
  return rows.flatMap(row=>{
    const month=row.period.slice(0,7);
    if(!/^\d{4}-\d{2}$/.test(month)||seen.has(month))return [];
    seen.add(month);
    return [row.period];
  });
}

const numberText=(value:number)=>Number(value).toLocaleString(undefined,{maximumFractionDigits:3});

function SeriesTicks({items,selected,onToggle}:{items:Definition[];selected:string[];onToggle:(id:string)=>void}) {
  return <div className="series-ticks">{items.map(item=><label key={item.id}><input type="checkbox" checked={selected.includes(item.id)} onChange={()=>onToggle(item.id)}/><span>{item.label}</span></label>)}</div>;
}

export default function BaselineTimeSeries({annual,result,nutrientRecovery,embedded=false,juiceFlowRatio=0}:{annual:AnnualSummary|null|undefined;result?:SimulationResult;nutrientRecovery?:string;embedded?:boolean;juiceFlowRatio?:number}) {
  const [enabled,setEnabled]=useState<GraphId[]>(['feed','products','energy']);
  const [feedSelected,setFeedSelected]=useState<FeedId[]>(['available','processed','press_cake','digestate']);
  const [productsSelected,setProductsSelected]=useState<ProductId[]>(['protein','biostimulant','nutrient','ammonium','potassium','nutrient_solids','biomethane']);
  const [energySelected,setEnergySelected]=useState<EnergyId[]>(['electricity','heat','cooling']);
  const supported=annual?.method==='quasi_dynamic_integration'||(annual?.method==='steady_state_annualization'&&Boolean(result));
  const nutrientLabel=nutrientRecovery==='NR2'||nutrientRecovery==='NR4'||nutrientRecovery==='NR7'?'Struvite':nutrientRecovery==='NR5'?'Calcium phosphate':'Phosphorus product';
  const productSeries=useMemo<Definition[]>(()=>[
    {id:'protein',label:'Protein',source:'small_products',key:'protein_tonnes',color:'#9563a7',unit:'t/month'},
    {id:'biostimulant',label:'Biostimulant',source:'small_products',key:'biostimulant_product_tonnes',color:'#63a6a3',unit:'t/month'},
    {id:'nutrient',label:nutrientLabel,source:'small_products',key:'phosphorus_product_tonnes',color:'#d277a3',unit:'t/month'},
    {id:'ammonium',label:'Ammonium product',source:'small_products',key:'ammonium_product_tonnes',color:'#8c9d46',unit:'t/month'},
    {id:'potassium',label:'Potassium concentrate',source:'small_products',key:'potassium_concentrate_tonnes',color:'#52677e',unit:'t/month'},
    {id:'nutrient_solids',label:'Nutrient-rich solids',source:'small_products',key:'nutrient_rich_solids_tonnes',color:'#bc7d55',unit:'t/month'},
    {id:'biomethane',label:'Biomethane',source:'biomethane',key:'biomethane_m3',color:'#307e86',unit:'m³/month'},
  ],[nutrientLabel]);
  const feedChart=useMemo(()=>{
    const selected=feedSeries.filter(item=>feedSelected.includes(item.id as FeedId));
    const rows=new Map<string,Record<string,any>>();
    for(const item of selected){for(const point of intervalRows(annual||undefined,item,result)){
      const target=rows.get(point.period)||{period:point.period};target[item.id]=point.value;rows.set(point.period,target);
    }}
    return {series:selected.filter(item=>[...rows.values()].some(row=>Number(row[item.id])>0)),rows:[...rows.values()].sort((a,b)=>a.period.localeCompare(b.period))};
  },[annual,feedSelected,juiceFlowRatio,result]);
  const productCharts=useMemo(()=>{
    const selected=productSeries.filter(item=>productsSelected.includes(item.id as ProductId));
    const massSeries=selected.filter(item=>item.unit==='t/month');
    const volumeSeries=selected.filter(item=>item.unit==='m³/month');
    const makeRows=(series:Definition[])=>{
      const rows=new Map<string,Record<string,any>>();
      for(const item of series)for(const point of monthlyRows(annual||undefined,item,result)){
        const target=rows.get(point.period)||{period:point.period};target[item.id]=point.value;rows.set(point.period,target);
      }
      return {series:series.filter(item=>[...rows.values()].some(row=>Number(row[item.id])>0)),rows:[...rows.values()].sort((a,b)=>a.period.localeCompare(b.period))};
    };
    return {mass:makeRows(massSeries),volume:makeRows(volumeSeries)};
  },[annual,productSeries,productsSelected,juiceFlowRatio,result]);
  const energyChart=useMemo(()=>{
    const selected=energySeries.filter(item=>energySelected.includes(item.id as EnergyId));
    const rows=new Map<string,Record<string,any>>();
    for(const item of selected){for(const point of monthlyRows(annual||undefined,item,result)){
      const target=rows.get(point.period)||{period:point.period};target[item.id]=point.value;rows.set(point.period,target);
    }}
    return {series:selected.filter(item=>[...rows.values()].some(row=>Number(row[item.id])>0)),rows:[...rows.values()].sort((a,b)=>a.period.localeCompare(b.period))};
  },[annual,energySelected,result]);
  const toggleGraph=(id:GraphId)=>setEnabled(current=>current.includes(id)?current.filter(item=>item!==id):[...current,id]);
  const toggleFeed=(id:FeedId)=>setFeedSelected(current=>current.includes(id)?current.filter(item=>item!==id):[...current,id]);
  const toggleProduct=(id:ProductId)=>setProductsSelected(current=>current.includes(id)?current.filter(item=>item!==id):[...current,id]);
  const toggleEnergy=(id:EnergyId)=>setEnergySelected(current=>current.includes(id)?current.filter(item=>item!==id):[...current,id]);
  const selected= (id:GraphId)=>enabled.includes(id);
  const toggleLabel=(id:GraphId,label:string)=><label className="graph-toggle" key={id}><input type="checkbox" checked={selected(id)} onChange={()=>toggleGraph(id)}/><span>{label}</span></label>;

  // Weekly model steps are integrated into calendar months before plotting.
  const feedUnitLabel='t/month';
  const orderedFeedSeries=[...feedChart.series].sort((a,b)=>({processed:0,available:1,press_cake:2,digestate:3}[a.id]??9)-({processed:0,available:1,press_cake:2,digestate:3}[b.id]??9));
  return <section className={`panel baseline-series${embedded?' embedded':''}`} aria-label="Monthly process graphs">
    <div className="baseline-series-head"><h2>Monthly process performance</h2>{annual?.method==='steady_state_annualization'&&<p className="series-basis">Annualized steady-state monthly mean · seasonality is not simulated</p>}{annual?.method==='quasi_dynamic_integration'&&<p className="series-basis">Seasonal model output · weekly steps integrated by month</p>}<div className="graph-toggles">{toggleLabel('feed','Biomass')}{toggleLabel('products','Products')}{toggleLabel('energy','Energy')}</div></div>
    {!supported?<div className="empty-state"><strong>Series unavailable for this route</strong><span>{annual?.basis||'Run the backend simulation to load real time-series values.'}</span></div>:<div className="baseline-graph-blocks">
      {selected('feed')&&<section className="baseline-graph-block"><div className="baseline-block-head"><h3>Biomass</h3><SeriesTicks items={feedSeries} selected={feedSelected} onToggle={id=>toggleFeed(id as FeedId)}/></div>{feedChart.series.length?<div className="baseline-series-chart" role="img" aria-label="Weekly biomass availability, processed feed, press cake and juice with monthly ticks"><ResponsiveContainer width="100%" height="100%"><LineChart data={feedChart.rows} margin={{top:12,right:22,bottom:8,left:16}}><CartesianGrid stroke="#ded8d0" vertical={false}/><XAxis dataKey="period" ticks={calendarMonthTicks(feedChart.rows)} tick={{fontSize:11}} tickFormatter={monthTick} interval={0}/><YAxis width={62} tick={{fontSize:10}} label={{value:feedUnitLabel,angle:-90,position:'insideLeft',style:{textAnchor:'middle',fill:'#557077',fontSize:10}}}/><Tooltip labelFormatter={intervalLabel} formatter={(value:number,name:string)=>[numberText(value)+' '+feedUnitLabel,name]}/><Legend/>{orderedFeedSeries.map(item=><Line key={item.id} dataKey={item.id} name={item.label} type="linear" stroke={item.color} strokeWidth={item.id==='available'||item.id==='processed'?3:2.5} dot={{r:1.5,strokeWidth:0}} activeDot={{r:4}} connectNulls={false} isAnimationActive={false}/>)}</LineChart></ResponsiveContainer></div>:<div className="empty-state"><strong>No biomass lines selected</strong></div>}</section>}
      {selected('products')&&<section className="baseline-graph-block"><div className="baseline-block-head"><h3>Products</h3><SeriesTicks items={productSeries} selected={productsSelected} onToggle={id=>toggleProduct(id as ProductId)}/></div>{productCharts.mass.series.length||productCharts.volume.series.length?<div className="product-combined-charts">{productCharts.mass.series.length>0&&<article className="baseline-series-plot"><h3>Product mass</h3><div className="baseline-series-chart" role="img" aria-label="Monthly mass production by product"><ResponsiveContainer width="100%" height="100%"><LineChart data={productCharts.mass.rows} margin={{top:12,right:22,bottom:8,left:16}}><CartesianGrid stroke="#ded8d0" vertical={false}/><XAxis dataKey="period" tick={{fontSize:11}} tickFormatter={monthTick} interval={0}/><YAxis width={62} tick={{fontSize:10}} label={{value:'t/month',angle:-90,position:'insideLeft',style:{textAnchor:'middle',fill:'#557077',fontSize:10}}}/><Tooltip labelFormatter={monthLabel} formatter={(value:number,name:string)=>[numberText(value)+' t',name]}/><Legend/>{productCharts.mass.series.map(item=><Line key={item.id} dataKey={item.id} name={item.label} type="monotone" stroke={item.color} strokeWidth={2.5} dot={false} connectNulls={false} isAnimationActive={false}/>)}</LineChart></ResponsiveContainer></div></article>}{productCharts.volume.series.length>0&&<article className="baseline-series-plot"><h3>Biomethane</h3><div className="baseline-series-chart" role="img" aria-label="Monthly biomethane production"><ResponsiveContainer width="100%" height="100%"><LineChart data={productCharts.volume.rows} margin={{top:12,right:22,bottom:8,left:16}}><CartesianGrid stroke="#ded8d0" vertical={false}/><XAxis dataKey="period" tick={{fontSize:11}} tickFormatter={monthTick} interval={0}/><YAxis width={72} tick={{fontSize:10}} label={{value:'m³/month',angle:-90,position:'insideLeft',style:{textAnchor:'middle',fill:'#557077',fontSize:10}}}/><Tooltip labelFormatter={monthLabel} formatter={(value:number,name:string)=>[numberText(value)+' m³',name]}/><Legend/>{productCharts.volume.series.map(item=><Line key={item.id} dataKey={item.id} name={item.label} type="monotone" stroke={item.color} strokeWidth={2.5} dot={false} connectNulls={false} isAnimationActive={false}/>)}</LineChart></ResponsiveContainer></div></article>}</div>:<div className="empty-state"><strong>No product lines selected</strong></div>}</section>}
      {selected('energy')&&<section className="baseline-graph-block"><div className="baseline-block-head"><h3>Energy · MWh/month</h3><SeriesTicks items={energySeries} selected={energySelected} onToggle={id=>toggleEnergy(id as EnergyId)}/></div>{energyChart.series.length?<div className="baseline-series-chart" role="img" aria-label="Electricity, heat and cooling demand, megawatt-hours per month"><ResponsiveContainer width="100%" height="100%"><LineChart data={energyChart.rows} margin={{top:12,right:22,bottom:8,left:8}}><CartesianGrid stroke="#ded8d0" vertical={false}/><XAxis dataKey="period" tick={{fontSize:11}} tickFormatter={monthTick} interval={0}/><YAxis tick={{fontSize:10}}/><Tooltip labelFormatter={monthLabel} formatter={(value:number,name:string)=>[numberText(value)+' MWh',name]}/><Legend/>{energyChart.series.map(item=><Line key={item.id} dataKey={item.id} name={item.label} type="monotone" stroke={item.color} strokeWidth={2.5} dot={false} connectNulls={false} isAnimationActive={false}/>)}</LineChart></ResponsiveContainer></div>:<div className="empty-state"><strong>No energy lines selected</strong></div>}</section>}
    </div>}
  </section>;
}
