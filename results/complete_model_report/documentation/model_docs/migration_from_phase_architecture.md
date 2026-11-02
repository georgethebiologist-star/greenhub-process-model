# Migration From Historical Phase Architecture

## Canonical Alpha API

Use:

```python
from Greenhub import create_integrated_greenhub_system

model = create_integrated_greenhub_system().simulate()
digestion = model.process_areas["anaerobic_digestion"]
```

Meaningful builder arguments include `feed_preparation_scenario_id`, `protein_recovery_scenario_id`, `anaerobic_digestion_scenario_id`, `biogas_upgrading_scenario_id`, `scenario_id` for nutrient recovery, `selected_month`, and `process_order`.

## Preserved Compatibility

- `create_phase3_scenario()` through `create_phase7_scenario()` remain available.
- Workbook IDs `F*`, `PR*`, `AD*`, `BG*`, `NR*`, and order IDs remain unchanged.
- Historical module and workbook sheet names remain unchanged.
- Unit IDs remain unchanged.
- `create_greenhub_system()` still builds only the historical T101/S101 foundation; it was not silently redefined.
- Established phase-specific CSV and Excel reports continue to be generated alongside the integrated report.

The phase dataclasses are currently nested compatibility containers over one connected BioSTEAM graph. A future package move requires an explicit approval checkpoint, equivalence tests, and import deprecation notices.
