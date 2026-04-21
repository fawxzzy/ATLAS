from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from PIL import Image, ImageChops

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from ops._atlas import atlas_relative, atlas_root, normalize_slashes
from ops.atlas.ui_observe.fitness import UI_CAPTURE_MAP_CONTRACT_VERSION, load_json_object
from ops.cortex._artifacts import stable_json_digest, write_json

UI_VISUAL_PROOF_CONTRACT_VERSION = "atlas.ui.visual-proof.v1"
UI_VISUAL_PROOF_SCHEMA_ID = "atlas://schemas/atlas.ui.visual-proof.v1.json"
UI_VISUAL_PROOF_REPORT_CONTRACT_VERSION = "atlas.ui.visual-proof.report.v1"
VISUAL_PROOF_RUNNER_VERSION = "atlas.ui.visual-proof.fitness.v1"
ASSERTION_KINDS = (
    "unchanged",
    "changed_expected",
    "changed_only_within_mask",
    "max_visual_delta",
    "min_visual_delta",
)


def validate_visual_proof_report_payload(payload: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if payload.get("contract_version") != UI_VISUAL_PROOF_REPORT_CONTRACT_VERSION:
        errors.append(f"contract_version must be '{UI_VISUAL_PROOF_REPORT_CONTRACT_VERSION}'.")
    report_id = payload.get("report_id")
    if not isinstance(report_id, str) or not report_id.startswith("sha256:"):
        errors.append("report_id must be a sha256 digest string.")
    if not isinstance(payload.get("generated_at"), str) or not str(payload.get("generated_at")).strip():
        errors.append("generated_at must be a non-empty string.")
    if not isinstance(payload.get("owner_repo_id"), str) or not str(payload.get("owner_repo_id")).strip():
        errors.append("owner_repo_id must be a non-empty string.")
    if not isinstance(payload.get("manifest_ref"), str) or not str(payload.get("manifest_ref")).strip():
        errors.append("manifest_ref must be a non-empty string.")
    if not isinstance(payload.get("capture_map_ref"), str) or not str(payload.get("capture_map_ref")).strip():
        errors.append("capture_map_ref must be a non-empty string.")
    summary = payload.get("summary")
    if not isinstance(summary, dict):
        errors.append("summary must be an object.")
    else:
        if summary.get("status") not in {"clean", "proof_failed"}:
            errors.append("summary.status must be 'clean' or 'proof_failed'.")
        for field in ("capture_count", "passing_count", "failing_count"):
            value = summary.get(field)
            if not isinstance(value, int) or value < 0:
                errors.append(f"summary.{field} must be a non-negative integer.")
    results = payload.get("results")
    if not isinstance(results, list):
        errors.append("results must be an array.")
    operator_summary = payload.get("operator_summary")
    if not isinstance(operator_summary, list):
        errors.append("operator_summary must be an array.")
    return errors


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def stamp_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")


def default_manifest_path(root: Path | None = None) -> Path:
    base = (root or atlas_root()).resolve()
    return base / "ops" / "atlas" / "ui_visual_proof" / "fitness_visual_proof.v1.json"


def default_schema_path(root: Path | None = None) -> Path:
    base = (root or atlas_root()).resolve()
    return base / "schemas" / "atlas.ui.visual-proof.v1.json"


def default_report_root(root: Path | None = None) -> Path:
    base = (root or atlas_root()).resolve()
    return base / "runtime" / "atlas" / "ui-visual-proof" / "fitness"


def _resolve_ref(ref: str, *, root: Path) -> Path:
    candidate = Path(ref)
    return candidate.resolve() if candidate.is_absolute() else (root / candidate).resolve()


def _default_current_image_path(capture_id: str, *, manifest: dict[str, Any], root: Path) -> Path:
    artifact_root_ref = str(manifest.get("image_artifact_root", "runtime/atlas/ui-observe/fitness"))
    return _resolve_ref(artifact_root_ref, root=root) / capture_id / "visual" / "latest.png"


def _default_reference_image_path(capture_id: str, *, manifest: dict[str, Any], root: Path) -> Path:
    reference_root_ref = str(manifest.get("reference_root", "data/atlas/ui-visual-proof/fitness"))
    return _resolve_ref(reference_root_ref, root=root) / capture_id / "reference.png"


def _default_mask_image_path(capture_id: str, *, manifest: dict[str, Any], root: Path) -> Path:
    reference_root_ref = str(manifest.get("reference_root", "data/atlas/ui-visual-proof/fitness"))
    return _resolve_ref(reference_root_ref, root=root) / capture_id / "mask.png"


def validate_schema_definition(schema: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if schema.get("$schema") != "https://json-schema.org/draft/2020-12/schema":
        errors.append("Schema $schema must target draft 2020-12.")
    if schema.get("$id") != UI_VISUAL_PROOF_SCHEMA_ID:
        errors.append(f"Schema $id must be '{UI_VISUAL_PROOF_SCHEMA_ID}'.")
    if schema.get("title") != "ATLAS UI visual proof v1":
        errors.append("Schema title must be 'ATLAS UI visual proof v1'.")
    return errors


def _capture_map_ids(manifest: dict[str, Any], *, root: Path) -> tuple[set[str], str]:
    capture_map_path = _resolve_ref(str(manifest["capture_map_ref"]), root=root)
    capture_map = load_json_object(capture_map_path)
    capture_ids = {
        str(item.get("capture_id"))
        for item in capture_map.get("captures", [])
        if isinstance(item, dict) and isinstance(item.get("capture_id"), str)
    }
    return capture_ids, stable_json_digest(capture_map)


def validate_visual_proof_manifest(manifest: dict[str, Any], *, root: Path) -> list[str]:
    errors: list[str] = []
    if manifest.get("contract_version") != UI_VISUAL_PROOF_CONTRACT_VERSION:
        errors.append(f"contract_version must be '{UI_VISUAL_PROOF_CONTRACT_VERSION}'.")

    for key in ("owner_repo_id", "owner_repo_path", "capture_map_ref", "image_artifact_root", "reference_root"):
        value = manifest.get(key)
        if not isinstance(value, str) or not value.strip():
            errors.append(f"{key} must be a non-empty string.")

    owner_repo_path = manifest.get("owner_repo_path")
    if isinstance(owner_repo_path, str) and owner_repo_path.strip() and not _resolve_ref(owner_repo_path, root=root).exists():
        errors.append(f"owner_repo_path does not exist: {owner_repo_path}")

    capture_map_ref = manifest.get("capture_map_ref")
    capture_map_ids: set[str] = set()
    if isinstance(capture_map_ref, str) and capture_map_ref.strip():
        capture_map_path = _resolve_ref(capture_map_ref, root=root)
        if not capture_map_path.exists():
            errors.append(f"capture_map_ref does not exist: {capture_map_ref}")
        else:
            capture_map = load_json_object(capture_map_path)
            if capture_map.get("contract_version") != UI_CAPTURE_MAP_CONTRACT_VERSION:
                errors.append(f"capture_map_ref must point to '{UI_CAPTURE_MAP_CONTRACT_VERSION}'.")
            else:
                capture_map_ids = {
                    str(item.get("capture_id"))
                    for item in capture_map.get("captures", [])
                    if isinstance(item, dict) and isinstance(item.get("capture_id"), str)
                }

    expected_capture_map_digest = manifest.get("expected_capture_map_digest")
    if expected_capture_map_digest is not None and (
        not isinstance(expected_capture_map_digest, str) or not expected_capture_map_digest.startswith("sha256:")
    ):
        errors.append("expected_capture_map_digest must be a sha256 digest string when present.")

    captures = manifest.get("captures")
    if not isinstance(captures, list):
        errors.append("captures must be an array.")
        return errors

    seen_capture_ids: set[str] = set()
    for index, item in enumerate(captures):
        path = f"captures[{index}]"
        if not isinstance(item, dict):
            errors.append(f"{path} must be an object.")
            continue
        capture_id = item.get("capture_id")
        if not isinstance(capture_id, str) or not capture_id.strip():
            errors.append(f"{path}.capture_id must be a non-empty string.")
            continue
        if capture_id in seen_capture_ids:
            errors.append(f"{path}.capture_id '{capture_id}' is duplicated.")
        else:
            seen_capture_ids.add(capture_id)
        if capture_map_ids and capture_id not in capture_map_ids:
            errors.append(f"{path}.capture_id '{capture_id}' does not exist in the capture map.")

        expected_observation_digest = item.get("expected_observation_digest")
        if expected_observation_digest is not None and (
            not isinstance(expected_observation_digest, str) or not expected_observation_digest.startswith("sha256:")
        ):
            errors.append(f"{path}.expected_observation_digest must be a sha256 digest string when present.")

        assertion = item.get("assertion")
        if not isinstance(assertion, dict):
            errors.append(f"{path}.assertion must be an object.")
            continue
        kind = assertion.get("kind")
        if kind not in ASSERTION_KINDS:
            errors.append(f"{path}.assertion.kind must be one of: {', '.join(ASSERTION_KINDS)}.")
            continue
        if kind == "max_visual_delta":
            value = assertion.get("max_visual_delta")
            if not isinstance(value, (int, float)) or value < 0 or value > 1:
                errors.append(f"{path}.assertion.max_visual_delta must be a number between 0 and 1.")
        if kind == "min_visual_delta":
            value = assertion.get("min_visual_delta")
            if not isinstance(value, (int, float)) or value < 0 or value > 1:
                errors.append(f"{path}.assertion.min_visual_delta must be a number between 0 and 1.")
        if kind == "changed_only_within_mask":
            mask_ref = item.get("mask_image_ref")
            default_mask = _default_mask_image_path(capture_id, manifest=manifest, root=root)
            if mask_ref is None and not default_mask.exists():
                errors.append(f"{path} requires mask_image_ref or a default mask at {normalize_slashes(str(default_mask))}.")
    return errors


def _load_rgba(path: Path) -> Image.Image:
    with Image.open(path) as image:
        return image.convert("RGBA")


def _load_mask(path: Path, *, size: tuple[int, int]) -> Image.Image:
    with Image.open(path) as image:
        mask = image.convert("L")
    if mask.size != size:
        raise ValueError("mask_size_mismatch")
    return mask


def _compare_images(current: Image.Image, reference: Image.Image, mask: Image.Image | None) -> dict[str, Any]:
    if current.size != reference.size:
        raise ValueError("image_size_mismatch")

    diff_image = ImageChops.difference(reference, current)
    current_pixels = current.load()
    reference_pixels = reference.load()
    mask_pixels = mask.load() if mask is not None else None
    width, height = current.size
    diff_pixels = 0
    total_channel_delta = 0
    outside_mask_diff_pixels = 0

    for y in range(height):
        for x in range(width):
            current_pixel = current_pixels[x, y]
            reference_pixel = reference_pixels[x, y]
            if current_pixel == reference_pixel:
                continue
            diff_pixels += 1
            total_channel_delta += sum(abs(int(current_pixel[index]) - int(reference_pixel[index])) for index in range(4))
            if mask_pixels is not None and int(mask_pixels[x, y]) == 0:
                outside_mask_diff_pixels += 1

    total_pixels = width * height
    diff_ratio = diff_pixels / total_pixels if total_pixels else 0.0
    channel_delta_ratio = total_channel_delta / (total_pixels * 4 * 255) if total_pixels else 0.0
    return {
        "diff_image": diff_image,
        "metrics": {
            "width": width,
            "height": height,
            "total_pixels": total_pixels,
            "diff_pixels": diff_pixels,
            "diff_ratio": round(diff_ratio, 8),
            "total_channel_delta": total_channel_delta,
            "channel_delta_ratio": round(channel_delta_ratio, 8),
            "outside_mask_diff_pixels": outside_mask_diff_pixels,
        },
    }


def _evaluate_assertion(assertion: dict[str, Any], metrics: dict[str, Any]) -> tuple[str, str | None]:
    kind = str(assertion["kind"])
    diff_pixels = int(metrics["diff_pixels"])
    diff_ratio = float(metrics["diff_ratio"])
    outside_mask_diff_pixels = int(metrics["outside_mask_diff_pixels"])

    if kind == "unchanged":
        return ("pass", None) if diff_pixels == 0 else ("fail", "Image changed but assertion requires unchanged.")
    if kind == "changed_expected":
        return ("pass", None) if diff_pixels > 0 else ("fail", "Image did not change but assertion expects a change.")
    if kind == "changed_only_within_mask":
        if diff_pixels == 0:
            return "fail", "Image did not change but assertion expects masked change."
        if outside_mask_diff_pixels > 0:
            return "fail", "Detected visual change outside the allowed mask."
        return "pass", None
    if kind == "max_visual_delta":
        return ("pass", None) if diff_ratio <= float(assertion["max_visual_delta"]) else ("fail", "Visual delta exceeds max_visual_delta.")
    if kind == "min_visual_delta":
        return ("pass", None) if diff_ratio >= float(assertion["min_visual_delta"]) else ("fail", "Visual delta is below min_visual_delta.")
    return "fail", f"Unsupported assertion kind '{kind}'."


def _write_diff_image(path: Path, image: Image.Image) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    image.save(path, format="PNG")


def _markdown_report(report: dict[str, Any]) -> str:
    lines = [
        "# ATLAS UI Visual Proof",
        "",
        f"- Generated: `{report['generated_at']}`",
        f"- Owner repo: `{report['owner_repo_id']}`",
        f"- Status: `{report['summary']['status']}`",
        f"- Results: {report['summary']['capture_count']}",
        f"- Failing: {report['summary']['failing_count']}",
        "",
        "## Operator Summary",
        "",
    ]
    for line in report["operator_summary"]:
        lines.append(f"- {line}")
    if report["results"]:
        lines.extend(["", "## Results", ""])
        for result in report["results"]:
            lines.append(
                f"- `{result['capture_id']}` `{result['assertion']['kind']}` -> `{result['status']}` "
                f"(diff_ratio={result['metrics'].get('diff_ratio')})"
            )
            if result.get("message"):
                lines.append(f"  - {result['message']}")
    return "\n".join(lines) + "\n"


def run_visual_proof(
    *,
    root: Path | None = None,
    manifest_path: Path | None = None,
    schema_path: Path | None = None,
    report_root: Path | None = None,
    capture_ids: list[str] | None = None,
    dry_run: bool = False,
) -> dict[str, Any]:
    base_root = (root or atlas_root()).resolve()
    manifest_target = (manifest_path or default_manifest_path(base_root)).resolve()
    schema_target = (schema_path or default_schema_path(base_root)).resolve()
    report_target = (report_root or default_report_root(base_root)).resolve()

    schema = load_json_object(schema_target)
    schema_errors = validate_schema_definition(schema)
    if schema_errors:
        raise ValueError("; ".join(schema_errors))

    manifest = load_json_object(manifest_target)
    manifest_errors = validate_visual_proof_manifest(manifest, root=base_root)
    if manifest_errors:
        raise ValueError("; ".join(manifest_errors))

    capture_map_ids, live_capture_map_digest = _capture_map_ids(manifest, root=base_root)
    selected_capture_ids = {item.strip() for item in (capture_ids or []) if item.strip()}
    expected_capture_map_digest = manifest.get("expected_capture_map_digest")
    manifest_stale = (
        isinstance(expected_capture_map_digest, str)
        and expected_capture_map_digest.strip()
        and expected_capture_map_digest != live_capture_map_digest
    )
    results: list[dict[str, Any]] = []

    for capture in manifest.get("captures", []):
        if not isinstance(capture, dict):
            continue
        capture_id = str(capture["capture_id"])
        if selected_capture_ids and capture_id not in selected_capture_ids:
            continue

        current_image_path = (
            _resolve_ref(str(capture["current_image_ref"]), root=base_root)
            if isinstance(capture.get("current_image_ref"), str)
            else _default_current_image_path(capture_id, manifest=manifest, root=base_root)
        )
        reference_image_path = (
            _resolve_ref(str(capture["reference_image_ref"]), root=base_root)
            if isinstance(capture.get("reference_image_ref"), str)
            else _default_reference_image_path(capture_id, manifest=manifest, root=base_root)
        )
        mask_image_path = (
            _resolve_ref(str(capture["mask_image_ref"]), root=base_root)
            if isinstance(capture.get("mask_image_ref"), str)
            else _default_mask_image_path(capture_id, manifest=manifest, root=base_root)
        )
        observation_path = (
            _resolve_ref(str(capture["observation_ref"]), root=base_root)
            if isinstance(capture.get("observation_ref"), str)
            else base_root / "runtime" / "atlas" / "ui-observe" / "fitness" / capture_id / "latest.json"
        )

        result: dict[str, Any] = {
            "capture_id": capture_id,
            "status": "pass",
            "message": None,
            "assertion": dict(capture["assertion"]),
            "current_image_ref": atlas_relative(current_image_path, root=base_root),
            "reference_image_ref": atlas_relative(reference_image_path, root=base_root),
            "mask_image_ref": atlas_relative(mask_image_path, root=base_root) if mask_image_path.exists() else None,
            "observation_ref": atlas_relative(observation_path, root=base_root) if observation_path.exists() else None,
            "metrics": {
                "diff_pixels": 0,
                "diff_ratio": 0.0,
                "total_pixels": 0,
                "total_channel_delta": 0,
                "channel_delta_ratio": 0.0,
                "outside_mask_diff_pixels": 0,
            },
            "stale_manifest": False,
            "outputs": {},
        }

        if capture_id not in capture_map_ids:
            result["status"] = "fail"
            result["message"] = "Capture id is not present in the active capture map."
            results.append(result)
            continue

        if manifest_stale:
            result["status"] = "fail"
            result["message"] = "Manifest expected_capture_map_digest does not match the active capture map digest."
            result["stale_manifest"] = True
            results.append(result)
            continue

        expected_observation_digest = capture.get("expected_observation_digest")
        if expected_observation_digest is not None:
            if not observation_path.exists():
                result["status"] = "fail"
                result["message"] = "Expected observation digest was declared but the latest observation is missing."
                result["stale_manifest"] = True
                results.append(result)
                continue
            observation_payload = load_json_object(observation_path)
            if observation_payload.get("comparison_digest") != expected_observation_digest:
                result["status"] = "fail"
                result["message"] = "Manifest expected_observation_digest does not match the latest observation."
                result["stale_manifest"] = True
                results.append(result)
                continue

        if not reference_image_path.exists():
            result["status"] = "fail"
            result["message"] = "Reference image is missing."
            results.append(result)
            continue
        if not current_image_path.exists():
            result["status"] = "fail"
            result["message"] = "Current image artifact is missing."
            results.append(result)
            continue

        try:
            current_image = _load_rgba(current_image_path)
            reference_image = _load_rgba(reference_image_path)
            mask_image = None
            if str(capture["assertion"]["kind"]) == "changed_only_within_mask":
                if not mask_image_path.exists():
                    result["status"] = "fail"
                    result["message"] = "Mask image is missing for changed_only_within_mask."
                    results.append(result)
                    continue
                mask_image = _load_mask(mask_image_path, size=current_image.size)
            comparison = _compare_images(current_image, reference_image, mask_image)
        except ValueError as exc:
            if str(exc) == "mask_size_mismatch":
                result["status"] = "fail"
                result["message"] = "Mask image size does not match the compared images."
            else:
                result["status"] = "fail"
                result["message"] = "Current and reference images must be the same size."
            results.append(result)
            continue

        result["metrics"] = comparison["metrics"]
        status, message = _evaluate_assertion(capture["assertion"], comparison["metrics"])
        result["status"] = status
        result["message"] = message

        if not dry_run:
            diff_path = report_target / capture_id / "latest-diff.png"
            _write_diff_image(diff_path, comparison["diff_image"])
            result["outputs"]["diff_image_ref"] = atlas_relative(diff_path, root=base_root)

        results.append(result)

    results.sort(key=lambda item: item["capture_id"])
    summary = {
        "status": "clean" if all(item["status"] == "pass" for item in results) else "proof_failed",
        "capture_count": len(results),
        "passing_count": sum(1 for item in results if item["status"] == "pass"),
        "failing_count": sum(1 for item in results if item["status"] != "pass"),
    }
    report_body = {
        "contract_version": UI_VISUAL_PROOF_REPORT_CONTRACT_VERSION,
        "generated_at": utc_now(),
        "runner_version": VISUAL_PROOF_RUNNER_VERSION,
        "owner_repo_id": str(manifest["owner_repo_id"]),
        "owner_repo_path": normalize_slashes(str(manifest["owner_repo_path"])),
        "manifest_ref": atlas_relative(manifest_target, root=base_root),
        "capture_map_ref": str(manifest["capture_map_ref"]),
        "summary": summary,
        "results": results,
        "operator_summary": (
            [f"Visual proof passed across {summary['capture_count']} captures."]
            if summary["status"] == "clean"
            else [f"Visual proof failed: {summary['failing_count']} of {summary['capture_count']} captures failed."]
        ),
    }
    report = {**report_body, "report_id": stable_json_digest(report_body)}

    outputs: dict[str, str] = {}
    if not dry_run:
        stamped_name = f"{stamp_now()}-{report['report_id'].replace('sha256:', '')[:16]}"
        latest_json = report_target / "latest.json"
        latest_md = report_target / "latest.md"
        stamped_json = report_target / f"{stamped_name}.json"
        stamped_md = report_target / f"{stamped_name}.md"
        write_json(latest_json, report)
        write_json(stamped_json, report)
        latest_md.parent.mkdir(parents=True, exist_ok=True)
        latest_md.write_text(_markdown_report(report), encoding="utf-8")
        stamped_md.write_text(_markdown_report(report), encoding="utf-8")
        outputs = {
            "latest_json_ref": atlas_relative(latest_json, root=base_root),
            "latest_md_ref": atlas_relative(latest_md, root=base_root),
            "report_json_ref": atlas_relative(stamped_json, root=base_root),
            "report_md_ref": atlas_relative(stamped_md, root=base_root),
        }

    return {
        **report,
        "schema_ref": atlas_relative(schema_target, root=base_root),
        "outputs": outputs,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run deterministic ATLAS UI visual proof against declared image captures.")
    parser.add_argument("--root", type=Path, default=atlas_root())
    parser.add_argument("--manifest-file", type=Path)
    parser.add_argument("--schema-file", type=Path)
    parser.add_argument("--report-root", type=Path)
    parser.add_argument("--capture-id", action="append", default=[])
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args(argv)

    result = run_visual_proof(
        root=args.root.resolve(),
        manifest_path=args.manifest_file.resolve() if isinstance(args.manifest_file, Path) else None,
        schema_path=args.schema_file.resolve() if isinstance(args.schema_file, Path) else None,
        report_root=args.report_root.resolve() if isinstance(args.report_root, Path) else None,
        capture_ids=list(args.capture_id),
        dry_run=bool(args.dry_run),
    )
    print(json.dumps(result, indent=2))
    return 0 if result["summary"]["status"] == "clean" else 1


if __name__ == "__main__":
    raise SystemExit(main())
