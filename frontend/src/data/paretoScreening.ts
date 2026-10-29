/** Seeded, bounded screening model. Not the empirical BioSTEAM model or complete LCA. */
import reference from './paretoReference.json';
export type Range={low:number;high:number;unit:string;status:string;source:string};
export type Ranges=Record<string,Range>;
const assumption='Explicit screening assumption; not calibrated';
const price=(name:keyof typeof reference.prices,divisor=1):Range=>{const p=reference.prices[name];return {low:p.low/divisor,high:p.high/divisor,unit:divisor===1000?'EUR/kg':p.unit,status:p.status,source:p.source};};
export const defaultRanges:Ranges={
  proteinPrice:price('Protein product',1000),gasPrice:price('Biomethane'),ammoniumPrice:price('Ammonium product',1000),phosphorusPrice:price('Phosphorus/struvite product',1000),solidsPrice:price('Nutrient-rich solids',1000),
  electricityPrice:{low:.1991*.8,high:.1991*1.2,unit:'EUR/kWh',status:'Register tariff ±20% screening sensitivity',source:'TEA-036'},
  heatPrice:{low:.0793*.8,high:.0793*1.2,unit:'EUR/kWh useful heat',status:'Register delivered-heat proxy ±20%',source:'TEA-038'},
  labourRate:{low:47.9*.85,high:47.9*1.15,unit:'EUR/paid hour',status:'Register rate ±15% assumed range',source:'TEA-029'},
  logisticsRate:{low:10.77*.8,high:10.77*1.2,unit:'EUR/t wet feed',status:'Register haulage proxy ±20%',source:'TEA-032'},
  capitalMultiplier:{low:.7,high:1.3,unit:'× reference equipment cost',status:assumption,source:'Cost-register anchors; ±30% assumed uncertainty'},
  scaleExponent:{low:.6,high:.85,unit:'capacity scaling exponent',status:'Assumed envelope around register scaling exponents',source:'tea_cost_register.csv'},
  staffingExponent:{low:.5,high:.8,unit:'staffing scaling exponent',status:assumption,source:'N=max(2,ceil(Nfull × fraction^exponent × route complexity))'},
  proteinYield:{low:.8,high:1.2,unit:'× reference protein yield',status:assumption,source:'Saved empirical baseline; ±20% assumed'},
  methaneYield:{low:.8,high:1.2,unit:'× reference methane yield',status:assumption,source:'Saved empirical baseline; ±20% assumed'},
  nutrientYield:{low:.8,high:1.2,unit:'× reference nutrient product yield',status:assumption,source:'Saved empirical baseline; ±20% assumed'},
  utilityMultiplier:{low:.8,high:1.2,unit:'× included process utilities',status:assumption,source:'Route utility shares and method effects are engineering assumptions'},
  gridFactor:{low:.15,high:.3,unit:'kg CO₂e/kWh',status:'Assumed range around existing 0.20 NL electricity proxy',source:'Expanded process register; boundary unverified'},
  heatFactor:{low:.16,high:.25,unit:'kg CO₂e/kWh useful heat',status:assumption,source:'Illustrative delivered-heat footprint'},
  gasDisplacement:{low:1.8,high:2.3,unit:'kg CO₂e/Nm³ CH₄ displaced',status:assumption,source:'Fossil-gas substitution counterfactual; market eligibility unverified'},
  methaneLeak:{low:.005,high:.03,unit:'fraction raw CH₄',status:assumption,source:'Tracked + untracked leakage scenario; not measured'},
  transportFactor:{low:1,high:5,unit:'kg CO₂e/t wet feed',status:assumption,source:'Transport activity/vehicle evidence missing'},
  consumablesCost:{low:1,high:5,unit:'EUR/t active recovery feed',status:assumption,source:'Placeholder reagent/adsorbent allowance, not measured consumption'},
};
export type Routes={pef:boolean;protein:'Bypass'|'Acid'|'Heat'|'Acid + heat';digestion:'Bypass'|'Mesophilic'|'Thermophilic';gas:'No product · flare'|'Water scrubbing'|'Membrane'|'PSA';fertilizer:'Bypass'|'Separation'|'Phosphorus'|'Ammonia'|'Combined N/P'};
export type Settings={availableTonnes:number;hours:number;fullScalePeople:number;maxFlowKgH:number;years:number;discount:number};
export const defaultSettings:Settings={availableTonnes:30000,hours:5160,fullScalePeople:5,maxFlowKgH:3000,years:20,discount:.08};
export type Point={id:string;fraction:number;feedTonnes:number;flowKgH:number;routes:Routes;assumptions:Record<string,number>;capital:number;people:number;revenue:number;opex:number;capitalCharge:number;operatingProfit:number;profit:number;burden:number;credit:number;offset:number;proteinKg:number;methaneNm3:number;fertilizerKg:number;electricityKwh:number;heatKwh:number;residualKg:number;feasible:boolean;reasons:string[];pareto:boolean};
export function seededRandom(seed:number){let state=seed>>>0;return()=>{state+=0x6D2B79F5;let t=state;t=Math.imul(t^(t>>>15),t|1);t^=t+Math.imul(t^(t>>>7),t|61);return((t^(t>>>14))>>>0)/4294967296;};}
export function validateInputs(seed:number,ranges:Ranges,settings:Settings){
  if(!Number.isSafeInteger(seed)||seed<0||seed>4294967295)throw Error('Seed must be an integer from 0 to 4294967295.');
  for(const key of Object.keys(defaultRanges)){const r=ranges[key];if(!r||![r.low,r.high].every(Number.isFinite)||r.low<0||r.high<r.low)throw Error(`${key}: use finite nonnegative low ≤ high.`);}
  for(const key of ['scaleExponent','staffingExponent','methaneLeak'])if(ranges[key].high>1)throw Error(`${key}: upper bound must be ≤1.`);
  if(!Object.values(settings).every(Number.isFinite)||settings.availableTonnes<=0||settings.hours<=0||settings.hours>8760||!Number.isInteger(settings.fullScalePeople)||settings.fullScalePeople<2||settings.maxFlowKgH<=0||!Number.isInteger(settings.years)||settings.years<1||settings.years>60||settings.discount<0||settings.discount>1)throw Error('Check plant basis: positive feed/capacity, hours ≤8760, ≥2 staff, 1–60 years and 0–100% discount.');
}
export function evaluateCandidate(routes:Routes,fraction:number,a:Record<string,number>,s:Settings,id='candidate'):Point {
  const tonnes=s.availableTonnes*fraction,flow=tonnes*1000/s.hours,ratio=flow/reference.referenceFlowKgH;
  const protein=routes.protein!=='Bypass',ad=routes.digestion!=='Bypass',gas=ad&&routes.gas!=='No product · flare',fert=ad&&routes.fertilizer!=='Bypass';
  const proteinFactor=({Bypass:0,Acid:.85,Heat:.95,'Acid + heat':1}[routes.protein])*(routes.pef?1:.9);
  const gasRecovery=({'No product · flare':0,'Water scrubbing':.94,Membrane:.96,PSA:.95}[routes.gas]);
  const proteinKg=reference.productsKg.dry_protein_product/reference.annualFeedTonnes*tonnes*proteinFactor*a.proteinYield;
  const rawMethaneKg=ad?reference.rawMethaneKg/reference.annualFeedTonnes*tonnes*a.methaneYield*(routes.digestion==='Thermophilic'?1.08:1)*(1+.12*(1-proteinFactor)):0;
  const methaneNm3=rawMethaneKg/16.04246*22.414*gasRecovery*(1-a.methaneLeak);
  const nitrogen=fert&&['Ammonia','Combined N/P'].includes(routes.fertilizer)?reference.productsKg.ammonium_product/reference.annualFeedTonnes*tonnes*a.nutrientYield:0;
  const phosphorus=fert&&['Phosphorus','Combined N/P'].includes(routes.fertilizer)?reference.productsKg.phosphorus_product/reference.annualFeedTonnes*tonnes*a.nutrientYield:0;
  const solids=fert?reference.productsKg.nutrient_rich_solids/reference.annualFeedTonnes*tonnes:0;
  const base=reference.capital as Record<string,{eur:number;exponent:number;name:string}>;
  const ids=['TEA-001','TEA-003','TEA-004',...(routes.pef?['TEA-005']:[]),...(protein?['TEA-008','TEA-009']:[]),...(ad?['TEA-013','TEA-015']:[]),...(gas?['TEA-017-WATER_SCRUBBING']:[]),...(fert?['TEA-019']:[]),...(nitrogen>0?['TEA-020']:[]),...(phosphorus>0?['TEA-022']:[])];
  const gasCapex=routes.gas==='Membrane'?1.15:routes.gas==='PSA'?1.25:1;
  const methodCapex=routes.protein==='Heat'?.9:routes.protein==='Acid'?.85:1;
  const capital=ids.reduce((sum,key)=>{const method=key==='TEA-017-WATER_SCRUBBING'?gasCapex:key==='TEA-008'?methodCapex:key==='TEA-013'&&routes.digestion==='Thermophilic'?1.15:1;
    // A 15% fixed share prevents all equipment cost disappearing at tiny scale.
    return sum+base[key].eur*a.capitalMultiplier*(.15+.85*ratio**((base[key].exponent+a.scaleExponent)/2))*method;},0);
  const complexity=.6+(routes.pef?.05:0)+(protein?.15:0)+(ad?.1:0)+(fert?.1:0);
  const people=Math.max(2,Math.ceil(s.fullScalePeople*fraction**a.staffingExponent*complexity));
  // Utility shares close to the reference total for the complete reference chain.
  const eShare=.2+(routes.pef?.15:0)+(protein?.2:0)+(ad?.15:0)+(gas?.1*(routes.gas==='PSA'?1.2:routes.gas==='Membrane'?.9:1):0)+(fert?.2:0);
  const hShare=(protein?.55*(routes.protein==='Acid'?.65:1):0)+(ad?.2*(routes.digestion==='Thermophilic'?1.35:1):0)+(fert?.25:0);
  const electricityKwh=reference.electricityKwh/reference.annualFeedTonnes*tonnes*eShare*a.utilityMultiplier;
  const heatKwh=reference.heatKwh/reference.annualFeedTonnes*tonnes*hShare*a.utilityMultiplier;
  // Gas sales use methane LHV (9.94 kWh/Nm3), not compressed product m3.
  const revenue=proteinKg*a.proteinPrice+methaneNm3*9.94/1000*a.gasPrice+nitrogen*a.ammoniumPrice+phosphorus*a.phosphorusPrice+solids*a.solidsPrice;
  const opex=people*1500*a.labourRate+tonnes*a.logisticsRate+electricityKwh*a.electricityPrice+heatKwh*a.heatPrice+.02*capital+tonnes*a.consumablesCost*((protein?1:0)+(gas?.25:0)+(fert?1:0));
  const recovery=s.discount===0?1/s.years:s.discount/(1-(1+s.discount)**-s.years),capitalCharge=capital*recovery;
  const emittedMethane=ad?(gas?rawMethaneKg*(a.methaneLeak+(1-a.methaneLeak)*(1-gasRecovery)):rawMethaneKg*(a.methaneLeak+(1-a.methaneLeak)*.02)):0;
  const burden=electricityKwh*a.gridFactor+heatKwh*a.heatFactor+emittedMethane*27+tonnes*a.transportFactor;
  const credit=methaneNm3*a.gasDisplacement;
  const residualKg=tonnes*1000-proteinKg-rawMethaneKg-nitrogen-phosphorus-solids;
  const reasons:string[]=[];
  if(fraction<.1||fraction>.5)reasons.push('Valorization outside 10–50%.');
  if(!ad&&(routes.gas!=='No product · flare'||routes.fertilizer!=='Bypass'))reasons.push('Gas/fertilizer route requires AD in this screening topology.');
  if(flow>s.maxFlowKgH)reasons.push('Required throughput exceeds available plant capacity.');
  if(proteinKg>tonnes*1000*.35||rawMethaneKg>tonnes*1000*.35||residualKg<0)reasons.push('Product/export quantities exceed feed envelope.');
  if(![capital,revenue,opex,burden,credit,flow].every(Number.isFinite))reasons.push('Nonfinite calculation.');
  return {id,fraction,feedTonnes:tonnes,flowKgH:flow,routes,assumptions:a,capital,people,revenue,opex,capitalCharge,operatingProfit:revenue-opex,profit:revenue-opex-capitalCharge,burden,credit,offset:(credit-burden)/1000,proteinKg,methaneNm3,fertilizerKg:nitrogen+phosphorus+solids,electricityKwh,heatKwh,residualKg,feasible:!reasons.length,reasons,pareto:false};
}
export function markPareto(points:Point[]):Point[]{
  // Maximize both axes. Equal objective pairs are all retained; same-x lower-y points are dominated.
  const sorted=points.filter(p=>p.feasible).sort((a,b)=>b.profit-a.profit||b.offset-a.offset);
  let best=-Infinity,lastX=NaN,groupBest=-Infinity;
  const front=new Set<string>();
  for(const p of sorted){if(p.profit!==lastX){best=Math.max(best,groupBest);groupBest=-Infinity;lastX=p.profit;}if(p.offset>best&&p.offset>=groupBest)front.add(p.id);groupBest=Math.max(groupBest,p.offset);}
  return points.map(p=>({...p,pareto:front.has(p.id)}));
}
export function generateScreeningBatch(seed=42,ranges:Ranges=defaultRanges,settings:Settings=defaultSettings){
  validateInputs(seed,ranges,settings);const rng=seededRandom(seed),pick=<T,>(items:T[])=>items[Math.floor(rng()*items.length)];
  const fractions=Array.from({length:2000},(_,i)=>.1+.4*(i+rng())/2000);
  for(let i=fractions.length-1;i>0;i--){const j=Math.floor(rng()*(i+1));[fractions[i],fractions[j]]=[fractions[j],fractions[i]];}
  const points=fractions.map((fraction,i)=>{const digestion=pick<Routes['digestion']>(['Bypass','Mesophilic','Thermophilic']);const routes:Routes={pef:rng()<.5,protein:pick<Routes['protein']>(['Bypass','Acid','Heat','Acid + heat']),digestion,gas:digestion==='Bypass'?'No product · flare':pick<Routes['gas']>(['No product · flare','Water scrubbing','Membrane','PSA']),fertilizer:digestion==='Bypass'?'Bypass':pick<Routes['fertilizer']>(['Bypass','Separation','Phosphorus','Ammonia','Combined N/P'])};
    const a=Object.fromEntries(Object.entries(ranges).map(([key,r])=>[key,r.low+(r.high-r.low)*rng()]));return evaluateCandidate(routes,fraction,a,settings,`S-${seed}-${String(i+1).padStart(4,'0')}`);});
  return {seed,settings:{...settings},ranges:structuredClone(ranges),points:markPareto(points),method:'2000 stratified biomass fractions; seeded categorical routes and independent uniform uncertainty draws',validation:'Screening topology/capacity/product-envelope checks only; not 2000 BioSTEAM simulations or validated feasible plants',referenceRun:reference.sourceRun};
}
