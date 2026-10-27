"""Synthetic-only tests for the uninstalled host-bound archive-key bridge.

No test reads the protected vault, calls a provider, or creates a real recovery
code. Each fixture lives in a disposable system-temp directory.
"""

from __future__ import annotations

import base64
import hashlib
import json
import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[1] / "export_supabase_master_recovery_key_live_bridge_r003.ps1"
PWSH = shutil.which("pwsh")
PROJECT = "testprojectref123456"
ARCHIVE_SHA = hashlib.sha256(b"synthetic archive fixture").hexdigest()
DESCRIPTOR_SHA = hashlib.sha256(b"synthetic descriptor fixture").hexdigest()
ATTEMPT = "attempt-001"


class SyntheticCapsuleTests(unittest.TestCase):
    def setUp(self) -> None:
        if not PWSH:
            self.skipTest("PowerShell 7 is unavailable")
        self.fixture = tempfile.TemporaryDirectory(prefix="atlas-key-capsule-")
        self.addCleanup(self.fixture.cleanup)
        self.root = Path(self.fixture.name)
        self.key = bytes(range(32))
        self.code = bytes(range(32, 64))
        (self.root / "synthetic-fixture.marker.json").write_text(
            json.dumps({"schema": "atlas.synthetic-key-capsule-fixture.v1", "synthetic_only": True}),
            encoding="utf-8",
        )

    @property
    def capsule(self) -> Path:
        return self.root / "capsules" / f"{ATTEMPT}.capsule.json"

    @property
    def host_marker(self) -> Path:
        return self.root / "capsules" / f"{ATTEMPT}.attempt.json"

    def invoke(
        self,
        action: str,
        *,
        attempt: str = ATTEMPT,
        archive_sha: str = ARCHIVE_SHA,
        wrong_code: bool = False,
        wrong_key: bool = False,
        tamper_core_context: bool = False,
        fixture_root: Path | None = None,
    ) -> subprocess.CompletedProcess[str]:
        command = [
                PWSH,
                "-NoProfile",
                "-File",
                str(SCRIPT),
                "-Action",
                action,
                "-FixtureRoot",
                str(fixture_root or self.root),
                "-AttemptId",
                attempt,
                "-ProjectRef",
                PROJECT,
                "-DescriptorSha256",
                DESCRIPTOR_SHA,
                "-ArchiveSha256",
                archive_sha,
            ]
        if wrong_code:
            command.append("-WrongCode")
        if wrong_key:
            command.append("-WrongKey")
        if tamper_core_context:
            command.append("-TamperCoreContext")
        return subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=30,
            check=False,
        )

    def seal(self) -> dict[str, object]:
        run = self.invoke("SealSynthetic")
        self.assertEqual(run.returncode, 0, run.stderr)
        return json.loads(run.stdout)

    def powershell(self, script: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [PWSH, "-NoProfile", "-Command", script],
            capture_output=True,
            text=True,
            timeout=30,
            check=False,
        )

    @staticmethod
    def ps_path(path: Path) -> str:
        return "'" + str(path).replace("'", "''") + "'"

    def handoff_fixture(self, display_body: str, *, drift: bool = False, padding: int = 0) -> Path:
        """Substitute only a public-vector display in an isolated source fixture."""
        helper_path = SCRIPT.with_name("private_recovery_code_handoff_r001.ps1")
        helper = helper_path.read_bytes()
        source = SCRIPT.read_text(encoding="utf-8")
        pinned = hashlib.sha256(helper).hexdigest()
        self.assertEqual(source.count(pinned), 1)
        mock = (
            "\nfunction Show-PrivateRecoveryCodeDialog {\n"
            "param([byte[]]$Code,[switch]$Interactive)\n"
            "$expected=[byte[]](0..31)\n"
            "if (-not [System.Security.Cryptography.CryptographicOperations]::FixedTimeEquals($expected,$Code)) "
            "{ throw 'TEST_PUBLIC_VECTOR_ONLY' }\n"
            + display_body + "\n}\n"
        ).encode("utf-8")
        fixture_helper = helper + mock + (b"\n#" + b"x" * padding if padding else b"")
        if not drift:
            source = source.replace(pinned, hashlib.sha256(fixture_helper).hexdigest())
        folder = Path(tempfile.mkdtemp(prefix="handoff-source-", dir=self.root)) / "ops" / "atlas"
        folder.mkdir(parents=True)
        bridge = folder / SCRIPT.name
        bridge.write_text(source, encoding="utf-8")
        (folder / helper_path.name).write_bytes(fixture_helper)
        return bridge

    def invoke_handoff_fixture(self, bridge: Path, *, interactive: bool = True) -> subprocess.CompletedProcess[str]:
        # Load definitions through an existing fixed-vector/no-vault action.
        load = (
            f"$null = . {self.ps_path(bridge)} -Action VerifyHostCoreSynthetic "
            f"-FixtureRoot {self.ps_path(self.root)} -AttemptId '{ATTEMPT}' "
            f"-ProjectRef '{PROJECT}' -DescriptorSha256 '{DESCRIPTOR_SHA}' "
            f"-ArchiveSha256 '{ARCHIVE_SHA}'; "
        )
        opt_in = " -Interactive" if interactive else ""
        return self.powershell(
            load + "$ErrorActionPreference='Stop'; try { "
            f"Confirm-OfflineCodeHandoff -Code ([byte[]](0..31)){opt_in}; 'CONFIRMED' "
            "} catch { $_.Exception.Message; exit 7 }"
        )

    def test_integrated_handoff_confirmation_emits_no_material(self) -> None:
        result = self.invoke_handoff_fixture(self.handoff_fixture("return $true"))
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout.strip(), "CONFIRMED")
        self.assertFalse(self.capsule.exists())
        self.assertFalse(self.host_marker.exists())

    def test_integrated_handoff_cancel_or_affinity_fault_stops_before_capsule(self) -> None:
        for body, reason in (
            ("return $false", "PRIVATE_USER_ONLY_HANDOFF_NOT_CONFIRMED"),
            ("throw 'CAPTURE_AFFINITY_REJECTED'", "CAPTURE_AFFINITY_REJECTED"),
            ("$true; 'unexpected pipeline output'", "PRIVATE_USER_ONLY_HANDOFF_NOT_CONFIRMED"),
        ):
            with self.subTest(reason=reason):
                # Each variant has its own isolated fixture directory.
                result = self.invoke_handoff_fixture(self.handoff_fixture(body))
                self.assertEqual(result.returncode, 7, result.stderr)
                self.assertEqual(result.stdout.strip(), reason)
                self.assertFalse(self.capsule.exists())
                self.assertFalse(self.host_marker.exists())

    def test_integrated_handoff_requires_opt_in_before_display(self) -> None:
        result = self.invoke_handoff_fixture(
            self.handoff_fixture("throw 'TEST_DISPLAY_MUST_NOT_RUN'"), interactive=False,
        )
        self.assertEqual(result.returncode, 7, result.stderr)
        self.assertEqual(result.stdout.strip(), "PRIVATE_HANDOFF_INTERACTIVE_OPT_IN_REQUIRED")

    def test_integrated_handoff_rejects_companion_source_drift_before_ui(self) -> None:
        result = self.invoke_handoff_fixture(
            self.handoff_fixture("throw 'TEST_DISPLAY_MUST_NOT_RUN'", drift=True),
        )
        self.assertEqual(result.returncode, 7, result.stderr)
        self.assertEqual(result.stdout.strip(), "PRIVATE_HANDOFF_SOURCE_IDENTITY_REJECTED")
        self.assertFalse(self.capsule.exists())

    def test_integrated_handoff_rejects_oversized_companion_before_read_or_ui(self) -> None:
        result = self.invoke_handoff_fixture(
            self.handoff_fixture("throw 'TEST_DISPLAY_MUST_NOT_RUN'", padding=65536),
        )
        self.assertEqual(result.returncode, 7, result.stderr)
        self.assertEqual(result.stdout.strip(), "PRIVATE_HANDOFF_SOURCE_IDENTITY_REJECTED")
        self.assertFalse(self.capsule.exists())

    def test_seal_and_verify_use_authenticated_synthetic_context(self) -> None:
        sealed = self.seal()
        self.assertEqual(sealed["result"], "SYNTHETIC_CAPSULE_SEALED")
        self.assertEqual(sealed["capsule_sha256"], hashlib.sha256(self.capsule.read_bytes()).hexdigest())
        capsule = json.loads(self.capsule.read_text(encoding="utf-8"))
        self.assertEqual(capsule["context"]["archive_sha256"], ARCHIVE_SHA)
        self.assertEqual(capsule["context"]["descriptor_sha256"], DESCRIPTOR_SHA)
        self.assertEqual(capsule["context"]["attempt_id"], ATTEMPT)
        self.assertEqual(len(base64.b64decode(capsule["nonce_b64"])), 12)
        self.assertEqual(len(base64.b64decode(capsule["tag_b64"])), 16)
        self.assertEqual(len(base64.b64decode(capsule["wrapped_key_b64"])), 32)
        verified = self.invoke("VerifySynthetic")
        self.assertEqual(verified.returncode, 0, verified.stderr)
        self.assertEqual(json.loads(verified.stdout)["result"], "SYNTHETIC_CAPSULE_VERIFIED")

    def test_host_core_uses_authenticated_synthetic_vectors(self) -> None:
        checked = self.invoke("VerifyHostCoreSynthetic")
        self.assertEqual(checked.returncode, 0, checked.stderr)
        result = json.loads(checked.stdout)
        self.assertEqual(result["result"], "SYNTHETIC_HOST_CORE_VERIFIED")
        self.assertFalse(result["secret_emitted"])
        self.assertFalse(result["live_effect"])
        self.assertFalse(self.capsule.exists())

    def test_host_core_rejects_mutated_serialized_context(self) -> None:
        checked = self.invoke("VerifyHostCoreSynthetic", tamper_core_context=True)
        self.assertNotEqual(checked.returncode, 0)
        self.assertIn("authentication", checked.stderr.lower())
        self.assertFalse(self.capsule.exists())

    def test_host_persistence_uses_create_new_marker_and_capsule(self) -> None:
        checked = self.invoke("VerifyHostPersistenceSynthetic")
        self.assertEqual(checked.returncode, 0, checked.stderr)
        result = json.loads(checked.stdout)
        self.assertEqual(result["result"], "SYNTHETIC_HOST_PERSISTENCE_VERIFIED")
        self.assertEqual(result["marker_sha256"], hashlib.sha256(self.host_marker.read_bytes()).hexdigest())
        self.assertEqual(result["capsule_sha256"], hashlib.sha256(self.capsule.read_bytes()).hexdigest())
        self.assertTrue(result["marker_file_acl_verified"])
        self.assertTrue(result["capsule_file_acl_verified"])
        observed = checked.stdout + self.host_marker.read_text() + self.capsule.read_text()
        for value in (self.key, self.code):
            self.assertNotIn(value.hex(), observed)
            self.assertNotIn(base64.b64encode(value).decode("ascii"), observed)
        self.capsule.unlink()
        duplicate = self.invoke("VerifyHostPersistenceSynthetic")
        self.assertNotEqual(duplicate.returncode, 0)
        self.assertIn("Live attempt already exists", duplicate.stderr)
        self.assertFalse(self.capsule.exists())

    def test_path_guard_rejects_directory_swap_and_closed_file_replacement(self) -> None:
        checked = self.invoke("VerifyPathIdentitySynthetic")
        self.assertEqual(checked.returncode, 0, checked.stderr)
        result = json.loads(checked.stdout)
        self.assertEqual(result["result"], "SYNTHETIC_PATH_IDENTITY_VERIFIED")
        self.assertTrue(result["directory_swap_blocked_or_detected"])
        self.assertTrue(result["closed_file_replacement_rejected"])
        self.assertTrue(result["same_file_tamper_rejected"])
        self.assertTrue(result["pinned_file_swap_blocked_or_detected"])
        self.assertFalse(result["secret_emitted"])
        self.assertFalse(result["live_effect"])
        for value in (self.key, self.code):
            self.assertNotIn(value.hex(), checked.stdout + checked.stderr)
            self.assertNotIn(base64.b64encode(value).decode("ascii"), checked.stdout + checked.stderr)
        self.assertFalse(self.host_marker.exists())
        self.assertFalse(self.capsule.exists())

    def test_created_files_have_protected_owner_acl_on_independent_readback(self) -> None:
        created = self.invoke("VerifyHostPersistenceSynthetic")
        self.assertEqual(created.returncode, 0, created.stderr)
        verified = self.invoke("VerifyFileAclSynthetic")
        self.assertEqual(verified.returncode, 0, verified.stderr)
        self.assertEqual(json.loads(verified.stdout)["result"], "SYNTHETIC_FILE_ACL_VERIFIED")
        for path in (self.host_marker, self.capsule):
            readback = self.powershell(
                f"$acl=Get-Acl -LiteralPath {self.ps_path(path)}; "
                "$sid=[System.Security.Principal.WindowsIdentity]::GetCurrent().User.Value; "
                "$rules=@($acl.GetAccessRules($true,$true,"
                "[System.Security.Principal.SecurityIdentifier])); "
                "[ordered]@{owner_matches=($acl.GetOwner("
                "[System.Security.Principal.SecurityIdentifier]).Value -ceq $sid); "
                "protected=$acl.AreAccessRulesProtected; "
                "rules=@($rules | ForEach-Object { $_.IdentityReference.Value })} "
                "| ConvertTo-Json -Compress -Depth 4"
            )
            self.assertEqual(readback.returncode, 0, readback.stderr)
            acl = json.loads(readback.stdout)
            self.assertTrue(acl["owner_matches"])
            self.assertTrue(acl["protected"])
            self.assertGreaterEqual(len(acl["rules"]), 1)

    def test_foreign_file_principal_is_rejected_without_replacement(self) -> None:
        created = self.invoke("VerifyHostPersistenceSynthetic")
        self.assertEqual(created.returncode, 0, created.stderr)
        preimage = self.capsule.read_bytes()
        changed = self.powershell(
            f"$file=[System.IO.FileInfo]::new({self.ps_path(self.capsule)}); "
            "$acl=[System.IO.FileSystemAclExtensions]::GetAccessControl("
            "$file,[System.Security.AccessControl.AccessControlSections]::Access); "
            "$everyone=[System.Security.Principal.SecurityIdentifier]::new('S-1-1-0'); "
            "$rule=[System.Security.AccessControl.FileSystemAccessRule]::new("
            "$everyone,[System.Security.AccessControl.FileSystemRights]::ReadData,"
            "[System.Security.AccessControl.AccessControlType]::Allow); "
            "$acl.AddAccessRule($rule); "
            "[System.IO.FileSystemAclExtensions]::SetAccessControl($file,$acl)"
        )
        self.assertEqual(changed.returncode, 0, changed.stderr)
        rejected = self.invoke("VerifyFileAclSynthetic")
        self.assertNotEqual(rejected.returncode, 0)
        self.assertIn("unexpected rule", rejected.stderr)
        self.assertEqual(self.capsule.read_bytes(), preimage)
        duplicate = self.invoke("VerifyHostPersistenceSynthetic")
        self.assertNotEqual(duplicate.returncode, 0)
        self.assertIn("Live attempt already exists", duplicate.stderr)

    def test_file_acl_inheritance_drift_is_rejected(self) -> None:
        created = self.invoke("VerifyHostPersistenceSynthetic")
        self.assertEqual(created.returncode, 0, created.stderr)
        changed = self.powershell(
            f"$file=[System.IO.FileInfo]::new({self.ps_path(self.host_marker)}); "
            "$acl=[System.IO.FileSystemAclExtensions]::GetAccessControl("
            "$file,[System.Security.AccessControl.AccessControlSections]::Access); "
            "$acl.SetAccessRuleProtection($false,$false); "
            "[System.IO.FileSystemAclExtensions]::SetAccessControl($file,$acl)"
        )
        self.assertEqual(changed.returncode, 0, changed.stderr)
        rejected = self.invoke("VerifyFileAclSynthetic")
        self.assertNotEqual(rejected.returncode, 0)
        self.assertIn("DACL protection drift", rejected.stderr)

    def test_missing_file_acl_readback_fails_closed(self) -> None:
        created = self.invoke("VerifyHostPersistenceSynthetic")
        self.assertEqual(created.returncode, 0, created.stderr)
        self.capsule.unlink()
        rejected = self.invoke("VerifyFileAclSynthetic")
        self.assertNotEqual(rejected.returncode, 0)
        self.assertFalse(self.capsule.exists())
        self.assertTrue(self.host_marker.exists())

    def test_live_action_refuses_before_vault_or_capsule_access(self) -> None:
        checked = self.invoke("SealLive", fixture_root=self.root / "missing-fixture")
        self.assertNotEqual(checked.returncode, 0)
        self.assertIn("LIVE_ACTION_NOT_ADMITTED_PRIVATE_HANDOFF_NOT_INSTALLED", checked.stderr)
        self.assertFalse(self.capsule.exists())

    def test_wrong_code_rejects_without_emitting_material(self) -> None:
        self.seal()
        verified = self.invoke("VerifySynthetic", wrong_code=True)
        self.assertNotEqual(verified.returncode, 0)
        self.assertIn("Capsule authentication failed", verified.stderr)
        self.assertNotIn(self.key.hex(), verified.stdout + verified.stderr)
        self.assertNotIn(self.code.hex(), verified.stdout + verified.stderr)

    def test_authenticated_wrong_key_is_rejected(self) -> None:
        sealed = self.invoke("SealSynthetic", wrong_key=True)
        self.assertEqual(sealed.returncode, 0, sealed.stderr)
        verified = self.invoke("VerifySynthetic")
        self.assertNotEqual(verified.returncode, 0)
        self.assertIn("Synthetic key mismatch", verified.stderr)

    def test_marker_named_external_bytes_cannot_supply_key_or_code(self) -> None:
        (self.root / "synthetic-archive-key.bin").write_bytes(bytes(range(96, 128)))
        (self.root / "synthetic-recovery-code.bin").write_bytes(bytes(range(64, 96)))
        self.seal()
        verified = self.invoke("VerifySynthetic")
        self.assertEqual(verified.returncode, 0, verified.stderr)

    def test_altered_associated_data_rejects(self) -> None:
        self.seal()
        changed = self.invoke("VerifySynthetic", archive_sha=hashlib.sha256(b"other archive").hexdigest())
        self.assertNotEqual(changed.returncode, 0)
        self.assertIn("Capsule context mismatch", changed.stderr)
        capsule = json.loads(self.capsule.read_text(encoding="utf-8"))
        capsule["context"]["archive_sha256"] = hashlib.sha256(b"other archive").hexdigest()
        self.capsule.write_text(json.dumps(capsule), encoding="utf-8")
        tampered = self.invoke("VerifySynthetic", archive_sha=capsule["context"]["archive_sha256"])
        self.assertNotEqual(tampered.returncode, 0)
        self.assertIn("Capsule authentication failed", tampered.stderr)

    def test_duplicate_attempt_does_not_replace_capsule(self) -> None:
        self.seal()
        preimage = self.capsule.read_bytes()
        duplicate = self.invoke("SealSynthetic")
        self.assertNotEqual(duplicate.returncode, 0)
        self.assertIn("Duplicate synthetic attempt", duplicate.stderr)
        self.assertEqual(self.capsule.read_bytes(), preimage)

    def test_path_escape_attempt_is_rejected(self) -> None:
        run = self.invoke("SealSynthetic", attempt="../escape")
        self.assertNotEqual(run.returncode, 0)
        self.assertIn("Unsafe synthetic attempt ID", run.stderr)
        self.assertFalse((self.root.parent / "escape.capsule.json").exists())

    def test_intermediate_directory_link_is_rejected(self) -> None:
        target = self.root / "target"
        fixture = target / "fixture"
        fixture.mkdir(parents=True)
        shutil.copy2(self.root / "synthetic-fixture.marker.json", fixture)
        link = self.root / "link"
        try:
            os.symlink(target, link, target_is_directory=True)
        except OSError as error:
            self.skipTest(f"directory link unavailable: {error}")
        run = self.invoke("SealSynthetic", fixture_root=link / "fixture")
        self.assertNotEqual(run.returncode, 0)
        self.assertIn("reparse point", run.stderr)
        self.assertFalse((fixture / "capsules" / f"{ATTEMPT}.capsule.json").exists())

    def test_invalid_fixture_leaves_no_capsule(self) -> None:
        (self.root / "synthetic-fixture.marker.json").write_text(
            json.dumps({"schema": "atlas.synthetic-key-capsule-fixture.v1", "synthetic_only": False}),
            encoding="utf-8",
        )
        run = self.invoke("SealSynthetic")
        self.assertNotEqual(run.returncode, 0)
        self.assertFalse(self.capsule.exists())

    def test_stdout_and_capsule_do_not_contain_key_or_code(self) -> None:
        sealed = self.invoke("SealSynthetic")
        self.assertEqual(sealed.returncode, 0, sealed.stderr)
        observed = sealed.stdout + sealed.stderr + self.capsule.read_text(encoding="utf-8")
        for value in (self.key, self.code):
            self.assertNotIn(value.hex(), observed)
            self.assertNotIn(base64.b64encode(value).decode("ascii"), observed)
        self.assertFalse(json.loads(sealed.stdout)["secret_emitted"])
        self.assertFalse(json.loads(sealed.stdout)["live_effect"])


if __name__ == "__main__":
    unittest.main()
