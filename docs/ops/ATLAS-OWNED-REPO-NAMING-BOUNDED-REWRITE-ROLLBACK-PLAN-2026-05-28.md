# Atlas-Owned Repo Naming Bounded Rewrite And Rollback Plan - 2026-05-28

- Date: `2026-05-28`
- Lane: `Atlas-owned Repo Naming Canonicalization`
- Mode: `docs-only execution-readiness planning`
- Marker posture: `Atlas-owned Repo Naming Canonicalization: 60%`
- Source surfaces:
  - `docs/ops/ATLAS-OWNED-REPO-NAMING-CANONICALIZATION-2026-05-27.md`
  - `docs/ops/ATLAS-OWNED-REPO-NAMING-EXECUTION-GATE-PASS-1-2026-05-27.md`
  - `docs/ops/ATLAS-OWNED-REPO-NAMING-INVENTORY-DEPENDENCY-MAP-2026-05-27.md`
  - `docs/ops/ATLAS-OWNED-REPO-NAMING-SAFE-FIRST-CANDIDATE-DECISION-2026-05-27.md`
  - `docs/atlas-book/02-lanes-and-markers.md`
  - `docs/atlas-book/05-receipt-index.md`
  - `docs/atlas-book/11-system-map-graph.md`
  - `docs/atlas-book/12-restart-and-handoff-guide.md`
  - `stack.yaml`
  - `stack.lock.yaml`
  - `docs/registry/STACK-REPO-INVENTORY.json`
  - `docs/audits/STACK-REPO-INVENTORY.md`
- Control-plane checkpoint: `main@c0bb965`

## Objective

Freeze the exact bounded rewrite order and rollback order for future internal ATLAS-owned repo renames without performing any rename yet.

This pass does not:

- rename any local repo directory
- rename any remote
- assume any GitHub-side rename
- reopen the `fawxzzy-fitness` exception
- mutate owner-repo content
- change runtime, schema, env, or deploy surfaces
- touch `archive/`

## Root State

- branch: `main`
- HEAD: `c0bb965`
- status: clean except intentional untracked `archive/`

## Validation Posture

Executed:

- `python .\ops\validation\validate_stack.py`

Result:

- `critical=0 error=0 warning=310`

## Candidate Set Recomputed

### Later-candidate class

- `repos/fawxzzy-foundation -> repos/foundation`
- `repos/fawxzzy-mazer -> repos/mazer`
- `repos/fawxzzy-stream -> repos/stream`
- `repos/fawxzzy-trove -> repos/trove`

### Blocked class

- `repos/fawxzzy-lifeline -> repos/lifeline`
- `repos/fawxzzy-playbook -> repos/playbook`

### Preserved exception

- `repos/fawxzzy-fitness`

## Bounded Candidate Order Frozen

The future local-only rename ladder is now frozen in this order:

1. `stream`
2. `foundation`
3. `trove`
4. `mazer`

Why this order:

- `stream` is the smallest current-truth rewrite footprint:
  - clean
  - `main`
  - no configured remote
  - no current `11-system-map-graph.md` path mentions
- `foundation` is also clean on `main`, but it touches active system-map and Vercel current-truth language
- `trove` is clean, but currently on a non-`main` branch
- `mazer` is clean, but currently on a non-`main` branch and carries a related-initiative link in the repo inventory

## Exact Shared Rewrite Order

Any future candidate execution packet must use this exact order after candidate-local preflight passes:

1. verify candidate-local preflight
2. rename the local directory under `repos/`
3. update `stack.yaml`
4. update `stack.lock.yaml`
5. update `docs/registry/STACK-REPO-INVENTORY.json`
6. update `docs/audits/STACK-REPO-INVENTORY.md`
7. update current-truth book surfaces that still name the old path
8. add the candidate-specific execution receipt and update `docs/atlas-book/05-receipt-index.md`
9. run `python .\ops\validation\validate_stack.py`

Rule:

- remote URLs do not change in this sequence
- GitHub naming does not change in this sequence
- historical receipts are not mass-rewritten; only current-truth surfaces and the new execution receipt are touched

## Exact Shared Rollback Order

Any future rollback packet must use the exact reverse order:

1. revert current-truth book surfaces and execution receipt/index updates
2. revert `docs/audits/STACK-REPO-INVENTORY.md`
3. revert `docs/registry/STACK-REPO-INVENTORY.json`
4. revert `stack.lock.yaml`
5. revert `stack.yaml`
6. rename the local directory back to the original prefixed path
7. run `python .\ops\validation\validate_stack.py`

Rule:

- rollback restores local directory naming and ATLAS control-plane truth only
- rollback does not imply any remote URL or GitHub rename reversal because those are never changed in the local-only lane

## Candidate-Local Preflight Contract

Every future candidate execution packet must prove all of the following before step 2 begins:

1. source path exists
2. target path does not exist
3. current repo branch posture is admitted for the packet
4. dirty state is admitted for the packet
5. no active worktree or adjacent retained surface still depends on the old local path
6. no current-truth control-plane surface outside the planned rewrite set still requires the old path
7. remote rename remains explicitly out of scope

If any one of those fails, execution stays blocked.

## Exact Rewrite Scope By Candidate

### `stream`

Current path:

- `repos/fawxzzy-stream`

Target path:

- `repos/stream`

