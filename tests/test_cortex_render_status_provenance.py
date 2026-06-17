from __future__ import annotations

from contextlib import ExitStack
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from ops.cortex.render_status import (
    attention_queue,
    blocked_workers,
    classify_merge_requests,
    closure_receipts,
    conversation_summary,
    legacy_compatibility_surfaces,
    open_merge_requests,
    proposal_only_state,
    provenance_alert_summary,
    provenance_attention_items,
    render_status_payload,
    trust_posture_summary,
    trust_surfaces,
)


def _conversation_descriptor(
    *,
    turn_id: str,
    action_mode: str,
    intent: str = "propose_change",
    conversation_id: str = "conversation-1",
    source_ref: str = "runtime/atlas/conversations/conversation-1/turns/turn.json",
) -> dict[str, object]:
    return {
        "artifact_type": "conversation_turn",
        "source_ref": source_ref,
        "identity": {
            "conversation_id": conversation_id,
            "turn_id": turn_id,
        },
        "state": {
            "action_mode": action_mode,
            "intent": intent,
        },
    }


def _conversation_manifest_descriptor(
    *,
    conversation_id: str = "conversation-1",
    mode: str = "governed",
    status: str = "active",
    turn_count: int = 3,
    updated_at: str = "2026-06-17T12:00:00Z",
    last_turn_at: str = "2026-06-17T11:59:00Z",
    recent_turn_refs: list[str] | None = None,
    active_initiative_refs: list[str] | None = None,
    active_session_refs: list[str] | None = None,
    source_ref: str | None = None,
) -> dict[str, object]:
    return {
        "artifact_type": "conversation_manifest",
        "source_ref": source_ref
        or f"runtime/atlas/conversations/{conversation_id}/conversation.manifest.json",
        "identity": {
            "conversation_id": conversation_id,
            "mode": mode,
        },
        "state": {
            "status": status,
            "turn_count": turn_count,
            "updated_at": updated_at,
            "last_turn_at": last_turn_at,
        },
        "links": {
            "recent_turn_refs": recent_turn_refs
            or [f"runtime/atlas/conversations/{conversation_id}/turns/turn-1.json"],
            "active_initiative_refs": active_initiative_refs or [],
            "active_session_refs": active_session_refs or [],
        },
    }


def _knowledge_catalog_descriptor(
    *,
    archive_id: str,
    trust_class: str,
    source_ref: str,
    indexing_profile: str = "metadata_only",
    promotion_status: str = "quarantined",
) -> dict[str, object]:
    return {
        "artifact_type": "knowledge_catalog",
        "source_ref": source_ref,
        "identity": {
            "archive_id": archive_id,
        },
        "trust_class": trust_class,
        "state": {
            "indexing_profile": indexing_profile,
            "promotion_status": promotion_status,
        },
    }


def _worker_status_descriptor(
    *,
    worker_id: str,
    worker_state: str,
    heartbeat_at: str,
    assignment_id: str | None = None,
    tool_id: str | None = None,
    extension_id: str | None = None,
    blocked_reason: str | None = None,
    registry_digest: str = "registry-digest-1",
    source_ref: str | None = None,
) -> dict[str, object]:
    worker_suffix = worker_id.replace("worker-", "")
    return {
        "artifact_type": "worker_status",
        "source_ref": source_ref or f"runtime/atlas/workers/{worker_id}/status.json",
        "identity": {
            "worker_id": worker_id,
            "assignment_id": assignment_id or f"assignment-{worker_suffix}",
            "tool_id": tool_id or f"tool-{worker_id}",
            "extension_id": extension_id or f"extension-{worker_id}",
        },
        "state": {
            "worker_state": worker_state,
            "heartbeat_at": heartbeat_at,
            "blocked_reason": blocked_reason,
            "registry_digest": registry_digest,
        },
    }


def _legacy_runtime_backfill_descriptor(
    *,
    session_id: str,
    source_ref: str,
    original_session_ref: str | None = None,
    compatibility_class: str = "legacy_pre_registry",
    cutover_at: str | None = "2026-06-17T00:00:00Z",
    observed_at: str | None = "2026-06-17T00:01:00Z",
    recorded_at: str | None = "2026-06-17T00:02:00Z",
    missing_governed_requirements: list[str] | None = None,
    governed_identity: dict[str, object] | None = None,
) -> dict[str, object]:
    return {
        "artifact_type": "legacy_runtime_backfill",
        "source_ref": source_ref,
        "identity": {
            "session_id": session_id,
        },
        "state": {
            "compatibility_class": compatibility_class,
            "cutover_at": cutover_at,
            "observed_at": observed_at,
            "recorded_at": recorded_at,
        },
        "links": {
            "original_session_ref": original_session_ref
            or f"runtime/atlas/sessions/{session_id}/original.manifest.json",
            "missing_governed_requirements": missing_governed_requirements or ["tool_id"],
            "governed_identity": governed_identity or {"tool_id": f"tool-{session_id}"},
        },
    }


def _merge_request_descriptor(
    *,
    merge_request_id: str,
    source_ref: str,
    lineage_key: str | None = None,
    conflict_key: str | None = None,
    tool_id: str | None = None,
    extension_id: str | None = None,
    registry_digest: str = "registry-digest-1",
    conflicting_workers: list[str] | None = None,
) -> dict[str, object]:
    return {
        "artifact_type": "merge_request",
        "source_ref": source_ref,
        "identity": {
            "merge_request_id": merge_request_id,
            "lineage_key": lineage_key,
            "conflict_key": conflict_key or lineage_key or f"conflict-{merge_request_id}",
            "tool_id": tool_id or f"tool-{merge_request_id}",
            "extension_id": extension_id or f"extension-{merge_request_id}",
        },
        "state": {
            "registry_digest": registry_digest,
        },
        "links": {
            "conflicting_workers": conflicting_workers or [],
        },
    }


def _merge_completion_descriptor(
    *,
    merge_request_id: str,
    source_ref: str | None = None,
) -> dict[str, object]:
    return {
        "artifact_type": "supervisor_merge_completion",
        "source_ref": source_ref or f"runtime/atlas/merge-completions/{merge_request_id}.json",
        "identity": {
            "merge_request_id": merge_request_id,
        },
    }


def _session_manifest_descriptor(
    *,
    session_id: str = "session-1",
    merge_request_refs: list[str] | None = None,
    close_receipt_refs: list[str] | None = None,
    source_ref: str = "runtime/atlas/sessions/session-1/session.manifest.json",
) -> dict[str, object]:
    return {
        "artifact_type": "session_manifest",
        "source_ref": source_ref,
        "identity": {
            "session_id": session_id,
            "task_id": f"task-{session_id}",
        },
        "state": {
            "session_state": "running",
        },
        "links": {
            "merge_request_refs": merge_request_refs or [],
            "close_receipt_refs": close_receipt_refs or [],
        },
    }


def _execution_receipt_descriptor(
    *,
    receipt_id: str,
    source_ref: str,
    result: str = "succeeded",
    tool_id: str | None = None,
    extension_id: str | None = None,
    registry_digest: str = "registry-digest-1",
    supersedes_receipt_ref: str | None = None,
    reconciled_at: str = "2026-06-16T12:00:00Z",
    executed_at: str = "2026-06-16T11:59:00Z",
    reconciled_by_tool_version: str = "tool-version-1",
    repair_basis_refs: list[str] | None = None,
) -> dict[str, object]:
    return {
        "artifact_type": "execution_receipt",
        "source_ref": source_ref,
        "identity": {
            "receipt_id": receipt_id,
            "tool_id": tool_id or f"tool-{receipt_id}",
            "extension_id": extension_id or f"extension-{receipt_id}",
        },
        "state": {
            "result": result,
            "registry_digest": registry_digest,
            "reconciled_at": reconciled_at,
            "executed_at": executed_at,
            "reconciled_by_tool_version": reconciled_by_tool_version,
        },
        "links": {
            "supersedes_receipt_ref": supersedes_receipt_ref,
            "repair_basis_refs": repair_basis_refs or [],
        },
    }


