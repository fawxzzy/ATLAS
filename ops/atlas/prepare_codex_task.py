from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from ops._atlas import atlas_root
from ops.atlas.build_codex_context import DEFAULT_OUTPUT_ROOT, render_codex_prompt


def _default_context_path(task_id: str, *, root: Path) -> Path:
    return (root / DEFAULT_OUTPUT_ROOT / task_id / "context.json").resolve()


def load_context_pack(*, task_id: str | None, context_json: Path | None, root: Path | None = None) -> dict[str, object]:
    base_root = (root or atlas_root()).resolve()
    path = context_json.resolve() if context_json else _default_context_path(str(task_id), root=base_root)
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("Context pack must be a JSON object.")
    return payload


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Render a copy-paste-ready Codex prompt from a context pack.")
    parser.add_argument("--task-id")
    parser.add_argument("--context-json")
    args = parser.parse_args(argv)
    if not args.task_id and not args.context_json:
        raise SystemExit("Provide --task-id or --context-json.")

    payload = load_context_pack(
        task_id=args.task_id,
        context_json=Path(args.context_json).resolve() if args.context_json else None,
        root=atlas_root(),
    )
    print(render_codex_prompt(payload))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
