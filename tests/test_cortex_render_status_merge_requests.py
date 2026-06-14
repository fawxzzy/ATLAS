from __future__ import annotations

import unittest

from ops.cortex.render_status import classify_merge_requests


class RenderStatusMergeRequestTests(unittest.TestCase):
    def test_completed_lineage_member_suppresses_duplicate_open_merge_request(self) -> None:
        canonical_ref = "runtime/cortex/supervisor/session-proof/merge-request-new.json"
        descriptors = [
            {
                "artifact_type": "session_manifest",
                "links": {"merge_request_refs": [canonical_ref]},
            },
            {
                "artifact_type": "supervisor_merge_completion",
                "identity": {"merge_request_id": "merge-request-new"},
            },
            {
                "artifact_type": "merge_request",
                "source_ref": canonical_ref,
                "identity": {
                    "merge_request_id": "merge-request-new",
                    "conflict_key": "stack-lock-new",
                    "lineage_key": "shared-lineage",
                },
                "links": {"conflicting_workers": ["worker-a", "worker-b"]},
                "state": {"registry_digest": "sha256:new"},
            },
            {
                "artifact_type": "merge_request",
                "source_ref": "runtime/cortex/supervisor/session-proof/merge-request-old-a.json",
                "identity": {
                    "merge_request_id": "merge-request-old-a",
                    "conflict_key": "stack-lock-old",
                    "lineage_key": "shared-lineage",
                },
                "links": {"conflicting_workers": ["worker-b"]},
                "state": {"registry_digest": "sha256:old"},
            },
            {
                "artifact_type": "merge_request",
                "source_ref": "runtime/cortex/supervisor/session-proof/merge-request-old-b.json",
                "identity": {
                    "merge_request_id": "merge-request-old-b",
                    "conflict_key": "stack-lock-old",
                    "lineage_key": "shared-lineage",
                },
                "links": {"conflicting_workers": ["worker-a", "worker-b"]},
                "state": {"registry_digest": "sha256:old"},
            },
        ]

        active, residue = classify_merge_requests(descriptors)
        self.assertEqual(active, [])
        self.assertEqual(len(residue), 2)
        self.assertTrue(all(item["status"] == "superseded_residue" for item in residue))
        self.assertTrue(all(item["canonical_source_ref"] == canonical_ref for item in residue))

    def test_unlinked_lineage_chooses_broadest_active_member(self) -> None:
        broad_ref = "runtime/cortex/supervisor/session-proof/merge-request-broad.json"
        descriptors = [
            {
                "artifact_type": "merge_request",
                "source_ref": "runtime/cortex/supervisor/session-proof/merge-request-narrow.json",
                "identity": {
                    "merge_request_id": "merge-request-narrow",
                    "conflict_key": "stack-lock-old",
                    "lineage_key": "shared-lineage",
                },
                "links": {"conflicting_workers": ["worker-b"]},
                "state": {"registry_digest": "sha256:old"},
            },
            {
                "artifact_type": "merge_request",
                "source_ref": broad_ref,
                "identity": {
                    "merge_request_id": "merge-request-broad",
                    "conflict_key": "stack-lock-new",
                    "lineage_key": "shared-lineage",
                },
                "links": {"conflicting_workers": ["worker-a", "worker-b"]},
                "state": {"registry_digest": "sha256:new"},
            },
        ]

        active, residue = classify_merge_requests(descriptors)
        self.assertEqual(len(active), 1)
        self.assertEqual(active[0]["source_ref"], broad_ref)
        self.assertEqual(len(residue), 1)
        self.assertEqual(residue[0]["status"], "retained_residue")


if __name__ == "__main__":
    unittest.main()
