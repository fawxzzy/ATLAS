from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from ops.atlas.marker_knockout_selector import build_campaign, main


MARKER_DOC = """# Lanes And Markers

## Active Front-Page Marker Table

- _stack Readiness: `100%`
- Atlas-owned Repo Naming Canonicalization: `79%`
- Local Data Gateway: `66%`
- Dependency Untangling: `72%`
- Truth Map & ATLAS Book: `87%`
- Inventory & Truth Map: `76%`
- Knowledge Capture & Transfer: `83%`
- Durable Context Externalization: `78%`
- Discord OS Infrastructure Separation: `95%`
- Discord OS Feedback Workflow Canonicalization: `72%`

## Supporting Open Markers

- Verta Absorption: `99%`
- ATLAS Core Phase: `95%`
- Lifeline Readiness: `97%`
- Playbook Maturity: `92%`
- Cortex Readiness: `41%`
- Fitness QA/LLEL Workflow: `96%`
- Fitness Branch Cleanup / Main-Only Governance: `96%`
- Fitness Recovery Preservation: `80%`
- Tmp Dependency Elimination: `90%`
- Duplicate Surface Decommission: `98%`
- Brand Asset Canonicalization: `90%`
- Preview Cache & Surface Consistency: `78%`
- Vercel Hobby Cost Governance: `35%`
- Operator Secret Path Hygiene: `64%`
- Manual Deploy Exception Burn-Down: `84%`
- Unified Workflow Convergence: `73%`
- Vision & Future Alignment: `25%`
- Core Pattern Convergence: `43%`
- Discord Workflow, Publication & Docs Reliability: `32%`
- Playbook Everywhere + Cortex Interface: `22%`
- AI Repetition-to-Automation Pipeline: `32%`
- AI Long-Run Batch Orchestration: `20%`
- Feedback Loop Readiness: `42%`
- Sandbox Simulation Readiness: `0%`
- Post-Convergence Lane Split Readiness: `61%`

## Closed / Locked Ratchets

- Archive Normalization: `100%`
"""

CURRENT_STATE_DOC = """# Current State

- the next durable ATLAS-side active lane is now `AI Long-Run Batch Orchestration`
"""


def _write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


