from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from ops.atlas import resume_session as resume_module


def _write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


class AtlasResumeSessionTests(unittest.TestCase):
    def _temp_root(self) -> Path:
        temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(temp_dir.cleanup)
        return Path(temp_dir.name)

    def test_validate_resume_ready_session_accepts_recorded_resume_fixture(self) -> None:
        root = self._temp_root()
        session_id = "session-resume-validate"
        worker_id = f"{session_id}-worker"
        assignment_id = f"{session_id}-assignment"
        session_manifest_ref = f"runtime/atlas/sessions/{session_id}/session.manifest.json"
        merge_request_ref = f"runtime/cortex/supervisor/{session_id}/merge-request.json"
        merge_completion_ref = f"runtime/atlas/sessions/{session_id}/artifacts/merge/completion.json"
        resume_context_ref = (
            f"runtime/atlas/sessions/{session_id}/artifacts/merge/resume-context.{worker_id}.json"
        )
        paused_status_ref = f"runtime/atlas/sessions/{session_id}/artifacts/worker.status.paused.json"
        paused_handoff_ref = f"runtime/atlas/sessions/{session_id}/artifacts/paused-handoff.json"
        merge_handoff_ref = f"runtime/cortex/supervisor/{session_id}.merge-handoff.json"

        _write_json(
            root / merge_request_ref,
            {
                "contract_version": "atlas.worker.merge-request.v1",
                "merge_request_id": f"merge-request-{session_id}",
                "stack_lock_digest": "sha256:test-lock",
                "conflicting_workers": [worker_id, f"{session_id}-worker-fixture"],
                "overlaps": [
                    {
                        "repo_path": ".",
                        "path": "README-STACK.md",
                        "overlap_type": "line_overlap",
                        "file_digest_before": "sha256:file-before",
                        "conflicting_ranges": [
                            {
                                "worker_id": worker_id,
                                "start_line": 1,
                                "end_line": 2,
                                "op": "modify",
                            },
                            {
                                "worker_id": f"{session_id}-worker-fixture",
                                "start_line": 1,
                                "end_line": 2,
                                "op": "modify",
                            },
                        ],
                        "reason": "fixture overlap",
                    }
                ],
                "paused_handoff_refs": [paused_handoff_ref],
                "merge_worker_handoff": {
                    "worker_id": f"merge-{session_id}",
                    "assignment_id": f"assignment-merge-{session_id}",
                    "task_id": f"merge-{session_id}",
                    "handoff_ref": merge_handoff_ref,
                    "tool_id": "workspace_file_apply",
                    "extension_id": None,
                    "registry_digest": "sha256:test-registry",
                },
                "tool_id": "workspace_file_apply",
                "extension_id": None,
                "registry_digest": "sha256:test-registry",
            },
        )
        _write_json(
            root / merge_completion_ref,
            {
                "schema_version": "atlas.stack.supervisor-consumer.v1",
                "merge_request_id": f"merge-request-{session_id}",
                "merge_request_ref": merge_request_ref,
                "stack_lock_digest": "sha256:test-lock",
                "tool_id": "workspace_file_apply",
                "extension_id": None,
                "registry_digest": "sha256:test-registry",
                "resume_contexts": [
                    {
                        "worker_id": worker_id,
                        "assignment_id": assignment_id,
                        "path": resume_context_ref,
                    }
                ],
            },
        )
        _write_json(
            root / resume_context_ref,
            {
                "schema_version": "atlas.stack.resume-context.v1",
                "merge_request_id": f"merge-request-{session_id}",
                "worker_id": worker_id,
                "assignment_id": assignment_id,
                "stack_lock_digest": "sha256:test-lock",
                "tool_id": "workspace_file_apply",
                "extension_id": None,
                "registry_digest": "sha256:test-registry",
                "merge_request_ref": merge_request_ref,
                "paused_status_ref": paused_status_ref,
                "paused_handoff_refs": [paused_handoff_ref],
                "merge_handoff_ref": merge_handoff_ref,
                "transcript_dependency": False,
            },
        )
        _write_json(
            root / paused_status_ref,
            {
                "contract_version": "atlas.worker.status.v1",
                "worker_id": worker_id,
                "assignment_id": assignment_id,
                "tool_id": "workspace_file_apply",
                "extension_id": None,
                "registry_digest": "sha256:test-registry",
                "state": "paused",
            },
        )
        (root / paused_handoff_ref).parent.mkdir(parents=True, exist_ok=True)
        (root / paused_handoff_ref).write_text("{\"paused\":true}\n", encoding="utf-8")
        (root / merge_handoff_ref).parent.mkdir(parents=True, exist_ok=True)
        (root / merge_handoff_ref).write_text("{\"merge\":true}\n", encoding="utf-8")

        _write_json(
            root / session_manifest_ref,
            {
                "contract_version": "atlas.session.v1",
                "session_id": session_id,
                "title": "Resume validation fixture",
                "task_id": "resume-validation",
                "scenario": "conflict_fixture",
                "session_state": "resume_ready",
                "automation_level": "context",
                "stack_lock_digest": "sha256:test-lock",
                "stack_manifest_ref": "stack.yaml",
                "created_at": "2026-06-14T12:00:00Z",
                "updated_at": "2026-06-14T12:05:00Z",
                "closed_at": "2026-06-14T12:05:00Z",
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
                    "worker_id": worker_id,
                    "assignment_id": assignment_id,
                    "context_ref": f"runtime/atlas/sessions/{session_id}/artifacts/worker.context.json",
                    "assignment_ref": f"runtime/atlas/sessions/{session_id}/artifacts/worker.assignment.json",
                },
                "refs": {
                    "status_refs": [paused_status_ref],
                    "capability_profile_ref": None,
                    "request_ref": None,
                    "approval_receipt_ref": None,
                    "execution_receipt_ref": f"runtime/lifeline/worker-execution/{session_id}/receipt.json",
                    "bridge_record_ref": None,
                    "merge_request_refs": [merge_request_ref],
                    "pause_status_refs": [paused_status_ref],
                    "resume_context_refs": [resume_context_ref],
                    "merge_assignment_ref": None,
                    "merge_prompt_ref": None,
                    "merge_context_ref": None,
                    "merge_completion_ref": merge_completion_ref,
                    "resume_request_ref": None,
                    "resume_dispatch_ref": None,
                    "resume_run_manifest_ref": None,
                    "resumed_assignment_ref": None,
                    "resumed_running_status_ref": None,
                    "resumed_completed_status_ref": None,
                },
                "resume": {
                    "status": "resume_ready",
                    "requested_at": None,
                    "requested_worker_id": worker_id,
                    "resume_context_ref": resume_context_ref,
                    "merge_completion_ref": merge_completion_ref,
                    "dispatched_at": None,
                    "completed_at": None,
                    "failure_reason": None,
                },
                "completion": {
                    "final_status": "resume_ready",
                    "final_status_ref": merge_completion_ref,
                    "close_receipt_refs": [
                        f"runtime/lifeline/worker-execution/{session_id}/receipt.json"
                    ],
                },
            },
        )

        with (
            patch.object(resume_module, "ROOT", root),
            patch.object(
                resume_module,
                "load_stack_lock_payload",
                return_value={"lock_digest": "sha256:test-lock"},
            ),
            patch.object(
                resume_module,
                "load_tool_registry_bundle",
                return_value={"registry_digest": "sha256:test-registry"},
            ),
            patch.object(
                resume_module,
                "list_inventory",
                return_value={"entries": [{"key": session_id, "status": "resume_ready"}]},
            ),
            patch.object(
                resume_module,
                "list_attention",
                return_value={"attention_items": []},
            ),
        ):
            context = resume_module.validate_resume_ready_session(session_id)

        self.assertEqual(context["session_id"], session_id)
        self.assertEqual(context["worker_id"], worker_id)
        self.assertEqual(context["assignment_id"], assignment_id)
        self.assertEqual(context["merge_request_ref"], merge_request_ref)
        self.assertEqual(context["merge_completion_ref"], merge_completion_ref)
        self.assertEqual(context["resume_context_ref"], resume_context_ref)
        self.assertEqual(context["paused_handoff_refs"], [paused_handoff_ref])
        self.assertEqual(context["merge_handoff_ref"], merge_handoff_ref)

    def test_resume_session_emits_request_dispatch_and_completion_artifacts(self) -> None:
        root = self._temp_root()
        session_id = "session-resume-proof"
        session_root = root / "runtime" / "atlas" / "sessions" / session_id
        artifact_root = session_root / "artifacts"
        session_manifest_path = session_root / "session.manifest.json"
        run_manifest_path = root / ".codex" / "logs" / "resume-proof" / "run.json"
        resumed_completed_status_ref = (
            f"runtime/atlas/sessions/{session_id}/artifacts/worker.status.completed.resumed.json"
        )
        resumed_completed_status_path = root / resumed_completed_status_ref

        _write_json(
            resumed_completed_status_path,
            {
                "contract_version": "atlas.worker.status.v1",
                "state": "completed",
            },
        )
        _write_json(
            run_manifest_path,
            {
                "status": "success",
                "workerArtifacts": {
                    "assignment": f"runtime/atlas/sessions/{session_id}/artifacts/worker.assignment.resumed.json",
                    "runningStatus": f"runtime/atlas/sessions/{session_id}/artifacts/worker.status.running.resumed.json",
                    "completedStatus": resumed_completed_status_ref,
                },
            },
        )

        manifest = {
            "contract_version": "atlas.session.v1",
            "session_id": session_id,
            "title": "Resume proof session",
            "task_id": "resume-proof",
            "scenario": "conflict_fixture",
            "session_state": "resume_ready",
            "automation_level": "context",
            "stack_lock_digest": "sha256:test-lock",
            "stack_manifest_ref": "stack.yaml",
            "created_at": "2026-06-14T12:00:00Z",
            "updated_at": "2026-06-14T12:00:00Z",
            "closed_at": "2026-06-14T12:00:00Z",
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
                "status_refs": [],
                "capability_profile_ref": None,
                "request_ref": None,
                "approval_receipt_ref": None,
                "execution_receipt_ref": f"runtime/lifeline/worker-execution/{session_id}/receipt.json",
                "bridge_record_ref": None,
                "merge_request_refs": [],
                "pause_status_refs": [],
                "resume_context_refs": [],
                "merge_assignment_ref": None,
                "merge_prompt_ref": None,
                "merge_context_ref": None,
                "merge_completion_ref": None,
                "resume_request_ref": None,
                "resume_dispatch_ref": None,
                "resume_run_manifest_ref": None,
                "resumed_assignment_ref": None,
                "resumed_running_status_ref": None,
                "resumed_completed_status_ref": None,
            },
            "resume": {
                "status": "resume_ready",
                "requested_at": None,
                "requested_worker_id": None,
                "resume_context_ref": None,
                "merge_completion_ref": None,
                "dispatched_at": None,
                "completed_at": None,
                "failure_reason": None,
            },
            "completion": {
                "final_status": "resume_ready",
                "final_status_ref": "runtime/atlas/sessions/session-resume-proof/artifacts/merge/completion.json",
                "close_receipt_refs": [
                    f"runtime/lifeline/worker-execution/{session_id}/receipt.json"
                ],
            },
        }
        _write_json(session_manifest_path, manifest)

        adapter_path = root / "repos" / "_stack" / "ops" / "codex" / "repos" / "atlas" / "adapter.json"
        runner_path = root / "repos" / "_stack" / "ops" / "codex" / "Invoke-CodexRepoTask.ps1"
        adapter_path.parent.mkdir(parents=True, exist_ok=True)
        runner_path.parent.mkdir(parents=True, exist_ok=True)
        adapter_path.write_text("{}\n", encoding="utf-8")
        runner_path.write_text("# runner\n", encoding="utf-8")

        context = {
            "session_id": session_id,
            "session_root": session_root,
            "session_manifest_path": session_manifest_path,
            "manifest": manifest,
            "stack_lock_digest": "sha256:test-lock",
            "registry_digest": "sha256:test-registry",
            "tool_id": "workspace_file_apply",
            "extension_id": None,
            "worker_id": f"{session_id}-worker",
            "assignment_id": f"{session_id}-assignment",
            "merge_request_ref": f"runtime/cortex/supervisor/{session_id}/merge-request.json",
            "merge_completion_ref": f"runtime/atlas/sessions/{session_id}/artifacts/merge/completion.json",
            "merge_prompt_ref": None,
            "merge_context_ref": None,
            "merge_assignment_ref": None,
            "resume_context_ref": f"runtime/atlas/sessions/{session_id}/artifacts/merge/resume-context.{session_id}-worker.json",
            "paused_handoff_refs": ["runtime/atlas/sessions/session-resume-proof/artifacts/pause-handoff.json"],
            "merge_handoff_ref": f"runtime/cortex/supervisor/{session_id}.merge-handoff.json",
        }

        emitted: list[tuple[str, str]] = []
        sync_summary = {
            "status_snapshot_ref": f"runtime/atlas/sessions/{session_id}/status.snapshot.json",
            "world_model_summary": {
                "snapshot_ref": "runtime/state/atlas/world-model.snapshot.latest.json",
                "attention_ref": "runtime/state/atlas/world-model.attention.latest.json",
            },
        }

        with (
            patch.object(resume_module, "ROOT", root),
            patch.object(resume_module, "ATLAS_ADAPTER_PATH", adapter_path),
            patch.object(resume_module, "CODEX_RUNNER_PATH", runner_path),
            patch.object(resume_module, "validate_resume_ready_session", return_value=context),
            patch.object(resume_module, "collect_run_manifest_paths", side_effect=[[], [run_manifest_path]]),
            patch.object(
                resume_module,
                "run_resume_dispatch",
                return_value=SimpleNamespace(returncode=0, stdout="", stderr=""),
            ),
            patch.object(resume_module, "sync_session_outputs", return_value=sync_summary),
            patch.object(
                resume_module,
                "emit_resume_observation",
                side_effect=lambda **kwargs: emitted.append(
                    (str(kwargs["observation_type"]), str(kwargs["source_ref"]))
                ),
            ),
        ):
            result = resume_module.resume_session(session_id=session_id, no_commit=True)

        updated_manifest = json.loads(session_manifest_path.read_text(encoding="utf-8"))
        request_payload = json.loads((artifact_root / "resume.request.json").read_text(encoding="utf-8"))
        dispatch_payload = json.loads((artifact_root / "resume.dispatch.json").read_text(encoding="utf-8"))

        self.assertEqual(result["session_state"], "completed")
        self.assertEqual(updated_manifest["session_state"], "completed")
        self.assertEqual(updated_manifest["resume"]["status"], "completed")
        self.assertEqual(updated_manifest["completion"]["final_status"], "completed")
        self.assertEqual(
            updated_manifest["refs"]["resumed_completed_status_ref"],
            resumed_completed_status_ref,
        )
        self.assertEqual(
            request_payload["contract_version"],
            "atlas.session.resume.request.v1",
        )
        self.assertEqual(request_payload["worker_id"], f"{session_id}-worker")
        self.assertEqual(request_payload["assignment_id"], f"{session_id}-assignment")
        self.assertIn(
            f"runtime/atlas/sessions/{session_id}/session.manifest.json",
            request_payload["source_artifact_refs"],
        )
        self.assertEqual(
            dispatch_payload["contract_version"],
            "atlas.session.resume.dispatch.v1",
        )
        self.assertEqual(dispatch_payload["worker_id"], f"{session_id}-worker")
        self.assertEqual(dispatch_payload["assignment_id"], f"{session_id}-assignment")
        self.assertEqual(
            dispatch_payload["resume_request_ref"],
            f"runtime/atlas/sessions/{session_id}/artifacts/resume.request.json",
        )
        self.assertEqual(dispatch_payload["runner"]["no_commit"], True)
        self.assertEqual(dispatch_payload["runner"]["status"], "success")
        self.assertEqual(
            dispatch_payload["resumed_completed_status_ref"],
            resumed_completed_status_ref,
        )
        self.assertIn(
            ".codex/logs/resume-proof/run.json",
            dispatch_payload["source_artifact_refs"],
        )
        self.assertEqual(
            [item[0] for item in emitted],
            ["resume_requested", "resume_dispatched", "resume_completed"],
        )


if __name__ == "__main__":
    unittest.main()
