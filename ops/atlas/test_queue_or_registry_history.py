from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from ops.atlas.queue_or_registry_history import (
    QueueOrRegistryHistoryError,
    build_queue_or_registry_history,
)


def _write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def _session_manifest(
    *,
    session_id: str,
    task_id: str,
    scenario: str,
    session_state: str,
    resume_status: str,
    final_status: str | None,
    created_at: str,
    updated_at: str,
    closed_at: str | None,
    status_refs: list[str] | None = None,
    merge_request_refs: list[str] | None = None,
    pause_status_refs: list[str] | None = None,
    resume_context_refs: list[str] | None = None,
    close_receipt_refs: list[str] | None = None,
    resume_request_ref: str | None = None,
    resume_dispatch_ref: str | None = None,
    resume_run_manifest_ref: str | None = None,
    resumed_assignment_ref: str | None = None,
    resumed_running_status_ref: str | None = None,
    resumed_completed_status_ref: str | None = None,
) -> dict[str, object]:
    return {
        "contract_version": "atlas.session.v1",
        "session_id": session_id,
        "title": session_id,
        "task_id": task_id,
        "scenario": scenario,
        "session_state": session_state,
        "stack_lock_digest": "sha256:test-lock",
        "stack_manifest_ref": "stack.yaml",
        "created_at": created_at,
        "updated_at": updated_at,
        "closed_at": closed_at,
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
            "execution": {"tool_id": "workspace_file_apply", "extension_id": None},
        },
        "worker": {
            "worker_id": f"{session_id}-worker",
            "assignment_id": f"{session_id}-assignment",
            "context_ref": f"runtime/atlas/sessions/{session_id}/artifacts/worker.context.json",
            "assignment_ref": f"runtime/atlas/sessions/{session_id}/artifacts/worker.assignment.json",
        },
        "refs": {
            "status_refs": status_refs or [],
            "capability_profile_ref": None,
            "request_ref": None,
            "approval_receipt_ref": None,
            "execution_receipt_ref": None,
            "bridge_record_ref": None,
            "merge_request_refs": merge_request_refs or [],
            "pause_status_refs": pause_status_refs or [],
            "resume_context_refs": resume_context_refs or [],
            "merge_assignment_ref": None,
            "merge_prompt_ref": None,
            "merge_context_ref": None,
            "merge_completion_ref": None,
            "resume_request_ref": resume_request_ref,
            "resume_dispatch_ref": resume_dispatch_ref,
            "resume_run_manifest_ref": resume_run_manifest_ref,
            "resumed_assignment_ref": resumed_assignment_ref,
            "resumed_running_status_ref": resumed_running_status_ref,
            "resumed_completed_status_ref": resumed_completed_status_ref,
        },
        "resume": {
            "status": resume_status,
            "requested_at": None,
            "requested_worker_id": None,
            "resume_context_ref": None,
            "merge_completion_ref": None,
            "dispatched_at": None,
            "completed_at": None,
            "failure_reason": None,
        },
        "completion": {
            "final_status": final_status,
            "final_status_ref": None,
            "close_receipt_refs": close_receipt_refs or [],
        },
    }


