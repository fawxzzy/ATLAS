from __future__ import annotations

import json
import os
import platform
from hashlib import sha256
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping
from urllib.parse import urlsplit

from ops._atlas import atlas_relative, atlas_root, load_repo_registry, normalize_slashes
from ops.cortex._artifacts import stable_json_digest, write_json

QA_LLEL_VERSION = "1.0.0"
RUNNER_CONTRACT_VERSION = "atlas.qa.llel.v1"
SCENARIO_CONTRACT_VERSION = "atlas.qa.scenario.v1"
ARTIFACT_CONTRACT_VERSION = "atlas.qa.artifact.v1"
RESULT_CONTRACT_VERSION = "atlas.qa.result.v1"
PROMOTION_CONTRACT_VERSION = "atlas.qa.promotion.v1"
LENS_CONTRACT_VERSION = "atlas.qa.lens.v1"
PROVIDER_CONTRACT_VERSION = "atlas.qa.provider.v1"
MANUAL_ATTESTATION_CONTRACT_VERSION = "atlas.qa.manual_attestation.v1"
WAIVER_CONTRACT_VERSION = "atlas.qa.waiver.v1"
ADAPTER_CONTRACT_VERSION = "atlas.qa.adapter.v1"
CAPTURE_RECEIPT_CONTRACT_VERSION = "atlas.qa.capture_receipt.v1"
TEST_EVIDENCE_CONTRACT_VERSION = "atlas.qa.test_evidence.v1"
VISUAL_BASELINE_CONTRACT_VERSION = "atlas.qa.visual_baseline.v1"
EVIDENCE_INDEX_CONTRACT_VERSION = "atlas.qa.evidence_index.v1"
SCHEMA_IDS = {
    ADAPTER_CONTRACT_VERSION: "atlas://schemas/atlas.qa.adapter.v1.json",
    SCENARIO_CONTRACT_VERSION: "atlas://schemas/atlas.qa.scenario.v1.json",
    ARTIFACT_CONTRACT_VERSION: "atlas://schemas/atlas.qa.artifact.v1.json",
    RESULT_CONTRACT_VERSION: "atlas://schemas/atlas.qa.result.v1.json",
    PROMOTION_CONTRACT_VERSION: "atlas://schemas/atlas.qa.promotion.v1.json",
    LENS_CONTRACT_VERSION: "atlas://schemas/atlas.qa.lens.v1.json",
    PROVIDER_CONTRACT_VERSION: "atlas://schemas/atlas.qa.provider.v1.json",
    MANUAL_ATTESTATION_CONTRACT_VERSION: "atlas://schemas/atlas.qa.manual_attestation.v1.json",
    WAIVER_CONTRACT_VERSION: "atlas://schemas/atlas.qa.waiver.v1.json",
    CAPTURE_RECEIPT_CONTRACT_VERSION: "atlas://schemas/atlas.qa.capture_receipt.v1.json",
    TEST_EVIDENCE_CONTRACT_VERSION: "atlas://schemas/atlas.qa.test_evidence.v1.json",
    VISUAL_BASELINE_CONTRACT_VERSION: "atlas://schemas/atlas.qa.visual_baseline.v1.json",
    EVIDENCE_INDEX_CONTRACT_VERSION: "atlas://schemas/atlas.qa.evidence_index.v1.json",
}
SCHEMA_TITLES = {
    ADAPTER_CONTRACT_VERSION: "ATLAS QA adapter v1",
    SCENARIO_CONTRACT_VERSION: "ATLAS QA scenario v1",
    ARTIFACT_CONTRACT_VERSION: "ATLAS QA artifact manifest v1",
    RESULT_CONTRACT_VERSION: "ATLAS QA result v1",
    PROMOTION_CONTRACT_VERSION: "ATLAS QA promotion v1",
    LENS_CONTRACT_VERSION: "ATLAS QA lens manifest v1",
    PROVIDER_CONTRACT_VERSION: "ATLAS QA provider v1",
    MANUAL_ATTESTATION_CONTRACT_VERSION: "ATLAS QA manual attestation v1",
    WAIVER_CONTRACT_VERSION: "ATLAS QA waiver v1",
    CAPTURE_RECEIPT_CONTRACT_VERSION: "ATLAS QA capture receipt v1",
    TEST_EVIDENCE_CONTRACT_VERSION: "ATLAS QA test evidence v1",
    VISUAL_BASELINE_CONTRACT_VERSION: "ATLAS QA visual baseline v1",
    EVIDENCE_INDEX_CONTRACT_VERSION: "ATLAS QA evidence index v1",
}
ARTIFACT_KINDS = {
    "screenshot",
    "trace",
    "console_log",
    "network_log",
    "video",
    "executable_report",
    "api_report",
    "manual_note",
}
PROOF_KINDS = {"emulated", "real"}
EVIDENCE_TIERS = {"dry_run", "emulated_browser", "physical_device", "manual_attestation"}
EVIDENCE_PROFILES = {"web_visual", "package_contract", "docs_governance"}
EXECUTION_MODES = {"repo_command", "manual_external", "browser_capture", "provider_capture"}
TEST_RUNNERS = {"pytest", "unittest", "jest", "vitest", "npm", "custom"}
RECEIPT_ORIGIN_TYPES = {"local_dev", "ci_pr", "ci_release", "protected_manual", "provider"}
PROMOTION_STATUSES = {
    "dry_run",
    "blocked",
    "manual_review",
    "promoted_emulated",
    "promoted_physical",
    "promoted_physical_manual",
    "waived_promoted",
}
RESULT_STAGES = {"planned", "executed", "evaluated"}
ARTIFACT_STAGES = {"planned", "collected"}
PROMOTION_DECISIONS = {"promote", "hold", "manual_review"}
PROMOTION_DISPLAY_STATUSES = {
    "dry_run",
    "blocked",
    "manual_review",
    "promoted_contract",
    "promoted_docs_governance",
    "promoted_web_visual",
    "promoted_physical",
    "promoted_physical_manual",
    "waived_promoted",
}


