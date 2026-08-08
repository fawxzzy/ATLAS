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
from ops.atlas.qa._common import default_adapter_dir, load_json_object, utc_now
from ops.cortex._artifacts import write_json


def default_bootstrap_adapter_repo_path(*, root: Path | None = None) -> Path:
    base = (root or atlas_root()).resolve()
    return base / "runtime" / "atlas" / "qa" / "bootstrap-adapter-repo.latest.json"


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


def _status_porcelain(repo_path: Path) -> list[str]:
    code, stdout, _ = _git(repo_path, "status", "--porcelain=v1", "--untracked-files=all")
    if code != 0:
        return []
    return [line for line in stdout.splitlines() if line.strip()]


def _ensure_commit_available(repo_path: Path, requested_sha: str) -> tuple[bool, str]:
    code, _, stderr = _git(repo_path, "cat-file", "-e", f"{requested_sha}^{{commit}}")
    if code == 0:
        return True, ""
    first_error = stderr

    # Reused CI worktrees may carry a narrow remote refspec. Fetch all branch refs
    # before declaring a just-pushed target SHA unavailable.
    code, _, fetch_stderr = _git(
        repo_path,
        "fetch",
        "--tags",
        "--prune",
        "origin",
        "+refs/heads/*:refs/remotes/origin/*",
    )
    if code != 0:
        return False, fetch_stderr or first_error

    code, _, stderr = _git(repo_path, "cat-file", "-e", f"{requested_sha}^{{commit}}")
    if code == 0:
        return True, ""
    return False, stderr or first_error or f"requested commit '{requested_sha}' is not available after fetch."


def _load_adapter(*, root: Path, adapter_id: str) -> tuple[dict[str, Any], Path]:
    adapter_path = default_adapter_dir(root=root) / f"{adapter_id}.json"
    if not adapter_path.exists():
        raise FileNotFoundError(f"Adapter manifest not found: {atlas_relative(adapter_path, root=root)}")
    payload = load_json_object(adapter_path)
    return payload, adapter_path.resolve()


def _load_repo_inventory(*, root: Path) -> dict[str, Any]:
    inventory_path = root / "docs" / "registry" / "STACK-REPO-INVENTORY.json"
    if not inventory_path.exists():
        raise FileNotFoundError("Repo inventory not found: docs/registry/STACK-REPO-INVENTORY.json")
    return load_json_object(inventory_path.resolve())


def _resolve_repo_inventory_entry(
    *,
    root: Path,
    repo_id: str,
    repo_path: str,
) -> dict[str, Any]:
    inventory = _load_repo_inventory(root=root)
    repos = inventory.get("repos", [])
    if not isinstance(repos, list):
        raise ValueError("Repo inventory is invalid: repos must be a list.")
    normalized_repo_path = repo_path.replace("\\", "/").strip()
    for item in repos:
        if not isinstance(item, dict):
            continue
        logical_id = str(item.get("logical_id") or "").strip()
        local_path = str(item.get("local_path") or "").replace("\\", "/").strip()
        if logical_id == repo_id or (normalized_repo_path and local_path == normalized_repo_path):
            return item
    raise KeyError(
        f"Repo inventory entry not found for repo_id '{repo_id}' and path '{normalized_repo_path}'."
    )


