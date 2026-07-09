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
from ops.atlas import held_lane_prompt_suppression as suppression
from ops.atlas import marker_aware_next_packet_planner as planner

SCHEMA_VERSION = "atlas.codex_hour_block_queue_prompt.v1"
STATUS_OK = "ok"
STATUS_BLOCKED = "blocked"
STATUS_INTERNAL_ERROR = "internal_error"
HOLD_HEADER = "ATLAS ROOT HELD - DO NOT CONTINUE GENERICALLY"

QUEUE_STAGES = [
    ("preflight", "Verify root cleanliness, branch, parity, and recent commits."),
    ("baseline_checks", "Run stack validation, selector, continuity health, restart index, and coverage."),
    ("exact_packet", "Follow the exact packet named by selector or continuity manifest when one exists."),
    ("planner_fallback", "If no exact packet exists, run marker-aware planner and select only a safe root-bounded candidate."),
    ("held_lane_review", "If all candidates are held, run only an admitted held-lane review or unlock helper."),
    ("commit_cycle", "Commit, push, fetch, verify parity, then reread selector before continuing."),
    ("closeout", "Stop when all lanes are held, validation fails, or remaining work would be churn."),
]

ROOT_MARKER_LANES = [
    "AI Repetition-to-Automation Pipeline",
    "AI Long-Run Batch Orchestration",
    "Vercel Platform Observability Governance",
    "Cortex Readiness",
    "Playbook Everywhere + Cortex Interface",
    "AI Work Session Stability & Auto-Sync Loop",
    "Inventory & Truth Map",
    "Sandbox Simulation Readiness",
]

EXCLUDED_SURFACES = [
    "Fitness app implementation",
    "Mazer game implementation",
    "Playbook owner repo mutation",
    "any owner repo mutation",
    "BrowserStack or protected proof unless already available and explicitly named",
    "Stripe or human checkout proof",
    "Vercel, Supabase, deploy, secrets, .env*, .vercel, archive, and .playwright-mcp surfaces",
    "workflow dispatch or workflow edit authority",
    "hidden transcript scraping",
    "final receipt authority outside ATLAS rules",
]

SCOPE_LOCK_LINES = [
    "SCOPE LOCK:",
    "This is an ATLAS-root-only packet.",
    "",
    "Allowed:",
    "- ATLAS root governance files",
    "- ATLAS Book / continuity manifests / selector / planner / root helpers",
    "- root-owned tests and validation",
    "",
    "Forbidden:",
    "- repos/fawxzzy-fitness/**",
    "- repos/mazer/**",
    "- any owner repo mutation",
    "- Fitness product, business, Stripe, Vercel, or live launch work",
    "- Mazer game work",
    "- Vercel, Supabase, deploy, secrets, .env*, .vercel, .playwright-mcp, archive, or broad untracked backlog",
    "",
    "Fitness and Mazer may only be mentioned as advisory owner-lane inventory status.",
    "They must not be selected as next work lanes.",
    "If ATLAS selector or planner returns no root packet, stop and report held state.",
    "Do not switch to Fitness or Mazer as a fallback.",
]

REQUIRED_BASELINE_COMMANDS = [
    "git status -sb",
    "git branch --show-current",
    "git fetch origin main",
    "git rev-list --left-right --count origin/main...HEAD",
    "git log -12 --oneline --decorate",
    "git diff --name-only",
    "git diff --cached --name-only",
    "python ops/validation/validate_stack.py",
    "python ops/atlas/marker_knockout_selector.py --format json",
    "python ops/atlas/continuity_manifest_health.py",
    "python ops/atlas/continuity_open_marker_restart_index.py",
    "python ops/atlas/continuity_coverage.py",
]

OPTIONAL_HELPER_COMMANDS = [
    "python ops/atlas/marker_aware_next_packet_planner.py --json",
    "python ops/atlas/held_lane_unlock_matrix.py --json",
    "python ops/atlas/held_lane_unlock_matrix_validator.py --json",
    "python ops/atlas/ai_work_session_closeout.py --json --scope root",
    "python ops/atlas/projection_freshness.py --json --scope root",
]

BOUNDARIES = [
    "root_owned_sources_only",
    "no_owner_repo_mutation",
    "no_fitness_mutation",
    "no_mazer_mutation",
    "no_secret_or_deploy_access",
    "no_workflow_edit_or_dispatch",
    "no_hidden_transcript_inference",
    "no_protected_surface_touch",
    "no_marker_movement_without_receipt_backed_ratchet",
    "no_final_receipt_authority",
]


