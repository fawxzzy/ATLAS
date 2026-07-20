from __future__ import annotations

import argparse
import copy
import dataclasses
import datetime as dt
import hashlib
import json
import os
import queue
import re
import shutil
import subprocess
import sys
import threading
import time
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Iterable


ROOT = Path(__file__).resolve().parents[2]
MANIFEST_REF = "docs/registry/ATLAS-WORKFLOW-MANIFEST.v1.json"
REGISTRY_REF = "docs/registry/ATLAS-WORKFLOW-LIVE-MAPPING.v1.json"
DECISION_REGISTRY_REF = "docs/registry/ATLAS-WORKFLOW-DECISIONS.v1.json"
BOOTSTRAP_CONTINUITY_REF = "docs/registry/ATLAS-WORKFLOW-BOOTSTRAP-CONTINUITY-HANDOFF.v1.json"
MANIFEST_SCHEMA_REF = "schemas/atlas.workflow.manifest.v1.json"
REGISTRY_SCHEMA_REF = "schemas/atlas.workflow.runtime-registry.v1.json"
DECISION_REGISTRY_SCHEMA_REF = "schemas/atlas.workflow.decision-registry.v1.json"
ENVELOPE_SCHEMA_REF = "schemas/atlas.workflow.envelope.v1.json"
DESKTOP_OBSERVATION_SCHEMA_REF = "schemas/atlas.workflow.desktop-observation.v1.json"
PLAN_SCHEMA_REF = "schemas/atlas.workflow.recovery-plan.v1.json"
CREATION_JOURNAL_SCHEMA_REF = "schemas/atlas.workflow.creation-journal.v1.json"
GENERATED_VIEW_REF = "docs/architecture/ATLAS-WORKFLOW-RECOVERY.md"
DEFAULT_RUNTIME_REF = "runtime/atlas/workflow-recovery"
DESKTOP_OBSERVATION_FIXTURE_REF = "tests/fixtures/atlas-workflow-recovery/valid-desktop-observation.json"

DESKTOP_OBSERVATION_MAX_AGE_SECONDS = 300
DESKTOP_OBSERVATION_FUTURE_SKEW_SECONDS = 30
MODERN_PERMISSION_PROFILES = frozenset({":read-only", ":workspace", ":danger-full-access"})

HEALTH_VALUES = (
    "HEALTHY",
    "DEGRADED",
    "MISSING",
    "DUPLICATE",
    "BLOCKED",
    "HELD",
    "UNKNOWN",
)


class WorkflowRecoveryError(RuntimeError):
    pass


class ValidationFailure(WorkflowRecoveryError):
    pass


class PartialCreateFailure(WorkflowRecoveryError):
    def __init__(self, message: str, mutation_receipts: list[dict[str, Any]]) -> None:
        super().__init__(message)
        self.mutation_receipts = mutation_receipts


def _load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _canonical_bytes(value: Any) -> bytes:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")


def _pretty_bytes(value: Any) -> bytes:
    return (json.dumps(value, indent=2, ensure_ascii=False) + "\n").encode("utf-8")


def _sha256_bytes(value: bytes) -> str:
    return "sha256:" + hashlib.sha256(value).hexdigest()


def _sha256_file(path: Path) -> str:
    return _sha256_bytes(path.read_bytes())


def _relative_ref(path: Path) -> str:
    return path.resolve().relative_to(ROOT.resolve()).as_posix()


def _resolve_local_ref(root_schema: dict[str, Any], reference: str) -> dict[str, Any]:
    if not reference.startswith("#/"):
        raise ValidationFailure(f"unsupported non-local schema reference: {reference}")
    current: Any = root_schema
    for raw in reference[2:].split("/"):
        segment = raw.replace("~1", "/").replace("~0", "~")
        if not isinstance(current, dict) or segment not in current:
            raise ValidationFailure(f"unresolvable schema reference: {reference}")
        current = current[segment]
    if not isinstance(current, dict):
        raise ValidationFailure(f"schema reference is not an object: {reference}")
    return current


def _type_matches(value: Any, expected: str) -> bool:
    if expected == "object":
        return isinstance(value, dict)
    if expected == "array":
        return isinstance(value, list)
    if expected == "string":
        return isinstance(value, str)
    if expected == "integer":
        return isinstance(value, int) and not isinstance(value, bool)
    if expected == "number":
        return isinstance(value, (int, float)) and not isinstance(value, bool)
    if expected == "boolean":
        return isinstance(value, bool)
    if expected == "null":
        return value is None
    raise ValidationFailure(f"unsupported schema type: {expected}")


def _schema_errors(
    value: Any,
    schema: dict[str, Any],
    root_schema: dict[str, Any] | None = None,
    at: str = "$",
) -> list[str]:
    """Validate the dependency-free JSON-Schema subset used by this packet."""

    root_schema = root_schema or schema
    if "$ref" in schema:
        return _schema_errors(value, _resolve_local_ref(root_schema, schema["$ref"]), root_schema, at)

    errors: list[str] = []
    if "const" in schema and value != schema["const"]:
        errors.append(f"{at}: expected const {schema['const']!r}")
    if "enum" in schema and value not in schema["enum"]:
        errors.append(f"{at}: value is not in enum {schema['enum']!r}")

    expected = schema.get("type")
    if expected is not None:
        allowed = expected if isinstance(expected, list) else [expected]
        if not any(_type_matches(value, item) for item in allowed):
            errors.append(f"{at}: expected type {' | '.join(allowed)}")
            return errors

    if isinstance(value, str):
        if len(value) < schema.get("minLength", 0):
            errors.append(f"{at}: string shorter than {schema['minLength']}")
        if "pattern" in schema and re.search(schema["pattern"], value) is None:
            errors.append(f"{at}: string does not match {schema['pattern']}")

    if isinstance(value, (int, float)) and not isinstance(value, bool):
        if "minimum" in schema and value < schema["minimum"]:
            errors.append(f"{at}: number below minimum {schema['minimum']}")

    if isinstance(value, list):
        if len(value) < schema.get("minItems", 0):
            errors.append(f"{at}: fewer than {schema['minItems']} items")
        child = schema.get("items")
        if isinstance(child, dict):
            for index, item in enumerate(value):
                errors.extend(_schema_errors(item, child, root_schema, f"{at}[{index}]"))

    if isinstance(value, dict):
        required = schema.get("required", [])
        for key in required:
            if key not in value:
                errors.append(f"{at}.{key}: required property missing")
        properties = schema.get("properties", {})
        if schema.get("additionalProperties") is False:
            for key in value:
                if key not in properties:
                    errors.append(f"{at}.{key}: property is not allowed")
        for key, child in properties.items():
            if key in value and isinstance(child, dict):
                errors.extend(_schema_errors(value[key], child, root_schema, f"{at}.{key}"))
    return errors


def _assert_schema(value: Any, schema_ref: str, label: str) -> None:
    schema = _load_json(ROOT / schema_ref)
    errors = _schema_errors(value, schema)
    if errors:
        joined = "\n".join(f"- {item}" for item in errors[:40])
        raise ValidationFailure(f"{label} failed {schema_ref}:\n{joined}")


def _atomic_write_bytes(path: Path, value: bytes) -> None:
    """Replace one runtime artifact atomically within its destination directory."""

    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{os.getpid()}.{time.time_ns()}.tmp")
    try:
        with temporary.open("xb") as handle:
            handle.write(value)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    except OSError as exc:
        raise WorkflowRecoveryError(f"atomic runtime artifact write failed for {path}: {exc}") from exc
    finally:
        try:
            temporary.unlink(missing_ok=True)
        except OSError:
            pass


class CreationJournal:
    """Content-addressed retained bindings written before post-create actions."""

    schema = "atlas.workflow.creation-journal.v1"

    def __init__(
        self,
        path: Path,
        manifest: dict[str, Any],
        durable_registry: dict[str, Any],
        manifest_digest: str,
    ) -> None:
        self.path = path
        self.manifest = manifest
        self.durable_registry = durable_registry
        self.manifest_digest = manifest_digest
        self.event_id: str | None = None
        self.payload_digest: str | None = None
        self.entries: dict[str, dict[str, Any]] = {}
        if path.exists():
            self._load()

    @property
    def bindings(self) -> dict[str, str]:
        return {role_id: entry["runtime_id"] for role_id, entry in self.entries.items()}

    def _load(self) -> None:
        envelope = _load_json(self.path)
        _assert_schema(envelope, CREATION_JOURNAL_SCHEMA_REF, "creation journal")
        payload_digest = _sha256_bytes(_canonical_bytes(envelope["payload"]))
        event_id = "onv1_" + payload_digest.removeprefix("sha256:")
        errors: list[str] = []
        if envelope["payload_digest"] != payload_digest:
            errors.append("payload digest mismatch")
        if envelope["event_id"] != event_id:
            errors.append("event ID mismatch")
        payload = envelope["payload"]
        if payload["manifest_digest"] != self.manifest_digest:
            errors.append(
                "manifest digest mismatch: "
                f"{payload['manifest_digest']} != {self.manifest_digest}"
            )
        role_ids = {item["role_id"] for item in self.manifest["roles"]}
        entry_role_ids = [item["role_id"] for item in payload["entries"]]
        runtime_ids = [item["runtime_id"] for item in payload["entries"]]
        if len(entry_role_ids) != len(set(entry_role_ids)):
            errors.append("role IDs are not unique")
        if len(runtime_ids) != len(set(runtime_ids)):
            errors.append("runtime IDs are not unique")
        unknown_roles = sorted(set(entry_role_ids) - role_ids)
        if unknown_roles:
            errors.append(f"unknown logical roles: {unknown_roles}")
        for entry in payload["entries"]:
            accepted_digest_hex = entry["accepted_plan_digest"].removeprefix("sha256:")
            if entry["accepted_plan_id"] != f"awrp1_{accepted_digest_hex}":
                errors.append(f"{entry['role_id']}: accepted plan ID/digest mismatch")
            post_apply_plan_id = entry["post_apply_plan_id"]
            post_apply_plan_digest = entry["post_apply_plan_digest"]
            if entry["state"] == "CREATED_PENDING_READBACK":
                if post_apply_plan_id is not None or post_apply_plan_digest is not None:
                    errors.append(
                        f"{entry['role_id']}: pending entry cannot bind a post-apply plan"
                    )
            elif post_apply_plan_id is None or post_apply_plan_digest is None:
                errors.append(
                    f"{entry['role_id']}: confirmed entry requires a post-apply plan"
                )
            elif post_apply_plan_id != (
                "awrp1_" + post_apply_plan_digest.removeprefix("sha256:")
            ):
                errors.append(f"{entry['role_id']}: post-apply plan ID/digest mismatch")
        if errors:
            raise ValidationFailure(
                "creation journal validation failed:\n- " + "\n- ".join(errors)
            )
        self.event_id = event_id
        self.payload_digest = payload_digest
        self.entries = {
            item["role_id"]: copy.deepcopy(item)
            for item in payload["entries"]
        }

    def _write(self) -> None:
        payload = {
            "manifest_digest": self.manifest_digest,
            "no_archive": True,
            "supersedes_event_id": self.event_id,
            "entries": [copy.deepcopy(self.entries[role_id]) for role_id in sorted(self.entries)],
        }
        payload_digest = _sha256_bytes(_canonical_bytes(payload))
        event_id = "onv1_" + payload_digest.removeprefix("sha256:")
        envelope = {
            "schema": self.schema,
            "event_id": event_id,
            "payload_digest": payload_digest,
            "payload": payload,
        }
        _assert_schema(envelope, CREATION_JOURNAL_SCHEMA_REF, "creation journal")
        _atomic_write_bytes(self.path, _pretty_bytes(envelope))
        self.event_id = event_id
        self.payload_digest = payload_digest

    def record_created(
        self,
        accepted_plan: dict[str, Any],
        role_id: str,
        runtime_id: str,
        adapter_name: str,
    ) -> None:
        existing = self.entries.get(role_id)
        if existing is not None:
            if existing["runtime_id"] != runtime_id:
                raise WorkflowRecoveryError(
                    f"{role_id}: creation journal collision "
                    f"{existing['runtime_id']} != {runtime_id}"
                )
            return
        if runtime_id in self.bindings.values():
            raise WorkflowRecoveryError(
                f"created runtime {runtime_id} is already retained for another logical role"
            )
        self.entries[role_id] = {
            "role_id": role_id,
            "runtime_id": runtime_id,
            "prior_runtime_id": next(
                item["current_runtime_id"]
                for item in self.durable_registry["bindings"]
                if item["role_id"] == role_id
            ),
            "accepted_plan_id": accepted_plan["plan_id"],
            "accepted_plan_digest": accepted_plan["plan_digest"],
            "created_at": accepted_plan["generated_at"],
            "adapter": adapter_name,
            "state": "CREATED_PENDING_READBACK",
            "post_apply_plan_id": None,
            "post_apply_plan_digest": None,
        }
        self._write()

    def confirm_readback(
        self,
        post_apply_plan: dict[str, Any],
        threads: Iterable["ThreadRecord"],
    ) -> None:
        roles = {item["role_id"]: item for item in post_apply_plan["roles"]}
        returned_runtime_ids = {item.thread_id for item in threads}
        changed = False
        for role_id, entry in self.entries.items():
            role = roles.get(role_id)
            if (
                role is None
                or role["runtime_id"] != entry["runtime_id"]
                or entry["runtime_id"] not in returned_runtime_ids
            ):
                raise WorkflowRecoveryError(
                    f"{role_id}: retained created runtime {entry['runtime_id']!r} "
                    "was not returned and bound by post-apply reconciliation"
                )
            if (
                entry["state"] != "READBACK_CONFIRMED"
                or entry["post_apply_plan_digest"] != post_apply_plan["plan_digest"]
            ):
                entry["state"] = "READBACK_CONFIRMED"
                entry["post_apply_plan_id"] = post_apply_plan["plan_id"]
                entry["post_apply_plan_digest"] = post_apply_plan["plan_digest"]
                changed = True
        if changed:
            self._write()

    def apply_to(self, adapter: "DiscoveryAdapter", durable_registry: dict[str, Any]) -> None:
        durable = {item["role_id"]: item for item in durable_registry["bindings"]}
        durable_runtime_owners = {
            item["current_runtime_id"]: item["role_id"]
            for item in durable_registry["bindings"]
            if item["current_runtime_id"] is not None
        }
        unbound_runtime_ids = {
            item["runtime_id"]
            for item in durable_registry["unbound_runtime_claims"]
        }
        for role_id, runtime_id in self.bindings.items():
            durable_runtime_id = durable[role_id]["current_runtime_id"]
            accepted_prior_runtime_id = self.entries[role_id]["prior_runtime_id"]
            if durable_runtime_id not in {None, runtime_id, accepted_prior_runtime_id}:
                raise WorkflowRecoveryError(
                    f"{role_id}: retained created runtime {runtime_id} conflicts with "
                    f"durable current runtime {durable_runtime_id}"
                )
            other_owner = durable_runtime_owners.get(runtime_id)
            if other_owner is not None and other_owner != role_id:
                raise WorkflowRecoveryError(
                    f"{role_id}: retained created runtime {runtime_id} is already the durable current runtime for {other_owner}"
                )
            if runtime_id in unbound_runtime_ids:
                raise WorkflowRecoveryError(
                    f"{role_id}: retained created runtime {runtime_id} is still classified as an unbound runtime claim"
                )
            adapter.binding_overrides[role_id] = runtime_id
            adapter.retained_creation_bindings[role_id] = runtime_id

    def receipt_summary(self) -> dict[str, Any] | None:
        if self.event_id is None or self.payload_digest is None:
            return None
        return {
            "path": str(self.path),
            "event_id": self.event_id,
            "payload_digest": self.payload_digest,
            "bindings": self.bindings,
        }


