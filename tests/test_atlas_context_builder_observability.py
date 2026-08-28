from __future__ import annotations

import json
import tempfile
import time
import unittest
from pathlib import Path
from types import ModuleType

from ops.atlas.profile_codex_context import AggregateProbe, profile_context_build


class AtlasContextBuilderObservabilityTests(unittest.TestCase):
    def test_probe_reports_aggregate_reads_without_paths_or_content(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            sample = Path(temporary_directory) / "private-name.json"
            sample.write_text("secret-shaped-fixture", encoding="utf-8")

            def build(**_kwargs):
                sample.read_text(encoding="utf-8")
                sample.read_text(encoding="utf-8")
                return {
                    "context_digest": "stable",
                    "selected_refs": {"bootstrap": []},
                    "bootstrap_contract": {"ordered_reads": []},
                }

            _payload, report = profile_context_build(
                task_id="fixture",
                objective="measure fixture",
                intent_class="governance",
                atlas_data_root=Path(temporary_directory),
                build_function=build,
                prompt_renderer=lambda _payload: "prompt",
                markdown_renderer=lambda _payload: "markdown",
            )
            rendered = json.dumps(report, sort_keys=True)
            reads = report["measurement"]["file_reads"]
            self.assertEqual(2, reads["total"])
            self.assertEqual(1, reads["unique_files"])
            self.assertEqual(1, reads["repeated_reads"])
            self.assertNotIn("private-name.json", rendered)
            self.assertNotIn("secret-shaped-fixture", rendered)

    def test_profile_does_not_change_payload(self) -> None:
        calls = 0

        def build(**_kwargs):
            nonlocal calls
            calls += 1
            if calls == 2:
                time.sleep(0.05)
            return {
                "context_digest": "stable-digest",
                "selected_refs": {"bootstrap": [{"ref": "safe-ref"}]},
                "bootstrap_contract": {"ordered_reads": [{"ref": "safe-ref"}]},
            }

        payload, report = profile_context_build(
            task_id="fixture",
            objective="measure fixture",
            intent_class="governance",
            atlas_data_root=Path.cwd(),
            build_function=build,
            prompt_renderer=lambda current: current["context_digest"],
            markdown_renderer=lambda current: current["context_digest"],
        )
        self.assertEqual(2, calls)
        self.assertEqual("stable-digest", payload["context_digest"])
        self.assertEqual("stable-digest", report["payload_identity"]["context_digest"])
        self.assertTrue(report["payload_identity"]["payload_sha256"].startswith("sha256:"))
        scoped_sources = report["source_identity"]["scoped_sources"]
        self.assertEqual(
            {
                "builder",
                "awareness",
                "continuity",
                "measurement_wrapper",
            },
            set(scoped_sources),
        )
        for identity in scoped_sources.values():
            self.assertTrue(identity["sha256"].startswith("sha256:"))
        self.assertTrue(report["deterministic_regression"]["payload_equal"])
        self.assertTrue(report["deterministic_regression"]["context_digest_equal"])
        self.assertLess(
            report["measurement"]["wall_seconds"],
            report["deterministic_regression"]["reference_wall_seconds"],
        )

    def test_query_wrapper_counts_results_and_repeated_signatures(self) -> None:
        module = ModuleType("fixture_query_module")

        def query(*, root: Path, limit: int = 2):
            return {"results": [{"id": 1}, {"id": 2}][:limit]}

        module.query = query
        probe = AggregateProbe()
        probe.wrap(module, "query", "fixture_query", query=True)
        try:
            module.query(root=Path("one"), limit=2)
            module.query(root=Path("two"), limit=2)
        finally:
            probe.restore()
        report = probe.report()
        self.assertEqual(2, report["queries"]["total_calls"])
        self.assertEqual(4, report["queries"]["result_count_by_operation"]["query"])
        self.assertEqual(1, report["queries"]["repeated_calls"])

    def test_cache_counters_do_not_claim_unobserved_hits(self) -> None:
        report = AggregateProbe().report()
        cache = report["cache_reuse"]
        self.assertFalse(cache["explicit_cache_contract_observed"])
        self.assertEqual(0, cache["cache_hits"])
        self.assertEqual(0, cache["cache_misses"])
        self.assertEqual("REUSE_OPPORTUNITIES_OBSERVED_CACHE_CAUSALITY_UNKNOWN", cache["classification"])

    def test_probe_attributes_aggregate_reads_to_current_stage(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            sample = Path(temporary_directory) / "private-stage-name.json"
            sample.write_text("private-stage-content", encoding="utf-8")
            probe = AggregateProbe()
            probe._patch_path_reads()
            try:
                probe.call("fixture_stage", sample.read_text, encoding="utf-8")
                probe.call("fixture_stage", sample.read_text, encoding="utf-8")
            finally:
                probe.restore()
            rendered = json.dumps(probe.report(), sort_keys=True)
            stage = probe.report()["file_reads"]["reads_by_stage"][0]
            self.assertEqual("fixture_stage", stage["stage"])
            self.assertEqual(2, stage["total"])
            self.assertEqual(1, stage["unique_files"])
            self.assertEqual(1, stage["repeated_reads"])
            self.assertNotIn("private-stage-name.json", rendered)
            self.assertNotIn("private-stage-content", rendered)

    def test_explicit_root_binding_is_transitive_and_restored(self) -> None:
        module = ModuleType("fixture_root_module")

        def original_root() -> Path:
            return Path("original")

        module.atlas_root = original_root
        probe = AggregateProbe()
        patched = probe.bind_atlas_root(Path.cwd(), modules=[module], original=original_root)
        try:
            self.assertEqual(1, patched)
            self.assertEqual(Path.cwd().resolve(), module.atlas_root())
        finally:
            probe.restore()
        self.assertIs(original_root, module.atlas_root)


if __name__ == "__main__":
    unittest.main()
