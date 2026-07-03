# AI Work Session Stability Auto-Sync Loop Projection Freshness Checker First-Implementation Admission

- CODEX-MSG-ID: `CODEX-2026-07-02-AI-WORK-SESSION-STABILITY-PROJECTION-FRESHNESS-FIRST-IMPLEMENTATION-ADMISSION`
- Date: `2026-07-02`
- Mode: `docs-only first-implementation admission`
- Scope: `admit a future read-only projection freshness checker without implementing it`
- Branch basis: `main@28f2cab7`
- Worker implementation: `not included`
- Owner-repo mutation: `none`
- Platform mutation: `none`
- Protected-surface mutation: `none`
- Marker movement: `none`

## Admission Decision

Admit a future first implementation for:

- `ops/atlas/projection_freshness.py`
- `tests/test_atlas_projection_freshness.py`

The shorter `projection_freshness.py` name is intentional: the checker is rooted in the AI Work Session Stability lane, but its read-only job is to compare stack projections across root truth, inventory, Book mirrors, receipts, manifests, PR bodies, proof state, and owner-lane semantics.

This receipt does not create those files. It admits the next prompt-pack and worker handoff contract only.

## Why This Is The Next 55 Percent Threshold

The lane has already landed:

1. a read-only preflight helper that checks whether a session can begin or continue safely
2. a read-only closeout helper that checks whether a session can stop safely
3. direct tests for both helpers
4. a reconciliation receipt that moved `AI Work Session Stability & Auto-Sync Loop` to `40%`

The next meaningful threshold is not more prose. It is a read-only projection freshness checker that detects whether the stack's projected truth is stale relative to current root and owner-lane facts.

Movement to `55%` requires the checker implementation, direct tests, clean validation, and reconciliation proof. This admission alone keeps the marker at `40%`.

## Difference From Preflight And Closeout

Preflight answers: `Can this session safely start or continue?`

Closeout answers: `Can this session safely stop, and what exact next action remains?`

Projection freshness answers: `Are the projected truth surfaces stale or contradictory, and what exact refresh is required before claims continue?`

The checker sits between live facts and narrative handoff. It prevents old branch heads, stale inventory, stale marker mirrors, dry-run/protected-proof confusion, and owner-lane advisory dirt from repeatedly blocking unrelated ATLAS work.

## Stale States The Checker Must Detect

The future checker must detect or classify:

- `stack.lock.yaml` disagreement with live root or managed owner repo heads where applicable
- `docs/registry/STACK-REPO-INVENTORY.json` disagreement with stack lock or owner-lane semantics
- `docs/audits/STACK-REPO-INVENTORY.md` disagreement with inventory JSON
- ATLAS Book current-state drift relative to current receipts and manifests
- marker board disagreement with continuity manifests
- stale PR body branch-head references when a PR is in scope
- owner-lane dirty repos that should be advisory rather than root-blocking
- dry-run proof being represented as protected proof
- protected BrowserStack proof being represented without evidence
- restart surfaces stale relative to latest receipts
- missing or unclear exact surfaces that need refresh

## Future Output Contract

The future checker must emit deterministic JSON with these top-level fields:

```json
{
  "schema_version": "atlas.projection_freshness.v1",
  "status": "ok | advisory_drift | blocker | internal_error",
  "root": "ATLAS root",
  "branch": "current branch",
  "head": "current commit",
  "parity": {},
  "stack_lock": {},
  "inventory": {},
  "atlas_book": {},
  "receipts": {},
  "manifests": {},
  "markers": {},
  "pull_requests": {},
  "owner_lanes": {},
  "proof_state": {},
  "protected_surfaces": {},
  "blockers": [],
  "warnings": [],
  "required_refreshes": [],
  "safe_to_continue": false
}
```

## Status Classes

- `ok`: projections agree with current facts and no blocking refresh is required.
- `advisory_drift`: non-blocking stale or advisory state exists and is explicitly reported.
- `blocker`: a projected claim is unsafe because required root, owner-lane, proof, marker, PR, or validation truth is missing or contradictory.
- `internal_error`: required inspection failed before the checker could classify state safely.

## Required Behavior

The future checker must:

- default to read-only
- avoid file mutation by default
- avoid owner-repo mutation
- avoid platform mutation
- avoid deploy or publication
- avoid marker movement
- avoid receipt generation
- avoid PR editing
- avoid staging, committing, or pushing
- touch no protected surfaces
- report exact required refreshes instead of performing them

## Proof Matrix For Future Worker

The future worker packet must prove:

- clean projections return `ok`
- stale inventory versus lock returns at least `advisory_drift`
- stale Book marker mirror returns at least `advisory_drift`
- dry-run proof represented as protected proof returns `blocker`
- root-blocking dirty inventory returns `blocker`
- advisory owner-lane dirt remains advisory
- unsafe output paths are rejected
- output order is deterministic

## Marker Decision

No marker moves from this admission packet.

`AI Work Session Stability & Auto-Sync Loop` remains `40%`.

Movement to `55%` requires the projection freshness checker implementation, direct tests, clean validation, preserved read-only boundaries, and a reconciliation receipt.

## Next Packet

`AI Work Session Stability & Auto-Sync Loop projection freshness checker prompt-pack and worker handoff contract`

That next packet should freeze the CLI flags, JSON output fields, exit-code policy, read-only checks, forbidden behavior, proof matrix, stop conditions, and worker-routing criteria.
