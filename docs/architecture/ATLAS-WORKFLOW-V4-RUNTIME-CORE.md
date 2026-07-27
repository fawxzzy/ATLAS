# ATLAS Workflow V4 runtime core

This is the first executable slice of the Workflow V4 cutover. It moves queue
truth out of conversational threads while preserving the existing owner,
review, provider, and production authority boundaries.

## Guarantees

- SQLite uses WAL mode and durable transactions.
- Tasks use explicit truthful states; `RUNNING` requires a lease and worker/run identity.
- Leases are scoped to a repository, worktree, provider, deployment, or protected path set.
- Terminal receipt plus successor enqueue is one transaction.
- Duplicate task and receipt events are idempotent.
- Restart reconciliation converts expired/orphaned work to `PAUSED_RUNTIME`.

## Not included in this slice

This core does not start Codex workers, call providers, merge code, deploy, or
replace the legacy scheduler. Worker adapters, watchdog supervision, shadow
replay, and cutover remain subsequent bounded waves.

## Verification

Run `python -m unittest tests.test_atlas_runtime -v` from the ATLAS root. The
tests use temporary databases and do not touch canonical runtime state.
