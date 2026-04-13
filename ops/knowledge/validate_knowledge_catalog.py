from __future__ import annotations

import json

from _pipeline import validate_catalog


def main() -> int:
    report = validate_catalog()
    print(json.dumps(report, indent=2))
    return 0 if report["summary"]["errors"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
