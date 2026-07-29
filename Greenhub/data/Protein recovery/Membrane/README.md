# GreenHub Membrane Protein-Recovery Dataset Audit

This package provides source-traceable inputs for microfiltration, ultrafiltration, concentration and diafiltration of grass and comparable biological streams.

Clean-water permeability is explicitly separated using `performance_category=clean_water` and must never be used as biomass-stream process flux.

The legacy datasets contained populated engineering priors for viscosity, osmotic effects, pump efficiency, cleaning recovery, component rejection and high-fouling-stream flux. These have been converted into blank `missing` records.

Direct clover-grass anchors include 22 L/m²/h average flux at VCF 3, 52% crude-protein rejection, 33% dry-matter rejection, and >99% rejection of chlorophyll-binding and photosystem proteins. No graph digitization or kinetic/fouling fitting was performed.

Load values only when feed, membrane, configuration, operating conditions, basis and transferability match the scenario.
