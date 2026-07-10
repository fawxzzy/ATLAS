from __future__ import annotations

import io
import json
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import patch

from ops.cortex.simulation_substrate_requirements import (
    AUTHORITY_DENIALS,
    RECONCILIATION_PACKET,
    SCHEMA_VERSION,
    build_simulation_requirements_report,
    main,
    validate_output_path,
)


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


class SimulationSubstrateRequirementsTests(unittest.TestCase):
    def _temp_root(self, *, validation_error: bool = False) -> Path:
        temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(temp_dir.cleanup)
        root = Path(temp_dir.name)
        summary = {"critical": 0, "error": 1 if validation_error else 0, "warning": 0, "info": 0}
        _write(root / "runtime/receipts/validation/stack-validation.latest.json", json.dumps({"summary": summary}) + "\n")
        return root

    def _write_default_sources(self, root: Path, *, include_research_groups: bool = True) -> None:
        _write(root / "AGENTS.md", "# ATLAS Root Rules\nATLAS root governance only.\n")
        _write(root / "docs/PLAYBOOK_NOTES.md", "# Playbook Notes\nexplicit inputs\nexplicit outputs\nexplicit denied authority\ndeterministic schemas\nreplayable proof posture\n")
        _write(root / "docs/atlas-book/05-receipt-index.md", "# Receipt Index\n- simulation receipt\n")
        _write(
            root / "docs/memory/profiles/zachariah_workflow_profile.md",
            (
                "# Zachariah Workflow Profile\n"
                "Codex: implementation work, repo edits, test fixes, refactors, docs changes\n"
                "Recommended execution path: Codex\n"
            ),
        )
        _write(
            root / "docs/ops/ATLAS-ROOT-OPERATOR-RESELECTION-TO-CORTEX-SIMULATION-SUBSTRATE-2026-07-09.md",
            "# Reselection\nSimulation lane selected through operator-approved root reselection.\n",
        )
        _write(
            root / "docs/ops/CORTEX-DUAL-MODE-AND-SIMULATION-SUBSTRATE-MARKER-ADMISSION-2026-07-09.md",
            "# Marker Admission\nCortex Simulation remains a governed root-owned lane.\n",
        )
        research_lines = [
            "# Research Contract",
            "scenario substrate",
            "agent substrate",
            "world-state substrate",
            "replay and evaluation substrate",
            "memory of prior experience",
            "reflection over that experience",
            "planning against current state",
            "sandboxed interaction among agents",
            "collaborator-aware planning",
            "model scenarios",
            "evaluate candidate plans",
            "ATLAS receipts",
            "continuity manifests",
            "proof availability",
            "forbidden authority",
            "explicit denied authority",
            "`scenario`",
            "`agent`",
            "`world_state`",
            "`memory`",
            "`reflection`",
            "`plan`",
            "`action`",
            "`observation`",
            "`evaluation`",
            "`safety_boundary`",
            "`proof_reference`",
        ]
        if not include_research_groups:
            research_lines = ["# Research Contract", "scenario substrate", "agent substrate"]
        _write(
            root / "docs/ops/CORTEX-SIMULATION-SUBSTRATE-READINESS-FABLE-GENERATIVE-AGENT-RESEARCH-CONTRACT-FREEZE-2026-07-09.md",
            "\n".join(research_lines) + "\n",
        )
        _write(
            root / "docs/ops/CORTEX-SIMULATION-SUBSTRATE-READINESS-SIMULATION-REQUIREMENTS-MAP-FIRST-IMPLEMENTATION-ADMISSION-2026-07-09.md",
            (
                "# Admission\n"
                "read root-owned simulation doctrine and receipt inputs\n"
                "emit a deterministic requirements map\n"
                "admitted first schema groups\n"
                "`scenario`\n`agent`\n`world_state`\n`memory`\n`reflection`\n`plan`\n`action`\n`observation`\n`evaluation`\n`safety_boundary`\n`proof_reference`\n"
            ),
        )
        _write(
            root / "docs/ops/CORTEX-SIMULATION-SUBSTRATE-READINESS-SIMULATION-REQUIREMENTS-MAP-PROMPT-PACK-AND-WORKER-HANDOFF-CONTRACT-2026-07-10.md",
            (
                "# Prompt Pack\n"
                "explicit safe output only under tmp/**.json\n"
                "deterministic JSON\n"
                "authority denials remain explicit\n"
                "reject absolute source paths\n"
                "reject owner repos\n"
                "reject .env* .vercel .playwright-mcp archive\n"
            ),
        )

    def test_build_report_maps_all_admitted_groups(self) -> None:
        root = self._temp_root()
        self._write_default_sources(root)

        with patch("ops.cortex.simulation_substrate_requirements.collect_git_state", return_value=("main", "abc123")):
            payload = build_simulation_requirements_report(root=root)

        self.assertEqual(SCHEMA_VERSION, payload["schema_version"])
        self.assertEqual("ok", payload["status"])
        self.assertTrue(payload["safe_to_use"])
        self.assertEqual(11, payload["requirement_group_count"])
        self.assertEqual(11, payload["mapped_group_count"])
        self.assertEqual(0, payload["unmapped_group_count"])
        self.assertEqual(RECONCILIATION_PACKET, payload["next_recommended_packet"])
        self.assertEqual(list(AUTHORITY_DENIALS), payload["authority_denials"])
        requirement_ids = [item["requirement_id"] for item in payload["requirements"]]
        self.assertEqual(
            [
                "scenario",
                "agent",
                "world_state",
                "memory",
                "reflection",
                "plan",
                "action",
                "observation",
                "evaluation",
                "safety_boundary",
                "proof_reference",
            ],
            requirement_ids,
        )
        self.assertEqual(
            [
                "schema_version",
                "status",
                "root",
                "branch",
                "head",
                "source_refs",
                "source_digests",
                "research_basis",
                "requirement_group_count",
                "mapped_group_count",
                "unmapped_group_count",
                "requirements",
                "requirement_groups",
                "core_primitives",
                "governance_primitives",
                "optional_extensions",
                "project_adapter_requirements",
                "evaluation_requirements",
                "admitted_data_surfaces",
                "forbidden_data_surfaces",
                "admitted_authority",
                "forbidden_authority",
                "authority_denials",
                "ethical_risks",
                "ip_rights_risks",
                "privacy_risks",
                "missing_requirements",
                "warnings",
                "blockers",
                "safe_to_use",
                "next_recommended_packet",
            ],
            list(payload.keys()),
        )
        json.dumps(payload, sort_keys=True)

    def test_omitted_supporting_context_is_advisory_gap(self) -> None:
        root = self._temp_root()
        self._write_default_sources(root)

        payload = build_simulation_requirements_report(
            root=root,
            sources=[
                "AGENTS.md",
                "docs/memory/profiles/zachariah_workflow_profile.md",
                "docs/ops/CORTEX-SIMULATION-SUBSTRATE-READINESS-FABLE-GENERATIVE-AGENT-RESEARCH-CONTRACT-FREEZE-2026-07-09.md",
                "docs/ops/CORTEX-SIMULATION-SUBSTRATE-READINESS-SIMULATION-REQUIREMENTS-MAP-FIRST-IMPLEMENTATION-ADMISSION-2026-07-09.md",
                "docs/ops/CORTEX-SIMULATION-SUBSTRATE-READINESS-SIMULATION-REQUIREMENTS-MAP-PROMPT-PACK-AND-WORKER-HANDOFF-CONTRACT-2026-07-10.md",
            ],
        )

        self.assertEqual("advisory_gap", payload["status"])
        self.assertFalse(payload["safe_to_use"])
        self.assertEqual("supporting_context_omitted", payload["warnings"][0]["code"])

    def test_missing_research_groups_fails_closed(self) -> None:
        root = self._temp_root()
        self._write_default_sources(root, include_research_groups=False)

        payload = build_simulation_requirements_report(root=root)

        self.assertEqual("blocker", payload["status"])
        codes = {item["code"] for item in payload["blockers"]}
        self.assertIn("required_group_unmapped", codes)

    def test_protected_hidden_and_absolute_sources_are_rejected(self) -> None:
        root = self._temp_root()
        self._write_default_sources(root)

        for candidate in (
            "repos/fawxzzy-fitness/docs/ops/receipt.md",
            "runtime/transcripts/session.json",
            "vercel/projects.json",
            "../outside.md",
            str(root / "AGENTS.md"),
        ):
            payload = build_simulation_requirements_report(root=root, sources=[candidate])
            self.assertEqual("blocker", payload["status"], candidate)
            self.assertFalse(payload["safe_to_use"], candidate)

    def test_validation_error_blocks_report(self) -> None:
        root = self._temp_root(validation_error=True)
        self._write_default_sources(root)

        payload = build_simulation_requirements_report(root=root)

        self.assertEqual("blocker", payload["status"])
        self.assertEqual("validation_not_safe", payload["blockers"][0]["code"])

    def test_output_path_guards(self) -> None:
        root = self._temp_root()

        allowed, error = validate_output_path(root, "tmp/cortex/simulation-substrate-requirements.json")
        self.assertIsNotNone(allowed)
        self.assertIsNone(error)

        for candidate in ("docs/ops/out.json", "tmp/cortex/out.txt", "repos/x/out.json", "../out.json", str(root / "tmp/out.json")):
            allowed, error = validate_output_path(root, candidate)
            self.assertIsNone(allowed, candidate)
            self.assertIsNotNone(error, candidate)

    def test_main_default_writes_no_files(self) -> None:
        root = self._temp_root()
        self._write_default_sources(root)
        output = root / "tmp/cortex/simulation-substrate-requirements.json"

        with patch("ops.cortex.simulation_substrate_requirements.atlas_root", return_value=root):
            stdout = io.StringIO()
            with redirect_stdout(stdout):
                exit_code = main(["--json"])

        self.assertEqual(0, exit_code)
        self.assertFalse(output.exists())
        self.assertEqual("ok", json.loads(stdout.getvalue())["status"])

    def test_main_writes_only_with_explicit_safe_output(self) -> None:
        root = self._temp_root()
        self._write_default_sources(root)
        output = root / "tmp/cortex/simulation-substrate-requirements.json"

        with patch("ops.cortex.simulation_substrate_requirements.atlas_root", return_value=root):
            stdout = io.StringIO()
            with redirect_stdout(stdout):
                exit_code = main(["--json", "--output", "tmp/cortex/simulation-substrate-requirements.json"])

        self.assertEqual(0, exit_code)
        self.assertTrue(output.exists())
        self.assertEqual("ok", json.loads(output.read_text(encoding="utf-8"))["status"])
        self.assertEqual("ok", json.loads(stdout.getvalue())["status"])

    def test_main_rejects_protected_output_without_writing(self) -> None:
        root = self._temp_root()
        self._write_default_sources(root)

        with patch("ops.cortex.simulation_substrate_requirements.atlas_root", return_value=root):
            stdout = io.StringIO()
            with redirect_stdout(stdout):
                exit_code = main(["--json", "--output", "secrets/simulation-substrate-requirements.json"])

        self.assertEqual(2, exit_code)
        payload = json.loads(stdout.getvalue())
        self.assertEqual("blocker", payload["status"])
        self.assertEqual("protected_path_forbidden", payload["blockers"][-1]["code"])
        self.assertFalse((root / "secrets/simulation-substrate-requirements.json").exists())

    def test_strict_returns_nonzero_for_advisory_gap(self) -> None:
        root = self._temp_root()
        self._write_default_sources(root)

        with patch("ops.cortex.simulation_substrate_requirements.atlas_root", return_value=root):
            stdout = io.StringIO()
            with redirect_stdout(stdout):
                exit_code = main(
                    [
                        "--json",
                        "--strict",
                        "--source",
                        "AGENTS.md",
                        "--source",
                        "docs/memory/profiles/zachariah_workflow_profile.md",
                        "--source",
                        "docs/ops/CORTEX-SIMULATION-SUBSTRATE-READINESS-FABLE-GENERATIVE-AGENT-RESEARCH-CONTRACT-FREEZE-2026-07-09.md",
                        "--source",
                        "docs/ops/CORTEX-SIMULATION-SUBSTRATE-READINESS-SIMULATION-REQUIREMENTS-MAP-FIRST-IMPLEMENTATION-ADMISSION-2026-07-09.md",
                        "--source",
                        "docs/ops/CORTEX-SIMULATION-SUBSTRATE-READINESS-SIMULATION-REQUIREMENTS-MAP-PROMPT-PACK-AND-WORKER-HANDOFF-CONTRACT-2026-07-10.md",
                    ]
                )

        self.assertEqual(2, exit_code)
        self.assertEqual("advisory_gap", json.loads(stdout.getvalue())["status"])
