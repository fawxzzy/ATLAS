# Playbook Preserved Proof/Test Branch Disposal Decision - 2026-05-26

- Date: `2026-05-26`
- Lane: `Playbook preserved proof/test branch disposal decision`
- Mode: `docs-only post-preservation disposition`
- Control-plane checkpoint: `main@885dfe6`

## Scope

Decide the post-preservation disposition of only the four Playbook proof/test branches preserved in:

- `docs/ops/PLAYBOOK-EXTERNAL-SMOKE-PRESERVATION-EXPORT-PACKET-2026-05-26.md`

In scope:

- `codex/codex-inbox-proof-docs-touch-2`
- `codex/mock-stdin-smoke-nine`
- `codex/mock-watcher-smoke-five`
- `codex/mock-watcher-smoke-six`

Out of scope:

- `smoke-home`
- Playbook stashes
- Lifeline retained worktrees
- active repo roots
- `archive/`
- any branch or worktree deletion

## Operating Posture

- ATLAS root remains the control-plane and receipt layer
- preservation and disposal remain separate governance steps
- this pass is decision-only
- no owner-repo tracked content is changed
- no external services are touched
- `Fitness Supabase Profile/Data Hygiene` stays closed at `100%`

## Inputs

- current ATLAS root `main@885dfe668e67e5cb6e679df9eb8d110a746c1f8c`
- `docs/ops/PLAYBOOK-EXTERNAL-SMOKE-EXPORT-ARCHIVE-AND-SMOKE-HOME-MANUAL-REVIEW-DECISION-2026-05-26.md`
- `docs/ops/PLAYBOOK-EXTERNAL-SMOKE-PRESERVATION-EXPORT-PACKET-2026-05-26.md`
- `packages/patches/playbook-external-smoke-preservation-2026-05-26/manifest.json`
- current branch metadata for `repos/fawxzzy-playbook`
- commit inspection for the four preserved branch heads

## Preservation Confirmation

Confirmed present and complete in the tracked preservation packet:

| Branch | Commit | Artifact |
| --- | --- | --- |
| `codex/codex-inbox-proof-docs-touch-2` | `bce63a8634120189be5a5d379e055d21ed557a9f` | `packages/patches/playbook-external-smoke-preservation-2026-05-26/codex-codex-inbox-proof-docs-touch-2-bce63a86.patch` |
| `codex/mock-stdin-smoke-nine` | `cb77456666c7da45210c6ea655781432d5e8e10a` | `packages/patches/playbook-external-smoke-preservation-2026-05-26/codex-mock-stdin-smoke-nine-cb774566.patch` |
| `codex/mock-watcher-smoke-five` | `c494750e7b3829a3f1f5c5feca8a02c8493c62b2` | `packages/patches/playbook-external-smoke-preservation-2026-05-26/codex-mock-watcher-smoke-five-c494750e.patch` |
| `codex/mock-watcher-smoke-six` | `245ed3a4dc13f690703d789783a7f4ad5f81fdf2` | `packages/patches/playbook-external-smoke-preservation-2026-05-26/codex-mock-watcher-smoke-six-245ed3a4.patch` |

Result:

- preservation is satisfied for all four branches
- reversibility is now artifact-backed rather than branch-backed
- no additional live branch retention is needed for evidence purposes

## Branch Read

Each in-scope branch still shows the same proof/test structure already established in the prior packet:

| Branch | HEAD | Commit summary | Live-use read |
| --- | --- | --- | --- |
| `codex/codex-inbox-proof-docs-touch-2` | `bce63a86` | `docs: record codex inbox proof run` | one-off docs proof artifact, not active owner work |
| `codex/mock-stdin-smoke-nine` | `cb774566` | `test: mock stdin smoke nine` | one-line smoke proof, not product/runtime work |
| `codex/mock-watcher-smoke-five` | `c494750e` | `test: mock watcher smoke five` | one-line smoke proof, not product/runtime work |
| `codex/mock-watcher-smoke-six` | `245ed3a4` | `test: mock watcher smoke six` | one-line smoke proof, not product/runtime work |

Why none should merge into active owner work:

- each branch is a single isolated proof/test commit created by `Codex Inbox Runner`
- each branch is already behind `origin/main` and does not represent ongoing branch lineage worth normalizing into current Playbook work
- the useful evidence is the preserved patch payload, not continued branch existence
- merging would import stale proof/test residue into active owner history without solving a live product or doctrine need

## Disposition Table

| Branch | Disposition class | Decision | Why | Next owner-safe action |
| --- | --- | --- | --- | --- |
| `codex/codex-inbox-proof-docs-touch-2` | dispose after preservation | decision-cleared for disposal | preserved docs proof commit has durable artifact coverage and no continuing owner-work value as a live branch | open a branch-disposal execution pass that removes only the preserved proof/test branch surface |
| `codex/mock-stdin-smoke-nine` | dispose after preservation | decision-cleared for disposal | preserved one-line smoke commit has durable artifact coverage and no continuing reference value as a live branch | open a branch-disposal execution pass that removes only the preserved proof/test branch surface |
| `codex/mock-watcher-smoke-five` | dispose after preservation | decision-cleared for disposal | preserved one-line smoke commit has durable artifact coverage and no continuing reference value as a live branch | open a branch-disposal execution pass that removes only the preserved proof/test branch surface |
| `codex/mock-watcher-smoke-six` | dispose after preservation | decision-cleared for disposal | preserved one-line smoke commit has durable artifact coverage and no continuing reference value as a live branch | open a branch-disposal execution pass that removes only the preserved proof/test branch surface |

## Boundary Confirmation

This pass does not reopen or absorb:

- `smoke-home`
- Playbook stashes
- Lifeline retained worktrees
- active Playbook repo work
- any Fitness or DiscordOS lane state

`smoke-home` remains a separate stranded-checkout manual-review case and should not inherit this branch-disposal decision.

## Marker Confirmation

Confirmed unchanged:

- `Inventory & Truth Map`: `74%`
- `Full Stack Re-sync, Clean & Closeout`: `85%`
- `Truth Map & ATLAS Book`: `85%`
- `Discord OS Infrastructure Separation`: `95%`

No marker movement is justified by this pass.

## Recommended Follow-On Packages

1. `Playbook preserved proof/test branch disposal execution`
2. `Playbook smoke-home stranded checkout disposal/manual-review packet`

Recommended ordering:

- execute the now-cleared preserved-branch disposal pass first
- keep `smoke-home` isolated as its own checkout-disposal question second

## Validation

Executed:

- `python .\\ops\\validation\\validate_stack.py`

Result:

- `critical=0 error=0 warning=306`

## Files Changed

- `docs/atlas-book/01-current-state.md`
- `docs/atlas-book/05-receipt-index.md`
- `docs/atlas-book/12-restart-and-handoff-guide.md`
- `docs/ops/PLAYBOOK-PRESERVED-PROOF-TEST-BRANCH-DISPOSAL-DECISION-2026-05-26.md`

## Next Package

`Playbook preserved proof/test branch disposal execution`

Why:

- preservation is complete
- disposal is now explicitly decision-cleared
- `smoke-home` remains outside this disposal scope
