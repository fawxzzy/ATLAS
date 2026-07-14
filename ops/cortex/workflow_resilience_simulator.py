from __future__ import annotations

import argparse
import hashlib
import json
import sys
from collections import OrderedDict
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from ops._atlas import atlas_root, normalize_slashes
from ops.cortex.receipt_replay import run as run_receipt_replay

MANIFEST_VERSION = "atlas.cortex.simulation.workflow-resilience-manifest.v1"
OUTPUT_VERSION = "atlas.cortex.simulation.workflow-resilience.v1"
ADAPTER_ID = "atlas-workflow-resilience"
SCENARIO_CLASSES = {"observed", "proof_recovery", "blocked_hold"}
MANIFEST_FIELDS = {
    "contract_version",
    "scenario_id",
    "generated_at",
    "adapter_id",
    "receipt_replay_manifest_ref",
    "receipt_replay_manifest_digest",
    "max_steps",
    "scenario_classes",
}


def _stable(value: object) -> str:
    raw = json.dumps(value, ensure_ascii=True, sort_keys=True, separators=(",", ":")).encode()
    return "sha256:" + hashlib.sha256(raw).hexdigest()


def _finding(code: str, message: str, **details: object) -> OrderedDict[str, object]:
    item: OrderedDict[str, object] = OrderedDict([("code", code), ("message", message)])
    if details:
        item["details"] = OrderedDict(sorted(details.items()))
    return item


def _safe_ref(value: object, prefix: str) -> str | None:
    if not isinstance(value, str) or not value.strip() or Path(value).is_absolute():
        return None
    ref = normalize_slashes(value).strip("/")
    if ref.startswith("../") or "/../" in f"/{ref}/" or not ref.startswith(prefix) or not ref.endswith(".json"):
        return None
    return ref


