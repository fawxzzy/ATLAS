from __future__ import annotations

import argparse
import json
import re
import sys
from collections import OrderedDict
from pathlib import Path
from typing import Any, Iterable

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from ops._atlas import atlas_root, normalize_slashes
from ops.atlas.marker_knockout_selector import build_campaign
from ops.stack.generate_lockfile import git_output

SCHEMA_VERSION = "atlas.playbook_adoption_matrix.v1"
STATUS_OK = "ok"
STATUS_ADVISORY = "advisory_gap"
STATUS_BLOCKER = "blocker"
STATUS_INTERNAL_ERROR = "internal_error"
SCOPES = {"owner", "platform", "research", "root"}
PROTECTED_OUTPUT_PREFIXES = {
    ".playwright-mcp",
    ".vercel",
    "archive",
    "repos",
    "runtime",
    "secrets",
}
SOURCE_REFS = (
    "docs/PLAYBOOK_NOTES.md",
    "docs/ops/PLAYBOOK-ADOPTION-MATRIX.md",
    "docs/architecture/ATLAS-CORTEX-PLAYBOOK-CODEX.md",
    "docs/standards/WORKER-ORCHESTRATION.md",
)
CONSUMER_REFS = (
    "docs/atlas-book/01-current-state.md",
    "docs/atlas-book/02-lanes-and-markers.md",
    "docs/registry/STACK-REPO-INVENTORY.json",
    "docs/audits/STACK-REPO-INVENTORY.md",
    "stack.yaml",
    "stack.lock.yaml",
)
TEXT_SUFFIXES = {".json", ".md", ".py", ".toml", ".yaml", ".yml"}
CONSUMER_TERMS = (
    "adoption matrix",
    "consumer",
    "consumes",
    "continuity",
    "handoff",
    "manifest",
    "packet",
    "projection",
    "receipt",
    "restart",
    "routes",
)
ENFORCEMENT_TERMS = (
    "blocker",
    "command",
    "enforce",
    "gate",
    "must",
    "selector",
    "test",
    "validate",
    "validator",
)
CORTEX_TERMS = (
    "curated-data boundary",
    "failure mode",
    "handoff example",
    "pattern",
    "prompt-governance",
    "rule",
)


def _read_text(path: Path) -> str | None:
    if not path.exists() or not path.is_file():
        return None
    try:
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return path.read_text(encoding="utf-8", errors="ignore")


def _read_json(path: Path) -> dict[str, Any] | None:
    text = _read_text(path)
    if text is None:
        return None
    try:
        payload = json.loads(text)
    except json.JSONDecodeError:
        return None
    return payload if isinstance(payload, dict) else None


def _git_stdout(repo_root: Path, *args: str) -> tuple[int, str]:
    code, stdout = git_output(repo_root, *args)
    return code, stdout.strip()


def _git_lines(repo_root: Path, *args: str) -> list[str]:
    code, stdout = _git_stdout(repo_root, *args)
    if code != 0 or not stdout:
        return []
    return [line.strip() for line in stdout.splitlines() if line.strip()]


def _finding(code: str, message: str, *, severity: str = "advisory", **details: Any) -> OrderedDict[str, Any]:
    payload: OrderedDict[str, Any] = OrderedDict([("code", code), ("severity", severity), ("message", message)])
    if details:
        payload["details"] = details
    return payload


def _protected_path(relative_path: str) -> bool:
    normalized = normalize_slashes(relative_path).strip("/")
    if not normalized:
        return True
    first = normalized.split("/", 1)[0]
    if first in PROTECTED_OUTPUT_PREFIXES:
        return True
    if first.startswith(".env"):
        return True
    filename = normalized.rsplit("/", 1)[-1]
    return filename.startswith(".env")


