from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from collections import OrderedDict
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from ops._atlas import atlas_root, normalize_slashes

SCHEMA_VERSION = "atlas.cortex.simulation_substrate_requirements.v1"
STATUS_OK = "ok"
STATUS_ADVISORY = "advisory_gap"
STATUS_BLOCKER = "blocker"
STATUS_INTERNAL_ERROR = "internal_error"

DEFAULT_SOURCE_REFS = (
    "AGENTS.md",
    "docs/PLAYBOOK_NOTES.md",
    "docs/atlas-book/05-receipt-index.md",
    "docs/memory/profiles/zachariah_workflow_profile.md",
    "docs/ops/ATLAS-ROOT-OPERATOR-RESELECTION-TO-CORTEX-SIMULATION-SUBSTRATE-2026-07-09.md",
    "docs/ops/CORTEX-DUAL-MODE-AND-SIMULATION-SUBSTRATE-MARKER-ADMISSION-2026-07-09.md",
    "docs/ops/CORTEX-SIMULATION-SUBSTRATE-READINESS-FABLE-GENERATIVE-AGENT-RESEARCH-CONTRACT-FREEZE-2026-07-09.md",
    "docs/ops/CORTEX-SIMULATION-SUBSTRATE-READINESS-SIMULATION-REQUIREMENTS-MAP-FIRST-IMPLEMENTATION-ADMISSION-2026-07-09.md",
    "docs/ops/CORTEX-SIMULATION-SUBSTRATE-READINESS-SIMULATION-REQUIREMENTS-MAP-PROMPT-PACK-AND-WORKER-HANDOFF-CONTRACT-2026-07-10.md",
)
ALLOWED_EXACT_SOURCE_REFS = set(DEFAULT_SOURCE_REFS)
CORE_REQUIRED_SOURCE_REFS = {
    "AGENTS.md",
    "docs/memory/profiles/zachariah_workflow_profile.md",
    "docs/ops/CORTEX-SIMULATION-SUBSTRATE-READINESS-FABLE-GENERATIVE-AGENT-RESEARCH-CONTRACT-FREEZE-2026-07-09.md",
    "docs/ops/CORTEX-SIMULATION-SUBSTRATE-READINESS-SIMULATION-REQUIREMENTS-MAP-FIRST-IMPLEMENTATION-ADMISSION-2026-07-09.md",
    "docs/ops/CORTEX-SIMULATION-SUBSTRATE-READINESS-SIMULATION-REQUIREMENTS-MAP-PROMPT-PACK-AND-WORKER-HANDOFF-CONTRACT-2026-07-10.md",
}
SUPPORTING_SOURCE_REFS = {
    "docs/PLAYBOOK_NOTES.md",
    "docs/atlas-book/05-receipt-index.md",
    "docs/ops/ATLAS-ROOT-OPERATOR-RESELECTION-TO-CORTEX-SIMULATION-SUBSTRATE-2026-07-09.md",
    "docs/ops/CORTEX-DUAL-MODE-AND-SIMULATION-SUBSTRATE-MARKER-ADMISSION-2026-07-09.md",
}
PROTECTED_PREFIXES = (
    ".github/workflows",
    ".playwright-mcp",
    ".vercel",
    "archive",
    "repos",
    "secrets",
)
DEPLOY_OR_PLATFORM_PREFIXES = (
    "deploy",
    "deployment",
    "platform",
    "supabase",
    "vercel",
)
HIDDEN_CONTEXT_PREFIXES = (
    ".codex",
    "runtime/chats",
    "runtime/session",
    "runtime/sessions",
    "runtime/transcripts",
    "runtime/atlas/conversations",
    "runtime/atlas/sessions",
    "tmp/chats",
    "tmp/transcripts",
)
AUTHORITY_DENIALS = (
    "simulation-execution",
    "agent-execution",
    "owner-repo-mutation",
    "platform-mutation",
    "deploy",
    "secret-handling",
    "workflow-dispatch",
    "final-receipt",
    "marker-movement",
    "hidden-transcript-ingestion",
    "model-training",
    "media-generation",
)
FORBIDDEN_DATA_SURFACES = (
    "hidden transcripts",
    "secret-bearing exports",
    ".env*",
    "raw live user data by default",
    "unauthorized copyrighted character or story assets",
    "unbounded scraped conversation archives",
    "owner-repo private drift treated as canonical simulation truth",
)
SIMULATION_GROUPS = (
    (
        "scenario",
        "scenario",
        "Govern the scenario envelope, inputs, objectives, and packet context for rehearsal.",
        ("scenario substrate", "`scenario`", "model scenarios"),
        ("scenario_id", "objective", "constraints", "proof_basis"),
    ),
    (
        "agent",
        "agent",
        "Model governed agent roles, boundaries, and collaborator-aware behavior.",
        ("agent substrate", "`agent`", "collaborator-aware planning"),
        ("agent_id", "role", "authority_boundary", "memory_refs"),
    ),
    (
        "world_state",
        "world_state",
        "Represent stack, lane, and platform state as replayable simulation context.",
        ("world-state substrate", "`world_state`", "current state"),
        ("state_id", "marker_state", "repo_state", "platform_state"),
    ),
    (
        "memory",
        "memory",
        "Capture governed memory of prior experience without hidden transcript ingestion.",
        ("`memory`", "memory of prior experience"),
        ("memory_id", "summary", "source_refs", "retention_policy"),
    ),
    (
        "reflection",
        "reflection",
        "Record reflection over prior outcomes and blocked progress.",
        ("`reflection`", "reflection over that experience"),
        ("reflection_id", "observation_refs", "assessment", "follow_on_constraints"),
    ),
    (
        "plan",
        "plan",
        "Model plan candidates against current state and denied authority boundaries.",
        ("`plan`", "planning against current state", "evaluate candidate plans"),
        ("plan_id", "inputs", "steps", "success_criteria"),
    ),
    (
        "action",
        "action",
        "Represent bounded proposed actions without executing them.",
        ("`action`", "sandboxed interaction among agents"),
        ("action_id", "proposed_change", "authority_check", "proof_required"),
    ),
    (
        "observation",
        "observation",
        "Carry replayable observations and evidence gathered from admitted sources.",
        ("`observation`", "proof availability"),
        ("observation_id", "event", "source_refs", "confidence"),
    ),
    (
        "evaluation",
        "evaluation",
        "Score candidate plans and replay outcomes against explicit criteria.",
        ("replay and evaluation substrate", "`evaluation`", "evaluate candidate plans"),
        ("evaluation_id", "criteria", "result", "proof_refs"),
    ),
    (
        "safety_boundary",
        "safety_boundary",
        "Make denied authority and forbidden surfaces first-class simulation constraints.",
        ("`safety_boundary`", "forbidden authority", "explicit denied authority"),
        ("boundary_id", "forbidden_surface", "forbidden_authority", "escalation_rule"),
    ),
    (
        "proof_reference",
        "proof_reference",
        "Reference receipts, manifests, and doctrine as canonical replay and proof inputs.",
        ("`proof_reference`", "ATLAS receipts", "continuity manifests"),
        ("proof_id", "source_ref", "digest", "replay_class"),
    ),
)
RECONCILIATION_PACKET = (
    "Cortex Simulation Substrate Readiness simulation requirements map first-implementation worker cluster reconciliation"
)
ADMITTED_DATA_SURFACES = (
    "ATLAS receipts",
    "ATLAS Book restart surfaces",
    "continuity manifests",
    "stack inventory",
    "explicit doctrine contracts",
    "future synthetic or fixture-backed scenario inputs",
)
ADMITTED_AUTHORITY = (
    "read admitted root-owned doctrine and receipts",
    "classify simulation substrate requirements deterministically",
    "report gaps, warnings, blockers, and deferred adapters explicitly",
    "write advisory JSON only to explicit safe tmp/**.json outputs",
)
ETHICAL_RISKS = (
    "synthetic-human misrepresentation",
    "authority creep from scenario reasoning into execution",
    "data-governance drift",
    "prompt injection through ungoverned inputs",
    "false confidence from plausible but unverified simulated outcomes",
)
IP_RIGHTS_RISKS = (
    "unauthorized IP generation",
    "unauthorized copyrighted character or story assets",
)
PRIVACY_RISKS = (
    "hidden transcript ingestion",
    "raw live user data exposure",
    "secret-bearing export leakage",
)


