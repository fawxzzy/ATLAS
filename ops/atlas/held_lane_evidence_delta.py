from __future__ import annotations

import argparse
import hashlib
import json
import sys
from collections.abc import Mapping, Sequence
from pathlib import Path, PurePosixPath
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from ops._atlas import atlas_root


CONTRACT_VERSION = "atlas.held-lane-evidence-delta.v1"
RECEIPT_VERSION = "atlas.held-lane-evidence-delta-receipt.v1"
ALLOWED_SOURCE_PREFIXES = ("docs/", "ops/", "tests/", "data/", "runtime/atlas/")
PROHIBITED_COMPONENTS = {"repos", "secrets"}
PROHIBITED_NAME_TOKENS = {"deploy", "deployment", "deployments", "workflow", "workflows"}
DECISIONS = {"reopen_eligible", "still_held", "blocked"}


class HeldLaneEvidenceDeltaError(RuntimeError):
    pass


def _canonical_json(payload: Mapping[str, Any]) -> str:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def _sha256(raw: bytes) -> str:
    return "sha256:" + hashlib.sha256(raw).hexdigest()


def _validate_ref(ref: object, *, contract: bool = False) -> str:
    if not isinstance(ref, str) or not ref or "\\" in ref:
        raise HeldLaneEvidenceDeltaError("invalid_source_ref")
    path = PurePosixPath(ref)
    if path.is_absolute() or ".." in path.parts or ref != path.as_posix():
        raise HeldLaneEvidenceDeltaError(f"unsafe_source_ref:{ref}")
    lowered = [part.lower() for part in path.parts]
    if any(part in PROHIBITED_COMPONENTS or part == ".env" or part.startswith(".env.") for part in lowered):
        raise HeldLaneEvidenceDeltaError(f"protected_source_ref:{ref}")
    path_tokens: set[str] = set()
    for part in lowered:
        path_tokens.update(part.replace("_", "-").replace(".", "-").split("-"))
    if path_tokens & PROHIBITED_NAME_TOKENS:
        raise HeldLaneEvidenceDeltaError(f"mutation_surface_ref:{ref}")
    if contract:
        if not ref.startswith("docs/registry/") or not ref.endswith(".json"):
            raise HeldLaneEvidenceDeltaError("contract_ref_not_registry_json")
    elif not ref.startswith(ALLOWED_SOURCE_PREFIXES):
        raise HeldLaneEvidenceDeltaError(f"unadmitted_source_ref:{ref}")
    return ref


def _read_source(root: Path, ref: str) -> tuple[bytes, Path]:
    candidate = (root / ref).resolve()
    try:
        candidate.relative_to(root.resolve())
    except ValueError as exc:
        raise HeldLaneEvidenceDeltaError(f"outside_root_source:{ref}") from exc
    if not candidate.is_file():
        raise HeldLaneEvidenceDeltaError(f"missing_source:{ref}")
    return candidate.read_bytes(), candidate


def _load_contract(root: Path, contract_ref: str) -> tuple[dict[str, Any], str]:
    ref = _validate_ref(contract_ref, contract=True)
    raw, _ = _read_source(root, ref)
    try:
        payload = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise HeldLaneEvidenceDeltaError("invalid_contract_json") from exc
    if not isinstance(payload, Mapping):
        raise HeldLaneEvidenceDeltaError("contract_not_object")
    return dict(payload), _sha256(raw)


def _json_path(payload: object, path: Sequence[object]) -> object:
    current = payload
    for part in path:
        if isinstance(current, Mapping) and isinstance(part, str) and part in current:
            current = current[part]
        elif isinstance(current, list) and isinstance(part, int) and 0 <= part < len(current):
            current = current[part]
        else:
            raise KeyError(part)
    return current


