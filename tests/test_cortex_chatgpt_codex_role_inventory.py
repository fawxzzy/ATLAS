from __future__ import annotations

import io
import json
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import patch

from ops.cortex.chatgpt_codex_role_inventory import (
    AUTHORITY_DENIALS,
    SCHEMA_VERSION,
    build_role_inventory_report,
    main,
    validate_output_path,
)


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


class ChatgptCodexRoleInventoryTests(unittest.TestCase):
    def _temp_root(self, *, validation_error: bool = False) -> Path:
        temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(temp_dir.cleanup)
        root = Path(temp_dir.name)
        summary = {"critical": 0, "error": 1 if validation_error else 0, "warning": 0, "info": 0}
        _write(root / "runtime/receipts/validation/stack-validation.latest.json", json.dumps({"summary": summary}) + "\n")
        return root

    def _write_default_sources(self, root: Path, *, include_codex: bool = True) -> None:
        _write(root / "AGENTS.md", "# ATLAS Root Rules\nATLAS root governance.\n")
        _write(
            root / "docs/PLAYBOOK_NOTES.md",
            "# Playbook Notes\nPlaybook doctrine keeps reusable patterns and failure modes explicit.\n",
        )
        _write(
            root / "docs/architecture/ATLAS-CORTEX-PLAYBOOK-CODEX.md",
            "# ATLAS, CORTEX, Playbook, and Codex\nATLAS owns stack truth. Playbook owns repo doctrine. Cortex Bridge stays governed.\n",
        )
        _write(root / "docs/atlas-book/05-receipt-index.md", "# Receipt Index\n- dual-mode receipts\n")
        codex_route_line = "Codex: implementation work, repo edits, test fixes, refactors, docs changes" if include_codex else "Execution worker route intentionally omitted"
        _write(
            root / "docs/memory/profiles/zachariah_workflow_profile.md",
            "\n".join(
                [
                    "# Zachariah Workflow Profile",
                    "ChatGPT: quick decisions, lightweight planning, copy edits, small prompts",
                    "Pro Chat: deeper technical reasoning, architecture review, debugging strategy",
                    "Deep Research: current external research, broad comparisons, high-stakes factual investigation",
                    codex_route_line,
                    "Recommended execution path: Codex",
                ]
            )
            + "\n",
        )
        _write(
            root / "docs/ops/CORTEX-DUAL-MODE-AND-SIMULATION-SUBSTRATE-MARKER-ADMISSION-2026-07-09.md",
            "# Marker Admission\nChatGPT and Codex are current external scaffolding. Cortex Bridge is part of the future substrate.\n",
        )
        codex_line = "Current Codex Mapping\nCodex-style execution for bounded edits, tests, proof, and reconciliation.\n" if include_codex else ""
        _write(
            root / "docs/ops/CORTEX-DUAL-MODE-REPLACEMENT-READINESS-OPERATING-MODE-CONTRACT-FREEZE-2026-07-09.md",
            (
                "# Operating Model\n"
                "Current ChatGPT Mapping\n"
                "ChatGPT-style synthesis for framing, compression, and operator-facing reasoning.\n"
                f"{codex_line}"
                "Cortex Synthesis Interface\n"
                "Cortex Execution Interface\n"
                "Cortex Bridge\n"
                "Shared ATLAS Memory And Proof Substrate\n"
                "Shared Playbook Doctrine Substrate\n"
            ),
        )
        admission_text = (
            "# Admission\nChatGPT-style systems are current synthesis scaffolding. Codex-style systems are current execution scaffolding. "
            "ATLAS receipts and Playbook doctrine remain canonical.\n"
            if include_codex
            else "# Admission\nChatGPT-style systems are current synthesis scaffolding. ATLAS receipts and Playbook doctrine remain canonical.\n"
        )
        _write(
            root / "docs/ops/CORTEX-DUAL-MODE-REPLACEMENT-READINESS-CHATGPT-CODEX-ROLE-INVENTORY-FIRST-IMPLEMENTATION-ADMISSION-2026-07-09.md",
            admission_text,
        )
        prompt_pack_text = (
            "# Prompt Pack\nImplement one bounded helper/test pair. ATLAS receipts/manifests/Book/read-model truth. Playbook doctrine/pattern/failure-mode truth. ChatGPT-style synthesis duties. Codex-style execution duties.\n"
            if include_codex
            else "# Prompt Pack\nImplement one bounded helper/test pair. ATLAS receipts/manifests/Book/read-model truth. Playbook doctrine/pattern/failure-mode truth. ChatGPT-style synthesis duties only.\n"
        )
        _write(
            root / "docs/ops/CORTEX-DUAL-MODE-REPLACEMENT-READINESS-CHATGPT-CODEX-ROLE-INVENTORY-PROMPT-PACK-AND-WORKER-HANDOFF-CONTRACT-2026-07-09.md",
            prompt_pack_text,
        )
        _write(
            root / "docs/registry/STACK-REPO-INVENTORY.json",
            json.dumps({"schema_version": "atlas.stack.repo-inventory.v1", "repo_count": 1}, indent=2) + "\n",
        )

    def test_build_report_classifies_core_and_optional_roles(self) -> None:
        root = self._temp_root()
        self._write_default_sources(root)

        with patch("ops.cortex.chatgpt_codex_role_inventory.collect_git_state", return_value=("main", "abc123")):
            payload = build_role_inventory_report(root=root)

        self.assertEqual(SCHEMA_VERSION, payload["schema_version"])
        self.assertEqual("ok", payload["status"])
        self.assertTrue(payload["safe_to_use"])
        self.assertEqual(list(AUTHORITY_DENIALS), payload["authority_denials"])
        self.assertEqual([], payload["simulation_roles"])
        self.assertIn("cortex_bridge", payload["replacement_targets"])
        self.assertIn("shared_atlas_substrate", payload["shared_substrate_dependencies"])
        self.assertIn("shared_playbook_doctrine_substrate", payload["shared_substrate_dependencies"])
        systems = {role["current_system"] for role in payload["role_inventory"]}
        for system in ("ChatGPT", "Codex", "Deep Research", "Pro Chat", "Normal Chat", "ATLAS", "Playbook", "Cortex"):
            self.assertIn(system, systems)
        self.assertEqual(
            [
                "schema_version",
                "status",
                "root",
                "branch",
                "head",
                "source_refs",
                "role_inventory",
                "synthesis_roles",
                "execution_roles",
                "bridge_roles",
                "simulation_roles",
                "replacement_targets",
                "external_dependencies",
                "current_role_count",
                "mapped_role_count",
                "unmapped_role_count",
                "current_roles",
                "future_interface_targets",
                "shared_substrate_dependencies",
                "authority_denials",
                "forbidden_surfaces",
                "split_brain_risks",
                "warnings",
                "blockers",
                "safe_to_use",
            ],
            list(payload.keys()),
        )
        json.dumps(payload, sort_keys=True)

    def test_missing_operating_model_source_fails_closed(self) -> None:
        root = self._temp_root()
        self._write_default_sources(root)

        payload = build_role_inventory_report(
            root=root,
            sources=[
                "docs/memory/profiles/zachariah_workflow_profile.md",
                "docs/ops/CORTEX-DUAL-MODE-REPLACEMENT-READINESS-CHATGPT-CODEX-ROLE-INVENTORY-FIRST-IMPLEMENTATION-ADMISSION-2026-07-09.md",
                "docs/ops/CORTEX-DUAL-MODE-REPLACEMENT-READINESS-CHATGPT-CODEX-ROLE-INVENTORY-PROMPT-PACK-AND-WORKER-HANDOFF-CONTRACT-2026-07-09.md",
            ],
        )

        self.assertEqual("blocker", payload["status"])
        self.assertEqual("core_source_missing", payload["blockers"][0]["code"])

    def test_missing_required_role_mapping_fails_closed(self) -> None:
        root = self._temp_root()
        self._write_default_sources(root, include_codex=False)

        payload = build_role_inventory_report(root=root)

        self.assertEqual("blocker", payload["status"])
        codes = {item["code"] for item in payload["blockers"]}
        self.assertIn("required_role_system_missing", codes)

    def test_hidden_owner_deploy_and_absolute_sources_are_rejected(self) -> None:
        root = self._temp_root()
        self._write_default_sources(root)

        for candidate in (
            "repos/fawxzzy-fitness/docs/ops/receipt.md",
            "runtime/transcripts/session.json",
            "deploy/output.json",
            "../outside.md",
            str(root / "docs/memory/profiles/zachariah_workflow_profile.md"),
        ):
            payload = build_role_inventory_report(root=root, sources=[candidate])
            self.assertEqual("blocker", payload["status"], candidate)
            self.assertFalse(payload["safe_to_use"], candidate)

    def test_output_path_guards(self) -> None:
        root = self._temp_root()

        allowed, error = validate_output_path(root, "tmp/cortex/role-inventory.json")
        self.assertIsNotNone(allowed)
        self.assertIsNone(error)

        for candidate in ("docs/ops/out.json", "tmp/cortex/out.txt", "repos/x/out.json", "../out.json", str(root / "tmp/out.json")):
            allowed, error = validate_output_path(root, candidate)
            self.assertIsNone(allowed, candidate)
            self.assertIsNotNone(error, candidate)

    def test_main_default_writes_no_files(self) -> None:
        root = self._temp_root()
        self._write_default_sources(root)
        output = root / "tmp/cortex/role-inventory.json"

        with patch("ops.cortex.chatgpt_codex_role_inventory.atlas_root", return_value=root):
            stdout = io.StringIO()
            with redirect_stdout(stdout):
                exit_code = main(["--json"])

        self.assertEqual(0, exit_code)
        self.assertFalse(output.exists())
        self.assertEqual("ok", json.loads(stdout.getvalue())["status"])

    def test_main_writes_only_with_explicit_safe_output(self) -> None:
        root = self._temp_root()
        self._write_default_sources(root)
        output = root / "tmp/cortex/role-inventory.json"

        with patch("ops.cortex.chatgpt_codex_role_inventory.atlas_root", return_value=root):
            stdout = io.StringIO()
            with redirect_stdout(stdout):
                exit_code = main(["--json", "--output", "tmp/cortex/role-inventory.json"])

        self.assertEqual(0, exit_code)
        self.assertTrue(output.exists())
        self.assertEqual("ok", json.loads(output.read_text(encoding="utf-8"))["status"])
        self.assertEqual("ok", json.loads(stdout.getvalue())["status"])

    def test_main_rejects_protected_output_without_writing(self) -> None:
        root = self._temp_root()
        self._write_default_sources(root)

        with patch("ops.cortex.chatgpt_codex_role_inventory.atlas_root", return_value=root):
            stdout = io.StringIO()
            with redirect_stdout(stdout):
                exit_code = main(["--json", "--output", "secrets/role-inventory.json"])

        self.assertEqual(2, exit_code)
        payload = json.loads(stdout.getvalue())
        self.assertEqual("blocker", payload["status"])
        self.assertEqual("owner_repo_source_forbidden", payload["blockers"][-1]["code"])
        self.assertFalse((root / "secrets/role-inventory.json").exists())

    def test_strict_returns_nonzero_for_blockers(self) -> None:
        root = self._temp_root(validation_error=True)
        self._write_default_sources(root)

        with patch("ops.cortex.chatgpt_codex_role_inventory.atlas_root", return_value=root):
            stdout = io.StringIO()
            with redirect_stdout(stdout):
                exit_code = main(["--json", "--strict"])

        self.assertEqual(2, exit_code)
        self.assertEqual("blocker", json.loads(stdout.getvalue())["status"])


if __name__ == "__main__":
    unittest.main()
