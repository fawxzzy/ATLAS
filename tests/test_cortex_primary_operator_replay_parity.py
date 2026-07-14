from __future__ import annotations

import io
import hashlib
import json
import tempfile
import unittest
from collections import OrderedDict
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import patch

from ops.cortex.primary_operator import build_decision
from ops.cortex.primary_operator_replay_parity import (
    ADAPTER_SCHEMA,
    REPORT_SCHEMA,
    build_report,
    exit_code,
    main,
)


def _write(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value), encoding="utf-8")


class CortexPrimaryOperatorReplayParityTests(unittest.TestCase):
    SOURCE_DIGESTS = [
        OrderedDict((("path", "tmp/atlas/authority.json"), ("sha256", "a" * 64))),
        OrderedDict((("path", "tmp/atlas/leases.json"), ("sha256", "b" * 64))),
        OrderedDict((("path", "tmp/atlas/plan.json"), ("sha256", "c" * 64))),
        OrderedDict((("path", "tmp/atlas/truth.json"), ("sha256", "d" * 64))),
    ]
    def _root(self) -> Path:
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        return Path(directory.name)

    def _plan(self, **overrides: object) -> dict[str, object]:
        value: dict[str, object] = {
            "schema_version": "atlas.cortex.execution_plan.v1",
            "plan_id": "plan-123", "plan_status": "ready_for_admission",
            "safe_to_admit": True, "blocked_reasons": [], "source_digests": [],
        }
        value.update(overrides)
        return value

    def _authority(self, **overrides: object) -> dict[str, object]:
        value: dict[str, object] = {
            "authority_id": "authority-123", "host_capability": "full-access",
            "allowed_actions": [], "external_mutation_authority": False, "runtime_dispatch": False,
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

    def _adapter(self, **overrides: object) -> dict[str, object]:
        acceptance, _ = build_decision(
            plan=self._plan(), authority=self._authority(), leases=self._leases(), truth=self._truth()
        )
        value: dict[str, object] = {
            "schema_version": ADAPTER_SCHEMA, "adapter": "codex", "plan_id": acceptance["plan_id"],
            "acceptance_state": acceptance["state"], "reason_codes": [],
            "source_digests": self.SOURCE_DIGESTS,
            "receipt_correlation": {"plan_id": acceptance["plan_id"], "acceptance_id": acceptance["acceptance_id"]},
            "runtime_dispatch": False, "mutation_performed": False, "operator_plane": "_stack",
            "external_adapters_required": False, "external_action_authority": [],
        }
        value.update(overrides)
        return value

    def _report(self, adapter: dict[str, object] | None = None, **overrides: object):
        return build_report(
            plan=overrides.get("plan", self._plan()), authority=overrides.get("authority", self._authority()),
            leases=overrides.get("leases", self._leases()), truth=overrides.get("truth", self._truth()),
            adapter=adapter,
            source_digests=self.SOURCE_DIGESTS,
        )

    def test_internal_no_adapter_baseline_is_complete_and_safe(self) -> None:
        report = self._report()
        self.assertEqual(REPORT_SCHEMA, report["schema_version"])
        self.assertEqual("internal_no_adapter", report["replay_mode"])
        self.assertEqual("equivalent", report["result_class"])
        self.assertTrue(report["safe_to_use"])
        self.assertFalse(report["external_adapters_required"])

    def test_repeated_reports_have_stable_identity(self) -> None:
        self.assertEqual(self._report()["report_id"], self._report()["report_id"])

    def test_equivalent_optional_adapter_projection_is_safe(self) -> None:
        report = self._report(self._adapter())
        self.assertEqual("optional_adapter_projection", report["replay_mode"])
        self.assertEqual("equivalent", report["result_class"])
        self.assertTrue(report["safe_to_use"])

    def test_cortex_stricter_adapter_is_not_safe_parity(self) -> None:
        blocked_plan = self._plan(plan_status="blocked", safe_to_admit=True, blocked_reasons=[{"code": "root_busy"}])
        acceptance, _ = build_decision(
            plan=blocked_plan, authority=self._authority(), leases=self._leases(), truth=self._truth()
        )
        adapter = self._adapter(
            plan_id=acceptance["plan_id"], acceptance_state="accepted", reason_codes=[],
            receipt_correlation={"plan_id": acceptance["plan_id"], "acceptance_id": acceptance["acceptance_id"]},
        )
        report = self._report(adapter, plan=blocked_plan)
        self.assertEqual("cortex_stricter", report["result_class"])
        self.assertFalse(report["safe_to_use"])

    def test_adapter_stricter_projection_is_safe(self) -> None:
        adapter = self._adapter(acceptance_state="blocked", reason_codes=["adapter_hold"])
        report = self._report(adapter)
        self.assertEqual("adapter_stricter", report["result_class"])
        self.assertTrue(report["safe_to_use"])

    def test_authority_widening_is_regression(self) -> None:
        report = self._report(self._adapter(external_action_authority=["push"]))
        self.assertEqual("authority_regression", report["result_class"])
        self.assertFalse(report["safe_to_use"])
        self.assertIn("adapter_authority_widening", {item["code"] for item in report["authority_regressions"]})

    def test_dispatch_or_mutation_claim_is_regression(self) -> None:
        report = self._report(self._adapter(runtime_dispatch=True, mutation_performed=True))
        self.assertEqual("authority_regression", report["result_class"])
        codes = {item["code"] for item in report["authority_regressions"]}
        self.assertIn("adapter_dispatch_claim", codes)
        self.assertIn("adapter_mutation_claim", codes)

    def test_plan_or_receipt_correlation_mismatch_is_blocked(self) -> None:
        report = self._report(self._adapter(plan_id="plan-other", receipt_correlation={"plan_id": "plan-other", "acceptance_id": "wrong"}))
        self.assertEqual("mismatch", report["result_class"])
        self.assertFalse(report["safe_to_use"])
        codes = {item["code"] for item in report["mismatches"]}
        self.assertIn("plan_identity_mismatch", codes)
        self.assertIn("receipt_correlation_mismatch", codes)

    def test_adapter_source_digest_mismatch_is_blocked(self) -> None:
        report = self._report(self._adapter(source_digests=[]))
        self.assertEqual("mismatch", report["result_class"])
        self.assertFalse(report["safe_to_use"])
        self.assertIn("source_digest_mismatch", {item["code"] for item in report["mismatches"]})

    def test_adapter_source_digests_are_compared(self) -> None:
        report = self._report(self._adapter())
        comparison = next(item for item in report["comparisons"] if item["dimension"] == "source_digests")
        self.assertEqual(self.SOURCE_DIGESTS, comparison["internal"])
        self.assertEqual(self.SOURCE_DIGESTS, comparison["adapter"])

    def test_report_never_claims_execution_side_effects(self) -> None:
        report = self._report(self._adapter())
        self.assertFalse(report["runtime_dispatch"])
        self.assertFalse(report["mutation_performed"])
        self.assertEqual("_stack", report["operator_plane"])

    def test_cli_writes_only_explicit_tmp_output(self) -> None:
        root = self._root()
        plan, authority, leases, truth = self._plan(), self._authority(), self._leases(), self._truth()
        acceptance, _ = build_decision(plan=plan, authority=authority, leases=leases, truth=truth)
        adapter = self._adapter(
            plan_id=acceptance["plan_id"],
            receipt_correlation={"plan_id": acceptance["plan_id"], "acceptance_id": acceptance["acceptance_id"]},
        )
        values = {"plan": plan, "authority": authority, "leases": leases, "truth": truth, "adapter": adapter}
        for name, value in values.items():
            if name == "adapter":
                continue
            _write(root / f"tmp/atlas/{name}.json", value)
        adapter["source_digests"] = sorted(
            [
                OrderedDict(
                    (("path", f"tmp/atlas/{name}.json"),
                     ("sha256", hashlib.sha256((root / f"tmp/atlas/{name}.json").read_bytes()).hexdigest()))
                )
                for name in ("plan", "authority", "leases", "truth")
            ],
            key=lambda item: item["path"],
        )
        _write(root / "tmp/atlas/adapter.json", adapter)
        argv = [
            "--execution-plan", "tmp/atlas/plan.json", "--authority-envelope", "tmp/atlas/authority.json",
            "--lease-receipts", "tmp/atlas/leases.json", "--truth-digests", "tmp/atlas/truth.json",
            "--adapter-projection", "tmp/atlas/adapter.json", "--output", "tmp/atlas/report.json",
        ]
        with patch("ops.cortex.primary_operator_replay_parity.atlas_root", return_value=root), redirect_stdout(io.StringIO()):
            code = main(argv)
        self.assertEqual(0, code)
        payload = json.loads((root / "tmp/atlas/report.json").read_text(encoding="utf-8"))
        self.assertEqual("equivalent", payload["result_class"])
        self.assertEqual({"plan.json", "authority.json", "leases.json", "truth.json", "adapter.json", "report.json"}, {p.name for p in (root / "tmp/atlas").iterdir()})

    def test_non_safe_report_returns_nonzero(self) -> None:
        self.assertEqual(0, exit_code(self._report()))
        self.assertEqual(2, exit_code(self._report(self._adapter(runtime_dispatch=True))))


if __name__ == "__main__":
    unittest.main()
