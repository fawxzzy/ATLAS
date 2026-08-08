from __future__ import annotations

import copy
import hashlib
import inspect
import json
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from ops.atlas.machine_stewardship import collectors, contracts, reporting
from ops.atlas.machine_stewardship.cli import build_parser

ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "tests" / "fixtures" / "atlas-machine-stewardship"


def _load(path: Path) -> dict:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise AssertionError(f"Fixture must contain an object: {path}")
    return payload


def _digest(prefix: str, character: str) -> str:
    return f"{prefix}_{character * 64}"


def _sha(character: str) -> str:
    return f"sha256:{character * 64}"


def _valid_documents() -> list[dict]:
    observed = _load(FIXTURES / "observed-state.v1.json")
    policy = _load(FIXTURES / "policy.v1.json")
    desired = {
        "contract_version": "atlas.machine-desired-state.v1",
        "desired_state_id": _digest("mdes", "1"),
        "target_machine_id": _sha("2"),
        "policy_id": policy["policy_id"],
        "created_at_utc": "2026-07-29T00:01:00Z",
        "maximum_authority_level": "L1",
        "controls": [
            {
                "control_id": "storage.fixed-local-observation",
                "category": "storage",
                "desired_condition": "Record redacted capacity metadata only.",
                "enforcement": "observe_only",
                "protected": True,
            }
        ],
    }
    proposal = {
        "contract_version": "atlas.machine-action-proposal.v1",
        "proposal_id": _digest("mapr", "3"),
        "target_machine_id": desired["target_machine_id"],
        "desired_state_id": desired["desired_state_id"],
        "policy_id": policy["policy_id"],
        "created_at_utc": "2026-07-29T00:02:00Z",
        "authority_level": "L2",
        "action_kind": "REPAIR",
        "status": "PROPOSED_ONLY",
        "execution_boundary": "LIFELINE_REQUIRED",
        "summary": "Propose a future deterministic local repair.",
        "rationale": "ATLAS describes intent; Lifeline must own execution.",
        "preconditions": ["Fresh observation", "Explicit operator admission"],
        "risk_flags": {
            "destructive": False,
            "elevation_required": False,
            "network_required": False,
            "protected_zone_impact": False,
        },
    }
    receipt = {
        "contract_version": "atlas.machine-execution-receipt.v1",
        "execution_receipt_id": _digest("mexr", "4"),
        "proposal_id": proposal["proposal_id"],
        "target_machine_id": proposal["target_machine_id"],
        "executor": "lifeline",
        "authority_level": "L2",
        "status": "REJECTED",
        "started_at_utc": None,
        "finished_at_utc": "2026-07-29T00:03:00Z",
        "result_digest": None,
        "mutation_summary": [],
        "errors": [
            {
                "code": "AUTHORITY_MISSING",
                "message": "No execution admission was present.",
                "recoverable": True,
            }
        ],
    }
    return [observed, desired, proposal, receipt, policy]


