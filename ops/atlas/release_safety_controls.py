from __future__ import annotations

import hashlib
import json
import os
import re
import stat
import unicodedata
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence
from urllib.parse import unquote_to_bytes, urlsplit


_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
_PERCENT_ESCAPE_RE = re.compile(r"%(?![0-9A-Fa-f]{2})")
_CONTROL_RE = re.compile(r"[\x00-\x1f\x7f]")
_LINKAGE_MUTATION_COMMANDS = {"deploy", "dev", "link", "pull"}
_UNRESERVED_BYTES = frozenset(b"ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-._~")
_HOSTED_REVIEW_STATUSES = {"queued", "in_progress", "completed"}
_HOSTED_REVIEW_RESULTS = {"pass", "findings"}


class ReleaseSafetyViolation(ValueError):
    """A fail-closed common-control rejection with a stable, non-secret code."""

    def __init__(self, code: str, detail: str) -> None:
        super().__init__(f"{code}: {detail}")
        self.code = code
        self.detail = detail


def _fail(code: str, detail: str) -> None:
    raise ReleaseSafetyViolation(code, detail)


def _canonical_origin(origin: str) -> tuple[str, str, int | None]:
    parsed = urlsplit(origin)
    if parsed.scheme not in {"http", "https"} or not parsed.hostname:
        _fail("WORKBOX_EXPECTED_ORIGIN_INVALID", "expected origin must be absolute HTTP(S)")
    if parsed.username or parsed.password or parsed.path not in {"", "/"} or parsed.query or parsed.fragment:
        _fail("WORKBOX_EXPECTED_ORIGIN_INVALID", "expected origin must contain only scheme and authority")
    try:
        port = parsed.port
    except ValueError:
        _fail("WORKBOX_EXPECTED_ORIGIN_INVALID", "expected origin has an invalid port")
    if (parsed.scheme == "https" and port == 443) or (parsed.scheme == "http" and port == 80):
        port = None
    return parsed.scheme.lower(), parsed.hostname.lower(), port


def _decode_safe_path(path: str) -> str:
    if "\\" in path or _CONTROL_RE.search(path) or _PERCENT_ESCAPE_RE.search(path):
        _fail("WORKBOX_PATH_UNSAFE", "path contains a backslash, control character, or malformed escape")
    try:
        decoded = unquote_to_bytes(path).decode("utf-8", errors="strict")
    except UnicodeDecodeError:
        _fail("WORKBOX_PATH_UNSAFE", "path is not valid percent-encoded UTF-8")
    decoded = unicodedata.normalize("NFC", decoded)
    if "\\" in decoded or _CONTROL_RE.search(decoded):
        _fail("WORKBOX_PATH_UNSAFE", "decoded path contains a backslash or control character")
    segments = decoded.split("/")
    if any(segment in {".", ".."} for segment in segments):
        _fail("WORKBOX_PATH_TRAVERSAL", "dot segments are forbidden before canonical comparison")

    normalized_raw = unicodedata.normalize("NFC", path)

    def normalize_escape(match: re.Match[str]) -> str:
        value = int(match.group(0)[1:], 16)
        if value in _UNRESERVED_BYTES:
            return chr(value)
        return f"%{value:02X}"

    canonical = re.sub(r"%[0-9A-Fa-f]{2}", normalize_escape, normalized_raw)
    return "/" + canonical.lstrip("/")


