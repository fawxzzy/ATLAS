from __future__ import annotations

import argparse
import json
import re
import sys
from collections import OrderedDict
from pathlib import Path
from typing import Any, Iterable

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from ops._atlas import atlas_root, normalize_slashes

SCHEMA_VERSION = "atlas.vercel_log_runtime_error_inventory.v1"
WRAPPER_SCHEMA_VERSION = "atlas.vercel.observability.log_runtime_wrapper.v1"
RECORD_SCHEMA_VERSION = "atlas.vercel.observability.log_runtime_record.v1"

STATUS_OK = "ok"
STATUS_ADVISORY_GAP = "advisory_gap"
STATUS_BLOCKER = "blocker"
STATUS_INTERNAL_ERROR = "internal_error"

AUDIT_RECEIPT = "docs/ops/VERCEL-PLATFORM-OBSERVABILITY-CAPABILITY-AUDIT-2026-07-09.md"
PROJECT_COVERAGE_RECEIPT = (
    "docs/ops/VERCEL-PLATFORM-OBSERVABILITY-GOVERNANCE-PROJECT-INVENTORY-COVERAGE-RECONCILIATION-CONTRACT-FREEZE-2026-07-09.md"
)
CONTRACT_RECEIPT = "docs/ops/VERCEL-PLATFORM-OBSERVABILITY-GOVERNANCE-LOG-AND-RUNTIME-ERROR-INVENTORY-CONTRACT-FREEZE-2026-07-09.md"
ADMISSION_RECEIPT = "docs/ops/VERCEL-PLATFORM-OBSERVABILITY-GOVERNANCE-LOG-AND-RUNTIME-ERROR-INVENTORY-FIRST-IMPLEMENTATION-ADMISSION-2026-07-09.md"
PROMPT_PACK_RECEIPT = (
    "docs/ops/VERCEL-PLATFORM-OBSERVABILITY-GOVERNANCE-LOG-AND-RUNTIME-ERROR-INVENTORY-PROMPT-PACK-AND-WORKER-HANDOFF-CONTRACT-2026-07-09.md"
)
READINESS_RECEIPT = (
    "docs/ops/VERCEL-PLATFORM-OBSERVABILITY-GOVERNANCE-LOG-AND-RUNTIME-ERROR-INVENTORY-IMPLEMENTATION-READINESS-CLOSEOUT-AND-WORKER-ROUTING-2026-07-09.md"
)
CURRENT_STATE = "docs/atlas-book/01-current-state.md"
RECEIPT_INDEX = "docs/atlas-book/05-receipt-index.md"
RESTART_GUIDE = "docs/atlas-book/12-restart-and-handoff-guide.md"
STACK_REPO_INVENTORY = "docs/registry/STACK-REPO-INVENTORY.json"

REQUIRED_TEXT_REFS = (
    AUDIT_RECEIPT,
    PROJECT_COVERAGE_RECEIPT,
    CONTRACT_RECEIPT,
    ADMISSION_RECEIPT,
    PROMPT_PACK_RECEIPT,
    READINESS_RECEIPT,
    CURRENT_STATE,
    RECEIPT_INDEX,
    RESTART_GUIDE,
)

NEXT_RECOMMENDED_PACKET = "Vercel Platform Observability Governance log and runtime-error inventory first-implementation worker-cluster reconciliation"

GOVERNED_PROJECTS = OrderedDict(
    [
        (
            "fawxzzy-discordos",
            OrderedDict(
                [
                    ("project_id", "prj_C2RSEa34OblHfhuEpVChRQQZSjuG"),
                    ("repo_logical_id", "discordos"),
                ]
            ),
        ),
        (
            "fawxzzy-fitness",
            OrderedDict(
                [
                    ("project_id", "prj_rtlFVOMFAWCRoJ3SQjHloi89881K"),
                    ("repo_logical_id", "fitness"),
                ]
            ),
        ),
        (
            "fawxzzy-mazer",
            OrderedDict(
                [
                    ("project_id", "prj_t3zothbtj9DExrh3FjMsH98hwwSZ"),
                    ("repo_logical_id", "mazer"),
                ]
            ),
        ),
        (
            "fawxzzy-trove",
            OrderedDict(
                [
                    ("project_id", "prj_vhUyajI4AL6BgCF40VnKtdxrBLuV"),
                    ("repo_logical_id", "trove"),
                ]
            ),
        ),
        (
            "fawxzzy-foundation",
            OrderedDict(
                [
                    ("project_id", "prj_o37CPLlESB6Zybe8GB74BX3wrkpy"),
                    ("repo_logical_id", "foundation"),
                ]
            ),
        ),
    ]
)

PROJECT_BY_ID = {meta["project_id"]: slug for slug, meta in GOVERNED_PROJECTS.items()}
REQUIRED_INVENTORY_IDS = tuple(meta["repo_logical_id"] for meta in GOVERNED_PROJECTS.values())