def validate_envelope(envelope: dict[str, Any]) -> dict[str, Any]:
    """Validate envelope shape and its canonical payload digest."""

    _assert_schema(envelope, ENVELOPE_SCHEMA_REF, "workflow envelope")
    expected_digest = _sha256_bytes(_canonical_bytes(envelope["payload"]))
    if envelope["payload_digest"] != expected_digest:
        raise ValidationFailure(
            "workflow envelope payload digest mismatch: "
            f"{envelope['payload_digest']} != {expected_digest}"
        )
    return {
        "status": "PASS",
        "event_id": envelope["event_id"],
        "payload_digest": expected_digest,
    }


def _parse_utc_timestamp(value: str, label: str) -> dt.datetime:
    try:
        parsed = dt.datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValidationFailure(f"{label} is not a valid ISO-8601 timestamp: {value}") from exc
    if parsed.tzinfo is None:
        raise ValidationFailure(f"{label} must include a timezone: {value}")
    return parsed.astimezone(dt.timezone.utc)


def _validate_desktop_observation_receipt(
    observation: dict[str, Any],
    manifest: dict[str, Any],
    registry: dict[str, Any],
    *,
    now: dt.datetime | None = None,
) -> dict[str, Any]:
    """Validate one immutable, content-addressed task/thread activity receipt."""

    _assert_schema(observation, DESKTOP_OBSERVATION_SCHEMA_REF, "desktop observation")
    expected_digest = _sha256_bytes(_canonical_bytes(observation["payload"]))
    errors: list[str] = []
    if observation["payload_digest"] != expected_digest:
        errors.append(
            "payload digest mismatch: "
            f"{observation['payload_digest']} != {expected_digest}"
        )
    expected_observation_id = "onv1_" + expected_digest.removeprefix("sha256:")
    if observation["observation_id"] != expected_observation_id:
        errors.append(
            "observation ID is not derived from the canonical payload digest: "
            f"{observation['observation_id']} != {expected_observation_id}"
        )
    payload = observation["payload"]
    supersedes = payload["supersession"]["supersedes_observation_ids"]
    if len(supersedes) != len(set(supersedes)):
        errors.append("supersedes_observation_ids contains duplicates")
    if observation["observation_id"] in supersedes:
        errors.append("observation cannot supersede itself")
    entries = payload["entries"]
    roles = {item["role_id"]: item for item in manifest["roles"]}
    bindings = {item["role_id"]: item for item in registry["bindings"]}
    expected_role_ids = set(roles)
    observed_role_ids = [item["role_id"] for item in entries]
    observed_runtime_ids = [item["runtime_thread_id"] for item in entries]

    if payload["required_role_count"] != len(expected_role_ids):
        errors.append(
            "required role count does not match the manifest denominator: "
            f"{payload['required_role_count']} != {len(expected_role_ids)}"
        )
    if len(entries) != len(expected_role_ids):
        errors.append(
            "partial or over-complete role denominator: "
            f"{len(entries)} != {len(expected_role_ids)}"
        )
    duplicate_roles = sorted(
        role_id for role_id, count in Counter(observed_role_ids).items() if count > 1
    )
    if duplicate_roles:
        errors.append("duplicate role entries: " + ", ".join(duplicate_roles))
    duplicate_runtimes = sorted(
        runtime_id for runtime_id, count in Counter(observed_runtime_ids).items() if count > 1
    )
    if duplicate_runtimes:
        errors.append("duplicate runtime entries: " + ", ".join(duplicate_runtimes))
    observed_role_set = set(observed_role_ids)
    missing_roles = sorted(expected_role_ids - observed_role_set)
    unknown_roles = sorted(observed_role_set - expected_role_ids)
    if missing_roles:
        errors.append("missing required roles: " + ", ".join(missing_roles))
    if unknown_roles:
        errors.append("unknown required roles: " + ", ".join(unknown_roles))

    now_utc = (now or dt.datetime.now(dt.timezone.utc)).astimezone(dt.timezone.utc)
    captured_at = _parse_utc_timestamp(payload["captured_at"], "payload.captured_at")

    def check_freshness(timestamp: dt.datetime, label: str) -> None:
        age_seconds = (now_utc - timestamp).total_seconds()
        if age_seconds > DESKTOP_OBSERVATION_MAX_AGE_SECONDS:
            errors.append(
                f"{label} is stale by {int(age_seconds)} seconds; "
                f"maximum is {DESKTOP_OBSERVATION_MAX_AGE_SECONDS}"
            )
        if age_seconds < -DESKTOP_OBSERVATION_FUTURE_SKEW_SECONDS:
            errors.append(
                f"{label} is in the future by {int(-age_seconds)} seconds; "
                f"maximum skew is {DESKTOP_OBSERVATION_FUTURE_SKEW_SECONDS}"
            )

    check_freshness(captured_at, "payload.captured_at")
    for index, entry in enumerate(entries):
        role_id = entry["role_id"]
        observed_at = _parse_utc_timestamp(
            entry["observed_at"], f"payload.entries[{index}].observed_at"
        )
        check_freshness(observed_at, f"payload.entries[{index}].observed_at")
        if observed_at > captured_at + dt.timedelta(seconds=DESKTOP_OBSERVATION_FUTURE_SKEW_SECONDS):
            errors.append(f"{role_id}: entry observation is later than the snapshot boundary")
        if entry["source_host_id"] != payload["source_host_id"]:
            errors.append(
                f"{role_id}: source host mismatch: "
                f"{entry['source_host_id']} != {payload['source_host_id']}"
            )
        if role_id not in roles or role_id not in bindings:
            continue
        role = roles[role_id]
        binding = bindings[role_id]
        expected_runtime_id = binding["current_runtime_id"]
        if expected_runtime_id is None:
            errors.append(f"{role_id}: durable registry has no current runtime to observe")
        elif entry["runtime_thread_id"] != expected_runtime_id:
            errors.append(
                f"{role_id}: runtime binding mismatch: "
                f"{entry['runtime_thread_id']} != {expected_runtime_id}"
            )
        expected_title = binding["title"]
        if expected_title is None or _normalize_title(entry["source_title"]) != _normalize_title(expected_title):
            errors.append(
                f"{role_id}: source title mismatch: "
                f"{entry['source_title']!r} != {expected_title!r}"
            )
        aliases = {_normalize_title(item) for item in role["title_aliases"]}
        if _normalize_title(entry["source_title"]) not in aliases:
            errors.append(f"{role_id}: source title is not a canonical role alias")

    if errors:
        raise ValidationFailure(
            "desktop observation validation failed:\n"
            + "\n".join(f"- {item}" for item in errors)
        )
    return {
        "status": "PASS",
        "observation_id": observation["observation_id"],
        "payload_digest": expected_digest,
        "role_count": len(entries),
        "source_host_id": payload["source_host_id"],
        "captured_at": payload["captured_at"],
        "pin_state": "UNKNOWN",
        "pin_capability": "UNSUPPORTED",
    }


def validate_desktop_observation(
    observation: dict[str, Any],
    current_observation: dict[str, Any],
    manifest: dict[str, Any],
    registry: dict[str, Any],
    *,
    now: dt.datetime | None = None,
) -> dict[str, Any]:
    """Validate a candidate against a trusted current immutable receipt."""

    candidate = _validate_desktop_observation_receipt(
        observation,
        manifest,
        registry,
        now=now,
    )
    if current_observation is observation:
        current = candidate
    else:
        current = _validate_desktop_observation_receipt(
            current_observation,
            manifest,
            registry,
            now=now,
        )

    errors: list[str] = []
    if candidate["observation_id"] == current["observation_id"]:
        if candidate["payload_digest"] != current["payload_digest"]:
            errors.append("candidate and current observation IDs match but payload digests differ")
    else:
        superseded_ids = current_observation["payload"]["supersession"][
            "supersedes_observation_ids"
        ]
        if candidate["observation_id"] in superseded_ids:
            errors.append(
                "observation has been superseded by trusted current observation "
                + current["observation_id"]
            )
        else:
            errors.append(
                "candidate does not match the trusted current observation and the current receipt does not prove cumulative supersession"
            )
        candidate_time = _parse_utc_timestamp(candidate["captured_at"], "candidate captured_at")
        current_time = _parse_utc_timestamp(current["captured_at"], "current captured_at")
        if current_time < candidate_time:
            errors.append("trusted current observation predates the candidate")

    if errors:
        raise ValidationFailure(
            "desktop observation current-head validation failed:\n"
            + "\n".join(f"- {item}" for item in errors)
        )
    return {
        **candidate,
        "current_observation_id": current["observation_id"],
    }


