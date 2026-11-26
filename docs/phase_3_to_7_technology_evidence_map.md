# Phase 3–7 technology and evidence map

These names describe technology families, not a migration of saved IDs. The
existing F, PR, AD, BG and NR scenario IDs and API selections remain stable.
The GreenHub roadside-grass pathway is one material-specific application of
the families. A technology equation can transfer to another residual stream;
its feed composition, recovery, fouling, kinetics, capacity and product-grade
parameters generally cannot transfer without checking the stated basis.

| Existing phase | Technology family | Current route choices | Transferable evidence | Material/site-specific evidence still needed |
| --- | --- | --- | --- | --- |
| 3 | Pretreatment and fractionation | F0 bypass; F1 mechanical cleaning, size reduction, screw pressing and centrifugation. F2/F3 PEF are retired. | Mechanical/electrical power equations, mass-conservation structure, equipment design envelopes. | Contaminant and particle-size distribution; paired feed/juice/cake flow, DM and component assays; press settings, juice yield and power on each feedstock. |
| 4 | Protein recovery | PR0 bypass; PR1 acid precipitation; PR2 heat coagulation; PR3 combined acid/heat. PR4 fermentation, PR5 CO₂ precipitation, PR6 ultrafiltration and PR7 biostimulant membrane routes remain inactive or gated. | Acid-base balance, heat capacity, membrane flux/area and dryer heat/mass equations where applicable. | Juice titration, soluble/insoluble protein partition, pH/temperature-specific recovery, reagent use, precipitate quality, membrane fouling and drying behaviour. |
| 5 | Anaerobic digestion | AD0 bypass; AD1 mesophilic post-protein CSTR; AD2 direct mesophilic CSTR; AD3 thermophilic CSTR. AD4 two-stage and AD5 high-rate are reserved. | COD and elemental balance methods, CSTR volume/HRT/OLR framework, vessel heat-loss equation. | BMP and continuous-reactor kinetics on the actual routed residue, inhibition, gas composition, digestate flow, inlet temperature and local heat-loss/insulation checks. |
| 6 | Biogas upgrading (within the digestion-to-biomethane route) | BG0 bypass and active upgrading alternatives BG2–BG4; other BG routes are gated by their own readiness checks. | Gas property and separation-balance equations, vendor operating envelopes. | Raw/product/off-gas composition and metered methane recovery/slip, specific electricity and replacement consumables for the chosen feed gas and unit. |
| 7 | NPK recovery | NR0 bypass; NR1 solids separation; NR2 struvite; NR3 ammonia stripping/capture; NR4 integrated N/P; NR5 calcium phosphate; NR6 ion exchange; NR7 N/P/K cascade. | Stoichiometry, charge/element balances, equilibrium constraints and equipment envelopes. | Flow-weighted digestate N/P/K speciation, product assay/grade, contaminant limits, recovery efficiencies, reagents, utilities and field-substitution evidence. |

Classify each record before connecting it to a calculation:

- **Context-independent:** a physical constant or equation with explicit units,
  reference conditions and applicability limits. Do not reuse a paper's fitted
  efficiency as a universal constant.
- **Technology-specific:** measured vendor or literature performance under a
  stated feed composition, scale and operating envelope. It needs a transfer
  check before another feedstock or plant uses it.
- **Material/site-specific:** sampled grass or another waste stream, local
  weather, collection and storage, utility tariff or product-market grade.
  These require a site or feedstock selector and never silently become global
  defaults.

The reference-only King et al. (2012) grass-silage data package now includes the
reported washing/pressing protocol and Table 1–2 means/SEM. It is useful for
comparing the effects of wash count and hydraulic pressure, but it is not fresh
roadside-grass or screw-press calibration data. The Table 1–2 solubles response
heading and footnote use conflicting definitions, so this response is explicitly
blocked from calculation use pending source clarification. See
`Greenhub/data/Pre-treatment/Mechanical/king_2012_grass_silage_fractionation_table_data_reference.csv`
and its `.source.json` provenance sidecar.

The missing measurements and acquisition roles for these families are listed
in `Greenhub/data/platform/catalogs/phase_3_7_measurement_acquisition_register.csv`
and the matching Excel checklist. A blank measurement is not zero, and a
reference comparator is not an activated parameter.

### New open literature comparators, 2026-11-09

Five additional source-linked datasets broaden the reusable technology evidence
pool without changing GreenHub calculations:

- **Pretreatment and fractionation / protein recovery:** [Hansen et al. (2022)](https://doi.org/10.3390/foods11203229)
  report pilot single-screw alfalfa pressing and repeated-pass fraction masses,
  protein content, digestibility, and cumulative recovery. The extract is
  equipment- and alfalfa-specific.
- **Protein recovery:** [Lin et al. (2020)](https://doi.org/10.3390/molecules25030488) compare alkaline, aqueous, and
  subcritical-water extraction of pasture grass, with source-defined extraction
  yield and precipitate purity. Laboratory TCA precipitation and lyophilization
  are not commercial route coefficients.
- **Pretreatment and fractionation / anaerobic digestion:** [Brown et al. (2022)](https://doi.org/10.3390/en15103495)
  report grass hydrothermal-carbonization process-water BMP comparisons. The
  [Leeds supporting dataset](https://doi.org/10.5518/1154) provides its open data.
  batch assay, substrate, inoculum, and test conditions do not represent a
  continuous GreenHub post-protein digester.
- **Biogas upgrading:** [Hoyos et al. (2026)](https://doi.org/10.1016/j.fuel.2025.138010) report gas composition from a small
  carbonate absorption and air-stripping pilot using synthetic gas. The study
  does not provide a commercial methane-recovery or energy-demand factor.
- **Anaerobic-digestion assay validation:** [Hafner et al. (2026)](https://doi.org/10.1016/j.biortech.2026.134136)
  provide an open, CC BY 4.0 interlaboratory dataset. The 619 bottle-level
  `bmp_calc` records span six assay substrates, two tests and 31 laboratories,
  in mL CH4 per g substrate VS added. The values are calculated by the authors
  from submitted measurements. They support BMP-method validation and
  reproducibility checks, not substrate-specific continuous-digester yields.

All five records are B-tier literature evidence, indexed under their related
technology families, and remain reference-only. Their source location, license,
retrieval date, applicability, and transfer limits are carried into the
cross-project catalog. Phase 7 still needs GreenHub digestate speciation,
flow-weighted nutrient partition, product assay, contaminant, and field-use
measurements; existing nutrient-recovery analogues do not replace these.
