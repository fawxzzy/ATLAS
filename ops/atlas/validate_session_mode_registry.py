from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from ops._atlas import atlas_root
from ops.atlas.load_session_mode_registry import (
    load_session_mode_registry_bundle,
    resolve_mode_from_invocation,
    resolve_repo_input,
    select_mode_entry,
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Validate the root-owned ATLAS session mode registry and optionally require selected mode, invocation, and repo resolution.",
    )
    parser.add_argument("--mode-id")
    parser.add_argument("--invocation")
    parser.add_argument("--repo")
    args = parser.parse_args(argv)

    bundle = load_session_mode_registry_bundle(root=atlas_root())
    if args.mode_id:
        select_mode_entry(bundle, args.mode_id)
    if args.invocation:
        bundle["validated_invocation"] = resolve_mode_from_invocation(bundle, args.invocation)["mode_id"]
    if args.repo:
        bundle["validated_repo"] = {
            "logical_id": resolve_repo_input(args.repo, root=atlas_root()).get("logical_id"),
            "local_path": resolve_repo_input(args.repo, root=atlas_root()).get("local_path"),
        }

    print(
        json.dumps(
            {
                "ok": True,
                "registry_digest": bundle["registry_digest"],
                "mode_count": bundle["mode_count"],
                "registry_ref": bundle["registry_ref"],
                "repo_inventory_ref": bundle["repo_inventory_ref"],
                "validated_mode_id": args.mode_id,
                "validated_invocation": bundle.get("validated_invocation"),
                "validated_repo": bundle.get("validated_repo"),
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
