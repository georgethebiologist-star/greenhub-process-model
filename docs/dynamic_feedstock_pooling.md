# Dynamic Whole-Feed Pooling

## Boundary

This policy pools whole fresh grass before pressing. It does not partition material into press liquid and press cake, register a feed profile, create model overrides, or activate protein extraction, anaerobic digestion, or nutrient recovery.

## Default Literature Policy

The opt-in `default_literature_pool_policy()` uses the user-supplied literature assumptions below. Means are calculation defaults; source low/high values remain sensitivity metadata.

- Protein: 50% soluble and 50% insoluble. Source: <https://pmc.ncbi.nlm.nih.gov/articles/PMC11741079/>. Both pools carry the surrogate formula `(C4.94H7.76O1.52N1.28S0.04)n` as metadata.
- WSC: raw means are 0.60 fructan, 0.25 sucrose, and 0.125 combined hexose. Their sum is 0.975, so defaults are normalized to 0.6153846, 0.2564103, and 0.1282051. Source ranges remain 0.50-0.70, 0.20-0.30, and 0.10-0.15. Source: <https://www.nzgajournal.org.nz/index.php/ProNZGA/article/download/2826/2454/4219>.
- Leaf dry matter: structural and non-structural raw means are 0.525 and 0.475, already summing to one. Source ranges remain 0.35-0.70 and 0.30-0.65. Source: <https://www.sciencedirect.com/science/article/pii/S0022030213003780>.
- Structural fiber: raw means are 0.20 hemicellulose, 0.24 cellulose, and 0.04 lignin. Their sum is 0.48, so defaults are normalized to 0.4166667, 0.50, and 0.0833333. Source ranges remain 0.15-0.25, 0.18-0.30, and 0.02-0.06.

Fructan, cellulose, hemicellulose, and lignin formulas are surrogate metadata only. In particular, the lignin expression is representative and does not declare an exact molecular species or rigorous thermodynamic identity.

## Calculation

`total_solids_wet_basis` converts dry-basis feedstock pools to wet-feed fractions. Ash, total protein, and WSC come from the resolved dynamic bundle. The structural default is allocated only while dry matter remains available. Evidence values are never silently rescaled. Any remainder after ash, protein, WSC, and structural-fiber allocation is reported as `residual_unallocated_dry_matter_wet_fraction`.

Parent `structural_fiber_wet_fraction` is a subtotal and is not counted again when validating the sum of cellulose, hemicellulose, lignin, water, ash, protein, sugars, and residual mass.

## Existing Component Mapping

- Water is represented by feed-profile `moisture_fraction` and by `Water` in the pool result.
- Ash maps to `Ash`.
- Soluble and insoluble protein map to `SolubleProtein` and `SuspendedProtein`.
- Sucrose maps to `Sucrose`.
- Combined hexose is split 50/50 into `Glucose` and `Fructose` as a report-only
  assumption until a source-specific ratio is available. The parent hexose
  subtotal remains metadata for traceability.
- Cellulose, hemicellulose, and lignin map to their existing components.
- Fructan has no exact existing component.
- Residual unallocated dry matter has no exact component.

Fructan, the parent hexose subtotal, and residual dry matter remain
metadata-only, so the pooled adapter row cannot yet drive simulation.

## Downstream Limits

Protein extraction still needs press partition coefficients, solubilization behavior, and recovery performance. Anaerobic digestion still needs reviewed biodegradability, COD, BMP, and kinetic mappings. Nutrient recovery still needs nitrogen, phosphorus, potassium, sulfur, and mineral speciation. None of those calculations are activated by whole-feed pooling.
