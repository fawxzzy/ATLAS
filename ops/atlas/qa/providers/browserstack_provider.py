from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import tempfile
import urllib.parse
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[4]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def _required_env(provider_payload: dict[str, Any]) -> dict[str, str]:
    values: dict[str, str] = {}
    missing: list[str] = []
    for key in provider_payload.get("auth_env_vars", []):
        if not isinstance(key, str) or not key.strip():
            continue
        value = os.environ.get(key, "")
        if not value:
            missing.append(key)
        else:
            values[key] = value
    if missing:
        raise RuntimeError(f"BrowserStack provider is missing required environment variables: {', '.join(missing)}.")
    return values


def _redact_provider_output(text: str, secrets: dict[str, str]) -> str:
    redacted = text
    for value in secrets.values():
        if not value:
            continue
        redacted = redacted.replace(value, "[REDACTED]")
        redacted = redacted.replace(urllib.parse.quote(value, safe=""), "[REDACTED]")
    patterns = (
        (r'("browserstack\.username"\s*:\s*")[^"]+(")', r"\1[REDACTED]\2"),
        (r'("browserstack\.accessKey"\s*:\s*")[^"]+(")', r"\1[REDACTED]\2"),
        (r"(BROWSERSTACK_USERNAME\s*[=:]\s*)\S+", r"\1[REDACTED]"),
        (r"(BROWSERSTACK_ACCESS_KEY\s*[=:]\s*)\S+", r"\1[REDACTED]"),
    )
    for pattern, replacement in patterns:
        redacted = re.sub(pattern, replacement, redacted)
    return redacted


def capture_with_browserstack_provider(
    *,
    root: Path,
    provider_payload: dict[str, Any],
    provider_path: Path,
    config: dict[str, Any],
) -> dict[str, Any]:
    env_values = _required_env(provider_payload)
    payload = {
        "provider": provider_payload,
        "providerPath": str(provider_path.resolve()),
        "config": config,
    }
    with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False, encoding="utf-8") as handle:
        handle.write(json.dumps(payload, indent=2))
        temp_path = Path(handle.name)
    script_path = (root / "ops" / "atlas" / "qa" / "capture_browserstack.mjs").resolve()
    env = os.environ.copy()
    env.update(env_values)
    completed = subprocess.run(
        ["node", str(script_path), "--config", str(temp_path)],
        cwd=str(root),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
        env=env,
    )
    try:
        temp_path.unlink(missing_ok=True)
    except OSError:
        pass
    if completed.returncode != 0:
        detail = completed.stderr.strip() or completed.stdout.strip() or "capture_browserstack failed."
        raise RuntimeError(_redact_provider_output(detail, env_values))
    payload = json.loads(completed.stdout)
    if not isinstance(payload, dict):
        raise ValueError("capture_browserstack did not return a JSON object.")
    return payload
