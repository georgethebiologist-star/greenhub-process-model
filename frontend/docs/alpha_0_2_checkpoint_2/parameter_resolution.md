# Canonical Parameter Resolution

## Precedence

Resolution is deterministic and applies hard applicability gates before ranking candidates:

1. run-specific user override;
2. saved project override;
3. measured project value;
4. calibrated value;
5. transferable literature default;
6. structural workbook assumption;
7. missing or blocked.

An equal-rank, equal-specificity tie is blocked rather than selected by file order. Scenario, month, technology, material, and calculation-mode applicability must match. Unit conversion occurs only through the explicit conversion table; the resolver never guesses a unit.

## Modes

- `structural` preserves existing workbook assumptions and behavior.
- `literature_default` may select a transferable, active literature candidate.
- `project_data` and `calibrated` are represented but cannot fabricate absent inputs.
- `expert_override` is required for expert scientific overrides; values are validated and retained as run provenance.

`quasi_dynamic` and `dynamic` are represented but return a blocking validation issue. They are never silently downgraded. `steady_state` and existing monthly-independent model behavior remain available.

## Source Protection

Overrides are immutable run records and are never written to the master workbook or literature CSVs. The original 301 source datasets remain unchanged. Canonical, editable, and activation registries are generated overlays under `Greenhub/data/advanced_model/`.