def _validate_relative_ref(reference: str, label: str) -> list[str]:
    if "://" in reference or reference.startswith("local automation:"):
        return []
    if reference.startswith("repos/"):
        # Child repositories are registered external roots and are intentionally
        # absent from a clean checkout of the ATLAS coordination repository.
        return []
    path = Path(reference)
    errors: list[str] = []
    if path.is_absolute() or ".." in path.parts or "\\" in reference:
        errors.append(f"{label}: non-portable path: {reference}")
    elif not (ROOT / path).exists():
        errors.append(f"{label}: missing path: {reference}")
    return errors


def validate_repository(
    manifest_path: Path = ROOT / MANIFEST_REF,
    registry_path: Path = ROOT / REGISTRY_REF,
    *,
    check_generated: bool = True,
) -> dict[str, Any]:
    manifest = _load_json(manifest_path)
    registry = _load_json(registry_path)
    decisions = _load_json(ROOT / DECISION_REGISTRY_REF)
    bootstrap_continuity = _load_json(ROOT / BOOTSTRAP_CONTINUITY_REF)
    _assert_schema(manifest, MANIFEST_SCHEMA_REF, "workflow manifest")
    _assert_schema(registry, REGISTRY_SCHEMA_REF, "runtime registry")
    _assert_schema(decisions, DECISION_REGISTRY_SCHEMA_REF, "decision registry")
    _assert_schema(bootstrap_continuity, "schemas/atlas.continuity.handoff.v1.json", "bootstrap continuity handoff")
    observation_fixture = _load_json(ROOT / DESKTOP_OBSERVATION_FIXTURE_REF)
    observation_fixture_now = _parse_utc_timestamp(
        observation_fixture["payload"]["captured_at"],
        "desktop observation fixture captured_at",
    )
    validate_desktop_observation(
        observation_fixture,
        observation_fixture,
        manifest,
        registry,
        now=observation_fixture_now,
    )

    errors: list[str] = []
    roles = manifest["roles"]
    role_ids = [item["role_id"] for item in roles]
    component_ids = [item["component_id"] for item in manifest["components"]]
    known_nodes = set(role_ids) | set(component_ids)
    if len(role_ids) != len(set(role_ids)):
        errors.append("manifest role IDs are not unique")
    if len(component_ids) != len(set(component_ids)):
        errors.append("manifest component IDs are not unique")
    if manifest["logical_root_role_id"] not in set(role_ids):
        errors.append("logical_root_role_id is not present in roles")

    for role in roles:
        prompt_text = ""
        for reference in role["prompt_template"]["fragments"]:
            errors.extend(_validate_relative_ref(reference, f"{role['role_id']} prompt"))
            path = ROOT / reference
            if path.exists():
                prompt_text += path.read_text(encoding="utf-8") + "\n"
        for marker in role["prompt_template"]["required_markers"]:
            if marker not in prompt_text:
                errors.append(f"{role['role_id']}: prompt marker missing: {marker}")
        for reference in role["source_of_truth"]:
            errors.extend(_validate_relative_ref(reference, f"{role['role_id']} source_of_truth"))

    for component in manifest["components"]:
        for reference in component["source_of_truth"]:
            errors.extend(_validate_relative_ref(reference, f"{component['component_id']} source_of_truth"))

    edge_ids: list[str] = []
    for edge in manifest["edges"]:
        edge_ids.append(edge["edge_id"])
        if edge["from"] not in known_nodes:
            errors.append(f"{edge['edge_id']}: unknown from node {edge['from']}")
        if edge["to"] not in known_nodes:
            errors.append(f"{edge['edge_id']}: unknown to node {edge['to']}")
    if len(edge_ids) != len(set(edge_ids)):
        errors.append("topology edge IDs are not unique")

    binding_ids = [item["role_id"] for item in registry["bindings"]]
    if set(binding_ids) != set(role_ids):
        errors.append(
            "registry role set differs from manifest: "
            f"missing={sorted(set(role_ids) - set(binding_ids))} "
            f"extra={sorted(set(binding_ids) - set(role_ids))}"
        )
    current_ids = [
        item["current_runtime_id"]
        for item in registry["bindings"]
        if item["current_runtime_id"] is not None
    ]
    if len(current_ids) != len(set(current_ids)):
        errors.append("registry current runtime IDs are not unique")
    unbound_claims = registry["unbound_runtime_claims"]
    claim_ids = [item["runtime_id"] for item in unbound_claims]
    if len(claim_ids) != len(set(claim_ids)):
        errors.append("unbound runtime claim IDs are not unique")
    if set(current_ids) & set(claim_ids):
        errors.append("a runtime ID cannot be both a current role binding and an unbound claim")
    for claim in unbound_claims:
        target = claim["canonical_target_id"]
        if target is not None and target not in known_nodes:
            errors.append(f"{claim['runtime_id']}: unknown canonical target {target}")
        if claim["admission_state"] == "DURABLY_ADMITTED":
            errors.append(f"{claim['runtime_id']}: durably admitted runtime must be bound to a role")
    question_ids = [item["question_id"] for item in decisions["questions"]]
    if len(question_ids) != len(set(question_ids)):
        errors.append("decision registry question IDs are not unique")
    for decision in decisions["questions"]:
        if decision["status"] == "ANSWERED" and decision["execution_state"] == "UNKNOWN":
            errors.append(f"{decision['question_id']}: answered decision execution state cannot be UNKNOWN")
    continuity_meta = bootstrap_continuity.get("metadata", {})
    if continuity_meta.get("source_task_id") != "019f7ded-cdb6-7d40-a102-74a70326d81c":
        errors.append("bootstrap continuity source task ID drift")
    if continuity_meta.get("successor_runtime_id") != "019f7df6-8521-7292-a012-297208fce120":
        errors.append("bootstrap continuity successor runtime ID drift")
    architect_binding = next(item for item in registry["bindings"] if item["role_id"] == "atlas.workflow-architect")
    bootstrap_epoch = next(
        (
            item
            for item in architect_binding["related_epochs"]
            if item["runtime_id"] == continuity_meta.get("source_task_id")
        ),
        None,
    )
    if bootstrap_epoch is None:
        errors.append("bootstrap continuity source task is missing from related epochs")
    else:
        expected_epoch_status = {
            "ARCHIVE_AUTHORIZED_PENDING_READBACK": "archive-authorized-pending-readback",
            "ARCHIVED": "archived",
        }.get(continuity_meta.get("source_lifecycle"))
        if expected_epoch_status is None:
            errors.append("bootstrap continuity source lifecycle is invalid")
        elif bootstrap_epoch["status"] != expected_epoch_status:
            errors.append(
                "bootstrap continuity lifecycle drift: "
                f"{bootstrap_epoch['status']} != {expected_epoch_status}"
            )
    expected_manifest_digest = _sha256_file(manifest_path)
    if registry["manifest_digest"] != expected_manifest_digest:
        errors.append(
            "registry manifest digest drift: "
            f"{registry['manifest_digest']} != {expected_manifest_digest}"
        )

    if check_generated:
        view_path = ROOT / GENERATED_VIEW_REF
        if not view_path.exists():
            errors.append(f"generated workflow view missing: {GENERATED_VIEW_REF}")
        else:
            expected_view = render_markdown(manifest, registry, expected_manifest_digest)
            if view_path.read_text(encoding="utf-8").replace("\r\n", "\n") != expected_view:
                errors.append(f"generated workflow view drift: {GENERATED_VIEW_REF}")

    if errors:
        raise ValidationFailure("workflow repository validation failed:\n" + "\n".join(f"- {item}" for item in errors))
    return {
        "status": "PASS",
        "manifest_digest": expected_manifest_digest,
        "roles": len(role_ids),
        "components": len(component_ids),
        "edges": len(edge_ids),
        "unbound_runtime_claims": len(unbound_claims),
        "manual_questions": len(question_ids),
        "answered_manual_questions": sum(item["status"] == "ANSWERED" for item in decisions["questions"]),
        "bootstrap_source_lifecycle": continuity_meta.get("source_lifecycle"),
        "desktop_observation_fixture_roles": len(observation_fixture["payload"]["entries"]),
    }


@dataclasses.dataclass
class ThreadRecord:
    thread_id: str
    title: str | None
    status: str
    cwd: str | None
    archived: bool | None
    pinned: bool | None
    preview: str = ""
    role_marker: str | None = None
    created_at: int | float | None = None
    updated_at: int | float | None = None
    raw: dict[str, Any] = dataclasses.field(default_factory=dict)

    @property
    def active(self) -> bool | None:
        value = self.status.lower()
        if value in {"active", "running", "inprogress", "in_progress"}:
            return True
        if value in {"idle", "completed", "archived"}:
            return False
        return None


class JsonRpcAppServer:
    def __init__(self, timeout_seconds: float = 25.0) -> None:
        self.timeout_seconds = timeout_seconds
        self.process: subprocess.Popen[str] | None = None
        self.messages: queue.Queue[dict[str, Any] | BaseException] = queue.Queue()
        self.stderr_lines: list[str] = []
        self._next_id = 1

    @staticmethod
    def _command() -> list[str]:
        executable = shutil.which("codex")
        if not executable:
            raise WorkflowRecoveryError("codex executable is not available")
        suffix = Path(executable).suffix.lower()
        if os.name == "nt" and suffix in {".cmd", ".bat"}:
            comspec = os.environ.get("COMSPEC", "cmd.exe")
            # cmd /s strips the only quote pair in a way that makes a quoted
            # .cmd path non-executable. The npm shim path normally has no
            # spaces; fail closed instead of guessing if it does.
            if " " in executable:
                raise WorkflowRecoveryError(
                    f"Codex command shim contains spaces and no direct executable was found: {executable}"
                )
            return [comspec, "/d", "/s", "/c", f"{executable} app-server"]
        return [executable, "app-server"]

    def __enter__(self) -> "JsonRpcAppServer":
        self.process = subprocess.Popen(
            self._command(),
            cwd=ROOT,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding="utf-8",
            errors="replace",
            bufsize=1,
        )
        assert self.process.stdout is not None
        assert self.process.stderr is not None

        def read_stdout() -> None:
            try:
                for line in self.process.stdout:
                    stripped = line.strip()
                    if stripped:
                        try:
                            self.messages.put(json.loads(stripped))
                        except json.JSONDecodeError as exc:
                            self.messages.put(WorkflowRecoveryError(f"invalid app-server JSON: {stripped[:200]}: {exc}"))
            except BaseException as exc:  # pragma: no cover - defensive reader boundary
                self.messages.put(exc)

        def read_stderr() -> None:
            for line in self.process.stderr:
                if len(self.stderr_lines) < 200:
                    self.stderr_lines.append(line.rstrip())

        threading.Thread(target=read_stdout, daemon=True).start()
        threading.Thread(target=read_stderr, daemon=True).start()
        self.request(
            "initialize",
            {
                "clientInfo": {
                    "name": "atlas-workflow-recovery",
                    "title": "ATLAS Workflow Recovery",
                    "version": "1.0.0",
                },
                "capabilities": {
                    "experimentalApi": True,
                    "optOutNotificationMethods": [
                        "item/started",
                        "item/completed",
                        "turn/outputDelta",
                    ],
                },
            },
        )
        self.notify("initialized", {})
        return self

    def __exit__(self, exc_type: Any, exc: Any, traceback: Any) -> None:
        del exc_type, exc, traceback
        if self.process is None:
            return
        if self.process.stdin is not None:
            try:
                self.process.stdin.close()
            except OSError:
                pass
        try:
            self.process.wait(timeout=2)
        except subprocess.TimeoutExpired:
            self.process.terminate()
            try:
                self.process.wait(timeout=2)
            except subprocess.TimeoutExpired:
                self.process.kill()

    def _write(self, message: dict[str, Any]) -> None:
        if self.process is None or self.process.stdin is None:
            raise WorkflowRecoveryError("app-server is not running")
        self.process.stdin.write(json.dumps(message, separators=(",", ":")) + "\n")
        self.process.stdin.flush()

    def notify(self, method: str, params: dict[str, Any]) -> None:
        self._write({"method": method, "params": params})

    def request(self, method: str, params: dict[str, Any]) -> Any:
        request_id = self._next_id
        self._next_id += 1
        self._write({"id": request_id, "method": method, "params": params})
        deadline = time.monotonic() + self.timeout_seconds
        while True:
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                stderr = " | ".join(self.stderr_lines[-8:])
                raise WorkflowRecoveryError(f"app-server timeout for {method}; stderr={stderr}")
            try:
                message = self.messages.get(timeout=remaining)
            except queue.Empty as exc:
                raise WorkflowRecoveryError(f"app-server timeout for {method}") from exc
            if isinstance(message, BaseException):
                raise WorkflowRecoveryError(str(message))
            if message.get("id") != request_id:
                continue
            if "error" in message:
                raise WorkflowRecoveryError(f"app-server {method} error: {message['error']}")
            return message.get("result")


