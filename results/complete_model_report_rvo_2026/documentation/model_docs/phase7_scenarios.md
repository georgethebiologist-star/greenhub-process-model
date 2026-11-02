# Phase 7 Scenarios And Process Orders

## Scenario Matrix

| Scenario | Separation | P route | N route | K route | Default order |
|---|---:|---|---|---|---|
| NR0 | No | None | None | None | D |
| NR1 | Yes | None | None | None | D |
| NR2 | Yes | Struvite | None | None | A |
| NR3 | Yes | None | Stripping and acid capture | None | A |
| NR4 | Yes | Struvite | Stripping and acid capture | None | A |
| NR5 | Yes | Calcium phosphate | None | None | A |
| NR6 | Yes | None | Zeolite ion exchange | None | A |
| NR7 | Yes | Struvite | Stripping and acid capture | Evaporation or membrane | A |

All scenarios are active structural engineering cases. Active does not mean calibrated or commercially ready.

## Process Orders

### Order A

```text
T701 -> S701 -> phosphorus route -> ammonia route -> optional K route
```

This is the NR4 and NR7 baseline. Phosphorus recovery can consume part of NH4 before stripping.

### Order B

```text
T701 -> S701 -> ammonia route -> phosphorus route -> optional K route
```

Removing TAN first can reduce struvite formation. The model preserves this interaction rather than forcing identical recoveries.

### Order C

```text
T701 -> whole-digestate phosphorus route -> S701 -> ammonia route
```

This can physically recover mineral already present in whole digestate and exposes the crystallizer to particulate impurities. Its performance is especially uncertain without whole-digestate trials.

### Order D

```text
T701 -> S701
```

NR0 bypasses even these units; NR1 uses Order D. Targeted-recovery scenarios reject Order D because silently deactivating their named mechanism would be misleading.

## Upstream Interaction

Each factory receives explicit upstream F/PR/AD/BG IDs and selected month. The resulting digestate therefore changes with protein bypass/recovery, direct/post-protein digestion, mesophilic/thermophilic operation, and feed seasonality.

`BG0`, `BG2`, `BG3`, `BG4`, and `BG5` can be upstream choices. `BG1` CHP and `BG6` cryogenic remain data-gated in the actual repository, so Phase 7 does not fabricate those interactions. Once a real CHP utility bus is implemented, Phase 7 metrics can consume its available heat/electricity keys.

## Comparison Rules

The scenario workbook uses a common metric schema for material, nutrient, reagent, utility, and product-quality inventories. It deliberately has no weighted score, best-case label, ranking, or MCDA result. Class-E values, incomplete utilities, absent CAPEX, and unverified product eligibility make selection premature.
