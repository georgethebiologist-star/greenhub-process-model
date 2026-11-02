# Scientific Assumptions

The master workbook is the quantitative source of truth. This page summarizes cross-cutting assumptions; detailed equations remain in the historical methodology files so they are not duplicated.

- Monthly operation is represented by independent steady states, not hourly dynamics, inventory scheduling, or transient control.
- Structural-test inputs demonstrate connectivity and conservation; they are not final measured, calibrated, design, or commercial values.
- Real ThermoSTEAM chemicals are used where defensible. Lumped proteins, solids, contaminants, biomass, and analytical pools are explicit pseudo-components or metadata and do not imply exact molecular identity.
- ThermoSTEAM property calculations do not make empirical precipitation, absorption, gas partitioning, or stripping models rigorous equilibrium models.
- Protein recovery uses empirical pool transfers and documented reagent bookkeeping; project titration and recovery data are still required.
- Anaerobic digestion uses a hybrid component/COD fate model and is not ADM1.
- Biogas upgrading uses technology-specific screening models; final compression, storage, grid injection, CHP, and shared utilities are incomplete.
- Nutrient reactions use explicit limiting-species and formula balances, not a rigorous electrolyte activity model.
- Custom-equipment CAPEX is missing where no approved correlation or quotation exists. A numerical zero must not be interpreted as free equipment.
- Product eligibility, fertilizer compliance, water reuse, TEA, LCA, uncertainty, ranking, and MCDA are outside the current alpha claim.

See `docs/phase2_methodology.md` through `docs/phase7_methodology.md` and `docs/phase7_equations.md` for implementation-specific detail.