def _is_relative_to(path: Path, base: Path) -> bool:
    try:
        path.resolve().relative_to(base.resolve())
        return True
    except ValueError:
        return False


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def stamp_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")


def load_json_object(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"Expected JSON object at {normalize_slashes(str(path))}.")
    return payload


def resolve_ref(ref: str | Path, *, root: Path) -> Path:
    candidate = Path(ref)
    return candidate.resolve() if candidate.is_absolute() else (root / candidate).resolve()


def _is_loopback_url(url: str) -> bool:
    try:
        hostname = (urlsplit(str(url).strip()).hostname or "").strip().lower()
    except ValueError:
        return False
    return hostname in {"127.0.0.1", "::1", "localhost"}


def resolve_execution_target_url(
    url: str,
    *,
    execution_mode: str,
    env: Mapping[str, str] | None = None,
) -> str:
    target_url = str(url).strip()
    if not target_url:
        return ""
    if execution_mode != "provider_capture" or not _is_loopback_url(target_url):
        return target_url.rstrip("/")

    env_map = env or os.environ
    override_url = (
        str(env_map.get("ATLAS_QA_PROVIDER_BASE_URL", "")).strip()
        or str(env_map.get("FITNESS_QA_TUNNEL_URL", "")).strip()
    )
    return override_url.rstrip("/") if override_url else target_url.rstrip("/")


def default_schema_path(contract_version: str, *, root: Path | None = None) -> Path:
    base = (root or atlas_root()).resolve()
    filename = f"{contract_version}.json"
    return base / "schemas" / filename


def default_adapter_dir(*, root: Path | None = None) -> Path:
    base = (root or atlas_root()).resolve()
    return base / "ops" / "atlas" / "qa" / "adapters"


def default_scenario_dir(*, root: Path | None = None) -> Path:
    base = (root or atlas_root()).resolve()
    return base / "ops" / "atlas" / "qa" / "scenarios"


def default_run_root(*, root: Path | None = None) -> Path:
    base = (root or atlas_root()).resolve()
    return base / "runtime" / "atlas" / "qa" / "runs"


def default_lens_dir(*, root: Path | None = None) -> Path:
    base = (root or atlas_root()).resolve()
    return base / "ops" / "atlas" / "qa" / "lenses"


def default_provider_dir(*, root: Path | None = None) -> Path:
    base = (root or atlas_root()).resolve()
    return base / "ops" / "atlas" / "qa" / "providers"


def default_baseline_dir(*, root: Path | None = None) -> Path:
    base = (root or atlas_root()).resolve()
    return base / "data" / "atlas" / "qa" / "baselines"


def default_evidence_index_path(*, root: Path | None = None) -> Path:
    base = (root or atlas_root()).resolve()
    return base / "runtime" / "atlas" / "qa" / "evidence-index.latest.json"


def default_release_policy_path(*, root: Path | None = None) -> Path:
    base = (root or atlas_root()).resolve()
    return base / "ops" / "atlas" / "qa" / "release_policy.v1.json"


def default_release_readiness_path(*, root: Path | None = None) -> Path:
    base = (root or atlas_root()).resolve()
    return base / "runtime" / "atlas" / "qa" / "release-readiness.latest.json"


def default_adoption_drift_path(*, root: Path | None = None) -> Path:
    base = (root or atlas_root()).resolve()
    return base / "runtime" / "atlas" / "qa" / "adoption-drift.latest.json"


def default_run_waiver_dir(*, root: Path | None = None, run_id: str) -> Path:
    return default_run_root(root=root) / run_id / "waivers"


def baseline_manifest_path(image_path: Path) -> Path:
    return image_path.with_suffix(".baseline.json")


def normalize_contract_version(value: Any) -> str:
    return str(value).strip() if value is not None else ""


def stack_lock_hash(*, root: Path | None = None) -> str:
    base = (root or atlas_root()).resolve()
    target = base / "stack.lock.yaml"
    if not target.exists():
        return ""
    return f"sha256:{sha256(target.read_bytes()).hexdigest()}"


def _default_receipt_origin_type() -> str:
    return resolve_receipt_origin_type()


def resolve_receipt_origin_type(origin_type: str | None = None) -> str:
    explicit = str(origin_type or "").strip()
    override = str(os.environ.get("ATLAS_QA_ORIGIN_TYPE", "")).strip()
    github_actions = str(os.environ.get("GITHUB_ACTIONS", "")).lower() == "true"

    if github_actions:
        if explicit in RECEIPT_ORIGIN_TYPES:
            return explicit
        if override in RECEIPT_ORIGIN_TYPES:
            return override
        event_name = str(os.environ.get("GITHUB_EVENT_NAME", "")).strip().lower()
        if event_name == "pull_request":
            return "ci_pr"
        if event_name == "workflow_dispatch":
            return "protected_manual"
        return "ci_release"

    if explicit == "local_dev" or override == "local_dev":
        return "local_dev"
    return "local_dev"


def build_receipt_origin(
    *,
    root: Path | None = None,
    runner_version: str,
    repo_id: str,
    git_sha: str,
    command: str = "",
    origin_type: str | None = None,
) -> dict[str, str]:
    base = (root or atlas_root()).resolve()
    resolved_origin = resolve_receipt_origin_type(origin_type)
    actor = (
        str(os.environ.get("GITHUB_ACTOR", "")).strip()
        or str(os.environ.get("USERNAME", "")).strip()
        or str(os.environ.get("USER", "")).strip()
        or "unknown"
    )
    return {
        "origin_type": resolved_origin,
        "actor": actor,
        "workflow_name": str(os.environ.get("GITHUB_WORKFLOW", "")).strip(),
        "workflow_run_id": str(os.environ.get("GITHUB_RUN_ID", "")).strip(),
        "command": command.strip(),
        "runner_os": platform.platform(),
        "generated_at": utc_now(),
        "repo": repo_id.strip(),
        "git_sha": git_sha.strip(),
        "stack_lock_hash": stack_lock_hash(root=base),
        "qa_runner_version": runner_version.strip(),
    }


