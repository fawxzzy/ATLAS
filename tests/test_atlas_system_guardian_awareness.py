from __future__ import annotations

from copy import deepcopy
import unittest

from ops._atlas import atlas_root
from ops.atlas import cockpit
from ops.atlas.awareness import atlas_status, cockpit_status


class AtlasSystemGuardianAwarenessTests(unittest.TestCase):
    def setUp(self) -> None:
        self.root = atlas_root()

    def test_awareness_and_cockpit_surface_system_guardian_read_model(self) -> None:
        status = atlas_status(root=self.root)
        guardian = status["system_guardian"]

        self.assertEqual("ops/scripts/system-guardian/system-guardian.policy.json", guardian["policy"]["ref"])
        self.assertTrue(guardian["policy"]["hash"])
        self.assertIn(guardian["scheduled_task"]["state"], {"installed", "uninstalled", "unknown"})
        self.assertIn(guardian["kill_switch"]["state"], {"enabled", "disabled"})
        self.assertIn(guardian["last_run"]["mode"], {"observe", "notify", "cleanup", None})
        self.assertIn(
            guardian["last_run"]["result"],
            {"clean", "skipped", "cleanup_applied", "notify_only", "observe_only", "findings_present", "unavailable"},
        )
        self.assertIsInstance(guardian["last_receipt"]["summary_lines"], list)
        self.assertTrue(guardian["last_receipt"]["present"])

        payload = cockpit_status(root=self.root)
        self.assertEqual(guardian, payload["system_guardian"])

        html = cockpit._render_html(payload, refresh_seconds=60)
        self.assertIn("System Guardian Telemetry", html)
        self.assertIn("Latest Receipt Summary", html)
        self.assertNotIn("<button", html.lower())
        self.assertNotIn("<form", html.lower())

    def test_cockpit_renders_cleanly_without_latest_guardian_receipt(self) -> None:
        payload = cockpit_status(root=self.root)
        payload["system_guardian"] = deepcopy(payload["system_guardian"])
        payload["system_guardian"]["last_receipt"] = {
            "present": False,
            "ref": payload["system_guardian"]["last_receipt"]["ref"],
            "summary_lines": [],
        }

        html = cockpit._render_html(payload, refresh_seconds=60)
        self.assertIn("System Guardian Telemetry", html)
        self.assertIn("No latest guardian receipt is available.", html)
        self.assertNotIn("<button", html.lower())
        self.assertNotIn("<form", html.lower())


if __name__ == "__main__":
    unittest.main()
