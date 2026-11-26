# Current PR1 literature pathway

The checkpoint release notes in this folder describe the earlier `REC-001` activation as it existed at that checkpoint. The current resolver uses the later ryegrass records below; see `Greenhub/parameters/loaders.py` and `Greenhub/data/advanced_model/parameter_activation_registry.csv` for the active registry entries.

## Current selection

For PR1 in `literature_default` or `expert_override` mode, GreenHub selects:

- `REC-005`: 0.38 precipitated nitrogen per total nitrogen in cleared ryegrass juice, from la Cour et al. (2019), DOI [10.3389/fsufs.2019.00112](https://doi.org/10.3389/fsufs.2019.00112). The row records Figure 5, the conclusion, and precipitation methods as its source locations.
- `REC-006`: pH 4.5, the upper endpoint of the paper's reported pH 4.0–4.5 interval.

The process model applies the recovery fraction to its lumped `SolubleProtein` pool. The paper's denominator is total nitrogen, including non-protein nitrogen, so this mapping is a screening proxy. The study used cultivated ryegrass juice, double pressing with added water, clarification, and laboratory centrifugation; these differ from GreenHub's roadside feed and process boundary. Do not interpret the result as a measured GreenHub protein recovery.

## Exclusions and validation needs

Structural mode continues to use the workbook placeholder. PR3 remains structural; this evidence does not establish combined heat/wash performance. The source provides no GreenHub titration curve, pH-response kinetics, equipment sizing, power, or CAPEX. Project measurements must validate feed applicability, protein and nitrogen balances, pH, and recovered-product composition before design or economic use.

The earlier 0.34 `REC-001` calculation remains documented as a historical checkpoint in [the release notes](release_notes.md) and [the numerical comparison](numerical_comparison.md); it is not the current resolver selection.
