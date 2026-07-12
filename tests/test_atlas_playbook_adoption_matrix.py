from __future__ import annotations

import io
import json
import tempfile
import unittest
from collections import OrderedDict
from datetime import datetime, timezone
from pathlib import Path
from unittest import mock

from ops.atlas import playbook_adoption_matrix as matrix


NOW = datetime(2026, 7, 12, 12, 0, tzinfo=timezone.utc)
CURRENT_HEAD = "a" * 40


def _branch_state(
    *,
    parity_status: str = "clean",
    staged: list[str] | None = None,
    unstaged: list[str] | None = None,
    untracked: list[str] | None = None,
) -> OrderedDict[str, object]:
    return OrderedDict(
        [
            ("branch", "main"),
            ("head", "abc123"),
            ("parity", OrderedDict([("status", parity_status), ("behind", 0), ("ahead", 0)])),
            ("staged", staged or []),
            ("unstaged", unstaged or []),
            ("untracked", untracked or []),
        ]
    )


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _minimal_root(root: Path) -> None:
    _write(root / "docs" / "PLAYBOOK_NOTES.md", "# Playbook\n\nCanonical doctrine source.\n")
    _write(root / "docs" / "ops" / "PLAYBOOK-ADOPTION-MATRIX.md", "# Matrix\n\nPlaybook adoption matrix source.\n")
    _write(root / "docs" / "atlas-book" / "01-current-state.md", "Playbook adoption matrix consumes doctrine for continuity routing.\n")
    _write(root / "docs" / "atlas-book" / "02-lanes-and-markers.md", "Playbook selector must gate packet routing.\n")
    _write(root / "docs" / "registry" / "STACK-REPO-INVENTORY.json", json.dumps({"repos": []}))
    _write(root / "docs" / "audits" / "STACK-REPO-INVENTORY.md", "No playbook reference here.\n")
    _write(root / "stack.yaml", "name: atlas\n")
    _write(root / "stack.lock.yaml", "lock: true\n")


def _covered_root(root: Path) -> None:
    _write(root / "docs" / "PLAYBOOK_NOTES.md", "# Playbook\n\nCanonical doctrine source.\n")
    _write(root / "docs" / "ops" / "PLAYBOOK-ADOPTION-MATRIX.md", "# Matrix\n\nPlaybook adoption matrix source.\n")
    _write(root / "docs" / "architecture" / "ATLAS-CORTEX-PLAYBOOK-CODEX.md", "Playbook Cortex contract.\n")
    _write(root / "docs" / "standards" / "WORKER-ORCHESTRATION.md", "Playbook worker orchestration must validate adoption.\n")
    _write(root / "docs" / "atlas-book" / "01-current-state.md", "Playbook adoption matrix consumes doctrine for continuity routing.\n")
    _write(root / "docs" / "atlas-book" / "02-lanes-and-markers.md", "Playbook selector must gate packet routing.\n")
    _write(root / "docs" / "registry" / "STACK-REPO-INVENTORY.json", json.dumps({"playbook": True, "repos": []}))
    _write(root / "docs" / "audits" / "STACK-REPO-INVENTORY.md", "Playbook adoption matrix inventory projection.\n")
    _write(root / "stack.yaml", "playbook: true\n")
    _write(root / "stack.lock.yaml", "playbook: true\n")


def _inventory_row(repo_id: str, *, declaration: str | None = None, profile: str | None = None, version: str | None = None, head: str = CURRENT_HEAD) -> dict[str, object]:
    row: dict[str, object] = {"logical_id": repo_id, "local_path": f"repos/{repo_id}", "remote_url": f"https://example.test/{repo_id}.git", "current_commit": head, "current_ref": "main", "trust_class": "trusted", "exists": True, "is_git_root": True}
    if declaration is not None:
        row["playbook_adoption_status"] = declaration
    if profile is not None:
        row["playbook_adoption_profile"] = profile
    if version is not None:
        row["playbook_adoption_version"] = version
    return row


def _inventory(*rows: dict[str, object]) -> dict[str, object]:
    return {"repos": list(rows)}


