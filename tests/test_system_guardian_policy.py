from __future__ import annotations

import json
import unittest
from pathlib import Path


class SystemGuardianPolicyTests(unittest.TestCase):
    def setUp(self) -> None:
        self.root = Path(__file__).resolve().parents[1]
        self.policy_path = self.root / "ops" / "scripts" / "system-guardian" / "system-guardian.policy.json"
        self.doc_path = self.root / "docs" / "ops" / "ATLAS-SYSTEM-GUARDIAN.md"

    def test_policy_file_exists_under_ops(self) -> None:
        self.assertTrue(self.policy_path.exists())
        self.assertEqual(self.policy_path.parts[-4:-1], ("ops", "scripts", "system-guardian"))

    def test_policy_contains_required_top_level_sections(self) -> None:
        policy = json.loads(self.policy_path.read_text(encoding="utf-8"))
        for key in ("defaults", "protected", "profiles", "candidates"):
            self.assertIn(key, policy)

        defaults = policy["defaults"]
        self.assertIn("scheduledTask", defaults)
        self.assertIn("thresholds", defaults)
        self.assertIn("profile", defaults)

    def test_profiles_and_candidate_rules_cover_required_modes(self) -> None:
        policy = json.loads(self.policy_path.read_text(encoding="utf-8"))
        self.assertTrue({"normal", "focus", "stream", "build"}.issubset(policy["profiles"]))
        self.assertEqual(policy["profiles"]["normal"]["mode"], "observe")
        self.assertEqual(policy["profiles"]["build"]["mode"], "cleanup")
        for name, profile in policy["profiles"].items():
            self.assertTrue(profile.get("summary"), f"profile {name} is missing a summary")

        candidate_ids = {item["id"] for item in policy["candidates"]}
        self.assertEqual(len(candidate_ids), len(policy["candidates"]))
        self.assertIn("browser-background-review", candidate_ids)
        self.assertIn("atlas-safe-test-process", candidate_ids)
        for candidate in policy["candidates"]:
            self.assertIn(candidate["defaultAction"], {"observe", "notify", "cleanup"})
            self.assertTrue(candidate.get("operatorHint"))
            classification = candidate.get("classification", {})
            self.assertTrue(classification.get("family"))
            self.assertTrue(classification.get("intent"))

    def test_doc_uses_root_allowed_paths(self) -> None:
        doc = self.doc_path.read_text(encoding="utf-8")
        self.assertIn("ops/scripts/system-guardian/", doc)
        self.assertIn("runtime/atlas/system-guardian/", doc)
        self.assertNotIn("config/system-guardian.policy.json", doc)
        self.assertIn("observe -> classify -> dry-run -> apply -> receipt", doc)
        self.assertIn("runtime/atlas/system-guardian/receipts/", doc)


if __name__ == "__main__":
    unittest.main()
