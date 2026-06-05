from __future__ import annotations

import io
import json
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

from ops._atlas import atlas_root
from ops.cortex.shadow_marker_checkpoint import (
    SHADOW_MARKER_CHECKPOINT_CONTRACT_VERSION,
    build_shadow_marker_checkpoint_payload,
    main,
    persist_shadow_marker_checkpoint_artifact,
)


def _write_text(path: Path, value: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(value, encoding="utf-8")


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


class CortexShadowMarkerCheckpointTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.root = atlas_root()
        cls.registry_payload = json.loads(
            (cls.root / "runtime" / "cortex" / "shadow-agent-registry.seed.v1.json").read_text(encoding="utf-8")
        )

    def _marker_surface_text(self) -> str:
        return """# Lanes And Markers

## Active Front-Page Marker Table

- _stack Readiness: `70%`
- Playbook Everywhere + Cortex Interface: `21%`

## Supporting Open Markers

- Cortex Readiness: `35%`
- Feedback Loop Readiness: `42%`
"""

    def _restart_surface_text(self) -> str:
        return """# Restart

- the exact next lane now routes to `Cortex Readiness`: the next honest leverage is a second bounded shadow-consumption proof
"""

    def _seed_temp_root(
        self,
        *,
        registry_payload: dict | None = None,
        marker_surface_text: str | None = None,
        restart_surface_text: str | None = None,
    ) -> Path:
        temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(temp_dir.cleanup)
        root = Path(temp_dir.name)
        _write_json(
            root / "runtime" / "cortex" / "shadow-agent-registry.seed.v1.json",
            registry_payload or self.registry_payload,
        )
        _write_text(
            root / "docs" / "atlas-book" / "02-lanes-and-markers.md",
            marker_surface_text or self._marker_surface_text(),
        )
        _write_text(
            root / "docs" / "atlas-book" / "12-restart-and-handoff-guide.md",
            restart_surface_text or self._restart_surface_text(),
        )
        return root

    def test_payload_consumes_marker_checkpoint_without_authority(self) -> None:
        root = self._seed_temp_root()

        payload = build_shadow_marker_checkpoint_payload(root=root)

        self.assertEqual(SHADOW_MARKER_CHECKPOINT_CONTRACT_VERSION, payload["contract_version"])
        self.assertEqual("marker-checkpoint-shadow", payload["agent"]["id"])
        self.assertEqual("shadow-consumed", payload["consumption_status"])
        self.assertFalse(payload["authority"]["has_production_authority"])
        self.assertFalse(payload["authority"]["can_ratchet_markers"])
        self.assertEqual("Cortex Readiness", payload["marker_checkpoint"]["next_lane_route"])

    def test_persist_writes_json_and_markdown(self) -> None:
        root = self._seed_temp_root()

        artifact = persist_shadow_marker_checkpoint_artifact(root=root)

        payload = json.loads(artifact.artifact_path.read_text(encoding="utf-8"))
        summary = artifact.summary_path.read_text(encoding="utf-8") if artifact.summary_path is not None else ""
        self.assertEqual("marker-checkpoint-shadow", payload["agent"]["id"])
        self.assertIn("# Cortex Shadow Marker Checkpoint", summary)
        self.assertIn("Can ratchet markers: `no`", summary)
        self.assertIn("## Active Front-Page Markers", summary)

    def test_missing_next_lane_fails_clearly(self) -> None:
        root = self._seed_temp_root(restart_surface_text="# Restart\n\n- no lane route here\n")

        stdout = io.StringIO()
        stderr = io.StringIO()
        with redirect_stdout(stdout), redirect_stderr(stderr):
            exit_code = main(["--root", str(root), "--quiet"])

        self.assertEqual(2, exit_code)
        self.assertEqual("", stdout.getvalue())
        self.assertIn("does not contain the expected next-lane route line", stderr.getvalue())

    def test_blocked_registry_agent_fails_clearly(self) -> None:
        registry_payload = json.loads(json.dumps(self.registry_payload))
        for agent in registry_payload["agents"]:
            if agent["id"] == "marker-checkpoint-shadow":
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
