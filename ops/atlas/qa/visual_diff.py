from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from PIL import Image, ImageChops, ImageDraw

from ops._atlas import atlas_relative
from ops.atlas.qa._common import baseline_manifest_path, default_baseline_dir, resolve_ref, utc_now, validate_visual_baseline_payload
from ops.cortex._artifacts import write_json


def _mask_ignored_regions(image: Image.Image, ignored_regions: list[dict[str, int]]) -> Image.Image:
    masked = image.copy()
    draw = ImageDraw.Draw(masked)
    for region in ignored_regions:
        x = int(region["x"])
        y = int(region["y"])
        width = int(region["width"])
        height = int(region["height"])
        draw.rectangle((x, y, x + width - 1, y + height - 1), fill=(0, 0, 0, 0))
    return masked


def _count_changed_pixels(diff_image: Image.Image) -> int:
    changed = 0
    pixels = diff_image.load()
    width, height = diff_image.size
    for x in range(width):
        for y in range(height):
            pixel = pixels[x, y]
            if isinstance(pixel, int):
                if pixel != 0:
                    changed += 1
            elif any(channel != 0 for channel in pixel):
                changed += 1
    return changed


def evaluate_visual_diffs(
    *,
    root: Path,
    run_root: Path,
    scenario_payload: dict[str, Any],
    artifact_payload: dict[str, Any],
    dry_run: bool,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    visual_assertions = scenario_payload.get("visual_assertions")
    if not isinstance(visual_assertions, list) or not visual_assertions:
        return [], []

    screenshot_by_lens = {
        str(item.get("lens_id")): item
        for item in artifact_payload.get("artifacts", [])
        if isinstance(item, dict) and item.get("artifact_kind") == "screenshot"
    }
    receipts: list[dict[str, Any]] = []
    findings: list[dict[str, Any]] = []
    baseline_root = default_baseline_dir(root=root)
    output_dir = run_root / "visual-diffs"
    output_dir.mkdir(parents=True, exist_ok=True)

    for assertion in visual_assertions:
        if not isinstance(assertion, dict):
            continue
        lens_id = str(assertion.get("lens_id") or "")
        baseline_ref = str(assertion.get("baseline_ref") or "")
        max_pixel_delta = int(assertion.get("max_pixel_delta") or 0)
        ignored_regions = [region for region in assertion.get("ignored_regions", []) if isinstance(region, dict)]
        ignored_selectors = [str(selector) for selector in assertion.get("ignored_selectors", []) if isinstance(selector, str) and selector.strip()]
        artifact = screenshot_by_lens.get(lens_id)
        receipt: dict[str, Any] = {
            "lens_id": lens_id,
            "baseline_ref": baseline_ref,
            "max_pixel_delta": max_pixel_delta,
            "ignored_regions": ignored_regions,
            "ignored_selectors": ignored_selectors,
            "evaluated_at": utc_now(),
            "status": "planned" if dry_run else "candidate_missing",
        }
        if dry_run:
            receipts.append(receipt)
            continue
        if ignored_selectors:
            findings.append(
                {
                    "severity": "warning",
                    "code": "ignored_selectors_not_applied",
                    "message": f"Visual assertion for '{lens_id}' declares ignored_selectors, but root diffing only applies ignored_regions.",
                    "lens_id": lens_id,
                }
            )
        if not baseline_ref:
            receipt["status"] = "baseline_required"
            receipts.append(receipt)
            findings.append(
                {
                    "severity": "warning",
                    "code": "baseline_required",
                    "message": f"Visual assertion for '{lens_id}' does not yet have a promoted baseline.",
                    "lens_id": lens_id,
                }
            )
            continue
        baseline_path = resolve_ref(baseline_ref, root=root)
        if not baseline_path.exists():
            receipt["status"] = "baseline_required"
            receipts.append(receipt)
            findings.append(
                {
                    "severity": "warning",
                    "code": "baseline_required",
                    "message": f"Visual assertion baseline is missing for '{lens_id}'.",
                    "lens_id": lens_id,
                }
            )
            continue
        baseline_state_path = baseline_manifest_path(baseline_path)
        if not baseline_state_path.exists():
            receipt["status"] = "baseline_required"
            receipts.append(receipt)
            findings.append(
                {
                    "severity": "warning",
                    "code": "baseline_manifest_required",
                    "message": f"Visual baseline for '{lens_id}' exists but is not blessed under the v1 baseline lifecycle.",
                    "lens_id": lens_id,
                }
            )
            continue
        baseline_manifest = json.loads(baseline_state_path.read_text(encoding="utf-8"))
        baseline_manifest_errors = validate_visual_baseline_payload(baseline_manifest)
        if baseline_manifest_errors or baseline_manifest.get("state") != "blessed":
            receipt["status"] = "baseline_required"
            receipts.append(receipt)
            for message in baseline_manifest_errors or ["Baseline manifest must be blessed before it can gate promotion."]:
                findings.append(
                    {
                        "severity": "warning",
                        "code": "baseline_manifest_required",
                        "message": f"Visual baseline manifest for '{lens_id}' is not promotion-ready: {message}",
                        "lens_id": lens_id,
                    }
                )
            continue
        if not str(atlas_relative(baseline_path, root=root)).startswith(str(atlas_relative(baseline_root, root=root))):
            receipt["status"] = "invalid_baseline"
            receipts.append(receipt)
            findings.append(
                {
                    "severity": "error",
                    "code": "invalid_baseline_location",
                    "message": f"Visual baseline for '{lens_id}' must live under {atlas_relative(baseline_root, root=root)}.",
                    "lens_id": lens_id,
                }
            )
            continue
        if not isinstance(artifact, dict) or artifact.get("status") != "present" or not isinstance(artifact.get("path_ref"), str):
            receipt["status"] = "candidate_missing"
            receipts.append(receipt)
            findings.append(
                {
                    "severity": "error",
                    "code": "missing_visual_candidate",
                    "message": f"Visual assertion candidate screenshot is missing for '{lens_id}'.",
                    "lens_id": lens_id,
                }
            )
            continue
        candidate_path = resolve_ref(str(artifact["path_ref"]), root=root)
        if not candidate_path.exists():
            receipt["status"] = "candidate_missing"
            receipts.append(receipt)
            findings.append(
                {
                    "severity": "error",
                    "code": "missing_visual_candidate",
                    "message": f"Visual assertion candidate file does not exist for '{lens_id}'.",
                    "lens_id": lens_id,
                }
            )
            continue
        try:
            with Image.open(baseline_path) as baseline_image_raw, Image.open(candidate_path) as candidate_image_raw:
                baseline_image = baseline_image_raw.convert("RGBA")
                candidate_image = candidate_image_raw.convert("RGBA")
                if baseline_image.size != candidate_image.size:
                    receipt["status"] = "size_mismatch"
                    receipt["baseline_size"] = list(baseline_image.size)
                    receipt["candidate_size"] = list(candidate_image.size)
                    receipts.append(receipt)
                    findings.append(
                        {
                            "severity": "error",
                            "code": "visual_size_mismatch",
                            "message": f"Visual assertion dimensions differ for '{lens_id}'.",
                            "lens_id": lens_id,
                        }
                    )
                    continue
                masked_baseline = _mask_ignored_regions(baseline_image, ignored_regions)
                masked_candidate = _mask_ignored_regions(candidate_image, ignored_regions)
                diff_image = ImageChops.difference(masked_baseline, masked_candidate)
                changed_pixels = _count_changed_pixels(diff_image)
                diff_path = output_dir / f"{lens_id}.diff.png"
                diff_image.save(diff_path, format="PNG")
                receipt["baseline_image_ref"] = atlas_relative(baseline_path, root=root)
                receipt["candidate_image_ref"] = atlas_relative(candidate_path, root=root)
                receipt["diff_image_ref"] = atlas_relative(diff_path, root=root)
                receipt["changed_pixels"] = changed_pixels
                receipt["status"] = "passed" if changed_pixels <= max_pixel_delta else "failed"
                receipt_path = output_dir / f"{lens_id}.result.json"
                write_json(receipt_path, receipt)
                receipt["receipt_ref"] = atlas_relative(receipt_path, root=root)
                receipts.append(receipt)
                if changed_pixels > max_pixel_delta:
                    findings.append(
                        {
                            "severity": "error",
                            "code": "visual_diff_failed",
                            "message": f"Visual diff exceeded the max pixel delta for '{lens_id}' ({changed_pixels} > {max_pixel_delta}).",
                            "lens_id": lens_id,
                        }
                    )
        except Exception as exc:
            receipt["status"] = "invalid_candidate"
            receipts.append(receipt)
            findings.append(
                {
                    "severity": "error",
                    "code": "visual_diff_error",
                    "message": f"Visual diff failed for '{lens_id}': {exc}",
                    "lens_id": lens_id,
                }
            )
    return receipts, findings
