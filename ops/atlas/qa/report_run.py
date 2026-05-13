from __future__ import annotations

import argparse
import json
import sys
from html import escape
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from ops._atlas import atlas_relative, atlas_root
from ops.atlas.qa._common import default_run_root, display_promotion_status, load_json_object, utc_now
from ops.cortex._artifacts import write_json


def _rel(target: str | Path | None, *, base: Path, root: Path) -> str:
    if target is None:
        return ""
    path = Path(str(target))
    resolved = path if path.is_absolute() else (root / path).resolve()
    try:
        return resolved.relative_to(base).as_posix()
    except ValueError:
        return atlas_relative(resolved, root=root)


def report_run(*, root: Path | None = None, run_id: str, output_dir: Path | None = None) -> dict[str, Any]:
    base_root = (root or atlas_root()).resolve()
    run_root = (default_run_root(root=base_root) / run_id).resolve()
    result = load_json_object(run_root / "matrix.result.json")
    artifacts = load_json_object(run_root / "artifacts.manifest.json")
    evaluated = load_json_object(run_root / "evaluated.result.json")
    promotion = load_json_object(run_root / "promotion.record.json")
    test_evidence = load_json_object(run_root / "test-evidence.json") if (run_root / "test-evidence.json").exists() else {"receipts": [], "summary": {"status": "not_configured"}}
    report_root = output_dir.resolve() if isinstance(output_dir, Path) else run_root
    report_root.mkdir(parents=True, exist_ok=True)

    screenshots = [
        item for item in artifacts.get("artifacts", [])
        if isinstance(item, dict) and item.get("artifact_kind") == "screenshot"
    ]
    per_lens: list[dict[str, Any]] = []
    for lane in result.get("matrix", []):
        if not isinstance(lane, dict):
            continue
        lens_id = str(lane.get("lens_id") or "")
        lens_shots = [item for item in screenshots if item.get("lens_id") == lens_id]
        shot = lens_shots[0] if lens_shots else None
        per_lens.append(
            {
                "lens_id": lens_id,
                "status": str(lane.get("status") or ""),
                "proof_kind": str(lane.get("proof_kind") or ""),
                "evidence_kind": str(lane.get("evidence_kind") or ""),
                "screenshot_ref": str(shot.get("path_ref") or "") if isinstance(shot, dict) else "",
                "trace_ref": next((str(item.get("path_ref") or "") for item in artifacts.get("artifacts", []) if isinstance(item, dict) and item.get("lens_id") == lens_id and item.get("artifact_kind") == "trace"), ""),
                "console_ref": next((str(item.get("path_ref") or "") for item in artifacts.get("artifacts", []) if isinstance(item, dict) and item.get("lens_id") == lens_id and item.get("artifact_kind") == "console_log"), ""),
                "network_ref": next((str(item.get("path_ref") or "") for item in artifacts.get("artifacts", []) if isinstance(item, dict) and item.get("lens_id") == lens_id and item.get("artifact_kind") == "network_log"), ""),
            }
        )

    visual_diffs = list(evaluated.get("visual_diffs", []))
    evidence_profile = str(promotion.get("evidence_profile") or evaluated.get("summary", {}).get("evidence_profile") or "unknown")
    promotion_status = str(promotion.get("promotion_status") or "")
    promotion_display_status = display_promotion_status(
        promotion_status=promotion_status,
        evidence_profile=evidence_profile,
    )
    summary_payload = {
        "contract_version": "atlas.qa.report.v1",
        "generated_at": utc_now(),
        "run_id": run_id,
        "scenario_id": result.get("scenario_ref"),
        "adapter_id": result.get("adapter_id"),
        "repo_id": result.get("repo_id"),
        "git_sha": result.get("git_sha"),
        "promotion_status": promotion_status,
        "promotion_display_status": promotion_display_status,
        "evidence_profile": evidence_profile,
        "highest_satisfied_tier": promotion.get("highest_satisfied_tier"),
        "missing_evidence_tiers": promotion.get("missing_evidence_tiers", []),
        "manual_required_lanes": promotion.get("manual_required_lanes", []),
        "waived_lanes": promotion.get("waived_lanes", []),
        "waiver_refs": promotion.get("waiver_refs", []),
        "waiver_reasons": promotion.get("waiver_reasons", []),
        "visual_status": evaluated.get("summary", {}).get("visual_status"),
        "test_evidence_status": evaluated.get("summary", {}).get("test_evidence_status"),
        "receipt_origin": promotion.get("receipt_origin") if isinstance(promotion.get("receipt_origin"), dict) else {},
        "per_lens": per_lens,
        "visual_diffs": visual_diffs,
        "test_evidence": test_evidence.get("receipts", []),
        "findings": evaluated.get("findings", []),
    }

    md_lines = [
        f"# ATLAS QA Report: `{run_id}`",
        "",
        f"- Repo: `{result.get('repo_id')}`",
        f"- Adapter: `{result.get('adapter_id')}`",
        f"- Git SHA: `{result.get('git_sha')}`",
        f"- Promotion status: `{promotion_status}`",
        f"- Promotion display: `{promotion_display_status}`",
        f"- Evidence profile: `{evidence_profile}`",
        f"- Highest evidence tier: `{promotion.get('highest_satisfied_tier')}`",
        f"- Receipt origin: `{str((promotion.get('receipt_origin') or {}).get('origin_type') or 'unknown')}`",
        f"- Missing evidence tiers: `{', '.join(promotion.get('missing_evidence_tiers', [])) or 'none'}`",
        f"- Manual-required lanes: `{', '.join(promotion.get('manual_required_lanes', [])) or 'none'}`",
        f"- Waived lanes: `{', '.join(promotion.get('waived_lanes', [])) or 'none'}`",
        f"- Visual status: `{evaluated.get('summary', {}).get('visual_status', 'not_configured')}`",
        f"- Test evidence status: `{evaluated.get('summary', {}).get('test_evidence_status', 'not_configured')}`",
        "",
        "## Lenses",
        "",
        "| Lens | Status | Proof | Evidence | Screenshot | Trace | Console | Network |",
        "| --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    for lane in per_lens:
        md_lines.append(
            "| {lens} | {status} | {proof} | {evidence} | {screenshot} | {trace} | {console} | {network} |".format(
                lens=lane["lens_id"],
                status=lane["status"],
                proof=lane["proof_kind"],
                evidence=lane["evidence_kind"],
                screenshot=lane["screenshot_ref"] or "-",
                trace=lane["trace_ref"] or "-",
                console=lane["console_ref"] or "-",
                network=lane["network_ref"] or "-",
            )
        )
    if visual_diffs:
        md_lines.extend(["", "## Visual Diffs", "", "| Lens | Status | Changed Pixels | Threshold | Diff |", "| --- | --- | --- | --- | --- |"])
        for item in visual_diffs:
            md_lines.append(
                "| {lens} | {status} | {changed} | {threshold} | {diff} |".format(
                    lens=item.get("lens_id", ""),
                    status=item.get("status", ""),
                    changed=item.get("changed_pixels", "-"),
                    threshold=item.get("max_pixel_delta", "-"),
                    diff=item.get("diff_image_ref", "-"),
                )
            )
    if test_evidence.get("receipts"):
        md_lines.extend(["", "## Test Evidence", "", "| Evidence | Status | Runner | Kind | Exit Code | Stdout | Stderr |", "| --- | --- | --- | --- | --- | --- | --- |"])
        for item in test_evidence.get("receipts", []):
            if not isinstance(item, dict):
                continue
            md_lines.append(
                "| {evidence} | {status} | {runner} | {kind} | {exit_code} | {stdout} | {stderr} |".format(
                    evidence=item.get("evidence_id", ""),
                    status=item.get("status", ""),
                    runner=item.get("runner", ""),
                    kind=item.get("kind", ""),
                    exit_code=item.get("exit_code", "-"),
                    stdout=item.get("stdout_ref", "-"),
                    stderr=item.get("stderr_ref", "-"),
                )
            )
    if evaluated.get("findings"):
        md_lines.extend(["", "## Findings", ""])
        for item in evaluated.get("findings", []):
            md_lines.append(f"- [{item.get('severity')}] `{item.get('code')}`: {item.get('message')}")
    if promotion.get("waiver_refs"):
        md_lines.extend(["", "## Waivers", ""])
        for ref, reason in zip(promotion.get("waiver_refs", []), promotion.get("waiver_reasons", []), strict=False):
            md_lines.append(f"- `{ref}`: {reason or 'no reason recorded'}")
    markdown = "\n".join(md_lines) + "\n"

    html_lines = [
        "<!doctype html>",
        "<html><head><meta charset='utf-8'><title>ATLAS QA Report</title>",
        "<style>body{font-family:Segoe UI,Arial,sans-serif;margin:24px;background:#f6f7fb;color:#172033;}table{border-collapse:collapse;width:100%;margin:16px 0;background:#fff;}th,td{border:1px solid #d7dcea;padding:8px;text-align:left;vertical-align:top;}th{background:#eef2ff;}code{background:#edf1f7;padding:2px 4px;border-radius:4px;}img{max-width:320px;border:1px solid #d7dcea;background:#fff;}.card{background:#fff;border:1px solid #d7dcea;padding:16px;margin:16px 0;}</style>",
        "</head><body>",
        f"<h1>ATLAS QA Report: <code>{escape(run_id)}</code></h1>",
        "<div class='card'>",
        f"<p><strong>Repo:</strong> <code>{escape(str(result.get('repo_id') or ''))}</code><br>",
        f"<strong>Adapter:</strong> <code>{escape(str(result.get('adapter_id') or ''))}</code><br>",
        f"<strong>Git SHA:</strong> <code>{escape(str(result.get('git_sha') or ''))}</code><br>",
        f"<strong>Promotion status:</strong> <code>{escape(promotion_status)}</code><br>",
        f"<strong>Promotion display:</strong> <code>{escape(promotion_display_status)}</code><br>",
        f"<strong>Evidence profile:</strong> <code>{escape(evidence_profile)}</code><br>",
        f"<strong>Highest evidence tier:</strong> <code>{escape(str(promotion.get('highest_satisfied_tier') or ''))}</code><br>",
        f"<strong>Receipt origin:</strong> <code>{escape(str((promotion.get('receipt_origin') or {}).get('origin_type') or 'unknown'))}</code><br>",
        f"<strong>Waived lanes:</strong> <code>{escape(', '.join(promotion.get('waived_lanes', [])) or 'none')}</code><br>",
        f"<strong>Visual status:</strong> <code>{escape(str(evaluated.get('summary', {}).get('visual_status') or 'not_configured'))}</code></p>",
        f"<p><strong>Test evidence status:</strong> <code>{escape(str(evaluated.get('summary', {}).get('test_evidence_status') or 'not_configured'))}</code></p>",
        "</div>",
        "<h2>Lenses</h2><table><thead><tr><th>Lens</th><th>Status</th><th>Evidence</th><th>Screenshot</th><th>Artifacts</th></tr></thead><tbody>",
    ]
    for lane in per_lens:
        screenshot_html = "-"
        if lane["screenshot_ref"]:
            screenshot_html = f"<div><code>{escape(lane['screenshot_ref'])}</code><br><img src='{escape(_rel(lane['screenshot_ref'], base=report_root, root=base_root))}' alt='{escape(lane['lens_id'])}'></div>"
        artifact_html = "<br>".join(
            escape(value) for value in [lane["trace_ref"], lane["console_ref"], lane["network_ref"]] if value
        ) or "-"
        html_lines.append(
            f"<tr><td><code>{escape(lane['lens_id'])}</code></td><td>{escape(lane['status'])}</td><td>{escape(lane['evidence_kind'])}</td><td>{screenshot_html}</td><td>{artifact_html}</td></tr>"
        )
    html_lines.append("</tbody></table>")
    if visual_diffs:
        html_lines.append("<h2>Visual Diffs</h2><table><thead><tr><th>Lens</th><th>Status</th><th>Changed Pixels</th><th>Threshold</th><th>Diff</th></tr></thead><tbody>")
        for item in visual_diffs:
            diff_html = "-"
            diff_ref = str(item.get("diff_image_ref") or "")
            if diff_ref:
                diff_html = f"<div><code>{escape(diff_ref)}</code><br><img src='{escape(_rel(diff_ref, base=report_root, root=base_root))}' alt='{escape(str(item.get('lens_id') or ''))} diff'></div>"
            html_lines.append(
                f"<tr><td><code>{escape(str(item.get('lens_id') or ''))}</code></td><td>{escape(str(item.get('status') or ''))}</td><td>{escape(str(item.get('changed_pixels') or '-'))}</td><td>{escape(str(item.get('max_pixel_delta') or '-'))}</td><td>{diff_html}</td></tr>"
            )
        html_lines.append("</tbody></table>")
    if test_evidence.get("receipts"):
        html_lines.append("<h2>Test Evidence</h2><table><thead><tr><th>Evidence</th><th>Status</th><th>Runner</th><th>Kind</th><th>Exit Code</th><th>Stdout</th><th>Stderr</th></tr></thead><tbody>")
        for item in test_evidence.get("receipts", []):
            if not isinstance(item, dict):
                continue
            html_lines.append(
                f"<tr><td><code>{escape(str(item.get('evidence_id') or ''))}</code></td><td>{escape(str(item.get('status') or ''))}</td><td>{escape(str(item.get('runner') or ''))}</td><td>{escape(str(item.get('kind') or ''))}</td><td>{escape(str(item.get('exit_code') or '-'))}</td><td>{escape(str(item.get('stdout_ref') or '-'))}</td><td>{escape(str(item.get('stderr_ref') or '-'))}</td></tr>"
            )
        html_lines.append("</tbody></table>")
    if evaluated.get("findings"):
        html_lines.append("<h2>Findings</h2><div class='card'><ul>")
        for item in evaluated.get("findings", []):
            html_lines.append(
                f"<li><strong>{escape(str(item.get('severity') or ''))}</strong> <code>{escape(str(item.get('code') or ''))}</code>: {escape(str(item.get('message') or ''))}</li>"
            )
        html_lines.append("</ul></div>")
    if promotion.get("waiver_refs"):
        html_lines.append("<h2>Waivers</h2><div class='card'><ul>")
        for ref, reason in zip(promotion.get("waiver_refs", []), promotion.get("waiver_reasons", []), strict=False):
            html_lines.append(f"<li><code>{escape(str(ref))}</code>: {escape(str(reason or 'no reason recorded'))}</li>")
        html_lines.append("</ul></div>")
    html_lines.append("</body></html>")
    html = "\n".join(html_lines) + "\n"

    md_path = report_root / "report.md"
    html_path = report_root / "report.html"
    json_path = report_root / "report.summary.json"
    md_path.write_text(markdown, encoding="utf-8")
    html_path.write_text(html, encoding="utf-8")
    write_json(json_path, summary_payload)
    return {
        "runner_version": "atlas.qa.report-run.v1",
        "generated_at": utc_now(),
        "run_id": run_id,
        "report_md_ref": atlas_relative(md_path, root=base_root),
        "report_html_ref": atlas_relative(html_path, root=base_root),
        "report_summary_ref": atlas_relative(json_path, root=base_root),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Render operator-facing QA evidence reports for an ATLAS QA run.")
    parser.add_argument("--root", type=Path, default=atlas_root())
    parser.add_argument("--run", required=True)
    parser.add_argument("--output-dir", type=Path)
    args = parser.parse_args(argv)
    report = report_run(
        root=args.root.resolve(),
        run_id=args.run,
        output_dir=args.output_dir.resolve() if isinstance(args.output_dir, Path) else None,
    )
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
