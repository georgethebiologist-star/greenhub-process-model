# Git History And Deletion Audit

Audit date: 2026-07-29

## Repository State

| Field | Value |
|---|---|
| Current branch | `early-front-end` |
| HEAD | `6ba0493c007df20c9f94dbf78b9214911c738044` (`API wrapped`) |
| Scientific snapshot | `031f1661ac0ed7de2e02f8098159305237cf9f99` (`GreenHub process model repository`) |
| Other branch | `main` at `031f166` |
| Tags | None |
| Baseline worktree | Clean |

Only normal Git commands were used. Protected application directories were excluded
from every path-limited scientific diff.

## Available Scientific History

The initial commit `031f166` adds the complete scientific repository in one snapshot:
357 files and 33,104 inserted lines, with no predecessor implementation in this Git
graph. It already contains all historical Phase 2-7 modules, tests, workbook backups,
reports, documentation, and the protein-recovery dataset suite.

Between `031f166` and HEAD, the only allowed-tree change is two added dependency lines
in `requirements.txt`. The current stash also changes only these two dependency lines
within the allowed scientific path set.

## Deletion And Rename Queries

| Query | Result |
|---|---|
| `git log --all --diff-filter=D --name-status -- Greenhub tests docs ...` | No deletions |
| `git log --all --diff-filter=R --summary -- Greenhub tests docs ...` | No renames |
| `git diff --numstat 031f166..HEAD -- Greenhub tests docs ...` | `requirements.txt`: +2/-0 |
| `git diff --name-status 031f166..HEAD -- Greenhub tests docs ...` | Only `requirements.txt` modified |

## Large-Deletion Finding

The reported Phase 6-to-Phase 7 change of approximately +7,000/-14,000 lines cannot be
confirmed, disproved, or reconstructed from this repository. No commit in the available
graph records that transition. The available evidence begins after the transition as a
single consolidated snapshot.

Status: **cannot verify**.

## Capability-Loss Conclusions

- Confirmed lost capabilities: none from available Git evidence.
- Suspected lost capabilities: CHP/plant utility integration is required by an
  available Phase 6 prompt but is explicitly absent in current code and documentation.
  Whether it was deleted or never implemented cannot be determined.
- Disconnected capabilities: the protein-recovery CSV suite describes dynamic
  fermentation, membrane, and drying models but is not connected to Python loaders or
  scenario factories.
- Intentionally data-gated capabilities: PR4-PR6, AD4-AD5, BG1, and BG6.

No historical code is restored solely on filename or line-count evidence. A repository
or bundle containing the missing incremental commits is required for a true deletion
audit.

