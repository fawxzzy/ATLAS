from __future__ import annotations

import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from ops.atlas.playbook_contract import build_playbook_adoption_report


class AtlasPlaybookVerificationProjectionTests(unittest.TestCase):
    def _write_json(self, path: Path, payload: dict) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")

    def _write_text(self, path: Path, text: str) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")

    def _inventory_payload(self) -> dict:
        return {
            "repos": [
                {
                    "logical_id": "playbook",
                    "local_path": "repos/fawxzzy-playbook",
                    "exists": True,
                    "remote_url": "https://example.com/playbook.git",
                    "trust_class": "trusted",
                    "related_initiative_refs": [],
                },
                {
                    "logical_id": "fitness",
                    "local_path": "repos/fawxzzy-fitness",
                    "exists": True,
                    "remote_url": "https://example.com/fitness.git",
                    "trust_class": "trusted",
                    "related_initiative_refs": [],
                },
            ]
        }

    def _write_playbook_owner_surface(self, root: Path) -> None:
        repo_root = root / "repos" / "fawxzzy-playbook"
        self._write_json(
            repo_root / "exports" / "playbook.contract.example.v1.json",
            {
                "contract_id": "playbook_convergence_contract",
                "contract_version": "1.0.0",
                "status": "active",
                "intent": {},
                "canonical_principles": [],
                "operating_loop": {},
                "owner_domains": [],
                "conformance_classes": [],
                "patterns": [],
                "continuity_requirements": {},
                "adoption_statuses": [],
                "evidence_types": [],
                "exception_requirements": {},
                "adoption_checks": [],
                "verification_hooks": [],
                "anti_patterns": [],
            },
        )
        self._write_json(repo_root / "exports" / "playbook.contract.schema.v1.json", {"type": "object"})
        self._write_text(repo_root / "docs" / "contracts" / "PLAYBOOK-CONTRACT.md", "# Playbook Contract\n")
        self._write_text(
            repo_root / "packages" / "engine" / "test" / "playbookContractExport.test.ts",
            "export {};\n",
        )

    def _write_repo_adoption_surface(
        self,
        root: Path,
        *,
        repo_id: str = "fitness",
        not_applicable_notes: list[str] | None = None,
    ) -> None:
        repo_root = root / "repos" / f"fawxzzy-{repo_id}"
        self._write_json(repo_root / "exports" / "repo.playbook.adoption.evidence.schema.v1.json", {"type": "object"})
        self._write_text(
            repo_root / "docs" / "ops" / f"{repo_id.upper()}-PLAYBOOK-ADOPTION.md",
            f"# {repo_id.upper()} Playbook Adoption\n",
        )
        self._write_text(repo_root / "tests" / "playbook-adoption-evidence.test.mjs", "export {};\n")
        self._write_json(
            repo_root / "exports" / f"{repo_id}.playbook.adoption.evidence.v1.json",
            {
                "artifact_id": f"{repo_id}_playbook_adoption_evidence_v1",
                "generated_at": "2026-04-17T18:00:00Z",
                "repo": {
                    "repo_id": repo_id,
                    "role": "vertical_owner_repo",
                    "repo_identity": "remote",
                    "repo_path": f"repos/fawxzzy-{repo_id}",
                },
                "contract_claim": {
                    "contract_id": "playbook_convergence_contract",
                    "contract_version": "1.0.0",
                    "source_repo_id": "playbook",
                    "source_export_path": "repos/fawxzzy-playbook/exports/playbook.contract.example.v1.json",
                    "claim_state": "declared",
                },
                "summary": {
                    "adoption_status": "adopted",
                    "verification_state": "targeted",
                    "continuity_status": "structured",
                    "drift_status": "none_detected",
                    "notes": ["Repo is adopted but not yet verified."],
                },
                "implemented_patterns": [
                    {
                        "id": "pattern_required",
                        "status": "implemented",
                        "notes": ["Implemented in the repo-local lane."],
                    },
                    {
                        "id": "pattern_root_owned_boundary",
                        "status": "not_applicable",
                        "notes": not_applicable_notes if not_applicable_notes is not None else ["Root-owned boundary."],
                    },
                ],
                "adoption_checks": [
                    {
                        "id": "adoption_check_required",
                        "status": "implemented",
                        "notes": ["Adoption check is covered by the repo-local test."],
                    }
                ],
                "continuity": {
                    "structured_handoff_required": True,
                    "transcript_role": "trace_only",
                    "promotion_targets": ["knowledge", "receipt"],
                },
                "evidence_refs": [
                    f"exports/{repo_id}.playbook.adoption.evidence.v1.json",
                    "tests/playbook-adoption-evidence.test.mjs",
                ],
                "verification_commands": ["npm run test:playbook-adoption", "npm run verify"],
            },
        )

    def _write_verification_report(
        self,
        root: Path,
        *,
        repo_id: str = "fitness",
        verification_status: str,
        adoption_export_status: str = "passed",
        adoption_test_status: str = "passed",
        verification_path_status: str = "passed",
        blocking_gaps: list[str] | None = None,
        last_verified_at: str | None = None,
    ) -> None:
        repo_root = root / "repos" / f"fawxzzy-{repo_id}"
        self._write_json(
            repo_root / "exports" / f"{repo_id}.playbook.verification.report.v1.json",
            {
                "artifact_id": f"{repo_id}_playbook_verification_report_v1",
                "generated_at": "2026-04-17T19:00:00Z",
                "repo": {
                    "repo_id": repo_id,
                    "repo_identity": "remote",
                    "repo_path": f"repos/fawxzzy-{repo_id}",
                },
                "summary": {
                    "adoption_status": "adopted",
                    "verification_status": verification_status,
                    "blocking_gaps": blocking_gaps or [],
                    "last_verified_at": last_verified_at,
                },
                "scope": {
                    "verification_kind": "targeted",
                    "covered_surfaces": ["Repo-owned verification path"],
                    "notes": ["Targeted verification scope for the repo-owned slice."],
                },
                "criteria": {
                    "adoption_export": {
                        "status": adoption_export_status,
                        "evidence_refs": [f"exports/{repo_id}.playbook.adoption.evidence.v1.json"],
                    },
                    "adoption_test": {
                        "status": adoption_test_status,
                        "evidence_refs": ["tests/playbook-adoption-evidence.test.mjs"],
                    },
                    "verification_path": {
                        "status": verification_path_status,
                        "commands": ["npm run verify"],
                        "evidence_refs": ["runtime/receipts/verify.json"],
                    },
                },
                "evidence_refs": [
                    f"exports/{repo_id}.playbook.adoption.evidence.v1.json",
                    "tests/playbook-adoption-evidence.test.mjs",
                    "runtime/receipts/verify.json",
                ],
            },
        )

    def _fitness_row(self, root: Path) -> dict:
        report = build_playbook_adoption_report(root=root, inventory_payload=self._inventory_payload())
        return next(row for row in report["repos"] if row["repo_id"] == "fitness")

    def test_verified_repo_requires_green_verification_report(self) -> None:
        with TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            self._write_playbook_owner_surface(root)
            self._write_repo_adoption_surface(root)
            self._write_verification_report(
                root,
                verification_status="verified",
                last_verified_at="2026-04-17T19:05:00Z",
            )

            row = self._fitness_row(root)

        self.assertEqual(row["adoption_status"], "adopted")
        self.assertEqual(row["verification_scope"], "targeted")
        self.assertEqual(row["verification_status"], "verified")
        self.assertEqual(row["last_verified_at"], "2026-04-17T19:05:00Z")
        self.assertEqual(row["blocking_gaps"], [])

    def test_partial_repo_stays_below_verified_when_verification_path_is_incomplete(self) -> None:
        with TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            self._write_playbook_owner_surface(root)
            self._write_repo_adoption_surface(root)
            self._write_verification_report(
                root,
                verification_status="partial",
                verification_path_status="missing",
                blocking_gaps=["Verification path has not run green yet."],
            )

            row = self._fitness_row(root)

        self.assertEqual(row["adoption_status"], "adopted")
        self.assertEqual(row["verification_status"], "partial")
        self.assertIn("Verification path has not run green yet.", row["blocking_gaps"])

    def test_blocked_repo_stays_non_green_when_verification_report_fails(self) -> None:
        with TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            self._write_playbook_owner_surface(root)
            self._write_repo_adoption_surface(root)
            self._write_verification_report(
                root,
                verification_status="blocked",
                adoption_test_status="failed",
                blocking_gaps=["Repo verify command is red."],
            )

            row = self._fitness_row(root)

        self.assertEqual(row["verification_status"], "blocked")
        self.assertIn("Repo verify command is red.", row["blocking_gaps"])

    def test_unjustified_not_applicable_blocks_verified_promotion(self) -> None:
        with TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            self._write_playbook_owner_surface(root)
            self._write_repo_adoption_surface(root, not_applicable_notes=[])
            self._write_verification_report(
                root,
                verification_status="verified",
                last_verified_at="2026-04-17T19:05:00Z",
            )

            row = self._fitness_row(root)

        self.assertEqual(row["verification_status"], "blocked")
        self.assertTrue(
            any("not_applicable" in gap for gap in row["blocking_gaps"]),
            row["blocking_gaps"],
        )


if __name__ == "__main__":
    unittest.main()