ALLOWED_SOURCE_CLASSES = {"request_log", "runtime_log", "runtime_error_group", "build_log_summary"}
ALLOWED_STATUSES = {STATUS_OK, STATUS_ADVISORY_GAP, STATUS_BLOCKER, STATUS_INTERNAL_ERROR}
ALLOWED_REDACTION_STATUSES = {"redacted", "sanitized"}
ALLOWED_LEVELS = {"debug", "info", "warn", "warning", "error", "fatal"}
ALLOWED_INPUT_SUFFIXES = {".json", ".jsonl", ".ndjson"}
FORBIDDEN_KEYS = {
    "env",
    "env_value",
    "env_values",
    "token",
    "token_value",
    "token_values",
    "secret",
    "secret_value",
    "secret_values",
    "cookie",
    "cookies",
    "authorization",
    "authorization_header",
    "auth_header",
    "headers",
    "request_body",
    "raw_request_body",
    "body",
    "customer_data",
    "payment_data",
    "payment_payload",
    "mutation_payload",
    "stack_trace",
    "raw_stack_trace",
}

SENSITIVE_VALUE_PATTERNS: tuple[tuple[str, re.Pattern[str], str], ...] = (
    (
        "env_value_pattern",
        re.compile(r"\b[A-Z][A-Z0-9_]{2,}\s*=\s*\S+"),
        "Wrapper includes an env-style assignment string.",
    ),
    (
        "token_value_pattern",
        re.compile(r"(?i)\b(?:bearer\s+[A-Za-z0-9._-]{8,}|(?:token|api[_-]?key|secret(?:_key)?)\s*[:=]\s*[A-Za-z0-9._-]{8,})"),
        "Wrapper includes a token- or secret-style string.",
    ),
    (
        "cookie_or_auth_value_pattern",
        re.compile(r"(?i)\b(?:cookie|set-cookie|authorization)\s*[:=]"),
        "Wrapper includes cookie or authorization header material.",
    ),
    (
        "payment_or_customer_pattern",
        re.compile(r"(?i)\b(?:card_number|payment_intent|customer_email|customer_id)\b"),
        "Wrapper includes payment or customer field material.",
    ),
    (
        "unredacted_stack_pattern",
        re.compile(r"(?s)\bError:.*\n\s+at\s+\S+"),
        "Wrapper includes a raw stack-trace style string.",
    ),
)


def _finding(code: str, message: str, *, severity: str = "blocker", **details: Any) -> OrderedDict[str, Any]:
    payload: OrderedDict[str, Any] = OrderedDict([("code", code), ("severity", severity), ("message", message)])
    if details:
        payload["details"] = details
    return payload


def _read_text(path: Path) -> str | None:
    if not path.exists() or not path.is_file():
        return None
    try:
        return path.read_text(encoding="utf-8-sig")
    except UnicodeDecodeError:
        return path.read_text(encoding="utf-8-sig", errors="ignore")


def _load_json(path: Path) -> dict[str, Any] | None:
    text = _read_text(path)
    if text is None:
        return None
    try:
        payload = json.loads(text)
    except json.JSONDecodeError:
        return None
    return payload if isinstance(payload, dict) else None


def _normal(value: str | Path) -> str:
    return normalize_slashes(str(value)).strip("/")


def _protected_path(relative_path: str) -> bool:
    normalized = _normal(relative_path)
    if not normalized:
        return True
    if normalized.startswith(("repos/", "secrets/", "runtime/", ".vercel/", ".playwright-mcp/", "archive/")):
        return True
    return any(part.startswith(".env") for part in normalized.split("/"))


def _validate_runtime_path(
    *, root: Path, relative_path: str, allowed_suffixes: Iterable[str], tmp_message: str
) -> tuple[Path | None, OrderedDict[str, Any] | None]:
    candidate = Path(relative_path)
    if candidate.is_absolute():
        return None, _finding("absolute_path", "Path must be root-relative.", path=normalize_slashes(str(candidate)))
    normalized = _normal(candidate)
    if ".." in Path(normalized).parts:
        return None, _finding("parent_traversal_path", "Path must not use parent traversal.", path=normalized)
    if _protected_path(normalized) or not normalized.startswith("tmp/") or Path(normalized).suffix.lower() not in set(allowed_suffixes):
        return None, _finding("protected_path", tmp_message, path=normalized)
    resolved = (root / normalized).resolve()
    try:
        resolved.relative_to(root.resolve())
    except ValueError:
        return None, _finding("outside_root_path", "Path must stay inside the ATLAS root.", path=normalized)
    return resolved, None


def validate_input_path(*, root: Path, relative_path: str) -> tuple[Path | None, OrderedDict[str, Any] | None]:
    return _validate_runtime_path(
        root=root,
        relative_path=relative_path,
        allowed_suffixes=ALLOWED_INPUT_SUFFIXES,
        tmp_message="Input paths are admitted only under root-relative tmp/**.{json,jsonl,ndjson}.",
    )


