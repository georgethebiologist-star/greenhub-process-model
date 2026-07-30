# GreenHub Integrated BioSTEAM Model - Alpha

This repository contains one connected GreenHub model covering feed characterization, preparation and primary separation, protein recovery, anaerobic digestion, biogas conditioning/upgrading, digestate processing, and nutrient recovery. It produces transparent engineering inventories for later TEA, LCA, uncertainty analysis, regulatory review, and MCDA. It does not rank configurations or claim a commercial design.

The current alpha restoration keeps historically named `phaseX_*` modules as tested compatibility layers. New code should use `create_integrated_greenhub_system()` and meaningful process-area views rather than treating development phases as separate plants. Audit evidence, Git findings, dataset readiness, and the restoration plan are under [docs/audit](docs/audit/).

Advanced-model Checkpoint 1 adds read-only governance for the 301-dataset global audit package. It quarantines defective rows and classifies datasets, equations, and cost overlaps without activating literature values or changing process calculations. See [advanced-model plans](docs/advanced_model/integration_plan.md).

Alpha 0.2 Checkpoint 2 adds immutable canonical parameters, deterministic override precedence, versioned simulation/result contracts, isolated application services, structured process graphs, plot and run exports, and a `/api/v1` WSGI adapter. Checkpoint 3A activates one bounded literature pathway only: `REC-001` supplies a 0.34 precipitation-recovery fraction for `PR1` in `literature_default` mode. Structural runs remain unchanged. See [Checkpoint 2 release notes](docs/alpha_0_2_checkpoint_2/release_notes.md).

Checkpoint 3C adds transport-neutral seasonal and quasi-dynamic simulation. Monthly runs default to May-November, while explicit monthly or daily grids can use direct, normalized, CSV, or workbook feed profiles. Each step conserves feed, storage inventory, overflow, processing, products, utilities, and tracked balance residuals; it rebuilds and simulates the existing integrated BioSTEAM model rather than creating a second process model. See [Checkpoint 3C release notes](docs/alpha_0_2_checkpoint_3c/release_notes.md).

## System Boundary

The fibre-rich press cake remains an upstream side stream. Downstream fibre-panel production is excluded.

```text
Measured liquid or roadside-grass front end
-> protein recovery or bypass
-> anaerobic digestion or bypass
-> raw-biogas conditioning and selected BG pathway
-> actual Phase 5 digestate
-> optional equalization
-> solid-liquid separation
-> selected phosphorus route
-> selected ammonia route
-> optional potassium concentration
-> nutrient products, residual liquor/water, wastewater, and off-gas
```

The current repository does not contain the CHP and plant-wide utility network described as completed in the Phase 7 specification. `BG1` is still inactive and Phase 6 explicitly defers CHP. Phase 7 therefore calculates gross duties and exposes bounded heat/electricity interfaces, but defaults both recovered heat and CHP electricity to zero.

## Integrated Interface

```python
from Greenhub import create_integrated_greenhub_system

model = create_integrated_greenhub_system().simulate()
protein_area = model.process_areas["protein_recovery"]
print(model.system.ID, protein_area.units, model.validation_report.report)
```

The returned object exposes `system`, `flowsheet`, `process_areas`, `units`, `streams`, `feed_specification`, `scenario_configuration`, `warnings`, `assumptions`, `validation_report`, `metrics`, `report_paths`, `dataset_provenance`, and `model_completeness`. `create_greenhub_system()` remains unchanged for compatibility and still means the historical T101/S101 foundation only.

## Nutrient-Recovery Scenarios

| ID | Active route |
|---|---|
| `NR0` | No targeted recovery; digestate inventory only |
| `NR1` | Digestate solid-liquid separation |
| `NR2` | Separation and struvite recovery |
| `NR3` | Separation, ammonia stripping, and acid capture |
| `NR4` | Struvite plus ammonia-salt recovery baseline |
| `NR5` | Calcium-phosphate alternative |
| `NR6` | Zeolite ion exchange with explicit NaCl regeneration recycle |
| `NR7` | Integrated P/N recovery plus non-selective K concentration |

Orders `A`, `B`, `C`, and `D` are selectable. Order A is separation-P-N-K; B is separation-N-P-K; C precipitates P from whole digestate before separation; D is separation only. NR0 and NR1 always use D.

## Installation And Use

