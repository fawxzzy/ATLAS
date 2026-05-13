from __future__ import annotations

from pathlib import Path
from typing import Any

from ops.atlas.qa._common import load_provider_manifest
from ops.atlas.qa.providers.browserstack_provider import capture_with_browserstack_provider
from ops.atlas.qa.providers.mock_provider import capture_with_mock_provider


def load_provider_config(*, root: Path, provider_manifest_ref: str) -> tuple[dict[str, Any], Path]:
    return load_provider_manifest(root=root, provider_manifest_ref=provider_manifest_ref)


def capture_with_provider(*, root: Path, provider_manifest_ref: str, config: dict[str, Any]) -> dict[str, Any]:
    provider_payload, provider_path = load_provider_config(root=root, provider_manifest_ref=provider_manifest_ref)
    provider_id = str(provider_payload.get("provider_id") or "")
    if provider_id == "mock.physical-device":
        return capture_with_mock_provider(root=root, provider_payload=provider_payload, provider_path=provider_path, config=config)
    if provider_id == "browserstack.playwright":
        return capture_with_browserstack_provider(root=root, provider_payload=provider_payload, provider_path=provider_path, config=config)
    raise RuntimeError(f"Provider '{provider_id}' is not installed for ATLAS QA capture.")
