from __future__ import annotations

import argparse
from collections import defaultdict
import json
import os
import sys
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, urlparse

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from ops.atlas.awareness import (
    atlas_status,
    cockpit_status,
    fetch,
    fetch_artifact,
    fetch_session,
    list_attention,
    list_inventory,
    query_knowledge,
    search,
    voice_runtime,
)
from ops.atlas.http_boundary import (
    authenticate_bearer,
    enforce_remote_bind_policy,
    is_loopback_host,
    load_auth_tokens,
)
from ops.atlas.load_tool_registry import automation_level_allows, normalize_automation_level

OBSERVE_AUTOMATION_LEVEL = "observe"
CONTEXT_AUTOMATION_LEVEL = "context"
ROUTE_MAX_AUTOMATION_LEVELS = {
    "/health": OBSERVE_AUTOMATION_LEVEL,
    "/atlas/status": OBSERVE_AUTOMATION_LEVEL,
    "/atlas/cockpit": OBSERVE_AUTOMATION_LEVEL,
    "/atlas/voice": OBSERVE_AUTOMATION_LEVEL,
    "/atlas/inventory": OBSERVE_AUTOMATION_LEVEL,
    "/atlas/snapshot": OBSERVE_AUTOMATION_LEVEL,
    "/atlas/attention": OBSERVE_AUTOMATION_LEVEL,
    "/atlas/search": CONTEXT_AUTOMATION_LEVEL,
    "/atlas/knowledge/query": CONTEXT_AUTOMATION_LEVEL,
    "/atlas/artifacts/fetch": CONTEXT_AUTOMATION_LEVEL,
}


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _first(query: dict[str, list[str]], key: str) -> str | None:
    values = query.get(key)
    if not values:
        return None
    value = values[0].strip()
    return value or None


def _first_int(query: dict[str, list[str]], key: str, default: int) -> int:
    raw = _first(query, key)
    if raw is None:
        return default
    try:
        return int(raw)
    except ValueError:
        return default


def _query_shape(query: dict[str, list[str]]) -> dict[str, list[int]]:
    return {
        key: [len(value) for value in values]
        for key, values in sorted(query.items())
    }


def _append_jsonl(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(payload, ensure_ascii=True) + "\n")


def _prune_old_logs(path: Path, *, retention_days: int) -> None:
    if retention_days <= 0 or not path.exists():
        return
    cutoff = time.time() - (retention_days * 86400)
    for candidate in path.glob("*.jsonl"):
        try:
            if candidate.stat().st_mtime < cutoff:
                candidate.unlink()
        except OSError:
            continue


@dataclass(slots=True)
class AwarenessRateLimiter:
    window_seconds: int
    max_requests: int
    hits: dict[str, list[float]] = field(default_factory=lambda: defaultdict(list))

    def check(self, key: str) -> int | None:
        if self.max_requests <= 0 or self.window_seconds <= 0:
            return None
        now = time.time()
        window_floor = now - self.window_seconds
        bucket = [value for value in self.hits.get(key, []) if value >= window_floor]
        self.hits[key] = bucket
        if len(bucket) >= self.max_requests:
            retry_after = max(1, int(self.window_seconds - (now - bucket[0])))
            return retry_after
        bucket.append(now)
        self.hits[key] = bucket
        return None


@dataclass(slots=True)
class AwarenessServerConfig:
    auth_tokens: list[str]
    request_log_dir: Path
    deployment_profile: str
    request_log_retention_days: int
    rate_limiter: AwarenessRateLimiter


class AwarenessHTTPServer(ThreadingHTTPServer):
    atlas_config: AwarenessServerConfig


