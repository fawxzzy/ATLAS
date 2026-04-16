from __future__ import annotations

import json
import unittest

from ops._atlas import atlas_root
from ops.atlas.awareness import atlas_status, fetch, search
from ops.atlas.build_turn_context import build_turn_context
from ops.atlas.plan_conversation_response import compose_response


class AtlasWave11TextSlicesTests(unittest.TestCase):
    def setUp(self) -> None:
        self.root = atlas_root()

    def test_repeated_identical_turn_context_refs_match(self) -> None:
        first = build_turn_context(
            "what repo work is waiting on blessing review",
            root=self.root,
            conversation_id="wave11-repeat-a",
            mode="text",
        )
        second = build_turn_context(
            "what repo work is waiting on blessing review",
            root=self.root,
            conversation_id="wave11-repeat-b",
            mode="text",
        )
        self.assertEqual(first["retrieved_ref_set"], second["retrieved_ref_set"])

    def test_repo_waiting_on_review_prefers_mazer_slice(self) -> None:
        context = build_turn_context(
            "what repo work is waiting on blessing review",
            root=self.root,
            conversation_id="wave11-mazer",
            mode="text",
        )
        response = compose_response(context)
        self.assertIn("initiative:initiative-mazer-d2-learning-scorer", context["retrieved_ref_set"]["initiative_refs"])
        self.assertIn(
            "runtime/atlas/proposed-sessions/session-proposed-mazer-d2-fixed-blessed-id-soak/session.manifest.json",
            context["retrieved_ref_set"]["artifact_refs"],
        )
        self.assertIn("Mazer D2 Learning Scorer", response["response_text"])
        self.assertNotIn("active_session=", response["response_text"])

    def test_proposal_search_by_initiative_ref(self) -> None:
        results = search(
            "docs/memory/initiatives/initiative-mazer-d2-learning-scorer.json",
            root=self.root,
            limit=20,
        )
        proposal_items = [
            item
            for item in results["results"]
            if isinstance(item, dict) and str(item.get("id", "")).startswith("proposal:")
        ]
        self.assertTrue(proposal_items)
        proposal = fetch("proposal:initiative-mazer-d2-learning-scorer", root=self.root)
        payload = json.loads(proposal["text"])
        self.assertEqual(proposal["metadata"]["source_kind"], "proposal")
        self.assertEqual(payload["initiative_id"], "initiative-mazer-d2-learning-scorer")
        self.assertEqual(
            proposal["metadata"]["proposal_ref"],
            "runtime/atlas/proposed-sessions/session-proposed-mazer-d2-fixed-blessed-id-soak/session.manifest.json",
        )

    def test_trust_posture_keeps_verta_metadata_only(self) -> None:
        status = atlas_status(root=self.root)
        trust_posture = status["trust_posture"]
        self.assertIn("items", trust_posture)
        verta_items = [
            item
            for item in trust_posture["items"]
            if isinstance(item, dict) and "verta" in str(item.get("archive_id", "")).lower()
        ]
        self.assertTrue(verta_items)
        for item in verta_items:
            self.assertEqual(item["trust_class"], "untrusted")
            self.assertEqual(item["read_mode"], "metadata_only")
        trust_slice = fetch("slice:trust_posture", root=self.root)
        self.assertEqual(trust_slice["metadata"]["source_kind"], "status_slice")


if __name__ == "__main__":
    unittest.main()
