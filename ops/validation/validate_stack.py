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
ABSOLUTE_PATTERNS = [
    ("critical", "windows-user-path", re.compile(r"[A-Za-z]:\\Users\\")),
    ("critical", "windows-user-path-alt", re.compile(r"[A-Za-z]:/Users/")),
    ("critical", "unix-home-path", re.compile(r"(/Users/|/home/)")),
]
MUTABLE_DIR_CANDIDATES = [
    ".next", ".playbook", ".lifeline", ".venv", ".vercel", "node_modules", "dist",
    "coverage", "playwright-report", "test-results", "DerivedDataCache",
    "Intermediate", "Saved", "Binaries",
]
ROOT_LOG_PATTERNS = ["*.log", "*.err.log", "*.out.log", "*.tmp", "*.db", "*.sqlite", "*.sqlite3"]
ROOT_CAPTURE_PATTERNS = ["*screenshot*.png", "artifacts*.png", "*check*.png", "*review*.png"]
BASELINE_VERSION = "atlas.stack.validation.baseline.v1"
VERTA_SECRET_PATTERNS = [
    ("verta-live-secret", re.compile(r"gh[pousr]_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{20,}|AKIA[0-9A-Z]{16}|sk-[A-Za-z0-9]{20,}|xox[baprs]-[A-Za-z0-9-]{10,}|-----BEGIN [A-Z ]*PRIVATE KEY-----|Bearer\s+[A-Za-z0-9._-]{16,}")),
]
VERTA_SURFACE_TEXT_EXTENSIONS = {".bat", ".cmd", ".conf", ".cfg", ".ini", ".json", ".md", ".ps1", ".py", ".sh", ".txt", ".yaml", ".yml"}

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from ops.stack.generate_lockfile import (
    STACK_LOCK_SCHEMA_VERSION,
    TRUST_CLASSES,
    build_lock_payload,
    default_lockfile_path,
    git_output,
    load_lockfile,
    repo_is_git_root,
)
from ops.stack.audit_gitdir_hygiene import build_report as build_gitdir_hygiene_report, default_target_paths as default_gitdir_hygiene_targets


@dataclass
class Finding:
    severity: str
    category: str
    path: str
    message: str
    details: dict[str, Any] | None = None


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
    for candidate in ["README-STACK.md", "AGENTS.md", "stack.yaml", "docs", "ops"]:
        candidate_path = root / candidate
        if candidate_path.exists():
            roots.append(candidate_path)
    for repo in config.get("repo_registry", {}).values():
        if isinstance(repo, dict) and isinstance(repo.get("path"), str) and repo.get("status") in {"active", "incubating", "unmanaged"}:
            repo_path = resolve_path(stack_file, repo["path"])
            if repo_path.exists():
                roots.append(repo_path)
    seen: set[Path] = set()
    result: list[Path] = []
    for item in roots:
        if item not in seen:
            seen.add(item)
            result.append(item)
    return result


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


def build_findings(stack_file: Path, config: dict[str, Any], *, lock_file_override: Path | None = None) -> list[Finding]:
    root = stack_file.parent.resolve()
    findings: list[Finding] = []
    findings.extend(validate_subsystem_registry(stack_file, config))
    findings.extend(validate_verta_trust_gate(stack_file, config))

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
            findings.append(Finding("warning", "repo-local-secret-material", normalize_slashes(str(env_candidate.relative_to(root))), "Repo-local environment file detected; secrets should not be part of default exports.", {"repo_id": repo_id}))
        for pattern in ROOT_LOG_PATTERNS:
            for file_path in repo_path.glob(pattern):
                if file_path.is_file():
                    findings.append(Finding("warning", "mutable-artifact-in-repo-root", normalize_slashes(str(file_path.relative_to(root))), "Mutable log, temp, or database artifact detected in repo root.", {"repo_id": repo_id, "pattern": pattern}))
        for pattern in ROOT_CAPTURE_PATTERNS:
            for file_path in repo_path.glob(pattern):
                if file_path.is_file():
                    findings.append(Finding("warning", "capture-artifact-in-repo-root", normalize_slashes(str(file_path.relative_to(root))), "Likely review or capture artifact detected in repo root.", {"repo_id": repo_id, "pattern": pattern}))

    lockfile_path = lock_file_override.resolve() if lock_file_override is not None else lockfile_output_path(stack_file, config)
    lockfile_rel = relative_to_root(root, lockfile_path)
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
            try:
                generated_lock = build_lock_payload(config=config, root=root)
            except Exception as exc:
                findings.append(
                    Finding(
                        "error",
                        "stack-lock-build-failed",
                        lockfile_rel,
                        f"Current stack lock payload could not be rebuilt: {exc}",
                    )
                )
                generated_lock = None
            if isinstance(generated_lock, dict) and lockfile != generated_lock:
                findings.append(
                    Finding(
                        "error",
                        "stack-lock-drift",
                        lockfile_rel,
                        "Stack lockfile does not match the current pinned working set.",
                    )
                )

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
                required_component_fields = {
                    "path",
                    "remote",
                    "ref_type",
                    "ref",
                    "commit",
                    "dirty",
                    "trust_class",
                    "release_eligible",
                }
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
                    ref_problem = verify_locked_ref(repo_path, component)
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
                    findings.append(Finding(severity, category, normalize_slashes(str(file_path.relative_to(root))), "Absolute path leak detected in committed text.", {"line_number": line_number, "line_preview": line.strip()[:220]}))
                    break

    return findings