def validate_output_path(*, root: Path, output_path: str) -> tuple[Path | None, dict[str, Any] | None]:
    candidate = Path(output_path)
    if candidate.is_absolute():
        return None, _finding(
            "absolute_output_path",
            "Output path must be root-relative.",
            severity="blocker",
            path=normalize_slashes(str(candidate)),
        )
    relative_path = normalize_slashes(str(candidate))
    if _protected_path(relative_path):
        return None, _finding(
            "protected_output_path",
            "Output path targets a protected surface.",
            severity="blocker",
            path=relative_path,
        )
    resolved = (root / candidate).resolve()
    try:
        resolved.relative_to(root.resolve())
    except ValueError:
        return None, _finding(
            "outside_root_output_path",
            "Output path must stay inside the ATLAS root.",
            severity="blocker",
            path=relative_path,
        )
    return resolved, None


def collect_branch_state(root: Path) -> OrderedDict[str, Any]:
    branch_code, branch = _git_stdout(root, "branch", "--show-current")
    head_code, head = _git_stdout(root, "rev-parse", "HEAD")
    branch_name = branch if branch_code == 0 and branch else None
    remote_tracking = f"origin/{branch_name}" if branch_name else None
    behind = ahead = None
    parity_status = "unavailable"
    if remote_tracking:
        parity_code, parity_text = _git_stdout(root, "rev-list", "--left-right", "--count", f"{remote_tracking}...HEAD")
        if parity_code == 0 and parity_text:
            parts = parity_text.split()
            if len(parts) == 2 and all(part.isdigit() for part in parts):
                behind = int(parts[0])
                ahead = int(parts[1])
                parity_status = "clean" if behind == 0 and ahead == 0 else "drift"
    return OrderedDict(
        [
            ("branch", branch_name),
            ("head", head if head_code == 0 and head else None),
            ("parity", OrderedDict([("status", parity_status), ("behind", behind), ("ahead", ahead)])),
            ("staged", _git_lines(root, "diff", "--cached", "--name-only")),
            ("unstaged", _git_lines(root, "diff", "--name-only")),
            ("untracked", _git_lines(root, "ls-files", "--others", "--exclude-standard")),
        ]
    )


def _root_relative(path: Path, root: Path) -> str:
    return normalize_slashes(str(path.resolve().relative_to(root.resolve())))


def _dedupe_paths(paths: Iterable[Path]) -> list[Path]:
    seen: set[Path] = set()
    result: list[Path] = []
    for path in paths:
        normalized = path.resolve()
        if normalized in seen:
            continue
        seen.add(normalized)
        result.append(path)
    return sorted(result, key=lambda item: normalize_slashes(str(item)))


def discover_source_paths(root: Path) -> list[Path]:
    fixed = [root / ref for ref in SOURCE_REFS]
    discovered = [
        path
        for path in (root / "docs").rglob("*")
        if path.is_file() and path.suffix.lower() in TEXT_SUFFIXES and "playbook" in normalize_slashes(str(path)).lower()
    ]
    return _dedupe_paths([path for path in [*fixed, *discovered] if path.exists()])


def discover_consumer_paths(root: Path) -> list[Path]:
    fixed = [root / ref for ref in CONSUMER_REFS if (root / ref).exists()]
    patterns: list[Path] = []
    for base in ("docs/ops", "docs/memory/initiatives"):
        base_path = root / base
        if not base_path.exists():
            continue
        patterns.extend(
            path
            for path in base_path.rglob("*")
            if path.is_file()
            and path.suffix.lower() in TEXT_SUFFIXES
            and (
                "playbook" in path.name.lower()
                or "ai-work-session-stability-auto-sync-loop" in path.name.lower()
            )
        )
    return _dedupe_paths([*fixed, *patterns])


def _terms_present(text: str, terms: Iterable[str]) -> list[str]:
    lower = text.lower()
    return sorted({term for term in terms if term in lower})


