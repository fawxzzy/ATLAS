# ATLAS autonomous scheduler conflict-group lease and standing continuation v2

## Decision

The autonomous scheduler selects a dependency-satisfied execution wave, not a
single global packet. Safety is enforced by exclusive conflict-group leases:

- one canonical-root writer;
- one mutating writer per owner repository or declared external-resource group;
- concurrent writers across distinct scopes only when declared resource claims
  are disjoint;
- bounded read-only work only when it does not collide with an exclusive claim.

This supersedes the v1 one-packet scheduling rule. It does not supersede exact
authority, scope, review, merge, provider, deployment, production, or data
gates.

## Standing packet contract

A standing packet is schedulable only when it carries:

- `state` equal to `READY`, `ADMITTED`, or `QUEUED`;
- a stable `packet_id` and bounded packet description;
- `logical_role_id`, `repository`, `writer_scope`, and `execution_class`;
- a canonical `onv1_` SHA-256 event ID and `sha256:` payload digest;
- explicit dependencies and resource claims when applicable.

Owner-like prose without this metadata is not inferred into authority. The
scheduler fails closed instead of treating a textual owner reference as a
license to mutate that repository.

## Lease behavior

An active lease blocks only its exact `writer_scope`. Multiple active leases
for one scope remain a collision and block that scope. A terminal correlated
receipt releases only its exact lease; blocked, latency-bound, or unknown work
does not release a lease by implication.

`atlas.worker-lease.v2` now requires `writer_scope`; a lease without its
conflict-group identity is invalid and cannot reserve global capacity by
accident.

The default scope for a `repo_worktree` job is derived from its repository. A
`canonical_workspace` job always claims the ATLAS root. Explicit narrower
conflict groups remain responsible for complete, non-overlapping file,
worktree, port, browser, and external-writer claims.

## Continuation behavior

`ATLAS MAIN` consumes all newly READY packets, selects the largest deterministic
conflict-free wave within configured writer and read-only limits, and routes
each packet to its existing standing logical role. `IDLE` and `notLoaded` are
resumable binding states, not terminal states.

When a receipt arrives, MAIN persists it, releases the correlated lease, and
immediately selects the next eligible wave. It does not wait for the next
heartbeat. Heartbeats recover interrupted coordination only.

## Stop conditions

The affected lane stops on missing or malformed authority, identity or scope
drift, unmet dependencies, active lease collision, undeclared protected
surface access, or resource overlap. Unrelated conflict groups continue.

No scheduler output grants GitHub workflow dispatch, provider access,
Supabase/SQL/Auth/data mutation, deployment, production, secret access, or
canonical-root mutation beyond the exact admitted packet.

## Verification surface

- `tests/test_cortex_execution_planner.py` proves implicit writer-scope claims,
  same-scope serialization, and distinct-repository parallel waves.
- `tests/test_atlas_autonomous_lane_scheduler.py` proves canonical standing
  authority, dependency gating, active-lease isolation, and deterministic
  multi-scope wave selection.
- `tests/test_atlas_workflow_recovery.py` and the generated workflow view prove
  that the durable manifest retains per-scope collision handling and standing
  continuation rules.
