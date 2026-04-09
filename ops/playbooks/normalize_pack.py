from __future__ import annotations

import argparse
import json

from _pipeline import add_common_pack_args, normalize_pack, resolve_pack_dir


def main() -> int:
    parser = argparse.ArgumentParser(description="Normalize accepted playbook metadata into the runtime catalog.")
    add_common_pack_args(parser)
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()

    pack_dir = resolve_pack_dir(args.source_name, args.slug, args.pack_dir)
    result = normalize_pack(pack_dir=pack_dir, dry_run=args.dry_run, force=args.force)
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
