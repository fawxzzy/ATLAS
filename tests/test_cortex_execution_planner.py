from __future__ import annotations

import io
import json
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import patch

from ops.cortex.execution_planner import (
    AUTHORITY_DENIALS,
    BRIDGE_SCHEMA_VERSION,
    EXECUTION_CLASSES,
    NO_EXECUTION_AUTHORITY,
    SCHEMA_VERSION,
    SYNTHESIS_SCHEMA_VERSION,
    TOP_LEVEL_FIELDS,
    build_plan,
    build_schema_only_payload,
    exit_code,
    main,
    validate_input_path,
    validate_output_path,
)


def _write(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value), encoding="utf-8")


class CortexExecutionPlannerTests(unittest.TestCase):
    def _root(self) -> Path:
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        return Path(directory.name)

    def _job(self, job_id: str = "job-a", **overrides: object) -> dict[str, object]:
        job: dict[str, object] = {
            "job_id": job_id,
            "objective": "Prove one bounded advisory outcome.",
            "project": "atlas",
            "component": "cortex",
            "repository": "stack",
            "owner": "stack",
            "execution_class": "read_only",
            "allowed_files": [f"ops/cortex/{job_id}.py"],
            "forbidden_files": ["secrets/**"],
            "dependencies": [],
            "resource_claims": {},
            "verification_requirements": ["python -m unittest"],
        }
        job.update(overrides)
        return job

    def _packets(self, root: Path, jobs: list[dict[str, object]] | None = None, **contract: object) -> tuple[str, str]:
        synthesis = {"schema_version": SYNTHESIS_SCHEMA_VERSION, "packet_id": "synthesis-a", "status": "ok"}
        execution_contract: dict[str, object] = {
            "selected_lane": "Cortex Dual-Mode Replacement Readiness",
            "selected_marker": "Cortex Dual-Mode Replacement Readiness = 50%",
            "selected_packet": "planner implementation",
            "objective": "Produce a bounded advisory plan.",
            "local_capability": "full-access",
            "jobs": jobs if jobs is not None else [self._job()],
        }
        execution_contract.update(contract)
        bridge = {"schema_version": BRIDGE_SCHEMA_VERSION, "packet_id": "bridge-a", "status": "ok", "execution_contract": execution_contract}
        _write(root / "tmp/atlas/synthesis.json", synthesis)
        _write(root / "tmp/atlas/bridge.json", bridge)
        return "tmp/atlas/synthesis.json", "tmp/atlas/bridge.json"

    def _plan(self, root: Path, jobs: list[dict[str, object]] | None = None, **contract: object) -> tuple[dict[str, object], str]:
        synthesis, bridge = self._packets(root, jobs, **contract)
        return build_plan(root=root, synthesis_path=synthesis, bridge_path=bridge, sources=[])

    def test_schema_only_output_is_valid_and_not_admissible(self) -> None:
        plan = build_schema_only_payload()
        self.assertEqual(SCHEMA_VERSION, plan["schema_version"])
        self.assertEqual("draft", plan["plan_status"])
        self.assertFalse(plan["safe_to_admit"])

    def test_schema_only_field_order_is_frozen(self) -> None:
        self.assertEqual(list(TOP_LEVEL_FIELDS), list(build_schema_only_payload().keys()))

    def test_schema_only_always_emits_authority_denials(self) -> None:
        authority = build_schema_only_payload()["external_action_authority"]
        self.assertEqual(NO_EXECUTION_AUTHORITY, authority["planner_authority"])
        self.assertEqual(list(AUTHORITY_DENIALS), authority["denials"])

    def test_stable_repeated_output(self) -> None:
        root = self._root()
        first, _ = self._plan(root)
        second, _ = self._plan(root)
        self.assertEqual(first, second)

    def test_single_job_planning_is_ready(self) -> None:
        plan, status = self._plan(self._root())
        self.assertEqual("ok", status)
        self.assertEqual("ready_for_admission", plan["plan_status"])
        self.assertEqual(1, len(plan["job_candidates"]))
        self.assertTrue(plan["safe_to_admit"])

    def test_derived_job_id_is_stable(self) -> None:
        root = self._root()
        job = self._job()
        job.pop("job_id")
        first, _ = self._plan(root, [job])
        second, _ = self._plan(root, [job])
        self.assertEqual(first["job_candidates"][0]["job_id"], second["job_candidates"][0]["job_id"])

    def test_multi_wave_dependencies(self) -> None:
        jobs = [self._job("first"), self._job("second", dependencies=["first"]), self._job("third", dependencies=["second"])]
        plan, _ = self._plan(self._root(), jobs)
        self.assertEqual([1, 2, 3], [wave["wave"] for wave in plan["execution_waves"]])
        self.assertEqual(2, len(plan["dependency_graph"]))

    def test_dependency_cycle_blocks_admission(self) -> None:
        jobs = [self._job("first", dependencies=["second"]), self._job("second", dependencies=["first"])]
        plan, status = self._plan(self._root(), jobs)
        self.assertEqual("blocker", status)
        self.assertFalse(plan["safe_to_admit"])
        self.assertIn("dependency_cycle", [item["code"] for item in plan["blocked_reasons"]])

    def test_unknown_dependency_blocks_admission(self) -> None:
        plan, status = self._plan(self._root(), [self._job("first", dependencies=["missing"])])
        self.assertEqual("blocker", status)
        self.assertIn("unknown_dependency", [item["code"] for item in plan["blocked_reasons"]])

    def test_resource_collisions_serialize_jobs(self) -> None:
        jobs = [self._job("one", allowed_files=["ops/cortex/shared.py"]), self._job("two", allowed_files=["ops/cortex/shared.py"])]
        plan, _ = self._plan(self._root(), jobs)
        self.assertEqual(2, len(plan["execution_waves"]))
        self.assertEqual(["files"], plan["collision_risks"][0]["resource_kinds"])

    def test_generated_artifact_collisions_serialize_jobs(self) -> None:
        claims = {"generated_artifacts": ["tmp/atlas/plan.json"]}
        plan, _ = self._plan(self._root(), [self._job("one", resource_claims=claims), self._job("two", resource_claims=claims)])
        self.assertEqual(2, len(plan["execution_waves"]))
        self.assertIn("generated_artifacts", plan["collision_risks"][0]["resource_kinds"])

    def test_schema_and_canonical_root_collisions_serialize_jobs(self) -> None:
        jobs = [self._job("one", resource_claims={"schemas": ["plan.v1"], "canonical_root": ["atlas"]}), self._job("two", resource_claims={"schemas": ["plan.v1"], "canonical_root": ["atlas"]})]
        plan, _ = self._plan(self._root(), jobs)
        self.assertEqual(2, len(plan["execution_waves"]))
        self.assertEqual(["canonical_root", "schemas"], plan["collision_risks"][0]["resource_kinds"])

    def test_worktree_port_browser_and_external_writer_collisions_serialize_jobs(self) -> None:
        for kind, claim in (("worktrees", "main"), ("ports", "3000"), ("browsers", "default"), ("external_writers", "discordos")):
            with self.subTest(kind=kind):
                claims = {kind: [claim]}
                plan, _ = self._plan(self._root(), [self._job("one", resource_claims=claims), self._job("two", resource_claims=claims)])
                self.assertEqual(2, len(plan["execution_waves"]))
                self.assertIn(kind, plan["collision_risks"][0]["resource_kinds"])

    def test_non_contending_read_only_jobs_share_wave(self) -> None:
        plan, _ = self._plan(self._root(), [self._job("one"), self._job("two")])
        self.assertEqual(1, len(plan["execution_waves"]))
        self.assertEqual(2, len(plan["execution_waves"][0]["job_ids"]))

    def test_writers_are_serialized_even_without_resource_overlap(self) -> None:
        plan, _ = self._plan(self._root(), [self._job("one", execution_class="repo_worktree"), self._job("two", execution_class="repo_worktree")])
        self.assertEqual(2, len(plan["execution_waves"]))

    def test_missing_owner_blocks_admission(self) -> None:
        job = self._job(); job.pop("owner")
        plan, status = self._plan(self._root(), [job])
        self.assertEqual("blocker", status)
        self.assertIn("missing_ownership", [item["code"] for item in plan["blocked_reasons"]])

    def test_invalid_execution_class_blocks_admission(self) -> None:
        plan, status = self._plan(self._root(), [self._job(execution_class="launch")])
        self.assertEqual("blocker", status)
        self.assertIn("invalid_execution_class", [item["code"] for item in plan["blocked_reasons"]])

    def test_digest_conflict_blocks_admission(self) -> None:
        root = self._root(); synthesis, bridge = self._packets(root)
        source = json.loads((root / synthesis).read_text(encoding="utf-8"))
        source["source_digests"] = [{"path": "docs/a.md", "sha256": "a"}, {"path": "docs/a.md", "sha256": "b"}]
        _write(root / synthesis, source)
        plan, status = build_plan(root=root, synthesis_path=synthesis, bridge_path=bridge, sources=[])
        self.assertEqual("blocker", status)
        self.assertIn("digest_conflict", [item["code"] for item in plan["blocked_reasons"]])

    def test_stale_truth_blocks_admission(self) -> None:
        root = self._root(); synthesis, bridge = self._packets(root)
        source = json.loads((root / bridge).read_text(encoding="utf-8")); source["stale"] = True; _write(root / bridge, source)
        plan, status = build_plan(root=root, synthesis_path=synthesis, bridge_path=bridge, sources=[])
        self.assertEqual("blocker", status)
        self.assertIn("stale_source_truth", [item["code"] for item in plan["blocked_reasons"]])

    def test_packet_conflict_is_not_safe_to_admit(self) -> None:
        root = self._root(); synthesis, bridge = self._packets(root)
        source = json.loads((root / synthesis).read_text(encoding="utf-8")); source["status"] = "conflict"; _write(root / synthesis, source)
        plan, status = build_plan(root=root, synthesis_path=synthesis, bridge_path=bridge, sources=[])
        self.assertEqual("conflict", status)
        self.assertEqual("blocked", plan["plan_status"])
        self.assertFalse(plan["safe_to_admit"])

    def test_unknown_authority_blocks_external_action(self) -> None:
        plan, status = self._plan(self._root(), [self._job(external_actions=["push"])])
        self.assertEqual("blocker", status)
        self.assertIn("unknown_external_authority", [item["code"] for item in plan["blocked_reasons"]])

    def test_explicit_authority_and_approval_admit_external_action_advisory_only(self) -> None:
        plan, status = self._plan(self._root(), [self._job(external_actions=["deploy"])], external_action_authority="explicit_task_local_authority", required_approvals=["current_thread_project_specific"])
        self.assertEqual("ok", status)
        self.assertTrue(plan["safe_to_admit"])
        self.assertEqual(NO_EXECUTION_AUTHORITY, plan["external_action_authority"]["planner_authority"])

    def test_full_access_is_capability_not_external_authority(self) -> None:
        plan, _ = self._plan(self._root(), local_capability="full-access")
        self.assertEqual("full-access", plan["permission_posture"]["requested_capability"])
        self.assertEqual(NO_EXECUTION_AUTHORITY, plan["external_action_authority"]["planner_authority"])

    def test_fast_fallback_warning_is_deterministic(self) -> None:
        job = self._job(runtime={"speed": "fast", "model": "candidate"})
        plan, status = self._plan(self._root(), [job])
        self.assertEqual("advisory_gap", status)
        self.assertEqual("standard", plan["runtime_recommendation"]["speed"])
        self.assertIn("fast_fallback", [item["code"] for item in plan["warnings"]])

    def test_fast_without_fallback_blocks_admission(self) -> None:
        plan, status = self._plan(self._root(), [self._job(runtime={"speed": "fast", "fallback": "blocked"})])
        self.assertEqual("blocker", status)
        self.assertIn("unsupported_runtime_without_fallback", [item["code"] for item in plan["blocked_reasons"]])

    def test_invalid_synthesis_schema_blocks_admission(self) -> None:
        root = self._root(); synthesis, bridge = self._packets(root)
        _write(root / synthesis, {"schema_version": "invalid"})
        _, status = build_plan(root=root, synthesis_path=synthesis, bridge_path=bridge, sources=[])
        self.assertEqual("blocker", status)

    def test_invalid_bridge_schema_blocks_admission(self) -> None:
        root = self._root(); synthesis, bridge = self._packets(root)
        _write(root / bridge, {"schema_version": "invalid"})
        _, status = build_plan(root=root, synthesis_path=synthesis, bridge_path=bridge, sources=[])
        self.assertEqual("blocker", status)

    def test_rejects_absolute_and_protected_paths(self) -> None:
        root = self._root(); _write(root / "docs/ok.json", {})
        for candidate in (str(root / "docs/ok.json"), "repos/app/a.json", "secrets/a.json", "runtime/a.json", "tmp/atlas/.env.json", "tmp/atlas/transcript.json"):
            with self.subTest(candidate=candidate):
                path, error = validate_input_path(root, candidate)
                self.assertIsNone(path)
                self.assertIsNotNone(error)

    def test_traversal_rejection(self) -> None:
        root = self._root()
        for candidate in ("../escape.json", "tmp/atlas/../escape.json"):
            path, error = validate_input_path(root, candidate)
            self.assertIsNone(path)
            self.assertEqual("parent_traversal", error["code"])

    def test_safe_explicit_output(self) -> None:
        root = self._root(); self._packets(root)
        with patch("ops.cortex.execution_planner.atlas_root", return_value=root), redirect_stdout(io.StringIO()):
            code = main(["--json", "--synthesis-packet", "tmp/atlas/synthesis.json", "--bridge-packet", "tmp/atlas/bridge.json", "--output", "tmp/atlas/output.json"])
        self.assertEqual(0, code)
        self.assertEqual(SCHEMA_VERSION, json.loads((root / "tmp/atlas/output.json").read_text(encoding="utf-8"))["schema_version"])

    def test_no_output_without_explicit_flag(self) -> None:
        root = self._root(); self._packets(root)
        with patch("ops.cortex.execution_planner.atlas_root", return_value=root), redirect_stdout(io.StringIO()):
            self.assertEqual(0, main(["--json", "--synthesis-packet", "tmp/atlas/synthesis.json", "--bridge-packet", "tmp/atlas/bridge.json"]))
        self.assertFalse((root / "tmp/atlas/output.json").exists())

    def test_output_rejects_non_tmp_atlas_json(self) -> None:
        root = self._root()
        for candidate in ("docs/out.json", "tmp/out.json", "tmp/atlas/out.txt", "../out.json"):
            path, error = validate_output_path(root, candidate)
            self.assertIsNone(path)
            self.assertIsNotNone(error)

    def test_strict_conflict_exit_is_two(self) -> None:
        root = self._root(); synthesis, bridge = self._packets(root)
        source = json.loads((root / synthesis).read_text(encoding="utf-8")); source["status"] = "conflict"; _write(root / synthesis, source)
        with patch("ops.cortex.execution_planner.atlas_root", return_value=root), redirect_stdout(io.StringIO()):
            code = main(["--json", "--synthesis-packet", synthesis, "--bridge-packet", bridge, "--strict"])
        self.assertEqual(2, code)

    def test_blocker_exit_is_two(self) -> None:
        root = self._root(); synthesis, bridge = self._packets(root, [self._job(execution_class="invalid")])
        with patch("ops.cortex.execution_planner.atlas_root", return_value=root), redirect_stdout(io.StringIO()):
            self.assertEqual(2, main(["--json", "--synthesis-packet", synthesis, "--bridge-packet", bridge]))

    def test_internal_error_exit_is_three(self) -> None:
        with patch("ops.cortex.execution_planner.build_plan", side_effect=RuntimeError("test")), redirect_stdout(io.StringIO()):
            self.assertEqual(3, main(["--json", "--synthesis-packet", "tmp/atlas/a.json", "--bridge-packet", "tmp/atlas/b.json"]))

    def test_exit_code_policy(self) -> None:
        self.assertEqual(0, exit_code("conflict", strict=False))
        self.assertEqual(2, exit_code("conflict", strict=True))
        self.assertEqual(3, exit_code("internal_error", strict=True))

    def test_sources_are_digested_and_sorted(self) -> None:
        root = self._root(); synthesis, bridge = self._packets(root)
        _write(root / "docs/b.json", {"b": 1}); _write(root / "docs/a.json", {"a": 1})
        plan, status = build_plan(root=root, synthesis_path=synthesis, bridge_path=bridge, sources=["docs/b.json", "docs/a.json"])
        self.assertEqual("ok", status)
        self.assertEqual(["docs/a.json", "docs/b.json", "tmp/atlas/bridge.json", "tmp/atlas/synthesis.json"], [item["path"] for item in plan["source_digests"]])

    def test_no_execution_side_effects_from_direct_planning(self) -> None:
        root = self._root(); synthesis, bridge = self._packets(root)
        before = sorted(str(path.relative_to(root)) for path in root.rglob("*"))
        build_plan(root=root, synthesis_path=synthesis, bridge_path=bridge, sources=[])
        after = sorted(str(path.relative_to(root)) for path in root.rglob("*"))
        self.assertEqual(before, after)

    def test_execution_class_literals_are_admitted(self) -> None:
        self.assertEqual(("read_only", "repo_worktree", "canonical_workspace"), EXECUTION_CLASSES)


if __name__ == "__main__":
    unittest.main()
