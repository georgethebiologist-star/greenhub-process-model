# GreenHub Membrane Protein-Recovery Dataset Audit

This package provides source-traceable inputs for microfiltration, ultrafiltration, concentration and diafiltration of grass and comparable biological streams.

Clean-water permeability is explicitly separated using `performance_category=clean_water` and must never be used as biomass-stream process flux.

The legacy datasets contained populated engineering priors for viscosity, osmotic effects, pump efficiency, cleaning recovery, component rejection and high-fouling-stream flux. These have been converted into blank `missing` records.

Direct clover-grass anchors include 22 L/m²/h average flux at VCF 3, 52% crude-protein rejection, 33% dry-matter rejection, and >99% rejection of chlorophyll-binding and photosystem proteins. No graph digitization or kinetic/fouling fitting was performed.

Load values only when feed, membrane, configuration, operating conditions, basis and transferability match the scenario.

`clover_grass_membrane_stream_composition_and_conditions_echers_2026_reference.csv`
adds a source-located 45-row extract of cultivated Danish clover-grass Table 1
stream DM/CP values, selected screw-press and membrane conditions, and reported
pigment concentrations. This is a single pilot-batch comparator for Phases 1,
3 and 4. It has no paired stream flows, so concentrations and pigment depletion
must not be interpreted as mass recovery. Explicitly unreported permeate
composition remains missing. The final diafiltered concentrate is a liquid
stream, not dried powder. The record is B-tier, D3/reference-only and has no
runtime/default link. The publisher states CC BY-NC 3.0; commercial reuse
requires a rights review.

## PR7 biostimulant membrane route

The `biostimulant_*.csv` registers contain the separate user-supplied screening
benchmarks, EUR price references, attributional CIP factors, retention matrix,
missing-pool evidence, and contextual membrane-energy references. They define clarified grass juice with no
fermentation. The fermented-juice viscosity record is retained as reference
only; resistance flux requires measured no-fermentation viscosity, sourced TMP,
and sourced `Cf/C0`. External drinking-water NF results are catalogued as
transferability context in `biostimulant_unmapped_pool_evidence.csv` and do not
fill retention gates for the chemically undefined GreenHub pools. The
`biostimulant_membrane_energy_references.csv` file records published water
filtration energy values for context; none are used as PR7 crossflow electricity
because feed and process configuration are not matched. The
`biostimulant_product_price_references.csv` file records a public 1,000 L
vegetable amino-acid hydrolysate listing in EUR as a non-equivalent market
comparator; it does not change the user-supplied PR7 price screen. The
`dataset_manifest.csv` records row counts and integration status for these
files. In a PR7 BioSTEAM run, every uncovered nonzero liquid pool is conserved
at the explicit `biostimulant_unresolved` outlet. This allows a closed mass
balance without assigning an unsupported membrane fate; validation blocks
complete PR7 product allocation, area, TEA revenue and LCA readiness until
retention evidence or a source-noted override is supplied.
