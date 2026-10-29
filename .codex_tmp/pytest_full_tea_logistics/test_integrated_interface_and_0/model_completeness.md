# GreenHub Model Completeness Register

Generated: 2026-10-28T19:42:51.934676+00:00
Selected configuration: `F2/PR3/AD1/BG2/NR4`; order `A`; month `July`.
Selected connected units represented: **51**.
Additional implemented scenario-only or compatibility units represented: **38**.
Total unit-ID rows: **89**.

This register describes implementation presence, not scientific validation. A calculated value may still use structural-test inputs. Zero is never interpreted as proof that a model is available.

## State Definitions

`available`, `calculated`, `assumed`, `placeholder`, `not applicable`, `missing`, and `not yet implemented` are the only completeness states.

## Coverage Summary

| Process area | Active units |
|---|---:|
| Anaerobic Digestion | 4 |
| Biogas Conditioning and Upgrading | 48 |
| Digestate Treatment and Nutrient Recovery | 22 |
| Feed Preparation and Primary Separation | 6 |
| Protein Recovery | 9 |

| Maturity | Units |
|---|---:|
| E0 | 21 |
| E1 | 12 |
| E2 | 5 |
| E3 | 7 |
| E4 | 44 |
| E5 | 0 |

No unit is classified E5: the active model uses structural inputs and lacks sufficient project validation and custom-equipment costing.

## Active Unit Register

