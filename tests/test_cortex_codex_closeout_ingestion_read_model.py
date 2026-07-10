from __future__ import annotations

import io
import json
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import patch

from ops.cortex.codex_closeout_ingestion_read_model import (
    AUTHORITY_DENIALS,
    DUAL_MODE_MARKER,
    NEXT_WORKER_PACKET,
    RECONCILIATION_PACKET,
    SCHEMA_VERSION,
    TOP_LEVEL_FIELDS,
    build_closeout_read_model,
    build_schema_only_payload,
    main,
    validate_output_path,
)


HEAD = "a" * 40
OLD_HEAD = "b" * 40


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _write_json(path: Path, payload: object) -> None:
    _write(path, json.dumps(payload, indent=2) + "\n")


class CodexCloseoutIngestionReadModelTests(unittest.TestCase):
    def _temp_root(self, *, validation_warning: int = 0) -> Path:
        temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(temp_dir.cleanup)
        root = Path(temp_dir.name)
        _write(
            root / "docs/atlas-book/02-lanes-and-markers.md",
            f"# Markers\n- {DUAL_MODE_MARKER}: `30%`\n",
        )
        _write_json(
            root / "docs/memory/initiatives/continuity-manifest-cortex-dual-mode-replacement-readiness.json",
            {
                "contract_version": "atlas.initiative.v1",
                "metadata": {
                    "next_package_ladder": [
                        {
                            "package": NEXT_WORKER_PACKET,
                        }
                    ]
                },
            },
        )
        _write_json(
            root / "runtime/receipts/validation/stack-validation.latest.json",
            {"summary": {"critical": 0, "error": 0, "warning": validation_warning, "info": 0}},
        )
        _write(root / "docs/ops/TEST-RECEIPT.md", "# Test receipt\n")
        return root

    def _verified_closeout(self) -> dict[str, object]:
        return {
            "message_id": "closeout-1",
            "captured_at": "2026-07-10T00:00:00-04:00",
            "branch": "main",
            "head": HEAD,
            "parity": {"behind": 0, "ahead": 0},
            "commits": [HEAD],
            "receipts_created": ["docs/ops/TEST-RECEIPT.md"],
            "validation": {"critical": 0, "error": 0, "warning": 0, "info": 0},
            "marker_changes": [{"marker": DUAL_MODE_MARKER, "from": 20, "to": 30}],
            "current_marker_board": {DUAL_MODE_MARKER: 30},
            "next_exact_packet": NEXT_WORKER_PACKET,
        }

    def _write_verified_source(self, root: Path) -> Path:
        path = root / "tmp/atlas/closeout.json"
        _write_json(path, self._verified_closeout())
        return path

    def _git_patches(self, *, commit_exists: bool = True):
        return (
            patch("ops.cortex.codex_closeout_ingestion_read_model.collect_git_state", return_value=("main", HEAD)),
            patch(
                "ops.cortex.codex_closeout_ingestion_read_model.collect_git_parity",
                return_value={"behind": 0, "ahead": 0, "raw": "0\t0"},
            ),
            patch("ops.cortex.codex_closeout_ingestion_read_model.commit_exists", return_value=commit_exists),
        )

    def test_valid_structured_closeout_verifies_core_claims(self) -> None:
        root = self._temp_root()
        self._write_verified_source(root)
        git_state, git_parity, git_commit = self._git_patches()

        with git_state, git_parity, git_commit:
            payload = build_closeout_read_model(
                root=root,
                sources=["tmp/atlas/closeout.json"],
                verify_git=True,
                verify_receipts=True,
                verify_marker_board=True,
            )

        self.assertEqual(SCHEMA_VERSION, payload["schema_version"])
        self.assertEqual("ok", payload["status"])
        self.assertTrue(payload["safe_to_use"])
        self.assertEqual(list(TOP_LEVEL_FIELDS), list(payload.keys()))
        self.assertEqual(["tmp/atlas/closeout.json"], payload["source_refs"])
        self.assertEqual(1, len(payload["closeouts"]))
        self.assertEqual(NEXT_WORKER_PACKET, payload["next_packet"])
        self.assertEqual(RECONCILIATION_PACKET, payload["next_recommended_packet"])
        self.assertEqual(list(AUTHORITY_DENIALS), payload["authority_denials"])
        self.assertEqual(9, payload["verification_summary"]["verified_claim_count"])
        self.assertEqual(0, payload["verification_summary"]["unverified_claim_count"])
        self.assertEqual(0, payload["verification_summary"]["conflict_count"])
        self.assertEqual(1, len(payload["marker_deltas"]))
        evidence_classes = {claim["field"]: claim["evidence_class"] for claim in payload["verified_claims"]}
        self.assertEqual("receipt_backed", evidence_classes["receipts_created"])
        self.assertEqual("git_verified", evidence_classes["head"])
        self.assertEqual("validation_verified", evidence_classes["validation"])
        self.assertEqual("manifest_verified", evidence_classes["next_exact_packet"])
        json.dumps(payload, sort_keys=True)

    def test_markdown_text_closeout_is_accepted_as_advisory(self) -> None:
        root = self._temp_root()
        _write(
            root / "tmp/atlas/closeout.md",
            "\n".join(
                [
                    "message_id: text-closeout",
                    "branch: main",
                    f"head: {HEAD}",
                    f"{DUAL_MODE_MARKER}: `30%`",
                    f"next exact packet: {NEXT_WORKER_PACKET}",
                    "This closeout prose is useful but not final truth.",
                ]
            )
            + "\n",
        )
        git_state, git_parity, git_commit = self._git_patches()

        with git_state, git_parity, git_commit:
            payload = build_closeout_read_model(
                root=root,
                sources=["tmp/atlas/closeout.md"],
                verify_git=True,
                verify_marker_board=True,
            )

        self.assertEqual("advisory_gap", payload["status"])
        self.assertEqual(1, len(payload["closeouts"]))
        self.assertTrue(any(claim["field"] == "prose" for claim in payload["unverified_claims"]))

    def test_conflict_stale_missing_receipt_and_missing_commit_detection(self) -> None:
        root = self._temp_root()
        _write_json(
            root / "tmp/atlas/conflict.json",
            {
                "message_id": "conflict",
                "branch": "feature",
                "head": OLD_HEAD,
                "commits": ["deadbeef"],
                "receipts_created": ["docs/ops/MISSING.md"],
                "current_marker_board": {DUAL_MODE_MARKER: 20},
                "next_exact_packet": "Wrong packet",
            },
        )
        git_state = patch("ops.cortex.codex_closeout_ingestion_read_model.collect_git_state", return_value=("main", HEAD))
        git_parity = patch(
            "ops.cortex.codex_closeout_ingestion_read_model.collect_git_parity",
            return_value={"behind": 0, "ahead": 0, "raw": "0\t0"},
        )

        def fake_commit_exists(_root: Path, commit: str) -> bool:
            return commit == OLD_HEAD

        with git_state, git_parity, patch("ops.cortex.codex_closeout_ingestion_read_model.commit_exists", side_effect=fake_commit_exists):
            payload = build_closeout_read_model(
                root=root,
                sources=["tmp/atlas/conflict.json"],
                verify_git=True,
                verify_receipts=True,
                verify_marker_board=True,
            )

        self.assertEqual("conflict", payload["status"])
        self.assertFalse(payload["safe_to_use"])
        conflict_fields = {claim["field"] for claim in payload["conflicts"]}
        self.assertIn("branch", conflict_fields)
        self.assertIn("commits", conflict_fields)
        self.assertIn("current_marker_board", conflict_fields)
        self.assertIn("next_exact_packet", conflict_fields)
        self.assertEqual("head", payload["stale_claims"][0]["field"])
        self.assertEqual("missing_receipt", payload["missing_receipts"][0]["code"])

    def test_duplicate_closeouts_are_deduped_by_message_id(self) -> None:
        root = self._temp_root()
        duplicate = self._verified_closeout()
        duplicate["head"] = OLD_HEAD
        _write_json(root / "tmp/atlas/duplicates.json", {"closeouts": [self._verified_closeout(), duplicate]})
        git_state, git_parity, git_commit = self._git_patches()

        with git_state, git_parity, git_commit:
            payload = build_closeout_read_model(
                root=root,
                sources=["tmp/atlas/duplicates.json"],
                verify_git=True,
                verify_receipts=True,
                verify_marker_board=True,
            )

        self.assertEqual("ok", payload["status"])
        self.assertEqual(1, len(payload["closeouts"]))
        self.assertEqual(HEAD, payload["closeouts"][0]["head"])

    def test_utf8_bom_json_closeout_is_accepted(self) -> None:
        root = self._temp_root()
        path = root / "tmp/atlas/bom-closeout.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(self._verified_closeout(), indent=2) + "\n", encoding="utf-8-sig")
        git_state, git_parity, git_commit = self._git_patches()

        with git_state, git_parity, git_commit:
            payload = build_closeout_read_model(
                root=root,
                sources=["tmp/atlas/bom-closeout.json"],
                verify_git=True,
                verify_receipts=True,
                verify_marker_board=True,
            )

        self.assertEqual("ok", payload["status"])
        self.assertEqual(1, len(payload["closeouts"]))

    def test_source_and_output_path_guards(self) -> None:
        root = self._temp_root()

        blocked_sources = (
            "runtime/transcripts/session.json",
            "repos/fawxzzy-fitness/closeout.json",
            "tmp/atlas/.env.closeout",
            "tmp/atlas/vercel-live-data.json",
            str(root / "tmp/atlas/closeout.json"),
        )
        for source in blocked_sources:
            payload = build_closeout_read_model(root=root, sources=[source])
            self.assertEqual("blocker", payload["status"], source)

        allowed, error = validate_output_path(root, "tmp/atlas/out.json")
        self.assertIsNotNone(allowed)
        self.assertIsNone(error)

        for output in ("docs/ops/out.json", "tmp/out.json", "secrets/out.json", "../out.json", str(root / "tmp/atlas/out.json")):
            allowed, error = validate_output_path(root, output)
            self.assertIsNone(allowed, output)
            self.assertIsNotNone(error, output)

    def test_main_write_schema_and_strict_behaviour(self) -> None:
        root = self._temp_root()
        self._write_verified_source(root)
        output = root / "tmp/atlas/out.json"
        git_state, git_parity, git_commit = self._git_patches()

        with patch("ops.cortex.codex_closeout_ingestion_read_model.atlas_root", return_value=root), git_state, git_parity, git_commit:
            stdout = io.StringIO()
            with redirect_stdout(stdout):
                exit_code = main(["--json", "--source", "tmp/atlas/closeout.json", "--verify-git", "--verify-receipts", "--verify-marker-board"])

        self.assertEqual(0, exit_code)
        self.assertFalse(output.exists())
        self.assertEqual("ok", json.loads(stdout.getvalue())["status"])

        git_state, git_parity, git_commit = self._git_patches()
        with patch("ops.cortex.codex_closeout_ingestion_read_model.atlas_root", return_value=root), git_state, git_parity, git_commit:
            stdout = io.StringIO()
            with redirect_stdout(stdout):
                exit_code = main(
                    [
                        "--json",
                        "--source",
                        "tmp/atlas/closeout.json",
                        "--output",
                        "tmp/atlas/out.json",
                        "--strict",
                        "--verify-git",
                        "--verify-receipts",
                        "--verify-marker-board",
                    ]
                )

        self.assertEqual(0, exit_code)
        self.assertTrue(output.exists())
        self.assertEqual("ok", json.loads(output.read_text(encoding="utf-8"))["status"])

        with patch("ops.cortex.codex_closeout_ingestion_read_model.atlas_root", return_value=root):
            stdout = io.StringIO()
            with redirect_stdout(stdout):
                exit_code = main(["--json", "--schema-only"])
        self.assertEqual(0, exit_code)
        self.assertEqual(SCHEMA_VERSION, json.loads(stdout.getvalue())["schema_version"])

        with patch("ops.cortex.codex_closeout_ingestion_read_model.atlas_root", return_value=root):
            stdout = io.StringIO()
            with redirect_stdout(stdout):
                exit_code = main(["--json", "--source", "tmp/atlas/missing.json", "--strict"])
        self.assertEqual(2, exit_code)
        self.assertEqual("blocker", json.loads(stdout.getvalue())["status"])

    def test_schema_only_and_validation_warning_count_are_deterministic(self) -> None:
        root = self._temp_root(validation_warning=3)
        self._write_verified_source(root)
        closeout = self._verified_closeout()
        closeout["validation"] = {"critical": 0, "error": 0, "warning": 3, "info": 0}
        _write_json(root / "tmp/atlas/warning-closeout.json", closeout)
        git_state, git_parity, git_commit = self._git_patches()

        with git_state, git_parity, git_commit:
            first = build_closeout_read_model(
                root=root,
                sources=["tmp/atlas/warning-closeout.json"],
                verify_git=True,
                verify_receipts=True,
                verify_marker_board=True,
            )
        git_state, git_parity, git_commit = self._git_patches()
        with git_state, git_parity, git_commit:
            second = build_closeout_read_model(
                root=root,
                sources=["tmp/atlas/warning-closeout.json"],
                verify_git=True,
                verify_receipts=True,
                verify_marker_board=True,
            )

        self.assertEqual(first, second)
        self.assertEqual(3, first["verification_summary"]["validation_warning_count"])
        self.assertEqual([], first["warnings"])
        schema_payload = build_schema_only_payload(root=root)
        self.assertEqual(list(TOP_LEVEL_FIELDS), list(schema_payload.keys()))


if __name__ == "__main__":
    unittest.main()
