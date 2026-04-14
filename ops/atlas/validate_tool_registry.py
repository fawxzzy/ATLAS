from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from ops._atlas import atlas_root
from ops.atlas.load_tool_registry import load_tool_registry_bundle, select_extension_entry, select_tool_entry


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Validate the root-owned ATLAS tool and extension registries and optionally require selected ids.",
    )
    parser.add_argument("--tool-id")
    parser.add_argument("--extension-id")
    args = parser.parse_args(argv)

    bundle = load_tool_registry_bundle(root=atlas_root())
    if args.tool_id:
        select_tool_entry(bundle, args.tool_id)
    if args.extension_id:
        select_extension_entry(bundle, args.extension_id)

    print(
        json.dumps(
            {
                "ok": True,
                "registry_digest": bundle["registry_digest"],
                "tool_count": bundle["tool_count"],
                "extension_count": bundle["extension_count"],
                "tool_registry_ref": bundle["tool_registry_ref"],
                "extension_registry_ref": bundle["extension_registry_ref"],
                "validated_tool_id": args.tool_id,
                "validated_extension_id": args.extension_id,
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
