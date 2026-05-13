from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from PIL import Image

from ops._atlas import atlas_relative
from ops.atlas.qa._common import utc_now
from ops.cortex._artifacts import write_json


def _png(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    Image.new("RGBA", (32, 32), (0, 160, 220, 255)).save(path, format="PNG")


def capture_with_mock_provider(
    *,
    root: Path,
    provider_payload: dict[str, Any],
    provider_path: Path,
    config: dict[str, Any],
) -> dict[str, Any]:
    output_dir = Path(str(config["outputDir"])).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    screenshot_path = output_dir / "screenshot.png"
    console_path = output_dir / "console.log"
    network_path = output_dir / "network.json"
    _png(screenshot_path)
    console_path.write_text("mock provider console log\n", encoding="utf-8")
    network_path.write_text(json.dumps({"requests": []}, indent=2) + "\n", encoding="utf-8")
    metadata = {
        "contract_version": "atlas.qa.capture_receipt.v1",
        "captured_at": utc_now(),
        "capture_backend": "mock-provider",
        "capture_method": "provider_automation",
        "provider_id": str(provider_payload["provider_id"]),
        "provider_run_id": f"mock-{config['runId']}-{config['lensId']}",
        "device_model": str(config.get("deviceModel") or "Mock Phone"),
        "os_name": str(config.get("osName") or "MockOS"),
        "os_version": str(config.get("osVersion") or "1.0"),
        "browser_name": str(config.get("browserName") or config.get("browserEngine") or "browser"),
        "browser_version": str(config.get("browserVersion") or "1.0"),
        "run_id": str(config["runId"]),
        "scenario_id": str(config["scenarioId"]),
        "adapter_id": str(config["adapterId"]),
        "repo_id": str(config["repoId"]),
        "git_sha": str(config["gitSha"]),
        "lens_id": str(config["lensId"]),
        "source_url": str(config["sourceUrl"]),
        "provider_manifest_ref": atlas_relative(provider_path.resolve(), root=root),
    }
    metadata_path = output_dir / "capture.metadata.json"
    write_json(metadata_path, metadata)
    return {
        "provider_id": str(provider_payload["provider_id"]),
        "provider_run_id": str(metadata["provider_run_id"]),
        "metadata_path": str(metadata_path),
        "outputs": {
            "screenshot": str(screenshot_path),
            "console_log": str(console_path),
            "network_log": str(network_path),
        },
    }