| Unit | Class | Process area | Maturity | Purchase cost | Power | Heat | Principal gaps |
|---|---|---|---|---|---|---|---|
| U101 | FeedPreparation | Feed Preparation and Primary Separation | E4 | missing | calculated | not applicable | purchase cost; installed cost; equipment lifetime; maintenance basis; consumables |
| U201 | PulsedElectricField | Feed Preparation and Primary Separation | E4 | missing | calculated | not applicable | purchase cost; installed cost; equipment lifetime; maintenance basis; consumables |
| S201 | ScrewPress | Feed Preparation and Primary Separation | E4 | missing | calculated | not applicable | purchase cost; installed cost; equipment lifetime; maintenance basis; consumables |
| C301 | PrimaryCentrifuge | Feed Preparation and Primary Separation | E4 | missing | calculated | not applicable | purchase cost; installed cost; equipment lifetime; maintenance basis |
| M401 | AcidificationMixer | Protein Recovery | E4 | missing | calculated | not applicable | purchase cost; installed cost; equipment lifetime; maintenance basis |
| H401 | HXutility | Protein Recovery | E4 | calculated | missing | calculated | power demand; equipment lifetime; maintenance basis; consumables |
| R401 | ProteinPrecipitation | Protein Recovery | E4 | missing | calculated | not applicable | kinetics; purchase cost; installed cost; equipment lifetime; maintenance basis; consumables |
| C401 | ProteinSeparator | Protein Recovery | E4 | missing | calculated | not applicable | purchase cost; installed cost; equipment lifetime; maintenance basis; consumables |
| W401 | CakeWasher | Protein Recovery | E1 | missing | missing | not applicable | energy balance; power demand; purchase cost; installed cost; equipment lifetime; maintenance basis |
| D401 | MechanicalDewatering | Protein Recovery | E4 | missing | calculated | not applicable | purchase cost; installed cost; equipment lifetime; maintenance basis; consumables |
| DR401 | ProteinDryer | Protein Recovery | E4 | missing | calculated | calculated | kinetics; purchase cost; installed cost; equipment lifetime; maintenance basis; consumables |
| M402 | Mixer | Protein Recovery | E0 | not applicable | not applicable | not applicable | none identified at this maturity level |
| M403 | NeutralizationMixer | Protein Recovery | E4 | missing | calculated | not applicable | purchase cost; installed cost; equipment lifetime; maintenance basis |
| M501 | DigesterFeedConditioner | Anaerobic Digestion | E4 | missing | calculated | not applicable | purchase cost; installed cost; equipment lifetime; maintenance basis |
| H501 | HXutility | Anaerobic Digestion | E4 | calculated | missing | calculated | power demand; equipment lifetime; maintenance basis; consumables |
| R501 | AnaerobicDigester | Anaerobic Digestion | E4 | missing | calculated | calculated | kinetics; purchase cost; installed cost; equipment lifetime; maintenance basis; consumables |
| V501 | BiogasDisengagement | Anaerobic Digestion | E1 | missing | missing | not applicable | energy balance; power demand; purchase cost; installed cost; equipment lifetime; maintenance basis; consumables |
| G601 | RawBiogasCooler | Biogas Conditioning and Upgrading | E4 | missing | calculated | calculated | purchase cost; installed cost; equipment lifetime; maintenance basis; consumables |
| S601 | CondensateSeparator | Biogas Conditioning and Upgrading | E1 | missing | missing | not applicable | energy balance; power demand; purchase cost; installed cost; equipment lifetime; maintenance basis; consumables |
| R601 | HydrogenSulfideRemoval | Biogas Conditioning and Upgrading | E2 | missing | missing | not applicable | energy balance; power demand; purchase cost; installed cost; equipment lifetime; maintenance basis |
| R602 | AmmoniaRemoval | Biogas Conditioning and Upgrading | E2 | missing | missing | not applicable | energy balance; power demand; purchase cost; installed cost; equipment lifetime; maintenance basis |
| F601 | ParticleSiloxaneFilter | Biogas Conditioning and Upgrading | E4 | missing | calculated | not applicable | purchase cost; installed cost; equipment lifetime; maintenance basis; consumables |
| M606 | Mixer | Biogas Conditioning and Upgrading | E0 | not applicable | not applicable | not applicable | none identified at this maturity level |
| M607 | Mixer | Biogas Conditioning and Upgrading | E0 | not applicable | not applicable | not applicable | none identified at this maturity level |
| M610 | Mixer | Biogas Conditioning and Upgrading | E0 | not applicable | not applicable | not applicable | none identified at this maturity level |
| S610 | Splitter | Biogas Conditioning and Upgrading | E0 | not applicable | not applicable | not applicable | none identified at this maturity level |
| C611 | IsentropicCompressor | Biogas Conditioning and Upgrading | E4 | missing | calculated | not applicable | purchase cost; installed cost; equipment lifetime; maintenance basis; consumables |
| E611 | HXutility | Biogas Conditioning and Upgrading | E4 | calculated | missing | calculated | power demand; equipment lifetime; maintenance basis; consumables |
| A611 | WaterAbsorber | Biogas Conditioning and Upgrading | E3 | missing | missing | not applicable | energy balance; power demand; purchase cost; installed cost; equipment lifetime; maintenance basis |
| V611 | GasWaterSeparator | Biogas Conditioning and Upgrading | E1 | missing | missing | not applicable | energy balance; power demand; purchase cost; installed cost; equipment lifetime; maintenance basis; consumables |
| D611 | GasWaterSeparator | Biogas Conditioning and Upgrading | E1 | missing | missing | not applicable | energy balance; power demand; purchase cost; installed cost; equipment lifetime; maintenance basis; consumables |
| V612 | WaterFlashTank | Biogas Conditioning and Upgrading | E1 | missing | missing | not applicable | energy balance; power demand; purchase cost; installed cost; equipment lifetime; maintenance basis; consumables |
| A612 | WaterRegenerator | Biogas Conditioning and Upgrading | E4 | missing | calculated | not applicable | purchase cost; installed cost; equipment lifetime; maintenance basis |
| P611 | Pump | Biogas Conditioning and Upgrading | E4 | calculated | calculated | not applicable | equipment lifetime; maintenance basis; consumables |
| M618 | Mixer | Biogas Conditioning and Upgrading | E0 | not applicable | not applicable | not applicable | none identified at this maturity level |
| M619 | Mixer | Biogas Conditioning and Upgrading | E0 | not applicable | not applicable | not applicable | none identified at this maturity level |
| M698 | Mixer | Biogas Conditioning and Upgrading | E0 | not applicable | not applicable | not applicable | none identified at this maturity level |
| M699 | Mixer | Biogas Conditioning and Upgrading | E0 | not applicable | not applicable | not applicable | none identified at this maturity level |
| T701 | DigestateEqualization | Digestate Treatment and Nutrient Recovery | E4 | missing | calculated | not applicable | purchase cost; installed cost; equipment lifetime; maintenance basis; consumables |
| S701 | DigestateSolidLiquidSeparator | Digestate Treatment and Nutrient Recovery | E4 | missing | calculated | not applicable | purchase cost; installed cost; equipment lifetime; maintenance basis; consumables |
| R711 | StruviteCrystallizer | Digestate Treatment and Nutrient Recovery | E2 | missing | missing | not applicable | energy balance; power demand; purchase cost; installed cost; equipment lifetime; maintenance basis |
| S711 | CrystalSeparator | Digestate Treatment and Nutrient Recovery | E4 | missing | calculated | not applicable | purchase cost; installed cost; equipment lifetime; maintenance basis; consumables |
| W711 | NutrientProductWasher | Digestate Treatment and Nutrient Recovery | E1 | missing | missing | not applicable | energy balance; power demand; purchase cost; installed cost; equipment lifetime; maintenance basis |
| D711 | NutrientProductDryer | Digestate Treatment and Nutrient Recovery | E4 | missing | calculated | calculated | kinetics; purchase cost; installed cost; equipment lifetime; maintenance basis; consumables |
| M721 | AlkalineConditioner | Digestate Treatment and Nutrient Recovery | E4 | missing | calculated | not applicable | purchase cost; installed cost; equipment lifetime; maintenance basis |
| H721 | ProcessHeater | Digestate Treatment and Nutrient Recovery | E4 | missing | missing | calculated | power demand; purchase cost; installed cost; equipment lifetime; maintenance basis; consumables |
| A721 | AmmoniaStripper | Digestate Treatment and Nutrient Recovery | E3 | missing | calculated | calculated | kinetics; energy balance; purchase cost; installed cost; equipment lifetime; maintenance basis; consumables |
| A722 | AcidAbsorber | Digestate Treatment and Nutrient Recovery | E2 | missing | missing | not applicable | energy balance; power demand; purchase cost; installed cost; equipment lifetime; maintenance basis |
| V722 | ProductStorage | Digestate Treatment and Nutrient Recovery | E1 | missing | missing | not applicable | energy balance; power demand; purchase cost; installed cost; equipment lifetime; maintenance basis; consumables |
| M798 | Mixer | Digestate Treatment and Nutrient Recovery | E0 | not applicable | not applicable | not applicable | none identified at this maturity level |
| M799 | Mixer | Digestate Treatment and Nutrient Recovery | E0 | not applicable | not applicable | not applicable | none identified at this maturity level |
| T101 | StorageTank | Feed Preparation and Primary Separation | E4 | available | missing | not applicable | power demand; equipment lifetime; maintenance basis; consumables |
| S101 | Splitter | Feed Preparation and Primary Separation | E0 | not applicable | not applicable | not applicable | none identified at this maturity level |
| S609 | Splitter | Biogas Conditioning and Upgrading | E0 | not applicable | not applicable | not applicable | none identified at this maturity level |
| M621 | MembraneStage | Biogas Conditioning and Upgrading | E3 | missing | missing | not applicable | energy balance; power demand; purchase cost; installed cost; equipment lifetime; maintenance basis; consumables |
| M622 | MembraneStage | Biogas Conditioning and Upgrading | E3 | missing | missing | not applicable | energy balance; power demand; purchase cost; installed cost; equipment lifetime; maintenance basis; consumables |
| C621 | IsentropicCompressor | Biogas Conditioning and Upgrading | E4 | available | available | not applicable | equipment lifetime; maintenance basis; consumables |
| E621 | HXutility | Biogas Conditioning and Upgrading | E4 | available | missing | available | power demand; equipment lifetime; maintenance basis; consumables |
| D621 | GasWaterSeparator | Biogas Conditioning and Upgrading | E1 | missing | missing | not applicable | energy balance; power demand; purchase cost; installed cost; equipment lifetime; maintenance basis; consumables |
| M620 | Mixer | Biogas Conditioning and Upgrading | E0 | not applicable | not applicable | not applicable | none identified at this maturity level |
| M628 | Mixer | Biogas Conditioning and Upgrading | E0 | not applicable | not applicable | not applicable | none identified at this maturity level |
| S622 | Splitter | Biogas Conditioning and Upgrading | E0 | not applicable | not applicable | not applicable | none identified at this maturity level |
| M629 | Mixer | Biogas Conditioning and Upgrading | E0 | not applicable | not applicable | not applicable | none identified at this maturity level |
| C631 | IsentropicCompressor | Biogas Conditioning and Upgrading | E4 | available | available | not applicable | equipment lifetime; maintenance basis; consumables |
| D631 | GasWaterSeparator | Biogas Conditioning and Upgrading | E1 | missing | missing | not applicable | energy balance; power demand; purchase cost; installed cost; equipment lifetime; maintenance basis; consumables |
| A631 | PressureSwingAdsorber | Biogas Conditioning and Upgrading | E4 | missing | available | not applicable | purchase cost; installed cost; equipment lifetime; maintenance basis; consumables |
| M630 | Mixer | Biogas Conditioning and Upgrading | E0 | not applicable | not applicable | not applicable | none identified at this maturity level |
| S631 | Splitter | Biogas Conditioning and Upgrading | E0 | not applicable | not applicable | not applicable | none identified at this maturity level |
| M639 | Mixer | Biogas Conditioning and Upgrading | E0 | not applicable | not applicable | not applicable | none identified at this maturity level |
| C641 | IsentropicCompressor | Biogas Conditioning and Upgrading | E4 | available | available | not applicable | equipment lifetime; maintenance basis; consumables |
| E640 | HXutility | Biogas Conditioning and Upgrading | E4 | available | missing | available | power demand; equipment lifetime; maintenance basis; consumables |
| A641 | MEAAbsorber | Biogas Conditioning and Upgrading | E3 | missing | missing | not applicable | energy balance; power demand; purchase cost; installed cost; equipment lifetime; maintenance basis; consumables |
| E641 | RichLeanHeatExchanger | Biogas Conditioning and Upgrading | E4 | missing | missing | available | power demand; purchase cost; installed cost; equipment lifetime; maintenance basis; consumables |
| H641 | MEAReboiler | Biogas Conditioning and Upgrading | E4 | missing | missing | available | power demand; purchase cost; installed cost; equipment lifetime; maintenance basis; consumables |
| A642 | MEAStripper | Biogas Conditioning and Upgrading | E3 | missing | missing | not applicable | energy balance; power demand; purchase cost; installed cost; equipment lifetime; maintenance basis; consumables |
| V641 | RefluxCondenser | Biogas Conditioning and Upgrading | E4 | missing | missing | available | power demand; purchase cost; installed cost; equipment lifetime; maintenance basis; consumables |
| E643 | LeanHeatRecovery | Biogas Conditioning and Upgrading | E4 | missing | missing | available | power demand; purchase cost; installed cost; equipment lifetime; maintenance basis; consumables |
| P641 | Pump | Biogas Conditioning and Upgrading | E4 | available | available | not applicable | equipment lifetime; maintenance basis; consumables |
| E642 | HXutility | Biogas Conditioning and Upgrading | E4 | available | missing | available | power demand; equipment lifetime; maintenance basis; consumables |
| M641 | Mixer | Biogas Conditioning and Upgrading | E0 | not applicable | not applicable | not applicable | none identified at this maturity level |
| R712 | CalciumPhosphateReactor | Digestate Treatment and Nutrient Recovery | E2 | missing | missing | not applicable | energy balance; power demand; purchase cost; installed cost; equipment lifetime; maintenance basis |
| S712 | CrystalSeparator | Digestate Treatment and Nutrient Recovery | E4 | missing | available | not applicable | purchase cost; installed cost; equipment lifetime; maintenance basis; consumables |
| W712 | NutrientProductWasher | Digestate Treatment and Nutrient Recovery | E1 | missing | missing | not applicable | energy balance; power demand; purchase cost; installed cost; equipment lifetime; maintenance basis |
| D712 | NutrientProductDryer | Digestate Treatment and Nutrient Recovery | E4 | missing | available | available | kinetics; purchase cost; installed cost; equipment lifetime; maintenance basis; consumables |
| A731 | IonExchangeBed | Digestate Treatment and Nutrient Recovery | E3 | missing | missing | not applicable | kinetics; energy balance; power demand; purchase cost; installed cost; equipment lifetime; maintenance basis; consumables |
| R731 | IonExchangeRegeneration | Digestate Treatment and Nutrient Recovery | E4 | missing | available | not applicable | purchase cost; installed cost; equipment lifetime; maintenance basis |
| E741 | PotassiumEvaporator | Digestate Treatment and Nutrient Recovery | E4 | missing | available | available | purchase cost; installed cost; equipment lifetime; maintenance basis; consumables |
| M741 | PotassiumMembraneConcentrator | Digestate Treatment and Nutrient Recovery | E4 | missing | available | not applicable | purchase cost; installed cost; equipment lifetime; maintenance basis; consumables |
| V741 | ProductStorage | Digestate Treatment and Nutrient Recovery | E1 | missing | missing | not applicable | energy balance; power demand; purchase cost; installed cost; equipment lifetime; maintenance basis; consumables |