def canonicalize_same_origin_workbox_key(
    raw_url: str,
    *,
    expected_origin: str,
    query_policy: str = "exact",
    fragment_policy: str = "reject",
) -> str:
    """Return a strict same-origin Workbox key; never performs basename matching."""

    if not isinstance(raw_url, str) or not raw_url or raw_url != raw_url.strip():
        _fail("WORKBOX_URL_INVALID", "URL must be a nonempty string without surrounding whitespace")
    if _CONTROL_RE.search(raw_url):
        _fail("WORKBOX_URL_INVALID", "URL must not contain control characters")
    if query_policy not in {"exact", "ignore", "reject"} or fragment_policy not in {"exact", "ignore", "reject"}:
        _fail("WORKBOX_URL_POLICY_INVALID", "query and fragment policies must be exact, ignore, or reject")
    if raw_url.startswith("//"):
        _fail("WORKBOX_NETWORK_PATH_REJECTED", "network-path references are ambiguous")

    expected = _canonical_origin(expected_origin)
    parsed = urlsplit(raw_url)
    if parsed.scheme or parsed.netloc:
        if parsed.scheme not in {"http", "https"} or not parsed.hostname or parsed.username or parsed.password:
            _fail("WORKBOX_FOREIGN_ORIGIN", "absolute URL is not an admissible HTTP(S) origin")
        try:
            port = parsed.port
        except ValueError:
            _fail("WORKBOX_FOREIGN_ORIGIN", "absolute URL has an invalid port")
        if (parsed.scheme == "https" and port == 443) or (parsed.scheme == "http" and port == 80):
            port = None
        observed = (parsed.scheme.lower(), parsed.hostname.lower(), port)
        if observed != expected:
            _fail("WORKBOX_FOREIGN_ORIGIN", "absolute URL does not match the expected origin")

    path = _decode_safe_path(parsed.path)
    if parsed.query and query_policy == "reject":
        _fail("WORKBOX_QUERY_REJECTED", "query semantics were not admitted")
    if parsed.fragment and fragment_policy == "reject":
        _fail("WORKBOX_FRAGMENT_REJECTED", "fragment semantics were not admitted")
    query = parsed.query if query_policy == "exact" else ""
    fragment = parsed.fragment if fragment_policy == "exact" else ""
    result = path
    if query:
        result += f"?{query}"
    if fragment:
        result += f"#{fragment}"
    return result


def verify_workbox_precache_entries(
    observed_entries: Iterable[Mapping[str, Any]],
    required_entries: Iterable[Mapping[str, Any]],
    *,
    expected_origin: str,
    query_policy: str = "exact",
    fragment_policy: str = "reject",
    allow_unexpected: bool = False,
) -> dict[str, Any]:
    """Verify canonical URL coverage plus exact byte count and SHA-256 identity."""

    def index(entries: Iterable[Mapping[str, Any]], label: str) -> dict[str, tuple[int, str]]:
        result: dict[str, tuple[int, str]] = {}
        for entry in entries:
            if not isinstance(entry, Mapping):
                _fail("WORKBOX_ENTRY_INVALID", f"{label} entry must be an object")
            key = canonicalize_same_origin_workbox_key(
                entry.get("url"),
                expected_origin=expected_origin,
                query_policy=query_policy,
                fragment_policy=fragment_policy,
            )
            if key in result:
                _fail("WORKBOX_DUPLICATE_CANONICAL_KEY", f"{label} contains a duplicate canonical key")
            byte_count = entry.get("bytes")
            digest = entry.get("sha256")
            if not isinstance(byte_count, int) or isinstance(byte_count, bool) or byte_count < 0:
                _fail("WORKBOX_BYTE_IDENTITY_INVALID", f"{label} byte count must be a nonnegative integer")
            if not isinstance(digest, str) or not _SHA256_RE.fullmatch(digest.lower()):
                _fail("WORKBOX_HASH_IDENTITY_INVALID", f"{label} SHA-256 must be 64 hexadecimal characters")
            result[key] = (byte_count, digest.lower())
        return result

    observed = index(observed_entries, "observed")
    required = index(required_entries, "required")
    missing = sorted(set(required) - set(observed))
    unexpected = sorted(set(observed) - set(required))
    if missing:
        _fail("WORKBOX_REQUIRED_ENTRY_MISSING", f"{len(missing)} required canonical entries are missing")
    if unexpected and not allow_unexpected:
        _fail("WORKBOX_UNEXPECTED_ENTRY", f"{len(unexpected)} unexpected canonical entries were observed")
    drift = sorted(key for key in required if observed[key] != required[key])
    if drift:
        _fail("WORKBOX_BYTE_OR_HASH_DRIFT", f"{len(drift)} canonical entries have byte or hash drift")
    return {
        "schema": "atlas.workbox-precache-verification.v1",
        "valid": True,
        "required_entry_count": len(required),
        "observed_entry_count": len(observed),
        "unexpected_entry_count": len(unexpected),
        "query_policy": query_policy,
        "fragment_policy": fragment_policy,
    }


