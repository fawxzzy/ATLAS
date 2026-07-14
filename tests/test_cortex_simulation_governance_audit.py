from __future__ import annotations

import unittest
from pathlib import Path

from ops.cortex.simulation_governance_audit import _all_authority_false, run


ROOT = Path(__file__).resolve().parents[1]


class SimulationGovernanceAuditTests(unittest.TestCase):
    def test_live_root_passes_nine_machine_gates_and_waits_for_independent_review(self) -> None:
        result, code = run(root=ROOT, independent_review_path=None, output_path=None)
        self.assertEqual(1, code)
        self.assertEqual("awaiting_review", result["status"])
        self.assertEqual(9, result["audit"]["passed_count"])
        self.assertEqual("AWAIT_INDEPENDENT_REVIEW", result["audit"]["decision"])
        self.assertFalse(result["audit"]["gates"][-1]["passed"])
        self.assertFalse(result["audit"]["eligible_for_100"])

    def test_authority_scan_rejects_nested_true_authorization(self) -> None:
        self.assertTrue(_all_authority_false({"advisory_only": True, "nested": [{"execution_authorized": False}]}))
        self.assertFalse(_all_authority_false({"advisory_only": True, "nested": [{"execution_authorized": True}]}))
        self.assertFalse(_all_authority_false({"advisory_only": False}))

    def test_unsafe_review_and_output_paths_do_not_ratify(self) -> None:
        result, code = run(root=ROOT, independent_review_path="../review.json", output_path=None)
        self.assertEqual(1, code)
        self.assertEqual(9, result["audit"]["passed_count"])
        result, code = run(root=ROOT, independent_review_path=None, output_path="../audit.json")
        self.assertEqual(1, code)
        self.assertEqual("blocker", result["status"])


if __name__ == "__main__":
    unittest.main()
