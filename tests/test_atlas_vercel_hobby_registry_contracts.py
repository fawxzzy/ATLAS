"""Contract tests for the tracked, source-owned Vercel Hobby-governance
registry (docs/registry/vercel-project-links/, docs/registry/vercel-hobby-reviews/).

These paths replace the previous data/atlas/qa/vercel-hobby-cost-governance/
location, which is gitignored (see .gitignore lines 35, 43-44) and therefore
never survived a fresh clone or hosted CI checkout -- the exact defect this
PR closes. See ops/atlas/vercel_hobby_guardrail_report.py's
_project_link_fallback_path()/_parse_expected_project_link_payload() and
ops/atlas/vercel_hobby_decision_checkpoint.py's _default_review_ref().
"""

from __future__ import annotations

import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from ops.atlas.ui_standards.validate import validate_json_schema
from ops.atlas.vercel_hobby_guardrail_report import (
    GuardrailReportError,
    _load_project_link,
    _project_link_fallback_path,
)
from ops.atlas.vercel_hobby_decision_checkpoint import _default_review_ref

FITNESS_PROJECT_ID = "prj_rtlFVOMFAWCRoJ3SQjHloi89881K"
FITNESS_TEAM_ID = "team_CMJn7MvzFZZBnhNnjVUZF2RD"
FITNESS_TEAM_SLUG = "fawxzzy"
FITNESS_PROJECT_NAME = "fawxzzy-fitness"