class AwarenessHandler(BaseHTTPRequestHandler):
    server_version = "ATLASAwareness/1.1"

    def _config(self) -> AwarenessServerConfig:
        return self.server.atlas_config  # type: ignore[attr-defined]

    def _request_id(self) -> str:
        return uuid.uuid4().hex

    def _authenticate(self) -> tuple[bool, str, str | None]:
        return authenticate_bearer(self.headers, self._config().auth_tokens)

    def _requested_automation_level(self, query: dict[str, list[str]]) -> str:
        raw_value = _first(query, "automation_level") or self.headers.get("X-ATLAS-Automation-Level")
        if raw_value is None:
            return OBSERVE_AUTOMATION_LEVEL
        return normalize_automation_level(raw_value, "automation_level")

    def _max_route_automation_level(self, route: str) -> str:
        if route.startswith("/atlas/sessions/"):
            return CONTEXT_AUTOMATION_LEVEL
        return ROUTE_MAX_AUTOMATION_LEVELS.get(route, OBSERVE_AUTOMATION_LEVEL)

    def _send_json(
        self,
        payload: dict[str, Any],
        *,
        request_id: str,
        status: int = HTTPStatus.OK,
        etag: str | None = None,
        extra_headers: dict[str, str] | None = None,
    ) -> int:
        if etag and self.headers.get("If-None-Match") == etag:
            self.send_response(HTTPStatus.NOT_MODIFIED)
            self.send_header("Cache-Control", "private, no-store")
            self.send_header("ETag", etag)
            self.send_header("X-ATLAS-Request-Id", request_id)
            self.send_header("X-ATLAS-Deployment-Profile", self._config().deployment_profile)
            if extra_headers:
                for key, value in extra_headers.items():
                    self.send_header(key, value)
            self.end_headers()
            return HTTPStatus.NOT_MODIFIED

        encoded = json.dumps(payload, indent=2).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(encoded)))
        self.send_header("Cache-Control", "private, no-store")
        self.send_header("X-ATLAS-Request-Id", request_id)
        self.send_header("X-ATLAS-Deployment-Profile", self._config().deployment_profile)
        if etag:
            self.send_header("ETag", etag)
        if extra_headers:
            for key, value in extra_headers.items():
                self.send_header(key, value)
        self.end_headers()
        self.wfile.write(encoded)
        return status

    def _log_request(
        self,
        *,
        request_id: str,
        route: str,
        query: dict[str, list[str]],
        status: int,
        duration_ms: float,
        auth_result: str,
        auth_principal: str | None,
        error: str | None,
        etag: str | None,
        requested_automation_level: str,
        max_automation_level: str,
    ) -> None:
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        log_path = self._config().request_log_dir / f"{today}.jsonl"
        _append_jsonl(
            log_path,
            {
                "recorded_at": utc_now(),
                "request_id": request_id,
                "remote_addr": self.client_address[0] if self.client_address else None,
                "method": self.command,
                "route": route,
                "query_keys": sorted(query.keys()),
                "query_shape": _query_shape(query),
                "status": int(status),
                "duration_ms": round(duration_ms, 3),
                "auth_required": bool(self._config().auth_tokens),
                "auth_result": auth_result,
                "auth_principal": auth_principal,
                "deployment_profile": self._config().deployment_profile,
                "etag": etag,
                "requested_automation_level": requested_automation_level,
                "max_automation_level": max_automation_level,
                "error": error,
            },
        )

    def _handle_request(self) -> None:
        started = time.perf_counter()
        request_id = self._request_id()
        parsed = urlparse(self.path)
        query = parse_qs(parsed.query, keep_blank_values=False)
        refresh = _first(query, "refresh") == "true"
        route = parsed.path
        status = HTTPStatus.OK
        auth_result = "not_checked"
        auth_principal: str | None = None
        error: str | None = None
        etag: str | None = None
        requested_automation_level = OBSERVE_AUTOMATION_LEVEL
        max_automation_level = OBSERVE_AUTOMATION_LEVEL

        try:
            requested_automation_level = self._requested_automation_level(query)
            max_automation_level = self._max_route_automation_level(route)
            automation_headers = {
                "X-ATLAS-Automation-Level": requested_automation_level,
                "X-ATLAS-Max-Automation-Level": max_automation_level,
            }
            if not automation_level_allows(
                max_level=max_automation_level,
                requested_level=requested_automation_level,
            ):
                status = self._send_json(
                    {
                        "ok": False,
                        "error": "automation_level_denied",
                        "message": "Requested automation level exceeds the read-only policy for this Awareness API route.",
                        "requested_automation_level": requested_automation_level,
                        "max_automation_level": max_automation_level,
                    },
                    request_id=request_id,
                    status=HTTPStatus.FORBIDDEN,
                    extra_headers=automation_headers,
                )
                return

            remote_addr = self.client_address[0] if self.client_address else "unknown"
            retry_after = self._config().rate_limiter.check(remote_addr)
            if retry_after is not None:
                status = self._send_json(
                    {
                        "ok": False,
                        "error": "rate_limited",
                        "message": "The ATLAS Awareness API rate limit was exceeded for this client.",
                        "category": "abuse-control",
                        "retryable": True,
                    },
                    request_id=request_id,
                    status=HTTPStatus.TOO_MANY_REQUESTS,
                    extra_headers={**automation_headers, "Retry-After": str(retry_after)},
                )
                return

            if parsed.path == "/health":
                payload = atlas_status(refresh=False)
                etag = "|".join(
                    str(item)
                    for item in [
                        payload.get("digests", {}).get("registry_digest") if isinstance(payload.get("digests"), dict) else None,
                        payload.get("digests", {}).get("world_model_digest") if isinstance(payload.get("digests"), dict) else None,
                        payload.get("digests", {}).get("attention_digest") if isinstance(payload.get("digests"), dict) else None,
                        payload.get("digests", {}).get("working_memory_digest") if isinstance(payload.get("digests"), dict) else None,
                    ]
                    if isinstance(item, str) and item
                ) or None
                status = self._send_json(
                    {
                        "ok": True,
                        "service": "atlas-awareness",
                        "auth_required": bool(self._config().auth_tokens),
                        "deployment_profile": self._config().deployment_profile,
                        "read_only": True,
                        "requested_automation_level": requested_automation_level,
                        "max_automation_level": max_automation_level,
                        "request_log_retention_days": self._config().request_log_retention_days,
                        "rate_limit": {
                            "window_seconds": self._config().rate_limiter.window_seconds,
                            "max_requests": self._config().rate_limiter.max_requests,
                        },
                        "digests": payload.get("digests"),
                    },
                    request_id=request_id,
                    etag=etag,
                    extra_headers=automation_headers,
                )
                return

            authenticated, auth_result, auth_principal = self._authenticate()
            if not authenticated:
                status = self._send_json(
                    {
                        "ok": False,
                        "error": "unauthorized",
                        "message": "A valid bearer token is required for the ATLAS Awareness API.",
                        "category": "auth",
                        "retryable": False,
                    },
                    request_id=request_id,
                    status=HTTPStatus.UNAUTHORIZED,
                    extra_headers={**automation_headers, "WWW-Authenticate": 'Bearer realm="atlas-awareness"'},
                )
                return

            if parsed.path == "/atlas/status":
                payload = atlas_status(refresh=refresh)
                etag = str(payload.get("snapshot", {}).get("content_digest") or "")
                status = self._send_json(payload, request_id=request_id, etag=etag, extra_headers=automation_headers)
                return

            if parsed.path == "/atlas/cockpit":
                payload = cockpit_status(refresh=refresh)
                digests = payload.get("digests") if isinstance(payload.get("digests"), dict) else {}
                lock_hygiene = (
                    payload.get("lock_worktree_hygiene", {})
                    if isinstance(payload.get("lock_worktree_hygiene"), dict)
                    else {}
                )
                etag = "|".join(
                    str(value or "")
                    for value in [
                        digests.get("world_model_digest"),
                        digests.get("attention_digest"),
                        digests.get("working_memory_digest"),
                        digests.get("repo_inventory_digest"),
                        lock_hygiene.get("generated_lock_digest"),
                    ]
                )
                status = self._send_json(payload, request_id=request_id, etag=etag, extra_headers=automation_headers)
                return

            if parsed.path == "/atlas/voice":
                payload = voice_runtime(
                    refresh=refresh,
                    conversation_id=_first(query, "conversation_id"),
                )
                digests = payload.get("digests") if isinstance(payload.get("digests"), dict) else {}
                conversation = payload.get("conversation") if isinstance(payload.get("conversation"), dict) else {}
                conversation_summary = conversation.get("summary") if isinstance(conversation.get("summary"), dict) else {}
                etag = "|".join(
                    str(value or "")
                    for value in [
                        digests.get("world_model_digest"),
                        digests.get("attention_digest"),
                        digests.get("working_memory_digest"),
                        conversation_summary.get("last_turn_at"),
                    ]
                )
                status = self._send_json(payload, request_id=request_id, etag=etag, extra_headers=automation_headers)
                return

            if parsed.path in {"/atlas/inventory", "/atlas/snapshot"}:
                payload = list_inventory(
                    refresh=refresh,
                    entry_type=_first(query, "entry_type"),
                    status=_first(query, "status"),
                    trust_class=_first(query, "trust_class"),
                    query=_first(query, "query"),
                    limit=_first_int(query, "limit", 0) or None,
                )
                etag = str(payload.get("snapshot_content_digest") or "")
                status = self._send_json(payload, request_id=request_id, etag=etag, extra_headers=automation_headers)
                return

            if parsed.path == "/atlas/attention":
                payload = list_attention(
                    refresh=refresh,
                    severity=_first(query, "severity"),
                    query=_first(query, "query"),
                    limit=_first_int(query, "limit", 0) or None,
                )
                etag = str(payload.get("attention_content_digest") or "")
                status = self._send_json(payload, request_id=request_id, etag=etag, extra_headers=automation_headers)
                return

            if parsed.path == "/atlas/search":
                q = _first(query, "q")
                if q is None:
                    raise ValueError("Missing required query parameter: q")
                payload = search(q, refresh=refresh, limit=_first_int(query, "limit", 10))
                status = self._send_json(payload, request_id=request_id, extra_headers=automation_headers)
                return

            if parsed.path == "/atlas/knowledge/query":
                q = _first(query, "q")
                if q is None:
                    raise ValueError("Missing required query parameter: q")
                payload = query_knowledge(q, refresh=refresh, limit=_first_int(query, "limit", 5))
                status = self._send_json(payload, request_id=request_id, extra_headers=automation_headers)
                return

            if parsed.path == "/atlas/artifacts/fetch":
                identifier = _first(query, "id")
                ref = _first(query, "ref")
                if identifier:
                    payload = fetch(identifier, refresh=refresh)
                elif ref:
                    payload = fetch_artifact(ref)
                else:
                    raise ValueError("Provide either id or ref for /atlas/artifacts/fetch")
                status = self._send_json(payload, request_id=request_id, extra_headers=automation_headers)
                return

            if parsed.path.startswith("/atlas/sessions/"):
                session_id = parsed.path.rsplit("/", 1)[-1].strip()
                if not session_id:
                    raise ValueError("Session path must end with a session id.")
                payload = fetch_session(session_id, refresh=refresh)
                status = self._send_json(payload, request_id=request_id, extra_headers=automation_headers)
                return

            status = self._send_json(
                {
                    "ok": False,
                    "error": "not_found",
                    "path": parsed.path,
                    "category": "routing",
                    "retryable": False,
                },
                request_id=request_id,
                status=HTTPStatus.NOT_FOUND,
                extra_headers=automation_headers,
            )
        except FileNotFoundError as exc:
            error = str(exc)
            status = self._send_json(
                {"ok": False, "error": "not_found", "message": error, "category": "lookup", "retryable": False},
                request_id=request_id,
                status=HTTPStatus.NOT_FOUND,
                extra_headers={
                    "X-ATLAS-Automation-Level": requested_automation_level,
                    "X-ATLAS-Max-Automation-Level": max_automation_level,
                },
            )
        except ValueError as exc:
            error = str(exc)
            status = self._send_json(
                {"ok": False, "error": "bad_request", "message": error, "category": "client-contract", "retryable": False},
                request_id=request_id,
                status=HTTPStatus.BAD_REQUEST,
                extra_headers={
                    "X-ATLAS-Automation-Level": requested_automation_level,
                    "X-ATLAS-Max-Automation-Level": max_automation_level,
                },
            )
        except Exception as exc:  # pragma: no cover - defensive server path
            error = str(exc)
            status = self._send_json(
                {"ok": False, "error": "internal_error", "message": error, "category": "server", "retryable": True},
                request_id=request_id,
                status=HTTPStatus.INTERNAL_SERVER_ERROR,
                extra_headers={
                    "X-ATLAS-Automation-Level": requested_automation_level,
                    "X-ATLAS-Max-Automation-Level": max_automation_level,
                },
            )
        finally:
            _prune_old_logs(
                self._config().request_log_dir,
                retention_days=self._config().request_log_retention_days,
            )
            self._log_request(
                request_id=request_id,
                route=route,
                query=query,
                status=status,
                duration_ms=(time.perf_counter() - started) * 1000,
                auth_result=auth_result,
                auth_principal=auth_principal,
                error=error,
                etag=etag,
                requested_automation_level=requested_automation_level,
                max_automation_level=max_automation_level,
            )

    def do_GET(self) -> None:  # noqa: N802
        self._handle_request()

    def log_message(self, format: str, *args: object) -> None:  # noqa: A003
        return


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Serve the ATLAS Awareness API over HTTP.")
    parser.add_argument("--host", default=os.environ.get("ATLAS_AWARENESS_HOST", "127.0.0.1"))
    parser.add_argument("--port", type=int, default=int(os.environ.get("ATLAS_AWARENESS_PORT", "8765")))
    parser.add_argument("--auth-token")
    parser.add_argument("--auth-token-file")
    parser.add_argument("--auth-token-previous")
    parser.add_argument("--auth-token-previous-file")
    parser.add_argument("--allow-unauthenticated", action="store_true")
    parser.add_argument("--deployment-profile", choices=["local-only", "hosted"])
    parser.add_argument("--request-log-retention-days", type=int, default=int(os.environ.get("ATLAS_AWARENESS_REQUEST_LOG_RETENTION_DAYS", "14")))
    parser.add_argument("--rate-limit-window-seconds", type=int, default=int(os.environ.get("ATLAS_AWARENESS_RATE_LIMIT_WINDOW_SECONDS", "60")))
    parser.add_argument("--rate-limit-max-requests", type=int, default=int(os.environ.get("ATLAS_AWARENESS_RATE_LIMIT_MAX_REQUESTS", "120")))
    parser.add_argument(
        "--request-log-dir",
        default=str(ROOT / "runtime" / "atlas" / "awareness" / "requests"),
    )
    args = parser.parse_args(argv)

    auth_tokens = load_auth_tokens(
        specs=[
            (
                args.auth_token,
                args.auth_token_file,
                "ATLAS_AWARENESS_TOKEN",
                "ATLAS_AWARENESS_TOKEN_FILE",
            ),
            (
                args.auth_token_previous,
                args.auth_token_previous_file,
                "ATLAS_AWARENESS_PREVIOUS_TOKEN",
                "ATLAS_AWARENESS_PREVIOUS_TOKEN_FILE",
            ),
        ]
    )
    deployment_profile = args.deployment_profile or ("local-only" if is_loopback_host(args.host) else "hosted")
    enforce_remote_bind_policy(
        parser=parser,
        host=args.host,
        auth_tokens=auth_tokens,
        allow_unauthenticated=args.allow_unauthenticated,
        error_message="Remote ATLAS Awareness API binds require --auth-token or --auth-token-file unless --allow-unauthenticated is set.",
    )

    request_log_dir = Path(args.request_log_dir).resolve()
    _prune_old_logs(request_log_dir, retention_days=args.request_log_retention_days)
    server = AwarenessHTTPServer((args.host, args.port), AwarenessHandler)
    server.atlas_config = AwarenessServerConfig(
        auth_tokens=auth_tokens,
        request_log_dir=request_log_dir,
        deployment_profile=deployment_profile,
        request_log_retention_days=args.request_log_retention_days,
        rate_limiter=AwarenessRateLimiter(
            window_seconds=args.rate_limit_window_seconds,
            max_requests=args.rate_limit_max_requests,
        ),
    )
    print(
        json.dumps(
            {
                "host": args.host,
                "port": args.port,
                "service": "atlas-awareness",
                "auth_required": bool(auth_tokens),
                "deployment_profile": deployment_profile,
                "token_rotation_enabled": len(auth_tokens) > 1,
                "request_log_dir": str(server.atlas_config.request_log_dir),
                "request_log_retention_days": args.request_log_retention_days,
                "rate_limit_window_seconds": args.rate_limit_window_seconds,
                "rate_limit_max_requests": args.rate_limit_max_requests,
            },
            indent=2,
        )
    )
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
