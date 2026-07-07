from __future__ import annotations

import argparse
import json
import sys
from collections import OrderedDict
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from ops._atlas import atlas_root
from ops.atlas import marker_aware_next_packet_planner as planner

SCHEMA_VERSION = "atlas.held_lane_unlock_matrix.v1"

STATUS_OK = "ok"
STATUS_ADVISORY_MATRIX = "advisory_matrix"
STATUS_BLOCKED = "blocked"
STATUS_INTERNAL_ERROR = "internal_error"

BLOCKER_CLASSES = [
    "held_by_manifest",
    "proof_gated",
    "external_proof_required",
    "owner_lane_required",
    "operator_selection_required",
    "already_completed",
    "stale_packet",
    "implementation_missing",
    "contract_missing",
    "readiness_missing",
    "authority_risk",
    "protected_surface_risk",
    "no_action_hold",
]

PLAYBOOK_RULE_REFS = [
    "docs/PLAYBOOK_NOTES.md#marker-ratchet-threshold",
    "docs/PLAYBOOK_NOTES.md#implementation-readiness-before-worker-routing",
    "docs/architecture/ATLAS-CORTEX-PLAYBOOK-CODEX.md#explicit-artifact-ref-handoff",
    "docs/standards/WORKER-ORCHESTRATION.md#handoff-artifacts",
]

OWNER_LANE_BOUNDARIES = [
    "Fitness app work is an owner lane and is not mutated by this helper.",
    "Mazer game work is an owner lane and is not mutated by this helper.",
    "Playbook owner-repo work requires a separate owner-side packet.",
    "ATLAS root may read durable owner-truth mirrors but may not convert owner drift into root mutation authority.",
]

AUTHORITY_RISKS = [
    OrderedDict([("risk", "owner_lane_mutation"), ("mitigation", "helper emits advisory unlock records only and rejects owner-repo source refs")]),
    OrderedDict([("risk", "secret_or_deploy_authority"), ("mitigation", "helper inherits secret, deploy, platform, and Vercel source/output guards")]),
    OrderedDict([("risk", "workflow_edit_or_dispatch"), ("mitigation", "helper has no workflow edit or dispatch path")]),
    OrderedDict([("risk", "marker_or_final_receipt_authority"), ("mitigation", "helper cannot move markers or emit final receipts")]),
    OrderedDict([("risk", "cortex_authority_drift"), ("mitigation", "Cortex refs remain advisory evidence only")]),
]


def _finding(code: str, message: str, *, severity: str = "warning", **details: Any) -> OrderedDict[str, Any]:
    payload: OrderedDict[str, Any] = OrderedDict([("code", code), ("severity", severity), ("message", message)])
    if details:
        payload["details"] = details
    return payload


def _text(candidate: dict[str, Any]) -> str:
    return " ".join(str(candidate.get(key) or "") for key in ("marker", "classification", "packet", "mode", "reason")).lower()


def candidate_blocker_classes(candidate: dict[str, Any]) -> list[str]:
    classification = str(candidate.get("classification") or "")
    text = _text(candidate)
    classes: list[str] = []

    if classification in {planner.CLASS_HELD, planner.CLASS_NO_ACTION}:
        classes.append("held_by_manifest")
        if "no immediate" in text or "no action" in text or "hold" in text:
            classes.append("no_action_hold")
    if classification == planner.CLASS_PROOF_GATED:
        classes.append("proof_gated")
    if classification == planner.CLASS_EXTERNAL_PROOF:
        classes.append("external_proof_required")
    if classification == planner.CLASS_OWNER_BLOCKED or "owner-side" in text or "owner lane" in text:
        classes.append("owner_lane_required")
    if classification == planner.CLASS_STALE:
        classes.append("stale_packet")
    if classification == planner.CLASS_UNSAFE:
        classes.extend(["authority_risk", "protected_surface_risk"])
    if classification == planner.CLASS_IMPLEMENTATION_READY:
        classes.append("implementation_missing")
    if classification == planner.CLASS_DOCS_ONLY:
        if "contract" in text and "freeze" in text:
            classes.append("contract_missing")
        elif "readiness" in text:
            classes.append("readiness_missing")
        elif "prompt-pack" in text or "handoff" in text:
            classes.append("readiness_missing")
        elif "first-implementation admission" in text:
            classes.append("implementation_missing")
        else:
            classes.append("operator_selection_required")
    if "operator" in text or "separately selected" in text:
        classes.append("operator_selection_required")
    if candidate.get("percent") == 100 or "closed" in text or "already complete" in text:
        classes.append("already_completed")
    if "protected" in text or "secret" in text or "deploy" in text or "workflow" in text:
        classes.append("protected_surface_risk")
    if "authority" in text or "final receipt" in text or "marker-write" in text:
        classes.append("authority_risk")

    if not classes:
        classes.append("operator_selection_required")
    return [blocker_class for blocker_class in BLOCKER_CLASSES if blocker_class in set(classes)]


