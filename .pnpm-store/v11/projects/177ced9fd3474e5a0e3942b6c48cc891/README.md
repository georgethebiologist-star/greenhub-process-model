# GreenHub frontend

The React interface and Node web server live here. The Python model remains a separate service; see the [repository README](../README.md) for the beginner setup and the [architecture guide](../docs/architecture.md) for the service boundary.

## Local development

Start the Python API from the repository root in one terminal:

```powershell
.\.venv\Scripts\python.exe -m api
```

In a second terminal, change into `frontend/` and start the web service:

```powershell
cd frontend
corepack pnpm install --frozen-lockfile
corepack pnpm dev
```

Open `http://127.0.0.1:3000`. The Node service forwards `/api/v1` requests to the Python API at `http://127.0.0.1:8000`. Keep both terminals open; use Ctrl+C in each to stop the services.

## Checks and production build

```powershell
cd frontend
corepack pnpm lint
corepack pnpm check:fallback
corepack pnpm check:decision
corepack pnpm build
```

The build creates `dist/`. Start the Python API separately, then run `corepack pnpm start` from this folder to serve the compiled interface and proxy API requests. The Windows one-click launcher in the repository root automates the local interactive setup.
