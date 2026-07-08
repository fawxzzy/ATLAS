from __future__ import annotations

import io
import json
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import patch

from ops.atlas import held_lane_prompt_suppression as suppression


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _selector_payload(*, action: str = "no_immediate_root_packet", next_packet: str | None = None) -> dict[str, object]:
    return {
        "operator_action": action,
        "selected_current_packet": None,
        "next_after_current_packet": next_packet,
    }


def _planner_payload(*, status: str = "advisory_recommendation", selected_packet: str | None = None, candidate_packet: str | None = None) -> dict[str, object]:
    return {
        "status": status,
        "selected_packet": selected_packet,
        "candidate_scores": [
            {
                "marker": "AI Repetition-to-Automation Pipeline",
                "classification": "held_lane",
                "packet": candidate_packet or selected_packet or "No immediate root packet",
                "reason": "fixture",
                "safe_to_select": selected_packet is not None,
            }
        ],
    }


def _closeout_payload(*, root_clean: bool = True, critical: int = 0, error: int = 0, owner_fallback_forbidden: bool = True) -> dict[str, object]:
    return {
        "root_clean": root_clean,
        "validation_state": {"critical": critical, "error": error, "warning": 0, "info": 0},
        "owner_lane_fallback_forbidden": owner_fallback_forbidden,
    }


