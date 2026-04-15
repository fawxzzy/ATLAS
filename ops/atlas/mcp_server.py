from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from ops.atlas.load_tool_registry import load_awareness_connector_toolset

SERVER_NAME = "atlas-awareness-mcp"
SERVER_VERSION = "0.2.0"
MCP_PROTOCOL_VERSION = "2025-11-05"


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _append_jsonl(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(payload, ensure_ascii=True) + "\n")


def _token_fingerprint(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()[:16]


def _is_loopback_host(host: str) -> bool:
    return host in {"127.0.0.1", "localhost", "::1"}


def _load_token(
    *,
    direct_value: str | None,
    file_value: str | None,
    env_key: str,
    env_file_key: str,
) -> str | None:
    if isinstance(direct_value, str) and direct_value.strip():
        return direct_value.strip()
    env_token = os.environ.get(env_key, "").strip()
    if env_token:
        return env_token
    token_file = file_value or os.environ.get(env_file_key)
    if token_file:
        token_path = Path(str(token_file)).expanduser().resolve()
        token = token_path.read_text(encoding="utf-8").strip()
        if token:
            return token
    return None


@dataclass(slots=True)
class AwarenessApiClient:
    base_url: str
    auth_token: str | None = None

    def request_json(self, path: str, *, query: dict[str, Any] | None = None) -> dict[str, Any]:
        url = self.base_url.rstrip("/") + path
        if query:
            encoded_query = urllib.parse.urlencode(
                {
                    key: value
                    for key, value in query.items()
                    if value is not None
                }
            )
            if encoded_query:
                url = f"{url}?{encoded_query}"
        headers = {"Accept": "application/json"}
        if self.auth_token:
            headers["Authorization"] = f"Bearer {self.auth_token}"
        request = urllib.request.Request(url, headers=headers, method="GET")
        try:
            with urllib.request.urlopen(request, timeout=30) as response:
                body = response.read().decode("utf-8")
        except urllib.error.HTTPError as exc:
            body = exc.read().decode("utf-8", errors="replace")
            try:
                payload = json.loads(body)
            except json.JSONDecodeError:
                payload = {"error": "remote_http_error", "message": body}
            raise AwarenessApiError(status=exc.code, payload=payload) from exc
        except urllib.error.URLError as exc:
            raise RuntimeError(f"Unable to reach Awareness API at {url}: {exc.reason}") from exc
        payload = json.loads(body)
        if not isinstance(payload, dict):
            raise ValueError("Awareness API response must be a JSON object.")
        return payload


@dataclass(slots=True)
class AwarenessApiError(Exception):
    status: int
    payload: dict[str, Any]

    def __str__(self) -> str:
        message = self.payload.get("message")
        if isinstance(message, str) and message.strip():
            return message
        error = self.payload.get("error")
        if isinstance(error, str) and error.strip():
            return error
        return f"Awareness API returned HTTP {self.status}."


@dataclass(slots=True)
class MCPServerConfig:
    auth_token: str | None
    api_client: AwarenessApiClient
    tool_defs: list[dict[str, Any]]
    request_log_dir: Path
    toolset_digest: str | None
    registry_digest: str | None


class MCPHTTPServer(ThreadingHTTPServer):
    mcp_config: MCPServerConfig


def _content_text(payload: dict[str, Any]) -> dict[str, Any]:
    return {
        "content": [
            {
                "type": "text",
                "text": json.dumps(payload, indent=2, ensure_ascii=True),
            }
        ]
    }


def _tool_defs() -> list[dict[str, Any]]:
    toolset = load_awareness_connector_toolset(root=ROOT)
    return [
        {
            "name": tool["name"],
            "description": tool["description"],
            "inputSchema": tool["inputSchema"],
        }
        for tool in toolset["tools"]
    ]


def call_tool(name: str, arguments: dict[str, Any] | None, *, client: AwarenessApiClient) -> dict[str, Any]:
    args = arguments or {}
    if name == "search":
        return _content_text(
            client.request_json(
                "/atlas/search",
                query={
                    "q": str(args.get("query", "")),
                    "limit": max(int(args.get("limit", 10)), 1),
                },
            )
        )
    if name == "fetch":
        return _content_text(
            client.request_json(
                "/atlas/artifacts/fetch",
                query={"id": str(args.get("id", ""))},
            )
        )
    if name == "atlas_status":
        return _content_text(client.request_json("/atlas/status"))
    if name == "atlas_session_fetch":
        session_id = urllib.parse.quote(str(args.get("session_id", "")).strip(), safe="")
        return _content_text(client.request_json(f"/atlas/sessions/{session_id}"))
    if name == "atlas_query_knowledge":
        return _content_text(
            client.request_json(
                "/atlas/knowledge/query",
                query={
                    "q": str(args.get("query", "")),
                    "limit": max(int(args.get("limit", 5)), 1),
                },
            )
        )
    raise ValueError(f"Unsupported tool: {name}")


def _response(message_id: Any, result: dict[str, Any]) -> dict[str, Any]:
    return {"jsonrpc": "2.0", "id": message_id, "result": result}


def _error(message_id: Any, code: int, message: str) -> dict[str, Any]:
    return {
        "jsonrpc": "2.0",
        "id": message_id,
        "error": {
            "code": code,
            "message": message,
        },
    }


def _handle_message(
    payload: dict[str, Any],
    *,
    client: AwarenessApiClient,
    tool_defs: list[dict[str, Any]],
) -> dict[str, Any] | None:
    message_id = payload.get("id")
    method = payload.get("method")
    params = payload.get("params") if isinstance(payload.get("params"), dict) else {}

    if method == "initialize":
        return _response(
            message_id,
            {
                "protocolVersion": MCP_PROTOCOL_VERSION,
                "serverInfo": {"name": SERVER_NAME, "version": SERVER_VERSION},
                "capabilities": {
                    "tools": {"listChanged": False},
                },
            },
        )
    if method == "notifications/initialized":
        return None
    if method == "ping":
        return _response(message_id, {})
    if method == "tools/list":
        return _response(message_id, {"tools": tool_defs})
    if method == "tools/call":
        name = str(params.get("name", "")).strip()
        arguments = params.get("arguments") if isinstance(params.get("arguments"), dict) else {}
        try:
            return _response(message_id, call_tool(name, arguments, client=client))
        except AwarenessApiError as exc:
            if exc.status == HTTPStatus.NOT_FOUND:
                return _error(message_id, -32001, str(exc))
            if exc.status == HTTPStatus.UNAUTHORIZED:
                return _error(message_id, -32002, str(exc))
            if exc.status == HTTPStatus.BAD_REQUEST:
                return _error(message_id, -32602, str(exc))
            return _error(message_id, -32603, str(exc))
        except ValueError as exc:
            return _error(message_id, -32602, str(exc))
        except Exception as exc:  # pragma: no cover - defensive protocol path
            return _error(message_id, -32603, str(exc))
    if method is None and "id" not in payload:
        return None
    return _error(message_id, -32601, f"Method not found: {method}")


def run_stdio(*, client: AwarenessApiClient, tool_defs: list[dict[str, Any]]) -> int:
    for raw_line in sys.stdin:
        line = raw_line.strip()
        if not line:
            continue
        try:
            payload = json.loads(line)
        except json.JSONDecodeError as exc:
            response = _error(None, -32700, f"Parse error: {exc}")
        else:
            if not isinstance(payload, dict):
                response = _error(None, -32600, "Invalid request object.")
            else:
                response = _handle_message(payload, client=client, tool_defs=tool_defs)
        if response is not None:
            sys.stdout.write(json.dumps(response, ensure_ascii=True) + "\n")
            sys.stdout.flush()
    return 0


class MCPHandler(BaseHTTPRequestHandler):
    server_version = "ATLASAwarenessMCP/1.0"

    def _config(self) -> MCPServerConfig:
        return self.server.mcp_config  # type: ignore[attr-defined]

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
        extra_headers: dict[str, str] | None = None,
    ) -> int:
        encoded = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(encoded)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-ATLAS-Request-Id", request_id)
        if extra_headers:
            for key, value in extra_headers.items():
                self.send_header(key, value)
        self.end_headers()
        self.wfile.write(encoded)
        return status

    def _send_empty(self, *, request_id: str, status: int = HTTPStatus.NO_CONTENT) -> int:
        self.send_response(status)
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-ATLAS-Request-Id", request_id)
        self.end_headers()
        return status

    def _log_request(
        self,
        *,
        request_id: str,
        route: str,
        rpc_method: str | None,
        tool_name: str | None,
        status: int,
        duration_ms: float,
        auth_result: str,
        auth_principal: str | None,
        error: str | None,
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
                "rpc_method": rpc_method,
                "tool_name": tool_name,
                "status": int(status),
                "duration_ms": round(duration_ms, 3),
                "auth_required": self._config().auth_token is not None,
                "auth_result": auth_result,
                "auth_principal": auth_principal,
                "awareness_base_url": self._config().api_client.base_url,
                "toolset_digest": self._config().toolset_digest,
                "registry_digest": self._config().registry_digest,
                "error": error,
            },
        )

    def do_GET(self) -> None:  # noqa: N802
        request_id = self._request_id()
        started = time.perf_counter()
        status = HTTPStatus.OK
        error: str | None = None
        try:
            if self.path == "/health":
                status = self._send_json(
                    {
                        "ok": True,
                        "service": SERVER_NAME,
                        "auth_required": self._config().auth_token is not None,
                        "awareness_base_url": self._config().api_client.base_url,
                        "tool_names": [tool["name"] for tool in self._config().tool_defs],
                        "toolset_digest": self._config().toolset_digest,
                        "registry_digest": self._config().registry_digest,
                    },
                    request_id=request_id,
                )
                return
            status = self._send_json(
                {"ok": False, "error": "not_found", "path": self.path},
                request_id=request_id,
                status=HTTPStatus.NOT_FOUND,
            )
        finally:
            self._log_request(
                request_id=request_id,
                route=self.path,
                rpc_method=None,
                tool_name=None,
                status=status,
                duration_ms=(time.perf_counter() - started) * 1000,
                auth_result="not_checked",
                auth_principal=None,
                error=error,
            )

    def do_POST(self) -> None:  # noqa: N802
        started = time.perf_counter()
        request_id = self._request_id()
        route = self.path
        status = HTTPStatus.OK
        rpc_method: str | None = None
        tool_name: str | None = None
        auth_result = "not_checked"
        auth_principal: str | None = None
        error: str | None = None

        try:
            if self.path != "/mcp":
                status = self._send_json(
                    {"ok": False, "error": "not_found", "path": self.path},
                    request_id=request_id,
                    status=HTTPStatus.NOT_FOUND,
                )
                return

            authenticated, auth_result, auth_principal = self._authenticate()
            if not authenticated:
                status = self._send_json(
                    {
                        "ok": False,
                        "error": "unauthorized",
                        "message": "A valid bearer token is required for the ATLAS MCP bridge.",
                    },
                    request_id=request_id,
                    status=HTTPStatus.UNAUTHORIZED,
                    extra_headers={"WWW-Authenticate": 'Bearer realm="atlas-awareness-mcp"'},
                )
                return

            content_length = int(self.headers.get("Content-Length", "0") or "0")
            raw_body = self.rfile.read(content_length).decode("utf-8")
            payload = json.loads(raw_body)
            if not isinstance(payload, dict):
                raise ValueError("Invalid request object.")

            rpc_method = str(payload.get("method")) if payload.get("method") is not None else None
            params = payload.get("params") if isinstance(payload.get("params"), dict) else {}
            tool_name = str(params.get("name")) if rpc_method == "tools/call" and params.get("name") is not None else None

            response = _handle_message(
                payload,
                client=self._config().api_client,
                tool_defs=self._config().tool_defs,
            )
            if response is None:
                status = self._send_empty(request_id=request_id)
            else:
                status = self._send_json(response, request_id=request_id)
        except json.JSONDecodeError as exc:
            error = str(exc)
            status = self._send_json(
                _error(None, -32700, f"Parse error: {exc}"),
                request_id=request_id,
                status=HTTPStatus.BAD_REQUEST,
            )
        except ValueError as exc:
            error = str(exc)
            status = self._send_json(
                _error(None, -32600, str(exc)),
                request_id=request_id,
                status=HTTPStatus.BAD_REQUEST,
            )
        except Exception as exc:  # pragma: no cover - defensive server path
            error = str(exc)
            status = self._send_json(
                _error(None, -32603, str(exc)),
                request_id=request_id,
                status=HTTPStatus.INTERNAL_SERVER_ERROR,
            )
        finally:
            self._log_request(
                request_id=request_id,
                route=route,
                rpc_method=rpc_method,
                tool_name=tool_name,
                status=status,
                duration_ms=(time.perf_counter() - started) * 1000,
                auth_result=auth_result,
                auth_principal=auth_principal,
                error=error,
            )

    def log_message(self, format: str, *args: object) -> None:  # noqa: A003
        return


