from __future__ import annotations

import io
import json
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

from ops._atlas import atlas_root
from ops.cortex.shadow_receipt_doctrine_draft import (
    SHADOW_RECEIPT_DOCTRINE_DRAFT_CONTRACT_VERSION,
    build_shadow_receipt_doctrine_draft_payload,
    main,
    persist_shadow_receipt_doctrine_draft_artifact,
)


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def _write_text(path: Path, value: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(value, encoding="utf-8")


class CortexShadowReceiptDoctrineDraftTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.root = atlas_root()
        cls.registry_payload = json.loads(
            (cls.root / "runtime" / "cortex" / "shadow-agent-registry.seed.v1.json").read_text(encoding="utf-8")
        )

    def _playbook_text(self) -> str:
        return """# Playbook Notes

## 2026-06-01 - Example doctrine block

- Rule: `Example Rule`.
- Pattern: `Example Pattern`.
- Failure Mode: `Example Failure`.
"""

    def _failure_modes_text(self) -> str:
        return """# Failures

## 15. Manual Toggle Drift
## 16. Automation Claim Inflation
## 17. Agent Premature Entanglement
"""

    def _receipt_text(self) -> str:
        return """# Receipt

- `validation-summary-shadow`
- `marker-checkpoint-shadow`
- `receipt-doctrine-draft-shadow`
"""

    def _seed_temp_root(
        self,
        *,
        registry_payload: dict | None = None,
        playbook_text: str | None = None,
        failure_modes_text: str | None = None,
        receipt_text: str | None = None,
    ) -> Path:
        temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(temp_dir.cleanup)
        root = Path(temp_dir.name)
        _write_json(
            root / "runtime" / "cortex" / "shadow-agent-registry.seed.v1.json",
            registry_payload or self.registry_payload,
        )
        _write_text(root / "docs" / "PLAYBOOK_NOTES.md", playbook_text or self._playbook_text())
        _write_text(
            root / "docs" / "atlas-book" / "10-failure-modes-and-recovery.md",
            failure_modes_text or self._failure_modes_text(),
        )
        _write_text(
            root / "docs" / "ops" / "AI-REPETITION-TO-AUTOMATION-PIPELINE-AUTOMATION-CANDIDATE-THRESHOLD-PASS-1-2026-06-01.md",
            receipt_text or self._receipt_text(),
        )
        return root

    def test_payload_consumes_draft_shadow_without_authority(self) -> None:
        root = self._seed_temp_root()

        payload = build_shadow_receipt_doctrine_draft_payload(root=root)

        self.assertEqual(SHADOW_RECEIPT_DOCTRINE_DRAFT_CONTRACT_VERSION, payload["contract_version"])
        self.assertEqual("receipt-doctrine-draft-shadow", payload["agent"]["id"])
        self.assertEqual("shadow-consumed", payload["consumption_status"])
        self.assertFalse(payload["authority"]["has_production_authority"])
        self.assertFalse(payload["authority"]["can_admit_doctrine"])
        self.assertIn("Example Rule", payload["draft_payload"]["candidate_rules"])

    def test_persist_writes_json_and_markdown(self) -> None:
        root = self._seed_temp_root()

        artifact = persist_shadow_receipt_doctrine_draft_artifact(root=root)

        payload = json.loads(artifact.artifact_path.read_text(encoding="utf-8"))
        summary = artifact.summary_path.read_text(encoding="utf-8") if artifact.summary_path is not None else ""
        self.assertEqual("receipt-doctrine-draft-shadow", payload["agent"]["id"])
        self.assertIn("# Cortex Shadow Receipt/Doctrine Draft", summary)
        self.assertIn("Can admit doctrine: `no`", summary)
        self.assertIn("## Receipt Focus Tokens", summary)

    def test_missing_doctrine_entries_fail_clearly(self) -> None:
        root = self._seed_temp_root(playbook_text="# Playbook Notes\n\n## Empty\n\n- nothing useful\n")

        stdout = io.StringIO()
        stderr = io.StringIO()
        with redirect_stdout(stdout), redirect_stderr(stderr):
            exit_code = main(["--root", str(root), "--quiet"])

        self.assertEqual(2, exit_code)
        self.assertEqual("", stdout.getvalue())
        self.assertIn("did not yield any draftable doctrine entries", stderr.getvalue())

    def test_blocked_registry_agent_fails_clearly(self) -> None:
        registry_payload = json.loads(json.dumps(self.registry_payload))
        for agent in registry_payload["agents"]:
            if agent["id"] == "receipt-doctrine-draft-shadow":
                agent["stage"] = "blocked"
                agent["admissibility_state"] = "blocked"
                agent["runnable"] = False
                agent["blocked_reason"] = "forced test block"
        root = self._seed_temp_root(registry_payload=registry_payload)

        stdout = io.StringIO()
        stderr = io.StringIO()
        with redirect_stdout(stdout), redirect_stderr(stderr):
            exit_code = main(["--root", str(root), "--quiet"])

        self.assertEqual(2, exit_code)
        self.assertEqual("", stdout.getvalue())
        self.assertIn("is not eligible for consumption", stderr.getvalue())


if __name__ == "__main__":
    unittest.main()
