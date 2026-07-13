from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import sys
from collections import OrderedDict
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from ops._atlas import atlas_root, load_repo_registry, normalize_slashes

ADOPTION_RECORD_REF = "docs/registry/ATLAS-PLAYBOOK-DOCTRINE-ADOPTION.json"
CONTRACT_VERSION = "atlas.playbook_doctrine_adoption.v1"
STATUS_VERIFIED = "verified"
STATUS_INVALID = "invalid"
STATUS_INTERNAL_ERROR = "internal_error"
EXPECTED_REGISTRY_ID = "atlas-engineering-doctrine-registry"
EXPECTED_REGISTRY_SCHEMA_VERSION = "atlas-engineering-doctrine-registry.v1"
EXPECTED_SCHEMA_ID = "atlas-engineering-doctrine-registry.schema.v1.json"
EXPECTED_VALIDATION_COMMAND = "python ops/atlas/playbook_doctrine_adoption.py --json"
SKILL_ID_RE = re.compile(r"^[a-z][a-z0-9]*(?:-[a-z0-9]+)*$")
COMMIT_RE = re.compile(r"^[0-9a-f]{40}$")


def _read_json(path: Path) -> dict[str, Any] | None:
    if not path.exists() or not path.is_file():
        return None
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return payload if isinstance(payload, dict) else None


def _finding(code: str, message: str, **details: Any) -> OrderedDict[str, Any]:
    payload: OrderedDict[str, Any] = OrderedDict([("code", code), ("message", message)])
    if details:
        payload["details"] = details
    return payload


def _append_check(checks: list[OrderedDict[str, Any]], code: str, ok: bool, **details: Any) -> None:
    payload: OrderedDict[str, Any] = OrderedDict([("code", code), ("ok", ok)])
    if details:
        payload["details"] = details
    checks.append(payload)


