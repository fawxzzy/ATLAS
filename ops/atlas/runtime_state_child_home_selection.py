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
EXCLUDED_CHILD_HOME = "receipts"
LAYOUT_STATUS_NOTE = "exact runtime subtree, filename, schema, snapshot shape, and persistence layout remain deferred"
DECISION_ADMITTED = "admitted-state-child-home-candidate"
DECISION_EXCLUDED = "excluded-receipt-history-child-home"
DECISION_NON_ADMITTED_RUNTIME = "non-admitted-runtime-child-home"
DECISION_OUTSIDE_RUNTIME = "outside-runtime-home-family"
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


class RuntimeStateChildHomeSelectionError(RuntimeError):
    pass


@dataclass(frozen=True)
class RuntimeStateChildHomeSelectionResult:
    normalized_candidate_path: str
    decision: str
    top_level_home_class: str
    child_home_class: str
    layout_status_note: str = LAYOUT_STATUS_NOTE

    def to_payload(self) -> dict[str, Any]:
        return {
            "normalized_candidate_path": self.normalized_candidate_path,
            "decision": self.decision,
            "top_level_home_class": self.top_level_home_class,
            "child_home_class": self.child_home_class,
            "layout_status_note": self.layout_status_note,
        }


def _normalize_text(value: Any) -> str | None:
    if not isinstance(value, str):
        return None
    normalized = " ".join(value.strip().split())
    return normalized or None


def _load_json_payload(*, input_path: Path | None, inline_json: str | None) -> Any:
    if bool(input_path) == bool(inline_json):
        raise RuntimeStateChildHomeSelectionError("Provide exactly one of --input or --json.")
    if input_path is not None:
        try:
            return json.loads(input_path.read_text(encoding="utf-8"))
        except FileNotFoundError as exc:
            raise RuntimeStateChildHomeSelectionError(f"Input file not found: {input_path}") from exc
        except json.JSONDecodeError as exc:
            raise RuntimeStateChildHomeSelectionError(f"Malformed JSON input file: {exc}") from exc
    assert inline_json is not None
    try:
        return json.loads(inline_json)
    except json.JSONDecodeError as exc:
        raise RuntimeStateChildHomeSelectionError(f"Malformed inline JSON payload: {exc}") from exc


def _extract_candidate_path(payload: Any) -> str:
    if isinstance(payload, list):
        raise RuntimeStateChildHomeSelectionError("multi-candidate payloads are unsupported")
    if isinstance(payload, str):
        candidate_path = _normalize_text(payload)
        if candidate_path is None:
            raise RuntimeStateChildHomeSelectionError("candidate_path must be a non-empty string")
        return candidate_path
    if not isinstance(payload, dict):
        raise RuntimeStateChildHomeSelectionError(
            "runtime-state child-home selector input must be a JSON string or JSON object"
        )
    if not payload:
        raise RuntimeStateChildHomeSelectionError("candidate_path is required")

    for key in payload:
        if key in UNSUPPORTED_TOP_LEVEL_KEYS:
            raise RuntimeStateChildHomeSelectionError(f"unsupported input field: {key}")
        if key != "candidate_path":
            raise RuntimeStateChildHomeSelectionError(f"unsupported input field: {key}")

    candidate_path = _normalize_text(payload.get("candidate_path"))
    if candidate_path is None:
        raise RuntimeStateChildHomeSelectionError("candidate_path must be a non-empty string")
    return candidate_path


def _render_candidate_path(relative_path: str) -> str:
    normalized = normalize_slashes(relative_path).strip("/")
    parts = [part for part in normalized.split("/") if part]
    if not parts:
        raise RuntimeStateChildHomeSelectionError("candidate_path must resolve below the ATLAS root")
    if len(parts) == 1:
        return f"{parts[0]}/"
    if len(parts) == 2:
        return f"{parts[0]}/{parts[1]}/"
    return "/".join(parts)


def classify_runtime_state_child_home_selection(
    payload: Any,
    *,
    root: Path | None = None,
) -> RuntimeStateChildHomeSelectionResult:
    base_root = (root or atlas_root()).resolve()
    candidate_path = _extract_candidate_path(payload)
    resolved = resolve_atlas_path(candidate_path, root=base_root)
    if not path_is_within(resolved, base_root):
        raise RuntimeStateChildHomeSelectionError("candidate_path must resolve within the ATLAS root")

    relative_path = normalize_slashes(str(resolved.relative_to(base_root)))
    normalized_candidate_path = _render_candidate_path(relative_path)
    parts = normalized_candidate_path.strip("/").split("/")
    top_level_home_name = parts[0]
    top_level_home_class = f"{top_level_home_name}/"

    if top_level_home_name != ADMITTED_TOP_LEVEL_HOME:
        return RuntimeStateChildHomeSelectionResult(
            normalized_candidate_path=normalized_candidate_path,
            decision=DECISION_OUTSIDE_RUNTIME,
            top_level_home_class=top_level_home_class,
            child_home_class="none",
        )

    if len(parts) < 2:
        raise RuntimeStateChildHomeSelectionError("candidate_path must resolve to a child home below runtime/")

    child_home_name = parts[1]
    child_home_class = f"{ADMITTED_TOP_LEVEL_HOME}/{child_home_name}/"

    if child_home_name == ADMITTED_CHILD_HOME:
        decision = DECISION_ADMITTED
    elif child_home_name == EXCLUDED_CHILD_HOME:
        decision = DECISION_EXCLUDED
    else:
        decision = DECISION_NON_ADMITTED_RUNTIME

    return RuntimeStateChildHomeSelectionResult(
        normalized_candidate_path=normalized_candidate_path,
        decision=decision,
        top_level_home_class=top_level_home_class,
        child_home_class=child_home_class,
    )


def run_classifier(
    *,
    input_path: Path | None = None,
    inline_json: str | None = None,
    root: Path | None = None,
) -> RuntimeStateChildHomeSelectionResult:
    payload = _load_json_payload(input_path=input_path, inline_json=inline_json)
    return classify_runtime_state_child_home_selection(payload, root=root)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Classify one explicit runtime-state child-home candidate for queue-or-registry control-plane work."
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
    except RuntimeStateChildHomeSelectionError as exc:
        print(str(exc), file=sys.stderr)
        return 1

    print(json.dumps(result.to_payload(), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
