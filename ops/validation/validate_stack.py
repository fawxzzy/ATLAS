from __future__ import annotations

import argparse
import json
import os
import re
import sys
from collections import Counter
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

TEXT_EXTENSIONS = {
    ".bat", ".cjs", ".cmd", ".conf", ".cfg", ".ini", ".js", ".json", ".md",
    ".mjs", ".ps1", ".py", ".sh", ".toml", ".ts", ".tsx", ".txt", ".yaml", ".yml",
}
SCAN_SKIP_DIRS = {
    ".git", ".next", ".venv", "__pycache__", ".pytest_cache", ".mypy_cache",
    ".ruff_cache", ".cache", ".turbo", ".parcel-cache", ".codex", ".playbook",
    ".lifeline", ".vercel", "node_modules", "dist", "coverage", "playwright-report",
    "test-results", "runtime", "tmp", "secrets",
}
ACTIVE_STATUSES = {"active"}
AGENTS_EXPECTED_STATUSES = {"active", "incubating"}
CONFIG_EXPECTED_STATUSES = {"active"}
WINDOWS_DRIVE_PREFIX_PATTERN = r"[A-Za-z]:"
USER_HOME_DIRECTORY = "Users"
UNIX_HOME_DIRECTORIES = ("Users", "home")


def build_home_path_pattern(*, separator: str, directory: str) -> re.Pattern[str]:
    return re.compile(
        WINDOWS_DRIVE_PREFIX_PATTERN
        + separator
        + re.escape(directory)
        + separator
    )


ABSOLUTE_PATTERNS = [
    ("critical", "windows-user-path", build_home_path_pattern(separator=r"\\", directory=USER_HOME_DIRECTORY)),
    ("critical", "windows-user-path-alt", build_home_path_pattern(separator="/", directory=USER_HOME_DIRECTORY)),
    ("critical", "unix-home-path", re.compile("|".join(re.escape(f"/{directory}/") for directory in UNIX_HOME_DIRECTORIES))),
]
QUARANTINED_EXCLUDED_SURFACE_LABEL = "quarantined-excluded-surface"
EXCLUDED_SURFACE_LABEL = "excluded-surface"
MUTABLE_DIR_CANDIDATES = [
    ".next", ".playbook", ".lifeline", ".venv", ".vercel", "node_modules", "dist",
    "coverage", "playwright-report", "test-results", "DerivedDataCache",
    "Intermediate", "Saved", "Binaries",
]
ROOT_LOG_PATTERNS = ["*.log", "*.err.log", "*.out.log", "*.tmp", "*.db", "*.sqlite", "*.sqlite3"]
ROOT_CAPTURE_PATTERNS = ["*screenshot*.png", "artifacts*.png", "*check*.png", "*review*.png"]
BASELINE_VERSION = "atlas.stack.validation.baseline.v1"
DECLARED_STACK_SURFACE_SCAN_CANDIDATES = [
    "README-STACK.md",
    "AGENTS.md",
    "stack.yaml",
    "stack.lock.yaml",
    ".github/workflows",
    "docs",
    "ops",
    "packages",
    "data",
]
REQUIRED_STACK_GOVERNANCE_SCAN_SURFACES = [
    "README-STACK.md",
    "AGENTS.md",
    "stack.yaml",
    "stack.lock.yaml",
    ".github/workflows",
    "docs",
    "ops",
]
PLAYBOOK_ENFORCEMENT_TRACKED_PATHS = [
    "packages/engine/src/verify/rules/atlasRootPolicyChecks.ts",
    "packages/engine/src/verify/rules/atlasRootPolicyChecks.test.ts",
]
VERTA_SECRET_PATTERNS = [
    ("verta-live-secret", re.compile(r"gh[pousr]_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{20,}|AKIA[0-9A-Z]{16}|sk-[A-Za-z0-9]{20,}|xox[baprs]-[A-Za-z0-9-]{10,}|-----BEGIN [A-Z ]*PRIVATE KEY-----|Bearer\s+[A-Za-z0-9._-]{16,}")),
]
VERTA_SURFACE_TEXT_EXTENSIONS = {".bat", ".cmd", ".conf", ".cfg", ".ini", ".json", ".md", ".ps1", ".py", ".sh", ".txt", ".yaml", ".yml"}

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from ops.stack.generate_lockfile import (
    LOCK_COMPONENT_FIELDS,
    LOCK_EXCLUDED_SURFACE_FIELDS,
    LOCK_METADATA_FIELDS,
    STACK_LOCK_SCHEMA_VERSION,
    TRUST_CLASSES,
    build_canonical_lockfile_artifacts,
    default_lockfile_path,
    describe_lock_payload_drift,
    git_output,
    load_lockfile,
    normalize_lock_payload,
    repo_is_git_root,
    render_lockfile_bytes,
)
from ops.stack.audit_gitdir_hygiene import build_report as build_gitdir_hygiene_report, default_target_paths as default_gitdir_hygiene_targets
from ops.atlas.backfill_legacy_runtime_artifacts import backfill_legacy_runtime_artifacts
from ops.atlas.observations import (
    GOVERNED_ARTIFACT_EPOCH_LEGACY_PRE_REGISTRY,
    build_observation,
    canonical_observation_type,
    execution_receipt_residue_records,
    load_execution_receipt_payloads,
    emit_observation,
    governed_artifact_epoch_details,
    load_observations,
    resolve_preferred_execution_receipt_ref,
)
from ops.atlas.load_tool_registry import load_tool_registry_bundle
from ops.cortex._artifacts import load_descriptors, register_artifact_descriptors, stable_json_digest
from ops.cortex.index_working_memory import (
    build_working_memory_catalog,
    load_working_memory_catalog,
    validate_working_memory_documents,
)
from ops.cortex.world_model import world_model_state_root, write_world_model_state
from ops.validation.atlas_topology_contract import validate_contract_files as validate_atlas_topology_contract_files


@dataclass
class Finding:
    severity: str
    category: str
    path: str
    message: str
    details: dict[str, Any] | None = None


DEBT_CLASS_CONFIG = [
    {
        "id": "repo-local-config-gaps",
        "categories": {
            "missing-repo-path",
            "repo-path-not-directory",
            "repo-path-not-git-root",
            "missing-readme",
        },
    },
    {
        "id": "path-discipline-leaks",
        "categories": {
            "windows-user-path",
            "windows-user-path-alt",
            "unix-home-path",
            "atlas-root-path",
            "atlas-root-path-alt",
        },
    },
    {
        "id": "lock-registry-hygiene",
        "categories": {
            "unregistered-git-root",
            "missing-stack-lockfile",
            "invalid-stack-lockfile",
            "stack-lock-drift",
            "stack-lock-missing-ref",
            "stack-lock-pin-drift",
            "stack-lock-worktree-drift",
            "stack-lock-render-drift",
            "stack-lock-metadata-drift",
            "stack-lock-component-membership-drift",
            "stack-lock-component-trust",
            "stack-lock-component-release",
            "stack-lock-excluded-surface-membership-drift",
            "stack-lock-excluded-surface-drift",
            "stack-lock-excluded-surface-release",
            "stack-lock-excluded-surface-trust",
            "root-lock-refresh-accepted",
            "root-lock-refresh-pending",
            "playbook-enforcement-untracked",
            "playbook-enforcement-tracking-check-failed",
        },
        "prefixes": [
            "stack-lock-",
            "gitdir-hygiene-",
            "execution-receipt-repair-",
        ],
    },
    {
        "id": "missing-agents-codex-defaults",
        "categories": {
            "missing-agents",
            "missing-codex-config",
        },
    },
    {
        "id": "historical-stack-baseline-residue",
        "categories": {
            "mutable-state-in-repo",
            "mutable-artifact-in-repo-root",
            "capture-artifact-in-repo-root",
            "repo-local-secret-material",
        },
    },
]
ENV_EXAMPLE_MARKERS = (".example", ".sample", ".template", ".dist")
REMEDIATION_BUCKET_CONFIG = [
    {
        "bucket_id": "execution-receipt-repair-invalid",
        "title": "Execution Receipt Repair",
        "treatment": "repair through canonical builders",
        "categories": {
            "execution-receipt-repair-required",
            "execution-receipt-repair-invalid",
        },
    },
    {
        "bucket_id": "mutable-state-warnings",
        "title": "Mutable-State Warnings",
        "treatment": "classify as retained residue / historical debt",
        "categories": {
            "mutable-state-in-repo",
            "mutable-artifact-in-repo-root",
            "capture-artifact-in-repo-root",
        },
    },
    {
        "bucket_id": "repo-local-config-gaps",
        "title": "Repo-Local Config Gaps",
        "treatment": "move into the debt ledger as inherited debt",
        "categories": {
            "missing-repo-path",
            "repo-path-not-directory",
            "repo-path-not-git-root",
            "missing-readme",
        },
    },
    {
        "bucket_id": "path-discipline-leaks",
        "title": "Path-Discipline Leaks",
        "treatment": "move into the debt ledger as inherited debt",
        "categories": {
            "windows-user-path",
            "windows-user-path-alt",
            "unix-home-path",
            "atlas-root-path",
            "atlas-root-path-alt",
        },
    },
    {
        "bucket_id": "retained-runtime-residue",
        "title": "Retained Runtime Residue",
        "treatment": "classify as retained residue / historical debt",
        "categories": set(),
        "include_execution_receipt_residue": True,
    },
]


def classify_debt_class(category: str) -> str:
    for config in DEBT_CLASS_CONFIG:
        if category in config.get("categories", set()):
            return str(config["id"])
        for prefix in config.get("prefixes", []):
            if category.startswith(str(prefix)):
                return str(config["id"])
    return "governed-surface-contracts"


def is_repo_local_secret_candidate(path: Path) -> bool:
    name = path.name.lower()
    if name == ".env":
        return True
    if not name.startswith(".env."):
        return False
    suffix = name.removeprefix(".env.")
    return not any(marker in suffix for marker in ENV_EXAMPLE_MARKERS)


def summarize_debt_classes(findings: list[dict[str, Any]]) -> list[dict[str, Any]]:
    buckets: dict[str, dict[str, Any]] = {}
    for finding in findings:
        category = str(finding.get("category", ""))
        debt_class = classify_debt_class(category)
        bucket = buckets.setdefault(
            debt_class,
            {
                "class_id": debt_class,
                "total": 0,
                "blocking_total": 0,
                "severity_counts": Counter(),
                "category_counts": Counter(),
            },
        )
        bucket["total"] += 1
        if finding.get("severity") in {"critical", "error"}:
            bucket["blocking_total"] += 1
        bucket["severity_counts"][str(finding.get("severity", "unknown"))] += 1
        bucket["category_counts"][category] += 1
    summarized: list[dict[str, Any]] = []
    for debt_class in sorted(buckets):
        bucket = buckets[debt_class]
        summarized.append(
            {
                "class_id": debt_class,
                "total": bucket["total"],
                "blocking_total": bucket["blocking_total"],
                "severity_counts": dict(sorted(bucket["severity_counts"].items())),
                "category_counts": dict(sorted(bucket["category_counts"].items())),
            }
        )
    return summarized


def debt_class_counts(findings: list[dict[str, Any]]) -> dict[str, int]:
    counts: Counter[str] = Counter()
    for finding in findings:
        counts[classify_debt_class(str(finding.get("category", "")))] += 1
    return dict(sorted(counts.items()))


def summarize_remediation_buckets(
    findings: list[dict[str, Any]],
    *,
    root: Path,
) -> list[dict[str, Any]]:
    summarized: list[dict[str, Any]] = []
    execution_receipt_residue = execution_receipt_residue_records(root)
    for config in REMEDIATION_BUCKET_CONFIG:
        bucket_findings = [
            finding
            for finding in findings
            if str(finding.get("category", "")) in config.get("categories", set())
        ]
        residue_records = execution_receipt_residue if config.get("include_execution_receipt_residue") else []
        if not bucket_findings and not residue_records:
            continue
        category_counts = Counter(str(finding.get("category", "")) for finding in bucket_findings)
        severity_counts = Counter(str(finding.get("severity", "unknown")) for finding in bucket_findings)
        residue_status_counts = Counter(str(item.get("status", "unknown")) for item in residue_records)
        examples: list[str] = []
        for finding in bucket_findings:
            candidate = str(finding.get("path", "")).strip()
            if candidate and candidate not in examples:
                examples.append(candidate)
            if len(examples) >= 5:
                break
        if len(examples) < 5:
            for residue in residue_records:
                candidate = str(residue.get("source_ref", "")).strip()
                if candidate and candidate not in examples:
                    examples.append(candidate)
                if len(examples) >= 5:
                    break
        summarized.append(
            {
                "bucket_id": str(config["bucket_id"]),
                "title": str(config["title"]),
                "treatment": str(config["treatment"]),
                "finding_count": len(bucket_findings),
                "blocking_count": sum(
                    1 for finding in bucket_findings if finding.get("severity") in {"critical", "error"}
                ),
                "residue_count": len(residue_records),
                "severity_counts": dict(sorted(severity_counts.items())),
                "category_counts": dict(sorted(category_counts.items())),
                "residue_status_counts": dict(sorted(residue_status_counts.items())),
                "examples": examples,
            }
        )
    return summarized


def warning_repo_id_for_finding(finding: dict[str, Any]) -> str:
    details = finding.get("details")
    if isinstance(details, dict):
        repo_id = details.get("repo_id")
        if isinstance(repo_id, str) and repo_id.strip():
            return repo_id
    path = str(finding.get("path", "")).replace("\\", "/")
    if path.startswith("repos/"):
        parts = path.split("/")
        if len(parts) >= 2:
            repo_root = parts[1]
            mapping = {
                "_stack": "_stack",
                "fawxzzy-fitness": "fitness",
                "fawxzzy-playbook": "playbook",
                "fawxzzy-lifeline": "lifeline",
                "fawxzzy-trove": "trove",
                "fawxzzy-mazer": "mazer",
                "fawxzzy-stack": "stack",
                "fawxzzy-stream": "stream",
                "Nat1-Games": "nat1-games",
                "playbook-demo": "playbook-demo",
            }
            return mapping.get(repo_root, repo_root)
    return "atlas-root"


