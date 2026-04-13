from __future__ import annotations

import json
import argparse

from _pipeline import validate_catalog


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Validate knowledge imports, receipts, runtime catalogs, promotion docs, and the deterministic query bundle."
    )
    parser.add_argument(
        "--skip-query-bundle",
        action="store_true",
        help="Validate the import, receipt, promotion, and runtime catalog lanes without checking runtime/cortex/query/knowledge/bundle.json.",
    )
    args = parser.parse_args()

    report = validate_catalog(include_query_bundle=not args.skip_query_bundle)
    print(json.dumps(report, indent=2))
    return 0 if report["summary"]["errors"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
