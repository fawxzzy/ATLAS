from __future__ import annotations

import argparse
import hashlib
import os
from pathlib import Path
from typing import Any


def token_fingerprint(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()[:16]


def is_loopback_host(host: str) -> bool:
    return host in {"127.0.0.1", "localhost", "::1"}


def load_optional_token(
    *,
    direct_value: str | None,
    file_value: str | None,
    env_key: str | None = None,
    env_file_key: str | None = None,
) -> str | None:
    if isinstance(direct_value, str) and direct_value.strip():
        return direct_value.strip()
    if isinstance(env_key, str) and env_key.strip():
        env_token = os.environ.get(env_key, "").strip()
        if env_token:
            return env_token
    token_file = file_value
    if not token_file and isinstance(env_file_key, str) and env_file_key.strip():
        token_file = os.environ.get(env_file_key)
    if token_file:
        token_path = Path(str(token_file)).expanduser().resolve()
        token = token_path.read_text(encoding="utf-8").strip()
        if token:
            return token
    return None


def load_auth_tokens(
    *,
    specs: list[tuple[str | None, str | None, str | None, str | None]],
) -> list[str]:
    unique: list[str] = []
    seen: set[str] = set()
    for direct_value, file_value, env_key, env_file_key in specs:
        token = load_optional_token(
            direct_value=direct_value,
            file_value=file_value,
            env_key=env_key,
            env_file_key=env_file_key,
        )
        if not isinstance(token, str) or not token.strip() or token in seen:
            continue
        seen.add(token)
        unique.append(token)
    return unique


def client_bearer_token(headers: Any) -> str | None:
    authorization = str(headers.get("Authorization", "")).strip()
    if authorization.startswith("Bearer "):
        token = authorization.removeprefix("Bearer ").strip()
        return token or None
    return None


def authenticate_bearer(headers: Any, auth_tokens: list[str]) -> tuple[bool, str, str | None]:
    if not auth_tokens:
        return True, "not_required", None
    presented = client_bearer_token(headers)
    if not presented:
        return False, "missing", None
    if presented not in auth_tokens:
        return False, "invalid", token_fingerprint(presented)
    return True, "ok", token_fingerprint(presented)


def enforce_remote_bind_policy(
    *,
    parser: argparse.ArgumentParser,
    host: str,
    auth_tokens: list[str],
    allow_unauthenticated: bool,
    error_message: str,
) -> None:
    if auth_tokens or allow_unauthenticated or is_loopback_host(host):
        return
    parser.error(error_message)
