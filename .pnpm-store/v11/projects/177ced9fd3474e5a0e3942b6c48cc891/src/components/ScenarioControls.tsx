import React, { useState } from 'react';
import { ScenarioSelection, NutrientScenarioId, ProcessOrder } from '../types';
import { Sliders, Sparkles, Layers, Cpu, Flame, Leaf, Droplet, HelpCircle } from 'lucide-react';
import { TooltipInfo } from './TooltipInfo';

interface ScenarioControlsProps {
  scenarios: ScenarioSelection;
  onChange: (scenarios: ScenarioSelection) => void;
  availableScenariosData?: any;
}

export const ScenarioControls: React.FC<ScenarioControlsProps> = ({
  scenarios,
  onChange,
  availableScenariosData
}) => {
  const [activeAreaTab, setActiveAreaTab] = useState<
    'all' | 'front_end' | 'protein_recovery' | 'anaerobic_digestion' | 'biogas_upgrading' | 'nutrient_recovery'
  >('all');

  const updateScenario = (key: keyof ScenarioSelection, value: any) => {
    onChange({ ...scenarios, [key]: value });
  };

  const nrScenarios: Array<{ id: NutrientScenarioId; title: string; desc: string }> = [
    { id: 'NR0', title: 'NR0: No Recovery', desc: 'Digestate inventory only; zero targeted chemical extraction' },
    { id: 'NR1', title: 'NR1: Solid Separation', desc: 'Screw press / decanter separation into cake and liquid' },
    { id: 'NR2', title: 'NR2: Struvite Only', desc: 'Precipitation of MgNH4PO4·6H2O from decanter liquor' },
    { id: 'NR3', title: 'NR3: N-Stripping Only', desc: 'Air stripping & H2SO4 absorption for (NH4)2SO4 fertilizer' },
    { id: 'NR4', title: 'NR4: Struvite + N-Salt', desc: 'Baseline combined Phosphorus and Nitrogen recovery' },
    { id: 'NR5', title: 'NR5: Calcium Phosphate', desc: 'Ca(OH)2 addition alternative for phosphate fertilizer' },
    { id: 'NR6', title: 'NR6: Zeolite Ion Exchange', desc: 'Clinoptilolite column ion exchange with NaCl regeneration' },
    { id: 'NR7', title: 'NR7: Full P/N/K Recovery', desc: 'Integrated P/N recovery plus thermal K-concentration' },
  ];

  const processOrders: Array<{ id: ProcessOrder; label: string; desc: string }> = [
    { id: 'A', label: 'Order A (Default)', desc: 'Separation -> Phosphorus -> Nitrogen -> Potassium' },
    { id: 'B', label: 'Order B', desc: 'Separation -> Nitrogen -> Phosphorus -> Potassium' },
    { id: 'C', label: 'Order C', desc: 'Precipitate P from whole digestate -> Separation -> N -> K' },
    { id: 'D', label: 'Order D', desc: 'Separation only (Baseline NR0/NR1 constraint)' },
  ];

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5 mb-6 shadow-sm">
      <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-3 mb-4 pb-3 border-b border-slate-800">
        <div className="flex items-center gap-2">
          <Sliders className="w-5 h-5 text-emerald-400" />
          <h2 className="text-base font-semibold text-white">
            Integrated Multi-Phase System Configurator
          </h2>
          <TooltipInfo
            title="Multi-Phase System Configurator"
            content="Allows testing mixed process configurations across all 5 bioprocess areas simultaneously. Changes automatically recalculate system mass, energy, COD, and nutrient balances via the BioSTEAM backend model."
          />
        </div>
        <div className="flex items-center gap-1.5 overflow-x-auto text-xs">
          {[
            { id: 'all', label: 'All 5 Phases' },
            { id: 'front_end', label: '1. Front-End' },
            { id: 'protein_recovery', label: '2. Protein' },
            { id: 'anaerobic_digestion', label: '3. AD' },
            { id: 'biogas_upgrading', label: '4. Upgrading' },
            { id: 'nutrient_recovery', label: '5. Nutrient (Phase 7)' },
          ].map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveAreaTab(tab.id as any)}
              className={`px-3 py-1.5 rounded-lg font-medium transition cursor-pointer whitespace-nowrap ${
                activeAreaTab === tab.id
                  ? 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/40 font-semibold'
                  : 'bg-slate-950 text-slate-400 hover:text-slate-200 border border-slate-800'
              }`}
            >
              {tab.label}
            </button>
          ))}
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {/* Phase 1: Front-End Feed */}
        {(activeAreaTab === 'all' || activeAreaTab === 'front_end') && (
          <div className="bg-slate-950/70 border border-slate-800/90 rounded-xl p-4 flex flex-col justify-between">
            <div>
              <div className="flex items-center justify-between mb-2">
                <span className="text-xs font-bold text-emerald-400 flex items-center gap-1.5">
                  <Leaf className="w-3.5 h-3.5" /> 1. Front-End Feed
                </span>
                <span className="text-[10px] bg-slate-800 px-2 py-0.5 rounded-full text-slate-300">
                  Phase 1
                </span>
              </div>
              <p className="text-[11px] text-slate-400 mb-3">
                Feedstock characterization and cell maceration disruption.
              </p>

              {/* Feed Type Selector */}
              <div className="mb-3">
                <label className="text-[11px] text-slate-300 font-medium block mb-1">
                  Feedstock Blend:
                </label>
                <select
                  value={scenarios.feed_front_end}
                  onChange={(e) => updateScenario('feed_front_end', e.target.value)}
                  className="w-full bg-slate-900 border border-slate-700 rounded-lg px-2.5 py-1.5 text-xs text-emerald-300 focus:outline-none focus:border-emerald-500"
                >
                  <option value="measured_grass">Measured Fresh Grass Silage (78% Moisture)</option>
                  <option value="roadside_grass">Roadside Grass Cuts (82% Moisture, Sand)</option>
                  <option value="clover_grass_mix">Clover-Grass Silage Blend (+15% N)</option>
                  <option value="manure_co_digest">Grass + Dairy Manure Co-Digest</option>
                </select>
              </div>

              {/* Maceration Intensity */}
              <div>
                <label className="text-[11px] text-slate-300 font-medium block mb-1">
                  Maceration Tech:
                </label>
                <select
                  value={scenarios.maceration_intensity || 'standard_screw'}
                  onChange={(e) => updateScenario('maceration_intensity', e.target.value)}
                  className="w-full bg-slate-900 border border-slate-700 rounded-lg px-2.5 py-1.5 text-xs text-slate-200 focus:outline-none focus:border-emerald-500"
                >
                  <option value="standard_screw">Standard Screw Press (1.0x)</option>
                  <option value="high_shear">High-Shear Mechanical Homogenizer (+10% protein)</option>
                  <option value="hydrothermal_prep">Hydrothermal Pre-treatment (+22% protein)</option>
                </select>
              </div>
            </div>
          </div>
        )}

        {/* Phase 2: Protein Recovery */}
        {(activeAreaTab === 'all' || activeAreaTab === 'protein_recovery') && (
          <div className="bg-slate-950/70 border border-slate-800/90 rounded-xl p-4 flex flex-col justify-between">
            <div>
              <div className="flex items-center justify-between mb-2">
                <span className="text-xs font-bold text-emerald-400 flex items-center gap-1.5">
                  <Sparkles className="w-3.5 h-3.5" /> 2. Protein Recovery
                </span>
                <span className="text-[10px] bg-slate-800 px-2 py-0.5 rounded-full text-slate-300">
                  Phase 2
                </span>
              </div>
              <p className="text-[11px] text-slate-400 mb-3">
                RuBisCO leaf protein extraction & coagulation vessel controls.
              </p>

              {/* Protein Method */}
              <div className="mb-3">
                <label className="text-[11px] text-slate-300 font-medium block mb-1">
                  Extraction Pathway:
                </label>
                <select
                  value={scenarios.protein_recovery}
                  onChange={(e) => updateScenario('protein_recovery', e.target.value)}
                  className="w-full bg-slate-900 border border-slate-700 rounded-lg px-2.5 py-1.5 text-xs text-emerald-300 focus:outline-none focus:border-emerald-500"
                >
                  <option value="isoelectric_precipitation">PR1/PR2 Isoelectric Precipitation (pH 4.2)</option>
                  <option value="thermal_coagulation">Thermal Heat Coagulation (65°C)</option>
                  <option value="membrane_ultrafiltration">Ultrafiltration Membrane Separation</option>
                  <option value="bypassed_direct_ad">Bypass Protein Recovery (Direct to AD)</option>
                </select>
              </div>

              {scenarios.protein_recovery === 'bypassed_direct_ad' ? (
                <div className="p-2 bg-amber-500/10 border border-amber-500/30 rounded-lg text-[11px] text-amber-300">
                  Protein recovery bypassed. All leaf proteins enter AD digester directly, increasing biogas yield & FAN load.
                </div>
              ) : (
                <div className="text-[11px] text-slate-400">
                  Target precipitation pH: <strong className="text-emerald-400 font-mono">4.2</strong> (Optimized RuBisCO isoelectric point)
                </div>
              )}
            </div>
          </div>
        )}

        {/* Phase 3: Anaerobic Digestion */}
        {(activeAreaTab === 'all' || activeAreaTab === 'anaerobic_digestion') && (
          <div className="bg-slate-950/70 border border-slate-800/90 rounded-xl p-4 flex flex-col justify-between">
            <div>
              <div className="flex items-center justify-between mb-2">
                <span className="text-xs font-bold text-emerald-400 flex items-center gap-1.5">
                  <Flame className="w-3.5 h-3.5" /> 3. Anaerobic Digestion
                </span>
                <span className="text-[10px] bg-slate-800 px-2 py-0.5 rounded-full text-slate-300">
                  Phase 3
                </span>
              </div>
              <p className="text-[11px] text-slate-400 mb-3">
                CSTR ADM1 kinetic digester & operating condition controls.
              </p>

              {/* Digester Technology */}
              <div className="mb-3">
                <label className="text-[11px] text-slate-300 font-medium block mb-1">
                  Digester Tech & Temp:
                </label>
                <select
                  value={scenarios.anaerobic_digestion}
                  onChange={(e) => updateScenario('anaerobic_digestion', e.target.value)}
                  className="w-full bg-slate-900 border border-slate-700 rounded-lg px-2.5 py-1.5 text-xs text-emerald-300 focus:outline-none focus:border-emerald-500"
                >
                  <option value="cstr_mesophilic">CSTR Mesophilic AD (38°C, 20-day HRT)</option>
                  <option value="cstr_thermophilic">CSTR Thermophilic AD (52°C, 12-day HRT)</option>
                  <option value="two_stage_ad">Two-Stage Acidogenic/Methanogenic AD</option>
                  <option value="plug_flow">Plug-Flow Digester</option>
                </select>
              </div>

              <div className="text-[11px] text-slate-400">
                Operating OLR: <strong className="text-emerald-400 font-mono">3.5 kg COD/m³/d</strong>
              </div>
            </div>
          </div>
        )}

        {/* Phase 4: Biogas Upgrading */}
        {(activeAreaTab === 'all' || activeAreaTab === 'biogas_upgrading') && (
          <div className="bg-slate-950/70 border border-slate-800/90 rounded-xl p-4 flex flex-col justify-between">
            <div>
              <div className="flex items-center justify-between mb-2">
                <span className="text-xs font-bold text-emerald-400 flex items-center gap-1.5">
                  <Cpu className="w-3.5 h-3.5" /> 4. Biogas Upgrading
                </span>
                <span className="text-[10px] bg-slate-800 px-2 py-0.5 rounded-full text-slate-300">
                  Phase 4
                </span>
              </div>
              <p className="text-[11px] text-slate-400 mb-3">
                CO2 separation & biomethane grid conditioning.
              </p>

              {/* Upgrading System */}
              <div className="mb-3">
                <label className="text-[11px] text-slate-300 font-medium block mb-1">
                  Separation Technology:
                </label>
                <select
                  value={scenarios.biogas_upgrading}
                  onChange={(e) => updateScenario('biogas_upgrading', e.target.value)}
                  className="w-full bg-slate-900 border border-slate-700 rounded-lg px-2.5 py-1.5 text-xs text-emerald-300 focus:outline-none focus:border-emerald-500"
                >
                  <option value="membrane_3stage">3-Stage Polyimide Membrane (97.5% CH4)</option>
                  <option value="water_scrubbing">High-Pressure Water Scrubbing (96.5% CH4)</option>
                  <option value="amine_absorption">Chemical Amine Scrubbing (98.8% CH4)</option>
                  <option value="psa_4bed">4-Bed Pressure Swing Adsorption (97.2% CH4)</option>
                </select>
              </div>

              <div className="text-[11px] text-slate-400">
                Methane Slip Target: <strong className="text-emerald-400 font-mono">&lt;1.5%</strong>
              </div>
            </div>
          </div>
        )}

        {/* Phase 5: Nutrient Recovery (Phase 7) */}
        {(activeAreaTab === 'all' || activeAreaTab === 'nutrient_recovery') && (
          <div className="bg-slate-950/70 border border-slate-800/90 rounded-xl p-4 md:col-span-2 lg:col-span-2 flex flex-col justify-between">
            <div>
              <div className="flex items-center justify-between mb-2">
                <span className="text-xs font-bold text-emerald-400 flex items-center gap-1.5">
                  <Droplet className="w-3.5 h-3.5" /> 5. Phase 7 Nutrient Recovery Pathway
                </span>
                <span className="text-[10px] bg-slate-800 px-2 py-0.5 rounded-full text-slate-300">
                  Phase 5
                </span>
              </div>

              {/* Scenario Selector */}
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 mb-3">
                {nrScenarios.map((opt) => {
                  const isSelected = scenarios.nutrient_recovery === opt.id;
                  return (
                    <button
                      key={opt.id}
                      onClick={() => updateScenario('nutrient_recovery', opt.id)}
                      className={`p-2 rounded-lg border text-left transition cursor-pointer ${
                        isSelected
                          ? 'bg-emerald-500/15 border-emerald-500/60 ring-1 ring-emerald-500/30'
                          : 'bg-slate-900 border-slate-800 text-slate-300 hover:border-slate-700'
                      }`}
                    >
                      <div className="flex items-center justify-between">
                        <span className={`text-[11px] font-bold font-mono ${isSelected ? 'text-emerald-400' : 'text-slate-200'}`}>
                          {opt.id}
                        </span>
                        {isSelected && <Sparkles className="w-3 h-3 text-emerald-400" />}
                      </div>
                      <p className="text-[10px] text-slate-400 truncate mt-0.5">{opt.title.split(':')[1]}</p>
                    </button>
                  );
                })}
              </div>

              {/* Unit Sequence */}
              <div>
                <label className="text-[11px] text-slate-300 font-medium block mb-1">
                  Unit Process Order Sequence:
                </label>
                <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
                  {processOrders.map((ord) => {
                    const isSelected = scenarios.process_order === ord.id;
                    return (
                      <button
                        key={ord.id}
                        onClick={() => updateScenario('process_order', ord.id)}
                        className={`p-1.5 rounded-md border text-left text-[11px] transition cursor-pointer ${
                          isSelected
                            ? 'bg-emerald-500/20 border-emerald-500/50 text-emerald-300 font-semibold'
                            : 'bg-slate-900 border-slate-800 text-slate-400 hover:text-slate-200'
                        }`}
                      >
                        <div>{ord.label}</div>
                      </button>
                    );
                  })}
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
