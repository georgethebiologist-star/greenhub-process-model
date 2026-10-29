// Lightweight checks using the existing React/esbuild dependencies; no new test stack.
import assert from 'node:assert/strict';
import fs from 'node:fs';
import Module, {createRequire} from 'node:module';
import path from 'node:path';
import {buildSync} from 'esbuild';
import React from 'react';
import {renderToStaticMarkup} from 'react-dom/server';

const code=buildSync({stdin:{contents:`export {DecisionResults} from './src/components/DecisionSupport'; export {default as DecisionOverview} from './src/components/DecisionOverview'; export {previewFinance,baselineSnapshot} from './src/data/decisionPreview'; export {buildDecisionConfiguration} from './src/data/decisionSupport';`,resolveDir:process.cwd()},bundle:true,write:false,platform:'node',format:'cjs',packages:'external',loader:{'.css':'empty'},define:{'import.meta.env':'{}'}}).outputFiles[0].text;
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