class AtlasVercelHobbyRegistryContractTests(unittest.TestCase):
    def _read_json(self, path: Path) -> dict:
        return json.loads(path.read_text(encoding="utf-8"))

    def _temp_root(self) -> Path:
        temp_dir = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, temp_dir, ignore_errors=True)
        (temp_dir / "repos" / "fawxzzy-fitness" / ".vercel").mkdir(parents=True)
        return temp_dir

    # -- path relocation -----------------------------------------------

    def test_project_link_path_function_targets_tracked_registry_not_gitignored_data(self) -> None:
        path = _project_link_fallback_path(ROOT, "fitness")
        rel = path.relative_to(ROOT).as_posix()
        self.assertEqual("docs/registry/vercel-project-links/fitness.json", rel)
        self.assertFalse(rel.startswith("data/"))

    def test_review_ref_targets_tracked_registry_not_gitignored_data(self) -> None:
        rel = _default_review_ref("fitness")
        self.assertEqual("docs/registry/vercel-hobby-reviews/fitness.latest.json", rel)
        self.assertFalse(rel.startswith("data/"))

    def test_project_link_path_is_actually_tracked_by_git(self) -> None:
        path = _project_link_fallback_path(ROOT, "fitness")
        self.assertTrue(path.exists(), f"expected tracked file missing: {path}")

    # -- committed identity is real, and uses team_id not team_slug ----

    def test_committed_fitness_project_link_conforms_to_its_own_schema(self) -> None:
        schema = self._read_json(ROOT / "schemas" / "atlas.vercel-project-link.v1.json")
        payload = self._read_json(ROOT / "docs" / "registry" / "vercel-project-links" / "fitness.json")
        errors = validate_json_schema(payload, schema)
        self.assertEqual([], errors)

    def test_committed_fitness_project_link_is_not_a_placeholder(self) -> None:
        payload = self._read_json(ROOT / "docs" / "registry" / "vercel-project-links" / "fitness.json")
        self.assertEqual(FITNESS_PROJECT_ID, payload["project_id"])
        self.assertEqual(FITNESS_PROJECT_NAME, payload["project_name"])

    def test_committed_fitness_team_id_is_the_canonical_id_not_the_slug(self) -> None:
        payload = self._read_json(ROOT / "docs" / "registry" / "vercel-project-links" / "fitness.json")
        self.assertEqual(FITNESS_TEAM_ID, payload["team_id"])
        self.assertTrue(payload["team_id"].startswith("team_"))
        self.assertNotEqual(FITNESS_TEAM_SLUG, payload["team_id"])
        # team_slug may be present as audit-only metadata but must never be
        # what a real orgId comparison checks against.
        self.assertEqual(FITNESS_TEAM_SLUG, payload.get("team_slug"))

    def test_project_link_schema_rejects_team_slug_shaped_as_team_id(self) -> None:
        schema = self._read_json(ROOT / "schemas" / "atlas.vercel-project-link.v1.json")
        payload = {
            "contract_version": "atlas.vercel-project-link.v1",
            "repo_id": "fitness",
            "project_id": FITNESS_PROJECT_ID,
            "team_id": FITNESS_TEAM_SLUG,  # a bare slug, not team_<id>
            "project_name": FITNESS_PROJECT_NAME,
        }
        errors = validate_json_schema(payload, schema)
        self.assertTrue(errors, "a bare team slug must not satisfy the team_id pattern")

    # -- runtime match/mismatch semantics against a real orgId ---------

    def test_local_orgid_matching_canonical_team_id_is_a_match(self) -> None:
        root = self._temp_root()
        (root / "repos" / "fawxzzy-fitness" / ".vercel" / "project.json").write_text(
            json.dumps(
                {
                    "projectId": FITNESS_PROJECT_ID,
                    "orgId": FITNESS_TEAM_ID,
                    "projectName": FITNESS_PROJECT_NAME,
                }
            ),
            encoding="utf-8",
        )
        fallback_dir = root / "docs" / "registry" / "vercel-project-links"
        fallback_dir.mkdir(parents=True, exist_ok=True)
        (fallback_dir / "fitness.json").write_text(
            json.dumps(
                {
                    "contract_version": "atlas.vercel-project-link.v1",
                    "repo_id": "fitness",
                    "project_id": FITNESS_PROJECT_ID,
                    "team_id": FITNESS_TEAM_ID,
                    "project_name": FITNESS_PROJECT_NAME,
                }
            ),
            encoding="utf-8",
        )

        result = _load_project_link(root, "fitness", root / "repos" / "fawxzzy-fitness")
        self.assertTrue(result["project_link_match"])
        self.assertEqual(FITNESS_TEAM_ID, result["team_id"])

    def test_local_orgid_matching_team_slug_instead_of_canonical_id_fails_closed(self) -> None:
        # This is the exact defect the correction addresses: if the
        # committed record's team_id were ever a slug, a normally linked
        # checkout (whose real orgId is the canonical team_<id>) would
        # mismatch every time. Prove the reverse holds too: a local file
        # that (incorrectly) reports the slug as orgId must fail closed
        # against a correctly-canonical committed record, not silently pass.
        root = self._temp_root()
        (root / "repos" / "fawxzzy-fitness" / ".vercel" / "project.json").write_text(
            json.dumps(
                {
                    "projectId": FITNESS_PROJECT_ID,
                    "orgId": FITNESS_TEAM_SLUG,  # wrong shape for orgId
                    "projectName": FITNESS_PROJECT_NAME,
                }
            ),
            encoding="utf-8",
        )
        fallback_dir = root / "docs" / "registry" / "vercel-project-links"
        fallback_dir.mkdir(parents=True, exist_ok=True)
        (fallback_dir / "fitness.json").write_text(
            json.dumps(
                {
                    "contract_version": "atlas.vercel-project-link.v1",
                    "repo_id": "fitness",
                    "project_id": FITNESS_PROJECT_ID,
                    "team_id": FITNESS_TEAM_ID,
                    "project_name": FITNESS_PROJECT_NAME,
                }
            ),
            encoding="utf-8",
        )

        with self.assertRaises(GuardrailReportError) as ctx:
            _load_project_link(root, "fitness", root / "repos" / "fawxzzy-fitness")
        self.assertIn("team_id", str(ctx.exception))

    # -- runtime schema enforcement for the expected identity file -----

    def test_load_project_link_fails_closed_on_expected_identity_with_extra_field(self) -> None:
        root = self._temp_root()
        fallback_dir = root / "docs" / "registry" / "vercel-project-links"
        fallback_dir.mkdir(parents=True, exist_ok=True)
        (fallback_dir / "fitness.json").write_text(
            json.dumps(
                {
                    "contract_version": "atlas.vercel-project-link.v1",
                    "repo_id": "fitness",
                    "project_id": FITNESS_PROJECT_ID,
                    "team_id": FITNESS_TEAM_ID,
                    "project_name": FITNESS_PROJECT_NAME,
                    "unexpected": "should fail closed",
                }
            ),
            encoding="utf-8",
        )
        (root / "repos" / "fawxzzy-fitness" / ".vercel" / "project.json").unlink(missing_ok=True)

        with self.assertRaises(GuardrailReportError) as ctx:
            _load_project_link(root, "fitness", root / "repos" / "fawxzzy-fitness")
        self.assertIn("schema validation", str(ctx.exception))

    def test_load_project_link_fails_closed_on_wrong_contract_version(self) -> None:
        root = self._temp_root()
        fallback_dir = root / "docs" / "registry" / "vercel-project-links"
        fallback_dir.mkdir(parents=True, exist_ok=True)
        (fallback_dir / "fitness.json").write_text(
            json.dumps(
                {
                    "contract_version": "atlas.vercel-project-link.v0",
                    "repo_id": "fitness",
                    "project_id": FITNESS_PROJECT_ID,
                    "team_id": FITNESS_TEAM_ID,
                    "project_name": FITNESS_PROJECT_NAME,
                }
            ),
            encoding="utf-8",
        )
        (root / "repos" / "fawxzzy-fitness" / ".vercel" / "project.json").unlink(missing_ok=True)

        with self.assertRaises(GuardrailReportError) as ctx:
            _load_project_link(root, "fitness", root / "repos" / "fawxzzy-fitness")
        self.assertIn("schema validation", str(ctx.exception))

    # -- review schema: closed shape, both positive and negative -------

    def test_hobby_review_schema_rejects_malformed_records(self) -> None:
        schema = self._read_json(ROOT / "schemas" / "atlas.vercel-hobby-review.v1.json")

        wrong_decision = {
            "contract_version": "atlas.vercel_hobby_review.v1",
            "repo_id": "fitness",
            "checkpoint_status": "ready",
            "decision": "upgrade",
            "accepted_signature_digest": "sha256:aaaa",
            "accepted_drift_fields": [],
        }
        self.assertTrue(validate_json_schema(wrong_decision, schema))

        missing_digest = {
            "contract_version": "atlas.vercel_hobby_review.v1",
            "repo_id": "fitness",
            "checkpoint_status": "ready",
            "decision": "keep_hobby",
            "accepted_drift_fields": [],
        }
        self.assertTrue(validate_json_schema(missing_digest, schema))

        malformed_digest_type = {
            "contract_version": "atlas.vercel_hobby_review.v1",
            "repo_id": "fitness",
            "checkpoint_status": "ready",
            "decision": "keep_hobby",
            "accepted_signature_digest": 12345,
            "accepted_drift_fields": [],
        }
        self.assertTrue(validate_json_schema(malformed_digest_type, schema))

        wrong_repo_status = {
            "contract_version": "atlas.vercel_hobby_review.v1",
            "repo_id": "fitness",
            "checkpoint_status": "draft",
            "decision": "keep_hobby",
            "accepted_signature_digest": "sha256:aaaa",
            "accepted_drift_fields": [],
        }
        self.assertTrue(validate_json_schema(wrong_repo_status, schema))

        extra_field = {
            "contract_version": "atlas.vercel_hobby_review.v1",
            "repo_id": "fitness",
            "checkpoint_status": "ready",
            "decision": "keep_hobby",
            "accepted_signature_digest": "sha256:aaaa",
            "accepted_drift_fields": [],
            "unexpected_field": "should be rejected",
        }
        self.assertTrue(validate_json_schema(extra_field, schema))

    def test_hobby_review_schema_accepts_a_well_formed_record(self) -> None:
        schema = self._read_json(ROOT / "schemas" / "atlas.vercel-hobby-review.v1.json")
        valid = self._read_json(
            ROOT / "tests" / "fixtures" / "atlas-vercel-hobby-governance" / "valid-review-record.json"
        )
        self.assertEqual([], validate_json_schema(valid, schema))

    def test_load_matching_review_fails_closed_on_extra_field_via_runtime_call(self) -> None:
        from ops.atlas.vercel_hobby_decision_checkpoint import _load_matching_review

        root = self._temp_root()
        review_dir = root / "docs" / "registry" / "vercel-hobby-reviews"
        review_dir.mkdir(parents=True, exist_ok=True)
        (review_dir / "fitness.latest.json").write_text(
            json.dumps(
                {
                    "contract_version": "atlas.vercel_hobby_review.v1",
                    "repo_id": "fitness",
                    "checkpoint_status": "ready",
                    "decision": "keep_hobby",
                    "accepted_signature_digest": "sha256:" + ("a" * 64),
                    "accepted_drift_fields": [],
                    "unexpected_field": "should fail closed before digest authorization",
                }
            ),
            encoding="utf-8",
        )

        review, findings = _load_matching_review(
            root=root,
            repo_id="fitness",
            latest_signature={"anything": "irrelevant, schema fails first"},
            latest_alignment_drift=[],
        )
        self.assertIsNone(review)
        self.assertTrue(any("schema validation" in f for f in findings))

    # -- the empty-directory case is a valid, non-permanent state ------

    def test_review_directory_records_all_schema_valid_zero_is_valid(self) -> None:
        # Enumerate every *.latest.json instance actually committed and
        # validate each against the closed schema. Zero instances is a
        # valid outcome (the correct current state) -- this test does not
        # hard-code "must be empty forever," so a future legitimate review
        # record requires no test-code rewrite to be accepted, only to
        # continue passing schema validation.
        schema = self._read_json(ROOT / "schemas" / "atlas.vercel-hobby-review.v1.json")
        review_dir = ROOT / "docs" / "registry" / "vercel-hobby-reviews"
        self.assertTrue(review_dir.is_dir())
        instances = sorted(review_dir.glob("*.latest.json"))
        for instance in instances:
            payload = self._read_json(instance)
            errors = validate_json_schema(payload, schema)
            self.assertEqual([], errors, f"{instance.name} failed schema validation: {errors}")
        # Document current state without asserting it must stay this way.
        if not instances:
            self.assertEqual([], instances)

    def test_review_directory_has_no_gitkeep_placeholder(self) -> None:
        # Superseded by README.md, which documents the contract instead of
        # being a silent, content-free placeholder.
        review_dir = ROOT / "docs" / "registry" / "vercel-hobby-reviews"
        self.assertFalse((review_dir / ".gitkeep").exists())
        self.assertTrue((review_dir / "README.md").exists())

    # -- schema/runtime field parity ------------------------------------

    def test_hobby_review_schema_field_set_matches_runtime_supported_fields(self) -> None:
        # ops/atlas/vercel_hobby_decision_checkpoint.py reads decision_reason
        # and next_action off a matched review (see build_checkpoint()'s
        # `matching_review.get(...)` calls). If the closed schema's property
        # set ever drifts out of sync with what the runtime actually reads,
        # a legitimate operator-authored field would be schema-rejected
        # before it ever reached that runtime code. This test freezes the
        # complete source-record field set so the two cannot silently
        # diverge again.
        schema = self._read_json(ROOT / "schemas" / "atlas.vercel-hobby-review.v1.json")
        expected_fields = {
            "contract_version",
            "repo_id",
            "checkpoint_status",
            "decision",
            "accepted_signature_digest",
            "accepted_drift_fields",
            "target_sha",
            "decision_reason",
            "next_action",
        }
        self.assertEqual(expected_fields, set(schema["properties"].keys()))


if __name__ == "__main__":
    unittest.main()
