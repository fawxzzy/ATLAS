from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from ops.atlas.queue_or_registry_supervisor_inventory import (
    QueueOrRegistrySupervisorInventoryError,
    build_queue_or_registry_supervisor_inventory,
)


def _write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def _session_manifest(*, session_id: str, merge_request_refs: list[str], updated_at: str) -> dict[str, object]:
    return {
        "contract_version": "atlas.session.v1",
        "session_id": session_id,
        "title": session_id,
        "task_id": "history-pass",
        "scenario": "conflict_fixture",
        "session_state": "resume_ready",
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
            "execution_receipt_ref": None,
            "bridge_record_ref": None,
            "merge_request_refs": merge_request_refs,
            "pause_status_refs": [],
            "resume_context_refs": [],
            "merge_assignment_ref": None,
            "merge_prompt_ref": None,
            "merge_context_ref": None,
            "merge_completion_ref": None,
        },
        "completion": {"final_status": "resume_ready", "final_status_ref": None, "close_receipt_refs": []},
    }


def _merge_request(*, merge_request_id: str, conflicting_workers: list[str]) -> dict[str, object]:
    return {
        "contract_version": "atlas.worker.merge-request.v1",
        "merge_request_id": merge_request_id,
        "stack_lock_digest": "sha256:test-lock",
        "tool_id": "read_only_scan",
        "extension_id": None,
        "registry_digest": "sha256:test-registry",
        "conflicting_workers": conflicting_workers,
        "overlaps": [],
        "paused_handoff_refs": [],
        "merge_worker_handoff": {
            "worker_id": "pending-merge-worker",
            "assignment_id": f"assignment-{merge_request_id}",
            "task_id": f"merge-{merge_request_id}",
            "handoff_ref": f"runtime/cortex/supervisor/{merge_request_id}.merge-handoff.json",
            "tool_id": "read_only_scan",
            "extension_id": None,
            "registry_digest": "sha256:test-registry",
        },
    }


class QueueOrRegistrySupervisorInventoryTests(unittest.TestCase):
    def _temp_root(self) -> Path:
        temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(temp_dir.cleanup)
        root = Path(temp_dir.name)
        (root / "stack.yaml").write_text("repo_registry: {}\n", encoding="utf-8")
        return root

    def test_inventory_counts_linked_and_unlinked_merge_requests(self) -> None:
        root = self._temp_root()
        session_id = "session-proof"
        linked_ref = f"runtime/cortex/supervisor/{session_id}/merge-request-linked.json"
        extra_ref = f"runtime/cortex/supervisor/{session_id}/merge-request-extra.json"

        _write_json(
            root / "runtime" / "atlas" / "sessions" / session_id / "session.manifest.json",
            _session_manifest(session_id=session_id, merge_request_refs=[linked_ref], updated_at="2026-06-14T10:00:00Z"),
        )
        _write_json(root / linked_ref, _merge_request(merge_request_id="merge-request-linked", conflicting_workers=["worker-a"]))
        _write_json(root / extra_ref, _merge_request(merge_request_id="merge-request-extra", conflicting_workers=["worker-b", "worker-c"]))

        payload = build_queue_or_registry_supervisor_inventory(root=root).to_payload()

        self.assertEqual(payload["supervisor_session_count"], 1)
        self.assertEqual(payload["total_merge_request_file_count"], 2)
        self.assertEqual(payload["linked_merge_request_ref_count"], 1)
        self.assertEqual(payload["unlinked_merge_request_ref_count"], 1)
        self.assertEqual(payload["multi_merge_request_session_count"], 1)
        entry = payload["supervisor_session_entries"][0]
        self.assertEqual(entry["linked_supervisor_merge_request_ref_count"], 1)
        self.assertEqual(entry["unlinked_supervisor_merge_request_ref_count"], 1)
        self.assertEqual(entry["conflicting_worker_count"], 3)

    def test_missing_manifest_link_is_reported(self) -> None:
        root = self._temp_root()
        session_id = "session-missing-link"
        missing_ref = f"runtime/cortex/supervisor/{session_id}/merge-request-missing.json"
        _write_json(
            root / "runtime" / "atlas" / "sessions" / session_id / "session.manifest.json",
            _session_manifest(session_id=session_id, merge_request_refs=[missing_ref], updated_at="2026-06-14T09:00:00Z"),
        )

        payload = build_queue_or_registry_supervisor_inventory(root=root).to_payload()
        self.assertEqual(payload["missing_manifest_link_count"], 1)
        self.assertEqual(payload["supervisor_session_entries"][0]["missing_manifest_link_count"], 1)

    def test_unexpected_merge_request_contract_fails_closed(self) -> None:
        root = self._temp_root()
        session_id = "session-bad"
        _write_json(
            root / "runtime" / "cortex" / "supervisor" / session_id / "merge-request-bad.json",
            {
                **_merge_request(merge_request_id="merge-request-bad", conflicting_workers=[]),
                "contract_version": "atlas.worker.merge-request.v0",
            },
        )

        with self.assertRaises(QueueOrRegistrySupervisorInventoryError) as context:
            build_queue_or_registry_supervisor_inventory(root=root)
        self.assertIn("Unexpected merge request contract_version", str(context.exception))


if __name__ == "__main__":
    unittest.main()
