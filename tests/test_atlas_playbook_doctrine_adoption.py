from __future__ import annotations

import hashlib
import io
import json
import subprocess
import tempfile
import textwrap
import unittest
from pathlib import Path
from unittest import mock

from ops.atlas import playbook_doctrine_adoption as adoption

REGISTRY_PATH = "docs/doctrine/atlas-engineering-doctrine-registry.v1.json"
SCHEMA_PATH = "docs/doctrine/atlas-engineering-doctrine-registry.schema.v1.json"
SKILL_PATH = ".agents/skills/review-project-next-step/SKILL.md"

REGISTRY_PAYLOAD = {
    "schema_version": "atlas-engineering-doctrine-registry.v1",
    "registry_id": "atlas-engineering-doctrine-registry",
    "owner": "playbook",
    "consumer_adoption": {
        "atlas_role": "adopter-and-conformance-owner",
        "discovery": "Atlas reads the Playbook registry by source reference.",
        "copying_rule": "Atlas keeps adoption evidence without copying doctrine bodies.",
    },
    "records": [
        {
            "id": "rule-owner-repo-truth",
            "kind": "rule",
            "lifecycle": "promoted",
            "statement": "Owner repositories remain the implementation source of truth.",
            "rationale": "Avoid duplicate doctrine stores.",
            "scope": {"truth_class": "universal-doctrine", "applies_to": "routing", "excludes": []},
            "evidence": [{"evidence_id": "owner-truth", "authority": "canonical-playbook", "ref": "docs/contracts/PLAYBOOK-CONTRACT.md#owner", "note": "Owner truth."}],
            "enforcement": {"owner": "playbook", "mechanism": "review"},
            "exceptions": [],
            "review": {"last_reviewed": "2026-07-13", "reviewer": "playbook", "next_review_due": "2027-01-13"},
            "supersession": {"supersedes": [], "superseded_by": None, "retired_reason": None},
        },
        {
            "id": "failure-mode-summary-truth-drift",
            "kind": "failure-mode",
            "lifecycle": "superseded",
            "statement": "Status summaries can outpace current evidence.",
            "rationale": "Evidence must win.",
            "scope": {"truth_class": "imported-provenance", "applies_to": "status", "excludes": []},
            "evidence": [{"evidence_id": "summary-drift", "authority": "canonical-atlas", "ref": "docs/registry/example.json", "note": "Drift."}],
            "enforcement": {"owner": "atlas", "mechanism": "review"},
            "exceptions": [],
            "review": {"last_reviewed": "2026-07-13", "reviewer": "atlas", "next_review_due": "2027-01-13"},
            "supersession": {"supersedes": [], "superseded_by": "rule-owner-repo-truth", "retired_reason": None},
        },
        {
            "id": "decision-imported-plan-progress-as-current-truth",
            "kind": "decision",
            "lifecycle": "retired",
            "statement": "Imported progress is current truth.",
            "rationale": "Retained only as a rejected posture.",
            "scope": {"truth_class": "imported-provenance", "applies_to": "progress", "excludes": []},
            "evidence": [{"evidence_id": "plan-progress", "authority": "canonical-atlas", "ref": "docs/registry/example.json", "note": "Rejected."}],
            "enforcement": {"owner": "atlas", "mechanism": "classification"},
            "exceptions": [],
            "review": {"last_reviewed": "2026-07-13", "reviewer": "atlas", "next_review_due": "2027-01-13"},
            "supersession": {"supersedes": [], "superseded_by": None, "retired_reason": "Rejected."},
        },
        {
            "id": "pattern-one-honest-next-step",
            "kind": "pattern",
            "lifecycle": "candidate",
            "statement": "Choose one bounded evidence-producing next step.",
            "rationale": "Keep review actionable.",
            "scope": {"truth_class": "imported-provenance", "applies_to": "routing", "excludes": []},
            "evidence": [{"evidence_id": "one-step", "authority": "imported-provenance", "ref": "skill://review", "note": "Advisory."}],
            "enforcement": {"owner": "playbook", "mechanism": "candidate"},
            "exceptions": [],
            "review": {"last_reviewed": "2026-07-13", "reviewer": "playbook", "next_review_due": "2026-10-13"},
            "supersession": {"supersedes": [], "superseded_by": None, "retired_reason": None},
        },
    ],
}

SCHEMA_PAYLOAD = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "$id": "atlas-engineering-doctrine-registry.schema.v1.json",
    "title": "Atlas Engineering Doctrine Registry",
    "type": "object",
    "required": ["schema_version", "registry_id", "owner", "consumer_adoption", "records"],
}