def validate_output_path(*, root: Path, relative_path: str) -> tuple[Path | None, OrderedDict[str, Any] | None]:
    return _validate_runtime_path(
        root=root,
        relative_path=relative_path,
        allowed_suffixes={".json"},
        tmp_message="Output paths are admitted only under root-relative tmp/**.json.",
    )


def _inventory_ids(payload: dict[str, Any]) -> set[str]:
    repos = payload.get("repos")
    if not isinstance(repos, list):
        return set()
    ids: set[str] = set()
    for item in repos:
        if isinstance(item, dict) and isinstance(item.get("logical_id"), str):
            ids.add(str(item["logical_id"]))
    return ids


def _ensure_required_files(root: Path) -> tuple[dict[str, str], list[OrderedDict[str, Any]]]:
    texts: dict[str, str] = {}
    blockers: list[OrderedDict[str, Any]] = []
    for ref in REQUIRED_TEXT_REFS:
        text = _read_text(root / ref)
        if text is None:
            blockers.append(_finding("required_receipt_missing", "Required root-owned Vercel governance input is missing.", path=ref))
            continue
        texts[ref] = text
    inventory = _load_json(root / STACK_REPO_INVENTORY)
    if inventory is None:
        blockers.append(_finding("stack_repo_inventory_missing", "Required stack repo inventory JSON is missing or malformed.", path=STACK_REPO_INVENTORY))
    else:
        inventory_ids = _inventory_ids(inventory)
        missing_ids = [repo_id for repo_id in REQUIRED_INVENTORY_IDS if repo_id not in inventory_ids]
        if missing_ids:
            blockers.append(
                _finding(
                    "stack_repo_inventory_incomplete",
                    "Stack repo inventory is missing one or more required logical ids.",
                    missing_ids=missing_ids,
                )
            )
    return texts, blockers


def _validate_contract_texts(texts: dict[str, str], blockers: list[OrderedDict[str, Any]]) -> None:
    audit_text = texts.get(AUDIT_RECEIPT, "")
    for slug, meta in GOVERNED_PROJECTS.items():
        if slug not in audit_text or meta["project_id"] not in audit_text:
            blockers.append(
                _finding(
                    "audit_project_missing",
                    "Vercel observability audit is missing the expected governed project reference.",
                    project_slug=slug,
                    project_id=meta["project_id"],
                )
            )
    for needle in ("billing-webhook-stripe", "/api/billing/webhook/stripe", "dpl_HUsDUbhofhJFEKxLCazcDfQk8pTM"):
        if needle not in audit_text:
            blockers.append(
                _finding(
                    "audit_runtime_error_reference_missing",
                    "Vercel observability audit is missing the expected runtime-error evidence reference.",
                    required_reference=needle,
                )
            )

    project_coverage_text = texts.get(PROJECT_COVERAGE_RECEIPT, "")
    for needle in ("5/5", "fawxzzy-foundation", "fawxzzy-trove"):
        if needle not in project_coverage_text:
            blockers.append(
                _finding(
                    "project_coverage_reference_missing",
                    "Project inventory coverage receipt is missing the expected governed coverage reference.",
                    required_reference=needle,
                )
            )

    contract_text = texts.get(CONTRACT_RECEIPT, "")
    for needle in ("request logs", "runtime logs", "grouped runtime errors", "tmp/atlas/vercel-observability/"):
        if needle not in contract_text:
            blockers.append(
                _finding(
                    "contract_reference_missing",
                    "Log/runtime-error contract is missing a required boundary reference.",
                    required_reference=needle,
                )
            )

    admission_text = texts.get(ADMISSION_RECEIPT, "")
    for needle in ("ops/atlas/vercel_log_runtime_error_inventory.py", "tests/test_atlas_vercel_log_runtime_error_inventory.py", "--strict"):
        if needle not in admission_text:
            blockers.append(
                _finding(
                    "admission_reference_missing",
                    "First-implementation admission is missing a required worker reference.",
                    required_reference=needle,
                )
            )

    prompt_text = texts.get(PROMPT_PACK_RECEIPT, "")
    for needle in (SCHEMA_VERSION, "runtime_error_group", "build_log_summary", "tmp/**.json"):
        if needle not in prompt_text:
            blockers.append(
                _finding(
                    "prompt_pack_reference_missing",
                    "Prompt-pack contract is missing a required helper contract reference.",
                    required_reference=needle,
                )
            )

    readiness_text = texts.get(READINESS_RECEIPT, "")
    for needle in ("implementation_ready", "ops/atlas/vercel_log_runtime_error_inventory.py", "worker-cluster reconciliation"):
        if needle not in readiness_text:
            blockers.append(
                _finding(
                    "readiness_reference_missing",
                    "Implementation-readiness closeout is missing a required routing reference.",
                    required_reference=needle,
                )
            )


def _ensure_string(payload: dict[str, Any], key: str) -> str | None:
    value = payload.get(key)
    return value if isinstance(value, str) else None


def _ensure_positive_int(payload: dict[str, Any], key: str) -> int | None:
    value = payload.get(key)
    return value if isinstance(value, int) and value > 0 else None