def _scope_lock_payload() -> OrderedDict[str, Any]:
    return OrderedDict(
        [
            ("scope", "ATLAS-root-only"),
            ("allowed", ["ATLAS root governance files", "ATLAS Book / continuity manifests / selector / planner / root helpers", "root-owned tests and validation"]),
            ("forbidden", EXCLUDED_SURFACES),
            ("boundaries", BOUNDARIES),
            ("owner_lane_fallback_forbidden", True),
        ]
    )


def _finding(code: str, message: str, *, severity: str = "warning", **details: Any) -> OrderedDict[str, Any]:
    payload: OrderedDict[str, Any] = OrderedDict([("code", code), ("severity", severity), ("message", message)])
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
    status = "clean" if behind == 0 and ahead == 0 else "drift"
    return OrderedDict([("status", status), ("behind", behind), ("ahead", ahead)])


def _latest_validation_state(root: Path) -> OrderedDict[str, int]:
    validation_path = root / "runtime" / "receipts" / "validation" / "stack-validation.latest.json"
    loaded: dict[str, Any] = {}
    if validation_path.exists():
        try:
            payload = json.loads(validation_path.read_text(encoding="utf-8"))
            if isinstance(payload, dict):
                loaded = payload
        except (OSError, json.JSONDecodeError):
            loaded = {}
    source: dict[str, Any] = loaded
    for key in ("validation_state", "validation", "summary"):
        nested = source.get(key)
        if isinstance(nested, dict):
            source = nested
            break

    def as_count(value: Any) -> int:
        if isinstance(value, bool):
            return int(value)
        if isinstance(value, int):
            return value
        if isinstance(value, str) and value.strip().isdigit():
            return int(value.strip())
        return 0

    return OrderedDict(
        [
            ("critical", as_count(source.get("critical", source.get("critical_count", 0)))),
            ("error", as_count(source.get("error", source.get("error_count", 0)))),
            ("warning", as_count(source.get("warning", source.get("warning_count", 0)))),
            ("info", as_count(source.get("info", source.get("info_count", 0)))),
        ]
    )


def _closeout_report(root: Path) -> OrderedDict[str, Any]:
    dirty = _git_stdout(root, "status", "--porcelain")
    return OrderedDict(
        [
            ("root_clean", dirty == ""),
            ("validation_state", _latest_validation_state(root)),
            ("owner_lane_fallback_forbidden", True),
        ]
    )


def _selector_summary(selector: dict[str, Any]) -> OrderedDict[str, Any]:
    open_markers = []
    for item in selector.get("open_markers") or []:
        if isinstance(item, dict):
            open_markers.append(
                OrderedDict(
                    [
                        ("marker", item.get("marker")),
                        ("percentage", item.get("percentage")),
                        ("category", item.get("category")),
                        ("priority", item.get("priority")),
                    ]
                )
            )
    return OrderedDict(
        [
            ("selected_marker", selector.get("selected_marker")),
            ("selected_percentage", selector.get("selected_percentage")),
            ("operator_action", selector.get("operator_action")),
            ("operator_action_reason", selector.get("operator_action_reason")),
            ("current_packet", selector.get("selected_current_packet")),
            ("next_packet", selector.get("next_after_current_packet")),
            ("open_markers", open_markers),
        ]
    )


def _planner_summary(planner_report: dict[str, Any]) -> OrderedDict[str, Any]:
    safe_candidates = []
    held_count = 0
    for item in planner_report.get("candidate_scores") or []:
        if not isinstance(item, dict):
            continue
        if item.get("classification") == planner.CLASS_HELD:
            held_count += 1
        if item.get("safe_to_select") is True:
            safe_candidates.append(
                OrderedDict(
                    [
                        ("marker", item.get("marker")),
                        ("packet", item.get("packet")),
                        ("classification", item.get("classification")),
                        ("score", item.get("score")),
                    ]
                )
            )
    return OrderedDict(
        [
            ("status", planner_report.get("status")),
            ("selected_marker", planner_report.get("selected_marker")),
            ("selected_packet", planner_report.get("selected_packet")),
            ("candidate_count", planner_report.get("candidate_count")),
            ("held_count", held_count),
            ("safe_candidate_count", len(safe_candidates)),
            ("safe_candidates", safe_candidates),
        ]
    )


