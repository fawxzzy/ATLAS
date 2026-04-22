from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from ops._atlas import atlas_root
from ops.atlas.build_codex_context import DEFAULT_OUTPUT_ROOT, build_codex_context, render_codex_prompt, write_codex_context_pack


def _default_context_path(task_id: str, *, root: Path) -> Path:
    return (root / DEFAULT_OUTPUT_ROOT / task_id / "context.json").resolve()


def _slug(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return slug or "task"


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
    parser.add_argument("--mode-id")
    parser.add_argument("--repo")
    parser.add_argument("--objective")
    parser.add_argument("--intent-class", default="operator/conversation")
    parser.add_argument("--write-context-pack", action="store_true")
    parser.add_argument("--output-root")
    args = parser.parse_args(argv)
    if args.mode_id:
        if not args.repo:
            raise SystemExit("Provide --repo when using --mode-id.")
        task_id = _slug(args.task_id or f"{args.mode_id}-{args.repo}")
        objective = args.objective or f"Open the {args.mode_id} for {args.repo}."
        if args.write_context_pack:
            payload = write_codex_context_pack(
                task_id=task_id,
                objective=objective,
                intent_class=args.intent_class,
                session_mode_id=args.mode_id,
                session_mode_repo_input=args.repo,
                root=atlas_root(),
                output_root=Path(args.output_root).resolve() if args.output_root else None,
            )
        else:
            payload = build_codex_context(
                task_id=task_id,
                objective=objective,
                intent_class=args.intent_class,
                session_mode_id=args.mode_id,
                session_mode_repo_input=args.repo,
                root=atlas_root(),
            )
    else:
        if not args.task_id and not args.context_json:
            raise SystemExit("Provide --task-id or --context-json, or use --mode-id with --repo.")
        payload = load_context_pack(
            task_id=args.task_id,
            context_json=Path(args.context_json).resolve() if args.context_json else None,
            root=atlas_root(),
        )
    print(render_codex_prompt(payload))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
