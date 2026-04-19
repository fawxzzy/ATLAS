from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from ops.atlas.shadow_events import emit_shadow_event


class AtlasShadowEventsTests(unittest.TestCase):
    def test_emit_shadow_event_writes_schema_valid_receipt(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            receipt_root = Path(temp_dir)
            result = emit_shadow_event(
                event_type="session_start",
                session_id="session-shadow-001",
                workspace_root=".",
                payload={
                    "trigger": "wrapper",
                    "intent": "Exercise the Atlas shadow telemetry lane.",
                    "workspace_scope": [
                        "runtime/atlas/sessions",
                    ],
                },
                event_token="session-start",
                receipt_root=receipt_root,
                strict=True,
            )

            self.assertTrue(result["ok"])
            receipt_path = receipt_root / "session_start" / Path(result["paths"]["receipt_path"]).name
            latest_path = receipt_root / "session_start" / "latest.json"
            self.assertTrue(receipt_path.exists())
            self.assertTrue(latest_path.exists())

            receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
            self.assertEqual(receipt["event"]["contract_version"], "atlas.event.v1")
            self.assertEqual(receipt["event"]["producer"]["name"], "atlas-session-runner-shadow")
            self.assertEqual(receipt["event"]["session"]["run_label"], "shadow-mode")
            self.assertEqual(receipt["processing"]["status"], "accepted")

    def test_emit_shadow_event_rejects_invalid_payload_in_strict_mode(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            with self.assertRaises(ValueError):
                emit_shadow_event(
                    event_type="task_start",
                    session_id="session-shadow-002",
                    workspace_root=".",
                    payload={
                        "task_summary": "Missing scoped paths should fail validation.",
                        "mutation_mode": "stack_only",
                    },
                    task={
                        "task_id": "task-shadow-002",
                        "task_name": "Shadow task",
                        "scope_paths": ["runtime/atlas/sessions"],
                        "repo_ids": ["stack"],
                        "mutation_mode": "stack_only",
                    },
                    event_token="task-start-invalid",
                    receipt_root=Path(temp_dir),
                    strict=True,
                )


if __name__ == "__main__":
    unittest.main()
