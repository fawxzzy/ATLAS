from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from ops._atlas import atlas_root, resolve_atlas_path
from ops.cortex._artifacts import register_artifact_descriptors
from ops.cortex.world_model import write_world_model_state
from ops.cortex.world_model import world_model_state_root


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Build deterministic ATLAS world-model state and attention artifacts from explicit sources."
    )
    parser.add_argument("--descriptor-root", default="runtime/cortex/artifacts")
    args = parser.parse_args(argv)

    root = atlas_root()
    descriptor_root = resolve_atlas_path(args.descriptor_root, root=root)
    summary = write_world_model_state(
        descriptor_root=descriptor_root,
        root=root,
    )
    descriptor_summary = register_artifact_descriptors(
        [world_model_state_root(root)],
        output_dir=root / "runtime" / "cortex" / "artifacts",
        root=root,
    )
    summary["registered_descriptor_count"] = len(descriptor_summary)
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
