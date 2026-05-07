from __future__ import annotations

import io
import json
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

from ops._atlas import atlas_root
from ops.cortex.context_assembler import (
    build_context_packet_payload,
    default_context_latest_json_path,
    default_context_latest_markdown_path,
    main,
    persist_context_packet_artifact,
)


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


class CortexContextAssemblerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.root = atlas_root()
        cls.current_state_payload = json.loads(
            (cls.root / "runtime" / "cortex" / "current-state" / "latest.json").read_text(encoding="utf-8")
        )
        cls.rail_state_payload = json.loads(
            (cls.root / "runtime" / "cortex" / "rail-state" / "latest.json").read_text(encoding="utf-8")
        )
        cls.state_payload = json.loads(
            (cls.root / "runtime" / "cortex" / "kernel.state-model.seed.v1.json").read_text(encoding="utf-8")
        )
        cls.rule_payload = json.loads(
            (cls.root / "runtime" / "cortex" / "kernel.rule-registry.seed.v1.json").read_text(encoding="utf-8")
        )

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
            "generated_at": "2026-05-05T23:50:00+00:00",
            "stack_file": "stack.yaml",
            "stack_root": ".",
            "stack_lock_file": "stack.lock.yaml",
            "summary": summary,
            "repo_ids": ["stack", "fitness", "lifeline"],
            "findings": findings or [],
        }

    def _base_current_state_payload(self) -> dict:
        payload = json.loads(json.dumps(self.current_state_payload))
        payload["generated_at"] = "2026-05-05T23:51:00+00:00"
        payload["branch"] = "codex/cortex-context-assembler-wave3"
        payload["head"] = "abc123def456"
        payload["worktree_status"] = "clean"
        payload["changed_files"] = []
        payload["untracked_files"] = []
        payload["validation_counts"] = {
            "critical": 0,
            "error": 0,
            "warning": 4,
            "info": 1,
            "total": 5,
        }
        payload["validation_receipt"] = {
            "generated_at": "2026-05-05T23:50:00+00:00",
            "path": "runtime/receipts/validation/stack-validation.latest.json",
            "counts": payload["validation_counts"],
        }
        payload["active_blockers"] = []
        payload["next_recommended_lane"] = {
            "lane_id": "promote-cortex-stack-consumer-default-routing-wave8",
            "owner_layer": "cortex",
            "rationale": "The canonical ledger is landed, but Cortex still needs one promoted worker-prompt artifact contract that _stack can consume while planner, context, proof, receipt-draft, and final receipt stay separate and linked by refs and digests.",
            "blocked_by": [],
            "source_refs": [
                "runtime/cortex/kernel.state-model.seed.v1.json",
                "runtime/cortex/kernel.rule-registry.seed.v1.json",
            ],
        }
        return payload

    def _base_rail_state_payload(self) -> dict:
        payload = json.loads(json.dumps(self.rail_state_payload))
        payload["generated_at"] = "2026-05-05T23:52:00+00:00"
        payload["rail_status"] = "ready"
        payload["active_blockers"] = []
        payload["dirty_lanes"] = ["cortex-stack-consumer-default-routing-v0-1"]
        payload["validation_posture"] = {
            "status": "ambient-debt-only",
            "counts": {
                "critical": 0,
                "error": 0,
                "warning": 4,
                "info": 1,
                "total": 5,
            },
            "receipt_generated_at": "2026-05-05T23:50:00+00:00",
            "receipt_path": "runtime/receipts/validation/stack-validation.latest.json",
        }
        payload["next_recommended_lane"] = {
            "lane_id": "promote-cortex-stack-consumer-default-routing-wave8",
            "owner_layer": "cortex",
            "rationale": "The canonical ledger is landed, but Cortex still needs one promoted worker-prompt artifact contract that _stack can consume while planner, context, proof, receipt-draft, and final receipt stay separate and linked by refs and digests.",
            "blocked_by": [],
            "source_refs": [
                "runtime/cortex/current-state/latest.json",
                "runtime/cortex/kernel.state-model.seed.v1.json",
                "runtime/cortex/kernel.rule-registry.seed.v1.json",
            ],
        }
        payload["seeded_rail_state"]["next_action"]["action_id"] = "promote-cortex-stack-consumer-default-routing-wave8"
        payload["seeded_rail_state"]["next_action"]["owner_layer"] = "cortex"
        return payload

    def _temp_root(
        self,
        *,
        current_state_payload: dict | None = None,
        rail_state_payload: dict | None = None,
        validation_payload: dict | None = None,
    ) -> Path:
        temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(temp_dir.cleanup)
        root = Path(temp_dir.name)
        _write_json(root / "runtime" / "cortex" / "current-state" / "latest.json", current_state_payload or self._base_current_state_payload())
        _write_json(root / "runtime" / "cortex" / "rail-state" / "latest.json", rail_state_payload or self._base_rail_state_payload())
        _write_json(root / "runtime" / "receipts" / "validation" / "stack-validation.latest.json", validation_payload or self._base_validation_payload())
        _write_json(root / "runtime" / "cortex" / "kernel.state-model.seed.v1.json", self.state_payload)
        _write_json(root / "runtime" / "cortex" / "kernel.rule-registry.seed.v1.json", self.rule_payload)
        return root

    def test_clean_posture_assembles_seeded_lane_packet(self) -> None:
        root = self._temp_root()

        payload = build_context_packet_payload(root=root)

        self.assertEqual("atlas.cortex.context-packet.v1", payload["contract_version"])
        self.assertEqual("context-promote-cortex-stack-consumer-default-routing-wave8", payload["packet_id"])
        self.assertEqual("promote-cortex-stack-consumer-default-routing-wave8", payload["task_frame"]["lane_id"])
        self.assertTrue(payload["task_frame"]["ready_to_execute"])
        self.assertIsNone(payload["deferred_lane"])
        self.assertEqual("cortex-mvp", payload["active_rail"])
        self.assertEqual(
            [
                "runtime/cortex/current-state/latest.json",
                "runtime/cortex/rail-state/latest.json",
                "runtime/receipts/validation/stack-validation.latest.json",
                "runtime/cortex/kernel.state-model.seed.v1.json",
                "runtime/cortex/kernel.rule-registry.seed.v1.json",
            ],
            payload["source_refs"],
        )
        self.assertTrue(payload["rule_highlights"])
        json.dumps(payload, sort_keys=True)

    def test_validation_blocker_switches_immediate_lane_and_preserves_deferred_lane(self) -> None:
        current_state_payload = self._base_current_state_payload()
        current_state_payload["active_blockers"] = [
            {
                "code": "missing-codex-config",
                "severity": "error",
                "summary": "Expected .codex/config.toml is missing for an active repo.",
                "source_kind": "validation_receipt",
                "source_ref": "runtime/receipts/validation/stack-validation.latest.json",
                "details": {"path": "repos/fawxzzy-foundation"},
            }
        ]
        current_state_payload["next_recommended_lane"] = {
            "lane_id": "stabilize-stack-validation",
            "owner_layer": "atlas",
            "rationale": "Blocking stack-validation findings are active, so the next lane must stabilize validation before new roadmap work proceeds.",
            "blocked_by": ["missing-codex-config"],
            "source_refs": ["runtime/receipts/validation/stack-validation.latest.json"],
        }
        rail_state_payload = self._base_rail_state_payload()
        rail_state_payload["rail_status"] = "blocked"
        rail_state_payload["active_blockers"] = current_state_payload["active_blockers"]
        rail_state_payload["next_recommended_lane"] = current_state_payload["next_recommended_lane"]
        validation_payload = self._base_validation_payload(
            counts={"critical": 0, "error": 1, "warning": 4, "info": 0, "total": 5},
            findings=[
                {
                    "severity": "error",
                    "category": "missing-codex-config",
                    "path": "repos/fawxzzy-foundation",
                    "message": "Expected .codex/config.toml is missing for an active repo.",
                }
            ],
        )
        root = self._temp_root(
            current_state_payload=current_state_payload,
            rail_state_payload=rail_state_payload,
            validation_payload=validation_payload,
        )

        payload = build_context_packet_payload(root=root)

        self.assertEqual("stabilize-stack-validation", payload["task_frame"]["lane_id"])
        self.assertEqual("blocked", payload["task_frame"]["status"])
        self.assertEqual(["missing-codex-config"], payload["task_frame"]["blocked_by"])
        self.assertIsNotNone(payload["deferred_lane"])
        self.assertEqual("promote-cortex-stack-consumer-default-routing-wave8", payload["deferred_lane"]["lane_id"])

    def test_dirty_worktree_switches_immediate_lane(self) -> None:
        current_state_payload = self._base_current_state_payload()
        current_state_payload["worktree_status"] = "dirty"
        current_state_payload["changed_files"] = ["ops/cortex/context_assembler.py"]
        current_state_payload["active_blockers"] = [
            {
                "code": "dirty-worktree",
                "severity": "error",
                "summary": "The ATLAS root worktree is dirty and should be stabilized before new lane claims or publication decisions.",
                "source_kind": "git_status",
                "source_ref": "git status --porcelain=v1 --untracked-files=all",
                "details": {"changed_files": ["ops/cortex/context_assembler.py"], "untracked_files": []},
            }
        ]
        rail_state_payload = self._base_rail_state_payload()
        rail_state_payload["rail_status"] = "stabilize-first"
        rail_state_payload["active_blockers"] = current_state_payload["active_blockers"]
        rail_state_payload["next_recommended_lane"] = {
            "lane_id": "stabilize-root-worktree",
            "owner_layer": "atlas",
            "rationale": "The root worktree is dirty, so the rail must stabilize the checkout before advancing the next Cortex lane.",
            "blocked_by": ["dirty-worktree"],
            "source_refs": ["git status --porcelain=v1 --untracked-files=all"],
        }
        root = self._temp_root(current_state_payload=current_state_payload, rail_state_payload=rail_state_payload)

        payload = build_context_packet_payload(root=root)

        self.assertEqual("stabilize-root-worktree", payload["task_frame"]["lane_id"])
        self.assertEqual("stabilize-first", payload["task_frame"]["status"])
        self.assertFalse(payload["task_frame"]["ready_to_execute"])
        self.assertEqual("promote-cortex-stack-consumer-default-routing-wave8", payload["deferred_lane"]["lane_id"])

    def test_persist_writes_latest_json_and_markdown(self) -> None:
        root = self._temp_root()

        artifact = persist_context_packet_artifact(root=root)
        payload = json.loads(default_context_latest_json_path(root).read_text(encoding="utf-8"))
        summary = default_context_latest_markdown_path(root).read_text(encoding="utf-8")

        self.assertEqual(artifact.payload["packet_id"], payload["packet_id"])
        self.assertIn("# Cortex Context Packet", summary)
        self.assertIn("## Objective", summary)
        self.assertIn("promote-cortex-stack-consumer-default-routing-wave8", summary)

    def test_cli_fails_clearly_when_current_state_is_missing(self) -> None:
        temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(temp_dir.cleanup)
        root = Path(temp_dir.name)
        _write_json(root / "runtime" / "cortex" / "rail-state" / "latest.json", self._base_rail_state_payload())
        _write_json(root / "runtime" / "receipts" / "validation" / "stack-validation.latest.json", self._base_validation_payload())
        _write_json(root / "runtime" / "cortex" / "kernel.state-model.seed.v1.json", self.state_payload)
        _write_json(root / "runtime" / "cortex" / "kernel.rule-registry.seed.v1.json", self.rule_payload)

        stdout = io.StringIO()
        stderr = io.StringIO()
        with redirect_stdout(stdout), redirect_stderr(stderr):
            exit_code = main(["--root", str(root), "--quiet"])

        self.assertEqual(2, exit_code)
        self.assertEqual("", stdout.getvalue())
        self.assertIn("Cortex current-state artifact not found", stderr.getvalue())


if __name__ == "__main__":
    unittest.main()
