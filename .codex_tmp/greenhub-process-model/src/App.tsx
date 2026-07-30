import React, { useState, useEffect } from 'react';
import {
  CalculationMode,
  NutrientScenarioId,
  ParameterDefinition,
  ScenarioSelection,
  SimulationResult
} from './types';
import { runSimulation, DEFAULT_PARAMETERS } from './data/greenhubData';
import { Header } from './components/Header';
import { ScenarioControls } from './components/ScenarioControls';
import { MetricsCards } from './components/MetricsCards';
import { FlowsheetViewer } from './components/FlowsheetViewer';
import { BalancesTab } from './components/BalancesTab';
import { ParameterRegister } from './components/ParameterRegister';
import { PlotCatalog } from './components/PlotCatalog';
import { ReportExport } from './components/ReportExport';
import { Layers, Sliders, Scale, Activity, FileSpreadsheet, Info } from 'lucide-react';

export function App() {
  const [calculationMode, setCalculationMode] = useState<CalculationMode>('literature_default');
  const [selectedMonth, setSelectedMonth] = useState<string>('July');
  const [scenarios, setScenarios] = useState<ScenarioSelection>({
    feed_front_end: 'measured_grass',
    protein_recovery: 'isoelectric_precipitation',
    anaerobic_digestion: 'cstr_mesophilic',
    biogas_upgrading: 'membrane_3stage',
    nutrient_recovery: 'NR4',
    process_order: 'A'
  });

  const [parameters, setParameters] = useState<ParameterDefinition[]>(DEFAULT_PARAMETERS);
  const [activeTab, setActiveTab] = useState<'flowsheet' | 'balances' | 'parameters' | 'plots' | 'exports'>('flowsheet');
  const [isSimulating, setIsSimulating] = useState<boolean>(false);
  const [simulationResult, setSimulationResult] = useState<SimulationResult>(() =>
    runSimulation({ calculation_mode: 'literature_default', selected_month: 'July', scenarios })
  );

  const executeRun = () => {
    setIsSimulating(true);
    setTimeout(() => {
      const overrides = parameters.map((p) => ({
        parameter_id: p.parameter_id,
        value: p.current_value
      }));
      const res = runSimulation({
        calculation_mode: calculationMode,
        selected_month: selectedMonth,
        scenarios,
        design_overrides: overrides
      });
      setSimulationResult(res);
      setIsSimulating(false);
    }, 250);
  };

  useEffect(() => {
    executeRun();
  }, [calculationMode, selectedMonth, scenarios]);

  const handleUpdateParameter = (parameterId: string, newValue: number | string | boolean) => {
    setParameters((prev) =>
      prev.map((p) => (p.parameter_id === parameterId ? { ...p, current_value: newValue } : p))
    );
  };

  const handleResetDefaults = () => {
    setParameters(DEFAULT_PARAMETERS);
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col font-sans">
      <Header
        calculationMode={calculationMode}
        setCalculationMode={setCalculationMode}
        selectedMonth={selectedMonth}
        setSelectedMonth={setSelectedMonth}
        onRunSimulation={executeRun}
        isSimulating={isSimulating}
        dataReadinessScore={simulationResult.metrics.data_readiness_score}
      />

      <main className="flex-1 max-w-7xl w-full mx-auto px-4 py-6">
        {/* Scenario Controls */}
        <ScenarioControls scenarios={scenarios} onChange={setScenarios} />

        {/* Top KPI Metrics Cards */}
        <MetricsCards metrics={simulationResult.metrics} />

        {/* Primary View Navigation Tabs */}
        <div className="flex items-center gap-2 border-b border-slate-800 mb-6 overflow-x-auto pb-1">
          {[
            { id: 'flowsheet', label: 'Flowsheet & Units', icon: Layers },
            { id: 'balances', label: 'Mass & Elemental Balances', icon: Scale },
            { id: 'parameters', label: 'Parameter Registry', icon: Sliders },
            { id: 'plots', label: 'Plot Catalog', icon: Activity },
            { id: 'exports', label: 'Stream Tables & Reports', icon: FileSpreadsheet },
          ].map((tab) => {
            const Icon = tab.icon;
            const isActive = activeTab === tab.id;
            return (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id as any)}
                className={`flex items-center gap-2 px-4 py-2.5 rounded-t-xl text-xs font-semibold border-b-2 transition cursor-pointer whitespace-nowrap ${
                  isActive
                    ? 'border-emerald-400 text-emerald-400 bg-emerald-500/10'
                    : 'border-transparent text-slate-400 hover:text-slate-200 hover:bg-slate-900/60'
                }`}
              >
                <Icon className="w-4 h-4" />
                <span>{tab.label}</span>
              </button>
            );
          })}
        </div>

        {/* Active Tab View */}
        {activeTab === 'flowsheet' && (
          <FlowsheetViewer
            processAreas={simulationResult.process_areas}
            units={simulationResult.units}
            streams={simulationResult.streams}
          />
        )}

        {activeTab === 'balances' && <BalancesTab balances={simulationResult.balances} />}

        {activeTab === 'parameters' && (
          <ParameterRegister
            parameters={parameters}
            onUpdateParameter={handleUpdateParameter}
            onResetDefaults={handleResetDefaults}
          />
        )}

        {activeTab === 'plots' && <PlotCatalog plots={simulationResult.plots} />}

        {activeTab === 'exports' && <ReportExport simulationResult={simulationResult} />}
      </main>

      <footer className="border-t border-slate-800 bg-slate-900 py-4 px-4 text-center text-xs text-slate-500">
        <p>GreenHub BioSTEAM Process Model &bull; Transport-Neutral WSGI & REST Service &bull; Version 1.0.0</p>
      </footer>
    </div>
  );
}

export default App;
