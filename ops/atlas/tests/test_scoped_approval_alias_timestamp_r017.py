from __future__ import annotations

import json
import multiprocessing
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from ops.atlas.scoped_approval_alias import (
    ScopedApprovalError,
    _write_once_or_idempotent,
    authorize_alias,
    canonical_alias_path,
    canonical_authorization_path,
    canonical_consumption_path,
    canonicalize_decision_request,
    consume_alias,
    issue_alias,
)


def _consume_race_worker(
    alias_path: str,
    authorization_path: str,
    correlation: str,
    barrier: multiprocessing.synchronize.Barrier,
    results: multiprocessing.queues.Queue,
) -> None:
    try:
        payload = consume_alias(
            alias_path=Path(alias_path),
            authorization_path=Path(authorization_path),
            execution_correlation_id=correlation,
            consumed_at="2026-08-27T02:30:00.000000Z",
        )
        barrier.wait(timeout=10)
        _write_once_or_idempotent(canonical_consumption_path(Path(alias_path)), payload)
        results.put(("written", correlation))
    except Exception as error:
        results.put(("collision", correlation, type(error).__name__, str(error)))


class ScopedApprovalTimestampR017Tests(unittest.TestCase):
    def test_writer_and_issuer_share_canonical_six_digit_utc(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            runtime = root / "runtime" / "atlas"
            runtime.mkdir(parents=True)
            template = runtime / "r017-template.json"
            template.write_text(json.dumps({
                "schema": "atlas.operator-decision-request.v1",
                "packet": "FP-MAZER-MASTER-R017-SUPABASE-PREPARATION-20260825-001",
                "semantic_objective": "mazer_master_r017_protected_preparation_jit_approval_bound_invocation",
                "exact_authorization_phrase": "AUTHORIZE EXACT TEST",
                "execution_authority": False,
            }), encoding="utf-8")
            decision = canonicalize_decision_request(
                template_path=template,
                created_at="2026-08-27T02:00:00.1234567+00:00",
                expires_at="2026-08-28T03:20:17.0085299+02:00",
            )
            self.assertEqual("2026-08-27T02:00:00.123456Z", decision["created_at"])
            self.assertEqual("2026-08-28T01:20:17.008529Z", decision["expires_at"])
            decision_path = runtime / "r017-operator-decision-request.json"
            decision_path.write_text(json.dumps(decision), encoding="utf-8")
            alias = issue_alias(
                decision_request_path=decision_path,
                originating_task_id="019fa791-8d17-7c83-9c61-3e3c687e9dd7",
                effect_class="supabase_protected_master_preparation",
                target="supabase:test",
                max_effect_count=20,
                issued_at="2026-08-27T02:00:00.1234567Z",
                expires_at="2026-08-28T01:20:17.0085299Z",
            )
            self.assertEqual("2026-08-27T02:00:00.123456Z", alias["issued_at"])
            self.assertEqual(decision["expires_at"], alias["expires_at"])

    def test_issuer_rejects_noncanonical_decision_and_different_expiry(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            runtime = root / "runtime" / "atlas"
            runtime.mkdir(parents=True)
            base = {
                "schema": "atlas.operator-decision-request.v1",
                "packet": "FP-MAZER-MASTER-R017-SUPABASE-PREPARATION-20260825-001",
                "semantic_objective": "mazer_master_r017_protected_preparation_jit_approval_bound_invocation",
                "exact_authorization_phrase": "AUTHORIZE EXACT TEST",
                "execution_authority": False,
                "expires_at": "2026-08-28T01:20:17.0085299Z",
            }
            decision_path = runtime / "r017-operator-decision-request.json"
            decision_path.write_text(json.dumps(base), encoding="utf-8")
            kwargs = dict(
                decision_request_path=decision_path,
                originating_task_id="019fa791-8d17-7c83-9c61-3e3c687e9dd7",
                effect_class="supabase_protected_master_preparation",
                target="supabase:test",
                max_effect_count=20,
                issued_at="2026-08-27T02:00:00.000000Z",
                expires_at="2026-08-28T01:20:17.008529Z",
            )
            with self.assertRaisesRegex(ScopedApprovalError, "canonical six-digit UTC"):
                issue_alias(**kwargs)
            base["expires_at"] = "2026-08-28T01:20:17.008529Z"
            decision_path.write_text(json.dumps(base), encoding="utf-8")
            kwargs["expires_at"] = "2026-08-28T01:20:17.009529Z"
            with self.assertRaisesRegex(ScopedApprovalError, "expiry must match"):
                issue_alias(**kwargs)

    def test_concurrent_consumers_have_one_durable_winner_without_overwrite(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            runtime = root / "runtime" / "atlas"
            runtime.mkdir(parents=True)
            decision_path = runtime / "r017-operator-decision-request.json"
            decision_path.write_text(json.dumps({
                "schema": "atlas.operator-decision-request.v1",
                "packet": "FP-MAZER-MASTER-R017-SUPABASE-PREPARATION-20260825-001",
                "semantic_objective": "mazer_master_r017_protected_preparation_jit_approval_bound_invocation",
                "exact_authorization_phrase": "AUTHORIZE EXACT TEST",
                "execution_authority": False,
                "expires_at": "2026-08-28T01:20:17.008529Z",
            }), encoding="utf-8")
            alias_path = canonical_alias_path(decision_path)
            alias = issue_alias(
                decision_request_path=decision_path,
                originating_task_id="019fa791-8d17-7c83-9c61-3e3c687e9dd7",
                effect_class="supabase_protected_master_preparation",
                target="supabase:test",
                max_effect_count=20,
                issued_at="2026-08-27T02:00:00.000000Z",
                expires_at="2026-08-28T01:20:17.008529Z",
            )
            _write_once_or_idempotent(alias_path, alias)
            authorization_path = canonical_authorization_path(alias_path)
            authorization = authorize_alias(
                alias_path=alias_path,
                operator_response=alias["expected_operator_response"],
                originating_task_id="019fa791-8d17-7c83-9c61-3e3c687e9dd7",
                authorized_at="2026-08-27T02:10:00.000000Z",
            )
            _write_once_or_idempotent(authorization_path, authorization)

            context = multiprocessing.get_context("spawn")
            barrier = context.Barrier(2)
            results = context.Queue()
            correlations = [
                "11111111-1111-4111-8111-111111111111",
                "22222222-2222-4222-8222-222222222222",
            ]
            processes = [context.Process(
                target=_consume_race_worker,
                args=(str(alias_path), str(authorization_path), correlation, barrier, results),
            ) for correlation in correlations]
            for process in processes:
                process.start()
            for process in processes:
                process.join(timeout=15)
                self.assertFalse(process.is_alive(), "consumer process hung")
                self.assertEqual(0, process.exitcode)

            outcomes = [results.get(timeout=5), results.get(timeout=5)]
            self.assertEqual(1, sum(outcome[0] == "written" for outcome in outcomes))
            self.assertEqual(1, sum(outcome[0] == "collision" for outcome in outcomes))
            collision = next(outcome for outcome in outcomes if outcome[0] == "collision")
            self.assertEqual("ScopedApprovalError", collision[2])
            self.assertIn("Output identity collision", collision[3])
            durable = json.loads(canonical_consumption_path(alias_path).read_text(encoding="utf-8"))
            winner = next(outcome[1] for outcome in outcomes if outcome[0] == "written")
            self.assertEqual(winner, durable["execution_correlation_id"])
            self.assertEqual(1, len(list(runtime.glob("*-consumption.json"))))

    def test_isolated_issuer_uses_canonical_runtime_reference_and_rejects_absolute_fallback(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            runtime = root / "canonical" / "runtime" / "atlas"
            runtime.mkdir(parents=True)
            isolated_script = root / "isolated-worktree" / "ops" / "atlas" / "scoped_approval_alias.py"
            isolated_script.parent.mkdir(parents=True)
            shutil.copy2(Path(__file__).parents[1] / "scoped_approval_alias.py", isolated_script)
            decision_path = runtime / "r017-isolated-operator-decision-request.json"
            decision_path.write_text(json.dumps({
                "schema": "atlas.operator-decision-request.v1",
                "packet": "FP-MAZER-MASTER-R017-SUPABASE-PREPARATION-20260825-001",
                "semantic_objective": "mazer_master_r017_protected_preparation_jit_approval_bound_invocation",
                "exact_authorization_phrase": "AUTHORIZE EXACT ISOLATED TEST",
                "execution_authority": False,
                "expires_at": "2026-08-28T01:20:17.008529Z",
            }), encoding="utf-8")
            alias_path = canonical_alias_path(decision_path)
            issue = subprocess.run([
                sys.executable, str(isolated_script), "issue",
                "--decision-request", str(decision_path),
                "--originating-task-id", "019fa791-8d17-7c83-9c61-3e3c687e9dd7",
                "--effect-class", "supabase_protected_master_preparation",
                "--target", "supabase:test", "--max-effect-count", "20",
                "--issued-at", "2026-08-27T02:00:00.000000Z",
                "--expires-at", "2026-08-28T01:20:17.008529Z",
                "--output", str(alias_path),
            ], text=True, capture_output=True, check=False)
            self.assertEqual(0, issue.returncode, issue.stderr)
            alias = json.loads(alias_path.read_text(encoding="utf-8"))
            self.assertEqual(f"runtime/atlas/{decision_path.name}", alias["decision_request"]["path"])
            self.assertFalse(Path(alias["decision_request"]["path"]).is_absolute())

            authorization_path = canonical_authorization_path(alias_path)
            authorize = subprocess.run([
                sys.executable, str(isolated_script), "authorize",
                "--alias", str(alias_path), "--response", alias["expected_operator_response"],
                "--originating-task-id", "019fa791-8d17-7c83-9c61-3e3c687e9dd7",
                "--authorized-at", "2026-08-27T02:10:00.000000Z",
                "--output", str(authorization_path),
            ], text=True, capture_output=True, check=False)
            self.assertEqual(0, authorize.returncode, authorize.stderr)
            authorization = json.loads(authorization_path.read_text(encoding="utf-8"))
            self.assertEqual(f"runtime/atlas/{alias_path.name}", authorization["alias"]["path"])

            alias["decision_request"]["path"] = str(decision_path.resolve())
            alias_path.write_text(json.dumps(alias), encoding="utf-8")
            with self.assertRaisesRegex(ScopedApprovalError, "canonical runtime/atlas relative"):
                authorize_alias(
                    alias_path=alias_path,
                    operator_response=alias["expected_operator_response"],
                    originating_task_id="019fa791-8d17-7c83-9c61-3e3c687e9dd7",
                    authorized_at="2026-08-27T02:10:00.000000Z",
                )


if __name__ == "__main__":
    unittest.main()