def _write_owner_evidence(root: Path, repo_id: str, *, version: str = "1.0.0", verified_at: str | None = "2026-07-12T11:00:00Z", owner_head: str = CURRENT_HEAD, verification: bool = True) -> None:
    adoption = {"artifact_id": f"{repo_id}_playbook_adoption_evidence_v1", "generated_at": "2026-07-12T11:00:00Z", "repo": {"repo_id": repo_id, "role": "vertical_owner_repo", "repo_identity": "remote", "owner_head": owner_head, "owner_ref": "main"}, "contract_claim": {"contract_id": "playbook_convergence_contract", "contract_version": version, "source_repo_id": "playbook", "source_export_path": "exports/playbook.contract.example.v1.json", "claim_state": "declared"}, "summary": {"adoption_status": "adopted", "verification_state": "targeted", "continuity_status": "structured", "drift_status": "none_detected"}, "implemented_patterns": [{"id": "owner_truth", "status": "implemented", "notes": []}], "adoption_checks": [{"id": "root_validation", "status": "implemented", "notes": []}], "continuity": {"structured_handoff_required": True, "transcript_role": "trace_only"}, "evidence_refs": ["docs/ops/PLAYBOOK-ADOPTION.md"]}
    _write(root / "repos" / repo_id / "exports" / f"{repo_id}.playbook.adoption.evidence.v1.json", json.dumps(adoption))
    if not verification:
        return
    report = {"artifact_id": f"{repo_id}_playbook_verification_report_v1", "generated_at": verified_at, "repo": {"repo_id": repo_id, "repo_identity": "remote", "owner_head": owner_head, "owner_ref": "main"}, "summary": {"adoption_status": "adopted", "verification_status": "verified", "blocking_gaps": [], "last_verified_at": verified_at}, "scope": {"verification_kind": "targeted", "covered_surfaces": ["owner adoption contract"], "notes": []}, "criteria": {"adoption_export": {"status": "passed", "evidence_refs": ["exports/adoption.json"]}, "adoption_test": {"status": "passed", "evidence_refs": ["tests/adoption.test"]}, "verification_path": {"status": "passed", "commands": ["python -m unittest"], "evidence_refs": ["tests/verification.test"]}}, "evidence_refs": ["exports/verification.json"]}
    _write(root / "repos" / repo_id / "exports" / f"{repo_id}.playbook.verification.report.v1.json", json.dumps(report))


