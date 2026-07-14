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


SCHEMA_VERSION = "atlas.cortex.simulation.agent-state.v1"
STATUS_OK = "ok"
STATUS_ADVISORY = "advisory_gap"
STATUS_BLOCKER = "blocker"
INPUT_PREFIX = "data/cortex/simulation-fixtures/"
OUTPUT_PREFIX = "tmp/atlas/"
ALLOWED_FIXTURE_FIELDS = {
    "scenario_id",
    "agent_id",
    "generated_at",
    "objective",
    "minimum_confidence",
    "scoring",
    "observations",
}
ALLOWED_OBSERVATION_FIELDS = {
    "observed_at",
    "content_summary",
    "source_ref",
    "source_digest",
    "importance",
    "confidence",
    "retention_class",
    "rights_class",
    "privacy_class",
    "injection_state",
}


def _canonical_json(value: object) -> str:
    return json.dumps(value, ensure_ascii=True, sort_keys=True, separators=(",", ":"))


def _stable_id(value: object) -> str:
    return "sha256:" + hashlib.sha256(_canonical_json(value).encode("utf-8")).hexdigest()


def _finding(code: str, message: str, **details: object) -> OrderedDict[str, object]:
    finding: OrderedDict[str, object] = OrderedDict([("code", code), ("message", message)])
    if details:
        finding["details"] = OrderedDict(sorted(details.items()))
    return finding


def _normalize_path(root: Path, candidate: str, *, prefix: str) -> tuple[str | None, OrderedDict[str, object] | None]:
    value = Path(candidate)
    if value.is_absolute():
        return None, _finding("absolute_path_forbidden", "Path must be root-relative.", path=normalize_slashes(candidate))
    ref = normalize_slashes(candidate).strip("/")
    if not ref or ref.startswith("../") or "/../" in f"/{ref}/":
        return None, _finding("path_traversal_forbidden", "Path must remain inside the admitted root prefix.", path=ref)
    if not ref.startswith(prefix) or not ref.endswith(".json"):
        return None, _finding("path_not_admitted", "Path is outside the admitted JSON prefix.", path=ref, prefix=prefix)
    resolved = (root / ref).resolve()
    try:
        resolved.relative_to(root.resolve())
    except ValueError:
        return None, _finding("outside_root_forbidden", "Path resolves outside the ATLAS root.", path=ref)
    return ref, None


def _number(value: object, field: str, blockers: list[OrderedDict[str, object]]) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not 0 <= float(value) <= 1:
        blockers.append(_finding("invalid_score", "Score must be a number from 0 to 1.", field=field))
        return 0.0
    return float(value)


def _is_admitted_fixture_ref(value: object) -> bool:
    if not isinstance(value, str) or not value.strip():
        return False
    candidate = Path(value)
    ref = normalize_slashes(value).strip("/")
    return (
        not candidate.is_absolute()
        and not ref.startswith("../")
        and "/../" not in f"/{ref}/"
        and ref.startswith(INPUT_PREFIX)
        and ref.endswith(".json")
    )


def _validate_fixture(payload: object) -> tuple[dict[str, Any] | None, list[OrderedDict[str, object]]]:
    blockers: list[OrderedDict[str, object]] = []
    if not isinstance(payload, dict):
        return None, [_finding("fixture_not_object", "Fixture must be a JSON object.")]
    unknown = sorted(set(payload) - ALLOWED_FIXTURE_FIELDS)
    if unknown:
        blockers.append(_finding("unknown_fixture_fields", "Fixture contains unadmitted fields.", fields=unknown))
    for field in ("scenario_id", "agent_id", "generated_at", "objective"):
        if not isinstance(payload.get(field), str) or not payload[field].strip():
            blockers.append(_finding("required_field_missing", "Required fixture field is missing or empty.", field=field))
    observations = payload.get("observations")
    if not isinstance(observations, list):
        blockers.append(_finding("observations_not_array", "Observations must be an array."))
        observations = []
    for index, observation in enumerate(observations):
        if not isinstance(observation, dict):
            blockers.append(_finding("observation_not_object", "Observation must be an object.", index=index))
            continue
        unknown_observation = sorted(set(observation) - ALLOWED_OBSERVATION_FIELDS)
        if unknown_observation:
            blockers.append(
                _finding("unknown_observation_fields", "Observation contains unadmitted fields.", index=index, fields=unknown_observation)
            )
        for field in ("observed_at", "content_summary", "source_ref", "source_digest"):
            if not isinstance(observation.get(field), str) or not observation[field].strip():
                blockers.append(_finding("observation_field_missing", "Observation field is missing or empty.", index=index, field=field))
        if not _is_admitted_fixture_ref(observation.get("source_ref")):
            blockers.append(
                _finding(
                    "source_ref_not_admitted",
                    "Observation source reference must remain inside the synthetic-fixture boundary.",
                    index=index,
                )
            )
        if isinstance(observation.get("source_digest"), str) and not (
            observation["source_digest"].startswith("sha256:") and len(observation["source_digest"]) == 71
        ):
            blockers.append(_finding("invalid_source_digest", "Observation source digest must be sha256-prefixed.", index=index))
        _number(observation.get("importance"), f"observations[{index}].importance", blockers)
        _number(observation.get("confidence"), f"observations[{index}].confidence", blockers)
        if observation.get("retention_class") not in {"ephemeral", "session", "project", "durable"}:
            blockers.append(_finding("invalid_retention_class", "Observation retention class is invalid.", index=index))
        if observation.get("rights_class") not in {"synthetic", "operator_owned", "authorized_external"}:
            blockers.append(_finding("rights_not_admitted", "Observation rights are unknown or blocked.", index=index))
        if observation.get("privacy_class") not in {"public", "internal"}:
            blockers.append(_finding("privacy_not_admitted", "Observation privacy class is prohibited.", index=index))
        if observation.get("injection_state") not in {"trusted", "neutralized"}:
            blockers.append(_finding("injection_not_admitted", "Observation injection state is rejected.", index=index))
    _number(payload.get("minimum_confidence", 0.5), "minimum_confidence", blockers)
    scoring = payload.get("scoring", {"recency_weight": 0.3, "importance_weight": 0.3, "relevance_weight": 0.4})
    if not isinstance(scoring, dict) or set(scoring) != {"recency_weight", "importance_weight", "relevance_weight"}:
        blockers.append(_finding("invalid_scoring", "Scoring must contain exactly recency, importance, and relevance weights."))
    else:
        weights = [
            _number(scoring.get(field), f"scoring.{field}", blockers)
            for field in ("recency_weight", "importance_weight", "relevance_weight")
        ]
        if abs(sum(weights) - 1.0) > 1e-9:
            blockers.append(_finding("invalid_scoring_total", "Scoring weights must sum to 1."))
    return payload, blockers


