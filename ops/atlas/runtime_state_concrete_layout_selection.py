from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from ops._atlas import atlas_root, normalize_slashes, path_is_within, resolve_atlas_path

ADMITTED_TOP_LEVEL_HOME = "runtime"
ADMITTED_CHILD_HOME = "state"
ADMITTED_LAYOUT_FAMILY_SEGMENTS = (
    "runtime",
    "state",
    "ai-long-run-batch-orchestration",
    "queue-or-registry",
)
ADMITTED_LAYOUT_FAMILY_ROOT = "runtime/state/ai-long-run-batch-orchestration/queue-or-registry/"
LAYOUT_STATUS_NOTE = (
    "exact filename, schema, snapshot shape, runtime-state discovery, and final queue-home or registry-home choice remain deferred"
)
DECISION_ADMITTED_ROOT = "admitted-neutral-layout-family-root"
DECISION_ADMITTED_DESCENDANT = "admitted-neutral-layout-family-descendant"
DECISION_NON_ADMITTED_SIBLING = "non-admitted-retained-state-sibling"
DECISION_OUTSIDE_CHILD_HOME = "outside-admitted-state-child-home"
UNSUPPORTED_TOP_LEVEL_KEYS = {
    "candidate_paths",
    "dispatch_mode",
    "discovered_paths",
    "execution_hint",
    "execution_home",
    "input_mode",
    "paths",
    "queue_home",
    "queue_hint",
    "queue_path",
    "registry_home",
    "registry_hint",
    "registry_path",
    "resume_mode",
}


class RuntimeStateConcreteLayoutSelectionError(RuntimeError):
    pass


@dataclass(frozen=True)
class RuntimeStateConcreteLayoutSelectionResult:
    normalized_candidate_path: str
    decision: str
    top_level_home_class: str
    child_home_class: str
    layout_family_root: str
    layout_status_note: str = LAYOUT_STATUS_NOTE

    def to_payload(self) -> dict[str, Any]:
        return {
            "normalized_candidate_path": self.normalized_candidate_path,
            "decision": self.decision,
            "top_level_home_class": self.top_level_home_class,
            "child_home_class": self.child_home_class,
            "layout_family_root": self.layout_family_root,
            "layout_status_note": self.layout_status_note,
        }


def _normalize_text(value: Any) -> str | None:
    if not isinstance(value, str):
        return None
    normalized = " ".join(value.strip().split())
    return normalized or None


def _load_json_payload(*, input_path: Path | None, inline_json: str | None) -> Any:
    if bool(input_path) == bool(inline_json):
        raise RuntimeStateConcreteLayoutSelectionError("Provide exactly one of --input or --json.")
    if input_path is not None:
        try:
            return json.loads(input_path.read_text(encoding="utf-8"))
        except FileNotFoundError as exc:
            raise RuntimeStateConcreteLayoutSelectionError(f"Input file not found: {input_path}") from exc
        except json.JSONDecodeError as exc:
            raise RuntimeStateConcreteLayoutSelectionError(f"Malformed JSON input file: {exc}") from exc
    assert inline_json is not None
    try:
        return json.loads(inline_json)
    except json.JSONDecodeError as exc:
        raise RuntimeStateConcreteLayoutSelectionError(f"Malformed inline JSON payload: {exc}") from exc


def _extract_candidate_path(payload: Any) -> str:
    if isinstance(payload, list):
        raise RuntimeStateConcreteLayoutSelectionError("multi-candidate payloads are unsupported")
    if isinstance(payload, str):
        candidate_path = _normalize_text(payload)
        if candidate_path is None:
            raise RuntimeStateConcreteLayoutSelectionError("candidate_path must be a non-empty string")
        return candidate_path
    if not isinstance(payload, dict):
        raise RuntimeStateConcreteLayoutSelectionError(
            "runtime-state concrete-layout selector input must be a JSON string or JSON object"
        )
    if not payload:
        raise RuntimeStateConcreteLayoutSelectionError("candidate_path is required")

    for key in payload:
        if key in UNSUPPORTED_TOP_LEVEL_KEYS:
            raise RuntimeStateConcreteLayoutSelectionError(f"unsupported input field: {key}")
        if key != "candidate_path":
            raise RuntimeStateConcreteLayoutSelectionError(f"unsupported input field: {key}")

    candidate_path = _normalize_text(payload.get("candidate_path"))
    if candidate_path is None:
        raise RuntimeStateConcreteLayoutSelectionError("candidate_path must be a non-empty string")
    return candidate_path


