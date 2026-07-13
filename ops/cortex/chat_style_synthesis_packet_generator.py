from __future__ import annotations

"""Build a deterministic, evidence-aware, advisory Cortex synthesis packet.

This module deliberately has no network client, executor, queue, or scheduler.
It reads only explicitly named governed root files and writes only explicit
``tmp/atlas/**`` artifacts.
"""

import argparse
import hashlib
import json
import re
import subprocess
import sys
from collections import OrderedDict
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from ops._atlas import atlas_root, normalize_slashes

SCHEMA_VERSION = "atlas.cortex.chat_style_synthesis_packet.v1"
STATUSES = ("ok", "advisory_gap", "conflict", "blocker", "internal_error")
MODES = ("strategy", "architecture", "decision", "research", "handoff")
TRUST_CLASSES = (
    "verified_fact",
    "receipt_backed",
    "manifest_backed",
    "git_backed",
    "validation_backed",
    "reasoned_inference",
    "operator_assumption",
    "unverified",
    "conflicted",
    "forbidden",
)
TOP_LEVEL_FIELDS = (
    "schema_version",
    "status",
    "root",
    "branch",
    "head",
    "mode",
    "source_refs",
    "source_digests",
    "trust_summary",
    "synthesis_packet",
    "options",
    "recommendation",
    "evidence_gaps",
    "risk_register",
    "playbook_refs",
    "marker_impacts",
    "codex_handoff",
    "authority_denials",
    "warnings",
    "blockers",
    "safe_to_use",
    "next_recommended_packet",
)
SYNTHESIS_PACKET_FIELDS = (
    "title",
    "packet_id",
    "captured_at",
    "source_refs",
    "source_digests",
    "decision_problem",
    "current_state",
    "objective",
    "constraints",
    "facts",
    "inferences",
    "assumptions",
    "evidence_gaps",
    "options",
    "tradeoffs",
    "recommended_option",
    "rejected_options",
    "risk_register",
    "playbook_rule_refs",
    "pattern_refs",
    "failure_mode_refs",
    "marker_impacts",
    "authority_boundaries",
    "codex_handoff",
    "verification_requirements",
    "next_recommended_packet",
)
OPTION_FIELDS = (
    "option_id",
    "description",
    "benefits",
    "costs",
    "risks",
    "proof_available",
    "external_input_required",
    "authority_required",
    "score",
    "rejection_reason",
)
AUTHORITY_DENIALS = (
    "no repo mutation authority beyond explicitly requested helper outputs",
    "no stage, commit, push, or PR approval authority",
    "no deploy or platform mutation authority",
    "no secret or environment-file access",
    "no hidden transcript scraping or private reasoning inference",
    "no unrestricted owner-repo reads",
    "no live external system queries or network requirement",
    "no marker movement authority",
    "no final authoritative receipt, manifest, or Book authority",
    "no packet execution, Codex invocation, or workflow dispatch",
    "no custom SQLite execution queue or scheduler implementation",
    "no model training or fine-tuning",
)
ALLOWED_FILES = (
    "ops/cortex/chat_style_synthesis_packet_generator.py",
    "tests/test_cortex_chat_style_synthesis_packet_generator.py",
)
FORBIDDEN_FILES = (
    "docs/**",
    "stack.yaml",
    "stack.lock.yaml",
    "repos/**",
    "packages/**",
    "runtime/**",
    "secrets/**",
)
NEXT_PACKET = "Cortex Dual-Mode Replacement Readiness chat-style synthesis packet generation first-implementation worker cluster reconciliation"
PROTECTED_PARTS = {"repos", "secrets", ".vercel", ".playwright-mcp", "archive", "runtime", ".codex"}
LIVE_TOKENS = ("vercel", "supabase", "discord", "github", "network", "api", "live-")


def _finding(code: str, message: str, **details: Any) -> OrderedDict[str, Any]:
    value: OrderedDict[str, Any] = OrderedDict((("code", code), ("message", message)))
    if details:
        value["details"] = OrderedDict(sorted(details.items()))
    return value


