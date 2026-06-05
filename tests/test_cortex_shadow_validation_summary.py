from __future__ import annotations

import io
import json
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

from ops._atlas import atlas_root
from ops.cortex.shadow_validation_summary import (
    SHADOW_VALIDATION_SUMMARY_CONTRACT_VERSION,
    build_shadow_validation_summary_payload,
    main,
    persist_shadow_validation_summary_artifact,
)


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


class CortexShadowValidationSummaryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.root = atlas_root()
        cls.registry_payload = json.loads(
            (cls.root / "runtime" / "cortex" / "shadow-agent-registry.seed.v1.json").read_text(encoding="utf-8")
        )

    def _validation_payload(self) -> dict:
        return {
            "generated_at": "2026-06-01T20:00:00+00:00",
            "stack_file": "stack.yaml",
            "stack_root": ".",
            "summary": {
                "critical": 0,
                "error": 0,
                "warning": 493,
                "info": 0,
                "total": 493,
            },
            "findings": [],
        }

    def _seed_temp_root(self, *, registry_payload: dict | None = None, validation_payload: dict | None = None) -> Path:
        temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(temp_dir.cleanup)
        root = Path(temp_dir.name)
        _write_json(
            root / "runtime" / "cortex" / "shadow-agent-registry.seed.v1.json",
            registry_payload or self.registry_payload,
        )
        _write_json(
            root / "runtime" / "receipts" / "validation" / "stack-validation.latest.json",
            validation_payload or self._validation_payload(),
        )
        return root

    def test_payload_consumes_validation_shadow_agent_without_authority(self) -> None:
        root = self._seed_temp_root()

        payload = build_shadow_validation_summary_payload(root=root)

        self.assertEqual(SHADOW_VALIDATION_SUMMARY_CONTRACT_VERSION, payload["contract_version"])
        self.assertEqual("validation-summary-shadow", payload["agent"]["id"])
        self.assertEqual("shadow-consumed", payload["consumption_status"])
        self.assertFalse(payload["authority"]["has_production_authority"])
        self.assertFalse(payload["authority"]["can_waive_findings"])
        self.assertEqual(493, payload["validation_receipt"]["counts"]["warning"])

    def test_persist_writes_json_and_markdown(self) -> None:
        root = self._seed_temp_root()

        artifact = persist_shadow_validation_summary_artifact(root=root)

        payload = json.loads(artifact.artifact_path.read_text(encoding="utf-8"))
        summary = artifact.summary_path.read_text(encoding="utf-8") if artifact.summary_path is not None else ""
        self.assertEqual("validation-summary-shadow", payload["agent"]["id"])
        self.assertIn("# Cortex Shadow Validation Summary", summary)
        self.assertIn("Production authority: `no`", summary)
        self.assertIn("## Source Receipts", summary)

    def test_blocked_registry_agent_fails_clearly(self) -> None:
        registry_payload = json.loads(json.dumps(self.registry_payload))
        for agent in registry_payload["agents"]:
            if agent["id"] == "validation-summary-shadow":
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

    def test_cli_prints_summary(self) -> None:
        root = self._seed_temp_root()
        stdout = io.StringIO()
        stderr = io.StringIO()

        with redirect_stdout(stdout), redirect_stderr(stderr):
            exit_code = main(["--root", str(root)])

        self.assertEqual(0, exit_code)
        self.assertEqual("", stderr.getvalue())
        self.assertIn("Cortex Shadow Validation Summary", stdout.getvalue())


if __name__ == "__main__":
    unittest.main()
