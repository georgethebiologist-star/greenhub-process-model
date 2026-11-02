# Cost Overlap Resolution

Checkpoint 1 permits no new literature cost aggregation.

## Audit Status

- Potential cost issue rows: 49.
- Cross-dataset overlap groups: 24.
- Ownership groups resolved: 0.
- Cost records selected: 0.

The global overlap register identifies variables that occur in multiple datasets. It
does not establish whether values are alternatives, duplicated package costs, shared
facilities, or differently scoped observations. Summing them would risk double
counting.

## Ownership Contract

Every future selected cost record must identify the owning unit or facility, included
and excluded equipment, cost basis, currency, cost year, capacity basis, scaling
equation or exponent, direct source, overlap group, and selected/non-selected state.
Shared skid, common utility, tank, pump, compressor, instrumentation, replacement,
chemical, and maintenance costs remain separate categories.

`Greenhub/data/global_audit_package/cost_ownership_registry.csv` records all 24 groups
as `blocked` and `not_selected`. Blank source facts are represented as `missing`, not
zero.

## Resolution Procedure

1. Inspect all datasets in one overlap group and their direct sources.
2. Define the equipment and system boundary for every record.
3. Assign one owner and explicit inclusions/exclusions.
4. Reconcile currency, year, capacity, technology, and scale.
5. Decide whether records are alternatives, calibration points, or true duplicates.
6. Select at most the applicable non-overlapping records.
7. Add cost ownership and no-double-counting tests before future TEA reporting.
