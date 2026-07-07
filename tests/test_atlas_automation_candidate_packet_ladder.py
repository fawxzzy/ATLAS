from __future__ import annotations

import io
import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from ops.atlas import automation_candidate_packet_ladder as ladder
from ops.atlas import receipt_automation_candidate_review as review

HANDOFF_DECISION_REF = "docs/ops/AI-REPETITION-TO-AUTOMATION-PIPELINE-HANDOFF-HELPER-CANDIDATE-REVIEW-CONTRACT-FREEZE-2026-07-07.md"


def _review(candidate_id: str, *, status: str = "review_ready", repeat_count: int = 5) -> dict[str, object]:
    return {
        "candidate_id": candidate_id,
        "category": "helper",
        "review_status": status,
        "review_priority": 0,
        "repeat_count": repeat_count,
        "supporting_receipt_count": repeat_count,
        "recommended_review_packet": f"AI Repetition-to-Automation Pipeline {candidate_id} candidate-review contract freeze",
        "required_operator_decision": "contract_freeze_or_reject",
        "evidence_summary": f"repeated {candidate_id}",
        "boundaries": ["read_only", "no_marker_movement"],
    }


def _review_report(*reviews: dict[str, object], status: str = review.STATUS_OK) -> dict[str, object]:
    return {
        "schema_version": review.SCHEMA_VERSION,
        "status": status,
        "root": "C:/ATLAS",
        "branch": "main",
        "head": "abc123",
        "candidate_report_ref": "live:test",
        "source_report_schema": "atlas.receipt_automation_candidate_extractor.v1",
        "source_report_status": "ok",
        "candidate_count": len(reviews),
        "review_count": len(reviews),
        "reviews": list(reviews),
        "warnings": [],
        "blockers": [],
        "safe_to_use": status != review.STATUS_BLOCKER,
    }