class HeldLanePromptSuppressionTests(unittest.TestCase):
    def _temp_root(self) -> Path:
        temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(temp_dir.cleanup)
        return Path(temp_dir.name)

    def _write_artifacts(
        self,
        root: Path,
        *,
        selector: dict[str, object] | str | None = None,
        planner: dict[str, object] | str | None = None,
        closeout: dict[str, object] | str | None = None,
    ) -> tuple[str, str, str]:
        values = {
            "selector": selector if selector is not None else _selector_payload(),
            "planner": planner if planner is not None else _planner_payload(),
            "closeout": closeout if closeout is not None else _closeout_payload(),
        }
        refs: list[str] = []
        for name, payload in values.items():
            relative = Path("tmp") / "held-lane-suppression" / f"{name}.json"
            text = payload if isinstance(payload, str) else json.dumps(payload, indent=2) + "\n"
            _write(root / relative, text)
            refs.append(suppression.normalize_slashes(str(relative)))
        return tuple(refs)  # type: ignore[return-value]

    def _run_main(self, root: Path, args: list[str]) -> tuple[int, dict[str, object]]:
        with patch.object(suppression, "atlas_root", return_value=root):
            stdout = io.StringIO()
            with redirect_stdout(stdout):
                code = suppression.main(args)
        return code, json.loads(stdout.getvalue())

    def test_suppresses_clean_held_root_state_without_exact_packet(self) -> None:
        report = suppression.build_report(
            selector_report=_selector_payload(),
            planner_report=_planner_payload(),
            closeout_report=_closeout_payload(),
        )

        self.assertEqual(suppression.STATUS_SUPPRESS, report["status"])
        self.assertEqual(suppression.DECISION_SUPPRESS_CONTINUATION, report["decision"])
        self.assertFalse(report["safe_to_continue"])
        self.assertFalse(report["exact_packet_available"])

    def test_allows_exact_packet_from_planner(self) -> None:
        report = suppression.build_report(
            selector_report=_selector_payload(),
            planner_report=_planner_payload(selected_packet="AI Repetition exact bounded packet"),
            closeout_report=_closeout_payload(),
        )

        self.assertEqual(suppression.STATUS_ALLOW, report["status"])
        self.assertEqual(suppression.DECISION_ALLOW_EXACT_PACKET, report["decision"])
        self.assertTrue(report["exact_packet_available"])

    def test_allows_operator_selected_packet(self) -> None:
        report = suppression.build_report(
            selector_report=_selector_payload(),
            planner_report=_planner_payload(),
            closeout_report=_closeout_payload(),
            operator_selected_packet="AI Repetition selected root packet",
        )

        self.assertEqual(suppression.STATUS_ALLOW, report["status"])
        self.assertEqual(suppression.DECISION_ALLOW_OPERATOR_SELECTED_PACKET, report["decision"])
        self.assertEqual("AI Repetition selected root packet", report["operator_selected_packet"])

    def test_validation_or_dirty_root_allows_cleanup(self) -> None:
        report = suppression.build_report(
            selector_report=_selector_payload(),
            planner_report=_planner_payload(),
            closeout_report=_closeout_payload(root_clean=False, critical=0, error=1),
        )

        self.assertEqual(suppression.STATUS_ALLOW, report["status"])
        self.assertEqual(suppression.DECISION_ALLOW_VALIDATION_CLEANUP, report["decision"])
        self.assertEqual(1, report["validation_state"]["error"])

    def test_worker_and_reconciliation_packets_are_not_suppressed(self) -> None:
        report = suppression.build_report(
            selector_report=_selector_payload(),
            planner_report=_planner_payload(selected_packet="AI Repetition held-lane prompt suppression worker packet 1"),
            closeout_report=_closeout_payload(),
        )

        self.assertEqual(suppression.STATUS_ALLOW, report["status"])
        self.assertEqual(suppression.DECISION_ALLOW_WORKER_RECONCILIATION, report["decision"])

    def test_owner_fallback_is_blocked_by_scope_lock(self) -> None:
        report = suppression.build_report(
            selector_report=_selector_payload(),
            planner_report=_planner_payload(selected_packet="Use owner lane fallback cleanup packet"),
            closeout_report=_closeout_payload(),
        )

        self.assertEqual(suppression.STATUS_BLOCKED, report["status"])
        self.assertEqual(suppression.DECISION_BLOCKED_BY_SCOPE_LOCK, report["decision"])

    def test_fitness_and_mazer_fallbacks_are_blocked(self) -> None:
        for packet in ("Fitness receipt cleanup fallback", "Mazer browser parity fallback"):
            report = suppression.build_report(
                selector_report=_selector_payload(),
                planner_report=_planner_payload(selected_packet=packet),
                closeout_report=_closeout_payload(),
            )
            self.assertEqual(suppression.STATUS_BLOCKED, report["status"])
            self.assertEqual(suppression.DECISION_BLOCKED_BY_OWNER_LANE_FALLBACK, report["decision"])

    def test_secret_deploy_and_protected_packets_are_blocked(self) -> None:
        for packet in ("rotate secret key", "deploy production", "edit .github/workflows/qa.yml"):
            report = suppression.build_report(
                selector_report=_selector_payload(),
                planner_report=_planner_payload(),
                closeout_report=_closeout_payload(),
                operator_selected_packet=packet,
            )
            self.assertEqual(suppression.STATUS_BLOCKED, report["status"])
            self.assertEqual(suppression.DECISION_BLOCKED_BY_SCOPE_LOCK, report["decision"])

    def test_stale_completed_packet_suppresses_rerun(self) -> None:
        report = suppression.build_report(
            selector_report=_selector_payload(),
            planner_report=_planner_payload(selected_packet="Already completed AI Repetition packet"),
            closeout_report=_closeout_payload(),
        )

        self.assertEqual(suppression.STATUS_SUPPRESS, report["status"])
        self.assertEqual(suppression.DECISION_SUPPRESS_CONTINUATION, report["decision"])

    def test_deterministic_top_level_json_order(self) -> None:
        report = suppression.build_report(
            selector_report=_selector_payload(),
            planner_report=_planner_payload(),
            closeout_report=_closeout_payload(),
        )

        self.assertEqual(suppression.OUTPUT_FIELDS, list(report.keys()))
        json.dumps(report, sort_keys=True)

    def test_strict_suppress_returns_nonzero(self) -> None:
        root = self._temp_root()
        selector_ref, planner_ref, closeout_ref = self._write_artifacts(root)

        code, payload = self._run_main(
            root,
            [
                "--json",
                "--strict",
                "--selector-output",
                selector_ref,
                "--planner-output",
                planner_ref,
                "--closeout-output",
                closeout_ref,
            ],
        )

        self.assertEqual(1, code)
        self.assertEqual(suppression.STATUS_SUPPRESS, payload["status"])

    def test_malformed_input_fails_closed(self) -> None:
        root = self._temp_root()
        selector_ref, planner_ref, closeout_ref = self._write_artifacts(root, planner="{not json")

        code, payload = self._run_main(
            root,
            [
                "--json",
                "--selector-output",
                selector_ref,
                "--planner-output",
                planner_ref,
                "--closeout-output",
                closeout_ref,
            ],
        )

        self.assertEqual(3, code)
        self.assertEqual(suppression.STATUS_INTERNAL_ERROR, payload["status"])
        self.assertIn("invalid_json_input", payload["suppression_reason"])

    def test_output_rejects_absolute_path(self) -> None:
        root = self._temp_root()
        selector_ref, planner_ref, closeout_ref = self._write_artifacts(root)
        output = root / "tmp" / "absolute.json"

        code, payload = self._run_main(
            root,
            [
                "--json",
                "--selector-output",
                selector_ref,
                "--planner-output",
                planner_ref,
                "--closeout-output",
                closeout_ref,
                "--output",
                str(output),
            ],
        )

        self.assertEqual(2, code)
        self.assertEqual(suppression.STATUS_BLOCKED, payload["status"])
        self.assertIn("absolute_output_path", payload["suppression_reason"])
        self.assertFalse(output.exists())

    def test_output_rejects_protected_path(self) -> None:
        root = self._temp_root()
        selector_ref, planner_ref, closeout_ref = self._write_artifacts(root)

        code, payload = self._run_main(
            root,
            [
                "--json",
                "--selector-output",
                selector_ref,
                "--planner-output",
                planner_ref,
                "--closeout-output",
                closeout_ref,
                "--output",
                "secrets/suppression.json",
            ],
        )

        self.assertEqual(2, code)
        self.assertEqual(suppression.STATUS_BLOCKED, payload["status"])
        self.assertIn("protected_output_path", payload["suppression_reason"])
        self.assertFalse((root / "secrets" / "suppression.json").exists())

    def test_safe_tmp_output_is_written(self) -> None:
        root = self._temp_root()
        selector_ref, planner_ref, closeout_ref = self._write_artifacts(root)
        output = root / "tmp" / "held-lane-suppression" / "report.json"

        code, payload = self._run_main(
            root,
            [
                "--json",
                "--selector-output",
                selector_ref,
                "--planner-output",
                planner_ref,
                "--closeout-output",
                closeout_ref,
                "--output",
                "tmp/held-lane-suppression/report.json",
            ],
        )

        self.assertEqual(0, code)
        self.assertTrue(output.exists())
        self.assertEqual(suppression.STATUS_SUPPRESS, payload["status"])
        self.assertEqual(payload, json.loads(output.read_text(encoding="utf-8")))


if __name__ == "__main__":
    unittest.main()
