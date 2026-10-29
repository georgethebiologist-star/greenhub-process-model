// Lightweight checks using the existing React/esbuild dependencies; no new test stack.
import assert from 'node:assert/strict';
import fs from 'node:fs';
import Module, {createRequire} from 'node:module';
import path from 'node:path';
import {buildSync} from 'esbuild';
import React from 'react';
import {renderToStaticMarkup} from 'react-dom/server';

const code=buildSync({stdin:{contents:`export {DecisionResults} from './src/components/DecisionSupport'; export {default as DecisionOverview} from './src/components/DecisionOverview'; export {previewFinance,baselineSnapshot} from './src/data/decisionPreview'; export {generateScreeningBatch,evaluateCandidate,markPareto,defaultRanges,defaultSettings} from './src/data/paretoScreening'; export {buildDecisionConfiguration} from './src/data/decisionSupport';`,resolveDir:process.cwd()},bundle:true,write:false,platform:'node',format:'cjs',packages:'external',loader:{'.css':'empty'},define:{'import.meta.env':'{}'}}).outputFiles[0].text;
const compiled=new Module(path.resolve('scripts/decision-check.cjs'));
compiled.filename=path.resolve('scripts/decision-check.cjs');
compiled.require=createRequire(import.meta.url);compiled._compile(code,compiled.filename);
const {DecisionResults,DecisionOverview,previewFinance,baselineSnapshot,buildDecisionConfiguration}=compiled.exports;
const report=JSON.parse(fs.readFileSync('../Greenhub/results/decision_support/static.json','utf8'));
const html=renderToStaticMarkup(React.createElement(DecisionResults,{report}));
for(const label of ['Not a validated simulation','validated_simulation_ready = false','Partial direct CAPEX','Operating profit','Climate inventory','Source status','Incomplete'])assert.ok(html.includes(label),label);
assert.ok(html.includes('ds-chart'),'Existing charts render their responsive containers with real default data.');
assert.ok(html.includes(report.tea.source_traceability[0].cost_id),'Traceable cost ID');
const config=buildDecisionConfiguration(report.configuration,{model:'quasi_dynamic',feedRate:1234,capacity:1500,days:5,hours:16,start:'2026-04-15',end:'2026-11-15',peak:'2026-07-31',timeStep:'monthly',available:30000,target:20000,collection:0.8,storageEnabled:true,storageDays:2,aerobic:0.4,activity:1,temperature:20,customFeed:false,screeningLca:false});
assert.equal(config.simulation.wet_feed_rate_kg_hr,1234);
assert.equal(config.simulation.biomass_schedule.annual_processed_biomass_tonnes,20000);
assert.equal(config.simulation.storage_conditions.aerobic_fraction,0.4);
assert.equal(config.simulation.start_date,'2026-01-01');
assert.equal(config.simulation.storage_conditions.allow_assumptions,true);
assert.equal(config.use_screening_lca_factors,false,'Screening LCA proxy must remain off by default.');
const screeningConfig=buildDecisionConfiguration(report.configuration,{model:'steady_state',feedRate:1000,capacity:1000,days:7,hours:24,start:'2026-04-15',end:'2026-11-15',peak:'2026-07-31',timeStep:'monthly',available:30000,target:30000,collection:1,storageEnabled:false,storageDays:0,aerobic:0,activity:1,temperature:20,customFeed:false,screeningLca:true});
assert.equal(screeningConfig.use_screening_lca_factors,true,'Screening LCA checkbox must activate the opt-in flag.');
assert.equal(report.configuration.simulation.wet_feed_rate_kg_hr,1000,'Request construction must not mutate saved result.');
console.log('Decision support rendering, evidence, readiness and request payload checks passed.');

// Financial preview mathematics and offline rendering must remain independent of the API.
const previewHtml=renderToStaticMarkup(React.createElement(DecisionOverview));
for(const label of ['BASELINE PREVIEW','TEA &amp; LCA at a glance','IRR preview','No IRR','Not reached','Climate impact contributors','Complete LCA result','Blocked'])assert.ok(previewHtml.includes(label),label);
assert.ok(Math.abs(baselineSnapshot.costs.reduce((s,r)=>s+(r.value??0),0)-baselineSnapshot.opex)<0.01);
assert.ok(Math.abs(baselineSnapshot.revenues.reduce((s,r)=>s+(r.value??0),0)-baselineSnapshot.revenue)<0.01);
const profitable=previewFinance(100,60,2,0);
assert.equal(profitable.npv,20);
assert.ok(Math.abs(profitable.irr-((60+Math.sqrt(27600))/200-1))<1e-9);
assert.ok(Math.abs(profitable.payback-100/60)<1e-9);
assert.ok(Math.abs(profitable.discountedPayback-100/60)<1e-9);
assert.equal(previewFinance(100,-10,20,0.08).irr,null,'Negative-only cash flows have no IRR.');
assert.equal(previewFinance(100,-10,20,0.08).payback,null);
assert.equal(previewFinance(100,10,2,0).payback,null,'No payback inside a short horizon.');
assert.equal(previewFinance(100,0,20,0).irr,null);
assert.equal(previewFinance(100,60,2,0).cashflows.at(-1).cumulative,20);
console.log('Offline baseline, contribution sums, IRR, NPV and payback checks passed.');

