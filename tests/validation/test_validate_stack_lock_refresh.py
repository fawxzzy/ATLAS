from __future__ import annotations

import tempfile
import unittest
from contextlib import ExitStack
from pathlib import Path
from unittest.mock import patch

from ops.stack.generate_lockfile import (
    STACK_LOCK_SCHEMA_VERSION,
    describe_lock_payload_drift,
    included_repo_ids,
    normalize_lock_payload,
    render_lockfile_bytes,
)
from ops.validation.validate_stack import (
    build_findings,
    classify_root_lock_refresh_state,
    describe_stack_lock_drift,
)


OLD_ROOT_COMMIT = "1" * 40
NEW_ROOT_COMMIT = "2" * 40
CHILD_COMMIT = "3" * 40


def _component(*, path: str, role: str, status: str, ref: str, commit: str) -> dict[str, object]:
    return {
        "path": path,
        "role": role,
        "status": status,
        "remote": None,
        "ref_type": "branch",
        "ref": ref,
        "commit": commit,
        "dirty": False,
        "trust_class": "trusted",
        "release_eligible": False,
    }


def _lock_payload(
    root_commit: str,
    *,
    stack_manifest_digest: str = "sha256:manifest-a",
    child_commit: str | None = None,
) -> dict[str, object]:
    components: dict[str, dict[str, object]] = {
        "stack": _component(
            path=".",
            role="operator-layer",
            status="active",
            ref="main",
            commit=root_commit,
        )
    }
    if child_commit is not None:
        components["child"] = _component(
            path="repos/child",
            role="application",
            status="active",
            ref="main",
            commit=child_commit,
        )
    return normalize_lock_payload(
        {
            "schema_version": STACK_LOCK_SCHEMA_VERSION,
            "stack_manifest_path": "stack.yaml",
            "stack_manifest_digest": stack_manifest_digest,
            "component_count": len(components),
            "components": components,
            "excluded_surfaces": {},
        }
    )


def _canonical_lock(
    root: Path,
    payload: dict[str, object],
    *,
    dirty_actual: bool,
    dirty_effective: bool,
    modified_paths: list[str],
    self_refresh_only: bool,
) -> dict[str, object]:
    return {
        "payload": payload,
        "bytes": render_lockfile_bytes(payload),
        "lockfile_path": root / "stack.lock.yaml",
        "stack_root": {
            "repo_id": "stack",
            "lockfile_path": root / "stack.lock.yaml",
            "lockfile_rel": "stack.lock.yaml",
            "modified_paths": modified_paths,
            "dirty_actual": dirty_actual,
            "dirty_effective": dirty_effective,
            "self_refresh_only": self_refresh_only,
        },
    }