def build_state(*, fixture: dict[str, Any], input_ref: str) -> OrderedDict[str, object]:
    minimum_confidence = float(fixture.get("minimum_confidence", 0.5))
    scoring = fixture.get("scoring", {"recency_weight": 0.3, "importance_weight": 0.3, "relevance_weight": 0.4})
    memories: list[OrderedDict[str, object]] = []
    for observation in fixture["observations"]:
        memory_basis = OrderedDict(
            [
                ("scenario_id", fixture["scenario_id"]),
                ("agent_id", fixture["agent_id"]),
                ("observed_at", observation["observed_at"]),
                ("content_summary", observation["content_summary"]),
                ("source_ref", observation["source_ref"]),
                ("source_digest", observation["source_digest"]),
            ]
        )
        memories.append(
            OrderedDict(
                [
                    ("memory_id", _stable_id(memory_basis)),
                    ("observed_at", observation["observed_at"]),
                    ("content_summary", observation["content_summary"]),
                    ("source_refs", [observation["source_ref"]]),
                    ("source_digest", observation["source_digest"]),
                    ("importance", float(observation["importance"])),
                    ("confidence", float(observation["confidence"])),
                    ("retention_class", observation["retention_class"]),
                    ("rights_class", observation["rights_class"]),
                    ("privacy_class", observation["privacy_class"]),
                    ("injection_state", observation["injection_state"]),
                    ("supersedes", []),
                ]
            )
        )
    memories.sort(key=lambda item: str(item["memory_id"]))
    candidate_ids = [str(item["memory_id"]) for item in memories]
    selected = [item for item in memories if float(item["confidence"]) >= minimum_confidence]
    selected_ids = [str(item["memory_id"]) for item in selected]
    excluded = [
        OrderedDict([("memory_id", item["memory_id"]), ("reason", "below_confidence")])
        for item in memories
        if float(item["confidence"]) < minimum_confidence
    ]
    source_refs = sorted({input_ref, *(str(item["source_refs"][0]) for item in memories)})
    reflections: list[OrderedDict[str, object]] = []
    active_plan: OrderedDict[str, object] | None = None
    if selected:
        reflection_basis = OrderedDict(
            [
                ("scenario_id", fixture["scenario_id"]),
                ("agent_id", fixture["agent_id"]),
                ("source_memory_ids", selected_ids),
                ("objective", fixture["objective"]),
            ]
        )
        reflection_id = _stable_id(reflection_basis)
        reflections.append(
            OrderedDict(
                [
                    ("reflection_id", reflection_id),
                    ("generated_at", fixture["generated_at"]),
                    ("trigger", "replay_checkpoint"),
                    ("source_memory_ids", selected_ids),
                    ("summary", f"Derived from {len(selected_ids)} admitted memories for objective: {fixture['objective']}"),
                    ("confidence", min(float(item["confidence"]) for item in selected)),
                    ("source_refs", source_refs),
                    ("derived_not_observed", True),
                    ("approval_state", "advisory_only"),
                    ("retention_class", "project"),
                ]
            )
        )
        plan_basis = OrderedDict(
            [
                ("scenario_id", fixture["scenario_id"]),
                ("agent_id", fixture["agent_id"]),
                ("reflection_id", reflection_id),
                ("objective", fixture["objective"]),
            ]
        )
        active_plan = OrderedDict(
            [
                ("plan_id", _stable_id(plan_basis)),
                ("objective", fixture["objective"]),
                ("status", "candidate"),
                ("source_memory_ids", selected_ids),
                ("source_reflection_ids", [reflection_id]),
                (
                    "steps",
                    [
                        OrderedDict(
                            [
                                ("step_id", "step-1"),
                                ("objective", "Review the advisory scenario projection."),
                                ("state", "ready"),
                                ("proposed_action", "Return the projection for operator review without execution."),
                                ("evidence_required", source_refs),
                                ("authority_check", "advisory_only"),
                            ]
                        )
                    ],
                ),
                ("success_criteria", ["operator receives schema-valid advisory state"]),
                ("termination_reason", None),
                ("confidence", min(float(item["confidence"]) for item in selected)),
                ("execution_authorized", False),
            ]
        )
    state_without_id = OrderedDict(
        [
            ("contract_version", SCHEMA_VERSION),
            ("scenario_id", fixture["scenario_id"]),
            ("agent_id", fixture["agent_id"]),
            ("generated_at", fixture["generated_at"]),
            ("source_refs", source_refs),
            ("memories", memories),
            (
                "retrieval_context",
                OrderedDict(
                    [
                        ("query_summary", fixture["objective"]),
                        ("candidate_memory_ids", candidate_ids),
                        ("selected_memory_ids", selected_ids),
                        (
                            "scoring",
                            OrderedDict(
                                [
                                    ("recency_weight", float(scoring["recency_weight"])),
                                    ("importance_weight", float(scoring["importance_weight"])),
                                    ("relevance_weight", float(scoring["relevance_weight"])),
                                ]
                            ),
                        ),
                        ("minimum_confidence", minimum_confidence),
                        ("deterministic_tiebreaker", "score_desc_then_memory_id_asc"),
                        ("excluded", excluded),
                    ]
                ),
            ),
            ("reflections", reflections),
            ("active_plan", active_plan),
            (
                "authority",
                OrderedDict(
                    [
                        ("advisory_only", True),
                        ("execution_authorized", False),
                        ("owner_repo_mutation_authorized", False),
                        ("platform_mutation_authorized", False),
                        ("discord_write_authorized", False),
                        ("marker_movement_authorized", False),
                    ]
                ),
            ),
        ]
    )
    return OrderedDict(
        [
            ("contract_version", SCHEMA_VERSION),
            ("state_id", _stable_id(state_without_id)),
            *[(key, value) for key, value in state_without_id.items() if key != "contract_version"],
        ]
    )