def bootstrap_adapter_repo(
    *,
    root: Path | None = None,
    adapter: str,
    target_sha: str | None = None,
    output_file: Path | None = None,
) -> dict[str, Any]:
    base_root = (root or atlas_root()).resolve()
    adapter_payload, adapter_path = _load_adapter(root=base_root, adapter_id=adapter)
    repo_id = str(adapter_payload.get("repo_id") or "").strip()
    repo_path_raw = str(adapter_payload.get("repo_path") or "").strip()
    if not repo_id or not repo_path_raw:
        raise ValueError("Adapter manifest must declare repo_id and repo_path.")
    inventory_entry = _resolve_repo_inventory_entry(root=base_root, repo_id=repo_id, repo_path=repo_path_raw)
    remote_url = str(inventory_entry.get("remote_url") or "").strip()
    if not remote_url:
        raise ValueError(f"Repo inventory entry for '{repo_id}' is missing remote_url.")

    repo_path = (base_root / repo_path_raw).resolve()
    requested_sha = str(target_sha or "").strip() or str(inventory_entry.get("current_commit") or "").strip()
    requested_sha_source = "target_sha" if str(target_sha or "").strip() else "repo_inventory.current_commit"
    if not requested_sha:
        raise ValueError(
            f"Protected adapter bootstrap for '{repo_id}' requires --target-sha or a repo inventory current_commit."
        )

    result = {
        "repo_id": repo_id,
        "adapter_id": str(adapter_payload.get("adapter_id") or adapter).strip(),
        "adapter_ref": atlas_relative(adapter_path, root=base_root),
        "repo_path": atlas_relative(repo_path, root=base_root),
        "remote_url": remote_url,
        "requested_sha": requested_sha,
        "requested_sha_source": requested_sha_source,
        "checkout_sha": "",
        "status": "planned",
        "message": "",
    }

    repo_path.parent.mkdir(parents=True, exist_ok=True)
    if not repo_path.exists():
        code, _, stderr = _git(None, "clone", remote_url, str(repo_path))
        if code != 0:
            result["status"] = "failed"
            result["message"] = stderr or "git clone failed."
            raise RuntimeError(result["message"])
    code, stdout, stderr = _git(repo_path, "rev-parse", "--show-toplevel")
    if code != 0 or Path(stdout).resolve() != repo_path:
        result["status"] = "failed"
        result["message"] = stderr or "bootstrap target is not a git root."
        raise RuntimeError(result["message"])
    existing_dirty = _status_porcelain(repo_path)
    if existing_dirty:
        result["status"] = "failed"
        result["message"] = "bootstrap target has local modifications and cannot be trusted for protected execution."
        raise RuntimeError(result["message"])
    code, _, stderr = _git(repo_path, "remote", "set-url", "origin", remote_url)
    if code != 0:
        result["status"] = "failed"
        result["message"] = stderr or "unable to set origin remote."
        raise RuntimeError(result["message"])
    code, _, stderr = _git(repo_path, "fetch", "--tags", "--prune", "origin")
    if code != 0:
        result["status"] = "failed"
        result["message"] = stderr or "git fetch failed."
        raise RuntimeError(result["message"])
    commit_available, stderr = _ensure_commit_available(repo_path, requested_sha)
    if not commit_available:
        result["status"] = "failed"
        result["message"] = stderr or f"requested commit '{requested_sha}' is not available after fetch."
        raise RuntimeError(result["message"])
    code, _, stderr = _git(repo_path, "checkout", "--detach", requested_sha)
    if code != 0:
        result["status"] = "failed"
        result["message"] = stderr or "git checkout failed."
        raise RuntimeError(result["message"])
    code, head, stderr = _git(repo_path, "rev-parse", "HEAD")
    if code != 0:
        result["status"] = "failed"
        result["message"] = stderr or "unable to resolve checkout HEAD."
        raise RuntimeError(result["message"])
    result["checkout_sha"] = head
    if head != requested_sha:
        result["status"] = "failed"
        result["message"] = f"checked out SHA '{head}' does not match requested SHA '{requested_sha}'."
        raise RuntimeError(result["message"])
    existing_dirty = _status_porcelain(repo_path)
    if existing_dirty:
        result["status"] = "failed"
        result["message"] = "checked out repo is dirty after bootstrap."
        raise RuntimeError(result["message"])
    result["status"] = "ready"
    result["message"] = "exact-SHA adapter repo checkout is present and clean."

    payload = {
        "contract_version": "atlas.qa.bootstrap_adapter_repo.v1",
        "generated_at": utc_now(),
        "result": result,
    }
    target = output_file.resolve() if isinstance(output_file, Path) else default_bootstrap_adapter_repo_path(root=base_root)
    target.parent.mkdir(parents=True, exist_ok=True)
    write_json(target, payload)
    md_path = target.with_suffix(".md")
    md_lines = [
        "# ATLAS Adapter Repo Bootstrap",
        "",
        f"- Generated at: `{payload['generated_at']}`",
        f"- Repo: `{repo_id}`",
        f"- Adapter: `{result['adapter_id']}`",
        f"- Path: `{result['repo_path']}`",
        f"- Remote: `{remote_url}`",
        f"- Requested SHA: `{requested_sha}`",
        f"- Requested SHA source: `{requested_sha_source}`",
        f"- Checkout SHA: `{result['checkout_sha'] or '-'}`",
        f"- Status: `{result['status']}`",
        f"- Message: {result['message']}",
    ]
    md_path.write_text("\n".join(md_lines) + "\n", encoding="utf-8")
    return {
        "generated_at": payload["generated_at"],
        "bootstrap_adapter_repo_ref": atlas_relative(target, root=base_root),
        "bootstrap_adapter_repo_md_ref": atlas_relative(md_path, root=base_root),
        "repo_id": repo_id,
        "adapter_id": result["adapter_id"],
        "checkout_sha": result["checkout_sha"],
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Bootstrap a protected adapter repo checkout from the tracked stack repo inventory.")
    parser.add_argument("--root", type=Path, default=atlas_root())
    parser.add_argument("--adapter", required=True)
    parser.add_argument("--target-sha")
    parser.add_argument("--output-file", type=Path)
    args = parser.parse_args(argv)
    result = bootstrap_adapter_repo(
        root=args.root.resolve(),
        adapter=str(args.adapter).strip(),
        target_sha=str(args.target_sha or "").strip() or None,
        output_file=args.output_file.resolve() if isinstance(args.output_file, Path) else None,
    )
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