def build_warning_budget_summary(
    report: dict[str, Any],
    *,
    stack_file: Path,
    output_dir: Path,
) -> dict[str, Any]:
    findings = report.get("findings", []) if isinstance(report.get("findings"), list) else []
    warnings = [item for item in findings if isinstance(item, dict) and item.get("severity") == "warning"]
    category_counts = Counter(str(item.get("category", "unknown")) for item in warnings)
    repo_counts = Counter(warning_repo_id_for_finding(item) for item in warnings)
    top_category = category_counts.most_common(1)[0][0] if category_counts else ""
    top_repo = repo_counts.most_common(1)[0][0] if repo_counts else ""
    previous_path = output_dir / "stack-warning-budget.latest.json"
    baseline_warning_count = len(warnings)
    if previous_path.exists():
        try:
            previous = json.loads(previous_path.read_text(encoding="utf-8"))
            previous_policy = previous.get("policy", {}) if isinstance(previous.get("policy"), dict) else {}
            previous_baseline = previous_policy.get("baseline_warning_count")
            if isinstance(previous_baseline, int) and previous_baseline >= 0:
                baseline_warning_count = previous_baseline
        except Exception:
            baseline_warning_count = len(warnings)
    previous_baseline_warning_count = baseline_warning_count
    ratchet_applied = False
    if len(warnings) < baseline_warning_count:
        baseline_warning_count = len(warnings)
        ratchet_applied = True
    allowed_growth = 25
    current_delta = len(warnings) - baseline_warning_count
    within_budget = len(warnings) <= baseline_warning_count + allowed_growth
    budget_status = "within_budget"
    if current_delta > 0 and within_budget:
        budget_status = "growth_within_budget"
    elif not within_budget:
        budget_status = "budget_exceeded"
    recommended_next_fix = ""
    if top_category:
        recommended_next_fix = f"Reduce '{top_category}' warnings first"
        if top_repo and top_repo != "atlas-root":
            recommended_next_fix += f" in repo '{top_repo}'"
        recommended_next_fix += "."
    summary = {
        "generated_at": report.get("generated_at"),
        "stack_file": baseline_relpath(stack_file, stack_file),
        "warning_count": len(warnings),
        "warning_categories": dict(sorted(category_counts.items())),
        "warnings_by_repo": dict(sorted(repo_counts.items())),
        "top_5_warning_categories": [
            {"category": category, "count": count}
            for category, count in category_counts.most_common(5)
        ],
        "top_5_warning_repos": [
            {"repo_id": repo_id, "count": count}
            for repo_id, count in repo_counts.most_common(5)
        ],
        "top_recurring_warning": {
            "category": top_category,
            "count": int(category_counts.get(top_category, 0)),
            "repo_id": top_repo,
            "repo_warning_count": int(repo_counts.get(top_repo, 0)),
        },
        "policy": {
            "previous_baseline_warning_count": previous_baseline_warning_count,
            "baseline_warning_count": baseline_warning_count,
            "allowed_growth": allowed_growth,
            "current_delta": current_delta,
            "within_budget": within_budget,
            "budget_mode": "report_only",
            "budget_status": budget_status,
            "increase_requires_explanation": current_delta > 0,
            "governance_review_required": current_delta > 0,
            "hard_review_threshold": allowed_growth,
            "ratchet_enabled": True,
            "ratchet_applied": ratchet_applied,
        },
        "recommended_next_fix": recommended_next_fix,
        "recommended_next_cleanup": recommended_next_fix,
    }
    json_path = output_dir / "stack-warning-budget.latest.json"
    md_path = output_dir / "stack-warning-budget.latest.md"
    json_path.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    md_lines = [
        "# ATLAS Stack Warning Budget",
        "",
        f"- Generated: `{summary['generated_at']}`",
        f"- Warning count: `{summary['warning_count']}`",
        f"- Baseline warning count: `{summary['policy']['baseline_warning_count']}`",
        f"- Previous baseline warning count: `{summary['policy']['previous_baseline_warning_count']}`",
        f"- Allowed growth: `{summary['policy']['allowed_growth']}`",
        f"- Current delta: `{summary['policy']['current_delta']}`",
        f"- Within budget: `{summary['policy']['within_budget']}`",
        f"- Budget status: `{summary['policy']['budget_status']}`",
        f"- Ratchet applied: `{summary['policy']['ratchet_applied']}`",
        "",
        "## By Category",
        "",
    ]
    for category, count in sorted(category_counts.items(), key=lambda item: (-item[1], item[0])):
        md_lines.append(f"- `{category}`: {count}")
    md_lines += ["", "## By Repo", ""]
    for repo_id, count in sorted(repo_counts.items(), key=lambda item: (-item[1], item[0])):
        md_lines.append(f"- `{repo_id}`: {count}")
    if summary["top_5_warning_categories"]:
        md_lines += ["", "## Top 5 Categories", ""]
        for item in summary["top_5_warning_categories"]:
            md_lines.append(f"- `{item['category']}`: {item['count']}")
    if summary["top_5_warning_repos"]:
        md_lines += ["", "## Top 5 Repos", ""]
        for item in summary["top_5_warning_repos"]:
            md_lines.append(f"- `{item['repo_id']}`: {item['count']}")
    if recommended_next_fix:
        md_lines += ["", "## Recommendation", "", f"- {recommended_next_fix}"]
    md_path.write_text("\n".join(md_lines) + "\n", encoding="utf-8")
    return {
        "warning_budget_ref": baseline_relpath(stack_file, json_path),
        "warning_budget_md_ref": baseline_relpath(stack_file, md_path),
        "warning_count": len(warnings),
    }


def parse_scalar(value: str) -> Any:
    lowered = value.lower()
    if lowered == "true":
        return True
    if lowered == "false":
        return False
    if lowered == "null":
        return None
    if (value.startswith('"') and value.endswith('"')) or (value.startswith("'") and value.endswith("'")):
        return value[1:-1]
    if re.fullmatch(r"-?\d+", value):
        return int(value)
    if re.fullmatch(r"-?\d+\.\d+", value):
        return float(value)
    return value


def parse_simple_yaml(text: str) -> dict[str, Any]:
    lines: list[tuple[int, str]] = []
    for raw_line in text.splitlines():
        if not raw_line.strip():
            continue
        stripped = raw_line.lstrip(" ")
        if stripped.startswith("#"):
            continue
        lines.append((len(raw_line) - len(stripped), stripped.rstrip()))

    root: dict[str, Any] = {}
    stack: list[tuple[int, Any]] = [(-1, root)]
    for index, (indent, content) in enumerate(lines):
        while stack and indent <= stack[-1][0]:
            stack.pop()
        parent = stack[-1][1]
        next_indent = lines[index + 1][0] if index + 1 < len(lines) else -1
        next_content = lines[index + 1][1] if index + 1 < len(lines) else ""

        if content.startswith("- "):
            if not isinstance(parent, list):
                raise ValueError(f"List item found without list parent near: {content}")
            parent.append(parse_scalar(content[2:].strip()))
            continue

        key, separator, value_text = content.partition(":")
        if not separator:
            raise ValueError(f"Unsupported YAML line: {content}")
        key = key.strip()
        value_text = value_text.strip()
        if value_text:
            if not isinstance(parent, dict):
                raise ValueError(f"Key/value pair found without mapping parent near: {content}")
            parent[key] = parse_scalar(value_text)
            continue

        child: Any = [] if next_indent > indent and next_content.startswith("- ") else {}
        if not isinstance(parent, dict):
            raise ValueError(f"Nested mapping found without mapping parent near: {content}")
        parent[key] = child
        stack.append((indent, child))
    return root


def load_stack_config(path: Path) -> dict[str, Any]:
    text = path.read_text(encoding="utf-8")
    try:
        import yaml  # type: ignore

        loaded = yaml.safe_load(text)
        if not isinstance(loaded, dict):
            raise ValueError("stack.yaml must deserialize to a mapping")
        return loaded
    except ModuleNotFoundError:
        return parse_simple_yaml(text)


def repo_root() -> Path:
    return ROOT


def resolve_path(stack_file: Path, raw_path: str) -> Path:
    path = Path(raw_path)
    return path.resolve() if path.is_absolute() else (stack_file.parent / path).resolve()


def normalize_slashes(path: str) -> str:
    return path.replace("\\", "/")


def relative_to_root(root: Path, path: Path) -> str:
    resolved = path.resolve()
    if resolved.is_relative_to(root.resolve()):
        relative = resolved.relative_to(root.resolve())
        return "." if not relative.parts else normalize_slashes(str(relative))
    return normalize_slashes(str(resolved))


def collect_excluded_surface_roots(
    stack_file: Path,
    config: dict[str, Any],
) -> list[tuple[Path, dict[str, Any]]]:
    root = stack_file.parent.resolve()
    lock_config = config.get("stack_lock", {})
    excluded_surfaces = lock_config.get("excluded_surfaces", {}) if isinstance(lock_config, dict) else {}
    if not isinstance(excluded_surfaces, dict):
        return []

    collected: list[tuple[Path, dict[str, Any]]] = []
    for surface_id, surface in excluded_surfaces.items():
        if not isinstance(surface, dict) or not isinstance(surface.get("path"), str):
            continue
        resolved_path = resolve_path(stack_file, str(surface["path"])).resolve()
        trust_class = str(surface.get("trust_class", ""))
        collected.append(
            (
                resolved_path,
                {
                    "surface_id": str(surface_id),
                    "path": relative_to_root(root, resolved_path),
                    "trust_class": trust_class,
                    "release_eligible": bool(surface.get("release_eligible")),
                    "reason": str(surface.get("reason", "")).strip() or None,
                    "label": (
                        QUARANTINED_EXCLUDED_SURFACE_LABEL
                        if trust_class == "untrusted"
                        else EXCLUDED_SURFACE_LABEL
                    ),
                },
            )
        )
    collected.sort(key=lambda item: len(item[0].parts), reverse=True)
    return collected


def excluded_surface_details_for_path(
    file_path: Path,
    *,
    excluded_surface_roots: list[tuple[Path, dict[str, Any]]],
) -> dict[str, Any] | None:
    resolved_file_path = file_path.resolve()
    for surface_root, metadata in excluded_surface_roots:
        if resolved_file_path == surface_root or resolved_file_path.is_relative_to(surface_root):
            return {
                "surface_id": str(metadata.get("surface_id", "")),
                "path": str(metadata.get("path", "")),
                "trust_class": str(metadata.get("trust_class", "")),
                "release_eligible": bool(metadata.get("release_eligible")),
                "reason": metadata.get("reason"),
                "label": str(metadata.get("label", EXCLUDED_SURFACE_LABEL)),
            }
    return None


def build_absolute_path_finding(
    *,
    root: Path,
    file_path: Path,
    severity: str,
    category: str,
    line_number: int,
    line_preview: str,
    excluded_surface_roots: list[tuple[Path, dict[str, Any]]],
) -> Finding:
    details: dict[str, Any] = {
        "line_number": line_number,
        "line_preview": line_preview[:220],
    }
    emitted_severity = severity
    message = "Absolute path leak detected in committed text."
    excluded_surface = excluded_surface_details_for_path(
        file_path,
        excluded_surface_roots=excluded_surface_roots,
    )
    if excluded_surface is not None:
        details["excluded_surface"] = excluded_surface
        if excluded_surface.get("label") == QUARANTINED_EXCLUDED_SURFACE_LABEL:
            emitted_severity = "warning"
            message = "Absolute path leak detected in quarantined excluded surface."
        else:
            message = "Absolute path leak detected in excluded surface."
    return Finding(
        emitted_severity,
        category,
        relative_to_root(root, file_path),
        message,
        details,
    )


def lockfile_output_path(stack_file: Path, config: dict[str, Any]) -> Path:
    return default_lockfile_path(config=config, root=stack_file.parent.resolve())


def verify_locked_ref(repo_path: Path, component: dict[str, Any]) -> str | None:
    ref_type = str(component.get("ref_type", ""))
    ref = str(component.get("ref", ""))
    commit = str(component.get("commit", ""))
    if ref_type == "branch":
        code, _ = git_output(repo_path, "show-ref", "--verify", "--quiet", f"refs/heads/{ref}")
        if code != 0:
            return f"Pinned branch ref '{ref}' is missing."
    elif ref_type == "tag":
        code, _ = git_output(repo_path, "show-ref", "--verify", "--quiet", f"refs/tags/{ref}")
        if code != 0:
            return f"Pinned tag ref '{ref}' is missing."
    elif ref_type == "commit":
        code, output = git_output(repo_path, "rev-parse", "--verify", f"{ref}^{{commit}}")
        if code != 0 or not output:
            return f"Pinned commit ref '{ref}' is missing."
    else:
        return f"Unsupported ref_type '{ref_type}'."

    code, head_commit = git_output(repo_path, "rev-parse", "HEAD")
    if code != 0 or not head_commit:
        return "Unable to resolve current HEAD for pinned component."
    if commit and head_commit != commit:
        return f"Pinned commit '{commit}' does not match current HEAD '{head_commit}'."
    return None


