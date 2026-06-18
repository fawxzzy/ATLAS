from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from ops._atlas import atlas_relative, atlas_root, load_repo_registry
from ops.atlas.qa._common import (
    default_evidence_index_path,
    default_release_policy_path,
    default_release_readiness_path,
    display_promotion_status,
    load_json_object,
    resolve_ref,
    utc_now,
    validate_waiver_payload,
)
from ops.atlas.qa.evidence_index import build_evidence_index
from ops.stack.generate_lockfile import default_lockfile_path, git_output, load_lockfile
from ops.cortex._artifacts import write_json

ORIGIN_PRIORITY = {
    "ci_release": 5,
    "protected_manual": 4,
    "provider": 3,
    "ci_pr": 2,
    "local_dev": 1,
}


def _evaluate_governance_checks(
    *,
    base_root: Path,
    repo_id: str,
    override: dict[str, Any],
) -> list[dict[str, Any]]:
    specs = override.get("governance_checks", [])
    if not isinstance(specs, list):
        return []
    checks: list[dict[str, Any]] = []
    for index, spec in enumerate(specs):
        if not isinstance(spec, dict):
            continue
        check_id = str(spec.get("check_id") or f"{repo_id}-governance-check-{index + 1}")
        kind = str(spec.get("kind") or "json_report")
        report_ref = str(spec.get("report_ref") or "").strip()
        contract_version = str(spec.get("contract_version") or "").strip()
        required_for_modes = [
            str(value)
            for value in spec.get("required_for_modes", [])
            if isinstance(value, str) and value.strip()
        ]
        notes = [
            str(value)
            for value in spec.get("notes", [])
            if isinstance(value, str) and value.strip()
        ]
        blockers: list[str] = []
        payload: dict[str, Any] = {}
        generated_at = ""
        age_hours = None
        checkpoint_status = ""
        decision = ""
        decision_reason = ""
        max_age_hours = spec.get("max_age_hours")
        if not report_ref:
            blockers.append(f"Governance check '{check_id}' is missing report_ref.")
        elif kind != "json_report":
            blockers.append(f"Governance check '{check_id}' uses unsupported kind '{kind}'.")
        else:
            try:
                payload = load_json_object(resolve_ref(report_ref, root=base_root))
            except Exception as exc:
                blockers.append(f"Governance check '{check_id}' could not load '{report_ref}': {exc}")
            else:
                observed_contract = str(payload.get("contract_version") or payload.get("report_version") or "").strip()
                if contract_version and observed_contract != contract_version:
                    blockers.append(
                        f"Governance check '{check_id}' expected contract '{contract_version}' but found '{observed_contract or 'missing'}'."
                    )
                generated_at = str(payload.get("generated_at") or "")
                checkpoint_status = str(payload.get("checkpoint_status") or "").strip()
                decision = str(payload.get("decision") or "").strip()
                decision_reason = str(payload.get("decision_reason") or "").strip()
                generated_dt = _parse_utc(generated_at)
                if isinstance(max_age_hours, (int, float)):
                    if generated_dt is None:
                        blockers.append(
                            f"Governance check '{check_id}' report timestamp is missing or unreadable."
                        )
                    else:
                        age_hours = round((datetime.now(timezone.utc) - generated_dt).total_seconds() / 3600, 3)
                        if age_hours > float(max_age_hours):
                            blockers.append(
                                f"Governance check '{check_id}' report is stale ({age_hours}h > {float(max_age_hours)}h)."
                            )
                if checkpoint_status and checkpoint_status != "ready":
                    detail = f"Governance check '{check_id}' status is '{checkpoint_status}'."
                    if decision:
                        detail += f" Decision: '{decision}'."
                    if decision_reason:
                        detail += f" Reason: {decision_reason}"
                    blockers.append(detail)
        guardrail_posture = payload.get("guardrail_posture") if isinstance(payload.get("guardrail_posture"), dict) else {}
        summary = payload.get("summary") if isinstance(payload.get("summary"), dict) else {}
        checks.append(
            {
                "check_id": check_id,
                "kind": kind,
                "report_ref": report_ref,
                "contract_version": contract_version,
                "observed_contract_version": str(payload.get("contract_version") or payload.get("report_version") or "").strip(),
                "required_for_modes": required_for_modes,
                "notes": notes,
                "generated_at": generated_at,
                "age_hours": age_hours,
                "max_age_hours": float(max_age_hours) if isinstance(max_age_hours, (int, float)) else None,
                "status": "blocked" if blockers else "ready",
                "blockers": blockers,
                "checkpoint_status": checkpoint_status,
                "decision": decision,
                "decision_reason": decision_reason,
                "guardrail_posture": guardrail_posture,
                "summary": summary,
            }
        )
    return checks


