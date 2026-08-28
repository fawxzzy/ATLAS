from __future__ import annotations

import io
import json
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import patch

from ops._atlas import atlas_root
from ops.atlas.awareness import atlas_status
from ops.atlas.build_codex_context import build_codex_context, main, render_codex_prompt, write_codex_context_pack


class AtlasCodexContextTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.root = atlas_root()
        cls.mazer_payload = build_codex_context(
            task_id="mazer-context",
            objective="Prepare Codex context for the Mazer D2 scorer follow-up.",
            intent_class="operator/conversation",
            target_repo_ids=["mazer"],
            root=cls.root,
        )
        cls.playbook_payload = build_codex_context(
            task_id="playbook-governance",
            objective="Audit Playbook verify rules and bindings.",
            intent_class="governance",
            target_repo_ids=["playbook"],
            root=cls.root,
        )
        cls.lifeline_payload = build_codex_context(
            task_id="lifeline-execution",
            objective="Review Lifeline capability and approval examples for read-only execution.",
            intent_class="execution",
            target_repo_ids=["lifeline"],
            root=cls.root,
        )
        cls.topology_payload = build_codex_context(
            task_id="topology-audit",
            objective="Review stack topology and quarantined repo visibility.",
            intent_class="topology/git",
            root=cls.root,
        )

    def test_context_pack_is_deterministic_for_identical_inputs(self) -> None:
        with patch("ops.atlas.build_codex_context.atlas_status", wraps=atlas_status) as status:
            first = build_codex_context(
                task_id="mazer-context",
                objective="Prepare Codex context for the Mazer D2 scorer follow-up.",
                intent_class="operator/conversation",
                target_repo_ids=["mazer"],
                root=self.root,
            )
            second = build_codex_context(
                task_id="mazer-context",
                objective="Prepare Codex context for the Mazer D2 scorer follow-up.",
                intent_class="operator/conversation",
                target_repo_ids=["mazer"],
                root=self.root,
            )
        self.assertEqual(status.call_count, 2)
        self.assertEqual(first["selected_refs"], second["selected_refs"])
        self.assertEqual(first["context_digest"], second["context_digest"])

    def test_mazer_context_pulls_initiative_proposal_inventory_and_attention(self) -> None:
        payload = self.mazer_payload
        bootstrap_refs = {item["ref"] for item in payload["bootstrap_contract"]["ordered_reads"]}
        self.assertIn("initiative:initiative-mazer-d2-learning-scorer", bootstrap_refs)
        self.assertIn(
            "runtime/atlas/proposed-sessions/session-proposed-mazer-d2-fixed-blessed-id-soak/session.manifest.json",
            bootstrap_refs,
        )
        repo_refs = {item["ref"] for item in payload["selected_refs"]["repo_inventory"]}
        self.assertIn("repo:mazer", repo_refs)
        attention_refs = {item["ref"] for item in payload["selected_refs"]["attention"]}
        initiative = json.loads(
            (self.root / "docs" / "memory" / "initiatives" / "initiative-mazer-d2-learning-scorer.json").read_text(
                encoding="utf-8"
            )
        )
        declared_attention_refs = set(initiative.get("related_attention_refs", []))
        self.assertTrue(declared_attention_refs)
        self.assertTrue(declared_attention_refs.issubset(attention_refs))
        trust_refs = {item["ref"] for item in payload["bootstrap_contract"]["ordered_reads"] if item["kind"] == "trust_posture"}
        self.assertIn("knowledge:personal--verta-core", trust_refs)

    def test_playbook_governance_context_prefers_verify_surfaces_only(self) -> None:
        payload = self.playbook_payload
        route_refs = {item["ref"] for item in payload["selected_refs"]["route_surfaces"]}
        self.assertIn("repos/playbook/docs/commands/verify.md", route_refs)
        self.assertIn("repos/playbook/docs/rules/verify-rules.md", route_refs)
        all_refs = {
            item["ref"]
            for group in payload["selected_refs"].values()
            for item in group
        }
        self.assertFalse(any(ref.startswith("repos/fawxzzy-mazer/") for ref in all_refs))

    def test_lifeline_execution_context_pulls_tool_registry_and_examples(self) -> None:
        payload = self.lifeline_payload
        route_refs = {item["ref"] for item in payload["selected_refs"]["route_surfaces"]}
        self.assertIn("docs/registry/ATLAS-TOOL-REGISTRY.json", route_refs)
        self.assertIn(
            "repos/lifeline/examples/privileged-execution/read-only-scan.request.json",
            route_refs,
        )
        self.assertIn(
            "repos/lifeline/examples/privileged-execution/read-only-scan.approval.json",
            route_refs,
        )

    def test_topology_context_keeps_verta_visible_but_metadata_only(self) -> None:
        payload = self.topology_payload
        trust_records = [
            item
            for item in payload["bootstrap_contract"]["ordered_reads"]
            if item["kind"] == "trust_posture"
        ]
        verta_records = [
            item
            for item in trust_records
            if item["title"] in {"personal--verta-core", "personal--verta-core-sanitized"}
        ]
        self.assertTrue(verta_records)
        for record in verta_records:
            self.assertEqual(record["hydration_mode"], "metadata_only")
            self.assertEqual(record["details"]["trust_class"], "untrusted")
        excluded_refs = {item["ref"] for item in payload["selected_refs"]["excluded_surfaces"]}
        self.assertIn("excluded_surface:verta_core_checkout", excluded_refs)
        self.assertIn("excluded_surface:verta_core_archive", excluded_refs)

    def test_prepare_prompt_uses_bootstrap_order_and_rules(self) -> None:
        prompt = render_codex_prompt(self.mazer_payload)
        self.assertIn("Follow the root bootstrap contract in this order", prompt)
        self.assertIn("Federate, don't duplicate.", prompt)
        self.assertIn("stack.yaml", prompt)
        self.assertIn("docs/registry/STACK-REPO-INVENTORY.json", prompt)
        self.assertIn("docs/memory/profiles/zachariah_workflow_profile.md", prompt)
        self.assertIn("python -m ops.atlas.persist_thread_context", prompt)
        self.assertIn("CONTEXT_PERSISTENCE_BLOCKED", prompt)
        self.assertIn("RESPONSE_EXPECTED", prompt)
        self.assertIn("Engineering memory gate:", prompt)
        self.assertIn("engineering_memory_gate.mjs", prompt)
        self.assertIn("Search the current repository and ATLAS docs directly", prompt)

    def test_every_intent_carries_the_precedent_lookup_gate(self) -> None:
        for payload in (
            self.mazer_payload,
            self.playbook_payload,
            self.lifeline_payload,
            self.topology_payload,
        ):
            precedent = payload["precedent_lookup"]
            self.assertTrue(precedent["required_before_mutation"])
            self.assertEqual(precedent["minimum_direct_search_sources"], ["current_repo", "atlas_docs"])
            self.assertIn("ops/atlas/engineering_memory_gate.mjs", precedent["gate_ref"])
            bootstrap_refs = {item["ref"] for item in payload["bootstrap_contract"]["ordered_reads"]}
            self.assertIn("docs/registry/ATLAS-ENGINEERING-MEMORY-POLICY.v1.json", bootstrap_refs)

    def test_bootstrap_includes_canonical_zachariah_profile(self) -> None:
        refs = {item["ref"] for item in self.mazer_payload["bootstrap_contract"]["ordered_reads"]}
        self.assertIn("docs/memory/profiles/zachariah_workflow_profile.md", refs)

    def test_every_context_inherits_book_ai_system_map(self) -> None:
        for payload in (
            self.mazer_payload,
            self.playbook_payload,
            self.lifeline_payload,
            self.topology_payload,
        ):
            refs = {item["ref"] for item in payload["bootstrap_contract"]["ordered_reads"]}
            self.assertIn("docs/atlas-book/AI-SYSTEM-MAP.v1.json", refs)

    def test_book_ai_system_map_is_recent_first_and_pointer_based(self) -> None:
        map_path = self.root / "docs" / "atlas-book" / "AI-SYSTEM-MAP.v1.json"
        payload = json.loads(map_path.read_text(encoding="utf-8"))
        self.assertEqual(payload["schema"], "atlas.book-ai-system-map.v1")
        self.assertEqual(payload["retrieval_policy"]["historical_priority"], "recent-first")
        self.assertEqual(payload["retrieval_policy"]["mode"], "minimal-then-expand")
        self.assertIn("ops/atlas/build_codex_context.py", payload["workflow_adoption"]["bootstrap_integration"])
        surface_ids = [surface["surface_id"] for surface in payload["surfaces"]]
        self.assertEqual(len(surface_ids), len(set(surface_ids)))
        for surface in payload["surfaces"]:
            for ref in surface.get("canonical_sources", []):
                self.assertTrue((self.root / ref).exists(), ref)

    def test_book_maps_playbook_capabilities_without_absorbing_atlas_authority(self) -> None:
        map_path = self.root / "docs" / "atlas-book" / "AI-SYSTEM-MAP.v1.json"
        payload = json.loads(map_path.read_text(encoding="utf-8"))
        integration = payload["playbook_integration"]
        self.assertIn("Playbook does not encapsulate Atlas", integration["architecture_decision"])
        group_ids = [group["group_id"] for group in integration["capability_groups"]]
        self.assertEqual(len(group_ids), len(set(group_ids)))
        commands = {
            command
            for group in integration["capability_groups"]
            for command in group["commands"]
        }
        for required in ("ai-context", "ai-contract", "verify", "plan", "apply", "receipt", "knowledge", "telemetry"):
            self.assertIn(required, commands)
        seam_ids = [seam["seam_id"] for seam in integration["consumer_seams"]]
        self.assertEqual(len(seam_ids), len(set(seam_ids)))
        for seam in integration["consumer_seams"]:
            for ref in seam["source_refs"]:
                self.assertTrue((self.root / ref).exists(), ref)
        self.assertIn("Do not install, build, upgrade, or activate Playbook implicitly", integration["workflow_gate"]["fallback"])

    def test_standing_baseline_inherits_guarded_playbook_first_rule(self) -> None:
        baseline = (self.root / "docs" / "prompts" / "atlas-workflow" / "STANDING-BASELINE.md").read_text(
            encoding="utf-8"
        )
        self.assertIn("content-addressed `ai-context` and `ai-contract` output", baseline)
        self.assertIn("Never install, build, upgrade, or activate Playbook implicitly", baseline)
        self.assertIn("never replaces the canonical Atlas job or", baseline)

    def test_stale_optional_proposal_does_not_block_context_bootstrap(self) -> None:
        payload = build_codex_context(
            task_id="topology-stale-proposal-tolerance",
            objective="Review Atlas Full-System Re-evaluation topology without executing its closing audit.",
            intent_class="topology/git",
            root=self.root,
        )
        refs = {item["ref"] for item in payload["bootstrap_contract"]["ordered_reads"]}
        self.assertIn("docs/atlas-book/AI-SYSTEM-MAP.v1.json", refs)

    def test_write_codex_context_pack_writes_expected_files(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            output_root = Path(temp_dir)
            write_codex_context_pack(
                task_id="mazer-context",
                objective="Prepare Codex context for the Mazer D2 scorer follow-up.",
                intent_class="operator/conversation",
                target_repo_ids=["mazer"],
                root=self.root,
                output_root=output_root,
                payload=self.mazer_payload,
            )
            task_dir = output_root / "mazer-context"
            self.assertTrue((task_dir / "context.json").exists())
            self.assertTrue((task_dir / "context.md").exists())

    def test_cli_defaults_to_compact_output_and_preserves_full_payload_opt_in(self) -> None:
        argv = [
            "--task-id",
            "cli-output",
            "--objective",
            "Prepare Codex context for the Mazer D2 scorer follow-up.",
            "--intent-class",
            "operator/conversation",
            "--target-repo",
            "mazer",
        ]
        with tempfile.TemporaryDirectory() as temp_dir:
            output_root = Path(temp_dir)
            with patch("ops.atlas.build_codex_context.build_codex_context", return_value=self.mazer_payload):
                compact_stdout = io.StringIO()
                with redirect_stdout(compact_stdout):
                    self.assertEqual(main([*argv, "--output-root", temp_dir]), 0)
                compact = json.loads(compact_stdout.getvalue())
                self.assertEqual(compact["status"], "written")
                self.assertEqual(compact["context_digest"], self.mazer_payload["context_digest"])
                self.assertFalse(compact["full_payload_stdout"])
                self.assertNotIn("selected_refs", compact)
                saved = json.loads((output_root / "cli-output" / "context.json").read_text(encoding="utf-8"))
                self.assertEqual(saved, self.mazer_payload)

                full_stdout = io.StringIO()
                with redirect_stdout(full_stdout):
                    self.assertEqual(main([*argv, "--output-root", temp_dir, "--print-payload"]), 0)
                full = json.loads(full_stdout.getvalue())
                self.assertEqual(full, self.mazer_payload)


if __name__ == "__main__":
    unittest.main()

