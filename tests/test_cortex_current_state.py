from __future__ import annotations

import io
import json
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

from ops._atlas import atlas_root
from ops.cortex.current_state import (
    build_current_state_payload,
    default_current_state_latest_json_path,
    default_current_state_latest_markdown_path,
    main,
    persist_current_state_artifact,
)


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


class CortexCurrentStateTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.root = atlas_root()
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
            "warning": 8,
            "info": 0,
            "total": 8,
        }
        return {
            "generated_at": "2026-05-03T23:00:00+00:00",
            "stack_file": "stack.yaml",
            "stack_root": ".",
            "stack_lock_file": "stack.lock.yaml",
            "summary": summary,
            "repo_ids": ["stack", "fitness", "lifeline"],
            "findings": findings or [],
        }

    def _temp_root(self, validation_payload: dict) -> Path:
        temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(temp_dir.cleanup)
        root = Path(temp_dir.name)
        _write_json(root / "runtime" / "receipts" / "validation" / "stack-validation.latest.json", validation_payload)
        _write_json(root / "runtime" / "cortex" / "kernel.state-model.seed.v1.json", self.state_payload)
        _write_json(root / "runtime" / "cortex" / "kernel.rule-registry.seed.v1.json", self.rule_payload)
        return root

    def test_validation_and_git_blockers_override_lane_selection(self) -> None:
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
        root = self._temp_root(validation_payload)

        payload = build_current_state_payload(
            root=root,
            git_state={
                "branch": "codex/atlas-cortex-current-state",
                "head": "abc123def456",
                "worktree_status": "dirty",
                "changed_files": ["ops/cortex/current_state.py"],
                "untracked_files": ["tmp/scratch/current-state.json"],
                "remote_status": {
                    "status": "ahead",
                    "upstream": "origin/codex/atlas-cortex-current-state",
                    "ahead": 2,
                    "behind": 0,
                },
            },
            publication_state={
                "status": "unpublished_ahead_of_origin",
                "published": False,
                "pr_state": "none",
                "notes": ["Waiting for validation stabilization before publication."],
            },
        )

        blocker_codes = {item["code"] for item in payload["active_blockers"]}
        self.assertEqual("codex/atlas-cortex-current-state", payload["branch"])
        self.assertEqual("abc123def456", payload["head"])
        self.assertIn("missing-codex-config", blocker_codes)
        self.assertIn("dirty-worktree", blocker_codes)
        self.assertEqual("stabilize-stack-validation", payload["next_recommended_lane"]["lane_id"])
        self.assertEqual("cortex-receipt-interpretation-contract-v0-1", payload["latest_clean_step"]["step_id"])
        self.assertEqual("unpublished_ahead_of_origin", payload["remote_publication_state"]["status"])

    def test_clean_inputs_route_to_seeded_cortex_lane(self) -> None:
        validation_payload = self._base_validation_payload(
            counts={"critical": 0, "error": 0, "warning": 2, "info": 0, "total": 2},
            findings=[
                {
                    "severity": "warning",
                    "category": "missing-cortex-adjacent-snapshot",
                    "path": "repos/cortex",
                    "message": "Configured Cortex adjacent snapshot path does not exist.",
                }
            ],
        )
        root = self._temp_root(validation_payload)

        payload = build_current_state_payload(
            root=root,
            git_state={
                "branch": "codex/atlas-cortex-current-state",
                "head": "def456abc123",
                "worktree_status": "clean",
                "changed_files": [],
                "untracked_files": [],
                "remote_status": {
                    "status": "in_sync",
                    "upstream": "origin/codex/atlas-cortex-current-state",
                    "ahead": 0,
                    "behind": 0,
                },
            },
        )

        self.assertEqual([], payload["active_blockers"])
        self.assertEqual("promote-cortex-receipt-interpretation-stack-consumption-wave10", payload["next_recommended_lane"]["lane_id"])
        self.assertEqual("cortex", payload["next_recommended_lane"]["owner_layer"])
        self.assertEqual("cortex-receipt-interpretation-contract-v0-1", payload["latest_clean_step"]["step_id"])
        self.assertEqual("in_sync", payload["remote_publication_state"]["status"])

    def test_persist_writes_latest_json_and_markdown(self) -> None:
        validation_payload = self._base_validation_payload(
            counts={"critical": 0, "error": 0, "warning": 1, "info": 0, "total": 1},
        )
        root = self._temp_root(validation_payload)

        artifact = persist_current_state_artifact(
            root=root,
            git_state={
                "branch": "codex/atlas-cortex-current-state",
                "head": "789abc123def",
                "worktree_status": "clean",
                "changed_files": [],
                "untracked_files": [],
                "remote_status": {
                    "status": "in_sync",
                    "upstream": "origin/codex/atlas-cortex-current-state",
                    "ahead": 0,
                    "behind": 0,
                },
            },
        )

        payload = json.loads(default_current_state_latest_json_path(root).read_text(encoding="utf-8"))
        summary = default_current_state_latest_markdown_path(root).read_text(encoding="utf-8")

        self.assertEqual(artifact.payload["head"], payload["head"])
        self.assertEqual("atlas.cortex.current-state.v1", payload["contract_version"])
        self.assertIn("# Cortex Current State", summary)
        self.assertIn("promote-cortex-receipt-interpretation-stack-consumption-wave10", summary)

    def test_cli_fails_clearly_when_validation_receipt_is_missing(self) -> None:
        temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(temp_dir.cleanup)
        root = Path(temp_dir.name)
        _write_json(root / "runtime" / "cortex" / "kernel.state-model.seed.v1.json", self.state_payload)
        _write_json(root / "runtime" / "cortex" / "kernel.rule-registry.seed.v1.json", self.rule_payload)

        stdout = io.StringIO()
        stderr = io.StringIO()
        with redirect_stdout(stdout), redirect_stderr(stderr):
            exit_code = main(["--root", str(root), "--quiet"])

        self.assertEqual(2, exit_code)
        self.assertEqual("", stdout.getvalue())
        self.assertIn("Stack validation receipt not found", stderr.getvalue())


if __name__ == "__main__":
    unittest.main()

