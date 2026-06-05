from __future__ import annotations

import io
import json
import unittest
from contextlib import redirect_stdout

from ops._atlas import atlas_root
from ops.cortex._artifacts import read_json
from ops.cortex.shadow_agent_registry import (
    SHADOW_AGENT_REGISTRY_CONTRACT_VERSION,
    ShadowAgentBlockedError,
    build_shadow_agent_registry_summary,
    default_shadow_agent_registry_path,
    load_shadow_agent_registry,
    main,
    resolve_shadow_agent_for_consumption,
)


class CortexShadowAgentRegistryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.root = atlas_root()

    def test_seed_loads_with_expected_shadow_and_blocked_families(self) -> None:
        path = default_shadow_agent_registry_path(self.root)
        payload = read_json(path)
        self.assertEqual(SHADOW_AGENT_REGISTRY_CONTRACT_VERSION, payload["contract_version"])

        registry = load_shadow_agent_registry(root=self.root)
        self.assertEqual(9, len(registry.agents))
        self.assertEqual(3, len(registry.eligible_agents))
        self.assertEqual(0, len(registry.exportable_agents))
        self.assertEqual(6, len(registry.blocked_agents))
        self.assertEqual(
            {
                "validation-summary-shadow",
                "marker-checkpoint-shadow",
                "receipt-doctrine-draft-shadow",
            },
            {item.agent_id for item in registry.eligible_agents},
        )
        self.assertIn(
            "fresh-live-proof-capture-blocked",
            {item.agent_id for item in registry.blocked_agents},
        )
        self.assertTrue(all(item.contract_id.startswith("atlas.cortex.contract.") for item in registry.agents))

    def test_blocked_families_are_non_runnable_with_reasons(self) -> None:
        registry = load_shadow_agent_registry(root=self.root)
        for item in registry.blocked_agents:
            self.assertFalse(item.runnable)
            self.assertIsNotNone(item.blocked_reason)
            self.assertTrue(item.blocked_reason)
            self.assertEqual("blocked", item.admissibility_state)

    def test_shadow_consumption_gate_allows_shadow_only_and_rejects_blocked(self) -> None:
        eligible = resolve_shadow_agent_for_consumption("validation-summary-shadow", root=self.root)
        self.assertEqual("atlas.cortex.contract.validation-summary-shadow.v1", eligible.contract_id)
        self.assertEqual("shadow-only", eligible.admissibility_state)

        with self.assertRaises(ShadowAgentBlockedError):
            resolve_shadow_agent_for_consumption("final-deploy-judgment-blocked", root=self.root)

    def test_summary_surface_is_deterministic_and_local_only(self) -> None:
        summary = build_shadow_agent_registry_summary(root=self.root)
        self.assertEqual(SHADOW_AGENT_REGISTRY_CONTRACT_VERSION, summary["contract_version"])
        self.assertEqual(9, summary["agent_count"])
        self.assertEqual(9, summary["contract_count"])
        self.assertEqual([], summary["exportable_contract_ids"])
        self.assertEqual(
            [
                "atlas.cortex.contract.validation-summary-shadow.v1",
                "atlas.cortex.contract.marker-checkpoint-shadow.v1",
                "atlas.cortex.contract.receipt-doctrine-draft-shadow.v1",
            ],
            summary["shadow_contract_ids"],
        )
        self.assertEqual(
            [
                "validation-summary-shadow",
                "marker-checkpoint-shadow",
                "receipt-doctrine-draft-shadow",
            ],
            summary["eligible_agent_ids"],
        )
        self.assertIn(
            "docs/ops/PLAYBOOK-EVERYWHERE-CORTEX-INTERFACE-CONTRACT-FIRST-AGENT-SHADOWING-PASS-1-2026-06-01.md",
            summary["source_receipts"],
        )
        json.dumps(summary, sort_keys=True)

    def test_cli_renders_json_summary(self) -> None:
        stdout = io.StringIO()
        with redirect_stdout(stdout):
            exit_code = main([])
        payload = json.loads(stdout.getvalue())
        self.assertEqual(0, exit_code)
        self.assertEqual(9, payload["agent_count"])
        self.assertEqual(6, len(payload["blocked_agent_ids"]))


if __name__ == "__main__":
    unittest.main()