def render_prompt(report: dict[str, Any]) -> str:
    selector = report["selector"]
    planner_state = report["planner"]
    suppression_state = report["suppression"]
    lines = [
        "CODEX-MSG-ID: CODEX-HOUR-BLOCK-ATLAS-MARKER-PROGRESSION-QUEUE",
        "",
        *SCOPE_LOCK_LINES,
        "",
        "You are operating in bounded autonomous execution mode for an ATLAS root work block.",
        "",
        "Goal:",
        "Make as much receipt-backed ATLAS marker progress as safely possible in this single run, without touching excluded owner, deploy, secret, protected, or platform surfaces.",
        "",
        "Current state:",
        f"- Branch: `{report.get('branch') or 'unknown'}`",
        f"- Head: `{report.get('head') or 'unknown'}`",
        f"- Parity: `{report.get('parity', {}).get('status')}` behind `{report.get('parity', {}).get('behind')}` ahead `{report.get('parity', {}).get('ahead')}`",
        f"- Selected marker: `{selector.get('selected_marker')}` at `{selector.get('selected_percentage')}`",
        f"- Operator action: `{selector.get('operator_action')}`",
        f"- Planner selected packet: `{planner_state.get('selected_packet')}`",
        f"- Planner safe candidates: `{planner_state.get('safe_candidate_count')}`",
        f"- Suppression decision: `{report.get('suppression_decision')}`",
        f"- Selected packet source: `{report.get('selected_packet_source')}`",
        f"- Selected packet classification: `{report.get('selected_packet_classification')}`",
        f"- Packet authority risk: `{report.get('packet_authority_risk')}`",
        f"- Should generate queue: `{report.get('should_generate_queue')}`",
        "",
        "Execution budget:",
        "- Attempt up to 7 bundles.",
        "- Prefer 2-4 commits only when meaningful validated work exists.",
        "- Stop earlier for hard stops, validation failure, missing authority, no admissible packet, or low-value churn.",
        "",
        "Allowed root marker lanes:",
    ]
    lines.extend(f"- `{lane}`" for lane in ROOT_MARKER_LANES)
    lines.extend(["", "Excluded from this work block:"])
    lines.extend(f"- {item}" for item in EXCLUDED_SURFACES)
    lines.extend(["", "Queue stages:"])
    lines.extend(f"- `{stage_id}`: {purpose}" for stage_id, purpose in QUEUE_STAGES)
    lines.extend(["", "Required baseline commands:"])
    lines.extend(f"- `{command}`" for command in REQUIRED_BASELINE_COMMANDS)
    lines.extend(["", "Optional helper commands if files exist:"])
    lines.extend(f"- `{command}`" for command in OPTIONAL_HELPER_COMMANDS)
    lines.extend(["", "Selection rule:"])
    lines.extend(
        [
            "- Follow the exact packet named by the selector or active manifest first.",
            "- If no exact packet exists, use marker-aware planner output.",
            "- If planner safe_candidate_count is zero, do not invent work; run only admitted held-lane review helpers or close out.",
            "- If all remaining lanes are held, stop with a clear closeout.",
        ]
    )
    lines.extend(["", "Commit cadence:"])
    lines.extend(
        [
            "- Stage exact intended files only.",
            "- Commit with a specific message.",
            "- Push to `origin main`.",
            "- Fetch and verify `origin/main...HEAD = 0 0`.",
            "- Reread selector or manifest before continuing.",
        ]
    )
    lines.extend(["", "Marker movement rule:"])
    lines.extend(
        [
            "- Move a marker only when implementation or proof landed, focused tests passed, stack validation passed, and a receipt-backed ratchet condition is recorded.",
            "- Do not move markers for wording refresh, selector-only reads, PR body edits, root inventory resync, or generic cleanup.",
        ]
    )
    lines.extend(["", "Hard stops:"])
    lines.extend(
        [
            "- Owner repo mutation is required.",
            "- Fitness or Mazer mutation is required.",
            "- Protected proof is required but unavailable.",
            "- Secrets, deploy, Supabase, Vercel, or workflow dispatch are required.",
            "- Stack validation has critical or error.",
            "- Planner has no executable candidate and no admitted held-lane helper remains.",
            "- Remaining work is narration or churn.",
        ]
    )
    lines.extend(["", "Final closeout must include commits, marker movement, validation, tests, protected surfaces untouched, owner repos untouched, exact next package, blockers, and whether another queued prompt would be useful."])
    if suppression_state.get("allowed_next_actions"):
        lines.extend(["", "Suppression-aware allowed next actions:"])
        lines.extend(f"- `{action}`" for action in suppression_state.get("allowed_next_actions", []))
    return "\n".join(lines) + "\n"


