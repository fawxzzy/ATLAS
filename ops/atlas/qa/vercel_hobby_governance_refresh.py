from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from ops._atlas import atlas_relative, atlas_root
from ops.atlas.vercel_hobby_decision_checkpoint import build_checkpoint, render_markdown as render_decision_markdown
from ops.atlas.vercel_hobby_guardrail_report import build_report, render_markdown as render_guardrail_markdown
from ops.cortex._artifacts import write_json


def _seed_dir(root: Path) -> Path:
    return root / "data" / "atlas" / "qa" / "vercel-hobby-cost-governance"


def _receipt_dir(root: Path) -> Path:
    return root / "runtime" / "receipts" / "vercel-hobby-cost-governance"


def refresh_vercel_hobby_governance(
    *,
    root: Path | None = None,
    repo_id: str = "fitness",
    repo_root_override: Path | None = None,
) -> dict[str, object]:
    base_root = (root or atlas_root()).resolve()
    seed_dir = _seed_dir(base_root)
    receipt_dir = _receipt_dir(base_root)
    receipt_dir.mkdir(parents=True, exist_ok=True)

    copied_refs: list[str] = []
    for seed in sorted(seed_dir.glob(f"{repo_id}-hobby-guardrail.????-??-??.*")):
        if seed.suffix not in {".json", ".md"}:
            continue
        target = receipt_dir / seed.name
        shutil.copyfile(seed, target)
        copied_refs.append(atlas_relative(target, root=base_root))

    if not any(ref.endswith(".json") for ref in copied_refs):
        raise FileNotFoundError(
            f"No preserved Vercel Hobby guardrail snapshots found for repo '{repo_id}' in {atlas_relative(seed_dir, root=base_root)}"
        )

    guardrail = build_report(root=base_root, repo_id=repo_id, repo_root_override=repo_root_override)
    latest_json = receipt_dir / f"{repo_id}-hobby-guardrail.latest.json"
    latest_md = receipt_dir / f"{repo_id}-hobby-guardrail.latest.md"
    write_json(latest_json, guardrail)
    latest_md.write_text(render_guardrail_markdown(guardrail), encoding="utf-8")

    decision = build_checkpoint(root=base_root, repo_id=repo_id)
    decision_json = receipt_dir / f"{repo_id}-hobby-decision.latest.json"
    decision_md = receipt_dir / f"{repo_id}-hobby-decision.latest.md"
    write_json(decision_json, decision)
    decision_md.write_text(render_decision_markdown(decision), encoding="utf-8")

    return {
        "contract_version": "atlas.vercel_hobby_governance_refresh.v1",
        "repo_id": repo_id,
        "preserved_guardrail_refs": copied_refs,
        "latest_guardrail_ref": atlas_relative(latest_json, root=base_root),
        "latest_guardrail_md_ref": atlas_relative(latest_md, root=base_root),
        "decision_ref": atlas_relative(decision_json, root=base_root),
        "decision_md_ref": atlas_relative(decision_md, root=base_root),
        "decision_status": decision.get("checkpoint_status"),
        "decision": decision.get("decision"),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Refresh no-secret Vercel Hobby governance receipts for release readiness.")
    parser.add_argument("--root", type=Path, default=atlas_root())
    parser.add_argument("--repo-id", default="fitness")
    parser.add_argument("--repo-path", type=Path, help="Optional repo root override for exact-SHA local verification")
    args = parser.parse_args(argv)
    result = refresh_vercel_hobby_governance(
        root=args.root.resolve(),
        repo_id=args.repo_id,
        repo_root_override=args.repo_path.resolve() if isinstance(args.repo_path, Path) else None,
    )
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
