# GreenHub second-centrifuge protein capture and wet-cake moisture traceability

## Scope
The dataset contains **27 source-backed records** for:

`green juice -> protein aggregation -> second centrifuge/separator -> wet protein cake + supernatant`

Aggregation routes are kept separate: acid/isoelectric precipitation, lactic fermentation, and heat coagulation.

## Direct grass evidence
Sandoval et al. (2026) provide the strongest direct perennial-ryegrass wet-cake record. Clarified PRG juice was adjusted to pH 3.5 and separated at 21,000 g, producing **25 kg wet protein-rich precipitate at 21.9% DM**.

Calculated only from the reported DM:
- wet-cake moisture = `1 - 0.219 = 0.781 kg/kg`
- dry solids in cake = `25 × 0.219 = 5.475 kg`

No protein capture fraction is calculated because the compatible inlet and supernatant protein inventories are not reported for this exact separation boundary.

## Grass-clover fermentation
Santamaría-Fernández et al. report demonstration-scale grass-clover protein concentrate around **37.3% crude protein in DM** after lactic-acid fermentation and centrifugation. This is a direct product-quality benchmark, not a centrifuge-only capture coefficient.

## Wet-cake moisture envelope
Jørgensen et al. report protein concentrate paste at about **30–50% DM** before final drying. This corresponds exactly to **50–70% wet-basis moisture**. The range is preserved and not collapsed to a midpoint.

## Protein recovery evidence
The Aarhus DCA report estimates about **45% of the protein in green biomass** can be recovered in protein concentrate paste, with concentrate protein around **47% of DM**. This is whole-process recovery and should not be interpreted as second-centrifuge efficiency.

Andrade et al. report **>90% recovery of the crude protein remaining in green juice after precipitation and centrifugation**. This is a strong downstream recovery envelope when GreenHub matches the same aggregation route, but it remains a combined precipitation + centrifugation coefficient.

## Alfalfa heat-coagulation proxy
dos Passos & Ambye-Jensen report demonstration-scale separation after **55 °C heat coagulation**.

Total crude protein removed as LPC:
- decanter: 18%
- disc-stack: 28%
- two-stage: 41%

Residual precipitated green protein remaining in clarified juice:
- decanter: >80%
- disc-stack: 17%
- two-stage: 4%

Two-stage centrifugation retained >80% of the soluble white-protein fraction.

These are class-B alfalfa proxies and require an explicit upstream `heat_coagulated` protein state.

## Recommended GreenHub policies

### `second_centrifuge_prg_pH3_5_21000g`
Direct grass:
- pH 3.5
- 21,000 g
- wet cake 25 kg for documented batch
- wet-cake DM 0.219
- wet-cake moisture 0.781

Do not assign a protein capture fraction yet.

### `second_centrifuge_green_biomass_90pct_recovery`
Opt-in combined precipitation + centrifugation envelope:
- protein recovery >0.90 of green-juice crude protein.

### `second_centrifuge_wet_cake_generic`
Generic wet-cake envelope:
- DM 0.30–0.50
- moisture 0.50–0.70

### `second_centrifuge_alfalfa_heat_coagulation`
B-class equipment-selectivity proxy after a 55 °C heat-aggregation state.

## Report-only rows
- whole-biomass 45% protein-to-concentrate recovery
- generic 47% DM product protein concentration
- grass-clover 37.3% DM concentrate CP
- qualitative wet-LPC storage constraints

## Still missing
Direct roadside-grass / perennial-ryegrass same-batch data remain missing for:
- inlet protein mass to second centrifuge
- wet-cake protein mass
- supernatant residual protein mass
- true centrifuge-only protein capture
- wet-cake CP purity before drying
- cake rheology/compressibility
- cake wash-water requirements
- direct grass cake moisture for fermentation and heat-coagulation routes

These remain inactive rather than being constructed by mixing studies.
