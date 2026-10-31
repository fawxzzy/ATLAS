"""Synthetic-only contract tests; never construct or read a live recovery key."""

from pathlib import Path
import json
import subprocess
import unittest


SCRIPT = Path(__file__).resolve().parents[1] / "private_recovery_code_handoff_r001.ps1"
PUBLIC_CODE = "".join(f"{value:02X}" for value in range(32))


def run_ps(command: str) -> subprocess.CompletedProcess[str]:
    source = str(SCRIPT).replace("'", "''")
    return subprocess.run(
        ["pwsh", "-NoProfile", "-NonInteractive", "-Command", f". '{source}'; {command}"],
        capture_output=True, text=True, check=False, timeout=20,
    )


class PrivateHandoffSourceTests(unittest.TestCase):
    def test_public_fixed_vector_matches(self) -> None:
        result = run_ps(
            "$expected=[byte[]](0..31); "
            f"Test-OfflineRecoveryCodeEntry -Expected $expected -Entry '{PUBLIC_CODE}'"
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout.strip(), "True")

    def test_grouped_public_vector_matches(self) -> None:
        grouped = "-".join(PUBLIC_CODE[i:i + 8] for i in range(0, 64, 8))
        result = run_ps(
            "$expected=[byte[]](0..31); "
            f"Test-OfflineRecoveryCodeEntry -Expected $expected -Entry '{grouped}'"
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout.strip(), "True")

    def test_wrong_and_malformed_entry_reject_without_value(self) -> None:
        wrong = "FF" + PUBLIC_CODE[2:]
        for entry in (wrong, "bad", "", "G" * 64):
            with self.subTest(entry_kind="wrong" if len(entry) == 64 else "malformed"):
                result = run_ps(
                    "$expected=[byte[]](0..31); "
                    f"Test-OfflineRecoveryCodeEntry -Expected $expected -Entry '{entry}'"
                )
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertEqual(result.stdout.strip(), "False")
                self.assertNotIn(PUBLIC_CODE, result.stdout + result.stderr)

    def test_expected_shape_rejects(self) -> None:
        result = run_ps(
            f"Test-OfflineRecoveryCodeEntry -Expected ([byte[]](0..15)) -Entry '{PUBLIC_CODE}'"
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("EXPECTED_CODE_SHAPE_REJECTED", result.stderr)

    def test_private_entry_requires_explicit_interaction_before_material(self) -> None:
        result = run_ps("Invoke-PrivateRecoveryCodeHandoff")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("PRIVATE_HANDOFF_INTERACTIVE_OPT_IN_REQUIRED", result.stderr)

    def test_private_entry_rejects_wrong_shape_before_ui(self) -> None:
        result = run_ps("Invoke-PrivateRecoveryCodeHandoff -RecoveryCode ([byte[]](0..15)) -Interactive")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("RECOVERY_CODE_SHAPE_REJECTED", result.stderr)

    def test_private_handoff_clears_owned_copy_on_confirmation_or_cancel(self) -> None:
        for accepted in (True, False):
            with self.subTest(accepted=accepted):
                literal = "$true" if accepted else "$false"
                result = run_ps(
                    "function Show-PrivateRecoveryCodeDialog { param([byte[]]$Code,[switch]$Interactive); "
                    "$script:seen=$Code; "
                    f"return {literal} }}; "
                    "$caller=[byte[]](0..31); "
                    "$value=Invoke-PrivateRecoveryCodeHandoff -RecoveryCode $caller -Interactive; "
                    "[ordered]@{accepted=$value;owned_zeroed=(@($script:seen | Where-Object {$_ -ne 0}).Count -eq 0);"
                    f"caller_unchanged=([Convert]::ToHexString($caller) -ceq '{PUBLIC_CODE}')}} | ConvertTo-Json -Compress"
                )
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertEqual(json.loads(result.stdout), {
                    "accepted": accepted, "owned_zeroed": True, "caller_unchanged": True,
                })
                self.assertNotIn(PUBLIC_CODE, result.stdout + result.stderr)

    def test_display_affinity_fault_clears_owned_copy_without_echo(self) -> None:
        result = run_ps(
            "function Show-PrivateRecoveryCodeDialog { param([byte[]]$Code,[switch]$Interactive); "
            "$script:seen=$Code; throw 'CAPTURE_AFFINITY_REJECTED' }; "
            "$caller=[byte[]](0..31); "
            "try { Invoke-PrivateRecoveryCodeHandoff -RecoveryCode $caller -Interactive } "
            "catch { $reason=$_.Exception.Message }; "
            "[ordered]@{reason=$reason;owned_zeroed=(@($script:seen | Where-Object {$_ -ne 0}).Count -eq 0)} "
            "| ConvertTo-Json -Compress"
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout), {
            "reason": "CAPTURE_AFFINITY_REJECTED", "owned_zeroed": True,
        })
        self.assertNotIn(PUBLIC_CODE, result.stdout + result.stderr)

    def test_synthetic_gui_requires_explicit_interaction(self) -> None:
        result = run_ps("Invoke-SyntheticPrivateRecoveryCodeHandoff")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("SYNTHETIC_INTERACTION_EXPLICIT_OPT_IN_REQUIRED", result.stderr)

    def test_dialog_rejects_non_public_bytes_before_ui(self) -> None:
        result = run_ps(
            "Show-SyntheticPrivateRecoveryCodeDialog -SyntheticCode ([byte[]](1..32))"
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("NON_PUBLIC_SYNTHETIC_VECTOR_REJECTED", result.stderr)

    def test_capture_exclusion_host_version_gate(self) -> None:
        for major, build, expected in ((10, 18363, "False"),
                                       (10, 19041, "True"),
                                       (10, 22631, "True"),
                                       (6, 9600, "False")):
            with self.subTest(major=major, build=build):
                result = run_ps(
                    f"Test-PrivateHandoffHostVersion -Major {major} -Build {build}"
                )
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertEqual(result.stdout.strip(), expected)


if __name__ == "__main__":
    unittest.main()
