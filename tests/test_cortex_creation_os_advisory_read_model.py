from __future__ import annotations

import copy
import hashlib
import json
import tempfile
import unittest
from dataclasses import replace
from pathlib import Path

import ops.cortex.creation_os_advisory_read_model as model


ROOT = Path(__file__).resolve().parents[1]


def _read(relative: str) -> bytes:
    return (ROOT / relative).read_bytes()


def _synthetic_sources() -> tuple[dict[str, bytes], dict[str, bytes], dict[str, object], model.PinnedSources]:
    atlas_blobs = {
        model.MANIFEST_PATH.as_posix(): _read(model.MANIFEST_PATH.as_posix()),
        model.KNOWLEDGE_CANDIDATE_SCHEMA_PATH.as_posix(): _read(model.KNOWLEDGE_CANDIDATE_SCHEMA_PATH.as_posix()),
    }
    manifest = json.loads(atlas_blobs[model.MANIFEST_PATH.as_posix()])
    manifest_by_id = {record["record_id"]: record for record in manifest["records"]}
    receipt_candidates = []
    queue_candidates = []
    for candidate_id, (kind, destination, artifact_sha256) in model.EXPECTED_CANDIDATES.items():
        artifact_path = f"data/knowledge-candidates/creation-os/{candidate_id}.knowledge-candidate.v2.json"
        atlas_blobs[artifact_path] = _read(artifact_path)
        candidate = json.loads(atlas_blobs[artifact_path])
        content_sha256 = hashlib.sha256(model._canonical_compact(candidate)).hexdigest()
        record_id = f"record-{candidate_id}"
        consumer_receipt_id = f"receipt-{candidate_id}"
        consumer_receipt = {
            "receipt_id": consumer_receipt_id,
            "candidate_record_id": record_id,
            "candidate_content_sha256": content_sha256,
            "owner_disposition": "accept",
            "promotion_authority": "none",
            "decision": "candidate-only-admitted",
        }
        queue_candidates.append({
            "external_candidate_id": candidate_id,
            "record_id": record_id,
            "candidate_content_sha256": content_sha256,
            "candidate": candidate,
            "source_artifact": {"path": artifact_path, "sha256": artifact_sha256},
            "owner_disposition": "accept",
            "admission": {"state": "review-candidate", "promotion_authority": "none", "suggested_destination_authority": "proposal-only"},
            "consumer_receipt": consumer_receipt,
        })
        receipt_candidates.append({
            "candidate_id": candidate_id,
            "source_revision": model.PINNED.atlas_revision,
            "source_artifact_path": artifact_path,
            "source_artifact_sha256": artifact_sha256,
            "manifest_record_sha256": manifest_by_id[candidate_id]["record_sha256"],
            "kind": kind,
            "suggested_destination": destination,
            "review_status": "candidate",
            "candidate_record_id": record_id,
            "candidate_content_sha256": content_sha256,
            "consumer_receipt_id": consumer_receipt_id,
            "owner_disposition": {"decision": "accept", "effect": "candidate-review-only"},
        })
    queue = {"schema_version": "1.0", "kind": "playbook.atlas-knowledge-candidate.queue.v1", "candidates": queue_candidates}
    queue_raw = model.canonical_json_bytes(queue)
    pinned = replace(model.PINNED, queue_sha256=model._sha256(queue_raw))
    receipt = {
        "schema_version": "1.0",
        "kind": "playbook.atlas-knowledge-candidate.owner-intake-receipt.v1",
        "receipt_id": pinned.playbook_receipt_id,
        "authority": {"mode": "candidate-review-only", "promotion_authority": "none", "doctrine_mutation": False},
        "source": {"revision": pinned.atlas_revision, "manifest_path": model.MANIFEST_PATH.as_posix(), "manifest_sha256": pinned.manifest_sha256, "counts": {"total_source_records": 7, "knowledge_candidates": 6, "deferred_decisions": 1}},
        "registry": {"queue_sha256": pinned.queue_sha256, "candidate_count": 6, "owner_disposition_count": 6},
        "candidates": receipt_candidates,
        "excluded": [{"candidate_id": model.DECISION_ID, "classification": "atlas-product-decision", "kind": "decision", "disposition": "deferred-atlas-product-decision"}],
        "proof": {"doctrine_invariance": {"baseline_revision": pinned.playbook_baseline, "intake_revision": pinned.playbook_initial_intake, "paths": [{"path": "docs/PLAYBOOK_NOTES.md", "before_sha256": "sha256:same", "after_sha256": "sha256:same"}]}},
    }
    playbook_blobs = {
        model.PLAYBOOK_QUEUE_PATH.as_posix(): queue_raw,
        model.PLAYBOOK_RECEIPT_PATH.as_posix(): model.canonical_json_bytes(receipt),
    }
    topology = {"parents": [pinned.playbook_baseline, pinned.playbook_accepted_head], "accepted_head_is_ancestor": True, "committed_at": "2026-07-16T13:56:04Z"}
    return atlas_blobs, playbook_blobs, topology, pinned


def _build(atlas_blobs=None, playbook_blobs=None, topology=None, pinned=None):
    defaults = _synthetic_sources()
    return model.build_models(
        atlas_revision=(pinned or defaults[3]).atlas_revision,
        playbook_revision=(pinned or defaults[3]).playbook_revision,
        atlas_blobs=atlas_blobs or defaults[0],
        playbook_blobs=playbook_blobs or defaults[1],
        topology=topology or defaults[2],
        pinned=pinned or defaults[3],
    )


