# Roadside grass composition dataset — source coverage

The CSV contains **187 rows** and all 36 requested provenance columns.

- Direct roadside-grass rows: 126
- Indirect non-roadside grass-juice rows: 15
- Explicit unresolved/missing rows: 46

## Direct source coverage
Brown et al. (2020): fresh/ensiled proximate and ultimate analysis, C:N, moisture, VS and BMP.
Mason et al. (2020): moisture, site-specific PTEs and selected PAH markers.
Smit et al. (2022): bulk density, protein and extractive sugars.
Scott et al. (2023): screw-pressed roadside-grass liquid-fraction pH, N, P2O5 and K2O.

## Indirect evidence
Rows marked `indirect` are from other grass press juices. They are retained only as analyte/measurement targets and cannot be used as roadside-grass defaults.

## Equations requiring Python
- `EQ_VS_CORR`: `%VS_corrected = 2.08 + 0.975 × %VS_uncorrected`
- `% to kg/kg`: divide by 100
- `g/L to kg/m3`: numerical value unchanged
- `mg/L to kg/m3`: multiply by 10^-3
- `µg/g to mg/kg`: numerical value unchanged
- `mL/g to m3/kg`: multiply by 10^-3

## Key unresolved groups
EC, density, viscosity, COD fractions, BOD5, alkalinity, nitrogen species, VFA species, cellulose, hemicellulose, lignin, NDF/ADF, amino acids, thermal properties and microbial load remain blank with `evidence_status=missing`.