def validate_receipt_origin(value: Any) -> list[str]:
    if value is None:
        return []
    if not isinstance(value, dict):
        return ["receipt_origin must be an object when present."]
    errors: list[str] = []
    origin_type = value.get("origin_type")
    if not isinstance(origin_type, str) or origin_type not in RECEIPT_ORIGIN_TYPES:
        errors.append("receipt_origin.origin_type must be one of: local_dev, ci_pr, ci_release, protected_manual, provider.")
    for key in ("actor", "runner_os", "generated_at", "repo", "git_sha", "qa_runner_version"):
        item = value.get(key)
        if not isinstance(item, str) or not item.strip():
            errors.append(f"receipt_origin.{key} must be a non-empty string.")
    for key in ("workflow_name", "workflow_run_id", "command", "stack_lock_hash"):
        item = value.get(key)
        if item is not None and not isinstance(item, str):
            errors.append(f"receipt_origin.{key} must be a string when present.")
    return errors


def validate_declared_contract_version(value: Any, expected: str) -> list[str]:
    declared = normalize_contract_version(value)
    if not declared:
        return ["contract_version must be a non-empty string."]
    if declared != expected:
        if declared in SCHEMA_IDS:
            return [f"contract_version must be '{expected}', found '{declared}'."]
        return [f"contract_version '{declared}' is not supported by ATLAS QA LLEL {QA_LLEL_VERSION}; expected '{expected}'."]
    return []


def compatibility_summary(*, adapter_payload: dict[str, Any] | None = None, scenario_payload: dict[str, Any] | None = None) -> dict[str, Any]:
    providers = sorted(
        path.stem
        for path in default_provider_dir().glob("*.json")
        if path.name != "base.py"
    )
    return {
        "llel_version": QA_LLEL_VERSION,
        "runner_contract_version": RUNNER_CONTRACT_VERSION,
        "schema_versions": {key: SCHEMA_IDS[key] for key in sorted(SCHEMA_IDS)},
        "adapter_version": None if adapter_payload is None else adapter_payload.get("contract_version"),
        "scenario_version": None if scenario_payload is None else scenario_payload.get("contract_version"),
        "evidence_tier_support": sorted(EVIDENCE_TIERS),
        "provider_support": providers,
    }


def derive_evidence_profile(
    *,
    scenario_payload: dict[str, Any] | None = None,
    adapter_payload: dict[str, Any] | None = None,
    matrix: list[dict[str, Any]] | None = None,
) -> str:
    scenario = scenario_payload if isinstance(scenario_payload, dict) else {}
    adapter = adapter_payload if isinstance(adapter_payload, dict) else {}
    lane_matrix = matrix if isinstance(matrix, list) else []

    if any(
        isinstance(item, dict) and item.get("execution_mode") in {"browser_capture", "provider_capture"}
        for item in lane_matrix
    ):
        return "web_visual"

    if any(
        isinstance(item, dict) and item.get("execution_mode") in {"browser_capture", "provider_capture"}
        for item in adapter.get("lenses", [])
        if isinstance(item, dict)
    ):
        return "web_visual"

    visual_assertions = scenario.get("visual_assertions")
    if isinstance(visual_assertions, list) and visual_assertions:
        return "web_visual"

    framework = str(adapter.get("framework") or "").strip()
    tags = {
        str(item).strip().lower()
        for item in scenario.get("tags", [])
        if isinstance(item, str) and item.strip()
    }
    if framework in {"docs-or-governance", "docs-or-runtime"} or {"docs", "governance"} & tags:
        return "docs_governance"

    return "package_contract"


def display_promotion_status(*, promotion_status: str, evidence_profile: str) -> str:
    status = promotion_status.strip()
    profile = evidence_profile.strip()
    if status != "promoted_emulated":
        return status
    if profile == "docs_governance":
        return "promoted_docs_governance"
    if profile == "package_contract":
        return "promoted_contract"
    if profile == "web_visual":
        return "promoted_web_visual"
    return status


def validate_schema_metadata(schema: dict[str, Any], contract_version: str) -> list[str]:
    errors: list[str] = []
    if contract_version not in SCHEMA_IDS:
        errors.append(f"Unsupported contract_version '{contract_version}'.")
        return errors
    if schema.get("$schema") != "https://json-schema.org/draft/2020-12/schema":
        errors.append("Schema $schema must target draft 2020-12.")
    if schema.get("$id") != SCHEMA_IDS[contract_version]:
        errors.append(f"Schema $id must be '{SCHEMA_IDS[contract_version]}'.")
    if schema.get("title") != SCHEMA_TITLES[contract_version]:
        errors.append(f"Schema title must be '{SCHEMA_TITLES[contract_version]}'.")
    if schema.get("type") != "object":
        errors.append("Schema root type must be object.")
    if schema.get("additionalProperties") is not False:
        errors.append("Schema root must set additionalProperties to false.")
    return errors


