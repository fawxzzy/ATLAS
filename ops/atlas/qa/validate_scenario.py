from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from ops._atlas import atlas_root
from ops.atlas.qa._common import default_scenario_dir, load_json_object, validate_scenario_manifest, validate_schema_definition


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate an ATLAS QA scenario manifest.")
    parser.add_argument("--root", type=Path, default=atlas_root())
    parser.add_argument("--scenario-file", type=Path)
    parser.add_argument("--scenario")
    args = parser.parse_args(argv)

    base_root = args.root.resolve()
    if isinstance(args.scenario_file, Path):
        target = args.scenario_file.resolve()
    elif args.scenario:
        target = (default_scenario_dir(root=base_root) / f"{args.scenario}.json").resolve()
    else:
        raise SystemExit("Provide --scenario-file or --scenario.")
    payload = load_json_object(target)
    errors = [*validate_schema_definition("atlas.qa.scenario.v1", root=base_root), *validate_scenario_manifest(payload, root=base_root)]
    print(json.dumps({"ok": not errors, "errors": errors}, indent=2))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