def _parse_utc_timestamp(value: Any, *, code: str, label: str) -> datetime:
    if not isinstance(value, str) or not value:
        _fail(code, f"{label} must be a nonempty UTC timestamp")
    candidate = value[:-1] + "+00:00" if value.endswith("Z") else value
    try:
        parsed = datetime.fromisoformat(candidate)
    except ValueError:
        _fail(code, f"{label} must be an ISO-8601 timestamp")
    if parsed.tzinfo is None or parsed.utcoffset() != timezone.utc.utcoffset(parsed):
        _fail(code, f"{label} must be explicitly UTC")
    return parsed.astimezone(timezone.utc)


def validate_hosted_review_quiescence_premerge(
    *,
    expected_head_sha: str,
    ready_transition_head_sha: str,
    ready_transition_at: str,
    observed_at: str,
    action_time: str,
    max_observation_age_seconds: int,
    required_reviewers: Sequence[str],
    review_attempts: Iterable[Mapping[str, Any]],
    review_threads: Iterable[Mapping[str, Any]],
) -> dict[str, Any]:
    """Require positive post-ready exact-head review completion before merge."""

    if not isinstance(expected_head_sha, str) or not re.fullmatch(r"[0-9a-f]{40}|[0-9a-f]{64}", expected_head_sha):
        _fail("HOSTED_REVIEW_HEAD_INVALID", "expected head must be a lowercase 40- or 64-character hexadecimal SHA")
    if ready_transition_head_sha != expected_head_sha:
        _fail("HOSTED_REVIEW_HEAD_IDENTITY_DRIFT", "the ready transition is not bound to the expected head")
    ready_at = _parse_utc_timestamp(
        ready_transition_at,
        code="HOSTED_REVIEW_READY_TRANSITION_INVALID",
        label="ready transition",
    )
    snapshot_at = _parse_utc_timestamp(
        observed_at,
        code="HOSTED_REVIEW_OBSERVATION_INVALID",
        label="observation",
    )
    action_at = _parse_utc_timestamp(
        action_time,
        code="HOSTED_REVIEW_ACTION_TIME_INVALID",
        label="action time",
    )
    if (
        not isinstance(max_observation_age_seconds, int)
        or isinstance(max_observation_age_seconds, bool)
        or not 1 <= max_observation_age_seconds <= 300
    ):
        _fail(
            "HOSTED_REVIEW_FRESHNESS_CEILING_INVALID",
            "maximum observation age must be an integer from 1 through 300 seconds",
        )
    if snapshot_at < ready_at:
        _fail("HOSTED_REVIEW_OBSERVATION_INVALID", "observation predates the ready transition")
    if snapshot_at > action_at:
        _fail("HOSTED_REVIEW_OBSERVATION_FUTURE", "observation is later than the trusted action time")
    observation_age_seconds = (action_at - snapshot_at).total_seconds()
    if observation_age_seconds > max_observation_age_seconds:
        _fail(
            "HOSTED_REVIEW_OBSERVATION_STALE",
            "hosted-review observation is older than the admitted action-time freshness ceiling",
        )

    reviewers = list(required_reviewers)
    if not reviewers or any(not isinstance(reviewer, str) or not reviewer.strip() for reviewer in reviewers):
        _fail("HOSTED_REVIEW_REQUIRED_REVIEWERS_INVALID", "at least one named hosted reviewer is required")
    if len(set(reviewers)) != len(reviewers):
        _fail("HOSTED_REVIEW_REQUIRED_REVIEWERS_INVALID", "required hosted reviewers must be unique")

    completed_reviewers: set[str] = set()
    attempt_count = 0
    for attempt in review_attempts:
        attempt_count += 1
        if not isinstance(attempt, Mapping):
            _fail("HOSTED_REVIEW_ATTEMPT_INVALID", "each review attempt must be an object")
        reviewer = attempt.get("reviewer")
        head_sha = attempt.get("head_sha")
        status = attempt.get("status")
        if not isinstance(reviewer, str) or not reviewer:
            _fail("HOSTED_REVIEW_ATTEMPT_INVALID", "review attempt reviewer is required")
        if head_sha != expected_head_sha:
            _fail("HOSTED_REVIEW_HEAD_IDENTITY_DRIFT", "a hosted review attempt is not bound to the expected head")
        if status not in _HOSTED_REVIEW_STATUSES:
            _fail("HOSTED_REVIEW_ATTEMPT_INVALID", "review attempt status is not recognized")
        started_at = _parse_utc_timestamp(
            attempt.get("started_at"),
            code="HOSTED_REVIEW_ATTEMPT_INVALID",
            label="review attempt start",
        )
        if started_at <= ready_at:
            _fail("HOSTED_REVIEW_COMPLETION_PREDATES_READY", "pre-ready review evidence cannot satisfy the merge gate")
        if status != "completed":
            _fail("HOSTED_REVIEW_NOT_QUIESCENT", "a hosted review attempt remains queued or in progress")
        completed_at = _parse_utc_timestamp(
            attempt.get("completed_at"),
            code="HOSTED_REVIEW_ATTEMPT_INVALID",
            label="review attempt completion",
        )
        if completed_at < started_at or completed_at > snapshot_at:
            _fail("HOSTED_REVIEW_ATTEMPT_INVALID", "review completion is outside the admitted observation window")
        result = attempt.get("result")
        if result not in _HOSTED_REVIEW_RESULTS:
            _fail("HOSTED_REVIEW_ATTEMPT_INVALID", "completed review result must be pass or findings")
        if result == "findings":
            _fail("HOSTED_REVIEW_FINDINGS_PRESENT", "a completed exact-head hosted review has findings")
        completed_reviewers.add(reviewer)

    missing = sorted(set(reviewers) - completed_reviewers)
    if missing:
        _fail(
            "HOSTED_REVIEW_COMPLETION_MISSING",
            "every required hosted reviewer must complete on the exact head after the ready transition",
        )

    thread_count = 0
    for thread in review_threads:
        thread_count += 1
        if not isinstance(thread, Mapping):
            _fail("HOSTED_REVIEW_THREAD_INVALID", "each review thread must be an object")
        is_resolved = thread.get("is_resolved")
        is_outdated = thread.get("is_outdated")
        if not isinstance(is_resolved, bool) or not isinstance(is_outdated, bool):
            _fail("HOSTED_REVIEW_THREAD_INVALID", "review thread resolution and outdated state must be explicit booleans")
        if is_outdated:
            continue
        if thread.get("head_sha") != expected_head_sha:
            _fail("HOSTED_REVIEW_HEAD_IDENTITY_DRIFT", "a current review thread is not bound to the expected head")
        if not is_resolved and not is_outdated:
            _fail("HOSTED_REVIEW_THREAD_UNRESOLVED", "a non-outdated exact-head review thread remains unresolved")

    return {
        "schema": "atlas.hosted-review-quiescence-premerge.v1",
        "valid": True,
        "exact_head": expected_head_sha,
        "ready_transition_head_exact": True,
        "ready_transition_at": ready_transition_at,
        "observed_at": observed_at,
        "action_time": action_time,
        "observation_age_seconds": observation_age_seconds,
        "max_observation_age_seconds": max_observation_age_seconds,
        "required_reviewer_count": len(reviewers),
        "completed_reviewer_count": len(set(reviewers) & completed_reviewers),
        "review_attempt_count": attempt_count,
        "review_thread_count": thread_count,
        "queued_or_in_progress": 0,
        "unresolved_non_outdated_threads": 0,
        "provider_invocations": 0,
    }


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _is_link_or_reparse(path: Path) -> bool:
    try:
        info = path.lstat()
    except OSError:
        return False
    attributes = getattr(info, "st_file_attributes", 0)
    reparse_flag = getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0x400)
    return path.is_symlink() or bool(attributes & reparse_flag)