def _required_proofs(blocker_classes: list[str]) -> list[str]:
    proofs: list[str] = []
    if "proof_gated" in blocker_classes:
        proofs.append("artifact-backed or receipt-backed proof")
    if "external_proof_required" in blocker_classes:
        proofs.append("validated external proof")
    if "implementation_missing" in blocker_classes:
        proofs.append("first-implementation worker-cluster reconciliation")
    if "readiness_missing" in blocker_classes:
        proofs.append("implementation-readiness closeout and worker routing")
    if "authority_risk" in blocker_classes or "protected_surface_risk" in blocker_classes:
        proofs.append("narrowed no-forbidden-authority scope")
    return proofs


def _required_receipts(candidate: dict[str, Any], blocker_classes: list[str]) -> list[str]:
    receipts: list[str] = []
    current = candidate.get("current_checkpoint_receipt")
    if isinstance(current, str) and current:
        receipts.append(current)
    if "contract_missing" in blocker_classes:
        receipts.append("contract-freeze receipt")
    if "readiness_missing" in blocker_classes:
        receipts.append("implementation-readiness closeout receipt")
    if "operator_selection_required" in blocker_classes:
        receipts.append("operator-selected packet receipt")
    return receipts


def _operator_actions(blocker_classes: list[str]) -> list[str]:
    actions: list[str] = []
    if "operator_selection_required" in blocker_classes:
        actions.append("select exact bounded scope")
    if "owner_lane_required" in blocker_classes:
        actions.append("route separate owner-side packet")
    if "external_proof_required" in blocker_classes:
        actions.append("supply and validate external proof")
    if "protected_surface_risk" in blocker_classes or "authority_risk" in blocker_classes:
        actions.append("narrow scope or add explicit approval gate")
    if "no_action_hold" in blocker_classes:
        actions.append("hold until state changes")
    return actions


def _is_unlockable(candidate: dict[str, Any]) -> bool:
    return bool(candidate.get("safe_to_select")) and candidate.get("classification") in {
        planner.CLASS_IMMEDIATE,
        planner.CLASS_DOCS_ONLY,
        planner.CLASS_IMPLEMENTATION_READY,
    }


def _matrix_candidate(candidate: dict[str, Any]) -> OrderedDict[str, Any]:
    blocker_classes = candidate_blocker_classes(candidate)
    return OrderedDict(
        [
            ("marker", candidate.get("marker")),
            ("percent", candidate.get("percent")),
            ("source_ref", candidate.get("source_ref")),
            ("planner_classification", candidate.get("classification")),
            ("packet", candidate.get("packet")),
            ("mode", candidate.get("mode")),
            ("safe_to_select", bool(candidate.get("safe_to_select"))),
            ("unlockable", _is_unlockable(candidate)),
            ("blocker_classes", blocker_classes),
            ("required_proofs", _required_proofs(blocker_classes)),
            ("required_receipts", _required_receipts(candidate, blocker_classes)),
            ("operator_actions", _operator_actions(blocker_classes)),
            ("reason", candidate.get("reason")),
        ]
    )


def _unique(values: list[str]) -> list[str]:
    return sorted({value for value in values if value})


