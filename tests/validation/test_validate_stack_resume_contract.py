from __future__ import annotations

import json
import tempfile
import unittest
from contextlib import ExitStack
from pathlib import Path
from unittest.mock import patch

from ops.cortex._artifacts import stable_json_digest
from ops.validation.validate_stack import validate_world_model_state


ROOT = Path(__file__).resolve().parents[2]


def _write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def _snapshot_payload(
    *,
    kind: str,
    observations: list[dict[str, object]],
    inventory_entries: list[dict[str, object]],
    attention_items: list[dict[str, object]],
) -> dict[str, object]:
    payload: dict[str, object] = {
        "contract_version": "atlas.state.snapshot.v1",
        "snapshot_kind": kind,
        "generated_at": "2026-06-14T12:00:00Z",
        "source_refs": {
            "descriptor_root": "runtime/cortex/artifacts",
            "registry_refs": [],
            "event_latest_refs": [],
            "knowledge_latest_refs": [],
            "validation_refs": [],
        },
        "observations": observations,
        "inventory_entries": inventory_entries,
        "attention_items": attention_items,
    }
    payload["content_digest"] = stable_json_digest(
        {
            key: value
            for key, value in payload.items()
            if key != "content_digest"
        }
    )
    return payload


def _observation(observation_type: str, source_ref: str, *, status: str = "ok") -> dict[str, object]:
    return {
        "observation_type": observation_type,
        "source_ref": source_ref,
        "status": status,
    }


