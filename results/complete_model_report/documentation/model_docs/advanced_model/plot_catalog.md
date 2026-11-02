# Advanced Plot Catalog

Checkpoint 1 generates no advanced scientific plots. The catalog defines useful plots
and their data gates so later work does not manufacture graphs from incomplete data.

| Plot ID | Purpose | Required structured data | Initial status |
|---|---|---|---|
| SYS-AREA-MASS | Process-area mass input/output | ProcessAreaResult boundaries | planned |
| SYS-COMPONENT-FATE | Component and water fate | Stream/component result table | planned |
| SYS-ELEMENT-FATE | C/N/P/K products and residuals | Elemental balance records | planned |
| SEASON-FEED | Monthly availability and composition | Validated feed schedule | planned |
| PRETREAT-RELEASE | Release and energy versus intensity | Eligible pretreatment observations/model | blocked by data gate |
| PROTEIN-PH | Protein solubility/recovery versus pH | Eligible titration and pH-response model | blocked by data gate |
| PROTEIN-DRYING | Moisture, duty, temperature, quality | Validated drying state model | blocked by data gate |
| AD-STATES | COD/substrate/gas/inhibition over time | Validated dynamic AD state results | blocked by data gate |
| BG-PERFORMANCE | Methane purity, recovery, slip, power | Upgrading structured results | planned |
| NR-RECOVERY | Nutrient recovery, purity, residuals | Nutrient area result records | planned |
| UTIL-BALANCE | Unit power, heating, cooling and net balance | Shared utility records | blocked by missing utility area |
| VALIDATION-RESIDUALS | Mass/element residuals and data gaps | ValidationIssue and balance records | planned |

Every implemented plot will carry plot ID, title, axes and units, process area,
scenario, run ID, data source, assumptions, warnings, and stable PNG/SVG/CSV paths. Plot
services will consume structured result objects, never scrape workbooks.

The machine-readable `plot_manifest.json` is an inactive Checkpoint 1 catalog; it does
not claim that image files exist.
