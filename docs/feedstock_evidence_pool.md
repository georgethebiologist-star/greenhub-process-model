# Feedstock Evidence Pool

`build_feedstock_evidence_pool()` creates one report-only table for feedstock evidence. It does not activate calculations, create `model_overrides`, change empirical defaults, or select values for the model.

## Included Evidence

- measured project data supplied by the caller
- user overrides supplied by the caller
- direct literature rows
- derived literature rows
- indirect proxy rows
- engineering assumptions from the feedstock assumption register
- missing rows

## Current national roadside-availability evidence (staged only)

The evidence register includes four additional B-tier records from two traceable sources:

- Rijkswaterstaat's current motorway verge maintenance page reports **more than 18,000 ha** of managed motorway verges and says most grass mowing occurs once per year. This is total verge area, not eligible grass area or a GreenHub supply contract: [Rijkswaterstaat, Bermonderhoud](https://www.rijkswaterstaat.nl/leefomgeving/leefbaarheid-en-milieu/bermonderhoud).
- Wageningen Research Report 2415 reports **115,000 t dry matter/year** of grass mixed with other herbaceous biomass on RWS-managed sites, which include verges and canal banks; its Table 7 separately reports other biomass categories. This is not pure grass, not roadside-only supply, and not metered delivery. [DOI 10.18174/630159](https://doi.org/10.18174/630159), p. 18, section 2.1.6 and Table 7.
- The same report gives a broad **3–5 t DM/ha** road-verge biomass snapshot and states a corresponding transport range of **12–20 t fresh/ha**. It warns that the yield is a current-situation snapshot and can decline with more intensive removal; paired endpoints, accessible area, removal fraction, collection losses, and moisture are not established.

These records are staged evidence, not active defaults or calculation inputs. Do not multiply the RWS total area by the national yield range to claim a deliverable annual feedstock supply: the area scope, vegetation mix, spatial overlap, competing ecological uses, safe/accessible harvest area, harvest fraction, contamination, and logistics are not resolved. The rows support a future spatially constrained availability calculation, but do not replace the current explicit user feed-supply assumption.

## Required Flags

Each row includes:

- `canonical_field`
- `parameter_id`
- `value`, `value_min`, `value_max`, `raw_value`
- `unit`
- `source`
- `certainty_class`
- `use_status`
- `confidence_score`
- `requires_user_confirmation`
- `limitation_note`

## Certainty Classes

- `measured_project`: 1.0
- `direct_literature`: 0.75
- `derived_from_literature`: 0.65
- `indirect_proxy`: 0.4
- `engineering_assumption`: 0.25
- `user_override`: 0.5 by default, 0.6 when source metadata is supplied
- `missing`: 0.0

Confidence scores are reporting metadata only. They must not change calculations until a separate activation path is designed and tested.

## Use Status

- `report_only_candidate`: visible for review, not active
- `requires_confirmation`: needs explicit user or reviewer acceptance
- `reference_only`: useful context but not a candidate default
- `blocked_report_only`: visible as a gap, not usable for activation

This pool simplifies future activation by letting measured data, literature, proxies, assumptions, overrides, and missing rows share one JSON-safe shape while keeping activation decisions explicit.
