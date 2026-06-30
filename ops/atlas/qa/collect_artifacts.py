from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from ops._atlas import atlas_relative, atlas_root, normalize_slashes
from ops.atlas.qa._common import (
    ARTIFACT_CONTRACT_VERSION,
    RESULT_CONTRACT_VERSION,
    default_run_root,
    load_adapter_manifest,
    load_json_object,
    load_lens_manifest,
    load_schema,
    load_provider_manifest,
    payload_with_digest,
    resolve_ref,
    utc_now,
    validate_artifact_manifest,
    validate_result_payload,
    validate_schema_metadata,
    write_manifest,
)
from ops.atlas.qa.capture_browser import capture_with_playwright
from ops.atlas.qa.manual_attestation import validate_attestation_file
from ops.atlas.qa.providers import capture_with_provider
from ops.cortex._artifacts import read_json, sha256_bytes, write_json

RUNNER_VERSION = "atlas.qa.collect-artifacts.v2"


def _artifact_override_map(values: list[str], *, root: Path) -> dict[tuple[str, str], Path]:
    result: dict[tuple[str, str], Path] = {}
    for value in values:
        lens_id, separator, rest = value.partition(":")
        artifact_kind, separator2, path_ref = rest.partition(":")
        if not separator or not separator2:
            raise ValueError("artifact overrides must use lens_id:artifact_kind:path format.")
        result[(lens_id.strip(), artifact_kind.strip())] = resolve_ref(path_ref.strip(), root=root)
    return result


def _attestation_file_list(values: list[str], *, root: Path, run_root: Path) -> list[Path]:
    explicit = [resolve_ref(value, root=root) for value in values]
    discovered = sorted((run_root / "manual-attestations").glob("*.json")) if (run_root / "manual-attestations").exists() else []
    seen: set[Path] = set()
    result: list[Path] = []
    for item in [*explicit, *discovered]:
        resolved = item.resolve()
        if resolved not in seen:
            seen.add(resolved)
            result.append(resolved)
    return result


def _load_attestations(*, root: Path, run_root: Path, attestation_files: list[str]) -> tuple[dict[str, dict[str, Any]], list[dict[str, Any]]]:
    by_lens: dict[str, dict[str, Any]] = {}
    summaries: list[dict[str, Any]] = []
    for path in _attestation_file_list(attestation_files, root=root, run_root=run_root):
        summary, findings = validate_attestation_file(root=root, attestation_path=path)
        lens_id = summary.get("lens_id")
        if isinstance(lens_id, str) and lens_id.strip():
            by_lens[lens_id] = summary
        summaries.append(summary)
    return by_lens, summaries


def _find_run_root(result_path: Path) -> Path:
    if result_path.name == "matrix.result.json":
        return result_path.parent
    return result_path.parent


def _result_by_lens(result_payload: dict[str, Any]) -> dict[str, dict[str, Any]]:
    output: dict[str, dict[str, Any]] = {}
    for item in result_payload.get("matrix", []):
        if isinstance(item, dict) and isinstance(item.get("lens_id"), str):
            output[str(item["lens_id"])] = item
    return output


def _read_bytes(path: Path) -> bytes:
    return path.read_bytes()


def _content_type_for_kind(artifact_kind: str) -> str:
    if artifact_kind == "screenshot":
        return "image/png"
    if artifact_kind == "trace":
        return "application/zip"
    if artifact_kind == "video":
        return "video/webm"
    if artifact_kind in {"console_log", "manual_note"}:
        return "text/plain"
    return "application/json"