class DiscoveryAdapter:
    name = "abstract"
    capabilities: dict[str, bool] = {}
    binding_overrides: dict[str, str]
    retained_creation_bindings: dict[str, str]

    def discover(self) -> tuple[list[ThreadRecord], list[dict[str, Any]]]:
        raise NotImplementedError

    def mutate(self, action: str, role: dict[str, Any], thread: ThreadRecord | None) -> ThreadRecord | None:
        raise NotImplementedError

    def resolve_role_cwd(self, role: dict[str, Any]) -> str:
        raise NotImplementedError

    def validate_planned_cwd(self, role_plan: dict[str, Any]) -> None:
        del role_plan


def _status_text(value: Any) -> str:
    if isinstance(value, str):
        return value
    if isinstance(value, dict):
        for key in ("type", "status", "state"):
            if isinstance(value.get(key), str):
                return value[key]
    return "unknown"


class LiveAppServerAdapter(DiscoveryAdapter):
    name = "live-app-server"
    capabilities = {
        "discover": True,
        "create": True,
        "resume": True,
        "read": True,
        "set_title": True,
        "unarchive": True,
        "bootstrap_turn": True,
        "set_runtime": False,
        "set_pin": False,
        "read_pin": False,
        "archive": False,
    }

    def __init__(
        self,
        timeout_seconds: float = 25.0,
        cwd_bindings: dict[str, Path] | None = None,
    ) -> None:
        self.timeout_seconds = timeout_seconds
        self.client: JsonRpcAppServer | None = None
        self.binding_overrides = {}
        self.retained_creation_bindings = {}
        self.cwd_bindings = dict(cwd_bindings or {})

    def _resolve_cwd_locator(self, locator: str) -> Path:
        if locator == "ATLAS_ROOT":
            resolved = ROOT.resolve()
        else:
            bound = self.cwd_bindings.get(locator)
            if bound is None:
                raise WorkflowRecoveryError(
                    f"cwd locator {locator} has no admitted absolute binding; "
                    f"pass --cwd-binding {locator}=<absolute-worktree>"
                )
            try:
                resolved = Path(bound).resolve(strict=True)
            except OSError as exc:
                raise WorkflowRecoveryError(
                    f"cwd locator {locator} is no longer resolvable: {bound}"
                ) from exc
        if not resolved.is_dir():
            raise WorkflowRecoveryError(f"cwd locator {locator} does not resolve to a directory: {resolved}")
        if locator != "ATLAS_ROOT" and resolved == ROOT.resolve():
            raise WorkflowRecoveryError(
                f"cwd locator {locator} resolves to the ATLAS recovery checkout instead of an admitted isolated worktree"
            )
        return resolved

    def resolve_role_cwd(self, role: dict[str, Any]) -> str:
        return str(self._resolve_cwd_locator(role["runtime"]["cwd_locator"]))

    def validate_planned_cwd(self, role_plan: dict[str, Any]) -> None:
        expected = str(self._resolve_cwd_locator(role_plan["cwd_locator"]))
        if role_plan.get("resolved_cwd") != expected:
            raise WorkflowRecoveryError(
                f"{role_plan['role_id']}: accepted cwd binding drifted; "
                f"plan={role_plan.get('resolved_cwd')!r} current={expected!r}"
            )

    def _thread_start_params(self, role: dict[str, Any]) -> dict[str, Any]:
        runtime = role["runtime"]
        permission_profile = runtime["permissions"]
        if permission_profile not in MODERN_PERMISSION_PROFILES:
            raise WorkflowRecoveryError(
                f"{role['role_id']}: unsupported modern permission profile {permission_profile!r}; "
                "legacy sandbox tokens are not accepted"
            )
        return {
            "cwd": self.resolve_role_cwd(role),
            "model": runtime["model"],
            "approvalPolicy": runtime["approval_policy"],
            "permissions": permission_profile,
            "serviceTier": runtime["service_tier"],
            "ephemeral": False,
        }

    def _bootstrap_params(self, role: dict[str, Any], thread_id: str) -> dict[str, Any]:
        runtime = role["runtime"]
        return {
            "threadId": thread_id,
            "input": [{"type": "text", "text": self._prompt(role)}],
            "cwd": self.resolve_role_cwd(role),
            "model": runtime["model"],
            "effort": runtime["effort_floor"],
            "approvalPolicy": runtime["approval_policy"],
        }

    @staticmethod
    def _thread_from_raw(raw: dict[str, Any], archived: bool) -> ThreadRecord:
        title = raw.get("name")
        preview = raw.get("preview") or ""
        if not title and preview:
            first = preview.splitlines()[0].strip()
            if first and len(first) <= 160:
                title = first
        return ThreadRecord(
            thread_id=str(raw.get("id") or raw.get("sessionId") or ""),
            title=title,
            status=_status_text(raw.get("status")),
            cwd=raw.get("cwd"),
            archived=archived,
            pinned=None,
            preview=preview,
            created_at=raw.get("createdAt"),
            updated_at=raw.get("updatedAt"),
            raw=raw,
        )

    def _list(self, client: JsonRpcAppServer, archived: bool) -> list[ThreadRecord]:
        result: list[ThreadRecord] = []
        cursor: str | None = None
        seen: set[str] = set()
        for _ in range(100):
            params: dict[str, Any] = {
                "archived": archived,
                "limit": 100,
                "sortKey": "updated_at",
                "sortDirection": "desc",
            }
            if cursor:
                params["cursor"] = cursor
            response = client.request("thread/list", params) or {}
            for raw in response.get("data", []):
                record = self._thread_from_raw(raw, archived)
                if record.thread_id and record.thread_id not in seen:
                    result.append(record)
                    seen.add(record.thread_id)
            cursor = response.get("nextCursor")
            if not cursor:
                break
        else:
            raise WorkflowRecoveryError("thread/list exceeded 100 pages")
        return result

    def discover(self) -> tuple[list[ThreadRecord], list[dict[str, Any]]]:
        with JsonRpcAppServer(self.timeout_seconds) as client:
            active = self._list(client, archived=False)
            archived = self._list(client, archived=True)
        return active + archived, []

    def _prompt(self, role: dict[str, Any], bindings: dict[str, str] | None = None) -> str:
        fragments = [
            (ROOT / ref).read_text(encoding="utf-8").strip()
            for ref in role["prompt_template"]["fragments"]
        ]
        if bindings:
            fragments.append(
                "# Generated logical bindings\n\n"
                + "\n".join(f"- {key}: {value}" for key, value in sorted(bindings.items()))
            )
        return "\n\n".join(fragments) + "\n"

    def mutate(self, action: str, role: dict[str, Any], thread: ThreadRecord | None) -> ThreadRecord | None:
        if action in {"SET_PIN", "PROVE_PIN_STATE"}:
            raise WorkflowRecoveryError("Codex app-server exposes neither pin mutation nor pin readback; manual desktop fallback required")
        if action == "SET_RUNTIME_POLICY":
            raise WorkflowRecoveryError(
                "Codex app-server exposes no supported mutation for an existing thread runtime policy"
            )
        if action == "CREATE":
            with JsonRpcAppServer(self.timeout_seconds) as client:
                response = client.request(
                    "thread/start",
                    self._thread_start_params(role),
                )
            raw = (response or {}).get("thread", response or {})
            return self._thread_from_raw(raw, archived=False)
        if thread is None:
            raise WorkflowRecoveryError(f"{action} requires a runtime")
        with JsonRpcAppServer(self.timeout_seconds) as client:
            if action == "SET_TITLE":
                client.request("thread/name/set", {"threadId": thread.thread_id, "name": role["human_title"]})
                thread.title = role["human_title"]
            elif action == "UNARCHIVE":
                client.request("thread/unarchive", {"threadId": thread.thread_id})
                thread.archived = False
            elif action == "RESUME":
                client.request("thread/resume", {"threadId": thread.thread_id})
                thread.status = "idle"
            elif action == "BOOTSTRAP":
                client.request(
                    "turn/start",
                    self._bootstrap_params(role, thread.thread_id),
                )
            elif action == "REFRESH_REGISTRY":
                self.binding_overrides[role["role_id"]] = thread.thread_id
            elif action in {"POST_CREATE_READBACK", "POST_REPAIR_READBACK", "UPDATE_BINDING"}:
                pass
            else:
                raise WorkflowRecoveryError(f"unsupported live action: {action}")
        return thread