def validate_scenario_manifest(
    payload: dict[str, Any],
    *,
    root: Path,
    require_repo_path_exists: bool = True,
) -> list[str]:
    errors: list[str] = []
    errors.extend(validate_declared_contract_version(payload.get("contract_version"), SCENARIO_CONTRACT_VERSION))
    for key in ("scenario_id", "title", "repo_id", "repo_path", "adapter_id", "criticality"):
        value = payload.get(key)
        if not isinstance(value, str) or not value.strip():
            errors.append(f"{key} must be a non-empty string.")
    repo_path = payload.get("repo_path")
    if (
        require_repo_path_exists
        and isinstance(repo_path, str)
        and repo_path.strip()
        and not resolve_ref(repo_path, root=root).exists()
    ):
        errors.append(f"repo_path does not exist: {repo_path}")
    criticality = payload.get("criticality")
    if criticality not in {"low", "medium", "high", "critical"}:
        errors.append("criticality must be one of: low, medium, high, critical.")
    entrypoint = payload.get("entrypoint")
    if not isinstance(entrypoint, dict):
        errors.append("entrypoint must be an object.")
    else:
        path_value = entrypoint.get("path")
        if not isinstance(path_value, str) or not path_value.strip():
            errors.append("entrypoint.path must be a non-empty string.")
    proof = payload.get("proof")
    if not isinstance(proof, dict):
        errors.append("proof must be an object.")
    else:
        for key in ("pr_lenses", "certify_lenses"):
            value = proof.get(key)
            if not isinstance(value, list):
                errors.append(f"proof.{key} must be an array.")
            elif key == "pr_lenses" and not value:
                errors.append("proof.pr_lenses must contain at least one lens.")
        lens_manifest_ref = proof.get("lens_manifest_ref")
        if not isinstance(lens_manifest_ref, str) or not lens_manifest_ref.strip():
            errors.append("proof.lens_manifest_ref must be a non-empty string.")
        elif not resolve_ref(lens_manifest_ref, root=root).exists():
            errors.append(f"proof.lens_manifest_ref does not exist: {lens_manifest_ref}")
    required_artifacts = payload.get("required_artifacts")
    if not isinstance(required_artifacts, list) or not required_artifacts:
        errors.append("required_artifacts must be a non-empty array.")
    else:
        for index, item in enumerate(required_artifacts):
            path = f"required_artifacts[{index}]"
            if not isinstance(item, dict):
                errors.append(f"{path} must be an object.")
                continue
            artifact_kind = item.get("artifact_kind")
            if artifact_kind not in ARTIFACT_KINDS:
                errors.append(f"{path}.artifact_kind must be a supported artifact kind.")
            lenses = item.get("required_lenses")
            if not isinstance(lenses, list) or not lenses:
                errors.append(f"{path}.required_lenses must be a non-empty array.")
    execution = payload.get("execution")
    if not isinstance(execution, dict):
        errors.append("execution must be an object.")
    else:
        for key in ("pr_command_sequence", "certify_command_sequence"):
            value = execution.get(key)
            if not isinstance(value, list):
                errors.append(f"execution.{key} must be an array.")
        preflight = execution.get("preflight_command_sequence")
        if preflight is not None and not isinstance(preflight, list):
            errors.append("execution.preflight_command_sequence must be an array when present.")
    promotion = payload.get("promotion")
    if not isinstance(promotion, dict):
        errors.append("promotion must be an object.")
    visual_assertions = payload.get("visual_assertions")
    if visual_assertions is not None:
        if not isinstance(visual_assertions, list):
            errors.append("visual_assertions must be an array when present.")
        else:
            baseline_root = default_baseline_dir(root=root)
            for index, item in enumerate(visual_assertions):
                path = f"visual_assertions[{index}]"
                if not isinstance(item, dict):
                    errors.append(f"{path} must be an object.")
                    continue
                lens_id = item.get("lens_id")
                if not isinstance(lens_id, str) or not lens_id.strip():
                    errors.append(f"{path}.lens_id must be a non-empty string.")
                baseline_ref = item.get("baseline_ref")
                if not isinstance(baseline_ref, str) or not baseline_ref.strip():
                    errors.append(f"{path}.baseline_ref must be a non-empty string.")
                else:
                    if Path(baseline_ref).is_absolute():
                        errors.append(f"{path}.baseline_ref must be relative to the ATLAS root.")
                    baseline_path = resolve_ref(baseline_ref, root=root)
                    if not _is_relative_to(baseline_path, baseline_root):
                        errors.append(f"{path}.baseline_ref must live under {atlas_relative(baseline_root, root=root)}.")
                max_pixel_delta = item.get("max_pixel_delta")
                if not isinstance(max_pixel_delta, int) or max_pixel_delta < 0:
                    errors.append(f"{path}.max_pixel_delta must be a non-negative integer.")
                ignored_regions = item.get("ignored_regions")
                if ignored_regions is not None:
                    if not isinstance(ignored_regions, list):
                        errors.append(f"{path}.ignored_regions must be an array when present.")
                    else:
                        for region_index, region in enumerate(ignored_regions):
                            region_path = f"{path}.ignored_regions[{region_index}]"
                            if not isinstance(region, dict):
                                errors.append(f"{region_path} must be an object.")
                                continue
                            for key in ("x", "y", "width", "height"):
                                value = region.get(key)
                                if not isinstance(value, int) or value < 0 or (key in {"width", "height"} and value <= 0):
                                    errors.append(f"{region_path}.{key} must be a non-negative integer and width/height must be positive.")
                ignored_selectors = item.get("ignored_selectors")
                if ignored_selectors is not None:
                    if not isinstance(ignored_selectors, list):
                        errors.append(f"{path}.ignored_selectors must be an array when present.")
                    else:
                        for selector_index, selector in enumerate(ignored_selectors):
                            if not isinstance(selector, str) or not selector.strip():
                                errors.append(f"{path}.ignored_selectors[{selector_index}] must be a non-empty string.")
    test_evidence = payload.get("test_evidence")
    if test_evidence is not None:
        if not isinstance(test_evidence, list):
            errors.append("test_evidence must be an array when present.")
        else:
            for index, item in enumerate(test_evidence):
                path = f"test_evidence[{index}]"
                if not isinstance(item, dict):
                    errors.append(f"{path} must be an object.")
                    continue
                for key in ("evidence_id", "command_ref", "runner", "kind"):
                    value = item.get(key)
                    if not isinstance(value, str) or not value.strip():
                        errors.append(f"{path}.{key} must be a non-empty string.")
                runner = item.get("runner")
                if runner not in TEST_RUNNERS:
                    errors.append(f"{path}.runner must be one of: {', '.join(sorted(TEST_RUNNERS))}.")
                required_for = item.get("required_for")
                if not isinstance(required_for, list) or not required_for:
                    errors.append(f"{path}.required_for must be a non-empty array.")
                elif any(value not in {"evidence", "promotion"} for value in required_for):
                    errors.append(f"{path}.required_for may contain only 'evidence' or 'promotion'.")
    return errors


