from __future__ import annotations

import argparse
import json

from _pipeline import (
    INDEXING_PROFILES,
    PROMOTION_STATUSES,
    RETENTION_CLASSES,
    add_common_archive_args,
    promote_archive,
    resolve_archive_dir,
)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Create or update a canonical promotion doc for a reviewed knowledge archive."
    )
    add_common_archive_args(parser)
    parser.add_argument("--indexing-profile", choices=sorted(INDEXING_PROFILES))
    parser.add_argument("--promotion-status", choices=sorted(PROMOTION_STATUSES - {'not_promoted'}), default="draft")
    parser.add_argument("--retention-class", choices=sorted(RETENTION_CLASSES))
    parser.add_argument("--refresh-derived", action="store_true")
    args = parser.parse_args()

    archive_path = resolve_archive_dir(args.source_name, args.slug, args.archive_dir)
    result = promote_archive(
        archive_path=archive_path,
        indexing_profile=args.indexing_profile,
        promotion_status=args.promotion_status,
        retention_class=args.retention_class,
        refresh_derived=args.refresh_derived,
        dry_run=args.dry_run,
    )
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