From `Model` in PowerShell:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m Greenhub.data_governance
.\.venv\Scripts\python.exe -m Greenhub.parameters
.\.venv\Scripts\python.exe -m Greenhub.application.schema_export
.\.venv\Scripts\python.exe -m Greenhub.main
.\.venv\Scripts\pytest.exe -q
```

If the virtual environment is active, use `python -m Greenhub.main` and `pytest -q`. BioSTEAM is imported from `.venv/Lib/site-packages`; no local source copy is used.

Graphviz is expected at `C:\Program Files\Graphviz\bin`. Immediately before `system.diagram(...)`, `Greenhub.main` executes:

```python
import os
graphviz_bin = r"C:\Program Files\Graphviz\bin"
os.environ["PATH"] = graphviz_bin + os.pathsep + os.environ.get("PATH", "")
```

A Graphviz failure is reported without discarding a valid simulation or blocking tabular reports.

To start the local synchronous development API:

```powershell
.\.venv\Scripts\python.exe -m api
```

Use `GET http://127.0.0.1:8000/api/v1/health` for health and `GET /api/v1/openapi.json` for the OpenAPI 3.1 contract. The scientific layer does not depend on HTTP, the API returns run-relative artifact references, and production deployment still requires a real WSGI server and job queue.

For seasonal simulation, submit `resolution_mode: "quasi_dynamic"` with `start_date`, `end_date`, `time_step`, `feed_supply_profile_id`, and an optional operating schedule, annual biomass target, initial inventory, or `seasonal.storage_capacity_kg` design override. Register direct or normalized profiles through `POST /api/v1/feed-profiles`; inspect outputs through the run `time-series`, `inventory`, `utilization`, and `seasonal-summary` resources. Daily mode requires a daily profile and explicit operating schedule; monthly workbook data are not silently interpolated.

## Master Workbook

Edit [greenhub_feed_inputs.xlsx](Greenhub/data/greenhub_feed_inputs.xlsx). [greenhub_feed_inputs_phase6_backup.xlsx](Greenhub/data/greenhub_feed_inputs_phase6_backup.xlsx) preserves the workbook immediately before Phase 7 was added.

`ModelControl` selects the month and F/PR/AD/BG/NR chain. Nutrient-recovery controls are:

- `selected_phase7_scenario`, default `NR4`;
- `selected_phase7_process_order`, default `A`;
- `phase7_structural_test_mode`, default `TRUE`;
- `phase7_input_basis`, default `structural_test`.

`Phase7Parameters` is the historical workbook name for a consolidated 130-row nutrient-recovery register. It includes values, units, bounds, scenario/month applicability, provenance, quality class, required status, calculation method, and limitation ID.

All supplied Phase 7 values are quality-class `E` assumptions. Required blanks are never silently changed to zero. Optional missing laboratory fields remain missing and do not create material. Replace class-E values before design, economic, regulatory, or configuration-selection interpretation.

Monthly feed mass remains controlled in `MonthlyMass` or `GrassAvailability`; composition remains in `FeedMeasurements` or `GrassMeasurements`. Each month is simulated as an independent steady state. Annual totals use that month's operating hours, and key equipment is reported at peak month times the workbook safety factor.

## Engineering Methods

Real ThermoSTEAM chemicals are used where defensible. Formula-balanced products and exchange-site equivalents support conservation without claiming exact commercial mineral identity.

- `T701` reports residence-time volume, configurable cylindrical dimensions, mixer power, and a class-E feed-to-ambient heat-loss estimate.
- `S701` applies component-class particulate capture and derives one mother-liquor entrainment fraction from cake moisture; screw press, decanter, and belt-filter labels are selectable but need separate calibration data.
- `R711` enforces `Mg + NH4 + PO4 + 6 H2O -> struvite` and cannot exceed any reactant.
- `R712` supports explicit formula balances for calcium phosphate, dicalcium phosphate, or hydroxyapatite bookkeeping products.
- `A721` uses a pH-, temperature-, pressure-, gas-ratio-, and packing-responsive Level-1 stripping relation.
- `A722` forms ammonium sulfate or ammonium chloride stoichiometrically and reports a liquid solution, not dry crystals.
- `A731/R731` conserve Na/NH4 exchange-site equivalents and use a real recycle only for NR6.
- `E741` removes water non-selectively; `M741` applies pressure-responsive water recovery and species-class rejection.
- `W711/W712` and `D711/D712` are optional and disabled by default until product-finishing data exist.

Analytical indicators such as TAN, TKN, COD, TP, and TOC are calculated metrics rather than duplicate physical mass. Reports distinguish kg N/h from kg NH4/h, kg P/h from kg PO4/h, and elemental nutrient mass from product mass.

See [Phase 7 methodology](docs/phase7_methodology.md), [equations](docs/phase7_equations.md), [scenarios](docs/phase7_scenarios.md), and [products](docs/phase7_products.md).

## Validation

The default failure tolerance is `1e-6 kg/hr`. Phase 7 checks:

