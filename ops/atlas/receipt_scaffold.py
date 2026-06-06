from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from ops._atlas import atlas_relative, atlas_root, normalize_slashes

HELPER_VERSION = "atlas.receipt-scaffold.v1"
STACK_COMMAND_ID = "stack receipt package"
DEFAULT_MODE = "draft-only operator-usable receipt scaffold"
DEFAULT_STATUS = "normal"
PLACEHOLDER_OBJECTIVE = "REPLACE_ME_OBJECTIVE"
PLACEHOLDER_SCOPE = "REPLACE_ME_SCOPE"
PLACEHOLDER_VERIFICATION = "REPLACE_ME_VERIFICATION"
PLACEHOLDER_NEXT_PACKAGE = "REPLACE_ME_NEXT_PACKAGE"
DEFAULT_VERIFICATION_COMMAND = r"python .\ops\validation\validate_stack.py --ratchet"
DEFAULT_MARKER_DECISION = "none"
DEFAULT_PROTECTED_SURFACES = (
    "repos/fawxzzy-fitness",
    "archive/",
    ".vercel",
    ".env",
)


class ReceiptScaffoldError(RuntimeError):
    pass


def _default_objective(*, lane: str, status: str) -> str:
    normalized_lane = lane.strip()
    if status == "blocked":
        return (
            f"Preserve one bounded blocked draft-only receipt scaffold for `{normalized_lane}` "
            f"using the admitted `{STACK_COMMAND_ID}` contract without widening into marker "
            "movement, doctrine truth, publication readiness, or deploy authority."
        )

    return (
        f"Preserve one bounded draft-only operator-usable receipt scaffold for `{normalized_lane}` "
        f"using the admitted `{STACK_COMMAND_ID}` contract without widening into marker movement, "
        "doctrine truth, publication readiness, or deploy authority."
    )


def _default_scope(
    *,
    next_package: str,
    marker_percentage: str,
    supporting_posture: str,
    status: str,
) -> str:
    marker_text = marker_percentage or "unreported"
    support_text = supporting_posture or "unreported"

    scope_lines = [
        "- render one draft-only receipt scaffold from the admitted `_stack` contract",
        f"- preserve current marker posture `{marker_text}` and supporting posture `{support_text}`",
        f"- carry the current exact next package `{next_package}` without widening into owner execution or authority claims",
    ]
    if status == "blocked":
        scope_lines.append("- stop after preserving the blocked scaffold until the blocker class materially changes")
    return "\n".join(scope_lines)


def _default_verification_lines() -> tuple[str, ...]:
    return (DEFAULT_VERIFICATION_COMMAND,)


@dataclass(frozen=True)
class ReceiptScaffoldInput:
    title: str
    lane: str
    date: str
    status: str
    objective: str
    scope: str
    receipt_context: str | None
    blocker_code: str | None
    blocker_summary: str | None
    marker_decision: str
    verification_lines: tuple[str, ...]
    protected_surfaces: tuple[str, ...]
    output_ref: str | None


def _non_empty(value: str, *, field_name: str) -> str:
    normalized = value.strip()
    if not normalized:
        raise ReceiptScaffoldError(f"{field_name} must be a non-empty string.")
    return normalized


def _normalized_optional(value: str | None) -> str | None:
    if value is None:
        return None
    normalized = value.strip()
    return normalized or None


def _normalize_lines(values: list[str] | None, *, default: str) -> tuple[str, ...]:
    items = tuple(item.strip() for item in (values or []) if item and item.strip())
    return items if items else (default,)


def _normalize_surfaces(values: list[str] | None) -> tuple[str, ...]:
    items = tuple(normalize_slashes(item.strip()) for item in (values or []) if item and item.strip())
    return items if items else DEFAULT_PROTECTED_SURFACES


