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

- No literature-derived degradation rates are supplied. Users must provide
  `degradation_rate_per_day` for their scenarios or connect an external dataset.
- This module is deliberately independent but has now been integrated as an opt-in
  feature of the seasonal controller. To preserve backwards compatibility, the
  seasonal controller will not apply degradation unless a resolved parameter
  `seasonal.storage_degradation_rate_per_day` is supplied (via parameter overrides
  or the parameter-resolution process). If that parameter is absent or blocked,
  no degradation is applied and a clear limitation is recorded in the per-step
  provenance.
- Evaporation, dry-matter loss, chemical transformation, temperature dependence,
  and weather response are out of scope in this initial slice.

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

- Add validated degradation-rate datasets with provenance (literature or pilot data).
- Decide whether the opt-in seasonal degradation hook should become part of the
  public seasonal workflow, API, or reporting surface.
- Expand to include temperature- and moisture-dependence, and multi-pool
  (dry-matter/water) accounting when data permit.