def _git_text(repo: Path, *args: str) -> tuple[int, str, str]:
    completed = subprocess.run(
        ["git", "-C", str(repo), *args],
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    return completed.returncode, completed.stdout.strip(), completed.stderr.strip()


def _git_bytes(repo: Path, *args: str) -> tuple[int, bytes, str]:
    completed = subprocess.run(
        ["git", "-C", str(repo), *args],
        check=False,
        capture_output=True,
    )
    return completed.returncode, completed.stdout, completed.stderr.decode("utf-8", errors="replace").strip()


def _root_relative(path: Path, root: Path) -> str:
    try:
        return normalize_slashes(str(path.resolve().relative_to(root.resolve())))
    except ValueError:
        return normalize_slashes(str(path.resolve()))


def _resolve_playbook_repo(root: Path) -> Path:
    registry = load_repo_registry(root=root)
    entry = registry.get("playbook")
    if entry is not None:
        return entry.root
    return (root / "repos" / "playbook").resolve()


def _sha256_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _parse_skill_metadata(text: str) -> dict[str, str]:
    metadata: dict[str, str] = {}
    if not text.startswith("---"):
        return metadata
    parts = text.split("---", 2)
    if len(parts) < 3:
        return metadata
    for line in parts[1].splitlines():
        key, separator, value = line.partition(":")
        if not separator:
            continue
        metadata[key.strip()] = value.strip()
    return metadata


def _walk_payload(value: Any, path: str = "$") -> list[tuple[str, Any]]:
    rows: list[tuple[str, Any]] = []
    if isinstance(value, dict):
        for key, child in value.items():
            child_path = f"{path}.{key}"
            rows.append((child_path, key))
            rows.extend(_walk_payload(child, child_path))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            rows.extend(_walk_payload(child, f"{path}[{index}]"))
    else:
        rows.append((path, value))
    return rows


def _split_findings(findings: list[OrderedDict[str, Any]]) -> tuple[list[OrderedDict[str, Any]], list[OrderedDict[str, Any]]]:
    blockers = [item for item in findings if item["code"] != "local_checkout_diverged"]
    warnings = [item for item in findings if item["code"] == "local_checkout_diverged"]
    return blockers, warnings


def _artifact_decl(record: dict[str, Any], key: str) -> dict[str, Any]:
    source = record.get("source") if isinstance(record.get("source"), dict) else {}
    artifacts = source.get("artifacts") if isinstance(source.get("artifacts"), dict) else {}
    artifact = artifacts.get(key) if isinstance(artifacts.get(key), dict) else {}
    return artifact


def build_report(*, root: Path, record_path: Path | None = None) -> OrderedDict[str, Any]:
    checks: list[OrderedDict[str, Any]] = []
    findings: list[OrderedDict[str, Any]] = []
    resolved_record_path = record_path or (root / ADOPTION_RECORD_REF)
    record = _read_json(resolved_record_path)
    if record is None:
        findings.append(_finding("adoption_record_missing", "Atlas adoption record is missing or invalid JSON.", path=_root_relative(resolved_record_path, root)))
        blockers, warnings = _split_findings(findings)
        return OrderedDict(
            [
                ("status", STATUS_INVALID),
                ("source", OrderedDict()),
                ("local_checkout", OrderedDict()),
                ("adoption", OrderedDict([("record_path", _root_relative(resolved_record_path, root))])),
                ("checks", checks),
                ("warnings", warnings),
                ("blockers", blockers),
            ]
        )

    source = record.get("source") if isinstance(record.get("source"), dict) else {}
    registry_decl = record.get("registry") if isinstance(record.get("registry"), dict) else {}
    governed_skill = record.get("governed_skill") if isinstance(record.get("governed_skill"), dict) else {}
    validation = record.get("validation") if isinstance(record.get("validation"), dict) else {}
    source_repo_path = str(source.get("repository_path") or "repos/playbook")
    accepted_ref = str(source.get("accepted_ref") or "")
    accepted_commit = str(source.get("accepted_commit") or "")
    pull_request = str(source.get("pull_request") or "")
    playbook_repo = _resolve_playbook_repo(root)

    adoption = OrderedDict(
        [
            ("record_path", _root_relative(resolved_record_path, root)),
            ("contract_version", str(record.get("contract_version") or "")),
            ("registry_id", str(registry_decl.get("registry_id") or "")),
            ("schema_version", str(registry_decl.get("schema_version") or "")),
            ("schema_id", str(registry_decl.get("schema_id") or "")),
            (
                "adopted_record_ids",
                OrderedDict(
                    (
                        key,
                        list(value) if isinstance(value, list) else []
                    )
                    for key, value in (registry_decl.get("adopted_record_ids") or {}).items()
                ),
            ),
            (
                "governed_skill",
                OrderedDict(
                    [
                        ("identity", str(governed_skill.get("identity") or "")),
                        ("path", str(governed_skill.get("path") or "")),
                    ]
                ),
            ),
            ("validation_command", str(validation.get("command") or "")),
            ("evidence_refs", list(record.get("evidence_refs") or [])),
            ("current_limitations", list(record.get("current_limitations") or [])),
        ]
    )
    source_summary = OrderedDict(
        [
            ("repository_path", source_repo_path),
            ("remote_owner", str(source.get("remote_owner") or "")),
            ("accepted_ref", accepted_ref),
            ("accepted_commit", accepted_commit),
            ("pull_request", pull_request),
            (
                "artifacts",
                OrderedDict(
                    [
                        ("registry", OrderedDict([("path", str(_artifact_decl(record, "registry").get("path") or "")), ("sha256", str(_artifact_decl(record, "registry").get("sha256") or "")), ("observed_sha256", None)])),
                        ("schema", OrderedDict([("path", str(_artifact_decl(record, "schema").get("path") or "")), ("sha256", str(_artifact_decl(record, "schema").get("sha256") or "")), ("observed_sha256", None)])),
                        ("governed_skill", OrderedDict([("path", str(_artifact_decl(record, "governed_skill").get("path") or "")), ("sha256", str(_artifact_decl(record, "governed_skill").get("sha256") or "")), ("observed_sha256", None)])),
                    ]
                ),
            ),
        ]
    )

    _append_check(checks, "contract_version_match", str(record.get("contract_version") or "") == CONTRACT_VERSION, expected=CONTRACT_VERSION, actual=str(record.get("contract_version") or ""))
    if str(record.get("contract_version") or "") != CONTRACT_VERSION:
        findings.append(_finding("contract_version_mismatch", "Atlas adoption record contract version does not match the expected Atlas contract.", expected=CONTRACT_VERSION, actual=str(record.get("contract_version") or "")))

    _append_check(checks, "validation_command_match", adoption["validation_command"] == EXPECTED_VALIDATION_COMMAND, expected=EXPECTED_VALIDATION_COMMAND, actual=adoption["validation_command"])
    if adoption["validation_command"] != EXPECTED_VALIDATION_COMMAND:
        findings.append(_finding("validation_command_mismatch", "Adoption record validation command is not the governed read-only validator command.", expected=EXPECTED_VALIDATION_COMMAND, actual=adoption["validation_command"]))

    repo_exists = playbook_repo.exists() and playbook_repo.is_dir()
    _append_check(checks, "source_repo_exists", repo_exists, repository_path=_root_relative(playbook_repo, root))
    if not repo_exists:
        findings.append(_finding("source_repo_missing", "Playbook owner repository does not exist at the resolved path.", repository_path=_root_relative(playbook_repo, root)))

    branch = None
    head = None
    if repo_exists:
        _, branch_out, _ = _git_text(playbook_repo, "branch", "--show-current")
        _, head_out, _ = _git_text(playbook_repo, "rev-parse", "HEAD")
        branch = branch_out or None
        head = head_out or None
    local_checkout = OrderedDict(
        [
            ("repository_path", _root_relative(playbook_repo, root)),
            ("branch", branch),
            ("head", head),
            ("matches_accepted_source", bool(branch == accepted_ref and head == accepted_commit)),
            ("uses_git_object_reads", True),
        ]
    )

    commit_available = bool(COMMIT_RE.fullmatch(accepted_commit))
    if repo_exists and commit_available:
        code, _, _ = _git_text(playbook_repo, "rev-parse", "--verify", f"{accepted_commit}^{{commit}}")
        commit_available = code == 0
    _append_check(checks, "source_commit_available", commit_available, accepted_commit=accepted_commit)
    if repo_exists and not commit_available:
        findings.append(_finding("source_commit_missing", "Accepted Playbook source commit is not present in the local Git object database.", accepted_commit=accepted_commit))

    artifact_payloads: dict[str, bytes] = {}
    artifact_json: dict[str, dict[str, Any]] = {}
    if repo_exists and commit_available:
        for key in ("registry", "schema", "governed_skill"):
            artifact = _artifact_decl(record, key)
            path = str(artifact.get("path") or "")
            read_code, stdout, _stderr = _git_bytes(playbook_repo, "show", f"{accepted_commit}:{path}")
            ok = read_code == 0
            _append_check(checks, f"source_{key}_readable", ok, path=path)
            if not ok:
                findings.append(_finding("source_path_missing", "A declared Playbook source artifact path is missing at the accepted commit.", artifact=key, path=path, accepted_commit=accepted_commit))
                continue
            artifact_payloads[key] = stdout
            digest = _sha256_hex(stdout)
            source_summary["artifacts"][key]["observed_sha256"] = digest
            recorded_digest = str(artifact.get("sha256") or "")
            digest_ok = digest == recorded_digest
            _append_check(checks, f"source_{key}_digest_match", digest_ok, expected=recorded_digest, actual=digest)
            if not digest_ok:
                findings.append(_finding("source_digest_mismatch", "Recorded source digest does not match the accepted Playbook Git object.", artifact=key, path=path, expected=recorded_digest, actual=digest))
            if key in {"registry", "schema"}:
                try:
                    payload = json.loads(stdout.decode("utf-8"))
                except (UnicodeDecodeError, json.JSONDecodeError):
                    findings.append(_finding("source_json_invalid", "A declared Playbook JSON artifact could not be parsed from the accepted commit.", artifact=key, path=path))
                    continue
                if isinstance(payload, dict):
                    artifact_json[key] = payload

    registry_payload = artifact_json.get("registry", {})
    schema_payload = artifact_json.get("schema", {})
    if registry_payload:
        registry_ok = registry_payload.get("registry_id") == adoption["registry_id"] == EXPECTED_REGISTRY_ID
        _append_check(checks, "registry_identity_match", registry_ok, expected=EXPECTED_REGISTRY_ID, actual=registry_payload.get("registry_id"))
        if not registry_ok:
            findings.append(_finding("registry_identity_mismatch", "Registry identity does not match the governed Playbook registry id.", expected=EXPECTED_REGISTRY_ID, actual=registry_payload.get("registry_id"), recorded=adoption["registry_id"]))

        schema_version_ok = registry_payload.get("schema_version") == adoption["schema_version"] == EXPECTED_REGISTRY_SCHEMA_VERSION
        _append_check(checks, "registry_schema_version_match", schema_version_ok, expected=EXPECTED_REGISTRY_SCHEMA_VERSION, actual=registry_payload.get("schema_version"))
        if not schema_version_ok:
            findings.append(_finding("registry_schema_version_mismatch", "Registry schema version does not match the governed Playbook schema version.", expected=EXPECTED_REGISTRY_SCHEMA_VERSION, actual=registry_payload.get("schema_version"), recorded=adoption["schema_version"]))
    if schema_payload:
        schema_id_ok = schema_payload.get("$id") == adoption["schema_id"] == EXPECTED_SCHEMA_ID
        _append_check(checks, "schema_identity_match", schema_id_ok, expected=EXPECTED_SCHEMA_ID, actual=schema_payload.get("$id"))
        if not schema_id_ok:
            findings.append(_finding("schema_identity_mismatch", "Registry schema identity does not match the governed Playbook schema id.", expected=EXPECTED_SCHEMA_ID, actual=schema_payload.get("$id"), recorded=adoption["schema_id"]))

    source_records = registry_payload.get("records") if isinstance(registry_payload.get("records"), list) else []
    source_id_to_lifecycle: dict[str, str] = {}
    source_statements: list[str] = []
    duplicate_source_ids: list[str] = []
    for record_item in source_records:
        if not isinstance(record_item, dict):
            continue
        record_id = str(record_item.get("id") or "")
        lifecycle = str(record_item.get("lifecycle") or "")
        statement = str(record_item.get("statement") or "")
        if statement:
            source_statements.append(statement)
        if not record_id:
            continue
        if record_id in source_id_to_lifecycle:
            duplicate_source_ids.append(record_id)
            continue
        source_id_to_lifecycle[record_id] = lifecycle
    source_ids_unique = not duplicate_source_ids
    _append_check(checks, "source_record_ids_unique", source_ids_unique, duplicate_ids=duplicate_source_ids)
    if not source_ids_unique:
        findings.append(_finding("source_record_duplicate", "Playbook source registry contains duplicate stable record ids.", duplicate_ids=duplicate_source_ids))

    adopted_groups = registry_decl.get("adopted_record_ids") if isinstance(registry_decl.get("adopted_record_ids"), dict) else {}
    adopted_flat: list[str] = []
    adopted_duplicates: list[str] = []
    lifecycle_mismatches: list[OrderedDict[str, Any]] = []
    unknown_ids: list[str] = []
    for lifecycle, ids in adopted_groups.items():
        if not isinstance(ids, list):
            continue
        for record_id in ids:
            normalized_id = str(record_id)
            if normalized_id in adopted_flat and normalized_id not in adopted_duplicates:
                adopted_duplicates.append(normalized_id)
            adopted_flat.append(normalized_id)
            source_lifecycle = source_id_to_lifecycle.get(normalized_id)
            if source_lifecycle is None:
                if normalized_id not in unknown_ids:
                    unknown_ids.append(normalized_id)
                continue
            if source_lifecycle != lifecycle:
                lifecycle_mismatches.append(OrderedDict([("id", normalized_id), ("recorded_lifecycle", lifecycle), ("source_lifecycle", source_lifecycle)]))
    _append_check(checks, "adopted_record_ids_unique", not adopted_duplicates, duplicate_ids=adopted_duplicates)
    if adopted_duplicates:
        findings.append(_finding("adopted_record_duplicate", "Atlas adoption record contains duplicate adopted record ids.", duplicate_ids=adopted_duplicates))
    _append_check(checks, "adopted_record_ids_known", not unknown_ids, unknown_ids=unknown_ids)
    if unknown_ids:
        findings.append(_finding("adopted_record_unknown", "Atlas adoption record references unknown Playbook doctrine ids.", unknown_ids=unknown_ids))
    _append_check(checks, "adopted_record_lifecycles_match", not lifecycle_mismatches, mismatches=lifecycle_mismatches)
    if lifecycle_mismatches:
        findings.append(_finding("lifecycle_mismatch", "Atlas adoption record grouped one or more adopted ids under the wrong lifecycle.", mismatches=lifecycle_mismatches))

    if source_id_to_lifecycle:
        missing_ids = sorted(set(source_id_to_lifecycle) - set(adopted_flat))
        _append_check(checks, "all_source_record_ids_adopted", not missing_ids, missing_ids=missing_ids)
        if missing_ids:
            findings.append(_finding("adopted_record_missing", "Atlas adoption record does not list every stable Playbook doctrine id.", missing_ids=missing_ids))

    copied_doctrine_paths: list[OrderedDict[str, Any]] = []
    for path, value in _walk_payload(record):
        if isinstance(value, str) and value == "statement":
            copied_doctrine_paths.append(OrderedDict([("path", path), ("reason", "statement_key_present")]))
            continue
        if isinstance(value, str) and any(statement and statement in value for statement in source_statements):
            copied_doctrine_paths.append(OrderedDict([("path", path), ("reason", "statement_body_copied")]))
    no_copied_doctrine = not copied_doctrine_paths
    _append_check(checks, "no_copied_doctrine_text", no_copied_doctrine, matches=copied_doctrine_paths)
    if not no_copied_doctrine:
        findings.append(_finding("copied_doctrine_rejected", "Atlas adoption record contains a copied doctrine statement field or statement body.", matches=copied_doctrine_paths))

    skill_payload = artifact_payloads.get("governed_skill", b"")
    skill_name = None
    if skill_payload:
        metadata = _parse_skill_metadata(skill_payload.decode("utf-8", errors="replace"))
        skill_name = metadata.get("name")
    skill_identity = str(governed_skill.get("identity") or "")
    skill_path = str(governed_skill.get("path") or "")
    declared_skill_path = str(_artifact_decl(record, "governed_skill").get("path") or "")
    skill_identity_ok = bool(SKILL_ID_RE.fullmatch(skill_identity)) and skill_identity == skill_name and skill_path == declared_skill_path
    _append_check(checks, "governed_skill_identity_match", skill_identity_ok, expected=skill_name, actual=skill_identity, path=skill_path)
    if not skill_identity_ok:
        findings.append(_finding("skill_identity_invalid", "Atlas adoption record governed skill identity or path does not match the accepted Playbook skill metadata.", expected=skill_name, actual=skill_identity, path=skill_path, source_path=declared_skill_path))

    if repo_exists and branch is not None and head is not None and (branch != accepted_ref or head != accepted_commit):
        findings.append(_finding("local_checkout_diverged", "Active local Playbook checkout differs from the accepted source ref or commit, but source verification still used Git object reads.", branch=branch, head=head, accepted_ref=accepted_ref, accepted_commit=accepted_commit))

    blockers, warnings = _split_findings(findings)
    status = STATUS_VERIFIED if not blockers else STATUS_INVALID
    return OrderedDict(
        [
            ("status", status),
            ("source", source_summary),
            ("local_checkout", local_checkout),
            ("adoption", adoption),
            ("checks", checks),
            ("warnings", warnings),
            ("blockers", blockers),
        ]
    )


def render_summary(report: dict[str, Any]) -> str:
    return "\n".join(
        [
            f"Status: {report.get('status')}",
            f"Warnings: {len(report.get('warnings', []))}",
            f"Blockers: {len(report.get('blockers', []))}",
            f"Accepted commit: {report.get('source', {}).get('accepted_commit') or 'unknown'}",
            f"Local checkout branch: {report.get('local_checkout', {}).get('branch') or 'unknown'}",
        ]
    )


def render_stdout(report: dict[str, Any], *, json_only: bool) -> str:
    json_text = json.dumps(report, indent=2) + "\n"
    if json_only:
        return json_text
    return render_summary(report) + "\n\n" + json_text


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Read-only Atlas validator for Playbook doctrine adoption by source reference.")
    parser.add_argument("--json", action="store_true", help="Emit JSON only on stdout.")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    root = atlas_root().resolve()
    try:
        report = build_report(root=root)
        sys.stdout.write(render_stdout(report, json_only=args.json))
        return 0 if report["status"] == STATUS_VERIFIED else 1
    except Exception as exc:
        report = OrderedDict(
            [
                ("status", STATUS_INTERNAL_ERROR),
                ("source", OrderedDict()),
                ("local_checkout", OrderedDict()),
                ("adoption", OrderedDict([("record_path", ADOPTION_RECORD_REF)])),
                ("checks", []),
                ("warnings", []),
                ("blockers", [_finding("internal_error", "Playbook doctrine adoption validation failed before producing a normal report.", exception=str(exc))]),
            ]
        )
        sys.stdout.write(render_stdout(report, json_only=args.json))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