class ValidateStackResumeContractTests(unittest.TestCase):
    def _temp_root(self) -> Path:
        temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(temp_dir.cleanup)
        root = Path(temp_dir.name)
        (root / "runtime" / "state" / "atlas").mkdir(parents=True, exist_ok=True)
        (root / "runtime" / "cortex" / "artifacts").mkdir(parents=True, exist_ok=True)
        (root / "stack.yaml").write_text("repo_registry: {}\n", encoding="utf-8")
        return root

    def _write_minimal_session_files(self, root: Path, *, final_status: str) -> tuple[str, dict[str, str]]:
        session_ref = "runtime/atlas/sessions/session-resume-contract/session.manifest.json"
        assignment_ref = "runtime/atlas/sessions/session-resume-contract/artifacts/worker.assignment.json"
        running_status_ref = "runtime/atlas/sessions/session-resume-contract/artifacts/worker.status.running.json"
        request_ref = "runtime/atlas/sessions/session-resume-contract/artifacts/privileged-action.request.json"
        approval_ref = "runtime/atlas/sessions/session-resume-contract/artifacts/approval.receipt.json"
        execution_receipt_ref = "runtime/lifeline/worker-execution/session-resume-contract-assignment/receipt.json"
        merge_request_ref = "runtime/cortex/supervisor/session-resume-contract/merge-request.json"
        pause_status_ref = "runtime/atlas/sessions/session-resume-contract/artifacts/worker.status.paused.json"
        resume_context_ref = "runtime/atlas/sessions/session-resume-contract/artifacts/merge/resume-context.session-resume-contract-worker.json"
        merge_assignment_ref = "runtime/atlas/sessions/session-resume-contract/artifacts/merge/worker.assignment.merge.json"
        merge_completion_ref = "runtime/atlas/sessions/session-resume-contract/artifacts/merge/completion.json"
        resume_request_ref = "runtime/atlas/sessions/session-resume-contract/artifacts/resume.request.json"
        resume_dispatch_ref = "runtime/atlas/sessions/session-resume-contract/artifacts/resume.dispatch.json"
        resume_run_manifest_ref = ".codex/logs/session-resume-contract/run.json"
        resumed_completed_status_ref = "runtime/atlas/sessions/session-resume-contract/artifacts/worker.status.completed.resumed.json"

        refs = {
            "session_ref": session_ref,
            "assignment_ref": assignment_ref,
            "running_status_ref": running_status_ref,
            "request_ref": request_ref,
            "approval_ref": approval_ref,
            "execution_receipt_ref": execution_receipt_ref,
            "merge_request_ref": merge_request_ref,
            "pause_status_ref": pause_status_ref,
            "resume_context_ref": resume_context_ref,
            "merge_assignment_ref": merge_assignment_ref,
            "merge_completion_ref": merge_completion_ref,
            "resume_request_ref": resume_request_ref,
            "resume_dispatch_ref": resume_dispatch_ref,
            "resume_run_manifest_ref": resume_run_manifest_ref,
            "resumed_completed_status_ref": resumed_completed_status_ref,
        }

        session_manifest = {
            "contract_version": "atlas.session.v1",
            "session_id": "session-resume-contract",
            "title": "Resume contract test",
            "task_id": "resume-contract",
            "scenario": "conflict_fixture",
            "session_state": final_status,
            "stack_lock_digest": "sha256:test-lock",
            "stack_manifest_ref": "stack.yaml",
            "created_at": "2026-06-14T12:00:00Z",
            "updated_at": "2026-06-14T12:10:00Z",
            "closed_at": "2026-06-14T12:10:00Z",
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
                "worker_id": "session-resume-contract-worker",
                "assignment_id": "session-resume-contract-assignment",
                "context_ref": "runtime/atlas/sessions/session-resume-contract/artifacts/worker.context.json",
                "assignment_ref": assignment_ref,
            },
            "refs": {
                "status_refs": [running_status_ref, resumed_completed_status_ref],
                "capability_profile_ref": "runtime/atlas/sessions/session-resume-contract/artifacts/capability-profile.json",
                "request_ref": request_ref,
                "approval_receipt_ref": approval_ref,
                "execution_receipt_ref": execution_receipt_ref,
                "bridge_record_ref": "runtime/atlas/sessions/session-resume-contract/artifacts/worker.execution.json",
                "merge_request_refs": [merge_request_ref],
                "pause_status_refs": [pause_status_ref],
                "resume_context_refs": [resume_context_ref],
                "merge_assignment_ref": merge_assignment_ref,
                "merge_prompt_ref": "runtime/atlas/sessions/session-resume-contract/artifacts/merge/merge.prompt.md",
                "merge_context_ref": "runtime/cortex/context/assignment-merge.json",
                "merge_completion_ref": merge_completion_ref,
                "resume_request_ref": resume_request_ref,
                "resume_dispatch_ref": resume_dispatch_ref,
                "resume_run_manifest_ref": resume_run_manifest_ref,
                "resumed_assignment_ref": "runtime/atlas/sessions/session-resume-contract/artifacts/worker.assignment.resumed.json",
                "resumed_running_status_ref": "runtime/atlas/sessions/session-resume-contract/artifacts/worker.status.running.resumed.json",
                "resumed_completed_status_ref": resumed_completed_status_ref,
            },
            "resume": {
                "status": final_status,
                "requested_at": "2026-06-14T12:05:00Z",
                "requested_worker_id": "session-resume-contract-worker",
                "resume_context_ref": resume_context_ref,
                "merge_completion_ref": merge_completion_ref,
                "dispatched_at": "2026-06-14T12:06:00Z",
                "completed_at": "2026-06-14T12:10:00Z",
                "failure_reason": "resume failed during proof" if final_status == "resume_failed" else None,
            },
            "completion": {
                "final_status": final_status,
                "final_status_ref": resumed_completed_status_ref if final_status == "completed" else resume_run_manifest_ref,
                "close_receipt_refs": [execution_receipt_ref],
            },
        }
        _write_json(root / session_ref, session_manifest)
        _write_json(root / running_status_ref, {"contract_version": "atlas.worker.status.v1", "state": "running"})
        _write_json(root / approval_ref, {"contract_version": "atlas.approval.receipt.v1", "approval_status": "approved"})
        _write_json(root / execution_receipt_ref, {"contract_version": "atlas.privileged-action.receipt.v1", "result": "succeeded"})
        return session_ref, refs

    def test_schema_admits_root_resume_states(self) -> None:
        payload = json.loads((ROOT / "schemas" / "atlas.session.v1.json").read_text(encoding="utf-8"))
        self.assertIn("resume_requested", payload["properties"]["session_state"]["enum"])
        self.assertIn("running", payload["properties"]["session_state"]["enum"])
        self.assertIn("resume_failed", payload["properties"]["session_state"]["enum"])
        self.assertIn("resume_failed", payload["properties"]["completion"]["properties"]["final_status"]["enum"])
        self.assertIn("resume_requested", payload["properties"]["resume"]["properties"]["status"]["enum"])
        self.assertIn("running", payload["properties"]["resume"]["properties"]["status"]["enum"])
        self.assertIn("resume_failed", payload["properties"]["resume"]["properties"]["status"]["enum"])

    def test_completed_resumed_session_requires_resume_transition_observations(self) -> None:
        root = self._temp_root()
        session_ref, refs = self._write_minimal_session_files(root, final_status="completed")

        observations = [
            _observation("session_state", session_ref),
            _observation("assignment_created", refs["assignment_ref"]),
            _observation("heartbeat", refs["running_status_ref"]),
            _observation("execution_requested", refs["request_ref"]),
            _observation("execution_approved", refs["approval_ref"]),
            _observation("execution_completed", refs["execution_receipt_ref"]),
            _observation("completed", refs["resumed_completed_status_ref"]),
            _observation("merge_requested", refs["merge_request_ref"]),
            _observation("paused", refs["pause_status_ref"]),
            _observation("merger_assigned", refs["merge_assignment_ref"]),
            _observation("resume_ready", refs["resume_context_ref"], status="ready"),
        ]
        inventory_entries = [{"entry_type": "session", "source_ref": session_ref}]
        snapshot = _snapshot_payload(
            kind="state",
            observations=observations,
            inventory_entries=inventory_entries,
            attention_items=[],
        )
        attention = _snapshot_payload(
            kind="attention",
            observations=[],
            inventory_entries=[],
            attention_items=[],
        )
        _write_json(root / "runtime/state/atlas/world-model.snapshot.latest.json", snapshot)
        _write_json(root / "runtime/state/atlas/world-model.attention.latest.json", attention)

        descriptors = [
            {
                "artifact_type": "session_manifest",
                "source_ref": session_ref,
                "state": {"final_status": "completed"},
                "links": {"close_receipt_refs": [refs["execution_receipt_ref"]]},
            }
        ]

        with ExitStack() as stack:
            stack.enter_context(patch("ops.validation.validate_stack.load_descriptors", return_value=descriptors))
            stack.enter_context(patch("ops.validation.validate_stack.load_observations", return_value=observations))
            findings = validate_world_model_state(root / "stack.yaml")

        messages = [finding.message for finding in findings]
        self.assertTrue(any("resume_requested" in message for message in messages))
        self.assertTrue(any("resume_dispatched" in message for message in messages))
        self.assertTrue(any("resume_completed" in message for message in messages))

    def test_resume_failed_session_requires_resume_failed_observation(self) -> None:
        root = self._temp_root()
        session_ref, refs = self._write_minimal_session_files(root, final_status="resume_failed")

        observations = [
            _observation("session_state", session_ref),
            _observation("assignment_created", refs["assignment_ref"]),
            _observation("heartbeat", refs["running_status_ref"]),
            _observation("execution_requested", refs["request_ref"]),
            _observation("execution_approved", refs["approval_ref"]),
            _observation("execution_completed", refs["execution_receipt_ref"]),
            _observation("merge_requested", refs["merge_request_ref"]),
            _observation("paused", refs["pause_status_ref"]),
            _observation("merger_assigned", refs["merge_assignment_ref"]),
            _observation("resume_ready", refs["resume_context_ref"], status="ready"),
            _observation("resume_requested", refs["resume_request_ref"], status="requested"),
            _observation("resume_dispatched", refs["resume_dispatch_ref"], status="running"),
        ]
        inventory_entries = [{"entry_type": "session", "source_ref": session_ref}]
        snapshot = _snapshot_payload(
            kind="state",
            observations=observations,
            inventory_entries=inventory_entries,
            attention_items=[],
        )
        attention = _snapshot_payload(
            kind="attention",
            observations=[],
            inventory_entries=[],
            attention_items=[],
        )
        _write_json(root / "runtime/state/atlas/world-model.snapshot.latest.json", snapshot)
        _write_json(root / "runtime/state/atlas/world-model.attention.latest.json", attention)

        descriptors = [
            {
                "artifact_type": "session_manifest",
                "source_ref": session_ref,
                "state": {"final_status": "resume_failed"},
                "links": {"close_receipt_refs": [refs["execution_receipt_ref"]]},
            }
        ]

        with ExitStack() as stack:
            stack.enter_context(patch("ops.validation.validate_stack.load_descriptors", return_value=descriptors))
            stack.enter_context(patch("ops.validation.validate_stack.load_observations", return_value=observations))
            findings = validate_world_model_state(root / "stack.yaml")

        messages = [finding.message for finding in findings]
        self.assertTrue(any("resume_failed" in message for message in messages))


if __name__ == "__main__":
    unittest.main()
