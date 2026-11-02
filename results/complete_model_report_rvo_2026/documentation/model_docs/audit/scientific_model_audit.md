# Scientific Model Audit

Audit date: 2026-07-29

Engineering maturity levels follow the alpha specification: E0 topology, E1 empirical
mass transformation, E2 stoichiometric material model, E3 kinetic/equilibrium or
mass-transfer model, E4 material/energy model with sizing, and E5 sufficiently validated
and costed engineering model.

No GreenHub unit is classified E5. Structural-test mode is active, project validation
data are incomplete, custom CAPEX is mostly absent, and the active compressor cost
correlation is used below its validated range.

## Unit-Class Maturity

| Process area | Unit class | Typical IDs | Maturity | Evidence and principal gap |
|---|---|---|---|---|
| Preparation | FeedPreparation | U101 | E1 | Empirical removal plus throughput/power; no validated cleaning curve/cost |
| Preparation | PulsedElectricField | U201 | E4 | Material ledger, specific energy and sizing; no treatment-response calibration/cost |
| Preparation | ScrewPress | S201 | E1 | Component partition and cake moisture; no press mechanics/vendor curve |
| Preparation | PrimaryCentrifuge | C301 | E1 | Component capture/sludge moisture/power; no settling or vendor correlation |
| Protein | AcidificationMixer | M401 | E1 | Explicit reagent solution and empirical/titration-capable dose; pH is not rigorous equilibrium |
| Protein | ProteinPrecipitation | R401 | E3 | pH/temperature/residence response and kinetic option; project pI/kinetics missing |
| Protein | ProteinSeparator | C401 | E1 | Component-specific empirical capture; no separation mechanics/cost |
| Protein | CakeWasher | W401 | E1 | Stage-wise empirical displacement; no washing data |
| Protein | MechanicalDewatering | D401 | E1 | Moisture target and power; no pressure/filtration mechanics |
| Protein | ProteinDryer | DR401 | E4 | Water/energy/design screening; no drying kinetics or validated product-quality model |
| Protein | NeutralizationMixer | M403 | E2 | Formula-balanced neutralization/salts; no electrolyte equilibrium |
| Digestion | DigesterFeedConditioner | M501 | E2 | Reagent and nutrient bookkeeping; empirical pH demand |
| Digestion | AnaerobicDigester | R501 | E4 | Stoichiometry/kinetic options, inhibition, heat, geometry and power; no GreenHub time-course calibration/cost |
| Digestion | BiogasDisengagement | V501 | E1 | Empirical gas/water partition and design; no rate-based gas transfer |
| Biogas | RawBiogasCooler | G601 | E4 | Thermal duty, condensate and design; screening properties |
| Biogas | CondensateSeparator | S601 | E1 | Physical allocation and design; no demister hydraulics |
| Biogas | HydrogenSulfideRemoval | R601 | E2 | Media/oxidation bookkeeping; no breakthrough kinetics/vendor life |
| Biogas | AmmoniaRemoval | R602 | E2 | Water/acid capture bookkeeping; no absorber mass transfer |
| Biogas | ParticleSiloxaneFilter | F601 | E1 | Empirical capture/media use/power; no breakthrough data |
| Biogas | WaterAbsorber | A611 | E3 | Pressure/T/circulation-dependent apparent absorption; not rigorous equilibrium stages |
| Biogas | WaterFlashTank/WaterRegenerator | V612/A612 | E1 | Empirical pressure allocation/recovery; no flash EOS/mass transfer |
| Biogas | GasWaterSeparator | V611/D611 | E1 | Empirical water split; no droplet/dryer design |
| Biogas | MembraneStage | BG3 stages | E3 | Partial-pressure permeation and area; uncalibrated permeance/fouling |
| Biogas | PressureSwingAdsorber | BG4 | E3 | Cycle-average recovery response and sizing; no isotherm/cycle validation |
| Biogas | MEAAbsorber/MEAStripper | BG5 | E3 | Equivalent loading/reversible solvent loop; no rigorous electrolyte/rate model |
| Biogas | RichLeanHeatExchanger/LeanHeatRecovery/MEAReboiler/RefluxCondenser | BG5 | E4 | Explicit heat/design screening; no vendor/fouling validation |
| Nutrient | DigestateEqualization | T701 | E4 | Volume, dimensions, power and heat-loss estimate; no dynamic buffering/settling |
| Nutrient | DigestateSolidLiquidSeparator | S701 | E1 | Component capture and cake moisture; technology label lacks separate performance curves |
| Nutrient | StruviteCrystallizer | R711 | E2 | Exact limiting-species formula balance; no Ksp/activity/nucleation model |
| Nutrient | CalciumPhosphateReactor | R712 | E2 | Formula-selected precipitation; no mineral equilibrium/speciation |
| Nutrient | CrystalSeparator | S711/S712 | E1 | Empirical product/impurity capture and moisture |
| Nutrient | AlkalineConditioner | M721 | E1 | Explicit base/water dose; no alkalinity/titration prediction |
| Nutrient | ProcessHeater | H721 | E4 | Sensible duty and utility; constant bulk heat capacity |
| Nutrient | AmmoniaStripper | A721 | E3 | pH/T/P/gas/packing-responsive NTU-like transfer; no rate-based validation |
| Nutrient | AcidAbsorber | A722 | E2 | Formula-balanced acid capture and neutralization heat; no absorber hydraulics |
| Nutrient | IonExchangeBed/Regeneration | A731/R731 | E2 | Site-equivalent balance and recycle; no breakthrough/kinetic cycle |
| Nutrient | PotassiumEvaporator | E741 | E4 | Water/heat/power/design; no salt solubility/scaling equilibrium |
| Nutrient | PotassiumMembraneConcentrator | M741 | E3 | Pressure/rejection/area response; no calibrated fouling/osmotic model |
| Nutrient | NutrientProductWasher | W711/W712 | E1 | Empirical impurity removal; disabled by default without data |
| Nutrient | NutrientProductDryer | D711/D712 | E4 | Moisture/heat/power and stability limit; disabled by default without data |
| Nutrient | ProductStorage | V722/V741 | E4 | Residence/working mass; no vessel design/cost |
| Shared | BioSTEAM Mixer/Splitter | M*/S* | E0-E1 | Topology/material mixing only unless wrapped by process logic |
| Shared | HXutility/Compressor/Pump/StorageTank | H*/E*/C*/P*/T101 | E4 | Built-in material/energy/design/cost where applicable; correlation range and process validation must be checked |

## Scientific Strengths

- One physical component inventory is conserved through the selected graph.
- Aggregate COD/TKN/TAN/TP/TOC measurements are diagnostics, not added mass.
- Reactions and pseudo-component conversions have element-ledger tests.
- Scenario factories use fresh flowsheets and deterministic rebuild tests.
- Missing required workbook values fail; optional blanks do not create material.
- Nutrient recovery tracks reagent counterions and residual destinations.

## Scientific Gaps

- No rigorous electrolyte/activity/charge-balance package.
- Limited project-specific kinetic, mass-transfer, membrane, separator, and drying data.
- CHP/plant utility production is absent; recovered-energy credits default to zero.
- Most custom equipment lacks approved purchase-cost, installed-cost, lifetime, and
  maintenance bases.
- Current P feed is unspeciated; the selected NR4 case forms no new struvite.
- Product quality, fertilizer eligibility, water reuse, emissions compliance, and
  industrial operability are not validated.

