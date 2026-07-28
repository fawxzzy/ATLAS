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
```

The SQLite database is runtime state and is intentionally excluded from source
snapshots. A future adapter wave will add a supervised worker process and only
then may report a task as `RUNNING`.

## Current cutover status

Legacy scheduling remains authoritative. This command is suitable only for
isolated tests and shadow/replay work until the adapter, watchdog, and parity
proof waves are accepted.
