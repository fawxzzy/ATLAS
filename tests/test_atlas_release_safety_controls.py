from __future__ import annotations

import hashlib
import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from ops.atlas.release_safety_controls import (
    ReleaseSafetyViolation,
    canonicalize_same_origin_workbox_key,
    validate_vercel_no_auto_link_preflight,
    verify_workbox_precache_entries,
)


class WorkboxReleaseSafetyTests(unittest.TestCase):
    origin = "https://app.example"
    digest = "a" * 64

    def test_relative_root_relative_and_absolute_same_origin_are_equivalent(self) -> None:
        keys = {
            canonicalize_same_origin_workbox_key(value, expected_origin=self.origin)
            for value in ("favicon.ico", "/favicon.ico", "https://app.example/favicon.ico")
        }
        self.assertEqual({"/favicon.ico"}, keys)

    def test_exact_verification_preserves_bytes_and_hash(self) -> None:
        result = verify_workbox_precache_entries(
            [{"url": "favicon.ico", "bytes": 42, "sha256": self.digest}],
            [{"url": "/favicon.ico", "bytes": 42, "sha256": self.digest}],
            expected_origin=self.origin,
        )
        self.assertTrue(result["valid"])
        self.assertEqual(1, result["required_entry_count"])

    def assert_rejected(self, code: str, function, *args, **kwargs) -> None:
        with self.assertRaises(ReleaseSafetyViolation) as caught:
            function(*args, **kwargs)
        self.assertEqual(code, caught.exception.code)

    def test_rejects_foreign_origin(self) -> None:
        self.assert_rejected(
            "WORKBOX_FOREIGN_ORIGIN",
            canonicalize_same_origin_workbox_key,
            "https://evil.example/favicon.ico",
            expected_origin=self.origin,
        )

    def test_rejects_raw_control_characters_before_url_parsing(self) -> None:
        for control in ("\t", "\r", "\n"):
            self.assert_rejected(
                "WORKBOX_URL_INVALID",
                canonicalize_same_origin_workbox_key,
                f"/foo{control}bar",
                expected_origin=self.origin,
            )

    def test_rejects_raw_and_encoded_traversal(self) -> None:
        for value in ("../favicon.ico", "%2e%2e/favicon.ico", "/safe/%2E%2E/favicon.ico"):
            self.assert_rejected(
                "WORKBOX_PATH_TRAVERSAL",
                canonicalize_same_origin_workbox_key,
                value,
                expected_origin=self.origin,
            )

    def test_safe_encoded_path_canonicalizes_without_basename_matching(self) -> None:
        self.assertEqual(
            "/assets/favicon.ico",
            canonicalize_same_origin_workbox_key("/assets/%66avicon.ico", expected_origin=self.origin),
        )
        self.assertNotEqual(
            canonicalize_same_origin_workbox_key("/a/favicon.ico", expected_origin=self.origin),
            canonicalize_same_origin_workbox_key("/b/favicon.ico", expected_origin=self.origin),
        )

    def test_encoded_reserved_delimiters_and_separators_remain_distinct(self) -> None:
        self.assertNotEqual(
            canonicalize_same_origin_workbox_key("/a%3Fb", expected_origin=self.origin),
            canonicalize_same_origin_workbox_key("/a?b", expected_origin=self.origin),
        )
        self.assertNotEqual(
            canonicalize_same_origin_workbox_key("/a%23b", expected_origin=self.origin),
            canonicalize_same_origin_workbox_key("/a#b", expected_origin=self.origin, fragment_policy="exact"),
        )
        self.assertNotEqual(
            canonicalize_same_origin_workbox_key("/a%2Fb", expected_origin=self.origin),
            canonicalize_same_origin_workbox_key("/a/b", expected_origin=self.origin),
        )
        self.assertEqual(
            "/a%3Fb%23c%2Fd",
            canonicalize_same_origin_workbox_key("/a%3fb%23c%2fd", expected_origin=self.origin),
        )

    def test_rejects_duplicate_after_canonicalization(self) -> None:
        entries = [
            {"url": "favicon.ico", "bytes": 42, "sha256": self.digest},
            {"url": "/favicon.ico", "bytes": 42, "sha256": self.digest},
        ]
        self.assert_rejected(
            "WORKBOX_DUPLICATE_CANONICAL_KEY",
            verify_workbox_precache_entries,
            entries,
            [],
            expected_origin=self.origin,
        )

    def test_query_and_fragment_semantics_are_explicit(self) -> None:
        self.assertNotEqual(
            canonicalize_same_origin_workbox_key("/a.js?v=1", expected_origin=self.origin),
            canonicalize_same_origin_workbox_key("/a.js?v=2", expected_origin=self.origin),
        )
        self.assertEqual(
            "/a.js",
            canonicalize_same_origin_workbox_key(
                "/a.js?v=1#fragment",
                expected_origin=self.origin,
                query_policy="ignore",
                fragment_policy="ignore",
            ),
        )
        self.assert_rejected(
            "WORKBOX_FRAGMENT_REJECTED",
            canonicalize_same_origin_workbox_key,
            "/a.js#fragment",
            expected_origin=self.origin,
        )

    def test_rejects_missing_entry_and_byte_or_hash_drift(self) -> None:
        required = [{"url": "/favicon.ico", "bytes": 42, "sha256": self.digest}]
        self.assert_rejected(
            "WORKBOX_REQUIRED_ENTRY_MISSING",
            verify_workbox_precache_entries,
            [],
            required,
            expected_origin=self.origin,
        )
        for observed in (
            [{"url": "/favicon.ico", "bytes": 43, "sha256": self.digest}],
            [{"url": "/favicon.ico", "bytes": 42, "sha256": "b" * 64}],
        ):
            self.assert_rejected(
                "WORKBOX_BYTE_OR_HASH_DRIFT",
                verify_workbox_precache_entries,
                observed,
                required,
                expected_origin=self.origin,
            )


class VercelNoAutoLinkTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.workspace = Path(self.temporary.name) / "workspace"
        self.binding = self.workspace / ".vercel" / "project.json"
        self.binding.parent.mkdir(parents=True)
        self.binding.write_text(json.dumps({"projectId": "prj_exact", "orgId": "team_exact"}), encoding="utf-8")
        self.binding_hash = hashlib.sha256(self.binding.read_bytes()).hexdigest()
        self.kwargs = {
            "workspace_root": self.workspace,
            "expected_workspace_root": self.workspace,
            "expected_project_id": "prj_exact",
            "expected_org_id": "team_exact",
            "expected_binding_sha256": self.binding_hash,
            "command_args": ["curl", "/health", "--deployment", "dpl_exact", "--scope", "team_exact"],
            "environment": {},
        }

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def assert_rejected(self, code: str, **changes) -> None:
        values = {**self.kwargs, **changes}
        with self.assertRaises(ReleaseSafetyViolation) as caught:
            validate_vercel_no_auto_link_preflight(**values)
        self.assertEqual(code, caught.exception.code)

    def test_accepts_exact_binding_and_explicit_curl_deployment(self) -> None:
        result = validate_vercel_no_auto_link_preflight(**self.kwargs)
        self.assertTrue(result["valid"])
        self.assertEqual(0, result["provider_invocations"])
        self.assertNotIn("prj_exact", json.dumps(result))
        self.assertNotIn("team_exact", json.dumps(result))

    def test_rejects_absent_and_auto_created_binding_bytes(self) -> None:
        self.binding.unlink()
        self.assert_rejected("VERCEL_BINDING_MISSING")
        self.binding.write_text(json.dumps({"projectId": "prj_exact", "orgId": "team_exact", "created": True}), encoding="utf-8")
        self.assert_rejected("VERCEL_BINDING_HASH_DRIFT")

    def test_rejects_project_org_and_environment_mismatch(self) -> None:
        self.assert_rejected("VERCEL_PROJECT_BINDING_MISMATCH", expected_project_id="prj_other")
        self.assert_rejected("VERCEL_ORG_BINDING_MISMATCH", expected_org_id="team_other")
        self.assert_rejected(
            "VERCEL_ENV_BINDING_MISMATCH",
            environment={"VERCEL_PROJECT_ID": "prj_other", "VERCEL_ORG_ID": "team_exact"},
        )

    def test_omitted_environment_rejects_ambient_binding_mismatch(self) -> None:
        values = {key: value for key, value in self.kwargs.items() if key != "environment"}
        with mock.patch.dict(
            os.environ,
            {"VERCEL_PROJECT_ID": "prj_other", "VERCEL_ORG_ID": "team_exact"},
            clear=True,
        ):
            with self.assertRaises(ReleaseSafetyViolation) as caught:
                validate_vercel_no_auto_link_preflight(**values)
        self.assertEqual("VERCEL_ENV_BINDING_MISMATCH", caught.exception.code)

    def test_rejects_ambiguous_repo_binding(self) -> None:
        (self.workspace / ".vercel" / "repo.json").write_text(
            json.dumps({"projects": [{"id": "prj_exact", "orgId": "team_exact", "directory": "."}]}),
            encoding="utf-8",
        )
        self.assert_rejected("VERCEL_BINDING_AMBIGUOUS")

    def test_accepts_exact_repository_binding(self) -> None:
        self.binding.unlink()
        repo_binding = self.workspace / ".vercel" / "repo.json"
        repo_binding.write_text(
            json.dumps({"projects": [{"id": "prj_exact", "orgId": "team_exact", "directory": "."}]}),
            encoding="utf-8",
        )
        result = validate_vercel_no_auto_link_preflight(
            **{**self.kwargs, "expected_binding_sha256": hashlib.sha256(repo_binding.read_bytes()).hexdigest()}
        )
        self.assertEqual("repo", result["binding_kind"])

    def test_rejects_reparse_or_symlink_ambiguity(self) -> None:
        with mock.patch("ops.atlas.release_safety_controls._is_link_or_reparse", side_effect=lambda path: path == self.binding):
            self.assert_rejected("VERCEL_BINDING_PATH_AMBIGUOUS")

    def test_rejects_unclassified_implicit_link_and_unsafe_curl_surfaces(self) -> None:
        self.assert_rejected("VERCEL_LINKAGE_MUTATION_COMMAND_FORBIDDEN", command_args=["link", "--yes"])
        self.assert_rejected("VERCEL_COMMAND_SURFACE_UNCLASSIFIED", command_args=["logs", "dpl_exact"])
        self.assert_rejected("VERCEL_COMMAND_TARGET_MISSING", command_args=["curl", "/health", "--scope", "team_exact"])
        for option in ("--yes", "--cwd", "--local-config", "--global-config", "--config", "--project", "--token"):
            self.assert_rejected(
                "VERCEL_COMMAND_OPTION_UNCLASSIFIED",
                command_args=["curl", "/health", "--deployment", "dpl_exact", "--scope", "team_exact", option, "other"],
            )

    def test_rejects_duplicate_or_ambiguous_curl_targeting(self) -> None:
        self.assert_rejected(
            "VERCEL_COMMAND_TARGET_AMBIGUOUS",
            command_args=[
                "curl", "/health", "--deployment", "dpl_exact", "--deployment", "dpl_other", "--scope", "team_exact"
            ],
        )
        self.assert_rejected(
            "VERCEL_COMMAND_TARGET_AMBIGUOUS",
            command_args=[
                "curl", "/health", "--deployment", "dpl_exact", "--scope", "team_exact", "--scope=team_other"
            ],
        )
        self.assert_rejected(
            "VERCEL_COMMAND_PATH_AMBIGUOUS",
            command_args=["curl", "/health", "/other", "--deployment", "dpl_exact", "--scope", "team_exact"],
        )


if __name__ == "__main__":
    unittest.main()