class RenderStatusProvenanceTests(unittest.TestCase):
    def test_render_status_payload_routes_provenance_summary_into_attention_queue(self) -> None:
        provenance_summary = {
            "status": "drift_detected",
            "initiative_item_count": 1,
            "proposal_item_count": 0,
            "item_count": 1,
            "items": [
                {
                    "kind": "initiative_provenance_drift",
                    "initiative_id": "initiative-proof",
                    "title": "Proof",
                    "source_ref": "docs/memory/initiatives/initiative-proof.json",
                    "stale_attention_refs": ["attention:sha256:stale"],
                    "missing_file_refs": [],
                }
            ],
        }

        with TemporaryDirectory() as temp_dir:
            descriptor_root = Path(temp_dir)
            (descriptor_root / "placeholder.json").write_text("{}", encoding="utf-8")
            patch_specs = [
                ("ops.cortex.render_status.load_descriptors", []),
                ("ops.cortex.render_status.load_registry_state", {"ok": True}),
                ("ops.cortex.render_status.choose_latest_session", None),
                ("ops.cortex.render_status.session_overview", None),
                ("ops.cortex.render_status.blocked_workers", []),
                ("ops.cortex.render_status.classify_merge_requests", ([], [])),
                ("ops.cortex.render_status.closure_receipts", []),
                ("ops.cortex.render_status.execution_receipt_residue_records", []),
                ("ops.cortex.render_status.governed_writes", []),
                ("ops.cortex.render_status.legacy_compatibility_surfaces", []),
                ("ops.cortex.render_status.trust_surfaces", []),
                ("ops.cortex.render_status.trust_posture_summary", {}),
                ("ops.cortex.render_status.working_memory_summary", {"_items": [], "initiatives": {}}),
                ("ops.cortex.render_status.provenance_alert_summary", provenance_summary),
                ("ops.cortex.render_status.conversation_summary", {}),
                ("ops.cortex.render_status.build_canonical_lockfile_artifacts", {}),
                ("ops.cortex.render_status.repo_inventory_summary_from_lock", {"items": []}),
                ("ops.cortex.render_status.lock_worktree_hygiene", {"status": "frozen"}),
                ("ops.cortex.render_status.registry_summary", {}),
                ("ops.cortex.render_status.artifact_inventory", {}),
                ("ops.cortex.render_status.proposal_only_state", {}),
                ("ops.cortex.render_status.world_model_state", {}),
            ]
            with ExitStack() as stack:
                for target, value in patch_specs:
                    stack.enter_context(patch(target, return_value=value))
                payload = render_status_payload(descriptor_root)

        self.assertEqual(provenance_summary, payload["provenance_alerts"])
        self.assertEqual("needs_review", payload["attention_queue"]["status"])
        self.assertEqual(1, payload["attention_queue"]["item_count"])
        self.assertEqual("initiative_provenance_drift", payload["attention_queue"]["items"][0]["kind"])

    def test_render_status_payload_preserves_full_provenance_summary_while_bounding_queue_signals(self) -> None:
        provenance_summary = {
            "status": "drift_detected",
            "initiative_item_count": 3,
            "proposal_item_count": 2,
            "item_count": 5,
            "items": [
                {
                    "kind": "initiative_provenance_drift",
                    "initiative_id": "initiative-zeta",
                    "title": "Zeta",
                    "source_ref": "docs/memory/initiatives/initiative-zeta.json",
                    "stale_attention_refs": ["attention:sha256:zeta"],
                    "missing_file_refs": [],
                },
                {
                    "kind": "proposed_session_provenance_drift",
                    "session_id": "session-bravo",
                    "task_id": "task-bravo",
                    "source_ref": "runtime/atlas/proposed-sessions/session-bravo/session.manifest.json",
                    "stale_attention_refs": [],
                    "missing_initiative_ref": "docs/memory/initiatives/missing-bravo.json",
                },
                {
                    "kind": "initiative_provenance_drift",
                    "initiative_id": "initiative-alpha",
                    "title": "Alpha",
                    "source_ref": "docs/memory/initiatives/initiative-alpha.json",
                    "stale_attention_refs": [],
                    "missing_file_refs": ["docs/memory/initiatives/missing-alpha.json"],
                },
                {
                    "kind": "proposed_session_provenance_drift",
                    "session_id": "session-charlie",
                    "task_id": "task-charlie",
                    "source_ref": "runtime/atlas/proposed-sessions/session-charlie/session.manifest.json",
                    "stale_attention_refs": ["attention:sha256:charlie"],
                    "missing_initiative_ref": None,
                },
                {
                    "kind": "initiative_provenance_drift",
                    "initiative_id": "initiative-beta",
                    "title": "Beta",
                    "source_ref": "docs/memory/initiatives/initiative-beta.json",
                    "stale_attention_refs": ["attention:sha256:beta"],
                    "missing_file_refs": [],
                },
            ],
        }

        with TemporaryDirectory() as temp_dir:
            descriptor_root = Path(temp_dir)
            (descriptor_root / "placeholder.json").write_text("{}", encoding="utf-8")
            patch_specs = [
                ("ops.cortex.render_status.load_descriptors", []),
                ("ops.cortex.render_status.load_registry_state", {"ok": True}),
                ("ops.cortex.render_status.choose_latest_session", None),
                ("ops.cortex.render_status.session_overview", None),
                ("ops.cortex.render_status.blocked_workers", []),
                ("ops.cortex.render_status.classify_merge_requests", ([], [])),
                ("ops.cortex.render_status.closure_receipts", []),
                ("ops.cortex.render_status.execution_receipt_residue_records", []),
                ("ops.cortex.render_status.governed_writes", []),
                ("ops.cortex.render_status.legacy_compatibility_surfaces", []),
                ("ops.cortex.render_status.trust_surfaces", []),
                ("ops.cortex.render_status.trust_posture_summary", {}),
                ("ops.cortex.render_status.working_memory_summary", {"_items": [], "initiatives": {}}),
                ("ops.cortex.render_status.provenance_alert_summary", provenance_summary),
                ("ops.cortex.render_status.conversation_summary", {}),
                ("ops.cortex.render_status.build_canonical_lockfile_artifacts", {}),
                ("ops.cortex.render_status.repo_inventory_summary_from_lock", {"items": []}),
                ("ops.cortex.render_status.lock_worktree_hygiene", {"status": "frozen"}),
                ("ops.cortex.render_status.registry_summary", {}),
                ("ops.cortex.render_status.artifact_inventory", {}),
                ("ops.cortex.render_status.proposal_only_state", {}),
                ("ops.cortex.render_status.world_model_state", {}),
            ]
            with ExitStack() as stack:
                for target, value in patch_specs:
                    stack.enter_context(patch(target, return_value=value))
                payload = render_status_payload(descriptor_root)

        self.assertEqual(provenance_summary, payload["provenance_alerts"])
        self.assertEqual(5, payload["provenance_alerts"]["item_count"])
        self.assertEqual(5, len(payload["provenance_alerts"]["items"]))
        self.assertEqual("needs_review", payload["attention_queue"]["status"])
        self.assertEqual(4, payload["attention_queue"]["item_count"])
        self.assertEqual("high", payload["attention_queue"]["highest_severity"])
        self.assertEqual(
            [
                "initiative_provenance_drift",
                "proposed_session_provenance_drift",
                "initiative_provenance_drift",
                "provenance_alert_overflow",
            ],
            [item["kind"] for item in payload["attention_queue"]["items"]],
        )
        self.assertEqual(
            {
                "suppressed_item_count": 2,
                "signal_cap": 3,
                "highest_suppressed_severity": "medium",
                "total_provenance_alert_count": 5,
            },
            payload["attention_queue"]["items"][3]["details"],
        )

    def test_render_status_payload_preserves_session_needs_resume_handoff(self) -> None:
        with TemporaryDirectory() as temp_dir:
            descriptor_root = Path(temp_dir)
            (descriptor_root / "placeholder.json").write_text("{}", encoding="utf-8")
            active_session = {
                "session_id": "session-resume-payload",
                "task_id": "task-resume-payload",
                "session_state": "resume_ready",
                "final_status": "running",
                "source_ref": "runtime/atlas/sessions/session-resume-payload/session.manifest.json",
            }
            patch_specs = [
                ("ops.cortex.render_status.load_descriptors", []),
                ("ops.cortex.render_status.load_registry_state", {"ok": True}),
                ("ops.cortex.render_status.choose_latest_session", None),
                ("ops.cortex.render_status.session_overview", active_session),
                ("ops.cortex.render_status.blocked_workers", []),
                ("ops.cortex.render_status.classify_merge_requests", ([], [])),
                ("ops.cortex.render_status.closure_receipts", []),
                ("ops.cortex.render_status.execution_receipt_residue_records", []),
                ("ops.cortex.render_status.governed_writes", []),
                ("ops.cortex.render_status.legacy_compatibility_surfaces", []),
                ("ops.cortex.render_status.trust_surfaces", []),
                ("ops.cortex.render_status.trust_posture_summary", {}),
                ("ops.cortex.render_status.working_memory_summary", {"_items": [], "initiatives": {}}),
                ("ops.cortex.render_status.provenance_alert_summary", {"status": "clear", "item_count": 0, "items": []}),
                ("ops.cortex.render_status.conversation_summary", {}),
                ("ops.cortex.render_status.build_canonical_lockfile_artifacts", {}),
                ("ops.cortex.render_status.repo_inventory_summary_from_lock", {"items": []}),
                ("ops.cortex.render_status.lock_worktree_hygiene", {"status": "frozen"}),
                ("ops.cortex.render_status.registry_summary", {}),
                ("ops.cortex.render_status.artifact_inventory", {}),
                ("ops.cortex.render_status.world_model_state", {}),
            ]
            with ExitStack() as stack:
                for target, value in patch_specs:
                    stack.enter_context(patch(target, return_value=value))
                payload = render_status_payload(descriptor_root)

        self.assertEqual(active_session, payload["active_session"])
        self.assertEqual("needs_review", payload["attention_queue"]["status"])
        self.assertEqual(1, payload["attention_queue"]["item_count"])
        self.assertEqual("session_needs_resume", payload["attention_queue"]["items"][0]["kind"])
        self.assertEqual(
            {
                "session_id": "session-resume-payload",
                "task_id": "task-resume-payload",
            },
            payload["attention_queue"]["items"][0]["details"],
        )

    def test_render_status_payload_preserves_resume_failed_handoff(self) -> None:
        with TemporaryDirectory() as temp_dir:
            descriptor_root = Path(temp_dir)
            (descriptor_root / "placeholder.json").write_text("{}", encoding="utf-8")
            active_session = {
                "session_id": "session-resume-failed-payload",
                "task_id": "task-resume-failed-payload",
                "session_state": "resume_failed",
                "final_status": "running",
                "resume_failure_reason": "resume dispatch artifact missing",
                "source_ref": "runtime/atlas/sessions/session-resume-failed-payload/session.manifest.json",
            }
            patch_specs = [
                ("ops.cortex.render_status.load_descriptors", []),
                ("ops.cortex.render_status.load_registry_state", {"ok": True}),
                ("ops.cortex.render_status.choose_latest_session", None),
                ("ops.cortex.render_status.session_overview", active_session),
                ("ops.cortex.render_status.blocked_workers", []),
                ("ops.cortex.render_status.classify_merge_requests", ([], [])),
                ("ops.cortex.render_status.closure_receipts", []),
                ("ops.cortex.render_status.execution_receipt_residue_records", []),
                ("ops.cortex.render_status.governed_writes", []),
                ("ops.cortex.render_status.legacy_compatibility_surfaces", []),
                ("ops.cortex.render_status.trust_surfaces", []),
                ("ops.cortex.render_status.trust_posture_summary", {}),
                ("ops.cortex.render_status.working_memory_summary", {"_items": [], "initiatives": {}}),
                ("ops.cortex.render_status.provenance_alert_summary", {"status": "clear", "item_count": 0, "items": []}),
                ("ops.cortex.render_status.conversation_summary", {}),
                ("ops.cortex.render_status.build_canonical_lockfile_artifacts", {}),
                ("ops.cortex.render_status.repo_inventory_summary_from_lock", {"items": []}),
                ("ops.cortex.render_status.lock_worktree_hygiene", {"status": "frozen"}),
                ("ops.cortex.render_status.registry_summary", {}),
                ("ops.cortex.render_status.artifact_inventory", {}),
                ("ops.cortex.render_status.world_model_state", {}),
            ]
            with ExitStack() as stack:
                for target, value in patch_specs:
                    stack.enter_context(patch(target, return_value=value))
                payload = render_status_payload(descriptor_root)

        self.assertEqual(active_session, payload["active_session"])
        self.assertEqual("needs_review", payload["attention_queue"]["status"])
        self.assertEqual(1, payload["attention_queue"]["item_count"])
        self.assertEqual("resume_failed", payload["attention_queue"]["items"][0]["kind"])
        self.assertEqual(
            {
                "session_id": "session-resume-failed-payload",
                "task_id": "task-resume-failed-payload",
                "resume_failure_reason": "resume dispatch artifact missing",
            },
            payload["attention_queue"]["items"][0]["details"],
        )

    def test_render_status_payload_preserves_session_failed_handoff(self) -> None:
        with TemporaryDirectory() as temp_dir:
            descriptor_root = Path(temp_dir)
            (descriptor_root / "placeholder.json").write_text("{}", encoding="utf-8")
            active_session = {
                "session_id": "session-failed-payload",
                "task_id": "task-failed-payload",
                "session_state": "failed",
                "final_status": "running",
                "source_ref": "runtime/atlas/sessions/session-failed-payload/session.manifest.json",
            }
            patch_specs = [
                ("ops.cortex.render_status.load_descriptors", []),
                ("ops.cortex.render_status.load_registry_state", {"ok": True}),
                ("ops.cortex.render_status.choose_latest_session", None),
                ("ops.cortex.render_status.session_overview", active_session),
                ("ops.cortex.render_status.blocked_workers", []),
                ("ops.cortex.render_status.classify_merge_requests", ([], [])),
                ("ops.cortex.render_status.closure_receipts", []),
                ("ops.cortex.render_status.execution_receipt_residue_records", []),
                ("ops.cortex.render_status.governed_writes", []),
                ("ops.cortex.render_status.legacy_compatibility_surfaces", []),
                ("ops.cortex.render_status.trust_surfaces", []),
                ("ops.cortex.render_status.trust_posture_summary", {}),
                ("ops.cortex.render_status.working_memory_summary", {"_items": [], "initiatives": {}}),
                ("ops.cortex.render_status.provenance_alert_summary", {"status": "clear", "item_count": 0, "items": []}),
                ("ops.cortex.render_status.conversation_summary", {}),
                ("ops.cortex.render_status.build_canonical_lockfile_artifacts", {}),
                ("ops.cortex.render_status.repo_inventory_summary_from_lock", {"items": []}),
                ("ops.cortex.render_status.lock_worktree_hygiene", {"status": "frozen"}),
                ("ops.cortex.render_status.registry_summary", {}),
                ("ops.cortex.render_status.artifact_inventory", {}),
                ("ops.cortex.render_status.world_model_state", {}),
            ]
            with ExitStack() as stack:
                for target, value in patch_specs:
                    stack.enter_context(patch(target, return_value=value))
                payload = render_status_payload(descriptor_root)

        self.assertEqual(active_session, payload["active_session"])
        self.assertEqual("needs_review", payload["attention_queue"]["status"])
        self.assertEqual(1, payload["attention_queue"]["item_count"])
        self.assertEqual("session_failed", payload["attention_queue"]["items"][0]["kind"])
        self.assertEqual(
            {
                "session_id": "session-failed-payload",
                "task_id": "task-failed-payload",
            },
            payload["attention_queue"]["items"][0]["details"],
        )

    def test_render_status_payload_preserves_registry_error_attention_queue_handoff(self) -> None:
        with TemporaryDirectory() as temp_dir:
            descriptor_root = Path(temp_dir)
            (descriptor_root / "placeholder.json").write_text("{}", encoding="utf-8")
            patch_specs = [
                ("ops.cortex.render_status.load_descriptors", []),
                ("ops.cortex.render_status.load_registry_state", {"ok": False, "error": "registry unavailable"}),
                ("ops.cortex.render_status.choose_latest_session", None),
                ("ops.cortex.render_status.session_overview", None),
                ("ops.cortex.render_status.blocked_workers", []),
                ("ops.cortex.render_status.classify_merge_requests", ([], [])),
                ("ops.cortex.render_status.closure_receipts", []),
                ("ops.cortex.render_status.execution_receipt_residue_records", []),
                ("ops.cortex.render_status.governed_writes", []),
                ("ops.cortex.render_status.legacy_compatibility_surfaces", []),
                ("ops.cortex.render_status.trust_surfaces", []),
                ("ops.cortex.render_status.trust_posture_summary", {}),
                ("ops.cortex.render_status.working_memory_summary", {"_items": [], "initiatives": {}}),
                ("ops.cortex.render_status.provenance_alert_summary", {"status": "clear", "item_count": 0, "items": []}),
                ("ops.cortex.render_status.conversation_summary", {}),
                ("ops.cortex.render_status.build_canonical_lockfile_artifacts", {}),
                ("ops.cortex.render_status.repo_inventory_summary_from_lock", {"items": []}),
                ("ops.cortex.render_status.lock_worktree_hygiene", {"status": "frozen"}),
                ("ops.cortex.render_status.registry_summary", {"status": "unavailable"}),
                ("ops.cortex.render_status.artifact_inventory", {}),
                ("ops.cortex.render_status.proposal_only_state", {}),
                ("ops.cortex.render_status.world_model_state", {}),
            ]
            with ExitStack() as stack:
                for target, value in patch_specs:
                    stack.enter_context(patch(target, return_value=value))
                payload = render_status_payload(descriptor_root)

        self.assertEqual("needs_review", payload["attention_queue"]["status"])
        self.assertEqual(1, payload["attention_queue"]["item_count"])
        self.assertEqual("critical", payload["attention_queue"]["highest_severity"])
        self.assertEqual("registry_error", payload["attention_queue"]["items"][0]["kind"])
        self.assertEqual({"error": "registry unavailable"}, payload["attention_queue"]["items"][0]["details"])

    def test_render_status_payload_preserves_registry_drift_handoff(self) -> None:
        with TemporaryDirectory() as temp_dir:
            descriptor_root = Path(temp_dir)
            (descriptor_root / "placeholder.json").write_text("{}", encoding="utf-8")
            active_session = {
                "session_id": "session-registry-drift-payload",
                "task_id": "task-registry-drift-payload",
                "session_state": "running",
                "final_status": "running",
                "registry_digest": "stale-digest",
                "source_ref": "runtime/atlas/sessions/session-registry-drift-payload/session.manifest.json",
            }
            patch_specs = [
                ("ops.cortex.render_status.load_descriptors", []),
                ("ops.cortex.render_status.load_registry_state", {"ok": True, "registry_digest": "current-digest"}),
                ("ops.cortex.render_status.choose_latest_session", None),
                ("ops.cortex.render_status.session_overview", active_session),
                ("ops.cortex.render_status.blocked_workers", []),
                ("ops.cortex.render_status.classify_merge_requests", ([], [])),
                ("ops.cortex.render_status.closure_receipts", []),
                ("ops.cortex.render_status.execution_receipt_residue_records", []),
                ("ops.cortex.render_status.governed_writes", []),
                ("ops.cortex.render_status.legacy_compatibility_surfaces", []),
                ("ops.cortex.render_status.trust_surfaces", []),
                ("ops.cortex.render_status.trust_posture_summary", {}),
                ("ops.cortex.render_status.working_memory_summary", {"_items": [], "initiatives": {}}),
                ("ops.cortex.render_status.provenance_alert_summary", {"status": "clear", "item_count": 0, "items": []}),
                ("ops.cortex.render_status.conversation_summary", {}),
                ("ops.cortex.render_status.build_canonical_lockfile_artifacts", {}),
                ("ops.cortex.render_status.repo_inventory_summary_from_lock", {"items": []}),
                ("ops.cortex.render_status.lock_worktree_hygiene", {"status": "frozen"}),
                ("ops.cortex.render_status.registry_summary", {}),
                ("ops.cortex.render_status.artifact_inventory", {}),
                ("ops.cortex.render_status.world_model_state", {}),
            ]
            with ExitStack() as stack:
                for target, value in patch_specs:
                    stack.enter_context(patch(target, return_value=value))
                payload = render_status_payload(descriptor_root)

        self.assertEqual(active_session, payload["active_session"])
        self.assertEqual("needs_review", payload["attention_queue"]["status"])
        self.assertEqual(1, payload["attention_queue"]["item_count"])
        self.assertEqual("registry_drift", payload["attention_queue"]["items"][0]["kind"])
        self.assertEqual(
            {
                "session_id": "session-registry-drift-payload",
                "session_registry_digest": "stale-digest",
                "current_registry_digest": "current-digest",
            },
            payload["attention_queue"]["items"][0]["details"],
        )

    def test_render_status_payload_preserves_unknown_tool_surface_handoff(self) -> None:
        with TemporaryDirectory() as temp_dir:
            descriptor_root = Path(temp_dir)
            (descriptor_root / "placeholder.json").write_text("{}", encoding="utf-8")
            active_session = {
                "session_id": "session-unknown-tool-payload",
                "task_id": "task-unknown-tool-payload",
                "session_state": "running",
                "final_status": "running",
                "source_ref": "runtime/atlas/sessions/session-unknown-tool-payload/session.manifest.json",
                "governed_surfaces": {
                    "context": {
                        "tool_id": " missing-tool ",
                        "extension_id": "known-extension",
                    }
                },
            }
            patch_specs = [
                ("ops.cortex.render_status.load_descriptors", []),
                (
                    "ops.cortex.render_status.load_registry_state",
                    {
                        "ok": True,
                        "tool_ids": {"known-tool"},
                        "extension_ids": {"known-extension"},
                    },
                ),
                ("ops.cortex.render_status.choose_latest_session", None),
                ("ops.cortex.render_status.session_overview", active_session),
                ("ops.cortex.render_status.blocked_workers", []),
                ("ops.cortex.render_status.classify_merge_requests", ([], [])),
                ("ops.cortex.render_status.closure_receipts", []),
                ("ops.cortex.render_status.execution_receipt_residue_records", []),
                ("ops.cortex.render_status.governed_writes", []),
                ("ops.cortex.render_status.legacy_compatibility_surfaces", []),
                ("ops.cortex.render_status.trust_surfaces", []),
                ("ops.cortex.render_status.trust_posture_summary", {}),
                ("ops.cortex.render_status.working_memory_summary", {"_items": [], "initiatives": {}}),
                ("ops.cortex.render_status.provenance_alert_summary", {"status": "clear", "item_count": 0, "items": []}),
                ("ops.cortex.render_status.conversation_summary", {}),
                ("ops.cortex.render_status.build_canonical_lockfile_artifacts", {}),
                ("ops.cortex.render_status.repo_inventory_summary_from_lock", {"items": []}),
                ("ops.cortex.render_status.lock_worktree_hygiene", {"status": "frozen"}),
                ("ops.cortex.render_status.registry_summary", {}),
                ("ops.cortex.render_status.artifact_inventory", {}),
                ("ops.cortex.render_status.world_model_state", {}),
            ]
            with ExitStack() as stack:
                for target, value in patch_specs:
                    stack.enter_context(patch(target, return_value=value))
                payload = render_status_payload(descriptor_root)

        self.assertEqual(active_session, payload["active_session"])
        self.assertEqual("needs_review", payload["attention_queue"]["status"])
        self.assertEqual(1, payload["attention_queue"]["item_count"])
        self.assertEqual("high", payload["attention_queue"]["highest_severity"])
        self.assertEqual(
            {
                "kind": "unknown_tool_surface",
                "severity": "high",
                "summary": "active_session.context references unknown tool_id 'missing-tool'.",
                "source_ref": "runtime/atlas/sessions/session-unknown-tool-payload/session.manifest.json",
                "details": {
                    "scope": "active_session.context",
                    "tool_id": "missing-tool",
                    "extension_id": "known-extension",
                },
            },
            payload["attention_queue"]["items"][0],
        )

    def test_render_status_payload_preserves_unknown_extension_surface_handoff(self) -> None:
        with TemporaryDirectory() as temp_dir:
            descriptor_root = Path(temp_dir)
            (descriptor_root / "placeholder.json").write_text("{}", encoding="utf-8")
            active_session = {
                "session_id": "session-unknown-extension-payload",
                "task_id": "task-unknown-extension-payload",
                "session_state": "running",
                "final_status": "running",
                "source_ref": "runtime/atlas/sessions/session-unknown-extension-payload/session.manifest.json",
                "governed_surfaces": {
                    "context": {
                        "tool_id": "known-tool",
                        "extension_id": " missing-extension ",
                    }
                },
            }
            patch_specs = [
                ("ops.cortex.render_status.load_descriptors", []),
                (
                    "ops.cortex.render_status.load_registry_state",
                    {
                        "ok": True,
                        "tool_ids": {"known-tool"},
                        "extension_ids": {"known-extension"},
                    },
                ),
                ("ops.cortex.render_status.choose_latest_session", None),
                ("ops.cortex.render_status.session_overview", active_session),
                ("ops.cortex.render_status.blocked_workers", []),
                ("ops.cortex.render_status.classify_merge_requests", ([], [])),
                ("ops.cortex.render_status.closure_receipts", []),
                ("ops.cortex.render_status.execution_receipt_residue_records", []),
                ("ops.cortex.render_status.governed_writes", []),
                ("ops.cortex.render_status.legacy_compatibility_surfaces", []),
                ("ops.cortex.render_status.trust_surfaces", []),
                ("ops.cortex.render_status.trust_posture_summary", {}),
                ("ops.cortex.render_status.working_memory_summary", {"_items": [], "initiatives": {}}),
                ("ops.cortex.render_status.provenance_alert_summary", {"status": "clear", "item_count": 0, "items": []}),
                ("ops.cortex.render_status.conversation_summary", {}),
                ("ops.cortex.render_status.build_canonical_lockfile_artifacts", {}),
                ("ops.cortex.render_status.repo_inventory_summary_from_lock", {"items": []}),
                ("ops.cortex.render_status.lock_worktree_hygiene", {"status": "frozen"}),
                ("ops.cortex.render_status.registry_summary", {}),
                ("ops.cortex.render_status.artifact_inventory", {}),
                ("ops.cortex.render_status.world_model_state", {}),
            ]
            with ExitStack() as stack:
                for target, value in patch_specs:
                    stack.enter_context(patch(target, return_value=value))
                payload = render_status_payload(descriptor_root)

        self.assertEqual(active_session, payload["active_session"])
        self.assertEqual("needs_review", payload["attention_queue"]["status"])
        self.assertEqual(1, payload["attention_queue"]["item_count"])
        self.assertEqual("high", payload["attention_queue"]["highest_severity"])
        self.assertEqual(
            {
                "kind": "unknown_extension_surface",
                "severity": "high",
                "summary": "active_session.context references unknown extension_id 'missing-extension'.",
                "source_ref": "runtime/atlas/sessions/session-unknown-extension-payload/session.manifest.json",
                "details": {
                    "scope": "active_session.context",
                    "tool_id": "known-tool",
                    "extension_id": "missing-extension",
                },
            },
            payload["attention_queue"]["items"][0],
        )

    def test_render_status_payload_preserves_legacy_compatibility_signal_handoff(self) -> None:
        with TemporaryDirectory() as temp_dir:
            descriptor_root = Path(temp_dir)
            (descriptor_root / "placeholder.json").write_text("{}", encoding="utf-8")
            legacy_payload = [
                {
                    "session_id": "session-legacy-payload",
                    "source_ref": "runtime/atlas/sessions/session-legacy-payload/session.manifest.json",
                    "original_session_ref": "runtime/atlas/sessions/session-legacy-payload/original.manifest.json",
                    "epoch": "legacy_pre_registry",
                    "cutover_at": "2026-06-17T00:00:00Z",
                    "observed_at": "2026-06-17T00:01:00Z",
                    "recorded_at": "2026-06-17T00:02:00Z",
                    "missing_governed_requirements": ["tool_id", "extension_id"],
                    "governed_identity": {"tool_id": "ignored"},
                }
            ]
            patch_specs = [
                ("ops.cortex.render_status.load_descriptors", []),
                (
                    "ops.cortex.render_status.load_registry_state",
                    {
                        "ok": True,
                        "tool_ids": {"known-tool"},
                        "extension_ids": {"known-extension"},
                    },
                ),
                ("ops.cortex.render_status.choose_latest_session", None),
                ("ops.cortex.render_status.session_overview", None),
                ("ops.cortex.render_status.blocked_workers", []),
                ("ops.cortex.render_status.classify_merge_requests", ([], [])),
                ("ops.cortex.render_status.closure_receipts", []),
                ("ops.cortex.render_status.execution_receipt_residue_records", []),
                ("ops.cortex.render_status.governed_writes", []),
                ("ops.cortex.render_status.legacy_compatibility_surfaces", legacy_payload),
                ("ops.cortex.render_status.trust_surfaces", []),
                ("ops.cortex.render_status.trust_posture_summary", {}),
                ("ops.cortex.render_status.working_memory_summary", {"_items": [], "initiatives": {}}),
                ("ops.cortex.render_status.provenance_alert_summary", {"status": "clear", "item_count": 0, "items": []}),
                ("ops.cortex.render_status.conversation_summary", {}),
                ("ops.cortex.render_status.build_canonical_lockfile_artifacts", {}),
                ("ops.cortex.render_status.repo_inventory_summary_from_lock", {"items": []}),
                ("ops.cortex.render_status.lock_worktree_hygiene", {"status": "frozen"}),
                ("ops.cortex.render_status.registry_summary", {}),
                ("ops.cortex.render_status.artifact_inventory", {}),
                ("ops.cortex.render_status.world_model_state", {}),
            ]
            with ExitStack() as stack:
                for target, value in patch_specs:
                    stack.enter_context(patch(target, return_value=value))
                payload = render_status_payload(descriptor_root)

        self.assertEqual(legacy_payload, payload["legacy_compatibility"])
        self.assertEqual("needs_review", payload["attention_queue"]["status"])
        self.assertEqual(1, payload["attention_queue"]["item_count"])
        self.assertEqual("low", payload["attention_queue"]["highest_severity"])
        self.assertEqual(
            {
                "kind": "legacy_compatibility_signal",
                "severity": "low",
                "summary": "Historical session 'session-legacy-payload' remains in legacy_pre_registry compatibility mode.",
                "source_ref": "runtime/atlas/sessions/session-legacy-payload/session.manifest.json",
                "details": {
                    "session_id": "session-legacy-payload",
                    "epoch": "legacy_pre_registry",
                    "original_session_ref": "runtime/atlas/sessions/session-legacy-payload/original.manifest.json",
                    "missing_governed_requirements": ["tool_id", "extension_id"],
                },
            },
            payload["attention_queue"]["items"][0],
        )

    def test_render_status_payload_preserves_top_level_legacy_payload_separate_from_queue_signal(self) -> None:
        with TemporaryDirectory() as temp_dir:
            descriptor_root = Path(temp_dir)
            (descriptor_root / "placeholder.json").write_text("{}", encoding="utf-8")
            descriptors = [
                _legacy_runtime_backfill_descriptor(
                    session_id="session-legacy-separation",
                    source_ref="runtime/atlas/sessions/session-legacy-separation/session.manifest.json",
                    missing_governed_requirements=["tool_id", "extension_id"],
                    governed_identity={"tool_id": "legacy-tool"},
                )
            ]
            patch_specs = [
                ("ops.cortex.render_status.load_descriptors", descriptors),
                (
                    "ops.cortex.render_status.load_registry_state",
                    {
                        "ok": True,
                        "tool_ids": {"known-tool"},
                        "extension_ids": {"known-extension"},
                    },
                ),
                ("ops.cortex.render_status.choose_latest_session", None),
                ("ops.cortex.render_status.session_overview", None),
                ("ops.cortex.render_status.blocked_workers", []),
                ("ops.cortex.render_status.classify_merge_requests", ([], [])),
                ("ops.cortex.render_status.closure_receipts", []),
                ("ops.cortex.render_status.execution_receipt_residue_records", []),
                ("ops.cortex.render_status.governed_writes", []),
                ("ops.cortex.render_status.trust_surfaces", []),
                ("ops.cortex.render_status.trust_posture_summary", {}),
                ("ops.cortex.render_status.working_memory_summary", {"_items": [], "initiatives": {}}),
                ("ops.cortex.render_status.provenance_alert_summary", {"status": "clear", "item_count": 0, "items": []}),
                ("ops.cortex.render_status.conversation_summary", {}),
                ("ops.cortex.render_status.build_canonical_lockfile_artifacts", {}),
                ("ops.cortex.render_status.repo_inventory_summary_from_lock", {"items": []}),
                ("ops.cortex.render_status.lock_worktree_hygiene", {"status": "frozen"}),
                ("ops.cortex.render_status.registry_summary", {}),
                ("ops.cortex.render_status.artifact_inventory", {}),
                ("ops.cortex.render_status.world_model_state", {}),
            ]
            with ExitStack() as stack:
                for target, value in patch_specs:
                    stack.enter_context(patch(target, return_value=value))
                payload = render_status_payload(descriptor_root)

        self.assertEqual(
            [
                {
                    "session_id": "session-legacy-separation",
                    "source_ref": "runtime/atlas/sessions/session-legacy-separation/session.manifest.json",
                    "original_session_ref": "runtime/atlas/sessions/session-legacy-separation/original.manifest.json",
                    "epoch": "legacy_pre_registry",
                    "cutover_at": "2026-06-17T00:00:00Z",
                    "observed_at": "2026-06-17T00:01:00Z",
                    "recorded_at": "2026-06-17T00:02:00Z",
                    "missing_governed_requirements": ["tool_id", "extension_id"],
                    "governed_identity": {"tool_id": "legacy-tool"},
                }
            ],
            payload["legacy_compatibility"],
        )
        self.assertEqual(
            {
                "kind": "legacy_compatibility_signal",
                "severity": "low",
                "summary": "Historical session 'session-legacy-separation' remains in legacy_pre_registry compatibility mode.",
                "source_ref": "runtime/atlas/sessions/session-legacy-separation/session.manifest.json",
                "details": {
                    "session_id": "session-legacy-separation",
                    "epoch": "legacy_pre_registry",
                    "original_session_ref": "runtime/atlas/sessions/session-legacy-separation/original.manifest.json",
                    "missing_governed_requirements": ["tool_id", "extension_id"],
                },
            },
            payload["attention_queue"]["items"][0],
        )

    def test_legacy_compatibility_surfaces_omits_non_legacy_and_missing_source_ref(self) -> None:
        items = legacy_compatibility_surfaces(
            [
                _conversation_descriptor(
                    turn_id="legacy-non-qualifying",
                    action_mode="proposal_required",
                ),
                _legacy_runtime_backfill_descriptor(
                    session_id="session-empty-source-ref",
                    source_ref="   ",
                ),
            ]
        )

        self.assertEqual([], items)

    def test_legacy_compatibility_surfaces_preserves_exact_fields_for_qualifying_descriptor(self) -> None:
        descriptor = _legacy_runtime_backfill_descriptor(
            session_id="session-legacy-helper",
            source_ref="runtime/atlas/sessions/session-legacy-helper/session.manifest.json",
            missing_governed_requirements=["tool_id", "extension_id"],
            governed_identity={"tool_id": "legacy-tool", "extension_id": "legacy-extension"},
        )
        descriptor["links"]["ignored_extra"] = "ignored"
        descriptor["state"]["ignored_extra"] = "ignored"

        items = legacy_compatibility_surfaces([descriptor])

        self.assertEqual(
            [
                {
                    "session_id": "session-legacy-helper",
                    "source_ref": "runtime/atlas/sessions/session-legacy-helper/session.manifest.json",
                    "original_session_ref": "runtime/atlas/sessions/session-legacy-helper/original.manifest.json",
                    "epoch": "legacy_pre_registry",
                    "cutover_at": "2026-06-17T00:00:00Z",
                    "observed_at": "2026-06-17T00:01:00Z",
                    "recorded_at": "2026-06-17T00:02:00Z",
                    "missing_governed_requirements": ["tool_id", "extension_id"],
                    "governed_identity": {"tool_id": "legacy-tool", "extension_id": "legacy-extension"},
                }
            ],
            items,
        )

    def test_legacy_compatibility_surfaces_sorts_by_observed_at_session_id_and_source_ref(self) -> None:
        items = legacy_compatibility_surfaces(
            [
                _legacy_runtime_backfill_descriptor(
                    session_id="session-zulu",
                    source_ref="runtime/atlas/sessions/session-zulu/session.manifest.json",
                    observed_at="2026-06-17T00:03:00Z",
                ),
                _legacy_runtime_backfill_descriptor(
                    session_id="session-alpha",
                    source_ref="runtime/atlas/sessions/session-alpha/z.manifest.json",
                    observed_at="2026-06-17T00:01:00Z",
                ),
                _legacy_runtime_backfill_descriptor(
                    session_id="session-alpha",
                    source_ref="runtime/atlas/sessions/session-alpha/a.manifest.json",
                    observed_at="2026-06-17T00:01:00Z",
                ),
            ]
        )

        self.assertEqual(
            [
                "runtime/atlas/sessions/session-alpha/a.manifest.json",
                "runtime/atlas/sessions/session-alpha/z.manifest.json",
                "runtime/atlas/sessions/session-zulu/session.manifest.json",
            ],
            [item["source_ref"] for item in items],
        )

    def test_provenance_attention_items_ignore_malformed_and_unknown_payloads(self) -> None:
        items = provenance_attention_items(
            {
                "items": [
                    "not-a-dict",
                    {"kind": "initiative_provenance_drift", "initiative_id": "empty-initiative"},
                    {"kind": "proposed_session_provenance_drift", "session_id": "empty-session"},
                    {"kind": "unknown_provenance_kind", "source_ref": "docs/memory/initiatives/ignored.json"},
                    {
                        "kind": "initiative_provenance_drift",
                        "initiative_id": "initiative-proof",
                        "source_ref": "docs/memory/initiatives/initiative-proof.json",
                        "stale_attention_refs": ["attention:sha256:stale"],
                        "missing_file_refs": [],
                    },
                ]
            }
        )

        self.assertEqual(1, len(items))
        self.assertEqual("initiative_provenance_drift", items[0]["kind"])
        self.assertEqual("medium", items[0]["severity"])
        self.assertEqual(["attention:sha256:stale"], items[0]["details"]["stale_attention_refs"])

    def test_provenance_attention_items_cap_signals_and_surface_overflow(self) -> None:
        items = provenance_attention_items(
            {
                "items": [
                    {
                        "kind": "initiative_provenance_drift",
                        "initiative_id": "initiative-zeta",
                        "source_ref": "docs/memory/initiatives/initiative-zeta.json",
                        "stale_attention_refs": ["attention:sha256:zeta"],
                        "missing_file_refs": [],
                    },
                    {
                        "kind": "proposed_session_provenance_drift",
                        "session_id": "session-bravo",
                        "task_id": "task-bravo",
                        "source_ref": "runtime/atlas/proposed-sessions/session-bravo/session.manifest.json",
                        "stale_attention_refs": [],
                        "missing_initiative_ref": "docs/memory/initiatives/missing-bravo.json",
                    },
                    {
                        "kind": "initiative_provenance_drift",
                        "initiative_id": "initiative-alpha",
                        "source_ref": "docs/memory/initiatives/initiative-alpha.json",
                        "stale_attention_refs": [],
                        "missing_file_refs": ["docs/memory/initiatives/missing-alpha.json"],
                    },
                    {
                        "kind": "proposed_session_provenance_drift",
                        "session_id": "session-charlie",
                        "task_id": "task-charlie",
                        "source_ref": "runtime/atlas/proposed-sessions/session-charlie/session.manifest.json",
                        "stale_attention_refs": ["attention:sha256:charlie"],
                        "missing_initiative_ref": None,
                    },
                    {
                        "kind": "initiative_provenance_drift",
                        "initiative_id": "initiative-beta",
                        "source_ref": "docs/memory/initiatives/initiative-beta.json",
                        "stale_attention_refs": ["attention:sha256:beta"],
                        "missing_file_refs": [],
                    },
                ]
            }
        )

        self.assertEqual(4, len(items))
        self.assertEqual(
            [
                "initiative_provenance_drift",
                "proposed_session_provenance_drift",
                "initiative_provenance_drift",
                "provenance_alert_overflow",
            ],
            [item["kind"] for item in items],
        )
        self.assertEqual(
            ["high", "high", "medium", "medium"],
            [item["severity"] for item in items],
        )
        self.assertEqual("initiative-alpha", items[0]["details"]["initiative_id"])
        self.assertEqual("session-bravo", items[1]["details"]["session_id"])
        self.assertEqual("initiative-beta", items[2]["details"]["initiative_id"])
        self.assertEqual(2, items[3]["details"]["suppressed_item_count"])
        self.assertEqual(3, items[3]["details"]["signal_cap"])
        self.assertEqual(5, items[3]["details"]["total_provenance_alert_count"])
        self.assertEqual("medium", items[3]["details"]["highest_suppressed_severity"])

    def test_provenance_alerts_route_into_attention_queue(self) -> None:
        queue = attention_queue(
            descriptors=[],
            active_session=None,
            blocked_workers_payload=[],
            open_merge_requests_payload=[],
            closure_receipts_payload=[],
            legacy_compatibility_payload=[],
            trust_surfaces_payload=[],
            working_memory_items=[],
            provenance_alerts={
                "status": "drift_detected",
                "initiative_item_count": 1,
                "proposal_item_count": 1,
                "item_count": 2,
                "items": [
                    {
                        "kind": "initiative_provenance_drift",
                        "initiative_id": "initiative-proof",
                        "title": "Proof",
                        "source_ref": "docs/memory/initiatives/initiative-proof.json",
                        "stale_attention_refs": ["attention:sha256:stale"],
                        "missing_file_refs": ["docs/memory/initiatives/missing.json"],
                    },
                    {
                        "kind": "proposed_session_provenance_drift",
                        "session_id": "session-proposed-proof",
                        "task_id": "proof-task",
                        "source_ref": "runtime/atlas/proposed-sessions/session-proposed-proof/session.manifest.json",
                        "stale_attention_refs": ["attention:sha256:stale"],
                        "missing_initiative_ref": None,
                    },
                ],
            },
            registry_state={"ok": True},
        )

        self.assertEqual("needs_review", queue["status"])
        self.assertEqual(2, queue["item_count"])
        self.assertEqual("high", queue["highest_severity"])
        self.assertEqual("initiative_provenance_drift", queue["items"][0]["kind"])
        self.assertEqual("high", queue["items"][0]["severity"])
        self.assertEqual("proposed_session_provenance_drift", queue["items"][1]["kind"])
        self.assertEqual("medium", queue["items"][1]["severity"])

    def test_attention_queue_is_clear_without_initiative_or_provenance_items(self) -> None:
        queue = attention_queue(
            descriptors=[],
            active_session=None,
            blocked_workers_payload=[],
            open_merge_requests_payload=[],
            closure_receipts_payload=[],
            legacy_compatibility_payload=[],
            trust_surfaces_payload=[],
            working_memory_items=[],
            provenance_alerts={"status": "clear", "item_count": 0, "items": []},
            registry_state={"ok": True},
        )

        self.assertEqual("clear", queue["status"])
        self.assertEqual(0, queue["item_count"])
        self.assertIsNone(queue["highest_severity"])
        self.assertEqual([], queue["items"])

    def test_attention_queue_emits_registry_error_when_registry_is_unavailable(self) -> None:
        queue = attention_queue(
            descriptors=[],
            active_session=None,
            blocked_workers_payload=[],
            open_merge_requests_payload=[],
            closure_receipts_payload=[],
            legacy_compatibility_payload=[],
            trust_surfaces_payload=[],
            working_memory_items=[],
            provenance_alerts={"status": "clear", "item_count": 0, "items": []},
            registry_state={"ok": False, "error": "registry unavailable"},
        )

        self.assertEqual("needs_review", queue["status"])
        self.assertEqual(1, queue["item_count"])
        self.assertEqual("critical", queue["highest_severity"])
        self.assertEqual(
            {
                "kind": "registry_error",
                "severity": "critical",
                "summary": "The governed tool registry could not be loaded.",
                "source_ref": "docs/registry",
                "details": {"error": "registry unavailable"},
            },
            queue["items"][0],
        )

    def test_attention_queue_omits_registry_error_when_registry_is_healthy(self) -> None:
        queue = attention_queue(
            descriptors=[],
            active_session=None,
            blocked_workers_payload=[],
            open_merge_requests_payload=[],
            closure_receipts_payload=[],
            legacy_compatibility_payload=[],
            trust_surfaces_payload=[],
            working_memory_items=[],
            provenance_alerts={"status": "clear", "item_count": 0, "items": []},
            registry_state={"ok": True, "tool_ids": set(), "extension_ids": set()},
        )

        self.assertEqual("clear", queue["status"])
        self.assertEqual(0, queue["item_count"])
        self.assertIsNone(queue["highest_severity"])
        self.assertEqual([], queue["items"])

    def test_attention_queue_omits_registry_health_dependent_contradiction_items_when_registry_is_unavailable(self) -> None:
        queue = attention_queue(
            descriptors=[],
            active_session={
                "session_id": "session-registry-proof",
                "task_id": "task-registry-proof",
                "source_ref": "runtime/atlas/sessions/session-registry-proof/session.manifest.json",
                "registry_digest": "stale-digest",
                "governed_surfaces": {
                    "context": {
                        "tool_id": "missing-tool",
                        "extension_id": "missing-extension",
                    }
                },
            },
            blocked_workers_payload=[],
            open_merge_requests_payload=[],
            closure_receipts_payload=[],
            legacy_compatibility_payload=[],
            trust_surfaces_payload=[],
            working_memory_items=[],
            provenance_alerts={"status": "clear", "item_count": 0, "items": []},
            registry_state={
                "ok": False,
                "error": "registry unavailable",
                "registry_digest": "current-digest",
                "tool_ids": {"known-tool"},
                "extension_ids": {"known-extension"},
            },
        )

        self.assertEqual("needs_review", queue["status"])
        self.assertEqual(["registry_error"], [item["kind"] for item in queue["items"]])

    def test_attention_queue_preserves_order_for_registry_error_and_other_queue_families(self) -> None:
        queue = attention_queue(
            descriptors=[],
            active_session=None,
            blocked_workers_payload=[],
            open_merge_requests_payload=[],
            closure_receipts_payload=[],
            legacy_compatibility_payload=[],
            trust_surfaces_payload=[],
            working_memory_items=[
                {
                    "memory_kind": "initiative",
                    "id": "initiative-open",
                    "title": "Open initiative",
                    "path": "docs/memory/initiatives/initiative-open.json",
                    "status": "active",
                    "metadata": {
                        "attention_summary": "Needs review",
                        "attention_severity": "medium",
                    },
                }
            ],
            provenance_alerts={
                "status": "drift_detected",
                "initiative_item_count": 1,
                "proposal_item_count": 0,
                "item_count": 1,
                "items": [
                    {
                        "kind": "initiative_provenance_drift",
                        "initiative_id": "initiative-proof",
                        "title": "Proof",
                        "source_ref": "docs/memory/initiatives/initiative-proof.json",
                        "stale_attention_refs": [],
                        "missing_file_refs": ["docs/memory/initiatives/missing.json"],
                    }
                ],
            },
            registry_state={"ok": False, "error": "registry unavailable"},
        )

        self.assertEqual("needs_review", queue["status"])
        self.assertEqual(3, queue["item_count"])
        self.assertEqual("critical", queue["highest_severity"])
        self.assertEqual(
            ["registry_error", "initiative_provenance_drift", "initiative_open_attention"],
            [item["kind"] for item in queue["items"]],
        )

    def test_attention_queue_emits_registry_drift_for_mismatched_session_and_current_digest(self) -> None:
        queue = attention_queue(
            descriptors=[],
            active_session={
                "session_id": "session-registry-drift",
                "task_id": "task-registry-drift",
                "session_state": "running",
                "final_status": "running",
                "registry_digest": "stale-digest",
                "source_ref": "runtime/atlas/sessions/session-registry-drift/session.manifest.json",
            },
            blocked_workers_payload=[],
            open_merge_requests_payload=[],
            closure_receipts_payload=[],
            legacy_compatibility_payload=[],
            trust_surfaces_payload=[],
            working_memory_items=[],
            provenance_alerts={"status": "clear", "item_count": 0, "items": []},
            registry_state={"ok": True, "registry_digest": "current-digest"},
        )

        self.assertEqual("needs_review", queue["status"])
        self.assertEqual(1, queue["item_count"])
        self.assertEqual("high", queue["highest_severity"])
        self.assertEqual(
            {
                "kind": "registry_drift",
                "severity": "high",
                "summary": "The active session was created against a different registry digest.",
                "source_ref": "runtime/atlas/sessions/session-registry-drift/session.manifest.json",
                "details": {
                    "session_id": "session-registry-drift",
                    "session_registry_digest": "stale-digest",
                    "current_registry_digest": "current-digest",
                },
            },
            queue["items"][0],
        )

    def test_attention_queue_omits_registry_drift_when_digests_match(self) -> None:
        queue = attention_queue(
            descriptors=[],
            active_session={
                "session_id": "session-registry-match",
                "task_id": "task-registry-match",
                "session_state": "running",
                "final_status": "running",
                "registry_digest": "current-digest",
                "source_ref": "runtime/atlas/sessions/session-registry-match/session.manifest.json",
            },
            blocked_workers_payload=[],
            open_merge_requests_payload=[],
            closure_receipts_payload=[],
            legacy_compatibility_payload=[],
            trust_surfaces_payload=[],
            working_memory_items=[],
            provenance_alerts={"status": "clear", "item_count": 0, "items": []},
            registry_state={"ok": True, "registry_digest": "current-digest"},
        )

        self.assertEqual("clear", queue["status"])
        self.assertEqual(0, queue["item_count"])
        self.assertEqual([], queue["items"])

    def test_attention_queue_omits_registry_drift_when_active_session_digest_is_missing(self) -> None:
        queue = attention_queue(
            descriptors=[],
            active_session={
                "session_id": "session-registry-missing-session-digest",
                "task_id": "task-registry-missing-session-digest",
                "session_state": "running",
                "final_status": "running",
                "source_ref": "runtime/atlas/sessions/session-registry-missing-session-digest/session.manifest.json",
            },
            blocked_workers_payload=[],
            open_merge_requests_payload=[],
            closure_receipts_payload=[],
            legacy_compatibility_payload=[],
            trust_surfaces_payload=[],
            working_memory_items=[],
            provenance_alerts={"status": "clear", "item_count": 0, "items": []},
            registry_state={"ok": True, "registry_digest": "current-digest"},
        )

        self.assertEqual("clear", queue["status"])
        self.assertEqual(0, queue["item_count"])
        self.assertEqual([], queue["items"])

    def test_attention_queue_omits_registry_drift_when_current_registry_digest_is_missing(self) -> None:
        queue = attention_queue(
            descriptors=[],
            active_session={
                "session_id": "session-registry-missing-current-digest",
                "task_id": "task-registry-missing-current-digest",
                "session_state": "running",
                "final_status": "running",
                "registry_digest": "stale-digest",
                "source_ref": "runtime/atlas/sessions/session-registry-missing-current-digest/session.manifest.json",
            },
            blocked_workers_payload=[],
            open_merge_requests_payload=[],
            closure_receipts_payload=[],
            legacy_compatibility_payload=[],
            trust_surfaces_payload=[],
            working_memory_items=[],
            provenance_alerts={"status": "clear", "item_count": 0, "items": []},
            registry_state={"ok": True},
        )

        self.assertEqual("clear", queue["status"])
        self.assertEqual(0, queue["item_count"])
        self.assertEqual([], queue["items"])

    def test_attention_queue_preserves_order_for_registry_drift_and_other_queue_families(self) -> None:
        queue = attention_queue(
            descriptors=[],
            active_session={
                "session_id": "session-registry-drift-order",
                "task_id": "task-registry-drift-order",
                "session_state": "running",
                "final_status": "running",
                "registry_digest": "stale-digest",
                "source_ref": "runtime/atlas/sessions/session-registry-drift-order/session.manifest.json",
            },
            blocked_workers_payload=[],
            open_merge_requests_payload=[],
            closure_receipts_payload=[],
            legacy_compatibility_payload=[],
            trust_surfaces_payload=[],
            working_memory_items=[
                {
                    "memory_kind": "initiative",
                    "id": "initiative-open",
                    "title": "Open initiative",
                    "path": "docs/memory/initiatives/initiative-open.json",
                    "status": "active",
                    "metadata": {
                        "attention_summary": "Needs review",
                        "attention_severity": "medium",
                    },
                }
            ],
            provenance_alerts={"status": "clear", "item_count": 0, "items": []},
            registry_state={"ok": True, "registry_digest": "current-digest"},
        )

        self.assertEqual("needs_review", queue["status"])
        self.assertEqual(
            ["registry_drift", "initiative_open_attention"],
            [item["kind"] for item in queue["items"]],
        )

    def test_attention_queue_emits_unknown_tool_surface_for_active_session_governed_surface(self) -> None:
        queue = attention_queue(
            descriptors=[],
            active_session={
                "session_id": "session-unknown-tool",
                "task_id": "task-unknown-tool",
                "session_state": "running",
                "final_status": "running",
                "source_ref": "runtime/atlas/sessions/session-unknown-tool/session.manifest.json",
                "governed_surfaces": {
                    "context": {
                        "tool_id": " missing-tool ",
                        "extension_id": "known-extension",
                    }
                },
            },
            blocked_workers_payload=[],
            open_merge_requests_payload=[],
            closure_receipts_payload=[],
            legacy_compatibility_payload=[],
            trust_surfaces_payload=[],
            working_memory_items=[],
            provenance_alerts={"status": "clear", "item_count": 0, "items": []},
            registry_state={
                "ok": True,
                "tool_ids": {"known-tool"},
                "extension_ids": {"known-extension"},
            },
        )

        self.assertEqual("needs_review", queue["status"])
        self.assertEqual(1, queue["item_count"])
        self.assertEqual("high", queue["highest_severity"])
        self.assertEqual(
            {
                "kind": "unknown_tool_surface",
                "severity": "high",
                "summary": "active_session.context references unknown tool_id 'missing-tool'.",
                "source_ref": "runtime/atlas/sessions/session-unknown-tool/session.manifest.json",
                "details": {
                    "scope": "active_session.context",
                    "tool_id": "missing-tool",
                    "extension_id": "known-extension",
                },
            },
            queue["items"][0],
        )

    def test_attention_queue_emits_unknown_extension_surface_for_active_session_governed_surface(self) -> None:
        queue = attention_queue(
            descriptors=[],
            active_session={
                "session_id": "session-unknown-extension",
                "task_id": "task-unknown-extension",
                "session_state": "running",
                "final_status": "running",
                "source_ref": "runtime/atlas/sessions/session-unknown-extension/session.manifest.json",
                "governed_surfaces": {
                    "context": {
                        "tool_id": "known-tool",
                        "extension_id": " missing-extension ",
                    }
                },
            },
            blocked_workers_payload=[],
            open_merge_requests_payload=[],
            closure_receipts_payload=[],
            legacy_compatibility_payload=[],
            trust_surfaces_payload=[],
            working_memory_items=[],
            provenance_alerts={"status": "clear", "item_count": 0, "items": []},
            registry_state={
                "ok": True,
                "tool_ids": {"known-tool"},
                "extension_ids": {"known-extension"},
            },
        )

        self.assertEqual("needs_review", queue["status"])
        self.assertEqual(1, queue["item_count"])
        self.assertEqual("high", queue["highest_severity"])
        self.assertEqual(
            {
                "kind": "unknown_extension_surface",
                "severity": "high",
                "summary": "active_session.context references unknown extension_id 'missing-extension'.",
                "source_ref": "runtime/atlas/sessions/session-unknown-extension/session.manifest.json",
                "details": {
                    "scope": "active_session.context",
                    "tool_id": "known-tool",
                    "extension_id": "missing-extension",
                },
            },
            queue["items"][0],
        )

    def test_attention_queue_omits_unknown_tool_surface_for_known_missing_empty_and_nondict_scope_values(self) -> None:
        cases = [
            (
                "known-tool",
                {"context": {"tool_id": "known-tool", "extension_id": "known-extension"}},
            ),
            (
                "missing-tool-id",
                {"context": {"extension_id": "known-extension"}},
            ),
            (
                "empty-tool-id",
                {"context": {"tool_id": "   ", "extension_id": "known-extension"}},
            ),
            (
                "nondict-scope",
                {"context": "not-a-dict"},
            ),
        ]

        for case_name, governed_surfaces in cases:
            with self.subTest(case=case_name):
                queue = attention_queue(
                    descriptors=[],
                    active_session={
                        "session_id": f"session-{case_name}",
                        "task_id": f"task-{case_name}",
                        "session_state": "running",
                        "final_status": "running",
                        "source_ref": f"runtime/atlas/sessions/session-{case_name}/session.manifest.json",
                        "governed_surfaces": governed_surfaces,
                    },
                    blocked_workers_payload=[],
                    open_merge_requests_payload=[],
                    closure_receipts_payload=[],
                    legacy_compatibility_payload=[],
                    trust_surfaces_payload=[],
                    working_memory_items=[],
                    provenance_alerts={"status": "clear", "item_count": 0, "items": []},
                    registry_state={
                        "ok": True,
                        "tool_ids": {"known-tool"},
                        "extension_ids": {"known-extension"},
                    },
                )

                self.assertEqual("clear", queue["status"])
                self.assertEqual(0, queue["item_count"])
                self.assertIsNone(queue["highest_severity"])
                self.assertEqual([], queue["items"])

    def test_attention_queue_omits_unknown_extension_surface_for_known_missing_empty_and_nondict_scope_values(self) -> None:
        cases = [
            (
                "known-extension",
                {"context": {"tool_id": "known-tool", "extension_id": "known-extension"}},
            ),
            (
                "missing-extension-id",
                {"context": {"tool_id": "known-tool"}},
            ),
            (
                "empty-extension-id",
                {"context": {"tool_id": "known-tool", "extension_id": "   "}},
            ),
            (
                "nondict-scope",
                {"context": "not-a-dict"},
            ),
        ]

        for case_name, governed_surfaces in cases:
            with self.subTest(case=case_name):
                queue = attention_queue(
                    descriptors=[],
                    active_session={
                        "session_id": f"session-{case_name}",
                        "task_id": f"task-{case_name}",
                        "session_state": "running",
                        "final_status": "running",
                        "source_ref": f"runtime/atlas/sessions/session-{case_name}/session.manifest.json",
                        "governed_surfaces": governed_surfaces,
                    },
                    blocked_workers_payload=[],
                    open_merge_requests_payload=[],
                    closure_receipts_payload=[],
                    legacy_compatibility_payload=[],
                    trust_surfaces_payload=[],
                    working_memory_items=[],
                    provenance_alerts={"status": "clear", "item_count": 0, "items": []},
                    registry_state={
                        "ok": True,
                        "tool_ids": {"known-tool"},
                        "extension_ids": {"known-extension"},
                    },
                )

                self.assertEqual("clear", queue["status"])
                self.assertEqual(0, queue["item_count"])
                self.assertIsNone(queue["highest_severity"])
                self.assertEqual([], queue["items"])

    def test_attention_queue_preserves_unknown_tool_surface_with_unknown_extension_surface(self) -> None:
        queue = attention_queue(
            descriptors=[],
            active_session={
                "session_id": "session-unknown-siblings",
                "task_id": "task-unknown-siblings",
                "session_state": "running",
                "final_status": "running",
                "source_ref": "runtime/atlas/sessions/session-unknown-siblings/session.manifest.json",
                "governed_surfaces": {
                    "context": {
                        "tool_id": "missing-tool",
                        "extension_id": "missing-extension",
                    }
                },
            },
            blocked_workers_payload=[],
            open_merge_requests_payload=[],
            closure_receipts_payload=[],
            legacy_compatibility_payload=[],
            trust_surfaces_payload=[],
            working_memory_items=[],
            provenance_alerts={"status": "clear", "item_count": 0, "items": []},
            registry_state={
                "ok": True,
                "tool_ids": {"known-tool"},
                "extension_ids": {"known-extension"},
            },
        )

        self.assertEqual("needs_review", queue["status"])
        self.assertEqual(2, queue["item_count"])
        self.assertEqual("high", queue["highest_severity"])
        self.assertEqual(
            ["unknown_extension_surface", "unknown_tool_surface"],
            [item["kind"] for item in queue["items"]],
        )
        self.assertEqual(
            {
                "scope": "active_session.context",
                "tool_id": "missing-tool",
                "extension_id": "missing-extension",
            },
            queue["items"][0]["details"],
        )
        self.assertEqual(
            {
                "scope": "active_session.context",
                "tool_id": "missing-tool",
                "extension_id": "missing-extension",
            },
            queue["items"][1]["details"],
        )

    def test_attention_queue_preserves_unknown_extension_surface_with_unknown_tool_surface(self) -> None:
        queue = attention_queue(
            descriptors=[],
            active_session={
                "session_id": "session-unknown-extension-siblings",
                "task_id": "task-unknown-extension-siblings",
                "session_state": "running",
                "final_status": "running",
                "source_ref": "runtime/atlas/sessions/session-unknown-extension-siblings/session.manifest.json",
                "governed_surfaces": {
                    "context": {
                        "tool_id": "missing-tool",
                        "extension_id": "missing-extension",
                    }
                },
            },
            blocked_workers_payload=[],
            open_merge_requests_payload=[],
            closure_receipts_payload=[],
            legacy_compatibility_payload=[],
            trust_surfaces_payload=[],
            working_memory_items=[],
            provenance_alerts={"status": "clear", "item_count": 0, "items": []},
            registry_state={
                "ok": True,
                "tool_ids": {"known-tool"},
                "extension_ids": {"known-extension"},
            },
        )

        self.assertEqual("needs_review", queue["status"])
        self.assertEqual(2, queue["item_count"])
        self.assertEqual("high", queue["highest_severity"])
        self.assertEqual(
            ["unknown_extension_surface", "unknown_tool_surface"],
            [item["kind"] for item in queue["items"]],
        )
        self.assertEqual(
            {
                "kind": "unknown_extension_surface",
                "severity": "high",
                "summary": "active_session.context references unknown extension_id 'missing-extension'.",
                "source_ref": "runtime/atlas/sessions/session-unknown-extension-siblings/session.manifest.json",
                "details": {
                    "scope": "active_session.context",
                    "tool_id": "missing-tool",
                    "extension_id": "missing-extension",
                },
            },
            queue["items"][0],
        )

    def test_attention_queue_preserves_unknown_extension_surface_with_admitted_session_state_families(self) -> None:
        cases = [
            ("resume_ready", "running", ["unknown_extension_surface", "session_needs_resume"]),
            ("resume_failed", "running", ["resume_failed", "unknown_extension_surface"]),
            ("failed", "running", ["session_failed", "unknown_extension_surface"]),
        ]

        for session_state, final_status, expected_kinds in cases:
            with self.subTest(session_state=session_state, final_status=final_status):
                queue = attention_queue(
                    descriptors=[],
                    active_session={
                        "session_id": f"session-{session_state}-unknown-extension",
                        "task_id": f"task-{session_state}-unknown-extension",
                        "session_state": session_state,
                        "final_status": final_status,
                        "resume_failure_reason": "resume dispatch artifact missing",
                        "source_ref": f"runtime/atlas/sessions/session-{session_state}-unknown-extension/session.manifest.json",
                        "governed_surfaces": {
                            "context": {
                                "tool_id": "known-tool",
                                "extension_id": "missing-extension",
                            }
                        },
                    },
                    blocked_workers_payload=[],
                    open_merge_requests_payload=[],
                    closure_receipts_payload=[],
                    legacy_compatibility_payload=[],
                    trust_surfaces_payload=[],
                    working_memory_items=[],
                    provenance_alerts={"status": "clear", "item_count": 0, "items": []},
                    registry_state={
                        "ok": True,
                        "tool_ids": {"known-tool"},
                        "extension_ids": {"known-extension"},
                    },
                )

                self.assertEqual("needs_review", queue["status"])
                self.assertEqual(expected_kinds, [item["kind"] for item in queue["items"]])

    def test_attention_queue_preserves_order_for_unknown_extension_surface_and_other_queue_families(self) -> None:
        queue = attention_queue(
            descriptors=[],
            active_session={
                "session_id": "session-unknown-extension-order",
                "task_id": "task-unknown-extension-order",
                "session_state": "resume_ready",
                "final_status": "running",
                "registry_digest": "stale-digest",
                "source_ref": "runtime/atlas/sessions/session-unknown-extension-order/session.manifest.json",
                "governed_surfaces": {
                    "context": {
                        "tool_id": "known-tool",
                        "extension_id": "missing-extension",
                    }
                },
            },
            blocked_workers_payload=[],
            open_merge_requests_payload=[],
            closure_receipts_payload=[],
            legacy_compatibility_payload=[],
            trust_surfaces_payload=[],
            working_memory_items=[
                {
                    "memory_kind": "initiative",
                    "id": "initiative-open",
                    "title": "Open initiative",
                    "path": "docs/memory/initiatives/initiative-open.json",
                    "status": "active",
                    "metadata": {
                        "attention_summary": "Needs review",
                        "attention_severity": "medium",
                    },
                }
            ],
            provenance_alerts={"status": "clear", "item_count": 0, "items": []},
            registry_state={
                "ok": True,
                "registry_digest": "current-digest",
                "tool_ids": {"known-tool"},
                "extension_ids": {"known-extension"},
            },
        )

        self.assertEqual("needs_review", queue["status"])
        self.assertEqual("high", queue["highest_severity"])
        self.assertEqual(
            [
                "registry_drift",
                "unknown_extension_surface",
                "initiative_open_attention",
                "session_needs_resume",
            ],
            [item["kind"] for item in queue["items"]],
        )

    def test_attention_queue_preserves_provenance_overflow_with_unknown_extension_surface(self) -> None:
        provenance_summary = {
            "status": "drift_detected",
            "initiative_item_count": 3,
            "proposal_item_count": 2,
            "item_count": 5,
            "items": [
                {
                    "kind": "initiative_provenance_drift",
                    "initiative_id": "initiative-zeta",
                    "title": "Zeta",
                    "source_ref": "docs/memory/initiatives/initiative-zeta.json",
                    "stale_attention_refs": ["attention:sha256:zeta"],
                    "missing_file_refs": [],
                },
                {
                    "kind": "proposed_session_provenance_drift",
                    "session_id": "session-bravo",
                    "task_id": "task-bravo",
                    "source_ref": "runtime/atlas/proposed-sessions/session-bravo/session.manifest.json",
                    "stale_attention_refs": [],
                    "missing_initiative_ref": "docs/memory/initiatives/missing-bravo.json",
                },
                {
                    "kind": "initiative_provenance_drift",
                    "initiative_id": "initiative-alpha",
                    "title": "Alpha",
                    "source_ref": "docs/memory/initiatives/initiative-alpha.json",
                    "stale_attention_refs": [],
                    "missing_file_refs": ["docs/memory/initiatives/missing-alpha.json"],
                },
                {
                    "kind": "proposed_session_provenance_drift",
                    "session_id": "session-charlie",
                    "task_id": "task-charlie",
                    "source_ref": "runtime/atlas/proposed-sessions/session-charlie/session.manifest.json",
                    "stale_attention_refs": ["attention:sha256:charlie"],
                    "missing_initiative_ref": None,
                },
                {
                    "kind": "initiative_provenance_drift",
                    "initiative_id": "initiative-beta",
                    "title": "Beta",
                    "source_ref": "docs/memory/initiatives/initiative-beta.json",
                    "stale_attention_refs": ["attention:sha256:beta"],
                    "missing_file_refs": [],
                },
            ],
        }

        queue = attention_queue(
            descriptors=[],
            active_session={
                "session_id": "session-unknown-extension-overflow",
                "task_id": "task-unknown-extension-overflow",
                "session_state": "running",
                "final_status": "running",
                "source_ref": "runtime/atlas/sessions/session-unknown-extension-overflow/session.manifest.json",
                "governed_surfaces": {
                    "context": {
                        "tool_id": "known-tool",
                        "extension_id": "missing-extension",
                    }
                },
            },
            blocked_workers_payload=[],
            open_merge_requests_payload=[],
            closure_receipts_payload=[],
            legacy_compatibility_payload=[],
            trust_surfaces_payload=[],
            working_memory_items=[],
            provenance_alerts=provenance_summary,
            registry_state={
                "ok": True,
                "tool_ids": {"known-tool"},
                "extension_ids": {"known-extension"},
            },
        )

        self.assertEqual("needs_review", queue["status"])
        self.assertEqual(5, queue["item_count"])
        self.assertEqual(
            [
                "initiative_provenance_drift",
                "proposed_session_provenance_drift",
                "unknown_extension_surface",
                "initiative_provenance_drift",
                "provenance_alert_overflow",
            ],
            [item["kind"] for item in queue["items"]],
        )
        self.assertEqual(
            {
                "suppressed_item_count": 2,
                "signal_cap": 3,
                "highest_suppressed_severity": "medium",
                "total_provenance_alert_count": 5,
            },
            queue["items"][4]["details"],
        )

    def test_attention_queue_emits_legacy_compatibility_signal_for_legacy_pre_registry_payload(self) -> None:
        queue = attention_queue(
            descriptors=[],
            active_session=None,
            blocked_workers_payload=[],
            open_merge_requests_payload=[],
            closure_receipts_payload=[],
            legacy_compatibility_payload=[
                {
                    "session_id": "session-legacy-proof",
                    "source_ref": "runtime/atlas/sessions/session-legacy-proof/session.manifest.json",
                    "original_session_ref": "runtime/atlas/sessions/session-legacy-proof/original.manifest.json",
                    "epoch": "legacy_pre_registry",
                    "cutover_at": "2026-06-17T00:00:00Z",
                    "observed_at": "2026-06-17T00:01:00Z",
                    "recorded_at": "2026-06-17T00:02:00Z",
                    "missing_governed_requirements": ["tool_id", "extension_id"],
                    "governed_identity": {"tool_id": "ignored"},
                }
            ],
            trust_surfaces_payload=[],
            working_memory_items=[],
            provenance_alerts={"status": "clear", "item_count": 0, "items": []},
            registry_state={"ok": True},
        )

        self.assertEqual("needs_review", queue["status"])
        self.assertEqual(1, queue["item_count"])
        self.assertEqual("low", queue["highest_severity"])
        self.assertEqual(
            {
                "kind": "legacy_compatibility_signal",
                "severity": "low",
                "summary": "Historical session 'session-legacy-proof' remains in legacy_pre_registry compatibility mode.",
                "source_ref": "runtime/atlas/sessions/session-legacy-proof/session.manifest.json",
                "details": {
                    "session_id": "session-legacy-proof",
                    "epoch": "legacy_pre_registry",
                    "original_session_ref": "runtime/atlas/sessions/session-legacy-proof/original.manifest.json",
                    "missing_governed_requirements": ["tool_id", "extension_id"],
                },
            },
            queue["items"][0],
        )

    def test_attention_queue_omits_legacy_compatibility_signal_for_missing_source_ref_and_non_legacy_epoch(self) -> None:
        queue = attention_queue(
            descriptors=[],
            active_session=None,
            blocked_workers_payload=[],
            open_merge_requests_payload=[],
            closure_receipts_payload=[],
            legacy_compatibility_payload=[
                {
                    "session_id": "session-missing-source-ref",
                    "source_ref": "   ",
                    "original_session_ref": "runtime/atlas/sessions/session-missing-source-ref/original.manifest.json",
                    "epoch": "legacy_pre_registry",
                    "missing_governed_requirements": ["tool_id"],
                },
                {
                    "session_id": "session-non-legacy-epoch",
                    "source_ref": "runtime/atlas/sessions/session-non-legacy-epoch/session.manifest.json",
                    "original_session_ref": "runtime/atlas/sessions/session-non-legacy-epoch/original.manifest.json",
                    "epoch": "governed_v1",
                    "missing_governed_requirements": ["extension_id"],
                },
            ],
            trust_surfaces_payload=[],
            working_memory_items=[],
            provenance_alerts={"status": "clear", "item_count": 0, "items": []},
            registry_state={"ok": True},
        )

        self.assertEqual("clear", queue["status"])
        self.assertEqual(0, queue["item_count"])
        self.assertIsNone(queue["highest_severity"])
        self.assertEqual([], queue["items"])

    def test_attention_queue_preserves_order_for_legacy_compatibility_signal_and_other_queue_families(self) -> None:
        queue = attention_queue(
            descriptors=[],
            active_session={
                "session_id": "session-legacy-order",
                "task_id": "task-legacy-order",
                "session_state": "resume_ready",
                "final_status": "running",
                "registry_digest": "stale-digest",
                "source_ref": "runtime/atlas/sessions/session-legacy-order/session.manifest.json",
            },
            blocked_workers_payload=[],
            open_merge_requests_payload=[],
            closure_receipts_payload=[],
            legacy_compatibility_payload=[
                {
                    "session_id": "session-legacy-order",
                    "source_ref": "runtime/atlas/sessions/session-legacy-order/session.manifest.json",
                    "original_session_ref": "runtime/atlas/sessions/session-legacy-order/original.manifest.json",
                    "epoch": "legacy_pre_registry",
                    "missing_governed_requirements": ["tool_id"],
                }
            ],
            trust_surfaces_payload=[],
            working_memory_items=[
                {
                    "memory_kind": "initiative",
                    "id": "initiative-open",
                    "title": "Open initiative",
                    "path": "docs/memory/initiatives/initiative-open.json",
                    "status": "active",
                    "metadata": {
                        "attention_summary": "Needs review",
                        "attention_severity": "medium",
                    },
                }
            ],
            provenance_alerts={"status": "clear", "item_count": 0, "items": []},
            registry_state={"ok": True, "registry_digest": "current-digest"},
        )

        self.assertEqual("needs_review", queue["status"])
        self.assertEqual("high", queue["highest_severity"])
        self.assertEqual(
            [
                "registry_drift",
                "initiative_open_attention",
                "session_needs_resume",
                "legacy_compatibility_signal",
            ],
            [item["kind"] for item in queue["items"]],
        )

    def test_attention_queue_preserves_provenance_overflow_with_legacy_compatibility_signal(self) -> None:
        provenance_summary = {
            "status": "drift_detected",
            "initiative_item_count": 3,
            "proposal_item_count": 2,
            "item_count": 5,
            "items": [
                {
                    "kind": "initiative_provenance_drift",
                    "initiative_id": "initiative-zeta",
                    "title": "Zeta",
                    "source_ref": "docs/memory/initiatives/initiative-zeta.json",
                    "stale_attention_refs": ["attention:sha256:zeta"],
                    "missing_file_refs": [],
                },
                {
                    "kind": "proposed_session_provenance_drift",
                    "session_id": "session-bravo",
                    "task_id": "task-bravo",
                    "source_ref": "runtime/atlas/proposed-sessions/session-bravo/session.manifest.json",
                    "stale_attention_refs": [],
                    "missing_initiative_ref": "docs/memory/initiatives/missing-bravo.json",
                },
                {
                    "kind": "initiative_provenance_drift",
                    "initiative_id": "initiative-alpha",
                    "title": "Alpha",
                    "source_ref": "docs/memory/initiatives/initiative-alpha.json",
                    "stale_attention_refs": [],
                    "missing_file_refs": ["docs/memory/initiatives/missing-alpha.json"],
                },
                {
                    "kind": "proposed_session_provenance_drift",
                    "session_id": "session-charlie",
                    "task_id": "task-charlie",
                    "source_ref": "runtime/atlas/proposed-sessions/session-charlie/session.manifest.json",
                    "stale_attention_refs": ["attention:sha256:charlie"],
                    "missing_initiative_ref": None,
                },
                {
                    "kind": "initiative_provenance_drift",
                    "initiative_id": "initiative-beta",
                    "title": "Beta",
                    "source_ref": "docs/memory/initiatives/initiative-beta.json",
                    "stale_attention_refs": ["attention:sha256:beta"],
                    "missing_file_refs": [],
                },
            ],
        }

        queue = attention_queue(
            descriptors=[],
            active_session=None,
            blocked_workers_payload=[],
            open_merge_requests_payload=[],
            closure_receipts_payload=[],
            legacy_compatibility_payload=[
                {
                    "session_id": "session-legacy-overflow",
                    "source_ref": "runtime/atlas/sessions/session-legacy-overflow/session.manifest.json",
                    "original_session_ref": "runtime/atlas/sessions/session-legacy-overflow/original.manifest.json",
                    "epoch": "legacy_pre_registry",
                    "missing_governed_requirements": ["tool_id"],
                }
            ],
            trust_surfaces_payload=[],
            working_memory_items=[],
            provenance_alerts=provenance_summary,
            registry_state={"ok": True},
        )

        self.assertEqual("needs_review", queue["status"])
        self.assertEqual(5, queue["item_count"])
        self.assertEqual(
            [
                "initiative_provenance_drift",
                "proposed_session_provenance_drift",
                "initiative_provenance_drift",
                "provenance_alert_overflow",
                "legacy_compatibility_signal",
            ],
            [item["kind"] for item in queue["items"]],
        )
        self.assertEqual(
            {
                "suppressed_item_count": 2,
                "signal_cap": 3,
                "highest_suppressed_severity": "medium",
                "total_provenance_alert_count": 5,
            },
            queue["items"][3]["details"],
        )

    def test_attention_queue_preserves_unknown_tool_surface_with_admitted_session_state_families(self) -> None:
        cases = [
            ("resume_ready", "running", ["unknown_tool_surface", "session_needs_resume"]),
            ("resume_failed", "running", ["resume_failed", "unknown_tool_surface"]),
            ("failed", "running", ["session_failed", "unknown_tool_surface"]),
        ]

        for session_state, final_status, expected_kinds in cases:
            with self.subTest(session_state=session_state, final_status=final_status):
                queue = attention_queue(
                    descriptors=[],
                    active_session={
                        "session_id": f"session-{session_state}-unknown-tool",
                        "task_id": f"task-{session_state}-unknown-tool",
                        "session_state": session_state,
                        "final_status": final_status,
                        "resume_failure_reason": "resume dispatch artifact missing",
                        "source_ref": f"runtime/atlas/sessions/session-{session_state}-unknown-tool/session.manifest.json",
                        "governed_surfaces": {
                            "context": {
                                "tool_id": "missing-tool",
                                "extension_id": "known-extension",
                            }
                        },
                    },
                    blocked_workers_payload=[],
                    open_merge_requests_payload=[],
                    closure_receipts_payload=[],
                    legacy_compatibility_payload=[],
                    trust_surfaces_payload=[],
                    working_memory_items=[],
                    provenance_alerts={"status": "clear", "item_count": 0, "items": []},
                    registry_state={
                        "ok": True,
                        "tool_ids": {"known-tool"},
                        "extension_ids": {"known-extension"},
                    },
                )

                self.assertEqual("needs_review", queue["status"])
                self.assertEqual(expected_kinds, [item["kind"] for item in queue["items"]])

    def test_attention_queue_preserves_order_for_unknown_tool_surface_and_other_queue_families(self) -> None:
        queue = attention_queue(
            descriptors=[],
            active_session={
                "session_id": "session-unknown-tool-order",
                "task_id": "task-unknown-tool-order",
                "session_state": "resume_ready",
                "final_status": "running",
                "registry_digest": "stale-digest",
                "source_ref": "runtime/atlas/sessions/session-unknown-tool-order/session.manifest.json",
                "governed_surfaces": {
                    "context": {
                        "tool_id": "missing-tool",
                        "extension_id": "missing-extension",
                    }
                },
            },
            blocked_workers_payload=[],
            open_merge_requests_payload=[],
            closure_receipts_payload=[],
            legacy_compatibility_payload=[],
            trust_surfaces_payload=[],
            working_memory_items=[
                {
                    "memory_kind": "initiative",
                    "id": "initiative-open",
                    "title": "Open initiative",
                    "path": "docs/memory/initiatives/initiative-open.json",
                    "status": "active",
                    "metadata": {
                        "attention_summary": "Needs review",
                        "attention_severity": "medium",
                    },
                }
            ],
            provenance_alerts={"status": "clear", "item_count": 0, "items": []},
            registry_state={
                "ok": True,
                "registry_digest": "current-digest",
                "tool_ids": {"known-tool"},
                "extension_ids": {"known-extension"},
            },
        )

        self.assertEqual("needs_review", queue["status"])
        self.assertEqual("high", queue["highest_severity"])
        self.assertEqual(
            [
                "registry_drift",
                "unknown_extension_surface",
                "unknown_tool_surface",
                "initiative_open_attention",
                "session_needs_resume",
            ],
            [item["kind"] for item in queue["items"]],
        )

    def test_attention_queue_preserves_provenance_overflow_with_unknown_tool_surface(self) -> None:
        provenance_summary = {
            "status": "drift_detected",
            "initiative_item_count": 3,
            "proposal_item_count": 2,
            "item_count": 5,
            "items": [
                {
                    "kind": "initiative_provenance_drift",
                    "initiative_id": "initiative-zeta",
                    "title": "Zeta",
                    "source_ref": "docs/memory/initiatives/initiative-zeta.json",
                    "stale_attention_refs": ["attention:sha256:zeta"],
                    "missing_file_refs": [],
                },
                {
                    "kind": "proposed_session_provenance_drift",
                    "session_id": "session-bravo",
                    "task_id": "task-bravo",
                    "source_ref": "runtime/atlas/proposed-sessions/session-bravo/session.manifest.json",
                    "stale_attention_refs": [],
                    "missing_initiative_ref": "docs/memory/initiatives/missing-bravo.json",
                },
                {
                    "kind": "initiative_provenance_drift",
                    "initiative_id": "initiative-alpha",
                    "title": "Alpha",
                    "source_ref": "docs/memory/initiatives/initiative-alpha.json",
                    "stale_attention_refs": [],
                    "missing_file_refs": ["docs/memory/initiatives/missing-alpha.json"],
                },
                {
                    "kind": "proposed_session_provenance_drift",
                    "session_id": "session-charlie",
                    "task_id": "task-charlie",
                    "source_ref": "runtime/atlas/proposed-sessions/session-charlie/session.manifest.json",
                    "stale_attention_refs": ["attention:sha256:charlie"],
                    "missing_initiative_ref": None,
                },
                {
                    "kind": "initiative_provenance_drift",
                    "initiative_id": "initiative-beta",
                    "title": "Beta",
                    "source_ref": "docs/memory/initiatives/initiative-beta.json",
                    "stale_attention_refs": ["attention:sha256:beta"],
                    "missing_file_refs": [],
                },
            ],
        }

        queue = attention_queue(
            descriptors=[],
            active_session={
                "session_id": "session-unknown-tool-overflow",
                "task_id": "task-unknown-tool-overflow",
                "session_state": "running",
                "final_status": "running",
                "source_ref": "runtime/atlas/sessions/session-unknown-tool-overflow/session.manifest.json",
                "governed_surfaces": {
                    "context": {
                        "tool_id": "missing-tool",
                        "extension_id": "known-extension",
                    }
                },
            },
            blocked_workers_payload=[],
            open_merge_requests_payload=[],
            closure_receipts_payload=[],
            legacy_compatibility_payload=[],
            trust_surfaces_payload=[],
            working_memory_items=[],
            provenance_alerts=provenance_summary,
            registry_state={
                "ok": True,
                "tool_ids": {"known-tool"},
                "extension_ids": {"known-extension"},
            },
        )

        self.assertEqual("needs_review", queue["status"])
        self.assertEqual(5, queue["item_count"])
        self.assertEqual(
            [
                "initiative_provenance_drift",
                "proposed_session_provenance_drift",
                "unknown_tool_surface",
                "initiative_provenance_drift",
                "provenance_alert_overflow",
            ],
            [item["kind"] for item in queue["items"]],
        )
        self.assertEqual(
            {
                "suppressed_item_count": 2,
                "signal_cap": 3,
                "highest_suppressed_severity": "medium",
                "total_provenance_alert_count": 5,
            },
            queue["items"][4]["details"],
        )

    def test_attention_queue_emits_session_needs_resume_for_resume_ready_session_state(self) -> None:
        queue = attention_queue(
            descriptors=[],
            active_session={
                "session_id": "session-resume-ready",
                "task_id": "task-resume-ready",
                "session_state": "resume_ready",
                "final_status": "running",
                "source_ref": "runtime/atlas/sessions/session-resume-ready/session.manifest.json",
            },
            blocked_workers_payload=[],
            open_merge_requests_payload=[],
            closure_receipts_payload=[],
            legacy_compatibility_payload=[],
            trust_surfaces_payload=[],
            working_memory_items=[],
            provenance_alerts={"status": "clear", "item_count": 0, "items": []},
            registry_state={"ok": True},
        )

        self.assertEqual("needs_review", queue["status"])
        self.assertEqual(1, queue["item_count"])
        self.assertEqual("medium", queue["highest_severity"])
        self.assertEqual(
            {
                "kind": "session_needs_resume",
                "severity": "medium",
                "summary": "The active session is waiting for an explicit resume or merge follow-up.",
                "source_ref": "runtime/atlas/sessions/session-resume-ready/session.manifest.json",
                "details": {
                    "session_id": "session-resume-ready",
                    "task_id": "task-resume-ready",
                },
            },
            queue["items"][0],
        )

    def test_attention_queue_emits_session_needs_resume_for_resume_ready_final_status(self) -> None:
        queue = attention_queue(
            descriptors=[],
            active_session={
                "session_id": "session-resume-final",
                "task_id": "task-resume-final",
                "session_state": "running",
                "final_status": "resume_ready",
                "source_ref": "runtime/atlas/sessions/session-resume-final/session.manifest.json",
            },
            blocked_workers_payload=[],
            open_merge_requests_payload=[],
            closure_receipts_payload=[],
            legacy_compatibility_payload=[],
            trust_surfaces_payload=[],
            working_memory_items=[],
            provenance_alerts={"status": "clear", "item_count": 0, "items": []},
            registry_state={"ok": True},
        )

        self.assertEqual("needs_review", queue["status"])
        self.assertEqual(1, queue["item_count"])
        self.assertEqual("session_needs_resume", queue["items"][0]["kind"])
        self.assertEqual("session-resume-final", queue["items"][0]["details"]["session_id"])

    def test_attention_queue_emits_resume_failed_for_resume_failed_session_state(self) -> None:
        queue = attention_queue(
            descriptors=[],
            active_session={
                "session_id": "session-resume-failed",
                "task_id": "task-resume-failed",
                "session_state": "resume_failed",
                "final_status": "running",
                "resume_failure_reason": "resume dispatch artifact missing",
                "source_ref": "runtime/atlas/sessions/session-resume-failed/session.manifest.json",
            },
            blocked_workers_payload=[],
            open_merge_requests_payload=[],
            closure_receipts_payload=[],
            legacy_compatibility_payload=[],
            trust_surfaces_payload=[],
            working_memory_items=[],
            provenance_alerts={"status": "clear", "item_count": 0, "items": []},
            registry_state={"ok": True},
        )

        self.assertEqual("needs_review", queue["status"])
        self.assertEqual(1, queue["item_count"])
        self.assertEqual("high", queue["highest_severity"])
        self.assertEqual(
            {
                "kind": "resume_failed",
                "severity": "high",
                "summary": "The active session resume path failed and needs operator review.",
                "source_ref": "runtime/atlas/sessions/session-resume-failed/session.manifest.json",
                "details": {
                    "session_id": "session-resume-failed",
                    "task_id": "task-resume-failed",
                    "resume_failure_reason": "resume dispatch artifact missing",
                },
            },
            queue["items"][0],
        )

    def test_attention_queue_emits_resume_failed_for_resume_failed_final_status(self) -> None:
        queue = attention_queue(
            descriptors=[],
            active_session={
                "session_id": "session-resume-failed-final",
                "task_id": "task-resume-failed-final",
                "session_state": "running",
                "final_status": "resume_failed",
                "resume_failure_reason": "resume merge completion missing",
                "source_ref": "runtime/atlas/sessions/session-resume-failed-final/session.manifest.json",
            },
            blocked_workers_payload=[],
            open_merge_requests_payload=[],
            closure_receipts_payload=[],
            legacy_compatibility_payload=[],
            trust_surfaces_payload=[],
            working_memory_items=[],
            provenance_alerts={"status": "clear", "item_count": 0, "items": []},
            registry_state={"ok": True},
        )

        self.assertEqual("needs_review", queue["status"])
        self.assertEqual(1, queue["item_count"])
        self.assertEqual("resume_failed", queue["items"][0]["kind"])
        self.assertEqual("session-resume-failed-final", queue["items"][0]["details"]["session_id"])

    def test_attention_queue_omits_resume_failed_when_resume_failed_is_absent(self) -> None:
        queue = attention_queue(
            descriptors=[],
            active_session={
                "session_id": "session-running",
                "task_id": "task-running",
                "session_state": "running",
                "final_status": "running",
                "source_ref": "runtime/atlas/sessions/session-running/session.manifest.json",
            },
            blocked_workers_payload=[],
            open_merge_requests_payload=[],
            closure_receipts_payload=[],
            legacy_compatibility_payload=[],
            trust_surfaces_payload=[],
            working_memory_items=[],
            provenance_alerts={"status": "clear", "item_count": 0, "items": []},
            registry_state={"ok": True},
        )

        self.assertEqual("clear", queue["status"])
        self.assertEqual(0, queue["item_count"])
        self.assertEqual([], queue["items"])

    def test_attention_queue_preserves_resume_failed_when_registry_is_unavailable(self) -> None:
        queue = attention_queue(
            descriptors=[],
            active_session={
                "session_id": "session-resume-failed-offline-registry",
                "task_id": "task-resume-failed-offline-registry",
                "session_state": "resume_failed",
                "final_status": "running",
                "resume_failure_reason": "resume request unresolved",
                "source_ref": "runtime/atlas/sessions/session-resume-failed-offline-registry/session.manifest.json",
            },
            blocked_workers_payload=[],
            open_merge_requests_payload=[],
            closure_receipts_payload=[],
            legacy_compatibility_payload=[],
            trust_surfaces_payload=[],
            working_memory_items=[],
            provenance_alerts={"status": "clear", "item_count": 0, "items": []},
            registry_state={"ok": False, "error": "registry unavailable"},
        )

        self.assertEqual("needs_review", queue["status"])
        self.assertEqual(
            ["registry_error", "resume_failed"],
            [item["kind"] for item in queue["items"]],
        )

    def test_attention_queue_preserves_resume_failed_with_registry_drift(self) -> None:
        queue = attention_queue(
            descriptors=[],
            active_session={
                "session_id": "session-resume-failed-drift",
                "task_id": "task-resume-failed-drift",
                "session_state": "resume_failed",
                "final_status": "running",
                "registry_digest": "stale-digest",
                "resume_failure_reason": "resume worker status missing",
                "source_ref": "runtime/atlas/sessions/session-resume-failed-drift/session.manifest.json",
            },
            blocked_workers_payload=[],
            open_merge_requests_payload=[],
            closure_receipts_payload=[],
            legacy_compatibility_payload=[],
            trust_surfaces_payload=[],
            working_memory_items=[],
            provenance_alerts={"status": "clear", "item_count": 0, "items": []},
            registry_state={"ok": True, "registry_digest": "current-digest"},
        )

        self.assertEqual("needs_review", queue["status"])
        self.assertEqual(
            ["registry_drift", "resume_failed"],
            [item["kind"] for item in queue["items"]],
        )

    def test_attention_queue_emits_session_failed_for_failed_session_state(self) -> None:
        queue = attention_queue(
            descriptors=[],
            active_session={
                "session_id": "session-failed",
                "task_id": "task-failed",
                "session_state": "failed",
                "final_status": "running",
                "source_ref": "runtime/atlas/sessions/session-failed/session.manifest.json",
            },
            blocked_workers_payload=[],
            open_merge_requests_payload=[],
            closure_receipts_payload=[],
            legacy_compatibility_payload=[],
            trust_surfaces_payload=[],
            working_memory_items=[],
            provenance_alerts={"status": "clear", "item_count": 0, "items": []},
            registry_state={"ok": True},
        )

        self.assertEqual("needs_review", queue["status"])
        self.assertEqual(1, queue["item_count"])
        self.assertEqual("high", queue["highest_severity"])
        self.assertEqual(
            {
                "kind": "session_failed",
                "severity": "high",
                "summary": "The active session ended in a failed state.",
                "source_ref": "runtime/atlas/sessions/session-failed/session.manifest.json",
                "details": {
                    "session_id": "session-failed",
                    "task_id": "task-failed",
                },
            },
            queue["items"][0],
        )

    def test_attention_queue_emits_session_failed_for_failed_final_status(self) -> None:
        queue = attention_queue(
            descriptors=[],
            active_session={
                "session_id": "session-failed-final",
                "task_id": "task-failed-final",
                "session_state": "running",
                "final_status": "failed",
                "source_ref": "runtime/atlas/sessions/session-failed-final/session.manifest.json",
            },
            blocked_workers_payload=[],
            open_merge_requests_payload=[],
            closure_receipts_payload=[],
            legacy_compatibility_payload=[],
            trust_surfaces_payload=[],
            working_memory_items=[],
            provenance_alerts={"status": "clear", "item_count": 0, "items": []},
            registry_state={"ok": True},
        )

        self.assertEqual("needs_review", queue["status"])
        self.assertEqual(1, queue["item_count"])
        self.assertEqual("session_failed", queue["items"][0]["kind"])
        self.assertEqual("session-failed-final", queue["items"][0]["details"]["session_id"])

    def test_attention_queue_omits_session_failed_when_failed_is_absent(self) -> None:
        queue = attention_queue(
            descriptors=[],
            active_session={
                "session_id": "session-running",
                "task_id": "task-running",
                "session_state": "running",
                "final_status": "running",
                "source_ref": "runtime/atlas/sessions/session-running/session.manifest.json",
            },
            blocked_workers_payload=[],
            open_merge_requests_payload=[],
            closure_receipts_payload=[],
            legacy_compatibility_payload=[],
            trust_surfaces_payload=[],
            working_memory_items=[],
            provenance_alerts={"status": "clear", "item_count": 0, "items": []},
            registry_state={"ok": True},
        )

        self.assertEqual("clear", queue["status"])
        self.assertEqual(0, queue["item_count"])
        self.assertEqual([], queue["items"])

    def test_attention_queue_preserves_session_failed_when_registry_is_unavailable(self) -> None:
        queue = attention_queue(
            descriptors=[],
            active_session={
                "session_id": "session-failed-offline-registry",
                "task_id": "task-failed-offline-registry",
                "session_state": "failed",
                "final_status": "running",
                "source_ref": "runtime/atlas/sessions/session-failed-offline-registry/session.manifest.json",
            },
            blocked_workers_payload=[],
            open_merge_requests_payload=[],
            closure_receipts_payload=[],
            legacy_compatibility_payload=[],
            trust_surfaces_payload=[],
            working_memory_items=[],
            provenance_alerts={"status": "clear", "item_count": 0, "items": []},
            registry_state={"ok": False, "error": "registry unavailable"},
        )

        self.assertEqual("needs_review", queue["status"])
        self.assertEqual(
            ["registry_error", "session_failed"],
            [item["kind"] for item in queue["items"]],
        )

    def test_attention_queue_preserves_session_failed_with_registry_drift(self) -> None:
        queue = attention_queue(
            descriptors=[],
            active_session={
                "session_id": "session-failed-drift",
                "task_id": "task-failed-drift",
                "session_state": "failed",
                "final_status": "running",
                "registry_digest": "stale-digest",
                "source_ref": "runtime/atlas/sessions/session-failed-drift/session.manifest.json",
            },
            blocked_workers_payload=[],
            open_merge_requests_payload=[],
            closure_receipts_payload=[],
            legacy_compatibility_payload=[],
            trust_surfaces_payload=[],
            working_memory_items=[],
            provenance_alerts={"status": "clear", "item_count": 0, "items": []},
            registry_state={"ok": True, "registry_digest": "current-digest"},
        )

        self.assertEqual("needs_review", queue["status"])
        self.assertEqual(
            ["registry_drift", "session_failed"],
            [item["kind"] for item in queue["items"]],
        )

    def test_attention_queue_omits_session_needs_resume_when_resume_ready_is_absent(self) -> None:
        queue = attention_queue(
            descriptors=[],
            active_session={
                "session_id": "session-running",
                "task_id": "task-running",
                "session_state": "running",
                "final_status": "running",
                "source_ref": "runtime/atlas/sessions/session-running/session.manifest.json",
            },
            blocked_workers_payload=[],
            open_merge_requests_payload=[],
            closure_receipts_payload=[],
            legacy_compatibility_payload=[],
            trust_surfaces_payload=[],
            working_memory_items=[],
            provenance_alerts={"status": "clear", "item_count": 0, "items": []},
            registry_state={"ok": True},
        )

        self.assertEqual("clear", queue["status"])
        self.assertEqual(0, queue["item_count"])
        self.assertEqual([], queue["items"])

    def test_attention_queue_preserves_session_needs_resume_when_registry_is_unavailable(self) -> None:
        queue = attention_queue(
            descriptors=[],
            active_session={
                "session_id": "session-resume-offline-registry",
                "task_id": "task-resume-offline-registry",
                "session_state": "resume_ready",
                "final_status": "running",
                "source_ref": "runtime/atlas/sessions/session-resume-offline-registry/session.manifest.json",
            },
            blocked_workers_payload=[],
            open_merge_requests_payload=[],
            closure_receipts_payload=[],
            legacy_compatibility_payload=[],
            trust_surfaces_payload=[],
            working_memory_items=[],
            provenance_alerts={"status": "clear", "item_count": 0, "items": []},
            registry_state={"ok": False, "error": "registry unavailable"},
        )

        self.assertEqual("needs_review", queue["status"])
        self.assertEqual(
            ["registry_error", "session_needs_resume"],
            [item["kind"] for item in queue["items"]],
        )

    def test_attention_queue_preserves_session_needs_resume_with_registry_drift(self) -> None:
        queue = attention_queue(
            descriptors=[],
            active_session={
                "session_id": "session-resume-drift",
                "task_id": "task-resume-drift",
                "session_state": "resume_ready",
                "final_status": "running",
                "registry_digest": "stale-digest",
                "source_ref": "runtime/atlas/sessions/session-resume-drift/session.manifest.json",
            },
            blocked_workers_payload=[],
            open_merge_requests_payload=[],
            closure_receipts_payload=[],
            legacy_compatibility_payload=[],
            trust_surfaces_payload=[],
            working_memory_items=[],
            provenance_alerts={"status": "clear", "item_count": 0, "items": []},
            registry_state={"ok": True, "registry_digest": "current-digest"},
        )

        self.assertEqual("needs_review", queue["status"])
        self.assertEqual(
            ["registry_drift", "session_needs_resume"],
            [item["kind"] for item in queue["items"]],
        )

    def test_attention_queue_preserves_order_for_session_needs_resume_and_other_queue_families(self) -> None:
        queue = attention_queue(
            descriptors=[],
            active_session={
                "session_id": "session-resume-order",
                "task_id": "task-resume-order",
                "session_state": "resume_ready",
                "final_status": "running",
                "source_ref": "runtime/atlas/sessions/session-resume-order/session.manifest.json",
            },
            blocked_workers_payload=[],
            open_merge_requests_payload=[],
            closure_receipts_payload=[],
            legacy_compatibility_payload=[],
            trust_surfaces_payload=[],
            working_memory_items=[
                {
                    "memory_kind": "initiative",
                    "id": "initiative-open",
                    "title": "Open initiative",
                    "path": "docs/memory/initiatives/initiative-open.json",
                    "status": "active",
                    "metadata": {
                        "attention_summary": "Needs review",
                        "attention_severity": "medium",
                    },
                }
            ],
            provenance_alerts={"status": "clear", "item_count": 0, "items": []},
            registry_state={"ok": True},
        )

        self.assertEqual("needs_review", queue["status"])
        self.assertEqual(
            ["initiative_open_attention", "session_needs_resume"],
            [item["kind"] for item in queue["items"]],
        )

    def test_attention_queue_preserves_provenance_overflow_when_session_needs_resume_is_present(self) -> None:
        queue = attention_queue(
            descriptors=[],
            active_session={
                "session_id": "session-resume-overflow",
                "task_id": "task-resume-overflow",
                "session_state": "resume_ready",
                "final_status": "running",
                "source_ref": "runtime/atlas/sessions/session-resume-overflow/session.manifest.json",
            },
            blocked_workers_payload=[],
            open_merge_requests_payload=[],
            closure_receipts_payload=[],
            legacy_compatibility_payload=[],
            trust_surfaces_payload=[],
            working_memory_items=[],
            provenance_alerts={
                "status": "drift_detected",
                "initiative_item_count": 3,
                "proposal_item_count": 2,
                "item_count": 5,
                "items": [
                    {
                        "kind": "initiative_provenance_drift",
                        "initiative_id": "initiative-zeta",
                        "title": "Zeta",
                        "source_ref": "docs/memory/initiatives/initiative-zeta.json",
                        "stale_attention_refs": ["attention:sha256:zeta"],
                        "missing_file_refs": [],
                    },
                    {
                        "kind": "proposed_session_provenance_drift",
                        "session_id": "session-bravo",
                        "task_id": "task-bravo",
                        "source_ref": "runtime/atlas/proposed-sessions/session-bravo/session.manifest.json",
                        "stale_attention_refs": [],
                        "missing_initiative_ref": "docs/memory/initiatives/missing-bravo.json",
                    },
                    {
                        "kind": "initiative_provenance_drift",
                        "initiative_id": "initiative-alpha",
                        "title": "Alpha",
                        "source_ref": "docs/memory/initiatives/initiative-alpha.json",
                        "stale_attention_refs": [],
                        "missing_file_refs": ["docs/memory/initiatives/missing-alpha.json"],
                    },
                    {
                        "kind": "proposed_session_provenance_drift",
                        "session_id": "session-charlie",
                        "task_id": "task-charlie",
                        "source_ref": "runtime/atlas/proposed-sessions/session-charlie/session.manifest.json",
                        "stale_attention_refs": ["attention:sha256:charlie"],
                        "missing_initiative_ref": None,
                    },
                    {
                        "kind": "initiative_provenance_drift",
                        "initiative_id": "initiative-beta",
                        "title": "Beta",
                        "source_ref": "docs/memory/initiatives/initiative-beta.json",
                        "stale_attention_refs": ["attention:sha256:beta"],
                        "missing_file_refs": [],
                    },
                ],
            },
            registry_state={"ok": True},
        )

        self.assertEqual("needs_review", queue["status"])
        self.assertEqual(
            [
                "initiative_provenance_drift",
                "proposed_session_provenance_drift",
                "initiative_provenance_drift",
                "provenance_alert_overflow",
                "session_needs_resume",
            ],
            [item["kind"] for item in queue["items"]],
        )
        self.assertEqual(
            {
                "suppressed_item_count": 2,
                "signal_cap": 3,
                "highest_suppressed_severity": "medium",
                "total_provenance_alert_count": 5,
            },
            queue["items"][3]["details"],
        )

    def test_attention_queue_preserves_order_for_resume_failed_and_other_queue_families(self) -> None:
        queue = attention_queue(
            descriptors=[],
            active_session={
                "session_id": "session-resume-failed-order",
                "task_id": "task-resume-failed-order",
                "session_state": "resume_failed",
                "final_status": "running",
                "resume_failure_reason": "resume worker missing",
                "source_ref": "runtime/atlas/sessions/session-resume-failed-order/session.manifest.json",
            },
            blocked_workers_payload=[],
            open_merge_requests_payload=[],
            closure_receipts_payload=[],
            legacy_compatibility_payload=[],
            trust_surfaces_payload=[],
            working_memory_items=[
                {
                    "memory_kind": "initiative",
                    "id": "initiative-open",
                    "title": "Open initiative",
                    "path": "docs/memory/initiatives/initiative-open.json",
                    "status": "active",
                    "metadata": {
                        "attention_summary": "Needs review",
                        "attention_severity": "medium",
                    },
                }
            ],
            provenance_alerts={"status": "clear", "item_count": 0, "items": []},
            registry_state={"ok": True},
        )

        self.assertEqual("needs_review", queue["status"])
        self.assertEqual(
            ["resume_failed", "initiative_open_attention"],
            [item["kind"] for item in queue["items"]],
        )

    def test_attention_queue_preserves_order_for_session_failed_and_other_queue_families(self) -> None:
        queue = attention_queue(
            descriptors=[],
            active_session={
                "session_id": "session-failed-order",
                "task_id": "task-failed-order",
                "session_state": "failed",
                "final_status": "running",
                "source_ref": "runtime/atlas/sessions/session-failed-order/session.manifest.json",
            },
            blocked_workers_payload=[],
            open_merge_requests_payload=[],
            closure_receipts_payload=[],
            legacy_compatibility_payload=[],
            trust_surfaces_payload=[],
            working_memory_items=[
                {
                    "memory_kind": "initiative",
                    "id": "initiative-open",
                    "title": "Open initiative",
                    "path": "docs/memory/initiatives/initiative-open.json",
                    "status": "active",
                    "metadata": {
                        "attention_summary": "Needs review",
                        "attention_severity": "medium",
                    },
                }
            ],
            provenance_alerts={"status": "clear", "item_count": 0, "items": []},
            registry_state={"ok": True},
        )

        self.assertEqual("needs_review", queue["status"])
        self.assertEqual(
            ["session_failed", "initiative_open_attention"],
            [item["kind"] for item in queue["items"]],
        )

    def test_attention_queue_preserves_provenance_overflow_when_registry_drift_is_present(self) -> None:
        queue = attention_queue(
            descriptors=[],
            active_session={
                "session_id": "session-registry-drift-overflow",
                "task_id": "task-registry-drift-overflow",
                "session_state": "running",
                "final_status": "running",
                "registry_digest": "stale-digest",
                "source_ref": "runtime/atlas/sessions/session-registry-drift-overflow/session.manifest.json",
            },
            blocked_workers_payload=[],
            open_merge_requests_payload=[],
            closure_receipts_payload=[],
            legacy_compatibility_payload=[],
            trust_surfaces_payload=[],
            working_memory_items=[],
            provenance_alerts={
                "status": "drift_detected",
                "initiative_item_count": 3,
                "proposal_item_count": 2,
                "item_count": 5,
                "items": [
                    {
                        "kind": "initiative_provenance_drift",
                        "initiative_id": "initiative-zeta",
                        "title": "Zeta",
                        "source_ref": "docs/memory/initiatives/initiative-zeta.json",
                        "stale_attention_refs": ["attention:sha256:zeta"],
                        "missing_file_refs": [],
                    },
                    {
                        "kind": "proposed_session_provenance_drift",
                        "session_id": "session-bravo",
                        "task_id": "task-bravo",
                        "source_ref": "runtime/atlas/proposed-sessions/session-bravo/session.manifest.json",
                        "stale_attention_refs": [],
                        "missing_initiative_ref": "docs/memory/initiatives/missing-bravo.json",
                    },
                    {
                        "kind": "initiative_provenance_drift",
                        "initiative_id": "initiative-alpha",
                        "title": "Alpha",
                        "source_ref": "docs/memory/initiatives/initiative-alpha.json",
                        "stale_attention_refs": [],
                        "missing_file_refs": ["docs/memory/initiatives/missing-alpha.json"],
                    },
                    {
                        "kind": "proposed_session_provenance_drift",
                        "session_id": "session-charlie",
                        "task_id": "task-charlie",
                        "source_ref": "runtime/atlas/proposed-sessions/session-charlie/session.manifest.json",
                        "stale_attention_refs": ["attention:sha256:charlie"],
                        "missing_initiative_ref": None,
                    },
                    {
                        "kind": "initiative_provenance_drift",
                        "initiative_id": "initiative-beta",
                        "title": "Beta",
                        "source_ref": "docs/memory/initiatives/initiative-beta.json",
                        "stale_attention_refs": ["attention:sha256:beta"],
                        "missing_file_refs": [],
                    },
                ],
            },
            registry_state={"ok": True, "registry_digest": "current-digest"},
        )

        self.assertEqual("needs_review", queue["status"])
        self.assertEqual(
            [
                "initiative_provenance_drift",
                "proposed_session_provenance_drift",
                "registry_drift",
                "initiative_provenance_drift",
                "provenance_alert_overflow",
            ],
            [item["kind"] for item in queue["items"]],
        )
        self.assertEqual(
            {
                "suppressed_item_count": 2,
                "signal_cap": 3,
                "highest_suppressed_severity": "medium",
                "total_provenance_alert_count": 5,
            },
            queue["items"][4]["details"],
        )

    def test_attention_queue_preserves_provenance_overflow_when_resume_failed_is_present(self) -> None:
        queue = attention_queue(
            descriptors=[],
            active_session={
                "session_id": "session-resume-failed-overflow",
                "task_id": "task-resume-failed-overflow",
                "session_state": "resume_failed",
                "final_status": "running",
                "resume_failure_reason": "resume dispatch missing",
                "source_ref": "runtime/atlas/sessions/session-resume-failed-overflow/session.manifest.json",
            },
            blocked_workers_payload=[],
            open_merge_requests_payload=[],
            closure_receipts_payload=[],
            legacy_compatibility_payload=[],
            trust_surfaces_payload=[],
            working_memory_items=[],
            provenance_alerts={
                "status": "drift_detected",
                "initiative_item_count": 3,
                "proposal_item_count": 2,
                "item_count": 5,
                "items": [
                    {
                        "kind": "initiative_provenance_drift",
                        "initiative_id": "initiative-zeta",
                        "title": "Zeta",
                        "source_ref": "docs/memory/initiatives/initiative-zeta.json",
                        "stale_attention_refs": ["attention:sha256:zeta"],
                        "missing_file_refs": [],
                    },
                    {
                        "kind": "proposed_session_provenance_drift",
                        "session_id": "session-bravo",
                        "task_id": "task-bravo",
                        "source_ref": "runtime/atlas/proposed-sessions/session-bravo/session.manifest.json",
                        "stale_attention_refs": [],
                        "missing_initiative_ref": "docs/memory/initiatives/missing-bravo.json",
                    },
                    {
                        "kind": "initiative_provenance_drift",
                        "initiative_id": "initiative-alpha",
                        "title": "Alpha",
                        "source_ref": "docs/memory/initiatives/initiative-alpha.json",
                        "stale_attention_refs": [],
                        "missing_file_refs": ["docs/memory/initiatives/missing-alpha.json"],
                    },
                    {
                        "kind": "proposed_session_provenance_drift",
                        "session_id": "session-charlie",
                        "task_id": "task-charlie",
                        "source_ref": "runtime/atlas/proposed-sessions/session-charlie/session.manifest.json",
                        "stale_attention_refs": ["attention:sha256:charlie"],
                        "missing_initiative_ref": None,
                    },
                    {
                        "kind": "initiative_provenance_drift",
                        "initiative_id": "initiative-beta",
                        "title": "Beta",
                        "source_ref": "docs/memory/initiatives/initiative-beta.json",
                        "stale_attention_refs": ["attention:sha256:beta"],
                        "missing_file_refs": [],
                    },
                ],
            },
            registry_state={"ok": True},
        )

        self.assertEqual("needs_review", queue["status"])
        self.assertEqual(
            [
                "initiative_provenance_drift",
                "proposed_session_provenance_drift",
                "resume_failed",
                "initiative_provenance_drift",
                "provenance_alert_overflow",
            ],
            [item["kind"] for item in queue["items"]],
        )
        self.assertEqual(
            {
                "suppressed_item_count": 2,
                "signal_cap": 3,
                "highest_suppressed_severity": "medium",
                "total_provenance_alert_count": 5,
            },
            queue["items"][4]["details"],
        )

    def test_attention_queue_routes_initiative_open_attention_without_provenance(self) -> None:
        queue = attention_queue(
            descriptors=[],
            active_session=None,
            blocked_workers_payload=[],
            open_merge_requests_payload=[],
            closure_receipts_payload=[],
            legacy_compatibility_payload=[],
            trust_surfaces_payload=[],
            working_memory_items=[
                {
                    "memory_kind": "initiative",
                    "id": "initiative-open",
                    "title": "Open initiative",
                    "path": "docs/memory/initiatives/initiative-open.json",
                    "status": "active",
                    "metadata": {
                        "attention_summary": "Needs review",
                        "attention_severity": "medium",
                    },
                }
            ],
            provenance_alerts={"status": "clear", "item_count": 0, "items": []},
            registry_state={"ok": True},
        )

        self.assertEqual("needs_review", queue["status"])
        self.assertEqual(1, queue["item_count"])
        self.assertEqual("medium", queue["highest_severity"])
        self.assertEqual("initiative_open_attention", queue["items"][0]["kind"])

    def test_attention_queue_preserves_deterministic_order_for_mixed_initiative_and_provenance_items(self) -> None:
        queue = attention_queue(
            descriptors=[],
            active_session=None,
            blocked_workers_payload=[],
            open_merge_requests_payload=[],
            closure_receipts_payload=[],
            legacy_compatibility_payload=[],
            trust_surfaces_payload=[],
            working_memory_items=[
                {
                    "memory_kind": "initiative",
                    "id": "initiative-open",
                    "title": "Open initiative",
                    "path": "docs/memory/initiatives/initiative-open.json",
                    "status": "active",
                    "metadata": {
                        "attention_summary": "Needs review",
                        "attention_severity": "medium",
                    },
                }
            ],
            provenance_alerts={
                "status": "drift_detected",
                "initiative_item_count": 1,
                "proposal_item_count": 0,
                "item_count": 1,
                "items": [
                    {
                        "kind": "initiative_provenance_drift",
                        "initiative_id": "initiative-proof",
                        "title": "Proof",
                        "source_ref": "docs/memory/initiatives/initiative-proof.json",
                        "stale_attention_refs": [],
                        "missing_file_refs": ["docs/memory/initiatives/missing.json"],
                    }
                ],
            },
            registry_state={"ok": True},
        )

        self.assertEqual("needs_review", queue["status"])
        self.assertEqual(2, queue["item_count"])
        self.assertEqual("high", queue["highest_severity"])
        self.assertEqual(
            ["initiative_provenance_drift", "initiative_open_attention"],
            [item["kind"] for item in queue["items"]],
        )

    def test_attention_queue_omits_initiatives_without_actionable_attention_summary(self) -> None:
        queue = attention_queue(
            descriptors=[],
            active_session=None,
            blocked_workers_payload=[],
            open_merge_requests_payload=[],
            closure_receipts_payload=[],
            legacy_compatibility_payload=[],
            trust_surfaces_payload=[],
            working_memory_items=[
                {
                    "memory_kind": "initiative",
                    "id": "initiative-idle",
                    "title": "Idle initiative",
                    "path": "docs/memory/initiatives/initiative-idle.json",
                    "status": "active",
                    "metadata": {},
                }
            ],
            provenance_alerts={"status": "clear", "item_count": 0, "items": []},
            registry_state={"ok": True},
        )

        self.assertEqual("clear", queue["status"])
        self.assertEqual(0, queue["item_count"])
        self.assertEqual([], queue["items"])

    def test_attention_queue_emits_conversation_action_request_for_proposal_required_turn(self) -> None:
        queue = attention_queue(
            descriptors=[
                _conversation_descriptor(
                    turn_id="turn-proposal",
                    action_mode="proposal_required",
                    intent="write_receipt",
                    conversation_id="conversation-governed",
                    source_ref="runtime/atlas/conversations/conversation-governed/turns/turn-proposal.json",
                )
            ],
            active_session=None,
            blocked_workers_payload=[],
            open_merge_requests_payload=[],
            closure_receipts_payload=[],
            legacy_compatibility_payload=[],
            trust_surfaces_payload=[],
            working_memory_items=[],
            provenance_alerts={"status": "clear", "item_count": 0, "items": []},
            registry_state={"ok": True},
        )

        self.assertEqual("needs_review", queue["status"])
        self.assertEqual(1, queue["item_count"])
        self.assertEqual("medium", queue["highest_severity"])
        self.assertEqual("conversation_action_request", queue["items"][0]["kind"])
        self.assertEqual(
            {
                "conversation_id": "conversation-governed",
                "turn_id": "turn-proposal",
                "intent": "write_receipt",
            },
            queue["items"][0]["details"],
        )

    def test_attention_queue_omits_non_qualifying_conversation_turn(self) -> None:
        queue = attention_queue(
            descriptors=[_conversation_descriptor(turn_id="turn-info", action_mode="informational")],
            active_session=None,
            blocked_workers_payload=[],
            open_merge_requests_payload=[],
            closure_receipts_payload=[],
            legacy_compatibility_payload=[],
            trust_surfaces_payload=[],
            working_memory_items=[],
            provenance_alerts={"status": "clear", "item_count": 0, "items": []},
            registry_state={"ok": True},
        )

        self.assertEqual("clear", queue["status"])
        self.assertEqual(0, queue["item_count"])
        self.assertIsNone(queue["highest_severity"])
        self.assertEqual([], queue["items"])

    def test_attention_queue_preserves_order_for_provenance_and_conversation_request(self) -> None:
        queue = attention_queue(
            descriptors=[_conversation_descriptor(turn_id="turn-proposal", action_mode="proposal_required")],
            active_session=None,
            blocked_workers_payload=[],
            open_merge_requests_payload=[],
            closure_receipts_payload=[],
            legacy_compatibility_payload=[],
            trust_surfaces_payload=[],
            working_memory_items=[],
            provenance_alerts={
                "status": "drift_detected",
                "initiative_item_count": 1,
                "proposal_item_count": 0,
                "item_count": 1,
                "items": [
                    {
                        "kind": "initiative_provenance_drift",
                        "initiative_id": "initiative-proof",
                        "title": "Proof",
                        "source_ref": "docs/memory/initiatives/initiative-proof.json",
                        "stale_attention_refs": [],
                        "missing_file_refs": ["docs/memory/initiatives/missing.json"],
                    }
                ],
            },
            registry_state={"ok": True},
        )

        self.assertEqual("needs_review", queue["status"])
        self.assertEqual(2, queue["item_count"])
        self.assertEqual("high", queue["highest_severity"])
        self.assertEqual(
            ["initiative_provenance_drift", "conversation_action_request"],
            [item["kind"] for item in queue["items"]],
        )

    def test_blocked_workers_select_latest_qualifying_worker_state_per_worker(self) -> None:
        descriptors = [
            _worker_status_descriptor(
                worker_id="worker-1",
                worker_state="blocked",
                heartbeat_at="2026-06-16T12:00:00Z",
                blocked_reason="waiting on secret",
                source_ref="runtime/atlas/workers/worker-1/status-older.json",
            ),
            _worker_status_descriptor(
                worker_id="worker-1",
                worker_state="running",
                heartbeat_at="2026-06-16T12:05:00Z",
                source_ref="runtime/atlas/workers/worker-1/status-latest.json",
            ),
            _worker_status_descriptor(
                worker_id="worker-2",
                worker_state="running",
                heartbeat_at="2026-06-16T12:01:00Z",
                source_ref="runtime/atlas/workers/worker-2/status-older.json",
            ),
            _worker_status_descriptor(
                worker_id="worker-2",
                worker_state="merge_wait",
                heartbeat_at="2026-06-16T12:06:00Z",
                blocked_reason="waiting for merge",
                source_ref="runtime/atlas/workers/worker-2/status-latest.json",
            ),
        ]

        self.assertEqual(
            [
                {
                    "worker_id": "worker-2",
                    "assignment_id": "assignment-2",
                    "tool_id": "tool-worker-2",
                    "extension_id": "extension-worker-2",
                    "state": "merge_wait",
                    "blocked_reason": "waiting for merge",
                    "registry_digest": "registry-digest-1",
                    "source_ref": "runtime/atlas/workers/worker-2/status-latest.json",
                }
            ],
            blocked_workers(descriptors),
        )

    def test_classify_merge_requests_prefers_session_linked_canonical_request_per_lineage(self) -> None:
        descriptors = [
            _merge_request_descriptor(
                merge_request_id="merge-request-older",
                lineage_key="lineage-1",
                source_ref="runtime/atlas/merge-requests/merge-request-older.json",
                conflicting_workers=["worker-a", "worker-b"],
            ),
            _merge_request_descriptor(
                merge_request_id="merge-request-linked",
                lineage_key="lineage-1",
                source_ref="runtime/atlas/merge-requests/merge-request-linked.json",
                conflicting_workers=["worker-z"],
            ),
            _session_manifest_descriptor(
                merge_request_refs=[
                    "runtime/atlas/merge-requests/merge-request-linked.json",
                ]
            ),
        ]

        active, residue = classify_merge_requests(descriptors)

        self.assertEqual(
            [
                {
                    "merge_request_id": "merge-request-linked",
                    "tool_id": "tool-merge-request-linked",
                    "extension_id": "extension-merge-request-linked",
                    "registry_digest": "registry-digest-1",
                    "conflicting_workers": ["worker-z"],
                    "source_ref": "runtime/atlas/merge-requests/merge-request-linked.json",
                    "conflict_key": "lineage-1",
                }
            ],
            active,
        )
        self.assertEqual(
            [
                {
                    "merge_request_id": "merge-request-older",
                    "source_ref": "runtime/atlas/merge-requests/merge-request-older.json",
                    "conflict_key": "lineage-1",
                    "status": "retained_residue",
                    "canonical_merge_request_id": "merge-request-linked",
                    "canonical_source_ref": "runtime/atlas/merge-requests/merge-request-linked.json",
                }
            ],
            residue,
        )
        self.assertEqual(active, open_merge_requests(descriptors))

    def test_classify_merge_requests_omits_completed_lineage_from_active_payload(self) -> None:
        descriptors = [
            _merge_request_descriptor(
                merge_request_id="merge-request-completed",
                lineage_key="lineage-1",
                source_ref="runtime/atlas/merge-requests/merge-request-completed.json",
                conflicting_workers=["worker-a"],
            ),
            _merge_request_descriptor(
                merge_request_id="merge-request-residue",
                lineage_key="lineage-1",
                source_ref="runtime/atlas/merge-requests/merge-request-residue.json",
                conflicting_workers=["worker-b", "worker-c"],
            ),
            _merge_completion_descriptor(merge_request_id="merge-request-completed"),
        ]

        active, residue = classify_merge_requests(descriptors)

        self.assertEqual([], active)
        self.assertEqual(
            [
                {
                    "merge_request_id": "merge-request-residue",
                    "source_ref": "runtime/atlas/merge-requests/merge-request-residue.json",
                    "conflict_key": "lineage-1",
                    "status": "superseded_residue",
                    "canonical_merge_request_id": "merge-request-completed",
                    "canonical_source_ref": "runtime/atlas/merge-requests/merge-request-completed.json",
                }
            ],
            residue,
        )
        self.assertEqual([], open_merge_requests(descriptors))

    def test_closure_receipts_emits_missing_sentinel_for_unresolved_close_receipt_ref(self) -> None:
        session_descriptor = _session_manifest_descriptor(
            close_receipt_refs=[
                "runtime/atlas/execution-receipts/receipt-missing.json",
            ]
        )

        self.assertEqual(
            [
                {
                    "source_ref": "runtime/atlas/execution-receipts/receipt-missing.json",
                    "missing": True,
                }
            ],
            closure_receipts([], session_descriptor=session_descriptor),
        )

    def test_closure_receipts_resolves_superseded_close_receipt_ref_to_latest_descriptor(self) -> None:
        original_ref = "runtime/atlas/execution-receipts/receipt-original.json"
        superseding_ref = "runtime/atlas/execution-receipts/receipt-reconciled.json"
        session_descriptor = _session_manifest_descriptor(close_receipt_refs=[original_ref])
        descriptors = [
            _execution_receipt_descriptor(
                receipt_id="receipt-reconciled",
                source_ref=superseding_ref,
                supersedes_receipt_ref=original_ref,
                tool_id="tool-reconciled",
                extension_id="extension-reconciled",
                registry_digest="registry-digest-reconciled",
                reconciled_at="2026-06-16T12:10:00Z",
                executed_at="2026-06-16T12:05:00Z",
                reconciled_by_tool_version="tool-version-2",
                repair_basis_refs=["runtime/atlas/execution-receipts/repair-basis.json"],
            )
        ]

        self.assertEqual(
            [
                {
                    "source_ref": superseding_ref,
                    "original_source_ref": original_ref,
                    "artifact_type": "execution_receipt",
                    "receipt_id": "receipt-reconciled",
                    "tool_id": "tool-reconciled",
                    "extension_id": "extension-reconciled",
                    "result": "succeeded",
                    "registry_digest": "registry-digest-reconciled",
                    "supersedes_receipt_ref": original_ref,
                    "reconciled_at": "2026-06-16T12:10:00Z",
                    "reconciled_by_tool_version": "tool-version-2",
                    "repair_basis_refs": ["runtime/atlas/execution-receipts/repair-basis.json"],
                }
            ],
            closure_receipts(descriptors, session_descriptor=session_descriptor),
        )

    def test_attention_queue_emits_missing_closure_receipt_with_fixed_high_severity(self) -> None:
        queue = attention_queue(
            descriptors=[],
            active_session=None,
            blocked_workers_payload=[],
            open_merge_requests_payload=[],
            closure_receipts_payload=[
                {
                    "source_ref": "runtime/atlas/execution-receipts/receipt-missing.json",
                    "missing": True,
                    "details": {"should": "not-surface"},
                }
            ],
            legacy_compatibility_payload=[],
            trust_surfaces_payload=[],
            working_memory_items=[],
            provenance_alerts={"status": "clear", "item_count": 0, "items": []},
            registry_state={"ok": True},
        )

        self.assertEqual("needs_review", queue["status"])
        self.assertEqual(1, queue["item_count"])
        self.assertEqual("high", queue["highest_severity"])
        self.assertEqual(
            {
                "kind": "missing_closure_receipt",
                "severity": "high",
                "summary": "A session closure receipt ref could not be resolved.",
                "source_ref": "runtime/atlas/execution-receipts/receipt-missing.json",
            },
            queue["items"][0],
        )

    def test_attention_queue_preserves_missing_closure_receipt_when_registry_is_unavailable(self) -> None:
        queue = attention_queue(
            descriptors=[],
            active_session=None,
            blocked_workers_payload=[],
            open_merge_requests_payload=[],
            closure_receipts_payload=[
                {
                    "source_ref": "runtime/atlas/execution-receipts/receipt-missing.json",
                    "missing": True,
                }
            ],
            legacy_compatibility_payload=[],
            trust_surfaces_payload=[],
            working_memory_items=[],
            provenance_alerts={"status": "clear", "item_count": 0, "items": []},
            registry_state={"ok": False, "error": "registry unavailable"},
        )

        self.assertEqual("needs_review", queue["status"])
        self.assertEqual(2, queue["item_count"])
        self.assertEqual("critical", queue["highest_severity"])
        self.assertEqual(
            ["registry_error", "missing_closure_receipt"],
            [item["kind"] for item in queue["items"]],
        )

    def test_attention_queue_preserves_order_for_missing_closure_receipt_and_other_queue_families(self) -> None:
        queue = attention_queue(
            descriptors=[],
            active_session=None,
            blocked_workers_payload=[
                {
                    "worker_id": "worker-2",
                    "assignment_id": "assignment-2",
                    "tool_id": "tool-worker-2",
                    "extension_id": "extension-worker-2",
                    "state": "blocked",
                    "blocked_reason": "waiting on merge",
                    "source_ref": "runtime/atlas/workers/worker-2/status.json",
                }
            ],
            open_merge_requests_payload=[],
            closure_receipts_payload=[
                {
                    "source_ref": "runtime/atlas/execution-receipts/receipt-missing.json",
                    "missing": True,
                }
            ],
            legacy_compatibility_payload=[],
            trust_surfaces_payload=[],
            working_memory_items=[
                {
                    "memory_kind": "initiative",
                    "id": "initiative-open",
                    "title": "Open initiative",
                    "path": "docs/memory/initiatives/initiative-open.json",
                    "status": "active",
                    "metadata": {
                        "attention_summary": "Needs review",
                        "attention_severity": "medium",
                    },
                }
            ],
            provenance_alerts={"status": "clear", "item_count": 0, "items": []},
            registry_state={
                "ok": True,
                "tool_ids": {"tool-worker-2"},
                "extension_ids": {"extension-worker-2"},
            },
        )

        self.assertEqual("needs_review", queue["status"])
        self.assertEqual(3, queue["item_count"])
        self.assertEqual("high", queue["highest_severity"])
        self.assertEqual(
            ["blocked_worker", "missing_closure_receipt", "initiative_open_attention"],
            [item["kind"] for item in queue["items"]],
        )

    def test_attention_queue_preserves_provenance_overflow_when_missing_closure_receipt_is_present(self) -> None:
        queue = attention_queue(
            descriptors=[],
            active_session=None,
            blocked_workers_payload=[],
            open_merge_requests_payload=[],
            closure_receipts_payload=[
                {
                    "source_ref": "runtime/atlas/execution-receipts/receipt-missing.json",
                    "missing": True,
                }
            ],
            legacy_compatibility_payload=[],
            trust_surfaces_payload=[],
            working_memory_items=[],
            provenance_alerts={
                "status": "drift_detected",
                "initiative_item_count": 3,
                "proposal_item_count": 2,
                "item_count": 5,
                "items": [
                    {
                        "kind": "initiative_provenance_drift",
                        "initiative_id": "initiative-zeta",
                        "title": "Zeta",
                        "source_ref": "docs/memory/initiatives/initiative-zeta.json",
                        "stale_attention_refs": ["attention:sha256:zeta"],
                        "missing_file_refs": [],
                    },
                    {
                        "kind": "proposed_session_provenance_drift",
                        "session_id": "session-bravo",
                        "task_id": "task-bravo",
                        "source_ref": "runtime/atlas/proposed-sessions/session-bravo/session.manifest.json",
                        "stale_attention_refs": [],
                        "missing_initiative_ref": "docs/memory/initiatives/missing-bravo.json",
                    },
                    {
                        "kind": "initiative_provenance_drift",
                        "initiative_id": "initiative-alpha",
                        "title": "Alpha",
                        "source_ref": "docs/memory/initiatives/initiative-alpha.json",
                        "stale_attention_refs": [],
                        "missing_file_refs": ["docs/memory/initiatives/missing-alpha.json"],
                    },
                    {
                        "kind": "proposed_session_provenance_drift",
                        "session_id": "session-charlie",
                        "task_id": "task-charlie",
                        "source_ref": "runtime/atlas/proposed-sessions/session-charlie/session.manifest.json",
                        "stale_attention_refs": ["attention:sha256:charlie"],
                        "missing_initiative_ref": None,
                    },
                    {
                        "kind": "initiative_provenance_drift",
                        "initiative_id": "initiative-beta",
                        "title": "Beta",
                        "source_ref": "docs/memory/initiatives/initiative-beta.json",
                        "stale_attention_refs": ["attention:sha256:beta"],
                        "missing_file_refs": [],
                    },
                ],
            },
            registry_state={"ok": True},
        )

        self.assertEqual("needs_review", queue["status"])
        self.assertEqual(5, queue["item_count"])
        self.assertEqual("high", queue["highest_severity"])
        self.assertEqual(
            [
                "initiative_provenance_drift",
                "missing_closure_receipt",
                "proposed_session_provenance_drift",
                "initiative_provenance_drift",
                "provenance_alert_overflow",
            ],
            [item["kind"] for item in queue["items"]],
        )
        self.assertEqual(
            {
                "suppressed_item_count": 2,
                "signal_cap": 3,
                "highest_suppressed_severity": "medium",
                "total_provenance_alert_count": 5,
            },
            queue["items"][4]["details"],
        )

    def test_attention_queue_emits_closure_receipt_issue_with_high_severity_for_failed_result(self) -> None:
        queue = attention_queue(
            descriptors=[],
            active_session=None,
            blocked_workers_payload=[],
            open_merge_requests_payload=[],
            closure_receipts_payload=[
                {
                    "source_ref": "runtime/atlas/execution-receipts/receipt-failed.json",
                    "receipt_id": "receipt-failed",
                    "result": "failed",
                    "details": {"should": "not-surface"},
                }
            ],
            legacy_compatibility_payload=[],
            trust_surfaces_payload=[],
            working_memory_items=[],
            provenance_alerts={"status": "clear", "item_count": 0, "items": []},
            registry_state={"ok": True},
        )

        self.assertEqual("needs_review", queue["status"])
        self.assertEqual(1, queue["item_count"])
        self.assertEqual("high", queue["highest_severity"])
        self.assertEqual(
            {
                "kind": "closure_receipt_issue",
                "severity": "high",
                "summary": "Closure receipt 'receipt-failed' ended with result 'failed'.",
                "source_ref": "runtime/atlas/execution-receipts/receipt-failed.json",
                "details": {
                    "receipt_id": "receipt-failed",
                    "result": "failed",
                },
            },
            queue["items"][0],
        )

    def test_attention_queue_uses_medium_severity_for_non_failed_closure_receipt_issue(self) -> None:
        queue = attention_queue(
            descriptors=[],
            active_session=None,
            blocked_workers_payload=[],
            open_merge_requests_payload=[],
            closure_receipts_payload=[
                {
                    "source_ref": "runtime/atlas/execution-receipts/receipt-canceled.json",
                    "receipt_id": "receipt-canceled",
                    "result": "canceled",
                }
            ],
            legacy_compatibility_payload=[],
            trust_surfaces_payload=[],
            working_memory_items=[],
            provenance_alerts={"status": "clear", "item_count": 0, "items": []},
            registry_state={"ok": True},
        )

        self.assertEqual("needs_review", queue["status"])
        self.assertEqual(1, queue["item_count"])
        self.assertEqual("medium", queue["highest_severity"])
        self.assertEqual("closure_receipt_issue", queue["items"][0]["kind"])
        self.assertEqual("medium", queue["items"][0]["severity"])
        self.assertEqual(
            {
                "receipt_id": "receipt-canceled",
                "result": "canceled",
            },
            queue["items"][0]["details"],
        )

    def test_attention_queue_omits_closure_receipt_issue_for_succeeded_result(self) -> None:
        queue = attention_queue(
            descriptors=[],
            active_session=None,
            blocked_workers_payload=[],
            open_merge_requests_payload=[],
            closure_receipts_payload=[
                {
                    "source_ref": "runtime/atlas/execution-receipts/receipt-succeeded.json",
                    "receipt_id": "receipt-succeeded",
                    "result": "succeeded",
                }
            ],
            legacy_compatibility_payload=[],
            trust_surfaces_payload=[],
            working_memory_items=[],
            provenance_alerts={"status": "clear", "item_count": 0, "items": []},
            registry_state={"ok": True},
        )

        self.assertEqual("clear", queue["status"])
        self.assertEqual(0, queue["item_count"])
        self.assertIsNone(queue["highest_severity"])
        self.assertEqual([], queue["items"])

    def test_attention_queue_preserves_closure_receipt_issue_when_registry_is_unavailable(self) -> None:
        queue = attention_queue(
            descriptors=[],
            active_session=None,
            blocked_workers_payload=[],
            open_merge_requests_payload=[],
            closure_receipts_payload=[
                {
                    "source_ref": "runtime/atlas/execution-receipts/receipt-failed.json",
                    "receipt_id": "receipt-failed",
                    "result": "failed",
                    "tool_id": "missing-tool",
                    "extension_id": "missing-extension",
                }
            ],
            legacy_compatibility_payload=[],
            trust_surfaces_payload=[],
            working_memory_items=[],
            provenance_alerts={"status": "clear", "item_count": 0, "items": []},
            registry_state={"ok": False, "error": "registry unavailable"},
        )

        self.assertEqual("needs_review", queue["status"])
        self.assertEqual(2, queue["item_count"])
        self.assertEqual("critical", queue["highest_severity"])
        self.assertEqual(
            ["registry_error", "closure_receipt_issue"],
            [item["kind"] for item in queue["items"]],
        )

    def test_attention_queue_preserves_order_for_closure_receipt_issue_and_other_queue_families(self) -> None:
        queue = attention_queue(
            descriptors=[],
            active_session=None,
            blocked_workers_payload=[
                {
                    "worker_id": "worker-2",
                    "assignment_id": "assignment-2",
                    "tool_id": "tool-worker-2",
                    "extension_id": "extension-worker-2",
                    "state": "blocked",
                    "blocked_reason": "waiting on merge",
                    "source_ref": "runtime/atlas/workers/worker-2/status.json",
                }
            ],
            open_merge_requests_payload=[],
            closure_receipts_payload=[
                {
                    "source_ref": "runtime/atlas/execution-receipts/receipt-failed.json",
                    "receipt_id": "receipt-failed",
                    "result": "failed",
                }
            ],
            legacy_compatibility_payload=[],
            trust_surfaces_payload=[],
            working_memory_items=[
                {
                    "memory_kind": "initiative",
                    "id": "initiative-open",
                    "title": "Open initiative",
                    "path": "docs/memory/initiatives/initiative-open.json",
                    "status": "active",
                    "metadata": {
                        "attention_summary": "Needs review",
                        "attention_severity": "medium",
                    },
                }
            ],
            provenance_alerts={"status": "clear", "item_count": 0, "items": []},
            registry_state={
                "ok": True,
                "tool_ids": {"tool-worker-2"},
                "extension_ids": {"extension-worker-2"},
            },
        )

        self.assertEqual("needs_review", queue["status"])
        self.assertEqual(3, queue["item_count"])
        self.assertEqual("high", queue["highest_severity"])
        self.assertEqual(
            ["blocked_worker", "closure_receipt_issue", "initiative_open_attention"],
            [item["kind"] for item in queue["items"]],
        )

    def test_attention_queue_preserves_provenance_overflow_when_closure_receipt_issue_is_present(self) -> None:
        queue = attention_queue(
            descriptors=[],
            active_session=None,
            blocked_workers_payload=[],
            open_merge_requests_payload=[],
            closure_receipts_payload=[
                {
                    "source_ref": "runtime/atlas/execution-receipts/receipt-failed.json",
                    "receipt_id": "receipt-failed",
                    "result": "failed",
                }
            ],
            legacy_compatibility_payload=[],
            trust_surfaces_payload=[],
            working_memory_items=[],
            provenance_alerts={
                "status": "drift_detected",
                "initiative_item_count": 3,
                "proposal_item_count": 2,
                "item_count": 5,
                "items": [
                    {
                        "kind": "initiative_provenance_drift",
                        "initiative_id": "initiative-zeta",
                        "title": "Zeta",
                        "source_ref": "docs/memory/initiatives/initiative-zeta.json",
                        "stale_attention_refs": ["attention:sha256:zeta"],
                        "missing_file_refs": [],
                    },
                    {
                        "kind": "proposed_session_provenance_drift",
                        "session_id": "session-bravo",
                        "task_id": "task-bravo",
                        "source_ref": "runtime/atlas/proposed-sessions/session-bravo/session.manifest.json",
                        "stale_attention_refs": [],
                        "missing_initiative_ref": "docs/memory/initiatives/missing-bravo.json",
                    },
                    {
                        "kind": "initiative_provenance_drift",
                        "initiative_id": "initiative-alpha",
                        "title": "Alpha",
                        "source_ref": "docs/memory/initiatives/initiative-alpha.json",
                        "stale_attention_refs": [],
                        "missing_file_refs": ["docs/memory/initiatives/missing-alpha.json"],
                    },
                    {
                        "kind": "proposed_session_provenance_drift",
                        "session_id": "session-charlie",
                        "task_id": "task-charlie",
                        "source_ref": "runtime/atlas/proposed-sessions/session-charlie/session.manifest.json",
                        "stale_attention_refs": ["attention:sha256:charlie"],
                        "missing_initiative_ref": None,
                    },
                    {
                        "kind": "initiative_provenance_drift",
                        "initiative_id": "initiative-beta",
                        "title": "Beta",
                        "source_ref": "docs/memory/initiatives/initiative-beta.json",
                        "stale_attention_refs": ["attention:sha256:beta"],
                        "missing_file_refs": [],
                    },
                ],
            },
            registry_state={"ok": True},
        )

        self.assertEqual("needs_review", queue["status"])
        self.assertEqual(5, queue["item_count"])
        self.assertEqual("high", queue["highest_severity"])
        self.assertEqual(
            [
                "closure_receipt_issue",
                "initiative_provenance_drift",
                "proposed_session_provenance_drift",
                "initiative_provenance_drift",
                "provenance_alert_overflow",
            ],
            [item["kind"] for item in queue["items"]],
        )
        self.assertEqual(
            {
                "suppressed_item_count": 2,
                "signal_cap": 3,
                "highest_suppressed_severity": "medium",
                "total_provenance_alert_count": 5,
            },
            queue["items"][4]["details"],
        )

    def test_attention_queue_emits_blocked_worker_with_admitted_details_and_high_severity(self) -> None:
        queue = attention_queue(
            descriptors=[],
            active_session=None,
            blocked_workers_payload=[
                {
                    "worker_id": "worker-blocked",
                    "assignment_id": "assignment-blocked",
                    "tool_id": "tool-worker-blocked",
                    "extension_id": "extension-worker-blocked",
                    "state": "blocked",
                    "blocked_reason": "waiting on operator input",
                    "registry_digest": "registry-digest-1",
                    "source_ref": "runtime/atlas/workers/worker-blocked/status.json",
                }
            ],
            open_merge_requests_payload=[],
            closure_receipts_payload=[],
            legacy_compatibility_payload=[],
            trust_surfaces_payload=[],
            working_memory_items=[],
            provenance_alerts={"status": "clear", "item_count": 0, "items": []},
            registry_state={
                "ok": True,
                "tool_ids": {"tool-worker-blocked"},
                "extension_ids": {"extension-worker-blocked"},
            },
        )

        self.assertEqual("needs_review", queue["status"])
        self.assertEqual(1, queue["item_count"])
        self.assertEqual("high", queue["highest_severity"])
        self.assertEqual(
            {
                "kind": "blocked_worker",
                "severity": "high",
                "summary": "Worker 'worker-blocked' is blocked.",
                "source_ref": "runtime/atlas/workers/worker-blocked/status.json",
                "details": {
                    "worker_id": "worker-blocked",
                    "assignment_id": "assignment-blocked",
                    "state": "blocked",
                    "blocked_reason": "waiting on operator input",
                },
            },
            queue["items"][0],
        )

    def test_attention_queue_uses_medium_severity_for_paused_blocked_worker(self) -> None:
        queue = attention_queue(
            descriptors=[],
            active_session=None,
            blocked_workers_payload=[
                {
                    "worker_id": "worker-paused",
                    "assignment_id": "assignment-paused",
                    "tool_id": "tool-worker-paused",
                    "extension_id": "extension-worker-paused",
                    "state": "paused",
                    "blocked_reason": "waiting on review",
                    "registry_digest": "registry-digest-1",
                    "source_ref": "runtime/atlas/workers/worker-paused/status.json",
                }
            ],
            open_merge_requests_payload=[],
            closure_receipts_payload=[],
            legacy_compatibility_payload=[],
            trust_surfaces_payload=[],
            working_memory_items=[],
            provenance_alerts={"status": "clear", "item_count": 0, "items": []},
            registry_state={
                "ok": True,
                "tool_ids": {"tool-worker-paused"},
                "extension_ids": {"extension-worker-paused"},
            },
        )

        self.assertEqual("needs_review", queue["status"])
        self.assertEqual("medium", queue["highest_severity"])
        self.assertEqual("medium", queue["items"][0]["severity"])
        self.assertEqual("paused", queue["items"][0]["details"]["state"])

    def test_attention_queue_preserves_blocked_worker_when_registry_is_unavailable(self) -> None:
        queue = attention_queue(
            descriptors=[],
            active_session=None,
            blocked_workers_payload=[
                {
                    "worker_id": "worker-registry-outage",
                    "assignment_id": "assignment-registry-outage",
                    "tool_id": "missing-tool",
                    "extension_id": "missing-extension",
                    "state": "blocked",
                    "blocked_reason": "registry unavailable",
                    "registry_digest": "stale-digest",
                    "source_ref": "runtime/atlas/workers/worker-registry-outage/status.json",
                }
            ],
            open_merge_requests_payload=[],
            closure_receipts_payload=[],
            legacy_compatibility_payload=[],
            trust_surfaces_payload=[],
            working_memory_items=[],
            provenance_alerts={"status": "clear", "item_count": 0, "items": []},
            registry_state={
                "ok": False,
                "error": "registry unavailable",
                "registry_digest": "current-digest",
                "tool_ids": {"known-tool"},
                "extension_ids": {"known-extension"},
            },
        )

        self.assertEqual("needs_review", queue["status"])
        self.assertEqual(["registry_error", "blocked_worker"], [item["kind"] for item in queue["items"]])

    def test_attention_queue_emits_open_merge_request_with_admitted_details_and_high_severity(self) -> None:
        queue = attention_queue(
            descriptors=[],
            active_session=None,
            blocked_workers_payload=[],
            open_merge_requests_payload=[
                {
                    "merge_request_id": "merge-request-open",
                    "tool_id": "tool-merge-request-open",
                    "extension_id": "extension-merge-request-open",
                    "registry_digest": "registry-digest-1",
                    "conflicting_workers": ["worker-a", "worker-b"],
                    "source_ref": "runtime/atlas/merge-requests/merge-request-open.json",
                    "conflict_key": "lineage-1",
                }
            ],
            closure_receipts_payload=[],
            legacy_compatibility_payload=[],
            trust_surfaces_payload=[],
            working_memory_items=[],
            provenance_alerts={"status": "clear", "item_count": 0, "items": []},
            registry_state={
                "ok": True,
                "tool_ids": {"tool-merge-request-open"},
                "extension_ids": {"extension-merge-request-open"},
            },
        )

        self.assertEqual("needs_review", queue["status"])
        self.assertEqual(1, queue["item_count"])
        self.assertEqual("high", queue["highest_severity"])
        self.assertEqual(
            {
                "kind": "open_merge_request",
                "severity": "high",
                "summary": "Merge request 'merge-request-open' remains open.",
                "source_ref": "runtime/atlas/merge-requests/merge-request-open.json",
                "details": {
                    "merge_request_id": "merge-request-open",
                    "conflicting_workers": ["worker-a", "worker-b"],
                },
            },
            queue["items"][0],
        )

    def test_attention_queue_preserves_open_merge_request_when_registry_is_unavailable(self) -> None:
        queue = attention_queue(
            descriptors=[],
            active_session=None,
            blocked_workers_payload=[],
            open_merge_requests_payload=[
                {
                    "merge_request_id": "merge-request-open",
                    "tool_id": "tool-merge-request-open",
                    "extension_id": "extension-merge-request-open",
                    "registry_digest": "registry-digest-1",
                    "conflicting_workers": ["worker-a"],
                    "source_ref": "runtime/atlas/merge-requests/merge-request-open.json",
                    "conflict_key": "lineage-1",
                }
            ],
            closure_receipts_payload=[],
            legacy_compatibility_payload=[],
            trust_surfaces_payload=[],
            working_memory_items=[],
            provenance_alerts={"status": "clear", "item_count": 0, "items": []},
            registry_state={"ok": False, "error": "registry unavailable"},
        )

        self.assertEqual("needs_review", queue["status"])
        self.assertEqual(2, queue["item_count"])
        self.assertEqual(
            ["registry_error", "open_merge_request"],
            [item["kind"] for item in queue["items"]],
        )

    def test_attention_queue_preserves_order_for_blocked_worker_and_other_queue_families(self) -> None:
        queue = attention_queue(
            descriptors=[_conversation_descriptor(turn_id="turn-proposal", action_mode="proposal_required")],
            active_session=None,
            blocked_workers_payload=[
                {
                    "worker_id": "worker-paused",
                    "assignment_id": "assignment-paused",
                    "tool_id": "tool-worker-paused",
                    "extension_id": "extension-worker-paused",
                    "state": "paused",
                    "blocked_reason": "waiting on review",
                    "registry_digest": "registry-digest-1",
                    "source_ref": "runtime/atlas/workers/worker-paused/status.json",
                }
            ],
            open_merge_requests_payload=[],
            closure_receipts_payload=[],
            legacy_compatibility_payload=[],
            trust_surfaces_payload=[],
            working_memory_items=[
                {
                    "memory_kind": "initiative",
                    "id": "initiative-open",
                    "title": "Open initiative",
                    "path": "docs/memory/initiatives/initiative-open.json",
                    "status": "active",
                    "metadata": {
                        "attention_summary": "Needs review",
                        "attention_severity": "medium",
                    },
                }
            ],
            provenance_alerts={"status": "clear", "item_count": 0, "items": []},
            registry_state={
                "ok": True,
                "tool_ids": {"tool-worker-paused"},
                "extension_ids": {"extension-worker-paused"},
            },
        )

        self.assertEqual("needs_review", queue["status"])
        self.assertEqual(3, queue["item_count"])
        self.assertEqual(
            [
                "blocked_worker",
                "conversation_action_request",
                "initiative_open_attention",
            ],
            [item["kind"] for item in queue["items"]],
        )

    def test_attention_queue_preserves_provenance_overflow_when_blocked_worker_is_present(self) -> None:
        queue = attention_queue(
            descriptors=[],
            active_session=None,
            blocked_workers_payload=[
                {
                    "worker_id": "worker-paused",
                    "assignment_id": "assignment-paused",
                    "tool_id": "tool-worker-paused",
                    "extension_id": "extension-worker-paused",
                    "state": "paused",
                    "blocked_reason": "waiting on review",
                    "registry_digest": "registry-digest-1",
                    "source_ref": "runtime/atlas/workers/worker-paused/status.json",
                }
            ],
            open_merge_requests_payload=[],
            closure_receipts_payload=[],
            legacy_compatibility_payload=[],
            trust_surfaces_payload=[],
            working_memory_items=[],
            provenance_alerts={
                "status": "drift_detected",
                "initiative_item_count": 3,
                "proposal_item_count": 2,
                "item_count": 5,
                "items": [
                    {
                        "kind": "initiative_provenance_drift",
                        "initiative_id": "initiative-zeta",
                        "title": "Zeta",
                        "source_ref": "docs/memory/initiatives/initiative-zeta.json",
                        "stale_attention_refs": ["attention:sha256:zeta"],
                        "missing_file_refs": [],
                    },
                    {
                        "kind": "proposed_session_provenance_drift",
                        "session_id": "session-bravo",
                        "task_id": "task-bravo",
                        "source_ref": "runtime/atlas/proposed-sessions/session-bravo/session.manifest.json",
                        "stale_attention_refs": [],
                        "missing_initiative_ref": "docs/memory/initiatives/missing-bravo.json",
                    },
                    {
                        "kind": "initiative_provenance_drift",
                        "initiative_id": "initiative-alpha",
                        "title": "Alpha",
                        "source_ref": "docs/memory/initiatives/initiative-alpha.json",
                        "stale_attention_refs": [],
                        "missing_file_refs": ["docs/memory/initiatives/missing-alpha.json"],
                    },
                    {
                        "kind": "proposed_session_provenance_drift",
                        "session_id": "session-charlie",
                        "task_id": "task-charlie",
                        "source_ref": "runtime/atlas/proposed-sessions/session-charlie/session.manifest.json",
                        "stale_attention_refs": ["attention:sha256:charlie"],
                        "missing_initiative_ref": None,
                    },
                    {
                        "kind": "initiative_provenance_drift",
                        "initiative_id": "initiative-beta",
                        "title": "Beta",
                        "source_ref": "docs/memory/initiatives/initiative-beta.json",
                        "stale_attention_refs": ["attention:sha256:beta"],
                        "missing_file_refs": [],
                    },
                ],
            },
            registry_state={
                "ok": True,
                "tool_ids": {"tool-worker-paused"},
                "extension_ids": {"extension-worker-paused"},
            },
        )

        self.assertEqual("needs_review", queue["status"])
        self.assertEqual(5, queue["item_count"])
        self.assertEqual("high", queue["highest_severity"])
        self.assertEqual(
            [
                "initiative_provenance_drift",
                "proposed_session_provenance_drift",
                "blocked_worker",
                "initiative_provenance_drift",
                "provenance_alert_overflow",
            ],
            [item["kind"] for item in queue["items"]],
        )
        self.assertEqual(
            {
                "suppressed_item_count": 2,
                "signal_cap": 3,
                "highest_suppressed_severity": "medium",
                "total_provenance_alert_count": 5,
            },
            queue["items"][4]["details"],
        )

    def test_attention_queue_preserves_provenance_overflow_when_open_merge_request_is_present(self) -> None:
        queue = attention_queue(
            descriptors=[],
            active_session=None,
            blocked_workers_payload=[],
            open_merge_requests_payload=[
                {
                    "merge_request_id": "merge-request-open",
                    "tool_id": "tool-merge-request-open",
                    "extension_id": "extension-merge-request-open",
                    "registry_digest": "registry-digest-1",
                    "conflicting_workers": ["worker-a"],
                    "source_ref": "runtime/atlas/merge-requests/merge-request-open.json",
                    "conflict_key": "lineage-1",
                }
            ],
            closure_receipts_payload=[],
            legacy_compatibility_payload=[],
            trust_surfaces_payload=[],
            working_memory_items=[],
            provenance_alerts={
                "status": "drift_detected",
                "initiative_item_count": 3,
                "proposal_item_count": 2,
                "item_count": 5,
                "items": [
                    {
                        "kind": "initiative_provenance_drift",
                        "initiative_id": "initiative-zeta",
                        "source_ref": "docs/memory/initiatives/initiative-zeta.json",
                        "stale_attention_refs": ["attention:sha256:zeta"],
                        "missing_file_refs": [],
                    },
                    {
                        "kind": "proposed_session_provenance_drift",
                        "session_id": "session-bravo",
                        "task_id": "task-bravo",
                        "source_ref": "runtime/atlas/proposed-sessions/session-bravo/session.manifest.json",
                        "stale_attention_refs": [],
                        "missing_initiative_ref": "docs/memory/initiatives/missing-bravo.json",
                    },
                    {
                        "kind": "initiative_provenance_drift",
                        "initiative_id": "initiative-alpha",
                        "source_ref": "docs/memory/initiatives/initiative-alpha.json",
                        "stale_attention_refs": [],
                        "missing_file_refs": ["docs/memory/initiatives/missing-alpha.json"],
                    },
                    {
                        "kind": "proposed_session_provenance_drift",
                        "session_id": "session-charlie",
                        "task_id": "task-charlie",
                        "source_ref": "runtime/atlas/proposed-sessions/session-charlie/session.manifest.json",
                        "stale_attention_refs": ["attention:sha256:charlie"],
                        "missing_initiative_ref": None,
                    },
                    {
                        "kind": "initiative_provenance_drift",
                        "initiative_id": "initiative-beta",
                        "source_ref": "docs/memory/initiatives/initiative-beta.json",
                        "stale_attention_refs": ["attention:sha256:beta"],
                        "missing_file_refs": [],
                    },
                ],
            },
            registry_state={
                "ok": True,
                "tool_ids": {"tool-merge-request-open"},
                "extension_ids": {"extension-merge-request-open"},
            },
        )

        self.assertEqual("needs_review", queue["status"])
        self.assertEqual(5, queue["item_count"])
        self.assertEqual(
            [
                "initiative_provenance_drift",
                "open_merge_request",
                "proposed_session_provenance_drift",
                "initiative_provenance_drift",
                "provenance_alert_overflow",
            ],
            [item["kind"] for item in queue["items"]],
        )
        self.assertEqual(
            {
                "suppressed_item_count": 2,
                "signal_cap": 3,
                "highest_suppressed_severity": "medium",
                "total_provenance_alert_count": 5,
            },
            queue["items"][4]["details"],
        )

    def test_attention_queue_emits_quarantined_trust_surface_for_untrusted_knowledge_catalog(self) -> None:
        descriptors = [
            _knowledge_catalog_descriptor(
                archive_id="archive-untrusted",
                trust_class="untrusted",
                source_ref="data/knowledge/archive-untrusted.descriptor.json",
                indexing_profile="metadata_only",
                promotion_status="quarantined",
            )
        ]

        queue = attention_queue(
            descriptors=descriptors,
            active_session=None,
            blocked_workers_payload=[],
            open_merge_requests_payload=[],
            closure_receipts_payload=[],
            legacy_compatibility_payload=[],
            trust_surfaces_payload=trust_surfaces(descriptors),
            working_memory_items=[],
            provenance_alerts={"status": "clear", "item_count": 0, "items": []},
            registry_state={"ok": True},
        )

        self.assertEqual("needs_review", queue["status"])
        self.assertEqual(1, queue["item_count"])
        self.assertEqual("medium", queue["highest_severity"])
        self.assertEqual(
            {
                "kind": "quarantined_trust_surface",
                "severity": "medium",
                "summary": "Knowledge surface 'archive-untrusted' remains untrusted.",
                "source_ref": "data/knowledge/archive-untrusted.descriptor.json",
                "details": {
                    "archive_id": "archive-untrusted",
                    "indexing_profile": "metadata_only",
                    "promotion_status": "quarantined",
                },
            },
            queue["items"][0],
        )

    def test_attention_queue_omits_non_qualifying_descriptor_from_quarantine_family(self) -> None:
        descriptors = [
            {
                "artifact_type": "session_manifest",
                "source_ref": "runtime/atlas/sessions/session-proof/session.manifest.json",
                "identity": {"session_id": "session-proof"},
                "state": {"session_state": "proposed"},
            }
        ]

        queue = attention_queue(
            descriptors=descriptors,
            active_session=None,
            blocked_workers_payload=[],
            open_merge_requests_payload=[],
            closure_receipts_payload=[],
            legacy_compatibility_payload=[],
            trust_surfaces_payload=trust_surfaces(descriptors),
            working_memory_items=[],
            provenance_alerts={"status": "clear", "item_count": 0, "items": []},
            registry_state={"ok": True},
        )

        self.assertEqual([], trust_surfaces(descriptors))
        self.assertEqual("clear", queue["status"])
        self.assertEqual(0, queue["item_count"])
        self.assertEqual([], queue["items"])

    def test_attention_queue_omits_trust_surface_that_is_not_untrusted(self) -> None:
        descriptors = [
            _knowledge_catalog_descriptor(
                archive_id="archive-restricted",
                trust_class="restricted",
                source_ref="data/knowledge/archive-restricted.descriptor.json",
                promotion_status="review_pending",
            )
        ]
        trust_surfaces_payload = trust_surfaces(descriptors)
        trust_posture = trust_posture_summary(trust_surfaces_payload)

        queue = attention_queue(
            descriptors=descriptors,
            active_session=None,
            blocked_workers_payload=[],
            open_merge_requests_payload=[],
            closure_receipts_payload=[],
            legacy_compatibility_payload=[],
            trust_surfaces_payload=trust_surfaces_payload,
            working_memory_items=[],
            provenance_alerts={"status": "clear", "item_count": 0, "items": []},
            registry_state={"ok": True},
        )

        self.assertEqual("restricted", trust_posture["status"])
        self.assertEqual(1, trust_posture["item_count"])
        self.assertEqual("restricted", trust_posture["items"][0]["trust_class"])
        self.assertEqual("clear", queue["status"])
        self.assertEqual(0, queue["item_count"])
        self.assertEqual([], queue["items"])

    def test_trust_surfaces_is_empty_without_qualifying_descriptors(self) -> None:
        descriptors = [
            {
                "artifact_type": "session_manifest",
                "source_ref": "runtime/atlas/sessions/session-proof/session.manifest.json",
                "identity": {"session_id": "session-proof"},
                "state": {"session_state": "proposed"},
            },
            _knowledge_catalog_descriptor(
                archive_id="archive-trusted",
                trust_class="trusted",
                source_ref="data/knowledge/archive-trusted.descriptor.json",
                indexing_profile="full_text",
                promotion_status="promoted",
            ),
        ]

        self.assertEqual([], trust_surfaces(descriptors))

    def test_trust_surfaces_projects_exact_admitted_fields_for_restricted_surface(self) -> None:
        descriptors = [
            _knowledge_catalog_descriptor(
                archive_id="archive-restricted",
                trust_class="restricted",
                source_ref="data/knowledge/archive-restricted.descriptor.json",
                indexing_profile="metadata_only",
                promotion_status="review_pending",
            )
        ]

        self.assertEqual(
            [
                {
                    "archive_id": "archive-restricted",
                    "knowledge_ref": "knowledge:archive-restricted",
                    "trust_class": "restricted",
                    "indexing_profile": "metadata_only",
                    "promotion_status": "review_pending",
                    "source_ref": "data/knowledge/archive-restricted.descriptor.json",
                }
            ],
            trust_surfaces(descriptors),
        )

    def test_trust_surfaces_projects_exact_admitted_fields_for_untrusted_surface(self) -> None:
        descriptors = [
            _knowledge_catalog_descriptor(
                archive_id="archive-untrusted",
                trust_class="untrusted",
                source_ref="data/knowledge/archive-untrusted.descriptor.json",
                indexing_profile="metadata_only",
                promotion_status="quarantined",
            )
        ]

        self.assertEqual(
            [
                {
                    "archive_id": "archive-untrusted",
                    "knowledge_ref": "knowledge:archive-untrusted",
                    "trust_class": "untrusted",
                    "indexing_profile": "metadata_only",
                    "promotion_status": "quarantined",
                    "source_ref": "data/knowledge/archive-untrusted.descriptor.json",
                }
            ],
            trust_surfaces(descriptors),
        )

    def test_trust_surfaces_preserves_deterministic_ordering(self) -> None:
        descriptors = [
            _knowledge_catalog_descriptor(
                archive_id="archive-zulu",
                trust_class="untrusted",
                source_ref="data/knowledge/archive-zulu.descriptor.json",
                indexing_profile="metadata_only",
                promotion_status="quarantined",
            ),
            _knowledge_catalog_descriptor(
                archive_id="archive-bravo",
                trust_class="restricted",
                source_ref="data/knowledge/archive-bravo.descriptor.json",
                indexing_profile="metadata_only",
                promotion_status="review_pending",
            ),
            _knowledge_catalog_descriptor(
                archive_id="archive-alpha",
                trust_class="restricted",
                source_ref="data/knowledge/archive-alpha.descriptor.json",
                indexing_profile="metadata_only",
                promotion_status="review_pending",
            ),
        ]

        self.assertEqual(
            ["archive-alpha", "archive-bravo", "archive-zulu"],
            [item["archive_id"] for item in trust_surfaces(descriptors)],
        )

    def test_trust_posture_summary_is_clear_without_admitted_trust_surfaces(self) -> None:
        descriptors = [
            _knowledge_catalog_descriptor(
                archive_id="archive-trusted",
                trust_class="trusted",
                source_ref="data/knowledge/archive-trusted.descriptor.json",
                indexing_profile="full_text",
                promotion_status="promoted",
            )
        ]

        trust_surfaces_payload = trust_surfaces(descriptors)
        trust_posture = trust_posture_summary(trust_surfaces_payload)

        self.assertEqual([], trust_surfaces_payload)
        self.assertEqual(
            {
                "status": "clear",
                "item_count": 0,
                "untrusted_item_count": 0,
                "metadata_only_item_count": 0,
                "items": [],
            },
            trust_posture,
        )

    def test_trust_posture_summary_marks_restricted_surface_as_metadata_only(self) -> None:
        descriptors = [
            _knowledge_catalog_descriptor(
                archive_id="archive-restricted",
                trust_class="restricted",
                source_ref="data/knowledge/archive-restricted.descriptor.json",
                indexing_profile="metadata_only",
                promotion_status="review_pending",
            )
        ]

        trust_posture = trust_posture_summary(trust_surfaces(descriptors))

        self.assertEqual("restricted", trust_posture["status"])
        self.assertEqual(1, trust_posture["item_count"])
        self.assertEqual(0, trust_posture["untrusted_item_count"])
        self.assertEqual(1, trust_posture["metadata_only_item_count"])
        self.assertEqual("restricted", trust_posture["items"][0]["trust_class"])
        self.assertEqual("metadata_only", trust_posture["items"][0]["read_mode"])

    def test_trust_posture_summary_projects_exact_admitted_item_fields_for_untrusted_surface(self) -> None:
        trust_posture = trust_posture_summary(
            [
                {
                    "archive_id": "archive-untrusted",
                    "knowledge_ref": "knowledge:archive-untrusted",
                    "trust_class": "untrusted",
                    "indexing_profile": "metadata_only",
                    "promotion_status": "quarantined",
                    "source_ref": "data/knowledge/archive-untrusted.descriptor.json",
                    "unexpected_field": "ignored",
                }
            ]
        )

        self.assertEqual("restricted", trust_posture["status"])
        self.assertEqual(1, trust_posture["item_count"])
        self.assertEqual(1, trust_posture["untrusted_item_count"])
        self.assertEqual(1, trust_posture["metadata_only_item_count"])
        self.assertEqual(
            {
                "archive_id": "archive-untrusted",
                "knowledge_ref": "knowledge:archive-untrusted",
                "trust_class": "untrusted",
                "indexing_profile": "metadata_only",
                "promotion_status": "quarantined",
                "source_ref": "data/knowledge/archive-untrusted.descriptor.json",
                "read_mode": "metadata_only",
            },
            trust_posture["items"][0],
        )

    def test_trust_posture_summary_preserves_inherited_mixed_surface_order(self) -> None:
        trust_surfaces_payload = [
            {
                "archive_id": "archive-restricted",
                "knowledge_ref": "knowledge:archive-restricted",
                "trust_class": "restricted",
                "indexing_profile": "metadata_only",
                "promotion_status": "review_pending",
                "source_ref": "data/knowledge/archive-restricted.descriptor.json",
            },
            {
                "archive_id": "archive-untrusted",
                "knowledge_ref": "knowledge:archive-untrusted",
                "trust_class": "untrusted",
                "indexing_profile": "metadata_only",
                "promotion_status": "quarantined",
                "source_ref": "data/knowledge/archive-untrusted.descriptor.json",
            },
        ]

        trust_posture = trust_posture_summary(trust_surfaces_payload)

        self.assertEqual(
            ["archive-restricted", "archive-untrusted"],
            [item["archive_id"] for item in trust_posture["items"]],
        )
        self.assertEqual(
            [item["archive_id"] for item in trust_surfaces_payload],
            [item["archive_id"] for item in trust_posture["items"]],
        )

    def test_attention_queue_preserves_order_for_provenance_and_quarantine_items(self) -> None:
        descriptors = [
            _knowledge_catalog_descriptor(
                archive_id="archive-untrusted",
                trust_class="untrusted",
                source_ref="data/knowledge/archive-untrusted.descriptor.json",
            )
        ]

        queue = attention_queue(
            descriptors=descriptors,
            active_session=None,
            blocked_workers_payload=[],
            open_merge_requests_payload=[],
            closure_receipts_payload=[],
            legacy_compatibility_payload=[],
            trust_surfaces_payload=trust_surfaces(descriptors),
            working_memory_items=[],
            provenance_alerts={
                "status": "drift_detected",
                "initiative_item_count": 1,
                "proposal_item_count": 0,
                "item_count": 1,
                "items": [
                    {
                        "kind": "initiative_provenance_drift",
                        "initiative_id": "initiative-proof",
                        "title": "Proof",
                        "source_ref": "docs/memory/initiatives/initiative-proof.json",
                        "stale_attention_refs": [],
                        "missing_file_refs": ["docs/memory/initiatives/missing.json"],
                    }
                ],
            },
            registry_state={"ok": True},
        )

        self.assertEqual("needs_review", queue["status"])
        self.assertEqual(2, queue["item_count"])
        self.assertEqual("high", queue["highest_severity"])
        self.assertEqual(
            ["initiative_provenance_drift", "quarantined_trust_surface"],
            [item["kind"] for item in queue["items"]],
        )

    def test_attention_queue_preserves_order_for_quarantine_and_other_queue_families(self) -> None:
        descriptors = [
            _conversation_descriptor(turn_id="turn-proposal", action_mode="proposal_required"),
            _knowledge_catalog_descriptor(
                archive_id="archive-untrusted",
                trust_class="untrusted",
                source_ref="data/knowledge/archive-untrusted.descriptor.json",
            ),
        ]

        queue = attention_queue(
            descriptors=descriptors,
            active_session=None,
            blocked_workers_payload=[],
            open_merge_requests_payload=[],
            closure_receipts_payload=[],
            legacy_compatibility_payload=[],
            trust_surfaces_payload=trust_surfaces(descriptors),
            working_memory_items=[
                {
                    "memory_kind": "initiative",
                    "id": "initiative-open",
                    "title": "Open initiative",
                    "path": "docs/memory/initiatives/initiative-open.json",
                    "status": "active",
                    "metadata": {
                        "attention_summary": "Needs review",
                        "attention_severity": "medium",
                    },
                }
            ],
            provenance_alerts={"status": "clear", "item_count": 0, "items": []},
            registry_state={"ok": True},
        )

        self.assertEqual("needs_review", queue["status"])
        self.assertEqual(3, queue["item_count"])
        self.assertEqual(
            [
                "conversation_action_request",
                "initiative_open_attention",
                "quarantined_trust_surface",
            ],
            [item["kind"] for item in queue["items"]],
        )

    def test_attention_queue_preserves_provenance_overflow_when_quarantine_item_is_present(self) -> None:
        descriptors = [
            _knowledge_catalog_descriptor(
                archive_id="archive-untrusted",
                trust_class="untrusted",
                source_ref="data/knowledge/archive-untrusted.descriptor.json",
            )
        ]

        queue = attention_queue(
            descriptors=descriptors,
            active_session=None,
            blocked_workers_payload=[],
            open_merge_requests_payload=[],
            closure_receipts_payload=[],
            legacy_compatibility_payload=[],
            trust_surfaces_payload=trust_surfaces(descriptors),
            working_memory_items=[],
            provenance_alerts={
                "status": "drift_detected",
                "initiative_item_count": 3,
                "proposal_item_count": 2,
                "item_count": 5,
                "items": [
                    {
                        "kind": "initiative_provenance_drift",
                        "initiative_id": "initiative-zeta",
                        "title": "Zeta",
                        "source_ref": "docs/memory/initiatives/initiative-zeta.json",
                        "stale_attention_refs": ["attention:sha256:zeta"],
                        "missing_file_refs": [],
                    },
                    {
                        "kind": "proposed_session_provenance_drift",
                        "session_id": "session-bravo",
                        "task_id": "task-bravo",
                        "source_ref": "runtime/atlas/proposed-sessions/session-bravo/session.manifest.json",
                        "stale_attention_refs": [],
                        "missing_initiative_ref": "docs/memory/initiatives/missing-bravo.json",
                    },
                    {
                        "kind": "initiative_provenance_drift",
                        "initiative_id": "initiative-alpha",
                        "title": "Alpha",
                        "source_ref": "docs/memory/initiatives/initiative-alpha.json",
                        "stale_attention_refs": [],
                        "missing_file_refs": ["docs/memory/initiatives/missing-alpha.json"],
                    },
                    {
                        "kind": "proposed_session_provenance_drift",
                        "session_id": "session-charlie",
                        "task_id": "task-charlie",
                        "source_ref": "runtime/atlas/proposed-sessions/session-charlie/session.manifest.json",
                        "stale_attention_refs": ["attention:sha256:charlie"],
                        "missing_initiative_ref": None,
                    },
                    {
                        "kind": "initiative_provenance_drift",
                        "initiative_id": "initiative-beta",
                        "title": "Beta",
                        "source_ref": "docs/memory/initiatives/initiative-beta.json",
                        "stale_attention_refs": ["attention:sha256:beta"],
                        "missing_file_refs": [],
                    },
                ],
            },
            registry_state={"ok": True},
        )

        self.assertEqual("needs_review", queue["status"])
        self.assertEqual(5, queue["item_count"])
        self.assertEqual("high", queue["highest_severity"])
        self.assertEqual(
            [
                "initiative_provenance_drift",
                "proposed_session_provenance_drift",
                "initiative_provenance_drift",
                "provenance_alert_overflow",
                "quarantined_trust_surface",
            ],
            [item["kind"] for item in queue["items"]],
        )
        self.assertEqual(
            {
                "suppressed_item_count": 2,
                "signal_cap": 3,
                "highest_suppressed_severity": "medium",
                "total_provenance_alert_count": 5,
            },
            queue["items"][3]["details"],
        )

    def test_attention_queue_preserves_provenance_overflow_when_session_failed_is_present(self) -> None:
        queue = attention_queue(
            descriptors=[],
            active_session={
                "session_id": "session-failed-overflow",
                "task_id": "task-failed-overflow",
                "session_state": "failed",
                "final_status": "running",
                "source_ref": "runtime/atlas/sessions/session-failed-overflow/session.manifest.json",
            },
            blocked_workers_payload=[],
            open_merge_requests_payload=[],
            closure_receipts_payload=[],
            legacy_compatibility_payload=[],
            trust_surfaces_payload=[],
            working_memory_items=[],
            provenance_alerts={
                "status": "drift_detected",
                "initiative_item_count": 3,
                "proposal_item_count": 2,
                "item_count": 5,
                "items": [
                    {
                        "kind": "initiative_provenance_drift",
                        "initiative_id": "initiative-zeta",
                        "title": "Zeta",
                        "source_ref": "docs/memory/initiatives/initiative-zeta.json",
                        "stale_attention_refs": ["attention:sha256:zeta"],
                        "missing_file_refs": [],
                    },
                    {
                        "kind": "proposed_session_provenance_drift",
                        "session_id": "session-bravo",
                        "task_id": "task-bravo",
                        "source_ref": "runtime/atlas/proposed-sessions/session-bravo/session.manifest.json",
                        "stale_attention_refs": [],
                        "missing_initiative_ref": "docs/memory/initiatives/missing-bravo.json",
                    },
                    {
                        "kind": "initiative_provenance_drift",
                        "initiative_id": "initiative-alpha",
                        "title": "Alpha",
                        "source_ref": "docs/memory/initiatives/initiative-alpha.json",
                        "stale_attention_refs": [],
                        "missing_file_refs": ["docs/memory/initiatives/missing-alpha.json"],
                    },
                    {
                        "kind": "proposed_session_provenance_drift",
                        "session_id": "session-charlie",
                        "task_id": "task-charlie",
                        "source_ref": "runtime/atlas/proposed-sessions/session-charlie/session.manifest.json",
                        "stale_attention_refs": ["attention:sha256:charlie"],
                        "missing_initiative_ref": None,
                    },
                    {
                        "kind": "initiative_provenance_drift",
                        "initiative_id": "initiative-kappa",
                        "title": "Kappa",
                        "source_ref": "docs/memory/initiatives/initiative-kappa.json",
                        "stale_attention_refs": ["attention:sha256:kappa"],
                        "missing_file_refs": [],
                    },
                ],
            },
            registry_state={"ok": True},
        )

        self.assertEqual("needs_review", queue["status"])
        self.assertEqual(5, queue["item_count"])
        self.assertEqual(
            [
                "initiative_provenance_drift",
                "proposed_session_provenance_drift",
                "session_failed",
                "initiative_provenance_drift",
                "provenance_alert_overflow",
            ],
            [item["kind"] for item in queue["items"]],
        )
        self.assertEqual(
            {
                "suppressed_item_count": 2,
                "signal_cap": 3,
                "highest_suppressed_severity": "medium",
                "total_provenance_alert_count": 5,
            },
            queue["items"][4]["details"],
        )

    def test_proposal_only_state_filters_request_items_and_preserves_fields(self) -> None:
        proposal_only = proposal_only_state(
            {
                "items": [
                    {
                        "kind": "initiative_provenance_drift",
                        "severity": "high",
                        "summary": "Ignore me",
                        "source_ref": "docs/memory/initiatives/initiative-proof.json",
                        "details": {},
                    },
                    {
                        "kind": "conversation_action_request",
                        "severity": "medium",
                        "summary": "Conversation turn 'turn-proposal' requested a governed action proposal.",
                        "source_ref": "runtime/atlas/conversations/conversation-1/turns/turn-proposal.json",
                        "details": {
                            "conversation_id": "conversation-1",
                            "turn_id": "turn-proposal",
                            "intent": "write_receipt",
                        },
                    },
                ]
            }
        )

        self.assertEqual("pending", proposal_only["status"])
        self.assertEqual(1, proposal_only["item_count"])
        self.assertEqual(
            {
                "summary": "Conversation turn 'turn-proposal' requested a governed action proposal.",
                "severity": "medium",
                "source_ref": "runtime/atlas/conversations/conversation-1/turns/turn-proposal.json",
                "conversation_id": "conversation-1",
                "turn_id": "turn-proposal",
                "intent": "write_receipt",
            },
            proposal_only["items"][0],
        )

    def test_proposal_only_state_is_clear_without_request_items(self) -> None:
        proposal_only = proposal_only_state(
            {
                "items": [
                    {
                        "kind": "initiative_open_attention",
                        "severity": "medium",
                        "summary": "Open initiative",
                        "source_ref": "docs/memory/initiatives/initiative-open.json",
                        "details": {},
                    }
                ]
            }
        )

        self.assertEqual("clear", proposal_only["status"])
        self.assertEqual(0, proposal_only["item_count"])
        self.assertEqual([], proposal_only["items"])

    def test_proposal_only_state_caps_items_at_five(self) -> None:
        queue_items = []
        for index in range(6):
            queue_items.append(
                {
                    "kind": "conversation_action_request",
                    "severity": "medium",
                    "summary": f"Conversation turn 'turn-{index}' requested a governed action proposal.",
                    "source_ref": f"runtime/atlas/conversations/conversation-1/turns/turn-{index}.json",
                    "details": {
                        "conversation_id": "conversation-1",
                        "turn_id": f"turn-{index}",
                        "intent": "write_receipt",
                    },
                }
            )

        proposal_only = proposal_only_state({"items": queue_items})

        self.assertEqual("pending", proposal_only["status"])
        self.assertEqual(6, proposal_only["item_count"])
        self.assertEqual(5, len(proposal_only["items"]))
        self.assertEqual("turn-0", proposal_only["items"][0]["turn_id"])
        self.assertEqual("turn-4", proposal_only["items"][-1]["turn_id"])

    def test_render_status_payload_surfaces_proposal_only_projection(self) -> None:
        with TemporaryDirectory() as temp_dir:
            descriptor_root = Path(temp_dir)
            (descriptor_root / "placeholder.json").write_text("{}", encoding="utf-8")
            patch_specs = [
                (
                    "ops.cortex.render_status.load_descriptors",
                    [_conversation_descriptor(turn_id="turn-proposal", action_mode="proposal_required")],
                ),
                ("ops.cortex.render_status.load_registry_state", {"ok": True}),
                ("ops.cortex.render_status.choose_latest_session", None),
                ("ops.cortex.render_status.session_overview", None),
                ("ops.cortex.render_status.blocked_workers", []),
                ("ops.cortex.render_status.classify_merge_requests", ([], [])),
                ("ops.cortex.render_status.closure_receipts", []),
                ("ops.cortex.render_status.execution_receipt_residue_records", []),
                ("ops.cortex.render_status.governed_writes", []),
                ("ops.cortex.render_status.legacy_compatibility_surfaces", []),
                ("ops.cortex.render_status.trust_surfaces", []),
                ("ops.cortex.render_status.trust_posture_summary", {}),
                ("ops.cortex.render_status.working_memory_summary", {"_items": [], "initiatives": {}}),
                ("ops.cortex.render_status.provenance_alert_summary", {"status": "clear", "item_count": 0, "items": []}),
                ("ops.cortex.render_status.conversation_summary", {}),
                ("ops.cortex.render_status.build_canonical_lockfile_artifacts", {}),
                ("ops.cortex.render_status.repo_inventory_summary_from_lock", {"items": []}),
                ("ops.cortex.render_status.lock_worktree_hygiene", {"status": "frozen"}),
                ("ops.cortex.render_status.registry_summary", {}),
                ("ops.cortex.render_status.artifact_inventory", {}),
                ("ops.cortex.render_status.world_model_state", {}),
            ]
            with ExitStack() as stack:
                for target, value in patch_specs:
                    stack.enter_context(patch(target, return_value=value))
                payload = render_status_payload(descriptor_root)

        self.assertEqual("needs_review", payload["attention_queue"]["status"])
        self.assertEqual("pending", payload["proposal_only"]["status"])
        self.assertEqual(1, payload["proposal_only"]["item_count"])
        self.assertEqual("turn-proposal", payload["proposal_only"]["items"][0]["turn_id"])

    def test_render_status_payload_preserves_quarantine_attention_queue_handoff(self) -> None:
        descriptors = [
            _knowledge_catalog_descriptor(
                archive_id="archive-untrusted",
                trust_class="untrusted",
                source_ref="data/knowledge/archive-untrusted.descriptor.json",
            )
        ]

        with TemporaryDirectory() as temp_dir:
            descriptor_root = Path(temp_dir)
            (descriptor_root / "placeholder.json").write_text("{}", encoding="utf-8")
            patch_specs = [
                ("ops.cortex.render_status.load_descriptors", descriptors),
                ("ops.cortex.render_status.load_registry_state", {"ok": True}),
                ("ops.cortex.render_status.choose_latest_session", None),
                ("ops.cortex.render_status.session_overview", None),
                ("ops.cortex.render_status.blocked_workers", []),
                ("ops.cortex.render_status.classify_merge_requests", ([], [])),
                ("ops.cortex.render_status.closure_receipts", []),
                ("ops.cortex.render_status.execution_receipt_residue_records", []),
                ("ops.cortex.render_status.governed_writes", []),
                ("ops.cortex.render_status.legacy_compatibility_surfaces", []),
                ("ops.cortex.render_status.working_memory_summary", {"_items": [], "initiatives": {}}),
                ("ops.cortex.render_status.provenance_alert_summary", {"status": "clear", "item_count": 0, "items": []}),
                ("ops.cortex.render_status.conversation_summary", {}),
                ("ops.cortex.render_status.build_canonical_lockfile_artifacts", {}),
                ("ops.cortex.render_status.repo_inventory_summary_from_lock", {"items": []}),
                ("ops.cortex.render_status.lock_worktree_hygiene", {"status": "frozen"}),
                ("ops.cortex.render_status.registry_summary", {}),
                ("ops.cortex.render_status.artifact_inventory", {}),
                ("ops.cortex.render_status.world_model_state", {}),
            ]
            with ExitStack() as stack:
                for target, value in patch_specs:
                    stack.enter_context(patch(target, return_value=value))
                payload = render_status_payload(descriptor_root)

        self.assertEqual("needs_review", payload["attention_queue"]["status"])
        self.assertEqual(1, payload["attention_queue"]["item_count"])
        self.assertEqual("quarantined_trust_surface", payload["attention_queue"]["items"][0]["kind"])
        self.assertEqual("restricted", payload["trust_posture"]["status"])
        self.assertEqual(1, payload["trust_posture"]["untrusted_item_count"])
        self.assertEqual("archive-untrusted", payload["attention_queue"]["items"][0]["details"]["archive_id"])

    def test_render_status_payload_separates_restricted_trust_posture_from_clear_attention_queue(self) -> None:
        descriptors = [
            _knowledge_catalog_descriptor(
                archive_id="archive-restricted",
                trust_class="restricted",
                source_ref="data/knowledge/archive-restricted.descriptor.json",
                indexing_profile="metadata_only",
                promotion_status="review_pending",
            )
        ]

        with TemporaryDirectory() as temp_dir:
            descriptor_root = Path(temp_dir)
            (descriptor_root / "placeholder.json").write_text("{}", encoding="utf-8")
            patch_specs = [
                ("ops.cortex.render_status.load_descriptors", descriptors),
                ("ops.cortex.render_status.load_registry_state", {"ok": True}),
                ("ops.cortex.render_status.choose_latest_session", None),
                ("ops.cortex.render_status.session_overview", None),
                ("ops.cortex.render_status.blocked_workers", []),
                ("ops.cortex.render_status.classify_merge_requests", ([], [])),
                ("ops.cortex.render_status.closure_receipts", []),
                ("ops.cortex.render_status.execution_receipt_residue_records", []),
                ("ops.cortex.render_status.governed_writes", []),
                ("ops.cortex.render_status.legacy_compatibility_surfaces", []),
                ("ops.cortex.render_status.working_memory_summary", {"_items": [], "initiatives": {}}),
                ("ops.cortex.render_status.provenance_alert_summary", {"status": "clear", "item_count": 0, "items": []}),
                ("ops.cortex.render_status.conversation_summary", {}),
                ("ops.cortex.render_status.build_canonical_lockfile_artifacts", {}),
                ("ops.cortex.render_status.repo_inventory_summary_from_lock", {"items": []}),
                ("ops.cortex.render_status.lock_worktree_hygiene", {"status": "frozen"}),
                ("ops.cortex.render_status.registry_summary", {}),
                ("ops.cortex.render_status.artifact_inventory", {}),
                ("ops.cortex.render_status.world_model_state", {}),
            ]
            with ExitStack() as stack:
                for target, value in patch_specs:
                    stack.enter_context(patch(target, return_value=value))
                payload = render_status_payload(descriptor_root)

        self.assertEqual(
            {
                "status": "restricted",
                "item_count": 1,
                "untrusted_item_count": 0,
                "metadata_only_item_count": 1,
                "items": [
                    {
                        "archive_id": "archive-restricted",
                        "knowledge_ref": "knowledge:archive-restricted",
                        "trust_class": "restricted",
                        "indexing_profile": "metadata_only",
                        "promotion_status": "review_pending",
                        "source_ref": "data/knowledge/archive-restricted.descriptor.json",
                        "read_mode": "metadata_only",
                    }
                ],
            },
            payload["trust_posture"],
        )
        self.assertEqual("clear", payload["attention_queue"]["status"])
        self.assertEqual(0, payload["attention_queue"]["item_count"])
        self.assertEqual([], payload["attention_queue"]["items"])

    def test_render_status_payload_mirrors_trust_posture_into_slices_handoff(self) -> None:
        descriptors = [
            _knowledge_catalog_descriptor(
                archive_id="archive-untrusted",
                trust_class="untrusted",
                source_ref="data/knowledge/archive-untrusted.descriptor.json",
            ),
            _knowledge_catalog_descriptor(
                archive_id="archive-restricted",
                trust_class="restricted",
                source_ref="data/knowledge/archive-restricted.descriptor.json",
                promotion_status="review_pending",
            ),
        ]

        with TemporaryDirectory() as temp_dir:
            descriptor_root = Path(temp_dir)
            (descriptor_root / "placeholder.json").write_text("{}", encoding="utf-8")
            patch_specs = [
                ("ops.cortex.render_status.load_descriptors", descriptors),
                ("ops.cortex.render_status.load_registry_state", {"ok": True}),
                ("ops.cortex.render_status.choose_latest_session", None),
                ("ops.cortex.render_status.session_overview", None),
                ("ops.cortex.render_status.blocked_workers", []),
                ("ops.cortex.render_status.classify_merge_requests", ([], [])),
                ("ops.cortex.render_status.closure_receipts", []),
                ("ops.cortex.render_status.execution_receipt_residue_records", []),
                ("ops.cortex.render_status.governed_writes", []),
                ("ops.cortex.render_status.legacy_compatibility_surfaces", []),
                ("ops.cortex.render_status.working_memory_summary", {"_items": [], "initiatives": {}}),
                ("ops.cortex.render_status.provenance_alert_summary", {"status": "clear", "item_count": 0, "items": []}),
                ("ops.cortex.render_status.conversation_summary", {}),
                ("ops.cortex.render_status.build_canonical_lockfile_artifacts", {}),
                ("ops.cortex.render_status.repo_inventory_summary_from_lock", {"items": []}),
                ("ops.cortex.render_status.lock_worktree_hygiene", {"status": "frozen"}),
                ("ops.cortex.render_status.registry_summary", {}),
                ("ops.cortex.render_status.artifact_inventory", {}),
                ("ops.cortex.render_status.world_model_state", {}),
            ]
            with ExitStack() as stack:
                for target, value in patch_specs:
                    stack.enter_context(patch(target, return_value=value))
                payload = render_status_payload(descriptor_root)

        self.assertEqual(payload["trust_posture"], payload["slices"]["trust_posture"])
        self.assertEqual("restricted", payload["trust_posture"]["status"])
        self.assertEqual(2, payload["trust_posture"]["item_count"])
        self.assertEqual(1, payload["trust_posture"]["untrusted_item_count"])
        self.assertEqual(2, payload["trust_posture"]["metadata_only_item_count"])
        self.assertEqual(
            ["archive-restricted", "archive-untrusted"],
            [item["archive_id"] for item in payload["slices"]["trust_posture"]["items"]],
        )

    def test_render_status_payload_preserves_top_level_trust_surfaces_separately(self) -> None:
        descriptors = [
            _knowledge_catalog_descriptor(
                archive_id="archive-untrusted",
                trust_class="untrusted",
                source_ref="data/knowledge/archive-untrusted.descriptor.json",
                indexing_profile="metadata_only",
                promotion_status="quarantined",
            ),
            _knowledge_catalog_descriptor(
                archive_id="archive-restricted",
                trust_class="restricted",
                source_ref="data/knowledge/archive-restricted.descriptor.json",
                indexing_profile="metadata_only",
                promotion_status="review_pending",
            ),
        ]

        with TemporaryDirectory() as temp_dir:
            descriptor_root = Path(temp_dir)
            (descriptor_root / "placeholder.json").write_text("{}", encoding="utf-8")
            patch_specs = [
                ("ops.cortex.render_status.load_descriptors", descriptors),
                ("ops.cortex.render_status.load_registry_state", {"ok": True}),
                ("ops.cortex.render_status.choose_latest_session", None),
                ("ops.cortex.render_status.session_overview", None),
                ("ops.cortex.render_status.blocked_workers", []),
                ("ops.cortex.render_status.classify_merge_requests", ([], [])),
                ("ops.cortex.render_status.closure_receipts", []),
                ("ops.cortex.render_status.execution_receipt_residue_records", []),
                ("ops.cortex.render_status.governed_writes", []),
                ("ops.cortex.render_status.legacy_compatibility_surfaces", []),
                ("ops.cortex.render_status.working_memory_summary", {"_items": [], "initiatives": {}}),
                ("ops.cortex.render_status.provenance_alert_summary", {"status": "clear", "item_count": 0, "items": []}),
                ("ops.cortex.render_status.conversation_summary", {}),
                ("ops.cortex.render_status.build_canonical_lockfile_artifacts", {}),
                ("ops.cortex.render_status.repo_inventory_summary_from_lock", {"items": []}),
                ("ops.cortex.render_status.lock_worktree_hygiene", {"status": "frozen"}),
                ("ops.cortex.render_status.registry_summary", {}),
                ("ops.cortex.render_status.artifact_inventory", {}),
                ("ops.cortex.render_status.world_model_state", {}),
            ]
            with ExitStack() as stack:
                for target, value in patch_specs:
                    stack.enter_context(patch(target, return_value=value))
                payload = render_status_payload(descriptor_root)

        self.assertEqual(
            [
                {
                    "archive_id": "archive-restricted",
                    "knowledge_ref": "knowledge:archive-restricted",
                    "trust_class": "restricted",
                    "indexing_profile": "metadata_only",
                    "promotion_status": "review_pending",
                    "source_ref": "data/knowledge/archive-restricted.descriptor.json",
                },
                {
                    "archive_id": "archive-untrusted",
                    "knowledge_ref": "knowledge:archive-untrusted",
                    "trust_class": "untrusted",
                    "indexing_profile": "metadata_only",
                    "promotion_status": "quarantined",
                    "source_ref": "data/knowledge/archive-untrusted.descriptor.json",
                },
            ],
            payload["trust_surfaces"],
        )
        self.assertEqual("restricted", payload["trust_posture"]["status"])
        self.assertEqual(2, payload["trust_posture"]["item_count"])
        self.assertEqual(1, payload["attention_queue"]["item_count"])
        self.assertEqual("quarantined_trust_surface", payload["attention_queue"]["items"][0]["kind"])

    def test_conversation_summary_is_empty_without_conversation_manifests(self) -> None:
        self.assertEqual(
            {
                "item_count": 0,
                "active_count": 0,
                "recent_items": [],
            },
            conversation_summary([]),
        )

    def test_conversation_summary_omits_non_conversation_descriptors(self) -> None:
        summary = conversation_summary(
            [
                _conversation_descriptor(turn_id="turn-proposal", action_mode="proposal_required"),
                _knowledge_catalog_descriptor(
                    archive_id="archive-restricted",
                    trust_class="restricted",
                    source_ref="data/knowledge/archive-restricted.descriptor.json",
                ),
            ]
        )

        self.assertEqual(0, summary["item_count"])
        self.assertEqual(0, summary["active_count"])
        self.assertEqual([], summary["recent_items"])

    def test_conversation_summary_preserves_one_active_manifest_fields(self) -> None:
        summary = conversation_summary(
            [
                _conversation_manifest_descriptor(
                    conversation_id="conversation-active",
                    mode="voice",
                    status="active",
                    turn_count=7,
                    updated_at="2026-06-17T12:30:00Z",
                    last_turn_at="2026-06-17T12:29:00Z",
                    recent_turn_refs=[
                        "runtime/atlas/conversations/conversation-active/turns/turn-6.json",
                        "runtime/atlas/conversations/conversation-active/turns/turn-7.json",
                    ],
                    active_initiative_refs=[
                        "docs/memory/initiatives/initiative-active.json",
                    ],
                    active_session_refs=[
                        "runtime/atlas/sessions/session-active/session.manifest.json",
                    ],
                )
            ]
        )

        self.assertEqual(1, summary["item_count"])
        self.assertEqual(1, summary["active_count"])
        self.assertEqual(
            [
                {
                    "conversation_id": "conversation-active",
                    "mode": "voice",
                    "status": "active",
                    "turn_count": 7,
                    "last_turn_at": "2026-06-17T12:29:00Z",
                    "recent_turn_refs": [
                        "runtime/atlas/conversations/conversation-active/turns/turn-6.json",
                        "runtime/atlas/conversations/conversation-active/turns/turn-7.json",
                    ],
                    "active_initiative_refs": [
                        "docs/memory/initiatives/initiative-active.json",
                    ],
                    "active_session_refs": [
                        "runtime/atlas/sessions/session-active/session.manifest.json",
                    ],
                    "source_ref": "runtime/atlas/conversations/conversation-active/conversation.manifest.json",
                }
            ],
            summary["recent_items"],
        )

    def test_conversation_summary_preserves_one_non_active_manifest_without_incrementing_active_count(self) -> None:
        summary = conversation_summary(
            [
                _conversation_manifest_descriptor(
                    conversation_id="conversation-paused",
                    mode="governed",
                    status="paused",
                    turn_count=2,
                    updated_at="2026-06-17T10:00:00Z",
                    last_turn_at="2026-06-17T09:55:00Z",
                )
            ]
        )

        self.assertEqual(1, summary["item_count"])
        self.assertEqual(0, summary["active_count"])
        self.assertEqual(
            {
                "conversation_id": "conversation-paused",
                "mode": "governed",
                "status": "paused",
                "turn_count": 2,
                "last_turn_at": "2026-06-17T09:55:00Z",
                "recent_turn_refs": [
                    "runtime/atlas/conversations/conversation-paused/turns/turn-1.json",
                ],
                "active_initiative_refs": [],
                "active_session_refs": [],
                "source_ref": "runtime/atlas/conversations/conversation-paused/conversation.manifest.json",
            },
            summary["recent_items"][0],
        )

    def test_conversation_summary_preserves_descending_order_and_caps_recent_items_at_five(self) -> None:
        descriptors = [
            _conversation_manifest_descriptor(
                conversation_id=f"conversation-{index}",
                updated_at=f"2026-06-17T12:0{index}:00Z",
                last_turn_at=f"2026-06-17T12:0{index}:30Z",
            )
            for index in range(6)
        ]
        descriptors.append(
            _conversation_manifest_descriptor(
                conversation_id="conversation-z",
                updated_at="2026-06-17T12:05:00Z",
                last_turn_at="2026-06-17T12:05:30Z",
            )
        )

        summary = conversation_summary(descriptors)

        self.assertEqual(7, summary["item_count"])
        self.assertEqual(7, summary["active_count"])
        self.assertEqual(5, len(summary["recent_items"]))
        self.assertEqual(
            [
                "conversation-z",
                "conversation-5",
                "conversation-4",
                "conversation-3",
                "conversation-2",
            ],
            [item["conversation_id"] for item in summary["recent_items"]],
        )

    def test_render_status_payload_preserves_top_level_conversations_separately(self) -> None:
        descriptors = [
            _conversation_manifest_descriptor(
                conversation_id="conversation-top-level",
                status="active",
                turn_count=4,
                updated_at="2026-06-17T14:00:00Z",
                last_turn_at="2026-06-17T13:59:00Z",
                active_initiative_refs=["docs/memory/initiatives/initiative-top-level.json"],
                active_session_refs=[
                    "runtime/atlas/sessions/session-top-level/session.manifest.json",
                ],
            ),
            _conversation_descriptor(
                turn_id="turn-proposal",
                action_mode="proposal_required",
                intent="write_receipt",
                conversation_id="conversation-top-level",
                source_ref="runtime/atlas/conversations/conversation-top-level/turns/turn-proposal.json",
            ),
        ]

        with TemporaryDirectory() as temp_dir:
            descriptor_root = Path(temp_dir)
            (descriptor_root / "placeholder.json").write_text("{}", encoding="utf-8")
            patch_specs = [
                ("ops.cortex.render_status.load_descriptors", descriptors),
                ("ops.cortex.render_status.load_registry_state", {"ok": True}),
                ("ops.cortex.render_status.choose_latest_session", None),
                ("ops.cortex.render_status.session_overview", None),
                ("ops.cortex.render_status.blocked_workers", []),
                ("ops.cortex.render_status.classify_merge_requests", ([], [])),
                ("ops.cortex.render_status.closure_receipts", []),
                ("ops.cortex.render_status.execution_receipt_residue_records", []),
                ("ops.cortex.render_status.governed_writes", []),
                ("ops.cortex.render_status.legacy_compatibility_surfaces", []),
                ("ops.cortex.render_status.trust_surfaces", []),
                ("ops.cortex.render_status.trust_posture_summary", {}),
                ("ops.cortex.render_status.working_memory_summary", {"_items": [], "initiatives": {}}),
                ("ops.cortex.render_status.provenance_alert_summary", {"status": "clear", "item_count": 0, "items": []}),
                ("ops.cortex.render_status.build_canonical_lockfile_artifacts", {}),
                ("ops.cortex.render_status.repo_inventory_summary_from_lock", {"items": []}),
                ("ops.cortex.render_status.lock_worktree_hygiene", {"status": "frozen"}),
                ("ops.cortex.render_status.registry_summary", {}),
                ("ops.cortex.render_status.artifact_inventory", {}),
                ("ops.cortex.render_status.world_model_state", {}),
            ]
            with ExitStack() as stack:
                for target, value in patch_specs:
                    stack.enter_context(patch(target, return_value=value))
                payload = render_status_payload(descriptor_root)

        self.assertEqual(
            {
                "item_count": 1,
                "active_count": 1,
                "recent_items": [
                    {
                        "conversation_id": "conversation-top-level",
                        "mode": "governed",
                        "status": "active",
                        "turn_count": 4,
                        "last_turn_at": "2026-06-17T13:59:00Z",
                        "recent_turn_refs": [
                            "runtime/atlas/conversations/conversation-top-level/turns/turn-1.json",
                        ],
                        "active_initiative_refs": [
                            "docs/memory/initiatives/initiative-top-level.json",
                        ],
                        "active_session_refs": [
                            "runtime/atlas/sessions/session-top-level/session.manifest.json",
                        ],
                        "source_ref": "runtime/atlas/conversations/conversation-top-level/conversation.manifest.json",
                    }
                ],
            },
            payload["conversations"],
        )
        self.assertEqual("conversation_action_request", payload["attention_queue"]["items"][0]["kind"])
        self.assertEqual("pending", payload["proposal_only"]["status"])
        self.assertEqual(1, payload["proposal_only"]["item_count"])
        self.assertEqual("turn-proposal", payload["proposal_only"]["items"][0]["turn_id"])

    def test_render_status_payload_preserves_blocked_worker_handoff(self) -> None:
        descriptors = [
            _worker_status_descriptor(
                worker_id="worker-1",
                worker_state="blocked",
                heartbeat_at="2026-06-16T12:00:00Z",
                blocked_reason="older state",
                source_ref="runtime/atlas/workers/worker-1/status-older.json",
            ),
            _worker_status_descriptor(
                worker_id="worker-1",
                worker_state="running",
                heartbeat_at="2026-06-16T12:05:00Z",
                source_ref="runtime/atlas/workers/worker-1/status-latest.json",
            ),
            _worker_status_descriptor(
                worker_id="worker-2",
                worker_state="merge_wait",
                heartbeat_at="2026-06-16T12:06:00Z",
                blocked_reason="waiting for merge",
                source_ref="runtime/atlas/workers/worker-2/status-latest.json",
            ),
        ]

        with TemporaryDirectory() as temp_dir:
            descriptor_root = Path(temp_dir)
            (descriptor_root / "placeholder.json").write_text("{}", encoding="utf-8")
            patch_specs = [
                ("ops.cortex.render_status.load_descriptors", descriptors),
                (
                    "ops.cortex.render_status.load_registry_state",
                    {
                        "ok": True,
                        "tool_ids": {"tool-worker-2"},
                        "extension_ids": {"extension-worker-2"},
                    },
                ),
                ("ops.cortex.render_status.choose_latest_session", None),
                ("ops.cortex.render_status.session_overview", None),
                ("ops.cortex.render_status.classify_merge_requests", ([], [])),
                ("ops.cortex.render_status.closure_receipts", []),
                ("ops.cortex.render_status.execution_receipt_residue_records", []),
                ("ops.cortex.render_status.governed_writes", []),
                ("ops.cortex.render_status.legacy_compatibility_surfaces", []),
                ("ops.cortex.render_status.trust_surfaces", []),
                ("ops.cortex.render_status.trust_posture_summary", {}),
                ("ops.cortex.render_status.working_memory_summary", {"_items": [], "initiatives": {}}),
                ("ops.cortex.render_status.provenance_alert_summary", {"status": "clear", "item_count": 0, "items": []}),
                ("ops.cortex.render_status.conversation_summary", {}),
                ("ops.cortex.render_status.build_canonical_lockfile_artifacts", {}),
                ("ops.cortex.render_status.repo_inventory_summary_from_lock", {"items": []}),
                ("ops.cortex.render_status.lock_worktree_hygiene", {"status": "frozen"}),
                ("ops.cortex.render_status.registry_summary", {}),
                ("ops.cortex.render_status.artifact_inventory", {}),
                ("ops.cortex.render_status.world_model_state", {}),
            ]
            with ExitStack() as stack:
                for target, value in patch_specs:
                    stack.enter_context(patch(target, return_value=value))
                payload = render_status_payload(descriptor_root)

        self.assertEqual(
            [
                {
                    "worker_id": "worker-2",
                    "assignment_id": "assignment-2",
                    "tool_id": "tool-worker-2",
                    "extension_id": "extension-worker-2",
                    "state": "merge_wait",
                    "blocked_reason": "waiting for merge",
                    "registry_digest": "registry-digest-1",
                    "source_ref": "runtime/atlas/workers/worker-2/status-latest.json",
                }
            ],
            payload["blocked_workers"],
        )
        self.assertEqual("needs_review", payload["attention_queue"]["status"])
        self.assertEqual(1, payload["attention_queue"]["item_count"])
        self.assertEqual("blocked_worker", payload["attention_queue"]["items"][0]["kind"])
        self.assertEqual("merge_wait", payload["attention_queue"]["items"][0]["details"]["state"])

    def test_render_status_payload_preserves_open_merge_request_handoff(self) -> None:
        descriptors = [
            _merge_request_descriptor(
                merge_request_id="merge-request-older",
                lineage_key="lineage-1",
                source_ref="runtime/atlas/merge-requests/merge-request-older.json",
                conflicting_workers=["worker-a", "worker-b"],
            ),
            _merge_request_descriptor(
                merge_request_id="merge-request-linked",
                lineage_key="lineage-1",
                source_ref="runtime/atlas/merge-requests/merge-request-linked.json",
                conflicting_workers=["worker-z"],
            ),
            _session_manifest_descriptor(
                merge_request_refs=[
                    "runtime/atlas/merge-requests/merge-request-linked.json",
                ]
            ),
        ]

        with TemporaryDirectory() as temp_dir:
            descriptor_root = Path(temp_dir)
            (descriptor_root / "placeholder.json").write_text("{}", encoding="utf-8")
            patch_specs = [
                ("ops.cortex.render_status.load_descriptors", descriptors),
                (
                    "ops.cortex.render_status.load_registry_state",
                    {
                        "ok": True,
                        "tool_ids": {"tool-merge-request-linked"},
                        "extension_ids": {"extension-merge-request-linked"},
                    },
                ),
                ("ops.cortex.render_status.choose_latest_session", None),
                ("ops.cortex.render_status.session_overview", None),
                ("ops.cortex.render_status.closure_receipts", []),
                ("ops.cortex.render_status.execution_receipt_residue_records", []),
                ("ops.cortex.render_status.governed_writes", []),
                ("ops.cortex.render_status.legacy_compatibility_surfaces", []),
                ("ops.cortex.render_status.trust_surfaces", []),
                ("ops.cortex.render_status.trust_posture_summary", {}),
                ("ops.cortex.render_status.working_memory_summary", {"_items": [], "initiatives": {}}),
                ("ops.cortex.render_status.provenance_alert_summary", {"status": "clear", "item_count": 0, "items": []}),
                ("ops.cortex.render_status.conversation_summary", {}),
                ("ops.cortex.render_status.build_canonical_lockfile_artifacts", {}),
                ("ops.cortex.render_status.repo_inventory_summary_from_lock", {"items": []}),
                ("ops.cortex.render_status.lock_worktree_hygiene", {"status": "frozen"}),
                ("ops.cortex.render_status.registry_summary", {}),
                ("ops.cortex.render_status.artifact_inventory", {}),
                ("ops.cortex.render_status.world_model_state", {}),
            ]
            with ExitStack() as stack:
                for target, value in patch_specs:
                    stack.enter_context(patch(target, return_value=value))
                payload = render_status_payload(descriptor_root)

        self.assertEqual(
            [
                {
                    "merge_request_id": "merge-request-linked",
                    "tool_id": "tool-merge-request-linked",
                    "extension_id": "extension-merge-request-linked",
                    "registry_digest": "registry-digest-1",
                    "conflicting_workers": ["worker-z"],
                    "source_ref": "runtime/atlas/merge-requests/merge-request-linked.json",
                    "conflict_key": "lineage-1",
                }
            ],
            payload["open_merge_requests"],
        )
        self.assertEqual("needs_review", payload["attention_queue"]["status"])
        self.assertEqual(1, payload["attention_queue"]["item_count"])
        self.assertEqual("open_merge_request", payload["attention_queue"]["items"][0]["kind"])
        self.assertEqual(
            "merge-request-linked",
            payload["attention_queue"]["items"][0]["details"]["merge_request_id"],
        )

    def test_render_status_payload_preserves_missing_closure_receipt_handoff(self) -> None:
        missing_ref = "runtime/atlas/execution-receipts/receipt-missing.json"
        descriptors = [
            _session_manifest_descriptor(
                session_id="session-closure-proof",
                close_receipt_refs=[missing_ref],
                source_ref="runtime/atlas/sessions/session-closure-proof/session.manifest.json",
            )
        ]

        with TemporaryDirectory() as temp_dir:
            descriptor_root = Path(temp_dir)
            (descriptor_root / "placeholder.json").write_text("{}", encoding="utf-8")
            patch_specs = [
                ("ops.cortex.render_status.load_descriptors", descriptors),
                ("ops.cortex.render_status.load_registry_state", {"ok": True}),
                (
                    "ops.cortex.render_status.session_overview",
                    {
                        "session_id": "session-closure-proof",
                        "task_id": "task-session-closure-proof",
                        "source_ref": "runtime/atlas/sessions/session-closure-proof/session.manifest.json",
                    },
                ),
                ("ops.cortex.render_status.blocked_workers", []),
                ("ops.cortex.render_status.classify_merge_requests", ([], [])),
                ("ops.cortex.render_status.execution_receipt_residue_records", []),
                ("ops.cortex.render_status.governed_writes", []),
                ("ops.cortex.render_status.legacy_compatibility_surfaces", []),
                ("ops.cortex.render_status.trust_surfaces", []),
                ("ops.cortex.render_status.trust_posture_summary", {}),
                ("ops.cortex.render_status.working_memory_summary", {"_items": [], "initiatives": {}}),
                ("ops.cortex.render_status.provenance_alert_summary", {"status": "clear", "item_count": 0, "items": []}),
                ("ops.cortex.render_status.conversation_summary", {}),
                ("ops.cortex.render_status.build_canonical_lockfile_artifacts", {}),
                ("ops.cortex.render_status.repo_inventory_summary_from_lock", {"items": []}),
                ("ops.cortex.render_status.lock_worktree_hygiene", {"status": "frozen"}),
                ("ops.cortex.render_status.registry_summary", {}),
                ("ops.cortex.render_status.artifact_inventory", {}),
                ("ops.cortex.render_status.world_model_state", {}),
            ]
            with ExitStack() as stack:
                for target, value in patch_specs:
                    stack.enter_context(patch(target, return_value=value))
                payload = render_status_payload(
                    descriptor_root,
                    session_id="session-closure-proof",
                )

        self.assertEqual(
            [{"source_ref": missing_ref, "missing": True}],
            payload["closure_receipts"],
        )
        self.assertEqual("needs_review", payload["attention_queue"]["status"])
        self.assertEqual(1, payload["attention_queue"]["item_count"])
        self.assertEqual("missing_closure_receipt", payload["attention_queue"]["items"][0]["kind"])
        self.assertEqual(missing_ref, payload["attention_queue"]["items"][0]["source_ref"])

    def test_render_status_payload_preserves_closure_receipt_issue_handoff(self) -> None:
        receipt_ref = "runtime/atlas/execution-receipts/receipt-failed.json"
        descriptors = [
            _session_manifest_descriptor(
                session_id="session-closure-issue-proof",
                close_receipt_refs=[receipt_ref],
                source_ref="runtime/atlas/sessions/session-closure-issue-proof/session.manifest.json",
            ),
            _execution_receipt_descriptor(
                receipt_id="receipt-failed",
                source_ref=receipt_ref,
                result="failed",
                tool_id="tool-receipt-failed",
                extension_id="extension-receipt-failed",
            ),
        ]

        with TemporaryDirectory() as temp_dir:
            descriptor_root = Path(temp_dir)
            (descriptor_root / "placeholder.json").write_text("{}", encoding="utf-8")
            patch_specs = [
                ("ops.cortex.render_status.load_descriptors", descriptors),
                (
                    "ops.cortex.render_status.load_registry_state",
                    {
                        "ok": True,
                        "tool_ids": {"tool-receipt-failed"},
                        "extension_ids": {"extension-receipt-failed"},
                    },
                ),
                (
                    "ops.cortex.render_status.session_overview",
                    {
                        "session_id": "session-closure-issue-proof",
                        "task_id": "task-session-closure-issue-proof",
                        "source_ref": "runtime/atlas/sessions/session-closure-issue-proof/session.manifest.json",
                    },
                ),
                ("ops.cortex.render_status.blocked_workers", []),
                ("ops.cortex.render_status.classify_merge_requests", ([], [])),
                ("ops.cortex.render_status.execution_receipt_residue_records", []),
                ("ops.cortex.render_status.governed_writes", []),
                ("ops.cortex.render_status.legacy_compatibility_surfaces", []),
                ("ops.cortex.render_status.trust_surfaces", []),
                ("ops.cortex.render_status.trust_posture_summary", {}),
                ("ops.cortex.render_status.working_memory_summary", {"_items": [], "initiatives": {}}),
                ("ops.cortex.render_status.provenance_alert_summary", {"status": "clear", "item_count": 0, "items": []}),
                ("ops.cortex.render_status.conversation_summary", {}),
                ("ops.cortex.render_status.build_canonical_lockfile_artifacts", {}),
                ("ops.cortex.render_status.repo_inventory_summary_from_lock", {"items": []}),
                ("ops.cortex.render_status.lock_worktree_hygiene", {"status": "frozen"}),
                ("ops.cortex.render_status.registry_summary", {}),
                ("ops.cortex.render_status.artifact_inventory", {}),
                ("ops.cortex.render_status.world_model_state", {}),
            ]
            with ExitStack() as stack:
                for target, value in patch_specs:
                    stack.enter_context(patch(target, return_value=value))
                payload = render_status_payload(
                    descriptor_root,
                    session_id="session-closure-issue-proof",
                )

        self.assertEqual(
            [
                {
                    "source_ref": receipt_ref,
                    "original_source_ref": receipt_ref,
                    "artifact_type": "execution_receipt",
                    "receipt_id": "receipt-failed",
                    "tool_id": "tool-receipt-failed",
                    "extension_id": "extension-receipt-failed",
                    "result": "failed",
                    "registry_digest": "registry-digest-1",
                    "supersedes_receipt_ref": None,
                    "reconciled_at": "2026-06-16T12:00:00Z",
                    "reconciled_by_tool_version": "tool-version-1",
                    "repair_basis_refs": [],
                }
            ],
            payload["closure_receipts"],
        )
        self.assertEqual("needs_review", payload["attention_queue"]["status"])
        self.assertEqual(1, payload["attention_queue"]["item_count"])
        self.assertEqual("closure_receipt_issue", payload["attention_queue"]["items"][0]["kind"])
        self.assertEqual("high", payload["attention_queue"]["items"][0]["severity"])
        self.assertEqual(
            {
                "receipt_id": "receipt-failed",
                "result": "failed",
            },
            payload["attention_queue"]["items"][0]["details"],
        )

    def test_provenance_summary_reports_initiative_and_proposal_drift(self) -> None:
        working_memory_items = [
            {
                "memory_kind": "initiative",
                "id": "initiative-proof",
                "title": "Proof",
                "path": "docs/memory/initiatives/initiative-proof.json",
                "related_attention_refs": [
                    "attention:sha256:current",
                    "attention:sha256:stale",
                ],
            }
        ]
        descriptors = [
            {
                "artifact_type": "session_manifest",
                "source_ref": "runtime/atlas/proposed-sessions/session-proposed-proof/session.manifest.json",
                "identity": {
                    "session_id": "session-proposed-proof",
                    "task_id": "proof-task",
                },
                "state": {
                    "session_state": "proposed",
                },
                "links": {
                    "initiative_ref": "docs/memory/initiatives/missing.json",
                    "triggering_attention_refs": [
                        "attention:sha256:current",
                        "attention:sha256:stale",
                    ],
                },
            }
        ]

        with patch(
            "ops.cortex.render_status.load_current_attention_refs",
            return_value={"attention:sha256:current"},
        ), patch(
            "ops.cortex.render_status.resolve_atlas_path",
            side_effect=lambda ref, root: Path(__file__).with_name("missing.json"),
        ):
            summary = provenance_alert_summary(
                working_memory_items=working_memory_items,
                descriptors=descriptors,
            )

        self.assertEqual("drift_detected", summary["status"])
        self.assertEqual(1, summary["initiative_item_count"])
        self.assertEqual(1, summary["proposal_item_count"])
        self.assertEqual(2, summary["item_count"])
        self.assertEqual("initiative_provenance_drift", summary["items"][0]["kind"])
        self.assertEqual("proposed_session_provenance_drift", summary["items"][1]["kind"])

    def test_provenance_summary_is_clear_when_refs_resolve(self) -> None:
        working_memory_items = [
            {
                "memory_kind": "initiative",
                "id": "initiative-proof",
                "title": "Proof",
                "path": "docs/memory/initiatives/initiative-proof.json",
                "related_attention_refs": [
                    "attention:sha256:current",
                ],
            }
        ]
        descriptors = [
            {
                "artifact_type": "session_manifest",
                "source_ref": "runtime/atlas/proposed-sessions/session-proposed-proof/session.manifest.json",
                "identity": {
                    "session_id": "session-proposed-proof",
                    "task_id": "proof-task",
                },
                "state": {
                    "session_state": "proposed",
                },
                "links": {
                    "initiative_ref": "docs/memory/initiatives/initiative-proof.json",
                    "triggering_attention_refs": [
                        "attention:sha256:current",
                    ],
                },
            }
        ]

        with patch(
            "ops.cortex.render_status.load_current_attention_refs",
            return_value={"attention:sha256:current"},
        ), patch(
            "ops.cortex.render_status.resolve_atlas_path",
            side_effect=lambda ref, root: Path(__file__) if ref == "docs/memory/initiatives/initiative-proof.json" else Path(__file__).with_name("missing.json"),
        ):
            summary = provenance_alert_summary(
                working_memory_items=working_memory_items,
                descriptors=descriptors,
            )

        self.assertEqual("clear", summary["status"])
        self.assertEqual(0, summary["item_count"])
        self.assertEqual([], summary["items"])


if __name__ == "__main__":
    unittest.main()
