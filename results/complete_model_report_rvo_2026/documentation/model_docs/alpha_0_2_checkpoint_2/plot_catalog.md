# Plot Catalog

| Plot ID | Area | Y unit | Availability | Source fields |
|---|---|---:|---|---|
| `SYS-AREA-MASS` | Integrated system | kg/h | All completed runs | process-area outlet streams and stream total mass |
| `VALIDATION-RESIDUALS` | Integrated system | kg/h or reported balance unit | All completed runs | balance residuals |
| `SYS-UNIT-POWER` | Shared utilities | kW | All completed runs | unit power |
| `DATA-READINESS` | Data governance | count | All completed runs | dataset readiness counts |
| `PR-PRECIP-RECOVERY` | Protein recovery | fraction | `PR1` plus `literature_default` | R401 acid-recovery design result |

Each run exports plot metadata/data as JSON and CSV. Available non-empty plots also export PNG and SVG using Matplotlib's headless `Agg` backend. Stable metadata includes plot ID, title, area, axis labels and units, scenario, run ID, source fields, warnings, and availability.

These plots report implemented calculations only. They do not imply optimization, uncertainty, TEA, LCA, or configuration ranking.
