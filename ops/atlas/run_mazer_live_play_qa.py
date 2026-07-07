"""Run the mazer live-play QA harness from ATLAS.

This is intentionally a thin stack-level wrapper. The game-specific solver and
control-driving logic lives in repos/mazer/scripts/analysis/live-play-qa.mjs.
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
from pathlib import Path
from typing import Any


DEFAULT_LABEL = "atlas-live-play-qa"


def atlas_relative(path: Path, *, root: Path) -> str:
    try:
        return path.resolve().relative_to(root.resolve()).as_posix()
    except ValueError:
        return str(path)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run mazer's live play QA harness and copy the latest receipt into ATLAS runtime.")
    parser.add_argument("--root", default=".", help="ATLAS root. Defaults to current directory.")
    parser.add_argument("--label", default=DEFAULT_LABEL, help="QA run label.")
    parser.add_argument("--skip-build", action="store_true", help="Reuse existing mazer dist output.")
    parser.add_argument("--headless", default="true", choices=["true", "false"], help="Browser headless mode passed to mazer.")
    parser.add_argument("--movement-speed", default="0.42", help="Temporary QA browser movement speed preference.")
    parser.add_argument("--move-cap", default="320", help="Maximum moves before declaring the route capped.")
    parser.add_argument("--route", default=None, help="Optional mazer route override.")
    return parser.parse_args(argv)


def run(args: argparse.Namespace) -> dict[str, Any]:
    root = Path(args.root).resolve()
    mazer_root = root / "repos" / "mazer"
    if not mazer_root.exists():
        raise SystemExit(f"mazer repo not found at {mazer_root}")

    runtime_dir = root / "runtime" / "receipts" / "mazer-live-play-qa"
    runtime_dir.mkdir(parents=True, exist_ok=True)
    output_root = root / "tmp" / "captures" / "mazer-live-play-qa"

    command = [
        "npm",
        "run",
        "live:play-qa",
        "--",
        "--label",
        args.label,
        "--output-root",
        str(output_root),
        "--headless",
        args.headless,
        "--movement-speed",
        args.movement_speed,
        "--move-cap",
        args.move_cap,
    ]
    if args.skip_build:
        command.append("--skip-build")
    if args.route:
        command.extend(["--route", args.route])

    if os.name == "nt":
        command[0] = "npm.cmd"

    completed = subprocess.run(
        command,
        cwd=mazer_root,
        check=False,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )
    print(completed.stdout, end="")
    if completed.returncode != 0:
        raise SystemExit(completed.returncode)

    latest_summary = output_root / "latest.summary.json"
    if not latest_summary.exists():
        raise SystemExit(f"mazer live play QA did not write {latest_summary}")

    latest_receipt = runtime_dir / "latest.summary.json"
    shutil.copyfile(latest_summary, latest_receipt)
    summary = json.loads(latest_receipt.read_text(encoding="utf-8"))
    atlas_receipt = {
        "schema": "atlas.mazer-live-play-qa.receipt.v1",
        "source_summary_ref": atlas_relative(latest_summary, root=root),
        "latest_receipt_ref": atlas_relative(latest_receipt, root=root),
        "pass": bool(summary.get("result", {}).get("pass")),
        "seed": summary.get("route", {}).get("seed"),
        "seed_source": summary.get("route", {}).get("seedSource"),
        "executed_move_count": summary.get("result", {}).get("executedMoveCount"),
        "estimated_fps": summary.get("performance", {}).get("estimatedFps"),
    }
    atlas_receipt_path = runtime_dir / "latest.atlas-receipt.json"
    atlas_receipt_path.write_text(f"{json.dumps(atlas_receipt, indent=2)}\n", encoding="utf-8")
    print(json.dumps(atlas_receipt, indent=2))
    return atlas_receipt


def main(argv: list[str] | None = None) -> int:
    receipt = run(parse_args(argv))
    return 0 if receipt.get("pass") else 1


if __name__ == "__main__":
    raise SystemExit(main())
