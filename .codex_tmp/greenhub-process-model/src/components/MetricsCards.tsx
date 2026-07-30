import React from 'react';
import { RecoveryMetrics } from '../types';
import { Flame, Zap, Droplet, ShieldCheck, Leaf, Factory } from 'lucide-react';

interface MetricsCardsProps {
  metrics: RecoveryMetrics;
}

export const MetricsCards: React.FC<MetricsCardsProps> = ({ metrics }) => {
  const cards = [
    {
      title: 'Biogas Production',
      value: `${metrics.biogas_m3h.toFixed(1)} m³/h`,
      sub: `${metrics.methane_purity_pct.toFixed(1)}% CH₄ purity`,
      icon: Flame,
      color: 'text-amber-400',
      bg: 'bg-amber-500/10 border-amber-500/20'
    },
    {
      title: 'Protein Concentrate',
      value: `${metrics.protein_recovered_kgh.toFixed(1)} kg/h`,
      sub: `${metrics.protein_purity_pct.toFixed(1)}% protein dry purity`,
      icon: Leaf,
      color: 'text-emerald-400',
      bg: 'bg-emerald-500/10 border-emerald-500/20'
    },
    {
      title: 'Struvite Yield (P)',
      value: `${metrics.struvite_yield_kgh.toFixed(1)} kg/h`,
      sub: `MgNH₄PO₄·6H₂O crystal product`,
      icon: Droplet,
      color: 'text-cyan-400',
      bg: 'bg-cyan-500/10 border-cyan-500/20'
    },
    {
      title: 'Ammonium Sulfate (N)',
      value: `${metrics.ammonia_sulfate_kgh.toFixed(1)} kg/h`,
      sub: `28% liquid fertilizer solution`,
      icon: Factory,
      color: 'text-purple-400',
      bg: 'bg-purple-500/10 border-purple-500/20'
    },
    {
      title: 'Net Power Balance',
      value: `${metrics.net_power_kw.toFixed(1)} kW`,
      sub: `Heat demand: ${metrics.net_heat_kw.toFixed(0)} kW`,
      icon: Zap,
      color: 'text-blue-400',
      bg: 'bg-blue-500/10 border-blue-500/20'
    },
  ];

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-3 mb-6">
      {cards.map((card, idx) => {
        const Icon = card.icon;
        return (
          <div
            key={idx}
            className={`p-4 rounded-xl border ${card.bg} flex flex-col justify-between transition-all`}
          >
            <div className="flex items-center justify-between mb-2">
              <span className="text-xs font-medium text-slate-400">{card.title}</span>
              <Icon className={`w-4 h-4 ${card.color}`} />
            </div>
            <div>
              <div className="text-xl font-bold font-mono text-white mb-0.5">{card.value}</div>
              <p className="text-[11px] text-slate-400">{card.sub}</p>
            </div>
          </div>
        );
      })}
    </div>
  );
};
