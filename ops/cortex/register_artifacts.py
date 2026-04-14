from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from ops._atlas import atlas_relative, atlas_root, resolve_atlas_path
from ops.cortex._artifacts import default_artifact_source_paths, register_artifact_descriptors


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Register deterministic artifact descriptors for ATLAS runtime artifacts."
    )
    parser.add_argument("--artifact-path", action="append", dest="artifact_paths")
    parser.add_argument("--output-dir", default="runtime/cortex/artifacts")
    args = parser.parse_args(argv)

    root = atlas_root()
    source_paths = (
        [resolve_atlas_path(item, root=root) for item in args.artifact_paths]
        if args.artifact_paths
        else default_artifact_source_paths(root)
    )
    output_dir = resolve_atlas_path(args.output_dir, root=root)
    written = register_artifact_descriptors(source_paths, output_dir=output_dir, root=root)
    summary = {
        "descriptor_contract_version": "atlas.artifact.descriptor.v1",
        "output_dir": atlas_relative(output_dir, root=root),
        "source_paths": [atlas_relative(path, root=root) for path in source_paths],
        "descriptor_count": len(written),
        "descriptors": written,
    }
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