def _mode_gate_status(*, promotion_status: str, allowed_statuses: set[str]) -> str:
    if promotion_status in allowed_statuses:
        return "ready"
    if promotion_status == "manual_review":
        return "manual_review"
    if promotion_status == "dry_run":
        return "planned_only"
    return "blocked"


def _parse_utc(value: str) -> datetime | None:
    if not value.strip():
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(timezone.utc)
    except ValueError:
        return None


def _validate_runtime_waivers(
    *,
    base_root: Path,
    waiver_refs: list[str],
    repo_id: str,
    scenario_id: str,
    run_id: str,
) -> tuple[list[dict[str, Any]], list[str]]:
    valid_waivers: list[dict[str, Any]] = []
    findings: list[str] = []
    for ref in waiver_refs:
        try:
            payload = load_json_object(resolve_ref(ref, root=base_root))
        except Exception as exc:
            findings.append(f"Waiver '{ref}' could not be loaded: {exc}")
            continue
        errors = validate_waiver_payload(payload)
        if errors:
            findings.extend(f"Waiver '{ref}' is invalid: {detail}" for detail in errors)
            continue
        if str(payload.get("repo_id") or "") != repo_id:
            findings.append(f"Waiver '{ref}' repo_id does not match the release target repo.")
            continue
        if str(payload.get("scenario_id") or "") != scenario_id:
            findings.append(f"Waiver '{ref}' scenario_id does not match the release target scenario.")
            continue
        if str(payload.get("run_id") or "") != run_id:
            findings.append(f"Waiver '{ref}' run_id does not match the selected release run.")
            continue
        expires_at = _parse_utc(str(payload.get("expires_at") or ""))
        if expires_at is None or expires_at <= datetime.now(timezone.utc):
            findings.append(f"Waiver '{ref}' is expired or has an invalid expires_at.")
            continue
        lane = str(payload.get("waived_lane") or "")
        if lane:
            days_until_expiry = round((expires_at - datetime.now(timezone.utc)).total_seconds() / 86400, 3)
            valid_waivers.append(
                {
                    "waiver_ref": ref,
                    "waived_lane": lane,
                    "expires_at": expires_at.isoformat().replace("+00:00", "Z"),
                    "days_until_expiry": days_until_expiry,
                    "operator": str(payload.get("operator") or ""),
                    "reason": str(payload.get("reason") or ""),
                    "limitation": str(payload.get("limitation") or ""),
                }
            )
    return valid_waivers, findings


def _resolve_target_sha(
    *,
    repo_id: str,
    explicit_target_sha: str,
    base_root: Path,
    stack_lock_file: Path | None,
    adapter_refs: list[str] | None = None,
) -> dict[str, str]:
    stack_lock_pin = ""
    if isinstance(stack_lock_file, Path) and stack_lock_file.exists():
        try:
            lockfile = load_lockfile(stack_lock_file)
            components = lockfile.get("components", {}) if isinstance(lockfile.get("components"), dict) else {}
            component = components.get(repo_id, {}) if isinstance(components.get(repo_id), dict) else {}
            stack_lock_pin = str(component.get("commit") or "").strip()
        except Exception:
            stack_lock_pin = ""
    current_repo_sha = ""
    repo_registry = load_repo_registry(root=base_root)
    repo_entry = repo_registry.get(repo_id)
    candidate_paths: list[Path] = []
    if repo_entry is not None and repo_entry.root.exists():
        candidate_paths.append(repo_entry.root)
    for ref in adapter_refs or []:
        target = (base_root / ref).resolve()
        if not target.exists():
            continue
        try:
            payload = load_json_object(target)
        except Exception:
            continue
        repo_path = payload.get("repo_path")
        if isinstance(repo_path, str) and repo_path.strip():
            repo_root = (base_root / repo_path).resolve()
            if repo_root.exists():
                candidate_paths.append(repo_root)
    seen_paths: set[str] = set()
    for candidate in candidate_paths:
        normalized = str(candidate.resolve()).lower()
        if normalized in seen_paths:
            continue
        seen_paths.add(normalized)
        code, stdout = git_output(candidate, "rev-parse", "HEAD")
        if code == 0 and stdout.strip():
            current_repo_sha = stdout.strip()
            break
    target_sha = explicit_target_sha.strip() or stack_lock_pin or current_repo_sha
    target_source = "explicit" if explicit_target_sha.strip() else "stack_lock" if stack_lock_pin else "repo_head" if current_repo_sha else "unresolved"
    return {
        "target_sha": target_sha,
        "target_source": target_source,
        "stack_lock_pin": stack_lock_pin,
        "current_repo_sha": current_repo_sha,
    }