def classify_root_lock_refresh_state(
    *,
    root: Path,
    lockfile_path: Path,
    lockfile: dict[str, Any],
    lockfile_bytes: bytes,
    canonical_lock: dict[str, Any] | None,
    drift_report: dict[str, Any] | None,
) -> dict[str, Any] | None:
    if not isinstance(canonical_lock, dict):
        return None

    stack_root_state = canonical_lock.get("stack_root")
    canonical_bytes = canonical_lock.get("bytes")
    repo_id = stack_root_state.get("repo_id") if isinstance(stack_root_state, dict) else None
    if not isinstance(stack_root_state, dict) or not isinstance(repo_id, str):
        return None

    if (
        lockfile_path.resolve() == canonical_lock.get("lockfile_path")
        and bool(stack_root_state.get("self_refresh_only"))
        and isinstance(canonical_bytes, bytes)
        and lockfile_bytes == canonical_bytes
    ):
        return {
            "state": "pending",
            "repo_id": repo_id,
            "details": {
                "repo_id": repo_id,
                "dirty_actual": stack_root_state.get("dirty_actual"),
                "dirty_effective": stack_root_state.get("dirty_effective"),
                "modified_paths": stack_root_state.get("modified_paths"),
            },
        }

    if not isinstance(drift_report, dict):
        return None
    if bool(stack_root_state.get("dirty_actual")) or bool(stack_root_state.get("dirty_effective")):
        return None
    modified_paths = stack_root_state.get("modified_paths")
    if modified_paths not in ([], None):
        return None
    if drift_report.get("metadata_fields") or drift_report.get("excluded_surfaces"):
        return None

    component_drift = drift_report.get("components")
    if not isinstance(component_drift, dict) or sorted(component_drift) != [repo_id]:
        return None
    repo_drift = component_drift.get(repo_id)
    if not isinstance(repo_drift, dict):
        return None
    if str(repo_drift.get("kind", "")) != "pin":
        return None
    drift_fields = repo_drift.get("fields")
    if drift_fields != ["commit"]:
        return None

    locked_payload = normalize_lock_payload(lockfile)
    if lockfile.get("lock_digest") != locked_payload.get("lock_digest"):
        return None
    if lockfile_bytes != render_lockfile_bytes(locked_payload):
        return None

    locked_components = drift_report.get("locked", {}).get("components")
    generated_components = drift_report.get("generated", {}).get("components")
    if not isinstance(locked_components, dict) or not isinstance(generated_components, dict):
        return None
    locked_component = locked_components.get(repo_id)
    generated_component = generated_components.get(repo_id)
    if not isinstance(locked_component, dict) or not isinstance(generated_component, dict):
        return None

    pinned_commit = str(locked_component.get("commit", ""))
    current_commit = str(generated_component.get("commit", ""))
    if not pinned_commit or not current_commit:
        return None

    code, _ = git_output(root, "cat-file", "-e", f"{pinned_commit}^{{commit}}")
    if code != 0:
        return None
    code, _ = git_output(root, "merge-base", "--is-ancestor", pinned_commit, current_commit)
    if code != 0:
        return None
    code, diff_output = git_output(root, "diff", "--name-only", pinned_commit, current_commit)
    if code != 0:
        return None
    changed_paths = sorted(
        normalize_slashes(line.strip())
        for line in diff_output.splitlines()
        if line.strip()
    )
    lockfile_rel = relative_to_root(root, lockfile_path)
    if changed_paths != [lockfile_rel]:
        return None

    return {
        "state": "accepted",
        "repo_id": repo_id,
        "details": {
            "repo_id": repo_id,
            "pinned_commit": pinned_commit,
            "current_commit": current_commit,
            "changed_paths": changed_paths,
        },
    }


def describe_stack_lock_drift(
    *,
    lockfile_rel: str,
    drift_report: dict[str, Any],
) -> list[Finding]:
    findings: list[Finding] = []
    locked = drift_report.get("locked") if isinstance(drift_report.get("locked"), dict) else {}
    generated = drift_report.get("generated") if isinstance(drift_report.get("generated"), dict) else {}

    component_drift = drift_report.get("components") if isinstance(drift_report.get("components"), dict) else {}
    for component_id in sorted(component_drift):
        component_path = f"{lockfile_rel}#{component_id}"
        details = component_drift.get(component_id)
        if not isinstance(details, dict):
            continue
        drift_kind = str(details.get("kind", ""))
        drift_fields = [str(field) for field in details.get("fields", []) if isinstance(field, str)]
        if drift_kind == "membership":
            findings.append(
                Finding(
                    "error",
                    "stack-lock-component-membership-drift",
                    component_path,
                    "Pinned component membership differs from the current generated working set.",
                )
            )
            continue
        if drift_kind == "worktree":
            locked_components = locked.get("components") if isinstance(locked.get("components"), dict) else {}
            generated_components = generated.get("components") if isinstance(generated.get("components"), dict) else {}
            locked_component = locked_components.get(component_id) if isinstance(locked_components.get(component_id), dict) else {}
            generated_component = generated_components.get(component_id) if isinstance(generated_components.get(component_id), dict) else {}
            findings.append(
                Finding(
                    "error",
                    "stack-lock-worktree-drift",
                    component_path,
                    f"Pinned dirty state is {locked_component.get('dirty')!r} but the current worktree state is {generated_component.get('dirty')!r}.",
                )
            )
            continue
        if not drift_fields:
            continue
        findings.append(
            Finding(
                "error",
                "stack-lock-pin-drift",
                component_path,
                f"Pinned component fields differ from the current generated working set: {', '.join(drift_fields)}.",
            )
        )

    surface_drift = drift_report.get("excluded_surfaces") if isinstance(drift_report.get("excluded_surfaces"), dict) else {}
    for surface_id in sorted(surface_drift):
        surface_path = f"{lockfile_rel}#{surface_id}"
        details = surface_drift.get(surface_id)
        if not isinstance(details, dict):
            continue
        drift_kind = str(details.get("kind", ""))
        drift_fields = [str(field) for field in details.get("fields", []) if isinstance(field, str)]
        if drift_kind == "membership":
            findings.append(
                Finding(
                    "error",
                    "stack-lock-excluded-surface-membership-drift",
                    surface_path,
                    "Excluded surface membership differs from the current generated working set.",
                )
            )
            continue
        if drift_fields:
            findings.append(
                Finding(
                    "error",
                    "stack-lock-excluded-surface-drift",
                    surface_path,
                    f"Excluded surface fields differ from the current generated working set: {', '.join(drift_fields)}.",
                )
            )

    for field in [
        str(field)
        for field in drift_report.get("metadata_fields", [])
        if isinstance(field, str) and field in LOCK_METADATA_FIELDS
    ]:
        findings.append(
            Finding(
                "error",
                "stack-lock-metadata-drift",
                lockfile_rel,
                f"Stack lockfile field '{field}' differs from the current generated working set.",
            )
        )
    return findings


def discover_unregistered_git_roots(root: Path, config: dict[str, Any], stack_file: Path) -> list[Path]:
    repos_root = root / "repos"
    if not repos_root.exists():
        return []
    registry_paths = {
        resolve_path(stack_file, repo_info["path"]).resolve()
        for repo_info in config.get("repo_registry", {}).values()
        if isinstance(repo_info, dict) and isinstance(repo_info.get("path"), str)
    }
    lock_config = config.get("stack_lock", {})
    excluded_roots = {
        resolve_path(stack_file, value["path"]).resolve()
        for value in lock_config.get("excluded_surfaces", {}).values()
        if isinstance(lock_config, dict)
        and isinstance(value, dict)
        and isinstance(value.get("path"), str)
    } if isinstance(lock_config, dict) else set()

    candidates: set[Path] = set()
    for top_level in repos_root.iterdir():
        if not top_level.is_dir():
            continue
        candidates.add(top_level)
        for child in top_level.iterdir():
            if child.is_dir():
                candidates.add(child)

    discovered: list[Path] = []
    for candidate in sorted(candidates):
        if not repo_is_git_root(candidate):
            continue
        resolved = candidate.resolve()
        if resolved in registry_paths:
            continue
        if any(resolved == excluded or resolved.is_relative_to(excluded) for excluded in excluded_roots):
            continue
        discovered.append(resolved)
    return discovered


def validate_subsystem_registry(stack_file: Path, config: dict[str, Any]) -> list[Finding]:
    root = stack_file.parent.resolve()
    findings: list[Finding] = []
    repo_registry = config.get("repo_registry", {})
    subsystem_registry = config.get("subsystem_registry", {})

    if "cortex" in repo_registry:
        findings.append(
            Finding(
                "error",
                "cortex-repo-registry-entry",
                "stack.yaml",
                "Cortex must not be modeled as a repo_registry entry; use subsystem_registry for the root-owned runtime surface.",
            )
        )

    if not isinstance(subsystem_registry, dict):
        findings.append(
            Finding(
                "error",
                "missing-subsystem-registry",
                "stack.yaml",
                "subsystem_registry must declare root-owned runtime subsystems.",
            )
        )
        return findings

    cortex = subsystem_registry.get("cortex")
    if not isinstance(cortex, dict):
        findings.append(
            Finding(
                "error",
                "missing-cortex-subsystem",
                "stack.yaml",
                "subsystem_registry.cortex must declare the active root-owned Cortex surface.",
            )
        )
        return findings

    raw_path = cortex.get("path")
    if not isinstance(raw_path, str):
        findings.append(
            Finding(
                "error",
                "invalid-cortex-subsystem-path",
                "stack.yaml",
                "subsystem_registry.cortex.path must be a relative path string.",
            )
        )
        return findings

    cortex_path = resolve_path(stack_file, raw_path)
    cortex_rel = relative_to_root(root, cortex_path)
    if not cortex_path.exists():
        findings.append(
            Finding(
                "error",
                "missing-cortex-subsystem-path",
                cortex_rel,
                "Configured Cortex subsystem path does not exist.",
            )
        )
    elif not cortex_path.is_dir():
        findings.append(
            Finding(
                "error",
                "cortex-subsystem-path-not-directory",
                cortex_rel,
                "Configured Cortex subsystem path must be a directory.",
            )
        )

    if str(cortex.get("owner", "")) != "stack":
        findings.append(
            Finding(
                "error",
                "invalid-cortex-subsystem-owner",
                "stack.yaml",
                "subsystem_registry.cortex.owner must be 'stack'.",
            )
        )
    if str(cortex.get("model", "")) != "root-owned-subsystem":
        findings.append(
            Finding(
                "error",
                "invalid-cortex-subsystem-model",
                "stack.yaml",
                "subsystem_registry.cortex.model must be 'root-owned-subsystem'.",
            )
        )
    if str(cortex.get("status", "")) != "active":
        findings.append(
            Finding(
                "warning",
                "inactive-cortex-subsystem",
                "stack.yaml",
                "subsystem_registry.cortex.status should remain 'active' while Cortex is the live root-owned runtime surface.",
            )
        )

    adjacent_snapshot = cortex.get("adjacent_snapshot")
    if isinstance(adjacent_snapshot, str):
        adjacent_path = resolve_path(stack_file, adjacent_snapshot)
        if not adjacent_path.exists():
            findings.append(
                Finding(
                    "warning",
                    "missing-cortex-adjacent-snapshot",
                    relative_to_root(root, adjacent_path),
                    "Configured Cortex adjacent snapshot path does not exist.",
                )
            )
    return findings


def validate_gitdir_hygiene(root: Path) -> list[Finding]:
    findings: list[Finding] = []
    try:
        report = build_gitdir_hygiene_report(default_gitdir_hygiene_targets(root), apply_repairs=False)
    except Exception as exc:
        return [
            Finding(
                "warning",
                "gitdir-hygiene-audit-failed",
                "ops/stack/audit_gitdir_hygiene.py",
                f"Gitdir hygiene audit could not complete: {exc}",
            )
        ]

    for repo in report.get("repos", []):
        if not isinstance(repo, dict):
            continue
        repo_path = str(repo.get("repo_path", ""))
        for item in repo.get("findings", []):
            if not isinstance(item, dict):
                continue
            path = str(item.get("metadata_path") or item.get("target_path") or repo_path or "repos")
            findings.append(
                Finding(
                    "warning",
                    f"gitdir-hygiene-{item.get('category', 'finding')}",
                    path,
                    str(item.get("message", "Gitdir hygiene finding detected.")),
                    {"repo_path": repo_path},
                )
            )
        commands = repo.get("commands", {})
        if not isinstance(commands, dict):
            continue
        for command_name, command_result in commands.items():
            if not isinstance(command_result, dict):
                continue
            exit_code = command_result.get("exit_code")
            if exit_code == 0:
                continue
            stderr = str(command_result.get("stderr") or command_result.get("stdout") or "").strip()
            message = f"Git hygiene command '{command_name}' failed during audit."
            if stderr:
                message = f"{message} {stderr}"
            findings.append(
                Finding(
                    "warning",
                    f"gitdir-hygiene-command-{command_name}",
                    repo_path or "repos",
                    message,
                )
            )
    return findings


def validate_working_memory(stack_file: Path) -> list[Finding]:
    root = stack_file.parent.resolve()
    findings: list[Finding] = []
    for error in validate_working_memory_documents(root):
        findings.append(
            Finding(
                "error",
                "working-memory-invalid",
                str(error["path"]),
                str(error["message"]),
            )
        )
    if findings:
        return findings

    try:
        generated = build_working_memory_catalog(root)
        stored = load_working_memory_catalog(root)
    except Exception as exc:
        return [
            Finding(
                "error",
                "working-memory-index-failed",
                "runtime/cortex/catalog/memory/working-memory.latest.json",
                f"Working-memory catalog could not be built: {exc}",
            )
        ]

    if stored != generated:
        findings.append(
            Finding(
                "error",
                "working-memory-catalog-drift",
                "runtime/cortex/catalog/memory/working-memory.latest.json",
                "Working-memory catalog does not match the current structured memory documents.",
            )
        )
    return findings


