from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from ops._atlas import atlas_root
from ops.atlas.build_codex_context import build_codex_context, render_codex_prompt, write_codex_context_pack


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
        self.assertTrue(any("6a9aeb06d039913aeed84e9f24a209e53bdbcdb2285a1cf409a51c7c69a2f880" in ref for ref in attention_refs))
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
            "repos/fawxzzy-lifeline/examples/privileged-execution/read-only-scan.request.json",
            route_refs,
        )
        self.assertIn(
            "repos/fawxzzy-lifeline/examples/privileged-execution/read-only-scan.approval.json",
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

    def test_bootstrap_includes_canonical_zachariah_profile(self) -> None:
        refs = {item["ref"] for item in self.mazer_payload["bootstrap_contract"]["ordered_reads"]}
        self.assertIn("docs/memory/profiles/zachariah_workflow_profile.md", refs)

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


if __name__ == "__main__":
    unittest.main()