def validate_artifact_manifest(payload: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    errors.extend(validate_declared_contract_version(payload.get("contract_version"), ARTIFACT_CONTRACT_VERSION))
    if payload.get("stage") not in ARTIFACT_STAGES:
        errors.append("stage must be 'planned' or 'collected'.")
    if payload.get("mode") not in {"dry_run", "execute"}:
        errors.append("mode must be 'dry_run' or 'execute'.")
    if payload.get("evidence_grade") not in {"dry_run", "evidence"}:
        errors.append("evidence_grade must be 'dry_run' or 'evidence'.")
    attestations = payload.get("attestations")
    if attestations is not None and not isinstance(attestations, list):
        errors.append("attestations must be an array when present.")
    artifacts = payload.get("artifacts")
    if not isinstance(artifacts, list):
        errors.append("artifacts must be an array.")
    else:
        for index, item in enumerate(artifacts):
            path = f"artifacts[{index}]"
            if not isinstance(item, dict):
                errors.append(f"{path} must be an object.")
                continue
            if item.get("artifact_kind") not in ARTIFACT_KINDS:
                errors.append(f"{path}.artifact_kind must be a supported artifact kind.")
            if item.get("proof_kind") not in PROOF_KINDS:
                errors.append(f"{path}.proof_kind must be 'emulated' or 'real'.")
            if item.get("status") not in {"planned", "present", "missing", "skipped", "manual_required", "manual_attested"}:
                errors.append(f"{path}.status must be planned, present, missing, skipped, manual_required, or manual_attested.")
            evidence = item.get("evidence")
            if evidence is not None and not isinstance(evidence, dict):
                errors.append(f"{path}.evidence must be an object when present.")
    return errors


def validate_result_payload(payload: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    errors.extend(validate_declared_contract_version(payload.get("contract_version"), RESULT_CONTRACT_VERSION))
    if payload.get("stage") not in RESULT_STAGES:
        errors.append("stage must be planned, executed, or evaluated.")
    if payload.get("mode") not in {"dry_run", "execute"}:
        errors.append("mode must be 'dry_run' or 'execute'.")
    matrix = payload.get("matrix")
    if not isinstance(matrix, list):
        errors.append("matrix must be an array.")
    summary = payload.get("summary")
    if not isinstance(summary, dict):
        errors.append("summary must be an object.")
    findings = payload.get("findings")
    if not isinstance(findings, list):
        errors.append("findings must be an array.")
    artifact_refs = payload.get("artifact_manifest_refs")
    if not isinstance(artifact_refs, list):
        errors.append("artifact_manifest_refs must be an array.")
    summary = payload.get("summary") if isinstance(payload.get("summary"), dict) else {}
    if summary:
        if summary.get("certification_status") not in {"planned", "satisfied", "manual_required", "manual_attested", "missing"}:
            errors.append("summary.certification_status must be planned, satisfied, manual_required, manual_attested, or missing.")
        if summary.get("highest_satisfied_tier") is not None and summary.get("highest_satisfied_tier") not in EVIDENCE_TIERS:
            errors.append("summary.highest_satisfied_tier must be a supported evidence tier when present.")
        if summary.get("visual_status") is not None and summary.get("visual_status") not in {"not_configured", "planned", "passed", "baseline_required", "failed"}:
            errors.append("summary.visual_status must be not_configured, planned, passed, baseline_required, or failed when present.")
        if summary.get("test_evidence_status") is not None and summary.get("test_evidence_status") not in {"not_configured", "planned", "clean", "failed", "missing"}:
            errors.append("summary.test_evidence_status must be not_configured, planned, clean, failed, or missing when present.")
        if summary.get("evidence_profile") is not None and summary.get("evidence_profile") not in EVIDENCE_PROFILES:
            errors.append("summary.evidence_profile must be web_visual, package_contract, or docs_governance when present.")
        for key in ("satisfied_evidence_tiers", "missing_evidence_tiers", "manual_required_lanes"):
            value = summary.get(key)
            if value is not None and not isinstance(value, list):
                errors.append(f"summary.{key} must be an array when present.")
        visual_diff_count = summary.get("visual_diff_count")
        if visual_diff_count is not None and (not isinstance(visual_diff_count, int) or visual_diff_count < 0):
            errors.append("summary.visual_diff_count must be a non-negative integer when present.")
        required_test_evidence_count = summary.get("required_test_evidence_count")
        if required_test_evidence_count is not None and (not isinstance(required_test_evidence_count, int) or required_test_evidence_count < 0):
            errors.append("summary.required_test_evidence_count must be a non-negative integer when present.")
    visual_diffs = payload.get("visual_diffs")
    if visual_diffs is not None and not isinstance(visual_diffs, list):
        errors.append("visual_diffs must be an array when present.")
    test_evidence_refs = payload.get("test_evidence_refs")
    if test_evidence_refs is not None and not isinstance(test_evidence_refs, list):
        errors.append("test_evidence_refs must be an array when present.")
    errors.extend(validate_receipt_origin(payload.get("receipt_origin")))
    return errors


def validate_promotion_payload(payload: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    errors.extend(validate_declared_contract_version(payload.get("contract_version"), PROMOTION_CONTRACT_VERSION))
    if payload.get("decision") not in PROMOTION_DECISIONS:
        errors.append("decision must be promote, hold, or manual_review.")
    if payload.get("promotion_status") not in PROMOTION_STATUSES:
        errors.append("promotion_status must be a supported promotion status.")
    if payload.get("highest_satisfied_tier") is not None and payload.get("highest_satisfied_tier") not in EVIDENCE_TIERS:
        errors.append("highest_satisfied_tier must be a supported evidence tier when present.")
    if payload.get("evidence_profile") is not None and payload.get("evidence_profile") not in EVIDENCE_PROFILES:
        errors.append("evidence_profile must be web_visual, package_contract, or docs_governance when present.")
    for key in ("satisfied_evidence_tiers", "missing_evidence_tiers", "manual_required_lanes", "waived_lanes", "waiver_refs", "waiver_reasons"):
        value = payload.get(key)
        if value is not None and not isinstance(value, list):
            errors.append(f"{key} must be an array when present.")
    source_refs = payload.get("source_refs")
    if not isinstance(source_refs, dict):
        errors.append("source_refs must be an object.")
    errors.extend(validate_receipt_origin(payload.get("receipt_origin")))
    return errors


def validate_lens_manifest(payload: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    errors.extend(validate_declared_contract_version(payload.get("contract_version"), LENS_CONTRACT_VERSION))
    if not isinstance(payload.get("lens_set_id"), str) or not str(payload.get("lens_set_id")).strip():
        errors.append("lens_set_id must be a non-empty string.")
    lenses = payload.get("lenses")
    if not isinstance(lenses, list) or not lenses:
        errors.append("lenses must be a non-empty array.")
        return errors
    seen: set[str] = set()
    for index, lens in enumerate(lenses):
        path = f"lenses[{index}]"
        if not isinstance(lens, dict):
            errors.append(f"{path} must be an object.")
            continue
        lens_id = lens.get("lens_id")
        if not isinstance(lens_id, str) or not lens_id.strip():
            errors.append(f"{path}.lens_id must be a non-empty string.")
            continue
        if lens_id in seen:
            errors.append(f"{path}.lens_id '{lens_id}' is duplicated.")
        else:
            seen.add(lens_id)
        if lens.get("browser_engine") not in {"chromium", "webkit", "firefox"}:
            errors.append(f"{path}.browser_engine must be chromium, webkit, or firefox.")
        viewport = lens.get("viewport")
        if not isinstance(viewport, dict):
            errors.append(f"{path}.viewport must be an object.")
            continue
        for key in ("width", "height"):
            value = viewport.get(key)
            if not isinstance(value, int) or value <= 0:
                errors.append(f"{path}.viewport.{key} must be a positive integer.")
        dpr = viewport.get("device_scale_factor")
        if not isinstance(dpr, (int, float)) or dpr <= 0:
            errors.append(f"{path}.viewport.device_scale_factor must be a positive number.")
        for key in ("mobile", "has_touch"):
            if not isinstance(lens.get(key), bool):
                errors.append(f"{path}.{key} must be a boolean.")
    return errors


def validate_provider_manifest(payload: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    errors.extend(validate_declared_contract_version(payload.get("contract_version"), PROVIDER_CONTRACT_VERSION))
    for key in ("provider_id", "provider_type"):
        value = payload.get(key)
        if not isinstance(value, str) or not value.strip():
            errors.append(f"{key} must be a non-empty string.")
    auth_env_vars = payload.get("auth_env_vars")
    if auth_env_vars is not None and not isinstance(auth_env_vars, list):
        errors.append("auth_env_vars must be an array when present.")
    supported_lenses = payload.get("supported_lenses")
    if not isinstance(supported_lenses, list) or not supported_lenses:
        errors.append("supported_lenses must be a non-empty array.")
    artifact_capabilities = payload.get("artifact_capabilities")
    if not isinstance(artifact_capabilities, list) or not artifact_capabilities:
        errors.append("artifact_capabilities must be a non-empty array.")
    else:
        for item in artifact_capabilities:
            if item not in ARTIFACT_KINDS:
                errors.append("artifact_capabilities must use supported artifact kinds only.")
                break
    return errors


def validate_manual_attestation(payload: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    errors.extend(validate_declared_contract_version(payload.get("contract_version"), MANUAL_ATTESTATION_CONTRACT_VERSION))
    required_strings = (
        "attestation_id",
        "operator",
        "operator_identity",
        "scenario_id",
        "adapter_id",
        "run_id",
        "lens_id",
        "device_model",
        "os_name",
        "os_version",
        "browser_name",
        "capture_timestamp",
        "expires_at",
    )
    for key in required_strings:
        value = payload.get(key)
        if not isinstance(value, str) or not value.strip():
            errors.append(f"{key} must be a non-empty string.")
    screenshots = payload.get("screenshot_artifacts")
    if not isinstance(screenshots, list) or not screenshots:
        errors.append("screenshot_artifacts must be a non-empty array.")
    else:
        for index, item in enumerate(screenshots):
            path = f"screenshot_artifacts[{index}]"
            if not isinstance(item, dict):
                errors.append(f"{path} must be an object.")
                continue
            if not isinstance(item.get("path_ref"), str) or not str(item.get("path_ref")).strip():
                errors.append(f"{path}.path_ref must be a non-empty string.")
            checksum = item.get("checksum_sha256")
            if not isinstance(checksum, str) or not checksum.startswith("sha256:"):
                errors.append(f"{path}.checksum_sha256 must be a sha256 digest string.")
    notes = payload.get("notes")
    if notes is not None and not isinstance(notes, list):
        errors.append("notes must be an array when present.")
    supporting = payload.get("supporting_artifacts")
    if supporting is not None and not isinstance(supporting, list):
        errors.append("supporting_artifacts must be an array when present.")
    return errors


def validate_waiver_payload(payload: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    errors.extend(validate_declared_contract_version(payload.get("contract_version"), WAIVER_CONTRACT_VERSION))
    required_strings = (
        "waiver_id",
        "repo_id",
        "scenario_id",
        "run_id",
        "waived_lane",
        "reason",
        "operator",
        "created_at",
        "expires_at",
        "limitation",
    )
    for key in required_strings:
        value = payload.get(key)
        if not isinstance(value, str) or not value.strip():
            errors.append(f"{key} must be a non-empty string.")
    evidence_present = payload.get("evidence_present")
    if not isinstance(evidence_present, list) or not evidence_present:
        errors.append("evidence_present must be a non-empty array.")
    else:
        for index, item in enumerate(evidence_present):
            if not isinstance(item, str) or not item.strip():
                errors.append(f"evidence_present[{index}] must be a non-empty string.")
    for key in ("notes",):
        value = payload.get(key)
        if value is not None and not isinstance(value, list):
            errors.append(f"{key} must be an array when present.")
    return errors


def load_schema(contract_version: str, *, root: Path) -> dict[str, Any]:
    return load_json_object(default_schema_path(contract_version, root=root))


def validate_schema_definition(contract_version: str, *, root: Path) -> list[str]:
    schema = load_schema(contract_version, root=root)
    return validate_schema_metadata(schema, contract_version)


def load_adapter_manifest(
    *,
    root: Path,
    adapter_id: str | None = None,
    repo_id: str | None = None,
    adapter_dir: Path | None = None,
) -> tuple[dict[str, Any], Path]:
    base_dir = (adapter_dir or default_adapter_dir(root=root)).resolve()
    if adapter_id:
        path = base_dir / f"{adapter_id}.json"
        if path.exists():
            payload = load_json_object(path)
            return payload, path
    for path in sorted(base_dir.glob("*.json")):
        payload = load_json_object(path)
        if adapter_id and payload.get("adapter_id") == adapter_id:
            return payload, path
        if repo_id and payload.get("repo_id") == repo_id:
            return payload, path
    raise FileNotFoundError(f"Unable to find adapter for adapter_id={adapter_id!r} repo_id={repo_id!r}.")


def load_lens_manifest(*, root: Path, lens_manifest_ref: str | Path) -> tuple[dict[str, Any], Path]:
    path = resolve_ref(lens_manifest_ref, root=root)
    payload = load_json_object(path)
    return payload, path


def load_provider_manifest(*, root: Path, provider_manifest_ref: str | Path) -> tuple[dict[str, Any], Path]:
    path = resolve_ref(provider_manifest_ref, root=root)
    payload = load_json_object(path)
    return payload, path


def validate_adapter_manifest(
    payload: dict[str, Any],
    *,
    root: Path,
    require_repo_path_exists: bool = True,
) -> list[str]:
    errors: list[str] = []
    errors.extend(validate_declared_contract_version(payload.get("contract_version"), ADAPTER_CONTRACT_VERSION))
    registry = load_repo_registry(root=root)
    repo_id = payload.get("repo_id")
    repo_path = payload.get("repo_path")
    for key in ("adapter_id", "repo_id", "repo_path"):
        value = payload.get(key)
        if not isinstance(value, str) or not value.strip():
            errors.append(f"{key} must be a non-empty string.")
    if (
        require_repo_path_exists
        and isinstance(repo_path, str)
        and repo_path.strip()
        and not resolve_ref(repo_path, root=root).exists()
    ):
        errors.append(f"repo_path does not exist: {repo_path}")
    if isinstance(repo_id, str) and repo_id in registry and isinstance(repo_path, str):
        if normalize_slashes(repo_path) != registry[repo_id].atlas_path:
            errors.append(f"repo_path for repo_id '{repo_id}' must match stack.yaml.")
    commands = payload.get("commands")
    if not isinstance(commands, dict):
        errors.append("commands must be an object.")
    else:
        for key, value in commands.items():
            if not isinstance(value, dict):
                errors.append(f"commands.{key} must be an object.")
                continue
            command = value.get("command")
            if not isinstance(command, str) or not command.strip():
                errors.append(f"commands.{key}.command must be a non-empty string.")
    prepare = payload.get("prepare")
    if prepare is not None:
        if not isinstance(prepare, dict):
            errors.append("prepare must be an object when present.")
        else:
            if prepare.get("kind") not in {None, "command"}:
                errors.append("prepare.kind must be 'command' when present.")
            command = prepare.get("command")
            if not isinstance(command, str) or not command.strip():
                errors.append("prepare.command must be a non-empty string when prepare is present.")
    lenses = payload.get("lenses")
    if not isinstance(lenses, list) or not lenses:
        errors.append("lenses must be a non-empty array.")
    else:
        for index, item in enumerate(lenses):
            path = f"lenses[{index}]"
            if not isinstance(item, dict):
                errors.append(f"{path} must be an object.")
                continue
            if item.get("proof_kind") not in PROOF_KINDS:
                errors.append(f"{path}.proof_kind must be 'emulated' or 'real'.")
            if item.get("execution_mode") not in EXECUTION_MODES:
                errors.append(f"{path}.execution_mode must be a supported execution mode.")
            profile_id = item.get("profile_id")
            if not isinstance(profile_id, str) or not profile_id.strip():
                errors.append(f"{path}.profile_id must be a non-empty string.")
            if item.get("evidence_kind") not in {"emulated_browser", "physical_device"}:
                errors.append(f"{path}.evidence_kind must be emulated_browser or physical_device.")
            required_for = item.get("required_for")
            if not isinstance(required_for, list) or not required_for:
                errors.append(f"{path}.required_for must be a non-empty array.")
            promotion_tier = item.get("promotion_tier")
            if promotion_tier not in {"emulated_browser", "physical_device"}:
                errors.append(f"{path}.promotion_tier must be emulated_browser or physical_device.")
            fallback_behavior = item.get("fallback_behavior")
            if fallback_behavior not in {"blocked", "manual_review", "manual_attestation", "optional"}:
                errors.append(f"{path}.fallback_behavior must be blocked, manual_review, manual_attestation, or optional.")
            provider_manifest_ref = item.get("provider_manifest_ref")
            if provider_manifest_ref is not None:
                if not isinstance(provider_manifest_ref, str) or not provider_manifest_ref.strip():
                    errors.append(f"{path}.provider_manifest_ref must be a non-empty string when present.")
                else:
                    try:
                        provider_payload, _ = load_provider_manifest(root=root, provider_manifest_ref=provider_manifest_ref)
                        provider_errors = validate_provider_manifest(provider_payload)
                        errors.extend(f"{path}.provider_manifest_ref: {detail}" for detail in provider_errors)
                    except Exception as exc:
                        errors.append(f"{path}.provider_manifest_ref could not be loaded: {exc}")
    capture = payload.get("capture")
    if capture is not None:
        if not isinstance(capture, dict):
            errors.append("capture must be an object when present.")
        else:
            tool = capture.get("tool")
            if tool is not None and tool not in {"playwright"}:
                errors.append("capture.tool must currently be 'playwright' when present.")
    lens_manifest_ref = payload.get("lens_manifest_ref")
    if not isinstance(lens_manifest_ref, str) or not lens_manifest_ref.strip():
        errors.append("lens_manifest_ref must be a non-empty string.")
    else:
        try:
            lens_payload, _ = load_lens_manifest(root=root, lens_manifest_ref=lens_manifest_ref)
            lens_errors = validate_lens_manifest(lens_payload)
            errors.extend(f"lens_manifest_ref: {item}" for item in lens_errors)
            valid_profiles = {
                str(item.get("lens_id"))
                for item in lens_payload.get("lenses", [])
                if isinstance(item, dict) and isinstance(item.get("lens_id"), str)
            }
            for index, item in enumerate(payload.get("lenses", [])):
                if isinstance(item, dict):
                    profile_id = item.get("profile_id")
                    if isinstance(profile_id, str) and valid_profiles and profile_id not in valid_profiles:
                        errors.append(f"lenses[{index}].profile_id '{profile_id}' does not exist in the lens manifest.")
        except Exception as exc:
            errors.append(f"lens_manifest_ref could not be loaded: {exc}")
    return errors


def validate_capture_receipt(payload: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    errors.extend(validate_declared_contract_version(payload.get("contract_version"), CAPTURE_RECEIPT_CONTRACT_VERSION))
    for key in ("run_id", "scenario_id", "adapter_id", "repo_id", "git_sha", "lens_id", "captured_at", "source_url", "capture_backend"):
        value = payload.get(key)
        if not isinstance(value, str) or not value.strip():
            errors.append(f"{key} must be a non-empty string.")
    capture_method = payload.get("capture_method")
    if capture_method not in {"browser_emulation", "provider_automation", "manual_attestation"}:
        errors.append("capture_method must be browser_emulation, provider_automation, or manual_attestation.")
    return errors


def validate_test_evidence_payload(payload: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    errors.extend(validate_declared_contract_version(payload.get("contract_version"), TEST_EVIDENCE_CONTRACT_VERSION))
    for key in ("run_id", "scenario_id", "adapter_id", "repo_id", "git_sha", "mode"):
        value = payload.get(key)
        if not isinstance(value, str) or not value.strip():
            errors.append(f"{key} must be a non-empty string.")
    if payload.get("mode") not in {"dry_run", "execute"}:
        errors.append("mode must be dry_run or execute.")
    receipts = payload.get("receipts")
    if not isinstance(receipts, list):
        errors.append("receipts must be an array.")
    else:
        for index, item in enumerate(receipts):
            path = f"receipts[{index}]"
            if not isinstance(item, dict):
                errors.append(f"{path} must be an object.")
                continue
            for key in ("evidence_id", "command_ref", "runner", "kind", "status"):
                value = item.get(key)
                if not isinstance(value, str) or not value.strip():
                    errors.append(f"{path}.{key} must be a non-empty string.")
            if item.get("runner") not in TEST_RUNNERS:
                errors.append(f"{path}.runner must be one of: {', '.join(sorted(TEST_RUNNERS))}.")
            if item.get("status") not in {"planned", "passed", "failed", "missing"}:
                errors.append(f"{path}.status must be planned, passed, failed, or missing.")
    errors.extend(validate_receipt_origin(payload.get("receipt_origin")))
    return errors


def validate_visual_baseline_payload(payload: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    errors.extend(validate_declared_contract_version(payload.get("contract_version"), VISUAL_BASELINE_CONTRACT_VERSION))
    for key in ("baseline_id", "scenario_id", "adapter_id", "lens_id", "evidence_tier", "source_run_id", "git_sha", "artifact_hash", "state"):
        value = payload.get(key)
        if not isinstance(value, str) or not value.strip():
            errors.append(f"{key} must be a non-empty string.")
    if payload.get("state") not in {"proposed", "blessed", "superseded", "rejected"}:
        errors.append("state must be proposed, blessed, superseded, or rejected.")
    approved_by = payload.get("approved_by")
    if approved_by is not None and not isinstance(approved_by, str):
        errors.append("approved_by must be a string when present.")
    return errors


def validate_evidence_index_payload(payload: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    errors.extend(validate_declared_contract_version(payload.get("contract_version"), EVIDENCE_INDEX_CONTRACT_VERSION))
    runs = payload.get("runs")
    if not isinstance(runs, list):
        errors.append("runs must be an array.")
    return errors


def write_manifest(path: Path, payload: dict[str, Any]) -> None:
    write_json(path, payload)


def payload_with_digest(payload: dict[str, Any], field_name: str) -> dict[str, Any]:
    body = dict(payload)
    digest = stable_json_digest(body)
    return {field_name: digest, **body}
