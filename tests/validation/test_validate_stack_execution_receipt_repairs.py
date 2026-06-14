import json
import tempfile
import unittest
from contextlib import ExitStack
from pathlib import Path
from unittest.mock import patch

from ops.validation.validate_stack import validate_execution_receipt_repairs


def _write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def _session_manifest(*, execution_receipt_ref: str, close_receipt_refs: list[str]) -> dict[str, object]:
    return {
        "contract_version": "atlas.session.v1",
        "session_id": "session-proof",
        "title": "Proof",
        "task_id": "proof-task",
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
            "worker_id": "session-proof-worker",
            "assignment_id": "session-proof-assignment",
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
            "final_status_ref": "runtime/atlas/sessions/session-proof/artifacts/worker.status.completed.json",
            "close_receipt_refs": close_receipt_refs,
        },
    }


def _receipt(*, registry_digest: str, supersedes_receipt_ref: str | None = None) -> dict[str, object]:
    payload: dict[str, object] = {
        "contract_version": "atlas.privileged-action.receipt.v1",
        "receipt_id": "receipt-proof",
        "assignment_id": "session-proof-assignment",
        "request_id": "request-proof",
        "worker_id": "worker-proof",
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


class ValidateStackExecutionReceiptRepairTests(unittest.TestCase):
    def _temp_root(self) -> Path:
        temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(temp_dir.cleanup)
        root = Path(temp_dir.name)
        (root / "stack.yaml").write_text("repo_registry: {}\n", encoding="utf-8")
        return root

    def test_stale_manifest_links_are_reported_when_truthful_reconciled_receipt_exists(self) -> None:
        root = self._temp_root()
        session_ref = "runtime/atlas/sessions/session-proof/session.manifest.json"
        primary_ref = "runtime/lifeline/worker-execution/session-proof-assignment/receipt-primary.json"
        reconciled_ref = "runtime/lifeline/worker-execution/session-proof-assignment/receipt-primary--reconciled.json"

        _write_json(root / session_ref, _session_manifest(execution_receipt_ref=primary_ref, close_receipt_refs=[primary_ref]))
        _write_json(root / primary_ref, _receipt(registry_digest="sha256:old"))
        _write_json(root / reconciled_ref, _receipt(registry_digest="sha256:current", supersedes_receipt_ref=primary_ref))

        with ExitStack() as stack:
            stack.enter_context(patch("ops.validation.validate_stack.load_tool_registry_bundle", return_value={"registry_digest": "sha256:current"}))
            stack.enter_context(patch("ops.atlas.observations.load_tool_registry_bundle", return_value={"registry_digest": "sha256:current"}))
            findings = validate_execution_receipt_repairs(root / "stack.yaml")

        categories = {finding.category for finding in findings}
        self.assertIn("execution-receipt-manifest-stale", categories)
        self.assertIn("execution-receipt-close-links-stale", categories)

    def test_canonical_manifest_links_clear_stale_link_findings(self) -> None:
        root = self._temp_root()
        session_ref = "runtime/atlas/sessions/session-proof/session.manifest.json"
        primary_ref = "runtime/lifeline/worker-execution/session-proof-assignment/receipt-primary.json"
        reconciled_ref = "runtime/lifeline/worker-execution/session-proof-assignment/receipt-primary--reconciled.json"

        _write_json(root / session_ref, _session_manifest(execution_receipt_ref=reconciled_ref, close_receipt_refs=[reconciled_ref]))
        _write_json(root / primary_ref, _receipt(registry_digest="sha256:old"))
        _write_json(root / reconciled_ref, _receipt(registry_digest="sha256:current", supersedes_receipt_ref=primary_ref))

        with ExitStack() as stack:
            stack.enter_context(patch("ops.validation.validate_stack.load_tool_registry_bundle", return_value={"registry_digest": "sha256:current"}))
            stack.enter_context(patch("ops.atlas.observations.load_tool_registry_bundle", return_value={"registry_digest": "sha256:current"}))
            findings = validate_execution_receipt_repairs(root / "stack.yaml")

        categories = {finding.category for finding in findings}
        self.assertNotIn("execution-receipt-manifest-stale", categories)
        self.assertNotIn("execution-receipt-close-links-stale", categories)


if __name__ == "__main__":
    unittest.main()