def _origin_rank(origin_type: str) -> int:
    return ORIGIN_PRIORITY.get(origin_type, 0)


def _string_list(values: Any) -> list[str]:
    if not isinstance(values, list):
        return []
    return [str(value) for value in values if isinstance(value, str) and value.strip()]


def _choose_release_receipt(
    *,
    repo_runs: list[dict[str, Any]],
    target_sha: str,
    expected_profile: str,
    max_receipt_age_hours: float,
) -> tuple[dict[str, Any] | None, dict[str, Any]]:
    candidates: list[tuple[tuple[int, int, int, int, int, str], dict[str, Any], dict[str, Any]]] = []
    newest_run: dict[str, Any] | None = None
    newest_generated = ""
    for run in repo_runs:
        if not isinstance(run, dict):
            continue
        generated_at = str(run.get("promotion_generated_at") or "")
        if generated_at > newest_generated:
            newest_generated = generated_at
            newest_run = run
        run_profile = str(run.get("evidence_profile") or "")
        run_sha = str(run.get("git_sha") or "").strip()
        origin = run.get("receipt_origin") if isinstance(run.get("receipt_origin"), dict) else {}
        origin_type = str(origin.get("origin_type") or "")
        generated_dt = _parse_utc(generated_at)
        age_hours = None
        if generated_dt is not None:
            age_hours = round((datetime.now(timezone.utc) - generated_dt).total_seconds() / 3600, 3)
        fresh = isinstance(age_hours, (int, float)) and age_hours <= max_receipt_age_hours
        metadata = {
            "origin_type": origin_type,
            "origin_rank": _origin_rank(origin_type),
            "sha_match": bool(target_sha and run_sha and target_sha == run_sha),
            "profile_match": bool(expected_profile and run_profile == expected_profile),
            "fresh": fresh,
            "age_hours": age_hours,
            "generated_at": generated_at,
        }
        rank = (
            1 if metadata["sha_match"] else 0,
            1 if metadata["profile_match"] else 0,
            1 if fresh else 0,
            0 if str(run.get("promotion_status") or "") == "dry_run" else 1,
            metadata["origin_rank"],
            generated_at,
        )
        candidates.append((rank, run, metadata))
    if not candidates:
        return None, {"newest_run_id": "", "selection_reason": ""}
    candidates.sort(key=lambda item: item[0], reverse=True)
    chosen_rank, chosen, chosen_meta = candidates[0]
    selection_reason = ""
    newest_run_id = str((newest_run or {}).get("run_id") or "")
    if newest_run is not None and str(newest_run.get("run_id") or "") != str(chosen.get("run_id") or ""):
        newest_origin = newest_run.get("receipt_origin") if isinstance(newest_run.get("receipt_origin"), dict) else {}
        newest_origin_type = str(newest_origin.get("origin_type") or "")
        newest_sha = str(newest_run.get("git_sha") or "").strip()
        newest_profile = str(newest_run.get("evidence_profile") or "")
        newest_dt = _parse_utc(str(newest_run.get("promotion_generated_at") or ""))
        newest_age_hours = None
        if newest_dt is not None:
            newest_age_hours = round((datetime.now(timezone.utc) - newest_dt).total_seconds() / 3600, 3)
        if target_sha and newest_sha != target_sha:
            selection_reason = "newer receipt ignored because it targets the wrong SHA."
        elif expected_profile and newest_profile != expected_profile:
            selection_reason = "newer receipt ignored because its evidence profile does not match the release profile."
        elif newest_age_hours is not None and newest_age_hours > max_receipt_age_hours:
            selection_reason = "newer receipt ignored because it is stale."
        elif _origin_rank(newest_origin_type) < int(chosen_meta["origin_rank"]):
            selection_reason = "newer receipt ignored because an older receipt has a stronger trusted origin."
        else:
            selection_reason = "newer receipt ignored because an older receipt is the strongest valid release source."
    return chosen, {
        "newest_run_id": newest_run_id,
        "selection_reason": selection_reason,
    }