def _git_stdout(root: Path, *args: str) -> str | None:
    result = subprocess.run(
        ["git", "-C", str(root), *args], check=False, capture_output=True,
        text=True, encoding="utf-8", errors="replace"
    )
    return result.stdout.strip() if result.returncode == 0 else None


def collect_git_state(root: Path) -> tuple[str | None, str | None]:
    return _git_stdout(root, "branch", "--show-current"), _git_stdout(root, "rev-parse", "HEAD")


def _ref(value: str | Path) -> str:
    return normalize_slashes(str(value)).strip("/")


def _forbidden_source(ref: str) -> tuple[str, str] | None:
    lowered = ref.lower()
    parts = lowered.split("/")
    if any(part.startswith(".env") for part in parts):
        return "environment_source_forbidden", "Environment-file sources are forbidden."
    if any(part in PROTECTED_PARTS for part in parts):
        if "repos" in parts:
            return "owner_repo_source_forbidden", "Owner-repo sources are forbidden."
        return "protected_source_forbidden", "Protected sources are forbidden."
    if "transcript" in lowered or "conversation" in lowered or "chain-of-thought" in lowered or "private-reasoning" in lowered:
        return "transcript_source_forbidden", "Hidden transcript or private reasoning sources are forbidden."
    if any(token in lowered for token in LIVE_TOKENS):
        return "live_external_source_forbidden", "Live external, network, or API sources are forbidden."
    if any(token in lowered for token in ("customer", "health", "payment", "account-data", "browser-profile")):
        return "sensitive_source_forbidden", "Raw sensitive or browser-profile sources are forbidden."
    return None


def validate_source_path(root: Path, source: str) -> tuple[str | None, OrderedDict[str, Any] | None]:
    candidate = Path(source)
    if candidate.is_absolute():
        return None, _finding("absolute_source_path", "Source path must be root-relative.", path=normalize_slashes(str(candidate)))
    ref = _ref(source)
    if not ref or ref.startswith("../") or "/../" in f"/{ref}/":
        return None, _finding("source_parent_traversal", "Source path must not use parent traversal.", path=ref)
    forbidden = _forbidden_source(ref)
    if forbidden is not None:
        return None, _finding(forbidden[0], forbidden[1], path=ref)
    if not (ref.startswith("docs/") or ref.startswith("tmp/atlas/")):
        return None, _finding("source_not_admitted", "Source is outside admitted root-owned source classes.", path=ref)
    resolved = (root / ref).resolve()
    try:
        resolved.relative_to(root.resolve())
    except ValueError:
        return None, _finding("source_outside_root", "Source path must stay inside the ATLAS root.", path=ref)
    return ref, None


def validate_output_path(root: Path, output: str, suffix: str) -> tuple[Path | None, OrderedDict[str, Any] | None]:
    candidate = Path(output)
    if candidate.is_absolute():
        return None, _finding("absolute_output_path", "Output path must be root-relative.", path=normalize_slashes(str(candidate)))
    ref = _ref(output)
    if not ref or ref.startswith("../") or "/../" in f"/{ref}/":
        return None, _finding("outside_root_output_path", "Output path must stay inside the ATLAS root.", path=ref)
    if not ref.startswith("tmp/atlas/"):
        return None, _finding("unsafe_output_path", "Output path must be under tmp/atlas/**.", path=ref)
    if not ref.endswith(suffix):
        return None, _finding("output_suffix_invalid", f"Output path must end with {suffix}.", path=ref)
    if _forbidden_source(ref) is not None:
        return None, _finding("protected_output_path", "Output path targets a protected surface.", path=ref)
    resolved = (root / ref).resolve()
    try:
        resolved.relative_to(root.resolve())
    except ValueError:
        return None, _finding("outside_root_output_path", "Output path must stay inside the ATLAS root.", path=ref)
    return resolved, None


def _trust_for_ref(ref: str) -> str:
    if ref.startswith("docs/ops/"):
        return "receipt_backed"
    if ref.startswith("docs/memory/initiatives/"):
        return "manifest_backed"
    if "validation" in ref:
        return "validation_backed"
    if ref.startswith("tmp/atlas/"):
        return "unverified"
    return "verified_fact"