SKILL_TEXT = textwrap.dedent(
    """\
    ---
    name: review-project-next-step
    description: Reconcile a project and choose one safe next step.
    ---

    # Review Project and Next Step

    Read doctrine by stable id.
    """
)


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _git(repo: Path, *args: str) -> str:
    completed = subprocess.run(
        ["git", "-C", str(repo), *args],
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    return completed.stdout.strip()


def _sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _adoption_record(commit: str) -> dict[str, object]:
    grouped: dict[str, list[str]] = {}
    for record in REGISTRY_PAYLOAD["records"]:
        grouped.setdefault(str(record["lifecycle"]), []).append(str(record["id"]))
    return {
        "contract_version": adoption.CONTRACT_VERSION,
        "source": {
            "repository_path": "repos/playbook",
            "remote_owner": "fawxzzy/playbook",
            "accepted_ref": "main",
            "accepted_commit": commit,
            "pull_request": "fawxzzy/playbook#22",
            "artifacts": {
                "registry": {"path": REGISTRY_PATH, "sha256": _sha256_text(json.dumps(REGISTRY_PAYLOAD, indent=2) + "\n")},
                "schema": {"path": SCHEMA_PATH, "sha256": _sha256_text(json.dumps(SCHEMA_PAYLOAD, indent=2) + "\n")},
                "governed_skill": {"path": SKILL_PATH, "sha256": _sha256_text(SKILL_TEXT)},
            },
        },
        "registry": {
            "registry_id": "atlas-engineering-doctrine-registry",
            "schema_version": "atlas-engineering-doctrine-registry.v1",
            "schema_id": "atlas-engineering-doctrine-registry.schema.v1.json",
            "adopted_record_ids": grouped,
        },
        "governed_skill": {"identity": "review-project-next-step", "path": SKILL_PATH},
        "validation": {"command": "python ops/atlas/playbook_doctrine_adoption.py --json"},
        "evidence_refs": ["docs/ops/ATLAS-PLAYBOOK-DOCTRINE-ADOPTION-2026-07-13.md"],
        "current_limitations": ["Root-only adoption evidence."],
    }


def _fixture_root(*, divergent_checkout: bool = False) -> tuple[Path, str]:
    root = Path(tempfile.mkdtemp())
    _write(
        root / "stack.yaml",
        textwrap.dedent(
            """\
            repo_registry:
              playbook:
                path: repos/playbook
                role: governance-runtime
                status: active
            """
        ),
    )
    repo = root / "repos" / "playbook"
    repo.mkdir(parents=True, exist_ok=True)
    _git(repo, "init", "--initial-branch=main")
    _git(repo, "config", "user.name", "Atlas Test")
    _git(repo, "config", "user.email", "atlas@example.test")
    _write(repo / REGISTRY_PATH, json.dumps(REGISTRY_PAYLOAD, indent=2) + "\n")
    _write(repo / SCHEMA_PATH, json.dumps(SCHEMA_PAYLOAD, indent=2) + "\n")
    _write(repo / SKILL_PATH, SKILL_TEXT)
    _git(repo, "add", ".")
    _git(repo, "commit", "-m", "seed doctrine registry")
    accepted_commit = _git(repo, "rev-parse", "HEAD")
    if divergent_checkout:
        _git(repo, "checkout", "-b", "codex/path-discipline-warning-slice-playbook")
        _write(repo / "README.md", "# Divergent checkout\n")
        _git(repo, "add", "README.md")
        _git(repo, "commit", "-m", "diverge checkout")
    _write(root / adoption.ADOPTION_RECORD_REF, json.dumps(_adoption_record(accepted_commit), indent=2) + "\n")
    return root, accepted_commit


class AtlasPlaybookDoctrineAdoptionTests(unittest.TestCase):
    def test_divergent_active_checkout_is_reported_but_verified(self) -> None:
        root, accepted_commit = _fixture_root(divergent_checkout=True)

        report = adoption.build_report(root=root)

        self.assertEqual(adoption.STATUS_VERIFIED, report["status"])
        self.assertEqual(accepted_commit, report["source"]["accepted_commit"])
        self.assertFalse(report["local_checkout"]["matches_accepted_source"])
        self.assertIn("local_checkout_diverged", {item["code"] for item in report["warnings"]})
        self.assertEqual([], report["blockers"])

    def test_source_commit_missing_is_blocker(self) -> None:
        root, _accepted_commit = _fixture_root()
        record = json.loads((root / adoption.ADOPTION_RECORD_REF).read_text(encoding="utf-8"))
        record["source"]["accepted_commit"] = "1" * 40
        _write(root / adoption.ADOPTION_RECORD_REF, json.dumps(record, indent=2) + "\n")

        report = adoption.build_report(root=root)

        self.assertEqual(adoption.STATUS_INVALID, report["status"])
        self.assertIn("source_commit_missing", {item["code"] for item in report["blockers"]})

    def test_source_path_missing_is_blocker(self) -> None:
        root, _accepted_commit = _fixture_root()
        record = json.loads((root / adoption.ADOPTION_RECORD_REF).read_text(encoding="utf-8"))
        record["source"]["artifacts"]["schema"]["path"] = "docs/doctrine/missing.schema.json"
        _write(root / adoption.ADOPTION_RECORD_REF, json.dumps(record, indent=2) + "\n")

        report = adoption.build_report(root=root)

        self.assertIn("source_path_missing", {item["code"] for item in report["blockers"]})

    def test_source_digest_mismatch_is_blocker(self) -> None:
        root, _accepted_commit = _fixture_root()
        record = json.loads((root / adoption.ADOPTION_RECORD_REF).read_text(encoding="utf-8"))
        record["source"]["artifacts"]["registry"]["sha256"] = "0" * 64
        _write(root / adoption.ADOPTION_RECORD_REF, json.dumps(record, indent=2) + "\n")

        report = adoption.build_report(root=root)

        self.assertIn("source_digest_mismatch", {item["code"] for item in report["blockers"]})

    def test_unknown_adopted_record_is_blocker(self) -> None:
        root, _accepted_commit = _fixture_root()
        record = json.loads((root / adoption.ADOPTION_RECORD_REF).read_text(encoding="utf-8"))
        record["registry"]["adopted_record_ids"]["candidate"].append("unknown-record-id")
        _write(root / adoption.ADOPTION_RECORD_REF, json.dumps(record, indent=2) + "\n")

        report = adoption.build_report(root=root)

        self.assertIn("adopted_record_unknown", {item["code"] for item in report["blockers"]})

    def test_duplicate_adopted_record_is_blocker(self) -> None:
        root, _accepted_commit = _fixture_root()
        record = json.loads((root / adoption.ADOPTION_RECORD_REF).read_text(encoding="utf-8"))
        record["registry"]["adopted_record_ids"]["candidate"].append("pattern-one-honest-next-step")
        _write(root / adoption.ADOPTION_RECORD_REF, json.dumps(record, indent=2) + "\n")

        report = adoption.build_report(root=root)

        self.assertIn("adopted_record_duplicate", {item["code"] for item in report["blockers"]})

    def test_lifecycle_mismatch_is_blocker(self) -> None:
        root, _accepted_commit = _fixture_root()
        record = json.loads((root / adoption.ADOPTION_RECORD_REF).read_text(encoding="utf-8"))
        record["registry"]["adopted_record_ids"]["candidate"] = ["rule-owner-repo-truth"]
        _write(root / adoption.ADOPTION_RECORD_REF, json.dumps(record, indent=2) + "\n")

        report = adoption.build_report(root=root)

        self.assertIn("lifecycle_mismatch", {item["code"] for item in report["blockers"]})

    def test_copied_doctrine_rejected_when_statement_body_is_copied(self) -> None:
        root, _accepted_commit = _fixture_root()
        record = json.loads((root / adoption.ADOPTION_RECORD_REF).read_text(encoding="utf-8"))
        record["notes"] = REGISTRY_PAYLOAD["records"][0]["statement"]
        _write(root / adoption.ADOPTION_RECORD_REF, json.dumps(record, indent=2) + "\n")

        report = adoption.build_report(root=root)

        self.assertIn("copied_doctrine_rejected", {item["code"] for item in report["blockers"]})

    def test_malformed_skill_identity_is_blocker(self) -> None:
        root, _accepted_commit = _fixture_root()
        record = json.loads((root / adoption.ADOPTION_RECORD_REF).read_text(encoding="utf-8"))
        record["governed_skill"]["identity"] = "Review Project Next Step"
        _write(root / adoption.ADOPTION_RECORD_REF, json.dumps(record, indent=2) + "\n")

        report = adoption.build_report(root=root)

        self.assertIn("skill_identity_invalid", {item["code"] for item in report["blockers"]})

    def test_main_emits_zero_only_for_verified_adoption(self) -> None:
        root, _accepted_commit = _fixture_root()
        stdout = io.StringIO()
        with mock.patch.object(adoption, "atlas_root", return_value=root), mock.patch("sys.stdout", stdout):
            code = adoption.main(["--json"])

        self.assertEqual(0, code)
        payload = json.loads(stdout.getvalue())
        self.assertEqual(adoption.STATUS_VERIFIED, payload["status"])


if __name__ == "__main__":
    unittest.main()
