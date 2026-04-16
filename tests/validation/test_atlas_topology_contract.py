from __future__ import annotations

import json
import tempfile
import unittest
from copy import deepcopy
from pathlib import Path

from ops.validation.atlas_topology_contract import (
    default_manifest_path,
    default_schema_path,
    validate_contract_files,
)

ROOT = Path(__file__).resolve().parents[2]


class AtlasTopologyContractTests(unittest.TestCase):
    def test_current_manifest_is_valid(self) -> None:
        _, _, issues = validate_contract_files(
            manifest_path=default_manifest_path(),
            schema_path=default_schema_path(),
            stack_file=ROOT / "stack.yaml",
        )
        self.assertEqual([], issues)

    def test_machine_identity_hostname_is_rejected(self) -> None:
        manifest = json.loads(default_manifest_path().read_text(encoding="utf-8"))
        broken = deepcopy(manifest)
        broken["hostname_rules"][0]["hostname_template"] = "machine-{app}.{zone}"

        with tempfile.TemporaryDirectory() as temp_dir:
            manifest_path = Path(temp_dir) / "broken-topology-manifest.json"
            manifest_path.write_text(json.dumps(broken, indent=2) + "\n", encoding="utf-8")
            _, _, issues = validate_contract_files(
                manifest_path=manifest_path,
                schema_path=default_schema_path(),
                stack_file=ROOT / "stack.yaml",
            )

        categories = {issue.category for issue in issues}
        self.assertIn("atlas-topology-hostname-template", categories)


if __name__ == "__main__":
    unittest.main()
