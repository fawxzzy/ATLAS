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

ADMITTED_LAYOUT_FAMILY_SEGMENTS = (
    "runtime",
    "state",
    "ai-long-run-batch-orchestration",
    "queue-or-registry",
)
ADMITTED_LAYOUT_FAMILY_ROOT = "runtime/state/ai-long-run-batch-orchestration/queue-or-registry/"
QUEUE_HOME_SEGMENTS = ADMITTED_LAYOUT_FAMILY_SEGMENTS + ("queue-home",)
QUEUE_HOME_ROOT = "runtime/state/ai-long-run-batch-orchestration/queue-or-registry/queue-home/"
REGISTRY_HOME_SEGMENTS = ADMITTED_LAYOUT_FAMILY_SEGMENTS + ("registry-home",)
REGISTRY_HOME_ROOT = "runtime/state/ai-long-run-batch-orchestration/queue-or-registry/registry-home/"
ARTIFACT_STATUS_NOTE = (
    "live runtime-state read execution, queue mutation, registry mutation, execution-ready entry movement, and final execution-home routing remain deferred"
)

DECISION_QUEUE_ROOT = "queue-home-destination-root-still-unresolved"
DECISION_QUEUE_DIRECT_BLOCKED = "admitted-queue-home-live-direct-json-read-blocked-before-execution"
DECISION_QUEUE_DIRECTORY_BLOCKED = "admitted-queue-home-live-directory-read-blocked-before-execution"
DECISION_REGISTRY_ROOT = "registry-home-destination-root-still-unresolved"
DECISION_REGISTRY_DIRECT_BLOCKED = "admitted-registry-home-live-direct-json-read-blocked-before-execution"
DECISION_REGISTRY_DIRECTORY_BLOCKED = "admitted-registry-home-live-directory-read-blocked-before-execution"
DECISION_UNSUPPORTED_TRANSITION = "non-admitted-discovery-mode-execution-transition"
DECISION_NEUTRAL_ROOT = "neutral-family-root-without-destination-class"
DECISION_NON_ADMITTED_DESCENDANT = "non-admitted-neutral-family-descendant"
DECISION_OUTSIDE_NEUTRAL_ROOT = "outside-admitted-neutral-family-root"

SHAPE_JSON = "json-file-candidate"
SHAPE_DIRECTORY = "directory-candidate"
SHAPE_NONE = "none"

DISCOVERY_JSON_READ = "direct-json-file-read-candidate"
DISCOVERY_DIRECTORY_READ = "directory-scoped-read-candidate"
DISCOVERY_NONE = "none"

TRANSITION_DIRECT_BLOCKED = "blocked-pending-live-direct-json-read"
TRANSITION_DIRECTORY_BLOCKED = "blocked-pending-live-directory-read"
TRANSITION_NONE = "none"

