from __future__ import annotations

import hashlib
import json
import multiprocessing
import tempfile
import time
import unittest
from pathlib import Path
from queue import Empty
from unittest.mock import patch

from ops.atlas.persist_thread_context import (
    ThreadContextError,
    build_checkpoint,
    persist_checkpoint,
)


def _persist_checkpoint_worker(checkpoint, root, start_event, result_queue) -> None:
    import ops.atlas.persist_thread_context as context_module

    original_load_index = context_module._load_index

    def slow_load_index(path):
        index = original_load_index(path)
        time.sleep(0.2)
        return index

    context_module._load_index = slow_load_index
    if not start_event.wait(timeout=10):
        result_queue.put("start timeout")
        return
    try:
        context_module.persist_checkpoint(checkpoint, output_root=Path(root))
    except Exception as error:  # pragma: no cover - returned to the parent process
        result_queue.put(f"{type(error).__name__}: {error}")
    else:
        result_queue.put(None)


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

    def test_older_exact_retry_does_not_regress_latest_or_index(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            older = self.checkpoint()
            newer = self.checkpoint(
                state="TERMINAL",
                summary="The bounded packet is terminal.",
                recorded_at="2026-07-29T12:02:00Z",
            )
            persist_checkpoint(older, output_root=root)
            persist_checkpoint(newer, output_root=root)

            with patch("ops.atlas.persist_thread_context._atomic_write_json") as writer:
                result = persist_checkpoint(older, output_root=root)

            writer.assert_not_called()
            self.assertTrue(result["deduplicated"])
            latest = json.loads((root / "thread-123" / "latest.json").read_text())
            index = json.loads((root / "index.json").read_text())
            self.assertEqual(newer["checkpoint_id"], latest["checkpoint_id"])
            self.assertEqual(newer["checkpoint_id"], index["threads"][0]["checkpoint_id"])

    def test_concurrent_writers_preserve_both_shared_index_records(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            process_context = multiprocessing.get_context("spawn")
            start_event = process_context.Event()
            result_queue = process_context.Queue()
            checkpoints = [
                self.checkpoint(thread_id="thread-a", summary="First concurrent writer."),
                self.checkpoint(thread_id="thread-b", summary="Second concurrent writer."),
            ]
            processes = [
                process_context.Process(
                    target=_persist_checkpoint_worker,
                    args=(checkpoint, str(root), start_event, result_queue),
                )
                for checkpoint in checkpoints
            ]
            for process in processes:
                process.start()
            start_event.set()
            for process in processes:
                process.join(timeout=15)
                self.assertFalse(process.is_alive())
                self.assertEqual(0, process.exitcode)

            results = []
            for _ in processes:
                try:
                    results.append(result_queue.get(timeout=5))
                except Empty:
                    self.fail("Concurrent context writer did not return a result")
            self.assertEqual([None, None], sorted(results, key=lambda value: value or ""))
            index = json.loads((root / "index.json").read_text())
            self.assertEqual(
                ["thread-a", "thread-b"],
                [record["thread_id"] for record in index["threads"]],
            )

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

    def test_persistence_scan_covers_mapping_keys_and_tuple_values(self) -> None:
        sensitive_value = "sb_secret_0123456789abcdefghij"
        mutations = (
            lambda checkpoint: checkpoint["payload"].update({sensitive_value: "value"}),
            lambda checkpoint: checkpoint["payload"].update({"done": (sensitive_value,)}),
        )
        for mutate in mutations:
            with self.subTest(mutation=mutate):
                checkpoint = self.checkpoint()
                mutate(checkpoint)
                with tempfile.TemporaryDirectory() as temporary_directory:
                    root = Path(temporary_directory)
                    with self.assertRaises(ThreadContextError) as raised:
                        persist_checkpoint(checkpoint, output_root=root)
                    self.assertFalse(list(root.rglob("*.json")))
                self.assertEqual(
                    "context contains prohibited sensitive material",
                    str(raised.exception),
                )

    def test_persistence_rejects_noncanonical_shape_and_unsupported_values(self) -> None:
        checkpoints = []
        extra_field = self.checkpoint()
        extra_field["payload"]["unexpected"] = "value"
        checkpoints.append(extra_field)
        unsupported_value = self.checkpoint()
        unsupported_value["payload"]["done"] = {"not", "json"}
        checkpoints.append(unsupported_value)
        tuple_value = self.checkpoint()
        tuple_value["payload"]["done"] = ("not canonical",)
        checkpoints.append(tuple_value)
        for checkpoint in checkpoints:
            with self.subTest(value=checkpoint["payload"]["done"]):
                with tempfile.TemporaryDirectory() as temporary_directory:
                    root = Path(temporary_directory)
                    with self.assertRaisesRegex(
                        ThreadContextError,
                        "Malformed thread context checkpoint",
                    ):
                        persist_checkpoint(checkpoint, output_root=root)
                    self.assertFalse(list(root.rglob("*.json")))

    def test_checkpoint_id_is_digest_bound_and_cannot_escape_output_root(self) -> None:
        checkpoint = self.checkpoint()
        checkpoint["checkpoint_id"] = "..\\..\\escaped"
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory) / "context"
            with self.assertRaisesRegex(
                ThreadContextError,
                "checkpoint identity mismatch",
            ):
                persist_checkpoint(checkpoint, output_root=root)
            self.assertFalse((Path(temporary_directory) / "escaped.json").exists())
            self.assertFalse(root.exists())

    def test_thread_directory_must_remain_under_output_root(self) -> None:
        checkpoint = self.checkpoint(thread_id="..")
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory) / "context"
            with self.assertRaisesRegex(ThreadContextError, "safe path component"):
                persist_checkpoint(checkpoint, output_root=root)
            self.assertFalse(root.exists())

    def test_thread_directory_uses_cross_platform_safe_components(self) -> None:
        unsafe_ids = ["thread:123", "thread.", "CON", "con.txt", "COM1", "LPT9.log"]
        for thread_id in unsafe_ids:
            with self.subTest(thread_id=thread_id):
                checkpoint = self.checkpoint(thread_id=thread_id)
                with tempfile.TemporaryDirectory() as temporary_directory:
                    root = Path(temporary_directory) / "context"
                    with self.assertRaisesRegex(ThreadContextError, "safe path component"):
                        persist_checkpoint(checkpoint, output_root=root)
                    self.assertFalse(root.exists())

    def test_filesystem_path_failure_is_wrapped_before_json_write(self) -> None:
        checkpoint = self.checkpoint()
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory) / "context"
            root.write_text("not a directory", encoding="utf-8")
            with self.assertRaisesRegex(ThreadContextError, "Unable to prepare"):
                persist_checkpoint(checkpoint, output_root=root)
            self.assertEqual("not a directory", root.read_text(encoding="utf-8"))
            self.assertFalse(list(Path(temporary_directory).rglob("*.json")))

    def test_rejects_unknown_state(self) -> None:
        with self.assertRaisesRegex(ThreadContextError, "state must be one of"):
            self.checkpoint(state="MAYBE")


if __name__ == "__main__":
    unittest.main()