def _scan_forbidden(value: Any, *, path: str = "") -> list[OrderedDict[str, Any]]:
    blockers: list[OrderedDict[str, Any]] = []
    if isinstance(value, dict):
        for key, nested in value.items():
            next_path = f"{path}.{key}".strip(".")
            if isinstance(key, str) and key in FORBIDDEN_KEYS:
                blockers.append(_finding("forbidden_sensitive_key", "Wrapper includes a forbidden sensitive field.", path=next_path))
            blockers.extend(_scan_forbidden(nested, path=next_path))
        return blockers
    if isinstance(value, list):
        for index, nested in enumerate(value):
            blockers.extend(_scan_forbidden(nested, path=f"{path}[{index}]"))
        return blockers
    if isinstance(value, str):
        for detector, pattern, message in SENSITIVE_VALUE_PATTERNS:
            if pattern.search(value):
                blockers.append(_finding("forbidden_sensitive_value", message, path=path or "(value)", detector=detector))
                break
    return blockers


def _normalize_route_pattern(route: str) -> str:
    normalized = route.strip()
    if not normalized:
        return normalized
    if "://" in normalized:
        normalized = "/" + normalized.split("://", 1)[1].split("/", 1)[1] if "/" in normalized.split("://", 1)[1] else "/"
    normalized = normalized.split("?", 1)[0].split("#", 1)[0]
    segments: list[str] = []
    for segment in normalized.split("/"):
        if not segment:
            continue
        lowered = segment.lower()
        if re.fullmatch(r"\d+", segment) or re.fullmatch(r"[0-9a-f]{8,}", lowered) or re.fullmatch(r"[0-9a-f-]{12,}", lowered):
            segments.append("[id]")
        else:
            segments.append(segment)
    return "/" + "/".join(segments) if segments else "/"


def _status_code_family(value: str) -> str | None:
    if re.fullmatch(r"[1-5]xx", value):
        return value
    if re.fullmatch(r"[1-5]\d\d", value):
        return f"{value[0]}xx"
    if value == "unknown":
        return value
    return None


def _metadata_from_object(payload: dict[str, Any], *, object_path: str) -> tuple[OrderedDict[str, Any] | None, list[OrderedDict[str, Any]]]:
    blockers = _scan_forbidden(payload, path=object_path)
    source_class = _ensure_string(payload, "source_class")
    project_slug = _ensure_string(payload, "project_slug")
    project_id = _ensure_string(payload, "project_id")
    environment = _ensure_string(payload, "environment")
    deployment_id = _ensure_string(payload, "deployment_id")

    if source_class is None:
        blockers.append(_finding("source_class_missing", "Wrapper record must include string source_class.", path=object_path))
    elif source_class not in ALLOWED_SOURCE_CLASSES:
        blockers.append(
            _finding(
                "unsupported_source_class",
                "Wrapper record uses an unsupported source class.",
                path=object_path,
                source_class=source_class,
            )
        )
    if project_slug is None:
        blockers.append(_finding("project_slug_missing", "Wrapper record must include string project_slug.", path=object_path))
    if project_id is None:
        blockers.append(_finding("project_id_missing", "Wrapper record must include string project_id.", path=object_path))
    if environment is None:
        blockers.append(_finding("environment_missing", "Wrapper record must include string environment.", path=object_path))
    if deployment_id is None:
        blockers.append(_finding("deployment_id_missing", "Wrapper record must include string deployment_id.", path=object_path))

    if blockers or source_class is None or project_slug is None or project_id is None or environment is None or deployment_id is None:
        return None, blockers

    expected = GOVERNED_PROJECTS.get(project_slug)
    if expected is None:
        blockers.append(_finding("unknown_project_slug", "Wrapper project_slug is not part of the governed Vercel set.", project_slug=project_slug))
        return None, blockers
    if expected["project_id"] != project_id:
        blockers.append(
            _finding(
                "project_mapping_mismatch",
                "Wrapper project mapping does not match the governed Vercel project set.",
                project_slug=project_slug,
                expected_project_id=expected["project_id"],
                actual_project_id=project_id,
            )
        )
        return None, blockers
    if PROJECT_BY_ID.get(project_id) != project_slug:
        blockers.append(
            _finding(
                "unknown_project_id",
                "Wrapper project_id is not part of the governed Vercel project set.",
                project_id=project_id,
            )
        )
        return None, blockers

    return (
        OrderedDict(
            [
                ("source_class", source_class),
                ("project_slug", project_slug),
                ("project_id", project_id),
                ("environment", environment),
                ("deployment_id", deployment_id),
            ]
        ),
        blockers,
    )


