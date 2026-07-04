from __future__ import annotations

import io
import json
import tempfile
import unittest
from collections import OrderedDict
from pathlib import Path
from unittest import mock

from ops.atlas import projection_freshness as freshness


def _branch_state(
    *,
    staged: list[str] | None = None,
    unstaged: list[str] | None = None,
    untracked: list[str] | None = None,
    parity_status: str = "clean",
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


def _inventory(
    *,
    advisory: list[str] | None = None,
    root_blocking: list[str] | None = None,
    digest_matches: bool = True,
    root_head_matches: bool = True,
) -> OrderedDict[str, object]:
    return OrderedDict(
        [
            ("source_ref", "docs/registry/STACK-REPO-INVENTORY.json"),
            ("available", True),
            ("reported_digest", "sha256:good"),
            ("actual_digest", "sha256:good" if digest_matches else "sha256:bad"),
            ("digest_matches", digest_matches),
            ("markdown_ref", "docs/audits/STACK-REPO-INVENTORY.md"),
            ("markdown_digest_matches", True),
            ("repo_count", 12),
            ("dirty_repo_count", len(root_blocking or [])),
            ("visible_dirty_repo_count", len(advisory or []) + len(root_blocking or [])),
            ("advisory_dirty_repo_count", len(advisory or [])),
            ("root_head_matches", root_head_matches),
            ("root_blocking_dirty_repos", root_blocking or []),
            ("advisory_dirty_repos", advisory or []),
            ("payload", {"repos": [{"logical_id": "fitness", "dirty": bool(advisory), "dirty_blocks_root": False}]}),
        ]
    )


def _stack_lock() -> OrderedDict[str, object]:
    return OrderedDict([("source_ref", "stack.lock.yaml"), ("available", True), ("digest", "sha256:lock"), ("component_count", 1), ("drift", [])])


def _atlas_book() -> OrderedDict[str, object]:
    return OrderedDict([("expected_truth_present", {"marker_current": True, "projection_packet": True, "routing_receipt": True})])


def _receipts() -> OrderedDict[str, object]:
    return OrderedDict([("required_refs", []), ("missing", []), ("complete", True)])


def _manifests(*, next_package: str | None = None) -> OrderedDict[str, object]:
    return OrderedDict(
        [
            ("source_ref", "docs/memory/initiatives/continuity-manifest-ai-work-session-stability-auto-sync-loop.json"),
            ("available", True),
            ("marker_percent", freshness.AI_WORK_SESSION_MARKER_PERCENT),
            ("next_package", next_package or freshness.PROJECTION_PACKET),
            ("current_checkpoint_receipt", freshness.PROJECTION_RECEIPT),
        ]
    )


def _manifests_with_owner_repo_scan_checkpoint() -> OrderedDict[str, object]:
    payload = _manifests()
    payload["current_checkpoint_receipt"] = freshness.OWNER_REPO_RECEIPT_SCAN_RECEIPT
    return payload


def _manifests_with_owner_adoption_threshold_checkpoint() -> OrderedDict[str, object]:
    payload = _manifests()
    payload["current_checkpoint_receipt"] = freshness.OWNER_ADOPTION_THRESHOLD_RECEIPT
    return payload


def _markers(*, packet: str | None = None) -> OrderedDict[str, object]:
    return OrderedDict(
        [
            ("source_ref", "docs/atlas-book/02-lanes-and-markers.md"),
            ("active_lane", "Sandbox Simulation Readiness"),
            ("operator_action", "hold_current_lane"),
            ("next_after_current_marker", "AI Work Session Stability & Auto-Sync Loop"),
            ("next_after_current_percentage", freshness.AI_WORK_SESSION_MARKER_PERCENT),
            ("next_after_current_packet", packet or freshness.PROJECTION_PACKET),
            ("next_after_current_packet_basis_ref", freshness.PROJECTION_RECEIPT),
            ("next_after_current_packet_mode", "bounded read-only worker implementation"),
        ]
    )


def _no_immediate_markers() -> OrderedDict[str, object]:
    return OrderedDict(
        [
            ("source_ref", "docs/atlas-book/02-lanes-and-markers.md"),
            ("active_lane", "Sandbox Simulation Readiness"),
            ("operator_action", freshness.NO_IMMEDIATE_OPERATOR_ACTION),
            ("next_after_current_marker", None),
            ("next_after_current_percentage", None),
            ("next_after_current_packet", None),
            ("next_after_current_packet_basis_ref", None),
            ("next_after_current_packet_mode", None),
        ]
    )


def _proof_state(*, dry_run_only: bool = False) -> OrderedDict[str, object]:
    return OrderedDict(
        [
            ("release_readiness_available", True),
            ("dry_run_refs", ["artifact"] if dry_run_only else []),
            ("protected_refs", [] if dry_run_only else ["protected"]),
            ("protected_proof_explicit", not dry_run_only),
        ]
    )


def _patch_collectors(
    *,
    branch_state: OrderedDict[str, object] | None = None,
    inventory: OrderedDict[str, object] | None = None,
    manifests: OrderedDict[str, object] | None = None,
    markers: OrderedDict[str, object] | None = None,
    proof_state: OrderedDict[str, object] | None = None,
    pr_findings: list[dict[str, object]] | None = None,
):
    return mock.patch.multiple(
        freshness,
        collect_branch_state=mock.Mock(return_value=branch_state or _branch_state()),
        collect_inventory=mock.Mock(return_value=(inventory or _inventory(), [])),
        collect_stack_lock=mock.Mock(return_value=(_stack_lock(), [])),
        collect_atlas_book=mock.Mock(return_value=(_atlas_book(), [])),
        collect_receipts=mock.Mock(return_value=(_receipts(), [])),
        collect_manifests=mock.Mock(return_value=(manifests or _manifests(), [])),
        collect_markers=mock.Mock(return_value=(markers or _markers(), [])),
        collect_pull_requests=mock.Mock(return_value=(OrderedDict([("checked", False), ("stale_refs", [])]), pr_findings or [])),
        collect_proof_state=mock.Mock(return_value=(proof_state or _proof_state(), [])),
        collect_protected_surfaces=mock.Mock(return_value=OrderedDict([("touched", []), ("blocked", [])])),
    )


class AtlasProjectionFreshnessTests(unittest.TestCase):
    def test_root_scope_clean_projection_returns_ok(self) -> None:
        with _patch_collectors():
            report = freshness.build_report(root=Path("C:/ATLAS"), scope="root")
        self.assertEqual(freshness.STATUS_OK, report["status"])
        self.assertTrue(report["safe_to_continue"])

    def test_advisory_owner_lane_dirt_returns_advisory(self) -> None:
        with _patch_collectors(inventory=_inventory(advisory=["fitness"])):
            report = freshness.build_report(root=Path("C:/ATLAS"), scope="owner", owners=["fitness"])
        self.assertEqual(freshness.STATUS_ADVISORY, report["status"])
        self.assertTrue(report["safe_to_continue"])
        self.assertEqual([], report["blockers"])
        self.assertIn("advisory_owner_lane_dirty", {item["code"] for item in report["warnings"]})

    def test_stale_inventory_digest_returns_drift(self) -> None:
        with _patch_collectors(
            inventory=_inventory(digest_matches=False),
        ):
            with mock.patch.object(
                freshness,
                "collect_inventory",
                return_value=(
                    _inventory(digest_matches=False),
                    [freshness._finding("inventory_digest_drift", "digest drift")],
                ),
            ):
                report = freshness.build_report(root=Path("C:/ATLAS"), scope="root")
        self.assertEqual(freshness.STATUS_ADVISORY, report["status"])
        self.assertIn("inventory_digest_drift", {item["code"] for item in report["warnings"]})

    def test_stale_stack_inventory_owner_head_returns_drift(self) -> None:
        with _patch_collectors():
            with mock.patch.object(
                freshness,
                "collect_stack_lock",
                return_value=(
                    OrderedDict([("drift", [{"repo": "playbook"}])]),
                    [freshness._finding("stack_lock_inventory_drift", "lock drift")],
                ),
            ):
                report = freshness.build_report(root=Path("C:/ATLAS"), scope="root")
        self.assertEqual(freshness.STATUS_ADVISORY, report["status"])
        self.assertIn("stack_lock_inventory_drift", {item["code"] for item in report["warnings"]})

    def test_stale_marker_manifest_current_packet_returns_drift(self) -> None:
        stale_packet = "old packet"
        with _patch_collectors(markers=_markers(packet=stale_packet)):
            with mock.patch.object(
                freshness,
                "collect_markers",
                return_value=(
                    _markers(packet=stale_packet),
                    [freshness._finding("selector_next_packet_drift", "selector drift")],
                ),
            ):
                report = freshness.build_report(root=Path("C:/ATLAS"), scope="root")
        self.assertEqual(freshness.STATUS_ADVISORY, report["status"])
        self.assertIn("selector_next_packet_drift", {item["code"] for item in report["warnings"]})

    def test_no_immediate_selector_matches_manifest_hold(self) -> None:
        with _patch_collectors(markers=_no_immediate_markers()):
            report = freshness.build_report(root=Path("C:/ATLAS"), scope="root")

        self.assertEqual(freshness.STATUS_OK, report["status"])
        self.assertEqual(freshness.NO_IMMEDIATE_OPERATOR_ACTION, report["markers"]["operator_action"])
        self.assertEqual(None, report["markers"]["next_after_current_packet"])

    def test_no_immediate_selector_accepts_owner_repo_scan_checkpoint(self) -> None:
        with _patch_collectors(markers=_no_immediate_markers(), manifests=_manifests_with_owner_repo_scan_checkpoint()):
            report = freshness.build_report(root=Path("C:/ATLAS"), scope="root")

        self.assertEqual(freshness.STATUS_OK, report["status"])
        self.assertNotIn("manifest_checkpoint_drift", {item["code"] for item in report["warnings"]})
        self.assertEqual(freshness.OWNER_REPO_RECEIPT_SCAN_RECEIPT, report["manifests"]["current_checkpoint_receipt"])

    def test_no_immediate_selector_accepts_owner_adoption_threshold_checkpoint(self) -> None:
        with _patch_collectors(markers=_no_immediate_markers(), manifests=_manifests_with_owner_adoption_threshold_checkpoint()):
            report = freshness.build_report(root=Path("C:/ATLAS"), scope="root")

        self.assertEqual(freshness.STATUS_OK, report["status"])
        self.assertNotIn("manifest_checkpoint_drift", {item["code"] for item in report["warnings"]})
        self.assertEqual(freshness.OWNER_ADOPTION_THRESHOLD_RECEIPT, report["manifests"]["current_checkpoint_receipt"])

    def test_dry_run_proof_is_not_classified_as_protected(self) -> None:
        with _patch_collectors():
            with mock.patch.object(
                freshness,
                "collect_proof_state",
                return_value=(
                    _proof_state(dry_run_only=True),
                    [freshness._finding("dry_run_not_protected_proof", "dry run only")],
                ),
            ):
                report = freshness.build_report(root=Path("C:/ATLAS"), scope="root")
        self.assertEqual(freshness.STATUS_ADVISORY, report["status"])
        self.assertFalse(report["proof_state"]["protected_proof_explicit"])

    def test_protected_output_path_rejected(self) -> None:
        resolved, error = freshness.validate_output_path(root=Path("C:/ATLAS"), output_path="runtime/out.json")
        self.assertIsNone(resolved)
        self.assertEqual("protected_output_path", error["code"])

    def test_absolute_output_path_rejected(self) -> None:
        resolved, error = freshness.validate_output_path(root=Path("C:/ATLAS"), output_path="C:/tmp/out.json")
        self.assertIsNone(resolved)
        self.assertEqual("absolute_output_path", error["code"])

    def test_strict_returns_nonzero_for_advisory_drift(self) -> None:
        self.assertEqual(1, freshness.report_exit_code(status=freshness.STATUS_ADVISORY, strict=True))

    def test_advisory_status_is_safe_to_continue_when_no_blockers(self) -> None:
        with _patch_collectors():
            with mock.patch.object(
                freshness,
                "collect_inventory",
                return_value=(
                    _inventory(root_head_matches=False),
                    [freshness._finding("inventory_root_head_drift", "root head drift")],
                ),
            ):
                report = freshness.build_report(root=Path("C:/ATLAS"), scope="root")
        self.assertEqual(freshness.STATUS_ADVISORY, report["status"])
        self.assertEqual([], report["blockers"])
        self.assertTrue(report["safe_to_continue"])

    def test_inventory_self_reference_lag_is_not_required_refresh(self) -> None:
        with _patch_collectors():
            with mock.patch.object(
                freshness,
                "collect_inventory",
                return_value=(
                    _inventory(root_head_matches=False),
                    [freshness._finding("inventory_root_head_self_reference_lag", "self reference lag")],
                ),
            ):
                report = freshness.build_report(root=Path("C:/ATLAS"), scope="root")

        self.assertEqual(freshness.STATUS_ADVISORY, report["status"])
        self.assertIn("inventory_root_head_self_reference_lag", {item["code"] for item in report["warnings"]})
        self.assertNotIn("inventory_root_head_self_reference_lag", {item["code"] for item in report["required_refreshes"]})

    def test_blocker_state_returns_nonzero(self) -> None:
        with _patch_collectors(inventory=_inventory(root_blocking=["playbook"])):
            report = freshness.build_report(root=Path("C:/ATLAS"), scope="root")
        self.assertEqual(freshness.STATUS_BLOCKER, report["status"])
        self.assertFalse(report["safe_to_continue"])
        self.assertEqual(2, freshness.report_exit_code(status=report["status"], strict=False))

    def test_deterministic_json_field_ordering(self) -> None:
        with _patch_collectors():
            report = freshness.build_report(root=Path("C:/ATLAS"), scope="root")
        self.assertEqual(
            [
                "schema_version",
                "status",
                "root",
                "branch",
                "head",
                "parity",
                "stack_lock",
                "inventory",
                "atlas_book",
                "receipts",
                "manifests",
                "markers",
                "pull_requests",
                "owner_lanes",
                "proof_state",
                "protected_surfaces",
                "blockers",
                "warnings",
                "required_refreshes",
                "safe_to_continue",
            ],
            list(report.keys()),
        )

    def test_internal_error_classified_as_internal_error(self) -> None:
        with mock.patch.object(freshness, "build_report", side_effect=RuntimeError("boom")):
            stdout = io.StringIO()
            with mock.patch("sys.stdout", stdout), mock.patch.object(freshness, "atlas_root", return_value=Path("C:/ATLAS")):
                code = freshness.main(["--json"])
        payload = json.loads(stdout.getvalue())
        self.assertEqual(3, code)
        self.assertEqual(freshness.STATUS_INTERNAL_ERROR, payload["status"])

    def test_main_writes_output_only_for_root_relative_path(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            output_path = root / "tmp" / "projection.json"
            with _patch_collectors(), mock.patch.object(freshness, "atlas_root", return_value=root):
                stdout = io.StringIO()
                with mock.patch("sys.stdout", stdout):
                    code = freshness.main(["--json", "--output", "tmp/projection.json"])
            self.assertEqual(0, code)
            self.assertTrue(output_path.exists())
            payload = json.loads(output_path.read_text(encoding="utf-8"))
            self.assertEqual(freshness.SCHEMA_VERSION, payload["schema_version"])


if __name__ == "__main__":
    unittest.main()