def _validate_relative_ref(value: str, *, field_name: str) -> str:
    normalized = normalize_slashes(_non_empty(value, field_name=field_name))
    path_value = Path(normalized)
    if path_value.is_absolute() or normalized.startswith("../"):
        raise ReceiptScaffoldError(f"{field_name} must be a bounded ATLAS-relative path.")
    return normalized


def build_input(args: argparse.Namespace) -> ReceiptScaffoldInput:
    status = _non_empty(args.status, field_name="status")
    if status not in {"normal", "blocked"}:
        raise ReceiptScaffoldError("status must be 'normal' or 'blocked'.")

    blocker_code = _normalized_optional(args.blocker_code)
    blocker_summary = _normalized_optional(args.blocker_summary)
    if status == "blocked" and (not blocker_code or not blocker_summary):
        raise ReceiptScaffoldError("blocked status requires both --blocker-code and --blocker-summary.")

    receipt_context = _normalized_optional(args.receipt_context)
    if receipt_context is not None:
        receipt_context = _validate_relative_ref(receipt_context, field_name="receipt_context")

    output_ref = _normalized_optional(args.output)
    if output_ref is not None:
        output_ref = _validate_relative_ref(output_ref, field_name="output")

    return ReceiptScaffoldInput(
        title=_non_empty(args.title, field_name="title"),
        lane=_non_empty(args.lane, field_name="lane"),
        date=_non_empty(args.date, field_name="date"),
        status=status,
        objective=_normalized_optional(args.objective) or PLACEHOLDER_OBJECTIVE,
        scope=_normalized_optional(args.scope) or PLACEHOLDER_SCOPE,
        receipt_context=receipt_context,
        blocker_code=blocker_code,
        blocker_summary=blocker_summary,
        marker_decision=_normalized_optional(args.marker_decision) or DEFAULT_MARKER_DECISION,
        verification_lines=_normalize_lines(args.verification, default=PLACEHOLDER_VERIFICATION),
        protected_surfaces=_normalize_surfaces(args.protected_surface),
        output_ref=output_ref,
    )


def run_receipt_package_contract(*, root: Path, lane: str, receipt_context: str | None = None) -> dict[str, Any]:
    script_path = root / "repos" / "_stack" / "scripts" / "receipt-package.mjs"
    if not script_path.exists():
        raise ReceiptScaffoldError(f"Required _stack helper surface is missing: {atlas_relative(script_path, root=root)}")

    command = ["node", str(script_path), "--format", "json", "--lane", lane]
    if receipt_context:
        command.extend(["--receipt-context", receipt_context])

    completed = subprocess.run(
        command,
        cwd=str(root),
        capture_output=True,
        text=True,
        check=False,
        env={
            **os.environ,
            "STACK_RECEIPT_PACKAGE_WORKSPACE_ROOT": str(root),
        },
    )

    stdout = completed.stdout.strip()
    try:
        payload = json.loads(stdout) if stdout else None
    except json.JSONDecodeError as exc:
        raise ReceiptScaffoldError(
            "The _stack receipt-package helper returned non-JSON output.\n"
            f"stdout:\n{completed.stdout}\n"
            f"stderr:\n{completed.stderr}"
        ) from exc

    if not isinstance(payload, dict):
        raise ReceiptScaffoldError(
            "The _stack receipt-package helper failed without a usable contract payload.\n"
            f"stdout:\n{completed.stdout}\n"
            f"stderr:\n{completed.stderr}"
        )

    if payload.get("ok") is True:
        report = payload.get("report")
        if not isinstance(report, dict):
            raise ReceiptScaffoldError("The _stack receipt-package helper did not return a report payload.")
        return report

    report = payload.get("report")
    if completed.returncode != 0 and isinstance(report, dict):
        if str(report.get("failure_code") or "") == "receipt-basis-unavailable":
            return report

    if completed.returncode != 0 or payload.get("ok") is not True:
        if isinstance(report, dict):
            failure_code = str(report.get("failure_code") or "unknown")
            message = str(report.get("message") or "Receipt-package contract failed.")
            raise ReceiptScaffoldError(f"{failure_code}: {message}")
        raise ReceiptScaffoldError(
            "The _stack receipt-package helper failed without a usable contract payload.\n"
            f"stdout:\n{completed.stdout}\n"
            f"stderr:\n{completed.stderr}"
        )
    raise ReceiptScaffoldError("The _stack receipt-package helper returned an unexpected state.")


