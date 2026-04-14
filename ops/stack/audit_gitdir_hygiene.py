from __future__ import annotations

import argparse
import json
import subprocess
import sys
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from ops._atlas import atlas_root, normalize_slashes, resolve_atlas_path

DEFAULT_TARGETS = [
    Path("repos/_stack"),
    Path("repos/fawxzzy-lifeline"),
]


@dataclass
class HygieneFinding:
    category: str
    repo_path: str
    message: str
    metadata_path: str | None = None
    target_path: str | None = None
    repairable: bool = True


def git_output(repo_path: Path, *args: str) -> tuple[int, str, str]:
    completed = subprocess.run(
        ["git", "-C", str(repo_path), *args],
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    return completed.returncode, completed.stdout.strip(), completed.stderr.strip()


def git_dir_for_repo(repo_path: Path) -> Path | None:
    code, stdout, _ = git_output(repo_path, "rev-parse", "--git-dir")
    if code != 0 or not stdout:
        git_dir = repo_path / ".git"
        return git_dir.resolve() if git_dir.exists() else None
    candidate = Path(stdout)
    return candidate.resolve() if candidate.is_absolute() else (repo_path / candidate).resolve()


def parse_worktree_list(repo_path: Path) -> list[dict[str, Any]]:
    code, stdout, stderr = git_output(repo_path, "worktree", "list", "--porcelain")
    if code != 0:
        return [{
            "path": normalize_slashes(str(repo_path)),
            "head": None,
            "branch": None,
            "prunable": None,
            "error": stderr or stdout or "git worktree list failed",
        }]

    entries: list[dict[str, Any]] = []
    current: dict[str, Any] | None = None
    for raw_line in stdout.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        key, _, value = line.partition(" ")
        if key == "worktree":
            if current is not None:
                entries.append(current)
            current = {
                "path": value.strip(),
                "head": None,
                "branch": None,
                "prunable": None,
            }
            continue
        if current is None:
            continue
        current[key] = value.strip() if value else True
    if current is not None:
        entries.append(current)
    return entries


def audit_worktree_admin_dirs(repo_path: Path, git_dir: Path) -> list[HygieneFinding]:
    findings: list[HygieneFinding] = []
    worktrees_dir = git_dir / "worktrees"
    if not worktrees_dir.exists():
        return findings

    for admin_dir in sorted(path for path in worktrees_dir.iterdir() if path.is_dir()):
        gitdir_file = admin_dir / "gitdir"
        if not gitdir_file.exists():
            findings.append(
                HygieneFinding(
                    category="missing-worktree-gitdir-file",
                    repo_path=normalize_slashes(str(repo_path)),
                    metadata_path=normalize_slashes(str(gitdir_file)),
                    message="Worktree admin directory is missing its gitdir pointer file.",
                )
            )
            continue

        raw_target = gitdir_file.read_text(encoding="utf-8", errors="replace").strip()
        target_path = Path(raw_target) if Path(raw_target).is_absolute() else (admin_dir / raw_target).resolve()
        target_path_str = normalize_slashes(str(target_path))
        if not target_path.exists():
            findings.append(
                HygieneFinding(
                    category="stale-worktree-gitdir-pointer",
                    repo_path=normalize_slashes(str(repo_path)),
                    metadata_path=normalize_slashes(str(gitdir_file)),
                    target_path=target_path_str,
                    message="Worktree admin metadata points at a missing worktree gitdir path.",
                )
            )

    config_path = git_dir / "config"
    if config_path.exists():
        for index, raw_line in enumerate(config_path.read_text(encoding="utf-8", errors="replace").splitlines(), start=1):
            line = raw_line.strip()
            if not line.lower().startswith("worktree ="):
                continue
            _, _, raw_value = line.partition("=")
            worktree_value = raw_value.strip()
            if not Path(worktree_value).is_absolute():
                continue
            if not Path(worktree_value).exists():
                findings.append(
                    HygieneFinding(
                        category="stale-core-worktree-config",
                        repo_path=normalize_slashes(str(repo_path)),
                        metadata_path=f"{normalize_slashes(str(config_path))}:{index}",
                        target_path=normalize_slashes(worktree_value),
                        message="Local git config contains an absolute worktree path that no longer exists.",
                    )
                )
    return findings


def audit_nested_worktree_gitfiles(repo_path: Path) -> list[HygieneFinding]:
    findings: list[HygieneFinding] = []
    nested_root = repo_path / ".codex" / "worktrees"
    if not nested_root.exists():
        return findings

    for gitfile in sorted(nested_root.glob("*/.git")):
        raw_value = gitfile.read_text(encoding="utf-8", errors="replace").strip()
        if not raw_value.lower().startswith("gitdir:"):
            continue
        _, _, raw_target = raw_value.partition(":")
        target = raw_target.strip()
        target_path = Path(target) if Path(target).is_absolute() else (gitfile.parent / target).resolve()
        if target_path.exists():
            continue
        findings.append(
            HygieneFinding(
                category="stale-nested-worktree-gitfile",
                repo_path=normalize_slashes(str(repo_path)),
                metadata_path=normalize_slashes(str(gitfile)),
                target_path=normalize_slashes(str(target_path)),
                message="Nested .codex worktree gitfile points at a missing gitdir path.",
            )
        )
    return findings


def audit_repo(repo_path: Path) -> dict[str, Any]:
    resolved_repo = repo_path.resolve()
    repo_str = normalize_slashes(str(resolved_repo))
    git_dir = git_dir_for_repo(resolved_repo)
    status_code, status_stdout, status_stderr = git_output(resolved_repo, "status", "--short")
    toplevel_code, toplevel_stdout, toplevel_stderr = git_output(resolved_repo, "rev-parse", "--show-toplevel")
    gitdir_code, gitdir_stdout, gitdir_stderr = git_output(resolved_repo, "rev-parse", "--git-dir")

    findings: list[HygieneFinding] = []
    worktrees = parse_worktree_list(resolved_repo)
    for entry in worktrees:
        if entry.get("error"):
            findings.append(
                HygieneFinding(
                    category="worktree-list-failed",
                    repo_path=repo_str,
                    message=f"git worktree list failed: {entry['error']}",
                    repairable=False,
                )
            )
            continue
        if entry.get("prunable"):
            findings.append(
                HygieneFinding(
                    category="prunable-worktree-entry",
                    repo_path=repo_str,
                    target_path=normalize_slashes(str(entry.get("path", ""))),
                    message="Git reports a prunable linked worktree entry.",
                )
            )

    if git_dir is None:
        findings.append(
            HygieneFinding(
                category="missing-git-dir",
                repo_path=repo_str,
                message="Unable to resolve the local git directory for this repo.",
                repairable=False,
            )
        )
    else:
        findings.extend(audit_worktree_admin_dirs(resolved_repo, git_dir))
    findings.extend(audit_nested_worktree_gitfiles(resolved_repo))

    return {
        "repo_path": repo_str,
        "git_dir": normalize_slashes(str(git_dir)) if git_dir is not None else None,
        "commands": {
            "status": {
                "exit_code": status_code,
                "stdout": status_stdout,
                "stderr": status_stderr,
            },
            "show_toplevel": {
                "exit_code": toplevel_code,
                "stdout": normalize_slashes(toplevel_stdout) if toplevel_stdout else "",
                "stderr": toplevel_stderr,
            },
            "git_dir": {
                "exit_code": gitdir_code,
                "stdout": normalize_slashes(gitdir_stdout) if gitdir_stdout else "",
                "stderr": gitdir_stderr,
            },
        },
        "worktrees": worktrees,
        "findings": [asdict(item) for item in findings],
        "ok": len(findings) == 0 and status_code == 0 and toplevel_code == 0 and gitdir_code == 0,
    }


def default_target_paths(root: Path) -> list[Path]:
    return [resolve_atlas_path(item, root=root) for item in DEFAULT_TARGETS]


def audit_targets(repo_paths: list[Path]) -> list[dict[str, Any]]:
    return [audit_repo(path) for path in repo_paths]


def prune_repo(repo_path: Path) -> dict[str, Any]:
    completed = subprocess.run(
        ["git", "-C", str(repo_path), "worktree", "prune", "--verbose", "--expire", "now"],
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    return {
        "repo_path": normalize_slashes(str(repo_path.resolve())),
        "exit_code": completed.returncode,
        "stdout": completed.stdout.strip(),
        "stderr": completed.stderr.strip(),
    }


def repair_nested_worktree_gitfiles(repo_path: Path) -> list[dict[str, Any]]:
    repairs: list[dict[str, Any]] = []
    nested_root = repo_path / ".codex" / "worktrees"
    if not nested_root.exists():
        return repairs

    for gitfile in sorted(nested_root.glob("*/.git")):
        raw_value = gitfile.read_text(encoding="utf-8", errors="replace").strip()
        if not raw_value.lower().startswith("gitdir:"):
            continue
        _, _, raw_target = raw_value.partition(":")
        target = raw_target.strip()
        target_path = Path(target) if Path(target).is_absolute() else (gitfile.parent / target).resolve()
        if target_path.exists():
            continue
        backup_path = gitfile.with_name(".git.stale")
        if backup_path.exists():
            backup_path.unlink()
        gitfile.rename(backup_path)
        repairs.append(
            {
                "repo_path": normalize_slashes(str(repo_path.resolve())),
                "metadata_path": normalize_slashes(str(gitfile)),
                "backup_path": normalize_slashes(str(backup_path)),
                "target_path": normalize_slashes(str(target_path)),
                "action": "renamed stale nested gitfile to .git.stale",
            }
        )
    return repairs


def build_report(repo_paths: list[Path], *, apply_repairs: bool) -> dict[str, Any]:
    before = audit_targets(repo_paths)
    repairs: list[dict[str, Any]] = []
    if apply_repairs:
        for repo_path, audit in zip(repo_paths, before):
            if audit["findings"]:
                repairs.append(prune_repo(repo_path))
                repairs.extend(repair_nested_worktree_gitfiles(repo_path))
        after = audit_targets(repo_paths)
    else:
        after = before

    finding_count = sum(len(item["findings"]) for item in after)
    prunable_count = sum(
        1 for item in after for finding in item["findings"] if finding["category"] == "prunable-worktree-entry"
    )
    stale_pointer_count = sum(
        1 for item in after for finding in item["findings"] if finding["category"] == "stale-worktree-gitdir-pointer"
    )
    stale_nested_gitfile_count = sum(
        1 for item in after for finding in item["findings"] if finding["category"] == "stale-nested-worktree-gitfile"
    )
    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "apply_repairs": apply_repairs,
        "repo_count": len(repo_paths),
        "summary": {
            "finding_count": finding_count,
            "prunable_worktree_count": prunable_count,
            "stale_pointer_count": stale_pointer_count,
            "stale_nested_gitfile_count": stale_nested_gitfile_count,
            "ok": finding_count == 0 and all(item["ok"] for item in after),
        },
        "repairs": repairs,
        "repos": after,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Audit and optionally repair stale gitdir/worktree metadata for relocated ATLAS child repos."
    )
    parser.add_argument("--repo-path", action="append", dest="repo_paths")
    parser.add_argument("--apply", action="store_true", help="Prune stale linked-worktree metadata after auditing.")
    args = parser.parse_args(argv)

    root = atlas_root()
    repo_paths = (
        [resolve_atlas_path(item, root=root) for item in args.repo_paths]
        if args.repo_paths
        else default_target_paths(root)
    )
    report = build_report(repo_paths, apply_repairs=args.apply)
    print(json.dumps(report, indent=2))
    return 0 if report["summary"]["ok"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
