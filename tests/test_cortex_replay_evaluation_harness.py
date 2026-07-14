from __future__ import annotations

import io
import json
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import patch

from ops.cortex.replay_evaluation_harness import (
    ADAPTER_SCHEMA,
    AUTHORITY_DENIALS,
    CASE_SCHEMA,
    DIMENSIONS,
    NO_EXECUTION_AUTHORITY,
    PLAN_SCHEMA,
    REPORT_FIELDS,
    REPORT_SCHEMA,
    RUBRIC_SCHEMA,
    SYNTHESIS_SCHEMA,
    build_report,
    build_schema_only_payload,
    exit_code,
    main,
    validate_input_path,
    validate_output_path,
)


def _write(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value), encoding="utf-8")


class CortexReplayEvaluationHarnessTests(unittest.TestCase):
    def _root(self) -> Path:
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        return Path(directory.name)

    def _artifacts(self, root: Path, *, dimensions: list[str] | None = None, adapter_constraints: dict[str, object] | None = None, cortex_constraints: dict[str, object] | None = None, **case_overrides: object) -> tuple[str, str, str, str, str]:
        dims = dimensions or ["scope_lock"]
        case: dict[str, object] = {"schema_version": CASE_SCHEMA, "case_id": "case-a", "constraints": {}}
        case.update(case_overrides)
        adapter = {"schema_version": ADAPTER_SCHEMA, "case_id": "case-a", "constraints": adapter_constraints or {"scope_lock": ["ops/cortex/replay_evaluation_harness.py"]}}
        synthesis = {"schema_version": SYNTHESIS_SCHEMA, "case_id": "case-a", "constraints": cortex_constraints or {"scope_lock": ["ops/cortex/replay_evaluation_harness.py"]}}
        plan = {"schema_version": PLAN_SCHEMA, "case_id": "case-a"}
        rubric = {"schema_version": RUBRIC_SCHEMA, "rubric_version": "v1", "comparison_dimensions": dims, "allow_complementary": True}
        paths = ("tmp/atlas/case.json", "tmp/atlas/adapter.json", "tmp/atlas/synthesis.json", "tmp/atlas/plan.json", "tmp/atlas/rubric.json")
        for path, value in zip(paths, (case, adapter, synthesis, plan, rubric)):
            _write(root / path, value)
        return paths

    def _report(self, root: Path, **kwargs: object) -> tuple[dict[str, object], str]:
        paths = self._artifacts(root, **kwargs)
        return build_report(root=root, case_path=paths[0], adapter_path=paths[1], synthesis_path=paths[2], plan_path=paths[3], rubric_path=paths[4])

    def test_equivalent_normalized_artifacts(self) -> None:
        report, result = self._report(self._root())
        self.assertEqual("equivalent", result)
        self.assertTrue(report["safe_to_use"])

    def test_all_rubric_dimensions_normalize_equivalently(self) -> None:
        root = self._root()
        constraints = {dimension: ["same-" + dimension] for dimension in DIMENSIONS}
        report, result = self._report(root, dimensions=list(DIMENSIONS), adapter_constraints=constraints, cortex_constraints=constraints)
        self.assertEqual("equivalent", result)
        self.assertEqual(len(DIMENSIONS), report["metrics"]["compared_dimensions"])

    def test_digest_conflict_blocks_comparison(self) -> None:
        root = self._root(); paths = self._artifacts(root)
        value = json.loads((root / paths[1]).read_text()); value["source_digests"] = [{"path": "docs/a.json", "sha256": "a"}]; _write(root / paths[1], value)
        value = json.loads((root / paths[2]).read_text()); value["source_digests"] = [{"path": "docs/a.json", "sha256": "b"}]; _write(root / paths[2], value)
        report, result = build_report(root=root, case_path=paths[0], adapter_path=paths[1], synthesis_path=paths[2], plan_path=paths[3], rubric_path=paths[4])
        self.assertEqual("blocked", result); self.assertIn("digest_conflict", [item["code"] for item in report["blocked_reasons"]])

    def test_authority_widening_is_regression(self) -> None:
        root = self._root(); paths = self._artifacts(root)
        value = json.loads((root / paths[1]).read_text()); value["external_action_authority"] = "explicit_task_local_authority"; _write(root / paths[1], value)
        report, result = build_report(root=root, case_path=paths[0], adapter_path=paths[1], synthesis_path=paths[2], plan_path=paths[3], rubric_path=paths[4])
        self.assertEqual("blocked", result); self.assertIn("self_granted_authority", [item["code"] for item in report["authority_regressions"]])

    def test_repeated_output_is_deterministic(self) -> None:
        root = self._root(); first, _ = self._report(root); second, _ = self._report(root)
        self.assertEqual(first, second); self.assertEqual(first["report_id"], second["report_id"])

    def test_prior_report_regression_is_detected(self) -> None:
        root = self._root(); paths = self._artifacts(root, constraints={"scope_lock": ["required"]}, adapter_constraints={"scope_lock": ["a"]}, cortex_constraints={"scope_lock": ["b"]}, dimensions=["scope_lock"])
        prior = build_schema_only_payload(); prior["schema_version"] = REPORT_SCHEMA; prior["result_class"] = "equivalent"; _write(root / "tmp/atlas/prior.json", prior)
        report, result = build_report(root=root, case_path=paths[0], adapter_path=paths[1], synthesis_path=paths[2], plan_path=paths[3], rubric_path=paths[4], prior_report_path="tmp/atlas/prior.json")
        self.assertEqual("regression", result); self.assertIn("prior_report_regression", [item["code"] for item in report["contradictions"]])

    def test_safe_explicit_output(self) -> None:
        root = self._root(); paths = self._artifacts(root)
        with patch("ops.cortex.replay_evaluation_harness.atlas_root", return_value=root), redirect_stdout(io.StringIO()):
            code = main(["--json", "--case", paths[0], "--adapter", paths[1], "--synthesis", paths[2], "--plan", paths[3], "--rubric", paths[4], "--output", "tmp/atlas/output.json"])
        self.assertEqual(0, code); self.assertEqual(REPORT_SCHEMA, json.loads((root / "tmp/atlas/output.json").read_text())["schema_version"])

    def test_rejects_hidden_transcript_and_secret_paths(self) -> None:
        root = self._root()
        for candidate in ("tmp/atlas/hidden-transcript.json", "tmp/atlas/.env.json", "secrets/a.json"):
            with self.subTest(candidate=candidate):
                path, error = validate_input_path(root, candidate); self.assertIsNone(path); self.assertIsNotNone(error)

    def test_rejects_absolute_traversal_owner_runtime_and_live_platform_paths(self) -> None:
        root = self._root()
        for candidate in (str(root / "docs/a.json"), "../docs/a.json", "repos/a.json", "runtime/a.json", "docs/vercel.json", "docs/browser-profile.json"):
            with self.subTest(candidate=candidate):
                path, error = validate_input_path(root, candidate); self.assertIsNone(path); self.assertIsNotNone(error)

    def test_no_output_without_explicit_flag(self) -> None:
        root = self._root(); paths = self._artifacts(root)
        with patch("ops.cortex.replay_evaluation_harness.atlas_root", return_value=root), redirect_stdout(io.StringIO()):
            self.assertEqual(0, main(["--json", "--case", paths[0], "--adapter", paths[1], "--synthesis", paths[2], "--plan", paths[3], "--rubric", paths[4]]))
        self.assertFalse((root / "tmp/atlas/output.json").exists())

    def test_cortex_stricter_constraint_inclusion(self) -> None:
        report, result = self._report(self._root(), adapter_constraints={"scope_lock": ["a"]}, cortex_constraints={"scope_lock": ["a", "b"]})
        self.assertEqual("cortex_stricter", result); self.assertTrue(report["safe_to_use"])

    def test_adapter_stricter_constraint_inclusion(self) -> None:
        _, result = self._report(self._root(), adapter_constraints={"scope_lock": ["a", "b"]}, cortex_constraints={"scope_lock": ["a"]})
        self.assertEqual("adapter_stricter", result)

    def test_admitted_complementary_constraints(self) -> None:
        _, result = self._report(self._root(), adapter_constraints={"scope_lock": ["a"]}, cortex_constraints={"scope_lock": ["b"]})
        self.assertEqual("complementary", result)

    def test_unadmitted_complementary_is_incomparable(self) -> None:
        root = self._root(); paths = self._artifacts(root, adapter_constraints={"scope_lock": ["a"]}, cortex_constraints={"scope_lock": ["b"]})
        value = json.loads((root / paths[4]).read_text()); value["allow_complementary"] = False; _write(root / paths[4], value)
        _, result = build_report(root=root, case_path=paths[0], adapter_path=paths[1], synthesis_path=paths[2], plan_path=paths[3], rubric_path=paths[4])
        self.assertEqual("incomparable", result)

    def test_unknown_rubric_version_blocks(self) -> None:
        root = self._root(); paths = self._artifacts(root)
        value = json.loads((root / paths[4]).read_text()); value.pop("rubric_version"); _write(root / paths[4], value)
        report, result = build_report(root=root, case_path=paths[0], adapter_path=paths[1], synthesis_path=paths[2], plan_path=paths[3], rubric_path=paths[4])
        self.assertEqual("blocked", result); self.assertIn("unknown_rubric_version", [item["code"] for item in report["blocked_reasons"]])

    def test_unknown_dimension_blocks(self) -> None:
        root = self._root(); paths = self._artifacts(root)
        value = json.loads((root / paths[4]).read_text()); value["comparison_dimensions"] = ["unknown_dimension"]; _write(root / paths[4], value)
        _, result = build_report(root=root, case_path=paths[0], adapter_path=paths[1], synthesis_path=paths[2], plan_path=paths[3], rubric_path=paths[4])
        self.assertEqual("blocked", result)

    def test_invalid_schema_blocks(self) -> None:
        root = self._root(); paths = self._artifacts(root)
        value = json.loads((root / paths[0]).read_text()); value["schema_version"] = "invalid"; _write(root / paths[0], value)
        _, result = build_report(root=root, case_path=paths[0], adapter_path=paths[1], synthesis_path=paths[2], plan_path=paths[3], rubric_path=paths[4])
        self.assertEqual("blocked", result)

    def test_source_identity_mismatch_blocks(self) -> None:
        root = self._root(); paths = self._artifacts(root)
        value = json.loads((root / paths[3]).read_text()); value["case_id"] = "wrong"; _write(root / paths[3], value)
        report, result = build_report(root=root, case_path=paths[0], adapter_path=paths[1], synthesis_path=paths[2], plan_path=paths[3], rubric_path=paths[4])
        self.assertEqual("blocked", result); self.assertIn("source_identity_mismatch", [item["code"] for item in report["blocked_reasons"]])

    def test_case_constraint_omission_is_regression(self) -> None:
        _, result = self._report(self._root(), constraints={"scope_lock": ["required"]}, adapter_constraints={"scope_lock": ["a"]}, cortex_constraints={"scope_lock": ["a"]})
        self.assertEqual("regression", result)

    def test_schema_only_is_non_authoritative(self) -> None:
        report = build_schema_only_payload()
        self.assertEqual(REPORT_SCHEMA, report["schema_version"]); self.assertFalse(report["safe_to_use"]); self.assertEqual("blocked", report["result_class"])

    def test_report_field_order_is_frozen(self) -> None:
        self.assertEqual(list(REPORT_FIELDS), list(build_schema_only_payload().keys()))

    def test_authority_denials_are_complete(self) -> None:
        report = build_schema_only_payload()
        self.assertEqual(NO_EXECUTION_AUTHORITY, report["authority_denials"][0]); self.assertEqual(list(AUTHORITY_DENIALS), report["authority_denials"])

    def test_normal_output_contains_all_authority_denials(self) -> None:
        report, _ = self._report(self._root())
        self.assertEqual(list(AUTHORITY_DENIALS), report["authority_denials"])

    def test_strict_regression_exits_two(self) -> None:
        self.assertEqual(2, exit_code("regression", strict=True)); self.assertEqual(0, exit_code("regression", strict=False))

    def test_strict_incomparable_exits_two(self) -> None:
        self.assertEqual(2, exit_code("incomparable", strict=True)); self.assertEqual(0, exit_code("incomparable", strict=False))

    def test_strict_cli_incomparable_exits_two(self) -> None:
        root = self._root(); paths = self._artifacts(root, adapter_constraints={"scope_lock": ["a"]}, cortex_constraints={"scope_lock": ["b"]})
        value = json.loads((root / paths[4]).read_text()); value["allow_complementary"] = False; _write(root / paths[4], value)
        with patch("ops.cortex.replay_evaluation_harness.atlas_root", return_value=root), redirect_stdout(io.StringIO()):
            self.assertEqual(2, main(["--case", paths[0], "--adapter", paths[1], "--synthesis", paths[2], "--plan", paths[3], "--rubric", paths[4], "--strict"]))

    def test_blocked_always_exits_two(self) -> None:
        self.assertEqual(2, exit_code("blocked", strict=False)); self.assertEqual(2, exit_code("blocked", strict=True))

    def test_schema_only_cli_exits_zero(self) -> None:
        with redirect_stdout(io.StringIO()):
            self.assertEqual(0, main(["--json", "--schema-only"]))

    def test_output_path_must_be_tmp_atlas_json(self) -> None:
        root = self._root()
        for candidate in ("docs/out.json", "tmp/out.json", "tmp/atlas/out.txt", "../out.json"):
            with self.subTest(candidate=candidate):
                path, error = validate_output_path(root, candidate); self.assertIsNone(path); self.assertIsNotNone(error)

    def test_missing_required_input_blocks(self) -> None:
        report, result = build_report(root=self._root(), case_path=None, adapter_path=None, synthesis_path=None, plan_path=None, rubric_path=None)
        self.assertEqual("blocked", result); self.assertEqual(5, len(report["blocked_reasons"]))

    def test_explicit_docs_json_is_admitted(self) -> None:
        root = self._root(); _write(root / "docs/fixture.json", {})
        path, error = validate_input_path(root, "docs/fixture.json")
        self.assertEqual(root / "docs/fixture.json", path); self.assertIsNone(error)

    def test_all_contract_dimensions_are_known(self) -> None:
        self.assertEqual(15, len(DIMENSIONS)); self.assertIn("repeated_output_stability", DIMENSIONS)


if __name__ == "__main__":
    unittest.main()
