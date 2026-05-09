from __future__ import annotations

import io
import json
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

from ops._atlas import atlas_root
from ops.cortex.ledger import (
    build_cortex_ledger_payload,
    default_ledger_latest_json_path,
    default_ledger_latest_markdown_path,
    main,
    persist_cortex_ledger_artifact,
)
from ops.cortex.loop import load_and_run_cortex_loop


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


class CortexLedgerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.root = atlas_root()
        cls.current_state_payload = json.loads(
            (cls.root / "runtime" / "cortex" / "current-state" / "latest.json").read_text(encoding="utf-8")
        )
        cls.rail_state_payload = json.loads(
            (cls.root / "runtime" / "cortex" / "rail-state" / "latest.json").read_text(encoding="utf-8")
        )
        cls.context_payload = json.loads(
            (cls.root / "runtime" / "cortex" / "context" / "latest.json").read_text(encoding="utf-8")
        )
        cls.operator_surface_payload = json.loads(
            (cls.root / "runtime" / "cortex" / "operator-surface" / "latest.json").read_text(encoding="utf-8")
        )
        cls.state_payload = json.loads(
            (cls.root / "runtime" / "cortex" / "kernel.state-model.seed.v1.json").read_text(encoding="utf-8")
        )
        cls.rule_payload = json.loads(
            (cls.root / "runtime" / "cortex" / "kernel.rule-registry.seed.v1.json").read_text(encoding="utf-8")
        )
        cls.run_payload = load_and_run_cortex_loop(root=cls.root).to_payload()

    def _base_validation_payload(
        self,
        *,
        counts: dict[str, int] | None = None,
        findings: list[dict] | None = None,
    ) -> dict:
        summary = counts or {
            "critical": 0,
            "error": 0,
            "warning": 4,
            "info": 1,
            "total": 5,
        }
        return {
            "generated_at": "2026-05-06T21:00:00+00:00",
            "stack_file": "stack.yaml",
            "stack_root": ".",
            "stack_lock_file": "stack.lock.yaml",
            "summary": summary,
            "repo_ids": ["stack", "fitness", "lifeline"],
            "findings": findings or [],
        }

    def _base_current_state_payload(self) -> dict:
        payload = json.loads(json.dumps(self.current_state_payload))
        payload["generated_at"] = "2026-05-06T21:01:00+00:00"
        payload["branch"] = "codex/cortex-ledger-wave5"
        payload["head"] = "def456abc123"
        payload["worktree_status"] = "clean"
        payload["changed_files"] = []
        payload["untracked_files"] = []
        payload["remote_publication_state"] = {
            "status": "in_sync",
            "branch": "codex/cortex-ledger-wave5",
            "head": "def456abc123",
            "published": True,
            "upstream": "origin/codex/cortex-ledger-wave5",
            "pr_state": "open",
            "pr_url": "https://example.invalid/pr/10",
            "notes": [],
        }
        payload["validation_counts"] = {
            "critical": 0,
            "error": 0,
            "warning": 4,
            "info": 1,
            "total": 5,
        }
        payload["active_blockers"] = []
        payload["next_recommended_lane"] = {
            "lane_id": "promote-cortex-receipt-interpretation-contract-wave9",
            "owner_layer": "cortex",
            "rationale": "The bounded _stack stack-consumption pilot is landed, but Cortex still needs one promoted default _stack consumer routing contract that consumes explicit Cortex worker-prompt, context, operator, ledger, and pilot artifacts without transcript scraping, execution authority, owner-truth mutation, or Lifeline receipt authority.",
            "blocked_by": [],
            "source_refs": [
                "runtime/cortex/kernel.state-model.seed.v1.json",
                "runtime/cortex/kernel.rule-registry.seed.v1.json",
            ],
        }
        return payload

    def _base_rail_state_payload(self) -> dict:
        payload = json.loads(json.dumps(self.rail_state_payload))
        payload["generated_at"] = "2026-05-06T21:02:00+00:00"
        payload["rail_status"] = "ready"
        payload["active_blockers"] = []
        payload["dirty_lanes"] = ["cortex-receipt-interpretation-contract-v0-1"]
        payload["validation_posture"] = {
            "status": "ambient-debt-only",
            "counts": {
                "critical": 0,
                "error": 0,
                "warning": 4,
                "info": 1,
                "total": 5,
            },
            "receipt_generated_at": "2026-05-06T21:00:00+00:00",
            "receipt_path": "runtime/receipts/validation/stack-validation.latest.json",
        }
        payload["next_recommended_lane"] = {
            "lane_id": "promote-cortex-receipt-interpretation-contract-wave9",
            "owner_layer": "cortex",
            "rationale": "The bounded _stack stack-consumption pilot is landed, but Cortex still needs one promoted default _stack consumer routing contract that consumes explicit Cortex worker-prompt, context, operator, ledger, and pilot artifacts without transcript scraping, execution authority, owner-truth mutation, or Lifeline receipt authority.",
            "blocked_by": [],
            "source_refs": [
                "runtime/cortex/current-state/latest.json",
                "runtime/cortex/kernel.state-model.seed.v1.json",
                "runtime/cortex/kernel.rule-registry.seed.v1.json",
            ],
        }
        return payload

    def _base_context_payload(self) -> dict:
        payload = json.loads(json.dumps(self.context_payload))
        payload["generated_at"] = "2026-05-06T21:03:00+00:00"
        payload["packet_id"] = "context-promote-cortex-receipt-interpretation-contract-wave9"
        payload["context_summary"] = (
            "Cortex context packet for promote-cortex-receipt-interpretation-contract-wave9 derived from explicit current-state, "
            "rail-state, validation, and seed artifacts."
        )
        payload["task_frame"]["lane_id"] = "promote-cortex-receipt-interpretation-contract-wave9"
        payload["task_frame"]["owner_layer"] = "cortex"
        payload["task_frame"]["title"] = "Promote Cortex _stack consumer default routing."
        payload["task_frame"]["status"] = "ready"
        payload["task_frame"]["rationale"] = (
            "The worker-prompt contract is landed, but Cortex still needs one bounded _stack pilot that consumes current "
            "context and planning artifacts without transcript scraping while planner, context, proof, receipt-draft, and final receipt stay separate and "
            "linked by refs and digests."
        )
        payload["task_frame"]["blocked_by"] = []
        payload["task_frame"]["required_inputs"] = [
            "runtime/cortex/current-state/latest.json",
            "runtime/cortex/rail-state/latest.json",
            "runtime/cortex/context/latest.json",
            "runtime/cortex/operator-surface/latest.json",
            "runtime/cortex/ledger/latest.json",
            "runtime/cortex/worker-prompts/latest.json",
            "runtime/cortex/stack-consumption-pilot/latest.json",
            "runtime/cortex/kernel.state-model.seed.v1.json",
            "runtime/cortex/kernel.rule-registry.seed.v1.json",
            "docs/atlas/notes/cortex-surface-reconciliation-2026-05-06.md",
        ]
        payload["task_frame"]["ready_to_execute"] = True
        return payload

    def _base_operator_surface_payload(self) -> dict:
        payload = json.loads(json.dumps(self.operator_surface_payload))
        payload["generated_at"] = "2026-05-06T21:04:00+00:00"
        payload["operator_summary"] = (
            "Cortex operator surface for promote-cortex-receipt-interpretation-contract-wave9 derived from explicit current-state, "
            "rail-state, context, validation, and seed artifacts."
        )
        payload["rail_status"] = "ready"
        payload["active_blockers"] = []
        payload["dirty_lanes"] = ["cortex-receipt-interpretation-contract-v0-1"]
        payload["next_recommended_lane"] = {
            "lane_id": "promote-cortex-receipt-interpretation-contract-wave9",
            "owner_layer": "cortex",
            "rationale": "The bounded _stack stack-consumption pilot is landed, but Cortex still needs one promoted default _stack consumer routing contract that consumes explicit Cortex worker-prompt, context, operator, ledger, and pilot artifacts without transcript scraping, execution authority, owner-truth mutation, or Lifeline receipt authority.",
            "blocked_by": [],
            "source_refs": [
                "runtime/cortex/current-state/latest.json",
                "runtime/cortex/kernel.state-model.seed.v1.json",
                "runtime/cortex/kernel.rule-registry.seed.v1.json",
            ],
        }
        payload["validation_counts"] = {
            "critical": 0,
            "error": 0,
            "warning": 4,
            "info": 1,
            "total": 5,
        }
        payload["publication_posture"] = {
            "branch": "codex/cortex-ledger-wave5",
            "head": "def456abc123",
            "worktree_status": "clean",
            "remote_status": "in_sync",
            "upstream": "origin/codex/cortex-ledger-wave5",
            "published": True,
            "pr_state": "open",
            "pr_url": "https://example.invalid/pr/10",
        }
        payload["context_packet_id"] = "context-promote-cortex-receipt-interpretation-contract-wave9"
        payload["context_summary"] = (
            "Cortex context packet for promote-cortex-receipt-interpretation-contract-wave9 derived from explicit current-state, "
            "rail-state, validation, and seed artifacts."
        )
        payload["task_frame_summary"]["lane_id"] = "promote-cortex-receipt-interpretation-contract-wave9"
        payload["task_frame_summary"]["owner_layer"] = "cortex"
        payload["task_frame_summary"]["title"] = "Promote Cortex _stack consumer default routing."
        payload["task_frame_summary"]["status"] = "ready"
        payload["task_frame_summary"]["rationale"] = (
            "The worker-prompt contract is landed, but Cortex still needs one bounded _stack pilot that consumes current "
            "context and planning artifacts without transcript scraping while planner, context, proof, receipt-draft, and final receipt stay separate and "
            "linked by refs and digests."
        )
        payload["task_frame_summary"]["blocked_by"] = []
        payload["task_frame_summary"]["required_inputs"] = [
            "runtime/cortex/current-state/latest.json",
            "runtime/cortex/rail-state/latest.json",
            "runtime/cortex/context/latest.json",
            "runtime/cortex/operator-surface/latest.json",
            "runtime/cortex/ledger/latest.json",
            "runtime/cortex/worker-prompts/latest.json",
            "runtime/cortex/stack-consumption-pilot/latest.json",
            "runtime/cortex/kernel.state-model.seed.v1.json",
            "runtime/cortex/kernel.rule-registry.seed.v1.json",
            "docs/atlas/notes/cortex-surface-reconciliation-2026-05-06.md",
        ]
        payload["task_frame_summary"]["ready_to_execute"] = True
        payload["top_evidence_refs"] = [
            "runtime/cortex/current-state/latest.json",
            "runtime/cortex/rail-state/latest.json",
            "runtime/receipts/validation/stack-validation.latest.json",
            "runtime/cortex/kernel.state-model.seed.v1.json",
            "runtime/cortex/kernel.rule-registry.seed.v1.json",
        ]
        return payload

    def _temp_root(
        self,
        *,
        current_state_payload: dict | None = None,
        rail_state_payload: dict | None = None,
        context_payload: dict | None = None,
        operator_surface_payload: dict | None = None,
        validation_payload: dict | None = None,
        include_run_artifact: bool = False,
    ) -> Path:
        temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(temp_dir.cleanup)
        root = Path(temp_dir.name)
        _write_json(
            root / "runtime" / "cortex" / "current-state" / "latest.json",
            current_state_payload or self._base_current_state_payload(),
        )
        _write_json(
            root / "runtime" / "cortex" / "rail-state" / "latest.json",
            rail_state_payload or self._base_rail_state_payload(),
        )
        _write_json(
            root / "runtime" / "cortex" / "context" / "latest.json",
            context_payload or self._base_context_payload(),
        )
        _write_json(
            root / "runtime" / "cortex" / "operator-surface" / "latest.json",
            operator_surface_payload or self._base_operator_surface_payload(),
        )
        _write_json(
            root / "runtime" / "receipts" / "validation" / "stack-validation.latest.json",
            validation_payload or self._base_validation_payload(),
        )
        _write_json(root / "runtime" / "cortex" / "kernel.state-model.seed.v1.json", self.state_payload)
        _write_json(root / "runtime" / "cortex" / "kernel.rule-registry.seed.v1.json", self.rule_payload)
        if include_run_artifact:
            _write_json(root / "runtime" / "cortex" / "runs" / "cortex-run-result.latest.json", self.run_payload)
        return root

    def test_clean_ready_posture_emits_canonical_ledger(self) -> None:
        root = self._temp_root()

        payload = build_cortex_ledger_payload(root=root)

        self.assertEqual("atlas.cortex.ledger.v1", payload["schema_version"])
        self.assertEqual("read_only_advisory", payload["authority_level"])
        self.assertEqual("ready", payload["rail_status"])
        self.assertEqual([], payload["active_blockers"])
        self.assertEqual("promote-cortex-receipt-interpretation-contract-wave9", payload["next_recommended_lane"]["lane_id"])
        self.assertEqual("context-promote-cortex-receipt-interpretation-contract-wave9", payload["context_packet_id"])
        self.assertEqual("clean", payload["worktree_status"])
        self.assertEqual("unavailable", payload["proof_or_receipt_readiness"]["status"])
        self.assertEqual(
            {
                "current_state": "runtime/cortex/current-state/latest.json",
                "rail_state": "runtime/cortex/rail-state/latest.json",
                "context": "runtime/cortex/context/latest.json",
                "operator_surface": "runtime/cortex/operator-surface/latest.json",
                "validation": "runtime/receipts/validation/stack-validation.latest.json",
                "seed": "runtime/cortex/kernel.state-model.seed.v1.json",
                "rules": "runtime/cortex/kernel.rule-registry.seed.v1.json",
            },
            payload["source_artifact_refs"],
        )
        json.dumps(payload, sort_keys=True)

    def test_run_ledger_summary_is_included_when_run_artifact_exists(self) -> None:
        root = self._temp_root(include_run_artifact=True)

        payload = build_cortex_ledger_payload(root=root)

        proof = payload["proof_or_receipt_readiness"]
        self.assertEqual("passed", proof["status"])
        self.assertTrue(proof["receipt_ready"])
        self.assertEqual("promote-cortex-receipt-interpretation-contract-wave9", proof["selected_next_action"])
        labels = [item["label"] for item in payload["evidence_refs"]]
        self.assertIn("run_ledger.latest_run", labels)

    def test_validation_blockers_are_preserved_and_ordered_deterministically(self) -> None:
        current_state_payload = self._base_current_state_payload()
        current_state_payload["worktree_status"] = "dirty"
        current_state_payload["changed_files"] = ["ops/cortex/ledger.py"]
        current_state_payload["active_blockers"] = [
            {
                "code": "zeta",
                "severity": "critical",
                "summary": "Zeta blocker.",
                "source_kind": "validation_receipt",
                "source_ref": "runtime/receipts/validation/stack-validation.latest.json",
                "details": {"path": "repos/example-z"},
            },
            {
                "code": "alpha",
                "severity": "critical",
                "summary": "Alpha blocker.",
                "source_kind": "validation_receipt",
                "source_ref": "runtime/receipts/validation/stack-validation.latest.json",
                "details": {"path": "repos/example-a"},
            },
        ]
        rail_state_payload = self._base_rail_state_payload()
        rail_state_payload["rail_status"] = "blocked"
        rail_state_payload["active_blockers"] = list(reversed(current_state_payload["active_blockers"]))
        operator_surface_payload = self._base_operator_surface_payload()
        operator_surface_payload["active_blockers"] = rail_state_payload["active_blockers"]
        validation_payload = self._base_validation_payload(
            counts={"critical": 1, "error": 1, "warning": 4, "info": 0, "total": 6},
            findings=[
                {"severity": "critical", "category": "zeta", "path": "repos/example-z", "message": "Zeta blocker."},
                {"severity": "error", "category": "alpha", "path": "repos/example-a", "message": "Alpha blocker."},
            ],
        )
        root = self._temp_root(
            current_state_payload=current_state_payload,
            rail_state_payload=rail_state_payload,
            operator_surface_payload=operator_surface_payload,
            validation_payload=validation_payload,
        )

        payload = build_cortex_ledger_payload(root=root)

        self.assertEqual(["alpha", "zeta"], [item["code"] for item in payload["active_blockers"]])
        self.assertEqual("dirty", payload["worktree_status"])

    def test_markdown_output_includes_next_lane_counts_and_evidence(self) -> None:
        root = self._temp_root(include_run_artifact=True)

        artifact = persist_cortex_ledger_artifact(root=root)
        payload = json.loads(default_ledger_latest_json_path(root).read_text(encoding="utf-8"))
        summary = default_ledger_latest_markdown_path(root).read_text(encoding="utf-8")

        self.assertEqual(json.dumps(payload), json.dumps(artifact.payload))
        self.assertIn("# Cortex Ledger", summary)
        self.assertIn("promote-cortex-receipt-interpretation-contract-wave9", summary)
        self.assertIn("rail status", summary.lower())
        self.assertIn("validation", summary.lower())
        self.assertIn("Evidence Refs", summary)

    def test_missing_required_rail_state_fails_clearly(self) -> None:
        temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(temp_dir.cleanup)
        root = Path(temp_dir.name)
        _write_json(root / "runtime" / "cortex" / "current-state" / "latest.json", self._base_current_state_payload())
        _write_json(root / "runtime" / "cortex" / "context" / "latest.json", self._base_context_payload())
        _write_json(root / "runtime" / "cortex" / "operator-surface" / "latest.json", self._base_operator_surface_payload())
        _write_json(root / "runtime" / "receipts" / "validation" / "stack-validation.latest.json", self._base_validation_payload())
        _write_json(root / "runtime" / "cortex" / "kernel.state-model.seed.v1.json", self.state_payload)
        _write_json(root / "runtime" / "cortex" / "kernel.rule-registry.seed.v1.json", self.rule_payload)

        stdout = io.StringIO()
        stderr = io.StringIO()
        with redirect_stdout(stdout), redirect_stderr(stderr):
            exit_code = main(["--root", str(root), "--quiet"])

        self.assertEqual(2, exit_code)
        self.assertEqual("", stdout.getvalue())
        self.assertIn("Cortex rail-state artifact not found", stderr.getvalue())


if __name__ == "__main__":
    unittest.main()