def _record_from_payload(
    payload: dict[str, Any], *, inherited: dict[str, Any] | None, object_path: str
) -> tuple[OrderedDict[str, Any] | None, list[OrderedDict[str, Any]]]:
    combined = dict(inherited or {})
    combined.update(payload)
    metadata, blockers = _metadata_from_object(combined, object_path=object_path)
    if metadata is None:
        return None, blockers

    route_pattern_raw = _ensure_string(combined, "route_pattern")
    level = _ensure_string(combined, "level")
    status_code_value = _ensure_string(combined, "status_code_family")
    first_seen = _ensure_string(combined, "first_seen")
    last_seen = _ensure_string(combined, "last_seen")
    redaction_status = _ensure_string(combined, "redaction_status")
    occurrence_count = _ensure_positive_int(combined, "occurrence_count")
    sample_count = _ensure_positive_int(combined, "sample_count")
    cluster_label = _ensure_string(combined, "cluster_label")

    if route_pattern_raw is None:
        blockers.append(_finding("route_pattern_missing", "Wrapper record must include string route_pattern.", path=object_path))
    if level is None:
        blockers.append(_finding("level_missing", "Wrapper record must include string level.", path=object_path))
    elif level not in ALLOWED_LEVELS:
        blockers.append(_finding("invalid_level", "Wrapper record level is outside the admitted bounded vocabulary.", path=object_path, level=level))
    if status_code_value is None:
        blockers.append(_finding("status_code_family_missing", "Wrapper record must include string status_code_family.", path=object_path))
    if first_seen is None:
        blockers.append(_finding("first_seen_missing", "Wrapper record must include string first_seen.", path=object_path))
    if last_seen is None:
        blockers.append(_finding("last_seen_missing", "Wrapper record must include string last_seen.", path=object_path))
    if redaction_status is None:
        blockers.append(_finding("redaction_status_missing", "Wrapper record must include string redaction_status.", path=object_path))
    elif redaction_status not in ALLOWED_REDACTION_STATUSES:
        blockers.append(
            _finding(
                "invalid_redaction_status",
                "Wrapper record redaction_status is outside the admitted bounded vocabulary.",
                path=object_path,
                redaction_status=redaction_status,
            )
        )
    if occurrence_count is None:
        blockers.append(_finding("occurrence_count_missing", "Wrapper record must include positive integer occurrence_count.", path=object_path))
    if sample_count is None:
        blockers.append(_finding("sample_count_missing", "Wrapper record must include positive integer sample_count.", path=object_path))

    route_pattern = _normalize_route_pattern(route_pattern_raw or "")
    if not route_pattern:
        blockers.append(_finding("route_pattern_invalid", "Wrapper route_pattern cannot be empty after normalization.", path=object_path))
    status_code_family = _status_code_family(status_code_value or "")
    if status_code_family is None:
        blockers.append(
            _finding(
                "invalid_status_code_family",
                "Wrapper status_code_family must already be a family or a concrete HTTP status.",
                path=object_path,
                status_code_family=status_code_value,
            )
        )

    source_class = str(metadata["source_class"])
    if source_class == "runtime_error_group" and cluster_label is None:
        blockers.append(_finding("cluster_label_missing", "runtime_error_group records must include string cluster_label.", path=object_path))
    elif cluster_label is None:
        cluster_label = source_class

    if blockers:
        return None, blockers

    record = OrderedDict(
        [
            ("source_class", source_class),
            ("project_slug", str(metadata["project_slug"])),
            ("project_id", str(metadata["project_id"])),
            ("environment", str(metadata["environment"])),
            ("deployment_id", str(metadata["deployment_id"])),
            ("cluster_label", str(cluster_label)),
            ("route_pattern", route_pattern),
            ("status_code_family", str(status_code_family)),
            ("level", str(level)),
            ("first_seen", str(first_seen)),
            ("last_seen", str(last_seen)),
            ("occurrence_count", int(occurrence_count)),
            ("sample_count", int(sample_count)),
            ("redaction_status", str(redaction_status)),
        ]
    )
    return record, blockers


def _records_from_wrapper(payload: dict[str, Any], *, object_path: str) -> tuple[list[OrderedDict[str, Any]], list[OrderedDict[str, Any]]]:
    blockers = _scan_forbidden({key: value for key, value in payload.items() if key != "records"}, path=object_path)
    schema_version = _ensure_string(payload, "schema_version")
    if schema_version != WRAPPER_SCHEMA_VERSION:
        blockers.append(
            _finding(
                "unexpected_wrapper_schema",
                "Wrapper object does not use the admitted log/runtime wrapper schema.",
                path=object_path,
                expected=WRAPPER_SCHEMA_VERSION,
                actual=schema_version,
            )
        )
        return [], blockers
    records = payload.get("records")
    if not isinstance(records, list) or not records:
        blockers.append(_finding("records_missing", "Wrapper object must include a non-empty records array.", path=object_path))
        return [], blockers

    inherited = {
        key: payload.get(key)
        for key in ("source_class", "project_slug", "project_id", "environment", "deployment_id")
        if key in payload
    }
    normalized: list[OrderedDict[str, Any]] = []
    for index, item in enumerate(records):
        item_path = f"{object_path}.records[{index}]"
        if not isinstance(item, dict):
            blockers.append(_finding("record_malformed", "Each wrapper record entry must be an object.", path=item_path))
            continue
        record, record_blockers = _record_from_payload(item, inherited=inherited, object_path=item_path)
        blockers.extend(record_blockers)
        if record is not None:
            normalized.append(record)
    return normalized, blockers