def render_hold_prompt(report: dict[str, Any]) -> str:
    selector = report["selector"]
    suppression_state = report["suppression"]
    validation_state = suppression_state.get("validation_state") or {}
    lines = [
        "CODEX-MSG-ID: CODEX-HOUR-BLOCK-ATLAS-ROOT-HELD-NO-GENERIC-CONTINUATION",
        "",
        HOLD_HEADER,
        "",
        *SCOPE_LOCK_LINES,
        "",
        "Current state:",
        f"- Branch: `{report.get('branch') or 'unknown'}`",
        f"- Head: `{report.get('head') or 'unknown'}`",
        f"- Parity: `{report.get('parity', {}).get('status')}` behind `{report.get('parity', {}).get('behind')}` ahead `{report.get('parity', {}).get('ahead')}`",
        f"- Selected marker: `{selector.get('selected_marker')}` at `{selector.get('selected_percentage')}`",
        f"- Operator action: `{selector.get('operator_action')}`",
        f"- Planner selected packet: `{report.get('planner', {}).get('selected_packet')}`",
        f"- Planner safe candidates: `{report.get('planner', {}).get('safe_candidate_count')}`",
        "",
        "Suppression state:",
        f"- Decision: `{report.get('suppression_decision')}`",
        f"- Reason: {report.get('suppression_reason')}",
        f"- Root is clean: `{suppression_state.get('root_clean')}`",
        f"- Validation: critical `{validation_state.get('critical')}` error `{validation_state.get('error')}` warning `{validation_state.get('warning')}` info `{validation_state.get('info')}`",
        f"- Exact root packet exists: `{suppression_state.get('exact_packet_available')}`",
        f"- Owner-lane fallback is forbidden: `{suppression_state.get('owner_lane_fallback_forbidden')}`",
        "",
        "Do not continue generically.",
        "",
        "Do not:",
        "- Do not open a generic ATLAS root work loop.",
        "- Do not switch into Fitness or Mazer.",
        "- Do not use owner-lane fallback.",
        "- Do not touch secrets, deploy, Vercel, Supabase, workflows, or protected surfaces.",
        "- Do not move markers without receipt-backed proof.",
        "",
        "Required next move:",
        "- Choose a new bounded ATLAS-root packet before continuing.",
        "- If the next work is owner-lane work, start a separate owner-lane packet outside this ATLAS root queue.",
        "- If material state changed, rerun selector, planner, suppression, validation, and continuity health before issuing another queue.",
        "",
        "Allowed next actions:",
    ]
    lines.extend(f"- `{action}`" for action in suppression_state.get("allowed_next_actions", []))
    return "\n".join(lines) + "\n"


