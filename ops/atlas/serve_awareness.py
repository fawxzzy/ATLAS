from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
import time
import uuid
from dataclasses import dataclass
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
    fetch,
    fetch_artifact,
    fetch_session,
    list_attention,
    list_inventory,
    query_knowledge,
    search,
)


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


def _token_fingerprint(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()[:16]


def _load_auth_token(args: argparse.Namespace) -> str | None:
    if isinstance(args.auth_token, str) and args.auth_token.strip():
        return args.auth_token.strip()
    env_token = os.environ.get("ATLAS_AWARENESS_TOKEN", "").strip()
    if env_token:
        return env_token
    token_file = args.auth_token_file or os.environ.get("ATLAS_AWARENESS_TOKEN_FILE")
    if token_file:
        token_path = Path(str(token_file)).expanduser().resolve()
        token = token_path.read_text(encoding="utf-8").strip()
        if token:
            return token
    return None


def _is_loopback_host(host: str) -> bool:
    return host in {"127.0.0.1", "localhost", "::1"}


def _query_shape(query: dict[str, list[str]]) -> dict[str, list[int]]:
    return {
        key: [len(value) for value in values]
        for key, values in sorted(query.items())
    }


def _append_jsonl(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(payload, ensure_ascii=True) + "\n")


@dataclass(slots=True)
class AwarenessServerConfig:
    auth_token: str | None
    request_log_dir: Path


class AwarenessHTTPServer(ThreadingHTTPServer):
    atlas_config: AwarenessServerConfig


class AwarenessHandler(BaseHTTPRequestHandler):
    server_version = "ATLASAwareness/1.1"

    def _config(self) -> AwarenessServerConfig:
        return self.server.atlas_config  # type: ignore[attr-defined]

    def _request_id(self) -> str:
        return uuid.uuid4().hex

    def _client_token(self) -> str | None:
        authorization = self.headers.get("Authorization", "").strip()
        if authorization.startswith("Bearer "):
            token = authorization.removeprefix("Bearer ").strip()
            return token or None
        return None

    def _authenticate(self) -> tuple[bool, str, str | None]:
        auth_token = self._config().auth_token
        if not auth_token:
            return True, "not_required", None
        presented = self._client_token()
        if not presented:
            return False, "missing", None
        if presented != auth_token:
            return False, "invalid", _token_fingerprint(presented)
        return True, "ok", _token_fingerprint(presented)

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
            self.send_header("Cache-Control", "no-store")
            self.send_header("ETag", etag)
            self.send_header("X-ATLAS-Request-Id", request_id)
            if extra_headers:
                for key, value in extra_headers.items():
                    self.send_header(key, value)
            self.end_headers()
            return HTTPStatus.NOT_MODIFIED

        encoded = json.dumps(payload, indent=2).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(encoded)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-ATLAS-Request-Id", request_id)
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
                "auth_required": self._config().auth_token is not None,
                "auth_result": auth_result,
                "auth_principal": auth_principal,
                "etag": etag,
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

        try:
            if parsed.path == "/health":
                status = self._send_json(
                    {
                        "ok": True,
                        "service": "atlas-awareness",
                        "auth_required": self._config().auth_token is not None,
                    },
                    request_id=request_id,
                )
                return

            authenticated, auth_result, auth_principal = self._authenticate()
            if not authenticated:
                status = self._send_json(
                    {
                        "ok": False,
                        "error": "unauthorized",
                        "message": "A valid bearer token is required for the ATLAS Awareness API.",
                    },
                    request_id=request_id,
                    status=HTTPStatus.UNAUTHORIZED,
                    extra_headers={"WWW-Authenticate": 'Bearer realm="atlas-awareness"'},
                )
                return

            if parsed.path == "/atlas/status":
                payload = atlas_status(refresh=refresh)
                etag = str(payload.get("snapshot", {}).get("content_digest") or "")
                status = self._send_json(payload, request_id=request_id, etag=etag)
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
                status = self._send_json(payload, request_id=request_id, etag=etag)
                return

            if parsed.path == "/atlas/attention":
                payload = list_attention(
                    refresh=refresh,
                    severity=_first(query, "severity"),
                    query=_first(query, "query"),
                    limit=_first_int(query, "limit", 0) or None,
                )
                etag = str(payload.get("attention_content_digest") or "")
                status = self._send_json(payload, request_id=request_id, etag=etag)
                return

            if parsed.path == "/atlas/search":
                q = _first(query, "q")
                if q is None:
                    raise ValueError("Missing required query parameter: q")
                payload = search(q, refresh=refresh, limit=_first_int(query, "limit", 10))
                status = self._send_json(payload, request_id=request_id)
                return

            if parsed.path == "/atlas/knowledge/query":
                q = _first(query, "q")
                if q is None:
                    raise ValueError("Missing required query parameter: q")
                payload = query_knowledge(q, refresh=refresh, limit=_first_int(query, "limit", 5))
                status = self._send_json(payload, request_id=request_id)
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
                status = self._send_json(payload, request_id=request_id)
                return

            if parsed.path.startswith("/atlas/sessions/"):
                session_id = parsed.path.rsplit("/", 1)[-1].strip()
                if not session_id:
                    raise ValueError("Session path must end with a session id.")
                payload = fetch_session(session_id, refresh=refresh)
                status = self._send_json(payload, request_id=request_id)
                return

            status = self._send_json(
                {
                    "ok": False,
                    "error": "not_found",
                    "path": parsed.path,
                },
                request_id=request_id,
                status=HTTPStatus.NOT_FOUND,
            )
        except FileNotFoundError as exc:
            error = str(exc)
            status = self._send_json(
                {"ok": False, "error": "not_found", "message": error},
                request_id=request_id,
                status=HTTPStatus.NOT_FOUND,
            )
        except ValueError as exc:
            error = str(exc)
            status = self._send_json(
                {"ok": False, "error": "bad_request", "message": error},
                request_id=request_id,
                status=HTTPStatus.BAD_REQUEST,
            )
        except Exception as exc:  # pragma: no cover - defensive server path
            error = str(exc)
            status = self._send_json(
                {"ok": False, "error": "internal_error", "message": error},
                request_id=request_id,
                status=HTTPStatus.INTERNAL_SERVER_ERROR,
            )
        finally:
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
    parser.add_argument("--allow-unauthenticated", action="store_true")
    parser.add_argument(
        "--request-log-dir",
        default=str(ROOT / "runtime" / "atlas" / "awareness" / "requests"),
    )
    args = parser.parse_args(argv)

    auth_token = _load_auth_token(args)
    if auth_token is None and not args.allow_unauthenticated and not _is_loopback_host(args.host):
        parser.error(
            "Remote ATLAS Awareness API binds require --auth-token or --auth-token-file unless --allow-unauthenticated is set."
        )

    server = AwarenessHTTPServer((args.host, args.port), AwarenessHandler)
    server.atlas_config = AwarenessServerConfig(
        auth_token=auth_token,
        request_log_dir=Path(args.request_log_dir).resolve(),
    )
    print(
        json.dumps(
            {
                "host": args.host,
                "port": args.port,
                "service": "atlas-awareness",
                "auth_required": auth_token is not None,
                "request_log_dir": str(server.atlas_config.request_log_dir),
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
