from __future__ import annotations

import argparse
import json

from _pipeline import build_query_bundle


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Build the deterministic ATLAS knowledge query bundle from promotions, runtime catalogs, and latest receipts."
    )
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    result = build_query_bundle(dry_run=args.dry_run)
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
