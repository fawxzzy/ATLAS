from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from ops.validation.validate_stack import validate_initiative_provenance


def _write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


class ValidateStackInitiativeProvenanceTests(unittest.TestCase):
    def _temp_root(self) -> Path:
        temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(temp_dir.cleanup)
        root = Path(temp_dir.name)
        (root / "stack.yaml").write_text("repo_registry: {}\n", encoding="utf-8")
        return root

    def test_stale_initiative_attention_refs_are_reported(self) -> None:
        root = self._temp_root()
        source_ref = "runtime/atlas/sessions/session-proof/session.manifest.json"
        (root / source_ref).parent.mkdir(parents=True, exist_ok=True)
        (root / source_ref).write_text("{}\n", encoding="utf-8")

        _write_json(
            root / "runtime" / "state" / "atlas" / "world-model.attention.latest.json",
            {
                "attention_items": [
                    {
                        "attention_id": "sha256:current",
                    }
                ]
            },
        )
        _write_json(
            root / "docs" / "memory" / "initiatives" / "initiative-proof.json",
            {
                "contract_version": "atlas.initiative.v1",
                "id": "initiative-proof",
                "title": "Proof",
                "summary": "Proof",
                "status": "active",
                "owner": "stack-root",
                "created_at": "2026-06-14T12:00:00Z",
                "updated_at": "2026-06-14T12:00:00Z",
                "related_plan_refs": [],
                "related_decision_refs": [],
                "related_hypothesis_refs": [],
                "related_session_refs": [],
                "related_attention_refs": [
                    "attention:sha256:current",
                    "attention:sha256:stale",
                    source_ref,
                ],
                "evidence_refs": [source_ref],
                "proposed_next_session_refs": [],
                "supersedes": [],
                "superseded_by": [],
                "metadata": {
                    "authoring_source": "initiative-proposal-loop",
                    "task_id": "proof-task",
                },
            },
        )

        findings = validate_initiative_provenance(root / "stack.yaml")

        self.assertEqual(
            [finding.category for finding in findings],
            ["stale-initiative-attention-provenance"],
        )
        self.assertIn(
            "related_attention_ref does not resolve: attention:sha256:stale",
            findings[0].message,
        )

    def test_current_attention_and_file_refs_pass(self) -> None:
        root = self._temp_root()
        source_ref = "runtime/atlas/sessions/session-proof/session.manifest.json"
        (root / source_ref).parent.mkdir(parents=True, exist_ok=True)
        (root / source_ref).write_text("{}\n", encoding="utf-8")

        _write_json(
            root / "runtime" / "state" / "atlas" / "world-model.attention.latest.json",
            {
                "attention_items": [
                    {
                        "attention_id": "sha256:current",
                    }
                ]
            },
        )
        _write_json(
            root / "docs" / "memory" / "initiatives" / "initiative-proof.json",
            {
                "contract_version": "atlas.initiative.v1",
                "id": "initiative-proof",
                "title": "Proof",
                "summary": "Proof",
                "status": "active",
                "owner": "stack-root",
                "created_at": "2026-06-14T12:00:00Z",
                "updated_at": "2026-06-14T12:00:00Z",
                "related_plan_refs": [],
                "related_decision_refs": [],
                "related_hypothesis_refs": [],
                "related_session_refs": [],
                "related_attention_refs": [
                    "attention:sha256:current",
                    source_ref,
                ],
                "evidence_refs": [source_ref],
                "proposed_next_session_refs": [],
                "supersedes": [],
                "superseded_by": [],
                "metadata": {
                    "authoring_source": "initiative-proposal-loop",
                    "task_id": "proof-task",
                },
            },
        )

        findings = validate_initiative_provenance(root / "stack.yaml")

        self.assertEqual([], findings)


if __name__ == "__main__":
    unittest.main()
