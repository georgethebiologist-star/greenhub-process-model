import baseline from './decisionBaseline.json';
import type {DecisionReport} from './decisionSupport';
export type AnalysisSnapshot = Omit<typeof baseline, 'dryFeedTonnes'|'electricityKwh'|'heatKwh'|'methaneKg'> & {dryFeedTonnes:number|null;electricityKwh:number|null;heatKwh:number|null;methaneKg:number|null};
export const baselineSnapshot:AnalysisSnapshot=baseline;
export function snapshotFromReport(report:DecisionReport):AnalysisSnapshot {
  const t=report.tea.totals, inventory=report.lca.inventory;
  return {...baseline,label:'Selected run screening preview',sourceRun:report.run_id,sourceCommit:'',scenario:report.scenario_ids,
    feedTonnes:report.annual.feed_processed.value/1000,
    dryFeedTonnes:report.lca.project_basis.annual_dry_feed_kg==null?null:report.lca.project_basis.annual_dry_feed_kg/1000,
    people:report.tea.project_basis?.staffing_people??5,paidHoursPerPerson:report.tea.project_basis?.paid_hours_per_person??1500,
    capital:t.screening_capital_basis_eur??t.total_installed_capex_eur??t.partial_direct_capex_eur,
    revenue:t.annual_revenue_eur,opex:t.annual_opex_eur,
    costs:report.tea.opex_lines.map((r:any)=>({name:r.equipment_or_cost_item,value:r.annual_cost_eur??null})),
    revenues:report.tea.revenue_lines.map((r:any)=>({name:r.equipment_or_cost_item,value:r.annual_revenue_eur??null})),
    capitalLines:report.tea.capex_lines.map((r:any)=>({name:r.equipment_or_cost_item,value:r.installed_cost_eur??r.direct_cost_eur??null})),
    electricityKwh:inventory.find((r:any)=>r.flow_id==='electricity')?.quantity??null,
    heatKwh:inventory.find((r:any)=>r.flow_id==='heat')?.quantity??null,
    methaneKg:!inventory.some((r:any)=>r.flow_id.endsWith('_Methane'))||inventory.some((r:any)=>r.flow_id.endsWith('_Methane')&&r.quantity==null)?null:inventory.filter((r:any)=>r.flow_id.endsWith('_Methane')).reduce((s:number,r:any)=>s+r.quantity,0),
    teaMissing:report.tea.missing_inputs,lcaMissing:report.lca.missing_inputs};
}
export function previewFinance(capital:number, annualCash:number, years:number, rate:number) {
  const cashflows=Array.from({length:years+1},(_,year)=>({year,cash:year===0?-capital:annualCash,
    cumulative:-capital+annualCash*year,discounted:-capital+Array.from({length:year},(_,i)=>annualCash/(1+rate)**(i+1)).reduce((a,b)=>a+b,0)}));
  const npvAt=(r:number)=>-capital+Array.from({length:years},(_,i)=>annualCash/(1+r)**(i+1)).reduce((a,b)=>a+b,0);
  let irr:number|null=null;
  if(capital>0&&annualCash>0) {
    let lo=-0.999,hi=1;
    while(npvAt(hi)>0&&hi<1e6)hi*=2;
    if(npvAt(lo)>0&&npvAt(hi)<=0){for(let i=0;i<120;i++){const mid=(lo+hi)/2;if(npvAt(mid)>0)lo=mid;else hi=mid;}irr=(lo+hi)/2;}
  }
  const crossing=cashflows.findIndex(row=>row.discounted>=0);
  const discountedPayback=crossing>0?crossing-1+(-cashflows[crossing-1].discounted)/(cashflows[crossing].discounted-cashflows[crossing-1].discounted):null;
  return {cashflows,npv:npvAt(rate),irr,payback:capital>0&&annualCash>0&&capital/annualCash<=years?capital/annualCash:null,discountedPayback};
}
