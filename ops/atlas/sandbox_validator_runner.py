from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from collections.abc import Mapping
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from ops._atlas import atlas_root


SCENARIO_ID = "local-only-example-stub"
VALIDATOR_ID = "local-only-example-stub-validator-001"
SCENARIO_REF = "data/atlas/sandbox/scenarios/local-only-example-stub.json"
FIXTURE_PACK_REF = "data/atlas/sandbox/fixtures/local-only-example-stub/fixture-pack.json"
VALIDATOR_REF = "data/atlas/sandbox/validators/local-only-example-stub/validator.json"
RUNNER_REF = "ops/atlas/sandbox_validator_runner.py"
NOTE_REF = "data/atlas/sandbox/fixtures/local-only-example-stub/notes/first-note-stub.md"
INPUT_REF = "data/atlas/sandbox/fixtures/local-only-example-stub/inputs/first-input-stub.json"
ORACLE_REF = "data/atlas/sandbox/fixtures/local-only-example-stub/expected-output/first-expected-output-stub.json"
RUNTIME_PREFIX = f"runtime/atlas/sandbox/runs/{SCENARIO_ID}/"
RUN_ID_PATTERN = re.compile(r"^[a-z0-9][a-z0-9-]{2,79}$")
REQUIRED_CONSTRAINTS = (
    "no owner-repo mutation",
    "no deploy mutation",
    "no secret use",
    "no live-data mutation",
)
COMPARISON_FIELDS = ("payload.mode", "payload.status", "payload.observations")
AUTHORITY_GUARD_KEYS = (
    "owner_repo_mutation",
    "deploy_mutation",
    "secret_use",
    "live_data_mutation",
    "_stack_execution",
)


class SandboxValidatorRunError(RuntimeError):
    pass


def _canonical_json(payload: Mapping[str, Any]) -> str:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def _digest_bytes(value: bytes) -> str:
    return "sha256:" + hashlib.sha256(value).hexdigest()


def _digest_payload(payload: Mapping[str, Any]) -> str:
    return _digest_bytes(_canonical_json(payload).encode("utf-8"))


def _load_mapping(root: Path, ref: str) -> tuple[dict[str, Any], str]:
    candidate = (root / ref).resolve()
    try:
        candidate.relative_to(root.resolve())
    except ValueError as exc:
        raise SandboxValidatorRunError(f"outside_root_source:{ref}") from exc
    if not candidate.is_file():
        raise SandboxValidatorRunError(f"missing_source:{ref}")
    raw = candidate.read_bytes()
    try:
        payload = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise SandboxValidatorRunError(f"invalid_json_source:{ref}") from exc
    if not isinstance(payload, Mapping):
        raise SandboxValidatorRunError(f"non_object_source:{ref}")
    return dict(payload), _digest_bytes(raw)


def _load_text(root: Path, ref: str) -> tuple[str, str]:
    candidate = (root / ref).resolve()
    try:
        candidate.relative_to(root.resolve())
    except ValueError as exc:
        raise SandboxValidatorRunError(f"outside_root_source:{ref}") from exc
    if not candidate.is_file():
        raise SandboxValidatorRunError(f"missing_source:{ref}")
    raw = candidate.read_bytes()
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise SandboxValidatorRunError(f"invalid_utf8_source:{ref}") from exc
    return text, _digest_bytes(raw)


def _require_false_guards(payload: Mapping[str, Any], source: str) -> None:
    guards = payload.get("guards")
    if not isinstance(guards, Mapping) or set(guards) != set(AUTHORITY_GUARD_KEYS):
        raise SandboxValidatorRunError(f"{source}_guard_shape_drift")
    if any(guards.get(key) is not False for key in AUTHORITY_GUARD_KEYS):
        raise SandboxValidatorRunError(f"{source}_guard_drift")