def render_receipt_scaffold(
    scaffold_input: ReceiptScaffoldInput,
    contract_report: dict[str, Any],
) -> str:
    authoritative_refs = tuple(
        str(item).strip()
        for item in contract_report.get("authoritative_refs", [])
        if isinstance(item, str) and item.strip()
    )
    next_package = str(contract_report.get("next_package") or "").strip() or PLACEHOLDER_NEXT_PACKAGE
    package_mode = str(contract_report.get("package_mode") or "draft-skeleton-with-placeholders").strip()
    context_status = str(contract_report.get("context_status") or "placeholder-fallback").strip()
    routing_note = str(contract_report.get("routing_note") or "").strip()
    marker_percentage = str(contract_report.get("marker_percentage") or "").strip()
    supporting_posture = str(contract_report.get("supporting_posture") or "").strip()
    context_fallback_reason = str(contract_report.get("context_fallback_reason") or "").strip()
    receipt_context = str(contract_report.get("receipt_context") or "").strip()
    failure_scope = str(contract_report.get("failure_scope") or "").strip()
    contradiction_note = contract_report.get("contradiction_note")
    objective = (
        scaffold_input.objective
        if scaffold_input.objective != PLACEHOLDER_OBJECTIVE
        else _default_objective(lane=scaffold_input.lane, status=scaffold_input.status)
    )
    scope = (
        scaffold_input.scope
        if scaffold_input.scope != PLACEHOLDER_SCOPE
        else _default_scope(
            next_package=next_package,
            marker_percentage=marker_percentage,
            supporting_posture=supporting_posture,
            status=scaffold_input.status,
        )
    )
    verification_lines = (
        scaffold_input.verification_lines
        if scaffold_input.verification_lines != (PLACEHOLDER_VERIFICATION,)
        else _default_verification_lines()
    )

    lines: list[str] = [
        f"# {scaffold_input.title}",
        "",
        f"- Date: `{scaffold_input.date}`",
        f"- Lane: `{scaffold_input.lane}`",
        f"- Mode: `{DEFAULT_MODE}`",
        f"- Status: `{scaffold_input.status}`",
        f"- Helper: `ops/atlas/receipt_scaffold.py`",
        f"- Source contract: `{STACK_COMMAND_ID}`",
        "",
        "## Objective",
        "",
        objective,
        "",
        "## Scope",
        "",
        scope,
        "",
        "## Source Surfaces",
        "",
    ]
    for ref in authoritative_refs:
        lines.append(f"- `{ref}`")
    if receipt_context:
        lines.append(f"- `{receipt_context}`")

    lines.extend(
        [
            "",
            "## Receipt Basis",
            "",
            f"- package mode: `{package_mode}`",
            f"- context status: `{context_status}`",
        ]
    )
    if marker_percentage:
        lines.append(f"- current marker posture: `{marker_percentage}`")
    if supporting_posture:
        lines.append(f"- supporting posture: `{supporting_posture}`")
    if context_fallback_reason:
        lines.append(f"- context fallback reason: `{context_fallback_reason}`")
    if failure_scope:
        lines.append(f"- fallback scope: `{failure_scope}`")
    if routing_note:
        lines.append(f"- routing note: `{routing_note}`")
    if isinstance(contradiction_note, dict):
        contradiction_scope = str(contradiction_note.get("contradiction_scope") or "").strip()
        conflicting_refs = [
            str(item).strip()
            for item in contradiction_note.get("conflicting_refs", [])
            if isinstance(item, str) and item.strip()
        ]
        if contradiction_scope:
            lines.append(f"- contradiction scope: `{contradiction_scope}`")
        if conflicting_refs:
            lines.append("- conflicting refs:")
            for ref in conflicting_refs:
                lines.append(f"  - `{ref}`")

    if scaffold_input.status == "blocked":
        lines.extend(
            [
                "",
                "## Blocker",
                "",
                f"- blocker code: `{scaffold_input.blocker_code}`",
                f"- blocker summary: {scaffold_input.blocker_summary}",
            ]
        )

    lines.extend(["", "## Verification", ""])
    for item in verification_lines:
        lines.append(f"- {item}")

    lines.extend(["", "## Marker Decision", "", f"- `{scaffold_input.marker_decision}`"])

    lines.extend(["", "## Protected Surfaces Not Touched", ""])
    for surface in scaffold_input.protected_surfaces:
        lines.append(f"- `{surface}`")

    lines.extend(["", "## Exact Next Package", "", f"- `{next_package}`"])

    lines.extend(
        [
            "",
            "## Stop Conditions",
            "",
            "- draft-only structure does not imply doctrine admission, publication readiness, deploy readiness, or final proof",
            "- marker movement stays `none` unless an explicit operator-provided marker decision is passed",
            "- protected surfaces remain out of scope for this scaffold pass",
        ]
    )
    if scaffold_input.status == "blocked":
        lines.append("- stop after preserving the blocker receipt until the blocker class materially changes")

    return "\n".join(lines).rstrip() + "\n"


