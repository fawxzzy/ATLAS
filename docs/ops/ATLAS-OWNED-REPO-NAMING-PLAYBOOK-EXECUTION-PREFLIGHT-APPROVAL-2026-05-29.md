# Atlas-Owned Repo Naming Playbook Execution Preflight Approval - 2026-05-29

- Date: `2026-05-29`
- Lane: `Atlas-owned Repo Naming Canonicalization`
- Mode: `docs-only preflight / approval gate`
- Marker posture: `Atlas-owned Repo Naming Canonicalization: 78%`
- Source surfaces:
  - `docs/ops/ATLAS-OWNED-REPO-NAMING-REMAINING-FAMILY-DELTA-RECHECK-PASS-7-2026-05-29.md`
  - `repos/playbook/docs/naming-blocker-compression-pass-6.md`
  - `docs/atlas-book/05-receipt-index.md`
  - `runtime/receipts/validation/stack-validation.latest.md`
- Control-plane checkpoint: `main@9bb230c`

## Objective

Confirm whether `repos/playbook -> repos/playbook` is approved for one bounded naming execution cluster.

This pass does not:

- rename any repo directory
- rename any remote
- assume any GitHub-side rename
- reopen already-durable `stream`, `foundation`, `trove`, `lifeline`, or `mazer` execution families
- reopen any other naming family
- move any marker

## Durable Preflight

- this approval packet is not already durable
- remaining-family delta recheck pass 7 is still current and still selects `playbook` as the one honest safe-next candidate
- no other naming family is reopened by this gate

## Approval Basis

Owner-side evidence consumed:

- `repos/playbook/docs/naming-blocker-compression-pass-6.md` froze the final blocker collapse and candidate-ready posture
- current repo-visible status for `repos/playbook` is `main...origin/main [behind 7]`
- current owner-side `pnpm playbook verify --json` is green
- current owner-side `pnpm playbook docs audit --json` is green

Root-side readiness consumed:

- source path exists: `repos/playbook`
- destination path is clear: `repos/playbook` does not exist
- no exact root-side path collision exists
- the read-only scout identified a bounded must-update root surface set if the rename lands

Owner-side watchlist consumed:

- no exact owner-side pre-rename blocker exists
- immediate post-rename watchlist is limited to path-sensitive tests and fixtures that hardcode `repos/playbook` or `repos/fawxzzy-playbook`
- no runtime or governance surface requires owner-side write-before-rename action

## Root-Side Execution Scope

Execution-cluster rewrite scope is approved as:

- `stack.yaml`
- `stack.lock.yaml`
- `README-STACK.md`
- `docs/registry/STACK-REPO-INVENTORY.json`
- `docs/audits/STACK-REPO-INVENTORY.md`
- `docs/registry/STACK-SYNERGY-REGISTRY.json`
- `docs/architecture/STACK-STANDARDS.md`
- `docs/ops/ATLAS-NEXT-BUILD-QUEUE.md`
- `docs/memory/initiatives/continuity-manifest-atlas-owned-repo-naming-canonicalization.json`
- `ops/atlas/build_codex_context.py`
- `ops/atlas/continuity.py`
- `data/fixtures/atlas.playbook.adoption.report.example.v1.json`
- `tests/test_atlas_codex_context.py`
- candidate-specific execution / proof / closeout receipts
- `docs/atlas-book/05-receipt-index.md`
- `docs/atlas-book/12-restart-and-handoff-guide.md` only if next-ladder wording changes during closeout
- `docs/atlas-book/02-lanes-and-markers.md` only if ratchet is later justified

Replacement-map rules approved:

- replace exact active local-path truth `repos/playbook` -> `repos/playbook`
- replace descendant local-path truth `repos/playbook/...` -> `repos/playbook/...`
- do not blanket-replace bare `fawxzzy-playbook` when it is still remote/project identity, package artifact naming, alias intent, or historical narrative
- do not touch adjacent excluded-surface identity `repos/fawxzzy-playbook-codex`

## Approval Decision

Decision:

- `approved for naming execution cluster`

Why:

- `playbook` remains the one honest safe-next candidate
- owner-side blocker set remains `none`
- destination path is clear
- the root-side must-update surface set is bounded and known
- no exact root-side blocker remains

## Exact Next Move

Open one bounded naming execution cluster only for:

- `repos/playbook -> repos/playbook`

That cluster may now perform:

1. local directory rename
2. exact root-side surface reconciliation
3. root validation
4. conditional owner-side post-rename fixups only if a real break surfaces
5. proof / reconciliation receipt
6. later ratchet closeout as a separate package

## Rule

Approval gate and execution are separate packages.

## Failure Mode

Treating pass 7 candidate selection as automatic approval would skip the exact root-side rewrite set and the bounded owner-side watchlist needed for a clean final naming packet.

