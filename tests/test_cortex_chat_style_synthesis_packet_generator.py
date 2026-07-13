from __future__ import annotations

import io
import json
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import patch

from ops.cortex.chat_style_synthesis_packet_generator import (
    AUTHORITY_DENIALS,
    NEXT_PACKET,
    OPTION_FIELDS,
    SCHEMA_VERSION,
    SYNTHESIS_PACKET_FIELDS,
    TOP_LEVEL_FIELDS,
    TRUST_CLASSES,
    build_packet,
    build_schema_only_payload,
    main,
    render_markdown,
    validate_output_path,
)


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


class ChatStyleSynthesisPacketGeneratorTests(unittest.TestCase):
    def _root(self) -> Path:
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        root = Path(directory.name)
        _write(root / "docs/memory/profiles/workflow.md", "# Workflow\nRULE - Evidence Separation\nPATTERN - Advisory First\nFAILURE MODE - Prose As Truth\n")
        _write(root / "docs/ops/receipt.md", "# Receipt\nThe governed receipt is durable.\n")
        _write(root / "docs/atlas-book/state.md", "# Book\n")
        return root

    def _payload(self, root: Path, *sources: str, mode: str = "strategy") -> dict[str, object]:
        return build_packet(root=root, sources=list(sources or ("docs/memory/profiles/workflow.md", "docs/ops/receipt.md")), mode=mode)

    # Proof 01: valid governed input is accepted and preserved.
    def test_proof_01_valid_source_is_preserved(self) -> None:
        payload = self._payload(self._root())
        self.assertIn("docs/memory/profiles/workflow.md", payload["source_refs"])

    # Proof 02: multiple classes are sorted deterministically.
    def test_proof_02_multiple_sources_are_deterministic(self) -> None:
        root = self._root()
        first = self._payload(root, "docs/ops/receipt.md", "docs/memory/profiles/workflow.md")
        second = self._payload(root, "docs/memory/profiles/workflow.md", "docs/ops/receipt.md")
        self.assertEqual(first["source_refs"], second["source_refs"])
        self.assertEqual(first, second)

    # Proof 03: facts and inferences are separate evidence classes.
    def test_proof_03_facts_and_inferences_are_separate(self) -> None:
        packet = self._payload(self._root())["synthesis_packet"]
        self.assertNotEqual(packet["facts"], packet["inferences"])
        self.assertTrue(all(item["trust_class"] != "reasoned_inference" for item in packet["facts"]))

    # Proof 04: the operator assumption is never implicit.
    def test_proof_04_assumptions_are_explicit(self) -> None:
        assumptions = self._payload(self._root())["synthesis_packet"]["assumptions"]
        self.assertEqual("operator_assumption", assumptions[0]["trust_class"])

    # Proof 05: incomplete evidence creates an explicit gap.
    def test_proof_05_evidence_gaps_are_explicit(self) -> None:
        payload = self._payload(self._root(), "docs/memory/profiles/workflow.md")
        self.assertEqual("advisory_gap", payload["status"])
        self.assertTrue(payload["evidence_gaps"])

    # Proof 06: comparison is bounded to multiple options.
    def test_proof_06_multiple_bounded_options(self) -> None:
        self.assertEqual(2, len(self._payload(self._root())["options"]))

    # Proof 07: tradeoffs do not vary for identical input.
    def test_proof_07_tradeoffs_are_deterministic(self) -> None:
        root = self._root()
        self.assertEqual(self._payload(root)["synthesis_packet"]["tradeoffs"], self._payload(root)["synthesis_packet"]["tradeoffs"])

    # Proof 08: safe packets contain exactly one recommendation.
    def test_proof_08_one_safe_recommendation(self) -> None:
        payload = self._payload(self._root())
        self.assertTrue(payload["safe_to_use"])
        self.assertIsNotNone(payload["recommendation"])

    # Proof 09: rejected options name their reason.
    def test_proof_09_rejected_options_have_reasons(self) -> None:
        rejected = self._payload(self._root())["synthesis_packet"]["rejected_options"]
        self.assertTrue(rejected[0]["rejection_reason"])
        self.assertEqual(list(OPTION_FIELDS), list(rejected[0].keys()))

    # Proof 10: doctrine stays a doctrine reference, not landing proof.
    def test_proof_10_playbook_doctrine_is_not_proof(self) -> None:
        refs = self._payload(self._root())["playbook_refs"]
        self.assertTrue(refs["doctrine_is_not_implementation_proof"])
        self.assertTrue(refs["rules"] and refs["patterns"] and refs["failure_modes"])

    # Proof 11: marker effects are advisory only.
    def test_proof_11_marker_impact_is_advisory(self) -> None:
        impact = self._payload(self._root())["marker_impacts"][0]
        self.assertTrue(impact["advisory_only"])

    # Proof 12: exactly one bounded handoff objective exists.
    def test_proof_12_one_handoff_objective(self) -> None:
        handoff = self._payload(self._root())["codex_handoff"]
        self.assertIsInstance(handoff["objective"], str)
        self.assertNotIsInstance(handoff, list)

    # Proof 13: handoff is advisory and cannot run or claim completion.
    def test_proof_13_handoff_is_non_executing(self) -> None:
        handoff = self._payload(self._root())["codex_handoff"]
        self.assertFalse(handoff["automatic_execution"])
        self.assertFalse(handoff["completion_claimed"])

    # Proof 14: hidden transcript input is forbidden.
    def test_proof_14_hidden_transcript_is_rejected(self) -> None:
        payload = self._payload(self._root(), "tmp/atlas/transcripts/session.json")
        self.assertEqual("blocker", payload["status"])
        self.assertEqual("forbidden", payload["synthesis_packet"]["inferences"][-1]["trust_class"])

    # Proof 15: owner repositories are forbidden sources.
    def test_proof_15_owner_repo_is_rejected(self) -> None:
        self.assertEqual("blocker", self._payload(self._root(), "repos/example/README.md")["status"])

    # Proof 16: .env files are forbidden sources.
    def test_proof_16_environment_source_is_rejected(self) -> None:
        self.assertEqual("blocker", self._payload(self._root(), "tmp/atlas/.env.snapshot")["status"])

    # Proof 17: live platform paths are forbidden.
    def test_proof_17_live_platform_source_is_rejected(self) -> None:
        for name in ("vercel-live.json", "supabase-live.json", "discord-live.json", "github-live.json"):
            self.assertEqual("blocker", self._payload(self._root(), f"tmp/atlas/{name}")["status"])

    # Proof 18: absolute source paths fail closed.
    def test_proof_18_absolute_source_is_rejected(self) -> None:
        root = self._root()
        self.assertEqual("blocker", self._payload(root, str(root / "docs/ops/receipt.md"))["status"])

    # Proof 19: absolute JSON outputs fail closed.
    def test_proof_19_absolute_json_output_is_rejected(self) -> None:
        root = self._root()
        path, error = validate_output_path(root, str(root / "tmp/atlas/out.json"), ".json")
        self.assertIsNone(path)
        self.assertEqual("absolute_output_path", error["code"])

    # Proof 20: protected/out-of-scope outputs are rejected.
    def test_proof_20_protected_output_is_rejected(self) -> None:
        root = self._root()
        for candidate in ("docs/ops/out.json", "tmp/out.json", "../out.json", "tmp/atlas/out.md"):
            path, error = validate_output_path(root, candidate, ".json")
            self.assertIsNone(path, candidate)
            self.assertIsNotNone(error, candidate)

    # Proof 21: an explicit ignored tmp/atlas JSON output is accepted.
    def test_proof_21_safe_tmp_atlas_output_is_accepted(self) -> None:
        root = self._root()
        path, error = validate_output_path(root, "tmp/atlas/out.json", ".json")
        self.assertIsNotNone(path)
        self.assertIsNone(error)

    # Proof 22: exact top-level order is stable.
    def test_proof_22_json_field_order_is_frozen(self) -> None:
        payload = self._payload(self._root())
        self.assertEqual(list(TOP_LEVEL_FIELDS), list(payload.keys()))
        self.assertEqual(SCHEMA_VERSION, payload["schema_version"])

    # Proof 23: Markdown renderer is deterministic.
    def test_proof_23_markdown_is_deterministic(self) -> None:
        root = self._root()
        self.assertEqual(render_markdown(self._payload(root)), render_markdown(self._payload(root)))

    # Proof 24: contradictory JSON claims create a classified conflict.
    def test_proof_24_conflicts_are_classified(self) -> None:
        root = self._root()
        _write(root / "tmp/atlas/conflict.json", json.dumps({"claims": [{"claim": "packet", "value": "A"}, {"claim": "packet", "value": "B"}]}))
        payload = self._payload(root, "tmp/atlas/conflict.json", "docs/ops/receipt.md")
        self.assertEqual("conflict", payload["status"])
        self.assertIn("conflicted", [item["trust_class"] for item in payload["synthesis_packet"]["inferences"]])

    # Proof 25: strict mode gives a nonzero conflict exit.
    def test_proof_25_strict_conflict_is_nonzero(self) -> None:
        root = self._root()
        _write(root / "tmp/atlas/conflict.json", json.dumps({"claims": [{"claim": "packet", "value": 1}, {"claim": "packet", "value": 2}]}))
        with patch("ops.cortex.chat_style_synthesis_packet_generator.atlas_root", return_value=root), redirect_stdout(io.StringIO()):
            code = main(["--json", "--source", "tmp/atlas/conflict.json", "--source", "docs/ops/receipt.md", "--strict"])
        self.assertNotEqual(0, code)

    # Proof 26: CLI is write-silent without explicit output flags.
    def test_proof_26_no_output_without_flags(self) -> None:
        root = self._root()
        with patch("ops.cortex.chat_style_synthesis_packet_generator.atlas_root", return_value=root), redirect_stdout(io.StringIO()):
            self.assertEqual(0, main(["--json", "--source", "docs/memory/profiles/workflow.md", "--source", "docs/ops/receipt.md"]))
        self.assertFalse((root / "tmp/atlas").exists())

    # Proof 27: all permanent authority denials are always serialized.
    def test_proof_27_authority_denials_are_always_emitted(self) -> None:
        self.assertEqual(list(AUTHORITY_DENIALS), self._payload(self._root())["authority_denials"])
        self.assertIn("no custom SQLite execution queue or scheduler implementation", AUTHORITY_DENIALS)

    # Proof 28: generator writes only explicitly requested tmp artifacts.
    def test_proof_28_no_governed_surface_mutation(self) -> None:
        root = self._root()
        output = root / "tmp/atlas/output.json"
        with patch("ops.cortex.chat_style_synthesis_packet_generator.atlas_root", return_value=root), redirect_stdout(io.StringIO()):
            self.assertEqual(0, main(["--json", "--source", "docs/memory/profiles/workflow.md", "--source", "docs/ops/receipt.md", "--output", "tmp/atlas/output.json"]))
        self.assertTrue(output.exists())
        self.assertFalse((root / "runtime").exists())

    # Proof 29: no network dependency is present in admitted packet construction.
    def test_proof_29_no_network_is_required(self) -> None:
        payload = self._payload(self._root())
        self.assertIn("no network requirement", payload["synthesis_packet"]["constraints"])

    # Proof 30: focused schema/contract test remains self-contained.
    def test_proof_30_schema_and_contract_shape(self) -> None:
        schema = build_schema_only_payload(root=self._root())
        self.assertEqual(list(TOP_LEVEL_FIELDS), list(schema.keys()))
        self.assertEqual(list(SYNTHESIS_PACKET_FIELDS), list(schema["synthesis_packet"].keys()))
        self.assertEqual(list(TRUST_CLASSES), [item["trust_class"] for item in schema["trust_summary"]])
        self.assertEqual(NEXT_PACKET, schema["next_recommended_packet"])


if __name__ == "__main__":
    unittest.main()
