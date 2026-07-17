from __future__ import annotations

import hashlib
import importlib.util
import json
import subprocess
import sys
import types
import unittest
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "ops" / "atlas" / "master_program.py"
SPEC = importlib.util.spec_from_file_location("atlas_master_program", MODULE_PATH)
assert SPEC and SPEC.loader
MASTER_PROGRAM = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MASTER_PROGRAM)


def load_json(ref: str) -> dict:
    return json.loads((ROOT / ref).read_text(encoding="utf-8"))


class AtlasMasterProgramTests(unittest.TestCase):
    def test_repository_contract_is_valid(self) -> None:
        self.assertEqual([], MASTER_PROGRAM.validate_repository())

    def test_historical_guards_match_exact_merged_base_blobs(self) -> None:
        for ref, expected in MASTER_PROGRAM.HISTORICAL_FILE_GUARDS.items():
            committed = subprocess.check_output(
                ["git", "show", f"{MASTER_PROGRAM.BASE_COMMIT}:{ref}"],
                cwd=ROOT,
            )
            self.assertEqual(expected, hashlib.sha256(committed).hexdigest(), ref)
            self.assertEqual(expected, MASTER_PROGRAM._file_digest(ROOT / ref), ref)

    def test_generated_artifacts_are_byte_deterministic(self) -> None:
        first_register = MASTER_PROGRAM._json_bytes(MASTER_PROGRAM.build_master_register())
        second_register = MASTER_PROGRAM._json_bytes(MASTER_PROGRAM.build_master_register())
        self.assertEqual(first_register, second_register)
        self.assertEqual(
            first_register,
            (ROOT / "docs/registry/ATLAS-MASTER-PROGRAM-REGISTER.v1.json").read_bytes(),
        )
        for source_spec in MASTER_PROGRAM.IMPORTS:
            first = MASTER_PROGRAM._json_bytes(MASTER_PROGRAM.build_import_manifest(source_spec))
            second = MASTER_PROGRAM._json_bytes(MASTER_PROGRAM.build_import_manifest(source_spec))
            self.assertEqual(first, second)
            self.assertEqual(first, (ROOT / source_spec["manifest_ref"]).read_bytes())

    def test_source_imports_are_exact_and_have_one_manifest_contract(self) -> None:
        for source_spec in MASTER_PROGRAM.IMPORTS:
            raw = (ROOT / source_spec["stored_ref"]).read_bytes()
            self.assertEqual(source_spec["byte_length"], len(raw))
            self.assertEqual(source_spec["sha256"], hashlib.sha256(raw).hexdigest())
            manifest = load_json(source_spec["manifest_ref"])
            self.assertEqual(source_spec["stored_ref"], manifest["stored"]["path"])
            self.assertTrue(manifest["copy_policy"]["byte_for_byte"])
            self.assertFalse(manifest["copy_policy"]["normalization"])
            self.assertTrue(manifest["copy_policy"]["fail_closed"])
        self.assertFalse(
            (ROOT / "data/imports/deepseek-bridge/2026-07-13/source-manifest.json").exists()
        )
        self.assertFalse(
            (ROOT / "data/imports/fawxzzy-platform/2026-07-16/source-manifest.json").exists()
        )
        self.assertEqual([], MASTER_PROGRAM._validate_packet_git_attributes())

    def test_new_lanes_are_complete_and_unmeasured(self) -> None:
        registry = load_json("docs/registry/ATLAS-FULL-SYSTEM-REEVALUATION-LANES.json")
        entries = registry["lanes"] + registry["backlog_candidates"]
        by_id = {entry["id"]: entry for entry in entries}
        required = {
            "owner",
            "authority",
            "scope",
            "dependencies",
            "serialization_rules",
            "approval_gates",
            "evidence_sources",
            "definition_of_done",
            "status",
            "next_packet",
            "measurement_status",
        }
        self.assertEqual(MASTER_PROGRAM.NEW_LANE_IDS, MASTER_PROGRAM.NEW_LANE_IDS & by_id.keys())
        for lane_id in MASTER_PROGRAM.NEW_LANE_IDS:
            lane = by_id[lane_id]
            self.assertTrue(required.issubset(lane), lane_id)
            self.assertIsNone(lane["percentage"], lane_id)
            self.assertEqual("UNMEASURED", lane["measurement_status"], lane_id)
            self.assertIsNone(lane["denominator"]["value"], lane_id)

    def test_platform_decision_and_recovery_serialization_are_exact(self) -> None:
        admission = load_json("docs/registry/FAWXZZY-PLATFORM-MIGRATION-ADMISSION.json")
        decision = admission["architecture_decision"]
        self.assertIn("Fitness", decision["platform_seed"])
        self.assertIn("separate", decision["discordos"])
        self.assertIn("fourth blank project", decision["new_blank_project"])
        self.assertEqual(["expand", "migrate", "verify", "cutover", "contract"], decision["migration_sequence"])
        self.assertIsNone(admission["decomposition"]["measurement_effect"])
        packets = admission["terminal_zero_mutation_parity_truth"]["recovery_packets"]
        self.assertEqual(
            ["FP-DOS-REC-001", "FP-MZR-REC-001", "FP-FIT-REC-001", "FP-PARITY-RATCHET-001"],
            [packet["id"] for packet in packets],
        )
        self.assertEqual("FP-DOS-REC-001", admission["next_packet"])

    def test_deepseek_historical_metric_is_preserved_but_not_reused(self) -> None:
        initiative = load_json(
            "docs/memory/initiatives/initiative-external-model-sidecar-deepseek-litellm-bridge.json"
        )
        self.assertEqual(
            {
                "numerator": 2,
                "denominator": 6,
                "percent": 33.3,
                "marker": "33.3%",
                "admission_completes_no_unit": False,
            },
            initiative["metadata"]["progress"],
        )
        self.assertEqual(
            {"status": "UNMEASURED", "percentage": None, "denominator": None},
            initiative["metadata"]["current_measurement"],
        )
        admission = load_json("docs/registry/DEEPSEEK-BRIDGE-WAVE-0-ADMISSION.json")
        self.assertEqual("UNMEASURED", admission["measurement_status"])
        self.assertEqual(
            "lane-external-model-sidecar-deepseek-evaluation",
            admission["initiative_mapping"]["current_backlog_id"],
        )
        registry = load_json("docs/registry/ATLAS-FULL-SYSTEM-REEVALUATION-LANES.json")
        lane = next(
            entry
            for entry in registry["backlog_candidates"]
            if entry["id"] == "lane-external-model-sidecar-deepseek-evaluation"
        )
        register = load_json("docs/registry/ATLAS-MASTER-PROGRAM-REGISTER.v1.json")
        program = next(
            entry for entry in register["programs"] if entry["id"] == "program-deepseek-sidecar-evaluation"
        )
        self.assertEqual("DS-BRIDGE-CAP-001", lane["next_packet"]["id"])
        self.assertEqual("DS-BRIDGE-CAP-001", admission["next_packet"])
        self.assertEqual("DS-BRIDGE-CAP-001", initiative["metadata"]["current_exact_next_packet"])
        self.assertTrue(initiative["proposed_next_session_refs"][0].startswith("DS-BRIDGE-CAP-001 "))
        self.assertEqual("DS-BRIDGE-CAP-001", program["next_packet"])

    def test_schema_formats_fail_closed_in_full_and_fallback_paths(self) -> None:
        invalid = load_json("docs/registry/DEEPSEEK-BRIDGE-WAVE-0-ADMISSION.json")
        invalid["generated_at"] = "2026-07-16T23:00:00"
        self.assertTrue(
            MASTER_PROGRAM._schema_subset_validate(
                invalid,
                load_json("schemas/atlas.program-admission.v1.json"),
            )
        )
        self.assertTrue(
            MASTER_PROGRAM._schema_validate(
                invalid,
                "schemas/atlas.program-admission.v1.json",
            )
        )

        class FakeFormatChecker:
            pass

        class FakeDraft202012Validator:
            received_checker = None

            def __init__(self, schema, *, format_checker=None):
                del schema
                type(self).received_checker = format_checker

            def iter_errors(self, instance):
                del instance
                return []

        fake_jsonschema = types.SimpleNamespace(
            Draft202012Validator=FakeDraft202012Validator,
            FormatChecker=FakeFormatChecker,
        )
        with mock.patch.dict(sys.modules, {"jsonschema": fake_jsonschema}):
            self.assertEqual(
                [],
                MASTER_PROGRAM._schema_validate(
                    load_json("docs/registry/DEEPSEEK-BRIDGE-WAVE-0-ADMISSION.json"),
                    "schemas/atlas.program-admission.v1.json",
                ),
            )
        self.assertIsInstance(FakeDraft202012Validator.received_checker, FakeFormatChecker)

    def test_master_register_covers_required_program_families(self) -> None:
        register = load_json("docs/registry/ATLAS-MASTER-PROGRAM-REGISTER.v1.json")
        program_ids = {program["id"] for program in register["programs"]}
        required = {
            "program-clean-resync-authority-index",
            "program-mandatory-closing-exhaustive-audit",
            "program-discordos-board-governance",
            "program-github-control-plane",
            "program-fawxzzyweb-distribution",
            "program-fawxzzy-platform-migration",
            "program-atlas-book-playbook-convergence",
            "program-long-task-continuity-resource-hygiene",
            "program-post-preparation-atlas-development",
            "program-cortex-capability-conversion",
            "program-lifeline-foundation-platform-conversion",
            "program-shared-contracts-wiring",
            "program-cross-project-synergy-knowledge-promotion",
            "program-model-effort-speed-routing",
            "program-persistent-workspace-leases",
            "program-historical-conversation-task-knowledge",
            "program-deepseek-sidecar-evaluation",
        }
        self.assertTrue(required.issubset(program_ids))
        index = register["authority_indexes"]["clean_and_resync_lane_registry"]
        self.assertEqual(20, len(index["lane_ids"]))
        self.assertEqual(48, len(index["backlog_ids"]))


if __name__ == "__main__":
    unittest.main()
