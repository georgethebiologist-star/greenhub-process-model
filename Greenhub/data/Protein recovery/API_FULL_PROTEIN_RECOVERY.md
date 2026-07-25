# GreenHub Dataset API

## Core architecture

ProductionModel
 |- FeedState
 |- ProteinRecovery
 |   |- IsoelectricRecovery
 |   |- LacticFermentationRecovery
 |- MembraneSystem
 |- DryingSystem
 |- Utilities
 |- Reports

## Standard workflow

1. Read feed composition.
2. Build component vector.
3. Choose process scenario.
4. Validate mandatory inputs.
5. Solve dynamic equations.
6. Update stream composition.
7. Pass stream to downstream unit.
8. Store assumptions.
9. Export reports.

## Data exchange

Each unit exports:

Mass flow
Component composition
Protein state
Moisture
Temperature
pH
Energy demand
Chemical consumption
Utilities
CAPEX/OPEX variables

These become direct inputs for the following unit.

## Coding rules

Never hard-code constants.

Always load values from CSV.

Unknown parameters must be loaded from the assumption register.

Every equation should reference the Equation Registry.

All units must preserve mass and elemental balances.