class FixtureAdapter(DiscoveryAdapter):
    name = "fixture"
    capabilities = {
        "discover": True,
        "create": True,
        "resume": True,
        "read": True,
        "set_title": True,
        "unarchive": True,
        "bootstrap_turn": True,
        "set_runtime": True,
        "set_pin": True,
        "read_pin": True,
        "archive": False,
    }

    def __init__(self, manifest: dict[str, Any], registry: dict[str, Any], fixture: dict[str, Any]) -> None:
        self.manifest = manifest
        self.registry = registry
        self.fixture = fixture
        self.threads = self._build_threads()
        self.leases = copy.deepcopy(fixture.get("leases", []))
        self.mutations = 0
        self.fail_after_mutations = fixture.get("fail_after_mutations")
        self.created_counter = 0
        self.binding_overrides = {}
        self.retained_creation_bindings = {}

    def resolve_role_cwd(self, role: dict[str, Any]) -> str:
        return role["runtime"]["cwd_locator"]

    def validate_planned_cwd(self, role_plan: dict[str, Any]) -> None:
        if role_plan.get("resolved_cwd") != role_plan["cwd_locator"]:
            raise WorkflowRecoveryError(f"{role_plan['role_id']}: fixture cwd binding drifted")

    def _build_threads(self) -> list[ThreadRecord]:
        roles = {item["role_id"]: item for item in self.manifest["roles"]}
        bindings = {item["role_id"]: item for item in self.registry["bindings"]}
        records: list[ThreadRecord] = []
        if self.fixture.get("seed_from_registry", True):
            for role_id, role in roles.items():
                binding = bindings[role_id]
                if binding["current_runtime_id"] is None:
                    continue
                records.append(
                    ThreadRecord(
                        thread_id=binding["current_runtime_id"],
                        title=role["human_title"],
                        status=self.fixture.get("seed_status", "idle"),
                        cwd=binding["cwd"],
                        archived=False,
                        pinned=self.fixture.get("seed_pinned", True),
                        preview="fixture standing role",
                        role_marker=role_id,
                        created_at=1000,
                        updated_at=1000,
                    )
                )

        def find_role(role_id: str) -> ThreadRecord | None:
            return next((item for item in records if item.role_marker == role_id), None)

        for operation in self.fixture.get("operations", []):
            kind = operation["op"]
            role_id = operation.get("role_id")
            if kind == "remove":
                records = [item for item in records if item.role_marker != role_id]
            elif kind == "stale_id":
                record = find_role(role_id)
                if record is None:
                    raise ValidationFailure(f"fixture stale_id role missing: {role_id}")
                record.thread_id = operation["runtime_id"]
            elif kind == "set_status":
                record = find_role(role_id)
                if record is None:
                    raise ValidationFailure(f"fixture set_status role missing: {role_id}")
                record.status = operation["status"]
            elif kind == "set_archived":
                record = find_role(role_id)
                if record is None:
                    raise ValidationFailure(f"fixture set_archived role missing: {role_id}")
                record.archived = operation["archived"]
            elif kind == "set_pinned":
                record = find_role(role_id)
                if record is None:
                    raise ValidationFailure(f"fixture set_pinned role missing: {role_id}")
                record.pinned = operation["pinned"]
            elif kind == "duplicate":
                source = find_role(role_id)
                if source is None:
                    raise ValidationFailure(f"fixture duplicate role missing: {role_id}")
                duplicate = copy.deepcopy(source)
                duplicate.thread_id = operation["runtime_id"]
                duplicate.role_marker = role_id
                records.append(duplicate)
            elif kind == "partial_runtime":
                records = [item for item in records if item.role_marker != role_id]
                records.append(
                    ThreadRecord(
                        thread_id=operation["runtime_id"],
                        title=operation.get("title"),
                        status=operation.get("status", "idle"),
                        cwd=operation.get("cwd"),
                        archived=operation.get("archived", False),
                        pinned=operation.get("pinned", False),
                        preview="partial recovery runtime",
                        role_marker=role_id,
                        created_at=2000,
                        updated_at=2000,
                    )
                )
            else:
                raise ValidationFailure(f"unsupported fixture operation: {kind}")
        return records

    def discover(self) -> tuple[list[ThreadRecord], list[dict[str, Any]]]:
        if self.fixture.get("discovery_error"):
            raise WorkflowRecoveryError(self.fixture["discovery_error"])
        return copy.deepcopy(self.threads), copy.deepcopy(self.leases)

    def _record_mutation(self) -> None:
        self.mutations += 1
        if self.fail_after_mutations is not None and self.mutations > self.fail_after_mutations:
            raise WorkflowRecoveryError(f"fixture injected failure after {self.fail_after_mutations} mutation(s)")

    def mutate(self, action: str, role: dict[str, Any], thread: ThreadRecord | None) -> ThreadRecord | None:
        if thread is not None:
            persisted = next(
                (item for item in self.threads if item.thread_id == thread.thread_id),
                None,
            )
            if persisted is not None:
                thread = persisted
        if action in {"POST_CREATE_READBACK", "POST_REPAIR_READBACK", "UPDATE_BINDING", "PROVE_PIN_STATE"}:
            return thread
        if action == "REFRESH_REGISTRY":
            if thread is None:
                raise WorkflowRecoveryError("fixture REFRESH_REGISTRY requires a runtime")
            self.binding_overrides[role["role_id"]] = thread.thread_id
            return thread
        self._record_mutation()
        if action == "CREATE":
            self.created_counter += 1
            thread = ThreadRecord(
                thread_id=f"fixture-created-{role['role_id']}-{self.created_counter}",
                title=None,
                status="idle",
                cwd=role["runtime"]["cwd_locator"],
                archived=False,
                pinned=False,
                preview="",
                role_marker=role["role_id"],
                created_at=3000 + self.created_counter,
                updated_at=3000 + self.created_counter,
            )
            self.threads.append(thread)
        elif thread is None:
            raise WorkflowRecoveryError(f"fixture {action} requires a runtime")
        elif action == "SET_TITLE":
            thread.title = role["human_title"]
        elif action == "SET_RUNTIME_POLICY":
            thread.cwd = role["runtime"]["cwd_locator"]
        elif action == "SET_PIN":
            thread.pinned = True
        elif action == "UNARCHIVE":
            thread.archived = False
        elif action == "RESUME":
            thread.status = "idle"
        elif action == "BOOTSTRAP":
            thread.preview = "\n".join(role["prompt_template"]["required_markers"])
        else:
            raise WorkflowRecoveryError(f"unsupported fixture action: {action}")
        return thread


def _normalize_title(value: str | None) -> str:
    return re.sub(r"\s+", " ", (value or "").strip()).casefold()


def _role_claims(role: dict[str, Any], thread: ThreadRecord) -> bool:
    if thread.role_marker == role["role_id"]:
        return True
    aliases = {_normalize_title(item) for item in role["title_aliases"]}
    return bool(thread.title) and _normalize_title(thread.title) in aliases


def _actions_for_record(role: dict[str, Any], record: ThreadRecord, *, stale_binding: bool) -> tuple[list[str], list[str]]:
    actions: list[str] = []
    reasons: list[str] = []
    aliases = {_normalize_title(item) for item in role["title_aliases"]}
    if stale_binding:
        actions.append("UPDATE_BINDING")
        reasons.append("durable runtime ID is stale; one unique role candidate was discovered")
    if record.title is None or _normalize_title(record.title) not in aliases:
        actions.append("SET_TITLE")
        reasons.append("runtime title does not match a canonical alias")
    if record.cwd is None:
        actions.append("SET_RUNTIME_POLICY")
        reasons.append("runtime cwd/project policy is missing")
    if record.archived is True:
        actions.append("UNARCHIVE")
        reasons.append("required standing runtime is archived")
    elif record.archived is None:
        actions.append("PROVE_ARCHIVE_STATE")
        reasons.append("archive state is unknown")
    if record.pinned is False:
        actions.append("SET_PIN")
        reasons.append("required standing runtime is unpinned")
    elif record.pinned is None:
        actions.append("PROVE_PIN_STATE")
        reasons.append("pin state is unavailable through the discovery adapter")
    if record.status.lower() in {"notloaded", "not_loaded"}:
        actions.append("PROVE_IDLE_BOUNDARY")
        reasons.append(
            "runtime is persisted but an isolated app-server cannot prove desktop active/idle state"
        )
    elif record.active is None:
        actions.append("PROVE_IDLE_BOUNDARY")
        reasons.append(f"runtime status is unknown: {record.status}")
    if actions:
        actions.extend(["POST_REPAIR_READBACK", "REFRESH_REGISTRY"])
    return list(dict.fromkeys(actions)), reasons


def _apply_desktop_observation_statuses(
    threads: list[ThreadRecord],
    observation: dict[str, Any],
) -> tuple[list[ThreadRecord], set[str]]:
    """Overlay only supported activity evidence onto already discovered runtimes."""

    observed_threads = copy.deepcopy(threads)
    by_id = {item.thread_id: item for item in observed_threads}
    applied_role_ids: set[str] = set()
    for entry in observation["payload"]["entries"]:
        record = by_id.get(entry["runtime_thread_id"])
        if record is None:
            continue
        record.status = entry["activity"]
        record.raw = {
            **record.raw,
            "desktop_observation_activity": entry["activity"],
        }
        applied_role_ids.add(entry["role_id"])
    return observed_threads, applied_role_ids


