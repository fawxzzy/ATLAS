from __future__ import annotations

import argparse
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
from ops.atlas import ai_work_session_preflight
from ops.atlas import marker_aware_next_packet_planner as planner

SCHEMA_VERSION = "atlas.autonomous_lane_scheduler.v1"
PROGRAM_SCHEMA_VERSION = "atlas.autonomous-work-program.v1"

STATUS_EXECUTE = "execute"
STATUS_HOLD = "hold"
STATUS_VALIDATION_CLEANUP = "validation_cleanup"
STATUS_BLOCKED = "blocked"
STATUS_INTERNAL_ERROR = "internal_error"

DECISION_VALIDATION_CLEANUP = "validation_cleanup"
DECISION_WORKER_RECONCILIATION = "worker_reconciliation"
DECISION_ROUTED_WORKER = "routed_worker"
DECISION_EXACT_MANIFEST_PACKET = "exact_manifest_packet"
DECISION_OPERATOR_PROGRAM_PACKET = "operator_program_packet"
DECISION_CROSS_MARKER_OPPORTUNITY = "cross_marker_opportunity"
DECISION_PLANNER_CANDIDATE = "planner_candidate"
DECISION_HOLD = "hold"

PHASE_WORKER_RECONCILIATION = "worker_reconciliation"
PHASE_WORKER_IMPLEMENTATION = "worker_implementation"
PHASE_IMPLEMENTATION_READINESS = "implementation_readiness"
PHASE_PROMPT_PACK = "prompt_pack"
PHASE_FIRST_IMPLEMENTATION_ADMISSION = "first_implementation_admission"
PHASE_CONTRACT_FREEZE = "contract_freeze"
PHASE_SELECTOR = "selector"
PHASE_HOLD = "hold"

SAFE_CLASSIFICATIONS = {
    planner.CLASS_IMPLEMENTATION_READY,
    planner.CLASS_IMMEDIATE,
    planner.CLASS_DOCS_ONLY,
}
DOCS_ONLY_PHASES = {
    PHASE_IMPLEMENTATION_READINESS,
    PHASE_PROMPT_PACK,
    PHASE_FIRST_IMPLEMENTATION_ADMISSION,
    PHASE_CONTRACT_FREEZE,
    PHASE_SELECTOR,
}
OWNER_LANE_TERMS = (
    "fitness",
    "mazer",
    "discordos",
    "foundation",
    "trove",
    "stream",
    "owner repo",
    "owner-repo",
    "playbook owner repo",
    "repos/playbook",
    "repos\\playbook",
)
PROTECTED_TERMS = (
    ".env",
    ".github/workflows",
    ".playwright-mcp",
    ".vercel",
    "archive/",
    "deploy",
    "deployment",
    "secret",
    "supabase",
    "vercel",
    "workflow dispatch",
)
AUTHORITY_DENIALS = [
    "owner-repo-mutation",
    "platform-mutation",
    "deploy",
    "secret-handling",
    "workflow-dispatch",
    "final-receipt",
    "marker-movement",
    "hidden-transcript-ingestion",
]
BASELINE_COMMANDS = [
    "git status -sb",
    "git branch --show-current",
    "git fetch origin main",
    "git rev-list --left-right --count origin/main...HEAD",
    "git log -15 --oneline --decorate",
    "git diff --name-only",
    "git diff --cached --name-only",
    "python ops/validation/validate_stack.py",
    "python ops/atlas/marker_knockout_selector.py --format json",
    "python ops/atlas/continuity_manifest_health.py",
    "python ops/atlas/continuity_open_marker_restart_index.py",
    "python ops/atlas/continuity_coverage.py",
]


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


def _branch_state(root: Path) -> tuple[str | None, str | None]:
    return _git_stdout(root, "branch", "--show-current"), _git_stdout(root, "rev-parse", "HEAD")


def _parity_state(root: Path) -> OrderedDict[str, Any]:
    raw = _git_stdout(root, "rev-list", "--left-right", "--count", "origin/main...HEAD")
    if raw is None:
        return OrderedDict([("status", "unknown"), ("behind", None), ("ahead", None)])
    parts = raw.split()
    if len(parts) != 2:
        return OrderedDict([("status", "unknown"), ("behind", None), ("ahead", None)])
    behind = int(parts[0])
    ahead = int(parts[1])
    return OrderedDict([("status", "clean" if behind == 0 and ahead == 0 else "drift"), ("behind", behind), ("ahead", ahead)])


