# Process Areas

The default structural configuration is `F2/PR3/AD1/BG2/NR4`, order `A`. Unit IDs remain unchanged during the compatibility migration.

| Process area | Default active units | Principal boundaries |
|---|---|---|
| Feedstock and Characterization | No physical unit | Workbook feed to characterized biomass stream |
| Feed Preparation and Primary Separation | `U101`, `U201`, `S201`, `C301` | Feed to clarified protein-rich liquid, fibre cake, rejects, and sludge |
| Protein Recovery | `M401`, `H401`, `R401`, `C401`, `W401`, `D401`, `DR401`, `M402`, `M403` | Clarified liquid to dry protein, depleted liquid, filtrates, and dryer exhaust |
| Anaerobic Digestion | `M501`, `H501`, `R501`, `V501` | Digester feed to raw biogas, digestate, and uncaptured gas |
| Biogas Conditioning and Upgrading | Scenario-dependent `G6xx` through `M699` | Raw biogas to biomethane, reject gas, wastewater, and spent material |
| Digestate Treatment and Nutrient Recovery | Scenario-dependent `T701` through `M799` | Digestate to solids, nutrient products, residual liquid or water, wastewater, and off-gas |
| Shared Utilities and Supporting Operations | None | Explicit missing CHP and plant-wide utility interfaces |

Every `ProcessAreaView` exposes `units`, `inlet_streams`, `outlet_streams`, `assumptions`, `warnings`, `validation`, `metrics`, and `reports`. Empty shared-utility units are intentional evidence of a missing model, not evidence of zero utility demand.

Engineering maturity is recorded per active unit in `docs/audit/model_completeness.md` and `Greenhub/results/model_completeness.csv`. Conservation, sizing, and utility calculations do not by themselves establish E5 validation.
