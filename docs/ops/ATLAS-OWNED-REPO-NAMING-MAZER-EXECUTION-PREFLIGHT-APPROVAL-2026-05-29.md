# Atlas-Owned Repo Naming Mazer Execution Preflight Approval - 2026-05-29

- Date: `2026-05-29`
- Lane: `Atlas-owned Repo Naming Canonicalization`
- Mode: `docs-only preflight / approval gate`
- Marker posture: `Atlas-owned Repo Naming Canonicalization: 77%`
- Source surfaces:
  - `docs/ops/ATLAS-OWNED-REPO-NAMING-REMAINING-FAMILY-DELTA-RECHECK-PASS-6-2026-05-28.md`
  - `repos/fawxzzy-mazer/docs/naming-blocker-compression-pass-6.md`
  - `docs/atlas-book/05-receipt-index.md`
  - `runtime/receipts/validation/stack-validation.latest.md`
- Control-plane checkpoint: `main@9bb230c`

## Objective

Confirm whether `repos/fawxzzy-mazer -> repos/mazer` is approved for one bounded naming execution cluster.

This pass does not:

- rename any repo directory
- rename any remote
- assume any GitHub-side rename
- reopen already-durable `stream`, `foundation`, `trove`, or `lifeline` execution families
- reopen `playbook`
- move any marker

## Durable Preflight

- this approval packet is not already durable
- remaining-family delta recheck pass 6 is still current and still selects `mazer` as the one honest safe-next candidate
- `playbook` remains blocked and out of scope for this approval gate

## Approval Basis

Owner-side evidence consumed:

- `repos/fawxzzy-mazer/docs/naming-blocker-compression-pass-6.md` froze the final blocker collapse and candidate-ready posture
- owner-side follow-up preserved the one exact post-rename fix on `main` at `eb78807`
- current repo-visible status for `repos/fawxzzy-mazer` is `main...origin/main [ahead 2]`
- current owner-side verify is green

Root-side readiness consumed:

- source path exists: `repos/fawxzzy-mazer`
- destination path is clear: `repos/mazer` does not exist
- no exact root-side path collision exists
- the read-only scout identified a bounded must-update root surface set if the rename lands

## Root-Side Execution Scope

Execution-cluster rewrite scope is approved as:

- `stack.yaml`
- `stack.lock.yaml`
- `README-STACK.md`
- `docs/registry/STACK-REPO-INVENTORY.json`
- `docs/audits/STACK-REPO-INVENTORY.md`
- `tests/test_stack_repo_inventory.py`
- `docs/architecture/STACK-STANDARDS.md`
- `docs/architecture/atlas-current-tree.md`
- `docs/atlas-book/11-system-map-graph.md`
- `docs/ops/ATLAS-NEXT-BUILD-QUEUE.md`
- `docs/ops/PLAYBOOK-ADOPTION-MATRIX.md`
- `docs/memory/initiatives/initiative-mazer-d2-learning-scorer.json`
- `docs/ops/MAZER-DEPLOY-IDENTITY-HARDENING-2026-05-24.md`
- `docs/ops/MAZER-DEPLOY-IDENTITY-HARDENING-INVENTORY-2026-05-24.md`
- `ops/validation/stack-validation.baseline.json`
- candidate-specific execution / proof / closeout receipts
- `docs/atlas-book/05-receipt-index.md`
- `docs/atlas-book/12-restart-and-handoff-guide.md` only if the next-ladder wording changes during closeout
- `docs/atlas-book/02-lanes-and-markers.md` only if ratchet is later justified

Replacement-map rules approved:

- replace exact active local-path truth `repos/fawxzzy-mazer` -> `repos/mazer`
- replace descendant local-path truth `repos/fawxzzy-mazer/...` -> `repos/mazer/...`
- replace fetch-contract truth `repo_path:repos/fawxzzy-mazer` -> `repo_path:repos/mazer`
- do not blanket-replace bare `fawxzzy-mazer` when it is still remote/project identity or historical narrative

## Approval Decision

Decision:

- `approved for naming execution cluster`

Why:

- `mazer` remains the one honest safe-next candidate
- owner-side blocker set remains `none`
- destination path is clear
- the root-side must-update surface set is bounded and known
- no exact root-side blocker remains

## Exact Next Move

Open one bounded naming execution cluster only for:

- `repos/fawxzzy-mazer -> repos/mazer`

That cluster may now perform:

1. local directory rename
2. exact root-side surface reconciliation
3. root validation
4. proof / reconciliation receipt
5. later ratchet closeout as a separate package

## Rule

Approval gate and execution are separate packages.

## Failure Mode

Treating pass 6 candidate selection as automatic approval would skip the exact root-side surface map and the one real owner-side post-rename path fix that needed to be preserved first.
