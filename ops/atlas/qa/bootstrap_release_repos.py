from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from ops._atlas import atlas_relative, atlas_root
from ops.atlas.qa._common import default_release_policy_path, load_json_object, utc_now
from ops.stack.generate_lockfile import default_lockfile_path, load_lockfile
from ops.cortex._artifacts import write_json


def default_bootstrap_release_repos_path(*, root: Path | None = None) -> Path:
    base = (root or atlas_root()).resolve()
    return base / "runtime" / "atlas" / "qa" / "bootstrap-release-repos.latest.json"


def _git(repo_path: Path | None, *args: str) -> tuple[int, str, str]:
    command = ["git"]
    if isinstance(repo_path, Path):
        command.extend(["-C", str(repo_path)])
    command.extend(args)
    completed = subprocess.run(
        command,
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    return completed.returncode, completed.stdout.strip(), completed.stderr.strip()


def _requested_release_repo_ids(*, root: Path, repo_ids: list[str] | None = None) -> list[str]:
    explicit = [repo_id.strip() for repo_id in (repo_ids or []) if repo_id and repo_id.strip()]
    if explicit:
        return explicit
    policy = load_json_object(default_release_policy_path(root=root))
    repo_overrides = policy.get("repo_overrides", {}) if isinstance(policy.get("repo_overrides"), dict) else {}
    requested = sorted(str(repo_id).strip() for repo_id in repo_overrides if str(repo_id).strip())
    if not requested:
        raise ValueError("No release repos were resolved from release_policy.v1.json.")
    return requested


def _status_porcelain(repo_path: Path) -> list[str]:
    code, stdout, _ = _git(repo_path, "status", "--porcelain=v1", "--untracked-files=all")
    if code != 0:
        return []
    return [line for line in stdout.splitlines() if line.strip()]


def _bootstrap_repo(
    *,
    root: Path,
    repo_id: str,
    component: dict[str, Any],
) -> dict[str, Any]:
    repo_path_raw = str(component.get("path") or "").strip()
    remote = component.get("remote")
    remote_value = str(remote).strip() if isinstance(remote, str) else ""
    commit = str(component.get("commit") or "").strip()
    dirty = bool(component.get("dirty"))
    release_eligible = bool(component.get("release_eligible"))
    repo_path = (root / repo_path_raw).resolve() if repo_path_raw else root
    parent = repo_path.parent
    result = {
        "repo_id": repo_id,
        "path": atlas_relative(repo_path, root=root),
        "remote": remote_value,
        "commit": commit,
        "release_eligible": release_eligible,
        "dirty_in_lock": dirty,
        "status": "planned",
        "checkout_sha": "",
        "message": "",
    }
    if not repo_path_raw:
        result["status"] = "failed"
        result["message"] = "stack.lock entry is missing path."
        return result
    if not remote_value:
        result["status"] = "failed"
        result["message"] = "stack.lock entry is missing remote."
        return result
    if not commit:
        result["status"] = "failed"
        result["message"] = "stack.lock entry is missing commit."
        return result
    if release_eligible and dirty:
        result["status"] = "failed"
        result["message"] = "release-eligible target is still marked dirty in stack.lock.yaml."
        return result
    parent.mkdir(parents=True, exist_ok=True)
    if not repo_path.exists():
        code, _, stderr = _git(None, "clone", remote_value, str(repo_path))
        if code != 0:
            result["status"] = "failed"
            result["message"] = stderr or "git clone failed."
            return result
    code, stdout, stderr = _git(repo_path, "rev-parse", "--show-toplevel")
    if code != 0 or Path(stdout).resolve() != repo_path.resolve():
        result["status"] = "failed"
        result["message"] = stderr or "bootstrap target is not a git root."
        return result
    existing_dirty = _status_porcelain(repo_path)
    if existing_dirty:
        result["status"] = "failed"
        result["message"] = "bootstrap target has local modifications and cannot be trusted for protected release proof."
        return result
    code, _, stderr = _git(repo_path, "remote", "set-url", "origin", remote_value)
    if code != 0:
        result["status"] = "failed"
        result["message"] = stderr or "unable to set origin remote."
        return result
    code, _, stderr = _git(repo_path, "fetch", "--tags", "--prune", "origin")
    if code != 0:
        result["status"] = "failed"
        result["message"] = stderr or "git fetch failed."
        return result
    code, _, stderr = _git(repo_path, "cat-file", "-e", f"{commit}^{{commit}}")
    if code != 0:
        result["status"] = "failed"
        result["message"] = stderr or f"locked commit '{commit}' is not available after fetch."
        return result
    code, _, stderr = _git(repo_path, "checkout", "--detach", commit)
    if code != 0:
        result["status"] = "failed"
        result["message"] = stderr or "git checkout failed."
        return result
    code, head, stderr = _git(repo_path, "rev-parse", "HEAD")
    if code != 0:
        result["status"] = "failed"
        result["message"] = stderr or "unable to resolve checkout HEAD."
        return result
    result["checkout_sha"] = head
    if head != commit:
        result["status"] = "failed"
        result["message"] = f"checked out SHA '{head}' does not match locked commit '{commit}'."
        return result
    existing_dirty = _status_porcelain(repo_path)
    if existing_dirty:
        result["status"] = "failed"
        result["message"] = "checked out repo is dirty after bootstrap."
        return result
    result["status"] = "ready"
    result["message"] = "exact-SHA checkout is present and clean."
    return result


def bootstrap_release_repos(
    *,
    root: Path | None = None,
    repo_ids: list[str] | None = None,
    output_file: Path | None = None,
) -> dict[str, Any]:
    base_root = (root or atlas_root()).resolve()
    requested = _requested_release_repo_ids(root=base_root, repo_ids=repo_ids)
    lockfile_path = default_lockfile_path(root=base_root)
    lockfile = load_lockfile(lockfile_path)
    components = lockfile.get("components", {}) if isinstance(lockfile.get("components"), dict) else {}
    repos: list[dict[str, Any]] = []
    failures: list[str] = []
    for repo_id in requested:
        component = components.get(repo_id)
        if not isinstance(component, dict):
            repos.append(
                {
                    "repo_id": repo_id,
                    "path": "",
                    "remote": "",
                    "commit": "",
                    "release_eligible": False,
                    "dirty_in_lock": False,
                    "status": "failed",
                    "checkout_sha": "",
                    "message": "repo is missing from stack.lock.yaml.",
                }
            )
            failures.append(f"{repo_id}: repo is missing from stack.lock.yaml.")
            continue
        result = _bootstrap_repo(root=base_root, repo_id=repo_id, component=component)
        repos.append(result)
        if result["status"] != "ready":
            failures.append(f"{repo_id}: {result['message']}")
    payload = {
        "contract_version": "atlas.qa.bootstrap_release_repos.v1",
        "generated_at": utc_now(),
        "stack_lock_ref": atlas_relative(lockfile_path, root=base_root),
        "requested_repo_ids": requested,
        "repos": repos,
        "summary": {
            "repo_count": len(repos),
            "ready_count": sum(1 for item in repos if item.get("status") == "ready"),
            "failed_count": sum(1 for item in repos if item.get("status") == "failed"),
        },
    }
    target = output_file.resolve() if isinstance(output_file, Path) else default_bootstrap_release_repos_path(root=base_root)
    target.parent.mkdir(parents=True, exist_ok=True)
    write_json(target, payload)
    md_path = target.with_suffix(".md")
    md_lines = [
        "# ATLAS Release Repo Bootstrap",
        "",
        f"- Generated at: `{payload['generated_at']}`",
        f"- Stack lock: `{payload['stack_lock_ref']}`",
        f"- Requested repos: `{', '.join(requested)}`",
        f"- Ready: `{payload['summary']['ready_count']}`",
        f"- Failed: `{payload['summary']['failed_count']}`",
        "",
        "| Repo | Path | Commit | Dirty In Lock | Status | Message |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for item in repos:
        md_lines.append(
            f"| {item['repo_id']} | {item['path'] or '-'} | {item['commit'] or '-'} | {item['dirty_in_lock']} | {item['status']} | {item['message']} |"
        )
    md_path.write_text("\n".join(md_lines) + "\n", encoding="utf-8")
    if failures:
        raise SystemExit("; ".join(failures))
    return {
        "generated_at": payload["generated_at"],
        "bootstrap_release_repos_ref": atlas_relative(target, root=base_root),
        "bootstrap_release_repos_md_ref": atlas_relative(md_path, root=base_root),
        "repo_count": len(repos),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Bootstrap release repos from stack.lock.yaml for protected QA execution.")
    parser.add_argument("--root", type=Path, default=atlas_root())
    parser.add_argument("--repo", action="append", default=[])
    parser.add_argument("--output-file", type=Path)
    args = parser.parse_args(argv)
    result = bootstrap_release_repos(
        root=args.root.resolve(),
        repo_ids=[str(item).strip() for item in args.repo if str(item).strip()],
        output_file=args.output_file.resolve() if isinstance(args.output_file, Path) else None,
    )
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
