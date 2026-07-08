# Inventory & Truth Map owner-truth adoption proof contract freeze

- Date: `2026-07-08`
- Lane: `Inventory & Truth Map`
- Mode: `ATLAS-root docs-only contract freeze`
- Control-plane checkpoint: `16f75543`
- Marker posture: `Inventory & Truth Map: 99%`

## Decision

Freeze the contract for a future root-owned owner-truth adoption proof helper.

Future implementation target:

- `ops/atlas/owner_truth_adoption_proof.py`
- `tests/test_atlas_owner_truth_adoption_proof.py`

This packet does not implement the helper and does not move the marker.

## Contract Purpose

The helper must prove whether ATLAS root is correctly adopting owner-lane truth as advisory inventory state while preserving owner-lane separation.

It must answer:

- which owner repos are advisory dirty
- whether any owner repo dirt blocks ATLAS root
- whether owner dirt is represented in inventory and Book mirrors
- whether root validation remains clean without scanning or mutating owner internals
- whether the current posture respects the root scope lock
- whether a future marker movement is merely advisory, implementation-backed, or blocked

## Admitted Inputs

- `docs/registry/STACK-REPO-INVENTORY.json`
- `docs/audits/STACK-REPO-INVENTORY.md`
- `stack.yaml`
- `stack.lock.yaml`
- `AGENTS.md`
- `docs/atlas-book/01-current-state.md`
- `docs/atlas-book/02-lanes-and-markers.md`
- `docs/atlas-book/05-receipt-index.md`
- `docs/atlas-book/12-restart-and-handoff-guide.md`
- `docs/memory/initiatives/continuity-manifest-inventory-and-truth-map.json`
- durable Inventory, scope-lock, and owner-lane separation receipts under `docs/ops/`
- explicit read-only owner repo status summaries supplied by the operator packet

## Forbidden Inputs

- owner repo source diffs as root truth
- owner repo file contents unless separately admitted by a packet
- owner repo mutation
- deploy/platform APIs
- secrets, secret values, `.env*`, `.vercel`, `.playwright-mcp/`, or `archive/`
- unbounded owner backlog scans
- runtime screenshots or generated artifacts as root authority unless cited by a durable receipt

## Output Contract

The future helper should emit JSON with:

- `schema_version`
- `status`
- `safe_to_use`
- `root_validation_summary`
- `inventory_dirty_repo_count`
- `inventory_visible_dirty_repo_count`
- `inventory_advisory_dirty_repo_count`
- `advisory_owner_repos`
- `root_blocking_owner_repos`
- `owner_status_inputs`
- `book_mirror_status`
- `scope_lock_status`
- `adoption_result`
- `marker_implication`
- `blockers`
- `authority_denials`

Allowed `adoption_result` values:

- `adopted_advisory_truth`
- `blocked_root_truth`
- `insufficient_evidence`
- `contract_violation`

Allowed `marker_implication` values:

- `no_marker_movement`
- `candidate_for_future_ratchet`
- `blocked`

## Proof Rules

Proof may count only if:

- root validation is `critical=0 error=0`
- inventory root-blocking dirty count is zero or explicitly explained
- advisory owner dirt is represented without becoming root fallback work
- Book mirrors and manifest surfaces agree with inventory posture
- the helper rejects protected paths and owner mutation authority
- focused tests cover clean, advisory-dirty, root-blocking, stale-mirror, and forbidden-input cases

Proof must not count if:

- it mutates owner repos
- it reads secrets
- it relies on owner implementation diffs as root truth
- it treats Fitness or Mazer as fallback work
- it claims product, game, deploy, or release readiness
- it moves a marker without a reconciliation receipt

## Current Read-Only Owner Awareness

The operator-selected packet read owner status only:

- Fitness: advisory dirty, non-root-blocking
- Mazer: advisory dirty / ahead of remote, non-root-blocking
- DiscordOS: clean in read-only status, non-mutated

This awareness is not owner-repo work and does not authorize owner mutation.

## Marker Decision

No marker movement.

`Inventory & Truth Map` remains `99%` until the future implementation and reconciliation prove the contract with live helper output and tests.

## Next

`Inventory & Truth Map owner-truth adoption proof first-implementation admission`

