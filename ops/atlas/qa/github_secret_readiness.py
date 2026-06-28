from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any, Callable

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from ops._atlas import atlas_relative, atlas_root
from ops.atlas.qa._common import utc_now
from ops.cortex._artifacts import write_json


def default_github_secret_readiness_path(*, root: Path | None = None) -> Path:
    base = (root or atlas_root()).resolve()
    return base / "runtime" / "atlas" / "qa" / "github-secret-readiness.latest.json"


def _git_credential_fill(*, host: str = "github.com", protocol: str = "https") -> dict[str, str]:
    completed = subprocess.run(
        ["git", "credential", "fill"],
        input=f"protocol={protocol}\nhost={host}\n\n",
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    payload: dict[str, str] = {}
    for raw_line in completed.stdout.splitlines():
        line = raw_line.strip()
        if not line or "=" not in line:
            continue
        key, value = line.split("=", 1)
        payload[key.strip()] = value.strip()
    return payload


def _resolve_github_token() -> str:
    for env_name in ("GITHUB_TOKEN", "GH_TOKEN", "ATLAS_GITHUB_TOKEN"):
        value = str(os.environ.get(env_name) or "").strip()
        if value:
            return value
    payload = _git_credential_fill()
    token = str(payload.get("password") or "").strip()
    if not token:
        raise RuntimeError("No GitHub token available via env or git credential fill.")
    return token


def _fetch_secret_names(repo: str, token: str) -> list[str]:
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "User-Agent": "atlas-qa-github-secret-readiness",
    }
    names: list[str] = []
    page = 1
    while True:
        query = urllib.parse.urlencode({"per_page": 100, "page": page})
        request = urllib.request.Request(
            f"https://api.github.com/repos/{repo}/actions/secrets?{query}",
            headers=headers,
            method="GET",
        )
        try:
            with urllib.request.urlopen(request, timeout=30) as response:
                payload = json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")
            raise RuntimeError(f"GitHub API request failed for repo '{repo}': HTTP {exc.code} {detail}") from exc
        except urllib.error.URLError as exc:
            raise RuntimeError(f"GitHub API request failed for repo '{repo}': {exc.reason}") from exc

        secrets = payload.get("secrets", [])
        if not isinstance(secrets, list):
            raise RuntimeError(f"GitHub API returned invalid secrets payload for repo '{repo}'.")
        page_names = [
            str(item.get("name") or "").strip()
            for item in secrets
            if isinstance(item, dict) and str(item.get("name") or "").strip()
        ]
        names.extend(page_names)
        total_count = payload.get("total_count")
        if not isinstance(total_count, int):
            total_count = len(names)
        if len(names) >= total_count or not page_names:
            break
        page += 1
    return sorted(set(names))


def github_secret_readiness(
    *,
    root: Path | None = None,
    repo: str,
    required_secret_names: list[str],
    output_file: Path | None = None,
    token: str | None = None,
    secret_names_fetcher: Callable[[str, str], list[str]] | None = None,
) -> dict[str, Any]:
    base_root = (root or atlas_root()).resolve()
    normalized_repo = str(repo).strip()
    required = sorted({str(name).strip() for name in required_secret_names if str(name).strip()})
    if not normalized_repo:
        raise ValueError("Repo must be provided in owner/name form.")
    if not required:
        raise ValueError("At least one required secret name must be provided.")

    resolved_token = str(token or "").strip() or _resolve_github_token()
    fetcher = secret_names_fetcher or _fetch_secret_names
    available_secret_names = fetcher(normalized_repo, resolved_token)
    statuses = {
        name: ("present" if name in available_secret_names else "missing")
        for name in required
    }
    missing = [name for name, status in statuses.items() if status == "missing"]
    browserstack_named = [
        name for name in available_secret_names
        if "BROWSERSTACK" in name.upper()
    ]
    payload = {
        "contract_version": "atlas.qa.github_secret_readiness.v1",
        "generated_at": utc_now(),
        "repo": normalized_repo,
        "available_secret_count": len(available_secret_names),
        "required_secret_names": required,
        "required_secret_statuses": statuses,
        "missing_required_secret_names": missing,
        "browserstack_named_secret_names": browserstack_named,
        "status": "ready" if not missing else "blocked",
    }
    target = output_file.resolve() if isinstance(output_file, Path) else default_github_secret_readiness_path(root=base_root)
    target.parent.mkdir(parents=True, exist_ok=True)
    write_json(target, payload)
    md_path = target.with_suffix(".md")
    md_lines = [
        "# ATLAS GitHub Secret Readiness",
        "",
        f"- Generated at: `{payload['generated_at']}`",
        f"- Repo: `{normalized_repo}`",
        f"- Available secret count: `{payload['available_secret_count']}`",
        f"- Required secrets: `{', '.join(required)}`",
        f"- Status: `{payload['status']}`",
    ]
    for secret_name in required:
        md_lines.append(f"- `{secret_name}`: `{statuses[secret_name]}`")
    if browserstack_named:
        md_lines.append(f"- BrowserStack-named secrets: `{', '.join(browserstack_named)}`")
    else:
        md_lines.append("- BrowserStack-named secrets: `none`")
    md_path.write_text("\n".join(md_lines) + "\n", encoding="utf-8")
    return {
        "generated_at": payload["generated_at"],
        "github_secret_readiness_ref": atlas_relative(target, root=base_root),
        "github_secret_readiness_md_ref": atlas_relative(md_path, root=base_root),
        "repo": normalized_repo,
        "status": payload["status"],
        "missing_required_secret_names": missing,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Audit GitHub Actions secret-name readiness for a repo.")
    parser.add_argument("--root", type=Path, default=atlas_root())
    parser.add_argument("--repo", required=True, help="GitHub repo in owner/name form.")
    parser.add_argument(
        "--require-secret",
        dest="required_secret_names",
        action="append",
        default=[],
        help="Required Actions secret name. Repeat for multiple names.",
    )
    parser.add_argument("--output-file", type=Path)
    args = parser.parse_args(argv)
    report = github_secret_readiness(
        root=args.root.resolve(),
        repo=str(args.repo).strip(),
        required_secret_names=[str(item).strip() for item in args.required_secret_names],
        output_file=args.output_file.resolve() if isinstance(args.output_file, Path) else None,
    )
    print(json.dumps(report, indent=2))
    return 0 if report["status"] == "ready" else 1


if __name__ == "__main__":
    raise SystemExit(main())
