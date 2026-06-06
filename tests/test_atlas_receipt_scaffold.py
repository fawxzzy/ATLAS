from __future__ import annotations

import json
import tempfile
import unittest
from datetime import date
from pathlib import Path

from ops.atlas.receipt_scaffold import (
    ReceiptScaffoldInput,
    build_input,
    main,
    render_receipt_scaffold,
)


def _contract_report(**overrides: object) -> dict[str, object]:
    payload: dict[str, object] = {
        "command": "stack receipt package",
        "lane": "AI Repetition-to-Automation Pipeline",
        "package_mode": "draft-skeleton-plus-context",
        "draft_status": "draft-only",
        "authoritative_refs": [
            "docs/atlas-book/01-current-state.md",
            "docs/atlas-book/02-lanes-and-markers.md",
        ],
        "context_status": "agreed",
        "routing_note": "package draft-only skeleton plus exact agreed context and continue",
        "marker_percentage": "31%",
        "supporting_posture": "immediate control-plane family",
        "next_package": "AI Repetition-to-Automation Pipeline Receipt Skeleton Drafts Operator-Usable Scaffold Surface Pass 2",
    }
    payload.update(overrides)
    return payload


class AtlasReceiptScaffoldTests(unittest.TestCase):
    def _temp_root(self) -> Path:
        temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(temp_dir.cleanup)
        root = Path(temp_dir.name)
        (root / "docs" / "ops").mkdir(parents=True, exist_ok=True)
        return root

    def test_normal_no_marker_movement_receipt_renders_from_agreed_contract(self) -> None:
        scaffold_input = ReceiptScaffoldInput(
            title="AI Repetition-to-Automation Pipeline Receipt Skeleton Drafts Operator-Usable Scaffold Surface Pass 1",
            lane="AI Repetition-to-Automation Pipeline",
            date="2026-06-06",
            status="normal",
            objective="REPLACE_ME_OBJECTIVE",
            scope="REPLACE_ME_SCOPE",
            receipt_context=None,
            blocker_code=None,
            blocker_summary=None,
            marker_decision="none",
            verification_lines=("REPLACE_ME_VERIFICATION",),
            protected_surfaces=("repos/fawxzzy-fitness", "archive/"),
            output_ref=None,
        )

        body = render_receipt_scaffold(scaffold_input, _contract_report())

        self.assertIn("# AI Repetition-to-Automation Pipeline Receipt Skeleton Drafts Operator-Usable Scaffold Surface Pass 1", body)
        self.assertIn("- current marker posture: `31%`", body)
        self.assertIn("## Marker Decision", body)
        self.assertIn("- `none`", body)
        self.assertIn("## Exact Next Package", body)
        self.assertIn("Operator-Usable Scaffold Surface Pass 2", body)
        self.assertNotIn("REPLACE_ME_OBJECTIVE", body)
        self.assertNotIn("REPLACE_ME_SCOPE", body)
        self.assertNotIn("REPLACE_ME_VERIFICATION", body)
        self.assertIn("Preserve one bounded draft-only operator-usable receipt scaffold", body)
        self.assertIn("preserve current marker posture `31%`", body)
        self.assertIn(r"python .\ops\validation\validate_stack.py --ratchet", body)

    def test_blocked_lane_receipt_requires_and_renders_explicit_blocker_fields(self) -> None:
        args = build_input(
            type(
                "Args",
                (),
                {
                    "title": "Blocked Receipt",
                    "lane": "AI Repetition-to-Automation Pipeline",
                    "date": "2026-06-06",
                    "status": "blocked",
                    "objective": None,
                    "scope": None,
                    "receipt_context": None,
                    "blocker_code": "blocked_test",
                    "blocker_summary": "Blocked on one explicit test seam.",
                    "marker_decision": "none",
                    "verification": None,
                    "protected_surface": None,
                    "output": None,
                },
            )()
        )

        body = render_receipt_scaffold(args, _contract_report())

        self.assertIn("## Blocker", body)
        self.assertIn("- blocker code: `blocked_test`", body)
        self.assertIn("- blocker summary: Blocked on one explicit test seam.", body)
        self.assertIn("stop after preserving the blocker receipt", body)
        self.assertNotIn("REPLACE_ME_OBJECTIVE", body)
        self.assertNotIn("REPLACE_ME_SCOPE", body)
        self.assertNotIn("REPLACE_ME_VERIFICATION", body)

    def test_receipt_lists_protected_surfaces_not_touched(self) -> None:
        scaffold_input = ReceiptScaffoldInput(
            title="Protected Surface Receipt",
            lane="AI Repetition-to-Automation Pipeline",
            date="2026-06-06",
            status="normal",
            objective="REPLACE_ME_OBJECTIVE",
            scope="REPLACE_ME_SCOPE",
            receipt_context=None,
            blocker_code=None,
            blocker_summary=None,
            marker_decision="none",
            verification_lines=("REPLACE_ME_VERIFICATION",),
            protected_surfaces=("repos/fawxzzy-fitness", "archive/", ".vercel", ".env"),
            output_ref=None,
        )

        body = render_receipt_scaffold(scaffold_input, _contract_report())

        self.assertIn("## Protected Surfaces Not Touched", body)
        self.assertIn("- `repos/fawxzzy-fitness`", body)
        self.assertIn("- `archive/`", body)
        self.assertIn("- `.vercel`", body)
        self.assertIn("- `.env`", body)

    def test_main_accepts_bounded_receipt_basis_fallback_and_renders_placeholder_next_package(self) -> None:
        root = self._temp_root()
        output_ref = "docs/ops/fallback-receipt.md"

        def fallback_contract_loader(**_: object) -> dict[str, object]:
            return {
                "command": "stack receipt package",
                "failure_code": "receipt-basis-unavailable",
                "failure_scope": "restart-context",
                "lane": "AI Repetition-to-Automation Pipeline",
                "draft_status": "draft-only",
                "authoritative_refs": [
                    "docs/atlas-book/01-current-state.md",
                    "docs/atlas-book/02-lanes-and-markers.md",
                ],
                "placeholder_fields": ["next_package"],
                "routing_note": "package draft-only skeleton with placeholders and continue",
                "contradiction_note": {
                    "contradiction_scope": "restart-surfaces",
                    "conflicting_refs": [
                        "docs/atlas-book/11-system-map-graph.md",
                        "docs/atlas-book/12-restart-and-handoff-guide.md",
                    ],
                    "summary_consequence": "no-next-package",
                },
            }

        exit_code = main(
            [
                "scaffold",
                "--root",
                str(root),
                "--title",
                "Fallback Receipt",
                "--lane",
                "AI Repetition-to-Automation Pipeline",
                "--date",
                "2026-06-06",
                "--output",
                output_ref,
            ],
            contract_loader=fallback_contract_loader,
        )

        self.assertEqual(0, exit_code)
        body = (root / output_ref).read_text(encoding="utf-8")
        self.assertIn("- fallback scope: `restart-context`", body)
        self.assertIn("- contradiction scope: `restart-surfaces`", body)
        self.assertIn(f"- `{ 'REPLACE_ME_NEXT_PACKAGE' }`", body)

    def test_invalid_input_fails_safely_without_writing_output(self) -> None:
        root = self._temp_root()
        output_ref = "docs/ops/blocked-receipt.md"

        def failing_contract_loader(**_: object) -> dict[str, object]:
            raise AssertionError("contract loader should not run for invalid input")

        exit_code = main(
            [
                "scaffold",
                "--root",
                str(root),
                "--title",
                "Invalid Receipt",
                "--lane",
                "AI Repetition-to-Automation Pipeline",
                "--date",
                "2026-06-06",
                "--status",
                "blocked",
                "--output",
                output_ref,
            ],
            contract_loader=failing_contract_loader,
        )

        self.assertEqual(1, exit_code)
        self.assertFalse((root / output_ref).exists())

    def test_main_writes_operator_usable_receipt_scaffold(self) -> None:
        root = self._temp_root()
        output_ref = "docs/ops/generated-receipt.md"

        def fake_contract_loader(**_: object) -> dict[str, object]:
            return _contract_report()

        exit_code = main(
            [
                "scaffold",
                "--root",
                str(root),
                "--title",
                "Generated Receipt",
                "--lane",
                "AI Repetition-to-Automation Pipeline",
                "--date",
                "2026-06-06",
                "--output",
                output_ref,
                "--verification",
                "python .\\ops\\validation\\validate_stack.py --ratchet",
            ],
            contract_loader=fake_contract_loader,
        )

        self.assertEqual(0, exit_code)
        payload = (root / output_ref).read_text(encoding="utf-8")
        self.assertIn("# Generated Receipt", payload)
        self.assertIn("python .\\ops\\validation\\validate_stack.py --ratchet", payload)
        self.assertNotIn("REPLACE_ME_OBJECTIVE", payload)
        self.assertNotIn("REPLACE_ME_SCOPE", payload)
        self.assertNotIn("REPLACE_ME_VERIFICATION", payload)

    def test_main_defaults_date_when_omitted(self) -> None:
        root = self._temp_root()
        output_ref = "docs/ops/date-default-receipt.md"

        def fake_contract_loader(**_: object) -> dict[str, object]:
            return _contract_report()

        exit_code = main(
            [
                "scaffold",
                "--root",
                str(root),
                "--title",
                "Date Default Receipt",
                "--lane",
                "AI Repetition-to-Automation Pipeline",
                "--output",
                output_ref,
            ],
            contract_loader=fake_contract_loader,
        )

        self.assertEqual(0, exit_code)
        payload = (root / output_ref).read_text(encoding="utf-8")
        self.assertIn(f"- Date: `{date.today().isoformat()}`", payload)


if __name__ == "__main__":
    unittest.main()
