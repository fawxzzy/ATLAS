from __future__ import annotations

import argparse
import json

from _pipeline import add_common_pack_args, evaluate_pack, resolve_pack_dir


def main() -> int:
    parser = argparse.ArgumentParser(description="Evaluate an imported playbook pack without executing vendor content.")
    add_common_pack_args(parser)
    args = parser.parse_args()

    pack_dir = resolve_pack_dir(args.source_name, args.slug, args.pack_dir)
    result = evaluate_pack(pack_dir=pack_dir, dry_run=args.dry_run)
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
