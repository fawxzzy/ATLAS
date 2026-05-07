from __future__ import annotations

import io
import json
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

from ops._atlas import atlas_root
from ops.cortex.operator_surface import (
    build_operator_surface_payload,
    default_operator_surface_latest_json_path,
    default_operator_surface_latest_markdown_path,
    main,
    persist_operator_surface_artifact,
)


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


class CortexOperatorSurfaceTests(unittest.TestCase):
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
            "generated_at": "2026-05-06T20:00:00+00:00",
            "stack_file": "stack.yaml",
            "stack_root": ".",
            "stack_lock_file": "stack.lock.yaml",
            "summary": summary,
            "repo_ids": ["stack", "fitness", "lifeline"],
            "findings": findings or [],
        }

    def _base_current_state_payload(self) -> dict:
        payload = json.loads(json.dumps(self.current_state_payload))
        payload["generated_at"] = "2026-05-06T20:01:00+00:00"
        payload["branch"] = "codex/cortex-operator-surface-wave4"
        payload["head"] = "abc123def456"
        payload["worktree_status"] = "clean"
        payload["changed_files"] = []
        payload["untracked_files"] = []
        payload["remote_publication_state"] = {
            "status": "in_sync",
            "branch": "codex/cortex-operator-surface-wave4",
            "head": "abc123def456",
            "published": True,
            "upstream": "origin/codex/cortex-operator-surface-wave4",
            "pr_state": "open",
            "pr_url": "https://example.invalid/pr/9",
            "notes": [],
        }
        payload["validation_counts"] = {
            "critical": 0,
            "error": 0,
            "warning": 4,
            "info": 1,
            "total": 5,
        }
        payload["validation_receipt"] = {
            "generated_at": "2026-05-06T20:00:00+00:00",
            "path": "runtime/receipts/validation/stack-validation.latest.json",
            "counts": payload["validation_counts"],
        }
        payload["active_blockers"] = []
        payload["next_recommended_lane"] = {
            "lane_id": "pilot-cortex-worker-prompt-stack-consumption-wave7",
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
        payload["generated_at"] = "2026-05-06T20:02:00+00:00"
        payload["rail_status"] = "ready"
        payload["active_blockers"] = []
        payload["dirty_lanes"] = ["cortex-worker-prompt-stack-consumption-pilot-v0-1"]
        payload["validation_posture"] = {
            "status": "ambient-debt-only",
            "counts": {
                "critical": 0,
                "error": 0,
                "warning": 4,
                "info": 1,
                "total": 5,
            },
            "receipt_generated_at": "2026-05-06T20:00:00+00:00",
            "receipt_path": "runtime/receipts/validation/stack-validation.latest.json",
        }
        payload["next_recommended_lane"] = {
            "lane_id": "pilot-cortex-worker-prompt-stack-consumption-wave7",
            "owner_layer": "cortex",
            "rationale": "The canonical ledger is landed, but Cortex still needs one promoted worker-prompt artifact contract that _stack can consume while planner, context, proof, receipt-draft, and final receipt stay separate and linked by refs and digests.",
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
        payload["generated_at"] = "2026-05-06T20:03:00+00:00"
        payload["packet_id"] = "context-pilot-cortex-worker-prompt-stack-consumption-wave7"
        payload["context_summary"] = (
            "Cortex context packet for pilot-cortex-worker-prompt-stack-consumption-wave7 derived from explicit current-state, "
            "rail-state, validation, and seed artifacts."
        )
        payload["posture_snapshot"]["branch"] = "codex/cortex-operator-surface-wave4"
        payload["posture_snapshot"]["head"] = "abc123def456"
        payload["posture_snapshot"]["worktree_status"] = "clean"
        payload["posture_snapshot"]["active_blocker_count"] = 0
        payload["posture_snapshot"]["dirty_lanes"] = ["cortex-worker-prompt-stack-consumption-pilot-v0-1"]
        payload["posture_snapshot"]["validation_status"] = "ambient-debt-only"
        payload["posture_snapshot"]["validation_counts"] = {
            "critical": 0,
            "error": 0,
            "warning": 4,
            "info": 1,
            "total": 5,
        }
        payload["task_frame"]["lane_id"] = "pilot-cortex-worker-prompt-stack-consumption-wave7"
        payload["task_frame"]["owner_layer"] = "cortex"
        payload["task_frame"]["title"] = "Promote the Cortex worker-prompt contract."
        payload["task_frame"]["status"] = "ready"
        payload["task_frame"]["rationale"] = (
            "The canonical ledger is landed, but Cortex still needs one promoted worker-prompt artifact contract that "
            "_stack can consume while planner, context, proof, receipt-draft, and final receipt stay separate and "
            "linked by refs and digests."
        )
        payload["task_frame"]["blocked_by"] = []
        payload["task_frame"]["ready_to_execute"] = True
        return payload

    def _temp_root(
        self,
        *,
        current_state_payload: dict | None = None,
        rail_state_payload: dict | None = None,
        context_payload: dict | None = None,
        validation_payload: dict | None = None,
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
            root / "runtime" / "receipts" / "validation" / "stack-validation.latest.json",
            validation_payload or self._base_validation_payload(),
        )
        _write_json(root / "runtime" / "cortex" / "kernel.state-model.seed.v1.json", self.state_payload)
        _write_json(root / "runtime" / "cortex" / "kernel.rule-registry.seed.v1.json", self.rule_payload)
        return root

    def test_clean_posture_joins_existing_artifacts(self) -> None:
        root = self._temp_root()

        payload = build_operator_surface_payload(root=root)

        self.assertEqual("atlas.cortex.operator-surface.v1", payload["contract_version"])
        self.assertEqual("cortex-mvp", payload["active_rail"])
        self.assertEqual("ready", payload["rail_status"])
        self.assertEqual("pilot-cortex-worker-prompt-stack-consumption-wave7", payload["next_recommended_lane"]["lane_id"])
        self.assertEqual("context-pilot-cortex-worker-prompt-stack-consumption-wave7", payload["context_packet_id"])
        self.assertEqual([], payload["active_blockers"])
        self.assertEqual("in_sync", payload["publication_posture"]["remote_status"])
        self.assertEqual(
            [
                "runtime/cortex/current-state/latest.json",
                "runtime/cortex/rail-state/latest.json",
                "runtime/receipts/validation/stack-validation.latest.json",
                "runtime/cortex/kernel.state-model.seed.v1.json",
                "runtime/cortex/kernel.rule-registry.seed.v1.json",
            ],
            payload["top_evidence_refs"][:5],
        )
        json.dumps(payload, sort_keys=True)

    def test_validation_blocker_is_reflected_without_recomputing_lane(self) -> None:
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
            "rationale": "Blocking stack-validation findings are active, so the next lane must stabilize validation.",
            "blocked_by": ["missing-codex-config"],
            "source_refs": ["runtime/receipts/validation/stack-validation.latest.json"],
        }
        rail_state_payload = self._base_rail_state_payload()
        rail_state_payload["rail_status"] = "blocked"
        rail_state_payload["active_blockers"] = current_state_payload["active_blockers"]
        rail_state_payload["next_recommended_lane"] = current_state_payload["next_recommended_lane"]
        rail_state_payload["dirty_lanes"] = ["stabilize-stack-validation", "cortex-worker-prompt-stack-consumption-pilot-v0-1"]
        context_payload = self._base_context_payload()
        context_payload["task_frame"]["lane_id"] = "stabilize-stack-validation"
        context_payload["task_frame"]["owner_layer"] = "atlas"
        context_payload["task_frame"]["status"] = "blocked"
        context_payload["task_frame"]["ready_to_execute"] = False
        context_payload["task_frame"]["blocked_by"] = ["missing-codex-config"]
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
            context_payload=context_payload,
            validation_payload=validation_payload,
        )

        payload = build_operator_surface_payload(root=root)

        self.assertEqual("blocked", payload["rail_status"])
        self.assertEqual("stabilize-stack-validation", payload["next_recommended_lane"]["lane_id"])
        self.assertEqual(["missing-codex-config"], payload["task_frame_summary"]["blocked_by"])
        self.assertEqual("blocked", payload["task_frame_summary"]["status"])

    def test_deterministic_ordering_and_markdown_rendering(self) -> None:
        rail_state_payload = self._base_rail_state_payload()
        rail_state_payload["active_blockers"] = [
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
            {
                "code": "alpha",
                "severity": "critical",
                "summary": "Alpha blocker.",
                "source_kind": "validation_receipt",
                "source_ref": "runtime/receipts/validation/stack-validation.latest.json",
                "details": {"path": "repos/example-a"},
            },
        ]
        rail_state_payload["rail_status"] = "blocked"
        rail_state_payload["next_recommended_lane"] = {
            "lane_id": "stabilize-stack-validation",
            "owner_layer": "atlas",
            "rationale": "Blocking validation findings must be stabilized first.",
            "blocked_by": ["alpha", "zeta"],
            "source_refs": ["runtime/receipts/validation/stack-validation.latest.json"],
        }
        context_payload = self._base_context_payload()
        context_payload["task_frame"]["lane_id"] = "stabilize-stack-validation"
        context_payload["task_frame"]["owner_layer"] = "atlas"
        context_payload["task_frame"]["status"] = "blocked"
        context_payload["task_frame"]["ready_to_execute"] = False
        context_payload["task_frame"]["blocked_by"] = ["alpha", "zeta"]
        root = self._temp_root(rail_state_payload=rail_state_payload, context_payload=context_payload)

        artifact = persist_operator_surface_artifact(root=root)
        payload = json.loads(default_operator_surface_latest_json_path(root).read_text(encoding="utf-8"))
        summary = default_operator_surface_latest_markdown_path(root).read_text(encoding="utf-8")

        blocker_codes = [item["code"] for item in payload["active_blockers"]]
        self.assertEqual(["alpha", "zeta"], blocker_codes)
        self.assertEqual(json.dumps(payload), json.dumps(artifact.payload))
        self.assertIn("# Cortex Operator Surface", summary)
        self.assertIn("## Task Frame", summary)
        self.assertIn("## Top Evidence", summary)
        self.assertIn("stabilize-stack-validation", summary)

    def test_cli_fails_clearly_when_context_is_missing(self) -> None:
        temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(temp_dir.cleanup)
        root = Path(temp_dir.name)
        _write_json(root / "runtime" / "cortex" / "current-state" / "latest.json", self._base_current_state_payload())
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
        self.assertIn("Cortex context artifact not found", stderr.getvalue())


if __name__ == "__main__":
    unittest.main()
