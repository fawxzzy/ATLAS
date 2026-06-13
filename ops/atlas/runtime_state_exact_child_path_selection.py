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
    "exact filename, schema, snapshot shape, runtime-state discovery, and final artifact-shape choice remain deferred"
)

DECISION_QUEUE_ROOT = "queue-home-destination-root-still-unresolved"
DECISION_QUEUE_EXACT = "admitted-queue-home-exact-child-path-candidate"
DECISION_REGISTRY_ROOT = "registry-home-destination-root-still-unresolved"
DECISION_REGISTRY_EXACT = "admitted-registry-home-exact-child-path-candidate"
DECISION_NEUTRAL_ROOT = "neutral-family-root-without-destination-class"
DECISION_NON_ADMITTED_DESCENDANT = "non-admitted-neutral-family-descendant"
DECISION_OUTSIDE_NEUTRAL_ROOT = "outside-admitted-neutral-family-root"

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


class RuntimeStateExactChildPathSelectionError(RuntimeError):
    pass


@dataclass(frozen=True)
class RuntimeStateExactChildPathSelectionResult:
    normalized_candidate_path: str
    decision: str
    top_level_home_class: str
    child_home_class: str
    layout_family_root: str
    destination_class: str
    destination_root_path: str
    exact_child_path_candidate: str
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
            "artifact_status_note": self.artifact_status_note,
        }


def _normalize_text(value: Any) -> str | None:
    if not isinstance(value, str):
        return None
    normalized = " ".join(value.strip().split())
    return normalized or None


def _load_json_payload(*, input_path: Path | None, inline_json: str | None) -> Any:
    if bool(input_path) == bool(inline_json):
        raise RuntimeStateExactChildPathSelectionError("Provide exactly one of --input or --json.")
    if input_path is not None:
        try:
            return json.loads(input_path.read_text(encoding="utf-8"))
        except FileNotFoundError as exc:
            raise RuntimeStateExactChildPathSelectionError(f"Input file not found: {input_path}") from exc
        except json.JSONDecodeError as exc:
            raise RuntimeStateExactChildPathSelectionError(f"Malformed JSON input file: {exc}") from exc
    assert inline_json is not None
    try:
        return json.loads(inline_json)
    except json.JSONDecodeError as exc:
        raise RuntimeStateExactChildPathSelectionError(f"Malformed inline JSON payload: {exc}") from exc


def _extract_candidate_path(payload: Any) -> str:
    if isinstance(payload, list):
        raise RuntimeStateExactChildPathSelectionError("multi-candidate payloads are unsupported")
    if isinstance(payload, str):
        candidate_path = _normalize_text(payload)
        if candidate_path is None:
            raise RuntimeStateExactChildPathSelectionError("candidate_path must be a non-empty string")
        return candidate_path
    if not isinstance(payload, dict):
        raise RuntimeStateExactChildPathSelectionError(
            "runtime-state exact child-path selector input must be a JSON string or JSON object"
        )
    if not payload:
        raise RuntimeStateExactChildPathSelectionError("candidate_path is required")

    for key in payload:
        if key in UNSUPPORTED_TOP_LEVEL_KEYS:
            raise RuntimeStateExactChildPathSelectionError(f"unsupported input field: {key}")
        if key != "candidate_path":
            raise RuntimeStateExactChildPathSelectionError(f"unsupported input field: {key}")

    candidate_path = _normalize_text(payload.get("candidate_path"))
    if candidate_path is None:
        raise RuntimeStateExactChildPathSelectionError("candidate_path must be a non-empty string")
    return candidate_path


def _render_candidate_path(relative_path: str) -> str:
    normalized = normalize_slashes(relative_path).strip("/")
    parts = [part for part in normalized.split("/") if part]
    if not parts:
        raise RuntimeStateExactChildPathSelectionError("candidate_path must resolve below the ATLAS root")
    if tuple(parts) == ADMITTED_LAYOUT_FAMILY_SEGMENTS:
        return ADMITTED_LAYOUT_FAMILY_ROOT
    if tuple(parts) == QUEUE_HOME_SEGMENTS:
        return QUEUE_HOME_ROOT
    if tuple(parts) == REGISTRY_HOME_SEGMENTS:
        return REGISTRY_HOME_ROOT
    if len(parts) <= 3:
        return "/".join(parts) + "/"
    return "/".join(parts)


def _exact_child_path_candidate(parts: list[str], destination_segments: tuple[str, ...], normalized_candidate_path: str) -> str:
    return "none" if len(parts) == len(destination_segments) else normalized_candidate_path


