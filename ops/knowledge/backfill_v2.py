from __future__ import annotations

import argparse
import json

from _pipeline import backfill_archive, discover_import_manifests


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Backfill existing knowledge imports to the Knowledge Ingest V2 contract."
    )
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    results = [
        backfill_archive(manifest_file.parent, dry_run=args.dry_run)
        for manifest_file in discover_import_manifests()
    ]
    print(json.dumps({"dry_run": args.dry_run, "archive_count": len(results), "results": results}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