def build_release_readiness(
    *,
    root: Path | None = None,
    policy_file: Path | None = None,
    evidence_index_file: Path | None = None,
    output_file: Path | None = None,
    target_sha: str = "",
    stack_lock_file: Path | None = None,
    max_receipt_age_hours: float = 168.0,
) -> dict[str, Any]:
    base_root = (root or atlas_root()).resolve()
    policy_path = policy_file.resolve() if isinstance(policy_file, Path) else default_release_policy_path(root=base_root)
    evidence_index_path = evidence_index_file.resolve() if isinstance(evidence_index_file, Path) else default_evidence_index_path(root=base_root)
    resolved_stack_lock = stack_lock_file.resolve() if isinstance(stack_lock_file, Path) else default_lockfile_path(root=base_root)
    if not evidence_index_path.exists():
        build_evidence_index(root=base_root, output_file=evidence_index_path)

    policy = load_json_object(policy_path)
    evidence_index = load_json_object(evidence_index_path)
    profiles = policy.get("profiles", {}) if isinstance(policy.get("profiles"), dict) else {}
    repo_overrides = policy.get("repo_overrides", {}) if isinstance(policy.get("repo_overrides"), dict) else {}
    adoption = evidence_index.get("adoption", []) if isinstance(evidence_index.get("adoption"), list) else []
    runs = evidence_index.get("runs", []) if isinstance(evidence_index.get("runs"), list) else []
    runs_by_repo: dict[str, list[dict[str, Any]]] = {}
    for run in runs:
        if not isinstance(run, dict):
            continue
        repo_id = str(run.get("repo_id") or "")
        if not repo_id:
            continue
        runs_by_repo.setdefault(repo_id, []).append(run)

    repos: list[dict[str, Any]] = []
    for item in adoption:
        if not isinstance(item, dict):
            continue
        repo_id = str(item.get("repo_id") or "")
        evidence_profile = str(item.get("evidence_profile") or "")
        override = repo_overrides.get(repo_id, {}) if isinstance(repo_overrides.get(repo_id), dict) else {}
        release_profile = str(override.get("release_profile") or evidence_profile or "package_contract")
        profile_policy = profiles.get(release_profile, {}) if isinstance(profiles.get(release_profile), dict) else {}
        mode_requirements = profile_policy.get("mode_requirements", {}) if isinstance(profile_policy.get("mode_requirements"), dict) else {}
        governance_checks = _evaluate_governance_checks(base_root=base_root, repo_id=repo_id, override=override)
        target = _resolve_target_sha(
            repo_id=repo_id,
            explicit_target_sha=target_sha,
            base_root=base_root,
            stack_lock_file=resolved_stack_lock,
            adapter_refs=[str(value) for value in item.get("adapter_refs", []) if isinstance(value, str)],
        )
        repo_runs = runs_by_repo.get(repo_id, [])
        strongest_run, selection_meta = _choose_release_receipt(
            repo_runs=repo_runs,
            target_sha=str(target["target_sha"] or ""),
            expected_profile=evidence_profile,
            max_receipt_age_hours=max_receipt_age_hours,
        )
        latest_run = strongest_run
        promotion_status = str((latest_run or {}).get("promotion_status") or item.get("last_promotion_status") or "")
        promotion_display_status = display_promotion_status(
            promotion_status=promotion_status,
            evidence_profile=evidence_profile,
        )
        latest_generated_at = str((latest_run or {}).get("promotion_generated_at") or "")
        latest_generated_dt = _parse_utc(latest_generated_at)
        age_hours = None
        if latest_generated_dt is not None:
            age_hours = round((datetime.now(timezone.utc) - latest_generated_dt).total_seconds() / 3600, 3)
        receipt_sha = str((latest_run or {}).get("git_sha") or item.get("last_git_sha") or "").strip()
        sha_match = bool(target["target_sha"] and receipt_sha and target["target_sha"] == receipt_sha)
        receipt_fresh = isinstance(age_hours, (int, float)) and age_hours <= max_receipt_age_hours
        per_mode: dict[str, Any] = {}
        for mode_name in ("pr", "main", "release", "manual_promotion"):
            mode_policy = mode_requirements.get(mode_name, {}) if isinstance(mode_requirements.get(mode_name), dict) else {}
            allowed_statuses = {
                str(value)
                for value in mode_policy.get("allowed_statuses", [])
                if isinstance(value, str) and value.strip()
            }
            gate_status = _mode_gate_status(promotion_status=promotion_status, allowed_statuses=allowed_statuses) if allowed_statuses else "policy_only"
            per_mode[mode_name] = {
                "gate_status": gate_status,
                "required_evidence": list(mode_policy.get("required_evidence", [])),
                "required_tiers": list(mode_policy.get("required_tiers", [])),
                "allowed_statuses": sorted(allowed_statuses),
                "trusted_origins": list(mode_policy.get("trusted_origins", [])),
                "notes": list(mode_policy.get("notes", [])),
            }
        for mode_name, mode_entry in per_mode.items():
            mode_governance = [
                {
                    "check_id": check["check_id"],
                    "status": check["status"],
                    "report_ref": check["report_ref"],
                    "generated_at": check["generated_at"],
                    "age_hours": check["age_hours"],
                    "max_age_hours": check["max_age_hours"],
                    "blockers": list(check["blockers"]),
                }
                for check in governance_checks
                if mode_name in check["required_for_modes"]
            ]
            governance_blockers = [
                blocker
                for check in mode_governance
                for blocker in check["blockers"]
            ]
            governance_gate_status = "not_required"
            if mode_governance:
                governance_gate_status = "blocked" if governance_blockers else "ready"
                if governance_gate_status == "blocked":
                    mode_entry["gate_status"] = "blocked"
            mode_entry["governance_checks"] = mode_governance
            mode_entry["governance_gate_status"] = governance_gate_status
            mode_entry["governance_blockers"] = governance_blockers
        release_gate = per_mode.get("release", {})
        legacy_release_origins = _string_list(release_gate.get("trusted_origins"))
        allowed_release_origins = _string_list(profile_policy.get("allowed_release_origins")) or legacy_release_origins
        allowed_pr_origins = _string_list(profile_policy.get("allowed_pr_origins"))
        legacy_origin_policy = bool(legacy_release_origins) and "require_trusted_origin" not in profile_policy
        require_trusted_origin = bool(profile_policy.get("require_trusted_origin", legacy_origin_policy))
        origin_enforcement_stage = str(
            profile_policy.get("enforcement_stage")
            or ("enforce" if legacy_origin_policy else "observe")
        )
        release_gate_status = str(release_gate.get("gate_status") or "policy_only")
        release_ready = release_gate_status == "ready"
        release_blockers: list[str] = []
        release_blockers.extend(
            str(item)
            for item in release_gate.get("governance_blockers", [])
            if isinstance(item, str) and item.strip()
        )
        waiver_refs = [str(value) for value in (latest_run or {}).get("waiver_refs", []) if isinstance(value, str) and value.strip()]
        waived_lanes = [str(value) for value in (latest_run or {}).get("waived_lanes", []) if isinstance(value, str) and value.strip()]
        validated_waivers, waiver_findings = _validate_runtime_waivers(
            base_root=base_root,
            waiver_refs=waiver_refs,
            repo_id=repo_id,
            scenario_id=str((latest_run or {}).get("scenario_id") or ""),
            run_id=str((latest_run or {}).get("run_id") or ""),
        ) if waiver_refs else ([], [])
        validated_waived_lanes = [str(item.get("waived_lane") or "") for item in validated_waivers if str(item.get("waived_lane") or "")]
        waiver_valid = bool(waiver_refs) and not waiver_findings and bool(validated_waivers)
        waiver_expires_at = ""
        days_until_expiry = None
        if validated_waivers:
            earliest = min(validated_waivers, key=lambda item: str(item.get("expires_at") or ""))
            waiver_expires_at = str(earliest.get("expires_at") or "")
            earliest_days = earliest.get("days_until_expiry")
            if isinstance(earliest_days, (int, float)):
                days_until_expiry = float(earliest_days)
        if waiver_findings:
            release_ready = False
            release_gate_status = "blocked"
            release_blockers.extend(waiver_findings)
        receipt_origin = (latest_run or {}).get("receipt_origin") if isinstance((latest_run or {}).get("receipt_origin"), dict) else {}
        receipt_origin_type = str(receipt_origin.get("origin_type") or "")
        trusted_origins = set(allowed_release_origins)
        if not receipt_fresh:
            release_ready = False
            release_gate_status = "blocked"
            if age_hours is None:
                release_blockers.append("Latest receipt timestamp is missing or unreadable.")
            else:
                release_blockers.append(f"Latest receipt is stale ({age_hours}h > {max_receipt_age_hours}h).")
        if target["target_sha"] and not sha_match:
            release_ready = False
            release_gate_status = "blocked"
            release_blockers.append("Latest receipt is for the wrong SHA and does not match the target release SHA or stack pin.")
        elif not target["target_sha"]:
            release_ready = False
            release_gate_status = "blocked"
            release_blockers.append("No target release SHA could be resolved for provenance.")
        trusted_origin_required = require_trusted_origin and bool(trusted_origins)
        trusted_origin_match = not trusted_origin_required or receipt_origin_type in trusted_origins
        trusted_origin_status = "not_required"
        if trusted_origin_required:
            if trusted_origin_match:
                trusted_origin_status = "trusted"
            elif origin_enforcement_stage == "observe":
                trusted_origin_status = "observe"
            elif origin_enforcement_stage == "warn":
                trusted_origin_status = "warn"
            elif release_gate_status == "ready":
                trusted_origin_status = "blocked"
                release_ready = False
                release_gate_status = "blocked"
                release_blockers.append("Latest receipt origin is not trusted for release enforcement.")
            else:
                trusted_origin_status = "warn"
        if not release_ready and not release_blockers:
            if promotion_status == "manual_review":
                release_blockers.append("Release gate still requires manual or provider-backed physical proof.")
            elif promotion_status == "dry_run":
                release_blockers.append("Latest repo receipt is dry-run only; evidence-grade execution is still required.")
            else:
                release_blockers.append(f"Latest promotion status '{promotion_status}' does not satisfy the release gate.")
        repos.append(
            {
                "repo_id": repo_id,
                "evidence_profile": evidence_profile,
                "release_profile": release_profile,
                "display_name": str(profile_policy.get("display_name") or release_profile),
                "readiness_source_run_id": str((latest_run or {}).get("run_id") or item.get("last_run_id") or ""),
                "last_run_id": str(item.get("last_run_id") or ""),
                "last_promotion_generated_at": latest_generated_at,
                "last_receipt_age_hours": age_hours,
                "max_receipt_age_hours": max_receipt_age_hours,
                "receipt_fresh": receipt_fresh,
                "target_sha": target["target_sha"],
                "target_sha_source": target["target_source"],
                "receipt_sha": receipt_sha,
                "sha_match": sha_match,
                "stack_lock_pin": target["stack_lock_pin"],
                "current_repo_sha": target["current_repo_sha"],
                "promotion_status": promotion_status,
                "promotion_display_status": promotion_display_status,
                "receipt_origin": receipt_origin,
                "receipt_origin_type": receipt_origin_type,
                "trusted_origin_required": trusted_origin_required,
                "allowed_release_origins": allowed_release_origins,
                "allowed_pr_origins": allowed_pr_origins,
                "trusted_origin_match": trusted_origin_match,
                "trusted_origin_status": trusted_origin_status,
                "origin_enforcement_stage": origin_enforcement_stage,
                "selection_source_run_id": str((latest_run or {}).get("run_id") or ""),
                "selection_newest_run_id": str(selection_meta.get("newest_run_id") or ""),
                "selection_reason": str(selection_meta.get("selection_reason") or ""),
                "governance_checks": governance_checks,
                "waiver_refs": waiver_refs,
                "waived_lanes": waived_lanes,
                "waiver_valid": waiver_valid,
                "waiver_expires_at": waiver_expires_at,
                "days_until_expiry": days_until_expiry,
                "validated_waivers": validated_waivers,
                "validated_waived_lanes": validated_waived_lanes,
                "release_ready_with_waiver": bool(promotion_status == "waived_promoted" and validated_waived_lanes and not waiver_findings),
                "waiver_blocks_trusted_origin_enforcement": bool(promotion_status == "waived_promoted" and trusted_origin_required and origin_enforcement_stage == "enforce"),
                "release_ready": release_ready,
                "release_gate_status": release_gate_status,
                "release_blockers": release_blockers,
                "mode_requirements": per_mode,
            }
        )

    payload = {
        "contract_version": "atlas.qa.release_readiness.v1",
        "generated_at": utc_now(),
        "policy_ref": atlas_relative(policy_path, root=base_root),
        "evidence_index_ref": atlas_relative(evidence_index_path, root=base_root),
        "stack_lock_ref": atlas_relative(resolved_stack_lock, root=base_root) if resolved_stack_lock.exists() else "",
        "target_sha_override": target_sha,
        "max_receipt_age_hours": max_receipt_age_hours,
        "repos": repos,
        "summary": {
            "repo_count": len(repos),
            "release_ready_count": sum(1 for item in repos if item.get("release_ready")),
            "manual_review_count": sum(1 for item in repos if item.get("release_gate_status") == "manual_review"),
            "blocked_count": sum(1 for item in repos if item.get("release_gate_status") == "blocked"),
        },
    }
    target = output_file.resolve() if isinstance(output_file, Path) else default_release_readiness_path(root=base_root)
    target.parent.mkdir(parents=True, exist_ok=True)
    write_json(target, payload)
    md_path = target.with_suffix(".md")
    md_lines = [
        "# ATLAS QA Release Readiness",
        "",
        f"- Generated at: `{payload['generated_at']}`",
        f"- Policy: `{payload['policy_ref']}`",
        f"- Evidence index: `{payload['evidence_index_ref']}`",
        f"- Stack lock: `{payload['stack_lock_ref'] or 'none'}`",
        f"- Max receipt age (hours): `{max_receipt_age_hours}`",
        f"- Repos: `{payload['summary']['repo_count']}`",
        f"- Release ready: `{payload['summary']['release_ready_count']}`",
        f"- Manual review: `{payload['summary']['manual_review_count']}`",
        f"- Blocked: `{payload['summary']['blocked_count']}`",
        "",
        "| Repo | Profile | Release Tier | Status | Display | Origin | Origin Stage | Origin Status | Release Gate | Ready | Waiver | Waiver Expiry | SHA Match |",
        "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    for item in repos:
        md_lines.append(
            f"| {item['repo_id']} | {item['evidence_profile'] or '-'} | {item['release_profile']} | {item['promotion_status']} | {item['promotion_display_status']} | {item['receipt_origin_type'] or '-'} | {item['origin_enforcement_stage']} | {item['trusted_origin_status']} | {item['release_gate_status']} | {item['release_ready']} | {', '.join(item.get('validated_waived_lanes', [])) or '-'} | {item.get('waiver_expires_at') or '-'} | {item['sha_match']} |"
        )
        md_lines.append(
            f"|  |  |  |  |  | target `{item['target_sha'] or '-'}` from `{item['target_sha_source']}` | receipt `{item['receipt_sha'] or '-'}` | run `{item['readiness_source_run_id'] or '-'}` |"
        )
        if item.get("selection_reason"):
            md_lines.append(f"|  |  |  |  |  | selection: {item['selection_reason']} |  |  |")
        for check in item.get("governance_checks", []):
            if not isinstance(check, dict):
                continue
            md_lines.append(
                f"|  |  |  |  |  | governance `{check.get('check_id') or '-'}`: {check.get('status') or '-'} via `{check.get('report_ref') or '-'}` |  |  |"
            )
            guardrail_posture = check.get("guardrail_posture")
            if isinstance(guardrail_posture, dict) and guardrail_posture:
                posture_summary = ", ".join(
                    f"{key}={value}"
                    for key, value in sorted(guardrail_posture.items())
                    if isinstance(value, str) and value.strip()
                )
                if posture_summary:
                    md_lines.append(f"|  |  |  |  |  | governance posture: {posture_summary} |  |  |")
            decision = str(check.get("decision") or "").strip()
            decision_reason = str(check.get("decision_reason") or "").strip()
            checkpoint_status = str(check.get("checkpoint_status") or "").strip()
            if decision:
                detail = f"governance decision: {decision}"
                if checkpoint_status:
                    detail += f" ({checkpoint_status})"
                md_lines.append(f"|  |  |  |  |  | {detail} |  |  |")
            if decision_reason:
                md_lines.append(f"|  |  |  |  |  | governance decision reason: {decision_reason} |  |  |")
            for blocker in check.get("blockers", []):
                md_lines.append(f"|  |  |  |  |  | governance blocker: {blocker} |  |  |")
        if item["release_blockers"]:
            for blocker in item["release_blockers"]:
                md_lines.append(f"|  |  |  |  |  | blocker: {blocker} |  |  |")
    md_lines += ["", "## Mode Policy", ""]
    for profile_id, profile_policy in sorted(profiles.items()):
        if not isinstance(profile_policy, dict):
            continue
        md_lines.append(f"### `{profile_id}`")
        display_name = str(profile_policy.get("display_name") or profile_id)
        md_lines.append("")
        md_lines.append(f"- Display name: `{display_name}`")
        md_lines.append(f"- Trusted origin required: `{bool(profile_policy.get('require_trusted_origin', False))}`")
        md_lines.append(f"- Origin enforcement stage: `{str(profile_policy.get('enforcement_stage') or 'observe')}`")
        if profile_policy.get("allowed_release_origins"):
            md_lines.append(f"- Allowed release origins: `{', '.join(profile_policy.get('allowed_release_origins', []))}`")
        if profile_policy.get("allowed_pr_origins"):
            md_lines.append(f"- Allowed PR origins: `{', '.join(profile_policy.get('allowed_pr_origins', []))}`")
        mode_requirements = profile_policy.get("mode_requirements", {}) if isinstance(profile_policy.get("mode_requirements"), dict) else {}
        for mode_name in ("pr", "main", "release", "manual_promotion"):
            mode_policy = mode_requirements.get(mode_name, {}) if isinstance(mode_requirements.get(mode_name), dict) else {}
            if not mode_policy:
                continue
            md_lines.append(f"- `{mode_name}` required evidence: `{', '.join(mode_policy.get('required_evidence', [])) or 'n/a'}`")
            if mode_policy.get("required_tiers"):
                md_lines.append(f"- `{mode_name}` required tiers: `{', '.join(mode_policy.get('required_tiers', []))}`")
            if mode_policy.get("allowed_statuses"):
                md_lines.append(f"- `{mode_name}` allowed statuses: `{', '.join(mode_policy.get('allowed_statuses', []))}`")
            if mode_policy.get("trusted_origins"):
                md_lines.append(f"- `{mode_name}` trusted origins: `{', '.join(mode_policy.get('trusted_origins', []))}`")
            for note in mode_policy.get("notes", []):
                md_lines.append(f"- `{mode_name}` note: {note}")
        md_lines.append("")
    md_path.write_text("\n".join(md_lines) + "\n", encoding="utf-8")
    return {
        "generated_at": payload["generated_at"],
        "release_readiness_ref": atlas_relative(target, root=base_root),
        "release_readiness_md_ref": atlas_relative(md_path, root=base_root),
        "repo_count": payload["summary"]["repo_count"],
    }


def enforce_release_repo_readiness(
    *,
    payload: dict[str, Any],
    repo_id: str,
    mode: str,
    max_receipt_age_hours: float,
) -> None:
    repos = payload.get("repos", []) if isinstance(payload.get("repos"), list) else []
    repo_entry = next((item for item in repos if isinstance(item, dict) and str(item.get("repo_id") or "") == repo_id), None)
    if repo_entry is None:
        raise SystemExit(f"Repo '{repo_id}' is not present in release readiness.")
    mode_requirements = repo_entry.get("mode_requirements", {}) if isinstance(repo_entry.get("mode_requirements"), dict) else {}
    mode_entry = mode_requirements.get(mode, {}) if isinstance(mode_requirements.get(mode), dict) else {}
    gate_status = str(
        repo_entry.get("release_gate_status") if mode == "release" else mode_entry.get("gate_status") or "blocked"
    )
    age_hours = repo_entry.get("last_receipt_age_hours")
    if not bool(repo_entry.get("receipt_fresh")):
        if isinstance(age_hours, (int, float)):
            raise SystemExit(
                f"Repo '{repo_id}' receipt is stale ({age_hours}h > {max_receipt_age_hours}h) and cannot satisfy {mode} readiness."
            )
        raise SystemExit(f"Repo '{repo_id}' receipt timestamp is missing or unreadable.")
    if not bool(repo_entry.get("sha_match")):
        raise SystemExit(
            f"Repo '{repo_id}' receipt SHA '{repo_entry.get('receipt_sha') or ''}' does not match target '{repo_entry.get('target_sha') or ''}'."
        )
    if gate_status != "ready":
        blockers = repo_entry.get("release_blockers", []) if isinstance(repo_entry.get("release_blockers"), list) else []
        blocker_text = "; ".join(str(item) for item in blockers) or f"gate_status={gate_status}"
        raise SystemExit(f"Repo '{repo_id}' is not {mode}-ready: {blocker_text}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build the ATLAS QA release-readiness report.")
    parser.add_argument("--root", type=Path, default=atlas_root())
    parser.add_argument("--policy-file", type=Path)
    parser.add_argument("--evidence-index-file", type=Path)
    parser.add_argument("--output-file", type=Path)
    parser.add_argument("--stack-lock-file", type=Path)
    parser.add_argument("--target-sha", default="")
    parser.add_argument("--repo")
    parser.add_argument("--mode", choices=("pr", "main", "release", "manual_promotion"), default="release")
    parser.add_argument("--max-receipt-age-hours", type=float, default=168.0)
    parser.add_argument("--enforce", action="store_true")
    args = parser.parse_args(argv)
    result = build_release_readiness(
        root=args.root.resolve(),
        policy_file=args.policy_file.resolve() if isinstance(args.policy_file, Path) else None,
        evidence_index_file=args.evidence_index_file.resolve() if isinstance(args.evidence_index_file, Path) else None,
        output_file=args.output_file.resolve() if isinstance(args.output_file, Path) else None,
        target_sha=str(args.target_sha or ""),
        stack_lock_file=args.stack_lock_file.resolve() if isinstance(args.stack_lock_file, Path) else None,
        max_receipt_age_hours=args.max_receipt_age_hours,
    )
    if args.enforce:
        payload = load_json_object((args.output_file.resolve() if isinstance(args.output_file, Path) else default_release_readiness_path(root=args.root.resolve())))
        target_repo = str(args.repo or "").strip()
        if not target_repo:
            raise SystemExit("Provide --repo when using --enforce.")
        enforce_release_repo_readiness(
            payload=payload,
            repo_id=target_repo,
            mode=args.mode,
            max_receipt_age_hours=args.max_receipt_age_hours,
        )
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