def _lens_profile_map(lens_manifest: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {
        str(item["lens_id"]): item
        for item in lens_manifest.get("lenses", [])
        if isinstance(item, dict) and isinstance(item.get("lens_id"), str)
    }


def _target_file_for_kind(output_dir: Path, artifact_kind: str) -> Path:
    if artifact_kind == "screenshot":
        return output_dir / "screenshot.png"
    if artifact_kind == "trace":
        return output_dir / "trace.zip"
    if artifact_kind == "console_log":
        return output_dir / "console.log"
    if artifact_kind == "network_log":
        return output_dir / "network.json"
    if artifact_kind == "video":
        return output_dir / "video.webm"
    return output_dir / f"{artifact_kind}.json"


def _build_capture_config(
    *,
    repo_root: Path,
    output_dir: Path,
    adapter: dict[str, Any],
    lens: dict[str, Any],
    lens_profile: dict[str, Any],
    scenario: dict[str, Any],
    result_payload: dict[str, Any],
) -> dict[str, Any]:
    capture = adapter.get("capture", {}) if isinstance(adapter.get("capture"), dict) else {}
    start = adapter.get("start", {}) if isinstance(adapter.get("start"), dict) else {}
    target_url = str(start.get("default_url") or "")
    entrypoint = scenario.get("entrypoint", {}) if isinstance(scenario.get("entrypoint"), dict) else {}
    entry_path = str(entrypoint.get("path") or "").strip()
    if entry_path and target_url.rstrip("/"):
        source_url = f"{target_url.rstrip('/')}/{entry_path.lstrip('/')}"
    else:
        source_url = target_url
    return {
        "repoRoot": str(repo_root),
        "outputDir": str(output_dir),
        "browserEngine": str(lens_profile["browser_engine"]),
        "viewport": dict(lens_profile["viewport"]),
        "mobile": bool(lens_profile.get("mobile")),
        "hasTouch": bool(lens_profile.get("has_touch")),
        "userAgent": lens_profile.get("user_agent"),
        "sourceUrl": source_url,
        "waitUntil": str(capture.get("wait_until") or "networkidle"),
        "settleMs": int(capture.get("settle_ms") or 0),
        "readySelector": capture.get("ready_selector"),
        "readyTimeoutMs": int(capture.get("ready_timeout_ms") or 30000),
        "fullPage": bool(capture.get("full_page")),
        "disableAnimations": bool(capture.get("disable_animations", True)),
        "artifactKinds": ["screenshot", "console_log", "network_log", "trace"],
        "runId": str(result_payload["run_id"]),
        "scenarioId": str(scenario["scenario_id"]),
        "adapterId": str(adapter["adapter_id"]),
        "repoId": str(result_payload["repo_id"]),
        "gitSha": str(result_payload["git_sha"]),
        "lensId": str(lens["lens_id"]),
        "lensProfileId": str(lens["profile_id"]),
        "evidenceKind": str(lens.get("evidence_kind") or ""),
    }


def _provider_capture_config(
    *,
    base_config: dict[str, Any],
    lens_id: str,
    lens: dict[str, Any],
    lens_profile: dict[str, Any],
    provider_type: str,
) -> dict[str, Any]:
    explicit_values = {
        "deviceModel": lens.get("device_model"),
        "osName": lens.get("os_name"),
        "osVersion": lens.get("os_version"),
        "browserName": lens.get("browser_name"),
        "browserVersion": lens.get("browser_version"),
    }
    defaults_by_lens = {
        "desktop.chromium.real": {
            "deviceModel": "Windows Desktop",
            "osName": "Windows",
            "osVersion": "11",
            "browserName": "chrome",
            "browserVersion": "latest",
        },
        "android.chrome.real": {
            "deviceModel": "Samsung Galaxy S23",
            "osName": "Android",
            "osVersion": "13.0",
            "browserName": "chrome",
            "browserVersion": "latest",
        },
        "iphone.webkit.real": {
            "deviceModel": "iPhone 15",
            "osName": "iOS",
            "osVersion": "17",
            "browserName": "safari",
            "browserVersion": "17",
        },
    }
    profile_browser_name = str(lens_profile.get("browser_engine") or "").strip().lower()
    normalized_browser_name = {
        "chromium": "chrome",
        "webkit": "safari",
    }.get(profile_browser_name, profile_browser_name)
    defaults = defaults_by_lens.get(lens_id, {})
    merged = {
        **base_config,
        "deviceModel": explicit_values["deviceModel"] or defaults.get("deviceModel"),
        "osName": explicit_values["osName"] or defaults.get("osName"),
        "osVersion": explicit_values["osVersion"] or defaults.get("osVersion"),
        "browserName": explicit_values["browserName"] or defaults.get("browserName") or normalized_browser_name,
        "browserVersion": explicit_values["browserVersion"] or defaults.get("browserVersion") or "latest",
        "providerType": provider_type,
    }
    missing = [
        key
        for key in ("deviceModel", "osName", "osVersion", "browserName", "browserVersion")
        if not isinstance(merged.get(key), str) or not str(merged.get(key)).strip()
    ]
    if missing:
        raise RuntimeError(
            f"Lens '{lens_id}' requires explicit provider capability mapping before provider_capture can run. "
            f"Missing: {', '.join(missing)}."
        )
    return merged


def _capture_cache(
    *,
    execute: bool,
    repo_root: Path,
    run_root: Path,
    adapter: dict[str, Any],
    scenario: dict[str, Any],
    result_payload: dict[str, Any],
    lens_payload: dict[str, Any],
    lens_profiles: dict[str, dict[str, Any]],
    result_by_lens: dict[str, dict[str, Any]],
) -> dict[str, dict[str, Any]]:
    cache: dict[str, dict[str, Any]] = {}
    if not execute:
        return cache
    for lens_id, matrix_entry in result_by_lens.items():
        if matrix_entry.get("execution_mode") not in {"browser_capture", "provider_capture"}:
            continue
        lens = next(
            (
                item
                for item in adapter.get("lenses", [])
                if isinstance(item, dict) and item.get("lens_id") == lens_id
            ),
            None,
        )
        if not isinstance(lens, dict):
            continue
        profile = lens_profiles.get(str(lens.get("profile_id") or ""))
        if not isinstance(profile, dict):
            continue
        output_dir = run_root / "captures" / lens_id
        config = _build_capture_config(
            repo_root=repo_root,
            output_dir=output_dir,
            adapter=adapter,
            lens=lens,
            lens_profile=profile,
            scenario=scenario,
            result_payload=result_payload,
        )
        if matrix_entry.get("execution_mode") == "provider_capture":
            provider_manifest_ref = lens.get("provider_manifest_ref")
            if not isinstance(provider_manifest_ref, str) or not provider_manifest_ref.strip():
                raise RuntimeError(f"Lens '{lens_id}' requires provider_capture but does not declare provider_manifest_ref.")
            provider_payload, _ = load_provider_manifest(root=ROOT, provider_manifest_ref=provider_manifest_ref)
            provider_config = _provider_capture_config(
                base_config=config,
                lens_id=lens_id,
                lens=lens,
                lens_profile=profile,
                provider_type=str(provider_payload.get("provider_type") or ""),
            )
            cache[lens_id] = capture_with_provider(root=ROOT, provider_manifest_ref=provider_manifest_ref, config=provider_config)
        else:
            cache[lens_id] = capture_with_playwright(root=ROOT, config=config)
    return cache


def _evidence_for_path(
    *,
    artifact_path: Path,
    metadata_path: Path | None,
    lens_id: str,
    lens_profile: dict[str, Any],
    metadata_payload: dict[str, Any] | None,
) -> dict[str, Any]:
    artifact_bytes = _read_bytes(artifact_path)
    evidence = {
        "run_id": str(metadata_payload.get("run_id")) if isinstance(metadata_payload, dict) else "",
        "scenario_id": str(metadata_payload.get("scenario_id")) if isinstance(metadata_payload, dict) else "",
        "adapter_id": str(metadata_payload.get("adapter_id")) if isinstance(metadata_payload, dict) else "",
        "repo_id": str(metadata_payload.get("repo_id")) if isinstance(metadata_payload, dict) else "",
        "git_sha": str(metadata_payload.get("git_sha")) if isinstance(metadata_payload, dict) else "",
        "lens_id": lens_id,
        "evidence_tier": "manual_attestation" if isinstance(metadata_payload, dict) and metadata_payload.get("capture_method") == "manual_attestation" else (
            "physical_device" if isinstance(metadata_payload, dict) and metadata_payload.get("capture_method") == "provider_automation" else "emulated_browser"
        ),
        "viewport": {
            "width": int(lens_profile["viewport"]["width"]),
            "height": int(lens_profile["viewport"]["height"]),
            "device_scale_factor": float(lens_profile["viewport"]["device_scale_factor"]),
            "mobile": bool(lens_profile.get("mobile")),
        },
        "browser_engine": str(lens_profile["browser_engine"]),
        "captured_at": str(metadata_payload.get("captured_at")) if isinstance(metadata_payload, dict) else "",
        "source_url": str(metadata_payload.get("source_url")) if isinstance(metadata_payload, dict) else "",
        "artifact_sha256": sha256_bytes(artifact_bytes),
        "capture_backend": str(metadata_payload.get("capture_backend") or "") if isinstance(metadata_payload, dict) else "",
        "capture_method": str(metadata_payload.get("capture_method") or "browser_emulation") if isinstance(metadata_payload, dict) else "browser_emulation",
    }
    if isinstance(metadata_payload, dict):
        for key in (
            "provider_id",
            "provider_run_id",
            "device_model",
            "os_name",
            "os_version",
            "browser_name",
            "browser_version",
            "operator",
            "attestation_ref",
        ):
            value = metadata_payload.get(key)
            if isinstance(value, str) and value:
                evidence[key] = value
    if metadata_path is not None:
        evidence["metadata_ref"] = atlas_relative(metadata_path, root=ROOT)
    return evidence


def _write_executable_report(
    *,
    run_root: Path,
    lens_id: str,
    result_payload: dict[str, Any],
    matrix_entry: dict[str, Any],
) -> Path:
    target = run_root / "captures" / lens_id / "executable-report.json"
    payload = {
        "run_id": result_payload["run_id"],
        "scenario_ref": result_payload["scenario_ref"],
        "lens_id": lens_id,
        "matrix_entry": matrix_entry,
    }
    write_json(target, payload)
    return target


def collect_artifacts(
    *,
    root: Path | None = None,
    result_path: Path | None = None,
    run_id: str | None = None,
    artifact_files: list[str] | None = None,
    attestation_files: list[str] | None = None,
    output_file: Path | None = None,
    dry_run: bool = False,
) -> dict[str, Any]:
    base_root = (root or atlas_root()).resolve()
    artifact_schema = load_schema("atlas.qa.artifact.v1", root=base_root)
    schema_errors = validate_schema_metadata(artifact_schema, "atlas.qa.artifact.v1")
    if schema_errors:
        raise ValueError("; ".join(schema_errors))

    if result_path is None:
        if not run_id:
            raise ValueError("Provide result_path or run_id.")
        result_path = (default_run_root(root=base_root) / run_id / "matrix.result.json").resolve()
    result_payload = load_json_object(result_path.resolve())
    if result_payload.get("contract_version") != RESULT_CONTRACT_VERSION:
        raise ValueError("result_file must contain atlas.qa.result.v1.")
    result_errors = validate_result_payload(result_payload)
    if result_errors:
        raise ValueError("; ".join(result_errors))

    scenario_path = resolve_ref(str(result_payload["scenario_ref"]), root=base_root)
    scenario_payload = load_json_object(scenario_path)
    if isinstance(result_payload.get("adapter_ref"), str) and str(result_payload.get("adapter_ref")).strip():
        adapter_payload = load_json_object(resolve_ref(str(result_payload["adapter_ref"]), root=base_root))
    else:
        adapter_payload, _ = load_adapter_manifest(root=base_root, adapter_id=str(result_payload["adapter_id"]), repo_id=str(result_payload["repo_id"]))
    lens_payload, _ = load_lens_manifest(root=base_root, lens_manifest_ref=str(result_payload["lens_manifest_ref"]))
    lens_profiles = _lens_profile_map(lens_payload)
    override_map = _artifact_override_map(list(artifact_files or []), root=base_root)
    result_by_lens = _result_by_lens(result_payload)
    artifacts: list[dict[str, Any]] = []
    execute = not dry_run and result_payload.get("mode") == "execute"
    run_root = _find_run_root(result_path.resolve())
    repo_root = resolve_ref(str(result_payload["repo_path"]), root=base_root)
    attestation_by_lens, attestation_summaries = _load_attestations(
        root=base_root,
        run_root=run_root,
        attestation_files=list(attestation_files or []),
    )
    capture_results = _capture_cache(
        execute=execute,
        repo_root=repo_root,
        run_root=run_root,
        adapter=adapter_payload,
        scenario=scenario_payload,
        result_payload=result_payload,
        lens_payload=lens_payload,
        lens_profiles=lens_profiles,
        result_by_lens=result_by_lens,
    )

    for item in scenario_payload.get("required_artifacts", []):
        if not isinstance(item, dict):
            continue
        artifact_kind = str(item["artifact_kind"])
        step_id = str(item.get("step_id") or "default")
        for lens_id in item.get("required_lenses", []):
            lens_key = str(lens_id)
            matrix_entry = result_by_lens.get(lens_key, {})
            proof_kind = str(matrix_entry.get("proof_kind") or "emulated")
            lens_profile_id = str(matrix_entry.get("lens_profile_id") or "")
            lens_profile = lens_profiles.get(lens_profile_id, {})
            attestation = attestation_by_lens.get(lens_key)
            override = override_map.get((lens_key, artifact_kind))
            artifact_path: Path | None = None
            metadata_path: Path | None = None
            metadata_payload: dict[str, Any] | None = None
            status = "planned" if dry_run else "missing"

            if override is not None:
                artifact_path = override
                status = "present" if override.exists() else "missing"
            elif execute and matrix_entry.get("execution_mode") in {"browser_capture", "provider_capture"} and lens_key in capture_results:
                capture_result = capture_results[lens_key]
                metadata_path = Path(str(capture_result["metadata_path"])).resolve()
                metadata_payload = read_json(metadata_path)
                output_lookup = {
                    "screenshot": "screenshot",
                    "trace": "trace",
                    "console_log": "console_log",
                    "network_log": "network_log",
                }
                if artifact_kind in output_lookup and output_lookup[artifact_kind] in capture_result.get("outputs", {}):
                    artifact_path = Path(str(capture_result["outputs"][output_lookup[artifact_kind]])).resolve()
                    status = "present" if artifact_path.exists() else "missing"
                elif artifact_kind == "executable_report":
                    artifact_path = _write_executable_report(
                        run_root=run_root,
                        lens_id=lens_key,
                        result_payload=result_payload,
                        matrix_entry=matrix_entry,
                    )
                    metadata_payload = {
                        "run_id": result_payload["run_id"],
                        "scenario_id": scenario_payload["scenario_id"],
                        "adapter_id": result_payload["adapter_id"],
                        "repo_id": result_payload["repo_id"],
                        "git_sha": result_payload["git_sha"],
                        "captured_at": utc_now(),
                        "source_url": str(matrix_entry.get("url_target") or ""),
                        "capture_backend": "matrix-executable-report",
                    }
                    status = "present"
            elif execute and matrix_entry.get("execution_mode") == "repo_command" and artifact_kind == "executable_report":
                artifact_path = _write_executable_report(
                    run_root=run_root,
                    lens_id=lens_key,
                    result_payload=result_payload,
                    matrix_entry=matrix_entry,
                )
                metadata_payload = {
                    "run_id": result_payload["run_id"],
                    "scenario_id": scenario_payload["scenario_id"],
                    "adapter_id": result_payload["adapter_id"],
                    "repo_id": result_payload["repo_id"],
                    "git_sha": result_payload["git_sha"],
                    "captured_at": utc_now(),
                    "source_url": str(matrix_entry.get("url_target") or ""),
                    "capture_backend": "repo-command-report",
                }
                status = "present" if artifact_path.exists() else "missing"
            elif not dry_run and isinstance(attestation, dict) and attestation.get("status") == "valid":
                if artifact_kind == "screenshot":
                    screenshot_artifacts = scenario_payload.get("required_artifacts", [])
                    _ = screenshot_artifacts
                    attestation_payload = load_json_object(resolve_ref(str(attestation["attestation_ref"]), root=base_root))
                    screenshot_ref = next(
                        (
                            item
                            for item in attestation_payload.get("screenshot_artifacts", [])
                            if isinstance(item, dict)
                        ),
                        None,
                    )
                    if isinstance(screenshot_ref, dict):
                        artifact_path = resolve_ref(str(screenshot_ref["path_ref"]), root=base_root)
                        metadata_payload = {
                            "run_id": str(attestation_payload["run_id"]),
                            "scenario_id": str(attestation_payload["scenario_id"]),
                            "adapter_id": str(attestation_payload["adapter_id"]),
                            "repo_id": str(result_payload["repo_id"]),
                            "git_sha": str(result_payload["git_sha"]),
                            "captured_at": str(attestation_payload["capture_timestamp"]),
                            "source_url": str(matrix_entry.get("url_target") or ""),
                            "capture_backend": "manual-attestation",
                            "capture_method": "manual_attestation",
                            "operator": str(attestation_payload["operator"]),
                            "attestation_ref": str(attestation["attestation_ref"]),
                            "provider_id": "manual.attestation",
                            "provider_run_id": str(attestation_payload["attestation_id"]),
                            "device_model": str(attestation_payload["device_model"]),
                            "os_name": str(attestation_payload["os_name"]),
                            "os_version": str(attestation_payload["os_version"]),
                            "browser_name": str(attestation_payload["browser_name"]),
                            "browser_version": str(attestation_payload.get("browser_version") or ""),
                        }
                        status = "present" if artifact_path.exists() else "missing"
                else:
                    status = "manual_attested"
            elif not dry_run:
                if isinstance(matrix_entry, dict) and matrix_entry.get("status") == "manual_required":
                    status = "manual_required"
                elif proof_kind == "real":
                    status = "manual_required"

            artifact = {
                "artifact_id": f"{result_payload['run_id']}:{step_id}:{lens_key}:{artifact_kind}",
                "artifact_kind": artifact_kind,
                "step_id": step_id,
                "lens_id": lens_key,
                "proof_kind": proof_kind,
                "required": True,
                "status": status,
                "content_type": _content_type_for_kind(artifact_kind),
                "notes": [f"collector={RUNNER_VERSION}"],
            }
            if status == "manual_attested" and isinstance(attestation, dict):
                artifact["source_ref"] = str(attestation["attestation_ref"])
                artifact["notes"].append(f"attestation_id={attestation.get('attestation_id')}")
            if artifact_path is not None:
                artifact["path_ref"] = atlas_relative(artifact_path, root=base_root)
                if artifact_path.exists():
                    artifact["checksum_sha256"] = sha256_bytes(_read_bytes(artifact_path))
            if artifact_kind == "screenshot" and artifact_path is not None and artifact_path.exists() and isinstance(lens_profile, dict):
                artifact["evidence"] = _evidence_for_path(
                    artifact_path=artifact_path,
                    metadata_path=metadata_path,
                    lens_id=lens_key,
                    lens_profile=lens_profile,
                    metadata_payload=metadata_payload,
                )
            artifacts.append(artifact)

    lens_manifest_summary = {
        lens_id: {
            "browser_engine": str(payload["browser_engine"]),
            "viewport": dict(payload["viewport"]),
            "mobile": bool(payload["mobile"]),
            "has_touch": bool(payload["has_touch"]),
        }
        for lens_id, payload in lens_profiles.items()
    }
    body = {
        "contract_version": ARTIFACT_CONTRACT_VERSION,
        "generated_at": utc_now(),
        "run_id": str(result_payload["run_id"]),
        "scenario_id": str(scenario_payload["scenario_id"]),
        "adapter_id": str(result_payload["adapter_id"]),
        "repo_id": str(result_payload["repo_id"]),
        "repo_path": normalize_slashes(str(result_payload["repo_path"])),
        "stage": "planned" if dry_run else "collected",
        "mode": str(result_payload["mode"]),
        "evidence_grade": "dry_run" if dry_run else "evidence",
        "git_sha": str(result_payload["git_sha"]),
        "environment": {
            "execution_root": atlas_relative(run_root, root=base_root),
            "target_url": str(next(iter(result_by_lens.values()), {}).get("url_target") or ""),
        },
        "lenses": lens_manifest_summary,
        "attestations": attestation_summaries,
        "artifacts": artifacts,
        "summary": {
            "artifact_count": len(artifacts),
            "required_count": len(artifacts),
            "present_count": sum(1 for artifact in artifacts if artifact["status"] == "present"),
            "missing_count": sum(1 for artifact in artifacts if artifact["status"] == "missing"),
            "manual_required_count": sum(1 for artifact in artifacts if artifact["status"] == "manual_required"),
            "manual_attested_count": sum(1 for artifact in artifacts if artifact["status"] == "manual_attested"),
            "invalid_count": 0,
        },
    }
    manifest = payload_with_digest(body, "artifact_manifest_id")
    manifest_errors = validate_artifact_manifest(manifest)
    if manifest_errors:
        raise ValueError("; ".join(manifest_errors))

    target = output_file.resolve() if isinstance(output_file, Path) else result_path.with_name("artifacts.manifest.json")
    write_manifest(target, manifest)
    return manifest | {"output_ref": atlas_relative(target, root=base_root)}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Collect or plan ATLAS QA artifact manifests.")
    parser.add_argument("--root", type=Path, default=atlas_root())
    parser.add_argument("--result-file", type=Path)
    parser.add_argument("--run")
    parser.add_argument("--artifact-file", action="append", default=[])
    parser.add_argument("--attestation-file", action="append", default=[])
    parser.add_argument("--output-file", type=Path)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args(argv)

    result = collect_artifacts(
        root=args.root.resolve(),
        result_path=args.result_file.resolve() if isinstance(args.result_file, Path) else None,
        run_id=args.run,
        artifact_files=list(args.artifact_file),
        attestation_files=list(args.attestation_file),
        output_file=args.output_file.resolve() if isinstance(args.output_file, Path) else None,
        dry_run=bool(args.dry_run),
    )
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
