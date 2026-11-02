# Recent Development Handoff

## What was added

- `Greenhub.storage.StorageModel`: a small inventory helper with optional capacity and optional first-order degradation.
- `Greenhub.logistics`: lightweight dataclasses and helpers for simple biomass transport calculations.
- Focused tests for storage, seasonal storage degradation helper behavior, and logistics.
- Documentation for storage degradation and logistics behavior.
- An opt-in seasonal storage degradation parameter and controller helper. No degradation is applied when the parameter is absent or blocked.

## How to use

Storage:

```python
from Greenhub.storage import StorageModel

storage = StorageModel(capacity_kg=10000.0, initial_inventory_kg=500.0, degradation_rate_per_day=None)
step = storage.simulate_step(inflow_kg=200.0, outflow_kg=50.0, days=7.0)
```

Logistics:

```python
from Greenhub.logistics import LogisticsScenario, VehicleSpec, simulate_logistics

scenario = LogisticsScenario(total_biomass_kg=1000.0, distance_km=10.0)
vehicle = VehicleSpec(
    payload_kg=500.0,
    fuel_consumption_l_per_100km=30.0,
    fuel_cost_per_l=1.5,
    fuel_emission_kg_co2_per_l=2.68,
)
result = simulate_logistics(scenario, vehicle)
```

## Not yet integrated

- Logistics is not integrated into the API, seasonal controller, or phase modules.
- Storage degradation is only an opt-in seasonal helper, not a broader reporting or API feature.
- No validated degradation, fuel, cost, distance, or emissions datasets were added.

## Next recommended step

Decide the intended public integration point for logistics and seasonal degradation reporting before adding more calculations.

## Tests run

- `pytest -q --basetemp=.pytest_tmp tests/test_storage.py tests/test_storage_integration.py tests/test_logistics.py`
- Result: not run in this environment because `pytest` is not available on PATH.
- Fallback attempt: `python -m pytest -q --basetemp=.pytest_tmp tests/test_storage.py tests/test_storage_integration.py tests/test_logistics.py`
- Result: not run because `python` is not available on PATH.