def build_recovery_plan(
    manifest: dict[str, Any],
    registry: dict[str, Any],
    adapter: DiscoveryAdapter,
    *,
    mode: str,
    deterministic: bool,
    desktop_observation: dict[str, Any] | None = None,
    desktop_observation_current: dict[str, Any] | None = None,
    observation_now: dt.datetime | None = None,
) -> tuple[dict[str, Any], list[ThreadRecord], list[dict[str, Any]]]:
    manifest_digest = _sha256_file(ROOT / MANIFEST_REF)
    registry_digest = _sha256_file(ROOT / REGISTRY_REF)
    bindings = {item["role_id"]: item for item in registry["bindings"]}
    roles = {item["role_id"]: item for item in manifest["roles"]}
    generated_at = "DETERMINISTIC" if deterministic else dt.datetime.now(dt.timezone.utc).isoformat().replace("+00:00", "Z")

    observation_result: dict[str, Any] | None = None
    observation_entries: dict[str, dict[str, Any]] = {}
    if desktop_observation is not None:
        if desktop_observation_current is None:
            raise ValidationFailure(
                "desktop observation requires a trusted current observation receipt"
            )
        observation_result = validate_desktop_observation(
            desktop_observation,
            desktop_observation_current,
            manifest,
            registry,
            now=observation_now,
        )
        observation_entries = {
            item["role_id"]: item for item in desktop_observation["payload"]["entries"]
        }

    try:
        threads, leases = adapter.discover()
        discovery_error: str | None = None
    except WorkflowRecoveryError as exc:
        threads, leases = [], []
        discovery_error = str(exc)

    observation_applied_roles: set[str] = set()
    if desktop_observation is not None and discovery_error is None:
        threads, observation_applied_roles = _apply_desktop_observation_statuses(
            threads,
            desktop_observation,
        )

    by_id = {item.thread_id: item for item in threads}
    results: list[dict[str, Any]] = []
    for role_id in sorted(roles):
        role = roles[role_id]
        binding = bindings[role_id]
        current_id = adapter.binding_overrides.get(role_id, binding["current_runtime_id"])
        related_ids = {item["runtime_id"] for item in binding["related_epochs"]}
        if discovery_error:
            results.append(
                {
                    "role_id": role_id,
                    "runtime_id": current_id,
                    "health": "UNKNOWN",
                    "decision": "FAIL_CLOSED_UNKNOWN",
                    "actions": [],
                    "reasons": [f"discovery failed: {discovery_error}"],
                    "active": None,
                    "archived": None,
                    "pinned": None,
                }
            )
            continue

        current = by_id.get(current_id) if current_id else None
        retained_runtime_id = adapter.retained_creation_bindings.get(role_id)
        if retained_runtime_id is not None and current is None:
            results.append(
                {
                    "role_id": role_id,
                    "runtime_id": retained_runtime_id,
                    "health": "BLOCKED",
                    "decision": "FAIL_CLOSED_RETAINED_CREATION_NOT_DISCOVERED",
                    "actions": [],
                    "reasons": [
                        "the atomic creation journal retains this runtime ID, but complete discovery did not return it; never create a replacement until identity is reconciled"
                    ],
                    "active": None,
                    "archived": None,
                    "pinned": None,
                }
            )
            continue
        if (
            current is None
            and role_id in observation_entries
            and observation_entries[role_id]["runtime_thread_id"] == current_id
        ):
            results.append(
                {
                    "role_id": role_id,
                    "runtime_id": current_id,
                    "health": "UNKNOWN",
                    "decision": "FAIL_CLOSED_OBSERVATION_DISCOVERY_MISMATCH",
                    "actions": [],
                    "reasons": [
                        "validated activity observation names the durable runtime, but primary discovery did not return it; activity evidence cannot establish existence or authorize repair"
                    ],
                    "active": None,
                    "archived": None,
                    "pinned": None,
                }
            )
            continue
        claims = [item for item in threads if _role_claims(role, item)]
        other_claims = [
            item
            for item in claims
            if item.thread_id != current_id and item.thread_id not in related_ids
        ]

        def is_unaccepted_duplicate(item: ThreadRecord) -> bool:
            if item.role_marker == role_id or item.active is True:
                return True
            if current is None:
                return True
            if item.created_at is None or current.created_at is None:
                return True
            # Exact-title sessions older than the accepted epoch are historical
            # residue, not standing-role duplicates. Newer claimants still fail
            # closed unless the durable registry names their relationship.
            return item.created_at >= current.created_at

        unaccepted = [item for item in other_claims if is_unaccepted_duplicate(item)]
        historical_residue = [item for item in other_claims if item not in unaccepted]
        if current is not None and unaccepted:
            results.append(
                {
                    "role_id": role_id,
                    "runtime_id": current.thread_id,
                    "health": "DUPLICATE",
                    "decision": "FAIL_CLOSED_DUPLICATE",
                    "actions": [],
                    "reasons": [
                        "unaccepted runtimes also claim this logical role: "
                        + ", ".join(sorted(item.thread_id for item in unaccepted))
                    ],
                    "active": current.active,
                    "archived": current.archived,
                    "pinned": current.pinned,
                }
            )
            continue

        if current is None:
            candidates = [item for item in claims if item.thread_id not in related_ids]
            if len(candidates) > 1:
                results.append(
                    {
                        "role_id": role_id,
                        "runtime_id": None,
                        "health": "DUPLICATE",
                        "decision": "FAIL_CLOSED_DUPLICATE",
                        "actions": [],
                        "reasons": ["multiple candidates claim the role: " + ", ".join(sorted(item.thread_id for item in candidates))],
                        "active": None,
                        "archived": None,
                        "pinned": None,
                    }
                )
                continue
            if len(candidates) == 1:
                current = candidates[0]
                actions, reasons = _actions_for_record(role, current, stale_binding=True)
                health = "DEGRADED"
                decision = "REPAIR_UNIQUE_STALE_BINDING"
            else:
                policy = role["creation_policy"]
                if policy == "create_if_missing":
                    actions = [
                        "CREATE",
                        "SET_TITLE",
                        "SET_PIN",
                        "BOOTSTRAP",
                        "POST_CREATE_READBACK",
                        "REFRESH_REGISTRY",
                    ]
                    reasons = ["complete discovery found no current or candidate runtime"]
                    health = "MISSING"
                    decision = "CREATE_MISSING_AFTER_ACCEPTANCE"
                elif policy == "reuse_only":
                    actions = []
                    reasons = ["role is missing and manifest requires reuse of an accepted standing epoch"]
                    health = "BLOCKED"
                    decision = "BLOCKED_REUSE_ONLY"
                else:
                    actions = []
                    reasons = ["role is missing and creation requires an explicit lifecycle/admission decision"]
                    health = "BLOCKED"
                    decision = "BLOCKED_MANUAL_GATE"
                results.append(
                    {
                        "role_id": role_id,
                        "runtime_id": None,
                        "health": health,
                        "decision": decision,
                        "actions": actions,
                        "reasons": reasons,
                        "active": None,
                        "archived": None,
                        "pinned": None,
                    }
                )
                continue
        else:
            actions, reasons = _actions_for_record(role, current, stale_binding=False)
            if role_id in observation_applied_roles:
                reasons.append("activity status comes from a validated supported task/thread readback observation")
            if historical_residue:
                reasons.append(
                    "ignored older exact-title historical residue: "
                    + ", ".join(sorted(item.thread_id for item in historical_residue))
                )
            if current.active is True:
                decision = "REUSE_ACTIVE_NO_STEER" if not actions else "REUSE_ACTIVE_HOLD_REPAIRS"
            elif actions:
                decision = "REUSE_AND_REPAIR_AFTER_ACCEPTANCE"
            else:
                decision = "REUSE_NO_CHANGE"
            health = "HEALTHY" if not actions else "DEGRADED"

        if (
            role_id in observation_applied_roles
            and current.active is True
            and role.get("writer_scope") not in {None, "", "read-only"}
        ):
            actions = []
            health = "BLOCKED"
            decision = "FAIL_CLOSED_OBSERVED_ACTIVE_WRITER"
            reasons.append(
                "validated observation reports an active writer; recovery must not steer, repair, or mutate it"
            )

        assert current is not None
        results.append(
            {
                "role_id": role_id,
                "runtime_id": current.thread_id,
                "health": health,
                "decision": decision,
                "actions": actions,
                "reasons": reasons or ["unique runtime matches canonical role and requires no change"],
                "active": current.active,
                "archived": current.archived,
                "pinned": current.pinned,
            }
        )

    for item in results:
        role = roles[item["role_id"]]
        item["cwd_locator"] = role["runtime"]["cwd_locator"]
        item["resolved_cwd"] = None
        if any(action in {"CREATE", "BOOTSTRAP"} for action in item["actions"]):
            try:
                item["resolved_cwd"] = adapter.resolve_role_cwd(role)
            except WorkflowRecoveryError as exc:
                item["health"] = "BLOCKED"
                item["decision"] = "FAIL_CLOSED_CWD_BINDING_REQUIRED"
                item["actions"] = []
                item["reasons"].append(str(exc))

    lease_groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for lease in leases:
        if str(lease.get("status", "")).lower() == "active":
            lease_groups[str(lease.get("writer_scope"))].append(lease)
    collisions = {scope: items for scope, items in lease_groups.items() if scope and len(items) > 1}
    if collisions:
        role_by_id = {item["role_id"]: item for item in results}
        for role_id, role in roles.items():
            scope = role.get("writer_scope")
            if scope in collisions:
                item = role_by_id[role_id]
                item["health"] = "BLOCKED"
                item["decision"] = "FAIL_CLOSED_ACTIVE_WRITER_COLLISION"
                item["actions"] = []
                item["reasons"] = [
                    f"writer scope {scope} has {len(collisions[scope])} active leases"
                ]

    counts = Counter(item["health"] for item in results)
    if counts["DUPLICATE"] or counts["BLOCKED"]:
        terminal = "BLOCKED"
    elif counts["UNKNOWN"]:
        terminal = "UNKNOWN"
    elif all(item["health"] == "HEALTHY" for item in results):
        terminal = "HEALTHY"
    else:
        terminal = "DEGRADED"

    plan: dict[str, Any] = {
        "schema": "atlas.workflow.recovery-plan.v1",
        "manifest_ref": MANIFEST_REF,
        "manifest_digest": manifest_digest,
        "registry_ref": REGISTRY_REF,
        "registry_digest": registry_digest,
        "adapter": adapter.name,
        "mode": mode,
        "no_archive": True,
        "generated_at": generated_at,
        "capabilities": dict(adapter.capabilities),
        "roles": results,
        "summary": {
            "role_count": len(results),
            "health_counts": {name: counts[name] for name in HEALTH_VALUES},
            "create_count": sum("CREATE" in item["actions"] for item in results),
            "reuse_count": sum(item["runtime_id"] is not None for item in results),
            "duplicate_count": counts["DUPLICATE"],
            "active_no_steer_count": sum(item["active"] is True for item in results),
            "writer_collision_scopes": sorted(collisions),
            "volatile_fields_excluded_from_digest": ["generated_at"],
        },
        "terminal_status": terminal,
        "plan_digest": "",
        "plan_id": "",
    }
    if observation_result is not None:
        plan["summary"]["desktop_observation"] = {
            "present": True,
            "observation_id": observation_result["observation_id"],
            "current_observation_id": observation_result["current_observation_id"],
            "payload_digest": observation_result["payload_digest"],
            "source_host_id": observation_result["source_host_id"],
            "captured_at": observation_result["captured_at"],
            "validated_role_count": observation_result["role_count"],
            "applied_activity_count": len(observation_applied_roles),
            "pin_state": "UNKNOWN",
            "pin_capability": "UNSUPPORTED",
            "plan_identity_binding": "validated activity effects only",
        }
        plan["summary"]["volatile_fields_excluded_from_digest"].extend(
            [
                "summary.desktop_observation.observation_id",
                "summary.desktop_observation.current_observation_id",
                "summary.desktop_observation.payload_digest",
                "summary.desktop_observation.source_host_id",
                "summary.desktop_observation.captured_at",
            ]
        )
    digest_source = copy.deepcopy(plan)
    digest_source["generated_at"] = "<volatile>"
    if observation_result is not None:
        observation_digest_source = digest_source["summary"]["desktop_observation"]
        for key in (
            "observation_id",
            "current_observation_id",
            "payload_digest",
            "source_host_id",
            "captured_at",
        ):
            observation_digest_source[key] = "<volatile>"
    digest_source["plan_digest"] = ""
    digest_source["plan_id"] = ""
    plan_digest = _sha256_bytes(_canonical_bytes(digest_source))
    plan["plan_digest"] = plan_digest
    plan["plan_id"] = "awrp1_" + plan_digest.removeprefix("sha256:")
    _assert_schema(plan, PLAN_SCHEMA_REF, "recovery plan")
    return plan, threads, leases


def _load_acceptance(
    path: Path,
    plan: dict[str, Any],
    *,
    allow_fixture_template: bool = False,
) -> dict[str, Any]:
    value = _load_json(path)
    if allow_fixture_template and value.get("fixture_only") is True:
        required_fixture = {
            "schema": "atlas.workflow.recovery-acceptance.v1",
            "accepted_by_role_id": "atlas.main",
            "no_archive": True,
        }
        errors = [
            f"{key} must equal {expected!r}"
            for key, expected in required_fixture.items()
            if value.get(key) != expected
        ]
        if errors:
            raise ValidationFailure("invalid fixture acceptance:\n- " + "\n- ".join(errors))
        return value
    required = {
        "schema": "atlas.workflow.recovery-acceptance.v1",
        "manifest_digest": plan["manifest_digest"],
        "plan_digest": plan["plan_digest"],
        "no_archive": True,
    }
    errors = [f"{key} must equal {expected!r}" for key, expected in required.items() if value.get(key) != expected]
    if not isinstance(value.get("event_id"), str) or not value["event_id"]:
        errors.append("event_id is required")
    if value.get("accepted_by_role_id") != "atlas.main":
        errors.append("accepted_by_role_id must be atlas.main")
    if errors:
        raise ValidationFailure("invalid live recovery acceptance:\n- " + "\n- ".join(errors))
    return value


def _preflight_apply(plan: dict[str, Any], adapter: DiscoveryAdapter) -> None:
    for item in plan["roles"]:
        if item["decision"] in {
            "FAIL_CLOSED_OBSERVED_ACTIVE_WRITER",
            "FAIL_CLOSED_OBSERVATION_DISCOVERY_MISMATCH",
        }:
            raise WorkflowRecoveryError(
                f"{item['role_id']}: {item['decision']}; fail closed"
            )
        if item["active"] is True and item["actions"]:
            raise WorkflowRecoveryError(f"{item['role_id']}: active runtime has pending repairs; fail closed without steering")
        if any(action in {"CREATE", "BOOTSTRAP"} for action in item["actions"]):
            adapter.validate_planned_cwd(item)
        for action in item["actions"]:
            capability = {
                "CREATE": "create",
                "SET_TITLE": "set_title",
                "SET_RUNTIME_POLICY": "set_runtime",
                "SET_PIN": "set_pin",
                "PROVE_PIN_STATE": "read_pin",
                "UNARCHIVE": "unarchive",
                "RESUME": "resume",
                "BOOTSTRAP": "bootstrap_turn",
            }.get(action)
            if capability and not adapter.capabilities.get(capability, False):
                raise WorkflowRecoveryError(
                    f"{item['role_id']}: {action} is required but adapter capability {capability} is unavailable; fail closed"
                )
            if action in {"PROVE_ARCHIVE_STATE", "PROVE_IDLE_BOUNDARY"}:
                raise WorkflowRecoveryError(f"{item['role_id']}: {action} requires manual/live proof before mutation")


def apply_plan(
    plan: dict[str, Any],
    manifest: dict[str, Any],
    adapter: DiscoveryAdapter,
    creation_journal: CreationJournal | None = None,
) -> list[dict[str, Any]]:
    _preflight_apply(plan, adapter)
    roles = {item["role_id"]: item for item in manifest["roles"]}
    discovered, _ = adapter.discover()
    by_id = {item.thread_id: item for item in discovered}
    receipts: list[dict[str, Any]] = []
    try:
        for item in plan["roles"]:
            role = roles[item["role_id"]]
            thread = by_id.get(item["runtime_id"]) if item["runtime_id"] else None
            for action in item["actions"]:
                before_id = thread.thread_id if thread else None
                thread = adapter.mutate(action, role, thread)
                after_id = thread.thread_id if thread else None
                if action == "CREATE" and after_id:
                    # Preserve the accepted plan as immutable. The newly created
                    # runtime is carried separately into post-apply readback and
                    # registry generation.
                    adapter.binding_overrides[item["role_id"]] = after_id
                receipt = {
                    "role_id": item["role_id"],
                    "action": action,
                    "before_runtime_id": before_id,
                    "after_runtime_id": after_id,
                    "status": "APPLIED",
                }
                receipts.append(receipt)
                if action == "CREATE" and after_id and creation_journal is not None:
                    creation_journal.record_created(
                        plan,
                        item["role_id"],
                        after_id,
                        adapter.name,
                    )
                    # The same process must use the durable binding immediately;
                    # otherwise a failed post-apply discovery could plan a second
                    # CREATE before a restart has a chance to reload the journal.
                    adapter.retained_creation_bindings[item["role_id"]] = after_id
    except WorkflowRecoveryError as exc:
        raise PartialCreateFailure(str(exc), receipts) from exc
    return receipts