def _records_from_record_object(payload: dict[str, Any], *, object_path: str) -> tuple[list[OrderedDict[str, Any]], list[OrderedDict[str, Any]]]:
    schema_version = _ensure_string(payload, "schema_version")
    blockers: list[OrderedDict[str, Any]] = []
    if schema_version != RECORD_SCHEMA_VERSION:
        blockers.append(
            _finding(
                "unexpected_record_schema",
                "Record object does not use the admitted log/runtime record schema.",
                path=object_path,
                expected=RECORD_SCHEMA_VERSION,
                actual=schema_version,
            )
        )
        return [], blockers
    record, record_blockers = _record_from_payload(payload, inherited=None, object_path=object_path)
    blockers.extend(record_blockers)
    return ([record] if record is not None else []), blockers


def _load_input_records(*, root: Path, relative_path: str) -> tuple[list[OrderedDict[str, Any]], list[OrderedDict[str, Any]]]:
    resolved, path_error = validate_input_path(root=root, relative_path=relative_path)
    if path_error is not None:
        return [], [path_error]
    if resolved is None:
        return [], []
    text = _read_text(resolved)
    if text is None:
        return [], [_finding("input_missing", "Input wrapper path does not exist.", path=relative_path)]

    suffix = resolved.suffix.lower()
    blockers: list[OrderedDict[str, Any]] = []
    normalized_records: list[OrderedDict[str, Any]] = []

    if suffix == ".json":
        try:
            payload = json.loads(text)
        except json.JSONDecodeError:
            return [], [_finding("input_json_missing_or_malformed", "Input JSON wrapper is missing or malformed.", path=relative_path)]
        if not isinstance(payload, dict):
            return [], [_finding("input_json_not_object", "Input JSON wrapper must be an object.", path=relative_path)]
        if isinstance(payload.get("records"), list):
            records, record_blockers = _records_from_wrapper(payload, object_path=relative_path)
        else:
            records, record_blockers = _records_from_record_object(payload, object_path=relative_path)
        normalized_records.extend(records)
        blockers.extend(record_blockers)
        return normalized_records, blockers

    for index, line in enumerate(text.splitlines(), start=1):
        stripped = line.strip()
        if not stripped:
            continue
        try:
            payload = json.loads(stripped)
        except json.JSONDecodeError:
            blockers.append(_finding("input_jsonl_line_malformed", "JSON Lines input contains a malformed line.", path=relative_path, line=index))
            continue
        if not isinstance(payload, dict):
            blockers.append(_finding("input_jsonl_line_not_object", "Each JSON Lines record must be an object.", path=relative_path, line=index))
            continue
        object_path = f"{relative_path}:{index}"
        if isinstance(payload.get("records"), list):
            records, record_blockers = _records_from_wrapper(payload, object_path=object_path)
        else:
            records, record_blockers = _records_from_record_object(payload, object_path=object_path)
        normalized_records.extend(records)
        blockers.extend(record_blockers)
    if not normalized_records and not blockers:
        blockers.append(_finding("input_jsonl_empty", "JSON Lines input produced no admitted records.", path=relative_path))
    return normalized_records, blockers


def _project_sort_key(item: OrderedDict[str, Any]) -> str:
    return str(item.get("project_slug") or "")


def _cluster_sort_key(item: OrderedDict[str, Any]) -> tuple[str, str, str, str, str, str]:
    return (
        str(item.get("project_slug") or ""),
        str(item.get("deployment_id") or ""),
        str(item.get("source_class") or ""),
        str(item.get("cluster_label") or ""),
        str(item.get("route_pattern") or ""),
        str(item.get("status_code_family") or ""),
    )


