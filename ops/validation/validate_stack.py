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
    return Path(__file__).resolve().parents[2]


def resolve_path(stack_file: Path, raw_path: str) -> Path:
    path = Path(raw_path)
    return path.resolve() if path.is_absolute() else (stack_file.parent / path).resolve()


def normalize_slashes(path: str) -> str:
    return path.replace("\\", "/")


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


def build_findings(stack_file: Path, config: dict[str, Any]) -> list[Finding]:
    root = stack_file.parent.resolve()
    findings: list[Finding] = []

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
    lines = [
        "# ATLAS Stack Validation Report",
        "",
        f"- Generated: `{report['generated_at']}`",
        f"- Stack file: `{report['stack_file']}`",
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


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate the ATLAS stack against stack.yaml.")
    parser.add_argument("--stack-file", default=str(repo_root() / "stack.yaml"))
    parser.add_argument("--output-dir")
    parser.add_argument("--json-name", default="stack-validation.latest.json")
    parser.add_argument("--markdown-name", default="stack-validation.latest.md")
    args = parser.parse_args(argv)

    stack_file = Path(args.stack_file).resolve()
    output_dir = Path(args.output_dir).resolve() if args.output_dir else default_output_dir(stack_file)
    try:
        config = load_stack_config(stack_file)
        report = {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "stack_file": normalize_slashes(str(stack_file)),
            "stack_root": normalize_slashes(str(stack_file.parent.resolve())),
            "summary": summarize_findings(findings := build_findings(stack_file, config)),
            "repo_ids": sorted(config.get("repo_registry", {}).keys()),
            "findings": [asdict(item) for item in findings],
        }
    except Exception as exc:
        output_dir.mkdir(parents=True, exist_ok=True)
        report = {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "stack_file": normalize_slashes(str(stack_file)),
            "stack_root": normalize_slashes(str(stack_file.parent.resolve())),
            "summary": {"critical": 1, "error": 0, "warning": 0, "info": 0, "total": 1},
            "repo_ids": [],
            "findings": [asdict(Finding("critical", "validator-crash", normalize_slashes(str(stack_file)), f"Validator failed before completion: {exc}"))],
        }
    output_dir.mkdir(parents=True, exist_ok=True)
    json_path = output_dir / args.json_name
    markdown_path = output_dir / args.markdown_name
    json_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    write_markdown_report(report, markdown_path)
    summary = report["summary"]
    print(f"Stack validation complete: critical={summary['critical']} error={summary['error']} warning={summary['warning']} info={summary['info']}")
    print(f"Markdown report: {normalize_slashes(str(markdown_path))}")
    print(f"JSON report: {normalize_slashes(str(json_path))}")
    return 2 if summary["critical"] > 0 else 0


if __name__ == "__main__":
    raise SystemExit(main())
