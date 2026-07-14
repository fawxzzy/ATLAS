from __future__ import annotations

import copy
import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from ops.cortex.receipt_replay import run
from tests.test_cortex_simulation_agent_state_schema import SCHEMA_PATH, validate_contract


def write_json(path: Path, payload: object) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def receipt_v1() -> dict[str, object]:
    return {"contract_version": "atlas.receipt.v1", "receipt_id": "receipt-pass", "recorded_at": "2026-07-14T10:00:00Z", "status": "passed", "summary": "Passed proof."}


def receipt_v2() -> dict[str, object]:
    return {"contract_version": "atlas.execution-receipt.v2", "receipt_id": "receipt-block", "recorded_at": "2026-07-14T10:01:00Z", "status": "blocked", "verification": [{"status": "blocked"}], "summary": "Blocked proof."}


class CortexReceiptReplayTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.manifest_ref = "data/cortex/simulation-replays/test/manifest.json"
        self.first_ref = "data/cortex/simulation-replays/test/pass.json"
        self.second_ref = "data/cortex/simulation-replays/test/block.json"
        first_digest = write_json(self.root / self.first_ref, receipt_v1())
        second_digest = write_json(self.root / self.second_ref, receipt_v2())
        self.manifest = {"contract_version": "atlas.cortex.simulation.receipt-replay-manifest.v1", "scenario_id": "scenario", "agent_id": "agent", "generated_at": "2026-07-14T10:02:00Z", "objective": "Replay receipts.", "receipts": [{"ref": self.second_ref, "digest": second_digest, "trust_class": "committed_replay_fixture"}, {"ref": self.first_ref, "digest": first_digest, "trust_class": "committed_replay_fixture"}]}
        write_json(self.root / self.manifest_ref, self.manifest)

    def rerun(self, manifest: dict[str, object]) -> tuple[dict[str, object], int]:
        write_json(self.root / self.manifest_ref, manifest)
        return run(root=self.root, manifest_path=self.manifest_ref, output_path=None)

    def test_mixed_replay_is_deterministic_chronological_and_authority_false(self) -> None:
        first, code = self.rerun(self.manifest)
        second, second_code = self.rerun(self.manifest)
        self.assertEqual((0, 0), (code, second_code))
        self.assertEqual(first, second)
        replay = first["replay"]
        self.assertTrue(replay["threshold_eligible"])
        self.assertEqual(["receipt-pass", "receipt-block"], [item["receipt_id"] for item in replay["receipt_observations"]])
        self.assertEqual({"success": 1, "advisory": 0, "failure": 0, "blocked": 1}, replay["failure_mode_counts"])
        self.assertFalse(replay["authority"]["execution_authorized"])
        schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
        validate_contract(replay["agent_state"], schema, schema)

    def test_digest_mismatch_duplicate_and_unknown_contract_fail_closed(self) -> None:
        bad = copy.deepcopy(self.manifest)
        bad["receipts"][0]["digest"] = "sha256:" + "0" * 64
        self.assertEqual("blocker", self.rerun(bad)[0]["status"])
        duplicate = receipt_v2()
        duplicate["receipt_id"] = "receipt-pass"
        digest = write_json(self.root / self.second_ref, duplicate)
        bad = copy.deepcopy(self.manifest)
        bad["receipts"][0]["digest"] = digest
        self.assertIn("duplicate_receipt_id", [item["code"] for item in self.rerun(bad)[0]["blockers"]])
        restored_digest = write_json(self.root / self.second_ref, receipt_v2())
        unknown = receipt_v1()
        unknown["contract_version"] = "atlas.unknown.v1"
        digest = write_json(self.root / self.first_ref, unknown)
        bad = copy.deepcopy(self.manifest)
        bad["receipts"][0]["digest"] = restored_digest
        bad["receipts"][1]["digest"] = digest
        self.assertIn("receipt_contract_not_admitted", [item["code"] for item in self.rerun(bad)[0]["blockers"]])

    def test_contract_fixture_only_is_advisory_and_unsafe_paths_are_blocked(self) -> None:
        contract_ref = "packages/atlas-contracts/fixtures/valid/receipt.json"
        digest = write_json(self.root / contract_ref, receipt_v1())
        manifest = copy.deepcopy(self.manifest)
        manifest["receipts"] = [{"ref": contract_ref, "digest": digest, "trust_class": "contract_fixture"}]
        result, code = self.rerun(manifest)
        self.assertEqual(1, code)
        self.assertEqual("advisory_gap", result["status"])
        for unsafe in ("../manifest.json", "repos/mazer/manifest.json", "secrets/manifest.json"):
            self.assertEqual("blocker", run(root=self.root, manifest_path=unsafe, output_path=None)[0]["status"])

    def test_explicit_safe_output_only(self) -> None:
        output = "tmp/atlas/replay.json"
        result, code = run(root=self.root, manifest_path=self.manifest_ref, output_path=output)
        self.assertEqual(0, code)
        self.assertEqual(result["replay"], json.loads((self.root / output).read_text(encoding="utf-8")))
        self.assertEqual("blocker", run(root=self.root, manifest_path=self.manifest_ref, output_path="../replay.json")[0]["status"])


if __name__ == "__main__":
    unittest.main()