class CreationOsAdvisoryReadModelTests(unittest.TestCase):
    def test_builds_exact_candidate_only_and_separate_decision_models(self) -> None:
        catalog, query, receipt = _build()
        self.assertEqual(6, len(catalog["candidate_projections"]))
        self.assertEqual([], catalog["promoted_knowledge"])
        self.assertEqual([model.DECISION_ID], [item["record_id"] for item in catalog["deferred_product_decisions"]])
        self.assertNotIn(model.DECISION_ID, {item["candidate_id"] for item in catalog["candidate_projections"]})
        self.assertFalse(catalog["marker_movement_authorized"])
        self.assertEqual([], catalog["marker_deltas"])
        self.assertFalse(catalog["authority"]["execution"])
        self.assertFalse(query["selection"]["automatic_selection"])
        self.assertEqual("corrected-and-verified", receipt["extensions"]["base_proof_correction"]["status"])
        self.assertEqual("unknown-not-exposed", receipt["runtime_effective"]["speed"])
        self.assertEqual(
            "not-performed-by-generator-terminal-proof-required",
            receipt["extensions"]["global_cortex_surfaces"]["actual_identity_verification"],
        )

    def test_render_is_canonical_lf_and_repeatable(self) -> None:
        first = model.render_outputs(*_build())
        second = model.render_outputs(*_build())
        self.assertEqual(first, second)
        for raw in first.values():
            self.assertTrue(raw.endswith(b"\n"))
            self.assertNotIn(b"\r\n", raw)
        model.validate_rendered_outputs(first, ROOT)

    def test_failure_classifications_are_fail_closed(self) -> None:
        atlas, playbook, topology, pinned = _synthetic_sources()
        with self.assertRaisesRegex(model.EvidenceError, "pinned source set") as stale:
            model.build_models(atlas_revision="0" * 40, playbook_revision=pinned.playbook_revision, atlas_blobs=atlas, playbook_blobs=playbook, topology=topology, pinned=pinned)
        self.assertEqual("stale", stale.exception.classification)

        missing = dict(atlas)
        missing.pop(model.MANIFEST_PATH.as_posix())
        with self.assertRaises(model.EvidenceError) as unknown:
            model.build_models(atlas_revision=pinned.atlas_revision, playbook_revision=pinned.playbook_revision, atlas_blobs=missing, playbook_blobs=playbook, topology=topology, pinned=pinned)
        self.assertEqual("unknown", unknown.exception.classification)

        mutated = dict(atlas)
        artifact_path = next(path for path in mutated if path.endswith(".knowledge-candidate.v2.json"))
        mutated[artifact_path] = mutated[artifact_path].replace(b"rule", b"pattern", 1)
        with self.assertRaises(model.EvidenceError) as conflict:
            model.build_models(atlas_revision=pinned.atlas_revision, playbook_revision=pinned.playbook_revision, atlas_blobs=mutated, playbook_blobs=playbook, topology=topology, pinned=pinned)
        self.assertEqual("conflict", conflict.exception.classification)

    def test_duplicate_decision_doctrine_and_disposition_drift_are_conflicts_without_write(self) -> None:
        atlas, playbook, topology, pinned = _synthetic_sources()
        sentinel_dir = Path(tempfile.mkdtemp())
        sentinel = sentinel_dir / model.CATALOG_PATH
        sentinel.parent.mkdir(parents=True)
        sentinel.write_bytes(b"sentinel\n")

        cases = []
        receipt = json.loads(playbook[model.PLAYBOOK_RECEIPT_PATH.as_posix()])
        receipt["candidates"][-1]["candidate_id"] = receipt["candidates"][0]["candidate_id"]
        cases.append({**playbook, model.PLAYBOOK_RECEIPT_PATH.as_posix(): model.canonical_json_bytes(receipt)})

        receipt = json.loads(playbook[model.PLAYBOOK_RECEIPT_PATH.as_posix()])
        receipt["proof"]["doctrine_invariance"]["paths"][0]["after_sha256"] = "sha256:changed"
        cases.append({**playbook, model.PLAYBOOK_RECEIPT_PATH.as_posix(): model.canonical_json_bytes(receipt)})

        receipt = json.loads(playbook[model.PLAYBOOK_RECEIPT_PATH.as_posix()])
        receipt["candidates"][0]["owner_disposition"]["decision"] = "reject"
        cases.append({**playbook, model.PLAYBOOK_RECEIPT_PATH.as_posix(): model.canonical_json_bytes(receipt)})

        queue = json.loads(playbook[model.PLAYBOOK_QUEUE_PATH.as_posix()])
        queue["candidates"][0]["external_candidate_id"] = model.DECISION_ID
        queue_raw = model.canonical_json_bytes(queue)
        cases.append({**playbook, model.PLAYBOOK_QUEUE_PATH.as_posix(): queue_raw})

        for candidate_playbook in cases:
            case_pinned = replace(pinned, queue_sha256=model._sha256(candidate_playbook[model.PLAYBOOK_QUEUE_PATH.as_posix()]))
            receipt_payload = json.loads(candidate_playbook[model.PLAYBOOK_RECEIPT_PATH.as_posix()])
            receipt_payload["registry"]["queue_sha256"] = case_pinned.queue_sha256
            candidate_playbook[model.PLAYBOOK_RECEIPT_PATH.as_posix()] = model.canonical_json_bytes(receipt_payload)
            with self.assertRaises(model.EvidenceError) as conflict:
                model.build_models(atlas_revision=case_pinned.atlas_revision, playbook_revision=case_pinned.playbook_revision, atlas_blobs=atlas, playbook_blobs=candidate_playbook, topology=topology, pinned=case_pinned)
            self.assertEqual("conflict", conflict.exception.classification)
            self.assertEqual(b"sentinel\n", sentinel.read_bytes())


if __name__ == "__main__":
    unittest.main()
