# ATLASD local control plane (Wave 1A)

`atlasd` is the local, durable health and reconciliation entrypoint for ATLAS
Workflow V4. In this wave it does **not** launch Codex, alter repository state,
or call a provider. Its purpose is to make queue truth observable before worker
supervision is enabled.

## Local-only commands

```powershell
python ops/atlas/atlasd.py --database runtime/atlas/atlasd.sqlite init
python ops/atlas/atlasd.py --database runtime/atlas/atlasd.sqlite health
python ops/atlas/atlasd.py --database runtime/atlas/atlasd.sqlite reconcile
python ops/atlas/atlasd.py --database runtime/atlas/atlasd.sqlite watchdog --event
python ops/atlas/atlasd.py --database runtime/atlas/atlasd.sqlite watchdog --heartbeat-timeout 120
```

The SQLite database is runtime state and is intentionally excluded from source
snapshots. `watchdog` records a durable, idempotent wake-or-hold receipt and
uses a 30-minute fallback when no event is observed. A fallback cooldown begins
only after the run completes successfully; failed runs are immediately
retryable and crashed reservations expire for recovery. `--heartbeat-timeout`
controls the reconciliation pass for both `reconcile` and `watchdog`, and
non-positive timeout or fallback values are rejected.

`PAUSED_USAGE` is observed as an explicit `HOLD`. The watchdog never launches a
worker, resumes paused work, releases a lease, mutates task state from a
receipt, or steers a chat. A receipt can describe a stale observation if task
state changes between its read and write, but it remains side-effect free and
records `execution: NOT_STARTED`. A future adapter wave will add a supervised
worker process and only then may report a task as `RUNNING`.

## Current cutover status

Legacy scheduling remains authoritative. This command is suitable only for
isolated tests and shadow/replay work until the adapter, watchdog, and parity
proof waves are accepted.
