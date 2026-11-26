# GreenHub user guide

## What the setup terms mean

- **Python** is the program that runs GreenHub's scientific process calculations. Use CPython 3.12.x for this release setup.
- **Node.js** runs the local web interface service that displays the React screens in your browser. It does not replace the Python model.
- A **virtual environment** is a project-local `.venv` folder where GreenHub keeps its Python packages, without changing packages for other applications on your computer.
- The **API** is the local connection the web interface uses to ask the Python model to run a calculation and return results. You do not need to configure it yourself.
- `http://127.0.0.1:3000` is an address for an application running on this same computer. It is not a public website and normally cannot be opened from another device.

## Install and launch on Windows

GreenHub's Windows launcher supports CPython 3.12.x for the scientific API and Node.js 24.x with Corepack for the React web interface. Use Node 24 for this handover because it is the tested LTS line and includes Corepack, which reads this project's pinned pnpm version. Node 25 and later do not bundle Corepack, so they need an extra package-manager setup step outside the tested beginner path ([Node.js release schedule](https://nodejs.org/en/about/previous-releases), [Node.js distribution notes](https://github.com/nodejs/node/blob/main/doc/contributing/distribution.md)). Install the official [Python Install Manager](https://docs.python.org/3/using/windows.html) from the Microsoft Store or the [Python for Windows downloads page](https://www.python.org/downloads/windows/). After it installs, open PowerShell and run:

```powershell
py install 3.12
```

This installs the latest stable CPython 3.12 runtime managed by Python. GreenHub selects that 3.12 runtime when creating `.venv`, even if another Python version is the system default. Install [Node.js 24 LTS](https://nodejs.org/en/download/) with the default options; Corepack selects the project's pinned pnpm version. The tested versions were CPython 3.12.14, Node.js 24.18.1, and pnpm 11.16.0.

Download the [GreenHub repository](https://github.com/georgethebiologist-star/greenhub-process-model) using **Code → Download ZIP**, then extract it. This route does not need Git. (To use Git, install it from [git-scm.com](https://git-scm.com/downloads), then run `git clone https://github.com/georgethebiologist-star/greenhub-process-model.git`.) Open the extracted or cloned folder containing `Start GreenHub.bat` in File Explorer. Double-click it to start GreenHub. For the terminal alternative, open the folder in File Explorer, click its address bar, type `powershell`, press Enter, and run:

```powershell
powershell -ExecutionPolicy Bypass -File .\launch.ps1
```

The first run creates `.venv` and installs the Python packages pinned in `requirements.txt` plus frontend packages pinned in `frontend/pnpm-lock.yaml` using pnpm 11.16.0. It needs internet access and may take several minutes. The launcher records dependency-file hashes in the ignored `.venv` folder and reinstalls if the Python requirements, frontend manifest, or lockfile changes. A successful start prints **GreenHub is ready at http://127.0.0.1:3000/** and opens the browser. Keep the PowerShell window open during use; press **Ctrl+C** there to stop the UI and API. Run the same command again to restart. `-SkipInstall` skips package installation after a successful setup.

To update, download and extract the newer version to a new folder, then launch that copy. Preserve your old folder until you have copied any local work or data changes you need. Do not overwrite a locally modified dataset with a downloaded default without comparing its source and revision.

## Run a scenario

1. Select **Configure → Biomass** to review the monthly feed availability schedule and composition editor. Keep the evidence/source notes with any changed composition values; the editor values are model inputs, not new measurements.
2. Select **Configure → Process** to set operating days and hours, annual processing target, and product routes. Protein recovery and biostimulant recovery are mutually exclusive. Enable biomethane to choose an anaerobic digestion and upgrading route; enable nutrient products to choose a nutrient-recovery scenario. Check compatibility warnings if you combine routes.
3. Review **Configure → Economics** and **Environment** before interpreting TEA or LCA. These assumptions affect the downstream results. They do not calibrate the process model.
4. In **Model settings**, choose the evidence basis and reference month, and review core or detailed assumptions as needed. Avoid changing several parameters at once when diagnosing a result.
5. Click **Run simulation** and wait for the progress indicator to finish. The status banner identifies whether the displayed result is live, a preview baseline, or a stale result left from earlier inputs. Only interpret a run as current when the banner and run details identify the completed API-backed run.
6. Review **Results → Performance** for the process graph, KPIs, process areas, balance checks, and warnings. Use **Inventory** and **Hotspots** for downstream inventory and contribution views. A successful validation check only reports internal model checks; it is not experimental validation.
7. Use **Results → Optimization** to inspect available Pareto screening candidates and **Model comparison** for the available comparison workflow. Candidate lists depend on a generated/available Pareto artifact; an empty or loading view does not mean the model found no viable process.
8. Use **Reports** to download the selected run's available exports. Review the included scenario, input request, limitations, and warnings before sharing. **Save baseline** and **Save candidate** snapshots are kept in this browser's local storage; they do not create a shared project archive.

Start with the supplied defaults, review warnings and assumptions shown with the run, and compare one deliberate input or route change at a time. Retain run IDs and input settings when sharing results.

The repository's master workbook is `Greenhub/data/greenhub_feed_inputs.xlsx`; the README's [Master Workbook](../README.md#master-workbook) section describes its controls. Feed and route IDs, parameter definitions, and scenario constraints are documented in `Greenhub/parameters/`, `Greenhub/data/`, and `docs/scenario_reference.md`. See [scientific assumptions](scientific_assumptions.md) and [limitations](model_limitations.md) before interpreting results.

TEA and LCA are post-simulation evaluations. Economic indicators depend on cost, price, capacity, and finance assumptions; environmental indicators depend on inventory boundaries, factors, and data quality. Optimization explores the selected objective and constraints and should be treated as screening, not as an independently validated recommendation. Reports and exports describe the selected run; check their provenance and warnings before reuse.

## Run without the UI

From the repository root in PowerShell (the folder containing `README.md`, `launch.ps1`, and `Greenhub/`):

```powershell
py install 3.12
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m Greenhub.main
```

Start the API separately with `.\.venv\Scripts\python.exe -m api`; its health endpoint is `http://127.0.0.1:8000/api/v1/health` and its OpenAPI contract is at `http://127.0.0.1:8000/api/v1/openapi.json`. A frontend developer can run `corepack pnpm install --frozen-lockfile` and then `corepack pnpm dev` from `frontend/` after starting the Python API. The lockfile pins the web dependency graph and the package manager version. The Windows launcher automates this workflow.

## macOS and Linux

The Python model and services are cross-platform in principle, but the one-click launcher is currently Windows-only. On macOS or Linux, use Python 3.12.x and Node.js 24.x and install project dependencies, then use two terminals from the downloaded project root:

```sh
python3.12 -m venv .venv
. .venv/bin/activate
python -m pip install -r requirements.txt
python -m api
```

In a second terminal:

```sh
cd frontend
corepack pnpm install --frozen-lockfile
corepack pnpm dev
```

Open `http://127.0.0.1:3000`. Stop each service with Ctrl+C in its terminal.