def validate_execution_receipt_repairs(stack_file: Path) -> list[Finding]:
    root = stack_file.parent.resolve()
    findings: list[Finding] = []
    try:
        registry_bundle = load_tool_registry_bundle(root=root)
    except Exception as exc:
        return [
            Finding(
                "warning",
                "execution-receipt-repair-registry-unavailable",
                "docs/registry",
                f"Could not validate execution receipt repairs because the registry bundle failed to load: {exc}",
            )
        ]

    receipt_payloads = load_execution_receipt_payloads(root)
    current_digest = str(registry_bundle.get("registry_digest", ""))
    sessions_root = root / "runtime" / "atlas" / "sessions"
    if not sessions_root.exists():
        return findings

    for session_path in sorted(sessions_root.rglob("session.manifest.json")):
        session_payload = load_json_object(session_path)
        if not isinstance(session_payload, dict):
            continue
        epoch = governed_artifact_epoch_details(session_payload, source_ref=relative_to_root(root, session_path))
        if not isinstance(epoch, dict) or epoch.get("epoch") == GOVERNED_ARTIFACT_EPOCH_LEGACY_PRE_REGISTRY:
            continue
        refs = session_payload.get("refs") if isinstance(session_payload.get("refs"), dict) else {}
        original_ref = str(refs.get("execution_receipt_ref") or "").strip()
        if not original_ref:
            continue
        original_payload = receipt_payloads.get(original_ref)
        if not isinstance(original_payload, dict):
            continue
        if str(original_payload.get("registry_digest") or "") == current_digest:
            continue

        preferred_ref = resolve_preferred_execution_receipt_ref(original_ref, root=root)
        if preferred_ref == original_ref:
            findings.append(
                Finding(
                    "error",
                    "execution-receipt-repair-required",
                    original_ref,
                    "Post-cutover execution receipt does not match the current registry digest and has no truthful superseding receipt.",
                    {"session_ref": relative_to_root(root, session_path)},
                )
            )
            continue
        preferred_payload = receipt_payloads.get(preferred_ref or "")
        if not isinstance(preferred_payload, dict):
            findings.append(
                Finding(
                    "error",
                    "execution-receipt-repair-required",
                    original_ref,
                    "Post-cutover execution receipt does not match the current registry digest and has no truthful superseding receipt.",
                    {"session_ref": relative_to_root(root, session_path)},
                )
            )
            continue

        repair_basis_refs = preferred_payload.get("repair_basis_refs")
        if (
            str(preferred_payload.get("registry_digest") or "") != current_digest
            or str(preferred_payload.get("supersedes_receipt_ref") or "") != original_ref
            or not isinstance(repair_basis_refs, list)
            or len([item for item in repair_basis_refs if isinstance(item, str) and item.strip()]) == 0
            or not str(preferred_payload.get("reconciled_at") or "").strip()
            or not str(preferred_payload.get("reconciled_by_tool_version") or "").strip()
        ):
            findings.append(
                Finding(
                    "error",
                    "execution-receipt-repair-invalid",
                    preferred_ref or original_ref,
                    "Superseding execution receipt exists but does not satisfy the truthful repair contract.",
                    {"original_receipt_ref": original_ref, "session_ref": relative_to_root(root, session_path)},
                )
            )
    return findings


def validate_playbook_enforcement_tracking(stack_file: Path, config: dict[str, Any]) -> list[Finding]:
    root = stack_file.parent.resolve()
    repo_registry = config.get("repo_registry", {})
    playbook = repo_registry.get("playbook") if isinstance(repo_registry, dict) else None
    if not isinstance(playbook, dict) or not isinstance(playbook.get("path"), str):
        return []

    playbook_root = resolve_path(stack_file, playbook["path"])
    if not playbook_root.exists() or not playbook_root.is_dir() or not repo_is_git_root(playbook_root):
        return []

    repo_rel = relative_to_root(root, playbook_root)
    code, output = git_output(
        playbook_root,
        "status",
        "--short",
        "--untracked-files=all",
        "--",
        *PLAYBOOK_ENFORCEMENT_TRACKED_PATHS,
    )
    if code != 0:
        return [
            Finding(
                "warning",
                "playbook-enforcement-tracking-check-failed",
                repo_rel,
                "Unable to verify whether Playbook ATLAS enforcement files are tracked repo truth.",
            )
        ]

    untracked = []
    for line in output.splitlines():
        if line.startswith("?? "):
            candidate = line[3:].strip().replace("\\", "/")
            if candidate:
                untracked.append(candidate)
    if not untracked:
        return []

    return [
        Finding(
            "error",
            "playbook-enforcement-untracked",
            repo_rel,
            "ATLAS root validation cannot depend on untracked Playbook enforcement files.",
            {"paths": untracked},
        )
    ]


def load_json_object(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"Expected JSON object at {normalize_slashes(str(path))}.")
    return payload


def validate_verta_trust_gate(stack_file: Path, config: dict[str, Any]) -> list[Finding]:
    root = stack_file.parent.resolve()
    findings: list[Finding] = []
    lock_config = config.get("stack_lock", {})
    excluded_surfaces = lock_config.get("excluded_surfaces", {}) if isinstance(lock_config, dict) else {}
    required_surfaces = {
        "verta_core_checkout": "repos/Verta-Core",
        "verta_core_archive": "repos/Verta-Core.zip",
    }
    for surface_id, expected_path in required_surfaces.items():
        surface = excluded_surfaces.get(surface_id)
        if not isinstance(surface, dict):
            findings.append(
                Finding(
                    "error",
                    "verta-trust-surface-missing",
                    "stack.yaml",
                    f"stack_lock.excluded_surfaces.{surface_id} must remain declared for the standing Verta trust gate.",
                )
            )
            continue
        if str(surface.get("path", "")) != expected_path:
            findings.append(
                Finding(
                    "error",
                    "verta-trust-surface-path",
                    "stack.yaml",
                    f"stack_lock.excluded_surfaces.{surface_id}.path must remain '{expected_path}'.",
                )
            )
        if str(surface.get("trust_class", "")) != "untrusted":
            findings.append(
                Finding(
                    "error",
                    "verta-trust-class",
                    "stack.yaml",
                    f"stack_lock.excluded_surfaces.{surface_id}.trust_class must remain 'untrusted'.",
                )
            )
        if bool(surface.get("release_eligible")):
            findings.append(
                Finding(
                    "error",
                    "verta-release-eligibility",
                    "stack.yaml",
                    f"stack_lock.excluded_surfaces.{surface_id}.release_eligible must remain false.",
                )
            )

    catalog_expectations = {
        "runtime/cortex/catalog/knowledge/personal--verta-core.json": {
            "safe_for_indexing": "no",
            "indexing_profile": "metadata_only",
            "promotion_status": "not_promoted",
            "promotion_doc_path": None,
        },
        "runtime/cortex/catalog/knowledge/personal--verta-core-sanitized.json": {
            "safe_for_indexing": "restricted",
            "indexing_profile": "metadata_only",
            "promotion_status": "not_promoted",
            "promotion_doc_path": None,
        },
    }
    for relative_path, expected in catalog_expectations.items():
        catalog_path = root / relative_path
        if not catalog_path.exists():
            findings.append(
                Finding(
                    "error",
                    "verta-catalog-missing",
                    relative_path,
                    "Expected Verta trust-gate catalog artifact is missing.",
                )
            )
            continue
        try:
            payload = load_json_object(catalog_path)
        except Exception as exc:
            findings.append(
                Finding(
                    "error",
                    "verta-catalog-invalid",
                    relative_path,
                    f"Unable to read the Verta trust-gate catalog artifact: {exc}",
                )
            )
            continue
        for field, expected_value in expected.items():
            if payload.get(field) != expected_value:
                findings.append(
                    Finding(
                        "error",
                        "verta-catalog-policy",
                        relative_path,
                        f"Field '{field}' must remain {expected_value!r} for the standing Verta trust gate.",
                    )
                )
        if not bool(payload.get("no_execute_guarantee")):
            findings.append(
                Finding(
                    "error",
                    "verta-no-execute-guarantee",
                    relative_path,
                    "Verta trust-gate catalogs must retain no_execute_guarantee = true.",
                )
            )

    for promotion_doc in [
        root / "docs" / "knowledge" / "promotions" / "personal--verta-core.md",
        root / "docs" / "knowledge" / "promotions" / "personal--verta-core-sanitized.md",
    ]:
        if promotion_doc.exists():
            findings.append(
                Finding(
                    "error",
                    "verta-promotion-doc-present",
                    relative_to_root(root, promotion_doc),
                    "Verta trust-gate surfaces must not grow a promotion doc before an explicit trust change.",
                )
            )

    scan_roots = [
        root / "data" / "imports" / "knowledge" / "personal" / "verta-core-sanitized" / "raw",
        root / "data" / "imports" / "knowledge" / "personal" / "verta-core-sanitized" / "extracted",
    ]
    for scan_root in scan_roots:
        if not scan_root.exists():
            continue
        for candidate in scan_root.rglob("*"):
            if not candidate.is_file() or candidate.suffix.lower() not in VERTA_SURFACE_TEXT_EXTENSIONS:
                continue
            try:
                text = candidate.read_text(encoding="utf-8", errors="ignore")
            except OSError:
                continue
            for line_number, line in enumerate(text.splitlines(), start=1):
                for category, pattern in VERTA_SECRET_PATTERNS:
                    if pattern.search(line):
                        findings.append(
                            Finding(
                                "error",
                                category,
                                relative_to_root(root, candidate),
                                "Potential live secret material was detected in a Verta trust-gated surface.",
                                {"line_number": line_number, "line_preview": line.strip()[:220]},
                            )
                        )
                        break
    return findings