def _statement(statement_id: str, text: str, trust_class: str, refs: list[str], digests: list[str]) -> OrderedDict[str, Any]:
    return OrderedDict(
        (("statement_id", statement_id), ("text", text), ("trust_class", trust_class),
         ("source_refs", refs), ("source_digests", digests))
    )


def _source_entries(root: Path, requested: list[str]) -> tuple[list[tuple[str, str, str]], list[OrderedDict[str, Any]], list[OrderedDict[str, Any]]]:
    entries: list[tuple[str, str, str]] = []
    warnings: list[OrderedDict[str, Any]] = []
    blockers: list[OrderedDict[str, Any]] = []
    seen: set[str] = set()
    for source in requested:
        ref, error = validate_source_path(root, source)
        if error is not None:
            blockers.append(error)
            continue
        assert ref is not None
        if ref in seen:
            continue
        seen.add(ref)
        path = (root / ref).resolve()
        if not path.is_file():
            blockers.append(_finding("source_missing", "Explicit admitted source is missing or not a file.", path=ref))
            continue
        try:
            text = path.read_text(encoding="utf-8-sig")
        except UnicodeDecodeError:
            blockers.append(_finding("source_not_text", "Admitted source must be UTF-8 text or JSON.", path=ref))
            continue
        entries.append((ref, hashlib.sha256(text.encode("utf-8")).hexdigest(), text))
    entries.sort(key=lambda item: item[0])
    return entries, warnings, blockers


def _claim_conflicts(entries: list[tuple[str, str, str]]) -> list[OrderedDict[str, Any]]:
    values: dict[str, list[tuple[str, Any]]] = {}
    for ref, _digest, text in entries:
        try:
            document = json.loads(text)
        except json.JSONDecodeError:
            continue
        claims = document.get("claims", []) if isinstance(document, dict) else []
        if not isinstance(claims, list):
            continue
        for claim in claims:
            if not isinstance(claim, dict):
                continue
            name = claim.get("claim", claim.get("field"))
            if not isinstance(name, str) or "value" not in claim:
                continue
            values.setdefault(name, []).append((ref, claim["value"]))
    conflicts: list[OrderedDict[str, Any]] = []
    for name in sorted(values):
        claimed = values[name]
        distinct = {json.dumps(value, sort_keys=True, ensure_ascii=False) for _ref_name, value in claimed}
        if len(distinct) > 1:
            refs = sorted(ref for ref, _value in claimed)
            conflicts.append(OrderedDict((("claim", name), ("source_refs", refs), ("classification", "conflicted"))))
    return conflicts


def _doctrine_refs(entries: list[tuple[str, str, str]]) -> tuple[list[OrderedDict[str, Any]], list[OrderedDict[str, Any]], list[OrderedDict[str, Any]]]:
    found: dict[str, list[OrderedDict[str, Any]]] = {"rule": [], "pattern": [], "failure_mode": []}
    matcher = re.compile(r"(?:^|\n)\s*-?\s*(RULE|PATTERN|FAILURE MODE)\s*-\s*([^\n]+)", re.IGNORECASE)
    for ref, _digest, text in entries:
        for kind, title in matcher.findall(text):
            key = {"rule": "rule", "pattern": "pattern", "failure mode": "failure_mode"}[kind.lower()]
            item = OrderedDict((("ref", ref), ("title", title.strip()), ("doctrine_only", True)))
            if item not in found[key]:
                found[key].append(item)
    return found["rule"], found["pattern"], found["failure_mode"]


def _options(mode: str, safe: bool) -> list[OrderedDict[str, Any]]:
    primary = OrderedDict(
        (("option_id", "bounded-advisory-synthesis"),
         ("description", f"Generate one deterministic {mode} advisory packet from the admitted evidence."),
         ("benefits", ["preserves provenance", "keeps execution separate"]),
         ("costs", ["does not execute work"]),
         ("risks", ["evidence may be incomplete"]),
         ("proof_available", safe), ("external_input_required", False), ("authority_required", False),
         ("score", 1 if safe else 0), ("rejection_reason", None))
    )
    rejected = OrderedDict(
        (("option_id", "unbounded-execution"),
         ("description", "Execute or broaden work directly from chat-style synthesis."),
         ("benefits", []), ("costs", ["violates the synthesis-only boundary"]),
         ("risks", ["would bypass governance"]),
         ("proof_available", False), ("external_input_required", True), ("authority_required", True),
         ("score", 0), ("rejection_reason", "Rejected: packet generation has no execution or authority-bearing role."))
    )
    return [primary, rejected]


