from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from ops.atlas.queue_or_registry_execution_receipt_writeback import (
    reconcile_queue_or_registry_execution_receipt_links,
)


def _write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def _session_manifest(
    *,
    session_id: str,
    assignment_id: str,
    execution_receipt_ref: str,
    close_receipt_refs: list[str],
    final_status_ref: str,
) -> dict[str, object]:
    return {
        "contract_version": "atlas.session.v1",
        "session_id": session_id,
        "title": session_id,
        "task_id": "writeback-pass",
        "scenario": "read_only",
        "session_state": "completed",
        "stack_lock_digest": "sha256:test-lock",
        "stack_manifest_ref": "stack.yaml",
        "created_at": "2026-06-14T08:00:00Z",
        "updated_at": "2026-06-14T10:00:00Z",
        "closed_at": "2026-06-14T10:00:00Z",
        "orchestrator": {
            "owner": "stack-root",
            "stack_component": {},
            "orchestrator_component": {},
            "supervisor_component": {},
            "executor_component": {},
        },
        "governed_surfaces": {
            "registry_digest": "sha256:test-registry",
            "context": {"tool_id": "cortex.build_worker_context", "extension_id": None},
            "supervision": {"tool_id": "cortex.supervise_workers", "extension_id": None},
            "execution": {"tool_id": "read_only_scan", "extension_id": None},
        },
        "worker": {
            "worker_id": f"{session_id}-worker",
            "assignment_id": assignment_id,
            "context_ref": "ctx",
            "assignment_ref": "assignment",
        },
        "refs": {
            "status_refs": [],
            "capability_profile_ref": None,
            "request_ref": None,
            "approval_receipt_ref": None,
            "execution_receipt_ref": execution_receipt_ref,
            "bridge_record_ref": None,
            "merge_request_refs": [],
            "pause_status_refs": [],
            "resume_context_refs": [],
            "merge_assignment_ref": None,
            "merge_prompt_ref": None,
            "merge_context_ref": None,
            "merge_completion_ref": None,
        },
        "completion": {
            "final_status": "completed",
            "final_status_ref": final_status_ref,
            "close_receipt_refs": close_receipt_refs,
        },
    }


def _receipt(*, receipt_id: str, registry_digest: str, supersedes_receipt_ref: str | None = None) -> dict[str, object]:
    payload: dict[str, object] = {
        "contract_version": "atlas.privileged-action.receipt.v1",
        "receipt_id": receipt_id,
        "assignment_id": "assignment",
        "request_id": "request",
        "worker_id": "worker",
        "tool_id": "read_only_scan",
        "extension_id": None,
        "registry_digest": registry_digest,
        "stack_lock_digest": "sha256:test-lock",
        "result": "succeeded",
        "executed_at": "2026-06-14T09:59:59Z",
    }
    if supersedes_receipt_ref is not None:
        payload["supersedes_receipt_ref"] = supersedes_receipt_ref
        payload["repair_basis_refs"] = ["runtime/atlas/sessions/session-proof/session.manifest.json"]
        payload["reconciled_at"] = "2026-06-14T10:10:00Z"
        payload["reconciled_by_tool_version"] = "lifeline.privileged-execution-repair.v1"
    return payload


class QueueOrRegistryExecutionReceiptWritebackTests(unittest.TestCase):
    def _temp_root(self) -> Path:
        temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(temp_dir.cleanup)
        root = Path(temp_dir.name)
        (root / "stack.yaml").write_text("repo_registry: {}\n", encoding="utf-8")
        (root / "runtime" / "cortex" / "artifacts").mkdir(parents=True, exist_ok=True)
        (root / "runtime" / "cortex" / "catalog" / "knowledge").mkdir(parents=True, exist_ok=True)
        return root

    def test_dry_run_reports_candidate_without_mutating_manifest(self) -> None:
        root = self._temp_root()
        session_id = "session-proof"
        assignment_id = f"{session_id}-assignment"
        primary_ref = f"runtime/lifeline/worker-execution/{assignment_id}/receipt-primary.json"
        reconciled_ref = f"runtime/lifeline/worker-execution/{assignment_id}/receipt-primary--reconciled.json"
        final_status_ref = "runtime/atlas/sessions/session-proof/artifacts/worker.status.completed.json"
        manifest_path = root / "runtime" / "atlas" / "sessions" / session_id / "session.manifest.json"

        _write_json(
            manifest_path,
            _session_manifest(
                session_id=session_id,
                assignment_id=assignment_id,
                execution_receipt_ref=primary_ref,
                close_receipt_refs=[primary_ref],
                final_status_ref=final_status_ref,
            ),
        )
        _write_json(root / primary_ref, _receipt(receipt_id="receipt-primary", registry_digest="sha256:old"))
        _write_json(
            root / reconciled_ref,
            _receipt(
                receipt_id="receipt-primary--reconciled",
                registry_digest="sha256:current",
                supersedes_receipt_ref=primary_ref,
            ),
        )

        result = reconcile_queue_or_registry_execution_receipt_links(root=root, apply_changes=False)
        payload = result.to_payload()
        self.assertEqual(payload["candidate_session_count"], 1)
        self.assertEqual(payload["updated_session_count"], 1)
        self.assertEqual(payload["updated_sessions"][0]["execution_receipt_ref_after"], reconciled_ref)

        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        self.assertEqual(manifest["refs"]["execution_receipt_ref"], primary_ref)
        self.assertEqual(manifest["completion"]["close_receipt_refs"], [primary_ref])
        self.assertEqual(manifest["completion"]["final_status_ref"], final_status_ref)

    def test_apply_rewrites_receipt_links_and_preserves_final_status_ref(self) -> None:
        root = self._temp_root()
        session_id = "session-proof"
        assignment_id = f"{session_id}-assignment"
        primary_ref = f"runtime/lifeline/worker-execution/{assignment_id}/receipt-primary.json"
        reconciled_ref = f"runtime/lifeline/worker-execution/{assignment_id}/receipt-primary--reconciled.json"
        final_status_ref = "runtime/atlas/sessions/session-proof/artifacts/worker.status.completed.json"
        manifest_path = root / "runtime" / "atlas" / "sessions" / session_id / "session.manifest.json"

        _write_json(
            manifest_path,
            _session_manifest(
                session_id=session_id,
                assignment_id=assignment_id,
                execution_receipt_ref=primary_ref,
                close_receipt_refs=[primary_ref],
                final_status_ref=final_status_ref,
            ),
        )
        _write_json(root / primary_ref, _receipt(receipt_id="receipt-primary", registry_digest="sha256:old"))
        _write_json(
            root / reconciled_ref,
            _receipt(
                receipt_id="receipt-primary--reconciled",
                registry_digest="sha256:current",
                supersedes_receipt_ref=primary_ref,
            ),
        )

        with patch("ops.atlas.queue_or_registry_execution_receipt_writeback._sync_updated_sessions") as sync_mock:
            result = reconcile_queue_or_registry_execution_receipt_links(root=root, apply_changes=True, sync_outputs=False)
        self.assertFalse(sync_mock.called)
        self.assertEqual(result.updated_session_count, 1)

        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        self.assertEqual(manifest["refs"]["execution_receipt_ref"], reconciled_ref)
        self.assertEqual(manifest["completion"]["close_receipt_refs"], [reconciled_ref])
        self.assertEqual(manifest["completion"]["final_status_ref"], final_status_ref)


if __name__ == "__main__":
    unittest.main()
