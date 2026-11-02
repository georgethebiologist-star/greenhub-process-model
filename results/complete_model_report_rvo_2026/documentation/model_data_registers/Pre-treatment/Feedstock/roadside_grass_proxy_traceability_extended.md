# Extended roadside-grass proxy traceability

## Summary
Added **23 separate proxy rows**. No incompatible species were averaged.

## Defendable proxy hierarchy
- **P1:** temperate perennial ryegrass and clean perennial-grass data.
- **P2:** timothy grass, used to bracket temperate grass-species variation.
- **P3:** Napier grass press liquor, used only as broad liquid-process bounds.

## Similarity assumptions
A proxy is stronger when botanical family, perennial growth form, climate, harvested organs, maturity, preservation state and analytical method match. Perennial ryegrass matches roadside-grass biology best. Timothy is a supporting temperate Poaceae proxy. Napier matches Poaceae anatomy and screw pressing but differs in climate, physiology and conditioning.

## Reference-backed candidates
**Truba et al. (2017), DOI 10.12911/22998993/66249**
- Lolium cellulose 240.8 g/kg DM
- hemicellulose 149.7 g/kg DM
- ADL 41.2 g/kg DM

**Guțu et al. (2025)**
- Lolium: NDF 633, ADF 355, ADL 22, cellulose 333, hemicellulose 278, soluble sugars 181 g/kg DM
- Phleum: NDF 734, ADF 417, ADL 26, cellulose 391, hemicellulose 317, soluble sugars 65 g/kg DM
- Timothy starch 18.8 g/kg DM is secondary evidence and remains low confidence

**Amaleviciute-Volunge et al. (2020)**
- perennial-grass heating value 17.7–19.02 MJ/kg; gross/net basis must be confirmed

**Suaisom (2019)**
- Napier press liquor TCOD 18,765–30,195 mg/L
- filtered COD 8,704–14,585 mg/L
- TS 20,535–40,052 mg/L
- VS 12,385–24,202 mg/L
- TP 112–383 mg/L
- pH 4.19–5.30

## Conversions
- g/kg ÷ 1000 = kg/kg
- mg/L × 10^-3 = kg/m³
- No midpoint or cross-species average was calculated
- ADL remains ADL, not total Klason lignin
- filtered COD remains a soluble-COD proxy
- total soluble sugars remain a WSC proxy

## GreenHub use
Use these only as optional sensitivity scenarios:
- `lolium_2017_low_fibre`
- `lolium_2025_early_flowering`
- `phleum_2025_high_fibre`
- `napier_press_liquor_bounds`

Do not activate unresolved EC, density, viscosity, BOD5, alkalinity, TAN, NH4, nitrate, VFA species, ORP, osmolality, microbiology, thermal conductivity, amino-acid profile, NPN, chlorine, silica or ensiled sulfur.