- every active Phase 7 unit, including exact reaction mass and elemental conservation;
- the complete digestate-plus-reagent boundary;
- reaction-adjusted components and total mass;
- water plus C, H, O, N, P, K, Mg, Ca, S, Cl, and Na;
- every persistent contaminant pool;
- non-negative flows and bounded capture/rejection/removal values;
- majority capture of configured particulate solids and majority centrate retention of soluble nutrients;
- process-order consistency and deterministic rebuilds.

Existing BioSTEAM cost warnings remain visible. At the structural scale, the Phase 6 compressor is far below its cost correlation range. Custom Phase 7 equipment has zero CAPEX because no approved correlation or vendor quotation exists.

## Outputs

`python -m Greenhub.main` writes under `Greenhub/results/`:

- `phase7_flowsheet.png`;
- `integrated_greenhub_flowsheet.png`;
- `integrated_greenhub_report.xlsx`;
- `integrated_process_area_summary.csv`;
- `model_completeness.csv` and `docs/audit/model_completeness.md`;
- `phase7_nutrient_recovery_report.xlsx`;
- `phase7_scenario_comparison.xlsx`;
- `phase7_limitations_and_data_needs.xlsx`;
- digestate, separation, phosphorus, ammonia, ion-exchange, potassium, product-quality, reagent, utility, energy, seasonal, assumption, and limitation CSVs;
- total/component and N/P/K/S/Cl elemental-balance CSVs.

The comparison workbook reports common engineering metrics but contains no score, winner, or MCDA result.

## Architecture

```text
Greenhub/
|-- integration.py            Canonical integrated facade and process-area views
|-- application/             Versioned contracts and transport-neutral run services
|-- parameters/              Canonical registry, precedence, overrides, and provenance
|-- scientific_equations.py  Approved typed equation registry; no expression evaluation
|-- integrated_reporting.py   Process-area and complete-plant report
|-- model_completeness.py     Unit-level maturity and missing-data register
|-- phase7_inputs.py           Workbook controls, quality gates, and provenance
|-- phase7_specifications.py   Pure stoichiometry, transfer, sizing, and pressure equations
|-- phase7_units.py            T701 through V741 BioSTEAM unit models
|-- phase7_systems.py          Actual-digestate NR0-NR7 factories and seasonal simulation
|-- phase7_metrics.py          Nutrient, product, utility, annual, and peak metrics
|-- phase7_validation.py       Unit/boundary/element/contaminant checks
|-- phase7_limitations.py      Permanent Phase 1-7 limitation register
|-- phase7_reporting.py        CSV and Excel outputs
|-- scenarios.py               F, PR, AD, BG, and NR scenario definitions
|-- systems.py                 Existing factories plus lazy Phase 7 entry points
`-- main.py                    Integrated executable with compatibility reports

api/
|-- app.py                    Thin versioned WSGI adapter
`-- __main__.py               Local synchronous development server
```

See [architecture](docs/architecture.md), [process areas](docs/process_areas.md), [scenario reference](docs/scenario_reference.md), and [migration guide](docs/migration_from_phase_architecture.md).

## Missing Data And Simplifications

- Feed composition, digestate speciation, recoveries, reagent doses, transfer parameters, and equipment values remain structural assumptions.
- Only explicit `Orthophosphate` is available to mineral reactions. Unspeciated dissolved-P, organic-P, and particulate-P pools are not invented as precipitable phosphate.
- The active thermo is not a rigorous electrolyte package and does not calculate activity coefficients, charge balance, Ksp, or full pH/alkalinity response.
- Precipitation lacks nucleation, growth, particle-size, and selected separator data.
- Base doses are empirical because digestate titration curves are unavailable.
- Stripping lacks GreenHub rate-based mass-transfer and carbonate-equilibrium calibration.
- Product washing, drying, storage, corrosion, and handling require vendor and experimental data.
- Evaporation does not solve salt solubility or scaling; membrane rejection and fouling are uncalibrated.
- Aggregate contaminants are conserved and co-reported, but compound-specific sorption, co-precipitation, and pathogen fate are unknown.
- The absent CHP/utility network prevents final heat recovery, grid demand, or net export conclusions.
- No custom Phase 7 CAPEX, final TEA/LCA, fertilizer compliance, water-reuse claim, uncertainty analysis, ranking, or MCDA is implemented.
- Seasonal storage capacity is unbounded unless `seasonal.storage_capacity_kg` is supplied; no defensible project capacity is currently available.
- Storage degradation, water loss, dry-matter loss, crop growth, and weather response remain explicitly unimplemented because no eligible project data or approved equations exist.
- Quasi-dynamic mode is a deterministic sequence of independent integrated steady-state simulations with a conserved storage state; it is not a continuous ODE model.

The detailed evidence gaps and validation routes are exported in `phase7_model_limitations.csv` and `phase7_limitations_and_data_needs.xlsx`.
