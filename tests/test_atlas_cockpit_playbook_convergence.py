from __future__ import annotations

import unittest

from ops._atlas import atlas_root
from ops.atlas import cockpit
from ops.atlas.awareness import cockpit_status


class AtlasCockpitPlaybookConvergenceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.root = atlas_root()

    def test_cockpit_payload_and_html_include_new_read_only_sections(self) -> None:
        payload = cockpit_status(root=self.root)

        self.assertIn("playbook_convergence", payload)
        self.assertIn("continuity", payload)

        html = cockpit._render_html(payload, refresh_seconds=60)
        self.assertIn("Playbook Convergence", html)
        self.assertIn("Continuity Coverage", html)
        self.assertNotIn("<button", html.lower())
        self.assertNotIn("<form", html.lower())


if __name__ == "__main__":
    unittest.main()
