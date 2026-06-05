from __future__ import annotations

import io
import json
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

from ops._atlas import atlas_root
from ops.cortex.rail_state_reader import (
    build_rail_state_payload,
    default_rail_state_latest_json_path,
    default_rail_state_latest_markdown_path,
    main,
    persist_rail_state_artifact,
)


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


class CortexRailStateReaderTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.root = atlas_root()
        cls.state_payload = json.loads(
            (cls.root / "runtime" / "cortex" / "kernel.state-model.seed.v1.json").read_text(encoding="utf-8")
        )
        cls.rule_payload = json.loads(
            (cls.root / "runtime" / "cortex" / "kernel.rule-registry.seed.v1.json").read_text(encoding="utf-8")
        )
        cls.current_state_payload = json.loads(
            (cls.root / "runtime" / "cortex" / "current-state" / "latest.json").read_text(encoding="utf-8")
        )
        cls.operator_surface_payload = json.loads(
            (cls.root / "runtime" / "cortex" / "operator-surface" / "latest.json").read_text(encoding="utf-8")
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
            "warning": 3,
            "info": 1,
            "total": 4,
        }
        return {
            "generated_at": "2026-05-04T03:00:00+00:00",
            "stack_file": "stack.yaml",
            "stack_root": ".",
            "stack_lock_file": "stack.lock.yaml",
            "summary": summary,
            "repo_ids": ["stack", "fitness", "lifeline"],
            "findings": findings or [],
        }

    def _base_current_state_payload(self) -> dict:
        payload = json.loads(json.dumps(self.current_state_payload))
        payload["generated_at"] = "2026-05-04T03:01:00+00:00"
        payload["branch"] = "codex/cortex-rail-state-reader-wave2"
        payload["head"] = "abc123def456"
        payload["worktree_status"] = "clean"
        payload["changed_files"] = []
        payload["untracked_files"] = []
        payload["validation_counts"] = {
            "critical": 0,
            "error": 0,
            "warning": 3,
            "info": 1,
            "total": 4,
        }
        payload["validation_receipt"] = {
            "generated_at": "2026-05-04T03:00:00+00:00",
            "path": "runtime/receipts/validation/stack-validation.latest.json",
            "counts": payload["validation_counts"],
        }
        payload["active_blockers"] = []
        payload["next_recommended_lane"] = {
            "lane_id": "atlas-cortex-catch-up",
            "owner_layer": "atlas",
            "rationale": "Wave 11 is landed as the latest clean Cortex step. The next bounded lane is an ATLAS root catch-up that records the widened Cortex rail surface, preserves stack-level runtime and receipt posture, and prepares any later owner-side routing without reopening Cortex capability implementation.",
            "blocked_by": [],
            "source_refs": [
                "runtime/cortex/kernel.state-model.seed.v1.json",
                "runtime/cortex/kernel.rule-registry.seed.v1.json",
            ],
        }
        payload["operator_surface_projection"] = {
            "artifact_ref": "runtime/cortex/operator-surface/latest.json",
            "artifact_generated_at": "2026-06-02T02:50:56.638274+00:00",
            "registry_ref": "runtime/cortex/shadow-agent-registry.seed.v1.json",
            "artifact_root": "runtime/cortex/shadow-agent-consumption",
            "shadow_contract_ids": [
                "atlas.cortex.contract.validation-summary-shadow.v1",
                "atlas.cortex.contract.marker-checkpoint-shadow.v1",
                "atlas.cortex.contract.receipt-doctrine-draft-shadow.v1",
            ],
            "blocked_contract_ids": [
                "atlas.cortex.contract.fresh-live-proof-capture-blocked.v1",
                "atlas.cortex.contract.final-deploy-judgment-blocked.v1",
            ],
            "blocked_agent_ids": [
                "fresh-live-proof-capture-blocked",
                "final-deploy-judgment-blocked",
            ],
            "projected_agent_ids": [
                "marker-checkpoint-shadow",
                "receipt-doctrine-draft-shadow",
                "validation-summary-shadow",
            ],
            "projected_contract_ids": [
                "atlas.cortex.contract.marker-checkpoint-shadow.v1",
                "atlas.cortex.contract.receipt-doctrine-draft-shadow.v1",
                "atlas.cortex.contract.validation-summary-shadow.v1",
            ],
            "missing_eligible_agent_ids": [],
            "missing_eligible_contract_ids": [],
            "consumed_artifact_refs": [
                "runtime/cortex/shadow-agent-consumption/marker-checkpoint.latest.json",
                "runtime/cortex/shadow-agent-consumption/receipt-doctrine-draft.latest.json",
                "runtime/cortex/shadow-agent-consumption/validation-summary.latest.json",
            ],
            "projected_agents": [
                {
                    "agent_id": "marker-checkpoint-shadow",
                    "contract_id": "atlas.cortex.contract.marker-checkpoint-shadow.v1",
                    "family_name": "marker checkpoint rendering",
                    "trigger": "ATLAS marker or restart-surface refresh that needs a bounded projection artifact",
                    "admissibility_state": "shadow-only",
                    "authority": {
                        "can_mutate_truth": False,
                        "can_ratchet_markers": False,
                        "has_production_authority": False,
                    },
                }
            ],
            "blocked_agents": [
                {
                    "agent_id": "fresh-live-proof-capture-blocked",
                    "contract_id": "atlas.cortex.contract.fresh-live-proof-capture-blocked.v1",
                    "family_name": "fresh live proof capture through the frozen bridge path",
                    "trigger": "A proof request that still depends on the frozen bridge path",
                    "admissibility_state": "blocked",
                }
            ],
        }
        return payload

    def _temp_root(
        self,
        *,
        current_state_payload: dict,
        validation_payload: dict,
        include_seed: bool = True,
    ) -> Path:
        temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(temp_dir.cleanup)
        root = Path(temp_dir.name)
        _write_json(root / "runtime" / "cortex" / "current-state" / "latest.json", current_state_payload)
        _write_json(root / "runtime" / "receipts" / "validation" / "stack-validation.latest.json", validation_payload)
        if include_seed:
            _write_json(root / "runtime" / "cortex" / "kernel.state-model.seed.v1.json", self.state_payload)
            _write_json(root / "runtime" / "cortex" / "kernel.rule-registry.seed.v1.json", self.rule_payload)
        return root

    def test_clean_current_state_routes_to_seeded_next_lane(self) -> None:
        root = self._temp_root(
            current_state_payload=self._base_current_state_payload(),
            validation_payload=self._base_validation_payload(),
        )

        payload = build_rail_state_payload(root=root)

        self.assertEqual("cortex-mvp", payload["active_rail"])
        self.assertEqual("ready", payload["rail_status"])
        self.assertEqual("atlas-cortex-catch-up", payload["next_recommended_lane"]["lane_id"])
        self.assertEqual([], payload["active_blockers"])
        self.assertEqual([], payload["dirty_lanes"])
        self.assertEqual(
            [
                "marker-checkpoint-shadow",
                "receipt-doctrine-draft-shadow",
                "validation-summary-shadow",
            ],
            payload["operator_surface_projection"]["projected_agent_ids"],
        )
        self.assertEqual(
            [
                "atlas.cortex.contract.marker-checkpoint-shadow.v1",
                "atlas.cortex.contract.receipt-doctrine-draft-shadow.v1",
                "atlas.cortex.contract.validation-summary-shadow.v1",
            ],
            payload["operator_surface_projection"]["projected_contract_ids"],
        )

    def test_validation_blocker_forces_stabilize_stack_validation(self) -> None:
        current_state_payload = self._base_current_state_payload()
        validation_payload = self._base_validation_payload(
            counts={"critical": 0, "error": 1, "warning": 3, "info": 0, "total": 4},
            findings=[
                {
                    "severity": "error",
                    "category": "missing-codex-config",
                    "path": "repos/fawxzzy-foundation",
                    "message": "Expected .codex/config.toml is missing for an active repo.",
                }
            ],
        )
        root = self._temp_root(current_state_payload=current_state_payload, validation_payload=validation_payload)

        payload = build_rail_state_payload(root=root)

        self.assertEqual("blocked", payload["rail_status"])
        self.assertEqual("stabilize-stack-validation", payload["next_recommended_lane"]["lane_id"])
        self.assertEqual(["stabilize-stack-validation"], payload["dirty_lanes"])

    def test_dirty_worktree_forces_stabilize_root_worktree(self) -> None:
        current_state_payload = self._base_current_state_payload()
        current_state_payload["worktree_status"] = "dirty"
        current_state_payload["changed_files"] = ["ops/cortex/rail_state_reader.py"]
        current_state_payload["active_blockers"] = [
            {
                "code": "dirty-worktree",
                "severity": "warning",
                "summary": "Tracked or untracked changes are present in the ATLAS root worktree.",
                "source_kind": "git_state",
                "source_ref": "git status --porcelain=v1 --untracked-files=all",
                "details": {
                    "changed_files": ["ops/cortex/rail_state_reader.py"],
                    "untracked_files": [],
                },
            }
        ]
        current_state_payload["next_recommended_lane"] = {
            "lane_id": "stabilize-root-worktree",
            "owner_layer": "atlas",
            "rationale": "The root worktree is dirty, so current posture should be stabilized before new lane routing or publication decisions.",
            "blocked_by": ["dirty-worktree"],
            "source_refs": ["git status --porcelain=v1 --untracked-files=all"],
        }
        root = self._temp_root(
            current_state_payload=current_state_payload,
            validation_payload=self._base_validation_payload(),
        )

        payload = build_rail_state_payload(root=root)

        self.assertEqual("stabilize-first", payload["rail_status"])
        self.assertEqual("stabilize-root-worktree", payload["next_recommended_lane"]["lane_id"])
        self.assertEqual(["stabilize-root-worktree"], payload["dirty_lanes"])

    def test_missing_current_state_artifact_fails_clearly(self) -> None:
        temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(temp_dir.cleanup)
        root = Path(temp_dir.name)
        _write_json(root / "runtime" / "receipts" / "validation" / "stack-validation.latest.json", self._base_validation_payload())

        stdout = io.StringIO()
        stderr = io.StringIO()
        with redirect_stdout(stdout), redirect_stderr(stderr):
            exit_code = main(["--root", str(root), "--quiet"])

        self.assertEqual(2, exit_code)
        self.assertEqual("", stdout.getvalue())
        self.assertIn("Cortex current-state artifact not found", stderr.getvalue())

    def test_missing_optional_seed_produces_bounded_fallback(self) -> None:
        root = self._temp_root(
            current_state_payload=self._base_current_state_payload(),
            validation_payload=self._base_validation_payload(),
            include_seed=False,
        )

        payload = build_rail_state_payload(root=root)

        self.assertEqual("bounded-fallback", payload["rail_status"])
        self.assertEqual("atlas-cortex-catch-up", payload["next_recommended_lane"]["lane_id"])
        self.assertEqual(
            [
                "runtime/cortex/current-state/latest.json",
                "runtime/receipts/validation/stack-validation.latest.json",
                "runtime/cortex/operator-surface/latest.json",
            ],
            payload["evidence_refs"],
        )

    def test_deterministic_ordering_and_markdown_rendering(self) -> None:
        current_state_payload = self._base_current_state_payload()
        current_state_payload["active_blockers"] = [
            {
                "code": "dirty-worktree",
                "severity": "warning",
                "summary": "Tracked or untracked changes are present in the ATLAS root worktree.",
                "source_kind": "git_state",
                "source_ref": "git status --porcelain=v1 --untracked-files=all",
                "details": {},
            },
            {
                "code": "dirty-worktree",
                "severity": "warning",
                "summary": "Tracked or untracked changes are present in the ATLAS root worktree.",
                "source_kind": "git_state",
                "source_ref": "git status --porcelain=v1 --untracked-files=all",
                "details": {},
            },
        ]
        validation_payload = self._base_validation_payload(
            counts={"critical": 1, "error": 0, "warning": 2, "info": 0, "total": 3},
            findings=[
                {
                    "severity": "critical",
                    "category": "zeta",
                    "path": "repos/example-z",
                    "message": "Zeta blocker.",
                },
                {
                    "severity": "critical",
                    "category": "alpha",
                    "path": "repos/example-a",
                    "message": "Alpha blocker.",
                },
            ],
        )
        root = self._temp_root(current_state_payload=current_state_payload, validation_payload=validation_payload)

        artifact = persist_rail_state_artifact(root=root)
        payload = json.loads(default_rail_state_latest_json_path(root).read_text(encoding="utf-8"))
        summary = default_rail_state_latest_markdown_path(root).read_text(encoding="utf-8")

        blocker_codes = [item["code"] for item in payload["active_blockers"]]
        self.assertEqual(["alpha", "zeta", "dirty-worktree"], blocker_codes)
        self.assertEqual(json.dumps(payload), json.dumps(artifact.payload))
        self.assertIn("# Cortex Rail State", summary)
        self.assertIn("## Active Blockers", summary)
        self.assertIn("## Operator Surface", summary)
        self.assertIn("atlas.cortex.contract.validation-summary-shadow.v1", summary)
        self.assertIn("## Evidence", summary)
        self.assertIn("stabilize-stack-validation", summary)


if __name__ == "__main__":
    unittest.main()

