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
      nutrient_recovery_scenarios: [
        { id: 'NR0', title: 'No Recovery', description: 'Digestate inventory only' },
        { id: 'NR1', title: 'Solid Separation', description: 'Screw press / decanter separation' },
        { id: 'NR2', title: 'Struvite Recovery', description: 'MgNH4PO4 crystallization' },
        { id: 'NR3', title: 'Ammonia Stripping', description: 'Air stripping & acid absorption' },
        { id: 'NR4', title: 'Struvite + N-Salt', description: 'Integrated P & N baseline' },
        { id: 'NR5', title: 'Calcium Phosphate', description: 'Ca(OH)2 precipitation alternative' },
        { id: 'NR6', title: 'Zeolite Ion Exchange', description: 'Clinoptilolite column exchange' },
        { id: 'NR7', title: 'Full P/N/K Recovery', description: 'Integrated P, N, and K concentration' }
      ],
      process_orders: ['A', 'B', 'C', 'D']
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