const {generateScreeningBatch,evaluateCandidate,markPareto,defaultRanges,defaultSettings}=compiled.exports;
const study=generateScreeningBatch();
assert.equal(study.points.length,2000);
assert.equal(new Set(study.points.map(p=>p.id)).size,2000);
assert.deepEqual(study,generateScreeningBatch(),'Same seed must reproduce all configurations and KPIs.');
assert.notDeepEqual(study.points,generateScreeningBatch(43).points);
assert.ok(study.points.every(p=>p.fraction>=.1&&p.fraction<=.5&&p.people>=2&&Number.isInteger(p.people)));
assert.ok(study.points.some(p=>p.people===2));
assert.ok(study.points.some(p=>p.routes.pef)&&study.points.some(p=>!p.routes.pef));
assert.ok(study.points.some(p=>p.routes.protein==='Bypass')&&study.points.some(p=>p.routes.protein==='Heat'));
assert.ok(study.points.some(p=>p.routes.gas==='PSA')&&study.points.some(p=>p.routes.fertilizer==='Phosphorus'));
assert.ok(study.points.every(p=>p.routes.digestion!=='Bypass'||p.routes.gas==='No product · flare'&&p.routes.fertilizer==='Bypass'));
for(const p of study.points){
 assert.ok(Math.abs(p.profit-(p.revenue-p.opex-p.capitalCharge))<1e-7);
 assert.ok(Math.abs(p.offset-(p.credit-p.burden)/1000)<1e-9);
 for(const [key,r] of Object.entries(defaultRanges))assert.ok(p.assumptions[key]>=r.low&&p.assumptions[key]<=r.high);
}
const brute=study.points.filter(p=>p.feasible&&!study.points.some(q=>q.feasible&&q.profit>=p.profit&&q.offset>=p.offset&&(q.profit>p.profit||q.offset>p.offset))).map(p=>p.id).sort();
assert.deepEqual(study.points.filter(p=>p.pareto).map(p=>p.id).sort(),brute,'Front must maximize both axes.');
const same=study.points.find(p=>p.routes.digestion!=='Bypass');
const small=evaluateCandidate(same.routes,.1,same.assumptions,defaultSettings);
const large=evaluateCandidate(same.routes,.5,same.assumptions,defaultSettings);
assert.ok(small.capital<large.capital,'Lower volume must reduce matched equipment CAPEX.');
assert.ok(small.people<=large.people&&small.people>=2,'Staff must scale down with a floor.');
const skip=evaluateCandidate({...same.routes,pef:false,protein:'Bypass',digestion:'Bypass',gas:'No product · flare',fertilizer:'Bypass'},.3,same.assumptions,defaultSettings);
assert.equal(skip.proteinKg,0);assert.equal(skip.methaneNm3,0);assert.equal(skip.fertilizerKg,0);assert.equal(skip.credit,0);
assert.ok(evaluateCandidate(same.routes,.5,same.assumptions,{...defaultSettings,maxFlowKgH:100}).reasons.some(r=>r.includes('capacity')));
assert.throws(()=>generateScreeningBatch(1,{...defaultRanges,proteinPrice:{...defaultRanges.proteinPrice,low:3,high:2}}),/low/);
assert.throws(()=>generateScreeningBatch(1,defaultRanges,{...defaultSettings,fullScalePeople:1}),/staff/);
const ties=markPareto([{id:'a',profit:1,offset:2,feasible:true},{id:'b',profit:1,offset:2,feasible:true},{id:'c',profit:1,offset:1,feasible:true},{id:'d',profit:100,offset:100,feasible:false}]);
assert.deepEqual(ties.filter(p=>p.pareto).map(p=>p.id),['a','b']);
console.log(`2000-scenario determinism, bounds, flow/staff scaling, bypasses and Pareto checks passed (${brute.length} front points).`);

// Sales corrections must propagate to baseline previews and every sampled case.
assert.ok(Math.abs(baselineSnapshot.revenues.find(r=>r.name==='biomethane').value-10859.974934446958)<.01);
assert.equal(baselineSnapshot.productSales.find(r=>r.product_id==='phosphorus_product').quantity,0);
assert.ok(Math.abs(baselineSnapshot.productSales.find(r=>r.product_id==='ammonium_product').quantity-24759.733901753727)<.01);
assert.equal(defaultRanges.orthophosphateShare.high,0,'Unknown speciation must not become recovered struvite.');
assert.ok(study.points.every(p=>p.struviteKg===0));
const hypotheticalAssumptions={...same.assumptions,orthophosphateShare:1};
const fullN=evaluateCandidate({...same.routes,digestion:'Mesophilic',fertilizer:'Ammonia'},.3,hypotheticalAssumptions,defaultSettings);
const withP=evaluateCandidate({...same.routes,digestion:'Mesophilic',fertilizer:'Combined N/P'},.3,hypotheticalAssumptions,defaultSettings);
assert.ok(withP.struviteKg>0&&withP.magnesiumReagentKg>0&&withP.struviteHypothetical);
assert.ok(withP.ammoniumSulfateKg<=fullN.ammoniumSulfateKg,'N recovered into struvite cannot be sold again as ammonium sulfate.');
for(const p of study.points.filter(p=>p.methaneNm3>0)){
 const purity=p.routes.gas==='Water scrubbing'?.9437269935:.98;
 assert.ok(Math.abs(p.gasAtmosphericM3-p.methaneNm3/purity*293.15/273.15)<1e-8);
}
console.log('Atmospheric gas sales, dry sulfate, zero actual struvite, conditional P recovery and shared-N checks passed.');
