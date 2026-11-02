# Render frontend fallback

## Deployment contract

The production frontend defaults to same-origin API requests under `/api/v1`. This works when Render routes the UI and Python API through one public origin. When they are separate Render services, set this build-time environment variable on the frontend service:

```text
VITE_GREENHUB_API_URL=https://<python-service>.onrender.com/api/v1
VITE_GREENHUB_API_TIMEOUT_MS=15000
```

`VITE_GREENHUB_API_URL` is compiled into the Vite bundle, so set it before `npm run build` and redeploy after changing it. The Python service must allow the frontend origin through CORS. Do not set a production value to `127.0.0.1`; in a browser that address means the visitor's computer.

The bundled Express server serves a lightweight JavaScript simulation endpoint, but it does not expose the Python dynamic-complete service or its full annual reporting resources. A separate Python URL or an external same-origin reverse proxy is required for live scientific results.

## Fallback behavior

The frontend includes the versioned fixture `greenhub-baseline-2026-09-16` in `frontend/src/data/baselineFixtures.ts`. It contains a complete 30,000 t/year empirical annual report and a complete dynamic proxy report with monthly schedule, products, energy, economics/environmental proxy, and evidence records.

If simulation creation, annual reporting, dynamic options, or dynamic scenario calculation fails, the UI keeps charts and reports populated from this fixture. The source banner uses one of five states:

- `live_python`: empirical result and annual reporting bundle came from Python.
- `live_api`: dynamic proxy result came from the Python API.
- `preview_baseline`: the bundled baseline is shown before a live result.
- `backend_unavailable`: a live request failed and the baseline is shown.
- `stale_previous_result`: controls changed or a refresh failed, so the last result was retained.

Changing controls while offline does not recalculate the fixture. The UI explicitly says that the displayed values are unchanged. Preview values must not be used as live Python evidence.

## Verification

```powershell
cd frontend
npm run lint
npm run check:fallback
npm run build
```

To test the failure path, temporarily point `VITE_GREENHUB_API_URL` to an unavailable host, build the frontend, and confirm that both dashboards show the yellow backend-unavailable banner while retaining all charts and report exports.