def _ensure_unambiguous_path(path: Path, stop: Path) -> None:
    current = path
    while True:
        if _is_link_or_reparse(current):
            _fail("VERCEL_BINDING_PATH_AMBIGUOUS", "workspace or binding path crosses a link or reparse point")
        if current == stop:
            return
        if current.parent == current:
            _fail("VERCEL_WORKSPACE_IDENTITY_MISMATCH", "binding path is outside the expected workspace")
        current = current.parent


def _binding_from_project_json(value: Mapping[str, Any]) -> tuple[str, str]:
    project_id = value.get("projectId")
    org_id = value.get("orgId")
    if not isinstance(project_id, str) or not project_id or not isinstance(org_id, str) or not org_id:
        _fail("VERCEL_BINDING_SCHEMA_INVALID", "project.json requires nonempty projectId and orgId")
    return project_id, org_id


def _binding_from_repo_json(value: Mapping[str, Any], relative_workspace: str) -> tuple[str, str]:
    projects = value.get("projects")
    if not isinstance(projects, list):
        _fail("VERCEL_BINDING_SCHEMA_INVALID", "repo.json requires a projects array")
    normalized_relative = relative_workspace.replace("\\", "/").strip("/") or "."
    matches = []
    for project in projects:
        if not isinstance(project, Mapping):
            continue
        directory = str(project.get("directory", ".")).replace("\\", "/").strip("/") or "."
        if directory == normalized_relative:
            matches.append(project)
    if len(matches) != 1:
        _fail("VERCEL_REPO_BINDING_AMBIGUOUS", "repo.json must identify exactly one project for the workspace")
    project_id = matches[0].get("id")
    org_id = matches[0].get("orgId", value.get("orgId"))
    if not isinstance(project_id, str) or not project_id or not isinstance(org_id, str) or not org_id:
        _fail("VERCEL_BINDING_SCHEMA_INVALID", "repo.json project requires id and project or top-level orgId")
    return project_id, org_id


