from __future__ import annotations

import hashlib
import io
import json
import sqlite3
import tempfile
import threading
import unittest
from concurrent.futures import ThreadPoolExecutor
from contextlib import closing, redirect_stderr, redirect_stdout
from datetime import datetime
from pathlib import Path

from jsonschema import Draft202012Validator, FormatChecker

from ops.atlas.operator_notification_idempotency import (
    ACK_CONTRACT_VERSION,
    EVENT_CONTRACT_VERSION,
    ClaimTokenError,
    DeliveryStateError,
    LedgerCorruptionError,
    LedgerProvisioningError,
    LedgerUnavailableError,
    NotificationContractError,
    NotificationLedger,
    UnknownLedgerSchemaError,
    build_event,
    main as notification_main,
    validate_event,
)


ROOT = Path(__file__).resolve().parents[1]
EVENT_SCHEMA = ROOT / "schemas" / "atlas.operator-notification.event.v1.json"
ACK_SCHEMA = ROOT / "schemas" / "atlas.operator-notification.ack.v1.json"
THREAD_ID = "019f52d9-7667-72a3-a5f7-9c0613aedd8f"
CREATED = "2026-07-17T14:00:00Z"
SEEN = "2026-07-17T14:00:01Z"
ACKED = "2026-07-17T14:00:02Z"
STARTED = "2026-07-17T14:00:01.500000Z"


class OperatorNotificationIdempotencyTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.runtime_root = Path(self.temporary.name) / "runtime"
        self.ledger_path = self.runtime_root / "atlas" / "notifications" / "receive.sqlite3"
        self.clock_now = datetime.fromisoformat(
            STARTED[:-1] + "+00:00"
        )
        self.token_counter = 0
        self.token_lock = threading.Lock()
        self.ledger = NotificationLedger.provision(
            self.runtime_root,
            self.ledger_path,
            _clock=lambda: self.clock_now,
            _token_bytes=self.fixture_token_bytes,
        )

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def fixture_token_bytes(self, size: int) -> bytes:
        if size != 32:
            raise AssertionError(f"unexpected token size: {size}")
        with self.token_lock:
            self.token_counter += 1
            return self.token_counter.to_bytes(size, "big")

    @staticmethod
    def expected_fixture_token(index: int) -> str:
        return "oncl1_" + index.to_bytes(32, "big").hex()

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
        seen_at = kwargs.pop("seen_at", SEEN)
        clock_at = kwargs.pop("clock_at", seen_at)
        self.clock_now = datetime.fromisoformat(clock_at[:-1] + "+00:00")
        return self.ledger.claim(
            event,
            claimant_id=kwargs.pop("claimant_id", "host-a"),
            seen_at=seen_at,
            **kwargs,
        )

    @staticmethod
    def run_cli(*argv: str) -> tuple[int, str, str]:
        stdout = io.StringIO()
        stderr = io.StringIO()
        with redirect_stdout(stdout), redirect_stderr(stderr):
            exit_code = notification_main(list(argv))
        return exit_code, stdout.getvalue(), stderr.getvalue()

    def begin(self, event: dict, claim: dict, *, clock_at: str = STARTED) -> dict:
        self.clock_now = datetime.fromisoformat(clock_at[:-1] + "+00:00")
        return self.ledger.begin_delivery(
            event["event_id"],
            claim_token=claim["claim_token"],
            claim_generation=claim["claim_generation"],
        )

    def acknowledge(
        self, event: dict, claim: dict, *, acknowledged_at: str = ACKED
    ) -> dict:
        return self.ledger.acknowledge(
            event["event_id"],
            claim_token=claim["claim_token"],
            claim_generation=claim["claim_generation"],
            acknowledged_at=acknowledged_at,
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
        self.begin(event, claim)
        ack = self.acknowledge(event, claim)
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
        self.assertTrue(first["should_begin_delivery"])
        self.assertFalse(first["should_emit"])
        self.assertFalse(first["operator_message_authorized"])
        self.assertFalse(duplicate["should_emit"])
        self.assertEqual(duplicate["disposition"], "duplicate_exact")
        self.assertEqual(self.ledger.record(event["event_id"])["duplicate_count"], 1)

    def test_pre_send_fence_is_the_only_operator_delivery_authorization(self) -> None:
        event = self.event()
        claim = self.claim(event)
        self.assertTrue(claim["should_begin_delivery"])
        self.assertFalse(claim["should_emit"])
        self.assertFalse(claim["operator_message_authorized"])

        delivery = self.begin(event, claim)
        self.assertTrue(delivery["should_emit"])
        self.assertTrue(delivery["operator_message_authorized"])
        self.assertTrue(delivery["transport_event_id_dedupe_required"])
        self.assertEqual(delivery["transport_idempotency_key"], event["event_id"])
        self.assertEqual(delivery["delivery_outcome"], "UNKNOWN")
        self.assertTrue(delivery["reconciliation_required"])
        with self.assertRaisesRegex(DeliveryStateError, "requires reconciliation"):
            self.begin(event, claim)

    def test_expired_claimant_is_fenced_after_replacement_claim(self) -> None:
        event = self.event()
        original = self.claim(event, lease_seconds=1)
        self.clock_now = datetime.fromisoformat(
            "2026-07-17T14:00:02.000001+00:00"
        )
        replacement = self.ledger.claim(
            event,
            claimant_id="replacement-host",
            seen_at="2026-07-17T14:00:02.000001Z",
            lease_seconds=30,
        )
        self.assertTrue(replacement["should_begin_delivery"])
        self.assertGreater(
            replacement["claim_generation"], original["claim_generation"]
        )
        with self.assertRaisesRegex(ClaimTokenError, "active claim fence"):
            self.clock_now = datetime.fromisoformat(
                "2026-07-17T14:00:02.100000+00:00"
            )
            self.ledger.begin_delivery(
                event["event_id"],
                claim_token=original["claim_token"],
                claim_generation=original["claim_generation"],
            )
        delivery = self.ledger.begin_delivery(
            event["event_id"],
            claim_token=replacement["claim_token"],
            claim_generation=replacement["claim_generation"],
        )
        self.assertTrue(delivery["operator_message_authorized"])

    def test_transport_crash_state_is_durable_unknown_and_non_retryable(self) -> None:
        event = self.event()
        claim = self.claim(event)
        self.begin(event, claim)
        restarted = NotificationLedger(self.runtime_root, self.ledger_path)
        duplicate = restarted.claim(
            event,
            claimant_id="restart-host",
            seen_at="2026-07-18T14:00:00Z",
        )
        self.assertFalse(duplicate["should_begin_delivery"])
        self.assertFalse(duplicate["should_emit"])
        self.assertEqual(duplicate["disposition"], "duplicate_delivery_unknown")
        self.assertEqual(duplicate["delivery_outcome"], "UNKNOWN")
        self.assertTrue(duplicate["reconciliation_required"])
        self.assertFalse(
            restarted.should_retry(event["event_id"], at="2026-07-18T14:00:00Z")
        )
        record = restarted.record(event["event_id"])
        self.assertEqual(record["delivery_state"], "delivery_in_progress")
        self.assertEqual(record["delivery_outcome"], "UNKNOWN")
        self.assertTrue(record["reconciliation_required"])

    def test_active_ack_requires_matching_generation_and_pre_send_fence(self) -> None:
        event = self.event()
        original = self.claim(event, lease_seconds=1)
        with self.assertRaisesRegex(DeliveryStateError, "fenced delivery"):
            self.acknowledge(event, original)
        self.clock_now = datetime.fromisoformat(
            "2026-07-17T14:00:02.000001+00:00"
        )
        replacement = self.ledger.claim(
            event,
            claimant_id="replacement-host",
            seen_at="2026-07-17T14:00:02.000001Z",
            lease_seconds=30,
        )
        self.clock_now = datetime.fromisoformat(
            "2026-07-17T14:00:02.100000+00:00"
        )
        self.ledger.begin_delivery(
            event["event_id"],
            claim_token=replacement["claim_token"],
            claim_generation=replacement["claim_generation"],
        )
        with self.assertRaisesRegex(ClaimTokenError, "active claim fence"):
            self.acknowledge(
                event, original, acknowledged_at="2026-07-17T14:00:03Z"
            )
        ack = self.acknowledge(
            event, replacement, acknowledged_at="2026-07-17T14:00:03Z"
        )
        self.assertEqual(ack["claim_generation"], replacement["claim_generation"])

    def test_lease_expiry_preserves_microsecond_floor(self) -> None:
        event = self.event()
        first = self.claim(
            event,
            seen_at="2026-07-17T14:00:00.999999Z",
            lease_seconds=1,
        )
        self.assertEqual(
            first["claim_expires_at"], "2026-07-17T14:00:01.999999Z"
        )
        self.clock_now = datetime.fromisoformat(
            "2026-07-17T14:00:01+00:00"
        )
        early = self.ledger.claim(
            event,
            claimant_id="early-host",
            seen_at="2026-07-17T14:00:01Z",
            lease_seconds=1,
        )
        self.assertFalse(early["should_begin_delivery"])
        self.clock_now = datetime.fromisoformat(
            "2026-07-17T14:00:01.999999+00:00"
        )
        retry = self.ledger.claim(
            event,
            claimant_id="on-boundary-host",
            seen_at="2026-07-17T14:00:01.999999Z",
            lease_seconds=1,
        )
        self.assertTrue(retry["should_begin_delivery"])
        self.assertEqual(retry["disposition"], "retry_claimed")

    def test_timestamps_require_canonical_rfc3339_utc_grammar(self) -> None:
        invalid = (
            "2026-07-17 14:00:00Z",
            "2026-07-17T14:00:00+00:00",
            "2026-07-17T14:00:00",
            "2026-07-17t14:00:00z",
            "2026-07-17T14:00:00.Z",
            "2026-07-17T14:00:00.1234567Z",
        )
        for value in invalid:
            with self.subTest(value=value):
                with self.assertRaisesRegex(
                    NotificationContractError, "canonical RFC 3339"
                ):
                    self.event(created_at=value)
        valid = self.event(created_at="2026-07-17T14:00:00.123456Z")
        self.assertEqual(validate_event(valid), valid)
        schema = json.loads(EVENT_SCHEMA.read_text(encoding="utf-8"))
        Draft202012Validator(schema, format_checker=FormatChecker()).validate(valid)
        invalid_schema_event = dict(valid)
        invalid_schema_event["created_at"] = "2026-07-17 14:00:00Z"
        self.assertTrue(
            list(
                Draft202012Validator(
                    schema, format_checker=FormatChecker()
                ).iter_errors(invalid_schema_event)
            )
        )

        with self.assertRaisesRegex(
            NotificationContractError, "canonical RFC 3339"
        ):
            self.ledger.claim(
                valid,
                claimant_id="host-a",
                seen_at="2026-07-17T14:00:01+00:00",
            )
        claim = self.claim(valid)
        self.begin(valid, claim)
        with self.assertRaisesRegex(
            NotificationContractError, "canonical RFC 3339"
        ):
            self.acknowledge(
                valid, claim, acknowledged_at="2026-07-17T14:00:02+00:00"
            )
        with self.assertRaisesRegex(DeliveryStateError, "predates"):
            self.acknowledge(
                valid, claim, acknowledged_at="2026-07-17T14:00:01.499999Z"
            )
        self.acknowledge(valid, claim)

    def test_json_pointer_delta_escape_grammar_and_root_policy(self) -> None:
        predecessor = "onv1_" + "a" * 64
        for path in ("", "/status~", "/status~2value", "/~a"):
            with self.subTest(path=path):
                with self.assertRaisesRegex(NotificationContractError, "JSON Pointer"):
                    self.event(
                        supersedes_event_id=predecessor,
                        delta={"changed_fact_paths": [path]},
                    )
        valid_paths = ["/", "//", "/path~1segment", "/status~0value"]
        event = self.event(
            supersedes_event_id=predecessor,
            delta={"changed_fact_paths": valid_paths},
        )
        self.assertEqual(event["delta"]["changed_fact_paths"], valid_paths)
        schema = json.loads(EVENT_SCHEMA.read_text(encoding="utf-8"))
        Draft202012Validator.check_schema(schema)
        Draft202012Validator(schema, format_checker=FormatChecker()).validate(event)
        invalid_schema_event = json.loads(json.dumps(event))
        invalid_schema_event["delta"]["changed_fact_paths"] = ["/status~2value"]
        self.assertTrue(
            list(
                Draft202012Validator(
                    schema, format_checker=FormatChecker()
                ).iter_errors(invalid_schema_event)
            )
        )

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

    def test_notification_kind_has_distinct_deterministic_identity(self) -> None:
        heartbeat = self.event(notification_kind="heartbeat")
        operator_update = self.event(notification_kind="operator_update")
        retry = self.event(
            notification_kind="operator_update",
            transport={"host_id": "host-b", "attempt": 9},
            created_at="2026-07-17T14:05:00Z",
        )
        self.assertEqual(
            heartbeat["canonical_payload_digest"],
            operator_update["canonical_payload_digest"],
        )
        self.assertNotEqual(heartbeat["event_id"], operator_update["event_id"])
        self.assertEqual(operator_update["event_id"], retry["event_id"])
        suppressed = self.claim(heartbeat)
        admitted = self.ledger.claim(
            operator_update,
            claimant_id="host-b",
            seen_at="2026-07-17T14:00:02Z",
        )
        self.assertEqual(suppressed["disposition"], "suppressed_control")
        self.assertTrue(admitted["should_begin_delivery"])

    def test_control_events_cannot_supersede_deliverable_events(self) -> None:
        deliverable = self.event(event_class="task.control-target")
        claim = self.claim(deliverable)
        for kind, event_class in (
            ("heartbeat", "task.control-target"),
            ("continuation", "task.unrelated-stream"),
        ):
            with self.subTest(kind=kind, event_class=event_class):
                with self.assertRaisesRegex(
                    NotificationContractError, "cannot supersede"
                ):
                    self.event(
                        facts={"status": "control", "card_id": "ATLAS-1"},
                        event_class=event_class,
                        notification_kind=kind,
                        supersedes_event_id=deliverable["event_id"],
                        delta={"changed_fact_paths": ["/status"]},
                    )
        with self.assertRaisesRegex(NotificationContractError, "cannot supersede"):
            self.event(
                event_class="task.control-target",
                notification_kind="heartbeat",
                supersedes_event_id=deliverable["event_id"],
            )
        self.assertIsNone(
            self.ledger.record(deliverable["event_id"])["supersession"][
                "superseded_by_event_id"
            ]
        )
        self.assertTrue(self.begin(deliverable, claim)["operator_message_authorized"])

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
        self.assertTrue(result["should_begin_delivery"])

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

    def test_causal_occurrence_identity_supports_ready_blocked_ready(self) -> None:
        ready = self.event(event_class="task.causal-cycle")
        self.claim(ready)
        blocked = self.event(
            facts={"status": "blocked", "card_id": "ATLAS-1"},
            event_class="task.causal-cycle",
            supersedes_event_id=ready["event_id"],
            delta={"changed_fact_paths": ["/status"]},
        )
        self.ledger.claim(
            blocked,
            claimant_id="host-b",
            seen_at="2026-07-17T14:00:02Z",
        )
        ready_again = self.event(
            event_class="task.causal-cycle",
            supersedes_event_id=blocked["event_id"],
            delta={"changed_fact_paths": ["/status"]},
        )
        admitted = self.ledger.claim(
            ready_again,
            claimant_id="host-c",
            seen_at="2026-07-17T14:00:03Z",
        )

        self.assertEqual(
            ready_again["canonical_payload_digest"], ready["canonical_payload_digest"]
        )
        self.assertEqual(blocked["supersedes_event_id"], ready["event_id"])
        self.assertEqual(ready_again["supersedes_event_id"], blocked["event_id"])
        self.assertEqual(
            len({ready["event_id"], blocked["event_id"], ready_again["event_id"]}),
            3,
        )
        self.assertTrue(admitted["should_begin_delivery"])
        self.assertFalse(admitted["operator_message_authorized"])

    def test_causal_identity_retry_is_stable_across_hosts_and_restart(self) -> None:
        ready = self.event(event_class="task.causal-retry")
        self.claim(ready)
        changed = self.event(
            facts={"status": "blocked", "card_id": "ATLAS-1"},
            event_class="task.causal-retry",
            transport={"host_id": "windows-a", "attempt": 1},
            supersedes_event_id=ready["event_id"],
            delta={"changed_fact_paths": ["/status"]},
        )
        retry = self.event(
            facts={"status": "blocked", "card_id": "ATLAS-1"},
            event_class="task.causal-retry",
            transport={"host_id": "linux-b", "attempt": 8},
            created_at="2026-07-18T01:02:03Z",
            supersedes_event_id=ready["event_id"],
            delta={"changed_fact_paths": ["/status"]},
        )
        self.assertEqual(changed["event_id"], retry["event_id"])
        self.ledger.claim(
            changed,
            claimant_id="windows-a",
            seen_at="2026-07-17T14:00:02Z",
        )
        restarted = NotificationLedger(
            self.runtime_root,
            self.ledger_path,
            _clock=lambda: self.clock_now,
            _token_bytes=self.fixture_token_bytes,
        )
        duplicate = restarted.claim(
            retry,
            claimant_id="linux-b",
            seen_at="2026-07-17T14:00:03Z",
        )
        self.assertFalse(duplicate["operator_message_authorized"])
        self.assertEqual(duplicate["event_id"], changed["event_id"])

    def test_causal_lineage_rejects_unrelated_stream_and_accepts_legacy_event(self) -> None:
        first = self.event(event_class="task.legacy-causal")
        self.claim(first)
        current = self.event(
            facts={"status": "complete", "card_id": "ATLAS-1"},
            event_class="task.legacy-causal",
            supersedes_event_id=first["event_id"],
            delta={"changed_fact_paths": ["/status"]},
        )
        legacy = dict(current)
        legacy["event_id"] = "onv1_" + hashlib.sha256(
            "\x1f".join(
                [
                    current["source_thread_id"],
                    current["event_class"],
                    current["notification_kind"],
                    current["canonical_payload_digest"],
                ]
            ).encode("utf-8")
        ).hexdigest()
        self.assertEqual(validate_event(legacy), legacy)
        self.ledger.claim(
            legacy,
            claimant_id="legacy-host",
            seen_at="2026-07-17T14:00:02Z",
        )
        restarted = NotificationLedger(self.runtime_root, self.ledger_path)
        duplicate = restarted.claim(
            legacy,
            claimant_id="restart-host",
            seen_at="2026-07-17T14:00:03Z",
        )
        self.assertFalse(duplicate["operator_message_authorized"])

        unrelated = self.event(event_class="task.unrelated-causal")
        self.ledger.claim(
            unrelated,
            claimant_id="unrelated-host",
            seen_at="2026-07-17T14:00:04Z",
        )
        with self.assertRaisesRegex(NotificationContractError, "supersede"):
            self.ledger.claim(
                self.event(
                    facts={"status": "complete", "card_id": "ATLAS-1"},
                    event_class="task.unrelated-causal",
                    supersedes_event_id=legacy["event_id"],
                    delta={"changed_fact_paths": ["/status"]},
                ),
                claimant_id="unrelated-host",
                seen_at="2026-07-17T14:00:05Z",
            )
        self.assertNotEqual(unrelated["event_id"], legacy["event_id"])

    def test_acknowledgement_stops_retry_and_replays_stable_control_ack(self) -> None:
        event = self.event()
        claim = self.claim(event)
        self.begin(event, claim)
        ack = self.acknowledge(event, claim)
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
        self.begin(event, claim)
        first = self.acknowledge(event, claim)
        second = self.acknowledge(
            event, claim, acknowledged_at="2026-07-17T14:10:00Z"
        )
        self.assertEqual(first["ack_id"], second["ack_id"])
        self.assertEqual(first["acknowledged_at"], second["acknowledged_at"])
        self.assertEqual(second["ack_disposition"], "replayed")
        self.assertFalse(second["operator_message_authorized"])

    def test_heartbeat_and_continuation_never_replay_operator_message(self) -> None:
        event = self.event()
        claim = self.claim(event)
        self.begin(event, claim)
        self.acknowledge(event, claim)
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
        self.begin(event, claim)
        expected_ack = self.acknowledge(event, claim)
        restarted = NotificationLedger(self.runtime_root, self.ledger_path)
        result = restarted.claim(
            event,
            claimant_id="host-after-restart",
            seen_at="2026-07-18T00:00:00Z",
        )
        self.assertFalse(result["should_emit"])
        self.assertEqual(result["ack"]["ack_id"], expected_ack["ack_id"])

    def test_missing_startup_ledger_requires_explicit_provisioning(self) -> None:
        missing_path = (
            self.runtime_root / "unprovisioned" / "notifications.sqlite3"
        )
        with self.assertRaisesRegex(LedgerUnavailableError, "provision explicitly"):
            NotificationLedger(self.runtime_root, missing_path)
        self.assertFalse(missing_path.exists())
        self.assertFalse(missing_path.parent.exists())

        provisioned = NotificationLedger.provision(self.runtime_root, missing_path)
        self.assertTrue(missing_path.is_file())
        self.assertIsNone(provisioned.record(self.event()["event_id"]))
        restarted = NotificationLedger(self.runtime_root, missing_path)
        self.assertIsNone(restarted.record(self.event()["event_id"]))
        with self.assertRaisesRegex(LedgerProvisioningError, "already exists"):
            NotificationLedger.provision(self.runtime_root, missing_path)

    def test_lock_contention_is_temporarily_unavailable_not_corruption(self) -> None:
        short_wait_ledger = NotificationLedger(
            self.runtime_root,
            self.ledger_path,
            _clock=lambda: self.clock_now,
            _token_bytes=self.fixture_token_bytes,
            _busy_timeout_ms=20,
        )
        with closing(
            sqlite3.connect(self.ledger_path, timeout=0, isolation_level=None)
        ) as blocker:
            blocker.execute("PRAGMA busy_timeout=0")
            blocker.execute("BEGIN IMMEDIATE")
            with self.assertRaisesRegex(
                LedgerUnavailableError, "temporarily unavailable.*lock contention"
            ):
                NotificationLedger(
                    self.runtime_root,
                    self.ledger_path,
                    _token_bytes=self.fixture_token_bytes,
                    _busy_timeout_ms=20,
                )
            with self.assertRaisesRegex(
                LedgerUnavailableError, "temporarily unavailable.*lock contention"
            ):
                short_wait_ledger.claim(
                    self.event(event_class="task.lock-contention"),
                    claimant_id="blocked-host",
                    seen_at=SEEN,
                )
            blocker.execute("ROLLBACK")

        restarted = NotificationLedger(
            self.runtime_root,
            self.ledger_path,
            _token_bytes=self.fixture_token_bytes,
            _busy_timeout_ms=20,
        )
        admitted = restarted.claim(
            self.event(event_class="task.lock-contention"),
            claimant_id="recovered-host",
            seen_at=SEEN,
        )
        self.assertTrue(admitted["should_begin_delivery"])

    def test_corrupt_and_unknown_ledger_schema_fail_closed(self) -> None:
        corrupt_path = self.runtime_root / "atlas" / "notifications" / "corrupt.sqlite3"
        corrupt_path.write_bytes(b"not-a-sqlite-database")
        with self.assertRaises(LedgerCorruptionError):
            NotificationLedger(self.runtime_root, corrupt_path)

        unknown_path = self.runtime_root / "atlas" / "notifications" / "unknown.sqlite3"
        NotificationLedger.provision(self.runtime_root, unknown_path)
        with closing(sqlite3.connect(unknown_path)) as connection:
            connection.execute(
                "UPDATE ledger_meta SET value='atlas.operator-notification.ledger.v999' "
                "WHERE key='schema_version'"
            )
            connection.commit()
        with self.assertRaises(UnknownLedgerSchemaError):
            NotificationLedger(self.runtime_root, unknown_path)

        incompatible_path = (
            self.runtime_root / "atlas" / "notifications" / "incompatible.sqlite3"
        )
        NotificationLedger.provision(self.runtime_root, incompatible_path)
        with closing(sqlite3.connect(incompatible_path)) as connection:
            connection.execute(
                "ALTER TABLE notification_events ADD COLUMN unexpected TEXT"
            )
            connection.commit()
        with self.assertRaises(UnknownLedgerSchemaError):
            NotificationLedger(self.runtime_root, incompatible_path)

        legacy_path = self.runtime_root / "atlas" / "notifications" / "legacy.sqlite3"
        NotificationLedger.provision(self.runtime_root, legacy_path)
        with closing(sqlite3.connect(legacy_path)) as connection:
            connection.execute(
                "UPDATE ledger_meta SET value='atlas.operator-notification.ledger.v1' "
                "WHERE key='schema_version'"
            )
            connection.execute(
                "ALTER TABLE notification_events DROP COLUMN claim_acquired_at"
            )
            connection.commit()
        with self.assertRaises(UnknownLedgerSchemaError):
            NotificationLedger(self.runtime_root, legacy_path)

    def test_concurrent_duplicate_claim_allows_exactly_one_delivery_candidate(self) -> None:
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
        self.assertEqual(
            sum(result["should_begin_delivery"] for result in results), 1
        )
        self.assertEqual(self.ledger.record(event["event_id"])["duplicate_count"], 11)

    def test_concurrent_startup_and_claim_allows_one_delivery_candidate(self) -> None:
        event = self.event(event_class="task.concurrent-startup")
        ledger_path = (
            self.runtime_root / "atlas" / "notifications" / "startup.sqlite3"
        )
        NotificationLedger.provision(self.runtime_root, ledger_path)
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
        self.assertEqual(
            sum(result["should_begin_delivery"] for result in results), 1
        )
        self.assertEqual(ledger.record(event["event_id"])["duplicate_count"], 11)

    def test_concurrent_pre_send_fence_allows_exactly_one_authorization(self) -> None:
        event = self.event(event_class="task.concurrent-delivery")
        claim = self.claim(event)
        barrier = threading.Barrier(12)

        def attempt(_: int) -> bool:
            barrier.wait()
            try:
                result = self.begin(event, claim)
            except DeliveryStateError:
                return False
            return bool(result["operator_message_authorized"])

        with ThreadPoolExecutor(max_workers=12) as executor:
            results = list(executor.map(attempt, range(12)))
        self.assertEqual(sum(results), 1)
        record = self.ledger.record(event["event_id"])
        self.assertEqual(record["delivery_state"], "delivery_in_progress")
        self.assertEqual(record["delivery_outcome"], "UNKNOWN")

    def test_expired_claim_can_be_retried_exactly_once(self) -> None:
        event = self.event()
        first = self.claim(event, lease_seconds=1)
        self.clock_now = datetime.fromisoformat(
            "2026-07-17T14:00:03+00:00"
        )
        retry = self.ledger.claim(
            event,
            claimant_id="recovery-host",
            seen_at="2026-07-17T14:00:03Z",
            lease_seconds=30,
        )
        self.clock_now = datetime.fromisoformat(
            "2026-07-17T14:00:04+00:00"
        )
        duplicate = self.ledger.claim(
            event,
            claimant_id="late-host",
            seen_at="2026-07-17T14:00:04Z",
            lease_seconds=30,
        )
        self.assertTrue(first["should_begin_delivery"])
        self.assertTrue(retry["should_begin_delivery"])
        self.assertEqual(retry["disposition"], "retry_claimed")
        self.assertNotEqual(first["claim_token"], retry["claim_token"])
        self.assertFalse(duplicate["should_emit"])

    def test_claim_tokens_are_independent_persisted_capabilities(self) -> None:
        event = self.event(event_class="task.random-capability")
        initial = self.claim(event, lease_seconds=1)
        self.assertEqual(initial["claim_token"], self.expected_fixture_token(1))

        self.clock_now = datetime.fromisoformat(
            "2026-07-17T14:00:02.000001+00:00"
        )
        replacement = self.ledger.claim(
            event,
            claimant_id="replacement-host",
            seen_at="2026-07-17T14:00:02.000001Z",
            lease_seconds=30,
        )
        self.assertEqual(replacement["claim_token"], self.expected_fixture_token(2))
        self.assertNotEqual(initial["claim_token"], replacement["claim_token"])

        with self.assertRaisesRegex(ClaimTokenError, "active claim fence"):
            self.ledger.begin_delivery(
                event["event_id"],
                claim_token=initial["claim_token"],
                claim_generation=replacement["claim_generation"],
            )
        with self.assertRaisesRegex(ClaimTokenError, "active claim fence"):
            self.ledger.begin_delivery(
                event["event_id"],
                claim_token=initial["claim_token"],
                claim_generation=initial["claim_generation"],
            )

        restarted = NotificationLedger(
            self.runtime_root,
            self.ledger_path,
            _clock=lambda: self.clock_now,
            _token_bytes=self.fixture_token_bytes,
        )
        delivery = restarted.begin_delivery(
            event["event_id"],
            claim_token=replacement["claim_token"],
            claim_generation=replacement["claim_generation"],
        )
        self.assertTrue(delivery["operator_message_authorized"])

        independent = restarted.claim(
            self.event(event_class="task.independent-capability"),
            claimant_id="independent-host",
            seen_at="2026-07-17T14:00:03Z",
        )
        self.assertEqual(independent["claim_token"], self.expected_fixture_token(3))
        self.assertNotIn(
            independent["claim_token"],
            {initial["claim_token"], replacement["claim_token"]},
        )

    def test_existing_ledger_v2_claim_token_remains_valid_across_restart(self) -> None:
        event = self.event(event_class="task.ledger-v2-token-compatibility")
        claim = self.claim(event)
        legacy_token = "oncl1_" + hashlib.sha256(
            f"{event['event_id']}\x1f{claim['claim_generation']}".encode("utf-8")
        ).hexdigest()
        with closing(sqlite3.connect(self.ledger_path)) as connection:
            connection.execute(
                "UPDATE notification_events SET claim_token=? WHERE event_id=?",
                (legacy_token, event["event_id"]),
            )
            connection.commit()

        restarted = NotificationLedger(
            self.runtime_root,
            self.ledger_path,
            _clock=lambda: self.clock_now,
            _token_bytes=self.fixture_token_bytes,
        )
        delivery = restarted.begin_delivery(
            event["event_id"],
            claim_token=legacy_token,
            claim_generation=claim["claim_generation"],
        )
        self.assertTrue(delivery["operator_message_authorized"])

    def test_claim_token_source_failures_roll_back_without_replacing_capability(self) -> None:
        invalid_path = (
            self.runtime_root / "atlas" / "notifications" / "invalid-token.sqlite3"
        )
        invalid = NotificationLedger.provision(
            self.runtime_root,
            invalid_path,
            _token_bytes=lambda size: b"too-short",
        )
        invalid_event = self.event(event_class="task.invalid-token-source")
        with self.assertRaisesRegex(LedgerUnavailableError, "exactly 32 bytes"):
            invalid.claim(invalid_event, claimant_id="host-a", seen_at=SEEN)
        self.assertIsNone(invalid.record(invalid_event["event_id"]))

        repeated_path = (
            self.runtime_root / "atlas" / "notifications" / "repeated-token.sqlite3"
        )
        repeated = NotificationLedger.provision(
            self.runtime_root,
            repeated_path,
            _clock=lambda: self.clock_now,
            _token_bytes=lambda size: b"r" * size,
        )
        repeated_event = self.event(event_class="task.repeated-token-source")
        self.clock_now = datetime.fromisoformat("2026-07-17T14:00:01+00:00")
        original = repeated.claim(
            repeated_event,
            claimant_id="host-a",
            seen_at=SEEN,
            lease_seconds=1,
        )
        self.clock_now = datetime.fromisoformat("2026-07-17T14:00:02+00:00")
        with self.assertRaisesRegex(LedgerUnavailableError, "repeated"):
            repeated.claim(
                repeated_event,
                claimant_id="replacement-host",
                seen_at="2026-07-17T14:00:02Z",
                lease_seconds=30,
            )
        record = repeated.record(repeated_event["event_id"])
        self.assertEqual(record["claim_generation"], original["claim_generation"])
        self.assertEqual(record["delivery_state"], "claimed")

    def test_delivery_start_is_fenced_by_current_claim_acquisition(self) -> None:
        event = self.event(event_class="task.claim-acquisition")
        self.claim(event, lease_seconds=1)
        self.clock_now = datetime.fromisoformat(
            "2026-07-17T14:00:03.123456+00:00"
        )
        replacement = self.ledger.claim(
            event,
            claimant_id="replacement-host",
            seen_at="2026-07-17T14:00:03.123456Z",
            lease_seconds=30,
        )
        self.assertEqual(
            replacement["claim_acquired_at"], "2026-07-17T14:00:03.123456Z"
        )
        self.clock_now = datetime.fromisoformat(
            "2026-07-17T14:00:03.123455+00:00"
        )
        with self.assertRaisesRegex(DeliveryStateError, "active claim lease"):
            self.ledger.begin_delivery(
                event["event_id"],
                claim_token=replacement["claim_token"],
                claim_generation=replacement["claim_generation"],
            )
        self.clock_now = datetime.fromisoformat(
            "2026-07-17T14:00:03.123456+00:00"
        )
        restarted = NotificationLedger(
            self.runtime_root,
            self.ledger_path,
            _clock=lambda: self.clock_now,
        )
        record = restarted.record(event["event_id"])
        self.assertEqual(
            record["claim_acquired_at"], "2026-07-17T14:00:03.123456Z"
        )
        delivery = restarted.begin_delivery(
            event["event_id"],
            claim_token=replacement["claim_token"],
            claim_generation=replacement["claim_generation"],
        )
        self.assertTrue(delivery["operator_message_authorized"])
        self.assertEqual(
            delivery["delivery_started_at"], "2026-07-17T14:00:03.123456Z"
        )

    def test_claim_lease_uses_ledger_clock_not_skewed_seen_at(self) -> None:
        event = self.event(event_class="task.claim-clock")
        self.clock_now = datetime.fromisoformat(
            "2026-07-17T14:00:10.123456+00:00"
        )
        initial = self.ledger.claim(
            event,
            claimant_id="future-skewed-host",
            seen_at="2099-07-17T14:00:00Z",
            lease_seconds=30,
        )
        self.assertEqual(initial["claim_acquired_at"], "2026-07-17T14:00:10.123456Z")
        self.assertEqual(initial["claim_expires_at"], "2026-07-17T14:00:40.123456Z")
        record = self.ledger.record(event["event_id"])
        self.assertEqual(record["first_seen"], "2099-07-17T14:00:00Z")

        self.clock_now = datetime.fromisoformat(
            "2026-07-17T14:00:11.123456+00:00"
        )
        restarted = NotificationLedger(
            self.runtime_root,
            self.ledger_path,
            _clock=lambda: self.clock_now,
        )
        active = restarted.claim(
            event,
            claimant_id="second-future-skewed-host",
            seen_at="2199-07-17T14:00:00Z",
            lease_seconds=30,
        )
        self.assertFalse(active["should_begin_delivery"])
        self.assertEqual(
            restarted.record(event["event_id"])["claim_generation"],
            initial["claim_generation"],
        )

        self.clock_now = datetime.fromisoformat(
            "2026-07-17T14:00:40.123456+00:00"
        )
        replacement = restarted.claim(
            event,
            claimant_id="past-skewed-host",
            seen_at="2020-07-17T14:00:00Z",
            lease_seconds=10,
        )
        self.assertTrue(replacement["should_begin_delivery"])
        self.assertEqual(
            replacement["claim_generation"], initial["claim_generation"] + 1
        )
        self.assertEqual(
            replacement["claim_acquired_at"], "2026-07-17T14:00:40.123456Z"
        )
        self.assertEqual(
            replacement["claim_expires_at"], "2026-07-17T14:00:50.123456Z"
        )
        restarted_record = restarted.record(event["event_id"])
        self.assertEqual(restarted_record["last_seen"], "2020-07-17T14:00:00Z")
        self.assertEqual(
            restarted_record["ledger_schema_version"],
            "atlas.operator-notification.ledger.v2",
        )

    def test_expired_claimant_cannot_backdate_delivery_start(self) -> None:
        event = self.event(event_class="task.expired-delivery")
        claim = self.claim(event, lease_seconds=1)
        self.clock_now = datetime.fromisoformat(
            "2026-07-17T14:00:02.000001+00:00"
        )
        with self.assertRaisesRegex(DeliveryStateError, "active claim lease"):
            self.ledger.begin_delivery(
                event["event_id"],
                claim_token=claim["claim_token"],
                claim_generation=claim["claim_generation"],
            )
        self.assertEqual(
            self.ledger.record(event["event_id"])["delivery_state"], "claimed"
        )

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
        self.assertTrue(result["should_begin_delivery"])
        self.assertIsNone(second["supersedes_event_id"])

    def test_payload_body_is_not_retained_in_receive_ledger(self) -> None:
        secret_text = "operator-visible-body-not-for-ledger"
        event = self.event(facts={"status": "ready", "body": secret_text})
        self.claim(event)
        raw_database = self.ledger_path.read_bytes()
        self.assertNotIn(secret_text.encode("utf-8"), raw_database)
        record = self.ledger.record(event["event_id"])
        self.assertNotIn("payload", record)

    def test_cli_input_failures_are_sanitized_contract_rejections(self) -> None:
        input_root = self.runtime_root.parent / "operator-inputs"
        input_root.mkdir()
        unreadable = input_root / "unreadable-marker"
        unreadable.mkdir()
        missing = input_root / "missing-private-marker.json"
        malformed = input_root / "malformed.json"
        malformed.write_text('{"private_payload_marker":', encoding="utf-8")
        non_object = input_root / "non-object.json"
        non_object.write_text('["private-list-marker"]', encoding="utf-8")
        missing_fields = input_root / "missing-fields.json"
        missing_fields.write_text("{}", encoding="utf-8")
        extra_field = input_root / "extra-field.json"
        extra_field.write_text(
            json.dumps(
                {
                    "source_thread_id": THREAD_ID,
                    "event_class": "task.cli",
                    "payload": {"facts": {"status": "ready"}},
                    "created_at": CREATED,
                    "raw_private_argument": "must-not-leak",
                }
            ),
            encoding="utf-8",
        )
        invalid_type = input_root / "invalid-type.json"
        invalid_type.write_text(
            json.dumps(
                {
                    "source_thread_id": ["private-thread-marker"],
                    "event_class": "task.cli",
                    "payload": {"facts": {"status": "ready"}},
                    "created_at": CREATED,
                }
            ),
            encoding="utf-8",
        )

        cases = {
            "missing": missing,
            "unreadable": unreadable,
            "malformed": malformed,
            "non_object": non_object,
            "missing_fields": missing_fields,
            "extra_field": extra_field,
            "invalid_type": invalid_type,
        }
        forbidden = {
            str(input_root),
            "missing-private-marker",
            "unreadable-marker",
            "private_payload_marker",
            "private-list-marker",
            "must-not-leak",
            "private-thread-marker",
            "Traceback",
        }
        for name, path in cases.items():
            with self.subTest(name=name):
                exit_code, stdout, stderr = self.run_cli(
                    "prepare", "--input", str(path)
                )
                self.assertEqual(exit_code, 2)
                self.assertEqual(stdout, "")
                rejection = json.loads(stderr)
                self.assertEqual(
                    set(rejection), {"error", "message", "status"}
                )
                self.assertEqual(rejection["status"], "rejected")
                self.assertEqual(rejection["error"], "NotificationContractError")
                for marker in forbidden:
                    self.assertNotIn(marker, stderr)


if __name__ == "__main__":
    unittest.main()
