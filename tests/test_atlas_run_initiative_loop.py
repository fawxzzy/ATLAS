from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from ops.atlas import run_initiative_loop as initiative_loop


def _write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


class RunInitiativeLoopTests(unittest.TestCase):
    def _temp_root(self) -> Path:
        temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(temp_dir.cleanup)
        root = Path(temp_dir.name)
        (root / "stack.yaml").write_text("repo_registry: {}\n", encoding="utf-8")
        return root

    def test_run_initiative_loop_prunes_stale_attention_refs_and_refreshes_proposal(self) -> None:
        root = self._temp_root()
        task_id = "atlas-session-conflict"
        initiative_path = root / "docs" / "memory" / "initiatives" / "initiative-session-conflict-governed-resume.json"
        proposal_path = root / "runtime" / "atlas" / "proposed-sessions" / "session-proposed-atlas-session-conflict" / "session.manifest.json"
        source_ref = "runtime/atlas/sessions/session-atlas-session-conflict-20260414T080843Z/session.manifest.json"
        source_path = root / source_ref
        source_path.parent.mkdir(parents=True, exist_ok=True)
        source_path.write_text("{}\n", encoding="utf-8")

        initiative_payload = {
            "contract_version": "atlas.initiative.v1",
            "id": "initiative-session-conflict-governed-resume",
            "title": "Governed Session Conflict Resume",
            "summary": "summary",
            "status": "active",
            "owner": "stack-root",
            "created_at": "2026-04-15T04:20:00Z",
            "updated_at": "2026-04-15T04:20:00Z",
            "related_plan_refs": [],
            "related_decision_refs": [],
            "related_hypothesis_refs": [],
            "related_session_refs": [],
            "related_attention_refs": [
                "attention:sha256:stale",
                "attention:sha256:current",
                source_ref,
            ],
            "evidence_refs": [source_ref],
            "proposed_next_session_refs": [
                "runtime/atlas/proposed-sessions/session-proposed-atlas-session-conflict/session.manifest.json"
            ],
            "supersedes": [],
            "superseded_by": [],
            "metadata": {
                "authoring_source": "initiative-proposal-loop",
                "task_id": task_id,
                "attention_kinds": ["session_needs_resume"],
                "session_count": 1,
            },
        }
        _write_json(initiative_path, initiative_payload)

        existing_proposal_payload = {
            "contract_version": "atlas.session.v1",
            "session_id": "session-proposed-atlas-session-conflict",
            "title": "Proposed next session",
            "task_id": task_id,
            "scenario": "proposed_session",
            "session_role": "proposed_session",
            "session_state": "proposed",
            "automation_level": "observe",
            "max_automation_level": "approved_action",
            "stack_lock_digest": "sha256:test-lock",
            "stack_manifest_ref": "stack.yaml",
            "created_at": "2026-04-15T04:20:00Z",
            "updated_at": "2026-04-15T04:20:00Z",
            "closed_at": None,
            "orchestrator": {},
            "governed_surfaces": {},
            "worker": {"worker_id": "proposal-worker", "assignment_id": "proposal-assignment", "context_ref": None, "assignment_ref": None},
            "refs": {
                "status_refs": [],
                "capability_profile_ref": None,
                "request_ref": None,
                "approval_receipt_ref": None,
                "execution_receipt_ref": None,
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
                "status": "not_requested",
                "requested_at": None,
                "requested_worker_id": None,
                "resume_context_ref": None,
                "merge_completion_ref": None,
                "dispatched_at": None,
                "completed_at": None,
                "failure_reason": None,
            },
            "completion": {"final_status": None, "final_status_ref": None, "close_receipt_refs": []},
            "proposal": {
                "initiative_ref": "docs/memory/initiatives/initiative-session-conflict-governed-resume.json",
                "triggering_attention_refs": ["attention:sha256:stale", "attention:sha256:current"],
                "supporting_evidence_refs": [source_ref],
                "related_plan_refs": [],
                "related_decision_refs": [],
                "related_hypothesis_refs": [],
                "related_prior_session_refs": [],
                "generated_from_digest": "sha256:old",
            },
        }
        _write_json(proposal_path, existing_proposal_payload)

        attention_payload = {
            "attention_items": [
                {
                    "attention_id": "sha256:current",
                    "kind": "session_needs_resume",
                    "source_ref": source_ref,
                    "details": {"session_id": "session-atlas-session-conflict-20260414T080843Z", "task_id": task_id},
                }
            ]
        }

        initiative_record = SimpleNamespace(
            ref="docs/memory/initiatives/initiative-session-conflict-governed-resume.json",
            path=initiative_path,
            payload=initiative_payload,
        )

        with patch.object(initiative_loop, "load_latest_attention", return_value=attention_payload), patch.object(
            initiative_loop, "load_tool_registry_bundle", return_value={"registry_digest": "sha256:test-registry"}
        ), patch.object(
            initiative_loop, "load_stack_lock_payload", return_value={"lock_digest": "sha256:test-lock"}
        ), patch.object(
            initiative_loop, "load_memory_by_kind", return_value={"initiative": [initiative_record], "plan": [], "decision": [], "hypothesis": []}
        ), patch.object(
            initiative_loop, "all_session_manifests", return_value=[]
        ), patch.object(
            initiative_loop, "all_proposed_session_manifests", return_value=[(proposal_path, existing_proposal_payload)]
        ), patch.object(
            initiative_loop,
            "select_execution_surface",
            return_value={"tool_id": "read_only_scan", "extension_id": None, "max_automation_level": "approved_action"},
        ), patch.object(
            initiative_loop, "select_tool_entry", side_effect=lambda bundle, tool_id: {"tool_id": tool_id, "extension_id": None}
        ), patch.object(
            initiative_loop, "component_snapshot", return_value={}
        ), patch.object(
            initiative_loop, "write_working_memory_catalog", return_value={"output_path": "runtime/cortex/catalog/memory/working-memory.latest.json", "item_count": 1, "content_digest": "sha256:test"}
        ), patch.object(
            initiative_loop, "refresh_descriptors_and_world_model", return_value={"snapshot_ref": "runtime/state/atlas/world-model.snapshot.latest.json", "attention_ref": "runtime/state/atlas/world-model.attention.latest.json"}
        ):
            report = initiative_loop.run_initiative_loop(root=root, dry_run=False, refresh_inputs=False)

        self.assertEqual(report["initiative_count"], 1)
        self.assertEqual(report["proposal_count"], 1)

        refreshed_initiative = json.loads(initiative_path.read_text(encoding="utf-8"))
        self.assertEqual(
            refreshed_initiative["related_attention_refs"],
            ["attention:sha256:current", source_ref],
        )

        refreshed_proposal = json.loads(proposal_path.read_text(encoding="utf-8"))
        self.assertEqual(
            refreshed_proposal["proposal"]["triggering_attention_refs"],
            ["attention:sha256:current"],
        )


if __name__ == "__main__":
    unittest.main()
