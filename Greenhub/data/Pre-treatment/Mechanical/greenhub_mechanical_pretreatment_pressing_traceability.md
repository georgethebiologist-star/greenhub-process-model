# GreenHub mechanical pretreatment and pressing traceability

## Scope

The dataset contains **106 source-backed records** covering direct grass and grass-clover evidence, legume proxies, and explicitly low-transferability wet-fibrous proxies.

## Direct grass data

Direct or near-direct grass evidence includes perennial ryegrass, festulolium, tall fescue, reed canary grass, grass-clover mixtures, and grass-clover silage.

The strongest records are:
- paired feed and press-cake DM, protein, ash and fibre composition for perennial ryegrass;
- clover-grass product mass fractions of 39.5% cake, 56.8% brown juice and 3.7% protein concentrate;
- PEF-associated relative increases of around 25% in juice yield and 31% in crude-protein yield;
- festulolium and ryegrass integrated-process energy values, clearly marked as not press-only.
- a separate 2026 Tuv pilot-derived fractionation benchmark with feed and product streams on fresh- and dry-matter bases (Table 2, DOI `10.1038/s44264-026-00189-y`). It is report-only and grass-clover-specific, not a roadside-grass default.

### Tuv whole-pathway mass-balance benchmark

Rows M095–M106 transcribe the published table's 5,263 kg fresh / 1,000 kg DM
feed basis and the pulp, green-juice intermediate, protein-concentrate,
brown-juice, and unrecovered-mass entries. For a final-output closure check,
sum pulp + protein concentrate + brown juice + unrecovered loss; the fresh-mass
sum is 5,264 kg per 1,000 kg DM feed versus the reported 5,263 kg input (1 kg
rounding difference), and the dry-matter sum is 1,000 kg. Green juice (2,311 kg
fresh, 208 kg DM) is an intermediate entering protein recovery; adding it to
the final streams double-counts mass and is expressly prohibited. The article
states the mass balance derives from Tuv pilot trials; it does not provide
roadside-grass-specific conditions or uncertainty for these rounded entries.
Use this only for whole-pathway plausibility and intermediate/final-stream
accounting checks; do not transfer the split directly into active Phase 3 or
Phase 4 parameters.

## Alfalfa, lucerne and clover proxies

These are marked transferability class B. They share wet leafy biomass processing characteristics but differ from roadside grass in protein solubility, fibre anatomy, buffering and mineral composition.

The alfalfa screw-press study provides:
- 6 bar working pressure;
- 16% protein recovery after one pressing;
- 48% cumulative recovery after rehydration and up to ten pressings.

These values support pass-dependent model structure but should not become direct roadside-grass coefficients.

## Broader plant proxies

Silage dewatering and wet lignocellulosic chip pressing are class C. They are retained only for equipment-scale context. The wet-chip energy values must not calibrate GreenHub wet-grass pressing.

## Required assumptions

Before a dynamic split is activated, GreenHub must distinguish:
1. fresh versus ensiled biomass;
2. raw green juice versus brown juice after protein recovery;
3. single-pass versus cumulative re-pressing;
4. fresh-mass versus dry-matter basis;
5. released protein in juice versus precipitated or final recovered protein;
6. press-only energy versus integrated-process energy;
7. species, maturity, initial DM and particle size.

## Safe for report-only use

- mixed-species mean juice and pulp protein concentrations;
- PEF relative improvements without absolute baseline flows;
- integrated energy per kg protein concentrate;
- CNCPS theoretical extractable protein;
- silage and wet-chip energy bounds;
- composition enrichment where paired stream masses are missing.

## Candidates for future dynamic press-split activation

Potentially usable after boundary verification:
- 39.5/56.8/3.7 clover-grass product split;
- 6 bar alfalfa pass-dependent protein recovery;
- species-specific paired feed and pulp composition;
- a PEF multiplier applied only after an untreated absolute yield is defined.

## Important remaining gaps

No sufficiently transferable paired source was found for:
- direct roadside-grass juice and cake yield;
- roadside-grass water partition;
- complete soluble/insoluble protein partition;
- WSC partition with feed–juice–cake closure;
- mineral partition with closure;
- net loaded press power paired with fresh-grass throughput;
- screw speed, screen aperture, cone gap, active volume and residence time paired with yields;
- particle-size distributions before and after treatment;
- temperature rise during pressing;
- multi-pass ryegrass mass balances.

These fields should remain inactive until full pilot data or a targeted laboratory campaign is available.

## 9. Pilot-scale perennial ryegrass screw-press stream properties

Sandoval et al. (2026), DOI `10.1038/s41538-026-00831-6`, reports a June 2023 pilot campaign in Aberystwyth using a Vincent CP-10 screw press. From 1.5 t fresh perennial ryegrass, 610 L raw grass juice was collected; raw juice had pH 6.00, 5.13% dry matter, and 16.0 ± 0.7% crude protein on a dry-matter basis. These observations are M123–M126 in the mechanical evidence file.

This is a direct-ryegrass, pilot-scale stream-quality benchmark, but **not a closed press balance**: the paper does not report juice density, press-cake mass, feed composition, or unrecovered mass. Keep the volume/feed ratio as L per 1,500 kg fresh feed; do not convert it to mass yield or use it to close the press balance. Juice pH is not a precipitation setpoint, and total crude protein is not soluble-protein recovery. The DOI and source context are recorded in `prg_screw_press_pilot_benchmark.source.json`. The benchmark remains report-only and does not change route defaults.