def validate_world_model_state(stack_file: Path) -> list[Finding]:
    root = stack_file.parent.resolve()
    findings: list[Finding] = []
    snapshot_path = root / "runtime" / "state" / "atlas" / "world-model.snapshot.latest.json"
    attention_path = root / "runtime" / "state" / "atlas" / "world-model.attention.latest.json"
    descriptor_root = root / "runtime" / "cortex" / "artifacts"
    descriptors = load_descriptors(descriptor_root) if descriptor_root.exists() else []

    required_files = [
        (snapshot_path, "state"),
        (attention_path, "attention"),
    ]
    payloads: dict[str, dict[str, Any]] = {}
    for path, snapshot_kind in required_files:
        relative_path = relative_to_root(root, path)
        if not path.exists():
            findings.append(
                Finding(
                    "error",
                    "missing-world-model-artifact",
                    relative_path,
                    f"Required world-model {snapshot_kind} artifact is missing.",
                )
            )
            continue
        try:
            payload = load_json_object(path)
        except Exception as exc:
            findings.append(
                Finding(
                    "error",
                    "invalid-world-model-artifact",
                    relative_path,
                    f"Unable to read the world-model {snapshot_kind} artifact: {exc}",
                )
            )
            continue
        payloads[snapshot_kind] = payload
        if payload.get("contract_version") != "atlas.state.snapshot.v1":
            findings.append(
                Finding(
                    "error",
                    "world-model-contract-version",
                    relative_path,
                    "World-model artifacts must use contract_version 'atlas.state.snapshot.v1'.",
                )
            )
        if payload.get("snapshot_kind") != snapshot_kind:
            findings.append(
                Finding(
                    "error",
                    "world-model-snapshot-kind",
                    relative_path,
                    f"World-model artifact must declare snapshot_kind '{snapshot_kind}'.",
                )
            )
        expected_digest = stable_json_digest(
            {
                key: value
                for key, value in payload.items()
                if key != "content_digest"
            }
        )
        if payload.get("content_digest") != expected_digest:
            findings.append(
                Finding(
                    "error",
                    "world-model-content-digest",
                    relative_path,
                    "World-model artifact content_digest does not match the stable payload.",
                )
            )

    snapshot = payloads.get("state")
    attention = payloads.get("attention")
    if not isinstance(snapshot, dict):
        return findings

    source_refs = snapshot.get("source_refs")
    if not isinstance(source_refs, dict):
        findings.append(
            Finding(
                "error",
                "world-model-source-refs",
                relative_to_root(root, snapshot_path),
                "State snapshot must declare source_refs.",
            )
        )
    else:
        for required_key in [
            "descriptor_root",
            "registry_refs",
            "event_latest_refs",
            "knowledge_latest_refs",
            "validation_refs",
        ]:
            if required_key not in source_refs:
                findings.append(
                    Finding(
                        "error",
                        "world-model-source-ref-key",
                        relative_to_root(root, snapshot_path),
                        f"State snapshot source_refs must include '{required_key}'.",
                    )
                )

    observations = snapshot.get("observations", [])
    inventory_entries = snapshot.get("inventory_entries", [])
    attention_items = snapshot.get("attention_items", [])
    stored_observations = load_observations(root)
    observation_source_refs = {
        str(item.get("source_ref"))
        for item in observations
        if isinstance(item, dict) and isinstance(item.get("source_ref"), str)
    }
    stored_observation_source_refs = {
        str(item.get("source_ref"))
        for item in stored_observations
        if isinstance(item, dict) and isinstance(item.get("source_ref"), str)
    }
    snapshot_observation_keys = {
        (
            canonical_observation_type(
                str(item.get("observation_type", "")),
                status=str(item.get("status", "")),
            ),
            str(item.get("source_ref")),
        )
        for item in observations
        if isinstance(item, dict) and isinstance(item.get("source_ref"), str)
    }
    stored_observation_keys = {
        (
            canonical_observation_type(
                str(item.get("observation_type", "")),
                status=str(item.get("status", "")),
            ),
            str(item.get("source_ref")),
        )
        for item in stored_observations
        if isinstance(item, dict) and isinstance(item.get("source_ref"), str)
    }
    inventory_source_refs = {
        str(item.get("source_ref"))
        for item in inventory_entries
        if isinstance(item, dict) and isinstance(item.get("source_ref"), str)
    }
    attention_item_keys = {
        (str(item.get("kind", "")), str(item.get("source_ref")))
        for item in attention_items
        if isinstance(item, dict) and isinstance(item.get("source_ref"), str)
    }

    def optional_string(value: Any) -> str | None:
        if isinstance(value, str) and value.strip():
            return value.strip()
        return None

    legacy_backfill_by_session_ref = {
        optional_string(descriptor.get("links", {}).get("original_session_ref")): descriptor
        for descriptor in descriptors
        if str(descriptor.get("artifact_type", "")) == "legacy_runtime_backfill"
        and isinstance(descriptor.get("links"), dict)
        and optional_string(descriptor.get("links", {}).get("original_session_ref"))
    }

    def source_payload(source_ref: str | None) -> dict[str, Any] | None:
        if not isinstance(source_ref, str) or not source_ref.strip():
            return None
        candidate = root / Path(source_ref)
        if not candidate.exists():
            return None
        try:
            return load_json_object(candidate)
        except Exception:
            return None

    def approval_observation_type(payload: dict[str, Any]) -> tuple[str, str]:
        approval_status = optional_string(payload.get("approval_status")) or "unknown"
        expiry_at = optional_string(payload.get("expiry_at"))
        if expiry_at:
            try:
                expiry = datetime.fromisoformat(expiry_at.replace("Z", "+00:00"))
                if expiry <= datetime.now(timezone.utc):
                    return "execution_expired", "expired"
            except ValueError:
                pass
        if approval_status == "rejected":
            return "execution_rejected", approval_status
        return "execution_approved", approval_status

    def require_observation(
        observation_type: str,
        source_ref: str | None,
        *,
        owner_ref: str,
    ) -> None:
        normalized_source_ref = optional_string(source_ref)
        if not normalized_source_ref:
            return
        if (observation_type, normalized_source_ref) not in snapshot_observation_keys:
            findings.append(
                Finding(
                    "error",
                    "missing-required-observation",
                    relative_to_root(root, snapshot_path),
                    f"Governed flow '{owner_ref}' is missing observation '{observation_type}' for '{normalized_source_ref}' in the state snapshot.",
                )
            )
        if (observation_type, normalized_source_ref) not in stored_observation_keys:
            findings.append(
                Finding(
                    "error",
                    "missing-required-observation-store",
                    relative_to_root(root, snapshot_path),
                    f"Governed flow '{owner_ref}' is missing observation '{observation_type}' for '{normalized_source_ref}' in the observation store.",
                )
            )

    for descriptor in descriptors:
        artifact_type = str(descriptor.get("artifact_type", ""))
        source_ref = str(descriptor.get("source_ref", ""))
        state = descriptor.get("state", {})
        if artifact_type == "session_manifest" and str(state.get("final_status", "")) in {"completed", "resume_ready", "failed"}:
            if source_ref not in observation_source_refs:
                findings.append(
                    Finding(
                        "error",
                        "missing-session-observation",
                        relative_to_root(root, snapshot_path),
                        f"Completed session '{source_ref}' is missing from the state snapshot observations.",
                    )
                )
            if source_ref not in inventory_source_refs:
                findings.append(
                    Finding(
                        "error",
                        "missing-session-inventory-entry",
                        relative_to_root(root, snapshot_path),
                        f"Completed session '{source_ref}' is missing from the state snapshot inventory.",
                    )
                )
            if source_ref not in stored_observation_source_refs:
                findings.append(
                    Finding(
                        "error",
                        "missing-session-observation-store",
                        relative_to_root(root, snapshot_path),
                        f"Completed session '{source_ref}' is missing from the emitted observation store.",
                    )
                )
            session_payload = source_payload(source_ref)
            if not isinstance(session_payload, dict):
                findings.append(
                    Finding(
                        "error",
                        "invalid-governed-session-artifact",
                        relative_to_root(root, snapshot_path),
                        f"Completed governed session '{source_ref}' could not be loaded for observation validation.",
                    )
                )
                continue

            governed_surfaces = session_payload.get("governed_surfaces")
            epoch_details = governed_artifact_epoch_details(session_payload, source_ref=source_ref)
            if isinstance(epoch_details, dict) and epoch_details.get("epoch") == GOVERNED_ARTIFACT_EPOCH_LEGACY_PRE_REGISTRY:
                backfill_descriptor = legacy_backfill_by_session_ref.get(source_ref)
                if backfill_descriptor is None:
                    findings.append(
                        Finding(
                            "error",
                            "missing-legacy-backfill-record",
                            relative_to_root(root, snapshot_path),
                            f"Historical session '{source_ref}' is missing a descriptor-backed legacy backfill record.",
                        )
                    )
                    continue
                require_observation(
                    "governed_compatibility",
                    optional_string(backfill_descriptor.get("source_ref")),
                    owner_ref=source_ref,
                )
                continue

            close_receipt_refs = descriptor.get("links", {}).get("close_receipt_refs", [])
            if not isinstance(close_receipt_refs, list) or not any(
                isinstance(item, str) and item.strip() for item in close_receipt_refs
            ):
                findings.append(
                    Finding(
                        "error",
                        "missing-session-closure-evidence",
                        relative_to_root(root, snapshot_path),
                        f"Completed session '{source_ref}' is missing closure receipt refs.",
                    )
                )

            if not isinstance(governed_surfaces, dict):
                continue
            execution_surface = governed_surfaces.get("execution")
            if not isinstance(execution_surface, dict) or not optional_string(execution_surface.get("tool_id")):
                continue

            refs = session_payload.get("refs") if isinstance(session_payload.get("refs"), dict) else {}
            completion = session_payload.get("completion") if isinstance(session_payload.get("completion"), dict) else {}

            assignment_ref = optional_string(session_payload.get("worker", {}).get("assignment_ref")) or optional_string(refs.get("assignment_ref")) or optional_string(descriptor.get("links", {}).get("assignment_ref"))
            request_ref = optional_string(refs.get("request_ref")) or optional_string(descriptor.get("links", {}).get("request_ref"))
            approval_ref = optional_string(refs.get("approval_receipt_ref")) or optional_string(descriptor.get("links", {}).get("approval_receipt_ref"))
            execution_receipt_ref = optional_string(refs.get("execution_receipt_ref")) or optional_string(descriptor.get("links", {}).get("execution_receipt_ref"))
            final_status = optional_string(completion.get("final_status")) or optional_string(state.get("final_status"))
            final_status_ref = optional_string(completion.get("final_status_ref")) or optional_string(descriptor.get("links", {}).get("final_status_ref"))
            merge_request_refs = [
                item for item in (refs.get("merge_request_refs") or descriptor.get("links", {}).get("merge_request_refs") or [])
                if isinstance(item, str) and item.strip()
            ]
            pause_status_refs = [
                item for item in (refs.get("pause_status_refs") or descriptor.get("links", {}).get("pause_status_refs") or [])
                if isinstance(item, str) and item.strip()
            ]
            resume_context_refs = [
                item for item in (refs.get("resume_context_refs") or descriptor.get("links", {}).get("resume_context_refs") or [])
                if isinstance(item, str) and item.strip()
            ]
            merge_assignment_ref = optional_string(refs.get("merge_assignment_ref")) or optional_string(descriptor.get("links", {}).get("merge_assignment_ref"))
            merge_completion_ref = optional_string(refs.get("merge_completion_ref")) or optional_string(descriptor.get("links", {}).get("merge_completion_ref"))

            running_status_ref = None
            status_refs = [
                item for item in (refs.get("status_refs") or descriptor.get("links", {}).get("status_refs") or [])
                if isinstance(item, str) and item.strip()
            ]
            for status_ref in status_refs:
                status_payload = source_payload(status_ref)
                if isinstance(status_payload, dict) and optional_string(status_payload.get("state")) == "running":
                    running_status_ref = status_ref
                    break

            require_observation("assignment_created", assignment_ref, owner_ref=source_ref)
            require_observation("heartbeat", running_status_ref, owner_ref=source_ref)
            require_observation("execution_requested", request_ref, owner_ref=source_ref)

            approval_payload = source_payload(approval_ref)
            if isinstance(approval_payload, dict):
                approval_type, _ = approval_observation_type(approval_payload)
                require_observation(approval_type, approval_ref, owner_ref=source_ref)

            expected_execution_observation = "execution_completed"
            execution_receipt_payload = source_payload(execution_receipt_ref)
            if isinstance(execution_receipt_payload, dict):
                execution_result = optional_string(execution_receipt_payload.get("result")) or ""
                if execution_result in {"blocked", "failed"}:
                    expected_execution_observation = "execution_failed"
            require_observation(expected_execution_observation, execution_receipt_ref, owner_ref=source_ref)
            if final_status in {"completed", "failed"}:
                require_observation("completed", final_status_ref, owner_ref=source_ref)
            for merge_request_ref in merge_request_refs:
                require_observation("merge_requested", merge_request_ref, owner_ref=source_ref)
            for pause_status_ref in pause_status_refs:
                require_observation("paused", pause_status_ref, owner_ref=source_ref)
            require_observation("merger_assigned", merge_assignment_ref, owner_ref=source_ref)
            if resume_context_refs:
                for resume_context_ref in resume_context_refs:
                    require_observation("resume_ready", resume_context_ref, owner_ref=source_ref)
            else:
                require_observation("resume_ready", merge_completion_ref, owner_ref=source_ref)

    if isinstance(attention, dict):
        snapshot_attention_ids = sorted(
            str(item.get("attention_id"))
            for item in attention_items
            if isinstance(item, dict) and isinstance(item.get("attention_id"), str)
        )
        attention_attention_ids = sorted(
            str(item.get("attention_id"))
            for item in attention.get("attention_items", [])
            if isinstance(item, dict) and isinstance(item.get("attention_id"), str)
        )
        if snapshot_attention_ids != attention_attention_ids:
            findings.append(
                Finding(
                    "error",
                    "attention-artifact-drift",
                    relative_to_root(root, attention_path),
                    "Attention artifact does not match the state snapshot attention items.",
                )
            )

    return findings


def validate_proposed_sessions(stack_file: Path) -> list[Finding]:
    root = stack_file.parent.resolve()
    findings: list[Finding] = []
    proposed_root = root / "runtime" / "atlas" / "proposed-sessions"
    if not proposed_root.exists():
        return findings

    attention_ids: set[str] = set()
    attention_path = root / "runtime" / "state" / "atlas" / "world-model.attention.latest.json"
    if attention_path.exists():
        try:
            attention_payload = load_json_object(attention_path)
            attention_ids = {
                f"attention:{item.get('attention_id')}"
                for item in attention_payload.get("attention_items", [])
                if isinstance(item, dict) and isinstance(item.get("attention_id"), str)
            }
        except Exception:
            attention_ids = set()

    for path in sorted(proposed_root.rglob("session.manifest.json")):
        relative_path = relative_to_root(root, path)
        try:
            payload = load_json_object(path)
        except Exception as exc:
            findings.append(
                Finding(
                    "error",
                    "invalid-proposed-session",
                    relative_path,
                    f"Proposed session could not be parsed: {exc}",
                )
            )
            continue

        if payload.get("contract_version") != "atlas.session.v1":
            findings.append(Finding("error", "invalid-proposed-session", relative_path, "Proposed session must use atlas.session.v1."))
        if payload.get("scenario") != "proposed_session":
            findings.append(Finding("error", "invalid-proposed-session", relative_path, "Proposed session must use scenario 'proposed_session'."))
        if payload.get("session_state") != "proposed":
            findings.append(Finding("error", "invalid-proposed-session", relative_path, "Proposed session must remain in session_state 'proposed'."))
        if payload.get("session_role") != "proposed_session":
            findings.append(Finding("error", "invalid-proposed-session", relative_path, "Proposed session must declare session_role 'proposed_session'."))

        refs = payload.get("refs") if isinstance(payload.get("refs"), dict) else {}
        if any(refs.get(field) for field in ("request_ref", "approval_receipt_ref", "execution_receipt_ref", "bridge_record_ref")):
            findings.append(
                Finding(
                    "error",
                    "proposal-triggers-execution",
                    relative_path,
                    "Proposed sessions may not include request, approval, execution, or bridge refs.",
                )
            )
        if any(
            isinstance(refs.get(field), list) and refs.get(field)
            for field in ("status_refs", "merge_request_refs", "pause_status_refs", "resume_context_refs")
        ):
            findings.append(
                Finding(
                    "error",
                    "proposal-triggers-execution",
                    relative_path,
                    "Proposed sessions may not include live status, merge, or resume refs.",
                )
            )

        proposal = payload.get("proposal") if isinstance(payload.get("proposal"), dict) else None
        if proposal is None:
            findings.append(Finding("error", "missing-proposal-provenance", relative_path, "Proposed session is missing the proposal provenance block."))
            continue

        initiative_ref = proposal.get("initiative_ref")
        if not isinstance(initiative_ref, str) or not initiative_ref.strip():
            findings.append(Finding("error", "missing-proposal-provenance", relative_path, "proposal.initiative_ref is required."))
        elif not (root / Path(initiative_ref)).resolve().exists():
            findings.append(Finding("error", "missing-proposal-provenance", relative_path, f"proposal.initiative_ref does not resolve: {initiative_ref}"))

        triggering_attention_refs = proposal.get("triggering_attention_refs")
        if not isinstance(triggering_attention_refs, list) or not any(isinstance(ref, str) and ref.strip() for ref in triggering_attention_refs):
            findings.append(Finding("error", "missing-proposal-provenance", relative_path, "proposal.triggering_attention_refs must be non-empty."))
        else:
            for ref in triggering_attention_refs:
                if not isinstance(ref, str) or not ref.strip():
                    findings.append(Finding("error", "missing-proposal-provenance", relative_path, "proposal.triggering_attention_refs must contain non-empty strings."))
                elif ref not in attention_ids:
                    findings.append(Finding("error", "missing-proposal-provenance", relative_path, f"proposal.triggering_attention_ref does not resolve: {ref}"))

        for field in (
            "supporting_evidence_refs",
            "related_plan_refs",
            "related_decision_refs",
            "related_hypothesis_refs",
            "related_prior_session_refs",
        ):
            refs_value = proposal.get(field, [])
            if field == "supporting_evidence_refs" and (not isinstance(refs_value, list) or not refs_value):
                findings.append(Finding("error", "missing-proposal-provenance", relative_path, "proposal.supporting_evidence_refs must be non-empty."))
                continue
            if not isinstance(refs_value, list):
                findings.append(Finding("error", "missing-proposal-provenance", relative_path, f"proposal.{field} must be an array."))
                continue
            for ref in refs_value:
                if not isinstance(ref, str) or not ref.strip():
                    findings.append(Finding("error", "missing-proposal-provenance", relative_path, f"proposal.{field} must contain non-empty strings."))
                    continue
                if not (root / Path(ref)).resolve().exists():
                    findings.append(Finding("error", "missing-proposal-provenance", relative_path, f"proposal.{field} does not resolve: {ref}"))

    return findings


