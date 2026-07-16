from __future__ import annotations

import unittest
from copy import deepcopy
from pathlib import Path

from ops._atlas import load_stack_config
from ops.atlas.operational_identity import (
    OperationalIdentityError,
    canonicalize_vercel_project,
    load_operational_identity,
    operational_identity_from_config,
    resolve_operational_identity,
)


ROOT = Path(__file__).resolve().parents[1]


class OperationalIdentityTests(unittest.TestCase):
    def test_fawxzzyweb_mapping_preserves_stable_repo_contracts(self) -> None:
        identity = load_operational_identity(ROOT, "trove")

        self.assertEqual("trove", identity["logical_id"])
        self.assertEqual("repos/trove", identity["local_path"])
        self.assertEqual("FawxzzyWeb", identity["display_name"])
        self.assertEqual("fawxzzy/FawxzzyWeb", identity["github_repository"])
        self.assertEqual("fawxzzyweb", identity["vercel_project"])
        self.assertEqual("prj_vhUyajI4AL6BgCF40VnKtdxrBLuV", identity["vercel_project_id"])
        self.assertEqual("https://fawxzzy.com", identity["public_origin"])
        self.assertEqual("https://www.fawxzzy.com", identity["www_redirect_origin"])

    def test_canonical_and_legacy_aliases_resolve_to_trove(self) -> None:
        identity = load_operational_identity(ROOT, "trove")

        for alias in ("trove", "FawxzzyWeb", "fawxzzyweb", "Trove", "fawxzzy-trove"):
            with self.subTest(alias=alias):
                self.assertEqual("trove", resolve_operational_identity(identity, alias))

    def test_unknown_alias_fails_closed(self) -> None:
        identity = load_operational_identity(ROOT, "trove")

        with self.assertRaises(OperationalIdentityError):
            resolve_operational_identity(identity, "unknown-product")

    def test_vercel_alias_dual_read_normalizes_to_canonical_project(self) -> None:
        identity = load_operational_identity(ROOT, "trove")
        project_id = "prj_vhUyajI4AL6BgCF40VnKtdxrBLuV"

        self.assertEqual(
            "fawxzzyweb",
            canonicalize_vercel_project(identity, project_id=project_id, project_name="fawxzzyweb"),
        )
        self.assertEqual(
            "fawxzzyweb",
            canonicalize_vercel_project(identity, project_id=project_id, project_name="fawxzzy-trove"),
        )
        with self.assertRaises(OperationalIdentityError):
            canonicalize_vercel_project(identity, project_id=project_id, project_name="unknown-project")

    def test_malformed_identity_is_rejected(self) -> None:
        config = deepcopy(load_stack_config(ROOT / "stack.yaml"))
        del config["repo_registry"]["trove"]["identity"]["vercel"]["project_id"]

        with self.assertRaises(OperationalIdentityError):
            operational_identity_from_config(config, "trove")


if __name__ == "__main__":
    unittest.main()
