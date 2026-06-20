from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from ops._atlas import atlas_root
from ops.atlas.continuity import build_maintained_manifest_restart_index


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Report restart-ready continuity truth for all maintained initiative manifests."
    )
    parser.add_argument("--root", type=Path, default=atlas_root())
    args = parser.parse_args(argv)

    payload = build_maintained_manifest_restart_index(root=args.root.resolve())
    print(json.dumps(payload, indent=2))
    return 0 if payload.get("error_count", 0) == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