def _require_identity(
    scenario: Mapping[str, Any],
    fixture_pack: Mapping[str, Any],
    validator: Mapping[str, Any],
    input_fixture: Mapping[str, Any],
    oracle: Mapping[str, Any],
    note_text: str,
) -> None:
    if scenario.get("scenario_id") != SCENARIO_ID or scenario.get("status") != "active":
        raise SandboxValidatorRunError("scenario_not_active")
    _require_false_guards(scenario, "scenario")
    if scenario.get("fixture_refs") != [FIXTURE_PACK_REF]:
        raise SandboxValidatorRunError("scenario_fixture_ref_drift")
    if fixture_pack.get("scenario_id") != SCENARIO_ID or fixture_pack.get("status") != "active":
        raise SandboxValidatorRunError("fixture_pack_not_active")
    _require_false_guards(fixture_pack, "fixture_pack")
    expected_items = [
        ("local-only-example-stub-note-001", "note", NOTE_REF),
        ("local-only-example-stub-input-001", "input", INPUT_REF),
        ("local-only-example-stub-expected-output-001", "expected_output", ORACLE_REF),
    ]
    items = fixture_pack.get("items")
    if not isinstance(items, list) or not all(isinstance(item, Mapping) for item in items) or [
        (item.get("fixture_id"), item.get("kind"), item.get("path"))
        for item in items
    ] != expected_items:
        raise SandboxValidatorRunError("fixture_pack_member_drift")
    if validator.get("validator_id") != VALIDATOR_ID or validator.get("scenario_id") != SCENARIO_ID:
        raise SandboxValidatorRunError("validator_identity_mismatch")
    if validator.get("status") != "active":
        raise SandboxValidatorRunError("validator_not_active")
    _require_false_guards(validator, "validator")
    reads = validator.get("reads")
    if not isinstance(reads, Mapping) or reads.get("scenario_ref") != SCENARIO_REF or reads.get("fixture_pack_ref") != FIXTURE_PACK_REF:
        raise SandboxValidatorRunError("validator_read_graph_drift")
    if reads.get("allowed_kinds") != ["note", "input", "expected_output"]:
        raise SandboxValidatorRunError("validator_allowed_kinds_drift")
    expected_fixture_ids = {
        "input": "local-only-example-stub-input-001",
        "oracle": "local-only-example-stub-expected-output-001",
    }
    for name, payload in (("input", input_fixture), ("oracle", oracle)):
        if payload.get("scenario_id") != SCENARIO_ID:
            raise SandboxValidatorRunError(f"{name}_scenario_identity_mismatch")
        if payload.get("fixture_id") != expected_fixture_ids[name]:
            raise SandboxValidatorRunError(f"{name}_fixture_identity_mismatch")
    if "deterministic local-only validator" not in note_text:
        raise SandboxValidatorRunError("fixture_note_stale")


def _candidate_payload(input_fixture: Mapping[str, Any]) -> dict[str, Any]:
    payload = input_fixture.get("payload")
    if not isinstance(payload, Mapping):
        raise SandboxValidatorRunError("input_payload_missing")
    constraints = payload.get("constraints")
    if not isinstance(constraints, list) or tuple(constraints) != REQUIRED_CONSTRAINTS:
        raise SandboxValidatorRunError("input_constraint_drift")
    if payload.get("mode") != "stub":
        raise SandboxValidatorRunError("input_mode_drift")
    return {
        "mode": "local_only",
        "status": "validated",
        "observations": [
            "local-only sandbox input accepted",
            "all no-mutation constraints preserved",
        ],
    }


def _oracle_payload(oracle: Mapping[str, Any]) -> dict[str, Any]:
    payload = oracle.get("payload")
    if not isinstance(payload, Mapping):
        raise SandboxValidatorRunError("oracle_payload_missing")
    observations = payload.get("observations")
    if not isinstance(observations, list) or not all(isinstance(item, str) for item in observations):
        raise SandboxValidatorRunError("oracle_observations_invalid")
    return {
        "mode": payload.get("mode"),
        "status": payload.get("status"),
        "observations": observations,
    }


def _write_idempotent(path: Path, payload: Mapping[str, Any]) -> None:
    rendered = json.dumps(payload, indent=2, ensure_ascii=True) + "\n"
    if path.exists():
        if path.read_text(encoding="utf-8") != rendered:
            raise SandboxValidatorRunError(f"existing_artifact_conflict:{path.name}")
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(rendered, encoding="utf-8", newline="\n")


