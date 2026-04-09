from __future__ import annotations

import argparse

from _common import atlas_relative, build_retention_plan, resolve_atlas_path, write_retention_report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Preview the ATLAS memory and receipt retention plan.")
    parser.add_argument("--output-dir", default="runtime/receipts/retention")
    args = parser.parse_args(argv)

    output_dir = resolve_atlas_path(args.output_dir)
    report = build_retention_plan()
    json_path, md_path = write_retention_report(report, output_dir)

    print(f"Retention mode : {report['mode']}")
    print(f"Output json    : {atlas_relative(json_path)}")
    print(f"Output md      : {atlas_relative(md_path)}")
    print(f"Compacted      : {report['summary']['compacted']}")
    print(f"Archived       : {report['summary']['archived']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
