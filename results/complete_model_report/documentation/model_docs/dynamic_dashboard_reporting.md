# Dynamic complete dashboard reporting

This is an opt-in tool prototype around the existing isolated complete BioSTEAM
proxy chain. Open **Dynamic proxy**, then **Run proxy scenario**. The empirical
model and its existing workflow are unchanged. No static frontend fallback is
substituted if the proxy API fails.

## Runtime and boundary

Run `.venv\Scripts\python.exe -m api` from the repository root and `npm run dev`
from `frontend`. The browser client uses `VITE_GREENHUB_API_URL`, defaulting to
`http://127.0.0.1:8000/api/v1`. The frontend Express demo server is not the
scientific proxy API; this feature requires the Python API.

`dynamic_complete_scenario.py` validates planning inputs and creates the supply
schedule. `dynamic_complete_reporting_service.py` runs each active month at its
scheduled feed rate, builds the isolated complete BioSTEAM system, and requires
its parity/readiness checks before reporting downstream values. The ledger is
the authoritative reference, including metadata pools absent from chemical
streams. No global empirical flowsheet is connected. No artifacts are written
by these endpoints; responses contain no local absolute paths.

Press cake is always an external product, never AD feed. Juice and digestate
are intermediate flows and must not be added to final products as if they were
independent mass outputs. Recovered protein is the protein fraction of dried
product, not an additional product. Reagent/carrier mass can enter recovery
products from outside the feed boundary. Final residual liquor means the last
selected recovery unit's residual; without recovery it equals digestate.

## Biomass schedule

The baseline is **30,000 tonnes fresh grass available and processed per year**,
100% collection/refinery utilization, April 15–November 15 inclusive, a July 31
peak and a 55-day standard deviation. These are planning assumptions, not
measured collection records. Full-year mode extends the supply season to
January 1–December 31 of the selected year. Active months control processing,
not availability; no storage or carry-over between months is represented.

Monthly availability integrates a normal CDF between the actual collection
dates in each month, then normalizes the full season to annual availability.
Availability does **not** shrink when the processing target or fraction falls.

The requested processing budget is:

`min(annual_processed_biomass_tonnes, annual_available_biomass_tonnes * collection_refinery_fraction)`

For annual-input mode, solve a common monthly ceiling `C` such that:

`sum(min(month_available, C)) = achievable_requested_budget`

Only selected active months can process. This is a **monthly tonnes ceiling**,
not constant hourly equipment capacity; it deliberately makes a monthly
plateau. Hourly-input mode additionally limits each month by
`feed_kg_per_hr * operating_hours / 1000`. In either mode the annual target and
collection fraction still bound the annual total. Infeasible targets produce
an explicit `unmet_target_tonnes` warning, not rescaled availability.

Available, processed, unused and utilization are all reported per month.
`utilization_fraction = processed / available` (zero where no supply exists).
`basis_feed_kg_per_hr = processed_tonnes * 1000 / operating_hours`.
Operating hours are 24 times active collection days: baseline April has 384
hours and November has 360. Continuous operation on those days is an explicit
assumption; storage, downtime and capacity-dependent yields remain gaps.

## Units and annualization

| Quantity | Hourly | Monthly | Scheduled annual |
| --- | --- | --- | --- |
| Mass | kg_per_hr | tonnes_per_month | tonnes_per_year |
| Gas | m3_per_hr | m3_per_month | m3_per_year |
| Electricity | kWh_per_hr | MWh_per_month | MWh_per_year |
| Heat | MJ_per_hr | GJ_per_month | GJ_per_year |

Multiply hourly rates by each actual period's operating hours; divide mass,
electricity and heat by 1,000. Gas needs no additional factor. Core heat in
kWh/h is converted to MJ/h with 3.6 before aggregation. Gas is the core's normal
volume proxy; biomethane volume includes the modeled non-methane fraction.
The separate `biomethane_methane` metric provides recovered CH4 volume.

Annual cards sum scheduled months, including zero off-season production. Their
hourly values are operating-hour-weighted means, not calendar-year averages.
`annualized_estimate`, only when requested, multiplies the mean operating rate
by 8,760 or 8,784 hours. It is **not biomass-constrained** and is displayed
separately. `summarize_biosteam_grid()` supports existing monthly grids: the
legacy May–November grid has 214 days; it is not silently extended to a year.

## API and controls

| Method | Endpoint | Output |
| --- | --- | --- |
| GET | /api/v1/dynamic-complete/options | Canonical defaults, method options and analysis factors |
| GET | /api/v1/dynamic-complete/default-summary | Cached baseline report, no persistent run/artifact |
| POST | /api/v1/dynamic-complete/scenario-summary | New isolated scenario report |
| GET | /api/v1/dynamic-complete/assumptions | Baseline process and analysis evidence |

Example POST body (omitted scenario fields use documented defaults):

```json
{
  "scenario": {
    "annual_processed_biomass_tonnes": 15000,
    "collection_refinery_fraction": 1,
    "protein_method": "isoelectric",
    "drying_method": "spray_drying_proxy",
    "target_product_moisture": 0.15,
    "gas_route": "water_scrubbing",
    "allow_assumptions": true
  },
  "analysis_factors": {"electricity_price": 0.2}
}
```

