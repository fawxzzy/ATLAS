from __future__ import annotations

import hashlib
import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from ops.atlas import marker_knockout_selector as selector
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
- Vercel Platform Observability Governance: `0%`
- Cortex Dual-Mode Replacement Readiness: `0%`
- Cortex Simulation Substrate Readiness: `0%`
- Owner-Lane Agent Service Bus & DiscordOS Ops Readiness: `0%`
- GitHub Control-Plane Integration: `100%`
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
            "SANDBOX-SIMULATION-READINESS-POST-LOCAL-ONLY-FIRST-VALIDATOR-BROADER-"
            "RUNTIME-ASSERTIONS-ADMISSION-BOUNDARY-HOLD-OR-TOP-LEVEL-LANE-"
            "RESELECTION-2026-06-27.md"
        )
        sandbox_receipt.write_text(
            "\n".join(
                [
                    "# Sandbox Packet",
                    "",
                    "- Mode: `docs-only root-bounded hold or top-level lane reselection`",
                    "- Scope: `decide whether Sandbox stays held or returns to broader campaign routing now that the local-only first validator broader-runtime-assertions admission boundary is directly frozen on canonical main`",
                    "",
                ]
            ),
            encoding="utf-8",
        )

        ai_work_receipt = root / "docs" / "ops" / (
            "AI-WORK-SESSION-STABILITY-AUTO-SYNC-LOOP-READ-ONLY-PREFLIGHT-AGGREGATOR-"
            "PROMPT-PACK-AND-WORKER-HANDOFF-CONTRACT-2026-06-29.md"
        )
        ai_work_receipt.write_text(
            "\n".join(
                [
                    "# AI Work Packet",
                    "",
                    "- Mode: `docs-only implementation-readiness closeout and worker-routing`",
                    "- Scope: `decide whether the read-only ai_work_session_preflight worker can be routed with its current guards and proof contract, or whether any docs-only ambiguity still blocks worker admission`",
                    "",
                ]
            ),
            encoding="utf-8",
        )

        ai_work_readiness_receipt = root / "docs" / "ops" / (
            "AI-WORK-SESSION-STABILITY-AUTO-SYNC-LOOP-READ-ONLY-PREFLIGHT-AGGREGATOR-"
            "IMPLEMENTATION-READINESS-CLOSEOUT-AND-WORKER-ROUTING-2026-06-29.md"
        )
        ai_work_readiness_receipt.write_text(
            "\n".join(
                [
                    "# AI Work Readiness Packet",
                    "",
                    "- Mode: `docs-only root-bounded implementation-readiness closeout and worker-routing`",
                    "- Scope: `decide whether the read-only ai_work_session_preflight worker can now leave root docs-only planning, route exactly one bounded worker packet if so, and preserve the frozen read-only contract without implementing code in this receipt`",
                    "",
                ]
            ),
            encoding="utf-8",
        )

        dual_mode_reconciliation_receipt = root / "docs" / "ops" / (
            "CORTEX-DUAL-MODE-REPLACEMENT-READINESS-CHATGPT-CODEX-ROLE-INVENTORY-FIRST-"
            "IMPLEMENTATION-WORKER-CLUSTER-RECONCILIATION-2026-07-09.md"
        )
        dual_mode_reconciliation_receipt.write_text(
            "\n".join(
                [
                    "# Dual-Mode Role Inventory Reconciliation",
                    "",
                    "- Mode: `docs-only root-bounded ChatGPT/Codex role-inventory marker-surface ratchet decision`",
                    "- Scope: `decide whether the implementation-backed ChatGPT/Codex role inventory justifies broader marker adoption or should remain held at 0 percent without widening beyond admitted root doctrine`",
                    "",
                ]
            ),
            encoding="utf-8",
        )

        dual_mode_ratchet_receipt = root / "docs" / "ops" / (
            "CORTEX-DUAL-MODE-REPLACEMENT-READINESS-CHATGPT-CODEX-ROLE-INVENTORY-MARKER-"
            "SURFACE-RATCHET-DECISION-2026-07-09.md"
        )
        dual_mode_ratchet_receipt.write_text(
            "\n".join(
                [
                    "# Dual-Mode Marker Ratchet Decision",
                    "",
                    "- Mode: `docs-only root-bounded synthesis-to-execution bridge-schema contract freeze`",
                    "- Scope: `freeze the next dual-mode bridge boundary after the operating model and implementation-backed role inventory thresholds, without widening beyond admitted root doctrine, authority denials, and shared-substrate truth`",
                    "",
                ]
            ),
            encoding="utf-8",
        )

        primary_operator_contract = root / "docs" / "ops" / (
            "CORTEX-DUAL-MODE-REPLACEMENT-READINESS-PRIMARY-OPERATOR-ACCEPTANCE-AND-"
            "RECEIPT-CONTRACT-FREEZE-2026-07-14.md"
        )
        primary_operator_contract.write_text(
            "\n".join(
                [
                    "# Primary Operator Contract",
                    "",
                    "- Mode: `root-owned deterministic dry-run primary-operator implementation`",
                    "- Scope: `implement one Cortex helper/test pair that accepts or rejects atlas.cortex.execution_plan.v1, emits deterministic acceptance and receipt identities, preserves _stack execution ownership, requires no external adapter, and performs no runtime or platform mutation`",
                    "",
                ]
            ),
            encoding="utf-8",
        )

        primary_operator_implementation = root / "docs" / "ops" / (
            "CORTEX-DUAL-MODE-REPLACEMENT-READINESS-PRIMARY-OPERATOR-FIRST-"
            "IMPLEMENTATION-RECONCILIATION-2026-07-14.md"
        )
        primary_operator_implementation.write_text(
            "\n".join(
                [
                    "# Primary Operator First Implementation Reconciliation",
                    "",
                    "- Mode: `docs-only root-bounded replay-parity contract freeze`",
                    "- Scope: `freeze deterministic replay comparison between primary-operator acceptance/receipts and optional adapter projections, preserving _stack execution ownership and prohibiting runtime dispatch, marker movement, or external mutation`",
                    "",
                ]
            ),
            encoding="utf-8",
        )

        primary_operator_parity_contract = root / "docs" / "ops" / (
            "CORTEX-DUAL-MODE-REPLACEMENT-READINESS-PRIMARY-OPERATOR-REPLAY-PARITY-"
            "CONTRACT-FREEZE-2026-07-14.md"
        )
        primary_operator_parity_contract.write_text(
            "\n".join(
                [
                    "# Primary Operator Replay Parity Contract",
                    "",
                    "- Mode: `root-owned deterministic offline replay-parity implementation`",
                    "- Scope: `implement one Cortex helper/test pair for internal no-adapter replay and optional adapter projection comparison, preserving _stack execution ownership and prohibiting model calls, runtime dispatch, marker movement, or external mutation`",
                    "",
                ]
            ),
            encoding="utf-8",
        )

        primary_operator_parity_implementation = root / "docs" / "ops" / (
            "CORTEX-DUAL-MODE-REPLACEMENT-READINESS-PRIMARY-OPERATOR-REPLAY-PARITY-FIRST-"
            "IMPLEMENTATION-RECONCILIATION-2026-07-14.md"
        )
        primary_operator_parity_implementation.write_text(
            "\n".join(
                [
                    "# Primary Operator Replay Parity First Implementation",
                    "",
                    "- Mode: `docs-only cross-plane dispatch and durable-result contract freeze`",
                    "- Scope: `freeze one bounded Cortex-to-_stack dispatch contract with acceptance, job, run, and result correlation; preserve _stack execution ownership and prohibit self-granted push, deploy, Discord, database, or production authority`",
                    "",
                ]
            ),
            encoding="utf-8",
        )

        primary_operator_stack_dispatch_contract = root / "docs" / "ops" / (
            "CORTEX-DUAL-MODE-REPLACEMENT-READINESS-STACK-DISPATCH-AND-DURABLE-RESULT-"
            "CONTRACT-FREEZE-2026-07-14.md"
        )
        primary_operator_stack_dispatch_contract.write_text(
            "\n".join(
                [
                    "# Primary Operator Stack Dispatch Contract",
                    "",
                    "- Mode: `serialized root implementation then bounded live _stack no-change canary`",
                    "- Scope: `implement deterministic request, prompt, and result-correlation behavior around the existing codex:stack:task runner, then prove one success_no_changes canary without commit, push, deploy, Discord, board, database, secret, or marker mutation`",
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
            "No immediate AI Repetition-to-Automation Pipeline same-lane packet",
            payload["next_after_current_packet"],
        )
        self.assertEqual(
            "docs/ops/AI-REPETITION-TO-AUTOMATION-PIPELINE-HELD-LANE-EVIDENCE-DELTA-SELECTOR-INTEGRATION-FIRST-IMPLEMENTATION-WORKER-CLUSTER-RECONCILIATION-2026-07-14.md",
            payload["next_after_current_packet_basis_ref"],
        )
        self.assertEqual(
            "held after exact-checkpoint-bound selector integration reconciliation",
            payload["next_after_current_packet_mode"],
        )
        self.assertEqual(
            "preserve the independently ratified fail-closed evidence-delta routing seam; future widening requires a distinct registered held-lane case or materially new automation family rather than continuation by adjacency",
            payload["next_after_current_packet_scope"],
        )

    def _write_evidence_delta_contract(
        self,
        root: Path,
        *,
        marker: str,
        held_ref: str,
        evidence_present: bool = True,
        contract_name: str = "test-held-lane-evidence-delta.v1.json",
    ) -> str:
        evidence_ref = "docs/ops/new-evidence.md"
        held_path = root / held_ref
        if not held_path.exists():
            held_path.parent.mkdir(parents=True, exist_ok=True)
            held_path.write_text("held checkpoint\n", encoding="utf-8")
        held_digest = "sha256:" + hashlib.sha256(held_path.read_bytes()).hexdigest()
        if evidence_present:
            (root / evidence_ref).write_text("new implementation proof\n", encoding="utf-8")
        contract_ref = f"docs/registry/{contract_name}"
        _write_json(
            root / contract_ref,
            {
                "contract_version": "atlas.held-lane-evidence-delta.v1",
                "case_id": "selector-integration-test",
                "marker": marker,
                "blocker_class": "implementation_or_restart_truth_change",
                "held_checkpoint": {
                    "class": "held_checkpoint",
                    "ref": held_ref,
                    "assertions": [
                        {
                            "id": "held-hash",
                            "type": "sha256",
                            "equals": held_digest,
                        }
                    ],
                },
                "required_evidence_classes": ["implementation"],
                "evidence": [
                    {
                        "class": "implementation",
                        "ref": evidence_ref,
                        "assertions": [
                            {
                                "id": "implemented",
                                "type": "literal",
                                "value": "new implementation proof",
                            }
                        ],
                    }
                ],
                "authority": {
                    "marker_movement": False,
                    "selector_mutation": False,
                    "dispatch": False,
                    "owner_repo_mutation": False,
                    "deploy": False,
                    "discord": False,
                    "secret_access": False,
                    "final_receipt": False,
                },
                "expected_decision": "reopen_eligible",
            },
        )
        return contract_ref

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
        self.assertEqual("insufficient evidence / needs selector only", records["Vercel Platform Observability Governance"]["category"])
        self.assertEqual("admissible after current lane", records["Cortex Dual-Mode Replacement Readiness"]["category"])
        self.assertEqual("admissible after current lane", records["Cortex Simulation Substrate Readiness"]["category"])
        self.assertEqual("admissible after current lane", records["Owner-Lane Agent Service Bus & DiscordOS Ops Readiness"]["category"])
        self.assertEqual("admissible after current lane", records["AI Repetition-to-Automation Pipeline"]["category"])
        self.assertEqual("admissible now", records["AI Long-Run Batch Orchestration"]["category"])
        self.assertEqual("already closed / locked", records["_stack Readiness"]["category"])
        self.assertEqual("already closed / locked", records["GitHub Control-Plane Integration"]["category"])

    def test_build_campaign_never_routes_a_100_percent_open_section_marker(self) -> None:
        root = self._temp_root()
        marker_doc = MARKER_DOC.replace(
            "- Cortex Dual-Mode Replacement Readiness: `0%`",
            "- Cortex Dual-Mode Replacement Readiness: `100%`",
        )
        (root / "docs" / "atlas-book" / "02-lanes-and-markers.md").write_text(marker_doc, encoding="utf-8")
        (root / "docs" / "atlas-book" / "01-current-state.md").write_text(CURRENT_STATE_DOC, encoding="utf-8")
        self._write_packet_receipts(root)

        payload = build_campaign(root=root)
        records = {record["marker"]: record for record in payload["open_markers"]}

        self.assertEqual("already closed / locked", records["Cortex Dual-Mode Replacement Readiness"]["category"])
        self.assertNotEqual("Cortex Dual-Mode Replacement Readiness", payload["next_after_current_marker"])

    def test_build_campaign_holds_vercel_observability_without_safe_read_transport(self) -> None:
        root = self._temp_root()
        marker_doc = """# Lanes And Markers

## Active Front-Page Marker Table

- Sandbox Simulation Readiness: `99%`

## Supporting Open Markers

- Vercel Platform Observability Governance: `0%`

## Closed / Locked Ratchets

- _stack Readiness: `100%`
"""
        current_state_doc = """# Current State

- the current active ATLAS-side lane is now `Sandbox Simulation Readiness`
"""
        (root / "docs" / "atlas-book" / "02-lanes-and-markers.md").write_text(marker_doc, encoding="utf-8")
        (root / "docs" / "atlas-book" / "01-current-state.md").write_text(current_state_doc, encoding="utf-8")
        self._write_packet_receipts(root)
        self._write_manifest(
            root,
            manifest_name="continuity-manifest-sandbox-simulation-readiness.json",
            marker="Sandbox Simulation Readiness",
            percent=99,
            checkpoint_ref=(
                "docs/ops/"
                "SANDBOX-SIMULATION-READINESS-POST-LOCAL-ONLY-FIRST-VALIDATOR-BROADER-"
                "RUNTIME-ASSERTIONS-ADMISSION-BOUNDARY-HOLD-OR-TOP-LEVEL-LANE-"
                "RESELECTION-2026-06-27.md"
            ),
            next_package="No immediate Sandbox Simulation Readiness same-lane packet",
            mode="hold-flat after broader-runtime-assertions admission boundary freeze",
            reason="current sandbox lane is intentionally held",
        )

        payload = build_campaign(root=root)

        self.assertEqual("no_immediate_root_packet", payload["operator_action"])
        self.assertIsNone(payload["next_after_current_marker"])
        self.assertIsNone(payload["next_after_current_packet"])

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
        records = {record["marker"]: record for record in payload["open_markers"]}

        self.assertEqual("hold_current_lane", payload["operator_action"])
        self.assertTrue(payload["active_lane_is_held"])
        self.assertEqual("held active lane", records["AI Long-Run Batch Orchestration"]["category"])

    def test_evidence_delta_advisory_releases_only_the_matching_open_manifest_hold(self) -> None:
        root = self._temp_root()
        (root / "docs" / "atlas-book" / "02-lanes-and-markers.md").write_text(MARKER_DOC, encoding="utf-8")
        (root / "docs" / "atlas-book" / "01-current-state.md").write_text(CURRENT_STATE_DOC, encoding="utf-8")
        self._write_packet_receipts(root)
        checkpoint_ref = (
            "docs/ops/AI-LONG-RUN-BATCH-ORCHESTRATION-POST-STACK-COMMAND-IMPLEMENTATION-"
            "ACTUAL-OWNER-SIDE-MUTATION-AUTHORITY-CLASS-VALUE-DOWNSTREAM-HOLD-RECHECK-2026-06-26.md"
        )
        self._write_manifest(
            root,
            manifest_name="continuity-manifest-ai-long-run-batch-orchestration.json",
            marker="AI Long-Run Batch Orchestration",
            percent=20,
            checkpoint_ref=checkpoint_ref,
            next_package="No immediate AI Long-Run Batch Orchestration same-lane packet",
            mode="hold-flat after downstream follow-on recheck",
            reason="current lane is intentionally held",
        )
        contract_ref = self._write_evidence_delta_contract(
            root,
            marker="AI Long-Run Batch Orchestration",
            held_ref=checkpoint_ref,
        )

        with mock.patch.object(selector, "EVIDENCE_DELTA_CONTRACT_REFS", (contract_ref,)):
            payload = build_campaign(root=root)

        self.assertEqual("continue_current_lane", payload["operator_action"])
        self.assertFalse(payload["active_lane_is_held"])
        self.assertEqual(
            ["AI Long-Run Batch Orchestration"],
            payload["evidence_delta_reopened_markers"],
        )
        advisory = payload["evidence_delta_advisories"][0]
        self.assertEqual("reopen_eligible", advisory["decision"])
        self.assertTrue(advisory["advisory_only"])
        self.assertEqual([], advisory["authority_actions"])
        self.assertEqual(20, payload["selected_percentage"])

    def test_missing_evidence_delta_source_fails_closed_and_preserves_manifest_hold(self) -> None:
        root = self._temp_root()
        (root / "docs" / "atlas-book" / "02-lanes-and-markers.md").write_text(MARKER_DOC, encoding="utf-8")
        (root / "docs" / "atlas-book" / "01-current-state.md").write_text(CURRENT_STATE_DOC, encoding="utf-8")
        self._write_packet_receipts(root)
        checkpoint_ref = (
            "docs/ops/AI-LONG-RUN-BATCH-ORCHESTRATION-POST-STACK-COMMAND-IMPLEMENTATION-"
            "ACTUAL-OWNER-SIDE-MUTATION-AUTHORITY-CLASS-VALUE-DOWNSTREAM-HOLD-RECHECK-2026-06-26.md"
        )
        self._write_manifest(
            root,
            manifest_name="continuity-manifest-ai-long-run-batch-orchestration.json",
            marker="AI Long-Run Batch Orchestration",
            percent=20,
            checkpoint_ref=checkpoint_ref,
            next_package="No immediate AI Long-Run Batch Orchestration same-lane packet",
            mode="hold-flat after downstream follow-on recheck",
            reason="current lane is intentionally held",
        )
        contract_ref = self._write_evidence_delta_contract(
            root,
            marker="AI Long-Run Batch Orchestration",
            held_ref=checkpoint_ref,
            evidence_present=False,
        )

        with mock.patch.object(selector, "EVIDENCE_DELTA_CONTRACT_REFS", (contract_ref,)):
            payload = build_campaign(root=root)

        self.assertEqual("hold_current_lane", payload["operator_action"])
        self.assertTrue(payload["active_lane_is_held"])
        self.assertEqual([], payload["evidence_delta_reopened_markers"])
        self.assertEqual("blocked", payload["evidence_delta_advisories"][0]["decision"])

    def test_reopen_advisory_cannot_reopen_a_closed_marker(self) -> None:
        root = self._temp_root()
        (root / "docs" / "atlas-book" / "02-lanes-and-markers.md").write_text(MARKER_DOC, encoding="utf-8")
        (root / "docs" / "atlas-book" / "01-current-state.md").write_text(CURRENT_STATE_DOC, encoding="utf-8")
        self._write_packet_receipts(root)
        contract_ref = self._write_evidence_delta_contract(
            root,
            marker="Archive Normalization",
            held_ref="docs/ops/archive-normalization-held.md",
        )

        with mock.patch.object(selector, "EVIDENCE_DELTA_CONTRACT_REFS", (contract_ref,)):
            payload = build_campaign(root=root)

        self.assertEqual([], payload["evidence_delta_reopened_markers"])
        self.assertEqual(100, payload["closed_markers"][0]["percentage"])

    def test_stale_advisory_cannot_release_a_newer_manifest_hold(self) -> None:
        root = self._temp_root()
        (root / "docs" / "atlas-book" / "02-lanes-and-markers.md").write_text(MARKER_DOC, encoding="utf-8")
        (root / "docs" / "atlas-book" / "01-current-state.md").write_text(CURRENT_STATE_DOC, encoding="utf-8")
        self._write_packet_receipts(root)
        current_checkpoint_ref = (
            "docs/ops/AI-LONG-RUN-BATCH-ORCHESTRATION-POST-STACK-COMMAND-IMPLEMENTATION-"
            "ACTUAL-OWNER-SIDE-MUTATION-AUTHORITY-CLASS-VALUE-DOWNSTREAM-HOLD-RECHECK-2026-06-26.md"
        )
        self._write_manifest(
            root,
            manifest_name="continuity-manifest-ai-long-run-batch-orchestration.json",
            marker="AI Long-Run Batch Orchestration",
            percent=20,
            checkpoint_ref=current_checkpoint_ref,
            next_package="No immediate AI Long-Run Batch Orchestration same-lane packet",
            mode="hold-flat after downstream follow-on recheck",
            reason="current lane is intentionally held",
        )
        contract_ref = self._write_evidence_delta_contract(
            root,
            marker="AI Long-Run Batch Orchestration",
            held_ref="docs/ops/older-held-checkpoint.md",
        )

        with mock.patch.object(selector, "EVIDENCE_DELTA_CONTRACT_REFS", (contract_ref,)):
            payload = build_campaign(root=root)

        self.assertEqual("hold_current_lane", payload["operator_action"])
        self.assertEqual([], payload["evidence_delta_reopened_markers"])

    def test_multiple_advisories_for_one_subject_fail_closed(self) -> None:
        root = self._temp_root()
        (root / "docs" / "atlas-book" / "02-lanes-and-markers.md").write_text(MARKER_DOC, encoding="utf-8")
        (root / "docs" / "atlas-book" / "01-current-state.md").write_text(CURRENT_STATE_DOC, encoding="utf-8")
        self._write_packet_receipts(root)
        checkpoint_ref = (
            "docs/ops/AI-LONG-RUN-BATCH-ORCHESTRATION-POST-STACK-COMMAND-IMPLEMENTATION-"
            "ACTUAL-OWNER-SIDE-MUTATION-AUTHORITY-CLASS-VALUE-DOWNSTREAM-HOLD-RECHECK-2026-06-26.md"
        )
        self._write_manifest(
            root,
            manifest_name="continuity-manifest-ai-long-run-batch-orchestration.json",
            marker="AI Long-Run Batch Orchestration",
            percent=20,
            checkpoint_ref=checkpoint_ref,
            next_package="No immediate AI Long-Run Batch Orchestration same-lane packet",
            mode="hold-flat after downstream follow-on recheck",
            reason="current lane is intentionally held",
        )
        first = self._write_evidence_delta_contract(
            root,
            marker="AI Long-Run Batch Orchestration",
            held_ref=checkpoint_ref,
            contract_name="first-held-lane-evidence-delta.v1.json",
        )
        second = self._write_evidence_delta_contract(
            root,
            marker="AI Long-Run Batch Orchestration",
            held_ref=checkpoint_ref,
            contract_name="second-held-lane-evidence-delta.v1.json",
        )

        with mock.patch.object(selector, "EVIDENCE_DELTA_CONTRACT_REFS", (first, second)):
            payload = build_campaign(root=root)

        self.assertEqual("hold_current_lane", payload["operator_action"])
        self.assertEqual([], payload["evidence_delta_reopened_markers"])
        self.assertEqual(
            ["AI Long-Run Batch Orchestration"],
            payload["evidence_delta_conflicts"],
        )

    def test_missing_configured_contract_blocks_otherwise_valid_reopen(self) -> None:
        root = self._temp_root()
        (root / "docs" / "atlas-book" / "02-lanes-and-markers.md").write_text(MARKER_DOC, encoding="utf-8")
        (root / "docs" / "atlas-book" / "01-current-state.md").write_text(CURRENT_STATE_DOC, encoding="utf-8")
        self._write_packet_receipts(root)
        checkpoint_ref = (
            "docs/ops/AI-LONG-RUN-BATCH-ORCHESTRATION-POST-STACK-COMMAND-IMPLEMENTATION-"
            "ACTUAL-OWNER-SIDE-MUTATION-AUTHORITY-CLASS-VALUE-DOWNSTREAM-HOLD-RECHECK-2026-06-26.md"
        )
        self._write_manifest(
            root,
            manifest_name="continuity-manifest-ai-long-run-batch-orchestration.json",
            marker="AI Long-Run Batch Orchestration",
            percent=20,
            checkpoint_ref=checkpoint_ref,
            next_package="No immediate AI Long-Run Batch Orchestration same-lane packet",
            mode="hold-flat after downstream follow-on recheck",
            reason="current lane is intentionally held",
        )
        valid_ref = self._write_evidence_delta_contract(
            root,
            marker="AI Long-Run Batch Orchestration",
            held_ref=checkpoint_ref,
        )
        missing_ref = "docs/registry/missing-held-lane-evidence-delta.v1.json"

        with mock.patch.object(
            selector,
            "EVIDENCE_DELTA_CONTRACT_REFS",
            (valid_ref, missing_ref),
        ):
            payload = build_campaign(root=root)

        self.assertEqual("hold_current_lane", payload["operator_action"])
        self.assertEqual([], payload["evidence_delta_reopened_markers"])
        self.assertEqual(
            [f"unresolved_contract:{missing_ref}"],
            payload["evidence_delta_conflicts"],
        )

    def test_whitespace_subject_contract_blocks_otherwise_valid_reopen(self) -> None:
        root = self._temp_root()
        (root / "docs" / "atlas-book" / "02-lanes-and-markers.md").write_text(MARKER_DOC, encoding="utf-8")
        (root / "docs" / "atlas-book" / "01-current-state.md").write_text(CURRENT_STATE_DOC, encoding="utf-8")
        self._write_packet_receipts(root)
        checkpoint_ref = (
            "docs/ops/AI-LONG-RUN-BATCH-ORCHESTRATION-POST-STACK-COMMAND-IMPLEMENTATION-"
            "ACTUAL-OWNER-SIDE-MUTATION-AUTHORITY-CLASS-VALUE-DOWNSTREAM-HOLD-RECHECK-2026-06-26.md"
        )
        self._write_manifest(
            root,
            manifest_name="continuity-manifest-ai-long-run-batch-orchestration.json",
            marker="AI Long-Run Batch Orchestration",
            percent=20,
            checkpoint_ref=checkpoint_ref,
            next_package="No immediate AI Long-Run Batch Orchestration same-lane packet",
            mode="hold-flat after downstream follow-on recheck",
            reason="current lane is intentionally held",
        )
        valid_ref = self._write_evidence_delta_contract(
            root,
            marker="AI Long-Run Batch Orchestration",
            held_ref=checkpoint_ref,
        )
        invalid_ref = self._write_evidence_delta_contract(
            root,
            marker="   ",
            held_ref=checkpoint_ref,
            contract_name="whitespace-subject-held-lane-evidence-delta.v1.json",
        )

        with mock.patch.object(
            selector,
            "EVIDENCE_DELTA_CONTRACT_REFS",
            (valid_ref, invalid_ref),
        ):
            payload = build_campaign(root=root)

        self.assertEqual("hold_current_lane", payload["operator_action"])
        self.assertEqual([], payload["evidence_delta_reopened_markers"])
        self.assertEqual(
            [f"unresolved_contract:{invalid_ref}"],
            payload["evidence_delta_conflicts"],
        )

    def test_padded_subject_contract_blocks_otherwise_valid_reopen(self) -> None:
        root = self._temp_root()
        (root / "docs" / "atlas-book" / "02-lanes-and-markers.md").write_text(MARKER_DOC, encoding="utf-8")
        (root / "docs" / "atlas-book" / "01-current-state.md").write_text(CURRENT_STATE_DOC, encoding="utf-8")
        self._write_packet_receipts(root)
        checkpoint_ref = (
            "docs/ops/AI-LONG-RUN-BATCH-ORCHESTRATION-POST-STACK-COMMAND-IMPLEMENTATION-"
            "ACTUAL-OWNER-SIDE-MUTATION-AUTHORITY-CLASS-VALUE-DOWNSTREAM-HOLD-RECHECK-2026-06-26.md"
        )
        self._write_manifest(
            root,
            manifest_name="continuity-manifest-ai-long-run-batch-orchestration.json",
            marker="AI Long-Run Batch Orchestration",
            percent=20,
            checkpoint_ref=checkpoint_ref,
            next_package="No immediate AI Long-Run Batch Orchestration same-lane packet",
            mode="hold-flat after downstream follow-on recheck",
            reason="current lane is intentionally held",
        )
        valid_ref = self._write_evidence_delta_contract(
            root,
            marker="AI Long-Run Batch Orchestration",
            held_ref=checkpoint_ref,
        )
        invalid_ref = self._write_evidence_delta_contract(
            root,
            marker=" AI Long-Run Batch Orchestration ",
            held_ref=checkpoint_ref,
            contract_name="padded-subject-held-lane-evidence-delta.v1.json",
        )

        with mock.patch.object(
            selector,
            "EVIDENCE_DELTA_CONTRACT_REFS",
            (valid_ref, invalid_ref),
        ):
            payload = build_campaign(root=root)

        self.assertEqual("hold_current_lane", payload["operator_action"])
        self.assertEqual([], payload["evidence_delta_reopened_markers"])
        self.assertEqual(
            [f"unresolved_contract:{invalid_ref}"],
            payload["evidence_delta_conflicts"],
        )

    def test_missing_manifest_checkpoint_preserves_the_hold(self) -> None:
        root = self._temp_root()
        (root / "docs" / "atlas-book" / "02-lanes-and-markers.md").write_text(MARKER_DOC, encoding="utf-8")
        (root / "docs" / "atlas-book" / "01-current-state.md").write_text(CURRENT_STATE_DOC, encoding="utf-8")
        self._write_packet_receipts(root)
        restart_index = {
            "items": [
                {
                    "marker": "AI Long-Run Batch Orchestration",
                    "restart_status": "restart_ready",
                    "current_checkpoint_receipt": None,
                    "next_package": {
                        "package": "No immediate AI Long-Run Batch Orchestration same-lane packet"
                    },
                }
            ]
        }

        with (
            mock.patch.object(selector, "build_open_marker_restart_index", return_value=restart_index),
            mock.patch.object(selector, "EVIDENCE_DELTA_CONTRACT_REFS", ()),
        ):
            payload = build_campaign(root=root)

        self.assertEqual("hold_current_lane", payload["operator_action"])
        self.assertTrue(payload["active_lane_is_held"])

    def test_duplicate_manifest_checkpoints_preserve_the_hold(self) -> None:
        root = self._temp_root()
        (root / "docs" / "atlas-book" / "02-lanes-and-markers.md").write_text(MARKER_DOC, encoding="utf-8")
        (root / "docs" / "atlas-book" / "01-current-state.md").write_text(CURRENT_STATE_DOC, encoding="utf-8")
        self._write_packet_receipts(root)
        restart_index = {
            "items": [
                {
                    "marker": "AI Long-Run Batch Orchestration",
                    "restart_status": "restart_ready",
                    "current_checkpoint_receipt": "docs/ops/first.md",
                    "next_package": {
                        "package": "No immediate AI Long-Run Batch Orchestration same-lane packet"
                    },
                },
                {
                    "marker": "AI Long-Run Batch Orchestration",
                    "restart_status": "restart_ready",
                    "current_checkpoint_receipt": "docs/ops/second.md",
                    "next_package": {
                        "package": "No immediate AI Long-Run Batch Orchestration same-lane packet"
                    },
                },
            ]
        }

        with (
            mock.patch.object(selector, "build_open_marker_restart_index", return_value=restart_index),
            mock.patch.object(selector, "EVIDENCE_DELTA_CONTRACT_REFS", ()),
        ):
            payload = build_campaign(root=root)

        self.assertEqual("hold_current_lane", payload["operator_action"])
        self.assertTrue(payload["active_lane_is_held"])

    def test_build_campaign_reports_no_immediate_root_packet_when_all_open_markers_are_held(self) -> None:
        root = self._temp_root()
        marker_doc = """# Lanes And Markers

## Active Front-Page Marker Table

- AI Repetition-to-Automation Pipeline: `35%`
- AI Long-Run Batch Orchestration: `20%`

## Supporting Open Markers

- Fitness QA/LLEL Workflow: `96%`

## Closed / Locked Ratchets

- _stack Readiness: `100%`
"""
        current_state_doc = """# Current State

- the current active ATLAS-side lane is now `AI Long-Run Batch Orchestration`
"""
        (root / "docs" / "atlas-book" / "02-lanes-and-markers.md").write_text(marker_doc, encoding="utf-8")
        (root / "docs" / "atlas-book" / "01-current-state.md").write_text(current_state_doc, encoding="utf-8")
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

        payload = build_campaign(root=root)
        records = {record["marker"]: record for record in payload["open_markers"]}

        self.assertEqual("no_immediate_root_packet", payload["operator_action"])
        self.assertIsNone(payload["next_after_current_marker"])
        self.assertEqual("held active lane", records["AI Long-Run Batch Orchestration"]["category"])
        self.assertEqual(1, payload["category_counts"]["held active lane"])
        self.assertNotIn("admissible now", payload["category_counts"])

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
            "broader-runtime-assertions admission boundary contract",
            records["Sandbox Simulation Readiness"]["rationale"],
        )
        self.assertEqual(
            "No immediate Sandbox Simulation Readiness same-lane packet",
            payload["next_after_current_packet"],
        )
        self.assertEqual(
            "docs/ops/SANDBOX-SIMULATION-READINESS-POST-RUNTIME-BINDING-INDEPENDENT-RATIFICATION-2026-07-14.md",
            payload["next_after_current_packet_basis_ref"],
        )
        self.assertEqual(
            "completed-lane lock",
            payload["next_after_current_packet_mode"],
        )
        self.assertIn(
            "completed local-only Sandbox denominator",
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

    def test_main_markdown_omits_do_now_when_active_lane_is_held(self) -> None:
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
        output_ref = "docs/ops/selector-held-output.md"

        exit_code = main(["--root", str(root), "--format", "markdown", "--output", output_ref])

        self.assertEqual(0, exit_code)
        markdown = (root / output_ref).read_text(encoding="utf-8")
        self.assertIn("action: `hold_current_lane`", markdown)
        self.assertIn("- no immediate same-lane packet is open.", markdown)
        self.assertIn("`held active lane`", markdown)
        self.assertNotIn("- do now:", markdown)

    def test_main_markdown_reports_no_immediate_root_packet_when_everything_is_held(self) -> None:
        root = self._temp_root()
        marker_doc = """# Lanes And Markers

## Active Front-Page Marker Table

- AI Repetition-to-Automation Pipeline: `35%`
- AI Long-Run Batch Orchestration: `20%`

## Supporting Open Markers

- Fitness QA/LLEL Workflow: `96%`

## Closed / Locked Ratchets

- _stack Readiness: `100%`
"""
        current_state_doc = """# Current State

- the current active ATLAS-side lane is now `AI Long-Run Batch Orchestration`
"""
        (root / "docs" / "atlas-book" / "02-lanes-and-markers.md").write_text(marker_doc, encoding="utf-8")
        (root / "docs" / "atlas-book" / "01-current-state.md").write_text(current_state_doc, encoding="utf-8")
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
        output_ref = "docs/ops/selector-no-immediate-root-output.md"

        exit_code = main(["--root", str(root), "--format", "markdown", "--output", output_ref])

        self.assertEqual(0, exit_code)
        markdown = (root / output_ref).read_text(encoding="utf-8")
        self.assertIn("action: `no_immediate_root_packet`", markdown)
        self.assertIn("- no immediate ATLAS-root packet is open.", markdown)
        self.assertIn("`held active lane`", markdown)
        self.assertIn(
            "current packet scope: `re-evaluate the post-authority-class-value downstream fall-through against manifest-backed no-immediate packet holds and decide whether any honest root-bounded follow-on remains`",
            markdown,
        )
        self.assertIn("## Current Active Marker", markdown)
        self.assertIn(
            "current packet: `AI Long-Run Batch Orchestration post-stack-command-implementation-actual-owner-side-mutation-authority-class-value downstream hold recheck`",
            markdown,
        )
        self.assertNotIn("## First Admissible After Current Lane", markdown)
        self.assertNotIn("next packet mode:", markdown)
        self.assertNotIn("next packet scope:", markdown)

    def test_build_campaign_routes_new_ai_work_session_loop_after_current_hold(self) -> None:
        root = self._temp_root()
        marker_doc = """# Lanes And Markers

## Active Front-Page Marker Table

- AI Long-Run Batch Orchestration: `20%`
- Sandbox Simulation Readiness: `99%`

## Supporting Open Markers

- AI Work Session Stability & Auto-Sync Loop: `10%`

## Closed / Locked Ratchets

- _stack Readiness: `100%`
"""
        current_state_doc = """# Current State

- the current active ATLAS-side lane is now `Sandbox Simulation Readiness`
"""
        (root / "docs" / "atlas-book" / "02-lanes-and-markers.md").write_text(marker_doc, encoding="utf-8")
        (root / "docs" / "atlas-book" / "01-current-state.md").write_text(current_state_doc, encoding="utf-8")
        self._write_packet_receipts(root)
        contract_receipt = root / "docs" / "ops" / "AI-WORK-SESSION-STABILITY-AUTO-SYNC-LOOP-CONTRACT-FREEZE-2026-06-29.md"
        contract_receipt.write_text("# contract\n", encoding="utf-8")
        self._write_manifest(
            root,
            manifest_name="continuity-manifest-sandbox-simulation-readiness.json",
            marker="Sandbox Simulation Readiness",
            percent=99,
            checkpoint_ref=(
                "docs/ops/"
                "SANDBOX-SIMULATION-READINESS-POST-LOCAL-ONLY-FIRST-VALIDATOR-BROADER-"
                "RUNTIME-ASSERTIONS-ADMISSION-BOUNDARY-HOLD-OR-TOP-LEVEL-LANE-"
                "RESELECTION-2026-06-27.md"
            ),
            next_package="No immediate Sandbox Simulation Readiness same-lane packet",
            mode="hold-flat after broader-runtime-assertions admission boundary freeze",
            reason="current sandbox lane is intentionally held",
        )
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
            reason="fallback lane is intentionally held",
        )

        payload = build_campaign(root=root)

        self.assertEqual("hold_current_lane", payload["operator_action"])
        self.assertEqual("AI Work Session Stability & Auto-Sync Loop", payload["next_after_current_marker"])
        self.assertEqual(
            "No immediate AI Work Session Stability & Auto-Sync Loop same-lane packet; root-plus-owner adoption threshold is satisfied and future widening requires a separately scoped adoption or automation packet",
            payload["next_after_current_packet"],
        )
        self.assertEqual(
            "docs/ops/AI-WORK-SESSION-STABILITY-AUTO-SYNC-LOOP-ROOT-PLUS-OWNER-ADOPTION-THRESHOLD-RECONCILIATION-2026-07-04.md",
            payload["next_after_current_packet_basis_ref"],
        )
        self.assertEqual(
            "held after root-plus-owner adoption threshold reconciliation",
            payload["next_after_current_packet_mode"],
        )
        self.assertIn(
            "2 of 2 required owner-lane proof receipts",
            payload["next_after_current_packet_scope"],
        )

    def test_build_campaign_routes_new_cortex_future_markers_when_they_are_first_available(self) -> None:
        root = self._temp_root()
        marker_doc = """# Lanes And Markers

## Active Front-Page Marker Table

- Sandbox Simulation Readiness: `99%`

## Supporting Open Markers

- Cortex Dual-Mode Replacement Readiness: `20%`
- Cortex Simulation Substrate Readiness: `0%`

## Closed / Locked Ratchets

- _stack Readiness: `100%`
"""
        current_state_doc = """# Current State

- the current active ATLAS-side lane is now `Sandbox Simulation Readiness`
"""
        (root / "docs" / "atlas-book" / "02-lanes-and-markers.md").write_text(marker_doc, encoding="utf-8")
        (root / "docs" / "atlas-book" / "01-current-state.md").write_text(current_state_doc, encoding="utf-8")
        self._write_packet_receipts(root)
        self._write_manifest(
            root,
            manifest_name="continuity-manifest-sandbox-simulation-readiness.json",
            marker="Sandbox Simulation Readiness",
            percent=99,
            checkpoint_ref=(
                "docs/ops/"
                "SANDBOX-SIMULATION-READINESS-POST-LOCAL-ONLY-FIRST-VALIDATOR-BROADER-"
                "RUNTIME-ASSERTIONS-ADMISSION-BOUNDARY-HOLD-OR-TOP-LEVEL-LANE-"
                "RESELECTION-2026-06-27.md"
            ),
            next_package="No immediate Sandbox Simulation Readiness same-lane packet",
            mode="hold-flat after broader-runtime-assertions admission boundary freeze",
            reason="current sandbox lane is intentionally held",
        )
        self._write_manifest(
            root,
            manifest_name="continuity-manifest-cortex-dual-mode-replacement-readiness.json",
            marker="Cortex Dual-Mode Replacement Readiness",
            percent=20,
            checkpoint_ref=(
                "docs/ops/"
                "CORTEX-DUAL-MODE-REPLACEMENT-READINESS-CHATGPT-CODEX-ROLE-INVENTORY-"
                "MARKER-SURFACE-RATCHET-DECISION-2026-07-09.md"
            ),
            next_package="Cortex Dual-Mode Replacement Readiness synthesis-to-execution bridge schema contract freeze",
            mode="docs-only root-bounded synthesis-to-execution bridge-schema contract freeze",
            reason="the operating model and implementation-backed role inventory thresholds are now satisfied, so the next honest dual-mode threshold is freezing the bounded synthesis-to-execution bridge contract without widening authority",
        )

        payload = build_campaign(root=root)

        self.assertEqual("hold_current_lane", payload["operator_action"])
        self.assertEqual("Cortex Dual-Mode Replacement Readiness", payload["next_after_current_marker"])
        self.assertEqual(
            "Cortex Dual-Mode Replacement Readiness _stack dispatch and durable result first implementation",
            payload["next_after_current_packet"],
        )
        self.assertEqual(
            "serialized root implementation then bounded live _stack no-change canary",
            payload["next_after_current_packet_mode"],
        )
        self.assertIn("success_no_changes canary", payload["next_after_current_packet_scope"])

    def test_build_campaign_routes_owner_lane_service_bus_marker_when_it_is_first_available(self) -> None:
        root = self._temp_root()
        marker_doc = """# Lanes And Markers

## Active Front-Page Marker Table

- Sandbox Simulation Readiness: `99%`

## Supporting Open Markers

- Owner-Lane Agent Service Bus & DiscordOS Ops Readiness: `0%`

## Closed / Locked Ratchets

- _stack Readiness: `100%`
"""
        current_state_doc = """# Current State

- the current active ATLAS-side lane is now `Sandbox Simulation Readiness`
"""
        (root / "docs" / "atlas-book" / "02-lanes-and-markers.md").write_text(marker_doc, encoding="utf-8")
        (root / "docs" / "atlas-book" / "01-current-state.md").write_text(current_state_doc, encoding="utf-8")
        self._write_packet_receipts(root)
        self._write_manifest(
            root,
            manifest_name="continuity-manifest-sandbox-simulation-readiness.json",
            marker="Sandbox Simulation Readiness",
            percent=99,
            checkpoint_ref=(
                "docs/ops/"
                "SANDBOX-SIMULATION-READINESS-POST-LOCAL-ONLY-FIRST-VALIDATOR-BROADER-"
                "RUNTIME-ASSERTIONS-ADMISSION-BOUNDARY-HOLD-OR-TOP-LEVEL-LANE-"
                "RESELECTION-2026-06-27.md"
            ),
            next_package="No immediate Sandbox Simulation Readiness same-lane packet",
            mode="hold-flat after broader-runtime-assertions admission boundary freeze",
            reason="current sandbox lane is intentionally held",
        )

        payload = build_campaign(root=root)

        self.assertEqual("hold_current_lane", payload["operator_action"])
        self.assertEqual("Owner-Lane Agent Service Bus & DiscordOS Ops Readiness", payload["next_after_current_marker"])
        self.assertEqual(
            "Owner-Lane Agent Service Bus & DiscordOS Ops Atlas/Mazer/Fitness end-to-end canary admission",
            payload["next_after_current_packet"],
        )
        self.assertEqual(
            "docs/ops/OWNER-LANE-AGENT-SERVICE-BUS-AND-DISCORDOS-OPS-CURRENT-JOURNAL-LIVE-READBACK-COMPATIBILITY-AND-90-PERCENT-RECONCILIATION-2026-07-14.md",
            payload["next_after_current_packet_basis_ref"],
        )
        self.assertEqual(
            "bounded cross-surface no-production canary admission",
            payload["next_after_current_packet_mode"],
        )
        self.assertIn("job, native task, execution receipt, card", payload["next_after_current_packet_scope"])


if __name__ == "__main__":
    unittest.main()
