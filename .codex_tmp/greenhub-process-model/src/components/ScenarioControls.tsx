import React from 'react';
import { NutrientScenarioId, ProcessOrder, ScenarioSelection } from '../types';
import { Sparkles, ArrowRight, Settings2 } from 'lucide-react';

interface ScenarioControlsProps {
  scenarios: ScenarioSelection;
  onChange: (scenarios: ScenarioSelection) => void;
}

export const ScenarioControls: React.FC<ScenarioControlsProps> = ({ scenarios, onChange }) => {
  const scenarioOptions: Array<{ id: NutrientScenarioId; title: string; desc: string }> = [
    { id: 'NR0', title: 'NR0: No Recovery', desc: 'Digestate inventory only; no targeted chemical or nutrient extraction' },
    { id: 'NR1', title: 'NR1: Solid Separation', desc: 'Screw press / decanter separation into cake and liquid fraction' },
    { id: 'NR2', title: 'NR2: Struvite Only', desc: 'Precipitation of MgNH4PO4·6H2O from decanter liquor' },
    { id: 'NR3', title: 'NR3: N-Stripping Only', desc: 'Air stripping column & H2SO4 acid absorption for (NH4)2SO4 product' },
    { id: 'NR4', title: 'NR4: Struvite + N-Salt', desc: 'Baseline combined Phosphorus and Nitrogen recovery system' },
    { id: 'NR5', title: 'NR5: Calcium Phosphate', desc: 'Ca(OH)2 addition alternative for calcium phosphate fertilizer' },
    { id: 'NR6', title: 'NR6: Zeolite Ion Exchange', desc: 'Clinoptilolite column ion exchange with NaCl regeneration loop' },
    { id: 'NR7', title: 'NR7: Full P/N/K Recovery', desc: 'Integrated P/N recovery plus non-selective Potassium concentration' },
  ];

  const processOrders: Array<{ id: ProcessOrder; label: string; desc: string }> = [
    { id: 'A', label: 'Order A (Default)', desc: 'Separation -> Phosphorus -> Nitrogen -> Potassium' },
    { id: 'B', label: 'Order B', desc: 'Separation -> Nitrogen -> Phosphorus -> Potassium' },
    { id: 'C', label: 'Order C', desc: 'Precipitate P from whole digestate -> Separation -> N -> K' },
    { id: 'D', label: 'Order D', desc: 'Separation only (Baseline NR0/NR1 constraint)' },
  ];

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5 mb-6 shadow-sm">
      <div className="flex items-center justify-between mb-4 pb-3 border-b border-slate-800">
        <div className="flex items-center gap-2">
          <Settings2 className="w-5 h-5 text-emerald-400" />
          <h2 className="text-base font-semibold text-white">
            Phase 7 Nutrient Recovery Scenario & Pathway Controller
          </h2>
        </div>
        <span className="text-xs font-mono text-slate-400">
          Selected: <strong className="text-emerald-400">{scenarios.nutrient_recovery}</strong> ({scenarios.process_order})
        </span>
      </div>

      {/* Scenario Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3 mb-5">
        {scenarioOptions.map((opt) => {
          const isSelected = scenarios.nutrient_recovery === opt.id;
          return (
            <button
              key={opt.id}
              onClick={() => onChange({ ...scenarios, nutrient_recovery: opt.id })}
              className={`text-left p-3.5 rounded-xl border transition-all cursor-pointer ${
                isSelected
                  ? 'bg-emerald-500/10 border-emerald-500/60 ring-1 ring-emerald-500/40'
                  : 'bg-slate-950/60 border-slate-800 hover:border-slate-700 text-slate-300'
              }`}
            >
              <div className="flex items-center justify-between mb-1">
                <span className={`text-xs font-bold font-mono ${isSelected ? 'text-emerald-400' : 'text-slate-200'}`}>
                  {opt.id}
                </span>
                {isSelected && <Sparkles className="w-3.5 h-3.5 text-emerald-400" />}
              </div>
              <p className="text-xs font-semibold text-slate-100 mb-1">{opt.title.split(':')[1]}</p>
              <p className="text-[11px] text-slate-400 line-clamp-2 leading-relaxed">{opt.desc}</p>
            </button>
          );
        })}
      </div>

      {/* Process Order Selector */}
      <div className="bg-slate-950/60 border border-slate-800 rounded-xl p-4">
        <label className="text-xs font-semibold text-slate-300 mb-2 block">
          Unit Process Order Sequence:
        </label>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-2">
          {processOrders.map((ord) => {
            const isSelected = scenarios.process_order === ord.id;
            return (
              <button
                key={ord.id}
                onClick={() => onChange({ ...scenarios, process_order: ord.id })}
                className={`p-2.5 rounded-lg border text-left text-xs transition cursor-pointer ${
                  isSelected
                    ? 'bg-emerald-500/15 border-emerald-500/50 text-emerald-300'
                    : 'bg-slate-900 border-slate-800 text-slate-400 hover:text-slate-200'
                }`}
              >
                <div className="font-semibold mb-0.5 text-slate-200">{ord.label}</div>
                <div className="text-[10px] text-slate-400">{ord.desc}</div>
              </button>
            );
          })}
        </div>
      </div>
    </div>
  );
};