def _handoff(mode: str) -> OrderedDict[str, Any]:
    return OrderedDict(
        (("objective", f"Review the bounded {mode} advisory packet; do not execute it automatically."),
         ("allowed_files", list(ALLOWED_FILES)), ("forbidden_files", list(FORBIDDEN_FILES)),
         ("verification_commands", ["python -m unittest tests.test_cortex_chat_style_synthesis_packet_generator -v", "python ops/validation/validate_stack.py", "git diff --check"]),
         ("stop_conditions", ["Stop if a third committed path is required.", "Stop if any denied authority, live query, secret, owner-repo read, or execution is required."]),
         ("authority_denials", list(AUTHORITY_DENIALS)),
         ("expected_output_paths", list(ALLOWED_FILES)), ("automatic_execution", False),
         ("execution_authorized", False), ("completion_claimed", False))
    )


def build_packet(*, root: Path | None = None, sources: list[str] | None = None, mode: str = "strategy") -> OrderedDict[str, Any]:
    base = (root or atlas_root()).resolve()
    requested = list(sources or [])
    warnings: list[OrderedDict[str, Any]] = []
    entries, source_warnings, blockers = _source_entries(base, requested)
    warnings.extend(source_warnings)
    if mode not in MODES:
        blockers.append(_finding("invalid_mode", "Mode must be one of the frozen synthesis modes.", mode=mode))
    if not requested:
        blockers.append(_finding("source_required", "At least one explicit admitted source is required."))
    conflicts = _claim_conflicts(entries)
    refs = [ref for ref, _digest, _text in entries]
    digests = [OrderedDict((("ref", ref), ("sha256", digest))) for ref, digest, _text in entries]
    branch, head = collect_git_state(base)
    facts = [_statement(f"source-{index + 1}", f"Explicit governed source {ref} was read.", _trust_for_ref(ref), [ref], [digest]) for index, (ref, digest, _text) in enumerate(entries)]
    inferences = [_statement("bounded-synthesis", "The packet is advisory synthesis and is not execution authority.", "reasoned_inference", refs, [item["sha256"] for item in digests])]
    assumptions = [_statement("operator-intent", "The operator intends one bounded, non-executing packet for the selected mode.", "operator_assumption", [], [])]
    evidence_gaps: list[OrderedDict[str, Any]] = []
    if len(entries) < 2 and not blockers:
        evidence_gaps.append(_statement("limited-evidence", "Fewer than two admitted sources cannot fully prove the decision context.", "unverified", refs, [item["sha256"] for item in digests]))
    for conflict in conflicts:
        inferences.append(_statement(f"conflict-{conflict['claim']}", f"Contradictory evidence exists for {conflict['claim']}.", "conflicted", list(conflict["source_refs"]), []))
    for blocker in blockers:
        if blocker["code"].endswith("forbidden") or blocker["code"] == "owner_repo_source_forbidden":
            inferences.append(_statement(f"forbidden-{blocker['code']}", blocker["message"], "forbidden", [], []))
    rule_refs, pattern_refs, failure_mode_refs = _doctrine_refs(entries)
    advisory_marker = [OrderedDict((("marker", "Cortex Dual-Mode Replacement Readiness"), ("impact", "Advisory only; no marker movement is authorized."), ("advisory_only", True)))]
    provisional_safe = not blockers and not conflicts and not evidence_gaps
    options = _options(mode, provisional_safe)
    recommendation: OrderedDict[str, Any] | None = None
    if provisional_safe:
        recommendation = OrderedDict((("option_id", "bounded-advisory-synthesis"), ("reason", "The admitted evidence supports one deterministic non-executing recommendation.")))
    risks = [OrderedDict((("risk_id", "evidence-boundary"), ("description", "Unadmitted or incomplete evidence must not be promoted to fact."), ("mitigation", "Preserve provenance, gaps, and stop conditions.")))]
    packet_seed = json.dumps(OrderedDict((("mode", mode), ("sources", digests))), ensure_ascii=False, separators=(",", ":"))
    packet_id = "cortex-chat-style-" + hashlib.sha256(packet_seed.encode("utf-8")).hexdigest()[:16]
    status = "blocker" if blockers else "conflict" if conflicts else "advisory_gap" if evidence_gaps else "ok"
    safe = status == "ok"
    handoff = _handoff(mode)
    tradeoffs = [OrderedDict((("option_id", option["option_id"]), ("benefits", option["benefits"]), ("costs", option["costs"]), ("risks", option["risks"]))) for option in options]
    synthesis = OrderedDict(
        (("title", f"Cortex chat-style {mode} synthesis packet"), ("packet_id", packet_id),
         ("captured_at", "deterministic:" + packet_id.rsplit("-", 1)[-1]), ("source_refs", refs), ("source_digests", digests),
         ("decision_problem", "Choose one evidence-bound, advisory next-step framing without execution."),
         ("current_state", "Only explicitly supplied governed root sources are considered."),
         ("objective", f"Produce deterministic {mode} synthesis with one bounded Codex handoff."),
         ("constraints", ["root-relative admitted inputs only", "no execution", "no network requirement"]),
         ("facts", facts), ("inferences", inferences), ("assumptions", assumptions), ("evidence_gaps", evidence_gaps),
         ("options", options), ("tradeoffs", tradeoffs), ("recommended_option", recommendation),
         ("rejected_options", [option for option in options if option["rejection_reason"]]), ("risk_register", risks),
         ("playbook_rule_refs", rule_refs), ("pattern_refs", pattern_refs), ("failure_mode_refs", failure_mode_refs),
         ("marker_impacts", advisory_marker), ("authority_boundaries", list(AUTHORITY_DENIALS)),
         ("codex_handoff", handoff),
         ("verification_requirements", handoff["verification_commands"]), ("next_recommended_packet", NEXT_PACKET))
    )
    statements = facts + inferences + assumptions + evidence_gaps
    trust_summary = [OrderedDict((("trust_class", trust), ("statement_count", sum(1 for statement in statements if statement["trust_class"] == trust)))) for trust in TRUST_CLASSES]
    return OrderedDict(
        (("schema_version", SCHEMA_VERSION), ("status", status), ("root", normalize_slashes(str(base))), ("branch", branch), ("head", head),
         ("mode", mode), ("source_refs", refs), ("source_digests", digests), ("trust_summary", trust_summary),
         ("synthesis_packet", synthesis), ("options", options), ("recommendation", recommendation), ("evidence_gaps", evidence_gaps),
         ("risk_register", risks), ("playbook_refs", OrderedDict((("rules", rule_refs), ("patterns", pattern_refs), ("failure_modes", failure_mode_refs), ("doctrine_is_not_implementation_proof", True)))),
         ("marker_impacts", advisory_marker), ("codex_handoff", handoff), ("authority_denials", list(AUTHORITY_DENIALS)),
         ("warnings", warnings), ("blockers", blockers), ("safe_to_use", safe), ("next_recommended_packet", NEXT_PACKET))
    )


