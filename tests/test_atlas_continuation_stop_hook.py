import io
import json
import subprocess
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest import mock

from ops.atlas.atlas_runtime import AtlasRuntime
from ops.atlas.atlasd import (
    CodexPersistentThreadAdapter,
    ContinuationDispatcher,
    FixtureTriggerAdapter,
    SingleInstanceGuard,
    _closed_trigger_readback,
)
from ops.atlas.continuation_stop_hook import main as stop_hook_main


class HostileMapping(dict):
    def __getitem__(self, key):
        if key == "turn_id":
            raise RuntimeError("sensitive hostile payload")
        return super().__getitem__(key)


class AcceptedThenLostAdapter:
    def __init__(self):
        self.calls = 0

    def start_existing_turn(self, **kwargs):
        self.calls += 1
        raise RuntimeError("readback lost after external acceptance")


class DurableContinuationKernelTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.database = Path(self.tmp.name) / "atlas.db"
        self.runtime = AtlasRuntime(self.database)
        self.runtime.register_continuation_owner(owner_id="owner.test", thread_id="thread-existing")
        first = self.runtime.create_context_pack({"summary": "first", "source_refs": ["receipt:first"]})
        second = self.runtime.create_context_pack({"summary": "second", "source_refs": ["receipt:second"]})
        self.runtime.register_continuation_packet(
            packet_id="packet-1", owner_id="owner.test", conflict_key="repo:a", context_pack_id=first
        )
        self.runtime.register_continuation_packet(
            packet_id="packet-2", owner_id="owner.test", conflict_key="repo:b",
            context_pack_id=second, after_packet_id="packet-1", priority=10,
        )
        self.runtime.activate_continuation_packet(packet_id="packet-1")

    def tearDown(self):
        self.runtime.close()
        self.tmp.cleanup()

    def commit(self, **kwargs):
        return self.runtime.commit_continuation(
            packet_id="packet-1",
            terminal_receipt={"event_id": "terminal-1", "result": "SEALED"},
            expected_owner_revision=1,
            **kwargs,
        )

    def test_atomic_terminal_successor_claim_and_outbox(self):
        result = self.commit()
        self.assertEqual(result.successor_packet_id, "packet-2")
        self.assertTrue(result.trigger_key.startswith("trg_"))
        self.assertEqual(self.runtime.continuation_status()["packets_by_state"], {
            "DISPATCH_PENDING": 1, "SETTLED": 1,
        })
        self.assertEqual(self.runtime.continuation_status()["active_claims"], 1)

    def test_fault_injection_rolls_back_settlement_and_outbox(self):
        with self.assertRaisesRegex(RuntimeError, "fault injection"):
            self.commit(fail_after="outbox")
        self.assertEqual(
            self.runtime.db.execute(
                "SELECT state FROM continuation_packets WHERE packet_id='packet-1'"
            ).fetchone()["state"],
            "ACTIVE",
        )
        self.assertEqual(
            self.runtime.db.execute("SELECT COUNT(*) FROM continuation_outbox").fetchone()[0], 0
        )

    def test_exact_replay_is_noop_and_changed_replay_fails(self):
        first = self.commit()
        second = self.commit()
        self.assertTrue(second.replayed)
        self.assertEqual(second.trigger_key, first.trigger_key)
        with self.assertRaises(ValueError):
            self.runtime.commit_continuation(
                packet_id="packet-1",
                terminal_receipt={"event_id": "terminal-1", "result": "CHANGED"},
                expected_owner_revision=1,
            )

    def test_same_session_stop_hook_excludes_one_shot_dispatch(self):
        committed = self.commit()
        stdin = io.StringIO(json.dumps({"owner_id": "owner.test"}))
        stdout = io.StringIO()
        with mock.patch("sys.stdin", stdin), redirect_stdout(stdout):
            self.assertEqual(stop_hook_main(["--database", str(self.database)]), 0)
        decision = json.loads(stdout.getvalue())
        self.assertEqual(decision["decision"], "block")
        self.assertIn(committed.trigger_key, decision["reason"])
        adapter = FixtureTriggerAdapter()
        readback = ContinuationDispatcher(self.runtime, adapter).dispatch_one(worker_id="fixture")
        self.assertIsNone(readback)
        self.assertEqual(adapter.calls, [])
        row = self.runtime.db.execute(
            "SELECT state,delivery_method FROM continuation_outbox WHERE trigger_key=?",
            (committed.trigger_key,),
        ).fetchone()
        self.assertEqual((row["state"], row["delivery_method"]), ("DISPATCHED", "STOP_HOOK"))

    def test_stop_hook_resolves_official_session_id_and_honors_active_guard(self):
        self.commit()
        stdout = io.StringIO()
        with mock.patch("sys.stdin", io.StringIO(json.dumps({"session_id": "thread-existing"}))), redirect_stdout(stdout):
            stop_hook_main(["--database", str(self.database)])
        self.assertEqual(json.loads(stdout.getvalue())["decision"], "block")
        guarded = io.StringIO()
        with mock.patch(
            "sys.stdin",
            io.StringIO(json.dumps({"session_id": "thread-existing", "stop_hook_active": True})),
        ), redirect_stdout(guarded):
            stop_hook_main(["--database", str(self.database)])
        self.assertEqual(json.loads(guarded.getvalue()), {})

    def test_stop_hook_unbound_malformed_and_unavailable_allow_stop(self):
        for payload in ({"session_id": "unknown"}, [], {"session_id": ""}):
            with self.subTest(payload=payload):
                stdout = io.StringIO()
                with mock.patch("sys.stdin", io.StringIO(json.dumps(payload))), redirect_stdout(stdout):
                    stop_hook_main(["--database", str(self.database)])
                self.assertEqual(json.loads(stdout.getvalue()), {})
        stdout = io.StringIO()
        unavailable = Path(self.tmp.name) / "missing-parent" / "atlas.db"
        with mock.patch("sys.stdin", io.StringIO(json.dumps({"session_id": "thread-existing"}))), redirect_stdout(stdout):
            stop_hook_main(["--database", str(unavailable)])
        self.assertEqual(json.loads(stdout.getvalue()), {})

    def test_accepted_then_lost_readback_is_never_retried(self):
        committed = self.commit()
        adapter = AcceptedThenLostAdapter()
        dispatcher = ContinuationDispatcher(self.runtime, adapter)
        with self.assertRaisesRegex(RuntimeError, "readback lost"):
            dispatcher.dispatch_one(worker_id="fixture")
        row = self.runtime.db.execute(
            "SELECT state,error_class,confirmation_deadline FROM continuation_outbox WHERE trigger_key=?",
            (committed.trigger_key,),
        ).fetchone()
        self.assertEqual((row["state"], row["error_class"]),
                         ("DISPATCHED", "EXTERNAL_EFFECT_UNCONFIRMED"))
        self.assertIsNone(dispatcher.dispatch_one(worker_id="fixture"))
        self.assertEqual(adapter.calls, 1)
        actions = self.runtime.reconcile_continuation_startup(
            now=row["confirmation_deadline"] + 1
        )
        self.assertIn({"trigger_key": committed.trigger_key, "action": "DEAD_LETTER_AMBIGUOUS"}, actions)

    def test_restart_requeues_unsent_lease_and_dispatches_once(self):
        committed = self.commit()
        leased = self.runtime.lease_continuation_trigger(worker_id="crashed", lease_seconds=0.01)
        self.assertEqual(leased.trigger_key, committed.trigger_key)
        self.runtime.close()
        self.runtime = AtlasRuntime(self.database)
        actions = self.runtime.reconcile_continuation_startup(now=leased.leased_until + 1)
        self.assertIn({"trigger_key": committed.trigger_key, "action": "REQUEUED_UNSENT"}, actions)
        adapter = FixtureTriggerAdapter()
        ContinuationDispatcher(self.runtime, adapter).dispatch_one(worker_id="restart")
        self.assertEqual(len(adapter.calls), 1)

    def test_sent_unconfirmed_becomes_ambiguous_dead_letter(self):
        committed = self.commit()
        lease = self.runtime.lease_continuation_trigger(worker_id="worker")
        self.runtime.mark_continuation_trigger_dispatched(
            trigger_key=lease.trigger_key, worker_id="worker", confirmation_seconds=0.01
        )
        row = self.runtime.db.execute(
            "SELECT confirmation_deadline FROM continuation_outbox WHERE trigger_key=?",
            (committed.trigger_key,),
        ).fetchone()
        actions = self.runtime.reconcile_continuation_startup(now=row["confirmation_deadline"] + 1)
        self.assertIn({"trigger_key": committed.trigger_key, "action": "DEAD_LETTER_AMBIGUOUS"}, actions)

    def test_wrong_turn_identity_does_not_mutate_dispatched_row(self):
        committed = self.commit()
        lease = self.runtime.lease_continuation_trigger(worker_id="worker")
        self.runtime.mark_continuation_trigger_dispatched(
            trigger_key=lease.trigger_key, worker_id="worker"
        )
        with self.assertRaises(ValueError):
            self.runtime.confirm_continuation_trigger(
                trigger_key=committed.trigger_key, thread_id="wrong", turn_id="turn-1"
            )
        self.assertEqual(
            self.runtime.db.execute(
                "SELECT state FROM continuation_outbox WHERE trigger_key=?", (committed.trigger_key,)
            ).fetchone()["state"],
            "DISPATCHED",
        )

    def test_capacity_exhaustion_is_resumable(self):
        committed = self.commit()
        self.runtime.lease_continuation_trigger(worker_id="worker")
        state = self.runtime.fail_continuation_trigger(
            trigger_key=committed.trigger_key,
            worker_id="worker",
            error_class="CAPACITY_EXHAUSTED",
        )
        self.assertEqual(state, "PENDING")
        self.assertEqual(
            self.runtime.db.execute(
                "SELECT state FROM continuation_packets WHERE packet_id='packet-2'"
            ).fetchone()["state"],
            "RESUMABLE_QUEUED",
        )

    def test_unproven_cost_blocks_successor_without_outbox(self):
        third = self.runtime.create_context_pack({"summary": "paid", "source_refs": ["decision:x"]})
        self.runtime.register_continuation_packet(
            packet_id="packet-paid", owner_id="owner.test", conflict_key="billing:x",
            context_pack_id=third, after_packet_id="packet-1", priority=100,
            cost_kind="UNKNOWN",
        )
        result = self.commit()
        self.assertEqual(result.successor_packet_id, "packet-paid")
        self.assertIsNone(result.trigger_key)
        self.assertEqual(
            self.runtime.db.execute(
                "SELECT state FROM continuation_packets WHERE packet_id='packet-paid'"
            ).fetchone()["state"],
            "BLOCKED_COST",
        )
        self.assertEqual(self.runtime.db.execute("SELECT COUNT(*) FROM continuation_outbox").fetchone()[0], 0)

    def test_active_without_direct_restart_evidence_is_unexpected_idle(self):
        self.commit()
        adapter = FixtureTriggerAdapter()
        ContinuationDispatcher(self.runtime, adapter).dispatch_one(worker_id="fixture")
        actions = self.runtime.reconcile_continuation_startup(observed_turns={})
        self.assertIn({"owner_id": "owner.test", "action": "REDISPATCH_UNEXPECTED_IDLE"}, actions)
        owner = self.runtime.continuation_status()["owners"][0]
        self.assertEqual(owner["desired_state"], "DISPATCH_PENDING")
        self.assertEqual(owner["observed_state"], "UNEXPECTED_IDLE")
        before = self.runtime.db.execute(
            "SELECT COUNT(*) FROM continuation_outbox WHERE state='PENDING'"
        ).fetchone()[0]
        self.assertEqual(self.runtime.reconcile_continuation_startup(observed_turns={}), ())
        self.assertEqual(
            self.runtime.db.execute(
                "SELECT COUNT(*) FROM continuation_outbox WHERE state='PENDING'"
            ).fetchone()[0],
            before,
        )

    def test_deterministic_failure_is_not_retried(self):
        committed = self.commit()
        self.runtime.lease_continuation_trigger(worker_id="worker")
        state = self.runtime.fail_continuation_trigger(
            trigger_key=committed.trigger_key,
            worker_id="worker",
            error_class="IDENTITY_MISMATCH",
        )
        self.assertEqual(state, "DEAD_LETTER")
        self.assertIsNone(self.runtime.lease_continuation_trigger(worker_id="other"))

    def test_conflicting_scope_serializes_while_independent_scope_advances(self):
        other = AtlasRuntime(Path(self.tmp.name) / "other.db")
        try:
            other.register_continuation_owner(owner_id="owner.a", thread_id="thread-a")
            other.register_continuation_owner(owner_id="owner.b", thread_id="thread-b")
            pack = other.create_context_pack({"summary": "x", "source_refs": ["x"]})
            other.register_continuation_packet(
                packet_id="a", owner_id="owner.a", conflict_key="repo:shared", context_pack_id=pack
            )
            other.register_continuation_packet(
                packet_id="b", owner_id="owner.b", conflict_key="repo:shared", context_pack_id=pack
            )
            other.register_continuation_packet(
                packet_id="c", owner_id="owner.b", conflict_key="repo:independent",
                context_pack_id=pack,
            )
            other.activate_continuation_packet(packet_id="a")
            with self.assertRaises(Exception):
                other.activate_continuation_packet(packet_id="b")
            self.assertTrue(other.activate_continuation_packet(packet_id="c"))
        finally:
            other.close()

    def test_projection_export_is_byte_for_byte_deterministic(self):
        self.commit()
        first = self.runtime.export_continuation_projection()
        second = self.runtime.export_continuation_projection()
        self.assertEqual(first, second)
        self.assertEqual(json.loads(first)["schema"], "atlas.durable-continuation-kernel.projection.v1")

    def test_read_only_scheduler_import_and_drive_relative_rejection(self):
        valid = Path(self.tmp.name) / "scheduler.json"
        valid.write_text(json.dumps({"revision": 1129, "jobs": []}), encoding="utf-8")
        before = self.runtime.export_continuation_projection()
        result = self.runtime.inspect_json_scheduler(valid)
        self.assertEqual(result["revision"], 1129)
        self.assertFalse(result["mutated"])
        self.assertEqual(self.runtime.export_continuation_projection(), before)
        invalid = Path(self.tmp.name) / "invalid.json"
        invalid.write_text(json.dumps({"program": "C:ATLAS\\runner.py"}), encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "drive-relative"):
            self.runtime.inspect_json_scheduler(invalid)

    def test_duplicate_dispatch_is_noop_after_confirmation(self):
        self.commit()
        adapter = FixtureTriggerAdapter()
        dispatcher = ContinuationDispatcher(self.runtime, adapter)
        self.assertIsNotNone(dispatcher.dispatch_one(worker_id="fixture"))
        self.assertIsNone(dispatcher.dispatch_one(worker_id="fixture"))
        self.assertEqual(len(adapter.calls), 1)

    def test_worker_guard_is_single_instance(self):
        path = Path(self.tmp.name) / "worker.lock"
        with SingleInstanceGuard(path):
            with self.assertRaisesRegex(RuntimeError, "already active"):
                with SingleInstanceGuard(path):
                    pass

    def test_context_pack_rejects_secrets_and_raw_outputs(self):
        for payload in (
            {"secret": "x"}, {"nested": {"raw_output": "x"}}, {"prompt": "x"},
            {"__proto__": {"polluted": True}}, {"path": "C:ATLAS\\runner.py"},
        ):
            with self.subTest(payload=payload), self.assertRaises(ValueError):
                self.runtime.create_context_pack(payload)

    def test_hostile_readback_is_non_echoing(self):
        with self.assertRaisesRegex(ValueError, "fields are unavailable") as error:
            _closed_trigger_readback(
                HostileMapping(thread_id="thread-existing", turn_id="x", status="accepted"),
                expected_thread_id="thread-existing",
            )
        self.assertNotIn("sensitive hostile payload", str(error.exception))
        with self.assertRaisesRegex(ValueError, "structural limits"):
            _closed_trigger_readback(
                {"thread_id": "thread-existing", "turn_id": "x" * 257, "status": "accepted"},
                expected_thread_id="thread-existing",
            )

    def test_codex_adapter_has_no_thread_start_and_requires_one_match(self):
        responses = [
            subprocess.CompletedProcess(
                args=[], returncode=0,
                stdout=json.dumps({"thread_id": "thread-existing", "turn_id": "turn-1", "status": "accepted"}) + "\n",
                stderr="",
            ),
            subprocess.CompletedProcess(
                args=[], returncode=0,
                stdout=(json.dumps({"thread_id": "thread-existing", "turn_id": "turn-1"}) + "\n" +
                        json.dumps({"thread_id": "thread-existing", "turn_id": "turn-2"}) + "\n"),
                stderr="",
            ),
        ]
        commands = []

        def runner(command, **kwargs):
            commands.append(command)
            return responses.pop(0)

        adapter = CodexPersistentThreadAdapter(runner=runner)
        result = adapter.start_existing_turn(
            thread_id="thread-existing", trigger_key="trg_x", continuation_input="{}"
        )
        self.assertEqual(result.turn_id, "turn-1")
        self.assertEqual(commands[0][1:3], ["exec", "resume"])
        self.assertNotIn("thread/start", commands[0])
        with self.assertRaises(ValueError):
            adapter.start_existing_turn(
                thread_id="thread-existing", trigger_key="trg_x", continuation_input="{}"
            )


if __name__ == "__main__":
    unittest.main()
