from __future__ import annotations

import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from ops.atlas.persist_thread_context import (
    ThreadContextError,
    build_checkpoint,
    persist_checkpoint,
)


class AtlasThreadContextTests(unittest.TestCase):
    def checkpoint(self, **overrides):
        payload = {
            "thread_id": "thread-123",
            "role_id": "owner.example",
            "title": "Example",
            "state": "ACTIVE",
            "summary": "Implement the bounded example packet.",
            "recorded_at": "2026-07-29T12:00:00Z",
            "done": ["Preflight passed."],
            "now": ["Focused tests are running."],
            "next_items": ["Return the exact receipt."],
            "decisions": ["No production action."],
            "blockers": [],
            "receipts": ["receipt:example"],
            "source_refs": ["git:example@abc123"],
        }
        payload.update(overrides)
        return build_checkpoint(**payload)

    def test_persists_immutable_latest_and_global_index(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            checkpoint = self.checkpoint()
            result = persist_checkpoint(checkpoint, output_root=root)
            immutable = Path(result["checkpoint_ref"])
            self.assertTrue(immutable.exists())
            self.assertEqual(checkpoint, json.loads((root / "thread-123" / "latest.json").read_text()))
            index = json.loads((root / "index.json").read_text())
            self.assertEqual("atlas.thread-context-index.v1", index["schema"])
            self.assertEqual("thread-123", index["threads"][0]["thread_id"])
            self.assertNotIn("raw_transcript_included", checkpoint["payload"])
            self.assertEqual("COMPACT_OPERATIONAL_CONTEXT", checkpoint["payload"]["content_class"])

    def test_exact_retry_is_idempotent(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            checkpoint = self.checkpoint()
            first = persist_checkpoint(checkpoint, output_root=root)
            second = persist_checkpoint(checkpoint, output_root=root)
            self.assertEqual(first["checkpoint_id"], second["checkpoint_id"])
            immutable = list((root / "thread-123").glob("threadctx_*.json"))
            self.assertEqual(1, len(immutable))

    def test_changed_checkpoint_appends_and_updates_latest(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            persist_checkpoint(self.checkpoint(), output_root=root)
            changed = self.checkpoint(
                state="WAITING",
                summary="Waiting for exact-head review.",
                recorded_at="2026-07-29T12:01:00Z",
            )
            persist_checkpoint(changed, output_root=root)
            immutable = list((root / "thread-123").glob("threadctx_*.json"))
            self.assertEqual(2, len(immutable))
            latest = json.loads((root / "thread-123" / "latest.json").read_text())
            self.assertEqual("WAITING", latest["payload"]["state"])

    def test_rejects_secret_like_context(self) -> None:
        with self.assertRaisesRegex(ThreadContextError, "prohibited sensitive material"):
            self.checkpoint(summary="Use key sk_SYNTHETIC0123456789 for the test.")

    def test_rejects_extended_sensitive_classes_without_echoing(self) -> None:
        sensitive_values = [
            "OAuth gho_0123456789abcdefghij must never persist.",
            "Supabase sb_secret_0123456789abcdefghij must never persist.",
            "Supabase sb_publishable_0123456789abcdefghij must never persist.",
            "Database postgresql://atlas:synthetic-password@example.invalid/db",
            "Authorization: Bearer eyJheader12345.eyJpayload12345.signature12345",
            "Cookie: sessionid=synthetic-cookie-value",
            "DATABASE_PASSWORD=synthetic-password-value",
        ]
        for value in sensitive_values:
            with self.subTest(value=value.split()[0]):
                with self.assertRaises(ThreadContextError) as raised:
                    self.checkpoint(summary=value)
                message = str(raised.exception)
                self.assertEqual("context contains prohibited sensitive material", message)
                self.assertNotIn("synthetic", message)

    def test_persistence_rejects_bypassed_supabase_keys_without_echoing(self) -> None:
        sensitive_values = [
            "sb_secret_0123456789abcdefghij",
            "sb_publishable_0123456789abcdefghij",
        ]
        for value in sensitive_values:
            with self.subTest(prefix=value.split("_", 2)[:2]):
                checkpoint = self.checkpoint()
                checkpoint["payload"]["summary"] = value
                canonical = json.dumps(
                    checkpoint["payload"],
                    ensure_ascii=False,
                    sort_keys=True,
                    separators=(",", ":"),
                ).encode("utf-8")
                digest = f"sha256:{hashlib.sha256(canonical).hexdigest()}"
                checkpoint["payload_digest"] = digest
                checkpoint["checkpoint_id"] = f"threadctx_{digest.removeprefix('sha256:')}"
                with tempfile.TemporaryDirectory() as temporary_directory:
                    with self.assertRaises(ThreadContextError) as raised:
                        persist_checkpoint(checkpoint, output_root=Path(temporary_directory))
                self.assertEqual(
                    "context contains prohibited sensitive material",
                    str(raised.exception),
                )
                self.assertNotIn("sb_", str(raised.exception))

    def test_rejects_unknown_state(self) -> None:
        with self.assertRaisesRegex(ThreadContextError, "state must be one of"):
            self.checkpoint(state="MAYBE")


if __name__ == "__main__":
    unittest.main()