class ContractTests(unittest.TestCase):
    def test_all_five_schema_definitions_and_documents_validate(self) -> None:
        documents = _valid_documents()
        self.assertEqual(5, len(contracts.CONTRACT_SCHEMA_PATHS))
        for document in documents:
            with self.subTest(contract=document["contract_version"]):
                schema = contracts.load_schema(document["contract_version"])
                self.assertEqual(
                    "https://json-schema.org/draft/2020-12/schema",
                    schema["$schema"],
                )
                self.assertEqual([], contracts.validate_contract(document))

    def test_both_checked_in_fixtures_validate(self) -> None:
        for fixture in sorted(FIXTURES.glob("*.json")):
            with self.subTest(fixture=fixture.name):
                self.assertEqual([], contracts.validate_contract(_load(fixture)))

    def test_contract_version_is_fail_closed(self) -> None:
        payload = _valid_documents()[0]
        payload["contract_version"] = "atlas.machine-observed-state.v999"
        errors = contracts.validate_contract(payload)
        self.assertEqual(1, len(errors))
        self.assertIn("Unsupported machine contract version", errors[0])

    def test_observed_privacy_flags_cannot_be_relaxed(self) -> None:
        payload = _valid_documents()[0]
        payload["privacy"]["file_contents_read"] = True
        errors = contracts.validate_contract(payload)
        self.assertTrue(any("file_contents_read" in error for error in errors))

    def test_action_proposal_cannot_claim_execution(self) -> None:
        payload = _valid_documents()[2]
        payload["status"] = "SUCCEEDED"
        errors = contracts.validate_contract(payload)
        self.assertTrue(any("PROPOSED_ONLY" in error for error in errors))

    def test_execution_receipt_is_lifeline_owned(self) -> None:
        payload = _valid_documents()[3]
        payload["executor"] = "atlas"
        errors = contracts.validate_contract(payload)
        self.assertTrue(any("lifeline" in error for error in errors))

    def test_policy_requires_each_authority_level_exactly_once(self) -> None:
        payload = _valid_documents()[4]
        del payload["authority_levels"]["L4"]
        errors = contracts.validate_contract(payload)
        self.assertTrue(any("L4" in error for error in errors))

    def test_canonical_json_is_sorted_compact_and_array_stable(self) -> None:
        left = {"z": [2, 1], "a": {"y": 2, "x": 1}}
        right = {"a": {"x": 1, "y": 2}, "z": [2, 1]}
        expected = b'{"a":{"x":1,"y":2},"z":[2,1]}'
        self.assertEqual(expected, contracts.canonical_json_bytes(left))
        self.assertEqual(expected, contracts.canonical_json_bytes(right))
        self.assertEqual(contracts.canonical_sha256(left), contracts.canonical_sha256(right))

    def test_normalization_removes_only_explicit_volatile_fields(self) -> None:
        first = _valid_documents()[0]
        second = copy.deepcopy(first)
        second["observation_id"] = _digest("mobs", "9")
        second["collected_at_utc"] = "2026-07-29T00:09:00Z"
        self.assertNotEqual(
            contracts.canonical_json_bytes(first),
            contracts.canonical_json_bytes(second),
        )
        self.assertEqual(
            contracts.canonical_json_bytes(contracts.normalize_nonvolatile(first)),
            contracts.canonical_json_bytes(contracts.normalize_nonvolatile(second)),
        )


