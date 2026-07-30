import React from 'react';
import { Info, SlidersHorizontal } from 'lucide-react';
import type { ScenarioSelection } from '../types';

export type FeedInputs = { feedAmountKgh: number; moisturePct: number; liquidFractionPct: number; proteinPct: number; nitrogenPct: number; phosphorusPct: number };

export function InputStudio({ feed, setFeed, scenario, onRun }: { feed: FeedInputs; setFeed: React.Dispatch<React.SetStateAction<FeedInputs>>; scenario: ScenarioSelection; onRun: () => void }) {
  const update = (key: keyof FeedInputs, value: string) => setFeed(current => ({ ...current, [key]: Number(value) }));
  const field = (key: keyof FeedInputs, label: string, unit: string, note: string) => (
    <label className="input-card">
      <span title={note}>{label}<Info size={12}/></span>
      <div><input type="number" value={feed[key]} min={0} onChange={event => update(key, event.target.value)}/><em>{unit}</em></div>
      <small>{note}</small>
    </label>
  );
  return <section className="input-studio panel"><div className="panel-title"><span className="title-icon"><SlidersHorizontal size={17}/></span><div><h3>Feed & operating inputs</h3><p>Active backend controls are separated from provisional composition fields.</p></div></div><div className="input-section"><div className="eyebrow">Basic feed basis</div><div className="input-grid">{field('feedAmountKgh','Target throughput','kg/h','Active backend field: operating_schedule.target_throughput_kg_hr.')}{field('moisturePct','Moisture','% wet basis','Dataset/context value; direct steady-state override is not active yet.')}{field('liquidFractionPct','Liquid fraction','% feed','Future-ready field; not submitted to the current backend contract.')}</div></div><div className="input-section"><div className="eyebrow">Composition inputs <span className="badge provisional">provisional / future-ready</span></div><div className="input-grid">{field('proteinPct','Protein','% dry matter','Captured for future feed characterization; not active in the present request.')}{field('nitrogenPct','Total nitrogen','% wet basis','Informational until a backend feed profile is selected.')}{field('phosphorusPct','Total phosphorus','% wet basis','Informational until a backend feed profile is selected.')}</div></div><div className="input-summary"><div><strong>Run basis</strong><span>{scenario.feed_front_end} · {scenario.anaerobic_digestion} · {scenario.nutrient_recovery}</span></div><div><strong>Input governance</strong><span>Throughput active · composition fields provisional</span></div><button className="run-button" onClick={onRun}>Run with these inputs</button></div></section>;
}
