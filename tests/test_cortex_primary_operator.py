from __future__ import annotations

import io
import json
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import patch

from ops.cortex.primary_operator import (
    ACCEPTANCE_SCHEMA,
    PLAN_SCHEMA,
    RECEIPT_SCHEMA,
    build_decision,
    exit_code,
    main,
    validate_input_path,
    validate_output_path,
)


def _write(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value), encoding="utf-8")


class CortexPrimaryOperatorTests(unittest.TestCase):
    def _root(self) -> Path:
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        return Path(directory.name)

    def _plan(self, **overrides: object) -> dict[str, object]:
        value: dict[str, object] = {
            "schema_version": PLAN_SCHEMA,
            "plan_id": "plan-123",
            "plan_status": "ready_for_admission",
            "safe_to_admit": True,
            "blocked_reasons": [],
            "job_candidates": [{"job_id": "job-123"}],
            "source_digests": [{"path": "docs/source.md", "sha256": "a" * 64}],
        }
        value.update(overrides)
        return value

    def _authority(self, **overrides: object) -> dict[str, object]:
        value: dict[str, object] = {
            "authority_id": "authority-123",
            "host_capability": "full-access",
            "allowed_actions": [],
            "external_mutation_authority": False,
            "runtime_dispatch": False,
        }
        value.update(overrides)
        return value

    def _leases(self, **overrides: object) -> dict[str, object]:
        value: dict[str, object] = {"current": True, "leases": [], "conflicts": []}
        value.update(overrides)
        return value

    def _truth(self, **overrides: object) -> dict[str, object]:
        value: dict[str, object] = {"fresh": True, "digests": [{"path": "stack.yaml", "sha256": "b" * 64}]}
        value.update(overrides)
        return value

    def _decision(self, **overrides: object):
        return build_decision(
            plan=overrides.get("plan", self._plan()),
            authority=overrides.get("authority", self._authority()),
            leases=overrides.get("leases", self._leases()),
            truth=overrides.get("truth", self._truth()),
        )

    def test_ready_plan_is_accepted_with_correlated_receipt(self) -> None:
        acceptance, receipt = self._decision()
        self.assertEqual(ACCEPTANCE_SCHEMA, acceptance["schema_version"])
        self.assertEqual(RECEIPT_SCHEMA, receipt["schema_version"])
        self.assertEqual("accepted", acceptance["state"])
        self.assertEqual("completed", receipt["status"])
        self.assertEqual(acceptance["acceptance_id"], receipt["acceptance_id"])
        self.assertEqual("plan-123", receipt["plan_id"])

    def test_repeated_inputs_have_stable_ids(self) -> None:
        first = self._decision()
        second = self._decision()
        self.assertEqual(first[0]["acceptance_id"], second[0]["acceptance_id"])
        self.assertEqual(first[1]["receipt_id"], second[1]["receipt_id"])

    def test_unsafe_plan_is_rejected(self) -> None:
        acceptance, receipt = self._decision(plan=self._plan(safe_to_admit=False))
        self.assertEqual("rejected", acceptance["state"])
        self.assertEqual("failed", receipt["status"])
        self.assertIn("unsafe_plan", {item["code"] for item in acceptance["reasons"]})

    def test_blocked_plan_is_not_admitted(self) -> None:
        acceptance, _ = self._decision(plan=self._plan(plan_status="blocked", blocked_reasons=[{"code": "x"}]))
        self.assertEqual("blocked", acceptance["state"])
        self.assertIn("plan_not_ready", {item["code"] for item in acceptance["reasons"]})

    def test_external_authority_widening_is_rejected(self) -> None:
        acceptance, _ = self._decision(authority=self._authority(allowed_actions=["push", "discord_write"]))
        self.assertEqual("rejected", acceptance["state"])
        self.assertIn("authority_widening_rejected", {item["code"] for item in acceptance["reasons"]})

    def test_runtime_dispatch_is_rejected(self) -> None:
        acceptance, _ = self._decision(authority=self._authority(runtime_dispatch=True))
        self.assertEqual("rejected", acceptance["state"])
        self.assertIn("runtime_dispatch_rejected", {item["code"] for item in acceptance["reasons"]})

    def test_stale_truth_blocks(self) -> None:
        acceptance, _ = self._decision(truth=self._truth(fresh=False, stale=True))
        self.assertEqual("blocked", acceptance["state"])
        self.assertIn("stale_truth", {item["code"] for item in acceptance["reasons"]})

    def test_resource_lease_conflict_blocks(self) -> None:
        acceptance, _ = self._decision(leases=self._leases(conflicts=[{"resource": "canonical_root"}]))
        self.assertEqual("blocked", acceptance["state"])
        self.assertIn("resource_lease_conflict", {item["code"] for item in acceptance["reasons"]})

    def test_external_adapters_are_optional_transport(self) -> None:
        acceptance, receipt = self._decision(authority=self._authority(external_adapters=["chatgpt", "codex"]))
        self.assertEqual("accepted", acceptance["state"])
        self.assertEqual(["chatgpt", "codex"], acceptance["external_adapters"])
        self.assertFalse(acceptance["external_adapters_required"])
        self.assertFalse(receipt["external_adapters_required"])

    def test_no_execution_side_effects_are_claimed(self) -> None:
        acceptance, receipt = self._decision()
        self.assertFalse(acceptance["runtime_dispatch"])
        self.assertFalse(acceptance["safe_to_dispatch"])
        self.assertFalse(receipt["runtime_dispatch"])
        self.assertFalse(receipt["mutation_performed"])
        self.assertIsNone(receipt["execution_backend"])

    def test_paths_are_root_relative_and_output_is_tmp_only(self) -> None:
        root = self._root()
        _write(root / "tmp/atlas/plan.json", self._plan())
        self.assertIsNotNone(validate_input_path(root, "tmp/atlas/plan.json")[0])
        self.assertEqual("absolute_input_path", validate_input_path(root, "C:/ATLAS/plan.json")[1]["code"])
        self.assertEqual("parent_traversal", validate_input_path(root, "../plan.json")[1]["code"])
        self.assertIsNotNone(validate_output_path(root, "tmp/atlas/receipt.json")[0])
        self.assertEqual("unadmitted_output_path", validate_output_path(root, "docs/receipt.json")[1]["code"])

    def test_cli_writes_only_explicit_tmp_output(self) -> None:
        root = self._root()
        paths = {
            "execution_plan": "tmp/atlas/plan.json",
            "authority_envelope": "tmp/atlas/authority.json",
            "lease_receipts": "tmp/atlas/leases.json",
            "truth_digests": "tmp/atlas/truth.json",
        }
        _write(root / paths["execution_plan"], self._plan())
        _write(root / paths["authority_envelope"], self._authority())
        _write(root / paths["lease_receipts"], self._leases())
        _write(root / paths["truth_digests"], self._truth())
        argv = [
            "--execution-plan", paths["execution_plan"], "--authority-envelope", paths["authority_envelope"],
            "--lease-receipts", paths["lease_receipts"], "--truth-digests", paths["truth_digests"],
            "--output", "tmp/atlas/result.json",
        ]
        with patch("ops.cortex.primary_operator.atlas_root", return_value=root), redirect_stdout(io.StringIO()):
            code = main(argv)
        self.assertEqual(0, code)
        payload = json.loads((root / "tmp/atlas/result.json").read_text(encoding="utf-8"))
        self.assertEqual("accepted", payload["acceptance"]["state"])
        self.assertEqual({"plan.json", "authority.json", "leases.json", "truth.json", "result.json"}, {p.name for p in (root / "tmp/atlas").iterdir()})

    def test_nonaccepted_decisions_return_nonzero(self) -> None:
        self.assertEqual(0, exit_code("accepted"))
        self.assertEqual(2, exit_code("blocked"))
        self.assertEqual(2, exit_code("rejected"))


if __name__ == "__main__":
    unittest.main()
