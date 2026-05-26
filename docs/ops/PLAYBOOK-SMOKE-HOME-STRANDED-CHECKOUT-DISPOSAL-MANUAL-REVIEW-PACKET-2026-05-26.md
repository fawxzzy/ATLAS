# Playbook Smoke-Home Stranded Checkout Disposal Manual-Review Packet - 2026-05-26

- Date: `2026-05-26`
- Lane: `Playbook smoke-home stranded checkout disposal/manual-review packet`
- Mode: `docs-only stranded-checkout review`
- Control-plane checkpoint: `main@96d6186`

## Scope

Inspect and classify only the stranded `smoke-home` Playbook checkout identified in:

- `docs/ops/PLAYBOOK-EXTERNAL-SMOKE-EXPORT-ARCHIVE-AND-SMOKE-HOME-MANUAL-REVIEW-DECISION-2026-05-26.md`

In scope:

- the user-home `smoke-home` checkout
- the remaining `repos/fawxzzy-playbook/.git/worktrees/smoke-home` admin entry
- the `codex/home-smoke` branch surface only as evidence for checkout value/readiness

Out of scope:

- Playbook stashes
- Lifeline retained worktrees
- active repo roots
- `archive/`
- any broader branch/worktree cleanup
- any checkout deletion execution

## Operating Posture

- ATLAS root remains the coordination and receipt layer
- this pass is decision-only
- `smoke-home` stays isolated from the already-closed proof/test branch family
- no owner-repo tracked content is changed
- no external services are touched
- `Fitness Supabase Profile/Data Hygiene` stays closed at `100%`

## Inputs

- current ATLAS root `main@96d6186f5969464b476a26dcf9a5ca97fc9654b6`
- `docs/ops/PLAYBOOK-EXTERNAL-SMOKE-EXPORT-ARCHIVE-AND-SMOKE-HOME-MANUAL-REVIEW-DECISION-2026-05-26.md`
- `docs/ops/PLAYBOOK-PRESERVED-PROOF-TEST-BRANCH-DISPOSAL-EXECUTION-2026-05-26.md`
- current Playbook branch/worktree metadata
- direct filesystem inspection of the stranded `smoke-home` checkout

## Evidence

### Git pointer / admin state

Observed state:

- the `smoke-home` checkout `.git` file still points at an old user-home Playbook gitdir target that no longer exists
- the ATLAS-side Playbook worktree admin entry at `repos/fawxzzy-playbook/.git/worktrees/smoke-home` still exists
- that surviving admin entry still maps `HEAD` to `refs/heads/codex/home-smoke`
- the branch `codex/home-smoke` remains behind-only from `origin/main`
- `codex/home-smoke` resolves to `11859f21`, which is also the merge-base with `origin/main`

Decision-relevant read:

- the checkout is stranded because its user-home gitdir target is gone
- the remaining live surface is the directory plus the surviving ATLAS-side worktree admin metadata
- this is a local checkout residue case, not active branch lineage and not preservation-first branch content

### Content / divergence state

Observed state:

- `git status --short` against the surviving ATLAS-side worktree admin is empty
- `git diff --stat` against the stranded checkout is empty
- the checkout carries no staged, modified, or untracked payload
- branch-tree vs checkout-tree comparison found no extra checkout-only files
- the only path-count mismatch comes from a Windows case-collision pair in the branch tree:
  - `docs/CONTRIBUTING.md`
  - `docs/contributing.md`

Decision-relevant read:

- no local-only content was found that would justify export or further preservation
- the case-collision mismatch is a filesystem representation artifact on Windows, not evidence of unique operator work inside `smoke-home`
- the stranded checkout is functionally clean residue, not a value-bearing live workspace

## Disposition

| Surface | Decision class | Decision | Why | Next owner-safe action |
| --- | --- | --- | --- | --- |
| user-home `smoke-home` stranded checkout plus `repos/fawxzzy-playbook/.git/worktrees/smoke-home` admin entry | safe to dispose after manual review | decision-cleared for disposal execution | missing user-home gitdir target, no staged/modified/untracked payload, no checkout-only files, no preservation need, and branch is only a behind-only merge-base surface | open a bounded disposal execution pass that removes only the stranded checkout directory, the surviving worktree admin entry, and the `codex/home-smoke` local branch if still attached solely to that surface |

## Boundary Confirmation

This pass does not reopen or absorb:

- Playbook stashes
- Lifeline retained worktrees
- active Playbook repo work
- preserved proof/test branch disposal
- any Fitness or DiscordOS lane state

## Marker Confirmation

Confirmed unchanged:

- `Inventory & Truth Map`: `74%`
- `Full Stack Re-sync, Clean & Closeout`: `85%`
- `Truth Map & ATLAS Book`: `85%`
- `Discord OS Infrastructure Separation`: `95%`

No marker movement is justified by this pass.

## Recommended Follow-On Packages

1. `Playbook smoke-home stranded checkout disposal execution`
2. `DiscordOS-owned or preview/unfurl follow-on lanes only through their existing owners/gates`

Recommended ordering:

- consume the now-cleared `smoke-home` disposal class in its own execution pass
- keep stashes and Lifeline retained worktrees blocked and out of scope

## Validation

Executed:

- `python .\\ops\\validation\\validate_stack.py`

Result:

- `critical=0 error=0 warning=306`

## Files Changed

- `docs/atlas-book/01-current-state.md`
- `docs/atlas-book/05-receipt-index.md`
- `docs/atlas-book/12-restart-and-handoff-guide.md`
- `docs/ops/PLAYBOOK-SMOKE-HOME-STRANDED-CHECKOUT-DISPOSAL-MANUAL-REVIEW-PACKET-2026-05-26.md`

## Next Package

`Playbook smoke-home stranded checkout disposal execution`

Why:

- the manual-review question is now settled
- no further preservation is justified
- the remaining work is a narrowly bounded local disposal pass
