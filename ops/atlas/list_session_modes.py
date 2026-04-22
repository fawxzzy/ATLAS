from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from ops._atlas import atlas_root
from ops.atlas.load_session_mode_registry import load_session_mode_registry_bundle, select_mode_entry


def _example_opener(mode: dict[str, object], repo_example: str) -> str:
    aliases = mode.get("aliases", [])
    if isinstance(aliases, list) and aliases:
        primary = str(aliases[0]).strip()
        if primary:
            return f"{primary.capitalize()} for {repo_example}."
    return f"Open {mode.get('mode_id')} for {repo_example}."


def _render_text(bundle: dict[str, object], *, repo_example: str) -> str:
    registry = bundle.get("session_mode_registry", {})
    modes = registry.get("modes", []) if isinstance(registry, dict) else []
    lines = [
        "ATLAS session modes",
        "",
        f"Registry: {bundle.get('registry_ref')}",
        f"Mode count: {bundle.get('mode_count')}",
        f"Registry digest: {bundle.get('registry_digest')}",
        "",
    ]
    for mode in modes:
        if not isinstance(mode, dict):
            continue
        resolves_to = mode.get("resolves_to", {}) if isinstance(mode.get("resolves_to"), dict) else {}
        lines += [
            f"- {mode.get('mode_id')} ({mode.get('status')})",
            f"  display: {mode.get('display_name')}",
            f"  default validation: {resolves_to.get('default_validation_mode')}",
            f"  localhost assumption: {resolves_to.get('default_localhost_assumption')}",
            f"  patch style: {resolves_to.get('default_patch_style')}",
            f"  prompt doc: {resolves_to.get('prompt_doc')}",
            f"  workflow doc: {resolves_to.get('workflow_doc')}",
            f"  aliases: {', '.join(str(item) for item in mode.get('aliases', []))}",
            f"  opener: {_example_opener(mode, repo_example)}",
            "",
        ]
    return "\n".join(lines).rstrip() + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="List the root-owned ATLAS named session modes with defaults and example openers.",
    )
    parser.add_argument("--mode-id")
    parser.add_argument("--repo-example", default="fawxzzy-fitness")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)

    bundle = load_session_mode_registry_bundle(root=atlas_root())
    if args.mode_id:
        selected = select_mode_entry(bundle, args.mode_id)
        output = {
            "registry_ref": bundle["registry_ref"],
            "registry_digest": bundle["registry_digest"],
            "mode": selected,
            "example_opener": _example_opener(selected, args.repo_example),
        }
        print(json.dumps(output, indent=2))
        return 0

    if args.json:
        output = {
            "registry_ref": bundle["registry_ref"],
            "registry_digest": bundle["registry_digest"],
            "mode_count": bundle["mode_count"],
            "repo_example": args.repo_example,
            "modes": [
                {
                    **mode,
                    "example_opener": _example_opener(mode, args.repo_example),
                }
                for mode in bundle["session_mode_registry"]["modes"]
            ],
        }
        print(json.dumps(output, indent=2))
        return 0

    print(_render_text(bundle, repo_example=args.repo_example))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