def _surface(
    *,
    ref: str,
    role: str,
    classification: str,
    matched_terms: list[str],
    evidence: str,
) -> OrderedDict[str, Any]:
    return OrderedDict(
        [
            ("ref", ref),
            ("role", role),
            ("classification", classification),
            ("matched_terms", matched_terms),
            ("evidence", evidence),
        ]
    )


def classify_source_surfaces(root: Path, source_paths: list[Path]) -> tuple[list[OrderedDict[str, Any]], list[dict[str, Any]]]:
    warnings: list[dict[str, Any]] = []
    surfaces: list[OrderedDict[str, Any]] = []
    for path in source_paths:
        text = _read_text(path) or ""
        ref = _root_relative(path, root)
        matched_terms = ["playbook"] + _terms_present(text, ("doctrine", "matrix", "contract", "workflow"))
        surfaces.append(
            _surface(
                ref=ref,
                role="source",
                classification="documented_doctrine",
                matched_terms=sorted(set(matched_terms)),
                evidence="Playbook source or doctrine surface exists and is readable.",
            )
        )
    if not any(_root_relative(path, root) == "docs/PLAYBOOK_NOTES.md" for path in source_paths):
        warnings.append(_finding("playbook_notes_missing", "Canonical docs/PLAYBOOK_NOTES.md was not found."))
    return surfaces, warnings


