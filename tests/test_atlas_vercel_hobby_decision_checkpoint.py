from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from ops.atlas.vercel_hobby_decision_checkpoint import (
    DecisionCheckpointError,
    build_checkpoint,
    main,
)


class AtlasVercelHobbyDecisionCheckpointTests(unittest.TestCase):
    def _temp_root(self) -> Path:
        temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(temp_dir.cleanup)
        root = Path(temp_dir.name)
        (root / "runtime" / "receipts" / "vercel-hobby-cost-governance").mkdir(parents=True, exist_ok=True)
        return root

    def _guardrail_payload(self, *, generated_at: str, total_routes: int = 31) -> dict:
        return {
            "report_version": "atlas.vercel_hobby_guardrail.v1",
            "report_id": "vercel-hobby-guardrail-fitness",
            "generated_at": generated_at,
            "repo_id": "fitness",
            "project_link": {
                "project_id": "prj_test",
                "project_name": "fawxzzy-fitness",
            },
            "vercel_config": {
                "deployment_enabled": False,
            },
            "summary": {
                "total_routes": total_routes,
                "api_routes": 22,
                "auth_routes": 5,
                "dev_routes": 4,
                "force_dynamic_routes": 29,
                "nodejs_routes": 4,
                "fetch_inventory": {
                    "total_fetch_sites": 34,
                    "internal_fetch_sites": 17,
                    "external_or_dynamic_fetch_sites": 17,
                },
            },
            "middleware_inventory": {
                "present": True,
                "refresh_session_call_present": True,
                "public_authless_paths": [
                    "/api/app-version",
                    "/api/discord/interactions",
                ],
            },
            "nodejs_routes": [
                "/api/discord/interactions",
                "/api/spotify/oauth/callback",
            ],
            "watch_targets": [
                {
                    "target": "/api/discord/interactions",
                    "references": 1,
                    "files": ["src/lib/auth-session.ts"],
                }
            ],
            "guardrail_posture": {
                "deployment_posture": "ok",
                "route_pressure_posture": "watch",
                "middleware_pressure_posture": "watch",
                "integration_pressure_posture": "watch",
                "hot_route_watch_posture": "watch",
            },
        }

    def _write_json(self, path: Path, payload: dict) -> None:
        path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")

    def test_build_checkpoint_keeps_hobby_when_preserved_window_is_stable(self) -> None:
        root = self._temp_root()
        receipt_dir = root / "runtime" / "receipts" / "vercel-hobby-cost-governance"
        self._write_json(receipt_dir / "fitness-hobby-guardrail.2026-06-17.json", self._guardrail_payload(generated_at="2026-06-18T03:51:55Z"))
        self._write_json(receipt_dir / "fitness-hobby-guardrail.2026-06-18.json", self._guardrail_payload(generated_at="2026-06-18T04:45:01Z"))
        self._write_json(receipt_dir / "fitness-hobby-guardrail.latest.json", self._guardrail_payload(generated_at="2026-06-18T04:46:00Z"))

        checkpoint = build_checkpoint(root=root, repo_id="fitness")

        self.assertEqual("atlas.vercel_hobby_decision.v1", checkpoint["contract_version"])
        self.assertEqual("ready", checkpoint["checkpoint_status"])
        self.assertEqual("keep_hobby", checkpoint["decision"])
        self.assertEqual([], checkpoint["comparison"]["preserved_snapshot_drift"])
        self.assertEqual([], checkpoint["comparison"]["latest_alignment_drift"])

    def test_build_checkpoint_requires_upgrade_review_when_preserved_drift_exists(self) -> None:
        root = self._temp_root()
        receipt_dir = root / "runtime" / "receipts" / "vercel-hobby-cost-governance"
        self._write_json(receipt_dir / "fitness-hobby-guardrail.2026-06-17.json", self._guardrail_payload(generated_at="2026-06-18T03:51:55Z"))
        self._write_json(
            receipt_dir / "fitness-hobby-guardrail.2026-06-18.json",
            self._guardrail_payload(generated_at="2026-06-18T04:45:01Z", total_routes=32),
        )
        self._write_json(
            receipt_dir / "fitness-hobby-guardrail.latest.json",
            self._guardrail_payload(generated_at="2026-06-18T04:46:00Z", total_routes=32),
        )

        checkpoint = build_checkpoint(root=root, repo_id="fitness")

        self.assertEqual("blocked", checkpoint["checkpoint_status"])
        self.assertEqual("upgrade_review_required", checkpoint["decision"])
        self.assertTrue(checkpoint["comparison"]["preserved_snapshot_drift"])

    def test_build_checkpoint_fails_closed_without_two_preserved_snapshots(self) -> None:
        root = self._temp_root()
        receipt_dir = root / "runtime" / "receipts" / "vercel-hobby-cost-governance"
        self._write_json(receipt_dir / "fitness-hobby-guardrail.2026-06-18.json", self._guardrail_payload(generated_at="2026-06-18T04:45:01Z"))
        self._write_json(receipt_dir / "fitness-hobby-guardrail.latest.json", self._guardrail_payload(generated_at="2026-06-18T04:46:00Z"))

        with self.assertRaises(DecisionCheckpointError):
            build_checkpoint(root=root, repo_id="fitness")

    def test_main_writes_json_output(self) -> None:
        root = self._temp_root()
        receipt_dir = root / "runtime" / "receipts" / "vercel-hobby-cost-governance"
        self._write_json(receipt_dir / "fitness-hobby-guardrail.2026-06-17.json", self._guardrail_payload(generated_at="2026-06-18T03:51:55Z"))
        self._write_json(receipt_dir / "fitness-hobby-guardrail.2026-06-18.json", self._guardrail_payload(generated_at="2026-06-18T04:45:01Z"))
        self._write_json(receipt_dir / "fitness-hobby-guardrail.latest.json", self._guardrail_payload(generated_at="2026-06-18T04:46:00Z"))

        output_ref = "runtime/receipts/vercel-hobby-cost-governance/fitness-hobby-decision.latest.json"
        exit_code = main(["--root", str(root), "--repo-id", "fitness", "--format", "json", "--output", output_ref])

        self.assertEqual(0, exit_code)
        payload = json.loads((root / output_ref).read_text(encoding="utf-8"))
        self.assertEqual("vercel-hobby-decision-fitness", payload["checkpoint_id"])
        self.assertEqual("keep_hobby", payload["decision"])


if __name__ == "__main__":
    unittest.main()