def _evaluate_assertion(raw: bytes, assertion: Mapping[str, Any]) -> dict[str, Any]:
    assertion_id = assertion.get("id")
    assertion_type = assertion.get("type")
    if not isinstance(assertion_id, str) or not assertion_id:
        raise HeldLaneEvidenceDeltaError("invalid_assertion_id")
    if assertion_type == "literal":
        value = assertion.get("value")
        if not isinstance(value, str) or not value:
            raise HeldLaneEvidenceDeltaError(f"invalid_literal_assertion:{assertion_id}")
        try:
            actual = raw.decode("utf-8")
        except UnicodeDecodeError as exc:
            raise HeldLaneEvidenceDeltaError(f"invalid_utf8_source:{assertion_id}") from exc
        passed = value in actual
    elif assertion_type == "json_value":
        path = assertion.get("path")
        if not isinstance(path, list) or not path or not all(isinstance(item, (str, int)) for item in path):
            raise HeldLaneEvidenceDeltaError(f"invalid_json_path:{assertion_id}")
        try:
            payload = json.loads(raw.decode("utf-8"))
            actual = _json_path(payload, path)
        except (UnicodeDecodeError, json.JSONDecodeError, KeyError) as exc:
            return {"id": assertion_id, "type": assertion_type, "passed": False, "reason": "json_path_mismatch"}
        passed = actual == assertion.get("equals")
    elif assertion_type == "sha256":
        expected = assertion.get("equals")
        if not isinstance(expected, str) or not expected.startswith("sha256:") or len(expected) != 71:
            raise HeldLaneEvidenceDeltaError(f"invalid_sha256_assertion:{assertion_id}")
        passed = _sha256(raw) == expected
    else:
        raise HeldLaneEvidenceDeltaError(f"unsupported_assertion_type:{assertion_id}")
    return {
        "id": assertion_id,
        "type": assertion_type,
        "passed": passed,
        "reason": "matched" if passed else "assertion_mismatch",
    }


def _validate_contract_shape(contract: Mapping[str, Any]) -> None:
    if contract.get("contract_version") != CONTRACT_VERSION:
        raise HeldLaneEvidenceDeltaError("unsupported_contract_version")
    for field in ("case_id", "marker", "blocker_class"):
        value = contract.get(field)
        if not isinstance(value, str) or not value.strip() or value != value.strip():
            raise HeldLaneEvidenceDeltaError(f"missing_contract_field:{field}")
    if contract.get("expected_decision") not in DECISIONS:
        raise HeldLaneEvidenceDeltaError("invalid_expected_decision")
    required = contract.get("required_evidence_classes")
    evidence = contract.get("evidence")
    if not isinstance(required, list) or not required or not all(isinstance(item, str) and item for item in required):
        raise HeldLaneEvidenceDeltaError("invalid_required_evidence_classes")
    if len(set(required)) != len(required):
        raise HeldLaneEvidenceDeltaError("duplicate_required_evidence_class")
    if not isinstance(evidence, list) or not evidence:
        raise HeldLaneEvidenceDeltaError("invalid_evidence_list")
    held_checkpoint = contract.get("held_checkpoint")
    held_assertions = held_checkpoint.get("assertions") if isinstance(held_checkpoint, Mapping) else None
    if not isinstance(held_assertions, list) or not any(
        isinstance(assertion, Mapping) and assertion.get("type") == "sha256"
        for assertion in held_assertions
    ):
        raise HeldLaneEvidenceDeltaError("held_checkpoint_sha256_required")
    authority = contract.get("authority")
    required_authority = {
        "marker_movement": False,
        "selector_mutation": False,
        "dispatch": False,
        "owner_repo_mutation": False,
        "deploy": False,
        "discord": False,
        "secret_access": False,
        "final_receipt": False,
    }
    if authority != required_authority:
        raise HeldLaneEvidenceDeltaError("authority_guard_drift")