def _load_manifest(root: Path, manifest_path: str) -> tuple[str | None, dict[str, Any], list[OrderedDict[str, object]]]:
    blockers: list[OrderedDict[str, object]] = []
    manifest_ref = _safe_ref(manifest_path, "data/cortex/simulation-replays/")
    if manifest_ref is None:
        return None, {}, [_finding("manifest_path_not_admitted", "Simulator manifest path is not admitted.")]
    try:
        payload = json.loads((root / manifest_ref).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return manifest_ref, {}, [_finding("manifest_read_failed", "Simulator manifest could not be read.", error=str(exc))]
    if not isinstance(payload, dict):
        return manifest_ref, {}, [_finding("manifest_not_object", "Simulator manifest must be an object.")]
    unknown = sorted(set(payload) - MANIFEST_FIELDS)
    missing = sorted(MANIFEST_FIELDS - set(payload))
    if unknown:
        blockers.append(_finding("unknown_manifest_fields", "Simulator manifest contains unknown fields.", fields=unknown))
    if missing:
        blockers.append(_finding("manifest_fields_missing", "Simulator manifest is missing fields.", fields=missing))
    if payload.get("contract_version") != MANIFEST_VERSION or payload.get("adapter_id") != ADAPTER_ID:
        blockers.append(_finding("manifest_contract_invalid", "Simulator manifest contract or adapter is invalid."))
    max_steps = payload.get("max_steps")
    if not isinstance(max_steps, int) or isinstance(max_steps, bool) or not 1 <= max_steps <= 8:
        blockers.append(_finding("max_steps_invalid", "max_steps must be an integer from 1 through 8."))
    classes = payload.get("scenario_classes")
    if not isinstance(classes, list) or not classes or len(classes) != len(set(classes)) or any(item not in SCENARIO_CLASSES for item in classes):
        blockers.append(_finding("scenario_classes_invalid", "Scenario classes are empty, duplicated, or unadmitted."))
    return manifest_ref, payload, blockers


def _state(counts: dict[str, object]) -> str:
    if int(counts.get("blocked", 0)):
        return "blocked"
    if int(counts.get("failure", 0)):
        return "failed"
    if int(counts.get("advisory", 0)):
        return "watch"
    return "healthy"


def _templates(observed_state: str, source_refs: list[str]) -> list[OrderedDict[str, object]]:
    first_proof = source_refs[-1:] or ["fresh root receipt"]
    rows: list[tuple[str, str, str, list[str]]] = [
        ("observed", observed_state, "Preserve the replayed state and its receipt correlation without mutation.", source_refs),
    ]
    if observed_state == "blocked":
        rows.extend([
            ("blocked_hold", "blocked", "Hold the lane until the blocker class materially changes.", first_proof),
            ("proof_recovery", "rehearsed", "Rehearse owner-bounded blocker conversion and require a fresh execution receipt.", ["fresh execution receipt", "blocker-class change"]),
            ("proof_recovery", "rehearsed", "Rehearse validation, reconciliation, and marker review after corrected proof.", ["passing validation receipt", "reconciliation receipt"]),
        ])
    elif observed_state == "failed":
        rows.extend([
            ("proof_recovery", "rehearsed", "Rehearse failure isolation and one corrected bounded execution.", ["failure-class evidence", "corrected execution receipt"]),
            ("proof_recovery", "rehearsed", "Rehearse independent verification before reconciliation.", ["passing verification receipt"]),
        ])
    elif observed_state == "watch":
        rows.append(("proof_recovery", "rehearsed", "Request stronger committed evidence before selecting any action.", ["fresh non-advisory receipt"]))
    else:
        rows.append(("observed", "healthy", "Preserve the healthy state and recommend no mutation.", ["continued receipt freshness"]))
    return [OrderedDict([("scenario_class", kind), ("state", state), ("action", action), ("proof_required", proof), ("executed", False)]) for kind, state, action, proof in rows]


def run(*, root: Path, manifest_path: str, output_path: str | None) -> tuple[OrderedDict[str, object], int]:
    manifest_ref, manifest, blockers = _load_manifest(root, manifest_path)
    output_ref = None
    if output_path is not None:
        output_ref = _safe_ref(output_path, "tmp/atlas/")
        if output_ref is None:
            blockers.append(_finding("output_path_not_admitted", "Simulator output path is not admitted."))
    replay_ref = _safe_ref(manifest.get("receipt_replay_manifest_ref"), "data/cortex/simulation-replays/") if manifest else None
    if manifest and replay_ref is None:
        blockers.append(_finding("replay_manifest_path_not_admitted", "Receipt replay manifest path is not admitted."))
    if manifest and replay_ref is not None:
        try:
            raw = (root / replay_ref).read_bytes()
            digest = "sha256:" + hashlib.sha256(raw).hexdigest()
            if manifest.get("receipt_replay_manifest_digest") != digest:
                blockers.append(_finding("replay_manifest_digest_mismatch", "Receipt replay manifest byte digest does not match."))
        except OSError as exc:
            blockers.append(_finding("replay_manifest_read_failed", "Receipt replay manifest could not be read.", error=str(exc)))
    replay_result: dict[str, Any] | None = None
    if not blockers and replay_ref is not None:
        replay_result, replay_code = run_receipt_replay(root=root, manifest_path=replay_ref, output_path=None)
        if replay_code != 0 or replay_result.get("status") != "ok" or not isinstance(replay_result.get("replay"), dict):
            blockers.append(_finding("receipt_replay_not_eligible", "Receipt replay did not produce eligible deterministic evidence."))
    simulation = None
    if not blockers and replay_result is not None:
        replay = replay_result["replay"]
        observed_state = _state(replay["failure_mode_counts"])
        admitted = set(manifest["scenario_classes"])
        templates = [item for item in _templates(observed_state, list(replay["source_refs"])) if item["scenario_class"] in admitted]
        max_steps = int(manifest["max_steps"])
        selected = templates[:max_steps]
        steps = [OrderedDict([("sequence", index + 1), *item.items()]) for index, item in enumerate(selected)]
        reason = "max_steps_reached" if len(templates) > max_steps else "fixed_template_exhausted"
        recommendations = {
            "blocked": ["Keep the lane held until fresh proof changes the blocker class.", "Use a real execution and reconciliation receipt before marker review."],
            "failed": ["Isolate the failure class and require one corrected bounded execution.", "Require independent verification before reconciliation."],
            "watch": ["Collect fresh non-advisory evidence before selecting an action."],
            "healthy": ["Perform no mutation; preserve receipt freshness and monitor for material change."],
        }[observed_state]
        basis = {"manifest": manifest, "manifest_ref": manifest_ref, "replay_id": replay["replay_id"], "steps": steps}
        simulation = OrderedDict([
            ("contract_version", OUTPUT_VERSION), ("simulation_id", _stable(basis)),
            ("generated_at", manifest["generated_at"]), ("scenario_id", manifest["scenario_id"]),
            ("adapter_id", ADAPTER_ID), ("source_refs", [manifest_ref, *list(replay["source_refs"])]),
            ("replay_id", replay["replay_id"]), ("observed_state", observed_state), ("steps", steps),
            ("termination", OrderedDict([("terminated", True), ("reason", reason), ("max_steps", max_steps), ("steps_emitted", len(steps))])),
            ("recommendations", recommendations),
            ("authority", OrderedDict([("advisory_only", True), ("execution_authorized", False), ("dispatch_authorized", False), ("owner_repo_read_authorized", False), ("owner_repo_mutation_authorized", False), ("platform_mutation_authorized", False), ("discord_write_authorized", False), ("board_write_authorized", False), ("deployment_authorized", False), ("approval_authorized", False), ("final_receipt_authorized", False), ("marker_movement_authorized", False)])),
        ])
    status = "blocker" if blockers else "ok"
    result = OrderedDict([("status", status), ("safe_to_use", status == "ok"), ("manifest_ref", manifest_ref), ("output_ref", output_ref), ("simulation", simulation), ("warnings", []), ("blockers", blockers)])
    if simulation is not None and output_ref is not None:
        destination = root / output_ref
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(json.dumps(simulation, ensure_ascii=True, indent=2) + "\n", encoding="utf-8")
    return result, 0 if status == "ok" else 1


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run a bounded advisory Atlas workflow-resilience simulation.")
    parser.add_argument("--manifest", required=True)
    parser.add_argument("--output")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--strict", action="store_true")
    args = parser.parse_args(argv)
    result, code = run(root=atlas_root(), manifest_path=args.manifest, output_path=args.output)
    print(json.dumps(result, ensure_ascii=True, indent=2))
    return code if args.strict else (1 if result["status"] == "blocker" else 0)


if __name__ == "__main__":
    raise SystemExit(main())