def build_report(*, root: Path, inputs: list[str]) -> OrderedDict[str, Any]:
    texts, blockers = _ensure_required_files(root)
    _validate_contract_texts(texts, blockers)

    warnings: list[OrderedDict[str, Any]] = []
    if not inputs:
        blockers.append(_finding("input_required", "At least one --input tmp/** wrapper path is required."))

    records: list[OrderedDict[str, Any]] = []
    for input_path in inputs:
        loaded_records, load_blockers = _load_input_records(root=root, relative_path=input_path)
        records.extend(loaded_records)
        blockers.extend(load_blockers)

    project_accumulators: dict[str, dict[str, Any]] = {}
    cluster_accumulators: dict[tuple[str, str, str, str, str, str, str], dict[str, Any]] = {}

    for record in records:
        project_slug = str(record["project_slug"])
        project_entry = project_accumulators.setdefault(
            project_slug,
            {
                "project_slug": project_slug,
                "project_id": str(record["project_id"]),
                "environments": set(),
                "source_classes": set(),
                "deployment_ids": set(),
                "route_patterns": set(),
                "runtime_error_cluster_keys": set(),
                "status_code_families": set(),
                "levels": set(),
                "first_seen": None,
                "last_seen": None,
                "occurrence_count": 0,
                "sample_count": 0,
                "redaction_statuses": set(),
            },
        )
        project_entry["environments"].add(str(record["environment"]))
        project_entry["source_classes"].add(str(record["source_class"]))
        project_entry["deployment_ids"].add(str(record["deployment_id"]))
        project_entry["route_patterns"].add(str(record["route_pattern"]))
        project_entry["status_code_families"].add(str(record["status_code_family"]))
        project_entry["levels"].add(str(record["level"]))
        project_entry["occurrence_count"] += int(record["occurrence_count"])
        project_entry["sample_count"] += int(record["sample_count"])
        project_entry["redaction_statuses"].add(str(record["redaction_status"]))
        project_entry["first_seen"] = min(filter(None, [project_entry["first_seen"], str(record["first_seen"])]))
        project_entry["last_seen"] = max(filter(None, [project_entry["last_seen"], str(record["last_seen"])]))
        if str(record["source_class"]) == "runtime_error_group":
            project_entry["runtime_error_cluster_keys"].add((str(record["cluster_label"]), str(record["route_pattern"])))

        cluster_key = (
            str(record["project_slug"]),
            str(record["deployment_id"]),
            str(record["environment"]),
            str(record["source_class"]),
            str(record["cluster_label"]),
            str(record["route_pattern"]),
            str(record["status_code_family"]),
        )
        cluster_entry = cluster_accumulators.setdefault(
            cluster_key,
            {
                "project_slug": str(record["project_slug"]),
                "deployment_id": str(record["deployment_id"]),
                "environment": str(record["environment"]),
                "source_class": str(record["source_class"]),
                "cluster_label": str(record["cluster_label"]),
                "route_pattern": str(record["route_pattern"]),
                "status_code_family": str(record["status_code_family"]),
                "level": str(record["level"]),
                "first_seen": str(record["first_seen"]),
                "last_seen": str(record["last_seen"]),
                "occurrence_count": 0,
                "sample_count": 0,
                "redaction_statuses": set(),
            },
        )
        cluster_entry["occurrence_count"] += int(record["occurrence_count"])
        cluster_entry["sample_count"] += int(record["sample_count"])
        cluster_entry["redaction_statuses"].add(str(record["redaction_status"]))
        cluster_entry["first_seen"] = min(str(cluster_entry["first_seen"]), str(record["first_seen"]))
        cluster_entry["last_seen"] = max(str(cluster_entry["last_seen"]), str(record["last_seen"]))
        if str(record["level"]) == "error" or cluster_entry["level"] != "error":
            cluster_entry["level"] = str(record["level"])

    missing_project_ids = [slug for slug in GOVERNED_PROJECTS if slug not in project_accumulators]
    if missing_project_ids:
        warnings.append(
            OrderedDict(
                [
                    ("code", "partial_capture_coverage"),
                    ("severity", "warning"),
                    ("message", "One or more governed Vercel projects still lack admitted log/runtime captures."),
                    ("details", {"missing_project_slugs": missing_project_ids}),
                ]
            )
        )

    project_summaries: list[OrderedDict[str, Any]] = []
    for slug in GOVERNED_PROJECTS:
        if slug not in project_accumulators:
            continue
        item = project_accumulators[slug]
        environments = sorted(item["environments"])
        redaction_status = "redacted" if item["redaction_statuses"] == {"redacted"} else "sanitized"
        project_summaries.append(
            OrderedDict(
                [
                    ("project_slug", slug),
                    ("project_id", str(item["project_id"])),
                    ("environment", environments[0] if len(environments) == 1 else "mixed"),
                    ("source_classes", sorted(item["source_classes"])),
                    ("deployment_ids", sorted(item["deployment_ids"])),
                    ("route_pattern_count", len(item["route_patterns"])),
                    ("runtime_error_cluster_count", len(item["runtime_error_cluster_keys"])),
                    ("log_record_count", int(item["occurrence_count"])),
                    ("status_code_families", sorted(item["status_code_families"])),
                    ("levels", sorted(item["levels"])),
                    ("first_seen", item["first_seen"]),
                    ("last_seen", item["last_seen"]),
                    ("sample_count", int(item["sample_count"])),
                    ("redaction_status", redaction_status),
                ]
            )
        )

    cluster_summaries: list[OrderedDict[str, Any]] = []
    for cluster in sorted(cluster_accumulators.values(), key=lambda item: _cluster_sort_key(OrderedDict(item))):
        redaction_status = "redacted" if cluster["redaction_statuses"] == {"redacted"} else "sanitized"
        cluster_summaries.append(
            OrderedDict(
                [
                    ("project_slug", str(cluster["project_slug"])),
                    ("deployment_id", str(cluster["deployment_id"])),
                    ("environment", str(cluster["environment"])),
                    ("source_class", str(cluster["source_class"])),
                    ("cluster_label", str(cluster["cluster_label"])),
                    ("route_pattern", str(cluster["route_pattern"])),
                    ("status_code_family", str(cluster["status_code_family"])),
                    ("level", str(cluster["level"])),
                    ("first_seen", str(cluster["first_seen"])),
                    ("last_seen", str(cluster["last_seen"])),
                    ("occurrence_count", int(cluster["occurrence_count"])),
                    ("sample_count", int(cluster["sample_count"])),
                    ("redaction_status", redaction_status),
                ]
            )
        )

    forbidden_fields_detected = [item for item in blockers if str(item.get("code", "")).startswith("forbidden_")]
    if blockers:
        status = STATUS_BLOCKER
    elif warnings:
        status = STATUS_ADVISORY_GAP
    else:
        status = STATUS_OK
    if status not in ALLOWED_STATUSES:
        status = STATUS_INTERNAL_ERROR

    top_level_redaction_status = "blocked" if forbidden_fields_detected else ("redacted" if all(item.get("redaction_status") == "redacted" for item in project_summaries) and project_summaries else "sanitized")

    return OrderedDict(
        [
            ("schema_version", SCHEMA_VERSION),
            ("status", status),
            ("safe_to_use", not blockers),
            ("captured_project_count", len(project_summaries)),
            ("project_count", len(GOVERNED_PROJECTS)),
            ("runtime_error_cluster_count", sum(1 for item in cluster_summaries if item["source_class"] == "runtime_error_group")),
            ("log_record_count", sum(int(item["occurrence_count"]) for item in cluster_summaries)),
            ("redaction_status", top_level_redaction_status),
            ("projects", sorted(project_summaries, key=_project_sort_key)),
            ("clusters", cluster_summaries),
            ("warnings", warnings),
            ("blockers", blockers),
            ("forbidden_fields_detected", forbidden_fields_detected),
            ("next_recommended_packet", NEXT_RECOMMENDED_PACKET),
        ]
    )


