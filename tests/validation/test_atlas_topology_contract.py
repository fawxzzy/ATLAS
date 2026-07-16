from __future__ import annotations

import json
import tempfile
import unittest
from copy import deepcopy
from pathlib import Path

from ops.validation.atlas_topology_contract import (
    default_manifest_path,
    default_schema_path,
    resolve_topology_app_identity,
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

    def test_current_and_legacy_fawxzzyweb_identities_resolve_to_stable_app_id(self) -> None:
        manifest = json.loads(default_manifest_path().read_text(encoding="utf-8"))

        for candidate in [
            "trove",
            "FawxzzyWeb",
            "fawxzzyweb",
            "https://fawxzzy.com",
            "Trove",
            "fawxzzy-trove",
            "https://fawxzzy-trove.vercel.app",
        ]:
            with self.subTest(candidate=candidate):
                self.assertEqual("trove", resolve_topology_app_identity(manifest, candidate))

    def test_unknown_fawxzzyweb_identity_fails_closed(self) -> None:
        manifest = json.loads(default_manifest_path().read_text(encoding="utf-8"))
        with self.assertRaisesRegex(ValueError, "Unknown or ambiguous"):
            resolve_topology_app_identity(manifest, "fawxzzyweb-unknown")

    def test_identity_projection_drift_is_rejected(self) -> None:
        manifest = json.loads(default_manifest_path().read_text(encoding="utf-8"))
        broken = deepcopy(manifest)
        trove = next(app for app in broken["apps"] if app["app_id"] == "trove")
        trove["operational_identity"]["provider_project"] = "fawxzzy-trove"

        with tempfile.TemporaryDirectory() as temp_dir:
            manifest_path = Path(temp_dir) / "broken-topology-manifest.json"
            manifest_path.write_text(json.dumps(broken, indent=2) + "\n", encoding="utf-8")
            _, _, issues = validate_contract_files(
                manifest_path=manifest_path,
                schema_path=default_schema_path(),
                stack_file=ROOT / "stack.yaml",
            )

        self.assertIn("atlas-topology-operational-identity", {issue.category for issue in issues})
        with self.assertRaisesRegex(ValueError, "Unauthorized topology operational identity"):
            resolve_topology_app_identity(broken, "fawxzzy-trove")

    def test_operator_identity_without_stack_authority_is_rejected(self) -> None:
        manifest = json.loads(default_manifest_path().read_text(encoding="utf-8"))
        broken = deepcopy(manifest)
        lifeline = next(app for app in broken["apps"] if app["app_id"] == "lifeline")
        lifeline["operational_identity"] = {
            "identity_ref": "stack.yaml#repo_registry.lifeline.identity",
            "display_name": "Unauthorized Operator Alias",
            "github_repository": "example/unauthorized",
            "provider_project": "unauthorized",
            "provider_project_id": "prj_unauthorized",
            "canonical_public_origin": "https://unauthorized.example",
            "redirect_origins": ["https://www.unauthorized.example"],
            "accepted_aliases": ["unauthorized-operator"],
        }

        with tempfile.TemporaryDirectory() as temp_dir:
            manifest_path = Path(temp_dir) / "broken-topology-manifest.json"
            manifest_path.write_text(json.dumps(broken, indent=2) + "\n", encoding="utf-8")
            _, _, issues = validate_contract_files(
                manifest_path=manifest_path,
                schema_path=default_schema_path(),
                stack_file=ROOT / "stack.yaml",
            )

        self.assertIn("atlas-topology-operational-identity", {issue.category for issue in issues})
        with self.assertRaisesRegex(ValueError, "Unauthorized topology operational identity"):
            resolve_topology_app_identity(broken, "unauthorized-operator")

    def test_trove_production_rule_preserves_stable_service_key(self) -> None:
        manifest = json.loads(default_manifest_path().read_text(encoding="utf-8"))
        rule = next(rule for rule in manifest["hostname_rules"] if rule["rule_id"] == "trove-prod")
        self.assertEqual("trove/prod", rule["service_key_template"])


if __name__ == "__main__":
    unittest.main()
