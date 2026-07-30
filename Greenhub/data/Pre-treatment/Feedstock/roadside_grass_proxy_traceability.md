# Roadside grass missing-parameter proxy traceability

## 1. Summary of sources found

**Scott et al. (2023)**, *Constraints using the liquid fraction from roadside grass as a bio-based fertilizer*, DOI `10.1002/jpln.202200308`. Direct screw-pressed roadside-grass liquid-fraction data from Maldegem, Belgium.

**WASTE2ROAD consortium (2020)**, *D5.2 Identified value chains*. Direct roadside-grass LHV candidate in a SINTEF-hosted EU technical report.

**Smit et al. (2022)**, DOI `10.1021/acssuschemeng.2c00838`, was reviewed for roadside-grass lignocellulose composition. Exact supporting-information values were not verified sufficiently, so cellulose, hemicellulose and lignin remain missing.

## 2. Filled directly

solid_lhv, glf_ts, glf_total_p, glf_total_k, contaminant_cd, contaminant_pb, contaminant_hg

`glf_ts`, `glf_total_p`, and `glf_total_k` are calculations from direct published roadside-GLF measurements. Cd, Pb and Hg are direct roadside-GLF measurements. `solid_lhv` is a direct technical-report candidate.

## 3. Filled by indirect proxy

`solid_cp` contains an equation-only proxy. No numerical indirect proxy was accepted.

## 4. Remaining missing

fresh_solid_ph, fresh_solid_ec, solid_cellulose, solid_hemicellulose, solid_lignin, solid_ndf, solid_adf, solid_wsc, solid_starch, solid_lipids, solid_amino_acids, solid_true_protein, solid_npn, solid_d50, solid_porosity, solid_k, solid_hhv, solid_chlorine, solid_silica, ensiled_sulfur, glf_ec, glf_density, glf_viscosity, glf_vs, glf_cod_t, glf_cod_s, glf_bod5, glf_tic, glf_alkalinity, glf_tan, glf_nh4, glf_no3, glf_po4p, glf_vfa, glf_acetate, glf_propionate, glf_butyrate, glf_lactate, glf_buffer_capacity, glf_osmolality, glf_orp, glf_microbiology, contaminant_se

## 5. Assumptions and conversions

- Total solids: `x_TS = C_FM / C_DM = 1280 / 38788 = 0.0329999 kg/kg`.
- Elemental P from P₂O₅: factor `0.43642682`.
- Elemental K from K₂O: factor `0.83015130`.
- LHV: `13.1 MJ/kg × 10^6 = 13,100,000 J/kg`.
- Heat capacity: `c_p,mix = x_w c_p,w + (1-x_w)c_p,dry`; no value calculated.

## 6. Parameters that must not be activated in GreenHub yet

All rows marked `missing`, `solid_cp`, `solid_lhv` until basis confirmation, contaminant rows outside the liquid-fraction stream, total P as orthophosphate-P, total K as ionic activity, and `glf_ts` as a universal seasonal default.

## 7. Recommended confidence classes

- **A conversion / B representativeness:** `glf_total_p`, `glf_total_k`.
- **B:** `glf_ts`, roadside-GLF Cd and Pb.
- **C:** roadside-GLF Hg as displayed; `solid_lhv`.
- **D / inactive:** `solid_cp`.
- **Missing / inactive:** all remaining targets.

The unresolved COD, VFA, alkalinity, TAN, rheology, EC, ORP, osmolality and microbiology parameters should not be populated from wastewater, digestate, or unrelated silage datasets.
