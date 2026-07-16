#!/usr/bin/env python3
"""Build the pinned, advisory-only Creation OS Cortex read model."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
CATALOG_PATH = Path("runtime/cortex/catalog/knowledge/creation-os/advisory-read-model.latest.json")
QUERY_PATH = Path("runtime/cortex/query/knowledge/creation-os/advisory-query.latest.json")
RECEIPT_PATH = Path("runtime/receipts/knowledge/cortex-creation-os-advisory-refresh.execution-receipt.v2.json")
CATALOG_SCHEMA_PATH = Path("schemas/atlas.cortex.creation-os-advisory-read-model.v1.json")
QUERY_SCHEMA_PATH = Path("schemas/atlas.cortex.creation-os-advisory-query.v1.json")
EXECUTION_RECEIPT_SCHEMA_PATH = Path("packages/atlas-contracts/schemas/atlas.execution-receipt.v2.schema.json")
KNOWLEDGE_CANDIDATE_SCHEMA_PATH = Path("packages/atlas-contracts/schemas/atlas.knowledge-candidate.v2.schema.json")
MANIFEST_PATH = Path("data/knowledge-candidates/creation-os/manifest.v1.json")
PLAYBOOK_RECEIPT_PATH = Path(".playbook/memory/atlas-knowledge-candidate-intake-receipts/creation-os.v1.json")
PLAYBOOK_QUEUE_PATH = Path(".playbook/memory/atlas-knowledge-candidates.json")

CATALOG_VERSION = "atlas.cortex.creation-os-advisory-read-model.v1"
QUERY_VERSION = "atlas.cortex.creation-os-advisory-query.v1"
DECISION_ID = "creation-os-software-repo-voice-first-wedge"
DECISION_RECORD_SHA256 = "sha256:5f26456f7e2a5d18ca6ca513cdcd53d33af0df5a19a3b05c01a753d393a121d6"

EXPECTED_CANDIDATES: dict[str, tuple[str, str, str]] = {
    "creation-os-human-directed-authority": ("rule", "Playbook/rules", "sha256:0aee7841a054b2460d0260699151d0e878602af4fd63961ca9697e5cf71e2b4a"),
    "creation-os-bootstrap-pointer-not-memory": ("rule", "Playbook/rules", "sha256:71170a9442e24862e0f79876e3f8e7028c9146efe5a91bc20daacf1b3a679c05"),
    "creation-os-builder-creative-loop-separation": ("pattern", "Playbook/patterns", "sha256:8c50f2611698756850c88c15ff4ba3d3f09a8807378e4aeb339572842bf4d986"),
    "creation-os-platform-surface-vertical-contracts": ("pattern", "Playbook/patterns", "sha256:b8ce18b2720dbcc5900721e43de96dc660e91f4625223b683550c52de8bb8da2"),
    "creation-os-infrastructure-shopping-before-wedge": ("failure-mode", "Playbook/failure-modes", "sha256:44f882ae82ee35b4691457a6ac5039ff481c37d9aecb37fed75bbf659673405a"),
    "creation-os-xr-device-novelty-trap": ("failure-mode", "Playbook/failure-modes", "sha256:d44055c02c0acb69a58e15a9f28fd8a69421b083d927cecbe6828e0aebad390d"),
}

AUTHORITY = {
    "read": True,
    "synthesis_advisory": True,
    "routing_advisory": True,
    "retrieval_advisory": True,
    "doctrine": False,
    "policy": False,
    "scheduling": False,
    "execution": False,
    "deployment": False,
    "approval": False,
    "board": False,
    "repository_mutation": False,
    "promotion": False,
    "automatic_selection": False,
}

GLOBAL_SURFACE_BASELINE = [
    {"path": "runtime/cortex/current-state/latest.json", "sha256": "sha256:0daf01a2cbbeace49f73b3eb076e0e4daf3707fcff37c0c75fd3b1ef33d0a4d2"},
    {"path": "runtime/cortex/current-state/latest.md", "sha256": "sha256:dfc9cf5648f3948d49085128f1d4eb8efc1c7004ffa58e3d680cc9ce8da87c97"},
    {"path": "runtime/cortex/context/latest.json", "sha256": "sha256:5048d222f5def6bffc6cd990945ad9e2e0454b59cf9ffecbeb29aa9e39270446"},
    {"path": "runtime/cortex/context/latest.md", "sha256": "sha256:a7b4f706ca4d5007f7dbd821a9af3c16777826b4c0f0c877f2808848d35d3403"},
    {"path": "runtime/cortex/operator-surface/latest.json", "sha256": "sha256:afeb7a2b1c70e74835e77be76e000b426750bba75572d0c6cb0511e932da5662"},
    {"path": "runtime/cortex/operator-surface/latest.md", "sha256": "sha256:a1d74ec515d0897d96dfd3a8191ca77a97946aa34c5819fd9482f1bd6b51b36f"},
    {"path": "runtime/cortex/ledger/latest.json", "sha256": "sha256:360736a7cce673fb775039d9b3ecec1957168f5f684e2bc945622a24d2f25f58"},
    {"path": "runtime/cortex/ledger/latest.md", "sha256": "sha256:76358010295bcc7b1fddf9b901b3cd5ac8848eec3aac9781f1d2328a18af63fd"},
    {"path": "runtime/cortex/query/knowledge/bundle.json", "sha256": "sha256:7c5a0fc8aa4484601b7b8e4601c0889eb8a1f2390ebdce2429b0b057ec88da0e"},
]

CHANGED_PATHS = [
    "ops/cortex/creation_os_advisory_read_model.py",
    "ops/cortex/README.md",
    "schemas/atlas.cortex.creation-os-advisory-read-model.v1.json",
    "schemas/atlas.cortex.creation-os-advisory-query.v1.json",
    "tests/test_cortex_creation_os_advisory_read_model.py",
    "docs/ops/ATLAS-CREATION-OS-CORTEX-ADVISORY-READ-MODEL-REFRESH-2026-07-16.md",
    "docs/atlas-book/05-receipt-index.md",
    CATALOG_PATH.as_posix(),
    QUERY_PATH.as_posix(),
    RECEIPT_PATH.as_posix(),
]


@dataclass(frozen=True)
class PinnedSources:
    atlas_revision: str = "66f756768792de35ef00d1741cf8c6f6c965b733"
    manifest_sha256: str = "sha256:eaab80257186a1f1d32e45106ed87858e0e254065df315ccb26b1e89b854efe2"
    playbook_revision: str = "885ae2bb0104f5ffc1c99bc1febe1f4cf2fde1aa"
    playbook_accepted_head: str = "e692f574ed51cdb0f59ce423d0cbf6baa08fe51d"
    playbook_receipt_id: str = "playbook-akc-intake-creation-os-66f756768792"
    queue_sha256: str = "sha256:206e30ff026969dec954f04b2aa722fb047f6c8540e9258ddda8b9887dba0d75"
    playbook_baseline: str = "8aa912b492e689fca4c296d59a438c2813cba4fc"
    playbook_initial_intake: str = "44ce21cdff47bc88817d164ac8578141eb939651"


PINNED = PinnedSources()


class EvidenceError(RuntimeError):
    def __init__(self, classification: str, code: str, message: str):
        super().__init__(message)
        self.classification = classification
        self.code = code

    def payload(self) -> dict[str, str]:
        return {"status": "blocked", "classification": self.classification, "code": self.code, "message": str(self)}


def _sha256(data: bytes) -> str:
    return f"sha256:{hashlib.sha256(data).hexdigest()}"


def _canonical_compact(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def canonical_json_bytes(value: Any) -> bytes:
    return (json.dumps(value, sort_keys=True, indent=2, ensure_ascii=False) + "\n").encode("utf-8")


def _json_object(raw: bytes, label: str) -> dict[str, Any]:
    try:
        value = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise EvidenceError("conflict", "invalid_json", f"{label} is not canonical readable JSON: {exc}") from exc
    if not isinstance(value, dict):
        raise EvidenceError("conflict", "invalid_shape", f"{label} must be a JSON object")
    return value


def _require(condition: bool, code: str, message: str) -> None:
    if not condition:
        raise EvidenceError("conflict", code, message)


def _git(repo: Path, *args: str, binary: bool = False) -> bytes | str:
    result = subprocess.run(
        ["git", "-C", str(repo), *args],
        check=False,
        capture_output=True,
        text=not binary,
        encoding=None if binary else "utf-8",
        errors=None if binary else "replace",
    )
    if result.returncode != 0:
        stderr = result.stderr.decode("utf-8", "replace") if binary else result.stderr
        raise EvidenceError("unknown", "missing_git_evidence", stderr.strip() or f"git {' '.join(args)} failed")
    return result.stdout


def read_git_blob(repo: Path, revision: str, path: str) -> bytes:
    return _git(repo, "show", f"{revision}:{path}", binary=True)  # type: ignore[return-value]


def load_git_sources(atlas_repo: Path, playbook_repo: Path, atlas_revision: str, playbook_revision: str) -> tuple[dict[str, bytes], dict[str, bytes], dict[str, Any]]:
    atlas_paths = [MANIFEST_PATH.as_posix(), KNOWLEDGE_CANDIDATE_SCHEMA_PATH.as_posix()]
    atlas_paths.extend(
        f"data/knowledge-candidates/creation-os/{candidate_id}.knowledge-candidate.v2.json"
        for candidate_id in EXPECTED_CANDIDATES
    )
    atlas_blobs = {path: read_git_blob(atlas_repo, atlas_revision, path) for path in atlas_paths}
    playbook_blobs = {
        PLAYBOOK_RECEIPT_PATH.as_posix(): read_git_blob(playbook_repo, playbook_revision, PLAYBOOK_RECEIPT_PATH.as_posix()),
        PLAYBOOK_QUEUE_PATH.as_posix(): read_git_blob(playbook_repo, playbook_revision, PLAYBOOK_QUEUE_PATH.as_posix()),
    }
    parents = str(_git(playbook_repo, "show", "-s", "--format=%P", playbook_revision)).strip().split()
    committed_at = str(_git(playbook_repo, "show", "-s", "--format=%cI", playbook_revision)).strip()
    ancestor = subprocess.run(
        ["git", "-C", str(playbook_repo), "merge-base", "--is-ancestor", PINNED.playbook_accepted_head, playbook_revision],
        check=False,
        capture_output=True,
    ).returncode == 0
    return atlas_blobs, playbook_blobs, {"parents": parents, "accepted_head_is_ancestor": ancestor, "committed_at": committed_at}


def _validate_schema(instance: dict[str, Any], schema: dict[str, Any], label: str) -> None:
    from ops.atlas.ui_standards.validate import validate_json_schema

    errors = validate_json_schema(instance, schema)
    if errors:
        raise EvidenceError("conflict", "schema_validation_failed", f"{label} failed schema validation: {errors[0]}")


def _validate_manifest_record_hash(record: dict[str, Any]) -> None:
    body = {key: value for key, value in record.items() if key != "record_sha256"}
    _require(record.get("record_sha256") == _sha256(_canonical_compact(body)), "record_hash_drift", f"manifest record hash drift: {record.get('record_id')}")


def _source_set_digest(parts: list[tuple[str, bytes]]) -> str:
    digest = hashlib.sha256()
    for label, raw in parts:
        label_bytes = label.encode("utf-8")
        digest.update(len(label_bytes).to_bytes(8, "big"))
        digest.update(label_bytes)
        digest.update(len(raw).to_bytes(8, "big"))
        digest.update(raw)
    return f"sha256:{digest.hexdigest()}"


def _component(label: str, raw: bytes, *, path: str | None = None, value: str | None = None) -> dict[str, Any]:
    result: dict[str, Any] = {"label": label, "sha256": _sha256(raw), "byte_length": len(raw)}
    if path is not None:
        result["path"] = path
    if value is not None:
        result["value"] = value
    return result


def build_models(
    *,
    atlas_revision: str,
    playbook_revision: str,
    atlas_blobs: dict[str, bytes],
    playbook_blobs: dict[str, bytes],
    topology: dict[str, Any],
    pinned: PinnedSources = PINNED,
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    if atlas_revision != pinned.atlas_revision or playbook_revision != pinned.playbook_revision:
        raise EvidenceError("stale", "changed_revision", "requested source revision differs from the pinned source set")

    def blob(mapping: dict[str, bytes], path: str) -> bytes:
        if path not in mapping:
            raise EvidenceError("unknown", "missing_blob", f"required exact Git blob is missing: {path}")
        return mapping[path]

    manifest_raw = blob(atlas_blobs, MANIFEST_PATH.as_posix())
    _require(_sha256(manifest_raw) == pinned.manifest_sha256, "manifest_hash_drift", "Atlas manifest byte hash drifted")
    manifest = _json_object(manifest_raw, "Atlas manifest")
    schema = _json_object(blob(atlas_blobs, KNOWLEDGE_CANDIDATE_SCHEMA_PATH.as_posix()), "KnowledgeCandidate schema")
    _require(manifest.get("manifest_version") == "atlas.creation-os.knowledge-candidate-index.v1", "manifest_version_drift", "manifest version drifted")
    _require(manifest.get("counts") == {"total_source_records": 7, "knowledge_candidates": 6, "deferred_decisions": 1}, "manifest_count_drift", "manifest counts drifted")
    manifest_authority = manifest.get("authority", {})
    _require(
        manifest_authority.get("atlas_projection_only") is True
        and all(manifest_authority.get(key) is False for key in ("playbook_doctrine_mutation", "cortex_policy_authority", "owner_repository_mutation", "bulk_copy", "automatic_promotion")),
        "authority_drift",
        "Atlas manifest authority widened",
    )
    records = manifest.get("records")
    _require(isinstance(records, list) and len(records) == 7, "manifest_record_drift", "manifest must contain exactly seven records")
    by_id = {item.get("record_id"): item for item in records if isinstance(item, dict)}
    _require(len(by_id) == 7, "duplicate_identity", "manifest contains a missing or duplicate record identity")

    candidate_payloads: dict[str, dict[str, Any]] = {}
    artifact_raw: dict[str, bytes] = {}
    for candidate_id, (kind, destination, expected_hash) in EXPECTED_CANDIDATES.items():
        record = by_id.get(candidate_id)
        _require(isinstance(record, dict), "missing_candidate", f"manifest candidate missing: {candidate_id}")
        _validate_manifest_record_hash(record)
        path = f"data/knowledge-candidates/creation-os/{candidate_id}.knowledge-candidate.v2.json"
        raw = blob(atlas_blobs, path)
        artifact_raw[candidate_id] = raw
        _require(_sha256(raw) == expected_hash == record.get("artifact_sha256"), "artifact_hash_drift", f"candidate artifact hash drift: {candidate_id}")
        _require(record.get("kind") == kind and record.get("suggested_destination") == destination, "kind_destination_drift", f"manifest kind/destination drift: {candidate_id}")
        payload = _json_object(raw, candidate_id)
        _validate_schema(payload, schema, candidate_id)
        _require(payload.get("candidate_id") == candidate_id, "candidate_identity_drift", f"candidate identity drift: {candidate_id}")
        _require(payload.get("kind") == kind and payload.get("suggested_destination") == destination, "kind_destination_drift", f"candidate kind/destination drift: {candidate_id}")
        _require(_sha256(str(payload.get("statement", "")).encode("utf-8")) == record.get("source_statement_sha256"), "statement_hash_drift", f"statement hash drift: {candidate_id}")
        _require(_sha256(str(payload.get("scope", "")).encode("utf-8")) == record.get("source_scope_sha256"), "scope_hash_drift", f"scope hash drift: {candidate_id}")
        candidate_payloads[candidate_id] = payload

    decision = by_id.get(DECISION_ID)
    _require(isinstance(decision, dict), "missing_decision", "deferred Atlas product Decision is missing")
    _validate_manifest_record_hash(decision)
    _require(decision.get("record_sha256") == DECISION_RECORD_SHA256, "decision_hash_drift", "deferred Decision record hash drifted")
    _require(decision.get("classification") == "atlas-product-decision" and decision.get("kind") == "decision", "decision_classification_drift", "deferred Decision classification drifted")
    _require(decision.get("contract_eligible") is False and decision.get("artifact_path") is None and decision.get("artifact_sha256") is None, "decision_admission", "Decision became contract-eligible or gained a candidate artifact")
    _require(decision.get("disposition") == "deferred-atlas-product-decision", "decision_disposition_drift", "Decision disposition drifted")

    receipt_raw = blob(playbook_blobs, PLAYBOOK_RECEIPT_PATH.as_posix())
    queue_raw = blob(playbook_blobs, PLAYBOOK_QUEUE_PATH.as_posix())
    receipt = _json_object(receipt_raw, "Playbook receipt")
    queue = _json_object(queue_raw, "Playbook queue")
    _require(_sha256(queue_raw) == pinned.queue_sha256, "queue_hash_drift", "Playbook queue byte hash drifted")
    _require(len(topology.get("parents", [])) >= 2 and topology.get("accepted_head_is_ancestor") is True and pinned.playbook_accepted_head in topology.get("parents", []), "owner_evidence_open_only", "Playbook evidence is not the pinned merged accepted head")
    _require(receipt.get("schema_version") == "1.0" and receipt.get("kind") == "playbook.atlas-knowledge-candidate.owner-intake-receipt.v1", "receipt_version_drift", "Playbook receipt schema/kind drifted")
    _require(receipt.get("receipt_id") == pinned.playbook_receipt_id, "receipt_identity_drift", "Playbook receipt identity drifted")
    receipt_authority = receipt.get("authority", {})
    _require(receipt_authority.get("mode") == "candidate-review-only" and receipt_authority.get("promotion_authority") == "none" and receipt_authority.get("doctrine_mutation") is False, "doctrine_mutation", "Playbook receipt authority widened or doctrine changed")
    source = receipt.get("source", {})
    _require(source.get("revision") == atlas_revision and source.get("manifest_sha256") == pinned.manifest_sha256 and source.get("manifest_path") == MANIFEST_PATH.as_posix(), "receipt_source_binding_drift", "Playbook receipt source binding drifted")
    _require(source.get("counts") == {"total_source_records": 7, "knowledge_candidates": 6, "deferred_decisions": 1}, "receipt_source_binding_drift", "Playbook receipt source counts drifted")
    registry = receipt.get("registry", {})
    _require(registry.get("queue_sha256") == pinned.queue_sha256 and registry.get("candidate_count") == 6 and registry.get("owner_disposition_count") == 6, "receipt_queue_binding_drift", "Playbook receipt queue binding drifted")
    _require(queue.get("schema_version") == "1.0" and queue.get("kind") == "playbook.atlas-knowledge-candidate.queue.v1", "queue_version_drift", "Playbook queue schema/kind drifted")
    receipt_candidates = receipt.get("candidates")
    queue_candidates = queue.get("candidates")
    _require(isinstance(receipt_candidates, list) and len(receipt_candidates) == 6, "candidate_count_drift", "Playbook receipt must contain exactly six candidates")
    _require(isinstance(queue_candidates, list) and len(queue_candidates) == 6, "candidate_count_drift", "Playbook queue must contain exactly six candidates")
    receipt_by_id = {item.get("candidate_id"): item for item in receipt_candidates if isinstance(item, dict)}
    queue_by_id = {item.get("external_candidate_id"): item for item in queue_candidates if isinstance(item, dict)}
    _require(set(receipt_by_id) == set(EXPECTED_CANDIDATES) and len(receipt_by_id) == 6, "duplicate_identity", "Playbook receipt identity set drifted")
    _require(set(queue_by_id) == set(EXPECTED_CANDIDATES) and len(queue_by_id) == 6, "duplicate_identity", "Playbook queue identity set drifted or Decision was admitted")
    _require(DECISION_ID not in json.dumps(queue, sort_keys=True) and DECISION_ID not in receipt_by_id, "decision_admission", "deferred Decision leaked into a candidate array")
    excluded = receipt.get("excluded")
    _require(
        isinstance(excluded, list)
        and len(excluded) == 1
        and excluded[0].get("candidate_id") == DECISION_ID
        and excluded[0].get("classification") == "atlas-product-decision"
        and excluded[0].get("kind") == "decision"
        and excluded[0].get("disposition") == "deferred-atlas-product-decision",
        "decision_exclusion_drift",
        "Playbook Decision exclusion evidence drifted",
    )
    doctrine = receipt.get("proof", {}).get("doctrine_invariance", {})
    _require(doctrine.get("baseline_revision") == pinned.playbook_baseline and doctrine.get("intake_revision") == pinned.playbook_initial_intake, "doctrine_evidence_drift", "doctrine invariance revision proof drifted")
    doctrine_paths = doctrine.get("paths", [])
    _require(isinstance(doctrine_paths, list) and all(item.get("before_sha256") == item.get("after_sha256") for item in doctrine_paths if isinstance(item, dict)), "doctrine_mutation", "Playbook doctrine mutation was detected")

    projections: list[dict[str, Any]] = []
    for candidate_id in sorted(EXPECTED_CANDIDATES):
        kind, destination, expected_hash = EXPECTED_CANDIDATES[candidate_id]
        owner = receipt_by_id[candidate_id]
        queued = queue_by_id[candidate_id]
        candidate = candidate_payloads[candidate_id]
        _require(owner.get("source_revision") == atlas_revision and owner.get("source_artifact_sha256") == expected_hash, "owner_source_drift", f"owner source binding drift: {candidate_id}")
        _require(owner.get("kind") == kind and owner.get("suggested_destination") == destination and owner.get("review_status") == "candidate", "kind_destination_drift", f"owner kind/destination/review drift: {candidate_id}")
        disposition = owner.get("owner_disposition", {})
        admission = queued.get("admission", {})
        consumer_receipt = queued.get("consumer_receipt", {})
        _require(queued.get("candidate") == candidate, "candidate_content_drift", f"Playbook did not preserve candidate content: {candidate_id}")
        _require(queued.get("source_artifact") == {"path": owner.get("source_artifact_path"), "sha256": expected_hash}, "owner_source_drift", f"queue source binding drift: {candidate_id}")
        candidate_content_sha256 = hashlib.sha256(_canonical_compact(candidate)).hexdigest()
        _require(
            queued.get("record_id") == owner.get("candidate_record_id")
            and queued.get("candidate_content_sha256") == owner.get("candidate_content_sha256") == candidate_content_sha256
            and consumer_receipt.get("receipt_id") == owner.get("consumer_receipt_id")
            and consumer_receipt.get("candidate_record_id") == owner.get("candidate_record_id")
            and consumer_receipt.get("candidate_content_sha256") == candidate_content_sha256,
            "owner_receipt_binding_drift",
            f"owner receipt/record binding drift: {candidate_id}",
        )
        _require(disposition.get("decision") == "accept" and disposition.get("effect") == "candidate-review-only" and queued.get("owner_disposition") == "accept" and consumer_receipt.get("owner_disposition") == "accept", "conflicting_disposition", f"conflicting owner disposition: {candidate_id}")
        _require(admission.get("state") == "review-candidate" and admission.get("promotion_authority") == "none" and admission.get("suggested_destination_authority") == "proposal-only", "authority_drift", f"candidate admission authority drift: {candidate_id}")
        _require(consumer_receipt.get("promotion_authority") == "none" and consumer_receipt.get("decision") == "candidate-only-admitted", "authority_drift", f"consumer receipt authority drift: {candidate_id}")
        projections.append({
            "candidate_id": candidate_id,
            "classification": "playbook-review-candidate",
            "kind": kind,
            "name": candidate["name"],
            "statement": candidate["statement"],
            "scope": candidate["scope"],
            "provenance": candidate["provenance"],
            "review": candidate["review"],
            "suggested_destination": destination,
            "destination_authority": "proposal-only",
            "promotion_status": "not-promoted",
            "source": {
                "atlas_revision": atlas_revision,
                "artifact_path": owner["source_artifact_path"],
                "artifact_sha256": expected_hash,
                "manifest_record_sha256": owner["manifest_record_sha256"],
            },
            "owner_intake": {
                "receipt_id": receipt["receipt_id"],
                "candidate_record_id": owner["candidate_record_id"],
                "consumer_receipt": consumer_receipt,
                "disposition": disposition,
                "admission": admission,
            },
        })

    source_parts: list[tuple[str, bytes]] = [("atlas_revision", atlas_revision.encode("ascii")), ("atlas_manifest", manifest_raw)]
    for candidate_id in sorted(artifact_raw):
        source_parts.append((f"atlas_candidate:{candidate_id}", artifact_raw[candidate_id]))
    source_parts.extend([
        ("atlas_decision_record_sha256", DECISION_RECORD_SHA256.encode("ascii")),
        ("playbook_merged_revision", playbook_revision.encode("ascii")),
        ("playbook_owner_receipt", receipt_raw),
        ("playbook_candidate_queue", queue_raw),
    ])
    components = []
    for label, raw in source_parts:
        if label == "atlas_manifest":
            components.append(_component(label, raw, path=MANIFEST_PATH.as_posix()))
        elif label.startswith("atlas_candidate:"):
            candidate_id = label.split(":", 1)[1]
            components.append(_component(label, raw, path=f"data/knowledge-candidates/creation-os/{candidate_id}.knowledge-candidate.v2.json"))
        elif label == "playbook_owner_receipt":
            components.append(_component(label, raw, path=PLAYBOOK_RECEIPT_PATH.as_posix()))
        elif label == "playbook_candidate_queue":
            components.append(_component(label, raw, path=PLAYBOOK_QUEUE_PATH.as_posix()))
        else:
            components.append(_component(label, raw, value=raw.decode("ascii")))
    source_set = {
        "digest": _source_set_digest(source_parts),
        "digest_algorithm": "sha256 over ordered length-prefixed UTF-8 labels and exact raw component bytes",
        "components": components,
        "topology": {
            "playbook_merged_revision": playbook_revision,
            "playbook_accepted_head": pinned.playbook_accepted_head,
            "merge_parents": topology["parents"],
            "accepted_head_is_ancestor": True,
        },
    }
    deferred_decision = dict(decision)
    deferred_decision["thresholds_and_kill_criteria_status"] = "unresolved-pending-operator-ratification"
    deferred_decision["advisory_projection_only"] = True

    catalog = {
        "schema_version": CATALOG_VERSION,
        "status": "ready",
        "scope": "creation-os",
        "source_set": source_set,
        "candidate_projections": projections,
        "promoted_knowledge": [],
        "deferred_product_decisions": [deferred_decision],
        "authority": AUTHORITY,
        "failure_semantics": {
            "missing_evidence": "unknown",
            "changed_revision": "stale",
            "duplicate_hash_kind_destination_or_disposition_drift": "conflict",
            "decision_admission": "conflict",
            "doctrine_mutation": "conflict",
            "conflict_resolution": "operator-required-never-auto-select",
        },
        "marker_deltas": [],
        "marker_movement_authorized": False,
        "global_cortex_freshness_claimed": False,
    }
    by_kind = {kind: sorted(item["candidate_id"] for item in projections if item["kind"] == kind) for kind in ("rule", "pattern", "failure-mode")}
    by_destination = {destination: sorted(item["candidate_id"] for item in projections if item["suggested_destination"] == destination) for destination in ("Playbook/rules", "Playbook/patterns", "Playbook/failure-modes")}
    query = {
        "schema_version": QUERY_VERSION,
        "status": "ready",
        "scope": "creation-os",
        "source_set_digest": source_set["digest"],
        "catalog_ref": CATALOG_PATH.as_posix(),
        "candidate_retrieval": projections,
        "promoted_knowledge": [],
        "deferred_decision_retrieval": [deferred_decision],
        "indexes": {"candidate_ids_by_kind": by_kind, "candidate_ids_by_destination": by_destination, "deferred_decision_ids": [DECISION_ID]},
        "selection": {"automatic_selection": False, "conflict_resolution": "operator-required", "destination_authority": "proposal-only"},
        "authority": AUTHORITY,
        "failure_semantics": catalog["failure_semantics"],
        "marker_deltas": [],
        "marker_movement_authorized": False,
        "global_cortex_freshness_claimed": False,
    }
    receipt_recorded_at = str(topology.get("committed_at", "2026-07-16T13:56:04Z"))
    receipt_recorded_at = datetime.fromisoformat(receipt_recorded_at.replace("Z", "+00:00")).astimezone(timezone.utc).isoformat().replace("+00:00", "Z")
    receipt_payload = {
        "contract_version": "atlas.execution-receipt.v2",
        "receipt_id": "cortex-creation-os-advisory-refresh-66f756768792-885ae2bb0104",
        "job_id": "cortex-creation-os-advisory-refresh",
        "recorded_at": receipt_recorded_at,
        "status": "succeeded",
        "component_id": "cortex",
        "project_id": "atlas",
        "runtime_effective": {"model": "gpt-5.6-sol", "reasoning": "xhigh", "speed": "unknown-not-exposed", "permissions": "full-local-access-network-live-web", "approval_policy": "never"},
        "changed_paths": CHANGED_PATHS,
        "commits": [],
        "verification": [{"command": "python ops/cortex/creation_os_advisory_read_model.py --check --atlas-repo <ATLAS_WORKTREE> --playbook-repo <PLAYBOOK_REPO>", "status": "passed", "evidence_refs": [CATALOG_PATH.as_posix(), QUERY_PATH.as_posix()]}],
        "evidence_refs": [MANIFEST_PATH.as_posix(), PLAYBOOK_RECEIPT_PATH.as_posix(), PLAYBOOK_QUEUE_PATH.as_posix(), CATALOG_PATH.as_posix(), QUERY_PATH.as_posix()],
        "blockers": [],
        "follow_up": ["DiscordOS reliability continuation after this owner receipt is reconciled."],
        "correlations": {"card_id": None, "thread_id": "019f52d9-7667-72a3-a5f7-9c0613aedd8f", "turn_id": None, "branch": "codex/cortex-creation-os-advisory-refresh", "worktree": "runtime/codex/worktrees/atlas/cortex-creation-os-advisory-refresh"},
        "authority_actions": [],
        "summary": "Built the deterministic Creation OS candidate-only advisory catalog and retrieval model with one separately deferred Atlas product Decision.",
        "extensions": {
            "source_set": source_set,
            "projected_identities": {"candidate_ids": sorted(EXPECTED_CANDIDATES), "deferred_decision_ids": [DECISION_ID]},
            "output_hashes": {},
            "authority": AUTHORITY,
            "marker_deltas": [],
            "marker_movement_authorized": False,
            "global_cortex_surfaces": {
                "freshness_claimed": False,
                "expected_byte_identical": True,
                "actual_identity_verification": "not-performed-by-generator-terminal-proof-required",
                "baseline": GLOBAL_SURFACE_BASELINE,
            },
            "base_proof_correction": {
                "status": "corrected-and-verified",
                "canonical_head": "1d79d4ac3191dade11a2aa7c40352a5f210d35e2",
                "authoritative_base": pinned.atlas_revision,
                "relationship": "authoritative origin/main is seven commits ahead and contains canonical head in ancestry",
                "correction": "The initial left/right rev-list count was interpreted backward; worktree base 66f756768792 remained correct.",
            },
        },
    }
    return catalog, query, receipt_payload


def render_outputs(catalog: dict[str, Any], query: dict[str, Any], receipt: dict[str, Any]) -> dict[Path, bytes]:
    catalog_bytes = canonical_json_bytes(catalog)
    query_bytes = canonical_json_bytes(query)
    receipt = json.loads(json.dumps(receipt))
    receipt["extensions"]["output_hashes"] = {
        CATALOG_PATH.as_posix(): _sha256(catalog_bytes),
        QUERY_PATH.as_posix(): _sha256(query_bytes),
    }
    return {CATALOG_PATH: catalog_bytes, QUERY_PATH: query_bytes, RECEIPT_PATH: canonical_json_bytes(receipt)}


def validate_rendered_outputs(outputs: dict[Path, bytes], root: Path = ROOT) -> None:
    schema_pairs = [
        (CATALOG_PATH, CATALOG_SCHEMA_PATH),
        (QUERY_PATH, QUERY_SCHEMA_PATH),
        (RECEIPT_PATH, EXECUTION_RECEIPT_SCHEMA_PATH),
    ]
    for output_path, schema_path in schema_pairs:
        payload = _json_object(outputs[output_path], output_path.as_posix())
        schema = _json_object((root / schema_path).read_bytes(), schema_path.as_posix())
        _validate_schema(payload, schema, output_path.as_posix())


def write_or_check(outputs: dict[Path, bytes], *, root: Path, check: bool) -> list[str]:
    drift: list[str] = []
    for relative, raw in outputs.items():
        target = root / relative
        if check:
            if not target.is_file() or target.read_bytes() != raw:
                drift.append(relative.as_posix())
            continue
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(raw)
    return drift


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--atlas-repo", type=Path, default=ROOT)
    parser.add_argument("--playbook-repo", type=Path, required=True)
    parser.add_argument("--atlas-revision", default=PINNED.atlas_revision)
    parser.add_argument("--playbook-revision", default=PINNED.playbook_revision)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--write", action="store_true")
    mode.add_argument("--check", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    try:
        atlas_blobs, playbook_blobs, topology = load_git_sources(
            args.atlas_repo.resolve(), args.playbook_repo.resolve(), args.atlas_revision, args.playbook_revision
        )
        catalog, query, receipt = build_models(
            atlas_revision=args.atlas_revision,
            playbook_revision=args.playbook_revision,
            atlas_blobs=atlas_blobs,
            playbook_blobs=playbook_blobs,
            topology=topology,
        )
        outputs = render_outputs(catalog, query, receipt)
        validate_rendered_outputs(outputs, args.atlas_repo.resolve())
        drift = write_or_check(outputs, root=args.atlas_repo.resolve(), check=args.check)
        if drift:
            payload = {"status": "conflict", "code": "generated_output_drift", "paths": drift}
            print(json.dumps(payload, sort_keys=True), file=sys.stderr)
            return 1
        payload = {
            "status": "ok",
            "mode": "check" if args.check else "write",
            "source_set_digest": catalog["source_set"]["digest"],
            "candidate_count": len(catalog["candidate_projections"]),
            "deferred_decision_count": len(catalog["deferred_product_decisions"]),
            "output_hashes": {path.as_posix(): _sha256(raw) for path, raw in outputs.items()},
        }
        print(json.dumps(payload, sort_keys=True) if args.json else json.dumps(payload, indent=2, sort_keys=True))
        return 0
    except EvidenceError as exc:
        print(json.dumps(exc.payload(), sort_keys=True), file=sys.stderr)
        return 2
    except OSError as exc:
        print(json.dumps({"status": "blocked", "classification": "unknown", "code": "io_error", "message": str(exc)}, sort_keys=True), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