def build_schema_only_payload(*, root: Path | None = None, mode: str = "strategy") -> OrderedDict[str, Any]:
    base = (root or atlas_root()).resolve()
    branch, head = collect_git_state(base)
    packet_id = "cortex-chat-style-schema-only"
    handoff = _handoff(mode)
    synthesis = OrderedDict((field, [] if field in {"source_refs", "source_digests", "facts", "inferences", "assumptions", "evidence_gaps", "options", "tradeoffs", "rejected_options", "risk_register", "playbook_rule_refs", "pattern_refs", "failure_mode_refs", "marker_impacts", "authority_boundaries", "verification_requirements"} else None) for field in SYNTHESIS_PACKET_FIELDS)
    synthesis.update(OrderedDict((("title", "Cortex chat-style synthesis packet schema"), ("packet_id", packet_id), ("captured_at", "deterministic:schema-only"), ("codex_handoff", handoff), ("next_recommended_packet", NEXT_PACKET))))
    return OrderedDict(
        (("schema_version", SCHEMA_VERSION), ("status", "ok"), ("root", normalize_slashes(str(base))), ("branch", branch), ("head", head), ("mode", mode),
         ("source_refs", []), ("source_digests", []), ("trust_summary", [OrderedDict((("trust_class", trust), ("statement_count", 0))) for trust in TRUST_CLASSES]),
         ("synthesis_packet", synthesis), ("options", []), ("recommendation", None), ("evidence_gaps", []), ("risk_register", []),
         ("playbook_refs", OrderedDict((("rules", []), ("patterns", []), ("failure_modes", []), ("doctrine_is_not_implementation_proof", True)))),
         ("marker_impacts", []), ("codex_handoff", handoff), ("authority_denials", list(AUTHORITY_DENIALS)), ("warnings", []), ("blockers", []), ("safe_to_use", True), ("next_recommended_packet", NEXT_PACKET))
    )