class CollectorTests(unittest.TestCase):
    def test_command_runner_uses_explicit_array_timeout_and_no_shell(self) -> None:
        received: dict = {}

        def fake_runner(args, **kwargs):
            received["args"] = args
            received["kwargs"] = kwargs
            return subprocess.CompletedProcess(args, 0, "ok", "")

        result = collectors.run_command(
            ["tool.exe", "--metadata-only"],
            timeout_seconds=3.0,
            runner=fake_runner,
        )
        self.assertEqual(0, result.exit_code)
        self.assertEqual(["tool.exe", "--metadata-only"], received["args"])
        self.assertEqual(3.0, received["kwargs"]["timeout"])
        self.assertIs(False, received["kwargs"]["shell"])
        self.assertIs(True, received["kwargs"]["capture_output"])
        self.assertIs(True, received["kwargs"]["text"])
        self.assertIs(False, received["kwargs"]["check"])

    def test_command_runner_normalizes_timeout_and_redacts_output(self) -> None:
        def timeout_runner(args, **kwargs):
            raise subprocess.TimeoutExpired(
                args,
                kwargs["timeout"],
                output=r"C:\Users\Alice\capture",
                stderr="token=abc123",
            )

        result = collectors.run_command(["tool.exe"], runner=timeout_runner)
        self.assertTrue(result.timed_out)
        self.assertEqual(124, result.exit_code)
        self.assertNotIn("Alice", result.stdout)
        self.assertNotIn("abc123", result.stderr)
        self.assertIn("[REDACTED]", result.stdout)
        self.assertIn("[REDACTED]", result.stderr)

    def test_machine_identity_hashes_raw_host_label(self) -> None:
        identity = collectors.collect_machine_identity(
            system=lambda: "Windows",
            release=lambda: "11",
            version=lambda: "10.0.26100",
            machine=lambda: "AMD64",
            node=lambda: "private-host",
        )
        self.assertEqual("[REDACTED]", identity["host_label"])
        self.assertNotIn("private-host", json.dumps(identity))
        self.assertEqual(
            "sha256:" + hashlib.sha256(b"private-host").hexdigest(),
            identity["host_fingerprint"],
        )

    def test_fixed_volume_collector_is_metadata_only_and_rejects_nonlocal_rows(self) -> None:
        captured: list[str] = []
        payload = [
            {
                "DeviceID": "D:",
                "DriveType": 3,
                "FileSystem": "NTFS",
                "Size": "200",
                "FreeSpace": "50",
                "VolumeSerialNumber": "SERIAL-D",
            },
            {
                "DeviceID": r"\\server\share",
                "DriveType": 4,
                "FileSystem": "NTFS",
                "Size": "999",
                "FreeSpace": "999",
                "VolumeSerialNumber": "NETWORK",
            },
            {
                "DeviceID": "C:",
                "DriveType": 3,
                "FileSystem": "NTFS",
                "Size": "100",
                "FreeSpace": "40",
                "VolumeSerialNumber": "SERIAL-C",
            },
        ]

        def command(args):
            captured.extend(args)
            return collectors.CommandResult(json.dumps(payload), "", 0)

        volumes, status, errors = collectors.collect_fixed_local_volumes(
            os_name="nt",
            command=command,
        )
        self.assertEqual(["C:", "D:"], [volume["volume_id"] for volume in volumes])
        self.assertEqual("partial", status)
        self.assertEqual(["INVALID_VOLUME_METADATA"], [error.code for error in errors])
        joined = " ".join(captured)
        self.assertIn("Win32_LogicalDisk", joined)
        self.assertIn("DriveType=3", joined)
        for forbidden in (
            "Get-ChildItem",
            "-Recurse",
            "Get-Content",
            "Resolve-Path",
            "Invoke-WebRequest",
        ):
            self.assertNotIn(forbidden, joined)

    def test_inaccessible_volume_source_is_isolated_from_identity(self) -> None:
        error = collectors.CollectorError(
            "fixed_local_volumes",
            "ACCESS_DENIED",
            r"Access denied at C:\Users\Alice; password=private",
            True,
        )
        observation = collectors.collect_observed_state(
            collected_at_utc="2026-07-29T00:00:00Z",
            identity_collector=lambda: {
                "host_fingerprint": _sha("a"),
                "host_label": "[REDACTED]",
                "os_family": "windows",
                "os_release": "11",
                "os_version": "10.0.26100",
                "architecture": "amd64",
            },
            volume_collector=lambda: ([], "failed", [error]),
        )
        self.assertEqual("collected", observation["collector_status"]["machine_identity"])
        self.assertEqual("failed", observation["collector_status"]["fixed_local_volumes"])
        serialized = json.dumps(observation)
        self.assertNotIn("Alice", serialized)
        self.assertNotIn("private", serialized)
        self.assertEqual([], contracts.validate_contract(observation))

    def test_two_runs_are_identical_after_declared_volatile_fields_are_removed(self) -> None:
        identity = {
            "host_fingerprint": _sha("a"),
            "host_label": "[REDACTED]",
            "os_family": "windows",
            "os_release": "11",
            "os_version": "10.0.26100",
            "architecture": "amd64",
        }
        volumes = [
            {
                "volume_id": "C:",
                "drive_type": "fixed",
                "filesystem": "NTFS",
                "capacity_bytes": 100,
                "free_bytes": 40,
                "serial_fingerprint": _sha("b"),
            }
        ]
        first = collectors.collect_observed_state(
            collected_at_utc="2026-07-29T00:00:00Z",
            identity_collector=lambda: copy.deepcopy(identity),
            volume_collector=lambda: (copy.deepcopy(volumes), "collected", []),
        )
        second = collectors.collect_observed_state(
            collected_at_utc="2026-07-29T00:00:01Z",
            identity_collector=lambda: copy.deepcopy(identity),
            volume_collector=lambda: (copy.deepcopy(volumes), "collected", []),
        )
        first_bytes = contracts.canonical_json_bytes(contracts.normalize_nonvolatile(first))
        second_bytes = contracts.canonical_json_bytes(contracts.normalize_nonvolatile(second))
        self.assertEqual(first_bytes, second_bytes)
        self.assertEqual([], contracts.validate_contract(first))
        self.assertEqual([], contracts.validate_contract(second))

    def test_non_windows_volume_collection_fails_closed(self) -> None:
        volumes, status, errors = collectors.collect_fixed_local_volumes(os_name="posix")
        self.assertEqual([], volumes)
        self.assertEqual("unsupported", status)
        self.assertEqual("UNSUPPORTED_PLATFORM", errors[0].code)

    def test_collectors_expose_no_mutation_or_traversal_api(self) -> None:
        public_callables = {
            name
            for name, value in vars(collectors).items()
            if not name.startswith("_") and callable(value)
        }
        forbidden_verbs = (
            "apply",
            "delete",
            "move",
            "quarantine",
            "restore",
            "install",
            "upgrade",
            "uninstall",
            "repair",
            "schedule",
            "service",
            "startup",
            "security",
        )
        for name in public_callables:
            self.assertFalse(name.lower().startswith(forbidden_verbs), name)
        source = inspect.getsource(collectors)
        for forbidden_fragment in (
            "os.environ",
            ".rglob(",
            ".read_text(",
            ".read_bytes(",
            "follow_symlinks=True",
        ):
            self.assertNotIn(forbidden_fragment, source)


