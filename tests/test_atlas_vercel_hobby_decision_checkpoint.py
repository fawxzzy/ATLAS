from __future__ import annotations

import hashlib
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

    def _signature_digest(self, signature: dict) -> str:
        encoded = json.dumps(signature, sort_keys=True, separators=(",", ":")).encode("utf-8")
        return "sha256:" + hashlib.sha256(encoded).hexdigest()

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

    def test_build_checkpoint_accepts_matching_hobby_review_for_latest_drift(self) -> None:
        root = self._temp_root()
        receipt_dir = root / "runtime" / "receipts" / "vercel-hobby-cost-governance"
        review_dir = root / "data" / "atlas" / "qa" / "vercel-hobby-cost-governance"
        review_dir.mkdir(parents=True, exist_ok=True)
        self._write_json(receipt_dir / "fitness-hobby-guardrail.2026-06-17.json", self._guardrail_payload(generated_at="2026-06-18T03:51:55Z"))
        self._write_json(receipt_dir / "fitness-hobby-guardrail.2026-06-18.json", self._guardrail_payload(generated_at="2026-06-18T04:45:01Z"))
        self._write_json(
            receipt_dir / "fitness-hobby-guardrail.latest.json",
            self._guardrail_payload(generated_at="2026-07-01T19:00:00Z", total_routes=34),
        )

        blocked = build_checkpoint(root=root, repo_id="fitness")
        current_signature = blocked["comparison"]["current_signature"]
        self._write_json(
            review_dir / "fitness-hobby-review.latest.json",
            {
                "contract_version": "atlas.vercel_hobby_review.v1",
                "repo_id": "fitness",
                "checkpoint_status": "ready",
                "decision": "keep_hobby",
                "decision_reason": "bounded route drift reviewed",
                "accepted_signature_digest": self._signature_digest(current_signature),
                "accepted_drift_fields": ["total_routes"],
            },
        )

        checkpoint = build_checkpoint(root=root, repo_id="fitness")

        self.assertEqual("ready", checkpoint["checkpoint_status"])
        self.assertEqual("keep_hobby", checkpoint["decision"])
        self.assertEqual("bounded route drift reviewed", checkpoint["decision_reason"])
        self.assertEqual(
            "data/atlas/qa/vercel-hobby-cost-governance/fitness-hobby-review.latest.json",
            checkpoint["approved_review_ref"],
        )

    def test_build_checkpoint_rejects_hobby_review_with_stale_signature_digest(self) -> None:
        # A review approved against an OLD signature must not silently cover
        # a NEW drift state just because a review file happens to exist --
        # otherwise a review, once committed, could be reused indefinitely
        # regardless of what actually changed afterward.
        root = self._temp_root()
        receipt_dir = root / "runtime" / "receipts" / "vercel-hobby-cost-governance"
        review_dir = root / "data" / "atlas" / "qa" / "vercel-hobby-cost-governance"
        review_dir.mkdir(parents=True, exist_ok=True)
        self._write_json(receipt_dir / "fitness-hobby-guardrail.2026-06-17.json", self._guardrail_payload(generated_at="2026-06-18T03:51:55Z"))
        self._write_json(receipt_dir / "fitness-hobby-guardrail.2026-06-18.json", self._guardrail_payload(generated_at="2026-06-18T04:45:01Z"))
        self._write_json(
            receipt_dir / "fitness-hobby-guardrail.latest.json",
            self._guardrail_payload(generated_at="2026-07-01T19:00:00Z", total_routes=34),
        )
        self._write_json(
            review_dir / "fitness-hobby-review.latest.json",
            {
                "contract_version": "atlas.vercel_hobby_review.v1",
                "repo_id": "fitness",
                "checkpoint_status": "ready",
                "decision": "keep_hobby",
                "decision_reason": "bounded route drift reviewed",
                "accepted_signature_digest": "sha256:0000000000000000000000000000000000000000000000000000000000000",
                "accepted_drift_fields": ["total_routes"],
            },
        )

        checkpoint = build_checkpoint(root=root, repo_id="fitness")

        self.assertEqual("blocked", checkpoint["checkpoint_status"])
        self.assertEqual("upgrade_review_required", checkpoint["decision"])
        self.assertIn("signature digest does not match", checkpoint["decision_reason"])

    def test_build_checkpoint_rejects_hobby_review_missing_drift_field_coverage(self) -> None:
        # A review that approved one kind of drift must not be treated as
        # covering a *different* field that also drifted -- the review has
        # to name every field it is actually accepting.
        root = self._temp_root()
        receipt_dir = root / "runtime" / "receipts" / "vercel-hobby-cost-governance"
        review_dir = root / "data" / "atlas" / "qa" / "vercel-hobby-cost-governance"
        review_dir.mkdir(parents=True, exist_ok=True)
        self._write_json(receipt_dir / "fitness-hobby-guardrail.2026-06-17.json", self._guardrail_payload(generated_at="2026-06-18T03:51:55Z"))
        self._write_json(receipt_dir / "fitness-hobby-guardrail.2026-06-18.json", self._guardrail_payload(generated_at="2026-06-18T04:45:01Z"))
        self._write_json(
            receipt_dir / "fitness-hobby-guardrail.latest.json",
            self._guardrail_payload(generated_at="2026-07-01T19:00:00Z", total_routes=34),
        )
        blocked = build_checkpoint(root=root, repo_id="fitness")
        current_signature = blocked["comparison"]["current_signature"]
        self._write_json(
            review_dir / "fitness-hobby-review.latest.json",
            {
                "contract_version": "atlas.vercel_hobby_review.v1",
                "repo_id": "fitness",
                "checkpoint_status": "ready",
                "decision": "keep_hobby",
                "accepted_signature_digest": self._signature_digest(current_signature),
                "accepted_drift_fields": ["some_other_field"],
            },
        )

        checkpoint = build_checkpoint(root=root, repo_id="fitness")

        self.assertEqual("blocked", checkpoint["checkpoint_status"])
        self.assertEqual("upgrade_review_required", checkpoint["decision"])
        self.assertIn("does not cover current drift fields", checkpoint["decision_reason"])

    def test_build_checkpoint_review_target_sha_is_audit_only_not_authoritative(self) -> None:
        # target_sha is context, not a gate: a review with an arbitrary/
        # unverifiable target_sha must still be accepted on its other
        # merits, and the checkpoint must mark it audit-only rather than
        # silently implying it was validated.
        root = self._temp_root()
        receipt_dir = root / "runtime" / "receipts" / "vercel-hobby-cost-governance"
        review_dir = root / "data" / "atlas" / "qa" / "vercel-hobby-cost-governance"
        review_dir.mkdir(parents=True, exist_ok=True)
        self._write_json(receipt_dir / "fitness-hobby-guardrail.2026-06-17.json", self._guardrail_payload(generated_at="2026-06-18T03:51:55Z"))
        self._write_json(receipt_dir / "fitness-hobby-guardrail.2026-06-18.json", self._guardrail_payload(generated_at="2026-06-18T04:45:01Z"))
        self._write_json(
            receipt_dir / "fitness-hobby-guardrail.latest.json",
            self._guardrail_payload(generated_at="2026-07-01T19:00:00Z", total_routes=34),
        )
        blocked = build_checkpoint(root=root, repo_id="fitness")
        current_signature = blocked["comparison"]["current_signature"]
        self._write_json(
            review_dir / "fitness-hobby-review.latest.json",
            {
                "contract_version": "atlas.vercel_hobby_review.v1",
                "repo_id": "fitness",
                "checkpoint_status": "ready",
                "decision": "keep_hobby",
                "accepted_signature_digest": self._signature_digest(current_signature),
                "accepted_drift_fields": ["total_routes"],
                "target_sha": "0000000000000000000000000000000000000000",
            },
        )

        checkpoint = build_checkpoint(root=root, repo_id="fitness")

        self.assertEqual("keep_hobby", checkpoint["decision"])
        self.assertEqual("0000000000000000000000000000000000000000", checkpoint["review_target_sha"])
        self.assertEqual("audit_only", checkpoint["review_target_sha_authority"])

    def test_build_checkpoint_review_fails_closed_on_each_required_field(self) -> None:
        root = self._temp_root()
        receipt_dir = root / "runtime" / "receipts" / "vercel-hobby-cost-governance"
        review_dir = root / "data" / "atlas" / "qa" / "vercel-hobby-cost-governance"
        review_dir.mkdir(parents=True, exist_ok=True)
        self._write_json(receipt_dir / "fitness-hobby-guardrail.2026-06-17.json", self._guardrail_payload(generated_at="2026-06-18T03:51:55Z"))
        self._write_json(receipt_dir / "fitness-hobby-guardrail.2026-06-18.json", self._guardrail_payload(generated_at="2026-06-18T04:45:01Z"))
        self._write_json(
            receipt_dir / "fitness-hobby-guardrail.latest.json",
            self._guardrail_payload(generated_at="2026-07-01T19:00:00Z", total_routes=34),
        )
        blocked = build_checkpoint(root=root, repo_id="fitness")
        current_signature = blocked["comparison"]["current_signature"]

        base_review = {
            "contract_version": "atlas.vercel_hobby_review.v1",
            "repo_id": "fitness",
            "checkpoint_status": "ready",
            "decision": "keep_hobby",
            "accepted_signature_digest": self._signature_digest(current_signature),
            "accepted_drift_fields": ["total_routes"],
        }
        mutations = {
            "contract_version": "atlas.vercel_hobby_review.v0",
            "repo_id": "other-repo",
            "checkpoint_status": "blocked",
            "decision": "upgrade_review_required",
        }
        for field, bad_value in mutations.items():
            with self.subTest(field=field):
                review = dict(base_review)
                review[field] = bad_value
                self._write_json(review_dir / "fitness-hobby-review.latest.json", review)

                checkpoint = build_checkpoint(root=root, repo_id="fitness")

                self.assertEqual("blocked", checkpoint["checkpoint_status"], field)
                self.assertEqual("upgrade_review_required", checkpoint["decision"], field)

    def test_build_checkpoint_preserved_drift_still_blocks_despite_matching_review(self) -> None:
        # A review that only covers *latest* drift must never paper over
        # preserved-snapshot drift -- those are a different, independent
        # signal and the review contract doesn't speak to them at all.
        root = self._temp_root()
        receipt_dir = root / "runtime" / "receipts" / "vercel-hobby-cost-governance"
        review_dir = root / "data" / "atlas" / "qa" / "vercel-hobby-cost-governance"
        review_dir.mkdir(parents=True, exist_ok=True)
        self._write_json(receipt_dir / "fitness-hobby-guardrail.2026-06-17.json", self._guardrail_payload(generated_at="2026-06-18T03:51:55Z", total_routes=31))
        self._write_json(
            receipt_dir / "fitness-hobby-guardrail.2026-06-18.json",
            self._guardrail_payload(generated_at="2026-06-18T04:45:01Z", total_routes=32),
        )
        self._write_json(
            receipt_dir / "fitness-hobby-guardrail.latest.json",
            self._guardrail_payload(generated_at="2026-06-18T04:46:00Z", total_routes=32),
        )
        blocked = build_checkpoint(root=root, repo_id="fitness")
        self.assertTrue(blocked["comparison"]["preserved_snapshot_drift"])
        current_signature = blocked["comparison"]["current_signature"]
        self._write_json(
            review_dir / "fitness-hobby-review.latest.json",
            {
                "contract_version": "atlas.vercel_hobby_review.v1",
                "repo_id": "fitness",
                "checkpoint_status": "ready",
                "decision": "keep_hobby",
                "accepted_signature_digest": self._signature_digest(current_signature),
                "accepted_drift_fields": [],
            },
        )

        checkpoint = build_checkpoint(root=root, repo_id="fitness")

        self.assertEqual("blocked", checkpoint["checkpoint_status"])
        self.assertEqual("upgrade_review_required", checkpoint["decision"])
        self.assertIn("preserved dated guardrail snapshots drifted", checkpoint["decision_reason"])

    def test_build_checkpoint_non_ok_deployment_posture_still_blocks_despite_matching_review(self) -> None:
        root = self._temp_root()
        receipt_dir = root / "runtime" / "receipts" / "vercel-hobby-cost-governance"
        review_dir = root / "data" / "atlas" / "qa" / "vercel-hobby-cost-governance"
        review_dir.mkdir(parents=True, exist_ok=True)

        def _payload_with_posture(generated_at: str, posture: str) -> dict:
            payload = self._guardrail_payload(generated_at=generated_at)
            payload["guardrail_posture"]["deployment_posture"] = posture
            return payload

        self._write_json(receipt_dir / "fitness-hobby-guardrail.2026-06-17.json", _payload_with_posture("2026-06-18T03:51:55Z", "ok"))
        self._write_json(receipt_dir / "fitness-hobby-guardrail.2026-06-18.json", _payload_with_posture("2026-06-18T04:45:01Z", "ok"))
        self._write_json(receipt_dir / "fitness-hobby-guardrail.latest.json", _payload_with_posture("2026-06-18T04:46:00Z", "at_risk"))

        blocked = build_checkpoint(root=root, repo_id="fitness")
        current_signature = blocked["comparison"]["current_signature"]
        self._write_json(
            review_dir / "fitness-hobby-review.latest.json",
            {
                "contract_version": "atlas.vercel_hobby_review.v1",
                "repo_id": "fitness",
                "checkpoint_status": "ready",
                "decision": "keep_hobby",
                "accepted_signature_digest": self._signature_digest(current_signature),
                "accepted_drift_fields": [],
            },
        )

        checkpoint = build_checkpoint(root=root, repo_id="fitness")

        self.assertEqual("blocked", checkpoint["checkpoint_status"])
        self.assertIn("deployment posture is no longer ok", checkpoint["decision_reason"])

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
