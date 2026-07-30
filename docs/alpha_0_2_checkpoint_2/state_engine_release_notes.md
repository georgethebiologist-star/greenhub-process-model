# State-engine continuation release notes

This continuation adds an additive process-state layer to the active reference
pathway. States are derived from canonical resolved parameters and existing
BioSTEAM stream results; unavailable scientific inputs remain explicit
structural fallbacks. Quasi-dynamic mode now emits a bounded state history and
inventory records without a continuous ODE solver. New JSON/CSV-ready result
collections cover snapshots, history, unit summaries, equation use, sensitivity
availability, component fate, utilities, and inventory evolution. Three state
plots are included in the existing plot service.

No blocked dataset was activated. The pathway remains structural except for the
previously connected D4 precipitation parameter. API and workbook input
contracts remain unchanged.