def _normalize_ref(candidate: str | Path, root: Path) -> tuple[str | None, OrderedDict[str, Any] | None]:
    value = Path(candidate)
    if value.is_absolute():
        return None, _finding("absolute_path_forbidden", "Path must be root-relative.", path=normalize_slashes(str(value)))
    ref = normalize_slashes(str(value)).strip("/")
    if not ref or ref.startswith("../") or "/../" in f"/{ref}/":
        return None, _finding("parent_traversal_forbidden", "Path must not use parent traversal.", path=ref)
    if ref.startswith("repos/") or ref.startswith("archive/") or ref.startswith("secrets/"):
        return None, _finding("protected_path_forbidden", "Path targets a protected surface.", path=ref)
    if any(part.startswith(".env") for part in ref.split("/")):
        return None, _finding("secret_path_forbidden", "Path targets an env secret surface.", path=ref)
    resolved = (root / ref).resolve()
    try:
        resolved.relative_to(root.resolve())
    except ValueError:
        return None, _finding("outside_root_path", "Path must stay inside the ATLAS root.", path=ref)
    return ref, None


def validate_program_path(root: Path, path: str) -> tuple[Path | None, OrderedDict[str, Any] | None]:
    ref, error = _normalize_ref(path, root)
    if error is not None or ref is None:
        return None, error
    if not ref.endswith(".json"):
        return None, _finding("program_not_json", "Program path must end with .json.", path=ref)
    resolved = (root / ref).resolve()
    if not resolved.exists():
        return None, _finding("program_missing", "Program path does not exist.", path=ref)
    return resolved, None


def validate_output_path(root: Path, path: str, *, suffix: str) -> tuple[Path | None, OrderedDict[str, Any] | None]:
    ref, error = _normalize_ref(path, root)
    if error is not None or ref is None:
        return None, error
    if not ref.startswith("tmp/atlas/") or not ref.endswith(suffix):
        return None, _finding("protected_output_path", f"Output path must be under tmp/atlas/** and end with {suffix}.", path=ref)
    return (root / ref).resolve(), None


