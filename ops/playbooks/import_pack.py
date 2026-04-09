from __future__ import annotations

import argparse
import json
from pathlib import Path

from _pipeline import import_pack


def main() -> int:
    parser = argparse.ArgumentParser(description="Import a third-party playbook pack into the ATLAS raw intake lane.")
    parser.add_argument("--input-path", required=True, type=Path)
    parser.add_argument("--source-name", required=True)
    parser.add_argument("--slug")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()

    result = import_pack(
        input_path=args.input_path.resolve(),
        source_name=args.source_name,
        slug=args.slug,
        dry_run=args.dry_run,
        force=args.force,
    )
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