class QueueOrRegistryHistoryTests(unittest.TestCase):
    def _temp_root(self) -> Path:
        temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(temp_dir.cleanup)
        root = Path(temp_dir.name)
        (root / "stack.yaml").write_text("repo_registry: {}\n", encoding="utf-8")
        return root

    def test_history_summary_counts_mixed_resume_progression(self) -> None:
        root = self._temp_root()
        sessions_root = root / "runtime" / "atlas" / "sessions"

        _write_json(
            sessions_root / "session-history-completed" / "session.manifest.json",
            _session_manifest(
                session_id="session-history-completed",
                task_id="history-pass",
                scenario="conflict_fixture",
                session_state="completed",
                resume_status="completed",
                final_status="completed",
                created_at="2026-06-14T10:00:00Z",
                updated_at="2026-06-14T10:40:00Z",
                closed_at="2026-06-14T10:40:00Z",
                status_refs=["status.running", "status.completed"],
                merge_request_refs=["merge.request"],
                pause_status_refs=["status.paused"],
                resume_context_refs=["resume.context"],
                close_receipt_refs=["close.receipt"],
                resume_request_ref="resume.request",
                resume_dispatch_ref="resume.dispatch",
                resume_run_manifest_ref="run.manifest",
                resumed_assignment_ref="resumed.assignment",
                resumed_running_status_ref="resumed.running",
                resumed_completed_status_ref="resumed.completed",
            ),
        )
        _write_json(
            sessions_root / "session-history-running" / "session.manifest.json",
            _session_manifest(
                session_id="session-history-running",
                task_id="history-pass",
                scenario="read_only",
                session_state="running",
                resume_status="running",
                final_status=None,
                created_at="2026-06-14T09:00:00Z",
                updated_at="2026-06-14T10:20:00Z",
                closed_at=None,
                status_refs=["status.running"],
                merge_request_refs=["merge.request"],
                pause_status_refs=["status.paused"],
                resume_context_refs=["resume.context"],
                resume_request_ref="resume.request",
                resume_dispatch_ref="resume.dispatch",
            ),
        )
        _write_json(
            sessions_root / "session-history-ready" / "session.manifest.json",
            _session_manifest(
                session_id="session-history-ready",
                task_id="history-pass",
                scenario="proposed_session",
                session_state="resume_ready",
                resume_status="resume_ready",
                final_status="resume_ready",
                created_at="2026-06-14T08:00:00Z",
                updated_at="2026-06-14T10:10:00Z",
                closed_at=None,
                merge_request_refs=["merge.request"],
                pause_status_refs=["status.paused"],
                resume_context_refs=["resume.context"],
            ),
        )

        payload = build_queue_or_registry_history(root=root).to_payload()

        self.assertEqual(payload["session_count"], 3)
        self.assertEqual(payload["open_session_count"], 2)
        self.assertEqual(payload["terminal_session_count"], 1)
        self.assertEqual(payload["state_counts"], {"completed": 1, "resume_ready": 1, "running": 1})
        self.assertEqual(payload["final_status_counts"], {"completed": 1, "resume_ready": 1})
        self.assertEqual(
            payload["resume_transition_counts"],
            {
                "resume_ready_sessions": 1,
                "resume_requested_sessions": 2,
                "resume_dispatched_sessions": 2,
                "resumed_completion_sessions": 1,
            },
        )
        self.assertEqual(payload["oldest_created_at"], "2026-06-14T08:00:00Z")
        self.assertEqual(payload["latest_updated_at"], "2026-06-14T10:40:00Z")
        self.assertEqual(
            [item["session_id"] for item in payload["session_entries"]],
            [
                "session-history-completed",
                "session-history-running",
                "session-history-ready",
            ],
        )
        self.assertEqual(payload["session_entries"][0]["close_receipt_ref_count"], 1)
        self.assertTrue(payload["session_entries"][0]["has_resumed_completed_status_ref"])
        self.assertFalse(payload["session_entries"][2]["has_resume_dispatch_ref"])

    def test_missing_sessions_root_returns_empty_read_model(self) -> None:
        root = self._temp_root()
        payload = build_queue_or_registry_history(root=root).to_payload()

        self.assertEqual(payload["session_count"], 0)
        self.assertEqual(payload["state_counts"], {})
        self.assertEqual(payload["resume_transition_counts"]["resume_ready_sessions"], 0)
        self.assertEqual(payload["read_model_basis"], "runtime/atlas/sessions")

    def test_unexpected_contract_version_fails_closed(self) -> None:
        root = self._temp_root()
        path = root / "runtime" / "atlas" / "sessions" / "session-bad" / "session.manifest.json"
        _write_json(
            path,
            {
                **_session_manifest(
                    session_id="session-bad",
                    task_id="history-pass",
                    scenario="read_only",
                    session_state="created",
                    resume_status="not_requested",
                    final_status=None,
                    created_at="2026-06-14T08:00:00Z",
                    updated_at="2026-06-14T08:10:00Z",
                    closed_at=None,
                ),
                "contract_version": "atlas.session.v0",
            },
        )

        with self.assertRaises(QueueOrRegistryHistoryError) as context:
            build_queue_or_registry_history(root=root)
        self.assertIn("Unexpected session manifest contract_version", str(context.exception))

    def test_non_list_refs_fail_closed(self) -> None:
        root = self._temp_root()
        path = root / "runtime" / "atlas" / "sessions" / "session-bad-refs" / "session.manifest.json"
        payload = _session_manifest(
            session_id="session-bad-refs",
            task_id="history-pass",
            scenario="read_only",
            session_state="created",
            resume_status="not_requested",
            final_status=None,
            created_at="2026-06-14T08:00:00Z",
            updated_at="2026-06-14T08:10:00Z",
            closed_at=None,
        )
        refs = payload["refs"]
        assert isinstance(refs, dict)
        refs["status_refs"] = "not-a-list"
        _write_json(path, payload)

        with self.assertRaises(QueueOrRegistryHistoryError) as context:
            build_queue_or_registry_history(root=root)
        self.assertIn("refs.status_refs must be a list of strings", str(context.exception))


if __name__ == "__main__":
    unittest.main()