def build_report(*, root: Path, source_refs: list[str] | None = None, planner_report: dict[str, Any] | None = None) -> OrderedDict[str, Any]:
    report = planner_report if planner_report is not None else planner.build_report(root=root, source_refs=source_refs or [])
    candidates = [_matrix_candidate(candidate) for candidate in report.get("candidate_scores", []) if isinstance(candidate, dict)]
    blockers = list(report.get("blockers", [])) if isinstance(report.get("blockers"), list) else []
    unlockable = [candidate for candidate in candidates if candidate.get("unlockable")]

    if blockers or report.get("status") == planner.STATUS_BLOCKED:
        status = STATUS_BLOCKED
    elif unlockable:
        status = STATUS_OK
    elif candidates:
        status = STATUS_ADVISORY_MATRIX
    else:
        status = STATUS_BLOCKED
        blockers.append(_finding("no_candidates", "No planner candidates were available for unlock-matrix classification.", severity="blocker"))

    required_proofs = _unique([proof for candidate in candidates for proof in candidate.get("required_proofs", [])])
    required_receipts = _unique([receipt for candidate in candidates for receipt in candidate.get("required_receipts", [])])
    operator_actions = _unique([action for candidate in candidates for action in candidate.get("operator_actions", [])])
    selected = report.get("selected_packet") if unlockable else None

    return OrderedDict(
        [
            ("schema_version", SCHEMA_VERSION),
            ("status", status),
            ("candidate_count", len(candidates)),
            ("held_count", sum(1 for candidate in candidates if "held_by_manifest" in candidate.get("blocker_classes", []))),
            ("unlockable_count", len(unlockable)),
            ("blocker_classes", BLOCKER_CLASSES),
            ("candidates", candidates),
            ("required_proofs", required_proofs),
            ("required_receipts", required_receipts),
            ("operator_actions", operator_actions),
            ("owner_lane_boundaries", OWNER_LANE_BOUNDARIES),
            ("playbook_rule_refs", PLAYBOOK_RULE_REFS),
            ("authority_risks", AUTHORITY_RISKS),
            ("recommended_next_selection", selected),
            ("safe_to_continue", not blockers),
            ("blockers", blockers),
            ("branch", report.get("branch")),
            ("head", report.get("head")),
        ]
    )


def report_exit_code(*, status: str, strict: bool) -> int:
    if status == STATUS_OK:
        return 0
    if status == STATUS_ADVISORY_MATRIX:
        return 1 if strict else 0
    if status == STATUS_BLOCKED:
        return 2
    return 3


def render_summary(report: dict[str, Any]) -> str:
    return "\n".join(
        [
            f"Status: {report.get('status')}",
            f"Branch: {report.get('branch') or 'unknown'}",
            f"Head: {report.get('head') or 'unknown'}",
            f"Candidates: {report.get('candidate_count')}",
            f"Held: {report.get('held_count')}",
            f"Unlockable: {report.get('unlockable_count')}",
            f"Recommended next selection: {report.get('recommended_next_selection') or 'none'}",
            f"Safe to continue: {str(report.get('safe_to_continue')).lower()}",
        ]
    )


def render_stdout(report: dict[str, Any], *, json_only: bool) -> str:
    json_text = json.dumps(report, indent=2) + "\n"
    if json_only:
        return json_text
    return render_summary(report) + "\n\n" + json_text


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Emit an advisory unlock matrix for held marker-aware planner candidates.")
    parser.add_argument("--json", action="store_true", help="Emit JSON only on stdout.")
    parser.add_argument("--source", action="append", default=[], help="Optional root-relative admitted source ref for the underlying planner. May be repeated.")
    parser.add_argument("--output", help="Optional root-relative tmp/**.json output path.")
    parser.add_argument("--strict", action="store_true")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    root = atlas_root().resolve()
    try:
        report = build_report(root=root, source_refs=list(args.source or []))
        if args.output:
            resolved_output, output_error = planner.validate_output_path(root=root, output_path=args.output)
            if output_error is not None:
                report["status"] = STATUS_BLOCKED
                report["blockers"] = list(report.get("blockers", [])) + [output_error]
                report["safe_to_continue"] = False
            elif resolved_output is not None:
                resolved_output.parent.mkdir(parents=True, exist_ok=True)
                resolved_output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
        sys.stdout.write(render_stdout(report, json_only=args.json))
        return report_exit_code(status=str(report.get("status") or STATUS_INTERNAL_ERROR), strict=args.strict)
    except Exception as exc:
        report = OrderedDict(
            [
                ("schema_version", SCHEMA_VERSION),
                ("status", STATUS_INTERNAL_ERROR),
                ("candidate_count", 0),
                ("held_count", 0),
                ("unlockable_count", 0),
                ("blocker_classes", BLOCKER_CLASSES),
                ("candidates", []),
                ("required_proofs", []),
                ("required_receipts", []),
                ("operator_actions", []),
                ("owner_lane_boundaries", OWNER_LANE_BOUNDARIES),
                ("playbook_rule_refs", PLAYBOOK_RULE_REFS),
                ("authority_risks", AUTHORITY_RISKS),
                ("recommended_next_selection", None),
                ("safe_to_continue", False),
                ("blockers", [_finding("internal_error", "Held-lane unlock matrix failed.", severity="blocker", exception=str(exc))]),
                ("branch", None),
                ("head", None),
            ]
        )
        sys.stdout.write(render_stdout(report, json_only=getattr(args, "json", False)))
        return 3


if __name__ == "__main__":
    raise SystemExit(main())