def _parse_exact_curl_profile(args: Sequence[str]) -> tuple[str, str, str]:
    options: dict[str, str] = {}
    positionals: list[str] = []
    index = 0
    while index < len(args):
        token = args[index]
        if token.startswith("-"):
            option, separator, inline_value = token.partition("=")
            if option not in {"--deployment", "--scope"}:
                _fail("VERCEL_COMMAND_OPTION_UNCLASSIFIED", f"option {option} is outside the installed curl profile")
            if option in options:
                _fail("VERCEL_COMMAND_TARGET_AMBIGUOUS", f"option {option} must appear exactly once")
            if separator:
                value = inline_value
            else:
                index += 1
                value = args[index] if index < len(args) else ""
            if not value or value.startswith("-"):
                _fail("VERCEL_COMMAND_TARGET_MISSING", f"required explicit option {option} has no value")
            options[option] = value
        else:
            positionals.append(token)
        index += 1
    missing = [option for option in ("--deployment", "--scope") if option not in options]
    if missing:
        _fail("VERCEL_COMMAND_TARGET_MISSING", f"required explicit option {missing[0]} is missing")
    if len(positionals) != 1 or not positionals[0]:
        _fail("VERCEL_COMMAND_PATH_AMBIGUOUS", "curl profile requires exactly one explicit request path")
    return positionals[0], options["--deployment"], options["--scope"]


