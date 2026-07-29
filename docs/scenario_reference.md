# Scenario Reference

Scenario IDs are stable workbook and API identifiers.

| Process area | Active IDs | Data-gated IDs |
|---|---|---|
| Feed Preparation and Primary Separation | `F0` measured liquid, `F1` no PEF, `F2` PEF baseline, `F3` PEF sensitivity | None |
| Protein Recovery | `PR0` bypass, `PR1` acid, `PR2` heat, `PR3` combined | `PR4` fermentation, `PR5` CO2-assisted, `PR6` ultrafiltration |
| Anaerobic Digestion | `AD0` bypass, `AD1` post-protein mesophilic, `AD2` direct mesophilic, `AD3` thermophilic | `AD4` two-stage, `AD5` high-rate |
| Biogas Upgrading | `BG0` raw export, `BG2` water scrubbing, `BG3` membrane, `BG4` PSA, `BG5` MEA | `BG1` CHP, `BG6` cryogenic |
| Nutrient Recovery | `NR0` through `NR7` | None |

Nutrient process orders are `A` separation-P-N-K, `B` separation-N-P-K, `C` whole-digestate P before separation, and `D` separation or inventory only. Incompatible route/order combinations raise an error.

Select the chain in the `ModelControl` sheet or pass meaningful aliases to `create_integrated_greenhub_system()`. Inactive scenarios raise `NotImplementedError` with their required data rather than silently falling back.