def classify_runtime_state_exact_child_path_selection(
    payload: Any,
    *,
    root: Path | None = None,
) -> RuntimeStateExactChildPathSelectionResult:
    base_root = (root or atlas_root()).resolve()
    candidate_path = _extract_candidate_path(payload)
    resolved = resolve_atlas_path(candidate_path, root=base_root)
    if not path_is_within(resolved, base_root):
        raise RuntimeStateExactChildPathSelectionError("candidate_path must resolve within the ATLAS root")

    relative_path = normalize_slashes(str(resolved.relative_to(base_root)))
    normalized_candidate_path = _render_candidate_path(relative_path)
    parts = normalized_candidate_path.strip("/").split("/")
    top_level_home_class = f"{parts[0]}/"
    admitted_prefix = list(ADMITTED_LAYOUT_FAMILY_SEGMENTS)

    if parts[: len(admitted_prefix)] != admitted_prefix:
        return RuntimeStateExactChildPathSelectionResult(
            normalized_candidate_path=normalized_candidate_path,
            decision=DECISION_OUTSIDE_NEUTRAL_ROOT,
            top_level_home_class=top_level_home_class,
            child_home_class="none",
            layout_family_root="none",
            destination_class="none",
            destination_root_path="none",
            exact_child_path_candidate="none",
        )

    if len(parts) == len(admitted_prefix):
        return RuntimeStateExactChildPathSelectionResult(
            normalized_candidate_path=normalized_candidate_path,
            decision=DECISION_NEUTRAL_ROOT,
            top_level_home_class=top_level_home_class,
            child_home_class="runtime/state/",
            layout_family_root=ADMITTED_LAYOUT_FAMILY_ROOT,
            destination_class="none",
            destination_root_path="none",
            exact_child_path_candidate="none",
        )

    if parts[: len(QUEUE_HOME_SEGMENTS)] == list(QUEUE_HOME_SEGMENTS):
        decision = DECISION_QUEUE_ROOT if len(parts) == len(QUEUE_HOME_SEGMENTS) else DECISION_QUEUE_EXACT
        return RuntimeStateExactChildPathSelectionResult(
            normalized_candidate_path=normalized_candidate_path,
            decision=decision,
            top_level_home_class=top_level_home_class,
            child_home_class="runtime/state/",
            layout_family_root=ADMITTED_LAYOUT_FAMILY_ROOT,
            destination_class="queue-home",
            destination_root_path=QUEUE_HOME_ROOT,
            exact_child_path_candidate=_exact_child_path_candidate(
                parts,
                QUEUE_HOME_SEGMENTS,
                normalized_candidate_path,
            ),
        )

    if parts[: len(REGISTRY_HOME_SEGMENTS)] == list(REGISTRY_HOME_SEGMENTS):
        decision = DECISION_REGISTRY_ROOT if len(parts) == len(REGISTRY_HOME_SEGMENTS) else DECISION_REGISTRY_EXACT
        return RuntimeStateExactChildPathSelectionResult(
            normalized_candidate_path=normalized_candidate_path,
            decision=decision,
            top_level_home_class=top_level_home_class,
            child_home_class="runtime/state/",
            layout_family_root=ADMITTED_LAYOUT_FAMILY_ROOT,
            destination_class="registry-home",
            destination_root_path=REGISTRY_HOME_ROOT,
            exact_child_path_candidate=_exact_child_path_candidate(
                parts,
                REGISTRY_HOME_SEGMENTS,
                normalized_candidate_path,
            ),
        )

    destination_class = parts[len(admitted_prefix)]
    return RuntimeStateExactChildPathSelectionResult(
        normalized_candidate_path=normalized_candidate_path,
        decision=DECISION_NON_ADMITTED_DESCENDANT,
        top_level_home_class=top_level_home_class,
        child_home_class="runtime/state/",
        layout_family_root=ADMITTED_LAYOUT_FAMILY_ROOT,
        destination_class=destination_class,
        destination_root_path="none",
        exact_child_path_candidate="none",
    )


def run_classifier(
    *,
    input_path: Path | None = None,
    inline_json: str | None = None,
    root: Path | None = None,
) -> RuntimeStateExactChildPathSelectionResult:
    payload = _load_json_payload(input_path=input_path, inline_json=inline_json)
    return classify_runtime_state_exact_child_path_selection(payload, root=root)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Classify one explicit retained-state exact child-path candidate for queue-or-registry "
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
    except RuntimeStateExactChildPathSelectionError as exc:
        print(str(exc), file=sys.stderr)
        return 1

    print(json.dumps(result.to_payload(), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