class AtlasMarkerKnockoutSelectorTests(unittest.TestCase):
    def _temp_root(self) -> Path:
        temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(temp_dir.cleanup)
        root = Path(temp_dir.name)
        (root / "docs" / "atlas-book").mkdir(parents=True, exist_ok=True)
        (root / "docs" / "memory" / "initiatives").mkdir(parents=True, exist_ok=True)
        return root

    def _write_packet_receipts(self, root: Path) -> None:
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

        sandbox_receipt = root / "docs" / "ops" / (
            "SANDBOX-SIMULATION-READINESS-POST-LOCAL-ONLY-FIRST-VALIDATOR-UNATTENDED-"
            "RUNTIME-PROOF-ADMISSION-BOUNDARY-NEXT-SLICE-SELECTION-2026-06-27.md"
        )
        sandbox_receipt.write_text(
            "\n".join(
                [
                    "# Sandbox Packet",
                    "",
                    "- Mode: `docs-only root-bounded next-slice selection`",
                    "- Scope: `choose the strongest bounded Sandbox follow-on now that the local-only first validator deploy-surface mutation admission boundary is directly frozen on canonical main`",
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
        supporting_path.parent.mkdir(parents=True, exist_ok=True)
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
                    "next_package_ladder": [
                        {"package": next_package, "mode": mode, "reason": reason}
                    ],
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

    def test_build_campaign_selects_active_lane_from_durable_restart_truth(self) -> None:
        root = self._temp_root()
        (root / "docs" / "atlas-book" / "02-lanes-and-markers.md").write_text(MARKER_DOC, encoding="utf-8")
        (root / "docs" / "atlas-book" / "01-current-state.md").write_text(CURRENT_STATE_DOC, encoding="utf-8")
        self._write_packet_receipts(root)

        payload = build_campaign(root=root)

        self.assertEqual("AI Long-Run Batch Orchestration", payload["selected_marker"])
        self.assertEqual(20, payload["selected_percentage"])
        self.assertEqual("continue_current_lane", payload["operator_action"])
        self.assertEqual(
            "AI Long-Run Batch Orchestration post-stack-command-implementation-actual-owner-side-mutation-authority-class-value downstream hold recheck",
            payload["selected_current_packet"],
        )
        self.assertEqual(
            "docs/ops/AI-LONG-RUN-BATCH-ORCHESTRATION-POST-STACK-COMMAND-IMPLEMENTATION-ACTUAL-OWNER-SIDE-MUTATION-AUTHORITY-CLASS-VALUE-DOWNSTREAM-HOLD-RECHECK-2026-06-26.md",
            payload["selected_current_packet_basis_ref"],
        )
        self.assertEqual(
            "docs-only root-bounded downstream hold recheck",
            payload["selected_current_packet_mode"],
        )
        self.assertEqual(
            "re-evaluate the post-authority-class-value downstream fall-through against manifest-backed no-immediate packet holds and decide whether any honest root-bounded follow-on remains",
            payload["selected_current_packet_scope"],
        )
        self.assertEqual(
            "AI Repetition-to-Automation Pipeline",
            payload["next_after_current_marker"],
        )
        self.assertEqual(
            "AI Repetition-to-Automation Pipeline non-Fitness marker knockout selector surface",
            payload["next_after_current_packet"],
        )
        self.assertEqual(
            "docs/ops/AI-REPETITION-TO-AUTOMATION-PIPELINE-NON-FITNESS-MARKER-KNOCKOUT-SELECTOR-ACTIVE-LANE-FOLLOW-ON-DISAMBIGUATION-2026-06-17.md",
            payload["next_after_current_packet_basis_ref"],
        )
        self.assertEqual("root-owned selector-surface refinement", payload["next_after_current_packet_mode"])
        self.assertEqual(
            "remove the current-lane self-reference from the non-Fitness marker knockout helper by separating the active packet from the first admissible downstream follow-on",
            payload["next_after_current_packet_scope"],
        )

    def test_build_campaign_classifies_fitness_and_secret_holds(self) -> None:
        root = self._temp_root()
        (root / "docs" / "atlas-book" / "02-lanes-and-markers.md").write_text(MARKER_DOC, encoding="utf-8")
        (root / "docs" / "atlas-book" / "01-current-state.md").write_text(CURRENT_STATE_DOC, encoding="utf-8")
        self._write_packet_receipts(root)

        payload = build_campaign(root=root)
        records = {record["marker"]: record for record in payload["open_markers"]}

        self.assertEqual("protected/Fitness hold", records["Fitness QA/LLEL Workflow"]["category"])
        self.assertEqual("secret/.env hold", records["Operator Secret Path Hygiene"]["category"])
        self.assertEqual("admissible after current lane", records["Vercel Hobby Cost Governance"]["category"])
        self.assertEqual("admissible after current lane", records["AI Repetition-to-Automation Pipeline"]["category"])
        self.assertEqual("admissible now", records["AI Long-Run Batch Orchestration"]["category"])
        self.assertEqual("already closed / locked", records["_stack Readiness"]["category"])

    def test_build_campaign_skips_manifest_held_follow_on_marker(self) -> None:
        root = self._temp_root()
        (root / "docs" / "atlas-book" / "02-lanes-and-markers.md").write_text(MARKER_DOC, encoding="utf-8")
        (root / "docs" / "atlas-book" / "01-current-state.md").write_text(CURRENT_STATE_DOC, encoding="utf-8")
        self._write_packet_receipts(root)
        self._write_manifest(
            root,
            manifest_name="continuity-manifest-ai-repetition-to-automation-pipeline.json",
            marker="AI Repetition-to-Automation Pipeline",
            percent=32,
            checkpoint_ref=(
                "docs/ops/"
                "AI-REPETITION-TO-AUTOMATION-PIPELINE-SELECTOR-LANE-EXHAUSTION-OR-FALLBACK-ROUTING-"
                "2026-06-18.md"
            ),
            next_package="No immediate AI Repetition-to-Automation Pipeline same-lane packet",
            mode="hold-flat after selector exhaustion",
            reason="selector family is currently held",
        )

        payload = build_campaign(root=root)

        self.assertEqual("Durable Context Externalization", payload["next_after_current_marker"])
        self.assertNotEqual("AI Repetition-to-Automation Pipeline", payload["next_after_current_marker"])

    def test_build_campaign_holds_active_lane_when_its_manifest_has_no_immediate_packet(self) -> None:
        root = self._temp_root()
        (root / "docs" / "atlas-book" / "02-lanes-and-markers.md").write_text(MARKER_DOC, encoding="utf-8")
        (root / "docs" / "atlas-book" / "01-current-state.md").write_text(CURRENT_STATE_DOC, encoding="utf-8")
        self._write_packet_receipts(root)
        self._write_manifest(
            root,
            manifest_name="continuity-manifest-ai-long-run-batch-orchestration.json",
            marker="AI Long-Run Batch Orchestration",
            percent=20,
            checkpoint_ref=(
                "docs/ops/"
                "AI-LONG-RUN-BATCH-ORCHESTRATION-POST-STACK-COMMAND-IMPLEMENTATION-"
                "ACTUAL-OWNER-SIDE-MUTATION-AUTHORITY-CLASS-VALUE-DOWNSTREAM-HOLD-RECHECK-2026-06-26.md"
            ),
            next_package="No immediate AI Long-Run Batch Orchestration same-lane packet",
            mode="hold-flat after downstream follow-on recheck",
            reason="current lane is intentionally held",
        )

        payload = build_campaign(root=root)

        self.assertEqual("hold_current_lane", payload["operator_action"])

    def test_build_campaign_promotes_sandbox_after_deploy_surface_mutation_admission_boundary_contract(self) -> None:
        root = self._temp_root()
        marker_doc = MARKER_DOC.replace(
            "- Sandbox Simulation Readiness: `0%`",
            "- Sandbox Simulation Readiness: `99%`",
        )
        (root / "docs" / "atlas-book" / "02-lanes-and-markers.md").write_text(marker_doc, encoding="utf-8")
        (root / "docs" / "atlas-book" / "01-current-state.md").write_text(CURRENT_STATE_DOC, encoding="utf-8")
        self._write_packet_receipts(root)
        self._write_manifest(
            root,
            manifest_name="continuity-manifest-ai-repetition-to-automation-pipeline.json",
            marker="AI Repetition-to-Automation Pipeline",
            percent=32,
            checkpoint_ref=(
                "docs/ops/"
                "AI-REPETITION-TO-AUTOMATION-PIPELINE-SELECTOR-LANE-EXHAUSTION-OR-FALLBACK-ROUTING-"
                "2026-06-18.md"
            ),
            next_package="No immediate AI Repetition-to-Automation Pipeline same-lane packet",
            mode="hold-flat after selector exhaustion",
            reason="selector family is currently held",
        )

        payload = build_campaign(root=root)
        records = {record["marker"]: record for record in payload["open_markers"]}

        self.assertEqual(
            "admissible after current lane",
            records["Sandbox Simulation Readiness"]["category"],
        )
        self.assertIn(
            "deploy-surface mutation admission boundary contract",
            records["Sandbox Simulation Readiness"]["rationale"],
        )
        self.assertEqual(
            "Sandbox Simulation Readiness local-only first validator public release truth admission boundary contract freeze",
            payload["next_after_current_packet"],
        )
        self.assertEqual(
            "docs/ops/SANDBOX-SIMULATION-READINESS-POST-LOCAL-ONLY-FIRST-VALIDATOR-DEPLOY-SURFACE-MUTATION-ADMISSION-BOUNDARY-NEXT-SLICE-SELECTION-2026-06-27.md",
            payload["next_after_current_packet_basis_ref"],
        )
        self.assertEqual(
            "root-owned docs-only validator-public-release-truth-admission-boundary contract freeze",
            payload["next_after_current_packet_mode"],
        )
        self.assertIn(
            "whether any public release truth may exist above that frozen deploy-mutation family at all",
            payload["next_after_current_packet_scope"],
        )

    def test_build_campaign_normalizes_inline_code_marker_names(self) -> None:
        root = self._temp_root()
        marker_doc = MARKER_DOC.replace("- _stack Readiness: `100%`", "- `_stack` Readiness: `100%`")
        (root / "docs" / "atlas-book" / "02-lanes-and-markers.md").write_text(marker_doc, encoding="utf-8")
        (root / "docs" / "atlas-book" / "01-current-state.md").write_text(CURRENT_STATE_DOC, encoding="utf-8")
        self._write_packet_receipts(root)

        payload = build_campaign(root=root)
        records = {record["marker"]: record for record in payload["open_markers"]}

        self.assertIn("_stack Readiness", records)

    def test_main_can_write_json_output(self) -> None:
        root = self._temp_root()
        (root / "docs" / "atlas-book" / "02-lanes-and-markers.md").write_text(MARKER_DOC, encoding="utf-8")
        (root / "docs" / "atlas-book" / "01-current-state.md").write_text(CURRENT_STATE_DOC, encoding="utf-8")
        self._write_packet_receipts(root)
        output_ref = "docs/ops/selector-output.json"

        exit_code = main(["--root", str(root), "--format", "json", "--output", output_ref])

        self.assertEqual(0, exit_code)
        payload = json.loads((root / output_ref).read_text(encoding="utf-8"))
        self.assertEqual("root-non-fitness-marker-knockout", payload["campaign_id"])
        self.assertEqual("continue_current_lane", payload["operator_action"])

    def test_main_markdown_separates_current_lane_from_next_follow_on(self) -> None:
        root = self._temp_root()
        (root / "docs" / "atlas-book" / "02-lanes-and-markers.md").write_text(MARKER_DOC, encoding="utf-8")
        (root / "docs" / "atlas-book" / "01-current-state.md").write_text(CURRENT_STATE_DOC, encoding="utf-8")
        self._write_packet_receipts(root)
        output_ref = "docs/ops/selector-output.md"

        exit_code = main(["--root", str(root), "--format", "markdown", "--output", output_ref])

        self.assertEqual(0, exit_code)
        markdown = (root / output_ref).read_text(encoding="utf-8")
        self.assertIn("## Operator Action", markdown)
        self.assertIn("action: `continue_current_lane`", markdown)
        self.assertIn(
            "current packet basis receipt: `docs/ops/AI-LONG-RUN-BATCH-ORCHESTRATION-POST-STACK-COMMAND-IMPLEMENTATION-ACTUAL-OWNER-SIDE-MUTATION-AUTHORITY-CLASS-VALUE-DOWNSTREAM-HOLD-RECHECK-2026-06-26.md`",
            markdown,
        )
        self.assertIn(
            "current packet mode: `docs-only root-bounded downstream hold recheck`",
            markdown,
        )
        self.assertIn(
            "current packet scope: `re-evaluate the post-authority-class-value downstream fall-through against manifest-backed no-immediate packet holds and decide whether any honest root-bounded follow-on remains`",
            markdown,
        )
        self.assertIn("## Current Active Marker", markdown)
        self.assertIn(
            "current packet: `AI Long-Run Batch Orchestration post-stack-command-implementation-actual-owner-side-mutation-authority-class-value downstream hold recheck`",
            markdown,
        )
        self.assertIn("## First Admissible After Current Lane", markdown)
        self.assertIn(
            "next packet after current lane: `AI Repetition-to-Automation Pipeline non-Fitness marker knockout selector surface`",
            markdown,
        )
        self.assertIn(
            "next packet basis receipt: `docs/ops/AI-REPETITION-TO-AUTOMATION-PIPELINE-NON-FITNESS-MARKER-KNOCKOUT-SELECTOR-ACTIVE-LANE-FOLLOW-ON-DISAMBIGUATION-2026-06-17.md`",
            markdown,
        )
        self.assertIn("next packet mode: `root-owned selector-surface refinement`", markdown)
        self.assertIn(
            "next packet scope: `remove the current-lane self-reference from the non-Fitness marker knockout helper by separating the active packet from the first admissible downstream follow-on`",
            markdown,
        )


if __name__ == "__main__":
    unittest.main()