Controls cover annual available/processed tonnes, collection fraction, annual
or hourly feed input, active months, season/peak dates and spread, full-year
supply, optional annualization, one protein method, one drying method, product
moisture, one gas route, and resource recovery checkboxes. Heat and generic
protein methods require an explicit recovery fraction in [0, 1]. Heat uses a
generic mass recovery closure; extraction heating/reagents are not modeled.
Recovery checkboxes execute in canonical separation → ammonia → phosphorus →
potassium/water → ion exchange order regardless of click order. Unknown
fields, multiple protein/gas selections, non-finite/invalid values, and press
cake routing to AD return user-readable HTTP 422 errors.

The dashboard defaults to spray-drying proxy so energy is visible. `mass_only`
now omits dryer energy and warns that zero is not an energy-free drying claim.
Freeze drying uses its explicit engineering electricity assumption. The core's
legacy default remains `mass_only`; old generated CSVs are historical and were
not silently overwritten. Heat extraction honors a supplied recovery fraction;
its legacy direct-core fallback remains available, but the dashboard requires
an explicit value.

## Traceability and readiness

Reports expose monthly/hourly metrics, scheduled annual totals, optional
annualization, selected methods, chart units, supply schedule, evidence,
warnings, blockers, BioSTEAM parity/boundary checks, and separate analysis.

Each evidence row has `policy_id`, `name`, `value`, `unit`, `source_status`,
`certainty_class`, `source_file`, `source_id` and `warning`. Upstream feedstock
reconciliation, extraction evidence, pooling, engineering closures and
downstream values are preserved, with full provenance expandable in the UI.
Equal records are deduplicated and collect `time_labels`; changed seasonal
values remain separate. Counts mean **unique evidence records**, not independent
measurements or citations. Unselected downstream closure-register entries are
marked `usage=closure_registry`; they are inspectable, not claimed as selected
unit inputs. Top assumptions are qualitative output drivers, not a computed
sensitivity ranking. Warning/blocker counts count occurrences; dictionaries
also expose distinct messages. Analysis evidence is counted separately.

`validated_simulation_ready` and `can_drive_simulation` remain false. BioSTEAM
parity tests numerical consistency with proxy ledgers, not empirical validity.
Strict mode reports actual core blockers and withholds downstream totals and
economic/environmental calculations (`null`/unavailable). The core's upstream
assumption scaffold is retained only to inspect evidence and blockers; it is
never presented as strict-mode production. Changing controls labels existing
results as stale until the next successful run.

## Baseline example

2026 April 15–November 15, 30,000 t/year, isoelectric, spray drying, 15% moisture,
water scrubbing and all recovery methods, assumptions enabled:

| Output | Scheduled annual total |
| --- | ---: |
| Feed processed | 30,000 t |
| External press cake | 13,125 t |
| Dried protein product / contained recovered protein | 109.95 / 58.48 t |
| Raw biogas / biomethane | 1,435,432 / 1,393,971 m³ |
| Digestate to recovery | 12,036.23 t |
| Ammonium / struvite candidates | 175.41 / 135.98 t |
| Potassium concentrate / recovered water | 1,808.84 / 4,791.84 t |
| Included gross electricity / heat demand | 420.73 MWh / 1,512.10 GJ |
| Final residual liquor | 3,793.87 t |

| Month | Processed t | Dried product t | Biomethane m³ |
| --- | ---: | ---: | ---: |
| April | 731.5 | 3.76 | 47,796 |
| May | 2,801.3 | 14.38 | 183,037 |
| June | 4,900.1 | 16.21 | 205,227 |
| July | 6,779.3 | 22.42 | 283,933 |
| August | 6,712.0 | 22.20 | 281,114 |
| September | 4,756.8 | 18.24 | 231,408 |
| October | 2,666.7 | 10.23 | 129,726 |
| November | 652.3 | 2.50 | 31,731 |

These numbers are proxy calculations, not validated performance forecasts.
Missing front-end, extraction and recovery utilities make energy totals partial.

## Focused verification

```powershell
New-Item -ItemType Directory -Path tmp -Force
.venv\Scripts\python.exe -m pytest -q tests/test_dynamic_complete_reporting.py tests/test_dynamic_complete_proxy.py tests/test_dynamic_complete_biosteam.py tests/test_api_v1.py --basetemp=tmp/pytest_dynamic_reporting
cd frontend
npm run lint
npm run build
```

There is no frontend test runner in the existing project; none was added.
Backend tests assert the frontend-visible data contract. Browser verification
covers baseline cards/charts, a 15,000 t/year capped schedule with unchanged
availability, controls submitting updated requests, evidence field visibility,
and strict-mode unavailable totals. Chart data tables provide accessible
alternatives to visual graphs.

Verification on 2026-09-16: **56 focused backend tests passed**, with 15 existing
dependency warnings. `npm run lint` and `npm run build` passed. Vite reports a
bundle-size warning (about 645 kB uncompressed), not a build failure. A separate
full-year proxy check also processed 30,000 tonnes with all parity checks ready.

Before a validated tool release: collect site-specific yields and utilities,
validate AD kinetics and elemental/speciation routing, verify gas reference
conditions and technology performance, characterize product quality, close
reagent/utility inventories, introduce operating/storage constraints, and add
production deployment/concurrency/security review. This change does not deploy
the website or activate a validated simulation.
