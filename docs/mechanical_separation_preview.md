# Mechanical Separation Preview

This is a report-only bridge from whole-feed dynamic pooling to future mechanical
separation. It does not activate dynamic mode, create model overrides, or change
the empirical simulation path.

## Source-backed split now available

The strongest current split candidate comes from
`Greenhub/data/Pre-treatment/Mechanical/greenhub_mechanical_pretreatment_pressing_data.csv`:

- `M068`: press cake yield = `0.395` kg/kg processed clover-grass biomass
- `M069`: brown juice yield = `0.568` kg/kg processed clover-grass biomass
- `M070`: protein concentrate yield = `0.037` kg/kg processed clover-grass biomass
- `M071`: mass balance closure = `1.0`

Source: `S03_SANTAMARIA_2020`, clover grass biomass, transferability class
`A_direct_grass_or_green_forage`.

These yields close the product mass boundary, but the boundary includes
mechanical fractionation and protein recovery. They must be reviewed before
being used as raw press-only split coefficients.

## Implemented behavior

`Greenhub/mechanical_separation.py` adds:

- `default_mechanical_separation_policy()`
- `preview_mechanical_separation(pools, policy, component_partition=None)`

By default it only reports product-stream masses. It does not invent component
partition coefficients for protein, sugar, ash, water, or fiber. Components
remain `unmapped_components` until an explicit partition map is supplied.

When `component_partition` is supplied, each component's shares must sum to
`1.0`, and the preview conserves component mass across streams.

## Still missing before activation

- Direct roadside-grass or grass-clover juice/cake component partition.
- Soluble and insoluble protein split between brown juice, cake, and concentrate.
- Water partition between liquid and cake.
- WSC/sugar partition.
- Ash/mineral/nutrient partition.
- Fiber retention in cake and any carryover to liquid.
- Raw press-only boundary separate from downstream protein concentrate recovery.
- Press settings and energy paired with mass yields.

## Next development step

The typed evidence loader and conservative dynamic preview are now documented in
[`mechanical_press_dynamic_preview.md`](mechanical_press_dynamic_preview.md).
Current clover-grass Water evidence does not close and is deliberately not
normalized, while protein, sugar, ash, and fiber partitions remain unavailable
for the selected boundary. The preview therefore remains useful for evidence
review and stream architecture, but not for downstream protein extraction, AD,
or nutrient-recovery calculations.
