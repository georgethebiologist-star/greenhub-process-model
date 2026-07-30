import express from 'express';
import cors from 'cors';
import path from 'path';
import { createServer as createViteServer } from 'vite';
import { runSimulation, DEFAULT_PARAMETERS, PROCESS_AREAS } from './src/data/greenhubData';

async function startServer() {
  const app = express();
  const PORT = 3000;

  app.use(cors());
  app.use(express.json({ limit: '2mb' }));

  // In-memory simulation runs cache
  const runCache = new Map<string, any>();

  // REST API Routes under /api/v1
  app.get('/api/v1/health', (req, res) => {
    res.json({ status: 'ok', api_version: 'v1', schema_version: '1.0.0' });
  });

  app.get('/api/v1/model/info', (req, res) => {
    res.json({
      model: 'GreenHub BioSTEAM scientific process model',
      api_version: 'v1',
      request_schema_version: '1.0.0',
      calculation_modes: ['structural', 'literature_default', 'calibrated'],
      resolution_modes: ['strict', 'fallback'],
      parameter_count: DEFAULT_PARAMETERS.length,
      active_equation_ids: ['EQ-001', 'EQ-002', 'REC-001', 'AD-ADM1-01', 'STRUV-01'],
      execution_model: 'synchronous isolated run',
      scientific_core: 'transport-neutral'
    });
  });

  app.get('/api/v1/scenarios', (req, res) => {
    res.json({
      front_end: {
        feed_types: [
          { id: 'measured_grass', label: 'Measured Fresh Grass Silage', desc: '78% moisture, 0.88 VS/TS' },
          { id: 'roadside_grass', label: 'Roadside Grass Cuts', desc: '82% moisture, high silica/sand' },
          { id: 'clover_grass_mix', label: 'Clover-Grass Silage Blend', desc: 'Higher protein & N content' },
          { id: 'manure_co_digest', label: 'Grass + Dairy Manure Co-Digest', desc: 'Higher buffering capacity' }
        ],
        maceration_intensities: [
          { id: 'standard_screw', label: 'Standard Screw Press Maceration', desc: 'Baseline 1.0x disruption' },
          { id: 'high_shear', label: 'High-Shear Mechanical Homogenizer', desc: '+10% cell disruption' },
          { id: 'hydrothermal_prep', label: 'Hydrothermal Pre-treatment', desc: '+22% cell disruption' }
        ]
      },
      protein_recovery: {
        methods: [
          { id: 'isoelectric_precipitation', label: 'PR1/PR2 Isoelectric Precipitation (pH 4.2)', desc: 'Standard RuBisCO acid coagulation' },
          { id: 'thermal_coagulation', label: 'Thermal Heat Coagulation (65°C)', desc: 'Thermally induced protein aggregation' },
          { id: 'membrane_ultrafiltration', label: 'Ultrafiltration Membrane Separation', desc: 'High purity concentrate (>75% protein)' },
          { id: 'bypassed_direct_ad', label: 'Bypass Protein Recovery (Direct to AD)', desc: 'Zero protein extraction; all organics to AD' }
        ]
      },
      anaerobic_digestion: {
        technologies: [
          { id: 'cstr_mesophilic', label: 'CSTR Mesophilic AD (38°C)', desc: 'Standard 20-day HRT CSTR digester' },
          { id: 'cstr_thermophilic', label: 'CSTR Thermophilic AD (52°C)', desc: 'Faster kinetics, higher heat demand' },
          { id: 'two_stage_ad', label: 'Two-Stage Acidogenic/Methanogenic AD', desc: 'Phase-separated digestion' },
          { id: 'plug_flow', label: 'Plug-Flow Digester', desc: 'High solids dry anaerobic digestion' }
        ]
      },
      biogas_upgrading: {
        systems: [
          { id: 'membrane_3stage', label: '3-Stage Polyimide Membrane Module', desc: '97.5% CH4 purity, <1.5% slip' },
          { id: 'water_scrubbing', label: 'High-Pressure Water Scrubbing', desc: '96.5% CH4 purity, higher water load' },
          { id: 'amine_absorption', label: 'Chemical Amine Scrubbing', desc: '98.8% CH4 purity, high thermal regen' },
          { id: 'psa_4bed', label: '4-Bed Pressure Swing Adsorption (PSA)', desc: '97.2% CH4 purity, dry separation' }
        ]
      },
      nutrient_recovery: {
        scenarios: [
          { id: 'NR0', title: 'NR0: No Recovery', description: 'Digestate inventory only; zero nutrient extraction' },
          { id: 'NR1', title: 'NR1: Solid Separation', description: 'Screw press / decanter separation into cake & liquor' },
          { id: 'NR2', title: 'NR2: Struvite Only', description: 'MgNH4PO4 crystallization from liquid digestate' },
          { id: 'NR3', title: 'NR3: N-Stripping Only', description: 'Air stripping & H2SO4 acid absorption for (NH4)2SO4' },
          { id: 'NR4', title: 'NR4: Struvite + N-Salt', description: 'Integrated P and N recovery baseline' },
          { id: 'NR5', title: 'NR5: Calcium Phosphate', description: 'Ca(OH)2 addition alternative for phosphate fertilizer' },
          { id: 'NR6', title: 'NR6: Zeolite Ion Exchange', description: 'Clinoptilolite column ion exchange for ammonium' },
          { id: 'NR7', title: 'NR7: Full P/N/K Recovery', description: 'Integrated P/N recovery + thermal K-concentration' }
        ],
        process_orders: [
          { id: 'A', label: 'Order A (Default)', desc: 'Separation -> Phosphorus -> Nitrogen -> Potassium' },
          { id: 'B', label: 'Order B', desc: 'Separation -> Nitrogen -> Phosphorus -> Potassium' },
          { id: 'C', label: 'Order C', desc: 'Precipitate P from whole digestate -> Separation -> N -> K' },
          { id: 'D', label: 'Order D', desc: 'Separation only (NR0 / NR1 baseline constraint)' }
        ]
      }
    });
  });

  app.get('/api/v1/process-areas', (req, res) => {
    res.json(PROCESS_AREAS);
  });

  app.get('/api/v1/parameters', (req, res) => {
    res.json(DEFAULT_PARAMETERS);
  });

  app.post('/api/v1/parameters/validate', (req, res) => {
    const { parameter_id, value } = req.body || {};
    const param = DEFAULT_PARAMETERS.find((p) => p.parameter_id === parameter_id);
    if (!param) {
      return res.status(404).json({ valid: false, error: 'Parameter not found' });
    }
    const val = typeof value === 'number' ? value : parseFloat(value);
    const valid = val >= (param.min_value ?? -Infinity) && val <= (param.max_value ?? Infinity);
    res.json({
      valid,
      parameter_id,
      value: val,
      issues: valid ? [] : [`Value ${val} is outside allowed range [${param.min_value}, ${param.max_value}]`]
    });
  });

  app.post('/api/v1/simulations', (req, res) => {
    const request = req.body || {};
    const result = runSimulation(request);
    runCache.set(result.run_id, result);
    res.status(201).json(result);
  });

  app.get('/api/v1/simulations/:run_id/:resource', (req, res) => {
    const { run_id, resource } = req.params;
    let result = runCache.get(run_id);
    if (!result) {
      result = runSimulation({});
      runCache.set(run_id, result);
    }
    if (resource in result) {
      return res.json(result[resource as keyof typeof result]);
    }
    if (resource === 'status') {
      return res.json({ run_id, status: 'completed', completed_at: result.timestamp });
    }
    res.status(404).json({ error: `Resource ${resource} not found` });
  });

  // Vite development middleware or static production handler
  if (process.env.NODE_ENV !== 'production') {
    const vite = await createViteServer({
      server: { middlewareMode: true },
      appType: 'spa'
    });
    app.use(vite.middlewares);
  } else {
    const distPath = path.join(process.cwd(), 'dist');
    app.use(express.static(distPath));
    app.get('*', (req, res) => {
      res.sendFile(path.join(distPath, 'index.html'));
    });
  }

  app.listen(PORT, '0.0.0.0', () => {
    console.log(`[GreenHub Server] Server running on http://0.0.0.0:${PORT}`);
  });
}

startServer();
