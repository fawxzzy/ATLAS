from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from ops._atlas import atlas_root
from ops.atlas.qa._common import resolve_ref
from ops.cortex._artifacts import read_json


def capture_with_playwright(*, root: Path, config: dict[str, Any]) -> dict[str, Any]:
    with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False, encoding="utf-8") as handle:
        handle.write(json.dumps(config, indent=2))
        temp_path = Path(handle.name)
    script_path = (root / "ops" / "atlas" / "qa" / "capture_playwright.mjs").resolve()
    completed = subprocess.run(
        ["node", str(script_path), "--config", str(temp_path)],
        cwd=str(root),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )
    try:
        temp_path.unlink(missing_ok=True)
    except OSError:
        pass
    if completed.returncode != 0:
        raise RuntimeError(completed.stderr.strip() or completed.stdout.strip() or "capture_playwright failed.")
    payload = json.loads(completed.stdout)
    if not isinstance(payload, dict):
        raise ValueError("capture_playwright did not return a JSON object.")
    return payload


def main(argv: list[str] | None = None) -> int:
    import argparse

    parser = argparse.ArgumentParser(description="Run a browser-backed ATLAS QA capture.")
    parser.add_argument("--root", type=Path, default=atlas_root())
    parser.add_argument("--config-file", type=Path, required=True)
    args = parser.parse_args(argv)

    base_root = args.root.resolve()
    config = read_json(resolve_ref(args.config_file.resolve(), root=base_root))
    result = capture_with_playwright(root=base_root, config=config)
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