def classify_adoption_surfaces(root: Path, consumer_paths: list[Path]) -> tuple[list[OrderedDict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    surfaces: list[OrderedDict[str, Any]] = []
    gaps: list[dict[str, Any]] = []
    warnings: list[dict[str, Any]] = []
    for path in consumer_paths:
        text = _read_text(path) or ""
        ref = _root_relative(path, root)
        lower = text.lower()
        if "playbook" not in lower:
            gaps.append(_finding("missing_adoption", "Relevant surface has no Playbook adoption signal.", ref=ref))
            continue
        consumer_terms = _terms_present(text, CONSUMER_TERMS)
        enforcement_terms = _terms_present(text, ENFORCEMENT_TERMS)
        if path.suffix == ".py" or ref.startswith("tests/"):
            classification = "enforced_doctrine"
            evidence = "Surface uses enforcement, test, selector, validator, or command language around Playbook truth."
        elif consumer_terms:
            classification = "consumed_doctrine"
            evidence = "Surface projects Playbook truth into routing, continuity, receipt, or adoption decisions."
        else:
            classification = "referenced_doctrine"
            evidence = "Surface references Playbook without enough signal to classify it as consumption or enforcement."
        surfaces.append(
            _surface(
                ref=ref,
                role="consumer",
                classification=classification,
                matched_terms=sorted(set(["playbook", *consumer_terms, *enforcement_terms])),
                evidence=evidence,
            )
        )
    if not surfaces:
        warnings.append(_finding("no_adoption_surfaces", "No Playbook adoption surfaces were classified."))
    return surfaces, gaps, warnings


def build_consumer_matrix(sources: list[dict[str, Any]], adoption_surfaces: list[dict[str, Any]]) -> OrderedDict[str, Any]:
    classifications = [
        "documented_doctrine",
        "referenced_doctrine",
        "consumed_doctrine",
        "enforced_doctrine",
        "stale_doctrine",
        "missing_adoption",
        "owner_lane_advisory_adoption",
        "cortex_substrate_candidate",
    ]
    counts = OrderedDict((classification, 0) for classification in classifications)
    rows: list[OrderedDict[str, Any]] = []
    for item in [*sources, *adoption_surfaces]:
        classification = str(item.get("classification") or "")
        if classification in counts:
            counts[classification] += 1
        rows.append(
            OrderedDict(
                [
                    ("ref", item.get("ref")),
                    ("role", item.get("role")),
                    ("classification", classification),
                    ("counts_as_operational_adoption", classification in {"consumed_doctrine", "enforced_doctrine"}),
                ]
            )
        )
    return OrderedDict([("counts", counts), ("rows", rows)])


def collect_non_consumers(root: Path, gaps: list[dict[str, Any]]) -> list[OrderedDict[str, Any]]:
    result: list[OrderedDict[str, Any]] = []
    for gap in gaps:
        details = gap.get("details", {}) if isinstance(gap, dict) else {}
        result.append(
            OrderedDict(
                [
                    ("ref", details.get("ref")),
                    ("reason", "no_playbook_reference"),
                    ("classification", "missing_adoption"),
                ]
            )
        )
    for ref in ("README-STACK.md", "AGENTS.md"):
        path = root / ref
        text = _read_text(path) or ""
        if path.exists() and "playbook" not in text.lower():
            result.append(OrderedDict([("ref", ref), ("reason", "no_playbook_reference"), ("classification", "missing_adoption")]))
    return result


def collect_cortex_candidates(root: Path, paths: list[Path]) -> tuple[list[OrderedDict[str, Any]], list[OrderedDict[str, Any]], list[OrderedDict[str, Any]], list[OrderedDict[str, Any]]]:
    doctrine: list[OrderedDict[str, Any]] = []
    patterns: list[OrderedDict[str, Any]] = []
    failures: list[OrderedDict[str, Any]] = []
    candidates: list[OrderedDict[str, Any]] = []
    heading_pattern = re.compile(r"^#{1,3}\s+(Rule|Pattern|Failure Mode)\s*$", re.IGNORECASE | re.MULTILINE)
    for path in paths:
        text = _read_text(path) or ""
        if "playbook" not in text.lower() and not _terms_present(text, CORTEX_TERMS):
            continue
        ref = _root_relative(path, root)
        headings = sorted({match.group(1).lower().replace(" ", "_") for match in heading_pattern.finditer(text)})
        matched_terms = _terms_present(text, CORTEX_TERMS)
        if "rule" in headings:
            doctrine.append(OrderedDict([("ref", ref), ("kind", "rule"), ("classification", "documented_doctrine")]))
        if "pattern" in headings or "pattern" in matched_terms:
            patterns.append(OrderedDict([("ref", ref), ("kind", "pattern"), ("classification", "cortex_substrate_candidate")]))
        if "failure_mode" in headings or "failure mode" in matched_terms:
            failures.append(OrderedDict([("ref", ref), ("kind", "failure_mode"), ("classification", "cortex_substrate_candidate")]))
        if headings or matched_terms:
            candidates.append(
                OrderedDict(
                    [
                        ("ref", ref),
                        ("classification", "cortex_substrate_candidate"),
                        ("matched_terms", sorted(set([*headings, *matched_terms]))),
                        ("read_only", True),
                    ]
                )
            )
    return doctrine, patterns, failures, candidates


def collect_owner_lane_adoption(root: Path, owners: list[str]) -> OrderedDict[str, Any]:
    report_path = root / "docs" / "registry" / "STACK-REPO-INVENTORY.json"
    payload = _read_json(report_path) or {}
    repos = payload.get("repos", [])
    requested = {owner.lower() for owner in owners}
    rows: list[OrderedDict[str, Any]] = []
    if isinstance(repos, list):
        for repo in repos:
            if not isinstance(repo, dict):
                continue
            repo_id = str(repo.get("logical_id") or repo.get("repo_id") or repo.get("id") or "").strip()
            if not repo_id:
                continue
            if requested and repo_id.lower() not in requested:
                continue
            text = json.dumps(repo, sort_keys=True).lower()
            rows.append(
                OrderedDict(
                    [
                        ("owner", repo_id),
                        ("classification", "owner_lane_advisory_adoption" if "playbook" in text else "missing_adoption"),
                        ("source_ref", "docs/registry/STACK-REPO-INVENTORY.json"),
                        ("read_only", True),
                        ("root_owned_proof", False),
                    ]
                )
            )
    return OrderedDict(
        [
            ("scope", "owner" if owners else "root"),
            ("requested_owners", owners),
            ("read_only", True),
            ("rows", rows),
        ]
    )


def collect_selector_state(root: Path) -> tuple[dict[str, Any] | None, list[dict[str, Any]]]:
    try:
        campaign = build_campaign(root=root)
    except Exception as exc:
        return None, [_finding("marker_selector_unavailable", "Marker selector output cannot be read.", severity="blocker", exception=str(exc))]
    return campaign, []


def _split_findings(findings: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    blockers = [item for item in findings if item.get("severity") == "blocker"]
    warnings = [item for item in findings if item.get("severity") != "blocker"]
    return blockers, warnings


def build_report(*, root: Path, scope: str = "root", owners: list[str] | None = None) -> OrderedDict[str, Any]:
    owners = owners or []
    all_findings: list[dict[str, Any]] = []
    branch_state = collect_branch_state(root)
    if branch_state["parity"]["status"] == "unavailable":
        all_findings.append(_finding("parity_unavailable", "Remote parity truth is unavailable.", severity="blocker"))
    elif branch_state["parity"]["status"] == "drift":
        all_findings.append(_finding("parity_drift", "Root branch parity is not clean.", severity="blocker", parity=branch_state["parity"]))
    if branch_state["staged"]:
        all_findings.append(_finding("staged_files_present", "Staged files block adoption claims.", severity="blocker", paths=branch_state["staged"]))
    if branch_state["unstaged"] or branch_state["untracked"]:
        all_findings.append(_finding("local_residue_present", "Local residue is present; classification remains advisory.", unstaged=branch_state["unstaged"], untracked=branch_state["untracked"]))

    source_paths = discover_source_paths(root)
    if not source_paths:
        all_findings.append(_finding("playbook_sources_missing", "No Playbook source surfaces were found.", severity="blocker"))
    playbook_sources, source_warnings = classify_source_surfaces(root, source_paths)
    all_findings.extend(source_warnings)

    consumer_paths = discover_consumer_paths(root)
    selector_state, selector_findings = collect_selector_state(root)
    all_findings.extend(selector_findings)
    adoption_surfaces, gaps, surface_warnings = classify_adoption_surfaces(root, consumer_paths)
    all_findings.extend(gaps)
    all_findings.extend(surface_warnings)
    if selector_state and "playbook" in json.dumps(selector_state, sort_keys=True).lower():
        adoption_surfaces.append(
            _surface(
                ref="ops/atlas/marker_knockout_selector.py",
                role="selector",
                classification="enforced_doctrine",
                matched_terms=["playbook", "selector"],
                evidence="Marker selector output includes Playbook routing truth.",
            )
        )

    non_consumers = collect_non_consumers(root, gaps)
    doctrine_signals, pattern_signals, failure_mode_signals, cortex_candidates = collect_cortex_candidates(root, [*source_paths, *consumer_paths])
    owner_lane_adoption = collect_owner_lane_adoption(root, owners)
    if scope == "owner":
        all_findings.append(_finding("owner_scope_read_only", "Owner scope is read-only and advisory to ATLAS root.", owners=owners))
    if scope in {"platform", "research"}:
        all_findings.append(_finding(f"{scope}_scope_read_only", f"{scope} scope is classified locally without platform mutation."))

    blockers, warnings = _split_findings(all_findings)
    required_followups = []
    for item in all_findings:
        code = str(item.get("code", "unknown"))
        if code.endswith("_missing") or code.startswith("missing_") or "unavailable" in code or "advisory" in code:
            required_followups.append(OrderedDict([("code", code), ("target", item.get("message"))]))

    status = STATUS_OK
    if blockers:
        status = STATUS_BLOCKER
    elif warnings:
        status = STATUS_ADVISORY

    return OrderedDict(
        [
            ("schema_version", SCHEMA_VERSION),
            ("status", status),
            ("root", normalize_slashes(str(root))),
            ("branch", branch_state.get("branch")),
            ("head", branch_state.get("head")),
            ("parity", branch_state.get("parity")),
            ("playbook_sources", playbook_sources),
            ("adoption_surfaces", adoption_surfaces),
            ("consumer_matrix", build_consumer_matrix(playbook_sources, adoption_surfaces)),
            ("non_consumers", non_consumers),
            ("doctrine_signals", doctrine_signals),
            ("pattern_signals", pattern_signals),
            ("failure_mode_signals", failure_mode_signals),
            ("cortex_substrate_candidates", cortex_candidates),
            ("owner_lane_adoption", owner_lane_adoption),
            ("gaps", gaps),
            ("blockers", blockers),
            ("warnings", warnings),
            ("required_followups", required_followups),
            ("safe_to_continue", not blockers),
        ]
    )


def report_exit_code(*, status: str, strict: bool) -> int:
    if status == STATUS_OK:
        return 0
    if status == STATUS_ADVISORY:
        return 1 if strict else 0
    if status == STATUS_BLOCKER:
        return 2
    return 3


def render_summary(report: dict[str, Any]) -> str:
    parity = report.get("parity", {})
    counts = report.get("consumer_matrix", {}).get("counts", {})
    return "\n".join(
        [
            f"Status: {report.get('status')}",
            f"Branch: {report.get('branch') or 'unknown'}",
            f"Head: {report.get('head') or 'unknown'}",
            f"Parity: {parity.get('status', 'unknown')} (behind={parity.get('behind')}, ahead={parity.get('ahead')})",
            f"Sources: {len(report.get('playbook_sources', []))}",
            f"Consumed: {counts.get('consumed_doctrine', 0)}",
            f"Enforced: {counts.get('enforced_doctrine', 0)}",
            f"Safe to continue: {str(report.get('safe_to_continue')).lower()}",
        ]
    )


def render_stdout(report: dict[str, Any], *, json_only: bool) -> str:
    json_text = json.dumps(report, indent=2) + "\n"
    if json_only:
        return json_text
    return render_summary(report) + "\n\n" + json_text


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Read-only ATLAS Playbook adoption matrix classifier.")
    parser.add_argument("--json", action="store_true", help="Emit JSON only on stdout.")
    parser.add_argument("--scope", choices=sorted(SCOPES), default="root")
    parser.add_argument("--owner", action="append", default=[])
    parser.add_argument("--strict", action="store_true")
    parser.add_argument("--output")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    root = atlas_root().resolve()
    try:
        report = build_report(root=root, scope=args.scope, owners=list(args.owner or []))
        if args.output:
            resolved_output, output_error = validate_output_path(root=root, output_path=args.output)
            if output_error is not None:
                report["status"] = STATUS_BLOCKER
                report["blockers"] = list(report.get("blockers", [])) + [output_error]
                report["safe_to_continue"] = False
                report["required_followups"] = list(report.get("required_followups", [])) + [
                    OrderedDict([("code", output_error["code"]), ("target", output_error["message"])])
                ]
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
                ("parity", OrderedDict([("status", "unavailable"), ("behind", None), ("ahead", None)])),
                ("playbook_sources", []),
                ("adoption_surfaces", []),
                ("consumer_matrix", OrderedDict()),
                ("non_consumers", []),
                ("doctrine_signals", []),
                ("pattern_signals", []),
                ("failure_mode_signals", []),
                ("cortex_substrate_candidates", []),
                ("owner_lane_adoption", OrderedDict()),
                ("gaps", []),
                ("blockers", [_finding("internal_error", "Playbook adoption matrix failed before classification.", severity="blocker", exception=str(exc))]),
                ("warnings", []),
                ("required_followups", [OrderedDict([("code", "internal_error"), ("target", "debug Playbook adoption matrix worker")])]),
                ("safe_to_continue", False),
            ]
        )
        sys.stdout.write(render_stdout(report, json_only=getattr(args, "json", False)))
        return 3


if __name__ == "__main__":
    raise SystemExit(main())
