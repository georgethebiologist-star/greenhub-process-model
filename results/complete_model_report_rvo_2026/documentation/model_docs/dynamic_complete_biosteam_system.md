# Dynamic Complete BioSTEAM System

`Greenhub.dynamic_downstream_biosteam` extends the isolated calculation-owning
protein shadow system with BioSTEAM units for residual AD, one selected gas
route, and the configured sequential resource-recovery train. It is opt-in and
does not register streams or units in the empirical GreenHub flowsheet.

An isolated [reporting and dashboard service](dynamic_dashboard_reporting.md)
now aggregates this chain on a 30,000 t/year seasonal processing schedule.
It checks monthly BioSTEAM parity and reports hourly, monthly and scheduled
annual units, with separate optional annualization and unvalidated analysis.

## Default system boundary

The default May-November route is whole feed through raw pressing, two
centrifuges, isoelectric protein extraction, drying to 15% moisture, residual
AD, water-scrubbing upgrading, digestate separation, ammonia recovery,
phosphorus recovery, potassium/water concentration, and ion exchange. Press
cake remains an external system output and is never an AD input.

The downstream BioSTEAM unit classes are:

- `DynamicADProxyUnit`
- `DynamicGasConditioningUnit`
- `DynamicBiogasUpgradingUnit`
- `DynamicCHPProxyUnit`
- `DynamicDigestateSeparationUnit`
- `DynamicAmmoniaRecoveryUnit`
- `DynamicPhosphorusRecoveryUnit`
- `DynamicPotassiumWaterConcentrationUnit`
- `DynamicIonExchangeUnit`

Each unit scales the authoritative `dynamic_complete_proxy.py` transformation
from its actual BioSTEAM inlet mass. Source policy IDs, evidence records,
warnings, metrics, and blockers remain attached to the unit payload.

## Chemicals and metadata

Methane, carbon dioxide, ammonia, hydrogen sulfide, water, potassium ion, and
struvite use existing GreenHub chemicals. Abstract ledger identities remain in
parallel records. Declared existing bookkeeping carriers provide BioSTEAM mass
closure: dry matter uses `OtherBiodegradableOrganics`, recovered-N equivalents
use `OrganicNitrogen`, unresolved carrier/reagent mass uses
`SolubleInertSolids`, and CHP flue-gas equivalent uses `CarbonDioxide`. These
carrier assignments are not molecular-speciation claims.

The fructan and residual-unallocated-DM pools omitted from the protein adapter
enter AD through an explicit metadata-carrier stream. This bridge is reported
and is never confused with press cake.

## Status

The system validates exact represented components, parallel metadata, every
downstream output, protein shadow parity, mass closure, press-cake exclusion,
and empirical registry restoration. Nevertheless, all calculations retain the
proxy/assumption evidence of the complete ledger. Therefore
`can_drive_simulation=False` and `validated_simulation_ready=False`.

Project measurements are still required for AD conversion and elemental
routing, gas-system performance at GreenHub scale, ionic digestate speciation,
resource-product quality, reagents, utilities, and equipment design/costing.
