from __future__ import annotations

import io
import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from ops.atlas import receipt_automation_candidate_extractor as extractor
from ops.atlas import receipt_automation_candidate_review as review


def _candidate(candidate_id: str, category: str, repeat_count: int) -> dict[str, object]:
    return {
        "id": candidate_id,
        "title": candidate_id.replace("-", " ").title(),
        "category": category,
        "status": "admitted",
        "supporting_receipts": [f"docs/ops/{candidate_id}-{index}.md" for index in range(repeat_count)],
        "pattern_summary": f"repeated {candidate_id}",
        "repeat_count": repeat_count,
        "recommended_next_packet": f"AI Repetition {candidate_id}",
        "boundaries": ["read_only", "no_marker_movement"],
        "rejection_reason": None,
    }


def _candidate_report(*candidates: dict[str, object], status: str = extractor.STATUS_OK) -> dict[str, object]:
    return {
        "schema_version": extractor.SCHEMA_VERSION,
        "status": status,
        "root": "C:/ATLAS",
        "branch": "main",
        "head": "abc123",
        "source_refs": ["docs/ops"],
        "candidate_count": len(candidates),
        "candidates": list(candidates),
        "rejected_candidates": [],
        "warnings": [],
        "blockers": [],
        "safe_to_use": status != extractor.STATUS_BLOCKER,
    }


class ReceiptAutomationCandidateReviewTests(unittest.TestCase):
    def test_live_extractor_report_becomes_ordered_review_cards(self) -> None:
        report = _candidate_report(
            _candidate("selector-routing", "selector_or_routing_rule", 4),
            _candidate("first-implementation", "helper", 3),
            _candidate("validation-governance", "validation_or_governance_check", 5),
        )
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            with mock.patch.object(review.extractor, "build_report", return_value=report):
                payload = review.build_report(root=root)

        self.assertEqual(review.STATUS_OK, payload["status"])
        self.assertEqual(3, payload["review_count"])
        self.assertEqual(
            ["first-implementation", "validation-governance", "selector-routing"],
            [item["candidate_id"] for item in payload["reviews"]],
        )
        self.assertNotIn("marker", payload)
        self.assertNotIn("marker_movement", payload)

    def test_tmp_candidate_report_can_be_loaded(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            report_path = root / "tmp" / "candidates.json"
            report_path.parent.mkdir(parents=True, exist_ok=True)
            report_path.write_text(json.dumps(_candidate_report(_candidate("prompt-pack", "prompt_pack", 2))), encoding="utf-8")

            payload = review.build_report(root=root, candidate_report_path="tmp/candidates.json")

        self.assertEqual(review.STATUS_OK, payload["status"])
        self.assertEqual("tmp/candidates.json", payload["candidate_report_ref"])
        self.assertEqual("prompt-pack", payload["reviews"][0]["candidate_id"])

    def test_candidate_report_path_must_be_tmp_json(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            for ref in ["docs/ops/candidates.json", "tmp/candidates.txt", "../tmp/candidates.json", str(root / "tmp" / "candidates.json")]:
                payload = review.build_report(root=root, candidate_report_path=ref)
                self.assertEqual(review.STATUS_BLOCKER, payload["status"], ref)

    def test_extractor_blocker_report_blocks_review(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            with mock.patch.object(review.extractor, "build_report", return_value=_candidate_report(status=extractor.STATUS_BLOCKER)):
                payload = review.build_report(root=root)

        self.assertEqual(review.STATUS_BLOCKER, payload["status"])
        self.assertIn("candidate_report_blocked", {item["code"] for item in payload["blockers"]})

    def test_no_candidates_is_advisory_gap(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            with mock.patch.object(review.extractor, "build_report", return_value=_candidate_report(status=extractor.STATUS_ADVISORY_GAP)):
                payload = review.build_report(root=root)

        self.assertEqual(review.STATUS_ADVISORY_GAP, payload["status"])
        self.assertEqual(0, payload["review_count"])

    def test_main_writes_output_only_for_explicit_tmp_path(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            output_path = root / "tmp" / "reviews.json"
            with mock.patch.object(review, "atlas_root", return_value=root):
                with mock.patch.object(review.extractor, "build_report", return_value=_candidate_report(_candidate("first-implementation", "helper", 2))):
                    stdout = io.StringIO()
                    with mock.patch("sys.stdout", stdout):
                        code = review.main(["--json", "--output", "tmp/reviews.json"])

            self.assertEqual(0, code)
            self.assertTrue(output_path.exists())
            payload = json.loads(output_path.read_text(encoding="utf-8"))
            self.assertEqual(review.SCHEMA_VERSION, payload["schema_version"])

    def test_main_rejects_protected_output_path(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            with mock.patch.object(review, "atlas_root", return_value=root):
                stdout = io.StringIO()
                with mock.patch("sys.stdout", stdout):
                    code = review.main(["--json", "--output", "docs/ops/reviews.json"])

        self.assertEqual(2, code)

    def test_deterministic_top_level_ordering(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            with mock.patch.object(review.extractor, "build_report", return_value=_candidate_report(_candidate("first-implementation", "helper", 2))):
                payload = review.build_report(root=root)

        self.assertEqual(
            [
                "schema_version",
                "status",
                "root",
                "branch",
                "head",
                "candidate_report_ref",
                "source_report_schema",
                "source_report_status",
                "candidate_count",
                "review_count",
                "reviews",
                "warnings",
                "blockers",
                "safe_to_use",
            ],
            list(payload.keys()),
        )

    def test_strict_returns_nonzero_for_advisory_gap(self) -> None:
        self.assertEqual(1, review.report_exit_code(status=review.STATUS_ADVISORY_GAP, strict=True))


if __name__ == "__main__":
    unittest.main()
