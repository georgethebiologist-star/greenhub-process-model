# Mechanical Partition Evidence Summary

This report audits source evidence only. It does not activate dynamic or empirical calculations.

## Record Status

- Candidate partition rows: `74`
- Context/composition/yield rows: `88`
- Eligible scalar rows at the selected boundary: `48`
- Blocked candidate rows: `26`

## Selected Complete Triplets

| Pool | Closure | Class | Disposition |
|---|---:|---|---|
| carbon | 0.936369 | element_only_metadata | metadata_or_validation_only |
| total nitrogen | 0.928484 | element_only_metadata | metadata_or_validation_only |
| total phosphorus | 0.908525 | element_only_metadata | metadata_or_validation_only |
| total potassium | 0.733073 | element_only_metadata | metadata_or_validation_only |
| total solids | 0.925943 | aggregate_pool_metadata | metadata_or_validation_only |
| total sulfur | 0.941869 | element_only_metadata | metadata_or_validation_only |
| volatile solids | 0.933575 | aggregate_pool_metadata | metadata_or_validation_only |
| water | 1.017012 | exact_component_candidate | closure_correction_fallback_candidate |

## Interpretation

Water is the only exact component candidate. Its selected shares total `1.017012`, so the conservative policy blocks it unless an explicit closure-correction policy is supplied.
TS, VS, C, N, P, K, and S are aggregate or elemental metadata and are not mapped to GreenHub components.
Protein, WSC species, ash, and structural-fiber components do not have complete source-compatible triplets for this selected boundary.

## Warnings

- Source ranges remain ranges; no midpoint was calculated.
- Complete elemental triplets are metadata and are not mapped to Ash.
- The selected boundary includes downstream protein recovery and is not raw pressing only.
