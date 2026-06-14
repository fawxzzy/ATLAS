from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from ops.atlas.queue_or_registry_execution_home_inventory import (
    QueueOrRegistryExecutionHomeInventoryError,
    build_queue_or_registry_execution_home_inventory,
)


def _write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def _session_manifest(*, session_id: str, execution_receipt_ref: str | None, close_receipt_refs: list[str], updated_at: str) -> dict[str, object]:
    return {
        "contract_version": "atlas.session.v1",
        "session_id": session_id,
        "title": session_id,
        "task_id": "execution-home-pass",
        "scenario": "read_only",
        "session_state": "completed",
        "stack_lock_digest": "sha256:test-lock",
        "stack_manifest_ref": "stack.yaml",
        "created_at": "2026-06-14T08:00:00Z",
        "updated_at": updated_at,
        "closed_at": updated_at,
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
            "assignment_id": f"{session_id}-assignment",
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
        "completion": {"final_status": "completed", "final_status_ref": execution_receipt_ref, "close_receipt_refs": close_receipt_refs},
    }


def _receipt(*, receipt_id: str, supersedes_receipt_ref: str | None = None) -> dict[str, object]:
    payload: dict[str, object] = {
        "contract_version": "atlas.privileged-action.receipt.v1",
        "receipt_id": receipt_id,
        "assignment_id": "assignment",
        "request_id": "request",
        "worker_id": "worker",
        "tool_id": "read_only_scan",
        "extension_id": None,
        "registry_digest": "sha256:test-registry",
        "stack_lock_digest": "sha256:test-lock",
        "result": "succeeded",
    }
    if supersedes_receipt_ref is not None:
        payload["supersedes_receipt_ref"] = supersedes_receipt_ref
    return payload


class QueueOrRegistryExecutionHomeInventoryTests(unittest.TestCase):
    def _temp_root(self) -> Path:
        temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(temp_dir.cleanup)
        root = Path(temp_dir.name)
        (root / "stack.yaml").write_text("repo_registry: {}\n", encoding="utf-8")
        return root

    def test_inventory_counts_linked_and_reconciled_receipts(self) -> None:
        root = self._temp_root()
        session_id = "session-proof"
        primary_ref = f"runtime/lifeline/worker-execution/{session_id}-assignment/receipt-primary.json"
        reconciled_ref = f"runtime/lifeline/worker-execution/{session_id}-assignment/receipt-primary--reconciled.json"

        _write_json(
            root / "runtime" / "atlas" / "sessions" / session_id / "session.manifest.json",
            _session_manifest(session_id=session_id, execution_receipt_ref=primary_ref, close_receipt_refs=[primary_ref], updated_at="2026-06-14T10:00:00Z"),
        )
        _write_json(root / primary_ref, _receipt(receipt_id="receipt-primary"))
        _write_json(root / reconciled_ref, _receipt(receipt_id="receipt-primary--reconciled", supersedes_receipt_ref=primary_ref))

        payload = build_queue_or_registry_execution_home_inventory(root=root).to_payload()

        self.assertEqual(payload["execution_home_session_count"], 1)
        self.assertEqual(payload["assignment_root_count"], 1)
        self.assertEqual(payload["total_receipt_file_count"], 2)
        self.assertEqual(payload["linked_receipt_ref_count"], 1)
        self.assertEqual(payload["unlinked_receipt_ref_count"], 1)
        self.assertEqual(payload["reconciled_receipt_file_count"], 1)
        self.assertEqual(payload["sessions_with_reconciled_receipts"], 1)
        entry = payload["execution_home_entries"][0]
        self.assertTrue(entry["execution_receipt_ref_present"])
        self.assertEqual(entry["linked_receipt_ref_count"], 1)
        self.assertEqual(entry["unlinked_receipt_ref_count"], 1)

    def test_missing_manifest_receipt_link_is_reported(self) -> None:
        root = self._temp_root()
        session_id = "session-missing"
        missing_ref = f"runtime/lifeline/worker-execution/{session_id}-assignment/receipt-missing.json"
        _write_json(
            root / "runtime" / "atlas" / "sessions" / session_id / "session.manifest.json",
            _session_manifest(session_id=session_id, execution_receipt_ref=missing_ref, close_receipt_refs=[missing_ref], updated_at="2026-06-14T09:00:00Z"),
        )

        payload = build_queue_or_registry_execution_home_inventory(root=root).to_payload()
        self.assertEqual(payload["missing_manifest_receipt_link_count"], 1)
        self.assertEqual(payload["execution_home_entries"][0]["missing_manifest_receipt_link_count"], 1)

    def test_unexpected_receipt_contract_fails_closed(self) -> None:
        root = self._temp_root()
        session_id = "session-bad"
        bad_ref = root / "runtime" / "lifeline" / "worker-execution" / f"{session_id}-assignment" / "receipt-bad.json"
        _write_json(bad_ref, {**_receipt(receipt_id="receipt-bad"), "contract_version": "atlas.privileged-action.receipt.v0"})

        with self.assertRaises(QueueOrRegistryExecutionHomeInventoryError) as context:
            build_queue_or_registry_execution_home_inventory(root=root)
        self.assertIn("Unexpected execution receipt contract_version", str(context.exception))


if __name__ == "__main__":
    unittest.main()