def build_runtime_registry(
    manifest: dict[str, Any],
    durable_registry: dict[str, Any],
    plan: dict[str, Any],
    threads: Iterable[ThreadRecord],
    runtime_id_overrides: dict[str, str] | None = None,
) -> dict[str, Any]:
    by_id = {item.thread_id: item for item in threads}
    durable = {item["role_id"]: item for item in durable_registry["bindings"]}
    runtime_id_overrides = dict(runtime_id_overrides or {})
    bindings: list[dict[str, Any]] = []
    for item in plan["roles"]:
        old = durable[item["role_id"]]
        runtime_id = runtime_id_overrides.get(item["role_id"], item["runtime_id"])
        runtime = by_id.get(runtime_id) if runtime_id else None
        applied_binding = item["role_id"] in runtime_id_overrides
        if applied_binding and runtime is None:
            raise WorkflowRecoveryError(
                f"{item['role_id']}: post-apply runtime {runtime_id!r} was not returned by readback; fail closed"
            )
        bindings.append(
            {
                "role_id": item["role_id"],
                "current_runtime_id": runtime_id,
                "runtime_status": runtime.status if runtime else "missing",
                "health": item["health"],
                "archived": runtime.archived if runtime else None,
                "title": runtime.title if runtime else None,
                "cwd": runtime.cwd if runtime else None,
                "evidence": [
                    f"recovery-plan:{plan['plan_id']}",
                    f"adapter:{plan['adapter']}",
                    *(
                        ["post-apply runtime binding returned by complete readback"]
                        if applied_binding
                        else []
                    ),
                    *item["reasons"],
                ],
                "related_epochs": old["related_epochs"],
            }
        )
    return {
        "schema": "atlas.workflow.runtime-registry.v1",
        "manifest_ref": MANIFEST_REF,
        "manifest_digest": plan["manifest_digest"],
        "observed_at": plan["generated_at"],
        "observation_precision": "second" if plan["generated_at"] != "DETERMINISTIC" else "day",
        "discovery": {
            "sources": [f"recovery adapter: {plan['adapter']}", f"plan: {plan['plan_id']}"],
            "unknown_preserved": True,
        },
        "bindings": bindings,
        "unbound_runtime_claims": durable_registry["unbound_runtime_claims"],
    }


def render_markdown(
    manifest: dict[str, Any],
    registry: dict[str, Any],
    manifest_digest: str | None = None,
) -> str:
    manifest_digest = manifest_digest or _sha256_bytes(_pretty_bytes(manifest))
    bindings = {item["role_id"]: item for item in registry["bindings"]}
    decisions = _load_json(ROOT / DECISION_REGISTRY_REF)
    lines = [
        "<!-- GENERATED by ops/atlas/workflow_recovery.py render. DO NOT EDIT BY HAND. -->",
        "# ATLAS workflow architecture and recovery",
        "",
        f"Canonical manifest: `{MANIFEST_REF}`",
        f"Manifest digest: `{manifest_digest}`",
        f"Runtime seed: `{REGISTRY_REF}`",
        "",
        "This view is generated from the versioned manifest. Stable logical role IDs are the contract; Codex thread IDs are replaceable runtime epochs refreshed in the live registry.",
        "",
        "## Authority and safety",
        "",
        f"- Authority sink: `{manifest['authority']['authority_sink']}`.",
        f"- Recovery owner: `{manifest['authority']['architecture_owner']}`.",
        "- Default recovery is dry-run and no-archive.",
        "- A live apply needs an independent ATLAS MAIN acceptance bound to both manifest and plan digests.",
        "- Active tasks are never steered or interrupted; duplicate writers, unknown identity, and incomplete pin/readback proof fail closed.",
        "",
        "## Standing role catalog",
        "",
        "| Logical role | Human title | Purpose | Writer scope | Creation | Runtime floor | Current epoch | Health seed |",
        "|---|---|---|---|---|---|---|---|",
    ]
    for role in manifest["roles"]:
        binding = bindings[role["role_id"]]
        scope = role["writer_scope"] or "read-only"
        runtime = role["runtime"]
        epoch = binding["current_runtime_id"] or "MISSING"
        purpose = role["purpose"].replace("|", "\\|")
        lines.append(
            f"| `{role['role_id']}` | {role['human_title']} | {purpose} | `{scope}` | "
            f"`{role['creation_policy']}` | `{runtime['model']}/{runtime['effort_floor']}` | "
            f"`{epoch}` | `{binding['health']}` |"
        )

    lines.extend([
        "",
        "## Preserved unbound runtime claims",
        "",
        "These live or historical runtimes used standing-task prose but lack a current durable logical-role admission. They are inventoried so recovery cannot silently recreate, discard, or lifecycle-mutate them.",
        "",
        "| Runtime | Title | Disposition | Canonical target | Health | Recovery action |",
        "|---|---|---|---|---|---|",
    ])
    for claim in registry["unbound_runtime_claims"]:
        target = claim["canonical_target_id"] or "UNBOUND"
        lines.append(
            f"| `{claim['runtime_id']}` | {claim['title']} | `{claim['disposition']}` | "
            f"`{target}` | `{claim['health']}` | `{claim['recovery_action']}` |"
        )

    lines.extend([
        "",
        "## Manual decision ledger",
        "",
        "Answered questions are suppressed from repetition. Transport acceptance does not imply execution authority or completion.",
        "",
        "| Question | Project | Status | Inbox transport | Main route | Execution |",
        "|---|---|---|---|---|---|",
    ])
    for decision in decisions["questions"]:
        lines.append(
            f"| `{decision['question_id']}` | {decision['project']} | `{decision['status']}` | "
            f"`{decision['transport_state']}` | `{decision['atlas_main_route_state']}` | "
            f"`{decision['execution_state']}` |"
        )

    lines.extend(["", "## Boot order", ""])
    for phase in manifest["boot"]["phases"]:
        members = ", ".join(f"`{item}`" for item in phase["members"])
        lines.append(
            f"{phase['phase']}. **{phase['mode'].upper()}** — {members}. Gate: {phase['success_gate']}"
        )
    lines.extend(["", "Serialization rules:", ""])
    lines.extend(f"- {item}" for item in manifest["boot"]["serialization_rules"])

    lines.extend([
        "",
        "## Lifecycle state machines",
        "",
    ])
    for name in ("standing", "bounded"):
        machine = manifest["lifecycle_state_machines"][name]
        lines.extend([f"### {name.title()}", "", "States: " + " -> ".join(f"`{item}`" for item in machine["states"]), ""])
        lines.append("| From | To | Gate |")
        lines.append("|---|---|---|")
        for transition in machine["transitions"]:
            lines.append(f"| `{transition['from']}` | `{transition['to']}` | {transition['gate']} |")
        lines.append("")

    lines.extend([
        "## Topology",
        "",
        "Every edge below is a logical contract. The sender resolves the current runtime ID at send time.",
        "",
        "| Type | From | To | Contract |",
        "|---|---|---|---|",
    ])
    for edge in manifest["edges"]:
        contract = edge["contract"].replace("|", "\\|")
        lines.append(f"| `{edge['type']}` | `{edge['from']}` | `{edge['to']}` | {contract} |")

    lines.extend([
        "",
        "## Embedded and non-standing components",
        "",
        "| Component | Kind | Standing task? | Recovery rule |",
        "|---|---|---|---|",
    ])
    for component in manifest["components"]:
        recovery = component["recovery"].replace("|", "\\|")
        lines.append(
            f"| `{component['component_id']}` | `{component['kind']}` | "
            f"`{str(component['standing_task']).lower()}` | {recovery} |"
        )

    lines.extend([
        "",
        "## One-command recovery",
        "",
        "From the ATLAS root:",
        "",
        "```powershell",
        "python ops/atlas/workflow_recovery.py recover --dry-run --adapter live",
        "```",
        "",
        "The command validates the manifest/schemas/prompts, discovers non-archived and archived tasks, reconciles by stable role ID, detects duplicate/active-writer collisions, emits a deterministic plan digest, refreshes only `runtime/atlas/workflow-recovery/`, and performs no archive or task mutation in dry-run mode.",
        "",
        "A role whose manifest locator is not `ATLAS_ROOT` can be created or bootstrapped only when the operator supplies an explicit absolute admitted worktree through a repeated `--cwd-binding LOCATOR=ABSOLUTE_PATH` argument. Missing, relative, duplicate, nonexistent, recovery-root, or changed bindings fail closed. The resolved cwd is included in plan identity. Creation sends one canonical modern named profile (`:read-only`, `:workspace`, or `:danger-full-access`) through `permissions`, rejects legacy sandbox tokens, and omits `sandbox`; bootstrap reuses the same accepted cwd.",
        "",
        "Optional `--desktop-observation <receipt.json> --desktop-observation-current <head.json>` inputs supply a complete, fresh, content-addressed activity snapshot plus the trusted current immutable head produced by a supported external task/thread readback ledger on the v1 `local` host. Each newer head cumulatively names prior receipt IDs in `supersedes_observation_ids`, so an older candidate is rejected without mutating its identity. Observation is dry-run only and can replace only `active`, `idle`, `notLoaded`, or `UNKNOWN` activity provenance on a runtime already returned by primary discovery. Pin state remains exactly `UNKNOWN` with capability `UNSUPPORTED`; private desktop storage, SQLite coupling, UI scraping, and pin inference are prohibited. Receipt/head identity, host, and timestamps are reported but excluded from plan identity; their validated activity effects remain digest-bound.",
        "",
        "A live apply additionally requires `--apply --acceptance <receipt.json>`. The receipt must bind the exact manifest and plan digests and name `atlas.main` as accepter. The current Codex app-server protocol does not expose pin readback or pin mutation, so any role needing pin proof fails closed before creation or repair. `ATLAS-WORKFLOW-MAN-001` rejected a manual fallback: the observation bridge can prove supported activity evidence, but live recovery remains blocked until deterministic pin readback and mutation exist.",
        "",
        "Creation binds its accepted runtime policy through `thread/start`; the supported app-server contract exposes no mutation for repairing a missing policy on an existing runtime, so that case fails preflight. Live apply must use the canonical runtime output directory. Immediately after `CREATE`, the exact runtime ID is atomically retained in a content-addressed creation journal before any later action can run. A fresh process validates and loads that binding before planning: it reuses the exact ID when discovery returns it and blocks without another create when discovery does not. A successful apply keeps the accepted plan immutable and carries the read-back runtime ID through a separate post-apply binding map into a content-addressed post-apply plan and the live registry. The terminal receipt binds the accepted plan, post-apply plan, and journal event/digest. Terminal health comes from the post-apply plan. If the bound runtime is absent from complete readback, registry generation fails closed.",
        "",
        "Fixture-safe creation proof:",
        "",
        "```powershell",
        "python ops/atlas/workflow_recovery.py recover --apply --adapter fixture --fixture tests/fixtures/atlas-workflow-recovery/missing-task.json --acceptance tests/fixtures/atlas-workflow-recovery/fixture-acceptance.json --output-dir runtime/atlas/workflow-recovery-fixture --deterministic",
        "```",
        "",
        "## Cold start and rollover summary",
        "",
        "1. Restore ATLAS and `_stack`; validate Git identity, manifest, schemas, prompts, leases, and live discovery.",
        "2. Recover/reuse ATLAS MAIN first. Do not create downstream roles until Main is unique and accepted.",
        "3. Recover queue surfaces in parallel, then owner/control surfaces by non-overlapping writer scope.",
        "4. For a rollover, persist a related epoch, bootstrap the successor with a stable event ID, prove routes/readback, obtain ATLAS MAIN acceptance, then and only then make the predecessor archive-eligible.",
        "5. On partial create, atomically journal the created ID before the next action, stop, and retry by logical role. A fresh process must load the journal and either reuse the exact ID or block; never delete it as rollback and never create a replacement while its identity is unresolved.",
        "6. On crash, re-run dry-run. Idempotence derives from role IDs, event IDs, payload digests, and retained runtime IDs—not from chat recollection.",
        "",
        "## Current archive-readiness truth",
        "",
        "`NOT PROVEN`. The durable contract, fixture recovery, and live dry-run can be proven locally, but live pin readback/mutation and independent recovery acceptance remain required before standing-task archival is safe.",
        "",
    ])
    return "\n".join(lines)