def serve_http(
    *,
    host: str,
    port: int,
    server_auth_token: str | None,
    request_log_dir: Path,
    client: AwarenessApiClient,
    tool_defs: list[dict[str, Any]],
    toolset_digest: str | None,
    registry_digest: str | None,
) -> int:
    server = MCPHTTPServer((host, port), MCPHandler)
    server.mcp_config = MCPServerConfig(
        auth_token=server_auth_token,
        api_client=client,
        tool_defs=tool_defs,
        request_log_dir=request_log_dir,
        toolset_digest=toolset_digest,
        registry_digest=registry_digest,
    )
    print(
        json.dumps(
            {
                "host": host,
                "port": port,
                "service": SERVER_NAME,
                "auth_required": server_auth_token is not None,
                "awareness_base_url": client.base_url,
                "request_log_dir": str(request_log_dir),
                "toolset_digest": toolset_digest,
                "registry_digest": registry_digest,
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


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run the ATLAS Awareness MCP bridge.")
    parser.add_argument("--awareness-url", default=os.environ.get("ATLAS_AWARENESS_URL", "http://127.0.0.1:8765"))
    parser.add_argument("--awareness-auth-token")
    parser.add_argument("--awareness-auth-token-file")
    parser.add_argument("--call-tool")
    parser.add_argument("--args-json")
    parser.add_argument("--serve-http", action="store_true")
    parser.add_argument("--host", default=os.environ.get("ATLAS_MCP_HOST", "127.0.0.1"))
    parser.add_argument("--port", type=int, default=int(os.environ.get("ATLAS_MCP_PORT", "8766")))
    parser.add_argument("--server-auth-token")
    parser.add_argument("--server-auth-token-file")
    parser.add_argument("--allow-unauthenticated", action="store_true")
    parser.add_argument(
        "--request-log-dir",
        default=str(ROOT / "runtime" / "atlas" / "mcp" / "requests"),
    )
    args = parser.parse_args(argv)

    awareness_auth_token = _load_token(
        direct_value=args.awareness_auth_token,
        file_value=args.awareness_auth_token_file,
        env_key="ATLAS_AWARENESS_TOKEN",
        env_file_key="ATLAS_AWARENESS_TOKEN_FILE",
    )
    client = AwarenessApiClient(
        base_url=str(args.awareness_url).rstrip("/"),
        auth_token=awareness_auth_token,
    )
    toolset = load_awareness_connector_toolset(root=ROOT)
    tool_defs = [
        {
            "name": tool["name"],
            "description": tool["description"],
            "inputSchema": tool["inputSchema"],
        }
        for tool in toolset["tools"]
    ]

    if args.call_tool:
        payload = json.loads(args.args_json) if args.args_json else {}
        result = call_tool(args.call_tool, payload if isinstance(payload, dict) else {}, client=client)
        print(json.dumps(result, indent=2))
        return 0

    if args.serve_http:
        server_auth_token = _load_token(
            direct_value=args.server_auth_token,
            file_value=args.server_auth_token_file,
            env_key="ATLAS_MCP_TOKEN",
            env_file_key="ATLAS_MCP_TOKEN_FILE",
        )
        if server_auth_token is None and not args.allow_unauthenticated and not _is_loopback_host(args.host):
            parser.error(
                "Remote MCP binds require --server-auth-token or --server-auth-token-file unless --allow-unauthenticated is set."
            )
        return serve_http(
            host=args.host,
            port=args.port,
            server_auth_token=server_auth_token,
            request_log_dir=Path(args.request_log_dir).resolve(),
            client=client,
            tool_defs=tool_defs,
            toolset_digest=toolset.get("toolset_digest"),
            registry_digest=toolset.get("registry_digest"),
        )

    return run_stdio(client=client, tool_defs=tool_defs)


if __name__ == "__main__":
    raise SystemExit(main())
