from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Sequence

from .collectors import collect_observed_state
from .reporting import build_validation_report, load_json_object, write_sample_bundle


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="ATLAS Machine Stewardship Wave 0A evidence-plane utility."
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    validate = subparsers.add_parser("validate", help="Validate one machine contract.")
    validate.add_argument("document", type=Path)

    sample = subparsers.add_parser(
        "sample",
        help="Collect redacted identity and fixed-local-volume metadata only.",
    )
    sample.add_argument("--output-dir", type=Path, required=True)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.command == "validate":
        report = build_validation_report(load_json_object(args.document))
        print(json.dumps(report, sort_keys=True, separators=(",", ":")))
        return 0 if report["valid"] else 1
    if args.command == "sample":
        result = write_sample_bundle(args.output_dir, collect_observed_state())
        print(json.dumps(result, sort_keys=True, separators=(",", ":")))
        return 0
    raise AssertionError(f"Unhandled command: {args.command}")


if __name__ == "__main__":
    raise SystemExit(main())