def write_scaffold(*, root: Path, output_ref: str, body: str, force: bool = False) -> Path:
    output_path = (root / output_ref).resolve()
    if output_path.exists() and not force:
        raise ReceiptScaffoldError(f"Output already exists: {atlas_relative(output_path, root=root)}")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(body, encoding="utf-8")
    return output_path


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Render a deterministic ATLAS draft receipt scaffold from the admitted _stack receipt-package contract.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    scaffold = subparsers.add_parser("scaffold", help="Render one draft-only operator-usable receipt scaffold.")
    scaffold.add_argument("--root", type=Path, default=atlas_root())
    scaffold.add_argument("--title", required=True)
    scaffold.add_argument("--lane", required=True)
    scaffold.add_argument("--date", required=True)
    scaffold.add_argument("--status", default=DEFAULT_STATUS, choices=("normal", "blocked"))
    scaffold.add_argument("--objective")
    scaffold.add_argument("--scope")
    scaffold.add_argument("--receipt-context")
    scaffold.add_argument("--blocker-code")
    scaffold.add_argument("--blocker-summary")
    scaffold.add_argument("--marker-decision", default=DEFAULT_MARKER_DECISION)
    scaffold.add_argument("--verification", action="append")
    scaffold.add_argument("--protected-surface", action="append")
    scaffold.add_argument("--output")
    scaffold.add_argument("--force", action="store_true")
    return parser


def main(
    argv: list[str] | None = None,
    *,
    contract_loader: Callable[..., dict[str, Any]] = run_receipt_package_contract,
) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.command != "scaffold":
        raise SystemExit("Unsupported command.")

    try:
        scaffold_input = build_input(args)
        root = args.root.resolve()
        contract_report = contract_loader(
            root=root,
            lane=scaffold_input.lane,
            receipt_context=scaffold_input.receipt_context,
        )
        body = render_receipt_scaffold(scaffold_input, contract_report)
        if scaffold_input.output_ref:
            output_path = write_scaffold(
                root=root,
                output_ref=scaffold_input.output_ref,
                body=body,
                force=bool(args.force),
            )
            print(json.dumps(
                {
                    "contract_version": HELPER_VERSION,
                    "output_ref": atlas_relative(output_path, root=root),
                    "lane": scaffold_input.lane,
                    "status": scaffold_input.status,
                    "marker_decision": scaffold_input.marker_decision,
                },
                indent=2,
            ))
            return 0

        sys.stdout.write(body)
        return 0
    except ReceiptScaffoldError as exc:
        print(str(exc), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
