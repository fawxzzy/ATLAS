from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from ops._atlas import atlas_root
from ops.atlas.awareness import atlas_status, fetch_status_slice, search
from ops.atlas.continuity import (
    build_maintained_manifest_restart_index,
    build_continuity_status_slices,
    build_initiative_continuity_manifest_health,
    build_open_marker_manifest_coverage,
    build_open_marker_restart_index,
)
from ops.atlas import continuity


def _write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


class AtlasInitiativeContinuityManifestHealthTests(unittest.TestCase):
    def _temp_root(self) -> Path:
        temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(temp_dir.cleanup)
        root = Path(temp_dir.name)
        (root / "docs" / "atlas-book").mkdir(parents=True, exist_ok=True)
        (root / "docs" / "memory" / "initiatives").mkdir(parents=True, exist_ok=True)
        (root / "docs" / "ops").mkdir(parents=True, exist_ok=True)
        return root

    def test_health_reports_ok_for_consistent_manifest(self) -> None:
        root = self._temp_root()
        (root / "docs" / "atlas-book" / "02-lanes-and-markers.md").write_text(
            "\n".join(
                [
                    "# Lanes And Markers",
                    "",
                    "## Active Front-Page Marker Table",
                    "",
                    "- Truth Map & ATLAS Book: `90%`",
                    "",
                ]
            )
            + "\n",
            encoding="utf-8",
        )
        checkpoint = root / "docs" / "ops" / "checkpoint.md"
        checkpoint.write_text("# checkpoint\n", encoding="utf-8")
        supporting = root / "docs" / "ops" / "supporting.md"
        supporting.write_text("# supporting\n", encoding="utf-8")

        _write_json(
            root / "docs" / "memory" / "initiatives" / "continuity-manifest-truth-map-and-atlas-book.json",
            {
                "contract_version": "atlas.initiative.v1",
                "id": "continuity-manifest-truth-map-and-atlas-book",
                "title": "Continuity Manifest Truth Map And ATLAS Book",
                "summary": "summary",
                "status": "active",
                "owner": "stack-root",
                "created_at": "2026-06-19T00:00:00Z",
                "updated_at": "2026-06-19T00:00:00Z",
                "related_plan_refs": [],
                "related_decision_refs": [],
                "related_hypothesis_refs": [],
                "related_session_refs": [],
                "related_attention_refs": [],
                "proposed_next_session_refs": [],
                "evidence_refs": [
                    "docs/ops/checkpoint.md",
                    "docs/ops/supporting.md",
                ],
                "supersedes": [],
                "superseded_by": [],
                "metadata": {
                    "artifact_kind": "continuity_manifest",
                    "lane_id": "truth-map-and-atlas-book",
                    "scope_class": "atlas-root-governance",
                    "current_checkpoint_receipt": "docs/ops/checkpoint.md",
                    "checkpoint_commit": "main",
                    "checkpoint_summary": "summary",
                    "governing_receipts": ["docs/ops/checkpoint.md"],
                    "owner_truth_surfaces": [
                        {"path": "docs/ops/checkpoint.md", "role": "checkpoint"}
                    ],
                    "verification_adoption_surfaces": [
                        {"path": "docs/ops/supporting.md", "role": "supporting"}
                    ],
                    "blocked_or_gated_work": [],
                    "next_package_ladder": [
                        {"package": "none", "mode": "hold", "reason": "reason"}
                    ],
                    "freshness_state": "manifest-backed",
                    "freshness_checked_receipt": "docs/ops/checkpoint.md",
                    "freshness_checked_at": "2026-06-19T00:00:00Z",
                    "freshness_basis": "basis",
                    "marker_posture": [
                        {
                            "marker": "Truth Map & ATLAS Book",
                            "percent": 90,
                            "source": "docs/atlas-book/02-lanes-and-markers.md",
                        }
                    ],
                },
            },
        )

        payload = build_initiative_continuity_manifest_health(root=root)

        self.assertEqual(payload["status"], "ok")
        self.assertEqual(payload["manifest_count"], 1)
        self.assertEqual(payload["error_count"], 0)
        self.assertEqual(payload["warning_count"], 0)
        self.assertEqual(payload["items"][0]["status"], "ok")

    def test_health_reports_error_for_marker_drift_and_missing_receipt(self) -> None:
        root = self._temp_root()
        (root / "docs" / "atlas-book" / "02-lanes-and-markers.md").write_text(
            "\n".join(
                [
                    "# Lanes And Markers",
                    "",
                    "## Active Front-Page Marker Table",
                    "",
                    "- Inventory & Truth Map: `78%`",
                    "",
                ]
            )
            + "\n",
            encoding="utf-8",
        )

        _write_json(
            root / "docs" / "memory" / "initiatives" / "continuity-manifest-inventory-and-truth-map.json",
            {
                "contract_version": "atlas.initiative.v1",
                "id": "continuity-manifest-inventory-and-truth-map",
                "title": "Continuity Manifest Inventory And Truth Map",
                "summary": "summary",
                "status": "active",
                "owner": "stack-root",
                "created_at": "2026-06-19T00:00:00Z",
                "updated_at": "2026-06-19T00:00:00Z",
                "related_plan_refs": [],
                "related_decision_refs": [],
                "related_hypothesis_refs": [],
                "related_session_refs": [],
                "related_attention_refs": [],
                "proposed_next_session_refs": [],
                "evidence_refs": [],
                "supersedes": [],
                "superseded_by": [],
                "metadata": {
                    "artifact_kind": "continuity_manifest",
                    "lane_id": "inventory-and-truth-map",
                    "scope_class": "atlas-root-governance",
                    "current_checkpoint_receipt": "docs/ops/missing.md",
                    "checkpoint_commit": "main",
                    "checkpoint_summary": "summary",
                    "governing_receipts": [],
                    "owner_truth_surfaces": [],
                    "verification_adoption_surfaces": [],
                    "blocked_or_gated_work": [],
                    "next_package_ladder": [],
                    "freshness_state": "manifest-backed",
                    "freshness_checked_receipt": "docs/ops/missing.md",
                    "freshness_checked_at": "2026-06-19T00:00:00Z",
                    "freshness_basis": "basis",
                    "marker_posture": [
                        {
                            "marker": "Inventory & Truth Map",
                            "percent": 77,
                            "source": "docs/atlas-book/02-lanes-and-markers.md",
                        }
                    ],
                },
            },
        )

        payload = build_initiative_continuity_manifest_health(root=root)

        self.assertEqual(payload["status"], "error")
        self.assertEqual(payload["manifest_count"], 1)
        self.assertGreater(payload["error_count"], 0)
        self.assertEqual(payload["items"][0]["status"], "error")
        self.assertTrue(
            any("drift" in message or "does not exist" in message for message in payload["items"][0]["errors"])
        )

    def test_live_awareness_exposes_manifest_health_slice(self) -> None:
        root = atlas_root()
        status = atlas_status(root=root)
        self.assertIn("continuity_initiative_manifest_health", status["slices"])

        payload = fetch_status_slice("continuity_initiative_manifest_health", root=root)
        self.assertEqual(payload["metadata"]["slice_name"], "continuity_initiative_manifest_health")
        self.assertIn("manifest_id", payload["text"])

        results = search("continuity initiative manifest health", root=root, limit=20)
        result_ids = {
            item["id"]
            for item in results["results"]
            if isinstance(item, dict) and isinstance(item.get("id"), str)
        }
        self.assertIn("slice:continuity_initiative_manifest_health", result_ids)

    def test_open_marker_manifest_coverage_reports_eligible_markers(self) -> None:
        root = self._temp_root()
        (root / "docs" / "atlas-book" / "02-lanes-and-markers.md").write_text(
            "\n".join(
                [
                    "# Lanes And Markers",
                    "",
                    "## Active Front-Page Marker Table",
                    "",
                    "- Truth Map & ATLAS Book: `90%`",
                    "- Dependency Untangling: `100%`",
                    "",
                    "## Supporting Open Markers",
                    "",
                    "### Automation / orchestration",
                    "",
                    "- Cortex Readiness: `41%`",
                    "",
                    "### Future / lane-structure",
                    "",
                    "- Sandbox Simulation Readiness: `0%`",
                    "",
                ]
            )
            + "\n",
            encoding="utf-8",
        )
        checkpoint = root / "docs" / "ops" / "checkpoint.md"
        checkpoint.write_text("# checkpoint\n", encoding="utf-8")
        supporting = root / "docs" / "ops" / "supporting.md"
        supporting.write_text("# supporting\n", encoding="utf-8")

        _write_json(
            root / "docs" / "memory" / "initiatives" / "continuity-manifest-truth-map-and-atlas-book.json",
            {
                "contract_version": "atlas.initiative.v1",
                "id": "continuity-manifest-truth-map-and-atlas-book",
                "title": "Continuity Manifest Truth Map And ATLAS Book",
                "summary": "summary",
                "status": "active",
                "owner": "stack-root",
                "created_at": "2026-06-19T00:00:00Z",
                "updated_at": "2026-06-19T00:00:00Z",
                "related_plan_refs": [],
                "related_decision_refs": [],
                "related_hypothesis_refs": [],
                "related_session_refs": [],
                "related_attention_refs": [],
                "proposed_next_session_refs": [],
                "evidence_refs": [
                    "docs/ops/checkpoint.md",
                    "docs/ops/supporting.md"
                ],
                "supersedes": [],
                "superseded_by": [],
                "metadata": {
                    "artifact_kind": "continuity_manifest",
                    "lane_id": "truth-map-and-atlas-book",
                    "scope_class": "atlas-root-governance",
                    "current_checkpoint_receipt": "docs/ops/checkpoint.md",
                    "checkpoint_commit": "main",
                    "checkpoint_summary": "summary",
                    "governing_receipts": ["docs/ops/checkpoint.md"],
                    "owner_truth_surfaces": [
                        {"path": "docs/ops/checkpoint.md", "role": "checkpoint"}
                    ],
                    "verification_adoption_surfaces": [
                        {"path": "docs/ops/supporting.md", "role": "supporting"}
                    ],
                    "blocked_or_gated_work": [],
                    "next_package_ladder": [
                        {"package": "none", "mode": "hold", "reason": "reason"}
                    ],
                    "freshness_state": "manifest-backed",
                    "freshness_checked_receipt": "docs/ops/checkpoint.md",
                    "freshness_checked_at": "2026-06-19T00:00:00Z",
                    "freshness_basis": "basis",
                    "marker_posture": [
                        {
                            "marker": "Truth Map & ATLAS Book",
                            "percent": 90,
                            "source": "docs/atlas-book/02-lanes-and-markers.md"
                        }
                    ]
                }
            },
        )

        payload = build_open_marker_manifest_coverage(root=root)

        self.assertEqual(payload["status"], "error")
        self.assertEqual(payload["eligible_open_marker_count"], 2)
        self.assertEqual(payload["manifest_backed_count"], 1)
        self.assertEqual(payload["missing_count"], 1)
        sandbox_item = next(item for item in payload["items"] if item["marker"] == "Sandbox Simulation Readiness")
        self.assertEqual(sandbox_item["coverage_status"], "not_required")
        self.assertEqual(sandbox_item["eligibility"], "excluded_zero")

    def test_open_marker_restart_index_reports_current_checkpoint_and_next_package(self) -> None:
        root = self._temp_root()
        (root / "docs" / "atlas-book" / "02-lanes-and-markers.md").write_text(
            "\n".join(
                [
                    "# Lanes And Markers",
                    "",
                    "## Active Front-Page Marker Table",
                    "",
                    "- Truth Map & ATLAS Book: `90%`",
                    "- Dependency Untangling: `100%`",
                    "",
                    "## Supporting Open Markers",
                    "",
                    "### Automation / orchestration",
                    "",
                    "- Cortex Readiness: `41%`",
                    "",
                ]
            )
            + "\n",
            encoding="utf-8",
        )
        checkpoint = root / "docs" / "ops" / "checkpoint.md"
        checkpoint.write_text("# checkpoint\n", encoding="utf-8")
        supporting = root / "docs" / "ops" / "supporting.md"
        supporting.write_text("# supporting\n", encoding="utf-8")

        _write_json(
            root / "docs" / "memory" / "initiatives" / "continuity-manifest-truth-map-and-atlas-book.json",
            {
                "contract_version": "atlas.initiative.v1",
                "id": "continuity-manifest-truth-map-and-atlas-book",
                "title": "Continuity Manifest Truth Map And ATLAS Book",
                "summary": "summary",
                "status": "active",
                "owner": "stack-root",
                "created_at": "2026-06-19T00:00:00Z",
                "updated_at": "2026-06-19T00:00:00Z",
                "related_plan_refs": [],
                "related_decision_refs": [],
                "related_hypothesis_refs": [],
                "related_session_refs": [],
                "related_attention_refs": [],
                "proposed_next_session_refs": [],
                "evidence_refs": [
                    "docs/ops/checkpoint.md",
                    "docs/ops/supporting.md"
                ],
                "supersedes": [],
                "superseded_by": [],
                "metadata": {
                    "artifact_kind": "continuity_manifest",
                    "lane_id": "truth-map-and-atlas-book",
                    "scope_class": "atlas-root-governance",
                    "current_checkpoint_receipt": "docs/ops/checkpoint.md",
                    "checkpoint_commit": "main",
                    "checkpoint_summary": "summary",
                    "governing_receipts": ["docs/ops/checkpoint.md"],
                    "owner_truth_surfaces": [
                        {"path": "docs/ops/checkpoint.md", "role": "checkpoint"}
                    ],
                    "verification_adoption_surfaces": [
                        {"path": "docs/ops/supporting.md", "role": "supporting"}
                    ],
                    "blocked_or_gated_work": [
                        {"item": "blocked item", "requirement": "proof"}
                    ],
                    "next_package_ladder": [
                        {"package": "none", "mode": "hold", "reason": "reason"}
                    ],
                    "freshness_state": "manifest-backed",
                    "freshness_checked_receipt": "docs/ops/checkpoint.md",
                    "freshness_checked_at": "2026-06-19T00:00:00Z",
                    "freshness_basis": "basis",
                    "marker_posture": [
                        {
                            "marker": "Truth Map & ATLAS Book",
                            "percent": 90,
                            "source": "docs/atlas-book/02-lanes-and-markers.md"
                        }
                    ]
                }
            },
        )

        payload = build_open_marker_restart_index(root=root)

        self.assertEqual(payload["status"], "error")
        self.assertEqual(payload["eligible_open_marker_count"], 2)
        self.assertEqual(payload["restart_ready_count"], 1)
        self.assertEqual(payload["missing_count"], 1)
        ready_item = next(item for item in payload["items"] if item["marker"] == "Truth Map & ATLAS Book")
        self.assertEqual(ready_item["restart_status"], "restart_ready")
        self.assertEqual(ready_item["current_checkpoint_receipt"], "docs/ops/checkpoint.md")
        self.assertEqual(ready_item["next_package"]["package"], "none")
        self.assertEqual(ready_item["blocked_item_count"], 1)

    def test_maintained_manifest_restart_index_reports_all_manifests(self) -> None:
        root = self._temp_root()
        (root / "docs" / "atlas-book" / "02-lanes-and-markers.md").write_text(
            "\n".join(
                [
                    "# Lanes And Markers",
                    "",
                    "## Active Front-Page Marker Table",
                    "",
                    "- Truth Map & ATLAS Book: `90%`",
                    "- Durable Context Externalization: `80%`",
                    "",
                ]
            )
            + "\n",
            encoding="utf-8",
        )
        checkpoint = root / "docs" / "ops" / "checkpoint.md"
        checkpoint.write_text("# checkpoint\n", encoding="utf-8")
        supporting = root / "docs" / "ops" / "supporting.md"
        supporting.write_text("# supporting\n", encoding="utf-8")

        for manifest_name, marker_name, percent in (
            ("continuity-manifest-truth-map-and-atlas-book.json", "Truth Map & ATLAS Book", 90),
            ("continuity-manifest-durable-context-externalization.json", "Durable Context Externalization", 80),
        ):
            _write_json(
                root / "docs" / "memory" / "initiatives" / manifest_name,
                {
                    "contract_version": "atlas.initiative.v1",
                    "id": manifest_name.replace(".json", ""),
                    "title": marker_name,
                    "summary": "summary",
                    "status": "active",
                    "owner": "stack-root",
                    "created_at": "2026-06-19T00:00:00Z",
                    "updated_at": "2026-06-19T00:00:00Z",
                    "related_plan_refs": [],
                    "related_decision_refs": [],
                    "related_hypothesis_refs": [],
                    "related_session_refs": [],
                    "related_attention_refs": [],
                    "proposed_next_session_refs": [],
                    "evidence_refs": [
                        "docs/ops/checkpoint.md",
                        "docs/ops/supporting.md"
                    ],
                    "supersedes": [],
                    "superseded_by": [],
                    "metadata": {
                        "artifact_kind": "continuity_manifest",
                        "lane_id": marker_name.lower().replace(" ", "-").replace("&", "and"),
                        "scope_class": "atlas-root-governance",
                        "current_checkpoint_receipt": "docs/ops/checkpoint.md",
                        "checkpoint_commit": "main",
                        "checkpoint_summary": "summary",
                        "governing_receipts": ["docs/ops/checkpoint.md"],
                        "owner_truth_surfaces": [
                            {"path": "docs/ops/checkpoint.md", "role": "checkpoint"}
                        ],
                        "verification_adoption_surfaces": [
                            {"path": "docs/ops/supporting.md", "role": "supporting"}
                        ],
                        "blocked_or_gated_work": [],
                        "next_package_ladder": [
                            {"package": "none", "mode": "hold", "reason": "reason"}
                        ],
                        "freshness_state": "manifest-backed",
                        "freshness_checked_receipt": "docs/ops/checkpoint.md",
                        "freshness_checked_at": "2026-06-19T00:00:00Z",
                        "freshness_basis": "basis",
                        "marker_posture": [
                            {
                                "marker": marker_name,
                                "percent": percent,
                                "source": "docs/atlas-book/02-lanes-and-markers.md"
                            }
                        ]
                    }
                },
            )

        payload = build_maintained_manifest_restart_index(root=root)

        self.assertEqual(payload["status"], "ok")
        self.assertEqual(payload["maintained_manifest_count"], 2)
        self.assertEqual(payload["restart_ready_count"], 2)
        self.assertEqual(payload["restart_ready_percent"], 100.0)
        self.assertEqual(payload["error_count"], 0)
        item = next(
            item for item in payload["items"] if item["manifest_id"] == "continuity-manifest-truth-map-and-atlas-book"
        )
        self.assertEqual(item["restart_status"], "restart_ready")
        self.assertIn("Truth Map & ATLAS Book", item["marker_names"])
        self.assertEqual(item["next_package"]["package"], "none")

    def test_continuity_coverage_rollup_reports_structured_status(self) -> None:
        root = atlas_root()

        _, slices = build_continuity_status_slices(root=root)
        payload = slices["continuity_coverage"]

        self.assertEqual(payload["status"], "structured")
        self.assertEqual(payload["pending_review_count"], 0)
        self.assertEqual(payload["initiative_manifest_status"], "ok")
        self.assertEqual(payload["open_marker_manifest_coverage_status"], "ok")
        self.assertEqual(payload["open_marker_restart_index_status"], "ok")
        self.assertEqual(payload["maintained_manifest_restart_index_status"], "ok")

    def test_continuity_rollup_reuses_manifest_health_and_bundles_per_request(self) -> None:
        root = atlas_root()
        with (
            mock.patch.object(
                continuity,
                "build_initiative_continuity_manifest_health",
                wraps=continuity.build_initiative_continuity_manifest_health,
            ) as health_builder,
            mock.patch.object(
                continuity,
                "_load_initiative_manifest_bundles",
                wraps=continuity._load_initiative_manifest_bundles,
            ) as bundle_builder,
        ):
            build_continuity_status_slices(root=root)

        self.assertEqual(1, health_builder.call_count)
        self.assertEqual(1, bundle_builder.call_count)

    def test_continuity_rollup_matches_fresh_standalone_slices(self) -> None:
        root = atlas_root()
        _, slices = build_continuity_status_slices(root=root)
        health = build_initiative_continuity_manifest_health(root=root)
        bundles = continuity._load_initiative_manifest_bundles(root=root, manifest_health=health)

        self.assertEqual(health, slices["continuity_initiative_manifest_health"])
        self.assertEqual(
            build_open_marker_manifest_coverage(root=root, manifest_health=health),
            slices["continuity_open_marker_manifest_coverage"],
        )
        self.assertEqual(
            build_open_marker_restart_index(root=root, manifest_bundles=bundles),
            slices["continuity_open_marker_restart_index"],
        )
        self.assertEqual(
            build_maintained_manifest_restart_index(root=root, manifest_bundles=bundles),
            slices["continuity_maintained_manifest_restart_index"],
        )

    def test_continuity_rollup_refreshes_across_requests(self) -> None:
        root = self._temp_root()
        marker_path = root / "docs" / "atlas-book" / "02-lanes-and-markers.md"
        marker_path.write_text(
            "## Active Front-Page Marker Table\n\n- Freshness Fixture: `50%`\n",
            encoding="utf-8",
        )
        _, first = build_continuity_status_slices(root=root)

        marker_path.write_text(
            "## Active Front-Page Marker Table\n\n- Freshness Fixture: `75%`\n",
            encoding="utf-8",
        )
        _, second = build_continuity_status_slices(root=root)

        first_item = first["continuity_open_marker_manifest_coverage"]["items"][0]
        second_item = second["continuity_open_marker_manifest_coverage"]["items"][0]
        self.assertEqual(50, first_item["percent"])
        self.assertEqual(75, second_item["percent"])


if __name__ == "__main__":
    unittest.main()
