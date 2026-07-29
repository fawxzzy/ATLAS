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
- The watchdog is event-driven with a durable 30-minute fallback. It records
  one idempotent `WAKE_NEEDED` or `HOLD` receipt per task/cooldown window, but
  never starts a chat or worker. A short durable run reservation records
  `IN_PROGRESS`, `SUCCEEDED`, or `ABANDONED`; only `SUCCEEDED` begins the
  fallback cooldown. Reservation expiry is a hard deadline. The complete
  deterministic receipt set, exact unexpired reservation transition, and
  cooldown advance commit in one SQLite write transaction; stale, expired, or
  replaced owners leave none of those effects. Exact committed replays are
  read-only no-ops, while partial or different replays fail closed. Exceptions
  abandon immediately, and a crashed reservation expires for recovery without
  holding a transaction across reconciliation.
- Valid leases, manual/external/provider/production gates, unresolved
  dependencies, `PAUSED_USAGE`, paused runtime work, and unknown state remain
  explicit holds. `PAUSED_USAGE` is observe-only and is never automatically
  resumed or dispatched.
- Watchdog heartbeat staleness is configurable and is applied to the
  reconciliation pass. Invalid non-positive timeout and fallback values fail
  before runtime work begins.
- Watchdog candidate reads remain separate from finalization. A concurrent task
  transition can make a receipt observation stale, but every receipt records
  `execution: NOT_STARTED` and cannot launch work, mutate task state, or release
  a lease. Reconciliation uses its own bounded transaction: its conditional
  `RUNNING` to `PAUSED_RUNTIME` transition plus lease deletion is idempotent,
  so overlapping reconcilers cannot repeat or undo durable work.

## Not included in this slice

This core does not start Codex workers, call providers, merge code, deploy, or
replace the legacy scheduler. The worker adapter supplies a fail-closed receipt
contract only. The watchdog is observe-only; controlled worker launch and
cutover remain subsequent bounded waves.

## Verification

Run `python -m unittest tests.test_atlas_runtime -v` from the ATLAS root. The
tests use temporary databases and do not touch canonical runtime state.
