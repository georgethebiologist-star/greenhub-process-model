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
  return <section className="input-studio panel">
    <div className="panel-title"><span className="title-icon"><SlidersHorizontal size={17}/></span><div><h3>Feed characterization context</h3><p>The master workbook remains authoritative. These values are visible planning references and do not overwrite empirical chemistry.</p></div></div>
    <div className="input-section"><div className="eyebrow">Feed composition <span className="badge provisional">planning only</span></div><div className="input-grid">
      {field('moisturePct','Moisture','% wet basis','Shown for review; the workbook feed profile remains authoritative.',100)}
      {field('proteinPct','Protein','% dry matter','Shown for review; not sent to the scientific model yet.',100)}
      {field('phosphorusPct','Total phosphorus','% wet basis','Shown for review; not sent to the scientific model yet.',100)}
    </div></div>
    <div className="input-summary"><div><strong>Selected pathway</strong><span>{scenario.feed_front_end ? 'Feed preparation, digestion and nutrient recovery configured' : 'Choose a process pathway above'}</span></div><div><strong>Input status</strong><span>Operating schedule active above · composition shown for context</span></div><button className="run-button" onClick={onRun}>Run annual plan</button></div>
  </section>;
}