UNSUPPORTED_TOP_LEVEL_KEYS = {
    "candidate_paths",
    "destination_class",
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


class RuntimeStateExecutionReadyTransitionSemanticsError(RuntimeError):
    pass


@dataclass(frozen=True)
class RuntimeStateExecutionReadyTransitionSemanticsResult:
    normalized_candidate_path: str
    decision: str
    top_level_home_class: str
    child_home_class: str
    layout_family_root: str
    destination_class: str
    destination_root_path: str
    exact_child_path_candidate: str
    artifact_shape_class: str
    discovery_mode_class: str
    execution_transition_class: str
    artifact_status_note: str = ARTIFACT_STATUS_NOTE

    def to_payload(self) -> dict[str, Any]:
        return {
            "normalized_candidate_path": self.normalized_candidate_path,
            "decision": self.decision,
            "top_level_home_class": self.top_level_home_class,
            "child_home_class": self.child_home_class,
            "layout_family_root": self.layout_family_root,
            "destination_class": self.destination_class,
            "destination_root_path": self.destination_root_path,
            "exact_child_path_candidate": self.exact_child_path_candidate,
            "artifact_shape_class": self.artifact_shape_class,
            "discovery_mode_class": self.discovery_mode_class,
            "execution_transition_class": self.execution_transition_class,
            "artifact_status_note": self.artifact_status_note,
        }


def _normalize_text(value: Any) -> str | None:
    if not isinstance(value, str):
        return None
    normalized = " ".join(value.strip().split())
    return normalized or None


def _load_json_payload(*, input_path: Path | None, inline_json: str | None) -> Any:
    if bool(input_path) == bool(inline_json):
        raise RuntimeStateExecutionReadyTransitionSemanticsError("Provide exactly one of --input or --json.")
    if input_path is not None:
        try:
            return json.loads(input_path.read_text(encoding="utf-8"))
        except FileNotFoundError as exc:
            raise RuntimeStateExecutionReadyTransitionSemanticsError(f"Input file not found: {input_path}") from exc
        except json.JSONDecodeError as exc:
            raise RuntimeStateExecutionReadyTransitionSemanticsError(f"Malformed JSON input file: {exc}") from exc
    assert inline_json is not None
    try:
        return json.loads(inline_json)
    except json.JSONDecodeError as exc:
        raise RuntimeStateExecutionReadyTransitionSemanticsError(f"Malformed inline JSON payload: {exc}") from exc


def _extract_candidate_path(payload: Any) -> str:
    if isinstance(payload, list):
        raise RuntimeStateExecutionReadyTransitionSemanticsError("multi-candidate payloads are unsupported")
    if isinstance(payload, str):
        candidate_path = _normalize_text(payload)
        if candidate_path is None:
            raise RuntimeStateExecutionReadyTransitionSemanticsError("candidate_path must be a non-empty string")
        return candidate_path
    if not isinstance(payload, dict):
        raise RuntimeStateExecutionReadyTransitionSemanticsError(
            "runtime-state execution-ready-transition selector input must be a JSON string or JSON object"
        )
    if not payload:
        raise RuntimeStateExecutionReadyTransitionSemanticsError("candidate_path is required")

    for key in payload:
        if key in UNSUPPORTED_TOP_LEVEL_KEYS:
            raise RuntimeStateExecutionReadyTransitionSemanticsError(f"unsupported input field: {key}")
        if key != "candidate_path":
            raise RuntimeStateExecutionReadyTransitionSemanticsError(f"unsupported input field: {key}")

    candidate_path = _normalize_text(payload.get("candidate_path"))
    if candidate_path is None:
        raise RuntimeStateExecutionReadyTransitionSemanticsError("candidate_path must be a non-empty string")
    return candidate_path


def _looks_like_directory(candidate_path: str) -> bool:
    return normalize_slashes(candidate_path).endswith("/")


def _render_candidate_path(relative_path: str, *, looks_like_directory: bool) -> str:
    normalized = normalize_slashes(relative_path).strip("/")
    parts = [part for part in normalized.split("/") if part]
    if not parts:
        raise RuntimeStateExecutionReadyTransitionSemanticsError("candidate_path must resolve below the ATLAS root")
    if tuple(parts) == ADMITTED_LAYOUT_FAMILY_SEGMENTS:
        return ADMITTED_LAYOUT_FAMILY_ROOT
    if tuple(parts) == QUEUE_HOME_SEGMENTS:
        return QUEUE_HOME_ROOT
    if tuple(parts) == REGISTRY_HOME_SEGMENTS:
        return REGISTRY_HOME_ROOT
    if looks_like_directory or len(parts) <= 3:
        return "/".join(parts) + "/"
    return "/".join(parts)


def classify_runtime_state_execution_ready_transition_semantics(
    payload: Any,
    *,
    root: Path | None = None,
) -> RuntimeStateExecutionReadyTransitionSemanticsResult:
    base_root = (root or atlas_root()).resolve()
    candidate_path = _extract_candidate_path(payload)
    looks_like_directory = _looks_like_directory(candidate_path)
    resolved = resolve_atlas_path(candidate_path, root=base_root)
    if not path_is_within(resolved, base_root):
        raise RuntimeStateExecutionReadyTransitionSemanticsError("candidate_path must resolve within the ATLAS root")

    relative_path = normalize_slashes(str(resolved.relative_to(base_root)))
    normalized_candidate_path = _render_candidate_path(relative_path, looks_like_directory=looks_like_directory)
    parts = normalized_candidate_path.strip("/").split("/")
    top_level_home_class = f"{parts[0]}/"
    admitted_prefix = list(ADMITTED_LAYOUT_FAMILY_SEGMENTS)

    if parts[: len(admitted_prefix)] != admitted_prefix:
        return RuntimeStateExecutionReadyTransitionSemanticsResult(
            normalized_candidate_path=normalized_candidate_path,
            decision=DECISION_OUTSIDE_NEUTRAL_ROOT,
            top_level_home_class=top_level_home_class,
            child_home_class=TRANSITION_NONE,
            layout_family_root=TRANSITION_NONE,
            destination_class=TRANSITION_NONE,
            destination_root_path=TRANSITION_NONE,
            exact_child_path_candidate=TRANSITION_NONE,
            artifact_shape_class=SHAPE_NONE,
            discovery_mode_class=DISCOVERY_NONE,
            execution_transition_class=TRANSITION_NONE,
        )

    if len(parts) == len(admitted_prefix):
        return RuntimeStateExecutionReadyTransitionSemanticsResult(
            normalized_candidate_path=normalized_candidate_path,
            decision=DECISION_NEUTRAL_ROOT,
            top_level_home_class=top_level_home_class,
            child_home_class="runtime/state/",
            layout_family_root=ADMITTED_LAYOUT_FAMILY_ROOT,
            destination_class=TRANSITION_NONE,
            destination_root_path=TRANSITION_NONE,
            exact_child_path_candidate=TRANSITION_NONE,
            artifact_shape_class=SHAPE_NONE,
            discovery_mode_class=DISCOVERY_NONE,
            execution_transition_class=TRANSITION_NONE,
        )

    if parts[: len(QUEUE_HOME_SEGMENTS)] == list(QUEUE_HOME_SEGMENTS):
        return _classify_destination_candidate(
            normalized_candidate_path=normalized_candidate_path,
            parts=parts,
            destination_segments=QUEUE_HOME_SEGMENTS,
            destination_root=QUEUE_HOME_ROOT,
            destination_class="queue-home",
            destination_root_decision=DECISION_QUEUE_ROOT,
            direct_blocked_decision=DECISION_QUEUE_DIRECT_BLOCKED,
            directory_blocked_decision=DECISION_QUEUE_DIRECTORY_BLOCKED,
        )

    if parts[: len(REGISTRY_HOME_SEGMENTS)] == list(REGISTRY_HOME_SEGMENTS):
        return _classify_destination_candidate(
            normalized_candidate_path=normalized_candidate_path,
            parts=parts,
            destination_segments=REGISTRY_HOME_SEGMENTS,
            destination_root=REGISTRY_HOME_ROOT,
            destination_class="registry-home",
            destination_root_decision=DECISION_REGISTRY_ROOT,
            direct_blocked_decision=DECISION_REGISTRY_DIRECT_BLOCKED,
            directory_blocked_decision=DECISION_REGISTRY_DIRECTORY_BLOCKED,
        )

    destination_class = parts[len(admitted_prefix)]
    return RuntimeStateExecutionReadyTransitionSemanticsResult(
        normalized_candidate_path=normalized_candidate_path,
        decision=DECISION_NON_ADMITTED_DESCENDANT,
        top_level_home_class=top_level_home_class,
        child_home_class="runtime/state/",
        layout_family_root=ADMITTED_LAYOUT_FAMILY_ROOT,
        destination_class=destination_class,
        destination_root_path=TRANSITION_NONE,
        exact_child_path_candidate=TRANSITION_NONE,
        artifact_shape_class=SHAPE_NONE,
        discovery_mode_class=DISCOVERY_NONE,
        execution_transition_class=TRANSITION_NONE,
    )


def _classify_destination_candidate(
    *,
    normalized_candidate_path: str,
    parts: list[str],
    destination_segments: tuple[str, ...],
    destination_root: str,
    destination_class: str,
    destination_root_decision: str,
    direct_blocked_decision: str,
    directory_blocked_decision: str,
) -> RuntimeStateExecutionReadyTransitionSemanticsResult:
    top_level_home_class = f"{parts[0]}/"
    if len(parts) == len(destination_segments):
        return RuntimeStateExecutionReadyTransitionSemanticsResult(
            normalized_candidate_path=normalized_candidate_path,
            decision=destination_root_decision,
            top_level_home_class=top_level_home_class,
            child_home_class="runtime/state/",
            layout_family_root=ADMITTED_LAYOUT_FAMILY_ROOT,
            destination_class=destination_class,
            destination_root_path=destination_root,
            exact_child_path_candidate=TRANSITION_NONE,
            artifact_shape_class=SHAPE_NONE,
            discovery_mode_class=DISCOVERY_NONE,
            execution_transition_class=TRANSITION_NONE,
        )

    exact_child_path_candidate = normalized_candidate_path
    if normalized_candidate_path.endswith("/"):
        return RuntimeStateExecutionReadyTransitionSemanticsResult(
            normalized_candidate_path=normalized_candidate_path,
            decision=directory_blocked_decision,
            top_level_home_class=top_level_home_class,
            child_home_class="runtime/state/",
            layout_family_root=ADMITTED_LAYOUT_FAMILY_ROOT,
            destination_class=destination_class,
            destination_root_path=destination_root,
            exact_child_path_candidate=exact_child_path_candidate,
            artifact_shape_class=SHAPE_DIRECTORY,
            discovery_mode_class=DISCOVERY_DIRECTORY_READ,
            execution_transition_class=TRANSITION_DIRECTORY_BLOCKED,
        )

    if normalized_candidate_path.endswith(".json"):
        return RuntimeStateExecutionReadyTransitionSemanticsResult(
            normalized_candidate_path=normalized_candidate_path,
            decision=direct_blocked_decision,
            top_level_home_class=top_level_home_class,
            child_home_class="runtime/state/",
            layout_family_root=ADMITTED_LAYOUT_FAMILY_ROOT,
            destination_class=destination_class,
            destination_root_path=destination_root,
            exact_child_path_candidate=exact_child_path_candidate,
            artifact_shape_class=SHAPE_JSON,
            discovery_mode_class=DISCOVERY_JSON_READ,
            execution_transition_class=TRANSITION_DIRECT_BLOCKED,
        )

    return RuntimeStateExecutionReadyTransitionSemanticsResult(
        normalized_candidate_path=normalized_candidate_path,
        decision=DECISION_UNSUPPORTED_TRANSITION,
        top_level_home_class=top_level_home_class,
        child_home_class="runtime/state/",
        layout_family_root=ADMITTED_LAYOUT_FAMILY_ROOT,
        destination_class=destination_class,
        destination_root_path=destination_root,
        exact_child_path_candidate=exact_child_path_candidate,
        artifact_shape_class=SHAPE_NONE,
        discovery_mode_class=DISCOVERY_NONE,
        execution_transition_class=TRANSITION_NONE,
    )


def run_classifier(
    *,
    input_path: Path | None = None,
    inline_json: str | None = None,
    root: Path | None = None,
) -> RuntimeStateExecutionReadyTransitionSemanticsResult:
    payload = _load_json_payload(input_path=input_path, inline_json=inline_json)
    return classify_runtime_state_execution_ready_transition_semantics(payload, root=root)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Classify one explicit retained-state execution-ready-transition candidate for queue-or-registry "
            "runtime-state control-plane work."
        )
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
    except RuntimeStateExecutionReadyTransitionSemanticsError as exc:
        print(str(exc), file=sys.stderr)
        return 1

    print(json.dumps(result.to_payload(), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
