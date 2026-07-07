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
from ops.atlas import receipt_automation_candidate_extractor as extractor

SCHEMA_VERSION = "atlas.receipt_automation_candidate_review.v1"
STATUS_OK = "ok"
STATUS_ADVISORY_GAP = "advisory_gap"
STATUS_BLOCKER = "blocker"
STATUS_INTERNAL_ERROR = "internal_error"
EXTRACTOR_SCHEMA_VERSION = extractor.SCHEMA_VERSION

REVIEW_PRIORITY = {
    "helper": 0,
    "validation_or_governance_check": 1,
    "selector_or_routing_rule": 2,
    "prompt_pack": 3,
    "read_model_or_manifest_projection": 4,
}


def _finding(code: str, message: str, *, severity: str = "warning", **details: Any) -> OrderedDict[str, Any]:
    payload: OrderedDict[str, Any] = OrderedDict([("code", code), ("severity", severity), ("message", message)])
    if details:
        payload["details"] = details
    return payload


def _normalized_relative(value: str) -> str:
    return normalize_slashes(value).strip("/")


def validate_tmp_json_path(*, root: Path, path_value: str, purpose: str) -> tuple[Path | None, OrderedDict[str, Any] | None]:
    candidate = Path(path_value)
    if candidate.is_absolute():
        return None, _finding(f"absolute_{purpose}_path", f"{purpose} path must be root-relative.", severity="blocker", path=normalize_slashes(str(candidate)))
    relative_path = _normalized_relative(str(candidate))
    if ".." in Path(relative_path).parts:
        return None, _finding(f"parent_traversal_{purpose}_path", f"{purpose} path must not use parent traversal.", severity="blocker", path=relative_path)
    if not relative_path.startswith("tmp/"):
        return None, _finding(f"protected_{purpose}_path", f"{purpose} path is admitted only under tmp/**.", severity="blocker", path=relative_path)
    if not relative_path.endswith(".json"):
        return None, _finding(f"non_json_{purpose}_path", f"{purpose} path must point to a JSON file.", severity="blocker", path=relative_path)
    resolved = (root / relative_path).resolve()
    try:
        resolved.relative_to(root.resolve())
    except ValueError:
        return None, _finding(f"outside_root_{purpose}_path", f"{purpose} path must stay inside the ATLAS root.", severity="blocker", path=relative_path)
    return resolved, None


def _branch_state(root: Path) -> tuple[str | None, str | None]:
    return extractor._branch_state(root)  # Reuse the extractor's read-only git helper.


