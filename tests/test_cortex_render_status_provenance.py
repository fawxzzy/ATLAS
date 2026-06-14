from __future__ import annotations

from pathlib import Path
import unittest
from unittest.mock import patch

from ops.cortex.render_status import provenance_alert_summary


class RenderStatusProvenanceTests(unittest.TestCase):
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