def _write_runtime_artifacts(
    output_dir: Path,
    accepted_plan: dict[str, Any],
    runtime_registry: dict[str, Any],
    mutation_receipts: list[dict[str, Any]],
    post_apply_plan: dict[str, Any] | None = None,
    creation_journal_receipt: dict[str, Any] | None = None,
) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "plan.json").write_bytes(_pretty_bytes(accepted_plan))
    if post_apply_plan is not None:
        (output_dir / "post-apply-plan.json").write_bytes(_pretty_bytes(post_apply_plan))
    (output_dir / "live-registry.json").write_bytes(_pretty_bytes(runtime_registry))
    terminal_plan = post_apply_plan or accepted_plan
    receipt = {
        "schema": "atlas.workflow.recovery-receipt.v1",
        "event_id": accepted_plan["plan_id"],
        "payload_digest": accepted_plan["plan_digest"],
        "manifest_digest": accepted_plan["manifest_digest"],
        "mode": accepted_plan["mode"],
        "no_archive": True,
        "terminal_status": terminal_plan["terminal_status"],
        "summary": terminal_plan["summary"],
        "accepted_plan_id": accepted_plan["plan_id"],
        "accepted_plan_digest": accepted_plan["plan_digest"],
        "post_apply_plan_id": post_apply_plan["plan_id"] if post_apply_plan else None,
        "post_apply_plan_digest": post_apply_plan["plan_digest"] if post_apply_plan else None,
        "creation_journal": creation_journal_receipt,
        "mutations": mutation_receipts,
    }
    (output_dir / "RECEIPT.json").write_bytes(_pretty_bytes(receipt))


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Deterministic ATLAS workflow recovery planner")
    subparsers = parser.add_subparsers(dest="command", required=True)

    recover = subparsers.add_parser("recover", help="discover, plan, and optionally apply recovery")
    mode = recover.add_mutually_exclusive_group()
    mode.add_argument("--dry-run", action="store_true", help="plan only (default)")
    mode.add_argument("--apply", action="store_true", help="apply an independently accepted plan")
    recover.add_argument("--adapter", choices=("live", "fixture"), default="live")
    recover.add_argument("--fixture", type=Path)
    recover.add_argument("--desktop-observation", type=Path)
    recover.add_argument("--desktop-observation-current", type=Path)
    recover.add_argument("--acceptance", type=Path)
    recover.add_argument("--output-dir", type=Path, default=Path(DEFAULT_RUNTIME_REF))
    recover.add_argument("--no-write-runtime", action="store_true")
    recover.add_argument("--deterministic", action="store_true")
    recover.add_argument("--json", action="store_true", help="print full plan JSON")
    recover.add_argument("--timeout-seconds", type=float, default=25.0)
    recover.add_argument(
        "--cwd-binding",
        action="append",
        default=[],
        metavar="LOCATOR=ABSOLUTE_PATH",
        help="bind a non-root manifest cwd locator to one admitted absolute worktree; repeat as needed",
    )

    validate = subparsers.add_parser("validate", help="validate schemas, manifest, prompts, registry, and generated view")
    validate.add_argument("--json", action="store_true")

    render = subparsers.add_parser("render", help="regenerate the human-readable view from the manifest")
    render.add_argument("--check", action="store_true", help="fail if the generated view would change")

    envelope = subparsers.add_parser(
        "validate-envelope",
        help="validate one workflow envelope and its canonical payload digest",
    )
    envelope.add_argument("path", type=Path)

    observation = subparsers.add_parser(
        "validate-desktop-observation",
        help="validate one complete externally produced task/thread activity observation",
    )
    observation.add_argument("path", type=Path)
    observation.add_argument("--current", type=Path, required=True)

    return parser.parse_args(argv)


def _parse_cwd_bindings(values: list[str]) -> dict[str, Path]:
    bindings: dict[str, Path] = {}
    paths: dict[Path, str] = {}
    for value in values:
        locator, separator, raw_path = value.partition("=")
        locator = locator.strip()
        raw_path = raw_path.strip()
        if not separator or not locator or not raw_path:
            raise ValidationFailure(
                "--cwd-binding must use LOCATOR=ABSOLUTE_PATH with both values present"
            )
        if locator == "ATLAS_ROOT":
            raise ValidationFailure("ATLAS_ROOT is reserved and resolves to the recovery checkout")
        if locator in bindings:
            raise ValidationFailure(f"duplicate --cwd-binding for {locator}")
        path = Path(raw_path)
        if not path.is_absolute():
            raise ValidationFailure(f"cwd binding for {locator} must be absolute: {raw_path}")
        try:
            resolved = path.resolve(strict=True)
        except OSError as exc:
            raise ValidationFailure(f"cwd binding for {locator} is not resolvable: {raw_path}") from exc
        if not resolved.is_dir():
            raise ValidationFailure(f"cwd binding for {locator} is not a directory: {resolved}")
        if resolved in paths:
            raise ValidationFailure(
                f"cwd bindings {paths[resolved]} and {locator} resolve to the same path: {resolved}"
            )
        bindings[locator] = resolved
        paths[resolved] = locator
    return bindings


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)
    creation_journal: CreationJournal | None = None
    try:
        if args.command == "render":
            manifest = _load_json(ROOT / MANIFEST_REF)
            registry = _load_json(ROOT / REGISTRY_REF)
            expected = render_markdown(manifest, registry, _sha256_file(ROOT / MANIFEST_REF))
            target = ROOT / GENERATED_VIEW_REF
            if args.check:
                actual = target.read_text(encoding="utf-8").replace("\r\n", "\n") if target.exists() else ""
                if actual != expected:
                    raise ValidationFailure(f"generated workflow view drift: {GENERATED_VIEW_REF}")
            else:
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_text(expected, encoding="utf-8", newline="\n")
            print(json.dumps({"status": "PASS", "generated": GENERATED_VIEW_REF, "check": args.check}, sort_keys=True))
            return 0

        if args.command == "validate":
            result = validate_repository()
            print(json.dumps(result, indent=2 if args.json else None, sort_keys=True))
            return 0

        if args.command == "validate-envelope":
            envelope_path = args.path if args.path.is_absolute() else ROOT / args.path
            result = validate_envelope(_load_json(envelope_path))
            print(json.dumps(result, sort_keys=True))
            return 0

        if args.command == "validate-desktop-observation":
            manifest = _load_json(ROOT / MANIFEST_REF)
            registry = _load_json(ROOT / REGISTRY_REF)
            observation_path = args.path if args.path.is_absolute() else ROOT / args.path
            current_path = args.current if args.current.is_absolute() else ROOT / args.current
            result = validate_desktop_observation(
                _load_json(observation_path),
                _load_json(current_path),
                manifest,
                registry,
            )
            print(json.dumps(result, sort_keys=True))
            return 0

        manifest = _load_json(ROOT / MANIFEST_REF)
        registry = _load_json(ROOT / REGISTRY_REF)
        validate_repository(check_generated=True)
        mode = "apply" if args.apply else "dry-run"
        if args.adapter == "fixture":
            if args.fixture is None:
                raise ValidationFailure("--fixture is required for the fixture adapter")
            if args.cwd_binding:
                raise ValidationFailure("--cwd-binding is valid only with --adapter live")
            fixture_path = args.fixture if args.fixture.is_absolute() else ROOT / args.fixture
            fixture = _load_json(fixture_path)
            adapter: DiscoveryAdapter = FixtureAdapter(manifest, registry, fixture)
        else:
            if args.fixture is not None:
                raise ValidationFailure("--fixture is valid only with --adapter fixture")
            adapter = LiveAppServerAdapter(
                args.timeout_seconds,
                cwd_bindings=_parse_cwd_bindings(args.cwd_binding),
            )

        output_dir = args.output_dir if args.output_dir.is_absolute() else ROOT / args.output_dir
        if args.apply and args.adapter == "live" and args.no_write_runtime:
            raise ValidationFailure(
                "live apply requires durable runtime output; --no-write-runtime is fixture-only"
            )
        canonical_runtime_dir = (ROOT / DEFAULT_RUNTIME_REF).resolve()
        if (
            args.apply
            and args.adapter == "live"
            and output_dir.resolve() != canonical_runtime_dir
        ):
            raise ValidationFailure(
                "live apply must use the canonical runtime output directory "
                f"{DEFAULT_RUNTIME_REF} so creation-journal continuity cannot be bypassed"
            )
        creation_journal_path = output_dir / "creation-journal.json"
        if creation_journal_path.exists() or (args.apply and not args.no_write_runtime):
            creation_journal = CreationJournal(
                creation_journal_path,
                manifest,
                registry,
                _sha256_file(ROOT / MANIFEST_REF),
            )
            creation_journal.apply_to(adapter, registry)

        desktop_observation = None
        desktop_observation_current = None
        if args.desktop_observation is not None:
            observation_path = (
                args.desktop_observation
                if args.desktop_observation.is_absolute()
                else ROOT / args.desktop_observation
            )
            desktop_observation = _load_json(observation_path)
            if args.desktop_observation_current is None:
                raise ValidationFailure(
                    "--desktop-observation requires --desktop-observation-current from the trusted observation ledger"
                )
            current_observation_path = (
                args.desktop_observation_current
                if args.desktop_observation_current.is_absolute()
                else ROOT / args.desktop_observation_current
            )
            desktop_observation_current = _load_json(current_observation_path)
            if args.apply:
                raise ValidationFailure(
                    "--desktop-observation is a read-only dry-run input and cannot accompany --apply"
                )
        elif args.desktop_observation_current is not None:
            raise ValidationFailure(
                "--desktop-observation-current requires --desktop-observation"
            )

        plan, threads, _leases = build_recovery_plan(
            manifest,
            registry,
            adapter,
            mode=mode,
            deterministic=args.deterministic,
            desktop_observation=desktop_observation,
            desktop_observation_current=desktop_observation_current,
        )
        mutation_receipts: list[dict[str, Any]] = []
        post_apply_plan: dict[str, Any] | None = None
        if args.apply:
            if args.acceptance is None:
                raise ValidationFailure("--acceptance is required for apply")
            acceptance_path = args.acceptance if args.acceptance.is_absolute() else ROOT / args.acceptance
            _load_acceptance(
                acceptance_path,
                plan,
                allow_fixture_template=args.adapter == "fixture",
            )
            mutation_receipts = apply_plan(
                plan,
                manifest,
                adapter,
                creation_journal=creation_journal,
            )
            post_apply_plan, threads, _ = build_recovery_plan(
                manifest,
                registry,
                adapter,
                mode="dry-run",
                deterministic=args.deterministic,
            )
            if creation_journal is not None:
                creation_journal.confirm_readback(post_apply_plan, threads)

        registry_plan = post_apply_plan or plan
        runtime_registry = build_runtime_registry(
            manifest,
            registry,
            registry_plan,
            threads,
            runtime_id_overrides=adapter.binding_overrides if args.apply else None,
        )
        _assert_schema(runtime_registry, REGISTRY_SCHEMA_REF, "generated runtime registry")
        if not args.no_write_runtime:
            _write_runtime_artifacts(
                output_dir,
                plan,
                runtime_registry,
                mutation_receipts,
                post_apply_plan=post_apply_plan,
                creation_journal_receipt=(
                    creation_journal.receipt_summary()
                    if creation_journal is not None
                    else None
                ),
            )

        if args.json:
            print(json.dumps(plan, indent=2, ensure_ascii=False, sort_keys=True))
        else:
            terminal_plan = post_apply_plan or plan
            print(
                json.dumps(
                    {
                        "status": terminal_plan["terminal_status"],
                        "plan_id": plan["plan_id"],
                        "plan_digest": plan["plan_digest"],
                        "post_apply_plan_id": post_apply_plan["plan_id"] if post_apply_plan else None,
                        "post_apply_plan_digest": post_apply_plan["plan_digest"] if post_apply_plan else None,
                        "mode": plan["mode"],
                        "adapter": plan["adapter"],
                        "no_archive": True,
                        "summary": terminal_plan["summary"],
                        "mutations": len(mutation_receipts),
                    },
                    sort_keys=True,
                )
            )
        return 0
    except PartialCreateFailure as exc:
        print(
            json.dumps(
                {
                    "status": "PARTIAL_CREATE",
                    "error": str(exc),
                    "mutation_receipts": exc.mutation_receipts,
                    "creation_journal": creation_journal.receipt_summary() if creation_journal else None,
                    "rollback": "retain created runtime IDs; retry by logical role; do not delete",
                },
                sort_keys=True,
            ),
            file=sys.stderr,
        )
        return 4
    except (OSError, ValueError, ValidationFailure, WorkflowRecoveryError) as exc:
        print(json.dumps({"status": "BLOCKED", "error": str(exc)}, sort_keys=True), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
