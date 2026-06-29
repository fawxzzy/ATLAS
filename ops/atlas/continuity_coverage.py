from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from ops._atlas import atlas_root
from ops.atlas.continuity import build_continuity_status_slices


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Report the structured continuity coverage rollup for the seeded ATLAS initiative set."
    )
    parser.add_argument("--root", type=Path, default=atlas_root())
    args = parser.parse_args(argv)

    _, slices = build_continuity_status_slices(root=args.root.resolve())
    payload = slices["continuity_coverage"]
    print(json.dumps(payload, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
