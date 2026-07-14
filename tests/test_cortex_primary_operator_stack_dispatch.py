from __future__ import annotations

import io
import json
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import patch

from ops.cortex.primary_operator import build_decision
from ops.cortex.primary_operator_stack_dispatch import (
    REQUEST_SCHEMA,
    RESULT_SCHEMA,
    build_dispatch_request,
    correlate_result,
    main,
    render_prompt,
    validate_stack_runtime_input,
    validate_output_path,
)


def _write(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value), encoding="utf-8")


class CortexPrimaryOperatorStackDispatchTests(unittest.TestCase):
    def _root(self) -> Path:
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        return Path(directory.name)

    def _plan(self, **overrides: object) -> dict[str, object]:
        value: dict[str, object] = {
            "schema_version": "atlas.cortex.execution_plan.v1", "plan_id": "plan-123",
            "plan_status": "ready_for_admission", "safe_to_admit": True, "blocked_reasons": [],
        }
        value.update(overrides)
        return value

    def _primary(self, plan: dict[str, object] | None = None):
        plan = plan or self._plan()
        return build_decision(
            plan=plan,
            authority={"authority_id": "a", "allowed_actions": [], "external_mutation_authority": False, "runtime_dispatch": False},
            leases={"current": True, "leases": [], "conflicts": []},
            truth={"fresh": True, "digests": [{"path": "stack.yaml", "sha256": "a" * 64}]},
        )

    def _request(self):
        plan = self._plan()
        acceptance, receipt = self._primary(plan)
        request, blockers = build_dispatch_request(acceptance=acceptance, primary_receipt=receipt, plan=plan)
        self.assertEqual([], blockers)
        return request

    def _stack_result(self, request: dict[str, object], *, status: str = "success_no_changes"):
        run_id, job_id = "run-123", "atlas-stack-run-123"
        succeeded = status == "success_no_changes"
        job = {
            "contract_version": "atlas.job-envelope.v2", "job_id": job_id,
            "correlations": {"parent_job_id": request["acceptance_id"]}, "extensions": {"run_id": run_id},
        }
        receipt = {
            "contract_version": "atlas.execution-receipt.v2", "receipt_id": "receipt-123", "job_id": job_id,
            "status": "succeeded" if succeeded else "failed", "changed_paths": [], "commits": [],
            "authority_actions": [], "extensions": {"run_id": run_id},
        }
        manifest = {
            "runId": run_id, "status": status, "changedPaths": [], "commitSha": None,
            "atlasContractsV2": {"validation": {"jobEnvelope": {"ok": True}, "executionReceipt": {"ok": True}}},
        }
        return manifest, job, receipt

    def test_safe_acceptance_builds_stable_ready_request(self) -> None:
        first, blockers = build_dispatch_request(acceptance=self._primary()[0], primary_receipt=self._primary()[1], plan=self._plan())
        second, _ = build_dispatch_request(acceptance=self._primary()[0], primary_receipt=self._primary()[1], plan=self._plan())
        self.assertEqual([], blockers)
        self.assertEqual(REQUEST_SCHEMA, first["schema_version"])
        self.assertEqual("ready_for_stack_dispatch", first["status"])
        self.assertEqual(first["request_id"], second["request_id"])
        self.assertEqual(first["acceptance_id"], first["session_id"])

    def test_unsafe_acceptance_is_rejected(self) -> None:
        plan = self._plan(safe_to_admit=False)
        acceptance, receipt = self._primary(plan)
        request, blockers = build_dispatch_request(acceptance=acceptance, primary_receipt=receipt, plan=plan)
        self.assertEqual("blocked", request["status"])
        self.assertTrue(blockers)

    def test_request_denies_all_external_actions(self) -> None:
        request = self._request()
        self.assertEqual([], request["authority"]["external_actions"])
        for field in ("push", "deploy", "production", "discord", "board", "data_mutation"):
            self.assertFalse(request["authority"][field])

    def test_prompt_uses_verified_no_change_and_exact_handoff(self) -> None:
        request = self._request()
        prompt = render_prompt(request, request_path=Path("C:/ATLAS/runtime/atlas/sessions/a/cortex-stack-dispatch-request.json"))
        self.assertIn("Allow No Changes: true", prompt)
        self.assertIn("No-Change Assertion IDs: dispatch-request-consumed, no-mutation-confirmed", prompt)
        self.assertIn("Handoff Ref: C:\\ATLAS\\runtime\\atlas\\sessions", prompt)
        self.assertIn("Do not modify tracked files", prompt)

    def test_success_result_preserves_complete_chain(self) -> None:
        request = self._request()
        manifest, job, receipt = self._stack_result(request)
        result = correlate_result(request=request, run_manifest=manifest, job_envelope=job, execution_receipt=receipt)
        self.assertEqual(RESULT_SCHEMA, result["schema_version"])
        self.assertEqual("succeeded", result["status"])
        self.assertTrue(result["correlation_complete"])
        self.assertTrue(result["safe_to_close"])
        self.assertEqual(request["acceptance_id"], result["acceptance_id"])

    def test_failed_terminal_result_still_correlates(self) -> None:
        request = self._request()
        manifest, job, receipt = self._stack_result(request, status="codex_failed")
        result = correlate_result(request=request, run_manifest=manifest, job_envelope=job, execution_receipt=receipt)
        self.assertEqual("failed_correlated", result["status"])
        self.assertTrue(result["correlation_complete"])
        self.assertFalse(result["safe_to_close"])

    def test_parent_job_mismatch_blocks(self) -> None:
        request = self._request()
        manifest, job, receipt = self._stack_result(request)
        job["correlations"]["parent_job_id"] = "wrong"
        result = correlate_result(request=request, run_manifest=manifest, job_envelope=job, execution_receipt=receipt)
        self.assertFalse(result["correlation_complete"])
        self.assertIn("parent_job_correlation_mismatch", {item["code"] for item in result["blockers"]})

    def test_commit_or_authority_action_blocks_canary(self) -> None:
        request = self._request()
        manifest, job, receipt = self._stack_result(request)
        manifest["commitSha"] = "abc"
        receipt["authority_actions"] = ["push"]
        result = correlate_result(request=request, run_manifest=manifest, job_envelope=job, execution_receipt=receipt)
        codes = {item["code"] for item in result["blockers"]}
        self.assertIn("unexpected_commit", codes)
        self.assertIn("unexpected_authority_action", codes)

    def test_output_paths_follow_runtime_and_tmp_policy(self) -> None:
        root = self._root()
        self.assertIsNotNone(validate_output_path(root, "runtime/atlas/sessions/a/cortex-stack-dispatch-request.json", kind="request")[0])
        self.assertIsNotNone(validate_output_path(root, "runtime/atlas/sessions/a/cortex-stack-result-correlation.json", kind="result")[0])
        self.assertIsNotNone(validate_output_path(root, "tmp/atlas/canary.md", kind="prompt")[0])
        self.assertEqual("unadmitted_output_path", validate_output_path(root, "docs/canary.md", kind="prompt")[1]["code"])

    def test_stack_runtime_inputs_are_narrowly_admitted(self) -> None:
        root = self._root()
        run_dir = root / "repos/_stack/.codex/logs/run-123"
        for name in ("run.json", "atlas.job-envelope.v2.json", "atlas.execution-receipt.v2.json"):
            _write(run_dir / name, {})
        self.assertEqual(
            run_dir / "run.json",
            validate_stack_runtime_input(root, str(run_dir / "run.json"), artifact="run_manifest")[0],
        )
        self.assertEqual(
            "unexpected_stack_runtime_artifact",
            validate_stack_runtime_input(root, str(run_dir / "run.json"), artifact="job_envelope")[1]["code"],
        )
        outside = root / "tmp/atlas/run.json"
        _write(outside, {})
        self.assertEqual(
            "unadmitted_stack_runtime_path",
            validate_stack_runtime_input(root, str(outside), artifact="run_manifest")[1]["code"],
        )

    def test_prepare_cli_writes_request_and_prompt_only(self) -> None:
        root = self._root()
        plan = self._plan()
        acceptance, receipt = self._primary(plan)
        _write(root / "tmp/atlas/plan.json", plan)
        _write(root / "tmp/atlas/acceptance.json", acceptance)
        _write(root / "tmp/atlas/receipt.json", receipt)
        argv = [
            "prepare", "--acceptance", "tmp/atlas/acceptance.json", "--primary-receipt", "tmp/atlas/receipt.json",
            "--plan", "tmp/atlas/plan.json", "--request-output", "runtime/atlas/sessions/a/cortex-stack-dispatch-request.json",
            "--prompt-output", "tmp/atlas/canary.md",
        ]
        with patch("ops.cortex.primary_operator_stack_dispatch.atlas_root", return_value=root), redirect_stdout(io.StringIO()):
            code = main(argv)
        self.assertEqual(0, code)
        self.assertTrue((root / "runtime/atlas/sessions/a/cortex-stack-dispatch-request.json").is_file())
        self.assertTrue((root / "tmp/atlas/canary.md").is_file())

    def test_correlate_cli_writes_durable_result(self) -> None:
        root = self._root()
        request = self._request()
        manifest, job, receipt = self._stack_result(request)
        _write(root / "runtime/atlas/request.json", request)
        run_dir = root / "repos/_stack/.codex/logs/run-123"
        _write(run_dir / "run.json", manifest)
        _write(run_dir / "atlas.job-envelope.v2.json", job)
        _write(run_dir / "atlas.execution-receipt.v2.json", receipt)
        argv = [
            "correlate", "--request", "runtime/atlas/request.json", "--run-manifest", str(run_dir / "run.json"),
            "--job-envelope", str(run_dir / "atlas.job-envelope.v2.json"),
            "--execution-receipt", str(run_dir / "atlas.execution-receipt.v2.json"),
            "--output", "runtime/atlas/sessions/a/cortex-stack-result-correlation.json",
        ]
        with patch("ops.cortex.primary_operator_stack_dispatch.atlas_root", return_value=root), redirect_stdout(io.StringIO()):
            code = main(argv)
        self.assertEqual(0, code)
        value = json.loads((root / "runtime/atlas/sessions/a/cortex-stack-result-correlation.json").read_text(encoding="utf-8"))
        self.assertEqual("succeeded", value["status"])


if __name__ == "__main__":
    unittest.main()
