import React from 'react';
import { Info, SlidersHorizontal } from 'lucide-react';
import type { ScenarioSelection } from '../types';

export type FeedInputs = {
  feedAmountKgh: number;
  operatingDaysPerWeek: number;
  operatingHoursPerDay: number;
  moisturePct: number;
  liquidFractionPct: number;
  proteinPct: number;
  nitrogenPct: number;
  phosphorusPct: number;
};

export function InputStudio({ feed, setFeed, scenario, onRun }: {
  feed: FeedInputs;
  setFeed: React.Dispatch<React.SetStateAction<FeedInputs>>;
  scenario: ScenarioSelection;
  onRun: () => void;
}) {
  const update = (key: keyof FeedInputs, value: string) => setFeed(current => ({ ...current, [key]: Number(value) }));
  const field = (key: keyof FeedInputs, label: string, unit: string, note: string, max?: number) => (
    <label className="input-card">
      <span title={note}>{label}<Info size={12}/></span>
      <div><input type="number" value={feed[key]} min={0} max={max} onChange={event => update(key, event.target.value)}/><em>{unit}</em></div>
      <small>{note}</small>
    </label>
  );
  const annualHours = Math.min(8760, 365 / 7 * feed.operatingDaysPerWeek * feed.operatingHoursPerDay);

  return <section className="input-studio panel">
    <div className="panel-title"><span className="title-icon"><SlidersHorizontal size={17}/></span><div><h3>Feed and operating plan</h3><p>Green fields change the scientific run. Yellow fields are planning context only.</p></div></div>
    <div className="input-section active-inputs"><div className="eyebrow">Used in this run <span className="badge active">active</span></div><div className="input-grid">
      {field('feedAmountKgh','Target throughput','kg/h','Sets the processing target for every operating period.')}
      {field('operatingDaysPerWeek','Operating days','days/week','Sets the annual operating calendar.',7)}
      {field('operatingHoursPerDay','Daily operating time','hours/day','Sets available production time on each operating day.',24)}
    </div><p className="input-basis">The current plan provides {annualHours.toLocaleString(undefined,{maximumFractionDigits:0})} operating hours per year.</p></div>
    <div className="input-section"><div className="eyebrow">Feed composition <span className="badge provisional">planning only</span></div><div className="input-grid">
      {field('moisturePct','Moisture','% wet basis','Shown for review; the workbook feed profile remains authoritative.',100)}
      {field('proteinPct','Protein','% dry matter','Shown for review; not sent to the scientific model yet.',100)}
      {field('phosphorusPct','Total phosphorus','% wet basis','Shown for review; not sent to the scientific model yet.',100)}
    </div></div>
    <div className="input-summary"><div><strong>Selected pathway</strong><span>{scenario.feed_front_end} · {scenario.anaerobic_digestion} · {scenario.nutrient_recovery}</span></div><div><strong>Input status</strong><span>Schedule active · composition planning only</span></div><button className="run-button" onClick={onRun}>Run annual plan</button></div>
  </section>;
}
