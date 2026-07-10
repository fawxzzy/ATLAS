from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import sys
from collections import OrderedDict
from pathlib import Path
from typing import Any, Iterable

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from ops._atlas import atlas_root, normalize_slashes

SCHEMA_VERSION = "atlas.cortex.codex_closeout_ingestion_read_model.v1"
STATUS_OK = "ok"
STATUS_ADVISORY = "advisory_gap"
STATUS_CONFLICT = "conflict"
STATUS_BLOCKER = "blocker"
STATUS_INTERNAL_ERROR = "internal_error"

NEXT_WORKER_PACKET = "Cortex Dual-Mode Replacement Readiness Codex closeout ingestion read-model first-implementation worker packet 1"
RECONCILIATION_PACKET = "Cortex Dual-Mode Replacement Readiness Codex closeout ingestion read-model first-implementation worker cluster reconciliation"
DUAL_MODE_MARKER = "Cortex Dual-Mode Replacement Readiness"
DUAL_MODE_MANIFEST_REF = "docs/memory/initiatives/continuity-manifest-cortex-dual-mode-replacement-readiness.json"
MARKER_BOARD_REF = "docs/atlas-book/02-lanes-and-markers.md"
VALIDATION_REF = "runtime/receipts/validation/stack-validation.latest.json"

TOP_LEVEL_FIELDS = (
    "schema_version",
    "status",
    "root",
    "branch",
    "head",
    "source_refs",
    "source_digests",
    "closeouts",
    "normalized_state",
    "verification_summary",
    "verified_claims",
    "unverified_claims",
    "conflicts",
    "stale_claims",
    "missing_receipts",
    "marker_deltas",
    "next_packet",
    "authority_denials",
    "warnings",
    "blockers",
    "safe_to_use",
    "next_recommended_packet",
)
CLAIM_FIELDS = (
    "claim_id",
    "category",
    "field",
    "claimed_value",
    "evidence_class",
    "evidence_refs",
    "verified_value",
    "status",
    "conflict_reason",
)
AUTHORITY_DENIALS = (
    "cannot execute a packet",
    "cannot mutate a repository",
    "cannot stage, commit, or push",
    "cannot change a marker",
    "cannot approve a PR",
    "cannot deploy",
    "cannot access secrets",
    "cannot scrape hidden transcripts",
    "cannot treat closeout prose as final truth",
    "cannot override ATLAS receipts, manifests, or selectors",
)
PROTECTED_PREFIXES = (
    ".github/workflows",
    ".playwright-mcp",
    ".vercel",
    "archive",
    "repos",
    "secrets",
)
HIDDEN_CONTEXT_PREFIXES = (
    ".codex",
    "runtime/chats",
    "runtime/session",
    "runtime/sessions",
    "runtime/transcripts",
    "runtime/atlas/conversations",
    "runtime/atlas/sessions",
    "tmp/chats",
    "tmp/transcripts",
)
ALLOWED_SOURCE_PREFIXES = (
    "tmp/atlas",
    "docs/ops",
    "docs/memory/initiatives",
    "docs/atlas-book",
)
VERIFIABLE_FIELDS = {
    "branch",
    "head",
    "remote_head",
    "parity",
    "commits",
    "validation",
    "marker_changes",
    "current_marker_board",
    "receipts_created",
    "receipt_refs",
    "source_refs",
    "next_exact_packet",
}
CORE_CLOSEOUT_FIELDS = (
    "message_id",
    "captured_at",
    "source_ref",
    "source_digest",
    "branch",
    "head",
    "remote_head",
    "parity",
    "commits",
    "receipts_created",
    "receipt_refs",
    "source_refs",
    "bundles_attempted",
    "bundles_completed",
    "files_changed",
    "tests_run",
    "validation",
    "marker_changes",
    "current_marker_board",
    "blockers",
    "risks",
    "residue",
    "boundaries_preserved",
    "owner_repos_mutated",
    "platforms_mutated",
    "secrets_touched",
    "next_exact_packet",
    "completion_percent",
    "prose",
)


def _finding(code: str, message: str, **details: Any) -> OrderedDict[str, Any]:
    payload: OrderedDict[str, Any] = OrderedDict([("code", code), ("message", message)])
    if details:
        payload["details"] = details
    return payload


def _claim(
    *,
    claim_id: str,
    category: str,
    field: str,
    claimed_value: Any,
    evidence_class: str,
    evidence_refs: Iterable[str] = (),
    verified_value: Any = None,
    status: str,
    conflict_reason: str | None = None,
) -> OrderedDict[str, Any]:
    return OrderedDict(
        [
            ("claim_id", claim_id),
            ("category", category),
            ("field", field),
            ("claimed_value", claimed_value),
            ("evidence_class", evidence_class),
            ("evidence_refs", sorted(set(evidence_refs))),
            ("verified_value", verified_value),
            ("status", status),
            ("conflict_reason", conflict_reason),
        ]
    )