def validate_tool_registry(root: Path) -> list[Finding]:
    try:
        bundle = load_tool_registry_bundle(root=root)
    except Exception as exc:
        return [
            Finding(
                "error",
                "invalid-tool-registry",
                "docs/registry",
                f"ATLAS tool or extension registry could not be loaded: {exc}",
            )
        ]

    findings: list[Finding] = []
    registry_digest = str(bundle.get("registry_digest", "")).strip()
    if not registry_digest:
        findings.append(
            Finding(
                "error",
                "missing-tool-registry-digest",
                "docs/registry",
                "ATLAS tool or extension registry did not resolve to a stable digest.",
            )
        )
    return findings


def iter_relative_directory_targets(config: dict[str, Any]) -> list[tuple[str, str]]:
    targets: list[tuple[str, str]] = []
    for key, value in config.get("paths", {}).items():
        if isinstance(value, str):
            targets.append((f"paths.{key}", value))
    for group, children in config.get("subpaths", {}).items():
        if isinstance(children, dict):
            for key, value in children.items():
                if isinstance(value, str):
                    targets.append((f"subpaths.{group}.{key}", value))
    targets.append(("subpaths.docs.ops", "docs/ops"))
    return targets


def should_scan_file(path: Path) -> bool:
    if path.suffix.lower() not in TEXT_EXTENSIONS:
        return False
    lowered_parts = {part.lower() for part in path.parts}
    return not (lowered_parts & {part.lower() for part in SCAN_SKIP_DIRS})


def is_import_evidence_file(root: Path, path: Path) -> bool:
    try:
        relative = path.resolve().relative_to(root.resolve())
    except ValueError:
        return False
    parts = [part.lower() for part in relative.parts]
    if len(parts) < 4:
        return False
    if parts[0] != "data" or parts[1] != "imports":
        return False
    return "raw" in parts[2:] or "extracted" in parts[2:]


def collect_text_scan_roots(root: Path, config: dict[str, Any], stack_file: Path) -> list[Path]:
    roots: list[Path] = []
    for candidate in DECLARED_STACK_SURFACE_SCAN_CANDIDATES:
        candidate_path = root / candidate
        if candidate_path.exists():
            roots.append(candidate_path)
    for repo in config.get("repo_registry", {}).values():
        if isinstance(repo, dict) and isinstance(repo.get("path"), str) and repo.get("status") in {"active", "incubating", "unmanaged"}:
            repo_path = resolve_path(stack_file, repo["path"])
            if repo_path.resolve() == root.resolve():
                continue
            if repo_path.exists():
                roots.append(repo_path)
    seen: set[Path] = set()
    result: list[Path] = []
    for item in roots:
        if item not in seen:
            seen.add(item)
            result.append(item)
    return result


def validate_declared_surface_scan_coverage(root: Path, config: dict[str, Any], stack_file: Path) -> list[Finding]:
    scan_roots = {path.resolve() for path in collect_text_scan_roots(root, config, stack_file)}
    findings: list[Finding] = []
    for surface in REQUIRED_STACK_GOVERNANCE_SCAN_SURFACES:
        surface_path = root / surface
        if not surface_path.exists():
            continue
        if surface_path.resolve() not in scan_roots:
            findings.append(
                Finding(
                    "error",
                    "declared-scan-surface-missing",
                    relative_to_root(root, surface_path),
                    "Required root governance surface exists but is not covered by declared text scanning.",
                    {"surface": surface},
                )
            )
    return findings


def iter_scan_files(roots: list[Path]) -> list[Path]:
    files: list[Path] = []
    for root in roots:
        if root.is_file():
            if should_scan_file(root):
                files.append(root)
            continue
        for dirpath, dirnames, filenames in os.walk(root):
            dirnames[:] = [name for name in dirnames if name not in SCAN_SKIP_DIRS]
            current = Path(dirpath)
            for filename in filenames:
                candidate = current / filename
                if should_scan_file(candidate):
                    files.append(candidate)
    return files


def build_findings(
    stack_file: Path,
    config: dict[str, Any],
    *,
    lock_file_override: Path | None = None,
    allow_missing_locked_repos: bool = False,
    required_present_repo_ids: set[str] | None = None,
) -> list[Finding]:
    root = stack_file.parent.resolve()
    findings: list[Finding] = []
    required_present_repo_ids = {
        str(repo_id).strip()
        for repo_id in (required_present_repo_ids or set())
        if str(repo_id).strip()
    }
    lockfile_path = lock_file_override.resolve() if lock_file_override is not None else lockfile_output_path(stack_file, config)
    lockfile_rel = relative_to_root(root, lockfile_path)
    preloaded_lockfile: dict[str, Any] | None = None
    allowed_missing_locked_repo_ids: set[str] = set()
    if allow_missing_locked_repos and lockfile_path.exists():
        try:
            candidate_lockfile = load_lockfile(lockfile_path)
        except Exception:
            candidate_lockfile = None
        if isinstance(candidate_lockfile, dict):
            preloaded_lockfile = candidate_lockfile
            locked_components = candidate_lockfile.get("components")
            if isinstance(locked_components, dict):
                allowed_missing_locked_repo_ids = {
                    str(repo_id).strip()
                    for repo_id, component in locked_components.items()
                    if str(repo_id).strip() and isinstance(component, dict)
                } - required_present_repo_ids

    findings.extend(validate_declared_surface_scan_coverage(root, config, stack_file))
    try:
        _, _, topology_issues = validate_atlas_topology_contract_files(stack_file=stack_file)
    except Exception as exc:
        findings.append(
            Finding(
                "error",
                "atlas-topology-validator-crash",
                "ops/validation/atlas_topology_contract.py",
                f"Atlas topology validator failed before completion: {exc}",
            )
        )
    else:
        findings.extend(Finding(item.severity, item.category, item.path, item.message, item.details) for item in topology_issues)
    findings.extend(validate_tool_registry(root))
    findings.extend(validate_subsystem_registry(stack_file, config))
    findings.extend(validate_execution_receipt_repairs(stack_file))
    findings.extend(validate_playbook_enforcement_tracking(stack_file, config))
    findings.extend(validate_verta_trust_gate(stack_file, config))
    findings.extend(validate_working_memory(stack_file))
    findings.extend(validate_world_model_state(stack_file))
    findings.extend(validate_proposed_sessions(stack_file))

    for label, raw_path in iter_relative_directory_targets(config):
        resolved = resolve_path(stack_file, raw_path)
        rel = normalize_slashes(str(resolved.relative_to(root))) if resolved.is_relative_to(root) else normalize_slashes(str(resolved))
        if not resolved.exists():
            findings.append(Finding("critical", "missing-directory", rel, f"Required directory from {label} is missing.", {"config_value": raw_path}))
        elif not resolved.is_dir():
            findings.append(Finding("critical", "path-not-directory", rel, f"Configured directory target for {label} is not a directory.", {"config_value": raw_path}))

    for repo_id, repo_info in config.get("repo_registry", {}).items():
        if not isinstance(repo_info, dict) or not isinstance(repo_info.get("path"), str):
            findings.append(Finding("critical", "invalid-repo-config", f"repo_registry.{repo_id}", "Repo entry is missing a valid path."))
            continue
        repo_path = resolve_path(stack_file, repo_info["path"])
        status = str(repo_info.get("status", "unknown"))
        repo_rel = normalize_slashes(str(repo_path.relative_to(root))) if repo_path.is_relative_to(root) else normalize_slashes(str(repo_path))
        if not repo_rel:
            repo_rel = "."
        is_stack_control_repo = repo_path == root
        if not repo_path.exists():
            if allow_missing_locked_repos and repo_id in allowed_missing_locked_repo_ids:
                continue
            findings.append(Finding("critical", "missing-repo-path", repo_rel, f"Repo path for '{repo_id}' does not exist.", {"status": status}))
            continue
        if not repo_path.is_dir():
            findings.append(Finding("critical", "repo-path-not-directory", repo_rel, f"Repo path for '{repo_id}' is not a directory.", {"status": status}))
            continue
        if not is_stack_control_repo and not repo_is_git_root(repo_path):
            findings.append(
                Finding(
                    "warning",
                    "repo-path-not-git-root",
                    repo_rel,
                    "Repo registry path resolves inside another git worktree and cannot be pinned as an independent child repo.",
                    {"repo_id": repo_id, "status": status},
                )
            )

        agents_path = repo_path / "AGENTS.md"
        singular_agent_path = repo_path / "AGENT.md"
        config_path = repo_path / ".codex" / "config.toml"
        readme_path = repo_path / ("README-STACK.md" if is_stack_control_repo else "README.md")
        if status in AGENTS_EXPECTED_STATUSES and not agents_path.exists():
            details: dict[str, Any] = {"status": status}
            message = "Expected AGENTS.md is missing."
            if singular_agent_path.exists():
                message = "Expected AGENTS.md is missing; singular AGENT.md exists."
                details["singular_agent_present"] = True
            findings.append(Finding("error" if status in ACTIVE_STATUSES else "warning", "missing-agents", repo_rel, message, details))
        if status in CONFIG_EXPECTED_STATUSES and not config_path.exists() and not is_stack_control_repo:
            findings.append(Finding("error", "missing-codex-config", repo_rel, "Expected .codex/config.toml is missing for an active repo.", {"status": status}))
        if status in ACTIVE_STATUSES and not readme_path.exists():
            readme_name = "README-STACK.md" if is_stack_control_repo else "README.md"
            findings.append(Finding("warning", "missing-readme", repo_rel, f"{readme_name} is missing for an active repo.", {"status": status}))

        for relative_dir in MUTABLE_DIR_CANDIDATES:
            candidate = repo_path / relative_dir
            if candidate.exists():
                rel = normalize_slashes(str(candidate.relative_to(root)))
                findings.append(Finding("warning", "mutable-state-in-repo", rel, "Mutable or generated state is present inside a repo path.", {"repo_id": repo_id, "state_path": relative_dir}))
        for env_candidate in list(repo_path.glob(".env")) + list(repo_path.glob(".env.*")):
            if not is_repo_local_secret_candidate(env_candidate):
                continue
            findings.append(Finding("warning", "repo-local-secret-material", normalize_slashes(str(env_candidate.relative_to(root))), "Repo-local environment file detected; secrets should not be part of default exports.", {"repo_id": repo_id}))
        for pattern in ROOT_LOG_PATTERNS:
            for file_path in repo_path.glob(pattern):
                if file_path.is_file():
                    findings.append(Finding("warning", "mutable-artifact-in-repo-root", normalize_slashes(str(file_path.relative_to(root))), "Mutable log, temp, or database artifact detected in repo root.", {"repo_id": repo_id, "pattern": pattern}))
        for pattern in ROOT_CAPTURE_PATTERNS:
            for file_path in repo_path.glob(pattern):
                if file_path.is_file():
                    findings.append(Finding("warning", "capture-artifact-in-repo-root", normalize_slashes(str(file_path.relative_to(root))), "Likely review or capture artifact detected in repo root.", {"repo_id": repo_id, "pattern": pattern}))
    if not lockfile_path.exists():
        findings.append(
            Finding(
                "error",
                "missing-stack-lockfile",
                lockfile_rel,
                "Stack lockfile is missing. Generate it before relying on root-driven orchestration.",
            )
        )
    else:
        lockfile = preloaded_lockfile
        if lockfile is None:
            try:
                lockfile = load_lockfile(lockfile_path)
            except Exception as exc:
                findings.append(
                    Finding(
                        "error",
                        "invalid-stack-lockfile",
                        lockfile_rel,
                        f"Stack lockfile could not be loaded: {exc}",
                    )
                )
                lockfile = None
        if isinstance(lockfile, dict):
            if lockfile.get("schema_version") != STACK_LOCK_SCHEMA_VERSION:
                findings.append(
                    Finding(
                        "error",
                        "stack-lock-schema-version",
                        lockfile_rel,
                        f"Stack lockfile schema_version must be '{STACK_LOCK_SCHEMA_VERSION}'.",
                    )
                )
            if allow_missing_locked_repos:
                canonical_lock = None
            else:
                try:
                    canonical_lock = build_canonical_lockfile_artifacts(config=config, root=root)
                except Exception as exc:
                    findings.append(
                        Finding(
                            "error",
                            "stack-lock-build-failed",
                            lockfile_rel,
                            f"Current stack lock payload could not be rebuilt: {exc}",
                        )
                    )
                    canonical_lock = None
            generated_lock = canonical_lock.get("payload") if isinstance(canonical_lock, dict) else None
            drift_report = describe_lock_payload_drift(lockfile, generated_lock) if isinstance(generated_lock, dict) else None
            canonical_bytes = canonical_lock.get("bytes") if isinstance(canonical_lock, dict) else None
            lockfile_bytes = lockfile_path.read_bytes()
            lockfile_bytes_match = isinstance(canonical_bytes, bytes) and lockfile_bytes == canonical_bytes
            root_lock_refresh_state = classify_root_lock_refresh_state(
                root=root,
                lockfile_path=lockfile_path,
                lockfile=lockfile,
                lockfile_bytes=lockfile_bytes,
                canonical_lock=canonical_lock,
                drift_report=drift_report,
            )
            accepted_root_refresh_repo_id = (
                str(root_lock_refresh_state.get("repo_id"))
                if isinstance(root_lock_refresh_state, dict) and root_lock_refresh_state.get("state") == "accepted"
                else None
            )
            has_payload_drift = isinstance(drift_report, dict) and bool(drift_report.get("has_drift"))
            has_render_drift = isinstance(canonical_bytes, bytes) and not lockfile_bytes_match
            if isinstance(root_lock_refresh_state, dict) and root_lock_refresh_state.get("state") == "accepted":
                findings.append(
                    Finding(
                        "info",
                        "root-lock-refresh-accepted",
                        lockfile_rel,
                        "Committed stack.lock.yaml self-refresh is accepted because the pinned root commit is an ancestor and stack.lock.yaml is the only intervening root diff.",
                        root_lock_refresh_state.get("details") if isinstance(root_lock_refresh_state.get("details"), dict) else None,
                    )
                )
            elif has_payload_drift or has_render_drift:
                findings.append(
                    Finding(
                        "error",
                        "stack-lock-drift",
                        lockfile_rel,
                        "Stack lockfile does not match the current pinned working set.",
                    )
                )
                if has_render_drift:
                    findings.append(
                        Finding(
                            "error",
                            "stack-lock-render-drift",
                            lockfile_rel,
                            "Stack lockfile bytes do not match the canonical generated lockfile payload.",
                        )
                    )
                if has_payload_drift and isinstance(drift_report, dict):
                    findings.extend(
                        describe_stack_lock_drift(
                            lockfile_rel=lockfile_rel,
                            drift_report=drift_report,
                        )
                    )
            elif isinstance(root_lock_refresh_state, dict) and root_lock_refresh_state.get("state") == "pending":
                findings.append(
                    Finding(
                        "info",
                        "root-lock-refresh-pending",
                        lockfile_rel,
                        "Root preflight is green with a pending stack.lock.yaml self-refresh because it is the sole root delta and already matches the canonical live working set.",
                        root_lock_refresh_state.get("details") if isinstance(root_lock_refresh_state.get("details"), dict) else None,
                    )
                )
            else:
                accepted_root_refresh_repo_id = None

            components = lockfile.get("components")
            if not isinstance(components, dict):
                findings.append(
                    Finding(
                        "error",
                        "stack-lock-components-shape",
                        lockfile_rel,
                        "Stack lockfile components must be a mapping keyed by repo id.",
                    )
                )
            else:
                required_component_fields = set(LOCK_COMPONENT_FIELDS)
                for component_id, component in components.items():
                    component_path = f"{lockfile_rel}#{component_id}"
                    if not isinstance(component, dict):
                        findings.append(Finding("error", "stack-lock-component-shape", component_path, "Stack lockfile component entry must be a mapping."))
                        continue
                    missing_fields = sorted(field for field in required_component_fields if field not in component)
                    if missing_fields:
                        findings.append(
                            Finding(
                                "error",
                                "stack-lock-component-fields",
                                component_path,
                                f"Stack lockfile component is missing required fields: {', '.join(missing_fields)}",
                            )
                        )
                    repo_path = resolve_path(stack_file, str(component.get("path", "")))
                    if not repo_path.exists():
                        if allow_missing_locked_repos and component_id in allowed_missing_locked_repo_ids:
                            continue
                        findings.append(Finding("error", "stack-lock-missing-path", component_path, "Pinned component path does not exist on disk."))
                        continue
                    if not repo_path.is_dir():
                        findings.append(Finding("error", "stack-lock-path-not-directory", component_path, "Pinned component path is not a directory."))
                        continue
                    if not repo_is_git_root(repo_path):
                        findings.append(Finding("error", "stack-lock-not-git-root", component_path, "Pinned component path is not a git root."))
                        continue
                    trust_class = str(component.get("trust_class", ""))
                    if trust_class not in TRUST_CLASSES:
                        findings.append(Finding("error", "stack-lock-trust-class", component_path, f"Unsupported trust_class '{trust_class}' in stack lockfile."))
                    ref_problem = None if component_id == accepted_root_refresh_repo_id else verify_locked_ref(repo_path, component)
                    if ref_problem:
                        findings.append(Finding("error", "stack-lock-missing-ref", component_path, ref_problem))
                    if bool(component.get("release_eligible")) and trust_class != "trusted":
                        findings.append(
                            Finding(
                                "error",
                                "stack-lock-release-trust",
                                component_path,
                                "Only trusted components may be marked release_eligible.",
                            )
                        )

            excluded_surfaces = lockfile.get("excluded_surfaces")
            if not isinstance(excluded_surfaces, dict):
                findings.append(
                    Finding(
                        "error",
                        "stack-lock-excluded-surfaces-shape",
                        lockfile_rel,
                        "Stack lockfile excluded_surfaces must be a mapping keyed by surface id.",
                    )
                )
            else:
                for surface_id, surface in excluded_surfaces.items():
                    surface_path = f"{lockfile_rel}#{surface_id}"
                    if not isinstance(surface, dict):
                        findings.append(Finding("error", "stack-lock-excluded-surface-shape", surface_path, "Excluded surface entry must be a mapping."))
                        continue
                    missing_fields = sorted(field for field in LOCK_EXCLUDED_SURFACE_FIELDS if field not in surface)
                    if missing_fields:
                        findings.append(
                            Finding(
                                "error",
                                "stack-lock-excluded-surface-fields",
                                surface_path,
                                f"Excluded surface entry is missing required fields: {', '.join(missing_fields)}",
                            )
                        )
                    trust_class = str(surface.get("trust_class", ""))
                    if trust_class not in TRUST_CLASSES:
                        findings.append(Finding("error", "stack-lock-excluded-surface-trust", surface_path, f"Unsupported trust_class '{trust_class}' in excluded surface entry."))
                    if bool(surface.get("release_eligible")) and trust_class != "trusted":
                        findings.append(
                            Finding(
                                "error",
                                "stack-lock-excluded-surface-release",
                                surface_path,
                                "Only trusted surfaces may be marked release_eligible.",
                            )
                        )

    for repo_path in discover_unregistered_git_roots(root, config, stack_file):
        findings.append(
            Finding(
                "warning",
                "unregistered-git-root",
                relative_to_root(root, repo_path),
                "Git repo root is present under repos/ but not tracked by repo_registry or excluded_surfaces.",
            )
        )

    findings.extend(validate_gitdir_hygiene(root))

    excluded_surface_roots = collect_excluded_surface_roots(stack_file, config)
    root_abs_patterns = [
        ("warning", "atlas-root-path", re.compile(re.escape(str(root)))),
        ("warning", "atlas-root-path-alt", re.compile(re.escape(normalize_slashes(str(root))))),
    ]
    for file_path in iter_scan_files(collect_text_scan_roots(root, config, stack_file)):
        if is_import_evidence_file(root, file_path):
            continue
        try:
            text = file_path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        for line_number, line in enumerate(text.splitlines(), start=1):
            for severity, category, pattern in ABSOLUTE_PATTERNS + root_abs_patterns:
                if pattern.search(line):
                    findings.append(
                        build_absolute_path_finding(
                            root=root,
                            file_path=file_path,
                            severity=severity,
                            category=category,
                            line_number=line_number,
                            line_preview=line.strip(),
                            excluded_surface_roots=excluded_surface_roots,
                        )
                    )
                    break

    return findings