def run_sandbox_validator(*, root: Path, run_id: str) -> dict[str, Any]:
    root = root.resolve()
    if not RUN_ID_PATTERN.fullmatch(run_id):
        raise SandboxValidatorRunError("invalid_run_id")

    scenario, scenario_digest = _load_mapping(root, SCENARIO_REF)
    fixture_pack, fixture_pack_digest = _load_mapping(root, FIXTURE_PACK_REF)
    validator, validator_digest = _load_mapping(root, VALIDATOR_REF)
    note_text, note_digest = _load_text(root, NOTE_REF)
    input_fixture, input_digest = _load_mapping(root, INPUT_REF)
    oracle, oracle_digest = _load_mapping(root, ORACLE_REF)
    _, runner_digest = _load_text(root, RUNNER_REF)
    _require_identity(scenario, fixture_pack, validator, input_fixture, oracle, note_text)

    candidate_boundary = _candidate_payload(input_fixture)
    expected_boundary = _oracle_payload(oracle)
    outcome = "equal_on_boundary" if candidate_boundary == expected_boundary else "unequal_on_boundary"
    terminal_status = "passed" if outcome == "equal_on_boundary" else "failed"
    source_digests = {
        "scenario": scenario_digest,
        "fixture_pack": fixture_pack_digest,
        "validator": validator_digest,
        "note": note_digest,
        "input": input_digest,
        "oracle": oracle_digest,
        "runner": runner_digest,
    }
    receipt_seed = {
        "scenario_id": SCENARIO_ID,
        "validator_id": VALIDATOR_ID,
        "run_id": run_id,
        "outcome": outcome,
        "source_digests": source_digests,
    }
    receipt_id = "asv_" + hashlib.sha256(_canonical_json(receipt_seed).encode("utf-8")).hexdigest()[:24]

    candidate = {
        "contract_version": "atlas.sandbox.validator-candidate-output.v2",
        "validator_id": VALIDATOR_ID,
        "scenario_id": SCENARIO_ID,
        "run_id": run_id,
        "validator_ref": VALIDATOR_REF,
        "source_input_fixture_id": input_fixture.get("fixture_id"),
        "source_input_ref": INPUT_REF,
        "oracle_ref": ORACLE_REF,
        "payload": candidate_boundary,
        "source_digests": source_digests,
    }
    report = {
        "contract_version": "atlas.sandbox.validation-report.v2",
        "validator_id": VALIDATOR_ID,
        "scenario_id": SCENARIO_ID,
        "run_id": run_id,
        "validator_ref": VALIDATOR_REF,
        "result": {
            "status": terminal_status,
            "summary": "Bounded local-only validator completed without external or owner-repository mutation.",
        },
        "compared_fixture_ids": [input_fixture.get("fixture_id"), oracle.get("fixture_id")],
        "compared_fields": list(COMPARISON_FIELDS),
        "comparison_outcome": outcome,
        "source_digests": source_digests,
        "authority_actions": [],
        "guards": {
            "owner_repo_mutation": False,
            "deploy_mutation": False,
            "secret_use": False,
            "live_data_mutation": False,
            "_stack_execution": False,
            "external_network": False,
        },
        "receipt_id": receipt_id,
    }

    validation_dir = root / RUNTIME_PREFIX / run_id / "validation"
    _write_idempotent(validation_dir / "candidate-output.json", candidate)
    _write_idempotent(validation_dir / "report.json", report)
    return report


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the bounded ATLAS local-only Sandbox validator.")
    parser.add_argument("--root", default=str(atlas_root()))
    parser.add_argument("--run-id", required=True)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        report = run_sandbox_validator(root=Path(args.root), run_id=args.run_id)
    except SandboxValidatorRunError as exc:
        print(json.dumps({"status": "blocked", "blocker": str(exc)}, indent=2))
        return 1
    print(json.dumps(report, indent=2))
    return 0 if report["result"]["status"] == "passed" else 2


if __name__ == "__main__":
    raise SystemExit(main())
