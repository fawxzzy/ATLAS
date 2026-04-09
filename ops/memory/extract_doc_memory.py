from __future__ import annotations

import argparse
from pathlib import Path

from _common import CATALOG_NAME, artifact_output_path, atlas_relative, build_memory_artifact, build_memory_catalog, discover_memory_sources, resolve_atlas_path, write_json


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Extract normalized memory artifacts from selected ATLAS docs.")
    parser.add_argument("--source", action="append", default=[])
    parser.add_argument("--output-dir", default="runtime/cortex/catalog/memory")
    args = parser.parse_args(argv)

    output_dir = resolve_atlas_path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    sources = discover_memory_sources(args.source or None)
    artifacts = [build_memory_artifact(source) for source in sources]
    for artifact in artifacts:
        write_json(artifact_output_path(output_dir, artifact), artifact)

    catalog = build_memory_catalog(artifacts, output_dir)
    write_json(output_dir / CATALOG_NAME, catalog)

    print(f"Memory sources   : {len(sources)}")
    print(f"Memory artifacts : {len(artifacts)}")
    print(f"Output dir       : {atlas_relative(output_dir)}")
    print(f"Catalog          : {atlas_relative(output_dir / CATALOG_NAME)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