class AutomationCandidatePacketLadderTests(unittest.TestCase):
    def test_handoff_helper_review_report_becomes_packet_ladder(self) -> None:
        report = _review_report(_review("handoff-helper", repeat_count=9))
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            with mock.patch.object(ladder.review, "build_report", return_value=report):
                payload = ladder.build_report(root=root, candidate_id="handoff-helper", decision_ref=HANDOFF_DECISION_REF)

        self.assertEqual(ladder.STATUS_OK, payload["status"])
        self.assertEqual("handoff-helper", payload["candidate_id"])
        self.assertEqual(9, payload["candidate_repeat_count"])
        self.assertEqual(5, len(payload["packet_ladder"]))
        self.assertEqual(
            "AI Repetition-to-Automation Pipeline handoff-helper packet ladder first-implementation admission",
            payload["next_packet"],
        )
        self.assertNotIn("marker", payload)
        self.assertNotIn("marker_movement", payload)

    def test_tmp_review_report_can_be_loaded(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            report_path = root / "tmp" / "reviews.json"
            report_path.parent.mkdir(parents=True, exist_ok=True)
            report_path.write_text(json.dumps(_review_report(_review("handoff-helper"))), encoding="utf-8")

            payload = ladder.build_report(root=root, review_report_path="tmp/reviews.json", candidate_id="handoff-helper", decision_ref=HANDOFF_DECISION_REF)

        self.assertEqual(ladder.STATUS_OK, payload["status"])
        self.assertEqual("tmp/reviews.json", payload["review_report_ref"])
        self.assertEqual(5, len(payload["packet_ladder"]))

    def test_review_report_path_must_be_tmp_json(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            for ref in ["docs/ops/reviews.json", "tmp/reviews.txt", "../tmp/reviews.json", str(root / "tmp" / "reviews.json")]:
                payload = ladder.build_report(root=root, review_report_path=ref, candidate_id="handoff-helper", decision_ref=HANDOFF_DECISION_REF)
                self.assertEqual(ladder.STATUS_BLOCKER, payload["status"], ref)

    def test_blocked_review_report_blocks_ladder(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            with mock.patch.object(ladder.review, "build_report", return_value=_review_report(status=review.STATUS_BLOCKER)):
                payload = ladder.build_report(root=root, candidate_id="handoff-helper", decision_ref=HANDOFF_DECISION_REF)

        self.assertEqual(ladder.STATUS_BLOCKER, payload["status"])
        self.assertIn("review_report_blocked", {item["code"] for item in payload["blockers"]})

    def test_missing_candidate_is_advisory_gap(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            with mock.patch.object(ladder.review, "build_report", return_value=_review_report(_review("first-implementation"))):
                payload = ladder.build_report(root=root, candidate_id="handoff-helper", decision_ref=HANDOFF_DECISION_REF)

        self.assertEqual(ladder.STATUS_ADVISORY_GAP, payload["status"])
        self.assertEqual(0, len(payload["packet_ladder"]))
        self.assertIn("candidate_not_found", {item["code"] for item in payload["warnings"]})

    def test_non_review_ready_candidate_blocks_ladder(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            with mock.patch.object(ladder.review, "build_report", return_value=_review_report(_review("handoff-helper", status="deferred"))):
                payload = ladder.build_report(root=root, candidate_id="handoff-helper", decision_ref=HANDOFF_DECISION_REF)

        self.assertEqual(ladder.STATUS_BLOCKER, payload["status"])
        self.assertIn("candidate_not_review_ready", {item["code"] for item in payload["blockers"]})

    def test_candidate_id_must_not_be_empty(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            with mock.patch.object(ladder.review, "build_report", return_value=_review_report(_review("handoff-helper"))):
                payload = ladder.build_report(root=root, candidate_id=" ", decision_ref=HANDOFF_DECISION_REF)

        self.assertEqual(ladder.STATUS_BLOCKER, payload["status"])
        self.assertIn("missing_candidate_id", {item["code"] for item in payload["blockers"]})

    def test_decision_ref_must_be_docs_path(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            with mock.patch.object(ladder.review, "build_report", return_value=_review_report(_review("handoff-helper"))):
                for decision_ref in ["repos/app/receipt.md", "tmp/receipt.md", "runtime/receipt.md", "README.md"]:
                    payload = ladder.build_report(root=root, candidate_id="handoff-helper", decision_ref=decision_ref)
                    self.assertEqual(ladder.STATUS_BLOCKER, payload["status"], decision_ref)

    def test_main_writes_output_only_for_explicit_tmp_path(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            output_path = root / "tmp" / "ladder.json"
            with mock.patch.object(ladder, "atlas_root", return_value=root):
                with mock.patch.object(ladder.review, "build_report", return_value=_review_report(_review("handoff-helper"))):
                    stdout = io.StringIO()
                    with mock.patch("sys.stdout", stdout):
                        code = ladder.main(["--json", "--candidate-id", "handoff-helper", "--decision-ref", HANDOFF_DECISION_REF, "--output", "tmp/ladder.json"])

            self.assertEqual(0, code)
            self.assertTrue(output_path.exists())
            payload = json.loads(output_path.read_text(encoding="utf-8"))
            self.assertEqual(ladder.SCHEMA_VERSION, payload["schema_version"])

    def test_main_rejects_protected_output_path(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            with mock.patch.object(ladder, "atlas_root", return_value=root):
                stdout = io.StringIO()
                with mock.patch("sys.stdout", stdout):
                    code = ladder.main(["--json", "--candidate-id", "handoff-helper", "--decision-ref", HANDOFF_DECISION_REF, "--output", "docs/ops/ladder.json"])

        self.assertEqual(2, code)

    def test_deterministic_top_level_ordering(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            with mock.patch.object(ladder.review, "build_report", return_value=_review_report(_review("handoff-helper"))):
                payload = ladder.build_report(root=root, candidate_id="handoff-helper", decision_ref=HANDOFF_DECISION_REF)

        self.assertEqual(
            [
                "schema_version",
                "status",
                "root",
                "branch",
                "head",
                "review_report_ref",
                "source_report_schema",
                "source_report_status",
                "candidate_id",
                "decision_ref",
                "candidate_review_status",
                "candidate_repeat_count",
                "supporting_receipt_count",
                "packet_ladder",
                "next_packet",
                "boundaries",
                "warnings",
                "blockers",
                "safe_to_use",
            ],
            list(payload.keys()),
        )

    def test_strict_returns_nonzero_for_advisory_gap(self) -> None:
        self.assertEqual(1, ladder.report_exit_code(status=ladder.STATUS_ADVISORY_GAP, strict=True))


if __name__ == "__main__":
    unittest.main()