def summarize_findings(findings: list[Finding]) -> dict[str, int]:
    counts = Counter(finding.severity for finding in findings)
    return {key: counts.get(key, 0) for key in ["critical", "error", "warning", "info"]} | {"total": len(findings)}


def summarize_excluded_surface_findings(findings: list[dict[str, Any]]) -> list[dict[str, Any]]:
    buckets: dict[str, dict[str, Any]] = {}
    for finding in findings:
        details = finding.get("details")
        if not isinstance(details, dict):
            continue
        excluded_surface = details.get("excluded_surface")
        if not isinstance(excluded_surface, dict):
            continue

        surface_id = str(excluded_surface.get("surface_id", "")).strip()
        if not surface_id:
            continue

        bucket = buckets.setdefault(
            surface_id,
            {
                "surface_id": surface_id,
                "path": str(excluded_surface.get("path", "")),
                "trust_class": str(excluded_surface.get("trust_class", "")),
                "release_eligible": bool(excluded_surface.get("release_eligible")),
                "reason": excluded_surface.get("reason"),
                "label": str(excluded_surface.get("label", EXCLUDED_SURFACE_LABEL)),
                "finding_count": 0,
                "blocking_count": 0,
                "severity_counts": Counter(),
                "category_counts": Counter(),
                "paths": {},
            },
        )
        bucket["finding_count"] += 1
        if finding.get("severity") in {"critical", "error"}:
            bucket["blocking_count"] += 1
        category = str(finding.get("category", ""))
        path = str(finding.get("path", ""))
        bucket["severity_counts"][str(finding.get("severity", "unknown"))] += 1
        bucket["category_counts"][category] += 1
        path_bucket = bucket["paths"].setdefault(
            path,
            {
                "path": path,
                "count": 0,
                "category_counts": Counter(),
            },
        )
        path_bucket["count"] += 1
        path_bucket["category_counts"][category] += 1

    summarized: list[dict[str, Any]] = []
    for surface_id in sorted(buckets):
        bucket = buckets[surface_id]
        path_entries = list(bucket["paths"].values())
        path_entries.sort(key=lambda item: (-int(item["count"]), str(item["path"])))
        summarized.append(
            {
                "surface_id": bucket["surface_id"],
                "path": bucket["path"],
                "trust_class": bucket["trust_class"],
                "release_eligible": bucket["release_eligible"],
                "reason": bucket["reason"],
                "label": bucket["label"],
                "finding_count": bucket["finding_count"],
                "blocking_count": bucket["blocking_count"],
                "severity_counts": dict(sorted(bucket["severity_counts"].items())),
                "category_counts": dict(sorted(bucket["category_counts"].items())),
                "paths": [
                    {
                        "path": item["path"],
                        "count": item["count"],
                        "category_counts": dict(sorted(item["category_counts"].items())),
                    }
                    for item in path_entries
                ],
            }
        )
    return summarized


def write_markdown_report(report: dict[str, Any], output_path: Path) -> None:
    summary = report["summary"]
    findings = report["findings"]
    ratchet = report.get("ratchet")
    debt_classes = report.get("debt_classes") if isinstance(report.get("debt_classes"), list) else []
    excluded_surface_summary = (
        report.get("excluded_surface_summary")
        if isinstance(report.get("excluded_surface_summary"), list)
        else []
    )
    remediation_buckets = (
        report.get("remediation_buckets")
        if isinstance(report.get("remediation_buckets"), list)
        else []
    )
    lines = [
        "# ATLAS Stack Validation Report",
        "",
        f"- Generated: `{report['generated_at']}`",
        f"- Stack file: `{report['stack_file']}`",
        f"- Stack lock file: `{report.get('stack_lock_file', 'stack.lock.yaml')}`",
        f"- Stack root: `{report['stack_root']}`",
        "",
        "## Summary",
        "",
        f"- Critical: {summary['critical']}",
        f"- Error: {summary['error']}",
        f"- Warning: {summary['warning']}",
        f"- Info: {summary['info']}",
        f"- Total: {summary['total']}",
        "",
    ]
    if debt_classes:
        lines += [
            "## Debt Classes",
            "",
        ]
        for item in debt_classes:
            if not isinstance(item, dict):
                continue
            lines.append(
                f"- `{item.get('class_id')}`: total={item.get('total', 0)}, blocking={item.get('blocking_total', 0)}, categories={len(item.get('category_counts') or {})}"
            )
        lines.append("")
    if excluded_surface_summary:
        lines += [
            "## Excluded Surface Debt",
            "",
        ]
        for item in excluded_surface_summary:
            if not isinstance(item, dict):
                continue
            lines.append(
                f"- `{item.get('surface_id')}` ({item.get('label')}): path={item.get('path')}, findings={item.get('finding_count', 0)}, blocking={item.get('blocking_count', 0)}, categories={json.dumps(item.get('category_counts', {}), sort_keys=True)}"
            )
            reason = item.get("reason")
            if reason:
                lines.append(f"  - reason: {reason}")
            for path_item in (item.get("paths") or [])[:3]:
                if not isinstance(path_item, dict):
                    continue
                lines.append(
                    f"  - `{path_item.get('path')}`: count={path_item.get('count', 0)}, categories={json.dumps(path_item.get('category_counts', {}), sort_keys=True)}"
                )
        lines.append("")
    if remediation_buckets:
        lines += [
            "## Remediation Buckets",
            "",
        ]
        for item in remediation_buckets:
            if not isinstance(item, dict):
                continue
            lines.append(
                f"- `{item.get('bucket_id')}`: treatment={item.get('treatment')}, findings={item.get('finding_count', 0)}, residue={item.get('residue_count', 0)}, blocking={item.get('blocking_count', 0)}"
            )
            examples = item.get("examples") if isinstance(item.get("examples"), list) else []
            for example in examples[:3]:
                lines.append(f"  - `{example}`")
        lines.append("")
    if isinstance(ratchet, dict):
        lines += [
            "## Ratchet",
            "",
            f"- Enabled: `{ratchet.get('enabled', False)}`",
            f"- Baseline: `{ratchet.get('baseline_path', 'none')}`",
            f"- Baseline findings: {ratchet.get('baseline_finding_count', 0)}",
            f"- Current blocking findings: {ratchet.get('current_blocking_count', 0)}",
            f"- New blocking findings: {ratchet.get('new_blocking_count', 0)}",
            f"- Inherited blocking classes: `{json.dumps(ratchet.get('inherited_blocking_by_class', {}), sort_keys=True)}`",
            f"- New blocking classes: `{json.dumps(ratchet.get('new_blocking_by_class', {}), sort_keys=True)}`",
            "",
        ]
        new_blocking = ratchet.get("new_blocking_findings") or []
        if new_blocking:
            lines += ["### New Blocking Findings", ""]
            for finding in new_blocking:
                detail = finding.get("details") or {}
                suffix = f" (line {detail['line_number']})" if detail.get("line_number") else ""
                lines.append(f"- `{finding['path']}`: {finding['message']}{suffix}")
            lines.append("")
    for severity in ["critical", "error", "warning", "info"]:
        scoped = [finding for finding in findings if finding["severity"] == severity]
        if not scoped:
            continue
        lines += [f"## {severity.title()} Findings", ""]
        for finding in scoped:
            detail = finding.get("details") or {}
            suffix = f" (line {detail['line_number']})" if detail.get("line_number") else ""
            lines.append(f"- `{finding['path']}`: {finding['message']}{suffix}")
        lines.append("")
    output_path.write_text("\n".join(lines).strip() + "\n", encoding="utf-8")


