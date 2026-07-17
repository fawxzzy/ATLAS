from __future__ import annotations

import copy
import hashlib
import json
import tempfile
import unittest
from dataclasses import replace
from pathlib import Path
from unittest import mock

from ops._atlas import atlas_root
from ops.cortex import activation_read_model_refresh as refresh_module
from ops.cortex.activation_read_model_refresh import (
    CONTEXT_JSON_PATH,
    CURRENT_STATE_JSON_PATH,
    EVENT_PATH,
    OPERATOR_JSON_PATH,
    OUTPUT_PATHS,
    READ_MODEL_OUTPUT_PATHS,
    RECEIPT_PATH,
    RefreshBuild,
    RefreshError,
    build_refresh,
    write_or_check,
)


class CortexActivationReadModelRefreshTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.root = atlas_root()
        cls.canonical_event = json.loads((cls.root / EVENT_PATH).read_text(encoding="utf-8"))

    def _event_file(self, payload: dict | None = None) -> Path:
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        path = Path(temp.name) / "event.json"
        path.write_text(json.dumps(payload or self.canonical_event, indent=2) + "\n", encoding="utf-8")
        return path

    def _output_root(self) -> Path:
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        return Path(temp.name)

    def _build_with_matching_prior_outputs(self) -> tuple[RefreshBuild, dict[Path, bytes]]:
        build = build_refresh(repo_root=self.root)
        event = copy.deepcopy(build.event)
        prior_outputs: dict[Path, bytes] = {}
        for item, path in zip(event["prior_artifacts"], READ_MODEL_OUTPUT_PATHS, strict=True):
            raw = f"prior artifact for {path.as_posix()}\n".encode("utf-8")
            item["sha256"] = "sha256:" + hashlib.sha256(raw).hexdigest()
            prior_outputs[path] = raw
        return replace(build, event=event), prior_outputs

    def test_canonical_event_changes_exactly_step_6_and_selects_step_7(self) -> None:
        build = build_refresh(
            repo_root=self.root,
            expected_source_revision="90f9de1dd55fe17b8fd2623b71193a6cc332e8f1",
        )
        current = json.loads(build.outputs[CURRENT_STATE_JSON_PATH])
        context = json.loads(build.outputs[CONTEXT_JSON_PATH])
        operator = json.loads(build.outputs[OPERATOR_JSON_PATH])

        statuses = {step["id"]: step["status"] for step in current["activation"]["steps"]}
        self.assertEqual("accepted", statuses["cortex-event-refresh"])
        self.assertEqual("pending", statuses["discordos-interaction-first-reliability-review"])
        self.assertEqual("pending", statuses["owner-export-integration"])
        self.assertEqual(1, build.receipt["state_change"]["changed_step_count"])
        self.assertEqual("DiscordOS interaction-first reliability review", context["task_frame"]["title"])
        self.assertFalse(operator["authority"]["discord_mutation"])
        self.assertFalse(operator["authority"]["owner_health_inference"])
        self.assertEqual([], current["status_boundaries"]["stale"])
        self.assertNotIn(
            "Principal Cortex current-state, context, and operator latest artifacts remain dated 2026-07-06; complete event-triggered refresh proof is UNKNOWN.",
            current["status_boundaries"]["unknown"],
        )
        self.assertEqual(
            {
                "runtime_activation_readiness": "8/8",
                "runtime_correlation_reliability": "5/5",
                "operator_surface_adoption": "4/4",
            },
            build.receipt["unchanged_markers"],
        )

    def test_two_run_replay_is_byte_stable_and_second_run_is_noop(self) -> None:
        output_root = self._output_root()
        first = build_refresh(repo_root=self.root)
        self.assertEqual("refreshed", write_or_check(first, output_root=output_root, check=False))
        before = {
            path: hashlib.sha256((output_root / path).read_bytes()).hexdigest()
            for path in OUTPUT_PATHS
        }

        second = build_refresh(repo_root=self.root)
        self.assertEqual(first.outputs, second.outputs)
        self.assertEqual("noop", write_or_check(second, output_root=output_root, check=False))
        after = {
            path: hashlib.sha256((output_root / path).read_bytes()).hexdigest()
            for path in OUTPUT_PATHS
        }
        self.assertEqual(before, after)

    def test_malformed_nonaccepted_and_stale_events_fail_before_writes(self) -> None:
        cases: list[tuple[str, dict, str]] = []
        malformed = copy.deepcopy(self.canonical_event)
        malformed.pop("change")
        cases.append(("malformed", malformed, "malformed"))
        nonaccepted = copy.deepcopy(self.canonical_event)
        nonaccepted["event_status"] = "pending"
        cases.append(("nonaccepted", nonaccepted, "not_accepted"))
        stale = copy.deepcopy(self.canonical_event)
        stale["source"]["commit"] = "0" * 40
        cases.append(("stale", stale, "stale"))

        for name, event, classification in cases:
            with self.subTest(name=name):
                output_root = self._output_root()
                with self.assertRaises(RefreshError) as raised:
                    build_refresh(repo_root=self.root, event_path=self._event_file(event))
                self.assertEqual(classification, raised.exception.classification)
                self.assertFalse(any((output_root / path).exists() for path in OUTPUT_PATHS))

    def test_conflicting_duplicate_is_rejected_without_partial_rewrite(self) -> None:
        output_root = self._output_root()
        build = build_refresh(repo_root=self.root)
        self.assertEqual("refreshed", write_or_check(build, output_root=output_root, check=False))
        receipt_path = output_root / RECEIPT_PATH
        receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
        receipt["event_digest"] = "sha256:" + ("0" * 64)
        receipt_path.write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
        before = {path: (output_root / path).read_bytes() for path in OUTPUT_PATHS}

        with self.assertRaises(RefreshError) as raised:
            write_or_check(build, output_root=output_root, check=False)

        self.assertEqual("conflict", raised.exception.classification)
        self.assertEqual("duplicate_event_conflict", raised.exception.code)
        self.assertEqual(before, {path: (output_root / path).read_bytes() for path in OUTPUT_PATHS})

    def test_partial_output_without_receipt_is_rejected_without_additional_writes(self) -> None:
        output_root = self._output_root()
        build = build_refresh(repo_root=self.root)
        partial_path = OUTPUT_PATHS[0]
        target = output_root / partial_path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(build.outputs[partial_path])

        for check in (False, True):
            with self.subTest(check=check):
                with self.assertRaises(RefreshError) as raised:
                    write_or_check(build, output_root=output_root, check=check)
                self.assertEqual("conflict", raised.exception.classification)
                self.assertEqual("partial_output_conflict", raised.exception.code)
                self.assertEqual(
                    [partial_path],
                    [path for path in OUTPUT_PATHS if (output_root / path).exists()],
                )

    def test_complete_matching_prior_set_is_admitted_for_exactly_one_refresh(self) -> None:
        output_root = self._output_root()
        build, prior_outputs = self._build_with_matching_prior_outputs()
        for path, raw in prior_outputs.items():
            target = output_root / path
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(raw)

        with self.assertRaises(RefreshError) as raised:
            write_or_check(build, output_root=output_root, check=True)
        self.assertEqual("stale", raised.exception.classification)
        self.assertEqual("output_drift", raised.exception.code)
        self.assertEqual(
            prior_outputs,
            {path: (output_root / path).read_bytes() for path in READ_MODEL_OUTPUT_PATHS},
        )

        self.assertEqual("refreshed", write_or_check(build, output_root=output_root, check=False))
        self.assertEqual(
            build.outputs,
            {path: (output_root / path).read_bytes() for path in OUTPUT_PATHS},
        )
        self.assertEqual("noop", write_or_check(build, output_root=output_root, check=False))

    def test_mid_publish_failure_restores_prior_set_and_retry_succeeds(self) -> None:
        output_root = self._output_root()
        build, prior_outputs = self._build_with_matching_prior_outputs()
        for path, raw in prior_outputs.items():
            target = output_root / path
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(raw)

        real_replace = refresh_module._replace_path
        call_count = 0

        def fail_second_publish(source: Path, target: Path) -> None:
            nonlocal call_count
            call_count += 1
            if call_count == 2:
                raise OSError("injected publication failure")
            real_replace(source, target)

        with mock.patch.object(refresh_module, "_replace_path", side_effect=fail_second_publish):
            with self.assertRaises(RefreshError) as raised:
                write_or_check(build, output_root=output_root, check=False)

        self.assertEqual("write_failure", raised.exception.classification)
        self.assertEqual("publication_failed_rolled_back", raised.exception.code)
        self.assertEqual(
            prior_outputs,
            {path: (output_root / path).read_bytes() for path in READ_MODEL_OUTPUT_PATHS},
        )
        self.assertFalse((output_root / RECEIPT_PATH).exists())
        self.assertFalse(any(path.name.startswith(".cortex-refresh-") for path in output_root.iterdir()))

        self.assertEqual("refreshed", write_or_check(build, output_root=output_root, check=False))
        self.assertEqual(
            build.outputs,
            {path: (output_root / path).read_bytes() for path in OUTPUT_PATHS},
        )


if __name__ == "__main__":
    unittest.main()
