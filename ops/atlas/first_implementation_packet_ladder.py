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

from ops._atlas import atlas_root, normalize_slashes
from ops.atlas import receipt_automation_candidate_review as review

SCHEMA_VERSION = "atlas.first_implementation_packet_ladder.v1"
STATUS_OK = "ok"
STATUS_ADVISORY_GAP = "advisory_gap"
STATUS_BLOCKER = "blocker"
STATUS_INTERNAL_ERROR = "internal_error"
REVIEW_SCHEMA_VERSION = review.SCHEMA_VERSION
DEFAULT_CANDIDATE_ID = "first-implementation"
DEFAULT_DECISION_REF = "docs/ops/AI-REPETITION-TO-AUTOMATION-PIPELINE-FIRST-IMPLEMENTATION-CANDIDATE-REVIEW-CONTRACT-FREEZE-2026-07-07.md"

PACKET_STAGES = [
    ("contract_freeze", "candidate-review contract freeze", "Freeze or reject the reviewed candidate before any implementation work."),
    ("first_implementation_admission", "first-implementation admission", "Admit the smallest exact first slice only after the candidate is accepted."),
    ("prompt_pack_and_worker_handoff_contract", "prompt-pack and worker handoff contract", "Freeze worker objective, allowed files, forbidden files, proof matrix, and stop conditions."),
    ("implementation_readiness_closeout_and_worker_routing", "implementation-readiness closeout and worker routing", "Decide whether the prompt pack can leave docs-only mode for one bounded worker."),
    ("first_implementation_worker_cluster_reconciliation", "first-implementation worker-cluster reconciliation", "Reconcile implementation, tests, proof, marker posture, and next package after the worker lands."),
]

BOUNDARIES = [
    "root_owned_sources_only",
    "review_report_input_tmp_only",
    "output_tmp_only",
    "no_owner_repo_mutation",
    "no_owner_truth",
    "no_hidden_transcript_inference",
    "no_secret_or_deploy_access",
    "no_stack_dispatch",
    "no_execution_authority",
    "no_marker_movement",
]


def _finding(code: str, message: str, *, severity: str = "warning", **details: Any) -> OrderedDict[str, Any]:
    payload: OrderedDict[str, Any] = OrderedDict([("code", code), ("severity", severity), ("message", message)])
    if details:
        payload["details"] = details
    return payload


def _normalized_relative(value: str) -> str:
    return normalize_slashes(value).strip("/")


