from __future__ import annotations

import argparse
import json
from pathlib import Path

from _pipeline import PRIVACY_FLAGS, import_archive


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Import a knowledge archive into the ATLAS raw intake lane."
    )
    parser.add_argument("--input-path", required=True, type=Path)
    parser.add_argument("--source-name", required=True)
    parser.add_argument("--slug")
    parser.add_argument("--privacy-flag", choices=sorted(PRIVACY_FLAGS), default="private")
    parser.add_argument("--provenance-note")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()

    result = import_archive(
        input_path=args.input_path,
        source_name=args.source_name,
        slug=args.slug,
        privacy_flag=args.privacy_flag,
        provenance_note=args.provenance_note,
        dry_run=args.dry_run,
        force=args.force,
    )
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