def _load_candidate_report(*, root: Path, candidate_report_path: str | None) -> tuple[dict[str, Any] | None, list[OrderedDict[str, Any]]]:
    if candidate_report_path is None:
        return extractor.build_report(root=root), []
    resolved, error = validate_tmp_json_path(root=root, path_value=candidate_report_path, purpose="candidate_report")
    if error is not None:
        return None, [error]
    if resolved is None or not resolved.exists():
        return None, [_finding("missing_candidate_report", "Candidate report does not exist.", severity="blocker", path=_normalized_relative(candidate_report_path))]
    try:
        payload = json.loads(resolved.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return None, [_finding("invalid_candidate_report_json", "Candidate report is not valid JSON.", severity="blocker", path=_normalized_relative(candidate_report_path), error=str(exc))]
    if not isinstance(payload, dict):
        return None, [_finding("invalid_candidate_report_shape", "Candidate report must be a JSON object.", severity="blocker", path=_normalized_relative(candidate_report_path))]
    return payload, []


def _review_packet(candidate: dict[str, Any]) -> str:
    candidate_id = str(candidate.get("id") or "unknown-candidate").replace("-", " ")
    return f"AI Repetition-to-Automation Pipeline {candidate_id} candidate-review contract freeze"


def _review_boundaries(candidate: dict[str, Any]) -> list[str]:
    inherited = [str(item) for item in candidate.get("boundaries") or []]
    extra = [
        "advisory_review_only",
        "contract_freeze_before_implementation",
        "no_owner_truth",
        "no_execution_authority",
        "no_marker_movement",
    ]
    return sorted(set(inherited + extra))


def build_reviews(candidate_report: dict[str, Any]) -> tuple[list[OrderedDict[str, Any]], list[OrderedDict[str, Any]]]:
    candidates = candidate_report.get("candidates")
    if not isinstance(candidates, list):
        return [], [_finding("invalid_candidates_shape", "Candidate report candidates field must be a list.", severity="blocker")]

    reviews: list[OrderedDict[str, Any]] = []
    for candidate in candidates:
        if not isinstance(candidate, dict):
            return [], [_finding("invalid_candidate_shape", "Each candidate must be a JSON object.", severity="blocker")]
        category = str(candidate.get("category") or "unknown")
        repeat_count = int(candidate.get("repeat_count") or 0)
        supporting_receipts = candidate.get("supporting_receipts") or []
        reviews.append(
            OrderedDict(
                [
                    ("candidate_id", str(candidate.get("id") or "unknown")),
                    ("category", category),
                    ("review_status", "review_ready"),
                    ("review_priority", REVIEW_PRIORITY.get(category, 99)),
                    ("repeat_count", repeat_count),
                    ("supporting_receipt_count", len(supporting_receipts) if isinstance(supporting_receipts, list) else 0),
                    ("recommended_review_packet", _review_packet(candidate)),
                    ("required_operator_decision", "contract_freeze_or_reject"),
                    ("evidence_summary", str(candidate.get("pattern_summary") or "")),
                    ("boundaries", _review_boundaries(candidate)),
                ]
            )
        )
    reviews.sort(key=lambda item: (int(item["review_priority"]), -int(item["repeat_count"]), str(item["candidate_id"])))
    return reviews, []


def build_report(*, root: Path, candidate_report_path: str | None = None) -> OrderedDict[str, Any]:
    branch, head = _branch_state(root)
    candidate_report, load_blockers = _load_candidate_report(root=root, candidate_report_path=candidate_report_path)
    warnings: list[OrderedDict[str, Any]] = []
    blockers: list[OrderedDict[str, Any]] = list(load_blockers)
    reviews: list[OrderedDict[str, Any]] = []
    candidate_count = 0
    source_report_schema = None
    source_report_status = None

    if candidate_report is not None:
        source_report_schema = candidate_report.get("schema_version")
        source_report_status = candidate_report.get("status")
        if source_report_schema != EXTRACTOR_SCHEMA_VERSION:
            blockers.append(
                _finding(
                    "unsupported_candidate_report_schema",
                    "Candidate report schema is not the admitted extractor schema.",
                    severity="blocker",
                    expected=EXTRACTOR_SCHEMA_VERSION,
                    actual=str(source_report_schema),
                )
            )
        elif source_report_status == extractor.STATUS_BLOCKER:
            blockers.append(_finding("candidate_report_blocked", "Candidate extractor report is blocked.", severity="blocker"))
        elif source_report_status not in {extractor.STATUS_OK, extractor.STATUS_ADVISORY_GAP}:
            blockers.append(_finding("candidate_report_unusable_status", "Candidate extractor report status is not reviewable.", severity="blocker", status=str(source_report_status)))
        else:
            candidate_count = int(candidate_report.get("candidate_count") or 0)
            reviews, review_blockers = build_reviews(candidate_report)
            blockers.extend(review_blockers)
            if not reviews and not blockers:
                warnings.append(_finding("no_reviewable_candidates", "No reviewable automation candidates were present in the extractor report."))

    status = STATUS_BLOCKER if blockers else (STATUS_OK if reviews else STATUS_ADVISORY_GAP)
    return OrderedDict(
        [
            ("schema_version", SCHEMA_VERSION),
            ("status", status),
            ("root", normalize_slashes(str(root))),
            ("branch", branch),
            ("head", head),
            ("candidate_report_ref", _normalized_relative(candidate_report_path) if candidate_report_path else "live:ops/atlas/receipt_automation_candidate_extractor.py"),
            ("source_report_schema", source_report_schema),
            ("source_report_status", source_report_status),
            ("candidate_count", candidate_count),
            ("review_count", len(reviews)),
            ("reviews", reviews),
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
            f"Candidates: {report.get('candidate_count')}",
            f"Reviews: {report.get('review_count')}",
            f"Safe to use: {str(report.get('safe_to_use')).lower()}",
        ]
    )


def render_stdout(report: dict[str, Any], *, json_only: bool) -> str:
    json_text = json.dumps(report, indent=2) + "\n"
    if json_only:
        return json_text
    return render_summary(report) + "\n\n" + json_text


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Review read-only receipt-derived automation candidates.")
    parser.add_argument("--json", action="store_true", help="Emit JSON only on stdout.")
    parser.add_argument("--candidate-report", help="Optional root-relative tmp/** extractor JSON report.")
    parser.add_argument("--output", help="Optional root-relative tmp/** JSON output path.")
    parser.add_argument("--strict", action="store_true")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    root = atlas_root().resolve()
    try:
        report = build_report(root=root, candidate_report_path=args.candidate_report)
        if args.output:
            resolved_output, output_error = validate_tmp_json_path(root=root, path_value=args.output, purpose="output")
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
                ("candidate_report_ref", None),
                ("source_report_schema", None),
                ("source_report_status", None),
                ("candidate_count", 0),
                ("review_count", 0),
                ("reviews", []),
                ("warnings", []),
                ("blockers", [_finding("internal_error", "Candidate review failed before classification.", severity="blocker", exception=str(exc))]),
                ("safe_to_use", False),
            ]
        )
        sys.stdout.write(render_stdout(report, json_only=getattr(args, "json", False)))
        return 3


if __name__ == "__main__":
    raise SystemExit(main())