def _load_review_report(*, root: Path, review_report_path: str | None) -> tuple[dict[str, Any] | None, list[OrderedDict[str, Any]]]:
    if review_report_path is None:
        return review.build_report(root=root), []
    resolved, error = review.validate_tmp_json_path(root=root, path_value=review_report_path, purpose="review_report")
    if error is not None:
        return None, [error]
    if resolved is None or not resolved.exists():
        return None, [_finding("missing_review_report", "Review report does not exist.", severity="blocker", path=_normalized_relative(review_report_path))]
    try:
        payload = json.loads(resolved.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return None, [_finding("invalid_review_report_json", "Review report is not valid JSON.", severity="blocker", path=_normalized_relative(review_report_path), error=str(exc))]
    if not isinstance(payload, dict):
        return None, [_finding("invalid_review_report_shape", "Review report must be a JSON object.", severity="blocker", path=_normalized_relative(review_report_path))]
    return payload, []


def _packet_title(candidate_id: str, suffix: str) -> str:
    return f"AI Repetition-to-Automation Pipeline {candidate_id} packet ladder {suffix}"


def _stage_payload(candidate_id: str) -> list[OrderedDict[str, Any]]:
    return [
        OrderedDict(
            [
                ("stage_id", stage_id),
                ("packet", _packet_title(candidate_id, suffix)),
                ("purpose", purpose),
                ("required_before_next_stage", True),
            ]
        )
        for stage_id, suffix, purpose in PACKET_STAGES
    ]


def _review_by_candidate(report: dict[str, Any], candidate_id: str) -> dict[str, Any] | None:
    reviews = report.get("reviews")
    if not isinstance(reviews, list):
        return None
    for item in reviews:
        if isinstance(item, dict) and str(item.get("candidate_id") or "") == candidate_id:
            return item
    return None


def build_report(*, root: Path, review_report_path: str | None = None, candidate_id: str = DEFAULT_CANDIDATE_ID, decision_ref: str = DEFAULT_DECISION_REF) -> OrderedDict[str, Any]:
    branch, head = review._branch_state(root)
    warnings: list[OrderedDict[str, Any]] = []
    blockers: list[OrderedDict[str, Any]] = []
    review_report, load_blockers = _load_review_report(root=root, review_report_path=review_report_path)
    blockers.extend(load_blockers)

    source_report_schema = None
    source_report_status = None
    selected_review: dict[str, Any] | None = None
    packet_ladder: list[OrderedDict[str, Any]] = []

    if not candidate_id.strip():
        blockers.append(_finding("missing_candidate_id", "Candidate id must not be empty.", severity="blocker"))

    normalized_decision_ref = _normalized_relative(decision_ref)
    if normalized_decision_ref.startswith(("repos/", "secrets/", "runtime/", "tmp/", ".vercel/", "archive/", ".playwright-mcp/")):
        blockers.append(_finding("unsupported_decision_ref", "Decision ref must be a durable root-owned docs surface.", severity="blocker", decision_ref=normalized_decision_ref))
    elif not normalized_decision_ref.startswith("docs/"):
        blockers.append(_finding("unsupported_decision_ref", "Decision ref must be under docs/**.", severity="blocker", decision_ref=normalized_decision_ref))

    if review_report is not None:
        source_report_schema = review_report.get("schema_version")
        source_report_status = review_report.get("status")
        if source_report_schema != REVIEW_SCHEMA_VERSION:
            blockers.append(_finding("unsupported_review_report_schema", "Review report schema is not the admitted candidate-review schema.", severity="blocker", expected=REVIEW_SCHEMA_VERSION, actual=str(source_report_schema)))
        elif source_report_status == review.STATUS_BLOCKER:
            blockers.append(_finding("review_report_blocked", "Review report is blocked.", severity="blocker"))
        elif source_report_status not in {review.STATUS_OK, review.STATUS_ADVISORY_GAP}:
            blockers.append(_finding("review_report_unusable_status", "Review report status is not packageable.", severity="blocker", status=str(source_report_status)))
        else:
            selected_review = _review_by_candidate(review_report, candidate_id)
            if selected_review is None:
                warnings.append(_finding("candidate_not_found", "Requested candidate was not present in the review report.", candidate_id=candidate_id))
            elif str(selected_review.get("review_status") or "") != "review_ready":
                blockers.append(_finding("candidate_not_review_ready", "Requested candidate is not review-ready.", severity="blocker", candidate_id=candidate_id, review_status=str(selected_review.get("review_status") or "")))
            else:
                packet_ladder = _stage_payload(candidate_id)

    status = STATUS_BLOCKER if blockers else (STATUS_OK if packet_ladder else STATUS_ADVISORY_GAP)
    return OrderedDict(
        [
            ("schema_version", SCHEMA_VERSION),
            ("status", status),
            ("root", normalize_slashes(str(root))),
            ("branch", branch),
            ("head", head),
            ("review_report_ref", _normalized_relative(review_report_path) if review_report_path else "live:ops/atlas/receipt_automation_candidate_review.py"),
            ("source_report_schema", source_report_schema),
            ("source_report_status", source_report_status),
            ("candidate_id", candidate_id),
            ("decision_ref", normalized_decision_ref),
            ("candidate_review_status", selected_review.get("review_status") if selected_review else None),
            ("candidate_repeat_count", int(selected_review.get("repeat_count") or 0) if selected_review else 0),
            ("supporting_receipt_count", int(selected_review.get("supporting_receipt_count") or 0) if selected_review else 0),
            ("packet_ladder", packet_ladder),
            ("next_packet", packet_ladder[1]["packet"] if len(packet_ladder) > 1 else None),
            ("boundaries", BOUNDARIES),
            ("warnings", warnings),
            ("blockers", blockers),
            ("safe_to_use", not blockers),
        ]
    )


def report_exit_code(*, status: str, strict: bool) -> int:
    if status == STATUS_OK:
        return 0
    if status == STATUS_ADVISORY_GAP:
        return 1 if strict else 0
    if status == STATUS_BLOCKER:
        return 2
    return 3


def render_summary(report: dict[str, Any]) -> str:
    return "\n".join(
        [
            f"Status: {report.get('status')}",
            f"Branch: {report.get('branch') or 'unknown'}",
            f"Head: {report.get('head') or 'unknown'}",
            f"Candidate: {report.get('candidate_id')}",
            f"Packet stages: {len(report.get('packet_ladder') or [])}",
            f"Safe to use: {str(report.get('safe_to_use')).lower()}",
        ]
    )


def render_stdout(report: dict[str, Any], *, json_only: bool) -> str:
    json_text = json.dumps(report, indent=2) + "\n"
    if json_only:
        return json_text
    return render_summary(report) + "\n\n" + json_text


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Package an accepted first-implementation review card into a deterministic packet ladder.")
    parser.add_argument("--json", action="store_true", help="Emit JSON only on stdout.")
    parser.add_argument("--review-report", help="Optional root-relative tmp/** candidate-review JSON report.")
    parser.add_argument("--candidate-id", default=DEFAULT_CANDIDATE_ID, help="Candidate id to package. Defaults to first-implementation.")
    parser.add_argument("--decision-ref", default=DEFAULT_DECISION_REF, help="Root-relative docs/** decision receipt ref.")
    parser.add_argument("--output", help="Optional root-relative tmp/** JSON output path.")
    parser.add_argument("--strict", action="store_true")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    root = atlas_root().resolve()
    try:
        report = build_report(root=root, review_report_path=args.review_report, candidate_id=args.candidate_id, decision_ref=args.decision_ref)
        if args.output:
            resolved_output, output_error = review.validate_tmp_json_path(root=root, path_value=args.output, purpose="output")
            if output_error is not None:
                report["status"] = STATUS_BLOCKER
                report["blockers"] = list(report.get("blockers", [])) + [output_error]
                report["safe_to_use"] = False
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
                ("root", normalize_slashes(str(root))),
                ("branch", None),
                ("head", None),
                ("review_report_ref", None),
                ("source_report_schema", None),
                ("source_report_status", None),
                ("candidate_id", getattr(args, "candidate_id", DEFAULT_CANDIDATE_ID)),
                ("decision_ref", getattr(args, "decision_ref", DEFAULT_DECISION_REF)),
                ("candidate_review_status", None),
                ("candidate_repeat_count", 0),
                ("supporting_receipt_count", 0),
                ("packet_ladder", []),
                ("next_packet", None),
                ("boundaries", BOUNDARIES),
                ("warnings", []),
                ("blockers", [_finding("internal_error", "First-implementation packet ladder packaging failed before classification.", severity="blocker", exception=str(exc))]),
                ("safe_to_use", False),
            ]
        )
        sys.stdout.write(render_stdout(report, json_only=getattr(args, "json", False)))
        return 3


if __name__ == "__main__":
    raise SystemExit(main())
