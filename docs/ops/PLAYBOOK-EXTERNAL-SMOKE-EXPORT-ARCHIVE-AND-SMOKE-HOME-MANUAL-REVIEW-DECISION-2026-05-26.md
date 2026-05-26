# Playbook External Smoke Export/Archive And Smoke-Home Manual-Review Decision - 2026-05-26

- Date: `2026-05-26`
- Lane: `Playbook external smoke export/archive and smoke-home manual-review decision`
- Mode: `docs-only preservation/manual-review classification`
- Control-plane checkpoint: `main@d3c7ffd`

## Scope

Classify only the remaining Playbook external-smoke surfaces after:

- `docs/ops/PLAYBOOK-LIFELINE-EXTERNAL-SMOKE-DISPOSAL-DECISION-2026-05-26.md`
- `docs/ops/PLAYBOOK-LIFELINE-RETAINED-SURFACE-DISPOSAL-EXECUTION-PASS-2-2026-05-26.md`

In scope:

- `codex/codex-inbox-proof-docs-touch-2`
- `codex/mock-stdin-smoke-nine`
- `codex/mock-watcher-smoke-five`
- `codex/mock-watcher-smoke-six`
- user-home stranded checkout `.codex/worktrees/fawxzzy-playbook/smoke-home`

Out of scope:

- Playbook stashes
- Lifeline retained worktrees
- active repo roots
- `archive/`
- any deletion or export execution

## Operating Posture

- ATLAS root remains the control-plane and receipt layer
- this pass is decision-only
- no owner-repo tracked content is changed
- no external services are touched
- `Fitness Supabase Profile/Data Hygiene` stays closed at `100%`
- Discord and Music Sesh residue remains routed to `Discord OS Infrastructure Separation`

## Inputs

- current ATLAS root `main@d3c7ffdf6b9b81aa4a16fc86e5f9f3a85169a733`
- current `git branch -vv` for `repos/fawxzzy-playbook`
- current `git worktree list --porcelain` for `repos/fawxzzy-playbook`
- branch commit inspection for the four ahead-by-`1` surfaces
- filesystem comparison between `codex/home-smoke` and the stranded `smoke-home` checkout

## Marker Confirmation

Confirmed unchanged:

- `Inventory & Truth Map`: `74%`
- `Full Stack Re-sync, Clean & Closeout`: `85%`
- `Truth Map & ATLAS Book`: `85%`
- `Discord OS Infrastructure Separation`: `95%`

No marker movement is justified by this pass.

## Evidence

### Ahead-by-`1` proof/test branches

Each remaining prunable branch carries exactly one unique commit relative to `origin/main`:

| Surface | HEAD | Commit summary | Unique payload |
| --- | --- | --- | --- |
| `codex/codex-inbox-proof-docs-touch-2` | `bce63a86` | `docs: record codex inbox proof run` | adds `docs/automation/codex-inbox-proof-run.md` with 9 inserted lines |
| `codex/mock-stdin-smoke-nine` | `cb774566` | `test: mock stdin smoke nine` | adds `mock-stdin-smoke-nine.txt` with 1 inserted line |
| `codex/mock-watcher-smoke-five` | `c494750e` | `test: mock watcher smoke five` | adds `mock-watcher-smoke-five.txt` with 1 inserted line |
| `codex/mock-watcher-smoke-six` | `245ed3a4` | `test: mock watcher smoke six` | adds `mock-watcher-smoke-six.txt` with 1 inserted line |

Observed pattern:

- all four are single-commit proof/test branches
- none represent active product or runtime work
- none justify merge pressure into current Playbook owner work
- all still need preservation before any future branch/worktree disposal because each has unique commit content

### `smoke-home`

Observed state:

- `smoke-home` is still present as a user-home checkout under `.codex/worktrees/fawxzzy-playbook/smoke-home`
- its `.git` file points to a missing historical gitdir location under the old user-home Playbook dev checkout
- the branch `codex/home-smoke` is behind-only from `origin/main`
- `codex/home-smoke` resolves to commit `11859f21`
- `11859f21` is also the merge-base with `origin/main`

Filesystem comparison excluding `.git` internals:

- branch snapshot path count: identical
- checkout path count: identical
- path-only diff count: `0`
- sampled full-file hash diff count: `0`

Decision-relevant read:

- no unique non-`.git` filesystem divergence was found inside `smoke-home`
- `smoke-home` does not currently show evidence of local-only code/content worth export-preserving
- but it is still a full stranded checkout directory, not just a broken metadata registration

## Disposition Table

| Surface | Current class | Decision | Why | Next owner-safe action |
| --- | --- | --- | --- | --- |
| `codex/codex-inbox-proof-docs-touch-2` | export/archive first | retain until preservation packet runs | docs-only unique commit still exists and should be preserved before any disposal | export a one-commit patch or equivalent preservation artifact, then reopen for disposal |
| `codex/mock-stdin-smoke-nine` | export/archive first | retain until preservation packet runs | unique one-line proof commit still exists and should be preserved before any disposal | export a one-commit patch or equivalent preservation artifact, then reopen for disposal |
| `codex/mock-watcher-smoke-five` | export/archive first | retain until preservation packet runs | unique one-line proof commit still exists and should be preserved before any disposal | export a one-commit patch or equivalent preservation artifact, then reopen for disposal |
| `codex/mock-watcher-smoke-six` | export/archive first | retain until preservation packet runs | unique one-line proof commit still exists and should be preserved before any disposal | export a one-commit patch or equivalent preservation artifact, then reopen for disposal |
| user-home stranded checkout `.codex/worktrees/fawxzzy-playbook/smoke-home` | manual review | keep manual-review blocked | no content divergence was found, but this is still a live stranded checkout directory and should not inherit metadata-only delete logic | open a dedicated local checkout disposal/manual-review packet; no export/archive appears necessary unless new local-only evidence is found |

## What This Pass Proves

- no execution-safe delete-now class remains in the Playbook external-smoke family
- the four remaining prunable proof/test branches are preservation-first, not merge-first and not delete-now
- `smoke-home` is not currently a preservation-first case based on content evidence
- `smoke-home` also should not be silently deleted through metadata-cleanup logic because it is a stranded checkout directory, not just metadata

## What Stays Out Of Scope

- Playbook stashes
- Lifeline retained worktrees
- active Playbook repo work
- archive review
- export execution
- checkout deletion execution

## Recommended Follow-On Packages

1. `Playbook external smoke preservation export packet`
2. `Playbook smoke-home stranded checkout disposal/manual-review packet`

Recommended ordering:

- preserve the four unique one-commit proof/test branches first
- review `smoke-home` as its own checkout-disposal question second

## Validation

Executed:

- `python .\\ops\\validation\\validate_stack.py`

Result:

- `critical=0 error=0 warning=306`

## Files Changed

- `docs/ops/PLAYBOOK-EXTERNAL-SMOKE-EXPORT-ARCHIVE-AND-SMOKE-HOME-MANUAL-REVIEW-DECISION-2026-05-26.md`

## Next Package

`Playbook external smoke preservation export packet`

Why:

- it is the first remaining non-gated package that can reduce external-smoke pressure without reopening blocked checkout or stash surfaces