Exact rewrite surfaces:

- `stack.yaml`
- `stack.lock.yaml`
- `docs/registry/STACK-REPO-INVENTORY.json`
- `docs/audits/STACK-REPO-INVENTORY.md`
- candidate execution receipt
- `docs/atlas-book/05-receipt-index.md`

Expected no-op checks:

- `docs/atlas-book/11-system-map-graph.md`
- `docs/atlas-book/12-restart-and-handoff-guide.md`

Reason:

- no current path references are active there today

Execution-packet-ready after this planning pass:

- `yes`

Why:

- clean
- `main`
- no configured remote
- smallest current-truth rewrite footprint in the candidate set

### `foundation`

Current path:

- `repos/fawxzzy-foundation`

Target path:

- `repos/foundation`

Exact rewrite surfaces:

- `stack.yaml`
- `stack.lock.yaml`
- `docs/registry/STACK-REPO-INVENTORY.json`
- `docs/audits/STACK-REPO-INVENTORY.md`
- `docs/atlas-book/11-system-map-graph.md`
- candidate execution receipt
- `docs/atlas-book/05-receipt-index.md`

Expected no-op check:

- `docs/atlas-book/12-restart-and-handoff-guide.md`

Execution-packet-ready after this planning pass:

- `not yet`

Why:

- the candidate is clean and on `main`
- but it is intentionally second in order because it touches active system-map and Vercel current-truth language
- the lane should prove the smallest footprint packet first rather than open two different truth-map scopes at once

### `trove`

Current path:

- `repos/fawxzzy-trove`

Target path:

- `repos/trove`

Exact rewrite surfaces:

- `stack.yaml`
- `stack.lock.yaml`
- `docs/registry/STACK-REPO-INVENTORY.json`
- `docs/audits/STACK-REPO-INVENTORY.md`
- `docs/atlas-book/11-system-map-graph.md`
- candidate execution receipt
- `docs/atlas-book/05-receipt-index.md`

Expected no-op check:

- `docs/atlas-book/12-restart-and-handoff-guide.md`

Execution-packet-ready after this planning pass:

- `no`

Blocked reason:

- current branch is `codex/trove-brand-asset-sync`, not `main`

### `mazer`

Current path:

- `repos/fawxzzy-mazer`

Target path:

- `repos/mazer`

Exact rewrite surfaces:

- `stack.yaml`
- `stack.lock.yaml`
- `docs/registry/STACK-REPO-INVENTORY.json`
- `docs/audits/STACK-REPO-INVENTORY.md`
- `docs/atlas-book/11-system-map-graph.md`
- candidate execution receipt
- `docs/atlas-book/05-receipt-index.md`

Expected no-op check:

- `docs/atlas-book/12-restart-and-handoff-guide.md`

Execution-packet-ready after this planning pass:

- `no`

Blocked reasons:

- current branch is `codex/mazer-remove-pwa-install-surface`, not `main`
- repo inventory currently carries a related initiative reference that should not be mixed into a first execution packet

### `lifeline`

Current path:

- `repos/fawxzzy-lifeline`

Target path:

- `repos/lifeline`

Blocked status:

- `blocked`

Blocked reasons:

- dirty
- non-`main`
- active local-operator lane posture

### `playbook`

Current path:

- `repos/fawxzzy-playbook`

Target path:

- `repos/playbook`

Blocked status:

- `blocked`

Blocked reasons:

- dirty
- non-`main`
- active governance-runtime lane posture

### `fitness`

Status:

- `preserved exception`

Reason:

- explicit exception remains durable
- this lane does not reopen product-facing or remote identity surfaces

## Historical Receipt Rewrite Rule

Do not mass-rewrite old naming receipts just because a local rename later lands.

Historical receipts should preserve the path truth that existed when they were written unless they are current-truth surfaces by design.

Current-truth rewrite scope in this lane is limited to:

- registry files
- active inventory publication
- system map when it currently names the repo path
- restart surface only if it currently names the repo path
- the new execution receipt and index spine

## Does Any Candidate Become Execution-Packet-Ready?

Yes.

After this planning pass:

- `stream` becomes the first exact execution-packet-ready candidate

Meaning:

- the rewrite order is exact
- the rollback order is exact
- the current rewrite footprint is smallest
- execution is still not approved until a separate bounded execution packet opens

No other candidate becomes execution-packet-ready in this pass.

## What Remains Blocked

Still blocked after this planning pass:

- any remote rename assumption
- any GitHub-side rename assumption
- `fawxzzy-fitness` rename
- `lifeline` rename
- `playbook` rename
- `trove` rename while non-`main`
- `mazer` rename while non-`main`
- `foundation` as a first packet before the smaller `stream` packet is proven

## Exact Next Package

`Atlas-owned Repo Naming stream execution-packet preflight pass 1`

Why:

- the smallest exact packet is now known
- the rewrite and rollback order is now frozen
- the next honest move is one narrow preflight packet for `stream`, not a broad multi-repo rename lane

## Rule

Rename planning must freeze exact rewrite and rollback order before any execution lane opens.

## Pattern

policy admission -> execution gate -> dependency map -> safe-first decision -> bounded rewrite/rollback plan -> one exact execution-packet-ready candidate -> one bounded execution packet

## Failure Mode

A planning pass stays vague, so the later rename lane still has to improvise.
