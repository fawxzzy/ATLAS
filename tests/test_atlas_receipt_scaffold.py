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


def _write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


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
        (root / "docs" / "atlas-book").mkdir(parents=True, exist_ok=True)
        (root / "docs" / "memory" / "initiatives").mkdir(parents=True, exist_ok=True)
        return root

    def _write_selector_sources(self, root: Path) -> None:
        (root / "docs" / "atlas-book" / "02-lanes-and-markers.md").write_text(
            "\n".join(
                [
                    "# Lanes And Markers",
                    "",
                    "## Active Front-Page Marker Table",
                    "",
                    "- AI Repetition-to-Automation Pipeline: `35%`",
                    "- AI Long-Run Batch Orchestration: `66%`",
                    "",
                    "## Supporting Open Markers",
                    "",
                    "- Fitness QA/LLEL Workflow: `96%`",
                    "",
                    "## Closed / Locked Ratchets",
                    "",
                    "- _stack Readiness: `100%`",
                    "",
                ]
            ),
            encoding="utf-8",
        )
        (root / "docs" / "atlas-book" / "01-current-state.md").write_text(
            "# Current State\n\n- the current active ATLAS-side lane is now `AI Long-Run Batch Orchestration`\n",
            encoding="utf-8",
        )
        current_receipt = root / "docs" / "ops" / (
            "AI-LONG-RUN-BATCH-ORCHESTRATION-POST-STACK-COMMAND-IMPLEMENTATION-"
            "ACTUAL-OWNER-SIDE-MUTATION-AUTHORITY-CLASS-VALUE-DOWNSTREAM-HOLD-RECHECK-"
            "2026-06-26.md"
        )
        current_receipt.parent.mkdir(parents=True, exist_ok=True)
        current_receipt.write_text(
            "\n".join(
                [
                    "# Current Packet",
                    "",
                    "- Mode: `docs-only root-bounded downstream hold recheck`",
                    "- Scope: `re-evaluate the post-authority-class-value downstream fall-through against manifest-backed no-immediate packet holds and decide whether any honest root-bounded follow-on remains`",
                    "",
                ]
            ),
            encoding="utf-8",
        )
        fallback_receipt = root / "docs" / "ops" / (
            "AI-REPETITION-TO-AUTOMATION-PIPELINE-NON-FITNESS-MARKER-KNOCKOUT-SELECTOR-"
            "ACTIVE-LANE-FOLLOW-ON-DISAMBIGUATION-2026-06-17.md"
        )
        fallback_receipt.write_text(
            "\n".join(
                [
                    "# Fallback Packet",
                    "",
                    "- Mode: `root-owned selector-surface refinement`",
                    "- Scope: `remove the current-lane self-reference from the non-Fitness marker knockout helper by separating the active packet from the first admissible downstream follow-on`",
                    "",
                ]
            ),
            encoding="utf-8",
        )

    def _write_manifest(
        self,
        root: Path,
        *,
        manifest_name: str,
        marker: str,
        percent: int,
        checkpoint_ref: str,
        next_package: str,
        mode: str,
        reason: str,
    ) -> None:
        checkpoint_path = root / checkpoint_ref
        checkpoint_path.parent.mkdir(parents=True, exist_ok=True)
        if not checkpoint_path.exists():
            checkpoint_path.write_text("# checkpoint\n", encoding="utf-8")
        supporting_ref = "docs/ops/supporting.md"
        supporting_path = root / supporting_ref
        if not supporting_path.exists():
            supporting_path.write_text("# supporting\n", encoding="utf-8")
        _write_json(
            root / "docs" / "memory" / "initiatives" / manifest_name,
            {
                "contract_version": "atlas.initiative.v1",
                "id": manifest_name.removesuffix(".json"),
                "title": manifest_name.removesuffix(".json"),
                "summary": "summary",
                "status": "active",
                "owner": "stack-root",
                "created_at": "2026-06-19T00:00:00Z",
                "updated_at": "2026-06-19T00:00:00Z",
                "related_plan_refs": [],
                "related_decision_refs": [],
                "related_hypothesis_refs": [],
                "related_session_refs": [],
                "related_attention_refs": [],
                "proposed_next_session_refs": [],
                "evidence_refs": [checkpoint_ref, supporting_ref],
                "supersedes": [],
                "superseded_by": [],
                "metadata": {
                    "artifact_kind": "continuity_manifest",
                    "lane_id": manifest_name.removesuffix(".json").removeprefix("continuity-manifest-"),
                    "scope_class": "atlas-root-governance",
                    "current_checkpoint_receipt": checkpoint_ref,
                    "checkpoint_commit": "main",
                    "checkpoint_summary": "summary",
                    "governing_receipts": [checkpoint_ref],
                    "owner_truth_surfaces": [{"path": checkpoint_ref, "role": "checkpoint"}],
                    "verification_adoption_surfaces": [{"path": supporting_ref, "role": "supporting"}],
                    "blocked_or_gated_work": [],
                    "next_package_ladder": [{"package": next_package, "mode": mode, "reason": reason}],
                    "freshness_state": "manifest-backed",
                    "freshness_checked_receipt": checkpoint_ref,
                    "freshness_checked_at": "2026-06-19T00:00:00Z",
                    "freshness_basis": "basis",
                    "marker_posture": [
                        {
                            "marker": marker,
                            "percent": percent,
                            "source": "docs/atlas-book/02-lanes-and-markers.md",
                        }
                    ],
                },
            },
        )

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
        (root / "docs" / "atlas-book" / "12-restart-and-handoff-guide.md").write_text(
            "- the current active ATLAS-side lane remains `AI Repetition-to-Automation Pipeline`\n",
            encoding="utf-8",
        )

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

    def test_main_defaults_title_when_omitted(self) -> None:
        root = self._temp_root()
        output_ref = "docs/ops/title-default-receipt.md"
        (root / "docs" / "atlas-book" / "12-restart-and-handoff-guide.md").write_text(
            "- the current active ATLAS-side lane remains `AI Repetition-to-Automation Pipeline`\n",
            encoding="utf-8",
        )

        def fake_contract_loader(**_: object) -> dict[str, object]:
            return _contract_report()

        exit_code = main(
            [
                "scaffold",
                "--root",
                str(root),
                "--lane",
                "AI Repetition-to-Automation Pipeline",
                "--output",
                output_ref,
            ],
            contract_loader=fake_contract_loader,
        )

        self.assertEqual(0, exit_code)
        payload = (root / output_ref).read_text(encoding="utf-8")
        self.assertIn(f"# AI Repetition-to-Automation Pipeline Receipt Scaffold - {date.today().isoformat()}", payload)

    def test_main_can_write_deterministic_default_output_path(self) -> None:
        root = self._temp_root()
        (root / "docs" / "atlas-book" / "12-restart-and-handoff-guide.md").write_text(
            "- the current active ATLAS-side lane remains `AI Repetition-to-Automation Pipeline`\n",
            encoding="utf-8",
        )

        def fake_contract_loader(**_: object) -> dict[str, object]:
            return _contract_report()

        exit_code = main(
            [
                "scaffold",
                "--root",
                str(root),
                "--lane",
                "AI Repetition-to-Automation Pipeline",
                "--write-default-output",
            ],
            contract_loader=fake_contract_loader,
        )

        self.assertEqual(0, exit_code)
        expected_ref = f"docs/ops/AI-REPETITION-TO-AUTOMATION-PIPELINE-RECEIPT-SCAFFOLD-{date.today().isoformat()}.md"
        payload = (root / expected_ref).read_text(encoding="utf-8")
        self.assertIn(f"# AI Repetition-to-Automation Pipeline Receipt Scaffold - {date.today().isoformat()}", payload)

    def test_main_defaults_lane_from_restart_truth_when_omitted(self) -> None:
        root = self._temp_root()
        output_ref = "docs/ops/current-lane-default-receipt.md"
        (root / "docs" / "atlas-book" / "12-restart-and-handoff-guide.md").write_text(
            "\n".join(
                [
                    "# Restart And Handoff Guide",
                    "",
                    "- the current active ATLAS-side lane remains `AI Repetition-to-Automation Pipeline`",
                ]
            )
            + "\n",
            encoding="utf-8",
        )

        def fake_contract_loader(**_: object) -> dict[str, object]:
            return _contract_report()

        exit_code = main(
            [
                "scaffold",
                "--root",
                str(root),
                "--output",
                output_ref,
            ],
            contract_loader=fake_contract_loader,
        )

        self.assertEqual(0, exit_code)
        payload = (root / output_ref).read_text(encoding="utf-8")
        self.assertIn("- Lane: `AI Repetition-to-Automation Pipeline`", payload)

    def test_main_selector_target_do_now_uses_selected_current_packet_context(self) -> None:
        root = self._temp_root()
        self._write_selector_sources(root)
        output_ref = "docs/ops/selector-do-now-receipt.md"
        captured: dict[str, object] = {}

        def fake_contract_loader(**kwargs: object) -> dict[str, object]:
            captured.update(kwargs)
            return _contract_report(
                lane=str(kwargs["lane"]),
                next_package="AI Long-Run Batch Orchestration Next Packet",
            )

        exit_code = main(
            [
                "scaffold",
                "--root",
                str(root),
                "--selector-target",
                "do-now",
                "--output",
                output_ref,
            ],
            contract_loader=fake_contract_loader,
        )

        self.assertEqual(0, exit_code)
        self.assertEqual("AI Long-Run Batch Orchestration", captured["lane"])
        self.assertEqual(
            "docs/ops/AI-LONG-RUN-BATCH-ORCHESTRATION-POST-STACK-COMMAND-IMPLEMENTATION-ACTUAL-OWNER-SIDE-MUTATION-AUTHORITY-CLASS-VALUE-DOWNSTREAM-HOLD-RECHECK-2026-06-26.md",
            captured["receipt_context"],
        )
        payload = (root / output_ref).read_text(encoding="utf-8")
        self.assertIn("- Lane: `AI Long-Run Batch Orchestration`", payload)
        self.assertIn("- selector target: `do-now`", payload)
        self.assertIn("- selector operator action: `continue_current_lane`", payload)

    def test_main_selector_target_fallback_after_current_uses_downstream_packet_context(self) -> None:
        root = self._temp_root()
        self._write_selector_sources(root)
        output_ref = "docs/ops/selector-fallback-receipt.md"
        captured: dict[str, object] = {}

        def fake_contract_loader(**kwargs: object) -> dict[str, object]:
            captured.update(kwargs)
            return _contract_report(
                lane=str(kwargs["lane"]),
                next_package="AI Repetition-to-Automation Pipeline Next Packet",
            )

        exit_code = main(
            [
                "scaffold",
                "--root",
                str(root),
                "--selector-target",
                "fallback-after-current",
                "--output",
                output_ref,
            ],
            contract_loader=fake_contract_loader,
        )

        self.assertEqual(0, exit_code)
        self.assertEqual("AI Repetition-to-Automation Pipeline", captured["lane"])
        self.assertEqual(
            "docs/ops/AI-REPETITION-TO-AUTOMATION-PIPELINE-NON-FITNESS-MARKER-KNOCKOUT-SELECTOR-ACTIVE-LANE-FOLLOW-ON-DISAMBIGUATION-2026-06-17.md",
            captured["receipt_context"],
        )
        payload = (root / output_ref).read_text(encoding="utf-8")
        self.assertIn("- Lane: `AI Repetition-to-Automation Pipeline`", payload)
        self.assertIn("- selector target: `fallback-after-current`", payload)
        self.assertIn("- selector operator action: `continue_current_lane`", payload)

    def test_main_selector_target_do_now_fails_when_selector_has_no_immediate_root_packet(self) -> None:
        root = self._temp_root()
        self._write_selector_sources(root)
        self._write_manifest(
            root,
            manifest_name="continuity-manifest-ai-long-run-batch-orchestration.json",
            marker="AI Long-Run Batch Orchestration",
            percent=66,
            checkpoint_ref=(
                "docs/ops/"
                "AI-LONG-RUN-BATCH-ORCHESTRATION-POST-STACK-COMMAND-IMPLEMENTATION-"
                "ACTUAL-OWNER-SIDE-MUTATION-AUTHORITY-CLASS-VALUE-DOWNSTREAM-HOLD-RECHECK-2026-06-26.md"
            ),
            next_package="No immediate AI Long-Run Batch Orchestration same-lane packet",
            mode="hold-flat after downstream hold recheck",
            reason="current lane is intentionally held",
        )
        self._write_manifest(
            root,
            manifest_name="continuity-manifest-ai-repetition-to-automation-pipeline.json",
            marker="AI Repetition-to-Automation Pipeline",
            percent=35,
            checkpoint_ref=(
                "docs/ops/"
                "AI-REPETITION-TO-AUTOMATION-PIPELINE-SELECTOR-LANE-EXHAUSTION-OR-FALLBACK-ROUTING-"
                "2026-06-18.md"
            ),
            next_package="No immediate AI Repetition-to-Automation Pipeline same-lane packet",
            mode="hold-flat after selector exhaustion and continuity-manifest seed",
            reason="fallback lane is intentionally held",
        )
        output_ref = "docs/ops/selector-should-fail.md"

        def failing_contract_loader(**_: object) -> dict[str, object]:
            raise AssertionError("contract loader should not run when selector truth has no immediate root packet")

        exit_code = main(
            [
                "scaffold",
                "--root",
                str(root),
                "--selector-target",
                "do-now",
                "--output",
                output_ref,
            ],
            contract_loader=failing_contract_loader,
        )

        self.assertEqual(1, exit_code)
        self.assertFalse((root / output_ref).exists())


if __name__ == "__main__":
    unittest.main()