class AtlasPlaybookAdoptionMatrixTests(unittest.TestCase):
    def test_clean_root_playbook_source_scan_returns_ok(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            _covered_root(root)
            with mock.patch.object(matrix, "collect_branch_state", return_value=_branch_state()), mock.patch.object(
                matrix, "collect_selector_state", return_value=({}, [])
            ):
                report = matrix.build_report(root=root)

        self.assertEqual(matrix.STATUS_OK, report["status"])
        self.assertTrue(report["safe_to_continue"])
        self.assertGreaterEqual(len(report["playbook_sources"]), 2)

    def test_source_only_doctrine_is_documented_not_consumed(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            _write(root / "docs" / "PLAYBOOK_NOTES.md", "# Playbook\n\nDoctrine only.\n")
            with mock.patch.object(matrix, "collect_branch_state", return_value=_branch_state()), mock.patch.object(
                matrix, "collect_selector_state", return_value=({}, [])
            ):
                report = matrix.build_report(root=root)

        self.assertEqual(["documented_doctrine"], [item["classification"] for item in report["playbook_sources"]])
        self.assertEqual(0, report["consumer_matrix"]["counts"]["consumed_doctrine"])
        self.assertEqual(0, report["consumer_matrix"]["counts"]["enforced_doctrine"])

    def test_receipt_reference_is_classified_as_consumed(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            _minimal_root(root)
            _write(root / "docs" / "ops" / "AI-WORK-SESSION-PLAYBOOK-RECEIPT.md", "Playbook receipt projects matrix truth into a handoff packet.\n")
            with mock.patch.object(matrix, "collect_branch_state", return_value=_branch_state()), mock.patch.object(
                matrix, "collect_selector_state", return_value=({}, [])
            ):
                report = matrix.build_report(root=root)

        classes = {item["classification"] for item in report["adoption_surfaces"]}
        self.assertIn("consumed_doctrine", classes)

    def test_unrelated_ai_work_session_receipt_is_not_a_playbook_gap(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            _covered_root(root)
            _write(
                root / "docs" / "ops" / "AI-WORK-SESSION-STABILITY-AUTO-SYNC-LOOP-CLOSEOUT-ONLY-2026-07-06.md",
                "Closeout receipt for root parity and validation safety.\n",
            )
            with mock.patch.object(matrix, "collect_branch_state", return_value=_branch_state()), mock.patch.object(
                matrix, "collect_selector_state", return_value=({}, [])
            ):
                report = matrix.build_report(root=root)

        gap_refs = {item["details"]["ref"] for item in report["gaps"]}
        self.assertNotIn(
            "docs/ops/AI-WORK-SESSION-STABILITY-AUTO-SYNC-LOOP-CLOSEOUT-ONLY-2026-07-06.md",
            gap_refs,
        )

    def test_playbook_ai_work_session_receipt_remains_a_consumer_surface(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            _covered_root(root)
            _write(
                root / "docs" / "ops" / "AI-WORK-SESSION-STABILITY-AUTO-SYNC-LOOP-PLAYBOOK-2026-07-06.md",
                "Playbook adoption matrix consumes doctrine for handoff packet routing.\n",
            )
            with mock.patch.object(matrix, "collect_branch_state", return_value=_branch_state()), mock.patch.object(
                matrix, "collect_selector_state", return_value=({}, [])
            ):
                report = matrix.build_report(root=root)

        refs = {item["ref"] for item in report["adoption_surfaces"]}
        self.assertIn("docs/ops/AI-WORK-SESSION-STABILITY-AUTO-SYNC-LOOP-PLAYBOOK-2026-07-06.md", refs)

    def test_selector_reference_is_operational_adoption(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            _minimal_root(root)
            selector_state = {"next_after_current_packet": "Playbook adoption matrix worker"}
            with mock.patch.object(matrix, "collect_branch_state", return_value=_branch_state()), mock.patch.object(
                matrix, "collect_selector_state", return_value=(selector_state, [])
            ):
                report = matrix.build_report(root=root)

        selector_rows = [item for item in report["adoption_surfaces"] if item["role"] == "selector"]
        self.assertEqual("enforced_doctrine", selector_rows[0]["classification"])

    def test_missing_adoption_is_advisory_gap(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            _minimal_root(root)
            with mock.patch.object(matrix, "collect_branch_state", return_value=_branch_state()), mock.patch.object(
                matrix, "collect_selector_state", return_value=({}, [])
            ):
                report = matrix.build_report(root=root)

        self.assertEqual(matrix.STATUS_ADVISORY, report["status"])
        self.assertIn("missing_adoption", {item["code"] for item in report["gaps"]})

    def test_strict_returns_nonzero_for_advisory_gap(self) -> None:
        self.assertEqual(1, matrix.report_exit_code(status=matrix.STATUS_ADVISORY, strict=True))

    def test_blocker_state_returns_nonzero(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            with mock.patch.object(matrix, "collect_branch_state", return_value=_branch_state()), mock.patch.object(
                matrix, "collect_selector_state", return_value=({}, [])
            ):
                report = matrix.build_report(root=root)

        self.assertEqual(matrix.STATUS_BLOCKER, report["status"])
        self.assertEqual(2, matrix.report_exit_code(status=report["status"], strict=False))

    def test_protected_output_path_rejected(self) -> None:
        resolved, error = matrix.validate_output_path(root=Path("C:/ATLAS"), output_path="secrets/out.json")
        self.assertIsNone(resolved)
        self.assertEqual("protected_output_path", error["code"])

    def test_absolute_output_path_rejected(self) -> None:
        resolved, error = matrix.validate_output_path(root=Path("C:/ATLAS"), output_path="C:/tmp/out.json")
        self.assertIsNone(resolved)
        self.assertEqual("absolute_output_path", error["code"])

    def test_deterministic_json_field_ordering(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            _minimal_root(root)
            with mock.patch.object(matrix, "collect_branch_state", return_value=_branch_state()), mock.patch.object(
                matrix, "collect_selector_state", return_value=({}, [])
            ):
                report = matrix.build_report(root=root)

        self.assertEqual(
            [
                "schema_version",
                "status",
                "root",
                "branch",
                "head",
                "parity",
                "playbook_sources",
                "adoption_surfaces",
                "consumer_matrix",
                "non_consumers",
                "doctrine_signals",
                "pattern_signals",
                "failure_mode_signals",
                "cortex_substrate_candidates",
                "owner_lane_adoption",
                "gaps",
                "blockers",
                "warnings",
                "required_followups",
                "safe_to_continue",
            ],
            list(report.keys()),
        )

    def test_owner_scope_remains_read_only_and_operational(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            _minimal_root(root)
            inventory = _inventory(_inventory_row("fitness"))
            inventory["repos"][0]["notes"] = "Playbook adopted"
            _write(root / "docs" / "registry" / "STACK-REPO-INVENTORY.json", json.dumps(inventory))
            with mock.patch.object(matrix, "collect_branch_state", return_value=_branch_state()), mock.patch.object(
                matrix, "collect_selector_state", return_value=({}, [])
            ):
                report = matrix.build_report(root=root, scope="owner", owners=["fitness"])

        self.assertEqual(matrix.STATUS_ADVISORY, report["status"])
        self.assertTrue(report["owner_lane_adoption"]["read_only"])
        self.assertEqual("missing", report["owner_lane_adoption"]["rows"][0]["classification"])
        self.assertEqual("missing_adoption", report["owner_lane_adoption"]["rows"][0]["legacy_classification"])

    def test_keyword_only_evidence_is_negative_safe(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            empty = _inventory_row("empty", declaration="")
            absent = _inventory_row("absent")
            empty["playbook_notes"] = "Playbook verified adoption"
            absent["notes"] = "Playbook adoption evidence"
            rows = matrix.collect_owner_lane_adoption(Path(temp_dir), [], now=NOW, inventory_payload=_inventory(empty, absent))["rows"]
        self.assertEqual(["missing", "missing"], [row["classification"] for row in rows])
        self.assertNotIn("owner_lane_advisory_adoption", {row["classification"] for row in rows})

    def test_not_claimed_is_negative_safe(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            row = matrix.collect_owner_lane_adoption(Path(temp_dir), [], now=NOW, inventory_payload=_inventory(_inventory_row("owner", declaration="not-claimed")))["rows"][0]
        self.assertEqual("not_claimed", row["classification"])

    def test_declared_without_current_receipt_is_declared(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            row = matrix.collect_owner_lane_adoption(Path(temp_dir), [], now=NOW, inventory_payload=_inventory(_inventory_row("owner", declaration="declared", profile="playbook_convergence_contract", version="1.0.0")))["rows"][0]
        self.assertEqual("declared", row["classification"])

    def test_validated_fresh_current_evidence_is_verified(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            _write_owner_evidence(root, "owner")
            row = matrix.collect_owner_lane_adoption(root, [], now=NOW, inventory_payload=_inventory(_inventory_row("owner", declaration="declared", profile="playbook_convergence_contract", version="1.0.0")))["rows"][0]
        self.assertEqual("verified", row["classification"])
        self.assertEqual(("valid", "fresh", "current"), (row["evidence_validation"], row["freshness"], row["head_correlation"]))

    def test_old_receipt_is_stale(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            _write_owner_evidence(root, "owner", verified_at="2026-05-01T11:00:00Z")
            row = matrix.collect_owner_lane_adoption(root, [], now=NOW, inventory_payload=_inventory(_inventory_row("owner", declaration="declared", profile="playbook_convergence_contract", version="1.0.0")))["rows"][0]
        self.assertEqual("stale", row["classification"])

    def test_mismatched_owner_head_is_stale(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            _write_owner_evidence(root, "owner", owner_head="b" * 40)
            row = matrix.collect_owner_lane_adoption(root, [], now=NOW, inventory_payload=_inventory(_inventory_row("owner", declaration="declared", profile="playbook_convergence_contract", version="1.0.0")))["rows"][0]
        self.assertEqual("stale", row["classification"])

    def test_manifest_owner_version_mismatch_is_conflicting(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            _write_owner_evidence(root, "owner", version="1.0.0")
            row = matrix.collect_owner_lane_adoption(root, [], now=NOW, inventory_payload=_inventory(_inventory_row("owner", declaration="declared", profile="playbook_convergence_contract", version="2.0.0")))["rows"][0]
        self.assertEqual("conflicting", row["classification"])

    def test_malformed_owner_evidence_is_blocked(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            _write(root / "repos" / "owner" / "exports" / "owner.playbook.adoption.evidence.v1.json", "{")
            row = matrix.collect_owner_lane_adoption(root, [], now=NOW, inventory_payload=_inventory(_inventory_row("owner", declaration="declared", profile="playbook_convergence_contract", version="1.0.0")))["rows"][0]
        self.assertEqual("blocked", row["classification"])

    def test_discordos_and_foundation_remain_not_claimed(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            rows = matrix.collect_owner_lane_adoption(Path(temp_dir), [], now=NOW, inventory_payload=_inventory(_inventory_row("discordos", declaration="not-claimed"), _inventory_row("foundation", declaration="not-claimed"), _inventory_row("cortex")))["rows"]
        classes = {row["component_id"]: row["classification"] for row in rows}
        self.assertEqual("not_claimed", classes["discordos"])
        self.assertEqual("not_claimed", classes["foundation"])
        self.assertEqual("missing", classes["cortex"])

    def test_owner_rows_are_deterministic_and_bounded(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            result = matrix.collect_owner_lane_adoption(Path(temp_dir), [], now=NOW, inventory_payload=_inventory(_inventory_row("zeta"), _inventory_row("alpha")))
        self.assertEqual(["alpha", "zeta"], [row["component_id"] for row in result["rows"]])
        self.assertEqual(set(matrix.OWNER_OPERATIONAL_STATUSES), set(result["legacy_mapping"]))

    def test_cortex_substrate_candidate_extraction(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            _minimal_root(root)
            _write(
                root / "docs" / "ops" / "AI-WORK-SESSION-PLAYBOOK-CORTEX.md",
                "## Rule\n\nPlaybook prompt-governance contract.\n\n## Pattern\n\nReusable handoff example.\n\n## Failure Mode\n\nDoctrine echo inflation.\n",
            )
            with mock.patch.object(matrix, "collect_branch_state", return_value=_branch_state()), mock.patch.object(
                matrix, "collect_selector_state", return_value=({}, [])
            ):
                report = matrix.build_report(root=root)

        self.assertTrue(report["cortex_substrate_candidates"])
        self.assertTrue(all(item["read_only"] for item in report["cortex_substrate_candidates"]))

    def test_main_writes_output_only_for_root_relative_path(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            _minimal_root(root)
            output_path = root / "tmp" / "matrix.json"
            with mock.patch.object(matrix, "atlas_root", return_value=root), mock.patch.object(
                matrix, "collect_branch_state", return_value=_branch_state()
            ), mock.patch.object(matrix, "collect_selector_state", return_value=({}, [])):
                stdout = io.StringIO()
                with mock.patch("sys.stdout", stdout):
                    code = matrix.main(["--json", "--output", "tmp/matrix.json"])
            self.assertEqual(0, code)
            self.assertTrue(output_path.exists())
            payload = json.loads(output_path.read_text(encoding="utf-8"))
            self.assertEqual(matrix.SCHEMA_VERSION, payload["schema_version"])


if __name__ == "__main__":
    unittest.main()
