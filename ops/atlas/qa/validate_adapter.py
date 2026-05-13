from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from ops._atlas import atlas_root
from ops.atlas.qa._common import load_adapter_manifest, validate_adapter_manifest, validate_schema_definition


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate an ATLAS QA adapter manifest.")
    parser.add_argument("--root", type=Path, default=atlas_root())
    parser.add_argument("--adapter-file", type=Path)
    parser.add_argument("--adapter")
    parser.add_argument("--repo")
    args = parser.parse_args(argv)

    base_root = args.root.resolve()
    if isinstance(args.adapter_file, Path):
        payload = json.loads(args.adapter_file.resolve().read_text(encoding="utf-8"))
    else:
        payload, _ = load_adapter_manifest(root=base_root, adapter_id=args.adapter, repo_id=args.repo)
    errors = [*validate_schema_definition("atlas.qa.adapter.v1", root=base_root), *validate_adapter_manifest(payload, root=base_root)]
    print(json.dumps({"ok": not errors, "errors": errors}, indent=2))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
