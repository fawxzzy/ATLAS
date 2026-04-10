from __future__ import annotations

import argparse
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from ops._atlas import atlas_relative, discover_git_root, load_repo_registry, load_stack_config, normalize_slashes

ROOT_REPO_ID = "stack"
DEFAULT_COMMIT_ELIGIBLE_STATUSES = {"active", "incubating", "demo"}
ROOT_SCOPE_PATHS = [
    "AGENTS.md",
    "README-STACK.md",
    "stack.yaml",
    ".gitignore",
    "docs",
    "ops",
    "data",
    "packages",
]


@dataclass(frozen=True)
class RepoSnapshot:
    repo_id: str
    role: str
    status: str
    root: Path
    atlas_path: str
    git_root: Path | None
    git_ready: bool
    dirty_lines: list[str]
    dirty: bool
    status_error: str | None
    selected: bool
    selected_reason: str
    commit_scope: str


@dataclass(frozen=True)
class RepoAction:
    snapshot: RepoSnapshot
    stage_paths: list[str]
    commit_message: list[str]


def run_git(arguments: list[str], cwd: Path) -> subprocess.CompletedProcess[str]:
    try:
        return subprocess.run(
            arguments,
            cwd=str(cwd),
            check=False,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
    except FileNotFoundError as exc:
        raise RuntimeError("git is not available on PATH.") from exc


def read_status_lines(repo_root: Path, pathspecs: list[str] | None = None) -> list[str]:
    args = ["git", "-C", str(repo_root), "status", "--short", "--untracked-files=normal"]
    if pathspecs:
        args.extend(["--", *pathspecs])
    completed = run_git(args, ROOT)
    if completed.returncode != 0:
        raise RuntimeError((completed.stderr or completed.stdout or "git status failed.").strip())
    return [line.rstrip() for line in completed.stdout.splitlines() if line.strip()]


def normalize_repo_id(value: str) -> str:
    normalized = normalize_slashes(value).strip().strip("/")
    if normalized in {"", ".", "root"}:
        return ROOT_REPO_ID
    return normalized


def resolve_requested_repo_ids(values: list[str]) -> list[str]:
    requested: list[str] = []
    for value in values:
        for chunk in value.split(","):
            normalized = normalize_repo_id(chunk)
            if normalized:
                requested.append(normalized)
    return requested


def summarize_status_lines(lines: list[str]) -> dict[str, int]:
    counts = {
        "dirty": 1 if lines else 0,
        "untracked": 0,
        "tracked": 0,
    }
    for line in lines:
        if line.startswith("??"):
            counts["untracked"] += 1
        else:
            counts["tracked"] += 1
    return counts


def resolve_commit_message(repo_id: str, snapshot: RepoSnapshot, message: str, prefix: str | None, suffix: str | None) -> list[str]:
    subject = (message or "ATLAS stack sync").strip()
    body = [
        f"Repo: {repo_id}",
        f"Root: {snapshot.atlas_path}",
        f"Status: {snapshot.status}",
        f"Dirty paths: {len(snapshot.dirty_lines)}",
        "Source: ops/codex/commit_stack_repos.ps1",
    ]

    parts: list[str] = []
    if prefix:
        parts.append(prefix.strip())
    parts.append(subject)
    parts.append("\n".join(body))
    if suffix:
        parts.append(suffix.strip())
    return [part for part in parts if part]


def build_snapshots(
    registry: dict[str, Any],
    requested_repo_ids: list[str],
    include_root: bool,
) -> list[RepoSnapshot]:
    snapshots: list[RepoSnapshot] = []
    requested = set(requested_repo_ids)
    default_commit_ids = {
        repo_id
        for repo_id, entry in registry.items()
        if repo_id != ROOT_REPO_ID and str(entry.status) in DEFAULT_COMMIT_ELIGIBLE_STATUSES
    }

    for repo_id, entry in registry.items():
        repo_root = entry.root.resolve()
        git_root = discover_git_root(repo_root)
        git_ready = git_root is not None and git_root == repo_root
        is_root = repo_id == ROOT_REPO_ID
        commit_scope = "root" if is_root else "child"
        selected = repo_id in requested if requested else (include_root if is_root else repo_id in default_commit_ids)
        selected_reason = "targeted explicitly" if repo_id in requested else (
            "included explicitly" if is_root and include_root else
            "selected by default" if selected else "skipped by default policy"
        )

        status_error: str | None = None
        if not git_ready:
            dirty_lines = []
        else:
            try:
                dirty_lines = read_status_lines(
                    repo_root,
                    ROOT_SCOPE_PATHS if is_root else None,
                )
            except RuntimeError as exc:
                status_error = str(exc)
                dirty_lines = []

        snapshots.append(
            RepoSnapshot(
                repo_id=repo_id,
                role=str(entry.role),
                status=str(entry.status),
                root=repo_root,
                atlas_path=atlas_relative(repo_root, root=ROOT),
                git_root=git_root,
                git_ready=git_ready,
                dirty_lines=dirty_lines,
                dirty=bool(dirty_lines),
                status_error=status_error,
                selected=selected,
                selected_reason=selected_reason,
                commit_scope=commit_scope,
            )
        )

    return snapshots


def print_summary(snapshots: list[RepoSnapshot], dry_run: bool, selected_repo_ids: list[str], commit_message: str, prefix: str | None, suffix: str | None) -> None:
    dirty_snapshots = [snapshot for snapshot in snapshots if snapshot.dirty]
    selected_dirty = [snapshot for snapshot in snapshots if snapshot.dirty and snapshot.selected and snapshot.git_ready]
    root_dirty = next((snapshot for snapshot in snapshots if snapshot.repo_id == ROOT_REPO_ID and snapshot.dirty), None)

    print("ATLAS multi-repo commit helper")
    print(f"Dry run           : {'yes' if dry_run else 'no'}")
    print(f"Target repos      : {', '.join(selected_repo_ids) if selected_repo_ids else '<default policy>'}")
    print(f"Dirty repos       : {len(dirty_snapshots)}")
    print(f"Selected commits  : {len(selected_dirty)}")
    print(f"Root commit scope : {'dirty' if root_dirty else 'clean'}")
    print("")

    for snapshot in snapshots:
        status = "dirty" if snapshot.dirty else "clean"
        selection = snapshot.selected_reason
        readiness = "git-ready" if snapshot.git_ready else "not-a-git-root"
        counts = summarize_status_lines(snapshot.dirty_lines)
        print(f"- {snapshot.repo_id} [{snapshot.status}] {status} ({snapshot.commit_scope}, {readiness})")
        print(f"  root: {snapshot.atlas_path}")
        print(f"  selection: {selection}")
        if snapshot.status_error:
            print(f"  status: {snapshot.status_error}")
        if snapshot.dirty_lines:
            print(f"  changes: {counts['tracked']} tracked, {counts['untracked']} untracked")
            for line in snapshot.dirty_lines:
                print(f"    {line}")
        else:
            print("  changes: none")
    print("")
    if prefix:
        print("Commit prefix   :")
        print(prefix)
    print("Commit message  :")
    print(commit_message)
    if suffix:
        print("Commit suffix   :")
        print(suffix)


def create_actions(
    snapshots: list[RepoSnapshot],
    commit_message: str,
    prefix: str | None,
    suffix: str | None,
) -> list[RepoAction]:
    actions: list[RepoAction] = []
    for snapshot in snapshots:
        if not snapshot.selected or not snapshot.git_ready or snapshot.status_error or not snapshot.dirty:
            continue
        if snapshot.repo_id == ROOT_REPO_ID:
            stage_paths = ROOT_SCOPE_PATHS
        else:
            stage_paths = ["."]
        actions.append(
            RepoAction(
                snapshot=snapshot,
                stage_paths=stage_paths,
                commit_message=resolve_commit_message(snapshot.repo_id, snapshot, commit_message, prefix, suffix),
            )
        )

    actions.sort(key=lambda action: (action.snapshot.repo_id == ROOT_REPO_ID, action.snapshot.repo_id))
    return actions


def stage_repo(action: RepoAction) -> subprocess.CompletedProcess[str]:
    args = ["git", "-C", str(action.snapshot.root), "add", "-A", "--", *action.stage_paths]
    return run_git(args, ROOT)


def commit_repo(action: RepoAction) -> subprocess.CompletedProcess[str]:
    args = ["git", "-C", str(action.snapshot.root), "commit"]
    for part in action.commit_message:
        args.extend(["-m", part])
    return run_git(args, ROOT)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Commit dirty ATLAS stack repos independently.")
    parser.add_argument("--repo-id", action="append", default=[], help="Target a repo id from stack.yaml; may be repeated or comma-separated.")
    parser.add_argument("--dry-run", action="store_true", help="Print the plan without mutating git.")
    parser.add_argument("--include-root", action="store_true", help="Also evaluate the ATLAS root control repo.")
    parser.add_argument("--commit-message", default="ATLAS stack sync", help="Base commit subject for each repo.")
    parser.add_argument("--commit-message-prefix", default="", help="Text to prepend to each commit message.")
    parser.add_argument("--commit-message-suffix", default="", help="Text to append to each commit message.")
    args = parser.parse_args(argv)

    root_config = load_stack_config(ROOT / "stack.yaml")
    registry = load_repo_registry(root_config, root=ROOT)
    requested_repo_ids = resolve_requested_repo_ids(args.repo_id)
    unknown_requested = [repo_id for repo_id in requested_repo_ids if repo_id not in registry]
    if unknown_requested:
        print(
            "Unknown repo id(s): "
            + ", ".join(sorted(set(unknown_requested)))
            + ". Known ids: "
            + ", ".join(registry.keys())
        )
        return 2

    snapshots = build_snapshots(registry, requested_repo_ids, args.include_root)
    actions = create_actions(
        snapshots,
        args.commit_message,
        args.commit_message_prefix or None,
        args.commit_message_suffix or None,
    )

    print_summary(
        snapshots,
        args.dry_run,
        requested_repo_ids,
        args.commit_message,
        args.commit_message_prefix or None,
        args.commit_message_suffix or None,
    )

    if args.dry_run:
        return 0

    if not actions:
        print("Nothing selected for commit.")
        return 0

    failures: list[str] = []
    for action in actions:
        print(f"Processing {action.snapshot.repo_id} ...")
        stage_result = stage_repo(action)
        if stage_result.returncode != 0:
            failures.append(f"{action.snapshot.repo_id}: git add failed: {(stage_result.stderr or stage_result.stdout or '').strip()}")
            print(f"  failed to stage {action.snapshot.repo_id}")
            continue

        commit_result = commit_repo(action)
        output = (commit_result.stdout or commit_result.stderr or "").strip()
        if commit_result.returncode == 0:
            print(f"  committed {action.snapshot.repo_id}")
            if output:
                print(output)
            continue

        if "nothing to commit" in output.lower():
            print(f"  no changes to commit for {action.snapshot.repo_id}")
            continue

        failures.append(f"{action.snapshot.repo_id}: git commit failed: {output}")
        print(f"  failed to commit {action.snapshot.repo_id}")

    if failures:
        print("")
        print("Failures:")
        for failure in failures:
            print(f"- {failure}")
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