def render_markdown(payload: OrderedDict[str, Any]) -> str:
    packet = payload["synthesis_packet"]
    lines = ["# Cortex Chat-Style Synthesis Packet", "", f"- Schema: `{payload['schema_version']}`", f"- Status: `{payload['status']}`", f"- Mode: `{payload['mode']}`", f"- Packet: `{packet['packet_id']}`", "", "## Sources", ""]
    lines.extend(f"- `{ref}`" for ref in payload["source_refs"])
    lines.extend(["", "## Recommendation", "", (f"- `{payload['recommendation']['option_id']}`: {payload['recommendation']['reason']}" if payload["recommendation"] else "- No recommendation: advisory evidence is incomplete or conflicted."), "", "## Codex Handoff", "", f"Objective: {payload['codex_handoff']['objective']}", "", "Allowed files:"])
    lines.extend(f"- `{path}`" for path in payload["codex_handoff"]["allowed_files"])
    lines.extend(["", "Authority denials:"])
    lines.extend(f"- {denial}" for denial in payload["authority_denials"])
    return "\n".join(lines) + "\n"


def _write_if_admitted(root: Path, argument: str | None, suffix: str, content: str, payload: OrderedDict[str, Any]) -> None:
    if argument is None:
        return
    path, error = validate_output_path(root, argument, suffix)
    if error is not None:
        payload["status"] = "blocker"
        payload["blockers"] = list(payload["blockers"]) + [error]
        payload["safe_to_use"] = False
        return
    assert path is not None
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def exit_code(status: str, *, strict: bool) -> int:
    if status in {"ok", "advisory_gap"}:
        return 0
    if status == "conflict":
        return 2 if strict else 0
    return 2 if status == "blocker" else 3


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Generate an advisory Cortex chat-style synthesis packet.")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--source", action="append", default=[])
    parser.add_argument("--mode", choices=MODES, default="strategy")
    parser.add_argument("--output")
    parser.add_argument("--markdown-output")
    parser.add_argument("--strict", action="store_true")
    parser.add_argument("--schema-only", action="store_true")
    args = parser.parse_args(argv)
    root = atlas_root().resolve()
    try:
        payload = build_schema_only_payload(root=root, mode=args.mode) if args.schema_only else build_packet(root=root, sources=list(args.source), mode=args.mode)
        _write_if_admitted(root, args.output, ".json", json.dumps(payload, indent=2, ensure_ascii=False) + "\n", payload)
        _write_if_admitted(root, args.markdown_output, ".md", render_markdown(payload), payload)
        print(json.dumps(payload, indent=2, ensure_ascii=False) if args.json else render_markdown(payload), end="" if not args.json else "\n")
        return exit_code(str(payload["status"]), strict=args.strict)
    except Exception as exc:
        fallback = build_schema_only_payload(root=root, mode=args.mode)
        fallback["status"] = "internal_error"
        fallback["blockers"] = [_finding("internal_error", "Packet generation failed before completion.", exception=str(exc))]
        fallback["safe_to_use"] = False
        print(json.dumps(fallback, indent=2, ensure_ascii=False) if args.json else render_markdown(fallback), end="" if not args.json else "\n")
        return 3


if __name__ == "__main__":
    raise SystemExit(main())