## Consolidated Missing Data

### Feedstock
Monthly availability is workbook-controlled, but project laboratory composition, density, pH, solids, COD, elemental pools, and uncertainty distributions remain incomplete. Missing measurements are not silently replaced with value-generating defaults.

### Protein Recovery
Project titration curves, precipitation or coagulation recoveries, separation performance, product quality, drying trials, and vendor costs are required. The 17 protein-recovery CSV datasets remain disconnected because several required values and validators are missing.

### Anaerobic Digestion
BMP or continuous-reactor calibration, kinetics, inhibition data, measured gas partitioning, digestate validation, heat-loss measurements, and equipment quotations remain required. R501 is not ADM1.

### Biogas Upgrading
Vendor curves, media lifetime, methane slip, gas specifications, compression and pumping validation, final storage or grid injection, and a CHP definition remain required.

### Nutrient Recovery
Full ionic analyses, activity or electrolyte treatment, pH titration, precipitation and stripping pilot data, product purity and moisture, reagent use, energy integration, and vendor prices remain required.

### Drying
Protein and nutrient drying use screening-level moisture, loss, heat, and power relationships. Drying kinetics, air psychrometrics, equipment geometry, emissions control, and vendor costs are not validated.

### Filtration
Separation and membrane units require measured rejection, flux, fouling, pressure-drop, cleaning, membrane lifetime, and module-cost data before design claims.

### Shared Utilities
No active CHP or plant-wide utility network exists. Heat recovery and electricity production remain explicit missing interfaces and default to zero rather than being inferred.

### Equipment Economics
Custom units intentionally have no invented CAPEX, installed-cost, lifetime, or maintenance basis. Built-in BioSTEAM correlations are reported where active but remain subject to their stated validity ranges.

### Process Validation
Conservation tests are extensive, but conservation alone does not validate yields, kinetics, equilibrium, energy demand, equipment sizing, product eligibility, or economics. Project measurements and pilot comparisons remain necessary.

The complete field set and one row per selected or implemented scenario-only unit ID are available in `Greenhub/results/model_completeness.csv`.
