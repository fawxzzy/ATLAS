from __future__ import annotations

from contextlib import ExitStack
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from ops.cortex.render_status import (
    attention_queue,
    provenance_alert_summary,
    provenance_attention_items,
    render_status_payload,
)


class RenderStatusProvenanceTests(unittest.TestCase):
    def test_render_status_payload_routes_provenance_summary_into_attention_queue(self) -> None:
        provenance_summary = {
            "status": "drift_detected",
            "initiative_item_count": 1,
            "proposal_item_count": 0,
            "item_count": 1,
            "items": [
                {
                    "kind": "initiative_provenance_drift",
                    "initiative_id": "initiative-proof",
                    "title": "Proof",
                    "source_ref": "docs/memory/initiatives/initiative-proof.json",
                    "stale_attention_refs": ["attention:sha256:stale"],
                    "missing_file_refs": [],
                }
            ],
        }

        with TemporaryDirectory() as temp_dir:
            descriptor_root = Path(temp_dir)
            (descriptor_root / "placeholder.json").write_text("{}", encoding="utf-8")
            patch_specs = [
                ("ops.cortex.render_status.load_descriptors", []),
                ("ops.cortex.render_status.load_registry_state", {"ok": True}),
                ("ops.cortex.render_status.choose_latest_session", None),
                ("ops.cortex.render_status.session_overview", None),
                ("ops.cortex.render_status.blocked_workers", []),
                ("ops.cortex.render_status.classify_merge_requests", ([], [])),
                ("ops.cortex.render_status.closure_receipts", []),
                ("ops.cortex.render_status.execution_receipt_residue_records", []),
                ("ops.cortex.render_status.governed_writes", []),
                ("ops.cortex.render_status.legacy_compatibility_surfaces", []),
                ("ops.cortex.render_status.trust_surfaces", []),
                ("ops.cortex.render_status.trust_posture_summary", {}),
                ("ops.cortex.render_status.working_memory_summary", {"_items": [], "initiatives": {}}),
                ("ops.cortex.render_status.provenance_alert_summary", provenance_summary),
                ("ops.cortex.render_status.conversation_summary", {}),
                ("ops.cortex.render_status.build_canonical_lockfile_artifacts", {}),
                ("ops.cortex.render_status.repo_inventory_summary_from_lock", {"items": []}),
                ("ops.cortex.render_status.lock_worktree_hygiene", {"status": "frozen"}),
                ("ops.cortex.render_status.registry_summary", {}),
                ("ops.cortex.render_status.artifact_inventory", {}),
                ("ops.cortex.render_status.proposal_only_state", {}),
                ("ops.cortex.render_status.world_model_state", {}),
            ]
            with ExitStack() as stack:
                for target, value in patch_specs:
                    stack.enter_context(patch(target, return_value=value))
                payload = render_status_payload(descriptor_root)

        self.assertEqual(provenance_summary, payload["provenance_alerts"])
        self.assertEqual("needs_review", payload["attention_queue"]["status"])
        self.assertEqual(1, payload["attention_queue"]["item_count"])
        self.assertEqual("initiative_provenance_drift", payload["attention_queue"]["items"][0]["kind"])

    def test_render_status_payload_preserves_full_provenance_summary_while_bounding_queue_signals(self) -> None:
        provenance_summary = {
            "status": "drift_detected",
            "initiative_item_count": 3,
            "proposal_item_count": 2,
            "item_count": 5,
            "items": [
                {
                    "kind": "initiative_provenance_drift",
                    "initiative_id": "initiative-zeta",
                    "title": "Zeta",
                    "source_ref": "docs/memory/initiatives/initiative-zeta.json",
                    "stale_attention_refs": ["attention:sha256:zeta"],
                    "missing_file_refs": [],
                },
                {
                    "kind": "proposed_session_provenance_drift",
                    "session_id": "session-bravo",
                    "task_id": "task-bravo",
                    "source_ref": "runtime/atlas/proposed-sessions/session-bravo/session.manifest.json",
                    "stale_attention_refs": [],
                    "missing_initiative_ref": "docs/memory/initiatives/missing-bravo.json",
                },
                {
                    "kind": "initiative_provenance_drift",
                    "initiative_id": "initiative-alpha",
                    "title": "Alpha",
                    "source_ref": "docs/memory/initiatives/initiative-alpha.json",
                    "stale_attention_refs": [],
                    "missing_file_refs": ["docs/memory/initiatives/missing-alpha.json"],
                },
                {
                    "kind": "proposed_session_provenance_drift",
                    "session_id": "session-charlie",
                    "task_id": "task-charlie",
                    "source_ref": "runtime/atlas/proposed-sessions/session-charlie/session.manifest.json",
                    "stale_attention_refs": ["attention:sha256:charlie"],
                    "missing_initiative_ref": None,
                },
                {
                    "kind": "initiative_provenance_drift",
                    "initiative_id": "initiative-beta",
                    "title": "Beta",
                    "source_ref": "docs/memory/initiatives/initiative-beta.json",
                    "stale_attention_refs": ["attention:sha256:beta"],
                    "missing_file_refs": [],
                },
            ],
        }

        with TemporaryDirectory() as temp_dir:
            descriptor_root = Path(temp_dir)
            (descriptor_root / "placeholder.json").write_text("{}", encoding="utf-8")
            patch_specs = [
                ("ops.cortex.render_status.load_descriptors", []),
                ("ops.cortex.render_status.load_registry_state", {"ok": True}),
                ("ops.cortex.render_status.choose_latest_session", None),
                ("ops.cortex.render_status.session_overview", None),
                ("ops.cortex.render_status.blocked_workers", []),
                ("ops.cortex.render_status.classify_merge_requests", ([], [])),
                ("ops.cortex.render_status.closure_receipts", []),
                ("ops.cortex.render_status.execution_receipt_residue_records", []),
                ("ops.cortex.render_status.governed_writes", []),
                ("ops.cortex.render_status.legacy_compatibility_surfaces", []),
                ("ops.cortex.render_status.trust_surfaces", []),
                ("ops.cortex.render_status.trust_posture_summary", {}),
                ("ops.cortex.render_status.working_memory_summary", {"_items": [], "initiatives": {}}),
                ("ops.cortex.render_status.provenance_alert_summary", provenance_summary),
                ("ops.cortex.render_status.conversation_summary", {}),
                ("ops.cortex.render_status.build_canonical_lockfile_artifacts", {}),
                ("ops.cortex.render_status.repo_inventory_summary_from_lock", {"items": []}),
                ("ops.cortex.render_status.lock_worktree_hygiene", {"status": "frozen"}),
                ("ops.cortex.render_status.registry_summary", {}),
                ("ops.cortex.render_status.artifact_inventory", {}),
                ("ops.cortex.render_status.proposal_only_state", {}),
                ("ops.cortex.render_status.world_model_state", {}),
            ]
            with ExitStack() as stack:
                for target, value in patch_specs:
                    stack.enter_context(patch(target, return_value=value))
                payload = render_status_payload(descriptor_root)

        self.assertEqual(provenance_summary, payload["provenance_alerts"])
        self.assertEqual(5, payload["provenance_alerts"]["item_count"])
        self.assertEqual(5, len(payload["provenance_alerts"]["items"]))
        self.assertEqual("needs_review", payload["attention_queue"]["status"])
        self.assertEqual(4, payload["attention_queue"]["item_count"])
        self.assertEqual("high", payload["attention_queue"]["highest_severity"])
        self.assertEqual(
            [
                "initiative_provenance_drift",
                "proposed_session_provenance_drift",
                "initiative_provenance_drift",
                "provenance_alert_overflow",
            ],
            [item["kind"] for item in payload["attention_queue"]["items"]],
        )
        self.assertEqual(
            {
                "suppressed_item_count": 2,
                "signal_cap": 3,
                "highest_suppressed_severity": "medium",
                "total_provenance_alert_count": 5,
            },
            payload["attention_queue"]["items"][3]["details"],
        )

    def test_provenance_attention_items_ignore_malformed_and_unknown_payloads(self) -> None:
        items = provenance_attention_items(
            {
                "items": [
                    "not-a-dict",
                    {"kind": "initiative_provenance_drift", "initiative_id": "empty-initiative"},
                    {"kind": "proposed_session_provenance_drift", "session_id": "empty-session"},
                    {"kind": "unknown_provenance_kind", "source_ref": "docs/memory/initiatives/ignored.json"},
                    {
                        "kind": "initiative_provenance_drift",
                        "initiative_id": "initiative-proof",
                        "source_ref": "docs/memory/initiatives/initiative-proof.json",
                        "stale_attention_refs": ["attention:sha256:stale"],
                        "missing_file_refs": [],
                    },
                ]
            }
        )

        self.assertEqual(1, len(items))
        self.assertEqual("initiative_provenance_drift", items[0]["kind"])
        self.assertEqual("medium", items[0]["severity"])
        self.assertEqual(["attention:sha256:stale"], items[0]["details"]["stale_attention_refs"])

    def test_provenance_attention_items_cap_signals_and_surface_overflow(self) -> None:
        items = provenance_attention_items(
            {
                "items": [
                    {
                        "kind": "initiative_provenance_drift",
                        "initiative_id": "initiative-zeta",
                        "source_ref": "docs/memory/initiatives/initiative-zeta.json",
                        "stale_attention_refs": ["attention:sha256:zeta"],
                        "missing_file_refs": [],
                    },
                    {
                        "kind": "proposed_session_provenance_drift",
                        "session_id": "session-bravo",
                        "task_id": "task-bravo",
                        "source_ref": "runtime/atlas/proposed-sessions/session-bravo/session.manifest.json",
                        "stale_attention_refs": [],
                        "missing_initiative_ref": "docs/memory/initiatives/missing-bravo.json",
                    },
                    {
                        "kind": "initiative_provenance_drift",
                        "initiative_id": "initiative-alpha",
                        "source_ref": "docs/memory/initiatives/initiative-alpha.json",
                        "stale_attention_refs": [],
                        "missing_file_refs": ["docs/memory/initiatives/missing-alpha.json"],
                    },
                    {
                        "kind": "proposed_session_provenance_drift",
                        "session_id": "session-charlie",
                        "task_id": "task-charlie",
                        "source_ref": "runtime/atlas/proposed-sessions/session-charlie/session.manifest.json",
                        "stale_attention_refs": ["attention:sha256:charlie"],
                        "missing_initiative_ref": None,
                    },
                    {
                        "kind": "initiative_provenance_drift",
                        "initiative_id": "initiative-beta",
                        "source_ref": "docs/memory/initiatives/initiative-beta.json",
                        "stale_attention_refs": ["attention:sha256:beta"],
                        "missing_file_refs": [],
                    },
                ]
            }
        )

        self.assertEqual(4, len(items))
        self.assertEqual(
            [
                "initiative_provenance_drift",
                "proposed_session_provenance_drift",
                "initiative_provenance_drift",
                "provenance_alert_overflow",
            ],
            [item["kind"] for item in items],
        )
        self.assertEqual(
            ["high", "high", "medium", "medium"],
            [item["severity"] for item in items],
        )
        self.assertEqual("initiative-alpha", items[0]["details"]["initiative_id"])
        self.assertEqual("session-bravo", items[1]["details"]["session_id"])
        self.assertEqual("initiative-beta", items[2]["details"]["initiative_id"])
        self.assertEqual(2, items[3]["details"]["suppressed_item_count"])
        self.assertEqual(3, items[3]["details"]["signal_cap"])
        self.assertEqual(5, items[3]["details"]["total_provenance_alert_count"])
        self.assertEqual("medium", items[3]["details"]["highest_suppressed_severity"])

    def test_provenance_alerts_route_into_attention_queue(self) -> None:
        queue = attention_queue(
            descriptors=[],
            active_session=None,
            blocked_workers_payload=[],
            open_merge_requests_payload=[],
            closure_receipts_payload=[],
            legacy_compatibility_payload=[],
            trust_surfaces_payload=[],
            working_memory_items=[],
            provenance_alerts={
                "status": "drift_detected",
                "initiative_item_count": 1,
                "proposal_item_count": 1,
                "item_count": 2,
                "items": [
                    {
                        "kind": "initiative_provenance_drift",
                        "initiative_id": "initiative-proof",
                        "title": "Proof",
                        "source_ref": "docs/memory/initiatives/initiative-proof.json",
                        "stale_attention_refs": ["attention:sha256:stale"],
                        "missing_file_refs": ["docs/memory/initiatives/missing.json"],
                    },
                    {
                        "kind": "proposed_session_provenance_drift",
                        "session_id": "session-proposed-proof",
                        "task_id": "proof-task",
                        "source_ref": "runtime/atlas/proposed-sessions/session-proposed-proof/session.manifest.json",
                        "stale_attention_refs": ["attention:sha256:stale"],
                        "missing_initiative_ref": None,
                    },
                ],
            },
            registry_state={"ok": True},
        )

        self.assertEqual("needs_review", queue["status"])
        self.assertEqual(2, queue["item_count"])
        self.assertEqual("high", queue["highest_severity"])
        self.assertEqual("initiative_provenance_drift", queue["items"][0]["kind"])
        self.assertEqual("high", queue["items"][0]["severity"])
        self.assertEqual("proposed_session_provenance_drift", queue["items"][1]["kind"])
        self.assertEqual("medium", queue["items"][1]["severity"])

    def test_attention_queue_is_clear_without_initiative_or_provenance_items(self) -> None:
        queue = attention_queue(
            descriptors=[],
            active_session=None,
            blocked_workers_payload=[],
            open_merge_requests_payload=[],
            closure_receipts_payload=[],
            legacy_compatibility_payload=[],
            trust_surfaces_payload=[],
            working_memory_items=[],
            provenance_alerts={"status": "clear", "item_count": 0, "items": []},
            registry_state={"ok": True},
        )

        self.assertEqual("clear", queue["status"])
        self.assertEqual(0, queue["item_count"])
        self.assertIsNone(queue["highest_severity"])
        self.assertEqual([], queue["items"])

    def test_attention_queue_routes_initiative_open_attention_without_provenance(self) -> None:
        queue = attention_queue(
            descriptors=[],
            active_session=None,
            blocked_workers_payload=[],
            open_merge_requests_payload=[],
            closure_receipts_payload=[],
            legacy_compatibility_payload=[],
            trust_surfaces_payload=[],
            working_memory_items=[
                {
                    "memory_kind": "initiative",
                    "id": "initiative-open",
                    "title": "Open initiative",
                    "path": "docs/memory/initiatives/initiative-open.json",
                    "status": "active",
                    "metadata": {
                        "attention_summary": "Needs review",
                        "attention_severity": "medium",
                    },
                }
            ],
            provenance_alerts={"status": "clear", "item_count": 0, "items": []},
            registry_state={"ok": True},
        )

        self.assertEqual("needs_review", queue["status"])
        self.assertEqual(1, queue["item_count"])
        self.assertEqual("medium", queue["highest_severity"])
        self.assertEqual("initiative_open_attention", queue["items"][0]["kind"])

    def test_attention_queue_preserves_deterministic_order_for_mixed_initiative_and_provenance_items(self) -> None:
        queue = attention_queue(
            descriptors=[],
            active_session=None,
            blocked_workers_payload=[],
            open_merge_requests_payload=[],
            closure_receipts_payload=[],
            legacy_compatibility_payload=[],
            trust_surfaces_payload=[],
            working_memory_items=[
                {
                    "memory_kind": "initiative",
                    "id": "initiative-open",
                    "title": "Open initiative",
                    "path": "docs/memory/initiatives/initiative-open.json",
                    "status": "active",
                    "metadata": {
                        "attention_summary": "Needs review",
                        "attention_severity": "medium",
                    },
                }
            ],
            provenance_alerts={
                "status": "drift_detected",
                "initiative_item_count": 1,
                "proposal_item_count": 0,
                "item_count": 1,
                "items": [
                    {
                        "kind": "initiative_provenance_drift",
                        "initiative_id": "initiative-proof",
                        "title": "Proof",
                        "source_ref": "docs/memory/initiatives/initiative-proof.json",
                        "stale_attention_refs": [],
                        "missing_file_refs": ["docs/memory/initiatives/missing.json"],
                    }
                ],
            },
            registry_state={"ok": True},
        )

        self.assertEqual("needs_review", queue["status"])
        self.assertEqual(2, queue["item_count"])
        self.assertEqual("high", queue["highest_severity"])
        self.assertEqual(
            ["initiative_provenance_drift", "initiative_open_attention"],
            [item["kind"] for item in queue["items"]],
        )

    def test_attention_queue_omits_initiatives_without_actionable_attention_summary(self) -> None:
        queue = attention_queue(
            descriptors=[],
            active_session=None,
            blocked_workers_payload=[],
            open_merge_requests_payload=[],
            closure_receipts_payload=[],
            legacy_compatibility_payload=[],
            trust_surfaces_payload=[],
            working_memory_items=[
                {
                    "memory_kind": "initiative",
                    "id": "initiative-idle",
                    "title": "Idle initiative",
                    "path": "docs/memory/initiatives/initiative-idle.json",
                    "status": "active",
                    "metadata": {},
                }
            ],
            provenance_alerts={"status": "clear", "item_count": 0, "items": []},
            registry_state={"ok": True},
        )

        self.assertEqual("clear", queue["status"])
        self.assertEqual(0, queue["item_count"])
        self.assertEqual([], queue["items"])

    def test_provenance_summary_reports_initiative_and_proposal_drift(self) -> None:
        working_memory_items = [
            {
                "memory_kind": "initiative",
                "id": "initiative-proof",
                "title": "Proof",
                "path": "docs/memory/initiatives/initiative-proof.json",
                "related_attention_refs": [
                    "attention:sha256:current",
                    "attention:sha256:stale",
                ],
            }
        ]
        descriptors = [
            {
                "artifact_type": "session_manifest",
                "source_ref": "runtime/atlas/proposed-sessions/session-proposed-proof/session.manifest.json",
                "identity": {
                    "session_id": "session-proposed-proof",
                    "task_id": "proof-task",
                },
                "state": {
                    "session_state": "proposed",
                },
                "links": {
                    "initiative_ref": "docs/memory/initiatives/missing.json",
                    "triggering_attention_refs": [
                        "attention:sha256:current",
                        "attention:sha256:stale",
                    ],
                },
            }
        ]

        with patch(
            "ops.cortex.render_status.load_current_attention_refs",
            return_value={"attention:sha256:current"},
        ), patch(
            "ops.cortex.render_status.resolve_atlas_path",
            side_effect=lambda ref, root: Path(__file__).with_name("missing.json"),
        ):
            summary = provenance_alert_summary(
                working_memory_items=working_memory_items,
                descriptors=descriptors,
            )

        self.assertEqual("drift_detected", summary["status"])
        self.assertEqual(1, summary["initiative_item_count"])
        self.assertEqual(1, summary["proposal_item_count"])
        self.assertEqual(2, summary["item_count"])
        self.assertEqual("initiative_provenance_drift", summary["items"][0]["kind"])
        self.assertEqual("proposed_session_provenance_drift", summary["items"][1]["kind"])

    def test_provenance_summary_is_clear_when_refs_resolve(self) -> None:
        working_memory_items = [
            {
                "memory_kind": "initiative",
                "id": "initiative-proof",
                "title": "Proof",
                "path": "docs/memory/initiatives/initiative-proof.json",
                "related_attention_refs": [
                    "attention:sha256:current",
                ],
            }
        ]
        descriptors = [
            {
                "artifact_type": "session_manifest",
                "source_ref": "runtime/atlas/proposed-sessions/session-proposed-proof/session.manifest.json",
                "identity": {
                    "session_id": "session-proposed-proof",
                    "task_id": "proof-task",
                },
                "state": {
                    "session_state": "proposed",
                },
                "links": {
                    "initiative_ref": "docs/memory/initiatives/initiative-proof.json",
                    "triggering_attention_refs": [
                        "attention:sha256:current",
                    ],
                },
            }
        ]

        with patch(
            "ops.cortex.render_status.load_current_attention_refs",
            return_value={"attention:sha256:current"},
        ), patch(
            "ops.cortex.render_status.resolve_atlas_path",
            side_effect=lambda ref, root: Path(__file__) if ref == "docs/memory/initiatives/initiative-proof.json" else Path(__file__).with_name("missing.json"),
        ):
            summary = provenance_alert_summary(
                working_memory_items=working_memory_items,
                descriptors=descriptors,
            )

        self.assertEqual("clear", summary["status"])
        self.assertEqual(0, summary["item_count"])
        self.assertEqual([], summary["items"])


if __name__ == "__main__":
    unittest.main()
