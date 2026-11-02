# Dynamic integrated proxy pathway

## Scope

`Greenhub.dynamic_integrated_proxy` is an isolated, opt-in backend preview. It
composes the calculation-owning protein shadow system with drying-energy, BMP,
biogas-upgrading, and resource-recovery previews. It does not connect to the
empirical flowsheet, seasonal service, API, or frontend.

## Selected defaults

- Protein: `isoelectric`, using the explicitly labelled `REC-001` N-to-protein
  proxy. `lactic_acid` (`PR-005`) and `membrane` (`REJ-001`) are selectable,
  calculation-owning alternatives. Heat is blocked by missing recovery data;
  generic requires a caller-supplied recovery policy.
- Drying: `mass_only`, with target product moisture `0.15`. The drying datasets
  provide operating envelopes but no transferable scalar heat/electric demand,
  so energy remains blocked rather than inferred.
- AD: `bmp_potential_only`. Residual VS is estimated from explicit organic
  components and labelled residual-DM proxy pools. `BMP_DFOS_VS`, methane
  fraction, and T80/T90 markers calculate potential gas; AD kinetics and
  digestate conversion are not run.
- Upgrading: `none`. Membrane, water scrubbing, and PSA have separate
  source-backed preview policies. MEA lacks methane recovery/slip, common
  conditioning is not CO2 upgrading, and CHP is an energy route rather than a
  biomethane-separation method.
- Fertilizer recovery: none selected. Ammonia, phosphorus, potassium/water,
  digestate separation, and ion exchange expose dataset availability and exact
  missing inputs. No elemental-to-ionic speciation is invented.

Press cake remains an external system output. Only cell debris and final
supernatant enter the residual/BMP boundary.

## Outputs and activation

The grid runner covers May-November 2026 and writes five CSV reports under
`Greenhub/results/`: summary, streams, units, alternatives, and blockers.
`can_drive_proxy_preview` and the isolated protein calculation-shadow flag may
be true, but `can_drive_simulation` and `validated_simulation_ready` remain
false. Validation requires project separation data, dryer duties, AD conversion
and digestate balances, gas conditioning constraints, and nutrient speciation.
