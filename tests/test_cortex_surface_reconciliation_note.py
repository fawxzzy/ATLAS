from __future__ import annotations

import unittest

from ops._atlas import atlas_root


class CortexSurfaceReconciliationNoteTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        root = atlas_root()
        cls.inventory_note = (root / "docs" / "atlas" / "notes" / "cortex-mvp-inventory-2026-04-26.md").read_text(
            encoding="utf-8"
        )
        cls.reconciliation_note = (
            root / "docs" / "atlas" / "notes" / "cortex-surface-reconciliation-2026-05-06.md"
        ).read_text(encoding="utf-8")

    def test_inventory_note_points_to_live_reconciliation_note(self) -> None:
        self.assertIn("cortex-surface-reconciliation-2026-05-06.md", self.inventory_note)
        self.assertIn("dated 2026-04-26 snapshot", self.inventory_note)

    def test_reconciliation_note_mentions_landed_surfaces_and_remaining_gaps(self) -> None:
        for required in (
            "ops/cortex/context_assembler.py",
            "ops/cortex/worker_plan.py",
            "ops/cortex/proof_receipt.py",
            "ops/cortex/run_ledger.py",
            "ops/cortex/lifeline_write_adapter.py",
            "single operator entrypoint",
            "Final Lifeline receipt emission remains gated.",
        ):
            self.assertIn(required, self.reconciliation_note)


if __name__ == "__main__":
    unittest.main()
