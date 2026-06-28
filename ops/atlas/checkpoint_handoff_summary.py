from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Any, Callable

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from ops._atlas import atlas_relative, normalize_slashes

CONTRACT_VERSION = "atlas.checkpoint_handoff_summary.v1"

CATEGORY_PREFIXES: tuple[tuple[str, str], ...] = (
    ("receipt_refs", "docs/ops/"),
    ("book_refs", "docs/atlas-book/"),
    ("atlas_helper_refs", "ops/atlas/"),
    ("stack_helper_refs", "repos/_stack/"),
    ("test_refs", "tests/"),
    ("runtime_refs", "runtime/"),
)

CATEGORY_TITLES: dict[str, str] = {
    "receipt_refs": "Receipts",
    "book_refs": "Book Surfaces",
    "atlas_helper_refs": "ATLAS Helpers",
    "stack_helper_refs": "_stack Helpers",
    "test_refs": "Tests",
    "runtime_refs": "Runtime Artifacts",
    "other_refs": "Other Root Files",
}


class CheckpointHandoffSummaryError(RuntimeError):
    pass


def _run_git(root: Path, *args: str) -> str:
    completed = subprocess.run(
        ["git", "-C", str(root), *args],
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    if completed.returncode != 0:
        raise CheckpointHandoffSummaryError(
            f"git {' '.join(args)} failed: {(completed.stderr or completed.stdout).strip() or 'unknown error'}"
        )
    return completed.stdout


def _resolve_commit(root: Path, ref: str, git_runner: Callable[..., str]) -> dict[str, str]:
    sha = git_runner(root, "rev-parse", "--verify", ref).strip()
    if not sha:
        raise CheckpointHandoffSummaryError(f"Could not resolve ref `{ref}`.")
    subject = git_runner(root, "log", "-1", "--format=%s", sha).strip()
    return {
        "ref": ref,
        "sha": sha,
        "short_sha": sha[:8],
        "subject": subject,
    }


def _list_commits(root: Path, since_ref: str, until_ref: str, git_runner: Callable[..., str]) -> list[dict[str, str]]:
    raw = git_runner(root, "log", "--format=%H%x1f%s", f"{since_ref}..{until_ref}")
    commits: list[dict[str, str]] = []
    for line in raw.splitlines():
        if "\x1f" not in line:
            continue
        sha, subject = line.split("\x1f", 1)
        sha = sha.strip()
        subject = subject.strip()
        if not sha:
            continue
        commits.append(
            {
                "sha": sha,
                "short_sha": sha[:8],
                "subject": subject,
            }
        )
    return commits


def _list_changed_files(root: Path, since_ref: str, until_ref: str, git_runner: Callable[..., str]) -> list[str]:
    raw = git_runner(root, "diff", "--name-only", f"{since_ref}..{until_ref}")
    return [normalize_slashes(line.strip()) for line in raw.splitlines() if line.strip()]


def _list_worktree_status(root: Path, git_runner: Callable[..., str]) -> list[str]:
    raw = git_runner(root, "status", "--short")
    return [line.rstrip() for line in raw.splitlines() if line.strip()]


def _categorize_paths(paths: list[str]) -> dict[str, list[str]]:
    categories: dict[str, list[str]] = {key: [] for key in CATEGORY_TITLES}
    for path in paths:
        matched = False
        for key, prefix in CATEGORY_PREFIXES:
            if path.startswith(prefix):
                categories[key].append(path)
                matched = True
                break
        if not matched:
            categories["other_refs"].append(path)
    return categories


def build_summary(
    *,
    root: Path,
    since_ref: str,
    until_ref: str = "HEAD",
    git_runner: Callable[..., str] = _run_git,
) -> dict[str, Any]:
    since_commit = _resolve_commit(root, since_ref, git_runner)
    until_commit = _resolve_commit(root, until_ref, git_runner)
    commits = _list_commits(root, since_commit["sha"], until_commit["sha"], git_runner)
    changed_files = _list_changed_files(root, since_commit["sha"], until_commit["sha"], git_runner)
    worktree_status = _list_worktree_status(root, git_runner)
    categories = _categorize_paths(changed_files)

    return {
        "contract_version": CONTRACT_VERSION,
        "root": atlas_relative(root, root=root),
        "since_commit": since_commit,
        "until_commit": until_commit,
        "commit_count": len(commits),
        "changed_file_count": len(changed_files),
        "worktree_clean": len(worktree_status) == 0,
        "worktree_status": worktree_status,
        "commits": commits,
        "categories": categories,
    }


def render_markdown(summary: dict[str, Any]) -> str:
    lines = [
        "# Checkpoint Handoff Summary",
        "",
        f"- since: `{summary['since_commit']['ref']}` -> `{summary['since_commit']['short_sha']}` {summary['since_commit']['subject']}",
        f"- until: `{summary['until_commit']['ref']}` -> `{summary['until_commit']['short_sha']}` {summary['until_commit']['subject']}",
        f"- commits: `{summary['commit_count']}`",
        f"- changed files: `{summary['changed_file_count']}`",
        f"- worktree: `{'clean' if summary['worktree_clean'] else 'dirty'}`",
        "",
        "## Commits",
        "",
    ]
    commits = summary.get("commits", [])
    if commits:
        for commit in commits:
            lines.append(f"- `{commit['short_sha']}` {commit['subject']}")
    else:
        lines.append("- no commits in range")

    lines.extend(["", "## Changed Surfaces", ""])
    categories = summary.get("categories", {})
    for key in CATEGORY_TITLES:
        refs = categories.get(key) if isinstance(categories, dict) else []
        if not refs:
            continue
        lines.append(f"### {CATEGORY_TITLES[key]}")
        lines.append("")
        for ref in refs:
            lines.append(f"- `{ref}`")
        lines.append("")

    if not any(categories.get(key) for key in CATEGORY_TITLES):
        lines.append("- no changed tracked files in range")
        lines.append("")

    lines.extend(["## Worktree Status", ""])
    if summary.get("worktree_clean"):
        lines.append("- clean")
    else:
        for line in summary.get("worktree_status", []):
            lines.append(f"- `{line}`")
    lines.append("")
    return "\n".join(lines)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Summarize committed ATLAS-root work between two git checkpoints for handoff or ChatGPT recap."
    )
    parser.add_argument("--root", default=str(ROOT), help="ATLAS root path")
    parser.add_argument("--since-ref", required=True, help="Inclusive base git ref or commit")
    parser.add_argument("--until-ref", default="HEAD", help="Ending git ref or commit")
    parser.add_argument("--format", choices=("json", "markdown"), default="markdown")
    parser.add_argument("--output", help="Optional output path")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    root = Path(args.root).resolve()
    summary = build_summary(root=root, since_ref=args.since_ref, until_ref=args.until_ref)
    rendered = json.dumps(summary, indent=2) + "\n" if args.format == "json" else render_markdown(summary)
    if args.output:
        output_path = Path(args.output)
        if not output_path.is_absolute():
            output_path = root / output_path
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(rendered, encoding="utf-8")
    else:
        sys.stdout.write(rendered)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
