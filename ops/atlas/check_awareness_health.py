from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.request
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def load_token(args: argparse.Namespace) -> str | None:
    if isinstance(args.auth_token, str) and args.auth_token.strip():
        return args.auth_token.strip()
    env_token = os.environ.get("ATLAS_AWARENESS_TOKEN", "").strip()
    if env_token:
        return env_token
    token_file = args.auth_token_file or os.environ.get("ATLAS_AWARENESS_TOKEN_FILE")
    if token_file:
        return Path(str(token_file)).expanduser().resolve().read_text(encoding="utf-8").strip()
    return None


def request_json(url: str, *, token: str | None = None, etag: str | None = None) -> tuple[dict[str, Any], str | None]:
    headers = {"Accept": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    if etag:
        headers["If-None-Match"] = etag
    request = urllib.request.Request(url, headers=headers, method="GET")
    with urllib.request.urlopen(request, timeout=30) as response:
        payload = json.loads(response.read().decode("utf-8"))
        return payload, response.headers.get("ETag")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Probe the ATLAS Awareness API health and status digests.")
    parser.add_argument("--base-url", default=os.environ.get("ATLAS_AWARENESS_URL", "http://127.0.0.1:8765"))
    parser.add_argument("--auth-token")
    parser.add_argument("--auth-token-file")
    args = parser.parse_args(argv)

    token = load_token(args)
    base_url = str(args.base_url).rstrip("/")
    health, health_etag = request_json(f"{base_url}/health", token=token)
    status_one, etag_one = request_json(f"{base_url}/atlas/status", token=token)
    status_two, etag_two = request_json(f"{base_url}/atlas/status", token=token)

    stable_etag = bool(etag_one and etag_one == etag_two)
    result = {
        "ok": bool(health.get("ok")) and stable_etag,
        "service": health.get("service"),
        "deployment_profile": health.get("deployment_profile"),
        "health_etag": health_etag,
        "status_etag": etag_one,
        "status_etag_stable": stable_etag,
        "digests": status_one.get("digests"),
        "tool_registry_digest": status_one.get("registry", {}).get("tool_registry_digest")
        if isinstance(status_one.get("registry"), dict)
        else None,
        "status_schema_version": status_one.get("schema_version"),
        "status_repeat_schema_version": status_two.get("schema_version"),
    }
    print(json.dumps(result, indent=2))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
