from __future__ import annotations

import argparse
import json

from _pipeline import update_catalog_doc


def main() -> int:
    parser = argparse.ArgumentParser(description="Refresh docs/playbooks/PLAYBOOK-CATALOG.md from imported pack records.")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    result = update_catalog_doc(dry_run=args.dry_run)
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
