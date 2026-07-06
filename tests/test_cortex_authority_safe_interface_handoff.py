from __future__ import annotations

import io
import json
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import patch

from ops._atlas import atlas_root
from ops.cortex.authority_safe_interface_handoff import (
    AUTHORITY_DENIALS,
    SCHEMA_VERSION,
    build_handoff_report,
    main,
    validate_output_path,
)


def _write(path: Path, text: str = "fixture\n") -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


class AuthoritySafeInterfaceHandoffTests(unittest.TestCase):
    def _temp_root(self, *, validation_error: bool = False) -> Path:
        temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(temp_dir.cleanup)
        root = Path(temp_dir.name)
        refs = [
            "docs/architecture/ATLAS-CORTEX-PLAYBOOK-CODEX.md",
            "docs/standards/WORKER-ORCHESTRATION.md",
            "docs/PLAYBOOK_NOTES.md",
            "docs/atlas-book/01-current-state.md",
            "docs/atlas-book/02-lanes-and-markers.md",
            "docs/atlas-book/05-receipt-index.md",
            "docs/atlas-book/12-restart-and-handoff-guide.md",
            "docs/memory/profiles/zachariah_workflow_profile.md",
            "docs/memory/initiatives/continuity-manifest-playbook-everywhere-cortex-interface.json",
            "docs/ops/PLAYBOOK-EVERYWHERE-CORTEX-INTERFACE-AUTHORITY-SAFE-CORTEX-INTERFACE-WIDENING-CONTRACT-FREEZE-2026-07-06.md",
            "docs/ops/PLAYBOOK-EVERYWHERE-CORTEX-INTERFACE-AUTHORITY-SAFE-CORTEX-INTERFACE-WIDENING-FIRST-IMPLEMENTATION-ADMISSION-2026-07-06.md",
            "docs/ops/PLAYBOOK-EVERYWHERE-CORTEX-INTERFACE-AUTHORITY-SAFE-CORTEX-INTERFACE-WIDENING-PROMPT-PACK-AND-WORKER-HANDOFF-CONTRACT-2026-07-06.md",
            "docs/ops/PLAYBOOK-EVERYWHERE-CORTEX-INTERFACE-AUTHORITY-SAFE-CORTEX-INTERFACE-WIDENING-IMPLEMENTATION-READINESS-CLOSEOUT-AND-WORKER-ROUTING-2026-07-06.md",
            "ops/atlas/playbook_adoption_matrix.py",
            "ops/cortex/worker_prompt.py",
            "runtime/cortex/worker-prompts/latest.json",
            "stack.lock.yaml",
        ]
        for ref in refs:
            _write(root / ref)
        summary = {"critical": 0, "error": 1 if validation_error else 0, "warning": 0, "info": 0}
        _write(
            root / "runtime/receipts/validation/stack-validation.latest.json",
            json.dumps({"summary": summary}, indent=2) + "\n",
        )
        return root

    def test_report_is_deterministic_and_authority_denying(self) -> None:
        root = self._temp_root()

        with patch("ops.cortex.authority_safe_interface_handoff.collect_git_state", return_value=("main", "abc123")):
            payload = build_handoff_report(root=root)

        self.assertEqual(SCHEMA_VERSION, payload["schema_version"])
        self.assertEqual("ok", payload["status"])
        self.assertEqual("main", payload["branch"])
        self.assertEqual("abc123", payload["head"])
        self.assertTrue(payload["safe_to_use"])
        self.assertEqual(list(AUTHORITY_DENIALS), payload["authority_denials"])
        self.assertFalse(payload["handoff_payload"]["execution_authorized"])
        self.assertFalse(payload["handoff_payload"]["owner_repo_mutation_authorized"])
        self.assertFalse(payload["handoff_payload"]["final_receipt_authorized"])
        self.assertEqual(
            [
                "schema_version",
                "status",
                "root",
                "branch",
                "head",
                "source_refs",
                "consumed_surfaces",
                "handoff_payload",
                "authority_denials",
                "forbidden_surfaces",
                "warnings",
                "blockers",
                "safe_to_use",
            ],
            list(payload.keys()),
        )
        json.dumps(payload, sort_keys=True)

    def test_owner_repo_source_is_rejected(self) -> None:
        root = self._temp_root()

        payload = build_handoff_report(root=root, sources=["repos/mazer/README.md"])

        self.assertEqual("blocker", payload["status"])
        self.assertFalse(payload["safe_to_use"])
        self.assertEqual("owner_repo_source_forbidden", payload["blockers"][0]["code"])

    def test_validation_error_sets_safe_to_use_false(self) -> None:
        root = self._temp_root(validation_error=True)

        payload = build_handoff_report(root=root)

        self.assertEqual("blocker", payload["status"])
        self.assertFalse(payload["safe_to_use"])
        self.assertEqual("validation_not_safe", payload["blockers"][0]["code"])

    def test_output_path_must_be_tmp_relative(self) -> None:
        root = self._temp_root()

        allowed, error = validate_output_path(root, "tmp/cortex/handoff.json")
        self.assertIsNotNone(allowed)
        self.assertIsNone(error)

        for candidate in ("docs/ops/not-allowed.md", "repos/x/out.json", "../out.json", str(root / "tmp/out.json")):
            allowed, error = validate_output_path(root, candidate)
            self.assertIsNone(allowed)
            self.assertIsNotNone(error)

    def test_main_writes_only_with_explicit_safe_output(self) -> None:
        root = self._temp_root()
        output = root / "tmp/cortex/handoff.json"

        with patch("ops.cortex.authority_safe_interface_handoff.atlas_root", return_value=root):
            stdout = io.StringIO()
            with redirect_stdout(stdout):
                exit_code = main(["--json", "--output", "tmp/cortex/handoff.json"])

        self.assertEqual(0, exit_code)
        self.assertTrue(output.exists())
        self.assertEqual("ok", json.loads(output.read_text(encoding="utf-8"))["status"])
        self.assertEqual("ok", json.loads(stdout.getvalue())["status"])

    def test_main_rejects_protected_output_without_writing(self) -> None:
        root = self._temp_root()

        with patch("ops.cortex.authority_safe_interface_handoff.atlas_root", return_value=root):
            stdout = io.StringIO()
            with redirect_stdout(stdout):
                exit_code = main(["--json", "--output", "secrets/handoff.json"])

        self.assertEqual(2, exit_code)
        payload = json.loads(stdout.getvalue())
        self.assertEqual("blocker", payload["status"])
        self.assertEqual("protected_output_path", payload["blockers"][0]["code"])
        self.assertFalse((root / "secrets/handoff.json").exists())


if __name__ == "__main__":
    unittest.main()