def default_output_dir(stack_file: Path) -> Path:
    return stack_file.parent.resolve() / "runtime" / "receipts" / "validation"


def default_baseline_path(stack_file: Path) -> Path:
    return stack_file.parent.resolve() / "ops" / "validation" / "stack-validation.baseline.json"


def baseline_relpath(stack_file: Path, path: Path) -> str:
    root = stack_file.parent.resolve()
    resolved = path.resolve()
    if resolved.is_relative_to(root):
        return normalize_slashes(str(resolved.relative_to(root)))
    return normalize_slashes(str(resolved))


def normalized_baseline_details(details: dict[str, Any] | None) -> dict[str, Any] | None:
    if not isinstance(details, dict):
        return None
    normalized: dict[str, Any] = {}
    if isinstance(details.get("line_number"), int):
        normalized["line_number"] = details["line_number"]
    return normalized or None


def normalize_finding_for_baseline(finding: Finding | dict[str, Any]) -> dict[str, Any]:
    if isinstance(finding, Finding):
        entry = {
            "severity": finding.severity,
            "category": finding.category,
            "path": finding.path,
            "message": finding.message,
        }
        details = normalized_baseline_details(finding.details)
    else:
        entry = {
            "severity": str(finding["severity"]),
            "category": str(finding["category"]),
            "path": str(finding["path"]),
            "message": str(finding["message"]),
        }
        details = normalized_baseline_details(finding.get("details"))
    if details is not None:
        entry["details"] = details
    return entry


def finding_baseline_key(finding: dict[str, Any]) -> str:
    return json.dumps(normalize_finding_for_baseline(finding), sort_keys=True, separators=(",", ":"))


def build_baseline(report: dict[str, Any], *, stack_file: Path) -> dict[str, Any]:
    findings = [normalize_finding_for_baseline(item) for item in report["findings"]]
    findings.sort(key=lambda item: json.dumps(item, sort_keys=True, separators=(",", ":")))
    return {
        "baseline_version": BASELINE_VERSION,
        "generated_at": report["generated_at"],
        "stack_file": baseline_relpath(stack_file, stack_file),
        "findings": findings,
    }


def load_baseline(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("Baseline file must contain a JSON object.")
    if payload.get("baseline_version") != BASELINE_VERSION:
        raise ValueError(f"Baseline version must be '{BASELINE_VERSION}'.")
    findings = payload.get("findings")
    if not isinstance(findings, list):
        raise ValueError("Baseline file must contain a findings array.")
    return payload


def ratchet_report(current_findings: list[dict[str, Any]], baseline: dict[str, Any], *, baseline_path: Path, stack_file: Path) -> dict[str, Any]:
    baseline_entries = [item for item in baseline.get("findings", []) if isinstance(item, dict)]
    baseline_keys = {finding_baseline_key(item) for item in baseline_entries}
    blocking = [
        item for item in current_findings
        if item["severity"] in {"critical", "error"}
    ]
    new_blocking = [
        item for item in blocking
        if finding_baseline_key(item) not in baseline_keys
    ]
    inherited_blocking = [
        item for item in blocking
        if finding_baseline_key(item) in baseline_keys
    ]
    return {
        "enabled": True,
        "baseline_path": baseline_relpath(stack_file, baseline_path),
        "baseline_version": baseline.get("baseline_version"),
        "baseline_finding_count": len(baseline_entries),
        "current_blocking_count": len(blocking),
        "new_blocking_count": len(new_blocking),
        "current_blocking_by_class": debt_class_counts(blocking),
        "inherited_blocking_by_class": debt_class_counts(inherited_blocking),
        "new_blocking_by_class": debt_class_counts(new_blocking),
        "new_blocking_findings": [normalize_finding_for_baseline(item) for item in new_blocking],
    }


def emit_validation_observations(report: dict[str, Any], *, json_path: Path, root: Path) -> None:
    summary = report.get("summary", {}) if isinstance(report.get("summary"), dict) else {}
    findings = report.get("findings", []) if isinstance(report.get("findings"), list) else []
    source_ref = relative_to_root(root, json_path)
    generated_at = str(report.get("generated_at")) if report.get("generated_at") is not None else None
    emit_observation(
        build_observation(
            observation_type="validation.stack",
            source_kind="validation_receipt",
            status="blocking" if (summary.get("critical", 0) or summary.get("error", 0)) else "clean",
            observed_at=generated_at,
            source_ref=source_ref,
            scope_ref="stack",
            details={
                "critical": summary.get("critical"),
                "error": summary.get("error"),
                "warning": summary.get("warning"),
                "total": summary.get("total"),
            },
        ),
        owner="stack-validation",
        root=root,
    )
    if any(isinstance(item, dict) and item.get("category") == "stack-lock-drift" for item in findings):
        emit_observation(
            build_observation(
                observation_type="lockfile.drift",
                source_kind="validation_receipt",
                status="detected",
                observed_at=generated_at,
                source_ref=source_ref,
                scope_ref="stack",
                details={"category": "stack-lock-drift"},
            ),
            owner="stack-validation",
            root=root,
        )
    ratchet = report.get("ratchet") if isinstance(report.get("ratchet"), dict) else {}
    if int(ratchet.get("new_blocking_count", 0) or 0) > 0:
        emit_observation(
            build_observation(
                observation_type="validation.ratchet",
                source_kind="validation_receipt",
                status="regression",
                observed_at=generated_at,
                source_ref=source_ref,
                scope_ref="stack",
                details={
                    "new_blocking_count": ratchet.get("new_blocking_count"),
                    "baseline_path": ratchet.get("baseline_path"),
                },
            ),
            owner="stack-validation",
            root=root,
        )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate the ATLAS stack against stack.yaml.")
    parser.add_argument("--stack-file", default=str(repo_root() / "stack.yaml"))
    parser.add_argument("--lock-file")
    parser.add_argument("--output-dir")
    parser.add_argument("--json-name", default="stack-validation.latest.json")
    parser.add_argument("--markdown-name", default="stack-validation.latest.md")
    parser.add_argument("--baseline-path")
    parser.add_argument("--write-baseline", action="store_true")
    parser.add_argument("--ratchet", action="store_true")
    parser.add_argument("--allow-missing-locked-repos", action="store_true")
    parser.add_argument("--require-present-repo-id", action="append", default=[])
    args = parser.parse_args(argv)

    stack_file = Path(args.stack_file).resolve()
    lock_file = Path(args.lock_file).resolve() if args.lock_file else None
    default_lock_file = lock_file or (stack_file.parent.resolve() / "stack.lock.yaml")
    output_dir = Path(args.output_dir).resolve() if args.output_dir else default_output_dir(stack_file)
    baseline_path = Path(args.baseline_path).resolve() if args.baseline_path else default_baseline_path(stack_file)
    should_exit_success = False
    try:
        config = load_stack_config(stack_file)
        backfill_legacy_runtime_artifacts(root=stack_file.parent.resolve())
        write_world_model_state(
            descriptor_root=stack_file.parent.resolve() / "runtime" / "cortex" / "artifacts",
            root=stack_file.parent.resolve(),
        )
        register_artifact_descriptors(
            [world_model_state_root(stack_file.parent.resolve())],
            output_dir=stack_file.parent.resolve() / "runtime" / "cortex" / "artifacts",
            root=stack_file.parent.resolve(),
        )
        resolved_lock_file = lock_file or lockfile_output_path(stack_file, config)
        report = {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "stack_file": normalize_slashes(str(stack_file)),
            "stack_root": normalize_slashes(str(stack_file.parent.resolve())),
            "stack_lock_file": relative_to_root(stack_file.parent.resolve(), resolved_lock_file),
            "summary": summarize_findings(
                findings := build_findings(
                    stack_file,
                    config,
                    lock_file_override=lock_file,
                    allow_missing_locked_repos=bool(args.allow_missing_locked_repos),
                    required_present_repo_ids={
                        str(repo_id).strip()
                        for repo_id in args.require_present_repo_id
                        if str(repo_id).strip()
                    },
                )
            ),
            "repo_ids": sorted(config.get("repo_registry", {}).keys()),
            "findings": [asdict(item) for item in findings],
        }
        report["debt_classes"] = summarize_debt_classes(report["findings"])
        report["excluded_surface_summary"] = summarize_excluded_surface_findings(report["findings"])
        report["remediation_buckets"] = summarize_remediation_buckets(
            report["findings"],
            root=stack_file.parent.resolve(),
        )
    except Exception as exc:
        output_dir.mkdir(parents=True, exist_ok=True)
        report = {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "stack_file": normalize_slashes(str(stack_file)),
            "stack_root": normalize_slashes(str(stack_file.parent.resolve())),
            "stack_lock_file": relative_to_root(stack_file.parent.resolve(), default_lock_file),
            "summary": {"critical": 1, "error": 0, "warning": 0, "info": 0, "total": 1},
            "repo_ids": [],
            "findings": [asdict(Finding("critical", "validator-crash", normalize_slashes(str(stack_file)), f"Validator failed before completion: {exc}"))],
        }
        report["debt_classes"] = summarize_debt_classes(report["findings"])
        report["excluded_surface_summary"] = summarize_excluded_surface_findings(report["findings"])
        report["remediation_buckets"] = summarize_remediation_buckets(
            report["findings"],
            root=stack_file.parent.resolve(),
        )
    if args.write_baseline:
        baseline_path.parent.mkdir(parents=True, exist_ok=True)
        baseline = build_baseline(report, stack_file=stack_file)
        baseline_path.write_text(json.dumps(baseline, indent=2) + "\n", encoding="utf-8")
        report["baseline"] = {
            "path": baseline_relpath(stack_file, baseline_path),
            "baseline_version": BASELINE_VERSION,
            "finding_count": len(baseline["findings"]),
        }
        should_exit_success = True
    if args.ratchet:
        baseline_error: str | None = None
        baseline: dict[str, Any] | None = None
        if baseline_path.exists():
            try:
                baseline = load_baseline(baseline_path)
            except Exception as exc:
                baseline_error = str(exc)
        else:
            baseline_error = "Ratchet mode requires a committed baseline file."
        if baseline is not None:
            report["ratchet"] = ratchet_report(
                report["findings"],
                baseline,
                baseline_path=baseline_path,
                stack_file=stack_file,
            )
            should_exit_success = report["ratchet"]["new_blocking_count"] == 0
        else:
            report["ratchet"] = {
                "enabled": True,
                "baseline_path": baseline_relpath(stack_file, baseline_path),
                "baseline_version": None,
                "baseline_finding_count": 0,
                "current_blocking_count": sum(
                    1 for item in report["findings"] if item["severity"] in {"critical", "error"}
                ),
                "new_blocking_count": 1,
                "new_blocking_findings": [
                    {
                        "severity": "critical",
                        "category": "baseline-missing",
                        "path": baseline_relpath(stack_file, baseline_path),
                        "message": baseline_error or "Ratchet mode requires a committed baseline file.",
                    }
                ],
            }
            should_exit_success = False
    output_dir.mkdir(parents=True, exist_ok=True)
    json_path = output_dir / args.json_name
    markdown_path = output_dir / args.markdown_name
    json_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    write_markdown_report(report, markdown_path)
    report["warning_budget"] = build_warning_budget_summary(
        report,
        stack_file=stack_file,
        output_dir=output_dir,
    )
    json_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    emit_validation_observations(report, json_path=json_path, root=stack_file.parent.resolve())
    summary = report["summary"]
    print(f"Stack validation complete: critical={summary['critical']} error={summary['error']} warning={summary['warning']} info={summary['info']}")
    print(f"Markdown report: {normalize_slashes(str(markdown_path))}")
    print(f"JSON report: {normalize_slashes(str(json_path))}")
    if args.ratchet or args.write_baseline:
        return 0 if should_exit_success else 2
    return 2 if summary["critical"] > 0 else 0


if __name__ == "__main__":
    raise SystemExit(main())
