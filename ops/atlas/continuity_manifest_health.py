from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from ops._atlas import atlas_root
from ops.atlas.continuity import build_initiative_continuity_manifest_health


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Validate ATLAS initiative continuity manifests against live marker and receipt truth."
    )
    parser.add_argument("--root", type=Path, default=atlas_root())
    args = parser.parse_args(argv)

    payload = build_initiative_continuity_manifest_health(root=args.root.resolve())
    print(json.dumps(payload, indent=2))
    return 0 if payload.get("error_count", 0) == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