def build_report(
    *,
    root: Path,
    source_refs: list[str] | None = None,
    operator_selected_packet: str | None = None,
    external_proof_present: bool = False,
) -> OrderedDict[str, Any]:
    branch, head = _branch_state(root)
    source_refs = list(source_refs or [])
    planner_report = planner.build_report(root=root, source_refs=source_refs)

    # The selector has no stable import-level report builder, so use its CLI as a read-only source.
    selector_payload: dict[str, Any]
    try:
        selector_text = subprocess.check_output(
            [sys.executable, str(root / "ops" / "atlas" / "marker_knockout_selector.py"), "--format", "json"],
            cwd=str(root),
            text=True,
            encoding="utf-8",
            errors="replace",
        )
        selector_payload = json.loads(selector_text)
    except Exception:
        selector_payload = {}

    suppression_report = suppression.build_report(
        selector_report=selector_payload,
        planner_report=planner_report,
        closeout_report=_closeout_report(root),
        operator_selected_packet=operator_selected_packet,
        external_proof_present=external_proof_present,
    )
    should_generate_queue = suppression_report.get("status") != suppression.STATUS_SUPPRESS

    blockers: list[OrderedDict[str, Any]] = []
    if not selector_payload:
        blockers.append(_finding("selector_unavailable", "Marker knockout selector JSON was unavailable.", severity="blocker"))
    if planner_report.get("status") == planner.STATUS_BLOCKED:
        blockers.append(_finding("planner_blocked", "Marker-aware planner is blocked.", severity="blocker"))
    if suppression_report.get("status") in {suppression.STATUS_BLOCKED, suppression.STATUS_INTERNAL_ERROR}:
        blockers.append(
            _finding(
                "suppression_blocked",
                "Held-lane prompt suppression blocked queue generation.",
                severity="blocker",
                decision=suppression_report.get("decision"),
                reason=suppression_report.get("suppression_reason"),
            )
        )

    prompt_text = ""
    status = STATUS_BLOCKED if blockers else STATUS_OK
    report = OrderedDict(
        [
            ("schema_version", SCHEMA_VERSION),
            ("status", status),
            ("root", normalize_slashes(str(root))),
            ("branch", branch),
            ("head", head),
            ("parity", _parity_state(root)),
            ("source_refs", [normalize_slashes(item) for item in source_refs]),
            ("selector", _selector_summary(selector_payload)),
            ("planner", _planner_summary(planner_report)),
            ("suppression", suppression_report),
            ("suppression_decision", suppression_report.get("decision")),
            ("suppression_reason", suppression_report.get("suppression_reason")),
            ("selected_packet_source", suppression_report.get("selected_packet_source")),
            ("selected_packet_classification", suppression_report.get("selected_packet_classification")),
            ("packet_authority_risk", suppression_report.get("packet_authority_risk")),
            ("allowed_next_actions", suppression_report.get("allowed_next_actions", [])),
            ("should_generate_queue", should_generate_queue and not blockers),
            ("operator_selected_packet", operator_selected_packet),
            ("scope_lock", _scope_lock_payload()),
            ("queue_stages", [OrderedDict([("stage_id", stage_id), ("purpose", purpose)]) for stage_id, purpose in QUEUE_STAGES]),
            ("allowed_root_marker_lanes", ROOT_MARKER_LANES),
            ("excluded_surfaces", EXCLUDED_SURFACES),
            ("boundaries", BOUNDARIES),
            ("baseline_commands", REQUIRED_BASELINE_COMMANDS),
            ("optional_helper_commands", OPTIONAL_HELPER_COMMANDS),
            ("blockers", blockers),
            ("warnings", []),
            ("safe_to_use", not blockers),
        ]
    )
    if not blockers:
        prompt_text = render_prompt(report) if report["should_generate_queue"] else render_hold_prompt(report)
    report["prompt_text"] = prompt_text
    return report


def report_exit_code(*, status: str, strict: bool) -> int:
    if status == STATUS_OK:
        return 0
    if status == STATUS_BLOCKED:
        return 1 if strict else 2
    return 3


def render_summary(report: dict[str, Any]) -> str:
    return "\n".join(
        [
            f"Status: {report.get('status')}",
            f"Branch: {report.get('branch') or 'unknown'}",
            f"Head: {report.get('head') or 'unknown'}",
            f"Selected marker: {report.get('selector', {}).get('selected_marker')}",
            f"Planner safe candidates: {report.get('planner', {}).get('safe_candidate_count')}",
            f"Safe to use: {str(report.get('safe_to_use')).lower()}",
        ]
    )


def render_stdout(report: dict[str, Any], *, json_only: bool, prompt_only: bool) -> str:
    if prompt_only:
        return str(report.get("prompt_text") or "")
    json_text = json.dumps(report, indent=2) + "\n"
    if json_only:
        return json_text
    return render_summary(report) + "\n\n" + json_text


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build a bounded Codex hour-block queue prompt from current ATLAS root state.")
    parser.add_argument("--json", action="store_true", help="Emit JSON only on stdout.")
    parser.add_argument("--prompt-only", action="store_true", help="Emit only the generated prompt text.")
    parser.add_argument("--source", action="append", default=[], help="Optional root-relative admitted source ref for planner context. May be repeated.")
    parser.add_argument("--operator-selected-packet", help="Explicit operator-selected root packet name.")
    parser.add_argument("--external-proof-present", action="store_true", help="Allow queue generation when admitted external proof exists.")
    parser.add_argument("--output", help="Optional root-relative tmp/**.json report output path.")
    parser.add_argument("--prompt-output", help="Optional root-relative tmp/**.md prompt output path.")
    parser.add_argument("--strict", action="store_true")
    return parser.parse_args(argv)


