# GreenHub centrifuge capture — debris and suspended protein traceability

## Scope
The dataset contains **34 records** for green-biomass juice centrifugation. It separates raw clarification from heat- or acid-induced protein precipitation.

## Direct grass evidence
**Perennial ryegrass (Sandoval et al., 2026)** is the strongest direct-grass source. A GEA SCE 205 clarifying decanter at 5590 rpm and 12 rpm differential clarified 555 L grass juice to 510 L. Dry matter decreased from 5.13% to 0.99%.

This supports direct grass hydraulic recovery and clarified-juice DM targets. It does **not** justify a DM mass-capture fraction because juice density and captured pellet mass were not reported. No density was assumed.

A later, separate pH 3.5 step used a GEA Scout SSE 10 at 21,000 g and produced 25 kg wet protein-rich precipitate at 21.9% DM. These records are explicitly downstream precipitation data, not raw debris capture.

## Alfalfa proxy for raw debris and suspended green protein
WO2015197078A1 Example 2 reports 1.022 kg green juice centrifuged at 3500 g for 10 min at 2–5 °C, producing 327 g wet solid phase containing **green protein and fibre**.

`wet sediment capture = 0.327 / 1.022`

The sediment DM was 8.27%. This is a defensible class-B proxy for a raw clarification wet-mass split.

The patent also reports a 13,000 g, 10 min first centrifugation whose green leaf-protein/suspended-solids phase contained 35.5% protein in DM. This is a captured-phase composition benchmark, not a protein capture fraction.

## Demonstration-scale equipment selectivity
dos Passos & Ambye-Jensen (2024) compare centrifuges after 55 °C green-protein coagulation:

- decanter: 3780 g, 1500 L/h;
- disc-stack: 12,344 g, 600 L/h, 100 s sediment discharge;
- two-stage decanter + disc-stack.

Residual suspended solids were 2.1%, 0.5%, and 0.1%, respectively. The article prose calls these vol%, while the figure caption calls them wt%; the dataset preserves that inconsistency.

Residual precipitated green protein in clarified juice was >80%, 17%, and 4%, respectively. Total crude protein removed as LPC was 18%, 28%, and 41%. The two-stage process retained >80% of soluble white protein in clarified juice.

These coefficients are suitable only when GreenHub explicitly activates an upstream heat-coagulation state.

## Historical clarification evidence
Lamsal et al. (2003) report that 10,000 g batch centrifugation after heating alfalfa juice to 55 °C reduced juice absorbance by up to 98% while removing particulates, insoluble protein and chlorophyll. This is retained as an optical clarification metric and is not converted into a mass-capture coefficient.

## Suggested GreenHub policies
### `centrifuge_prg_raw_clarification_2026`
Direct grass:
- 5590 rpm;
- 12 rpm differential;
- 555 -> 510 L volume recovery;
- 5.13% -> 0.99% DM.

Do not activate a debris mass-capture coefficient yet.

### `centrifuge_alfalfa_raw_debris_3500g`
Class-B proxy:
- 3500 g;
- 10 min;
- 2–5 °C;
- wet sediment capture derived from 327 g / 1.022 kg;
- sediment identity: green protein + fibre;
- sediment DM: 8.27%.

### `centrifuge_heat_coagulated_green_protein`
Separate downstream policy:
- equipment-dependent residual solids;
- green aggregate retention/capture;
- white-protein preservation.

Requires heat coagulation upstream.

## Component-state rule
GreenHub should distinguish:
1. debris/fibrous suspended solids;
2. insoluble or chloroplast-associated green protein;
3. soluble white protein;
4. intentionally precipitated protein.

Centrifuge coefficients measured after heat or acid precipitation must not be used for untreated raw juice.

## Still unresolved
Direct roadside-grass/perennial-ryegrass paired feed/pellet/supernatant data remain missing for:
- debris dry-mass capture;
- suspended insoluble-protein capture;
- soluble-protein loss in raw clarification;
- protein mass closure;
- particle-size-dependent capture;
- ash/mineral co-capture;
- grass-validated sigma-factor capture relationships.

These should remain inactive.