class ReportingAndCliTests(unittest.TestCase):
    def test_validation_report_is_deterministic(self) -> None:
        observed = _valid_documents()[0]
        first = reporting.render_validation_report(observed)
        second = reporting.render_validation_report(copy.deepcopy(observed))
        self.assertEqual(first, second)
        report = json.loads(first)
        self.assertTrue(report["valid"])
        self.assertRegex(report["document_digest"], r"^sha256:[0-9a-f]{64}$")
        self.assertRegex(report["nonvolatile_digest"], r"^sha256:[0-9a-f]{64}$")

    def test_execution_receipt_renderer_validates_before_rendering(self) -> None:
        receipt = _valid_documents()[3]
        self.assertTrue(reporting.render_execution_receipt(receipt).endswith(b"\n"))
        receipt["executor"] = "atlas"
        with self.assertRaises(contracts.ContractValidationError):
            reporting.render_execution_receipt(receipt)

    def test_sample_bundle_is_new_only_and_content_addressed(self) -> None:
        observed = _valid_documents()[0]
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary)
            result = reporting.write_sample_bundle(output, observed)
            run_directory = Path(result["run_directory"])
            self.assertEqual(observed["observation_id"], run_directory.name)
            for item in result["manifest"]["outputs"]:
                content = (run_directory / item["path"]).read_bytes()
                self.assertEqual(item["bytes"], len(content))
                self.assertEqual(
                    item["sha256"],
                    "sha256:" + hashlib.sha256(content).hexdigest(),
                )
            with self.assertRaises(FileExistsError):
                reporting.write_sample_bundle(output, observed)

    def test_cli_has_only_validate_and_sample_commands(self) -> None:
        parser = build_parser()
        subparser_action = next(
            action for action in parser._actions if getattr(action, "choices", None)
        )
        self.assertEqual({"sample", "validate"}, set(subparser_action.choices))
        help_text = parser.format_help().lower()
        for forbidden in ("apply", "delete", "install", "repair", "execute"):
            self.assertNotIn(forbidden, help_text)


if __name__ == "__main__":
    unittest.main()