def report_exit_code(*, status: str, strict: bool) -> int:
    if status == STATUS_OK:
        return 0
    if status == STATUS_ADVISORY_GAP:
        return 1 if strict else 0
    if status == STATUS_BLOCKER:
        return 2
    return 3


def render_summary(report: dict[str, Any]) -> str:
    return "\n".join(
        [
            f"Status: {report.get('status')}",
            f"Captured projects: {report.get('captured_project_count')}/{report.get('project_count')}",
            f"Runtime-error clusters: {report.get('runtime_error_cluster_count')}",
            f"Log record count: {report.get('log_record_count')}",
            f"Safe to use: {str(report.get('safe_to_use')).lower()}",
        ]
    )


def render_stdout(report: dict[str, Any], *, json_only: bool) -> str:
    json_text = json.dumps(report, indent=2) + "\n"
    if json_only:
        return json_text
    return render_summary(report) + "\n\n" + json_text


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Read-only Vercel log/runtime-error inventory helper for ATLAS root governance.")
    parser.add_argument("--input", action="append", default=[], help="Root-relative tmp/**.{json,jsonl,ndjson} Vercel log/runtime wrapper input.")
    parser.add_argument("--json", action="store_true", help="Emit JSON only on stdout.")
    parser.add_argument("--output", help="Optional root-relative tmp/**.json output path.")
    parser.add_argument("--strict", action="store_true", help="Return nonzero for advisory-gap and blocker statuses.")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    root = atlas_root().resolve()
    try:
        report = build_report(root=root, inputs=list(args.input))
        if args.output:
            resolved_output, output_error = validate_output_path(root=root, relative_path=args.output)
            if output_error is not None:
                report["status"] = STATUS_BLOCKER
                report["safe_to_use"] = False
                report["blockers"] = list(report.get("blockers", [])) + [output_error]
                report["forbidden_fields_detected"] = [item for item in report["blockers"] if str(item.get("code", "")).startswith("forbidden_")]
            elif resolved_output is not None:
                resolved_output.parent.mkdir(parents=True, exist_ok=True)
                resolved_output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
        sys.stdout.write(render_stdout(report, json_only=args.json))
        return report_exit_code(status=str(report.get("status") or STATUS_INTERNAL_ERROR), strict=bool(args.strict))
    except Exception as exc:
        report = OrderedDict(
            [
                ("schema_version", SCHEMA_VERSION),
                ("status", STATUS_INTERNAL_ERROR),
                ("safe_to_use", False),
                ("captured_project_count", 0),
                ("project_count", len(GOVERNED_PROJECTS)),
                ("runtime_error_cluster_count", 0),
                ("log_record_count", 0),
                ("redaction_status", "blocked"),
                ("projects", []),
                ("clusters", []),
                ("warnings", []),
                ("blockers", [_finding("internal_error", "Vercel log/runtime helper failed before summary output.", exception=str(exc))]),
                ("forbidden_fields_detected", []),
                ("next_recommended_packet", NEXT_RECOMMENDED_PACKET),
            ]
        )
        sys.stdout.write(render_stdout(report, json_only=getattr(args, "json", False)))
        return 3


if __name__ == "__main__":
    raise SystemExit(main())