def summarize_findings(findings: list[Finding]) -> dict[str, int]:
    counts = Counter(finding.severity for finding in findings)
    return {key: counts.get(key, 0) for key in ["critical", "error", "warning", "info"]} | {"total": len(findings)}


def write_markdown_report(report: dict[str, Any], output_path: Path) -> None:
    summary = report["summary"]
    findings = report["findings"]
    ratchet = report.get("ratchet")
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
    if isinstance(ratchet, dict):
        lines += [
            "## Ratchet",
            "",
            f"- Enabled: `{ratchet.get('enabled', False)}`",
            f"- Baseline: `{ratchet.get('baseline_path', 'none')}`",
            f"- Baseline findings: {ratchet.get('baseline_finding_count', 0)}",
            f"- Current blocking findings: {ratchet.get('current_blocking_count', 0)}",
            f"- New blocking findings: {ratchet.get('new_blocking_count', 0)}",
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
    return {
        "enabled": True,
        "baseline_path": baseline_relpath(stack_file, baseline_path),
        "baseline_version": baseline.get("baseline_version"),
        "baseline_finding_count": len(baseline_entries),
        "current_blocking_count": len(blocking),
        "new_blocking_count": len(new_blocking),
        "new_blocking_findings": [normalize_finding_for_baseline(item) for item in new_blocking],
    }


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
    args = parser.parse_args(argv)

    stack_file = Path(args.stack_file).resolve()
    lock_file = Path(args.lock_file).resolve() if args.lock_file else None
    default_lock_file = lock_file or (stack_file.parent.resolve() / "stack.lock.yaml")
    output_dir = Path(args.output_dir).resolve() if args.output_dir else default_output_dir(stack_file)
    baseline_path = Path(args.baseline_path).resolve() if args.baseline_path else default_baseline_path(stack_file)
    should_exit_success = False
    try:
        config = load_stack_config(stack_file)
        resolved_lock_file = lock_file or lockfile_output_path(stack_file, config)
        report = {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "stack_file": normalize_slashes(str(stack_file)),
            "stack_root": normalize_slashes(str(stack_file.parent.resolve())),
            "stack_lock_file": relative_to_root(stack_file.parent.resolve(), resolved_lock_file),
            "summary": summarize_findings(findings := build_findings(stack_file, config, lock_file_override=lock_file)),
            "repo_ids": sorted(config.get("repo_registry", {}).keys()),
            "findings": [asdict(item) for item in findings],
        }
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
    summary = report["summary"]
    print(f"Stack validation complete: critical={summary['critical']} error={summary['error']} warning={summary['warning']} info={summary['info']}")
    print(f"Markdown report: {normalize_slashes(str(markdown_path))}")
    print(f"JSON report: {normalize_slashes(str(json_path))}")
    if args.ratchet or args.write_baseline:
        return 0 if should_exit_success else 2
    return 2 if summary["critical"] > 0 else 0


if __name__ == "__main__":
    raise SystemExit(main())
