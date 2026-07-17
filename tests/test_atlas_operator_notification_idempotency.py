from __future__ import annotations

import json
import sqlite3
import tempfile
import threading
import unittest
from concurrent.futures import ThreadPoolExecutor
from contextlib import closing
from pathlib import Path

from jsonschema import Draft202012Validator, FormatChecker

from ops.atlas.operator_notification_idempotency import (
    ACK_CONTRACT_VERSION,
    EVENT_CONTRACT_VERSION,
    LedgerCorruptionError,
    NotificationContractError,
    NotificationLedger,
    UnknownLedgerSchemaError,
    build_event,
)


ROOT = Path(__file__).resolve().parents[1]
EVENT_SCHEMA = ROOT / "schemas" / "atlas.operator-notification.event.v1.json"
ACK_SCHEMA = ROOT / "schemas" / "atlas.operator-notification.ack.v1.json"
THREAD_ID = "019f52d9-7667-72a3-a5f7-9c0613aedd8f"
CREATED = "2026-07-17T14:00:00Z"
SEEN = "2026-07-17T14:00:01Z"
ACKED = "2026-07-17T14:00:02Z"


class OperatorNotificationIdempotencyTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.runtime_root = Path(self.temporary.name) / "runtime"
        self.ledger_path = self.runtime_root / "atlas" / "notifications" / "receive.sqlite3"
        self.ledger = NotificationLedger(self.runtime_root, self.ledger_path)

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def event(
        self,
        facts: dict | None = None,
        *,
        transport: dict | None = None,
        event_class: str = "task.completion",
        notification_kind: str = "operator_update",
        created_at: str = CREATED,
        supersedes_event_id: str | None = None,
        delta: dict | None = None,
    ) -> dict:
        return build_event(
            source_thread_id=THREAD_ID,
            event_class=event_class,
            notification_kind=notification_kind,
            created_at=created_at,
            supersedes_event_id=supersedes_event_id,
            delta=delta,
            payload={
                "facts": facts or {"status": "ready", "card_id": "ATLAS-1"},
                "transport": transport or {"host_id": "host-a", "attempt": 1},
            },
        )

    def claim(self, event: dict, **kwargs) -> dict:
        return self.ledger.claim(
            event,
            claimant_id=kwargs.pop("claimant_id", "host-a"),
            seen_at=kwargs.pop("seen_at", SEEN),
            **kwargs,
        )

    def test_schemas_compile_and_validate_generated_contracts(self) -> None:
        event_schema = json.loads(EVENT_SCHEMA.read_text(encoding="utf-8"))
        ack_schema = json.loads(ACK_SCHEMA.read_text(encoding="utf-8"))
        Draft202012Validator.check_schema(event_schema)
        Draft202012Validator.check_schema(ack_schema)
        event = self.event()
        Draft202012Validator(
            event_schema, format_checker=FormatChecker()
        ).validate(event)
        claim = self.claim(event)
        ack = self.ledger.acknowledge(
            event["event_id"],
            claim_token=claim["claim_token"],
            acknowledged_at=ACKED,
        )
        Draft202012Validator(
            ack_schema, format_checker=FormatChecker()
        ).validate(ack)
        self.assertEqual(event["contract_version"], EVENT_CONTRACT_VERSION)
        self.assertEqual(ack["contract_version"], ACK_CONTRACT_VERSION)

    def test_exact_duplicate_is_recorded_without_second_emission(self) -> None:
        event = self.event()
        first = self.claim(event)
        duplicate = self.ledger.claim(
            event,
            claimant_id="host-a",
            seen_at="2026-07-17T14:00:02Z",
        )
        self.assertTrue(first["should_emit"])
        self.assertFalse(duplicate["should_emit"])
        self.assertEqual(duplicate["disposition"], "duplicate_exact")
        self.assertEqual(self.ledger.record(event["event_id"])["duplicate_count"], 1)

    def test_semantic_duplicate_ignores_declared_transport_volatility(self) -> None:
        first = self.event(transport={"host_id": "host-a", "attempt": 1})
        retry = self.event(
            transport={"host_id": "host-b", "attempt": 99},
            created_at="2026-07-17T14:05:00Z",
        )
        self.assertEqual(first["event_id"], retry["event_id"])
        self.assertEqual(
            first["canonical_payload_digest"], retry["canonical_payload_digest"]
        )
        self.assertNotEqual(
            first["transport_envelope_digest"], retry["transport_envelope_digest"]
        )
        self.claim(first)
        result = self.ledger.claim(
            retry,
            claimant_id="host-b",
            seen_at="2026-07-17T14:00:02Z",
        )
        self.assertFalse(result["should_emit"])
        self.assertEqual(result["disposition"], "duplicate_semantic")

    def test_changed_payload_requires_delta_and_creates_new_event(self) -> None:
        first = self.event()
        self.claim(first)
        missing_delta = self.event(
            facts={"status": "complete", "card_id": "ATLAS-1"}
        )
        with self.assertRaisesRegex(NotificationContractError, "supersede"):
            self.claim(missing_delta)
        changed = self.event(
            facts={"status": "complete", "card_id": "ATLAS-1"},
            supersedes_event_id=first["event_id"],
            delta={"changed_fact_paths": ["/status"]},
        )
        result = self.ledger.claim(
            changed,
            claimant_id="host-b",
            seen_at="2026-07-17T14:00:03Z",
        )
        self.assertNotEqual(first["event_id"], changed["event_id"])
        self.assertTrue(result["should_emit"])

    def test_supersession_is_machine_readable_in_both_records(self) -> None:
        first = self.event()
        self.claim(first)
        changed = self.event(
            facts={"status": "complete", "card_id": "ATLAS-1"},
            supersedes_event_id=first["event_id"],
            delta={"changed_fact_paths": ["/status"]},
        )
        self.ledger.claim(
            changed,
            claimant_id="host-b",
            seen_at="2026-07-17T14:00:03Z",
        )
        predecessor = self.ledger.record(first["event_id"])
        successor = self.ledger.record(changed["event_id"])
        self.assertEqual(
            predecessor["supersession"]["superseded_by_event_id"], changed["event_id"]
        )
        self.assertEqual(
            successor["supersession"],
            {
                "supersedes_event_id": first["event_id"],
                "superseded_by_event_id": None,
                "delta": {"changed_fact_paths": ["/status"]},
            },
        )
        stale_retry = self.ledger.claim(
            first,
            claimant_id="stale-host",
            seen_at="2026-07-18T14:00:00Z",
        )
        self.assertFalse(stale_retry["should_emit"])
        self.assertEqual(stale_retry["disposition"], "duplicate_superseded")

    def test_cross_host_retry_has_identical_event_identity(self) -> None:
        host_a = self.event(transport={"host_id": "windows-a", "attempt": 1})
        host_b = self.event(
            transport={"host_id": "linux-b", "attempt": 2},
            created_at="2026-07-18T01:00:00Z",
        )
        self.assertEqual(host_a["event_id"], host_b["event_id"])
        self.claim(host_a)
        result = self.ledger.claim(
            host_b,
            claimant_id="linux-b",
            seen_at="2026-07-17T14:00:02Z",
        )
        self.assertFalse(result["operator_message_authorized"])

    def test_acknowledgement_stops_retry_and_replays_stable_control_ack(self) -> None:
        event = self.event()
        claim = self.claim(event)
        ack = self.ledger.acknowledge(
            event["event_id"],
            claim_token=claim["claim_token"],
            acknowledged_at=ACKED,
        )
        self.assertFalse(
            self.ledger.should_retry(event["event_id"], at="2026-07-18T00:00:00Z")
        )
        duplicate = self.ledger.claim(
            event,
            claimant_id="host-b",
            seen_at="2026-07-18T00:00:00Z",
        )
        self.assertEqual(duplicate["disposition"], "duplicate_acked")
        self.assertFalse(duplicate["should_emit"])
        self.assertEqual(duplicate["ack"]["ack_id"], ack["ack_id"])
        self.assertEqual(duplicate["ack"]["ack_disposition"], "replayed")
        self.assertFalse(duplicate["ack"]["operator_message_authorized"])

    def test_duplicate_ack_does_not_create_a_second_ack_or_message(self) -> None:
        event = self.event()
        claim = self.claim(event)
        first = self.ledger.acknowledge(
            event["event_id"],
            claim_token=claim["claim_token"],
            acknowledged_at=ACKED,
        )
        second = self.ledger.acknowledge(
            event["event_id"],
            claim_token=claim["claim_token"],
            acknowledged_at="2026-07-17T14:10:00Z",
        )
        self.assertEqual(first["ack_id"], second["ack_id"])
        self.assertEqual(first["acknowledged_at"], second["acknowledged_at"])
        self.assertEqual(second["ack_disposition"], "replayed")
        self.assertFalse(second["operator_message_authorized"])

    def test_heartbeat_and_continuation_never_replay_operator_message(self) -> None:
        event = self.event()
        claim = self.claim(event)
        self.ledger.acknowledge(
            event["event_id"],
            claim_token=claim["claim_token"],
            acknowledged_at=ACKED,
        )
        for kind in ("heartbeat", "continuation"):
            control = self.event(
                event_class=f"task.{kind}",
                notification_kind=kind,
                created_at="2026-07-17T15:00:00Z",
            )
            result = self.ledger.claim(
                control,
                claimant_id="host-b",
                seen_at="2026-07-17T15:00:01Z",
            )
            self.assertFalse(result["should_emit"])
            self.assertEqual(result["disposition"], "suppressed_control")
            self.assertFalse(
                self.ledger.should_retry(
                    control["event_id"], at="2026-07-18T00:00:00Z"
                )
            )

    def test_restart_recovery_preserves_deduplication_and_ack(self) -> None:
        event = self.event()
        claim = self.claim(event)
        expected_ack = self.ledger.acknowledge(
            event["event_id"],
            claim_token=claim["claim_token"],
            acknowledged_at=ACKED,
        )
        restarted = NotificationLedger(self.runtime_root, self.ledger_path)
        result = restarted.claim(
            event,
            claimant_id="host-after-restart",
            seen_at="2026-07-18T00:00:00Z",
        )
        self.assertFalse(result["should_emit"])
        self.assertEqual(result["ack"]["ack_id"], expected_ack["ack_id"])

    def test_corrupt_and_unknown_ledger_schema_fail_closed(self) -> None:
        corrupt_path = self.runtime_root / "atlas" / "notifications" / "corrupt.sqlite3"
        corrupt_path.write_bytes(b"not-a-sqlite-database")
        with self.assertRaises(LedgerCorruptionError):
            NotificationLedger(self.runtime_root, corrupt_path)

        unknown_path = self.runtime_root / "atlas" / "notifications" / "unknown.sqlite3"
        NotificationLedger(self.runtime_root, unknown_path)
        with closing(sqlite3.connect(unknown_path)) as connection:
            connection.execute(
                "UPDATE ledger_meta SET value='atlas.operator-notification.ledger.v999' "
                "WHERE key='schema_version'"
            )
            connection.commit()
        with self.assertRaises(UnknownLedgerSchemaError):
            NotificationLedger(self.runtime_root, unknown_path)

    def test_concurrent_duplicate_claim_allows_exactly_one_emission(self) -> None:
        event = self.event()
        barrier = threading.Barrier(12)

        def attempt(index: int) -> dict:
            barrier.wait()
            return self.ledger.claim(
                event,
                claimant_id=f"host-{index}",
                seen_at=SEEN,
            )

        with ThreadPoolExecutor(max_workers=12) as executor:
            results = list(executor.map(attempt, range(12)))
        self.assertEqual(sum(result["should_emit"] for result in results), 1)
        self.assertEqual(self.ledger.record(event["event_id"])["duplicate_count"], 11)

    def test_concurrent_first_open_and_claim_allows_exactly_one_emission(self) -> None:
        event = self.event(event_class="task.concurrent-startup")
        ledger_path = (
            self.runtime_root / "atlas" / "notifications" / "startup.sqlite3"
        )
        barrier = threading.Barrier(12)

        def attempt(index: int) -> dict:
            barrier.wait()
            ledger = NotificationLedger(self.runtime_root, ledger_path)
            return ledger.claim(
                event,
                claimant_id=f"startup-host-{index}",
                seen_at=SEEN,
            )

        with ThreadPoolExecutor(max_workers=12) as executor:
            results = list(executor.map(attempt, range(12)))
        ledger = NotificationLedger(self.runtime_root, ledger_path)
        self.assertEqual(sum(result["should_emit"] for result in results), 1)
        self.assertEqual(ledger.record(event["event_id"])["duplicate_count"], 11)

    def test_expired_claim_can_be_retried_exactly_once(self) -> None:
        event = self.event()
        first = self.claim(event, lease_seconds=1)
        retry = self.ledger.claim(
            event,
            claimant_id="recovery-host",
            seen_at="2026-07-17T14:00:03Z",
            lease_seconds=30,
        )
        duplicate = self.ledger.claim(
            event,
            claimant_id="late-host",
            seen_at="2026-07-17T14:00:04Z",
            lease_seconds=30,
        )
        self.assertTrue(first["should_emit"])
        self.assertTrue(retry["should_emit"])
        self.assertEqual(retry["disposition"], "retry_claimed")
        self.assertNotEqual(first["claim_token"], retry["claim_token"])
        self.assertFalse(duplicate["should_emit"])

    def test_periodic_digest_is_the_only_unlinked_full_snapshot_replay(self) -> None:
        first = self.event(
            facts={"digest_day": "2026-07-17", "open_items": 3},
            event_class="daily.summary",
            notification_kind="periodic_digest",
        )
        second = self.event(
            facts={"digest_day": "2026-07-18", "open_items": 2},
            event_class="daily.summary",
            notification_kind="periodic_digest",
            created_at="2026-07-18T14:00:00Z",
        )
        self.claim(first)
        result = self.ledger.claim(
            second,
            claimant_id="digest-host",
            seen_at="2026-07-18T14:00:01Z",
        )
        self.assertTrue(result["should_emit"])
        self.assertIsNone(second["supersedes_event_id"])

    def test_payload_body_is_not_retained_in_receive_ledger(self) -> None:
        secret_text = "operator-visible-body-not-for-ledger"
        event = self.event(facts={"status": "ready", "body": secret_text})
        self.claim(event)
        raw_database = self.ledger_path.read_bytes()
        self.assertNotIn(secret_text.encode("utf-8"), raw_database)
        record = self.ledger.record(event["event_id"])
        self.assertNotIn("payload", record)


if __name__ == "__main__":
    unittest.main()
