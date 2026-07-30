# Input Data Reference

The active master workbook is `Greenhub/data/greenhub_feed_inputs.xlsx`.

| Sheet | Purpose |
|---|---|
| `ReadMe` | Workbook instructions and conventions |
| `ModelControl` | Selected month, process scenarios, process order, and structural-test flags |
| `MonthlyMass` | Monthly liquid-fraction availability |
| `FeedMeasurements` | Measured-liquid composition and physical properties |
| `Parameters` | Foundation settings |
| `GrassAvailability` | Monthly roadside-grass availability |
| `GrassMeasurements` | Grass composition and characterization |
| `Phase3Parameters` | Historical preparation and primary-separation controls |
| `Phase4Parameters`, `AcidTitration`, `ProteinRecoveryData` | Historical protein-recovery controls and observations |
| `Phase5Parameters` | Historical digestion controls |
| `Phase6Parameters` | Historical biogas-conditioning and upgrading controls |
| `Phase7Parameters` | Historical digestate and nutrient-recovery controls |

Historical sheet names are retained for compatibility. Loaders validate required columns, types, units, ranges, scenario/month applicability, provenance class, and required blanks. Optional absent measurements remain absent and cannot create material or economic value.

The source hierarchy is measured project data, calibrated project data, peer-reviewed literature, documented engineering estimates, then explicit placeholders. Structural-test mode currently uses many quality-class E values.

Seventeen CSV files under `Greenhub/data/Protein recovery/` are inventoried in `docs/audit/dataset_inventory.md`. They remain disconnected because several required fermentation, membrane, and drying values are blank, validators are absent, and one cross-file dataset name is inconsistent. Their presence is not treated as scientific readiness.