def load_program(root: Path, program_path: str) -> tuple[dict[str, Any] | None, list[OrderedDict[str, Any]]]:
    resolved, error = validate_program_path(root, program_path)
    if error is not None or resolved is None:
        return None, [error] if error is not None else []
    try:
        payload = json.loads(resolved.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return None, [_finding("program_invalid_json", "Program file is not valid JSON.", path=program_path, error=str(exc))]
    if not isinstance(payload, dict):
        return None, [_finding("program_invalid_shape", "Program payload must be a JSON object.", path=program_path)]
    errors: list[OrderedDict[str, Any]] = []
    if payload.get("schema_version") != PROGRAM_SCHEMA_VERSION:
        errors.append(_finding("program_schema_mismatch", "Program schema_version is not admitted.", expected=PROGRAM_SCHEMA_VERSION, actual=payload.get("schema_version")))
    return payload, errors


def _load_selector(root: Path) -> dict[str, Any]:
    selector_text = subprocess.check_output(
        [sys.executable, str(root / "ops" / "atlas" / "marker_knockout_selector.py"), "--format", "json"],
        cwd=str(root),
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    payload = json.loads(selector_text)
    return payload if isinstance(payload, dict) else {}


def _scope_lock(program: dict[str, Any]) -> OrderedDict[str, Any]:
    return OrderedDict(
        [
            ("scope", "ATLAS-root-only"),
            ("allowed_markers", list(program.get("allowed_markers", []))),
            ("excluded_markers", list(program.get("excluded_markers", []))),
            ("forbidden_owner_lanes", list(program.get("forbidden_owner_lanes", []))),
            ("one_packet_per_invocation", True),
        ]
    )


def _phase_from_packet(packet: str, mode: str, classification: str) -> str:
    lowered_packet = packet.lower()
    lowered_mode = mode.lower()
    if "worker cluster reconciliation" in lowered_packet or "worker-cluster reconciliation" in lowered_packet or "reconciliation" in lowered_packet:
        return PHASE_WORKER_RECONCILIATION
    if "worker packet" in lowered_packet or classification == planner.CLASS_IMPLEMENTATION_READY:
        return PHASE_WORKER_IMPLEMENTATION
    if "implementation-readiness" in lowered_packet or "implementation readiness" in lowered_mode:
        return PHASE_IMPLEMENTATION_READINESS
    if "prompt-pack" in lowered_packet or "worker handoff contract" in lowered_packet:
        return PHASE_PROMPT_PACK
    if "first-implementation admission" in lowered_packet or "first implementation admission" in lowered_mode:
        return PHASE_FIRST_IMPLEMENTATION_ADMISSION
    if "contract freeze" in lowered_packet:
        return PHASE_CONTRACT_FREEZE
    if "reselection" in lowered_packet or "selector" in lowered_packet:
        return PHASE_SELECTOR
    if classification == planner.CLASS_DOCS_ONLY:
        return PHASE_CONTRACT_FREEZE
    return PHASE_HOLD


def _file_overlap_risk(phase: str) -> str:
    if phase in {PHASE_WORKER_RECONCILIATION, PHASE_WORKER_IMPLEMENTATION}:
        return "medium"
    if phase in DOCS_ONLY_PHASES:
        return "low"
    return "high"


def _is_owner_lane(packet: str) -> bool:
    lowered = packet.lower()
    return any(term in lowered for term in OWNER_LANE_TERMS)


def _is_protected_packet(packet: str) -> bool:
    lowered = packet.lower()
    return any(term in lowered for term in PROTECTED_TERMS)


def _is_stale_packet(packet: str, classification: str) -> bool:
    lowered = packet.lower()
    return classification in {planner.CLASS_HELD, planner.CLASS_STALE, planner.CLASS_NO_ACTION} or lowered.startswith("no immediate") or "already completed" in lowered


def _phase_priority_rank(program: dict[str, Any], phase: str) -> int:
    priorities = list(program.get("phase_priority", []))
    try:
        return priorities.index(phase)
    except ValueError:
        return len(priorities) + 1


def _slugify_marker(marker: str) -> str:
    return "-".join(token for token in "".join(ch if ch.isalnum() else " " for ch in marker).split()).upper()


def _reselection_receipt(marker: str) -> str:
    return f"docs/ops/ATLAS-ROOT-OPERATOR-RESELECTION-TO-{_slugify_marker(marker)}-2026-07-10.md"


def _candidate_from_planner_item(
    *,
    item: dict[str, Any],
    active_marker: str | None,
    active_lane_is_held: bool,
    program: dict[str, Any],
    recent_docs_only_streak: int,
) -> OrderedDict[str, Any]:
    marker = str(item.get("marker") or "")
    packet = str(item.get("packet") or "")
    classification = str(item.get("classification") or "")
    mode = str(item.get("mode") or "")
    phase = _phase_from_packet(packet, mode, classification)
    score = int(item.get("score") or 0)
    allowed_markers = set(program.get("allowed_markers", []))
    excluded_markers = set(program.get("excluded_markers", []))
    max_docs_only_streak = int(program.get("max_docs_only_streak", 2) or 2)
    requires_reselection = bool(active_lane_is_held and active_marker and marker and marker != active_marker)
    blocked_reason = None
    stale_reason = None
    requires_external_input = classification in {planner.CLASS_EXTERNAL_PROOF, planner.CLASS_PROOF_GATED, planner.CLASS_OWNER_BLOCKED}
    if marker and allowed_markers and marker not in allowed_markers:
        blocked_reason = "marker_not_allowed_by_program"
    elif marker in excluded_markers:
        blocked_reason = "marker_excluded_by_program"
    elif _is_owner_lane(packet):
        blocked_reason = "owner_lane_forbidden"
    elif _is_protected_packet(packet):
        blocked_reason = "protected_or_platform_mutation_forbidden"
    elif requires_external_input:
        blocked_reason = "requires_external_input"
    elif recent_docs_only_streak >= max_docs_only_streak and phase in DOCS_ONLY_PHASES:
        blocked_reason = "docs_only_streak_limit"
    elif _is_stale_packet(packet, classification):
        stale_reason = "held_or_stale_packet"
    safe = classification in SAFE_CLASSIFICATIONS and blocked_reason is None and stale_reason is None
    proof_delta = "implementation_backed" if phase in {PHASE_WORKER_RECONCILIATION, PHASE_WORKER_IMPLEMENTATION} else "docs_or_contract"
    return OrderedDict(
        [
            ("marker", marker),
            ("lane", marker),
            ("packet", packet or None),
            ("phase", phase),
            ("score", score),
            ("source", "planner"),
            ("proof_delta", proof_delta),
            ("blocked_reason", blocked_reason),
            ("stale_reason", stale_reason),
            ("file_overlap_risk", _file_overlap_risk(phase)),
            ("requires_external_input", requires_external_input),
            ("requires_reselection", requires_reselection and bool(program.get("allow_reselection"))),
            ("safe", safe),
            ("classification", classification),
            ("cross_marker_signal_applied", bool(item.get("cross_marker_signal_applied"))),
        ]
    )


def _selector_exact_packet(selector: dict[str, Any]) -> tuple[str | None, str | None]:
    action = str(selector.get("operator_action") or "")
    current_packet = str(selector.get("selected_current_packet") or "")
    if action not in {"hold_current_lane", "no_immediate_root_packet", "held", "hold"} and current_packet and not current_packet.lower().startswith("no immediate"):
        return str(selector.get("selected_marker") or ""), current_packet
    return None, None


def _sort_candidates(program: dict[str, Any], candidates: list[OrderedDict[str, Any]]) -> list[OrderedDict[str, Any]]:
    def key(item: OrderedDict[str, Any]) -> tuple[int, int]:
        return (_phase_priority_rank(program, str(item.get("phase") or "")), -int(item.get("score") or 0))

    return sorted(candidates, key=key)


def _validation_state(preflight_report: dict[str, Any]) -> OrderedDict[str, Any]:
    validation = preflight_report.get("validation", {}) if isinstance(preflight_report.get("validation"), dict) else {}
    projection = preflight_report.get("projection_freshness", {}) if isinstance(preflight_report.get("projection_freshness"), dict) else {}
    residue = preflight_report.get("local_residue", {}) if isinstance(preflight_report.get("local_residue"), dict) else {}
    return OrderedDict(
        [
            ("critical", int(validation.get("critical", 0) or 0)),
            ("error", int(validation.get("error", 0) or 0)),
            ("warning", int(validation.get("warning", 0) or 0)),
            ("info", int(validation.get("info", 0) or 0)),
            ("projection_status", projection.get("status")),
            ("inventory_matches_live_working_set", projection.get("inventory_matches_live_working_set")),
            ("root_dirty_path_count", len(residue.get("root_dirty_paths", []) if isinstance(residue.get("root_dirty_paths"), list) else [])),
        ]
    )


def render_prompt(report: dict[str, Any]) -> str:
    status = str(report.get("status") or "")
    if status == STATUS_HOLD:
        return "\n".join(
            [
                "ATLAS ROOT HELD - NO SAFE AUTOCOMPLETE PACKET",
                "",
                "Do not invent fallback work.",
                f"Stop reason: {report.get('stop_reason')}",
                "Do not switch into owner repos, deploy surfaces, secrets, or platform mutation.",
            ]
        ) + "\n"
    if status == STATUS_VALIDATION_CLEANUP:
        return "\n".join(
            [
                "ATLAS ROOT VALIDATION CLEANUP PACKET",
                "",
                "Execute only root cleanup and validation refresh work.",
                f"Reason: {report.get('stop_reason')}",
                f"Branch: `{report.get('git_state', {}).get('branch')}`",
                f"Head: `{report.get('git_state', {}).get('head')}`",
                "",
                "Required preflight:",
                *[f"- `{command}`" for command in BASELINE_COMMANDS],
                "",
                "One-packet-only rule: do not execute any other lane in this task.",
            ]
        ) + "\n"
    lines = [
        "Run the ATLAS autonomous lane scheduler and execute exactly one selected packet.",
        "",
        f"Selected lane: `{report.get('selected_lane')}`",
        f"Selected packet: `{report.get('selected_packet')}`",
        f"Phase: `{report.get('packet_phase')}`",
        f"Routing mode: `{report.get('routing_mode')}`",
        f"Branch: `{report.get('git_state', {}).get('branch')}`",
        f"Head: `{report.get('git_state', {}).get('head')}`",
        "",
        "Required preflight:",
    ]
    lines.extend(f"- `{command}`" for command in BASELINE_COMMANDS)
    lines.extend(
        [
            "",
            "Scope lock:",
            "- ATLAS root only.",
            "- Do not mutate Fitness, Mazer, DiscordOS, Foundation, FawxzzyWeb, Playbook, or Stream owner lanes.",
            "- Do not touch Vercel, Supabase, deploy, secrets, workflows, `.env*`, `.vercel`, `.playwright-mcp`, or `archive`.",
            "",
        ]
    )
    if report.get("requires_reselection_receipt"):
        lines.extend(
            [
                "Reselection bundle required:",
                f"- Create receipt: `{report.get('reselection_receipt')}`",
                f"- Previous routing: `{report.get('git_state', {}).get('active_lane')}`",
                f"- Selected routing: `{report.get('selected_marker')}`",
                "",
            ]
        )
    lines.extend(
        [
            "Validation commands:",
            "- `python ops/validation/validate_stack.py`",
            "",
            "Commit/push/parity requirements:",
            "- Stage exact intended files only.",
            "- Commit with a specific message.",
            "- Push to `origin main`.",
            "- Fetch and verify `origin/main...HEAD = 0 0`.",
            "",
            "One-packet-only rule: do not execute a second lane in this task.",
        ]
    )
    return "\n".join(lines) + "\n"


def build_report(
    *,
    root: Path,
    program: dict[str, Any],
    max_candidates: int,
    prompt_output_path: str | None = None,
    current_marker: str | None = None,
    recent_docs_only_streak: int = 0,
    preflight_report: dict[str, Any] | None = None,
    selector_report: dict[str, Any] | None = None,
    planner_report: dict[str, Any] | None = None,
) -> OrderedDict[str, Any]:
    branch, head = _branch_state(root)
    parity = _parity_state(root)
    preflight_report = preflight_report or ai_work_session_preflight.build_report(root=root, scope="root")
    selector_report = selector_report or _load_selector(root)
    planner_report = planner_report or planner.build_report(root=root)

    active_marker = current_marker or str(selector_report.get("selected_marker") or preflight_report.get("markers", {}).get("active_lane") or "")
    active_lane_is_held = bool(selector_report.get("active_lane_is_held") or preflight_report.get("markers", {}).get("active_lane_is_held"))
    validation_state = _validation_state(preflight_report)
    scope_lock = _scope_lock(program)

    candidates: list[OrderedDict[str, Any]] = []
    skipped_candidates: list[OrderedDict[str, Any]] = []
    blocked_candidates: list[OrderedDict[str, Any]] = []
    for item in planner_report.get("candidate_scores", [])[:max_candidates]:
        if not isinstance(item, dict):
            continue
        candidate = _candidate_from_planner_item(
            item=item,
            active_marker=active_marker,
            active_lane_is_held=active_lane_is_held,
            program=program,
            recent_docs_only_streak=recent_docs_only_streak,
        )
        if candidate["safe"]:
            candidates.append(candidate)
        elif candidate["blocked_reason"]:
            blocked_candidates.append(candidate)
        else:
            skipped_candidates.append(candidate)

    sorted_candidates = _sort_candidates(program, candidates)
    selected_candidate = sorted_candidates[0] if sorted_candidates else None
    status = STATUS_HOLD
    decision = DECISION_HOLD
    routing_mode = DECISION_HOLD
    selected_marker = None
    selected_packet = None
    packet_phase = PHASE_HOLD
    selected_packet_source = None
    requires_reselection_receipt = False
    reselection_receipt = None
    stop_reason = "no_safe_candidate"
    safe_to_execute = False

    exact_marker, exact_packet = _selector_exact_packet(selector_report)
    if validation_state["critical"] > 0 or validation_state["error"] > 0:
        status = STATUS_VALIDATION_CLEANUP
        decision = DECISION_VALIDATION_CLEANUP
        routing_mode = DECISION_VALIDATION_CLEANUP
        selected_marker = "ATLAS root"
        selected_packet = "ATLAS root validation cleanup"
        packet_phase = PHASE_SELECTOR
        selected_packet_source = "validation"
        stop_reason = "critical_or_error_validation"
        safe_to_execute = True
    elif exact_packet:
        selected_marker = exact_marker
        selected_packet = exact_packet
        packet_phase = _phase_from_packet(exact_packet, str(selector_report.get("selected_current_packet_mode") or ""), planner.CLASS_IMMEDIATE)
        selected_packet_source = "selector_current_packet"
        decision = DECISION_EXACT_MANIFEST_PACKET
        routing_mode = decision
        status = STATUS_EXECUTE
        stop_reason = None
        safe_to_execute = True
    elif selected_candidate is not None:
        selected_marker = str(selected_candidate["marker"] or "")
        selected_packet = str(selected_candidate["packet"] or "")
        packet_phase = str(selected_candidate["phase"] or PHASE_HOLD)
        selected_packet_source = str(selected_candidate["source"] or "planner")
        requires_reselection_receipt = bool(selected_candidate["requires_reselection"])
        reselection_receipt = _reselection_receipt(selected_marker) if requires_reselection_receipt else None
        if packet_phase == PHASE_WORKER_RECONCILIATION:
            decision = DECISION_WORKER_RECONCILIATION
        elif packet_phase == PHASE_WORKER_IMPLEMENTATION:
            decision = DECISION_ROUTED_WORKER
        elif bool(selected_candidate.get("cross_marker_signal_applied")):
            decision = DECISION_CROSS_MARKER_OPPORTUNITY
        elif requires_reselection_receipt:
            decision = DECISION_OPERATOR_PROGRAM_PACKET
        else:
            decision = DECISION_PLANNER_CANDIDATE
        routing_mode = decision
        status = STATUS_EXECUTE
        stop_reason = None
        safe_to_execute = True

    report = OrderedDict(
        [
            ("schema_version", SCHEMA_VERSION),
            ("status", status),
            ("decision", decision),
            ("routing_mode", routing_mode),
            ("selected_marker", selected_marker),
            ("selected_lane", selected_marker),
            ("selected_packet", selected_packet),
            ("packet_phase", packet_phase),
            ("selected_packet_source", selected_packet_source),
            ("requires_reselection_receipt", requires_reselection_receipt),
            ("reselection_receipt", reselection_receipt),
            ("candidate_count", len(candidates) + len(skipped_candidates) + len(blocked_candidates)),
            ("candidates", sorted_candidates),
            ("skipped_candidates", skipped_candidates),
            ("blocked_candidates", blocked_candidates),
            ("validation_state", validation_state),
            (
                "git_state",
                OrderedDict(
                    [
                        ("branch", branch),
                        ("head", head),
                        ("parity", parity),
                        ("active_lane", active_marker),
                        ("active_lane_is_held", active_lane_is_held),
                    ]
                ),
            ),
            ("scope_lock", scope_lock),
            ("authority_denials", AUTHORITY_DENIALS),
            ("safe_to_execute", safe_to_execute),
            ("stop_reason", stop_reason),
            ("prompt_output", prompt_output_path),
            (
                "next_recommended_command",
                "python ops/atlas/autonomous_lane_scheduler.py --json --program tmp/atlas/autonomous-work-program.json --max-candidates 30 --output tmp/atlas/autonomous-lane-scheduler.latest.json --prompt-output tmp/atlas/codex-autocomplete-prompt.latest.md",
            ),
        ]
    )
    return report


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Select one deterministic ATLAS root packet for autonomous execution.")
    parser.add_argument("--json", action="store_true", help="Emit JSON output.")
    parser.add_argument("--program", required=True, help="Root-relative operator work-program JSON path.")
    parser.add_argument("--output", required=True, help="Root-relative tmp/atlas/**.json output path.")
    parser.add_argument("--prompt-output", required=True, help="Root-relative tmp/atlas/**.md prompt output path.")
    parser.add_argument("--max-candidates", type=int, default=30, help="Maximum planner candidates to consider.")
    parser.add_argument("--strict", action="store_true", help="Return nonzero when no executable packet exists.")
    parser.add_argument("--explain", action="store_true", help="Reserved for verbose output compatibility.")
    parser.add_argument("--allow-reselection", action="store_true", help="Override program allow_reselection to true.")
    parser.add_argument("--current-marker", help="Optional explicit current marker override.")
    return parser.parse_args(argv)


def report_exit_code(*, status: str, strict: bool) -> int:
    if status == STATUS_EXECUTE:
        return 0
    if status == STATUS_HOLD:
        return 2 if strict else 0
    if status == STATUS_VALIDATION_CLEANUP:
        return 2 if strict else 1
    if status == STATUS_BLOCKED:
        return 2
    return 3


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    root = atlas_root()
    try:
        program, program_errors = load_program(root, args.program)
        output_path, output_error = validate_output_path(root, args.output, suffix=".json")
        prompt_output_path, prompt_output_error = validate_output_path(root, args.prompt_output, suffix=".md")
        if program is None or program_errors or output_error is not None or prompt_output_error is not None or output_path is None or prompt_output_path is None:
            blockers = [error for error in [output_error, prompt_output_error] if error is not None]
            blockers.extend(program_errors)
            payload = OrderedDict(
                [
                    ("schema_version", SCHEMA_VERSION),
                    ("status", STATUS_BLOCKED),
                    ("decision", DECISION_HOLD),
                    ("routing_mode", DECISION_HOLD),
                    ("selected_marker", None),
                    ("selected_lane", None),
                    ("selected_packet", None),
                    ("packet_phase", PHASE_HOLD),
                    ("selected_packet_source", None),
                    ("requires_reselection_receipt", False),
                    ("reselection_receipt", None),
                    ("candidate_count", 0),
                    ("candidates", []),
                    ("skipped_candidates", []),
                    ("blocked_candidates", blockers),
                    ("validation_state", OrderedDict()),
                    ("git_state", OrderedDict()),
                    ("scope_lock", OrderedDict()),
                    ("authority_denials", AUTHORITY_DENIALS),
                    ("safe_to_execute", False),
                    ("stop_reason", "invalid_scheduler_inputs"),
                    ("prompt_output", args.prompt_output),
                    ("next_recommended_command", None),
                ]
            )
            print(json.dumps(payload, indent=2))
            return 2

        if args.allow_reselection:
            program["allow_reselection"] = True

        report = build_report(
            root=root,
            program=program,
            max_candidates=args.max_candidates,
            prompt_output_path=normalize_slashes(args.prompt_output),
            current_marker=args.current_marker,
        )
        prompt_text = render_prompt(report)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
        prompt_output_path.parent.mkdir(parents=True, exist_ok=True)
        prompt_output_path.write_text(prompt_text, encoding="utf-8")
        print(json.dumps(report, indent=2))
        return report_exit_code(status=str(report.get("status") or STATUS_INTERNAL_ERROR), strict=args.strict)
    except Exception as exc:  # pragma: no cover - defensive guard
        payload = OrderedDict(
            [
                ("schema_version", SCHEMA_VERSION),
                ("status", STATUS_INTERNAL_ERROR),
                ("decision", DECISION_HOLD),
                ("routing_mode", DECISION_HOLD),
                ("selected_marker", None),
                ("selected_lane", None),
                ("selected_packet", None),
                ("packet_phase", PHASE_HOLD),
                ("selected_packet_source", None),
                ("requires_reselection_receipt", False),
                ("reselection_receipt", None),
                ("candidate_count", 0),
                ("candidates", []),
                ("skipped_candidates", []),
                ("blocked_candidates", [_finding("internal_error", "Unhandled scheduler exception.", error=str(exc))]),
                ("validation_state", OrderedDict()),
                ("git_state", OrderedDict()),
                ("scope_lock", OrderedDict()),
                ("authority_denials", AUTHORITY_DENIALS),
                ("safe_to_execute", False),
                ("stop_reason", "internal_error"),
                ("prompt_output", args.prompt_output if "args" in locals() else None),
                ("next_recommended_command", None),
            ]
        )
        print(json.dumps(payload, indent=2))
        return 3


if __name__ == "__main__":
    raise SystemExit(main())