def _finding(code: str, message: str, **details: Any) -> OrderedDict[str, Any]:
    payload: OrderedDict[str, Any] = OrderedDict([("code", code), ("message", message)])
    if details:
        payload["details"] = details
    return payload


def _git_stdout(root: Path, *args: str) -> str | None:
    completed = subprocess.run(
        ["git", "-C", str(root), *args],
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    if completed.returncode != 0:
        return None
    return completed.stdout.strip()


def collect_git_state(root: Path) -> tuple[str | None, str | None]:
    return _git_stdout(root, "branch", "--show-current"), _git_stdout(root, "rev-parse", "HEAD")


def _has_env_component(ref: str) -> bool:
    return any(part.startswith(".env") for part in ref.split("/"))


def _is_prefix_match(ref: str, prefixes: tuple[str, ...]) -> bool:
    return any(ref == prefix or ref.startswith(f"{prefix}/") for prefix in prefixes)


def _normalize_ref(candidate: str | Path, root: Path) -> tuple[str | None, OrderedDict[str, Any] | None]:
    value = Path(candidate)
    if value.is_absolute():
        return None, _finding("absolute_path_forbidden", "Path must be root-relative.", path=normalize_slashes(str(value)))
    ref = normalize_slashes(str(value)).strip("/")
    if not ref or ref.startswith("../") or "/../" in f"/{ref}/":
        return None, _finding("parent_traversal_forbidden", "Path must not use parent traversal.", path=ref)
    if _has_env_component(ref):
        return None, _finding("secret_path_forbidden", "Path targets an .env secret surface.", path=ref)
    if _is_prefix_match(ref, PROTECTED_PREFIXES):
        return None, _finding("protected_path_forbidden", "Owner or protected surfaces are not admitted.", path=ref)
    if _is_prefix_match(ref, DEPLOY_OR_PLATFORM_PREFIXES):
        return None, _finding("deploy_platform_path_forbidden", "Deploy and platform surfaces are not admitted.", path=ref)
    lowered_parts = tuple(part.lower() for part in ref.split("/"))
    hidden_tokens = {"transcript", "transcripts", "chat", "chats", "session", "sessions"}
    if _is_prefix_match(ref, HIDDEN_CONTEXT_PREFIXES) or any(part in hidden_tokens for part in lowered_parts):
        return None, _finding("hidden_context_path_forbidden", "Hidden transcript, chat, or session state is not admitted.", path=ref)
    resolved = (root / ref).resolve()
    try:
        resolved.relative_to(root.resolve())
    except ValueError:
        return None, _finding("outside_root_path", "Path must stay inside the ATLAS root.", path=ref)
    return ref, None


def resolve_sources(root: Path, requested_sources: list[str] | None = None) -> tuple[list[str], list[OrderedDict[str, Any]]]:
    errors: list[OrderedDict[str, Any]] = []
    refs: list[str] = []
    seen: set[str] = set()
    for source in requested_sources or list(DEFAULT_SOURCE_REFS):
        ref, error = _normalize_ref(source, root)
        if error is not None:
            errors.append(error)
            continue
        if ref is None:
            continue
        if ref not in ALLOWED_EXACT_SOURCE_REFS:
            errors.append(_finding("source_not_admitted", "Source path is outside the admitted simulation doctrine set.", path=ref))
            continue
        if ref not in seen:
            refs.append(ref)
            seen.add(ref)
    return refs, errors


def validate_output_path(root: Path, output: str) -> tuple[Path | None, OrderedDict[str, Any] | None]:
    ref, error = _normalize_ref(output, root)
    if error is not None or ref is None:
        return None, error
    if not ref.startswith("tmp/") or not ref.endswith(".json"):
        return None, _finding("non_tmp_json_output_path", "Output path must be under tmp/** and end with .json.", path=ref)
    return (root / ref).resolve(), None


def read_validation(root: Path) -> tuple[OrderedDict[str, int], OrderedDict[str, Any] | None]:
    counts = OrderedDict([("critical", 0), ("error", 0), ("warning", 0), ("info", 0)])
    path = root / "runtime" / "receipts" / "validation" / "stack-validation.latest.json"
    if not path.exists():
        return counts, _finding("validation_missing", "Stack validation receipt is unavailable.", path="runtime/receipts/validation/stack-validation.latest.json")
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return counts, _finding("validation_malformed", "Stack validation receipt is not valid JSON.", exception=str(exc))
    summary = payload.get("summary") if isinstance(payload, dict) else {}
    if not isinstance(summary, dict):
        return counts, _finding("validation_summary_missing", "Stack validation summary is unavailable.")
    for key in counts:
        counts[key] = int(summary.get(key, 0) or 0)
    return counts, None


def _read_sources(root: Path, source_refs: list[str]) -> tuple[OrderedDict[str, str], list[OrderedDict[str, Any]]]:
    texts: OrderedDict[str, str] = OrderedDict()
    errors: list[OrderedDict[str, Any]] = []
    for ref in source_refs:
        path = (root / ref).resolve()
        if not path.exists() or not path.is_file():
            errors.append(_finding("source_missing", "Admitted source path is missing.", path=ref))
            continue
        try:
            texts[ref] = path.read_text(encoding="utf-8")
        except OSError as exc:
            errors.append(_finding("source_read_failed", "Admitted source path could not be read.", path=ref, exception=str(exc)))
    return texts, errors


def _sha256(text: str) -> str:
    return f"sha256:{hashlib.sha256(text.encode('utf-8')).hexdigest()}"


def _contains_any(texts: dict[str, str], phrases: tuple[str, ...]) -> bool:
    lowered_texts = [text.lower() for text in texts.values()]
    lowered_phrases = [phrase.lower() for phrase in phrases]
    return any(phrase in text for phrase in lowered_phrases for text in lowered_texts)


def _ordered_strings(values: tuple[str, ...]) -> list[str]:
    return list(values)


def _build_requirement(
    requirement_id: str,
    category: str,
    name: str,
    description: str,
    required_fields: tuple[str, ...],
    source_refs: list[str],
) -> OrderedDict[str, Any]:
    return OrderedDict(
        [
            ("requirement_id", requirement_id),
            ("group_id", requirement_id),
            ("group_class", category),
            ("category", "schema_group"),
            ("name", name),
            ("summary", description),
            ("description", description),
            ("priority", "required"),
            ("required", True),
            ("required_fields", list(required_fields)),
            ("source_refs", source_refs),
            ("proof_required", True),
            ("authority_boundary", "advisory/read-only; no execution, owner-repo mutation, platform mutation, or marker movement"),
            ("admitted_inputs", list(source_refs)),
            ("forbidden_inputs", _ordered_strings(FORBIDDEN_DATA_SURFACES)),
            ("authority_notes", "Requirements mapping remains doctrine-bound and execution-denied."),
            ("future_adapter_notes", "Project-specific adapters remain deferred until a later admitted packet."),
            ("status", STATUS_OK),
            ("blocked_reason", None),
        ]
    )


def build_simulation_requirements_report(
    *,
    root: Path,
    sources: list[str] | None = None,
) -> OrderedDict[str, Any]:
    branch, head = collect_git_state(root)
    validation, validation_error = read_validation(root)
    source_refs, source_errors = resolve_sources(root, sources)
    texts, read_errors = _read_sources(root, source_refs)

    warnings: list[OrderedDict[str, Any]] = []
    blockers: list[OrderedDict[str, Any]] = []
    status = STATUS_OK
    safe_to_use = True

    if validation_error is not None:
        blockers.append(validation_error)
    elif validation["critical"] > 0 or validation["error"] > 0:
        blockers.append(
            _finding(
                "validation_not_safe",
                "Stack validation has critical or error findings; simulation requirements output is not safe to claim.",
                summary=dict(validation),
            )
        )

    blockers.extend(source_errors)
    blockers.extend(read_errors)

    missing_core_refs = sorted(CORE_REQUIRED_SOURCE_REFS.difference(source_refs))
    if missing_core_refs:
        blockers.append(
            _finding(
                "core_source_missing",
                "The admitted core simulation doctrine set is incomplete.",
                missing_refs=missing_core_refs,
            )
        )

    missing_supporting_refs = sorted(SUPPORTING_SOURCE_REFS.difference(source_refs))
    if missing_supporting_refs:
        warnings.append(
            _finding(
                "supporting_context_omitted",
                "Supporting root context was omitted; core mapping is still possible but adapter and routing context is reduced.",
                missing_refs=missing_supporting_refs,
            )
        )

    required_group_ids: list[str] = []
    requirements: list[OrderedDict[str, Any]] = []
    missing_group_ids: list[str] = []
    research_text = texts.get(
        "docs/ops/CORTEX-SIMULATION-SUBSTRATE-READINESS-FABLE-GENERATIVE-AGENT-RESEARCH-CONTRACT-FREEZE-2026-07-09.md",
        "",
    )
    for requirement_id, category, description, phrases, required_fields in SIMULATION_GROUPS:
        required_group_ids.append(requirement_id)
        supporting_refs = [
            "docs/ops/CORTEX-SIMULATION-SUBSTRATE-READINESS-FABLE-GENERATIVE-AGENT-RESEARCH-CONTRACT-FREEZE-2026-07-09.md",
            "docs/ops/CORTEX-SIMULATION-SUBSTRATE-READINESS-SIMULATION-REQUIREMENTS-MAP-FIRST-IMPLEMENTATION-ADMISSION-2026-07-09.md",
            "docs/ops/CORTEX-SIMULATION-SUBSTRATE-READINESS-SIMULATION-REQUIREMENTS-MAP-PROMPT-PACK-AND-WORKER-HANDOFF-CONTRACT-2026-07-10.md",
        ]
        if not blockers and not _contains_any(
            {
                "docs/ops/CORTEX-SIMULATION-SUBSTRATE-READINESS-FABLE-GENERATIVE-AGENT-RESEARCH-CONTRACT-FREEZE-2026-07-09.md": research_text
            },
            phrases,
        ):
            missing_group_ids.append(requirement_id)
            continue
        requirements.append(
            _build_requirement(
                requirement_id=requirement_id,
                category=category,
                name=category.replace("_", " "),
                description=description,
                required_fields=required_fields,
                source_refs=[ref for ref in supporting_refs if ref in source_refs],
            )
        )

    if missing_group_ids:
        blockers.append(
            _finding(
                "required_group_unmapped",
                "One or more admitted first-schema groups could not be mapped safely from the provided doctrine.",
                missing_groups=missing_group_ids,
            )
        )

    source_digests = OrderedDict((ref, _sha256(text)) for ref, text in texts.items())
    research_basis = [
        OrderedDict(
            [
                ("basis_id", "simulation-substrate-target"),
                ("summary", "Simulation targets scenario, agent, world-state, replay, and evaluation substrates rather than entertainment generation."),
                ("source_refs", ["docs/ops/CORTEX-SIMULATION-SUBSTRATE-READINESS-FABLE-GENERATIVE-AGENT-RESEARCH-CONTRACT-FREEZE-2026-07-09.md"]),
            ]
        ),
        OrderedDict(
            [
                ("basis_id", "governed-planning-lab"),
                ("summary", "Simulation is a safe planning and rehearsal lab, not an execution surface."),
                ("source_refs", ["docs/ops/CORTEX-SIMULATION-SUBSTRATE-READINESS-FABLE-GENERATIVE-AGENT-RESEARCH-CONTRACT-FREEZE-2026-07-09.md"]),
            ]
        ),
        OrderedDict(
            [
                ("basis_id", "deterministic-contract"),
                ("summary", "Simulation must preserve explicit inputs, outputs, denied authority, deterministic schemas, and replayable proof posture."),
                ("source_refs", [
                    "docs/PLAYBOOK_NOTES.md",
                    "docs/ops/CORTEX-SIMULATION-SUBSTRATE-READINESS-FABLE-GENERATIVE-AGENT-RESEARCH-CONTRACT-FREEZE-2026-07-09.md",
                    "docs/ops/CORTEX-SIMULATION-SUBSTRATE-READINESS-SIMULATION-REQUIREMENTS-MAP-PROMPT-PACK-AND-WORKER-HANDOFF-CONTRACT-2026-07-10.md",
                ]),
            ]
        ),
    ]

    core_primitives = [
        "scenario",
        "agent",
        "world_state",
        "memory",
        "reflection",
        "plan",
        "action",
        "observation",
    ]
    governance_primitives = [
        "explicit inputs",
        "explicit outputs",
        "explicit denied authority",
        "deterministic schemas",
        "replayable proof posture",
    ]
    optional_extensions = [
        OrderedDict([("extension_id", "marker_packet_planning"), ("summary", "ATLAS marker and packet planning support remains a later safe extension."), ("status", "deferred")]),
        OrderedDict([("extension_id", "fitness_support_scenarios"), ("summary", "Fitness client-goal and support scenarios remain deferred until owner-lane admission."), ("status", "deferred")]),
        OrderedDict([("extension_id", "mazer_regression_futures"), ("summary", "Mazer gameplay and regression futures remain deferred until owner-lane admission."), ("status", "deferred")]),
        OrderedDict([("extension_id", "platform_incident_rehearsal"), ("summary", "DiscordOS and broader platform incident rehearsal remain deferred."), ("status", "deferred")]),
    ]
    project_adapter_requirements = [
        OrderedDict([("adapter_id", "atlas-root"), ("summary", "ATLAS marker, packet, and proof planning adapters remain future work."), ("status", "deferred"), ("source_refs", ["docs/ops/CORTEX-SIMULATION-SUBSTRATE-READINESS-FABLE-GENERATIVE-AGENT-RESEARCH-CONTRACT-FREEZE-2026-07-09.md"])]),
        OrderedDict([("adapter_id", "fitness"), ("summary", "Fitness scenario adapters are out of scope for the first root-owned slice."), ("status", "deferred"), ("source_refs", ["docs/ops/CORTEX-SIMULATION-SUBSTRATE-READINESS-FABLE-GENERATIVE-AGENT-RESEARCH-CONTRACT-FREEZE-2026-07-09.md"])]),
        OrderedDict([("adapter_id", "mazer"), ("summary", "Mazer gameplay adapters are out of scope for the first root-owned slice."), ("status", "deferred"), ("source_refs", ["docs/ops/CORTEX-SIMULATION-SUBSTRATE-READINESS-FABLE-GENERATIVE-AGENT-RESEARCH-CONTRACT-FREEZE-2026-07-09.md"])]),
        OrderedDict([("adapter_id", "discordos"), ("summary", "DiscordOS moderation and platform-incident adapters are out of scope for the first root-owned slice."), ("status", "deferred"), ("source_refs", ["docs/ops/CORTEX-SIMULATION-SUBSTRATE-READINESS-FABLE-GENERATIVE-AGENT-RESEARCH-CONTRACT-FREEZE-2026-07-09.md"])]),
    ]
    evaluation_requirements = [
        OrderedDict([("requirement_id", "evaluation"), ("summary", "Replay and evaluation outputs must stay proof-backed and deterministic."), ("required", True)]),
        OrderedDict([("requirement_id", "safety_boundary"), ("summary", "Safety boundaries must remain first-class simulation primitives."), ("required", True)]),
        OrderedDict([("requirement_id", "proof_reference"), ("summary", "Proof references must tie simulated reasoning back to canonical ATLAS receipts and doctrine."), ("required", True)]),
    ]
    missing_requirements = [
        OrderedDict([("gap_id", "project_adapter_deferral"), ("summary", "Project-specific adapters remain deferred until later admitted packets."), ("severity", "advisory")]),
        OrderedDict([("gap_id", "fixture_input_contract"), ("summary", "Synthetic or fixture-backed scenario inputs are named but not yet concretely frozen for implementation."), ("severity", "advisory")]),
    ]

    if blockers:
        status = STATUS_BLOCKER
        safe_to_use = False
    elif warnings:
        status = STATUS_ADVISORY
        safe_to_use = False

    payload: OrderedDict[str, Any] = OrderedDict(
        [
            ("schema_version", SCHEMA_VERSION),
            ("status", status),
            ("root", normalize_slashes(str(root.resolve()))),
            ("branch", branch),
            ("head", head),
            ("source_refs", source_refs),
            ("source_digests", source_digests),
            ("research_basis", research_basis),
            ("requirement_group_count", len(required_group_ids)),
            ("mapped_group_count", len(requirements)),
            ("unmapped_group_count", max(0, len(required_group_ids) - len(requirements))),
            ("requirements", requirements),
            ("requirement_groups", requirements),
            ("core_primitives", core_primitives),
            ("governance_primitives", governance_primitives),
            ("optional_extensions", optional_extensions),
            ("project_adapter_requirements", project_adapter_requirements),
            ("evaluation_requirements", evaluation_requirements),
            ("admitted_data_surfaces", _ordered_strings(ADMITTED_DATA_SURFACES)),
            ("forbidden_data_surfaces", _ordered_strings(FORBIDDEN_DATA_SURFACES)),
            ("admitted_authority", _ordered_strings(ADMITTED_AUTHORITY)),
            ("forbidden_authority", _ordered_strings(AUTHORITY_DENIALS)),
            ("authority_denials", _ordered_strings(AUTHORITY_DENIALS)),
            ("ethical_risks", _ordered_strings(ETHICAL_RISKS)),
            ("ip_rights_risks", _ordered_strings(IP_RIGHTS_RISKS)),
            ("privacy_risks", _ordered_strings(PRIVACY_RISKS)),
            ("missing_requirements", missing_requirements),
            ("warnings", warnings),
            ("blockers", blockers),
            ("safe_to_use", safe_to_use),
            ("next_recommended_packet", RECONCILIATION_PACKET if status == STATUS_OK else None),
        ]
    )
    return payload


def _emit_payload(payload: OrderedDict[str, Any]) -> None:
    print(json.dumps(payload, indent=2))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build the Cortex simulation substrate requirements map.")
    parser.add_argument("--json", action="store_true", help="Emit JSON output.")
    parser.add_argument("--source", action="append", dest="sources", help="Repeatable admitted root-relative source path.")
    parser.add_argument("--output", help="Optional root-relative tmp/**.json output path.")
    parser.add_argument("--strict", action="store_true", help="Return nonzero when the report is not ok.")
    args = parser.parse_args(argv)

    root = atlas_root()
    try:
        payload = build_simulation_requirements_report(root=root, sources=args.sources)
    except Exception as exc:  # pragma: no cover - defensive contract guard
        payload = OrderedDict(
            [
                ("schema_version", SCHEMA_VERSION),
                ("status", STATUS_INTERNAL_ERROR),
                ("root", normalize_slashes(str(root.resolve()))),
                ("branch", None),
                ("head", None),
                ("source_refs", args.sources or list(DEFAULT_SOURCE_REFS)),
                ("source_digests", OrderedDict()),
                ("research_basis", []),
                ("requirement_group_count", len(SIMULATION_GROUPS)),
                ("mapped_group_count", 0),
                ("unmapped_group_count", len(SIMULATION_GROUPS)),
                ("requirements", []),
                ("requirement_groups", []),
                ("core_primitives", []),
                ("governance_primitives", []),
                ("optional_extensions", []),
                ("project_adapter_requirements", []),
                ("evaluation_requirements", []),
                ("admitted_data_surfaces", []),
                ("forbidden_data_surfaces", []),
                ("admitted_authority", []),
                ("forbidden_authority", []),
                ("authority_denials", list(AUTHORITY_DENIALS)),
                ("ethical_risks", []),
                ("ip_rights_risks", []),
                ("privacy_risks", []),
                ("missing_requirements", []),
                ("warnings", []),
                ("blockers", [_finding("internal_error", "Unhandled exception while building the report.", exception=str(exc))]),
                ("safe_to_use", False),
                ("next_recommended_packet", None),
            ]
        )

    if args.output:
        resolved_output, output_error = validate_output_path(root, args.output)
        if output_error is not None or resolved_output is None:
            payload["status"] = STATUS_BLOCKER
            payload["safe_to_use"] = False
            payload["next_recommended_packet"] = None
            payload["blockers"] = list(payload.get("blockers", [])) + [output_error]
            _emit_payload(payload)
            return 2
        resolved_output.parent.mkdir(parents=True, exist_ok=True)
        resolved_output.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")

    _emit_payload(payload)
    if payload["status"] == STATUS_OK:
        return 0
    if payload["status"] == STATUS_ADVISORY:
        return 2 if args.strict else 0
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
