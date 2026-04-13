from __future__ import annotations

import argparse
import json

from _pipeline import add_common_archive_args, evaluate_archive, resolve_archive_dir


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Evaluate an imported knowledge archive without executing its contents."
    )
    add_common_archive_args(parser)
    args = parser.parse_args()

    archive_path = resolve_archive_dir(args.source_name, args.slug, args.archive_dir)
    result = evaluate_archive(archive_path=archive_path, dry_run=args.dry_run)
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
