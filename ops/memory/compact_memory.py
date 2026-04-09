from __future__ import annotations

import argparse

from _common import apply_retention_plan, atlas_relative, build_retention_plan, resolve_atlas_path, write_retention_report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Compact stale previews, redundant receipts, and duplicate memory artifacts.")
    parser.add_argument("--output-dir", default="runtime/receipts/retention")
    parser.add_argument("--execute", action="store_true")
    args = parser.parse_args(argv)

    output_dir = resolve_atlas_path(args.output_dir)
    report = build_retention_plan()
    if args.execute:
        report = apply_retention_plan(report)
    json_path, md_path = write_retention_report(report, output_dir)

    print(f"Retention mode : {report['mode']}")
    print(f"Output json    : {atlas_relative(json_path)}")
    print(f"Output md      : {atlas_relative(md_path)}")
    if args.execute:
        print(f"Performed      : {report['summary'].get('performed', 0)}")
    else:
        print(f"Compacted      : {report['summary']['compacted']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