def _write_tmp_text(*, root: Path, output_path: str, text: str, purpose: str) -> OrderedDict[str, Any] | None:
    candidate = Path(output_path)
    if candidate.is_absolute():
        return _finding(f"absolute_{purpose}_path", "Prompt output path must be root-relative.", severity="blocker", path=normalize_slashes(str(candidate)))
    relative_path = normalize_slashes(str(candidate)).strip("/")
    if ".." in Path(relative_path).parts:
        return _finding(f"parent_traversal_{purpose}_path", "Prompt output path must not use parent traversal.", severity="blocker", path=relative_path)
    if not relative_path.startswith("tmp/") or not relative_path.endswith(".md"):
        return _finding(f"protected_{purpose}_path", "Prompt output writes are admitted only to root-relative tmp/**.md.", severity="blocker", path=relative_path)
    resolved_output = (root / relative_path).resolve()
    try:
        resolved_output.relative_to(root.resolve())
    except ValueError:
        return _finding(f"outside_root_{purpose}_path", "Prompt output path must stay inside the ATLAS root.", severity="blocker", path=relative_path)
    resolved_output.parent.mkdir(parents=True, exist_ok=True)
    resolved_output.write_text(text, encoding="utf-8")
    return None


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    root = atlas_root().resolve()
    try:
        report = build_report(
            root=root,
            source_refs=list(args.source or []),
            operator_selected_packet=args.operator_selected_packet,
            external_proof_present=bool(args.external_proof_present),
        )
        if args.output:
            resolved_output, output_error = planner.validate_output_path(root=root, output_path=args.output)
            if output_error is not None:
                report["status"] = STATUS_BLOCKED
                report["blockers"] = list(report.get("blockers", [])) + [output_error]
                report["safe_to_use"] = False
            elif resolved_output is not None:
                resolved_output.parent.mkdir(parents=True, exist_ok=True)
                resolved_output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
        if args.prompt_output:
            error = _write_tmp_text(root=root, output_path=args.prompt_output, text=str(report.get("prompt_text") or ""), purpose="prompt_output")
            if error is not None:
                report["status"] = STATUS_BLOCKED
                report["blockers"] = list(report.get("blockers", [])) + [error]
                report["safe_to_use"] = False
        sys.stdout.write(render_stdout(report, json_only=args.json, prompt_only=args.prompt_only))
        return report_exit_code(status=str(report.get("status") or STATUS_INTERNAL_ERROR), strict=args.strict)
    except Exception as exc:
        report = OrderedDict(
            [
                ("schema_version", SCHEMA_VERSION),
                ("status", STATUS_INTERNAL_ERROR),
                ("root", normalize_slashes(str(root))),
                ("branch", None),
                ("head", None),
                ("parity", OrderedDict([("status", "unknown"), ("behind", None), ("ahead", None)])),
                ("source_refs", []),
                ("selector", OrderedDict()),
                ("planner", OrderedDict()),
                ("suppression", OrderedDict()),
                ("suppression_decision", None),
                ("suppression_reason", None),
                ("selected_packet_source", None),
                ("selected_packet_classification", None),
                ("packet_authority_risk", "internal_error"),
                ("allowed_next_actions", []),
                ("should_generate_queue", False),
                ("operator_selected_packet", None),
                ("scope_lock", _scope_lock_payload()),
                ("queue_stages", []),
                ("allowed_root_marker_lanes", ROOT_MARKER_LANES),
                ("excluded_surfaces", EXCLUDED_SURFACES),
                ("boundaries", BOUNDARIES),
                ("baseline_commands", REQUIRED_BASELINE_COMMANDS),
                ("optional_helper_commands", OPTIONAL_HELPER_COMMANDS),
                ("blockers", [_finding("internal_error", "Codex hour-block queue prompt generation failed.", severity="blocker", exception=str(exc))]),
                ("warnings", []),
                ("safe_to_use", False),
                ("prompt_text", ""),
            ]
        )
        sys.stdout.write(render_stdout(report, json_only=getattr(args, "json", False), prompt_only=getattr(args, "prompt_only", False)))
        return 3


if __name__ == "__main__":
    raise SystemExit(main())
