from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from ops.atlas.queue_or_registry_supervisor_merge_request_selection import (
    build_queue_or_registry_supervisor_merge_request_selection,
)


def _write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def _session_manifest(*, session_id: str, merge_request_refs: list[str], merge_completion_ref: str | None) -> dict[str, object]:
    return {
        "contract_version": "atlas.session.v1",
        "session_id": session_id,
        "title": session_id,
        "task_id": "selection-pass",
        "scenario": "conflict_fixture",
        "session_state": "resume_ready",
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
            "merge_completion_ref": merge_completion_ref,
        },
        "completion": {"final_status": "resume_ready", "final_status_ref": merge_completion_ref, "close_receipt_refs": []},
    }


def _merge_request(
    *,
    merge_request_id: str,
    stack_lock_digest: str,
    conflicting_workers: list[str],
) -> dict[str, object]:
    return {
        "contract_version": "atlas.worker.merge-request.v1",
        "merge_request_id": merge_request_id,
        "stack_lock_digest": stack_lock_digest,
        "tool_id": "read_only_scan",
        "extension_id": None,
        "registry_digest": "sha256:test-registry",
        "conflicting_workers": conflicting_workers,
        "overlaps": [
            {
                "repo_path": ".",
                "path": "README-STACK.md",
                "overlap_type": "line_overlap",
                "file_digest_before": "sha256:file-before",
                "conflicting_ranges": [],
                "reason": "same file",
            }
        ],
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


class QueueOrRegistrySupervisorMergeRequestSelectionTests(unittest.TestCase):
    def _temp_root(self) -> Path:
        temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(temp_dir.cleanup)
        root = Path(temp_dir.name)
        (root / "stack.yaml").write_text("repo_registry: {}\n", encoding="utf-8")
        return root

    def test_completed_lineage_member_collapses_same_lineage_duplicates(self) -> None:
        root = self._temp_root()
        session_id = "session-proof"
        canonical_ref = f"runtime/cortex/supervisor/{session_id}/merge-request-new.json"
        old_a_ref = f"runtime/cortex/supervisor/{session_id}/merge-request-old-a.json"
        old_b_ref = f"runtime/cortex/supervisor/{session_id}/merge-request-old-b.json"
        completion_ref = f"runtime/atlas/sessions/{session_id}/artifacts/merge/merge-request-new/completion.json"

        _write_json(
            root / "runtime" / "atlas" / "sessions" / session_id / "session.manifest.json",
            _session_manifest(session_id=session_id, merge_request_refs=[canonical_ref], merge_completion_ref=completion_ref),
        )
        _write_json(
            root / completion_ref,
            {
                "schema_version": "atlas.stack.supervisor-consumer.v1",
                "merge_request_id": "merge-request-new",
            },
        )
        _write_json(root / canonical_ref, _merge_request(merge_request_id="merge-request-new", stack_lock_digest="sha256:new", conflicting_workers=["worker-a", "worker-b"]))
        _write_json(root / old_a_ref, _merge_request(merge_request_id="merge-request-old-a", stack_lock_digest="sha256:old", conflicting_workers=["worker-b"]))
        _write_json(root / old_b_ref, _merge_request(merge_request_id="merge-request-old-b", stack_lock_digest="sha256:old", conflicting_workers=["worker-a", "worker-b"]))

        payload = build_queue_or_registry_supervisor_merge_request_selection(root=root).to_payload()
        self.assertEqual(payload["selected_lineage_count"], 1)
        self.assertEqual(payload["canonical_completed_lineage_count"], 1)
        self.assertEqual(payload["superseded_residue_ref_count"], 2)
        self.assertEqual(payload["retained_residue_ref_count"], 0)
        entry = payload["selection_entries"][0]
        self.assertEqual(entry["canonical_merge_request_ref"], canonical_ref)
        self.assertEqual(sorted(entry["superseded_residue_refs"]), sorted([old_a_ref, old_b_ref]))

    def test_unlinked_lineage_prefers_broadest_conflict_set(self) -> None:
        root = self._temp_root()
        session_id = "session-open"
        narrow_ref = f"runtime/cortex/supervisor/{session_id}/merge-request-narrow.json"
        broad_ref = f"runtime/cortex/supervisor/{session_id}/merge-request-broad.json"

        _write_json(
            root / narrow_ref,
            _merge_request(merge_request_id="merge-request-narrow", stack_lock_digest="sha256:old", conflicting_workers=["worker-b"]),
        )
        _write_json(
            root / broad_ref,
            _merge_request(merge_request_id="merge-request-broad", stack_lock_digest="sha256:new", conflicting_workers=["worker-a", "worker-b"]),
        )

        payload = build_queue_or_registry_supervisor_merge_request_selection(root=root).to_payload()
        self.assertEqual(payload["selected_lineage_count"], 1)
        self.assertEqual(payload["active_unlinked_lineage_count"], 1)
        entry = payload["selection_entries"][0]
        self.assertEqual(entry["canonical_merge_request_ref"], broad_ref)
        self.assertEqual(entry["retained_residue_refs"], [narrow_ref])


if __name__ == "__main__":
    unittest.main()
