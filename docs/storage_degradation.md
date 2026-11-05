# Storage Degradation Framework (Alpha additive)

What was added

- Greenhub.storage.StorageModel: a lightweight, additive storage inventory model that
  tracks inventory (kg), optional capacity (kg), and optional first-order degradation
  (1/day).
- Each simulation step returns explicit provenance describing which methods were
  applied and any limitations or missing data indicators.
- Focused unit tests under `tests/test_storage.py` demonstrating the not-implemented
  behavior and a basic first-order loss when a degradation rate is provided.

Design choices and assumptions

- Missing degradation parameters are treated as "not implemented" — the model
  does not invent rates or silently convert missing values to zero. This preserves
  scientific traceability and prevents hidden mass losses.
- When `degradation_rate_per_day` is provided, a first-order (exponential) decay
  is applied: mass_after = mass_before * exp(-k * days). This is a commonly-used
  simple representation; any calibrated or mechanistic model must supply its own
  rate or connect a different degradation model.
- Withdrawals are applied before degradation in the step to match a perfectly-mixed
  withdrawal assumption used elsewhere in the seasonal controller.
- Capacity is enforced after degradation; overflow is reported in the step `overflow_kg`.

Limitations and remaining gaps

- The generic `component_retention` path has no validated default degradation
  rate. The separate `grass_reactions` package contains 23 explicit reaction
  rows, but its rate constants are assumed or indirectly transferred, not
  validated roadside-grass kinetics. They remain quality E and opt-in; their
  low/high values are scenario bounds, not confidence intervals. The FAIR
  `Master_Inputs` sheet/catalog indexes every reaction and provenance record,
  but is a generated read-only snapshot, not a runtime input source.
- The seasonal controller has two mutually exclusive opt-in paths. If a request
  supplies `storage_conditions`, that selected storage model is applied to arrivals
  and carried inventory. In that case the scalar registry parameter
  `seasonal.storage_degradation_rate_per_day` is not also applied (avoiding double
  counting). If no `storage_conditions` are supplied, the scalar parameter can
  apply a first-order wet-inventory loss; if it is absent or blocked, no such loss
  is applied and the per-step result reports the limitation. Storage capacity is
  independently optional and must be explicitly supplied to calculate overflow.
- The opt-in package includes stoichiometric chemical transformations and
  explicit temperature/moisture assumptions, but not a validated evaporation,
  weather, leaching, or protein-quality model. Its Q10, moisture activity,
  reaction rates, and some transformations remain assumptions; output
  completeness flags must not be read as validation or complete emissions
  accounting.
- Published grass-silage studies provide useful contextual bounds, but do not
  directly identify the GreenHub wet-inventory rate or roadside-grass reaction
  constants. Williams et al. (1997; DOI
  [10.1111/j.1365-2494.1997.tb02348.x](https://doi.org/10.1111/j.1365-2494.1997.tb02348.x))
  estimated only 0.3% and 0.9% aerobic dry-matter loss over 120–150 days in two
  carefully sealed ryegrass bunker silos. Rees (1982; DOI
  [10.1002/jsfa.2740330602](https://doi.org/10.1002/jsfa.2740330602)) reported
  laboratory relationships between temperature rise, duration/depth, and
  aerobic grass-silage dry-matter loss. Neither result is a transferable
  first-order loss constant for fresh roadside grass, and neither is used as a
  GreenHub default. Storage capacity is likewise a project/equipment input, not
  a literature constant. These two seasonal registry fields therefore remain
  explicitly missing until a project value or a validated, basis-matched model
  is supplied.

## Evidence reviewed (2026-11-05)

- Williams, A.G., Hoxey, R.P. & Lowe, J.F. (1997), “Changes in temperature and
  silo gas composition during ensiling, storage and feeding-out grass silage,”
  *Grass and Forage Science* 52(2), 176–189. DOI above. Evidence describes two
  approximately 12 t ryegrass bunkers and explicitly notes that loss may be
  lower than farm-silo losses because sealing was unusually thorough.
- Rees, D.V.H. (1982), “The aerobic deterioration of grass silage and its effect
  on the water-soluble carbohydrate and the associated heat production,”
  *Journal of the Science of Food and Agriculture* 33(6). DOI above. The
  reported lab equations depend on exposure/temperature geometry and are not
  copied into the current storage model.
- Evidence class for those publications is literature (B) as source records;
  applicability to the present roadside-grass process is low. This distinction
  does not upgrade the model's kinetic assumptions, which remain E.

Provenance and traceability

- Each call to `simulate_step` returns a `provenance` dict with keys `methods`,
  `limitations`, and `sources` describing what was applied and what was missing.
  This makes it suitable for inclusion in the model's `assumptions` or `warnings`
  collections by the caller.

How to use (example)

```python
from Greenhub.storage import StorageModel

s = StorageModel(capacity_kg=10000.0, initial_inventory_kg=500.0)
step = s.simulate_step(inflow_kg=200.0, outflow_kg=50.0, days=7.0)
print(step['inventory_kg'], step['provenance'])
```

Next steps for v1.0

- Obtain roadside-grass storage time series (mass, DM, WSC, acids, protein-N,
  methane/CO2/N losses) under defined moisture, temperature, packing, and oxygen
  conditions; fit and validate pool-specific rates before replacing E-class
  package values.
- Decide whether the opt-in seasonal degradation hook should become part of the
  public seasonal workflow, API, or reporting surface.
- Expand to include temperature- and moisture-dependence, and multi-pool
  (dry-matter/water) accounting when data permit.
