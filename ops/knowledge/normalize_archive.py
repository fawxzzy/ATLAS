from __future__ import annotations

import argparse
import json

from import_archive import add_common_archive_args, normalize_archive, resolve_archive_dir


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Normalize accepted knowledge archive metadata into the runtime catalog."
    )
    add_common_archive_args(parser)
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()

    archive_path = resolve_archive_dir(args.source_name, args.slug, args.archive_dir)
    result = normalize_archive(
        archive_path=archive_path,
        dry_run=args.dry_run,
        force=args.force,
    )
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
