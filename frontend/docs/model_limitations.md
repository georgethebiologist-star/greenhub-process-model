# Model Limitations

The machine-readable unit-level register is `Greenhub/results/model_completeness.csv`; the human summary is `docs/audit/model_completeness.md`.

Highest-priority limitations are:

- The available Git history cannot verify the reported Phase 6-to-7 deletion; earlier commits or patches are required for a definitive restoration audit.
- No active CHP or plant-wide utility-production network exists. Heat recovery and generated electricity default to zero unless a verified interface is supplied.
- Project feed and digestate composition, uncertainty, and seasonal laboratory characterization are incomplete.
- Protein, digestion, upgrading, and nutrient-recovery performance require project or pilot validation.
- Several unit models conserve mass and report design indicators but lack vendor costs, lifetime, maintenance, consumables, or validated operating ranges.
- The thermodynamic package is not a rigorous electrolyte, acid-base, precipitation, or digestate-speciation model.
- The added protein-recovery CSV datasets are not calculation-ready and remain disconnected.
- Built-in BioSTEAM cost correlations may be extrapolated outside validated ranges at current structural scale; warnings remain visible.

No unit is currently classified E5. Passing conservation tests establishes bookkeeping consistency, not engineering validation or commercial readiness.
