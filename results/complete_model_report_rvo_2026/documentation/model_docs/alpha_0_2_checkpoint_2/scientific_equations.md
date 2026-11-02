# Scientific Equation Registry

## Active Equation

`EQ-MB-001` is implemented as `protein_precipitation_mass_balance()` in `Greenhub/scientific_equations.py`:

```text
m_cake = m_in * recovery
m_supernatant = m_in - m_cake - m_loss
residual = m_in - m_supernatant - m_cake - m_loss
```

All mass terms use kg/h and recovery is dimensionless. Inputs must be finite, mass inputs non-negative, recovery within `[0, 1]`, and cake plus losses cannot exceed incoming protein. Tests cover reference reproduction, conservation, monotonic trend, zero/one boundaries, and invalid inputs.

`ProteinPrecipitation._run()` now calls this typed function. At the structural default of 0.75 the calculation is mathematically equivalent to its previous mass allocation; only parameter provenance and validation changed.

## Unresolved Equations

The Checkpoint 1 source registry retains 179 catalogued equation rows: 169 blocked and 10 reference-only. No formula string is evaluated. The advanced equation activation registry is a non-destructive overlay containing the one approved D4 implementation; all other equations require typed implementations, symbol/input resolution, dimensional checks, and reference/trend/boundary/invalid-input tests.