def _render_candidate_path(relative_path: str) -> str:
    normalized = normalize_slashes(relative_path).strip("/")
    parts = [part for part in normalized.split("/") if part]
    if not parts:
        raise RuntimeStateConcreteLayoutSelectionError("candidate_path must resolve below the ATLAS root")
    if len(parts) <= 2:
        return "/".join(parts) + "/"
    if parts == list(ADMITTED_LAYOUT_FAMILY_SEGMENTS):
        return ADMITTED_LAYOUT_FAMILY_ROOT
    if len(parts) == 3:
        return "/".join(parts) + "/"
    return "/".join(parts)


def _non_admitted_layout_family_root(parts: list[str]) -> str:
    if len(parts) < 3:
        raise RuntimeStateConcreteLayoutSelectionError(
            "candidate_path must resolve at or below one retained-state family root beneath runtime/state/"
        )
    if parts[2] == "ai-long-run-batch-orchestration":
        return "runtime/state/ai-long-run-batch-orchestration/"
    return f"runtime/state/{parts[2]}/"


def classify_runtime_state_concrete_layout_selection(
    payload: Any,
    *,
    root: Path | None = None,
) -> RuntimeStateConcreteLayoutSelectionResult:
    base_root = (root or atlas_root()).resolve()
    candidate_path = _extract_candidate_path(payload)
    resolved = resolve_atlas_path(candidate_path, root=base_root)
    if not path_is_within(resolved, base_root):
        raise RuntimeStateConcreteLayoutSelectionError("candidate_path must resolve within the ATLAS root")

    relative_path = normalize_slashes(str(resolved.relative_to(base_root)))
    normalized_candidate_path = _render_candidate_path(relative_path)
    parts = normalized_candidate_path.strip("/").split("/")
    top_level_home_class = f"{parts[0]}/"

    if len(parts) < 2 or parts[0] != ADMITTED_TOP_LEVEL_HOME or parts[1] != ADMITTED_CHILD_HOME:
        return RuntimeStateConcreteLayoutSelectionResult(
            normalized_candidate_path=normalized_candidate_path,
            decision=DECISION_OUTSIDE_CHILD_HOME,
            top_level_home_class=top_level_home_class,
            child_home_class="none",
            layout_family_root="none",
        )

    admitted_prefix = list(ADMITTED_LAYOUT_FAMILY_SEGMENTS)
    child_home_class = "runtime/state/"

    if parts[: len(admitted_prefix)] == admitted_prefix:
        decision = DECISION_ADMITTED_ROOT if len(parts) == len(admitted_prefix) else DECISION_ADMITTED_DESCENDANT
        layout_family_root = ADMITTED_LAYOUT_FAMILY_ROOT
    else:
        decision = DECISION_NON_ADMITTED_SIBLING
        layout_family_root = _non_admitted_layout_family_root(parts)

    return RuntimeStateConcreteLayoutSelectionResult(
        normalized_candidate_path=normalized_candidate_path,
        decision=decision,
        top_level_home_class=top_level_home_class,
        child_home_class=child_home_class,
        layout_family_root=layout_family_root,
    )


def run_classifier(
    *,
    input_path: Path | None = None,
    inline_json: str | None = None,
    root: Path | None = None,
) -> RuntimeStateConcreteLayoutSelectionResult:
    payload = _load_json_payload(input_path=input_path, inline_json=inline_json)
    return classify_runtime_state_concrete_layout_selection(payload, root=root)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Classify one explicit retained-state layout candidate for queue-or-registry runtime-state control-plane work."
    )
    parser.add_argument("--root", type=Path, default=atlas_root())
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--input", type=Path)
    group.add_argument("--json")
    args = parser.parse_args(argv)

    try:
        result = run_classifier(
            input_path=args.input.resolve() if isinstance(args.input, Path) else None,
            inline_json=args.json,
            root=args.root.resolve(),
        )
    except RuntimeStateConcreteLayoutSelectionError as exc:
        print(str(exc), file=sys.stderr)
        return 1

    print(json.dumps(result.to_payload(), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
