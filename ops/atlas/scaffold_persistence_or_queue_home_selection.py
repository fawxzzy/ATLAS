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

ADMITTED_HOME_CLASS = "runtime"
FORBIDDEN_HOME_CLASSES = (
    "repos",
    "docs",
    "ops",
    "data",
    "packages",
    "tmp",
    "secrets",
)
LAYOUT_STATUS_NOTE = "exact runtime subpath, filename, schema, and persistence layout remain deferred"
DECISION_ADMITTED = "admitted-runtime-home-candidate"
DECISION_FORBIDDEN = "forbidden-home-class"
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


class ScaffoldPersistenceOrQueueHomeSelectionError(RuntimeError):
    pass


@dataclass(frozen=True)
class ScaffoldPersistenceOrQueueHomeSelectionResult:
    normalized_candidate_path: str
    decision: str
    home_class: str
    layout_status_note: str = LAYOUT_STATUS_NOTE

    def to_payload(self) -> dict[str, Any]:
        return {
            "normalized_candidate_path": self.normalized_candidate_path,
            "decision": self.decision,
            "home_class": self.home_class,
            "layout_status_note": self.layout_status_note,
        }


def _normalize_text(value: Any) -> str | None:
    if not isinstance(value, str):
        return None
    normalized = " ".join(value.strip().split())
    return normalized or None


def _load_json_payload(*, input_path: Path | None, inline_json: str | None) -> Any:
    if bool(input_path) == bool(inline_json):
        raise ScaffoldPersistenceOrQueueHomeSelectionError("Provide exactly one of --input or --json.")
    if input_path is not None:
        try:
            return json.loads(input_path.read_text(encoding="utf-8"))
        except FileNotFoundError as exc:
            raise ScaffoldPersistenceOrQueueHomeSelectionError(f"Input file not found: {input_path}") from exc
        except json.JSONDecodeError as exc:
            raise ScaffoldPersistenceOrQueueHomeSelectionError(f"Malformed JSON input file: {exc}") from exc
    assert inline_json is not None
    try:
        return json.loads(inline_json)
    except json.JSONDecodeError as exc:
        raise ScaffoldPersistenceOrQueueHomeSelectionError(f"Malformed inline JSON payload: {exc}") from exc


def _extract_candidate_path(payload: Any) -> str:
    if isinstance(payload, list):
        raise ScaffoldPersistenceOrQueueHomeSelectionError("multi-candidate payloads are unsupported")
    if isinstance(payload, str):
        candidate_path = _normalize_text(payload)
        if candidate_path is None:
            raise ScaffoldPersistenceOrQueueHomeSelectionError("candidate path must be a non-empty string")
        return candidate_path
    if not isinstance(payload, dict):
        raise ScaffoldPersistenceOrQueueHomeSelectionError(
            "storage-home classifier input must be a JSON string or JSON object"
        )
    if not payload:
        raise ScaffoldPersistenceOrQueueHomeSelectionError("candidate_path is required")

    for key in payload:
        if key in UNSUPPORTED_TOP_LEVEL_KEYS:
            raise ScaffoldPersistenceOrQueueHomeSelectionError(f"unsupported input field: {key}")
        if key != "candidate_path":
            raise ScaffoldPersistenceOrQueueHomeSelectionError(f"unsupported input field: {key}")

    candidate_path = _normalize_text(payload.get("candidate_path"))
    if candidate_path is None:
        raise ScaffoldPersistenceOrQueueHomeSelectionError("candidate_path must be a non-empty string")
    return candidate_path


def _render_candidate_path(relative_path: str) -> str:
    normalized = normalize_slashes(relative_path).strip("/")
    parts = [part for part in normalized.split("/") if part]
    if not parts:
        raise ScaffoldPersistenceOrQueueHomeSelectionError("candidate_path must resolve below the ATLAS root")
    if len(parts) == 1:
        return f"{parts[0]}/"
    return "/".join(parts)


def classify_scaffold_persistence_or_queue_home_selection(
    payload: Any,
    *,
    root: Path | None = None,
) -> ScaffoldPersistenceOrQueueHomeSelectionResult:
    base_root = (root or atlas_root()).resolve()
    candidate_path = _extract_candidate_path(payload)
    resolved = resolve_atlas_path(candidate_path, root=base_root)
    if not path_is_within(resolved, base_root):
        raise ScaffoldPersistenceOrQueueHomeSelectionError("candidate_path must resolve within the ATLAS root")

    relative_path = normalize_slashes(str(resolved.relative_to(base_root)))
    normalized_candidate_path = _render_candidate_path(relative_path)
    home_class_name = normalized_candidate_path.split("/", 1)[0]
    home_class = f"{home_class_name}/"

    if home_class_name == ADMITTED_HOME_CLASS:
        decision = DECISION_ADMITTED
    elif home_class_name in FORBIDDEN_HOME_CLASSES:
        decision = DECISION_FORBIDDEN
    else:
        raise ScaffoldPersistenceOrQueueHomeSelectionError(
            f"candidate_path resolves to unsupported top-level home class: {home_class_name}"
        )

    return ScaffoldPersistenceOrQueueHomeSelectionResult(
        normalized_candidate_path=normalized_candidate_path,
        decision=decision,
        home_class=home_class,
    )


def run_classifier(
    *,
    input_path: Path | None = None,
    inline_json: str | None = None,
    root: Path | None = None,
) -> ScaffoldPersistenceOrQueueHomeSelectionResult:
    payload = _load_json_payload(input_path=input_path, inline_json=inline_json)
    return classify_scaffold_persistence_or_queue_home_selection(payload, root=root)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Classify one explicit storage-home candidate for queue-or-registry scaffold persistence."
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
    except ScaffoldPersistenceOrQueueHomeSelectionError as exc:
        print(str(exc), file=sys.stderr)
        return 1

    print(json.dumps(result.to_payload(), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
