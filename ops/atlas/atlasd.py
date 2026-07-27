"""ATLAS Workflow V4 local control-plane entrypoint.

The daemon deliberately owns only durable reconciliation in this wave.  Worker
launch is injected through a later adapter, so invoking this command cannot
start a chat, change a repository, or call a provider.
"""

from __future__ import annotations

import argparse
import json
import sqlite3
import sys
import time
from pathlib import Path

# Direct script execution (the documented operator command) does not place the
# repository root on sys.path. Keep module imports working in both modes.
if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from ops.atlas.atlas_runtime import AtlasRuntime


def _health(runtime: AtlasRuntime) -> dict[str, object]:
    rows = runtime.db.execute("SELECT state, COUNT(*) AS n FROM tasks GROUP BY state").fetchall()
    states = {row["state"]: row["n"] for row in rows}
    lease_count = runtime.db.execute("SELECT COUNT(*) AS n FROM leases").fetchone()["n"]
    return {
        "schema": "atlasd.health.v1",
        "generated_at": time.time(),
        "tasks_by_state": states,
        "running_worker_count": lease_count,
        "stranded_ready_count": states.get("QUEUED", 0),
        "legacy_scheduler_authoritative": True,
        "worker_launch_enabled": False,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="ATLAS Workflow V4 runtime control plane")
    parser.add_argument("--database", required=True, help="local SQLite database path")
    parser.add_argument("command", choices=("init", "health", "reconcile"))
    parser.add_argument("--heartbeat-timeout", type=float, default=120)
    args = parser.parse_args(argv)
    runtime = AtlasRuntime(Path(args.database))
    try:
        if args.command == "reconcile":
            paused = runtime.reconcile(heartbeat_timeout=args.heartbeat_timeout)
            output = _health(runtime) | {"paused_runtime_tasks": paused}
        else:
            output = _health(runtime)
        print(json.dumps(output, sort_keys=True))
        return 0
    finally:
        runtime.close()


if __name__ == "__main__":
    raise SystemExit(main())