class ValidateStackRootLockRefreshTests(unittest.TestCase):
    def _temp_root(self) -> Path:
        temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(temp_dir.cleanup)
        # Resolve immediately: on some hosted CI runners (observed on
        # GitHub Actions windows-latest) the raw tempfile path uses a
        # short (8.3-style) alias (e.g. "RUNNER~1") that differs from the
        # long-form path production code obtains via `Path.resolve()`
        # (e.g. via `stack_file.parent.resolve()` in validate_stack.py).
        # Without resolving here, identity/membership comparisons against
        # production-computed paths fail purely on path-form mismatch,
        # not on any real logic difference.
        root = Path(temp_dir.name).resolve()
        (root / "AGENTS.md").write_text("# temp\n", encoding="utf-8")
        (root / "README-STACK.md").write_text("# temp\n", encoding="utf-8")
        return root

    def _config(self) -> dict[str, object]:
        return {
            "repo_registry": {
                "stack": {
                    "path": ".",
                    "role": "operator-layer",
                    "status": "active",
                }
            },
            "stack_lock": {
                "path": "stack.lock.yaml",
            },
        }

    def _base_patchers(self) -> list[object]:
        return [
            patch("ops.validation.validate_stack.validate_atlas_topology_contract_files", return_value=(None, None, [])),
            patch("ops.validation.validate_stack.validate_tool_registry", return_value=[]),
            patch("ops.validation.validate_stack.validate_subsystem_registry", return_value=[]),
            patch("ops.validation.validate_stack.validate_execution_receipt_repairs", return_value=[]),
            patch("ops.validation.validate_stack.validate_playbook_enforcement_tracking", return_value=[]),
            patch("ops.validation.validate_stack.validate_verta_trust_gate", return_value=[]),
            patch("ops.validation.validate_stack.validate_working_memory", return_value=[]),
            patch("ops.validation.validate_stack.validate_world_model_state", return_value=[]),
            patch("ops.validation.validate_stack.validate_proposed_sessions", return_value=[]),
            patch("ops.validation.validate_stack.iter_relative_directory_targets", return_value=[]),
            patch("ops.validation.validate_stack.discover_unregistered_git_roots", return_value=[]),
            patch("ops.validation.validate_stack.validate_gitdir_hygiene", return_value=[]),
            patch("ops.validation.validate_stack.collect_text_scan_roots", return_value=[]),
            patch("ops.validation.validate_stack.iter_scan_files", return_value=[]),
            patch("ops.validation.validate_stack.repo_is_git_root", return_value=True),
        ]

    def test_pending_root_lock_refresh_remains_info(self) -> None:
        root = self._temp_root()
        stack_file = root / "stack.yaml"
        lockfile_path = root / "stack.lock.yaml"
        payload = _lock_payload(OLD_ROOT_COMMIT)
        lockfile_path.write_bytes(render_lockfile_bytes(payload))
        canonical_lock = _canonical_lock(
            root,
            payload,
            dirty_actual=True,
            dirty_effective=False,
            modified_paths=["stack.lock.yaml"],
            self_refresh_only=True,
        )

        with ExitStack() as stack:
            for patcher in self._base_patchers():
                stack.enter_context(patcher)
            stack.enter_context(
                patch(
                    "ops.validation.validate_stack.build_canonical_lockfile_artifacts",
                    return_value=canonical_lock,
                )
            )
            stack.enter_context(
                patch("ops.validation.validate_stack.verify_locked_ref", return_value=None)
            )
            findings = build_findings(stack_file, self._config(), lock_file_override=lockfile_path)

        categories = {finding.category for finding in findings}
        self.assertIn("root-lock-refresh-pending", categories)
        self.assertNotIn("stack-lock-drift", categories)
        self.assertNotIn("stack-lock-render-drift", categories)
        self.assertNotIn("stack-lock-pin-drift", categories)
        self.assertNotIn("stack-lock-missing-ref", categories)

    def test_committed_lock_only_root_refresh_is_accepted(self) -> None:
        root = self._temp_root()
        stack_file = root / "stack.yaml"
        lockfile_path = root / "stack.lock.yaml"
        locked_payload = _lock_payload(OLD_ROOT_COMMIT)
        generated_payload = _lock_payload(NEW_ROOT_COMMIT)
        lockfile_path.write_bytes(render_lockfile_bytes(locked_payload))
        canonical_lock = _canonical_lock(
            root,
            generated_payload,
            dirty_actual=False,
            dirty_effective=False,
            modified_paths=[],
            self_refresh_only=False,
        )

        def git_output_side_effect(repo_path: Path, *args: str) -> tuple[int, str]:
            self.assertEqual(root, repo_path)
            if args[:2] == ("cat-file", "-e"):
                return 0, ""
            if args[:2] == ("merge-base", "--is-ancestor"):
                return 0, ""
            if args[:2] == ("diff", "--name-only"):
                return 0, "stack.lock.yaml\n"
            raise AssertionError(f"Unexpected git invocation: {args!r}")

        with ExitStack() as stack:
            for patcher in self._base_patchers():
                stack.enter_context(patcher)
            stack.enter_context(
                patch(
                    "ops.validation.validate_stack.build_canonical_lockfile_artifacts",
                    return_value=canonical_lock,
                )
            )
            stack.enter_context(
                patch("ops.validation.validate_stack.git_output", side_effect=git_output_side_effect)
            )
            stack.enter_context(
                patch(
                    "ops.validation.validate_stack.verify_locked_ref",
                    side_effect=AssertionError("accepted root self-refresh should skip direct HEAD pin verification"),
                )
            )
            findings = build_findings(stack_file, self._config(), lock_file_override=lockfile_path)

        categories = {finding.category for finding in findings}
        self.assertIn("root-lock-refresh-accepted", categories)
        self.assertNotIn("stack-lock-drift", categories)
        self.assertNotIn("stack-lock-render-drift", categories)
        self.assertNotIn("stack-lock-pin-drift", categories)
        self.assertNotIn("stack-lock-missing-ref", categories)

    def test_committed_root_refresh_with_stack_manifest_drift_is_not_accepted(self) -> None:
        root = self._temp_root()
        lockfile_path = root / "stack.lock.yaml"
        locked_payload = _lock_payload(OLD_ROOT_COMMIT, stack_manifest_digest="sha256:manifest-a")
        generated_payload = _lock_payload(NEW_ROOT_COMMIT, stack_manifest_digest="sha256:manifest-b")
        drift_report = describe_lock_payload_drift(locked_payload, generated_payload)
        canonical_lock = _canonical_lock(
            root,
            generated_payload,
            dirty_actual=False,
            dirty_effective=False,
            modified_paths=[],
            self_refresh_only=False,
        )
        lockfile_bytes = render_lockfile_bytes(locked_payload)

        state = classify_root_lock_refresh_state(
            root=root,
            lockfile_path=lockfile_path,
            lockfile=locked_payload,
            lockfile_bytes=lockfile_bytes,
            canonical_lock=canonical_lock,
            drift_report=drift_report,
        )

        self.assertIsNone(state)

    def test_committed_root_refresh_with_non_lock_diff_is_not_accepted(self) -> None:
        root = self._temp_root()
        lockfile_path = root / "stack.lock.yaml"
        locked_payload = _lock_payload(OLD_ROOT_COMMIT)
        generated_payload = _lock_payload(NEW_ROOT_COMMIT)
        drift_report = describe_lock_payload_drift(locked_payload, generated_payload)
        canonical_lock = _canonical_lock(
            root,
            generated_payload,
            dirty_actual=False,
            dirty_effective=False,
            modified_paths=[],
            self_refresh_only=False,
        )
        lockfile_bytes = render_lockfile_bytes(locked_payload)

        def git_output_side_effect(repo_path: Path, *args: str) -> tuple[int, str]:
            self.assertEqual(root, repo_path)
            if args[:2] == ("cat-file", "-e"):
                return 0, ""
            if args[:2] == ("merge-base", "--is-ancestor"):
                return 0, ""
            if args[:2] == ("diff", "--name-only"):
                return 0, "ops/validation/validate_stack.py\nstack.lock.yaml\n"
            raise AssertionError(f"Unexpected git invocation: {args!r}")

        with patch("ops.validation.validate_stack.git_output", side_effect=git_output_side_effect):
            state = classify_root_lock_refresh_state(
                root=root,
                lockfile_path=lockfile_path,
                lockfile=locked_payload,
                lockfile_bytes=lockfile_bytes,
                canonical_lock=canonical_lock,
                drift_report=drift_report,
            )

        self.assertIsNone(state)

    def test_child_repo_pin_drift_still_reports_error(self) -> None:
        locked_payload = _lock_payload(OLD_ROOT_COMMIT, child_commit=CHILD_COMMIT)
        generated_payload = _lock_payload(OLD_ROOT_COMMIT, child_commit=NEW_ROOT_COMMIT)
        drift_report = describe_lock_payload_drift(locked_payload, generated_payload)

        findings = describe_stack_lock_drift(
            lockfile_rel="stack.lock.yaml",
            drift_report=drift_report,
        )

        categories_by_path = {(finding.category, finding.path) for finding in findings}
        self.assertIn(
            ("stack-lock-pin-drift", "stack.lock.yaml#child"),
            categories_by_path,
        )

    def test_unmanaged_repos_are_not_implicitly_lock_managed(self) -> None:
        config = {
            "repo_registry": {
                "stack": {"path": ".", "role": "operator-layer", "status": "active"},
                "fitness": {"path": "repos/fawxzzy-fitness", "role": "application", "status": "unmanaged"},
                "mazer": {"path": "repos/mazer", "role": "application", "status": "unmanaged"},
            }
        }

        self.assertEqual(["stack"], included_repo_ids(config))


if __name__ == "__main__":
    unittest.main()