def _git_stdout(root: Path, *args: str) -> str | None:
    completed = subprocess.run(
        ["git", "-C", str(root), *args],
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    if completed.returncode != 0:
        return None
    return completed.stdout.strip()


def collect_git_state(root: Path) -> tuple[str | None, str | None]:
    return _git_stdout(root, "branch", "--show-current"), _git_stdout(root, "rev-parse", "HEAD")


def collect_git_parity(root: Path) -> OrderedDict[str, Any] | None:
    raw = _git_stdout(root, "rev-list", "--left-right", "--count", "origin/main...HEAD")
    if not raw:
        return None
    parts = raw.replace("\t", " ").split()
    if len(parts) != 2:
        return None
    try:
        behind, ahead = int(parts[0]), int(parts[1])
    except ValueError:
        return None
    return OrderedDict([("behind", behind), ("ahead", ahead), ("raw", raw)])


def commit_exists(root: Path, commit: str) -> bool:
    return _git_stdout(root, "cat-file", "-e", f"{commit}^{{commit}}") == ""


def _has_env_component(ref: str) -> bool:
    return any(part.startswith(".env") for part in ref.split("/"))


def _is_prefix_match(ref: str, prefixes: tuple[str, ...]) -> bool:
    return any(ref == prefix or ref.startswith(f"{prefix}/") for prefix in prefixes)


def _is_platform_live_data_ref(ref: str) -> bool:
    lowered = ref.lower()
    live_platform_tokens = (
        "vercel-live",
        "supabase-live",
        "live-vercel",
        "live-supabase",
        "vercel-runtime-log",
        "supabase-runtime-log",
        "vercel-deploy-log",
        "supabase-export",
    )
    return any(token in lowered for token in live_platform_tokens)


def _normalize_ref(candidate: str | Path, root: Path) -> tuple[str | None, OrderedDict[str, Any] | None]:
    value = Path(candidate)
    if value.is_absolute():
        return None, _finding("absolute_path_forbidden", "Path must be root-relative.", path=normalize_slashes(str(value)))
    ref = normalize_slashes(str(value)).strip("/")
    if not ref or ref.startswith("../") or "/../" in f"/{ref}/":
        return None, _finding("parent_traversal_forbidden", "Path must not use parent traversal.", path=ref)
    if _has_env_component(ref):
        return None, _finding("secret_path_forbidden", "Path targets an .env secret surface.", path=ref)
    if _is_prefix_match(ref, PROTECTED_PREFIXES):
        return None, _finding("protected_path_forbidden", "Owner or protected surfaces are not admitted.", path=ref)
    lowered_parts = tuple(part.lower() for part in ref.split("/"))
    hidden_tokens = {"transcript", "transcripts", "chat", "chats", "session", "sessions"}
    if _is_prefix_match(ref, HIDDEN_CONTEXT_PREFIXES) or any(part in hidden_tokens for part in lowered_parts):
        return None, _finding("hidden_context_path_forbidden", "Hidden transcript, chat, or session state is not admitted.", path=ref)
    if _is_platform_live_data_ref(ref):
        return None, _finding("platform_live_data_forbidden", "Vercel or Supabase live data is not admitted.", path=ref)
    resolved = (root / ref).resolve()
    try:
        resolved.relative_to(root.resolve())
    except ValueError:
        return None, _finding("outside_root_path", "Path must stay inside the ATLAS root.", path=ref)
    return ref, None


def is_allowed_source_ref(ref: str) -> bool:
    return _is_prefix_match(ref, ALLOWED_SOURCE_PREFIXES)


def resolve_sources(root: Path, requested_sources: list[str] | None) -> tuple[list[str], list[OrderedDict[str, Any]]]:
    refs: list[str] = []
    errors: list[OrderedDict[str, Any]] = []
    seen: set[str] = set()
    for source in requested_sources or []:
        ref, error = _normalize_ref(source, root)
        if error is not None:
            errors.append(error)
            continue
        if ref is None:
            continue
        if not is_allowed_source_ref(ref):
            errors.append(_finding("source_not_admitted", "Source path is outside the admitted closeout source classes.", path=ref))
            continue
        if ref not in seen:
            refs.append(ref)
            seen.add(ref)
    if not requested_sources:
        errors.append(_finding("source_required", "At least one explicit --source path is required unless --schema-only is used."))
    return refs, errors


def validate_output_path(root: Path, output: str) -> tuple[Path | None, OrderedDict[str, Any] | None]:
    ref, error = _normalize_ref(output, root)
    if error is not None or ref is None:
        return None, error
    if not ref.startswith("tmp/atlas/") or not ref.endswith(".json"):
        return None, _finding("non_tmp_atlas_json_output_path", "Output path must be under tmp/atlas/** and end with .json.", path=ref)
    return (root / ref).resolve(), None


def _sha256_bytes(data: bytes) -> str:
    return f"sha256:{hashlib.sha256(data).hexdigest()}"


def _stable_digest(value: Any) -> str:
    encoded = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")
    return _sha256_bytes(encoded)


def _load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def read_validation_summary(root: Path) -> tuple[OrderedDict[str, int], str | None]:
    counts = OrderedDict([("critical", 0), ("error", 0), ("warning", 0), ("info", 0)])
    path = root / VALIDATION_REF
    if not path.exists():
        return counts, None
    try:
        payload = _load_json(path)
    except Exception:
        return counts, None
    summary = payload.get("summary") if isinstance(payload, dict) else {}
    if not isinstance(summary, dict):
        return counts, None
    for key in counts:
        try:
            counts[key] = int(summary.get(key, 0) or 0)
        except (TypeError, ValueError):
            counts[key] = 0
    return counts, VALIDATION_REF


def read_manifest_next_packet(root: Path) -> tuple[str | None, str | None]:
    path = root / DUAL_MODE_MANIFEST_REF
    if not path.exists():
        return None, None
    try:
        payload = _load_json(path)
    except Exception:
        return None, None
    metadata = payload.get("metadata") if isinstance(payload, dict) else {}
    ladder = metadata.get("next_package_ladder") if isinstance(metadata, dict) else []
    if not isinstance(ladder, list) or not ladder or not isinstance(ladder[0], dict):
        return None, DUAL_MODE_MANIFEST_REF
    package = ladder[0].get("package")
    return (str(package).strip() if isinstance(package, str) and package.strip() else None), DUAL_MODE_MANIFEST_REF


def read_marker_board(root: Path) -> tuple[OrderedDict[str, int], str | None]:
    path = root / MARKER_BOARD_REF
    board: OrderedDict[str, int] = OrderedDict()
    if not path.exists():
        return board, None
    try:
        text = path.read_text(encoding="utf-8")
    except OSError:
        return board, None
    pattern = re.compile(r"^\s*[-*]\s+(.+?):\s*`?(\d+)%`?", re.MULTILINE)
    for match in pattern.finditer(text):
        marker = match.group(1).strip().strip("`")
        board[marker] = int(match.group(2))
    return OrderedDict(sorted(board.items())), MARKER_BOARD_REF


def _normalize_validation(value: Any) -> OrderedDict[str, int] | None:
    if not isinstance(value, dict):
        return None
    summary = value.get("summary") if isinstance(value.get("summary"), dict) else value
    result = OrderedDict([("critical", 0), ("error", 0), ("warning", 0), ("info", 0)])
    for key in result:
        try:
            result[key] = int(summary.get(key, 0) or 0)
        except (AttributeError, TypeError, ValueError):
            return None
    return result


def _normalize_parity(value: Any) -> OrderedDict[str, Any] | None:
    if isinstance(value, dict):
        result = OrderedDict()
        try:
            result["behind"] = int(value.get("behind", 0) or 0)
            result["ahead"] = int(value.get("ahead", 0) or 0)
        except (TypeError, ValueError):
            return None
        raw = value.get("raw")
        if isinstance(raw, str):
            result["raw"] = raw
        return result
    if isinstance(value, str):
        match = re.search(r"behind\s*[:=]\s*(\d+).*ahead\s*[:=]\s*(\d+)", value, re.IGNORECASE)
        if match:
            return OrderedDict([("behind", int(match.group(1))), ("ahead", int(match.group(2))), ("raw", value)])
        parts = value.replace("\t", " ").split()
        if len(parts) == 2 and all(part.isdigit() for part in parts):
            return OrderedDict([("behind", int(parts[0])), ("ahead", int(parts[1])), ("raw", value)])
    return None


def _normalize_marker_board(value: Any) -> OrderedDict[str, int] | None:
    if not isinstance(value, dict):
        return None
    board: OrderedDict[str, int] = OrderedDict()
    for marker, percent in value.items():
        if not isinstance(marker, str) or not marker.strip():
            continue
        try:
            board[marker.strip()] = int(percent)
        except (TypeError, ValueError):
            return None
    return OrderedDict(sorted(board.items()))


def _normalize_marker_changes(value: Any) -> list[OrderedDict[str, Any]]:
    if not isinstance(value, list):
        return []
    changes: list[OrderedDict[str, Any]] = []
    for item in value:
        if not isinstance(item, dict):
            continue
        marker = item.get("marker")
        if not isinstance(marker, str) or not marker.strip():
            continue
        change = OrderedDict([("marker", marker.strip())])
        for field in ("from", "from_percent", "old", "to", "to_percent", "new"):
            if field in item:
                change[field] = item[field]
        if "to" not in change:
            for alias in ("to_percent", "new"):
                if alias in change:
                    change["to"] = change[alias]
                    break
        if "from" not in change:
            for alias in ("from_percent", "old"):
                if alias in change:
                    change["from"] = change[alias]
                    break
        changes.append(change)
    return changes


def _coerce_string_list(value: Any) -> list[str]:
    if isinstance(value, str):
        return [value]
    if not isinstance(value, list):
        return []
    return [str(item).strip() for item in value if isinstance(item, (str, int)) and str(item).strip()]


def _category_for_field(field: str) -> str:
    if field in {"branch", "head", "remote_head", "parity", "commits"}:
        return "git"
    if field == "validation":
        return "validation"
    if field in {"marker_changes", "current_marker_board", "completion_percent"}:
        return "marker"
    if field in {"receipts_created", "receipt_refs", "source_refs"}:
        return "receipt"
    if field == "next_exact_packet":
        return "manifest"
    if field in {"owner_repos_mutated", "platforms_mutated", "secrets_touched", "boundaries_preserved"}:
        return "authority"
    if field in {"blockers", "risks", "residue"}:
        return "risk"
    return "closeout"


def _extract_key_value(text: str, keys: tuple[str, ...]) -> str | None:
    for key in keys:
        pattern = re.compile(rf"^\s*(?:[-*]\s*)?{re.escape(key)}\s*[:=]\s*(.+?)\s*$", re.IGNORECASE | re.MULTILINE)
        match = pattern.search(text)
        if match:
            return match.group(1).strip().strip("`")
    return None


def _parse_markdown_closeout(text: str) -> OrderedDict[str, Any]:
    closeout: OrderedDict[str, Any] = OrderedDict()
    mappings = {
        "message_id": ("message_id", "message id"),
        "captured_at": ("captured_at", "captured at"),
        "branch": ("branch",),
        "head": ("head",),
        "remote_head": ("remote_head", "remote head"),
        "parity": ("parity",),
        "next_exact_packet": ("next_exact_packet", "next exact packet"),
        "completion_percent": ("completion_percent", "completion percent"),
    }
    for field, keys in mappings.items():
        value = _extract_key_value(text, keys)
        if value is not None:
            if field == "completion_percent":
                percent_match = re.search(r"\d+", value)
                closeout[field] = int(percent_match.group(0)) if percent_match else value
            else:
                closeout[field] = value
    validation_match = re.search(
        r"critical\s*=\s*(\d+)\s+error\s*=\s*(\d+)\s+warning\s*=\s*(\d+)\s+info\s*=\s*(\d+)",
        text,
        re.IGNORECASE,
    )
    if validation_match:
        closeout["validation"] = OrderedDict(
            [
                ("critical", int(validation_match.group(1))),
                ("error", int(validation_match.group(2))),
                ("warning", int(validation_match.group(3))),
                ("info", int(validation_match.group(4))),
            ]
        )
    marker_match = re.search(rf"{re.escape(DUAL_MODE_MARKER)}\s*:\s*`?(\d+)%`?", text)
    if marker_match:
        closeout["current_marker_board"] = OrderedDict([(DUAL_MODE_MARKER, int(marker_match.group(1)))])
    closeout["prose"] = text.strip()
    return closeout


def _iter_closeout_payloads(payload: Any) -> list[dict[str, Any]]:
    if isinstance(payload, dict) and isinstance(payload.get("closeouts"), list):
        return [item for item in payload["closeouts"] if isinstance(item, dict)]
    if isinstance(payload, dict):
        return [payload]
    return []


def _normalize_closeout(raw: dict[str, Any], *, source_ref: str, source_digest: str) -> OrderedDict[str, Any]:
    closeout: OrderedDict[str, Any] = OrderedDict()
    for field in CORE_CLOSEOUT_FIELDS:
        if field in raw:
            closeout[field] = raw[field]
    if "source_ref" not in closeout:
        closeout["source_ref"] = source_ref
    if "source_digest" not in closeout:
        closeout["source_digest"] = source_digest
    if "message_id" not in closeout:
        closeout["message_id"] = f"source:{source_digest}"
    return closeout


def load_closeouts(root: Path, source_refs: list[str]) -> tuple[list[OrderedDict[str, Any]], OrderedDict[str, str], list[OrderedDict[str, Any]]]:
    closeouts: list[OrderedDict[str, Any]] = []
    source_digests: OrderedDict[str, str] = OrderedDict()
    blockers: list[OrderedDict[str, Any]] = []
    seen: set[str] = set()

    for ref in source_refs:
        path = (root / ref).resolve()
        if not path.exists() or not path.is_file():
            blockers.append(_finding("source_missing", "Source path is missing.", path=ref))
            continue
        try:
            data = path.read_bytes()
        except OSError as exc:
            blockers.append(_finding("source_read_failed", "Source path could not be read.", path=ref, exception=str(exc)))
            continue
        source_digest = _sha256_bytes(data)
        source_digests[ref] = source_digest
        text = data.decode("utf-8-sig", errors="replace")
        raw_closeouts: list[dict[str, Any]]
        if path.suffix.lower() == ".json":
            try:
                payload = json.loads(text)
            except json.JSONDecodeError as exc:
                blockers.append(_finding("source_json_invalid", "Structured closeout JSON is malformed.", path=ref, exception=str(exc)))
                continue
            raw_closeouts = _iter_closeout_payloads(payload)
        elif path.suffix.lower() in {".md", ".txt"}:
            raw_closeouts = [_parse_markdown_closeout(text)]
        else:
            blockers.append(_finding("source_extension_not_admitted", "Closeout source must be .json, .md, or .txt.", path=ref))
            continue
        if not raw_closeouts:
            blockers.append(_finding("closeout_payload_missing", "Source did not contain a closeout object.", path=ref))
            continue
        for raw in raw_closeouts:
            normalized = _normalize_closeout(raw, source_ref=ref, source_digest=source_digest)
            key = str(normalized.get("message_id") or normalized.get("source_digest"))
            if key in seen:
                continue
            seen.add(key)
            closeouts.append(normalized)
    return closeouts, source_digests, blockers


def _verified_claim(claim_id: str, category: str, field: str, claimed: Any, verified: Any, evidence_class: str, refs: Iterable[str]) -> OrderedDict[str, Any]:
    return _claim(
        claim_id=claim_id,
        category=category,
        field=field,
        claimed_value=claimed,
        evidence_class=evidence_class,
        evidence_refs=refs,
        verified_value=verified,
        status="verified",
    )


def _conflict_claim(claim_id: str, category: str, field: str, claimed: Any, verified: Any, reason: str, refs: Iterable[str]) -> OrderedDict[str, Any]:
    return _claim(
        claim_id=claim_id,
        category=category,
        field=field,
        claimed_value=claimed,
        evidence_class="conflicted",
        evidence_refs=refs,
        verified_value=verified,
        status="conflict",
        conflict_reason=reason,
    )


def _stale_claim(claim_id: str, category: str, field: str, claimed: Any, verified: Any, reason: str, refs: Iterable[str]) -> OrderedDict[str, Any]:
    return _claim(
        claim_id=claim_id,
        category=category,
        field=field,
        claimed_value=claimed,
        evidence_class="stale",
        evidence_refs=refs,
        verified_value=verified,
        status="stale",
        conflict_reason=reason,
    )


def _unverified_claim(claim_id: str, category: str, field: str, claimed: Any, reason: str | None = None) -> OrderedDict[str, Any]:
    return _claim(
        claim_id=claim_id,
        category=category,
        field=field,
        claimed_value=claimed,
        evidence_class="unverified",
        evidence_refs=[],
        verified_value=None,
        status="unverified",
        conflict_reason=reason,
    )


def _forbidden_claim(claim_id: str, category: str, field: str, claimed: Any, reason: str) -> OrderedDict[str, Any]:
    return _claim(
        claim_id=claim_id,
        category=category,
        field=field,
        claimed_value=claimed,
        evidence_class="forbidden",
        evidence_refs=[],
        verified_value=None,
        status="forbidden",
        conflict_reason=reason,
    )


def _field_claims(
    *,
    root: Path,
    closeout: OrderedDict[str, Any],
    closeout_index: int,
    verify_git: bool,
    verify_receipts: bool,
    verify_marker_board: bool,
    branch: str | None,
    head: str | None,
    parity: OrderedDict[str, Any] | None,
    validation_summary: OrderedDict[str, int],
    validation_ref: str | None,
    marker_board: OrderedDict[str, int],
    marker_board_ref: str | None,
    manifest_next_packet: str | None,
    manifest_ref: str | None,
) -> tuple[list[OrderedDict[str, Any]], list[OrderedDict[str, Any]], list[OrderedDict[str, Any]], list[OrderedDict[str, Any]], list[OrderedDict[str, Any]], list[OrderedDict[str, Any]]]:
    verified: list[OrderedDict[str, Any]] = []
    unverified: list[OrderedDict[str, Any]] = []
    conflicts: list[OrderedDict[str, Any]] = []
    stale: list[OrderedDict[str, Any]] = []
    missing_receipts: list[OrderedDict[str, Any]] = []
    marker_deltas: list[OrderedDict[str, Any]] = []

    closeout_id = str(closeout.get("message_id") or f"closeout-{closeout_index}")
    for field, claimed in closeout.items():
        if field in {"message_id", "captured_at", "source_ref", "source_digest"}:
            continue
        category = _category_for_field(field)
        claim_id = f"{closeout_id}:{field}"
        if field not in VERIFIABLE_FIELDS:
            if field == "prose":
                unverified.append(_unverified_claim(claim_id, "prose", field, claimed, "Closeout prose is advisory and cannot become final truth by itself."))
            elif field in {"owner_repos_mutated", "platforms_mutated", "secrets_touched"} and claimed:
                conflicts.append(_forbidden_claim(claim_id, category, field, claimed, "Claim indicates protected authority was used."))
            else:
                unverified.append(_unverified_claim(claim_id, category, field, claimed))
            continue
        if field == "branch":
            if verify_git and branch is not None:
                if claimed == branch:
                    verified.append(_verified_claim(claim_id, category, field, claimed, branch, "git_verified", ["git:branch --show-current"]))
                else:
                    conflicts.append(_conflict_claim(claim_id, category, field, claimed, branch, "Claimed branch differs from current branch.", ["git:branch --show-current"]))
            else:
                unverified.append(_unverified_claim(claim_id, category, field, claimed))
        elif field == "head":
            if verify_git and head is not None:
                if claimed == head:
                    verified.append(_verified_claim(claim_id, category, field, claimed, head, "git_verified", ["git:rev-parse HEAD"]))
                elif isinstance(claimed, str) and commit_exists(root, claimed):
                    stale.append(_stale_claim(claim_id, category, field, claimed, head, "Claimed head exists but is not the current head.", ["git:rev-parse HEAD", "git:cat-file -e"]))
                else:
                    conflicts.append(_conflict_claim(claim_id, category, field, claimed, head, "Claimed head is not current and could not be found as a commit.", ["git:rev-parse HEAD", "git:cat-file -e"]))
            else:
                unverified.append(_unverified_claim(claim_id, category, field, claimed))
        elif field == "remote_head":
            if verify_git:
                remote_head = _git_stdout(root, "rev-parse", "origin/main")
                if remote_head is None:
                    unverified.append(_unverified_claim(claim_id, category, field, claimed, "origin/main is unavailable."))
                elif claimed == remote_head:
                    verified.append(_verified_claim(claim_id, category, field, claimed, remote_head, "git_verified", ["git:rev-parse origin/main"]))
                else:
                    conflicts.append(_conflict_claim(claim_id, category, field, claimed, remote_head, "Claimed remote head differs from origin/main.", ["git:rev-parse origin/main"]))
            else:
                unverified.append(_unverified_claim(claim_id, category, field, claimed))
        elif field == "parity":
            claimed_parity = _normalize_parity(claimed)
            if verify_git and parity is not None and claimed_parity is not None:
                comparable_claimed = OrderedDict((key, claimed_parity[key]) for key in ("behind", "ahead"))
                comparable_verified = OrderedDict((key, parity[key]) for key in ("behind", "ahead"))
                if comparable_claimed == comparable_verified:
                    verified.append(_verified_claim(claim_id, category, field, claimed_parity, parity, "git_verified", ["git:rev-list --left-right --count origin/main...HEAD"]))
                else:
                    conflicts.append(_conflict_claim(claim_id, category, field, claimed_parity, parity, "Claimed origin/main parity differs from git parity.", ["git:rev-list --left-right --count origin/main...HEAD"]))
            else:
                unverified.append(_unverified_claim(claim_id, category, field, claimed))
        elif field == "commits":
            commits = _coerce_string_list(claimed)
            missing = [commit for commit in commits if verify_git and not commit_exists(root, commit)]
            if verify_git and not missing:
                verified.append(_verified_claim(claim_id, category, field, commits, commits, "git_verified", ["git:cat-file -e"]))
            elif verify_git:
                conflicts.append(_conflict_claim(claim_id, category, field, commits, {"missing_commits": missing}, "One or more claimed commits do not exist locally.", ["git:cat-file -e"]))
            else:
                unverified.append(_unverified_claim(claim_id, category, field, commits))
        elif field == "validation":
            claimed_validation = _normalize_validation(claimed)
            if claimed_validation is not None and claimed_validation == validation_summary and validation_ref:
                verified.append(_verified_claim(claim_id, category, field, claimed_validation, validation_summary, "validation_verified", [validation_ref]))
            elif claimed_validation is not None and validation_ref:
                conflicts.append(_conflict_claim(claim_id, category, field, claimed_validation, validation_summary, "Claimed validation summary differs from local validation receipt.", [validation_ref]))
            else:
                unverified.append(_unverified_claim(claim_id, category, field, claimed, "Validation receipt is unavailable."))
        elif field in {"receipts_created", "receipt_refs", "source_refs"}:
            refs = _coerce_string_list(claimed)
            missing = []
            existing = []
            for ref in refs:
                normalized, error = _normalize_ref(ref, root)
                if error is not None or normalized is None:
                    missing.append(ref)
                    continue
                if (root / normalized).exists():
                    existing.append(normalized)
                else:
                    missing.append(normalized)
            if verify_receipts and not missing:
                verified.append(_verified_claim(claim_id, category, field, refs, existing, "receipt_backed", existing))
            elif verify_receipts:
                missing_receipts.append(_finding("missing_receipt", "One or more claimed receipt refs are missing.", claim_id=claim_id, refs=missing))
                conflicts.append(_conflict_claim(claim_id, category, field, refs, {"missing_receipts": missing}, "Claimed receipt refs are missing.", existing))
            else:
                unverified.append(_unverified_claim(claim_id, category, field, refs))
        elif field == "current_marker_board":
            claimed_board = _normalize_marker_board(claimed)
            if verify_marker_board and claimed_board is not None and marker_board_ref:
                mismatches = OrderedDict()
                for marker, percent in claimed_board.items():
                    if marker_board.get(marker) != percent:
                        mismatches[marker] = OrderedDict([("claimed", percent), ("verified", marker_board.get(marker))])
                if not mismatches:
                    verified.append(_verified_claim(claim_id, category, field, claimed_board, marker_board, "manifest_verified", [marker_board_ref]))
                else:
                    conflicts.append(_conflict_claim(claim_id, category, field, claimed_board, mismatches, "Claimed marker board differs from ATLAS marker board.", [marker_board_ref]))
            else:
                unverified.append(_unverified_claim(claim_id, category, field, claimed))
        elif field == "marker_changes":
            changes = _normalize_marker_changes(claimed)
            for change in changes:
                marker_deltas.append(change)
            if verify_marker_board and marker_board_ref:
                mismatches = []
                for change in changes:
                    marker = str(change.get("marker"))
                    try:
                        target = int(change.get("to"))
                    except (TypeError, ValueError):
                        mismatches.append(change)
                        continue
                    if marker_board.get(marker) != target:
                        mismatches.append(change)
                if not mismatches:
                    verified.append(_verified_claim(claim_id, category, field, changes, changes, "manifest_verified", [marker_board_ref]))
                else:
                    conflicts.append(_conflict_claim(claim_id, category, field, changes, {"mismatched_marker_changes": mismatches}, "Claimed marker delta target does not match the current marker board.", [marker_board_ref]))
            else:
                unverified.append(_unverified_claim(claim_id, category, field, changes))
        elif field == "next_exact_packet":
            if manifest_next_packet is not None and manifest_ref:
                if claimed == manifest_next_packet:
                    verified.append(_verified_claim(claim_id, category, field, claimed, manifest_next_packet, "manifest_verified", [manifest_ref]))
                else:
                    conflicts.append(_conflict_claim(claim_id, category, field, claimed, manifest_next_packet, "Claimed next packet differs from the continuity manifest.", [manifest_ref]))
            else:
                unverified.append(_unverified_claim(claim_id, category, field, claimed, "Continuity manifest next packet is unavailable."))
    return verified, unverified, conflicts, stale, missing_receipts, marker_deltas


def build_closeout_read_model(
    *,
    root: Path | None = None,
    sources: list[str] | None = None,
    verify_git: bool = False,
    verify_receipts: bool = False,
    verify_marker_board: bool = False,
) -> OrderedDict[str, Any]:
    base = (root or atlas_root()).resolve()
    branch, head = collect_git_state(base)
    parity = collect_git_parity(base) if verify_git else None
    validation_summary, validation_ref = read_validation_summary(base)
    manifest_next_packet, manifest_ref = read_manifest_next_packet(base)
    marker_board, marker_board_ref = read_marker_board(base)

    source_refs, source_errors = resolve_sources(base, sources)
    closeouts, source_digests, read_blockers = load_closeouts(base, source_refs)

    warnings: list[OrderedDict[str, Any]] = []
    blockers: list[OrderedDict[str, Any]] = []
    blockers.extend(source_errors)
    blockers.extend(read_blockers)

    verified_claims: list[OrderedDict[str, Any]] = []
    unverified_claims: list[OrderedDict[str, Any]] = []
    conflicts: list[OrderedDict[str, Any]] = []
    stale_claims: list[OrderedDict[str, Any]] = []
    missing_receipts: list[OrderedDict[str, Any]] = []
    marker_deltas: list[OrderedDict[str, Any]] = []

    if not closeouts and not blockers:
        warnings.append(_finding("closeouts_empty", "No closeouts were normalized from the provided sources."))

    for index, closeout in enumerate(closeouts):
        verified, unverified, closeout_conflicts, stale, missing, deltas = _field_claims(
            root=base,
            closeout=closeout,
            closeout_index=index,
            verify_git=verify_git,
            verify_receipts=verify_receipts,
            verify_marker_board=verify_marker_board,
            branch=branch,
            head=head,
            parity=parity,
            validation_summary=validation_summary,
            validation_ref=validation_ref,
            marker_board=marker_board,
            marker_board_ref=marker_board_ref,
            manifest_next_packet=manifest_next_packet,
            manifest_ref=manifest_ref,
        )
        verified_claims.extend(verified)
        unverified_claims.extend(unverified)
        conflicts.extend(closeout_conflicts)
        stale_claims.extend(stale)
        missing_receipts.extend(missing)
        marker_deltas.extend(deltas)

    if unverified_claims and not blockers:
        warnings.append(_finding("unverified_claims_present", "One or more closeout claims remain advisory because local evidence is unavailable."))
    if stale_claims and not blockers:
        warnings.append(_finding("stale_claims_present", "One or more closeout claims refer to older but locally known evidence."))

    status = STATUS_OK
    if blockers:
        status = STATUS_BLOCKER
    elif conflicts:
        status = STATUS_CONFLICT
    elif warnings or stale_claims or unverified_claims:
        status = STATUS_ADVISORY

    normalized_state = OrderedDict(
        [
            ("branch", branch),
            ("head", head),
            ("parity", parity),
            ("validation", validation_summary),
            ("current_marker_board", marker_board),
            ("manifest_next_packet", manifest_next_packet),
            ("closeout_count", len(closeouts)),
            ("claim_count", len(verified_claims) + len(unverified_claims) + len(conflicts) + len(stale_claims)),
        ]
    )
    verification_summary = OrderedDict(
        [
            ("source_count", len(source_refs)),
            ("closeout_count", len(closeouts)),
            ("verified_claim_count", len(verified_claims)),
            ("unverified_claim_count", len(unverified_claims)),
            ("conflict_count", len(conflicts)),
            ("stale_claim_count", len(stale_claims)),
            ("missing_receipt_count", len(missing_receipts)),
            ("blocker_count", len(blockers)),
            ("warning_count", len(warnings)),
            ("validation_warning_count", validation_summary["warning"]),
        ]
    )

    return OrderedDict(
        [
            ("schema_version", SCHEMA_VERSION),
            ("status", status),
            ("root", normalize_slashes(str(base))),
            ("branch", branch),
            ("head", head),
            ("source_refs", source_refs),
            ("source_digests", source_digests),
            ("closeouts", closeouts),
            ("normalized_state", normalized_state),
            ("verification_summary", verification_summary),
            ("verified_claims", sorted(verified_claims, key=lambda item: item["claim_id"])),
            ("unverified_claims", sorted(unverified_claims, key=lambda item: item["claim_id"])),
            ("conflicts", sorted(conflicts, key=lambda item: item["claim_id"])),
            ("stale_claims", sorted(stale_claims, key=lambda item: item["claim_id"])),
            ("missing_receipts", missing_receipts),
            ("marker_deltas", marker_deltas),
            ("next_packet", manifest_next_packet),
            ("authority_denials", list(AUTHORITY_DENIALS)),
            ("warnings", warnings),
            ("blockers", blockers),
            ("safe_to_use", status == STATUS_OK),
            ("next_recommended_packet", RECONCILIATION_PACKET if status == STATUS_OK else None),
        ]
    )


def build_schema_only_payload(root: Path | None = None) -> OrderedDict[str, Any]:
    base = (root or atlas_root()).resolve()
    branch, head = collect_git_state(base)
    return OrderedDict(
        [
            ("schema_version", SCHEMA_VERSION),
            ("status", STATUS_OK),
            ("root", normalize_slashes(str(base))),
            ("branch", branch),
            ("head", head),
            ("source_refs", []),
            ("source_digests", OrderedDict()),
            ("closeouts", []),
            ("normalized_state", OrderedDict([("top_level_fields", list(TOP_LEVEL_FIELDS)), ("claim_fields", list(CLAIM_FIELDS))])),
            ("verification_summary", OrderedDict([("source_count", 0), ("closeout_count", 0), ("verified_claim_count", 0), ("unverified_claim_count", 0), ("conflict_count", 0), ("stale_claim_count", 0), ("missing_receipt_count", 0), ("blocker_count", 0), ("warning_count", 0), ("validation_warning_count", 0)])),
            ("verified_claims", []),
            ("unverified_claims", []),
            ("conflicts", []),
            ("stale_claims", []),
            ("missing_receipts", []),
            ("marker_deltas", []),
            ("next_packet", None),
            ("authority_denials", list(AUTHORITY_DENIALS)),
            ("warnings", []),
            ("blockers", []),
            ("safe_to_use", True),
            ("next_recommended_packet", None),
        ]
    )


def _emit_payload(payload: OrderedDict[str, Any]) -> None:
    print(json.dumps(payload, indent=2))


def exit_code(status: str, *, strict: bool) -> int:
    if status == STATUS_OK:
        return 0
    if status == STATUS_ADVISORY:
        return 1 if strict else 0
    if status == STATUS_CONFLICT:
        return 2
    if status == STATUS_BLOCKER:
        return 2
    return 3


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build a read-only Cortex read model from explicit Codex closeout artifacts.")
    parser.add_argument("--json", action="store_true", help="Emit deterministic JSON.")
    parser.add_argument("--source", action="append", default=[], help="Repeatable root-relative closeout source path.")
    parser.add_argument("--output", help="Optional root-relative tmp/atlas/**.json output path.")
    parser.add_argument("--strict", action="store_true", help="Return nonzero when output is not ok.")
    parser.add_argument("--verify-git", action="store_true")
    parser.add_argument("--verify-receipts", action="store_true")
    parser.add_argument("--verify-marker-board", action="store_true")
    parser.add_argument("--schema-only", action="store_true")
    args = parser.parse_args(argv)

    root = atlas_root().resolve()
    try:
        if args.schema_only:
            payload = build_schema_only_payload(root=root)
        else:
            payload = build_closeout_read_model(
                root=root,
                sources=list(args.source or []),
                verify_git=args.verify_git,
                verify_receipts=args.verify_receipts,
                verify_marker_board=args.verify_marker_board,
            )
        if args.output:
            resolved_output, output_error = validate_output_path(root, args.output)
            if output_error is not None or resolved_output is None:
                payload["status"] = STATUS_BLOCKER
                payload["safe_to_use"] = False
                payload["next_recommended_packet"] = None
                payload["blockers"] = list(payload.get("blockers", [])) + [output_error]
            else:
                resolved_output.parent.mkdir(parents=True, exist_ok=True)
                resolved_output.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
        _emit_payload(payload)
        return exit_code(str(payload.get("status") or STATUS_INTERNAL_ERROR), strict=args.strict)
    except Exception as exc:  # pragma: no cover - defensive contract guard
        payload = OrderedDict(
            [
                ("schema_version", SCHEMA_VERSION),
                ("status", STATUS_INTERNAL_ERROR),
                ("root", normalize_slashes(str(root))),
                ("branch", None),
                ("head", None),
                ("source_refs", list(args.source or [])),
                ("source_digests", OrderedDict()),
                ("closeouts", []),
                ("normalized_state", OrderedDict()),
                ("verification_summary", OrderedDict()),
                ("verified_claims", []),
                ("unverified_claims", []),
                ("conflicts", []),
                ("stale_claims", []),
                ("missing_receipts", []),
                ("marker_deltas", []),
                ("next_packet", None),
                ("authority_denials", list(AUTHORITY_DENIALS)),
                ("warnings", []),
                ("blockers", [_finding("internal_error", "Closeout ingestion failed before completion.", exception=str(exc))]),
                ("safe_to_use", False),
                ("next_recommended_packet", None),
            ]
        )
        _emit_payload(payload)
        return 3


if __name__ == "__main__":
    raise SystemExit(main())