def evaluate_contract(*, root: Path, contract_ref: str) -> dict[str, Any]:
    root = root.resolve()
    contract, contract_digest = _load_contract(root, contract_ref)
    try:
        _validate_contract_shape(contract)
        held = contract.get("held_checkpoint")
        if not isinstance(held, Mapping):
            raise HeldLaneEvidenceDeltaError("invalid_held_checkpoint")
        entries: list[tuple[str, Mapping[str, Any]]] = [("held_checkpoint", held)]
        entries.extend(("evidence", item) for item in contract["evidence"] if isinstance(item, Mapping))
        if len(entries) != len(contract["evidence"]) + 1:
            raise HeldLaneEvidenceDeltaError("non_object_evidence")

        source_digests: dict[str, str] = {contract_ref: contract_digest}
        results: list[dict[str, Any]] = []
        passed_classes: set[str] = set()
        held_checkpoint_ref: str | None = None
        held_checkpoint_digest: str | None = None
        for role, entry in entries:
            evidence_class = entry.get("class")
            if not isinstance(evidence_class, str) or not evidence_class:
                raise HeldLaneEvidenceDeltaError("invalid_evidence_class")
            ref = _validate_ref(entry.get("ref"))
            assertions = entry.get("assertions")
            if not isinstance(assertions, list) or not assertions or not all(isinstance(item, Mapping) for item in assertions):
                raise HeldLaneEvidenceDeltaError(f"invalid_assertions:{ref}")
            raw, _ = _read_source(root, ref)
            source_digest = _sha256(raw)
            source_digests[ref] = source_digest
            if role == "held_checkpoint":
                held_checkpoint_ref = ref
                held_checkpoint_digest = source_digest
            elif ref == held_checkpoint_ref or source_digest == held_checkpoint_digest:
                raise HeldLaneEvidenceDeltaError(f"evidence_not_delta:{ref}")
            assertion_results = [_evaluate_assertion(raw, item) for item in assertions]
            passed = all(item["passed"] for item in assertion_results)
            if role == "evidence" and passed:
                passed_classes.add(evidence_class)
            results.append({
                "role": role,
                "class": evidence_class,
                "ref": ref,
                "passed": passed,
                "assertions": assertion_results,
            })

        required_classes = set(contract["required_evidence_classes"])
        all_assertions_passed = all(item["passed"] for item in results)
        missing_classes = sorted(required_classes - passed_classes)
        decision = "reopen_eligible" if all_assertions_passed and not missing_classes else "still_held"
        expected_decision = contract["expected_decision"]
        receipt_seed = {
            "case_id": contract["case_id"],
            "decision": decision,
            "expected_decision": expected_decision,
            "expectation_met": decision == expected_decision,
            "source_digests": dict(sorted(source_digests.items())),
            "assertions": results,
        }
        receipt_id = "ahd_" + hashlib.sha256(_canonical_json(receipt_seed).encode("utf-8")).hexdigest()[:24]
        return {
            "receipt_version": RECEIPT_VERSION,
            "receipt_id": receipt_id,
            "case_id": contract["case_id"],
            "subject": contract["marker"],
            "blocker_class": contract["blocker_class"],
            "held_checkpoint_ref": held_checkpoint_ref,
            "held_checkpoint_digest": held_checkpoint_digest,
            "decision": decision,
            "expected_decision": expected_decision,
            "expectation_met": decision == expected_decision,
            "required_evidence_classes": sorted(required_classes),
            "passed_evidence_classes": sorted(passed_classes),
            "missing_evidence_classes": missing_classes,
            "source_digests": dict(sorted(source_digests.items())),
            "evidence_results": results,
            "authority_actions": [],
            "advisory_only": True,
        }
    except HeldLaneEvidenceDeltaError as exc:
        receipt_seed = {"case_id": contract.get("case_id"), "decision": "blocked", "blocker": str(exc), "contract_digest": contract_digest}
        return {
            "receipt_version": RECEIPT_VERSION,
            "receipt_id": "ahd_" + hashlib.sha256(_canonical_json(receipt_seed).encode("utf-8")).hexdigest()[:24],
            "case_id": contract.get("case_id"),
            "subject": contract.get("marker"),
            "blocker_class": contract.get("blocker_class"),
            "held_checkpoint_ref": (
                contract.get("held_checkpoint", {}).get("ref")
                if isinstance(contract.get("held_checkpoint"), Mapping)
                else None
            ),
            "decision": "blocked",
            "blockers": [str(exc)],
            "source_digests": {contract_ref: contract_digest},
            "authority_actions": [],
            "advisory_only": True,
        }


def _validate_output_ref(output_ref: str) -> str:
    if "\\" in output_ref:
        raise HeldLaneEvidenceDeltaError("invalid_output_ref")
    path = PurePosixPath(output_ref)
    if path.is_absolute() or ".." in path.parts or output_ref != path.as_posix():
        raise HeldLaneEvidenceDeltaError("unsafe_output_ref")
    if not output_ref.startswith("tmp/atlas/") or path.suffix != ".json":
        raise HeldLaneEvidenceDeltaError("output_not_tmp_atlas_json")
    return output_ref


def write_output(*, root: Path, output_ref: str, receipt: Mapping[str, Any]) -> None:
    ref = _validate_output_ref(output_ref)
    target = (root.resolve() / ref).resolve()
    try:
        target.relative_to(root.resolve() / "tmp" / "atlas")
    except ValueError as exc:
        raise HeldLaneEvidenceDeltaError("outside_output_root") from exc
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(receipt, indent=2, ensure_ascii=True) + "\n", encoding="utf-8", newline="\n")


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Resolve source-bound evidence deltas for held ATLAS lanes.")
    parser.add_argument("--root", default=str(atlas_root()))
    parser.add_argument("--contract", required=True)
    parser.add_argument("--output")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    root = Path(args.root)
    try:
        receipt = evaluate_contract(root=root, contract_ref=args.contract)
        if args.output:
            write_output(root=root, output_ref=args.output, receipt=receipt)
    except HeldLaneEvidenceDeltaError as exc:
        print(json.dumps({"decision": "blocked", "blockers": [str(exc)]}, indent=2))
        return 2
    print(json.dumps(receipt, indent=2))
    return 0 if receipt["decision"] == "reopen_eligible" else (1 if receipt["decision"] == "still_held" else 2)


if __name__ == "__main__":
    raise SystemExit(main())
