# ATLAS Workflow V4 runtime core

This is the first executable slice of the Workflow V4 cutover. It moves queue
truth out of conversational threads while preserving the existing owner,
review, provider, and production authority boundaries.

## Guarantees

- SQLite uses WAL mode and durable transactions.
- Tasks use explicit truthful states; `RUNNING` requires a lease and worker/run identity.
- Wave 1 leases use opaque exact resource scopes such as a repository, worktree,
  provider, deployment, or protected path set. Path-overlap conflict predicates
  are a later scoped-lock wave.
- Terminal receipt plus successor enqueue is one transaction.
- Duplicate task and exact receipt events are idempotent; the canonical enqueue
  digest includes priority, dependencies, and successors, so reusing an event
  ID with different behavior fails closed.
- A successor remains blocked until every declared predecessor succeeds.
- Restart reconciliation converts expired/orphaned work to `PAUSED_RUNTIME`.
- Reconciliation exposes `READY_NOT_DISPATCHED` and
  `PAUSED_RUNTIME_REQUIRES_RESUME` dispositions; it never silently restarts a
  worker.

## Not included in this slice

This core does not start Codex workers, call providers, merge code, deploy, or
replace the legacy scheduler. The worker adapter supplies a fail-closed receipt
contract only; watchdog supervision, shadow replay, controlled worker launch,
and cutover remain subsequent bounded waves.

## Verification

Run `python -m unittest tests.test_atlas_runtime -v` from the ATLAS root. The
tests use temporary databases and do not touch canonical runtime state.
