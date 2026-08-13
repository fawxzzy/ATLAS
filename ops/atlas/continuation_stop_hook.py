"""Value-free Codex Stop hook for same-session ATLAS continuation.

This hook is source-only until explicitly installed and trusted. It reads only
the durable outbox projection and never starts a thread or turn itself.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from ops.atlas.atlas_runtime import AtlasRuntime


def decide(
    *, database: str | Path, owner_id: str | None = None,
    session_id: str | None = None,
) -> dict[str, str]:
    runtime = AtlasRuntime(database)
    try:
        if owner_id is None and session_id:
            row = runtime.db.execute(
                "SELECT owner_id FROM continuation_owners WHERE thread_id=?",
                (session_id,),
            ).fetchone()
            owner_id = row["owner_id"] if row else None
        if not owner_id:
            return {}
        return runtime.stop_hook_decision(owner_id=owner_id, thread_id=session_id)
    finally:
        runtime.close()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="ATLAS durable continuation Stop hook")
    parser.add_argument("--database", required=True)
    parser.add_argument("--owner-id")
    args = parser.parse_args(argv)
    try:
        event = json.loads(sys.stdin.read() or "{}")
        if not isinstance(event, dict):
            raise ValueError("hook input must be an object")
        if event.get("stop_hook_active") is True:
            output = {}
        else:
            owner_id = args.owner_id or event.get("owner_id") or os.environ.get("ATLAS_OWNER_ID")
            session_id = event.get("session_id")
            if owner_id is not None and (not isinstance(owner_id, str) or not owner_id.strip()):
                raise ValueError("owner identity is invalid")
            if session_id is not None and (not isinstance(session_id, str) or not session_id.strip()):
                raise ValueError("session identity is invalid")
            output = decide(database=args.database, owner_id=owner_id, session_id=session_id)
    except Exception:
        # A Stop hook may continue only an exactly bound, durably consumed
        # trigger. Invalid, unbound, or unavailable evidence must allow stop.
        output = {}
    print(json.dumps(output, sort_keys=True, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