def run(*, root: Path, input_path: str, output_path: str | None) -> tuple[OrderedDict[str, object], int]:
    input_ref, input_error = _normalize_path(root, input_path, prefix=INPUT_PREFIX)
    output_ref: str | None = None
    output_error: OrderedDict[str, object] | None = None
    if output_path is not None:
        output_ref, output_error = _normalize_path(root, output_path, prefix=OUTPUT_PREFIX)
    blockers = [item for item in (input_error, output_error) if item is not None]
    fixture: dict[str, Any] | None = None
    if not blockers and input_ref is not None:
        try:
            fixture_payload = json.loads((root / input_ref).read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            blockers.append(_finding("fixture_read_failed", "Fixture could not be read as JSON.", error=str(exc)))
        else:
            fixture, fixture_blockers = _validate_fixture(fixture_payload)
            blockers.extend(fixture_blockers)
    state = build_state(fixture=fixture, input_ref=input_ref) if fixture is not None and not blockers and input_ref is not None else None
    status = STATUS_BLOCKER if blockers else (STATUS_OK if state and state["memories"] else STATUS_ADVISORY)
    result: OrderedDict[str, object] = OrderedDict(
        [
            ("status", status),
            ("safe_to_use", status == STATUS_OK),
            ("input_ref", input_ref),
            ("output_ref", output_ref),
            ("state", state),
            ("warnings", [] if status != STATUS_ADVISORY else [_finding("no_observations", "Fixture produced no memories.")]),
            ("blockers", blockers),
        ]
    )
    if output_ref is not None and not blockers:
        destination = root / output_ref
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(json.dumps(state, ensure_ascii=True, indent=2) + "\n", encoding="utf-8")
    return result, 0 if status == STATUS_OK else 1


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build deterministic read-only Cortex scenario state from a synthetic fixture.")
    parser.add_argument("--input", required=True)
    parser.add_argument("--output")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--strict", action="store_true")
    args = parser.parse_args(argv)
    result, exit_code = run(root=atlas_root(), input_path=args.input, output_path=args.output)
    print(json.dumps(result, ensure_ascii=True, indent=2))
    return exit_code if args.strict else (1 if result["status"] == STATUS_BLOCKER else 0)


if __name__ == "__main__":
    raise SystemExit(main())