def validate_vercel_no_auto_link_preflight(
    *,
    workspace_root: Path,
    expected_workspace_root: Path,
    expected_project_id: str,
    expected_org_id: str,
    expected_binding_sha256: str,
    command_args: Sequence[str],
    environment: Mapping[str, str] | None = None,
) -> dict[str, Any]:
    """Validate immutable local Vercel binding and command targeting without invoking Vercel."""

    workspace = workspace_root.absolute()
    expected_workspace = expected_workspace_root.absolute()
    if workspace != expected_workspace or not workspace.is_dir():
        _fail("VERCEL_WORKSPACE_IDENTITY_MISMATCH", "workspace is missing or differs from the immutable expected root")
    _ensure_unambiguous_path(workspace, workspace.anchor and Path(workspace.anchor) or workspace)

    vercel_dir = workspace / ".vercel"
    project_path = vercel_dir / "project.json"
    repo_candidates = [candidate for candidate in (workspace / ".vercel" / "repo.json", workspace.parent / ".vercel" / "repo.json") if candidate.is_file()]
    direct_exists = project_path.is_file()
    if direct_exists and repo_candidates:
        _fail("VERCEL_BINDING_AMBIGUOUS", "both direct and repository bindings are present")
    if not direct_exists and len(repo_candidates) != 1:
        _fail("VERCEL_BINDING_MISSING", "exactly one project.json or repo.json binding is required")
    binding_path = project_path if direct_exists else repo_candidates[0]
    _ensure_unambiguous_path(binding_path, workspace if binding_path.is_relative_to(workspace) else workspace.parent)
    if not binding_path.is_file() or _is_link_or_reparse(binding_path):
        _fail("VERCEL_BINDING_PATH_AMBIGUOUS", "binding must be a regular non-link file")
    observed_hash = _sha256(binding_path)
    if observed_hash != expected_binding_sha256.removeprefix("sha256:").lower():
        _fail("VERCEL_BINDING_HASH_DRIFT", "binding bytes differ from the admitted immutable preimage")
    try:
        value = json.loads(binding_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError):
        _fail("VERCEL_BINDING_SCHEMA_INVALID", "binding is not readable UTF-8 JSON")
    if not isinstance(value, Mapping):
        _fail("VERCEL_BINDING_SCHEMA_INVALID", "binding must be a JSON object")
    if binding_path.name == "project.json":
        project_id, org_id = _binding_from_project_json(value)
        binding_kind = "project"
    else:
        relative = os.path.relpath(workspace, binding_path.parent.parent)
        project_id, org_id = _binding_from_repo_json(value, relative)
        binding_kind = "repo"
    if project_id != expected_project_id:
        _fail("VERCEL_PROJECT_BINDING_MISMATCH", "binding project ID differs from the expected immutable identity")
    if org_id != expected_org_id:
        _fail("VERCEL_ORG_BINDING_MISMATCH", "binding organization/team ID differs from the expected immutable identity")

    env = dict(os.environ) if environment is None else dict(environment)
    env_project = env.get("VERCEL_PROJECT_ID")
    env_org = env.get("VERCEL_ORG_ID")
    if bool(env_project) != bool(env_org):
        _fail("VERCEL_ENV_BINDING_PARTIAL", "VERCEL_PROJECT_ID and VERCEL_ORG_ID must be supplied together")
    if env_project and (env_project != expected_project_id or env_org != expected_org_id):
        _fail("VERCEL_ENV_BINDING_MISMATCH", "environment binding differs from the expected immutable identity")

    args = list(command_args)
    if not args:
        _fail("VERCEL_COMMAND_SURFACE_UNCLASSIFIED", "command arguments are required")
    command = args[0].lower()
    if command in _LINKAGE_MUTATION_COMMANDS:
        _fail("VERCEL_LINKAGE_MUTATION_COMMAND_FORBIDDEN", "linkage-capable mutation command is outside this common preflight")
    if command != "curl":
        _fail("VERCEL_COMMAND_SURFACE_UNCLASSIFIED", "only the locally verified curl command profile is installed")
    request_path, deployment, scope = _parse_exact_curl_profile(args[1:])
    if scope != expected_org_id:
        _fail("VERCEL_COMMAND_SCOPE_MISMATCH", "explicit command scope differs from the expected organization/team")
    return {
        "schema": "atlas.vercel-no-auto-link-preflight.v1",
        "valid": True,
        "binding_kind": binding_kind,
        "binding_sha256": f"sha256:{observed_hash}",
        "workspace_identity_exact": True,
        "project_identity_exact": True,
        "organization_identity_exact": True,
        "command": "curl",
        "request_path_present": bool(request_path),
        "deployment_target_present": bool(deployment),
        "scope_exact": True,
        "provider_invocations": 0,
    }
